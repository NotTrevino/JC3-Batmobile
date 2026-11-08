#!/bin/bash
# Phase 1 - Jeb tuning on the tuning split only (Jeb :8081 must be up).
# One order (0) is enough for tuning; the 3-order repeat requirement is for the test split.
cd E:/Modding/JC3-Batmobile || exit 1
P="python Tools/scripts/chase/fair_judge.py"
echo "PHASE1_START $(date +%H:%M:%S)"
$P --run --model jeb --arm choice --split tune --variant neutral  --order 0 | tail -4
echo "NEUTRAL_DONE $(date +%H:%M:%S)"
$P --run --model jeb --arm choice --split tune --variant explicit --order 0 | tail -4
echo "PHASE1_DONE $(date +%H:%M:%S)"
