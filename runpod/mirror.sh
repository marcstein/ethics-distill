#!/usr/bin/env bash
# Pull everything a RunPod job leaves on puget into the Mac repo folder (a second copy; puget is the first).
# Run from the Mac side:  ./runpod/mirror.sh
P=claude@192.168.1.173:ethics-distill; cd "$(dirname "$0")/.."
rsync -a --include='*/' --include='adapter/***' --include='summary.json' --exclude='*' $P/train/runs/ train/runs/
rsync -a $P/eval/gen/ eval/gen/
mkdir -p logs/pod && rsync -a --include='*.out' --include='*.log' --exclude='*' $P/ logs/pod/ && rsync -a $P/runpod/*.log logs/pod/
rsync -a --include='*/' --include='*.jsonl' --include='*.json' --include='*.md' --exclude='*' $P/data/p3/ data/p3/
echo "mirrored $(date -u +%FT%TZ): $(ls train/runs | wc -l) runs, $(ls eval/gen | wc -l) gen files, $(du -sh train/runs | cut -f1) adapters"
