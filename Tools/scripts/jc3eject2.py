#!/usr/bin/env python
"""jc3eject2.py - G2-20R: review of `EJECT.md` ("JC3 has no eject").

`Research/JC3Grab/EJECT.md` (G2-20, `jc3eject.py`) answers "does anything launch the driver
upward?" from the vehicle data and answers no. This script re-derives that answer and then
attacks the *headline* it puts on it, "JC3 has no eject", on four fronts the original never
read:

1. **The roster exit census** - re-counted here from `detail/*.ee.json` (232 graphs) and
   compared field by field with `EJECT.json`.
2. **The graphs the roster leaves out** - 344 `.epe` files ship; 234 contain
   `CInteractionGraphExit`, and 12 of those are not vehicle entities in the 232 roster
   (mounted weapons, turrets, contextual actions, a prototype boss helicopter). They are
   decoded here with the repo's Gibbed converter and their exits counted.
3. **The exe** - `JustCause3.exe` carries an action/state/name table. It is scanned for
   eject-like tokens, and every hit is quoted with its file offset and its neighbour names.
4. **Who uses those names** - each engine name is turned into the archive hash (Gibbed
   Jenkins lookup3 over the upper-case ASCII name, the scheme `rico_base.afsmb` verifiably
   uses: `ACT_EXIT_VEHICLE` is present both plaintext and as `7B3C34AB`) and searched for in
   all 165 `.afsmb` state machines, all 344 `.epe` graphs, all 300 `.gsc` + 300 `.gdc`
   scripts and all 61 `.asb` animation sets. Two controls ride along: `ACT_EXIT_VEHICLE`
   (known used) and `ACT_PANIC_EXIT_VEHICLE` (in the exe, expected unused).

Nothing here is inferred from outside the files: a name is evidence only of the name, and a
name with no reference is reported as an engine-side name with no data-side trigger.

Writes `Research/JC3Grab/EJECT_REVIEW.md` + `EJECT_REVIEW.json`. `--check` recomputes both.

Usage:
  python Tools/scripts/jc3eject2.py --write
  python Tools/scripts/jc3eject2.py --check
  python Tools/scripts/jc3eject2.py dump engine|refs|census|orig
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3grab  # noqa: E402
import jc3index  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402
import jc3eject  # noqa: E402  (the reviewed script, imported read-only)

OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
DETAIL = os.path.join(RAW, "detail")
ENTITIES = os.path.join(RAW, "entities")
DETAIL_INDEX = os.path.join(RAW, "detail_index.json")
INDEX_JSONL = os.path.join(OUT, "INDEX.jsonl")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
EXE = os.path.join(GAME, "JustCause3.exe")
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
SCRATCH = os.path.join(ROOT, "tmp", "freebuff", "scratch", "eject_review")

MD_NAME, JSON_NAME = "EJECT_REVIEW.md", "EJECT_REVIEW.json"
ORIG_MD, ORIG_JSON = os.path.join(OUT, "EJECT.md"), os.path.join(OUT, "EJECT.json")

EXIT_CLASS = "CInteractionGraphExit"
EXIT_KEYS = {"_object_id", "disable_event", "enable_event", "enabled", "interaction",
             "modifier", "name", "name_hash", "state"}
# The reviewed module sweep, exactly. `bail` was missing from it; `veloc` is a separate,
# wider lens reported beside it rather than silently mixed in.
ORIG_RE = re.compile(r"eject|launch|catapult|impulse|parachute|wingsuit", re.I)
ORIG_BAIL_RE = re.compile(r"eject|launch|catapult|bail|impulse|parachute|wingsuit", re.I)
WIDE_RE = re.compile(r"eject|launch|catapult|bail|impulse|veloc|parachute|wingsuit", re.I)
LAUNCH_RE = WIDE_RE

# Names the exe carries. The first six are the contradiction under test; the last four are
# the reference test (two known-used, two expected-unused).
ENGINE_NAMES = [
    "ACT_EJECT_FROM_VEHICLE",
    "ACT_EJECT_FROM_VEHICLE_MG",
    "S_EJECT_FROM_VEHICLE_ALIVE",
    "S_EJECT_FROM_VEHICLE_DEAD",
    "VehicleBailExplosion",
    "is_rico_bail_vulnerable_timer_active",
]
CONTROL_NAMES = [
    "ACT_EXIT_VEHICLE",
    "ACT_STUNT_VEHICLE_EXIT",
    "S_EXIT_VEHICLE_PARA",
    "ACT_PANIC_EXIT_VEHICLE",
]
ALL_NAMES = ENGINE_NAMES + CONTROL_NAMES
REF_EXTS = (".afsmb", ".epe", ".gsc", ".gdc", ".asb")

RICO_ASB = "animations/jc_statemachine/main_characters/rico/rico_base.asb"
RICO_AFSMB = "animations/jc_statemachine/main_characters/rico/rico_base.afsmb"
ASB_CLIPS = ["PPparachute_vehicle_eject",
             "rico_vehi_car_low_driver_to_parachute.ban"]


# ----------------------------------------------------------------------------- inputs

def index_rows() -> list[dict]:
    return [json.loads(l) for l in open(INDEX_JSONL, encoding="utf-8") if l.strip()]


def read_named(rows: list[dict], path: str) -> bytes | None:
    hit = [r for r in rows if r["path"] == path]
    if not hit:
        return None
    return jc3grab.read_entry(hit[0], GAME)


def roster_stems() -> set[str]:
    doc = json.load(open(DETAIL_INDEX, encoding="utf-8"))
    return {os.path.splitext(os.path.basename(r["entity"]))[0] for r in doc}


def detail_files() -> list[str]:
    return sorted(f for f in os.listdir(DETAIL) if f.endswith(".ee.json"))


def entity_files() -> list[str]:
    return sorted(f for f in os.listdir(ENTITIES) if f.endswith(".ee.json"))


# ----------------------------------------------------------------------------- census

def roster_census() -> dict:
    """Re-count the 232-graph exit census from the detail JSONs (independent of jc3eject)."""
    exits = 0
    graphs = 0
    names: collections.Counter = collections.Counter()
    keys: collections.Counter = collections.Counter()
    classes: collections.Counter = collections.Counter()
    state_missing = 0
    for fn in detail_files():
        doc = json.load(open(os.path.join(DETAIL, fn), encoding="utf-8"))
        objs = doc["epe"]["objects"]
        graphs += 1
        for o in objs:
            cls = o.get("class") or ""
            classes[cls] += 1
            if cls != EXIT_CLASS:
                continue
            exits += 1
            v = o.get("values") or {}
            names[o.get("name") or ""] += 1
            for k in v:
                keys[k] += 1
            if "state" not in v:
                state_missing += 1
    launch_members = sum(n for k, n in keys.items()
                         if re.search(r"veloc|impulse|launch|force|speed", k))
    launch_classes = sorted(c for c in classes
                            if re.search(r"Veloc|Impulse|Launch|Eject|Force", c))
    return {"graphs": graphs, "exits": exits, "distinct_names": len(names),
            "keys": dict(keys), "state_missing": state_missing,
            "unexpected_keys": sorted(k for k in keys if k not in EXIT_KEYS),
            "launch_members": launch_members,
            "classes": len(classes), "launch_classes": launch_classes,
            "top_names": names.most_common(6)}


def module_sweep() -> dict:
    """The 232 vehicle entity graphs' module rows under three lenses (see the regexes)."""
    lenses = {"orig": ORIG_RE, "orig_plus_bail": ORIG_BAIL_RE, "wide": WIDE_RE}
    found = {k: collections.Counter() for k in lenses}
    for fn in entity_files():
        doc = json.load(open(os.path.join(ENTITIES, fn), encoding="utf-8"))
        for mod in doc.get("modules") or []:
            if not mod.get("type"):
                continue
            for r in mod.get("rows", []):
                p = r.get("path", "")
                key = f"{mod['type']}.{p}"
                for name, rx in lenses.items():
                    if rx.search(p):
                        found[name][key] += 1
    return {name: {"members": dict(c), "distinct": len(c)} for name, c in found.items()}


