"""spec_check.py - prove every JC3 block input in an assembly equals its spec. §79 + B-03.

Two arms, run together when both are named:
  <dir> <template>   every CarPaintMM / Window block of an assembly equals its factors.py spec
                     (the original arm, unchanged)
  --lights <dir>     every CarLight block of B-03's light-part build equals
                     `lights_manifest.json`: the cloned vanilla header/mid-static/texture table
                     byte-exact (the block's material parameters are undecoded, MODLOG §102d) and
                     the manifest's counts and bbox. The directory must also hold exactly the
                     manifest's RBM set (a stray RBM is a failure). This is B-03's `Done` check.

For every RBM written by bat_assemble.py (body_lodN, wheel_<c>_lodN), block k belongs to
assembly.json's plan[part][k]. For each CarPaintMM block it decodes static_params (18 float4),
static_support (7 floats), dynamic_params (tints + overrides), flags and texture slots s0-s3 and
compares them with factors.json; Window blocks are checked for type. Any mismatch fails. It also
reports, per field, how many blocks still equal the SERPENTE template's value where the spec says
otherwise -- that number must be zero (no silent inheritance).

Usage: python spec_check.py <assembly_dir> <body_template.rbm> [--block 3]
"""
import argparse
import glob
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factors as FX  # noqa: E402
import rbm_geom as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", nargs="?")
    ap.add_argument("template", nargs="?")
    ap.add_argument("--block", type=int, default=3)
    ap.add_argument("--lights", help="B-03 light-part build directory (holds lights_manifest.json)")
    a = ap.parse_args()
    rc = 0
    if a.lights:
        rc |= check_lights(a.lights)
    if a.dir and a.template:
        rc |= check_assembly(a)
    elif not a.lights:
        ap.error("give <dir> <template>, --lights, or both")
    sys.exit(rc)


def check_lights(lights_dir):
    """B-03: every CarLight block equals the cloned template's header and the manifest's geometry."""
    import rbm_geom as R
    man_path = os.path.join(lights_dir, "lights_manifest.json")
    if not os.path.exists(man_path):
        print(f"FAIL: {man_path} missing")
        return 1
    man = json.load(open(man_path, encoding="utf-8"))
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tpl_path = os.path.join(root, man["template"]["file"])
    tpl = [b for b in R.decode(open(tpl_path, "rb").read()).blocks
           if R.BLOCK_NAMES.get(b.type_hash) == "CarLight"][0]
    fails, checked = [], 0
    want = {n for lamp in man["lamps"] for n in lamp["lod_files"]}
    have = {os.path.basename(p) for p in glob.glob(os.path.join(lights_dir, "*.rbm"))}
    for name in sorted(have - want):
        fails.append(f"{name}: not in lights_manifest.json (stray RBM in the build directory)")
    for name in sorted(want - have):
        fails.append(f"{name}: in the manifest, missing on disk")
    for lamp in man["lamps"]:
        if lamp.get("block") != "CarLight":
            fails.append(f"{lamp['part']}: manifest block {lamp.get('block')!r}, expected CarLight")
            continue
        if len(lamp["lod_files"]) != man["lod_ladder"]["lods"]:
            fails.append(f"{lamp['part']}: {len(lamp['lod_files'])} LODs vs "
                         f"{man['lod_ladder']['lods']} declared")
        for i, name in enumerate(lamp["lod_files"]):
            p = os.path.join(lights_dir, name)
            if not os.path.exists(p):
                fails.append(f"{name}: missing")
                continue
            raw = open(p, "rb").read()
            m = R.decode(raw)
            if len(m.blocks) != 1 or R.BLOCK_NAMES.get(m.blocks[0].type_hash) != "CarLight":
                fails.append(f"{name}: blocks {m.block_names()}")
                continue
            blk = m.blocks[0]
            checked += 1
            if blk.strides != (12, 24, 2):
                fails.append(f"{name}: strides {blk.strides} != (12, 24, 2)")
            if blk.pre_static != tpl.pre_static:
                fails.append(f"{name}: 1085 B header differs from {man['template']['file']}")
            if blk.mid_static != tpl.mid_static:
                fails.append(f"{name}: 16 B mid-static differs from the template")
            if blk.textures != tpl.textures:
                fails.append(f"{name}: texture table differs from the template")
            if blk.buffers[0].count != lamp["vertices_per_lod"][i]:
                fails.append(f"{name}: {blk.buffers[0].count} verts vs manifest "
                             f"{lamp['vertices_per_lod'][i]}")
            if blk.index_count != lamp["faces_per_lod"][i] * 3:
                fails.append(f"{name}: {blk.index_count} indices vs manifest "
                             f"{lamp['faces_per_lod'][i]} tris")
            pos = np.frombuffer(blk.buffers[0].data, "<f4").reshape(-1, 3)
            lo, hi = lamp["bbox_m"][i]
            if not np.allclose(pos.min(0), lo, atol=1e-4) or not np.allclose(pos.max(0), hi, atol=1e-4):
                fails.append(f"{name}: geometry bbox differs from the manifest")
            if not np.allclose(m.bbox_min, pos.min(0), atol=1e-5) or \
                    not np.allclose(m.bbox_max, pos.max(0), atol=1e-5):
                fails.append(f"{name}: file header bbox != geometry")
            six = np.frombuffer(blk.buffers[1].data, "<f4").reshape(-1, 6)
            if not np.allclose(six[:, 2:4], 0.0):
                fails.append(f"{name}: second-stream columns 2,3 are not zero")
            if m.write() != raw:
                fails.append(f"{name}: re-encode is not byte-identical")

    print(f"CarLight: checked {checked} blocks over {len(man['lamps'])} lamp parts; "
          f"spec mismatches {len(fails)}")
    for x in fails[:30]:
        print("  FAIL", x)
    return 1 if fails else 0


