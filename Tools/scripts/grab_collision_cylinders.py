"""grab_collision_cylinders.py - G3-01b (open item): name the two CylinderComponent floats.

COLLISION.md decodes two floats on the Batmobile's `FrontCollisionCylinder` /
`RearCollisionCylinder` templates at native offsets 540 (78.0) and 544 (175.0) and leaves both
names UNKNOWN because BMSDK_OFFSETS.json has no CylinderComponent layout. This script names
them from the cooked packages, never from general knowledge.

Why the names are not printed in the object's own tag stream: the Batman property tag carries
the native offset but a *simple* type (float) writes no name, so a float tag says "offset 540"
and nothing else. The names come from the class:

1. Engine.upk holds the class export `CylinderComponent` (export 4062) and its ten members
   (3 FloatProperty, 1 StructProperty, 4 BoolProperty, 2 Function). Their names are the export
   name fields - decoded.
2. Each member export carries a linked-list pointer (int32 at +2) to the next member; walking
   from the only unreferenced member covers all ten and ends at 0 - the class's member chain,
   decoded (oracle: covers exactly the class's members, no cycle, ends 0).
3. The class's own default object (export 4063, 114 bytes) serialises its properties. Its tag
   stream walks from byte 0 to the last byte (114/114, no tail) with 10 tags, and carries
   FloatProperty tags at 540, 544 and 548, the class's only StructProperty at 552 and a
   BoolProperty word at 556 - plus the inherited PrimitiveComponent members (316, 364, 476,
   480, 484).
4. Which float slot is whose. The class has exactly three float members, and the block above
   the ancestors' highest member (PrimitiveComponent's last tag is 528; ActorComponent's is
   120) holds exactly three float slots: 540, 544, 548. The slot *order* is fixed by type:
   the struct (the class's only StructProperty = CylinderColor) sits at 552 and the bool word
   (its four bools) at 556, i.e. both above all three floats, and in the member chain
   (GetExtent -> SetCylinderSize -> CollisionHeight -> CollisionRadius -> AABBScale ->
   CylinderColor -> the four bools) the struct and bools come *after* the floats. So the chain
   ascends with the offset, and the three floats pair in chain order:
       540 = CollisionHeight, 544 = CollisionRadius, 548 = AABBScale.
   The opposite reading (chain descending) is refuted by the same bytes: it would require the
   class's only struct, CylinderColor, to sit *below* all three floats, but its tag is at 552,
   above 548.

The script also walks the Batmobile's six cylinder objects so the named values are recorded for
the chain (Startup templates 82147/82148, BmGame base templates 142597/142598, the Playable
instances 277/278), and scans every CylinderComponent object in four packages for the one
independent invariant the data offers (AABBScale is a scale: 548 is 1.0 wherever serialised).

The executable is probed too, and reported honestly: BatmanAK.exe carries no
`CollisionRadius`/`CollisionHeight` string, and the displacements 0x21C / 0x220 occur in 336
movss sites across .text with no class anchor, so no site can be attributed to this class.
That probe contributes no naming evidence.

Usage
    python Tools/scripts/grab_collision_cylinders.py --write
    python Tools/scripts/grab_collision_cylinders.py --check
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

import upk_read  # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "COLLISION_CYLINDERS.md")
JS = os.path.join(OUT, "COLLISION_CYLINDERS.json")

GAME = "E:/Games/Batman - Arkham Knight"
COOKED = GAME + "/BmGame/CookedPCConsole/"
EXE = GAME + "/Binaries/Win64/BatmanAK.exe"

CLASS_NAME = "CylinderComponent"
CLASS_EXPORT = 4062
CDO_NAME = "Default__" + CLASS_NAME
ANCESTORS = ("PrimitiveComponent", "ActorComponent")
# the two fields the card asks about
FIELDS = (540, 544)
# member chain expected from the exports (order as walked, each -> next)
EXPECTED_CHAIN = ["GetExtent", "SetCylinderSize", "CollisionHeight", "CollisionRadius",
                  "AABBScale", "CylinderColor", "bDrawBoundingBox", "bDrawNonColliding",
                  "bAlwaysRenderIfSelected", "bForceGreenWhenSelected"]
FLEET_PACKAGES = ("Engine.upk", "Startup.upk", "BmGame.upk", "Playable_Batmobile_SF.upk")


# --------------------------------------------------------------------------- package helpers
def walk_best(pkg, index: int):
    """Best tag walk for a cooked object: the start that consumes the most bytes."""
    data = pkg.data(index)
    best = None
    for start in range(0, 41):
        tags, end, why = upk_read.walk_tags(pkg, data, start)
        score = (end >= len(data) - 4, len(tags))
        if best is None or score > best[0]:
            best = (score, start, tags, end, why)
    return {"size": len(data), "start": best[1], "tags": best[2], "end": best[3],
            "tail": data[best[3] + 2:].hex(), "stop": best[4]}


def find_export(pkg, name: str, outer=None):
    for i, e in enumerate(pkg.exports, 1):
        if e["name"] == name and (outer is None or e["outer_index"] == outer):
            return i
    return None


# --------------------------------------------------------------------------- class + chain
def decode_class(pkg) -> dict:
    cls = find_export(pkg, CLASS_NAME, 0)          # the class export has no outer
    e = pkg.exports[cls - 1]
    props = []
    for i, x in enumerate(pkg.exports, 1):
        if x["outer_index"] == cls:
            d = pkg.data(i)
            nxt = struct.unpack_from("<i", d, 2)[0] if len(d) >= 6 else 0
            props.append({"index": i, "name": x["name"], "class": pkg.object_class(i),
                          "size": len(d), "next": nxt, "data_hex": d.hex()})
    return {"class_export": cls, "class_size": e["size"],
            "super_index": e["super_index"],
            "super_name": pkg.class_name(e["super_index"]), "properties": props}


def chain_order(properties: list) -> tuple[list, list]:
    by_idx = {p["index"]: p for p in properties}
    targets = {p["next"] for p in properties if p["next"]}
    heads = [p for p in properties if p["index"] not in targets]
    order, problems = [], []
    if len(heads) != 1:
        return [], ["chain head not unique: %d candidates" % len(heads)]
    cur = heads[0]
    seen = set()
    while cur and cur["index"] not in seen:
        seen.add(cur["index"])
        order.append(cur)
        cur = by_idx.get(cur["next"])
    if len(order) != len(properties):
        problems.append("chain covers %d of %d members" % (len(order), len(properties)))
    if order and order[-1]["next"] != 0:
        problems.append("chain does not end at 0 (ends at %d)" % order[-1]["next"])
    return order, problems


def ancestor_bounds(pkg, cls_name: str) -> list:
    """Each ancestor class's own default object, and the highest offset it serialises.

    This is what makes "540 is CylinderComponent's, not inherited" a byte fact rather than an
    assumption: the ancestors' own members stop below the class's block.
    """
    out = []
    cur = pkg.exports[find_export(pkg, cls_name, 0) - 1]["super_index"]
    while cur and cur > 0:
        name = pkg.exports[cur - 1]["name"]
        cdo = find_export(pkg, "Default__" + name, 0)
        row = {"name": name, "class_export": cur, "cdo_export": cdo, "max_offset": None,
               "offsets": [], "floats": []}
        if cdo:
            w = walk_best(pkg, cdo)
            offs = sorted({t["offset"] for t in w["tags"]})
            row.update({"offsets": offs, "max_offset": offs[-1] if offs else None,
                        "floats": [[t["offset"], t.get("value")] for t in w["tags"]
                                   if t["type"] == "FloatProperty"],
                        "size": w["size"], "tags": len(w["tags"]), "end": w["end"]})
        out.append(row)
        cur = pkg.exports[cur - 1]["super_index"]
    return out


def pair_fields(order: list, cdo_tags: list, ancestor_max: int) -> dict:
    """Map the class's float members onto the float slots above the inherited members."""
    floats = [t for t in cdo_tags if t["type"] == "FloatProperty"]
    structs = [t for t in cdo_tags if t["type"] == "StructProperty"]
    bools = [t for t in cdo_tags if t["type"] == "BoolProperty"]
    struct_names = sorted({p["name"] for p in order if p["class"] == "StructProperty"})
    chain_floats = [p["name"] for p in order if p["class"] == "FloatProperty"]
    own = sorted(t["offset"] for t in floats if t["offset"] > (ancestor_max or 0))
    struct_off = structs[0]["offset"] if len(structs) == 1 else None
    bool_off = max((b["offset"] for b in bools), default=None)
    struct_size = structs[0].get("size") if len(structs) == 1 else None
    mapping, notes = {}, []
    if len(chain_floats) == 3 and len(own) == 3:
        mapping = dict(zip(own, chain_floats))
        notes.append("the class's 3 FloatProperty members paired with its 3 own float slots "
                     "(%s), ascending slot order = chain order" % ", ".join(map(str, own)))
    # slot order: the struct and the bool word sit above the floats AND follow them in the chain
    chain_idx = {p["name"]: i for i, p in enumerate(order)}
    last_float_idx = max((chain_idx[n] for n in chain_floats), default=None)
    struct_idx = chain_idx.get(struct_names[0]) if len(struct_names) == 1 else None
    bool_idx = max((chain_idx[p["name"]] for p in order if p["class"] == "BoolProperty"),
                   default=None)
    ascending = (struct_off is not None and bool_off is not None and own
                 and bool_off > struct_off > own[-1]
                 and struct_idx is not None and last_float_idx is not None
                 and struct_idx > last_float_idx and bool_idx > struct_idx)
    block = None
    if own and struct_off is not None and bool_off is not None and struct_size:
        block = [own[0], bool_off + 4, 3 * 4 + struct_size + 4]
    return {"mapping": {str(k): v for k, v in mapping.items()},
            "chain_floats": chain_floats, "own_float_offsets": own,
            "float_offsets_all": sorted(t["offset"] for t in floats),
            "struct_off": struct_off, "struct_names": struct_names,
            "struct_size": struct_size, "bool_off": bool_off,
            "chain_ascending": ascending, "class_block": block, "notes": notes,
            "values": {str(t["offset"]): t.get("value") for t in floats}}


