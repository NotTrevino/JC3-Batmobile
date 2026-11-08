#!/bin/bash
# Phase 3b - Jeb test arms only.  Assumes Jeb :8081 is already up and alone in VRAM.
cd E:/Modding/JC3-Batmobile || exit 1
P="python Tools/scripts/chase/fair_judge.py"
V=$(cat E:/Modding/_gamedata/BmAKgrab/chase/fair/FROZEN_VARIANT.txt)
echo "PHASE3B_START $(date +%H:%M:%S) variant=$V"
bash tmp/freebuff/srv.sh status
$P --run --model jeb --arm choice --split test --variant "$V" | tail -4
echo "JEB_CHOICE_DONE $(date +%H:%M:%S)"
$P --run --model jeb --arm native-jeb --split test | tail -4
echo "PHASE3B_DONE $(date +%H:%M:%S)"
