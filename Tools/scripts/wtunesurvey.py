"""wtunesurvey.py - comparison table of weapon tunings across .ee files.

For each given weapon .ee (resolved through a .tab index like tabextract.py),
prints one line per WeaponTuning instance: weapon-block kinds (M/G/B/F),
velocity, max_range, fire_rate, magazine, AI damage triple, missile
turning_speed (homing indicator), bullet tracer velocity, AI target
priorities, plus any ForcePulseSettings explosion tunings (.ftunec) packed
in the same .ee.

Reuses tabextract.read_tab, eetoc.unaaf/sarc_dir, adfdump.parse_adf/dec,
rbmhdr.hash_jenkins. Read-only w.r.t. inputs; prints to stdout.

Usage:
  python wtunesurvey.py <file.tab> <vfs/path1> [vfs/path2 ...]
  python wtunesurvey.py --gamedir <game install> <vfs/path1> [...]
VFS paths use forward slashes; --gamedir searches every game+patch tab.
"""
from __future__ import annotations

import argparse
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eetoc  # noqa: E402
from tabextract import read_tab  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402
from adfdump import parse_adf, dec  # noqa: E402


def arc_for(tab_path: str) -> str:
    return os.path.splitext(tab_path)[0] + ".arc"


def get_ee(tab_entries: dict, arc_path: str, vfs: str) -> bytes:
    h = hash_jenkins(vfs.replace("\\", "/").encode("ascii"))
    if h not in tab_entries:
        raise SystemExit(f"hash {h:08X} ({vfs}) not in tab")
    off, size = tab_entries[h]
    with open(arc_path, "rb") as f:
        f.seek(off)
        data = f.read(size)
    if len(data) != size:
        raise SystemExit(f"short read on {vfs}")
    return data


def scan_gamedir(game_dir: str):
    """Map archive hash -> (arc path, offset, size) over base + patch tabs.

    Patch entries take precedence (the game's VFS resolves loose patch files
    over base content). Returns (base, patch) dicts. Whole-.ee patch
    overrides are reported by callers; loose inner-file overrides (e.g. a
    patched .epe inside a base .ee) are NOT visible here -- check those with
    tabextract + rtpcdump against the patch tabs.
    """
    import glob
    base, patch = {}, {}
    for tab_path in sorted(glob.glob(os.path.join(game_dir, "archives_win64", "game*.tab"))):
        arc = arc_for(tab_path)
        for h, (off, size) in read_tab(tab_path).items():
            base.setdefault(h, (arc, off, size))
    for tab_path in sorted(glob.glob(os.path.join(game_dir, "patch_win64", "game*.tab"))):
        arc = arc_for(tab_path)
        for h, (off, size) in read_tab(tab_path).items():
            patch[h] = (arc, off, size)
    return base, patch


def root_val(t: str, name: str, typ: str = "float") -> str:
    m = re.findall(rf"(?<![\w]){name}={typ}=([^;,}}]+)", t)
    return m[0] if m else "?"


def summarize_weapon(label: str, t: str) -> str:
    blocks = []
    for bn in ("missile", "grenade", "bullet", "fow"):
        m = re.search(bn + r"_weapon=A\[\w+\]\[(\d+)\]", t)
        if m and m.group(1) != "0":
            blocks.append(bn[0].upper())
    ai = t.split("ai_tuning=")[-1] if "ai_tuning=" in t else t
    m = re.search(r"base_tuning=WeaponTuningBase\{impulse=float=[^;]+;"
                  r"vehicle_damage_factor=float=([^;]+);vehicle_impulse_factor=float=[^;]+;"
                  r"object_damage_factor=float=([^;]+);object_impulse_factor=float=[^;]+;"
                  r"damage=float=([^;]+)", ai)
    dmg = m.groups() if m else ("?", "?", "?")
    turn = re.findall(r"missile_turning_speed=float=([^;]+)", ai)
    trac = re.findall(r"tracer_fire_velocity=float=([^;]+)", ai)
    pri = {k: (re.findall(k + r"=float=([^;]+)", ai) or ["?"])[0]
           for k in ("air_vehicle_target_priority", "land_vehicle_target_priority",
                     "sea_vehicle_target_priority", "character_target_priority")}
    return (f"{label:12s} blk={''.join(blocks) or '-':4s} "
            f"vel={root_val(t, 'velocity'):>10s} rng={root_val(t, 'max_range'):>8s} "
            f"fr={root_val(t, 'fire_rate'):>7s} mag={root_val(t, 'magazine_size', 'int32'):>4s} "
            f"aiDmg={dmg[2]:>8s} vehDmg={dmg[0]:>8s} objDmg={dmg[1]:>8s} "
            f"turn={turn} tracer={trac} "
            f"priA/L/S/C={pri['air_vehicle_target_priority']}/{pri['land_vehicle_target_priority']}/"
            f"{pri['sea_vehicle_target_priority']}/{pri['character_target_priority']}")


