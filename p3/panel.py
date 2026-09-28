#!/usr/bin/env python3
"""Seven-seat Flash panel on the Phase 3 cases, median of 3 runs per seat (0.90 run-to-run stability in phase 2).
Used only to find the strongest dissent and to flag contested cases; the student never sees seats.
  python panel.py run      (resumable)   |   python panel.py stats"""
import json, os, sys, statistics as st, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distill"))
import orc, common as C, bakeoff as B, panel as P
CASES = os.path.join(C.ROOT, "data", "p3", "cases.jsonl"); RAW = os.path.join(C.ROOT, "data", "p3", "panel_raw.jsonl"); OUT = os.path.join(C.ROOT, "data", "p3", "panel.jsonl")
SEATS = [s for s in P.SEATS if s != "KantModern"]; K = 3
sgn = lambda x: (x > 0) - (x < 0)
def run():
    cases = {c["id"]: c for c in C.jsonl_read(CASES)}
    have = collections.Counter((r["id"], r["seat"]) for r in C.jsonl_read(RAW) if r["output"])
    todo = [(cid, s, i) for cid in cases for s in SEATS for i in range(K - have[(cid, s)])]
    print("panel calls", len(todo))
    def one(x):
        cid, seat, _ = x; o = None
        for _ in range(2):
            try: o, _t, _f, _u = B.call(orc.FLASH, seat, cases[cid])
            except Exception as e: print("err", cid, seat, str(e)[:100], file=sys.stderr)
            if P.valid(o): break
        return {"id": cid, "seat": seat, "output": {"position": o["position"], "verdict": o.get("verdict", ""), "strongest_objection": o.get("strongest_objection", ""), "reasoning": o.get("reasoning", "")} if P.valid(o) else None}
    for r in orc.pmap(one, todo, int(os.environ.get("THREADS", "8"))):
        if r: C.jsonl_append(RAW, [r])
    summarise(); print("OpenRouter spent $%.2f" % orc.spent())
def summarise():
    R = collections.defaultdict(list)
    for r in C.jsonl_read(RAW):
        if r["output"]: R[(r["id"], r["seat"])].append(r["output"])
    rows = []
    for cid in {k[0] for k in R}:
        med = {}; obj = {}
        for s in SEATS:
            v = R.get((cid, s), [])
            if not v: continue
            med[s] = int(st.median(o["position"] for o in v)); obj[s] = min(v, key=lambda o: abs(o["position"] - med[s]))
        if len(med) < 5: continue
        centre = st.median(med.values()); far = max(med, key=lambda s: (abs(med[s] - centre), -SEATS.index(s)))
        contested = any(p > 0 for p in med.values()) and any(p < 0 for p in med.values())
        rows.append({"id": cid, "positions": med, "panel_median": centre, "contested": contested, "dissent_seat": far, "dissent_position": med[far],
                     "dissent_verdict": obj[far]["verdict"], "dissent_objection": obj[far]["strongest_objection"], "dissent_reasoning": obj[far]["reasoning"]})
    with open(OUT, "w") as f:
        for r in sorted(rows, key=lambda r: r["id"]): f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("panel summary for", len(rows), "cases; contested", sum(r["contested"] for r in rows))
def stats():
    cases = {c["id"]: c for c in C.jsonl_read(CASES)}; agree = collections.defaultdict(list)
    for r in C.jsonl_read(OUT):
        c = cases.get(r["id"]);
        if not c: continue
        want = {"yes": 2, "yes with care": 1, "partly": -1, "no": -2}[c["intended"]]
        agree[c["type"]].append(sgn(r["panel_median"]) == sgn(want))
    for t, v in agree.items(): print(f"{t:16s} panel-median sign agrees with writer's intended decision: {sum(v)}/{len(v)}")
if __name__ == "__main__": {"run": run, "stats": stats, "summarise": summarise}[sys.argv[1]]()
