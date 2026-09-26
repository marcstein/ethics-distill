#!/usr/bin/env bash
# Run on puget:  setsid nohup ./pod_job.sh flash > pod_flash.log 2>&1 < /dev/null &
# Rents one GPU, trains the merged student on data/sft_<tag>, generates on the test set, copies results back, terminates the pod.
# The pod is terminated on ANY exit (trap) and after a hard wall-clock limit, so it can never sit idle and bill.
set -u
TAG=${1:?tag}; ED=$HOME/ethics-distill; cd $ED/runpod
LIMIT=${LIMIT:-10800}   # seconds
log(){ echo "$(date -u +%H:%M:%S) $*"; }
RP="python3 $ED/runpod/rp.py"
SSH=""
copyback(){ [ -n "$SSH" ] || return 0; log "copying back"; mkdir -p $ED/train/runs $ED/eval/gen
  $SSH "cd /root/ed && tar czf - train/runs train.out gen.out eval/gen 2>/dev/null" | (cd $ED && tar xzf -) || true; }
cleanup(){ copyback; log "terminating pod"; $RP down || true; }
trap cleanup EXIT
( sleep $LIMIT; log "wall-clock limit hit"; $RP down ) & WATCH=$!
for g in "NVIDIA A100-SXM4-80GB" "NVIDIA A100 80GB PCIe" "NVIDIA H100 80GB HBM3" "NVIDIA H200"; do
  python3 rp.py up "$g" ed-train && break; sleep 5; done
T=""
for i in $(seq 1 150); do T=$(python3 rp.py ssh | grep -o "root@[0-9.]* -p [0-9]*" | head -1); [ -n "$T" ] && break; sleep 10; done
[ -z "$T" ] && { log "no ssh endpoint"; exit 1; }
HOST=${T% -p *}; PORT=${T##* -p }; SSH="ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -p $PORT $HOST"; SCPP="-P $PORT"
log "pod at $HOST:$PORT"; python3 rp.py ssh
for i in $(seq 1 30); do $SSH true 2>/dev/null && break; sleep 10; done
scp -q $SCPP -o StrictHostKeyChecking=accept-new bootstrap.sh $HOST:/root/ && $SSH "SKIP_TRAIN_ENV=1 bash /root/bootstrap.sh" || { log "bootstrap failed"; exit 1; }
cd $ED && tar czf - train/runs/merged_t1000/adapter train/runs/flash_merged_t1000/adapter eval/robust.jsonl eval/gen.py eval/baseline_prompts.json | $SSH "cd /root/ed && tar xzf -"
# Long steps run detached on the pod (nohup) and are polled, so a dropped SSH connection cannot kill them.
remote(){ # remote NAME CMD  -> runs CMD detached, waits for NAME.done / NAME.fail
  $SSH "cd /root/ed && rm -f $1.done $1.fail && (nohup bash -c '$2 && touch /root/ed/$1.done || touch /root/ed/$1.fail' > /root/ed/$1.out 2>&1 < /dev/null &)"
  while true; do sleep 60
    S=$($SSH "cd /root/ed; [ -f $1.done ] && echo done; [ -f $1.fail ] && echo fail; tail -c 300 $1.out | tr '\r' '\n' | tail -1" 2>/dev/null) || { log "ssh poll failed, retrying"; continue; }
    echo "$S" | tail -1 | cut -c1-160; echo "$S" | grep -q '^done' && return 0; echo "$S" | grep -q '^fail' && return 1; done; }
log "generating robustness battery"
G="cd /root/ed/eval && . ../.venv-vllm/bin/activate && export VLLM_USE_FLASHINFER_SAMPLER=0 && python gen.py --test robust.jsonl"
remote rob1 "$G --name robust_merged_t1000 --lora ../train/runs/merged_t1000/adapter" || log "sonnet-student gen failed"
remote rob2 "$G --name robust_flash_merged_t1000 --lora ../train/runs/flash_merged_t1000/adapter" || log "flash-student gen failed"
remote rob3 "$G --name robust_instruct_full --prompt full --model Qwen/Qwen3-4B --nothink" || log "instruct gen failed"
kill $WATCH 2>/dev/null; copyback; ls -la $ED/eval/gen/robust_*; log "POD JOB DONE"
