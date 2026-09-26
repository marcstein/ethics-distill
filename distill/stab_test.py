"""Flash stability test on the v2 sample: runs tagged t0a,t0b (temperature 0) and m3,m4,m5,m6 (temperature 0.7).
Together with the two existing 0.7 runs (m1 = original panel, m2 = rerun) this gives two independent median-of-3 labels."""
import os, sys, json, statistics as st, collections
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as C, panel as P, bakeoff as B
cells = C.jsonl_read(os.path.join(C.ROOT, "data", "scenarios", "r2_sample20v2.jsonl")); OUT = os.path.join(C.ROOT, "results", "r2_stab.jsonl")
RUNS = {"t0a": 0.0, "t0b": 0.0, "m3": 0.7, "m4": 0.7, "m5": 0.7, "m6": 0.7}
def run():
    done = {(r["sid"], r["seat"], r["run"]) for r in C.jsonl_read(OUT)}
    jobs = [(c, s, k) for c in cells for s in P.SEATS for k in RUNS if (c["id"], s, k) not in done]
    def one(c, s, k):
        for _ in range(3):
            try:
                o = B.call("deepseek/deepseek-v4.1-flash", s, c, RUNS[k])[0]
                if P.valid(o): return {"sid": c["id"], "seat": s, "run": k, "position": o["position"]}
            except Exception: pass
    with ThreadPoolExecutor(48) as ex:
        for f in as_completed([ex.submit(one, *j) for j in jobs]):
            r = f.result()
            if r: C.jsonl_append(OUT, [r])
    print("left", len(jobs) - sum(1 for _ in []), "| OpenRouter $%.2f" % B.spent())
def report():
    seats = [s for s in P.SEATS if s != "KantModern"]; R = collections.defaultdict(dict)
    for r in C.jsonl_read(os.path.join(C.ROOT, "results", "r2_sample20v2_panels.jsonl")):
        if r["output"]: R["m1" if r["teacher"] == "flash" else "o1"][(r["sid"], r["seat"])] = r["output"]["position"]
    for r in C.jsonl_read(os.path.join(C.ROOT, "results", "r2_sample20v2_flash_rerun.jsonl")): R["m2"][(r["sid"], r["seat"])] = r["output"]["position"]
    for r in C.jsonl_read(os.path.join(C.ROOT, "results", "r2_sample20v2_opus_rerun.jsonl")): R["o2"][(r["sid"], r["seat"])] = r["output"]["position"]
    for r in C.jsonl_read(OUT): R[r["run"]][(r["sid"], r["seat"])] = r["position"]
    med = lambda runs: {k: int(st.median([R[x][k] for x in runs])) for k in R[runs[0]] if all(k in R[x] for x in runs)}
    L = {"flash t=0.7 single": (R["m1"], R["m2"]), "flash t=0 single": (R["t0a"], R["t0b"]),
         "flash median of 3": (med(["m1", "m3", "m5"]), med(["m2", "m4", "m6"])), "opus 5.5 single": (R["o1"], R["o2"])}
    O = {k: (R["o1"][k] + R["o2"][k]) / 2 for k in R["o1"] if k in R["o2"]}
    sg = lambda x: (x > 0) - (x < 0)
    print("method | same sign | exact | splits recur | same dissenters | sign agreement with Opus 5.5 (mean of 2)")
    for name, (a, b) in L.items():
        ks = [k for k in a if k in b and k[1] in seats]
        ids = sorted({k[0] for k in ks}); full = [i for i in ids if all((i, s) in a and (i, s) in b for s in seats)]
        sp = lambda D, i: (lambda ps: any(p > 0 for p in ps) and any(p < 0 for p in ps))([D[(i, s)] for s in seats])
        s1 = sum(sp(a, i) for i in full); both = sum(sp(a, i) and sp(b, i) for i in full)
        same = tot = 0
        for i in full:
            ma = sg(sum(sg(a[(i, s)]) for s in seats)); mb = sg(sum(sg(b[(i, s)]) for s in seats))
            da = {s for s in seats if sg(a[(i, s)]) != ma}; db = {s for s in seats if sg(b[(i, s)]) != mb}
            if da or db: tot += 1; same += da == db
        agree = [sg(a[k]) == sg(O[k]) for k in ks if k in O and O[k] != 0]
        print(f"{name:20s} | {sum(sg(a[k])==sg(b[k]) for k in ks)/len(ks):.2f} | {sum(a[k]==b[k] for k in ks)/len(ks):.2f} | {both}/{s1} | {same}/{tot} | {sum(agree)/len(agree):.2f}")
if __name__ == "__main__": {"run": run, "report": report}[sys.argv[1]]()
