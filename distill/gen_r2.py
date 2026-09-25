#!/usr/bin/env python3
"""Round 2 case writer: seat-dividing cases built on named fault lines between frameworks.
  python gen_r2.py sample      -> 20 cases (2 per fault line) + Flash and Opus 5.5 panels + review sheet"""
import json, os, sys, random, re, time, collections
from concurrent.futures import ThreadPoolExecutor
import common as C, panel as P, generate as G, bakeoff as B
# The writer never sees philosophers' names: each fault line is described as a concrete tension (no philosophy vocabulary in cases).
FAULT = {
 "kant_mill": ("Kant vs Mill", "Keeping a promise, telling the truth, or refusing to use a person merely as a tool would lead to clearly worse results for other people than breaking the promise, lying, or using them. The better outcome requires the lie, the broken promise, or the use."),
 "mill_rawls": ("Mill vs Rawls", "The option that produces the greatest total benefit does so by imposing a real, uncompensated loss on the one person who is already worst off. The alternative protects that person at a larger combined cost to many others who are better off."),
 "aristotle_kant": ("Aristotle vs Kant", "A clear rule points one way, but someone with good judgment who attends to these particular people and circumstances would see that applying it rigidly here is harsh or foolish. Making an exception carries a real risk of setting a precedent."),
 "hegel_kant": ("Hegel vs Kant", "What a legitimate role, institution, family or community reasonably expects of the decision-maker conflicts with their own private conscience. The institution is broadly fair and working as intended, not corrupt."),
 "aquinas_mill": ("Aquinas vs Mill", "The action that would produce clearly good consequences requires doing something widely regarded as wrong in itself (deliberately harming an innocent person, deceiving, taking what is not yours), or it turns on the difference between a harm that is intended and one that is foreseen but not intended."),
 "spinoza": ("Spinoza vs the panel", "The decision-maker is strongly tempted to act out of fear, anger, resentment or wounded pride, or to sacrifice their own long-term wellbeing for others; a calmer, clearer understanding of the situation points to a different course."),
 "rawls_aristotle": ("Rawls vs Aristotle", "A fair, impartial procedure (a lottery, a queue, a blind rule, equal shares) points one way, while what particular individuals have earned or deserve by their conduct or merit points the other."),
 "kant_modern": ("Historical vs contemporary Kantian", "A strict, exceptionless rule of conduct (never lie, never break a promise, never go back on your word) conflicts with showing real respect for a vulnerable person's dignity and ability to run their own life."),
 "hegel_mill": ("Hegel vs Mill", "Honoring a relationship of mutual obligation or membership (a family duty, professional solidarity, a civic role, loyalty to a community) costs more in total wellbeing than an impartial calculation would recommend."),
 "three_way": ("Three-way split", "Three considerations pull in different directions at once: a clear duty or rule, the overall consequences for many people, and the claims of a particular relationship or community."),
}
TRAIN_DOMAINS = [d for d in G.DOMAIN_DESC if d not in G.HELDOUT_DOMAINS]
def cell_prompt(c):
    p = [f"Domain: {G.DOMAIN_DESC[c['domain']]}.", f"Central tension: {FAULT[c['fault']][1]}",
         "Build the case so that thoughtful people reasoning from different moral starting points would genuinely disagree about the answer. Give both sides real weight; the case must not be easy.",
         f"Decision-maker: {G.AGENTS[c['agent']]}; where a person, {c['gender']}.", f"Stakes: {G.STAKES[c['stakes']]}.", f"Setting: {c['setting'][0]}; money in {c['setting'][1]}."]
    if c["domain"] not in G.HELDOUT_DOMAINS:
        p.append("Do not set the case in medicine, healthcare, clinical research or drug development, and do not make the decision-maker a clinician or a biomedical researcher; those settings are reserved.")
    return "\n".join(p)
def sample(seed=202609):
    rng = random.Random(seed); cells = []; sets = G.setting_schedule(20, rng)
    for i, f in enumerate(list(FAULT) * 2):
        cells.append({"id": f"R2S-{i}", "fault": f, "domain": TRAIN_DOMAINS[(i * 3) % len(TRAIN_DOMAINS)], "agent": rng.choice(list(G.AGENTS)),
                      "stakes": rng.choice(["minor", "serious", "serious", "grave"]), "gender": rng.choice(["a woman", "a man", "a person"]), "setting": sets[i], "type": "dividing"})
    C.check_cap(20 * 0.02)
    def write(c):
        m = C.message("gen_r2", {"model": G.MODEL, "max_tokens": 1400, "thinking": {"type": "disabled"}, "system": G.SYS, "messages": [{"role": "user", "content": cell_prompt(c)}]})
        c["text"], c["question"] = G.split_q(C.text_of(m)); return c
    with ThreadPoolExecutor(20) as ex: cells = list(ex.map(write, cells))
    out = os.path.join(C.ROOT, "data", "scenarios", "r2_sample20.jsonl")
    with open(out, "w") as f:
        for c in cells: f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print("wrote", len(cells), "cases; words", [len(c["text"].split()) for c in cells])
