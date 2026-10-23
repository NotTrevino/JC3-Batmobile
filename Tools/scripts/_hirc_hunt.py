"""HIRC-ID hunt: full dechunk top packs, grep every carved bank for battle/turbo event IDs.
Catches differently-named banks (content-based). Resume via hirc_hunt.log.
Usage: python _hirc_hunt.py
"""
import os, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lzo1x import lzo1x_decompress  # noqa: E402

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
A = r"E:\Modding\JC3-Batmobile\Working\Audio"
TAG = b"\xc1\x83\x2a\x9e"
EV1 = struct.pack("<I", 0x388710DB)
EV2 = struct.pack("<I", 0xB1B5DD98)
LOG = os.path.join(A, "hirc_hunt.log")

def dechunk(d, start):
    out = []
    i = d.find(TAG, start)
    while i >= 0 and i + 24 <= len(d):
        x, tc, tu = struct.unpack_from("<III", d, i + 4)
        if x != 0x20000:
            i = d.find(TAG, i + 4); continue
        q = i + 16
        pairs, su = [], 0
        while su < tu:
            if q + 8 > len(d) or len(pairs) > 512: break
            bc, bu = struct.unpack_from("<II", d, q); q += 8
            pairs.append((bc, bu)); su += bu
        if su != tu:
            i = d.find(TAG, i + 4); continue
        cat = bytearray(); bad = False
        for bc, bu in pairs:
            blk = d[q:q+bc]
            try:
                raw = zlib.decompress(blk) if blk[:2] in (b"\x78\x9c", b"\x78\x01", b"\x78\xda") \
                    else lzo1x_decompress(blk)
            except Exception: bad = True; break
            if len(raw) != bu: bad = True; break
            cat += raw; q += bc
        if not bad: out.append(bytes(cat))
        i = d.find(TAG, q)
    return out

def main():
    targets = [l.strip() for l in open(os.path.join(A, "hunthirc_targets.txt")) if l.strip()]
    done = set()
    if os.path.exists(LOG):
        for line in open(LOG):
            p = line.strip().split(" ", 1)
            if len(p) == 2 and p[0] in ("HIT", "DONE", "ERR"):
                done.add(p[1].split(":")[0])
    log = open(LOG, "a")
    for pkg in targets:
        if pkg in done:
            continue
        try:
            d = open(os.path.join(CK, pkg), "rb").read()
            if d[:4] != TAG:
                log.write("ERR %s: not-upk\n" % pkg); continue
            (ln,) = struct.unpack_from("<i", d, 12)
            o = 16 + ln
            flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", d, o)
            img = d[:noff] + b"".join(dechunk(d, noff))
            names = []
            oo = noff
            for _ in range(nc):
                (ln,) = struct.unpack_from("<i", img, oo); oo += 4
                if ln > 0:
                    raw = img[oo:oo+ln]; oo += ln
                    names.append(raw[:-1].decode("ascii", "replace"))
                else:
                    names.append(img[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); oo += (-ln)*2
                oo += 8
            oo = ioff; ak = set()
            for ii in range(ic):
                cnn, _ = struct.unpack_from("<ii", img, oo + 8)
                onn, _ = struct.unpack_from("<ii", img, oo + 20)
                if names[cnn] == "Class" and names[onn] == "AkBank":
                    ak.add(ii)
                oo += 28
            STR = (doff - eoff) // ec
            oo = eoff
            hit = []
            for _ in range(ec):
                ci, = struct.unpack_from("<i", img, oo)
                ni, _ = struct.unpack_from("<ii", img, oo + 12)
                _, _, _, _, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
                if any(ci == -(a + 1) for a in ak):
                    seg = img[off:off+size]
                    j = seg.find(b"BKHD")
                    if j >= 0 and (EV1 in seg or EV2 in seg):
                        hit.append(names[ni])
                oo += STR
            log.write("%s %s%s\n" % ("HIT" if hit else "DONE", pkg, ": " + ",".join(hit) if hit else ""))
            log.flush()
        except Exception as e:
            log.write("ERR %s: %s\n" % (pkg, str(e)[:100])); log.flush()
    log.write("HIRC-HUNT-DONE\n")
    print("hunt done")

main()
