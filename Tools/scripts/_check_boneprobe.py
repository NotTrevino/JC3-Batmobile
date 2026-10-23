"""Control for the bone-index probe in _check_extend.py.

If the probe reports violations on pristine vanilla files that were never edited,
the probe is wrong about the layout, not the files. Stride/layout for the deform
buffers is UNVERIFIED (see MODLOG), so this is the check that decides it.
"""
import glob
import struct
import sys

sys.path.insert(0, r"E:\Modding\JC3-Batmobile\Tools\scripts")
import rbm_geom as R  # noqa: E402

root = ("E:/Modding/JC3-Batmobile/Builds/test-003/aaf/models/jc_vehicles/01_land/"
        "v0300_car_kensington_sportsmuscle")

for name in ("sportsmuscle_plate_r_lod1.rbm", "sportsmuscle_body_lod1.rbm"):
    hits = glob.glob(root + "/" + name)
    if not hits:
        print("%-38s not found" % name)
        continue
    m = R.decode(open(hits[0], "rb").read())
    b = m.blocks[0]
    vb = b.vb0
    tbl = list(b.deform_table)
    valid = set(tbl[:256])
    out_of_range = 0
    for o in range(vb.count):
        st = o * vb.stride + 12
        for k in range(4):
            if st + k * 4 + 4 <= len(vb.data):
                v = struct.unpack_from("<i", vb.data, st + k * 4)[0]
                if v != 0 and v not in valid:
                    out_of_range += 1
    print("%-38s PRISTINE VANILLA" % name)
    print("   stride=%d count=%d  table populated=%d  probe reports %d out-of-range bone refs"
          % (vb.stride, vb.count, len([t for t in tbl[:256] if t not in (-1, 0xFFFFFFFF)]),
             out_of_range))
    print("   -> probe is %s" % ("BOGUS (it flags untouched vanilla data)"
                                 if out_of_range else "sound"))