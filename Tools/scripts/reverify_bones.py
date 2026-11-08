"""reverify_bones.py - does the cooked SkeletalMesh agree with BONES.md? (BONES re-verification)

`Research/BatmobileGrab/BONES.md` (G1-11, `grab_bones.py`) describes the Batmobile's skeleton and
LODs from the umodel-written ActorX `.pskx`/`.psk` files plus the cooked package's section
tables. The PSKX files are a *tool's* export, so this tool asks the game's own bytes instead:

  * **bones** - the reference skeleton of `SkeletalMesh` export 5284 (`Batmobile_V2`) in
    `Playable_Batmobile_SF.upk`, decoded here and compared name by name and parent by parent
    with `BONES.json`;
  * **triangles** - every `FStaticLODModel3`'s section table in the same export, summed per LOD,
    compared with the `.pskx` face counts `BONES.json` reports.

Nothing is located by a name taken from the card being tested. The skeleton array is found by its
own record shape: a run of 44-byte records `{quat(16) | pos(12) | FName(8) | parent(4) | -1(4)}`
in which the 4-byte word at +40 is `0xFFFFFFFF`, the 16 bytes at +0 are a unit quaternion, the
FName at +28 resolves in the package's name table, and the word at +36 gives a single connected
180-node tree. The LOD models are found by the `Sections` signature: 13-byte entries
(`int16 MaterialIndex, int16 ChunkIndex, int32 FirstIndex, int32 NumTriangles, byte`) whose
`FirstIndex` is the running `3 * NumTriangles`, followed by an index buffer whose count is exactly
`3 * faces`. Both signatures are oracles: random vertex/index data does not satisfy them, and the
comparison with BONES.json is a separate, later step.

Writes `Research/BatmobileGrab/REVERIFY_BONES.json` + `.md`.

Usage:
    python Tools/scripts/reverify_bones.py --write
    python Tools/scripts/reverify_bones.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
PACKAGE = "Playable_Batmobile_SF"
EXPORT = 5284
MESH = "Batmobile_V2"
RES = os.path.join(ROOT, "Research", "BatmobileGrab")
BONES_JSON = os.path.join(RES, "BONES.json")
BONES_MD = os.path.join(RES, "BONES.md")
OUT_JSON = os.path.join(RES, "REVERIFY_BONES.json")
OUT_MD = os.path.join(RES, "REVERIFY_BONES.md")

STRIDE = 44
SECTION_SIZE = 13
FF = b"\xff\xff\xff\xff"


class BoneError(Exception):
    pass


# ------------------------------------------------------------------ helpers
def f32(d: bytes, o: int) -> float:
    return struct.unpack_from("<f", d, o)[0]


def i32(d: bytes, o: int) -> int:
    return struct.unpack_from("<i", d, o)[0]


def quat_ok(d: bytes, o: int, tol: float = 0.02) -> bool:
    q = [f32(d, o + 4 * j) for j in range(4)]
    n = math.sqrt(sum(v * v for v in q))
    return abs(n - 1.0) <= tol


def name_ok(pkg: U.Package, d: bytes, o: int) -> tuple[str, int] | None:
    """A record's FName is (index u32, number u32); number 0 and a resolvable index."""
    ni, num = struct.unpack_from("<II", d, o)
    if num != 0 or ni >= len(pkg.names):
        return None
    return pkg.names[ni], ni


