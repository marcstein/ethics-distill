#!/usr/bin/env python3
"""Generate seat analyses for the test set with vLLM (run on puget in .venv-vllm).
  python gen.py --name merged_t1000   --lora ../train/runs/merged_t1000/adapter
  python gen.py --name seat_t1000     --lora "../train/runs/seat_{seat}_t1000/adapter"
  python gen.py --name base_label     (untrained base, one-line label only: the floor)
  python gen.py --name base_full      --prompt full            (untrained base, full seat prompt)
  python gen.py --name instruct_full  --prompt full --model Qwen/Qwen3-4B --nothink   (prompted baseline)
"""
import argparse, json, os, sys
ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--model", default="Qwen/Qwen3-4B-Base")
ap.add_argument("--lora", default=None, help="adapter dir, may contain {seat}"); ap.add_argument("--prompt", choices=["label", "full"], default="label")
ap.add_argument("--nothink", action="store_true"); ap.add_argument("--test", default="../data/sft/test.jsonl")
ap.add_argument("--limit", type=int, default=0, help="first N cases only"); ap.add_argument("--max-tokens", type=int, default=2600)
a = ap.parse_args()
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
rows = [json.loads(l) for l in open(a.test)]
if a.limit: keep = list(dict.fromkeys(r["sid"] for r in rows))[:a.limit]; rows = [r for r in rows if r["sid"] in set(keep)]
full = json.load(open("baseline_prompts.json"))
def prompt(r):
    sys_ = full[r["seat"]] if a.prompt == "full" else r["messages"][0]["content"]
    p = f"<|im_start|>system\n{sys_}<|im_end|>\n<|im_start|>user\n{r['messages'][1]['content']}<|im_end|>\n<|im_start|>assistant\n"
    return p + ("<think>\n\n</think>\n\n" if a.nothink else "")
lora_ids = {}
def lreq(seat):
    if not a.lora: return None
    path = os.path.abspath(a.lora.format(seat=seat)); key = path
    if key not in lora_ids: lora_ids[key] = len(lora_ids) + 1
    return LoRARequest(f"{a.name}_{lora_ids[key]}", lora_ids[key], path)
llm = LLM(model=a.model, dtype="bfloat16", max_model_len=8192, gpu_memory_utilization=0.88, seed=0,
          enable_lora=bool(a.lora), max_lora_rank=16, max_loras=8)
sp = SamplingParams(temperature=0.0, max_tokens=a.max_tokens, stop=["<|im_end|>", "<|endoftext|>"], repetition_penalty=1.03)
reqs = [lreq(r["seat"]) for r in rows]
outs = llm.generate([prompt(r) for r in rows], sp, lora_request=reqs if a.lora else None)
os.makedirs("gen", exist_ok=True)
with open(f"gen/{a.name}.jsonl", "w") as f:
    for r, o in zip(rows, outs):
        f.write(json.dumps({"sid": r["sid"], "seat": r["seat"], "domain": r.get("domain"), "text": o.outputs[0].text,
                            "finish": o.outputs[0].finish_reason, "ntok": len(o.outputs[0].token_ids)}, ensure_ascii=False) + "\n")
print("wrote", len(rows), "to", f"gen/{a.name}.jsonl")
