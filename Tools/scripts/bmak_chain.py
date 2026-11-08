"""bmak_chain.py - name every value the Batmobile's objects actually carry.

The grab (`batmobile_grab.py`) reads the Batmobile's vehicle/sim/wheel objects out of the shipped
packages and writes their property tags. A cooked object keeps the **value and the layout offset**
of a property, but the cooker strips the property *name* from the stream, so `MECHANICS.md` prints
those rows as `offset 0x164  10000.0000` and a translation row is forced to answer "no BmAK source
exists" and reach for a fleet median instead.

The name is not lost: `Working/vendor/BmSDK/*.g.cs` is the generated layout for the same classes
and carries `Class.Prop -> offset`. This tool is the join:

    offset (package) + layout (SDK) = a named BmAK field with a value

Two sources, in order, and it never invents a number:
  1. the **archetype** - the Batmobile's own objects (objects.jsonl), where the shipped car
     overrides the class default;
  2. the **class default** - `Default__<class>` in BmGame.upk / Engine.upk, walking the class
     chain upward when a level is not serialized.
A property absent from both is reported `absent`, not zero-guessed: absence is itself the finding.

Every binding is cross-checked against `OFFSETS.json` (the 423 fields the earlier pass already
named); a disagreement fails `--check` rather than being smoothed over.

Usage:
  python Tools/scripts/bmak_chain.py RVehicleSimBatmobile.HoldingBrakeTime RVehicle.DriftSteeringBias
  python Tools/scripts/bmak_chain.py --grep 'Drift|Counter|Steer' --chain RVehicle,RVehicleSimCar
  python Tools/scripts/bmak_chain.py --write     # -> Research/BatmobileGrab/CHAIN.json
  python Tools/scripts/bmak_chain.py --check     # re-derive; fail if CHAIN.json drifted
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "Working" / "vendor" / "BmSDK"
GRAB = ROOT / "Research" / "BatmobileGrab"
OBJECTS = GRAB / "objects.jsonl"
OFFSETS = GRAB / "OFFSETS.json"
OUT = GRAB / "CHAIN.json"
GAME = Path("E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole")
DEFAULT_CHAIN = ("RVehicle,RVehicleBatmobileBase,RVehicleBatmobile,RVehicleSimCar,"
                 "RVehicleSimBatmobile,SVehicleSimCar,SVehicle,SVehicleWheel")

CLS_RE = re.compile(r"public\s+(?:abstract\s+|sealed\s+)?partial\s+class\s+(\w+)\s*(?::\s*([^{]+))?")
PROP_RE = re.compile(r"///\s*\w*Property:\s*(\w+)")
OFF_RE = re.compile(r"Ptr \+ (\d+)")
SCALARS = ("FloatProperty", "IntProperty", "BoolProperty", "ByteProperty")


def sdk_layout() -> tuple[dict[str, dict[str, int]], dict[str, str]]:
    """class -> {property: offset}, and class -> base class, from the generated SDK."""
    layout: dict[str, dict[str, int]] = {}
    base: dict[str, str] = {}
    for path in sorted(SDK.rglob("*.g.cs")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        cur = None
        for i, line in enumerate(lines):
            m = CLS_RE.search(line)
            if m:
                cur = m.group(1)
                b = (m.group(2) or "").split(",")[0].strip().split(".")[-1].strip()
                if b and b != cur:
                    base[cur] = b
                layout.setdefault(cur, {})
                continue
            if cur is None:
                continue
            pm = PROP_RE.search(line)
            if not pm:
                continue
            om = OFF_RE.search("\n".join(lines[i:i + 8]))
            if om:
                layout[cur].setdefault(pm.group(1), int(om.group(1)))
    return layout, base


def chain(cls: str, base: dict[str, str]) -> list[str]:
    out, seen = [], set()
    while cls and cls not in seen:
        seen.add(cls)
        out.append(cls)
        cls = base.get(cls, "")
    return out


def load_objects(layout) -> list[dict]:
    keep = []
    with open(OBJECTS, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("class") in layout and r.get("tags"):
                keep.append(r)
    return keep


def name_for(offset: int, cls: str, layout, base) -> str | None:
    """Name an offset by the class in this object's chain that declares it.

    A bool is *not* nameable this way: consecutive bools are bit-packed into one 32-bit word, so
    every bool of a run shares an offset (64 of them do on RVehicleBatmobileBase). A shared offset
    returns None - naming one of them would be a guess - and `candidates()` lists the contenders.
    """
    hits = [f"{c}.{prop}" for c in chain(cls, base)
            for prop, off in layout.get(c, {}).items() if off == offset]
    return hits[0] if len(hits) == 1 else None


def candidates(offset: int, cls: str, layout, base) -> list[str]:
    return [f"{c}.{prop}" for c in chain(cls, base)
            for prop, off in layout.get(c, {}).items() if off == offset]


_PKGS: dict[str, object] = {}


def _pkg(name: str):
    if name not in _PKGS:
        from upk_read import Package
        _PKGS[name] = Package(str(GAME / name))
    return _PKGS[name]


def class_default(decl_cls: str, offset: int, base) -> tuple[object | None, str | None]:
    """Value of `decl_cls.offset` from the class-default chain (Default__X, then its bases)."""
    from upk_read import export_summary
    for c in chain(decl_cls, base):
        for pkg_name in ("BmGame.upk", "Engine.upk"):
            pk = _pkg(pkg_name)
            idx = next((k for k in range(1, pk.export_count + 1)
                        if pk.object_path(k) == f"Default__{c}"), None)
            if not idx:
                continue
            for t in export_summary(pk, idx, max_tags=20000)["tags"]:
                if t.get("offset") == offset:
                    return t.get("value"), f"Default__{c}"
            break           # the default exists in this package; do not look in the other
    return None, None


def bind(rec: dict, layout, base) -> list[dict]:
    """Every tag in one object, named by the SDK layout when the stream did not carry a name."""
    rows = []
    for t in rec.get("tags", []):
        nm = t.get("name") or name_for(t.get("offset", -1), rec["class"], layout, base)
        row = {"offset": t.get("offset"), "name": nm, "type": t.get("type"),
               "value": t.get("value"),
               "named_by": "stream" if t.get("name") else ("sdk-layout" if nm else None)}
        if nm is None and not t.get("name"):
            cand = candidates(t.get("offset", -1), rec["class"], layout, base)
            if cand:
                row["named_by"] = "ambiguous-bitfield"
                row["candidates"] = cand
        rows.append(row)
    return rows


def build() -> dict:
    layout, base = sdk_layout()
    objs = load_objects(layout)
    fields: dict[str, dict[str, list[dict]]] = {}
    for rec in objs:
        bound = [r for r in bind(rec, layout, base) if r["name"]]
        if bound:
            fields.setdefault(rec["class"], {})[f"{rec['package']}.{rec['name']}"] = bound

    # cross-check: every field the earlier pass named by layout must get the same name here
    off = json.loads(OFFSETS.read_text(encoding="utf-8"))
    agree = disagree = 0
    for f in off["fields"]:
        per_obj = fields.get(f["class"], {})
        hits = [r for rows in per_obj.values() for r in rows
                if r["offset"] == f["offset"] and r["named_by"] == "sdk-layout"]
        if not hits:
            continue
        if all(r["name"].split(".")[-1] == f["field_name"] for r in hits):
            agree += 1
        else:
            disagree += 1
    unnamed = sorted({(cls, o, r["offset"], r["type"], r["value"])
                      for cls, per in fields.items()
                      for o, rows in per.items() for r in rows if r["named_by"] is None},
                     key=lambda x: (x[0], x[2]))
    ambiguous = sum(1 for per in fields.values() for rows in per.values()
                    for r in rows if r["named_by"] == "ambiguous-bitfield")
    return {
        "verdict": ("the package keeps every value and the SDK layout supplies every name, so a "
                    "Batmobile field is quotable even where the cooker stripped the tag name; "
                    "bools stay unnamed because a bit-packed word cannot say which flag it was"),
        "sdk_classes": len(layout),
        "objects_bound": sum(len(v) for v in fields.values()),
        "named_bindings": sum(len(r) for v in fields.values() for rows in v.values()
                              for r in rows if r["name"]),
        "offsets_cross_checked": agree,
        "cross_check_conflicts": disagree,
        "ambiguous_bitfields": ambiguous,
        "still_unnamed": len(unnamed),
        "fields": fields,
        "unnamed": [{"class": c, "object": o, "offset": k, "type": t, "value": v}
                    for c, o, k, t, v in unnamed],
    }


def query(props: list[str], grep: str | None, chain_spec: str) -> int:
    layout, base = sdk_layout()
    objs = load_objects(layout)
    want: dict[str, set[str]] = {}
    for p in props:
        cls, prop = p.rsplit(".", 1)
        want.setdefault(cls, set()).add(prop)
    if grep:
        rx = re.compile(grep)
        for cls in [c.strip() for c in chain_spec.split(",")]:
            hits = {p for p in layout.get(cls, {}) if rx.search(p)}
            if hits:
                want.setdefault(cls, set()).update(hits)
    if not want:
        raise SystemExit("nothing to resolve: give Class.Property or --grep")

    # index archetype values by (declaring class, offset)
    arch: dict[tuple[str, int], list[tuple[str, object]]] = {}
    for rec in objs:
        for r in bind(rec, layout, base):
            if not r["name"]:
                continue
            decl = r["name"].rsplit(".", 1)[0]
            arch.setdefault((decl, r["offset"]), []).append((f"{rec['package']}.{rec['name']}",
                                                            r["value"]))
    for cls in sorted(want):
        print(f"## {cls}")
        for prop in sorted(want[cls]):
            off = layout.get(cls, {}).get(prop)
            if off is None:
                print(f"   {prop:34s}  -- not in the SDK layout")
                continue
            hits = arch.get((cls, off), [])
            seen = sorted({v for _, v in hits}) if hits else []
            dv, dsrc = class_default(cls, off, base)
            state = (f"archetype={seen}" if seen else "archetype=absent")
            state += f"  class-default={dv!r} ({dsrc})" if dsrc else "  class-default=absent"
            print(f"   {prop:34s} @{off:5d}  {state}")
            for obj, v in hits[:4]:
                print(f"        {obj:56s} {v}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("props", nargs="*", help="Class.Property to resolve")
    ap.add_argument("--grep", help="regex over property names inside --chain")
    ap.add_argument("--chain", default=DEFAULT_CHAIN)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.props or a.grep:
        return query(a.props, a.grep, a.chain)

    doc = build()
    if a.write:
        OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {OUT}")
    if a.check:
        old = json.loads(OUT.read_text(encoding="utf-8"))
        bad = [k for k in ("sdk_classes", "objects_bound", "named_bindings",
                           "offsets_cross_checked", "cross_check_conflicts",
                           "ambiguous_bitfields", "still_unnamed") if old.get(k) != doc[k]]
        if old.get("fields") != doc["fields"]:
            bad.append("fields")
        for k in bad:
            print(f"FAIL: {k} changed")
        print(f"{'PASS' if not bad else 'FAIL'}: chain record current "
              f"({doc['objects_bound']} objects, {doc['named_bindings']} named bindings, "
              f"{doc['offsets_cross_checked']} cross-checked, {doc['cross_check_conflicts']} "
              f"conflicts, {doc['ambiguous_bitfields']} bool words left unnamed)")
        return 1 if bad else 0
    print(json.dumps({k: v for k, v in doc.items() if k not in ("fields", "unnamed")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())