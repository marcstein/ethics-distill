#!/usr/bin/env python3
"""Subscription judge: the same 120-item blind grading as judge_quality.py, done by Claude Code (no API).
  python3 eval/judge_sub.py pack SRC [SRC...]   -> results/judge_sub/todo_<src>_NN.md (12 items each) + results/judge_sub/key.json (private)
  python3 eval/judge_sub.py check               -> validates results/judge_sub/grades_*.jsonl against the key and schema
  python3 eval/judge_sub.py report              -> per-src means (overall, facts, fidelity, coherence, clarity, held-out) next to the API judge rows
The grader never sees the source model or the other models' answers for the same case. Output schema = judge_quality TOOL fields."""
import json, os, sys, glob, random, collections, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distill")); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, judge_quality as J
D = os.path.join(C.ROOT, "results", "judge_sub"); os.makedirs(D, exist_ok=True); KEY = os.path.join(D, "key.json")
FIELDS = list(J.TOOL["input_schema"]["properties"]); NUM = [f for f in FIELDS if f not in ("comment",)]
def pack(srcs):
    SC, keys = J.sample(); A = J.load(); key = json.load(open(KEY)) if os.path.exists(KEY) else {}
    for src in srcs:
        items = [(sid, seat) for sid, seat in keys if (src, sid, seat) in A]; rng = random.Random(hash(src) & 0xffff); rng.shuffle(items)
        for n in range(0, len(items), 12):
            batch = items[n:n + 12]; name = f"todo_{src}_{n // 12 + 1:02d}.md"; out = f"grades_{src}_{n // 12 + 1:02d}.jsonl"; lines = [f"# Blind grading batch {n // 12 + 1} for {src}\n",
                "Grade each item strictly and independently, as the rubric says; do not compare items. Write one JSON object per item to "
                f"`results/judge_sub/{out}` with fields: id, " + ", ".join(FIELDS) + " (same scale and meaning as eval/judge_quality.py TOOL; 1 to 5 criteria, 1 to 10 overall). Then run `python3 eval/judge_sub.py check`.\n"]
            for sid, seat in batch:
                iid = f"{src}__{sid}__{seat}"; key[iid] = {"src": src, "sid": sid, "seat": seat, "domain": SC[sid]["domain"]}
                lines.append(f"\n---\n## id: {iid}\n\nRUBRIC:\n{J.RUBRIC.format(name=J.NAME[seat])}\n\n{J.V.seat_user(SC[sid])}\n\n=== ANALYSIS (as {J.NAME[seat]}) ===\n{J.render(A[(src, sid, seat)])}\n")
            open(os.path.join(D, name), "w").write("\n".join(lines))
        print(src, len(items), "items,", (len(items) + 11) // 12, "batches")
    json.dump(key, open(KEY, "w"), indent=1)
def grades():
    key = json.load(open(KEY)); G = {}
    for f in sorted(glob.glob(os.path.join(D, "grades_*.jsonl"))):
        for r in C.jsonl_read(f): G[r["id"]] = r
    return key, G
def check():
    key, G = grades(); bad = [i for i, r in G.items() if i not in key or any(not isinstance(r.get(k), (int, float)) for k in ("overall", "fact_discipline", "fidelity", "coherence", "clarity"))]
    by = collections.Counter(key[i]["src"] for i in G if i in key); print({s: f"{by[s]}/{sum(1 for v in key.values() if v['src'] == s)}" for s in sorted({v['src'] for v in key.values()})}, "bad:", bad[:5])
def report():
    key, G = grades(); rows = collections.defaultdict(list)
    for i, r in G.items():
        if i in key: rows[key[i]["src"]].append((r, key[i]))
    print("src | n | overall | facts | fidelity | coherence | clarity | held-out overall")
    for src, L in sorted(rows.items()):
        m = lambda k, f=lambda kk: True: st.mean(r[k] for r, kk in L if f(kk))
        ho = [r["overall"] for r, kk in L if kk["domain"] in ("clinical", "biotech")]
        print(f"{src} | {len(L)} | {m('overall'):.2f} | {m('fact_discipline'):.2f} | {m('fidelity'):.2f} | {m('coherence'):.2f} | {m('clarity'):.2f} | {st.mean(ho) if ho else float('nan'):.2f}")
if __name__ == "__main__":
    a = sys.argv[1:]; {"pack": lambda: pack(a[1:]), "check": check, "report": report}[a[0]]()