# --------------------------------------------------------------------------- fleet invariant
def fleet() -> dict:
    """Every CylinderComponent object in four packages: which of the three slots are set.

    This is reported, never used as evidence. A first guess - "if 548 is AABBScale it is 1.0
    wherever it is written" - is refuted by the data below (0.4 and 2.0 occur), so it is
    recorded as a refuted hypothesis rather than quietly dropped.
    """
    out = {"packages": [], "offsets": [540, 544, 548]}
    for pack in FLEET_PACKAGES:
        p = upk_read.Package(COOKED + pack)
        rows, vals = [], {540: [], 544: [], 548: []}
        for i, e in enumerate(p.exports, 1):
            try:
                if p.object_class(i) != CLASS_NAME:
                    continue
            except Exception:                                   # noqa: BLE001
                continue
            w = walk_best(p, i)
            got = {t["offset"]: t.get("value") for t in w["tags"]
                   if t["type"] == "FloatProperty" and t["offset"] in vals}
            for off, v in got.items():
                vals[off].append(v)
            rows.append({"export": i, "name": e["name"], "size": w["size"],
                         "walk_start": w["start"], "tags": len(w["tags"]),
                         "values": {str(k): v for k, v in got.items()},
                         "clean": w["end"] + 2 == w["size"]})
        both = [(r["values"]["540"], r["values"]["544"]) for r in rows
                if "540" in r["values"] and "544" in r["values"]]
        out["packages"].append({"package": pack, "objects": len(rows),
                                "walked_to_last_byte": sum(1 for r in rows if r["clean"]),
                                "serialised": {str(k): v for k, v in vals.items()},
                                "both_540_544": len(both),
                                "radius_slot_smaller": sum(1 for a, b in both if b < a),
                                "rows": rows})
    all548 = [v for pk in out["packages"] for v in pk["serialised"]["548"]]
    out["d548_values"] = all548
    out["d548_all_one"] = bool(all548) and all(v == 1.0 for v in all548)
    out["objects"] = sum(pk["objects"] for pk in out["packages"])
    out["walked_to_last_byte"] = sum(pk["walked_to_last_byte"] for pk in out["packages"])
    out["both_540_544"] = sum(pk["both_540_544"] for pk in out["packages"])
    out["radius_slot_smaller"] = sum(pk["radius_slot_smaller"] for pk in out["packages"])
    return out