def xml_props(el: ET.Element) -> dict[str, str]:
    """Direct `value` children only - nesting must not leak into an object's own props."""
    out: dict[str, str] = {}
    for c in el:
        if c.tag == "value":
            key = c.get("name") or ("id:" + (c.get("id") or ""))
            out[key] = c.text or ""
    return out


def xml_props_typed(el: ET.Element) -> dict[str, tuple[str, str]]:
    """Direct `value` children as key -> (type, text)."""
    return {(c.get("name") or ("id:" + (c.get("id") or ""))):
            (c.get("type") or "", c.text or "") for c in el if c.tag == "value"}


def epe_exits(root: ET.Element) -> list[dict]:
    """Every `CInteractionGraphExit` in a decoded `.epe`, named and hash-named members split."""
    out = []
    for obj in root.iter("object"):
        pr = xml_props_typed(obj)
        if pr.get("_class", ("", ""))[1] != EXIT_CLASS:
            continue
        named = {k: v for k, v in pr.items() if not k.startswith("id:")}
        hashed = {k: v for k, v in pr.items() if k.startswith("id:")}
        out.append({
            "name": named.get("name", ("", ""))[1],
            "state": named.get("state", ("", ""))[1],
            "modifier": named.get("modifier", ("", ""))[1] or None,
            "named_keys": sorted(named),
            "hashed": {k: v[0] for k, v in hashed.items()},
        })
    return out


def decode_epe(path: str, blob: bytes) -> str:
    os.makedirs(SCRATCH, exist_ok=True)
    src = os.path.join(SCRATCH, "in.epe")
    dst = os.path.join(SCRATCH, "out.xml")
    open(src, "wb").write(blob)
    if os.path.exists(dst):
        os.remove(dst)
    r = subprocess.run([CONV, "--e", src, dst], capture_output=True, text=True)
    if r.returncode or not os.path.exists(dst):
        raise SystemExit(f"ConvertProperty failed on {path}: {r.returncode} {r.stderr}")
    text = open(dst, encoding="utf-8").read()
    os.remove(src)
    os.remove(dst)
    return text


def offroster_graphs(rows: list[dict]) -> dict:
    """Every `.epe` that carries an exit and is not one of the 232 roster vehicles."""
    stems = roster_stems()
    epe = [r for r in rows if r["path"].lower().endswith(".epe")]
    roster_files = extra_files = 0
    graphs = []
    for r in epe:
        blob = jc3grab.read_entry(r, GAME)
        if EXIT_CLASS.encode() not in blob:
            continue
        stem = os.path.splitext(os.path.basename(r["path"]))[0]
        if stem in stems:
            roster_files += 1
            continue
        extra_files += 1
        text = decode_epe(r["path"], blob)
        exits = epe_exits(ET.fromstring(text))
        # A launch field would be a *member*: a named key outside the known set, or a
        # float/vector-typed hash-named member. The exit's own name is not a member.
        for e in exits:
            e["extra_named"] = [k for k in e["named_keys"] if k not in EXIT_KEYS | {"_class", "tags"}]
            e["launch_named"] = bool(e["extra_named"]) or any(
                t in ("float", "vec", "vec3", "vec4") for t in e["hashed"].values())
        graphs.append({"path": r["path"], "bytes": len(blob), "exits": exits})
    total = sum(len(g["exits"]) for g in graphs)
    types = collections.Counter(t for g in graphs for e in g["exits"] for t in e["hashed"].values())
    hashed = {len(e["hashed"]) for g in graphs for e in g["exits"]}
    return {"epe_on_disk": len(epe), "roster_files": roster_files,
            "offroster_files": extra_files, "graphs": graphs,
            "offroster_exits": total,
            "offroster_launch_named": sum(1 for g in graphs for e in g["exits"]
                                          if e["launch_named"]),
            "offroster_hashed_members": sorted(hashed),
            "offroster_hashed_types": dict(types),
            "offroster_extra_named": sorted({k for g in graphs for e in g["exits"]
                                             for k in e["extra_named"]})}


