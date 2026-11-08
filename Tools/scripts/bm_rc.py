"""bm_rc.py - B-14: the release candidate `Builds/bm-RC1` (one tree: D-2 = one hybrid car).

Card (GRAB_BACKLOG.md B-14): one dropzone tree per variant set, receipt.json, install.ps1 with
-Action Install|Verify|Rollback091|Status, a rollback copy plan for every replaced file (banks and
Rebel Drop files too). Done (gate BX): the receipt lists every file with sha256; the installer's
-WhatIf lists exactly those.

Lineage of the card trees (each receipt's `base`):
    bm-001 -> bm-002 (B-02/03/04) -> bm-009 (B-09) -> bm-005 (B-05) -> {bm-006 B-06, bm-007 B-07,
    bm-008 B-08, bm-013b B-13b}       bm-004 (B-11 banks, outside the tree)   bm-013 (B-13 profile)
    B-10 = Working/Collision/batmobile.physicsc (in no tree yet: integrated here, gap G4)

Merge (every step asserts):
  1. stage = bm-005/aaf (it already holds B-02/03/04/05/09).
  2. files ONE branch adds or changes vs bm-005 are copied from that branch; a file two branches
     change is merged, never overwritten: the `.epe` and `@files.xml` go through a 3-way text merge
     (`git merge-file`, base bm-005) - the .epe as ConvertProperty XML (the round trip B-05 proved).
     A conflict stops the build. Afterwards every line any branch changed must be in the result.
  3. B-10: the donor's `sportsmuscle.physicsc` in the tree is replaced by the B-10 file (sha256 pinned).
  4. B-13b: `bm_leaf.rename_tree` gives the merged tree the standalone leaf.
  5. pack (SmallPack), unpack again and compare every file; `.toc` = the vanilla donor .toc with the
     leaf renamed, patched by `eetoc.patch_toc`; every changed file whose vanilla record is offset 0
     (= "load from the archives", test-023) is made internal - computed, not listed by hand (R8).
  6. the dropzone tree `drop/`: the `.ee` + `.ee.toc` at the new leaf, B-13's profile tables + icon,
     B-11's two banks. Every file hashed into the receipt with its owner card.
  7. install.ps1 (Windows PowerShell 5.1): Status | WhatIf | Install | Verify | Rollback091. A file the
     dropzone already has is backed up to <name>.bm-RC1-backup before Install and restored by
     Rollback091; a file this build added is removed.

Budgets (R9) and spec_check are V-01's gates; this card reports the inherited figures only.

Usage
    python Tools/scripts/bm_rc.py --write      # build bm-RC1
    python Tools/scripts/bm_rc.py --check      # re-hash, -WhatIf vs receipt, offline rehearsal
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_leaf  # noqa: E402
import eetoc  # noqa: E402

TAG = "bm-RC1"
OUT = os.path.join(ROOT, "Builds", TAG)
B = lambda t: os.path.join(ROOT, "Builds", t)
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
CONV = os.path.join(GIBBED, "Gibbed.JustCause3.ConvertProperty.exe")
WORK = os.environ.get("JC3_RAW", "E:/Modding/_shared/gamedata/JC3grab") + "/rc_merge"
DIR = bm_leaf.DIR
OLD, NEW = bm_leaf.OLD, bm_leaf.NEW
EPE_OLD = DIR + OLD + ".epe"
PHYS = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc"
B10 = os.path.join(ROOT, "Working", "Collision", "batmobile.physicsc")
B10_SHA = "192c12479d81da6e9515b42df2f0e55db555986633c497d7f2013b1f913d0d9e"
BASE = "bm-005"
BRANCHES = [("bm-006", "B-06"), ("bm-007", "B-07"), ("bm-008", "B-08")]
DROP_EE = DIR + NEW + ".ee"
SIM = os.path.join(ROOT, "tmp", "rc_sim")
PRE_EPE = os.path.join(ROOT, "Working", "RC", "base_bm005_prerework.epe")
PRE_SHA = "d118c0aa29167a5e6b695321a3e964b5b61e1bdfa7f5b5656277977c6c395c3d"
STALE_EPE_BASE = {"bm-007", "bm-008"}   # built on the pre-rework bm-005 (MODLOG B-06 rework, sha above)
DEPS = ["B-01", "B-02", "B-03", "B-04", "B-05", "B-06", "B-07", "B-08", "B-09", "B-10", "B-11",
        "B-12", "B-13"]


def sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tree(aaf: str) -> dict[str, str]:
    return {os.path.relpath(os.path.join(dp, n), aaf).replace("\\", "/"): sha(os.path.join(dp, n))
            for dp, _, fs in os.walk(aaf) for n in fs}


def run(args, what):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"{what} failed (rc {r.returncode}): {(r.stdout + r.stderr)[-800:]}")
    return r


def deps_ok() -> list[str]:
    t = open(os.path.join(ROOT, "GRAB_BACKLOG.md"), encoding="utf-8").read().splitlines()
    st = {l.split("|")[1].strip(): l.split("|")[2].strip() for l in t if l.startswith("| B-")}
    bad = [d for d in DEPS if not st.get(d, "").startswith(("done", "skipped"))]
    if bad:
        raise SystemExit(f"deps not done/skipped in section 12: {[(d, st.get(d)) for d in bad]}")
    return [f"{d}: {st[d][:30]}" for d in DEPS]


def merge3(base: str, branches: list, out: str) -> dict:
    """3-way merge onto `base`. A branch is a path (built on `base`) or (path, its_own_base): a
    branch built on an OLDER base contributes only its own edits, never the old base's lines
    (2026-10-31: bm-007/bm-008 sat on the pre-rework bm-005 and would have undone B-05's rework)."""
    os.makedirs(WORK, exist_ok=True)
    cur = os.path.join(WORK, "merge_cur")
    shutil.copy(base, cur)
    pairs = [b if isinstance(b, tuple) else (b, base) for b in branches]
    for br, bb in pairs:
        r = subprocess.run(["git", "merge-file", "-p", cur, bb, br], capture_output=True)
        if r.returncode != 0:
            raise SystemExit(f"3-way merge conflict ({r.returncode}) merging {br}")
        open(cur, "wb").write(r.stdout)
    shutil.copy(cur, out)
    # every line a branch changed vs ITS base must be in the result
    import difflib
    res = open(out, encoding="utf-8-sig", errors="replace").read().splitlines()
    bl = open(base, encoding="utf-8-sig", errors="replace").read().splitlines()
    rs, missing = set(res), []
    for br, bb in pairs:
        bbl = open(bb, encoding="utf-8-sig", errors="replace").read().splitlines()
        for l in difflib.unified_diff(bbl, open(br, encoding="utf-8-sig", errors="replace").read().splitlines(), n=0):
            if l.startswith("+") and not l.startswith("+++") and l[1:] not in rs:
                missing.append((os.path.basename(br), l[1:][:120]))
    if missing:
        raise SystemExit(f"merged result lost branch lines: {missing[:5]}")
    return {"base_lines": len(bl), "merged_lines": len(res)}


def vfs(path: str) -> bytes:
    import jc3strings, jc3weapons, jc3index  # noqa: E401
    row = jc3strings.load_index().get(path)
    if row is None:
        raise SystemExit(f"{path} not in the index")
    return jc3weapons.read_row(row, jc3index.DEFAULT_GAME)


def build() -> dict:
    deps = deps_ok()
    stage = os.path.join(WORK, "stage")
    if os.path.exists(stage):
        shutil.rmtree(stage)
    shutil.copytree(os.path.join(B(BASE), "aaf"), stage)
    base_t = tree(os.path.join(B(BASE), "aaf"))
    owners, steps = {}, []

    # 2. branch contributions
    touched: dict[str, list[str]] = {}
    for t, card in BRANCHES:
        bt = tree(os.path.join(B(t), "aaf"))
        for p, h in bt.items():
            if base_t.get(p) != h:
                touched.setdefault(p, []).append(t)
        gone = set(base_t) - set(bt)
        if gone:
            raise SystemExit(f"{t} removes files: {sorted(gone)[:5]}")
    card_of = dict(BRANCHES)
    for p, ts in sorted(touched.items()):
        if len(ts) == 1:
            shutil.copy(os.path.join(B(ts[0]), "aaf", p), os.path.join(stage, p)) if os.path.exists(
                os.path.join(stage, os.path.dirname(p))) else (os.makedirs(os.path.join(stage, os.path.dirname(p))),
                shutil.copy(os.path.join(B(ts[0]), "aaf", p), os.path.join(stage, p)))
            owners[p] = card_of[ts[0]]
            steps.append(f"copy {p} from {ts[0]}")
        elif p == EPE_OLD:
            xs = []
            for t in [BASE] + ts:
                x = os.path.join(WORK, f"{t}.xml")
                run([CONV, "--e", os.path.join(B(t), "aaf", p), x], f"ConvertProperty --e {t}")
                xs.append(x)
            if sha(PRE_EPE) != PRE_SHA:
                raise SystemExit("Working/RC/base_bm005_prerework.epe sha256 changed")
            pre_x = os.path.join(WORK, "prerework.xml")
            run([CONV, "--e", PRE_EPE, pre_x], "ConvertProperty --e prerework")
            branches = []
            for t, x in zip(ts, xs[1:]):
                eb = sha(os.path.join(B(t), "aaf", p))
                if t in STALE_EPE_BASE:
                    branches.append((x, pre_x))
                else:
                    branches.append(x)
                if eb == PRE_SHA:
                    steps.append(f"{t}: .epe is byte-identical to the pre-rework base -> contributes no .epe edit")
            m = merge3(xs[0], branches, os.path.join(WORK, "merged.xml"))
            # B-16: weapon-clone cleanup (V-03 found it): B-05 cloned the APC's CBulletWeaponBase and kept
            # the APC's owner link (F30CCB1C -> the APC's own CCar root, absent here) and its mounted-M2
            # body members (F9DCF6AB model_xml, 98BBA63E col .pfx, 9E74F03F grip_point), files that live
            # only inside the APC's .ee. The medium tank (whose w602/w603 names these clones carry) has
            # F30CCB1C null and none of the three members; the preorder Serpente's weapons are the same.
            mx = open(os.path.join(WORK, "merged.xml"), encoding="utf-8").read()
            n_owner = mx.count('id="F30CCB1C" type="objectid">4DAE31AE=FFFF05DA<')
            mx = mx.replace('id="F30CCB1C" type="objectid">4DAE31AE=FFFF05DA<', 'id="F30CCB1C" type="objectid">00000000<')
            n_body = 0
            for mem in ("F9DCF6AB", "98BBA63E", "9E74F03F"):
                mx, k = re.subn(rf'\n\s*<value id="{mem}" type="string">[^<]*w206_mounted_capstone_m2hm[^<]*</value>', "", mx)
                n_body += k
            open(os.path.join(WORK, "merged.xml"), "w", encoding="utf-8").write(mx)
            steps.append(f"B-16: {n_owner} F30CCB1C owner links -> null, {n_body} APC M2 gun-body members removed (medium-tank convention)")
            run([CONV, "-i", os.path.join(WORK, "merged.xml"), os.path.join(stage, p)], "ConvertProperty -i")
            run([CONV, "--e", os.path.join(stage, p), os.path.join(WORK, "merged_rt.xml")], "ConvertProperty rt")
            a = open(os.path.join(WORK, "merged.xml"), encoding="utf-8").read()
            b = open(os.path.join(WORK, "merged_rt.xml"), encoding="utf-8").read()
            if a != b:
                raise SystemExit("the merged .epe does not round-trip to the merged XML")
            owners[p] = "+".join(card_of[t] for t in ts) + "+B-16"
            steps.append(f"3-way merge {p} from {ts}: {m}, round trip identical")
        elif p == "@files.xml":
            m = merge3(os.path.join(B(BASE), "aaf", p), [os.path.join(B(t), "aaf", p) for t in ts],
                       os.path.join(stage, p))
            owners[p] = "+".join(card_of[t] for t in ts)
            steps.append(f"3-way merge {p} from {ts}: {m}")
        else:
            raise SystemExit(f"{p} changed by {ts} and has no merge rule")

    # 3. B-10 collision (BM_NO_B10=1: Q probe, keep the lineage physicsc - the one bm-001 ran in game)
    if os.environ.get("BM_NO_B10") == "1":
        steps.append("B-10: SKIPPED (BM_NO_B10=1)")
    elif sha(B10) != B10_SHA:
        raise SystemExit("B-10 physicsc sha256 differs from the one B-10 recorded")
    elif not os.path.exists(os.path.join(stage, PHYS)):
        raise SystemExit(f"{PHYS} not in the tree")
    else:
        shutil.copy(B10, os.path.join(stage, PHYS))
        owners[PHYS] = "B-10"
        steps.append(f"B-10: {PHYS} <- Working/Collision/batmobile.physicsc")
        # 3a2. B-10b: the body's world collision from the Batmobile mesh (Q re-test 4; bm_colmesh docstring)
        import bm_colmesh
        body_rbm = os.path.join(stage, os.path.dirname(PHYS), "sportsmuscle_body_lod2.rbm")
        cm = bm_colmesh.apply(os.path.join(stage, PHYS), body_rbm)
        owners[PHYS] += "+B-10b"
        steps.append(f"B-10b: {cm}")
        # 3a3. B-10c: body 0 (WORLD collision) = the Batmobile's convex hull (Q re-test 5; bm_colhull docstring)
        import bm_colhull
        ch = bm_colhull.apply(os.path.join(stage, PHYS), body_rbm)
        owners[PHYS] += "+B-10c"
        steps.append(f"B-10c: {ch}")

    # 3b. B-15 model budget (R9): far-LOD trim, calibrated measure (bm_budget.py docstring)
    import bm_budget
    bud = bm_budget.trim(stage)
    for c in bud["lods_changed"]:
        owners[c["lod"]] = "B-15"
    steps.append(f"B-15: {len(bud['lods_changed'])} .lod trimmed, non-vanilla model "
                 f"{bud['before']['non_vanilla_kb']} -> {bud['after']['non_vanilla_kb']} KB of {bud['cap_kb']}")

    # 3b2. B-04L parts module -> the live (patch_win64) schema (B-18 crash +0x2d49e0; bm_schema.py docstring)
    import bm_schema
    import bm_parts
    reb = bm_schema.rebuild_parts(os.path.join(stage, bm_parts.MODULE), vfs(bm_parts.MODULE), os.path.join(WORK, "b04r"))
    steps.append(f"B-04R: {reb}")
    sch = bm_schema.port_parts(os.path.join(stage, bm_parts.MODULE), vfs(bm_parts.MODULE), os.path.join(WORK, "b04l"))
    owners[bm_parts.MODULE] = owners.get(bm_parts.MODULE, "B-02/B-03/B-04") + "+B-04L"
    steps.append(f"B-04L: {sch}")

    # 3c. B-17 hide the visible Serpente leaf panels (V-02 per-part blame; bm_hide.py docstring)
    if os.environ.get("BM_NO_B17") == "1":   # Q-1a: test the raw part translation (user 2026-10-31)
        steps.append("B-17: SKIPPED (BM_NO_B17=1)")
    else:
        import bm_hide
        hid = bm_hide.apply(stage, os.path.join(WORK, "b17"))
        owners[bm_hide.bm_parts.MODULE] = owners.get(bm_hide.bm_parts.MODULE, "B-02/B-03/B-04") + "+B-17"
        steps.append(f"B-17: starts_deleted on {hid['hidden']}; held {sorted(hid['held'])}")

    # 3c2. T-13R interaction transforms on the merged .epe (Q re-test 4 "unenterable"; bm_entity
    # interaction_transforms docstring). Applied here, not only in B-05: the branch .epe files were built on
    # the old bm-005 and the 3-way merge would carry T-13's transforms back.
    import bm_entity
    import xml.etree.ElementTree as ET
    ex_in, ex_out = os.path.join(WORK, "t13r_in.xml"), os.path.join(WORK, "t13r_out.xml")
    epe_stage = os.path.join(stage, EPE_OLD)
    bm_entity.export(epe_stage, ex_in)
    tr = ET.parse(ex_in)
    n13 = bm_entity.interaction_transforms(tr.getroot())
    tr.write(ex_out, encoding="utf-8", xml_declaration=True)
    bm_entity.imp(ex_out, epe_stage)
    bm_entity.export(epe_stage, ex_in)

    def worlds(r):
        return {(bm_entity.vcls(o), bm_entity.vname(o)): [float(x) for x in bm_entity.get_value(o, "world").split(",")]
                for o in bm_entity.objects(r) if bm_entity.vcls(o) in ("CInteractionGraphPointNode", "CInteractionTrigger")
                and any(v.get("name") == "world" for v in o.findall("value"))}
    chk = ET.parse(ex_in).getroot()
    w_imported = worlds(chk)
    bm_entity.interaction_transforms(chk)
    if any(max(abs(a - b) for a, b in zip(w_imported[k], v)) > 1e-4 for k, v in worlds(chk).items()):
        raise SystemExit("T-13R: the imported .epe does not hold the written transforms")
    owners[EPE_OLD] = owners.get(EPE_OLD, "B-05") + "+T-13R"
    steps.append(f"T-13R: {n13} interaction transforms (donor 3x3 x box map, G2-18 positions, Driver seat)")

    # 3d. B-18 own paths: nothing the Batmobile changed may sit at a path a vanilla entity loads (Q-1a re-test 3)
    import bm_paths
    van_ee = eetoc.unaaf(vfs(DIR + OLD + ".ee"))
    van_files = {n: van_ee[o:o + s] for n, o, s in eetoc.sarc_dir(van_ee)}
    b18 = bm_paths.apply(stage, van_files, set(bm_leaf.verify_manifest(stage)["dangling"]), OLD,
                         os.path.join(WORK, "b18"))
    for o, n in b18["moved"].items():
        owners[n] = owners.pop(o, "base (bm-005 lineage)") + "+B-18"
    for m in b18["repointed"]:
        if m not in b18["moved"]:
            owners[m] = owners.get(m, "base (bm-005 lineage)") + "+B-18"
    for n in b18["reverted_to_vanilla"]:
        owners[n] = "B-18 (vanilla bytes)"
    steps.append(f"B-18: {len(b18['moved'])} files -> .../{bm_paths.SUB}/, {len(b18['repointed'])} referrers "
                 f"repointed, reverted to vanilla {b18['reverted_to_vanilla']}")

    # 4. B-13b leaf
    aaf = os.path.join(OUT, "aaf")
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    leaf = bm_leaf.rename_tree(stage, aaf)
    for k in list(owners):
        if OLD in k:
            owners[k.replace(OLD, NEW)] = owners.pop(k) + "+B-13b"
    for e in bm_leaf.INNER:
        owners.setdefault(DIR + NEW + e, "B-13b")
    owners["@files.xml"] = owners.get("@files.xml", "") + "+B-13b"
    steps.append(f"B-13b: leaf {NEW} (epe root {leaf['epe_after']})")

    # 5. pack, verify, toc
    drop = os.path.join(OUT, "drop")
    ee = os.path.join(drop, DROP_EE)
    os.makedirs(os.path.dirname(ee))
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee], "SmallPack")
    ver = os.path.join(WORK, "verify")
    if os.path.exists(ver):
        shutil.rmtree(ver)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee, ver], "SmallUnpack")
    at, vt = tree(aaf), tree(ver)
    listed = bm_leaf.verify_manifest(aaf)
    packed_diff = sorted(p for p in at if p != "@files.xml" and p not in listed["unlisted"] and vt.get(p) != at[p])
    if packed_diff:
        raise SystemExit(f"packed .ee differs from the tree: {packed_diff[:5]}")
    vanilla_toc = eetoc.read_toc(vfs(DIR + OLD + ".ee.toc"))
    vanilla_ee = vfs(DIR + OLD + ".ee")
    vtree = {n for n, _, _ in eetoc.sarc_dir(eetoc.unaaf(vanilla_ee))}
    eetoc._VANILLA_UNLISTED.update(vtree - {n for n, _, _ in vanilla_toc})
    # Base .toc = the lineage's newest packed .toc (bm-007, from bm-005), NOT the vanilla one: the
    # lineage already internalised land_global/land_engine (test-061, MODLOG 3158/3966) and the parts
    # and health modules; starting from vanilla silently dropped two of them (caught 2026-10-31).
    lineage_toc = eetoc.read_toc(open(os.path.join(B("bm-007"), OLD + ".ee.toc"), "rb").read())
    renamed = [(n.replace(OLD, NEW), o, s) for n, o, s in lineage_toc]
    # Safety net (R8): any offset-0 record whose bytes differ from the VANILLA .ee would be ignored by
    # the game; make it internal - except the size-only shared references @files.xml declares (stubs).
    van = {n: (o, s) for n, o, s in eetoc.sarc_dir(eetoc.unaaf(vanilla_ee))}
    vs = eetoc.unaaf(vanilla_ee)
    stubs = set(listed["dangling"])
    rc_dir = {n: (o, s) for n, o, s in eetoc.sarc_dir(eetoc.unaaf(open(ee, "rb").read()))}
    rs = eetoc.unaaf(open(ee, "rb").read())
    def differs(n):
        vn = n.replace(NEW, OLD)
        if n not in rc_dir:
            return False
        if vn not in van:
            return True
        (o1, s1), (o2, s2) = rc_dir[n], van[vn]
        return rs[o1:o1 + s1] != vs[o2:o2 + s2]
    changed = sorted(n for n in rc_dir if differs(n))
    internal = sorted(n for n, o, _ in renamed if o == 0 and n not in stubs and differs(n))
    ents = eetoc.patch_toc(open(ee, "rb").read(), renamed, internal, include_lod=True)
    with open(ee + ".toc", "wb") as f:
        for n, o, s in ents:
            nb = n.encode() + b"\0"
            nb += b"\0" * ((4 - len(nb) % 4) % 4) if False else b""
            f.write(len(nb).to_bytes(4, "little") + nb + o.to_bytes(4, "little") + s.to_bytes(4, "little"))
    back = eetoc.read_toc(open(ee + ".toc", "rb").read())
    if back != ents:
        raise SystemExit(".toc does not re-read to what was written")
    toc_info = {"records": len(ents), "internal": internal, "last": ents[-1][0],
                "offset0_left": sum(1 for _, o, _ in ents if o == 0),
                "changed_vs_vanilla": len(changed)}

    # 6. the rest of the dropzone
    for p in ("profile/item.onlinec", "profile/task.onlinec", "profile/online.stringlookup",
              "settings/spawn_vehicle_defs.bin",
              bm_leaf.DIR.split("editor/")[0] + "textures/ui/vehicle_icons/" + NEW + ".ddsc"):
        src = os.path.join(B("bm-013"), "drop", p)
        os.makedirs(os.path.dirname(os.path.join(drop, p)), exist_ok=True)
        shutil.copy(src, os.path.join(drop, p))
    for bank in ("vehicles.bank", "weapons.bank"):
        dst = os.path.join(drop, "sound", "fmod_banks", bank)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(B("bm-004"), "banks", bank), dst)
    owner_drop = {DROP_EE: "B-01..B-13b (merged)", DROP_EE + ".toc": "B-14",
                  "profile/item.onlinec": "B-13", "profile/task.onlinec": "B-13",
                  "profile/online.stringlookup": "B-13", "settings/spawn_vehicle_defs.bin": "B-13c",
                  "textures/ui/vehicle_icons/" + NEW + ".ddsc": "B-13",
                  "sound/fmod_banks/vehicles.bank": "B-11", "sound/fmod_banks/weapons.bank": "B-11"}
    files = []
    for dp, _, fs in os.walk(drop):
        for n in fs:
            p = os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/")
            files.append({"path": p, "bytes": os.path.getsize(os.path.join(dp, n)),
                          "sha256": sha(os.path.join(dp, n)), "owner_card": owner_drop.get(p, "?")})
    files.sort(key=lambda f: f["path"])
    if any(f["owner_card"] == "?" for f in files):
        raise SystemExit(f"drop files with no owner: {[f['path'] for f in files if f['owner_card'] == '?']}")
    aaf_files = [{"path": p, "sha256": h, "owner_card": owners.get(p, "base (bm-005 lineage)")}
                 for p, h in sorted(at.items())]

    rec = {"schema": 2, "card": "B-14", "tag": TAG, "variants": "one tree (D-2 = one hybrid car)",
           "deps": deps, "steps": steps, "b18": b18, "leaf": NEW, "files": files,
           "aaf": {"files": len(aaf_files), "list": aaf_files,
                   "manifest_gaps_inherited": listed},
           "toc": toc_info,
           "budgets": {"model": bud, "texture_resident_kb": round(sum(s for n, o, s in ents if o and n.endswith(".ddsc")) / 1024, 1),
                       "texture_cap_kb": 7065.0},
           "budgets_note": "model = non-vanilla meshes reachable from the parts module (calibrated, bm_budget.py); V-01 re-gates both",
           "replaced_rollback": "Install backs up any dropzone file it would overwrite to <name>.bm-RC1-backup; "
                                "Rollback091 restores those and deletes the files this build added",
           "unknown": ["whether the merged tree loads (phase Q)",
                       "whether the game resolves the NEW leaf from the Rebel Drop hash (Q-1)",
                       "front wheel lod4/5 .rbm are unlisted in @files.xml: unused by design (the wheel .lod never names them)"]}
    json.dump(rec, open(os.path.join(OUT, "receipt.json"), "w"), indent=1)
    open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8-sig").write(installer(files))
    os.makedirs(os.path.join(ROOT, "Working", "RC"), exist_ok=True)
    json.dump({"base": BASE, "branches": BRANCHES, "b10": "Working/Collision/batmobile.physicsc",
               "b11": "Builds/bm-004/banks", "b13": "Builds/bm-013/drop", "b13b": "bm_leaf.rename_tree",
               "owners": owners}, open(os.path.join(ROOT, "Working", "RC", "bm_rc_manifest.json"), "w"), indent=1)
    return rec


