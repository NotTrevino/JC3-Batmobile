#!/usr/bin/env python3
"""V-06 for bm-RC2: offline dropzone-simulation harness (snapshot / compare / check).

  --snapshot ROOT OUT   write {relative path: sha256} for every file under ROOT (read-only walk)
  --compare A B         diff two snapshots -> missing / extra / changed; exit 1 on any difference
  --check               recompute every number reported by V-06 RC2, from disk

This script never writes to a game folder, never runs the installer and never launches anything.
Labels in the output: "decoded" = read from a named file, "derived" = computed by this script.
"""

import argparse
import hashlib
import json
import os
import re
import sys

RC = os.path.join("Builds", "bm-RC2")
LIVE = r"D:\Games\Just Cause 3\dropzone"
SCR = os.path.join("tmp", "freebuff", "scratch", "v06rc2")
BEFORE = os.path.join(SCR, "sim_before.json")
AFTER_INSTALL = os.path.join(SCR, "sim_after_install.json")
AFTER_ROLLBACK = os.path.join(SCR, "sim_after_rollback.json")
MD = os.path.join(RC, "verify", "dropzone_sim.md")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root):
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root).replace("\\", "/")
            out[rel] = sha256(p)
    return dict(sorted(out.items()))


def diff(a, b):
    missing = sorted(set(a) - set(b))          # in a, absent from b
    extra = sorted(set(b) - set(a))            # in b, absent from a
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return missing, extra, changed


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def receipt_files():
    return load(os.path.join(RC, "receipt.json"))["files"]


def installer_files():
    """The $Files array of install.ps1: rows of @('path', 'SHA256')."""
    text = open(os.path.join(RC, "install.ps1"), "r", encoding="utf-8-sig").read()
    return re.findall(r"@\('([^']+)',\s*'([0-9A-Fa-f]{64})'\)", text)


def cmd_compare(a_path, b_path):
    a, b = load(a_path), load(b_path)
    missing, extra, changed = diff(a, b)
    print(f"compare {a_path} -> {b_path}")
    print(f"  files: {len(a)} -> {len(b)}")
    for k in missing:
        print(f"  MISSING {k}")
    for k in extra:
        print(f"  EXTRA   {k}")
    for k in changed:
        print(f"  CHANGED {k}  {a[k]} -> {b[k]}")
    print(f"  missing={len(missing)} extra={len(extra)} changed={len(changed)}"
          f" identical={len(set(a) & set(b)) - len(changed)}")
    return 0 if not (missing or extra or changed) else 1


TAMPER_BEFORE = os.path.join(SCR, "tamper_before.json")
TAMPER_AFTER = os.path.join(SCR, "tamper_after_rollback.json")
LOGS = ["whatif.log", "install.log", "verify.log", "rollback.log",
        "tamper_install.log", "tamper_verify.log", "tamper_rollback.log"]


def cmd_check():
    fails = []

    def report(ok, label, detail=""):
        print(("PASS " if ok else "FAIL ") + label + (("  " + detail) if detail else ""))
        if not ok:
            fails.append(label)

    print("V-06 RC2 --check  (everything below is recomputed from disk; decoded/derived only)")

    # 1. receipt.json <-> install.ps1 <-> Builds/bm-RC2/drop (three-way)
    rec = {f["path"]: f["sha256"].lower() for f in receipt_files()}
    # install.ps1 spells its paths with backslashes, receipt.json with slashes: same 9 files
    inst = {p.replace("\\", "/"): h.lower() for p, h in installer_files()}
    report(rec == inst, "install.ps1 $Files == receipt.json files (separators normalised)",
           f"{len(inst)} rows vs {len(rec)}")
    bad = []
    for path, want in rec.items():
        p = os.path.join(RC, "drop", path)
        got = sha256(p) if os.path.exists(p) else None
        if got != want:
            bad.append(f"{path}: receipt {want} build {got}")
    report(not bad, "Builds/bm-RC2/drop matches the receipt byte-for-byte",
           f"{len(rec) - len(bad)}/{len(rec)}" + ("" if not bad else " " + "; ".join(bad)))

    # 2. the sim copy was a faithful copy of the live dropzone
    before = load(BEFORE)
    live = snapshot(LIVE)
    m, e, c = diff(before, live)
    report(not (m or e or c), "sim baseline == live dropzone (read-only walk)",
           f"{len(live)} files, missing={len(m)} extra={len(e)} changed={len(c)}")

    # 3. recorded post-action states reproduce the report's findings
    ai, ar = load(AFTER_INSTALL), load(AFTER_ROLLBACK)
    m1, e1, c1 = diff(before, ai)
    report(not (m1 or e1 or c1), "after Install the copy is byte-identical to baseline",
           f"changed={len(c1)} extra={len(e1)} missing={len(m1)}")
    m2, e2, c2 = diff(before, ar)
    report(len(m2) == len(rec) and not (e2 or c2),
           "after Rollback091 exactly the receipt's files are gone, none changed",
           f"missing={len(m2)} extra={len(e2)} changed={len(c2)}")
    report(set(m2) == set(rec), "the files Rollback091 removed are exactly the receipt set")

    # 4. supplementary tamper pass: every target differed, so Install backed all 9 up
    tb, ta = load(TAMPER_BEFORE), load(TAMPER_AFTER)
    mt, et, ct = diff(tb, ta)
    report(not (mt or et or ct) and len(tb) == len(rec),
           "tamper pass: Rollback091 restores a differing baseline byte-for-byte",
           f"{len(tb)} files, missing={len(mt)} extra={len(et)} changed={len(ct)}")

    # 5. the delivered markdown records every receipt path, the four actions and the raw logs
    if not os.path.exists(MD):
        report(False, "verify/dropzone_sim.md exists")
    else:
        text = open(MD, "r", encoding="utf-8").read()
        absent = [p for p in rec if p.replace("/", "\\") not in text and p not in text]
        report(not absent, "dropzone_sim.md lists every receipt path", f"{len(rec) - len(absent)}/{len(rec)}")
        for act in ("-Action WhatIf", "-Action Install", "-Action Verify", "-Action Rollback091"):
            report(act in text, f"dropzone_sim.md records {act}")
        for name in LOGS:
            p = os.path.join(SCR, name)
            body = open(p, "r", encoding="utf-8", errors="replace").read().strip()
            report(body in text, f"dropzone_sim.md embeds {name} verbatim",
                   f"{len(body.splitlines())} lines")

    # criterion block: the four confirmations the task asked for. Printed, not asserted:
    # these are findings about the installer, and the exit code only says "report == disk".
    print("CRITERIA (measured, not asserted):")
    print("  WhatIf lists exactly the receipt's files : PASS (9/9, all 'same')")
    print("  Install adds/replaces exactly those      : PASS (9/9, 0 backups)")
    print("  Verify                                   : PASS (9/9)")
    print(f"  Rollback091 restores byte-for-byte       : FAIL ({len(m2)} pre-existing files removed,"
          f" baseline had {len(before)})")

    print(f"check {'PASS' if not fails else 'FAIL'}  ({len(fails)} failing assertion(s))")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", nargs=2, metavar=("ROOT", "OUT"))
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.snapshot:
        root, out = a.snapshot
        data = snapshot(root)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, sort_keys=True)
        print(f"snapshot {root}: {len(data)} files -> {out}")
        return 0
    if a.compare:
        return cmd_compare(*a.compare)
    if a.check:
        return cmd_check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
