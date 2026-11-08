#!/bin/bash
# Serialised runner for the fair Jeb vs Qwen test: one model at a time, absolute paths,
# resumable (fair_judge.py skips a cell whose JSON already exists).
# Tuning uses order 0 only (the 3-order repeat requirement applies to the test split).
PY=python
F="E:/Modding/JC3-Batmobile/Tools/scripts/chase/fair_judge.py"
run() { "$PY" "$F" "$@"; }
echo "START $(date +%H:%M:%S)"

echo "== tune: jeb neutral";   run --run --model jeb  --arm choice --split tune --variant neutral  --order 0 | tail -1
echo "== tune: qwen neutral";  run --run --model qwen --arm choice --split tune --variant neutral  --order 0 | tail -1
echo "== tune: jeb explicit";  run --run --model jeb  --arm choice --split tune --variant explicit --order 0 | tail -1
echo "== tune: qwen explicit"; run --run --model qwen --arm choice --split tune --variant explicit --order 0 | tail -1
echo "TUNING_DONE $(date +%H:%M:%S)"

V=$("$PY" -c "import sys; sys.path.insert(0,'E:/Modding/JC3-Batmobile/Tools/scripts/chase'); import fair_judge as f; print(f.tuned_variant()[0])")
echo "FROZEN_VARIANT=$V $(date +%H:%M:%S)"

echo "== jeb test: choice";  run --run --model jeb  --arm choice --split test --variant "$V" | tail -1
echo "JEB_CHOICE_DONE $(date +%H:%M:%S)"
echo "== qwen test: choice"; run --run --model qwen --arm choice --split test --variant "$V" | tail -1
echo "QWEN_CHOICE_DONE $(date +%H:%M:%S)"
echo "== jeb test: native";  run --run --model jeb  --arm native-jeb  --split test | tail -1
echo "JEB_NATIVE_DONE $(date +%H:%M:%S)"
echo "== qwen test: native"; run --run --model qwen --arm native-qwen --split test | tail -1
echo "QWEN_NATIVE_DONE $(date +%H:%M:%S)"

run --score
run --report
echo "ALL_DONE $(date +%H:%M:%S)"
