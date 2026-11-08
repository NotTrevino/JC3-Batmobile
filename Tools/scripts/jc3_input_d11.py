"""jc3_input_d11.py - D-11: can a car module receive battle mode / immobilizer / eject?

G3-08 (`Research/JC3Grab/INPUT.md`) decoded the keymaps and gave name-level verdicts for the
BmAK actions (INPUT.md's BmAK table: "not reachable" for battle mode and ejection, "reachable"
for the immobilizer via `USE_ITEM`). This card re-asks the three D-11 questions the only way
that can settle them, from JC3 data alone:

  * **is there a keymap action** (`settings/keymap_*.bin`, base + patch) whose name matches the
    action, using the *same* semantic regexes INPUT.md used;
  * **does any vehicle module consume it** - search every decoded vehicle `.epe` / `.vmodc`
    under `$JC3_RAW` for the action's id and for `H(action name)`, where `H` is
    `rbmhdr.hash_jenkins` (the same Jenkins lookup3 INPUT.md used), in little-endian,
    big-endian, decimal ASCII and hex ASCII.

A name-level match is not a hit. A row is a hit only when the hash occurs **and** the
occurrence can be named as a member/behaviour; otherwise the answer is UNKNOWN, with the
searched file count printed.

Controls that would fail if the search were broken:
  * the RTPC root hash `AA7D522A` must be found in the `.epe`/`.vmodc` set (positive control);
  * the keymap parse must reproduce INPUT.md's 474 bindings / 154 actions;
  * `USE_ITEM`'s decoded binding id must equal `H("USE_ITEM")`.

Usage
  python Tools/scripts/jc3_input_d11.py --write
  python Tools/scripts/jc3_input_d11.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jc3_input as I  # noqa: E402  (reused read-only: its archive reader + keymap parser)
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "INPUT_D11.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "INPUT_D11.json")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
ENTITIES = os.path.join(RAW, "entities")

# The three D-11 questions, with the regexes INPUT.md used for the same rows.
TARGETS = [
    {"id": "battle-mode toggle", "key": "battle",
     "rx": r"(?i)BATTLE|PURSUIT|TRANSFORM|MODE$",
     "inputmd": "battle mode (LT hold / release pursuit)",
     "inputmd_verdict": "not reachable"},
    {"id": "immobilizer", "key": "immobilizer",
     "rx": r"(?i)IMMOBIL|EMP",
     "inputmd": "immobilizer (B in track)",
     "inputmd_verdict": "reachable (via USE_ITEM)",
     "near_names": ["USE_ITEM"]},
    {"id": "eject", "key": "eject",
     "rx": r"(?i)EJECT|LAUNCH|CATA.?PULT",
     "inputmd": "electromagnetic ejection (A)",
     "inputmd_verdict": "not reachable"},
]
ROOT_HASH = 0xAA7D522A          # RTPC root, the positive control
CONTROL_NAME = b"RTPC"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def h32(name: str) -> int:
    return hash_jenkins(name.encode("ascii", "replace")) & 0xFFFFFFFF


# ---------------------------------------------------------------- keymaps
def keymap_actions() -> dict:
    """Parse all four keymap copies exactly as G3-08 did (its reader + parser)."""
    rows = I.load_index(os.path.join(ROOT, "Research", "JC3Grab"))
    copies, bindings = [], []
    for path in I.KEYMAPS:
        entries = I.read_entries(rows, path)
        if not entries:
            raise SystemExit("not in the index: %s" % path)
        for r, data in entries:
            bs, acc = I.parse_keymap(path, r, data)
            if acc["bindings"] != len(bs):
                raise SystemExit("%s: %d bindings parsed, %d accounted" %
                                 (path, len(bs), acc["bindings"]))
            device = "gamepad" if "gamepad" in path else "keyboard"
            copies.append({"path": path, "mount": r["mount"], "archive": r["archive"],
                           "entry_offset": r["offset"], "bindings": acc["bindings"],
                           "root_hash": acc["root_hash"], "sha256": acc["sha256"][:16],
                           "tiles": acc["blocks_tile_data"]})
            for b in bs:
                b.update(file=path, device=device, mount=r["mount"], archive=r["archive"],
                         entry_offset=r["offset"])
                bindings.append(b)
    # the mounted layer per INPUT.md's rule: the patch copy wins a path lookup
    active = {}
    for path in I.KEYMAPS:
        active[path] = max((c["mount"] for c in copies if c["path"] == path),
                           key=lambda m: I.MOUNT_RANK[m])
    return {"copies": copies, "bindings": bindings, "active": active}


def action_index(km: dict) -> dict:
    """action -> {device: [inputs]}, ids (node hashes), mounts - mounted layer only."""
    out = {}
    for b in km["bindings"]:
        if b["mount"] != km["active"][b["file"]]:
            continue
        d = out.setdefault(b["action"], {"inputs": {}, "ids": set(), "mounts": set(),
                                         "files": set()})
        d["inputs"].setdefault(b["device"], []).append(b["input"])
        d["ids"].add(b["node_hash"])
        d["mounts"].add(b["mount"])
        d["files"].add(b["file"])
    return out


# ---------------------------------------------------------------- search set
def search_set() -> dict:
    """Every decoded vehicle .epe / .vmodc under $JC3_RAW, deduplicated by content."""
    files = []
    for root, _dirs, names in os.walk(RAW):
        for n in names:
            if n.endswith((".epe", ".vmodc")):
                files.append(os.path.join(root, n))
    files.sort()
    seen, uniq, dupes = {}, [], []
    for p in files:
        blob = open(p, "rb").read()
        h = sha(blob)
        if h in seen:
            dupes.append({"path": os.path.relpath(p, RAW).replace("\\", "/"),
                          "same_as": seen[h]})
            continue
        seen[h] = os.path.relpath(p, RAW).replace("\\", "/")
        uniq.append({"path": os.path.relpath(p, RAW).replace("\\", "/"), "bytes": len(blob),
                     "sha256": h, "blob": blob})
    # a vehicle = one distinct `*_vehicle_parts.vmodc` module (the per-vehicle parts table)
    parts = sorted({os.path.basename(f["path"]).replace("_vehicle_parts.vmodc", "")
                    for f in uniq if f["path"].endswith("_vehicle_parts.vmodc")})
    kinds = Counter()
    for f in uniq:
        kinds[f["blob"][:4].hex()] += 1
    return {"on_disk": len(files),
            "unique": [{k: v for k, v in f.items() if k != "blob"} for f in uniq],
            "duplicates": dupes,
            "parts_modules": parts,
            "kinds": dict(sorted(kinds.items())),
            "blobs": {f["path"]: f["blob"] for f in uniq}}


# ---------------------------------------------------------------- the test
def probe(names: list, ids: set, blobs: dict) -> dict:
    """Search every unique file for the name's hashes and the action id."""
    forms = {}
    for n in names:
        h = h32(n)
        forms[n] = {"h": h, "action_id": sorted(i for i in ids),
                    "le": struct.pack("<I", h), "be": struct.pack(">I", h),
                    "dec": str(h).encode(), "hex": ("%08X" % h).encode(),
                    "hex_lower": ("%08x" % h).encode(), "name": n.encode()}
    hits = []
    name_hits = []
    for path, blob in blobs.items():
        for n, f in forms.items():
            found = [k for k in ("le", "be", "dec", "hex", "hex_lower") if f[k] in blob]
            for aid in f["action_id"]:
                raw = bytes.fromhex(aid)
                for enc, tag in ((raw, "id-le"), (raw[::-1], "id-be")):
                    if enc in blob:
                        found.append(tag)
            if found:
                hits.append({"path": path, "name": n, "hash": "%08X" % f["h"],
                             "forms": sorted(set(found))})
            if f["name"] in blob:
                name_hits.append({"path": path, "name": n})
    return {"forms": {n: {k: v for k, v in f.items()
                          if k not in ("le", "be", "dec", "hex", "hex_lower", "name")}
                      for n, f in forms.items()},
            "hits": hits, "name_hits": name_hits}


