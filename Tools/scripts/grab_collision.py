"""grab_collision.py - collision primitives of the DRIVABLE Batmobile (G3-01).

Reads, from the shipped cooked packages only, every collision-relevant object of
`Batmobile_archetypes.Vehicle.Batmobile` and its class-default templates, and writes:

    Research/BatmobileGrab/COLLISION.json   (machine readable)
    Research/BatmobileGrab/COLLISION.md     (human readable)

Sources (all decoded, nothing from engine defaults):
    Playable_Batmobile_SF.upk  instances: CollisionCylinder 276, FrontCollisionCylinder 277,
                               RearCollisionCylinder 278, RB_StayUprightSetup 5106,
                               SVehicleMesh 5289, BatmanCollisionMesh*0 5392/5393, archetype 5281
    Startup.upk                class default Default__RVehicleBatmobile (export 7530) and the
                               component templates under BmScript.Default__RVehicleBatmobile
    BmGame.upk                 Default__RVehicleBatmobileBase (10923) and its subobject templates
                               (142597, 142598, 175716, 176111, 176112, 172112, 170826)
    BmGame.upk                 StaticMesh 175974 (name candidate) and its RB_BodySetup 169749
    Research/BatmobileGrab/BMSDK_OFFSETS.json   class layouts (field name per absolute offset)
    Research/BatmobileGrab/BONES.json           JC3 transform offset (transform.offset_used)

Labels used on every value:
    decoded   read from bytes (export, offset, tag type, payload)
    derived   computed from decoded values with the rule stated next to it
    UNKNOWN   not decoded; `unknown_reason` says what was tried

Field names come only from BMSDK_OFFSETS.json at the same absolute offset.  A tag whose
offset has no BMSDK entry keeps the name UNKNOWN.

Usage:
    python Tools/scripts/grab_collision.py --write   # writes COLLISION.json and COLLISION.md
    python Tools/scripts/grab_collision.py --check   # re-derives and compares; exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402
import bat_assemble as BA  # noqa: E402  (the JC3 transform used by grab_sockets.py)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
RES = os.path.normpath(os.path.join(HERE, "..", "..", "Research", "BatmobileGrab"))
PLAYABLE = os.path.join(GAME, "Playable_Batmobile_SF.upk")
BMGAME = os.path.join(GAME, "BmGame.upk")
STARTUP = os.path.join(GAME, "Startup.upk")
BMSDK = os.path.join(RES, "BMSDK_OFFSETS.json")
BONES = os.path.join(RES, "BONES.json")
SOCKETS = os.path.join(RES, "SOCKETS_JC3.json")
OUT_JSON = os.path.join(RES, "COLLISION.json")
OUT_MD = os.path.join(RES, "COLLISION.md")

# --- the objects, by export index (1-based) in the package named in the comment -------------
INSTANCES = {  # Playable_Batmobile_SF.upk
    "CollisionCylinder": 276,
    "FrontCollisionCylinder": 277,
    "RearCollisionCylinder": 278,
    "RB_StayUprightSetup": 5106,
    "SVehicleMesh": 5289,
    "BatmanCollisionMeshBattleMode0": 5392,
    "BatmanCollisionMeshPursuitMode0": 5393,
}
ARCHETYPE = 5281  # Playable_Batmobile_SF.upk  Batmobile (RVehicleBatmobile)
STARTUP_CDO = 7530  # Startup.upk  Default__RVehicleBatmobile (outer BmScript)
STARTUP_TPL = {  # Startup.upk  BmScript.Default__RVehicleBatmobile.<name>
    "FrontCollisionCylinder": 82147,
    "RearCollisionCylinder": 82148,
    "SVehicleMesh": 169640,
    "BatmanCollisionMeshBattleMode0": 171103,
    "BatmanCollisionMeshPursuitMode0": 171104,
    "RB_StayUprightSetup": 154788,
}
BASE_CDO = 10923  # BmGame.upk  Default__RVehicleBatmobileBase
BMGAME_TPL = {  # BmGame.upk  Default__RVehicleBatmobileBase.<name>
    "FrontCollisionCylinder": 142597,
    "RearCollisionCylinder": 142598,
    "SVehicleMesh": 175716,
    "BatmanCollisionMeshBattleMode0": 176111,
    "BatmanCollisionMeshPursuitMode0": 176112,
    "RB_StayUprightSetup": 172112,
}
STATICMESH_CANDIDATE = 175974  # BmGame.upk  StaticMesh Batmobile_V2_Collision_Pursuite
COMPONENT_CLASS_LAYOUT = "PrimitiveComponent"  # BMSDK class used for offsets < 540

# Batman tags stored as an unnamed primitive; the layout name is applied only when the offset
# is in the BMSDK class layout AND the same offset carries a named tag that agrees (cross-check).
CROSSCHECK = {316: "ReplacementPrimitive"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ byte-exact walker
def walk(pkg, data, start):
    """Same grammar as upk_read.walk_tags, recording every tag's exact byte range."""
    rows = []
    p = start
    while p + 2 <= len(data):
        t = struct.unpack_from("<h", data, p)[0]
        if t == 0:
            rows.append({"kind": "END", "at": p, "end": p + 2})
            return rows, p + 2, "end"
        if p + 4 > len(data):
            return rows, p, "overrun"
        off = struct.unpack_from("<H", data, p + 2)[0]
        if False:
            rows.append({"kind": "END", "at": p, "end": p + 2})
            return rows, p + 2, "end"
        if t in U.SIMPLE:
            if t == 13:
                try:
                    text, nxt = U._fstr(data, p + 4)
                except U.UpkError:
                    return rows, p, "bad_string"
                rows.append({"type_id": t, "offset": off, "at": p, "end": nxt, "value": text})
                p = nxt
                continue
            n = U.SIMPLE[t]
            if p + 4 + n > len(data):
                return rows, p, "overrun"
            payload = data[p + 4:p + 4 + n]
            row = {"type_id": t, "offset": off, "at": p, "end": p + 4 + n, "payload": payload}
            if t == 3:
                row["bits"] = struct.unpack("<I", payload)[0]
            rows.append(row)
            p += 4 + n
        elif t in U.NAMED:
            if p + 20 > len(data):
                return rows, p, "overrun"
            ni, nn, size, arr = struct.unpack_from("<iiii", data, p + 4)
            if not (0 <= ni < len(pkg.names)) or size < 0 or p + 20 + size > len(data):
                return rows, p, "bad_tag"
            rows.append({"type_id": t, "offset": off, "at": p, "end": p + 20 + size,
                         "name": pkg.names[ni], "size": size, "payload": data[p + 20:p + 20 + size]})
            p += 20 + size
        else:
            return rows, p, "unknown_type_%d" % t
    return rows, p, "eof"


