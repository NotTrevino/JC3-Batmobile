"""bm_rc3.py - assemble `Builds/bm-RC3` from bm-RC2 + the jointed parts module + the two hinges.

Card: the three offline pieces that bm-RC2 lacks are (a) the jointed vehicle-parts module
(`Builds/bm-RC3-parts`, joints 11/12), (b) the physicsc carrying those two hinge objects
(`Working/Collision/batmobile_hinged.physicsc`) and (c) bm-004c's bank fixes. This tree takes
(a) and (b) and leaves the banks out, because bm-004c's loop-wrap gate is still RED.

This is a copy of `Tools/scripts/bm_rc2.py` (never edited) with its own TAG and a different
build shape: bm-RC2 is a merge of branches onto bm-005, while bm-RC3 is an **overlay onto bm-RC2**
- 691 files start byte-identical to the parent and exactly two change:

    1. models/.../batmobile/sportsmuscle_vehicle_parts.vmodc  <- Builds/bm-RC3-parts (sha pinned)
    2. models/.../batmobile/sportsmuscle.physicsc             <- bm-RC2's physicsc + the two
       304-byte hinge objects from Working/Collision/batmobile_hinged.physicsc (indices 11, 12)

Why the physicsc is appended onto bm-RC2's file instead of copied: bm-RC2's physicsc is the
902,384 B collision build (B-10b body world-collision from the Batmobile mesh, B-10c convex hull);
`batmobile_hinged.physicsc` is the 340,992 B pre-collision file with the hinges appended. Copying it
would silently undo B-10b/B-10c. So the two hinge objects are copied **byte for byte** from the
hinged file (asserted) and appended onto bm-RC2's collision build - the tree keeps both.

Banks: bm-004c's gate is RED (`Builds/bm-004c/verify/audio_004c.md`: "5/5 loudness gates pass,
2/3 loop-wrap gates pass; red: vehicles#279"), so `sound/fmod_banks/vehicles.bank` and
`weapons.bank` are **not** in this drop; the dropzone's existing banks are left alone.

Receipt: every drop file with sha256 + owner card; `changed_vs_parent` (the two files, with both
hashes and why); `identical_to_parent` counts for the aaf tree and the drop. `--check` re-hashes
everything, re-derives the two overlays, re-reads the .toc, and runs the installer rehearsals on a
simulated dropzone under tmp/ - never a real install (R6).

Usage
    python Tools/scripts/bm_rc3.py --write   # build Builds/bm-RC3 (then check it)
    python Tools/scripts/bm_rc3.py --check   # re-hash, re-derive, rehearse; writes nothing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_leaf  # noqa: E402
import eetoc  # noqa: E402

TAG = "bm-RC3"
PARENT = "bm-RC2"
OUT = os.path.join(ROOT, "Builds", TAG)
B = lambda t: os.path.join(ROOT, "Builds", t)
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
WORK = os.environ.get("JC3_RAW", "E:/Modding/_shared/gamedata/JC3grab") + "/rc3"
DIR = bm_leaf.DIR
LEAF = bm_leaf.NEW
EPE = DIR + LEAF + ".ee"          # the dropzone file (bm-RC2 ships the same name)
ROOT_EPE = DIR + LEAF + ".epe"     # the entity root *inside* it, last .toc record
PARTS = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/"
         "sportsmuscle_vehicle_parts.vmodc")
PHYS = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/"
        "sportsmuscle.physicsc")
PARTS_TAG = "bm-RC3-parts"
PARTS_SHA = "17d98205bb2eeaf7148804f291a7852a03de6f2335e284d2ba9887b2524f0c11"
PARTS_BASE_SHA = "6e379e4c5716f15c82f3b8a557f6140b059b7157f2655215f05fa8a340e82560"
HINGED = os.path.join(ROOT, "Working", "Collision", "batmobile_hinged.physicsc")
PROFILE_SRC = "bm-013"
PROFILE_FILES = ("profile/item.onlinec", "profile/task.onlinec", "profile/online.stringlookup",
                 "settings/spawn_vehicle_defs.bin",
                 "textures/ui/vehicle_icons/" + LEAF + ".ddsc")
BANK_PATHS = ("sound/fmod_banks/vehicles.bank", "sound/fmod_banks/weapons.bank")
GATE_FILE = "Builds/bm-004c/verify/audio_004c.md"
GATE_LINE = "STATUS: 5/5 loudness gates pass, 2/3 loop-wrap gates pass; red: vehicles#279"
SIM = os.path.join(ROOT, "tmp", "rc3_sim")


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


def hinged_physicsc(src: bytes) -> tuple[bytes, dict]:
    """bm-RC2's physicsc + the two hinge objects, taken from batmobile_hinged.physicsc."""
    import bm_physicsc_hinges as H
    s = H.Packfile(src)
    before = H.constraints(s)
    if len(before) != 11:
        raise SystemExit(f"{PARENT} physicsc has {len(before)} constraints, expected 11")
    _, donor = H.donor_physicsc()
    dpf = H.Packfile(donor)
    dcons = H.constraints(dpf)
    blobs = {r["id"]: H.patched(
        dpf.blob[dpf.base + dcons[r["donor_index"]].offset:
                dpf.base + dcons[r["donor_index"]].offset + H.HINGE_EXT], r)
        for r in (H.P01, H.P02)}
    out, info = H.append_objects(src, [(H.HINGE, blobs["P-01"]), (H.HINGE, blobs["P-02"])])

    # the two objects must be the ones the hinged file carries (byte equality, not a re-derivation)
    hb = open(HINGED, "rb").read()
    hpf = H.Packfile(hb)
    hcons = H.constraints(hpf)
    if len(hcons) != 13:
        raise SystemExit(f"{os.path.relpath(HINGED, ROOT)} has {len(hcons)} constraints, expected 13")
    for i, key in ((11, "P-01"), (12, "P-02")):
        o = hcons[i].offset
        if hpf.blob[hpf.base + o:hpf.base + o + H.HINGE_EXT] != blobs[key]:
            raise SystemExit(f"hinge index {i} differs from {os.path.relpath(HINGED, ROOT)}")

    o = H.Packfile(out)
    after = H.constraints(o)
    if len(after) != 13 or after[11].cls != H.HINGE or after[12].cls != H.HINGE:
        raise SystemExit(f"appended constraints read back as {len(after)}: "
                         f"{[c.cls for c in after[11:]]}")
    for i, r in ((11, H.P01), (12, H.P02)):
        c = after[i]
        axis = o.vec4(c.offset + H.AXIS)[:3]
        pivot = o.vec4(c.offset + H.PIVOT)[:3]
        lo, hi = o.f32(c.offset + H.MIN), o.f32(c.offset + H.MAX)
        if (any(abs(a - b) > 1e-5 for a, b in zip(axis, r["axis"]))
                or any(abs(a - b) > 1e-5 for a, b in zip(pivot, r["pivot"]))
                or abs(lo - r["min"]) > 1e-5 or abs(hi - r["max"]) > 1e-5):
            raise SystemExit(f"hinge {i} values do not re-read ({axis} {pivot} {lo}..{hi})")
    if [c.cls for c in after[:11]] != [c.cls for c in before]:
        raise SystemExit("the 11 inherited constraint classes changed")
    if [s.blob[s.base + x:s.base + x + s.extents[x]]
            for x in s._order if s._starts[x] == "hknpPhysicsSystemData"] != \
       [o.blob[o.base + x:o.base + x + o.extents[x]]
            for x in o._order if o._starts[x] == "hknpPhysicsSystemData"]:
        raise SystemExit("hknpPhysicsSystemData bytes changed")
    if o.virtual_residue or o.classname_marker_bad:
        raise SystemExit(f"table residue {o.virtual_residue} / markers {o.classname_marker_bad}")
    return out, {"method": "append the two 304-byte hinge objects from batmobile_hinged.physicsc "
                           "onto bm-RC2's 902,384 B collision build (B-10b/B-10c kept)",
                 "src_bytes": len(src), "bytes": len(out), "objects": info["objects"],
                 "constraints_before": len(before), "constraints_after": len(after),
                 "appended": [{"index": i, "id": r["id"], "part": r["part"],
                               "axis": list(r["axis"]), "pivot": list(r["pivot"]),
                               "min": r["min"], "max": r["max"]}
                              for i, r in ((11, H.P01), (12, H.P02))],
                 "hinged_file_blobs_equal": True}


