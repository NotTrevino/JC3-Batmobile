"""GRAB the whole Batman: Arkham Knight Batmobile out of the shipped packages.

Reads every package in scope with `upk_read.py` (own chunk/table/property-tag reader),
classifies every export, decodes the object graphs that are readable, and writes both a
machine manifest and human documents that answer "what does what":

    Research/BatmobileGrab/grab.json      summary, coverage, per-class counts
    Research/BatmobileGrab/objects.jsonl  one record per export (tags, refs, parse status)
    Research/BatmobileGrab/ASSETS.md      packages, class census, every object
    Research/BatmobileGrab/MATERIALS.md   master materials + instances (params, parents)
    Research/BatmobileGrab/TEXTURES.md    textures, formats, who binds them
    Research/BatmobileGrab/MECHANICS.md   vehicle/sim/wheels/physics/sockets/anims/weapons
    Research/BatmobileGrab/AUDIO.md       banks, events, vehicle sound, anim notifies
    Research/BatmobileGrab/GAPS.md        what could not be decoded, and why

Scope is discovered, not hand-listed: every `Playable_Batmobile*.upk` in the cooked folder is
read, minus the cinematic/death maps which are not vehicle assets (recorded in GAPS.md).

Usage:
    python Tools/scripts/batmobile_grab.py [--packages P1,P2] [--limit-exports N]
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upk_read import Package, best_walk, TYPE_NAMES  # noqa: E402
from grab_model import SCHEMA  # noqa: E402  (output layout lives with its reader)

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "Research", "BatmobileGrab")
SKIP = ("Cine_", "Death_", "Chases_Gen_")
MANIFEST_CAP = 4 * 1024 * 1024       # don't tag-walk huge binary payloads (banks, meshes)

APPEARANCE = {"Material", "MaterialInstanceConstant", "Texture2D", "TextureFlipBook",
              "MaterialExpressionScalarParameter", "MaterialExpressionVectorParameter",
              "MaterialExpressionTextureSampleParameter2D", "MaterialFunction"}
MESH = {"SkeletalMesh", "StaticMesh", "SkeletalMeshComponent", "StaticMeshComponent",
        "SkeletalMeshSocket", "PhysicsAsset", "RB_BodySetup", "RB_BodyInstance"}
MOTION = {"AnimSequence", "AnimSet", "AnimTree", "AnimNotify_Sound", "RAnimNotify_Script"}
AUDIO = {"AkBank", "AkEvent", "AkVehicleSound", "AkPlayerVehicleSoundInfo", "AkSwitchName",
         "AkSwitchGroupName", "AkStateName", "AkParameterName", "AkCurve", "AkEnvironmentName",
         "AkDialogueEvent", "AkDialogueConversation", "AkDialogueLineSingle"}
VFX = {"ParticleSystem", "ParticleSystemComponent", "LensFlare", "LensFlareComponent",
       "ApexGenericAsset", "ApexAttractorComponent", "ApexVortexComponent"}
VEHICLE = {"RVehicleBatmobile", "RVehicleSimBatmobile", "SVehicleWheel", "RVehicle",
           "RBatmobileCannon", "RBatmobileHeavyCannon", "RBatmobileMissileLauncher",
           "RBatmobileMissile", "RBatmobileEMPMissile", "RBatmobileEMP", "RBatmobileSonar",
           "RBatmobileWinch", "RBatmobileBooster", "RBatmobileVehicleTracker",
           "RBatmobileAllegianceSwitcher", "RBasicProjectile", "RDeadVehicle",
           "RAddContentBatmobileMesh", "ObjectReferencer"}
INTERESTING_REF_CLASSES = (VEHICLE | AUDIO | MOTION | MESH | VFX |
                          {"PhysicsAsset", "RB_BodySetup", "MaterialInstanceConstant",
                           "Material", "Texture2D", "SkeletalMesh"})


# ----------------------------------------------------------------------------- helpers

def short_hash(pkg, index):
    data = pkg.data(index)
    return hashlib.sha1(data).hexdigest()[:16]


def compact(tags, depth=0):
    """JSON-safe, size-limited form of a tag list."""
    out = []
    for t in tags:
        row = {k: v for k, v in t.items()
               if k in ("type", "type_id", "offset", "name", "size", "array_index")}
        if "props" in t:
            row["props"] = compact(t["props"], depth + 1)
        if "items" in t:
            items = []
            for it in t["items"][:32]:
                if isinstance(it, list):
                    items.append(compact(it, depth + 1))
                else:
                    items.append(it)
            row["items"] = items
        for k in ("value", "bits", "count", "floats", "vec3", "stride", "nested"):
            if k in t:
                row[k] = t[k]
        if "ref" in t and t["ref"]:
            row["ref"] = t["ref"]
        if "ref_class" in t and t["ref_class"]:
            row["ref_class"] = t["ref_class"]
        if "raw" in t and depth < 3:
            row["raw"] = t["raw"][:64]
        out.append(row)
    return out


def refs_in(tags, pkg, out=None):
    out = [] if out is None else out
    for t in tags:
        if t.get("type_id") in (5, 8) and isinstance(t.get("value"), int) and t["value"]:
            out.append({"index": t["value"], "path": pkg.object_path(t["value"]),
                        "class": pkg.object_class(t["value"]), "how": t.get("name", t["type"])})
        if t.get("type_id") == 16:
            v = t.get("value")
            if isinstance(v, int) and v:
                out.append({"index": v, "path": pkg.object_path(v),
                            "class": pkg.object_class(v), "how": "offset-only"})
        if "props" in t:
            refs_in(t["props"], pkg, out)
        if "items" in t:
            for it in t["items"]:
                if isinstance(it, list):
                    refs_in(it, pkg, out)
    return out


def native_refs(pkg, index, cap=128):
    """Unparsed native blobs: keep only aligned words that resolve to an interesting object.
    These are candidate references (the blob has no tags), so the docs label them as such."""
    data = pkg.data(index)
    seen, out = {}, []
    for i in range(0, len(data) - 4, 4):
        v = struct.unpack_from("<i", data, i)[0]
        if v == 0 or abs(v) > max(pkg.export_count, pkg.import_count):
            continue
        cls = pkg.object_class(v)
        if cls in INTERESTING_REF_CLASSES:
            if v in seen:
                seen[v]["hits"] += 1
                continue
            row = {"at": i, "index": v, "path": pkg.object_path(v), "class": cls, "hits": 1}
            seen[v] = row
            out.append(row)
            if len(out) >= cap:
                break
    return out


def name_value(pkg, tag):
    v = tag.get("value")
    if isinstance(v, str):            # resolved by upk_read.walk_tags (schema 3+)
        return v
    if isinstance(v, dict) and "name_index" in v:
        i = v["name_index"]
        return pkg.names[i] if 0 <= i < len(pkg.names) else None
    return None


def named(tags, key):
    for t in tags:
        if t.get("name") == key:
            return t
    return None


def walk_find(tags, key, acc=None):
    """Find every tag with this name anywhere in a nested tag tree."""
    acc = [] if acc is None else acc
    for t in tags:
        if t.get("name") == key:
            acc.append(t)
        if "props" in t:
            walk_find(t["props"], key, acc)
        if "items" in t:
            for it in t["items"]:
                if isinstance(it, list):
                    walk_find(it, key, acc)
    return acc


def array_items(tag):
    """Yield nested tag lists or dicts from a decoded array tag."""
    for it in tag.get("items", []):
        yield it


def item_fields(pkg, it):
    """Flatten one parameter-struct element: name + float/vector/ref."""
    if not isinstance(it, list):
        return None
    out = {}
    for t in it:
        if t.get("type") == "NameProperty":
            nm = name_value(pkg, t)
            if nm:
                out["name"] = nm
        elif t.get("type") == "FloatProperty":
            out.setdefault("floats", []).append(t.get("value"))
        elif t.get("type") == "VectorProperty":
            out["vector"] = t.get("value")
        elif t.get("type_id") in (5, 16):
            v = t.get("value")
            if isinstance(v, int) and v:
                out["ref"] = v
                out["ref_path"] = pkg.object_path(v)
                out["ref_class"] = pkg.object_class(v)
    return out or None


def scan_expression_refs(pkg, index, cap=16):
    """Material expressions keep references as raw 4-byte object words. Collect the textures they
    sample and the child expressions they feed from, so a slot can be resolved transitively."""
    data = pkg.data(index)
    tex, kids = [], []
    # property tags are not 4-byte aligned, so scan every offset; a random word almost never
    # resolves to a MaterialExpression or Texture2D object.
    for i in range(0, len(data) - 4):
        v = struct.unpack_from("<i", data, i)[0]
        if not v or abs(v) > max(pkg.export_count, pkg.import_count):
            continue
        cls = pkg.object_class(v)
        if cls in ("Texture2D", "TextureFlipBook"):
            path = pkg.object_path(v)
            if path and path not in tex:
                tex.append(path)
        elif cls and cls.startswith("MaterialExpression") and v > 0 and v != index:
            if v not in kids:
                kids.append(v)
        if len(tex) >= cap and len(kids) >= cap:
            break
    return tex, kids


def curve_points(tag):
    """Pull (x, y) samples out of a decoded curve struct (nested Points array of tagged points)."""
    for p in tag.get("props", []):
        if p.get("type") == "ArrayProperty" and "items" in p:
            pts = []
            for it in p["items"]:
                if not isinstance(it, list) or len(it) < 2:
                    continue
                floats = [t.get("value") for t in it if t.get("type") == "FloatProperty"]
                if len(floats) >= 2:
                    pts.append((floats[0], floats[1]))
            if pts:
                return pts
    return []


def fmt(v, digits=4):
    if isinstance(v, float):
        return ("%%.%df" % digits) % v
    return str(v)


def tag_value(pkg, t):
    """One-line description of a decoded property, including array payloads."""
    if t.get("type") == "StructProperty" and t.get("props"):
        pts = curve_points(t)
        if pts:
            return "%d curve points" % len(pts)
        return "{%d props}" % len(t["props"])
    if t.get("count") is not None:
        bits = ["%d items" % t["count"]]
        if t.get("strings"):
            bits.append("[" + ", ".join("`%s`" % s for s in t["strings"][:4]) + "]")
        if t.get("refs"):
            bits.append("[" + "; ".join("`%s`" % (x.get("path") or x.get("index"))
                                       for x in t["refs"][:4]) + "]")
        elif t.get("floats"):
            bits.append(str(t["floats"][:6]))
        return " ".join(bits)
    if t.get("ref"):
        return "→ `%s`" % t["ref"]
    return fmt(t.get("value"))


def light_entry(pkg, t, ordinal):
    bone = kind = mat = None
    refs = []
    for p in t.get("props", []):
        if p.get("type") == "NameProperty":
            bone = name_value(pkg, p)
        elif p.get("type_id") == 16 and p.get("value"):
            refs.append(p["value"])
        elif p.get("name") in ("Type", "MaterialType"):
            if p["name"] == "Type":
                kind = p.get("value")
            else:
                mat = p.get("value")
    return [ordinal, "`%s`" % (bone or "—"), kind if kind is not None else "—",
            mat if mat is not None else "—",
            "; ".join("`%s`" % (pkg.object_path(x) or x) for x in refs) or "—"]


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


# ----------------------------------------------------------------------------- grab

def discover():
    names = []
    for path in sorted(glob.glob(os.path.join(GAME, "*.upk"))):
        base = os.path.splitext(os.path.basename(path))[0]
        if not base.startswith("Playable_Batmobile"):
            continue
        if any(s in base for s in SKIP):
            continue
        names.append(base)
    return names


def read_package(base):
    path = os.path.join(GAME, base + ".upk")
    pkg = Package(path)
    records = []
    for i in range(1, pkg.export_count + 1):
        e = pkg.exports[i - 1]
        cls = pkg.object_class(i)
        rec = {
            "package": base, "index": i, "name": e["name"], "class": cls,
            "outer": pkg.object_path(e["outer_index"]), "size": e["size"],
            "sha1": short_hash(pkg, i),
        }
        if e["size"] <= MANIFEST_CAP:
            tags, end, why = best_walk(pkg, pkg.data(i))
            rec["tags"] = compact(tags)
            rec["tag_count"] = len(tags)
            rec["parsed"] = end
            rec["stop"] = why
            rec["refs"] = refs_in(tags, pkg)
        else:
            rec["tag_count"] = 0
            rec["parsed"] = 0
            rec["stop"] = "binary>%dMB" % (MANIFEST_CAP // (1024 * 1024))
            rec["refs"] = []
        if not rec["tag_count"]:
            rec["native_refs"] = native_refs(pkg, i)
        else:
            rec["native_refs"] = []
        records.append(rec)
    return pkg, records


def is_appearance(cls):
    return cls in APPEARANCE or (cls or "").startswith("MaterialExpression")


def build_docs(pkg_by_name, records_by_pkg):
    all_records = [r for rows in records_by_pkg.values() for r in rows]

    # ---------------- ASSETS.md
    lines = ["# Batmobile — asset inventory (grab output)", "",
             "Generated by `Tools/scripts/batmobile_grab.py` from the shipped packages. "
             "Do not edit by hand; re-run the grab.", "",
             "## Packages", ""]
    rows = []
    for base, pkg in pkg_by_name.items():
        rows.append([base, pkg.export_count, pkg.name_count, pkg.import_count,
                     sum(r["size"] for r in records_by_pkg[base])])
    lines.append(table(rows, ["package", "exports", "names", "imports", "serialized bytes"]))
    lines += ["", "## Class census", ""]
    counts = collections.Counter(r["class"] or "(unresolved)" for r in all_records)
    lines.append(table([[k, v] for k, v in counts.most_common()], ["class", "objects"]))
    lines += ["", "## Objects", ""]
    for base, rows in records_by_pkg.items():
        lines.append("### " + base)
        lines.append("")
        by = collections.defaultdict(list)
        for r in rows:
            by[r["class"]].append(r["name"])
        for cls in sorted(by, key=lambda c: (c is None, c or "")):
            names = sorted(set(by[cls]))
            shown = ", ".join("`%s`" % n for n in names[:40])
            more = "" if len(names) <= 40 else " … (+%d)" % (len(names) - 40)
            lines.append("- **%s** (%d): %s%s" % (cls, len(names), shown, more))
        lines.append("")
    open(os.path.join(OUT, "ASSETS.md"), "w", encoding="utf-8").write("\n".join(lines))

    # ---------------- MATERIALS.md
    mats = [r for r in all_records if r["class"] == "Material"]
    mis = [r for r in all_records if r["class"] == "MaterialInstanceConstant"]
    expr_direct = {(r["package"], r["index"]): (r.get("texture_refs", []), r.get("expr_children", []))
                   for r in all_records if (r["class"] or "").startswith("MaterialExpression")}

    def resolve_textures(pkg_name, idx, depth=4, seen=None):
        seen = set() if seen is None else seen
        if not idx or depth < 0 or (pkg_name, idx) in seen:
            return []
        seen.add((pkg_name, idx))
        tex, kids = expr_direct.get((pkg_name, idx), ([], []))
        out = list(tex)
        for k in kids:
            for t in resolve_textures(pkg_name, k, depth - 1, seen):
                if t not in out:
                    out.append(t)
        return out

    expr_tex = {(p, i): resolve_textures(p, i) for (p, i) in expr_direct}
    expr_tex = {k: v for k, v in expr_tex.items() if v}
    out = ["# Batmobile — materials", "",
           "Slot values come from the decoded `Material` tag stream; instance rows from "
           "`MaterialInstanceConstant` parameter arrays.", "",
           "## Master materials", ""]
    slot_rows = []
    for r in mats:
        pkg = pkg_by_name[r["package"]]
        tags = r.get("tags", [])
        slots = []
        for t in tags:
            if t.get("type") == "StructProperty":
                ref = None
                for it in t.get("props", []):
                    if it.get("type_id") in (5, 16) and isinstance(it.get("value"), int):
                        ref = it["value"]
                        break
                if ref:
                    texs = expr_tex.get((r["package"], ref), [])
                    slots.append("%s→`%s`%s" % (
                        t.get("name"), pkg.object_path(ref),
                        " [" + ", ".join("`%s`" % x.split(".")[-1] for x in texs) + "]" if texs else ""))
                else:
                    slots.append("%s→—" % t.get("name"))
        slot_rows.append([r["package"], r["name"], "; ".join(slots) or "—"])
    out.append(table(slot_rows, ["package", "material", "expression slots"]))
    # master-material slot -> expression -> texture
    rows = []
    for r in mats:
        pkg = pkg_by_name[r["package"]]
        for t in r.get("tags", []):
            if t.get("type") != "StructProperty":
                continue
            ref = None
            for it in t.get("props", []):
                if it.get("type_id") in (5, 16) and isinstance(it.get("value"), int):
                    ref = it["value"]
                    break
            texs = expr_tex.get((r["package"], ref), []) if ref else []
            rows.append([r["package"], "`%s`" % r["name"], t.get("name"),
                         "`%s`" % (pkg.object_path(ref) if ref else "—"),
                         "; ".join("`%s`" % x for x in texs) or "—"])
    out += ["", "## Slot → texture (masters)", ""]
    out.append(table(rows, ["package", "material", "slot", "expression", "texture"]))
    out += ["", "## Material instances", ""]
    mi_rows = []
    for r in mis:
        pkg = pkg_by_name[r["package"]]
        tags = r.get("tags", [])
        parent = None
        for t in tags:
            if t.get("type_id") == 16 and t.get("value"):
                parent = pkg.object_path(t["value"])
        scal, vec, tex = [], [], []
        for key, bucket in (("ScalarParameterValues", scal),
                            ("VectorParameterValues", vec),
                            ("TextureParameterValues", tex)):
            for t in walk_find(tags, key):
                for it in t.get("items", []):
                    f = item_fields(pkg, it) if isinstance(it, list) else None
                    if not f:
                        continue
                    if f.get("name") is None:
                        continue
                    if "floats" in f:
                        bucket.append("%s=%s" % (f["name"], fmt(f["floats"][0])))
                    elif "vector" in f:
                        bucket.append("%s=(%s)" % (f["name"], ", ".join(fmt(x, 3) for x in f["vector"])))
                    elif "ref_path" in f:
                        bucket.append("%s→`%s`" % (f["name"], f["ref_path"]))
        mi_rows.append([r["package"], r["name"], "`%s`" % (parent or "—"),
                        ", ".join(scal[:12]) or "—", ", ".join(vec[:6]) or "—",
                        ", ".join(tex) or "—"])
    out.append(table(mi_rows, ["package", "instance", "parent", "scalars", "vectors", "textures"]))
    open(os.path.join(OUT, "MATERIALS.md"), "w", encoding="utf-8").write("\n".join(out))

    # ---------------- TEXTURES.md
    texs = [r for r in all_records if r["class"] in ("Texture2D", "TextureFlipBook")]
    usage = collections.defaultdict(list)
    for r in mis:
        pkg = pkg_by_name[r["package"]]
        for t in walk_find(r.get("tags", []), "TextureParameterValues"):
            for it in t.get("items", []):
                f = item_fields(pkg, it) if isinstance(it, list) else None
                if f and f.get("ref_path"):
                    usage[f["ref_path"].split(".")[-1]].append(
                        "%s.%s (%s)" % (r["package"], r["name"], f.get("name")))
    for r in mats:
        pkg = pkg_by_name[r["package"]]
        for t in r.get("tags", []):
            if t.get("type") != "StructProperty":
                continue
            ref = None
            for it in t.get("props", []):
                if it.get("type_id") in (5, 16) and isinstance(it.get("value"), int):
                    ref = it["value"]
                    break
            for tex in expr_tex.get((r["package"], ref), []) if ref else []:
                usage[tex.split(".")[-1]].append("%s.%s (%s)" % (r["package"], r["name"], t.get("name")))
    rows = []
    for r in texs:
        dims = []
        fmtv = None
        for t in r.get("tags", []):
            if t.get("type") == "IntProperty" and t.get("offset") in (324, 328, 332, 336):
                dims.append(t.get("value"))
            if t.get("name") == "Format":
                fmtv = t.get("value")
        name = r["name"]
        rows.append([r["package"], "`%s`" % name, "×".join(str(d) for d in dims[:2]) or "—",
                     fmtv if fmtv is not None else "—", r["size"],
                     "; ".join(usage.get(name, []))[:160] or "—"])
    head = ["package", "texture", "size", "format", "bytes", "bound by"]
    note = ("# Batmobile — textures\n\n"
            "`format` is the BmAK pixel-format id as stored in the object (it differs between package "
            "variants for the same texture, because each cooked copy names its own format). "
            "`bound by` lists the material/instance and the parameter or slot that reaches the "
            "texture, resolved through the instance parameter arrays or the master-material "
            "expression graph.\n\n")
    open(os.path.join(OUT, "TEXTURES.md"), "w", encoding="utf-8").write(note + table(rows, head) + "\n")

    # ---------------- MECHANICS.md
    mech = [r for r in all_records if r["class"] in VEHICLE]
    out = ["# Batmobile — mechanics", "",
           "Every row is read from the package; offset-only values are primitives whose property "
           "name was stripped by the cooker (the value is real, the field name is not in the file).", ""]
    out += ["## Vehicle and simulation objects", ""]
    for r in mech:
        if r["class"] not in ("RVehicleBatmobile", "RVehicleSimBatmobile"):
            continue
        pkg = pkg_by_name[r["package"]]
        out.append("### %s — `%s` (%s, %d B)" % (r["name"], r["class"], r["package"], r["size"]))
        out.append("")
        if r["tag_count"]:
            rows, floats, curves, lights = [], [], [], []
            seen = collections.Counter()
            for t in r.get("tags", []):
                if t.get("name") == "VehicleLights":
                    lights.append(light_entry(pkg, t, len(lights)))
                    continue
                if t.get("name"):
                    if t.get("type") == "StructProperty" and t.get("props") and curve_points(t):
                        curves.append((t["name"], curve_points(t)))
                    seen[t["name"]] += 1
                    val = tag_value(pkg, t)
                    if seen[t["name"]] == 1:
                        rows.append(["`%s`" % t["name"], t.get("type"),
                                     "0x%X" % t.get("offset", 0), val])
                    else:
                        rows[-1][3] = "×%d, last: %s" % (seen[t["name"]], val)
                elif t.get("type") in ("FloatProperty",):
                    floats.append(t)
            if rows:
                out.append(table(rows, ["property", "type", "offset", "value"]))
                out.append("")
            if lights:
                out.append("Light rig (%d entries, each a `VehicleLights` struct):" % len(lights))
                out.append("")
                out.append(table(lights, ["#", "bone", "Type", "MaterialType", "components"]))
                out.append("")
            hooks = {}
            for x in r.get("refs", []):
                if x["class"] in AUDIO:
                    hooks[x["path"]] = x
            if hooks:
                out.append("Audio referenced by this object:")
                out.append("")
                out.append(table([["`%s`" % x["path"], x["class"], x["how"]]
                                  for x in sorted(hooks.values(),
                                                  key=lambda y: (y["class"], y["path"] or ""))],
                                 ["object", "class", "property"]))
                out.append("")
            if curves:
                out.append("Curves (x → y), decoded from the nested `Points` array:")
                out.append("")
                out.append("```")
                for cname, pts in curves:
                    out.append("%s = %s" % (cname, "  ".join("%s → %s" % (fmt(x, 1), fmt(y, 1))
                                                            for x, y in pts)))
                out.append("```")
                out.append("")
            if floats:
                out.append("Offset-only floats, sorted by class offset (the property name was "
                           "stripped by the cooker; the value is real):")
                out.append("")
                out.append("```")
                for t in sorted(floats, key=lambda x: x.get("offset", 0)):
                    out.append("offset 0x%03X  %s" % (t.get("offset", 0), fmt(t.get("value"))))
                out.append("```")
                out.append("")
        else:
            out.append("Parse status: **%s** — no properties in the serialized object." % r.get("stop"))
            out.append("")

    out += ["## Wheels and components", ""]
    rows = []
    for r in mech:
        if r["class"] == "SVehicleWheel":
            counts = collections.Counter(x["class"] for x in r.get("refs", []))
            rr = ", ".join("%s ×%d" % (c, n) for c, n in counts.most_common())
            unique = sorted({x["path"] for x in r.get("refs", [])})
            detail = "; ".join("`%s`" % x for x in unique[:6])
            rows.append([r["package"], "`%s`" % r["name"], r["size"], rr or "—", detail or "—"])
    out.append(table(rows, ["package", "component", "bytes", "reference classes",
                            "first references"]))
    out += ["", "## Physics", ""]
    rows = []
    for r in all_records:
        if r["class"] == "PhysicsAsset":
            bodies = 0
            for t in r.get("tags", []):
                if t.get("name") == "BodySetup":
                    bodies = t.get("count", 0)
            rows.append([r["package"], "`%s`" % r["name"], r["size"], bodies])
    out.append(table(rows, ["package", "physics asset", "bytes", "bodies"]))
    out += ["", "## Meshes", ""]
    mesh_rows = []
    for r in all_records:
        if r["class"] != "SkeletalMesh":
            continue
        lods = next((t.get("count") for t in r.get("tags", []) if t.get("name") == "LODInfo"), "—")
        socks = next((t.get("count") for t in r.get("tags", []) if t.get("name") == "Sockets"), "—")
        mesh_rows.append([r["package"], "`%s`" % r["name"], r["size"], lods, socks,
                          r.get("stop")])
    out.append(table(mesh_rows, ["package", "mesh", "bytes", "LODs", "sockets", "parse"]))
    out += ["", "### Mesh components", ""]
    comp_rows = []
    for r in all_records:
        if r["class"] != "SkeletalMeshComponent":
            continue
        meshes = [x["path"] for x in r.get("refs", []) if x["class"] == "SkeletalMesh"]
        anims = [x["path"] for x in r.get("refs", []) if x["class"] in ("AnimSet", "AnimTree")]
        comp_rows.append([r["package"], "`%s`" % r["name"], r.get("outer") or "—",
                          "; ".join("`%s`" % m for m in meshes) or "—",
                          "; ".join("`%s`" % m for m in anims) or "—"])
    out.append(table(comp_rows, ["package", "component", "owner", "mesh", "anim sets"]))
    out += ["", "## Sockets", ""]
    out.append("Socket objects carry the bone name and the relative location; they are the attach "
               "points for lights, muzzles, missiles, afterburners and the driver. The full bone "
               "hierarchy lives in the exported mesh (`Working/Appearance/grab/Playable_Batmobile_SF/"
               "SkeletalMesh3/Batmobile_V2.pskx`), which is the same mesh these sockets sit on.")
    out.append("")
    sock_rows = []
    for r in all_records:
        if r["class"] != "SkeletalMeshSocket":
            continue
        pkg = pkg_by_name[r["package"]]
        names = [name_value(pkg, t) for t in r.get("tags", []) if t.get("type") == "NameProperty"]
        vec = next((t.get("value") for t in r.get("tags", []) if t.get("type") == "VectorProperty"), None)
        sock_rows.append([r["package"], names[0] if names else "—", names[1] if len(names) > 1 else "—",
                          "(%s)" % ", ".join(fmt(v, 2) for v in vec) if vec else "—"])
    out.append(table(sock_rows, ["package", "socket", "bone", "relative location"]))
    out += ["", "## Animation", ""]
    anim_rows = []
    for r in all_records:
        if r["class"] not in MOTION:
            continue
        nums = [t.get("value") for t in r.get("tags", []) if t.get("type") == "FloatProperty"]
        nframes = [t.get("value") for t in r.get("tags", []) if t.get("type") == "IntProperty"]
        anim_rows.append([r["package"], "`%s`" % r["name"], r["class"], r["size"],
                          nums[0] if nums else "—", nframes[0] if nframes else "—"])
    out.append(table(anim_rows, ["package", "name", "class", "bytes", "first float", "first int"]))
    out += ["", "## Weapons and projectiles", ""]
    wrows = []
    for r in mech:
        if r["class"] in ("RBatmobileCannon", "RBatmobileHeavyCannon", "RBatmobileMissileLauncher",
                          "RBatmobileMissile", "RBatmobileEMPMissile", "RBatmobileEMP",
                          "RBatmobileSonar", "RBatmobileWinch", "RBatmobileBooster",
                          "RBatmobileVehicleTracker", "RBatmobileAllegianceSwitcher",
                          "RBasicProjectile"):
            props = [t["name"] for t in r.get("tags", []) if t.get("name")]
            links = "; ".join("`%s`" % (x.get("path") or "")
                             for x in r.get("refs", [])[:5]) or "—"
            wrows.append([r["package"], "`%s`" % r["name"], r["class"], len(props),
                          ", ".join("`%s`" % p for p in dict.fromkeys(props))[:120] or "—", links])
    out.append(table(wrows, ["package", "object", "class", "named props", "properties",
                            "references"]))
    open(os.path.join(OUT, "MECHANICS.md"), "w", encoding="utf-8").write("\n".join(out))

    # ---------------- AUDIO.md
    aud = [r for r in all_records if r["class"] in AUDIO]
    out = ["# Batmobile — audio", ""]
    banks = [r for r in aud if r["class"] == "AkBank"]
    out += ["## Banks", ""]
    out.append(table([["`%s`" % r["name"], r["package"], r["size"]] for r in banks],
                     ["bank", "package", "bytes"]))
    out += ["", "## Events", ""]
    ev = [r for r in aud if r["class"] == "AkEvent"]
    out.append(table([["`%s`" % r["name"], r["package"]] for r in ev], ["event", "package"]))
    out += ["", "## Vehicle sound + switches", ""]
    other = [r for r in aud if r["class"] not in ("AkBank", "AkEvent")]
    out.append(table([["`%s`" % r["name"], r["class"], r["package"]] for r in other],
                     ["object", "class", "package"]))
    notify = [r for r in all_records if r["class"] == "AnimNotify_Sound"]
    out += ["", "## Anim-notify sounds", ""]
    out.append(table([["`%s`" % r["name"], r["package"]] for r in notify], ["notify", "package"]))
    open(os.path.join(OUT, "AUDIO.md"), "w", encoding="utf-8").write("\n".join(out))

    # ---------------- GAPS.md
    out = ["# Batmobile — grab gaps", "",
           "What the grab could not decode, with the exact reason. Nothing here is silently "
           "filled in.", ""]
    total = len(all_records)
    readable = sum(1 for r in all_records if r["tag_count"])
    out += ["## Coverage", "",
            "- objects: **%d**" % total,
            "- decoded tag streams: **%d** (%.2f%%)" % (readable, 100.0 * readable / max(total, 1)),
            "- native / untagged: **%d**" % (total - readable), ""]
    by_pkg = collections.Counter(r["package"] for r in all_records)
    rows = []
    for base, n in by_pkg.items():
        ok = sum(1 for r in all_records if r["package"] == base and r["tag_count"])
        rows.append([base, n, ok, "%.1f%%" % (100.0 * ok / max(n, 1))])
    out.append(table(rows, ["package", "objects", "decoded", "coverage"]))
    out.append("")
    stops = collections.Counter((r["class"], r.get("stop")) for r in all_records if not r["tag_count"])
    out.append(table([[a, b, c] for (a, b), c in stops.most_common()],
                     ["class", "stop reason", "objects"]))
    out += ["", "## Native (untagged) objects", ""]
    native = [r for r in all_records if not r["tag_count"]]
    out.append(table([["`%s`" % r["name"], r["class"], r["size"], r.get("stop"), len(r.get("native_refs", []))]
                      for r in native[:80]], ["object", "class", "bytes", "stop", "refs recovered"]))
    if len(native) > 80:
        out.append("\n…and %d more (see `objects.jsonl`)." % (len(native) - 80))
    out += ["", "## Excluded packages", ""]
    excluded = [os.path.splitext(os.path.basename(p))[0]
                for p in sorted(glob.glob(os.path.join(GAME, "*Batmobile*.upk")))
                if not os.path.splitext(os.path.basename(p))[0].startswith("Playable_Batmobile")
                or any(s in p for s in SKIP)]
    out.append(", ".join("`%s`" % e for e in excluded) or "—")
    out.append("")
    out.append("Cinematics, death maps and generator packages are not vehicle assets; they are "
               "listed here so the scope is explicit.")
    out += ["", "## Physics asset", "",
            "The 32 `RB_BodySetup` records per vehicle are expanded in `PHYSICS.md`: bone name, box "
            "extents and local centre (PHY-1, `Tools/scripts/grab_physics.py --check`). They cover "
            "wheels, cockpit, doors, fins, turret and the destruction debris — there is **no chassis "
            "body**, so the driveable car's collision is not in this asset."]
    out += ["", "## Dependency closure", ""]
    rows = []
    for base, pkg in pkg_by_name.items():
        deps = sorted({i["class_package"] for i in pkg.imports if i["class_package"]})
        missing = [d for d in deps if not os.path.exists(os.path.join(GAME, d + ".upk"))]
        rows.append([base, len(deps), len(missing), ", ".join(missing[:10]) or "—"])
    out.append(table(rows, ["package", "imported packages", "not on disk", "examples"]))
    open(os.path.join(OUT, "GAPS.md"), "w", encoding="utf-8").write("\n".join(out))

    # ---------------- README.md (index + key numbers, all derived)
    main = [r for r in all_records if r["package"] == "Playable_Batmobile_SF"]
    sim = next((r for r in main if r["class"] == "RVehicleSimBatmobile"), None)
    curves = []
    if sim:
        for t in sim.get("tags", []):
            if t.get("type") == "StructProperty":
                pts = curve_points(t)
                if pts:
                    curves.append((t.get("name"), len(pts)))
    counts = collections.Counter(r["class"] for r in all_records)
    socket_names = sorted({r["name"] for r in all_records if r["class"] == "SkeletalMeshSocket"})
    anchors = [s for s in socket_names if any(k in s.lower() for k in
                                                ("light", "muzzle", "missile", "afterburner",
                                                 "winch", "driver"))]
    readme = [
        "# Batmobile — GRAB output", "",
        "Read-only inventory of the shipped Batman: Arkham Knight Batmobile, generated by "
        "`Tools/scripts/batmobile_grab.py` (reader: `upk_read.py`). Every number here is read from "
        "the `.upk` files; nothing is hand-listed. Re-run the script to refresh.", "",
        "## Totals", "",
        "- packages: **%d**" % len(pkg_by_name),
        "- objects: **%d** (decoded **%d**, native/untagged **%d**)" % (
            len(all_records), sum(1 for r in all_records if r["tag_count"]),
            sum(1 for r in all_records if not r["tag_count"])),
        "- materials: **%d** + **%d** instances" % (counts.get("Material", 0),
                                                    counts.get("MaterialInstanceConstant", 0)),
        "- textures: **%d**" % (counts.get("Texture2D", 0) + counts.get("TextureFlipBook", 0)),
        "- meshes: **%d**, sockets: **%d**" % (counts.get("SkeletalMesh", 0),
                                               counts.get("SkeletalMeshSocket", 0)),
        "- animation: **%d** sequences, **%d** sets/trees" % (
            counts.get("AnimSequence", 0), counts.get("AnimSet", 0) + counts.get("AnimTree", 0)),
        "- audio: **%d** banks, **%d** events" % (counts.get("AkBank", 0), counts.get("AkEvent", 0)),
        "- vehicles: **%d** RVehicleBatmobile, **%d** RVehicleSimBatmobile, **%d** wheels" % (
            counts.get("RVehicleBatmobile", 0), counts.get("RVehicleSimBatmobile", 0),
            counts.get("SVehicleWheel", 0)),
        "", "## Files", "",
        "| file | what it answers |", "|---|---|",
        "| `ASSETS.md` | what exists, per package and class |",
        "| `MATERIALS.md` | each material's slots/expressions and each instance's parent + params |",
        "| `TEXTURES.md` | each texture's size/format and which instance binds it to which parameter |",
        "| `MECHANICS.md` | vehicle + sim values and curves, wheels, meshes, physics, sockets, animation, weapons |",
        "| `AUDIO.md` | banks, events, vehicle-sound objects, anim-notify sounds |",
        "| `LIGHTS.md` | the light rig as JC3 `VehicleDynamicLight`: socket → bone, behavior, part, field values (GRB-8) |",
        "| `AUDIO_MAP.md` | every `AkEvent` → bank → WEM through HIRC, and the banks not on disk (GRB-9) |",
        "| `SLOTS.md` | LOD → material slot → texture, with the three agreeing slot orders and LOD0 faces (GRB-10) |",
        "| `OFFSETS.md` | remaining unnamed fields, named from layout or closed with evidence (GRB-11) |",
        "| `PHYSICS.md` | per-bone collision boxes (bone, extents, centre) from the physics asset (PHY-1) |",
        "| `GAPS.md` | coverage, native/untagged objects, dependency closure, verification |",
        "| `objects.jsonl` | one JSON record per export (tags, refs, parse status) — the machine source |",
        "| `grab.json` | totals, per-package counts, verification checks |",
        "", "Consumers must read these files through `Tools/scripts/grab_model.py` (schema %d)" % SCHEMA,
        "and run `python Tools/scripts/grab_model.py check`; other readers are unsupported.",
        "", "## Simulation model (main package)", "",
    ]
    if curves:
        readme.append("Named curves (property → point count):")
        readme.append("")
        readme.append("```")
        for n, k in curves:
            readme.append("%-28s %d points" % (n, k))
        readme.append("```")
    else:
        readme.append("No simulation object found.")
    readme += ["", "Full points are in `MECHANICS.md`.", "", "## Attachment anchors (sockets)", ""]
    readme.append("Socket objects are read from the package; these names match light/muzzle/"
                  "afterburner/winch/driver roles:")
    readme.append("")
    readme.append(", ".join("`%s`" % s for s in anchors) if anchors else "—")
    readme += ["", "Every socket with its bone and relative location: see `MECHANICS.md` → Sockets.", ""]
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("\n".join(readme))
    return all_records


# Independent expectations for Playable_Batmobile_SF, from UEViewer's own listing
# (`umodel -list`): the grab must reproduce them from its own reader.
EXPECTED_MAIN = {
    "exports": 5490,
    "Material": 45,
    "MaterialInstanceConstant": 33,
    "SkeletalMesh": 3,
    "Texture2D": 92,
    "AnimSequence": 37,
    "SkeletalMeshSocket": 65,
    "AkBank": 7,
    "AkEvent": 91,
    "SVehicleWheel": 4,
    "PhysicsAsset": 1,
    "RB_BodySetup": 32,
    "ParticleSystem": 59,
}


def verify(all_records):
    main = [r for r in all_records if r["package"] == "Playable_Batmobile_SF"]
    counts = collections.Counter(r["class"] for r in main)
    checks = []
    checks.append(("exports", len(main), EXPECTED_MAIN["exports"], len(main) == EXPECTED_MAIN["exports"]))
    for cls, want in EXPECTED_MAIN.items():
        if cls == "exports":
            continue
        got = counts.get(cls, 0)
        checks.append((cls, got, want, got == want))
    sim = [r for r in main if r["class"] == "RVehicleSimBatmobile"]
    curves = sum(1 for r in sim for t in r.get("tags", []) if t.get("type") == "StructProperty")
    checks.append(("sim named structs", curves, "≥6", curves >= 6))
    bags = {r["name"] for r in main if r["class"] == "AkBank"}
    checks.append(("BML_Engine bank", "yes" if "BML_Engine" in bags else "no", "yes",
                   "BML_Engine" in bags))
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--packages", help="comma-separated package bases (default: discovered)")
    ap.add_argument("--limit-exports", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    bases = a.packages.split(",") if a.packages else discover()
    print("packages:", ", ".join(bases))
    pkg_by_name, records_by_pkg = {}, {}
    for base in bases:
        pkg = Package(os.path.join(GAME, base + ".upk"))
        n = pkg.export_count if not a.limit_exports else min(pkg.export_count, a.limit_exports)
        pkg_by_name[base] = pkg
        rows = []
        for i in range(1, n + 1):
            e = pkg.exports[i - 1]
            cls = pkg.object_class(i)
            rec = {"package": base, "index": i, "name": e["name"], "class": cls,
                   "outer": pkg.object_path(e["outer_index"]), "size": e["size"],
                   "sha1": short_hash(pkg, i)}
            data = pkg.data(i)
            if e["size"] <= MANIFEST_CAP:
                tags, end, why = best_walk(pkg, data)
                rec.update(tags=compact(tags), tag_count=len(tags), parsed=end, stop=why,
                           refs=refs_in(tags, pkg))
            else:
                # big binary exports (meshes, banks): their property block is at the front
                tags, end, why = best_walk(pkg, data[:65536])
                if tags:
                    rec.update(tags=compact(tags), tag_count=len(tags), parsed=end,
                               stop="truncated_walk(" + why + ")", truncated=True,
                               refs=refs_in(tags, pkg))
                else:
                    rec.update(tags=[], tag_count=0, parsed=0,
                               stop="binary>%dMB" % (MANIFEST_CAP // (1024 * 1024)), refs=[])
            rec["native_refs"] = native_refs(pkg, i) if not rec["tag_count"] else []
            if (cls or "").startswith("MaterialExpression"):
                tex, kids = scan_expression_refs(pkg, i)
                rec["texture_refs"] = tex
                rec["expr_children"] = kids
            rows.append(rec)
        records_by_pkg[base] = rows
        readable = sum(1 for r in rows if r["tag_count"])
        print("  %-34s %5d exports  %5d readable  %5d native/empty"
              % (base, len(rows), readable, len(rows) - readable))

    all_records = build_docs(pkg_by_name, records_by_pkg)
    with open(os.path.join(OUT, "objects.jsonl"), "w", encoding="utf-8") as fh:
        for r in all_records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    checks = verify(all_records)
    summary = {
        "schema": SCHEMA, "generator": "batmobile_grab.py",
        "game": GAME, "packages": bases,
        "exports": len(all_records),
        "readable": sum(1 for r in all_records if r["tag_count"]),
        "native": sum(1 for r in all_records if not r["tag_count"]),
        "classes": dict(collections.Counter(r["class"] or "(unresolved)" for r in all_records).most_common()),
        "per_package": {b: len(rows) for b, rows in records_by_pkg.items()},
        "checks": [{"name": n, "got": g, "want": w, "pass": bool(ok)} for n, g, w, ok in checks],
        "docs": ["ASSETS.md", "MATERIALS.md", "TEXTURES.md", "MECHANICS.md", "AUDIO.md",
                 "LIGHTS.md", "AUDIO_MAP.md", "SLOTS.md", "OFFSETS.md", "PHYSICS.md", "GAPS.md"],
    }
    failed = [c for c in checks if not c[3]]
    with open(os.path.join(OUT, "GAPS.md"), "a", encoding="utf-8") as fh:
        fh.write("\n## Verification against UEViewer's listing\n\n")
        fh.write("| check | grab | expected | result |\n|---|---|---|---|\n")
        for n, g, w, ok in checks:
            fh.write("| %s | %s | %s | %s |\n" % (n, g, w, "PASS" if ok else "FAIL"))
        fh.write("\n%d/%d checks passed.\n" % (len(checks) - len(failed), len(checks)))
    if failed:
        print("VERIFY FAILED:", ", ".join(c[0] for c in failed))
    json.dump(summary, open(os.path.join(OUT, "grab.json"), "w", encoding="utf-8"), indent=1)
    print("exports %d, readable %d, native %d" % (summary["exports"], summary["readable"],
                                                  summary["native"]))
    print("docs ->", OUT)


if __name__ == "__main__":
    main()