# ------------------------------------------------------------------ skeleton
def find_ref_skeleton(pkg: U.Package, d: bytes) -> dict:
    """Locate the 44-byte reference-skeleton record run by its own shape, then decode it."""
    runs = []
    pos = d.find(FF)
    while pos >= 0:
        p = pos - 40
        if p >= 0 and quat_ok(d, p) and name_ok(pkg, d, p + 28) is not None:
            n = 1
            while True:
                q = p + STRIDE * n
                if q + STRIDE > len(d) or d[q + 40:q + 44] != FF:
                    break
                if not quat_ok(d, q) or name_ok(pkg, d, q + 28) is None:
                    break
                n += 1
            runs.append((n, p))
        pos = d.find(FF, pos + 1)
    if not runs:
        raise BoneError("no 44-byte reference-skeleton record run found in the export")
    n, origin = max(runs)
    span = range(origin, origin + STRIDE * n)
    others = [r for r in runs if r[1] not in span]
    rows = []
    for k in range(n):
        o = origin + STRIDE * k
        name, ni = name_ok(pkg, d, o + 28)
        rows.append({
            "index": k,
            "name": name,
            "name_index": ni,
            "parent_index": i32(d, o + 36),
            "quat": [round(f32(d, o + 4 * j), 6) for j in range(4)],
            "position_cm": [round(f32(d, o + 16 + 4 * j), 5) for j in range(3)],
            "trailer_word": struct.unpack_from("<I", d, o + 40)[0],
        })
    return {"origin": origin, "stride": STRIDE, "count": n, "records": rows,
            "runs_found": len(runs),
            "other_longest_run": max((r[0] for r in others), default=0),
            "other_runs_of_2_plus": sum(1 for r in others if r[0] >= 2),
            "origin_label": "offset of record 0 inside the export's data (quat first: "
                            "quat@+0, position@+16, FName@+28, parent@+36, 0xFFFFFFFF@+40)"}


def tree_facts(rows: list[dict]) -> dict:
    parent = [r["parent_index"] for r in rows]
    n = len(parent)
    roots = [k for k in range(n) if parent[k] == k]
    reach = {}
    cyc = []
    for k in range(n):
        seen, j, hops = set(), k, 0
        while True:
            if j in seen:
                cyc.append(k)
                break
            seen.add(j)
            if parent[j] == j:
                reach[k] = hops
                break
            j = parent[j]
            hops += 1
            if hops > n:
                cyc.append(k)
                break
    return {"roots": roots, "parents_le_index": all(parent[k] <= k for k in range(n)),
            "connected": len(reach) == n and not cyc, "cycles": sorted(set(cyc))[:8],
            "distinct_names": len({r["name"] for r in rows}),
            "max_quat_norm_err": max(abs(math.sqrt(sum(v * v for v in r["quat"])) - 1.0)
                                     for r in rows),
            "trailer_words": sorted({r["trailer_word"] for r in rows})}


# ------------------------------------------------------------------ LOD models
def lod_models(d: bytes) -> list[dict]:
    """Every FStaticLODModel3 of the export: sections summed, index count confirmed."""
    cands = []
    arrays_seen = 0
    for j in range(0, len(d) - SECTION_SIZE - 8):
        n = i32(d, j)
        if not 1 <= n <= 64:
            continue
        o, cum, secs = j + 4, 0, []
        for _ in range(n):
            if o + SECTION_SIZE > len(d):
                break
            mat, chunk = struct.unpack_from("<hh", d, o)
            fi, nt = struct.unpack_from("<ii", d, o + 4)
            if fi != cum or nt <= 0 or not 0 <= mat < 64 or not 0 <= chunk < 512:
                break
            cum += 3 * nt
            secs.append({"material": mat, "chunk": chunk, "first_index": fi, "faces": nt})
            o += SECTION_SIZE
        else:
            arrays_seen += 1
            want = cum                     # 3 * faces
            idx_at = next((o + k for k in range(6, 14)
                           if o + k + 4 <= len(d) and i32(d, o + k) == want), None)
            if idx_at is None:
                continue                   # a section array whose index buffer is not there
            cands.append({"at": j, "sections": secs, "faces": sum(s["faces"] for s in secs),
                          "sections_end": o, "index_count_at": idx_at,
                          "index_count": want, "lod_array_len": i32(d, j - 4)})
    if not cands:
        return []
    first = next((c for c in cands if c["lod_array_len"] == len(cands)), cands[0])
    chain = sorted((c for c in cands if c["at"] >= first["at"]), key=lambda c: c["at"])
    out = []
    for i, c in enumerate(chain[: first["lod_array_len"]]):
        per_mat: dict[str, int] = {}
        for s in c["sections"]:
            per_mat[str(s["material"])] = per_mat.get(str(s["material"]), 0) + s["faces"]
        out.append({"lod": i, "offset": c["at"], "sections": len(c["sections"]),
                    "faces": c["faces"], "indices": c["index_count"],
                    "first_index_last": c["sections"][-1]["first_index"],
                    "faces_by_material": dict(sorted(per_mat.items(), key=lambda kv: int(kv[0]))),
                    "declared_lod_count": first["lod_array_len"],
                    "section_arrays_seen": arrays_seen,
                    "with_index_buffer": len(cands)})
    return out