def panels():
    cells = C.jsonl_read(os.path.join(C.ROOT, "data", "scenarios", "r2_sample20.jsonl")); out = os.path.join(C.ROOT, "results", "r2_sample20_panels.jsonl")
    done = {(r["sid"], r["seat"], r["teacher"]) for r in C.jsonl_read(out) if r["output"]}
    jobs = [(c, s, t) for c in cells for s in P.SEATS for t in ("flash", "opus55") if (c["id"], s, t) not in done]
    C.check_cap(sum(1 for j in jobs if j[2] == "opus55") * 0.05)
    def one(j):
        c, seat, t = j; o = None
        for _ in range(2):
            try:
                if t == "flash": o = B.call("deepseek/deepseek-v4.1-flash", seat, c)[0]
                else: o = P.repair(C.tool_input(C.message("r2_sample_opus", P.params(C.OPUS, seat, c))))
            except Exception as e: print("err", c["id"], seat, t, str(e)[:100])
            if P.valid(o): break
        return {"sid": c["id"], "seat": seat, "teacher": t, "output": o if P.valid(o) else None}
    from concurrent.futures import as_completed
    res = []
    with ThreadPoolExecutor(16) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]): r = f.result(); res.append(r); C.jsonl_append(out, [r])
    print("panels", sum(1 for r in res if r["output"]), "/", len(res), "| Anthropic $%.2f OpenRouter $%.2f" % (C.spent(), B.spent()))
def review():
    cells = C.jsonl_read(os.path.join(C.ROOT, "data", "scenarios", "r2_sample20.jsonl"))
    R = {(r["sid"], r["seat"], r["teacher"]): r["output"] for r in C.jsonl_read(os.path.join(C.ROOT, "results", "r2_sample20_panels.jsonl")) if r["output"]}
    seats = [s for s in P.SEATS if s != "KantModern"]; short = {"Kant": "Kant", "Mill": "Mill", "Aristotle": "Arist", "Rawls": "Rawls", "Hegel": "Hegel", "Spinoza": "Spin", "Aquinas": "Aquin", "KantModern": "cKant"}
    fmt = lambda p: "–" if p is None else (f"+{p}" if p > 0 else str(p))
    lines = ["# Round 2 sample: 20 seat-dividing cases", "", "Two cases per fault line. Positions from the training teacher (DeepSeek V4.1 Flash) and the gold teacher (Opus 5.5). Scale −2 (clearly not) to +2 (clearly yes). A split means at least one seat says yes and at least one says no.", "",
             "Your review per case: keep / fix / reject, and whether it really divides the seats named in the fault line.", ""]
    stats = collections.Counter()
    for c in cells:
        lines += [f"## {c['id']} · {FAULT[c['fault']][0]}", f"*{c['domain']} · stakes {c['stakes']} · {c['setting'][0]}*", "", c["text"], "", f"**{c['question']}**", "",
                  "| teacher | " + " | ".join(short[s] for s in P.SEATS) + " | split |", "|---|" + "---|" * (len(P.SEATS) + 1)]
        for t, name in (("flash", "Flash"), ("opus55", "Opus 5.5")):
            ps = [(R.get((c["id"], s, t)) or {}).get("position") for s in P.SEATS]; pp = [p for p, s in zip(ps, P.SEATS) if s != "KantModern" and p is not None]
            sp = any(p > 0 for p in pp) and any(p < 0 for p in pp); stats[(t, "split")] += sp; stats[(t, "n")] += 1
            stats[(t, "spread")] += (max(pp) - min(pp)) if pp else 0
            lines.append(f"| {name} | " + " | ".join(fmt(p) for p in ps) + f" | {'yes' if sp else 'no'} |")
        lines += ["", "Verdict: keep / fix / reject  ", "Divides the named seats? y/n  ", "Notes:", "", "---", ""]
    head = [f"**Splits:** Flash {stats[('flash','split')]}/{stats[('flash','n')]}, Opus 5.5 {stats[('opus55','split')]}/{stats[('opus55','n')]} (round 1: Sonnet 19%, Opus 5 10% of test cases).", ""]
    lines[6:6] = head
    open(os.path.join(C.ROOT, "docs", "r2_sample20_review.md"), "w").write("\n".join(lines))
    print(head[0])
if __name__ == "__main__": {"sample": sample, "panels": panels, "review": review}[sys.argv[1]]()
