#!/usr/bin/env python3
"""Seven-seat panel plus contemporary-Kantian annotation via the Batch API. Resumable.
Usage: panel.py submit SET MODEL | poll | collect SET | retry SET | status"""
import json, os, sys, copy, time
from concurrent.futures import ThreadPoolExecutor
import common as C, seat_prompts as V
import kant_modern_prompt as KM
SETS = {"train": ("../data/scenarios/train.jsonl", "../data/seats/train.jsonl"),
        "eval": (["../data/scenarios/eval_train_domains.jsonl", "../data/scenarios/eval_heldout.jsonl"], "../data/eval/seats.jsonl")}
SEATS = list(V.SEATS) + ["KantModern"]
ST = os.path.join(C.ROOT, "results", "panel_state.json")
REQ = V.SEAT_TOOL["input_schema"]["required"]; PROPS = V.SEAT_TOOL["input_schema"]["properties"]
def state(u=None):
    s = json.load(open(ST)) if os.path.exists(ST) else {}
    if u: s.update(u); json.dump(s, open(ST, "w"), indent=1)
    return s
def scen(name):
    src = SETS[name][0]; files = src if isinstance(src, list) else [src]
    return [r for f in files for r in C.jsonl_read(os.path.join(C.ROOT, "distill", f)) if "text" in r]
def system_for(seat): return (KM.MODERN if seat == "KantModern" else V.SEATS[seat]) + "\n" + V.SEAT_COMMON
def params(model, seat, s):
    return {"model": model, "max_tokens": 3500, "system": system_for(seat), "tools": [V.SEAT_TOOL],
            "tool_choice": {"type": "tool", "name": "record_analysis"}, "messages": [{"role": "user", "content": V.seat_user(s)}]}
def repair(o):
    if not isinstance(o, dict): return o
    for k, spec in PROPS.items():
        v = o.get(k)
        if spec["type"] == "string" and isinstance(v, str) and v.lstrip().startswith("<parameter"): o[k] = v[v.index(">") + 1:].replace("</parameter>", "").strip()
        if spec["type"] == "string" and isinstance(v, (list, dict)): o[k] = "\n".join("- " + str(x) for x in (v if isinstance(v, list) else v.values()))
    return o
def valid(o): return bool(o) and all(k in o for k in REQ) and isinstance(o["position"], int) and all(isinstance(o[k], str) for k in REQ if k != "position") and len(o["reasoning"].split()) > 120 and not any(isinstance(v, str) and "<parameter" in v for v in o.values())
def outpath(name): return os.path.join(C.ROOT, "distill", SETS[name][1])
def submit(name, model):
    key = f"{name}"; st = state()
    if key in st: print("already submitted", st[key]); return
    S = scen(name); reqs = [{"custom_id": f"{s['id']}__{seat}", "params": params(model, seat, s)} for s in S for seat in SEATS]
    est = len(reqs) * (2100 * C.PRICE[model][0] + 1750 * C.PRICE[model][1]) / 1e6 * 0.5; C.check_cap(est)
    ids = []
    for i in range(0, len(reqs), 10000):
        b = C.http("POST", "/messages/batches", {"requests": reqs[i:i + 10000]}); ids.append(b["id"])
    state({key: {"batches": ids, "model": model, "n": len(reqs), "est": round(est, 2), "t": time.time()}}); print(name, ids, len(reqs), "requests, est $%.2f" % est)
def poll():
    for k, v in state().items():
        for bid in v["batches"]:
            b = C.http("GET", f"/messages/batches/{bid}"); print(k, bid, b["processing_status"], b["request_counts"])
def collect(name):
    v = state()[name]; out = outpath(name)
    if os.path.exists(out): print("already collected; refusing to overwrite"); return
    rows = []; clean = rep = bad = 0; usage_i = usage_o = 0
    for bid in v["batches"]:
        b = C.http("GET", f"/messages/batches/{bid}")
        if b["processing_status"] != "ended": print(bid, "not ended"); return
        for line in C.http("GET", b["results_url"], raw=True).decode().splitlines():
            r = json.loads(line); sid, seat = r["custom_id"].split("__"); m = r["result"].get("message", {}) if r["result"]["type"] == "succeeded" else {}
            raw = C.tool_input(m) if m else None; ok0 = valid(copy.deepcopy(raw)); o = repair(copy.deepcopy(raw))
            if ok0: clean += 1
            elif valid(o): rep += 1
            else: bad += 1; o = None
            if m: usage_i += m["usage"]["input_tokens"]; usage_o += m["usage"]["output_tokens"]
            rows.append({"sid": sid, "seat": seat, "output": o, "first_pass": "clean" if ok0 else ("repaired" if o else "bad")})
    C.record(f"panel_{name}", v["model"], {"input_tokens": usage_i, "output_tokens": usage_o}, batch=True, n=len(rows))
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{name}: n={len(rows)} clean={clean} repaired={rep} needs_rerun={bad} | spent $%.2f" % C.spent())
def retry(name, limit=60):
    v = state()[name]; out = outpath(name); rows = C.jsonl_read(out); S = {s["id"]: s for s in scen(name)}
    bad = [i for i, r in enumerate(rows) if not r["output"]][:limit]; t0 = time.time()
    def run(i):
        r = rows[i]
        for _ in range(3):
            if time.time() - t0 > 100: return i, None
            m = C.message(f"panel_{name}_retry", params(v["model"], r["seat"], S[r["sid"]])); o = repair(C.tool_input(m))
            if valid(o): return i, o
        return i, None
    with ThreadPoolExecutor(30) as ex:
        for i, o in ex.map(run, bad):
            if o: rows[i]["output"] = o; rows[i]["retried"] = True
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, "still bad:", sum(1 for r in rows if not r["output"]), "| spent $%.2f" % C.spent())
def status():
    for name in SETS:
        out = outpath(name)
        if os.path.exists(out):
            rows = C.jsonl_read(out); print(name, len(rows), "rows,", sum(1 for r in rows if r["output"]), "valid")
    print("spent $%.2f" % C.spent())
if __name__ == "__main__":
    a = sys.argv[1:]
    {"submit": lambda: submit(a[1], a[2]), "poll": poll, "collect": lambda: collect(a[1]), "retry": lambda: retry(a[1]), "status": status}[a[0]]()
