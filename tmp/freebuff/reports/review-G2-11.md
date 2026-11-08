# Review — G2-11 · Weapon wiring per armed vehicle

Independent review, 2026-10-28. Read-only: nothing under `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file was edited; this report is the only file written.

## VERDICT: minor issues

The card is substantially sound. The four questions it must answer are answered in the generated
doc, the numbers behind them re-derive from `WEAPON_WIRING.jsonl`, `--check` really does re-read
all 53 `.epe`s out of the archives (it took ~2 minutes and printed one line per entity), and every
spot-check I ran matched. Two real defects are in the generated document, and three smaller
provenance/typing weaknesses are worth fixing before anyone copies the prose into a build card:

1. a leaked Python f-string placeholder `{len(rows)}` in the published doc, from a string literal
   that is missing its `f` prefix — **the tool's own `--check` cannot catch it**, because it diffs
   the regenerated md against a md produced by the same bug;
2. a sentence that describes "the last row" of the driver-fired table as the cargo-plane variant,
   when the table's last row is an armoured jeep and the cargo plane is filtered out of that table
   entirely — again invisible to `--check`;
3. several counts typed into prose instead of derived (R11): "53", "30 components on 9 entities",
   "22 of 88 … 19 gunner weapons";
4. one negative claim with no artefact ("a 1.1-million-string vocabulary search"), and one
   interpretation stated as fact ("it is an AI/script turret").

Nothing in these invalidates the disabled/enabled slot model, the driver/gunner split, or the four
answers; they are documentation-quality defects in an otherwise well-evidenced card.

## Check output (verbatim)

`python Tools/scripts/jc3wiring.py --check` (abridged only where the 53 per-entity progress lines
repeat the same shape; the verdict line and the first/last entities are exact):

```
[1/53] v0200_car_capstone_apc_debug.ee: 1 weapons, 0 driver, 1 gunner
[2/53] v0200_car_capstone_apc_military_01.ee: 1 weapons, 0 driver, 1 gunner
...
[52/53] v4800_plane_brothers_vintagefighter_rebel_01.ee: 1 weapons, 1 driver, 0 gunner
[53/53] v5603_train_urga_monorailmissilecar_military_01.ee: 1 weapons, 0 driver, 0 gunner
PASS: 53 entities, 88 weapons, 81 bound, 7 unbound, 193 seats, md 2045 lines
exit=0
```

The per-entity lines are all of the form `[n/53] <entity>: <weapons> weapons, <driver> driver,
<gunner> gunner`, 53 of them, and the run ends in `PASS` with exit 0. It re-decodes from the
archives, not from the cached `E:/Modding/JustCause3/_grab/wiring/epe/` XML.

## Issues

### 1. Leaked f-string placeholder in the published doc — `Research/JC3Grab/WEAPON_WIRING.md:93`

The sentence reads:

> `Counts above are components and roots, not vehicles. The cargo-tank variant carries a full CCar (tank) next to its CAirPlane, so the {len(rows)} entities hold 54 root objects; …`

`{len(rows)}` is literal text. Cause: `Tools/scripts/jc3wiring.py:559-562` — the `a(...)` call opens
with an f-string, but the continuation string holding `{len(rows)}` has no `f` prefix:

```python
a(f"Counts above are components and roots, not vehicles. The cargo-tank variant carries a "
  "full `CCar` (tank) next to its `CAirPlane`, so the {len(rows)} entities hold "      # <- no f
  f"{sum(len(r['root_classes']) for r in rows)} root objects; …")
