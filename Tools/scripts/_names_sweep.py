"""Background sweep: names-probe every target pack >=2MB for Battlemode/bank names.
Reads Working/Audio/hunt_targets.txt, appends hits to battlemode_hits.txt.
Usage: python _names_sweep.py
"""
import os, struct, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lzo1x import lzo1x_decompress  # noqa: E402

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
A = r"E:\Modding\JC3-Batmobile\Working\Audio"
TAG = b"\xc1\x83\x2a\x9e"
HITS = os.path.join(A, "battlemode_hits.txt")

def first_chunks(d, H, maxch=12):
    out = []
    i = d.find(TAG, H)
    while i >= 0 and len(out) < maxch and i + 24 <= len(d):
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
    targets = [l.strip() for l in open(os.path.join(A, "hunt_targets.txt")) if l.strip()]
    done = set()
    if os.path.exists(HITS):
        for line in open(HITS):
            parts = line.strip().split(" ", 2)
            if len(parts) >= 2 and parts[0] in ("HIT", "ERR", "DONE"):
                done.add(parts[1].rstrip(":"))
    log = open(HITS, "a")
    n = 0
    for pkg in targets:
        p = os.path.join(CK, pkg)
        if not os.path.exists(p) or pkg in done:
            continue
        n += 1
        try:
            d = open(p, "rb").read()
            if d[:4] != TAG: continue
            (ln,) = struct.unpack_from("<i", d, 12)
            o = 16 + ln
            flags, nc, noff = struct.unpack_from("<iii", d, o)
            stream = b"".join(first_chunks(d, noff))
            img = d[:noff] + stream
            oo = noff
            found = []
            for _ in range(nc):
                if oo + 4 > len(img): break
                (ln,) = struct.unpack_from("<i", img, oo); oo += 4
                if not (0 < ln < 512 or -512 < ln < 0): break
                if ln > 0:
                    raw = img[oo:oo+ln]; oo += ln
                    nm = raw[:-1].decode("ascii", "replace")
                else:
                    nm = img[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00"); oo += (-ln)*2
                oo += 8
                if nm == "BML_Battlemode" or nm in ("Play_BattlemodeEngine", "Play_Batmobile_Turbo",
                                                   "VEH_Batmobile_MK2_Engine", "BML_Engine"):
                    found.append(nm)
            if found:
                log.write("HIT %s: %s\n" % (pkg, ",".join(found))); log.flush()
            else:
                log.write("DONE %s\n" % pkg)
                if n % 25 == 0:
                    log.flush()
        except Exception as e:
            log.write("ERR %s: %s\n" % (pkg, str(e)[:80])); log.flush()
    log.write("SWEEP-DONE packs=%d\n" % n)
    print("swept %d packs" % n)

main()
