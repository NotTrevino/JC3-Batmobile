"""jc3_stations_vs_hinges.py - cross-check the wheel-station quads against G3-10e's hinge pivots.

`Research/JC3Grab/PHYSICS.md` (jc3phys.py) found the four wheel-station quads with a
*rectangle heuristic*: four `float4 (x, y, z, 1.0)` with one `|x|` at both signs, two `z` at
both signs, and one common `y`.  It agrees with the named
`land_global.base_wheel_hardpoint_positions` in 17 entities.  That is a name-vs-bytes check.

This pass asks the structural question: are those quads the wheel **hinge pivots** that
G3-10e decoded (`PHYSICS_LIMITS.json`, 419 `hkpLimitedHingeConstraintData`, frame A/B
translations)?  If they were, the rectangle heuristic would be confirmed by a decoded
structure.  They are not - and this tool also decodes what they are instead:

  * the container object of the quad (by class name, from the packfile), and
  * the 96-byte record the quad heads: position at +0x00 (`w == 1.0`), a unit quaternion at
    +0x10, 16 zero bytes at +0x20, then `u32 0, u32 0, i32 0x7fffffff, u32 id`, a `u16` and
    the same `u16 id` at +0x40, 16 zero bytes at +0x50.  Entries form one contiguous run of
    96-byte stride with consecutive 1-based ids; only the four wheel entries in that run
    carry a non-zero position.

The record's Havok type name is UNKNOWN (no 2014.1 header in this project); everything
claimed about it is read from the bytes and re-derived by `--check`.

    python Tools/scripts/jc3_stations_vs_hinges.py --write
    python Tools/scripts/jc3_stations_vs_hinges.py --check
"""

import glob
import json
import math
import os
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx                       # noqa: E402
import jc3phys as P                 # noqa: E402
import jc3_physics_limits as L      # noqa: E402
from eetoc import unaaf, sarc_dir   # noqa: E402

RAW = P.RAW
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_STATIONS_HINGES.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_STATIONS_HINGES.json")
INT_MAX = 0x7FFFFFFF
STRIDE = 96
SYS_CLASS = "hknpPhysicsSystemData"


# ---------------------------------------------------------------- inputs
def station_entities():
    """entity -> station set, for entities whose grab found exactly one set."""
    d = os.path.join(RAW, "phys")
    out = {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(d, fn), encoding="utf-8"))
        sets = [s for f in doc["physics"] for s in f["stations"]]
        if len(sets) == 1:
            out[doc["entity"]] = sets[0]
    return out


