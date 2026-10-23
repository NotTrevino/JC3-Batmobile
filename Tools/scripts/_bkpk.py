"""BKPK bundle inspector: layout, embedded files, string refs."""
import os, re, struct

for fn in ["57572DAC.bnk", "EDF036D6.bnk"]:
    p = os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\SFX", fn)
    d = open(p, "rb").read()
    print("== %s (%d B)" % (fn, len(d)))
    print("  magic:", d[:4], "sizefield:", struct.unpack_from("<I", d, 4)[0])
    o = 8
    # dump first records: try (hash,size,offset)-ish table?
    print("  head:", d[o:o+64].hex(" "))
    # scan for embedded magic
    for magic in [b"BKHD", b"HIRC", b"RIFF", b"WWAD", b"BKPK"]:
        idxs = []
        i = d.find(magic)
        while i >= 0:
            idxs.append("0x%X" % i)
            i = d.find(magic, i + 1)
            if len(idxs) > 12:
                idxs.append("...")
                break
        print("  %r: %d @ %s" % (magic, len(idxs), idxs[:12]))
    # strings of decent length that look like paths/names
    strs = re.findall(rb"[A-Za-z0-9_\\/.]{8,}", d)
    uniq = sorted({s.decode() for s in strs})
    print("  pathish strings:", len(uniq))
    for s in uniq[:50]:
        print("    ", s[:120])
