"""chase2_09_scan.py - second-pass search for the chase-09 rows (F-65, F-66, F-68 … F-72).

Routes the first pass did NOT finish: a byte scan of **every** shipped package (CookedPCConsole,
DLC and patch layers, `.upk` and `.u`) and of **every** ini under the install for the member names,
then a store-site attribution pass in the executable for the two native fields.

Read-only: every file is opened `rb` and never written. Game data written by this tool goes to
`E:/Modding/_shared/gamedata/BmAKgrab` only.

Usage
  python Tools/scripts/chase/chase2_09_scan.py --names            # every package, every member name
  python Tools/scripts/chase/chase2_09_scan.py --inis             # every ini, every member name
  python Tools/scripts/chase/chase2_09_scan.py --stores 0x6dc     # exe store sites + the window
  python Tools/scripts/chase/chase2_09_scan.py --all              # all three, JSON to _BmAKgrab
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chase09_native as native  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight"
OUT = r"E:\Modding\_shared\gamedata\BmAKgrab\chase2_09_packages.json"
NAMES = ["StayUprightStiffness", "StayUprightDamping", "StayUprightRollResistAngle",
         "StayUprightPitchResistAngle", "AirControl", "BattleModeYawOffset",
         "ArmourModeDamageReduction", "BattleModeThrottleSpeed", "BattleModeSteerBiasRate"]


def packages() -> list[str]:
    out = []
    for base, _dirs, files in os.walk(GAME):
        for f in files:
            if f.lower().endswith((".upk", ".u")):
                out.append(os.path.join(base, f))
    return sorted(out)


def scan_names(files: list[str]) -> dict:
    pats = {n: n.encode() for n in NAMES}
    hits: dict[str, list[dict]] = {n: [] for n in NAMES}
    for i, path in enumerate(files, 1):
        try:
            data = open(path, "rb").read()
        except OSError:
            continue
        for name, pat in pats.items():
            start = 0
            while True:
                at = data.find(pat, start)
                if at < 0:
                    break
                start = at + 1
                tail = data[at + len(pat):at + len(pat) + 48]
                kind = ""
                for k in (b"FloatProperty", b"IntProperty", b"BoolProperty",
                          b"StructProperty", b"ByteProperty"):
                    if k in tail:
                        kind = k.decode()
                        break
                hits[name].append({"package": os.path.relpath(path, GAME).replace(os.sep, "/"),
                                   "offset": at, "type_after_name": kind,
                                   "bytes16": data[max(0, at - 8):at + 24].hex()})
                if len(hits[name]) > 400:
                    break
        if i % 250 == 0:
            print(f"  … {i}/{len(files)} packages", file=sys.stderr, flush=True)
    return hits


def inis() -> list[str]:
    return sorted(glob.glob(os.path.join(GAME, "**", "*.ini"), recursive=True))


def scan_inis(files: list[str]) -> dict:
    hits: dict[str, list[dict]] = {n: [] for n in NAMES}
    for path in files:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for n in NAMES:
            if n in text:
                line = next((i for i, l in enumerate(text.splitlines(), 1) if n in l), 0)
                hits[n].append({"ini": os.path.relpath(path, GAME).replace(os.sep, "/"),
                                "line": line})
    return hits


def stores(disp: int, after: int = 40) -> dict:
    """Every store site at `disp` plus its disassembled window and the constants it loads."""
    exe = open(native.EXE, "rb").read()
    image_base, secs = native.sections(exe)
    hits = native.find_stores(exe, disp, limit=400)
    out = []
    for h in hits:
        base = native.window_start(exe, h["off"])
        rows = native.disasm(exe, secs, image_base, base, min(len(exe), h["off"] + 0x400))
        keep, past = [], 0
        for r in rows:
            keep.append(r)
            if r["off"] is not None and r["off"] > h["off"]:
                past += 1
                if past >= after:
                    break
        text = []
        for i, r in enumerate(keep):
            note = ""
            if "[rip +" in r["op_str"] and i + 1 < len(keep):
                tgt = keep[i + 1]["addr"] + int(r["op_str"].split("[rip + ")[1].split("]")[0], 16)
                toff = native.va_to_off(secs, image_base, tgt)
                if toff is not None and toff + 4 <= len(exe):
                    f = struct.unpack("<f", exe[toff:toff + 4])[0]
                    note = f"   ; [0x{tgt:x}] = float {f!r}"
            text.append(f"{'>> ' if r['off'] == h['off'] else '   '}0x{r['addr']:x}  "
                        f"{r['mnemonic']:<8} {r['op_str']}{note}")
        out.append({"va": f"0x{native.off_to_va(secs, image_base, h['off']):x}",
                    "store": h["what"], "snippet": "\n".join(text)})
    return {"offset": hex(disp), "sites": len(hits), "hits": out}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", action="store_true")
    ap.add_argument("--inis", action="store_true")
    ap.add_argument("--stores")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    rec: dict = {"tool": "chase2_09_scan.py", "game": GAME}
    if a.names or a.all:
        files = packages()
        print(f"scanning {len(files)} packages", file=sys.stderr)
        rec["packages"] = scan_names(files)
        rec["package_count"] = len(files)
    if a.inis or a.all:
        fs = inis()
        rec["inis"] = scan_inis(fs)
        rec["ini_count"] = len(fs)
    if a.stores or a.all:
        rec["stores"] = {o: stores(int(o, 16)) for o in
                         ([a.stores] if a.stores else ["0x6dc", "0x6e0"])}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {OUT}")
    for name, hits in (rec.get("packages") or {}).items():
        pkgs = sorted({h["package"] for h in hits})
        print(f"  {name:32} {len(hits):3} name hits in {len(pkgs)} package(s): "
              f"{', '.join(pkgs[:6])}{' …' if len(pkgs) > 6 else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
