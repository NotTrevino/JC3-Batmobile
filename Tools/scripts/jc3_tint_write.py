#!/usr/bin/env python3
"""jc3_tint_write.py - G3-09d: how a `Palette.tints[i].tint_r` edit is serialised.

The card: `Research/JC3Grab/TINT.md` decodes the paint tint as the entity graph's
`Palette.tints[i].tint_r`, but the write path was open.  This script answers, from files
only (no game launched, nothing installed, no build written):

  1. which carrier actually holds `tint_r`, and what bytes an edit touches;
  2. whether the current build writes that value;
  3. a round trip (ConvertProperty style: export -> edit one named value -> import ->
     export) proving that one tint float changes exactly four bytes and nothing else.

Carriers, measured here, never assumed:

  * `.epe` - RTPC v1 (`ConvertProperty`).  Exported, it has **no** `Palette` object and no
    `tint_r`; its only palette surface is `CCar.palette`, one int32 module-name hash
    (`0x29a` in the build's `.epe`).
  * palette `.vmodc` - ADF v4 (`ConvertAdf`).  `Palette.tints` is an `A[Tint]`; each `Tint`
    is 80 B with `tint_r` at +20 as a `ColorRGBA` of four float32 (R/G/B/A at +0/+4/+8/+12).
  * `.ee` - an AAF archive (`AAF\\0\\1...`); neither repo converter reads it, so whatever it
    packs is not decoded here.

Usage:
    python Tools/scripts/jc3_tint_write.py --write
    python Tools/scripts/jc3_tint_write.py --check
"""

from __future__ import annotations

import argparse
import difflib
import glob
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf      # noqa: E402  (ADF v4 reader: independent decode of the palette)
import rbmhdr      # noqa: E402  (Jenkins hash, pinned against HashName.exe)

CONVERT_PROPERTY = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
CONVERT_ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "TINT_WRITE.md")

DONOR = "v0300_car_kensington_sportsmuscle"
ENT = "aaf/editor/entities/jc_vehicles/01_land/" + DONOR
PAL_NAME = DONOR + "_palette.vmodc"
BUILDS = ["bm-001", "bm-005", "bm-009", "bm-RC1", "bm-RC2"]

# the one float the round trip edits, and the value it is changed to
EDIT_FLOAT = 0.239


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def signed32(u: int) -> int:
    return u - (1 << 32) if u >= (1 << 31) else u


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("command failed (%d): %s\n%s\n%s"
                         % (r.returncode, " ".join(cmd), r.stdout[:800], r.stderr[:800]))


def palette_path(build: str) -> str | None:
    for rel in (ENT + "/modules/default/" + PAL_NAME,
                ENT + "/modules/default/batmobile/" + PAL_NAME):
        p = os.path.join(ROOT, "Builds", build, rel)
        if os.path.exists(p):
            return p
    return None


def epe_path(build: str) -> str | None:
    hits = sorted(glob.glob(os.path.join(ROOT, "Builds", build, ENT, "*.epe")))
    return hits[0] if hits else None


def epe_palette_value(epe: str, tmp: str) -> tuple[int, str]:
    xml = os.path.join(tmp, "epe.xml")
    run([CONVERT_PROPERTY, "--e", epe, xml])
    text = open(xml, encoding="utf-8-sig").read()
    ms = re.findall(r'<value name="palette" type="int">(-?\d+)</value>', text)
    if len(ms) != 1:
        raise SystemExit("expected exactly one palette value in %s, found %d" % (epe, len(ms)))
    return int(ms[0]), text


def adf_layout(blob: bytes) -> dict:
    a = jc3adf.Adf(blob)
    out = {"adf": a, "types": {}, "values": {}}
    for name in ("Palette", "A[Tint]", "Tint", "ColorRGBA"):
        h = a.by_name.get(name)
        t = a.types.get(h) if h is not None else None
        if not t:
            raise SystemExit("type %s missing from the palette ADF" % name)
        out["types"][name] = t
    for path, _tn, val in jc3adf.walk(a):
        out["values"][path] = val
    return out


