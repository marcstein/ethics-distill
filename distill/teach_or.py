#!/usr/bin/env python3
"""Generate the full seat panel for a scenario set with an OpenRouter teacher. Resumable, saves each result as it lands.
  nohup python3 teach_or.py train deepseek/deepseek-v4.1-flash > ../results/teach_flash.log 2>&1 &"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as C, panel as P, bakeoff as B
name, model = sys.argv[1], sys.argv[2]; tag = model.split("/")[1]
OUT = os.path.join(C.ROOT, "data", "seats", f"{name}_{tag}.jsonl"); os.makedirs(os.path.dirname(OUT), exist_ok=True)
CAP = float(os.environ.get("OR_CAP", "40")); THREADS = int(os.environ.get("THREADS", "32"))
S = P.scen(name)
def one(s, seat):
    o = None; tries = 0
    while tries < 3 and not P.valid(o):
        tries += 1
        try: o, _, _, _ = B.call(model, seat, s)
        except Exception as e: print("err", s["id"], seat, str(e)[:120], flush=True); time.sleep(5)
    return {"sid": s["id"], "seat": seat, "output": o if P.valid(o) else None, "tries": tries, "teacher": model}
for rnd in range(3):
    done = {(r["sid"], r["seat"]) for r in C.jsonl_read(OUT) if r["output"]}
    todo = [(s, seat) for s in S for seat in P.SEATS if (s["id"], seat) not in done]
    print(time.strftime("%H:%M:%S"), f"round {rnd}: {len(todo)} to do, {len(done)} done, OpenRouter spent ${B.spent():.2f}", flush=True)
    if not todo: break
    with ThreadPoolExecutor(THREADS) as ex:
        futs = [ex.submit(one, s, seat) for s, seat in todo]
        for i, f in enumerate(as_completed(futs)):
            r = f.result()
            if r["output"]: C.jsonl_append(OUT, [r])
            if i % 200 == 0: print(time.strftime("%H:%M:%S"), i, "/", len(todo), f"${B.spent():.2f}", flush=True)
            if B.spent() > CAP: print("CAP reached"); os._exit(1)
done = {(r["sid"], r["seat"]) for r in C.jsonl_read(OUT) if r["output"]}
print(time.strftime("%H:%M:%S"), "DONE", len(done), "/", len(S) * len(P.SEATS), f"${B.spent():.2f}", flush=True)
