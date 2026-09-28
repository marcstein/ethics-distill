#!/usr/bin/env python3
"""Stage B: DPO on pressure pairs, LoRA on top of the stage-A model (pass the merged stage-A weights as --model).
  python train_dpo.py --model runs/p3_sft/merged --data ../data/p3/sft/dpo.jsonl --out runs/p3_dpo [--beta 0.05 --epochs 1 --lr 5e-6]
Needs: pip install trl  (in .venv). Output: runs/p3_dpo/adapter (LoRA over the merged stage-A model)."""
import argparse, json, os, torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import LoraConfig
from trl import DPOConfig, DPOTrainer
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--beta", type=float, default=0.05); ap.add_argument("--epochs", type=float, default=1); ap.add_argument("--lr", type=float, default=5e-6)
ap.add_argument("--bs", type=int, default=2); ap.add_argument("--accum", type=int, default=8); ap.add_argument("--rank", type=int, default=16); ap.add_argument("--max-len", type=int, default=2048)
a = ap.parse_args()
tok = AutoTokenizer.from_pretrained(a.model); tok.pad_token = tok.pad_token or "<|endoftext|>"
def chatml(msgs): return "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in msgs) + "<|im_start|>assistant\n"
rows = [json.loads(l) for l in open(a.data)]
ds = Dataset.from_list([{"prompt": chatml(r["prompt"]), "chosen": r["chosen"] + "<|im_end|>", "rejected": r["rejected"] + "<|im_end|>"} for r in rows])
print("pairs", len(ds))
model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa")
cfg = DPOConfig(output_dir=a.out, beta=a.beta, num_train_epochs=a.epochs, learning_rate=a.lr, per_device_train_batch_size=a.bs, gradient_accumulation_steps=a.accum,
                max_length=a.max_len, bf16=True, logging_steps=5, save_strategy="no", report_to="none", gradient_checkpointing=True, warmup_ratio=0.05, lr_scheduler_type="cosine", remove_unused_columns=False)
peft = LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05, task_type="CAUSAL_LM", target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
tr = DPOTrainer(model=model, ref_model=None, args=cfg, train_dataset=ds, processing_class=tok, peft_config=peft)
tr.train(); tr.model.save_pretrained(os.path.join(a.out, "adapter")); tok.save_pretrained(os.path.join(a.out, "adapter"))
json.dump({"pairs": len(ds), "beta": a.beta, "epochs": a.epochs, "lr": a.lr, "log": tr.state.log_history[-3:]}, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
print("saved", os.path.join(a.out, "adapter"))
