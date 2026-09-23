"""Shared: API client, spend ledger with hard cap, batch helpers. Stdlib only."""
import json, os, re, time, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.anthropic.com/v1"
PRICE = {"claude-sonnet-5": (2, 10), "claude-opus-5": (5, 25), "claude-opus-5-5": (4, 20), "claude-haiku-4-5-20251001": (1, 5)}
LEDGER = os.path.join(ROOT, "results", "spend_ledger.jsonl")
OPUS = "claude-opus-5-5"  # default for judging and any new Opus work; the eval gold set (data/eval/seats.jsonl) was generated on claude-opus-5 before this switch

def env(k, default=None):
    for line in open(os.path.join(ROOT, ".env")):
        m = re.match(rf"\s*{k}\s*=\s*(.+)", line)
        if m: return m.group(1).strip().strip('"').strip("'")
    return default

def spent():
    if not os.path.exists(LEDGER): return 0.0
    return sum(json.loads(l)["usd"] for l in open(LEDGER))

def record(stage, model, usage, batch=False, n=1):
    i, o = usage["input_tokens"], usage["output_tokens"]; pin, pout = PRICE[model]
    usd = (i * pin + o * pout) / 1e6 * (0.5 if batch else 1.0)
    with open(LEDGER, "a") as f: f.write(json.dumps({"t": time.time(), "stage": stage, "model": model, "in": i, "out": o, "batch": batch, "n": n, "usd": round(usd, 5)}) + "\n")
    return usd

def check_cap(planned_usd):
    cap = float(env("SPEND_CAP", "200")); s = spent()
    if s + planned_usd > cap: raise SystemExit(f"spend cap: ${s:.2f} spent + ${planned_usd:.2f} planned > ${cap:.0f}")

def http(method, path, body=None, raw=False, timeout=170):
    req = urllib.request.Request(path if path.startswith("http") else API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"x-api-key": env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01", "content-type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read(); return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code in (429, 500, 529) and attempt < 4: time.sleep(3 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")

def message(stage, params, batch=False):
    m = http("POST", "/messages", params); record(stage, params["model"], m["usage"], batch); return m

def tool_input(m):
    for b in m.get("content", []):
        if b.get("type") == "tool_use": return b["input"]
    return None

def text_of(m): return "".join(b.get("text", "") for b in m.get("content", []) if b.get("type") == "text")

def jsonl_read(p): return [json.loads(l) for l in open(p)] if os.path.exists(p) else []
def jsonl_append(p, rows):
    with open(p, "a") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