def installer(files: list[dict]) -> str:
    rows = "\n".join(f"    @('{f['path'].replace('/', chr(92))}', '{f['sha256'].upper()}')," for f in files).rstrip(",")
    return f"""<#
    {TAG} installer (B-14 release candidate). Generated by Tools/scripts/bm_rc.py, never run by it
    except against a simulated -GameDir under tmp/ (R6).
    -Action Status       what is installed vs this receipt (read-only)
    -Action WhatIf       list every file and what Install would do with it; writes nothing
    -Action Install      back up any dropzone file it replaces to <name>.{TAG}-backup, copy, re-hash
    -Action Verify       re-hash every installed file against the receipt
    -Action Rollback091  restore every backup and remove every file this build added
    Close the game before Install/Rollback091.
#>
[CmdletBinding()]
param([ValidateSet('Status','WhatIf','Install','Verify','Rollback091')][string]$Action = 'Status',
      [string]$GameDir = 'D:\\Games\\Just Cause 3')
$ErrorActionPreference = 'Stop'
$Src = Join-Path $PSScriptRoot 'drop'
$Drop = Join-Path $GameDir 'dropzone'
$Bak = '.{TAG}-backup'
$Files = @(
{rows}
)
function HashOf($p) {{ (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash }}
$n = 0; $bad = 0
foreach ($f in $Files) {{
    $rel = $f[0]; $sha = $f[1]
    $s = Join-Path $Src $rel; $d = Join-Path $Drop $rel; $b = $d + $Bak
    switch ($Action) {{
        'Status' {{
            if (Test-Path -LiteralPath $d) {{ if ((HashOf $d) -eq $sha) {{ $st = 'installed' }} else {{ $st = 'different' }} }} else {{ $st = 'absent' }}
            Write-Output ($st + ' ' + $rel)
        }}
        'WhatIf' {{
            if (Test-Path -LiteralPath $d) {{
                if ((HashOf $d) -eq $sha) {{ $op = 'same' }} else {{ $op = 'replace (backup ' + $rel + $Bak + ')' }}
            }} else {{ $op = 'add' }}
            Write-Output ($rel + ' ' + $sha + ' ' + $op)
        }}
        'Install' {{
            if ((HashOf $s) -ne $sha) {{ throw ('build file does not match the receipt: ' + $rel) }}
            $dir = Split-Path -Parent $d
            if (-not (Test-Path -LiteralPath $dir)) {{ New-Item -ItemType Directory -Force -Path $dir | Out-Null }}
            if ((Test-Path -LiteralPath $d) -and ((HashOf $d) -ne $sha)) {{
                if (Test-Path -LiteralPath $b) {{ throw ('an un-rolled-back backup already guards ' + $rel) }}
                Copy-Item -LiteralPath $d -Destination $b -Force
                Write-Output ('backed up ' + $rel)
            }}
            Copy-Item -LiteralPath $s -Destination $d -Force
            if ((HashOf $d) -ne $sha) {{ throw ('hash mismatch after copy: ' + $rel) }}
            Write-Output ('installed ' + $rel); $n++
        }}
        'Verify' {{
            if ((Test-Path -LiteralPath $d) -and ((HashOf $d) -eq $sha)) {{ Write-Output ('ok ' + $rel); $n++ }}
            else {{ Write-Output ('BAD ' + $rel); $bad++ }}
        }}
        'Rollback091' {{
            if (Test-Path -LiteralPath $b) {{
                Copy-Item -LiteralPath $b -Destination $d -Force; Remove-Item -LiteralPath $b -Force
                Write-Output ('restored ' + $rel)
            }} elseif (Test-Path -LiteralPath $d) {{
                Remove-Item -LiteralPath $d -Force; Write-Output ('removed ' + $rel)
            }}
            $n++
        }}
    }}
}}
if ($Action -eq 'WhatIf') {{ Write-Output ('wrote 0 files, ' + $Files.Count + ' listed') }}
if ($Action -eq 'Verify') {{ Write-Output ('verified ' + $n + '/' + $Files.Count); if ($bad) {{ exit 1 }} }}
if ($Action -eq 'Install') {{ Write-Output ('installed ' + $n + '/' + $Files.Count) }}
"""


