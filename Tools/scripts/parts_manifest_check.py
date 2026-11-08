"""parts_manifest_check.py - re-derive every B-02 `parts_manifest.json` check from the files.

Why this exists (independent review `tmp/freebuff/reports/review-B-02.md`, issue 2): `bat_assemble.py
--parts` writes eleven booleans into the manifest's `checks` block once, and `silhouette_check.py`
only *fails if one of them is false* - nothing recomputes `model_budget_green`, `ties_31`,
`pivots_finite` or `five_lods_each`. A stale or hand-edited manifest would pass the gate.

Issue 4 is the same hole from the other side: the build stores part vertices as `Vw - pivot` and the
silhouette check adds `pivot_m` back from the same manifest, so a wrong pivot cancels and the
coverage number cannot see it. Here each pivot is re-derived from `BONES.json`'s bind pose through
the one transform (`bat_assemble.pivot_point`) and compared with the manifest, so the pivot is
proven against the rig, not against itself.

Nothing is written. Exit 0 = every check re-derived and green, 1 = a check failed.

    python Tools/scripts/parts_manifest_check.py --check
    python Tools/scripts/parts_manifest_check.py --check --manifest <parts_manifest.json>
    python Tools/scripts/parts_manifest_check.py --check --tamper model_kb   # must FAIL

`--tamper` corrupts one field in memory and requires the matching assertion to fail: it proves the
check is not vacuous.
"""
import argparse
import collections
import copy
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import psk2rbm as P          # noqa: E402
import pskx_parts as PX      # noqa: E402
import rbm_geom as R         # noqa: E402
import preview_rbm as PR     # noqa: E402
import bat_assemble as B     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_MANIFEST = os.path.join(ROOT, "Working", "Appearance", "build_parts",
                                "parts_manifest.json")
# the same source-face count `silhouette_check.py` asserts and bat_assemble.py checks (215_893)
BODY_FACES = 215_893
PIVOT_TOL = 1e-5        # manifest pivots are rounded to 6 dp
KB_TOL = 0.15           # manifest model_kb is rounded to 1 dp
MODEL_HARD_KB = 4915.0  # R9 wall, GRAB_BACKLOG.md section 0.5

TAMPERS = {
    "model_kb": "model budget",
    "pivot": "pivots from BONES.json",
    "faces": "RBM triangle counts",
    "ties": "split re-derived from the source",
    "lods": "five LODs per entry",
}


def log(res, name, ok, detail=""):
    res.append((name, bool(ok), detail))


