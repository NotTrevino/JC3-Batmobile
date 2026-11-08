#!/bin/bash
# lane1-guard.sh - one-off (2026-11-04). Lane 1 (driver pid 6876, OLD code) is in a renewed Fast session ending ~19:26:52Z.
# The old driver sends the LONGEST queued task in the last 20 min and may send up to ~1 min after the real deadline (stale
# timer); a send after the deadline opens a NEW paid session (that is how the 18:26Z renewal happened). This script only moves
# task files, never touches a process:
#   phase B (19:05:00Z): move EST >= 45 out of queue/  -> the old "longest first" can only pick short (EST 30) tasks
#   phase C (19:23:50Z): move EVERYTHING out of queue/ and filler/ -> nothing can be sent into the deadline
#   restore: when the driver exits (or at 19:34Z at the latest) every moved file goes back to queue/ (filler/ for fillers)
B=/e/Modding/JustCause3/JC3-Batmobile/tmp/freebuff
H=$B/low/lane1-hold
PID=6876
LOG=$B/lane1-guard.log
mkdir -p $H/queue $H/filler
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> $LOG; }
at() { case "$1" in ??:??) t="$1:00";; *) t="$1";; esac; date -u -d "2026-11-04T${t}Z" +%s; }
alive() { tasklist //FI "PID eq $PID" 2>/dev/null | grep -q node; }
wait_until() { while [ "$(date -u +%s)" -lt "$1" ]; do alive || return 1; sleep 3; done; return 0; }
restore() {
  for f in $H/queue/*.txt; do [ -e "$f" ] || continue; [ -e "$B/queue/$(basename $f)" ] || mv "$f" "$B/queue/" 2>/dev/null; done
  for f in $H/filler/*.txt; do [ -e "$f" ] || continue; mv "$f" "$B/filler/" 2>/dev/null; done
  log "RESTORED: queue=$(ls $B/queue | wc -l) filler=$(ls $B/filler | wc -l) held-left=$(ls $H/queue $H/filler 2>/dev/null | grep -c txt)"
}
trap restore EXIT
log "START guard pid $$ (watching driver $PID)"
wait_until $(at 19:05) || { log "driver gone before phase B"; exit 0; }
n=0; for f in $B/queue/*.txt; do e=$(grep -m1 '^EST:' "$f" | tr -dc '0-9'); if [ "${e:-0}" -ge 45 ]; then mv "$f" $H/queue/ 2>/dev/null && n=$((n+1)); fi; done
log "PHASE B: held $n tasks with EST>=45; queue now $(ls $B/queue | wc -l)"
wait_until $(at 19:23:50) || { log "driver gone before phase C"; exit 0; }
# phase C: empty claimable work, and keep it empty (poll) until the driver exits or the cap
while alive && [ "$(date -u +%s)" -lt "$(at 19:34)" ]; do
  for f in $B/queue/*.txt; do [ -e "$f" ] && mv "$f" $H/queue/ 2>/dev/null && log "C: held queue/$(basename $f)"; done
  for f in $B/filler/*.txt; do [ -e "$f" ] && mv "$f" $H/filler/ 2>/dev/null && log "C: held filler/$(basename $f)"; done
  sleep 4
done
log "driver exited or cap reached"