def find_start(pkg, data):
    """Try every start 0..40; keep the walk that reaches END/eof with the most tags.

    Returns (start, rows, end, stop, prefix_bytes)."""
    best = None
    for st in range(0, 41):
        rows, end, why = walk(pkg, data, st)
        complete = why == "end" and end == len(data) or why == "end" and end >= len(data) - 2
        score = (complete, end >= len(data) - 2, len(rows), -st)
        if best is None or score > best[0]:
            best = (score, st, rows, end, why)
    _, st, rows, end, why = best
    return st, rows, end, why, data[:st]


def decode_prefix(pkg, prefix):
    """Prefix shapes seen: b'' (none), 1 zero byte, 4 zero bytes, or 4 zero bytes + an FName
    (index, number). The FName text is reported; its meaning is only stated where it matches."""
    out = {"hex": prefix.hex(), "bytes": len(prefix)}
    if len(prefix) >= 12:
        idx, num = struct.unpack_from("<ii", prefix, 4)
        out["fname"] = {"index": idx, "number": num,
                        "text": pkg.names[idx] if 0 <= idx < len(pkg.names) else None}
    return out


# ------------------------------------------------------------------ BMSDK layout
def load_layout():
    d = json.load(open(BMSDK, encoding="utf-8"))["classes"]
    return d


def class_chain(classes, name):
    chain = []
    while name:
        chain.append(name)
        name = classes.get(name, {}).get("super")
    return chain


def layout_at(classes, chain, offset):
    """(class, property) whose absolute offset matches, searched along the class chain."""
    hits = []
    for c in chain:
        for p in classes.get(c, {}).get("properties", []):
            if p["offset"] == offset:
                hits.append((c, p))
    return hits


def primitive_layout_at(classes, offset):
    hits = [p for p in classes[COMPONENT_CLASS_LAYOUT]["properties"] if p["offset"] == offset]
    return hits


BOOL_NOTE = "BoolProperty payload is the 32-bit word of the whole bitfield at that offset"


def decode_bits(classes, offset, bits):
    """Set bits -> named flags, from the BMSDK PrimitiveComponent layout at that offset."""
    named, unnamed_set = [], []
    entries = [p for p in classes[COMPONENT_CLASS_LAYOUT]["properties"]
               if p["offset"] == offset and p["kind"] == "BoolProperty"]
    covered = 0
    for p in entries:
        m = p.get("mask")
        if m is None:
            continue
        covered |= m
        if bits & m:
            named.append({"name": p["name"], "mask": m, "set": True})
    for i in range(32):
        b = 1 << i
        if bits & b and not (covered & b):
            unnamed_set.append(b)
    no_mask = [p["name"] for p in entries if p.get("mask") is None]
    return named, unnamed_set, no_mask


