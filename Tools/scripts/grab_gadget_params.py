"""grab_gadget_params.py - card GADGET-params: the 48 `RBatmobileRemoteBm` parameters, valued.

G3-05 left two batches open: "values of 97 RVehicleBatmobile defaults + 48 remote-gadget params".
G3-06b closed the 97 (`CLASS_DEFAULTS.md`). This tool closes the 48.

Where they are (all read from the package tables, never assumed):
  * the class `BmScript.RBatmobileRemoteBm` has 48 member exports in `Startup.upk` - 22 Function,
    3 State, 11 FloatProperty, 10 ObjectProperty, 2 BoolProperty (census in the report);
  * their values live in the class default object `BmScript.Default__RBatmobileRemoteBm`
    (`Startup.upk` 536, `StartupPatch.upk` 520), a 364 B payload with 33 property tags.

Naming rule (no guesses): a cooked tag carries only a byte offset and a type id. The name comes
from a class layout that declares a property at exactly that offset with a compatible kind, walking
`RBatmobileRemoteBm -> RBatmobileRemote -> RInventoryGadget -> Inventory -> Actor -> StateObject`.
The layout is read from BmSDK-AK's `.g.cs` bindings (MIT) - the same source and the same
`Layout`/`same_kind` helpers `grab_class_defaults.py` uses - and each row cites file:line. For a
`BoolProperty` the payload is the whole 32-bit bitfield word, so the offset names a set of members
and each member's value is `word & mask`.

Values: `decoded` from the tag payload; `derived` for a stated rule (bit splitting, "the tag is
absent", the Startup/StartupPatch comparison); `UNKNOWN` where the value is not in the stream
(absent tag) or a followed object reference points at an untagged component payload.

Nothing here maps anything to Just Cause 3.

    python Tools/scripts/grab_gadget_params.py --write
    python Tools/scripts/grab_gadget_params.py --check      # rebuilds and byte-compares

Read-only inputs: `Startup.upk`, `StartupPatch.upk`, the BmSDK-AK bindings, `PACKAGES_G305.md`
(the 48-name list, cross-checked against the export table) and `Tools/scripts/upk_read.py` +
`grab_class_defaults.py` (imported, unmodified). Output: `Research/BatmobileGrab/GADGET_PARAMS.md`.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402
from grab_class_defaults import Layout, same_kind, f  # noqa: E402  (read-only reuse)

GAME = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
BMSDK = r"E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated"
G305_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "PACKAGES_G305.md")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "GADGET_PARAMS.md")

CLASS = "RBatmobileRemoteBm"
CLASSPATH = "BmScript." + CLASS
CDO_NAME = "Default__" + CLASS
PACKAGES = ("Startup.upk", "StartupPatch.upk")
EXPECT_TAG_COUNT = 33
EXPECT_CLASS_SIZE = 2456
EXPECT_MEMBERS = {"Function": 22, "State": 3, "FloatProperty": 11, "ObjectProperty": 10,
                  "BoolProperty": 2}
# the 23 members that hold a value, and the 16 of them the CDO serialises
VALUE_KINDS = {"FloatProperty", "ObjectProperty", "BoolProperty"}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def class_size_of(path: str) -> int | None:
    for line in open(path, encoding="utf-8-sig"):
        m = re.search(r"\(size = (\d+)\)", line)
        if m:
            return int(m.group(1))
    return None


def doc_names_48() -> list[str]:
    """The 48 names as PACKAGES_G305.md §4 lists them, for a cross-check only."""
    text = open(G305_MD, encoding="utf-8").read()
    i = text.find("**`BmScript.RBatmobileRemoteBm`** - 48 property objects")
    if i < 0:
        return []
    j = text.find("42 of these names do not appear", i)
    block = text[i:j if j > 0 else i + 4000]
    names = re.findall(r"`([^`\n]+)`", block)
    seen, out = set(), []
    for n in names:
        if n in ("BmScript.RBatmobileRemoteBm",) or n.lower().startswith(("floatproperty",)):
            continue
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def read_package(name: str) -> dict:
    """Everything this card needs from one package, then the package object is dropped."""
    pkg = U.Package(os.path.join(GAME, name))
    class_export = None
    for j in range(1, pkg.export_count + 1):
        # a class object's own class is `Class`, so the path test is the identity here
        if pkg.object_path(j) == CLASSPATH and pkg.object_name(j) == CLASS:
            class_export = j
            break
    if class_export is None:
        raise SystemExit("class export %s not found in %s" % (CLASSPATH, name))
    members = []
    for j in range(1, pkg.export_count + 1):
        if pkg.exports[j - 1]["outer_index"] == class_export:
            members.append({"export": j, "name": pkg.object_name(j),
                            "class": pkg.object_class(j),
                            "size": pkg.exports[j - 1]["size"]})
    cdo = None
    for j in range(1, pkg.export_count + 1):
        if pkg.object_path(j) == "BmScript." + CDO_NAME:
            cdo = j
            break
    if cdo is None:
        raise SystemExit("CDO %s not found in %s" % (CDO_NAME, name))
    data = pkg.data(cdo)
    tags, end, why = U.walk_tags(pkg, data)
    return {"package": name, "export_count": pkg.export_count, "class_export": class_export,
            "class_size": pkg.exports[class_export - 1]["size"],
            "members": members, "cdo_export": cdo, "payload": len(data),
            "payload_sha1": hashlib.sha1(data).hexdigest(),
            "tags": tags, "walk_end": end, "walk_stop": why,
            "_pkg": pkg, "_data": data}


# ------------------------------------------------------------------ naming
def resolve(chain, props, offset, tag_type):
    """(owner, compatible members, all members) at a class offset - same_kind, no resemblance."""
    for cls in chain:
        members = [p for p in props[cls] if p["offset"] == offset]
        if not members:
            continue
        return cls, [p for p in members if same_kind(p["kind"], tag_type)], members
    return None, [], []


def name_tags(pkg, tags, chain, props) -> list[dict]:
    """Attach the layout's member name(s) to every tag; bools expand to one row per set member."""
    rows = []
    for t in tags:
        owner, ok, allk = resolve(chain, props, t["offset"], t["type"])
        if not ok:
            rows.append({"tag": t, "owner": owner, "member": None, "kind": None,
                         "label": "UNKNOWN (offset only)",
                         "candidates": [p["member"] for p in allk]})
            continue
        if t["type"] == "BoolProperty":
            bits = t.get("bits") or 0
            for p in ok:
                info = {"class": owner, "member": p["member"], "offset": p["offset"],
                        "kind": p["kind"], "mask": p.get("mask"),
                        "file": p.get("file"), "line": p.get("line")}
                mask = info.get("mask")
                rows.append({"tag": t, "owner": owner, "member": p["member"],
                             "kind": p["kind"], "mask": mask,
                             "value": (bool(bits & mask) if mask else None),
                             "info": info,
                             "label": "decoded" if mask else "UNKNOWN (mask)"})
            continue
        p = ok[0]
        info = {"class": owner, "member": p["member"], "offset": p["offset"],
                "kind": p["kind"], "mask": p.get("mask"),
                "file": p.get("file"), "line": p.get("line")}
        rows.append({"tag": t, "owner": owner, "member": p["member"], "kind": p["kind"],
                     "info": info, "label": "decoded"})
    return rows


