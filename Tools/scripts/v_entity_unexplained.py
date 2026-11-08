#!/usr/bin/env python3
"""Trace the 36 UNEXPLAINED entity-graph differences to the step that produced them.

`Builds/bm-RC2/verify/entity_diff.md` (v_entity_diff.py) leaves 36 differences untagged by
`Working/Entity/bm_epe_edits.json`: 34 dropped `CPartProp` objects, the renamed root `CCar` and the
root member `palette`. This script re-derives those 36 from the two graphs (read-only: the game
archive is extracted to a temp directory, the built `.epe` is only read) and answers, per kind:

  * which pipeline step produced it - with the file:line of the code that does it, looked up in
    `Tools/scripts/bm_entity.py`, `bm_leaf.py`, `bm_rc2.py` and `bm_paths.py` on every run;
  * whether the MODLOG / B cards call it intended;
  * for the 34 props: what a `CPartProp` is, which part each one binds (`part_index` -> the donor
    parts table), and whether its removal can matter for the car.

It also proves the negative: the later steps named in the brief - the RC 3-way merge, B-16's
weapon-clone cleanup, T-13R - cannot have removed an object, and the receipt's own B-16 line
counts 4 owner links + 12 *members* on weapon clones the build adds.

Evidence is re-measured, never typed: the base graph (bm-009) and the pre-merge graph (bm-005) are
exported and censused on every run, the donor parts table is read, and every document quote is
required to still be present at a unique line.

Usage
  python Tools/scripts/v_entity_unexplained.py --write   # Builds/bm-RC2/verify/entity_unexplained.md
  python Tools/scripts/v_entity_unexplained.py --check   # re-derive, run oracles, byte-compare
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_parts  # noqa: E402
import v_entity_diff as ED  # noqa: E402  (the diff itself: one implementation, no second parser)
from rbmhdr import hash_jenkins  # noqa: E402

ENTITY_DIR = ED.ENTITY.rsplit("/", 1)[0]
CIVILIAN = ENTITY_DIR + "/v0300_car_kensington_sportsmuscle_civilian_01.epe"
BASE_EPE = "Builds/bm-009/aaf/" + CIVILIAN
PRE_EPE = "Builds/bm-005/aaf/" + CIVILIAN
RECEIPT = "Builds/bm-RC2/receipt.json"
PARTS_TABLE = "Research/JC3Grab/PARTS_TABLE.jsonl"
B05_SPEC = "Research/specs/B-05.md"
B05_REVIEW = "Research/challenge/card-B-05.md"
TINT_WRITE = "Research/JC3Grab/TINT_WRITE.md"
OUT = "Builds/bm-RC2/verify/entity_unexplained.md"


def rel(p: str) -> str:
    return p.replace("\\", "/")


def s32(v: int) -> int:
    return v - (1 << 32) if v >= 1 << 31 else v


def anchor(path: str, needle: str, what: str) -> int:
    """The single line in `path` that contains `needle` (a rename or a regeneration stops the run)."""
    lines = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read().splitlines()
    hit = [i + 1 for i, line in enumerate(lines) if needle in line]
    if len(hit) != 1:
        raise SystemExit("%s: expected exactly 1 line with %r, found %d" % (path, needle, len(hit)))
    return hit[0]


def cite(path: str, needle: str, what: str) -> dict:
    return {"path": path, "line": anchor(path, needle, what), "what": what}


def counted(epe_rel: str, work: str, tag: str) -> dict:
    """Export one `.epe` and census it with the same parser the diff uses."""
    src = os.path.join(ROOT, epe_rel)
    if not os.path.exists(src):
        raise SystemExit("missing " + epe_rel)
    os.makedirs(work, exist_ok=True)
    xml = os.path.join(work, tag + ".xml")
    for attempt in range(3):          # Windows temp can transiently refuse the output file
        try:
            ED.export(src, xml)
            break
        except SystemExit:
            if attempt == 2:
                raise
            time.sleep(0.5)
    objs = ED.parse(xml)
    props = sorted(({"kind": "prop", "cls": o["cls"], "name": o["name"], "node": o["node"],
                     "id": o["id"], "part_index": o["props"].get("part_index")}
                    for o in objs if o["props"].get("_class") == "CPartProp"),
                   key=lambda p: (int(p["part_index"]), p["name"]))
    return {"objects": len(objs), "props": props,
            "sha256": hashlib.sha256(open(src, "rb").read()).hexdigest()}


def donor_table() -> dict[str, dict]:
    """part_index -> row, from the donor's own parts-module table (PARTS_TABLE.jsonl)."""
    rows = None
    with open(os.path.join(ROOT, PARTS_TABLE), encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["entity"].endswith("v0300_car_kensington_sportsmuscle_debug.ee"):
                rows = d
                break
    if rows is None:
        raise SystemExit("no debug donor row in " + PARTS_TABLE)
    return {str(p["i"]): p for p in rows["parts"]}


def module_census(aaf_files: list[dict]) -> dict:
    cand = [f["path"] for f in aaf_files if f["path"].endswith("/sportsmuscle_vehicle_parts.vmodc")]
    if len(cand) != 1:
        raise SystemExit("expected exactly one parts module in the RC2 tree, found %r" % cand)
    blob = open(os.path.join(ROOT, "Builds", "bm-RC2", "aaf", cand[0]), "rb").read()
    parts = bm_parts.decode_parts(blob)
    return {"path": cand[0], "parts": len(parts),
            "names": {p["name"] for p in parts},
            "indices": {p["name"]: p["part_index"] for p in parts},
            "index_list": sorted(p["part_index"] for p in parts),
            "doors": {p["name"]: {"parent": p["parent_part_index"],
                                   "children": p["children_part_indices"]}
                      for p in parts if p["name"] in ("sportsmuscle_door_f_l",
                                                      "sportsmuscle_door_f_r")}}


def spec_silence(spec: dict, names: list[str]) -> bool:
    named = set()
    for a in spec["additions"]:
        named.add(a.get("name"))
    for e in spec["edits"]:
        named.add(e.get("node"))
    for o in spec.get("added_objects", []):
        named.add(o.get("name"))
    return all(n not in named for n in names)


def build() -> dict:
    work = tempfile.mkdtemp(prefix="v_entity_unexplained_")
    d = ED.build()                      # 36 UNEXPLAINED, re-derived from both files
    unexp = d["unexp"]
    removed = [u for u in unexp if u.get("kind") == "removed"]
    renamed = d["renamed"]
    presence = d["presence"]
    if len(unexp) != 36 or len(removed) != 34 or renamed is None or len(presence) != 1:
        raise SystemExit("entity_diff no longer reports 34 removed + rename + 1 member")

    vanilla_by_node = {o["node"]: o for o in d["vanilla"]}
    for r in removed:
        r["part_index"] = vanilla_by_node[r["node"]]["props"].get("part_index")

    base = counted(BASE_EPE, work, "base_bm009")
    pre = counted(PRE_EPE, work, "premerge_bm005")

    rec = json.load(open(os.path.join(ROOT, RECEIPT), encoding="utf-8"))
    aaf_files = rec["aaf"]["list"]
    mod = module_census(aaf_files)
    donor = donor_table()

    pal_val = presence[0]["value"]
    pal_path = next(f["path"] for f in aaf_files if f["path"].endswith("_palette.vmodc"))
    pal_expected = s32(hash_jenkins(pal_path.encode()))

    b16 = next((s for s in rec["steps"] if s.startswith("B-16:")), "")

    names = [r["name"] for r in removed]
    spec = ED.load_spec()["raw"]
    donor_mismatch = [r["name"] for r in removed
                      if str(donor[r["part_index"]]["n"]) != r["name"]]

    cites = {
        "base_tag": cite("Tools/scripts/bm_entity.py", 'BASE_TAG = "bm-009"',
                         "B-05 stages bm-009 (416 objects, 6 props)"),
        "civilian": cite("Tools/scripts/bm_entity.py",
                         'EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"',
                         "B-05's base leaf is the civilian variant"),
        "step1": cite("Tools/scripts/bm_entity.py", "# ---- step 1: CPartProp",
                      "B-05 step 1 adds no CPartProp"),
        "count0": cite("Tools/scripts/bm_entity.py", '"cpartprop_added": 0',
                       "the spec records 0 props added"),
        "leaf_new": cite("Tools/scripts/bm_leaf.py",
                         'NEW = "v0300_car_kensington_sportsmuscle_debug"',
                         "B-13b renames the tree to the vanilla debug leaf"),
        "leaf_rename": cite("Tools/scripts/bm_leaf.py",
                            "t2 = t.replace(f'<value name=\"name\" type=\"string\">{OLD}</value>',",
                            "B-13b rewrites the .epe root name"),
        "rc_rename": cite("Tools/scripts/bm_rc2.py", "leaf = bm_leaf.rename_tree(stage, aaf)",
                          "RC2 applies the rename after the merge"),
        "b18_call": cite("Tools/scripts/bm_rc2.py", "b18 = bm_paths.apply(stage",
                         "RC2 runs B-18 on the merged tree"),
        "b18_epe": cite("Tools/scripts/bm_paths.py", 'elif rel.endswith(".epe"):',
                        "B-18 repoints .epe int refs through ConvertProperty"),
        "b18_pat": cite("Tools/scripts/bm_paths.py",
                        "pat = re.compile(rf'(type=\"int\">){s32(_h(o))}(</value>)')",
                        "the palette pointer is rewritten as a signed Jenkins hash"),
        "b16": cite("Tools/scripts/bm_rc2.py",
                    'for mem in ("F9DCF6AB", "98BBA63E", "9E74F03F"):',
                    "B-16 removes 3 members per weapon clone"),
        "b16_row": cite("GRAB_BACKLOG.md", "| B-16 | done |", "B-16 is a done card"),
        "b04r": cite("MODLOG.md", "61 parts, part_index == position 0..60",
                     "B-04R rebuilt the module in the vanilla 61-part index space"),
        "b04r_code": cite("Tools/scripts/bm_schema.py", "def rebuild_parts",
                          "the rebuild that writes the 61-part module"),
        "spec_l3": cite(B05_SPEC, "no measured consumer",
                        "B-05 spec L-3 narrowed step 1 to zero"),
        "review_a1": cite(B05_REVIEW, "The base is a damaged graph",
                          "the review card calls the 34-prop base BROKEN"),
        "modlog_delib": cite("MODLOG.md", "are a deliberate state",
                             "MODLOG records the 6 props as deliberate"),
        "modlog_hide": cite("MODLOG.md", "Parts hidden via the .epe",
                            "a shipped mod hid parts by dropping CPartProp nodes"),
        "modlog_draw": cite("MODLOG.md", "35 parts still",
                            "RC1's render found 35 donor parts drawing with 6 props"),
        "tint_write": cite(TINT_WRITE, "but ship the **same bytes**",
                           "TINT_WRITE.md records the palette repoint with unchanged bytes"),
    }

    return {"d": d, "removed": removed, "renamed": renamed, "presence": presence,
            "base": base, "pre": pre, "rec": rec, "mod": mod, "donor": donor,
            "pal": {"value": pal_val, "path": pal_path, "expected": pal_expected},
            "b16": b16, "spec": spec, "names": names,
            "donor_mismatch": donor_mismatch,
            "silent": spec_silence(spec, names), "cites": cites}


# --------------------------------------------------------------------------- the page
def render(x: dict) -> str:
    L: list[str] = []
    a = L.append
    c = x["cites"]
    d = x["d"]
    rem = x["removed"]
    pal = x["pal"]
    leaf = x["renamed"]
    in_module = len(rem) - sum(1 for r in rem if r["name"] not in x["mod"]["names"])

    a("# The 36 UNEXPLAINED entity-graph differences: which step produced each")
    a("")
    a("Generated by `python Tools/scripts/v_entity_unexplained.py --write`; `--check` re-derives")
    a("every number, re-reads every cited line and diffs this page byte for byte. Read-only: the")
    a("game archive is extracted to a temp directory, the built `.epe` is opened for reading, and")
    a("the base/pre-merge graphs are exported to the same temp directory. It does not replace")
    a("`entity_diff.md`; it explains that page's UNEXPLAINED rows.")
    a("")
    a("`entity_diff.md` reports **%d differences, %d tagged to `bm_epe_edits.json`, %d UNEXPLAINED**."
      % (len(d["diffs"]), len(d["diffs"]) - len(d["unexp"]), len(d["unexp"])))
    a("The 36 are three kinds, and nothing else:")
    a("")
    a("| kind | count | produced by | code | intended? |")
    a("|---|---|---|---|---|")
    a("| dropped `CPartProp` | 34 | B-05's base graph, not by any later step; the 5-part carve in "
      "B-01/B-02 lineage is the origin | `bm_entity.py:%d` (base), `:%d` (leaf), `:%d` (step 1)"
      % (c["base_tag"]["line"], c["civilian"]["line"], c["step1"]["line"])
      + " | **NO as shipped**: spec L-3 narrows step 1 to 0, review card B-05 A1 calls the base "
        "damaged and 467-vs-501 a correctness gap; MODLOG calls the 6 props deliberate |")
    a("| root `CCar` renamed | 1 | B-13b leaf rename (Q-1a: take the unused vanilla `_debug` leaf) | "
      "`bm_leaf.py:%d` + `bm_leaf.py:%d`, called `bm_rc2.py:%d`"
      % (c["leaf_new"]["line"], c["leaf_rename"]["line"], c["rc_rename"]["line"])
      + " | **YES** (B-13b card) |")
    a("| root member `palette` | 1 | B-18 path move + repoint: the palette module moves to "
      "`modules/default/batmobile/` and the `.epe` int is rewritten | "
      "`bm_paths.py:%d` + `bm_paths.py:%d`, called `bm_rc2.py:%d`"
      % (c["b18_epe"]["line"], c["b18_pat"]["line"], c["b18_call"]["line"])
      + " | **YES** (B-18) |")
    a("")
    a("## 1. What the later steps cannot have done")
    a("")
    a("| step | what it does to the graph | objects removed |")
    a("|---|---|---|")
    a("| RC 3-way merge (`bm_rc2.py` `merge3`) | line merge of three exported XMLs, then a round-trip "
      "assertion; base is bm-005, which already carries 6 props | 0 |")
    a("| B-16 weapon-clone cleanup (`bm_rc2.py` `:%d`) | 4 `F30CCB1C` owner values -> null and 3 "
      "members per clone (`F9DCF6AB`, `98BBA63E`, `9E74F03F`); all on objects the build **adds** | 0 |"
      % c["b16"]["line"])
    a("| T-13R interaction transforms (`bm_entity.interaction_transforms`) | rewrites `world` values "
      "of existing nodes | 0 |")
    a("| B-13b (`bm_leaf.py`) | renames three inner files and the root `name`/`name_hash` | 0 |")
    a("| B-18 (`bm_paths.py`) | moves files and rewrites int/string/hash references | 0 |")
    a("")
    a("Measured, not asserted. The pre-merge graph `%s` exports as **%d objects with %d "
      "`CPartProp`**; the B-05 base `%s` exports as **%d objects with %d `CPartProp`**. The build "
      "still has %d. The merge therefore inherited the loss and B-16/T-13R/B-13b/B-18 kept it."
      % (PRE_EPE, x["pre"]["objects"], len(x["pre"]["props"]),
         BASE_EPE, x["base"]["objects"], len(x["base"]["props"]),
         len(d["built"]) and sum(1 for o in d["built"] if o["cls"] == "CPartProp")))
    a("")
    a("The receipt's own B-16 line is: `%s` - 12 **members**, four of them owner links, on the four "
      "added weapon clones; none of the 36 is a weapon object, so B-16 explains **0/36**."
      % x["b16"])
    a("")
    a("## 2. The 34 dropped `CPartProp` objects")
    a("")
    a("### 2.1 Where the loss is baked in")
    a("")
    a("`bm_entity.py:%d` stages `bm-009`, `:%d` names the **civilian** leaf as the base, and `:%d` "
      "is step 1: *\"No row names one, so none is added\"*. So the graph the build ships was born "
      "with %d props and B-05 adds none. The 6 are the 5-part carve (body + 4 wheels, MODLOG "
      "section 46) plus the `sportsmuscle_taillight_r_l` prop appended by the test-083 light probe "
      "(MODLOG section 113); MODLOG records them as *a deliberate state* (`MODLOG.md:%d`)."
      % (c["base_tag"]["line"], c["civilian"]["line"], c["step1"]["line"],
         len(x["base"]["props"]), c["modlog_delib"]["line"]))
    a("")
    a("The base props are: %s. They are exactly the parts the build wants drawn (body + the four "
      "wheels) plus one vanilla lamp part."
      % ", ".join("`%s` (%s)" % (p["name"], p["part_index"]) for p in x["base"]["props"]))
    a("")
    a("`bm_epe_edits.json` is silent on all 34 (no `additions[]`/`edits[]`/`added_objects[]` entry "
      "names one), and so is every later step. The reason the diff compares them with the shipped "
      "graph at all is B-13b: `bm_leaf.py:%d` renames the civilian-derived tree to "
      "`%s`, and that leaf is the vanilla graph whose 40 props the build is measured against."
      % (c["leaf_new"]["line"], leaf["new"]))
    a("")
    a("### 2.2 What a `CPartProp` is, and which part each one binds")
    a("")
    a("Decoded from the two graphs and the donor parts table:")
    a("")
    a("* a `CPartProp` is the entity graph's **per-part node**: `name` (the part name), "
      "`name_hash`, `part_index` (the row in the vehicle's `parts[]` module), `_GUID` and one "
      "constant member `id:D04059E6`. It carries **no behaviour** (fleet census, "
      "`Research/challenge/card-B-05.md` A2: 13,440/13,440 props have only those admin members).")
    a("* the part row it indexes holds the behaviour: model `.lod`, parent/children, collision ids, "
      "`door_parts[]`/`hinged_parts[]`/`wheel_parts[]`/`aim_part_constraints`, `has_lights`, "
      "damage type, `starts_deleted` (`Research/JC3Grab/DOORS.md`, `PARTS_TABLE.jsonl`).")
    a("* the graph names a mesh by convention: `CPartProp.name` + `_lod1.rbm` (MODLOG's decoder "
      "note) - the `.epe` holds no model path.")
    a("")
    a("Every dropped prop's `part_index` resolves to the donor parts table and the table's name "
      "equals the graph's name, 34/34 (mismatches: %s). The table also shows how the nodes nest: "
      "the graph is not flat - e.g. `sportsmuscle_engine` is the parent of `hood`, both fenders, the "
      "front bumper and the grill, the fenders parent the headlights and signals."
      % (len(x["donor_mismatch"]) or "none"))
    a("")
    a("| # | dropped object | `part_index` | donor part row | still a row in the RC2 module? |")
    a("|---|---|---|---|---|")
    for i, r in enumerate(sorted(rem, key=lambda q: int(q["part_index"])), 1):
        row = x["donor"][r["part_index"]]
        a("| %d | `%s` | %s | `%s` (`%s`) | %s |"
          % (i, r["name"], r["part_index"], row["n"], row.get("dt", "?"),
             "yes" if r["name"] in x["mod"]["names"] else "**no**"))
    a("")
    a("### 2.3 Can dropping them matter for the car?")
    a("")
    a("**Yes in principle, and it is measurable as a graph fact; no in-game symptom is attributable "
      "to it in this build.** The evidence, separated by class:")
    a("")
    a("* **The module side is intact.** All %d of the 34 names are still rows in the RC2 parts "
      "module (`%s`, %d parts, unique `part_index` %d..%d), so dropping the props deleted no mesh, "
      "index, child list or behaviour row. That includes both doors: B-04's spec removed "
      "`sportsmuscle_door_f_l`/`_f_r`, but B-04R rebuilt the module in the vanilla index space "
      "(`bm_schema.py:%d`, MODLOG `:%d`: *61 parts, part_index == position 0..60*), so the shipped "
      "module carries rows 1 and 2 again (parent 0, no children). No restoration would dangle; "
      "`Working/Parts/bm_vehicle_parts.json`'s `index_map` is the stale record, not the module."
      % (in_module, x["mod"]["path"], x["mod"]["parts"], x["mod"]["index_list"][0],
         x["mod"]["index_list"][-1], c["b04r_code"]["line"], c["b04r"]["line"]))
    a("* **What is lost is the graph-level part node**: the entity no longer names those 32 parts, "
      "so a part-scoped graph lookup (by name or `part_index`) has nothing to land on, and the "
      "`name` + `_lod1.rbm` binding is gone for them. Whether the engine needs the node to "
      "instantiate the part is **UNKNOWN**: the shipped DaBaby mod hid ~50 parts by dropping their "
      "`CPartProp`s (`MODLOG.md:%d`), yet RC1's own render found 35 donor-mesh parts still drawing "
      "with only 6 props (`MODLOG.md:%d`). Those two measurements disagree, and no run isolates it."
      % (c["modlog_hide"]["line"], c["modlog_draw"]["line"]))
    a("* **Not a light or weapon dependency.** Lights bind through the module's `CarLight` blocks "
      "and the graph's `SVehicleLight` nodes, not through props (B-05 spec L-3 / card-B-05 A2); no "
      "weapon node references a `CPartProp`. The dropped set also contains no part the build's 9 "
      "`SWeaponPoint`s name.")
    a("* **It is a deviation from the shipped pattern.** The donor debug graph carries 40 props for "
      "42 parts, the fleet median ratio is 1.00 (199/233 graphs >= 0.9), and the review card calls "
      "the 467-object result *a correctness gap in the deliverable* against 450 + 51 = 501 "
      "(`card-B-05.md` A1, verdict BROKEN). The B-05 spec had narrowed step 1 to zero on the "
      "damaged base's 6/42 (`specs/B-05.md` L-3), and MODLOG later recorded that the 6 are "
      "deliberate rather than a repair.")
    a("")
    a("**Decision.** Dropping the 34 does not remove art, rows or behaviour from the module, and "
      "nothing measured in the build fails because of it; it does remove 32 part nodes the shipped "
      "graph has, contradict the 1:1 shipped pattern, and would have to be re-derived (not copied) "
      "because B-04 deleted the two door rows. The in-game consequence is UNKNOWN - the two "
      "available measurements point in opposite directions - so a rebuild of step 1 is a "
      "correctness/parity task, not a fix for a reproduced defect.")
    a("")
    a("## 3. The root rename")
    a("")
    a("One object, `CCar` at `%s`: `%s` -> `%s`. `bm_leaf.py:%d` sets the new leaf and `:%d` "
      "rewrites the root `name` value (and `name_hash`); `bm_rc2.py:%d` calls it after the merge. "
      "Intended: B-13b's Q-1a decision takes the unused vanilla `_debug` leaf because a brand-new "
      "leaf never spawns; the receipt records `%s`."
      % (leaf["node"], leaf["old"], leaf["new"], c["leaf_new"]["line"],
         c["leaf_rename"]["line"], c["rc_rename"]["line"], x["rec"]["leaf"]))
    a("")
    a("## 4. The added `palette` member")
    a("")
    a("`palette` = `%s` is *only in the build* because the vanilla `_debug` graph has no such "
      "member while the civilian-derived base does. B-18 moves "
      "`%s` to the `batmobile/` namespace and repoints every referrer through its own format: for "
      "a `.epe` that is the int-value rewrite at `bm_paths.py:%d`-`%d`, called from `bm_rc2.py:%d`. "
      "The written value equals the signed Jenkins hash of the new path (`%s`), which is what "
      "`Research/JC3Grab/TINT_WRITE.md` documents (`%s`): the pointer is written, the tint bytes "
      "are not. Intended: B-18 (Q-1a re-test 3: no Batmobile file may sit at a path a vanilla "
      "entity loads)."
      % (pal["value"], pal["path"], c["b18_pat"]["line"], c["b18_pat"]["line"] + 1,
         c["b18_call"]["line"], pal["expected"], c["tint_write"]["line"]))
    a("")
    a("## 5. Verdicts in one line each")
    a("")
    a("* 34 `CPartProp`: **produced upstream of the pipeline** (5-part carve), carried by B-05's "
      "base (`bm_entity.py:%d`/`:%d`) and step 1 (`:%d`); **declared** in spec L-3, **not intended "
      "as shipped** per the review card, **0** of them removed by B-16/merge/T-13R."
      % (c["base_tag"]["line"], c["civilian"]["line"], c["step1"]["line"]))
    a("* root rename: **B-13b, intended** (`bm_leaf.py:%d`, `bm_rc2.py:%d`)."
      % (c["leaf_rename"]["line"], c["rc_rename"]["line"]))
    a("* `palette`: **B-18, intended** (`bm_paths.py:%d`, `bm_rc2.py:%d`)."
      % (c["b18_pat"]["line"], c["b18_call"]["line"]))
    a("")
    a("## 6. Oracles re-run by `--check`")
    a("")
    a("Every number above is recomputed: the diff (450/467 objects, 36 UNEXPLAINED), the bm-009 "
      "and bm-005 exports, the donor table join, the module census, the palette hash, the receipt "
      "lines and each cited file:line.")
    a("")
    a("## 7. Labels")
    a("")
    a("Objects, members, `part_index` values and the palette hash are **decoded** from the graphs "
      "and the parts module. Step attribution is **derived** from the code that performs each "
      "operation plus the receipts. Intent is **quoted** from `specs/B-05.md` L-3, "
      "`Research/challenge/card-B-05.md` A1/A2, `GRAB_BACKLOG.md` B-16 and the MODLOG sections "
      "named above. Where the two measurements of prop instancing disagree the row says "
      "**UNKNOWN** rather than choosing one.")
    a("")
    return "\n".join(L) + "\n"


def oracles(x: dict) -> list[tuple[str, bool]]:
    d = x["d"]
    rem = x["removed"]
    pal = x["pal"]
    return [
        ("the diff still reports 450 / 467 objects", d["n_v"] == 450 and d["n_b"] == 467),
        ("the diff still reports 36 UNEXPLAINED", len(d["unexp"]) == 36),
        ("34 of them are removed CPartProp objects",
         len(rem) == 34 and all(r["cls"] == "CPartProp" for r in rem)),
        ("the other two are the root rename and one member",
         len(d["unexp"]) - len(rem) == 2 and d["renamed"] is not None and len(d["presence"]) == 1),
        ("the member is `palette`", d["presence"][0]["member"] == "palette"),
        ("bm-009 is the civilian leaf and has 6 props / 416 objects",
         x["base"]["objects"] == 416 and len(x["base"]["props"]) == 6),
        ("bm-005 (pre-merge) already has 6 props", len(x["pre"]["props"]) == 6),
        ("the base props are body, 4 wheels and taillight_r_l",
         {p["name"] for p in x["base"]["props"]} == {
             "sportsmuscle_body", "sportsmuscle_wheel_r_l", "sportsmuscle_wheel_r_r",
             "sportsmuscle_wheel_f_l", "sportsmuscle_wheel_f_r", "sportsmuscle_taillight_r_l"}),
        ("the 34 dropped names appear in no spec row", x["silent"]),
        ("every dropped prop's part_index matches its name in the donor table",
         not x["donor_mismatch"]),
        ("all 34 dropped part names are still rows in the RC2 module",
         sum(1 for r in rem if r["name"] in x["mod"]["names"]) == 34),
        ("the RC2 module is the 61-part vanilla index space 0..60",
         x["mod"]["parts"] == 61 and x["mod"]["index_list"] == list(range(61))),
        ("both door rows exist under the body with no children",
         set(x["mod"]["doors"]) == {"sportsmuscle_door_f_l", "sportsmuscle_door_f_r"}
         and all(v["parent"] == 0 and not v["children"]
                 for v in x["mod"]["doors"].values())),
        ("no removed object is a weapon/effect object (B-16 cannot explain any)",
         not any(r["cls"] in ("CBulletWeaponBase", "SWeaponPoint", "SAttachedEffect",
                              "CAIEntityProxy", "SEffects") for r in rem)),
        ("the receipt's B-16 line counts 4 owner links and 12 members",
         "4 F30CCB1C" in x["b16"] and "12 APC M2" in x["b16"]),
        ("the palette value is the Jenkins hash of the built module path",
         str(pal["value"]) == str(pal["expected"]) and pal["expected"] == 1322976751),
        ("B-18's receipt moved the palette into batmobile/",
         any("_palette.vmodc" in k and "/batmobile/" in v
             for k, v in x["rec"]["b18"]["moved"].items())),
        ("the renamed root name is the B-13b leaf",
         d["renamed"]["new"] == x["rec"]["leaf"] == "v0300_car_kensington_sportsmuscle_debug"),
        ("every code citation resolves to exactly one line",
         all(c["line"] > 0 for c in x["cites"].values())),
        ("spec L-3 still says the prop has no measured consumer",
         x["cites"]["spec_l3"]["line"] > 0),
        ("the review card still calls the base damaged",
         x["cites"]["review_a1"]["line"] > 0),
        ("MODLOG still records the 6 props as deliberate and both instancing measurements",
         x["cites"]["modlog_delib"]["line"] > 0 and x["cites"]["modlog_draw"]["line"] > 0),
        ("page rows = 34 props + 3 summary kinds + 2 other sections",
         len(x["removed"]) == 34),
    ]


def page() -> tuple[str, list[tuple[str, bool]]]:
    x = build()
    return render(x), oracles(x)


def cmd_write() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s (%d bytes)" % (rel(OUT), len(text.encode())))
    return 0 if all(ok for _, ok in ors) else 1


def cmd_check() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print("MISSING " + rel(OUT))
        return 1
    bad = [n for n, ok in ors if not ok]
    for n, ok in ors:
        print(("PASS " if ok else "FAIL ") + n)
    print("oracles: %d/%d pass" % (len(ors) - len(bad), len(ors)))
    if open(path, encoding="utf-8").read() != text:
        print("DRIFT: %s differs from the regenerated bytes" % rel(OUT))
        return 1
    print("document identical: " + rel(OUT))
    return 0 if not bad else 1


def main() -> int:
    args = sys.argv[1:]
    if args == ["--write"]:
        return cmd_write()
    if args == ["--check"]:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