# ------------------------------------------------------------------ value decoding
def decode_value(pkg, row):
    t = row["type_id"]
    if t == 4:
        return {"type": "FloatProperty", "value": round(struct.unpack("<f", row["payload"])[0], 7)}
    if t == 2:
        return {"type": "IntProperty", "value": struct.unpack("<i", row["payload"])[0]}
    if t == 3:
        return {"type": "BoolProperty", "bits": row["bits"], "bits_hex": "0x%08x" % row["bits"]}
    if t == 1:
        return {"type": "ByteProperty", "value": row["payload"][0]}
    if t == 11:
        v = struct.unpack("<3f", row["payload"])
        return {"type": "VectorProperty", "value": [round(x, 4) for x in v]}
    if t == 12:
        v = struct.unpack("<3i", row["payload"])
        return {"type": "RotatorProperty", "value": list(v)}
    if t in (5, 16, 8) and row.get("payload") is not None and len(row["payload"]) >= 4:
        v = struct.unpack_from("<i", row["payload"])[0]
        return {"type": "ObjectReference", "index": v}
    if t == 16 and row.get("payload") is None:
        return {"type": "ObjectNCRProperty"}
    if t == 6:
        idx, num = struct.unpack("<ii", row["payload"])
        return {"type": "NameProperty", "text": pkg.names[idx] if 0 <= idx < len(pkg.names) else None}
    if "name" in row:
        return {"type": U.TYPE_NAMES.get(t, str(t)), "size": row["size"]}
    return {"type": U.TYPE_NAMES.get(t, str(t))}


def ref_info(pkg, index):
    if not index:
        return None
    return {"index": index, "path": pkg.object_path(index), "class": pkg.object_class(index)}


def tag_list(pkg, rows):
    """Decoded tag list. Each entry has an absolute byte range, value, layout name when known."""
    out = []
    for r in rows:
        if r.get("kind") == "END":
            out.append({"kind": "terminator", "bytes": [r["at"], r["end"]], "raw": "0000"})
            continue
        e = {"offset": r["offset"], "bytes": [r["at"], r["end"]]}
        if "name" in r:
            e["name"] = {"text": r["name"], "label": "decoded"}
        v = decode_value(pkg, r)
        e.update(v)
        if r["type_id"] in (5, 16, 8) and "index" in v:
            e["ref"] = ref_info(pkg, v["index"])
        out.append(e)
    return out


def name_offset(classes, chain, offset):
    """Return (name, label, reason)."""
    hits = layout_at(classes, chain, offset)
    if hits:
        c, p = hits[0]
        return p["name"], "decoded", "BMSDK_OFFSETS.json %s.%s at 0x%x" % (c, p["name"], offset)
    hits = primitive_layout_at(classes, offset)
    if hits:
        p = hits[0]
        if offset in CROSSCHECK:
            return p["name"], "derived", "BMSDK PrimitiveComponent layout (checked: tag name %r agrees at offset %d)" % (CROSSCHECK[offset], offset)
        return p["name"], "derived", "BMSDK PrimitiveComponent layout at offset %d; the CylinderComponent / StaticMeshComponent / SkeletalMeshComponent layouts are not in BMSDK_OFFSETS.json" % offset
    return None, "UNKNOWN", "no BMSDK layout entry at offset %d (class layout not in BMSDK_OFFSETS.json)" % offset


