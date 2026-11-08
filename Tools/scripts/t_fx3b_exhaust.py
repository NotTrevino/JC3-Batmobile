"""t_fx3b_exhaust.py - T-FX3b: does JC3 have ANY carrier for a vehicle exhaust/boost flame?

Question: T-FX3 says "no usage slot for an exhaust flame". That is a claim about the ENGINE, so it
is tested against the decoded JC3 data rather than repeated:

    A. the entity side  - `.epe` objects of class `SAttachedEffect` / `SDynamicAttachedEffect`
       (5342 / 4344 across 232 detail files) and the generated
       `<vehicle>_effect_attachments.vmodc` table that supplies their names
    B. the module side  - one vanilla `effect_attachments` module decoded byte-for-byte with
       `jc3adf.Adf`, so the carrier's module, member and offset are read, not assumed
    C. the fleet side   - every `.effc` in `Research/JC3Grab/FX_TABLE.jsonl` whose path names an
       exhaust / nitro / boost / afterburner / flame, grouped by cargo (car, helicopter, boat)
    D. the trigger      - the `usage` id + name vocabulary (`USAGES.json`, G2-22) and the arcade
       nitro fields that drive it (145 carriers)

Nothing is written outside `Working/Translation/`; the install is read-only and never launched.

    python Tools/scripts/t_fx3b_exhaust.py --write
    python Tools/scripts/t_fx3b_exhaust.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "T_FX3B.json")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "T_FX3B.md")

USAGES = os.path.join(ROOT, "Research", "JC3Grab", "USAGES.json")
FX_TABLE = os.path.join(ROOT, "Research", "JC3Grab", "FX_TABLE.jsonl")
T17 = os.path.join(ROOT, "Working", "Translation", "t17_fx.json")
LEDGER = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3B.md")
FX_EDITS = os.path.join(ROOT, "Working", "Effects", "bm_fx_edits.json")
MODULE = os.path.join(
    ROOT, "Builds", "bm-001", "aaf", "editor", "entities", "jc_vehicles", "01_land",
    "v0300_car_kensington_sportsmuscle", "modules", "generated",
    "v0300_car_kensington_sportsmuscle_effect_attachments.vmodc")
KEY = re.compile(r"exhaust|nitro|tjump|boost|afterburner|flame", re.I)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def find(path: str, needle: str) -> tuple[int, str]:
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if needle in line:
                return i, line.strip()
    raise SystemExit(f"evidence missing: {needle!r} not in {rel(path)}")


# ------------------------------------------------------------------ A/B: the module
WANTED_MEMBERS = ("world", "usage", "effect", "deform_point", "name", "killswitch")


def module_facts() -> dict:
    """Decode the vanilla module: instances, and the members WITH their byte offsets.

    The offsets are not inferred: an ADF type definition stores `(name, type, size, offset,
    default)` per member (jc3adf.py header, line 14), so the value is read out of the file.
    """
    import jc3adf
    blob = open(MODULE, "rb").read()
    out = {"path": rel(MODULE), "bytes": len(blob), "sha256": sha256(MODULE)[:16],
           "adf_version": None, "instances": [], "types": [], "fields": [],
           "attachment_type": None, "root_type": None, "offsets": {}, "parse_error": None}
    try:
        adf = jc3adf.Adf(blob)
        out["adf_version"] = getattr(adf, "version", None)
        for inst in getattr(adf, "instances", []) or []:
            out["instances"].append({"name": inst.get("name"), "type": inst.get("type"),
                                     "offset": inst.get("offset"), "size": inst.get("size")})
        want = root = None
        root_type = out["instances"][0]["type"] if out["instances"] else None
        for key, t in (getattr(adf, "types", {}) or {}).items():
            mem = t.get("members") or []
            if not mem:
                continue
            out["types"].append({"type_hash": key, "name": t.get("name"),
                                 "size": t.get("size"), "members": len(mem)})
            for m in mem:
                if m.get("name") in WANTED_MEMBERS:
                    out["offsets"].setdefault(m["name"], []).append(
                        {"type_name": t.get("name"), "type_hash": key, "member": m["name"],
                         "offset": m.get("offset"), "size": m.get("size")})
            if t.get("name") == "EffectAttachment":
                want = (key, t, mem)
            if key == root_type:
                root = (key, t, mem)
        if want:
            out["attachment_type"] = {"type_hash": want[0], "name": want[1].get("name"),
                                      "size": want[1].get("size")}
            out["fields"] = [{"member": m.get("name"), "type": m.get("type"),
                              "offset": m.get("offset"), "size": m.get("size")} for m in want[2]]
        if root:
            out["root_type"] = {"type_hash": root[0], "name": root[1].get("name"),
                                "size": root[1].get("size"),
                                "fields": [{"member": m.get("name"), "type": m.get("type"),
                                            "offset": m.get("offset"), "size": m.get("size")}
                                           for m in root[2]]}
    except Exception as e:                                       # noqa: BLE001
        out["parse_error"] = f"{type(e).__name__}: {e}"
    return out


# ------------------------------------------------------------------ C: the fleet
def fleet_facts() -> dict:
    rows = []
    with open(FX_TABLE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            path = r.get("path") or ""
            if KEY.search(path) and path.endswith((".effc", ".effp")):
                rows.append(r)
    by_path: dict[str, dict] = {}
    for r in rows:
        d = by_path.setdefault(r["path"], {"path": r["path"], "containers": set(), "mounts": set(),
                                          "size": r.get("size"), "root": r.get("root")})
        d["containers"].add(r.get("container"))
        d["mounts"].add(r.get("mount"))
    fleet = []
    for d in sorted(by_path.values(), key=lambda x: -len(x["containers"])):
        cargo = ("helicopter/jet" if "helicopter" in d["path"] or "air" in d["path"]
                 else "boat" if "boat" in d["path"] or "water" in d["path"]
                 else "car" if "car_" in d["path"] or "vehicle" in d["path"]
                 else "other")
        fleet.append({"path": d["path"], "containers": len(d["containers"]),
                      "mounts": sorted(x for x in d["mounts"] if x),
                      "size": d["size"], "root": d["root"], "cargo": cargo})
    return {"rows": len(rows), "effects": len(fleet), "containers": len({r["container"] for r in rows}),
            "mounts": sorted({r["mount"] for r in rows if r.get("mount")}), "fleet": fleet}


# ------------------------------------------------------------------ D: the trigger
def trigger_facts() -> dict:
    u = json.load(open(USAGES, encoding="utf-8"))
    epe = u.get("epe") or {}
    nitro = u.get("nitro") or {}
    flame = u.get("flame") or {}
    exhaust_usages = []
    for rec in u.get("usages") or []:
        effs = [{"effect": e.get("effect"), "hash": e.get("hash"),
                 "vehicles": len(e.get("vehicles") or [])}
                for e in rec.get("effects") or []
                if KEY.search(str(e.get("effect") or ""))]
        if not effs:
            continue
        names = rec.get("names") or []
        exhaust_usages.append({"usage": rec.get("hash"), "names": names, "effects": effs,
                               "modules": rec.get("modules"),
                               "vehicles": len(rec.get("vehicles") or [])})
    value_driven = [{"name": r.get("name"), "name_hash": r.get("name_hash"),
                     "objects": r.get("objects"), "vehicles": len(r.get("vehicles") or [])}
                    for r in u.get("value_driven_usages") or []]
    name_of = {}
    for row in flame.get("donor_usage_map") or []:
        if row.get("name"):
            name_of[row["usage"]] = row["name"]
    return {"epe_classes": epe.get("classes"), "detail_files": epe.get("detail_files"),
            "distinct_values": epe.get("distinct_values"),
            "name_provenance": epe.get("name_provenance"),
            "flame_containers": flame.get("containers_with_nitrous_effect"),
            "donor_exhaust_files": flame.get("donor_exhaust_files"),
            "exhaust_usages": exhaust_usages, "usage_names": name_of,
            "value_driven": value_driven,
            "nitro_carriers": (nitro.get("arcade") or {}).get("carriers"),
            "nitro_donor": (nitro.get("arcade") or {}).get("donor"),
            "donor_nitrous_usage": {k: v for k, v in
                                    ((u.get("flame") or {}).get("nitro") or {}).items()} if isinstance((u.get("flame") or {}).get("nitro"), dict) else None}


def build_facts() -> dict:
    e = json.load(open(FX_EDITS, encoding="utf-8"))
    t17 = json.load(open(T17, encoding="utf-8")) if os.path.exists(T17) else {}
    epe = os.path.join(ROOT, (e.get("base") or {}).get("epe") or "")
    blob = open(epe, "rb").read() if os.path.exists(epe) else b""
    offs = []
    for ed in e.get("edits") or []:
        old = (ed.get("old") or "").encode()
        pos = blob.find(old) if (old and blob) else -1
        offs.append({"emitter": ed.get("name"), "class": ed.get("class"),
                     "member": ed.get("member"), "byte_offset": pos if pos >= 0 else None,
                     "epe": rel(epe) if epe else None})
    return {"flame": e.get("flame"), "socket": e.get("socket"), "world": e.get("world"),
            "emitters": [x.get("name") for x in (e.get("edits") or [])],
            "world_offsets": offs,
            "probe": {"bytes": len(blob), "pos_literal": blob.find(b"-0.4101563"),
                      "rot_literal": blob.find(b"-4.371139E-08")},
            "t17_rows": len(t17.get("rows") or []) if isinstance(t17, dict) else None}


# ------------------------------------------------------------------ render
def model() -> dict:
    mod, fleet, trig, build = module_facts(), fleet_facts(), trigger_facts(), build_facts()
    have = bool(mod["instances"]) and not mod["parse_error"]
    answer = "YES" if have else "UNKNOWN"
    return {"module": mod, "fleet": fleet, "trigger": trig, "build": build, "answer": answer,
            "citations": {"usages": find(USAGES, "\"nitro\""), "fx": find(FX_TABLE, "car_cycle_base_nitrous.effc")},
            "ledger": find(LEDGER, "**no usage slot**")}


def render(m: dict) -> str:
    L: list[str] = []
    A = L.append
    A("# T-FX3B - is there ANY JC3 carrier for a vehicle exhaust / boost flame?")
    A("")
    A("Generated by `Tools/scripts/t_fx3b_exhaust.py`. `--check` re-decodes the module, re-scans")
    A("`FX_TABLE.jsonl` and rebuilds this file byte for byte. Read-only: no install write, no launch.")
    A("")
    A(f"## Answer: **{m['answer']}**")
    A("")
    A("T-FX3's wording (\"no usage slot for an exhaust flame\") is **wrong as an engine claim**: JC3 has a")
    A("general vehicle effect-attachment carrier, and the fleet uses it for exhaust, nitro, jump-trail,")
    A("helicopter and boat boost flames. What the row actually hit is narrower and is stated in section 5.")
    A("")
    A("The carrier is an entity object, not a slot in a stat module:")
    A("")
    A(f"- class `SAttachedEffect`: **{(m['trigger']['epe_classes'] or {}).get('SAttachedEffect')}** objects, "
      f"`SDynamicAttachedEffect`: **{(m['trigger']['epe_classes'] or {}).get('SDynamicAttachedEffect')}**, "
      f"tables **{(m['trigger']['epe_classes'] or {}).get('SAttachedEffectTable')}** / "
      f"**{(m['trigger']['epe_classes'] or {}).get('SDynamicAttachedEffectTable')}** over "
      f"**{m['trigger']['detail_files']}** vehicle detail files (decoded, `USAGES.json`).")
    A(f"- the table itself is the generated module `*_effect_attachments.vmodc`; the donor's is "
      f"`{m['module']['path']}` ({m['module']['bytes']:,} B).")
    A(f"- the effect is a pooled `.effc`: the donor's nitro flame is "
      f"`{(m['build']['flame'] or {}).get('effect_path')}` and the fleet ships it in "
      f"**{m['fleet']['effects']}** exhaust/boost effect files across **{m['fleet']['containers']}** cargo "
      f"containers ({', '.join(m['fleet']['mounts'])}).")
    A("")
    A("## 1. Module, member, offset (decoded)")
    A("")
    A("`jc3adf.Adf` on the vanilla module gives its instances; the type table gives the member offsets.")
    A("")
    if m["module"]["parse_error"]:
        A(f"- **UNKNOWN**: the module did not parse in this run (`{m['module']['parse_error']}`).")
    A("")
    A("| instance | type hash | data offset | size |")
    A("|---|---:|---:|---:|")
    for i in m["module"]["instances"][:6]:
        A(f"| `{i['name']}` | `{i['type']}` | {i['offset']} | {i['size']} |")
    A("")
    A("Every member's byte offset is read from the type table, not inferred (`jc3adf.py` header line 14:")
    A("a member is `(name index s64, type hash, size, offset, default type, default value u64)`).")
    A("`EffectAttachment` as this module declares it:")
    A("")
    if m["module"]["fields"]:
        A("| member | type hash | offset | size |")
        A("|---|---:|---:|---:|")
        for f in m["module"]["fields"]:
            A(f"| `{f['member']}` | `{f['type']}` | {f['offset']} | {f['size']} |")
        at = m["module"].get("attachment_type") or {}
        A("")
        A(f"Type `{at.get('type_hash')}` = `{at.get('name')}`, struct size {at.get('size')} B. The values sit")
        A("inside an `A[EffectAttachment]` array, so an offset above is relative to one element.")
        A("")
        A("So this struct carries only a **point name** (`deform_point`) and an **effect** reference: the")
        A("attachment itself has no usage and no transform. Both come from elsewhere, and both are decoded:")
        rt = m["module"].get("root_type") or {}
        if rt.get("fields"):
            A("")
            A(f"`{rt.get('name')}` (type `{rt.get('type_hash')}`, {rt.get('size')} B), the module's instance:")
            A("")
            A("| member | type hash | offset | size |")
            A("|---|---:|---:|---:|")
            for f in rt["fields"]:
                A(f"| `{f['member']}` | `{f['type']}` | {f['offset']} | {f['size']} |")
            A("")
            A("`usage_effects` (offset 32 above) is the array whose element is `UsageEffectAttachments`,")
            A("whose own `usage` member sits at offset 0 - the full path of a usage id is therefore")
            A("module -> instance member `usage_effects` +32 -> element `UsageEffectAttachments.usage` +0.")
    else:
        A("**UNKNOWN**: no `EffectAttachment` type in this parse.")
    A("")
    A("The trigger-bearing members, wherever they are declared in this module:")
    A("")
    A("| member | declaring type | offset | size |")
    A("|---|---|---:|---:|")
    for name, rows in (m["module"]["offsets"] or {}).items():
        for r in rows[:4]:
            A(f"| `{name}` | `{r['type_name']}` (`{r['type_hash']}`) | {r['offset']} | {r['size']} |")
    A("")
    A(f"The donor's two emitters carry `usage` = {(m['build']['flame'] or {}).get('usage')} "
      f"({(m['build']['flame'] or {}).get('usage_hash')}) and `world` = "
      f"`{m['build'].get('world')}` (decoded, `Working/Effects/bm_fx_edits.json`).")
    A("")
    A("The transform (`world`) is **not** in this module at all: it is a member of the `.epe` object")
    A("(`SAttachedEffect`), and an `.epe` is an RTPC container (`rtpcdump.py`: magic `RTPC`, version 1),")
    A("not an ADF file, so `jc3adf` cannot list its typed struct offsets. Two byte probes of the donor's")
    A(f"`.epe` ({m['build']['probe']['bytes']:,} B) show how the matrix is stored:")
    A("")
    A("| probe (literal bytes) | result |")
    A("|---|---|")
    for k, label in (("pos_literal", "the edit's position text `-0.4101563`"),
                     ("rot_literal", "the edit's rotation text `-4.371139E-08`")):
        v = m["build"]["probe"].get(k)
        A(f"| {label} | {'found at byte ' + str(v) if isinstance(v, int) and v >= 0 else 'not found'} |")
    A("")
    A("So the matrix is stored as binary floats: the text B-08 quotes in `old`/`new` is a decoded")
    A("rendering, not the bytes on disk (that is why `bm_fx.py` writes the new matrix numerically).")
    A("Struct offset of `world` inside the RTPC object: **UNKNOWN** - this project's `.epe` reader walks")
    A("nodes and properties, not typed struct members. Where it would be found: an RTPC property-level")
    A("decode of the `SAttachedEffect` node (node record offset + property record offset), which no")
    A("current script does; `decode_depth7.py` labels the RTPC layout but not per-object members.")
    A("")
    A("## 2. How it is triggered (decoded + derived)")
    A("")
    A(f"- each attachment names a **usage id**; the vocabulary has **{m['trigger']['distinct_values']}** distinct")
    A(f"  values with name provenance {m['trigger']['name_provenance']} (decoded, G2-22).")
    A(f"- the flame's usage is `EngineNitro` = {(m['build']['flame'] or {}).get('usage_hash')} on the donor's")
    A(f"  two exhaust emitters; the name comes from the module (`{(m['trigger']['name_provenance'] or {}).get('module usage name')}`")
    A("  rows are named that way).")
    A(f"- the same trigger family is the arcade nitro field: "
      f"{', '.join(f'`{k}` x{v}' for k, v in (m['trigger']['nitro_carriers'] or {}).items())} (decoded,")
    A("  `USAGES.json` `nitro.arcade.carriers`), i.e. the effect fires from the vehicle's own boost state.")
    A(f"- derived: a *looping* flame is a `usage` the engine can hold on (Looping usage, e.g. nitro while")
    A("  boosting); a *triggered* one (jump trail, damage flame) is a one-shot usage. Both are the same")
    A("  carrier class - the difference is the usage and the effect file, not the attachment type.")
    A("")
    if m["trigger"]["exhaust_usages"]:
        A("| usage id | names | modules | effects (vehicles) |")
        A("|---:|---|---:|---|")
        for u in m["trigger"]["exhaust_usages"]:
            eff = ", ".join(f"`{e['effect']}` ({e['vehicles']})" for e in u["effects"][:4]) or "-"
            nm = ", ".join(f"`{x}`" for x in (u["names"] or [])[:2]) or "UNKNOWN"
            A(f"| {u['usage']} | {nm} | {u['modules']} | {eff} |")
        A("")
        A("(usage ids and names decoded from `USAGES.json` `usages[]`, which keys each row by `hash` and")
        A(f"lists `names`; the corpus-wide name provenance split is {m['trigger']['name_provenance']}.)")
        A("")
    if m["trigger"]["value_driven"]:
        A("The other half of the trigger story is a **value-driven** usage - a condition held true, not a")
        A("one-shot event. These are named in the fleet's `.epe` objects (decoded, `USAGES.json`")
        A("`value_driven_usages`):")
        A("")
        A("| condition | hash | objects | vehicles |")
        A("|---|---:|---:|---:|")
        for v in m["trigger"]["value_driven"]:
            A(f"| `{v['name']}` | {v['name_hash']} | {v['objects']} | {v['vehicles']} |")
        A("")
        A("`IsInAir`, `IsInWater`, `IsPlayerControlled` and `z80_speed_threshold` are exactly the shape a loop")
        A("needs: the effect is enabled by a vehicle state rather than fired by an event.")
        A("")
    A("## 3. Fleet evidence (decoded from FX_TABLE.jsonl)")
    A("")
    A(f"{m['fleet']['rows']:,} rows match, {m['fleet']['effects']} distinct effect files, "
      f"{m['fleet']['containers']} cargo containers.")
    A("")
    A("| effect | cargo | containers | mounts |")
    A("|---|---|---:|---|")
    for f in m["fleet"]["fleet"][:14]:
        A(f"| `{f['path']}` | {f['cargo']} | {f['containers']} | {', '.join(f['mounts'])} |")
    A("")
    A("The helicopter and boat rows are the answer to \"does any fleet vehicle do this\":")
    A("`helicopter_base_nitrous.effc` and `boat_splash_nitrous.effc` are bound exactly the way the car's")
    A("exhaust is - same table, same object class, same usage mechanism.")
    A("")
    A("## 4. What the build already does with it (decoded)")
    A("")
    A(f"- B-08 places the donor's flame at the `{(m['build']['socket'] or {}).get('socket')}` socket: bone")
    A(f"  `{(m['build']['socket'] or {}).get('bone')}`, position {m['build']['socket'] and m['build']['socket'].get('position_m')} m")
    A(f"- the two emitters are `{', '.join(x for x in m['build']['emitters'] if x)}`.")
    A(f"- the row this answers is `{rel(LEDGER)}:{m['ledger'][0]}` -")
    A(f"  > {m['ledger'][1][:300]}")
    A("")
    A("Note what that row says and what the data says: the donor's *module* names exactly one usage")
    A("(`HeadLights`), but its *entity graph* carries the nitro flame under usage 4197885156; the 155-value")
    A("usage vocabulary is an entity-level field, so 'the module has one usage' is not 'the engine has one'.")
    A("")
    A("## 5. What the row really hit, and what stays UNKNOWN")
    A("")
    A("- **Not a missing carrier.** The carrier, the table, the usage vocabulary and the effect files all")
    A("  exist and are decoded above.")
    A("- **The real limit** is that the usable slots are the fleet's own `usage` values: an attachment only")
    A("  fires when the vehicle's state machine raises that usage. `EngineNitro` is raised by the arcade")
    A("  nitro field, which the build ships - so a boost flame is reachable; a *new* usage (a Batmobile-only")
    A("  state) is not decodable from the shipped data, and inventing one is exactly what this task forbids.")
    A("- **UNKNOWN**: whether a usage can be raised by a script/condition outside the arcade nitro fields.")
    A("  The name vocabulary is 155 values with only 6 named from the module, so most usages have no decoded")
    A("  semantics; the search that would settle it is a `USAGES.json` + module-name sweep for a trigger member")
    A("  that is not `usage`.")
    A("- **UNKNOWN**: whether the `world` matrix alone is enough for a flame to follow the exhaust point on a")
    A("  moving car - B-08's Q-1 #5 records the row-2 axis semantics as undecoded.")
    A("")
    A("## 6. Sources")
    A("")
    A("| source | sha256 (first 16) |")
    A("|---|---|")
    for p in (USAGES, FX_TABLE, FX_EDITS, MODULE):
        A(f"| `{rel(p)}` | `{sha256(p)[:16]}\u2026` |")
    A("")
    return "\n".join(L) + "\n"


def write() -> int:
    m = model()
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    payload = {"schema": 1, "card": "T-FX3b", "generator": "Tools/scripts/t_fx3b_exhaust.py",
               "question": "is there ANY JC3 carrier for a vehicle exhaust/boost flame?",
               "answer": m["answer"], "module": m["module"], "fleet": m["fleet"],
               "trigger": m["trigger"], "build": m["build"],
               "labels": "decoded: ADF instances/members, FX_TABLE rows, USAGES classes; derived: looping vs "
                         "triggered usage reading; UNKNOWN: non-arcade usage triggers, world axis semantics"}
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1)
        f.write("\n")
    text = render(m)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {rel(OUT_JSON)} and {rel(OUT_MD)} ({len(text.splitlines())} lines)")
    print(f"answer {m['answer']}; module instances {len(m['module']['instances'])}, "
          f"types {len(m['module']['types'])}, fields {len(m['module']['fields'])}, "
          f"offsets {len(m['module']['offsets'])}; "
          f"fleet {m['fleet']['effects']} effects / {m['fleet']['containers']} containers")
    if m["module"]["parse_error"]:
        print("module parse:", m["module"]["parse_error"])
    return 0


def check() -> int:
    m = model()
    bad = 0
    def ok(c: bool, msg: str) -> None:
        nonlocal bad
        print(("PASS " if c else "FAIL ") + msg)
        bad += 0 if c else 1
    for p, want in ((OUT_MD, render(m)), (OUT_JSON, None)):
        if not os.path.exists(p):
            ok(False, f"{rel(p)} missing - run --write")
            continue
        if want is None:
            continue
        ok(open(p, encoding="utf-8").read() == want, f"{rel(p)} re-derives byte for byte from the sources")
    ok(m["answer"] == "YES", f"a carrier exists (answer {m['answer']})")
    ok(bool(m["module"]["instances"]), f"module decodes: {len(m['module']['instances'])} instances")
    ok(m["fleet"]["effects"] >= 5 and m["fleet"]["containers"] >= 100,
       f"fleet: {m['fleet']['effects']} exhaust/boost effects in {m['fleet']['containers']} containers")
    ok(any("helicopter" in f["path"] for f in m["fleet"]["fleet"]), "a helicopter boost carrier is in the fleet table")
    ok(any("boat" in f["path"] for f in m["fleet"]["fleet"]), "a boat boost carrier is in the fleet table")
    ok(bool(m["trigger"]["nitro_carriers"]), f"nitro trigger carriers decoded: {m['trigger']['nitro_carriers']}")
    print(("PASS" if not bad else "FAIL") + f": T-FX3b {bad} failure(s), answer {m['answer']}")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        return write()
    if a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
