"""research_restock.py - keep tmp/freebuff/filler/ stocked with RESEARCH work, without the operator (2026-11-03).

Why: 2026-11-03 the operator's agent was rate-limited for ~1 h, the filler pool ran dry, two paid sessions idled
25-30 min each. This runs from research_keeper.sh whenever filler/ < MIN. Sources, in order (never build cards):
  1. a review for every G3 report in reports/ that has no reports/review-<id>.md yet
  2. one 'resolve UNKNOWN' task per numbered UNKNOWN in each G3 report (parsed from its UNKNOWNs section),
     skipped once a chase report for it exists
Each generated task carries the same no-guess rules as the hand-written ones. Idempotent: a task whose DONE file
exists, or that is already in filler/queue/running/done, is not generated again.
"""
from __future__ import annotations

import glob
import zlib
import os
import re
import sys

FB = "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff"
REP = FB + "/reports"
MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 6
RULES = (
    "PROJECT: E:/Modding/JustCause3/JC3-Batmobile (Just Cause 3 Batmobile mod), RESEARCH RESET: no building, no installing, no "
    "translation into game files. Read E:/Modding/JustCause3/JC3-Batmobile/RESET_FINDINGS.md and GRAB_BACKLOG.md section 6b. "
    "THE ONE RULE: never guess. Every value is labelled decoded (file + offset/line, or package + export + offset), "
    "derived (rule + inputs) or UNKNOWN (what you tried, where it would be). Never fill a gap from general knowledge of "
    "Batman: Arkham Knight, Unreal Engine 3 or Just Cause 3; a hypothesis only counts if proven against the bytes with "
    "an oracle. HARD RULES: read-only on everything except the files this task names as outputs; do NOT edit "
    "GRAB_BACKLOG.md, MODLOG.md, STATUS.md or any existing Research/Tools file; never launch, attach to or read the "
    "memory of any game; never write under E:/Games or D:/Games; never commit or push; no secrets. BmAK packages: "
    "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole (reader Tools/scripts/upk_read.py); BmSDK layouts: "
    "E:/Modding/_shared/tools/BmSDK-AK (MIT); JC3 data: E:/Modding/_shared/gamedata/JC3grab. Python: 'uv run --with numpy --with "
    "pillow --with pefile --with capstone python ...'. RESUME: if outputs or a partial report exist, continue. ")


def existing():
    names = set()
    for d in ("filler", "queue", "running", "done", "low"):
        for f in glob.glob(f"{FB}/{d}/**/*.txt", recursive=True):
            names.add(re.sub(r"^L\d__", "", os.path.basename(f)))
    return names


def write(name, done, est, body):
    with open(f"{FB}/filler/{name}", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"DONE: {done}\nONLY: freebuff\nEST: {est}\n{body}\n")


def unknowns(md):
    t = open(md, encoding="utf-8", errors="replace").read()
    m = re.search(r"^#+\s*UNKNOWNs?[^\n]*\n(.*?)(?=^#+\s|\Z)", t, re.S | re.M)
    if not m:
        return []
    items = re.findall(r"^\s*(?:\d+\.|\|\s*U-?\d+\s*\|)\s*(.+)$", m.group(1), re.M)
    return [re.sub(r"\s+", " ", i).strip()[:400] for i in items if len(i.strip()) > 20][:6]


def main():
    have, made = existing(), []
    count = lambda: len(glob.glob(f"{FB}/filler/*.txt"))
    reports = sorted(p for p in glob.glob(f"{REP}/G3-*.md"))
    # 1. reviews
    for r in reports:
        cid = os.path.basename(r)[:-3]
        name = f"4{zlib.crc32(cid.encode()) % 1000:03d}-review-{cid.lower()}.txt"
        done = f"{REP}/review-{cid}.md"
        if count() >= MIN:
            break
        if os.path.exists(done) or name in have:
            continue
        body = RULES + (f"TASK: independent review of finished research card {cid}. You did not write it; check it "
                        f"critically. Read its report {r}, the outputs it names (doc + .json + script). 1) Run the "
                        f"script's --check, record output verbatim. 2) Re-read 5 values labelled decoded from the raw "
                        f"source yourself - value, source, match yes/no. 3) Flag every decoded/derived label its "
                        f"evidence does not support, and every unlabelled claim. 4) Flag UNKNOWNs you can resolve from "
                        f"the bytes (say how). FINAL: write {done} with VERDICT (sound / minor issues / needs rework), "
                        f"Check output, Spot-checks (5), Issues, Resolvable UNKNOWNs.")
        write(name, done, 30, body); have.add(name); made.append(name)
    # 2. UNKNOWN chasers
    for r in reports:
        cid = os.path.basename(r)[:-3]
        for n, u in enumerate(unknowns(r), 1):
            if count() >= MIN:
                break
            name = f"5{zlib.crc32(cid.encode()) % 1000:03d}-chase-{cid.lower()}-u{n}.txt"
            done = f"{REP}/chase-{cid}-u{n}.md"
            if os.path.exists(done) or name in have:
                continue
            body = RULES + (f"TASK: resolve one UNKNOWN left by research card {cid}. Read its report {r} and the outputs "
                            f"it names first. The UNKNOWN (verbatim from the report): \"{u}\". Try to decode it from "
                            f"the bytes with an oracle. Write a NEW script Tools/scripts/chase_{cid.lower().replace('-', '_')}"
                            f"_u{n}.py (--write/--check) and its own output; do not modify the card's files. If it "
                            f"cannot be resolved from files, say exactly what blocks it and where it would be found "
                            f"(runtime, another package, the executable). FINAL: write {done} with STATUS "
                            f"resolved|partial|blocked, the evidence, commands + outputs verbatim.")
            write(name, done, 45, body); have.add(name); made.append(name)
    print(f"filler now {count()} (made {len(made)}): {made}")


if __name__ == "__main__":
    main()
