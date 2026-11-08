"""probe for G2-28: dump the raw facts the card needs before damage_predict.py exists.

Read-only. Prints, per weapon class id:
  * the tune file it reads and its mount
  * every member whose name mentions damage/bullet/pellet/shot/armour/heavy
  * the .ftunec blast tunes carried in the same container (explosion weapons)
and, per health module, the four armour channel pairs.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import jc3index  # noqa: E402
import jc3weapons as W  # noqa: E402

INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
WANT = [
    "editor/entities/jc_weapons/01_one_handed/w011_pistol_u_pozhar_98/w011_pistol_u_pozhar_98.wtunec",
    "editor/entities/jc_weapons/02_two_handed/w111_assault_rifle_up_39/w111_assault_rifle_up_39.wtunec",
    "editor/entities/jc_weapons/02_two_handed/w131_machine_gun_urga_vdova_89/w131_machine_gun_urga_vdova_89.wtunec",
    "editor/entities/jc_weapons/02_two_handed/w151_shotgun_u_rys_96/w151_shotgun_u_rys_96.wtunec",
    "editor/entities/jc_weapons/02_two_handed/w141_rpg_uvk_13/w141_rpg_uvk_13.wtunec",
    "editor/entities/jc_weapons/03_thrown/w301_grenade/w301_grenade.wtunec",
]
KEYS = ("damage", "armor", "armour", "heavy", "pellet", "bullet", "shot", "spread", "rate")


def main() -> int:
    rows = [json.loads(line) for line in open(INDEX, encoding="utf-8") if line.strip()]
    best = W.best_by_path(rows)
    for path in WANT:
        r = best.get(path)
        print("=" * 78)
        print(path, "->", (r or {}).get("mount"))
        if not r:
            continue
        blob = W.read_row(r, jc3index.DEFAULT_GAME)
        try:
            stream, entries = W.unpack(blob)
            inner = blob
        except BaseException as ex:  # noqa: BLE001
            print("  (not a container:", ex, ")")
            inner, entries = blob, []
        dec = W.decode_tune(inner)
        for inst in dec["instances"]:
            print(f"  instance {inst['name']} ({inst['class']}, {len(inst['rows'])} rows)")
            for p, t, v in inst["rows"]:
                if any(k in p.lower() for k in KEYS):
                    print(f"    {p:70} {t:12} {v!r}")
        print("  inner files:")
        for name, off, size in entries:
            print("    ", name, size)
        for name, off, size in entries:
            if not name.endswith(".ftunec"):
                continue
            print("  blast", name)
            try:
                bdec = W.decode_tune(stream[off:off + size])
            except Exception as ex:  # noqa: BLE001
                print("    DECODE-FAIL", ex)
                continue
            for inst in bdec["instances"]:
                for p, t, v in inst["rows"]:
                    if "damage" in p.lower() or "radius" in p.lower():
                        print(f"    {p:60} {v!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