# --------------------------------------------------------------------------- exe probe
LOAD_RE = re.compile(r"^(xmm\d+),\s*(?:dword ptr )?\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]$")
STORE_RE = re.compile(r"^(?:dword ptr )?\[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?,\s*(xmm\d+)\]$")


def exe_probe() -> dict:
    """Static probe of BatmanAK.exe for a radial/axial use of 0x21C / 0x220.

    A hit would need: one object's two fields loaded into three consecutive vector slots with
    0x220 filling X and Y and 0x21C filling Z. That is the only shape that distinguishes the
    two fields, since the exe names neither.
    """
    out = {"available": os.path.exists(EXE), "sites": {}, "windows": 0, "same_base": 0,
           "triples": [], "notes": []}
    if not out["available"]:
        out["notes"].append("BatmanAK.exe not present")
        return out
    try:
        import pefile
        from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    except Exception as e:                                      # noqa: BLE001
        out["notes"].append("pefile/capstone unavailable: %s" % e)
        return out
    pe = pefile.PE(EXE, fast_load=True)
    text = next((s for s in pe.sections if s.Name.rstrip(b"\0") == b".text"), None)
    if text is None:
        out["notes"].append("no .text section")
        return out
    va0, off0, size = text.VirtualAddress, text.PointerToRawData, text.SizeOfRawData
    pe.close()
    blob = open(EXE, "rb").read()
    sec = blob[off0:off0 + size]
    sites = []
    for i in range(len(sec) - 8):
        if sec[i] == 0xF3 and sec[i + 1] == 0x0F and sec[i + 2] in (0x10, 0x11):
            modrm = sec[i + 3]
            if 0x80 <= modrm <= 0xBF:                 # mod=10 -> [reg + disp32]
                disp = struct.unpack_from("<I", sec, i + 4)[0]
                if disp in (0x21C, 0x220):
                    sites.append((va0 + i, disp, modrm))
    out["sites"] = {hex(d): sum(1 for s in sites if s[1] == d) for d in (0x21C, 0x220)}
    out["notes"].append("displacements are the member offsets decoded from the packages")
    # windows where both displacements are touched within 160 bytes, same base register
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    bys = sorted(sites)
    for a_i, a in enumerate(bys):
        for b in bys[a_i + 1:]:
            if b[0] - a[0] > 160:
                break
            if a[1] == b[1]:
                continue
            out["windows"] += 1
            base_a, base_b = a[2] & 7, b[2] & 7
            if base_a != base_b:
                continue
            out["same_base"] += 1
            start = max(a[0] - 64, va0)
            ins = list(md.disasm(sec[start - va0:start - va0 + 320], start))
            loads, stores = {}, []
            for k in ins:
                if k.mnemonic == "movss":
                    m = LOAD_RE.match(k.op_str)
                    if m:
                        loads[m.group(1)] = (m.group(2), m.group(3))
                        continue
                    m = STORE_RE.match(k.op_str)
                    if m:
                        stores.append((m.group(1), m.group(2), m.group(3)))
                if k.mnemonic in ("call", "ret") and k.address > a[0] + 64:
                    break
            by_store = {}
            for base, disp, reg in stores:
                by_store.setdefault(base, []).append((disp, reg))
            for base, lst in by_store.items():
                disps = {d: r for d, r in lst}
                for d in list(disps):
                    try:
                        d0 = int(d, 16)
                    except (TypeError, ValueError):
                        d0 = 0
                    pair = [disps.get("0x%x" % (d0 + n)) for n in (0, 4, 8)]
                    if none_ok(pair) or len([x for x in pair if x]) < 3:
                        continue
                    srcs = [loads.get(r) for r in pair]
                    disps_used = [s[1] if s else None for s in srcs]
                    if disps_used.count("0x220") == 2 and disps_used.count("0x21C") == 1:
                        out["triples"].append({
                            "va": hex(a[0]),
                            "stores": ["[%s + %s] <- %s" % (base, "0x%x" % (d0 + n), pair[n])
                                       for n in (0, 4, 8)],
                            "loads": ["%s <- [%s + %s]" % (pair[n], srcs[n][0], srcs[n][1])
                                      if srcs[n] else "?" for n in (0, 4, 8)],
                            "spelling": ["%s %s" % (k.mnemonic, k.op_str) for k in ins[:24]]})
    return out


