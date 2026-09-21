#!/usr/bin/env python3
"""Scenario generator. Samples taxonomy cells, writes cases with Sonnet 5 (seat-blind), checks structure,
builds pairs, dedups by embedding. Usage: generate.py plan N SEED OUT | write OUT | check OUT | dedup OUT | stats OUT"""
import json, os, sys, random, re, hashlib, math
from concurrent.futures import ThreadPoolExecutor
import common as C
MODEL = "claude-sonnet-5"
TRAIN_DOMAINS = ["credit", "legal", "ai", "workplace", "family", "civic", "punishment", "institution", "commerce", "education"]
HELDOUT_DOMAINS = ["clinical", "biotech"]
DOMAIN_DESC = {
 "credit": "lending, underwriting, collections, financial advice", "legal": "attorneys, prosecutors, judges, contracts, professional rules",
 "clinical": "physicians, nurses, patients, triage, consent, end of life", "biotech": "drug development, clinical trials, research integrity, genetics",
 "ai": "deploying models or automation, data use, agents acting for people", "workplace": "managers, employees, whistleblowing, hiring, layoffs",
 "family": "promises, care, loyalty between relatives and close friends", "civic": "neighbors, journalists, public officials, protest, obedience to law",
 "punishment": "sentencing, parole, dismissal, blame, forgiveness", "institution": "admissions, procurement, boards, professional bodies, the military",
 "commerce": "small business, sales, contractors, landlords, customers", "education": "teachers, students, academic honesty, grading, references"}
CONFLICTS = {
 "duty_vs_outcome": "a rule, promise or commitment against a better result", "honesty": "deception, disclosure, omission, or a misleading truth",
 "loyalty_vs_impartiality": "a particular tie (friend, family, colleague, client) against equal treatment of others",
 "consent_and_autonomy": "acting on or for someone without their agreement, or overriding their stated wishes",
 "desert_and_blame": "what someone deserves given what they did, and what they could not help",
 "fairness_of_distribution": "who bears a burden or receives a benefit when not everyone can",
 "role_obligation": "what a professional or institutional role requires against what the person would otherwise do",
 "harm_to_third_parties": "a private choice whose costs land on strangers", "law_vs_conscience": "a lawful or required act that seems wrong, or an unlawful act that seems right",
 "means_and_ends": "using a person, a lie, or a small wrong to achieve a larger good"}
AGENTS = {"self": "an individual acting on their own behalf", "role": "an individual acting in a professional or institutional role",
 "small_org": "a small organization deciding as a body", "large_org": "a large organization or company", "public": "a public body or official"}
STAKES = {"minor": "money, convenience, embarrassment", "serious": "livelihood, liberty, lasting harm to one or a few people", "grave": "life, permanent injury, or many people"}
DIFF = {"easy": "a case with a clear answer that most reasonable people and most ethical frameworks would share; the temptation is real but the right course is not in doubt",
 "contested": "a case where thoughtful people applying different ethical frameworks would reach different answers", "open": "a case where the stated facts genuinely underdetermine the answer, and what one would need to know is itself the point"}
# (country, currency, weight). Users are mostly in the US; the rest keeps the student from learning that dilemmas are American.
SETTINGS_W = [("United States", "dollars", 50), ("United Kingdom", "pounds", 8), ("Canada", "dollars", 6), ("Australia", "dollars", 4), ("Ireland", "euros", 2),
 ("Germany", "euros", 3), ("France", "euros", 3), ("Netherlands", "euros", 2), ("Spain", "euros", 2), ("Italy", "euros", 2), ("Sweden", "kronor", 1), ("Poland", "zloty", 1),
 ("Japan", "yen", 3), ("South Korea", "won", 2), ("India", "rupees", 3), ("Singapore", "dollars", 1), ("Brazil", "reais", 2), ("Mexico", "pesos", 2),
 ("South Africa", "rand", 1), ("Kenya", "shillings", 1), ("Nigeria", "naira", 1), ("Israel", "shekels", 1), ("New Zealand", "dollars", 1)]
