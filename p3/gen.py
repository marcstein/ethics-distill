#!/usr/bin/env python3
"""vLLM generation over a messages jsonl (Phase 3 eval set or any {key, messages} file). Requires the .venv-vllm environment.
  python gen.py --name NAME --model Qwen/Qwen3-4B-Base [--lora DIR] [--input ../data/p3/sft/eval.jsonl] [--n 1] [--temperature 0]
Writes data/p3/gen/NAME.jsonl : {key, text} (n>1 -> one line per sample with key suffix #i, for self-consistency voting)."""
import argparse, json, os, sys
ap = argparse.ArgumentParser(); ap.add_argument("--name", required=True); ap.add_argument("--model", default="Qwen/Qwen3-4B-Base"); ap.add_argument("--lora", default=None)
ap.add_argument("--input", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "p3", "sft", "eval.jsonl")); ap.add_argument("--n", type=int, default=1)
ap.add_argument("--temperature", type=float, default=0.0); ap.add_argument("--max-tokens", type=int, default=700); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest
rows = [json.loads(l) for l in open(a.input)]; rows = rows[:a.limit] if a.limit else rows
def chatml(msgs): return "".join(f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n" for m in msgs) + "<|im_start|>assistant\n"
prompts = [chatml(r["messages"]) for r in rows]
llm = LLM(model=a.model, dtype="bfloat16", max_model_len=4096, gpu_memory_utilization=0.88, seed=0, enable_lora=bool(a.lora), max_lora_rank=16)
sp = SamplingParams(temperature=a.temperature if a.n == 1 else max(a.temperature, 0.7), top_p=0.95, max_tokens=a.max_tokens, n=a.n, stop=["<|im_end|>", "<|endoftext|>", "\n\nCASE:"], repetition_penalty=1.03)
outs = llm.generate(prompts, sp, lora_request=LoRARequest("p3", 1, a.lora) if a.lora else None)
od = os.path.join(os.path.dirname(a.input), "..", "gen"); os.makedirs(od, exist_ok=True); out = os.path.join(od, a.name + ".jsonl")
with open(out, "w") as f:
    for r, o in zip(rows, outs):
        for i, c in enumerate(o.outputs):
            f.write(json.dumps({"key": r["key"] + (f"#{i}" if a.n > 1 else ""), "text": c.text, "finish": c.finish_reason}, ensure_ascii=False) + "\n")
print("wrote", out, len(rows) * a.n, "| finished by stop token:", sum(c.finish_reason == "stop" for o in outs for c in o.outputs), "/", len(rows) * a.n)
