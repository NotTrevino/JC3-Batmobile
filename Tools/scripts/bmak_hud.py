"""Grab the two legacy HUD movies (Scaleform GFx) out of the cooked packages.

**This is not the HUD inventory.** `TARGETS` is the hand-written two-movie list that the first
pass mistook for the HUD; the game runs 25 `RHudModule*` classes and 19 HUD movies. Use
`bmak_hud_inventory.py` (roster from the engine, 19 movies, every `UC_*` setter) as the authority;
this script is kept only so its size/hash check of the original two carves keeps passing.

The original Batmobile grab only opened `Playable_Batmobile_SF.upk`, which carries geometry,
materials and audio but **no HUD**. The HUD is elsewhere:

    BmGame.upk   HudModuleBatmobile.Image   SwfMovie   423,056 B   the Batmobile HUD module
    Startup.upk  StoryModeHUD.HUD           SwfMovie    23,752 B   the shared prompt/menu HUD

Both are **sub-packages** inside one cooked file (`HudModuleBatmobile`, `StoryModeHUD`), which is
why `ls CookedPCConsole | grep -i hud` finds nothing: there is no `HudModuleBatmobile.upk`.

Each SwfMovie's `RawData` array holds a `CFX` container: a u32 length, the `CFX` magic, a
header, then a zlib stream of GFx tags. `umodel` cannot address the dotted object path
(`HudModuleBatmobile.Image`), so this script carves the array itself and proves the result:
the zlib stream must inflate and the movie must contain the identifiers we expect.

Usage:
    python Tools/scripts/bmak_hud.py build          # carve + report -> HUD.json
    python Tools/scripts/bmak_hud.py check          # re-read the game, compare size/hash
    python Tools/scripts/bmak_hud.py report         # print what was found

The movies stay outside the repository (game content). Only sizes, hashes and identifier
counts are written to `Research/BatmobileGrab/HUD.json`.
"""
import argparse
import hashlib
import json
import os
import sys
import zlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upk_read import Package  # noqa: E402

GAME = Path(os.environ.get("BMAK_GAME", r"E:/Games/Batman - Arkham Knight"))
OUT = Path(os.environ.get("BMAK_HUD_OUT", r"E:/Modding/_gamedata/BmAKgrab_early/hud"))
HERE = Path(__file__).resolve().parents[2]
TABLE = HERE / "Research" / "BatmobileGrab" / "HUD.json"

# (package, object path, short name, identifiers that must appear in the inflated movie)
TARGETS = [
    ("BmGame.upk", "HudModuleBatmobile.Image", "HudModuleBatmobile",
     ("BattleMode_top", "BATTLETODRIVE", "BoostGauge", "EnergySystem", "WinchMeter", "CannonCoolDown")),
    ("Startup.upk", "StoryModeHUD.HUD", "HUD",
     ("CI_UI_A", "CI_UI_B", "HUD_I1", "ShowHUD")),
]


def carve(package: str, path: str) -> tuple[bytes, bytes]:
    """Return (CFX payload, inflated tag stream) for one SwfMovie export."""
    pkg = Package(str(GAME / "BmGame" / "CookedPCConsole" / package))
    idx = next((k for k in range(1, pkg.export_count + 1) if pkg.object_path(k) == path), None)
    if idx is None:
        raise SystemExit(f"{package}: no export {path!r}")
    rec = pkg.exports[idx - 1]
    blob = pkg.image[rec["offset"]: rec["offset"] + rec["size"]]
    at = blob.find(b"CFX")
    if at < 4:
        raise SystemExit(f"{package}:{path}: no CFX payload in {rec['size']} B")
    n = int.from_bytes(blob[at - 4:at], "little")
    if not 0 < n <= len(blob) - at:
        raise SystemExit(f"{package}:{path}: length prefix {n} does not fit")
    payload = blob[at:at + n]
    for off in range(0, 32):
        try:
            data = zlib.decompressobj().decompress(payload[off:])
        except zlib.error:
            continue
        if len(data) > 1024:
            return payload, data
    raise SystemExit(f"{package}:{path}: CFX payload does not inflate")


def census(data: bytes) -> dict:
    text = data.decode("latin-1")
    ids = set()
    word = []
    for ch in text:
        if ch.isalnum() or ch == "_":
            word.append(ch)
        elif word:
            ids.add("".join(word))
            word = []
    if word:
        ids.add("".join(word))
    return {
        "identifiers": len(ids),
        "CI_": sum(1 for x in ids if x.startswith("CI_")),
        "names": {k: sorted(x for x in ids if k.lower() in x.lower())[:8]
                  for k in ("BattleMode", "BoostGauge", "EnergySystem", "WinchMeter", "HUD_I", "CI_UI")},
    }


def build() -> dict:
    rows = []
    OUT.mkdir(parents=True, exist_ok=True)
    for package, path, short, required in TARGETS:
        payload, data = carve(package, path)
        missing = [r for r in required if r.encode() not in data]
        if missing:
            raise SystemExit(f"{package}:{path}: expected identifiers missing: {missing}")
        swf = OUT / f"{short}.gfx"
        raw = OUT / f"{short}.swf"
        swf.write_bytes(payload)
        raw.write_bytes(data)
        rows.append({
            "object": f"{package}:{path}", "file": str(swf), "bytes": len(payload),
            "inflated_bytes": len(data),
            "sha256": hashlib.sha256(payload).hexdigest(),
            **census(data),
        })
    table = {"source": str(GAME), "movies": rows}
    TABLE.write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
    return table


def check() -> None:
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    bad = 0
    for row in table["movies"]:
        package, path = row["object"].split(":", 1)
        payload, data = carve(package, path)
        got = hashlib.sha256(payload).hexdigest()
        ok = got == row["sha256"] and len(payload) == row["bytes"] and len(data) == row["inflated_bytes"]
        print(f"{'PASS' if ok else 'FAIL'} {row['object']}: {len(payload)} B, sha256 {got[:12]}")
        bad += not ok
    print(f"{'PASS' if not bad else 'FAIL'}: {len(table['movies'])} HUD movies")
    raise SystemExit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "check", "report"))
    a = ap.parse_args()
    if a.cmd == "build":
        for row in build()["movies"]:
            print(f"{row['object']}: {row['bytes']} B -> {row['inflated_bytes']} B, "
                  f"{row['identifiers']} identifiers, {row['CI_']} input prompts")
    elif a.cmd == "check":
        check()
    else:
        table = json.loads(TABLE.read_text(encoding="utf-8"))
        for row in table["movies"]:
            print(row["object"], row["bytes"], "B", row["sha256"][:16])
            for k, v in row["names"].items():
                if v:
                    print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