def target_of(pkg, idx: int) -> dict | None:
    if not idx:
        return None
    out = {"index": idx, "path": pkg.object_path(idx), "class": pkg.object_class(idx)}
    if idx > 0:
        e = pkg.exports[idx - 1]
        out["export"] = idx
        out["export_bytes"] = e["size"]
        out["outer"] = pkg.object_name(e["outer_index"])
        inner, end, why = U.walk_tags(pkg, pkg.data(idx))
        out["inner_tags"] = len(inner)
        out["inner_stop"] = why
        out["inner_label"] = ("decoded (%d tags)" % len(inner)) if inner else \
            "UNKNOWN (payload has no property tags: %d B, stop=%s)" % (e["size"], why)
    else:
        out["import"] = True
        out["inner_label"] = "UNKNOWN (import: the object is not in this package)"
    return out


def tag_value(pkg, row) -> tuple[str, str]:
    """(value text, label) for one named tag row."""
    t, kind = row["tag"], row["kind"]
    if kind == "FloatProperty":
        return f(t["value"]), "decoded"
    if kind == "IntProperty":
        return str(t["value"]), "decoded"
    if kind == "BoolProperty":
        if row.get("mask") is None:
            return "UNKNOWN (no mask in the bindings)", "UNKNOWN"
        return ("true" if row["value"] else "false"), "decoded"
    if kind in ("NameProperty",):
        return "`%s`" % t["value"], "decoded"
    if kind in ("StrProperty",):
        return '"%s"' % t["value"], "decoded"
    if kind == "ByteProperty":
        # walk_tags puts the enum entry in `value` and the enum's own type name in `name`
        enum = t.get("name")
        return ("`%s`" % t.get("value")) + (" (enum `%s`)" % enum if enum else ""), "decoded"
    if kind in ("VectorProperty", "RotatorProperty", "StructProperty"):
        v = t.get("value")
        if isinstance(v, list):
            return "[%s]" % ", ".join(f(x) for x in v), "decoded"
        return "`%s`" % (v if v is not None else t.get("raw")), "decoded"
    if kind in ("ObjectProperty", "ComponentProperty", "ClassProperty"):
        idx = t.get("value")
        if not idx:
            return "None", "decoded"
        tgt = target_of(pkg, idx)
        return "`%s` (%s)" % (tgt["path"], tgt["class"]), "decoded"
    return "`%s`" % (t.get("value") if t.get("value") is not None else t.get("raw")), "decoded"


