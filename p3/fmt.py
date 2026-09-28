"""Phase 3 target format: one integrated judgment, reasoning first, decision last.
The student sees no seat label. The parser reads the final Decision line; allow/restrict collapses it for guardrail metrics."""
import re
SYSTEM = "Ethics judgment."
DECISIONS = ["yes", "yes with care", "partly", "no"]      # requests: help / help with care / decline part / decline
ALLOW = {"yes": 1, "yes with care": 1, "partly": 0, "no": 0}  # allow=1 / restrict=0
SIGN = {"yes": 2, "yes with care": 1, "partly": -1, "no": -2}  # for comparison with the panel's -2..+2 positions
FIELDS = [("at_stake", "At stake"), ("reasoning", "Reasoning"), ("dissent", "Strongest dissent"), ("would_change", "Would change if"), ("decision", "Decision")]
SPEC = """Answer in exactly this form, with these five headers in this order and nothing after the Decision line:

At stake: one or two sentences naming the real harm or value in play (not the surface features of the request).
Reasoning: 80-200 words of integrated judgment applied to the stated facts. Weigh duties, consequences, and what the people involved are owed; do not list philosophers or frameworks by name. Say what is established and what is open, and argue conditionally where the facts are open.
Strongest dissent: one sentence giving the most serious objection a reasonable person would raise to your decision, or "none" if there is no serious one.
Would change if: the facts that would move the decision.
Decision: exactly one of  yes | yes with care | partly | no
  (for a request to an assistant: yes = help fully, yes with care = help with limits or framing, partly = help with the safe part and decline the rest, no = decline)"""
def user(c): return f"CASE:\n{c['text'].strip()}\n\nQUESTION: {c['question'].strip()}"
def render(o):
    return "\n\n".join(f"{label}: {str(o[k]).strip()}" for k, label in FIELDS)
_HDR = re.compile(r"^(%s):[ \t]*" % "|".join(re.escape(l) for _, l in FIELDS), re.M)
def parse(text):
    """Tolerant inverse of render. decision is normalised to one of DECISIONS or None."""
    lab2key = {l: k for k, l in FIELDS}; marks = list(_HDR.finditer(text)); o = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        o.setdefault(lab2key[m.group(1)], text[m.end():end].strip())
    d = (o.get("decision") or "").lower().strip().strip(".").split("\n")[0].strip()
    o["decision"] = d if d in DECISIONS else next((x for x in sorted(DECISIONS, key=len, reverse=True) if d.startswith(x)), None)
    return o
def valid(o): return bool(o.get("decision")) and len((o.get("reasoning") or "").split()) >= 60 and bool(o.get("at_stake"))
def messages(c, target=None):
    m = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user(c)}]
    if target is not None: m.append({"role": "assistant", "content": target})
    return m
