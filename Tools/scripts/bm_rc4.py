"""bm_rc4.py - B-14: assemble `Builds/bm-RC4` from the bm-RC4-* trees.

Inputs and what each contributes (measured from the trees, not assumed):

  bm-RC4-lights          stage: parts + lights module (688 files, OLD leaf)
  bm-RC4-entity          the .epe (B-05)
  bm-RC4-weapons         7 private .wtunec files + 5 repointed .epe members (own base: entity)
  bm-RC4-effects         the .epe effect attachments (base: parts)
  bm-RC4-damage-collision health module (new private copy), physicsc, custom_land_global
  bm-RC4-handling        5 handling modules; its custom_land_global is the merge base (MODULE_MERGES)
  bm-RC4-rebel           dropzone files (item/task/stringlookup/spawn/icon)
  bm-RC4-audio           the two banks

Every .epe contributor is merged with `git merge-file` on the ConvertProperty XML, exactly as
bm_rc.py did for RC1; the base is the parts tree's .epe. A conflict stops the build. The leaf is
then renamed once (bm_leaf.rename_tree), the tree is packed, the .toc is re-derived, the dropzone
tree and a schema-2 receipt are written, and install.ps1 is rendered from
Working/Installer/install_v3.ps1 (guards kept; simulation root `_dropzone_sim_rc4`).

Nothing is installed and no game is launched.

Usage
    python Tools/scripts/bm_rc4.py --write
    python Tools/scripts/bm_rc4.py --check
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
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_leaf                                    # noqa: E402
import eetoc                                      # noqa: E402
import t5_apply as T5                             # noqa: E402  (offset-anchor module writer)

TAG = "bm-RC4"
OUT = os.path.join(ROOT, "Builds", TAG)
B = lambda t: os.path.join(ROOT, "Builds", t)
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
CONV = os.path.join(GIBBED, "Gibbed.JustCause3.ConvertProperty.exe")
WORK = os.path.join(ROOT, "tmp", "b14")
DIR = bm_leaf.DIR
OLD, NEW = bm_leaf.OLD, bm_leaf.NEW
EPE = DIR + OLD + ".epe"
DROP_EE = DIR + NEW + ".ee"
ROOT_EPE = DIR + NEW + ".epe"
STAGE = "bm-RC4-lights"
E = DIR
PHYS = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc"
CLG = E + "modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc"
HEALTH = E + "batmobile_health_medium.vmodc"
HANDLING = [E + "modules/default/v0300_car_kensington_sportsmuscle_brakes.vmodc",
            E + "modules/default/v0300_car_kensington_sportsmuscle_land_aerodynamics.vmodc",
            E + "modules/default/v0300_car_kensington_sportsmuscle_land_engine.vmodc",
            E + "modules/default/v0300_car_kensington_sportsmuscle_land_global.vmodc",
            E + "modules/default/v0300_car_kensington_sportsmuscle_land_steering.vmodc"]
EPE_BRANCHES = [("bm-RC4-entity", None), ("bm-RC4-weapons", "bm-RC4-entity"),
                ("bm-RC4-effects", None), ("bm-RC4-damage-collision", None)]
DROP_SRC = {"profile/item.onlinec": "bm-RC4-rebel", "profile/task.onlinec": "bm-RC4-rebel",
            "profile/online.stringlookup": "bm-RC4-rebel",
            "settings/spawn_vehicle_defs.bin": "bm-RC4-rebel",
            "textures/ui/vehicle_icons/" + NEW + ".ddsc": "bm-RC4-rebel"}
SIM = r"E:\Modding\_dropzone_sim_rc4"   # install_v3.ps1's guard only accepts this root
INSTALL_V3 = os.path.join(ROOT, "Working", "Installer", "install_v3.ps1")

# Two branches write one binary module. They are member-disjoint: measured, the two branch
# copies are the same 3,399 B / 61-member layout and differ in exactly 7 members (D-08's 2 wheel
# rows + D-10's 5). So neither has to be dropped - the RC starts from D-10's module and writes
# D-08's two rows onto it with `t5_apply`'s offset-anchor writer, which refuses to move any other
# member. Both sets are then read back from the packed `.toc` (build() records it, check()
# re-derives it), so the merge is tested, not asserted.
MERGE_EDITS = [
    {"row": "T-14 ARM-4", "module": CLG, "member": "front_wheels_damage.skew_health",
     "old": 200, "new": 400},
    {"row": "T-14 ARM-4", "module": CLG, "member": "rear_wheels_damage.skew_health",
     "old": 200, "new": 400},
]
MODULE_MERGES = [{
    "path": CLG,
    "branches": ["bm-RC4-damage-collision", "bm-RC4-handling"],
    "base": "bm-RC4-handling",
    "edits": MERGE_EDITS,
    "why": ("D-08 writes front/rear_wheels_damage.skew_health 200 -> 400 here; D-10 writes the "
            "T-B1/T-B4/T-DR1 nitro/heat/drift members in the same module. A .vmodc is binary, so "
            "the two cannot be line-merged - but they are member-disjoint on one 61-member layout, "
            "so the RC carries D-10's module plus the two D-08 writes, and reads both sets back."),
}]

# No module overlap is left unresolved.
CONFLICTS: list[dict] = []
HANDLING_EDITS = os.path.join(ROOT, "Working", "Translation", "t1_handling_edits.json")

# 23 texture rows from D-04; 12 are unfaithful by its own ledger. Recorded, not fixed.
TEXTURE_ROWS = {
    "total": 23, "faithful": 11, "unfaithful": 12,
    "unfaithful_breakdown": {"chapter_masks": 4, "missing_pixel_sets": 8},
    "source": "tmp/freebuff/reports/build-d04-materials-textures.md §3 (D9, D10/D11 rows)",
    "names": (["Batmobile_V3_Body_Damage_ChapterMask", "Batmobile_V3_Wheel_Damage_ChapterMask",
               "Batmobile_V3_Glass_Damage_ChapterMask", "Batmobile_V3_Undercarriage_Damage_ChapterMask"]),
    "note": "4 chapter masks have no chapter selector (damage stays off, SupportDmgBlend 0); 8 rows "
            "name a pixel set the D-04 bake could not supply. The tree is therefore NOT complete.",
}


def sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tree(aaf: str) -> dict[str, str]:
    return {os.path.relpath(os.path.join(dp, n), aaf).replace("\\", "/"): sha(os.path.join(dp, n))
            for dp, _, fs in os.walk(aaf) for n in fs}


def clg_edits() -> list[dict]:
    """D-10's CustomLandGlobal rows, read from the edit list its own build applies."""
    return [e for e in json.load(open(HANDLING_EDITS, encoding="utf-8"))["edits"]
            if e["module"] == "CustomLandGlobal"]


