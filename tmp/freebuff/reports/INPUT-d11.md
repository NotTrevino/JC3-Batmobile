# INPUT-d11 — battle-mode toggle / immobilizer / eject against the JC3 keymaps and vehicle modules

STATUS: done

All three D-11 actions are **UNKNOWN** under the brief's rule ("report only a hit with a
consumer"), and each for a different, stated reason. Nothing JC3-side binds them to a car.

| D-11 action | keymap action a car could receive | consumer in a vehicle module | answer |
|---|---|---|---|
| battle-mode toggle | **none** — 0 of 154 action names match `BATTLE\|PURSUIT\|TRANSFORM\|MODE$` | 0 hits in 134 files | **UNKNOWN** |
| immobilizer | `USE_ITEM` (gamepad `RPADUP`, keyboard `E`, id `C0EC1595`) | 0 hits in 134 files | **UNKNOWN** |
| eject | **none** — 0 names match `EJECT\|LAUNCH\|CATA.?PULT` | 0 hits in 134 files | **UNKNOWN** |

The immobilizer is the only one with a name-level match, and it is exactly the case the brief
warns about: G3-08 mapped "B in track" to `USE_ITEM`, but `USE_ITEM` is a generic item action
and **no vehicle module references it** — not by its decoded binding id `C0EC1595`, not by
`H("USE_ITEM")`, not as a literal string. So the name match buys nothing.

## What was searched, and with what

- **Keymaps**: all four copies (`settings/keymap_gamepad.bin` base+patch,
  `settings/keymap_keyboard.bin` base+patch), parsed with G3-08's own
  `jc3_input.read_entries` + `parse_keymap` (read-only import). Result: **474 bindings, 154
  actions**, layer `patch` — identical to `INPUT.md`'s decoded counts, which is an oracle.
- **Vehicle modules**: every `.epe`/`.vmodc` under `E:/Modding/_gamedata/JC3grab` —
  **207 files on disk, 134 distinct contents** (the rest are byte-identical copies under
  `rc_merge/` and `verify/`), covering **79 vehicles** (one per `*_vehicle_parts.vmodc`).
  Container census: 17 `RTPC` (`.epe`), 117 other (ADF `.vmodc`).
- **Hash**: `rbmhdr.hash_jenkins` (Jenkins lookup3), the same function G3-08 used.
- **Encodings searched per target**: the action **id** from the keymap node hash,
  `H(action name)`, and the literal name — each as u32 little-endian, u32 big-endian, decimal
  ASCII, upper/lower hex ASCII, and the raw name bytes.
- **Secondary**: the 232 entity `.ee` dumps, re-scanned for the three names and hashes
  (0 / 0 for all three).

## The structural finding

**No vehicle `.epe`/`.vmodc` carries *any* of the 154 keymap action ids, and none carries any
`H(action name)`** — 0 files for both. So the button→behaviour route is not a data member in
this file set: whatever routes a button to a car's behaviour is native to the engine or lives
in a container these decoders do not expose. That is the honest explanation of three UNKNOWNs
rather than three coincidences.

## Files written

- `Tools/scripts/jc3_input_d11.py` — new script, `--write` / `--check`.
- `Research/JC3Grab/INPUT_D11.md` — generated note (92 lines).
- `Research/JC3Grab/INPUT_D11.json` — generated data (keymap copies, search set, per-target
  forms/hits, controls, oracles, UNKNOWNs).
- `tmp/freebuff/reports/INPUT-d11.md` — this report.

Read-only inputs: the four keymap archive entries (`archives_win64/game*`,
`patch_win64/game4`), the 207 `.epe`/`.vmodc` files, the 232 entity dumps,
`Research/JC3Grab/INPUT.md` (cited, not edited), `jc3_input.py`, `rbmhdr.py`, `jc3index.py`.

## Values, labelled

| value | label |
|---|---|
| 474 bindings / 154 actions, patch layer, `USE_ITEM` = `RPADUP` / `E`, id `C0EC1595` | **decoded** (keymap archive entries, via `jc3_input.parse_keymap`) |
| `H("USE_ITEM") = C0EC1595`, equal to the decoded binding id | **derived** (`rbmhdr.hash_jenkins`; matches, so the hash method is the one G3-08 used) |
| 0 names match `BATTLE\|PURSUIT\|TRANSFORM\|MODE$` and `EJECT\|LAUNCH\|CATA.?PULT` | **derived** (regex over the decoded action set; same regexes INPUT.md used) |
| 207 files on disk / 134 distinct / 79 vehicles / 17 RTPC + 117 ADF | **derived** (walk + sha256 dedupe + magic census) |
| 0 hash hits in 134 module files for all three targets | **derived** (byte search over 5 encodings per hash) |
| 0 action ids / name-hashes in any module | **derived** (all 154 actions × 134 files) |
| root hash `AA7D522A` present in exactly the 17 RTPC files | **decoded** (positive control) |
| what battle mode / eject / immobilizer do in a car | **UNKNOWN** |

