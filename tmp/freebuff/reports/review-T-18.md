# Review — T-18 · Lights translation completion

**VERDICT: minor issues.** The card's machinery is sound: every Out path exists, `--check` passes
and is deterministic (re-renders both outputs and byte-compares them, then cross-checks the ledger),
the Done line is generated from the rig rather than typed, and every number I spot-checked traces to
the input file or recomputes from `rbmhdr.hash_jenkins`. What is wrong is interpretive: one reading
of the stripped headlight pair is presented as decoded when the data does not settle it, one of the
36 BmAK components has no numbers in the doc, and one sentence about "two spot components per head
socket" is false for `HeadLight2`. None of these breaks the card's Done line; the first one changes
what a builder will put in the car, so it should be fixed before B-03/B-05 read these rows.

Reviewed read-only. Nothing outside this report was written; no game launched; no commit; no secret read.

## Check output (verbatim)

```
> python Tools/scripts/t18_lights.py --check
PASS: 28 rows: 22 mapped, 6 named omissions, 0 sharing a lamp | targets 18 = 11 donor rows + 1 graph object + 6 custom | donor 21 rows / 22 objects | ledger 28/28
EXIT=0
```

Identical to the line recorded in `MODLOG.md` §"T-18 · Lights translation completion — done".
I did not re-run the three tamper tests: they require editing `Tools/` or `Research/` files, which
this review must not do. Their mechanism is verifiable by reading `check()` (it compares the
re-rendered md/json to disk and each row's cells/disposition to `T_ROWS.jsonl`).

## Card, outputs and evidence row

| item | state |
|---|---|
| card `Done:` (GRAB_BACKLOG.md:939-946) | every light entry of the rig (28) maps to an `SVehicleLight` or a named omission, forensics rig out |
| `Out:` json | `Working/Translation/t14_lights.json` — exists, 99,696 B |
| `Out:` rows | `Working/Translation/T_ROWS.jsonl` — 28 rows with `doc == "T-14"` (14 `next`, 14 `out`) |
| doc named in §12 | `Working/Translation/T14_LIGHTS.md` — exists, 174 lines, generated |
| script | `Tools/scripts/t18_lights.py` — 1,257 lines, `--write`/`--check`/`show` |
| §12 row (GRAB_BACKLOG.md:1327) | matches the evidence file it names; counts agree with the doc |

Done ↔ check: `resolve()` iterates `load_entries()` (the 28 entries of `Playable_Batmobile_SF` in
`LIGHTS.json`), so one row per entry is structural rather than asserted; `assertions()` then pins
`entries=28`, `rows=28`, `mapped+omitted=28`, `mapped=22`, `omitted=6`, `rows with no target=0`,
`rows whose class is not decoded/derived=0`. That is exactly the card's Done line, and the
forensics exclusion is real (T-L21…T-L23 carry `forensics-rig` and cite the card). **Done is met.**

## Issues

### 1. The stripped headlight pair is read as a second road cluster — an inference labelled `decoded`

`Working/Translation/T14_LIGHTS.md:35`, `:58`, `:59` (and `MODLOG.md:12773-12775`).

`LIGHTS.json` entry 3/4 (`HeadLight1`/`HeadLight2`, type stripped) carry **LightColor 223,91,75, B 1.0,
cone -/44.0, R 1024.0** — a warm orange. The doc maps them to the donor's second head cluster
(`Front_Left_Point`+`Front_Left_Volumetric`, `Front_Right_*`) and adopts
`diffuse 0.875,0.357,0.294` (the /255 arithmetic is right: 223/255=0.8745, 91/255=0.3569,
75/255=0.2941). The consequence the doc never states: **one white and one orange beam per side**
(T-L8/T-L9 adopt 0.541,0.773,0.965 and 0.627,0.706,1.000), with a third, red cluster from T-L18/T-L19
on the same socket.

The data does not settle that role. In the same rig the battle-mode head pair is 255,0,0 at B 5.0
(entries 10/11) and the forensics pair is 255,0,0 with alpha 255 (entries 14/15); the stripped pair is
the only warm-tinted "HeadLight" in the rig, which is at least as consistent with a battle/damage
state whose `VEHLT_*` type was not cooked as with a second colour of road beam. `§6 What the files do
not say` lists five UNKNOWNs and none of them is this. Since the row's class column says `decoded`,
a reader takes the two-tone headlight as a decoded fact.

Fix (small): keep the numbers, and either move the "second cluster" reading into the proposal with
the alternative named, or add it to §6 as an UNKNOWN; the same sentence in `MODLOG.md` should not
assert "The donor already has two head clusters per side" as established.

### 2. One of the 36 BmAK components has no numbers in the doc

`Working/Translation/T14_LIGHTS.md:55` (T-L8) reports `B 0.15 cone 20.0/70.0 R 6000.0`.
Entry 0 has **three** components: `SpotLightComponent` (B 0.15, cone 20/70, **R 6000.0**),
`LensFlareComponent`, and a second `SpotLightComponent` (B 0.15, cone 20/70, **R 1800.0**) —
same colour, a second beam at a third of the reach. The second spot appears nowhere: the cell prints
one, and `t14_lights.json` row `T-L8` has `bmak.radius_ue = 6000.0` only (no field for the second).

The header row says "BmAK components behind the rows | 36", so a reader expects all 36 accounted for;
one is not. The card's Done line counts *entries*, so this does not fail the card — but it is data
the build will need (a low/high beam pair or a near spill) and the row's proposal gives the entry one
cluster.

### 3. "Two `SpotLightComponent`s on each head socket" is false for `HeadLight2`

`MODLOG.md:12774` and `T14_LIGHTS.md:35` ("the two BmAK spot components per socket take one cluster
each"). Measured: `HeadLight1` (entry 0) has two spot components; `HeadLight2` (entry 1) has **one**
(B 0.0, cone 10/35, R 0.1). The per-side symmetry the sentence claims is not in the data, which
matters because the "typed entry → `_01`, stripped entry → `_02`" pairing is justified by it.

### 4. `Front_Secondary_Head` = the battle-mode spot is asserted, not shown

`T14_LIGHTS.md:27`: "`Front_Secondary_Head` is the second one, and it is exactly the battle-mode
spotlight T-L5 named". The object's own values (`entity.xml`): `diffuse 0.6039,0.6039,0.9529,
radius 10, spot_angle 60, spot_inner_angle 0, multiplier 1, enabled 1` — i.e. the same colour as the
ordinary `Sport_Muscle_Headlight_*` presets (0.604,0.604,0.953) at a normal 60° cone, while the BmAK
battle spot is 5°/15° at R 4500 in white. The support is T-L5's earlier naming plus "no row uses it",
which is a name/absence match (the R5 trap), not a decode. The row itself is honest (its `now` column
cites T-LG2, its class carries the Q-1 probe), so this is a prose fix: "proposed (T-L5's
identification, unproven; alternative: a second headlight spill)".

### 5. R11 nit — a typed number in the renderer

`Tools/scripts/t18_lights.py:932` writes `(129 across the 4 rigs, G1-17)` as a literal, so `--check`
cannot catch it going stale. Today it is correct — 36 (`Playable_Batmobile_SF`) + 21 (Joker) + 36
(MK2) + 36 (Funhouse) = 129 — but it is the one number in the output the tool does not derive.
By contrast "25 members" is pinned by an assertion and "3,217" is cited from
`LIGHT_SYSTEM.json digest` (33 occurrences), so those are fine.

### 6. Cosmetic — doubled separator in the attachment cell

`T14_LIGHTS.md:55,58,59,63,…`: `sportsmuscle_body · ·sportsmuscle_LOD1·body·…`. `cell_attachment`
(`t18_lights.py:614`) replaces `|` with `·` on a string that already starts with `|`, leaving a
leading dot after the separator. Display only.

### 7. Observation (not an error) — four mapped lamps ship switched off

`T-L9` (R 0.1), `T-L13`/`T-L14` (B 0.0, R 0.0) and `T-L20` (B 0.0) come from BmAK components that are
effectively off, and the rows report those numbers faithfully (B and R are not converted, as §6 says).
But no row says "BmAK ships this lamp off", while the probes expect a glow ("the arch lamp glows with
the lights on", T-L13). One sentence per affected row would stop a builder reading the custom entry's
`range 2 / angle 10` as a replacement for a working BmAK lamp when the source lamp has R 0.0.

## Spot-checks (value → where verified)

| # | value in the doc | verified against | result |
|---|---|---|---|
| 1 | T-L8 `LightColor 138,197,246,255` → proposed `diffuse 0.541,0.773,0.965` | `Research/BatmobileGrab/LIGHTS.json`, `Playable_Batmobile_SF` entry 0 component 0 `colour.value` | match; 138/255=0.5412, 197/255=0.7725, 246/255=0.9647 |
| 2 | custom `sportsmuscle_wheel_f_l_arch`: `behavior_hash 3460580079`, `part_hash 571525670`, `deformable_transform_hash 3050336140` | `Tools/scripts/rbmhdr.hash_jenkins` recompute on `HeadLight`, `sportsmuscle_wheel_f_l_arch`, `\|sportsmuscle_LOD1\|wheel_f_l\|Wheel_Frnt_Left_Disc\|Wheel_Frnt_Left_Disc_LIG` | all three equal, exact |
| 3 | custom recipe `range 2`, `angle 10`, `falloff_start 0`, `near_cap 1`, `multiplier 1`, `projected_texture_index -1` | `Working/Lights/v082/lights.xml` → `paths(instances/instance)` keys `lights[2].*` (21 rows × 25 members) | all match, incl. 25 members per row |
| 4 | `part_index 42` (arch part), "42 records 0..41" | `Research/JC3Grab/PARTS_TABLE.jsonl` → `v0300_car_kensington_sportsmuscle_civilian_01.ee` | 42 parts, indices 0..41 contiguous, so 42 is the next free |
| 5 | "18 distinct targets = 11 donor rows + 1 graph object + 6 custom" | recomputed from `t14_lights.json` rows/targets | 18 distinct names; 11 distinct donor rows = 2,7,8,11,12,13,14,17,18,19,20; 1 `Front_Secondary_Head`; 6 custom |
| 6 | "20 of the 21 row presets resolve", orphan `3358775008` = row 3 `taillight_r_c` | module `preset_id` list vs graph `name_hash` set | 20 resolve; `lights[3]` preset 3358775008 has no object, part `sportsmuscle_taillight_r_c` |

Also verified while reviewing (no issue found): every donor mapping named in the rows — rows 13/8 on
`headlight_f_l_01`, 19/20 on `headlight_f_r_01`, 17/12 on `headlight_f_l_02`, 11/14 on
`headlight_f_r_02`, 18/7 on `signal_r_l`/`signal_r_r`, 2 = `Dash_Light`; `Rear_Break` and
`Front_Secondary_Head` are the only unreferenced objects; 22/22 object names rebuild from their hash;
`preset_id 0` traces to `Research/JC3Grab/LIGHT_SYSTEM.json /module/presets/zero = 17` (a fleet
count, not a local one — correctly labelled `decoded`).

## What is sound

- **Derivation (R11):** the doc is rendered from `build()`, not hand-written; summary values I
  recomputed independently agree (28 entries, 22/6, 18 targets, 14 colours adopted, 36 components,
  21 module rows, 22 objects, 9 fleet behaviours, 2 unreferenced, 1 unresolved preset). 21 assertions
  run in `--check`; `--check` byte-compares both outputs and every row's cells + disposition against
  `T_ROWS.jsonl`.
- **Provenance (R4):** no `assumed` class anywhere; the UE→JC3 unit gap is explicit (§6 items 3) and
  the shipped JC3 numbers are kept instead of converting; cone/brightness printed side by side; the
  new part indices and the "needs the §101b re-encode" caveat are stated rather than glossed.
- **Behaviour vs member (R5):** JC3 behaviours are taken from the BmAK entry
  (`entry["behavior"]`), not from a same-sounding JC3 member, and the TailLight/HeadLight behaviour of
  each donor row is printed. The one name-driven pick is issue 4.
- **Outputs:** both Out paths exist, the rows are in the ledger under doc `T-14`, and §12's evidence
  cell matches the file set.

## Recommended before B-03/B-05 consume these rows

1. Issue 1 (the stripped pair's role) — relabel as inference/UNKNOWN, or state the two-tone outcome.
2. Issue 2 — add `HeadLight1`'s second spot (R 1800.0) to T-L8 and to the json.
3. Issues 3-4 — correct the "two spots per socket" sentence and soften "exactly the battle-mode
   spotlight".
4. Issue 5-6 — derive the 129, drop the doubled separator (both cosmetic; a `--write` + `--check`
   cycle covers them).
