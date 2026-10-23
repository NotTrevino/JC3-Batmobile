"""Multi-PML diff: file sets per capture; battle-only vs pursuit-only files."""
import os, re
from collections import Counter

PM = r"C:\Users\User\Downloads\ProcessMonitor"
files = ["Pursuitmode_to_Battlemode_Logfile.PML", "Battlemode_to_Pursuitmode_Logfile.PML",
         "Pursuitmode_Afterburner_Logfile.PML", "Battlemode_Turbo_Logfile.PML",
         "Logfile.PML"]

def paths_of(p):
    d = open(os.path.join(PM, p), "rb").read()
    out = []
    for m in re.findall(rb"[A-Za-z]:\\(?:[^\\/:*?\"<>|\x00-\x1f]\x00){2,}[^\\/:*?\"<>|\x00-\x1f\x00]*?\.(?:upk|wad|bnk|wem|pck|fsb|bank)\x00?", d):
        try:
            s = m.decode("utf-16-le", "replace").rstrip("\x00")
            if len(s) < 300:
                out.append(s)
        except Exception:
            pass
    for m in re.findall(rb"[A-Za-z]:\\[ -~]{4,}?\.(?:upk|wad|bnk|wem|pck|fsb|bank)", d):
        try: out.append(m.decode())
        except Exception: pass
    return Counter(out)

sets = {}
for f in files:
    p = os.path.join(PM, f)
    if not os.path.exists(p):
        print(f, "MISSING"); continue
    c = paths_of(f)
    sets[f] = set(c)
    print("== %s (%dB): %d refs, %d unique" % (f, os.path.getsize(p), sum(c.values()), len(c)))

names = list(sets)
base = sets[names[0]]
for n in names[1:]:
    only_n = sets[n] - base
    only_base = base - sets[n]
    if only_n:
        print("--- only in %s:" % n)
        for x in sorted(only_n)[:20]: print("    ", x)
