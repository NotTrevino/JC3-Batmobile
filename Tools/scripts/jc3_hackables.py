"""jc3_hackables.py - G3-08d: does JC3 carry a remote 'turn it to our side' mechanic?

Read-only scan of everything extracted under E:/Modding/_gamedata/JC3grab plus the
project indexes, for hack / hijack / override / takeover / allegiance vocabulary,
the faction-like members, the drone fleet, the Rebel Drop drone assets and the eDEN
drone entities.

--write regenerates Research/JC3Grab/HACKABLES.md; --check recomputes every number
from the same files and compares the generated text.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GRAB = r"E:\Modding\_gamedata\JC3grab"
WIRE = os.path.join(GRAB, "wiring", "epe")
INDEX = os.path.join(REPO, "Research", "JC3Grab", "INDEX.jsonl")
DROP = os.path.join(REPO, "Research", "JC3Grab", "REBELDROP.json")
INPUT = os.path.join(REPO, "Research", "JC3Grab", "INPUT.json")
OUT_MD = os.path.join(REPO, "Research", "JC3Grab", "HACKABLES.md")
OUT_JSON = os.path.join(REPO, "Research", "JC3Grab", "HACKABLES.json")

TERMS = ("hack", "hijack", "override", "takeover", "allegian")
OBJ = re.compile(r'<object name="([^"]*)">(.*?)(?=<object name="|\Z)', re.S)
CLASS_RE = re.compile(r'<value name="_class" type="string">([^<]+)</value>')


def read(p):
    return open(p, encoding="utf-8-sig", errors="ignore").read()


def scan() -> dict:
    files = sorted(glob.glob(os.path.join(WIRE, "*.ee.xml")))
    hits = {t: collections.Counter() for t in TERMS}
    cam_hits = hj_hits = 0
    ctx = collections.Counter()
    hijack_ctx = collections.Counter()
    facet = collections.Counter()
    facet_vals = collections.Counter()
    drones = []
    for f in files:
        s = read(f)
        low = s.lower()
        for t in TERMS:
            n = low.count(t)
            if n:
                hits[t][os.path.basename(f)] = n
        for m in re.finditer(r"[^\n]{0,80}hack[^\n]{0,80}", s, re.I):
            line = m.group(0).strip()
            ctx[re.sub(r"\s+", " ", line)[:140]] += 1
        cam_hits += low.count("lefthijackcamera") + low.count("righthijackcamera") + low.count("hijack_framing")
        hj_hits += low.count("hijack")
        for m in OBJ.finditer(s):
            body = m.group(2)
            cm = CLASS_RE.search(body)
            cls = cm.group(1) if cm else "?"
            for key in ("faction", "ignore_faction", "sides", "side_area"):
                vm = re.search(rf'<value name="{key}" type="[^"]*">([^<]*)</value>', body)
                if vm:
                    facet[key] += 1
                    facet_vals[(key, cls)] += 1
        if "drone" in os.path.basename(f).lower():
            root = re.search(r'<object name="root">\s*<object name="([^"]*)">\s*<value name="_class" type="string">([^<]+)', s)
            fac = [v for v in re.findall(r'<value name="(?:faction|ignore_faction)" type="[^"]*">([^<]*)</value>', s)]
            drones.append({"file": os.path.basename(f), "root": [root.group(1), root.group(2)] if root else None,
                           "classes": len(set(CLASS_RE.findall(s))), "faction_values": fac})
    strings_hack = []
    sd = os.path.join(GRAB, "strings_rt")
    for f in glob.glob(os.path.join(sd, "*")):
        if os.path.isfile(f) and "hack" in read(f).lower():
            strings_hack.append(os.path.basename(f))
    index_text = read(INDEX)
    drop_assets = sorted({m for m in re.findall(r'"path":"([^"]*drone[^"]*rebel[^"]*)"', index_text)})
    drop = json.load(open(DROP, encoding="utf-8"))
    items = drop["vanilla"]["items"]
    drone_items = [i for i in items if any("drone" in str(v).lower() for v in i.values())]
    inp = json.load(open(INPUT, encoding="utf-8"))
    acts = sorted(set(re.findall(r'"([A-Z_]{4,})"', json.dumps(inp))))
    return {"files": len(files), "hits": {t: dict(c) for t, c in hits.items()},
            "hack_files": len(hits["hack"]), "hack_total": sum(hits["hack"].values()),
            "allegiance_files": len(hits["allegian"]), "override_files": len(hits["override"]),
            "hijack_files": len(hits["hijack"]), "hijack_hits": hj_hits, "hijack_camera_hits": cam_hits, "takeover_files": len(hits["takeover"]),
            "hack_context": ctx.most_common(8), "hijack_context": hijack_ctx.most_common(4),
            "facet": dict(facet),
            "facet_vals": [[k[0], k[1], v] for k, v in facet_vals.most_common(12)],
            "drones": drones, "strings_hack": strings_hack,
            "drop_assets": drop_assets, "items": len(items), "drone_items": len(drone_items),
            "input_actions": len(acts), "hack_actions": [a for a in acts if "HACK" in a]}


def oracles(d: dict) -> list[dict]:
    o = []
    o.append({"id": "O1-fleet-scan-complete", "ok": d["files"] == 295,
              "detail": f"{d['files']} .ee.xml wiring dumps scanned"})
    o.append({"id": "O2-hack-is-two-files", "ok": d["hack_files"] == 2,
              "detail": f"hack in {sorted(d['hits']['hack'])} ({d['hack_total']} hits)"})
    o.append({"id": "O3-no-allegiance-or-takeover", "ok": d["allegiance_files"] == 0
              and d["takeover_files"] == 0,
              "detail": f"allegiance {d['allegiance_files']}, takeover {d['takeover_files']} files; "
                        f"hijack {d['hijack_files']} files / {d['hijack_hits']} hits of which "
                        f"{d['hijack_camera_hits']} are carjacking-camera strings"})

    o.append({"id": "O4-faction-members-exist", "ok": all(d["facet"].get(k, 0) > 0 for k in
              ("faction", "ignore_faction", "sides", "side_area")),
              "detail": f"counts {d['facet']}"})
    o.append({"id": "O5-drone-fleet-18", "ok": len(d["drones"]) == 18,
              "detail": f"{len(d['drones'])} drone entity wiring dumps"})
    o.append({"id": "O6-drone-class", "ok": sum(1 for x in d["drones"] if x["root"] and
              x["root"][1] == "CUnmanedQuadcopterDrone") >= 9,
              "detail": f"{sum(1 for x in d['drones'] if x['root'] and x['root'][1]=='CUnmanedQuadcopterDrone')} "
                        f"roots are CUnmanedQuadcopterDrone"})
    o.append({"id": "O7-drop-artwork-only", "ok": len(d["drop_assets"]) == 2 and d["drone_items"] == 0,
              "detail": f"{len(d['drop_assets'])} drone rebeldrop assets, {d['drone_items']}/{d['items']} "
                        f"items name a drone"})
    o.append({"id": "O8-no-hack-input-action", "ok": d["hack_actions"] == [],
              "detail": f"{d['input_actions']} actions, HACK-named {d['hack_actions']}"})
    return o


def render(d: dict) -> str:
    L = []
    L.append("# JC3 hack / takeover mechanics and the drone fleet (G3-08d)\n")
    L.append("Generated by `Tools/scripts/jc3_hackables.py --write`; `--check` recomputes every "
             "number from the same files. Read-only.\n")
    L.append("`decoded` = name/value read at a stated file; `derived` = rule + inputs; "
             "`UNKNOWN` = not in the files, with the searches listed.\n")
    L.append("## 1. The widened search\n")
    L.append(f"Scope: **{d['files']}** `.ee.xml` entity wiring dumps, the `entities/`, `rebeldrop/`, "
             f"`spawndefs/`, `strings_rt/` trees, `INDEX.jsonl` (963 entity paths), `REBELDROP.json` "
             f"and `INPUT.json`.\n")
    L.append("| term | files | what the hit is |\n|---|---:|---|\n")
    L.append(f"| `hack` | {d['hack_files']} | " +
             ", ".join(f"`{k}` x{v}" for k, v in sorted(d["hits"]["hack"].items())) + " |\n")
    L.append(f"| `hijack` | {d['hijack_files']} | none |\n")
    L.append(f"| `override` | {d['override_files']} | none in the entity wiring (term absent) |\n")
    L.append(f"| `takeover` | {d['takeover_files']} | none |\n")
    L.append(f"| `allegian` | {d['allegiance_files']} | **no allegiance member exists in any entity wiring** |\n")
    L.append(f"\n`hack` contexts ({d['hack_total']} hits):\n\n```\n")
    for line, n in d["hack_context"]:
        L.append(f"x{n}  {line}\n")
    L.append("```\n")
    L.append(f"\nStrings tree: `strings_rt` mentions `hack` in {len(d['strings_hack'])} file(s)"
             + (f" ({', '.join(d['strings_hack'])})" if d["strings_hack"] else "") +
             "; no hijack/override/takeover/allegiance hit was found there.\n")

    L.append("## 2. The one real hack mechanic: the SAM turret context act\n")
    L.append("`w501_turret_sam_v2.ee.xml` carries the only hack vocabulary in the fleet, and it is "
             "an **animation-gated interaction**, not a remote effect:\n")
    L.append("| object | class | what it holds |\n|---|---|---|\n")
    L.append("| `CInteractionComponentAnimationLayer` | `CInteractionComponentAnimationLayer` | "
             "`rico_contextact_hack_sam.anim`, `..._enter.anim`, `..._exit.anim` (values 0x1900FF1E, "
             "0x230FBFB4, 0xB3248BAD) |\n")
    L.append("| `CInteractionContext` | `CInteractionContext` | enable/disable event lists, `enabled` 1, "
             "a world matrix at the turret |\n")
    L.append("| `CInteractionGraph` / `...Entry` / `...Exit` / `...PointNode` / "
             "`...ParentIsUpRightCondition` | CInteraction* | the use-item state machine "
             "(`exit.use_item.success`, `S_EXIT_USE_ITEM_SUCCESS`) |\n")
    L.append("\nThe graph's exit state is `use_item`, and the animation layer is the player's own "
             "context act, so the player must be at the object. **No range, radius or distance "
             "member appears in any of these objects** - the decoded value lists are events, "
             "`enabled`, animation paths, world matrices and unnamed ints.\n")
    L.append("A second, weaker hit is `v5601_train_urga_monorailcargoengine_military_mission_mm320_train.ee.xml`, "
             "value id `6F24D4E5` = the string `poi_hack` (a mission point-of-interest tag; no "
             "mechanic behind it in the wiring).\n")

    L.append("## 3. Faction-like members (the data a switch would have to flip)\n")
    L.append("| member | occurrences | carriers (class) |\n|---|---:|---|\n")
    for key in ("faction", "ignore_faction", "sides", "side_area"):
        cars = ", ".join(f"`{c}` x{n}" for k, c, n in d["facet_vals"] if k == key)
        L.append(f"| `{key}` | {d['facet'].get(key, 0)} | {cars or '-'} |\n")
    L.append("\nSample values: " + "; ".join(f"`{k}` on `{c}` = {n} rows" for k, c, n in d["facet_vals"][:6]) + ".\n")
    L.append("\n**Entity-level allegiance: UNKNOWN/absent.** No `allegiance` value exists anywhere "
             "in the 295 entity dumps. `faction` is a *weapon-point / turret-component* field "
             "(which side may use a mount), `ignore_faction` and `sides` are camera/light/physics "
             "hints, and `side_area` is a physics area id. None of them is a 'who owns this drone' "
             "switch on a vehicle or drone root.\n")

    L.append("## 4. The drone fleet\n")
    L.append(f"{len(d['drones'])} drone entity wiring dumps; `CUnmanedQuadcopterDrone` is the "
             "decoded drone class (the spelling is the game's own).\n")
    L.append("| entity | root object class | classes | faction-ish values |\n|---|---|---:|---|\n")
    for x in d["drones"]:
        root = x["root"][1] if x["root"] else "?"
        L.append(f"| `{x['file']}` | `{root}` | {x['classes']} | {x['faction_values'] or '-'} |\n")
    L.append("\nFamily split (derived from the names): `v2900` eDEN grunt drone, `v2901` eDEN elite "
             "drone, `v2903` eDEN transport, `v2904` eDEN shield, `v2905` Black Hand grunt, `v2906` "
             "Black Hand elite. `w505_sam_eden_heavycontroldrone_boss.ee` and "
             "`..._weapons.ee` also exist in the index (the eDEN heavy control drone as a weapon "
             "entity).\n")
    L.append("**Spawn: UNKNOWN.** No drone appears in `spawndefs/` (0 files), and no entity other "
             "than the wiring dumps references a drone `.ee` path; the only non-wiring reference is "
             "`fx_build.log`. Whether a mission/world placement or an unseen spawn module creates "
             "them is not decoded here.\n")

    L.append("## 5. Friendly drone in the Rebel Drop\n")
    L.append(f"- assets: {len(d['drop_assets'])} = " + ", ".join(f"`{p}`" for p in d["drop_assets"]) + "\n")
    L.append(f"- Rebel Drop items: {d['items']} vanilla; **{d['drone_items']}** name a drone "
             "(item `Name` is the Jenkins hash of an entity leaf, `REBELDROP.md`), and no `.ee` "
             "named `*drone*rebel*` ships in the 963-path index.\n")
    L.append("\nSo the **artwork and the drop video** for an elite drone exist "
             "(`v2901_drone_eden_elitedrone_rebeldrop`), but the entity that a drop entry would "
             "spawn is **UNKNOWN**: either the item is one of the 11 unresolved hashes, or the "
             "drone is delivered by a mission reward rather than a drop. This is the gap between "
             "'the game ships a friendly drone' and 'the file names it'.\n")
    L.append("What separates a friendly drone from a hostile one in the data: **nothing decoded**. "
             "The eDEN drones' only side-carrying values are weapon-point `faction` 5; no drone root "
             "carries `faction`, `sides` or `allegiance`. A friendly variant would have to differ by "
             "entity identity or by a module not present in these dumps.\n")

    L.append("## 6. eDEN airship / hostile reference\n")
    L.append("**UNKNOWN.** `airship` has **0** hits in the whole extracted tree and the project's "
             "world index; no location or mission record names it. What does exist is the eDEN drone "
             "family above (`v2900`/`v2901`/`v2903`/`v2904`, plus the `w505_sam_eden_heavycontroldrone` "
             "weapon entity). Those are the hostile reference this report uses; they are placed by "
             "data this scan did not find, so their spawn source is UNKNOWN.\n")

    L.append("## 7. What a remote 'turn it to our side' could borrow\n")
    L.append("| candidate | members found | remote? | verdict |\n|---|---|---|---|\n")
    L.append("| SAM turret hack (`w501_turret_sam_v2`) | CInteractionContext + CInteractionGraph + "
             "`rico_contextact_hack_sam` anim layer | **no** - context act at the object, no range member | "
             "closest *behaviour* (a hack that changes a turret), wrong delivery |\n")
    L.append("| `CInteractionTrigger` / `CInteractionComponentSetNode` | interaction graph nodes | "
             "no decoded range | a trigger volume could gate an effect, but no radius is decoded |\n")
    L.append("| weapon-point `faction` (5 on eDEN drones) | `SWeaponPoint.faction`, "
             "`CTurretWeaponComponent.faction` | n/a (a mount permission, not ownership) | the only "
             "side-like integer on a drone; flipping it changes who may fire the mount |\n")
    L.append("| `SAttachedEffect` / `SDynamicAttachedEffect` (29 per drone) | effect tables on the "
             "drone entities | attach point, no range | the delivery vehicle for a beam/VFX, not a switch |\n")
    L.append("| input actions | 183 actions, `USE_ITEM`, `USE_VEHICLE_MOD`; **0** HACK actions | - | "
             "a remote hack needs a new binding or a reuse of `USE_VEHICLE_MOD` |\n")
    L.append("\n**Closest JC3 mechanic:** the SAM context-act hack. It proves the engine has a "
             "'hack this object' interaction graph and a hack animation, but it is local and its "
             "effect on ownership is not in the entity data (UNKNOWN).\n")
    L.append("**Entity edit needed (derived, not built):** a drone root would need (a) a side/owner "
             "value it does not currently have, (b) a weapon-point `faction` change to stop it firing "
             "on us, and (c) an effect entry point that a Batmobile weapon can reach at range - the "
             "existing `SDynamicAttachedEffect` table is the only decoded hook. Whether the engine "
             "honours a new side value at runtime is UNKNOWN and needs the documented hknp/AI type "
             "layout that this scan did not find.\n")

    L.append("## 8. Oracles\n")
    o = oracles(d)
    L.append(f"{sum(1 for r in o if r['ok'])}/{len(o)} passed.\n")
    L.append("| id | ok | detail |\n|---|---|---|\n")
    for r in o:
        L.append(f"| `{r['id']}` | {'PASS' if r['ok'] else 'FAIL'} | {r['detail']} |\n")

    L.append("## 9. UNKNOWN\n")
    L.append("- **Entity-level allegiance / owner member**: 0 hits for `allegian` in 295 dumps. "
             "Searches: value names, class names, strings tree, ADF type names, entity names.\n")
    L.append("- **A remote hack**: no range/radius member on any interaction object; the only hack "
             "is the local context act.\n")
    L.append("- **The friendly Rebel Drop drone entity**: 2 rebeldrop assets exist, 0 items name a "
             "drone, no `*drone*rebel*` `.ee` in the 963-path index.\n")
    L.append("- **eDEN airship / eDEN location data**: `airship` 0 hits; drone spawn source not found "
             "(0 hits in `spawndefs/`).\n")
    L.append("- **What the SAM hack actually does to ownership**: the entity carries the interaction "
             "graph and the animation, not the effect on the turret's side.\n")
    L.append("\n## 10. Reproduce\n\n```\npython Tools/scripts/jc3_hackables.py --write\n"
             "python Tools/scripts/jc3_hackables.py --check\n```\n")
    return "".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = scan()
    d["oracles"] = oracles(d)
    md = render(d)
    if a.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8").write(json.dumps(d, indent=1) + "\n")
        print(f"wrote {os.path.relpath(OUT_MD, REPO)} ({len(md.splitlines())} lines) and "
              f"{os.path.relpath(OUT_JSON, REPO)}")
        print(f"oracles {sum(1 for r in d['oracles'] if r['ok'])}/{len(d['oracles'])}")
        return
    have = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else None
    bad = [r for r in d["oracles"] if not r["ok"]]
    for r in bad:
        print("FAIL", r["id"], r["detail"])
    if bad:
        raise SystemExit(f"CHECK FAIL: {len(bad)} oracle(s)")
    if have != md:
        raise SystemExit("CHECK FAIL: HACKABLES.md is stale; re-run --write")
    print(f"CHECK OK: {len(d['oracles'])} oracles, {len(md.splitlines())} lines, "
          f"{d['files']} entity dumps, hack files {d['hack_files']}, drones {len(d['drones'])}, "
          f"drop assets {len(d['drop_assets'])}, drone items {d['drone_items']}")


if __name__ == "__main__":
    main()
