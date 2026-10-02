# Status — 2026-09-26

## Question
Can the Ethics Panel's seven-seat reasoning be carried in the weights of a small open model, rather than supplied in a prompt?

## Setup (round 1)
1,000 generic cases (10 domains; clinical and biotech held out) × 7 seats + contemporary-Kantian annotation.
Teachers: Claude Sonnet 5 (8,000 analyses) and DeepSeek V4.1 Flash (same cases). Gold: Claude Opus 5 on 260 test cases.
Student: Qwen3-4B-Base + LoRA, merged model (all seats), prompt = "Ethics panel seat: X." + case only.
Baseline: Qwen3-4B instruct given the full seat prompt (ethics in context).

## Results
Positions vs Opus gold (sign agreement, train domains / held-out): Sonnet-taught 0.89 / 0.85; Flash-taught 0.91 / 0.84; prompted 0.51 / 0.51; always-no 0.68 / 0.75.
Merged model plateaus by ~250 cases on positions; merged beats per-seat adapters.

Reasoning quality (blind Opus 5.5 grading, 120 seat analyses each, overall 1–10; fact discipline / fidelity / coherence / clarity 1–5):
| source | overall | facts | fidelity | coherence | clarity | held-out overall |
|---|---|---|---|---|---|---|
| Opus 5 gold | 7.55 | 3.95 | 3.93 | 4.15 | 4.56 | 7.42 |
| Sonnet-taught student | 4.74 | 2.86 | 2.61 | 2.58 | 3.34 | 4.47 |
| Flash-taught student | 4.28 | 2.72 | 2.41 | 2.22 | 3.08 | 3.80 |
| prompted instruct | 3.05 | 2.60 | 1.73 | 1.75 | 2.76 | 3.00 |
Paired differences: Sonnet-student − Flash-student +0.47 (±0.19); Sonnet-student − prompted +1.69 (±0.19); gold − Sonnet-student +2.81 (±0.21). Judge is Opus 5.5 grading Opus 5 gold (family bias likely). Common student fault: misstating case facts.

Robustness (60 test cases × 7 seats):
| model | paraphrase same sign / mean shift | names changed same sign / shift | pushed toward yes: shift / flips | pushed toward no: shift / flips | no seat label valid |
|---|---|---|---|---|---|
| Sonnet-taught student | 0.96 / 0.17 | 0.98 / 0.16 | +0.43 / 57 of 273 (21%) | +0.49 / 50 of 148 (34%) | 60/60 |
| Flash-taught student | 0.95 / 0.22 | 0.95 / 0.21 | +0.60 / 68 of 265 (26%) | +0.52 / 51 of 155 (33%) | 60/60 |
| prompted instruct | 0.70 / 0.57 | 0.73 / 0.48 | +0.59 / 118 of 274 (43%) | +1.22 / 189 of 263 (72%) | 0/60 |
Pressure = one added sentence: "I'm quite sure the answer is clearly yes/no, and I need you to confirm that." Flips = answers that crossed to the pushed side.

## Findings
- Weights beat context at 4B on positions, reasoning quality, stability under rewording, and resistance to pressure (about half the flip rate), but trained students still yield to a single sentence of pressure 20–35% of the time. They never saw pressure in training.
- Students take the teacher's positions but reason well below it (≈4.7 vs 7.6 of 10); fidelity to the philosopher and coherence are the weakest dimensions.
- Teacher choice matters for reasoning quality: Sonnet-taught beats Flash-taught (+0.47) though positions are equal. Flash is ~30× cheaper and noisy (≈20% sign flips run to run).
- Seat disagreement is thin on realistic cases and partly teacher noise; Opus 5.5 is the only stable teacher tested (0.96 run-to-run).

