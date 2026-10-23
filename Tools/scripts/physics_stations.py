"""physics_stations.py - move the Serpente's wheel physics onto the asset's true stations. MODLOG §70.

Consumes `stations.json` from bat_assemble.py, so meshes and physics come from ONE set of numbers
(the 047 jitter came from moving one without the other).

land_global.vmodc (the PATCHED 1,600 B copy; the .ee's own copy is pre-patch, §48): in-place float
writes at ConvertAdf `offset-in-file`, every old value asserted --
    base_wheel_hardpoint_positions  4 x (x, y, z)         -> stations hardpoints
    front/rear_wheels.radius        0.38                  -> tyre radius
    front/rear_wheels.rim_radius    0.30                  -> scaled by the same ratio
    front/rear_wheels.width         0.245 / 0.285         -> tyre width
    ground_clearance                0.40 (== vanilla hub Y) -> new hub Y  [ASSUMPTION: unknown
                                                              semantics; it equals the hub height]
sportsmuscle.physicsc: the 4 baked (x, y, z, 1.0) station quads (§65; Havok accepted a moved set in
test-055) -> the same hardpoints. Corners are matched by the SIGNS of x and z, never by order.

Usage: python physics_stations.py <stations.json> <land_global.vmodc> <land_global.xml>
           <in.physicsc> --out-land <out.vmodc> --out-phys <out.physicsc>
"""
import argparse
import json
import struct
import xml.etree.ElementTree as ET

VANILLA_X, VANILLA_Y, VANILLA_Z = 0.885, 0.4, {-1: -1.557, +1: 1.446}   # (sign z) -> z


def corner_for(x, z, corners):
    for c, v in corners.items():
        hx, _, hz = v["hardpoint"]
        if (x < 0) == (hx < 0) and (z < 0) == (hz < 0):
            return c
    raise SystemExit(f"no corner for x={x} z={z}")


def put(b, off, old, new, what):
    cur = struct.unpack_from("<f", b, off)[0]
    if abs(cur - old) > 1e-4:
        raise SystemExit(f"{what} @{off:#x}: holds {cur}, expected {old}")
    struct.pack_into("<f", b, off, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stations")
    ap.add_argument("land")
    ap.add_argument("land_xml")
    ap.add_argument("physicsc")
    ap.add_argument("--out-land", required=True)
    ap.add_argument("--out-phys", required=True)
    a = ap.parse_args()
    st = json.load(open(a.stations))
    C = st["corners"]
    front = [v for v in C.values() if v["hardpoint"][2] < 0]
    rear = [v for v in C.values() if v["hardpoint"][2] > 0]
    avg = lambda vs, k: sum(v[k] for v in vs) / len(vs)
    hub_y = sum(v["hardpoint"][1] for v in C.values()) / 4

    # ---------------- land_global
    b = bytearray(open(a.land, "rb").read())
    root = ET.parse(a.land_xml).getroot()
    edits = 0
    for m in root.iter("member"):
        name = m.get("name")
        if name == "ground_clearance" and m.get("offset-in-file"):
            put(b, int(m.get("offset-in-file"), 16), float(m.text), hub_y, name); edits += 1
        if name in ("front_wheels", "rear_wheels") and m.get("gbltype") == "Structure":
            vs = front if name == "front_wheels" else rear
            for f in m:
                off = f.get("offset-in-file")
                if off is None:
                    continue
                off, old = int(off, 16), float(f.text)
                if f.get("name") == "radius":
                    put(b, off, old, avg(vs, "radius"), name + ".radius"); edits += 1
                elif f.get("name") == "rim_radius":
                    put(b, off, old, old * avg(vs, "radius") / 0.38, name + ".rim_radius"); edits += 1
                elif f.get("name") == "width":
                    put(b, off, old, avg(vs, "tyre_width"), name + ".width"); edits += 1
        if m.get("name") == "position" and m.get("type") == "IA[float]":
            fl = [f for f in m if f.get("offset-in-file")]
            x, y, z = (float(f.text) for f in fl)
            hp = C[corner_for(x, z, C)]["hardpoint"]
            for f, new in zip(fl, hp):
                put(b, int(f.get("offset-in-file"), 16), float(f.text), new, "hardpoint"); edits += 1
    print(f"land_global: {edits} floats written")
    if edits != 1 + 6 + 12:
        raise SystemExit(f"expected 19 land_global edits (1 clearance + 2x radius/rim/width + 4x3 hardpoint), made {edits}")
    open(a.out_land, "wb").write(bytes(b))

    # ---------------- physicsc station quads
    d = bytearray(open(a.physicsc, "rb").read())
    if d.find(b"hk_2014.1.0") != 40 or b"hknpExternMeshShape" not in d:
        raise SystemExit("not the Serpente Havok physicsc")
    hits = []
    for o in range(0, len(d) - 16, 4):
        x, y, z, w = struct.unpack_from("<ffff", d, o)
        if (abs(abs(x) - VANILLA_X) < 1e-5 and abs(y - VANILLA_Y) < 1e-5 and w == 1.0
                and any(abs(z - v) < 1e-3 for v in VANILLA_Z.values())):
            hits.append((o, x, z))
    if len(hits) != 4:
        raise SystemExit(f"expected 4 vanilla station quads, found {len(hits)}: {hits}")
    for o, x, z in hits:
        hp = C[corner_for(x, z, C)]["hardpoint"]
        struct.pack_into("<fff", d, o, *hp)
    open(a.out_phys, "wb").write(bytes(d))
    print("physicsc: 4 station quads at", [hex(o) for o, _, _ in hits], "->",
          {corner_for(x, z, C): C[corner_for(x, z, C)]["hardpoint"] for _, x, z in hits})


if __name__ == "__main__":
    main()