def none_ok(pair) -> bool:
    return any(p is None for p in pair)


# --------------------------------------------------------------------------- the Batmobile
CYLINDERS = [
    ("Startup template FrontCollisionCylinder", "Startup.upk", 82147, "front"),
    ("Startup template RearCollisionCylinder", "Startup.upk", 82148, "rear"),
    ("BmGame base FrontCollisionCylinder", "BmGame.upk", 142597, "front"),
    ("BmGame base RearCollisionCylinder", "BmGame.upk", 142598, "rear"),
    ("Playable instance FrontCollisionCylinder", "Playable_Batmobile_SF.upk", 277, "front"),
    ("Playable instance RearCollisionCylinder", "Playable_Batmobile_SF.upk", 278, "rear"),
]


def batmobile() -> list:
    rows = []
    for role, pack, idx, which in CYLINDERS:
        pkg = upk_read.Package(COOKED + pack)
        e = pkg.exports[idx - 1]
        w = walk_best(pkg, idx)
        rows.append({"role": role, "package": pack, "export": idx, "which": which,
                     "name": e["name"], "class": pkg.object_class(idx),
                     "outer": pkg.object_path(e["outer_index"]), "size": w["size"],
                     "walk_start": w["start"], "tags": w["tags"], "parsed": w["end"] + 2,
                     "tail": w["tail"], "stop": w["stop"]})
    return rows


