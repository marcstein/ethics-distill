#!/usr/bin/env python3
"""Open-weights teacher bake-off via OpenRouter on the 50 check55 cases (same prompts, same schema).
  python bakeoff.py run MODEL [N]   (chunked, resumable)   |   python bakeoff.py report"""
import json, os, sys, time, re, urllib.request, urllib.error, collections, statistics as st
from concurrent.futures import ThreadPoolExecutor
import common as C, panel as P, seat_prompts as V, check55 as K
ORCAP = 45.0; LED = os.path.join(C.ROOT, "results", "openrouter_ledger.jsonl")
MODELS = ["deepseek/deepseek-v4-pro", "deepseek/deepseek-v4.1-flash", "mistralai/mistral-large-2512", "z-ai/glm-5.2"]
def key(): return [l.split("=", 1)[1].strip() for l in open(os.path.join(C.ROOT, ".env")) if l.startswith("OPENROUTER_API_KEY=")][0]
def spent(): return sum(r["cost"] for r in C.jsonl_read(LED))
def out(m): return os.path.join(C.ROOT, "results", "bakeoff_" + m.split("/")[1] + ".jsonl")
TOOL = {"type": "function", "function": {"name": V.SEAT_TOOL["name"], "description": V.SEAT_TOOL["description"], "parameters": V.SEAT_TOOL["input_schema"]}}
def call(model, seat, s, temperature=0.7, reasoning=None, tool_choice=None):
    body = {"model": model, "max_tokens": 3500, "temperature": temperature, "messages": [{"role": "system", "content": P.system_for(seat)}, {"role": "user", "content": V.seat_user(s)}],
            "tools": [TOOL], "tool_choice": tool_choice or {"type": "function", "function": {"name": "record_analysis"}},
            "reasoning": reasoning or {"enabled": False}, "usage": {"include": True}}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json", "X-Title": "ethics-distill"})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=170) as r: m = json.loads(r.read()); break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503) and a < 3: time.sleep(4 * (a + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
    u = m.get("usage", {}); C.jsonl_append(LED, [{"t": time.time(), "model": model, "in": u.get("prompt_tokens"), "out": u.get("completion_tokens"), "cost": float(u.get("cost") or 0)}])
    ch = m["choices"][0]; msg = ch["message"]; o = None
    for tc in msg.get("tool_calls") or []:
        try: o = json.loads(tc["function"]["arguments"])
        except Exception: o = None
    if isinstance(o, dict) and isinstance(o.get("position"), str) and re.fullmatch(r"\s*[+-]?\d\s*", o["position"]): o["position"] = int(o["position"])
    return P.repair(o) if isinstance(o, dict) else None, (msg.get("content") or "")[:500], ch.get("finish_reason"), u
def run(model, n=40):
    done = {(r["sid"], r["seat"]) for r in C.jsonl_read(out(model)) if r["output"]}
    todo = [(src, s, seat) for src, s in K.cases() for seat in P.SEATS if (s["id"], seat) not in done][:n]
    if spent() > ORCAP: raise SystemExit(f"OpenRouter cap ${ORCAP} reached")
    t0 = time.time()
    def one(x):
        src, s, seat = x; o = txt = fin = None; tries = 0; err = None
        while tries < 2 and not P.valid(o):
            tries += 1
            try: o, txt, fin, _ = call(model, seat, s)
            except Exception as e: err = str(e)[:200]
        return {"src": src, "sid": s["id"], "seat": seat, "output": o if P.valid(o) else None, "raw_partial": None if P.valid(o) else o,
                "text": txt, "finish": fin, "tries": tries, "err": err, "sec": round(time.time() - t0)}
    from concurrent.futures import as_completed
    res = []
    with ThreadPoolExecutor(int(os.environ.get("BAKE_THREADS", "20"))) as ex:
        for f in as_completed([ex.submit(one, x) for x in todo]):
            r = f.result(); res.append(r); C.jsonl_append(out(model), [r])   # save as each finishes, so a timeout loses nothing
    left = 400 - len(done) - sum(1 for r in res if r["output"])
    print(f"{model}: did {len(todo)} ({sum(1 for r in res if r['output'])} valid) in {time.time()-t0:.0f}s | left {left} | OpenRouter spent ${spent():.2f}")
    for r in res[:3]:
        if not r["output"]: print("  fail", r["sid"], r["seat"], r["finish"], r["err"], repr((r["text"] or "")[:150]), list((r["raw_partial"] or {}).keys()))
sgn = lambda x: (x > 0) - (x < 0)
def report():
    O55 = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(K.OUT) if r["output"]}
    L = collections.defaultdict(list)
    for r in C.jsonl_read(LED): L[r["model"]].append(r)
    for model in MODELS + ["opus-5.5"]:
        if model == "opus-5.5": R = {k: {"output": v, "tries": 1} for k, v in O55.items()}
        else:
            if not os.path.exists(out(model)): continue
            R = {}
            for r in C.jsonl_read(out(model)): R[(r["sid"], r["seat"])] = r
        O = {k: r["output"] for k, r in R.items() if r["output"]}
        pairs = [(O[k]["position"], O55[k]["position"]) for k in O if k in O55]
        ids = sorted({k[0] for k in O}); full = [i for i in ids if all((i, s) in O for s in P.SEATS)]
        seats = [s for s in P.SEATS if s != "KantModern"]
        splits = sum(1 for i in full if any(O[(i, s)]["position"] > 0 for s in seats) and any(O[(i, s)]["position"] < 0 for s in seats))
        sd = st.mean(st.pstdev([O[(i, s)]["position"] for s in seats]) for i in full) if full else float("nan")
        words = st.median(len(O[k]["reasoning"].split()) for k in O) if O else 0
        first = sum(1 for r in R.values() if r["output"] and r.get("tries") == 1) / max(1, len(R))
        cost = sum(x["cost"] for x in L[model]); ncall = len(L[model])
        print(f"{model:32s} valid {len(O)}/{len(R)} first-try {first:.2f} | vs Opus5.5 sign {sum(sgn(a)==sgn(b) for a,b in pairs)/max(1,len(pairs)):.2f} "
              f"exact {sum(a==b for a,b in pairs)/max(1,len(pairs)):.2f} | splits {splits}/{len(full)} sd {sd:.2f} | reasoning words {words:.0f}"
              + (f" | ${cost:.2f} for {ncall} calls = ${cost/max(1,ncall)*8:.4f}/case" if ncall else ""))
if __name__ == "__main__":
    if sys.argv[1] == "run": run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 40)
    else: report()
