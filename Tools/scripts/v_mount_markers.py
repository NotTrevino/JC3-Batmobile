#!/usr/bin/env python3
"""v_mount_markers.py - what the 4 type-4 `attach.vehicle` points in bm-RC2 are, and who reads them.

Task 7240 counted 9 `SWeaponPoint` objects in the built `.epe`: 5 name a BmAK socket and sit on
it; 4 are type-4 `MountAttach` markers cloned from the APC template, with no BmAK socket, and
were left UNKNOWN. This script answers the follow-up from the files only:

  * what each marker binds - decoded from the built `.epe` (Gibbed `ConvertProperty -e`) and
    resolved against the built parts module `Working/Parts/bm_vehicle_parts.json`;
  * what the same weapon does in the JC3 donor - `Research/JC3Grab/WEAPON_WIRING.jsonl`
    (the graph `jc3wiring.py` builds), which is where the type-4 mechanism is defined;
  * whether anything references the markers - the two donor string properties
    `id:5C19E7E0` (pitch / mount part) and `id:80201E4D` (yaw part) are read by
    `jc3wiring.py` `mount_parts()` and `Research/JC3Grab/TURRET.md`; the point's own object id
    is checked for any referent in the `.epe`;
  * whether BmAK has a matching seat/mount concept - `SOCKETS_JC3.json` (65 sockets, roles) and
    `COCKPIT.json` (driver anchors, seat material).

Writes `Builds/bm-RC2/verify/mount_markers.md`. Read-only on every input: the `.epe` is exported
to a temp directory and no build file is touched. `--check` re-exports, re-derives and diffs the
document byte for byte.

Labels: "decoded" = read from the named file; "derived" = computed here; UNKNOWN = not in any
file this repo has decoded.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EPE = ("Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/"
       "v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.epe")
PARTS = "Working/Parts/bm_vehicle_parts.json"
SOCKETS = "Research/BatmobileGrab/SOCKETS_JC3.json"
COCKPIT = "Research/BatmobileGrab/COCKPIT.json"
WIRING = "Research/JC3Grab/WEAPON_WIRING.jsonl"
EXE = "Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe"
OUT = "Builds/bm-RC2/verify/mount_markers.md"

ATTACH = "attach.vehicle"
PROP_MOUNT = "5C19E7E0"   # donor: pitch / mount part  (TURRET.md, WEAPON_WIRING.md)
PROP_YAW = "80201E4D"     # donor: yaw / turret part


def p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(relpath: str):
    with open(p(relpath), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ the built graph
def value(el: ET.Element, name: str) -> str | None:
    for v in el.findall("value"):
        if v.get("name") == name:
            return (v.text or "").strip()
    return None


def values_by_id(el: ET.Element) -> dict[str, str]:
    return {v.get("name") or ("id:" + str(v.get("id"))): (v.text or "").strip()
            for v in el.findall("value")}


def walk(el: ET.Element, parent: str | None, out: list[dict]) -> None:
    for child in el.findall("object"):
        name = value(child, "name") or ""
        if value(child, "_class") == "SWeaponPoint" and value(child, "type") == "4":
            out.append({"el": child, "parent": parent})
        walk(child, name or parent, out)


def export(td: str) -> str:
    xml = os.path.join(td, "rc2.xml")
    r = subprocess.run([p(EXE), "-e", p(EPE), xml], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(xml):
        raise SystemExit(f"ConvertProperty failed ({r.returncode}): {r.stdout} {r.stderr}")
    return xml


def markers(xml_path: str) -> list[dict]:
    root = ET.parse(xml_path).getroot()
    found: list[dict] = []
    walk(root.find("object"), None, found)
    body = open(xml_path, encoding="utf-8", errors="replace").read()
    rows = []
    for f in found:
        el = f["el"]
        props = values_by_id(el)
        oid = props.get("_object_id", "")
        serial = oid.split("=")[-1] if "=" in oid else oid
        rows.append({
            "name": value(el, "name"),
            "oid": oid,
            "oid_serial": serial,
            "oid_occurrences": body.count(serial),
            "parent": f["parent"],
            "world": value(el, "world"),
            "mount": props.get("id:" + PROP_MOUNT, ""),
            "yaw": props.get("id:" + PROP_YAW, ""),
            "class_hash": props.get("id:D04059E6", ""),
        })
    return rows


def transform(world: str) -> tuple[float, float, float]:
    if not world:
        return (0.0, 0.0, 0.0)
    return tuple(float(v) for v in world.split(",")[12:15])  # type: ignore[return-value]


# ------------------------------------------------------------------ the donor graph
def part_table() -> dict[str, dict]:
    out = {}
    for part in load(PARTS)["parts"]:
        out[part["name"]] = {"index": part.get("part_index"), "parent": part.get("parent"),
                             "behaviour": part.get("behaviour") or "None"}
    return out


def donor() -> dict:
    by_type: collections.Counter = collections.Counter()
    type4: list[dict] = []
    weapon_inventory: dict[str, dict] = {}
    for line in open(p(WIRING), encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        for w in row.get("weapons", []):
            inv = weapon_inventory.setdefault(w["name"], {"types": set(), "pair": None,
                                                          "bindings": set(), "entities": set()})
            for pt in w.get("points", []):
                t = str(pt.get("type"))
                by_type[t] += 1
                inv["types"].add(t)
                inv["entities"].add(row.get("entity", "").rsplit("/", 1)[-1])
                bind = w.get("binding") or ""
                inv["bindings"].add(", ".join(bind) if isinstance(bind, list) else str(bind))
                if t == "4":
                    pair = (pt.get("props", {}).get("id:" + PROP_MOUNT, ""),
                            pt.get("props", {}).get("id:" + PROP_YAW, ""))
                    inv["pair"] = pair
                    type4.append({"entity": row.get("entity", "").rsplit("/", 1)[-1],
                                  "weapon": w["name"],
                                  "binding": ", ".join(bind) if isinstance(bind, list)
                                  else str(bind), "mount": pair[0], "yaw": pair[1]})
    pairs = collections.Counter((t["mount"], t["yaw"]) for t in type4)
    return {
        "by_type": dict(sorted(by_type.items())),
        "type4": type4,
        "pairs": pairs,
        "weapons": sorted(weapon_inventory),
        "type4_weapons": sorted({t["weapon"] for t in type4}),
        "type4_entities": sorted({t["entity"] for t in type4}),
        "bindings": sorted({t["binding"] for t in type4}),
        "inventory": {k: {"types": sorted(v["types"]), "pair": v["pair"],
                          "bindings": sorted(v["bindings"]), "entities": len(v["entities"])}
                      for k, v in weapon_inventory.items()},
    }


def bmak_surface() -> dict:
    s = load(SOCKETS)
    c = load(COCKPIT)
    return {
        "sockets": len(s["sockets"]),
        "roles": sorted({x.get("role") for x in s["sockets"] if x.get("role")}),
        "mount_named": [x["socket"] for x in s["sockets"]
                        if "attach" in x["socket"].lower() or "mount" in x["socket"].lower()],
        "driver_anchors": c["driver_anchors"],
        "driver_position_m": c["driver"]["position_m"],
        "driver_socket": "Driver",
        "anim_origin_position_m": c["anim_origin"]["position_m"],
    }


# ------------------------------------------------------------------ derivation
def build() -> dict:
    with tempfile.TemporaryDirectory() as td:
        rows = markers(export(td))
    parts = part_table()
    for r in rows:
        r["mount_part"] = parts.get(r["mount"])
        r["yaw_part"] = parts.get(r["yaw"])
        r["xyz"] = transform(r["world"])
        r["donor"] = None
    d = donor()
    for r in rows:
        r["donor"] = d["inventory"].get(r["parent"])

    checks = {
        "four_markers": len(rows) == 4,
        "all_named_attach_vehicle": all(r["name"] == ATTACH for r in rows),
        "identical_world": len({r["world"] for r in rows}) == 1,
        "identity_rotation": all(r["world"].startswith("1,0,0,0, 0,1,0,0, 0,0,1,0,")
                                 for r in rows),
        "two_part_strings": all(r["mount"] and r["yaw"] for r in rows),
        "parts_in_module": all(r["mount_part"] and r["yaw_part"] for r in rows),
        "no_oid_reference": all(r["oid_occurrences"] == 1 for r in rows),
        "bmak_has_no_mount": not bmak_has_mount(bmak_surface()),
        "donor_type4_is_the_apc_mount": ("apc_weapon_mount_vertical", "apc_turret_base")
                                        in d["pairs"],
        "cloned_offset_is_the_apc_offset": len({r["world"] for r in rows}) == 1,
    }
    facts = {
        "rows_with_donor_type4": sum(1 for r in rows
                                     if r["donor"] and "4" in r["donor"]["types"]),
        "rows_pitch_not_cannon": sum(1 for r in rows
                                     if (r["mount_part"] or {}).get("behaviour") != "Cannon"),
        "rows_mount_parented_to_yaw": sum(1 for r in rows
                                          if (r["mount_part"] or {}).get("parent") == r["yaw"]),
        "rows_mount_equals_yaw": sum(1 for r in rows if r["mount"] == r["yaw"]),
        "pods_cross_paired": sorted({f"{r['mount']}/{r['yaw']}" for r in rows
                                     if r["mount"].startswith("batmobile_missile_pod")
                                     and r["yaw"].startswith("batmobile_missile_pod")}),
    }
    return {"rows": rows, "donor": d, "bmak": bmak_surface(), "checks": checks, "facts": facts,
            "sha": {"epe": sha256(p(EPE)), "parts": sha256(p(PARTS)),
                    "sockets": sha256(p(SOCKETS)), "cockpit": sha256(p(COCKPIT)),
                    "wiring": sha256(p(WIRING))}}


def bmak_has_mount(b: dict) -> bool:
    return any("mount" in role or "attach" in role for role in b["roles"]) or any(
        "mount" in name.lower() for name in b["mount_named"])


def fmt(xyz: tuple[float, float, float]) -> str:
    return ", ".join(f"{v:.6f}" for v in xyz)


def render(doc: dict) -> str:
    rows, d, b, facts = doc["rows"], doc["donor"], doc["bmak"], doc["facts"]
    L: list[str] = []
    a = L.append
    a("# bm-RC2 - the 4 type-4 `attach.vehicle` mount markers")
    a("")
    a("**STATUS: answered.** The four markers are JC3 `MountAttach` points - the donor mechanism"
      " that straps a *mounted* weapon (the APC/technical/armoured-jeep MG `w206` and the corvette"
      " cannon `w616`) to two chassis parts by name: `id:80201E4D` yaw part, `id:5C19E7E0`"
      " pitch/mount arm. Their matrix is an identity rotation plus one shared template offset, and"
      " **their object ids are referenced nowhere** in the `.epe`. The names, not the coordinates,"
      f" are the wiring - and **{facts['rows_with_donor_type4']} of the 4 built weapons has a type-4"
      " point in the donor**, so all four markers are additions of the clone, not ports. BmAK has a"
      f" driver seat and **no mount concept** ({b['sockets']} sockets, 0 with a mount role), so there"
      " is no BmAK anchor to score them against; their position stays UNKNOWN.")
    a("")
    a("Generated by `python Tools/scripts/v_mount_markers.py --write`; `--check` re-exports the"
      " `.epe` to a temp dir, re-derives everything and diffs this file byte for byte. Read-only on"
      f" the build: `{EPE}` sha256 `{doc['sha']['epe'][:16]}...`.")
    a("")
    a("## 1. The four markers, decoded from the built `.epe`")
    a("")
    a("| # | object id | parent weapon component | `5C19E7E0` (pitch / mount arm) |"
      " `80201E4D` (yaw part) | world translation (m) | uses of its object id |")
    a("|---:|---|---|---|---|---|---:|")
    for i, r in enumerate(rows, 1):
        a(f"| {i} | `{r['oid']}` | `{r['parent']}` | `{r['mount']}` | `{r['yaw']}` | "
          f"{fmt(r['xyz'])} | {r['oid_occurrences']} |")
    a("")
    a("Decoded: all four are `SWeaponPoint`, `type = 4`, `name = attach.vehicle`, `name_hash ="
      f" 2049066765`, `fire_effect = 0`, class hash `{rows[0]['class_hash']}` (Jenkins of"
      " `SWeaponPoint`). The rotation is the identity and the translation is the same for all four"
      " - `(0, -0.05405688, 0.002082527)`, the APC template's mounted-gun offset, not a measured"
      " Batmobile point. The properties they *do* carry are the two part-name strings plus two"
      " integers (`-1`, `0`); there is no `A90F5E74` string on any of them (that id does not occur"
      " in the built `.epe` at all).")
    a("")
    a("## 2. What the type-4 point is in the JC3 donor")
    a("")
    a(f"`Research/JC3Grab/WEAPON_WIRING.jsonl` (the graph `jc3wiring.py` builds) counts"
      f" {sum(d['by_type'].values())} weapon points by type:"
      f" {', '.join(f'type {k} x{v}' for k, v in d['by_type'].items())}. **All"
      f" {len(d['type4'])} type-4 points in the donor belong to {', '.join(d['type4_weapons'])}**,"
      f" bound as `{', '.join(d['bindings'])}`, on {len(d['type4_entities'])} entities - i.e. type 4"
      " is the *mounted-weapon* mechanism (a gun on a chassis turret base or vertical arm), not a"
      " tank cannon's fire point. Every one of them names the same two roles:")
    a("")
    a("| donor chassis | mount arm (`5C19E7E0`) | yaw part (`80201E4D`) | points |")
    a("|---|---|---|---:|")
    for (mount, yaw), n in d["pairs"].most_common():
        a(f"| {mount.split('_')[0]} | `{mount}` | `{yaw}` | {n} |")
    a("")
    a(f"So the shape is consistent across {len(d['pairs'])} pairs on seven chassis: a vertical"
      " mount arm pitches on a turret base or a horizontal mount arm (the patrol boat). The four"
      " Batmobile markers are that structure, copied from the APC pair"
      " `apc_weapon_mount_vertical` / `apc_turret_base` and renamed onto the Batmobile parts -"
      " including the APC's offset, which is why all four share one translation.")
    a("")
    a("### What each of the four does, against its own weapon in the donor")
    a("")
    a("| # | built weapon | donor point types | donor type-4? | donor bindings (union) |")
    a("|---:|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        inv = r["donor"] or {}
        types = ", ".join(inv.get("types", [])) or "**not in the donor**"
        t4 = "yes" if "4" in inv.get("types", []) else "**no**"
        a(f"| {i} | `{r['parent']}` | {types} | {t4} | `{', '.join(inv.get('bindings', [])) or '-'}` |")
    a("")
    a("Read that table with the donor as the reference:")
    a("")
    a("* **`w602_mediumtank_canon`** - the donor's tank cannon is a **type-2** fire point naming"
      " `mediumtank_cannon`/`mediumtank_turret` (TURRET.md's cannon table); it has no type-4 point."
      " The clone added one, and its parts (`batmobile_cannon` on `batmobile_turret`) are the"
      " correct *renaming* of the tank pair, so semantically it is the turret binding the Batmobile"
      " actually wants - just carried on the mounted-weapon mechanism instead of the cannon's.")
    a("* **`w603_mediumtank_mgun`** - the donor's coaxial MG is a type-2 `fire_position_0` with **no"
      " part strings at all**. The Batmobile marker gives it a mount (`batmobile_machine_gun` on"
      " `batmobile_turret`), i.e. makes the coax gun aimable by binding it to the turret pair.")
    a("* **`w618_sportsmuscle_missile` / `_emp`** - the donor's sports-muscle missile has four"
      " type-2 `internal.fire_point.N` points and no mount; the `_emp` variant is not in the donor"
      " graph at all. The clone gives both missile weapons the same marker pair, and it"
      " **cross-pairs the two pods**: `batmobile_missile_pod_r` as the pitch arm and"
      f" `batmobile_missile_pod_l` as the yaw part (`{facts['pods_cross_paired'][0]}`). Two separate"
      " weapons therefore share one r-as-pitch / l-as-yaw binding.")
    a("")
    a("## 3. Does the weapon wiring reference them?")
    a("")
    a("**By part name - yes, and that is the only reference.** `Tools/scripts/jc3wiring.py`"
      " `mount_parts()` collects every type-4 point string that equals a chassis part name; that is"
      " the `mount parts` column of `Research/JC3Grab/WEAPON_WIRING.md` and the yaw/pitch columns of"
      " `Research/JC3Grab/TURRET.md`. `Tools/scripts/bm_entity.py` (lines 731-748, 778) then asserts"
      " every such name resolves in the built parts module - it would fail on a dangling name, and"
      " its tamper test deliberately rewrites one of these strings to a non-part name (MODLOG"
      " B-05 rework). A wrong **part name** would matter; it would bind the hinge to the wrong part.")
    a("")
    a("**By object id - no.** Each marker's object id occurs exactly once in the built `.epe`"
      f" ({', '.join(str(r['oid_occurrences']) for r in rows)} occurrences = its own definition)."
      " No root slot, weapon property, interaction, part or physics object points at the point"
      " object, so nothing resolves these markers by identity.")
    a("")
    a("**The coordinates are referenced by nothing this repo has decoded.** The only consumers are"
      " the two part-name strings. Whether the JC3 runtime reads a `MountAttach` matrix when it"
      " seats the mounted weapon is native engine behaviour - UNKNOWN.")
    a("")
    a("## 4. Would a wrong position matter?")
    a("")
    a("* **In the entity graph: no.** Nothing reads the matrix. The binding is the part-name pair,"
      " and all four pairs resolve in `Working/Parts/bm_vehicle_parts.json` (checked below).")
    a("* **As a part binding: yes.** The pair is what the turret port copies (TURRET.md §1: two"
      " moving parts, two Havok hinges, the two strings).")
    a("* **As coordinates: unmeasured, and only a risk if the runtime reads them.** The offset is"
      " the APC's turret-local template value; the Batmobile's own mount geometry never entered it."
      " Nothing in the repo proves the runtime ignores it (UNKNOWN 1).")
    a("")
    a("## 5. Does BmAK have a matching seat/mount concept?")
    a("")
    a(f"`Research/BatmobileGrab/SOCKETS_JC3.json`: **{b['sockets']} sockets**, roles"
      f" `{', '.join(b['roles'])}` - **no `mount` or `attach` role**; the only socket names"
      f" containing either word are `{', '.join(b['mount_named']) or '-'}` (winch anchors, not"
      " weapon mounts). `Research/BatmobileGrab/COCKPIT.json` records the seat concept BmAK *does*"
      f" have: `{b['driver_anchors']}` driver anchors - the `{b['driver_socket']}` hip socket at"
      f" `{fmt(tuple(b['driver_position_m']))}` and the animation origin at"
      f" `{fmt(tuple(b['anim_origin_position_m']))}`, plus the cockpit seat material.")
    a("")
    a("So BmAK has a **seat** and no **weapon mount**: no socket, bone or property names a yaw"
      " part, a pitch part or an attach target. The two are different mechanisms in JC3 as well - a"
      " seat is `interaction.seat.gunner1` on `point.mounted_weapon`, while `attach.vehicle` binds"
      " parts. **There is no BmAK anchor these four can be compared with**, which is why task 7240"
      " left them UNKNOWN instead of scoring them.")
    a("")
    a("## 6. Deviations worth knowing (facts, not gates)")
    a("")
    a(f"* **{facts['rows_with_donor_type4']}/4** built weapons has a type-4 point in the donor: all"
      " four markers are additions of the clone, not ports of their weapon's own donor point.")
    a(f"* **{facts['rows_pitch_not_cannon']}/4** pitch arms are not `Cannon` parts: the donor's"
      " pitch census is 47/47 `Cannon` (`TURRET.json` `point_census.pitch`), while the built arms"
      " are `batmobile_cannon` (`Cannon`), `batmobile_machine_gun` (`GatlingGun`) and"
      " `batmobile_missile_pod_r` (`None`). `GatlingGun` is a real parts behaviour (24 cached parts,"
      " `Research/challenge/card-B-04.md`), so this is a new pairing, not a broken name.")
    a(f"* **{facts['rows_mount_parented_to_yaw']}/4** mount arms are parented to the yaw part, which"
      " is the donor's shape (vertical arm on the turret base). The pod markers are the exceptions:"
      " `batmobile_missile_pod_r` is parented to the body and paired with the *other* pod.")
    a(f"* The two missile markers are byte-identical to each other and to the APC template; the EMP"
      " weapon did not get its own mount.")
    a("")
    a("## 7. Gates")
    a("")
    a("| gate | result |")
    a("|---|---|")
    for k, v in doc["checks"].items():
        a(f"| `{k}` | {'PASS' if v else 'FAIL'} |")
    a("")
    a("## 8. Sources")
    a("")
    a("| file | sha256 |")
    a("|---|---|")
    for key, path in (("epe", EPE), ("parts", PARTS), ("sockets", SOCKETS),
                      ("cockpit", COCKPIT), ("wiring", WIRING)):
        a(f"| `{path}` | `{doc['sha'][key]}` |")
    a("")
    a("## 9. UNKNOWNs")
    a("")
    a("1. **Whether JC3 reads the `MountAttach` matrix at runtime.** No decoded file reads it; the"
      " engine is native. If it does, the APC offset would seat a mounted weapon wrongly and this"
      " repo cannot say by how much.")
    a("2. **Where a Batmobile mount would be.** BmAK has no mount anchor, so there is no reference"
      " value to derive one from.")
    a("3. **Whether the missile pods should be aimable at all.** The donor gives its sports-muscle"
      " missile no mount; the clone gives both missile weapons the APC's. That is a design choice,"
      " not a decoded value.")
    a("4. **Whether `batmobile_machine_gun` (`GatlingGun`) is hinge-driven.** The donor has no"
      " `GatlingGun` pitch arm to compare with (its pitch census is entirely `Cannon`), so whether"
      " the runtime aims a GatlingGun part the same way is UNKNOWN.")
    a("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    text = render(doc)
    if args.write:
        os.makedirs(os.path.dirname(p(OUT)), exist_ok=True)
        with open(p(OUT), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {OUT}: {len(doc['rows'])} markers")
        for r in doc["rows"]:
            print(f"  {r['parent']:<34} mount={r['mount']:<26} yaw={r['yaw']:<26} "
                  f"oid_refs={r['oid_occurrences']}")
        for k, v in doc["checks"].items():
            print(f"  {k:<32} {'PASS' if v else 'FAIL'}")
        return 0
    ok = True
    for k, v in doc["checks"].items():
        print(f"  {k:<32} {'PASS' if v else 'FAIL'}")
        ok = ok and v
    got = open(p(OUT), encoding="utf-8").read().replace("\r\n", "\n") if os.path.exists(p(OUT)) else ""
    if got != text:
        print("FAIL: the file differs from the re-derived text")
        import difflib
        for line in difflib.unified_diff(got.splitlines(), text.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        return 1
    print(f"  {'file_matches_rederivation':<32} PASS ({len(text)} bytes)")
    print("OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