def load_context(man_path):
    man = json.load(open(man_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(man_path))
    return man, base


def check_spec_gate(res, man):
    """The `--parts` spec the manifest names must still load through bat_assemble's own gate."""
    path = os.path.join(ROOT, man["parts_spec"])
    try:
        spec = B.load_part_spec(path)
    except SystemExit as e:
        log(res, "parts spec loads through bat_assemble's gate", False, str(e))
        return None
    names = [p["name"] for p in spec["parts"]]
    want = [n for n in man["silhouette_parts"] if n != "body"]
    log(res, "parts spec loads through bat_assemble's gate",
        names == want, "%s: schema %s, %d parts" % (man["parts_spec"], spec.get("schema"),
                                                    len(names)))
    return spec


def check_meshes(res, man, base):
    """Every LOD file exists, decodes, and holds the triangles / vertices / blocks claimed."""
    bad_lod, bad_tri, bad_vert, bad_blk, nfiles = [], [], [], [], 0
    for e in man["entries"]:
        if len(e["faces_per_lod"]) != 5 or len(e["lod_files"]) != 5:
            bad_lod.append(e["name"])
            continue
        for i, fn in enumerate(e["lod_files"]):
            p = os.path.join(base, fn)
            if not os.path.exists(p):
                nfiles += 1
                bad_tri.append("%s missing" % fn)
                continue
            blocks = R.decode(open(p, "rb").read()).blocks
            tris = sum(len(PR.block_triangles(b)) for b in blocks)
            verts = sum(int(b.vb0.count) for b in blocks)
            if tris != e["faces_per_lod"][i]:
                bad_tri.append("%s %d != %d" % (fn, tris, e["faces_per_lod"][i]))
            if verts != e["vertices_per_lod"][i]:
                bad_vert.append("%s %d != %d" % (fn, verts, e["vertices_per_lod"][i]))
            if len(blocks) != e["blocks_per_lod"][i]:
                bad_blk.append("%s %d != %d" % (fn, len(blocks), e["blocks_per_lod"][i]))
    total = sum(len(e["lod_files"]) for e in man["entries"])
    log(res, "five LODs per entry", not bad_lod,
        "%d entries x 5 LODs%s" % (len(man["entries"]),
                                   "" if not bad_lod else "; " + ", ".join(bad_lod)))
    log(res, "every LOD file present", not nfiles,
        "%d of %d files on disk" % (total - nfiles, total)
        + ("" if not nfiles else "; " + ", ".join(bad_tri)))
    log(res, "RBM triangle counts", not bad_tri,
        "%d of %d files match faces_per_lod" % (total - len(bad_tri), total)
        + ("" if not bad_tri else "; " + ", ".join(bad_tri[:4])))
    log(res, "RBM vertex counts", not bad_vert,
        "%d of %d files match vertices_per_lod" % (total - len(bad_vert), total)
        + ("" if not bad_vert else "; " + ", ".join(bad_vert[:4])))
    log(res, "RBM block counts", not bad_blk,
        "%d of %d files match blocks_per_lod" % (total - len(bad_blk), total)
        + ("" if not bad_blk else "; " + ", ".join(bad_blk[:4])))


def check_pivots(res, man, base):
    """Each pivot re-derived from BONES.json bind (parts) / stations.json hardpoint (wheels)."""
    bdoc = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab", "BONES.json"),
                          encoding="utf-8"))
    bones = {b["name"]: b for b in bdoc["bones"]}
    stations = json.load(open(os.path.join(base, "stations.json"), encoding="utf-8"))
    scale = float(man["scale"])
    off = np.asarray(man["offset"], np.float64)
    worst, bad = 0.0, []
    for e in man["entries"]:
        got = np.asarray(e["pivot_m"], np.float64)
        if e["kind"] == "body":
            want, src = np.zeros(3), "zero"
        elif e["kind"] == "wheel":
            c = stations["corners"][e["name"][len("wheel_"):]]
            want, src = np.asarray(c["hardpoint"], np.float64), "stations.json hardpoint"
            if c["tyre_bone"] != e["pivot_bone"]:
                bad.append("%s tyre_bone %s != %s" % (e["name"], e["pivot_bone"],
                                                      c["tyre_bone"]))
        else:
            bone = bones.get(e["pivot_bone"])
            if bone is None:
                bad.append("%s pivot_bone %s not in BONES.json" % (e["name"], e["pivot_bone"]))
                continue
            want = B.pivot_point(bone["bind"]["world_position_cm"], scale, off)
            src = "BONES.json bind"
        d = float(np.max(np.abs(got - want)))
        worst = max(worst, d)
        if d > PIVOT_TOL:
            bad.append("%s %.6f m (%s)" % (e["name"], d, src))
    log(res, "pivots from BONES.json", not bad,
        "%d entries, max delta %.2e m (tol %.0e)%s"
        % (len(man["entries"]), worst, PIVOT_TOL, "" if not bad else "; " + ", ".join(bad)))