```

Why it matters beyond the cosmetic: it is direct evidence that `--check` validates *consistency*,
not *correctness*. The check regenerates the md from the same code and diffs it, so a generator bug
that produces wrong text passes. The neighbouring number (54 root objects) is derived correctly —
I re-derived it as `sum(len(root_classes)) = 54` over the 53 rows — so only the entity count is lost.

### 2. False statement about the driver-fired table — `Research/JC3Grab/WEAPON_WIRING.md:70`

> "The last row is the cargo-plane variant: its driver slots belong to the tank carried in its hold, not to the plane."

The table it follows ends at line 68 with `v0600_car_urga_armoredjeep_rebel_01.ee` — a gunner-only
armoured jeep — and the cargo plane (`v4603_plane_urga_cargotransport_military_cargo_tank.ee`)
**does not appear in that table at all**: `Tools/scripts/jc3wiring.py:447` and `:456-457` build the
table from `land = [r for r in rows if "CCar" in r["root_classes"] and "/01_land/" in r["entity"]]`,
which excludes the cargo plane because its path is not `01_land`. The cargo plane *is* in §4/§5 and
its two driver slots are counted in §3, so nothing is lost from the data — but the sentence is
wrong about the artefact it annotates, and a reader told to look at "the last row" will look at an
armoured jeep. Fixing it means deciding which is intended: drop the sentence, or add the cargo-plane
row under the `/01_land/` filter's exception.

### 3. Typed counts in generated prose (R11) — three instances

* `WEAPON_WIRING.md:27` "Across all 53 armed entities the maximum is 2" — the `53` is literal
  (`Tools/scripts/jc3wiring.py:470`), while the same sentence's `2` comes from `all_max`.
* `WEAPON_WIRING.md:95` "`CLightWeaponComponent` … (30 components on 9 entities)" — both numbers
  literal in the script; I re-derived them as 30 and 9, so they are right today.
* `WEAPON_WIRING.md:2029` "22 of 88 weapons carry a type-4 `MountAttach`: all 19 gunner weapons
  (two parts each)" — literal; re-derived 22 and 19, both right today.

Each is correct now, but each will silently go stale if the armed set or the decoding changes, and
`--check` will stay green because the literal regenerates identically. The rest of the file's
numbers are derived (`len(rows)`, `len({r['chassis'] …})`, `sum(wcls.values())`, …), which makes
these three stand out as the ones to convert.

### 4. A negative claim with no re-derivable artefact — `WEAPON_WIRING.md:16`

> "The 2nd driver slot resisted a 1.1-million-string vocabulary search (57 weapon/mount words in 2-
> and 3-word combinations, numeric suffixes); its id is the name of record."

The honest part — "no name found", `id:00568A74` as the name of record — is right and is what the
jsonl carries. The search itself is not reproducible from the repo: no word list, no script, no
result file. Under this project's own R4/§0.2 rule ("every value must be re-derivable by a
command") this should either be a scripted search with its artefact, or be worded as an
unsupported observation. It also cannot be verified by `--check`, which is why it survived.

### 5. Interpretation stated as fact — `WEAPON_WIRING.md:2031`

> "Its only weapon sits under a `CTurretWeaponComponent` and the entity exposes only `interaction.seat.stunt`; **it is an AI/script turret**, not a driver weapon."

The two facts are real and I confirmed them from the jsonl (no binding; the only seat is
`interaction.seat.stunt`; `CTurretWeaponComponent` appears exactly once in the whole file). "It is
an AI/script turret" is an inference about game code, not a decoded value — the doc should stop at
"no slot binds it and no driver/gunner seat exists; what fires it is UNKNOWN". This is the R5 risk
in reverse: a behaviour claim resting on a class name and an absence.

### 6. Card-level note (not a defect in the work): the `In` list names the wrong `WIRING.jsonl`

The card's `In:` says `... PARTS_TABLE.jsonl, WIRING.jsonl`. `Research/JC3Grab/WIRING.jsonl` is the
**`.physicsc` hull** table (35,499 rows, `compound`/`shape_class`/`shape_aabb`, G2-30's subject),
not weapon wiring; the tool correctly does not read it. Nothing is lost — but the card's input list
is misleading and should be corrected when it is next touched. The other input, `detail/*.ee.json`,
is deliberately not used, and the MODLOG entry explains why (it drops unnamed `<value id=…>` items,
which is exactly where the slot bindings live) — that is a good, honest departure.

## Spot-checks (value, where verified)

| # | value in the doc | verified where | result |
|---|---|---|---|
| 1 | 88 weapon components = 57 `CBulletWeaponBase` + 25 `CMissileWeaponBase` + 6 `CRPGFireLeachWeapon`; 81 bound / 7 unbound; 62 driver slots; 19 gunner slots; 193 seats; 23 distinct weapon names | counted directly over `WEAPON_WIRING.jsonl` (one row per entity, `weapons[]`, `seats[]`) | **all match.** 62 = 37 `main_weapon` + 23 `secondary (id:00568A74)` + 1 `CCar::main_weapon` + 1 `CCar::secondary`; gunner 19 = 14 `mounted_weapon` + 5 `mounted_weapon_2`; 62 + 19 = 81 |
| 2 | 22 of 88 weapons carry a type-4 `MountAttach` = all 19 gunner weapons + the corvette's cannon | counted `mount_parts` non-empty: 22, of which 19 gunner-bound; the other 3 are the corvette's **three entity copies** (`debug`, `military_01`, `rebel_01`) of `w616_corvette_canon` → `corvette_gun` + `corvette_turret` | **matches** (the singular "the corvette's driver cannon" hides that it is 3 components, which is why 19 + 1 ≠ 22 on a naive read) |
| 3 | "the heavy patrol's `mounted_weapon` joins `gunner2`/`point.gunner.right` (1.05 m) and `mounted_weapon_2` to `gunner1`/`point.gunner.left` (1.05 m); the slot order is not the seat order" | `nearest_gunner_seat` in the jsonl for `v1200_boat_capstone_heavypatrol_debug` | **matches**: 1.052 m → `gunner2` index 7, 1.054 m → `gunner1` index 6 |
| 4 | "the gunner strings match `PARTS_TABLE.jsonl` names … `Turret`/`Cannon` chains" | joined `mount_parts` against `PARTS_TABLE.jsonl` `parts[].n` / `parts[].b` | **matches with one nuance**: `apc_turret_base`=Turret + `apc_weapon_mount_vertical`=Cannon, `technicaljeep_rebel_turret`=Turret + `…_vertical`=Cannon, `armoredjeep_*` the same, `corvette_turret`=Turret + `corvette_gun`=Cannon — but the heavy patrol's **two** parts (`heavypatrol_weapon_mount_l_horizontal` / `_vertical`) are both `Cannon`, so the MODLOG's "those are all `Turret` -> `Cannon` chains" is loose for 2 of the 12 names. The doc itself does not repeat the generalisation, only the per-entity rows, so the doc is fine |
| 5 | 112 moving-part rows, 300 weapon points, 54 root objects, 21 chassis, primary roots CCar 17 / CAirPlane 9 / CBoat 12 / CHelicopter 14 / CTrain 1 | counted from the jsonl | **all match** (17+9+12+14+1 = 53) |
| 6 | "`action_1`/`action_2` are `1`/`2` on armed and unarmed cars alike"; `id:D04059E6` is the class-name hash | `E:/Modding/JustCause3/_grab/wiring/epe/v0201_car_capstone_mediumtank_debug.ee.xml` carries `<value name="action_1" type="int">1</value>` and `action_2 … 2`; class-hash property re-check is inside `--check` | **matches**, but note the action numbers are *not* in `WEAPON_WIRING.jsonl` — that claim is prose-only and `--check` cannot re-derive it |
| 7 | "`CLightWeaponComponent` … colour/radius/spot data (30 components on 9 entities)" | the jsonl subcomponents: 30 entries, all named `warning_light`, with `Color` `1,1,1,1`, `Radius` `0.5`, `SpotLight` `1`, `FalloffStart` 1 | **matches** — the colour/radius/spot claim is data-backed, not just a class name |

Corroborating structural check for the card's Done items: no entity in the 53 mixes a driver slot
with a gunner slot (0 rows with both counts non-zero), the maximum driver slots on any entity is 2
and on `01_land` is 2 (medium + Bavarium tanks), and the (d) table's 17 `CCar` rows match the
`01_land` set exactly.

## Summary of what to fix, cheapest first

1. `Tools/scripts/jc3wiring.py:560` — add the missing `f` prefix (one character), re-run `--write`.
2. `Tools/scripts/jc3wiring.py:513` — drop or rewrite the "last row is the cargo-plane variant"
   sentence; the cargo plane is filtered out of that table.
3. Convert the three typed counts (lines 470, ~568, §6 prose) to `len(rows)` / computed values.
4. Either script the 1.1-million-string search with an artefact, or reword line 16 to say the name
   is simply not in the shipped tables.
5. Reword line 2031's "it is an AI/script turret" to "no slot binds it; what fires it is UNKNOWN".

None of these change a decoded value, and the jsonl — the artefact later cards read — is
internally consistent and matched every number I checked.
