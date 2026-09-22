#!/usr/bin/env python3
"""Near-duplicate detection across all scenario files: TF-IDF cosine on word unigrams+bigrams (stdlib). Twins excluded. Reports effective sample size."""
import json, math, re, sys
from collections import Counter
import common as C
files = sys.argv[1:]
rows = []
for f in files:
    for r in C.jsonl_read(f):
        if "text" in r: r["_file"] = f; rows.append(r)
def toks(t):
    w = re.findall(r"[a-z]+", t.lower()); w = [x for x in w if len(x) > 2]
    return w + [a + "_" + b for a, b in zip(w, w[1:])]
docs = [Counter(toks(r["text"])) for r in rows]; df = Counter()
for d in docs: df.update(d.keys())
N = len(docs); vecs = []
for d in docs:
    v = {k: (1 + math.log(c)) * math.log(N / df[k]) for k, c in d.items() if df[k] < N * 0.5}
    n = math.sqrt(sum(x * x for x in v.values())) or 1; vecs.append({k: x / n for k, x in v.items()})
inv = {}
for i, v in enumerate(vecs):
    for k in v: inv.setdefault(k, []).append(i)
dups = []; seen = set()
for i, v in enumerate(vecs):
    cand = Counter()
    for k in v:
        if len(inv[k]) < 40:
            for j in inv[k]:
                if j < i: cand[j] += 1
    best = 0; bj = None
    for j in cand:
        if rows[i].get("pair_id") and rows[i].get("pair_id") == rows[j].get("pair_id"): continue
        s = sum(v[k] * vecs[j].get(k, 0) for k in v)
        if s > best: best, bj = s, j
    if best > 0.55: dups.append((rows[i]["id"], rows[bj]["id"], round(best, 2))); rows[i]["near_dup_of"] = rows[bj]["id"]; rows[i]["near_dup_sim"] = round(best, 3)
print("cases", N, "| near-duplicates (cosine > 0.55, twins excluded):", len(dups), "| effective sample size", N - len(dups))
for d in sorted(dups, key=lambda x: -x[2])[:8]: print("  ", d)
cross = [d for d in dups if any(r["id"] == d[0] and "eval" in r["_file"] for r in rows) or any(r["id"] == d[1] and "eval" in r["_file"] for r in rows)]
print("train/eval cross-duplicates:", len(cross))
for f in files:
    with open(f, "w") as fh:
        for r in rows:
            if r["_file"] == f: r2 = {k: v for k, v in r.items() if k != "_file"}; fh.write(json.dumps(r2, ensure_ascii=False) + "\n")
        for r in C.jsonl_read(f):
            pass
