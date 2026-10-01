#!/usr/bin/env python3
"""Eight-seat Opus panel (Batch API) on a small hand-voted case set. Usage: vote_panel.py submit SET | poll | collect SET | show SET
SET names a file data/scenarios/<SET>.jsonl with id/text/question; seats output -> results/vote_panel_<SET>.jsonl; state in results/vote_panel_state.json."""
import json, os, sys, copy, time, collections, statistics as st
import common as C, panel as P
ST = os.path.join(C.ROOT, "results", "vote_panel_state.json")
def state(u=None):
    s = json.load(open(ST)) if os.path.exists(ST) else {}
    if u: s.update(u); json.dump(s, open(ST, "w"), indent=1)
    return s
def scen(name): return [r for r in C.jsonl_read(os.path.join(C.ROOT, "data", "scenarios", name + ".jsonl")) if "text" in r]
def out(name): return os.path.join(C.ROOT, "results", f"vote_panel_{name}.jsonl")
def submit(name, model=C.OPUS):
    if name in state(): print("already submitted", state()[name]); return
    S = scen(name); reqs = [{"custom_id": f"{s['id']}__{seat}", "params": P.params(model, seat, s)} for s in S for seat in P.SEATS]
    est = len(reqs) * (2100 * C.PRICE[model][0] + 1750 * C.PRICE[model][1]) / 1e6 * 0.5; C.check_cap(est)
    b = C.http("POST", "/messages/batches", {"requests": reqs}); state({name: {"batches": [b["id"]], "model": model, "n": len(reqs), "est": round(est, 2), "t": time.time()}})
    print(name, b["id"], len(reqs), "requests, est $%.2f" % est)
def poll():
    for k, v in state().items():
        for bid in v["batches"]: b = C.http("GET", f"/messages/batches/{bid}"); print(k, bid, b["processing_status"], b["request_counts"])
def collect(name):
    v = state()[name]
    if os.path.exists(out(name)): print("already collected"); return
    rows = []; ui = uo = 0
    for bid in v["batches"]:
        b = C.http("GET", f"/messages/batches/{bid}")
        if b["processing_status"] != "ended": print(bid, "not ended"); return
        for line in C.http("GET", b["results_url"], raw=True).decode().splitlines():
            r = json.loads(line); sid, seat = r["custom_id"].split("__"); m = r["result"].get("message", {}) if r["result"]["type"] == "succeeded" else {}
            o = P.repair(copy.deepcopy(C.tool_input(m))) if m else None
            if not P.valid(o): o = None
            if m: ui += m["usage"]["input_tokens"]; uo += m["usage"]["output_tokens"]
            rows.append({"sid": sid, "seat": seat, "output": o})
    C.record(f"vote_panel_{name}", v["model"], {"input_tokens": ui, "output_tokens": uo}, batch=True, n=len(rows))
    with open(out(name), "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(rows), "rows,", sum(1 for r in rows if r["output"]), "valid; spent $%.2f" % C.spent()); show(name)
def show(name):
    R = collections.defaultdict(dict)
    for r in C.jsonl_read(out(name)):
        if r["output"]: R[r["sid"]][r["seat"]] = r["output"]
    for s in scen(name):
        o = R.get(s["id"], {}); yes = [k for k, v in o.items() if v["position"] > 0]; no = [k for k, v in o.items() if v["position"] < 0]; z = [k for k, v in o.items() if v["position"] == 0]
        ys = ", ".join("%s +%d" % (k, o[k]["position"]) for k in yes); ns = ", ".join("%s %d" % (k, o[k]["position"]) for k in no)
        print("%s: YES %d (%s) | NO %d (%s)%s" % (s["id"], len(yes), ys, len(no), ns, (" | 0: " + ", ".join(z)) if z else ""))
if __name__ == "__main__":
    a = sys.argv[1:]; {"submit": lambda: submit(*a[1:]), "poll": poll, "collect": lambda: collect(a[1]), "show": lambda: show(a[1])}[a[0]]()