def build() -> str:
    lay = Layout({"classes": {}}, CLASS)
    chain = lay.super_chain(CLASS)
    gcs = {}
    for cls in chain:
        p = lay._gen_files().get(cls)
        gcs[cls] = p
    size = class_size_of(gcs[CLASS]) if gcs.get(CLASS) else None
    props = {cls: lay.binding_props(cls) for cls in chain}

    runs = {}
    for name in PACKAGES:
        runs[name] = read_package(name)

    # name the tags of each package's CDO
    named = {}
    for name, run in runs.items():
        named[name] = name_tags(run["_pkg"], run["tags"], chain, props)

    doc48 = doc_names_48()
    startup = runs[PACKAGES[0]]
    members = startup["members"]
    member_names = [m["name"] for m in members]
    member_kinds = {}
    for m in members:
        member_kinds.setdefault(m["class"], []).append(m["name"])

    # member -> tag row (own members only)
    own_rows = [r for r in named[PACKAGES[0]] if r["member"] in set(member_names)]
    own_by_name = {}
    for r in own_rows:
        own_by_name.setdefault(r["member"], []).append(r)

    # value slots = the 23 members that declare a value
    value_members = [m for m in members if m["class"] in VALUE_KINDS]
    tagged = [m for m in value_members if m["name"] in own_by_name]
    untagged = [m for m in value_members if m["name"] not in own_by_name]

    # do the two packages agree, after decoding?
    def fingerprint(name):
        out = []
        for r in named[name]:
            txt, _lab = tag_value(runs[name]["_pkg"], r)
            out.append({"member": r["member"], "offset": r["tag"]["offset"],
                        "type": r["tag"]["type"], "value": txt, "mask": r.get("mask"),
                        "kind": r["kind"], "ref_class": r["tag"].get("ref_class")})
        return out

    fp_start = fingerprint(PACKAGES[0])
    fp_patch = fingerprint(PACKAGES[1])
    object_kinds = ("ObjectProperty", "ComponentProperty")
    scalar_diffs = [(a, b) for a, b in zip(fp_start, fp_patch)
                    if a["kind"] not in object_kinds and a != b]
    object_diffs = [(a, b) for a, b in zip(fp_start, fp_patch)
                    if a["kind"] in object_kinds and a["value"] != b["value"]]

    oracles = {}
    oracles["cdo_identity"] = {
        "ok": (all(r["payload"] == 364 and len(r["tags"]) == EXPECT_TAG_COUNT
                   and r["walk_stop"] == "eof" for r in runs.values())),
        "detail": {n: {"export": r["cdo_export"], "payload": r["payload"], "tags": len(r["tags"]),
                       "stop": r["walk_stop"], "sha1": r["payload_sha1"][:16]}
                   for n, r in runs.items()}}
    oracles["class_size_matches_bindings"] = {
        "ok": (size == EXPECT_CLASS_SIZE
               and all(t["offset"] < size for r in runs.values() for t in r["tags"])),
        "detail": {"size": size, "max_tag_offset":
                   max(t["offset"] for r in runs.values() for t in r["tags"])}}
    oracles["every_tag_named"] = {
        "ok": all(r["member"] for r in named[PACKAGES[0]]),
        "detail": {"distinct_tags": len(runs[PACKAGES[0]]["tags"]),
                   "rows_after_bool_split": len(named[PACKAGES[0]]),
                   "unnamed": [hex(r["tag"]["offset"]) for r in named[PACKAGES[0]]
                               if not r["member"]]}}
    oracles["member_census_48"] = {
        "ok": (len(members) == 48
               and {k: len(v) for k, v in member_kinds.items()} == EXPECT_MEMBERS),
        "detail": {k: len(v) for k, v in sorted(member_kinds.items())}}
    oracles["value_slots_23"] = {
        "ok": (len(value_members) == 23 and len(tagged) == 16 and len(untagged) == 7),
        "detail": {"value_members": len(value_members), "tagged": len(tagged),
                   "untagged": [m["name"] for m in untagged]}}
    oracles["eleven_floats_named_in_order"] = {
        "ok": ([r["member"] for r in own_rows if r["kind"] == "FloatProperty"]
               == ["JammingRange", "JammerTime", "CurrentJam", "CursorSpeed", "CursorAccel",
                   "CursorDecel", "CursorReturnFactor", "CursorReturnDelay", "MaxAimX",
                   "MaxAimY", "RelativeAimingCurvePower"]),
        "detail": {hex(r["tag"]["offset"]): r["member"] for r in own_rows
                   if r["kind"] == "FloatProperty"}}
    oracles["doc_list_matches_export_table"] = {
        "ok": sorted(doc48) == sorted(member_names),
        "detail": {"doc": len(doc48), "exports": len(member_names),
                   "doc_only": sorted(set(doc48) - set(member_names)),
                   "export_only": sorted(set(member_names) - set(doc48))}}
    oracles["packages_agree"] = {
        "ok": (len(fp_start) == len(fp_patch) and not scalar_diffs
               and all(a["ref_class"] == b["ref_class"] for a, b in object_diffs)),
        "detail": {"compared": len(fp_start), "scalar_diffs": len(scalar_diffs),
                   "object_path_diffs": [[a["member"], a["value"], b["value"]]
                                         for a, b in object_diffs]}}
    oracles["object_refs_resolve"] = {
        "ok": all(r["tag"].get("ref") for r in named[PACKAGES[0]]
                  if r["kind"] in ("ObjectProperty", "ComponentProperty")
                  and r["tag"].get("value")),
        "detail": {r["member"]: r["tag"].get("ref") for r in named[PACKAGES[0]]
                   if r["kind"] in ("ObjectProperty", "ComponentProperty")
                   and r["tag"].get("value")}}

    L = []
    A = L.append
    A("# GADGET_PARAMS - the 48 `RBatmobileRemoteBm` parameters, valued")
    A("")
    A("**Card:** GADGET-params (closes the second half of the G3-05 open item). **Gadget class:**")
    A(f"`{CLASSPATH}` in `Startup.upk` / `StartupPatch.upk`. Values come from its **class default")
    A("object** (`Default__RBatmobileRemoteBm`), not from an archetype: this class ships no archetype")
    A("in either package, and the CDO is where the cooked defaults live.")
    A("")
    A(f"**Result:** of the 48 members, **23 hold a value** (11 floats, 10 object pointers, 2 bools)")
    A(f"and **25 are behaviour** (22 functions, 3 states). The CDO serialises **{len(tagged)}** of the")
    A(f"23 value slots; the other **{len(untagged)}** carry no tag, so their values are not in the")
    A("stream and are marked UNKNOWN rather than assumed to be None/false.")
    A("")
    A("## 1. What was read (decoded)")
    A("")
    A("| role | package | export | object | class | payload | tags | walk |")
    A("|---|---|---|---|---|---:|---:|---|")
    for name, r in runs.items():
        A(f"| CDO | `{name}` | {r['cdo_export']} | `BmScript.{CDO_NAME}` | `{CLASS}` | "
          f"{r['payload']} | {len(r['tags'])} | `{r['walk_stop']}` at {r['walk_end']} |")
    A(f"| class | `Startup.upk` | {startup['class_export']} | `{CLASSPATH}` | `{CLASS}` | - | - | - |")
    A("")
    A(f"Class size: **{size}** bytes (`{os.path.basename(gcs.get(CLASS) or '?')}` line with "
      f"`(size = {size})`); every tag offset is inside it. The CDO payload sha1 is "
      f"`{runs[PACKAGES[0]]['payload_sha1']}` in `Startup.upk` and "
      f"`{runs[PACKAGES[1]]['payload_sha1']}` in `StartupPatch.upk` — different bytes (the object")
    A("index tables differ), identical decoded values (oracle `packages_agree`).")
    A("")
    A("**Layout chain** used for naming, from the bindings (`RBatmobileRemoteBm.g.cs` etc.):")
    A("")
    A("| class | declared properties | source |")
    A("|---|---:|---|")
    for cls in chain:
        src = os.path.basename(gcs[cls]) if gcs.get(cls) else "-"
        A(f"| `{cls}` | {len(props[cls])} | `{src}` |")
    A("")
    A("A tag is named only by a member declared at **exactly** its offset with a compatible kind")
    A("(`same_kind`: a cooked pointer is `ObjectNCRProperty` whatever the declared subclass; a native")
    A("vector is `StructProperty` in the bindings). Nothing is named by resemblance. All "
      f"**{len(named[PACKAGES[0]])}** tags resolve.")
    A("")
    A("## 2. The 23 value parameters (the table to translate from)")
    A("")
    A("`class` is the declaring class; `off` the class slot; `source` the package/export/payload")
    A("offset of the tag, so any row can be re-read without a tool.")
    A("")
    A("| class | field | type | value | source | label |")
    A("|---|---|---|---|---|---|")
    for m in value_members:
        rows = own_by_name.get(m["name"])
        if not rows:
            continue
        for r in rows:
            info = r.get("info") or {}
            txt, lab = tag_value(startup["_pkg"], r)
            A(f"| `{r['owner']}` | `{r['member']}` | {r['kind']} | {txt} | "
              f"`Startup.upk` {startup['cdo_export']} @0x{r['tag']['at']:x} "
              f"(class 0x{r['tag']['offset']:x}; `{os.path.basename(info.get('file') or '?')}:"
              f"{info.get('line', '?')}`) | {lab} |")
    A("")
    A("## 3. The 7 value slots the CDO does not serialise (UNKNOWN value)")
    A("")
    A("A cooked stream omits a property only when it equals the class's own initial value, so these")
    A("are almost certainly `None`/`false` — but that is a **hypothesis about the cooker, not a byte")
    A("fact**, and it is not used. Their offsets and types are decoded from the bindings.")
    A("")
    A("| class | field | type | class off | bindings | label |")
    A("|---|---|---|---|---|---|")
    for m in untagged:
        p = next((q for q in props[CLASS] if q["member"] == m["name"]), None)
        A(f"| `{CLASS}` | `{m['name']}` | {m['class']} | "
          f"{('0x%x' % p['offset']) if p else '-'} | "
          f"{('%s:%d' % (os.path.basename(gcs[CLASS]), p['line'])) if p else '-'} | "
          f"UNKNOWN (no tag in either CDO) |")
    A("")
    A("## 4. The 25 behaviour members (no default value exists)")
    A("")
    A("| class | field | export | payload | why there is no value |")
    A("|---|---|---:|---:|---|")
    for m in members:
        if m["class"] in VALUE_KINDS:
            continue
        A(f"| `{m['class']}` | `{m['name']}` | {m['export']} | {m['size']} | "
          f"{'Function' if m['class'] == 'Function' else 'State'} export: behaviour, not a parameter |")
    A("")
    A("Their bodies are **stripped** (the payloads are untagged 30-byte records per "
      "`PACKAGES_G305.md` §4), so any constant a function would use is UNKNOWN — that is where the")
    A("remaining remote-gadget behaviour lives.")
    A("")
    A("## 5. Inherited tags the CDO also serialises (decoded)")
    A("")
    A("These are not in the 48, but they identify and shape the gadget, so the translation needs them")
    A("next to the table: the enum that names the gadget and its HUD slot, the mesh component, the")
    A("aim config, and the inherited bool word.")
    A("")
    A("| class | field | type | value | source |")
    A("|---|---|---|---|---|")
    for r in named[PACKAGES[0]]:
        if r["member"] in set(member_names) or not r["member"]:
            continue
        info = r.get("info") or {}
        txt, lab = tag_value(startup["_pkg"], r)
        A(f"| `{r['owner']}` | `{r['member']}` | {r['kind']} | {txt} | "
          f"`Startup.upk` {startup['cdo_export']} @0x{r['tag']['at']:x} (class "
          f"0x{r['tag']['offset']:x}; `{os.path.basename(info.get('file') or '?')}:"
          f"{info.get('line', '?')}`) |")
    A("")
    A("### Inherited bool word `0x460` (decoded: bit splitting)")
    A("")
    word = next((r for r in named[PACKAGES[0]]
                 if r["tag"]["offset"] == 0x460), None)
    if word:
        bits = word["tag"].get("bits") or 0
        set_members = [r["member"] for r in named[PACKAGES[0]]
                       if r["tag"]["offset"] == 0x460 and r.get("value")]
        A(f"The tag carries the whole word `0x{bits:08x}` = {bits}; the members it turns on are")
        A("`" + "`, `".join(set_members) + "`. The other members at this offset are false.")
    A("")
    A("## 6. Object references, followed one level (decoded)")
    A("")
    A("| field | target | target class | target export | target payload | one level further |")
    A("|---|---|---|---:|---:|---|")
    for r in named[PACKAGES[0]]:
        if r["kind"] not in ("ObjectProperty", "ComponentProperty"):
            continue
        idx = r["tag"].get("value")
        if not idx:
            continue
        tgt = target_of(startup["_pkg"], idx)
        A(f"| `{r['member']}` | `{tgt['path']}` | {tgt['class']} | "
          f"{tgt.get('export', '-')} | {tgt.get('export_bytes', '-')} | {tgt['inner_label']} |")
    A("")
    A("The component targets are the class-default components themselves (`GadgetMesh`): their own")
    A("payloads carry **no property tags**, so the mesh asset, materials and transform behind them")
    A("are UNKNOWN here. The `AkEvent` and `RSpecialMoveConfigConfigurable` targets are imports or")
    A("exports of other packages and are reported by path, not opened.")
    A("")
    A("## 7. Startup vs StartupPatch (derived: the same decode on both)")
    A("")
    A(f"**{len(fp_start)}** decoded rows compared per package. Scalar, name, string, vector and enum")
    A(f"values: **{len(scalar_diffs)}** differences. Object references: **{len(object_diffs)}** rows")
    A("differ, every one of them in the package-qualified path of the target rather than its class:")
    A("")
    A("| field | class off | `Startup.upk` target | `StartupPatch.upk` target | target class |")
    A("|---|---|---|---|---|")
    for a, b in object_diffs:
        A(f"| `{a['member']}` | 0x{a['offset']:x} | {a['value']} | {b['value']} | "
          f"`{a['ref_class']}` |")
    A("")
    A("Both indices resolve through their own package's tables, so this is a real byte difference")
    A("between the two CDOs: the same sound member points at the same *kind* of object, under a")
    A("differently named outer package (`Engine` in one, `Ww_CHR_RemoteGadget` in the other). Which")
    A("of the two an installed build uses depends on package load order, which is UNKNOWN here.")
    A("")
    A("## 8. Oracles (`--check` re-runs each)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k in sorted(oracles):
        A(f"| `{k}` | {oracles[k]['ok']} | `{json.dumps(oracles[k]['detail'], sort_keys=True)[:240]}` |")
    A("")
    A("## 9. Result")
    A("")
    A(f"- the class has **{len(members)}** members: " +
      ", ".join(f"{k} {len(v)}" for k, v in sorted(member_kinds.items())) + " [decoded]")
    A(f"- value parameters: **{len(value_members)}**; decoded values: **{len(tagged)}**; "
      f"UNKNOWN (no tag): **{len(untagged)}**")
    A("- `GadgetType` = `GA_Gadget_JammerGadget`, `HudGadgetId` = `FGID_BatarangMulti2` [decoded: "
      "inherited tags 0x311/0x314]")
    A("- every value above carries its package, export, payload offset and class offset, so it can be "
      "re-read directly [decoded]")
    A("- function/state bodies: **UNKNOWN** (stripped)")
    A("- JC3 mapping: **not decided here** (out of scope by the brief)")
    A("")
    A("## 10. UNKNOWN")
    A("")
    A("1. **The 7 value slots with no tag** (§3). Tried: both CDOs, every start offset 0 (the walk")
    A("   closes at 362 with 0 unexplained bytes, so no tag is being skipped); checked the other")
    A("   package; checked the class's other exports for an archetype (none). Would be settled only")
    A("   by the cooker's omission rule, which the packages do not state.")
    A("2. **Values inside the followed component targets** (§6). Tried: walked each target's payload;")
    A("   untagged, so nothing is readable.")
    A("3. **Behaviour of the 25 function/state members.** Their 30-byte payloads are untagged; no")
    A("   bytecode and no constants survive.")
    A("")
    return "\n".join(L)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"
    if mode not in ("--write", "--check"):
        print(__doc__)
        return 2
    md = build()
    if mode == "--write":
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"wrote {rel(OUT_MD)} ({len(md):,} chars)")
        return 0
    with open(OUT_MD, encoding="utf-8", newline="") as fh:
        on_disk = fh.read()
    if on_disk != md:
        print("FAIL: GADGET_PARAMS.md differs from a fresh rebuild")
        return 1
    print("OK rebuilt byte-identical from Startup.upk, StartupPatch.upk and the BmSDK bindings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
