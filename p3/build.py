#!/usr/bin/env python3
"""Build Phase 3 training and evaluation files from cases + synth + pressure.
  python build.py   -> data/p3/sft/train.jsonl (messages; base cases + pressured variants, same target)
                       data/p3/sft/dpo.jsonl   (prompt messages, chosen, rejected)
                       data/p3/sft/eval.jsonl  (test cases: base + every wrapper; reference decision; no target)"""
import json, os, sys, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distill"))
import fmt, common as C
D = os.path.join(C.ROOT, "data", "p3"); S = os.path.join(D, "sft"); os.makedirs(S, exist_ok=True)
def w(name, rows):
    with open(os.path.join(S, name), "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows))
cases = {c["id"]: c for c in C.jsonl_read(os.path.join(D, "cases.jsonl"))}; synth = {r["id"]: r for r in C.jsonl_read(os.path.join(D, "synth.jsonl"))}
press = C.jsonl_read(os.path.join(D, "pressure.jsonl"))
train, dpo, ev = [], [], []
for cid, c in cases.items():
    if c["split"] == "train" and cid in synth:
        train.append({"id": cid, "type": c["type"], "wrap": "base", "messages": fmt.messages(c, synth[cid]["text"])})
    if c["split"] == "test":
        ev.append({"key": f"{cid}|base", "id": cid, "type": c["type"], "wrap": "base", "held_out_wrap": False, "reference": c["intended"], "messages": fmt.messages(c)})
for v in press:
    c = cases.get(v["id"]);
    if not c: continue
    vc = {"text": v["text"], "question": v["question"]}
    if v["split"] == "train" and v["id"] in synth:
        tgt = synth[v["id"]]["text"]
        train.append({"id": v["id"], "type": c["type"], "wrap": v["wrap"], "messages": fmt.messages(vc, tgt)})
        if v.get("rejected"): dpo.append({"id": v["id"], "wrap": v["wrap"], "push": v["push"], "prompt": fmt.messages(vc), "chosen": tgt, "rejected": v["rejected"]})
    elif v["split"] == "test":
        ev.append({"key": f"{v['id']}|{v['wrap']}", "id": v["id"], "type": c["type"], "wrap": v["wrap"], "held_out_wrap": v["held_out_wrap"], "push": v["push"], "reference": c["intended"], "messages": fmt.messages(vc)})
random.Random(0).shuffle(train)
w("train.jsonl", train); w("dpo.jsonl", dpo); w("eval.jsonl", ev)
print("train by wrap:", dict(collections.Counter(r["wrap"] for r in train)), "| eval by type:", dict(collections.Counter(r["type"] for r in ev)))
