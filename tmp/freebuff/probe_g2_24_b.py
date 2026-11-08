import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3wiring

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
ee = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee"
r = jc3detail.pick(rows, ee)
raw = jc3grab.read_entry(r, jc3index.DEFAULT_GAME)
stream, entries = jc3grab.inner_files(raw)
print("--- non-texture inner files (size, name) ---")
for n, off, size in entries:
    if not n.endswith((".ddsc", ".rbm", ".lod", ".rbmc", ".hkx")):
        print(f"{size:9d}  {n}")
        if n.endswith(".fmod_guids"):
            blob = stream[off:off+size]
            print("hex:", blob[:758].hex())
            print("ascii:", "".join(chr(b) if 32 <= b < 127 else "." for b in blob))
