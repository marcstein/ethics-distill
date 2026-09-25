#!/usr/bin/env python3
"""Build chat-format SFT files: per-seat and merged, nested case tiers 250/500/1000, plus dev/test from the eval set."""
import json, os, random, collections
import common as C, panel as P, sft_format as F
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("--seats", default=None); _ap.add_argument("--out", default="sft"); _a = _ap.parse_args()
R = C.ROOT; OUT = os.path.join(R, "data", _a.out); SEED = 20260924; TIERS = [250, 500, 1000]; NDEV = 40
def ex(seat, s, o): return {"messages": [{"role": "system", "content": F.system(seat)}, {"role": "user", "content": F.user(s)},
                                         {"role": "assistant", "content": F.render(o)}], "sid": s["id"], "seat": seat}
def groups(S):   # pair twins travel together
    g = collections.OrderedDict()
    for s in S: g.setdefault(s.get("pair_id") or s["id"], []).append(s)
    return list(g.values())
def nested_tiers(S):
    rng = random.Random(SEED); bydom = collections.defaultdict(list)
    for grp in groups(S): bydom[grp[0]["domain"]].append(grp)
    for d in bydom: rng.shuffle(bydom[d])
    order = []   # round-robin across domains -> every prefix is domain-balanced
    while any(bydom.values()):
        for d in sorted(bydom):
            if bydom[d]: order.extend(bydom[d].pop(0))
    return {t: [s["id"] for s in order[:t]] for t in TIERS}
def write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
def main():
    S = P.scen("train"); byid = {s["id"]: s for s in S}
    A = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(_a.seats or P.outpath("train"))}
    assert all(A.values()) and len(A) == len(S) * len(P.SEATS)
    tiers = nested_tiers(S); stats = {}
    for t, ids in tiers.items():
        for seat in P.SEATS:
            rows = [ex(seat, byid[i], A[(i, seat)]) for i in ids]; write(f"{OUT}/seat/{seat}/tier{t}.jsonl", rows)
        merged = [ex(seat, byid[i], A[(i, seat)]) for i in ids for seat in P.SEATS]
        random.Random(SEED + t).shuffle(merged); write(f"{OUT}/merged/tier{t}.jsonl", merged)
        stats[t] = {"cases": len(ids), "domains": dict(collections.Counter(byid[i]["domain"] for i in ids)),
                    "difficulty": dict(collections.Counter(byid[i]["difficulty"] for i in ids)),
                    "pair_members": sum(1 for i in ids if byid[i].get("pair_id"))}
    # eval: dev = NDEV train-domain groups (loss monitoring only); test = the rest; held-out domains all test
    E = P.scen("eval"); EA = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(P.outpath("eval"))}
    trd = [g for g in groups(E) if g[0]["domain"] not in ("clinical", "biotech")]; random.Random(SEED).shuffle(trd)
    dev, n = [], 0
    for g in trd:
        if n >= NDEV: break
        dev += [s["id"] for s in g]; n += len(g)
    test = [s["id"] for s in E if s["id"] not in set(dev)]; ebyid = {s["id"]: s for s in E}
    write(f"{OUT}/dev.jsonl", [ex(seat, ebyid[i], EA[(i, seat)]) for i in dev for seat in P.SEATS])
    write(f"{OUT}/test.jsonl", [ex(seat, ebyid[i], EA[(i, seat)]) | {"domain": ebyid[i]["domain"]} for i in test for seat in P.SEATS])
    json.dump({"seed": SEED, "tiers": tiers, "dev": dev, "test": test, "stats": stats}, open(f"{OUT}/splits.json", "w"), indent=1)
    # rough token counts (chars/3.7)
    tok = lambda r: sum(len(m["content"]) for m in r["messages"]) / 3.7
    m = C.jsonl_read(f"{OUT}/merged/tier1000.jsonl"); L = sorted(tok(r) for r in m)
    print("tiers", {t: s["cases"] for t, s in stats.items()}, "| dev cases", len(dev), "test cases", len(test))
    print("merged1000 examples", len(m), "tokens/example median %.0f p95 %.0f max %.0f total %.1fM" % (L[len(L)//2], L[int(.95*len(L))], L[-1], sum(L)/1e6))
    for t, s in stats.items(): print(t, s["domains"], s["difficulty"], "pair members", s["pair_members"])
    # round-trip check
    bad = sum(1 for r in m if F.parse(r["messages"][2]["content"])["position"] is None); print("unparseable positions", bad)
if __name__ == "__main__": main()
