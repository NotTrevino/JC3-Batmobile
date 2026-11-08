#!/bin/bash
# Hands-free smart-search chase: search (chase_candidates.py, built by a Freebuff card) -> local judge
# (chase_judge.py on llama-server, Qwen3.5-4B, free) -> verify (a DeepSeek queue card for the found=true hits only).
# Runs beside keeper.sh; every step is idempotent, so a restart just continues.
P=E:/Modding/JC3-Batmobile; B=$P/tmp/freebuff; G=E:/Modding/_BmAKgrab/chase
CAND=$G/candidates.jsonl; VERD=$G/verdicts.jsonl; S=$P/Tools/scripts/chase
LLAMA=E:/AI/llama/llama-server.exe; MODEL=E:/AI/models/Qwen3.5-4B-Q6_K.gguf
log(){ echo "$(date -Is) $*" >> $B/chase_pipeline.log; }
lines(){ [ -f "$1" ] && grep -c . "$1" || echo 0; }
server_up(){ curl -s --max-time 5 http://127.0.0.1:8080/health | grep -q ok; }
start_server(){
  log "starting llama-server"
  powershell.exe -NoProfile -Command "Start-Process -WindowStyle Hidden '$LLAMA' -ArgumentList '-m','$MODEL','-t','4','-np','1','-c','32768','--host','127.0.0.1','--port','8080','--jinja','--alias','qwen3.5-4b' -RedirectStandardError 'E:/AI/llama-server-qwen35.log'"
  for i in $(seq 60); do server_up && return 0; sleep 5; done; log "llama-server did not come up"; return 1; }
judge_running(){ [ -f $B/judge.pid ] && kill -0 "$(cat $B/judge.pid)" 2>/dev/null; }
log "pipeline start pid $$"
while true; do
  nc=$(lines $CAND); nv=$(lines $VERD)
  if [ "$nc" -gt 0 ] && [ "$nv" -lt "$nc" ] && ! judge_running; then
    # Search done and judging incomplete: judge the rest (resumable; ids already judged are skipped).
    server_up || start_server
    if server_up; then
      python $S/chase_judge.py --in $CAND --out $VERD >> $B/judge.log 2>&1 &
      echo $! > $B/judge.pid; log "judge started on $((nc - nv)) candidates (pid $!)"
    fi
  fi
  if [ "$nc" -gt 0 ] && [ "$nv" -ge "$nc" ] && [ ! -f $B/queue/060-chase-verify.txt ] && [ ! -f $B/done/060-chase-verify.txt ] \
     && ! ls $B/running/*060-chase-verify.txt >/dev/null 2>&1; then
    nf=$(grep -c '"found": true' $VERD)
    cat > $B/queue/060-chase-verify.txt <<EOF
DONE: $P/tmp/freebuff/reports/chase-verify.md
ONLY: freebuff
EST: 50
You are working in $P (Batman: Arkham Knight Batmobile -> Just Cause 3 mod, offline research). A local LLM triaged $nc search hits for the still-UNKNOWN G1 F-rows and marked $nf as found=true in $VERD (input hits in $CAND, same ids). The model is a filter, not evidence. For EVERY found=true hit: open the source it names (exe address via Tools/scripts/chase/chase09_native.py-style capstone disassembly of E:/Games/Batman - Arkham Knight/Binaries/Win64/BatmanAK.exe READ ONLY, or the file+offset), and decide CONFIRMED (the instruction/text really sets that member's default to that literal, and the code is an initialiser of the owning class or a subclass - say how you know the class) or REJECTED (why). Also sample 20 random found=false hits and report any the model missed. Read GRAB_BACKLOG.md section 0.5 (R4 provenance). Do NOT edit FOOTAGE.md, chase files or GRAB_BACKLOG.md; write $P/Research/BatmobileGrab/chase/chase-verify.md (per row: value, provenance class, evidence) and append a MODLOG.md entry 'chase-verify - done' with counts. Never launch or patch a game, never write into D:/Games or E:/Games, never commit, no secrets. FINAL: write $P/tmp/freebuff/reports/chase-verify.md with STATUS, confirmed/rejected/missed counts, per-row results, model precision on this run.
EOF
    log "judging complete ($nv verdicts, $nf found) -> queued 060-chase-verify"
  fi
  sleep 60
done