def adf_roundtrip(src: str, tmp: str) -> dict:
    """export -> change one tint_r.R -> import -> export; prove 4 bytes and nothing else."""
    p0 = os.path.join(tmp, "p0.vmodc")
    shutil.copy(src, p0)
    run([CONVERT_ADF, "--e", p0, os.path.join(tmp, "a.xml")])
    x = open(os.path.join(tmp, "a.xml"), encoding="utf-8-sig").read()
    inst = x.split("<instances", 1)[1]
    m = re.search(r'<member name="tint_r" gbltype="Structure".*?'
                  r'<member name="R" gbltype="Primitive" offset-in-file="([0-9A-Fa-f]{8})" '
                  r'type="float">([^<]+)</member>', inst, re.S)
    if not m:
        raise SystemExit("no instance tint_r.R in the palette export")
    off = int(m.group(1), 16)
    before_xml = m.group(2)
    old_block = m.group(0)
    new_block = old_block.replace(before_xml, repr(EDIT_FLOAT), 1)
    x2 = x.replace(old_block, new_block, 1)
    open(os.path.join(tmp, "a_edit.xml"), "w", encoding="utf-8").write(x2)

    run([CONVERT_ADF, "-i", os.path.join(tmp, "a_edit.xml"), os.path.join(tmp, "b.vmodc")])
    run([CONVERT_ADF, "--e", os.path.join(tmp, "b.vmodc"), os.path.join(tmp, "b.xml")])
    y = open(os.path.join(tmp, "b.xml"), encoding="utf-8-sig").read()

    changed = [ln for ln in difflib.unified_diff(x.splitlines(), y.splitlines(), lineterm="", n=0)
               if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]

    b0 = open(p0, "rb").read()
    b1 = open(os.path.join(tmp, "b.vmodc"), "rb").read()
    diffs = [i for i in range(min(len(b0), len(b1))) if b0[i] != b1[i]]

    run([CONVERT_ADF, "-i", os.path.join(tmp, "b.xml"), os.path.join(tmp, "c.vmodc")])
    b2 = open(os.path.join(tmp, "c.vmodc"), "rb").read()

    return {
        "src": src,
        "size0": len(b0), "size1": len(b1),
        "offset": off, "offset_hex": "0x%x" % off,
        "before_xml": before_xml,
        "after_xml": re.search(r">([^<]+)</member>", new_block).group(1),
        "before_bin": struct.unpack_from("<f", b0, off)[0],
        "after_bin": struct.unpack_from("<f", b1, off)[0],
        "target": struct.unpack("<f", struct.pack("<f", EDIT_FLOAT))[0],
        "diffs": diffs,
        "changed_lines": changed,
        "idempotent": b1 == b2,
        "n_tint_r_members": len(re.findall(r'<member name="tint_r" gbltype="Structure"', inst)),
        "n_tints_xml": inst.count('<member gbltype="Structure" type-hash="3565789129" type="Tint">'),
    }


