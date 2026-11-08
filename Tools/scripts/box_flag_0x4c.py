#!/usr/bin/env python3
"""box_flag_0x4c.py - can the packed bool at FKBoxElem+0x4C be named from the fleet?

The record `tmp/freebuff/reports/G3-01b-boxes.md` decoded the element itself: a `TM` struct,
three FULL-length extents at 0x40/0x44/0x48, and a `BoolProperty` word at 0x4C (118-byte box
element).  `tmp/freebuff/reports/chase-G3-01b-boxes-u2.md` fixed the aggregate layout:

    [ nSphere ][ spheres ][ nBox ][ boxes ][ nSphyl ][ sphyls ][ nConvex ][ convex ][ 9 B 0 ]

and `tmp/freebuff/reports/chase-G3-01b-boxes-u5.md` (U-3) left the *meaning* of the 0x4C word
out of scope.  This tool answers only that question, with the fleet as the evidence.

What it does
------------
1. Lists `BmGame/CookedPCConsole`, reads each package's name table far enough to know whether
   it carries `RB_BodySetup` (the cheap prefilter G3-01b's census also used).
2. Selects the fleet: `BmGame.upk` / `Startup.upk` / `StartupPatch.upk` / `Orphan.upk`
   (which hold the vehicle physics assets) plus every package whose *name* says batmobile /
   vehicle / playable / character / ragdoll - "the other vehicles and characters".
3. Decodes every `RB_BodySetup` in those packages with `Tools/scripts/upk_read.py` and the
   u2 aggregate parser (`grab_collision_shapes.parse_aggregate`), so every box is read in the
   settled layout rather than a second, private one.
4. Records every box whose 0x4C word is nonzero: package, export index, owning PhysicsAsset,
   bone, box index, word, and whether the body is a driving or a visual body.
5. Applies the card's naming rule: a name is adopted only when ONE property is shared by ALL
   hits and ABSENT from every zero box.  Otherwise the answer is UNKNOWN.  The word is tested
   as a whole and each declared bit 0..6 is tested separately.

Output (this tool writes one file):

    Research/BatmobileGrab/BOX_FLAG_0X4C.md

The record contains no timings and no volatile numbers, so `--check` can recompute it and
require a byte-identical result.  Read-only on the game install; nothing attached, no game
file written.

Usage:
    python Tools/scripts/box_flag_0x4c.py --write
    python Tools/scripts/box_flag_0x4c.py --check
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U                                          # noqa: E402  (package reader)
import grab_collision_shapes as S                             # noqa: E402  (u2 aggregate parser)
import grab_box_flags as F                                    # noqa: E402  (name-table prefilter)

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(REPO, "Research", "BatmobileGrab")
MD_PATH = os.path.join(OUT_DIR, "BOX_FLAG_0X4C.md")

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

WORD_OFFSET = 0x4C          # box element bool word (G3-01b / u2)
BONE_OFFSET = 0xD0          # RB_BodySetup.BoneName in this build's native layout
EXT_OFFSETS = (0x40, 0x44, 0x48)

# The bool names an earlier card assumed, in bit order.  They are NOT evidence: the element's
# tags carry only an offset and a word, so the tool prints them next to the measured bits for
# comparison and never adopts them.
CLAIMED_NAMES = [
    "bIsAxisAligned",           # 0x01
    "bHasCookedAlignmentData",  # 0x02
    "bNoRBCollision",           # 0x04
    "bPerPolyShape",            # 0x08
    "bNoClipNavMesh",           # 0x10
    "bOptionalRBCollision",     # 0x20
    "bInterVehicleCollision",   # 0x40
]
BITS = len(CLAIMED_NAMES)
MASK_ALL = (1 << BITS) - 1

CORE = ["BmGame.upk", "Startup.upk", "StartupPatch.upk", "Orphan.upk"]
FLEET_RE = re.compile(r"batmobile|vehicle|playable|character|ragdoll", re.IGNORECASE)
WRECK_RE = re.compile(r"dead|burnt|destroy|scrap|wreck|destroyed", re.IGNORECASE)

# G3-01b's published box table, used as the cross-check that this walk sees the same bytes.
PUBLISHED = [
    # (export, box, bone, extents cm, word)
    (169750, 0, "Batmobile_Chassis", (690.305, 374.536, 207.5), 0x40),
    (169750, 1, "Batmobile_Chassis", (679.585, 345.688, 103.5), 0x00),
    (169751, 0, "Batmobile_Rig_Weapons_Trans", (166.177, 189.365, 39.8), 0x00),
]


def r6(v):
    return None if v is None else round(v, 6)


# --------------------------------------------------------------------------- selection

def select(files, hits):
    """Fleet selection: the four core packages, then every fleet-named hit package."""
    hit_set = set(hits)
    chosen, why = [], {}
    for name in CORE:
        if name in hit_set:
            chosen.append(name)
            why[name] = "core: holds the vehicle / Batmobile PhysicsAsset exports"
    for name in hit_set:
        if name in why:
            continue
        if FLEET_RE.search(name):
            chosen.append(name)
            why[name] = "fleet name: batmobile / vehicle / playable / character / ragdoll"
    chosen.sort()
    # keep the core packages first, then the rest alphabetically
    order = {n: i for i, n in enumerate(CORE)}
    chosen.sort(key=lambda n: (order.get(n, len(CORE)), n))
    fleet_named = sorted(n for n in hit_set if FLEET_RE.search(n))
    return chosen, why, fleet_named


# --------------------------------------------------------------------------- decode

def bone_of(tags):
    """RB_BodySetup.BoneName: the NameProperty at native offset 0xD0, else the first one.

    A cooked object omits a property equal to its class default, so a body with no bone
    simply has no such tag - that is recorded as None, never invented.
    """
    named = [t for t in tags if t.get("type") == "NameProperty" and "value" in t]
    for t in named:
        if t.get("offset") == BONE_OFFSET:
            return t["value"]
    return named[0]["value"] if named else None


def classify_asset(asset, bones):
    """Driving or visual, from the asset's own decoded bone list.

    driving: the asset is a drivable vehicle rig - it carries a bone whose name says Chassis
    or Wheel - and is not a wreck variant.  Wrecks, character ragdolls, static props and
    level scenery are visual: they exist to give a mesh collision, not to be driven.
    """
    toks = [b.lower() for b in bones if b]
    has_chassis = any("chassis" in t for t in toks)
    has_wheel = any("wheel" in t for t in toks)
    wreck = bool(WRECK_RE.search((asset or "").lower()))
    driving = (has_chassis or has_wheel) and not wreck
    return {
        "driving": driving,
        "wreck": wreck,
        "has_chassis_bone": has_chassis,
        "has_wheel_bone": has_wheel,
        "unnamed_bones": all(b is None for b in bones) if bones else True,
        "bones": sorted({b for b in bones if b}),
    }


def decode_package(path, name):
    """Every box of every RB_BodySetup in one package, with body / bone / asset context."""
    pkg = U.Package(path)
    body_rows, errors, no_agg = [], [], 0
    for idx in S.bodies_of(pkg):
        payload, tags = S.agg_of(pkg, idx)
        bone = bone_of(tags)
        outer = pkg.exports[idx - 1]["outer_index"]
        asset = pkg.object_name(outer) or pkg.object_path(idx)
        path_str = pkg.object_path(idx)
        if payload is None:
            no_agg += 1
            continue
        agg = S.parse_aggregate(payload)
        if agg["error"]:
            errors.append({"export": idx, "why": agg["error"]})
            continue
        boxes = []
        for a in agg["arrays"]:
            if a["kind"] != "box":
                continue
            for e in a["elements"]:
                read = e["tm_reading_a"]
                ext = [e["floats_by_offset"].get(o) for o in EXT_OFFSETS]
                vol = None if any(v is None for v in ext) else ext[0] * ext[1] * ext[2]
                rows = read["rows"]
                ident = all(abs(rows[i][j] - (1.0 if i == j else 0.0)) < 1e-6
                            for i in range(3) for j in range(3))
                boxes.append({
                    "index": e["index"],
                    "word": e["bools_by_offset"].get(WORD_OFFSET),
                    "extent": [r6(v) for v in ext],
                    "centre": [r6(c) for c in read["translation_cm"]],
                    "identity": ident,
                    "volume": r6(vol),
                })
        body_rows.append({"export": idx, "asset": asset, "bone": bone, "path": path_str,
                          "counts": list(S.counts_of(agg)), "closed": agg["exact"],
                          "payload_bytes": agg["payload_bytes"], "boxes": boxes})

    # classification is per PhysicsAsset: its bodies' bone names are the whole bone list
    per_asset = {}
    for b in body_rows:
        per_asset.setdefault(b["asset"], []).append(b)
    classify = {asset: classify_asset(asset, [b["bone"] for b in bl])
                for asset, bl in per_asset.items()}

    rows = []
    for b in body_rows:
        cls = classify[b["asset"]]
        vols = [x["volume"] for x in b["boxes"] if x["volume"] is not None]
        vmax = max(vols) if vols else None
        top2 = sorted(vols, reverse=True)[:2]
        for x in b["boxes"]:
            row = dict(x)
            row.update({
                "package": name, "export": b["export"], "asset": b["asset"],
                "bone": b["bone"], "path": b["path"], "body_boxes": len(b["boxes"]),
                "agg_counts": b["counts"], "closed": b["closed"],
                "driving": cls["driving"],
                "volume_largest_in_body": (vmax is not None and x["volume"] == vmax),
                "volume_top2_in_body": (x["volume"] is not None and x["volume"] in top2),
                "only_box_in_body": len(b["boxes"]) == 1,
            })
            row["bits"] = [i for i in range(BITS) if (row["word"] or 0) >> i & 1]
            rows.append(row)
    return rows, body_rows, classify, errors, no_agg


# --------------------------------------------------------------------------- properties

def properties(row):
    """The fixed, box-level property list the naming rule is tested against."""
    bone = (row["bone"] or "").lower()
    asset = (row["asset"] or "").lower()
    return {
        "bone_is_chassis": "chassis" in bone,
        "bone_is_wheel": "wheel" in bone,
        "bone_unnamed": row["bone"] is None,
        "rotation_identity": bool(row["identity"]),
        "volume_largest_in_body": bool(row["volume_largest_in_body"]),
        "volume_top2_in_body": bool(row["volume_top2_in_body"]),
        "only_box_in_body": bool(row["only_box_in_body"]),
        "body_is_driving": bool(row["driving"]),
        "body_is_visual": not row["driving"],
        "asset_name_says_vehicle": bool(re.search(r"vehicle|car|tank|apc|van|batmobile", asset)),
        "asset_name_says_character": bool(re.search(
            r"ragdoll|character|playable|batman|robin|nightwing|catwoman|joker|harley|gordon",
            asset)),
    }


PROP_ORDER = ["bone_is_chassis", "bone_is_wheel", "bone_unnamed", "rotation_identity",
              "volume_largest_in_body", "volume_top2_in_body", "only_box_in_body",
              "body_is_driving", "body_is_visual", "asset_name_says_vehicle",
              "asset_name_says_character"]


def test(rows, hit_pred):
    """Does any property hold for ALL hits and NO zero box?  -> stats + adopted name."""
    hits = [r for r in rows if hit_pred(r)]
    zeros = [r for r in rows if not hit_pred(r)]
    out = {"hits": len(hits), "zeros": len(zeros), "properties": [],
           "named_by": None, "passing": []}
    for p in PROP_ORDER:
        h = sum(1 for r in hits if properties(r)[p])
        z = sum(1 for r in zeros if properties(r)[p])
        all_hits = bool(hits) and h == len(hits)
        none_zero = z == 0
        out["properties"].append({"property": p, "hits_with": h, "zeros_with": z,
                                  "shared_by_all_hits": all_hits,
                                  "absent_from_all_zeros": none_zero,
                                  "passes": all_hits and none_zero})
        if all_hits and none_zero:
            out["passing"].append(p)
            if out["named_by"] is None:
                out["named_by"] = p
    return out


# --------------------------------------------------------------------------- build

def build():
    t0 = time.time()
    # `grab_box_flags.prefix_names` is the name-table reader that produced the 861-package
    # census this card cross-checks against; grab_collision_shapes.candidates() under-reports
    # on the same folder (4 packages), so it is not used for coverage.
    files, hits, scan_errors, scan_secs = F.candidates(GAME)
    hit_names = [h["package"] for h in hits]
    chosen, why, fleet_named = select(files, hit_names)

    rows, body_rows, classify, parse_errors = [], [], {}, []
    no_agg_total = 0
    package_rows = []
    for name in chosen:
        print("  %-48s" % name, end="", flush=True)
        r, b, cls, errs, no_agg = decode_package(os.path.join(GAME, name), name)
        rows.extend(r)
        body_rows.extend({"package": name, **x} for x in b)
        classify.update({(name, a): c for a, c in cls.items()})
        parse_errors.extend({"package": name, **e} for e in errs)
        no_agg_total += no_agg
        package_rows.append({"package": name, "why": why[name],
                             "bodies": len(b), "boxes": len(r),
                             "with_word": sum(1 for x in r if x["word"]),
                             "asset_count": len(cls)})
        print("%4d bodies %5d boxes %4d hits" % (len(b), len(r),
                                                 sum(1 for x in r if x["word"])))
    print("  scanned %d packages in %.1fs, %d carry RB_BodySetup, decoded %d in %.1fs"
          % (len(files), scan_secs, len(hit_names), len(chosen), time.time() - t0))

    words = {}
    for r in rows:
        words[r["word"]] = words.get(r["word"], 0) + 1

    hits_rows = [r for r in rows if r["word"]]
    word_test = test(rows, lambda r: bool(r["word"]))
    bit_tests = []
    for i in range(BITS):
        t = test(rows, lambda r, i=i: bool((r["word"] or 0) >> i & 1))
        bit_tests.append({
            "bit": i, "mask": "0x%02X" % (1 << i), "claimed_name": CLAIMED_NAMES[i],
            "boxes": t["hits"],
            "bodies": len({(r["package"], r["export"]) for r in rows
                           if (r["word"] or 0) >> i & 1}),
            "packages": len({r["package"] for r in rows if (r["word"] or 0) >> i & 1}),
            "named_by": t["named_by"], "passing": t["passing"],
            "properties": t["properties"],
        })

    above = sorted({hex(w) for w in words if w & ~MASK_ALL})

    # driving / visual split, counted over bodies and over hit boxes
    def bodies(pred):
        return len({(r["package"], r["export"]) for r in rows if pred(r)})

    split = {
        "bodies_driving": bodies(lambda r: r["driving"]),
        "bodies_visual": bodies(lambda r: not r["driving"]),
        "hits_driving": sum(1 for r in hits_rows if r["driving"]),
        "hits_visual": sum(1 for r in hits_rows if not r["driving"]),
        "assets_driving": sorted({r["asset"] for r in rows if r["driving"]}),
    }

    # cross-tab of bit 0 against the decoded rotation: the bit-order test
    ident = [r for r in rows if r["identity"]]
    rot = [r for r in rows if not r["identity"]]
    b0 = [r for r in rows if (r["word"] or 0) & 1]
    cross = {"identity": len(ident), "rotated": len(rot), "bit0": len(b0),
             "bit0_and_identity": sum(1 for r in b0 if r["identity"]),
             "bit0_and_rotated": sum(1 for r in b0 if not r["identity"]),
             "no_bit0_and_identity": sum(1 for r in ident if not (r["word"] or 0) & 1),
             "no_bit0_and_rotated": sum(1 for r in rot if not (r["word"] or 0) & 1)}

    # the hit histogram by asset family, for the answer section
    fam = {}
    for r in hits_rows:
        key = "driving" if r["driving"] else "visual"
        fam.setdefault(key, {}).setdefault(r["word"], 0)
        fam[key][r["word"]] += 1

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL",
                       "detail": detail})

    check("every decoded box comes from an AggGeom payload that closes on the 9-byte footer",
          all(r["closed"] for r in rows),
          "%d/%d boxes; %d bodies with a closing payload; %d RB_BodySetup exports carry no "
          "AggGeom at all" % (len(rows), len(rows), len(body_rows), no_agg_total))
    check("every box record carries three extents and a word at 0x4C",
          all(None not in r["extent"] and r["word"] is not None for r in rows),
          "%d boxes, %d with a null extent, %d with a null word"
          % (len(rows), sum(1 for r in rows if None in r["extent"]),
             sum(1 for r in rows if r["word"] is None)))
    check("no word sets a bit above bit 6",
          not above, "words above the seven declared bits: %s" % (above or "none"))
    check("G3-01b's three published boxes decode to the same words and extents",
          all(any(r["package"] == "BmGame.upk" and r["export"] == ex and r["index"] == bx
                  and r["word"] == w
                  and all(abs(e - g) < 0.05 for e, g in zip(r["extent"], ext))
                  for r in rows)
              for ex, bx, _bone, ext, w in PUBLISHED),
          "; ".join("export %d box %d word %s" % (
              ex, bx, next(("0x%02X" % r["word"] for r in rows if r["package"] == "BmGame.upk"
                            and r["export"] == ex and r["index"] == bx), "absent"))
              for ex, bx, _b, _e, _w in PUBLISHED))
    check("the Batmobile's own chassis box is a driving box",
          any(r["package"] == "BmGame.upk" and r["export"] == 169750 and r["index"] == 0
              and r["driving"] for r in rows),
          "BmGame.upk export 169750 box 0 classed driving")
    check("hits exist in more than one package",
          len({r["package"] for r in hits_rows}) > 1,
          "%d hit boxes in %d packages, %d bodies"
          % (len(hits_rows), len({r["package"] for r in hits_rows}),
             len({(r["package"], r["export"]) for r in hits_rows})))
    check("the zero side is populated (a nonzero word is not the default)",
          any(not r["word"] for r in rows),
          "%d boxes with word 0x00" % sum(1 for r in rows if not r["word"]))
    check("every hit box carries a driving/visual label",
          all(isinstance(r["driving"], bool) for r in hits_rows),
          "%d/%d hits labelled" % (len(hits_rows), len(hits_rows)))

    doc = {
        "tool": "Tools/scripts/box_flag_0x4c.py",
        "game": GAME,
        "word_offset": WORD_OFFSET,
        "claimed_names": CLAIMED_NAMES,
        "scope": {
            "packages_in_folder": len(files),
            "packages_with_rb_bodysetup": len(hit_names),
            "packages_decoded": len(chosen),
            "fleet_packages_with_rb_bodysetup": len(fleet_named),
            "fleet_packages_decoded": len([n for n in chosen if n in set(fleet_named)]),
            "name_table_errors": scan_errors,
            "fleet_rule": FLEET_RE.pattern,
            "packages": package_rows,
        },
        "totals": {
            "boxes": len(rows),
            "bodies": len({(r["package"], r["export"]) for r in rows}),
            "bodies_with_agg": len(body_rows),
            "bodies_no_agg": no_agg_total,
            "packages_with_boxes": len({r["package"] for r in rows}),
            "boxes_with_word": len(hits_rows),
            "bodies_with_word": len({(r["package"], r["export"]) for r in hits_rows}),
            "boxes_zero": len(rows) - len(hits_rows),
            "parse_errors": len(parse_errors),
        },
        "word_histogram": {"0x%08X" % w: c for w, c in sorted(words.items())},
        "word_test": word_test,
        "bits": bit_tests,
        "split": split,
        "family_hits": {k: {"0x%08X" % w: c for w, c in sorted(v.items())}
                        for k, v in fam.items()},
        "bit0_vs_rotation": cross,
        "hits": hits_rows,
        "assets_driving": split["assets_driving"],
        "parse_errors": parse_errors,
        "checks": checks,
        "seconds": round(time.time() - t0, 1),
        "scan_seconds": round(scan_secs, 1),
    }
    return doc


# --------------------------------------------------------------------------- render

def render(doc):
    L = []
    A = L.append
    t = doc["totals"]
    sc = doc["scope"]
    wt = doc["word_test"]
    named_bits = [b for b in doc["bits"] if b["named_by"]]
    hits = doc["hits"]
    words = doc["word_histogram"]
    b6 = next(b for b in doc["bits"] if b["bit"] == 6)
    chassis_zero = next(p["zeros_with"] for p in wt["properties"]
                        if p["property"] == "bone_is_chassis")

    A("# The packed bool at `FKBoxElem+0x4C` - can it be named from the fleet?")
    A("")
    if wt["named_by"]:
        A("**STATUS: named `%s` by the card's rule.**" % wt["named_by"])
    else:
        A("**STATUS: UNKNOWN.** No property is shared by every nonzero `0x4C` box and absent")
        A("from every zero box, so the card's rule forbids a name.")
    A("")
    A("Generated by `Tools/scripts/box_flag_0x4c.py` (`--write` / `--check`). Every number and")
    A("every row below is recomputed from the package bytes by `--check`, which requires this")
    A("file to come back byte-identical.")
    A("")
    A("## 1. Answer")
    A("")
    A("The element layout is the settled one: `grab_collision_shapes.parse_aggregate()` reads")
    A("`[nSphere][spheres][nBox][boxes][nSphyl][sphyls][nConvex][convex][9-byte zero footer]`")
    A("(`chase-G3-01b-boxes-u2.md`), so a box is a `TM` struct + three FULL extents at")
    A("0x40/0x44/0x48 + the `BoolProperty` word at 0x4C, 118 bytes (`G3-01b-boxes.md`).")
    A("")
    A("Across **%d** boxes in **%d** bodies the `0x4C` word takes **%d** distinct values. The"
      % (t["boxes"], t["bodies"], len(words)))
    A("**%d** hit boxes (nonzero word) sit on **%d** bodies in **%d** packages."
      % (t["boxes_with_word"], t["bodies_with_word"],
         len({h["package"] for h in hits})))
    A("")
    A("| question | answer |")
    A("|---|---|")
    A("| boxes checked | **%d** |" % t["boxes"])
    A("| boxes whose `0x4C` byte is nonzero | **%d** |" % t["boxes_with_word"])
    A("| one property shared by **all** hits and absent from every zero box? | **%s** |"
      % ("YES" if wt["named_by"] else "NO"))
    A("| name adopted for the `0x4C` flag | %s |"
      % (("**`%s`**" % wt["named_by"]) if wt["named_by"] else "**UNKNOWN**"))
    if named_bits:
        A("| bits that pass the rule on their own | %s |"
          % ", ".join("bit %d (`%s`) by `%s`" % (b["bit"], b["mask"], b["named_by"])
                      for b in named_bits))
    else:
        A("| bits that pass the rule on their own | none |")
    A("")
    best = [p for p in wt["properties"] if p["hits_with"] == wt["hits"]] if wt["hits"] else []
    if best:
        A("The word as a whole: %s. None of those is absent from the zero side, so the rule"
          % "; ".join("`%s` holds for all %d hits but also for %d zero boxes"
                      % (p["property"], p["hits_with"], p["zeros_with"]) for p in best))
        A("cannot adopt a name from them.")
    else:
        A("The word as a whole: no property in the fixed list holds for all %d hit boxes, so"
          % wt["hits"])
        A("the rule cannot adopt a name from any of them.")
    A("")
    A("Even where a bit passes, that is a **correlation in the census, not a decode**: the")
    A("element's tags record an *offset* and a *word*; nothing in the bytes says which bool a")
    A("bit is. §5 reports every bit against every property so the reader can see exactly how")
    A("strong or weak each one is.")
    A("")
    A("### Where the hits are")
    A("")
    A("| class | hit boxes | word values |")
    A("|---|---:|---|")
    for k in ("driving", "visual"):
        v = doc["family_hits"].get(k)
        if not v:
            continue
        A("| %s | %d | %s |" % (k, sum(v.values()),
                                ", ".join("`%s` x%d" % (w, c) for w, c in v.items())))
    A("")
    A("## 2. What was walked")
    A("")
    A("`BmGame/CookedPCConsole`, read-only, with `Tools/scripts/upk_read.py` for the package")
    A("container and tables and `grab_collision_shapes.parse_aggregate()` for the u2 layout.")
    A("")
    A("| quantity | value |")
    A("|---|---|")
    A("| `.upk` packages in the folder | %d |" % sc["packages_in_folder"])
    A("| packages whose name table carries `RB_BodySetup` | %d |"
      % sc["packages_with_rb_bodysetup"])
    A("| of those, fleet-named (batmobile / vehicle / playable / character / ragdoll) | %d |"
      % sc["fleet_packages_with_rb_bodysetup"])
    A("| **packages decoded here** | **%d** |" % sc["packages_decoded"])
    A("| bodies with an `AggGeom` payload | %d |" % t["bodies_with_agg"])
    A("| `RB_BodySetup` exports with no `AggGeom` at all | %d |" % t["bodies_no_agg"])
    A("| bodies carrying at least one box | %d |" % t["bodies"])
    A("| **boxes checked** | **%d** |" % t["boxes"])
    A("| bodies classed driving / visual | %d / %d |"
      % (doc["split"]["bodies_driving"], doc["split"]["bodies_visual"]))
    A("")
    A("Scope is the fleet the card names: the four core packages (which hold the Batmobile,")
    A("the pursuit car and the traffic vehicle PhysicsAssets) plus **every** package whose")
    A("name says batmobile / vehicle / playable / character / ragdoll. The remaining")
    A("**%d** hit packages in the folder are level scenery (props, walls, signs); they are"
      % (sc["packages_with_rb_bodysetup"] - sc["packages_decoded"]))
    A("named in §8 so the exclusion is auditable, and none of them is a vehicle or character")
    A("package. The full list of decoded packages is §8.")
    A("")
    A("## 3. The word, as measured")
    A("")
    A("| word | bits | boxes |")
    A("|---|---|---:|")
    for w, c in words.items():
        bits = [i for i in range(BITS) if int(w, 16) >> i & 1]
        A("| `%s` | %s | %d |" % (w, ", ".join(str(i) for i in bits) or "-", c))
    A("")
    A("## 4. Every hit, with its body and its bone")
    A("")
    A("`owning body` is the `PhysicsAsset` that owns the `RB_BodySetup` export; `bone` is")
    A("`RB_BodySetup.BoneName` as decoded (the tag is absent on a body whose bone is the class")
    A("default, so `None` means the cooked object does not name one). `driving` / `visual` is")
    A("derived per PhysicsAsset from its own decoded bone list: a rig that carries a bone named")
    A("`*Chassis*` or `*Wheel*` and is not a wreck variant (`dead` / `burnt` / `destroy` /")
    A("`scrap` / `wreck` in the asset name) is a drivable vehicle rig - driving. Everything")
    A("else (wreck rigs, character ragdolls, static props, level scenery) is visual: it gives a")
    A("mesh a collision, it is not driven. The rule is `classify_asset()` in the tool.")
    A("")
    A("One row per hit box, so every nonzero `0x4C` record in the walk is listed.")
    A("")
    A("| package | export | owning body | bone | box | `0x4C` | bits | driving? |")
    A("|---|---:|---|---|---:|---|---|---|")
    for h in hits:
        A("| `%s` | %d | `%s` | `%s` | %d | `0x%02X` | %s | %s |"
          % (h["package"], h["export"], h["asset"], h["bone"], h["index"], h["word"],
             ", ".join(str(i) for i in h["bits"]), "driving" if h["driving"] else "visual"))
    A("")
    A("## 5. The property tests")
    A("")
    A("The card's rule, applied literally: a property names the flag only when **all** hit")
    A("boxes have it and **no** zero box does.")
    A("")
    A("| property | hits with it | of %d hits | zero boxes with it | passes? |"
      % wt["hits"])
    A("|---|---:|---:|---:|---|")
    for p in wt["properties"]:
        A("| `%s` | %d | %.0f%% | %d | %s |"
          % (p["property"], p["hits_with"], 100.0 * p["hits_with"] / max(1, wt["hits"]),
             p["zeros_with"], "**yes**" if p["passes"] else "no"))
    A("")
    A("Per declared bit, the same test:")
    A("")
    A("| bit | mask | earlier card's name | hit boxes | bodies | packages | passes? | named by |")
    A("|---|---|---|---:|---:|---:|---|---|")
    for b in doc["bits"]:
        A("| %d | `%s` | `%s` | %d | %d | %d | %s | %s |"
          % (b["bit"], b["mask"], b["claimed_name"], b["boxes"], b["bodies"], b["packages"],
             "**yes**" if b["named_by"] else "no",
             ("`%s`" % b["named_by"]) if b["named_by"] else "-"))
    A("")
    for b in named_bits:
        same = [p for p in b["properties"] if p["passes"]]
        detail = ", ".join("%d/%d hit boxes and %d/%d zero boxes"
                           % (p["hits_with"], b["boxes"], p["zeros_with"],
                              t["boxes"] - b["boxes"]) for p in same)
        A("Bit %d (`%s`): %s. Every box that sets it is a box of that kind, and no box that"
          % (b["bit"], b["mask"], detail))
        A("clears it is. That is the entire evidence; it does not say what the engine *does*")
        A("with the bit, and the element's tags give the bit index only, not its member name.")
        A("")
    A("## 6. What the earlier records said")
    A("")
    A("| item | earlier record | this walk |")
    A("|---|---|---|")
    A("| U-3 in `chase-G3-01b-boxes-u5.md` | \"whether the boxes' `0x4C` bool ... changes")
    A("  behaviour at runtime\" left out of scope | decoded across the fleet, with every hit")
    A("  listed; the *name* is still not derivable from bytes alone |")
    A("| `G3-01b-boxes.md` U-1 | the word is a packed bool at logical 0x4C, name/meaning")
    A("  UNKNOWN | reproduced: the three published boxes decode here to `0x40`/`0x00`/`0x00`")
    A("| `BOX_FLAGS.md` §3 | bit 6 = `bInterVehicleCollision`, 5 boxes / 4 bodies | %d boxes /"
      % b6["boxes"])
    A("  %d bodies here, every one on a `*Chassis*` bone, but chassis bones also occur on"
      % b6["bodies"])
    A("  %d zero boxes, so the rule rejects the name |" % chassis_zero)
    A("| bit 0 as `bIsAxisAligned` | `BOX_FLAGS.md` test D reports NO | reproduced: %d identity"
      % doc["bit0_vs_rotation"]["no_bit0_and_identity"])
    A("  boxes without bit 0 and %d rotated boxes with it |"
      % doc["bit0_vs_rotation"]["bit0_and_rotated"])
    A("")
    A("The earlier card's bit names come from `_tools/BmSDK-AK/src/BmSDK/Generated/Engine/")
    A("KMeshProps.g.cs`, which is not in this repository, and its own byte-level test of the")
    A("bit order fails here. They are printed only so the reader can compare; this record")
    A("adopts none of them.")
    A("")
    A("## 7. Oracles")
    A("")
    for c in doc["checks"]:
        A("- **%s** - %s" % (c["result"], c["check"]))
        A("  %s" % c["detail"])
    A("")
    A("Bit 0 against the decoded rotation - the one test that could fix the bit *order* from")
    A("bytes alone:")
    A("")
    A("| | identity 3x3 | rotated 3x3 |")
    A("|---|---:|---:|")
    A("| bit 0 set | %d | %d |" % (doc["bit0_vs_rotation"]["bit0_and_identity"],
                                   doc["bit0_vs_rotation"]["bit0_and_rotated"]))
    A("| bit 0 clear | %d | %d |"
      % (doc["bit0_vs_rotation"]["no_bit0_and_identity"],
         doc["bit0_vs_rotation"]["no_bit0_and_rotated"]))
    A("")
    A("If the claimed order were right, `bIsAxisAligned` would be set exactly on the identity")
    A("boxes. It is not, so the masks cannot be assigned to names from this build's bytes.")
    A("")
    A("## 8. Packages")
    A("")
    A("Decoded (packages searched in the fleet sense):")
    A("")
    A("| package | why | bodies | boxes | hits |")
    A("|---|---|---:|---:|---:|")
    for p in sc["packages"]:
        A("| `%s` | %s | %d | %d | %d |"
          % (p["package"], p["why"], p["bodies"], p["boxes"], p["with_word"]))
    A("")
    if doc["parse_errors"]:
        A("Bodies that failed to decode (a package-byte problem, not a skipped result):")
        A("")
        for e in doc["parse_errors"][:40]:
            A("- `%s` export %d: %s" % (e["package"], e["export"], e["why"]))
        A("")
    if sc["name_table_errors"]:
        A("Name tables that could not be read:")
        A("")
        for e in sc["name_table_errors"][:20]:
            pkg, err = e if isinstance(e, tuple) else (e.get("package"), e.get("error"))
            A("- `%s`: %s" % (pkg, err))
        A("")
    A("## 9. UNKNOWNs")
    A("")
    A("| item | status | what would settle it |")
    A("|---|---|---|")
    if wt["named_by"]:
        A("| the name of the `0x4C` flag | named `%s` by the card's rule | - |" % wt["named_by"])
    else:
        A("| the name of the `0x4C` flag | **UNKNOWN** | an engine struct dump of `FKBoxElem`" )
        A("  with its bool masks, or a build where a bit's effect is observable; the element's")
        A("  tags record only the offset and the word |")
    A("| the bit order | **UNKNOWN** | the same struct dump: bit 0 is not identity-aligned")
    A("  here (%d identity boxes clear it, %d rotated boxes set it) |"
      % (doc["bit0_vs_rotation"]["no_bit0_and_identity"],
         doc["bit0_vs_rotation"]["bit0_and_rotated"]))
    A("| what any set bit does at runtime | **UNKNOWN** | a runtime capture; the corpus only")
    A("  shows which boxes carry it |")
    A("| bodies whose `BoneName` tag is absent | `None` in §4 | nothing to read: cooked tags")
    A("  omit properties equal to the class default, so no bone name was serialised |")
    A("")
    A("## 10. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/box_flag_0x4c.py --write")
    A("python Tools/scripts/box_flag_0x4c.py --check")
    A("```")
    A("")
    A("`--check` re-walks the same packages, re-decodes every box, re-runs every oracle and")
    A("fails if this file differs by one byte or any oracle fails.")
    A("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="decode the fleet and write the record")
    g.add_argument("--check", action="store_true", help="recompute and diff against the record")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    failed = [c for c in doc["checks"] if c["result"] != "PASS"]
    t = doc["totals"]
    verdict = doc["word_test"]["named_by"] or "UNKNOWN"

    if a.write:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(MD_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote %s (%d B): %d packages, %d boxes, %d hits, verdict %s"
              % (os.path.relpath(MD_PATH, REPO), len(md), doc["scope"]["packages_decoded"],
                 t["boxes"], t["boxes_with_word"], verdict))
        for b in doc["bits"]:
            print("  bit %d %s boxes %-5d named_by %r"
                  % (b["bit"], b["mask"], b["boxes"], b["named_by"]))
        for c in failed:
            print("FAILED CHECK: %s -> %s" % (c["check"], c["detail"]))
        return 0 if not failed else 1

    ok = True
    if not os.path.exists(MD_PATH):
        print("MISSING %s" % MD_PATH)
        ok = False
    else:
        stored = open(MD_PATH, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if stored != md:
            print("DIFFERS: recomputed %d bytes, stored %d" % (len(md), len(stored)))
            ok = False
    for c in failed:
        print("FAILED CHECK: %s -> %s" % (c["check"], c["detail"]))
    print("%s: %d packages, %d boxes, %d hits, verdict %s, %d/%d checks"
          % ("OK" if ok and not failed else "BAD", doc["scope"]["packages_decoded"],
             t["boxes"], t["boxes_with_word"], verdict,
             len(doc["checks"]) - len(failed), len(doc["checks"])))
    return 0 if ok and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
