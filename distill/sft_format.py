"""Render a seat analysis as the student's plain-text target, and parse it back for evaluation."""
import re
FIELDS = [("action_rated", "Action rated"), ("established_facts", "Established facts"), ("open_facts", "Open facts"),
          ("reasoning", "Reasoning"), ("strongest_objection", "Strongest objection"), ("position", "Position"),
          ("verdict", "Verdict"), ("modified_version_acceptable", "Modified version acceptable"),
          ("modification", "Modification"), ("would_change_if", "Would change if")]
BLOCK = {"established_facts", "open_facts", "reasoning", "strongest_objection"}   # multi-line: header on its own line
SEAT_NAME = {"Kant": "Kant", "Mill": "Mill", "Aristotle": "Aristotle", "Rawls": "Rawls", "Hegel": "Hegel",
             "Spinoza": "Spinoza", "Aquinas": "Aquinas", "KantModern": "Contemporary Kantian"}
def system(seat): return f"Ethics panel seat: {SEAT_NAME[seat]}."
def user(s): return f"CASE:\n{s['text'].strip()}\n\nQUESTION: {s['question'].strip()}"
def render(o):
    out = []
    for k, label in FIELDS:
        v = o[k]
        if k == "position": v = f"{int(v):+d}" if int(v) else "0"
        v = str(v).strip()
        out.append(f"{label}:\n{v}" if k in BLOCK else f"{label}: {v}")
    return "\n\n".join(out)
_HDR = re.compile(r"^(%s):[ \t]*" % "|".join(re.escape(l) for _, l in FIELDS), re.M)
def parse(text):
    """Inverse of render; tolerant of missing fields. Returns dict with position as int or None."""
    lab2key = {l: k for k, l in FIELDS}; marks = list(_HDR.finditer(text)); o = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        o.setdefault(lab2key[m.group(1)], text[m.end():end].strip())
    p = re.match(r"\s*([+-]?\d)", o.get("position", "") or "")
    o["position"] = max(-2, min(2, int(p.group(1)))) if p else None
    return o
