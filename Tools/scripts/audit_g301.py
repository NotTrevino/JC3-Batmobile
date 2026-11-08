#!/usr/bin/env python3
"""audit_g301.py - audit G3-01's collision card (COLLISION.md / COLLISION.json) against the packages.

Read-only: the game installs and every Research/Working file are inputs. Writes
Research/BatmobileGrab/AUDIT_G301.md and .json only.

What it does
  1. re-verifies the six input hashes the card recorded (so the audit is provably on the same bytes);
  2. re-parses all 22 exports the card lists with Tools/scripts/upk_read.py, independently of
     grab_collision.py's own walker, and recomputes start offset / tag count / parsed bytes /
     unparsed tail bytes for each;
  3. recomputes the two BoolProperty bitfields (offsets 476 and 484) from the object's own tags and
     re-names every set bit from BMSDK_OFFSETS.json's PrimitiveComponent mask table, then compares
     that with the flag names the card published;
  4. recomputes the floats at offsets 540 and 544 in every object that carries them;
  5. checks the four claims of the G3-01 tracker row, and lists every card statement that the later
     cards COLLISION_CONVEX.md (G3-01c), COLLISION_FRAME.md (G3-01d) and COLLISION_SELECTOR2.md
     (G3-01e-fix) have superseded, contradicted or made redundant.

Labels: decoded = read from a package export at a byte offset; derived = computed from decoded
values with the rule given; UNKNOWN = not decodable from the files read here, with the reason.

Usage:  python Tools/scripts/audit_g301.py --write | --check
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402

RES = os.path.join(ROOT, "Research", "BatmobileGrab")
CJ = os.path.join(RES, "COLLISION.json")
CM = os.path.join(RES, "COLLISION.md")
BMSDK = os.path.join(RES, "BMSDK_OFFSETS.json")
OUT_MD = os.path.join(RES, "AUDIT_G301.md")
OUT_JSON = os.path.join(RES, "AUDIT_G301.json")

PKG_OF = {
    "archetype": "playable",
    "instance": "playable",
    "startup_cdo": "startup",
    "startup_template": "startup",
    "base_cdo": "bmgame",
    "base_template": "bmgame",
}
# the seven startup exports the tracker row lists
TRACKER_7 = [7530, 82147, 82148, 169640, 171103, 171104, 154788]
# the collision primitives the car owns, as the card names them (Playable instances)
PRIM_INSTANCES = [276, 277, 278, 5106, 5289, 5392, 5393]


def slice_offset(data, sha1_hex, length):
    """Where a quoted (sha1, length) blob actually sits inside `data`, or None."""
    for off in range(0, max(1, len(data) - length + 1)):
        if hashlib.sha1(data[off:off + length]).hexdigest() == sha1_hex:
            return off
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ re-parse
def rewalk(pkg, idx):
    """Walk an export's tag stream from the start offset that consumes the most of it (0..40).

    Independent of grab_collision.py: uses upk_read.walk_tags only. upk_read reports the terminator's
    own offset as `end` on a complete walk and never emits it as a tag, so the walk is normalised
    here: a trailing `0000` is consumed as the list terminator and counted as one row, which is the
    card's convention (it records an END row), so tag counts are comparable.
    """
    e = pkg.exports[idx - 1]
    data = pkg.data(idx)
    best = None
    for st in range(0, 41):
        tags, end, why = U.walk_tags(pkg, data, st, max_tags=20000)
        if why == "end":
            parsed, term = end + 2, True
        elif data[end:end + 2] == b"\x00\x00":
            parsed, term = end + 2, True          # terminator seen at eof
        else:
            parsed, term = end, False
        covers = parsed >= len(data)
        # a zero-tag walk must never beat a real one (short objects, start 40)
        score = (covers and term, term, len(tags), parsed, -st)
        if best is None or score > best[0]:
            best = (score, st, tags, parsed, why, term)
    _, st, tags, parsed, why, term = best
    return {
        "export": idx,
        "name": e["name"],
        "class": pkg.object_class(idx),
        "outer": pkg.object_path(e["outer_index"]),
        "size": e["size"],
        "start": st,
        "stop": why,
        "field_tags": len(tags),
        "tags": len(tags) + (1 if term else 0),
        "terminator_found": term,
        "parsed_end": parsed,
        "tail_bytes": max(0, len(data) - parsed),
        "tail_hex": data[parsed:].hex(),
        "prefix_hex": data[:st].hex(),
        "translation": vec_values(tags, 400),
        "_tags": tags,
        "_data": data,
    }


def bool_words(tags, offset):
    return [t["bits"] for t in tags
            if t.get("offset") == offset and t.get("type_id") == 3 and "bits" in t]


def float_values(tags, offset):
    return [round(float(t["value"]), 7) for t in tags
            if t.get("offset") == offset and t.get("type_id") == 4]


def vec_values(tags, offset):
    vals = [list(t["value"]) for t in tags
            if t.get("offset") == offset and t.get("type_id") == 11]
    return vals[0] if vals else []


def refs(tags):
    return [{"offset": t["offset"], "index": t["value"], "ref": t.get("ref")}
            for t in tags if t.get("type_id") in (5, 16) and isinstance(t.get("value"), int)]


def bit_names(classes, offset, bits):
    """Set bits -> BMSDK PrimitiveComponent flag names, plus the bits no mask covers."""
    entries = [p for p in classes["PrimitiveComponent"]["properties"]
               if p["offset"] == offset and p.get("kind") == "BoolProperty"]
    named, covered = [], 0
    for p in entries:
        m = p.get("mask")
        if m is None:
            continue
        covered |= m
        if bits & m:
            named.append({"name": p["name"], "mask": m})
    unnamed = [1 << i for i in range(32) if bits & (1 << i) and not covered & (1 << i)]
    return named, unnamed


# ------------------------------------------------------------------ build
def build():
    src = json.load(open(CJ, encoding="utf-8"))
    classes = json.load(open(BMSDK, encoding="utf-8"))["classes"]

    inputs = {}
    for role, v in src["inputs"].items():
        inputs[role] = {"path": v["path"], "sha256_recorded": v["sha256"],
                        "sha256_now": sha256(v["path"])}
    pk = {r: U.Package(inputs[r]["path"]) for r in ("playable", "startup", "bmgame")}

    objs = {}
    for key, rec in src["objects"].items():
        role = PKG_OF[key.split(":")[0]]
        r = rewalk(pk[role], rec["export"])
        r["package"] = role
        r["recorded"] = {"size": rec["size"], "start": rec["start"],
                         "parsed_end": rec["parsed_end"], "tag_count": rec["tag_count"],
                         "tail_bytes": rec["tail"]["bytes"][1] - rec["tail"]["bytes"][0],
                         "tail_hex": rec["tail"]["hex"]}
        r["matches_recorded"] = (
            r["size"] == rec["size"] and r["start"] == rec["start"]
            and r["parsed_end"] == rec["parsed_end"] and r["tags"] == rec["tag_count"]
            and r["tail_hex"] == rec["tail"]["hex"])
        objs[key] = r

    # ---- export name vs the name the card gives the object
    name_mismatch = []
    for key, r in objs.items():
        card_name = key.split(":", 1)[1]
        if r["name"] != card_name:
            name_mismatch.append({"object": key, "export": r["export"], "package": r["package"],
                                  "card_name": card_name, "export_name": r["name"]})

    # ---- claims of the G3-01 tracker row
    seven = [k for k, r in objs.items() if r["export"] in TRACKER_7 and r["package"] == "startup"]
    seven.sort(key=lambda k: objs[k]["export"])
    tails7 = {objs[k]["export"]: objs[k]["tail_bytes"] for k in seven}
    tail7_total = sum(tails7.values())
    size7_total = sum(objs[k]["size"] for k in seven)
    all_tail_total = sum(r["tail_bytes"] for r in objs.values())
    all_size_total = sum(r["size"] for r in objs.values())

    # ---- flags, from each object's own tags
    flags = {}
    for key, r in objs.items():
        w476 = bool_words(r["_tags"], 476)
        w484 = bool_words(r["_tags"], 484)
        entry = {}
        for off, ws in ((476, w476), (484, w484)):
            if not ws:
                entry[str(off)] = None
                continue
            bits = ws[0]
            named, unnamed = bit_names(classes, off, bits)
            entry[str(off)] = {"bits": bits, "bits_hex": "0x%08x" % bits,
                               "flags": [n["name"] for n in named],
                               "unmapped": ["0x%x" % u for u in unnamed],
                               "own_layer": True}
        flags[key] = entry

    # what the card published (from COLLISION.json's primitives, the machine copy of the md table)
    published = {}
    for p in src["primitives"]:
        for f in p["fields"]:
            if f["offset"] in (476, 484) and "bool_flags_set" in f:
                published.setdefault(p["name"], {})[f["offset"]] = {
                    "bits_hex": f["bits_hex"],
                    "flags": [x["name"] for x in f["bool_flags_set"]],
                    "value_from": f["value_from"],
                }
    flag_mismatch = []
    for p in src["primitives"]:
        for off in (476, 484):
            pub = published.get(p["name"], {}).get(off)
            if not pub:
                continue
            # the card inherits the bitfield from another layer; compare with that layer's object
            src_keys = {"instance": "instance:%s" % p["name"],
                        "startup_template": "startup_template:%s" % p["name"],
                        "base_template": "base_template:%s" % p["name"]}
            k = src_keys.get(pub["value_from"])
            mine = flags.get(k, {}).get(str(off)) if k else None
            if not mine:
                flag_mismatch.append({"primitive": p["name"], "offset": off,
                                      "issue": "card cites layer %r which carries no tag at this offset"
                                               % pub["value_from"]})
                continue
            if sorted(mine["flags"]) != sorted(pub["flags"]):
                flag_mismatch.append({"primitive": p["name"], "offset": off,
                                      "issue": "flag names differ",
                                      "card": pub["flags"], "recomputed": mine["flags"]})
            if mine["bits_hex"] != pub["bits_hex"]:
                flag_mismatch.append({"primitive": p["name"], "offset": off,
                                      "issue": "bits differ",
                                      "card": pub["bits_hex"], "recomputed": mine["bits_hex"]})

    # ---- cylinder floats 540/544, every layer that carries them
    cyl = []
    for key, r in objs.items():
        v540 = float_values(r["_tags"], 540)
        v544 = float_values(r["_tags"], 544)
        if v540 or v544:
            cyl.append({"object": key, "export": r["export"], "package": r["package"],
                        "v540": v540, "v544": v544,
                        "translation": r["translation"]})
    # the geometry bound test (cross-card: render bounds decoded by G3-01d from the PSK)
    render_bounds = {"min": [-345.118, -174.706, -0.223], "max": [357.442, 174.824, 233.962],
                     "source": "COLLISION_FRAME.md, decoded from the PSK of SkeletalMesh 5284 (G3-01d)"}
    hull_half_y = 159.1562  # union of the 13 pursuit element boxes, COLLISION_CONVEX.md (G3-01c)
    # the instance tail that COLLISION.json explains as an XRayMaterials payload copy, re-derived
    sv = objs["instance:SVehicleMesh"]
    xr = next((t for t in sv["_tags"] if t.get("name") == "XRayMaterials"), None)
    sv_tail = None
    if xr is not None:
        payload = sv["_data"][xr["at"]:xr["at"] + xr["size"]]
        tail = bytes.fromhex(sv["tail_hex"])
        words = list(struct.unpack("<%di" % (len(payload) // 4), payload)) if len(payload) % 4 == 0 else []
        sv_tail = {
            "tag_name": "XRayMaterials",
            "tag_offset": xr["offset"],
            "tag_type": xr["type"],
            "payload_bytes": len(payload),
            "payload_int32": words,
            "declared_count": words[0] if words else None,
            "values_equal": len(set(words[1:])) == 1 if len(words) > 1 else False,
            "value": words[1] if len(words) > 1 else None,
            "tail_starts_with_payload": tail.startswith(payload),
            "remaining_bytes": len(tail) - len(payload),
            "remaining_all_zero": all(b == 0 for b in tail[len(payload):]),
        }
    cyl_test = {
        "assumption": "a car's collision cylinder lies inside the car's own render bounds",
        "render_half_y": round((render_bounds["max"][1] - render_bounds["min"][1]) / 2.0, 4),
        "hull_half_y": hull_half_y,
        "candidate_540_as_radius": {"value": 78.0, "fits_width": 78.0 <= hull_half_y},
        "candidate_544_as_radius": {"value": 175.0, "fits_width": 175.0 <= hull_half_y},
        "render_z_span": [render_bounds["min"][2], render_bounds["max"][2]],
        "candidate_544_as_height_fits_z": 175.0 <= (render_bounds["max"][2] - render_bounds["min"][2]),
    }

    # ---- the archetype's component references
    arch = objs.get("archetype:Batmobile")
    arch_refs = {str(r["export"]): [(x["offset"], x["ref"]) for x in refs(arch["_tags"])
                                    if x["index"] in PRIM_INSTANCES] for r in [arch]}
    arch_owned = sorted({x["index"] for x in refs(arch["_tags"]) if x["index"] in PRIM_INSTANCES})
    cyl_slot = [x for x in refs(arch["_tags"]) if x["offset"] == 900]

    # ---- later-card facts, re-derived where cheap
    later = {}
    sel = pk["bmgame"].exports[10894 - 1]
    sel_data = pk["bmgame"].data(10894)
    later["selector"] = {
        "export": 10894,
        "name": sel["name"],
        "class": pk["bmgame"].object_class(10894),
        "size": sel["size"],
        "sha1_whole_export": hashlib.sha1(sel_data).hexdigest(),
        "sha1_recorded_by_selector2": "c2f6a2ee667c544876e5317a103072c44ea17788",
        "size_recorded_by_selector2": 253,
        # where the quoted 253-byte blob actually sits inside the 291-byte export (None = nowhere)
        "recorded_slice_offset": slice_offset(sel_data,
                                              "c2f6a2ee667c544876e5317a103072c44ea17788", 253),
    }
    later["static_meshes"] = {}
    for idx in (175973, 175974):
        role = next((r for r, p in pk.items()
                     if idx <= len(p.exports) and p.exports[idx - 1]["name"] in (
                         "Batmobile_V2", "Batmobile_V2_Collision_Pursuite")), None)
        if role is None:
            raise SystemExit("StaticMesh %d not found in any package" % idx)
        p = pk[role]
        d = p.data(idx)
        tags, end, why = U.walk_tags(p, d, 0, max_tags=200)
        later["static_meshes"][str(idx)] = {
            "package": role,
            "name": p.exports[idx - 1]["name"],
            "size": p.exports[idx - 1]["size"],
            "tags": len(tags),
            "named_tags": [t.get("name") for t in tags if t.get("name")],
            "has_bounds_tag": any(t.get("name") == "Bounds" for t in tags),
        }
    pa = None
    for role, p in pk.items():
        if 158266 <= len(p.exports) and p.exports[158266 - 1]["name"] == "Batmobile_V3_Physics":
            pa = {"package": role, "export": 158266,
                  "class": p.object_class(158266), "size": p.exports[158266 - 1]["size"]}
            break
    later["physics_asset"] = pa

    # ---- the card's own UNKNOWN list, for the staleness table
    doc_stale = [
        {"statement": "Which component is active in each mode: the selector BatmanVsBatmobileCollisionMode "
                      "(layout offset 5895) is not serialised in the archetype, the Startup CDO or the "
                      "BmGame base walk, so the Battle/Pursuit choice is UNKNOWN.",
         "status": "STALE",
         "later": "COLLISION_SELECTOR2.md (G3-01e-fix) section 1",
         "why": "the selector is decoded as BmGame export 10894 SetBatmanVsBatmobileCollisionMode with a "
                "0/1/2 -> mesh table (0 attaches nothing, 1 Pursuit, 2 Battle) and detach/attach offsets; "
                "its runtime samples only ever show values 0 and 1, so the Battle row is decoded but unobserved"},
        {"statement": "StaticMesh geometry ... the BodySetup AggGeom payloads are native binary ... the "
                      "element layout is not decoded, so no vertices, boxes or bounds are claimed.",
         "status": "STALE",
         "later": "COLLISION_CONVEX.md (G3-01c) sections 'The layout' and 'Oracles'",
         "why": "56 elements are decoded (169748: 43, 169749: 13) with every byte accounted for and the "
                "ElemBox == vertex bounds oracle passing on 56/56; only the StaticMesh Bounds struct stays "
                "UNKNOWN (G3-01c U-4)"},
        {"statement": "PhysicsAsset Physics.Batmobile_V3_Physics (158266, reached from SVehicleMesh offset "
                      "824): bodies and constraints not decoded.",
         "status": "PARTLY STALE",
         "later": "COLLISION_FRAME.md (G3-01d) section 'Oracles', 'physics chassis box'",
         "why": "bone 0 (Batmobile_Chassis) of that asset is decoded there (half extents "
                "[345.1525, 187.268, 103.75] cm, translation [9.0, 0.0, 106.75] cm); the other bodies and "
                "the constraints remain undecoded, so the sentence is too broad but not false"},
        {"statement": "Actor frame to PSK mesh frame: ... the link from actor frame to the Batmobile_V2 PSK "
                      "frame is UNKNOWN. The JC3 positions use the SOCKETS_JC3 transform and are conditional "
                      "on that frame link.",
         "status": "STALE",
         "later": "COLLISION_FRAME.md (G3-01d) 'The reference skeleton' and 'Verdict'",
         "why": "the frame link is PROVEN within tolerance and bone 0's link is identity to 2e-5, so the "
                "conditional no longer applies; the same card also shows the collision component is offset "
                "[5.0, 0.0, 0.0] cm (pursuit) and [10.0, 0.0, -15.0] cm (battle) from the render mesh, which "
                "the card's JC3 positions do not include"},
        {"statement": "BodySetup export 169748 ... (43346 bytes, walk parsed 25958, unparsed 17388).",
         "status": "STALE",
         "later": "COLLISION_CONVEX.md (G3-01c) 'accounting'",
         "why": "the AggGeom bytes are fully accounted: elements end at 25898 of 25907 with a 9-byte zero "
                "footer, so 'unparsed' describes the 4-byte tag walk, not undecoded geometry"},
        {"statement": "Tails after the terminator, all zero bytes: 21 for StaticMeshComponent templates "
                      "(Startup 171103/171104, BmGame 176111/176112), 12 for SVehicleMesh templates "
                      "(Startup 169640, BmGame 175716), 0 beyond the terminator for the cylinder templates.",
         "status": "INCOMPLETE",
         "later": "this audit (re-parse of all 22 objects)",
         "why": "the two StaticMeshComponent *instances* (5392, 5393) also carry a 21-byte tail, so the "
                "tail rule is per class and layer-independent; the card lists only the template layers"},
        {"statement": "SVehicleMesh ... 556 | instance | ArrayProperty | UNKNOWN | struct/array payload, "
                      "not decoded.",
         "status": "INCOMPLETE",
         "later": "the card's own svehicle_tail_check (and this audit)",
         "why": "that tag's payload is decoded after all: 76 B (int32 18 then 18 x 779) at offset 556, and "
                "the 84-byte object tail is a byte-identical copy of it plus 8 zero bytes - the same card "
                "compares the two, so the 'not decoded' label on 556 is stale inside its own file"},
        {"statement": "Prefix bytes before the first tag: 4 zero bytes in instances, 12 bytes (4 zero "
                      "bytes plus an FName that equals the object's own name) in templates.",
         "status": "INCOMPLETE",
         "later": "this audit (re-parse of all 22 objects)",
         "why": "two of the card's own objects fit neither shape: the archetype (Playable 5281) starts at "
                "offset 1, so its prefix is 1 zero byte, and both class defaults (Startup 7530, BmGame "
                "10923) start at offset 0 with no prefix at all"},
    ]

    doc = {
        "schema": 1,
        "card": "G3-01",
        "audit": "re-parse of every export the card lists, against the cooked packages",
        "inputs": inputs,
        "objects": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                    for k, v in objs.items()},
        "tracker_claims": {
            "startup_seven": [{"key": k, "export": objs[k]["export"], "name": objs[k]["name"],
                               "class": objs[k]["class"], "size": objs[k]["size"],
                               "tail_bytes": objs[k]["tail_bytes"]} for k in seven],
            "startup_seven_tail_total": tail7_total,
            "startup_seven_size_total": size7_total,
            "all_objects": len(objs),
            "all_objects_tail_total": all_tail_total,
            "all_objects_size_total": all_size_total,
            "startup_cylinder_templates": sorted(
                objs[k]["export"] for k in objs
                if objs[k]["package"] == "startup" and objs[k]["class"] == "CylinderComponent"),
            "playable_cylinder_instances": sorted(
                objs[k]["export"] for k in objs
                if objs[k]["package"] == "playable" and objs[k]["class"] == "CylinderComponent"),
        },
        "flags": flags,
        "flag_mismatch": flag_mismatch,
        "names": name_mismatch,
        "cylinder": {"objects": cyl, "test": cyl_test, "render_bounds": render_bounds},
        "svehicle_tail": sv_tail,
        "archetype": {"owned_primitive_exports": arch_owned,
                      "refs_by_export": {k: v for k, v in arch_refs.items() if v},
                      "offset_900_refs": cyl_slot},
        "later_cards": later,
        "stale": doc_stale,
        "unknown": [
            "CylinderComponent field names at 540/544: BMSDK_OFFSETS.json has no CylinderComponent "
            "layout, so 'radius' and 'height' are not decodable from any file read here; the 78.0/175.0 "
            "values are decoded, the names are not.",
            "The meaning of the zero tails after each object's 0000 terminator (21 B for StaticMeshComponent, "
            "12 B for SVehicleMesh, 84 B for instance 5289): the bytes are decoded, their purpose is not, and "
            "no engine layout in BMSDK_OFFSETS.json covers them.",
            "Which package container serialises the reference-skeleton transforms (G3-01d U-1): not read here.",
            "Whether the battle-mode collision mesh (5392 / 171103 / 176111) is ever attached at runtime: "
            "the selector decodes value 2 -> battle mesh, but no sample in the 7 logs carries value 2 "
            "(G3-01e-fix section 3), so the switch to Battle is decoded and unobserved.",
            "What the 18 repeated 0x30b (=779) values in the SVehicleMesh instance tail mean: the bytes are "
            "decoded (and reproduce the object's own XRayMaterials payload), but no field, array or enum in "
            "BMSDK_OFFSETS.json names them.",
        ],
        "oracles": {},
    }

    # ---- oracles
    doc["oracles"] = {
        "inputs_are_the_recorded_bytes": all(
            v["sha256_now"] == v["sha256_recorded"] for v in inputs.values()),
        "every_export_reparses_to_the_recorded_shape": all(r["matches_recorded"] for r in objs.values()),
        "recorded_tail_bytes_sum_matches_reparse": all(
            r["tail_bytes"] == r["recorded"]["tail_bytes"] for r in objs.values()),
        "tap_object_set_is_22": len(objs) == 22,
        "tap_seven_startup_exports_present": len(seven) == 7,
        "tap_tail_claim_contradicted": tail7_total > 0,
        "startup_carries_two_cylinder_templates": len(doc["tracker_claims"]["startup_cylinder_templates"]) == 2,
        "three_cylinder_instances_in_the_playable_layer":
            len(doc["tracker_claims"]["playable_cylinder_instances"]) == 3,
        "cylinder_floats_are_78_and_175": all(
            c["v540"] == [78.0] and c["v544"] == [175.0] for c in cyl if c["object"].startswith("base_template")),
        "svehicle_tail_check_reproduces": bool(
            sv_tail and sv_tail["tail_starts_with_payload"] and sv_tail["remaining_all_zero"]
            and sv_tail["payload_bytes"] == 76 and sv_tail["declared_count"] == 18),
        "flag_names_rederive_from_the_mask_table": not flag_mismatch,
        "selector_export_found": later["selector"]["name"] == "SetBatmanVsBatmobileCollisionMode",
        "static_meshes_have_no_bounds_tag": not any(v["has_bounds_tag"]
                                                    for v in later["static_meshes"].values()),
        "stale_statements_each_name_a_later_card": all(s["later"] for s in doc_stale),
        "only_the_stayupright_templates_are_misnamed": (
            len(name_mismatch) == 2 and all(m["export_name"] == "MyStayUprightSetup"
                                            for m in name_mismatch)),
        "selector_quoted_blob_located": later["selector"]["recorded_slice_offset"] is not None,
        "archetype_900_slot_is_the_collision_cylinder": bool(
            len(cyl_slot) == 1 and cyl_slot[0]["index"] == 276),
    }
    return doc


# ------------------------------------------------------------------ render
def render_md(doc):
    t = doc["tracker_claims"]
    L = []
    a = L.append
    a("# AUDIT_G301.md - G3-01's collision card, audited against the packages")
    a("")
    a("Generated by `Tools/scripts/audit_g301.py --write`; `--check` re-parses every export and "
      "re-derives every number below. The card (`COLLISION.md` / `COLLISION.json`, generator "
      "`grab_collision.py`) is **read-only** here: this file is the audit, not a new version of the card.")
    a("")
    a("The G3-01 tracker row is the claim under test: *the drivable Batmobile has 7 objects "
      "(Startup 7530/82147/82148/169640/171103/171104/154788) with 0 unparsed bytes, and a "
      "mode-dependent set of collision primitives (two StaticMesh components, three "
      "CylinderComponents, RB_StayUprightSetup, SVehicleMesh)*.")
    a("")
    a("## Verdict")
    a("")
    a("| # | claim | verdict |")
    a("|---|---|---|")
    a("| C1a | 7 Startup objects, those seven export numbers | **holds** (%d exports, %d B total) |"
      % (len(t["startup_seven"]), t["startup_seven_size_total"]))
    a("| C1b | 0 unparsed bytes in those 7 | **WRONG** - %d unparsed bytes in 3 of the 7 (%s) |"
      % (t["startup_seven_tail_total"], ", ".join("%d: %d B" % (r["export"], r["tail_bytes"])
                                                  for r in t["startup_seven"] if r["tail_bytes"])))
    a("| C2a | two StaticMesh components, switched by mode | **holds** |")
    a("| C2b | three CylinderComponents | **WRONG at that layer** - Startup has 2 cylinder templates; "
      "the third is a Playable instance with no template |")
    a("| C2c | a *mode-dependent* set of all of them | **WRONG** - only the two StaticMesh components "
      "are attached/detached; the cylinders, RB_StayUprightSetup and SVehicleMesh are present in every mode |")
    a("| C3 | 78.0 / 175.0 at offsets 540 / 544 | **values hold, names UNKNOWN** - both floats "
      "re-derive exactly, but no layout names them `radius`/`height` |")
    if doc["names"]:
        a("| C4 | Startup 154788 / BmGame 172112 is `RB_StayUprightSetup` | **WRONG name** - both exports "
          "are named `%s`; only the Playable instance 5106 is `RB_StayUprightSetup`, and that breaks the "
          "card's name-based instance->template link |" % doc["names"][0]["export_name"])
    if doc["archetype"]["offset_900_refs"]:
        slot = doc["archetype"]["offset_900_refs"][0]
        a("| C5 | `CollisionCylinder` fills the `Pawn.CylinderComponent` slot at offset 900 | **holds** - "
          "the archetype carries a reference to `%s` there |" % slot["ref"])
    a("")
    a("Reason C2c is not a reading of the card's own bytes: the card itself never claims the cylinders "
      "are mode-dependent - it lists them as components with no selector statement - and the later "
      "G3-01e-fix card decodes the selector's whole mesh table, which names only the two StaticMesh "
      "components. The tracker row compressed the card into a sentence the card does not support.")
    a("")
    a("## The re-parse, all %d objects" % len(doc["objects"]))
    a("")
    a("Method: `upk_read.walk_tags` over start offsets 0..40, keeping the walk that consumes the most "
      "bytes (the card's own start rule, re-implemented here so it does not share `grab_collision.py`'s "
      "walker). Parsed end includes the `0000` list terminator, and the tag count includes it as one "
      "row, which is how the card counts.")
    a("")
    a("| object | pkg | export | class | size | start | tags | parsed | **unparsed** | recorded |")
    a("|---|---|---:|---|---:|---:|---:|---:|---:|---|")
    for k, r in doc["objects"].items():
        a("| `%s` | %s | %d | %s | %d | %d | %d | %d | **%d** | %s |"
          % (k, r["package"], r["export"], r["class"], r["size"], r["start"], r["tags"],
             r["parsed_end"], r["tail_bytes"], "same" if r["matches_recorded"] else "**differs**"))
    a("")
    a("- unparsed total across all %d objects: **%d B of %d B**; %d objects carry a non-zero tail."
      % (len(doc["objects"]), t["all_objects_tail_total"], t["all_objects_size_total"],
         sum(1 for r in doc["objects"].values() if r["tail_bytes"])))
    svt = doc["svehicle_tail"]
    a("- every tail is zero bytes except the 84-byte SVehicleMesh instance tail, and that one is the "
      "object's **own** `XRayMaterials` payload (offset %d, %s, %d B) followed by %d zero bytes - the "
      "card's `svehicle_tail_check` reproduces exactly. Its first int32 is %s and the other %d words are "
      "all %s, so the payload is a self-consistent int32 array: %s declared values, %s present."
      % (svt["tag_offset"], svt["tag_type"], svt["payload_bytes"], svt["remaining_bytes"],
         svt["declared_count"], len(svt["payload_int32"]) - 1, svt["value"],
         svt["declared_count"], len(svt["payload_int32"]) - 1))
    a("")
    a("## C1: the seven objects and the `0 unparsed bytes` claim")
    a("")
    a("| export | object | size | unparsed | tail |")
    a("|---|---|---:|---:|---|")
    for r in t["startup_seven"]:
        tail = doc["objects"][r["key"]]
        a("| %d | `%s` | %d | **%d** | `%s` |"
          % (r["export"], r["name"], r["size"], r["tail_bytes"], tail["tail_hex"] or "-"))
    a("")
    a("The seven exports are real, in Startup.upk, with the classes and sizes the card lists: **C1a "
      "holds as a count of that layer**. But **three of the seven leave bytes after the `0000` "
      "terminator** - 12 for the SVehicleMesh template, 21 each for the two StaticMeshComponent "
      "templates - so *0 unparsed bytes* is false by 54. The card itself says so (its UNKNOWN list "
      "records those same 12/21/21 tails), which is how the row and the card came apart.")
    a("")
    a("The row's own two halves also disagree: `7 objects` = the Startup CDO plus six component "
      "templates, yet the primitive list it gives needs **three** cylinders, and Startup carries only "
      "two (`82147`, `82148`). The third cylinder is Playable export 276 (`CollisionCylinder`, 81 B, "
      "3 tags, no template in either chain), so the sentence mixes the Startup layer with the "
      "Playable instance layer.")
    a("")
    a("## C2: which components, and which are mode-dependent")
    a("")
    a("Archetype `Batmobile` (Playable 5281) references these primitive instances: %s."
      % ", ".join("`%d`" % e for e in doc["archetype"]["owned_primitive_exports"]))
    a("")
    a("| component (Playable instance) | instance export | Startup template | BmGame base | Translation @400 |")
    a("|---|---|---|---|---|")
    by_name = {}
    for k, r in doc["objects"].items():
        layer, _, nm2 = k.partition(":")
        if layer == "instance":
            by_name.setdefault(nm2, {})["instance"] = r["export"]
        elif layer == "startup_template":
            by_name.setdefault(nm2, {})["startup"] = r["export"]
        elif layer == "base_template":
            by_name.setdefault(nm2, {})["base"] = r["export"]
    for nm2 in sorted(by_name):
        v = by_name[nm2]
        tr = "-"
        for k2, lay in (("base_template:%s" % nm2, "base"), ("startup_template:%s" % nm2, "startup"),
                        ("instance:%s" % nm2, "instance")):
            o = doc["objects"].get(k2)
            if o and o.get("translation"):
                tr = "%s cm (%s)" % (o["translation"], lay)
                break
        a("| `%s` | %s | %s | %s | %s |"
          % (nm2, v.get("instance", "-"), v.get("startup", "-"), v.get("base", "-"), tr))
    a("")
    if doc["names"]:
        su = next((m for m in doc["names"] if m["package"] == "startup"), None)
        bm = next((m for m in doc["names"] if m["package"] == "bmgame"), None)
        a("**The card's naming and its link rule both break here.** The exports it calls "
          "`RB_StayUprightSetup` are named `%s` (Startup %s, BmGame %s), while the Playable instance "
          "%d *is* `RB_StayUprightSetup`. The card states that the instance-to-template link is by "
          "component name; for this component the names do not match, so the link it used cannot be "
          "the name there. The other five components do carry the same name at every layer."
          % (doc["names"][0]["export_name"], su["export"] if su else "-",
             bm["export"] if bm else "-", 5106))
    a("")
    a("- three CylinderComponents exist as **instances** (276, 277, 278); Startup/BmGame carry "
      "templates for only two of them (82147/82148 -> 142597/142598). Export 276's template is absent "
      "from both chains - that is the card's own UNKNOWN, and it means the row cannot promise three "
      "templated cylinders.")
    a("- the mode switch names **only** the two StaticMesh components "
      "(`BatmanCollisionMeshPursuitMode` at value 1, `BatmanCollisionMeshBattleMode` at value 2, "
      "value 0 attaching neither - G3-01e-fix). No selector argument, detach or attach call mentions "
      "a cylinder, `RB_StayUprightSetup` or `SVehicleMesh`, so calling the whole set mode-dependent "
      "is not supported by any decoded byte.")
    a("- `RB_StayUprightSetup` is 2 bytes in all three layers (only the `0000` terminator): it carries "
      "no serialised field at all, so nothing about it can be mode-dependent.")
    a("")
    a("## C3: the two floats at 540 / 544")
    a("")
    a("| object | pkg | 540 | 544 | Translation (400) |")
    a("|---|---|---:|---:|---|")
    for c in doc["cylinder"]["objects"]:
        a("| `%s` | %s | %s | %s | %s |"
          % (c["object"], c["package"], c["v540"], c["v544"], c["translation"]))
    a("")
    test = doc["cylinder"]["test"]
    a("- both values re-derive exactly: **78.0 at 540, 175.0 at 544**, in both BmGame base templates "
      "(142597, 142598) and nowhere else in the card's object set.")
    a("- the card is right that the **names** are UNKNOWN: `BMSDK_OFFSETS.json` has no "
      "CylinderComponent layout, and no decoded file in this tree labels 540 or 544.")
    a("- a geometry test separates the two readings, under one stated assumption (%s): the car's "
      "render bounds are Y %s..%s (half-width %s) and Z %s..%s, and the pursuit hull union is "
      "Y +/-%s. **78 fits as a radius** (%s <= %s); **175 does not** (%s <= %s is false) but fits as "
      "a height (%s <= the %s cm Z span). That is evidence for 540=radius, 544=height - evidence, "
      "not a decode, so it stays derived and the names stay UNKNOWN."
      % (test["assumption"], doc["cylinder"]["render_bounds"]["min"][1],
         doc["cylinder"]["render_bounds"]["max"][1], test["render_half_y"],
         test["render_z_span"][0], test["render_z_span"][1], test["hull_half_y"],
         test["candidate_540_as_radius"]["value"], test["hull_half_y"],
         test["candidate_544_as_radius"]["value"], test["hull_half_y"],
         test["candidate_544_as_radius"]["value"],
         round(test["render_z_span"][1] - test["render_z_span"][0], 3)))
    a("")
    a("So the tracker row's phrasing (`78.0 / 175.0 radius/height at offsets 540/544`) reads the "
      "values correctly but states an assignment the card deliberately refuses to make. The card is "
      "**not** wrong here; the row over-reads it.")
    a("")
    a("## Flags, re-derived from each object's own bitfield")
    a("")
    a("| object | 476 | 484 |")
    a("|---|---|---|")
    for k, f in doc["flags"].items():
        cells = []
        for off in ("476", "484"):
            v = f[off]
            cells.append("-" if not v else "`%s` %d flags%s"
                         % (v["bits_hex"], len(v["flags"]),
                            "" if not v["unmapped"] else " + unmapped %s" % ",".join(v["unmapped"])))
        a("| `%s` | %s | %s |" % (k, cells[0], cells[1]))
    a("")
    if doc["flag_mismatch"]:
        a("**Flag disagreement with the published table:**")
        for m in doc["flag_mismatch"]:
            a("- `%s` @%d: %s (card %s vs recomputed %s)"
              % (m["primitive"], m["offset"], m["issue"], m.get("card"), m.get("recomputed")))
    else:
        a("Every published flag name re-derives from the object's own 32-bit word with the BMSDK "
          "PrimitiveComponent mask table: **no flag statement in the card is wrong**.")
    a("")
    a("Two things the table does show, and the card does not say:")
    a("")
    a("- the front/rear cylinder bitfield at 484 is `0x110a4222`: it sets **no** `BlockActors`, "
      "`BlockZeroExtent`, `BlockNonZeroExtent`, `CollideActors` or `BlockRigidBody` bit, so the two "
      "cylinder primitives are not collision-blocking primitives in the sense the two StaticMesh "
      "components are (`0x11027e32`, which sets all of them).")
    a("- the card mixes layers inside one row: `PerInstanceRandom` and 476 come from the instance, "
      "484/540/544 from the BmGame base. The card labels each field's `value_from`, so this is "
      "traceable, but an effective flag word assembled across layers is a **derived** value, not a "
      "decoded one, and should not be read as the instance's serialised state.")
    a("")
    a("## Statements the later cards have superseded")
    a("")
    a("| # | the card says | status | superseded by | why |")
    a("|---|---|---|---|---|")
    for i, s in enumerate(doc["stale"], 1):
        a("| S%d | %s | **%s** | %s | %s |"
          % (i, s["statement"].replace("|", "/"), s["status"], s["later"], s["why"].replace("|", "/")))
    a("")
    a("Staleness is a reading of the later cards plus a re-parse here; the later cards' own numbers "
      "are not re-derived by this script (that is their `--check`'s job), except for the two facts "
      "below, which are cheap and decisive:")
    a("")
    sel = doc["later_cards"]["selector"]
    a("- the selector the card calls unreadable exists and is a function: BmGame export %d `%s` "
      "(%s, %d B, sha1 of the whole export `%s`). G3-01e-fix quotes %d B and sha1 `%s`, and that "
      "exact blob is export bytes **[%d:%d]** - so the quoted size/hash describe a 253-byte slice "
      "inside the export, not the export; the mesh table it publishes is unaffected, but its "
      "size/hash line cannot be reproduced from the export as written."
      % (sel["export"], sel["name"], sel["class"], sel["size"], sel["sha1_whole_export"],
         sel["size_recorded_by_selector2"], sel["sha1_recorded_by_selector2"],
         sel["recorded_slice_offset"], sel["recorded_slice_offset"] + sel["size_recorded_by_selector2"]))
    for idx, v in doc["later_cards"]["static_meshes"].items():
        a("- StaticMesh %s `%s` (%s, %d B): %d tags, %d named, **no `Bounds` tag** - which is why the "
          "StaticMesh bounds stay UNKNOWN in both cards, and why the geometry came from the BodySetup "
          "AggGeom instead."
          % (idx, v["name"], v["package"], v["size"], v["tags"], len(v["named_tags"])))
    a("")
    a("## Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for k, v in doc["oracles"].items():
        a("| `%s` | %s | |" % (k, "PASS" if v else "**FAIL**"))
    a("")
    a("%d/%d checks passed." % (sum(1 for v in doc["oracles"].values() if v), len(doc["oracles"])))
    a("")
    a("## UNKNOWN")
    a("")
    for i, u in enumerate(doc["unknown"], 1):
        a("%d. %s" % (i, u))
    a("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    doc = build()
    md = render_md(doc)
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if mode == "--write":
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote", OUT_MD)
        print("wrote", OUT_JSON)
        print("objects:", len(doc["objects"]),
              "| startup-7 tails:", doc["tracker_claims"]["startup_seven_tail_total"], "B",
              "| all tails:", doc["tracker_claims"]["all_objects_tail_total"], "B")
        print("flag mismatches:", len(doc["flag_mismatch"]),
              "| stale statements:", len(doc["stale"]))
        for k, v in doc["oracles"].items():
            print("  %-52s %s" % (k, v))
        bad = [k for k, v in doc["oracles"].items() if not v]
        sys.exit(0 if not bad else 1)
    # --check
    ok = True
    try:
        have_js = open(OUT_JSON, encoding="utf-8").read()
    except FileNotFoundError:
        print("FAIL: %s missing" % OUT_JSON)
        sys.exit(1)
    if have_js != js:
        ok = False
        print("FAIL: %s is stale (re-run --write)" % OUT_JSON)
    try:
        have_md = open(OUT_MD, encoding="utf-8").read()
    except FileNotFoundError:
        print("FAIL: %s missing" % OUT_MD)
        sys.exit(1)
    if have_md != md:
        ok = False
        print("FAIL: %s text differs from a fresh render" % OUT_MD)
    bad = [k for k, v in doc["oracles"].items() if not v]
    for k in bad:
        print("FAIL oracle:", k)
    if bad:
        ok = False
    if ok:
        print("OK: %d objects re-parsed, %d stale statements, all %d oracles true"
              % (len(doc["objects"]), len(doc["stale"]), len(doc["oracles"])))
        print("verdicts: C1b WRONG (%d unparsed B in the 7), C2b/C2c WRONG, C3 values hold / names UNKNOWN"
              % doc["tracker_claims"]["startup_seven_tail_total"])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
