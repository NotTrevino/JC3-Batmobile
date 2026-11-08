#!/usr/bin/env python3
"""t_light_entry11.py - which colour does BmAK use for built light entry 11, and is the build right?

Built light entry 11 (`Working/Lights/bm_lightrig.json`, origin `graph-object (T-L17)`) takes its
diffuse from JC3's own graph object `Front_Secondary_Head`. `Research/BatmobileGrab/LIGHTS.md`
prints the BmAK component's colour as the class default [255, 255, 255, 0]. This script decides
which one the BmAK game uses at run time by re-reading the component and its archetype out of
the shipped `Playable_Batmobile_SF.upk`, and by re-deriving the precedence chain
`grab_lights.py` implements:

  cooked component tags (only what differs from the archetype)
    -> the object's archetype (export record word 6)
    -> `Default__<class>` in Engine.upk / BmGame.upk
    -> the native default (in the executable, in no file)

The live reads use `grab_lights`' own helpers (`package`, `archetype_ref`, `fields_from`,
`class_defaults`, `resolve_component`), so the rule being tested is the rule that produced the
grab. Nothing is written except `Research/BatmobileGrab/LIGHT_ENTRY11.md`; no row, build file or
ledger is edited.

    python Tools/scripts/t_light_entry11.py --write
    python Tools/scripts/t_light_entry11.py --check
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_lights as GL  # noqa: E402  - the grab's own chain resolver
import upk_read as U  # noqa: E402

LIGHTS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.json")
LIGHTS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.md")
RIG = os.path.join(ROOT, "Working", "Lights", "bm_lightrig.json")
T14 = os.path.join(ROOT, "Working", "Translation", "t14_lights.json")
LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHT_ENTRY11.md")

PKG = "Playable_Batmobile_SF"
SOCKET = "BattleModeSpotLight"
TYPE = "VEHLT_BattleModeLight"
COMP_INDEX = 5371
BM_COLOUR = [255, 255, 255, 0]
BUILT_DIFFUSE = [0.6039, 0.6039, 0.9529]


def main(write: bool) -> int:
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    lights = json.load(open(LIGHTS_JSON, encoding="utf-8"))
    rig = json.load(open(RIG, encoding="utf-8"))
    t14 = json.load(open(T14, encoding="utf-8"))
    ledger = {r["id"]: r for r in (json.loads(l) for l in open(LEDGER, encoding="utf-8")
                                  if l.strip())}
    md_lights = open(LIGHTS_MD, encoding="utf-8").read()
    script = open(os.path.join(HERE, "grab_lights.py"), encoding="utf-8").read()

    entry = None
    for veh in lights["vehicles"]:
        if veh["package"] != PKG:
            continue
        for e in veh["entries"]:
            if e["socket"] == SOCKET and e["type"] == TYPE:
                entry = e
    ok(entry is not None, f"LIGHTS.json holds {PKG}/{SOCKET}/{TYPE}")
    assert entry is not None
    comp = entry["components"][0]
    built = rig["rows"][11]
    row14 = next(r for r in t14["rows"] if r["id"] == "T-L17")

    ok(comp["class"] == "SpotLightComponent" and comp["index"] == COMP_INDEX,
       f"the light's component is SpotLightComponent export {COMP_INDEX}",
       f'{comp["class"]} {comp["index"]}')
    ok(comp["fields"]["LightColor"] == BM_COLOUR,
       f"the grab records LightColor {BM_COLOUR}", str(comp["fields"]["LightColor"]))
    ok(comp["field_sources"]["LightColor"].startswith("class default"),
       "the grab says the colour came from the class default, not the component",
       comp["field_sources"]["LightColor"])
    others = [k for k, v in comp["field_sources"].items() if k != "LightColor"]
    ok(all(comp["field_sources"][k] == "component" for k in others) and len(others) == 7,
       f"the other 7 fields are serialised on the component ({len(others)})")
    ok(comp["gaps"] == [], "the archetype chain has no gaps")

    # ---------------------------------------------------------------- the bytes, re-read live
    upk = os.path.join(GL.GAME, PKG + ".upk")
    engine = os.path.join(GL.GAME, "Engine.upk")
    ok(os.path.isfile(upk) and os.path.isfile(engine),
       "the shipped packages are on disk (Playable_Batmobile_SF.upk, Engine.upk)")
    pkg = GL.package(upk)
    word = GL.archetype_ref(pkg, COMP_INDEX)
    tags, _end, _why = U.best_walk(pkg, pkg.data(COMP_INDEX))
    serialised = GL.fields_from(tags, "SpotLightComponent", GL.LIGHT_FIELDS)
    cdo = GL.class_defaults("SpotLightComponent", GL.LIGHT_FIELDS)
    vals, srcs, gaps = GL.resolve_component(PKG, {"class": "SpotLightComponent",
                                                  "index": COMP_INDEX})

    ok(word == 0, "export record word 6 (archetype) is 0 - the instance inherits straight from "
       "the class default", str(word))
    ok(len(tags) == 12, f"the component serialises 12 tags ({len(tags)})", str(len(tags)))
    ok("LightColor" not in serialised,
       "no tag on the component maps to LightColor")
    ok(serialised == {"InnerConeAngle": 5.0, "OuterConeAngle": 15.0, "Radius": 4500.0,
                      "FalloffExponent": 1.0, "Brightness": 0.0, "CastDynamicShadows": False,
                      "CastShadows": False},
       "the component's serialised fields are the 7 around the colour", str(serialised))
    ok(cdo["LightColor"][0] == BM_COLOUR and "Default__LightComponent" in cdo["LightColor"][1],
       f"Default__LightComponent's CDO carries LightColor {BM_COLOUR}", str(cdo["LightColor"]))
    ok(vals["LightColor"] == BM_COLOUR
       and srcs["LightColor"] == "class default: `Default__LightComponent` (Engine.upk)",
       "resolve_component lands on the CDO colour with that source", str(srcs["LightColor"]))
    ok(vals["Brightness"] == 0.0 and srcs["Brightness"] == "component",
       "Brightness 0.0 is serialised on the component itself")
    ok(gaps == [], "resolve_component reports no gap")

    # ---------------------------------------------------------------- the published table
    row_md = (f"| {PKG} | `{SOCKET}` | {TYPE} | SpotLightComponent | [255, 255, 255, 0] | "
              "CDO `Default__LightComponent` (Engine.upk) | 0.0 | component | 4500.0 | 5.0 | "
              "15.0 |")
    ok(row_md in md_lights, "LIGHTS.md prints that row with the CDO colour")
    ok("values\ncome from the component itself, then its archetype, then `Default__<class>`"
       in md_lights,
       "LIGHTS.md states the precedence (component -> archetype -> Default__<class>)")
    ok("Every field keeps the first source that carried it" in script,
       "grab_lights.py resolves in that same order (first source that carried the field)")

    # ---------------------------------------------------------------- the built entry
    ok(built["index"] == 11 and built["origin"] == "graph-object (T-L17)",
       "bm_lightrig entry 11 is the T-L17 graph-object entry", built["origin"])
    dif = [built["members"][k]["v"] for k in ("diffuse.R", "diffuse.G", "diffuse.B")]
    ok(dif == BUILT_DIFFUSE, f"the built diffuse is {BUILT_DIFFUSE}", str(dif))
    ok(all("Front_Secondary_Head" in built["members"][k]["src"]
           for k in ("diffuse.R", "diffuse.G", "diffuse.B")),
       "all three channels cite the JC3 graph object `Front_Secondary_Head`")
    ok(tuple(dif) != (1.0, 1.0, 1.0),
       "the built colour is not the BmAK colour (255/255 = 1.0, 1.0, 1.0)")
    ok(row14["socket"] == SOCKET and row14["bmak"]["colour"] == BM_COLOUR,
       "T-18's row T-L17 already records the BmAK colour [255, 255, 255, 0]",
       str(row14["bmak"]["colour"]))
    ok(row14["bmak"]["brightness"] == 0.0 and row14["bmak"]["radius_ue"] == 4500.0
       and row14["bmak"]["cone_outer"] == 15.0,
       "the row also records brightness 0.0, radius 4500, outer cone 15",
       str((row14["bmak"]["brightness"], row14["bmak"]["radius_ue"],
            row14["bmak"]["cone_outer"])))
    ok("LightColor 255,255,255,0" in " ".join(map(str, ledger["T-L17"]["cells"])),
       "the ledger row T-L17 prints LightColor 255,255,255,0 in its 'now' cell")
    ok(ledger["T-L17"]["dispo"] == "next",
       "T-L17 is still `next` (the change is not applied)", ledger["T-L17"]["dispo"])

    # ---------------------------------------------------------------- the document
    L: list[str] = []
    ap = L.append
    ap("# Built light entry 11: which colour does BmAK use?")
    ap("")
    ap("**Answer: white, `LightColor = [255, 255, 255, 0]` (i.e. 1.0, 1.0, 1.0 in the JC3 0..1")
    ap("scale). The built entry's `0.6039, 0.6039, 0.9529` is JC3's own graph-object colour, not")
    ap("the BmAK lamp's, so as a copy of BmAK the built colour is wrong.** The row that carries")
    ap("it is **`T-L17`** (build entry 11, origin `graph-object (T-L17)`); its correct BmAK colour")
    ap("is `[255, 255, 255, 0]`. Nothing was edited.")
    ap("")
    ap("## The precedence rule, from the bytes")
    ap("")
    ap("A cooked UE3 component serialises only the properties that differ from its archetype, and")
    ap("a tag carries `(type, struct offset, value)` with no name. `grab_lights.py` therefore")
    ap("resolves each field down a chain and keeps the **first link that carried it**:")
    ap("")
    ap("1. the component's own serialised tags,")
    ap("2. the object's archetype - export record word 6 (`archetype_ref`), following an import")
    ap("   chain when the word is negative,")
    ap("3. `Default__<class>` (and its parent CDOs) in `Engine.upk` / `BmGame.upk`,")
    ap("4. the native default, which is compiled into the executable and is in no file.")
    ap("")
    ap("`Research/BatmobileGrab/LIGHTS.md` states the same rule in its G1-17 section: values")
    ap("\"come from the component itself, then its archetype, then `Default__<class>` in")
    ap("`Engine.upk` / `BmGame.upk`\", and `grab_lights.py` implements it in `resolve_component`")
    ap("(\"Every field keeps the first source that carried it\", `field_sources`).")
    ap("")
    ap("### This light, read live out of the shipped packages")
    ap("")
    ap(f"Subject: `{PKG}.upk`, export **{COMP_INDEX}** (`Batmobile.SpotLightComponent`), the")
    ap("single component of the `BattleModeSpotLight` / `VEHLT_BattleModeLight` entry:")
    ap("")
    ap("| link | bytes read | carries LightColor? |")
    ap("|---|---|---|")
    ap(f"| component {COMP_INDEX} | {len(tags)} tags; word 6 (archetype) = **{word}** | **no** - "
       "no tag maps to the LightColor offset |")
    ap(f"| archetype | word 6 = 0, so the instance inherits straight from the class default | "
       "n/a - no archetype object in between |")
    ap("| `Default__LightComponent` (Engine.upk) | `LightColor = [255, 255, 255, 0]` (FColor, read "
       "B,G,R,A) | **yes** - this is the value the chain lands on |")
    ap("")
    ap("What the component *does* serialise (the 7 fields around the colour): " +
       ", ".join(f"`{k} = {v}`" for k, v in serialised.items()) + ".")
    ap(f"Its `Brightness` is the component's own `0.0`; its radius/cone are `4500.0` / "
       f"`{serialised['InnerConeAngle']}`..`{serialised['OuterConeAngle']}`. The chain reports")
    ap(f"no gap. `resolve_component` returns LightColor `{vals['LightColor']}` from")
    ap(f"`{srcs['LightColor']}`, and the CDO read of `SpotLightComponent`'s parent")
    ap(f"(`{cdo['LightColor'][1]}`) carries the same value.")
    ap("")
    ap("**So at run time the BmAK light's colour is the class default white.** Alpha 0 in the")
    ap("`FColor` is the unused fourth byte for a light, not transparency: the three colour")
    ap("channels are 255, 255, 255. (Derived, not decoded: with `Brightness = 0.0` the lamp")
    ap("contributes nothing until a script raises it; the colour it then shows is this white.)")
    ap("")
    ap("## What the build has instead")
    ap("")
    ap("`Working/Lights/bm_lightrig.json` entry 11 is the T-L17 graph-object entry. Its colour is")
    ap("the JC3 asset's own authored diffuse, decoded from the entity graph object")
    ap("`Front_Secondary_Head`:")
    ap("")
    ap("| member | built value | source recorded in the build |")
    ap("|---|---:|---|")
    for k in ("diffuse.R", "diffuse.G", "diffuse.B"):
        m = built["members"][k]
        ap(f"| `{k}` | {m['v']} | {m['src'].replace('|', '/')} |")
    ap(f"| `preset_id` | {built['members']['preset_id']['v']} | "
       f"{built['members']['preset_id']['src'].replace('|', '/')} |")
    ap("")
    ap("That graph object is a JC3-side preset (`Front_Secondary_Head`, hash 3189390601), so")
    ap("0.6039/0.6039/0.9529 is a colour JC3 authored for its own light, not a value BmAK holds.")
    ap("`T-18`'s row T-L17 already prints the BmAK side correctly - `LightColor 255,255,255,0`,")
    ap("`B 0.0`, `cone 5.0/15.0`, `R 4500.0` - and then proposes the graph values. The build")
    ap("implements the proposal, which is where the two numbers part.")
    ap("")
    ap("## The correction (given, not applied)")
    ap("")
    ap("| field | built now | BmAK (correct) | JC3 0..1 form |")
    ap("|---|---|---|---|")
    ap("| colour | 0.6039, 0.6039, 0.9529 | `LightColor [255, 255, 255, 0]` | **1.0, 1.0, 1.0** |")
    ap("| range | 10.0 | `Radius 4500.0` | 4500.0 (bridge decisions belong to T-18) |")
    ap("| angle | 60.0 | `OuterConeAngle 15.0` | 15.0 |")
    ap("")
    ap("Row to change: **`T-L17`** (`dispo: next`, never applied). Its `proposed` cell and the")
    ap("`bm_lightrig` entry 11 that mirrors it should carry `diffuse 1.000,1.000,1.000` for a")
    ap("BmAK-faithful lamp. The range/angle columns follow the same authorship difference and are")
    ap("listed only so the change is not half-made; whether to prefer BmAK's 4500/15 or the")
    ap("JC3 graph's 10/60 is a fidelity decision, not a byte question.")
    ap("")
    ap("## UNKNOWNs")
    ap("")
    ap("* **Whether anything at run time changes the colour**: the entity graph or Kismet could")
    ap("  set a colour on the component. The shipped default is white; a script override is not")
    ap("  decodable from these files and no game was launched (test ban).")
    ap("* **Whether T-L17 should be BmAK-faithful at all**: the row's intent may be \"give the")
    ap("  graph preset a module row that matches JC3's own look\". In that reading the built")
    ap("  colour is a deliberate artist choice, not an error - but it is still not the BmAK value")
    ap("  the row's `now` cell prints.")
    ap("* **Brightness semantics**: BmAK's 0.0 does not map 1:1 onto JC3's `multiplier` /")
    ap("  `min_luminosity`; the bridge is T-18's, not this audit's.")
    ap("")
    ap("## Oracles re-run by `--check`")
    ap("")
    for c in checks:
        ap(f"* {'PASS' if c['ok'] else 'FAIL'} {c['oracle']}")
    ap("")
    ap("## Labels")
    ap("")
    ap("Decoded: the live package reads (archetype word, 12 tags, the 7 serialised fields, the CDO")
    ap("colour), `LIGHTS.json` / `LIGHTS.md` / `bm_lightrig.json` / `t14_lights.json` / the ledger")
    ap("cell. Derived: the run-time conclusion (white), the JC3 0..1 form, the change list.")
    ap("UNKNOWN: the three items above.")
    ap("")
    text = "\n".join(L)

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    if failed:
        return 1
    if write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(OUT, ROOT).replace(os.sep, '/')}")
        return 0
    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if current != text:
        for line in difflib.unified_diff(current.splitlines(), text.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        print("FAIL document differs from the regenerated text")
        return 1
    print("PASS document: LIGHT_ENTRY11.md matches the regenerated text")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write LIGHT_ENTRY11.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