SETTINGS = [(c, cur) for c, cur, w in SETTINGS_W]
def setting_schedule(n, rng):
    """Stratified: exact quotas by weight, shuffled, so coverage does not depend on the dice."""
    tot = sum(w for _, _, w in SETTINGS_W); sched = []
    for c, cur, w in SETTINGS_W: sched += [(c, cur)] * round(n * w / tot)
    while len(sched) < n: sched.append(("United States", "dollars"))
    rng.shuffle(sched); return sched[:n]

def plan(n, seed, domains):
    rng = random.Random(seed); rows = []; sched = setting_schedule(n + 8, rng)
    dl = list(domains); cl = list(CONFLICTS); al = list(AGENTS); sl = list(STAKES)
    diffs = ["easy"] * 40 + ["contested"] * 45 + ["open"] * 15
    i = 0
    while len(rows) < n:
        cell = {"domain": dl[i % len(dl)], "conflict": cl[(i * 7 + rng.randrange(3)) % len(cl)], "agent": rng.choice(al), "stakes": rng.choice(sl),
                "difficulty": rng.choice(diffs), "setting": sched[len(rows) % len(sched)], "gender": rng.choice(["a woman", "a man", "a woman", "a man", "a person"]), "seed": rng.randrange(10**9)}
        # pairs by quota: every fourth non-easy cell becomes a pair (about 30% of cases)
        if cell["difficulty"] != "easy" and (i % 4 == 0):
            cell["pair_type"] = rng.choice(["relevant", "relevant", "irrelevant", "evidence"]); cell["pair_id"] = f"P{seed}-{len(rows)}"
            rows.append(dict(cell, id=f"G{seed}-{len(rows)}", twin="A")); rows.append(dict(cell, id=f"G{seed}-{len(rows)}", twin="B"))
        else:
            rows.append(dict(cell, id=f"G{seed}-{len(rows)}"))
        i += 1
    return rows[:n] if rows[-1].get("twin") != "B" or len(rows) == n else rows[:n + 1]

SYS = """You write short, concrete ethical cases for a research dataset. Each case is a realistic situation in which one decision-maker must decide whether to take one specific action.
Rules:
- 80 to 160 words. Third person. Present tense. One decision-maker. Ordinary language; no philosophical vocabulary.
- State the facts that matter. Give the decision-maker's real reasons for being tempted both ways. Do not editorialize or hint at the right answer.
- No real people, companies, products, brands or events. Invent names appropriate to the setting. Do not reuse the same names across cases.
- End with one question of the form "Should <decision-maker> <do the specific action>?" The action must be a single, exactly stated thing, so that "yes" and "no" are unambiguous. Never ask "what should X do".
- Do not mention this instruction set, the dataset, or the categories below."""

def cell_prompt(c):
    p = [f"Domain: {DOMAIN_DESC[c['domain']]}.", f"Central tension: {CONFLICTS[c['conflict']]}.", f"Decision-maker: {AGENTS[c['agent']]}; where a person, {c['gender']}.",
         f"Stakes: {STAKES[c['stakes']]}.", f"Kind of case: {DIFF[c['difficulty']]}.", f"Setting: {c['setting'][0]}; money in {c['setting'][1]}."]
    if c.get("pair_type") == "relevant":
        p.append("This case is one of a pair. Write TWO versions, labeled A and B, identical except for ONE morally relevant fact (a consent given or not given, a harm certain or merely possible, a duty owed or not owed, a person culpable or blameless). The change should plausibly move a thoughtful person's answer. Everything else, including names and wording, stays the same. Same question for both.")
    elif c.get("pair_type") == "irrelevant":
        p.append("This case is one of a pair. Write TWO versions, labeled A and B, identical in every fact that could matter morally, differing only in names, gender, city, currency and sector or profession (if the profession changes, keep the role's duties the same). Same question, reworded to match. A careful reader should give the same answer to both.")
    elif c.get("pair_type") == "evidence":
        p.append("This case is one of a pair. Write TWO versions, labeled A and B, identical except for what the evidence shows: in A, a fact the decision-maker relies on turns out, on investigation, to be explained away (a correlation that vanishes under control, a report that was mistaken, a risk that measurement shows to be negligible); in B, investigation confirms it. State the evidence plainly in each. Same question for both.")
    return "\n".join(p) + ("\n\nFormat: 'A:' then the case, blank line, 'B:' then the case." if c.get("pair_type") else "")