# ------------------------------------------------------------------ main derivation
def derive():
    classes = load_layout()
    chain_rvb = class_chain(classes, "RVehicleBatmobile")
    chain_base = class_chain(classes, "RVehicleBatmobileBase")
    inputs = {
        "playable": {"path": PLAYABLE, "sha256": sha256(PLAYABLE)},
        "bmgame": {"path": BMGAME, "sha256": sha256(BMGAME)},
        "startup": {"path": STARTUP, "sha256": sha256(STARTUP)},
        "bmsdk_offsets": {"path": BMSDK, "sha256": sha256(BMSDK)},
        "bones": {"path": BONES, "sha256": sha256(BONES)},
        "sockets_jc3": {"path": SOCKETS, "sha256": sha256(SOCKETS)},
    }
    pb = U.Package(PLAYABLE)
    bm = U.Package(BMGAME)
    su = U.Package(STARTUP)

    def walk_obj(pkg, idx):
        e = pkg.exports[idx - 1]
        data = pkg.data(idx)
        st, rows, end, why, prefix = find_start(pkg, data)
        return {
            "export": idx, "name": e["name"], "class": pkg.object_class(idx),
            "outer": pkg.object_path(e["outer_index"]), "size": len(data),
            "start": st, "stop": why, "parsed_end": end,
            "prefix": decode_prefix(pkg, prefix),
            "tail": {"bytes": [end, len(data)], "hex": data[end:].hex()},
            "tags": tag_list(pkg, rows), "_rows": rows, "_pkg": pkg,
            "_data": data,
        }

    objs = {}
    for name, idx in INSTANCES.items():
        objs[("instance", name)] = walk_obj(pb, idx)
    objs[("archetype", "Batmobile")] = walk_obj(pb, ARCHETYPE)
    objs[("startup_cdo", "Default__RVehicleBatmobile")] = walk_obj(su, STARTUP_CDO)
    for name, idx in STARTUP_TPL.items():
        objs[("startup_template", name)] = walk_obj(su, idx)
    objs[("base_cdo", "Default__RVehicleBatmobileBase")] = walk_obj(bm, BASE_CDO)
    for name, idx in BMGAME_TPL.items():
        objs[("base_template", name)] = walk_obj(bm, idx)

    def props(o):
        """tags by offset for the walked object (ints only)."""
        return {t["offset"]: t for t in o["tags"] if "offset" in t and t.get("kind") != "terminator"}

    # ---- resolve every named-by-layout tag and the bitfields for each instance / template
    def describe_tags(o, classes_chain_for_object):
        res = []
        for t in o["tags"]:
            if t.get("kind") == "terminator":
                res.append(t)
                continue
            nm, label, reason = name_offset(classes, classes_chain_for_object, t["offset"])
            e = dict(t)
            e["layout_name"] = {"text": nm, "label": label, "reason": reason}
            if t["type"] == "BoolProperty":
                named, unk, nomask = decode_bits(classes, t["offset"], t["bits"])
                e["bool_flags_set"] = named
                e["bool_bits_unmapped"] = ["0x%x" % b for b in unk]
                e["bool_names_without_mask"] = nomask
            res.append(e)
        return res

    prims = []
    for cname in ["CollisionCylinder", "FrontCollisionCylinder", "RearCollisionCylinder",
                  "BatmanCollisionMeshBattleMode0", "BatmanCollisionMeshPursuitMode0",
                  "SVehicleMesh", "RB_StayUprightSetup"]:
        inst = objs[("instance", cname)]
        chain_for = chain_base if False else class_chain(classes, "Pawn")
        # which template layer each primitive has: the Startup CDO component (no CollisionCylinder
        # template found in this chain) and the BmGame base template
        st_t = objs.get(("startup_template", cname))
        bm_t = objs.get(("base_template", cname))

        # the offset-based effective value per field: instance > startup template > base template
        def eff(offset):
            for layer, src in (("instance", inst), ("startup_template", st_t), ("base_template", bm_t)):
                if src is None:
                    continue
                for t in src["tags"]:
                    if t.get("offset") == offset and t.get("kind") != "terminator":
                        return layer, t
            return None, None

        offsets = sorted({t["offset"] for o in (inst, st_t, bm_t) if o for t in o["tags"] if "offset" in t})
        fields = []
        for off in offsets:
            layer, t = eff(off)
            nm, label, reason = name_offset(classes, class_chain(classes, "PrimitiveComponent"), off)
            if t is None:
                continue
            e = {"offset": off, "value_from": layer, "tag_type": t["type"]}
            if t["type"] == "BoolProperty":
                # one BoolProperty tag is the whole bitfield word at this offset: no single name
                e["layout_name"] = {"text": None, "label": "decoded",
                                    "reason": "BoolProperty bitfield at offset %d; flags listed in bool_flags_set" % off}
            else:
                e["layout_name"] = {"text": nm, "label": label, "reason": reason}
            for k in ("value", "bits", "bits_hex", "index", "ref", "text", "name"):
                if k in t:
                    e[k] = t[k]
            if t["type"] == "BoolProperty":
                named, unk, nomask = decode_bits(classes, off, t["bits"])
                e["bool_flags_set"] = named
                e["bool_bits_unmapped"] = ["0x%x" % b for b in unk]
            fields.append(e)
        prims.append({"name": cname, "instance_export": INSTANCES.get(cname),
                      "instance_bytes": {"size": inst["size"], "parsed_end": inst["parsed_end"],
                                         "stop": inst["stop"], "start": inst["start"],
                                         "prefix": inst["prefix"], "tail": inst["tail"]},
                      "startup_template_export": STARTUP_TPL.get(cname),
                      "base_template_export": BMGAME_TPL.get(cname),
                      "fields": fields})

    return {"inputs": inputs, "objects": objs, "prims": prims, "classes": classes,
            "chain_rvb": chain_rvb, "chain_base": chain_base, "pb": pb, "bm": bm, "su": su}