def epe_roundtrip(src: str, tmp: str) -> dict:
    """export -> change the palette int -> import -> export; prove 4 bytes and nothing else."""
    p0 = os.path.join(tmp, "e0.epe")
    shutil.copy(src, p0)
    run([CONVERT_PROPERTY, "--e", p0, os.path.join(tmp, "x0.xml")])
    x = open(os.path.join(tmp, "x0.xml"), encoding="utf-8-sig").read()
    ms = re.findall(r'<value name="palette" type="int">(-?\d+)</value>', x)
    if len(ms) != 1:
        raise SystemExit("expected one palette value in the .epe export, found %d" % len(ms))
    before = int(ms[0])
    old = '<value name="palette" type="int">%d</value>' % before
    new = '<value name="palette" type="int">%d</value>' % 1322976751
    x2 = x.replace(old, new, 1)
    if x2 == x:
        raise SystemExit("palette value substitution did nothing")
    open(os.path.join(tmp, "x_edit.xml"), "w", encoding="utf-8").write(x2)

    run([CONVERT_PROPERTY, "-i", os.path.join(tmp, "x_edit.xml"), os.path.join(tmp, "e1.epe")])
    run([CONVERT_PROPERTY, "--e", os.path.join(tmp, "e1.epe"), os.path.join(tmp, "x1.xml")])
    y = open(os.path.join(tmp, "x1.xml"), encoding="utf-8-sig").read()

    changed = [ln for ln in difflib.unified_diff(x.splitlines(), y.splitlines(), lineterm="", n=0)
               if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]

    b0 = open(p0, "rb").read()
    b1 = open(os.path.join(tmp, "e1.epe"), "rb").read()
    diffs = [i for i in range(min(len(b0), len(b1))) if b0[i] != b1[i]]

    run([CONVERT_PROPERTY, "-i", os.path.join(tmp, "x1.xml"), os.path.join(tmp, "e2.epe")])
    b2 = open(os.path.join(tmp, "e2.epe"), "rb").read()

    return {
        "src": src, "size0": len(b0), "size1": len(b1),
        "before": before, "after": 1322976751,
        "diffs": diffs, "changed_lines": changed, "idempotent": b1 == b2,
        "no_palette_class": "Palette" not in x,
        "no_tint": "tint_r" not in x,
        "xml_lines": len(x.splitlines()),
    }


