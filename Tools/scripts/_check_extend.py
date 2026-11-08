"""Do the appended-geometry RBMs decode back cleanly and satisfy every internal
invariant the engine could plausibly check? Separates 'we produced a malformed
file' from 'the engine rejects well-formed new geometry'."""
import struct
import sys

sys.path.insert(0, r"E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

CASES = [
    ("test-013 body+fin",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-013/body_lod1_finned.rbm",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf/models/jc_vehicles/01_land/"
     "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm"),
    ("test-014 plate_r+fin",
     "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-014/plate_r_finned.rbm", None),
]

for tag, path, orig in CASES:
    raw = open(path, "rb").read()
    print("=== %s : %d B ===" % (tag, len(raw)))
    try:
        m = R.decode(raw)
    except Exception as e:
        print("   DECODE FAILED: %s" % e)
        continue
    print("   decodes OK: blocks=%d version=%s" % (len(m.blocks), m.version))
    try:
        print("   whole-file re-encode byte-identical: %s" % (m.write() == raw))
    except Exception as e:
        print("   whole-file RE-ENCODE FAILED: %s" % e)

    om = R.decode(open(orig, "rb").read()) if orig else None

    for i, b in enumerate(m.blocks):
        ob = om.blocks[i] if om else None
        vb, ib = getattr(b, "vb0", None), getattr(b, "ib", None)
        ovb = getattr(ob, "vb0", None) if ob else None
        oib = getattr(ob, "ib", None) if ob else None
        print("   [%d] %-11s verts=%-5s (was %-5s)  idx=%-5s (was %-5s)" % (
            i, type(b).__name__,
            getattr(vb, "count", "?"), getattr(ovb, "count", "-") if ovb else "-",
            getattr(ib, "count", "?"), getattr(oib, "count", "-") if oib else "-"))

        # every 16-bit index must address an existing vertex
        if ib is not None and vb is not None:
            idx = [struct.unpack_from("<H", ib.data, k * 2)[0] for k in range(ib.count)]
            bad = [x for x in idx if x >= vb.count]
            print("        indices out of range: %d  (max index %d, verts %d)" % (
                len(bad), max(idx) if idx else -1, vb.count))
            if bad:
                print("        !! %s" % bad[:8])
            # degenerate / inverted triangles
            degen = sum(1 for t in range(0, len(idx) - 2, 3)
                        if idx[t] == idx[t + 1] or idx[t + 1] == idx[t + 2] or idx[t] == idx[t + 2])
            print("        degenerate triangles: %d of %d" % (degen, len(idx) // 3))

        # float sanity across the whole vertex buffer
        if vb is not None:
            import math
            bad_f = 0
            for o in range(vb.count):
                for k in range(0, 12, 4):
                    v = struct.unpack_from("<f", vb.data, o * vb.stride + k)[0]
                    if not math.isfinite(v):
                        bad_f += 1
            print("        non-finite floats in positions: %d" % bad_f)

        # bone indices in a deform block must be inside the 256-entry table
        if getattr(b, "deform_table", None):
            tbl = list(b.deform_table)
            valid = set(tbl[:256])
            bad_bone = 0
            if vb is not None:
                for o in range(vb.count):
                    st = o * vb.stride + 12
                    for k in range(4):
                        if st + k * 4 + 4 <= len(vb.data):
                            v = struct.unpack_from("<i", vb.data, st + k * 4)[0]
                            if v != 0 and v not in valid:
                                bad_bone += 1
            print("        deform table entries: %d populated; bone refs outside it: %d"
                  % (len([t for t in tbl[:256] if t != -1 and t != 0xFFFFFFFF]), bad_bone))

        # byte-exact re-encode of this block in isolation
        try:
            enc = R.encode_block(b)
            print("        block encodes to %d B" % len(enc))
        except Exception as e:
            print("        RE-ENCODE FAILED: %s" % e)
    print()