def to_json_safe(o):
    if isinstance(o, dict):
        return {k: to_json_safe(v) for k, v in o.items() if not k.startswith("_") and k not in ("pb", "bm", "su", "classes")}
    if isinstance(o, list):
        return [to_json_safe(x) for x in o]
    if isinstance(o, bytes):
        return o.hex()
    return o


def jc3_point(p_cm, offset):
    import numpy as np
    arr = np.asarray(p_cm, dtype=np.float64).reshape(1, 3)
    return [round(float(v), 6) for v in BA.to_jc3_rot(arr)[0] * 0.01 + offset]


def static_chain(pkg, idx):
    """StaticMesh export -> its BodySetup refs -> the BodySetup's tags and AggGeom payload."""
    e = pkg.exports[idx - 1]
    data = pkg.data(idx)
    st, rows, end, why, prefix = find_start(pkg, data)
    rec = {"export": idx, "name": e["name"], "class": pkg.object_class(idx),
           "outer": pkg.object_path(e["outer_index"]), "size": len(data),
           "start": st, "stop": why, "parsed_end": end, "tags": tag_list(pkg, rows),
           "body_setups": []}
    for r in rows:
        if r.get("kind") == "END" or "type_id" not in r:
            continue
        if r["type_id"] == 16 and r.get("payload") is None:
            continue
    for t in tag_list(pkg, rows):
        ref = t.get("ref")
        if ref and ref["class"] in ("RB_BodySetup", "BodySetup"):
            rec["body_setups"].append(body_chain(pkg, ref["index"]))
    return rec


def body_chain(pkg, idx):
    e = pkg.exports[idx - 1]
    data = pkg.data(idx)
    st, rows, end, why, prefix = find_start(pkg, data)
    body = {"export": idx, "name": e["name"], "class": pkg.object_class(idx),
            "outer": pkg.object_path(e["outer_index"]), "size": len(data),
            "start": st, "stop": why, "parsed_end": end, "tags": tag_list(pkg, rows),
            "unparsed_tail_bytes": len(data) - end}
    for r in rows:
        if r.get("name") == "AggGeom" and r.get("type_id") == 10:
            pl = r["payload"]
            sub = None
            best = None
            for s2 in range(0, 41):
                rr, en, wy = walk(pkg, pl, s2)
                sc = (wy == "end" and en >= len(pl) - 2, len(rr), -s2)
                if best is None or sc > best[0]:
                    best = (sc, s2, rr, en, wy)
            _, s2, rr, en, wy = best
            sub = {"start": s2, "stop": wy, "parsed_end": en, "tags": len(rr)}
            body["AggGeom"] = {
                "size": len(pl), "payload_first_32_hex": pl[:32].hex(),
                "nested_tag_walk": sub,
                "label": "UNKNOWN: AggGeom payload is not a tag stream (nested walk ends at %d of %d bytes); "
                         "its convex/box/sphere element layout is not decoded, so no geometry is claimed"
                         % (en, len(pl)),
            }
    return body


def build():
    d = derive()
    bones = json.load(open(BONES, encoding="utf-8"))
    offset_used = bones["transform"]["offset_used"]
    pb = d["pb"]
    bm = d["bm"]
    su = d["su"]

    primitives = []
    for prim in d["prims"]:
        entry = {"name": prim["name"], "instance_export": prim["instance_export"],
                 "instance_bytes": prim["instance_bytes"],
                 "startup_template_export": prim["startup_template_export"],
                 "base_template_export": prim["base_template_export"], "fields": []}
        for f in prim["fields"]:
            ff = dict(f)
            entry["fields"].append(ff)
        primitives.append(entry)

    # JC3 positions of the component Translation (offset 400, Vector3 cm) from the effective value
    for entry in primitives:
        tr = [f for f in entry["fields"] if f["offset"] == 400 and "value" in f]
        if tr:
            p = tr[0]["value"]
            entry["translation_cm"] = {"value": p, "label": "decoded", "from": tr[0]["value_from"],
                                       "source": "tag at offset 400 (Vector3)",
                                       "jc3_m_if_actor_frame_is_psk_frame": jc3_point(p, offset_used),
                                       "jc3_label": "derived: to_jc3_rot(p)*0.01 + BONES.offset_used, conditional on the actor frame equalling the PSK mesh frame (UNKNOWN link)"}
        for f in entry["fields"]:
            if f["offset"] == 644 and f.get("ref") and f["ref"]["class"] == "StaticMesh":
                entry["static_mesh_ref"] = {
                    "export": f["ref"]["index"], "path": f["ref"]["path"], "from": f["value_from"],
                    "field_offset": 644,
                    "field_name": "UNKNOWN (StaticMeshComponent layout not in BMSDK_OFFSETS.json)",
                    "label": "decoded: value and referent class; field name UNKNOWN"}
        cyl = [f for f in entry["fields"] if f["offset"] in (540, 544) and "value" in f]
        if cyl:
            entry["size_fields_540_544"] = [{"offset": f["offset"], "value": f["value"], "from": f["value_from"],
                                             "label": "decoded",
                                             "name": "UNKNOWN (CylinderComponent layout not in BMSDK_OFFSETS.json)"}
                                            for f in cyl]
    return d, primitives, bones, offset_used

