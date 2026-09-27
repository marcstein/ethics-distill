#!/usr/bin/env python3
"""Cheap-teacher experiment: does DeepSeek Flash sampled 5x with a Flash selector match Opus as a teacher?
Items = the 120 (case, seat) pairs whose Opus-5 gold analyses were already graded in results/judge_quality.jsonl,
so the gold grades are reused and every comparison is paired.
  python cheap_teacher.py sample    # 5 Flash samples per item (OpenRouter, resumable)
  python cheap_teacher.py select    # Flash picks the best of 5 (blind, shuffled)
  python cheap_teacher.py submit    # Opus 5.5 grades flash_single + flash_best5 (Batch API)
  python cheap_teacher.py collect   # collect the batch
  python cheap_teacher.py report"""
import json, os, sys, random, time, collections, statistics as st, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval"))
import common as C, panel as P, bakeoff as B, judge_quality as J
FLASH = "deepseek/deepseek-v4.1-flash"; K = 5
SAMP = os.path.join(C.ROOT, "results", "cheap_teacher_samples.jsonl")
SEL = os.path.join(C.ROOT, "results", "cheap_teacher_select.jsonl")
OUT = os.path.join(C.ROOT, "results", "cheap_teacher_judge.jsonl")
BATCH = os.path.join(C.ROOT, "results", "cheap_teacher_batch.json")
def items():
    G = [r for r in C.jsonl_read(J.OUT) if r["src"] == "gold_opus5"]
    SC = {s["id"]: s for s in P.scen("eval")}
    return SC, sorted({(r["sid"], r["seat"]) for r in G})
def sample():
    SC, keys = items(); done = collections.Counter((r["sid"], r["seat"]) for r in C.jsonl_read(SAMP) if r["output"])
    todo = [(sid, seat, i) for sid, seat in keys for i in range(K - done[(sid, seat)])]
    if B.spent() > B.ORCAP: raise SystemExit("OpenRouter cap reached")
    print("sampling", len(todo), "Flash calls"); t0 = time.time()
    def one(x):
        sid, seat, _ = x; o = None; tries = 0
        while tries < 3 and not P.valid(o):
            tries += 1
            try: o, _, _, _ = B.call(FLASH, seat, SC[sid])
            except Exception as e: print("err", sid, seat, str(e)[:120])
        return {"sid": sid, "seat": seat, "output": o if P.valid(o) else None, "tries": tries}
    with ThreadPoolExecutor(int(os.environ.get("BAKE_THREADS", "16"))) as ex:
        for f in as_completed([ex.submit(one, x) for x in todo]): C.jsonl_append(SAMP, [f.result()])
    n = sum(1 for r in C.jsonl_read(SAMP) if r["output"])
    print(f"valid samples {n}/{len(keys)*K} in {time.time()-t0:.0f}s | OpenRouter spent ${B.spent():.2f}")
SEL_TOOL = {"type": "function", "function": {"name": "pick", "description": "Record the best analysis.", "parameters": {"type": "object", "properties": {
    "best": {"type": "integer", "description": "1-based index of the best analysis"}, "why": {"type": "string"}}, "required": ["best", "why"]}}}
