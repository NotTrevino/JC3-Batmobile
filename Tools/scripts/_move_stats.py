"""Donor movement-stat map: decode every Serpente stat module ConvertAdf can read
and tabulate the movement members (name, file offset, value) that a handling
retune would edit. Sits next to vmodcdiff.py (which finds mod-authored deltas);
this one inventories the tunable surface itself.

BmAK target numbers are UNKNOWN (no Arkham tuning source on hand; pretrained
memory is not evidence). When they arrive, this table's (file, offset, type)
triples are exactly what an applier script needs.
Usage: python _move_stats.py [aaf-dir] [--all]
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

MOVE_WORDS = ("speed", "rpm", "torque", "gear", "brake", "tire", "tyre",
              "grip", "steer", "suspens", "nitro", "accel", "mass", "drag",
              "clutch", "transmission", "throttle", "downforce", "drift",
              "boost", "punch", "kph", "mph", "radius", "width", "engine",
              "differential", "final_drive", "redline")


def members(xml_path):
    x = open(xml_path, encoding="utf-8-sig").read()
    i = x.find("<instances")
    rows = []
    for m in re.finditer(
            r"<member name=\"([^\"]+)\"[^>]*?(?:offset-in-file=\"([0-9A-Fa-f]+)\"[^>]*?)?"
            r"type=\"(int32|uint32|float|int8|string)\"[^>]*>([^<]*)</member>",
            x[i:] if i >= 0 else x):
        rows.append((m.group(1), m.group(3), m.group(2) or "?",
                     m.group(4).strip()[:40]))
    return rows


def main():
    root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else \
        os.path.join("Builds", "test-003", "aaf")
    show_all = "--all" in sys.argv
    mods = sorted(glob.glob(os.path.join(root, "**", "*.vmodc"), recursive=True))
    print("== %d .vmodc modules under %s" % (len(mods), root))
    crashed, decoded = [], 0
    with tempfile.TemporaryDirectory() as td:
        for vm in mods:
            rel = os.path.relpath(vm, root).replace(os.sep, "/")
            out = os.path.join(td, "x.xml")
            r = subprocess.run(
                ["Tools/Gibbed/Gibbed.JustCause3.ConvertAdf.exe",
                 "--e", vm, out], capture_output=True)
            if r.returncode != 0:
                crashed.append(rel)
                continue
            decoded += 1
            rows = members(out)
            move = [x for x in rows if any(w in x[0].lower() for w in MOVE_WORDS)]
            rest = len(rows) - len(move)
            print("-- %s (%d B): %d members, %d movement" %
                  (rel.split("/")[-1], os.path.getsize(vm), len(rows), len(move)))
            for name, typ, off, val in (rows if show_all else move):
                mark = "" if any(w in name.lower() for w in MOVE_WORDS) else "  (other)"
                print("     @%s %-34s %-7s %s%s" % (off, name, typ, val, mark))
            if not show_all and rest:
                print("     ... +%d non-movement members (--all to list)" % rest)
    print("decoded %d, ConvertAdf crashed on %d: %s" %
          (decoded, len(crashed), crashed))


main()
