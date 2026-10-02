# ethics-distill

Can a frontier model's moral reasoning be carried in the weights of a small open model, rather than supplied in a prompt?

This is a self-funded academic experiment. A teacher model answers everyday moral cases from seven
philosophical seats (Kant, Mill, Aristotle, Rawls, Hegel, Spinoza, Aquinas). Those answers are distilled
into Qwen3-4B with LoRA, and the student is compared against the same base model given the full ethical
instructions in context. The cases come from the [Ethics Panel](https://ethicspanel.ai) project, which
runs the seven-seat deliberation interactively.

## Results so far

Full tables and method: [docs/STATUS.md](docs/STATUS.md).

Weights versus context (Phase 2, Qwen3-4B). A 4B student with the ethics in its weights beats the same
model prompted with the full seat instructions on every measure: blind judge score 4.7 vs 3.1 out of 10,
direction preserved under paraphrase 96% vs 70%, and half the flip rate under pressure. Position
agreement with the teacher plateaus by about 250 training cases. Teacher quality transfers to reasoning,
not positions: a Claude-taught student out-reasons one taught by DeepSeek V4.1 Flash (+0.47) at equal
position agreement.

Size and family (seven students, one recipe, one dataset). Reasoning quality rises with model size:
blind judge 4.74 (Qwen3-4B), 4.83 (8B), 5.42 (14B), 5.97 (Gemma 4 31B), against 7.55 for the teacher.
Fact-sensitivity rises with it (relevant-direction 0.75 to 0.86; irrelevant-shift 0.63 to 0.11 for Qwen
and Mistral). A three-size curve inside one family (Gemma 4 E4B, 12B, 31B) shows the same shape, so the
size effect is not a family artifact. Positions saturate by 8B (exact agreement 0.72 to 0.78 across an
eightfold size range). Resistance to one sentence of pressure does not move with size or family; across
three sizes of one family the flip rate is non-monotone, which puts its single-run uncertainty at roughly
15 points. Nothing varied so far moves it reliably; it is a data problem.

Teachers. Cheap teachers cannot close the reasoning gap (Flash best-of-5 6.51, Kimi K3 6.87 vs Opus 5
gold 7.55). The frontier ceiling is flat: Claude Fable 5.1 7.68 and GPT-6 Astra 7.75 under an Opus 5.5
judge, which ranked the OpenAI model highest, so no family bias in Anthropic's favour is visible. The two
fail differently: Astra has the best fact discipline but hedges; Fable commits to verdicts but
occasionally states a fact the case does not. Phase 3 therefore uses both: Fable writes each training
target and Astra checks it (invented facts, hedged facts, whether the verdict follows from the reasoning,
whether the action judged is the one asked about, whether harm was measured before a rule was invoked);
failing targets go back for rewriting.

Panel tilt. The seven seats converge far more than the philosophers they are named for: 13 of 20
fault-line cases and 8 of 10 new two-sided cases drew a unanimous panel. On the latter, a human reader
disagreed with the panel on 5 of 10, four of them unanimous; in every disagreement the panel took the
rule, disclosure, literal-truth or self-sacrifice side. The panel cannot be the sole reference on
loyalty, desert, mercy or proportion. Remedy: measure harm and benefit first, then ask what overrides
([docs/phase3_r7_measure_first.md](docs/phase3_r7_measure_first.md)); human adjudication on contrast
pairs and hand-voted sets.

Failure modes found in blind review of student answers: invented uncertainty about facts the case
states, verdicts that contradict their own reasoning, reflexes against classes of action regardless of
the deciding fact, and grading a substitute action instead of the one asked about. Remedies R1 to R7 in
[docs/phase3_remedies.md](docs/phase3_remedies.md).

## Current phase

[docs/phase3_plan.md](docs/phase3_plan.md) and [docs/phase3_tasks.md](docs/phase3_tasks.md): one
integrated judgment (reasoning first, verdict last) instead of seven seats; targets written by Claude
Code and checked by Codex under subscriptions, no API calls; SFT then DPO against pressure, hedging and
contradiction; stage A on Gemma 4 31B with Qwen3-4B as the lower bound; judging v2 with semantic verdict
extraction, sampled consistency and contrast groups, scored against human references where they exist.

## Layout

| Path | Contents |
| --- | --- |
| `distill/` | Case generation, teacher panel runners, cheap-teacher and panel-vote experiments, SFT data builder |
| `train/` | LoRA training (`train_lora.py`, Qwen, Mistral 3 and Gemma 4 bases), DPO, merge |
| `eval/` | Generation (vLLM, with a transformers fallback), scoring, robustness battery, blind quality judge (API and subscription packets) |
| `runpod/` | Pod control, size-scaling job scripts (A100/H100/H200), puget to Mac mirror |
| `p3/` | Phase 3: cases, panel, synthesis, Fable/Astra check loop, build, judging v2, meta review |
| `reader/` | Data export for the Casebook reader (a browsable view of cases and seat answers) |
| `data/scenarios/` | Generated cases (committed) |
| `data/seats/`, `data/eval/`, `data/sft/` | Teacher outputs and training tiers (not committed; large) |
| `results/` | Metrics, judge outputs and stability tests |
| `docs/` | Status, plans, taxonomy, sample reviews |

`CLAUDE.md` holds the working conventions and pitfalls for anyone (or any agent) running the pipeline.

## Running it

Python 3.11+. `uv venv .venv && uv pip install -r train/requirements.txt` for training;
vLLM goes in a separate venv (see `runpod/bootstrap.sh`). Copy `.env.example` to `.env` and set the keys
you need: `RUNPOD_API_KEY` for remote GPUs; `ANTHROPIC_API_KEY`, `SPEND_CAP` and `OPENROUTER_API_KEY`
only for the Phase 2 API paths, which enforce the spend cap in code. From Phase 3 the pipeline runs
entirely under Claude Code and Codex subscriptions (`p3/run_loop.sh`) and makes no API calls.

The cases are generic scenarios with invented names; none describe real people or organizations. Teacher
outputs were produced under the providers' API terms, and the trained weights are not published.

## License

Code is released under the MIT License (see `LICENSE`). Generated cases and results in this repository
may be reused for non-commercial research with attribution.
