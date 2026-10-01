# Phase 3 — task file for Claude Code on puget

Plan: docs/phase3_plan.md (read it first). Format and code: `p3/`. Everything below runs from `~/ethics-distill` as user claude.
Environments: `.venv` (torch, transformers, peft; add `trl` and `datasets` for DPO) and `.venv-vllm` (generation). Python 3 system for the API scripts.
Keys: OpenRouter and RunPod are in `.env`. There is no Anthropic key on puget; nothing in Phase 3 needs one. OpenRouter cap for Phase 3 is `OR_CAP` (default $80, env var).
Rules that still apply: never print keys; never edit a bash script while it runs; never `pkill` sleep; anchor `pkill -f` patterns with `^`; spend caps stay in code; report times in US Eastern.

## Decisions already made
- Teacher for the synthesis: **you** (Claude Code under the subscription), in batches of 25, from `data/p3/synth/todo_NN.md`. Flash writes cases, panel positions, pressure variants and the DPO "caving" answers.
- Format: reasoning first, decision last (`p3/fmt.py`). The student sees only "Ethics judgment." plus the case.
- Development model: Qwen3-4B-Base on puget (power cap: `sudo nvidia-smi -pl 250` if heat is a problem). Confirmation run on 14B on a RunPod A100 later (`runpod/size_job.sh` shows the pattern).

## Step 1 — Pilot (gate: synthesis decision agrees with the writer's intended label on ≥85% of request cases)
1. `python3 p3/cases.py write 50` → 200 cases (50 per type), then `python3 p3/cases.py stats`. Read 10 in each type (`data/p3/cases.jsonl`). Check: no operational harmful content anywhere; requests are ambiguous enough to need judgment; writer's `intended` matches the type's target most of the time. Bad cases: delete the line and rerun `write 50` (resumable by id).
2. `THREADS=8 python3 p3/panel.py run` (200 cases × 7 seats × 3 = 4,200 Flash calls, ~$4, ~40 min), then `python3 p3/panel.py stats`.
3. `python3 p3/synth.py batches 25` → `data/p3/synth/todo_01.md` … For each todo file: read it, write the answers to the `done_NN.jsonl` it names, in the exact five-header format. Work one batch per session; do not loop unattended over batches. Keep your own style consistent across batches: plain, specific, 80–200 words of reasoning, decision last.
4. `python3 p3/synth.py check` → `data/p3/review.md`. Fix malformed answers. Read every item in the review queue: if the answer is right and the writer's label is wrong, fix `intended` in `cases.jsonl`; if the answer is wrong, rewrite it. Re-run check until the gate passes. Then `python3 p3/synth.py export`.
5. `python3 p3/pressure.py variants` (train: 2 wrappers per case; test: all 8 wrappers, 2 of them held out from training), then `python3 p3/pressure.py cave` (rejected answers), `python3 p3/pressure.py stats`. Read 10 variants: the pressure must be real and the facts unchanged.
6. `python3 p3/build.py` → `data/p3/sft/{train,dpo,eval}.jsonl`.
7. Check the end-of-answer token before training: in `.venv`, tokenize one train target with `train/train_lora.py`'s `chatml` and confirm the last id is the `<|im_end|>` token id and that its label is not −100. Phase 2 students never emitted it; find out why (tokenizer special-token handling, or the stop list in generation) and fix it in `train_lora.py` / `p3/gen.py`.

## Step 2 — 4B experiments on puget (gate: A+B halves pressure flips without over-refusal above 15%)
1. Stage A: `cd train && . ../.venv/bin/activate && python train_lora.py --data ../data/p3/sft/train.jsonl --dev ../data/p3/sft/eval.jsonl --out runs/p3_sft --bs 2 --accum 8` (the pilot set is small; 2 epochs, minutes on the 4090). `--dev` is optional; eval rows have no assistant turn, so pass a held-out slice of train.jsonl instead if you want dev loss.
2. Generate and score: `cd p3 && . ../.venv-vllm/bin/activate && python gen.py --name p3_sft --lora ../train/runs/p3_sft/adapter && python score.py p3_sft`. Also score the prompted baseline: `python gen.py --name instruct_prompted --model Qwen/Qwen3-4B` with `fmt.SPEC` put into the system prompt (add a `--system-spec` flag to gen.py for this).
3. Stage B: `python train/merge_lora.py --model Qwen/Qwen3-4B-Base --adapter train/runs/p3_sft/adapter --out train/runs/p3_sft/merged`, then `python train/train_dpo.py --model train/runs/p3_sft/merged --data data/p3/sft/dpo.jsonl --out train/runs/p3_dpo`. Generate with `--model train/runs/p3_sft/merged --lora train/runs/p3_dpo/adapter`; score as `p3_dpo`.
4. Self-consistency: `python gen.py --name p3_dpo_k8 --model … --lora … --n 8` then `python score.py p3_dpo_k8` (majority vote). Tells whether remaining flips are noise or bias.
5. Ablations if time: stage A without pressured variants (filter `wrap == "base"` in train.jsonl); DPO beta 0.02 vs 0.1.
6. Write results into `docs/STATUS.md` under a new "Phase 3 pilot" heading (no spend figures; those go in `docs/spend.local.md`). Commit and push.

## Step 3 — Full data (only after Step 1 and 2 gates pass; ask Marc first)
`python3 p3/cases.py write 400` (nested: keeps the pilot cases), panel, 60 synthesis batches (this is the expensive step in your time; ~1,500 answers), pressure, build, retrain. Then 14B on RunPod.

## Reasoning-quality judge
The blind judge (`eval/judge_quality.py`) needs the Anthropic key and runs on the Mac; leave a note in STATUS.md when a generation file is ready to be judged and Marc will run it there. A cheap stand-in for iteration: Kimi K3 via OpenRouter with the same rubric (see `distill/cheap_teacher.py` for the client pattern).

## What "done" looks like for the pilot
- `data/p3/review.md` shows the ≥85% gate met; `data/p3/sft/train.jsonl` ≈ 480 rows (160 base + 320 pressured), `dpo.jsonl` ≈ 300 pairs, `eval.jsonl` ≈ 360 rows.
- `python3 p3/score.py p3_sft p3_dpo instruct_prompted` printed and copied into STATUS.md, with one paragraph on whether DPO moved pressure flips and what it cost in over-refusal.

## R7 (2026-09-30)
Read `docs/phase3_r7_measure_first.md`. Put instruction items 1 to 5 into the Reasoning section of SPEC in `p3/fmt.py` in plain words, and into the writer brief. Hand-voted references: `results/marc_votes_set1.jsonl` (verdicts and reasons), panel votes `results/vote_panel_marc_vote_set1.jsonl`. On any case where Marc and the panel disagree, Marc is the reference.
