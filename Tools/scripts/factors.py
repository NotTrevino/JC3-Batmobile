"""factors.py - translate each BmAK material's FULL interface into a JC3 block spec. MODLOG §79.

Why: up to test-066 every JC3 block silently inherited the Serpente template's material constants
(decal/dirt switches, dirt colour, damage tables, gloss vectors, tints). Here EVERY JC3 input is set
by an explicit rule and tagged with its source, and EVERY BmAK factor gets a disposition; an
unhandled BmAK parameter fails the run.

Source tags:  bmak:<param>   value taken/derived from that BmAK parameter
              neutral        BmAK has nothing to carry over; JC3's no-op value
              vanilla:<path> a game-shared JC3 texture used as a neutral input (dummies)
              generated      a texture this tool synthesises (solid colour) from BmAK values
Disposition:  mapped -> <JC3 input> | approximated (<how>) | no-jc3-equivalent (<why>) |
              missing-on-disk | engine-global (<JC3 system that owns it>)

BmAK side (UE3 dumps, *.props.txt): parent chains MIC -> ... -> Material3 master; NAMED
Texture/Scalar/Vector parameter overrides; masters give BlendMode / TwoSided / OpacityMaskClipValue
and ReferencedTextures. Expression wiring is not in the dumps, so semantics come from the names.
JC3 side (carpaintmm.fb.txt reflection): CarPaintStaticMaterialParams (18 float4) + 7 Support
floats + CarPaintDynamicMaterialParams (TintColor R/G/B + overrides); samplers s0 Diffuse,
s1 Normal, s2 PropertyMap, s3 TintMap, s4-s9 damage/dirt/decal (shared). Channel semantics
INFERRED from vanilla data (§78): PropertyMap RGB selects material channels 1-3 (black = 0), each
channel's gloss/metallic/clearcoat = component N of the 4-vectors; TintMap RGB = amount of tint
colour R/G/B. BmAK's Material_Separation_Mask -> MaterialN is the same structure.

Usage: python factors.py <pskx> <src_dir> -o factors.json [--report coverage.md]
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psk2rbm as P  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("texmatch", os.path.join(os.path.dirname(os.path.abspath(__file__)), "_texmatch.py"))
TM = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(TM)

STATIC = ["SpecularGloss", "Metallic", "ClearCoat", "Emissive", "DiffuseWrap", "DirtParams", "DirtBlend",
          "DirtColor", "DecalCount", "DecalWidth", "Decal1Color", "Decal2Color", "Decal3Color", "Decal4Color",
          "DecalBlend", "Damage", "DamageBlend", "DamageColor"]
SUPPORT = ["SupportDecals", "SupportDmgBlend", "SupportLayered", "SupportOverlay", "SupportRotating",
           "SupportDirt", "SupportSoftTint"]
FLAG = {"SUPPORT_DECALS": 0x1, "SUPPORT_DAMAGE_BLEND": 0x2, "SUPPORT_DIRT": 0x4, "SUPPORT_PALETTE_FILE": 0x8,
        "SUPPORT_SOFT_TINT": 0x10, "SUPPORT_LAYERED": 0x20, "SUPPORT_OVERLAY": 0x40,
        "DISABLE_BACKFACE_CULLING": 0x80, "TRANSPARENCY_ALPHABLENDING": 0x100, "TRANSPARENCY_ALPHATESTING": 0x200}
NEUTRAL_NRM = "textures/00_general/dummy/a00_dummy_flat_nrm.ddsc"
NEUTRAL_BLACK = "textures/00_general/dummy/a00_dummy_black_mpm.ddsc"   # black: channel 0 / no tint

# ---------------------------------------------------------------- BmAK side

def parse_props(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    ref = lambda s: s.split("'")[1].split(".")[-1] if "'" in s else s
    out = {"parent": None, "tex": {}, "sc": {}, "vec": {}, "settings": {}, "referenced": []}
    m = re.search(r"^Parent = (\S+)", t, re.M)
    if m:
        out["parent"] = ref(m.group(1))
    for val, name in re.findall(r"ParameterValue\s*=\s*Texture2D'([^']*)'\s*ParameterName\s*=\s*([A-Za-z0-9_]+)", t):
        out["tex"][name] = val.split(".")[-1]
    for name in re.findall(r"ParameterValue\s*=\s*\n?\s*ParameterName\s*=\s*([A-Za-z0-9_]+)", t):
        out["tex"].setdefault(name, None)                       # declared, no texture (inherits)
    for val, name in re.findall(r"ParameterValue\s*=\s*([-0-9.eE+]+)\s*ParameterName\s*=\s*([A-Za-z0-9_]+)", t):
        out["sc"][name] = float(val)
    for val, name in re.findall(r"ParameterValue\s*=\s*\{\s*R=([^}]*)\}\s*ParameterName\s*=\s*([A-Za-z0-9_]+)", t):
        out["vec"][name] = [float(x.split("=")[-1]) for x in ("R=" + val).split(",")]
    for k in ("BlendMode", "TwoSided", "OpacityMaskClipValue", "bIsMasked"):
        m = re.search(r"^%s\s*=\s*(.*)$" % k, t, re.M)
        if m:
            out["settings"][k] = m.group(1).strip()
    out["referenced"] = [x.split(".")[-1] for x in re.findall(r"ReferencedTextures\[\d+\]\s*=\s*Texture2D'([^']*)'", t)]
    return out


def load_bmak(src):
    props = {os.path.basename(p)[:-len(".props.txt")]: parse_props(p)
             for p in glob.glob(os.path.join(src, "**", "*.props.txt"), recursive=True)}
    files = {os.path.splitext(os.path.basename(f))[0]: f
             for f in glob.glob(os.path.join(src, "**", "*.tga"), recursive=True)}
    return props, files


def resolve(mat, props):
    """merged interface: master first, then each instance overriding down to `mat`"""
    chain, m = [], mat
    while m in props and m not in chain and len(chain) < 8:
        chain.append(m)
        m = props[m]["parent"]
    if m and m not in props:
        chain.append(m + " (no dump)")
    r = {"chain": chain, "tex": {}, "sc": {}, "vec": {}, "settings": {}, "referenced": [], "src": {}}
    for c in reversed([c for c in chain if c in props]):
        p = props[c]
        for k in ("tex", "sc", "vec"):
            for n, v in p[k].items():
                if v is not None or n not in r[k]:
                    r[k][n] = v
                    r["src"][k + ":" + n] = c
        r["settings"].update(p["settings"])
        r["referenced"] += p["referenced"]
    return r

# ---------------------------------------------------------------- disposition rules (every factor)

def _chan(name):
    m = re.search(r"Material(\d)", name)
    return int(m.group(1)) if m else None


RULES = [  # (kind, regex, disposition, target)   kind: tex | sc | vec
    ("tex", r"^(Colour_Map|Texture_Diffuse)$", "mapped", "s0 Diffuse (BC1)"),
    ("tex", r"^(Normal_Map|Texture_Normal|Normal_Map_Lacquer|Normal)$", "mapped", "s1 Normal (BC5); one normal per block, priority Normal_Map > Texture_Normal > Normal_Map_Lacquer > Normal"),
    ("tex", r"^Material_Separation_Mask$", "mapped", "s2 PropertyMap + s3 TintMap (RGB -> material channels 1-3)"),
    ("tex", r"^(Ref_n_Rough_Map|Texture_Ref_Rough)$", "approximated", "per-pixel reflectivity/roughness -> material-level gloss (JC3 varies properties only by channel)"),
    ("tex", r"^Emissive(_Map)?$", "approximated", "emissive mask -> material-level m_Emissive (JC3 emissive mask channel not decoded)"),
    ("tex", r"^OpacityMap$", "mapped", "glass -> Window dif alpha (BC3, x Glass_Opacity)"),
    ("tex", r"^Mask$", "approximated", "glass layer mask: no per-layer Window slots; carried as the material-level tint only"),
    ("tex", r"Microdetail", "no-jc3-equivalent", "tiling micro-detail (no CarPaintMM detail slot; could be baked into s1)"),
    ("tex", r"^Colour_Ramp_Map$", "no-jc3-equivalent", "colour ramp lookup (and the ramp files are missing-on-disk)"),
    ("tex", r"^Anisotropic$", "no-jc3-equivalent", "anisotropic highlight ramp"),
    ("tex", r"^Damage_Chapter_Mask$", "no-jc3-equivalent", "story-chapter damage reveal (JC3 damage is hit-driven: SupportDmgBlend 0)"),
    ("sc", r"^Material\d_Roughness$|^Roughness_Multiplier$", "mapped", "SpecularGloss[channel] = 1 - roughness (x multiplier)"),
    ("sc", r"Metalicity", "mapped", "Metallic[channel]"),
    ("sc", r"Reflectivity", "approximated", "dielectric reflectance: JC3 uses a fixed F0; kept only as metallic when no Metalicity is given and value > 0.5"),
    ("sc", r"^Material\d_Microdetail_Size$|^MicroDetail|Microdetail_Size", "no-jc3-equivalent", "micro-detail tiling size"),
    ("sc", r"^Glass_", "approximated", "glass response -> Window block (params not decoded: vanilla glass)"),
    ("sc", r"^Mud|^Damage_[Dd]irt|^Damage_Dirt", "engine-global", "JC3 dirt (dynamic per object); BmAK mud is chapter-scripted: SupportDirt 0, DirtColor recorded"),
    ("sc", r"^Rain|Wetness|^RainR", "engine-global", "JC3 weather/wetness system"),
    ("sc", r"^Emissive|^EmissiveMultiply$", "mapped", "m_Emissive intensity (emissive materials)"),
    ("sc", r"^EMP", "no-jc3-equivalent", "story EMP effect"),
    ("sc", r"^Vector_Displacement", "no-jc3-equivalent", "tessellated displacement"),
    ("sc", r"^Diffuse_Adjust$", "mapped", "multiplies the base colour / diffuse"),
    ("sc", r"^[Ff]ake$|^glass_smudges$", "no-jc3-equivalent", "editor/fake helper or smudge overlay"),
    ("vec", r"^Material\d_Base[Cc]olour$", "mapped", "channel colour: 0 -> s0 solid (generated) when no Colour_Map; 1-3 -> TintColor R/G/B"),
    ("vec", r"^Main_BaseColour", "mapped", "fallback channel-0 colour"),
    ("vec", r"^Roughness_per_material$|^Roughness_Base_Level$", "mapped", "SpecularGloss[0..3] fallback (1 - roughness per channel)"),
    ("vec", r"^underlayer_Detail_to_Roughness$", "no-jc3-equivalent", "micro-detail -> roughness modulation"),
    ("vec", r"Anisotropic|^Fake_Aniso", "no-jc3-equivalent", "anisotropic highlights"),
    ("vec", r"^Mud|^Damage_Dirt_Colour$", "engine-global", "JC3 dirt colour (recorded in DirtColor, dirt disabled)"),
    ("vec", r"^Batman_Rain|^Rain_", "engine-global", "JC3 weather"),
    ("vec", r"^CodeHeadlightColor$|^LightGroup", "engine-global", "JC3 lights module (CarLight blocks + lights.vmodc)"),
    ("vec", r"^Diffuse_Adjust$", "mapped", "multiplies the base colour / diffuse"),
    ("vec", r"^Art$", "no-jc3-equivalent", "editor helper"),
]


def disposition(kind, name):
    for k, rx, d, target in RULES:
        if k == kind and re.search(rx, name):
            return d, target
    return None, None

# ---------------------------------------------------------------- JC3 spec

# GRB-6: every appearance constant comes from `Research/BatmobileGrab/VALUES.json`, which
# `grab_values.py` derives from the grab and the shipped JC3 body template. Nothing below is
# hand-tuned; re-run that tool after a grab/template change.
import grab_values as GV  # noqa: E402

VALUES = GV.load()
GLASS_TINT = VALUES["glass"]["tint"]
GLOSS_CAP = VALUES["paint"]["gloss_cap"]
ALBEDO_GAIN = VALUES["paint"]["albedo_gain"]


def srgb8(c):
    """linear 0..1 -> the 8-bit sRGB value a .ddsc dif must hold.

    UE material colour parameters (BaseColour, Colour, Main_BaseColour) are linear; a JC3 dif is
    sampled as sRGB (vanilla dif headers carry flag 8). Writing the raw channel x 255 stores a
    *linear* number in a *sRGB* slot, and the engine decodes it again - the Batmobile paint
    0.0567 linear became byte 14 instead of 67, i.e. 12x too dark in linear terms, and the car
    rendered black in daylight (MODLOG §105)."""
    c = max(0.0, min(1.0, float(c)))
    s = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return round(s * 255) / 255


def jc3_spec(mat, r, tex_files, fallbacks=None, glass_override=False, tint=None):
    fallbacks = fallbacks or {}
    S = {"material": mat, "chain": r["chain"], "inputs": {}, "textures": {}, "flags": [], "dispositions": [],
         "warnings": []}
    src = lambda k, n: f"bmak:{n} ({r['src'].get(k + ':' + n, '?')})"
    put = lambda key, val, source: S["inputs"].__setitem__(key, {"value": val, "source": source})
    blend = r["settings"].get("BlendMode", "BLEND_Opaque (0)")
    is_glass = glass_override or "OpacityMap" in r["tex"] or any(n.startswith("Glass_") for n in r["sc"])
    S["block"] = "Window" if is_glass else "CarPaintMM"

    # every BmAK factor's disposition (unhandled -> recorded, the run fails on any)
    for kind in ("tex", "sc", "vec"):
        for n, v in sorted(r[kind].items()):
            d, target = disposition(kind, n)
            if kind == "tex" and v is not None and v not in tex_files and d == "mapped":
                d, target = "missing-on-disk", f"{target} -- texture {v} not in the dump"
            S["dispositions"].append({"factor": f"{kind}:{n}", "value": v, "disposition": d or "UNHANDLED",
                                      "target": target, "from": r["src"].get(kind + ":" + n)})
    S["dispositions"].append({"factor": "setting:BlendMode", "value": blend, "disposition": "mapped",
                              "target": "Window (translucent glass) / ALPHABLENDING 0x100 / ALPHATESTING 0x200"})
    S["dispositions"].append({"factor": "setting:TwoSided", "value": r["settings"].get("TwoSided"),
                              "disposition": "mapped", "target": "DISABLE_BACKFACE_CULLING 0x80"})
    if is_glass:
        # Window dif: BmAK glass has no colour map, so the JC3 dif is a BC3 whose ALPHA is the
        # opacity map x Glass_Opacity and whose RGB is a tint (material vector if it has one, else
        # the build's paint colour). The vanilla Window dif is the same format: BC3 / format 77.
        op = next((r["tex"][n] for n in ("OpacityMap", "Mask") if r["tex"].get(n) in tex_files), None)
        nrm = next((r["tex"][n] for n in ("Normal", "Texture_Normal", "Normal_Map")
                    if r["tex"].get(n) in tex_files), None)
        base = r["vec"].get("Main_BaseColour") or r["vec"].get("Colour") or tint or GLASS_TINT
        base = [srgb8(x) for x in base[:3]] + list(base[3:])          # linear param -> sRGB byte
        mult = float(r["sc"].get("Glass_Opacity", 1.0))
        if op:
            S["textures"]["s0"] = {"tga": tex_files[op], "kind": "glass",
                                    "tint": [float(x) for x in base[:3]], "alpha_multiplier": mult,
                                    "source": f"bmak:{op} (alpha x Glass_Opacity {mult:g}); tint {base[:3]}"}
            S["dispositions"].append({
                "factor": "derived:WindowDif", "value": f"BC3 {base[:3]} @ alpha x{mult:g}",
                "disposition": "mapped",
                "target": "Window slot 0 (DXT5: RGB tint + opacity map alpha x Glass_Opacity)"})
        else:
            S["warnings"].append("glass with no opacity map on disk -> Window keeps the template dif")
        if nrm:
            S["textures"]["s1"] = {"tga": tex_files[nrm], "kind": "normal", "source": "bmak:" + nrm}
        else:
            S["warnings"].append("glass with no normal map on disk -> Window keeps the dummy normal")
        return S
    # materials whose chain binds no colour/normal/roughness texture (anonymous master defaults):
    # tagged name-match fallback against the files on disk (_texmatch, data-derived stopwords)
    fallback = {}
    if not any(r["tex"].get(n) in tex_files for n in ("Colour_Map", "Texture_Diffuse", "Normal_Map",
                                                      "Texture_Normal", "Normal_Map_Lacquer", "Normal")):
        fb = fallbacks.get(mat, {})
        for role, (tex, path) in fb.items():
            if path and role.startswith("fallback:"):
                fallback[role.split(":")[1]] = tex

    # ---- channel properties (4-vectors: component N = material channel N)
    rough, rsrc = [None] * 4, ["neutral"] * 4
    for vname in ("Roughness_Base_Level", "Roughness_per_material"):        # later wins
        if vname in r["vec"]:
            for c in range(4):
                rough[c], rsrc[c] = r["vec"][vname][c], src("vec", vname)
    for c in range(4):
        n = f"Material{c}_Roughness"
        if n in r["sc"]:
            rough[c], rsrc[c] = r["sc"][n], src("sc", n)
    mul = r["sc"].get("Roughness_Multiplier", 1.0)
    gloss = [round(1.0 - min(1.0, (x if x is not None else 1.0) * mul), 4) for x in rough]
    # MAT-1: BmAK's near-mirror roughness (gloss 0.75-0.98) is authored for a rain-wet night scene with
    # a real environment probe; JC3 has no clearcoat input to spread that highlight, so the same numbers
    # render as wet black plastic in daylight. The vanilla Serpente body block - which reads correctly
    # in this engine - sits at gloss 0.400 on its paint channel, and in-game screenshots of test-079
    # confirm the mirror sheen. Cap gloss at the vanilla paint level instead of copying UE roughness.
    gloss = [min(g, GLOSS_CAP) for g in gloss]
    put("static.SpecularGloss", gloss, [((s if rough[c] is not None else "neutral (no roughness: gloss 0)")
                                        + (" capped to the vanilla paint gloss %.2f (GRB-6, VALUES.json)" % GLOSS_CAP
                                           if (rough[c] is not None and 1.0 - min(1.0, rough[c] * mul) > GLOSS_CAP)
                                           else ""))
                                       for c, s in enumerate(rsrc)])
    metal, msrc = [0.0] * 4, ["neutral (dielectric)"] * 4
    for c in range(4):
        for n in (f"Material{c}_Metalicity", "Metalicity"):
            if n in r["sc"]:
                metal[c], msrc[c] = r["sc"][n] * r["sc"].get("Metalicity_Multiplier", 1.0), src("sc", n)
                break
        else:
            n = f"Material{c}_Reflectivity"
            if r["sc"].get(n, 0) > 0.5:
                metal[c], msrc[c] = r["sc"][n], src("sc", n) + " (reflectivity > 0.5 read as metallic)"
    put("static.Metallic", metal, msrc)
    lac = "Normal_Map_Lacquer" in r["tex"]
    put("static.ClearCoat", [1.0 if lac else 0.0] * 4,
        src("tex", "Normal_Map_Lacquer") + " (lacquer layer)" if lac else "neutral (no lacquer)")
    emis = r["sc"].get("Emissive_Intensity", r["sc"].get("EmissiveMultiply", 0.0)) \
        if any(n.startswith("Emissive") for n in r["tex"]) else VALUES["emissive"]["intensity"]
    put("static.Emissive", [emis] * 4, "bmak:Emissive_* (material level)" if emis else "neutral")
    put("static.DiffuseWrap", [0.0] * 4, "neutral (no wrap lighting in BmAK params)")
    dirt = r["vec"].get("Mud_Colour")
    put("static.DirtParams", [0.0, 0.0, 0.0, 0.0], "neutral (dirt disabled)")
    put("static.DirtBlend", [0.0, 0.0, 0.0, 0.0], "neutral (dirt disabled)")
    put("static.DirtColor", dirt or [0.0, 0.0, 0.0, 1.0], src("vec", "Mud_Colour") + " (recorded; dirt disabled)" if dirt else "neutral")
    for n in ("DecalCount", "DecalWidth", "Decal1Color", "Decal2Color", "Decal3Color", "Decal4Color", "DecalBlend"):
        put("static." + n, [0.0] * 4, "neutral (BmAK has no livery-decal system; its decals are geometry)")
    dcol = r["vec"].get("Damage_Dirt_Colour")
    put("static.Damage", [0.0] * 4, "neutral (damage blend disabled)")
    put("static.DamageBlend", [0.0] * 4, "neutral (damage blend disabled)")
    put("static.DamageColor", dcol or [0.0, 0.0, 0.0, 1.0], src("vec", "Damage_Dirt_Colour") + " (recorded)" if dcol else "neutral")
    for n in SUPPORT:
        put("support." + n, 0.0, "neutral (switch off: " + {
            "SupportDecals": "no livery decals", "SupportDmgBlend": "chapter damage, not hit damage",
            "SupportLayered": "no layer map", "SupportOverlay": "no overlay map", "SupportRotating": "unused",
            "SupportDirt": "mud is chapter-scripted", "SupportSoftTint": "tints come from the TintMap"}[n] + ")")

    # ---- per-pixel roughness maps -> material-level values where no scalar gave them.
    # Channel packing INFERRED from physical plausibility (§79): tyre _R R=0.95 G=0.21 B=0.12
    # (rough, low spec, non-metal rubber), disc _R R=0.04 B=0.43 (smooth metallic) -> R roughness,
    # G reflectance, B metalness. Maps whose R channel is dead (std 0: the _S maps) are not read.
    rr = next((r["tex"][n] for n in ("Ref_n_Rough_Map", "Texture_Ref_Rough") if r["tex"].get(n) in tex_files), None)
    rr = rr or (fallback.get("r") if fallback else None)
    if rr and rough == [None] * 4:
        import numpy as np
        from PIL import Image
        px = np.asarray(Image.open(tex_files[rr]).convert("RGB"), np.float32).reshape(-1, 3) / 255.0
        if px[:, 0].std() > 0.01:
            g = round(1.0 - float(px[:, 0].mean()), 4)
            mt = round(float(px[:, 2].mean()), 4)
            put("static.SpecularGloss", [g] * 4, f"approximated: 1 - mean(R) of {rr} (R=roughness, inferred)")
            put("static.Metallic", [mt] * 4, f"approximated: mean(B) of {rr} (B=metalness, inferred)")
            gloss, metal = [g] * 4, [mt] * 4
        else:
            S["warnings"].append(f"{rr}: R channel dead (std {px[:, 0].std():.3f}); packing unknown, not read")

    # ---- colours: channel 0 = base (diffuse), channels 1-3 = TintColor R/G/B
    adj = r["vec"].get("Diffuse_Adjust", [r["sc"].get("Diffuse_Adjust", 1.0)] * 3 + [1.0])
    col, csrc = [None] * 4, ["neutral"] * 4
    if "Main_BaseColour" in r["vec"]:
        col[0], csrc[0] = r["vec"]["Main_BaseColour"], src("vec", "Main_BaseColour")
    for c in range(4):
        for n in (f"Material{c}_BaseColour", f"Material{c}_Basecolour"):
            if n in r["vec"]:
                col[c], csrc[c] = r["vec"][n], src("vec", n)
    cl = lambda v: [round(min(1.0, v[i] * adj[i]), 5) for i in range(3)] + [1.0]
    for i, k in enumerate(("TintColorR", "TintColorG", "TintColorB")):
        c = i + 1
        put("dynamic." + k, cl(col[c]) if col[c] else [0.0, 0.0, 0.0, 0.0],
            csrc[c] + (" x Diffuse_Adjust" if "Diffuse_Adjust" in r["vec"] or "Diffuse_Adjust" in r["sc"] else "")
            if col[c] else "neutral (channel unused)")
    put("dynamic.Overrides", [gloss[1], metal[1], S["inputs"]["static.ClearCoat"]["value"][1]],
        "= channel 1 properties (vanilla non-palette blocks do the same)")

    # ---- textures
    d = next((r["tex"][n] for n in ("Colour_Map", "Texture_Diffuse") if r["tex"].get(n) in tex_files), None)
    if d:
        S["textures"]["s0"] = {"tga": tex_files[d], "kind": "colour", "source": "bmak:" + d}
    elif fallback.get("d"):
        S["textures"]["s0"] = {"tga": tex_files[fallback["d"]], "kind": "colour",
                               "source": "fallback:name-match " + fallback["d"] + " (chain binds no colour map)"}
    elif col[0]:
        S["textures"]["s0"] = {"solid": [srgb8(x * ALBEDO_GAIN) for x in cl(col[0])[:3]] + [1.0],
                          "kind": "colour",
                          "source": "generated from " + csrc[0] +
                                    " (x%.2f, GRB-6: vanilla paint luma / authored paint luma)"
                                    % ALBEDO_GAIN}
    else:
        S["textures"]["s0"] = {"solid": [0.5, 0.5, 0.5, 1.0], "kind": "colour",
                               "source": "neutral (no colour data: mid grey)"}
        S["warnings"].append("no colour data at all")
    nrm = next((r["tex"][n] for n in ("Normal_Map", "Texture_Normal", "Normal_Map_Lacquer", "Normal")
                if r["tex"].get(n) in tex_files), None)
    if not nrm and fallback.get("n"):
        S["textures"]["s1"] = {"tga": tex_files[fallback["n"]], "kind": "normal",
                               "source": "fallback:name-match " + fallback["n"] + " (chain binds no normal map)"}
    else:
        S["textures"]["s1"] = ({"tga": tex_files[nrm], "kind": "normal", "source": "bmak:" + nrm} if nrm else
                               {"vanilla": NEUTRAL_NRM, "source": "vanilla flat normal (neutral)"})
    sep = r["tex"].get("Material_Separation_Mask")
    if sep in tex_files:
        S["textures"]["s2"] = {"tga": tex_files[sep], "kind": "mask", "source": "bmak:" + sep + " (channels 1-3)"}
        S["textures"]["s3"] = {"tga": tex_files[sep], "kind": "mask", "source": "bmak:" + sep + " (tint R/G/B)"}
    else:
        why = "neutral: no separation mask -> channel 0 everywhere"
        if sep:
            why = f"missing-on-disk: {sep} -> channel 0 everywhere"
        elif any(n.startswith(("Material1_", "Material2_", "Material3_")) for n in list(r["sc"]) + list(r["vec"])):
            refs = [t for t in r["referenced"] if re.search("mask", t, re.I) and not re.search("damage", t, re.I)]
            why = f"missing-on-disk: channels 1-3 are parameterised but the mask is the master's default ({refs or 'unnamed'}) -> channel 0"
            S["warnings"].append(why)
        S["textures"]["s2"] = {"vanilla": NEUTRAL_BLACK, "source": why}
        S["textures"]["s3"] = {"vanilla": NEUTRAL_BLACK, "source": why}

    # ---- flags (every bit decided)
    fl = 0
    if r["settings"].get("TwoSided", "false").lower() == "true":
        fl |= FLAG["DISABLE_BACKFACE_CULLING"]
    if "Masked" in blend:
        fl |= FLAG["TRANSPARENCY_ALPHATESTING"]
    if "Translucent" in blend:
        fl |= FLAG["TRANSPARENCY_ALPHABLENDING"]
    S["flags"] = {"value": fl, "source": f"bmak BlendMode={blend}, TwoSided={r['settings'].get('TwoSided')}; "
                  "decals/dirt/damage/palette/soft-tint/layered/overlay off (see support.*); IS_DEFORM off (user rule)"}
    if fl & FLAG["TRANSPARENCY_ALPHATESTING"]:
        # cut-out source: an opacity binding, the material's own "_A" texture, or s0's own alpha
        from PIL import Image
        a_tex = next((r["tex"][n] for n in ("OpacityMap", "Mask") if r["tex"].get(n) in tex_files), None)
        a_src = "bmak:" + a_tex if a_tex else None
        if not a_tex and fallback.get("a"):
            a_tex, a_src = fallback["a"], "fallback:name-match " + fallback["a"]
        s0 = S["textures"]["s0"]
        if a_tex:
            s0["alpha_tga"] = tex_files[a_tex]
            s0["alpha_source"] = a_src
        elif "tga" in s0 and Image.open(s0["tga"]).mode in ("RGBA", "LA"):
            s0["alpha_source"] = "s0's own alpha channel"
        else:
            fl &= ~FLAG["TRANSPARENCY_ALPHATESTING"]
            S["flags"]["value"] = fl
            S["flags"]["source"] += "; ALPHATESTING dropped: missing-on-disk (no opacity source)"
            S["warnings"].append("masked in BmAK but no opacity source on disk -> rendered opaque")
    return S

# ---------------------------------------------------------------- run

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pskx")
    ap.add_argument("src_dir")
    ap.add_argument("-o", required=True)
    ap.add_argument("--report")
    a = ap.parse_args()
    _, _, F, mats = P.read_pskx(a.pskx)
    props, files = load_bmak(a.src_dir)
    used = sorted({mats[i] for i in set(int(x) for x in F["m"])})
    fallbacks = TM.texture_bindings(used, a.src_dir)
    specs, unhandled = {}, []
    for m in used:
        r = resolve(m, props)
        s = jc3_spec(m, r, files, fallbacks)
        specs[m] = s
        unhandled += [f"{m}: {d['factor']}" for d in s["dispositions"] if d["disposition"] == "UNHANDLED"]
    json.dump({"materials": specs, "unhandled": unhandled}, open(a.o, "w"), indent=1)
    if a.report:
        write_report(specs, a.report)
    n_f = sum(len(s["dispositions"]) for s in specs.values())
    print(f"{len(specs)} materials, {n_f} BmAK factors, {len(unhandled)} unhandled -> {a.o}")
    for u in unhandled:
        print("  UNHANDLED", u)
    if unhandled:
        sys.exit(1)


def write_report(specs, path):
    L = ["# BmAK -> JC3 factor coverage (generated by factors.py)", ""]
    for m, s in specs.items():
        L += [f"## {m}  ->  {s['block']}", f"chain: {' -> '.join(s['chain'])}", ""]
        L += ["| BmAK factor | value | disposition | JC3 target | from |", "|---|---|---|---|---|"]
        for d in s["dispositions"]:
            L.append(f"| {d['factor']} | {d['value']} | {d['disposition']} | {d['target']} | {d.get('from') or ''} |")
        if s["inputs"]:
            L += ["", "| JC3 input | value | source |", "|---|---|---|"]
            for k, v in s["inputs"].items():
                L.append(f"| {k} | {v['value']} | {v['source']} |")
        if s["textures"]:
            L += ["", "| JC3 slot | content | source |", "|---|---|---|"]
            for k, v in s["textures"].items():
                content = os.path.basename(v.get("tga", "")) or v.get("vanilla") or f"solid {v.get('solid')}"
                L.append(f"| {k} | {content} | {v['source']} |")
        if s.get("flags"):
            L += ["", f"flags 0x{s['flags']['value']:04X}: {s['flags']['source']}"]
        for w in s["warnings"]:
            L.append(f"- WARNING: {w}")
        L.append("")
    open(path, "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    main()
