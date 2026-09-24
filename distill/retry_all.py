"""Synchronous retry of every invalid row in a seats file, in checkpointed chunks (background-safe)."""
import json, sys, time
from concurrent.futures import ThreadPoolExecutor
import common as C, panel as P
name = sys.argv[1] if len(sys.argv) > 1 else "train"; CHUNK = int(sys.argv[2]) if len(sys.argv) > 2 else 48; MAXCH = int(sys.argv[3]) if len(sys.argv) > 3 else 1
v = P.state()[name]; out = P.outpath(name); S = {s["id"]: s for s in P.scen(name)}
per = (2100 * C.PRICE[v["model"]][0] + 1750 * C.PRICE[v["model"]][1]) / 1e6
def run(args):
    i, r = args
    for _ in range(3):
        try:
            o = P.repair(C.tool_input(C.message(f"panel_{name}_syncretry", P.params(v["model"], r["seat"], S[r["sid"]]))))
            if P.valid(o): return i, o
        except Exception as e: print("err", r["sid"], r["seat"], str(e)[:120], flush=True); time.sleep(5)
    return i, None
done = 0
while done < MAXCH:
    done += 1
    rows = C.jsonl_read(out); bad = [(i, r) for i, r in enumerate(rows) if not r["output"]]
    if not bad: break
    chunk = bad[:CHUNK]; C.check_cap(len(chunk) * per)
    with ThreadPoolExecutor(CHUNK) as ex: res = list(ex.map(run, chunk))
    rows = C.jsonl_read(out); fixed = 0
    for i, o in res:
        if o and not rows[i]["output"]: rows[i]["output"] = o; rows[i]["retried"] = "sync"; fixed += 1
    with open(out + ".tmp", "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    import os; os.replace(out + ".tmp", out)
    left = sum(1 for r in rows if not r["output"])
    print(time.strftime("%H:%M:%S"), "fixed", fixed, "of", len(chunk), "| still bad", left, "| spent $%.2f" % C.spent(), flush=True)
    if fixed == 0: print("no progress; stopping"); break
print("DONE", name, "still bad:", sum(1 for r in C.jsonl_read(out) if not r["output"]), flush=True)
