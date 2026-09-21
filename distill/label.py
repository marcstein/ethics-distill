#!/usr/bin/env python3
"""Second-pass difficulty classifier (cheap, seat-blind). Relabels each case's difficulty from the text, keeping the generator's intent as 'difficulty_intended'."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
import common as C
SYS = """You classify short ethical cases by how contested the answer is among thoughtful people. Reply with exactly one word:
easy - a clear answer that most reasonable people and most ethical traditions would share; the temptation is real but the right course is not seriously in doubt.
contested - thoughtful people applying different ethical outlooks would reach different answers.
open - the stated facts leave the answer genuinely undetermined; what one would need to know is the point."""
def run(out):
    rows = C.jsonl_read(out); todo = [r for r in rows if "text" in r and "difficulty_label" not in r]
    C.check_cap(len(todo) * 0.0006)
    def one(r):
        m = C.message("label", {"model": "claude-haiku-4-5-20251001", "max_tokens": 5, "system": SYS, "messages": [{"role": "user", "content": r["text"] + "\n\n" + r["question"]}]})
        w = C.text_of(m).strip().lower().split()[0].strip(".") if C.text_of(m).strip() else "?"
        return r["id"], w if w in ("easy", "contested", "open") else "?"
    with ThreadPoolExecutor(24) as ex: res = dict(ex.map(one, todo))
    for r in rows:
        if r["id"] in res: r["difficulty_intended"] = r["difficulty"]; r["difficulty_label"] = res[r["id"]]
    with open(out, "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    agree = sum(1 for r in rows if r.get("difficulty_label") == r.get("difficulty_intended"))
    print("labeled", len(res), "| agree with intent", agree, "| labels", dict(Counter(r.get("difficulty_label") for r in rows if "difficulty_label" in r)))
if __name__ == "__main__": run(sys.argv[1])
