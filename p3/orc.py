"""Minimal OpenRouter client for Phase 3 (Flash by default). Logs cost to results/openrouter_ledger.jsonl and enforces OR_CAP."""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distill"))
import common as C
FLASH = "deepseek/deepseek-v4.1-flash"
LED = os.path.join(C.ROOT, "results", "openrouter_ledger.jsonl")
CAP = float(os.environ.get("OR_CAP", "80"))
def key(): return C.env("OPENROUTER_API_KEY")
def spent(): return sum(r["cost"] for r in C.jsonl_read(LED))
def chat(system, user, tool=None, model=FLASH, temperature=0.7, max_tokens=2500, tag="p3"):
    """Returns (parsed tool input or text, usage). tool = {"name", "description", "parameters"} forces a JSON answer."""
    if spent() > CAP: raise SystemExit(f"OpenRouter cap ${CAP} reached (${spent():.2f})")
    body = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "reasoning": {"enabled": False}, "usage": {"include": True},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if tool: body["tools"] = [{"type": "function", "function": tool}]; body["tool_choice"] = {"type": "function", "function": {"name": tool["name"]}}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json", "X-Title": "ethics-distill-p3"})
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=170) as r: m = json.loads(r.read()); break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code in (429, 500, 502, 503) and a < 3: time.sleep(4 * (a + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
        except Exception as e:
            if a < 3: time.sleep(4 * (a + 1)); continue
            raise
    u = m.get("usage", {})
    C.jsonl_append(LED, [{"t": time.time(), "model": model + "#" + tag, "in": u.get("prompt_tokens"), "out": u.get("completion_tokens"), "cost": float(u.get("cost") or 0)}])
    msg = m["choices"][0]["message"]
    if tool:
        for tc in msg.get("tool_calls") or []:
            try: return json.loads(tc["function"]["arguments"]), u
            except Exception: pass
        return None, u
    return (msg.get("content") or "").strip(), u
def pmap(fn, items, threads=8):
    """Parallel map that keeps order; exceptions become None (caller retries)."""
    from concurrent.futures import ThreadPoolExecutor
    def safe(x):
        try: return fn(x)
        except Exception as e: print("err", str(e)[:160], file=sys.stderr); return None
    with ThreadPoolExecutor(threads) as ex: return list(ex.map(safe, items))