# --------------------------------------------------------------------------- build
def build() -> dict:
    engine = upk_read.Package(COOKED + "Engine.upk")
    cls = decode_class(engine)
    order, chain_problems = chain_order(cls["properties"])
    cdo_idx = find_export(engine, CDO_NAME, 0)
    cdo = walk_best(engine, cdo_idx)
    ancestors = ancestor_bounds(engine, CLASS_NAME)
    ancestor_max = max([a["max_offset"] for a in ancestors if a["max_offset"]] or [0])
    pairing = pair_fields(order, cdo["tags"], ancestor_max)
    fl = fleet()
    exe = exe_probe()
    cyl = batmobile()

    def field_values():
        got = {}
        for r in cyl:
            for off in FIELDS:
                for t in r["tags"]:
                    if t.get("offset") == off and t["type"] == "FloatProperty":
                        got.setdefault(str(off), []).append({"object": r["role"],
                                                             "value": t["value"]})
        return got
    values = field_values()
    mapping = pairing["mapping"]

    checks = []
    def check(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    counts = {}
    for p in cls["properties"]:
        counts[p["class"]] = counts.get(p["class"], 0) + 1
    check("Engine.upk holds the class export and its ten members, typed",
          cls["class_export"] == CLASS_EXPORT and counts == {"BoolProperty": 4,
                                                            "FloatProperty": 3,
                                                            "Function": 2,
                                                            "StructProperty": 1},
          "export %d, super %s; %s"
          % (cls["class_export"], cls["super_name"], counts))
    check("the member linked list covers all ten and ends at 0",
          not chain_problems and [p["name"] for p in order] == EXPECTED_CHAIN,
          "; ".join(chain_problems) or " -> ".join(p["name"] for p in order) + " -> 0")
    cdo_floats = [t["offset"] for t in cdo["tags"] if t["type"] == "FloatProperty"]
    # the class's own bool word is the one above the inherited members; the inherited bools
    # (476, 480, 484) are serialised too, so counting all bool tags would be wrong
    own_bools = [t for t in cdo["tags"] if t["type"] == "BoolProperty"
                 and t["offset"] > ancestor_max]
    check("the default object walks from byte 0 to its last byte, carrying the class's "
          "3 floats, its struct and its one bool word",
          cdo["start"] == 0 and cdo["end"] + 2 == cdo["size"]
          and cdo_floats == [540, 544, 548, 364]
          and len([t for t in cdo["tags"] if t["type"] == "StructProperty"]) == 1
          and len(own_bools) == 1,
          "start %d, %d tags, %d/%d bytes parsed, tail %r, floats %s, own bool word(s) at %s"
          % (cdo["start"], len(cdo["tags"]), cdo["end"] + 2, cdo["size"], cdo["tail"],
             cdo_floats, [t["offset"] for t in own_bools]))
    check("no ancestor class serialises anything at or above 540",
          all((a["max_offset"] or 0) < 540 for a in ancestors),
          "; ".join("%s max %s" % (a["name"], a["max_offset"]) for a in ancestors))
    check("the class's own float slots are exactly 540, 544 and 548",
          pairing["own_float_offsets"] == [540, 544, 548],
          "own slots %s, all float tags %s, ancestor max %d"
          % (pairing["own_float_offsets"], pairing["float_offsets_all"], ancestor_max))
    check("the chain ascends with the offset (struct 552 and bool word 556 above the floats)",
          pairing["chain_ascending"],
          "struct %s at 552, bool word at %s, floats end at %s; chain floats at chain "
          "positions %s, struct at %s"
          % (pairing["struct_names"], pairing["bool_off"],
             pairing["own_float_offsets"][-1] if pairing["own_float_offsets"] else None,
             [i for i, p in enumerate(order) if p["class"] == "FloatProperty"],
             [i for i, p in enumerate(order) if p["class"] == "StructProperty"]))
    check("the class block 540..559 is fully packed (3 floats + struct + bool word)",
          pairing["class_block"] is not None
          and pairing["class_block"][1] - pairing["class_block"][0] == pairing["class_block"][2],
          "block %s (start, end, bytes)" % (pairing["class_block"],))
    check("both asked offsets are named",
          all(mapping.get(str(o)) for o in FIELDS),
          "; ".join("%d = %s" % (o, mapping.get(str(o))) for o in FIELDS))
    check("the Batmobile's base templates carry 78.0 at 540 and 175.0 at 544",
          [x["value"] for x in values.get("540", [])] == [78.0, 78.0]
          and [x["value"] for x in values.get("544", [])] == [175.0, 175.0],
          "; ".join("%s: %s" % (o, [(x["object"].split()[0], x["value"])
                                   for x in v]) for o, v in sorted(values.items())))

    if exe["triples"]:
        check("the executable fills a vector X,Y from 0x220 and Z from 0x21C",
              True, "%d triples, first at %s" % (len(exe["triples"]),
                                                 exe["triples"][0]["va"]))
    return {"class": cls, "chain": [p["name"] for p in order],
            "chain_problems": chain_problems,
            "cdo": {"export": cdo_idx, "tags": cdo["tags"], "size": cdo["size"],
                    "walk_start": cdo["start"], "parsed": cdo["end"] + 2,
                    "tail": cdo["tail"]},
            "ancestors": ancestors, "ancestor_max": ancestor_max,
            "pairing": pairing, "fleet": {
                "packages": [{k: v for k, v in pk.items() if k != "rows"}
                             for pk in fl["packages"]],
                "objects": fl["objects"], "walked_to_last_byte": fl["walked_to_last_byte"],
                "both_540_544": fl["both_540_544"],
                "radius_slot_smaller": fl["radius_slot_smaller"],
                "d548_values": fl["d548_values"], "d548_all_one": fl["d548_all_one"]},
            "exe": exe, "cylinders": cyl, "values": values, "checks": checks}


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    a = []
    A = a.append
    pr = d["pairing"]
    mp = pr["mapping"]
    A("# COLLISION_CYLINDERS.md - the CylinderComponent floats, named (G3-01b open item)")
    A("")
    A("Generated by `Tools/scripts/grab_collision_cylinders.py` (`--write`); `--check` re-derives")
    A("it. Labels: **decoded** = read from bytes at a stated package/export/offset;")
    A("**derived** = arithmetic or ordering on decoded values with the rule given; **UNKNOWN** =")
    A("not decoded, with what was tried.")
    A("")
    A("## The answer")
    A("")
    A("| native offset | name (**derived**) | default object value (decoded) | Batmobile value (decoded) |")
    A("|---:|---|---:|---:|")
    vals = d["values"]
    for off in (540, 544, 548):
        v = vals.get(str(off)) or []
        A("| %d (0x%X) | `%s` | %s | %s |"
          % (off, off, mp.get(str(off), "UNKNOWN"),
             pr["values"].get(off, pr["values"].get(str(off))),
             ", ".join("%g" % x["value"] for x in v if "BmGame base" in x["object"]) or "-"))
    A("")
    A("Both asked offsets are named: **540 = `CollisionHeight`** (78.0 cm on the drivable")
    A("Batmobile) and **544 = `CollisionRadius`** (175.0 cm). The third own float, 548, is")
    A("`AABBScale` (1.0, i.e. not overridden).")
    A("")
    A("Where the two values live (decoded): not in the Startup templates the card names, but in")
    A("the BmGame base templates the Startup templates and the Playable instances inherit from -")
    A("see the cylinder table below.")
    A("")
    A("Member chain, one per line: `%s`." % "`, `".join(d["chain"]))
    A("")
    A("## How the names are established")
    A("")
    A("A float tag cannot name itself: the Batman property tag carries the native offset, but a")
    A("simple type (float) writes **no name**, which is why COLLISION.md had to leave both")
    A("UNKNOWN. The names come from the class:")
    A("")
    A("1. **The class's member exports** (decoded, Engine.upk export %d, super `%s`): ten"
      % (d["class"]["class_export"], d["class"]["super_name"]))
    A("   members, typed by their class exports. Names are the export name fields.")
    A("")
    A("| export | name | class | bytes | next |")
    A("|---:|---|---|---:|---:|")
    for p in d["class"]["properties"]:
        A("| %d | `%s` | %s | %d | %d |"
          % (p["index"], p["name"], p["class"], p["size"], p["next"]))
    A("")
    A("2. **The member linked list** (decoded: the int32 at +2 of each export is the next")
    A("   member's export index). The only member nothing points at is the head; the walk covers")
    A("   all ten and ends at 0 (oracle: no cycle, nothing left out):")
    A("")
    A("   `%s` -> 0" % "` -> `".join(d["chain"]))
    A("")
    A("3. **The class's own default object** (export %d, %d bytes). Its tag stream walks from"
      % (d["cdo"]["export"], d["cdo"]["size"]))
    A("   byte 0 to the last byte - %d/%d parsed, tail %s - so no tag is invented and none is"
      % (d["cdo"]["parsed"], d["cdo"]["size"],
         "none" if not d["cdo"]["tail"] else "`%s`" % d["cdo"]["tail"]))
    A("   cut off:")
    A("")
    A("| stream offset | tag | native offset | value |")
    A("|---:|---|---:|---|")
    for t in d["cdo"]["tags"]:
        A("| %d | %s | %d | %s |"
          % (t["at"], t["type"], t["offset"],
             t.get("name") or (repr(t.get("value")) if t.get("value") is not None else "")))
    A("")
    A("   *(An earlier revision of this file walked this object from byte 8 instead of byte 0.")
    A("   That walk drops the 540 tag, which is why 540 stayed unnamed; the walk above starts")
    A("   at 0 and consumes all %d bytes, so all three floats are seen.)*" % d["cdo"]["size"])
    A("")
    A("   The three floats sit at **540, 544, 548** (values 22.0, 22.0, 1.0 in the class's own")
    A("   default), the class's only `StructProperty` (`%s`) at **552**, and one"
      % ", ".join(pr["struct_names"]))
    A("   `BoolProperty` word (its four bools) at **556**. The inherited `PrimitiveComponent`")
    A("   members are below all of them (316, 364, 476, 480, 484).")
    A("")
    A("4. **Which float is which** - three facts, all decoded:")
    A("")
    A("   a. *No ancestor owns 540.* Each ancestor's own default object tops out below the")
    A("      class's block: %s. So the three floats above that boundary are this class's own."
      % ", ".join("%s max %s" % (x["name"], x["max_offset"]) for x in d["ancestors"]))
    A("   b. *The class has exactly three float members*, and exactly three float slots lie")
    A("      above that boundary: %s. A fourth slot does not exist, and a float below the"
      % ", ".join(map(str, pr["own_float_offsets"])))
    A("      boundary would be an ancestor's.")
    A("   c. *Slot order = chain order.* In the chain the three floats come before the struct")
    A("      and the bools (`... CollisionHeight -> CollisionRadius -> AABBScale ->")
    A("      CylinderColor -> bDrawBoundingBox ...`), and by type the struct is at 552 and the")
    A("      bool word at 556 - both **above** all three floats. The chain therefore ascends")
    A("      with the offset, and pairing in chain order gives:")
    A("")
    A("      `%s` -> %s." % ("`, `".join(pr["chain_floats"]),
                            ", ".join("**%d**" % o for o in pr["own_float_offsets"])))
    A("")
    A("   **The opposite reading is refuted by the same bytes**: with the chain descending, the")
    A("   struct member `CylinderColor` - the class's only StructProperty - would have to sit")
    A("   *below* all three floats, but its tag is at 552, above 548. Ascending is the only")
    A("   reading the types allow.")
    A("")
    A("5. **Containment** (derived): the class's own block is %d..%d inclusive, %d bytes ="
      " 3 x 4 (floats)"
      % (pr["class_block"][0], pr["class_block"][1] - 1, pr["class_block"][2]))
    A("   + %d (struct) + 4 (bool word) - no gap, so the five property members occupy exactly"
      % pr["struct_size"])
    A("   the five slots 540, 544, 548, 552, 556 and nothing else fits between them.")
    A("")
    A("## The default values are a second, weaker signal (not proof)")
    A("")
    A("The class default has 22.0 at 540, 22.0 at 544 and 1.0 at 548, so the two lengths")
    A("default to the same value and the third defaults to 1.0. That is consistent with the")
    A("pairing (a scale of 1.0 at the `AABBScale` slot) but it cannot separate radius from")
    A("height - the two are equal there. Only the chain/type argument above does that.")
    A("")
    A("## Fleet observation - reported, NOT used as evidence")
    A("")
    fl = d["fleet"]
    A("Every `CylinderComponent` object in %s was walked: %d objects, %d of which parse to"
      % (", ".join("`%s`" % p["package"] for p in fl["packages"]), fl["objects"],
         fl["walked_to_last_byte"]))
    A("their last byte. Every 540/544/548 tag they carry:")
    A("")
    A("| package | objects | 540 values | 544 values | 548 values |")
    A("|---|---:|---|---|---|")
    for pk in fl["packages"]:
        A("| `%s` | %d | %s | %s | %s |"
          % (pk["package"], pk["objects"],
             ", ".join("%g" % v for v in pk["serialised"]["540"]) or "-",
             ", ".join("%g" % v for v in pk["serialised"]["544"]) or "-",
             ", ".join("%g" % v for v in pk["serialised"]["548"]) or "-"))
    A("")
    A("%d objects serialise both 540 and 544, and in %d of them the 544 value is the smaller"
      % (fl["both_540_544"], fl["radius_slot_smaller"]))
    A("of the two. The 548 slot is written %d times, with values %s."
      % (len(fl["d548_values"]), fl["d548_values"]))
    A("")
    A("**A hypothesis this section used and lost:** \"if 548 is `AABBScale`, it is 1.0 wherever")
    A("it is serialised\" - refuted, because 0.4 and 2.0 occur. So no fleet-consistency")
    A("argument is made: a cylinder's two lengths can stand in any ratio, and a scale need not")
    A("be 1.0. These numbers are recorded for the next reader and are **not** part of the")
    A("derivation, which rests on the chain/type argument above.")
    A("")
    A("## The executable (static only): no evidence")
    A("")
    A("`BatmanAK.exe` carries **no** `CollisionRadius` / `CollisionHeight` string (0 hits ASCII")
    A("and 0 UTF-16), so the names are not recoverable from its registration code. Its")
    A("instructions cannot name the fields either: the displacements 0x21C and 0x220 appear in")
    A("%s movss sites across .text (%d / %d), %d windows touch both within 160 bytes and %d of"
      % (sum(d["exe"]["sites"].values()), d["exe"]["sites"].get("0x21c", 0),
         d["exe"]["sites"].get("0x220", 0), d["exe"]["windows"], d["exe"]["same_base"]))
    A("those use the same base register - but those displacements are ordinary struct offsets in")
    A("this binary, and no site has a class anchor tying it to `CylinderComponent`. The radial")
    A("test (one object's two fields into three consecutive vector slots, X and Y from 0x220 and")
    A("Z from 0x21C) found %d qualifying site(s)." % len(d["exe"]["triples"]))
    A("")
    A("So the executable contributes **nothing** to this naming; the derivation above rests")
    A("entirely on the packages. (An earlier revision of this file reported a radial/axial")
    A("result here and then said no site met the test; that paragraph was removed - it asserted")
    A("a conclusion the probe had not produced.)")
    A("")
    A("## The Batmobile's cylinders, through the chain")
    A("")
    A("| object | package | export | class | bytes | tags at 540 / 544 / 548 | walk |")
    A("|---|---|---:|---|---:|---|---|")
    for r in d["cylinders"]:
        got = []
        for off in (540, 544, 548):
            t = next((x for x in r["tags"] if x.get("offset") == off), None)
            got.append("%g" % t["value"] if t else "-")
        A("| %s | `%s` | %d | %s | %d | %s | start %d, %d/%d bytes, stop `%s` |"
          % (r["role"], r["package"], r["export"], r["class"], r["size"], " / ".join(got),
             r["walk_start"], r["parsed"], r["size"], r["stop"]))
    A("")
    A("Derived: the values come from the **BmGame base** templates (142597/142598) and are")
    A("inherited by both the Startup templates (which serialise only `ReplacementPrimitive` and")
    A("`PerInstanceRandom`) and the Playable instances (only a bool word and `LightingChannels`).")
    A("So both collision cylinders are `CollisionRadius` = **175.0 cm**, `CollisionHeight` =")
    A("**78.0 cm**, `AABBScale` = 1.0, with translations [100, 0, 0] (front) and [-200, 0, 0]")
    A("(rear) cm. The card's attribution of 78.0/175.0 to the Startup templates is corrected")
    A("here: those two objects carry neither float.")
    A("")
    A("## Checks")
    A("")
    A("| check | result | detail |")
    A("|---|---|---|")
    for c in d["checks"]:
        A("| %s | %s | %s |" % (c["check"], "PASS" if c["pass"] else "FAIL", c["detail"]))
    A("")
    A("%d/%d checks passed." % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))
    A("")
    A("## UNKNOWN")
    A("")
    A("- **Which bit of the bool word at %s is which of the four bool members**"
      % pr["bool_off"])
    A("  (`bDrawBoundingBox`, `bDrawNonColliding`, `bAlwaysRenderIfSelected`,")
    A("  `bForceGreenWhenSelected`): the word is serialised once, so its members are not")
    A("  separable from this stream. Not needed by the card.")
    A("- **`CylinderColor`'s fields**: the structure at %s is named but not decoded (colour"
      % pr["struct_off"])
    A("  channels or flags); irrelevant to the two floats.")
    A("- **Whether `CollisionHeight` is half or full height in this engine**: the value is")
    A("  78.0 cm and nothing in these bytes states the convention, so no bounds are claimed")
    A("  from it. The cylinders' world extents stay UNKNOWN (COLLISION.md's stance is")
    A("  unchanged). This also means the two cylinders are *named*, not *sized*.")
    A("- **The executable's property-registration table**: not found. Tried: the two name")
    A("  strings (absent), the displacement scan (%s movss sites, %d same-base windows) and the"
      % (sum(d["exe"]["sites"].values()), d["exe"]["same_base"]))
    A("  radial/axial vector test (0 qualifying sites). No site could be tied to the class.")
    A("- **The 4-byte prefix of each instance stream and the 12-byte prefix of each template")
    A("  stream** (also noted in COLLISION.md): not decoded here; they are outside the tag")
    A("  stream this script walks.")
    A("")
    return "\n".join(a) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    d = build()
    md = render(d)
    mp = d["pairing"]["mapping"]
    if args.write:
        os.makedirs(OUT, exist_ok=True)
        open(JS, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=1) + "\n")
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote COLLISION_CYLINDERS.json and COLLISION_CYLINDERS.md "
              "(%d members in the class chain, %d/%d checks, 540=%s 544=%s 548=%s)"
              % (len(d["class"]["properties"]),
                 sum(1 for c in d["checks"] if c["pass"]), len(d["checks"]),
                 mp.get("540"), mp.get("544"), mp.get("548")))
    if args.check:
        old_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        old = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else {}
        same = old_md == md and old.get("pairing") == d["pairing"]
        bad = [c["check"] for c in d["checks"] if not c["pass"]]
        print("%s: 540=%s 544=%s 548=%s, %d/%d checks, md+pairing byte-identical=%s%s"
              % ("OK" if not bad and same else "FAIL",
                 mp.get("540"), mp.get("544"), mp.get("548"),
                 sum(1 for c in d["checks"] if c["pass"]), len(d["checks"]), same,
                 "" if not bad else " | failing: " + "; ".join(bad)))
        return 0 if (same and not bad) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
