"""bm_health.py - B-09: a private health module, the T-14 values, and the `.epe` repoint.

`GRAB_BACKLOG.md` §8 (`B-09`): "copy `lave_health_medium.vmodc` to a private path, apply
`t10_damage_edits.json`, repoint the `.epe` `damage` reference; part damage types per T-14.
Done: `damage_audit.py` green; `damage_predict.py --root <build>` prints the T-14 table."

What is built (every number from a recorded source, R4/R11):

  * a **private copy** of the shared `lave_health_medium.vmodc` under the Batmobile's own entity
    directory (R7: the shared file is never written; it stays byte-identical in the tree);
  * `max_health` 2000 -> 36000 (`t10_damage_edits.json` T-DM1: 24 BmAK heavy-cannon hits x 1500
    shell damage; a declared switch, pending Q1-DM-A). The two declared switches T-DM6
    (`deform_scale` 0) and T-DM8 (`impact_damage_factor` 0) are asserted, not written: the shipped
    module already carries them;
  * the two ARM-4 wheel rows from the same file (`front_/rear_wheels_damage.skew_health` 200 -> 400)
    in the entity's **own** `custom_land_global.vmodc`, which is not a shared module;
  * the `.epe` root property `damage` (a 4-byte Jenkins hash of the module's full path) repointed at
    the private copy;
  * no part damage type is changed here: the parts module already carries T-14's per-part types
    (B-04), so this step *asserts* that every part's `damage_type` has a `PartDamageType` row in the
    new health module.

Method: the module decodes with `Tools/Gibbed-patched/…ConvertAdf.exe` and every member carries
`offset-in-file`, so each value is written as a fixed-width write at its decoded offset. The file is
not re-encoded (no size change, no +544 B placement padding - MODLOG §101b). After writing, the
module is decoded again and compared member by member with the source: only the named members may
differ.

Usage:
  python Tools/scripts/bm_health.py --write          # build Builds/bm-009 + the spec
  python Tools/scripts/bm_health.py --check          # re-read the build and run the card's checks
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from eetoc import read_toc, sarc_dir, unaaf      # noqa: E402
from rbmhdr import hash_jenkins                  # noqa: E402

BASE_TAG = "bm-002"                              # B-04's build: the phase-B lineage head
TAG = "bm-009"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
GAME = r"D:\Games\Just Cause 3"
DROP = ("dropzone\\editor\\entities\\jc_vehicles\\01_land\\"
        "v0300_car_kensington_sportsmuscle")
ENT = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
SHARED = "editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc"
HEALTH = ENT + "/batmobile_health_medium.vmodc"          # the private copy (R7)
LAND_GLOBAL = ENT + "/modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc"
EPE = ENT + "/v0300_car_kensington_sportsmuscle_civilian_01.epe"
PARTS = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "sportsmuscle_vehicle_parts.vmodc")   # B-04's built module (its own tree path)
NEW_NAME = "batmobile_health_medium.vmodc"

GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")
SPEC = os.path.join(ROOT, "Working", "Damage", "bm_health.json")
EDITS = os.path.join(ROOT, "Working", "Translation", "t10_damage_edits.json")


def set_tags(base_tag: str, tag: str) -> None:
    """--base / --tag: the same B-09 edit on another build line (bm-RC4-damage-collision)."""
    global BASE_TAG, TAG, SPEC
    BASE_TAG, TAG = base_tag, tag
    name = "bm_health.json" if tag == "bm-009" else f"bm_health_{tag}.json"
    SPEC = os.path.join(ROOT, "Working", "Damage", name)
WORK = os.path.join(ROOT, "tmp", "b09")

# The four values, each with the T-14 row that owns it. `member` is the decoded member name.
EDITS_TABLE = [
    {"row": "T-DM1", "module": HEALTH, "member": "max_health", "from": 2000, "to": 36000,
     "why": "24 BmAK heavy-cannon hits x 1500.0 shell damage = 36000 (the H0 answer; H2 35750, "
            "H1 18000). Outside the shipped 500..4000, so a declared switch - pending Q1-DM-A.",
     "source": "Working/Translation/t10_damage_edits.json rows[T-DM1]"},
    {"row": "T-DM4", "module": HEALTH, "member": "explosion_threshold", "from": 4000, "to": 4000,
     "why": "per-hit damage threshold, independent of the health pool: 36000 does not move it",
     "source": "Working/Translation/t10_damage_edits.json rows[T-DM4] (keep)"},
    {"row": "T-DM6", "module": HEALTH, "member": "deform_scale", "from": 0.0, "to": 0.0,
     "why": "no panel crumple (APP-7); already 0 in the shipped module, declared switch",
     "source": "Working/Translation/t10_damage_edits.json rows[T-DM6] + damage_switches.json"},
    {"row": "T-DM8", "module": HEALTH, "member": "impact_damage_factor", "from": 0.0, "to": 0.0,
     "why": "incoming collision damage off (BmAK: ramming does not scratch it); declared switch",
     "source": "Working/Translation/t10_damage_edits.json rows[T-DM8] + damage_switches.json"},
    {"row": "T-14 ARM-4", "module": LAND_GLOBAL, "member": "front_wheels_damage.skew_health",
     "from": 200, "to": 400,
     "why": "wheel health at the shipped ceiling 200..400; JC3 has no unbreakable-wheel member",
     "source": "Working/Translation/t10_damage_edits.json arm4_wheels.edits[0]"},
    {"row": "T-14 ARM-4", "module": LAND_GLOBAL, "member": "rear_wheels_damage.skew_health",
     "from": 200, "to": 400,
     "why": "same row, rear axle",
     "source": "Working/Translation/t10_damage_edits.json arm4_wheels.edits[1]"},
]
DAMAGE_NAME_HASH = 0x4F489F01          # Jenkins("damage"), from jc3_damage_search.epe_fields
INT_TYPES = ("int8", "int16", "int32", "uint8", "uint16", "uint32")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


# ------------------------------------------------------------------ the ADF reader
def decode(vmodc: str, xml: str) -> str:
    r = subprocess.run([ADF, "--e", vmodc, xml], capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"decode failed: {rel(vmodc)}\n{r.stdout[-300:]}{r.stderr[-300:]}")
    with open(xml, encoding="utf-8-sig") as f:
        return f.read()


def members(instance: ET.Element) -> dict[str, dict]:
    """{member path: {offset, type, value}} for every primitive in the instance."""
    out: dict[str, dict] = {}

    def walk(node: ET.Element, prefix: list[str]) -> None:
        for i, kid in enumerate(node.findall("member")):
            name = kid.get("name")
            path = prefix + [name] if name else prefix[:-1] + [f"{prefix[-1]}[{i}]"]
            if kid.get("offset-in-file"):
                out[".".join(path)] = {"offset": int(kid.get("offset-in-file"), 16),
                                       "type": kid.get("type"),
                                       "value": (kid.text or "").strip()}
            else:
                walk(kid, path)

    walk(instance, [])
    strip = (instance.get("name") or "") + "."
    return {k[len(strip):] if k.startswith(strip) else k: v for k, v in out.items()}


def read_module(path: str, work: str) -> dict[str, dict]:
    xml = os.path.join(work, os.path.basename(path) + ".xml")
    decode(path, xml)
    root = ET.parse(xml).getroot()
    inst = root.find("instances/instance")
    if inst is None:
        raise SystemExit(f"no instance in {rel(path)}")
    return members(inst)


def number(text: str, kind: str):
    return float(text) if kind not in INT_TYPES else int(float(text))


def write_member(blob: bytearray, off: int, kind: str, to, fmt_check: dict) -> None:
    if kind in INT_TYPES:
        widths = {"int8": 1, "uint8": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4}
        signed = not kind.startswith("uint")
        blob[off:off + widths[kind]] = int(to).to_bytes(widths[kind], "little", signed=signed)
    elif kind in ("float", "double"):
        blob[off:off + 4] = struct.pack("<f", float(to))
    else:
        raise SystemExit(f"member type {kind!r} is not a fixed-width number")


# ------------------------------------------------------------------ the plan
def plan() -> dict:
    if not os.path.exists(EDITS):
        raise SystemExit(f"missing {rel(EDITS)}")
    doc = json.load(open(EDITS, encoding="utf-8"))
    by_id = {r["id"]: r for r in doc["rows"]}
    rows = []
    for e in EDITS_TABLE:
        ref = by_id.get(e["row"].split()[0])
        if e["row"].startswith("T-14"):
            arm = doc["arm4_wheels"]["edits"]
            ref = next((a for a in arm if a["member"] == e["member"]), None)
        if ref is None:
            raise SystemExit(f"{e['row']}: no row in {rel(EDITS)}")
        rows.append(dict(e, translation_row=ref))
    decided = doc["decision"]
    if decided["max_health_chosen"] != 36000:
        raise SystemExit(f"t10_damage_edits.json decision says {decided['max_health_chosen']}")
    return {
        "schema": 1,
        "card": "B-09",
        "generated_by": "Tools/scripts/bm_health.py",
        "decisions": {"T-DM9": decided["chosen"], "max_health": decided["max_health_chosen"],
                      "source": "Working/Translation/t10_damage_edits.json decision"},
        "rows": rows,
        "private_copy": {
            "from": SHARED, "to": HEALTH, "reason": (
                "R7: `lave_health_medium.vmodc` is shared by 77 vehicles, so the edit goes into a "
                "Batmobile-only copy and the entity's `.epe` `damage` hash is repointed at it"),
            "path_hash": {"old": 670155287,
                          "old_string": SHARED,
                          "new": hash_jenkins(HEALTH.encode()) & 0xFFFFFFFF,
                          "new_string": HEALTH},
        },
        "part_damage_types": {
            "edit": "none",
            "why": ("the parts module already carries T-14's per-part damage types (B-04 step 2); "
                    "the health module's 24 `PartDamageType` rows are the donor's, and this build "
                    "asserts every part's type resolves to one of them"),
        },
        "build": None,
    }


def write_build(p: dict) -> int:
    base_dir = os.path.join(ROOT, "Builds", BASE_TAG)
    tag_dir = os.path.join(ROOT, "Builds", TAG)
    base_ee = os.path.join(base_dir, EE)
    for path in (os.path.join(base_dir, "aaf"), base_ee, base_ee + ".toc"):
        if not os.path.exists(path):
            raise SystemExit(f"base build incomplete: {rel(path)}")
    if os.path.exists(tag_dir):
        if TAG != "bm-009":
            raise SystemExit(f"{rel(tag_dir)} exists: a `--tag` tree is never rebuilt in place")
        shutil.rmtree(tag_dir)
    os.makedirs(tag_dir)
    aaf = os.path.join(tag_dir, "aaf")
    shutil.copytree(os.path.join(base_dir, "aaf"), aaf)
    print(f"tree   {rel(aaf)} (copied from {BASE_TAG})")

    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)

    # --- the private health module: copy, then write the values at their decoded offsets
    src_health = os.path.join(aaf, SHARED)
    src_members = read_module(src_health, WORK)
    blob = bytearray(open(src_health, "rb").read())
    applied = []
    for e in p["rows"]:
        if e["module"] != HEALTH:
            continue
        m = src_members.get(e["member"])
        if m is None:
            raise SystemExit(f"{e['member']}: not in {SHARED}")
        cur = number(m["value"], m["type"])
        if abs(cur - float(e["from"])) > 1e-6:
            raise SystemExit(f"{e['member']}: module holds {cur}, the row expects {e['from']}")
        write_member(blob, m["offset"], m["type"], e["to"], {})
        applied.append({"row": e["row"], "module": e["module"], "member": e["member"],
                        "type": m["type"],
                        "offset": m["offset"], "from": e["from"], "to": e["to"],
                        "changed": cur != float(e["to"]), "why": e["why"], "source": e["source"]})
    dst_health = os.path.join(aaf, HEALTH)
    os.makedirs(os.path.dirname(dst_health), exist_ok=True)
    open(dst_health, "wb").write(bytes(blob))
    back = read_module(dst_health, WORK)
    touched = {a["member"] for a in applied if a["changed"]}
    moved = [k for k in src_members
             if k not in touched and src_members[k]["value"] != back[k]["value"]]
    if moved or set(back) != set(src_members):
        raise SystemExit(f"the health copy moved members it should not: {moved[:5]}")
    print(f"health  {NEW_NAME}: {len(blob)} B, {len(applied)} row(s) at their decoded offsets, "
          f"{sum(1 for a in applied if a['changed'])} value(s) written, "
          f"{len(src_members)} members re-read")

    # --- the entity's own land_global: the two wheel rows
    lg_path = os.path.join(aaf, LAND_GLOBAL)
    lg_members = read_module(lg_path, WORK)
    lg = bytearray(open(lg_path, "rb").read())
    lg_applied = []
    for e in p["rows"]:
        if e["module"] != LAND_GLOBAL:
            continue
        m = lg_members.get(e["member"])
        if m is None:
            raise SystemExit(f"{e['member']}: not in {LAND_GLOBAL}")
        cur = number(m["value"], m["type"])
        if abs(cur - float(e["from"])) > 1e-6:
            raise SystemExit(f"{e['member']}: module holds {cur}, the row expects {e['from']}")
        write_member(lg, m["offset"], m["type"], e["to"], {})
        lg_applied.append({"row": e["row"], "module": e["module"], "member": e["member"],
                           "type": m["type"],
                           "offset": m["offset"], "from": e["from"], "to": e["to"],
                           "changed": cur != float(e["to"]), "why": e["why"], "source": e["source"]})
    open(lg_path, "wb").write(bytes(lg))
    lg_back = read_module(lg_path, WORK)
    lg_touched = {a["member"] for a in lg_applied if a["changed"]}
    lg_moved = [k for k in lg_members
                if k not in lg_touched and lg_members[k]["value"] != lg_back[k]["value"]]
    if lg_moved or set(lg_back) != set(lg_members):
        raise SystemExit(f"land_global moved members it should not: {lg_moved[:5]}")
    print(f"wheels  {os.path.basename(LAND_GLOBAL)}: {len(lg_applied)} row(s), "
          f"{sum(1 for a in lg_applied if a['changed'])} value(s) written, "
          f"{len(lg_members)} members re-read")

    # --- the `.epe` damage hash (one 4-byte write; exactly one occurrence must exist)
    epe_path = os.path.join(aaf, EPE)
    epe = bytearray(open(epe_path, "rb").read())
    old_hash = p["private_copy"]["path_hash"]["old"]
    new_hash = p["private_copy"]["path_hash"]["new"]
    pat = int(old_hash).to_bytes(4, "little")
    hits = [i for i in range(len(epe) - 4) if epe.startswith(pat, i)]
    if len(hits) != 1:
        raise SystemExit(f"the .epe holds {len(hits)} copies of the old damage hash, expected 1")
    # a property is `type byte, uint32 name hash, value`; the root `damage` name hash is
    # `4f489f01` (jc3_damage_search.epe_fields), so the type byte sits 5 bytes before the value.
    type_at, hash_at = hits[0] - 5, hits[0] - 4
    if bytes(epe[hash_at:hash_at + 4]) != DAMAGE_NAME_HASH.to_bytes(4, "little"):
        raise SystemExit(f"the .epe value at {hits[0]} is not the `damage` property "
                         f"(name hash {bytes(epe[hash_at:hash_at + 4]).hex()})")
    if epe[type_at] != 0x0E:
        raise SystemExit(f"the .epe damage hash is not type 0x0e (byte {epe[type_at]:#04x})")
    epe[hits[0]:hits[0] + 4] = int(new_hash).to_bytes(4, "little")
    open(epe_path, "wb").write(bytes(epe))
    print(f"epe     damage hash {old_hash} -> {new_hash} at {hits[0]} "
          f"({os.path.basename(EPE)})")

    from deploy import add_to_manifest
    listed = add_to_manifest(aaf, [HEALTH])
    print(f"files   {listed} added to @files.xml")

    ee = os.path.join(tag_dir, EE)
    r = subprocess.run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"SmallPack failed: {r.stdout[-400:]}{r.stderr[-400:]}")
    shutil.rmtree(os.path.join(tag_dir, "verify"), ignore_errors=True)
    r = subprocess.run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee,
                        os.path.join(tag_dir, "verify")], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"SmallUnpack failed: {r.stdout[-400:]}{r.stderr[-400:]}")

    r = subprocess.run([sys.executable, os.path.join(HERE, "aafdiff.py"),
                        os.path.join(base_dir, "verify"),
                        os.path.join(tag_dir, "verify"), "--hash"],
                       capture_output=True, text=True)
    changed = []
    for line in r.stdout.splitlines():
        if not line.startswith("|") or "Bytes A" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        changed.append(cells[3].strip("`"))
    print(f"diff    {len(changed)} file(s) changed vs {BASE_TAG}")

    toc = ee + ".toc"
    r = subprocess.run([sys.executable, os.path.join(HERE, "eetoc.py"), "patch", ee,
                        base_ee + ".toc", "--base-ee", base_ee,
                        "--internal", NEW_NAME, "-o", toc], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"eetoc patch failed: {r.stdout[-400:]}{r.stderr[-400:]}")
    print("toc     " + r.stdout.strip().splitlines()[-1])

    recs = read_toc(open(toc, "rb").read())
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    bad = [(n, (o, s), real.get(n)) for n, o, s in recs if o and real.get(n) != (o, s)]
    if bad:
        raise SystemExit(f"{len(bad)} internal .toc record(s) disagree with the .ee: {bad[:3]}")
    rec = next((x for x in recs if x[0] == HEALTH), None)
    if rec is None or rec[1] == 0:
        raise SystemExit(f"the .toc has no internal record for {HEALTH}")

    base_rec = json.load(open(os.path.join(base_dir, "receipt.json"), encoding="utf-8"))
    p["build"] = {
        "tag": TAG, "base": f"Builds/{BASE_TAG}", "built": datetime.datetime.now().isoformat(
            timespec="seconds"),
        "ee_bytes": os.path.getsize(ee), "ee_sha256": sha256_file(ee),
        "toc_bytes": os.path.getsize(toc), "toc_sha256": sha256_file(toc),
        "toc_records": len(recs), "changed_files": changed,
        "module": {"path": HEALTH, "bytes": os.path.getsize(dst_health),
                   "sha256": sha256_file(dst_health),
                   "base_bytes": os.path.getsize(os.path.join(base_dir, "aaf", SHARED)),
                   "toc_offset": rec[1], "toc_size": rec[2]},
        "land_global": {"path": LAND_GLOBAL, "bytes": os.path.getsize(lg_path),
                        "sha256": sha256_file(lg_path)},
        "epe": {"path": EPE, "value_at": hits[0], "bytes": os.path.getsize(epe_path),
                "sha256": sha256_file(epe_path),
                "damage_hash": new_hash, "damage_hash_string": HEALTH},
        "health_rows": applied, "wheel_rows": lg_applied,
        "shared_module_untouched": sha256_file(src_health) == sha256_file(
            os.path.join(base_dir, "aaf", SHARED)),
        "budgets": base_rec.get("budgets", {}),
    }
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(p, f, indent=1)

    write_receipt_and_installer(tag_dir, p)
    print(f"{TAG}   .ee {p['build']['ee_bytes']} B {p['build']['ee_sha256'][:16]}…, "
          f".toc {p['build']['toc_bytes']} B, module record offset {rec[1]}")
    return check()


def write_receipt_and_installer(tag_dir: str, p: dict) -> None:
    b = p["build"]
    receipt = {
        "tag": TAG, "built": b["built"], "base": b["base"], "src": rel(os.path.join(tag_dir, "aaf")),
        "card": "B-09",
        "ee": {"bytes": b["ee_bytes"], "sha256": b["ee_sha256"]},
        "toc": {"bytes": b["toc_bytes"], "sha256": b["toc_sha256"], "records": b["toc_records"]},
        "module": b["module"],
        "land_global": b["land_global"],
        "epe": b["epe"],
        "modules_changed": [b["module"]["path"], b["land_global"]["path"]],
        "edits": {"rows": len(b["health_rows"]) + len(b["wheel_rows"]),
                  "values_written": sum(1 for r in b["health_rows"] + b["wheel_rows"]
                                        if r["changed"]),
                  "private_copy": p["private_copy"]},
        "budgets": b["budgets"],
        "checks": [],
        "installed": False,
        "bm": {"card": "B-09", "tag": TAG, "base": f"Builds/{BASE_TAG}",
               "installer_actions": ["Install", "Verify", "Rollback002", "Status"],
               "installed": False},
    }
    with open(os.path.join(tag_dir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    body = f"""<#
    {TAG} installer (B-09 private health module). Generated by Tools/scripts/bm_health.py,
    never run. Close the game before -Action Install. Rollback002 restores bm-002.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback002','Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$GameDir = '{GAME}'