def build() -> dict:
    parent_aaf, parent_drop = os.path.join(B(PARENT), "aaf"), os.path.join(B(PARENT), "drop")
    p_rec = json.load(open(os.path.join(B(PARENT), "receipt.json")))
    if p_rec.get("tag") != PARENT or p_rec.get("leaf") != LEAF:
        raise SystemExit(f"{PARENT} receipt is not the expected tree")
    p_tree, p_drop = tree(parent_aaf), tree(parent_drop)
    if p_tree.get(PARTS) != PARTS_BASE_SHA:
        raise SystemExit(f"{PARENT} parts module is not the jointed file's base")

    stamp = open(os.path.join(B(PARTS_TAG), "receipt.json"))
    j_rec = json.load(stamp)
    if (j_rec.get("base") != PARENT or j_rec.get("module") != PARTS
            or j_rec["module_sha256"].lower() != PARTS_SHA
            or [r["constraint_index_new"] for r in j_rec["joint_rows"]] != [11, 12]):
        raise SystemExit(f"{PARTS_TAG} receipt is not the jointed module this card names")
    src_parts = os.path.join(B(PARTS_TAG), "aaf", PARTS)
    if sha(src_parts) != PARTS_SHA:
        raise SystemExit(f"{PARTS_TAG} parts module sha256 differs from its receipt")

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    aaf = os.path.join(OUT, "aaf")
    shutil.copytree(parent_aaf, aaf)
    steps = []

    def step(msg: str) -> None:
        steps.append(msg)
        print("  " + msg, flush=True)

    step(f"stage = {PARENT}/aaf ({len(p_tree)} files, byte-identical)")

    shutil.copy(src_parts, os.path.join(aaf, PARTS))
    step(f"jointed parts module <- Builds/{PARTS_TAG} (sha {PARTS_SHA[:12]}, "
         f"constraint_index 11/12 on batmobile_turret/batmobile_cannon)")

    phys_src = open(os.path.join(aaf, PHYS), "rb").read()
    if hashlib.sha256(phys_src).hexdigest() != p_tree[PHYS]:
        raise SystemExit("staged physicsc is not the parent's")
    phys_out, phys_info = hinged_physicsc(phys_src)
    with open(os.path.join(aaf, PHYS), "wb") as f:
        f.write(phys_out)
    step(f"physicsc: {phys_info['constraints_before']} -> {phys_info['constraints_after']} "
         f"constraints, {phys_info['src_bytes']:,} -> {phys_info['bytes']:,} B, hinges 11/12")

    # pack and prove the payload round-trips
    drop = os.path.join(OUT, "drop")
    os.makedirs(drop)
    ee = os.path.join(drop, EPE)
    os.makedirs(os.path.dirname(ee), exist_ok=True)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee], "SmallPack")
    ver = os.path.join(WORK, "verify")
    if os.path.exists(ver):
        shutil.rmtree(ver)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee, ver], "SmallUnpack")
    at, vt = tree(aaf), tree(ver)
    listed = bm_leaf.verify_manifest(aaf)
    packed_diff = sorted(p for p in at
                         if p != "@files.xml" and p not in listed["unlisted"] and vt.get(p) != at[p])
    if packed_diff:
        raise SystemExit(f"packed .ee differs from the tree: {packed_diff[:5]}")
    step(f"packed {EPE.split('/')[-1]} ({os.path.getsize(ee):,} B), unpack matches "
         f"{len(at) - len(listed['unlisted'])} listed files (manifest gaps inherited)")

    # .toc: base = the parent's own .toc (it already internalises every changed module)
    p_ee = os.path.join(parent_drop, EPE)
    p_toc = eetoc.read_toc(open(p_ee + ".toc", "rb").read())
    new_raw = open(ee, "rb").read()
    ents = eetoc.patch_toc(new_raw, p_toc, internal=(), include_lod=True)
    with open(ee + ".toc", "wb") as f:
        f.write(eetoc.write_toc(ents))
    if eetoc.read_toc(open(ee + ".toc", "rb").read()) != ents:
        raise SystemExit(".toc does not re-read to what was written")
    R = {n: (o, s) for n, o, s in eetoc.sarc_dir(eetoc.unaaf(new_raw))}
    pe = eetoc.unaaf(open(p_ee, "rb").read())
    P = {n: (o, s) for n, o, s in eetoc.sarc_dir(pe)}
    nr = eetoc.unaaf(new_raw)
    # offset 0 in the .ee = "not stored here, load from the archives"; such a record is only stale
    # if this .ee DOES store the file (real offset) with bytes the parent's copy does not have.
    stale = [n for n, o, s in ents if o == 0 and n in R and R[n][0] > 0 and n in P
             and P[n][0] > 0 and nr[R[n][0]:R[n][0] + R[n][1]]
             != pe[P[n][0]:P[n][0] + P[n][1]]]
    if stale:
        raise SystemExit(f"offset-0 records carry new bytes (would be ignored): {stale[:4]}")
    if ents[-1][0] != ROOT_EPE:
        raise SystemExit(f".toc does not end with the root .epe: {ents[-1][0]}")
    for p in (PARTS, PHYS):
        got = R.get(p)
        if not got or got[1] != os.path.getsize(os.path.join(aaf, p)):
            raise SystemExit(f".toc record for {p} is {got}, not the packed size")
    toc_info = {"records": len(ents), "internal": [], "last": ents[-1][0],
                "offset0_left": sum(1 for _, o, _ in ents if o == 0),
                "parts": list(R[PARTS]), "physicsc": list(R[PHYS])}
    step(f".toc: {len(ents)} records, root last, parts {R[PARTS]}, physicsc {R[PHYS]}")

    # drop: the parent's non-bank files, the two overlays, and no banks (bm-004c gate RED)
    for p in PROFILE_FILES:
        s = os.path.join(B(PROFILE_SRC), "drop", p)
        os.makedirs(os.path.dirname(os.path.join(drop, p)), exist_ok=True)
        shutil.copy(s, os.path.join(drop, p))
    owner_drop = {EPE: "B-RC3 (B-01..B-13b merged + joints + hinges)", EPE + ".toc": "B-RC3",
                  "profile/item.onlinec": "B-13", "profile/task.onlinec": "B-13",
                  "profile/online.stringlookup": "B-13", "settings/spawn_vehicle_defs.bin": "B-13c",
                  "textures/ui/vehicle_icons/" + LEAF + ".ddsc": "B-13"}
    files = []
    for dp, _, fs in os.walk(drop):
        for n in fs:
            p = os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/")
            files.append({"path": p, "bytes": os.path.getsize(os.path.join(dp, n)),
                          "sha256": sha(os.path.join(dp, n)), "owner_card": owner_drop.get(p, "?")})
    files.sort(key=lambda f: f["path"])
    if any(f["owner_card"] == "?" for f in files):
        raise SystemExit(f"drop files with no owner: {[f['path'] for f in files if f['owner_card'] == '?']}")
    if any(f["path"] in BANK_PATHS for f in files):
        raise SystemExit("a bank is in the drop although bm-004c's gate is RED")

    changed = []
    for p, why in ((PARTS, "jointed module: constraint_index 11 (batmobile_turret) / 12 "
                           "(batmobile_cannon) rewritten on 2 of 61 parts"),
                   (PHYS, "two hkpHingeConstraintData objects appended (indices 11/12)")):
        changed.append({"path": p, "parent_sha256": p_tree[p], "sha256": at[p],
                        "owner_card": "B-04 + JOINT_FIELDS" if p == PARTS else "hinges",
                        "why": why, "bytes": os.path.getsize(os.path.join(aaf, p))})
    same_aaf = sorted(p for p in at if p not in (PARTS, PHYS) and p_tree.get(p) == at[p])
    same_drop = sorted(f["path"] for f in files
                       if f["path"] not in (EPE, EPE + ".toc")
                       and p_drop.get(f["path"]) == f["sha256"])
    if len(same_aaf) != len(at) - 2:
        raise SystemExit(f"{len(at) - 2 - len(same_aaf)} payload files changed beyond the two overlays")

    aaf_list = [{"path": p, "sha256": h,
                 "owner_card": "B-RC3 overlay" if p in (PARTS, PHYS)
                 else "inherited from " + PARENT} for p, h in sorted(at.items())]
    rec = {"schema": 2, "card": "B-RC3", "tag": TAG, "parent": PARENT,
           "parent_receipt_sha256": sha(os.path.join(B(PARENT), "receipt.json")),
           "parent_ee_sha256": p_drop[EPE], "leaf": LEAF,
           "lineage": f"{PARENT} <- {p_rec.get('lineage_card')} (B-01..B-13b); B-RC3 adds the joints",
           "steps": steps, "changed_vs_parent": changed,
           "identical_to_parent": {"aaf_files": len(same_aaf), "aaf_total": len(at),
                                   "drop_files": len(same_drop),
                                   "drop_total_excluding_ee": len(files) - 2},
           "physicsc": phys_info,
           "parts_module": {"tag": PARTS_TAG, "base_sha256": PARTS_BASE_SHA,
                            "sha256": PARTS_SHA, "joints": j_rec["joint_rows"],
                            "changed_rows": j_rec["changed_rows"]},
           "banks": {"included": False, "gate": GATE_FILE, "gate_line": GATE_LINE,
                     "why": "bm-004c's loop-wrap gate is RED (vehicles#279); the drop ships no "
                            "sound/fmod_banks file and the dropzone's own banks stay untouched",
                     "dropped_vs_parent": [{"path": p, "parent_sha256": p_drop[p]}
                                           for p in BANK_PATHS if p in p_drop]},
           "files": files,
           "aaf": {"files": len(aaf_list), "list": aaf_list,
                   "manifest_gaps_inherited": listed},
           "toc": toc_info,
           "budgets": {"inherited_from": PARENT, "model_delta_bytes": os.path.getsize(
               os.path.join(aaf, PHYS)) - os.path.getsize(os.path.join(parent_aaf, PHYS)),
               "texture_delta_bytes": 0, "note": "only the physicsc grows (+624 B); model mesh "
                                                 "and texture bytes are the parent's"},
           "replaced_rollback": "Install backs up any dropzone file it would overwrite to "
                                "<name>.bm-RC3-backup; Rollback091 restores those and deletes the "
                                "files this build added",
           "unknown": ["whether the jointed parts module + two hinge objects load (phase Q)",
                       "whether the turret/cannon hinge indices 11/12 bind the right parts (Q-3)",
                       "whether the excluded banks' RED loop wrap is audible (V-04c, phase Q)"]}
    json.dump(rec, open(os.path.join(OUT, "receipt.json"), "w"), indent=1)
    open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8-sig").write(installer(files))
    os.makedirs(os.path.join(ROOT, "Working", "RC"), exist_ok=True)
    json.dump({"tag": TAG, "parent": PARENT, "overlays": changed, "banks": False},
              open(os.path.join(ROOT, "Working", "RC", "bm_rc_manifest_%s.json" % TAG), "w"), indent=1)
    return rec