def check_assembly(a):
    """The original arm: every CarPaintMM / Window block equals its factors.py spec. §79."""
    asm = json.load(open(os.path.join(a.dir, "assembly.json")))
    specs = json.load(open(os.path.join(a.dir, "factors.json")))["materials"]
    tex_vfs = asm["textures"]
    tpl = R.decode(open(a.template, "rb").read()).blocks[a.block]
    tpl_sp = np.frombuffer(tpl.static_params, "<f4").reshape(18, 4)
    fails, checked, inherited = [], 0, 0
    for part, items in asm["plan"].items():
        for lod in range(1, 6):
            f = os.path.join(a.dir, f"{part}_lod{lod}.rbm")
            m = R.decode(open(f, "rb").read())
            if len(m.blocks) != len(items):
                fails.append(f"{f}: {len(m.blocks)} blocks vs {len(items)} planned")
                continue
            for blk, it in zip(m.blocks, items):
                spec = specs[it["material"]]
                name = R.BLOCK_NAMES.get(blk.type_hash)
                if name != spec["block"]:
                    fails.append(f"{f} {it['material']}: block {name} vs spec {spec['block']}")
                    continue
                checked += 1
                if name == "Window":
                    # glass: only the slots factors.py actually binds (dif/normal) are ours; the
                    # crack slots stay the template's, so they are reported, not failed
                    for s, t in spec["textures"].items():
                        path = blk.textures[int(s[1])]
                        if "tga" in t and path not in tex_vfs:
                            fails.append(f"{f} {it['material']}: Window {s} = {path} (spec {t.get('source')})")
                    continue
                inp = spec["inputs"]
                sp = np.frombuffer(blk.static_params, "<f4").reshape(18, 4)
                for i, n in enumerate(FX.STATIC):
                    want = np.array(inp["static." + n]["value"], np.float32)
                    if not np.allclose(sp[i], want, atol=1e-5):
                        fails.append(f"{f} {it['material']}: static.{n} {sp[i].tolist()} != {want.tolist()}")
                    if np.allclose(sp[i], tpl_sp[i]) and not np.allclose(want, tpl_sp[i]):
                        inherited += 1
                su = np.frombuffer(blk.static_support, "<f4")
                for i, n in enumerate(FX.SUPPORT):
                    if abs(su[i] - inp["support." + n]["value"]) > 1e-6:
                        fails.append(f"{f} {it['material']}: support.{n} {su[i]} != {inp['support.' + n]['value']}")
                dy = np.frombuffer(blk.dynamic_params, "<f4")
                for i, n in enumerate(("TintColorR", "TintColorG", "TintColorB")):
                    if not np.allclose(dy[4 * i:4 * i + 4], inp["dynamic." + n]["value"], atol=1e-5):
                        fails.append(f"{f} {it['material']}: dynamic.{n} {dy[4 * i:4 * i + 4].tolist()}")
                if not np.allclose(dy[16:19], inp["dynamic.Overrides"]["value"], atol=1e-5):
                    fails.append(f"{f} {it['material']}: dynamic.Overrides {dy[16:19].tolist()}")
                if blk.flags != spec["flags"]["value"]:
                    fails.append(f"{f} {it['material']}: flags 0x{blk.flags:04X} != 0x{spec['flags']['value']:04X}")
                for s in ("s0", "s1", "s2", "s3"):
                    path = blk.textures[int(s[1])]
                    t = spec["textures"][s]
                    if "vanilla" in t:
                        ok = path == t["vanilla"]
                    else:
                        ok = path in tex_vfs
                    if not ok:
                        fails.append(f"{f} {it['material']}: {s} = {path} (spec {t.get('source')})")
    print(f"checked {checked} blocks; spec mismatches {len(fails)}; template values silently inherited {inherited}")
    for x in fails[:30]:
        print("  FAIL", x)
    return 1 if fails or inherited else 0


if __name__ == "__main__":
    main()
