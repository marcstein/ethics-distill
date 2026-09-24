#!/usr/bin/env python3
"""Score generated seat analyses against the Opus gold set.  python score.py gen/*.jsonl  -> results/eval_table.md"""
import json, os, sys, statistics as st, itertools, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "distill"))
import common as C, panel as P, sft_format as F
PANEL = [s for s in P.SEATS if s != "KantModern"]; HELD = {"clinical", "biotech"}
SC = {s["id"]: s for s in P.scen("eval")}
GOLD = {(r["sid"], r["seat"]): r["output"]["position"] for r in C.jsonl_read(P.outpath("eval"))}
TEST = set(json.load(open(os.path.join(C.ROOT, "data", "sft", "splits.json")))["test"])
sgn = lambda x: (x > 0) - (x < 0)
def label(ps):
    if sum(1 for p in ps if p == 0) >= 2: return "open"
    if any(p > 0 for p in ps) and any(p < 0 for p in ps): return "contested"
    if all(abs(p) >= 1 for p in ps) and len({sgn(p) for p in ps}) == 1: return "easy"
    return "leaning"
def pos_stats(pairs):
    if not pairs: return {}
    return {"n": len(pairs), "exact": sum(m == g for m, g in pairs) / len(pairs), "within1": sum(abs(m - g) <= 1 for m, g in pairs) / len(pairs),
            "sign": sum(sgn(m) == sgn(g) for m, g in pairs) / len(pairs), "mae": sum(abs(m - g) for m, g in pairs) / len(pairs)}
def score(path):
    rows = C.jsonl_read(path); M = {}; valid = 0; trunc = 0
    for r in rows:
        o = F.parse(r["text"]); ok = o["position"] is not None and all(o.get(k) for k, _ in F.FIELDS if k not in ("modification", "open_facts"))
        valid += ok; trunc += r.get("finish") == "length"; M[(r["sid"], r["seat"])] = o["position"]
    res = {"name": os.path.basename(path)[:-6], "rows": len(rows), "valid": valid / len(rows), "truncated": trunc / len(rows)}
    def pairs(seats, dom):
        return [(M[k], GOLD[k]) for k in M if k[1] in seats and M[k] is not None and k in GOLD
                and ((SC[k[0]]["domain"] in HELD) == (dom == "held"))]
    res["panel_train_domains"] = pos_stats(pairs(PANEL, "train")); res["panel_heldout"] = pos_stats(pairs(PANEL, "held"))
    res["kantmodern"] = pos_stats(pairs(["KantModern"], "train") + pairs(["KantModern"], "held"))
    res["per_seat_sign"] = {s: pos_stats(pairs([s], "train") + pairs([s], "held")).get("sign") for s in P.SEATS}
    # distinctness: ordering of seats within a case, panel label, dissenters
    order_ok = order_n = lab_ok = lab_n = 0; tp = fp = fn = 0; spread_m, spread_g = [], []
    for sid in {k[0] for k in M}:
        mm = [M.get((sid, s)) for s in PANEL]; gg = [GOLD.get((sid, s)) for s in PANEL]
        if None in mm or None in gg: continue
        for i, j in itertools.combinations(range(7), 2):
            if gg[i] != gg[j]: order_n += 1; order_ok += sgn(mm[i] - mm[j]) == sgn(gg[i] - gg[j])
        lab_n += 1; lab_ok += label(mm) == label(gg); spread_m.append(st.pstdev(mm)); spread_g.append(st.pstdev(gg))
        maj = sgn(sum(sgn(g) for g in gg)); md = {s for s, g in zip(PANEL, gg) if sgn(g) != maj}
        mmj = sgn(sum(sgn(m) for m in mm)); dd = {s for s, m in zip(PANEL, mm) if sgn(m) != mmj}
        tp += len(md & dd); fp += len(dd - md); fn += len(md - dd)
    res["seat_order_agreement"] = order_ok / order_n if order_n else None
    res["panel_label_agreement"] = lab_ok / lab_n if lab_n else None
    res["spread_model_vs_gold"] = (st.mean(spread_m), st.mean(spread_g)) if spread_m else None
    res["dissenter_f1"] = 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None
    # contrast pairs
    twins = collections.defaultdict(dict)
    for sid in TEST:
        s = SC[sid]
        if s.get("pair_id"): twins[s["pair_id"]][s["twin"]] = s
    irr_m, irr_g, dir_ok, dir_n, moved = [], [], 0, 0, 0
    for pid, t in twins.items():
        if set(t) != {"A", "B"}: continue
        ptype = t["A"]["pair_type"]
        for seat in PANEL:
            ka, kb = (t["A"]["id"], seat), (t["B"]["id"], seat)
            if M.get(ka) is None or M.get(kb) is None: continue
            dm, dg = M[kb] - M[ka], GOLD[kb] - GOLD[ka]
            if ptype == "irrelevant": irr_m.append(abs(dm)); irr_g.append(abs(dg))
            elif dg != 0: dir_n += 1; dir_ok += sgn(dm) == sgn(dg); moved += dm != 0
    res["pairs_irrelevant_mean_abs_shift_model_vs_gold"] = (st.mean(irr_m), st.mean(irr_g)) if irr_m else None
    res["pairs_relevant_direction_agreement"] = dir_ok / dir_n if dir_n else None
    res["pairs_relevant_moved_when_gold_moved"] = moved / dir_n if dir_n else None
    return res
def fmt(x, p=2): return "–" if x is None else (f"{x:.{p}f}" if isinstance(x, float) else str(x))
if __name__ == "__main__":
    R = [score(p) for p in sys.argv[1:]]; os.makedirs(os.path.join(C.ROOT, "results"), exist_ok=True)
    json.dump(R, open(os.path.join(C.ROOT, "results", "eval_scores.json"), "w"), indent=1)
    hdr = "| config | valid | sign (train dom) | exact | sign (held-out) | exact | seat order | panel label | dissenter F1 | irrelevant shift (gold) | relevant dir |"
    lines = [hdr, "|" + "---|" * hdr.count("|")[:-1] if False else "|" + "---|" * (hdr.count("|") - 1)]
    for r in R:
        t, h = r["panel_train_domains"], r["panel_heldout"]; irr = r["pairs_irrelevant_mean_abs_shift_model_vs_gold"]
        lines.append(f"| {r['name']} | {fmt(r['valid'])} | {fmt(t.get('sign'))} | {fmt(t.get('exact'))} | {fmt(h.get('sign'))} | {fmt(h.get('exact'))} | "
                     f"{fmt(r['seat_order_agreement'])} | {fmt(r['panel_label_agreement'])} | {fmt(r['dissenter_f1'])} | "
                     f"{fmt(irr[0]) + ' (' + fmt(irr[1]) + ')' if irr else '–'} | {fmt(r['pairs_relevant_direction_agreement'])} |")
    open(os.path.join(C.ROOT, "results", "eval_table.md"), "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