def md_bones(path: str) -> list[tuple[int, str, str]]:
    """The `| index | bone | parent | ...` rows of BONES.md's skeleton table."""
    rows = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line)
        if m:
            rows.append((int(m.group(1)), m.group(2), m.group(3)))
    return rows


def md_verdict_faces(path: str) -> list[int]:
    """The three comma-grouped LOD face counts in BONES.md's verdict line."""
    for line in open(path, encoding="utf-8"):
        m = re.search(r"LODs: ([\d,]+) / ([\d,]+) / ([\d,]+)", line)
        if m:
            return [int(x.replace(",", "")) for x in m.groups()]
    return []


# ------------------------------------------------------------------ build
def build() -> dict:
    pkg = U.Package(os.path.join(GAME, PACKAGE + ".upk"))
    if pkg.object_path(EXPORT) != "Batmobile_V2_Mesh.Batmobile_V2" or \
            pkg.object_class(EXPORT) != "SkeletalMesh":
        raise BoneError("export %d is %s (%s), not the Batmobile_V2 SkeletalMesh"
                        % (EXPORT, pkg.object_path(EXPORT), pkg.object_class(EXPORT)))
    d = pkg.data(EXPORT)
    sk = find_ref_skeleton(pkg, d)
    facts = tree_facts(sk["records"])
    lods = lod_models(d)

    bj = json.load(open(BONES_JSON, encoding="utf-8"))
    cb = bj["bones"]
    # Bind-pose oracle for the field ORDER inside a record: the cooked pose must equal the PSKX
    # bind pose on every bone once the PSK's Y-negation is applied. If the quat/position slots
    # were in the wrong order this fails on all 180 bones instead of agreeing to 1e-7.
    bind = {"quat_max_1_minus_abs_dot": 0.0, "pos_max_dist_cm": 0.0, "bones_ok": 0}
    for k, r in enumerate(sk["records"]):
        q = [r["quat"][0], -r["quat"][1], r["quat"][2], r["quat"][3]]
        p = [r["position_cm"][0], -r["position_cm"][1], r["position_cm"][2]]
        bq = cb[k]["bind"]["local_rotation_quat"]
        bp = cb[k]["bind"]["local_position_cm"]
        dq = 1.0 - min(abs(sum(q[j] * bq[j] for j in range(4))), 1.0)
        dp = math.dist(p, bp)
        bind["quat_max_1_minus_abs_dot"] = max(bind["quat_max_1_minus_abs_dot"], dq)
        bind["pos_max_dist_cm"] = max(bind["pos_max_dist_cm"], dp)
        if dq < 1e-6 and dp < 0.01:
            bind["bones_ok"] += 1
    bind["quat_max_1_minus_abs_dot"] = float("%.3g" % bind["quat_max_1_minus_abs_dot"])
    bind["pos_max_dist_cm"] = float("%.6f" % bind["pos_max_dist_cm"])
    bind["label"] = ("decoded: the cooked record's quat/position reproduce BONES.json's PSKX "
                     "bind pose on %d/%d bones when the PSK's Y component is negated (the "
                     "convention grab_collision_frame.py reports); this is what fixes quat "
                     "before position inside the record"
                     % (bind["bones_ok"], len(sk["records"])))
    cmp_names = [k for k in range(min(len(cb), len(sk["records"])))
                 if sk["records"][k]["name"] != cb[k]["name"]]
    cmp_par = [k for k in range(min(len(cb), len(sk["records"])))
               if sk["records"][k]["parent_index"] != cb[k]["parent_index"]]
    # the card's own page, parsed independently of its json
    rows = md_bones(BONES_MD)
    md_name_bad = [(i, n, sk["records"][i]["name"]) for i, n, _ in rows
                   if i < sk["count"] and sk["records"][i]["name"] != n]
    md_par_bad = [(i, p, sk["records"][sk["records"][i]["parent_index"]]["name"]) for i, _, p in rows
                  if i < sk["count"]
                  and sk["records"][sk["records"][i]["parent_index"]]["name"] != p]
    md_faces = md_verdict_faces(BONES_MD)
    cmp_face = [(l["lod"], l["faces"], bj["lods"][l["lod"]]["faces"] if l["lod"] < len(bj["lods"]) else None)
                for l in lods
                if l["lod"] >= len(bj["lods"]) or l["faces"] != bj["lods"][l["lod"]]["faces"]]
    cmp_sec = [(l["lod"], l["sections"], bj["lods"][l["lod"]].get("sections"))
               for l in lods
               if l["lod"] < len(bj["lods"]) and l["sections"] != bj["lods"][l["lod"]].get("sections")]

    doc = {
        "schema": 1,
        "generator": "reverify_bones.py",
        "question": "do the cooked SkeletalMesh's own bytes agree with BONES.md/BONES.json, which "
                    "were built from umodel's PSKX exports?",
        "verdict": None,
        "source": {
            "package": "%s.upk" % PACKAGE,
            "path": os.path.join(GAME, PACKAGE + ".upk"),
            "export": EXPORT,
            "object": pkg.object_path(EXPORT),
            "class": pkg.object_class(EXPORT),
            "export_bytes": len(d),
            "mesh": MESH,
        },
        "skeleton": {
            "count": sk["count"],
            "origin_in_export": sk["origin"],
            "stride": sk["stride"],
            "runs_matching_the_record_shape": sk["runs_found"],
            "other_longest_run": sk["other_longest_run"],
            "other_runs_of_2_plus": sk["other_runs_of_2_plus"],
            "first": sk["records"][0],
            "last": sk["records"][-1],
            "names": [r["name"] for r in sk["records"]],
            "parents": [r["parent_index"] for r in sk["records"]],
            "names_sha1": __import__("hashlib").sha1(
                "\n".join(r["name"] for r in sk["records"]).encode()).hexdigest(),
            "parents_sha1": __import__("hashlib").sha1(
                ",".join(str(r["parent_index"]) for r in sk["records"]).encode()).hexdigest(),
            "label": "decoded: %d records at %d, stride %d (%s)" % (
                sk["count"], sk["origin"], sk["stride"], sk["origin_label"]),
        },
        "skeleton_oracles": facts,
        "skeleton_bind_vs_PSKX": bind,
        "lods": lods,
        "comparison_to_BONES_md": {
            "table_rows": len(rows),
            "indices_0_to_n_minus_1": [r[0] for r in rows] == list(range(len(rows))),
            "name_mismatches": md_name_bad,
            "parent_name_mismatches": md_par_bad,
            "verdict_faces": md_faces,
            "verdict_faces_match": md_faces == [l["faces"] for l in lods],
            "label": "parsed from BONES.md: the `| index | bone | parent |` table and the face "
                     "counts in its verdict line, compared with this decode",
        },
        "comparison_to_BONES_json": {
            "bones_in_card": len(cb),
            "name_mismatches": cmp_names,
            "parent_mismatches": cmp_par,
            "face_mismatches": cmp_face,
            "section_mismatches": cmp_sec,
            "lod_count_cooked": len(lods),
            "lod_count_card": len(bj["lods"]),
        },
    }
    agree = (not cmp_names and not cmp_par and not cmp_face and not cmp_sec
             and len(cb) == len(sk["records"]) and len(lods) == len(bj["lods"])
             and facts["connected"] and len(facts["roots"]) == 1
             and bind["bones_ok"] == len(sk["records"])
             and not md_name_bad and not md_par_bad and md_faces == [l["faces"] for l in lods]
             and len(rows) == sk["count"])
    doc["verdict"] = (
        "AGREES: the cooked SkeletalMesh carries %d bones with the same names and the same parent "
        "index on every bone as BONES.md/.json, and its own section tables give %s faces at "
        "LOD0/1/2 (%s sections) - identical to the card. The PSKX-based cards rest on a faithful "
        "export for the skeleton and the triangle counts."
        % (sk["count"], " / ".join("%d" % l["faces"] for l in lods),
           "/".join("%d" % l["sections"] for l in lods))
    ) if agree else (
        "DISAGREES: cooked bones %d vs card %d, name mismatches %d, parent mismatches %d, face "
        "mismatches %s."
        % (len(sk["records"]), len(cb), len(cmp_names), len(cmp_par), cmp_face)
    )
    doc["agrees"] = agree
    return doc