UNKNOWN_LIST = [
    "CylinderComponent radius and height: the floats at offsets 540 and 544 (78.0 and 175.0 in the BmGame base template) are decoded, but BMSDK_OFFSETS.json has no CylinderComponent layout, so which is radius and which is height is UNKNOWN. No bounds are claimed.",
    "CollisionCylinder (Playable export 276): its template is not found in Startup or BmGame base chains; its translation/radius/height are UNKNOWN. Pawn.CylinderComponent (offset 900) is the slot it fills (decoded from the archetype).",
    "StaticMesh geometry for Batmobile_V2 (175973) and Batmobile_V2_Collision_Pursuite (175974): the BodySetup AggGeom payloads are native binary (first 13 zero bytes then non-tag data); the element layout is not decoded, so no vertices, boxes or bounds are claimed.",
    "PhysicsAsset Physics.Batmobile_V3_Physics (158266, reached from SVehicleMesh offset 824): bodies and constraints not decoded.",
    "Which component is active in each mode: the selector BatmanVsBatmobileCollisionMode (layout offset 5895) is not serialised in the archetype, the Startup CDO or the BmGame base walk, so the Battle/Pursuit choice is UNKNOWN.",
    "Field names for offsets 540/544 (cylinder), 644 (StaticMeshComponent reference) and 556/640/656/824/1148/1500 (SkeletalMeshComponent): no layout entry in BMSDK_OFFSETS.json; referent classes are decoded, names are not.",
    "Collision flag effective values: taken from the BmGame base template (offset 484 and 476 bitfields); the bitfield-to-name map is the BMSDK PrimitiveComponent mask table. The RBChannel (524) and RBCollideWithChannels (516) values are not serialised in any walked layer and are UNKNOWN.",
    "Actor frame to PSK mesh frame: the Translation values are actor-local; the link from actor frame to the Batmobile_V2 PSK frame is UNKNOWN. The JC3 positions use the SOCKETS_JC3 transform and are conditional on that frame link.",
    "Prefix bytes before the first tag: 4 zero bytes in instances, 12 bytes (4 zero bytes plus an FName that equals the object's own name) in templates. Their meaning is UNKNOWN.",
    "Tails after the terminator, all zero bytes: 21 for StaticMeshComponent templates (Startup 171103/171104, BmGame 176111/176112), 12 for SVehicleMesh templates (Startup 169640, BmGame 175716), 0 beyond the terminator for the cylinder templates (BmGame 142597/142598 end at 135 of 137 with 0000 as the terminator). Meaning UNKNOWN. SVehicleMesh instance (5289) carries an 84-byte tail, see svehicle_tail_check.",
    "The Playable CollisionCylinder/Front/Rear and the StayUpright objects: sizes and terminators are decoded; no further tags exist.",
    "Wreck PhysicsAsset Batmobile_V3_Destroyed_Physics (Playable 5017) was not used.",
]