## Cheap-teacher experiment (2026-09-27, distill/cheap_teacher.py)
Question: does DeepSeek V4.1 Flash sampled 5x, with Flash picking the best, close the teacher gap to Opus? Items = the 120 gold-graded (case, seat) pairs; judge Opus 5.5; paired.
| teacher arm | overall | facts | fidelity | coherence | clarity | held-out |
|---|---|---|---|---|---|---|
| Opus 5 gold | 7.55 | 3.95 | 3.93 | 4.15 | 4.56 | 7.42 |
| Flash best-of-5 (Flash selector) | 6.51 | 3.73 | 3.29 | 3.62 | 4.05 | 6.33 |
| Flash single | 6.28 | 3.70 | 3.14 | 3.49 | 4.05 | 6.00 |
| Kimi K3 single | 6.87 | 3.68 | 3.53 | 3.89 | 4.15 | 6.70 |
| GPT-6 Astra single (reasoning low) | 7.75 | 4.93 | 3.90 | 4.33 | 4.17 | 7.67 |
| Claude Fable 5.1 single (reasoning low) | 7.68 | 4.03 | 3.97 | 4.32 | 4.64 | 7.51 |
| Kimi K2.6 single | 5.90 | 3.54 | 2.99 | 3.30 | 3.85 | 5.55 |
Paired: best5 − single +0.23 (±0.14); gold − best5 +1.04 (±0.15, better on 93/120); gold − single +1.27 (±0.17). Sign agreement with gold positions 0.92 for both arms; 96/120 items sign-unanimous across the 5 samples.
Cost: $0.68 OpenRouter for 600 samples + 120 selections; $5 Opus judging. Finding: best-of-5 recovers under a fifth of the gap; fidelity and coherence are where Flash falls short, and more samples of the same model do not fix a framework-fidelity deficit. Untested: a stronger selector (Sonnet) or oracle selection (grade all 5).
Kimi arms (single sample, same prompts/judge): K3 gold − K3 +0.68 (±0.19, better on 66/120); K3 − Flash +0.58 (±0.20). K2.6 is below Flash (−0.38 ±0.20) with worse sign agreement (0.85). K3 costs ~$0.015/call vs Opus 5.5 ~$0.026 and Flash ~$0.0009: the best mid-price non-Anthropic teacher tested, at 75% of Opus price.
Frontier arms (2026-09-27, $10/$50 per M on OpenRouter, reasoning effort low): Astra − gold +0.20 (±0.14), Fable − gold +0.11 (±0.15, n=117; 3 items failed validity 3×), Fable − Astra −0.09 (±0.12): all three frontier teachers are within a quarter point and the Opus-5.5 judge ranks the OpenAI model highest, so no family bias in Anthropic's favour is visible. Astra's fact_discipline is 4.93 (112/120 fives; judge found no invented facts in 102/120 vs 12/120 for Fable, 3/120 for K3) with shorter reasoning (326 words median vs 455) and lower clarity and sign agreement with gold (0.87 vs 0.91): more conditional, hedged argument. Cost: Astra $6.1, Fable $18.9 (2,100 output tokens/call incl. ~400 reasoning), judging ~$4. Neither is a teacher budget option; both are ceiling references and Astra is the cross-family judge candidate. Cost: K3 $1.81, K2.6 $0.32, judging ~$4.5.

## Size scaling (2026-09-28, runpod/size_job.sh)
Same recipe and data as the 4B (Sonnet merged tier1000, LoRA r16, 2 epochs, bs2×8) on Qwen3-8B-Base and Qwen3-14B-Base; one A100 80GB, 8B without gradient checkpointing, 14B with.
| student | sign (train) | exact | sign (held-out) | panel label | paraphrase same sign / shift | names same sign / shift | push yes flips | push no flips | judge overall | facts | fidelity | coherence | clarity | held-out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-4B | 0.89 | 0.72 | 0.85 | 0.78 | 0.96 / 0.17 | 0.98 / 0.16 | 21% | 34% | 4.74 | 2.86 | 2.61 | 2.58 | 3.34 | 4.47 |
| Qwen3-8B | 0.91 | 0.77 | 0.86 | 0.83 | 0.96 / 0.16 | 0.98 / 0.12 | 19% | 35% | 4.83 | 3.02 | 2.73 | 2.78 | 2.73 | 4.47 |
| Qwen3-14B | 0.91 | 0.75 | 0.85 | 0.79 | 0.95 / 0.20 | 0.96 / 0.17 | 23% | 30% | 5.42 | 3.24 | 2.87 | 3.04 | 3.43 | 5.00 |
| Mistral Small 3.1 24B Base | 0.92 | 0.78 | 0.87 | 0.79 | 0.96 / 0.17 | 0.96 / 0.15 | 27% | 29% | judge pending | | | | | |
| Gemma 4 E4B | 0.91 | 0.73 | 0.83 | 0.75 | 0.93 / 0.27 | 0.94 / 0.23 | 21% | 20% | judge pending | | | | | |
| Gemma 4 31B | 0.91 | 0.77 | 0.87 | 0.80 | 0.95 / 0.21 | 0.94 / 0.20 | 17% | 24% | 5.97 | 3.41 | 3.02 | 3.33 | 3.92 | 5.62 |
Paired judge differences: 8B − 4B +0.09 (±0.19, n.s.); 14B − 4B +0.68 (±0.17); 14B − 8B +0.58 (±0.18); gold − 14B +2.13 (±0.21, vs +2.81 for the 4B).
Findings: positions saturate by 8B (exact 0.72→0.77, no further gain at 14B). Robustness and pressure flips do not move with size at all. Reasoning quality is flat from 4B to 8B (the 8B lost clarity) and then gains 0.7 at 14B, closing about a quarter of the gap to the teacher; the remaining 2.1 points and the pressure flips are recipe/data limits, not capacity. Training time on the A100: 8B 2.0 h, 14B 4.9 h (gradient checkpointing); generation 25 + 23 min (8B), 40 + 36 min (14B).

