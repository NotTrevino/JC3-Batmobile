"""PML mining: extract file paths (UTF-16 + ASCII), rank .upk/.wad/.bnk access."""
import os, re
from collections import Counter

p = r"C:\Users\User\Downloads\ProcessMonitor\Logfile.PML"
d = open(p, "rb").read()
print("pml bytes:", len(d), "magic:", d[:4])
paths = []
for m in re.findall(rb"(?:[ -~]\x00){8,}\.apk.{0,4}?", d):
    pass
# utf-16 strings with drive + extension
for m in re.findall(rb"[A-Za-z]:\\(?:[^\\/:*?\"<>|\x00-\x1f]\x00){2,}[^\\/:*?\"<>|\x00-\x1f\x00]*?\.(?:upk|wad|bnk|wem|pck|fsb|bank)\x00?", d):
    try:
        s = m.decode("utf-16-le", "replace")
        if len(s) < 300:
            paths.append(s.rstrip("\x00"))
    except Exception:
        pass
# ascii too
for m in re.findall(rb"[A-Za-z]:\\[ -~]{4,}?\.(?:upk|wad|bnk|wem|pck|fsb|bank)", d):
    try:
        paths.append(m.decode())
    except Exception:
        pass
print("path refs:", len(paths))
c = Counter(paths)
print("unique:", len(c))
for pth, n in c.most_common(60):
    print("%6d %s" % (n, pth))
# any battlemode/turbo/bml strings?
low = d.lower()
for t in [b"bml_battlemode", b"bml_turbo", b"bml_engine", b"play_batmobile_turbo", b"play_battlemodeengine"]:
    print(t.decode(), "x", low.count(t))