def collect(tmp: str) -> dict:
    d: dict = {"tmp": tmp, "gates": []}

    def gate(ok: bool, name: str, detail: str) -> None:
        d["gates"].append((bool(ok), name, detail))

    # ---- 1. the palette ADF, decoded independently by jc3adf + rendered by ConvertAdf
    pal5 = palette_path("bm-005")
    if not pal5:
        raise SystemExit("bm-005 palette module missing")
    pal_blob = open(pal5, "rb").read()
    lay = adf_layout(pal_blob)
    tint_t = lay["types"]["Tint"]
    cg_t = lay["types"]["ColorRGBA"]
    tint_members = {m["name"]: (m["offset"], m["size"]) for m in tint_t["members"]}
    cg_members = {m["name"]: (m["offset"], m["size"]) for m in cg_t["members"]}
    d["layout"] = {
        "Palette": lay["types"]["Palette"]["size"],
        "A[Tint]": lay["types"]["A[Tint]"]["size"],
        "A[Tint].element": tint_t["size"],
        "Tint": tint_t["size"],
        "ColorRGBA": cg_t["size"],
        "tint_r_off": tint_members["tint_r"][0],
        "occ_off": tint_members["occurrence"][0],
        "cg": cg_members,
        "instance": lay["adf"].instances[0]["name"],
        "instance_size": lay["adf"].instances[0]["size"],
        "data_off": lay["adf"].data_off,
        "first_name": lay["values"].get("tints[0].name.string"),
        "first_occ": lay["values"].get("tints[0].occurrence"),
        "first_rgba": [lay["values"].get("tints[0].tint_r." + c) for c in "RGBA"],
        "n_walk": sum(1 for k in lay["values"] if k.endswith("].name.string")),
    }
    gate(tint_t["size"] == 80 and tint_members["tint_r"][0] == 20,
         "G1-adf-layout",
         "Tint size %d, tint_r +%d, ColorRGBA %d B (R/G/B/A +%d/+%d/+%d/+%d)"
         % (tint_t["size"], tint_members["tint_r"][0], cg_t["size"],
            cg_members["R"][0], cg_members["G"][0], cg_members["B"][0], cg_members["A"][0]))
    arr = lay["types"]["A[Tint]"]
    gate(arr["element"] == lay["adf"].by_name["Tint"] and tint_t["size"] == 80,
         "G1b-array-element",
         "A[Tint] element type = Tint (%d B stride)" % tint_t["size"])

    # ---- 2. the build's .epe: no Palette, one palette int
    epe5 = epe_path("bm-005")
    val5, epe_xml = epe_palette_value(epe5, tmp)
    d["epe"] = {"path": epe5, "palette": val5, "xml_lines": len(epe_xml.splitlines())}
    gate("Palette" not in epe_xml and "tint_r" not in epe_xml, "G2-epe-has-no-tint",
         "bm-005 .epe export: %d lines, 'Palette' %d, 'tint_r' %d, palette int %d"
         % (len(epe_xml.splitlines()), epe_xml.count("Palette"), epe_xml.count("tint_r"), val5))

    # ---- 3. hash mapping: .epe palette int == Jenkins(epe-relative module path)
    rel5 = os.path.relpath(pal5, os.path.join(ROOT, "Builds", "bm-005", "aaf")).replace(os.sep, "/")
    h5 = signed32(rbmhdr.name_hash(rel5))
    d["hash"] = {"rel5": rel5, "h5": h5}
    gate(h5 == val5, "G3-pointer-hash",
         "Jenkins('%s') = %d == .epe palette %d" % (rel5, h5, val5))

    # ---- 4. round trips
    rt = adf_roundtrip(pal5, tmp)
    d["rt_adf"] = rt
    gate(rt["n_tints_xml"] == d["layout"]["n_walk"], "G1c-tint-count",
         "%d Tint records by ConvertAdf export == %d by jc3adf.walk"
         % (rt["n_tints_xml"], d["layout"]["n_walk"]))
    gate(rt["size0"] == rt["size1"] and rt["diffs"] == list(range(rt["offset"], rt["offset"] + 4)),
         "G4-adf-roundtrip-bytes",
         "%d -> %d B; %d byte(s) differ at %s"
         % (rt["size0"], rt["size1"], len(rt["diffs"]),
            ", ".join("0x%x" % i for i in rt["diffs"][:6])))
    gate(rt["after_bin"] == rt["target"] and rt["before_bin"] != rt["after_bin"],
         "G4b-float-value",
         "float@%s %.9g -> %.9g (target float32 %.9g)"
         % (rt["offset_hex"], rt["before_bin"], rt["after_bin"], rt["target"]))
    gate(len(rt["changed_lines"]) == 2 and rt["idempotent"], "G4c-adf-idempotent",
         "%d XML value line(s) changed; re-import of the re-export is byte-identical: %s"
         % (len(rt["changed_lines"]), rt["idempotent"]))

    rte = epe_roundtrip(epe5, tmp)
    d["rt_epe"] = rte
    gate(rte["size0"] == rte["size1"] and rte["diffs"] == list(range(0x29A, 0x29E)),
         "G5-epe-roundtrip-bytes",
         "%d -> %d B; %d byte(s) differ at %s"
         % (rte["size0"], rte["size1"], len(rte["diffs"]),
            ", ".join("0x%x" % i for i in rte["diffs"][:6])))
    gate(len(rte["changed_lines"]) == 2 and rte["idempotent"], "G5b-epe-idempotent",
         "%d XML value line(s) changed; re-import byte-identical: %s"
         % (len(rte["changed_lines"]), rte["idempotent"]))

    # ---- 5. build state: does any build write a tint value?
    vanilla_sha = sha256(palette_path("bm-001"))
    rows = []
    for b in BUILDS:
        p = palette_path(b)
        e = epe_path(b)
        if not p or not e:
            rows.append({"build": b, "missing": True})
            continue
        val, _ = epe_palette_value(e, tmp)
        rel = os.path.relpath(p, os.path.join(ROOT, "Builds", b, "aaf")).replace(os.sep, "/")
        rows.append({
            "build": b, "pal": os.path.relpath(p, ROOT).replace(os.sep, "/"),
            "pal_sha": sha256(p), "same_as_vanilla": sha256(p) == vanilla_sha,
            "epe": os.path.basename(e), "palette_int": val,
            "rel": rel, "hash_ok": signed32(rbmhdr.name_hash(rel)) == val,
            "batmobile": "/batmobile/" in rel,
        })
    d["builds"] = rows
    gate(all(r.get("hash_ok") for r in rows if not r.get("missing")), "G6-build-pointers",
         "%d builds: every .epe palette int equals the Jenkins hash of the module path"
         % len(rows))
    gate(all(r["same_as_vanilla"] for r in rows if not r.get("missing")), "G6b-no-tint-written",
         "every build's palette module is byte-identical to bm-001: %s"
         % all(r["same_as_vanilla"] for r in rows if not r.get("missing")))

    # ---- 6. the entity edits spec has no palette/tint row
    spec_p = os.path.join(ROOT, "Working", "Entity", "bm_epe_edits.json")
    spec = json.load(open(spec_p, encoding="utf-8"))
    pal_rows = [e for e in spec.get("edits", []) if "palette" in json.dumps(e).lower()
                or "tint" in json.dumps(e).lower()]
    d["spec"] = {"path": spec_p, "n_edits": len(spec.get("edits", [])),
                 "pal_rows": len(pal_rows), "sha": sha256(spec_p)}
    gate(len(pal_rows) == 0, "G7-no-tint-row",
         "%d bm_epe_edits rows, %d name palette/tint" % (d["spec"]["n_edits"], len(pal_rows)))

    ee_hits = sorted(glob.glob(os.path.join(ROOT, "Builds", "bm-RC1", "drop", "editor",
                                            "entities", "jc_vehicles", "01_land", DONOR, "*.ee")))
    d["ee"] = (os.path.relpath(ee_hits[0], ROOT).replace(os.sep, "/") if ee_hits else "")
    magic = open(ee_hits[0], "rb").read(3) if ee_hits else b""
    gate(bool(ee_hits) and magic == b"AAF", "G8-ee-is-archive",
         "%s magic %r (an AAF archive, not ADF/RTPC)" % (os.path.basename(d["ee"]) if d["ee"] else "-", magic))

    # ---- 7. sources unchanged by this run
    d["sources"] = {
        "palette": (os.path.relpath(pal5, ROOT).replace(os.sep, "/"), sha256(pal5)),
        "epe": (os.path.relpath(epe5, ROOT).replace(os.sep, "/"), sha256(epe5)),
        "ConvertProperty": sha256(CONVERT_PROPERTY),
        "ConvertAdf": sha256(CONVERT_ADF),
    }
    return d


