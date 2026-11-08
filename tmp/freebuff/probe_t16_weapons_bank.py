"""T-16 probe: what samples does weapons.bank hold, and are the ones I need decodable?

Extracts sound/fmod_banks/weapons.bank from the game archives to
E:\Modding\JustCause3\_grab\audio\weapons.bank (outside the repo, R10) on first run, then
prints the FSB5 name table entries that match the four weapon candidates.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))

import jc3audio  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.path.join("E:/Modding/JustCause3/_grab/audio", "weapons.bank")
rows = jc3index.load_index(os.path.join(ROOT, "Research", "JC3Grab"))


def pick(path):
    return jc3detail_pick(rows, path)


def jc3detail_pick(rows, path):
    import jc3detail
    return jc3detail.pick(rows, path)


os.makedirs(os.path.dirname(DEST), exist_ok=True)
want = os.path.getsize(DEST) if os.path.exists(DEST) else -1
print("cached", want)
d = jc3audio.read_entry("sound/fmod_banks/weapons.bank", rows)
print("entry bytes", len(d))
if want != len(d):
    open(DEST, "wb").write(d)
    print("wrote", DEST, len(d))
f = jc3audio.fev(d)
print("fev", f["version"], f["build"], "fsb_off", f["fsb_off"])
fsb = jc3audio.fsb(d, f["fsb_off"], True)
print("samples", fsb["samples"], "names", len(fsb["names"]))
pat = re.compile(r"cannon|mgun|machine|missile|turret|minigun|gatling|rocket|tank|wpn", re.I)
for i, n in enumerate(fsb["names"], 1):
    if pat.search(n):
        print(i, n)
