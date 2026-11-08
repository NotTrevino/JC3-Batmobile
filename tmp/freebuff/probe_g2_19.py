"""G2-19 probe: where can a seated driver pose come from?

1. ASCII strings out of Rico's state-machine files (`*_base.afsmb` / `.asb`), looking for
   vehicle / seat / drive states and clip names.
2. The same for the `gen_male.bsk` skeleton.
3. The donor's `.epe` object list (already decoded by G2-18) for anything pose-like.
Read-only; writes nothing.
"""
import json
import re
import sys

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import jc3grab  # noqa: E402
import jc3index  # noqa: E402

ROWS = jc3index.load_index(jc3index.DEFAULT_OUT)
GAME = jc3index.DEFAULT_GAME
FILES = [
    "animations/jc_statemachine/main_characters/rico/rico_base.afsmb",
    "animations/jc_statemachine/main_characters/rico/rico_base.asb",
    "animations/jc_statemachine/main_characters/rico/rico_partial_global.afsmb",
    "animations/jc_skeletons/characters/gen_male.bsk",
    "animations/jc_statemachine/aero/wingsuit/wingsuit_base.afsmb",
]
KEYS = ("vehi", "seat", "sit", "driv", "car", "tank", "bike", "boat", "heli", "enter", "exit", "stunt")


def strings(blob, n=6):
    return re.findall(rb"[\x20-\x7e]{%d,}" % n, blob)


for path in FILES:
    hit = [r for r in ROWS if r["path"] == path]
    if not hit:
        print(f"{path}: NOT IN INDEX")
        continue
    blob = jc3grab.read_entry(hit[0], GAME)
    ss = [s.decode("latin-1") for s in strings(blob)]
    print(f"\n== {path}  {len(blob):,} B, {len(ss)} strings >=6")
    for k in KEYS:
        hs = [s for s in ss if k in s.lower()]
        print(f"   ~{k}: {len(hs)} {hs[:6]}")
    print("   first 12:", ss[:12])