def check_transform_and_budget(res, man, base):
    """scale/offset against build.log's own transform line, and both R9 numbers from the files."""
    log_path = os.path.join(base, "build.log")
    if os.path.exists(log_path):
        txt = open(log_path, encoding="utf-8", errors="replace").read()
        m = re.search(r"transform: scale ([0-9.]+)\s+offset \[([^\]]+)\]", txt)
        ok, det = False, "no transform line in build.log"
        if m:
            sc = float(m.group(1))
            ol = [float(x) for x in m.group(2).split(",")]
            d = max([abs(sc - float(man["scale"]))] +
                    [abs(a - b) for a, b in zip(ol, man["offset"])])
            ok = d <= 5e-4          # build.log rounds the offset to 4 dp
            det = "scale %g offset %s, max delta %.1e (log rounds to 4 dp)" % (sc, ol, d)
        log(res, "transform matches build.log", ok, det)
    else:
        log(res, "transform matches build.log", True, "build.log absent, not checked")

    kb = sum(os.path.getsize(os.path.join(base, e["lod_files"][i]))
             for e in man["entries"] for i in range(len(e["lod_files"]))) / 1024
    rec = man["budget"]
    log(res, "model budget", abs(kb - float(rec["model_kb"])) <= KB_TOL
        and kb <= float(rec["cap_kb"]) and float(rec["cap_kb"]) <= MODEL_HARD_KB,
        "%.1f KB measured, manifest %.1f KB, cap %.1f KB (R9 wall %.0f KB)"
        % (kb, float(rec["model_kb"]), float(rec["cap_kb"]), MODEL_HARD_KB))


def split_from_source(man):
    """Re-run the cut from the PSKX with bat_assemble's own classification + assign_parts."""
    pskx = os.path.join(ROOT, man["source"])
    spec = B.load_part_spec(os.path.join(ROOT, man["parts_spec"]))
    # bone list comes from the PSKX REFSKELT, exactly as bat_assemble.main() reads it
    Pp, W, F, _mats = P.read_pskx(pskx)
    bones, Wt = PX.skeleton(pskx)
    bdoc = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab", "BONES.json"),
                          encoding="utf-8"))
    if [b["name"] for b in bdoc["bones"]] != [b[0] for b in bones]:
        raise SystemExit("BONES.json bone order differs from the PSKX REFSKELT")
    part_of = B.part_bone_map(bones, spec)
    fb = PX.face_bones(Pp, W, F, Wt, len(bones))
    Vw = B.to_jc3_rot(Pp[W["p"]]) * float(man["scale"])
    tris = F["w"].astype(np.int64)

    cl = PX.classify(Vw, tris, fb, len(bones))
    round_b = [b for b, (k, _n, _i) in cl.items() if k == "spinning"]
    size = lambda b: max(cl[b][2][3], cl[b][2][4])
    nwheels = sum(1 for e in man["entries"] if e["kind"] == "wheel")
    anchors = sorted(round_b, key=size, reverse=True)[:nwheels]
    if len(anchors) != nwheels:
        raise SystemExit("found %d round parts for %d wheels" % (len(anchors), nwheels))
    cz = np.median([cl[b][2][0][2] for b in anchors])
    corner = {b: ("f" if cl[b][2][0][2] < cz else "r") + "_" + ("l" if cl[b][2][0][0] < 0 else "r")
              for b in anchors}
    wheel_of = dict(corner)
    for b in round_b:
        if b in wheel_of:
            continue
        c = cl[b][2][0]
        for ab in anchors:
            ac, r = cl[ab][2][0], size(ab) / 2
            if np.sign(c[0]) == np.sign(ac[0]) and np.linalg.norm(c[1:] - ac[1:]) < r \
                    and size(b) <= 2 * r:
                wheel_of[b] = corner[ab]
    face_part = np.array(["body"] * len(F), dtype=object)
    for b, c in wheel_of.items():
        face_part[fb == b] = "wheel_" + c
    hubs = {}
    for c in B.CORNERS:
        bs = [b for b, cc in wheel_of.items() if cc == c
              and size(b) >= 0.8 * max(size(x) for x in anchors)]
        tb = min(bs, key=lambda b: cl[b][2][2])
        pts = Vw[np.unique(tris[fb == tb])]
        lo, hi = pts.min(0), pts.max(0)
        hubs[c] = ((lo + hi) / 2, (hi[1] - lo[1]) / 2)
    cen = Vw[tris].mean(1)
    for c in B.CORNERS:
        rad = np.linalg.norm(cen[:, 1:] - hubs[c][0][1:], axis=1)
        out = (face_part == "wheel_" + c) & (rad > 1.03 * hubs[c][1])
        face_part[out] = "body"
    stats = B.assign_parts(face_part, W, F, Wt, bones, part_of)
    counts = collections.Counter(face_part)
    return stats, counts, len(F)


