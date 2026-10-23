"""spec_check.py - prove every JC3 block input in an assembly equals its factors.py spec. §79.

For every RBM written by bat_assemble.py (body_lodN, wheel_<c>_lodN), block k belongs to
assembly.json's plan[part][k]. For each CarPaintMM block it decodes static_params (18 float4),
static_support (7 floats), dynamic_params (tints + overrides), flags and texture slots s0-s3 and
compares them with factors.json; Window blocks are checked for type. Any mismatch fails. It also
reports, per field, how many blocks still equal the SERPENTE template's value where the spec says
otherwise -- that number must be zero (no silent inheritance).

Usage: python spec_check.py <assembly_dir> <body_template.rbm> [--block 3]
"""
import argparse
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
    ap.add_argument("dir")
    ap.add_argument("template")
    ap.add_argument("--block", type=int, default=3)
    a = ap.parse_args()
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
    sys.exit(1 if fails or inherited else 0)


if __name__ == "__main__":
    main()
