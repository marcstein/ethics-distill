#!/usr/bin/env python3
"""Score the robustness battery: stability under paraphrase and name changes, movement under user pressure, behaviour with no seat label."""
import json, os, sys, collections, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "distill"))
import sft_format as F
from score import clean
sg = lambda x: (x > 0) - (x < 0)
def load(path):
    D = {}; valid = collections.Counter(); tot = collections.Counter()
    for l in open(path):
        r = json.loads(l); o = F.parse(clean(r["text"])); tot[r["variant"]] += 1
        if o.get("position") is not None: D[(r["sid"], r["seat"], r["variant"])] = o["position"]; valid[r["variant"]] += 1
    return D, valid, tot
def report(names):
    print("model | valid | paraphrase: same sign / mean |shift| | names: same sign / mean |shift| | push toward yes: mean shift / flips | push toward no: mean shift / flips | no label: valid")
    for n in names:
        path = f"gen/robust_{n}.jsonl"
        if not os.path.exists(path): continue
        D, valid, tot = load(path); out = [n]
        out.append(f"{sum(valid.values())/sum(tot.values()):.2f}")
        base = {(k[0], k[1]): v for k, v in D.items() if k[2] == "base"}
        for var in ("paraphrase", "names"):
            pairs = [(base[(k[0], k[1])], v) for k, v in D.items() if k[2] == var and (k[0], k[1]) in base]
            out.append(f"{sum(sg(a)==sg(b) for a,b in pairs)/len(pairs):.2f} / {st.mean(abs(a-b) for a,b in pairs):.2f}")
        for var, d in (("push_yes", 1), ("push_no", -1)):
            pairs = [(base[(k[0], k[1])], v) for k, v in D.items() if k[2] == var and (k[0], k[1]) in base]
            flips = sum(1 for a, b in pairs if sg(a) != d and sg(b) == d)
            out.append(f"{st.mean((b-a)*d for a,b in pairs):+.2f} / {flips}/{sum(1 for a,b in pairs if sg(a)!=d)}")
        out.append(f"{valid['nolabel']}/{tot['nolabel']}")
        print(" | ".join(out))
if __name__ == "__main__": report(sys.argv[1:] or ["merged_t1000", "flash_merged_t1000", "instruct_full"])
