"""Re-run the Flash panel on the v2 sample (same prompts) to see whether seat disagreements are stable or sampling noise."""
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as C, panel as P, bakeoff as B
cells = C.jsonl_read(os.path.join(C.ROOT, "data", "scenarios", "r2_sample20v2.jsonl")); out = os.path.join(C.ROOT, "results", "r2_sample20v2_flash_rerun.jsonl")
done = {(r["sid"], r["seat"]) for r in C.jsonl_read(out)}
def one(c, s):
    for _ in range(2):
        try:
            o = B.call("deepseek/deepseek-v4.1-flash", s, c)[0]
            if P.valid(o): return {"sid": c["id"], "seat": s, "output": o}
        except Exception as e: pass
    return None
with ThreadPoolExecutor(32) as ex:
    for f in as_completed([ex.submit(one, c, s) for c in cells for s in P.SEATS if (c["id"], s) not in done]):
        r = f.result()
        if r: C.jsonl_append(out, [r])
