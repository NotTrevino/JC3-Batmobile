"""grab_lights.py - the BmAK VehicleLights rig -> a JC3 VehicleDynamicLight plan (GRB-8).

Input is the grab (`grab_model.py lights`): every repeated `VehicleLights` struct on each
`RVehicleBatmobile`, with the enum light type the cooker kept (`VEHLT_HeadLight`, ...), the SOCKET it
hangs on, that socket's bone resolved from the exported `Batmobile_V2.pskx` skeleton, and the resolved
component classes. This tool joins it with

  * the vanilla JC3 lights module (`Working/Lights/serpente_lights.xml`, ConvertAdf export of the
    sportsmuscle `*_lights.vmodc`) for the per-behavior field values LGT-1 has to write, and
  * the assembled model's part list (`Working/Assembled/assembly.json`) for the JC3 part each light
    belongs to.

and writes

    Research/BatmobileGrab/LIGHTS.json   one entry per light, with its JC3 destination
    Research/BatmobileGrab/LIGHTS.md     the same as a review table + dispositions

Nothing is invented. A light whose socket does not exist in the shipped mesh is reported as
`orphan-socket`; a JC3 anchor that the assembled model does not have yet is reported as
`needs-lig-bone` rather than written as if it worked.

Usage:
    python Tools/scripts/grab_lights.py --write
    python Tools/scripts/grab_lights.py --check
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_model          # noqa: E402
import pskx_parts as PX    # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MESH = os.path.join(ROOT, "Working", "Appearance", "grab", "Playable_Batmobile_SF",
                    "SkeletalMesh3", "Batmobile_V2.pskx")
VANILLA = os.path.join(ROOT, "Working", "Lights", "serpente_lights.xml")
ASSEMBLY = os.path.join(ROOT, "Working", "Assembled", "assembly.json")

# BmAK type enum -> (JC3 behavior, disposition). The enum names are read from the ByteProperty FNames,
# so this table is the whole mapping; an unknown value is an error, not a silent fallback.
TYPES = {
    "VEHLT_HeadLight": ("HeadLight", "mapped"),
    "VEHLT_TailLight": ("TailLight", "mapped"),
    "VEHLT_BattleModeLight": ("HeadLight", "approximated: battle-mode spotlight has no JC3 behavior"),
    "VEHLT_ForensicsLight": (None, "no-jc3-equivalent: crime-scene scan light"),
    "VEHLT_Interior": ("TailLight", "approximated: interior accent, no JC3 behavior"),
    "VEHLT_BootLight": ("TailLight", "approximated: boot light, no JC3 behavior"),
}

# BmAK component class -> (JC3 destination, disposition)
COMPONENTS = {
    "SpotLightComponent": ("VehicleDynamicLight", "mapped"),
    "PointLightComponent": ("VehicleDynamicLight", "mapped"),
    "LensFlareComponent": ("none", "no-jc3-equivalent: JC3 light module has no flare"),
    "RHelicopterSpotLightComponent": ("VehicleDynamicLight", "approximated: spotlight, no helicopter mode"),
}

# Fields LGT-1 writes into each VehicleDynamicLight (order of the vanilla struct; offsets from the
# type definition in serpente_lights.xml).
JC3_FIELDS = ("behavior", "part", "part_index", "diffuse", "range", "falloff_start", "near_cap",
              "multiplier", "min_luminosity", "light_type", "blinking", "angle", "cast_shadows",
              "projected_texture_index", "volumetric_mode", "volume_intensity", "uvscale",
              "deformable_transform", "preset_id")


def _socket_behavior(socket):
    s = (socket or "").lower()
    if "brake" in s:
        return "TailLight", "inferred: brake lamp shares the tail behavior"
    if "head" in s:
        return "HeadLight", "inferred from socket name (type stripped by the cooker)"
    if "wheel" in s:
        return "TailLight", "inferred: wheel accent light"
    if "signal" in s:
        return ("LeftSignal" if "left" in s else "RightSignal"), "inferred from socket name"
    if "reverse" in s:
        return "Reverse", "inferred from socket name"
    return None, "no-jc3-equivalent: type stripped and socket name carries no behavior"


def part_for(bone):
    """Shipped .epe part for a bone. Only geometry that actually spins with the wheel goes on a wheel
    part: a brake lamp hangs on the rear SUSP2 upright, which is body-side, and putting it on the
    wheel would make it rotate with the tyre."""
    b = (bone or "").lower()
    if "wheel_" in b and ("disc" in b or "fan" in b or "tyre" in b):
        side = "l" if "left" in b else ("r" if "right" in b else None)
        axle = "f" if "frnt" in b or "front" in b else ("r" if "rear" in b else None)
        if side and axle:
            return "sportsmuscle_wheel_%s_%s" % (axle, side)
    return "sportsmuscle_body"


def _vanilla_reference():
    """Per-behavior field values from the vanilla module, so LGT-1 copies shipped numbers."""
    if not os.path.exists(VANILLA):
        return {}, "missing " + os.path.relpath(VANILLA, ROOT)
    x = open(VANILLA, encoding="utf-8-sig").read()
    blocks = x.split('<member gbltype="Structure" type-hash="2535066178"')[1:]
    out = collections.defaultdict(list)
    for b in blocks:
        def f(name):
            m = re.search(r'name="%s"[^>]*>([^<]*)<' % name, b)
            return m.group(1).strip() if m else None

        beh = f("behavior")
        if not beh:
            continue
        rgba = [f("R"), f("G"), f("B")]
        rec = {"behavior": beh, "part": f("part"),
               "diffuse": [float(v) for v in rgba] if all(rgba) else None,
               "range": float(f("range") or 0), "falloff_start": float(f("falloff_start") or 0),
               "near_cap": float(f("near_cap") or 0), "multiplier": float(f("multiplier") or 0),
               "min_luminosity": float(f("min_luminosity") or 0),
               "light_type": int(f("light_type") or 0), "blinking": int(f("blinking") or 0),
               "angle": float(f("angle") or 0), "cast_shadows": int(f("cast_shadows") or 0),
               "projected_texture_index": int(f("projected_texture_index") or 0),
               "volumetric_mode": int(f("volumetric_mode") or 0),
               "volume_intensity": float(f("volume_intensity") or 0),
               "preset_id": int(f("preset_id") or 0)}
        out[beh].append(rec)
    ref = {}
    for beh, recs in out.items():
        # most common value per field: the vanilla car repeats a behavior on several parts
        agg = {}
        for k in recs[0]:
            if k in ("behavior", "part"):
                continue
            vals = [json.dumps(r[k], sort_keys=True) for r in recs]
            agg[k] = json.loads(collections.Counter(vals).most_common(1)[0][0])
        ref[beh] = agg
    return ref, "%d entries in %s" % (len(blocks), os.path.relpath(VANILLA, ROOT))


def _parts():
    """Part names of the shipped .epe (what the light module must reference), read from the newest build.
    Falls back to the assembly plan's part keys when no build exists yet."""
    import glob
    builds = sorted(glob.glob(os.path.join(ROOT, "Builds", "test-*")))
    for b in reversed(builds):
        for epe in glob.glob(os.path.join(b, "aaf", "**", "*.epe"), recursive=True):
            names = set(re.findall(rb"sportsmuscle_(?:body|wheel_[frl]+_[lr]|door_f_[lr])",
                                   open(epe, "rb").read()))
            if names:
                return {n.decode() for n in names}
    try:
        return {"sportsmuscle_" + k for k in json.load(open(ASSEMBLY, encoding="utf-8"))["plan"]}
    except (OSError, KeyError, ValueError):
        return set()