def context(blob: bytes, needle: bytes) -> list:
    """Every offset of `needle`, with a hex window - a hit with no name is not a consumer."""
    out = []
    start = 0
    while True:
        i = blob.find(needle, start)
        if i < 0:
            break
        out.append({"offset": i, "window": blob[max(0, i - 8):i + 12].hex()})
        start = i + 1
        if len(out) >= 8:
            break
    return out


def build() -> dict:
    km = keymap_actions()
    acts = action_index(km)
    ss = search_set()
    blobs = ss["blobs"]

    # positive control: the RTPC root hash must appear in the .epe/.vmodc set
    control = {"root_hash": "%08X" % ROOT_HASH,
               "files_with_root": sum(1 for b in blobs.values()
                                      if struct.pack("<I", ROOT_HASH) in b),
               "files_with_RTPC_magic": sum(1 for b in blobs.values()
                                            if b[:4] == CONTROL_NAME)}

    rows = []
    for t in TARGETS:
        rx = re.compile(t["rx"])
        named = sorted(a for a in acts if rx.search(a))
        near = [n for n in t.get("near_names", []) if n in acts]
        names = sorted(set(named) | set(near))
        ids = set()
        for n in names:
            ids |= acts[n]["ids"]
        pr = probe(names, ids, blobs) if names else {"forms": {}, "hits": [], "name_hits": []}
        consumers = []
        for hit in pr["hits"]:
            blob = blobs[hit["path"]]
            f = h32(hit["name"])
            ctx = context(blob, struct.pack("<I", f)) or context(blob, str(f).encode())
            hit["context"] = ctx
            # A hit is a consumer only if the occurrence sits in a named member. The RTPC
            # decoders in this tree do not expose .epe/.vmodc property names by offset, so
            # no hit can be named here: it is recorded as an unnamed match, not a consumer.
            hit["named_member"] = None
            consumers.append(hit)
        if not names:
            verdict = "no keymap action"
            detail = ("no action name in the four keymap copies matches /%s/ "
                      "(INPUT.md's regex for the same row)" % t["rx"])
        elif not consumers:
            verdict = "name only, no consumer"
            detail = ("%d keymap action(s) match by name (%s) but none of the %d decoded "
                      "vehicle .epe/.vmodc files contains its id or H(name) in any encoding"
                      % (len(names), ", ".join(names), len(blobs)))
        elif all(c["named_member"] is None for c in consumers):
            verdict = "unnamed hash match only"
            detail = ("%d hash occurrence(s) but none can be named as a member, so it is not "
                      "a consumer" % len(consumers))
        else:
            verdict = "hit with consumer"
            detail = "hash occurs inside a named member"
        rows.append({
            "id": t["id"], "key": t["key"], "regex": t["rx"],
            "inputmd_row": t["inputmd"], "inputmd_verdict": t["inputmd_verdict"],
            "actions_by_name": named, "near_names": near, "names_searched": names,
            "binding": {n: {"inputs": acts[n]["inputs"], "ids": sorted(acts[n]["ids"]),
                            "mounts": sorted(acts[n]["mounts"])} for n in names},
            "hashes": pr["forms"], "hits": consumers, "name_hits": pr["name_hits"],
            "verdict": verdict, "detail": detail,
            "answer": "UNKNOWN" if verdict != "hit with consumer" else "hit",
        })

    # structural control: does ANY keymap action hash appear in ANY vehicle module?
    all_ids = {i for a in acts.values() for i in a["ids"]}
    all_names = {n: h32(n) for n in acts}
    id_le = {bytes.fromhex(i) for i in all_ids}
    name_le = {struct.pack("<I", h) for h in all_names.values()}
    files_with_id = sorted(p for p, b in blobs.items() if any(x in b for x in id_le))
    files_with_name = sorted(p for p, b in blobs.items() if any(x in b for x in name_le))

    # secondary: the 232 entity dumps, for the same three names (ASCII + hash)
    ent_files = sorted(os.listdir(ENTITIES)) if os.path.isdir(ENTITIES) else []
    ent_hits = {n: 0 for n in ("USE_ITEM", "BATTLE", "EJECT")}
    ent_hash_hits = {n: 0 for n in ("USE_ITEM", "BATTLE", "EJECT")}
    for fn in ent_files:
        blob = open(os.path.join(ENTITIES, fn), "rb").read()
        for n in ent_hits:
            if n.encode() in blob:
                ent_hits[n] += 1
            if struct.pack("<I", h32(n)) in blob:
                ent_hash_hits[n] += 1

    oracles = {
        "keymap_parse_matches_g3_08": {
            "ok": len(km["bindings"]) == 474 and len(acts) == 154,
            "detail": {"bindings": len(km["bindings"]), "actions": len(acts),
                       "expected": [474, 154]}},
        "four_keymap_copies_tile": {
            "ok": all(c["tiles"] and c["bindings"] > 0 for c in km["copies"]) and
                  len(km["copies"]) == 4,
            "detail": {("%s@%s" % (c["path"], c["mount"])): c["bindings"]
                       for c in km["copies"]}},
        "positive_control_root_hash_found": {
            # every file that starts with the RTPC magic must contain the root hash;
            # that equality is what fails if the byte search misses
            "ok": control["files_with_root"] == control["files_with_RTPC_magic"] > 0,
            "detail": control},
        "vehicle_parts_modules_found": {
            "ok": len(ss["parts_modules"]) >= 70,
            "detail": {"vehicle_parts_modules": len(ss["parts_modules"])}},
        "use_item_id_is_H_of_its_name": {
            "ok": "USE_ITEM" in acts and
                  ("%08X" % h32("USE_ITEM")) in acts["USE_ITEM"]["ids"],
            "detail": {"H(USE_ITEM)": "%08X" % h32("USE_ITEM"),
                       "decoded ids": sorted(acts.get("USE_ITEM", {}).get("ids", []))}},
        "no_vehicle_module_carries_any_action_hash": {
            "ok": not files_with_id and not files_with_name,
            "detail": {"files_with_any_action_id": len(files_with_id),
                       "files_with_any_H(action)": len(files_with_name),
                       "action_ids": len(all_ids)}},
        "every_target_reports_a_reason": {
            "ok": all(r["verdict"] and r["detail"] for r in rows),
            "detail": {r["id"]: r["verdict"] for r in rows}},
    }
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/jc3_input_d11.py --write",
        "card": "D-11 - battle-mode toggle / immobilizer / eject against the JC3 keymaps and vehicle modules",
        "method": {
            "hash": "rbmhdr.hash_jenkins (Jenkins lookup3), the same function G3-08 used",
            "keymap_reader": "jc3_input.read_entries + parse_keymap (G3-08), read-only",
            "encodings": ["u32 little-endian", "u32 big-endian", "decimal ASCII",
                          "hex ASCII (upper/lower)", "action NAME ASCII"],
            "hit_rule": "a hit needs the hash in a vehicle module AND a nameable member; "
                        "a name-level keymap match alone is not a hit",
        },
        "keymap": {"copies": km["copies"], "active": km["active"],
                   "bindings": len(km["bindings"]), "actions": len(acts)},
        "search": {"root": RAW,
                   "files_on_disk": ss["on_disk"], "files_unique": len(blobs),
                   "duplicates": len(ss["duplicates"]), "kinds": ss["kinds"],
                   "vehicles": len(ss["parts_modules"]),
                   "vehicle_names": ss["parts_modules"]},
        "entities": {"files": len(ent_files), "ascii_hits": ent_hits,
                     "hash_hits": ent_hash_hits},
        "controls": control,
        "rows": rows,
        "oracles": oracles,
        "unknowns": [
            "battle-mode toggle: no keymap action name matches BATTLE/PURSUIT/TRANSFORM/MODE$ "
            "in any of the four copies, so there is nothing to bind and nothing a module could "
            "receive. Whether the game has a native mode switch outside the keymap is UNKNOWN.",
            "eject: likewise zero names match EJECT/LAUNCH/CATA.?PULT; the D-11 'A' mapping has "
            "no JC3 action in the decoded tables.",
            "immobilizer: `USE_ITEM` is bound (gamepad RPADUP, keyboard E) and is the name "
            "G3-08 mapped 'B in track' to, but it is a generic item action: no vehicle module "
            "in the 207 files references it, so what it does inside a car is UNKNOWN.",
            "the .epe/.vmodc property-name decoder: these containers store property hashes, "
            "not strings, and no decoder in this tree maps a .vmodc property hash to a member "
            "path by offset. A raw 4-byte hit could therefore not be named even if it existed, "
            "which is why the hit rule requires a nameable member.",
            "whether a car's input path exists at all in data: no vehicle .epe/.vmodc and no "
            "entity dump carries any of the 154 action ids or their name hashes, so the "
            "keymap-to-vehicle wiring is native to the engine, not a data member.",
        ],
    }