def ps(action: str, game: str) -> subprocess.CompletedProcess:
    return subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                           os.path.join(OUT, "install.ps1"), "-Action", action, "-GameDir", game],
                          capture_output=True, text=True, errors="replace")


def check() -> int:
    rec = json.load(open(os.path.join(OUT, "receipt.json")))
    bad = 0
    def ok(c, m):
        nonlocal bad
        print(("PASS " if c else "FAIL ") + m); bad += 0 if c else 1
    drop = os.path.join(OUT, "drop")
    on_disk = sorted(os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/") for dp, _, fs in os.walk(drop) for n in fs)
    ok(on_disk == [f["path"] for f in rec["files"]], f"receipt lists every drop file: {len(rec['files'])} = {len(on_disk)} on disk")
    rh = sum(1 for f in rec["files"] if sha(os.path.join(drop, f["path"])) == f["sha256"])
    ok(rh == len(rec["files"]), f"rehashed {rh}/{len(rec['files'])} ok")
    at = tree(os.path.join(OUT, "aaf"))
    ok(len(at) == rec["aaf"]["files"] and all(at.get(f["path"]) == f["sha256"] for f in rec["aaf"]["list"]),
       f"aaf source tree: {len(at)} files, every sha256 matches")
    ee = os.path.join(drop, DROP_EE)
    real = eetoc.sarc_dir(eetoc.unaaf(open(ee, "rb").read()))
    toc = eetoc.read_toc(open(ee + ".toc", "rb").read())
    R = {n: (o, s) for n, o, s in real}
    moved = [n for n, o, s in toc if o and R.get(n) != (o, s)]
    ok(not moved, f".toc: {len(toc)} records, every non-zero record matches the .ee ({len(real)} entries)")
    ok(toc[-1][0] == DIR + NEW + ".epe", f".toc ends with the root .epe ({toc[-1][0].split('/')[-1]})")
    van_raw = vfs(DIR + OLD + ".ee")
    vs = eetoc.unaaf(van_raw); V = {n: (o, s) for n, o, s in eetoc.sarc_dir(vs)}
    rs = eetoc.unaaf(open(ee, "rb").read())
    stubs = set(rec["aaf"]["manifest_gaps_inherited"]["dangling"])
    ignored = [n for n, o, _ in toc if o == 0 and n not in stubs and n in R and (
        n.replace(NEW, OLD) not in V or rs[R[n][0]:R[n][0] + R[n][1]] !=
        vs[V[n.replace(NEW, OLD)][0]:V[n.replace(NEW, OLD)][0] + V[n.replace(NEW, OLD)][1]])]
    ok(not ignored, f"R8: no offset-0 record carries bytes that differ from the vanilla .ee "
                    f"({len(stubs)} size-only shared references excluded){': ' + str(ignored[:4]) if ignored else ''}")
    for k in ("land_global.vmodc", "land_engine.vmodc", "vehicle_parts.vmodc", "health_medium.vmodc"):
        hit = [(n, o) for n, o, _ in toc if n.endswith(k)]
        ok(hit and all(o for _, o in hit), f"internal (real offset) {k}: {[o for _, o in hit]}")
    ok(all(R.get(n) and o for n, o, _ in toc if n in rec["toc"]["internal"]),
       f"internal records point into the .ee: {len(rec['toc']['internal'])} ({', '.join(x.split('/')[-1] for x in rec['toc']['internal'])})")
    sim = os.path.join(SIM, "clean")
    if os.path.exists(SIM):
        shutil.rmtree(SIM)
    os.makedirs(os.path.join(sim, "dropzone"))
    w = ps("WhatIf", sim)
    lines = [l for l in w.stdout.splitlines() if l and not l.startswith("wrote")]
    listed = [l.split(" ")[0].replace("\\", "/") for l in lines]
    ok(w.returncode == 0 and listed == [f["path"] for f in rec["files"]]
       and [l.split(" ")[1].lower() for l in lines] == [f["sha256"] for f in rec["files"]]
       and not any(os.scandir(os.path.join(sim, "dropzone"))),
       f"-WhatIf lists exactly the receipt's {len(listed)} files + sha256, wrote 0 files")
    r = ps("Install", sim); v = ps("Verify", sim)
    ok(r.returncode == 0 and v.returncode == 0 and f"verified {len(rec['files'])}/{len(rec['files'])}" in v.stdout,
       "rehearsal (a) clean dropzone: Install -> Verify " + (v.stdout.strip().splitlines() or ["?"])[-1])
    rb = ps("Rollback091", sim)
    left = [os.path.join(dp, n) for dp, _, fs in os.walk(os.path.join(sim, "dropzone")) for n in fs]
    ok(rb.returncode == 0 and not left, f"rehearsal (a) Rollback091 removed every added file ({len(left)} left)")
    sim2 = os.path.join(SIM, "decoy")
    decoy = os.path.join(sim2, "dropzone", "profile", "item.onlinec")
    os.makedirs(os.path.dirname(decoy))
    open(decoy, "wb").write(b"decoy vanilla bytes")
    d0 = sha(decoy)
    r = ps("Install", sim2)
    ok(r.returncode == 0 and os.path.exists(decoy + ".bm-RC1-backup") and "backed up profile" in r.stdout.replace("\\", "/"),
       "rehearsal (b) decoy dropzone: Install backed up the existing item.onlinec")
    rb = ps("Rollback091", sim2)
    left = [n for dp, _, fs in os.walk(os.path.join(sim2, "dropzone")) for n in fs]
    ok(rb.returncode == 0 and os.path.exists(decoy) and sha(decoy) == d0 and left == ["item.onlinec"],
       "rehearsal (b) Rollback091 restored the decoy byte-for-byte and removed the rest")
    shutil.rmtree(SIM)
    print(("PASS" if not bad else "FAIL") + f": {TAG} {bad} failure(s), {len(rec['files'])} drop files, "
          f"{rec['aaf']['files']} tree files, .toc {rec['toc']['records']} records")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        rec = build()
        print("\n".join(rec["steps"]))
        print(f"toc {rec['toc']}")
    if a.write or a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
