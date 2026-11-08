import os, sys, json, struct, re, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3adf, jc3wiring

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
ROOT = os.path.join(HERE, "..", "..")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME
DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_civilian_01.ee")

raw = jc3grab.read_entry(jc3detail.pick(rows, DONOR), GAME)
stream, entries = jc3grab.inner_files(raw)
n, off, size = next(e for e in entries if e[0].endswith("custom_land_global.vmodc"))
print("== custom_land_global nitro members")
for nm, t, v in jc3adf.walk(jc3adf.Adf(stream[off:off+size])):
    if "nitro" in nm.lower() or "boost" in nm.lower() or "turbo" in nm.lower():
        print("   %-46s %-8s %s" % (nm, t, v))

print("== donor epe nitrous objects")
objs, _ = jc3wiring.decode_epe(DONOR, rows, GAME)
for o in objs:
    nm = (o.name or "")
    if "nitro" in nm.lower():
        print("   %-20s %-26s Usage=%s Effect=%s Sound=%s" % (o.cls, nm, o.get("Usage"),
                                                              o.get("Effect"), o.get("Sound")))

# bank membership for the nitrous Sound GUIDs
guids = {}
for o in objs:
    if "nitro" in (o.name or "").lower() and o.get("Sound"):
        g = bytes(int(x, 16) for x in o.get("Sound").split(","))
        guids[o.name] = g
print("nitrous sound guids:", len(guids))
for bank in ("vehicles", "character", "effects"):
    b = jc3grab.read_entry(jc3detail.pick(rows, f"sound/fmod_banks/{bank}.bank"), GAME)
    hits = [nm for nm, g in guids.items() if b.find(g) >= 0]
    print(" ", bank, len(hits), hits)

# vehicle bank sample names with nitro/turbo
d = jc3grab.read_entry(jc3detail.pick(rows, "sound/fmod_banks/vehicles.bank"), GAME)
i = d.find(b"FSB5")
n2, shdr, namelen = struct.unpack_from("<III", d, i + 8)
t0 = i + 60 + shdr
names = []
for k in range(n2):
    p = t0 + struct.unpack_from("<I", d, t0 + 4*k)[0]
    e = d.find(b"\x00", p)
    names.append(d[p:e].decode("utf-8", "replace"))
hits = [(k+1, x) for k, x in enumerate(names) if re.search(r"nitro|turbo|boost", x, re.I)]
print("== vehicles.bank nitro/turbo names:", len(hits))
for h in hits:
    print("   ", h)

# test-060 files
print("== builds")
for p in sorted(glob.glob(os.path.join(ROOT, "Builds", "test-0*"))):
    print("   ", os.path.basename(p))
print("== premium_nitro in repo text")
for f in glob.glob(os.path.join(ROOT, "Tools", "**", "*.py"), recursive=True):
    s = open(f, encoding="utf-8", errors="replace").read()
    if "premium_nitro" in s:
        print("   ", os.path.relpath(f, ROOT))
