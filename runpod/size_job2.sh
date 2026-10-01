#!/usr/bin/env bash
# Run on puget:  setsid nohup ./size_job2.sh > pod_size2.log 2>&1 < /dev/null &
# Size-scaling arm 2: dense bases from other families, same Sonnet merged tier1000 recipe as the 4B/8B/14B.
# One pod per model (different GPU classes). Each: train (LoRA, gradient checkpointing), gen test set, gen robustness battery, copy back, terminate.
# Spec per model:  TAG|HF_ID|GPU list (comma)|BS|ACCUM
set -u
ED=$HOME/ethics-distill; cd $ED/runpod
SPECS=${SPECS:-"mistral24B|mistralai/Mistral-Small-3.1-24B-Base-2503|NVIDIA A100-SXM4-80GB,NVIDIA A100 80GB PCIe,NVIDIA H100 80GB HBM3|1|16
gemma31B|google/gemma-4-31B|NVIDIA H200 NVL,NVIDIA H200,NVIDIA B200|2|8"}
LIMIT=${LIMIT:-39600}   # 11 h hard wall clock per model
log(){ echo "$(date -u +%H:%M:%S) $*"; }
RP="python3 $ED/runpod/rp.py"
SSH=""
copyback(){ [ -n "$SSH" ] || return 0; log "copying back"; mkdir -p $ED/train/runs $ED/eval/gen
  $SSH "cd /root/ed && tar czf - --exclude='*/checkpoint-*' train/runs *.out eval/gen 2>/dev/null" | (cd $ED && tar xzf -) || true; }
cleanup(){ copyback; log "terminating pod"; $RP down || true; }
trap cleanup EXIT
remote(){ # remote NAME CMD  -> runs CMD detached on the pod, waits for NAME.done / NAME.fail
  $SSH "cd /root/ed && rm -f $1.done $1.fail && (nohup bash -c '$2 && touch /root/ed/$1.done || touch /root/ed/$1.fail' > /root/ed/$1.out 2>&1 < /dev/null &)"
  while true; do sleep 60
    S=$($SSH "cd /root/ed; [ -f $1.done ] && echo done; [ -f $1.fail ] && echo fail; tail -c 300 $1.out | tr '\r' '\n' | tail -1" 2>/dev/null) || { log "ssh poll failed, retrying"; continue; }
    echo "$S" | tail -1 | cut -c1-160; echo "$S" | grep -q '^done' && return 0; echo "$S" | grep -q '^fail' && return 1; done; }
exec 3<<< "$SPECS"
while IFS='|' read -r -u 3 TAG HF GPUS BS ACCUM; do
  [ -z "$TAG" ] && continue
  NAME=${TAG}_merged_t1000
  if [ -f $ED/eval/gen/robust_$NAME.jsonl ]; then log "skip $TAG (outputs exist)"; continue; fi
  ( sleep $LIMIT; log "wall-clock limit hit for $TAG"; $RP down ) & WATCH=$!
  UP=0; IFS=',' read -ra GL <<< "$GPUS"
  for g in "${GL[@]}"; do python3 rp.py up "$g" ed-size2 && { UP=1; break; }; sleep 5; done
  [ $UP = 1 ] || { log "no GPU available for $TAG"; kill $WATCH 2>/dev/null; continue; }
  T=""; for i in $(seq 1 150); do T=$(python3 rp.py ssh | grep -o "root@[0-9.]* -p [0-9]*" | head -1); [ -n "$T" ] && break; sleep 10; done
  [ -z "$T" ] && { log "no ssh endpoint"; $RP down; kill $WATCH 2>/dev/null; continue; }
  HOST=${T% -p *}; PORT=${T##* -p }; SSH="ssh -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -p $PORT $HOST"; SCPP="-P $PORT"
  log "$TAG pod at $HOST:$PORT"; python3 rp.py ssh
  for i in $(seq 1 30); do $SSH true 2>/dev/null && break; sleep 10; done
  scp -q $SCPP -o StrictHostKeyChecking=accept-new bootstrap.sh $HOST:/root/ && $SSH "bash /root/bootstrap.sh" || { log "bootstrap failed"; $RP down; kill $WATCH 2>/dev/null; SSH=""; continue; }
  (cd $ED && tar czf - data/sft/merged/tier1000.jsonl data/sft/dev.jsonl data/sft/test.jsonl eval/robust.jsonl train/train_lora.py eval/gen.py eval/gen_hf.py eval/baseline_prompts.json) | $SSH "cd /root/ed && tar xzf -"
  if [ -f $ED/train/runs/$NAME/adapter/adapter_config.json ]; then log "adapter exists, uploading and skipping training"; (cd $ED && tar czf - train/runs/$NAME/adapter) | $SSH "cd /root/ed && tar xzf -"; TRAINED=1; else TRAINED=0; fi
  log "training $NAME on $HF"
  if [ $TRAINED = 1 ] || remote train_$TAG "cd /root/ed/train && . ../.venv/bin/activate && export HF_HUB_ENABLE_HF_TRANSFER=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True && python train_lora.py --model $HF --data ../data/sft/merged/tier1000.jsonl --out runs/$NAME --bs $BS --accum $ACCUM --end eos"; then
    copyback
    G="cd /root/ed/eval && . ../.venv-vllm/bin/activate && export PATH=\$HOME/.local/bin:\$PATH; VIRTUAL_ENV=/root/ed/.venv-vllm uv pip install -q 'mistral_common[opencv]' timm 2>&1 | tail -2; export VLLM_USE_FLASHINFER_SAMPLER=0 && python gen.py --model $HF --lora ../train/runs/$NAME/adapter"
    H="cd /root/ed/eval && . ../.venv/bin/activate && python gen_hf.py --model $HF --lora ../train/runs/$NAME/adapter --bs ${HFBS:-16}"
    log "generating test set $NAME";  remote gen_$TAG "$G --name $NAME" || { log "vLLM gen failed, falling back to transformers"; remote genhf_$TAG "$H --name $NAME" || log "gen $NAME failed"; }
    log "generating robustness $NAME"; remote rob_$TAG "$G --name robust_$NAME --test robust.jsonl" || { log "vLLM robust failed, falling back to transformers"; remote robhf_$TAG "$H --name robust_$NAME --test robust.jsonl" || log "robust gen $NAME failed"; }
  else log "training $TAG failed"; $SSH "tail -c 3000 /root/ed/train_$TAG.out"; fi
  copyback; log "terminating pod for $TAG"; $RP down || true; SSH=""; kill $WATCH 2>/dev/null
done
ls -la $ED/eval/gen/*_merged_t1000.jsonl 2>/dev/null; log "POD JOB DONE"