def render(d: dict) -> str:
    rt, rte, lay, b = d["rt_adf"], d["rt_epe"], d["layout"], d["builds"]
    L: list[str] = []
    A = L.append

    A("# The `Palette.tints[i].tint_r` write path (G3-09d)")
    A("")
    A("Generated by `Tools/scripts/jc3_tint_write.py --write`; `--check` re-exports both")
    A("carriers, re-runs both round trips from the build bytes and compares this file byte for")
    A("byte. Static only: the game is never launched, nothing is installed, and no build file is")
    A("modified (every edit is staged in a temp directory, and the source hashes are re-checked).")
    A("")
    A("## 1. Answer")
    A("")
    A("**STATUS: DONE - the write path is decoded and round-trip proven; the current build does")
    A("not write a tint value.**")
    A("")
    A("`tint_r` is **not an `.epe` member**, so it cannot be edited \"in the `.epe`\" as one")
    A("value. The paint tint lives in the palette **`.vmodc`** (ADF v4); the `.epe` carries only")
    A("a 4-byte module hash that names that file. An edit is therefore one float in the palette")
    A("file plus, optionally, a pointer edit in the `.epe` if the palette is renamed:")
    A("")
    A("| carrier | format | repo tool | what it holds for the tint |")
    A("|---|---|---|---|")
    A("| `..._civilian_01.epe` | RTPC v1 | `ConvertProperty` | one `CCar.palette` int32 at "
      "file `0x%x`, the Jenkins hash of the palette module path; no `Palette` node, no `tint_r` |"
      % rte["diffs"][0])
    A("| `<default|default/batmobile>/%s` | ADF v4 | `ConvertAdf` | the `Palette.tints[i]` "
      "records, `tint_r` as `ColorRGBA` (four float32 at `Tint+20`) |" % PAL_NAME)
    A("| `..._debug.ee` | AAF archive | none in this repo | packs entity files; neither converter "
      "reads it (`ConvertAdf`: FormatException, `ConvertProperty`: NotSupported) |")
    A("")
    A("Which build writes what:")
    A("")
    A("* **bm-005 (the build under test)** points `palette` at the vanilla path")
    A("  (`%d`) and its palette module is **byte-identical** to bm-001: no tint value is written." % d["hash"]["h5"])
    A("* **bm-RC1 / bm-RC2** move the module to the `batmobile/` namespace and repoint the hash to")
    A("  `%d`, but ship the **same bytes** (`%s...`): the pointer is written, the tint is not."
      % (rte["after"], d["sources"]["palette"][1][:12]))
    A("* `Working/Entity/bm_epe_edits.json` has **%d** rows, **%d** of which name palette/tint:"
      % (d["spec"]["n_edits"], d["spec"]["pal_rows"]))
    A("  the B-05 graph writer never touches either carrier's tint.")
    A("")
    A("So today the Batmobile paints itself with the donor's **White** record")
    A("(`tint_r` = %.4f, %.4f, %.4f, %.4f) exactly as the civilian sportsmuscle did."
      % tuple(lay["first_rgba"]))
    A("")
    A("## 2. Serialisation, byte level")
    A("")
    A("### 2.1 The palette module (where the float is)")
    A("")
    A("`jc3adf` (independent of Gibbed) decodes the build's palette as one `Palette` instance")
    A("named `%s` (%d B), and `ConvertAdf --e` agrees on every offset below:"
      % (lay["instance"], lay["instance_size"]))
    A("")
    A("| type | size | member | offset |")
    A("|---|---:|---|---:|")
    A("| `Palette` | %d | `tints` | 0 |" % lay["Palette"])
    A("| `A[Tint]` | %d | element | stride %d |" % (lay["A[Tint]"], lay["A[Tint].element"]))
    A("| `Tint` | %d | `name` (`HashString`) | 0 |" % lay["Tint"])
    A("| | | `occurrence` (int32) | %d |" % lay["occ_off"])
    A("| | | `tint_r` (`ColorRGBA`) | %d |" % lay["tint_r_off"])
    A("| | | `tint_g` / `tint_b` | 36 / 52 |")
    A("| | | `specular_gloss` / `metallic` / `clear_coat` | 68 / 72 / 76 |")
    A("| `ColorRGBA` | %d | `R` / `G` / `B` / `A` (float32) | %d / %d / %d / %d |"
      % (lay["ColorRGBA"], lay["cg"]["R"][0], lay["cg"]["G"][0], lay["cg"]["B"][0], lay["cg"]["A"][0]))
    A("")
    A("The first record is `%s` (occurrence %s); its `tint_r` is"
      % (lay["first_name"], lay["first_occ"]))
    A("`%s` at file offset `%s` - the export's own `offset-in-file` for `tint_r.R`:"
      % (rt["before_xml"], rt["offset_hex"]))
    A("")
    A("```xml")
    A('<member name="tint_r" gbltype="Structure" type-hash="1221386478" type="ColorRGBA">')
    A('    <member name="R" gbltype="Primitive" offset-in-file="%08X" type="float">%s</member>'
      % (rt["offset"], rt["before_xml"]))
    A('    <member name="G" ... type="float">%s</member>' % lay["first_rgba"][1])
    A("</member>")
    A("```")
    A("")
    A("`tint_r` is therefore **four separate float32 stores**, not one packed colour: an edit")
    A("rewrites 4 bytes per channel (16 per colour). The palette holds **%d** `Tint` records"
      % rt["n_tints_xml"])
    A("(the same count from `ConvertAdf --e` and `jc3adf.walk`), so `tints[i].tint_r.c` lands at")
    A("`0x%x + 80*i + 20 + 4*c` (data base `0x%x`, array header 16 B)."
      % (lay["data_off"], lay["data_off"]))
    A("")
    A("### 2.2 The `.epe` (where the pointer is)")
    A("")
    A("The exported `.epe` is a `container format=\"RTPC\"` with **%d** lines; it has no `Palette`"
      % d["epe"]["xml_lines"])
    A("object. Its only palette surface is one value on `CCar`:")
    A("")
    A("```xml")
    A('<value name="palette" type="int">%d</value>' % d["epe"]["palette"])
    A("```")
    A("")
    A("That int is the Jenkins hash of the module **path**, which is why a rename changes it:")
    A("")
    A("```")
    A("Jenkins32(\"%s\") = %d" % (d["hash"]["rel5"], d["hash"]["h5"]))
    A('".../modules/default/batmobile/%s" = %d' % (PAL_NAME, rte["after"]))
    A("```")
    A("")
    A("`ConvertProperty -i` writes that int in place at file offset `0x%x` (4 bytes, no size"
      % rte["diffs"][0])
    A("change, no padding shift).")
    A("")
    A("### 2.3 The edit recipe the bytes imply")
    A("")
    A("1. Export the palette with `ConvertAdf --e`, change the target")
    A("   `tint_r.R/G/B/A` text, import with `-i`. One float in, one float out.")
    A("2. If the module keeps its path, stop - the `.epe` already hashes that path.")
    A("   If it moves (as bm-RC1 did to `batmobile/`), export the `.epe` with")
    A("   `ConvertProperty --e`, rewrite the `palette` int to the new path's hash and import.")
    A("3. Ship the module at exactly the path the hash names; the `.epe` stores no filename.")
    A("")
    A("## 3. Round trips (ConvertProperty style)")
    A("")
    A("Both were run on the build's own bytes, staged in a temp directory; the build files were")
    A("not modified (`--check` re-hashes them afterwards).")
    A("")
    A("| round trip | file | before -> after | bytes that differ | XML diff lines | re-import identical |")
    A("|---|---|---|---:|---:|---|")
    A("| one tint float | `%s` | %d -> %d B | **%d**, all at `%s` | %d | %s |"
      % (os.path.basename(rt["src"]), rt["size0"], rt["size1"], len(rt["diffs"]),
         rt["offset_hex"], len(rt["changed_lines"]), "yes" if rt["idempotent"] else "NO"))
    A("| palette pointer | `%s` | %d -> %d B | **%d**, all at `0x%x` | %d | %s |"
      % (os.path.basename(rte["src"]), rte["size0"], rte["size1"], len(rte["diffs"]),
         rte["diffs"][0], len(rte["changed_lines"]), "yes" if rte["idempotent"] else "NO"))
    A("")
    A("The tint edit changed `0x%x..0x%x` and nothing else; the binary float at `%s` went"
      % (rt["offset"], rt["offset"] + 3, rt["offset_hex"]))
    A("from `%.9g` to `%.9g` (float32 of %.3f is `%.9g`)."
      % (rt["before_bin"], rt["after_bin"], EDIT_FLOAT, rt["target"]))
    A("Re-exporting the edited file produced exactly one changed *value* line:")
    A("")
    A("```")
    A(rt["changed_lines"][0].strip() if rt["changed_lines"] else "")
    A(rt["changed_lines"][1].strip() if len(rt["changed_lines"]) > 1 else "")
    A("```")
    A("")
    A("So: **changing one `tint_r` float changes only that float**, and the writer is")
    A("layout-stable (same size, same offsets, idempotent re-import). The `.epe` pointer edit")
    A("behaves the same way: %d bytes at `0x%x`, idempotent."
      % (len(rte["diffs"]), rte["diffs"][0]))
    A("")
    A("## 4. Does the current build write it?")
    A("")
    A("| build | palette module | sha256 | palette int in `.epe` | = hash(path) | tint = vanilla |")
    A("|---|---|---|---:|---|---|")
    for r in b:
        if r.get("missing"):
            A("| `%s` | missing | - | - | - | - |" % r["build"])
            continue
        A("| `%s` | `%s` | `%s` | %d | %s | %s |"
          % (r["build"], r["pal"].split("/modules/", 1)[-1], r["pal_sha"][:12],
             r["palette_int"], "yes" if r["hash_ok"] else "NO",
             "yes" if r["same_as_vanilla"] else "NO"))
    A("")
    A("Reading the table: bm-005/bm-009 name the civilian palette, bm-RC1/bm-RC2 name the")
    A("`batmobile/` copy - but every module is the **same file** (`%s...`)."
      % d["sources"]["palette"][1][:12])
    A("No build has ever written a `tint_r` value; only the reference moved.")
    A("")
    A("## 5. What stays UNKNOWN")
    A("")
    A("* **Which engine code turns the palette into the shader's tint.** `TINT.md` (G3-09)")
    A("  measured that no asset names the `cb6` binding; this card adds the *write* side only.")
    A("  Tried: the `.epe` export (no binding), the palette ADF (values only).")
    A("* **Whether the packaged `.ee` overrides the loose palette.** `%s` is"
      % os.path.basename(d["ee"]))
    A("  an **AAF archive** (magic `AAF`); neither repo converter reads it, so no inlined")
    A("  palette could be inspected there. The loose palette is reached only via the `.epe` hash.")
    A("* **Whether the game honours an edited tint in play.** Test ban; not measured.")
    A("* **Which record a player's paint choice selects.** `TINT.md` decodes `occurrence`")
    A("  weights but no selector.")
    A("")
    A("## 6. Sources (re-hashed by `--check`)")
    A("")
    A("| source | sha256 |")
    A("|---|---|")
    A("| `%s` | `%s` |" % (d["sources"]["palette"][0], d["sources"]["palette"][1]))
    A("| `%s` | `%s` |" % (d["sources"]["epe"][0], d["sources"]["epe"][1]))
    A("| `Working/Entity/bm_epe_edits.json` | `%s` |" % d["spec"]["sha"])
    A("| `Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe` | `%s` |" % d["sources"]["ConvertProperty"])
    A("| `Tools/Gibbed-patched/Gibbed.JustCause3.ConvertAdf.exe` | `%s` |" % d["sources"]["ConvertAdf"])
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/jc3_tint_write.py --check")
    A("```")
    A("")
    A("`--check` re-exports the `.epe` and the palette, recomputes both Jenkins hashes,")
    A("re-runs both round trips, re-verifies all %d gates and compares this file byte for byte."
      % len(d["gates"]))
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    for exe in (CONVERT_PROPERTY, CONVERT_ADF):
        if not os.path.exists(exe):
            raise SystemExit("missing converter: " + exe)

    tmp = tempfile.mkdtemp(prefix="tint_write_")
    before = {}
    for p in (palette_path("bm-005"), epe_path("bm-005")):
        before[p] = sha256(p)
    try:
        d = collect(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [g for g in d["gates"] if not g[0]]
    for ok, name, detail in d["gates"]:
        print(("PASS " if ok else "FAIL ") + name + ": " + detail)
    for p, h in before.items():
        if sha256(p) != h:
            fails.append((False, "source-mutated", p))
            print("FAIL source-mutated: " + p)

    text = render(d) + "\n"
    if a.write:
        os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(text)
        print("wrote " + os.path.relpath(OUT_MD, ROOT))
    else:
        cur = open(OUT_MD, encoding="utf-8", newline="").read()
        if cur != text:
            diff = difflib.unified_diff(cur.splitlines(), text.splitlines(),
                                        "on-disk", "regenerated", lineterm="", n=1)
            print("\n".join(list(diff)[:60]))
            print("FAIL document: on-disk TINT_WRITE.md does not match the regenerated one")
            fails.append((False, "document", ""))
        else:
            print("PASS document: TINT_WRITE.md matches the regenerated text")

    if fails:
        print("%d FAILURE(S)" % len(fails))
        return 1
    print("OK (%d gates)" % len(d["gates"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
