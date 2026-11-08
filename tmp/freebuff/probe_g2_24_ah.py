import os, sys, json, glob, struct, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3adf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME

# w602/w603 wtunec members
for wid in ("w602_mediumtank_canon", "w603_mediumtank_mgun"):
    p = f"editor/entities/jc_weapons/06_vehicle/{wid}/{wid}.wtunec"
    raw = jc3grab.read_entry(jc3detail.pick(rows, p), GAME)
    names = [n for n, t, v in jc3adf.walk(jc3adf.Adf(raw))]
    print(wid, "members", len(names))
    print("   ", names[:40])

# medium tank epe sound names
p = glob.glob(r"E:/Modding/_JC3grab/detail/v0201_car_capstone_mediumtank*military_01.ee.json")[0]
d = json.load(open(p))
snd = [(o.get("class"), o.get("name"), o.get("values", {}).get("Sound")) for o in d["epe"]["objects"] if "Sound" in (o.get("values") or {})]
print("medium tank sound objects", len(snd))
for s in snd[:25]:
    print("   ", s)

# weapons.bank FSB name table
raw = jc3grab.read_entry(jc3detail.pick(rows, "sound/fmod_banks/weapons.bank"), GAME)
i = raw.find(b"FSB5")
n, shdr, namelen = struct.unpack_from("<III", raw, i+8)
t0 = i + 60 + shdr
blob_at = t0 + 4*n
names = []
o = blob_at
for _ in range(n):
    e = raw.find(b"\x00", o)
    names.append(raw[o:e].decode(errors="replace"))
    o = e + 1
print("weapons.bank samples", n, "names", len(names))
hits = [x for x in names if any(k in x.lower() for k in ("cannon", "tank", "mgun", "marine", "bullets"))]
print("tank/cannon-ish names:", len(hits))
for x in hits[:25]:
    print("   ", x)
