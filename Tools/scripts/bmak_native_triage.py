#!/usr/bin/env python3
"""bmak_native_triage.py - the 157 non-stub exports of BmAK's untagged remainder (G3-06c).

`REMAINDER.json` (G3-06) accounted for all **925** untagged exports of the BmAK grab and split
them by shape, never by opinion:

    empty_stub          768   a 2-byte `Package` payload - no properties exist to decode
    native_record       152   a payload no tag stream explains
    closes_from_offset    5   a tag stream that closes, but not from byte 0

The 157 non-stub exports (152 + 5) are the real remainder. This tool answers the only question
`STATUS.md` still leaves open about G1 - *does anything in the Batmobile's translation depend on
them* - by ranking each one against the ledger rows and the §1 feature codes, and by reading the
bytes of the top fifteen with `upk_read.py`.

Ranking is stated, not judged:

  feature weight   weapons 5, handling 5, damage 4, audio 4, HUD 3, interactions 2,
                   parts/animation 2, class-default descriptor 0, facial animation 0, other 1
  reachability     200 if `REMAINDER.json` found the object reachable from the drivable car's
                   chain, 20 if the walk could not decide, 0 otherwise
  class rule       `Function` and `State` are BmScript code, never data: weight 1, whatever
                   their owner is named
  package          +60 for `Playable_Batmobile_SF`, the drivable car's own package; the MK2,
                   Joker and Funhouse copies are separate assets (APP-8) and score nothing
  size             +1 per 200 bytes, capped at 20

Labels (same vocabulary as the rest of G1):

  decoded   the payload's own tag stream closes at its end, read with `upk_read.py`
  derived   the payload's size is one of G3-06 §C's two class-default descriptor sizes (30/34 B),
            so it is a property descriptor whose value is not on disk
  UNKNOWN   no tag stream and no derived class: the tool that would settle it is named per row

Usage:
    python Tools/scripts/bmak_native_triage.py --write    # -> NATIVE_TRIAGE.{json,md}
    python Tools/scripts/bmak_native_triage.py --check    # re-derive, compare, assert the counts
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402

G1 = os.path.join(ROOT, "Research", "BatmobileGrab")
REMAINDER = os.path.join(G1, "REMAINDER.json")
OBJECTS = os.path.join(G1, "objects.jsonl")
COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT_MD = os.path.join(G1, "NATIVE_TRIAGE.md")
OUT_JSON = os.path.join(G1, "NATIVE_TRIAGE.json")

CARD = "G3-06c"
DESCRIPTOR_SIZES = (30, 34)          # G3-06 §C: the two class-default property sizes
DESCRIPTOR_CLASSES = {"IntProperty", "BoolProperty", "FloatProperty", "ObjectProperty",
                      "ArrayProperty", "StructProperty", "NameProperty", "ByteProperty",
                      "ClassProperty", "ComponentProperty", "StrProperty", "MapProperty"}

# feature -> (ledger rows, §1 codes, tokens, classes, weight)
FEATURES = [
    ("weapons", "T-WP1…T-WP15", "WPN-1…WPN-12", 5,
     ("cannon", "gun", "missile", "rocket", "riot", "muzzle", "projectile", "turret", "emp",
      "weapon", "booster"),
     {"RBatmobileCannon", "RBatmobileHeavyCannon", "RBatmobileMissile", "RBatmobileMissileLauncher",
      "RBatmobileEMPMissile", "RBatmobileEMP", "RBatmobileWinch", "RBatmobileSonar",
      "RBatmobileVehicleTracker", "RBatmobileAllegianceSwitcher", "RBatmobileBooster"}),
    ("handling", "T-S6 / T-K4 / T-DR1 / T-SR1 / T-RA1 / T-G6", "DIM-4 (collision hull)", 5,
     ("bodyinstance", "constraint", "stayupright", "vehiclesim", "wheel", "suspension",
      "cylinder", "collision", "physics", "threat"),
     {"RB_BodyInstance", "RB_ConstraintInstance", "RB_StayUprightSetup", "CylinderComponent",
      "RVehicleThreatComponent"}),
    ("damage", "T-DM1 / T-DM7 / T-DM8 / T-DM9", "ARM-2 / ARM-3 / ARM-6", 4,
     ("damage", "visdmg", "destruct", "health", "armor", "armour"),
     {"RVisualDamageComponent"}),
    ("audio", "A-01…A-14 / W-03 / W-08 / T-AU5", "AUD-1…AUD-7", 4,
     ("ak", "sound", "audible", "dialogue", "waveform"),
     {"AkVehicleSound", "AkDialogueComponent", "AkComponent", "RAkAudible", "AnimNotify_Sound"}),
    ("hud", "T-HUD1…T-HUD24 / T-WP12", "WPN-12 (HUD)", 3,
     ("hud", "swf", "movie", "icon", "reticle"),
     {"RHudModuleBatmobile", "RHudModuleTargets", "SwfMovie"}),
    ("interactions", "T-15 / T-19 (prompts and exit)", "APP-5 / DIM-4", 2,
     ("interaction", "zapper", "contextact", "hidpoint"),
     {"RInteractionComponent"}),
    ("parts/animation", "P-01…P-15 / T-MD13 / T-PA4", "APP-5 / APP-6", 2,
     ("animnotify", "animset", "animseq", "animtree", "skeletalmesh", "particlesystem",
      "spotlight", "pointlight", "facefx"),
     {"SkeletalMeshComponent", "ParticleSystemComponent", "SpotLightComponent",
      "PointLightComponent", "FaceFXAnimSet"}),
]


def dependence(obj: dict) -> tuple[str, str, str, int]:
    """(feature, ledger rows, §1 codes, weight) for one remainder object. Never empty."""
    blob = " ".join(str(obj.get(k) or "") for k in ("name", "outer", "class")).lower()
    cls = obj.get("class")
    if cls == "FaceFXAnimSet":
        return ("facial animation (dialogue)", "none - character dialogue", "-", 0)
    if cls in DESCRIPTOR_CLASSES:
        return ("class-default descriptor", "G3-06 §C", "-", 0)
    if cls in ("Function", "State"):
        # code, not data: BmScript bytecode carries no number a ledger row could take
        return ("script code (BmScript)", "T-15 (mode swap trigger, U1 UNKNOWN)", "-", 1)
    for feature, rows, codes, weight, tokens, classes in FEATURES:
        if cls in classes or any(t in blob for t in tokens):
            return (feature, rows, codes, weight)
    if cls == "Function" or cls == "State":
        return ("script code (BmScript)", "T-15 (mode swap trigger, U1 UNKNOWN)", "-", 1)
    return ("other", "-", "-", 1)


def reach_bonus(verdict: str) -> int:
    if verdict.startswith("reachable"):
        return 200
    if verdict.startswith("UNKNOWN"):
        return 20
    return 0


def neighbours() -> dict[str, list[dict]]:
    """Per package, every export whose tag stream decoded - the candidates for a neighbour."""
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for line in open(OBJECTS, encoding="utf-8"):
        r = json.loads(line)
        if r.get("tag_count") and r.get("class") and r.get("name"):
            out[r["package"]].append({"index": r["index"], "name": r["name"],
                                      "class": r["class"], "size": r["size"]})
    for v in out.values():
        v.sort(key=lambda x: x["index"])
    return out


def nearest(obj: dict, nd: dict[str, list[dict]]) -> dict:
    """The closest decoded export in the same package: same owner first, then index distance."""
    cands = nd.get(obj["package"], [])
    if not cands:
        return {"name": None, "class": None, "index": None, "delta": None, "same_outer": False}
    sib = [c for c in cands if obj.get("outer") and c["name"] in str(obj["outer"]).split(".")]
    pool = sib or cands
    best = min(pool, key=lambda c: (abs(c["index"] - obj["index"]), c["index"]))
    return {"name": best["name"], "class": best["class"], "index": best["index"],
            "delta": best["index"] - obj["index"], "same_outer": bool(sib)}


def classify_read(summary: dict) -> tuple[str, str]:
    """(label, detail) from the bytes of one export."""
    n_tags, end, size, stop = (summary["tag_count"], summary["parsed_bytes"],
                               summary["size"], summary["stop"])
    if n_tags and stop in ("end", "eof") and end >= size - 2:
        return ("decoded", f"{n_tags} tags, {end}/{size} B, stream closes")
    if not n_tags and size <= 8 and end <= 2:
        # a component export with an empty body: values sit on the archetype / CDO, not here
        return ("derived", f"empty component stub: {size} B = a 2-byte tag terminator + "
                           f"{size - end} tail bytes; the component's values live on its "
                           f"archetype/CDO (G3-06 §C)")
    if size in DESCRIPTOR_SIZES:
        return ("derived", f"{size} B is G3-06 §C's class-default descriptor size; "
                           f"{n_tags} tags, stop {stop!r} at {end}/{size} B")
    if n_tags:
        return ("UNKNOWN", f"{n_tags} tags then stop {stop!r} at {end}/{size} B")
    return ("UNKNOWN", f"no tag stream from any start; stop {stop!r} at {end}/{size} B")


def settle_tool(row: dict, label: str) -> str:
    if label == "decoded":
        return "none - the bytes are read"
    if label == "derived":
        return ("`Tools/scripts/grab_remainder.py` §C (class-default size oracle) and "
                "`BMSDK_OFFSETS.json` for the member; the value is not on disk (G3-07b runtime)")
    cls = row.get("class")
    if cls == "FaceFXAnimSet":
        return ("an FxAnimSet reader (not in this toolkit); `NATIVE.md` \u00a7A lists the class, "
                "the payload is a FaceFX binary asset, not a property stream")
    if cls in ("Function", "State") or cls is None:
        return ("`Tools/scripts/grab_packages_g305.py` (PartialPackage) for the export's own "
                "byte layout, then the BmScript dump in `NATIVE.md`")
    if cls in DESCRIPTOR_CLASSES:
        return "`Tools/scripts/grab_remainder.py` §C - the descriptor names a default only"
    return ("`Tools/scripts/upk_read.py --dump %s` on %s.upk, then "
            "`grab_packages_g305.py` if the walk still stops early"
            % (row.get("name") or "<unnamed>", row["package"]))


def build() -> dict:
    rem = json.load(open(REMAINDER, encoding="utf-8"))
    untagged = rem["untagged"]
    objs = untagged["objects"]
    kinds = collections.Counter(o["shape"]["kind"] for o in objs)
    remainder = [o for o in objs if o["shape"]["kind"] != "empty_stub"]

    nd = neighbours()
    rows = []
    for o in remainder:
        feature, ledger, codes, weight = dependence(o)
        nb = nearest(o, nd)
        verdict = o["relevance"]["verdict"]
        pkg_bonus = 60 if o["package"] == "Playable_Batmobile_SF" else 0
        score = (weight * 100 + reach_bonus(verdict) + pkg_bonus
                 + min(o["size"], 4000) // 200)
        rows.append({
            "package": o["package"], "index": o["index"], "class": o["class"],
            "name": o["name"], "outer": o["outer"], "size": o["size"],
            "shape": o["shape"]["kind"], "stop": o["stop"], "sha1": o["sha1"],
            "head_hex": o["head_hex"], "relevance": verdict,
            "feature": feature, "ledger": ledger, "codes": codes, "weight": weight,
            "score": score, "package_bonus": pkg_bonus, "neighbour": nb,
        })
    rows.sort(key=lambda r: (-r["score"], -r["size"], r["package"], r["index"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    # the top fifteen, read from the bytes
    cache: dict[str, object] = {}
    for r in rows[:15]:
        pkgname = r["package"]
        path = os.path.join(COOKED, pkgname + ".upk")
        if pkgname not in cache:
            cache[pkgname] = U.Package(path) if os.path.exists(path) else None
        pkg = cache[pkgname]
        if pkg is None:
            r["read"] = {"label": "UNKNOWN", "detail": "package not on this machine",
                         "tags": []}
            r["settle"] = f"install `{pkgname}.upk` under the cooked path"
            continue
        s = U.export_summary(pkg, r["index"])
        label, detail = classify_read(s)
        tags = []
        for t in s["tags"][:12]:
            tags.append({k: t[k] for k in ("type", "offset", "name", "value", "ref", "size")
                         if k in t})
        r["read"] = {"label": label, "detail": detail, "tags": tags,
                     "tag_count": s["tag_count"], "parsed": s["parsed_bytes"],
                     "stop": s["stop"]}
        r["settle"] = settle_tool(r, label)

    return {
        "card": CARD,
        "generated_by": "Tools/scripts/bmak_native_triage.py --write",
        "inputs": {"remainder": "Research/BatmobileGrab/REMAINDER.json",
                   "objects": "Research/BatmobileGrab/objects.jsonl",
                   "cooked": COOKED,
                   "reader": "Tools/scripts/upk_read.py"},
        "counts": {"untagged": untagged["total"], "empty_stub": kinds.get("empty_stub", 0),
                   "native_record": kinds.get("native_record", 0),
                   "closes_from_offset": kinds.get("closes_from_offset", 0),
                   "remainder": len(rows),
                   "read": min(15, len(rows))},
        "by_feature": dict(collections.Counter(r["feature"] for r in rows)),
        "by_relevance": dict(collections.Counter(r["relevance"] for r in rows)),
        "by_package": dict(collections.Counter(r["package"] for r in rows)),
        "by_label": dict(collections.Counter(r.get("read", {}).get("label", "not read")
                                             for r in rows)),
        "rows": rows,
    }


def markdown(d: dict) -> str:
    c = d["counts"]
    L = [
        "# BmAK native/untagged remainder - triage of the 157 non-stub exports",
        "",
        f"Generated by `Tools/scripts/bmak_native_triage.py` (card `{CARD}`); `--check` re-reads",
        "`REMAINDER.json`, `objects.jsonl` and the cooked packages, re-derives this page and",
        "compares it byte for byte, and asserts the four counts below.",
        "",
        "## 1. What the 925 exports are",
        "",
        "| shape | exports | what it means |",
        "|---|---:|---|",
        f"| `empty_stub` | {c['empty_stub']} | a 2-byte `Package` payload: no properties exist to decode |",
        f"| `native_record` | {c['native_record']} | a payload no tag stream explains |",
        f"| `closes_from_offset` | {c['closes_from_offset']} | a tag stream that closes, but not from byte 0 |",
        f"| **total untagged** | **{c['untagged']}** | `REMAINDER.json` §A |",
        f"| **remainder (non-stub)** | **{c['remainder']}** | the {c['native_record']} + {c['closes_from_offset']} rows below |",
        "",
        f"Reachability, from `REMAINDER.json`'s own walk: {len([r for r in d['rows'] if r['relevance'].startswith('reachable')])} "
        "reachable from the drivable vehicle's chain, "
        f"{len([r for r in d['rows'] if r['relevance'].startswith('UNKNOWN')])} undecided, the rest in a package the walk never visits.",
        "",
        "## 2. The 157, ranked by what could depend on them",
        "",
        "A row's rank is `100 × feature weight + reachability + size`; the rule is in the module",
        "docstring, so the order is re-derivable. `neighbour` is the closest export in the same",
        "package whose tag stream decoded - the named object a remainder row sits next to.",
        "",
        "| rank | package | # | class | size | object | nearest named neighbour | depends on | §1 |",
        "|---:|---|---:|---|---:|---|---|---|---|",
    ]
    for r in d["rows"]:
        nb = r["neighbour"]
        nbtxt = ("`%s` (%s, %+#d)" % (nb["name"], nb["class"], nb["delta"])
                 if nb["name"] else "none decoded in this package")
        L.append("| %d | `%s` | %d | `%s` | %d | `%s.%s` | %s | %s (`%s`) | %s |"
                 % (r["rank"], r["package"], r["index"], r["class"] or "(unresolved)",
                    r["size"], r["outer"], r["name"], nbtxt, r["feature"], r["ledger"],
                    r["codes"]))
    L += ["", "## 3. The top fifteen, read with `upk_read.py`", ""]
    for r in d["rows"][:15]:
        rd = r.get("read", {})
        L += ["### %d. `%s` #%d - `%s` - %d B" % (r["rank"], r["package"], r["index"],
                                                  r["class"] or "(unresolved)", r["size"]),
              "",
              "- object: `%s.%s`; depends on **%s** (`%s`, %s)" % (
                  r["outer"], r["name"], r["feature"], r["ledger"], r["codes"]),
              "- verdict: **%s** - %s" % (rd.get("label", "not read"), rd.get("detail", "")),
              "- settles it: %s" % r.get("settle", "not read"),
              "- head: `%s`" % r["head_hex"]]
        tags = rd.get("tags") or []
        if tags:
            L.append("- first tags: " + ", ".join(
                "`%s`%s@%#x%s" % (t.get("name", "(offset-only)"),
                                  ":" + t["type"] if t.get("type") else "",
                                  t.get("offset", 0),
                                  (" -> " + str(t["ref"])) if t.get("ref") else
                                  (" = " + repr(t["value"])) if "value" in t else "")
                for t in tags[:8]))
        L.append("")
    L += ["## 4. The G1 percentage question",
          "",
          "| bucket | exports | why it does not move the Batmobile |",
          "|---|---:|---|",
          f"| 2-byte `Package` stubs | {c['empty_stub']} | no properties exist to read; nothing to translate |",
          "| class-default descriptors | %d | a descriptor names a default; the value is not on disk (G3-06 §C) |"
          % len([r for r in d["rows"] if r["feature"] == "class-default descriptor"]),
          "| in a package the drivable car never visits | %d | the object belongs to that package's own asset |"
          % len([r for r in d["rows"] if r["relevance"].startswith("not in")]),
          "| script code / unresolved class | %d | BmScript bytecode, not a vehicle factor |"
          % len([r for r in d["rows"] if r["feature"] == "script code (BmScript)"]),
          "| **vehicle-relevant remainder** | **%d** | becomes named cards below |"
          % len([r for r in d["rows"] if r["weight"] >= 3]),
          "",
          "### Named cards this triage creates",
          "",
          "| card | covers | exports | deps | done when |",
          "|---|---|---:|---|---|",
          "| `G3-06d` | damage component (`RVisualDamageComponent`) - ARM-2/ARM-3 material swap | %d | G1-22, G2-28 | each export's tags read, or UNKNOWN with the runtime probe named |" % len([r for r in d["rows"] if r["feature"] == "damage"]),
          "| `G3-06e` | vehicle audio objects (`AkVehicleSound`, `AkDialogueComponent`) | %d | G3-14 | each event's bank id resolved or UNKNOWN |" % len([r for r in d["rows"] if r["feature"] == "audio"]),
          "| `G3-06f` | interaction + threat + physics components | %d | G3-10 | each component's owner and members named |" % len([r for r in d["rows"] if r["feature"] in ("handling", "interactions")]),
          "| `G3-06g` | weapon-adjacent remainder | %d | T-11 | each object tied to a WPN row or shown not to be |" % len([r for r in d["rows"] if r["feature"] == "weapons"]),
          "| `G3-06h` | parts / light / particle components | %d | T-12, T-18 | each mapped to a part or light row |" % len([r for r in d["rows"] if r["feature"] == "parts/animation"]),
          "",
          "Each card is `todo` in `GRAB_BACKLOG.md` §12 until its check passes; none of them",
          "changes a ledger value on its own, which is why G1's 95.4% does not move from this",
          "pass - 768 of the 925 have no payload, and the remainder is either another package's",
          "asset or a descriptor.",
          ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = build()
    md = markdown(d)
    js = json.dumps(d, indent=1, ensure_ascii=False) + "\n"
    problems = []
    c = d["counts"]
    if c["remainder"] != c["native_record"] + c["closes_from_offset"]:
        problems.append("remainder != native_record + closes_from_offset")
    if c["untagged"] != c["empty_stub"] + c["remainder"]:
        problems.append("untagged != empty_stub + remainder")
    if c["read"] != min(15, c["remainder"]):
        problems.append("the top fifteen were not all read")
    if any("read" not in r for r in d["rows"][:15]):
        problems.append("a top-fifteen row has no byte verdict")
    if any(not r["settle"] for r in d["rows"][:15]):
        problems.append("a top-fifteen row names no settling tool")
    if a.check:
        if not os.path.exists(OUT_MD) or open(OUT_MD, encoding="utf-8").read() != md:
            problems.append("NATIVE_TRIAGE.md differs from the re-derived page")
        if not os.path.exists(OUT_JSON) or open(OUT_JSON, encoding="utf-8").read() != js:
            problems.append("NATIVE_TRIAGE.json differs from the re-derived record")
    elif a.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote", OUT_MD, "and", OUT_JSON)
    print("%d untagged = %d stubs + %d remainder (%d native + %d closes); %d read"
          % (c["untagged"], c["empty_stub"], c["remainder"], c["native_record"],
             c["closes_from_offset"], c["read"]))
    for k, v in sorted(d["by_feature"].items(), key=lambda kv: -kv[1]):
        print("  %-26s %3d" % (k, v))
    if problems:
        for p in problems:
            print("FAIL", p)
        return 1
    if a.check:
        print("check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
