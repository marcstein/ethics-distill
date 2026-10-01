#!/usr/bin/env python3
"""Fallback generator with plain transformers (no vLLM): merge the LoRA adapter into the base and generate greedily in batches.
Same arguments and output schema as gen.py. Used when vLLM cannot load the base (Mistral 3 / Gemma 4 wrappers)."""
import argparse, json, os, sys, time, torch
ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--model", required=True); ap.add_argument("--lora", required=True)
ap.add_argument("--test", default="../data/sft/test.jsonl"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--max-tokens", type=int, default=2600)
ap.add_argument("--bs", type=int, default=16)
a = ap.parse_args()
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
rows = [json.loads(l) for l in open(a.test)]
if a.limit: keep = list(dict.fromkeys(r["sid"] for r in rows))[:a.limit]; rows = [r for r in rows if r["sid"] in set(keep)]
def prompt(r):
    sys_ = r["messages"][0]["content"]; user = r["messages"][1]["content"]
    return (f"<|im_start|>system\n{sys_}<|im_end|>\n" if sys_ else "") + f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"; tok.pad_token = tok.pad_token or tok.eos_token
try: model = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
except Exception as e:
    print("CausalLM failed (%s); loading ImageTextToText" % str(e)[:100], flush=True)
    from transformers import AutoModelForImageTextToText
    try: model = AutoModelForImageTextToText.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
    except Exception as e2:
        print("ImageTextToText failed (%s); loading AutoModelForMultimodalLM" % str(e2)[:120], flush=True)
        from transformers import AutoModelForMultimodalLM
        model = AutoModelForMultimodalLM.from_pretrained(a.model, dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
model = PeftModel.from_pretrained(model, a.lora).merge_and_unload().eval(); print("merged adapter", a.lora, flush=True)
stops = ["<|im_end|>", "<|endoftext|>", "\n<|im_start|>"]
os.makedirs("gen", exist_ok=True); t0 = time.time()
order = sorted(range(len(rows)), key=lambda i: len(prompt(rows[i])))   # length-sorted batches waste less padding
res = [None] * len(rows)
for b in range(0, len(order), a.bs):
    idx = order[b:b + a.bs]; ps = [prompt(rows[i]) for i in idx]
    enc = tok(ps, return_tensors="pt", padding=True).to("cuda")
    with torch.no_grad(): g = model.generate(**enc, max_new_tokens=a.max_tokens, do_sample=False, repetition_penalty=1.03, eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id)
    for i, seq in zip(idx, g[:, enc["input_ids"].shape[1]:]):
        n = int((seq != tok.pad_token_id).sum()); text = tok.decode(seq, skip_special_tokens=True); fin = "length" if n >= a.max_tokens else "stop"
        for s in stops:
            if s in text: text = text.split(s)[0]; fin = "stop"
        res[i] = {"sid": rows[i]["sid"], "seat": rows[i]["seat"], "variant": rows[i].get("variant"), "domain": rows[i].get("domain"), "text": text, "finish": fin, "ntok": n}
    print(f"{b + len(idx)}/{len(rows)} {time.time() - t0:.0f}s", flush=True)
with open(f"gen/{a.name}.jsonl", "w") as out:
    for r in res: out.write(json.dumps(r, ensure_ascii=False) + "\n")
print("wrote", len(rows), "to", f"gen/{a.name}.jsonl")