def summarize_explosion(fname: str, t: str) -> str:
    pd = root_val(t, "PlayerDamage", "uint32")
    pr = root_val(t, "PlayerDamageRadius")
    ad = root_val(t, "AIDamage", "uint32")
    ar = root_val(t, "AIDamageRadius")
    return f"   blast {fname}: player {pd}/{pr}m  ai {ad}/{ar}m"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="tab file followed by VFS paths, "
                    "or just VFS paths with --gamedir")
    ap.add_argument("--gamedir", default=None,
                    help="game install dir: auto-locate each VFS across "
                         "archives_win64/patch_win64 tabs (patch wins). "
                         "Replaces the tab argument.")
    a = ap.parse_args()
    if a.gamedir:
        tab_path, vfs_list = None, a.paths
    else:
        if not a.paths:
            raise SystemExit("need tab file + VFS paths, or --gamedir + VFS paths")
        tab_path, vfs_list = a.paths[0], a.paths[1:]
    if not vfs_list:
        raise SystemExit("need at least one VFS path")
    patch_map: dict = {}
    base_map: dict = {}
    if a.gamedir:
        base_map, patch_map = scan_gamedir(a.gamedir)

        def locate(vfs: str):
            h = hash_jenkins(vfs.replace("\\", "/").encode("ascii"))
            if h in patch_map:
                arc, off, size = patch_map[h]
                return arc, off, size, True
            if h in base_map:
                arc, off, size = base_map[h]
                return arc, off, size, False
            raise SystemExit(f"hash {h:08X} ({vfs}) not found under {a.gamedir}")
    else:
        entries = read_tab(tab_path)
        arc = arc_for(tab_path)

        def locate(vfs: str):
            h = hash_jenkins(vfs.replace("\\", "/").encode("ascii"))
            if h not in entries:
                raise SystemExit(f"hash {h:08X} ({vfs}) not in tab")
            off, size = entries[h]
            return arc, off, size, False

    for vfs in vfs_list:
        label = vfs.split("/")[-1].rsplit(".", 1)[0][:12]
        try:
            arc, off, size, patched = locate(vfs)
            with open(arc, "rb") as f:
                f.seek(off)
                raw = f.read(size)
            if len(raw) != size:
                raise SystemExit(f"short read on {vfs}")
            sarc = eetoc.unaaf(raw)
        except SystemExit as ex:
            print(f"{label:12s} ERROR {ex}")
            continue
        if patched:
            print(f"{label:12s} NOTE whole .ee overridden in patch ({arc})")
        for name, oo, ss in eetoc.sarc_dir(sarc):
            if not oo or not name.endswith(".wtunec"):
                continue
            short = name.split("/")[-1]
            if short.startswith(("autoaim", "default_", "attach")):
                continue
            try:
                tds, sh, insts = parse_adf(sarc[oo:oo + ss])
            except Exception as ex:  # noqa: BLE001 - one bad file must not kill the survey
                print(f"{label:12s} {short}: PARSE-FAIL {ex}")
                continue
            for iname, th, oo2, sz2 in insts:
                # Offsets inside are absolute to the ADF file: slice instance
                # bytes but keep ioff at the instance's file offset, so array
                # / string targets resolve. (Slicing + ioff=0 misdecodes every
                # array into plausible-looking garbage while fixed-offset
                # members stay correct.)
                adf = sarc[oo:oo + ss]
                inst = adf[oo2:oo2 + sz2]
                t = dec(inst, tds, sh, oo2, th, 0, None, iname)
                if "WeaponTuning{" in t:
                    print(summarize_weapon(label, t))
        for name, oo, ss in eetoc.sarc_dir(sarc):
            if not oo or not name.endswith(".ftunec"):
                continue
            try:
                tds, sh, insts = parse_adf(sarc[oo:oo + ss])
            except Exception as ex:  # noqa: BLE001
                print(f"{label:12s} {name.split('/')[-1]}: PARSE-FAIL {ex}")
                continue
            for iname, th, oo2, sz2 in insts:
                adf = sarc[oo:oo + ss]
                inst = adf[oo2:oo2 + sz2]
                t = dec(inst, tds, sh, oo2, th, 0, None, iname)
                if "ForcePulseSettings{" in t:
                    print(summarize_explosion(name.split("/")[-1], t))


if __name__ == "__main__":
    main()
