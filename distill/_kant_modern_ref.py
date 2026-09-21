#!/usr/bin/env python3
"""Modern-Kantian seat on the 22 v3 cases, Sonnet 5, revised (v3) prompt. Resumable. Compares with historical Kant (v3) and the rest of the v3 panel."""
import json, os, sys, time, copy
from concurrent.futures import ThreadPoolExecutor
import check20 as C, pilot as R, prompts_v3 as V
MODERN = """You reason as a contemporary Kantian would: the constructivist reading of Kant developed by Christine Korsgaard, Onora O'Neill and Barbara Herman. Ground your analysis in the Groundwork and the Metaphysics of Morals as that tradition reads them.
Method: identify the maxim of the proposed action and test whether everyone affected could in principle share it, and whether the action treats any person merely as a means, that is, in a way to which they could not possibly consent. Respect for rational agency is the core; a constraint against using persons is not weighed against benefits. Distinguish perfect from imperfect duties and duties of right from duties of virtue. Where obligations appear to collide, do not deny the collision: work out which ground of obligation is stronger here and say what remains owed after the choice (a duty of repair, acknowledgment or regret).
On deception: the wrong of a lie lies in using the hearer's trust as a means. A person who has forfeited any claim to the truth (an aggressor seeking a victim, a fraudster) is not wronged by a false statement made to defeat their wrongdoing; the constraint still binds fully against deception for gain or convenience, and against manipulation that bypasses another's reason.
Where the historical Kant would have answered differently (for example on lying to an aggressor, or on any absolute prohibition you relax), say so in one sentence: state his position and that this seat departs from it.
Avoid the caricature in both directions: neither the rigorist who applies rules regardless of persons, nor a consequentialist in Kantian vocabulary. Give a determinate answer."""
OUT = os.path.join(R.HERE, "results", "v3_seats_kant_modern.jsonl")
def params(s):
    return {"model": C.MODEL, "max_tokens": 3500, "system": MODERN + "\n" + V.SEAT_COMMON, "tools": [V.SEAT_TOOL],
            "tool_choice": {"type": "tool", "name": "record_analysis"}, "messages": [{"role": "user", "content": V.seat_user(s)}]}
def load(): return [json.loads(l) for l in open(OUT)] if os.path.exists(OUT) else []
if sys.argv[1] == "run":
    done = {r["sid"] for r in load()}; jobs = [s for s in C.scen() if s["id"] not in done]; t0 = time.time()
    def run(s):
        for _ in range(3):
            if time.time() - t0 > 100: return None
            m = R.http("POST", "/messages", params(s), timeout=70); o, _ = C.repair(C.raw_input(m))
            if C.valid(o): return {"sid": s["id"], "seat": "KantModern", "output": o, "usage": m["usage"]}
        return None
    with ThreadPoolExecutor(22) as ex: new = [r for r in ex.map(run, jobs) if r]
    with open(OUT, "a") as f:
        for r in new: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("done", len(done) + len(new), "of", len(C.scen()))
else:
    km = {r["sid"]: r["output"] for r in load()}; v3 = {(r["sid"], r["seat"]): r["output"] for r in C.load()}
    import statistics as st
    sign = lambda x: (x > 0) - (x < 0)
    rows = []
    for s in C.scen():
        sid = s["id"]
        if sid not in km: continue
        m, h = km[sid]["position"], v3[(sid, "Kant")]["position"]
        others = [v3[(sid, x)]["position"] for x in V.SEATS if x != "Kant"]; med = st.median(others)
        rows.append((sid, h, m, med))
    print("sid    historical  modern  median-of-other-6   note")
    for sid, h, m, med in rows:
        note = ""
        if sign(h) != sign(m): note = "SIGN DIFFERS"
        elif abs(h - m) >= 1: note = "shift"
        print(f"{sid:6s} {h:+d}          {m:+d}       {med:+.1f}            {note}")
    print()
    print("cases where the two Kants differ in sign:", sum(1 for _, h, m, _ in rows if sign(h) != sign(m)), "of", len(rows))
    print("mean |historical - modern|:", round(st.mean(abs(h - m) for _, h, m, _ in rows), 2))
    hd = sum(1 for _, h, m, med in rows if med != 0 and sign(h) == -sign(med)); md = sum(1 for _, h, m, med in rows if med != 0 and sign(m) == -sign(med))
    print(f"dissents from the other six (opposite sign to their median): historical {hd}, modern {md}")
    print("mean |distance from median of other six|: historical", round(st.mean(abs(h - med) for _, h, m, med in rows), 2), " modern", round(st.mean(abs(m - med) for _, h, m, med in rows), 2))
    for sid, h, m, med in rows:
        if sign(h) != sign(m) or abs(h - m) >= 2:
            print(f"\n--- {sid}: {C.SC[sid]['question']}\n  historical ({h:+d}): {v3[(sid,'Kant')]['verdict'][:300]}\n  modern     ({m:+d}): {km[sid]['verdict'][:300]}")
    flagged = sum(1 for o in km.values() if any(w in (o["reasoning"] + o["verdict"]).lower() for w in ("kant himself", "historical kant", "kant's own", "departs", "kant would have")))
    print("\nanalyses that flag a departure from the historical Kant:", flagged, "of", len(km))
    u = [r["usage"] for r in load()]; print("cost $", round(sum(x["input_tokens"] * 2 + x["output_tokens"] * 10 for x in u) / 1e6, 2))
