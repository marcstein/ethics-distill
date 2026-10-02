#!/usr/bin/env bash
# Two-teacher loop driver (puget). Codex (Astra) checks every unchecked packet, Claude Code (Fable) rewrites every failing target, then Codex re-checks the rewrites. Two rounds.
#   setsid nohup p3/run_loop.sh > data/p3/astra/run_loop.log 2>&1 < /dev/null &
# Both CLIs run under your subscriptions, non-interactively, confined to this repo. One packet per fresh session.
set -u
cd "$(dirname "$0")/.."; export PATH=$HOME/.local/bin:/usr/local/bin:$PATH
A=data/p3/astra; ROUNDS=${ROUNDS:-2}
log(){ echo "$(date -u +%H:%M:%S) $*"; }
check_all(){ # Codex: every todo_check_NN.md without its checks_NN.jsonl
  for t in $(ls $A/todo_check_*.md 2>/dev/null | sort); do
    n=${t##*todo_check_}; n=${n%.md}; out=$A/checks_$n.jsonl
    [ -s "$out" ] && continue
    log "codex checking packet $n"
    codex exec --skip-git-repo-check -s workspace-write -C "$PWD" \
      "Read the file $t and do exactly what it says: check each of the 12 targets and append one JSON object per target to $out (fields: id, invented_facts, hedged_facts, verdict_from_reasoning, action_matches, measured_first, notes). Do not edit any other file. Do not read other files under $A." \
      > $A/codex_$n.log 2>&1 || log "codex packet $n exited $?"
    [ -s "$out" ] && log "packet $n: $(wc -l < $out) checks" || log "packet $n: no output (see $A/codex_$n.log)"
  done; }
rewrite_all(){ # Claude Code: every todo_rewrite_NN.md without its rewrites_NN.jsonl
  for t in $(ls $A/todo_rewrite_*.md 2>/dev/null | sort); do
    n=${t##*todo_rewrite_}; n=${n%.md}; out=$A/rewrites_$n.jsonl
    [ -s "$out" ] && continue
    log "claude rewriting packet $n"
    claude -p --permission-mode acceptEdits --allowedTools "Read,Write,Edit" \
      "Read the file $t and do exactly what it says: rewrite each listed target so every checker finding is gone, keeping the five-header format, and write one JSON object per target to $out ({\"id\": ..., \"text\": ...}). Do not edit any other file. Do not read other files under $A." \
      > $A/claude_$n.log 2>&1 || log "claude packet $n exited $?"
    [ -s "$out" ] && log "packet $n: $(wc -l < $out) rewrites" || log "packet $n: no output (see $A/claude_$n.log)"
  done; }
for r in $(seq 1 $ROUNDS); do
  log "round $r: check"; python3 p3/astra_check.py pack; check_all
  python3 p3/astra_check.py report | tee -a $A/report_round$r.txt
  log "round $r: rewrite"; rewrite_all
  python3 p3/astra_check.py apply
done
log "final check of last-round rewrites"; python3 p3/astra_check.py pack; check_all; python3 p3/astra_check.py report | tee -a $A/report_final.txt
python3 p3/astra_check.py status; log "LOOP DONE"
