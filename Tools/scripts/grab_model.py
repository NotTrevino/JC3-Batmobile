"""grab_model.py - typed, queryable view of the Batmobile grab (GRB-7).

`batmobile_grab.py` writes two files: `grab.json` (totals, checks, class census) and
`objects.jsonl` (one record per export, with decoded tags and resolved references).
This module is the only supported way for the rest of the pipeline to read them, so a
consumer never has to know the JSON layout, and a change to the grab is caught by
`check` instead of by a silently wrong build.

Usage:
    python Tools/scripts/grab_model.py check            # schema + invariants + spot checks
    python Tools/scripts/grab_model.py stats [--json]
    python Tools/scripts/grab_model.py find --class RVehicleSimBatmobile
    python Tools/scripts/grab_model.py find --value HeadLight2a --package Playable_Batmobile_SF
    python Tools/scripts/grab_model.py find --tag VehicleLights --package Playable_Batmobile_SF
    python Tools/scripts/grab_model.py show <name | outer.name | package:index> [--package P] [--json]
    python Tools/scripts/grab_model.py tags <name> [--package P] [--json]
    python Tools/scripts/grab_model.py offsets <name> [--package P]
    python Tools/scripts/grab_model.py lights [--package P] [--json]
    python Tools/scripts/grab_model.py curves [<sim name>]

`check` is the gate: it fails if the files disagree with their own summary, if a
decoded reference no longer resolves, or if the objects GRB-6 depends on are gone.
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Research", "BatmobileGrab")

SCHEMA = 6                       # objects.jsonl layout: 4 = object refs resolved, 5 = ByteProperty enum FNames resolved,
                                 # 6 = BoolProperty bitfield words preserved ("bits")
REQUIRED_ROW = ("package", "index", "name", "class", "size", "tags", "tag_count", "refs")


class GrabError(Exception):
    pass


def _flatten(tags, prefix="", out=None):
    """(dotted_field_path, tag) for every tag, including nested struct properties."""
    out = [] if out is None else out
    for t in tags:
        if not isinstance(t, dict):
            continue
        if t.get("name"):
            path = "%s.%s" % (prefix, t["name"]) if prefix else t["name"]
            out.append((path, t))
        else:
            # offset-only primitive: keep it, labelled by class offset
            path = "%s<0x%04X>" % (prefix + "." if prefix else "", t.get("offset") or 0)
            out.append((path, t))
        if "props" in t:
            _flatten(t["props"], path, out)
        for i, it in enumerate(t.get("items") or []):
            if isinstance(it, list):
                _flatten(it, "%s[%d]" % (path, i), out)
    return out


def _curve_points(tag):
    """(x, y) samples from a decoded curve struct (nested Points array of tagged points)."""
    for p in tag.get("props", []):
        if p.get("type") == "ArrayProperty" and "items" in p:
            pts = []
            for it in p["items"]:
                if not isinstance(it, list):
                    continue
                floats = [t.get("value") for t in it if t.get("type") == "FloatProperty"]
                if len(floats) >= 2:
                    pts.append((floats[0], floats[1]))
            if pts:
                return pts
    return []


class Grab:
    def __init__(self, out_dir=OUT):
        self.out_dir = out_dir
        self.summary_path = os.path.join(out_dir, "grab.json")
        self.rows_path = os.path.join(out_dir, "objects.jsonl")
        if not os.path.exists(self.rows_path) or not os.path.exists(self.summary_path):
            raise GrabError("no grab output in %s - run batmobile_grab.py first" % out_dir)
        self.summary = json.load(open(self.summary_path, encoding="utf-8"))
        self.rows = [json.loads(line) for line in open(self.rows_path, encoding="utf-8") if line.strip()]
        self.by_class = collections.defaultdict(list)
        self.by_package = collections.defaultdict(list)
        self.by_name = collections.defaultdict(list)
        self.by_path = {}
        for r in self.rows:
            self.by_class[r.get("class")].append(r)
            self.by_package[r.get("package")].append(r)
            self.by_name[r.get("name")].append(r)
            outer = r.get("outer")
            if outer:
                self.by_path["%s.%s" % (outer, r.get("name"))] = r
        self.by_path.update({"%s:%d" % (r["package"], r["index"]): r for r in self.rows})

    # ---------------- queries ----------------

    def find(self, class_=None, name=None, package=None, native=None, tag=None, value=None):
        """Filter rows. `class_` is exact, `name` is a regex, `tag` is NAME or NAME=SUBSTR
        matched against named properties, `value` is a substring of any tag value
        (e.g. `--value HeadLight` finds sockets whose name lives in an unnamed tag)."""
        pat = re.compile(name) if name else None
        tag_name, tag_val = (tag.split("=", 1) + [None])[:2] if tag else (None, None)
        out = []
        for r in self.rows:
            if class_ and r.get("class") != class_:
                continue
            if package and r.get("package") != package:
                continue
            if pat and not pat.search(r.get("name") or ""):
                continue
            if native is True and r.get("tag_count"):
                continue
            if native is False and not r.get("tag_count"):
                continue
            if value and not any(value.lower() in str(t.get("value", "")).lower()
                                for p, t in self.tags(r)):
                continue
            if tag_name:
                hits = [t for p, t in self.tags(r)
                        if (p or "").split(".")[-1] == tag_name or (p or "").endswith(tag_name)]
                if not hits:
                    continue
                if tag_val is not None and not any(tag_val.lower() in str(t.get("value", "")).lower()
                                                   for t in hits):
                    continue
            out.append(r)
        return out

    def one(self, key, package=None):
        """Resolve `<package>:<index>`, `outer.name`, or a bare object name."""
        if key in self.by_path:
            return self.by_path[key]
        if package and "%s:%s" % (package, key) in self.by_path:
            return self.by_path["%s:%s" % (package, key)]
        hits = [r for r in self.by_name.get(key, []) if not package or r["package"] == package]
        if not hits:
            raise GrabError("no object %r%s" % (key, " in " + package if package else ""))
        if len(hits) > 1:
            raise GrabError("%r is ambiguous (%d objects); use a package:index key or --package: %s"
                            % (key, len(hits), ", ".join("%s:%d" % (r["package"], r["index"])
                                                         for r in hits[:4])))
        return hits[0]

    def tags(self, row):
        return _flatten(row.get("tags") or [])

    def field(self, row, name):
        """Named property anywhere in the object's tag tree (last occurrence wins)."""
        hits = [t for p, t in self.tags(row) if (p or "").split(".")[-1] == name]
        return hits[-1] if hits else None

    def offset_only(self, row):
        """Primitives the cooker stripped of names: type, class offset, value."""
        out = []
        for path, t in self.tags(row):
            if not t.get("name") and "offset" in t and "value" in t:
                out.append({"path": path, "type": t.get("type"), "offset": t.get("offset"),
                            "value": t.get("value")})
        return out

    def sockets(self, package=None):
        """Socket name -> bone, relative location and rotation, from the exported SkeletalMeshSockets.
        The cooked socket objects carry offset-only tags, so the values are positional:
        [socket name, bone name, relative location, relative rotation].

        Keyed by `(package, socket)` because the same socket name hangs on different bones in
        different skins (HeadLight2a is on `Batmobile_Chassis` in the Jokerfied skin and on
        `Winch_DOOR_Mesh` in `Batmobile_V2`); a bare-name fallback is kept for callers without a
        package. Iterate `.values()` for the real list - the fallback aliases the same records."""
        out = {}
        for r in self.find(class_="SkeletalMeshSocket", package=package):
            names = [t.get("value") for p, t in self.tags(r)
                     if t.get("type") == "NameProperty" and isinstance(t.get("value"), str)]
            if len(names) < 2:
                continue
            vec = next((t.get("value") for p, t in self.tags(r) if t.get("type") == "VectorProperty"), None)
            rot = next((t.get("value") for p, t in self.tags(r) if t.get("type") == "RotatorProperty"), None)
            info = {"socket": names[0], "bone": names[1], "location": vec, "rotation": rot,
                    "package": r["package"], "owner": r.get("outer")}
            out.setdefault((r["package"], names[0]), info)   # the same socket name exists on several
            out.setdefault(names[0], info)                    # skins with different bones; key by mesh
        return out

    def lights(self, package=None):
        """The vehicle light rig, one entry per repeated `VehicleLights` struct.

        Struct layout (verified against the raw tag stream): component ref at 0, lens flare at 8,
        `Type` at 16 (ByteProperty holding an enum FName such as VEHLT_HeadLight), socket name at 20,
        `MaterialType` at 28 (VEHLTMAT_...), optional second component at 36. The NameProperty is the
        SOCKET the light hangs on, not a bone: resolve it through the exported sockets so every entry
        carries the real bone and the socket offset."""
        sockets = self.sockets()
        out = []
        for r in self.find(class_="RVehicleBatmobile", package=package):
            for path, t in self.tags(r):
                if (path or "").split(".")[-1] != "VehicleLights":
                    continue
                props = t.get("props") or []
                socket = next((x.get("value") for x in props
                               if x.get("type") == "NameProperty" and isinstance(x.get("value"), str)), None)
                sock = sockets.get((r["package"], socket)) or sockets.get(socket) or {}
                comps = [{"path": x.get("ref"), "class": x.get("ref_class")}
                         for x in props if x.get("ref")]
                out.append({
                    "package": r["package"], "owner": r.get("outer"),
                    "socket": socket, "bone": sock.get("bone"),
                    "socket_location": sock.get("location"),
                    "type": next((x.get("value") for x in props if x.get("name") == "Type"), None),
                    "material_type": next((x.get("value") for x in props
                                           if x.get("name") == "MaterialType"), None),
                    "components": comps,
                })
        return out

    def curves(self, sim_name=None):
        """Every named curve in every RVehicleSimBatmobile, with its points."""
        out = {}
        for r in self.find(class_="RVehicleSimBatmobile"):
            if sim_name and r.get("name") != sim_name:
                continue
            got = []
            for path, t in self.tags(r):
                pts = _curve_points(t)
                if pts:
                    got.append({"name": (path or "").split(".")[-1], "points": pts})
            if got:
                out["%s:%s" % (r["package"], r["name"])] = got
        return out

    def stats(self):
        classes = collections.Counter(r.get("class") or "(unresolved)" for r in self.rows)
        return {
            "schema": self.summary.get("schema"),
            "exports": len(self.rows),
            "decoded": sum(1 for r in self.rows if r.get("tag_count")),
            "native": sum(1 for r in self.rows if not r.get("tag_count")),
            "packages": len(self.by_package),
            "classes": dict(classes.most_common()),
            "checks": self.summary.get("checks", []),
        }

    # ---------------- verification ----------------

    def check(self):
        """Return (failures, facts). Facts are printed so the check is not a bare PASS."""
        fail = []
        if self.summary.get("schema") != SCHEMA:
            fail.append("grab.json schema %r != %d (re-run batmobile_grab.py)"
                        % (self.summary.get("schema"), SCHEMA))
        for i, r in enumerate(self.rows):
            missing = [k for k in REQUIRED_ROW if k not in r]
            if missing:
                fail.append("objects.jsonl line %d lacks %s" % (i + 1, ", ".join(missing)))
                break
        decoded = sum(1 for r in self.rows if r.get("tag_count"))
        native = len(self.rows) - decoded
        if self.summary.get("exports") not in (None, len(self.rows)):
            fail.append("grab.json exports %s != objects %d" % (self.summary.get("exports"), len(self.rows)))
        if self.summary.get("readable") not in (None, decoded):
            fail.append("grab.json readable %s != decoded %d" % (self.summary.get("readable"), decoded))
        if self.summary.get("native") not in (None, native):
            fail.append("grab.json native %s != untagged %d" % (self.summary.get("native"), native))
        for r in self.rows:
            if r.get("tag_count") != len(r.get("tags") or []):
                fail.append("%s:%s tag_count %s != %d tags"
                            % (r["package"], r["index"], r.get("tag_count"), len(r.get("tags") or [])))
                break

        facts = {"objects": len(self.rows), "decoded": decoded, "native": native}
        unresolved = sum(1 for r in self.rows for p, t in self.tags(r)
                         if t.get("type") == "NameProperty" and not isinstance(t.get("value"), str))
        facts["unresolved names"] = unresolved
        if unresolved:
            fail.append("%d NameProperty values are still name indices (schema 3 stores strings)"
                        % unresolved)

        # every decoded reference must resolve against the object index it was read from
        dangling = 0
        for r in self.rows:
            for ref in (r.get("refs") or []) + (r.get("native_refs") or []):
                if ref.get("path") is None:
                    dangling += 1
        if dangling:
            fail.append("%d decoded references have no path (index outside the package tables)" % dangling)

        # spot checks: the objects GRB-6 and the lights/audio work depend on
        sims = self.find(class_="RVehicleSimBatmobile")
        curves = self.curves()
        facts["sims"] = len(sims)
        facts["sim curves"] = sum(len(v) for v in curves.values())
        if not sims:
            fail.append("no RVehicleSimBatmobile object")
        if sum(len(v) for v in curves.values()) < 6:
            fail.append("fewer than 6 decoded sim curves")

        sockets = [r for r in self.find(class_="SkeletalMeshSocket") if r.get("tag_count")]
        facts["sockets"] = len(sockets)
        if len(sockets) < 200:
            fail.append("only %d decoded sockets (expected >= 200)" % len(sockets))
        sock_names = {t.get("value") for r in sockets for p, t in self.tags(r)
                      if t.get("type") == "NameProperty" and isinstance(t.get("value"), str)}
        facts["socket names"] = len(sock_names)
        if "HeadLight2a" not in sock_names:
            fail.append("socket names are not resolved strings (missing HeadLight2a)")

        # Batman serializes the light rig as repeated `VehicleLights` structs, not an array
        lights = self.lights()
        facts["light rigs"] = len(lights)
        if len(lights) < 90:
            fail.append("only %d VehicleLights structs decoded (expected >= 90)" % len(lights))
        unstuck = [x for x in lights if not x["bone"]]
        facts["orphan sockets"] = len(unstuck)
        if any(not x.get("socket") for x in lights):
            fail.append("a VehicleLights entry has neither socket nor bone")
        if len(unstuck) != 6 or any((x.get("socket") or "") not in ("HeadLight1c", "HeadLight2c")
                                    for x in unstuck):
            fail.append("expected exactly the 6 HeadLight1c/2c orphan sockets, got %d" % len(unstuck))
        if not any(c.get("class", "").endswith("LightComponent") for x in lights
                   for c in x["components"]):
            fail.append("VehicleLights component references are unresolved")
        if not any((x.get("type") or "").startswith("VEHLT_") for x in lights):
            fail.append("light Type enums are not resolved (ByteProperty FNames regressed)")

        # GRB-6 reads named values where the cooker kept them and class offsets where it did not
        offsets = {(o["offset"], o["value"]) for r in self.find(class_="RVehicleBatmobile")
                   for o in self.offset_only(r) if isinstance(o["value"], (int, float))}
        facts["offset-only values"] = len(offsets)
        if (0x1214, 640000.0) not in offsets:
            fail.append("vehicle offset 0x1214 = 640000 missing (offset-only decode regressed)")

        bank_rows = self.find(class_="AkBank")
        banks = {r["name"] for r in bank_rows}
        facts["banks"] = "%d objects / %d names" % (len(bank_rows), len(banks))
        if "BML_Engine" not in banks:
            fail.append("BML_Engine bank missing")

        facts["checks"] = "%d/%d grab checks passed" % (
            sum(1 for c in self.summary.get("checks", []) if c.get("pass")),
            len(self.summary.get("checks", [])))
        facts["schema"] = SCHEMA
        return fail, facts


