#!/usr/bin/env bash
# Run on puget:  setsid nohup ./size_job.sh > pod_size.log 2>&1 < /dev/null &
# Size-scaling arm: trains Qwen3-8B-Base and Qwen3-14B-Base on the Sonnet merged tier1000 data (same recipe as the 4B),
# generates the test set and the robustness battery for each, copies everything back, terminates the pod.
# One pod for both models; each model's steps are skipped if its outputs already exist (resumable).
set -u
ED=$HOME/ethics-distill; cd $ED/runpod
MODELS=${MODELS:-"8B 14B"}
LIMIT=${LIMIT:-28800}   # 8 h hard wall clock
log(){ echo "$(date -u +%H:%M:%S) $*"; }
RP="python3 $ED/runpod/rp.py"
SSH=""
copyback(){ [ -n "$SSH" ] || return 0; log "copying back"; mkdir -p $ED/train/runs $ED/eval/gen
  $SSH "cd /root/ed && tar czf - --exclude='*/checkpoint-*' train/runs *.out eval/gen 2>/dev/null" | (cd $ED && tar xzf -) || true; }
cleanup(){ copyback; log "terminating pod"; $RP down || true; }
trap cleanup EXIT
( sleep $LIMIT; log "wall-clock limit hit"; $RP down ) & WATCH=$!
for g in "NVIDIA A100-SXM4-80GB" "NVIDIA A100 80GB PCIe" "NVIDIA H100 80GB HBM3" "NVIDIA H200"; do
  python3 rp.py up "$g" ed-size && break; sleep 5; done
T=""
for i in $(seq 1 150); do T=$(python3 rp.py ssh | grep -o "root@[0-9.]* -p [0-9]*" | head -1); [ -n "$T" ] && break; sleep 10; done
[ -z "$T" ] && { log "no ssh endpoint"; exit 1; }
HOST=${T% -p *}; PORT=${T##* -p }; SSH="ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -p $PORT $HOST"; SCPP="-P $PORT"
log "pod at $HOST:$PORT"; python3 rp.py ssh
for i in $(seq 1 30); do $SSH true 2>/dev/null && break; sleep 10; done
scp -q $SCPP -o StrictHostKeyChecking=accept-new bootstrap.sh $HOST:/root/ && $SSH "bash /root/bootstrap.sh" || { log "bootstrap failed"; exit 1; }
cd $ED && tar czf - data/sft/merged/tier1000.jsonl data/sft/dev.jsonl data/sft/test.jsonl eval/robust.jsonl train/train_lora.py eval/gen.py eval/baseline_prompts.json | $SSH "cd /root/ed && tar xzf -"
remote(){ # remote NAME CMD  -> runs CMD detached on the pod, waits for NAME.done / NAME.fail
  $SSH "cd /root/ed && rm -f $1.done $1.fail && (nohup bash -c '$2 && touch /root/ed/$1.done || touch /root/ed/$1.fail' > /root/ed/$1.out 2>&1 < /dev/null &)"
  while true; do sleep 60
    S=$($SSH "cd /root/ed; [ -f $1.done ] && echo done; [ -f $1.fail ] && echo fail; tail -c 300 $1.out | tr '\r' '\n' | tail -1" 2>/dev/null) || { log "ssh poll failed, retrying"; continue; }
    echo "$S" | tail -1 | cut -c1-160; echo "$S" | grep -q '^done' && return 0; echo "$S" | grep -q '^fail' && return 1; done; }
for M in $MODELS; do
  NAME=q${M}_merged_t1000; HF=Qwen/Qwen3-${M}-Base
  GC=""; [ "$M" = 8B ] && GC="--no-gc"     # 14B keeps gradient checkpointing; 8B without it fits comfortably on 80 GB
  if [ -f $ED/train/runs/$NAME/adapter/adapter_config.json ]; then log "skip train $NAME"
  else log "training $NAME"
    remote train_$M "cd /root/ed/train && . ../.venv/bin/activate && export HF_HUB_ENABLE_HF_TRANSFER=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True && python train_lora.py --model $HF --data ../data/sft/merged/tier1000.jsonl --out runs/$NAME --bs 2 --accum 8 $GC" \
      || { log "training $NAME failed"; $SSH "tail -c 2000 /root/ed/train_$M.out"; copyback; continue; }
    copyback
  fi
  G="cd /root/ed/eval && . ../.venv-vllm/bin/activate && export VLLM_USE_FLASHINFER_SAMPLER=0 && python gen.py --model $HF --lora ../train/runs/$NAME/adapter"
  log "generating test set $NAME";  remote gen_$M "$G --name $NAME" || log "gen $NAME failed"
  log "generating robustness $NAME"; remote rob_$M "$G --name robust_$NAME --test robust.jsonl" || log "robust gen $NAME failed"
  copyback
done
kill $WATCH 2>/dev/null; copyback; ls -la $ED/eval/gen/q*_merged_t1000.jsonl $ED/eval/gen/robust_q* 2>/dev/null; log "POD JOB DONE"
