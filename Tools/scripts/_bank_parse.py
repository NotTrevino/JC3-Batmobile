"""Parse carved banks: HIRC event->media, STID names, DIDX media index."""
import os, struct

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"

def parse_hirc(d, label):
    hi = d.find(b"HIRC")
    if hi < 0:
        print(label, "no HIRC"); return {}
    (hsz,) = struct.unpack_from("<I", d, hi + 4)
    o = hi + 8
    (n,) = struct.unpack_from("<I", d, o); o += 4
    ev, snd = {}, {}
    from collections import Counter
    tc = Counter()
    for _ in range(n):
        t = d[o]; (sz,) = struct.unpack_from("<I", d, o + 1); body = d[o+5:o+5+sz]
        tc[t] += 1
        if t == 4:
            eid, = struct.unpack_from("<I", body, 0)
            na = body[4]
            ev[eid] = [struct.unpack_from("<I", body, 5 + 4 * k)[0] for k in range(na)]
        elif t == 2:
            sid, = struct.unpack_from("<I", body, 0)
            u32s = struct.unpack("<%dI" % (len(body)//4), body[:len(body)//4*4])
            snd[sid] = u32s
        o += 5 + sz
    print("%s: HIRC %d objs %s events=%d sounds=%d" % (label, n, dict(sorted(tc.items())), len(ev), len(snd)))
    return ev, snd

def parse_stid(d, label):
    si = d.find(b"STID")
    if si < 0:
        print(label, "no STID"); return
    (sz,) = struct.unpack_from("<I", d, si + 4)
    print(label, "STID size", sz, "body:", d[si+8:si+8+sz].hex(" "))

for fn in ["bank_BML_Burnout.bank", "bank_AUX_InBatmobile.bank"]:
    d = open(os.path.join(A, fn), "rb").read()
    parse_hirc(d, fn)
    parse_stid(d, fn)

# BML_Engine: DIDX + DATA (carve full bank incl. trailing sections first)
stream = open(os.path.join(A, "..", "..", "Working", "Audio", "bm_stream.bin"), "rb").read() \
    if False else None
import glob
src = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
so = 0x107DF6 - 0x369
seg = src[so:so+7278764]
i = seg.find(b"BKHD")
o = i
bank_end = None
while o + 8 <= len(seg):
    tag = seg[o:o+4]
    (sz,) = struct.unpack_from("<I", seg, o + 4)
    print("BML_Engine sect %r size %d" % (tag, sz))
    o += 8 + sz
    if o - i > 7278764:
        break
    if tag in (b"HIRC", b"STID", b"ENVS"):
        bank_end = o
        break
print("bank spans +113..+%d" % o)
full = seg[i:o]
open(os.path.join(A, "bank_BML_Engine.bank"), "wb").write(full)
# DIDX
di = full.find(b"DIDX")
(dsz,) = struct.unpack_from("<I", full, di + 4)
print("DIDX size:", dsz, "head:", full[di+8:di+40].hex(" "))
# try: u32 count then 12B entries (id, off, size)?
o2 = di + 8
(cnt,) = struct.unpack_from("<I", full, o2)
print("DIDX count?", cnt)
o2 += 4
for k in range(min(cnt if cnt < 1000 else 8, 8)):
    print("  entry:", full[o2:o2+12].hex(" "))
    o2 += 12