def select():
    SC, keys = items(); S = collections.defaultdict(list)
    for r in C.jsonl_read(SAMP):
        if r["output"]: S[(r["sid"], r["seat"])].append(r["output"])
    done = {(r["sid"], r["seat"]) for r in C.jsonl_read(SEL)}
    todo = [k for k in keys if k not in done and len(S[k]) >= 2]
    print("selecting for", len(todo), "items")
    def one(k):
        sid, seat = k; cands = S[k][:K]; order = list(range(len(cands))); random.Random(hash(k) & 0xffff).shuffle(order)
        body = "\n\n".join(f"=== ANALYSIS {i+1} ===\n{J.render(cands[j])}" for i, j in enumerate(order))
        sysm = J.RUBRIC.format(name=J.NAME[seat]).replace("grading one analysis", f"comparing {len(cands)} analyses") + "\nPick the single best analysis by these criteria and record its number with the pick tool."
        req = {"model": FLASH, "max_tokens": 600, "temperature": 0, "messages": [{"role": "system", "content": sysm}, {"role": "user", "content": f"{B.V.seat_user(SC[sid])}\n\n{body}"}],
               "tools": [SEL_TOOL], "tool_choice": {"type": "function", "function": {"name": "pick"}}, "reasoning": {"enabled": False}, "usage": {"include": True}}
        rq = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(req).encode(), method="POST",
                                    headers={"Authorization": "Bearer " + B.key(), "Content-Type": "application/json", "X-Title": "ethics-distill"})
        for a in range(4):
            try:
                with urllib.request.urlopen(rq, timeout=170) as r: m = json.loads(r.read()); break
            except Exception as e:
                if a == 3: print("err", k, str(e)[:100]); return None
                time.sleep(4 * (a + 1))
        u = m.get("usage", {}); C.jsonl_append(B.LED, [{"t": time.time(), "model": FLASH + "#select", "in": u.get("prompt_tokens"), "out": u.get("completion_tokens"), "cost": float(u.get("cost") or 0)}])
        try: p = json.loads(m["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]); b = int(p["best"])
        except Exception: return None
        if not 1 <= b <= len(cands): return None
        return {"sid": sid, "seat": seat, "best": order[b - 1], "n": len(cands), "why": p.get("why", "")[:300]}
    with ThreadPoolExecutor(16) as ex:
        for f in as_completed([ex.submit(one, k) for k in todo]):
            r = f.result()
            if r: C.jsonl_append(SEL, [r])
    print("selected", len(C.jsonl_read(SEL)), "| OpenRouter spent $%.2f" % B.spent())
def arms():
    S = collections.defaultdict(list)
    for r in C.jsonl_read(SAMP):
        if r["output"]: S[(r["sid"], r["seat"])].append(r["output"])
    A = {}
    for (sid, seat), c in S.items(): A[("flash_single", sid, seat)] = c[0]
    for r in C.jsonl_read(SEL): A[("flash_best5", r["sid"], r["seat"])] = S[(r["sid"], r["seat"])][r["best"]]
    return A
def submit():
    SC, _ = items(); A = arms(); done = {(r["src"], r["sid"], r["seat"]) for r in C.jsonl_read(OUT)}
    jobs = [k for k in A if k not in done]; C.check_cap(len(jobs) * 0.02)
    reqs = [{"custom_id": f"{src}__{sid}__{seat}", "params": {"model": C.OPUS, "max_tokens": 3000, "system": J.RUBRIC.format(name=J.NAME[seat]), "tools": [J.TOOL], "tool_choice": {"type": "auto"},
             "messages": [{"role": "user", "content": f"{B.V.seat_user(SC[sid])}\n\n=== ANALYSIS (as {J.NAME[seat]}) ===\n{J.render(A[(src, sid, seat)])}\n\nRecord your grade with the grade tool."}]}} for src, sid, seat in jobs]
    b = C.http("POST", "/messages/batches", {"requests": reqs})
    json.dump({"batch": b["id"], "n": len(reqs)}, open(BATCH, "w")); print("submitted", b["id"], len(reqs))
def collect():
    SC, _ = items(); s_ = json.load(open(BATCH)); b = C.http("GET", f"/messages/batches/{s_['batch']}")
    print(b["processing_status"], b["request_counts"])
    if b["processing_status"] != "ended" or s_.get("collected"): return
    ui = uo = 0; rows = []
    for line in C.http("GET", b["results_url"], raw=True).decode().splitlines():
        r = json.loads(line)
        if r["result"]["type"] != "succeeded": continue
        m = r["result"]["message"]; ui += m["usage"]["input_tokens"]; uo += m["usage"]["output_tokens"]; g = C.tool_input(m)
        src, sid, seat = r["custom_id"].split("__")
        if g and "overall" in g: rows.append({"src": src, "sid": sid, "seat": seat, "domain": SC[sid]["domain"], **g})
    C.jsonl_append(OUT, rows); C.record("cheap_teacher_judge", C.OPUS, {"input_tokens": ui, "output_tokens": uo}, batch=True, n=len(rows))
    s_["collected"] = True; json.dump(s_, open(BATCH, "w")); print("collected", len(rows), "| Anthropic $%.2f" % C.spent())
sgn = lambda x: (x > 0) - (x < 0)
def report():
    G = {(r["sid"], r["seat"]): r for r in C.jsonl_read(J.OUT) if r["src"] == "gold_opus5"}
    R = {"gold_opus5": G}
    for r in C.jsonl_read(OUT): R.setdefault(r["src"], {})[(r["sid"], r["seat"])] = r
    print("source | n | overall | facts | fidelity | coherence | clarity | held-out overall")
    for src, rs in R.items():
        v = list(rs.values()); ho = [r for r in v if r["domain"] in ("clinical", "biotech")]
        m = lambda k, rr=v: st.mean(r[k] for r in rr)
        print(f"{src:12s} | {len(v)} | {m('overall'):.2f} | {m('fact_discipline'):.2f} | {m('fidelity'):.2f} | {m('coherence'):.2f} | {m('clarity'):.2f} | {m('overall', ho) if ho else float('nan'):.2f}")
    def paired(a, b):
        ks = [k for k in R.get(a, {}) if k in R.get(b, {})]
        d = [R[a][k]["overall"] - R[b][k]["overall"] for k in ks]
        if len(d) < 2: return
        se = st.stdev(d) / len(d) ** 0.5
        print(f"{a} - {b}: {st.mean(d):+.2f} ±{1.96*se:.2f} (n={len(d)}, {sum(x>0 for x in d)} better / {sum(x<0 for x in d)} worse)")
    paired("flash_best5", "flash_single"); paired("gold_opus5", "flash_best5"); paired("gold_opus5", "flash_single")
    # position agreement across the 5 samples, and of each arm with gold positions
    S = collections.defaultdict(list)
    for r in C.jsonl_read(SAMP):
        if r["output"]: S[(r["sid"], r["seat"])].append(r["output"]["position"])
    unan = sum(1 for v in S.values() if len({sgn(x) for x in v}) == 1); print(f"samples: sign-unanimous items {unan}/{len(S)}")
    gold = {(r["sid"], r["seat"]): r["output"]["position"] for r in C.jsonl_read(P.outpath("eval"))}
    A = arms()
    for src in ("flash_single", "flash_best5"):
        ks = [k for k in A if k[0] == src and (k[1], k[2]) in gold]
        print(f"{src} sign agreement with gold positions: {sum(sgn(A[k]['position'])==sgn(gold[(k[1],k[2])]) for k in ks)/max(1,len(ks)):.2f} (n={len(ks)})")
    L = collections.defaultdict(float)
    for r in C.jsonl_read(B.LED):
        if r["model"].startswith(FLASH) and r["t"] > START: L[r["model"]] += r["cost"]
    print("OpenRouter cost this experiment:", {k: round(v, 3) for k, v in L.items()})
START = 0
if __name__ == "__main__":
    ST = os.path.join(C.ROOT, "results", "cheap_teacher_start.json")
    if not os.path.exists(ST): json.dump({"t": time.time()}, open(ST, "w"))
    START = json.load(open(ST))["t"] - 1
    {"sample": sample, "select": select, "submit": submit, "collect": collect, "report": report}[sys.argv[1]]()
