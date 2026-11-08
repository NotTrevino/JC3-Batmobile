"""bm_fx.py - B-08: the Batmobile's effect attachments (`.epe`).

`GRAB_BACKLOG.md` §8 (`B-08`): "add the afterburner flame / heat haze at `Afterburner` socket with
the usage from G2-22; weapon effects come with B-06; damage/death effects per T-14."
Done: "every effect path resolves; usage hash exists in the fleet vocabulary."

What the files say, measured before the edit (this script re-measures all of it, it never types a
number, R11)
-----------------------------------------------------------------------------------------------
* An effect attachment object (`SAttachedEffect` / `SDynamicAttachedEffect` / the two `…Table`
  classes) points at its effect through the **`Effect` member = `hash_jenkins(<.effc path>)`**, not
  through a name: every distinct `Effect` value in the base graph maps to exactly one of the 955
  distinct `.effc` paths that `Research/JC3Grab/FX_TABLE.jsonl` carries for the whole fleet.
* The afterburner flame is **already in the donor graph, already under `EngineNitro`**:
  `exhaust_upgrade_nitrous` and `exhaust_upgrade_nitrous2` both carry `Usage` `-97082140` =
  `4197885156` = `EngineNitro` (`Research/JC3Grab/USAGES.json` `nitro.usage.objects` lists exactly
  those two names) and `Effect` `-776668445` = `hash_jenkins("effects/jc_vehicles/exhaust/\
  car_cycle_base_dual_nitrous.effc")`, T-FX7's chosen effect. Their `world` sits at the Serpente's
  twin exhausts `(±0.410, 0.373, 2.480)`, which is not the Batmobile's jet.
  So the card's build step is **placement**: the two emitters get the `Afterburner` socket's matrix
  (`Research/BatmobileGrab/SOCKETS_JC3.json`, G1-13, bone `JetSMove`). No object is added or
  removed - the donor runs two emitters per pipe (each points at a *dual* exhaust `.effc`), so a
  one-nozzle car keeps the pair at the one socket.
* T-17 now reads 17 rows / 17 chosen carriers / 0 named omissions (`apply-effects-rows.md`).
  Heat haze (T-FX9), tracer and round trail (T-FX12/T-FX16), casings (T-FX13) and brake trail
  (T-FX20) name shipped carriers or an authoring plan, but the private `.effc` copies are **B-17**
  (the writer), not this card. B-08 attaches the flame; every Effect hash is gated to a `.effc`
  path that exists in the build tree, and every Usage to the fleet vocabulary. The four weapon
  rows (T-FX10/11/14/15) are B-06's payload; damage/death (T-FX21/22/23) are `keep`: the donor's
  `exp_car_01`, `dmg_fire_engine`/`_spread_base`/`_spread_roof`, `dmg_post_burn`/`dmg_smoke_engine`
  objects are present and hash-resolve. This script writes rows for that decision, it does not
  invent effects or author new `.effc` files.

Usage
    python Tools/scripts/bm_fx.py --write    # stage Builds/bm-008, edit, re-import, spec, receipt
    python Tools/scripts/bm_fx.py --check    # re-derive, compare, run both Done criteria
    python Tools/scripts/bm_fx.py --write --base bm-RC4-parts --tag bm-RC4-effects
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_entity as E                                # noqa: E402  (the one mat/hash/ConvertProperty set)
import jc3wiring                                     # noqa: E402  (the only .epe reader)

CARD = "B-08"
BASE_TAG = "bm-005"
TAG = "bm-008"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
EPE = EE.replace(".ee", ".epe")
ENT = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
BASE_DIR = os.path.join(ROOT, "Builds", BASE_TAG)
BASE_EPE = os.path.join(BASE_DIR, "aaf", ENT, EPE)
OUT = os.path.join(ROOT, "Builds", TAG)
OUT_EPE = os.path.join(OUT, "aaf", ENT, EPE)
SPEC = os.path.join(ROOT, "Working", "Effects", "bm_fx_edits.json")
T17 = os.path.join(ROOT, "Working", "Translation", "t17_fx.json")
SOCKETS = os.path.join(ROOT, "Research", "BatmobileGrab", "SOCKETS_JC3.json")
USAGES = os.path.join(ROOT, "Research", "JC3Grab", "USAGES.json")
FX = os.path.join(ROOT, "Research", "JC3Grab", "FX_TABLE.jsonl")
SCHEMA = 1

# the effect-attachment classes G2-22 counted (USAGES.md §3)
EFFECT_CLASSES = ("SAttachedEffect", "SDynamicAttachedEffect",
                  "SAttachedEffectTable", "SDynamicAttachedEffectTable")


def set_tags(base_tag: str, tag: str) -> None:
    """--base / --tag: apply the same B-08 edit to another build line.

    The `.epe` name is read from the base tree, so a line that still ships the donor leaf (the RC4
    tree before B-13b's rename is merged) works without hard-coding the leaf.
    """
    global BASE_TAG, TAG, BASE_DIR, BASE_EPE, OUT, OUT_EPE, EE, EPE
    BASE_TAG, TAG = base_tag, tag
    BASE_DIR = os.path.join(ROOT, "Builds", BASE_TAG)
    OUT = os.path.join(ROOT, "Builds", TAG)
    ent = os.path.join(BASE_DIR, "aaf", ENT)
    epes = sorted(f for f in os.listdir(ent) if f.endswith(".epe"))
    if len(epes) != 1:
        raise SystemExit(f"{E.rel(ent)}: expected exactly one .epe, found {epes}")
    EPE = epes[0]
    EE = EPE[:-4] + ".ee"
    BASE_EPE = os.path.join(ent, EPE)
    OUT_EPE = os.path.join(OUT, "aaf", ENT, EPE)


def spec_path() -> str:
    """bm-008 keeps the original spec file; a refreshed line gets its own record."""
    name = "bm_fx_edits.json" if TAG == "bm-008" else f"bm_fx_edits_{TAG}.json"
    return os.path.join(ROOT, "Working", "Effects", name)


# ------------------------------------------------------------------ inputs
def umask(v: int) -> int:
    """A stored int32 as the game's uint32 key (the XML writes them signed)."""
    return v + (1 << 32) if v < 0 else v


def sint(v: int) -> int:
    """The uint32 key as the signed int the XML writes."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >= (1 << 31) else v


def h(s: str) -> int:
    return E.h(s)


def effect_vocabulary() -> dict[int, str]:
    """Every distinct `.effc` path the fleet indexes, keyed by its hash (FX_TABLE, G2-9).

    `hash -> path` only when the hash is unambiguous, which is the property Done 1 rests on.
    """
    paths: set[str] = set()
    with open(FX, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("ext") == ".effc":
                paths.add(r["path"])
    seen: dict[int, set[str]] = {}
    for p in paths:
        seen.setdefault(umask(h(p)), set()).add(p)
    return {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}, seen


def usage_vocabulary() -> dict[int, dict]:
    d = json.load(open(USAGES, encoding="utf-8"))
    return {v["usage"]: v for v in d["epe"]["values"]}


def rows_by_id() -> dict[str, dict]:
    return {r["id"]: r for r in json.load(open(T17, encoding="utf-8"))["rows"]}


def sockets() -> dict[str, dict]:
    return {s["socket"]: s for s in json.load(open(SOCKETS, encoding="utf-8"))["sockets"]}


# ------------------------------------------------------------------ the edit plan
def plan(root, ctx) -> dict:
    rows = ctx["rows"]
    flame = rows["T-FX7"]
    path = flame["chosen"]["path"]
    want_effect = umask(h(path))
    usage_name = flame["trigger"]
    cands = [u for u, v in ctx["usage_vocab"].items() if v.get("name") == usage_name]
    if len(cands) != 1:
        raise SystemExit(f"{usage_name!r}: {len(cands)} usage values in the fleet vocabulary")
    want_usage = cands[0]
    hashes = ctx["effect_vocab"]
    if want_effect not in hashes:
        raise SystemExit(f"T-FX7's effect path {path!r} is not in the fleet .effc vocabulary")

    sk = ctx["sockets"][flame["attachment"]["name"]]
    world = E.mat(sk["position_m"], sk["forward_jc3"], sk["up_jc3"])

    edits, emitters = [], []
    for o in E.objects(root):
        if E.vcls(o) not in EFFECT_CLASSES:
            continue
        eff = o.find("value[@name='Effect']")
        if eff is None or not (eff.text or "").strip():
            continue
        if umask(int(eff.text)) != want_effect:
            continue
        usage = o.find("value[@name='Usage']")
        got = [umask(int(t)) for t in (usage.text or "").split(",") if t.strip()]
        name = E.vname(o)
        if want_usage not in got:
            raise SystemExit(f"{name!r} points at {path!r} but its Usage is {got}, "
                             f"not {want_usage} ({usage_name}) - the flame row is not this object")
        old = E.get_value(o, "world") if any(v.get("name") == "world" for v in o.findall("value")) \
            else None
        if old is None:
            raise SystemExit(f"{name!r} has no named `world` member to place")
        E.set_value(o, "world", world)
        emitters.append(name)
        edits.append({"class": E.vcls(o), "name": name, "member": "world",
                      "row": "T-FX7", "old": old, "new": world,
                      "why": f"the afterburner flame belongs on socket "
                             f"{flame['attachment']['name']} (G1-13, bone {sk['bone']}); the donor "
                             f"world is the Serpente's exhaust"})
    if not emitters:
        raise SystemExit(f"no effect object in the base graph points at {path!r}")

    # the rows this card does not build, each with the evidence that says why
    actions = {
        "T-FX7": ("written", f"both EngineNitro emitters placed on `Afterburner`"),
        "T-FX8": ("kept", "T-17 `propose` = keep; the donor's `exhaust`/`exhaust2` stay where the "
                          "donor graph has them (this card's Do names only the afterburner socket)"),
        "T-FX9": ("shipped", "T-17 `next`: the fleet's heater effect `car_speedrom_heater.effc` "
                              "is the haze carrier; the private tuning copy is B-17"),
        "T-FX10": ("b-06", "weapon effect: the `.effc` rides the cloned weapon bundle (T-11/B-06)"),
        "T-FX11": ("b-06", "weapon effect: the `.effc` rides the cloned weapon bundle (T-11/B-06)"),
        "T-FX12": ("shipped", "T-17 `next`: the linear half is the cloned WeaponTuning; the art "
                               "half rides the shipped `missile_trail_car.effc`, private copy B-17"),
        "T-FX13": ("shipped", "T-17 `next`: shipped `bullet_eject_minigun.effc` plus the "
                               "`SAttachedEffect ShellEjection` under the weapon entity; copy/attachment "
                               "on the weapon is B-17"),
        "T-FX14": ("b-06", "weapon effect: the `.effc` rides the cloned weapon bundle (T-11/B-06)"),
        "T-FX15": ("b-06", "weapon effect: the `.effc` rides the weapon's own explosion tune (T-11/B-06)"),
        "T-FX16": ("shipped", "T-17 `next`: the shipped `missile_trail_car.effc` is the round-trail "
                               "carrier (same file as T-FX12); the private copy is B-17"),
        "T-FX17": ("kept", "T-17 `propose` = keep; the donor's wheel-trail family is carried by the "
                           "`.ee`, not by the graph"),
        "T-FX18": ("kept", "T-17 `propose` = keep; the donor's chassis-slide family is carried by "
                           "the `.ee`"),
        "T-FX19": ("not-this-card", "T-FX19 is `derived` and not in B-08's Do; the donor already "
                                    "carries `spark_trail_02_med` on `dynamic_trail_effect`"),
        "T-FX20": ("shipped", "T-17 `next`: a restyle of the shipped "
                               "`car_cycle_base_dual_nitrous.effc` at `BrakeTrailL/R`; the private "
                               "copy and the brake trigger are B-17"),
        "T-FX21": ("kept", "damage/death per T-14: the donor's `explosion` object already points at "
                           "`exp_car_01.effc` (T-FX21 `keep`)"),
        "T-FX22": ("kept", "damage/death per T-14: the donor's `damage_fire_*`/`dynamic_burn_*` "
                           "objects already point at the 3-variant fire family (T-FX22 `keep`)"),
        "T-FX23": ("kept", "damage/death per T-14: the donor's `fire_post_explosion` object already "
                           "points at `dmg_post_burn.effc` (T-FX23 `keep`)"),
    }
    row_plan = []
    for rid in sorted(rows, key=lambda r: int(r.rsplit("FX", 1)[1])):
        r = rows[rid]
        action, why = actions.get(rid, ("unplanned", "no action planned"))
        row_plan.append({
            "row": rid, "code": r["code"], "feature": r.get("feature"),
            "t17_dispo": r["dispo"],
            "chosen_path": (r.get("chosen") or {}).get("path"),
            "attachment": f"{r['attachment']['kind']}:{r['attachment']['name']}",
            "trigger": r.get("trigger"),
            "action": action, "why": why,
        })
    unknown = [p for p in row_plan if p["action"] == "unplanned"]
    if unknown:
        raise SystemExit(f"T-17 row(s) with no B-08 action: {[p['row'] for p in unknown]}")

    return {
        "schema": SCHEMA, "card": CARD, "generator": E.rel(__file__),
        "base": {"build": E.rel(BASE_DIR), "epe": E.rel(BASE_EPE),
                 "epe_sha256": E.sha(open(BASE_EPE, "rb").read()),
                 "bytes": os.path.getsize(BASE_EPE)},
        "inputs": {
            "t17": E.rel(T17) + " (T-17: the 17 FX rows)",
            "sockets": E.rel(SOCKETS) + " (G1-13: 65 sockets in JC3 metres)",
            "usages": E.rel(USAGES) + " (G2-22: the 155-value `.epe` usage vocabulary)",
            "fx_table": E.rel(FX) + " (G2-9: 57,187 effect/camera/trim rows, 955 `.effc`)",
            "base_graph": E.rel(BASE_EPE) + " (B-05)",
        },
        "socket": {k: sk[k] for k in ("socket", "bone", "bone_parent", "role",
                                      "position_m", "forward_jc3", "up_jc3")},
        "world": world,
        "flame": {"row": "T-FX7", "effect_path": path, "effect_hash": sint(want_effect),
                  "usage": usage_name, "usage_hash": want_usage,
                  "emitters": emitters},
        "edits": edits,
        "rows": row_plan,
        "counts": {"emitters_placed": len(emitters), "edits": len(edits),
                   "rows": len(row_plan)},
    }


# ------------------------------------------------------------------ build / check helpers
def census(path: str):
    return jc3wiring.parse_epe(path)


def objects_with_effect(root):
    out = []
    for o in E.objects(root):
        if E.vcls(o) not in EFFECT_CLASSES:
            continue
        eff = o.find("value[@name='Effect']")
        if eff is None or not (eff.text or "").strip():
            continue
        out.append(o)
    return out


def usage_pairs(root) -> list[tuple[int, str, str]]:
    pairs = []
    for o in E.objects(root):
        if E.vcls(o) not in EFFECT_CLASSES:
            continue
        u = o.find("value[@name='Usage']")
        if u is None or not (u.text or "").strip():
            continue
        for t in u.text.split(","):
            if t.strip():
                pairs.append((umask(int(t)), E.vname(o), E.vcls(o)))
    return pairs


def done_report(root, ctx, doc) -> dict:
    """Both Done criteria of the card, re-derived from the built graph."""
    effv, effv_all = ctx["effect_vocab"], ctx["effect_vocab_all"]
    resolved, unresolved = {}, []
    for o in objects_with_effect(root):
        k = umask(int(o.find("value[@name='Effect']").text))
        if k in effv:
            resolved.setdefault(k, effv[k])
        else:
            unresolved.append((E.vname(o), E.vcls(o), sint(k)))
    # every T-17 chosen path must exist in the fleet effect vocabulary
    chosen = {r["id"]: r["chosen"]["path"] for r in ctx["rows"].values() if r.get("chosen")}
    chosen_bad = [rid for rid, p in chosen.items() if umask(h(p)) not in effv]
    # the flame path, in the build tree or in the donor container's own effect set
    flame_path = doc["flame"]["effect_path"]
    in_tree = os.path.exists(os.path.join(OUT, "aaf", flame_path))
    donor_rows = set()
    with open(FX, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["container"].endswith(EE) and r.get("ext") == ".effc":
                donor_rows.add(r["path"])

    usg = ctx["usage_vocab"]
    upairs = usage_pairs(root)
    outside = [(u, n) for (u, n, _c) in upairs if u not in usg]
    emitters = [o for o in objects_with_effect(root)
                if umask(int(o.find("value[@name='Effect']").text))
                == umask(h(flame_path))]
    emitter_usage = sorted({umask(int(t)) for o in emitters
                            for t in (o.find("value[@name='Usage']").text or "").split(",")
                            if t.strip()})
    tree_missing = sorted(p for p in resolved.values()
                          if not os.path.exists(os.path.join(OUT, "aaf", p)))
    return {
        "effect_objects": len(objects_with_effect(root)),
        "effect_hashes": len({umask(int(o.find("value[@name='Effect']").text))
                              for o in objects_with_effect(root)}),
        "resolved": len(resolved), "unresolved": unresolved,
        "effect_paths_in_tree": len(resolved) - len(tree_missing),
        "effect_paths_missing_in_tree": tree_missing,
        "chosen_paths": len(chosen), "chosen_outside_vocabulary": chosen_bad,
        "flame_path": flame_path, "flame_in_build_tree": in_tree,
        "flame_in_donor_container": flame_path in donor_rows,
        "donor_container_effc": len(donor_rows),
        "usage_pairs": len(upairs), "usage_pairs_outside": outside,
        "usage_vocabulary": len(usg),
        "emitters": len(emitters), "emitter_usage": emitter_usage,
        "emitter_usage_name": [usg.get(u, {}).get("name") for u in emitter_usage],
    }


def build(write: bool = True) -> dict:
    ctx = {"rows": rows_by_id(), "usage_vocab": usage_vocabulary(), "sockets": sockets()}
    effv, effv_all = effect_vocabulary()
    ctx["effect_vocab"], ctx["effect_vocab_all"] = effv, effv_all
    tmp = tempfile.mkdtemp(prefix="bm_fx_")
    base_xml = os.path.join(tmp, "base.xml")
    E.export(BASE_EPE, base_xml)
    root = ET.parse(base_xml).getroot()
    base_census = census(base_xml)
    doc = plan(root, ctx)
    doc["base"]["objects"] = len(base_census)
    doc["base"]["classes"] = len({o.cls for o in base_census})
    built_xml = os.path.join(ROOT, "tmp", "b08", f"built_{TAG}.xml")
    os.makedirs(os.path.dirname(built_xml), exist_ok=True)
    ET.ElementTree(root).write(built_xml, encoding="utf-8", xml_declaration=True)
    if write:
        os.makedirs(os.path.dirname(OUT_EPE), exist_ok=True)
        E.imp(built_xml, OUT_EPE)
    built_census = census(built_xml)
    doc["built"] = {"epe": E.rel(OUT_EPE) if write else "(not written)",
                    "objects": len(built_census),
                    "classes": len({o.cls for o in built_census}),
                    "expected_xml": built_xml}
    doc["counts"]["base_objects"] = len(base_census)
    doc["counts"]["built_objects"] = len(built_census)
    doc["counts"]["added_objects"] = len(built_census) - len(base_census)
    # the Done criteria, computed on the *plan* graph (the check re-runs them on the built file)
    doc["done"] = done_report(root, ctx, doc)
    return doc


def installer_text() -> str:
    return "\n".join([
        "<#",
        "    B-08 effect attachments installer. Generated by Tools/scripts/bm_fx.py.",
        "    Generated, never run by it. Close the game before -Action Install.",
        "    -GameDir defaults to the real install; point it at a copy to rehearse offline.",
        "#>",
        "[CmdletBinding()]",
        "param([ValidateSet('Install','Verify','Rollback091','Status')]"
        "[string]$Action = 'Status', [string]$GameDir = 'D:\\Games\\Just Cause 3')",
        "$ErrorActionPreference = 'Stop'",
        "$B = '" + OUT + "'",
        "$D = Join-Path $GameDir 'dropzone\\" + ENT + "'",
        "switch ($Action) {",
        "    'Install' {",
        "        New-Item -ItemType Directory -Force -Path $D | Out-Null",
        "        Copy-Item -LiteralPath (Join-Path $B 'aaf\\" + ENT + "\\" + EPE + "') "
        "-Destination (Join-Path $D '" + EPE + "') -Force",
        "        Write-Host 'deployed " + EPE + "'",
        "    }",
        "    'Verify' {",
        "        $p = Join-Path $D '" + EPE + "'",
        "        if (-not (Test-Path -LiteralPath $p)) { throw ('missing ' + $p) }",
        "        Write-Host ('verified ' + $p + ' ' + (Get-FileHash -LiteralPath $p).Hash)",
        "    }",
        "    'Rollback091' {",
        "        Remove-Item -LiteralPath (Join-Path $D '" + EPE + "') -Force -ErrorAction SilentlyContinue",
        "        if ($GameDir -eq 'D:\\Games\\Just Cause 3') {",
        "            & (Join-Path 'E:\\Modding\\JC3-Batmobile\\Builds\\test-091' 'install.ps1') "
        "-Action Install",
        "        } else { Write-Host ('rehearsal on ' + $GameDir + ': test-091 re-install skipped') }",
        "    }",
        "    'Status' { Write-Host ('epe: ' + (Join-Path $D '" + EPE + "')) }",
        "}",
    ]) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--base", default=BASE_TAG, help=f"base build tag (default {BASE_TAG})")
    ap.add_argument("--tag", default=TAG, help=f"build tag to write/check (default {TAG})")
    a = ap.parse_args()
    if a.base != BASE_TAG or a.tag != TAG:
        set_tags(a.base, a.tag)
    if a.write:
        if os.path.exists(OUT):
            if TAG != "bm-008":
                raise SystemExit(f"{E.rel(OUT)} exists: a `--tag` tree is never rebuilt in place; "
                                 f"delete it or pass a new tag")
            shutil.rmtree(OUT)
        os.makedirs(OUT)
        shutil.copytree(os.path.join(BASE_DIR, "aaf"), os.path.join(OUT, "aaf"))
        doc = build(write=True)
        os.makedirs(os.path.dirname(SPEC), exist_ok=True)
        os.makedirs(os.path.dirname(spec_path()), exist_ok=True)
        with open(spec_path(), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        with open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
            f.write(installer_text())
        receipt = {"schema": SCHEMA, "card": CARD, "tag": TAG, "base": E.rel(BASE_DIR),
                   "epe": {"file": E.rel(OUT_EPE), "sha256": E.sha(open(OUT_EPE, "rb").read()),
                           "bytes": os.path.getsize(OUT_EPE)},
                   "counts": doc["counts"], "socket": doc["socket"], "world": doc["world"],
                   "flame": doc["flame"], "edits": doc["edits"], "rows": doc["rows"],
                   "done": doc["done"], "installed": False}
        with open(os.path.join(OUT, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(receipt, f, indent=1)
        d = doc["done"]
        print(f"wrote {E.rel(OUT_EPE)}: {doc['counts']['edits']} edit(s) on "
              f"{doc['counts']['emitters_placed']} emitter(s); objects "
              f"{doc['counts']['base_objects']} -> {doc['counts']['built_objects']}")
        print(f"  socket {doc['socket']['socket']} ({doc['socket']['bone']}) "
              f"pos {doc['socket']['position_m']}")
        print(f"  Done 1: {d['resolved']}/{d['effect_hashes']} distinct Effect hashes resolve "
              f"({len(d['unresolved'])} unresolved), {d['chosen_paths']} T-17 chosen paths, "
              f"flame in build tree {d['flame_in_build_tree']}")
        print(f"  Done 2: {d['usage_pairs']} (usage, object) pairs, "
              f"{len(d['usage_pairs_outside'])} outside the {d['usage_vocabulary']}-value "
              f"vocabulary; emitters carry {d['emitter_usage']} = {d['emitter_usage_name']}")
        return
    sys.exit(check())


def check() -> int:
    fails: list[str] = []
    doc = build(write=False)
    if not os.path.exists(OUT_EPE):
        print("FAIL: " + E.rel(OUT_EPE) + " missing (run --write)")
        return 1
    tmp = tempfile.mkdtemp(prefix="bm_fx_check_")
    x1 = os.path.join(tmp, "a.xml")
    x2 = os.path.join(tmp, "b.xml")
    y = os.path.join(tmp, "b.epe")
    E.export(OUT_EPE, x1)
    E.imp(x1, y)
    if E.sha(open(OUT_EPE, "rb").read()) != E.sha(open(y, "rb").read()):
        fails.append("ConvertProperty --e/--i does not reproduce the built .epe")
    E.export(y, x2)
    if open(x1, "rb").read() != open(x2, "rb").read():
        fails.append("the round-tripped XML differs from the built XML")
    if os.path.exists(os.path.join(OUT, "receipt.json")):
        rec = json.load(open(os.path.join(OUT, "receipt.json"), encoding="utf-8"))
        if rec.get("epe", {}).get("sha256") != E.sha(open(OUT_EPE, "rb").read()):
            fails.append("the receipt's .epe sha256 does not match the built file")
    # the base build must be untouched (R7-style: a card writes into its own lineage only)
    if E.sha(open(BASE_EPE, "rb").read()) != doc["base"]["epe_sha256"]:
        fails.append("the base build's .epe changed - a card may not edit its dependency")
    # the built graph must be the graph the plan derives, value for value

    def norm(v: str):
        try:
            return tuple(round(float(x), 6) + 0.0 for x in str(v).split(","))
        except ValueError:
            try:
                return round(float(v), 6) + 0.0
            except ValueError:
                return str(v)

    def key(o):
        return (o.cls, o.name, tuple(sorted((k, norm(v)) for k, v in o.props.items())))

    from collections import Counter
    a_set = Counter(repr(key(o)) for o in census(x1))
    b_set = Counter(repr(key(o)) for o in census(doc["built"]["expected_xml"]))
    if a_set != b_set:
        extra = list((a_set - b_set).elements())[:2]
        missing = list((b_set - a_set).elements())[:2]
        fails.append(f"the built .epe differs from the re-derived plan: "
                     f"{sum((b_set - a_set).values())} object(s) missing, "
                     f"{sum((a_set - b_set).values())} unexpected, "
                     f"e.g. missing {missing} / unexpected {extra}")
    if doc["counts"]["added_objects"] != 0:
        fails.append(f"the plan adds/removes {doc['counts']['added_objects']} object(s); "
                     f"B-08 changes two mats and no structure")
    # the written mats are the socket's, member for member
    built_root = ET.parse(x1).getroot()
    want = doc["world"]
    fl = [o for o in objects_with_effect(built_root)
          if umask(int(o.find("value[@name='Effect']").text)) == umask(h(doc["flame"]["effect_path"]))]
    if len(fl) != doc["counts"]["emitters_placed"]:
        fails.append(f"{len(fl)} emitter(s) carry the flame effect, expected "
                     f"{doc['counts']['emitters_placed']}")
    for o in fl:
        if norm(E.get_value(o, "world")) != norm(want):
            fails.append(f"emitter {E.vname(o)!r} does not carry the socket's matrix")
    # ---- Done 1: every effect path resolves
    effv, effv_all = effect_vocabulary()
    d = done_report(built_root, {"effect_vocab": effv, "effect_vocab_all": effv_all,
                                 "rows": rows_by_id(),
                                 "usage_vocab": usage_vocabulary()}, doc)
    if d["unresolved"]:
        fails.append(f"Done 1: {len(d['unresolved'])} Effect hash(es) resolve to no fleet .effc: "
                     f"{d['unresolved'][:3]}")
    if d["chosen_outside_vocabulary"]:
        fails.append(f"Done 1: T-17 chosen path(s) outside the fleet vocabulary: "
                     f"{d['chosen_outside_vocabulary']}")
    if not (d["flame_in_build_tree"] or d["flame_in_donor_container"]):
        fails.append(f"Done 1: the flame path {d['flame_path']!r} exists neither in the build tree "
                     f"nor in the donor container's effect set")
    if d["effect_paths_missing_in_tree"]:
        fails.append(f"Done 1: {len(d['effect_paths_missing_in_tree'])} Effect path(s) are not "
                     f"files in the build tree: {d['effect_paths_missing_in_tree'][:3]}")
    # ---- Done 2: the usage hash exists in the fleet vocabulary
    if d["usage_pairs_outside"]:
        fails.append(f"Done 2: {len(d['usage_pairs_outside'])} usage value(s) are outside the "
                     f"fleet vocabulary: {d['usage_pairs_outside'][:3]}")
    if d["emitter_usage"] != [doc["flame"]["usage_hash"]]:
        fails.append(f"Done 2: the emitters carry {d['emitter_usage']}, "
                     f"expected [{doc['flame']['usage_hash']}]")
    if d["emitter_usage_name"] != [doc["flame"]["usage"]]:
        fails.append(f"Done 2: the emitters' usage does not name {doc['flame']['usage']!r}: "
                     f"{d['emitter_usage_name']}")
    if fails:
        for f in fails:
            print("FAIL: " + f)
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print(f"PASS: {E.rel(OUT_EPE)} {doc['counts']['base_objects']} -> "
          f"{doc['counts']['built_objects']} objects, {doc['counts']['edits']} mat edit(s) on "
          f"socket {doc['socket']['socket']} ({doc['socket']['bone']})")
    print(f"  Done 1  effect paths: {d['effect_objects']} effect objects / "
          f"{d['effect_hashes']} distinct Effect hashes, {d['resolved']} resolve to exactly one of "
          f"the fleet's `.effc` paths, {len(d['unresolved'])} unresolved, "
          f"{d['effect_paths_in_tree']}/{d['resolved']} present in the build tree; T-17 chosen paths "
          f"{d['chosen_paths']}/{d['chosen_paths']} in the vocabulary; flame path "
          f"{d['flame_path']} in the build tree = {d['flame_in_build_tree']} "
          f"(donor container set {d['donor_container_effc']} `.effc`)")
    print(f"  Done 2  usage vocabulary: {d['usage_pairs']} (usage, object) pairs over the "
          f"{d['usage_vocabulary']}-value fleet vocabulary, {len(d['usage_pairs_outside'])} "
          f"outside; the {d['emitters']} emitter(s) carry {d['emitter_usage']} = "
          f"{d['emitter_usage_name']}")
    return 0


if __name__ == "__main__":
    main()
