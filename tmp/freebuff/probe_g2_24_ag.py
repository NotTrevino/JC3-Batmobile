import os, sys, json, glob, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3adf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME

# LandAudio module
ee = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.ee"
raw = jc3grab.read_entry(jc3detail.pick(rows, ee), GAME)
stream, entries = jc3grab.inner_files(raw)
n, off, size = next(e for e in entries if e[0].endswith("land_audio.vmodc"))
print("LandAudio", size, n)
for name, typ, val in jc3adf.walk(jc3adf.Adf(stream[off:off+size])):
    print("   %-40s %-8s %s" % (name, typ, val))

# fleet scan
files = glob.glob(r"E:/Modding/_JC3grab/detail/*.ee.json")
print("detail files", len(files))
sound_objs = 0
names = collections.Counter()
per_entity = {}
horn, radio = [], []
for f in files:
    try:
        d = json.load(open(f))
    except Exception:
        continue
    got = False
    for o in d.get("epe", {}).get("objects", []):
        v = o.get("values") or {}
        if "Sound" in v:
            sound_objs += 1
            names[(o.get("class"), o.get("name"))] += 1
            got = True
            nm = (o.get("name") or "").lower()
            if "horn" in nm:
                horn.append((os.path.basename(f), o.get("class"), o.get("name"), v["Sound"]))
            if "radio" in nm:
                radio.append((os.path.basename(f), o.get("class"), o.get("name")))
    if got:
        per_entity[os.path.basename(f)] = True
print("Sound-carrying objects:", sound_objs, "in", len(per_entity), "entities")
print("distinct (class,name):", len(names))
print("horn objects:", len(horn))
for h in horn[:10]:
    print("   ", h)
print("radio objects:", len(radio))
for r in radio[:10]:
    print("   ", r)
print("top names:", names.most_common(12))
