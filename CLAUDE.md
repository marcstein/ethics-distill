# ethics-distill — instructions for Claude Code

Research project (Marc Stein): can the Ethics Panel's seven-seat moral reasoning be distilled into the weights of a small open model?
Seats: Kant (historical), Mill, Aristotle, Rawls, Hegel, Spinoza, Aquinas; "KantModern" (contemporary Kantian) is an annotation, never counted in the panel.
Results so far: docs/STATUS.md (read it first). Plans: docs/round2_plan.md. Production app ../ethics-panel is out of scope — never modify it.

## Conventions
- Times to Marc in US Eastern. Commits as `Marc Stein <marc.stein@gmail.com>`.
- Never print, echo or copy API keys. Keys live only in `.env` (gitignored): ANTHROPIC_API_KEY (Mac only unless Marc adds it), OPENROUTER_API_KEY, RUNPOD_API_KEY, SPEND_CAP.
- Spend is enforced in code: Anthropic via `distill/common.py` (`check_cap`, ledger results/spend_ledger.jsonl, SPEND_CAP in .env);
  OpenRouter via `distill/bakeoff.py` (ledger results/openrouter_ledger.jsonl, cap ORCAP/OR_CAP). Ask Marc before raising any cap.
- Generic scenarios only: no real people, companies or client situations. Clinical and biotech stay held out of training.
- Prefer cheap paths: DeepSeek V4.1 Flash (OpenRouter) for bulk teaching; Opus 5.5 only for small gold sets; Anthropic Batch API (half price) when latency is fine.

## Layout
- distill/: data pipeline. generate.py (round-1 case writer), gen_r2.py (round-2 fault-line writer), panel.py (seat panel via Anthropic, batch + retry),
  bakeoff.py (OpenRouter teacher calls: `call(model, seat, case, temperature)`), teach_or.py (full panel with an OpenRouter teacher, resumable),
  build_sft.py (chat-format SFT tiers; `--seats FILE --out sft_x`), sft_format.py (render/parse the student format), seat_prompts*.py, kant_modern_prompt.py.
- train/train_lora.py: LoRA SFT, Qwen3-4B-Base, loss on assistant turn only. Use `--bs 2 --accum 8` (bs4 OOMs on long Kant examples); `--no-gc` on 80GB+ GPUs.
- eval/: gen.py (vLLM generation; `--lora`, `--prompt full`, `--test FILE`), score.py (positions vs gold), judge_quality.py (blind Opus grading),
  make_robust.py + robust_score.py (paraphrase / name-change / pressure / no-label battery).
- runpod/: rp.py (start/stop pods named `ed-*` only), bootstrap.sh (per-pod env), pod_job.sh (train+gen), robust_job.sh.
- data/: scenarios (committed), seats/ sft/ sft_flash/ eval/ (not committed; large). results/: metrics and ledgers.

## How to run things
- Positions eval: `cd eval && python3 score.py gen/*.jsonl` → results/eval_table.md.
- Train + test-set generation on RunPod: `cd runpod && (setsid nohup ./pod_job.sh TAG > pod_TAG.log 2>&1 < /dev/null &)` (expects data/sft_TAG/merged/tier1000.jsonl).
  GEN_ONLY=1 reuses an existing adapter. A100 80GB is tried first (~$1.59/h; as fast as an H200 for a 4B LoRA).
- Local training on puget's 4090 is fine; ask Marc to cap power first (`sudo nvidia-smi -pl 250`) and prefer overnight runs.
- vLLM: always `export VLLM_USE_FLASHINFER_SAMPLER=0` (no nvcc here). Generation uses `.venv-vllm`, training `.venv`.

## Pitfalls already paid for
- Students never emit <|im_end|> (untrained token row; LoRA can't raise it). score.py truncates after the first "Would change if:" line. Fix next training run with PEFT `trainable_token_indices` for <|im_end|>, or end targets with <|endoftext|>.
- Opus 5.5 rejects forced tool_choice (use `{"type":"auto"}`) and thinks by default: give it max_tokens ≥ 3000 or tool calls get truncated.
- Sonnet 5 plain-text calls: set `"thinking": {"type": "disabled"}`. Strings-only tool schemas (arrays get garbled).
- OpenRouter Flash is not deterministic even at temperature 0; single samples flip sign ~20% run to run. Use median of 3 when stability matters.
- RunPod: never `pkill` a `sleep` process — pod_job watchdogs terminate pods when their sleep ends. pod_job copies results back before any termination.
- `pkill -f name` also matches your own shell if the pattern is in the command line; anchor patterns (`^python train_lora`).
- Background jobs: use `setsid nohup ... < /dev/null &` and write results incrementally (append per item) so timeouts lose nothing.
