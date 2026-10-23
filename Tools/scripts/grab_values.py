"""grab_values.py - derive the JC3 appearance constants from the Batmobile grab (GRB-6).

The appearance pipeline used three hand-set numbers: a paint gloss cap, an albedo gain and a glass
tint. This tool replaces them with values that are read from the shipped files:

    paint.gloss_cap   the vanilla JC3 body block's paint-channel gloss (the block the specs copy)
    paint.value       the authored BmAK paint colour (linear), no compensation
    paint.albedo_gain 1.0 - linear->sRGB is the only transform the files support (ALB-2's x4 removed)
    glass.tint        the authored BmAK paint colour (the canopy is tinted like the body)
    emissive.intensity  the authored Emissive_Intensity / EmissiveMultiply when present

Sources and hashes are written to `Research/BatmobileGrab/VALUES.json`; `factors.py` reads only that
file. Re-run after a grab or template change:

    python Tools/scripts/grab_values.py --write
    python Tools/scripts/grab_values.py           # print the current values
"""
import argparse
import glob
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "VALUES.json")
TEMPLATE_DIR = os.path.join(ROOT, "Working", "Serpente", "aaf", "models", "jc_vehicles", "01_land",
                            "v0300_car_kensington_sportsmuscle")
TEMPLATE = os.path.join(TEMPLATE_DIR, "sportsmuscle_body_lod1.rbm")
TEMPLATE_BLOCK = 6          # the body paint block the appearance specs use as their template


def _sha1(data):
    return hashlib.sha1(data).hexdigest()[:16]


def _named(tags, name):
    for t in tags or []:
        if t.get("name") == name:
            return t
    return None


def _array_items(t):
    return [i for i in (t or {}).get("items") or [] if isinstance(i, list)]


def _params(row, key):
    """ScalarParameterValues / VectorParameterValues -> {name: value} (value = float or vec4)."""
    out = {}
    t = _named(row.get("tags"), key)
    for item in _array_items(t):
        name = next((x.get("value") for x in item if x.get("type") == "NameProperty"), None)
        val = next((x.get("value") for x in item if x.get("type") in ("FloatProperty", "VectorProperty")), None)
        if val is None:
            # vector parameters serialise ParameterValue as a struct decoded to `floats`
            vtag = next((x for x in item if x.get("name") == "ParameterValue"), None)
            val = (vtag or {}).get("floats")
        if name and val is not None:
            out[name] = val
    return out


def _parent(g, row):
    """The MaterialInstanceConstant parent, resolved from the inline object reference."""
    for path, t in g.tags(row):
        if t.get("ref_class") == "MaterialInstanceConstant" and t.get("ref"):
            idx = t.get("value")
            for r in g.rows:
                if r.get("package") == row["package"] and r.get("index") == idx and r.get("tag_count"):
                    return r
    return None


def _with_parents(g, row):
    """Authored parameters, child overrides parent (mirrors factors.resolve)."""
    merged, seen = {}, 0
    while row is not None and seen < 8:
        for key in ("ScalarParameterValues", "VectorParameterValues"):
            for n, v in _params(row, key).items():
                merged.setdefault(n, v)       # child wins, so keep the first
        row = _parent(g, row)
        seen += 1
    return merged


def _body_material(g):
    """The painted body slot: a MaterialInstanceConstant whose name says Mainbody."""
    for r in g.find(class_="MaterialInstanceConstant"):
        if r.get("tag_count") and "mainbody" in r["name"].lower():
            if r.get("package") == "Playable_Batmobile_SF":
                return r
    for r in g.find(class_="MaterialInstanceConstant"):
        if r.get("tag_count") and "mainbody" in r["name"].lower():
            return r
    return None


def _emissive_intensity(g):
    rows = [r for r in g.find(class_="MaterialInstanceConstant")
            if r.get("tag_count") and "emissive" in r["name"].lower()]
    for r in rows:
        p = _with_parents(g, r)
        if "Emissive_Intensity" in p:
            return float(p["Emissive_Intensity"]), "scalar Emissive_Intensity on %s" % r["name"]
        if "EmissiveMultiply" in p:
            return float(p["EmissiveMultiply"]), "scalar EmissiveMultiply on %s" % r["name"]
    return 0.0, "no authored emissive scalar"


def _vanilla_paint():
    """Gloss and tint of the vanilla body block's paint channel (1 = TintColorR)."""
    import rbm_geom as R
    raw = open(TEMPLATE, "rb")
    data = raw.read()
    raw.close()
    b = R.decode(data).blocks[TEMPLATE_BLOCK]
    static = struct.unpack("<72f", b.static_params)
    dynamic = struct.unpack("<19f", b.dynamic_params)
    # static[0..3] = SpecularGloss vec4; dynamic[0..3] = TintColorR
    return round(float(static[1]), 4), [round(float(x), 4) for x in dynamic[:3]], _sha1(data)


def derive():
    import grab_model
    g = grab_model.Grab()
    body = _body_material(g)
    if body is None:
        raise SystemExit("grab has no Mainbody material instance")
    params = _with_parents(g, body)
    base = params.get("Material0_BaseColour") or params.get("Main_BaseColour")
    if not base:
        raise SystemExit("Mainbody material has no authored Material0_BaseColour")
    base = [round(float(x), 5) for x in base[:4]]
    adj = params.get("Diffuse_Adjust") or [1.0, 1.0, 1.0, 1.0]
    effective = [round(base[i] * float(adj[i]), 6) for i in range(3)]
    rough = float(params.get("Material0_Roughness", 0.0))
    gloss_vanilla, vanilla_tint, tsha = _vanilla_paint()

    def luma(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    gain = round(luma(vanilla_tint) / max(luma(effective), 1e-6), 4)
    emis, emis_src = _emissive_intensity(g)
    return {
        "schema": 1,
        "generated_by": "grab_values.py",
        "paint": {
            "gloss_cap": gloss_vanilla,
            "authored_gloss": round(1.0 - rough, 4),
            "base_colour": base,
            "effective_base_colour": effective,
            "albedo_gain": gain,
            "source": {
                "gloss_cap": "vanilla paint channel 1 of %s block %d (%.3f); authored BmAK gloss %.3f"
                             % (os.path.basename(TEMPLATE), TEMPLATE_BLOCK, gloss_vanilla, 1.0 - rough),
                "base_colour": "Material0_BaseColour on %s (via parent chain), x Diffuse_Adjust %s"
                               % (body["name"], adj[:3]),
                "albedo_gain": "vanilla paint tint luma %.4f / BmAK authored paint luma %.4f (GRB-6)"
                               % (luma(vanilla_tint), luma(effective)),
            },
        },
        "glass": {
            "tint": base[:3],
            "opacity_multiplier": 1.0,
            "source": "same authored paint colour as the body (canopy has no colour parameters)",
        },
        "vanilla": {"paint_gloss": gloss_vanilla, "paint_tint": vanilla_tint},
        "emissive": {
            "intensity": round(emis, 4),
            "source": emis_src,
        },
        "template": {"path": os.path.relpath(TEMPLATE, ROOT), "block": TEMPLATE_BLOCK, "sha1": tsha},
    }


def load(path=OUT):
    if not os.path.exists(path):
        raise SystemExit("%s missing - run `python Tools/scripts/grab_values.py --write`" % path)
    return json.load(open(path, encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write Research/BatmobileGrab/VALUES.json")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    v = derive()
    if a.write:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        json.dump(v, open(a.out, "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(a.out, ROOT))
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    main()
