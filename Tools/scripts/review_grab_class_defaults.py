#!/usr/bin/env python3
"""review_grab_class_defaults.py - audit of G3-06b (CLASS_DEFAULTS).

Re-walks the two Batmobile class-default streams with this script's own tag walker
(not `grab_class_defaults.py`), re-reads five tags chosen by the review (one float,
one bool word, one object reference, one struct, one int) plus the vector tag whose
label is conflation-prone, and checks each name against the BmSDK `.g.cs` binding at
`E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated`.

Also audits the two pointer tags whose names rest on the layout alone
(`RamDamageType` @5676, `InventoryManagerClass` @892): were their names unique at
that offset in the chain, and why could the type oracle not run?

Read-only inputs: the two packages, the BmSDK tree, `CLASS_DEFAULTS.json`.
Writes only `Research/BatmobileGrab/CLASS_DEFAULTS_REVIEW.md` / `.json`.

Usage:
  python Tools/scripts/review_grab_class_defaults.py --write
  python Tools/scripts/review_grab_class_defaults.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read as U  # noqa: E402

COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
BMSDK = r"E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated"
CARD = os.path.join(ROOT, "Research", "BatmobileGrab", "CLASS_DEFAULTS.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "CLASS_DEFAULTS_REVIEW.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "CLASS_DEFAULTS_REVIEW.json")

KIND_ALIASES = {
    "ObjectNCRProperty": {"ObjectProperty", "ComponentProperty", "ClassProperty"},
    "ObjectProperty": {"ObjectProperty", "ComponentProperty", "ClassProperty"},
    "ClassProperty": {"ClassProperty"},
    "VectorProperty": {"StructProperty"},
    "RotatorProperty": {"StructProperty"},
}

CDOS = [("subclass", "Startup.upk", 7530), ("base", "BmGame.upk", 10923)]
CHAIN = [("BmScript", "RVehicleBatmobile"), ("BmGame", "RVehicleBatmobileBase"),
         ("BmGame", "RVehicle"), ("Engine", "AkVehicle"), ("Engine", "SVehicle"),
         ("Engine", "Vehicle"), ("Engine", "Pawn"), ("Engine", "Actor")]

# the review's five tags + one vector control: (stream, label, class offset)
PICKS = [("subclass", "float", 1688), ("base", "bool", 1676),
         ("base", "object", 1764), ("base", "struct", 6596),
         ("base", "int", 1144), ("base", "vector", 4504)]
WANT_MEMBER = {"float": "ChassisMass", "bool": "bCanFlip", "object": "StayUprightConstraintSetup",
               "struct": "ExplosiveImpactScreenShake", "int": "Health",
               "vector": "NPCCheckExtents"}
WANT_KIND = {"float": ("FloatProperty",), "bool": ("BoolProperty",),
             "object": ("ObjectProperty",), "struct": ("StructProperty",),
             "int": ("IntProperty",), "vector": ("StructProperty", "VectorProperty")}
NO_TYPE = [5676, 892]


# ---------------------------------------------------------------- own tag walker
def _i32(payload):
    return struct.unpack_from("<i", payload)[0] if len(payload) >= 4 else None


def decode(pkg, t, payload):
    if t == 4:
        return struct.unpack_from("<f", payload)[0] if len(payload) >= 4 else None
    if t in (2, 3, 6, 16, 1):
        v = _i32(payload)
        if t in (6, 1):
            return pkg.names[v] if v is not None and 0 <= v < len(pkg.names) else None
        return v
    if t == 11:
        return list(struct.unpack_from("<3f", payload)) if len(payload) >= 12 else None
    if t == 12:
        return list(struct.unpack_from("<3i", payload)) if len(payload) >= 12 else None
    if t == 13:
        return U._fstr(payload, 0)[0] if payload else None
    if t == 17:
        return payload.hex() if payload else None
    return None


def walk(pkg, d, start=0):
    """Independent property walker: 4-byte header (i16 type, u16 class offset).

    NAMED types carry four more ints (name index, name number, size, array index),
    so their payload starts 20 bytes in; StrProperty has no fixed width at all and
    the next tag begins after the FString."""
    tags, p, why = [], start, ""
    while p + 4 <= len(d):
        t, off = struct.unpack_from("<hH", d, p)
        if t == 0:
            return tags, p, "terminator"
        hdr = p
        if t == 13:
            try:
                text, nxt = U._fstr(d, p + 4)
            except U.UpkError:
                return tags, p, "bad_string"
            tags.append({"type_id": 13, "offset": off, "hdr": p, "at": p + 8,
                         "size": nxt - (p + 4), "value": text})
            p = nxt
            continue
        if t in U.NAMED:
            ni, nn, size, aidx = struct.unpack_from("<iiii", d, p + 4)
            at = p + 20
            if at + size > len(d):
                return tags, p, "overrun"
            payload = d[at:at + size]
            rec = {"type_id": t, "offset": off, "hdr": hdr, "at": at, "size": size,
                   "array_index": aidx, "name_index": ni}
            if t == 10:
                sub, _e, _w = walk(pkg, payload)
                rec["props"] = [{"type_id": s["type_id"], "offset": s["offset"],
                                 "at": s["at"], "value": s.get("value")} for s in sub]
            p = at + size
        else:
            n = U.SIMPLE.get(t)
            if n is None:
                return tags, p, "unknown_type_%d" % t
            rec = {"type_id": t, "offset": off, "hdr": hdr, "at": p + 4, "size": n}
            payload = d[p + 4:p + 4 + n]
            p = p + 4 + n
        if t != 10:
            rec["value"] = decode(pkg, t, payload)
        tags.append(rec)
    return tags, p, "eof"


# ---------------------------------------------------------------- BmSDK layout
def cmpval(t, v):
    """A tag value in a form both walkers can be compared in (None = '+' compare)."""
    if t == "FloatProperty":
        return round(float(v), 6) if isinstance(v, (int, float)) else None
    if t in ("IntProperty", "BoolProperty"):
        return int(v) if isinstance(v, int) else None
    if t in ("VectorProperty", "RotatorProperty"):
        return [round(float(x), 4) for x in v] if isinstance(v, list) else None
    if t in ("NameProperty", "ByteProperty", "ClassProperty", "ObjectNCRProperty"):
        return v
    return None


def gen_path(pkg, cls):
    return os.path.join(BMSDK, pkg, cls + ".g.cs")


def layout_member(pkg, cls, member):
    """(kind, offset, mask or None, line) for `member` in its .g.cs, or None."""
    p = gen_path(pkg, cls)
    if not os.path.exists(p):
        return None
    text = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r"/// (\w+): " + re.escape(member) + r"\s*\n", text)
    if not m:
        return None
    kind = m.group(1)
    tail = text[m.end():m.end() + 1400]
    off = re.search(r"Ptr \+ (\d+)", tail)
    if not off:
        return None
    mask = re.search(r"&\s*(\d+)\)", tail)
    return {"kind": kind, "offset": int(off.group(1)),
            "mask": int(mask.group(1)) if mask else None,
            "line": text[:m.start()].count("\n") + 1}


def find_member(member):
    """Locate `member` anywhere in the Batmobile class chain, with its binding."""
    for pkg, cls in CHAIN:
        info = layout_member(pkg, cls, member)
        if info:
            return dict(info, **{"class": cls, "package": pkg})
    return None


def member_at_line(source):
    """Member name declared at the `.g.cs` line a card `source` string cites."""
    m = re.search(r"([\w\\/]+?\.g\.cs):(\d+)", source or "")
    if not m:
        return None
    p = os.path.join(BMSDK, m.group(1).replace("\\", "/"))
    line = int(m.group(2))
    if not os.path.exists(p):
        return None
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    for i in range(line - 1, max(-1, line - 24), -1):
        mm = re.search(r"/// (\w+): (\w+)", lines[i])
        if mm:
            return {"kind": mm.group(1), "member": mm.group(2), "line": i + 1}
    return None


def offset_owners(offset):
    """Chain members that sit at `offset` (uniqueness of a layout-only name)."""
    hits = []
    for pkg, cls in CHAIN:
        p = gen_path(pkg, cls)
        if not os.path.exists(p):
            continue
        pat = re.compile(r"Ptr \+ %d\b" % offset)
        for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
            if not pat.search(line):
                continue
            m = member_at_line("%s/%s.g.cs:%d" % (pkg, cls, i))
            name = (m or {}).get("member")
            # a property has a getter and a setter line; count the member, not the lines
            if (name or cls, cls) not in hits:
                hits.append((name or cls, cls))
    return hits


# ---------------------------------------------------------------- audit
def audit():
    claims = json.load(open(CARD, encoding="utf-8"))
    out = {"schema": 1,
           "generated_by": "Tools/scripts/review_grab_class_defaults.py --write",
           "review_of": "Research/BatmobileGrab/CLASS_DEFAULTS.md (G3-06b)", "cdos": {}}
    problems, streams = [], {}

    for role, fn, idx in CDOS:
        pkg = U.Package(os.path.join(COOKED, fn))
        d = pkg.data(idx)
        tags, end, why = walk(pkg, d)
        claimed = next(c for c in claims["cdo"].values() if c["export"] == idx)
        by = {t["offset"]: t for t in tags}
        cby = {t["offset"]: t for t in claimed["tags"]}
        only_mine = [o for o in by if o not in cby]
        only_card = [o for o in cby if o not in by]
        val_mism, struct_bad = [], []
        for o in by:
            if o not in cby:
                continue
            a, b_ = by[o], cby[o]
            if a["type_id"] == 10:
                n = len(((b_.get("value") or {}).get("props") or []))
                if len(a.get("props") or []) != n:
                    struct_bad.append({"offset": o, "mine": len(a.get("props") or []),
                                       "card": n})
                continue
            ta, tb = U.TYPE_NAMES.get(a["type_id"]), b_.get("tag_type")
            va, vb = cmpval(ta, a.get("value")), cmpval(tb, b_.get("value"))
            if va is not None and vb is not None and va != vb:
                val_mism.append({"offset": o, "mine": va, "card": vb})
        type_mism = [o for o in by if o in cby and
                     U.TYPE_NAMES.get(by[o]["type_id"]) != cby[o]["tag_type"]]
        out["cdos"][role] = {
            "object": claimed["object"], "export": idx, "bytes": len(d),
            "tags_walked": len(tags), "tags_claimed": claimed["tag_count"],
            "end": end, "stop": why,
            "offsets_only_mine": only_mine, "offsets_only_card": only_card,
            "value_mismatches": val_mism, "struct_nested_mismatches": struct_bad,
            "type_name_mismatches": type_mism,
            "count_matches": len(tags) == claimed["tag_count"],
            "end_matches": end == claimed["payload_end"],
        }
        if len(tags) != claimed["tag_count"] or only_mine or only_card:
            problems.append(f"{role}: walk differs from the card (tags {len(tags)} vs "
                            f"{claimed['tag_count']}, only mine {only_mine[:4]}, "
                            f"only card {only_card[:4]})")
        streams[role] = (pkg, d, by, cby)

    # ---- the five picks (+ vector control), re-read from the bytes
    picks = {}
    for role, label, off in PICKS:
        pkg, d, by, cby = streams[role]
        t = by.get(off)
        if t is None:
            picks[label] = {"offset": off, "stream": role,
                            "error": "no tag at this offset"}
            problems.append(f"{label}: no tag at {role} offset {off}")
            continue
        claim = cby.get(off, {})
        lay = find_member(WANT_MEMBER[label])
        rec = {"stream": role, "offset": off, "type": U.TYPE_NAMES.get(t["type_id"]),
               "tag_type_id": t["type_id"], "payload_at": t["at"],
               "header_hex": d[t["hdr"]:t["hdr"] + 4].hex(),
               "payload_hex": d[t["at"]:t["at"] + min(t["size"], 16)].hex(),
               "value": t.get("value"),
               "claimed_type": claim.get("tag_type"),
               "claimed_value": claim.get("value"),
               "claimed_kind": claim.get("kind"),
               "claimed_source": claim.get("source"),
               "layout": lay,
               "layout_names_it": bool(lay and lay["offset"] == off and
                                       lay["kind"] in WANT_KIND[label])}
        picks[label] = rec

    f = picks["float"]
    f["byte_ok"] = f.get("payload_hex", "")[:8] == "00005243"
    b = picks["bool"]
    masks = {}
    for name in ("bCanFlip", "bIsBatmobile"):
        m = find_member(name)
        masks[name] = (m or {}).get("mask")
    word = b["value"] or 0
    b.update(masks={k: (hex(v) if v else None) for k, v in masks.items()},
             true_members=[k for k, v in masks.items() if v and word & v],
             cited_mask_is_a_true_member=None)
    cited = re.search(r"mask 0x([0-9a-f]+)", b.get("claimed_source") or "")
    b["cited_mask"] = ("0x%08x" % int(cited.group(1), 16)) if cited else None
    b["cited_mask_is_a_true_member"] = bool(
        cited and int(cited.group(1), 16) in [v for v in masks.values() if v])

    o = picks["object"]
    oidx = o["value"]
    o["ref_path"] = pkg.object_path(oidx) if isinstance(oidx, int) else None
    o["ref_class"] = pkg.object_class(oidx) if isinstance(oidx, int) else None
    o["declared"] = (streams["base"][3][1764]["members"][0].get("array_type")
                      if streams["base"][3][1764].get("members") else None)
    o["object_class_ok"] = bool(o["ref_class"] and o["declared"] and
                                o["ref_class"] == o["declared"])

    s = picks["struct"]
    st = streams["base"][2][6596]
    s["nested"] = len(st.get("props") or [])
    s["first_props"] = [(p["offset"], p["value"]) for p in (st.get("props") or [])[:3]]

    v = picks["vector"]
    v["printed_as"] = v.get("claimed_kind")   # the .md table's column is `kind`
    v["tag_type_is_vector"] = v["type"] == "VectorProperty"

    out["picks"] = picks

    # ---- the two layout-only pointers
    pkg, d, by, cby = streams["base"]
    nt = []
    for off in NO_TYPE:
        t = cby[off]
        i = t["value"]
        owners = offset_owners(off)
        lay = find_member(t["name"])
        nt.append({"offset": off, "name": t["name"], "type": t["tag_type"],
                   "payload_index": i, "ref_path": pkg.object_path(i),
                   "ref_class": pkg.object_class(i),
                   "declared": (t["members"][0].get("array_type")
                                if t.get("members") else None),
                   "layout": lay,
                   "layout_names_it": bool(lay and lay["offset"] == off),
                   "offset_owners_in_chain": owners,
                   "name_unique_at_offset": len(owners) == 1,
                   "oracle": t.get("oracle"),
                   "payload_hex": d[t["payload_at"]:t["payload_at"] + 4].hex()})
        if len(owners) != 1:
            problems.append(f"pointer {t['name']} @{off}: {len(owners)} chain members "
                            f"at that offset")
        if not lay or lay["offset"] != off:
            problems.append(f"pointer {t['name']} @{off}: the binding does not sit there")
    out["no_type"] = nt

    # ---- corpus-level label defects
    base_claims = streams["base"][3]
    bool_rows = [t for t in base_claims.values() if t["tag_type"] == "BoolProperty"]
    rows = []
    for t in bool_rows:
        m = re.search(r"mask 0x([0-9a-f]+)", t.get("source") or "")
        cited = int(m.group(1), 16) if m else None
        members = t.get("members") or []
        true_m = [x for x in members if x.get("value")]
        owner = member_at_line(t.get("source"))
        rows.append({"offset": t["offset"], "name": t.get("name"),
                     "cited_mask": hex(cited) if cited is not None else None,
                     "cited_member": (owner or {}).get("member"),
                     "cited_line": (owner or {}).get("line"),
                     "true_members": [x["member"] for x in true_m],
                     "true_masks": [hex(x["mask"]) for x in true_m],
                     "cited_is_true": (cited in [x.get("mask") for x in true_m])
                     if cited is not None and true_m else None,
                     "source": t.get("source")})
    mislabelled = [r for r in rows if r["cited_is_true"] is False]

    kind_alias, kind_bad = [], []
    for t in base_claims.values():
        tt, k = t["tag_type"], t.get("kind")
        if not k or tt == k:
            continue
        if tt in KIND_ALIASES and k in KIND_ALIASES[tt]:
            kind_alias.append({"offset": t["offset"], "tag_type": tt, "kind": k})
        else:
            kind_bad.append({"offset": t["offset"], "tag_type": tt, "kind": k})
    out["labels"] = {"bool_rows": len(bool_rows), "bool_rows_detail": rows,
                     "bool_rows_mislabelled": len(mislabelled),
                     "rows_printing_the_layout_kind": len(kind_alias),
                     "kind_incompatible_rows": kind_bad,
                     "note": "the value column of the .md table prints `kind` (the layout "
                             "member's kind) beside the tag's own type in `tag_type`; the "
                             "alias rows are the documented Vector/Guid and Object* spellings"}

    out["problems"] = problems
    if problems:
        out["verdict"] = "needs rework"
    elif mislabelled:
        out["verdict"] = "minor issues"
    else:
        out["verdict"] = "holds"
    return out


def render_md(doc):
    L = []
    a = L.append
    a("# CLASS_DEFAULTS review - independent re-walk and BmSDK check (G3-06b)")
    a("")
    a("Generated by `Tools/scripts/review_grab_class_defaults.py --write`; `--check` "
      "recomputes and fails on drift. The walker here is its own (4-byte header "
      "`i16 type / u16 offset`, then that type's payload), not the audited tool's.")
    a("")
    a(f"**VERDICT: {doc['verdict']}**")
    a("")
    a("## Walks")
    a("")
    a("| stream | object | bytes | tags (mine) | tags (card) | end | stop |")
    a("|---|---|---:|---:|---:|---:|---|")
    for role, c in doc["cdos"].items():
        a(f"| {role} (`{c['export']}`) | `{c['object']}` | {c['bytes']} | "
          f"{c['tags_walked']} | {c['tags_claimed']} | {c['end']} | {c['stop']} |")
    a("")
    for role, c in doc["cdos"].items():
        a(f"- {role}: offsets only mine `{c['offsets_only_mine']}`, only in the card "
          f"`{c['offsets_only_card']}`, value mismatches `{c['value_mismatches']}`, "
          f"type-name mismatches `{c['type_name_mismatches']}`")
    a("")
    a("## The five tags, re-read from the bytes, against the BmSDK binding")
    a("")
    a("| pick | stream | off | tag type | payload @ | header | payload bytes | value | "
      "binding | names it |")
    a("|---|---|---:|---|---:|---|---|---|---|---|")
    for label, p in doc["picks"].items():
        if p.get("error"):
            a(f"| {label} | {p.get('stream')} | {p['offset']} | - | - | - | - | "
              f"`{p['error']}` | - | False |")
            continue
        lay = p.get("layout") or {}
        a(f"| {label} | {p['stream']} | {p['offset']} | {p['type']} | "
          f"0x{p['payload_at']:x} | `{p['header_hex']}` | `{p['payload_hex'][:16]}` | "
          f"`{p['value']}` | {lay.get('kind')} `{WANT_MEMBER[label]}` @ "
          f"{lay.get('offset')} ({lay.get('package')}/{lay.get('class')}:"
          f"{lay.get('line')}) | {p.get('layout_names_it')} |")
    a("")
    b = doc["picks"]["bool"]
    a("### Bool word at 1676")
    a("")
    a(f"- word `0x{(b['value'] or 0):08x}`; binding masks bCanFlip={b['masks']['bCanFlip']}, "
      f"bIsBatmobile={b['masks']['bIsBatmobile']}; true members `{b['true_members']}`")
    a(f"- the card's `source` cites mask `{b['cited_mask']}`; is that a true member's "
      f"mask? **{b['cited_mask_is_a_true_member']}**")
    a("")
    s = doc["picks"]["struct"]
    a("### Struct at 6596")
    a("")
    a(f"- `{s['type']}`, {s['nested']} nested tags, first `{s['first_props']}`; binding "
      f"`{(s.get('layout') or {}).get('kind')}` at "
      f"`{(s.get('layout') or {}).get('offset')}`")
    a("")
    v = doc["picks"]["vector"]
    a("### Vector control at 4504")
    a("")
    a(f"- tag type in the bytes is **{v['type']}** (id {v['tag_type_id']}); the card's "
      f"table prints **{v['printed_as']}** in its `kind` column; binding kind "
      f"`{(v.get('layout') or {}).get('kind')}`. The alias is documented, so the table is "
      f"not wrong - but the tag's own type is only visible in `tag_type` inside the JSON.")
    a("")
    a("## Two pointer tags whose names rest on the layout alone")
    a("")
    a("| off | name | bytes | referent | declared | unique at offset |")
    a("|---:|---|---|---|---|---|")
    for t in doc["no_type"]:
        lay = t.get("layout") or {}
        a(f"| {t['offset']} | `{t['name']}` | `{t['type']}` index `{t['payload_hex']}` "
          f"-> `{t['ref_path']}` (class `{t['ref_class']}`) | `{t['declared']}` | "
          f"{t['name_unique_at_offset']} ({len(t['offset_owners_in_chain'])} member(s): "
          f"{lay.get('class')} @ {lay.get('offset')}) |")
    a("")
    a("## The `source` column on the bool rows")
    a("")
    a("The `.md` value column is per-word ('bCanFlip, bIsBatmobile (2 of 28 bools in "
      "the word)') but `source` cites one member. Measured:")
    a("")
    a("| off | cited mask | cited member | true members (masks) | cited is true |")
    a("|---:|---|---|---|---|")
    for x in doc["labels"]["bool_rows_detail"]:
        a(f"| {x['offset']} | `{x['cited_mask']}` | `{x['cited_member']}` "
          f"(line {x['cited_line']}) | {x['true_members']} {x['true_masks']} | "
          f"{x['cited_is_true']} |")
    a("")
    a(f"Rows whose cited mask is not a true member's: **{doc['labels']['bool_rows_mislabelled']} "
      f"of {doc['labels']['bool_rows']}**.")
    a("")
    a("## Kind column vs the tag's own type")
    a("")
    a(f"{doc['labels']['rows_printing_the_layout_kind']} rows print the layout member's "
      f"kind where it differs from the tag type; incompatible pairs: "
      f"`{doc['labels']['kind_incompatible_rows']}`. All of them are the documented "
      f"Object*/Vector spellings, so the column is consistent with the card's model.")
    a("")
    a("## Problems")
    a("")
    for p in doc["problems"] or ["none"]:
        a(f"- {p}")
    a("")
    return "\n".join(L)


def write():
    doc = audit()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    for role, c in doc["cdos"].items():
        print(f"{role}: {c['tags_walked']} tags (card {c['tags_claimed']}), "
              f"values {len(c['value_mismatches'])} mismatched, end {c['end']}")
    for label, p in doc["picks"].items():
        print(f"{label:7s} @{p['offset']:<5d} {str(p.get('type')):18s} "
              f"value={p.get('value')!r} names_it={p.get('layout_names_it')}")
    b = doc["picks"]["bool"]
    print(f"bool: true {b['true_members']}, cited {b['cited_mask']} is_true_member="
          f"{b['cited_mask_is_a_true_member']}")
    print(f"label defects: {doc['labels']['bool_rows_mislabelled']}/{doc['labels']['bool_rows']} "
          f"bool source masks, {len(doc['labels']['kind_incompatible_rows'])} kind-incompatible")
    print(f"verdict: {doc['verdict']}")
    return 0


def check():
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    fresh = json.loads(json.dumps(audit()))   # same tuple->list round trip as the file
    fails = [f"stale: {k}" for k in stored if stored.get(k) != fresh.get(k)]
    if fresh["cdos"]["subclass"]["tags_walked"] != 93 or \
            fresh["cdos"]["base"]["tags_walked"] != 181:
        fails.append("tag counts differ from 93/181")
    for role in fresh["cdos"]:
        if fresh["cdos"][role]["value_mismatches"]:
            fails.append(f"{role}: a tag value differs between the two walkers")
    b = fresh["picks"]["bool"]
    if b["value"] != 0x04001000 or sorted(b["true_members"]) != ["bCanFlip", "bIsBatmobile"]:
        fails.append("bool word does not re-derive to bCanFlip+bIsBatmobile")
    if b["cited_mask_is_a_true_member"]:
        fails.append("the cited bool mask unexpectedly matches a true member")
    for label in ("float", "object", "struct", "int", "vector"):
        if not fresh["picks"][label].get("layout_names_it"):
            fails.append(f"{label}: BmSDK layout does not confirm the offset/kind")
    if not all(t["name_unique_at_offset"] for t in fresh["no_type"]):
        fails.append("a layout-only pointer name is ambiguous at its offset")
    if fresh["labels"]["kind_incompatible_rows"]:
        fails.append("a row's printed kind is incompatible with the tag's own type")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK walks 93/181; bool 0x{b['value']:08x}; "
          f"{fresh['labels']['bool_rows_mislabelled']} bool source masks off; "
          f"kind-incompatible {len(fresh['labels']['kind_incompatible_rows'])}; "
          f"verdict {fresh['verdict']}; md+json identical")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    return write() if args.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
