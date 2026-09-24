#!/usr/bin/env python3
"""LoRA SFT on Qwen3 base with loss on the assistant turn only (ChatML). Single GPU.
Examples:
  python train_lora.py --data ../data/sft/seat/Hegel/tier1000.jsonl --dev-seat Hegel --out runs/hegel_t1000
  python train_lora.py --data ../data/sft/merged/tier1000.jsonl --out runs/merged_t1000
  python train_lora.py --data ../data/sft/merged/tier250.jsonl --out runs/throughput --max-steps 30   # throughput test
"""
import argparse, json, math, os, time, torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, TrainerCallback
from peft import LoraConfig, get_peft_model
ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--model", default="Qwen/Qwen3-4B-Base"); ap.add_argument("--dev", default="../data/sft/dev.jsonl")
ap.add_argument("--dev-seat", default=None, help="restrict dev loss to one seat (per-seat adapters)")
ap.add_argument("--epochs", type=float, default=2); ap.add_argument("--lr", type=float, default=2e-4)
ap.add_argument("--rank", type=int, default=16); ap.add_argument("--max-len", type=int, default=3072)
ap.add_argument("--bs", type=int, default=4); ap.add_argument("--accum", type=int, default=4)
ap.add_argument("--max-steps", type=int, default=-1); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
tok = AutoTokenizer.from_pretrained(a.model); tok.pad_token = tok.pad_token or "<|endoftext|>"
def chatml(msgs):
    p = "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in msgs[:-1]) + "<|im_start|>assistant\n"
    return p, msgs[-1]["content"] + "<|im_end|>"
class DS(Dataset):
    def __init__(self, path, seat=None):
        rows = [json.loads(l) for l in open(path)]; rows = [r for r in rows if seat is None or r["seat"] == seat]
        self.items, self.cut = [], 0
        for r in rows:
            p, t = chatml(r["messages"]); pi = tok(p, add_special_tokens=False)["input_ids"]; ti = tok(t, add_special_tokens=False)["input_ids"]
            ids = (pi + ti)[:a.max_len]; lab = ([-100] * len(pi) + ti)[:a.max_len]; self.cut += len(pi + ti) > a.max_len
            self.items.append((ids, lab))
        self.ntok = sum(len(i) for i, _ in self.items)
    def __len__(self): return len(self.items)
    def __getitem__(self, i): return self.items[i]
def collate(b):
    n = max(len(i) for i, _ in b); pad = tok.pad_token_id
    ids = torch.tensor([i + [pad] * (n - len(i)) for i, _ in b]); lab = torch.tensor([l + [-100] * (n - len(l)) for _, l in b])
    return {"input_ids": ids, "labels": lab, "attention_mask": (torch.arange(n)[None] < torch.tensor([len(i) for i, _ in b])[:, None]).long()}
train = DS(a.data); dev = DS(a.dev, a.dev_seat) if a.dev and os.path.exists(a.dev) else None
print(f"train {len(train)} ex, {train.ntok/1e6:.2f}M tok, truncated {train.cut} | dev {len(dev) if dev else 0}", flush=True)
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
model.gradient_checkpointing_enable(); model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, task_type="CAUSAL_LM",
                       target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.print_trainable_parameters()
class Speed(TrainerCallback):
    def on_train_begin(self, *x, **k): self.t0 = time.time()
    def on_log(self, args, state, control, logs=None, **k):
        if state.global_step and logs is not None:
            dt = time.time() - self.t0; seen = state.global_step * args.per_device_train_batch_size * args.gradient_accumulation_steps
            logs["tok_per_s"] = round(seen * train.ntok / len(train) / dt); logs["mem_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 1)
steps_per_epoch = math.ceil(len(train) / (a.bs * a.accum))
args = TrainingArguments(output_dir=a.out, per_device_train_batch_size=a.bs, gradient_accumulation_steps=a.accum,
    num_train_epochs=a.epochs, max_steps=a.max_steps, learning_rate=a.lr, lr_scheduler_type="cosine", warmup_steps=max(1, int(0.05 * (a.max_steps if a.max_steps > 0 else steps_per_epoch * a.epochs))),
    weight_decay=0.0, bf16=True, logging_steps=5, save_strategy="no" if a.max_steps > 0 else "epoch", save_total_limit=2,
    eval_strategy="no" if (dev is None or a.max_steps > 0) else "steps", eval_steps=max(10, steps_per_epoch // 2),
    per_device_eval_batch_size=a.bs, report_to="none", seed=a.seed, remove_unused_columns=False,
    dataloader_num_workers=2)
tr = Trainer(model=model, args=args, train_dataset=train, eval_dataset=dev, data_collator=collate, callbacks=[Speed()])
t0 = time.time(); tr.train(); el = time.time() - t0
model.save_pretrained(os.path.join(a.out, "adapter"))
summary = {"args": vars(a), "train_examples": len(train), "train_tokens": train.ntok, "seconds": round(el),
           "steps": tr.state.global_step, "log": tr.state.log_history}
if dev is not None and a.max_steps < 0: summary["final_dev"] = tr.evaluate()
json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
print(f"done in {el/60:.1f} min", flush=True)
