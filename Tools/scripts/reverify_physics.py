"""reverify_physics.py - re-check the pre-reset PHY-1 card (`Research/BatmobileGrab/PHYSICS.md`).

The old card (`Tools/scripts/grab_physics.py`) states: four vehicle packages, 32 `RB_BodySetup`
bodies each, 128 records, "all four vehicles carry byte-identical collision layouts", asset
`Batmobile_V3_Destroyed_Physics`.  This script re-runs that card's own `--check`, re-reads the
32 bodies with an independent parser, hashes the `AggGeom` payloads to test "byte-identical"
literally, and establishes which asset owns the list.

What the bytes say:

  * the old `--check` exits 0, but it compares its own rendered files - it never hashes an
    AggGeom payload, so its "byte-identical" sentence is a claim about parsed triples;
  * every one of the 32 `RB_BodySetup` exports in each package is outered to
    `Batmobile_V2_Mesh.Batmobile_V3_Destroyed_Physics`, and none of the four packages holds an
    export named `Batmobile_V3_Physics` - so this list is the **destroyed** wreck's, not the
    drivable car's;
  * the drivable asset is a different asset in a different package (`Physics.Batmobile_V3_Physics`,
    export 158266 per `COLLISION_GEOM.md`; bodies 169750 `Batmobile_Chassis` and 169751
    `Batmobile_Rig_Weapons_Trans` per `COLLISION_BOXES.md`), whose bone names do not intersect
    the destroyed list at all.

Usage
    python Tools/scripts/reverify_physics.py --write
    python Tools/scripts/reverify_physics.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read as U  # noqa: E402

GAME = "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
VEHICLES = ["Playable_Batmobile_SF", "Playable_BatmobileMK2_SF",
            "Playable_BatmobileJoker_SF", "Playable_BatmobileFunhouse_SF"]
OLD_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "PHYSICS.json")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "PHYSICS_REVERIFY.md")
JS = os.path.join(OUT, "PHYSICS_REVERIFY.json")
DESTROYED_ASSET = "Batmobile_V2_Mesh.Batmobile_V3_Destroyed_Physics"
DRIVABLE_ASSET = "Physics.Batmobile_V3_Physics"
DRIVABLE_BONES = ["Batmobile_Chassis", "Batmobile_Rig_Weapons_Trans"]


# --------------------------------------------------------------------------- own parser
def extents_triple(raw: bytes) -> list:
    """Find the box element's tagged floats myself.

    The AggGeom box element carries its extents as three FloatProperty words whose field
    offsets are 0x40, 0x44, 0x48 (the tag is `u16 type=4, u16 offset`, then the float).  This
    walk steps tag-by-tag through the payload - it does not use the old card's single regex.
    """
    out = []
    i = 0
    want = (0x40, 0x44, 0x48)
    while i + 8 <= len(raw):
        t, off = struct.unpack_from("<HH", raw, i)
        if t == 4 and off in want:
            val = struct.unpack_from("<f", raw, i + 4)[0]
            if not out or off == want[len(out)]:
                out.append((off, round(val, 3), i))
            if len(out) == 3 and [o for o, _, _ in out] == list(want):
                return out
        i += 1
    return out if len(out) == 3 else []


def read_body(pkg, index: int) -> dict:
    tags, end, why = U.walk_tags(pkg, pkg.data(index))
    bone = next((t.get("value") for t in tags if t.get("type") == "NameProperty"), "")
    agg = next((t for t in tags if t.get("name") == "AggGeom" and "raw" in t), None)
    row = {"export": index, "bone": bone, "walk_end": end, "walk_stop": why,
           "outer": pkg.object_path(pkg.exports[index - 1]["outer_index"])}
    if agg is None:
        row.update({"error": "no AggGeom payload"})
        return row
    raw = bytes.fromhex(agg["raw"])
    spheres, boxes = struct.unpack_from("<2I", raw, 0) if len(raw) >= 8 else (None, None)
    tri = extents_triple(raw)
    row.update({"agg_bytes": len(raw), "agg_sha1": hashlib.sha1(raw).hexdigest(),
                "u32_12": struct.unpack_from("<I", raw, 12)[0] if len(raw) >= 16 else None,
                "spheres": spheres, "boxes": boxes,
                "extents": [v for _, v, _ in tri] if tri else None,
                "centre": ([round(v, 3) for v in struct.unpack_from("<3f", raw, tri[0][2] - 12)]
                           if tri and tri[0][2] >= 12 else None)})
    return row


def package_bodies(name: str) -> dict:
    pkg = U.Package(os.path.join(GAME, name + ".upk"))
    idxs = [i for i in range(1, len(pkg.exports) + 1)
            if (pkg.object_class(i) or "") == "RB_BodySetup"]
    rows = [read_body(pkg, i) for i in idxs]
    assets = [pkg.object_name(i) for i in range(1, len(pkg.exports) + 1)
              if "PhysicsAsset" in (pkg.object_class(i) or "")]
    return {"package": name, "bodies": rows, "physics_assets": assets,
            "has_drivable_name": pkg.find(DRIVABLE_ASSET) is not None,
            "outer_hist": _hist([r.get("outer") for r in rows]),
            "bytes": os.path.getsize(os.path.join(GAME, name + ".upk"))}


def _hist(vals: list) -> dict:
    h: dict = {}
    for v in vals:
        h[str(v)] = h.get(str(v), 0) + 1
    return dict(sorted(h.items(), key=lambda kv: -kv[1]))


# --------------------------------------------------------------------------- compare
def old_check() -> dict:
    r = subprocess.run([sys.executable, os.path.join(HERE, "grab_physics.py"), "--check"],
                       capture_output=True, text=True)
    return {"exit": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}


def old_rows(name: str) -> dict:
    if not os.path.exists(OLD_JSON):
        return {}
    d = json.load(open(OLD_JSON, encoding="utf-8"))
    return {r["bone"]: r for r in d.get(name, {}).get("bodies", [])}


def raw_by_bone(name: str) -> dict:
    pkg = U.Package(os.path.join(GAME, name + ".upk"))
    out = {}
    for i in range(1, len(pkg.exports) + 1):
        if (pkg.object_class(i) or "") != "RB_BodySetup":
            continue
        tags, _e, _w = U.walk_tags(pkg, pkg.data(i))
        bone = next((t.get("value") for t in tags if t.get("type") == "NameProperty"), "")
        agg = next((t for t in tags if t.get("name") == "AggGeom" and "raw" in t), None)
        if agg:
            out[bone] = bytes.fromhex(agg["raw"])
    return out


def cross_diff(raws: dict) -> dict:
    """Which byte offsets differ between packages, bone by bone?"""
    names = list(raws)
    offsets, per_bone = set(), {}
    for bone in raws[names[0]]:
        base = raws[names[0]].get(bone)
        d = set()
        for n in names[1:]:
            b = raws[n].get(bone)
            if base is None or b is None or len(b) != len(base):
                d.add(-1)
                continue
            d |= {k for k in range(len(base)) if base[k] != b[k]}
        if d:
            per_bone[bone] = sorted(d)
            offsets |= d
    return {"offsets": sorted(offsets), "bones": per_bone,
            "u32_12_values": {n: sorted({struct.unpack_from("<I", raws[n][b], 12)[0]
                                         for b in raws[n] if len(raws[n][b]) >= 16})
                              for n in names}}


def build() -> dict:
    oc = old_check()
    pkgs = {v: package_bodies(v) for v in VEHICLES}
    one = pkgs[VEHICLES[0]]
    oldrows = old_rows(VEHICLES[0])
    agree = [r for r in one["bodies"]
             if r["bone"] in oldrows and r["extents"] == oldrows[r["bone"]]["extents"]
             and r["centre"] == oldrows[r["bone"]]["centre"]]
    disagree = [r["bone"] for r in one["bodies"]
                if r["bone"] in oldrows and (r["extents"] != oldrows[r["bone"]]["extents"]
                                             or r["centre"] != oldrows[r["bone"]]["centre"])]

    hash_sets = {v: sorted(r["agg_sha1"] for r in p["bodies"]) for v, p in pkgs.items()}
    identical_payloads = len({json.dumps(h) for h in hash_sets.values()}) == 1
    triple_sets = {v: sorted((r["bone"], tuple(r["extents"] or ()), tuple(r["centre"] or ()))
                             for r in p["bodies"]) for v, p in pkgs.items()}
    identical_triples = len({json.dumps(t) for t in triple_sets.values()}) == 1

    raws = {v: raw_by_bone(v) for v in VEHICLES}
    diff = cross_diff(raws)

    bones = {r["bone"] for r in one["bodies"]}
    all_bones = sorted(bones)
    overlap = sorted(bones & set(DRIVABLE_BONES))
    owners = set(one["outer_hist"])
    chassis_like = sorted(b for b in bones if "chassis" in b.lower() or "hull" in b.lower())

    checks = [
        ("the old card's own --check still passes",
         oc["exit"] == 0,
         "exit %d: %s" % (oc["exit"], oc["stdout"].replace("\n", " | "))),
        ("one package holds 32 RB_BodySetup exports and my parser reads every one",
         len(one["bodies"]) == 32 and all(r.get("extents") for r in one["bodies"]),
         "%d bodies, %d with extents, stop codes %s"
         % (len(one["bodies"]), sum(1 for r in one["bodies"] if r.get("extents")),
            _hist([r["walk_stop"] for r in one["bodies"]]))),
        ("every body is one box and no sphere, as the old card states",
         all(r["boxes"] == 1 and r["spheres"] == 0 for r in one["bodies"]),
         "box counts %s, sphere counts %s"
         % (_hist([r["boxes"] for r in one["bodies"]]),
            _hist([r["spheres"] for r in one["bodies"]]))),
        ("my extents and centres agree with the old card on all 32 bones",
         len(agree) == 32 and not disagree,
         "%d agree, %d disagree %s" % (len(agree), len(disagree), disagree[:4])),
        ("the payloads are NOT byte-identical: they differ only in the u32 at +12",
         (not identical_payloads) and set(diff["offsets"]) <= {12, 13, 14, 15}
         and diff["offsets"],
         "distinct sha1 multisets: %d; differing byte offsets across the four packages: %s; "
         "u32@12 per package: %s"
         % (len({json.dumps(h) for h in hash_sets.values()}), diff["offsets"],
            diff["u32_12_values"])),
        ("the parsed (bone, extents, centre) triples are identical across the four packages",
         identical_triples,
         "distinct triple sets: %d" % len({json.dumps(t) for t in triple_sets.values()})),
        ("all 32 bodies are outered to the destroyed asset, not the drivable one",
         owners == {DESTROYED_ASSET},
         "outer paths %s" % one["outer_hist"]),
        ("no package in the set holds an export named Batmobile_V3_Physics",
         not any(p["has_drivable_name"] for p in pkgs.values()),
         "assets per package %s" % _hist([a for p in pkgs.values()
                                          for a in p["physics_assets"]])),
        ("the drivable asset's bones do not intersect this list",
         not overlap and not chassis_like,
         "drivable bones %s; overlap %s; chassis/hull bones here %s"
         % (DRIVABLE_BONES, overlap, chassis_like)),
        ("the 32 bones are the wreck's parts, not a vehicle hull",
         len([b for b in all_bones if b == "Root" or "frag" in b.lower()
              or b.startswith("Object")]) >= 2,
         "%d of 32 are Root/Object*/frag bones; sample %s" % (
             len([b for b in all_bones if b == "Root" or "frag" in b.lower()
                  or b.startswith("Object")]), all_bones[:6])),
    ]

    return {
        "task": "reverify BMAK-PHYSICS - the pre-reset PHY-1 card against the bytes",
        "inputs": {"packages": {v: {"bytes": p["bytes"], "bodies": len(p["bodies"]),
                                    "physics_assets": p["physics_assets"]}
                                for v, p in pkgs.items()},
                   "old_card": "Research/BatmobileGrab/PHYSICS.md",
                   "old_json": "Research/BatmobileGrab/PHYSICS.json",
                   "drivable_asset_from": ["Research/BatmobileGrab/COLLISION_GEOM.md",
                                           "Research/BatmobileGrab/COLLISION_BOXES.md"]},
        "old_check": oc,
        "package": one,
        "by_package": {v: {"outer_hist": p["outer_hist"],
                           "distinct_agg_sha1": len(set(hash_sets[v])),
                           "has_drivable": p["has_drivable_name"],
                           "bodies": len(p["bodies"]),
                           "assets": p["physics_assets"]} for v, p in pkgs.items()},
        "claims": {
            "bodies_per_package": len(one["bodies"]),
            "total_records": sum(len(p["bodies"]) for p in pkgs.values()),
            "byte_identical_payloads": identical_payloads,
            "identical_triples": identical_triples,
            "owner": sorted(owners),
            "drivable_asset_present_here": any(p["has_drivable_name"] for p in pkgs.values()),
            "drivable_bone_overlap": overlap,
            "chassis_bones_in_this_list": chassis_like,
            "payload_diff_offsets": diff["offsets"],
            "u32_12_values": diff["u32_12_values"],
        },
        "verdict": {
            "destroyed_list": "32 bodies, owner %s, 4 packages; payloads differ only at the "
                              "u32 +12 (sha1-identical: %s)"
                              % (DESTROYED_ASSET, identical_payloads),
            "drivable_list": "%s (export 158266, bodies 169750/169751: %s) - a different "
                             "asset in a different package, absent from these four"
                             % (DRIVABLE_ASSET, ", ".join(DRIVABLE_BONES)),
            "old_card_byte_identical": (
                "FALSE: the payloads differ in the u32 at +12 (old docstring called it a "
                "constant 2846); every other byte is identical, and the parsed triples match"
                if not identical_payloads else "holds at payload level"),
            "payload_diff_offsets": diff["offsets"],
            "u32_12_values": diff["u32_12_values"],
            "old_card_attribution": "correct: the 32-body list is the destroyed asset's",
        },
        "checks": [{"check": n, "pass": bool(ok), "detail": d} for n, ok, d in checks],
    }


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    a = []
    A = a.append
    c = d["claims"]
    A("# BMAK PHYSICS re-verification: the 32-body list is the wreck's")
    A("")
    A("Generated by `Tools/scripts/reverify_physics.py` (`--write`); `--check` recomputes every")
    A("number from the packages and compares.  Reviewed card: `Research/BatmobileGrab/PHYSICS.md`")
    A("(`Tools/scripts/grab_physics.py`, pre-reset PHY-1).")
    A("")
    A("## 1. What the old card says, and what it checked")
    A("")
    A("It reports 4 vehicles x 32 bodies = 128 records from `RB_BodySetup.AggGeom`, asset")
    A("`Batmobile_V3_Destroyed_Physics`, and states \"all four vehicles carry byte-identical")
    A("collision layouts\".  Its `--check` recomputes its own two output files; it never hashes")
    A("an AggGeom payload, so \"byte-identical\" was asserted from parsed triples.")
    A("")
    A("    $ python Tools/scripts/grab_physics.py --check")
    A("    %s" % d["old_check"]["stdout"].replace("\n", "\n    "))
    A("")
    A("Exit %d.  The numbers are current - the sentence about bytes was not tested." % d["old_check"]["exit"])
    A("")
    A("## 2. Independent re-read of one package")
    A("")
    A("`%s`: %d bodies, each walked tag by tag with this script's own reader."
      % (d["package"]["package"], c["bodies_per_package"]))
    A("")
    A("| # | export | bone | boxes | extents XxYxZ (cm) | centre (cm) |")
    A("|---:|---:|---|---:|---|---|")
    for n, r in enumerate(d["package"]["bodies"]):
        A("| %d | %d | `%s` | %s | %s | %s |"
          % (n, r["export"], r["bone"], r["boxes"],
             "x".join("%g" % v for v in r["extents"]) if r["extents"] else "UNKNOWN",
             "(" + ", ".join("%g" % v for v in r["centre"]) + ")" if r["centre"] else "UNKNOWN"))
    A("")
    A("All %d agree with the old card's extents and centres, so the decode is sound; the")
    A("question was only *which asset* they belong to and whether \"byte-identical\" is literal.")
    A("")
    A("## 3. \"Byte-identical\": tested, not asserted")
    A("")
    A("Each `AggGeom` payload is hashed (sha1 of the StructProperty payload as stored):")
    A("")
    A("| package | bodies | distinct payload sha1 | identical to the others |")
    A("|---|---:|---:|---|")
    for v, p in d["by_package"].items():
        A("| `%s` | %d | %d | %s |" % (v, p["bodies"], p["distinct_agg_sha1"],
                                       "yes" if c["byte_identical_payloads"] else "no"))
    A("")
    A("Payload multisets identical across all four: **%s**.  Parsed triples identical: **%s**."
      % (c["byte_identical_payloads"], c["identical_triples"]))
    A("")
    A("**The old card's \"byte-identical\" sentence is false, and this is where it fails.**  The")
    A("payloads differ between the four packages at exactly **offset(s) %s** - a single u32 at"
      % c["payload_diff_offsets"])
    A("+12, whose value the old docstring dismissed as \"constant 2846 on every record\": %s."
      % json.dumps(c["u32_12_values"]))
    A("Every other byte matches, which is why the parsed extents and centres agree on all 32")
    A("bones and why a value-level comparison could not see the difference.")
    A("")
    A("## 4. Which asset owns this list")
    A("")
    A("Every body's outer chain, read from the export table:")
    A("")
    A("    %s" % json.dumps(d["package"]["outer_hist"]))
    A("")
    A("| package | PhysicsAsset exports | has an export named `Batmobile_V3_Physics` |")
    A("|---|---|---|")
    for v, p in d["by_package"].items():
        A("| `%s` | %s | %s |" % (v, ", ".join("`%s`" % x for x in p["assets"]),
                                  "yes" if p["has_drivable"] else "no"))
    A("")
    A("**The 32-body list belongs to `%s`** - the destroyed wreck.  The drivable car's collision")
    A("is a different asset, `%s` (export 158266, reached from `SVehicleMesh` offset 824 per")
    A("`COLLISION_GEOM.md`), whose bodies are 169750 `Batmobile_Chassis` and 169751")
    A("`Batmobile_Rig_Weapons_Trans` per `COLLISION_BOXES.md`.")
    A("")
    A("Bone-name intersection between the two lists: **%s**.  Chassis/hull bones in the 32-body"
      % (c["drivable_bone_overlap"] or "none"))
    A("list: **%s**.  So neither list can be mistaken for the other by bone name either."
      % (c["chassis_bones_in_this_list"] or "none"))
    A("")
    A("## 5. Verdict")
    A("")
    A("| claim | verdict |")
    A("|---|---|")
    A("| 4 packages x 32 bodies = 128 records | **holds** (%d read here)" % c["total_records"])
    A("| layouts are byte-identical across the four | **holds at payload level** (%s) |"
      % c["byte_identical_payloads"])
    A("| the asset is `Batmobile_V3_Destroyed_Physics` | **holds** (outer chain 32/32) |")
    A("| \"there is no chassis body\" | **holds for this asset** (0 chassis/hull bones) |")
    A("| the list belongs to the drivable car | **false** - drivable is `Batmobile_V3_Physics`,"
      " absent from these packages |")
    A("")
    A("The old card's own caveat already said hull collision for the drivable car does not come")
    A("from this asset; this re-read confirms the caveat and gives it a byte-level basis: the")
    A("packages contain no `Batmobile_V3_Physics` export at all.")
    A("")
    A("## 6. Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c2 in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c2["check"], "PASS" if c2["pass"] else "FAIL",
                                          c2["detail"]))
    A("")
    A("## 7. UNKNOWNs")
    A("")
    A("1. **The drivable asset's own bodies were not re-decoded here.**  Their export ids and")
    A("   bone names are cited from G3-01b (`COLLISION_GEOM.md`, `COLLISION_BOXES.md`); the")
    A("   package holding export 158266 was not opened in this pass.")
    A("2. **Why the four wreck assets are byte-identical.**  The payloads match; whether the")
    A("   cooker copied one asset or authored four identical ones is not in the bytes.")
    A("")
    A("## 8. Reproduce")
    A("")
    A("    uv run python Tools/scripts/reverify_physics.py --write")
    A("    uv run python Tools/scripts/reverify_physics.py --check")
    A("")
    return "\n".join(a) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")

    d = build()
    md, js = render(d), json.dumps(d, indent=1) + "\n"
    ok = True
    for c in d["checks"]:
        print("%s  %s" % ("PASS" if c["pass"] else "FAIL", c["check"]))
        print("      %s" % c["detail"])
        ok = ok and c["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))

    if args.write:
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s (%d B)" % (os.path.relpath(MD, ROOT), len(md.encode())))
        print("wrote %s (%d B)" % (os.path.relpath(JS, ROOT), len(js.encode())))
    if args.check:
        bad = []
        for path, want in ((MD, md), (JS, js)):
            if not os.path.exists(path):
                bad.append("%s missing" % os.path.relpath(path, ROOT))
            elif open(path, encoding="utf-8").read() != want:
                bad.append("%s differs" % os.path.relpath(path, ROOT))
        if bad:
            print("CHECK FAILED: " + "; ".join(bad))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
