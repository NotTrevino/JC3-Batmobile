# The 36 unexplained entity differences: cause, code line, intent

**Status: answered, 23/23 oracles PASS.** Page: `Builds/bm-RC2/verify/entity_unexplained.md`.
Checker: `python Tools/scripts/v_entity_unexplained.py --check` (re-derives the 36 from the game
archive and the built `.epe`, re-reads every cited line, byte-compares the page).

## Answer in one table

| kind | n | produced by | code line | intended? |
|---|---|---|---|---|
| dropped `CPartProp` | 34 | the graph B-05 starts from (bm-009, 416 objects / 6 props), which descends from the 5-part carve; **not** by any later step | `Tools/scripts/bm_entity.py:75` (base bm-009), `:77` (civilian leaf), `:301` (step 1 adds 0) | **No as shipped.** Spec L-3 narrowed step 1 to zero; review card B-05 A1 calls the 34-prop base damaged and 467-vs-501 a correctness gap. MODLOG calls the 6 props deliberate. |
| root `CCar` renamed | 1 | B-13b leaf rename (Q-1a: take the unused vanilla `_debug` leaf) | `Tools/scripts/bm_leaf.py:57` + `:122`, called `Tools/scripts/bm_rc2.py:320` | **Yes** (B-13b) |
| root member `palette` | 1 | B-18 path move: palette module -> `modules/default/batmobile/`, `.epe` int repointed | `Tools/scripts/bm_paths.py:105` + `:110`, called `Tools/scripts/bm_rc2.py:303` | **Yes** (B-18; `TINT_WRITE.md`: pointer written, tint bytes unchanged) |

## The negative: the later steps named in the brief explain none of the 36

Measured on every run, not asserted:

* **RC 3-way merge** (`bm_rc2.py` `merge3`) only merges lines of exported XML. Its base is bm-005,
  which already exports as **467 objects / 6 `CPartProp`**; bm-009 (B-05's base) is **416 / 6**. So
  the loss predates the merge and the merge added/removed no object.
* **B-16** (`bm_rc2.py:203`) removes 3 members (`F9DCF6AB`, `98BBA63E`, `9E74F03F`) per weapon clone
  plus 4 `F30CCB1C` owner values. The receipt line is exactly
  `B-16: 4 F30CCB1C owner links -> null, 12 APC M2 gun-body members removed (medium-tank convention)`
  - 12 **members** on objects the build *adds*. None of the 36 is a weapon/effect object: B-16
  explains 0/36.
* **T-13R** rewrites `world` values on existing nodes; **B-13b** renames files and the root
  `name`/`name_hash`; **B-18** moves files and rewrites references. None removes an object.

## CPartProp: what they are, which parts they bind, does dropping matter

Decoded facts:

* A `CPartProp` is the graph's per-part node: `name`, `name_hash`, `part_index` (row in the
  vehicle's `parts[]` module), `_GUID`, and one constant member `id:D04059E6`. It carries **no
  behaviour** - fleet census, `Research/challenge/card-B-05.md` A2: 13,440/13,440 props have only
  those admin members.
* The part row it indexes carries model `.lod`, parent/children, collision ids, `door_parts[]`,
  `hinged_parts[]`, `wheel_parts[]`, `aim_part_constraints`, `has_lights`, damage type,
  `starts_deleted`. The graph names the mesh by convention: `CPartProp.name` + `_lod1.rbm` (no model
  path in the `.epe`).
* All 34 dropped props resolve their `part_index` to the donor parts table with the same name,
  34/34. They are the donor's bodywork, interior and lamps: doors + windows, engine, fenders, hood,
  bumpers, grill, plates, mirrors, seats, steering wheel, trunk, signals, headlights, rear lamps.
  The 6 kept props are body (0), four wheels (11/12/26/27) and one lamp (`taillight_r_l`, 8).
* The module side is fully intact: the RC2 module is the **61-part vanilla index space 0..60** with
  all 34 names still present as rows (B-04R rebuilt it that way, `bm_schema.py:118`; MODLOG: *61
  parts, part_index == position 0..60*). Dropping the props deleted no mesh, index, child list or
  behaviour row. `Working/Parts/bm_vehicle_parts.json`'s `index_map` (doors removed) is stale
  relative to the shipped module: rows 1/2 exist again, parented to the body with no children.

Verdict: **it can matter as a parity/correctness gap, but no in-game symptom is attributable to it
in this build.** The graph loses the part node for 32 real parts (name + index + `_lod1.rbm`
binding), which is a deviation from the shipped 40-props-for-42-parts pattern (fleet median ratio
1.00; review card A1 = BROKEN). Whether the engine needs the node to instantiate a part is
**UNKNOWN**: a shipped mod hid ~50 parts by dropping their props (MODLOG), while RC1's own render
found 35 donor parts still drawing with only 6 props (MODLOG). Those two measurements disagree and
no run isolates it. It is not a light or weapon dependency (lights bind via `CarLight` blocks and
`SVehicleLight` nodes; no weapon names a `CPartProp`).

## Verification actually run

```
python Tools/scripts/v_entity_unexplained.py --check
-> oracles: 23/23 pass; document identical: Builds/bm-RC2/verify/entity_unexplained.md
```

Oracles cover: 450/467 objects, 36 UNEXPLAINED, 34 removed props, rename + palette as the other two,
bm-009 416/6, bm-005 467/6, base prop set, spec silence on all 34, donor-table join 34/34, 61-part
module 0..60, door rows, no weapon object among the 36, B-16 receipt counts, palette =
Jenkins(`.../batmobile/..._palette.vmodc`) = 1322976751, B-18 moved it, root name = B-13b leaf, and
every cited file:line (spec L-3, review card A1, MODLOG quotes, TINT_WRITE).

## Limitations

* Static measurement only: the game was not launched, so the behavioural effect of the missing
  props remains UNKNOWN (stated above from two conflicting measurements).
* The 36 are exactly the set `v_entity_diff.py` reports; this page explains that set and does not
  re-scope the diff (member *values* stay outside both).
* Intent is quoted from `Research/specs/B-05.md` L-3, `Research/challenge/card-B-05.md` A1/A2,
  `GRAB_BACKLOG.md` B-16 and the MODLOG sections named on the page; no intent was inferred.

## Files and revert

* new: `Tools/scripts/v_entity_unexplained.py`, `Builds/bm-RC2/verify/entity_unexplained.md`, this
  report, and one MODLOG section.
* read-only: the game archive (extracted to temp), the built `.epe`, bm-009/bm-005 graphs (exported
  to temp), the parts module, the parts table, the receipts.
* revert: delete the script, the verify page and this report; remove the MODLOG section. No build,
  install, dropzone or game file was written.
