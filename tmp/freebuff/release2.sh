#!/bin/bash
# Releases T-15 and T-19 (low/) once T-11 is done in the tracker.
B=E:/Modding/JC3-Batmobile/tmp/freebuff; BL=E:/Modding/JC3-Batmobile/GRAB_BACKLOG.md
until grep -qE "^\| T-11 \| done" $BL; do sleep 60; done
mv $B/low/300-t-15.txt $B/low/310-t-19.txt $B/queue/ && echo "$(date -Is) release: T-15, T-19 queued (T-11 done)" >> $B/keeper.log