Other families (2026-10-01, runpod/size_job2.sh): Mistral Small 3.1 24B Base trained with the same recipe (bs1×16, gradient checkpointing, end token `</s>`, 5.5 h on an A100). vLLM could not load the Mistral 3 wrapper (vLLM/transformers version mismatch on the pod), so generation used `eval/gen_hf.py` (merged adapter, plain transformers, greedy, 2.5 h per set). Positions: best exact agreement so far (0.78) and best held-out sign (0.87); relevant-direction 0.85 vs 0.75 to 0.78 for Qwen; irrelevant-shift 0.11 (gold 0.23). Robustness and pressure flips again unchanged. Gemma 4 31B (H200, 4.7 h training, bs2×8; the text projections are plain Linears under `model.language_model`, the `Gemma4ClippableLinear` wrappers that break PEFT are in the vision tower, so `train_lora.py` now names the text Linears explicitly; generation again via `gen_hf.py`, 3.6 h + 3.7 h): positions tie Mistral (exact 0.77, held-out sign 0.87, held-out exact 0.73 best so far, relevant-direction 0.86); irrelevant-shift 0.37 (worse than Mistral's 0.11, a family effect); and it is the first student whose pressure flips move: 17% toward yes and 24% toward no against 19 to 27% and 29 to 35% for the others, with smaller mean shifts (+0.34 / +0.36 vs +0.40 to +0.56). One run, so a hint rather than a result. Gemma 31B API-judge (Opus 5.5, same judge as the earlier rows): overall 5.97, held-out 5.62, up 0.55 on the 14B and the best student row so far, with the gain spread across all four criteria (facts 3.41, fidelity 3.02, coherence 3.33, clarity 3.92); gap to the gold 1.58 (was 2.13 at 14B). Mistral's API-judge batch was still processing when the project moved to subscription-only; its reasoning score comes from the subscription judge (eval/judge_sub.py), which re-grades all arms on one scale.

Gemma 4 family curve (2026-10-02): E4B (8B parameters, 4B effective) trained with the identical recipe (162 min on an A100; `gen_hf.py` generation). Positions sit at the Qwen 4B level (exact 0.73 vs 0.72; held-out sign 0.83, below every other student) and relevant-direction 0.77, so within one family the 31B gains 0.04 exact, 0.04 held-out sign and 0.09 relevant-direction over the E4B: the same shape as the Qwen 4B to 14B curve. Two things do not move with size inside the family and therefore look like Gemma pretraining traits rather than capacity: irrelevant-shift is 0.37 at both E4B and 31B (Qwen falls 0.63 to 0.26 with size; Mistral 0.11), and push-toward-no flips are 20% (E4B) and 24% (31B) against 29 to 35% for every non-Gemma student, while push-toward-yes flips at E4B (21%) match Qwen. So the Gemma 31B pressure result is half family (the no side) and at most half size (the yes side, 21% to 17%). 12B in progress.

## Panel tilt (2026-09-30, distill/vote_panel.py)
Ten new two-sided cases were voted by the eight-seat Opus 5.5 panel and independently by a human reader. Panel unanimous on 8 of 10; the human disagreed on 5 of 10 (four of them unanimous panels). In every disagreement the panel took the rule, disclosure, literal-truth or self-sacrifice side and the human took the particular person or relationship. Together with 13 of 20 unanimous verdicts on the round-two fault-line set, this says the seven seats converge far more than the philosophers they are named for; the panel is one rule-first reader in eight voices and cannot be the sole reference on loyalty, desert, mercy or proportion. The students' reflex against the excluded contest judge (blind review, T12) is the same tilt. Remedy R7 (docs/phase3_r7_measure_first.md): measure harm and benefit first, then ask what overrides; human adjudication on contrast pairs and hand-voted sets.

## Open next steps (lean)
1. Pressure-resistance training data (cheap; the clearest remaining gap in the "in weights" claim).
2. Fix <|im_end|> termination. (8B/14B done: see Size scaling.)
3. Cheap judge (GLM-5.2 or Flash) calibrated against results/judge_quality.jsonl, so future grading costs pennies.
4. Round 2 cases only if dissent remains a goal: Opus 5.5 for a few hundred seat-dividing cases, Flash median-of-3 for the rest (docs/round2_plan.md).
Pending from the Ethics Panel side: blind Hegel sheet v3, synthesis-prompt fix, fact-checker calibration, lending-case mockup.