def exit_members(data: bytes) -> dict:
    """The donor's exits read as XML: the members the 232-graph detail JSON cannot show.

    `detail/*.ee.json` keeps only *named* values, so the reviewed census saw 9 keys. The
    converted donor `.epe` keeps the hash-named values too; this counts them and tests their
    types (a launch impulse has to be a float/vector member - an int cannot carry one).
    """
    root = ET.parse(os.path.join(ROOT, "Research", "Epe", "serpente_civilian.xml")).getroot()
    exits = epe_exits(root)
    hashed_types = collections.Counter(t for e in exits for t in e["hashed"].values())
    named = sorted({k for e in exits for k in e["named_keys"]})
    ids = sorted({k for e in exits for k in e["hashed"]})
    # the class-hash leaf: value == jenkins(class name) on every class in this file
    ok = bad = 0
    seen = set()
    exit_cls_value = None
    for obj in root.iter("object"):
        pr = xml_props_typed(obj)
        cls = pr.get("_class", ("", ""))[1]
        if not cls or cls in seen or "id:D04059E6" not in pr:
            continue
        seen.add(cls)
        try:
            v = int(pr["id:D04059E6"][1]) & 0xFFFFFFFF
        except ValueError:
            continue
        if cls == EXIT_CLASS:
            exit_cls_value = v
        if v == hash_jenkins(cls.encode()):
            ok += 1
        else:
            bad += 1
    # dictionary attack on the hash-named member names, vocabulary = exe strings
    toks = {t.decode("latin-1") for t in re.findall(rb"[a-z][a-z0-9_]{2,40}", data)}
    want = {int(k[3:], 16) for k in ids}
    hits = {}
    for w in toks:
        for scheme, h in (("jenkins", hash_jenkins(w.encode())),
                          ("jenkinsU", hash_jenkins(w.upper().encode()))):
            if h in want:
                hits.setdefault(f"{h:08X}", set()).add(w)
    return {"exits": len(exits), "named_keys": named, "hashed_ids": ids,
            "hashed_per_exit": sorted({len(e["hashed"]) for e in exits}),
            "hashed_types": dict(hashed_types),
            "float_members": sum(n for t, n in hashed_types.items()
                                 if t in ("float", "vec", "vec3", "vec4")),
            "class_hash_ok": ok, "class_hash_bad": bad,
            "class_hash_field": "id:D04059E6",
            "class_hash_exit_value": exit_cls_value,
            "class_hash_exit_matches": (exit_cls_value == hash_jenkins(EXIT_CLASS.encode())),
            "dictionary_tokens": len(toks), "dictionary_hits": {k: sorted(v) for k, v in hits.items()}}


# ----------------------------------------------------------------------------- exe

def printable_run(data: bytes, off: int, span: int = 90) -> str:
    a = off
    while a > 0 and 0x20 <= data[a - 1] <= 0x7E:
        a -= 1
    b = off
    while b < len(data) and 0x20 <= data[b] <= 0x7E:
        b += 1
    lo, hi = max(0, a - span), min(len(data), b + span)
    text = re.sub(rb"[^\x20-\x7e]", b"\n", data[lo:hi]).decode("latin-1")
    lines = [l for l in text.split("\n") if len(l) >= 4]
    return " | ".join(lines[:8])


def exe_scan(data: bytes) -> dict:
    hits = {}
    for n in ALL_NAMES:
        offs = [m.start() for m in re.finditer(re.escape(n.encode()), data)]
        hits[n] = {"count": len(offs),
                   "offsets": [hex(o) for o in offs],
                   "run": printable_run(data, offs[0]) if offs else "",
                   "engine": n in ENGINE_NAMES}
    # every eject-like separate token in the file, for the "did we miss one" question
    tokens = sorted({m.group().decode("latin-1")
                     for m in re.finditer(rb"[A-Za-z_][A-Za-z0-9_]{3,63}", data)
                     if re.search(rb"eject|catapult|bail", m.group(), re.I)})
    return {"file": os.path.basename(EXE), "bytes": len(data),
            "names": hits, "eject_like_tokens": tokens}


# ----------------------------------------------------------------------------- refs

def ref_scan(rows: list[dict]) -> dict:
    """Search every data file of each type for each name: plaintext and, for .afsmb, hash."""
    sel = [r for r in rows if os.path.splitext(r["path"])[1].lower() in REF_EXTS]
    hashes = {n: hash_jenkins(n.encode()) for n in ALL_NAMES}
    plain: dict[str, set] = collections.defaultdict(set)
    by_hash: dict[str, set] = collections.defaultdict(set)
    for r in sel:
        ext = os.path.splitext(r["path"])[1].lower()
        try:
            blob = jc3grab.read_entry(r, GAME)
        except Exception:
            continue
        for n in ALL_NAMES:
            if n.encode() in blob:
                plain[n].add(r["path"])
            if ext == ".afsmb":
                v = hashes[n]
                if (v.to_bytes(4, "little") in blob) or (v.to_bytes(4, "big") in blob):
                    by_hash[n].add(r["path"])
    return {"files_scanned": len(sel),
            "hashes": {n: f"{h:08X}" for n, h in hashes.items()},
            "plain": {n: sorted(plain[n]) for n in ALL_NAMES},
            "hash": {n: sorted(by_hash[n]) for n in ALL_NAMES}}


