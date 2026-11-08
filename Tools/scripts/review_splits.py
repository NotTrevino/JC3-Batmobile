"""review_splits.py - B-02 split-face cut review at LOD0.

`grab_bones.py` established that 1,701 of the 299,837 LOD0 faces are "split": their three
points do not share one unique >= 0.5 influence, so no single bone owns the face.  This tool
answers the B-02 question: which bone sets and material slots do those faces sit on, and how
many can the "larger weight" rule actually decide?

For each split face it records, from the raw LOD0 weights:

  * the distinct owner bone of each of the three points;
  * the summed weight of each candidate bone across the three points;
  * the weight margin between the best and second candidate;
  * a part hint per bone (body, wheel_f_l/r/l/r, weapons, jet, aero_flaps).

A face is assigned by larger summed weight only when the margin is non-zero.  Faces whose
three points are each rigidly bound to a different bone have equal 1.0 sums; those are
reported as ties.  The review also gives every tie a part-level vertex vote (2 weapons + 1
body or 3 weapons) so B-02 has a deterministic fallback instead of an arbitrary `max()`.

This is a review, not an assembly: no mesh, RBM, face list or part manifest is written.  The
canonical split list is `E:\\Modding\\_gamedata\\BmAKgrab\\bones\\_split.npy`, read and checked against
a fresh ownership pass.

Outputs:
  Research/BatmobileGrab/SPLIT_FACES.json
  Research/BatmobileGrab/SPLIT_FACES.md

Usage:
  python Tools/scripts/review_splits.py --write
  python Tools/scripts/review_splits.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grab_bones as GB  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GRAB = ROOT / "Research" / "BatmobileGrab"
OUT_JSON = GRAB / "SPLIT_FACES.json"
OUT_MD = GRAB / "SPLIT_FACES.md"
BONES_JSON = GRAB / "BONES.json"

SCHEMA = 1
MARGIN_EPS = 1e-6


class SplitError(Exception):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fnum(v, places: int = 6):
    return round(float(v), places)


def bone_part(name: str) -> str:
    """Review-only part class, from the bone name.  The final part list is B-02's job."""
    b = name.lower()
    if ("front" in b or "frnt" in b) and "left" in b:
        return "wheel_f_l"
    if ("front" in b or "frnt" in b) and "right" in b:
        return "wheel_f_r"
    if "rear" in b and "left" in b:
        return "wheel_r_l"
    if "rear" in b and "right" in b:
        return "wheel_r_r"
    if "weapons" in b:
        return "weapons"
    if "jet" in b:
        return "jet"
    if "aero_flap" in b:
        return "aero_flaps"
    return "body"


def bone_set_label(names) -> str:
    return " + ".join(names)


