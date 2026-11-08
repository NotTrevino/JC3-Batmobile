import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
ee = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee"
r = jc3detail.pick(rows, ee)
print("entry", {k: r.get(k) for k in ("path", "size", "offset") if k in r})
raw = jc3grab.read_entry(r, jc3index.DEFAULT_GAME)
stream, entries = jc3grab.inner_files(raw)
print("inner files", len(entries))
for n, off, size in entries:
    print(f"{size:9d}  {n}")
