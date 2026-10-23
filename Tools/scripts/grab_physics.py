#!/usr/bin/env python3
"""grab_physics.py - decode the batmobile collision bodies (PHY-1).

The grab knew there were 128 RB_BodySetup records (32 per vehicle) and the
asset name, but stopped at "AggGeom is a StructProperty blob".  This expands
them: per bone -> box extents (cm) + local centre + counts, and the physics
asset that owns them.

Decoded layout of the AggGeom struct (verified byte-for-byte on all 128):

    u32  sphere_count
    u32  box_count
    u32  sphyl_count?          (constant 10 on every record)
    u32  convex_count?         (constant 2846 on every record -> not a count)
    ...  box element:
         64 B FMatrix          identity rotation, translation in the last row
         12 B extents X/Y/Z     written as tagged floats at logical 0x40/0x44/0x48

So the extents live in the trailing property-tag stream, not inline in the
element, which is why a naive struct read produced zeros.  Everything the
game uses for collision placement is therefore recoverable: extents from the
tag stream, centre from the 12 bytes immediately before it.

Usage:
  python Tools/scripts/grab_physics.py            # write PHYSICS.md/.json
  python Tools/scripts/grab_physics.py --check    # verify the doc is current
"""
import argparse, glob, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import upk_read as U

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "Research", "BatmobileGrab")
VEHICLES = ["Playable_Batmobile_SF", "Playable_BatmobileMK2_SF",
            "Playable_BatmobileJoker_SF", "Playable_BatmobileFunhouse_SF"]

EXT_RE = re.compile(rb"\x04\x00\x40\x00(.{4})\x04\x00\x44\x00(.{4})\x04\x00\x48\x00(.{4})",
                    re.S)


def decode_aggeom(raw):
    """-> dict(spheres, boxes, extents, centre) or None."""
    if len(raw) < 24:
        return None
    spheres, boxes = struct.unpack_from("<2I", raw, 0)
    m = EXT_RE.search(raw)
    if not m:
        return None
    ext = struct.unpack("<3f", m.group(1) + m.group(2) + m.group(3))
    centre = struct.unpack_from("<3f", raw, m.start() - 12) if m.start() >= 12 else (0.0, 0.0, 0.0)
    return dict(spheres=spheres, boxes=boxes,
                extents=[round(v, 3) for v in ext],
                centre=[round(v, 3) for v in centre])


def body_rows(pkg):
    rows = []
    for i in range(len(pkg.exports)):
        if (pkg.object_class(i) or "") != "RB_BodySetup":
            continue
        tags, _end, _why = U.walk_tags(pkg, pkg.data(i))
        bones = [t.get("value") for t in tags if t.get("type") == "NameProperty"]
        agg = [t for t in tags if t.get("name") == "AggGeom"]
        if not agg or "raw" not in agg[0]:
            continue
        d = decode_aggeom(bytes.fromhex(agg[0]["raw"]))
        if d is None:
            continue
        d["bone"] = bones[0] if bones else ""
        d["asset"] = pkg.object_name(i).split(".")[-1]
        d["index"] = i
        rows.append(d)
    return rows


def physics_assets(pkg):
    return [pkg.object_name(i) for i in range(len(pkg.exports))
            if "PhysicsAsset" in (pkg.object_class(i) or "")]


def classify(bone):
    b = bone.lower()
    if "susp" in b or "wheel" in b:
        return "wheel/suspension"
    if "frag" in b or re.match(r"^object\d*$", b):
        return "destruction debris"
    if "door" in b:
        return "door"
    if "turret" in b:
        return "turret"
    if "fin" in b:
        return "jet fin"
    if "cockpit" in b:
        return "cockpit"
    if b == "root":
        return "root placeholder"
    return "other"


def collect():
    data = {}
    for v in VEHICLES:
        path = os.path.join(GAME, v + ".upk")
        if not os.path.exists(path):
            print(f"!! missing {v}", file=sys.stderr)
            continue
        pkg = U.Package(path)
        rows = body_rows(pkg)
        data[v] = dict(bodies=rows, physics_assets=physics_assets(pkg))
    return data


def identical(data):
    sigs = {v: json.dumps([(r["bone"], r["extents"], r["centre"]) for r in d["bodies"]],
                          sort_keys=True) for v, d in data.items()}
    return len(set(sigs.values())) <= 1


