#!/usr/bin/env python3
"""Export cases + panel analyses as JSON chunks for the case reader."""
import json, os, sys, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, "distill")); sys.path.insert(0, os.path.join(R, "eval"))
import common as C, panel as P, sft_format as F
from score import clean
OUT = os.path.join(R, "reader", "data"); os.makedirs(OUT, exist_ok=True)
KEEP = ["action_rated", "established_facts", "open_facts", "reasoning", "strongest_objection", "position", "verdict", "modified_version_acceptable", "modification", "would_change_if"]
def slim(o): return {k: o.get(k) for k in KEEP if o.get(k) not in (None, "")}
def load(path): return {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(path) if r.get("output")}
SON = load(P.outpath("train")); O5 = load(P.outpath("eval")); O55 = load(os.path.join(R, "results", "check55.jsonl"))
STU = {}
for r in C.jsonl_read(os.path.join(R, "eval", "gen", "merged_t1000.jsonl")):
    o = F.parse(clean(r["text"])); 
    if o.get("position") is not None: STU[(r["sid"], r["seat"])] = {k: v for k, v in o.items() if v not in (None, "")}
test = set(json.load(open(os.path.join(R, "data", "sft", "splits.json")))["test"])
SRC = {"sonnet": ("Sonnet 5 (teacher)", SON), "opus5": ("Opus 5 (gold)", O5), "student": ("Trained 4B student", STU), "opus55": ("Opus 5.5 (check)", O55)}
index, chunk, n = [], [], 0
def flush():
    global chunk, n
    if chunk: json.dump({"cases": chunk}, open(f"{OUT}/c{n:02d}.json", "w"), ensure_ascii=False, separators=(",", ":")); n += 1; chunk = []
for setname, cases in [("train", P.scen("train")), ("test", [s for s in P.scen("eval") if s["id"] in test])]:
    for s in cases:
        panels = {}
        for key, (label, D) in SRC.items():
            p = {seat: slim(D[(s["id"], seat)]) for seat in P.SEATS if (s["id"], seat) in D}
            if len(p) == len(P.SEATS): panels[key] = p
        if not panels: continue
        meta = {k: s.get(k) for k in ["id", "domain", "conflict", "agent", "stakes", "difficulty", "pair_id", "pair_type", "twin"]}
        meta["setting"] = (s.get("setting") or [None])[0]; meta["set"] = setname; meta["question"] = s["question"]
        index.append(meta | {"chunk": n, "pos": {k: [p[seat]["position"] for seat in P.SEATS] for k, p in panels.items()}})
        chunk.append(meta | {"text": s["text"], "panels": panels})
        if len(chunk) >= 100: flush()
    flush()
json.dump({"seats": P.SEATS, "sources": {k: v[0] for k, v in SRC.items()}, "cases": index}, open(f"{OUT}/index.json", "w"), ensure_ascii=False, separators=(",", ":"))
print(len(index), "cases in", n, "chunks"); os.system(f"du -sh {OUT}; ls -la {OUT} | head -20")