def check_split(res, man):
    try:
        stats, counts, nfaces = split_from_source(man)
    except SystemExit as e:
        log(res, "split re-derived from the source", False, str(e))
        return
    rec = man["split"]
    diffs = [k for k, v in rec.items() if stats.get(k) != v]
    log(res, "split re-derived from the source", not diffs,
        "%d body faces -> %d body + %d parts; split %d body / %d unique / %d weight, "
        "ties %d %s, unresolved %d"
        % (stats["body_faces"], counts["body"], stats["body_faces"] - counts["body"],
           stats["split_faces_body"], stats["part_unique"], stats["weight_resolved"],
           stats["ties"], dict(sorted(stats["ties_by_part"].items())), stats["unresolved"])
        + ("" if not diffs else "; differs: " + ", ".join(diffs)))
    log(res, "ties resolve to weapons only", rec.get("ties") == stats["ties"] == 31
        and all(k.startswith("batmobile_missile_pod") or k == "batmobile_riot_suppressor"
                for k in stats["ties_by_part"]),
        "%d ties -> %s" % (stats["ties"], dict(sorted(stats["ties_by_part"].items()))))
    bad = [e["name"] for e in man["entries"]
           if counts[e["name"]] != e["faces_lod0"]]
    log(res, "per-part LOD0 faces", not bad,
        "%d entries match the re-derived cut%s"
        % (len(man["entries"]), "" if not bad else "; " + ", ".join(bad)))
    log(res, "all faces accounted", sum(e["faces_lod0"] for e in man["entries"]) == nfaces
        and stats["body_faces"] == BODY_FACES,
        "%d faces in the source, body %s (expected %d)"
        % (nfaces, stats["body_faces"], BODY_FACES))


def run(man, base, skip_split=False):
    res = []
    bad_block = [k for k, v in (man.get("checks") or {}).items() if not v]
    log(res, "manifest checks block all true", not bad_block,
        "%d recorded checks%s" % (len(man.get("checks") or {}),
                                  "" if not bad_block else "; false: " + ", ".join(bad_block)))
    check_spec_gate(res, man)
    check_meshes(res, man, base)
    check_pivots(res, man, base)
    check_transform_and_budget(res, man, base)
    if not skip_split:
        check_split(res, man)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="re-derive and compare (always on)")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--tamper", choices=sorted(TAMPERS),
                    help="corrupt one field in memory; the named check must FAIL")
    a = ap.parse_args()

    man, base = load_context(a.manifest)
    if a.tamper:
        man = copy.deepcopy(man)
        if a.tamper == "model_kb":
            man["budget"]["model_kb"] = float(man["budget"]["model_kb"]) - 500.0
        elif a.tamper == "pivot":
            p = next(e for e in man["entries"] if e["kind"] == "part")
            p["pivot_m"][0] = round(p["pivot_m"][0] + 0.05, 6)
        elif a.tamper == "faces":
            p = next(e for e in man["entries"] if e["kind"] == "part")
            p["faces_per_lod"][0] += 7
        elif a.tamper == "ties":
            man["split"]["ties"] += 1
        elif a.tamper == "lods":
            p = next(e for e in man["entries"] if e["kind"] == "part")
            p["faces_per_lod"] = p["faces_per_lod"][:4]

    res = run(man, base, skip_split=(a.tamper == "faces"))
    for name, ok, detail in res:
        print("  %-4s %-44s %s" % ("PASS" if ok else "FAIL", name, detail))
    failed = [n for n, ok, _ in res if not ok]

    if a.tamper:
        want = TAMPERS[a.tamper]
        hit = any(n == want and not ok for n, ok, _ in res)
        print(("TAMPER %s: %s -> %s" % (a.tamper, want,
                                        "CAUGHT" if hit else "MISSED (check is vacuous)")))
        return 0 if hit else 1
    if failed:
        print("FAIL: %d of %d checks disagree with the files: %s"
              % (len(failed), len(res), ", ".join(failed)))
        return 1
    print("PASS: %s re-derived from the files (%d assertions)"
          % (os.path.relpath(a.manifest, ROOT), len(res)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
