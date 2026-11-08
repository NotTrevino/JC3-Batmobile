import os, sys, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Tools", "scripts"))
import jc3grab, jc3index, jc3detail, jc3wiring, jc3adf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "Research", "JC3Grab")
rows = jc3index.load_index(OUT)
GAME = jc3index.DEFAULT_GAME

def blob(p):
    return jc3grab.read_entry(jc3detail.pick(rows, p), GAME)

ees = ["editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.ee",
       "editor/entities/jc_weapons/06_vehicle/w619_buggy_mgun/w619_buggy_mgun.ee"]
for ee in ees:
    raw = blob(ee)
    stream, entries = jc3grab.inner_files(raw)
    print("==", ee.split("/")[-1], "inner", len(entries))
    for n, off, size in entries:
        if not n.endswith((".ddsc", ".rbm", ".lod", ".rbmc", ".hkx")):
            print("   %8d %s" % (size, n))
    objs, doc = jc3wiring.decode_epe(ee, rows, GAME)
    print("   epe objects", len(objs))
    for o in objs:
        s = o.get("Sound")
        if s:
            print("   SOUND", o.cls, o.name, s)
    print("   classes:", sorted({o.cls for o in objs}))
