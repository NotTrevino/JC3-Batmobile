#!/bin/bash
# Phase 2 - Qwen tuning (both variants), freeze the shared variant, then the Qwen test arms.
# Qwen :8080 must be up and Jeb :8081 stopped (one model in VRAM at a time).
cd E:/Modding/JustCause3/JC3-Batmobile || exit 1
P="python Tools/scripts/chase/fair_judge.py"
echo "PHASE2_START $(date +%H:%M:%S)"
bash tmp/freebuff/srv.sh stop-jeb
bash tmp/freebuff/srv.sh qwen || exit 1
bash tmp/freebuff/srv.sh status
$P --run --model qwen --arm choice --split tune --variant neutral  --order 0 | tail -4
echo "NEUTRAL_DONE $(date +%H:%M:%S)"
$P --run --model qwen --arm choice --split tune --variant explicit --order 0 | tail -4
echo "EXPLICIT_DONE $(date +%H:%M:%S)"
V=$(python -c "import sys; sys.path.insert(0,'Tools/scripts/chase'); import fair_judge as f; print(f.tuned_variant()[0])")
echo "FROZEN_VARIANT=$V $(date +%H:%M:%S)"
echo "$V" > E:/Modding/_shared/gamedata/BmAKgrab/chase/fair/FROZEN_VARIANT.txt
$P --run --model qwen --arm choice --split test --variant "$V" | tail -4
echo "QWEN_CHOICE_DONE $(date +%H:%M:%S)"
$P --run --model qwen --arm native-qwen --split test | tail -4
echo "PHASE2_DONE $(date +%H:%M:%S)"
