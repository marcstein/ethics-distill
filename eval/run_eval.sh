#!/usr/bin/env bash
# Waits for the training queue to finish, then generates on the test set for every config. Skips configs already generated.
cd "$(dirname "$0")"; source ../.venv-vllm/bin/activate; mkdir -p gen logs
export VLLM_USE_FLASHINFER_SAMPLER=0   # flashinfer JIT needs nvcc, which puget lacks
until grep -q "QUEUE COMPLETE" ../train/queue.log; do sleep 120; done
g() { n=$1; shift; [ -s gen/$n.jsonl ] && { echo "skip $n"; return; }
      echo "$(date -u +%FT%TZ) start $n"; python gen.py --name $n "$@" > logs/$n.log 2>&1 && echo "$(date -u +%FT%TZ) done $n" || echo "$(date -u +%FT%TZ) FAILED $n"; }
g merged_t1000  --lora ../train/runs/merged_t1000/adapter
g seat_t1000    --lora "../train/runs/seat_{seat}_t1000/adapter"
g instruct_full --prompt full --model Qwen/Qwen3-4B --nothink
g base_full     --prompt full
g base_label
for t in 500 250; do g merged_t$t --lora ../train/runs/merged_t$t/adapter; g seat_t$t --lora "../train/runs/seat_{seat}_t$t/adapter"; done
echo "$(date -u +%FT%TZ) EVAL GEN COMPLETE"
