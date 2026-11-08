import os, sys, struct, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3wiring

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME
ee = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee"

def inner(path):
    raw = jc3grab.read_entry(jc3detail.pick(rows, path), GAME)
    return jc3grab.inner_files(raw)

stream, entries = inner(ee)
fg = next(e for e in entries if e[0].endswith(".fmod_guids"))
blob = stream[fg[1]:fg[1]+fg[2]]
ver, nb = struct.unpack_from("<IH", blob, 0)
o = 6
banks = []
for _ in range(nb):
    (ln,) = struct.unpack_from("<H", blob, o); o += 2
    banks.append(blob[o:o+ln].decode()); o += ln
(ne,) = struct.unpack_from("<H", blob, o); o += 2
guids = [blob[o+i*16:o+i*16+16] for i in range(ne)]
print("ver", ver, "banks", banks, "events", ne, "end", o + ne*16, "len", len(blob))

objs, doc = jc3wiring.decode_epe(ee, rows, GAME)
sound = {}
for o_ in objs:
    s = o_.get("Sound")
    if not s:
        continue
    b = bytes(int(x, 16) for x in s.split(","))
    sound.setdefault(b, []).append((o_.cls, o_.name, o_.get("Usage")))
print("distinct Sound GUIDs in epe:", len(sound))
print("epe guids not in fmod_guids:", len([g for g in sound if g not in guids]))
print("fmod_guids not in epe:", len([g for g in guids if g not in sound]))

# bank membership: scan EVTS section of each bank for the 45 GUIDs
for bank in ("vehicles", "character", "effects"):
    path = f"sound/fmod_banks/{bank}.bank"
    raw = jc3grab.read_entry(jc3detail.pick(rows, path), GAME)
    hits = [g for g in guids if raw.find(g) >= 0]
    print(bank, "GUID hits", len(hits), "size", len(raw))
