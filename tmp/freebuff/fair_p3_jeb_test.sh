#!/bin/bash
# Phase 3 - Jeb test split, shared choice arm at the frozen variant + Jeb's native arm.
# Jeb :8081 must be up.  The variant was frozen in phase 2, before any test cell ran.
cd E:/Modding/JC3-Batmobile || exit 1
P="python Tools/scripts/chase/fair_judge.py"
V=$(cat E:/Modding/_gamedata/BmAKgrab/chase/fair/FROZEN_VARIANT.txt)
echo "PHASE3_START $(date +%H:%M:%S) variant=$V"
bash tmp/freebuff/srv.sh stop-qwen
bash tmp/freebuff/srv.sh jeb || exit 1
bash tmp/freebuff/srv.sh status
$P --run --model jeb --arm choice --split test --variant "$V" | tail -4
echo "JEB_CHOICE_DONE $(date +%H:%M:%S)"
$P --run --model jeb --arm native-jeb --split test | tail -4
echo "PHASE3_DONE $(date +%H:%M:%S)"