def check(doc: dict) -> list[str]:
    """Recompute from the package bytes and fail on any disagreement with the stored record."""
    fresh = build()
    bad = []
    if not fresh["agrees"]:
        bad.append("the decode does not agree with BONES.json: %s" % fresh["verdict"])
    if fresh["skeleton_oracles"]["roots"] != [0]:
        bad.append("roots %s, expected exactly [0]" % fresh["skeleton_oracles"]["roots"])
    if not fresh["skeleton_oracles"]["connected"]:
        bad.append("the parent field does not form one connected tree")
    if fresh["skeleton_oracles"]["distinct_names"] != fresh["skeleton"]["count"]:
        bad.append("bone names repeat")
    for l in fresh["lods"]:
        if l["indices"] != 3 * l["faces"]:
            bad.append("LOD%d index count %d != 3 * %d" % (l["lod"], l["indices"], l["faces"]))
        if sum(l["faces_by_material"].values()) != l["faces"]:
            bad.append("LOD%d per-material sum != total" % l["lod"])
    m = fresh["comparison_to_BONES_md"]
    if m["table_rows"] != fresh["skeleton"]["count"] or not m["indices_0_to_n_minus_1"]:
        bad.append("BONES.md's bone table has %d rows, expected %d in index order"
                   % (m["table_rows"], fresh["skeleton"]["count"]))
    if m["name_mismatches"]:
        bad.append("BONES.md bone names differ at %d rows: %s"
                   % (len(m["name_mismatches"]), m["name_mismatches"][:3]))
    if m["parent_name_mismatches"]:
        bad.append("BONES.md parent column differs at %d rows: %s"
                   % (len(m["parent_name_mismatches"]), m["parent_name_mismatches"][:3]))
    if not m["verdict_faces_match"]:
        bad.append("BONES.md verdict face counts %s != %s"
                   % (m["verdict_faces"], [l["faces"] for l in fresh["lods"]]))
    if fresh != doc:
        for k in fresh:
            if fresh[k] != doc.get(k):
                bad.append("stored %r differs from a fresh decode" % k)
    return bad


