"""Hash every collected name table vs unmatched BML_Engine events + key IDs."""
import glob, os

def fnv1(s):
    h = 0x811C9DC5
    for b in s.encode():
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ b
    return h

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
want = {0x2099606B: "?", 0x2479106C: "?", 0x388CE6FC: "?", 0x3C3F43C0: "?",
        0x9AF38C66: "?", 0xA88826DB: "?", 0xBD2FEE58: "?",
        0x388710DB: "Play_BattlemodeEngine?", 0xB1B5DD98: "Play_Batmobile_Turbo?"}
tables = ["bm_names.txt", "mk2_names.txt", "gpcd_names.txt"] + \
    [os.path.relpath(p, A) for p in glob.glob(os.path.join(A, "conv", "*", "names.txt"))]
print("tables:", len(tables))
for t in tables:
    p = os.path.join(A, t)
    if not os.path.exists(p):
        continue
    hit = []
    for line in open(p, encoding="utf-8", errors="replace"):
        nm = line.strip()
        if not nm:
            continue
        h = fnv1(nm.lower())
        if h in want:
            hit.append((nm, h))
    if hit:
        print("== %s:" % t)
        for nm, h in hit[:20]:
            print("   %08X = %s" % (h, nm))
print("done")
