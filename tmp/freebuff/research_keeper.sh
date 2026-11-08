#!/bin/bash
# research_keeper.sh - research-reset replacement for keeper.sh (2026-11-03).
# Never queues B/V/Q cards (keeper.sh does). Never wastes a session slot: whenever fewer than 3 freebuff.exe run on
# this machine (all projects share the 3-session cap) and a JC3 lane is down while queue/ or filler/ hold work, it
# starts the driver (lanes already running exit 2). Backs off until the 05:05 UTC daily reset when the driver reports
# no free hours / the wallet guard. Logs to research_keeper.log; prints LOW-FILLER when filler/ < 4 so the operator
# restocks with research fillers.
B=E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff
DRV=C:/Users/User/.claude/skills/freebuff/scripts/driver.cjs
LOG=$B/research_keeper.log
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> $LOG; }
alive() { [ -n "$1" ] && tasklist //FI "PID eq $1" 2>/dev/null | grep -q node; }
log "START research_keeper pid $$"
echo $$ > $B/research_keeper.pid
last_start=0
while true; do
  q=$(ls $B/queue 2>/dev/null | wc -l); f=$(ls $B/filler 2>/dev/null | wc -l)
  # 2026-11-03: restock automatically (the operator may be unavailable - rate limits idled two sessions)
  if [ "$f" -lt 6 ]; then
    log "LOW-FILLER filler=$f queue=$q -> research_restock.py"
    python $B/research_restock.py 8 >> $LOG 2>&1
    f=$(ls $B/filler 2>/dev/null | wc -l)
  fi
  if [ $((q + f)) -eq 0 ]; then log "NO WORK queue+filler empty"; sleep 60; continue; fi
  # hours exhausted? (driver lines since the last 05:00Z reset)
  today=$(date -u +%Y-%m-%d); hr=$(date -u +%H)
  since=$today"T05:00"; [ "$hr" -lt 5 ] && since=$(date -u -d yesterday +%Y-%m-%d)"T05:00"
  if cat $B/driver-L1.log $B/driver-L2.log $B/driver-L3.log 2>/dev/null | awk -v s="$since" '$1 >= s' | grep -qE "no free hours|WALLET GUARD|exit 7"; then
    log "NO HOURS since $since -> sleeping until 05:05Z"
    now=$(date -u +%s); nxt=$(date -u -d "$(date -u -d tomorrow +%Y-%m-%d)T05:05:00Z" +%s)
    [ "$hr" -lt 5 ] && nxt=$(date -u -d "${today}T05:05:00Z" +%s)
    sleep $(( nxt - now )); continue
  fi
  # sessions = freebuff.exe started by a driver (node.exe parent); a freebuff.exe child of freebuff.exe is a helper
  cli=$(powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='freebuff.exe'\" | Where-Object { (Get-CimInstance Win32_Process -Filter \"ProcessId=\$(\$_.ParentProcessId)\").Name -eq 'node.exe' }).Count" 2>/dev/null | tr -d '\r')
  [ -z "$cli" ] && cli=3
  down=0; for k in 1 2 3; do alive "$(cat $B/driver-L$k.pid 2>/dev/null)" || down=$((down + 1)); done
  now=$(date +%s)
  if [ "$cli" -lt 3 ] && [ "$down" -gt 0 ] && [ $((now - last_start)) -gt 150 ]; then
    log "SLOT FREE (freebuff.exe=$cli, lanes down=$down, queue=$q filler=$f) -> starting driver"
    node $DRV --project E:/Modding/JustCause3/JC3-Batmobile --parallel 3 --model "DeepSeek V4.1 Flash 10/17" >> $B/research_keeper.out 2>&1
    last_start=$(date +%s)
  fi
  sleep 30
done
