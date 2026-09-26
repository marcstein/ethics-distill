#!/usr/bin/env python3
"""Blind absolute scoring of seat analyses by Opus 5.5: gold (Opus 5), Sonnet-taught student, Flash-taught student, prompted instruct model.
Each analysis is judged alone, re-rendered in one uniform format, with no hint of its source.
  python judge_quality.py run  |  report"""
import json, os, sys, random, time, collections, statistics as st
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "distill"))
import common as C, panel as P, sft_format as F, seat_prompts as V
from score import clean
OUT = os.path.join(C.ROOT, "results", "judge_quality.jsonl")
SRC = {"gold_opus5": None, "student_sonnet": "gen/merged_t1000.jsonl", "student_flash": "gen/flash_merged_t1000.jsonl", "prompted_instruct": "gen/instruct_full.jsonl"}
NAME = {"Kant": "Immanuel Kant", "Mill": "John Stuart Mill", "Aristotle": "Aristotle", "Rawls": "John Rawls", "Hegel": "G. W. F. Hegel", "Spinoza": "Baruch Spinoza", "Aquinas": "Thomas Aquinas"}
RUBRIC = """You are an expert in moral philosophy grading one analysis of a concrete case, written as if by {name}. Grade it strictly and independently; do not compare it with any other answer.
Score each criterion from 1 (poor) to 5 (excellent):
- fact_discipline: relies only on facts the case states; marks what is open; argues conditionally where needed; invents no facts, motives or consequences.
- fidelity: reasons the way {name}'s framework actually works, applied to these facts (not a summary of the theory, not a different philosopher's reasoning in disguise). Penalize doctrinal errors.
- coherence: the position and verdict follow from the reasoning; the objection is real and actually answered.
- clarity: plain, precise, economical prose.
Also list any invented facts (or 'none'), any doctrinal errors about {name} (or 'none'), and give an overall score from 1 to 10."""
TOOL = {"name": "grade", "description": "Record the grade.", "input_schema": {"type": "object", "properties": {
    "fact_discipline": {"type": "integer"}, "fidelity": {"type": "integer"}, "coherence": {"type": "integer"}, "clarity": {"type": "integer"},
    "invented_facts": {"type": "string"}, "doctrinal_errors": {"type": "string"}, "overall": {"type": "integer"}, "comment": {"type": "string"}},
    "required": ["fact_discipline", "fidelity", "coherence", "clarity", "invented_facts", "doctrinal_errors", "overall", "comment"]}}
ORDER = ["action_rated", "established_facts", "open_facts", "reasoning", "strongest_objection", "position", "verdict", "modified_version_acceptable", "modification", "would_change_if"]
LABEL = dict(F.FIELDS)
def render(o): return "\n\n".join(f"{LABEL[k]}: {o[k]}" for k in ORDER if o.get(k) not in (None, ""))
def load():
    A = {}
    for r in C.jsonl_read(P.outpath("eval")): A[("gold_opus5", r["sid"], r["seat"])] = r["output"]
    for src, path in SRC.items():
        if not path: continue
        for r in C.jsonl_read(os.path.join(C.ROOT, "eval", path)):
            o = F.parse(clean(r["text"]))
            if o.get("position") is not None and o.get("reasoning"): A[(src, r["sid"], r["seat"])] = o
    return A
def sample():
    test = set(json.load(open(os.path.join(C.ROOT, "data", "sft", "splits.json")))["test"]); SC = {s["id"]: s for s in P.scen("eval") if s["id"] in test}
    rng = random.Random(5); keys = [(i, s) for i in sorted(SC) for s in NAME]; rng.shuffle(keys)
    tr = [k for k in keys if SC[k[0]]["domain"] not in ("clinical", "biotech")][:80]; ho = [k for k in keys if SC[k[0]]["domain"] in ("clinical", "biotech")][:40]
    return SC, tr + ho
def run(limit=500):
    SC, keys = sample(); A = load()
    done = {(r["src"], r["sid"], r["seat"]) for r in C.jsonl_read(OUT)}
    jobs = [(src, sid, seat) for sid, seat in keys for src in SRC if (src, sid, seat) in A and (src, sid, seat) not in done]
    random.Random(9).shuffle(jobs); jobs = jobs[:limit]; C.check_cap(len(jobs) * 0.03)
    def one(j):
        src, sid, seat = j; s = SC[sid]
        p = {"model": C.OPUS, "max_tokens": 3000, "system": RUBRIC.format(name=NAME[seat]), "tools": [TOOL], "tool_choice": {"type": "auto"},
             "messages": [{"role": "user", "content": f"{V.seat_user(s)}\n\n=== ANALYSIS (as {NAME[seat]}) ===\n{render(A[j])}\n\nRecord your grade with the grade tool."}]}
        for a in range(6):
            try:
                g = C.tool_input(C.message("judge_quality", p))
                if g and "overall" in g: return {"src": src, "sid": sid, "seat": seat, "domain": s["domain"], **g}
            except RuntimeError as e:
                if "429" in str(e): time.sleep(15 + 10 * a); continue
                return None
    with ThreadPoolExecutor(16) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            r = f.result()
            if r: C.jsonl_append(OUT, [r])
    print("judged", len(jobs), "| Anthropic $%.2f" % C.spent())