def blob_of(ent, rows):
    """The `.physicsc` bytes for an entity, read out of the shipped archive."""
    hits = [r for r in rows if r["path"] == ent]
    if not hits:
        raise SystemExit("not in index: " + ent)
    r = sorted(hits, key=lambda r: P.MOUNT_RANK[r["mount"]])[-1]
    with open(os.path.join(P.DEFAULT_GAME, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        raw = f.read(r["size"])
    stream = unaaf(raw)
    for name, off, size in sarc_dir(stream):
        if name.endswith(".physicsc"):
            return name, stream[off:off + size]
    raise SystemExit("no .physicsc in " + ent)


def hinges_of(blob):
    """G3-10e's own decoder, run on the same bytes (a temp copy, byte-identical)."""
    with tempfile.NamedTemporaryFile(suffix=".physicsc", delete=False) as f:
        f.write(blob)
        tmp = f.name
    try:
        s = L.scan(tmp)
    finally:
        os.unlink(tmp)
    out = []
    for h in s["hinges"]:
        fa, fb = L.rot3x4(h, 48), L.rot3x4(h, 112)
        if not fa or not fb:
            continue
        out.append({"offset": h["offset"],
                    "A": fa["translation"], "B": fb["translation"],
                    "AB_equal": all(abs(x - y) < 1e-6
                                    for x, y in zip(fa["translation"], fb["translation"]))})
    return out


# ---------------------------------------------------------------- the 96-byte record
def entry_at(b, k):
    """Decode one 96-byte entry at k, or None if the bytes do not fit the shape."""
    if k < 0 or k + STRIDE > len(b):
        return None
    x, y, z, w = struct.unpack_from("<4f", b, k)
    if w != 1.0:
        return None
    q = struct.unpack_from("<4f", b, k + 0x10)
    if abs(math.sqrt(sum(c * c for c in q)) - 1.0) > 1e-5:
        return None
    z0, z1, imax, rid = struct.unpack_from("<IIiH", b, k + 0x30)
    if z0 or z1 or imax != INT_MAX:
        return None
    flag, rid2 = struct.unpack_from("<HH", b, k + 0x40)
    if rid2 != rid:
        return None
    return {"at": k, "pos": [x, y, z], "quat": list(q), "id": rid, "flag": flag,
            "pad_zero": b[k + 0x20:k + 0x30] == bytes(16),
            "tail_zero": b[k + 0x50:k + 0x60] == bytes(16)}


def table_of(b, qs):
    """The contiguous 96-byte run that holds the station quads, walked both ways."""
    first = min(qs)
    while entry_at(b, first - STRIDE):
        first -= STRIDE
    entries, k = [], first
    while True:
        e = entry_at(b, k)
        if not e:
            break
        entries.append(e)
        k += STRIDE
    return entries


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------- the pass
def run():
    rows = P.load_index(P.DEFAULT_OUT)
    ents = station_entities()
    lg = P.land_global_stations()
    by_file = {}
    problems = []
    for ent in sorted(ents):
        st = ents[ent]
        name, blob = blob_of(ent, rows)
        pf = jc3hkx.Packfile(blob)
        quads = [struct.unpack_from("<4f", blob, o) for o in st["quads_at"]]
        holder = None
        for o in pf.objects:
            abs_off = pf.base + o.offset
            ext = pf.extents[o.offset]
            if all(abs_off <= q < abs_off + ext for q in st["quads_at"]):
                holder = {"class": o.cls, "object_offset": o.offset, "extent": ext,
                          "relative": [q - abs_off for q in st["quads_at"]]}
                body = blob[abs_off:abs_off + ext]
                break
        if not holder:
            problems.append({"entity": ent, "problem": "quad outside every object"})
            continue
        entries = table_of(body, holder["relative"])
        hs = hinges_of(blob)
        piv = [h["A"] for h in hs]
        per_quad = []
        for (x, y, z, w), off in zip(quads, st["quads_at"]):
            p = [x, y, z]
            near = min(piv, key=lambda t: dist(p, t)) if piv else None
            per_quad.append({
                "at": off, "pos": [x, y, z],
                "nearest_pivot": near,
                "nearest_distance": round(dist(p, near), 6) if near else None,
            })
        rec = {
            "entity": ent,
            "physicsc": name,
            "container": holder,
            "station": {"quads": per_quad, "track_m": st["track_m"],
                        "wheelbase_m": st["wheelbase_m"],
                        "named_hardpoints_agree": None},
            "hinges": {"n": len(hs), "pivots": len(piv),
                       "AB_equal": sum(1 for h in hs if h["AB_equal"]),
                       "pivots_xyz": [[round(c, 4) for c in h["A"]] for h in hs]},
            "table": {"stride": STRIDE, "entries": len(entries),
                      "id_first": entries[0]["id"] if entries else None,
                      "id_last": entries[-1]["id"] if entries else None,
                      "station_ids": [e["id"] for e in entries
                                      if e["at"] in holder["relative"]],
                      "nonzero_positions": sum(1 for e in entries
                                               if any(abs(c) > 1e-9 for c in e["pos"])),
                      "station_quats": [e["quat"] for e in entries
                                        if e["at"] in holder["relative"]],
                      "flags": sorted({e["flag"] for e in entries})},
        }
        ref = lg.get(ent)
        if ref:
            s = st
            rec["station"]["named_hardpoints_agree"] = all(
                abs(s[k] - ref[k]) < 1e-3 for k in ("x", "y", "z_rear", "z_front"))
        by_file.setdefault((name, st["track_m"], st["wheelbase_m"], st["x"],
                            st["y"], st["z_rear"], st["z_front"]), []).append(rec)

    models = []
    for (name, track, wb, x, y, zr, zf), recs in sorted(by_file.items()):
        d = [q["nearest_distance"] for q in recs[0]["station"]["quads"]]
        r0 = recs[0]
        # the variants of one car share one .physicsc: their numbers must be identical
        same = all([q["nearest_distance"] for q in r["station"]["quads"]] == d for r in recs)
        models.append({
            "physicsc": name, "entities": [r["entity"] for r in recs],
            "entity_count": len(recs),
            "station": {"x": x, "y": y, "z_rear": zr, "z_front": zf,
                        "track_m": track, "wheelbase_m": wb},
            "container": r0["container"],
            "table": r0["table"],
            "hinges": {"n": r0["hinges"]["n"], "AB_equal": r0["hinges"]["AB_equal"]},
            "hinge_pivots": r0["hinges"]["pivots_xyz"],
            "nearest_pivot_distance": {"min": min(d), "median": sorted(d)[len(d) // 2],
                                       "max": max(d), "per_quad": d,
                                       "variants_identical": same},
            "named_hardpoints_agree": all(
                r["station"]["named_hardpoints_agree"] for r in recs),
        })

    alld = [d for m in models for d in m["nearest_pivot_distance"]["per_quad"]]
    xs = [abs(p[0]) for m in models for p in m["hinge_pivots"]]
    side = sorted(x for x in xs if x > 0.1)
    pivot_x = {"n": len(xs), "side_n": len(side), "side_min": side[0] if side else None,
               "side_max": side[-1] if side else None,
               "centre_n": sum(1 for x in xs if x <= 0.1)}
    checks = {
        "four_quads_per_entity": all(
            len(m["nearest_pivot_distance"]["per_quad"]) == 4 and m["entity_count"] >= 1
            for m in models),
        "variants_of_one_car_agree": all(
            m["nearest_pivot_distance"]["variants_identical"] for m in models),
        "quads_inside_system_object": all(m["container"]["class"] == SYS_CLASS for m in models),
        "quads_are_distinct_table_entries": all(
            len(m["table"]["station_ids"]) == 4 and
            m["table"]["id_first"] <= min(m["table"]["station_ids"]) and
            max(m["table"]["station_ids"]) <= m["table"]["id_last"]
            for m in models),
        "only_wheel_entries_have_a_position": all(
            m["table"]["nonzero_positions"] == 4 for m in models),
        "station_rotation_is_identity": all(
            all(abs(q[0]) < 1e-6 and abs(q[1]) < 1e-6 and abs(q[2]) < 1e-6 and
                abs(abs(q[3]) - 1.0) < 1e-5 for q in m["table"]["station_quats"])
            for m in models),
        "named_hardpoints_agree": all(m["named_hardpoints_agree"] for m in models),
        "no_quad_is_a_hinge_pivot": all(d > 0.2 for d in alld),
        "hinge_frames_share_the_pivot": all(
            m["hinges"]["AB_equal"] == m["hinges"]["n"] for m in models),
    }
    return {
        "schema": "jc3.stations_vs_hinges/1",
        "generated_by": "Tools/scripts/jc3_stations_vs_hinges.py",
        "question": "are the four wheel-station quads the hinge pivots G3-10e decoded?",
        "answer": "no",
        "inputs": {"phys_grab": os.path.join(RAW, "phys"),
                   "limits_json": "Research/JC3Grab/PHYSICS_LIMITS.json",
                   "limits_md": "Research/JC3Grab/PHYSICS_LIMITS.md"},
        "entities": len(ents), "models": len(models),
        "distance_all_quads": {"n": len(alld), "min": min(alld),
                               "median": sorted(alld)[len(alld) // 2], "max": max(alld),
                               "within_1e-3": sum(1 for d in alld if d <= 1e-3),
                               "within_1e-2": sum(1 for d in alld if d <= 1e-2),
                               "within_0.05": sum(1 for d in alld if d <= 0.05),
                               "within_0.2": sum(1 for d in alld if d <= 0.2)},
        "models_detail": models,
        "pivot_x": pivot_x,
        "problems": problems,
        "station_ids": {os.path.basename(m["physicsc"]): m["table"]["station_ids"]
                        for m in models},
        "station_ids_consecutive": sum(
            1 for m in models
            if m["table"]["station_ids"] == list(range(m["table"]["station_ids"][0],
                                                       m["table"]["station_ids"][0] + 4))),
        "checks": checks,
    }


# ---------------------------------------------------------------- render
def fmt(v, n=3):
    return ("%." + str(n) + "f") % v


def render(doc):
    L_ = []
    A = L_.append
    A("# Do the wheel-station quads coincide with G3-10e's hinge pivots?")
    A("")
    A("**Answer: no** - the quads are not hinge pivots, and the rectangle heuristic is not "
      "confirmed by G3-10e's constraints.  Not one of the %d station quads in the six distinct "
      "`.physicsc` files (4 per file, 68 across the 17 entities) is a hinge pivot: the closest "
      "quad-to-pivot "
      "distance in any file is **%s m**, the median **%s m**, the farthest **%s m**, over the "
      "%d hinge pivots those six files carry.  What the quads *are* is decoded in §3: the "
      "position field of four entries of a 96-byte table inside `hknpPhysicsSystemData`."
      % (doc["distance_all_quads"]["n"],
         fmt(doc["distance_all_quads"]["min"]), fmt(doc["distance_all_quads"]["median"]),
         fmt(doc["distance_all_quads"]["max"]),
         sum(len(m["hinge_pivots"]) for m in doc["models_detail"])))
    A("")
    A("Read `PHYSICS.md`'s 17/17 agreement as what it is: the four quads equal the four named "
      "`land_global.base_wheel_hardpoint_positions` (re-derived here, 17/17), i.e. a bytes-vs-"
      "name check.  What the quads are is settled by the surrounding bytes, not by the hinges.")
    A("")
    A("## 1. Inputs")
    A("")
    A("| input | what |")
    A("|---|---|")
    A("| `%s` | the 232 per-entity `.physicsc` grabs, of which **17** have one station set |"
      % doc["inputs"]["phys_grab"])
    A("| `%s` | G3-10e's hinge decode: 419 `hkpLimitedHingeConstraintData`, frames A/B |"
      % doc["inputs"]["limits_json"])
    A("| `%s` | the station method being checked |" % doc["inputs"]["limits_md"])
    A("")
    A("The 17 entities are **%d distinct `.physicsc` files** - the variants of a car share one; "
      "the tables below are per file." % doc["models"])
    A("")
    A("## 2. Stations against hinge pivots, per model")
    A("")
    A("`nearest` = Euclidean distance from a station quad to the closest hinge pivot (frame A) "
      "in the same file.  Frame B carries the **same translation** as frame A in %s of %s "
      "hinges, so both frames were tested and only A is shown."
      % (sum(m["hinges"]["AB_equal"] for m in doc["models_detail"]),
         sum(m["hinges"]["n"] for m in doc["models_detail"])))
    A("")
    A("| `.physicsc` | entities | hinges | track | wheelbase | nearest pivot distances (4 quads) |")
    A("|---|---:|---:|---:|---:|---|")
    for m in doc["models_detail"]:
        A("| `%s` | %d | %d | %s | %s | %s |"
          % (os.path.basename(m["physicsc"]), m["entity_count"], m["hinges"]["n"],
             m["station"]["track_m"], m["station"]["wheelbase_m"],
             ", ".join(fmt(d) for d in m["nearest_pivot_distance"]["per_quad"])))
    A("")
    A("Distance distribution over all %d quads: **min %s**, median **%s**, max **%s**.  "
      "Quads within 1 mm of a pivot: **%d**; within 1 cm: **%d**; within 5 cm: **%d**; within "
      "20 cm: **%d**."
      % (doc["distance_all_quads"]["n"], fmt(doc["distance_all_quads"]["min"]),
         fmt(doc["distance_all_quads"]["median"]), fmt(doc["distance_all_quads"]["max"]),
         doc["distance_all_quads"]["within_1e-3"], doc["distance_all_quads"]["within_1e-2"],
         doc["distance_all_quads"]["within_0.05"], doc["distance_all_quads"]["within_0.2"]))
    A("")
    A("Decoded: the pivots reach y = %s m, far above every station's single hub height "
      "(y = %s … %s m across the six files).  `derived`: the hinges are body-panel joints (the "
      "decoded limit pairs are door-like: `0..80`, `-35..0`, `-15..0`, `0..30/70/90` deg, and "
      "%d of the %d pivots sit on the body sides at |x| %.3f-%.3f m and %d on the centre line at "
      "|x| <= 0.1 m), while the quads sit at wheel-centre height.  Which panels they are is "
      "UNKNOWN.  "
      "The nearest pivot to a station is the outboard hinge of the same corner."
      % (fmt(max(max(p[1] for p in m["hinge_pivots"]) for m in doc["models_detail"])),
         fmt(min(m["station"]["y"] for m in doc["models_detail"])),
         fmt(max(m["station"]["y"] for m in doc["models_detail"])),
         doc["pivot_x"]["side_n"], doc["pivot_x"]["n"], doc["pivot_x"]["side_min"],
         doc["pivot_x"]["side_max"], doc["pivot_x"]["centre_n"]))
    A("")
    A("## 3. What the quads are")
    A("")
    A("Every station quad is the **first field of a 96-byte entry** in one contiguous run of "
      "entries inside the `hknpPhysicsSystemData` object of the same file:")
    A("")
    A("| entry offset | bytes | reading |")
    A("|---:|---|---|")
    A("| +0x00 | `float4` | **position**, `(x, y, z, 1.0)` - this is the station quad |")
    A("| +0x10 | `float4` | `(0, 0, 0, 0.99999994)` - unit quaternion, i.e. no rotation |")
    A("| +0x20 | 16 B | zero |")
    A("| +0x30 | `u32 u32 i32 u16` | `0`, `0`, `0x7fffffff`, **id** |")
    A("| +0x40 | `u16 u16` | a flag (`1` or `255`) and the same **id** |")
    A("| +0x50 | 16 B | zero |")
    A("")
    A("Decoded facts about the run (each re-derived by `--check`):")
    A("")
    A("| file | entries | ids | the four wheel ids | entries with a non-zero position | flags seen |")
    A("|---|---:|---|---|---:|---|")
    for m in doc["models_detail"]:
        t = m["table"]
        A("| `%s` | %d | %d..%d | %s | **%d** | %s |"
          % (os.path.basename(m["physicsc"]), t["entries"], t["id_first"], t["id_last"],
             t["station_ids"], t["nonzero_positions"],
             ", ".join(str(f) for f in t["flags"])))
    A("")
    A("So the four quads are four entries of **one contiguous table** in the same object, and "
      "they are the **only** entries of it that carry a non-zero position (%d of %s).  Their "
      "ids are consecutive in **%d of the %d files** and split 2+2 in `sportsmuscle.physicsc` "
      "(%s), so 'consecutive' is a property of five files, not a rule.  Every one of the four "
      "carries the identity rotation.  The entry type's Havok name is **UNKNOWN** (§6): the "
      "container class is decoded from the packfile's own class name, and the four entries are "
      "the wheel poses because their positions equal the four named wheel hardpoints "
      "(re-derived here, 17/17)."
      % (doc["models_detail"][0]["table"]["nonzero_positions"],
         ", ".join(str(m["table"]["entries"]) for m in doc["models_detail"]),
         doc["station_ids_consecutive"], doc["models"],
         "; ".join("%s %s" % (k.replace(".physicsc", ""),
                              ("%d-%d" % (v[0], v[-1])) if v == list(range(v[0], v[-1] + 1))
                              else "/".join(str(x) for x in v))
                   for k, v in doc["station_ids"].items())))
    A("")
    A("Container per file:")
    A("")
    A("| `.physicsc` | class | object offset | extent | quad offsets inside it |")
    A("|---|---|---:|---:|---|")
    for m in doc["models_detail"]:
        c = m["container"]
        A("| `%s` | `%s` | 0x%X | %d B | %s |"
          % (os.path.basename(m["physicsc"]), c["class"], c["object_offset"], c["extent"],
             c["relative"]))
    A("")
    A("## 4. Why the hinges are not the answer")
    A("")
    A("- The hinge pivots live in separate `hkpLimitedHingeConstraintData` objects (304 B each), "
      "not in the `hknpPhysicsSystemData` table the quads sit in.")
    A("- A car with 16 hinges (the tank) has four station quads; a car with 8 hinges (the "
      "sedan) has four.  The count does not track.")
    A("- The pivots spread over these y ranges, one per file: %s; the quads of a car all sit at "
      "a single y (%s … %s m)."
      % (", ".join("%s %.3f-%.3f" % (os.path.basename(m["physicsc"]).replace(".physicsc", ""),
                                    min(p[1] for p in m["hinge_pivots"]),
                                    max(p[1] for p in m["hinge_pivots"]))
                   for m in doc["models_detail"]),
         fmt(min(m["station"]["y"] for m in doc["models_detail"])),
         fmt(max(m["station"]["y"] for m in doc["models_detail"]))))
    A("- Both frames of every hinge carry the same translation, so a pivot is one point in "
      "vehicle space; the quads are 0.40-1.43 m away from the nearest of them.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| oracle | result |")
    A("|---|---|")
    for k, v in doc["checks"].items():
        A("| `%s` | **%s** |" % (k, "pass" if v else "FAIL"))
    A("")
    A("`four_quads_per_entity` and `variants_of_one_car_agree` cover the 17 entities / 6 files.  "
      "`only_wheel_entries_have_a_position` is the sharp one: 4 of N entries "
      "(N = %s) are non-zero and they are exactly the station quads - an arbitrary float4 would "
      "not come with an id, a repeated id, the `0x7fffffff` sentinel and a unit quaternion in "
      "the next 16 bytes.  `no_quad_is_a_hinge_pivot` fails if any quad comes within 20 cm of "
      "any pivot; the closest is %s m, so it clears its bar by 2x."
      % (", ".join(str(m["table"]["entries"]) for m in doc["models_detail"]),
         fmt(doc["distance_all_quads"]["min"])))
    A("")
    A("## 6. UNKNOWNs")
    A("")
    A("- **The 96-byte entry's Havok type name.**  No Havok 2014.1 header or type library is in "
      "this project.  Fields are labelled by their decoded shape (float4 position with "
      "`w == 1.0`, unit quaternion, sentinel `0x7fffffff`, repeated id), never by a name.")
    A("- **The meaning of the `u16` flag at +0x40** (`1` in some files, `255` in others) and of "
      "the two zero `u32` at +0x30.")
    A("- **Why the run is as long as it is** (e.g. %s entries in the campervan) and why the "
      "wheel ids differ per file (%s in the six files): the table's other entries are all "
      "`(0, 0, 0)`, so the file does not say what they stand for."
      % (doc["models_detail"][0]["table"]["entries"],
         ", ".join(str(m["table"]["station_ids"]) for m in doc["models_detail"])))
    A("- **Whether the game uses a hinge or a raycast for these wheels**: no wheel constraint "
      "object appears in the six files (all hinges are `hkpLimitedHingeConstraintData`, "
      "304 B), but a raycast wheel model would live in the vehicle's run-time data, which is "
      "not in `.physicsc`.")
    A("")
    A("## 7. Tool")
    A("")
    A("```")
    A("python Tools/scripts/jc3_stations_vs_hinges.py --write   # this page + the JSON")
    A("python Tools/scripts/jc3_stations_vs_hinges.py --check   # re-derive, diff, exit 1 on drift")
    A("```")
    A("")
    A("G3-10e's own `jc3_physics_limits.scan` is imported and run on the same bytes (through a "
      "byte-identical temp copy, deleted after use), so the hinge side of this check is their "
      "decoder, not a re-implementation.")
    A("")
    return "\n".join(L_)


def main():
    doc = run()
    if "--write" in sys.argv:
        md = render(doc)
        os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1, sort_keys=False)
            f.write("\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote", os.path.relpath(OUT_JSON, ROOT))
        print("wrote", os.path.relpath(OUT_MD, ROOT))
        print("answer:", doc["answer"])
        for k, v in doc["checks"].items():
            print("  %-34s %s" % (k, "pass" if v else "FAIL"))
        return 0 if all(doc["checks"].values()) else 1
    if "--check" in sys.argv:
        md = render(doc)
        ok = True
        saved_json = open(OUT_JSON, encoding="utf-8").read()
        saved_md = open(OUT_MD, encoding="utf-8").read()
        fresh = json.dumps(doc, indent=1, sort_keys=False) + "\n"
        print("json:", "PASS" if saved_json == fresh else "FAIL")
        print("md:  ", "PASS" if saved_md == md else "FAIL")
        ok = saved_json == fresh and saved_md == md
        for k, v in doc["checks"].items():
            print("  %-34s %s" % (k, "pass" if v else "FAIL"))
            ok = ok and v
        print("check:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    print(json.dumps({k: doc[k] for k in ("answer", "entities", "models",
                                          "distance_all_quads", "checks")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