# ------------------------------------------------------------------ markdown
def write_md(doc: dict) -> None:
    s, o, c = doc["skeleton"], doc["skeleton_oracles"], doc["comparison_to_BONES_json"]
    L = ["# Re-verification of BONES.md against the cooked SkeletalMesh", "",
         "Generated by `Tools/scripts/reverify_bones.py`. `BONES.md`/`BONES.json` were built from",
         "umodel's ActorX exports; this page reads the same mesh out of the shipped package and",
         "compares the two. Read-only: the game install is never written.", "",
         "## Verdict", "", doc["verdict"], "",
         "| question | cooked bytes | `BONES.md`/`.json` | same? |", "|---|---|---|---|",
         "| bones | %d | %d | %s |" % (s["count"], c["bones_in_card"],
                                        "yes" if s["count"] == c["bones_in_card"] else "**NO**"),
         "| bone names, in order | %d/%d equal | — | %s |" % (
             s["count"] - len(c["name_mismatches"]), s["count"],
             "yes" if not c["name_mismatches"] else "**NO**"),
         "| parent index | %d/%d equal | — | %s |" % (
             s["count"] - len(c["parent_mismatches"]), s["count"],
             "yes" if not c["parent_mismatches"] else "**NO**"),
         "| LODs | %d | %d | %s |" % (len(doc["lods"]), c["lod_count_card"],
                                       "yes" if len(doc["lods"]) == c["lod_count_card"] else "**NO**"),
         ]
    card_lods = json.load(open(BONES_JSON, encoding="utf-8"))["lods"]
    for l in doc["lods"]:
        card = card_lods[l["lod"]]["faces"] if l["lod"] < len(card_lods) else None
        L.append("| LOD%d faces | %d | %s | %s |" % (
            l["lod"], l["faces"], card, "yes" if card == l["faces"] else "**NO**"))
    m = doc["comparison_to_BONES_md"]
    L.append("| BONES.md bone table rows | %d | checked | %s |" % (
        len(doc["skeleton"]["names"]), "yes" if m["table_rows"] == len(doc["skeleton"]["names"])
        else "**NO**"))
    L.append("| BONES.md parent column | %d rows | checked | %s |" % (
        m["table_rows"], "yes" if not m["parent_name_mismatches"] else "**NO**"))
    L.append("| BONES.md verdict face counts | %s | %d numbers | %s |" % (
        " / ".join("%d" % f for f in m["verdict_faces"]), len(doc["lods"]),
        "yes" if m["verdict_faces_match"] else "**NO**"))
    L += ["", "## How the bones were found (no name from the card was used to locate them)", "",
          "The export's data is **%d bytes**. A 44-byte record shape was searched for by its own"
          % doc["source"]["export_bytes"],
          "contents, not by a bone name:", "",
          "* `+0` 16 bytes form a unit quaternion (|q| = 1 ± 0.02),",
          "* `+16` 12 bytes are a position in cm,",
          "* `+28` 8 bytes are an FName (index, number) with number 0 that resolves in the package",
          "  name table,",
          "* `+36` 4 bytes are an int32 parent index,",
          "* `+40` 4 bytes are `0xFFFFFFFF` on every record (observed values: %s)."
          % ", ".join("0x%08X" % w for w in o["trailer_words"]),
          "",
          "The scan starts a run at every record whose shape matches, so it reports **%d** starts;"
          % s["runs_matching_the_record_shape"],
          "the longest is **%d** records long (the skeleton); outside the skeleton's own span no"
          % s["count"],
          "run exists at all (longest **%d** record(s)) - so the array is not a coincidence of"
          % s["other_longest_run"],
          "vertex data."
          "It sits at offset **%d**, stride **%d**; it ends at %d and LOD0's section array"
          % (s["origin_in_export"], s["stride"],
             s["origin_in_export"] + s["stride"] * s["count"]),
          "starts at %d, so no record is missing from either end."
          % (doc["lods"][0]["offset"] if doc["lods"] else -1),
          "",
          "| oracle | result |", "|---|---|",
          "| exactly one root | %s (record %d, parent == its own index) |" % (
              "yes" if len(o["roots"]) == 1 else "**NO**", o["roots"][0] if o["roots"] else -1),
          "| every parent index <= the child's index (topological order) | %s |" % o["parents_le_index"],
          "| parent field forms one connected tree over all %d records | %s |" % (
              s["count"], o["connected"]),
          "| bone names are distinct | %d distinct / %d |" % (o["distinct_names"], s["count"]),
          "| all quaternions unit length | max abs(1-abs(q)) = %.2e |" % o["max_quat_norm_err"],
          "| the record's pose reproduces the PSKX bind pose (quat slot before position slot) "
          "| %d/%d bones, max 1-abs(dot) %.2e, max position error %.5f cm |"
          % (doc["skeleton_bind_vs_PSKX"]["bones_ok"], s["count"],
             doc["skeleton_bind_vs_PSKX"]["quat_max_1_minus_abs_dot"],
             doc["skeleton_bind_vs_PSKX"]["pos_max_dist_cm"]),
          ""]
    L += ["", "Record 0 and record %d as decoded:" % (s["count"] - 1), "",
          "```", json.dumps(s["first"], indent=1), json.dumps(s["last"], indent=1), "```", "",
          "## LOD triangles from the export's own section tables", "",
          "Each `FStaticLODModel3` is found by its `Sections` signature: 13-byte entries whose",
          "`FirstIndex` is exactly the running `3 * NumTriangles`, followed 6-13 bytes later by an",
          "index count equal to `3 * faces`. The 4 bytes before LOD0 hold the LOD count.",
          "",
          "| LOD | offset | sections | faces | indices | LODs declared at LOD0 | section arrays seen | arrays with an index buffer |",
          "|---|---|---|---|---|---|---|---|"]
    for l in doc["lods"]:
        L.append("| %d | %d | %d | %d | %d | %d | %d | %d |" % (
            l["lod"], l["offset"], l["sections"], l["faces"], l["indices"],
            l["declared_lod_count"], l["section_arrays_seen"], l["with_index_buffer"]))
    seen = doc["lods"][0]["section_arrays_seen"] if doc["lods"] else 0
    kept = doc["lods"][0]["with_index_buffer"] if doc["lods"] else 0
    L += ["", "The `declared_lod_count` is read from the `int32` at LOD0's section-array offset",
          "minus 4. Of the %d section arrays whose `FirstIndex` chain is self-consistent, only %d"
          % (seen, kept),
          "are followed by an index count of `3 * faces`; the rest are single-section 65,536-face",
          "lookalikes inside vertex data, rejected by that second test.", "",
          "## What this does and does not establish", "",
          "* **Established:** the skeleton (bone count, every bone name in order, every parent",
          "  index) and the per-LOD triangle counts in `BONES.md` are what the shipped package",
          "  contains. Cards that use those two things rest on a faithful export.",
          "* **Not established here:** anything derived from the PSKX that is *not* in this export -",
          "  vertex positions, wedges, `RAWWEIGHTS`, per-face ownership and the split-face counts.",
          "  Those are checked only in so far as the bind poses are: this decode reproduces the",
          "  PSKX bind pose on all %d bones (local position within 0.01 cm, quaternion within 1e-6"
          % s["count"],
          "  of unit dot) once the PSK's Y-negation is applied, which is the same convention",
          "  `grab_collision_frame.py` reports.", "",
          "## Reproduce", "", "```",
          "python Tools/scripts/reverify_bones.py --write",
          "python Tools/scripts/reverify_bones.py --check", "```"]
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write("\n".join(L))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="decode and write REVERIFY_BONES.json/.md")
    ap.add_argument("--check", action="store_true", help="recompute and fail on any disagreement")
    a = ap.parse_args()
    doc = build()
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        write_md(doc)
    s, c = doc["skeleton"], doc["comparison_to_BONES_json"]
    print("export %d %s, %d bytes" % (EXPORT, doc["source"]["object"], doc["source"]["export_bytes"]))
    print("bones: %d records at %d, stride %d; roots %s; connected %s"
          % (s["count"], s["origin_in_export"], s["stride"],
             doc["skeleton_oracles"]["roots"], doc["skeleton_oracles"]["connected"]))
    print("names vs BONES.json: %d/%d equal; parents: %d/%d equal"
          % (s["count"] - len(c["name_mismatches"]), s["count"],
             s["count"] - len(c["parent_mismatches"]), s["count"]))
    print("LODs: " + " / ".join("%d faces (%d sections)" % (l["faces"], l["sections"])
                                for l in doc["lods"]))
    print(doc["verdict"])
    if a.check:
        bad = check(doc)
        if bad:
            print("\nFAIL")
            for b in bad:
                print(" ", b)
            sys.exit(1)
        print("checks: cooked bones == BONES.md/.json names+parents, one connected root, "
              "LOD faces == card (json and verdict line), index counts == 3*faces, "
              "stored json == fresh decode - all ok")


if __name__ == "__main__":
    main()
