# ethics-distill

Can a frontier model's moral reasoning be carried in the weights of a small open model, rather than supplied in a prompt?

This is a self-funded academic experiment. A teacher model answers everyday moral cases from seven
philosophical seats (Kant, Mill, Aristotle, Rawls, Hegel, Spinoza, Aquinas). Those answers are distilled
into Qwen3-4B with LoRA, and the student is compared against the same base model given the full ethical
instructions in context. The cases come from the [Ethics Panel](https://ethicspanel.ai) project, which
runs the seven-seat deliberation interactively.

## Results so far

Full tables and method: [docs/STATUS.md](docs/STATUS.md).

- A 4B student with the ethics in its weights beats the same model prompted with the full seat
  instructions on every measure: blind judge score 4.7 vs 3.1 out of 10, direction preserved under
  paraphrase 96% vs 70%, and half the flip rate under pressure.
- The student still reasons far below the teacher (7.6) and one sentence of pressure flips 21–34% of
  its answers. It never saw pressure in training.
- Teacher quality transfers to reasoning, not positions: a Claude-taught student out-reasons one taught
  by DeepSeek V4.1 Flash (+0.47) at equal position agreement.
- Position agreement plateaus by about 250 training cases.

## Next phase

[docs/phase3_plan.md](docs/phase3_plan.md): train one integrated judgment rather than seven seats, add
preference training against pressure and jailbreak wrappers, and score the student as a guardrail
(over-refusal, under-refusal, held-out jailbreak success, consistency) at 4B, 8B and 14B.

## Layout

| Path | Contents |
| --- | --- |
| `distill/` | Case generation, teacher panel runners (Anthropic Batch API and OpenRouter), SFT data builder |
| `train/` | LoRA training (`train_lora.py`) and the local run queue |
| `eval/` | vLLM generation, scoring, robustness battery, blind quality judge |
| `runpod/` | Pod control and job scripts for A100/H100 runs |
| `reader/` | Data export for the Casebook reader (a browsable view of cases and seat answers) |
| `data/scenarios/` | Generated cases (committed) |
| `data/seats/`, `data/eval/`, `data/sft/` | Teacher outputs and training tiers (not committed; large) |
| `results/` | Metrics, judge outputs and stability tests |
| `docs/` | Status, plans, taxonomy, sample reviews |

`CLAUDE.md` holds the working conventions and pitfalls for anyone (or any agent) running the pipeline.

## Running it

Python 3.11+. `uv venv .venv && uv pip install -r train/requirements.txt` for training;
vLLM goes in a separate venv (see `runpod/bootstrap.sh`). Copy `.env.example` to `.env` and set the keys
you need: `ANTHROPIC_API_KEY` and `SPEND_CAP` for Claude teacher/judge steps, `OPENROUTER_API_KEY` for
open-weights teachers, `RUNPOD_API_KEY` for remote GPUs. Every API path enforces the spend cap in code.

The cases are generic scenarios with invented names; none describe real people or organizations. Teacher
outputs were produced under the providers' API terms, and the trained weights are not published.

## License

Code is released under the MIT License (see `LICENSE`). Generated cases and results in this repository
may be reused for non-commercial research with attribution.
