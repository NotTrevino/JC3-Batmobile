import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3wiring

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
ee = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee"
objs, doc = jc3wiring.decode_epe(ee, rows, jc3index.DEFAULT_GAME)
print("objects", len(objs))
from collections import Counter
print(Counter(o.cls for o in objs).most_common(30))
print()
for o in objs:
    if "Effect" in o.cls or "Sound" in o.cls or "Audio" in o.cls:
        print(o.cls, "|", o.name, "|", {k: v for k, v in list(o.props.items())[:8]})
