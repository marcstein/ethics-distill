#!/usr/bin/env bash
# Full 4B training grid, in priority order. Skips any run whose adapter already exists. Stop with: pkill -f queue.sh; pkill -f train_lora.py
cd "$(dirname "$0")"; source ../.venv/bin/activate; mkdir -p logs
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
MEM="--bs 2 --accum 8"   # same effective batch (16) as bs4x4; bs4 OOMed on long Kant examples
SEATS="Hegel Kant KantModern Mill Aristotle Rawls Spinoza Aquinas"
run() { out=$1; shift; [ -d "$out/adapter" ] && { echo "skip $out"; return; }
        echo "$(date -u +%FT%TZ) start $out"; python train_lora.py --out "$out" $MEM "$@" > "logs/$(basename $out).log" 2>&1 \
          && echo "$(date -u +%FT%TZ) done $out" || echo "$(date -u +%FT%TZ) FAILED $out"; }
for s in $SEATS; do run runs/seat_${s}_t1000 --data ../data/sft/seat/$s/tier1000.jsonl --dev-seat $s; done
run runs/merged_t1000 --data ../data/sft/merged/tier1000.jsonl
for t in 500 250; do for s in $SEATS; do run runs/seat_${s}_t$t --data ../data/sft/seat/$s/tier$t.jsonl --dev-seat $s; done; done
for t in 500 250; do run runs/merged_t$t --data ../data/sft/merged/tier$t.jsonl; done
echo "$(date -u +%FT%TZ) QUEUE COMPLETE"