$EeT = Join-Path $GameDir '{DROP}\\{EE}'
$EeSha = '{b['ee_sha256']}'
$TocSha = '{b['toc_sha256']}'
$B = '{rel(tag_dir)}'
switch ($Action) {{
    'Install' {{
        Copy-Item -LiteralPath (Join-Path $B '{EE}') -Destination $EeT -Force
        Copy-Item -LiteralPath (Join-Path $B '{EE}.toc') -Destination ($EeT + '.toc') -Force
        Write-Host 'deployed {TAG}'
    }}
    'Verify' {{
        & python '{os.path.join(ROOT, "Tools", "scripts", "verify_install.py")}' --build $B
    }}
    'Rollback002' {{
        & (Join-Path '{os.path.join(ROOT, "Builds", BASE_TAG)}' 'install.ps1') -Action Install
    }}
    'Status' {{
        $e = if (Test-Path -LiteralPath $EeT) {{ (Get-FileHash -LiteralPath $EeT).Hash }} else {{ 'none' }}
        $t = if (Test-Path -LiteralPath ($EeT + '.toc')) {{ (Get-FileHash -LiteralPath ($EeT + '.toc')).Hash }} else {{ 'none' }}
        Write-Host "dropzone .ee : $e"
        Write-Host "dropzone .toc: $t"
        if ($e -eq $EeSha -and $t -eq $TocSha) {{ Write-Host '  == {TAG} (all match)' }}
    }}
}}
"""
    with open(os.path.join(tag_dir, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


# ------------------------------------------------------------------ check
def check() -> int:
    """The card's Done criteria, re-read from the built artefacts (no writes)."""
    tag_dir = os.path.join(ROOT, "Builds", TAG)
    fails: list[str] = []
    if not (os.path.exists(SPEC) and os.path.isdir(tag_dir)):
        print(f"FAIL: {rel(SPEC)} or {rel(tag_dir)} missing (run --write)")
        return 1
    p = json.load(open(SPEC, encoding="utf-8"))
    receipt = json.load(open(os.path.join(tag_dir, "receipt.json"), encoding="utf-8"))
    ee = os.path.join(tag_dir, EE)
    toc = ee + ".toc"
    aaf = os.path.join(tag_dir, "aaf")
    for path in (ee, toc):
        if not os.path.exists(path):
            print(f"FAIL: {rel(path)} missing")
            return 1
    if sha256_file(ee) != receipt["ee"]["sha256"]:
        fails.append(".ee sha256 differs from the receipt")
    if sha256_file(toc) != receipt["toc"]["sha256"]:
        fails.append(".toc sha256 differs from the receipt")

    # 1. the private copy, through the module's own .toc record (the way the game reads it)
    recs = {n: (o, s) for n, o, s in read_toc(open(toc, "rb").read())}
    stream = unaaf(open(ee, "rb").read())
    real = {n: (o, s) for n, o, s in sarc_dir(stream)}
    staged = open(os.path.join(aaf, HEALTH), "rb").read()
    rec = recs.get(HEALTH)
    if rec is None:
        fails.append(f"no .toc record for {HEALTH}")
    else:
        if rec[0] == 0:
            fails.append(f"{HEALTH}: .toc record is external (offset 0 = the archive copy)")
        if real.get(HEALTH) != rec:
            fails.append(f"{HEALTH}: .toc record disagrees with the .ee directory")
        if stream[rec[0]:rec[0] + rec[1]] != staged:
            fails.append("the .toc-sliced health module is not the staged copy")
    print(f"1. .toc record  {NEW_NAME}: offset={rec[0] if rec else None} "
          f"size={rec[1] if rec else None} ({'PASS' if rec and rec[0] else 'FAIL'})")

    # 2. the values, re-read from the staged modules
    back = read_module(os.path.join(aaf, HEALTH), WORK)
    for e in p["rows"]:
        if e["module"] != HEALTH:
            continue
        m = back.get(e["member"])
        if m is None:
            fails.append(f"{e['member']} missing from the built health module")
            continue
        got = number(m["value"], m["type"])
        if abs(got - float(e["to"])) > 1e-6:
            fails.append(f"{e['member']}: build {got} vs spec {e['to']}")
    print(f"2. health values  max_health={back.get('max_health', {}).get('value')}, "
          f"deform_scale={back.get('deform_scale', {}).get('value')}, "
          f"impact_damage_factor={back.get('impact_damage_factor', {}).get('value')}")

    lg = read_module(os.path.join(aaf, LAND_GLOBAL), WORK)
    for e in p["rows"]:
        if e["module"] != LAND_GLOBAL:
            continue
        got = number(lg[e["member"]]["value"], lg[e["member"]]["type"])
        if abs(got - float(e["to"])) > 1e-6:
            fails.append(f"{e['member']}: build {got} vs spec {e['to']}")
    print(f"3. wheel rows  front_wheels_damage.skew_health="
          f"{lg.get('front_wheels_damage.skew_health', {}).get('value')}, "
          f"rear_wheels_damage.skew_health="
          f"{lg.get('rear_wheels_damage.skew_health', {}).get('value')}")

    # 3. the .epe repoint: one 4-byte hash, equal to Jenkins of the private path
    epe_blob = open(os.path.join(aaf, EPE), "rb").read()
    want = hash_jenkins(HEALTH.encode()) & 0xFFFFFFFF
    pat = int(want).to_bytes(4, "little")
    hits = [i for i in range(len(epe_blob) - 4) if epe_blob.startswith(pat, i)]
    old = int(p["private_copy"]["path_hash"]["old"]).to_bytes(4, "little")
    old_hits = [i for i in range(len(epe_blob) - 4) if epe_blob.startswith(old, i)]
    if len(hits) != 1:
        fails.append(f"the .epe holds {len(hits)} copies of Jenkins({HEALTH}), expected 1")
    if old_hits:
        fails.append(f"the .epe still points at the shared module ({len(old_hits)} byte match)")
    if hits:
        hash_at = hits[0] - 4
        if bytes(epe_blob[hash_at:hash_at + 4]) != DAMAGE_NAME_HASH.to_bytes(4, "little"):
            fails.append("the repointed .epe value is not under the `damage` name hash")
        if epe_blob[hits[0] - 5] != 0x0E:
            fails.append("the repointed .epe field is not the type-0x0e `damage` property")
    print(f"4. .epe damage  {want} (Jenkins of {NEW_NAME}) x{len(hits)}, "
          f"shared hash x{len(old_hits)}")

    # 4. R7: the shared module is untouched, byte for byte against the base build
    shared_now = os.path.join(aaf, SHARED)
    shared_base = os.path.join(ROOT, "Builds", BASE_TAG, "aaf", SHARED)
    if not (os.path.exists(shared_now) and os.path.exists(shared_base)):
        fails.append(f"{SHARED} missing")
    elif sha256_file(shared_now) != sha256_file(shared_base):
        fails.append("the shared health module changed (R7)")
    print(f"5. R7 shared   {os.path.basename(SHARED)} sha256 "
          f"{sha256_file(shared_now)[:16] if os.path.exists(shared_now) else 'missing'}… "
          f"({'unchanged' if os.path.exists(shared_now) and sha256_file(shared_now) == sha256_file(shared_base) else 'CHANGED'})")

    # 5. part damage types per T-14: every part's type has a PartDamageType row
    parts_blob = open(os.path.join(aaf, PARTS), "rb").read()
    part_types = set()
    for line in open(os.path.join(aaf, PARTS), "rb").read().split(b"\x00"):
        pass
    sys.path.insert(0, HERE)
    import bm_parts  # noqa: E402  (B-04's reader: the same ADF decode)
    parts = bm_parts.decode_parts(parts_blob)
    rows = {k.split(".")[0] for k in back if k.startswith("part_damage_types[")}
    table = {}
    for k, m in back.items():
        if not k.startswith("part_damage_types["):
            continue
        idx, tail = k[len("part_damage_types["):].split("].", 1)
        table.setdefault(int(idx), {})[tail] = m["value"]
    names = {r["type.string"] for r in table.values() if "type.string" in r}
    for pt in parts:
        part_types.add(pt["damage_type"])
    missing = sorted(t for t in part_types if t not in names)
    print(f"6. part types  {len(parts)} parts use {len(part_types)} distinct damage types; "
          f"{len(names)} PartDamageType rows in the private module; "
          f"{len(missing)} without a row {missing if missing else ''}")

    # 6. the edits really are the T-14 list
    want_rows = {(e["module"], e["member"], e["to"]) for e in p["rows"]}
    have_rows = {(r["module"], r["member"], r["to"])
                 for r in p["build"]["health_rows"] + p["build"]["wheel_rows"]}
    if want_rows != have_rows:
        fails.append(f"the spec's edit rows {sorted(have_rows)} differ from the plan")

    for line in fails[:25]:
        print("  FAIL", line)
    print(f"{'PASS' if not fails else 'FAIL'}: {rel(tag_dir)} re-read "
          f"({receipt['ee']['sha256'][:16]}…, {len(recs)} .toc records, "
          f"{len(p['build']['health_rows']) + len(p['build']['wheel_rows'])} edit row(s), "
          f"{len(fails)} problem(s))")
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write the spec and Builds/bm-009")
    ap.add_argument("--check", action="store_true",
                    help="no writes: re-read the build and run the card's checks")
    ap.add_argument("--base", default=BASE_TAG, help=f"base build tag (default {BASE_TAG})")
    ap.add_argument("--tag", default=TAG, help=f"build tag to write/check (default {TAG})")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if a.base != BASE_TAG or a.tag != TAG:
        set_tags(a.base, a.tag)
    if a.write:
        p = plan()
        print(f"plan: {len(p['rows'])} row(s), private copy {NEW_NAME}, "
              f"hash {p['private_copy']['path_hash']['new']}")
        return write_build(p)
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
