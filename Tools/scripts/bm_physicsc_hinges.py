"""bm_physicsc_hinges.py - append the two Batmobile hinges to a COPY of the physicsc.

`Working/Collision/batmobile.physicsc` holds 11 constraint objects (indices 0..10), so the
parts module's `constraint_index` 11 / 12 name nothing.  This script copies the file to
`Working/Collision/batmobile_hinged.physicsc` and appends two 304-byte
`hkpLimitedHingeConstraintData` objects taken from the donor medium tank's turret and cannon
hinges, with axis / pivot / limits replaced by the Batmobile values in
`Working/Parts/JOINT_FIELDS.md` §3:

    P-01 turret  axis (0,1,0)  pivot (0.000013, 0.876249, 0.333226)  -1.047198 .. 1.047198 rad
    P-02 cannon  axis (1,0,0)  pivot (0.000358, 1.702446, 0.017586)  -0.087266 .. 0.349066 rad

The data section is re-laid out from per-object blobs with the existing local / global /
virtual fixups remapped, the virtual table grown by two entries, and the `__data__` record
rewritten - the mechanism `jc3hkx.packfile_bytes` proved (`PHYSICS_WRITE.md` §4, the 16-byte
insert), extended here to a *new* object rather than a resized one.

Never writes the original and never touches a Builds tree.

  python Tools/scripts/bm_physicsc_hinges.py --write
  python Tools/scripts/bm_physicsc_hinges.py --check
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from jc3hkx import Packfile, check_file, CLASSNAME_MARKER  # noqa: E402
from jc3index import DEFAULT_GAME, DEFAULT_OUT, load_index  # noqa: E402
import jc3hkx  # noqa: E402

SRC = os.path.join(ROOT, "Working", "Collision", "batmobile.physicsc")
OUT = os.path.join(ROOT, "Working", "Collision", "batmobile_hinged.physicsc")
DONOR_EE = ("editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/"
            "v0201_car_capstone_mediumtank_debug.ee")
HINGE = "hkpLimitedHingeConstraintData"
HINGE_EXT = 304
AXIS, PIVOT, MIN, MAX = 0x30, 0x60, 0xFC, 0x100

P01 = {"id": "P-01", "part": "batmobile_turret", "index": 11,
       "axis": (0.0, 1.0, 0.0), "pivot": (0.000013, 0.876249, 0.333226),
       "min": -1.047198, "max": 1.047198, "donor_index": 2}
P02 = {"id": "P-02", "part": "batmobile_cannon", "index": 12,
       "axis": (1.0, 0.0, 0.0), "pivot": (0.000358, 1.702446, 0.017586),
       "min": -0.087266, "max": 0.349066, "donor_index": 0}


def donor_physicsc() -> tuple[str, bytes]:
    rows = load_index(DEFAULT_OUT)
    files = jc3hkx.physicsc_of(DONOR_EE, rows, DEFAULT_GAME)
    if not files:
        raise SystemExit("donor entity yielded no .physicsc")
    return files[0]


def constraints(pf: Packfile) -> list:
    return sorted([o for o in pf.objects if "Constraint" in o.cls], key=lambda o: o.offset)


def patched(blob: bytes, row: dict) -> bytes:
    out = bytearray(blob)
    struct.pack_into("<4f", out, AXIS, *row["axis"], 0.0)
    struct.pack_into("<4f", out, PIVOT, *row["pivot"], 0.0)
    struct.pack_into("<f", out, MIN, row["min"])
    struct.pack_into("<f", out, MAX, row["max"])
    return bytes(out)


def append_objects(blob: bytes, new: list[tuple[str, bytes]]) -> tuple[bytes, dict]:
    """Lay the data section out again with `new` objects appended; remap every fixup."""
    pf = Packfile(blob)
    objs = sorted(pf._order)
    raw = {o: pf.blob[pf.base + o:pf.base + o + pf.extents[o]] for o in objs}
    at, pos = {}, 0
    for o in objs:
        at[o] = pos
        pos += len(raw[o])
    added = []
    for cls, b in new:
        if len(b) % 16:
            b = b + b"\x7f" * (16 - len(b) % 16)
        added.append((cls, pos, b))
        pos += len(b)
    lf_new = pos
    local_size, global_size = pf.gf - pf.lf, pf.vf - pf.gf
    virt_size = 12 * (len(pf.virtual) + len(added))
    data = bytearray(lf_new + local_size + global_size + virt_size)
    gf_new, vf_new, ex_new = lf_new + local_size, lf_new + local_size + global_size, len(data)
    data[lf_new:ex_new] = b"\xff" * (ex_new - lf_new)
    for o in objs:
        data[at[o]:at[o] + len(raw[o])] = raw[o]
    for _cls, off, b in added:
        data[off:off + len(b)] = b

    def remap(rel: int) -> int:
        if rel in at:
            return at[rel]
        i = bisect.bisect_right(objs, rel) - 1
        if i < 0 or rel >= objs[i] + pf.extents[objs[i]]:
            raise ValueError(f"fixup target {rel:#x} is outside every object")
        return at[objs[i]] + (rel - objs[i])

    for slot in range(0, local_size, 8):
        f, t = struct.unpack_from("<2I", pf.blob, pf.base + pf.lf + slot)
        if f == 0xFFFFFFFF or t == 0xFFFFFFFF:
            continue
        struct.pack_into("<2I", data, lf_new + slot, remap(f), remap(t))
    for slot in range(0, global_size, 12):
        f, sec, t = struct.unpack_from("<3I", pf.blob, pf.base + pf.gf + slot)
        if f == 0xFFFFFFFF or t == 0xFFFFFFFF:
            continue
        struct.pack_into("<3I", data, gf_new + slot, remap(f), sec, remap(t))
    cls_off = {nm: rel for rel, _h, nm in pf.classnames}
    entries = [(remap(o), 0, cls_off[c]) for o, c in pf.virtual]
    entries += [(off, 0, cls_off[c]) for c, off, _b in added]
    for i, ent in enumerate(entries):
        struct.pack_into("<3I", data, vf_new + 12 * i, *ent)

    out = bytearray(pf.blob[:pf.base])
    idx = [s.name for s in pf.section_list].index("__data__")
    struct.pack_into("<7I", out, 0x40 + 0x40 * idx + 20,
                     pf.base, lf_new, gf_new, vf_new, ex_new, ex_new, ex_new)
    out += data
    return bytes(out), {"objects": len(objs) + len(added), "lf": lf_new,
                        "size": len(out), "new": [(c, o) for c, o, _b in added]}


def build() -> dict:
    src = open(SRC, "rb").read()
    name, donor = donor_physicsc()
    dpf = Packfile(donor)
    dcons = constraints(dpf)
    if len(dcons) < 3:
        raise SystemExit(f"donor has {len(dcons)} constraints")
    # A copied blob must be pointer-free: its internal offsets belong to the donor file.
    for di in (P01["donor_index"], P02["donor_index"]):
        o = dcons[di].offset
        for f, _t in dpf.local:
            if o <= f < o + HINGE_EXT:
                raise SystemExit(f"donor hinge {di} has a local fixup inside it")
        for f, _s, _t in dpf.global_:
            if o <= f < o + HINGE_EXT:
                raise SystemExit(f"donor hinge {di} has a global fixup inside it")
    blobs = {r["id"]: patched(dpf.blob[dpf.base + dcons[r["donor_index"]].offset:
                                       dpf.base + dcons[r["donor_index"]].offset + HINGE_EXT], r)
             for r in (P01, P02)}
    out, info = append_objects(src, [(HINGE, blobs["P-01"]), (HINGE, blobs["P-02"])])
    return {"src": src, "out": out, "info": info, "donor": (name, donor, dpf, dcons),
            "blobs": blobs}


def verify(doc: dict) -> tuple[dict, list[str]]:
    bad: list[str] = []
    src, out = Packfile(doc["src"]), Packfile(doc["out"])
    cons = constraints(out)
    if len(cons) != 13:
        bad.append(f"constraint objects {len(cons)}, expected 13")
    for i, r in ((11, P01), (12, P02)):
        if i >= len(cons):
            bad.append(f"no constraint at index {i}")
            continue
        o = cons[i]
        if o.cls != HINGE:
            bad.append(f"index {i}: {o.cls}")
            continue
        axis = out.vec4(o.offset + AXIS)
        pivot = out.vec4(o.offset + PIVOT)
        lo, hi = out.f32(o.offset + MIN), out.f32(o.offset + MAX)
        for label, got, want in (("axis", axis[:3], r["axis"]),
                                 ("pivot", pivot[:3], r["pivot"]),
                                 ("min", (lo,), (r["min"],)), ("max", (hi,), (r["max"],))):
            if any(abs(a - b) > 1e-5 for a, b in zip(got, want)):
                bad.append(f"index {i} {label} {got} != {want}")
        if any(abs(a - b) > 1e-5 for a, b in zip(axis[:3], r["axis"])):
            bad.append(f"index {i} axis mismatch")
    if len(cons) >= 13 and [o.cls for o in cons[:11]] != [o.cls for o in constraints(src)]:
        bad.append("the 11 original constraint classes changed")
    # every original object, byte for byte, at its new offset
    old = {o: out.blob[out.base + c.offset:out.base + c.offset + out.extents[c.offset]]
           for o, c in zip(sorted(src._order), constraints(src))}
    new = {o: out.blob[out.base + c.offset:out.base + c.offset + out.extents[c.offset]]
           for o, c in zip(sorted(src._order), constraints(src))}
    if old != new:
        bad.append("an original constraint object changed")
    # the physics system data (body entries / stations) must be untouched
    a = [src.blob[src.base + o:src.base + o + src.extents[o]]
         for o in src._order if src._starts[o] == "hknpPhysicsSystemData"]
    b = [out.blob[out.base + o:out.base + o + out.extents[o]]
         for o in out._order if out._starts[o] == "hknpPhysicsSystemData"]
    if a != b:
        bad.append("hknpPhysicsSystemData bytes changed")
    info, problems = check_file(OUT if os.path.exists(OUT) else SRC)
    bad.extend(problems)
    if out.virtual_residue or out.classname_marker_bad:
        bad.append(f"table residue {out.virtual_residue} / markers {out.classname_marker_bad}")
    rows = []
    for i, r in ((11, P01), (12, P02)):
        o = cons[i]
        rows.append({"index": i, "id": r["id"], "part": r["part"], "class": o.cls,
                     "offset": o.offset, "extent": out.extents[o.offset],
                     "axis": [round(x, 6) for x in out.vec4(o.offset + AXIS)[:3]],
                     "pivot": [round(x, 6) for x in out.vec4(o.offset + PIVOT)[:3]],
                     "min": round(out.f32(o.offset + MIN), 6),
                     "max": round(out.f32(o.offset + MAX), 6)})
    return {"constraints": len(cons), "objects": len(out.objects), "rows": rows,
            "check": info, "orig_identical": old == new,
            "system_data_identical": a == b}, bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    doc = build()
    if a.write:
        with open(OUT, "wb") as f:
            f.write(doc["out"])
        vi, bad = verify(doc)
        print(f"wrote {os.path.relpath(OUT, ROOT)}: {len(doc['src']):,} -> "
              f"{len(doc['out']):,} B, objects {len(Packfile(doc['src']).objects)} -> "
              f"{vi['objects']}, constraints 11 -> {vi['constraints']}")
        for r in vi["rows"]:
            print(f"  index {r['index']} {r['id']} {r['part']:18s} axis {r['axis']} "
                  f"pivot {r['pivot']} limits {r['min']} .. {r['max']}")
        if bad:
            for p in bad:
                print("FAIL", p)
            return 1
        print("ok: appended objects re-read clean")
        return 0
    have = open(OUT, "rb").read()
    if have != doc["out"]:
        print("FAIL: %s differs from a fresh write" % os.path.relpath(OUT, ROOT))
        return 1
    vi, bad = verify(doc)
    p = subprocess.run([sys.executable, os.path.join(HERE, "jc3hkx.py"), "check",
                        "--entity", "__no_entity__", "--file", OUT],
                       capture_output=True, text=True, cwd=ROOT,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    print(p.stdout.strip())
    if p.returncode:
        bad.append("jc3hkx.py check --file failed")
    for r in vi["rows"]:
        print(f"  index {r['index']} {r['id']} {r['part']:18s} axis {r['axis']} "
              f"pivot {r['pivot']} limits {r['min']} .. {r['max']}")
    print(f"objects {vi['objects']}, constraint objects {vi['constraints']}, "
          f"original constraints identical {vi['orig_identical']}, "
          f"hknpPhysicsSystemData identical {vi['system_data_identical']}")
    for p2 in bad:
        print("FAIL", p2)
    if not bad:
        print("ok: copy matches, 13 constraints, new objects at 11 and 12")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
