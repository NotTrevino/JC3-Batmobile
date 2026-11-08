"""Prove the Immobiliser's launcher pointers and the payload on the archetype they name.

Run before the payload edit (baseline: the pointers pass, the payload fails) and again after it
(all eight assertions must pass). Read-only: opens the cooked packages with `upk_read.py`, never
launches, injects or writes a package.

    python Tools/scripts/wp4_emp_payload_check.py [--reverse]

Exit 0 = every assertion passed; 1 = at least one failed (the failing ones are printed as FAIL).
`--reverse` adds the incoming-reference count (slow: walks every export of the main package).
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from upk_read import Package, export_summary  # noqa: E402

LAUNCHER = "Batmobile_EMP_Missile_Launcher"
FIRED = "Batmobile_EMPMissile_Projectile_ForCars"
ORPHAN = "Batmobile_EMPMissile_Projectile"
IMPACT = "Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact"
DMG_TYPE = "Core.RDmgType_BatmobileCannon"
PACKAGES = ("Playable_Batmobile_SF.upk", "Playable_BatmobileMK2_SF.upk",
            "Playable_BatmobileFunhouse_SF.upk")
OUT = os.path.join("Working", "Weapons", "emp_payload_check.json")


def root() -> str:
    hits = glob.glob("E:/Games/*/BmGame/CookedPCConsole/BmGame.upk")
    if not hits:
        raise SystemExit("no BmAG install found at E:/Games/*/BmGame/CookedPCConsole")
    return os.path.dirname(hits[0])


def by_offset(tags: list[dict]) -> dict[int, dict]:
    return {t["offset"]: t for t in tags}


def ref_of(tag: dict | None) -> str:
    return (tag or {}).get("ref") or ""


def main() -> int:
    rev = "--reverse" in sys.argv
    base = root()
    print("root", base)
    rows, fails = [], []

    def want(label: str, ok: bool, got) -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}: {got}")
        rows.append({"assertion": label, "ok": bool(ok), "got": got})
        if not ok:
            fails.append(label)

    pkgs = {}
    for fn in PACKAGES:
        path = os.path.join(base, fn)
        if not os.path.exists(path):
            want(f"{fn} present", False, "MISSING")
            continue
        pkg = Package(path)
        pkgs[fn] = pkg
        li, fi = pkg.find(LAUNCHER), pkg.find(FIRED)
        oi = pkg.find(ORPHAN)
        print(f"\n{fn}  exports={pkg.export_count}  launcher={li} fired={fi} orphan={oi}")
        if not li or not fi:
            want(f"{fn} archetypes found", False, f"launcher={li} fired={fi}")
            continue
        ls = export_summary(pkg, li)
        fs = export_summary(pkg, fi)
        lt, ft = by_offset(ls["tags"]), by_offset(fs["tags"])
        want(f"{fn} launcher @2428 -> {FIRED}", ref_of(lt.get(2428)).endswith(FIRED),
             ref_of(lt.get(2428)) or "(none)")
        want(f"{fn} launcher @2492 -> {FIRED}", ref_of(lt.get(2492)).endswith(FIRED),
             ref_of(lt.get(2492)) or "(none)")
        want(f"{fn} fired @728 Damage == 60.0", ft.get(728, {}).get("value") == 60.0,
             ft.get(728, {}).get("value", "absent"))
        want(f"{fn} fired @732 DamageRadius == 0.0", ft.get(732, {}).get("value") == 0.0,
             ft.get(732, {}).get("value", "absent"))
        want(f"{fn} fired @712 MyDamageType == {DMG_TYPE}", ref_of(ft.get(712)).endswith(DMG_TYPE),
             ref_of(ft.get(712)) or "(none)")
        want(f"{fn} fired @968 impact sound == Immobiliser", ref_of(ft.get(968)).endswith(IMPACT),
             ref_of(ft.get(968)) or "(none)")
        print(f"  fired tags={fs['tag_count']} size={fs['size']}  launcher tags={ls['tag_count']}"
              f"  @2464 bInstantFire={lt.get(2464, {}).get('value', 'absent')}"
              f"  @2452 rotator={lt.get(2452, {}).get('value', 'absent')}")
        rows.append({"package": fn, "launcher_tags": ls["tag_count"],
                     "fired_tags": fs["tag_count"], "fired_size": fs["size"],
                     "bInstantFire": lt.get(2464, {}).get("value", "absent")})

        if rev and fn == PACKAGES[0] and oi:
            t0 = time.time()
            hits = {1: 0, oi: 0, fi: 0}
            for i in range(1, pkg.export_count + 1):
                try:
                    s = export_summary(pkg, i)
                except Exception:
                    continue
                for t in s["tags"]:
                    r = t.get("ref") or ""
                    for target, name in ((1, None), (oi, ORPHAN), (fi, FIRED)):
                        if name and r.endswith("." + name):
                            hits[target] += 1
            print(f"  reverse refs (walked {pkg.export_count} exports in {time.time()-t0:.1f}s): "
                  f"{ORPHAN}={hits[oi]}  {FIRED}={hits[fi]}")
            want(f"orphan {ORPHAN} still has 0 incoming refs", hits[oi] == 0, hits[oi])
            rows.append({"reverse_refs": {ORPHAN: hits[oi], FIRED: hits[fi]}})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"root": base, "assertions": rows, "failed": fails},
              open(OUT, "w", encoding="utf-8"), indent=1)
    print(f"\nwrote {OUT}")
    print("CHECK", "PASS" if not fails else f"FAIL ({len(fails)}): " + "; ".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
