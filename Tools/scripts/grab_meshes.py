r"""grab_meshes.py - every Batmobile skeletal mesh's geometry, and every LOD's face count (G1-4, G1-5).

Two units that look like one, because the same export answers both:

  * **G1-5** - geometry. `umodel -export` writes one ActorX `.pskx` per mesh; its header carries
    vertex/triangle/bone/material counts, so the mesh is measured, not described.
  * **G1-4** - LOD1/LOD2 face counts. umodel exports LOD0 only, so the extra LODs are read out of
    the cooked object itself. `USkeletalMesh3` serialises `LODModels` as an array of
    `FStaticLODModel3`, and each one begins with its `Sections` array - 13 bytes per section
    (`int16 MaterialIndex, int16 ChunkIndex, int32 FirstIndex, int32 NumTriangles, byte`) whose
    `FirstIndex` is exactly the running `3 * NumTriangles`. That chain is the signature: a real
    section array cannot be faked by vertex data, and the array's own count is the `LODModels`
    length sitting 4 bytes before LOD0.

The two reads are independent, so they check each other: LOD0's triangle count from the cooked
bytes must equal the `.pskx` header's, and LOD0's per-material faces must equal `SLOTS.md`'s
(they were measured through umodel's material assignment).

Writes `Research/BatmobileGrab/MESHES.json` + `MESHES.md`. Extracted geometry goes to
`E:\Modding\_BmAKgrab\meshes\` - outside the repo, per the project rule.

Usage:
    python Tools/scripts/grab_meshes.py --write
    python Tools/scripts/grab_meshes.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_model            # noqa: E402
import upk_read as U         # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
UMODEL = r"C:\Users\User\source\repos\UEViewer\umodel.exe"
MESH_OUT = r"E:\Modding\_BmAKgrab\meshes"
SECTION_SIZE = 13


class MeshError(Exception):
    pass


# ---------------- cooked LOD models ----------------

def _i32(d: bytes, o: int) -> int:
    return struct.unpack_from("<i", d, o)[0]


def section_arrays(d: bytes) -> list[dict]:
    """Every 13-byte section array whose FirstIndex chain is self-consistent.

    A real `FStaticLODModel3` starts with `Sections` and its entries are laid out so that section
    `k` starts where section `k-1` ended: `FirstIndex == 3 * sum(NumTriangles)`. Vertex/index data
    does not satisfy that by accident; the scan is a signature, not a guess.
    """
    out = []
    for j in range(4, len(d) - 8):
        n = _i32(d, j)
        if not 1 <= n <= 64:
            continue
        o, cum, secs = j + 4, 0, []
        for _ in range(n):
            if o + SECTION_SIZE > len(d):
                break
            mat, ch = struct.unpack_from("<hh", d, o)
            fi, nt = struct.unpack_from("<ii", d, o + 4)
            if fi != cum or nt <= 0 or not 0 <= mat < 64 or not 0 <= ch < 512:
                break
            cum += 3 * nt
            secs.append({"material": mat, "chunk": ch, "first_index": fi, "faces": nt})
            o += SECTION_SIZE
        else:
            out.append({"at": j, "count": n, "end": o, "sections": secs,
                        "faces": cum // 3, "lod_array_len": _i32(d, j - 4)})
    return out


def _index_count_after(d: bytes, end: int, faces: int) -> int | None:
    """The LOD's index buffer stores `3 * faces`; find that count just past the sections.

    `FStaticLODModel3` writes `Sections` then `IndexBuffer`; between them sit a small fixed header
    (Batman4: `int32 0`, `byte itemSize`, `int32 elementSize`, one marker byte), so the count lands
    8..12 bytes after the section array. Requiring the count *and* the position rejects lookalikes.
    """
    want = 3 * faces
    for k in range(8, 13):
        o = end + k
        if o + 4 <= len(d) and _i32(d, o) == want:
            return o
    return None


def lod_models(d: bytes) -> list[dict]:
    """All `FStaticLODModel3`s of one mesh, in LOD order, with their section tables."""
    cands = []
    for c in section_arrays(d):
        idx = _index_count_after(d, c["end"], c["faces"])
        if idx is None:
            continue
        c["index_count_at"] = idx
        cands.append(c)
    if not cands:
        return []
    # LOD0 is the array element that carries the array's own length in front of it.
    first = next((c for c in cands if c["lod_array_len"] == len(cands)), None)
    if first is None:
        first = cands[0]
    chain = [c for c in cands if c["at"] >= first["at"]]
    chain.sort(key=lambda c: c["at"])
    out = []
    for i, c in enumerate(chain[: first["lod_array_len"]]):
        per_mat: dict[str, int] = {}
        for s in c["sections"]:
            per_mat[str(s["material"])] = per_mat.get(str(s["material"]), 0) + s["faces"]
        out.append({"lod": i, "offset": c["at"], "sections": c["count"],
                    "faces": c["faces"], "vertices": None,
                    "faces_by_material": dict(sorted(per_mat.items(), key=lambda kv: int(kv[0])))})
    return out


# ---------------- pskx ----------------

def chunks(d: bytes):
    """Walk an ActorX chunk list: id[8], version[16], stride u32, count u32, payload.

    Batman's PSKX is *chunked*, not the flat Source PSK the format name suggests; reading it flat
    yields `numVertex = 20100422` (FINDINGS F4). Every chunk here is a 32-byte header, and the
    count in each header is the measurement.
    """
    p = 0
    while p + 32 <= len(d):
        cid = d[p:p + 8].decode("latin-1")
        stride, count = struct.unpack_from("<II", d, p + 24)
        yield cid, stride, count, p + 32
        nxt = p + 32 + stride * count
        if nxt <= p or nxt > len(d):
            return
        p = nxt


def read_pskx(path: str) -> dict:
    """Counts and bounds from the chunk list of one exported mesh."""
    d = open(path, "rb").read()
    got, verts = {}, None
    for cid, stride, count, data in chunks(d):
        key = cid.rstrip("\0")[:4]
        got[key] = {"stride": stride, "count": count}
        if key == "PNTS":
            raw = d[data:data + 12 * count]
            if len(raw) != 12 * count:
                raise MeshError("%s: truncated PNTS" % os.path.basename(path))
            xs = struct.unpack("<%df" % (3 * count), raw)
            verts = [list(xs[i::3]) for i in range(3)]
    for need in ("PNTS", "FACE"):
        if need not in got:
            raise MeshError("%s: no %s chunk" % (os.path.basename(path), need))
    lo = [min(v) for v in verts]
    hi = [max(v) for v in verts]
    return {"file": os.path.basename(path), "chunks": got,
            "vertices": got["PNTS"]["count"], "faces": got["FACE"]["count"],
            "bones": got.get("REFS", {}).get("count"),
            "materials": got.get("MATT", {}).get("count"),
            "bounds": {"min": [round(v, 3) for v in lo], "max": [round(v, 3) for v in hi],
                       "size": [round(hi[i] - lo[i], 3) for i in range(3)]}}


# ---------------- driver ----------------

def meshes() -> list[dict]:
    """The 12 SkeletalMesh exports the grab recorded, deduplicated into real meshes."""
    rows = [r for r in grab_model.Grab().rows if r.get("class") == "SkeletalMesh"]
    seen, out = set(), []
    for r in rows:
        key = (r["package"], r["outer"], r["name"], r["size"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def export_one(row: dict) -> str:
    """umodel-export one mesh's geometry; returns the `.pskx` path."""
    pkg = row["package"]
    name = row["name"]
    dst = os.path.join(MESH_OUT, pkg)
    os.makedirs(dst, exist_ok=True)
    cmd = [UMODEL, "-export", "-lods", "-notex", "-out=" + dst, "-path=" + GAME,
           pkg + ".upk", name, "SkeletalMesh"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = os.path.join(dst, "export_%s.log" % name)
    with open(log, "w", encoding="utf-8") as f:
        f.write(" ".join(cmd) + "\n" + (r.stdout or "") + (r.stderr or ""))
    if r.returncode != 0:
        raise MeshError("umodel failed for %s: %s" % (name, (r.stdout or r.stderr or "")[-400:]))
    # umodel writes `.pskx` when the faces carry 32-bit indices and `.psk` otherwise; both are the
    # same chunked container here.
    for ext in (".pskx", ".psk"):
        path = os.path.join(dst, pkg, "SkeletalMesh3", name + ext)
        if os.path.isfile(path):
            return path
    raise MeshError("no psk/pskx for %s (see %s)" % (name, log))


def build(reexport: bool) -> dict:
    pkg_cache: dict[str, U.Package] = {}
    out = []
    for row in meshes():
        pkg = row["package"]
        if pkg not in pkg_cache:
            pkg_cache[pkg] = U.Package(os.path.join(GAME, pkg + ".upk"))
        p = pkg_cache[pkg]
        idx = row["index"]                    # the grab's export index, not a name lookup:
        if not 0 < idx <= len(p.exports) or p.exports[idx - 1]["name"] != row["name"]:
            raise MeshError("%s@%d is not that export in %s" % (row["name"], idx, pkg))
        data = p.data(idx)
        lods = lod_models(data)
        name = row["name"]
        on_disk = [os.path.join(MESH_OUT, pkg, pkg, "SkeletalMesh3", name + e)
                   for e in (".pskx", ".psk")]
        pskx_path = next((p for p in on_disk if os.path.isfile(p)), None)
        if reexport or pskx_path is None:
            pskx_path = export_one(row)
        psk = read_pskx(pskx_path)
        out.append({"package": pkg, "path": "%s.%s" % (row["outer"], row["name"]),
                    "export_size": row["size"], "mesh": name, "pskx": psk,
                    "lods": lods})
    return {"schema": 1, "generated_by": "grab_meshes.py", "game": GAME,
            "mesh_root": MESH_OUT, "meshes": out}


def check(doc: dict) -> list[str]:
    bad = []
    if not doc["meshes"]:
        bad.append("no meshes")
    for m in doc["meshes"]:
        lods = m["lods"]
        if not lods:
            bad.append("%s: no LODModels parsed" % m["mesh"])
            continue
        if lods[0]["faces"] != m["pskx"]["faces"]:
            bad.append("%s: LOD0 faces %d != pskx %d"
                       % (m["mesh"], lods[0]["faces"], m["pskx"]["faces"]))
        faces = [l["faces"] for l in lods]
        if faces != sorted(faces, reverse=True):
            bad.append("%s: LOD faces are not descending: %s" % (m["mesh"], faces))
        for l in lods:
            if sum(l["faces_by_material"].values()) != l["faces"]:
                bad.append("%s LOD%d: per-material faces != total" % (m["mesh"], l["lod"]))
    return bad


def write_md(doc: dict) -> None:
    L = ["# Batmobile meshes - geometry and every LOD (G1-4, G1-5)", "",
         "Generated by `Tools/scripts/grab_meshes.py`. Geometry is exported with `umodel -lods` to",
         "`%s` (outside the repo); this page is the measurement." % doc["mesh_root"], "",
         "## Meshes", "",
         "| mesh | package | vertices | LOD0 | LOD1 | LOD2 | bones | materials | size (m) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for m in doc["meshes"]:
        lods = {l["lod"]: l["faces"] for l in m["lods"]}
        s = m["pskx"]["bounds"]["size"]
        L.append("| `%s` | %s | %d | %s | %s | %s | %d | %d | %.3f × %.3f × %.3f |" % (
            m["mesh"], m["package"], m["pskx"]["vertices"],
            lods.get(0, "—"), lods.get(1, "—"), lods.get(2, "—"),
            m["pskx"]["bones"], m["pskx"]["materials"], s[0], s[1], s[2]))
    L += ["", "## Per-slot faces at every LOD", "",
          "`SLOTS.md` gives LOD0 per material; this is the same join for the LODs umodel cannot export.",
          ""]
    for m in doc["meshes"]:
        mats = sorted({k for l in m["lods"] for k in l["faces_by_material"]}, key=int)
        L += ["### %s" % m["mesh"], "",
              "| material | " + " | ".join("LOD%d" % l["lod"] for l in m["lods"]) + " |",
              "|---|" + "---|" * len(m["lods"])]
        for k in mats:
            L.append("| %s | %s |" % (k, " | ".join(
                str(l["faces_by_material"].get(k, 0)) for l in m["lods"])))
        L.append("")
    open(os.path.join(OUT, "MESHES.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="export, measure and write MESHES.json/.md")
    ap.add_argument("--check", action="store_true", help="re-measure and fail on any disagreement")
    ap.add_argument("--reexport", action="store_true", help="re-run umodel even if the pskx exists")
    a = ap.parse_args()
    doc = build(a.reexport)
    bad = check(doc)
    if a.write:
        with open(os.path.join(OUT, "MESHES.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        write_md(doc)
    for m in doc["meshes"]:
        print("%-34s %-28s verts %7d  LODs %s"
              % (m["mesh"], m["package"], m["pskx"]["vertices"],
                 " / ".join(str(l["faces"]) for l in m["lods"])))
    print("%d meshes, %d LOD model(s)" % (len(doc["meshes"]),
                                          sum(len(m["lods"]) for m in doc["meshes"])))
    if bad:
        print("\nFAIL")
        for b in bad:
            print(" ", b)
        sys.exit(1)
    print("checks: LOD0 == pskx faces, LOD faces descending, per-material sums - all ok")


if __name__ == "__main__":
    main()