def installer(files: list[dict]) -> str:
    rows = "\n".join(f"    @('{f['path'].replace('/', chr(92))}', '{f['sha256'].upper()}'),"
                     for f in files).rstrip(",")
    return f"""<#
    {TAG} installer. Generated by Tools/scripts/bm_rc3.py, never run by it
    except against a simulated -GameDir under tmp/ (R6).
    -Action Status       what is installed vs this receipt (read-only)
    -Action WhatIf       list every file and what Install would do with it; writes nothing
    -Action Install      back up any dropzone file it replaces to <name>.{TAG}-backup, copy, re-hash
    -Action Verify       re-hash every installed file against the receipt
    -Action Rollback091  restore every backup and remove every file this build added
    Close the game before Install/Rollback091. No bank file is installed by this build.
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
        print(("PASS " if c else "FAIL ") + m)
        bad += 0 if c else 1

    aaf, drop = os.path.join(OUT, "aaf"), os.path.join(OUT, "drop")
    parent_aaf, parent_drop = os.path.join(B(PARENT), "aaf"), os.path.join(B(PARENT), "drop")
    p_tree, p_drop = tree(parent_aaf), tree(parent_drop)
    at = tree(aaf)
    on_disk = sorted(os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/")
                     for dp, _, fs in os.walk(drop) for n in fs)
    ok(on_disk == [f["path"] for f in rec["files"]],
       f"receipt lists every drop file: {len(rec['files'])} = {len(on_disk)} on disk")
    ok(all(sha(os.path.join(drop, f["path"])) == f["sha256"] for f in rec["files"]),
       f"rehashed {len(rec['files'])}/{len(rec['files'])} drop files")
    ok(len(at) == rec["aaf"]["files"] and all(at.get(f["path"]) == f["sha256"] for f in rec["aaf"]["list"]),
       f"aaf tree: {len(at)} files, every sha256 matches")
    changed = [c["path"] for c in rec["changed_vs_parent"]]
    others = [p for p in at if p not in changed]
    same = [p for p in others if p_tree.get(p) == at[p]]
    ok(changed == [PARTS, PHYS] and len(same) == len(others),
       f"exactly {len(changed)} changed vs {PARENT} ({', '.join(c.split('/')[-1] for c in changed)}); "
       f"{len(same)}/{len(others)} other payload files sha256-identical")
    ok(all(c["parent_sha256"] == p_tree[c["path"]] for c in rec["changed_vs_parent"]),
       "the receipt's parent hashes are the parent tree's own")
    same_drop = [f["path"] for f in rec["files"] if f["path"] not in (EPE, EPE + ".toc")
                 and p_drop.get(f["path"]) == f["sha256"]]
    ok(len(same_drop) == len(rec["files"]) - 2,
       f"drop: {len(same_drop)}/{len(rec['files']) - 2} non-.ee files sha256-identical to {PARENT}")
    ok(not any(f["path"] in BANK_PATHS for f in rec["files"]),
       f"no bank in the drop ({len(BANK_PATHS)} excluded: bm-004c gate RED)")

    ee = os.path.join(drop, EPE)
    raw = open(ee, "rb").read()
    real = eetoc.sarc_dir(eetoc.unaaf(raw))
    R = {n: (o, s) for n, o, s in real}
    toc = eetoc.read_toc(open(ee + ".toc", "rb").read())
    ok(all(R.get(n) == (o, s) for n, o, s in toc if o),
       f".toc: {len(toc)} records, every non-zero record matches the .ee ({len(real)} entries)")
    ok(toc[-1][0] == ROOT_EPE, f".toc ends with the root .epe ({toc[-1][0].split('/')[-1]})")
    ok(all(o for n, o, _ in toc if n == PARTS or n == PHYS),
       f"both overlays are internal: parts {R[PARTS]}, physicsc {R[PHYS]}")
    ok(R[PARTS][1] == os.path.getsize(os.path.join(aaf, PARTS))
       and R[PHYS][1] == rec["physicsc"]["bytes"],
       f"packed sizes: parts {R[PARTS][1]}, physicsc {R[PHYS][1]} (appended {rec['physicsc']['bytes']})")
    pe = eetoc.unaaf(open(os.path.join(parent_drop, EPE), "rb").read())
    P = {n: (o, s) for n, o, s in eetoc.sarc_dir(pe)}
    nr = eetoc.unaaf(raw)
    stale = [n for n, o, s in toc if o == 0 and n in R and R[n][0] > 0 and n in P
             and P[n][0] > 0
             and nr[R[n][0]:R[n][0] + R[n][1]] != pe[P[n][0]:P[n][0] + P[n][1]]]
    ok(not stale, f"no offset-0 record carries bytes that differ from {PARENT} ({len(stale)} stale)")

    import bm_physicsc_hinges as H
    pf = H.Packfile(open(os.path.join(aaf, PHYS), "rb").read())
    cons = H.constraints(pf)
    ok(len(cons) == 13 and cons[11].cls == H.HINGE and cons[12].cls == H.HINGE,
       f"physicsc re-derives: {len(cons)} constraint objects, 11/12 {cons[11].cls}")
    ok(all(abs(a - b) <= 1e-5 for a, b in zip(pf.vec4(cons[11].offset + H.PIVOT)[:3],
                                              H.P01["pivot"])),
       f"turret hinge pivot {[round(x, 6) for x in pf.vec4(cons[11].offset + H.PIVOT)[:3]]}")
    ok(all(abs(a - b) <= 1e-5 for a, b in zip(pf.vec4(cons[12].offset + H.AXIS)[:3],
                                              H.P02["axis"])),
       f"cannon hinge axis {[round(x, 6) for x in pf.vec4(cons[12].offset + H.AXIS)[:3]]}")
    dem = subprocess.run([sys.executable, os.path.join(HERE, "jc3hkx.py"), "check", "--entity",
                          "__no_entity__", "--file", os.path.join(aaf, PHYS)],
                         capture_output=True, text=True, cwd=ROOT,
                         env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    ok(dem.returncode == 0, "jc3hkx.py check --file: " + (dem.stdout.strip().splitlines() or ["?"])[-1])

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
    r, v = ps("Install", sim), ps("Verify", sim)
    ok(r.returncode == 0 and v.returncode == 0
       and f"verified {len(rec['files'])}/{len(rec['files'])}" in v.stdout,
       "rehearsal (a) clean dropzone: Install -> Verify "
       + (v.stdout.strip().splitlines() or ["?"])[-1])
    rb = ps("Rollback091", sim)
    left = [os.path.join(dp, n) for dp, _, fs in os.walk(os.path.join(sim, "dropzone")) for n in fs]
    ok(rb.returncode == 0 and not left, f"rehearsal (a) Rollback091 removed every added file ({len(left)} left)")
    sim2 = os.path.join(SIM, "decoy")
    decoy = os.path.join(sim2, "dropzone", "profile", "item.onlinec")
    os.makedirs(os.path.dirname(decoy))
    open(decoy, "wb").write(b"decoy vanilla bytes")
    d0 = sha(decoy)
    r = ps("Install", sim2)
    ok(r.returncode == 0 and os.path.exists(decoy + f".{TAG}-backup") and "backed up profile" in r.stdout,
       "rehearsal (b) decoy dropzone: Install backed up the existing item.onlinec")
    rb = ps("Rollback091", sim2)
    left = [n for dp, _, fs in os.walk(os.path.join(sim2, "dropzone")) for n in fs]
    ok(rb.returncode == 0 and os.path.exists(decoy) and sha(decoy) == d0 and left == ["item.onlinec"],
       "rehearsal (b) Rollback091 restored the decoy byte-for-byte and removed the rest")
    shutil.rmtree(SIM, ignore_errors=True)
    print(f"{'PASS' if not bad else 'FAIL'}: {TAG} {bad} failure(s), {len(rec['files'])} drop files, "
          f"{rec['aaf']['files']} tree files, {len(changed)} changed vs {PARENT}, .toc "
          f"{rec['toc']['records']} records")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        rec = build()
        print("\n".join(rec["steps"]))
        for c in rec["changed_vs_parent"]:
            print(f"  changed {c['path']} {c['parent_sha256'][:12]} -> {c['sha256'][:12]}")
        print(f"identical to parent: {rec['identical_to_parent']}")
        print(f"banks: {rec['banks']['why']}")
    if a.write or a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
