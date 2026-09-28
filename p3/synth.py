#!/usr/bin/env python3
"""Synthesis (the training targets), written by Claude Code in small batches under the subscription.
  python synth.py batches [25]   -> data/p3/synth/todo_NN.md  (case + panel summary + format spec; the writer's intended label is withheld)
  Claude Code answers each batch into data/p3/synth/done_NN.jsonl, one line per case: {"id": "...", "text": "<answer in the five-header format>"}
  python synth.py check          -> validates format, compares decisions with the writer's intended label and the panel, writes data/p3/review.md
  python synth.py export         -> data/p3/synth.jsonl (id, text, parsed) for build.py"""
import json, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "distill"))
import fmt, common as C
D = os.path.join(C.ROOT, "data", "p3"); SD = os.path.join(D, "synth"); os.makedirs(SD, exist_ok=True)
PNAME = {"Kant": "duty-based", "Mill": "consequence-based", "Aristotle": "character-and-judgment", "Rawls": "fairness-to-the-worst-off", "Hegel": "roles-and-institutions", "Spinoza": "clear-headed self-interest", "Aquinas": "natural-law"}
HEAD = """# Synthesis batch {n}

You are writing the training targets for a small model that must make ethical judgments from its weights alone. For each case below, write ONE integrated judgment in the exact format given. Write as a careful, plain-spoken moral reasoner; do not name philosophers, seats or frameworks. Use the panel summary only as input: it tells you where seven differently-minded reasoners landed and what the most dissenting one objected. Your Decision is your own; if you disagree with the panel, say why in the reasoning.

Rules: rely only on facts the case states; mark what is open; no invented facts, motives or consequences. For requests, decide whether an assistant should help, at what level, and why — name the actual harm or value at stake, not surface cues. Never include harmful operational content in an answer, even when declining.

{spec}

Write your answers to `{out}`, one JSON object per line: {{"id": "<case id>", "text": "<your answer, headers included, newline-separated>"}}. Answer every case in this batch. Then run `python3 p3/synth.py check`.

---
"""
def batches(size=25):
    cases = C.jsonl_read(os.path.join(D, "cases.jsonl")); panel = {r["id"]: r for r in C.jsonl_read(os.path.join(D, "panel.jsonl"))}
    cases = [c for c in cases if c["split"] == "train"]
    for n, i in enumerate(range(0, len(cases), size), 1):
        out = os.path.join(SD, f"done_{n:02d}.jsonl"); parts = [HEAD.format(n=n, spec=fmt.SPEC, out=os.path.relpath(out, C.ROOT))]
        for c in cases[i:i + size]:
            p = panel.get(c["id"]); parts.append(f"## {c['id']}  ({c['type']})\n\n{fmt.user(c)}\n")
            if p:
                pos = ", ".join(f"{PNAME[s]} {v:+d}" for s, v in p["positions"].items())
                parts.append(f"Panel summary (positions -2 strongly no .. +2 strongly yes): {pos}. Median {p['panel_median']:+.0f}{'; the panel is split' if p['contested'] else ''}.\n"
                             f"Most dissenting view ({PNAME[p['dissent_seat']]}, {p['dissent_position']:+d}): {p['dissent_verdict'].strip()} Objection it raises: {p['dissent_objection'].strip()}\n")
            parts.append("")
        open(os.path.join(SD, f"todo_{n:02d}.md"), "w").write("\n".join(parts))
    print("wrote", n, "batches of up to", size, "to", SD)
def load_done():
    A = {}
    for f in sorted(glob.glob(os.path.join(SD, "done_*.jsonl"))):
        for r in C.jsonl_read(f): A[r["id"]] = r["text"]
    return A
def check():
    cases = {c["id"]: c for c in C.jsonl_read(os.path.join(D, "cases.jsonl"))}; panel = {r["id"]: r for r in C.jsonl_read(os.path.join(D, "panel.jsonl"))}
    A = load_done(); bad, mism, ok = [], [], collections.Counter(); tot = collections.Counter()
    for cid, text in A.items():
        c = cases.get(cid);
        if not c: continue
        o = fmt.parse(text); tot[c["type"]] += 1
        if not fmt.valid(o): bad.append((cid, "format: decision=%s reasoning_words=%d" % (o.get("decision"), len((o.get("reasoning") or "").split())))); continue
        ref = c["intended"]; same = fmt.ALLOW[o["decision"]] == fmt.ALLOW[ref] if c["type"] != "dilemma" else (fmt.SIGN[o["decision"]] > 0) == (panel.get(cid, {}).get("panel_median", 0) > 0)
        ok[c["type"]] += same
        if not same: mism.append((cid, c["type"], o["decision"], ref if c["type"] != "dilemma" else f"panel median {panel.get(cid, {}).get('panel_median')}", c.get("why", "")))
    lines = [f"# Synthesis check — {len(A)} answers, {len(bad)} malformed\n"]
    for t in tot: lines.append(f"- {t}: decision agrees with reference on {ok[t]}/{tot[t]} ({ok[t]/tot[t]:.0%})" + ("  ← gate is ≥85% for request types" if t != "dilemma" else "  (reference = panel median sign; disagreement here is allowed, review only)"))
    lines.append("\n## Malformed\n" + "\n".join(f"- {c}: {m}" for c, m in bad) if bad else "\n## Malformed\nnone")
    lines.append("\n## Review queue (decision differs from reference)\n" + "\n".join(f"- {c} [{t}] answer={d!r} reference={r!r} — writer's note: {w}" for c, t, d, r, w in mism))
    open(os.path.join(D, "review.md"), "w").write("\n".join(lines)); print("\n".join(lines[:len(tot) + 1])); print("full report: data/p3/review.md")
def export():
    cases = {c["id"]: c for c in C.jsonl_read(os.path.join(D, "cases.jsonl"))}; A = load_done(); rows = []
    for cid, text in A.items():
        o = fmt.parse(text)
        if cid in cases and fmt.valid(o): rows.append({"id": cid, "text": fmt.render(o), "decision": o["decision"]})
    with open(os.path.join(D, "synth.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("exported", len(rows), "valid syntheses")
if __name__ == "__main__":
    {"batches": lambda: batches(int(sys.argv[2]) if len(sys.argv) > 2 else 25), "check": check, "export": export}[sys.argv[1]]()
