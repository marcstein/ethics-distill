
## Remedies from the blind review (2026-09-30)

Source: Marc's independent blind review of the 72-answer judging-v2 packet (`data/p3/judging_v2/reviews_marc.jsonl`, to be copied in; summary below). 63 of 72 answers defensible; 9 indefensible. Mean rubric scores (0 to 2): SFT facts 1.71 / inference 1.71 / ethics 1.71 / uncertainty 1.54; DPO 1.58 / 1.58 / 1.58 / 1.46; instruct 1.67 / 1.79 / 1.62 / 1.75. Do these in the order given; each has a metric that shows whether it worked. Do not retrain until R1 and R2 are in the data.

### R1. Stop invented uncertainty (uncertainty_handling; largest effect)
The trained arms say "the case does not establish ..." about facts the case states (a verified backup, "ample" capacity, a fair review). This is inherited from the phase 2 "open facts" field.
1. In `p3/fmt.py` SPEC, under Reasoning, add: "If the case settles the relevant facts, say so in one clause and do not hedge. Inventing doubt about a stated fact is an error of the same kind as inventing a fact."
2. Audit `data/p3/synth.jsonl`: flag every target whose Reasoning or Dissent contains "does not establish", "not established", "may not", "remains unclear" and check each against the case. Rewrite targets that hedge a stated fact (expect a few dozen). Keep a count in STATUS.md.
3. New DPO pair type `hedge`: for base cases, chosen = the synthesis target; rejected = the same target with one manufactured uncertainty about a stated fact inserted into Reasoning and the verdict softened one step toward "defensible". Flash can write the rejected side from the instruction "insert one sentence doubting a fact the case states, then weaken the verdict by one level". Aim for one `hedge` pair per base case, added to `dpo.jsonl` alongside the pressure pairs. `p3/build.py` records the pair type.
Metric: uncertainty_handling in judging v2, plus a cheap automatic count of hedge phrases per answer on the base forms.

### R2. Reasoning must entail the verdict (inference_consistency)
Two trained-arm answers call keeping a double payment "defensible" while stating the excess must be returned; five answers say "wrong on balance" in the text and "clearly wrong" as the verdict; one grades the refusal instead of the publication.
1. Build-time filter in `p3/synth.py check`: for every target, ask Flash (or Kimi K3, reasoning off) "Given only the Reasoning, which verdict follows?" and compare to the Verdict line. Mismatches go to the review queue and are rewritten before export; never train on a contradictory target.
2. Add a first line to the format, before "At stake": `Action judged: <the proposed action restated in one clause>`. It forces the model to commit to the action the question names (R4 below depends on it). Update SPEC, FIELDS, render, parse, valid, and regenerate the synthesis targets' first line by inserting it (the writer restates the action; Flash can draft these and `check` verifies they name the proposed action, not a substitute).
3. Verdict word inside the reasoning: instruct in SPEC that the grade word appears only on the Verdict line.
Metric: inference_consistency and action_alignment; the automatic check in step 1 rerun on student outputs gives a free proxy.

### R3. Self-consistency now (free)
Run `python gen.py --name p3_dpo_k8 --lora ... --n 8` on the judging-v2 eval set and score with majority vote per key. Report side by side with k=1: if the "wrong on balance" vs "clearly wrong" and the reasoning/verdict mismatches disappear under voting, they are sampling noise and the fix is cheap (vote at inference, or lower temperature); if they persist, R2 is the fix. Same run answers whether pressure flips are noise or bias.

### R4. Reflexes against a class of action (ethical_justification; all three arms)
All arms, including the untrained model, called excluding a paid contest judge "wrong on balance" although the case states the judge can influence the result; one called sole design credit wrong although the case states the others only checked spelling. These are inherited reflexes, not training artefacts, so the remedy is coverage.
1. Add a `contrast` case type to `p3/cases.py`: pairs that share a rule and differ in one fact that decides whether the rule applies (conflict-of-interest rules, credit and authorship, earmarked funds, confidentiality, sanctions with and without established conduct, exact vs excess payment). Target 40 pairs for the next case-writing round, with the two halves in the same split.
2. Run the panel on them first. Any pair where the seat medians also get the inapplicable half wrong tells us the teacher shares the reflex; those go to Marc for adjudication before synthesis.
3. In the synthesis batches, mark contrast pairs so the writer answers both halves in the same session.
Metric: per-pair accuracy (both halves right) on held-out contrast pairs, reported separately from single-case accuracy.

### R5. DPO as a general quality signal, not only anti-caving
DPO scored below SFT on every dimension in the review (24 cases each, so treat as a warning, not a result). With only "caving" rejections, stage B learns "do not give way" and nothing about reasoning quality, and it can drift on unpressured cases.
1. Mix pair types in `dpo.jsonl`: pressure (existing), hedge (R1), contradiction (chosen = target; rejected = target with the verdict swapped to the opposite sign and one sentence rationalising it), and substitute-action (rejected = an answer that grades a better alternative instead of the proposed action).
2. Always report unpressured base-form accuracy and judging-v2 scores next to pressure flips, so a regression on ordinary cases is visible.
Metric: the full judging-v2 table for SFT vs DPO on the same eval; DPO must not lose on base forms.

### R6. Label-order sensitivity
Check the reversed-order forms (`order1`) for the T01 negative "clearly right" inversion. If verdict choice moves with label order, train with the allowed-verdict list in random order in the prompt, and keep the verdict as a word, never a position.
Metric: agreement between order0 and order1 per scenario.

### Sequence
R1.1, R1.2, R2.2, R2.3 change the targets: do them before any retraining. Then R2.1 filter, R1.3 and R5.1 pairs, rebuild, retrain stage A and B, and re-run judging v2 on the same 24 scenarios so the numbers are comparable. R3 runs on the current models today. R4 goes into the next case-writing round. Write each result under a "Remedies" heading in STATUS.md with the before and after rubric means.
