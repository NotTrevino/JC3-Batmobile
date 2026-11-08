#!/bin/bash
# Keeps 3 Freebuff lanes on the JC3 queue until it is empty or the daily hours run out.
# Deferred tasks (deps not done yet) are parked in low/ and re-queued automatically once their deps are done:
#   NEEDS: <dep>[,<dep>...]   optional task header; a dep is a tracker id (GRAB_BACKLOG.md §12 row '| ID | done'),
#                             a task name in done/ (e.g. 030-chase-candidates) or an absolute file path that exists
#                             and does not say 'STATUS: deferred'.
# A deferred task without NEEDS is re-queued once any other task has finished since it was parked.
P=E:/Modding/JC3-Batmobile; B=$P/tmp/freebuff; DRV=C:/Users/User/.claude/skills/freebuff/scripts/driver.cjs
log(){ echo "$(date -Is) $*" >> $B/keeper.log; }
dep_ok(){ local d=$1
  if [[ $d == */* ]]; then [ -f "$d" ] && ! grep -q "STATUS: deferred" "$d"; return; fi
  ls $B/done/"$d".txt >/dev/null 2>&1 && return 0
  grep -qE "^\| $d \| (done|skipped)" $P/GRAB_BACKLOG.md; }  # skipped (e.g. B-12 by D-2) counts as met, 2026-10-31
needs_ok(){ local n; n=$(grep -m1 '^NEEDS:' "$1" | sed 's/^NEEDS:\s*//; s/,/ /g'); [ -n "$n" ] || return 2
  for d in $n; do dep_ok "$d" || return 1; done; return 0; }
log "keeper start pid $$"
SINCE=$(date -u -d "$(date -u +%F) 05:00" +%FT%TZ)   # today's reset; earlier "no hours" lines are stale
while true; do
  # 1) A deferred report parks its task in low/ (stamped with the time, to compare with later DONEs).
  for r in $B/reports/*.md; do [ -f "$r" ] || continue
    grep -q "STATUS: deferred" "$r" || continue
    id=$(basename $r .md); t=$(ls $B/done | grep -i -- "-$(echo $id|tr A-Z a-z).txt$" | head -1)
    [ -n "$t" ] || continue
    mv "$B/done/$t" "$B/low/$t"; touch "$B/low/$t"; mv "$r" "$r.deferred.$(date +%s)"; log "parked $id (deferred) -> low/$t"; done
  # 2) Parked tasks go back to the queue once their deps are done.
  for t in $B/low/*.txt; do [ -f "$t" ] || continue
    needs_ok "$t"; rc=$?
    if [ $rc -eq 0 ]; then mv "$t" $B/queue/; log "requeue $(basename $t) (NEEDS met)"
    elif [ $rc -eq 2 ] && grep -q '^DONE:' "$t" && [ -n "$(find $B/done -name '*.txt' -newer "$t" | head -1)" ] \
         && [ -n "$(ls $B/reports/*.deferred.* 2>/dev/null | grep -i "$(basename $t .txt | sed 's/^[0-9]*-//')")" ]; then
      mv "$t" $B/queue/; log "requeue $(basename $t) (no NEEDS; a task finished since it was parked)"; fi; done
  # Out of daily hours: wait for the reset (05:00 UTC = midnight Central, observed 2026-10-29) and carry on.
  # Only "no free hours" lines newer than the last reset count, so old log lines never stop a fresh day.
  if grep -h "no free hours left" $B/driver-L*.log 2>/dev/null | awk -v s="$SINCE" '$1 > s' | grep -q .; then
    now=$(date -u +%s); r=$(date -u -d "$(date -u +%F) 05:05" +%s); [ $r -le $now ] && r=$((r + 86400))
    log "no hours left -> sleeping until reset $(date -u -d @$r +%FT%TZ)"; sleep $((r - now))
    SINCE=$(date -u +%FT%TZ); log "daily reset -> resuming"; continue; fi
  # 3) Ready cards go to the queue by themselves (2026-10-30: B-04/B-11 sat ready, unqueued, behind a grouped todo row).
  #    A B/V card is ready when it is not done, has no task anywhere, and every id in its 'deps:' is done; ranges like
  #    B-05…B-11 expand. Q/R cards are in-game work and never auto-queued (no game launch).
  grep -E '^#### [BV]-[0-9]+ ' $P/GRAB_BACKLOG.md | while read -r _ id rest; do
    grep -qE "^\| $id \| done" $P/GRAB_BACKLOG.md && continue
    s=$(echo $id | tr A-Z a-z); { compgen -G "$B/*/*[0-9]-card-$s.txt" || compgen -G "$B/*/*[0-9][0-9][0-9]-$s.txt"; } >/dev/null && continue
    deps=$(echo "$rest" | sed -n 's/.*deps: *\([^·]*\).*/\1/p' | sed 's/([^)]*)//g')
    ok=1; for d in $(echo "$deps" | tr ',' ' '); do
      if [[ $d =~ ^([A-Z0-9]+)-([0-9]+)…[A-Z0-9]*-?([0-9]+)$ ]]; then
        for ((i=10#${BASH_REMATCH[2]}; i<=10#${BASH_REMATCH[3]}; i++)); do dep_ok "$(printf '%s-%02d' ${BASH_REMATCH[1]} $i)" || ok=0; done
      else dep_ok "$d" || ok=0; fi; done
    [ $ok -eq 1 ] || continue
    sz=$(echo "$rest" | grep -oE ' (S|M|L|XL) · deps' | awk '{print $1}'); case $sz in S) e=45;; M) e=90;; *) e=120;; esac
    sed "s/__ID__/$id/g; s/__EST__/$e/" $B/card_tpl.txt > $B/queue/0-card-$s.txt
    log "auto-queued $id (deps done: $deps)"; done
  nq=$(ls $B/queue/*.txt $B/filler/*.txt 2>/dev/null | wc -l); nr=$(ls $B/running 2>/dev/null | wc -l)
  # Never stop: an empty queue now means "wait for a card to become ready" (restock.sh keeps the fillers up).
  if [ "$nq" -eq 0 ] && [ "$nr" -eq 0 ]; then sleep 120; continue; fi
  # One-off model trial: test-model.txt = picker name -> the next start is ONE lane on that model, then the file is gone.
  if [ "$nq" -gt 0 ] && [ -s $B/test-model.txt ] && [ "$(ls $B/running | wc -l)" -lt 3 ]; then
    m=$(cat $B/test-model.txt); rm -f $B/test-model.txt; log "trial lane on $m"
    node $DRV --project $P --parallel 1 --model "$m" >> $B/keeper.log 2>&1; sleep 120; continue; fi
  if [ "$nq" -gt 0 ]; then node $DRV --project $P --parallel 3 --model "$(cat $B/model.txt 2>/dev/null || echo auto)" >> $B/keeper.log 2>&1; fi
  sleep 120
done
