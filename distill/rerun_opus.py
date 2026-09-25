"""Re-run the Opus 5.5 panel on the v2 sample to measure gold stability."""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as C, panel as P
cells = C.jsonl_read(os.path.join(C.ROOT, "data", "scenarios", "r2_sample20v2.jsonl")); out = os.path.join(C.ROOT, "results", "r2_sample20v2_opus_rerun.jsonl")
done = {(r["sid"], r["seat"]) for r in C.jsonl_read(out)}
todo = [(c, s) for c in cells for s in P.SEATS if (c["id"], s) not in done]; C.check_cap(len(todo) * 0.05)
def one(c, s):
    for a in range(4):
        try:
            o = P.repair(C.tool_input(C.message("r2_opus_rerun", P.params(C.OPUS, s, c))))
            if P.valid(o): return {"sid": c["id"], "seat": s, "output": o}
        except Exception as e:
            import time; time.sleep(10 * (a + 1))
    return None
with ThreadPoolExecutor(10) as ex:
    for f in as_completed([ex.submit(one, c, s) for c, s in todo]):
        r = f.result()
        if r: C.jsonl_append(out, [r])
