#!/usr/bin/env python3
"""Opus 5.5 panel check on 50 cases: 25 training cases (compare with Sonnet) + 25 test cases (compare with Opus 5).
Synchronous, resumable, chunked (call repeatedly until 'remaining 0').  python check55.py run | report"""
import json, os, sys, random, time, statistics as st, collections
from concurrent.futures import ThreadPoolExecutor
import common as C, panel as P
OUT = os.path.join(C.ROOT, "results", "check55.jsonl"); SEED = 55
def cases():
    rng = random.Random(SEED); tr = P.scen("train"); rng.shuffle(tr)
    test = set(json.load(open(os.path.join(C.ROOT, "data", "sft", "splits.json")))["test"])
    te = [s for s in P.scen("eval") if s["id"] in test]; rng.shuffle(te)
    return [("train", s) for s in tr[:25]] + [("test", s) for s in te[:25]]
def run(budget=150):
    done = {(r["sid"], r["seat"]) for r in C.jsonl_read(OUT) if r["output"]}
    todo = [(src, s, seat) for src, s in cases() for seat in P.SEATS if (s["id"], seat) not in done]
    per = (2300 * C.PRICE[C.OPUS][0] + 1800 * C.PRICE[C.OPUS][1]) / 1e6; t0 = time.time()
    chunk = todo[:32]; C.check_cap(len(chunk) * per * 1.3)
    def one(x):
        src, s, seat = x; tries = 0; o = None
        while tries < 2 and not P.valid(o):
            tries += 1
            try: o = P.repair(C.tool_input(C.message("check55", P.params(C.OPUS, seat, s))))
            except Exception as e: print("err", s["id"], seat, str(e)[:100], flush=True)
        return {"src": src, "sid": s["id"], "seat": seat, "output": o if P.valid(o) else None, "tries": tries}
    with ThreadPoolExecutor(32) as ex: res = list(ex.map(one, chunk))
    C.jsonl_append(OUT, res)
    print(f"did {len(chunk)} in {time.time()-t0:.0f}s | remaining {len(todo)-len(chunk)} | spent ${C.spent():.2f}")
sgn = lambda x: (x > 0) - (x < 0)
def panel_stats(D, ids):
    seats = [s for s in P.SEATS if s != "KantModern"]; out = collections.Counter(); sd = []
    for i in ids:
        ps = [D[(i, s)] for s in seats]
        out["split" if any(p > 0 for p in ps) and any(p < 0 for p in ps) else "unanimous" if len(set(ps)) == 1 else "same-sign/varied"] += 1
        sd.append(st.pstdev(ps))
    return dict(out), round(st.mean(sd), 2)
def report():
    R = {(r["sid"], r["seat"]): r for r in C.jsonl_read(OUT)}
    O = {k: r["output"]["position"] for k, r in R.items() if r["output"]}
    first = sum(1 for r in R.values() if r["tries"] == 1 and r["output"]); print(f"rows {len(R)} valid {len(O)} first-try valid {first/len(R):.3f}")
    S = {(r["sid"], r["seat"]): r["output"]["position"] for r in C.jsonl_read(P.outpath("train"))}
    G = {(r["sid"], r["seat"]): r["output"]["position"] for r in C.jsonl_read(P.outpath("eval"))}
    for src, ref, name in [("train", S, "Sonnet 5"), ("test", G, "Opus 5")]:
        ids = sorted({r["sid"] for r in R.values() if r["src"] == src and all((r["sid"], s) in O for s in P.SEATS)})
        print(f"\n{src}: {len(ids)} complete cases")
        print("  Opus 5.5 panel:", panel_stats(O, ids), "|", name, "panel:", panel_stats(ref, ids))
        pairs = [(O[(i, s)], ref[(i, s)]) for i in ids for s in P.SEATS]
        print(f"  agreement with {name}: sign {sum(sgn(a)==sgn(b) for a,b in pairs)/len(pairs):.2f} exact {sum(a==b for a,b in pairs)/len(pairs):.2f}")
        print("  position dist 5.5:", dict(sorted(collections.Counter(O[(i,s)] for i in ids for s in P.SEATS if s!='KantModern').items())),
              "|", name, dict(sorted(collections.Counter(ref[(i,s)] for i in ids for s in P.SEATS if s!='KantModern').items())))
        dev = collections.Counter()
        for i in ids:
            ps = {s: O[(i, s)] for s in P.SEATS if s != "KantModern"}; maj = sgn(sum(sgn(p) for p in ps.values()))
            for s, p in ps.items(): dev[s] += sgn(p) != maj
        print("  5.5 seats off the panel majority:", dict(dev))
if __name__ == "__main__": {"run": run, "report": report}[sys.argv[1]]()