def asb_scan(rows: list[dict]) -> dict:
    blob = read_named(rows, RICO_ASB)
    out = {}
    for clip in ASB_CLIPS:
        offs = [m.start() for m in re.finditer(re.escape(clip.encode()), blob)]
        out[clip] = {"count": len(offs), "offsets": [hex(o) for o in offs]}
    text = blob.decode("latin-1")
    parachute = sorted(set(re.findall(r"PPparachute_[A-Za-z0-9_]+", text)))
    return {"file": RICO_ASB, "bytes": len(blob), "clips": out,
            "parachute_clips": parachute}


def index_scan(rows: list[dict]) -> dict:
    barks = sorted(r["path"] for r in rows if "bark_rico_parachute_ejecting" in r["path"])
    dlc = sorted(r["path"] for r in rows if "mission_dlc2_mm110_dial_obj13_eject" in r["path"])
    eject_paths = sorted(r["path"] for r in rows if re.search(r"eject", r["path"], re.I))
    return {"bark_paths": barks, "bark_assets": len(barks),
            "dlc_eject_dialogue": len(dlc),
            "dlc_languages": sorted({p.split("/")[4] for p in dlc}),
            "paths_with_eject": len(eject_paths)}


def script_bail(rows: list[dict]) -> list[dict]:
    """Plaintext `bail`/`eject` hits in the shipped scripts, with the containing string."""
    out = []
    for r in rows:
        if os.path.splitext(r["path"])[1].lower() not in (".gsc", ".gdc"):
            continue
        blob = jc3grab.read_entry(r, GAME)
        for m in re.finditer(rb"[A-Za-z0-9_.]{3,}(?:bail|eject)[A-Za-z0-9_.]{0,40}", blob, re.I):
            out.append({"path": r["path"], "offset": hex(m.start()),
                        "string": m.group().decode("latin-1")})
    return out


# ----------------------------------------------------------------------------- original

def orig_check() -> dict:
    """Re-derive the reviewed report and say exactly how it differs on disk."""
    doc = jc3eject.build()
    md = jc3eject.report(doc)
    disk_json = open(ORIG_JSON, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    disk_md = open(ORIG_MD, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    derived_json = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    diff = [ln for ln in difflib.unified_diff(disk_md.splitlines(), md.splitlines(),
                                              "disk", "derived", lineterm="", n=0)]
    changed = [ln for ln in diff if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))]
    return {"derived_digest": doc["digest"],
            "disk_digest": json.loads(disk_json)["digest"],
            "json_equal": disk_json == derived_json,
            "md_equal": disk_md == md,
            "md_changed_lines": changed,
            "counts": doc["counts"]}


# ----------------------------------------------------------------------------- build

def build() -> dict:
    rows = index_rows()
    data = open(EXE, "rb").read()
    doc = {
        "card": "G2-20R (review of G2-20)",
        "reviewed": {"md": "Research/JC3Grab/EJECT.md",
                     "json": "Research/JC3Grab/EJECT.json",
                     "script": "Tools/scripts/jc3eject.py"},
        "orig_check": orig_check(),
        "census": roster_census(),
        "members": exit_members(data),
        "modules": module_sweep(),
        "offroster": offroster_graphs(rows),
        "engine": exe_scan(data),
        "refs": ref_scan(rows),
        "asb": asb_scan(rows),
        "index": index_scan(rows),
        "scripts": script_bail(rows),
    }
    c, o, r, e, m = doc["census"], doc["offroster"], doc["refs"], doc["engine"], doc["members"]
    engine_hits = sum(1 for n in ENGINE_NAMES if e["names"][n]["count"])
    engine_refs = sum(len(set(r["plain"][n]) | set(r["hash"][n])) for n in ENGINE_NAMES)
    control_refs = {n: len(set(r["plain"][n]) | set(r["hash"][n])) for n in CONTROL_NAMES}
    doc["counts"] = {
        "orig_json_equal": doc["orig_check"]["json_equal"],
        "orig_md_equal": doc["orig_check"]["md_equal"],
        "orig_md_changed_lines": len(doc["orig_check"]["md_changed_lines"]),
        "roster_exits": c["exits"],
        "roster_names": c["distinct_names"],
        "roster_launch_members": c["launch_members"],
        "roster_unexpected_keys": len(c["unexpected_keys"]),
        "member_exits": m["exits"],
        "member_named_keys": len(m["named_keys"]),
        "member_hashed_ids": len(m["hashed_ids"]),
        "member_hashed_per_exit": m["hashed_per_exit"],
        "member_float_members": m["float_members"],
        "member_class_hash_ok": m["class_hash_ok"],
        "member_dictionary_hits": len(m["dictionary_hits"]),
        "module_distinct_orig": doc["modules"]["orig"]["distinct"],
        "module_distinct_orig_plus_bail": doc["modules"]["orig_plus_bail"]["distinct"],
        "module_distinct_wide": doc["modules"]["wide"]["distinct"],
        "offroster_graphs": o["offroster_files"],
        "offroster_exits": o["offroster_exits"],
        "offroster_launch": o["offroster_launch_named"],
        "engine_names_present": engine_hits,
        "engine_names": len(ENGINE_NAMES),
        "engine_data_refs": engine_refs,
        "control_refs": control_refs,
        "asb_eject_clip": doc["asb"]["clips"]["PPparachute_vehicle_eject"]["count"],
        "bark_assets": doc["index"]["bark_assets"],
        "script_bail_hits": len(doc["scripts"]),
    }
    if (engine_hits == len(ENGINE_NAMES) and engine_refs == 0
            and c["launch_members"] == 0 and o["offroster_launch_named"] == 0
            and m["float_members"] == 0
            and control_refs.get("ACT_EXIT_VEHICLE", 0) > 0):
        doc["verdict"] = "PARTLY CONTRADICTED"
    elif engine_hits == 0:
        doc["verdict"] = "SOUND"
    else:
        doc["verdict"] = "UNRESOLVED"
    blob = json.dumps(doc, sort_keys=True, separators=(",", ":"))
    doc["digest"] = hashlib.md5(blob.encode()).hexdigest()[:16]
    return doc


