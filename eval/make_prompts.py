#!/usr/bin/env python3
"""Export per-seat system prompts for the prompted baselines: the full seat prompt the teacher saw, with the
tool instruction replaced by plain-text headers that match the student's target format."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "distill"))
import panel as P, seat_prompts as V, sft_format as F
props = V.SEAT_TOOL["input_schema"]["properties"]
fmt = "Write your analysis as plain text using exactly these headers, in this order:\n\n" + "\n".join(
    f"{label}: {props[k].get('description', '').strip() or ('an integer from -2 to +2' if k == 'position' else '')}" for k, label in F.FIELDS)
fmt += "\n\nPut Established facts, Open facts, Reasoning and Strongest objection on the lines after their header. Write Position as a signed integer, e.g. +1, 0 or -2."
out = {}
for seat in P.SEATS:
    s = P.system_for(seat); tail = "Record your analysis with the record_analysis tool."
    assert tail in s, seat; out[seat] = s.replace(tail, fmt)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "baseline_prompts.json"), "w"), indent=1, ensure_ascii=False)
print(len(out), "prompts;", len(out["Hegel"]), "chars for Hegel")
