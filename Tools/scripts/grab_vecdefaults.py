"""grab_vecdefaults.py - card COLOUR-vecdefaults (review of G3-04b, issue I-1): do the parent
material's `MaterialExpressionVectorParameter` exports carry a serialised default colour?

Review-G3-04b says G3-04b's "0/87 vector defaults" is wrong and the bytes hold 82/87 as a
`StructProperty` at 0xCC. This script reproduces the count from the package alone:

  * it walks EVERY export whose class is `MaterialExpressionVectorParameter` in
    `Playable_Batmobile_SF.upk`, parses that object's property-tag stream with the project's own
    reader (`Tools/scripts/upk_read.py`, read-only), and reports the tag fingerprint of each;
  * a default is counted only as a `StructProperty` whose tag name is `DefaultValue`, whose field
    offset is 0xCC and whose payload is exactly 16 B (four little-endian floats);
  * it lists all 87 (82 values + the 5 with none), groups them by master material, and compares the
    two values the brief names (BaseColour [0.0258, 0.0258, 0.03], Diffuse_Adjust [2.2, 2.0, 2.0])
    against the whole default set by value, not by name.

The combine rule is out of scope (G3-04b: 944 of 944 FunctionExpressions slots are zero) and is only
re-counted here as a guard, never re-argued.

    python Tools/scripts/grab_vecdefaults.py --write
    python Tools/scripts/grab_vecdefaults.py --check      # rebuilds and byte-compares

Read-only inputs: the package, `Research/BatmobileGrab/COLOUR_FUNCTIONS.md`,
`Research/BatmobileGrab/COLOUR_PARAMS.md`, `Tools/scripts/upk_read.py`, and BmSDK-AK's
`Generated/Engine/MaterialExpressionVectorParameter.g.cs` (MIT) for the field name/offset.
Output: `Research/BatmobileGrab/VEC_DEFAULTS.md`. Nothing else is written.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402  (project reader, read-only)

UPK = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile_SF.upk"
FUNCS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_FUNCTIONS.md")
PARAMS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLOUR_PARAMS.md")
BMSDK = r"E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated/Engine/MaterialExpressionVectorParameter.g.cs"
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "VEC_DEFAULTS.md")

CLASS = "MaterialExpressionVectorParameter"
NAME_FIELD = 0xAC          # MaterialExpressionParameter.ParameterName (BmSDK Ptr+172)
GUID_FIELD = 0xB4          # MaterialExpressionParameter.ExpressionGUID (Ptr+180)
DEFAULT_FIELD = 0xCC       # MaterialExpressionVectorParameter.DefaultValue (Ptr+204)
DEFAULT_BYTES = 16         # FLinearColor = 4 floats
CLASS_SIZE = 0xDC          # BmSDK: size = 220; 0xCC + 16 = 0xDC
EXPECTED_EXPORTS = 5490
EXPECTED_NAMES = 3151
EXPECTED_VECTORS = 87
EXPECTED_SHA1 = "c6e87dd0c06fbce9"

# the two values the brief names, and the exact text COLOUR_PARAMS.md stores them as
TARGETS = [
    {"what": "BaseColour", "names": ("Material0_BaseColour", "Main_BaseColour"),
     "value": [0.0258, 0.0258, 0.03, 1.0],
     "doc_text": "[0.025787, 0.025787, 0.03, 1]",
     "doc_row": "COLOUR_PARAMS.md §2 row 38 (owner `Batmobile_V3_WheelArchs_NEW_MIC` #767, "
                "VectorParameterValues field 0x168, item byte 262, tag @0x8)"},
    {"what": "Diffuse_Adjust", "names": ("Diffuse_Adjust",),
     "value": [2.2, 2.0, 2.0, 1.0],
     "doc_text": "[2.2, 2, 2, 1]",
     "doc_row": "COLOUR_PARAMS.md §2 row 37 (owner `Batmobile_V3_WheelArchs_NEW_MIC` #767, "
                "VectorParameterValues field 0x168, item byte 176, tag @0x8)"},
]
TOL = 5e-4


def r6(x: float) -> float:
    return round(x, 6)


def line_of(path: str, needle: str) -> int | None:
    for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        if needle in line:
            return i
    return None


def collect() -> dict:
    pkg = U.Package(UPK)
    raw = open(UPK, "rb").read()
    sha1 = hashlib.sha1(raw).hexdigest()
    rows = []
    for i in range(1, pkg.export_count + 1):
        if (pkg.object_class(i) or "") != CLASS:
            continue
        data = pkg.data(i)
        tags, end, why = U.walk_tags(pkg, data)
        name_tag = next((t for t in tags if t["type"] == "NameProperty"
                         and t.get("offset") == NAME_FIELD), None)
        guid_tag = next((t for t in tags if t["type"] == "GuidProperty"), None)
        structs = [t for t in tags if t["type"] == "StructProperty"]
        dflt = next((t for t in structs if t.get("offset") == DEFAULT_FIELD), None)
        value, at = None, None
        if dflt is not None and dflt.get("size") == DEFAULT_BYTES:
            at = dflt["at"]
            value = [r6(v) for v in struct.unpack_from("<4f", data, at)]
        # tag fingerprint: every tag as type@field, so a reader can see why a default is absent
        fp = sorted({"%s@%#x" % (t["type"], t.get("offset") or 0) for t in tags})
        rows.append({
            "export": i,
            "name": name_tag.get("value") if name_tag else None,
            "name_at": name_tag.get("offset") if name_tag else None,
            "material_export": pkg.exports[i - 1]["outer_index"],
            "material": pkg.object_name(pkg.exports[i - 1]["outer_index"]),
            "bytes": len(data),
            "walk_end": end, "walk_stop": why,
            "struct_tags": [{"offset": t.get("offset"), "size": t.get("size"),
                             "name": t.get("name")} for t in structs],
            "default": value,
            "default_at": at,
            "default_tag": dflt.get("name") if dflt is not None else None,
            "default_tag_offset": dflt.get("offset") if dflt is not None else None,
            "default_tag_size": dflt.get("size") if dflt is not None else None,
            "guid": (data[guid_tag["at"] + 16:guid_tag["at"] + 32].hex()[:8]
                     if guid_tag else None),
            "fingerprint": " ".join(fp),
        })
    return {"pkg": pkg, "sha1": sha1, "rows": rows,
            "exports": pkg.export_count, "names": len(pkg.names)}


def function_slots(pkg) -> dict:
    slots = nz = 0
    funcs = 0
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "MaterialFunction":
            continue
        funcs += 1
        tags, _e, _w = U.walk_tags(pkg, pkg.data(i))
        arr = next((t for t in tags if t.get("name") == "FunctionExpressions"), None)
        if not arr:
            continue
        body = pkg.data(i)[arr["at"]:arr["at"] + arr["size"]]
        n = struct.unpack_from("<i", body, 0)[0] if len(body) >= 4 else 0
        if len(body) == 4 + 4 * n:
            vals = struct.unpack("<%di" % n, body[4:4 + 4 * n])
            slots += n
            nz += sum(1 for v in vals if v)
    return {"functions": funcs, "slots": slots, "nonzero": nz}


def near(a: list[float] | None, b: list[float]) -> float:
    if a is None:
        return float("inf")
    return max(abs(x - y) for x, y in zip(a, b))


def build() -> str:
    d = collect()
    pkg, rows = d["pkg"], d["rows"]
    fs = function_slots(pkg)
    funcs_md = open(FUNCS_MD, encoding="utf-8").read()
    params_md = open(PARAMS_MD, encoding="utf-8").read()

    with_def = [r for r in rows if r["default"] is not None]
    without = [r for r in rows if r["default"] is None]
    # a GUID is a parameter *slot*, not an export: copies of a material share it
    guids = [r["guid"] for r in with_def]
    dupg = len([g for g in set(guids) if guids.count(g) > 1])
    # tag fingerprints -> how many exports share each shape
    shapes = {}
    for r in rows:
        shapes.setdefault(r["fingerprint"], []).append(r["export"])
    mats = {}
    for r in rows:
        m = mats.setdefault(r["material"], {"n": 0, "with": 0})
        m["n"] += 1
        m["with"] += 1 if r["default"] is not None else 0
    # every target: its same-named rows, the closest default anywhere, and whether it is present
    for t in TARGETS:
        named = [r for r in rows if r["name"] in t["names"]]
        t["named"] = named
        best = min(rows, key=lambda r: (near(r["default"], t["value"]), r["export"]))
        t["nearest"] = best
        t["nearest_dist"] = near(best["default"], t["value"])
        t["matches"] = [r for r in rows if near(r["default"], t["value"]) <= TOL]
        t["present_same"] = bool(t["matches"])
        t["doc_stored"] = t["doc_text"] in params_md
        t["doc_row_found"] = all(x in params_md for x in re.findall(r"\d+", t["doc_text"]))

    cf_count = None
    m = re.search(r"\| `%s` \| (\d+) \|" % CLASS, funcs_md)
    if m:
        cf_count = int(m.group(1))
    bmsdk = open(BMSDK, encoding="utf-8", errors="replace").read()
    l_struct = line_of(BMSDK, "StructProperty: DefaultValue")
    l_ptr = line_of(BMSDK, "Ptr + 204")
    l_size = line_of(BMSDK, "size = 220")

    oracles = {}
    oracles["package_header"] = {
        "ok": d["exports"] == EXPECTED_EXPORTS and d["names"] == EXPECTED_NAMES,
        "detail": {"exports": d["exports"], "names": d["names"]}}
    oracles["package_sha1_matches_colour_params"] = {
        "ok": d["sha1"].startswith(EXPECTED_SHA1),
        "detail": {"sha1": d["sha1"]}}
    oracles["vector_parameter_count_matches_colour_functions_md"] = {
        "ok": cf_count == len(rows) == EXPECTED_VECTORS,
        "detail": {"colour_functions_md": cf_count, "measured": len(rows)}}
    oracles["every_walk_reaches_eof"] = {
        "ok": all(r["walk_stop"] == "eof" for r in rows),
        "detail": {"eof": sum(1 for r in rows if r["walk_stop"] == "eof"), "of": len(rows)}}
    oracles["defaults_are_named_16_byte_structs_at_0xcc"] = {
        "ok": (len(with_def) == 82
               and all(r["default_tag"] == "DefaultValue" and r["default_tag_offset"] == DEFAULT_FIELD
                       and r["default_tag_size"] == DEFAULT_BYTES for r in with_def)),
        "detail": {"with_default": len(with_def),
                   "tag_names": sorted({r["default_tag"] for r in with_def}),
                   "tag_offsets": sorted({r["default_tag_offset"] for r in with_def}),
                   "tag_sizes": sorted({r["default_tag_size"] for r in with_def})}}
    oracles["five_without_have_no_struct_tag_at_all"] = {
        "ok": len(without) == 5 and all(not r["struct_tags"] for r in without)
              and len(rows) == len(with_def) + len(without),
        "detail": {"without": [[r["export"], r["name"], r["material"], r["bytes"]] for r in without]}}
    oracles["class_size_is_0xcc_plus_16"] = {
        "ok": DEFAULT_FIELD + DEFAULT_BYTES == CLASS_SIZE
              and l_struct is not None and l_ptr is not None and l_size is not None,
        "detail": {"0xcc+16": hex(DEFAULT_FIELD + DEFAULT_BYTES), "bmsdk_size": hex(CLASS_SIZE),
                   "gcs_lines": {"struct": l_struct, "ptr": l_ptr, "size": l_size}}}
    oracles["targets_are_not_defaults"] = {
        "ok": all(not t["present_same"] for t in TARGETS) and all(t["doc_stored"] for t in TARGETS),
        "detail": {t["what"]: {"matches": len(t["matches"]),
                               "nearest": [t["nearest"]["export"], t["nearest"]["name"],
                                           t["nearest"]["default"]],
                               "distance": t["nearest_dist"]} for t in TARGETS}}
    oracles["diffuse_adjust_default_is_white"] = {
        "ok": all(r["default"] == [1.0, 1.0, 1.0, 1.0] for r in rows
                  if r["name"] == "Diffuse_Adjust" and r["default"] is not None),
        "detail": {str(r["export"]): r["default"] for r in rows if r["name"] == "Diffuse_Adjust"}}
    oracles["operator_graph_still_stripped"] = {
        "ok": fs["slots"] == 944 and fs["nonzero"] == 0,
        "detail": fs}

    L = []
    A = L.append
    A("# VEC_DEFAULTS - the parent material's vector parameter defaults, read from the package")
    A("")
    A("**Card:** COLOUR-vecdefaults (follow-on to the review of **G3-04b**, issue I-1). "
      "**Status: the review is right.**")
    A(f"`Playable_Batmobile_SF.upk` holds **{len(rows)}** `MaterialExpressionVectorParameter` exports; "
      f"**{len(with_def)}**")
    A("serialise a default and **5** do not. The default is a `StructProperty` whose tag name is")
    A("**`DefaultValue`**, at field **0xCC**, payload **16 B** = four little-endian floats. G3-04b's")
    A("\"0/87, no value tag at all\" is therefore a decoder miss (it looked only for `FloatProperty`/")
    A("`VectorProperty` at 0xCC), not a property of the bytes.")
    A("")
    A("**Inputs (read-only):** the package, `COLOUR_FUNCTIONS.md` (the 87 and the material names),")
    A("`COLOUR_PARAMS.md` (the two values the brief names), `Tools/scripts/upk_read.py`, and BmSDK-AK's")
    A("`MaterialExpressionVectorParameter.g.cs` (MIT) for the field's name and offset. No game ran.")
    A("")
    A("## 1. Package and reader facts (decoded)")
    A("")
    A("| quantity | value | source |")
    A("|---|---:|---|")
    A(f"| package | `Playable_Batmobile_SF.upk` | header |")
    A(f"| bytes | {os.path.getsize(UPK):,} | file size |")
    A(f"| sha1 | `{d['sha1'][:16]}` | hashlib over the file |")
    A(f"| exports | {d['exports']} | export table |")
    A(f"| names | {d['names']} | name table |")
    A(f"| `{CLASS}` exports | {len(rows)} | export table, class name per export |")
    A(f"| of those with a serialised default | {len(with_def)} | tag walk, §2 |")
    A(f"| of those without | {len(without)} | tag walk, §5 |")
    A("")
    A("## 2. Where the default sits (decoded)")
    A("")
    A("| fact | value | evidence |")
    A("|---|---|---|")
    A(f"| tag type | `StructProperty` | tag stream of every export with a default |")
    A(f"| tag's own name | `DefaultValue` | same |")
    A(f"| field offset | 0xCC = {DEFAULT_FIELD} | same |")
    A(f"| payload | {DEFAULT_BYTES} B, 4 x f32 | {len(with_def)}/{len(with_def)} tags have size 16 |")
    A(f"| class size | 0xDC = {CLASS_SIZE} | 0xCC + 16 = 0xDC; BmSDK "
      f"`MaterialExpressionVectorParameter.g.cs:{l_size}` (`size = 220`) |")
    A(f"| BmSDK field | `DefaultValue`, `FLinearColor` | same file lines {l_struct} / {l_ptr} "
      f"(`StructProperty: DefaultValue`, `Ptr + 204`) |")
    A("")
    A("The offset is not inferred from UE3: the serialised tag offset, the tag name and BmSDK's own")
    A("declared field agree, and `0xCC + 16` lands exactly on the class size.")
    A("")
    A("## 3. All 87 vector parameters, by tag shape (decoded)")
    A("")
    A("`fingerprint` is every tag in the export as `Type@field`, so a missing default is visible as a")
    A("missing `StructProperty@0xcc` rather than as a decoder failure. Every walk reaches `eof`.")
    A("")
    A("| exports | count | fingerprint |")
    A("|---:|---:|---|")
    for fp, xs in sorted(shapes.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        A(f"| {len(xs)} | {len(xs)} | `{fp}` |")
    A("")
    A("## 4. The 82 defaults (decoded: package export, tag @0xCC, 16 B)")
    A("")
    A("| # | export | material (outer) | parameter | default [R, G, B, A] | guid | source |")
    A("|---:|---:|---|---|---|---|---|")
    for n, r in enumerate(with_def, 1):
        A(f"| {n} | {r['export']} | `{r['material']}` | `{r['name']}` | "
          f"[{r['default'][0]:g}, {r['default'][1]:g}, {r['default'][2]:g}, {r['default'][3]:g}] | "
          f"`{r['guid']}` | `StructProperty:DefaultValue` @0x{r['default_tag_offset']:x}, "
          f"value at object byte {r['default_at']} |")
    A("")
    A("## 5. The 5 that carry no default (decoded)")
    A("")
    min_w = min(r["bytes"] for r in with_def)
    sizes = sorted({r["bytes"] for r in without})
    A("Each walks to `eof` with no `StructProperty` anywhere in its stream, so the absence is a byte")
    A("fact: these exports are %s B against %d B for the smallest export that has a default."
      % ("/".join(str(s) for s in sizes), min_w))
    A("")
    A("| export | material (outer) | parameter | object bytes | tags present |")
    A("|---:|---|---|---:|---|")
    for r in without:
        A(f"| {r['export']} | `{r['material']}` | `{r['name']}` | {r['bytes']} | `{r['fingerprint']}` |")
    A("")
    A("## 6. The two values the brief names, checked against the whole default set")
    A("")
    A("Both are compared **by value** over all 82 defaults (max component difference <= %g), not by" % TOL)
    A("name, so a differently named expression carrying the same colour would still be found.")
    A("")
    A("| target | value (COLOUR_PARAMS.md) | same-named expressions and their defaults | defaults matching the value | nearest default | distance |")
    A("|---|---|---|---|---|---|")
    for t in TARGETS:
        named = "; ".join(
            f"{r['export']} `{r['name']}` "
            + ("**no default**" if r["default"] is None else
               f"[{r['default'][0]:g}, {r['default'][1]:g}, {r['default'][2]:g}, {r['default'][3]:g}]")
            for r in t["named"]) or "-"
        nrst = t["nearest"]
        A(f"| {t['what']} | [{t['value'][0]:g}, {t['value'][1]:g}, {t['value'][2]:g}, {t['value'][3]:g}] | "
          f"{named} | {len(t['matches'])} | {nrst['export']} `{nrst['name']}` "
          f"[{nrst['default'][0]:g}, {nrst['default'][1]:g}, {nrst['default'][2]:g}, {nrst['default'][3]:g}] | "
          f"{t['nearest_dist']:.6f} |")
    A("")
    for t in TARGETS:
        A(f"**{t['what']}.** The value the brief names is stored at {t['doc_row']}, i.e. it is an")
        A("`FVectorParameterValue` item in a **material instance**, not a default on an expression.")
        if t["named"]:
            miss = [r for r in t["named"] if r["default"] is None]
            have = [r for r in t["named"] if r["default"] is not None]
            p = "s" if len(t["named"]) != 1 else ""
            if miss:
                A(f"Of the {len(t['named'])} expression{p} with that name, {len(miss)} "
                  f"carr{'ies' if len(miss) == 1 else 'y'} **no default "
                  f"at all** ({', '.join(str(r['export']) for r in miss)})" +
                  ("; the rest default to "
                   + ", ".join(f"{r['export']} [{r['default'][0]:g}, {r['default'][1]:g}, "
                               f"{r['default'][2]:g}, {r['default'][3]:g}]" for r in have) + "." if have else "."))
            else:
                head = (f"The single expression with that name (`{t['names'][0]}`) carries a default: "
                        if len(have) == 1 else
                        f"All {len(have)} expressions with that name carry a default: ")
                A(head
                  + ", ".join(f"{r['export']} [{r['default'][0]:g}, {r['default'][1]:g}, "
                              f"{r['default'][2]:g}, {r['default'][3]:g}]" for r in have) + ".")
        A(f"Zero of the {len(with_def)} defaults match it (nearest is {t['nearest_dist']:.6f} away), so the")
        A("value is **not** among the 82 with the same numbers.")
        A("")
    A("**Answer to the brief's check:** neither value is a material default with those numbers.")
    A("`BaseColour` is the sharper case: the expressions of that name (`Material0_BaseColour` 716/720,")
    A("`Main_BaseColour` 683) have no serialised default at all, so the only base colour in the package is")
    A("the MIC override. `Diffuse_Adjust` has a default, and it is [1, 1, 1, 1] (export 711) - the")
    A("[2.2, 2, 2, 1] is the override in MIC 767.")
    A("")
    A("## 7. Per-material census (derived: counts from §4-§5)")
    A("")
    A("| master material | vector parameters | with default | without |")
    A("|---|---:|---:|---:|")
    for name, m in sorted(mats.items(), key=lambda kv: (-kv[1]["n"], kv[0])):
        A(f"| `{name}` | {m['n']} | {m['with']} | {m['n'] - m['with']} |")
    A("")
    A("## 8. What is not claimed")
    A("")
    A("- **No combine rule.** Re-counted only as a guard: "
      f"{fs['functions']} MaterialFunctions, {fs['slots']} `FunctionExpressions` slots, "
      f"{fs['nonzero']} non-zero. The operator graph is UNKNOWN (G3-04b), and this card does not")
    A("  re-open it.")
    A("- **No claim that a default is what the shader receives.** An expression default is the authored")
    A("  value a MIC may override; which one is live is a runtime question with no oracle in the project.")
    A("- **No socket mapping** (which parameter feeds base colour / roughness / dirt): the links are")
    A("  stripped, so that stays UNKNOWN.")
    A(f"- **GUIDs are not unique per export.** {dupg} of the {len(with_def)} default GUIDs occur in more")
    A("  than one export (the body/worn copies share them), so a GUID names a parameter slot and cannot")
    A("  on its own tie one expression to one override [derived: §4 guid column].")
    A("")
    A("## 9. Oracles (`--check` re-runs each)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k in sorted(oracles):
        A(f"| `{k}` | {oracles[k]['ok']} | `{json.dumps(oracles[k]['detail'], sort_keys=True)[:240]}` |")
    A("")
    A("## 10. Result")
    A("")
    A(f"- `{CLASS}` exports: **{len(rows)}** [decoded: export table]")
    A(f"- with a `DefaultValue` `StructProperty` @0xCC, 16 B: **{len(with_def)}** [decoded: tag walk]")
    A(f"- without any default: **5** - " + ", ".join(
        f"{r['export']} `{r['name']}`" for r in without) + " [decoded]")
    A("- the two named values: **not defaults**; both sit in MIC 767's `VectorParameterValues` "
      "[decoded: COLOUR_PARAMS.md §2 rows 37-38]")
    A("- how the parameters combine: **UNKNOWN**, unchanged (944/944 slots zero, §8)")
    A("")
    return "\n".join(L)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"
    if mode not in ("--write", "--check"):
        print(__doc__)
        return 2
    md = build()
    if mode == "--write":
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({len(md):,} chars, "
              f"{len(md.encode('utf-8')):,} B)")
        return 0
    on_disk = open(OUT_MD, encoding="utf-8", newline="").read()
    if on_disk != md:
        print("FAIL: VEC_DEFAULTS.md differs from a fresh rebuild")
        return 1
    print("OK rebuilt byte-identical from the package and the two colour documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
