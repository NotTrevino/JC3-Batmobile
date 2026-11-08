"""Export table stride probe + AkBank/AKEvent export hunt."""
import struct

IMG_BASE = 0x369
stream = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
names = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_names.txt").read().splitlines()
NC = len(names)
eoff, ecount = 0x1C9F9 - IMG_BASE, 5490

def score_stride(st):
    bad = 0
    for i in (0, 1, 100, 1000, ecount - 1):
        o = eoff + i * st
        ci, si, oi = struct.unpack_from("<iii", stream, o)
        ni, nn = struct.unpack_from("<ii", stream, o + 12)
        if not (0 <= ni < NC):
            bad += 1
    return bad

for st in (60, 64, 68, 72, 76, 80):
    print("stride", st, "bad=", score_stride(st))

ST = 72  # (0x7D209-0x369 - (0x1C9F9-0x369)) / 5490 = 395280/5490 = 72 exact
# full validation + collect AkBank/AKEvent-classed exports
o = eoff
exps = []
for i in range(ecount):
    ci, si, oi = struct.unpack_from("<iii", stream, o)
    ni, nn = struct.unpack_from("<ii", stream, o + 12)
    exps.append((ci, ni))
    o += ST
bad = sum(1 for _, ni in exps if not (0 <= ni < NC))
print("full walk bad:", bad)
# class names: negative ci = import index (-ci-1 into imports)? need imports; approximate:
# find exports whose object name matches banks/events of interest
want = {"BML_Batmobile", "BML_Batmobile_Subjective", "BML_Battlemode", "BML_Tyres",
        "Play_Batmobile_Turbo", "Play_BattlemodeEngine", "Play_Batmobile_Engine_Transition_In"}
for i, (ci, ni) in enumerate(exps):
    if names[ni] in want:
        print("export[%d] class_ref=%d name=%s" % (i, ci, names[ni]))
