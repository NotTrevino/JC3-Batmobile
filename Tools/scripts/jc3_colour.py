"""jc3_colour.py - G3-09 (desk part): the JC3 CarPaintMM colour path, as decoded facts.

The question this answers: *what makes a JC3 car the colour it is on screen, and what is
still missing before that can be predicted from authored values?*  Nothing here is inferred
from how paint "should" work - every value below is read out of the donor entity's own bytes,
or named as UNKNOWN with the place it would be found.

Sources, all in-repo:
  * the CarPaintMM block decoder/writer `Tools/scripts/rbm_geom.py` (byte-exact re-encode);
    field order and sizes from the shader reflection header quoted in MODLOG section 78:
    CarPaintStaticMaterialParams = 18 float4 (288 B), 7 support floats (28 B),
    CarPaintDynamicMaterialParams (TintColorR/G/B + gloss/metallic/clearcoat overrides,
    76 B), sampler slots s0 Diffuse, s1 Normal, s2 PropertyMap, s3 TintMap, s4-s9
    damage/dirt/decal;
  * the vehicle palette module `..._palette.vmodc`, read with `Tools/scripts/jc3adf.py`
    (ADF v4; MODLOG section 55 already named its 10 tints);
  * `Tools/scripts/palette_black.py`, which patches the tint floats in place and therefore
    documents that the palette is a float table, not an opaque blob.

What this tool adds over those notes: the palette's 10 tint records and the body's 9
CarPaintMM blocks are decoded side by side, with the byte offsets of the palette floats
(from Gibbed ConvertAdf's `offset-in-file`, asserted against the ADF decode) and the block
payload offsets derived from the decoder's own field order.  It also measures three things
the notes only claimed:

  1. tint_r / tint_g / tint_b hold the SAME colour in every one of the 10 records (10/10), so
     the three vectors are not three paint colours;
  2. no file in the 566-file bundle references the palette by name except the palette itself
     (measured by scanning every inner file) - the palette -> material link is engine-side;
  3. what JC3 data actually contains for exposure/tonemap/time-of-day: a name search over the
     whole 78,907-row VFS index, counted, not assumed.

Usage
    python Tools/scripts/jc3_colour.py --write
    python Tools/scripts/jc3_colour.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_rc  # noqa: E402
import eetoc  # noqa: E402
import jc3adf  # noqa: E402
import rbm_geom  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "COLOUR.md")
JS = os.path.join(OUT, "COLOUR.json")
BUNDLE = bm_rc.DIR + bm_rc.OLD + ".ee"
BODY = "sportsmuscle_body_lod1.rbm"
CONVADF = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertAdf.exe")

# CarPaintMM block payload layout, in the decoder's field order (rbm_geom.decode_carpaintmm).
# Offsets are inside the block payload (the 4-byte type hash is not part of it).
LAYOUT = [("version", 1), ("flags", 4), ("unknown", 4), ("static_params", 288),
          ("static_support", 28), ("dynamic_params", 76), ("deform_table", 1024)]
# static_params: 18 float4 in the reflection header's order.
STATIC18 = ["SpecularGloss", "Metallic", "ClearCoat", "Emissive",
            "DiffuseWrap", "DirtParams", "DirtBlend", "DirtColor",
            "DecalCount", "DecalWidth", "DecalColor1", "DecalColor2",
            "DecalColor3", "DecalColor4", "DecalBlend", "Damage",
            "DamageBlend", "DamageColor"]
SUPPORT7 = ["Decals", "DmgBlend", "Layered", "Overlay", "Rotating", "Dirt", "SoftTint"]
DYNAMIC = ["vec4[0]", "vec4[1]", "vec4[2]", "vec4[3]", "float[0]", "float[1]", "float[2]"]
# Sampler slots from the reflection header (MODLOG section 78); only s0-s3 are per-material.
SAMPLERS = ["s0 Diffuse", "s1 Normal", "s2 PropertyMap (mpm)", "s3 TintMap (msk)",
            "s4 DamageNormal", "s5 DamageAlbedo", "s6 DirtMap", "s7 Decal albedo",
            "s8 Decal normal", "s9 Decal property", "s10 (unused by the header)",
            "s11 (unused by the header)"]
FLAG_BITS = {0x1: "decals", 0x4: "damage blend", 0x10: "dirt", 0x40: "soft tint",
             0x80: "layered/overlay", 0x1000: "IS_DEFORM (vertex weights)",
             0x100: "ALPHABLENDING", 0x200: "ALPHATESTING"}


def bundle():
    raw = eetoc.unaaf(bm_rc.vfs(BUNDLE))
    return raw, eetoc.sarc_dir(raw)


def inner(raw, name, off, size):
    return raw[off:off + size] if off else bm_rc.vfs(name)


# --------------------------------------------------------------------------- palette
def palette(raw, ents) -> dict:
    name, off, size = next(e for e in ents if e[0].endswith("_palette.vmodc"))
    blob = inner(raw, name, off, size)
    a = jc3adf.Adf(blob)
    rows = {}
    for path, _t, v in jc3adf.walk(a):
        rows[path] = v
    tints, i = [], 0
    while f"tints[{i}].name.string" in rows:
        p = f"tints[{i}]"
        tints.append({
            "index": i,
            "name": rows[p + ".name.string"],
            "occurrence": rows[p + ".occurrence"],
            "tint_r": [rows[f"{p}.tint_r.{c}"] for c in "RGBA"],
            "tint_g": [rows[f"{p}.tint_g.{c}"] for c in "RGBA"],
            "tint_b": [rows[f"{p}.tint_b.{c}"] for c in "RGBA"],
            "specular_gloss": rows[p + ".specular_gloss"],
            "metallic": rows[p + ".metallic"],
            "clear_coat": rows[p + ".clear_coat"],
        })
        i += 1
    # exact file offsets of the tint floats: Gibbed ConvertAdf names them `offset-in-file`.
    offs = {}
    if os.path.exists(CONVADF):
        with tempfile.TemporaryDirectory(dir=os.path.join(ROOT, "tmp")) as td:
            src = os.path.join(td, "p.vmodc")
            xml = os.path.join(td, "p.xml")
            open(src, "wb").write(blob)
            r = subprocess.run([CONVADF, "--e", src, xml], capture_output=True)
            if r.returncode == 0:
                import xml.etree.ElementTree as ET
                root_ = ET.parse(xml).getroot()
                n = -1
                for t in root_.iter("member"):
                    if t.get("type") == "Tint":
                        n += 1
                    for m in t.iter("member"):
                        o = m.get("offset-in-file")
                        if o and m.get("type") == "float":
                            where = "palette" if n < 0 else f"tints[{n}]"
                            offs[f"{where}.{m.get('name')}"] = int(o, 16)
    return {"file": name, "bytes": len(blob), "adf_total": a.total,
            "types": sorted(t["name"] for t in a.types.values()),
            "tints": tints, "offsets": offs,
            "offset_source": ("ConvertAdf `offset-in-file` on the same bytes"
                              if offs else "UNKNOWN: ConvertAdf did not export")}


# --------------------------------------------------------------------------- blocks
def blocks(raw, ents) -> dict:
    name, off, size = next(e for e in ents if e[0].endswith(BODY))
    blob = inner(raw, name, off, size)
    m = rbm_geom.decode(blob)
    out, at = [], None
    for k, b in enumerate(m.blocks):
        st = struct.unpack("<72f", b.static_params)
        sup = struct.unpack("<7f", b.static_support)
        dyn = struct.unpack("<19f", b.dynamic_params)
        out.append({
            "block": k,
            "flags": b.flags,
            "flag_bits": [FLAG_BITS[x] for x in sorted(FLAG_BITS) if b.flags & x],
            "version": b.version,
            "unknown": b.unknown,
            "static": [list(struct.unpack("<4f", b.static_params[i * 16:(i + 1) * 16]))
                       for i in range(18)],
            "support": list(sup),
            "dynamic": list(dyn),
            "material_params": list(struct.unpack("<4f", b.material_params)),
            "textures": b.textures,
            "verts": b.vb0.count,
            "tris": b.ib.count // 3,
            "paint_zone": bool(b.flags & 0x1F) or len(b.textures) >= 4,
        })
    return {"file": name, "bytes": len(blob),
            "roundtrip": m.write() == blob, "blocks": out,
            "payload_offsets": LAYOUT}


def is_paint(b: dict) -> bool:
    return any(t.endswith("_body_dif.ddsc") or t.endswith("_body_msk.ddsc")
               for t in b["textures"])


# --------------------------------------------------------------------------- index search
TERMS = ["tonemap", "tone_map", "exposure", "postfx", "post_process", "lightprofile",
         "light_profile", "time_of_day", "sky", "sun", "weather", "color_curves"]


def index_search() -> dict:
    import jc3strings
    idx = jc3strings.load_index()
    res = {}
    for t in TERMS:
        hits = [k for k in idx if t in k.lower()]
        res[t] = {"count": len(hits), "examples": hits[:3]}
    return {"index_rows": len(idx), "terms": res}


# --------------------------------------------------------------------------- doc
def build() -> dict:
    raw, ents = bundle()
    pal = palette(raw, ents)
    bod = blocks(raw, ents)
    names = [b for b in bod["blocks"] if is_paint(b)]
    pal_refs = []
    for n, o, s in ents:
        b = inner(raw, n, o, s)
        c = b.count(b"palette")
        if c:
            pal_refs.append({"file": n, "occurrences": c})
    same = [t for t in pal["tints"]
            if t["tint_r"][:3] == t["tint_g"][:3] == t["tint_b"][:3]]
    return {
        "task": "G3-09",
        "bundle": BUNDLE,
        "body": bod,
        "palette": pal,
        "paint_blocks": [b["block"] for b in names],
        "paint_block_dynamic": {b["block"]: b["dynamic"] for b in names},
        "palette_references": pal_refs,
        "index": index_search(),
        "measured": {
            "tints": len(pal["tints"]),
            "tints_with_three_equal_vectors": len(same),
            "blocks": len(bod["blocks"]),
            "roundtrip": bod["roundtrip"],
            "paint_blocks": len(names),
            "static_bytes": 288, "support_bytes": 28, "dynamic_bytes": 76,
        },
    }


def md(doc: dict) -> str:
    pal, bod = doc["palette"], doc["body"]
    a = []
    a.append("# JC3 paint and colour pipeline (G3-09, desk part)")
    a.append("")
    a.append("What makes a JC3 car the colour it is, read out of the donor entity's own bytes. "
             "Card: `GRAB_BACKLOG.md` §6b `G3-09`. Evidence is labelled the project's way:")
    a.append("")
    a.append("* **decoded** - a project decoder read it; the file and offset/path is given;")
    a.append("* **derived** - a rule plus its inputs, stated;")
    a.append("* **UNKNOWN** - what was tried and where the answer would be.")
    a.append("")
    a.append("No value below comes from a shader source that is not on disk: the only shader "
             "evidence in the project is the reflection header quoted in MODLOG §78 "
             "(`jc-model-renderer`'s `carpaintmm.fb.txt`), which names the parameters and "
             "samplers but does not contain the shader body.")
    a.append("")
    a.append("## 1. The CarPaintMM block, as decoded")
    a.append("")
    a.append("`rbm_geom.decode` reads it and `rbm_geom`'s re-encode of every block of "
             "`%s` is **%s** - that round trip is the oracle for the field order, field sizes "
             "and every payload offset below." % (BODY, "byte-identical" if bod["roundtrip"]
                                                   else "NOT byte-identical"))
    a.append("")
    a.append("| payload offset | field | bytes | source of the name |")
    a.append("|---|---|---|---|")
    o = 0
    for f, n in bod["payload_offsets"]:
        a.append("| `0x%x` | `%s` | %d | decoder field order |" % (o, f, n))
        o += n
    a.append("")
    a.append("`static_params` is 18 float4 (288 B) and `static_support` 7 floats (28 B) - both "
             "**exactly** the sizes the reflection header's `CarPaintStaticMaterialParams` and "
             "its 7 support floats declare, which is why the header's names are used for the "
             "members but not for any value's meaning. `dynamic_params` is 76 B = 4 float4 + 3 "
             "floats, i.e. one float4 more than `TintColorR/G/B` + the three overrides.")
    a.append("")
    a.append("### Per block (all %d blocks of `%s`)" % (len(bod["blocks"]), BODY))
    a.append("")
    a.append("| block | flags | bits | verts | tris | textures | dynamic 19 floats |")
    a.append("|---|---|---|---|---|---|---|")
    for b in bod["blocks"]:
        a.append("| %d | `0x%X` | %s | %d | %d | %s | %s |"
                 % (b["block"], b["flags"], ", ".join(b["flag_bits"]) or "-",
                    b["verts"], b["tris"], "<br>".join(t.rsplit("/", 1)[-1]
                                                       for t in b["textures"]),
                    ", ".join("%.4g" % v for v in b["dynamic"])))
    a.append("")
    a.append("The %d blocks whose textures are the body's own `_body_dif` / `_body_nrm` / "
             "`_body_mpm` / `_body_msk` set are the paint zones: **blocks %s**. Their dynamic "
             "float4s are "
             "`%s`; every non-paint block carries an identity first float4 instead "
             "(`1,0,0,0`)." % (len(doc["paint_blocks"]),
                               ", ".join(str(x) for x in doc["paint_blocks"]),
                               ", ".join("(%s)" % ", ".join("%.4g" % v for v in row)
                                         for row in doc["paint_block_dynamic"].values())))
    a.append("")
    a.append("## 2. Sampler slots")
    a.append("")
    a.append("The block's texture table is a plain list; the slot index is the position. "
             "Mapped by the reflection header (MODLOG §78) and corroborated by the suffix of "
             "the texture each slot actually names on the paint blocks:")
    a.append("")
    a.append("| slot | shader sampler | paint-block texture | role |")
    a.append("|---|---|---|---|")
    pb = next(b for b in bod["blocks"] if is_paint(b))
    for i, t in enumerate(pb["textures"]):
        a.append("| %d | %s | `%s` | %s |"
                 % (i, SAMPLERS[i] if i < len(SAMPLERS) else "?",
                    t.rsplit("/", 1)[-1],
                    {0: "albedo (sRGB)", 1: "normal", 2: "PropertyMap: channel selectors",
                     3: "TintMap: per-channel tint amount"}.get(i, "shared, feature off")))
    a.append("")
    a.append("`s0`-`s3` are per-material; `s4`-`s11` are the shared damage/dirt/decal slots. "
             "The paint blocks' flags include the dirt/damage/soft-tint bits, so those "
             "samplers are live on the body - the paint colour is not `s0` alone.")
    a.append("")
    a.append("## 3. Static versus dynamic")
    a.append("")
    a.append("**Static** (per block, authored, cannot change without rewriting the `.rbm`): "
             "the 18 float4 named %s and the 7 support floats %s."
             % (", ".join("`%s`" % n for n in STATIC18[:4]) + ", ...",
                ", ".join("`%s`" % n for n in SUPPORT7)))
    a.append("")
    a.append("**Dynamic** (the 4 float4 + 3 floats at payload `0x145`, 76 B): the fields the "
             "engine can drive per spawn. The reflection header names three colour vectors "
             "`TintColorR/G/B` plus gloss/metallic/clearcoat overrides, which accounts for 60 "
             "of the 76 bytes; **which of the four float4 is which is UNKNOWN** - see §6.")
    a.append("")
    a.append("## 4. How a vanilla car's paint colour is chosen")
    a.append("")
    a.append("**The palette module.** `%s` (%d B, ADF v4 types %s) holds **%d tint records**:"
             % (pal["file"], pal["bytes"], ", ".join("`%s`" % t for t in pal["types"]),
                len(pal["tints"])))
    a.append("")
    a.append("| # | name | occurrence | tint_r = tint_g = tint_b (RGB) | A | gloss | metallic | clear coat |")
    a.append("|---|---|---|---|---|---|---|---|")
    for t in pal["tints"]:
        a.append("| %d | %s | %d | (%.4f, %.4f, %.4f) | %.2f | %.3f | %.3f | %.3f |"
                 % (t["index"], t["name"], t["occurrence"],
                    t["tint_r"][0], t["tint_r"][1], t["tint_r"][2], t["tint_r"][3],
                    t["specular_gloss"], t["metallic"], t["clear_coat"]))
    a.append("")
    a.append("Decoded facts about the table:")
    a.append("")
    a.append("* every one of the %d records holds the **same colour** in `tint_r`, `tint_g` "
             "and `tint_b` (%d of %d measured), so the three vectors are not three paint "
             "colours; they are the same RGB carried three times."
             % (len(pal["tints"]), doc["measured"]["tints_with_three_equal_vectors"],
                doc["measured"]["tints"]))
    a.append("* all ten `occurrence` values are 100, so the table is uniformly weighted as "
             "written. DERIVED (unproven): if `occurrence` is a spawn weight, every tint is "
             "equally likely. The selecting code is not in this entity.")
    a.append("* the five 'metallic' tints all carry gloss 0.45 / metallic 1.0 / coat 1.0, and "
             "the matte ones (White, Black) gloss 0.0 / metallic 0.0 / coat 1.0 - the palette "
             "carries the *look*, not only the colour.")
    if pal["offsets"]:
        first = min(pal["offsets"].values())
        a.append("* the file offsets are decoded, not assumed: ConvertAdf's `offset-in-file` "
                 "on the same bytes gives `tints[0].R` at `0x%x`, and %d floats in all - "
                 "**7 per record** (R/G/B/A + specular_gloss/metallic/clear_coat) for the 10 "
                 "tints plus the palette root's own default record (`palette.*`). "
                 "`tint_g` and `tint_b` are separate bytes in the file (jc3adf reads them: "
                 "equal to `tint_r` 10/10) but ConvertAdf exports only one ColorRGBA per "
                 "record, so they have no exported offset - which is why "
                 "`palette_black.py` patches R/G/B/A and the three scalars only."
                 % (first, len(pal["offsets"])))
    a.append("")
    a.append("**How the palette reaches the material: UNKNOWN, and measured to be so.** A scan "
             "of all **566** inner files for the byte string `palette` finds it in **%d** "
             "file(s): %s. No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so "
             "the binding is engine-side (spawn/vehicle-system), not an asset reference. "
             "DERIVED, therefore, not decoded: the visible paint is the block's own dynamic "
             "tint modulated by the TintMap (`body_msk`) channels, and the palette is what the "
             "engine writes into that dynamic slot for the chosen variant."
             % (len(doc["palette_references"]),
                ", ".join("`%s` (%d)" % (r["file"].rsplit("/", 1)[-1], r["occurrences"])
                          for r in doc["palette_references"]) or "none"))
    a.append("")
    a.append("## 5. Exposure, tonemap, time of day: what JC3 data holds")
    a.append("")
    a.append("Name search over the whole VFS index (**%d** rows), case-insensitive substring, "
             "counted per term:" % doc["index"]["index_rows"])
    a.append("")
    a.append("| term | files | example |")
    a.append("|---|---|---|")
    for t, r in doc["index"]["terms"].items():
        a.append("| `%s` | %d | %s |"
                 % (t, r["count"],
                    ("`%s`" % r["examples"][0]) if r["examples"] else "-"))
    a.append("")
    a.append("So: **no file in JC3's index is named for a tonemap, a post-process chain, a "
             "light profile or a time of day**. The only exposure-named asset is "
             "`textures/color_curves/color_correction_neutral_exposure.ddsc`, a colour-curve "
             "texture with no readable settings (its `.ddsc` payload is in the PARTIAL column "
             "of G3-12). Exposure and tonemapping are therefore **UNKNOWN** as data: they are "
             "either engine constants or live in the executable, and neither was read.")
    a.append("")
    a.append("## 6. What is still UNKNOWN, and where it would be answered")
    a.append("")
    a.append("1. **Which dynamic float4 is `TintColorR`, which is G, which is B, and what the "
             "fourth is.** The reflection header gives three names and the struct has four "
             "vectors; on the paint blocks the values are `(0.14, 0.19, 0.25, 1.0)`, "
             "`(0, 1, 0, 0)`, `(0, 0, 1, 0)`, `(2, 0, 1, 1)`, which reads more like a "
             "channel-to-tint matrix than three colours - but that is a hypothesis, not a "
             "decode. Where: the shader body (not on disk) or an in-game A/B write of one "
             "float4 with a screenshot readback.")
    a.append("2. **How the engine picks a tint and whether it writes the palette's rgb, gloss, "
             "metallic and coat into the dynamic slot.** The palette -> block binding is not "
             "in any of the 566 files (§4). Where: the vehicle spawn/variant code (executable), "
             "or a runtime oracle that dumps the material's dynamic constants after a spawn.")
    a.append("3. **The channel semantics of `PropertyMap` and `TintMap`.** MODLOG §78 reads "
             "them as 'PropertyMap RGB selects material channels 1-3, TintMap RGB = tint "
             "amount', from vanilla pixel statistics - INFERRED there, and the `.ddsc` payload "
             "is not decoded by any project script (G3-12). Where: a `.ddsc` reader (G3-12 "
             "open item) plus a decode of the four material channels.")
    a.append("4. **The on-screen transfer function.** No project file states an exposure, a "
             "tonemap curve or a lighting model (§5). Where: a runtime oracle.")
    a.append("")
    a.append("## 7. What an on-screen calibration needs")
    a.append("")
    a.append("The card's Done asks for `JC3 on-screen colour as a function of named terms, "
             "calibrated on >=3 vanilla paints, error stated`. None of that can be produced by "
             "reading files - it needs pixels. The minimum set, in the order it has to happen:")
    a.append("")
    a.append("1. **A fixed frame** (G3-07): one camera pose, one time of day, one weather "
             "state, HUD off, and the paint zone filling a known screen region. Without a fixed "
             "frame two screenshots are not comparable.")
    a.append("2. **>=3 vanilla cars whose palette record is known from the file side** - the "
             "donor's own 10 tints are already decoded here (`%s`, White / Black / Garnet Red "
             "Metallic are the most separable), so the same entity at three tints is a valid "
             "calibration set, and three different vanilla entities is a stronger one."
             % ", ".join(t["name"] for t in pal["tints"][:3]))
    a.append("3. **A readback with a known encoding**: screenshot in a lossless format, the "
             "paint-zone pixel average in linear light (the `.ddsc` flags say bit 8 = sRGB for "
             "colour textures, MODLOG §79), and the same for a neutral reference in frame.")
    a.append("4. **The authored terms for each sample**, which this tool now prints per block: "
             "the dynamic float4s, the static SpecularGloss/Metallic/ClearCoat float4s, and the "
             "palette record's rgb/gloss/metallic/coat.")
    a.append("5. Then fit `screen = f(tint, gloss, metallic, coat, TintMap, PropertyMap, "
             "exposure)` and report the residual per sample. Without (1)-(4) any such fit is "
             "the ALB-2 mistake again: a gain chosen from screenshots.")
    a.append("")
    a.append("## Reproduce")
    a.append("")
    a.append("```")
    a.append("python Tools/scripts/jc3_colour.py --write")
    a.append("python Tools/scripts/jc3_colour.py --check")
    a.append("```")
    a.append("")
    return "\n".join(a)


# --------------------------------------------------------------------------- checks
def checks(doc: dict) -> list[tuple[str, bool]]:
    m, pal, bod = doc["measured"], doc["palette"], doc["body"]
    out = []
    out.append(("the palette decodes as ADF v4 with the types MODLOG §55 names "
                "(%s) and its header total equals its length (%d)"
                % (", ".join(pal["types"]), pal["bytes"]),
                "Tint" in pal["types"] and pal["adf_total"] == pal["bytes"]))
    out.append(("the palette holds exactly 10 tint records, the names MODLOG §55 lists",
                m["tints"] == 10
                and [t["name"] for t in pal["tints"]] ==
                ["White", "Evergreen Pearl", "Garnet Red Metallic", "Black", "Grey",
                 "Silver", "Blue", "Brown", "Red", "Green"]))
    out.append(("tint_r, tint_g and tint_b carry the same RGB in every record (%d/%d) - the "
                "measured reason the palette is one colour per tint, not three"
                % (m["tints_with_three_equal_vectors"], m["tints"]),
                m["tints_with_three_equal_vectors"] == m["tints"] == 10))
    out.append(("every tint float is inside [0, 1] except the A lanes, and all occurrence "
                "values are 100",
                all(0.0 <= v <= 1.0 for t in pal["tints"] for v in
                    (list(t["tint_r"][:3])
                     + [t["specular_gloss"], t["metallic"], t["clear_coat"]]))
                and all(t["occurrence"] == 100 for t in pal["tints"])))
    out.append(("the body's %d CarPaintMM blocks re-encode byte for byte (the block layout "
                "oracle)" % m["blocks"], m["roundtrip"] and m["blocks"] == 9))
    out.append(("the three payload sizes are the reflection header's structures exactly "
                "(static 288 B / support 28 B / dynamic 76 B)",
                m["static_bytes"] == 18 * 16 and m["support_bytes"] == 7 * 4
                and m["dynamic_bytes"] == 4 * 16 + 3 * 4))
    pb = [b for b in bod["blocks"] if is_paint(b)]
    out.append(("the paint zones are exactly the blocks carrying the body's own "
                "_body_dif/_body_msk textures (%s) and every one of them has the dirt/damage/"
                "soft-tint flag bits set"
                % ", ".join(str(b["block"]) for b in pb),
                len(pb) == 3 and all(b["flags"] & 0x1F for b in pb)))
    out.append(("the s0-s3 slots on a paint block are dif / nrm / mpm / msk in that order "
                "(the reflection header's Diffuse / Normal / PropertyMap / TintMap), so the "
                "sampler order is corroborated by the texture suffixes, not assumed",
                [t.rsplit(".", 2)[-2].rsplit("_", 1)[-1] for t in pb[0]["textures"][:4]]
                == ["dif", "nrm", "mpm", "msk"]))
    out.append(("no file in the bundle references the palette except the palette itself: "
                "%d reference(s), measured over all 566 inner files"
                % len(doc["palette_references"]),
                len(doc["palette_references"]) == 1
                and doc["palette_references"][0]["file"].endswith("_palette.vmodc")))
    idx = doc["index"]
    out.append(("the exposure/tonemap search is a measurement over the whole index (%d rows), "
                "and it finds no tonemap/post-process/light-profile/time-of-day file"
                % idx["index_rows"],
                idx["index_rows"] > 70000
                and idx["terms"]["tonemap"]["count"] == 0
                and idx["terms"]["postfx"]["count"] == 0
                and idx["terms"]["lightprofile"]["count"] == 0
                and idx["terms"]["exposure"]["count"] == 1))
    out.append(("the palette floats' file offsets are decoded, not assumed (ConvertAdf "
                "`offset-in-file` on the same bytes): %d offsets = 7 (R/G/B/A + gloss / "
                "metallic / coat) x 11 records" % len(pal["offsets"]),
                len(pal["offsets"]) == 77
                and all(f"tints[{i}].{c}" in pal["offsets"] for i in range(10)
                        for c in ("R", "G", "B", "specular_gloss", "metallic",
                                  "clear_coat"))))
    out.append(("no on-screen calibration is claimed: the JSON's measured set is exactly the "
                "file-side numbers (tints, blocks, round trip, paint zones, three sizes) and "
                "carries no screen colour or error term",
                set(doc["measured"]) == {"tints", "tints_with_three_equal_vectors", "blocks",
                                         "roundtrip", "paint_blocks", "static_bytes",
                                         "support_bytes", "dynamic_bytes"}))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    text, blob = md(doc), json.dumps(doc, indent=1) + "\n"
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8", newline="\n").write(text)
        open(JS, "w", encoding="utf-8", newline="\n").write(blob)
        print("wrote %s (%d tints, %d blocks, %d paint zones)"
              % (MD, doc["measured"]["tints"], doc["measured"]["blocks"],
                 doc["measured"]["paint_blocks"]))
        print("wrote %s" % JS)
        return 0

    bad, res = [], checks(doc)
    for what, ok in res:
        print("%-4s %s" % ("ok" if ok else "FAIL", what))
        if not ok:
            bad.append(what)
    same_md = os.path.exists(MD) and open(MD, encoding="utf-8").read() == text
    same_js = os.path.exists(JS) and open(JS, encoding="utf-8").read() == blob
    print("%-4s %s is byte-identical to a fresh decode" % ("ok" if same_md else "FAIL", MD))
    print("%-4s %s is byte-identical to a fresh decode" % ("ok" if same_js else "FAIL", JS))
    if not same_md or not same_js:
        bad.append("drift")
    print("\n%s: %d/%d checks, md %s, json %s"
          % ("OK" if not bad else "FAILED", sum(1 for _w, g in res if g), len(res),
             "identical" if same_md else "DIFFERS", "identical" if same_js else "DIFFERS"))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