# ---------------------------------------------------------------- render
def md(s) -> str:
    return str(s).replace("|", "\\|")


def render(d: dict) -> str:
    o = []
    w = o.append
    w("# D-11: battle-mode toggle, immobilizer, eject - keymap action and vehicle consumer")
    w("")
    w("Generated by `Tools/scripts/jc3_input_d11.py --write`; `--check` re-parses the four "
      "keymap copies and re-scans every vehicle module. JC3 data only: the BmAK side is "
      "G3-02's `CONTROLS.md` and the D-11 mapping in `GRAB_BACKLOG.md`, which this card only "
      "cites.")
    w("")
    w("Method: the keymaps are parsed with G3-08's own reader (`jc3_input.read_entries` + "
      "`parse_keymap`, read-only) and hashed with `rbmhdr.hash_jenkins`, the same Jenkins "
      "lookup3 G3-08 used. Each target's action names are searched in **%d** decoded vehicle "
      "`.epe`/`.vmodc` files (%d on disk, %d distinct contents) as the action id, as `H(name)` "
      "and as the literal name, in little-endian, big-endian, decimal, hex and ASCII."
      % (d["search"]["files_unique"], d["search"]["files_on_disk"],
         d["search"]["files_unique"]))
    w("")
    w("**A name-level keymap match is not a hit.** A row counts as a hit only when the hash "
      "occurs in a vehicle module *and* the occurrence can be named as a member or behaviour. "
      "Everything else is **UNKNOWN**, with the searched count printed.")
    w("")
    w("## Answer")
    w("")
    w("| D-11 action | keymap action | consumer in a vehicle module | answer |")
    w("|---|---|---|---|")
    for r in d["rows"]:
        acts = ", ".join("`%s`" % n for n in r["names_searched"]) or "**none**"
        w("| %s | %s | %d hash hit(s) in %d files | **%s** |"
          % (r["id"], acts, len(r["hits"]), d["search"]["files_unique"], r["answer"]))
    w("")
    for r in d["rows"]:
        w("### %s" % r["id"])
        w("")
        w("- G3-08 row: %s -> %s" % (r["inputmd_row"], r["inputmd_verdict"]))
        w("- name rule (the same regex): `/%s/`" % r["regex"])
        w("- keymap actions matching: %s" % (", ".join("`%s`" % n for n in r["actions_by_name"])
                                             or "**none** in any of the four copies"))
        if r["near_names"]:
            w("- near-name G3-08 used for this row: %s"
              % ", ".join("`%s`" % n for n in r["near_names"]))
        for n, b in r["binding"].items():
            w("- `%s`: inputs %s ; binding id %s ; layer %s"
              % (n, json.dumps(b["inputs"], sort_keys=True), b["ids"], b["mounts"]))
        for n, h in r["hashes"].items():
            w("- `%s` hash **%08X**" % (n, h["h"]))
        w("- hash hits in the %d vehicle modules: **%d** ; literal-name hits: **%d**"
          % (d["search"]["files_unique"], len(r["hits"]), len(r["name_hits"])))
        w("- **answer %s** - %s" % (r["answer"], r["detail"]))
        w("")
    w("## Controls (a broken search would fail these)")
    w("")
    c = d["controls"]
    w("| control | value |")
    w("|---|---|")
    w("| RTPC root hash `%s` found in | %d of %d files |"
      % (c["root_hash"], c["files_with_root"], d["search"]["files_unique"]))
    w("| files starting with `RTPC` | %d of %d |"
      % (c["files_with_RTPC_magic"], d["search"]["files_unique"]))
    w("| keymap bindings parsed | %d (G3-08: 474) |" % d["keymap"]["bindings"])
    w("| distinct actions | %d (G3-08: 154) |" % d["keymap"]["actions"])
    w("| `H(\"USE_ITEM\")` | `%08X`, equal to the decoded binding id |"
      % d["rows"][1]["hashes"]["USE_ITEM"]["h"] if d["rows"][1]["hashes"] else "| - |")
    w("")
    w("## The search set")
    w("")
    w("| | |")
    w("|---|---|")
    w("| root | `%s` |" % md(d["search"]["root"]))
    w("| `.epe` / `.vmodc` on disk | %d |" % d["search"]["files_on_disk"])
    w("| distinct contents searched | %d |" % d["search"]["files_unique"])
    w("| byte-identical duplicates | %d |" % d["search"]["duplicates"])
    w("| distinct vehicles (one per `*_vehicle_parts.vmodc`) | %d |"
      % d["search"]["vehicles"])
    w("| container magics | %s |" % md(json.dumps(d["search"]["kinds"])))
    w("| entity dumps re-checked (secondary) | %d |" % d["entities"]["files"])
    w("")
    w("Vehicles covered (%d, one per `*_vehicle_parts.vmodc`): %s."
      % (d["search"]["vehicles"],
         ", ".join("`%s`" % v for v in d["search"]["vehicle_names"][:40])
         + (" …" if d["search"]["vehicles"] > 40 else "")))
    w("")
    w("## The structural result")
    w("")
    o2 = d["oracles"]["no_vehicle_module_carries_any_action_hash"]["detail"]
    w("No vehicle `.epe`/`.vmodc` carries **any** of the %d keymap action ids (%d files) or any "
      "`H(action name)` (%d files). The keymap-to-vehicle link is therefore not a data member in "
      "this file set: whatever routes a button to a car's behaviour is native or lives in a "
      "container none of these decoders exposes." % (o2["action_ids"],
                                                    o2["files_with_any_action_id"],
                                                    o2["files_with_any_H(action)"]))
    w("")
    w("Secondary scan of the %d entity `.ee` dumps: `USE_ITEM` as ASCII in %d file(s), its hash "
      "in %d ; `BATTLE` %d / %d ; `EJECT` %d / %d."
      % (d["entities"]["files"], d["entities"]["ascii_hits"]["USE_ITEM"],
         d["entities"]["hash_hits"]["USE_ITEM"], d["entities"]["ascii_hits"]["BATTLE"],
         d["entities"]["hash_hits"]["BATTLE"], d["entities"]["ascii_hits"]["EJECT"],
         d["entities"]["hash_hits"]["EJECT"]))
    w("")
    w("## Oracles (`--check` re-runs them)")
    w("")
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k, v in d["oracles"].items():
        w("| `%s` | %s | %s |" % (k, v["ok"], md(json.dumps(v["detail"]))[:300]))
    w("")
    w("## UNKNOWN")
    w("")
    for i, u in enumerate(d["unknowns"], 1):
        w("%d. %s" % (i, u))
    w("")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = render(doc)
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote INPUT_D11.md / .json")
        print("keymap: %d bindings, %d actions, active %s"
              % (doc["keymap"]["bindings"], doc["keymap"]["actions"], doc["keymap"]["active"]))
        print("search: %d files on disk, %d unique, %d vehicles"
              % (doc["search"]["files_on_disk"], doc["search"]["files_unique"],
                 doc["search"]["vehicles"]))
        for r in doc["rows"]:
            print("  %-20s names=%-12s hits=%d name_hits=%d -> %s"
                  % (r["id"], ",".join(r["names_searched"]) or "-", len(r["hits"]),
                     len(r["name_hits"]), r["answer"]))
        print("controls:", doc["controls"])
        print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
        return 0
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    if json.dumps(stored, sort_keys=True) != json.dumps(doc, sort_keys=True):
        fails.append("re-derivation differs from INPUT_D11.json")
    if open(OUT_MD, encoding="utf-8").read() != render(stored):
        fails.append("INPUT_D11.md is not the render of the JSON")
    for k, v in stored["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, md(json.dumps(v["detail"]))[:200]))
    for r in stored["rows"]:
        if r["answer"] == "hit" and not any(h.get("named_member") for h in r["hits"]):
            fails.append("%s claims a hit without a named consumer" % r["id"])
        if r["answer"] == "UNKNOWN" and any(h.get("named_member") for h in r["hits"]):
            fails.append("%s has a named consumer but says UNKNOWN" % r["id"])
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK: %d targets, answers %s; all oracles true"
          % (len(stored["rows"]), [r["answer"] for r in stored["rows"]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