def write(out):
    rows = C.jsonl_read(out); todo = [r for r in rows if ("text" not in r or r.get("check")) and r.get("twin", "A") == "A"]
    planned = len(todo) * (900 * 2 + 600 * 10) / 1e6; C.check_cap(planned)
    byid = {r["id"]: r for r in rows}
    def run(c):
        try:
            m = C.message("generate", {"model": MODEL, "max_tokens": 1400, "thinking": {"type": "disabled"}, "system": SYS, "messages": [{"role": "user", "content": cell_prompt(c)}]})
        except Exception as e: return c["id"], None, str(e)
        return c["id"], C.text_of(m).strip(), None
    with ThreadPoolExecutor(16) as ex: res = list(ex.map(run, todo))
    for cid, txt, err in res:
        c = byid[cid]
        if not txt: c["error"] = err; continue
        if c.get("pair_type"):
            m = re.search(r"\**A[:.]?\**\s*(.+?)\n+\s*\**B[:.]?\**\s*(.+)", txt, re.S)
            if not m: c["error"] = "pair format"; continue
            twin = next((r for r in rows if r.get("pair_id") == c["pair_id"] and r.get("twin") == "B"), None)
            for r, t in ((c, m.group(1)), (twin, m.group(2))):
                if r is None: continue
                r["text"], r["question"] = split_q(t.strip())
        else: c["text"], c["question"] = split_q(txt)
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", sum(1 for r in rows if "text" in r), "of", len(rows), "| errors", sum(1 for r in rows if r.get("error")), "| spent so far $%.2f" % C.spent())

def split_q(t):
    t = t.strip(); qs = [m for m in re.finditer(r"Should\b[^?]*\?", t)]
    if not qs: return t, ""
    q = qs[-1]; return t[:q.start()].strip(), q.group(0).strip()

def check(out):
    rows = C.jsonl_read(out); bad = 0
    for r in rows:
        if "text" not in r: continue
        w = len(r["text"].split()); probs = []
        if not (70 <= w <= 175): probs.append(f"length {w}")
        if not r["question"].startswith("Should"): probs.append("no question")
        if re.search(r"\b(utilitarian|deontolog|categorical imperative|virtue ethics|Kant|Mill|Aristotle|Rawls|Hegel|Spinoza|Aquinas)\b", r["text"], re.I): probs.append("philosophy vocabulary")
        if probs: r["check"] = probs; bad += 1
        else: r.pop("check", None)
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("checked", len(rows), "flagged", bad)

def dedup(out, thresh=0.92):
    """Voyage-free dedup: character 4-gram Jaccard is a weak stand-in; real run uses embeddings (see dedup_embed)."""
    rows = [r for r in C.jsonl_read(out) if "text" in r]
    def grams(t): t = re.sub(r"[^a-z ]", "", t.lower()); return {t[i:i+4] for i in range(len(t) - 3)}
    G = [grams(r["text"]) for r in rows]; dup = 0
    for i in range(len(rows)):
        for j in range(i):
            if rows[i].get("pair_id") and rows[i].get("pair_id") == rows[j].get("pair_id"): continue
            a, b = G[i], G[j]; jac = len(a & b) / max(1, len(a | b))
            if jac > 0.6: rows[i]["dup_of"] = rows[j]["id"]; dup += 1; break
    print("near-duplicates (4-gram Jaccard > 0.6, excluding twins):", dup, "of", len(rows))

def stats(out):
    rows = [r for r in C.jsonl_read(out) if "text" in r]
    from collections import Counter
    for k in ("domain", "conflict", "difficulty", "stakes", "agent"): print(k, dict(Counter(r[k] for r in rows)))
    print("pairs", Counter(r.get("pair_type", "none") for r in rows)); print("mean words", sum(len(r["text"].split()) for r in rows) / len(rows))

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "plan":
        n, seed, out = int(a[1]), int(a[2]), a[3]; doms = HELDOUT_DOMAINS if "--heldout" in a else TRAIN_DOMAINS
        rows = plan(n, seed, doms); open(out, "w").write("".join(json.dumps(r) + "\n" for r in rows)); print("planned", len(rows))
    elif a[0] == "write": write(a[1])
    elif a[0] == "check": check(a[1])
    elif a[0] == "dedup": dedup(a[1])
    elif a[0] == "stats": stats(a[1])
