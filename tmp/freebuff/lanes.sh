#!/bin/bash
# Read-only lane view: reads the driver's screen snapshots (screen-L*.txt, rewritten every 15 s) and logs.
# It never types into a session, so looking can never start or renew one.
B=E:/Modding/JC3-Batmobile/tmp/freebuff
now=$(date +%s)
for k in 1 2 3; do
  s=$B/screen-L$k.txt; [ -f $s ] || continue
  age=$(( now - $(stat -c %Y $s) ))
  w=$(grep -oE 'working\.\.\. +([0-9]+h )?([0-9]+m )?[0-9]+s' $s | tail -1 | sed 's/working\.\.\. */working /')
  task=$(ls $B/running 2>/dev/null | grep "^L${k}__" | sed "s/^L${k}__//")
  pid=$(cat $B/driver-L$k.pid 2>/dev/null)
  alive=$( [ -n "$pid" ] && tasklist //FI "PID eq $pid" 2>/dev/null | grep -q node && echo up || echo down )
  st=$(grep -E ' (WORK|IDLE) ' $B/driver-L$k.log 2>/dev/null | tail -1 | cut -c12-19,24-)
  printf 'L%s driver %-4s | %-18s | task %-30s | snapshot %ss old%s\n' $k "$alive" "${w:-not working}" "${task:--}" $age "${st:+ | last: $st}"
done
printf 'queue %s  filler %s  running %s  | local judge: %s\n' "$(ls $B/queue | wc -l)" "$(ls $B/filler | wc -l)" "$(ls $B/running | wc -l)" \
  "$(curl -s --max-time 2 localhost:8080/health | grep -q ok && echo "up, $(grep -c . E:/Modding/_BmAKgrab/chase/verdicts.jsonl 2>/dev/null || echo 0) verdicts" || echo off)"
