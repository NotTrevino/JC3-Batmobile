"""vhealth.py - armor/health summary per vehicle .ee for durability work.

For each given vehicle archive: unpacks the SARC directory (via eetoc),
finds *health*.vmodc modules, decodes the VehicleDamage instance (via
adfdump) and prints max_health, the four armor gate pairs, destroy/smoke
thresholds, plus the weapon .wtunec / blast .ftunec files packed alongside
and weapon-ish references from the entity .epe files.

Shares tabextract.read_tab, wtunesurvey.scan_gamedir, eetoc, adfdump and
rbmhdr helpers with the other readers. Read-only w.r.t. inputs.

Usage:
  python vhealth.py <file.tab> <vehicle-ee-vfs> [...]
  python vhealth.py --gamedir <game install> <vehicle-ee-vfs> [...]
VFS paths use forward slashes.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eetoc  # noqa: E402
from tabextract import read_tab  # noqa: E402
from wtunesurvey import scan_gamedir, arc_for  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402
from adfdump import parse_adf, dec  # noqa: E402


def one_val(t: str, name: str, typ: str = "int32") -> str:
    m = re.findall(rf"(?<![\w]){name}={typ}=([^;,}}]+)", t)
    return m[0] if m else "?"


def health_line(t: str) -> str:
    f = lambda n: one_val(t, n, "float")  # noqa: E731
    return (f"HP={one_val(t, 'max_health')} "
            f"blt={one_val(t, 'bullet_armor')}@{f('bullet_armor_strength')} "
            f"hvBl={one_val(t, 'bullet_heavy_armor')}@{f('bullet_heavy_armor_strength')} "
            f"exp={one_val(t, 'explosion_armor')}@{f('explosion_armor_strength')} "
            f"imp={one_val(t, 'impact_armor')}@{f('impact_armor_strength')} "
            f"thrExp={one_val(t, 'explosion_threshold')} "
            f"smoke={one_val(t, 'smoke_threshold', 'uint16')} "
            f"burn={one_val(t, 'burn_threshold', 'uint16')} "
            f"burnDur={one_val(t, 'burn_duration_s', 'uint16')}s "
            f"expDelay={one_val(t, 'explosion_delay_s', 'uint16')}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="tab file followed by VFS paths, "
                    "or just VFS paths with --gamedir")
    ap.add_argument("--gamedir", default=None)
    a = ap.parse_args()
    if a.gamedir:
        tab_path, vfs_list = None, a.paths
    else:
        if not a.paths:
            raise SystemExit("need tab file + VFS paths, or --gamedir + VFS paths")
        tab_path, vfs_list = a.paths[0], a.paths[1:]
    if not vfs_list:
        raise SystemExit("need at least one vehicle .ee VFS path")

    base_map: dict = {}
    patch_map: dict = {}
    if tab_path is None:
        base_map, patch_map = scan_gamedir(a.gamedir)

    def locate(vfs: str):
        h = hash_jenkins(vfs.replace("\\", "/").encode("ascii"))
        if tab_path is not None:
            entries = read_tab(tab_path)
            if h not in entries:
                raise SystemExit(f"hash {h:08X} ({vfs}) not in tab")
            off, size = entries[h]
            return arc_for(tab_path), off, size, False
        if h in patch_map:
            arc, off, size = patch_map[h]
            return arc, off, size, True
        if h in base_map:
            arc, off, size = base_map[h]
            return arc, off, size, False
        raise SystemExit(f"hash {h:08X} ({vfs}) not found")

    for vfs in vfs_list:
        label = vfs.split("/")[-2][:34]
        try:
            arc, off, size, patched = locate(vfs)
            with open(arc, "rb") as f:
                f.seek(off)
                raw = f.read(size)
            if len(raw) != size:
                raise SystemExit(f"short read on {vfs}")
            sarc = eetoc.unaaf(raw)
        except SystemExit as ex:
            print(f"== {label} ERROR {ex}")
            continue
        if patched:
            print(f"== {label} NOTE whole .ee overridden in patch")
        found_health = False
        for name, oo, ss in eetoc.sarc_dir(sarc):
            if not oo or "health" not in name or not name.endswith(".vmodc"):
                continue
            try:
                tds, sh, insts = parse_adf(sarc[oo:oo + ss])
            except Exception as ex:  # noqa: BLE001
                print(f"== {label} health {name.split('/')[-1]}: PARSE-FAIL {ex}")
                continue
            for iname, th, oo2, sz2 in insts:
                adf = sarc[oo:oo + ss]
                t = dec(adf[oo2:oo2 + sz2], tds, sh, oo2, th, 0, None, iname)
                if "VehicleDamage{" in t:
                    print(f"== {label} {health_line(t)} [{name.split('/')[-1]}]")
                    found_health = True
        if not found_health:
            print(f"== {label} (no VehicleDamage module)")
        guns = sorted({n.split("/")[-1] for n, oo, ss in eetoc.sarc_dir(sarc)
                       if oo and n.endswith(".wtunec") and "autoaim" not in n})
        blasts = sorted({n.split("/")[-1] for n, oo, ss in eetoc.sarc_dir(sarc)
                         if oo and n.endswith(".ftunec")})
        refs: set[str] = set()
        for n, oo, ss in eetoc.sarc_dir(sarc):
            if oo and n.endswith(".epe"):
                b = sarc[oo:oo + ss]
                pat = rb"w\d{3}_[a-z0-9_]+|autoaim_[a-z_]+|[a-z0-9_/.-]*\.wtune"
                refs.update(m.group(0).decode("ascii", "replace")
                            for m in re.finditer(pat, b))
        if guns:
            print(f"   guns: {', '.join(guns)}")
        if blasts:
            print(f"   blasts: {', '.join(blasts)}")
        if refs:
            print(f"   epe refs: {sorted(refs)[:12]}")


if __name__ == "__main__":
    main()