## Commands run (verbatim, abridged only where a command listed 96 rows)

1. Keymap action set + module-file discovery:

```
$ PYTHONIOENCODING=utf-8 uv run python - <<'PY'   ... I.parse_keymap over I.KEYMAPS; os.walk(RAW) ...
bindings parsed: 474 distinct actions: 154
battle  -> []
eject   -> []
immob   -> ['USE_ITEM']
    USE_ITEM             [('base', 'C0EC1595'), ('patch', 'C0EC1595')]
b13b\unpacked\...\v0300_car_kensington_sportsmuscle vmodc  1  eg batmobile_health_medium.vmodc
tmp vehicle_parts 78 eg advancedassault_vehicle_parts.vmodc
... (full walk printed 207 .epe/.vmodc files)
```

2. Hash values, file formats, and a first raw scan:

```
$ ... hash_jenkins over the three names; struct.pack; scan 207 files ...
USE_ITEM   H=C0EC1595 le=9515ecc0 dec=3236697493
BATTLE     H=DE12741E le=1e7412de dec=3725751326
EJECT      H=B754B21B le=1bb254b7 dec=3075781147
files: 207
-- b13b\cal.epe 115378 bytes, head: b'RTPC\x01\x00\x00\x00*R}\xaa\x14\x00\x00\x00...'
-- b13b\...\v0300_car_kensington_sportsmuscle_civilian_01.epe 105430 bytes, head: b'RTPC\x01...'
USE_ITEM hits: 0  []
BATTLE   hits: 0  []
EJECT    hits: 0  []
```

   (the `.epe` and `.vmodc` files are binary RTPC/ADF containers, not text: a "hash search"
   therefore had to cover raw u32 forms as well as ASCII, which the script does.)

3. First `--write`: crashed on a render key (`inputmd` vs `inputmd_row`), fixed.

4. Second `--write`/`--check`: the positive control failed because I had required the RTPC root
   hash in >100 files while only 17 files are RTPC at all:

```
oracles: {'positive_control_root_hash_found': False, ...}
write_exit=0
FAIL
  - oracle positive_control_root_hash_found failed: {"root_hash": "AA7D522A", "files_with_root": 17, "files_with_RTPC_magic": 17}
check_exit=1
```

   The control is now "every RTPC file contains the root hash, and there is at least one"
   (17 == 17), which is the property that fails if the byte search misses.

5. Final write and check:

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/jc3_input_d11.py --write; echo "write_exit=$?"; PYTHONIOENCODING=utf-8 uv run python Tools/scripts/jc3_input_d11.py --check; echo "check_exit=$?"
wrote INPUT_D11.md / .json
keymap: 474 bindings, 154 actions, active {'settings/keymap_gamepad.bin': 'patch', 'settings/keymap_keyboard.bin': 'patch'}
search: 207 files on disk, 134 unique, 79 vehicles
  battle-mode toggle   names=-            hits=0 name_hits=0 -> UNKNOWN
  immobilizer          names=USE_ITEM     hits=0 name_hits=0 -> UNKNOWN
  eject                names=-            hits=0 name_hits=0 -> UNKNOWN
controls: {'root_hash': 'AA7D522A', 'files_with_root': 17, 'files_with_RTPC_magic': 17}
oracles: {'keymap_parse_matches_g3_08': True, 'four_keymap_copies_tile': True, 'positive_control_root_hash_found': True, 'vehicle_parts_modules_found': True, 'use_item_id_is_H_of_its_name': True, 'no_vehicle_module_carries_any_action_hash': True, 'every_target_reports_a_reason': True}
write_exit=0
OK: 3 targets, answers ['UNKNOWN', 'UNKNOWN', 'UNKNOWN']; all oracles true
check_exit=0
```

## UNKNOWNs

1. **Battle-mode toggle** — no action name in any of the four keymap copies matches
   `BATTLE|PURSUIT|TRANSFORM|MODE$`, so there is nothing a module could receive. Whether the
   game switches modes through a keypath outside the keymap files is not decodable here.
2. **Eject** — likewise 0 names for `EJECT|LAUNCH|CATA.?PULT`; the D-11 "A" mapping has no JC3
   action in the decoded tables.
3. **Immobilizer** — `USE_ITEM` is bound and is the name G3-08 chose, but 0 of 134 vehicle
   modules reference its id or name-hash, so what it does inside a car is UNKNOWN. The BmAK
   side (`EMP`, G2-16) is not a JC3 action either.
4. **Naming a `.epe`/`.vmodc` property** — these containers store property hashes, not strings,
   and no decoder in this tree maps a `.vmodc` property hash to a member path by offset. Even a
   raw 4-byte hit could not be named, which is precisely why the brief's "hit with a consumer"
   rule can only be satisfied where a decoder exists. This pass found no hit to name.
5. **Why the link is absent** — the keymap→vehicle wiring is not a data member in any of the
   207 files. Where it lives (engine code, or a container not decoded here) is UNKNOWN and
   needs a runtime observation, not more file reading.