def part_node(part):
    """The deformable node a part roots at (vanilla: `sportsmuscle_body` lives at `body`)."""
    return part[len("sportsmuscle_"):] if part.startswith("sportsmuscle_") else part


def build():
    g = grab_model.Grab()
    lights = g.lights()
    bones = {b[0] for b in PX.skeleton(MESH)[0]} if os.path.exists(MESH) else set()
    parts = _parts()
    ref, ref_note = _vanilla_reference()
    vehicles = collections.OrderedDict()
    problems = []
    for x in lights:
        key = (x["package"], x["owner"])
        v = vehicles.setdefault(key, {"package": x["package"], "owner": x["owner"], "entries": []})
        comps = []
        for c in x["components"]:
            cls = c.get("class") or "?"
            dest, disp = COMPONENTS.get(cls, ("UNHANDLED", "UNHANDLED"))
            comps.append({"class": cls, "path": c.get("path"), "jc3": dest, "disposition": disp})
            if disp == "UNHANDLED":
                problems.append("%s: component class %s has no disposition" % (x["socket"], cls))
        typ = x.get("type")
        if typ in (None, "None"):
            typ = None
        if typ in TYPES:
            bhv, bdisp = TYPES[typ]
            bsrc = "enum %s" % typ
        else:
            bhv, bdisp = _socket_behavior(x.get("socket"))
            bsrc = "inferred from socket (type %s)" % ("stripped" if typ is None else typ)
        bone = x.get("bone")
        orphan = not bone
        if orphan:
            problems.append("%s/%s: socket %s does not exist in the shipped mesh"
                            % (x["package"], x["owner"], x["socket"]))
        elif bones and bone not in bones:
            problems.append("%s: socket %s hangs on bone %s, missing from Batmobile_V2.pskx"
                            % (x["socket"], x["socket"], bone))
        part = part_for(bone)
        if parts and part not in parts:
            problems.append("part %s for %s is not in the shipped .epe" % (part, x["socket"]))
        entry = {
            "socket": x["socket"],
            "socket_location": x.get("socket_location"),
            "bone": bone,
            "bone_in_rig": (bone in bones) if (bones and bone) else None,
            "orphan_socket": orphan,
            "type": typ,
            "material_type": x.get("material_type"),
            "behavior": bhv,
            "behavior_disposition": bdisp,
            "behavior_source": bsrc,
            "jc3_part": part,
            "part_exists": (part in parts) if parts else None,
            "jc3_anchor": (None if orphan or not bone else
                           "|sportsmuscle_LOD1|%s|%s|%s_LIG" % (part_node(part), bone, bone)),
            "anchor_state": ("orphan-socket: no bone, cannot place" if orphan
                             else "needs-lig-bone: the assembled part has no bone hierarchy yet"),
            "vanilla_reference": ref.get(bhv) if bhv else None,
            "components": comps,
        }
        v["entries"].append(entry)
    summary = {
        "entries": sum(len(v["entries"]) for v in vehicles.values()),
        "vehicles": len(vehicles),
        "orphan_sockets": sum(1 for v in vehicles.values() for e in v["entries"] if e["orphan_socket"]),
        "missing_bones": sum(1 for v in vehicles.values() for e in v["entries"]
                             if e["bone"] and e["bone_in_rig"] is False),
        "by_type": dict(collections.Counter(e["type"] or "(stripped)" for v in vehicles.values()
                                            for e in v["entries"])),
        "by_behavior": dict(collections.Counter(e["behavior"] or "(none)" for v in vehicles.values()
                                                for e in v["entries"])),
        "by_disposition": dict(collections.Counter(e["behavior_disposition"].split(":")[0]
                                                   for v in vehicles.values() for e in v["entries"])),
        "by_part": dict(collections.Counter(e["jc3_part"] for v in vehicles.values()
                                            for e in v["entries"])),
    }
    return {"schema": 1, "generated_by": "grab_lights.py",
            "skeleton": os.path.relpath(MESH, ROOT), "vanilla": ref_note,
            "jc3_fields": list(JC3_FIELDS), "vanilla_by_behavior": ref,
            "vehicles": list(vehicles.values()), "summary": summary, "problems": problems}