def report():
    R = collections.defaultdict(list)
    for r in C.jsonl_read(OUT): R[r["src"]].append(r)
    none = lambda x: (x or "").strip().lower().rstrip(".") in ("none", "", "n/a", "no")
    print("source | n | overall (1-10) | facts | fidelity | coherence | clarity | any invented fact | any doctrinal error | overall held-out")
    for src in SRC:
        rs = R.get(src, []);
        if not rs: continue
        m = lambda k, rr=rs: st.mean(r[k] for r in rr); ho = [r for r in rs if r["domain"] in ("clinical", "biotech")]
        print(f"{src:18s} | {len(rs)} | {m('overall'):.2f} | {m('fact_discipline'):.2f} | {m('fidelity'):.2f} | {m('coherence'):.2f} | {m('clarity'):.2f} | "
              f"{sum(not none(r['invented_facts']) for r in rs)/len(rs):.2f} | {sum(not none(r['doctrinal_errors']) for r in rs)/len(rs):.2f} | {m('overall', ho) if ho else float('nan'):.2f}")
if __name__ == "__main__" and sys.argv[1] in ("run", "report"): {"run": lambda: run(int(sys.argv[2]) if len(sys.argv) > 2 else 500), "report": report}[sys.argv[1]]()

def batch_submit():
    """Submit the remaining judgments as one Batch API job (half price, async)."""
    SC, keys = sample(); A = load(); done = {(r["src"], r["sid"], r["seat"]) for r in C.jsonl_read(OUT)}
    jobs = [(src, sid, seat) for sid, seat in keys for src in SRC if (src, sid, seat) in A and (src, sid, seat) not in done]
    C.check_cap(len(jobs) * 0.015)
    reqs = [{"custom_id": f"{src}__{sid}__{seat}", "params": {"model": C.OPUS, "max_tokens": 3000, "system": RUBRIC.format(name=NAME[seat]), "tools": [TOOL], "tool_choice": {"type": "auto"},
             "messages": [{"role": "user", "content": f"{V.seat_user(SC[sid])}\n\n=== ANALYSIS (as {NAME[seat]}) ===\n{render(A[(src, sid, seat)])}\n\nRecord your grade with the grade tool."}]}} for src, sid, seat in jobs]
    b = C.http("POST", "/messages/batches", {"requests": reqs})
    json.dump({"batch": b["id"], "n": len(reqs)}, open(os.path.join(C.ROOT, "results", "judge_quality_batch.json"), "w")); print("submitted", b["id"], len(reqs))
def batch_collect():
    st_ = json.load(open(os.path.join(C.ROOT, "results", "judge_quality_batch.json"))); b = C.http("GET", f"/messages/batches/{st_['batch']}")
    print(b["processing_status"], b["request_counts"])
    if b["processing_status"] != "ended" or st_.get("collected"): return
    SC, _ = sample(); ui = uo = 0; rows = []
    for line in C.http("GET", b["results_url"], raw=True).decode().splitlines():
        r = json.loads(line)
        if r["result"]["type"] != "succeeded": continue
        m = r["result"]["message"]; ui += m["usage"]["input_tokens"]; uo += m["usage"]["output_tokens"]; g = C.tool_input(m)
        src, sid, seat = r["custom_id"].split("__")
        if g and "overall" in g: rows.append({"src": src, "sid": sid, "seat": seat, "domain": SC[sid]["domain"], **g})
    C.jsonl_append(OUT, rows); C.record("judge_quality_batch", C.OPUS, {"input_tokens": ui, "output_tokens": uo}, batch=True, n=len(rows))
    st_["collected"] = True; json.dump(st_, open(os.path.join(C.ROOT, "results", "judge_quality_batch.json"), "w")); print("collected", len(rows), "| Anthropic $%.2f" % C.spent())
if __name__ == "__main__" and sys.argv[1] in ("submit", "collect"): {"submit": batch_submit, "collect": batch_collect}[sys.argv[1]]()