def collect() -> dict:
    bdoc = json.loads(BONES_JSON.read_text(encoding="utf-8"))
    bones = bdoc["bones"]
    names = [b["name"] for b in bones]
    if len(bones) != 180:
        raise SplitError("BONES.json has %d bones, expected 180" % len(bones))
    lod0 = bdoc["lods"][0]
    mesh_path = Path(lod0["file"])
    if not mesh_path.exists():
        raise SplitError("missing LOD0 mesh %s" % mesh_path)
    if sha256_file(mesh_path) != lod0["sha256"]:
        raise SplitError("LOD0 mesh hash differs from BONES.json")
    mesh = GB.read_mesh(mesh_path)
    if len(mesh["F"]) != lod0["faces"]:
        raise SplitError("LOD0 face count %d differs from BONES.json %d"
                         % (len(mesh["F"]), lod0["faces"]))
    W, F = mesh["W"], mesh["F"]
    ro, rs, rn = mesh["chunks"]["RAWWEIGHTS"]
    if rs != 12:
        raise SplitError("RAWWEIGHTS stride %d, expected 12" % rs)
    rw = np.frombuffer(mesh["data"], np.dtype([
        ("w", "<f4"), ("p", "<u4"), ("b", "<u4")]), rn, ro)
    acc = np.zeros((len(mesh["P"]), len(bones)), dtype=np.float32)
    np.add.at(acc, (rw["p"].astype(np.int64), rw["b"].astype(np.int64)),
              rw["w"].astype(np.float32))
    total = acc.sum(1)
    if not np.allclose(total, 1.0, atol=1e-4):
        raise SplitError("point weights do not sum to 1 (max error %.3g)"
                         % float(np.max(np.abs(total - 1.0))))
    owner = acc.argmax(1).astype(np.int32)
    maxw = acc.max(1)
    ties = np.count_nonzero(acc == maxw[:, None], axis=1) > 1
    owner[ties | (maxw < 0.5)] = -1
    if np.any(owner < 0):
        raise SplitError("%d points have no unique >= 0.5 owner" % int((owner < 0).sum()))

    face_pts = W["p"][F["w"]].astype(np.int64)
    face_owner = owner[face_pts]
    same = ((face_owner[:, 0] == face_owner[:, 1]) &
            (face_owner[:, 1] == face_owner[:, 2]) &
            (face_owner[:, 0] >= 0))
    split_mask = ~same
    split_ids = set(int(x) for x in np.nonzero(split_mask)[0])
    if len(split_ids) != lod0["split"]:
        raise SplitError("re-derived split count %d differs from BONES.json %d"
                         % (len(split_ids), lod0["split"]))

    split_file = Path(bdoc["checks"]["split_file"])
    if not split_file.exists():
        raise SplitError("missing split list %s" % split_file)
    arr = np.load(split_file)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise SplitError("_split.npy is not (N,3): %s" % (arr.shape,))
    s0 = arr[arr[:, 0] == 0]
    npy_ids = set(int(x) for x in s0[:, 1])
    if npy_ids != split_ids:
        raise SplitError("_split.npy LOD0 face set differs from a fresh ownership pass "
                         "(%d vs %d, %d only npy, %d only fresh)"
                         % (len(npy_ids), len(split_ids),
                            len(npy_ids - split_ids), len(split_ids - npy_ids)))

    slot_map = lod0["slot_map"]
    slots = bdoc["slots"]
    slot_name = {int(s["index"]): s["material"] for s in slots}
    face_slot = np.array([slot_map[int(m)] for m in F["m"]], dtype=np.int64)
    for fi, slot in s0[:, 1:]:
        if int(slot) != int(face_slot[int(fi)]):
            raise SplitError("face %d slot %d differs from PSK slot %d"
                             % (fi, slot, face_slot[int(fi)]))

    faces = []
    for fi, slot in s0[:, 1:]:
        fi = int(fi)
        slot = int(slot)
        pts = face_pts[fi]
        own = face_owner[fi]
        cand = [int(b) for b in np.unique(own) if b >= 0]
        if len(cand) < 2 or len(cand) > 3:
            raise SplitError("face %d has %d candidate bones" % (fi, len(cand)))
        sums = {b: float(acc[pts, b].sum()) for b in cand}
        order = sorted(cand, key=lambda b: (sums[b], int(np.count_nonzero(own == b)), -b),
                       reverse=True)
        margin = sums[order[0]] - sums[order[1]]
        tie = margin < MARGIN_EPS
        winner = None if tie else names[order[0]]
        winner_part = None if tie else bone_part(names[order[0]])
        vertex_parts = Counter(bone_part(names[int(b)]) for b in own)
        vtop = max(vertex_parts.values())
        vwinners = sorted(k for k, v in vertex_parts.items() if v == vtop)
        tie_part = vwinners[0] if len(vwinners) == 1 else None
        parts = sorted({bone_part(names[b]) for b in cand})
        faces.append({
            "face": fi,
            "slot": slot,
            "slot_name": slot_name.get(slot),
            "bones": [names[b] for b in sorted(cand)],
            "bone_count": len(cand),
            "weights": {names[b]: fnum(sums[b]) for b in sorted(cand)},
            "margin": fnum(max(0.0, margin)),
            "tie": bool(tie),
            "winner": winner,
            "winner_part": winner_part,
            "vertex_parts": dict(sorted(vertex_parts.items())),
            "tie_part": tie_part,
            "recommended_part": winner_part if not tie else tie_part,
            "part_pair": "|".join(parts),
            "cross_part": len(parts) > 1,
        })
    faces.sort(key=lambda x: x["face"])

    by_slot = defaultdict(lambda: {"faces": 0, "sets": set(), "ties": 0, "cross_part": 0})
    by_set = defaultdict(lambda: {"faces": 0, "slots": Counter(), "winners": Counter(),
                                  "ties": 0, "parts": set(), "cross_part": 0,
                                  "min_margin": None, "max_margin": None})
    by_set_slot = defaultdict(lambda: {"faces": 0, "winners": Counter(), "ties": 0,
                                       "parts": set(), "cross_part": 0,
                                       "min_margin": None, "max_margin": None})
    by_part_pair = defaultdict(lambda: {"faces": 0, "sets": set(), "ties": 0})
    winners = Counter()

    for f in faces:
        key = (tuple(f["bones"]), f["slot"])
        s = by_set_slot[key]
        s["faces"] += 1
        s["parts"].update(f["part_pair"].split("|"))
        s["cross_part"] += int(f["cross_part"])
        s["min_margin"] = f["margin"] if s["min_margin"] is None else min(s["min_margin"], f["margin"])
        s["max_margin"] = f["margin"] if s["max_margin"] is None else max(s["max_margin"], f["margin"])
        if f["tie"]:
            s["ties"] += 1
        else:
            s["winners"][f["winner"]] += 1
            winners[f["winner"]] += 1

        k = tuple(f["bones"])
        b = by_set[k]
        b["faces"] += 1
        b["slots"][f["slot"]] += 1
        b["parts"].update(f["part_pair"].split("|"))
        b["cross_part"] += int(f["cross_part"])
        b["min_margin"] = f["margin"] if b["min_margin"] is None else min(b["min_margin"], f["margin"])
        b["max_margin"] = f["margin"] if b["max_margin"] is None else max(b["max_margin"], f["margin"])
        if f["tie"]:
            b["ties"] += 1
        else:
            b["winners"][f["winner"]] += 1

        sl = by_slot[f["slot"]]
        sl["faces"] += 1
        sl["sets"].add(k)
        sl["ties"] += int(f["tie"])
        sl["cross_part"] += int(f["cross_part"])

        pp = by_part_pair[f["part_pair"]]
        pp["faces"] += 1
        pp["sets"].add(k)
        pp["ties"] += int(f["tie"])

    set_rows = []
    for k, b in by_set.items():
        set_rows.append({
            "bones": list(k),
            "bone_count": len(k),
            "faces": b["faces"],
            "slots": [{"slot": s, "faces": n} for s, n in sorted(b["slots"].items())],
            "winners": dict(sorted(b["winners"].items())),
            "ties": b["ties"],
            "part_pair": "|".join(sorted(b["parts"])),
            "cross_part": b["cross_part"],
            "min_margin": fnum(b["min_margin"] or 0.0),
            "max_margin": fnum(b["max_margin"] or 0.0),
        })
    set_rows.sort(key=lambda r: (-r["faces"], r["bones"]))

    set_slot_rows = []
    for (k, slot), s in by_set_slot.items():
        set_slot_rows.append({
            "bones": list(k),
            "bone_count": len(k),
            "slot": slot,
            "slot_name": slot_name.get(slot),
            "faces": s["faces"],
            "winners": dict(sorted(s["winners"].items())),
            "ties": s["ties"],
            "part_pair": "|".join(sorted(s["parts"])),
            "cross_part": s["cross_part"],
            "min_margin": fnum(s["min_margin"] or 0.0),
            "max_margin": fnum(s["max_margin"] or 0.0),
        })
    set_slot_rows.sort(key=lambda r: (-r["faces"], r["bones"], r["slot"]))

    slot_rows = []
    for slot, s in sorted(by_slot.items()):
        tops = [r for r in set_rows if slot in [x["slot"] for x in r["slots"]]]
        tops.sort(key=lambda r: -sum(x["faces"] for x in r["slots"] if x["slot"] == slot))
        slot_rows.append({
            "slot": slot,
            "slot_name": slot_name.get(slot),
            "faces": s["faces"],
            "bone_sets": len(s["sets"]),
            "ties": s["ties"],
            "cross_part": s["cross_part"],
            "top_set": tops[0]["bones"] if tops else [],
            "top_set_faces": sum(x["faces"] for x in tops[0]["slots"] if x["slot"] == slot)
            if tops else 0,
        })

    part_rows = []
    for pp, s in by_part_pair.items():
        part_rows.append({
            "part_pair": pp,
            "faces": s["faces"],
            "bone_sets": len(s["sets"]),
            "ties": s["ties"],
        })
    part_rows.sort(key=lambda r: (-r["faces"], r["part_pair"]))
    cross_part = sum(1 for f in faces if f["cross_part"])
    ties = [f for f in faces if f["tie"]]
    tie_rows = []
    tie_groups = defaultdict(list)
    for f in ties:
        tie_groups[(tuple(f["bones"]), f["slot"], f["part_pair"], f["recommended_part"])].append(f)
    for (k, slot, pp, rec), fs in sorted(tie_groups.items(),
                                        key=lambda kv: (-len(kv[1]), kv[0][0], kv[0][1])):
        sample = fs[0]
        tie_rows.append({
            "bones": list(k),
            "slot": slot,
            "slot_name": sample["slot_name"],
            "faces": len(fs),
            "part_pair": pp,
            "weights": sample["weights"],
            "vertex_parts": sample["vertex_parts"],
            "recommended_part": rec,
            "face_ids": [f["face"] for f in fs],
        })
    tie_rows.sort(key=lambda r: (-r["faces"], r["bones"], r["slot"]))

    tie_part_counts = Counter(f["recommended_part"] for f in ties)
    tie_slot_counts = Counter(f["slot"] for f in ties)
    pair_count = sum(1 for k in by_set if len(k) == 2)
    triple_count = sum(1 for k in by_set if len(k) == 3)
    assigned = len(faces) - len(ties)

    checks = {
        "split_faces_1701": len(faces) == 1701,
        "split_face_set_matches_npy": npy_ids == split_ids,
        "split_by_slot_matches_bones": [int(np.sum(face_slot[list(split_ids)] == i))
                                        for i in range(len(slots))] == lod0["split_by_slot"],
        "all_faces_two_or_three_bones": all(2 <= f["bone_count"] <= 3 for f in faces),
        "group_face_sum_1701": sum(r["faces"] for r in set_rows) == len(faces),
        "set_slot_face_sum_1701": sum(r["faces"] for r in set_slot_rows) == len(faces),
        "slot_face_sum_1701": sum(r["faces"] for r in slot_rows) == len(faces),
        "part_pair_face_sum_1701": sum(r["faces"] for r in part_rows) == len(faces),
        "tie_group_face_sum_31": sum(r["faces"] for r in tie_rows) == len(ties),
        "winner_faces_sum_1670": sum(winners.values()) == assigned,
        "winner_plus_ties_1701": assigned + len(ties) == len(faces),
        "all_ties_three_bone": all(f["bone_count"] == 3 for f in ties),
        "all_ties_part_resolved": all(f["recommended_part"] is not None for f in ties),
        "all_ties_resolve_to_weapons": all(f["recommended_part"] == "weapons" for f in ties),
        "no_weight_winner_differs_from_part": all(
            (f["tie"] or f["winner_part"] == max(f["vertex_parts"], key=f["vertex_parts"].get))
            for f in faces),
        "cross_part_230": cross_part == 230,
        "tie_count_31": len(ties) == 31,
    }

    verdict = (
        "%d LOD0 split faces in %d bone sets (%d pairs, %d triples) and %d bone-set × slot "
        "groups; %d cross-part seams. %d faces resolve by summed weight; %d are three-bone "
        "ties at slots %s, all with a 2:1 or 3:0 part-level vertex majority (%s)."
        % (len(faces), len(by_set), pair_count, triple_count, len(set_slot_rows),
           cross_part, assigned, len(ties),
           ", ".join("%d (%d)" % (s, n) for s, n in sorted(tie_slot_counts.items())),
           ", ".join("%s %d" % (p, n) for p, n in tie_part_counts.most_common()))
    )

    doc = {
        "schema": SCHEMA,
        "generator": "review_splits.py",
        "verdict": verdict,
        "inputs": {
            "bones_json": str(BONES_JSON),
            "bones_sha256": sha256_file(BONES_JSON),
            "mesh": str(mesh_path),
            "mesh_sha256": sha256_file(mesh_path),
            "split_npy": str(split_file),
            "split_npy_sha256": sha256_file(split_file),
        },
        "convention": {
            "split_face": "the three points do not share one unique >= 0.5 owner",
            "weight": "sum of the point's bone weight over the face's three points",
            "margin": "best candidate weight minus second candidate weight",
            "tie": "margin < 1e-6 (all observed ties are exactly 0)",
            "part_hint": "body, wheel_f_l/r/l/r, weapons, jet, aero_flaps from the bone name",
            "bone_set": "sorted distinct owner bone names; 2 or 3 per split face",
            "assignment": "larger summed weight; a tie uses the part with more of the three vertices",
        },
        "counts": {
            "split_faces": len(faces),
            "bone_sets": len(by_set),
            "bone_pairs": pair_count,
            "bone_triples": triple_count,
            "bone_set_slot_groups": len(set_slot_rows),
            "assigned_by_weight": assigned,
            "ties": len(ties),
            "ties_by_slot": {str(k): v for k, v in sorted(tie_slot_counts.items())},
            "ties_by_recommended_part": dict(tie_part_counts),
            "cross_part_faces": cross_part,
            "winner_bones": len(winners),
        },
        "by_slot": slot_rows,
        "by_part_pair": part_rows,
        "by_bone_set": set_rows,
        "by_bone_set_slot": set_slot_rows,
        "ties": tie_rows,
        "winner_bones": [{"bone": b, "faces": n} for b, n in winners.most_common()],
        "checks": checks,
    }

    # ---- markdown ----
    md = []
    md.append("# Batmobile_V2 — B-02 split-face review (LOD0)")
    md.append("")
    md.append("Generated by `Tools/scripts/review_splits.py` from `BONES.json`, the LOD0 "
              "PSKX and `_split.npy`.")
    md.append("")
    md.append("**Verdict:** " + verdict)
    md.append("")
    md.append("## What a split face is")
    md.append("")
    md.append("A face is owned only when all three points have the same unique ≥ 0.5 "
              "influence. Every other face is split; 1,701 of 299,837 LOD0 faces are in that "
              "set, exactly the `_split.npy` LOD0 list. `weight` is the sum of that bone's "
              "weight over the face's three points. A non-zero margin resolves the face; a "
              "zero margin is a tie.")
    md.append("")
    md.append("## Counts")
    md.append("")
    md.append("| fact | value |")
    md.append("|---|---:|")
    for label, key in (("split faces", "split_faces"), ("bone sets", "bone_sets"),
                       ("pairs", "bone_pairs"), ("triples", "bone_triples"),
                       ("bone-set × slot groups", "bone_set_slot_groups"),
                       ("assigned by summed weight", "assigned_by_weight"),
                       ("ties (all 3-bone)", "ties"),
                       ("cross-part faces", "cross_part_faces"),
                       ("bones receiving an assignment", "winner_bones")):
        md.append("| %s | %s |" % (label, doc["counts"][key]))
    md.append("")
    md.append("Ties by slot: " + ", ".join("slot %s: %d" % (s, n)
                                           for s, n in sorted(tie_slot_counts.items())) + ".")
    md.append("")
    md.append("## By material slot")
    md.append("")
    md.append("| slot | material | faces | bone sets | ties | cross-part | top bone set |")
    md.append("|---:|---|---:|---:|---:|---:|---|")
    for r in slot_rows:
        md.append("| %d | `%s` | %d | %d | %d | %d | %s |" % (
            r["slot"], r["slot_name"], r["faces"], r["bone_sets"], r["ties"],
            r["cross_part"], " + ".join("`%s`" % x for x in r["top_set"])))
    md.append("")
    md.append("## By part pair")
    md.append("")
    md.append("| part pair | faces | bone sets | ties |")
    md.append("|---|---:|---:|---:|")
    for r in part_rows:
        md.append("| `%s` | %d | %d | %d |" % (
            r["part_pair"], r["faces"], r["bone_sets"], r["ties"]))
    md.append("")
    md.append("## Bone set × material slot")
    md.append("")
    md.append("This is the grouping B-02 needs for the cut decision. `winners` counts the "
              "faces resolved by summed weight; `ties` is the remainder.")
    md.append("")
    md.append("| bones | slot | material | faces | winners | ties | part pair | min margin | max margin |")
    md.append("|---|---:|---|---:|---|---:|---|---:|---:|")
    for r in set_slot_rows:
        win = ", ".join("`%s`:%d" % (k, v) for k, v in r["winners"].items())
        md.append("| %s | %d | `%s` | %d | %s | %d | `%s` | %.3f | %.3f |" % (
            " + ".join("`%s`" % x for x in r["bones"]), r["slot"], r["slot_name"],
            r["faces"], win or "—", r["ties"], r["part_pair"],
            r["min_margin"], r["max_margin"]))
    md.append("")
    md.append("## Bone sets")
    md.append("")
    md.append("| bones | faces | slots | winners | ties | part pair |")
    md.append("|---|---:|---|---|---:|---|")
    for r in set_rows:
        slots_txt = ", ".join("%d:%d" % (s["slot"], s["faces"]) for s in r["slots"])
        win = ", ".join("`%s`:%d" % (k, v) for k, v in r["winners"].items())
        md.append("| %s | %d | %s | %s | %d | `%s` |" % (
            " + ".join("`%s`" % x for x in r["bones"]), r["faces"], slots_txt,
            win or "—", r["ties"], r["part_pair"]))
    md.append("")
    md.append("## Ties: 31 faces, all three-bone")
    md.append("")
    md.append("Every tie has one rigid point per bone and weight 1.0/1.0/1.0, so the "
              "larger-weight rule cannot decide it. The part-level vertex vote resolves all "
              "31: 15 have three weapon vertices; 16 have two weapon vertices and one body "
              "vertex. Assign those 16 to the weapon part, not to the body, unless B-02 "
              "deliberately chooses a different tie-break.")
    md.append("")
    md.append("| bones | slot | faces | weights | vertex parts | recommended part |")
    md.append("|---|---:|---:|---|---|---|")
    for r in tie_rows:
        w = ", ".join("`%s`=%.1f" % (k, v) for k, v in r["weights"].items())
        vp = ", ".join("%s=%d" % (k, v) for k, v in r["vertex_parts"].items())
        md.append("| %s | %d | %d | %s | %s | **%s** |" % (
            " + ".join("`%s`" % x for x in r["bones"]), r["slot"], r["faces"],
            w, vp, r["recommended_part"]))
    md.append("")
    md.append("## What this means for B-02")
    md.append("")
    md.append("- The weight rule assigns **%d of %d** faces and leaves **31** ties; it is not "
              "a complete rule on its own." % (assigned, len(faces)))
    md.append("- **%d** split faces cross a part boundary: %s." % (
        cross_part, ", ".join("%s %d" % (r["part_pair"], r["faces"]) for r in part_rows
                              if "|" in r["part_pair"])))
    md.append("- The largest single seam is the missile barrel/mid pair (89 faces per side); "
              "the largest cross-part seam is body ↔ weapons (111 faces), followed by aero "
              "flaps ↔ body (96).")
    md.append("- Keep every split face once. `_split.npy` lists each face once; a per-bone "
              "file may list it several times as `kind=1` (touching), which is not ownership.")
    md.append("")
    md.append("## Checks")
    md.append("")
    md.append("| check | result |")
    md.append("|---|---|")
    for k, v in checks.items():
        md.append("| `%s` | %s |" % (k, "PASS" if v else "**FAIL**"))
    md.append("")
    md.append("`--check` re-derives both files and checks the split set against a fresh "
              "ownership pass.")
    md.append("")
    return doc, "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write SPLIT_FACES.json and .md")
    g.add_argument("--check", action="store_true", help="re-derive and compare the outputs")
    a = ap.parse_args()
    try:
        doc, md = collect()
    except (SplitError, KeyError, ValueError, OSError) as e:
        print("FAIL: %s" % e, file=sys.stderr)
        return 1

    fail = [k for k, v in doc["checks"].items() if not v]
    if fail:
        print("FAIL: checks %s" % ", ".join(fail), file=sys.stderr)
        return 1

    if a.write:
        OUT_JSON.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        OUT_MD.write_text(md + "\n", encoding="utf-8")
        print(doc["verdict"])
        print("wrote %s and %s" % (OUT_JSON, OUT_MD))
        return 0

    if not OUT_JSON.exists() or not OUT_MD.exists():
        print("FAIL: outputs missing; run --write", file=sys.stderr)
        return 1
    old = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    if json.dumps(old, sort_keys=True) != json.dumps(doc, sort_keys=True):
        print("FAIL: SPLIT_FACES.json differs from the re-derived record", file=sys.stderr)
        return 1
    if OUT_MD.read_text(encoding="utf-8").rstrip("\n") != md.rstrip("\n"):
        print("FAIL: SPLIT_FACES.md differs from the re-derived record", file=sys.stderr)
        return 1
    print("PASS: %s" % doc["verdict"])
    for k, v in doc["checks"].items():
        print("  %-42s %s" % (k, "PASS" if v else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