def read_module(raw: bytes, toc: list, basename: str, want: list) -> dict:
    """Read named members out of a packed module, through the `.toc` - never from `aaf`.

    Same path `b10_handling.py` uses: the `.toc` record gives (offset, size) into the
    decompressed `.ee` stream, that slice is decoded with ConvertAdf, and each member compared.
    """
    hits = [(n, o, s) for n, o, s in toc if n.endswith("/" + basename)]
    if len(hits) != 1:
        raise SystemExit(f"{basename}: {len(hits)} .toc records (a module the .toc does not "
                         f"carry cannot be read back)")
    name, off, size = hits[0]
    if not off:
        raise SystemExit(f"{name}: offset 0 in the .toc (external, not in this .ee)")
    stream = eetoc.unaaf(raw)
    if size > len(stream) - off:
        raise SystemExit(f"{name}: .toc size {size} overruns the stream")
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, basename)
        open(p, "wb").write(stream[off:off + size])
        xml = p + ".xml"
        T5.decode(p, xml)
        with open(xml, encoding="utf-8-sig") as f:
            inst = ET.fromstring(f.read()).find("instances/instance")
        if inst is None:
            raise SystemExit(f"{name}: no instance in the packed module")
        table = T5.paths(inst)
    got: dict[str, str | None] = {}
    bad: list[str] = []
    for member, val in want:
        el = table.get(member)
        text = (el.text or "").strip() if el is not None else None
        got[member] = text
        if el is None:
            bad.append(f"{member}: absent")
            continue
        kind = el.get("type") or ""
        if kind.startswith("int") or kind.startswith("uint"):
            same_v = int(text) == int(val)
        else:
            same_v = abs(float(text) - float(val)) <= 1e-4 * max(1.0, abs(float(val)))
        if not same_v:
            bad.append(f"{member}: {text} != {val}")
    return {"file": name, "offset": off, "size": size, "checked": len(want),
            "members": got, "ok": not bad, "mismatches": bad}


def aafdiff_class(at: dict, rc2: dict, base: dict, stage_t: dict, owners: dict) -> dict:
    """Why every file differs from bm-RC2, one class per file; `unexplained` must stay empty.

    The RC carries three kinds of difference, and the diff must list exactly their union:
      merge-overlay  a file this B-14 merge wrote (the `owners` map)
      stage          a file the base already rebuilt (parts split / lights module), taken from
                     the stage tree - e.g. the 24-row lights module
      base-lineage   a file `bm-RC4-base` already changed or added relative to RC2 (appearance
                     meshes/textures, the mshswap wheels, the extra handling modules)
    """
    out = {}
    for p in sorted(set(at) | set(rc2)):
        if at.get(p) == rc2.get(p):
            continue
        if p in owners:
            out[p] = "merge-overlay"
        elif p in stage_t and stage_t[p] == at.get(p) and base.get(p) != stage_t[p]:
            out[p] = "stage"
        elif p not in rc2 or base.get(p) != rc2.get(p):
            out[p] = "base-lineage"
        else:
            out[p] = "unexplained"
    return out


def run(args, what):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"{what} failed (rc {r.returncode}): {(r.stdout + r.stderr)[-800:]}")
    return r


def merge3(base: str, branches: list, out: str) -> dict:
    import difflib
    os.makedirs(WORK, exist_ok=True)
    cur = os.path.join(WORK, "merge_cur")
    shutil.copy(base, cur)
    pairs = [b if isinstance(b, tuple) else (b, base) for b in branches]
    for br, bb in pairs:
        r = subprocess.run(["git", "merge-file", "-p", cur, bb, br], capture_output=True)
        if r.returncode != 0:
            raise SystemExit(f"3-way .epe merge conflict (rc {r.returncode}) merging {br}")
        open(cur, "wb").write(r.stdout)
    shutil.copy(cur, out)
    res = open(out, encoding="utf-8-sig", errors="replace").read().splitlines()
    rs = set(res)
    diffs = []
    for br, bb in pairs:
        diffs.append(difflib.unified_diff(open(bb, encoding="utf-8-sig", errors="replace").read().splitlines(),
                                          open(br, encoding="utf-8-sig", errors="replace").read().splitlines(),
                                          n=0))
    missing, superseded = [], 0
    for i, (d, (br, _bb)) in enumerate(zip(diffs, pairs)):
        # a line a LATER branch removes from its own base is superseded, not lost (the weapons
        # branch repoints the same five members B-05 wrote, so B-05's line cannot survive)
        later_removed = {l[1:] for d2 in diffs[i + 1:] for l in d2
                         if l.startswith("-") and not l.startswith("---")}
        for l in d:
            if l.startswith("+") and not l.startswith("+++") and l[1:] not in rs:
                if l[1:] in later_removed:
                    superseded += 1
                else:
                    missing.append((os.path.basename(br), l[1:][:110]))
    if missing:
        raise SystemExit(f"merged .epe lost branch lines: {missing[:5]}")
    if superseded:
        print(f"  {superseded} earlier line(s) superseded by a later branch")
    return {"base_lines": sum(1 for _ in open(base, encoding="utf-8-sig", errors="replace")),
            "merged_lines": len(res)}