def render_md(doc):
    """Human-readable COLLISION.md from the same document as COLLISION.json."""
    L = []
    A = L.append
    A("# COLLISION.md - drivable Batmobile collision primitives (G3-01)")
    A("")
    A("Generated by `Tools/scripts/grab_collision.py` (`--write`). Do not edit by hand; `--check` re-derives it.")
    A("")
    A("Labels: **decoded** = read from bytes (export, offset, tag type, payload); **derived** = computed from")
    A("decoded values, rule stated; **UNKNOWN** = not decoded, reason given. Nothing is taken from engine defaults.")
    A("")
    A("## Sources")
    A("")
    A("| role | package | export | class | outer | size |")
    A("|---|---|---|---|---|---|")
    for name, idx in INSTANCES.items():
        o = doc["objects"]["instance:" + name]
        A("| instance `%s` | Playable_Batmobile_SF.upk | %d | %s | %s | %d |" % (name, idx, o["class"], o["outer"], o["size"]))
    o = doc["objects"]["archetype:Batmobile"]
    A("| archetype `Batmobile` | Playable_Batmobile_SF.upk | %d | %s | %s | %d |" % (ARCHETYPE, o["class"], o["outer"], o["size"]))
    o = doc["objects"]["startup_cdo:Default__RVehicleBatmobile"]
    A("| class default `Default__RVehicleBatmobile` | Startup.upk | %d | %s | %s | %d |" % (STARTUP_CDO, o["class"], o["outer"], o["size"]))
    for name, idx in STARTUP_TPL.items():
        o = doc["objects"]["startup_template:" + name]
        A("| template `%s` | Startup.upk | %d | %s | %s | %d |" % (name, idx, o["class"], o["outer"], o["size"]))
    o = doc["objects"]["base_cdo:Default__RVehicleBatmobileBase"]
    A("| base class default `Default__RVehicleBatmobileBase` | BmGame.upk | %d | %s | %s | %d |" % (BASE_CDO, o["class"], o["outer"], o["size"]))
    for name, idx in BMGAME_TPL.items():
        o = doc["objects"]["base_template:" + name]
        A("| base template `%s` | BmGame.upk | %d | %s | %s | %d |" % (name, idx, o["class"], o["outer"], o["size"]))
    A("")
    A("Inheritance rule used (**derived**): a value is taken from the instance first, then the Startup template,")
    A("then the BmGame base template; a tag absent at a layer is inherited from the next. The class chain")
    A("RVehicleBatmobile -> RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle -> Pawn -> Actor")
    A("is decoded from BMSDK_OFFSETS.json `super` fields. The instance-to-template link is by component name")
    A("(the Playable imports name `Default__RVehicleBatmobile.<name>`); the walk does not decode the link itself.")
    A("")
    A("Byte accounting: every object is walked from the start offset that consumes the most of it (search 0..40).")
    A("The walk includes the `0000` list terminator. The bytes after it are the tail, reported below.")
    A("")
    for entry in doc["primitives"]:
        A("## %s" % entry["name"])
        A("")
        ib = entry["instance_bytes"]
        A("- instance export %s; walk start %d, stop `%s`, %d/%d bytes parsed (terminator included), tail %s."
          % (entry["instance_export"], ib["start"], ib["stop"], ib["parsed_end"], ib["size"],
             ("%d bytes `%s`" % ((ib["size"] - ib["parsed_end"]), ib["tail"]["hex"])) if ib["size"] > ib["parsed_end"] else "none"))
        A("- template exports: Startup %s, BmGame base %s" % (entry["startup_template_export"], entry["base_template_export"]))
        A("")
        A("| offset | value from | tag | field name (label) | value (decoded) |")
        A("|---|---|---|---|---|")
        for f in entry["fields"]:
            if f.get("bool_flags_set") is not None and f["tag_type"] == "BoolProperty":
                flags = ", ".join(x["name"] for x in f["bool_flags_set"]) or "(none of the named masks)"
                val = "%s bits; set: %s" % (f["bits_hex"], flags)
                if f.get("bool_bits_unmapped"):
                    val += "; unmapped bits: %s" % ", ".join(f["bool_bits_unmapped"])
                name = "bitfield (no single name)"
            elif "ref" in f and f["ref"]:
                val = "-> export %s %s (%s)" % (f["ref"]["index"], f["ref"]["path"], f["ref"]["class"])
                name = ("%s (%s)" % (f["layout_name"]["text"], f["layout_name"]["label"])) if f["layout_name"]["text"] else "UNKNOWN (no layout entry)"
            elif "index" in f:
                val = "null" if f["index"] == 0 else "index %s (no referent)" % f["index"]
                name = ("%s (%s)" % (f["layout_name"]["text"], f["layout_name"]["label"])) if f["layout_name"]["text"] else "UNKNOWN (no layout entry)"
            elif "value" in f:
                val = str(f["value"])
                name = "%s (%s)" % (f["layout_name"]["text"] or "UNKNOWN", f["layout_name"]["label"])
            else:
                val = "struct/array payload, not decoded (see tail rule)"
                name = ("%s (%s)" % (f["layout_name"]["text"], f["layout_name"]["label"])) if f["layout_name"]["text"] else "UNKNOWN (no layout entry)"
            A("| %d | %s | %s | %s | %s |" % (f["offset"], f["value_from"], f["tag_type"], name, val))
        A("")
        if "translation_cm" in entry:
            t = entry["translation_cm"]
            A("- Translation (offset 400, decoded from `%s`): %s cm." % (t["from"], t["value"]))
            A("- JC3 position (%s): %s m." % (t["jc3_label"], t["jc3_m_if_actor_frame_is_psk_frame"]))
        if "size_fields_540_544" in entry:
            for s in entry["size_fields_540_544"]:
                A("- float at offset %d (decoded, from `%s`): %s. Name: %s." % (s["offset"], s["from"], s["value"], s["name"]))
        if "static_mesh_ref" in entry:
            s = entry["static_mesh_ref"]
            A("- StaticMesh reference (%s): export %d `%s`. %s." % (s["from"], s["export"], s["path"], s["label"]))
            sc = doc["static_mesh_chains"][str(s["export"])]
            for b in sc["body_setups"]:
                A("  - BodySetup export %d `%s` (%s, %d bytes, walk parsed %d, unparsed %d). AggGeom %d bytes: %s"
                  % (b["export"], b["name"], b["class"], b["size"], b["parsed_end"], b["unparsed_tail_bytes"],
                     b["AggGeom"]["size"], b["AggGeom"]["label"]))
        A("")
    A("## SVehicleMesh references (SkeletalMeshComponent, instance and base template)")
    A("")
    for r in doc["svehicle_mesh_refs"]:
        A("- offset %d (%s): export %d `%s` (%s). %s." % (r["offset"], r["from"], r["ref"]["index"], r["ref"]["path"], r["ref"]["class"], r["label"]))
    A("")
    A("## Static mesh chains")
    A("")
    for k, v in sorted(doc["static_mesh_chains"].items()):
        A("- StaticMesh export %s `%s` (%s), outer `%s`, %d bytes, tags parsed to %d." % (k, v["name"], v["class"], v["outer"], v["size"], v["parsed_end"]))
    A("")
    A("## UNKNOWN / not reached")
    A("")
    for u in doc["unknown"]:
        A("- %s" % u)
    A("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d, primitives, bones, offset_used = build()
    statics = {}
    for entry in primitives:
        if "static_mesh_ref" in entry:
            idx = entry["static_mesh_ref"]["export"]
            statics[str(idx)] = static_chain(d["bm"], idx)
    svm = []
    for entry in primitives:
        if entry["name"] == "SVehicleMesh":
            for f in entry["fields"]:
                if "ref" in f and f["ref"]:
                    svm.append({"offset": f["offset"], "from": f["value_from"], "ref": f["ref"],
                                "field_name": "UNKNOWN (SkeletalMeshComponent layout not in BMSDK_OFFSETS.json)",
                                "label": "decoded value and referent class; field name UNKNOWN"})
    doc = {
        "schema": 1,
        "generator": "grab_collision.py",
        "card": "G3-01",
        "inputs": d["inputs"],
        "bones_transform_offset_used": offset_used,
        "primitives": primitives,
        "static_mesh_chains": statics,
        "svehicle_mesh_refs": svm,
        "objects": {
            "%s:%s" % k: {kk: vv for kk, vv in to_json_safe(v).items() if kk != "tags"} | {"tag_count": len(v["tags"])}
            for k, v in d["objects"].items()
        },
    }
    sv = d["objects"][("instance", "SVehicleMesh")]
    tail = bytes.fromhex(sv["tail"]["hex"])
    xray = [r for r in sv["_rows"] if r.get("name") == "XRayMaterials"][0]["payload"]
    tail_check = {"label": "decoded byte comparison",
                  "tail_hex": sv["tail"]["hex"],
                  "tail_bytes": len(tail),
                  "tail_starts_with_XRayMaterials_payload": tail[:len(xray)] == xray,
                  "XRayMaterials_payload_bytes": len(xray),
                  "remaining_bytes_after_copy_all_zero": all(b == 0 for b in tail[len(xray):])}
    doc["svehicle_tail_check"] = tail_check
    doc["unknown"] = UNKNOWN_LIST
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    md = render_md(doc)
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote", OUT_JSON)
        print("wrote", OUT_MD)
        return 0
    old = open(OUT_JSON, encoding="utf-8").read() if os.path.exists(OUT_JSON) else None
    old_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else None
    if old != text or old_md != md:
        print("DRIFT: COLLISION.json / COLLISION.md differ from re-derivation")
        return 1
    print("check ok:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
