"""UE3 import/export parse on decompressed stream; find vehicle-sound exports."""
import struct

IMG_BASE = 0x369  # file[0:0x369] + stream
stream = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
names = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_names.txt").read().splitlines()
NC = len(names)

def img(off):
    return off - IMG_BASE  # file offset -> stream offset

# --- imports: FObjectImport = ClassPackage(8) ClassName(8) PackageIndex(4) ObjectName(8) = 28B
ioff, icount = 0x182FD, 649
o = img(ioff)
imports = []
ok = True
for i in range(icount):
    cpp, cpn = struct.unpack_from("<ii", stream, o)
    cnn, cnn2 = struct.unpack_from("<ii", stream, o + 8)
    (pk,) = struct.unpack_from("<i", stream, o + 16)
    onn, onn2 = struct.unpack_from("<ii", stream, o + 20)
    o += 28
    imports.append((cpp, cpn, cnn, pk, onn))
# validate: name indices point at sane names
bad = sum(1 for _, _, cnn, _, onn in imports if not (0 <= cnn < NC and 0 <= onn < NC))
print("imports stride=28 bad=%d/%d" % (bad, icount))
if bad == 0:
    from collections import Counter
    print("import classes:", Counter(names[c] for _, _, c, _, _ in imports).most_common(12))
    akev = sorted({names[n] for _, _, c, _, n in imports if names[c] == "AkEvent"})
    akbk = sorted({names[n] for _, _, c, _, n in imports if names[c] == "AkBank"})
    print("== AkEvent imports (%d):" % len(akev))
    for n in akev:
        print("  EV:", n)
    print("== AkBank imports (%d):" % len(akbk))
    for n in akbk:
        print("  BK:", n)
    json = __import__("json")
    json.dump({"events": akev, "banks": akbk},
              open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\batmobile_wwise_refs.json", "w"), indent=1)