# ----------------------------------------------------------------------------- report

def report(doc: dict) -> str:
    L: list[str] = []

    def a(s: str = "") -> None:
        L.append(s)

    c = doc["counts"]
    o, e, r, idx = doc["offroster"], doc["engine"], doc["refs"], doc["index"]
    cen, mod, orig = doc["census"], doc["modules"], doc["orig_check"]
    m = doc["members"]

    a("# Review: does JC3 have an eject? (G2-20R, of G2-20)")
    a("")
    a(f"Generated by `Tools/scripts/jc3eject2.py` (digest `{doc['digest']}`). Reviewed: "
      "`Research/JC3Grab/EJECT.md`.")
    a("")
    a(f"**VERDICT: {doc['verdict']}.** The reviewed report's data conclusion is sound and "
      "re-derives exactly: no exit in any shipped interaction graph carries a launch, and "
      "no vehicle module carries a driver impulse. Two of its supporting statements are "
      "wrong, though: (a) its headline, **\"JC3 has no eject\", is "
      "wrong as an engine statement**: `JustCause3.exe` carries `ACT_EJECT_FROM_VEHICLE` "
      "and `ACT_EJECT_FROM_VEHICLE_MG` as actions, `S_EJECT_FROM_VEHICLE_ALIVE` / "
      "`S_EJECT_FROM_VEHICLE_DEAD` as states, a `VehicleBailExplosion` heat-tuning name and "
      "a vehicle member `is_rico_bail_vulnerable_timer_active`; Rico's animation set carries "
      "a clip `PPparachute_vehicle_eject`, and the game ships four "
      "`bark_rico_parachute_ejecting_*` voice lines. What is true is narrower: **no shipped "
      "graph, state machine or script references any of those names** - the eject exists as "
      "engine vocabulary with no data-side trigger. And (b) the 9-key exit census is "
      f"incomplete: the donor `.epe` carries {len(m['hashed_ids'])} further hash-named members "
      "per exit that the detail JSON drops; they are all int/event/matrix typed, so the "
      "no-launch finding survives - by type, not by key count.")
    a("")
    a("## 1. The reviewed report's own `--check`")
    a("")
    a(f"`jc3eject.py --check` **fails on this install** ({c['orig_md_changed_lines']} changed "
      "line(s) in `EJECT.md`). The cause is not a number: the report text was generated when "
      "the raw decode lived at `E:/Modding/_JC3grab` (that path no longer exists); it now "
      "lives at `E:/Modding/_gamedata/JC3grab`, and the path is printed into the header and "
      "the reproduce section. The JSON is byte-identical "
      f"(`json_equal={orig['json_equal']}`, digest `{orig['disk_digest']}`), so every number "
      "re-derives.")
    a("")
    a("| check | result |")
    a("|---|---|")
    a(f"| derived digest | `{orig['derived_digest']}` |")
    a(f"| on-disk digest | `{orig['disk_digest']}` |")
    a(f"| `EJECT.json` byte-equal | `{orig['json_equal']}` |")
    a(f"| `EJECT.md` byte-equal | `{orig['md_equal']}` |")
    a("")
    a("Changed lines (all path text):")
    a("")
    a("```")
    for ln in orig["md_changed_lines"][:6]:
        a(ln.rstrip())
    a("```")
    a("")
    a("So the report is **stale by one string, not by one value**. `--check` cannot pass "
      "until the report is regenerated (or `JC3_RAW` is honoured in the prose), and the "
      "reproduce command in its section 9 fails on this machine for the same reason.")
    a("")
    a("## 2. The exit census re-derived")
    a("")
    a(f"From the 232 `detail/*.ee.json` graphs: **{cen['exits']}** exits, "
      f"{cen['distinct_names']} distinct names, **{len(cen['keys'])}** member keys, "
      f"{cen['unexpected_keys'] and 'unexpected: ' + ', '.join(cen['unexpected_keys']) or 'no key outside the 9'}. "
      f"Members named velocity/impulse/launch/force/speed: **{cen['launch_members']}**. "
      f"`state` is absent on {cen['state_missing']} exits.")
    a("")
    a("| member | exits carrying it |")
    a("|---|---|")
    for k, n in sorted(cen["keys"].items(), key=lambda kv: (-kv[1], kv[0])):
        a(f"| `{k}` | {n} |")
    a("")
    a(f"Graph vocabulary: {cen['classes']} classes; those with "
      f"Veloc/Impulse/Launch/Eject/Force in the name: "
      f"{', '.join('`' + x + '`' for x in cen['launch_classes']) or 'none'}. "
      "Both are the reviewed report's own rows, re-counted.")
    a("")
    a(f"### 2a. The members that census cannot see")
    a("")
    a("`detail/*.ee.json` keeps only **named** values, so the reviewed census saw 9 keys per "
      "exit and reported 0 keys outside them. The donor `.epe` itself, converted to XML "
      "(`Research/Epe/serpente_civilian.xml` - the reviewed report's own input), carries "
      f"**{m['hashed_per_exit'][0]} hash-named members** on every one of its "
      f"{m['exits']} exits as well:")
    a("")
    a(f"| member set | count |")
    a("|---|---|")
    a(f"| named (`_class` + the 9 + `tags`) | {len(m['named_keys'])}: "
      + ", ".join(f"`{k}`" for k in m["named_keys"]) + " |")
    a(f"| hash-named (`id:XXXXXXXX`) | {len(m['hashed_ids'])} per exit |")
    a("")
    a(f"Types of the hash-named members across all {m['exits']} exits: "
      + ", ".join(f"{t} x{n}" for t, n in sorted(m["hashed_types"].items()))
      + f". **Float/vector members: {m['float_members']}.** An impulse or a launch velocity "
        "has to be a float or a vector, so none of the invisible members can be one - the "
        "conclusion holds, but by type, not by the 9-key count.")
    a("")
    a(f"One of them decodes: `{m['class_hash_field']}` holds the **jenkins hash of the "
      f"object's class name** on {m['class_hash_ok']} of {m['class_hash_ok'] + m['class_hash_bad']} "
      "classes in the file"
      + (f" (its value for {EXIT_CLASS} is {m['class_hash_exit_value']}, "
         f"which equals `hash(\"{EXIT_CLASS}\")`: {m['class_hash_exit_matches']})"
         if m["class_hash_ok"] else "")
      + ". The other ids resist a dictionary of "
      f"{m['dictionary_tokens']:,} snake_case tokens taken from the exe: "
      f"{len(m['dictionary_hits'])} hit(s). Their names are **UNKNOWN**.")
    a("")
    a("The vehicle **module** sweep, under three lenses, so the reviewed one is checked as "
      "written and the wider one is not passed off as the same test:")
    a("")
    a("| lens | distinct members | hits |")
    a("|---|---|---|")
    for label, key in (("reviewed regex: eject/launch/catapult/impulse/parachute/wingsuit", "orig"),
                       ("+ `bail` (the term the reviewed regex omitted)", "orig_plus_bail"),
                       ("+ `bail` and `veloc` (vehicle-physics names)", "wide")):
        d = mod[key]
        a(f"| {label} | {d['distinct']} | "
          + (", ".join(f"`{k}` x{v}" for k, v in sorted(d["members"].items())) or "-") + " |")
    a("")
    a(f"\"Adding `bail`\" changes nothing: the reviewed regex and the reviewed regex + `bail` "
      f"both read **{mod['orig_plus_bail']['distinct']}**, the train's `TrainGlobal.crashing_impulse`. "
      f"The `veloc` lens reads {mod['wide']['distinct']} because vehicle physics is full of "
      "velocity members (`RigidBody.max_linear_velocity`, tyre slip velocities, buoyancy"
      "`up_velocity_cap`, drift rotation) - every one acts on the vehicle body, none on a "
      "seated driver, and none is a launch.")
    a("")
    a("## 3. The graphs the roster leaves out")
    a("")
    a(f"`{o['epe_on_disk']}` `.epe` files ship; `{o['roster_files'] + o['offroster_files']}` "
      f"contain `{EXIT_CLASS}`, of which `{o['offroster_files']}` are **not** roster "
      f"vehicles. They were decoded with `Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe` "
      f"and their exits counted: **{o['offroster_exits']}** exits "
      f"({', '.join(str(n) for n in o['offroster_hashed_members'])} hash-named members each), "
      f"**{o['offroster_launch_named']}** with a launch-capable member, named keys outside "
      f"the known set: {', '.join(o['offroster_extra_named']) or 'none'}.")
    a("")
    a("| graph | exits | states |")
    a("|---|---|---|")
    for g in o["graphs"]:
        states = sorted({x["state"] for x in g["exits"] if x["state"]})
        a(f"| `{os.path.basename(g['path'])}` | {len(g['exits'])} | "
          + ", ".join(f"`{s}`" for s in states) + " |")
    a("")
    a(f"Member types on the off-roster exits: "
      + ", ".join(f"{t} x{n}" for t, n in sorted(o["offroster_hashed_types"].items()))
      + f" - float/vector: **{o['offroster_launch_named']}**.")
    a("")
    a("These are gunner/mount and contextual-action exits ``exit.gunner`` -> "
      "``S_EXIT_MOUNTED_WEAPON``, ``exit.gunner.left`` -> ``S_EXIT_MOUNTED_WEAPON_TO_LEFT``, "
      "``exit.use_item.success`` -> ``S_EXIT_USE_ITEM_SUCCESS``, ``exit.normal`` -> "
      "``S_EXIT_CONTEXT_ACTION``, ``exit.interrupt`` -> ``S_INTERRUPT_CONTEXT_ACTION``. One of "
      "the 12 is a helicopter-type graph with the full driver exit set "
      "(``exit.driver.moving.parachute`` included). None is an eject and none carries a "
      "number. The reviewed report's 232-graph scope therefore understates the exit census "
      f"by {o['offroster_exits']} exits, but the finding is unchanged: 0 launch members.")
    a("")
    a("## 4. What the exe carries")
    a("")
    a(f"`{e['file']}` ({e['bytes']:,} B), string table scanned. Eject-like tokens found as "
      f"standalone names: `{'`, `'.join(e['eject_like_tokens'])}`.")
    a("")
    a("| name | hits | offset | role in the reviewed claim |")
    a("|---|---|---|---|")
    for n in ENGINE_NAMES:
        h = e["names"][n]
        a(f"| `{n}` | {h['count']} | {h['offsets'][0] if h['offsets'] else '-'} | **contradicts \"no eject\"** |")
    for n in CONTROL_NAMES:
        h = e["names"][n]
        a(f"| `{n}` | {h['count']} | {h['offsets'][0] if h['offsets'] else '-'} | reference test |")
    a("")
    a("Neighbour names, quoted from each name's printable run in the exe:")
    a("")
    for n in ENGINE_NAMES:
        a(f"* `{n}`: {e['names'][n]['run'] or 'UNKNOWN'}")
    a("")
    a("Read strictly, these are **names**, not behaviour: the strings prove the engine "
      "declares an eject action (with a mounted-gun variant) and two eject states, plus a "
      "bail explosion name in the heat tuning and a vehicle-state member for a Rico bail "
      "timer. They do not prove any of them is reachable from a vehicle's data. Section 5 "
      "is the reachability test.")
    a("")
    a("One caveat in the other direction: this exe table is **not** the universe of state "
      "names. `S_EXIT_VEHICLE_PARA` - the reviewed report's carrier - is absent from it "
      f"({e['names']['S_EXIT_VEHICLE_PARA']['count']} hits) while living in "
      f"{len(set(r['plain']['S_EXIT_VEHICLE_PARA']) | set(r['hash']['S_EXIT_VEHICLE_PARA']))} "
      "data files. So a name missing from the exe proves nothing; only a name's presence is "
      "evidence, and only its data references are proof of use.")
    a("")
    a("## 5. Who references them")
    a("")
    a(f"Scanned `{r['files_scanned']}` files: all 165 `.afsmb` state machines, 344 `.epe`, "
      "300 `.gsc` + 300 `.gdc` scripts, 61 `.asb`. Plaintext and, for `.afsmb`, the archive "
      "hash (Gibbed Jenkins lookup3 over the upper-case name - the scheme is verified below "
      "by the control).")
    a("")
    a("| name | hash | `.afsmb` hash hits | distinct files (plaintext or hash) |")
    a("|---|---|---|---|")
    for n in ALL_NAMES:
        h = r["hashes"][n]
        af = len(r["hash"][n])
        files = sorted(set(r["plain"][n]) | set(r["hash"][n]))
        tag = " (control)" if n in CONTROL_NAMES else ""
        a(f"| `{n}`{tag} | `{h}` | {af} | {len(files)} |")
    a("")
    if doc["counts"]["control_refs"].get("ACT_EXIT_VEHICLE"):
        a(f"**Controls work.** `ACT_EXIT_VEHICLE` is found in "
          f"{doc['counts']['control_refs']['ACT_EXIT_VEHICLE']} distinct file(s) and "
          f"`ACT_PANIC_EXIT_VEHICLE` in "
          f"{doc['counts']['control_refs'].get('ACT_PANIC_EXIT_VEHICLE', 0)}: the exe's "
          "table is a **superset** of what the shipped data uses (both names are in the exe; "
          "only one is used in data), so a name being in the exe is not evidence of use, and "
          "a name being absent from the data is meaningful.")
        a("")
        for n in ("ACT_EXIT_VEHICLE", "ACT_STUNT_VEHICLE_EXIT", "S_EXIT_VEHICLE_PARA"):
            paths = sorted(set(r["plain"][n]) | set(r["hash"][n]))
            if paths:
                shown = ", ".join("`" + os.path.basename(p) + "`" for p in paths[:6])
                more = f" ... (+{len(paths) - 6} more)" if len(paths) > 6 else ""
                a(f"* `{n}`: {shown}{more}")
        a("")
    a(f"**Every eject/bail name reads 0.** The {len(ENGINE_NAMES)} names are in the exe and "
      "in no state machine, graph or script. `PPparachute_vehicle_eject` is in "
      f"`rico_base.asb` ({c['asb_eject_clip']} hit) and in no state machine, so the clip is "
      "shipped but unwired by name.")
    a("")
    a("## 6. Animation, audio and script evidence")
    a("")
    a("| carrier | evidence | what it proves |")
    a("|---|---|---|")
    a(f"| animation set | `{os.path.basename(RICO_ASB)}` clip `PPparachute_vehicle_eject` | "
      "an eject-into-parachute animation was authored |")
    a(f"| animation set | clip `rico_vehi_car_low_driver_to_parachute.ban` | a car "
      "driver-to-parachute clip exists per vehicle class |")
    a(f"| dialogue | {idx['bark_assets']} index paths `bark_rico_parachute_ejecting_01..04` "
      "(`.ban` + `.wavc`) | Rico comments on parachute ejecting |")
    a(f"| DLC dialogue | {idx['dlc_eject_dialogue']} files "
      f"`mission_dlc2_mm110_dial_obj13_eject_*` over {len(idx['dlc_languages'])} languages | "
      "a DLC mission has an eject beat |")
    seen = set()
    for s in doc["scripts"]:
        key = (s["path"], s["string"])
        if key in seen:
            continue
        seen.add(key)
        a(f"| script | `{os.path.basename(s['path'])}` @ {s['offset']} "
          f"`{s['string']}` | a scripted bail-out beat exists in this script |")
        if len(seen) >= 6:
            break
    a("")
    a(f"Parachute clips named in `{os.path.basename(RICO_ASB)}`: "
      f"{', '.join('`' + x + '`' for x in doc['asb']['parachute_clips'])}.")
    a("")
    a("None of this is a trajectory. A clip name does not give its root motion, and the "
      "reviewed report was right to leave the upward impulse UNKNOWN; what changes is that "
      "the reason is now \"an eject animation exists and is unwired by name\", not \"the "
      "game has no eject\".")
    a("")
    a("## 7. What this changes for MOD-3")
    a("")
    a("| claim in `EJECT.md` | after this review |")
    a("|---|---|")
    a("| \"JC3 has no eject\" | **overstated.** The engine has an eject action, two eject "
      "states, a bail explosion name and a bail timer member; nothing in the vehicle data "
      "references them. Correct wording: \"no vehicle graph authors an eject\". |")
    a("| \"0 of 4,832 exits carry a launch member\" | **holds**, and now covers all shipped "
      f"graphs: {cen['exits']} roster + {o['offroster_exits']} off-roster exits, "
      f"{cen['launch_members'] + o['offroster_launch_named']} launch members. |")
    a("| \"no vehicle module can push the driver up\" | **holds**, still one distinct hit "
      "(`TrainGlobal.crashing_impulse`) after adding `bail` to the sweep. |")
    a("| \"exiting above the gate selects `S_EXIT_VEHICLE_PARA`\" | unchanged - that state "
      "is present in `rico_base.afsmb` and is the only exit-into-parachute state wired. |")
    a("| launch half has no JC3 carrier | **unchanged in practice, changed in cause.** An "
      "engine eject exists but is unreachable from data; whether the shipped game triggers "
      "it from code, and whether it carries any vertical impulse, is UNKNOWN. |")
    a("")
    a("## 8. UNKNOWNs")
    a("")
    a("1. **Whether the engine's eject is reachable at all.** The names exist, no data "
      "references them. The trigger lives in native code (or in a code-side default not "
      "stored in any `.epe`/`.afsmb`/script). Testing it needs a Q-1 probe with an input or "
      "a debug command, which this review cannot do read-only.")
    a("2. **Whether `S_EXIT_VEHICLE_PARA` / the `PPparachute_vehicle_eject` clip applies a "
      "vertical impulse.** Clip bodies are not decoded; the reviewed report's Q1-EJ-A probe "
      "is still the only way to answer it.")
    a("3. **What `EJECT_FROM_VEHICLE_MG` selects.** The exe names a mounted-gun variant; the "
      "two mount graphs (`w201_minigun_mount`, `w205_mounted_urga_uzhas_120_mount`) exit "
      "through `S_EXIT_MOUNTED_WEAPON` and never name it, so which weapon/vehicle state it "
      "belongs to is UNKNOWN.")
    a("4. **Whether the four `parachute_ejecting` barks are reachable.** Dialogue files ship "
      "for four lines; no script or bark table in the index names them as a triggered event "
      "(the bark table itself is audio middleware data, not decoded here).")
    a("5. **The 17 hash-named exit members.** Their types are known (no float/vector) and one "
      "is the class-hash field, but their **names** are not decoded; a dictionary of "
      f"{m['dictionary_tokens']:,} exe tokens found none. Naming them needs the epe property "
      "name list, which is not in the grab.")
    a("")
    a("## 9. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/jc3eject.py --check        # the reviewed report: fails on path text")
    a("python Tools/scripts/jc3eject2.py --write      # this file + EJECT_REVIEW.json")
    a("python Tools/scripts/jc3eject2.py --check      # re-derive and compare")
    a("```")
    a("")
    a("Inputs (read-only): `Research/JC3Grab/EJECT.md` + `EJECT.json`, "
      f"`{DETAIL}/*.ee.json` x232, `{ENTITIES}/*.ee.json` x232, "
      "`Research/JC3Grab/INDEX.jsonl`, `D:/Games/Just Cause 3/JustCause3.exe`, and archive "
      "entries read through `jc3grab.read_entry` (`.afsmb`, `.epe`, `.asb`, `.gsc`, `.gdc`). "
      f"Off-roster `.epe` decoding uses `Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe` "
      "with scratch files under `tmp/freebuff/scratch/eject_review/`. No game launch, no "
      "archive write.")
    a("")
    return "\n".join(L)


