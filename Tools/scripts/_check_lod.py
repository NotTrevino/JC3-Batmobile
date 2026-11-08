"""Two checks.

1. The Havok version. The note says 2014.1 on the strength of a string inside the
   physicsc. Check that string across every physicsc in the donor, not just one.

2. The unexplored declaration site. Extending geometry crashes. I proved the .epe
   stores no counts and the .physicsc stores no baked mesh. But the entity tree
   also has .lod files I never opened. Inventory every extension present, then
   look at the ones that are neither .rbm nor .vmodc.
"""
import collections
import glob
import os
import re
import struct

ROOT = ("E:/Modding/JustCause3/JC3-Batmobile/Builds/test-003/aaf")

# ---------------------------------------------------------------- 1. version tag
print("=== 1. Havok version tag across all .physicsc in the donor ===")
ph = sorted(glob.glob(ROOT + "/**/*.physicsc", recursive=True))
print("   physicsc files found: %d" % len(ph))
tags = collections.Counter()
for f in ph:
    head = open(f, "rb").read(4096)
    for m in re.findall(rb"hk_\d{4}\.\d+\.\d+[\w\-]*", head + open(f, "rb").read()):
        tags[m.decode("latin1")] += 1
for t, n in tags.most_common():
    print("   %-24s x%d" % (t, n))
print()

# ------------------------------------------------------- 2. entity file inventory
print("=== 2. what file types exist in the donor entity? ===")
ext = collections.Counter()
for r, _d, names in os.walk(ROOT):
    for n in names:
        ext[os.path.splitext(n)[1].lower()] += 1
for e, n in ext.most_common():
    print("   %-10s %d" % (e or "<none>", n))
print()

print("=== 3. the .lod files, which I never opened ===")
lods = sorted(glob.glob(ROOT + "/**/*.lod", recursive=True))
print("   .lod files: %d" % len(lods))
if lods:
    sample = lods[0]
    d = open(sample, "rb").read()
    print("   sample: %s  (%d B)" % (os.path.basename(sample), len(d)))
    print("   first 64 B: %s" % " ".join("%02X" % c for c in d[:64]))
    strs = re.findall(rb"[ -~]{4,}", d)
    print("   printable runs: %d" % len(strs))
    for s in strs[:20]:
        print("      %r" % s.decode("latin1"))
    print()

# ------------------------------------- 4. do the .lod files carry mesh declarations?
print("=== 4. do .lod files declare vertex/index counts or bounds? ===")
# counts from every lod1 render model in the donor
body_counts = {}
for f in sorted(glob.glob(ROOT + "/models/jc_vehicles/01_land/*/*_lod1.rbm")):
    base = os.path.basename(f)[: -len("_lod1.rbm")]
    d = open(f, "rb").read()
    # walk count-prefixed buffers crudely: look for u32 counts followed by plausible data
    body_counts[base] = len(d)

# pull every int32/uint32 out of each .lod and see if any equals a model byte size,
# a plausible vertex count, or a float that looks like a bounding extent
for f in lods[:4]:
    d = open(f, "rb").read()
    ints = [struct.unpack_from("<I", d, o)[0] for o in range(0, len(d) - 4, 4)]
    floats = [struct.unpack_from("<f", d, o)[0] for o in range(0, len(d) - 4, 4)]
    plaus = [v for v in ints if 20 <= v <= 200000]
    print("   %-34s ints=%d  in mesh-plausible range=%d"
          % (os.path.basename(f), len(ints), len(plaus)))
    if plaus:
        print("      first 25: %s" % plaus[:25])
print()

# -------------------------------- 5. do any non-rbm/vmodc files mention the parts?
print("=== 5. which files name the body's render parts? ===")
needle = b"body_lod1"
hits = collections.Counter()
for r, _d, names in os.walk(ROOT):
    for n in names:
        p = os.path.join(r, n)
        if n.lower().endswith((".rbm", ".dds", ".png", ".tga")):
            continue
        try:
            if needle in open(p, "rb").read():
                hits[os.path.splitext(n)[1].lower()] += 1
        except Exception:
            pass
print("   non-texture files containing 'body_lod1': %s"
      % (dict(hits) if hits else "NONE"))