def build() -> dict:
    steps, owners = [], {}
    stage = os.path.join(WORK, "stage")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(WORK, exist_ok=True)
    shutil.copytree(B(STAGE) + "/aaf", stage)
    steps.append(f"stage = {STAGE}/aaf (parts split + lights module, 688 files)")

    # 1. the .epe: one 3-way merge of every graph contributor onto the parts tree's graph
    xs = []
    for t, own in EPE_BRANCHES:
        x = os.path.join(WORK, f"{t}.xml")
        run([CONV, "--e", os.path.join(B(t), "aaf", EPE), x], f"ConvertProperty --e {t}")
        xs.append((x, own))
    base_x = os.path.join(WORK, "base.xml")
    run([CONV, "--e", os.path.join(B(STAGE), "aaf", EPE), base_x], "ConvertProperty --e base")
    branches = []
    for x, own in xs:
        if own:
            ox = os.path.join(WORK, f"{own}.xml")
            branches.append((x, ox))
        else:
            branches.append(x)
    m = merge3(base_x, branches, os.path.join(WORK, "merged.xml"))
    run([CONV, "-i", os.path.join(WORK, "merged.xml"), os.path.join(stage, EPE)], "ConvertProperty -i")
    run([CONV, "--e", os.path.join(stage, EPE), os.path.join(WORK, "rt.xml")], "ConvertProperty rt")
    if open(os.path.join(WORK, "merged.xml"), encoding="utf-8").read() != \
            open(os.path.join(WORK, "rt.xml"), encoding="utf-8").read():
        raise SystemExit("the merged .epe does not round-trip to the merged XML")
    owners[EPE] = "+".join(t for t, _ in EPE_BRANCHES)
    steps.append(f"3-way .epe merge of {[t for t, _ in EPE_BRANCHES]} onto the parts graph: "
                 f"{m['base_lines']} -> {m['merged_lines']} XML lines, round trip identical")

    # 2. module overlays
    for t, paths, card in (("bm-RC4-damage-collision", [HEALTH, PHYS], "D-08"),
                           ("bm-RC4-handling", HANDLING, "D-10")):
        for p in paths:
            src, dst = os.path.join(B(t), "aaf", p), os.path.join(stage, p)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
            owners[p] = card
    # 2b. the overlapping binary module: D-10's copy, then D-08's two rows written on top.
    # `apply_file` asserts each `old` before writing and that no untouched member moves.
    merged: dict[str, dict] = {}
    for mg in MODULE_MERGES:
        dst = os.path.join(stage, mg["path"])
        shutil.copy(os.path.join(B(mg["base"]), "aaf", mg["path"]), dst)
        applied = T5.apply_file(dst, mg["edits"], False)
        merged[mg["path"]] = {
            "path": mg["path"],
            "branches": mg["branches"], "base": mg["base"], "why": mg["why"],
            "sources": {t: sha(os.path.join(B(t), "aaf", mg["path"])) for t in mg["branches"]},
            "edits": applied, "merged_sha256": sha(dst), "bytes": os.path.getsize(dst),
        }
        owners[mg["path"]] = mg["base"] + "+D-08 merge"
    steps.append(f"modules: health + physicsc (D-08), {len(HANDLING)} handling modules (D-10); "
                 f"{sum(len(m['edits']) for m in merged.values())} row(s) merged onto "
                 f"{len(merged)} overlapping module(s), {len(CONFLICTS)} conflict(s) left")

    # 3. weapons' private tunes (their .epe repoints came through the merge)
    wt = 0
    for dp, _, fs in os.walk(os.path.join(B("bm-RC4-weapons"), "aaf")):
        for n in fs:
            if not n.endswith(".wtunec"):
                continue
            p = os.path.relpath(os.path.join(dp, n), os.path.join(B("bm-RC4-weapons"), "aaf")).replace("\\", "/")
            src = os.path.join(B("bm-RC4-weapons"), "aaf", p)
            if os.path.exists(os.path.join(B(STAGE), "aaf", p)) and \
                    sha(src) == sha(os.path.join(B(STAGE), "aaf", p)):
                continue
            dst = os.path.join(stage, p)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
            owners[p] = "B-06"
            wt += 1
    steps.append(f"weapons: {wt} private .wtunec file(s) overlaid")

    # 3c. @files.xml registration: SmallPack packs only what the manifest lists (deploy.py
    # step 2, MODLOG 103a). The overlays above add files the stage manifest never carried - the
    # D-08 private `batmobile_health_medium.vmodc` and the weapons' private `.wtunec` files -
    # so without this they are silently dropped from the packed .ee.
    from deploy import add_to_manifest
    missing = bm_leaf.verify_manifest(stage)["unlisted"]
    n_reg = add_to_manifest(stage, missing) if missing else 0
    for p in missing:
        owners.setdefault(p, "B-09/B-06 private copy")
    steps.append(f"@files.xml: registered {n_reg} overlay file(s) SmallPack would have dropped")

    # 4. leaf rename
    aaf = os.path.join(OUT, "aaf")
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    leaf = bm_leaf.rename_tree(stage, aaf)
    for k in list(owners):
        if OLD in k:
            owners[k.replace(OLD, NEW)] = owners.pop(k) + "+B-13b"
    owners["@files.xml"] = owners.get("@files.xml", "base") + "+B-13b"
    for e in bm_leaf.INNER:
        owners.setdefault(DIR + NEW + e, "B-13b")
    steps.append(f"leaf {NEW} (epe root {leaf['epe_after']}); {len(bm_leaf.INNER)} inner files")

    # 5. B-15 budget: trim the far LODs, then measure (R9)
    import bm_budget
    bud = bm_budget.trim(aaf)
    for c in bud["lods_changed"]:
        owners[c["lod"]] = "B-15"
    steps.append(f"R9 model: non-vanilla {bud['before']['non_vanilla_kb']} -> "
                 f"{bud['after']['non_vanilla_kb']} KB of {bud['cap_kb']} "
                 f"({len(bud['lods_changed'])} .lod trimmed)")

    # 6. pack + .toc
    drop = os.path.join(OUT, "drop")
    ee = os.path.join(drop, DROP_EE)
    os.makedirs(os.path.dirname(ee))
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee], "SmallPack")
    ver = os.path.join(WORK, "verify")
    shutil.rmtree(ver, ignore_errors=True)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee, ver], "SmallUnpack")
    at, vt = tree(aaf), tree(ver)
    listed = bm_leaf.verify_manifest(aaf)
    packed_diff = sorted(p for p in at if p != "@files.xml"
                         and p not in listed["unlisted"] and vt.get(p) != at[p])
    if packed_diff:
        raise SystemExit(f"packed .ee differs from the tree: {packed_diff[:5]}")
    p_ee = os.path.join(B(STAGE), OLD + ".ee")          # the tree keeps its .ee at its root
    p_toc = eetoc.read_toc(open(p_ee + ".toc", "rb").read())
    renamed = [(n.replace(OLD, NEW), o, s) for n, o, s in p_toc]
    raw = open(ee, "rb").read()
    rs = eetoc.unaaf(raw)
    R = {n: (o, s) for n, o, s in eetoc.sarc_dir(rs)}
    # R8 safety net (bm_rc.py's rule): offset 0 means "load from the archives" (test-023), so
    # every record whose bytes differ from the VANILLA donor .ee must point into this .ee.
    # Computed from bytes, never listed by hand; @files.xml's size-only stubs stay external.
    import bm_rc
    vs = eetoc.unaaf(bm_rc.vfs(DIR + OLD + ".ee"))
    V = {n: (o, s) for n, o, s in eetoc.sarc_dir(vs)}
    stubs = set(listed["dangling"])

    def differs(n):
        if n not in R:
            return False
        vn = n.replace(NEW, OLD)
        if vn not in V:
            return True
        (o1, s1), (o2, s2) = R[n], V[vn]
        return rs[o1:o1 + s1] != vs[o2:o2 + s2]

    changed = sorted(n for n in R if differs(n))
    internal = sorted(n for n, o, _ in renamed if o == 0 and n not in stubs and n in R and differs(n))
    ents = eetoc.patch_toc(raw, renamed, internal=internal, include_lod=True)
    with open(ee + ".toc", "wb") as f:
        f.write(eetoc.write_toc(ents))
    if eetoc.read_toc(open(ee + ".toc", "rb").read()) != ents:
        raise SystemExit(".toc does not re-read to what was written")
    toc_info = {"records": len(ents), "last": ents[-1][0],
                "offset0_left": sum(1 for _, o, _ in ents if o == 0),
                "changed_vs_vanilla": len(changed), "internal": internal}
    for p in (DIR + NEW + ".epe", PHYS):
        got = R.get(p)
        if not got or not got[0]:
            raise SystemExit(f"{p} has no internal .toc record")
    toc_info.update({"physicsc": list(R[PHYS]), "epe": list(R[DIR + NEW + ".epe"]),
                     "internal_modules": [list(R[q]) for q in
                                          (HEALTH.replace(DIR, DIR),)] if HEALTH in R else []})
    steps.append(f"packed {os.path.basename(ee)} ({os.path.getsize(ee):,} B), "
                 f"{len(at) - len(listed['unlisted'])} listed files round-trip, .toc {len(ents)} records")
    # 6b. the merged module, read back through the packed .toc: both branches' rows must be there.
    for mg in merged.values():
        mg["read_back"] = read_module(raw, ents, mg["path"].rsplit("/", 1)[-1],
                                      [(e["member"], e["new"]) for e in mg["edits"]]
                                      + [(e["member"], e["new"]) for e in clg_edits()])
        if not mg["read_back"]["ok"]:
            raise SystemExit(f"module merge read-back mismatch: {mg['read_back']['mismatches']}")
    steps.append("module merge read back from the packed .toc: "
                 + "; ".join(f"{m['read_back']['checked']} member(s) at "
                             f"{m['read_back']['file']}" for m in merged.values()))

    # 7. the rest of the dropzone
    for p, t in DROP_SRC.items():
        s = os.path.join(B(t), "drop", p)
        d = os.path.join(drop, p)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(s, d)
    banks = []
    ad = os.path.join(B("bm-RC4-audio"), "banks")     # the bank build keeps them here
    for n in sorted(os.listdir(ad)) if os.path.isdir(ad) else []:
        if n.endswith(".bank"):
            p = "sound/fmod_banks/" + n
            d = os.path.join(drop, p)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy(os.path.join(ad, n), d)
            banks.append(p)
    owner_drop = {DROP_EE: "B-01..B-13b merged", DROP_EE + ".toc": "B-14",
                  "profile/item.onlinec": "B-13", "profile/task.onlinec": "B-13",
                  "profile/online.stringlookup": "B-13",
                  "settings/spawn_vehicle_defs.bin": "B-13c",
                  "textures/ui/vehicle_icons/" + NEW + ".ddsc": "B-13"}
    for p in banks:
        owner_drop[p] = "B-11"
    files = []
    for dp, _, fs in os.walk(drop):
        for n in fs:
            p = os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/")
            files.append({"path": p, "bytes": os.path.getsize(os.path.join(dp, n)),
                          "sha256": sha(os.path.join(dp, n)), "owner_card": owner_drop.get(p, "?")})
    files.sort(key=lambda f: f["path"])
    if any(f["owner_card"] == "?" for f in files):
        raise SystemExit(f"drop files with no owner: {[f['path'] for f in files if f['owner_card'] == '?']}")

    tex_bud = json.load(open(os.path.join(B("bm-RC4-appearance"), "budget.json")))

    # 8. aafdiff vs RC2: exactly the planned files
    rc2 = tree(os.path.join(B("bm-RC2"), "aaf"))
    base = tree(os.path.join(B("bm-RC4-base"), "aaf"))
    stage_t = tree(os.path.join(B(STAGE), "aaf"))
    vs_base = sorted(p for p in at if base.get(p) != at[p])
    kinds = aafdiff_class(at, rc2, base, stage_t, owners)
    vs_rc2 = sorted(kinds)
    extra = sorted(p for p, k in kinds.items() if k == "unexplained")
    planned = list(vs_rc2)
    af_out = os.path.join(OUT, "verify", "aafdiff_rc2.md")
    os.makedirs(os.path.dirname(af_out), exist_ok=True)
    run([sys.executable, os.path.join(HERE, "aafdiff.py"), os.path.join(B("bm-RC2"), "aaf"),
         aaf, "--hash", "--out", af_out], "aafdiff vs bm-RC2")
    if extra:
        raise SystemExit(f"aafdiff vs bm-RC2 has {len(extra)} unexplained file(s): {extra[:5]}")
    steps.append(f"aafdiff vs bm-RC2: {len(vs_rc2)} file(s) differ = the planned set "
                 f"({sum(1 for k in kinds.values() if k == 'merge-overlay')} merge overlays, "
                 f"{sum(1 for k in kinds.values() if k == 'stage')} stage rebuilds, "
                 f"{sum(1 for k in kinds.values() if k == 'base-lineage')} RC4 base lineage), 0 unplanned")

    # 9. cards and batch bookkeeping this RC is built against (review 8299)
    dc = json.load(open(os.path.join(B("bm-RC4-damage-collision"), "receipt.json")))
    coll = dc["collision"]
    if "2 bodies / 3 boxes / 1 constraint" not in coll.get("bmak_asset", ""):
        raise SystemExit("B-10 reopened: the collision receipt no longer names 2 bodies / 3 boxes / "
                         "1 constraint")
    dev_box = max(abs(float(x)) for x in coll["dev_vs_chassis_box_m"])
    size_dev = max(abs(float(a) - float(b)) for a, b in
                   zip(coll["body_hull_box_m"]["size"], coll["bmak_chassis_box0_m"]["size"]))
    if size_dev > 0.05:
        raise SystemExit(f"B-10 Done gate: the body hull's SHAPE deviates {size_dev} m from chassis "
                         f"box 0 (> 5 cm)")
    phys_sha = sha(os.path.join(aaf, PHYS))
    if phys_sha != coll["sha256"].lower():
        raise SystemExit("B-10: the packed physicsc is not the file the collision receipt recorded")
    # The card's gate is positional ("shape union within 5 cm of the two chassis boxes"). Since
    # correction 8390 the hull bottom is BmAK's own box floor (0.030 m, decoded from the box TM),
    # not DIM-1's ground line, so both shape and placement are measured on the rebuilt bytes.
    dev_axis = max(range(3), key=lambda i: abs(float(coll["dev_vs_chassis_box_m"][i])))
    b10_gate = {"chassis_box": "Physics.Batmobile_V3_Physics box 0, 690.305 x 374.536 x 207.5 cm",
                "hull_size_dev_m": size_dev, "placement_dev_m": coll["dev_vs_chassis_box_m"],
                "limit_m": 0.05, "pass": size_dev <= 0.05 and dev_box <= 0.05}
    if b10_gate["pass"]:
        b10_gate["reason"] = (
            f"the hull is chassis box 0's decoded shape and sits on the box's own floor: size dev "
            f"{size_dev * 100:.2f} cm, placement dev {dev_box * 100:.2f} cm on "
            f"{'xyz'[dev_axis]} (limit 5 cm), both re-measured on the rebuilt bytes")
    else:
        b10_gate["reason"] = (
            f"hull shape dev {size_dev * 100:.2f} cm / placement dev {dev_box * 100:.2f} cm on "
            f"{'xyz'[dev_axis]} vs the 5 cm gate")
        b10_gate["not_carried"] = f"chassis-box {'shape' if size_dev > 0.05 else 'placement'}"
    steps.append(f"B-10 reopened: hull shape = chassis box 0 (size dev {size_dev * 100:.2f} cm), "
                 f"placement dev {dev_box * 100:.2f} cm vs the 5 cm gate -> "
                 f"{'PASS' if b10_gate['pass'] else 'NOT MET (recorded; B-10 stays not-done)'}")
    # The card's Done rule asks for a shape union over the TWO chassis boxes plus the pod. One box
    # is carried, so the shapes clause is recorded met=false next to the passing box-0 clause.
    b10_gate["boxes_carried"] = 1
    b10_gate["boxes_decoded"] = 3
    b10_gate["shapes_pass"] = False
    b10_gate["shapes_reason"] = (
        f"chassis box 1 and the weapons-pod box have no hull shape instance: "
        f"{coll['shapes_missing']} of 3 boxes missing, {coll['free_hull_slots']} free hull slots "
        f"({coll['donor_bodies']} donor bodies over 54 hull objects)")
    steps.append(f"B-10 shapes: {b10_gate['boxes_carried']}/{b10_gate['boxes_decoded']} BmAK boxes "
                 f"carried (named capability gap, TMs recorded in the receipt)")
    # The two BmAK boxes with no JC3 shape instance, and the one constraint, stay named gaps with
    # the decoded TMs - not silently dropped, and not bent into a slot that does not exist.
    hull2 = json.load(open(os.path.join(ROOT, "Working", "Collision2", "bm_vehicle_hull.json"),
                           encoding="utf-8"))
    tms = {f"{t['export']}.{t['box']}": t for t in hull2["box_tms"]}

    def _gap(key: str, what: str) -> dict:
        t = tms[key]
        return {"what": what, "export": t["export"], "bone": t["bone"], "box": t["box"],
                "translation_cm": t["translation_cm"], "extents_cm": t["extents_cm"],
                "rows": t["rows"], "rotation_deg_about_y": t["rotation_deg_about_y"],
                "evidence": ("Working/Collision2/bm_vehicle_hull.json box_tms "
                             f"(export {t['export']} box {t['box']}, tm_at {t['tm_at']})"),
                "why_not_carried": (f"no free hull slot: {coll['free_hull_slots']} free slots, "
                                    f"{coll['donor_bodies']} donor bodies over 54 hull objects; "
                                    "G2-30 proved scale/translate of an existing hull, not a new "
                                    "shape")}

    capability_gaps = [_gap("169750.1", "BmAK chassis box 1 has no hull shape instance"),
                       _gap("169751.0", "BmAK weapons-pod box has no hull shape instance")]
    capability_gaps.append({
        "what": "BmAK's 1 constraint has no JC3 writer", "export": 171462,
        "evidence": coll["constraint"],
        "why_not_carried": ("capability gap: no RB_ConstraintSetup layout in BMSDK_OFFSETS.json, so "
                            "the constraint cannot be serialised")})
    bt = open(os.path.join(ROOT, "Working", "Translation", "BUILD_BATCHES.md"),
              encoding="utf-8").read().splitlines()
    brow = [l for l in bt if re.match(r"\| B-\d\d · ", l)]
    bstep = [re.match(r"\| (B-\d\d) · ", l).group(1) for l in brow]
    bcells = {re.match(r"\| (B-\d\d) · ", l).group(1): [c.strip() for c in l.strip("|").split("|")]
              for l in brow}
    no_payload = [s for s in ("B-17", "B-18", "B-19", "B-20")
                  if bcells.get(s, ["", "", ""])[2].startswith("-")]
    if len(bstep) != 24 or len(no_payload) != 4:
        raise SystemExit(f"BUILD_BATCHES: {len(bstep)} steps (expect 24), B-17..B-20 declared "
                         f"no-payload: {no_payload}")
    backlog = open(os.path.join(ROOT, "GRAB_BACKLOG.md"), encoding="utf-8").read()
    cards = [c for c in ("B-25", "B-26") if f"#### {c} ·" in backlog]
    if len(cards) != 2:
        raise SystemExit(f"B-25/B-26 cards missing from GRAB_BACKLOG section 8: {cards}")
    steps.append(f"B-10 reopened collision carried ({coll['bmak_asset']}, max chassis-box dev "
                 f"{dev_box * 100:.1f} cm <= 5 cm); B-25/B-26 are cards with no payload here; "
                 f"BUILD_BATCHES {len(bstep)} steps, no-payload {no_payload}")

    not_done = ["12 of 23 texture rows are unfaithful (4 chapter masks + 8 missing pixel sets): "
                "the tree is NOT complete",
                "B-12/D-2 modes: this RC is the pursuit set only. The pursuit/battle pair is built "
                "as a separate, unmerged payload in Builds/bm-RC4-modes (aafdiff = the 2 planned "
                "files); 0 rows are carried exactly, 2 are composed (T-MD5, T-MD6), 2 ride the same "
                "unbuilt switch (T-MD10, T-MD11) and 4 are not built (T-MD7, T-MD13, T-MD8, T-MD14)",
                "B-17..B-20 are declared no-payload in BUILD_BATCHES and ship no payload in this RC",
                "B-25 and B-26 are cards only; neither has a payload in this RC",
                "runtime load, Rebel Drop resolution and the Q takes are untested"]
    if not b10_gate["pass"]:
        not_done.insert(0, f"B-10 chassis-box gate NOT met: {b10_gate['reason']} "
                            f"({dev_box * 100:.1f} cm > 5 cm)")
    not_done.insert(1, f"B-10 shape set is incomplete: 1 of 3 BmAK boxes carried - "
                        f"{b10_gate['shapes_reason']}")
    rec = {"schema": 2, "card": "B-14", "tag": TAG, "leaf": NEW, "base": f"Builds/{STAGE}",
           "complete": False,
           "steps": steps,
           "conflicts": CONFLICTS,
           "module_merges": list(merged.values()),
           "texture_rows": TEXTURE_ROWS,
           "files": files,
           "aaf": {"files": len(at), "list": [{"path": p, "sha256": h,
                                              "owner_card": owners.get(p, "base (RC4 lineage)")}
                                             for p, h in sorted(at.items())],
                   "manifest_gaps_inherited": listed},
           "toc": toc_info,
           "budgets": {"model": bud, "model_cap_kb": 4915.0, "texture_cap_kb": 7065.0,
                       "texture_used_kb": tex_bud["tree_kb"],
                       "texture_used_note": (f"Builds/bm-RC4-appearance/budget.json: "
                                             f"{tex_bud['tree_textures']} textures, "
                                             f"{tex_bud['tree_kb']} KB, hard_ok "
                                             f"{tex_bud['hard_ok']}; allocator "
                                             f"{tex_bud['allocator_kb']} KB is "
                                             f"{'ok' if tex_bud['allocator_ok'] else 'OVER'} "
                                             f"(reported by D-04)")},
           "aafdiff_rc2": {"differ": len(vs_rc2), "planned": len(planned),
                           "unplanned": extra[:20], "planned_list": planned,
                           "by_class": {k: sorted(p for p, q in kinds.items() if q == k)
                                        for k in sorted(set(kinds.values()))},
                           "report": os.path.relpath(af_out, ROOT).replace("\\", "/")},
           "collision": {"card": "B-10 (reopened 2026-11-07)", "source": coll["source"],
                         "bmak_asset": coll["bmak_asset"], "hulls_written": coll["hulls_written"],
                         "donor_bodies": coll["donor_bodies"],
                         "shapes_missing": coll["shapes_missing"],
                         "free_hull_slots": coll["free_hull_slots"],
                         "dev_vs_chassis_box_m": coll["dev_vs_chassis_box_m"],
                         "dev_vs_render_bbox_m": coll["dev_vs_render_bbox_m"],
                         "constraint": coll["constraint"], "physicsc_sha256": phys_sha,
                         "capability_gaps": capability_gaps,
                         "toc_record": list(R[PHYS]), "gate": b10_gate},
           "build_batches": {"steps": len(bstep), "b17_b20_no_payload": no_payload,
                             "source": "Working/Translation/BUILD_BATCHES.md"},
           "modes": {
               "rc_set": "pursuit",
               "merged_into_rc": False,
               "built_trees": ["Builds/bm-RC4-modes/pursuit", "Builds/bm-RC4-modes/battle"],
               "aafdiff_planned_files": 2,
               "rows_exact": 0,
               "rows_composed": ["T-MD5", "T-MD6"],
               "rows_same_switch": ["T-MD10", "T-MD11"],
               "rows_not_built": ["T-MD7", "T-MD13", "T-MD8", "T-MD14"],
               "note": ("the pair is built but unmerged; the RC .ee is the pursuit/base tree, and "
                        "merging the second entity needs a runtime swap that is UNKNOWN")},
           "cards_without_payload": {"B-12": "pair built separately and unmerged in "
                                             "Builds/bm-RC4-modes; 0 exact rows, 4 not built; "
                                             "no payload in this RC",
                                     "B-17": "declared no-payload in BUILD_BATCHES section 4; "
                                             "no payload in this RC",
                                     "B-18": "declared no-payload in BUILD_BATCHES section 4; "
                                             "no payload in this RC",
                                     "B-19": "declared no-payload in BUILD_BATCHES section 4; "
                                             "no payload in this RC",
                                     "B-20": "declared no-payload in BUILD_BATCHES section 4; "
                                             "no payload in this RC",
                                     "B-25": "card in GRAB_BACKLOG section 8; no payload in this "
                                             "RC (lens flares + light units)",
                                     "B-26": "card in GRAB_BACKLOG section 8; no payload in this "
                                             "RC (per-entity audio override)"},
           "banks_included": banks,
           "not_done": not_done,
           "installed": False, "not_deployed": True}
    def _json_safe(o):
        """A receipt is JSON: no raw control character may survive inside a string."""
        ctrl = {chr(9), chr(10), chr(13)}
        if isinstance(o, dict):
            return {_json_safe(k): _json_safe(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_json_safe(v) for v in o]
        if isinstance(o, str):
            return "".join(c if 0x20 <= ord(c) <= 0xD7FF or c in ctrl else "?" for c in o)
        return o
    rec = _json_safe(rec)

    json.dump(rec, open(os.path.join(OUT, "receipt.json"), "w", encoding="utf-8"), indent=1)
    open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8-sig").write(installer(files))
    os.makedirs(os.path.join(ROOT, "Working", "RC"), exist_ok=True)
    json.dump({"tag": TAG, "stage": STAGE, "conflicts": CONFLICTS, "owners": owners},
              open(os.path.join(ROOT, "Working", "RC", "bm_rc_manifest_bm-RC4.json"), "w"), indent=1)
    return rec


def installer(files: list[dict]) -> str:
    """install_v3.ps1's guards, adopted: sim-root containment, per-target containment, fail-closed
    REFUSED/exit 2, snapshot-and-restore rollback. Rewritten here rather than string-mutated, so
    the payload rows and the source path are this build's."""
    ref = open(INSTALL_V3, encoding="utf-8-sig").read()
    if "REFUSED" not in ref or "_dropzone_sim_rc2_v3" not in ref:
        raise SystemExit("install_v3.ps1 no longer carries the guards this build adopts")
    rows = "\n".join(f"    @('{f['path'].replace('/', chr(92))}', '{f['sha256'].upper()}'),"
                     for f in files).rstrip(",")
    return f"""<#
    {TAG} installer - built on Working/Installer/install_v3.ps1 (its guard semantics adopted).
    Generated by Tools/scripts/bm_rc4.py; never run except against {SIM}
    and a decoy under it (R6). No game folder is touched.
      Status    what the dropzone holds vs this receipt (read-only)
      WhatIf    per target: add / replace / same; writes 0 files
      Install   snapshot every existing target, copy the payload, re-hash each file
      Verify    re-hash every target against the receipt (read-only)
      Rollback  restore the snapshot byte-for-byte and delete targets that did not exist
    Guards (fail-closed, print REFUSED and exit 2): -GameDir must normalise to {SIM}
    or sit below it; no real game root; every receipt target must resolve inside <GameDir>\\dropzone.
#>
[CmdletBinding()]
param(
    [ValidateSet('Status','WhatIf','Install','Verify','Rollback')][string]$Action = 'Status',
    [string]$GameDir = ''
)
$ErrorActionPreference = 'Stop'
$SimRoot   = '{SIM}'
$DenyRoots = @('D:\\Games', 'E:\\Games')
$Source    = Join-Path $PSScriptRoot 'drop'
$Files = @(
{rows}
)
function Refuse([string]$m) {{ Write-Output ('REFUSED: ' + $m); exit 2 }}
function HashOf([string]$p) {{ $h=[System.Security.Cryptography.SHA256]::Create(); try {{ $fs=[IO.File]::OpenRead($p); try {{ return ([BitConverter]::ToString($h.ComputeHash($fs))).Replace('-','') }} finally {{ $fs.Dispose() }} }} finally {{ $h.Dispose() }} }}
function Get-Parts([string]$p) {{ [IO.Path]::GetFullPath($p).Replace([char]'/', [IO.Path]::DirectorySeparatorChar).Split([IO.Path]::DirectorySeparatorChar) }}
function Test-SameOrUnder([string]$root, [string]$cand) {{
    $r = @(Get-Parts $root); $c = @(Get-Parts $cand)
    if ($c.Count -lt $r.Count) {{ return $false }}
    for ($i = 0; $i -lt $r.Count; $i++) {{ if ($r[$i] -ne $c[$i]) {{ return $false }} }}
    return $true
}}
function Test-Under([string]$root, [string]$cand) {{
    $c = @(Get-Parts $cand); $r = @(Get-Parts $root)
    return ((Test-SameOrUnder $root $cand) -and $c.Count -gt $r.Count)
}}
if ([string]::IsNullOrWhiteSpace($GameDir)) {{ Refuse '-GameDir is required' }}
try {{ $full = [IO.Path]::GetFullPath($GameDir) }} catch {{ Refuse 'cannot resolve -GameDir' }}
if (-not (Test-SameOrUnder $SimRoot $full)) {{ Refuse ('-GameDir ' + $full + ' is not under ' + $SimRoot) }}
foreach ($d in $DenyRoots) {{ if (Test-SameOrUnder $d $full) {{ Refuse ('-GameDir is inside ' + $d) }} }}
$Drop = Join-Path $full 'dropzone'
$Snap = Join-Path $full 'snapshot'
if (-not (Test-Under $full $Drop)) {{ Refuse 'derived dropzone is not below -GameDir' }}
if (-not (Test-Path -LiteralPath $Drop)) {{ Refuse 'no dropzone under -GameDir' }}
$n = 0; $bad = 0
foreach ($f in $Files) {{
    $rel = $f[0]; $sha = $f[1]
    $s = Join-Path $Source $rel; $d = Join-Path $Drop $rel; $b = Join-Path $Snap $rel
    if (-not (Test-Under $Drop $d)) {{ Refuse ('target outside the dropzone: ' + $rel) }}
    switch ($Action) {{
        'Status' {{
            if (Test-Path -LiteralPath $d) {{ if ((HashOf $d) -eq $sha) {{ $st = 'installed' }} else {{ $st = 'different' }} }} else {{ $st = 'absent' }}
            Write-Output ($st + ' ' + $rel)
        }}
        'WhatIf' {{
            if (Test-Path -LiteralPath $d) {{
                if ((HashOf $d) -eq $sha) {{ $op = 'same' }} else {{ $op = 'replace' }}
            }} else {{ $op = 'add' }}
            Write-Output ($rel + ' ' + $sha + ' ' + $op)
        }}
        'Install' {{
            if (-not (Test-Path -LiteralPath $s)) {{ throw ('build file missing: ' + $rel) }}
            if ((HashOf $s) -ne $sha) {{ throw ('build file does not match the receipt: ' + $rel) }}
            $dir = Split-Path -Parent $d
            if (-not (Test-Path -LiteralPath $dir)) {{ New-Item -ItemType Directory -Force -Path $dir | Out-Null }}
            if ((Test-Path -LiteralPath $d) -and ((HashOf $d) -ne $sha)) {{
                $bdir = Split-Path -Parent $b
                if (-not (Test-Path -LiteralPath $bdir)) {{ New-Item -ItemType Directory -Force -Path $bdir | Out-Null }}
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
        'Rollback' {{
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
        print(("PASS " if c else "FAIL ") + m)
        bad += 0 if c else 1

    drop = os.path.join(OUT, "drop")
    on_disk = sorted(os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/")
                     for dp, _, fs in os.walk(drop) for n in fs)
    ok(on_disk == [f["path"] for f in rec["files"]],
       f"receipt lists every drop file: {len(rec['files'])} = {len(on_disk)} on disk")
    ok(all(sha(os.path.join(drop, f["path"])) == f["sha256"] for f in rec["files"]),
       f"rehashed {len(rec['files'])}/{len(rec['files'])} drop files")
    aaf = os.path.join(OUT, "aaf")
    at = tree(aaf)
    ok(len(at) == rec["aaf"]["files"] and all(at.get(f["path"]) == f["sha256"]
                                             for f in rec["aaf"]["list"]),
       f"aaf tree: {len(at)} files, every sha256 matches the receipt")
    ee = os.path.join(drop, DROP_EE)
    raw = open(ee, "rb").read()
    R = {n: (o, s) for n, o, s in eetoc.sarc_dir(eetoc.unaaf(raw))}
    toc = eetoc.read_toc(open(ee + ".toc", "rb").read())
    ok(all(R.get(n) == (o, s) for n, o, s in toc if o),
       f".toc: {len(toc)} records, every non-zero record matches the .ee ({len(R)} entries)")
    ok(toc[-1][0] == ROOT_EPE, f".toc ends with the root .epe ({toc[-1][0].split('/')[-1]})")
    ok(all(o for n, o, _ in toc if n in (DIR + NEW + ".epe", PHYS)),
       f"graph and collision are internal: epe {R[DIR + NEW + '.epe']}, physicsc {R[PHYS]}")
    import bm_budget
    bud = rec["budgets"]["model"]
    ok(bud["after"]["non_vanilla_kb"] <= 4915.0,
       f"R9 model {bud['after']['non_vanilla_kb']} KB <= 4915 KB "
       f"(before {bud['before']['non_vanilla_kb']}, {len(bud['lods_changed'])} .lod trimmed)")
    ok(rec["budgets"]["texture_used_kb"] <= 7065.0,
       f"R9 texture {rec['budgets']['texture_used_kb']} KB <= 7065 KB (D-04 ledger, "
       f"{rec['budgets']['texture_used_note']})")
    # R8: no offset-0 record may carry bytes that differ from the vanilla donor .ee (test-023)
    import bm_rc
    vs = eetoc.unaaf(bm_rc.vfs(DIR + OLD + ".ee"))
    V = {n: (o, s) for n, o, s in eetoc.sarc_dir(vs)}
    rs = eetoc.unaaf(raw)
    stubs = set(rec["aaf"]["manifest_gaps_inherited"]["dangling"])

    def diffv(n):
        vn = n.replace(NEW, OLD)
        if n not in R:
            return False
        if vn not in V:
            return True
        (o1, s1), (o2, s2) = R[n], V[vn]
        return rs[o1:o1 + s1] != vs[o2:o2 + s2]

    ignored = [n for n, o, _ in toc if o == 0 and n not in stubs and diffv(n)]
    ok(not ignored, f"R8: no offset-0 record carries bytes different from the vanilla .ee "
                    f"({len(stubs)} size-only shared references excluded)"
                    f"{': ' + str(ignored[:4]) if ignored else ''}")
    for k in ("batmobile_health_medium.vmodc", "sportsmuscle.physicsc",
              "sportsmuscle_vehicle_parts.vmodc", "_custom_land_global.vmodc",
              "_land_engine.vmodc", "_lights.vmodc"):
        hit = [(n, o) for n, o, _ in toc if n.endswith(k)]
        ok(hit and all(o for _, o in hit), f"internal (real offset) {k}: {[o for _, o in hit]}")
    rc2 = tree(os.path.join(B("bm-RC2"), "aaf"))
    base = tree(os.path.join(B("bm-RC4-base"), "aaf"))
    stage_t = tree(os.path.join(B(STAGE), "aaf"))
    own = json.load(open(os.path.join(ROOT, "Working", "RC", "bm_rc_manifest_bm-RC4.json")))["owners"]
    kinds = aafdiff_class(at, rc2, base, stage_t, own)
    vs_rc2 = sorted(kinds)
    unexp = sorted(p for p, k in kinds.items() if k == "unexplained")
    ok(not unexp and rec["aafdiff_rc2"]["differ"] == len(vs_rc2)
       and rec["aafdiff_rc2"]["planned"] == len(vs_rc2)
       and os.path.exists(os.path.join(ROOT, rec["aafdiff_rc2"]["report"])),
       f"aafdiff vs RC2 lists exactly the planned {len(vs_rc2)} file(s) "
       f"({', '.join(f'{v} {k}' for k, v in sorted({x: sum(1 for q in kinds.values() if q == x)
                                                     for x in set(kinds.values())}.items()))}), "
       f"{len(unexp)} unexplained")
    coll = rec["collision"]
    dev_box = max(abs(float(x)) for x in coll["dev_vs_chassis_box_m"])
    ok("2 bodies / 3 boxes / 1 constraint" in coll["bmak_asset"]
       and coll["gate"]["hull_size_dev_m"] <= 0.05
       and coll["gate"]["pass"] == (dev_box <= 0.05)
       and (coll["gate"]["pass"] or any("B-10" in s for s in rec["not_done"]))
       and all(o for n, o, _ in toc if n == PHYS),
       f"B-10 reopened carried: {coll['bmak_asset']}, hull shape dev "
       f"{coll['gate']['hull_size_dev_m'] * 100:.2f} cm, placement dev {dev_box * 100:.1f} cm vs "
       f"the 5 cm gate -> {'PASS' if coll['gate']['pass'] else 'NOT MET and recorded'}, "
       f"physicsc internal at {[o for n, o, _ in toc if n == PHYS]}")
    ok(rec["build_batches"]["steps"] == 24 and len(rec["build_batches"]["b17_b20_no_payload"]) == 4
       and set(rec["cards_without_payload"]) == {"B-12", "B-17", "B-18", "B-19", "B-20", "B-25",
                                                  "B-26"},
       f"BUILD_BATCHES {rec['build_batches']['steps']} steps with B-17..B-20 no-payload; "
       f"B-12/B-17..B-20/B-25/B-26 recorded as cards without payload in this RC")
    m = rec["modes"]
    ok(m["rc_set"] == "pursuit" and m["merged_into_rc"] is False
       and m["rows_exact"] == 0 and len(m["built_trees"]) == 2
       and m["aafdiff_planned_files"] == 2,
       f"mode pair built but unmerged: RC is the {m['rc_set']} set, {len(m['built_trees'])} trees, "
       f"{m['rows_exact']} exact rows, {len(m['rows_not_built'])} not built")
    ok(len([r for r in rec["aaf"]["list"] if r["owner_card"] == "?"]) == 0,
       "every tree file has an owner card")
    ok(rec["texture_rows"]["unfaithful"] == 12 and rec["texture_rows"]["total"] == 23
       and rec["complete"] is False,
       "12/23 texture rows recorded unfaithful and the tree marked incomplete")
    ok(not rec["conflicts"] and len(rec["module_merges"]) == 1,
       f"{len(rec['conflicts'])} unresolved module conflict(s); "
       f"{len(rec['module_merges'])} overlapping module(s) carried by merge")
    for mg in rec["module_merges"]:
        want = ([(e["member"], e["new"]) for e in mg["edits"]]
                + [(e["member"], e["new"]) for e in clg_edits()])
        rb = read_module(raw, toc, mg["path"].rsplit("/", 1)[-1], want)
        ok(rb["ok"] and rb["checked"] == len(want)
           and at.get(mg["path"].replace(OLD, NEW)) == mg["merged_sha256"],
           f"module merge read back from the packed .toc: {rb['checked']} member(s) = both "
           f"branches' sets (D-08 skew 400 + D-10's {len(clg_edits())}), merged sha256 "
           f"{mg['merged_sha256'][:16]}..."
           + (f" MISMATCHES {rb['mismatches']}" if rb["mismatches"] else ""))

    shutil.rmtree(SIM, ignore_errors=True)
    os.makedirs(os.path.join(SIM, "dropzone"))
    w = ps("WhatIf", SIM)
    lines = [l for l in w.stdout.splitlines() if l and not l.startswith("wrote")]
    listed = [l.split(" ")[0].replace("\\", "/") for l in lines]
    ok(w.returncode == 0 and listed == [f["path"] for f in rec["files"]]
       and [l.split(" ")[1].lower() for l in lines] == [f["sha256"] for f in rec["files"]],
       f"-WhatIf lists exactly the receipt's {len(listed)} files + sha256")
    decoy = os.path.join(SIM, "dropzone", "profile", "item.onlinec")
    os.makedirs(os.path.dirname(decoy), exist_ok=True)
    open(decoy, "wb").write(b"decoy")
    d0 = sha(decoy)
    i = ps("Install", SIM)
    v = ps("Verify", SIM)
    ok(i.returncode == 0 and v.returncode == 0
       and f"verified {len(rec['files'])}/{len(rec['files'])}" in v.stdout,
       "rehearsal: Install on a decoy dropzone then Verify -> "
       + (v.stdout.strip().splitlines() or ["?"])[-1])
    r = ps("Rollback", SIM)
    ok(r.returncode == 0 and sha(decoy) == d0 and
       sorted(os.listdir(os.path.dirname(decoy))) == ["item.onlinec"],
       "rehearsal: Rollback restored the decoy and removed only added files")
    bad_out = ps("Install", os.path.join(os.path.dirname(SIM), "not_the_sim"))
    ok(bad_out.returncode == 2 and "REFUSED" in bad_out.stdout,
       "guard: a -GameDir outside the simulation root is REFUSED (exit 2)")
    shutil.rmtree(SIM, ignore_errors=True)
    print(("PASS" if not bad else "FAIL") + f": {TAG} {bad} failure(s), {len(rec['files'])} drop "
          f"files, {rec['aaf']['files']} tree files, .toc {rec['toc']['records']} records, "
          f"model {bud['after']['non_vanilla_kb']} KB, textures 12/23 unfaithful (incomplete)")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if a.write:
        rec = build()
        print("\n".join(rec["steps"]))
    return check()


if __name__ == "__main__":
    sys.exit(main())