# ----------------------------------------------------------------------------- CLI

def _print_rows(rows, limit=50):
    print("%-30s %-24s %-38s %8s %5s" % ("package", "class", "object", "bytes", "tags"))
    for r in rows[:limit]:
        print("%-30s %-24s %-38s %8d %5d" % (r["package"], r.get("class") or "-",
                                             (r.get("outer") or "") + "." + r["name"], r["size"],
                                             r.get("tag_count", 0)))
    if len(rows) > limit:
        print("... %d more" % (len(rows) - limit))


def _value(v):
    if isinstance(v, float):
        return "%.4f" % v
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="schema, invariants and spot checks")
    p = sub.add_parser("stats", help="totals and class census")
    p.add_argument("--json", action="store_true")
    for name, help_ in (("find", "list objects matching class/name/package"),
                        ("show", "one object with its named tags"),
                        ("tags", "flattened tags of one object"),
                        ("offsets", "offset-only primitives of one object")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("key", nargs="?" if name == "find" else None)
        p.add_argument("--class", dest="class_", default=None)
        p.add_argument("--name", default=None)
        p.add_argument("--package", default=None)
        p.add_argument("--native", action="store_true", default=None)
        p.add_argument("--tag", default=None, help="NAME or NAME=SUBSTR (named property filter)")
        p.add_argument("--value", default=None, help="substring of any tag value (named or offset-only)")
        p.add_argument("--json", action="store_true")
    p = sub.add_parser("curves", help="named sim curves with points")
    p.add_argument("key", nargs="?")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("lights", help="vehicle light rig from repeated VehicleLights structs")
    p.add_argument("--package", default=None)
    p.add_argument("--json", action="store_true")
    a = ap.parse_args()

    g = Grab(a.out)
    if a.cmd == "check":
        fail, facts = g.check()
        for k, v in facts.items():
            print("%-14s %s" % (k, v))
        if fail:
            print("\nFAIL")
            for f in fail:
                print("  -", f)
            return 1
        print("\nOK: grab output matches schema %d and its own summary." % SCHEMA)
        return 0
    if a.cmd == "stats":
        s = g.stats()
        if a.json:
            print(json.dumps(s, indent=1))
        else:
            print("objects   %d" % s["exports"])
            print("decoded   %d (%.2f%%)" % (s["decoded"], 100.0 * s["decoded"] / max(s["exports"], 1)))
            print("native    %d" % s["native"])
            print("packages  %d" % s["packages"])
            for k, v in s["classes"].items():
                print("  %-28s %5d" % (k, v))
        return 0
    if a.cmd == "find":
        rows = g.find(class_=a.class_, name=a.name, package=a.package, native=a.native,
                      tag=a.tag, value=a.value)
        if a.json:
            print(json.dumps(rows, indent=1))
        else:
            _print_rows(rows)
        return 0

    if a.cmd == "lights":
        out = g.lights(a.package)
        if a.json:
            print(json.dumps(out, indent=1))
        else:
            print("%-30s %-28s %-24s %5s %5s  %s" % ("package", "bone", "owner", "type", "mat", "components"))
            for x in out:
                comps = ", ".join(c["class"] or "?" for c in x["components"])
                print("%-30s %-28s %-24s %5s %5s  %s" % (x["package"], x["bone"] or "-",
                                                         x["owner"] or "-", x["type"], x["material_type"], comps))
        return 0
    if a.cmd == "curves":
        out = g.curves(a.key)
        if a.json:
            print(json.dumps(out, indent=1))
        else:
            for owner, curves in out.items():
                print(owner)
                for c in curves:
                    print("  %-34s %d points" % (c["name"], len(c["points"])))
                    print("    " + " ".join("(%g,%g)" % p for p in c["points"]))
        return 0

    row = g.one(a.key, a.package)
    if a.cmd == "show":
        info = {k: row.get(k) for k in ("package", "index", "outer", "name", "class", "size",
                                        "sha1", "tag_count", "stop")}
        tags = [{"path": p, "type": t.get("type"), "offset": t.get("offset"),
                 "value": _value(t.get("value")), "ref": t.get("ref"),
                 "items": len(t.get("items") or []) if "items" in t else None}
                for p, t in g.tags(row)]
        if a.json:
            print(json.dumps({"object": info, "tags": tags}, indent=1))
        else:
            for k, v in info.items():
                print("%-10s %s" % (k, v))
            print()
            for t in tags:
                extra = " ref=%s" % t["ref"] if t.get("ref") else ""
                if t["value"] is not None:
                    extra += " = %s" % t["value"]
                if t["items"] is not None:
                    extra += " [%d items]" % t["items"]
                print("  %-40s %-16s 0x%04X%s" % (t["path"], t["type"], t["offset"] or 0, extra))
        return 0
    if a.cmd == "tags":
        out = [{"path": p, "type": t.get("type"), "offset": t.get("offset"),
                "value": t.get("value"), "ref": t.get("ref")} for p, t in g.tags(row)]
        if a.json:
            print(json.dumps(out, indent=1))
        else:
            for t in out:
                print("%-46s %-16s 0x%04X  %s" % (t["path"], t["type"], t["offset"] or 0,
                                                  _value(t["value"]) if t["value"] is not None
                                                  else (t["ref"] or "")))
        return 0
    if a.cmd == "offsets":
        offs = g.offset_only(row)
        for o in offs:
            print("%-46s %-16s 0x%04X  %s" % (o["path"], o["type"], o["offset"] or 0, _value(o["value"])))
        if not offs:
            print("(no offset-only primitives)")
        return 0
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GrabError as e:
        print("grab_model:", e)
        sys.exit(2)
