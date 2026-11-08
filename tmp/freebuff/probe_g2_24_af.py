import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3wiring

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME

def blob(p):
    return jc3grab.read_entry(jc3detail.pick(rows, p), GAME)

def fmod_guids(ee):
    raw = blob(ee)
    stream, entries = jc3grab.inner_files(raw)
    hit = [e for e in entries if e[0].endswith(".fmod_guids")]
    if not hit:
        return None
    n, off, size = hit[0]
    b = stream[off:off+size]
    ver, nb = struct.unpack_from("<IH", b, 0)
    o = 6
    banks = []
    for _ in range(nb):
        (ln,) = struct.unpack_from("<H", b, o); o += 2
        banks.append(b[o:o+ln].decode()); o += ln
    (ne,) = struct.unpack_from("<H", b, o); o += 2
    return banks, [b[o+i*16:o+i*16+16] for i in range(ne)]

w619 = "editor/entities/jc_weapons/06_vehicle/w619_buggy_mgun/w619_buggy_mgun.ee"
print("w619 fmod_guids:", fmod_guids(w619))
w618 = "editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.ee"
print("w618 fmod_guids:", fmod_guids(w618))
objs, _ = jc3wiring.decode_epe(w619, rows, GAME)
for o in objs:
    if o.get("Sound"):
        print("  w619 SOUND", o.cls, o.name, o.get("Sound"))

# tank entities
for sub in ("v0201", "v0202"):
    ees = [r["path"] for r in rows if r["path"].startswith("editor/entities/jc_vehicles/") and sub in r["path"] and r["path"].endswith(".ee")]
    print(sub, len(ees))
    for ee in ees[:3]:
        print("  ", ee, "guids:", (fmod_guids(ee) or ("none",))[:1] if fmod_guids(ee) else "none")