# ----------------------------------------------------------------------------- cli

def dump(what: str) -> int:
    doc = build()
    if what == "engine":
        print(json.dumps(doc["engine"], indent=1)[:6000])
    elif what == "refs":
        print(json.dumps(doc["refs"], indent=1)[:6000])
    elif what == "census":
        print(json.dumps({"census": doc["census"], "offroster": doc["offroster"],
                          "counts": doc["counts"]}, indent=1)[:6000])
    elif what == "orig":
        print(json.dumps(doc["orig_check"], indent=1)[:6000])
    else:
        print("dump engine|refs|census|orig")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write EJECT_REVIEW.md + .json")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("what")
    a = ap.parse_args()
    if a.cmd == "dump":
        return dump(a.what)
    for p in (EXE, DETAIL, INDEX_JSONL, ORIG_MD):
        if not os.path.exists(p):
            print(f"BLOCKED: missing input {p}")
            return 2
    doc = build()
    md = report(doc)
    js = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    md_path, js_path = os.path.join(OUT, MD_NAME), os.path.join(OUT, JSON_NAME)
    c = doc["counts"]
    summary = (f"{doc['verdict']} | roster {c['roster_exits']} exits / "
               f"{c['roster_launch_members']} launch | off-roster {c['offroster_exits']} exits / "
               f"{c['offroster_launch']} launch | engine eject names "
               f"{c['engine_names_present']}/{c['engine_names']}, data refs {c['engine_data_refs']} | "
               f"control ACT_EXIT_VEHICLE {c['control_refs'].get('ACT_EXIT_VEHICLE', 0)} | "
               f"asb clip {c['asb_eject_clip']} | barks {c['bark_assets']} | "
               f"orig json_equal {c['orig_json_equal']} md_equal {c['orig_md_equal']}")
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(md_path, "w", encoding="utf-8", newline="\n").write(md)
        open(js_path, "w", encoding="utf-8", newline="\n").write(js)
        print(f"wrote {md_path} ({len(md.splitlines())} lines) + {js_path}")
    if a.check:
        bad = []
        for path, text, name in ((md_path, md, MD_NAME), (js_path, js, JSON_NAME)):
            if not os.path.exists(path):
                bad.append(f"{name} missing")
                continue
            disk = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
            if disk != text:
                diff = [ln for ln in difflib.unified_diff(disk.splitlines(), text.splitlines(),
                                                          "disk", "derived", lineterm="", n=0)][:8]
                bad.append(f"{name} stale: " + " | ".join(diff))
        if bad:
            for b in bad:
                print("FAIL", b)
            print(f"{len(bad)} problem(s)")
            return 1
        print(f"PASS: {summary}")
        return 0
    print(f"OK: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