def write_md(doc):
    s = doc["summary"]
    L = ["# Batmobile - light rig -> JC3 VehicleDynamicLight (GRB-8)", "",
         "Generated by `Tools/scripts/grab_lights.py` from `grab_model.py lights` (schema "
         + str(grab_model.SCHEMA) + ") and the exported `Batmobile_V2.pskx` skeleton.", "",
         "Each `VehicleLights` entry in the shipped BmAK packages carries: a component reference, an enum "
         "`Type` (`VEHLT_*`), the **socket** it hangs on, and a `MaterialType` enum. The socket names the "
         "bind pose; the bone below is read from that socket in the exported mesh. `jc3_anchor` is the "
         "vanilla `deformable_transform` syntax fitted to the bone - the assembled part does not have that "
         "bone node yet, which is why every entry is `needs-lig-bone` (LGT-1).", "",
         "## Summary", "",
         "| fact | value |", "|---|---|"]
    for k in ("entries", "vehicles", "orphan_sockets", "missing_bones"):
        L.append("| %s | **%s** |" % (k, s[k]))
    for k in ("by_type", "by_behavior", "by_disposition", "by_part"):
        L.append("| %s | %s |" % (k, ", ".join("%s=%s" % i for i in sorted(s[k].items()))))
    L += ["", "Vanilla reference: %s" % doc["vanilla"], "",
          "## Problems", ""]
    L += ["- " + p for p in doc["problems"]] or ["none."]
    L.append("")
    if doc["vanilla_by_behavior"]:
        L += ["## Vanilla field values per behavior (copied by LGT-1)", "",
              "| behavior | range | falloff | near cap | multiplier | angle | diffuse |",
              "|---|---|---|---|---|---|---|"]
        for beh, r in sorted(doc["vanilla_by_behavior"].items()):
            L.append("| %s | %s | %s | %s | %s | %s | %s |" % (
                beh, r["range"], r["falloff_start"], r["near_cap"], r["multiplier"],
                r["angle"], r["diffuse"]))
        L.append("")
    for v in doc["vehicles"]:
        L += ["## %s - %s" % (v["package"], v["owner"]), "",
              "| socket | bone | type | material | JC3 behavior | part | anchor | components |",
              "|---|---|---|---|---|---|---|---|"]
        for e in v["entries"]:
            comps = ", ".join("%s -> %s%s" % (c["class"], c["jc3"],
                                              "" if c["disposition"] == "mapped"
                                              else " (%s)" % c["disposition"])
                              for c in e["components"])
            L.append("| `%s` | %s | %s | %s | %s | `%s` | %s | %s |" % (
                e["socket"], ("`%s`" % e["bone"]) if e["bone"] else "**orphan**",
                e["type"] or "-", e["material_type"] or "-",
                e["behavior"] or "-", e["jc3_part"],
                ("`%s`" % e["jc3_anchor"].replace("|", chr(92) + "|")) if e["jc3_anchor"] else "-",
                comps or "-"))
        L.append("")
    open(os.path.join(OUT, "LIGHTS.md"), "w", encoding="utf-8").write("\n".join(L))
    return os.path.join(OUT, "LIGHTS.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        json.dump(doc, open(os.path.join(OUT, "LIGHTS.json"), "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(os.path.join(OUT, "LIGHTS.json"), ROOT), "and",
              os.path.relpath(write_md(doc), ROOT))
    print(json.dumps(doc["summary"], indent=1))
    if a.check:
        fail = []
        s = doc["summary"]
        if s["entries"] != 101:
            fail.append("expected 101 VehicleLights entries, got %d" % s["entries"])
        if s["orphan_sockets"] != 6:
            fail.append("expected the 6 known HeadLight1c/2c orphan sockets, got %d"
                        % s["orphan_sockets"])
        if s["missing_bones"]:
            fail.append("%d entries point at bones missing from the skeleton" % s["missing_bones"])
        if any(c["disposition"] == "UNHANDLED" for v in doc["vehicles"] for e in v["entries"]
               for c in e["components"]):
            fail.append("a component class has no disposition")
        if any(e["behavior"] is None and e["behavior_disposition"].startswith("approximated")
               for v in doc["vehicles"] for e in v["entries"]):
            fail.append("an entry has an approximated behavior but no behavior name")
        if any(e["part_exists"] is False for v in doc["vehicles"] for e in v["entries"]):
            fail.append("an entry targets a part the shipped .epe does not have")
        if not doc["vanilla_by_behavior"]:
            fail.append("vanilla reference values are missing")
        if fail:
            print("FAIL")
            for f in fail:
                print("  -", f)
            return 1
        print("OK: %d entries / %d rigs, %d orphan sockets, 0 missing bones"
              % (s["entries"], s["vehicles"], s["orphan_sockets"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