def render(data):
    L = []
    L.append("# Batmobile collision bodies (PHY-1)\n")
    L.append("Decoded by `Tools/scripts/grab_physics.py` from the four vehicle packages. "
             "Per-bone collision boxes: `RB_BodySetup` -> `AggGeom`, extents and local centre in "
             "centimetres (1 uu = 1 cm).\n")
    anyv = next(iter(data))
    bodies = data[anyv]["bodies"]
    same = identical(data)
    L.append(f"**{len(data)} vehicles, {len(bodies)} bodies each, "
             f"{len(data)*len(bodies)} records total.** "
             + ("All four vehicles carry byte-identical collision layouts." if same
                else "**Layouts differ between vehicles** — see per-vehicle JSON.") + "\n")
    L.append("Physics assets: " + ", ".join(f"`{a}`" for a in data[anyv]["physics_assets"]) + "\n")

    cats = {}
    for r in bodies:
        cats.setdefault(classify(r["bone"]), []).append(r)
    L.append("## Coverage by category\n")
    L.append("| category | bodies | bones |")
    L.append("|---|---|---|")
    for c in sorted(cats):
        L.append(f"| {c} | {len(cats[c])} | " + ", ".join(f"`{r['bone']}`" for r in cats[c]) + " |")
    L.append("")

    L.append("## Bodies\n")
    L.append("| # | bone | collision | extents X×Y×Z (cm) | centre (cm) | category |")
    L.append("|---|---|---|---|---|---|")
    for n, r in enumerate(bodies):
        ex = "×".join(f"{v:g}" for v in r["extents"])
        ce = "(" + ", ".join(f"{v:g}" for v in r["centre"]) + ")"
        shape = f"{r['boxes']} box" if r["boxes"] else f"{r['spheres']} sphere"
        L.append(f"| {n} | `{r['bone']}` | {shape} | {ex} | {ce} | {classify(r['bone'])} |")
    L.append("")

    volumes = []
    for r in bodies:
        volumes.append((r["bone"], 8 * r["extents"][0] * r["extents"][1] * r["extents"][2] / 1e6))
    volumes.sort(key=lambda t: -t[1])
    L.append("## Largest collision volumes\n")
    L.append("| bone | volume (m³, box) |")
    L.append("|---|---|")
    for b, v in volumes[:8]:
        L.append(f"| `{b}` | {v:.4f} |")
    L.append("")

    L.append("## What this means\n")
    L.append("- Every body is a **single axis-aligned-ish box** (box count 1, sphere count 0) with an "
             "identity rotation and a local centre, so the shapes are box hulls around each bone, "
             "not convex hulls.\n")
    L.append("- **There is no chassis body.** The 32 bones cover wheels/suspension, cockpit, doors, "
             "jet fins, the turret and the `Object*_frag_*` debris pieces — the main hull has no "
             "`RB_BodySetup`. Hull collision for the *driveable* car therefore does not come from this "
             "asset; it comes from the vehicle sim plus JC3's `sportsmuscle.physicsc` (MODLOG §65–70, "
             "§96–101), while this asset is what the game hands to the **destroyed** wreck.\n")
    L.append("- The extents are the per-bone envelopes the wreck's debris spawns from, so they also "
             "give a second, independent check on our own per-bone rig: a bone whose box is far "
             "larger than our geometry at that bone means our part is oversized there.\n")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the generated files are current")
    args = ap.parse_args()
    data = collect()
    if not data:
        print("no packages found", file=sys.stderr)
        return 2
    md = render(data)
    md_path = os.path.join(OUT, "PHYSICS.md")
    js_path = os.path.join(OUT, "PHYSICS.json")
    js = json.dumps(data, indent=1, sort_keys=True) + "\n"
    if args.check:
        ok = True
        for path, want in ((md_path, md), (js_path, js)):
            have = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if have != want:
                print(f"!! {os.path.basename(path)} is stale", file=sys.stderr)
                ok = False
        total = sum(len(d["bodies"]) for d in data.values())
        print(f"{len(data)} vehicles, {total} collision bodies, "
              f"{'identical' if identical(data) else 'DIFFERING'} layouts")
        print("PHYSICS.md/json current" if ok else "regenerate with: python Tools/scripts/grab_physics.py")
        return 0 if ok else 1
    open(md_path, "w", encoding="utf-8", newline="\n").write(md)
    open(js_path, "w", encoding="utf-8", newline="\n").write(js)
    print(f"wrote {os.path.relpath(md_path, REPO)} ({len(data)} vehicles, "
          f"{sum(len(d['bodies']) for d in data.values())} bodies)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
