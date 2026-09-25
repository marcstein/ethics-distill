#!/usr/bin/env python3
"""Blind pairwise judge (Opus 5.5): candidate analysis vs Opus 5.5 analysis of the same case and seat.
  python judge_bakeoff.py run MODEL [N]  |  report"""
import json, os, sys, random, time, collections
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as C, panel as P, seat_prompts as V, check55 as K, bakeoff as B
OUT = os.path.join(C.ROOT, "results", "judge_bakeoff.jsonl")
RUBRIC = """You are judging two analyses of the same moral case, each written as if by the same philosopher on a panel ({seat}). Judge which is the better analysis on these criteria, in order of weight:
1. Fact discipline: relies only on facts the case states; argues conditionally where facts are open; invents no facts, motives or consequences.
2. Fidelity: reasons the way this philosopher's framework actually works, applied to these facts rather than summarized.
3. Coherence: the position and verdict follow from the reasoning; the objection is real and answered.
4. Clarity: plain, precise prose without padding.
Ignore length except where it hurts clarity. Do not prefer an analysis because you agree with its conclusion."""
JTOOL = {"name": "judgment", "description": "Record the judgment.", "input_schema": {"type": "object", "properties": {
    "invented_facts_A": {"type": "string", "description": "Any facts A adds that the case does not state, or 'none'."},
    "invented_facts_B": {"type": "string", "description": "Any facts B adds that the case does not state, or 'none'."},
    "rationale": {"type": "string", "description": "Two to four sentences comparing them on the criteria."},
    "winner": {"type": "string", "enum": ["A", "B", "tie"]}}, "required": ["invented_facts_A", "invented_facts_B", "rationale", "winner"]}}
def fmt(o): return "\n".join(f"{k}: {o.get(k)}" for k in ["action_rated", "established_facts", "open_facts", "reasoning", "strongest_objection", "position", "verdict", "would_change_if"])
def msg_retry(p):
    for a in range(8):
        try: return C.message("judge_bakeoff", p)
        except RuntimeError as e:
            if "429" in str(e): time.sleep(15 + 10 * a); continue
            raise
    return {}
def run(model, n=60, refname="opus55"):
    cand = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(B.out(model)) if r["output"]} if model != "sonnet" else {}
    if refname == "opus55": ref = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(K.OUT) if r["output"]}
    else:
        tr = {s["id"] for src, s in K.cases() if src == "train"}
        ref = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(P.outpath("train")) if r["sid"] in tr}
        if model == "sonnet": cand = {(r["sid"], r["seat"]): r["output"] for r in C.jsonl_read(K.OUT) if r["output"] and r["sid"] in tr}; ref, cand = cand, ref
    done = {(r["sid"], r["seat"]) for r in C.jsonl_read(OUT) if r["model"] == model and r.get("ref", "opus55") == refname}
    S = {s["id"]: s for _, s in K.cases()}
    keys = sorted(k for k in cand if k in ref and k[1] != "KantModern"); random.Random(7).shuffle(keys)
    todo = [k for k in keys[:n] if k not in done]; C.check_cap(len(todo) * 0.03)
    def one(k):
        s = S[k[0]]; flip = random.Random(hash(k) & 0xffff).random() < 0.5
        A, Bo = (ref[k], cand[k]) if flip else (cand[k], ref[k])
        p = {"model": C.OPUS, "max_tokens": 1200, "system": RUBRIC.format(seat=k[1]), "tools": [JTOOL], "tool_choice": {"type": "auto"},
             "messages": [{"role": "user", "content": f"{V.seat_user(s)}\n\n=== ANALYSIS A ===\n{fmt(A)}\n\n=== ANALYSIS B ===\n{fmt(Bo)}\n\nRecord your judgment with the judgment tool."}]}
        j = C.tool_input(msg_retry(p)) or {}
        w = j.get("winner"); cw = "tie" if w == "tie" else ("cand" if (w == "B") == flip else "opus55") if w in ("A", "B") else None
        inv_c = j.get("invented_facts_B" if flip else "invented_facts_A"); inv_r = j.get("invented_facts_A" if flip else "invented_facts_B")
        return {"model": model, "ref": refname, "sid": k[0], "seat": k[1], "winner": cw, "cand_invented": inv_c, "ref_invented": inv_r, "rationale": j.get("rationale")}
    with ThreadPoolExecutor(8) as ex:
        for f in as_completed([ex.submit(one, k) for k in todo]): C.jsonl_append(OUT, [f.result()])
    print(model, "judged", len(todo), "| Anthropic spent $%.2f" % C.spent())
def report():
    R = collections.defaultdict(list)
    for r in C.jsonl_read(OUT): R[(r["model"], r.get("ref", "opus55"))].append(r)
    none = lambda x: (x or "").strip().lower().rstrip(".") in ("none", "", "no", "n/a")
    for m, rs in R.items():
        c = collections.Counter(r["winner"] for r in rs); n = len(rs)
        print(f"{m[0]:30s} vs {m[1]:7s} n={n} candidate wins {c['cand']/n:.2f} ties {c['tie']/n:.2f} reference wins {c['opus55']/n:.2f} | invented facts: candidate {sum(not none(r['cand_invented']) for r in rs)/n:.2f} Opus5.5 {sum(not none(r['ref_invented']) for r in rs)/n:.2f}")
if __name__ == "__main__":
    if sys.argv[1] == "run": run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 60, sys.argv[4] if len(sys.argv) > 4 else "opus55")
    else: report()
