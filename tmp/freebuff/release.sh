#!/bin/bash
# Releases gated work: G2X once G2-20 and G2-27 are done; T cards once G2X is done (per the tracker).
B=E:/Modding/JC3-Batmobile/tmp/freebuff; BL=E:/Modding/JC3-Batmobile/GRAB_BACKLOG.md
log(){ echo "$(date -Is) release: $*" >> $B/keeper.log; }
done_row(){ grep -qE "^\| $1 \| done" $BL; }
put(){ # move task file $1 (basename) into queue from wherever it is; drop its stale report
  for d in done low; do [ -f $B/$d/$1 ] && mv $B/$d/$1 $B/queue/$1; done; rm -f $B/reports/$2.md; log "queued $1"
  if grep -q "queue drained" <(grep -v release: $B/keeper.log | tail -1); then powershell.exe -NoProfile -Command "Start-Process -WindowStyle Hidden -FilePath 'C:/Program Files/Git/bin/bash.exe' -ArgumentList '$B/keeper.sh'"; log "keeper restarted"; fi; }
stage=0
while true; do
  if [ $stage -eq 0 ] && done_row G2-20 && done_row G2-27; then
    rm -f $B/queue/2*-t-*.txt.tmp; for f in $B/queue/200-t-10.txt; do [ -f $f ] && mv $f $B/low/; done
    put 190-g2x.txt G2X; stage=1; fi
  if [ $stage -eq 1 ] && done_row G2X; then
    for f in $(ls $B/low $B/done 2>/dev/null | grep -E '^2[0-9]0-t-[0-9]+\.txt$' | sort -u); do id=$(echo $f | sed -E 's/^[0-9]+-t-/T-/; s/\.txt$//'); done_row $id || put $f $id; done
    log "T cards released"; exit 0; fi
  # keep T cards parked while gated (the keeper may requeue deferred ones)
  for f in $B/queue/2*-t-*.txt; do [ -f "$f" ] && mv "$f" $B/low/; done
  [ $stage -eq 0 ] && [ -f $B/queue/190-g2x.txt ] && mv $B/queue/190-g2x.txt $B/low/
  sleep 60
done
