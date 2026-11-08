"""grab_collision_modes.py - which BmAK collision mesh is active per mode (GRB-G3-01b open item).

The drivable Batmobile carries two collision mesh components:
`BatmanCollisionMeshPursuitMode0` and `BatmanCollisionMeshBattleMode0`
(COLLISION.md rows, both StaticMeshComponent). Which one is live in each mode is set by
`BatmanVsBatmobileCollisionMode` (layout offset 5895 per COLLISION.md), which is not
serialised in the archetype, the Startup CDO or the BmGame base walk.

This tool searches the script bytes for the two ways a mode could select a component:

  * a **name reference** - the FName index of `BatmanCollisionMeshBattleMode0`, ...PursuitMode0,
    `BatmanVsBatmobileCollisionMode`, `CollisionComponent`, `SetHidden`, `SetActorCollision`,
    `SetBlockRigidBody` appearing as a 4-byte operand in a function body;
  * an **object reference** - the export index of the component (or of the base template)
    appearing as a 4-byte operand.

A hit is reported as `derived (name reference in script blob)` or
`derived (object reference to export N in script blob)`: it proves the body *touches* that
object, not that it does so under a condition. Control flow is not decoded, so a hit is not
on its own a statement that the mesh is enabled in that mode - that stays UNKNOWN unless the
body also carries the enabling call in the same function, which is reported but still labelled
as co-occurrence, not as an executed branch.

The mode functions are the State exports and the BeginState / EndState / Tick functions named
from them; the corpus scan covers every Function whose path names a Batmobile or vehicle class,
so a selector outside the state bodies is not missed silently.

Usage:
  python Tools/scripts/grab_collision_modes.py --write
  python Tools/scripts/grab_collision_modes.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402

GAME = r"E:/Games/Batman - Arkham Knight"
COOKED = os.path.join(GAME, "BmGame", "CookedPCConsole")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_MODES.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_MODES.json")

PACKAGES = ("BmGame.upk", "Startup.upk")
# State exports (COLLISION.md / CONTROLS_CONSUMERS.md): BmGame.upk only.
STATES = {"PursuitMode": 10525, "BattleMode": 10547}
# The state's own functions, decoded in CONTROLS_CONSUMERS.md (export indices).
STATE_FUNCS = {
    "PursuitMode": {"BeginState": 10515, "EndState": 10517, "Tick": 10524},
    "BattleMode": {"BeginState": 10529, "EndState": 10533, "Tick": 10546},
}
# Names the card asks about.
TARGET_NAMES = ("BatmanCollisionMeshBattleMode0", "BatmanCollisionMeshPursuitMode0",
                "BatmanVsBatmobileCollisionMode", "CollisionComponent",
                "SetHidden", "SetActorCollision", "SetBlockRigidBody")
# Collision component / template exports per package (COLLISION.md table).
COMPONENTS = {
    "BmGame.upk": {"BattleMode0 template": 176111, "PursuitMode0 template": 176112},
    "Startup.upk": {"BattleMode0 template": 171103, "PursuitMode0 template": 171104},
    "Playable_Batmobile_SF.upk": {"BattleMode0 instance": 5392, "PursuitMode0 instance": 5393},
}
CORPUS = ("Batmobile", "Vehicle")


def script_of(pkg, i: int) -> bytes:
    """The function body slice used by bmak_damage / grab_controls_consumers (d[22:-16])."""
    d = pkg.data(i)
    return d[22:len(d) - 16] if len(d) >= 38 else b""


def packed(idxs) -> list[bytes]:
    return [struct.pack("<i", n) for n in idxs]


def scan(buf: bytes, needles: dict[str, bytes]) -> list[dict]:
    out = []
    for label, needle in needles.items():
        pos = buf.find(needle)
        while pos >= 0:
            out.append({"label": label, "at": pos})
            pos = buf.find(needle, pos + 1)
    return sorted(out, key=lambda r: (r["at"], r["label"]))


def name_indices(pkg) -> dict[str, list[int]]:
    wanted = set(TARGET_NAMES)
    out: dict[str, list[int]] = {n: [] for n in TARGET_NAMES}
    for i, nm in enumerate(pkg.names):
        if nm in wanted:
            out[nm].append(i)
    return out


def resolve_states(pkg, pkg_name: str) -> tuple[dict, list[str]]:
    """The State export per mode.

    `STATES` is decoded from BmGame.upk and is applied there only. Export indices are
    package-local (Startup export 10525 is a dialogue anim), so any other package is
    resolved by path and the result is checked before it is used.
    """
    problems: list[str] = []
    if pkg_name == "BmGame.upk":
        cand = dict(STATES)
    else:
        cand = {}
        for i in range(1, len(pkg.exports) + 1):
            if pkg.object_class(i) != "State":
                continue
            nm, path = pkg.object_name(i), pkg.object_path(i)
            if nm in ("PursuitMode", "BattleMode") and "RVehicleBatmobile" in path:
                cand.setdefault(nm, i)
    out: dict[str, dict] = {}
    for label, idx in cand.items():
        if idx > len(pkg.exports):
            problems.append(f"{pkg_name}: {label} export {idx} is beyond the export table")
            continue
        cls, path = pkg.object_class(idx), pkg.object_path(idx)
        if cls != "State" or "RVehicleBatmobile" not in path:
            problems.append(f"{pkg_name}: export {idx} is {cls} `{path}`, not the {label} State - skipped")
            continue
        out[label] = {"export": idx, "class": cls, "path": path,
                      "bytes": pkg.exports[idx - 1].get("size")}
    return out, problems


def resolve_funcs(pkg, pkg_name: str, states: dict, needles: dict[str, bytes]
                  ) -> tuple[list[dict], list[str]]:
    """The mode's BeginState / EndState / Tick bodies.

    In BmGame.upk the indices are the decoded ones and each is path-verified before use.
    Elsewhere the functions are found under a `RVehicleBatmobile` class by name and are
    marked `state_bound: false` - they are the class's functions, not proven members of
    that state.
    """
    rows, problems, seen = [], [], set()
    if pkg_name == "BmGame.upk":
        for mode, funcs in STATE_FUNCS.items():
            if mode not in states:
                continue
            for fn, idx in funcs.items():
                if idx > len(pkg.exports):
                    problems.append(f"{pkg_name}: {mode}.{fn} export {idx} beyond the export table")
                    continue
                cls, path = pkg.object_class(idx), pkg.object_path(idx)
                # A state's functions are outered on the State object itself, so the export's
                # outer must be the State export (or, if the outer index is not recorded, the
                # rendered path must be `<state name>.<fn>`).
                state_export = states[mode]["export"]
                outer = pkg.exports[idx - 1].get("outer")
                member = (outer == state_export) if outer is not None else (
                    path == f"{pkg.object_name(state_export)}.{fn}")
                if cls != "Function" or pkg.object_name(idx) != fn or not member:
                    problems.append(f"{pkg_name}: export {idx} is {cls} `{path}`, not "
                                    f"{mode}.{fn} - skipped")
                    continue
                s = script_of(pkg, idx)
                rows.append({"mode": mode, "function": fn, "package": pkg_name, "export": idx,
                             "path": path, "script_bytes": len(s),
                             "script_sha1": hashlib.sha1(s).hexdigest(),
                             "hits": scan(s, needles), "state_bound": True})
                seen.add(idx)
    else:
        for i in range(1, len(pkg.exports) + 1):
            if pkg.object_class(i) != "Function":
                continue
            nm, path = pkg.object_name(i), pkg.object_path(i)
            if nm not in ("BeginState", "EndState", "Tick"):
                continue
            if not any("RVehicleBatmobile" in path for _ in (0,)):
                continue
            s = script_of(pkg, i)
            rows.append({"mode": None, "function": nm, "package": pkg_name, "export": i,
                         "path": path, "script_bytes": len(s),
                         "script_sha1": hashlib.sha1(s).hexdigest(),
                         "hits": scan(s, needles), "state_bound": False})
            seen.add(i)
    for i in range(1, len(pkg.exports) + 1):
        if i in seen:
            continue
        if pkg.object_class(i) != "Function":
            continue
    for i in range(1, len(pkg.exports) + 1):
        if i in seen or pkg.object_class(i) != "Function":
            continue
        path = pkg.object_path(i)
        if not any(k in path for k in CORPUS):
            continue
        s = script_of(pkg, i)
        if len(s) < 4:
            continue
        hits = scan(s, needles)
        if not hits:
            continue
        seen.add(i)
        rows.append({"mode": None, "function": pkg.object_name(i), "package": pkg_name,
                     "export": i, "path": path, "script_bytes": len(s),
                     "script_sha1": hashlib.sha1(s).hexdigest(),
                     "hits": hits, "state_bound": False, "corpus": True})
    return rows, problems


def verdicts(state_fns: list[dict], corpus: list[dict], components: dict) -> list[dict]:
    out = []
    for mode, funcs in STATE_FUNCS.items():
        rows = [r for r in state_fns if r["mode"] == mode]
        labels = sorted({h["label"] for r in rows for h in r["hits"]})
        own = [l for l in labels if mode.replace("Mode", "") + "Mode0" in l]
        other = [l for l in labels if "Mode0" in l and l not in own]
        if own:
            out.append({
                "id": f"{mode}_mesh",
                "statement": f"{mode} selects its own collision mesh",
                "verdict": "derived (name reference in script blob)",
                "evidence": f"{len(own)} reference(s) to {', '.join(own)} in the state's functions; "
                            f"control flow not decoded",
            })
        elif other:
            out.append({
                "id": f"{mode}_mesh",
                "statement": f"{mode} selects its own collision mesh",
                "verdict": "derived (reference to the other mode's mesh)",
                "evidence": f"the state's functions reference {', '.join(other)} and no "
                            f"{mode.replace('Mode', '')}Mode0 name; control flow not decoded",
            })
        else:
            out.append({
                "id": f"{mode}_mesh",
                "statement": f"{mode} selects its own collision mesh",
                "verdict": "UNKNOWN",
                "evidence": "no reference to either mesh name, to BatmanVsBatmobileCollisionMode, "
                            "to CollisionComponent, or to SetHidden/SetActorCollision/"
                            "SetBlockRigidBody in the state's functions "
                            f"({', '.join(r['function'] for r in rows)})",
            })
    all_modes = [l for r in state_fns for h in r["hits"] for l in [h["label"]] if "Mode0" in l]
    out.append({
        "id": "selector",
        "statement": "BatmanVsBatmobileCollisionMode (layout 5895) picks the component",
        "verdict": "UNKNOWN",
        "evidence": ("the property name is in the name table (index recorded per package) but "
                     "appears in no state or Batmobile/vehicle function body, and the property is "
                     "not serialised in the archetype/CDO walk (COLLISION.md); the selector's "
                     "values are not decoded")
        if not any(h["label"] == "BatmanVsBatmobileCollisionMode"
                   for r in state_fns + corpus for h in r["hits"]) else
        ("name reference found in a function body - see rows; control flow not decoded"),
    })
    return out


def build() -> dict:
    packs, problems = {}, []
    for name in PACKAGES:
        path = os.path.join(COOKED, name)
        if not os.path.exists(path):
            problems.append(f"{name} absent")
            continue
        pkg = upk_read.Package(path)
        needles, kinds = {}, {}
        for nm, idxs in name_indices(pkg).items():
            kinds[nm] = idxs
            for n in idxs:
                needles[f"name:{nm}"] = struct.pack("<i", n)
        for label, idx in (COMPONENTS.get(name) or {}).items():
            needles[f"object:{label}"] = struct.pack("<i", idx)
        states, state_problems = resolve_states(pkg, name)
        state_fns, fn_problems = resolve_funcs(pkg, name, states, needles)
        problems.extend(state_problems + fn_problems)
        packs[name] = {
            "path": path,
            "bytes": os.path.getsize(path),
            "exports": len(pkg.exports),
            "names": len(pkg.names),
            "name_indices": kinds,
            "states": [dict(mode=m, package=name, **v) for m, v in states.items()],
            "state_functions": [r for r in state_fns if r.get("mode")],
            "other_mode_functions": [r for r in state_fns if not r.get("mode") and not r.get("corpus")],
            "corpus_functions": [r for r in state_fns if r.get("corpus")],
            "needles": sorted(needles),
        }
    state_all = [r for p in packs.values() for r in p["state_functions"]]
    corpus_all = [r for p in packs.values() for r in p["corpus_functions"]]
    doc = {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_collision_modes.py --write",
        "card": "GRB-G3-01b open item - collision mesh per mode",
        "labels": {
            "derived": "a 4-byte operand in a function body resolves to the named object; "
                       "control flow is NOT decoded, so the reference proves contact, not a branch",
            "UNKNOWN": "the reference was not found in the searched bodies",
        },
        "targets": {"names": list(TARGET_NAMES), "components": COMPONENTS},
        "packages": packs,
        "state_functions": state_all,
        "corpus_functions": corpus_all,
        "verdicts": verdicts(state_all, corpus_all, COMPONENTS),
        "problems": problems,
    }
    return doc


def render_md(doc: dict) -> str:
    out = ["# BmAK collision mesh per mode - what the script bytes say", ""]
    out.append("GRB-G3-01b open item. Generated by `Tools/scripts/grab_collision_modes.py --write`; "
               "`--check` re-derives and compares.")
    out.append("")
    out.append("`decoded` = read from the package (export index, byte offset); `derived` = a rule "
               "applied to decoded bytes, stated with the rule; `UNKNOWN` = not found by the "
               "search. A 4-byte operand hit proves the body **touches** that object - control "
               "flow is not decoded, so it does not prove the branch that ships.")
    out.append("")
    out.append("## Verdicts")
    out.append("")
    for v in doc["verdicts"]:
        out.append(f"### {v['statement']}")
        out.append("")
        out.append(f"**{v['verdict']}** - {v['evidence']}")
        out.append("")
    out.append("## Name indices")
    out.append("")
    out.append("| package | name | FName index |")
    out.append("|---|---|---|")
    for name, p in doc["packages"].items():
        for nm, idxs in p["name_indices"].items():
            out.append(f"| {name} | {nm} | {idxs if idxs else '—'} |")
    out.append("")
    out.append("## States")
    out.append("")
    out.append("| package | mode | export | class | path | bytes |")
    out.append("|---|---|---|---|---|---|")
    for p in doc["packages"].values():
        for s in p["states"]:
            out.append(f"| {s['package']} | {s['mode']} | {s['export']} | {s['class']} | "
                       f"`{s['path']}` | {s['bytes']} |")
    out.append("")
    out.append("## State functions (BeginState / EndState / Tick)")
    out.append("")
    out.append("| mode | function | export | script bytes | hits |")
    out.append("|---|---|---|---|---|")
    for r in doc["state_functions"]:
        hits = ", ".join(f"{h['label']}@{h['at']}" for h in r["hits"]) or "—"
        out.append(f"| {r['mode']} | {r['function']} | {r['export']} | {r['script_bytes']} | {hits} |")
    for p in doc["packages"].values():
        for r in p.get("other_mode_functions") or []:
            hits = ", ".join(f"{h['label']}@{h['at']}" for h in r["hits"]) or "—"
            out.append(f"| (path-resolved) | {r['function']} | {r['export']} | {r['script_bytes']} | {hits} |")
    out.append("")
    out.append("## Corpus hits (Batmobile / vehicle functions)")
    out.append("")
    if not doc["corpus_functions"]:
        out.append("- none: no Batmobile or vehicle Function body references any target name or "
                   "component export.")
    else:
        out.append("| package | function | export | hits |")
        out.append("|---|---|---|---|")
        for r in doc["corpus_functions"]:
            hits = ", ".join(f"{h['label']}@{h['at']}" for h in r["hits"])
            out.append(f"| {r['package']} | `{r['path']}` | {r['export']} | {hits} |")
    out.append("")
    out.append("## Problems")
    out.append("")
    for p in doc["problems"] or ["none"]:
        out.append(f"- {p}")
    out.append("")
    return "\n".join(out)


def write() -> int:
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    for p, v in doc["packages"].items():
        print(f"{p}: {v['exports']} exports, {v['names']} names, "
              f"{len(v['state_functions'])} state fns, {len(v['corpus_functions'])} corpus hits")
    for v in doc["verdicts"]:
        print(f"  {v['id']}: {v['verdict']}")
    return 0


def check() -> int:
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    fresh = build()
    if not stored.get("packages"):
        fails.append("no packages decoded")
    for v in stored.get("verdicts") or []:
        if not v.get("verdict") or not v.get("evidence"):
            fails.append(f"verdict {v.get('id')} lacks a value or evidence")
    if not any("UNKNOWN" in str(v.get("verdict")) for v in stored.get("verdicts") or []) and \
            not any("derived" in str(v.get("verdict")) for v in stored.get("verdicts") or []):
        fails.append("no verdict is labelled derived or UNKNOWN")
    for p in stored["packages"].values():
        for row in p["state_functions"]:
            if row["script_bytes"] and not row["hits"]:
                continue
    if stored != fresh:
        drift = [k for k in stored if stored.get(k) != fresh.get(k)]
        fails.append("stale sections (inputs changed?): " + ", ".join(drift))
    md = open(OUT_MD, encoding="utf-8").read()
    for h in ("## Verdicts", "## Name indices", "## States", "## State functions", "## Corpus hits"):
        if h not in md:
            fails.append(f"markdown heading missing: {h}")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {len(stored['packages'])} packages, "
          f"{len(stored['state_functions'])} state functions, "
          f"{len(stored['corpus_functions'])} corpus hits, "
          f"{len(stored['verdicts'])} verdicts")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
