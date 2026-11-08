# Assumption challenge — card T-18 · Lights translation completion

Written 2026-10-30. **Read-only review**: no file outside this one was modified — not
`GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/`, `Working/`, `Builds/`, and nothing in a game
install. No game launched, nothing written to `D:\Games`, nothing committed, no secret read. Only
the generator's own `--check` and in-memory Python heredocs were run; no probe script was left on
disk.

**In scope**, as the task requires: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–76), the T-18 card
(lines 939–943), its §12 row (line 1327), the MODLOG sections `## T-18 · Lights translation
completion — intended change` (12564) and `— done (2026-10-28)` (12735), and the card's outputs —
`Working/Translation/T14_LIGHTS.md` (174 lines), `Working/Translation/t14_lights.json` (3,934
lines), `Tools/scripts/t18_lights.py` (1,257 lines). Cross-checked against the five inputs the tool
names (`Research/BatmobileGrab/LIGHTS.json`, `Working/Lights/v082/lights.xml`,
`Working/Lights/v082/entity.xml`, `Research/JC3Grab/LIGHT_SYSTEM.json`,
`Research/JC3Grab/PARTS_TABLE.jsonl`), the ledger `T_ROWS.jsonl` and `STATUS.md`, and — for the
claims T-18 leans on — `T1_TRANSLATION.md` (T-L1…T-L7), `T2_TRANSLATION.md`, `LIGHT_SYSTEM.md`,
`BONES.md`, `ANIMATIONS.md` and `grep_bones`.

**Card as written:** "Do: complete T-L1…T-L7, T-LG1…T-LG6 with colours/intensities/cones from
G1-17, the wheel-arch lights as custom `SVehicleLight` entries (closes T-L4/T-LG4), emissive
`CarLight` blocks per lamp part, light-part list for B-04. Out: rows;
`Working/Translation/t14_lights.json`. **Done: every light entry of the `Batmobile` rig (28) maps to
an `SVehicleLight` or a named omission (forensics rig stays out).**"

---

## VERDICT

**The gate is green, the hash join is exact, and the counting is honest — but the mapping throws away
every socket's position: six mapped headlamps, three left/right pairs, all land on one anchor node.**
`t18_lights.py --check` passes (exit 0), `t_rows.py check` is green, and I was able to re-derive the
hard parts independently: 28 rig entries → 28 rows (22 mapped, 6 omissions), 21 donor module rows
and 22 graph objects, **20 of 21 presets resolving** with the one documented orphan
(`3358775008`), **22 of 22 object names reproducing from `hash_jenkins`**, every row's
`behavior_hash`/`part_hash` reproducing, and exactly two objects referenced by no row
(`Front_Secondary_Head`, `Rear_Break`). The colour conversion is right (UE3 `FColor` is BGRA, which
`grab_lights.fcolor()` reverses once; the stored list is RGBA, and the brake lamps come out red), the
part indices are free (the donor has 42 parts, 0..41; new parts 42/43), and `has_lights` really is 1
on the body and 0 on the wheels.

What does not survive: **12 of the 28 entries carry the anchor
`…|body|Winch_DOOR_Mesh|Winch_DOOR_Mesh_LIG` — among them `HeadLight1` and `HeadLight2`, whose BmAK
sockets are 85.7 cm apart.** The row format is `deformable_transform` = one node path with no
offset, so both headlamps (and both secondary lamps, and both battle heads — three left/right pairs)
would emit from a single point. The doc's own verify cell for those rows is "one beam per side on
the road", which is exactly what this placement cannot produce. Second, **five mapped rows describe
lamps the donor ships at `Brightness 0.0`** (`HeadLight2` R 0.1, both wheel lamps R 0.0, the battle
spot, the battle arch) and every one is proposed as a lit JC3 row — the brightness is printed, the
consequence is not. Third, the doc's "two `SpotLightComponent`s on each head socket" is true of
`HeadLight1` (6000/1800) and false of `HeadLight2` (**one** component, R 0.1). Fourth, "0 rows
sharing a lamp" is true only because the eight flare rows are excluded from the metric *before* it
runs, while those rows explicitly "ride" the lamp above. Fifth, the "JC3 value" column is the
`SVehicleLight` object's members, while every proposal says "keep row N's members" — and the two
differ on every row I checked (row 13: range 2 / angle 10 vs the object's radius 1.5 / spot_angle 60).

| # | assumption | verdict |
|---|---|---|
| A1 | the Done gate (`t18_lights.py --check`, ledger, STATUS) is green and reproducible | **HOLDS** — PASS, exit 0; 28/28 ledger; `t_rows.py check` green |
| A2 | "every light entry of the Batmobile rig (28)" | **HOLDS for the SF rig, WEAK as a rig claim** — SF/MK2/Funhouse have 28 each, the Joker rig has **17** (4 HeadLights, no BootLight), unmodelled |
| A3 | 28 rows = 22 mapped + 6 omissions, 8 flares, 36 components | **HOLDS** — recomputed from `LIGHTS.json` |
| A4 | the join is `hash_jenkins(name)`; 22/22 names rebuild, 20/21 presets resolve, 1 orphan, 2 unreferenced objects | **HOLDS** — all four numbers independently reproduced |
| A5 | `Front_Secondary_Head` "is exactly the battle-mode spotlight T-L5 named" | **WEAK** — T-L5 names it as an unreferenced object and says the rig has no secondary spot row; nothing says "battle"; the object is enabled and parameterised (radius 10, spot 60) but no module row feeds it |
| A6 | colour is `LightColor`/255 → `diffuse`, UE3 `FColor` BGRA | **HOLDS** — the BGRA reversal is in `grab_lights.fcolor()`, the stored list is RGBA, and the brake lamps come out red |
| A7 | an entry's bone is enough to place its lamp | **BROKEN** — 12 entries share one anchor node; `HeadLight1`/`HeadLight2` sockets are 85.7 cm apart, three mapped L/R pairs collapse onto one point, no offset is stored |
| A8 | "BmAK puts two `SpotLightComponent`s on each head socket" | **WEAK** — true for `HeadLight1` (6000/1800), false for `HeadLight2` (one component, R 0.1) |
| A9 | a donor component's brightness does not change the mapping | **WEAK** — 5 mapped rows are lamps the donor ships at B 0.0 (and R 0.0–4500), all proposed lit |
| A10 | "0 rows sharing a lamp" | **WEAK** — the metric skips flare rows before comparing (`t18_lights.py` lines 518–528), and 8 flare rows share 4 lamps by design |
| A11 | the custom entries are G2-33's recipe from "the donor's shipped steady `HeadLight` point lamp (`lights[2]`)" | **HOLDS on provenance, WEAK on the consequence** — the template is `vanilla_reference` preset `2763198432` = **`Dash_Light`** (range 2, angle 10), so five new lamps get a dashboard light's 10° cone |
| A12 | parts: 42 donor records, body `has_lights` 1, wheels 0, new parts 42/43 | **HOLDS** — `PARTS_TABLE` donor record has 42 parts 0..41, `lights` 1/0, `Land_Body`/`Land_Wheel`, wheels at 26/27 |
| A13 | the table's "JC3 value" is what the row will build | **WEAK** — it is the `.epe` object's members; every proposal keeps the **module row's** members, which differ (range 2/angle 10 vs radius 1.5/spot_angle 60) |
| A14 | the forensics rig is "12 entries" | **WEAK** — 12 is the fleet total (3 per rig); the `Playable_Batmobile_SF` rig has 3, which is what the three rows cover |
| A15 | T-L24 (dashboard) keeps its behaviour | **WEAK** — BmAK's `VEHLT_Interior` maps to `TailLight`; the JC3 target `Dash_Light` is a `HeadLight` row, so the panel light would come on with the headlights |
| A16 | the counts (18 targets = 11 + 1 + 6; 21 rows / 22 objects; 2 unreferenced; 28/28 ledger) | **HOLDS** — every figure recomputed |
| A17 | the two `…c` sockets are absent from the mesh | **HOLDS** — `LIGHTS.json.problems` lists `HeadLight1c`/`HeadLight2c` per package |
| A18 | the anchors are usable once the build runs | **HOLDS as declared, with a limit** — every mapped row carries `anchor_state = needs-lig-bone` and the assembled body has no `_LIG` node yet (LGT-1 §4/§5), so nothing here is placeable until B-04 |

**Bottom line:** one real repair and four corrections. The repair: give the per-socket offset a home
— either one node per lamp (e.g. `Winch_DOOR_Mesh_LIG_L` / `_R`, or a node per entry) or a stored
`local offset` beside `deformable_transform` — otherwise the built car has one headlamp position for
six lamps and Q-1 #7 cannot pass. The corrections: say which lamps ship dark (A9), fix the
"two components per socket" sentence (A8), rename or define "sharing a lamp" (A10), and mark which
numbers in the "JC3 value" column the proposal actually keeps (A13). The hash join, the colour
conversion, the counts and the part work all hold.

---

## A1 · The Done gate is green and reproducible

**The result rests on:** §0.2 step 6 (run the Done check, paste the output) and R11 (generated,
`--check`).

**Test.**

```
$ python Tools/scripts/t18_lights.py --check
PASS: 28 rows: 22 mapped, 6 named omissions, 0 sharing a lamp | targets 18 = 11 donor rows + 1 graph object + 6 custom | donor 21 rows / 22 objects | ledger 28/28
EXIT=0

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 40 keep 60 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
EXIT=0
```

`--check` re-reads the five inputs, re-derives the doc and the json, compares both, re-asserts the
21-line §7 table, recomputes every custom entry's `behavior`/`part`/`anchor` hash, and compares each
row's cells and disposition with `T_ROWS.jsonl`. The three tamper tests in the done section match
that code (a target rename, a colour cell, a disposition).

**Verdict: HOLDS.** The ledger is now 198 rows, not the 150 the done section records — later cards
(T-11…T-15, T-19, T-22) have added to it since; `t_rows.py check` is green on today's file, which is
the only claim that matters.

---

## A2 · "Every light entry of the Batmobile rig (28)"

**The result rests on:** the card's Done line and the doc's "entries in the rig **28**", "the BmAK
rig `Playable_Batmobile_SF`, 28 entries".

**Test.** `LIGHTS.json` carries four rigs and 101 entries:

```
$ python - <<'EOF'   (Research/BatmobileGrab/LIGHTS.json)
summary: entries 101, vehicles 4, components 129
Playable_BatmobileFunhouse_SF 28  {HeadLight 14, BattleMode 4, stripped 3, Forensics 3, TailLight 2, Interior 1, BootLight 1}
Playable_BatmobileJoker_SF    17  {HeadLight 4,  BattleMode 4, stripped 3, Forensics 3, TailLight 2, Interior 1}
Playable_BatmobileMK2_SF      28  (same shape as SF)
Playable_Batmobile_SF         28  (same shape as SF)
EOF
```

The 28 is exact for `Playable_Batmobile_SF`, which is the package the mod builds (`v0300` base), and
the card names 28 explicitly. But the same car in the Joker package has a **17-entry** rig with 4
headlights instead of 14 — the Joker's headlight pairs (primary + secondary + flares) are absent. If
the project ever ships a Joker skin (D-5 says skins are extra drop entries), those lights have no
row and no omission. The doc's "36 components (129 across the 4 rigs)" records the fleet size without
saying the other rigs are out of scope.

**Verdict: HOLDS as the card is written, WEAK as a claim about "the Batmobile rig".** One sentence
("the Joker package's 17-entry rig is not covered; the build uses the V2") closes it.

---

## A3 · The row composition (28 = 22 + 6, 8 flares, 36 components)

**The result rests on:** §1's table, §7's assertions, and the done section's "18 distinct targets
cover the 22 mapped entries".

**Test.**

```
$ python - <<'EOF'   (LIGHTS.json, Playable_Batmobile_SF)
entries 28, components 36
components: LensFlareComponent 17, SpotLightComponent 16, PointLightComponent 2,
            RHelicopterSpotLightComponent 1
entries with no light component 10
```
```
$ grep -c "" / the doc's rows
T-L8…T-L35 = 28 rows; mapped 22 (T-L8…T-L20, T-L24…T-L27, T-L29, T-L31…T-L35)
omissions 6 (T-L10, T-L21, T-L22, T-L23, T-L28, T-L30); flares 8 (T-L25, 26, 27, 29, 31, 32, 33, 34)
```

36 components, 10 entries with no light component = 8 flare-only entries + the 2 absent `…c`
sockets. That is internally consistent: 22 mapped + 6 omitted = 28, and of the 22 mapped, 8 are
flares that ride another row. The 16 SpotLight + 2 PointLight + 1 helicopter spot = 19 light
components on 18 lamps; the extra is `HeadLight1`'s second spot (6000 and 1800).

**Verdict: HOLDS.**

---

## A4 · The hash join

**The result rests on:** §1 — "object names rebuilt from `hash_jenkins` **22/22**", "row presets that
resolve **20/21**", "row preset with no object `3358775008`", "objects no row references
`Front_Secondary_Head`, `Rear_Break`" — and the done section's "22/22, and 20 of the 21 row presets
resolve".

**Test.** Parsed the two donor files directly and recomputed the hash:

```
$ python - <<'EOF'   (Working/Lights/v082/{lights,entity}.xml + rbmhdr.hash_jenkins)
module rows (VehicleDynamicLight)  21
SVehicleLight objects              22
rows resolving by preset_id        20      unresolved [3358775008]
objects no row uses                ['Rear_Break', 'Front_Secondary_Head']
objects whose name_hash != hash_jenkins(name)   0 of 22
rows whose behavior_hash/part_hash != hash_jenkins(...)  0 of 21
Front_Secondary_Head -> 3189390601   Rear_Break -> 873569254
```

This is the strongest part of the card: the join is a real cryptographic-style match, all 22 object
names reproduce from their stored `name_hash`, and every module row's `behavior_hash`/`part_hash`
reproduces too. One detail the doc does not state: `3358775008` is the *fourth* module row, the
`taillight_r_c` TailLight on a part (`sportsmuscle_taillight_r_c`) that this rig's graph has no
object for — the same absent-part pattern as the `…c` flare sockets.

**Verdict: HOLDS.**

---

## A5 · `Front_Secondary_Head` "is exactly the battle-mode spotlight T-L5 named"

**The result rests on:** §1 — "`Front_Secondary_Head` is the second one, and it is exactly the
battle-mode spotlight T-L5 named" — and T-L17's target.

**Test.** What T-L5 actually said (it is the only prior claim):

```
$ grep -n "T-L5" -A 1 Working/Translation/T1_TRANSLATION.md
| T-L5 | `BattleModeSpotLight` | `Front_Secondary_Head` exists in the graph and is **unreferenced** —
this rig has no secondary spot row (measured, `t2_lg2.py`) | categorical | decoded | — |
```

So T-L5 said: BmAK has a `BattleModeSpotLight`, and the graph has an unreferenced
`Front_Secondary_Head`. It did **not** say the object is a battle spotlight; it said the rig lacks a
secondary spot *row*. The object itself:

```
$ python - <<'EOF'   (entity.xml, Front_Secondary_Head)
diffuse 0.6039,0.6039,0.9529   enabled 1   multiplier 1   near_cap 1.25
radius (absent)   spot_angle (absent)   preset_id = Front_Secondary_Head   name_hash 3189390601
```

It is an ordinary blue-white secondary head lamp, enabled, with no module row pointing at it. Its
own numbers (`radius` 10, `spot_angle` 60, `multiplier` 1, `near_cap` 1.25) are exactly T-L17's
"JC3 value" cell — "diffuse 0.604,0.604,0.953 r 10.0 ang 60.0" — so that column is right and
sourced to the object, not to the template.

**Verdict: WEAK.** The identification is by name and by "nothing else uses it", not by behaviour:
the object is a *secondary head* with no battle semantics anywhere in the files, and calling it
"exactly the battle-mode spotlight" states an inference as a fact. The row's values are the object's
own (radius 10 / spot_angle 60) and remain `decoded` — only the identification should read
"the unreferenced secondary head is the nearest object to BmAK's battle spot; nothing in the data
says battle".

---

## A6 · The colour conversion

**The result rests on:** §3 — "**The colour is adopted** - `LightColor`/255 -> `diffuse`, the G2-33
§7a conversion" — the MODLOG's "`LightColor` is `FColor` BGRA and `/255` gives `diffuse`", and §7's
"colours adopted 14 rows".

**Test.** Two independent checks.

```
$ sed -n '259,266p' Tools/scripts/grab_lights.py
def fcolor(raw):
    """Four serialised FColor bytes -> [R, G, B, A]. UE3 stores FColor B,G,R,A in memory
    (UEViewer, `UnCore.h`: "Since UE3, FColor has different memory layout - BGRA")."""
    b, g, r, a = (int(raw[i:i + 2], 16) for i in (0, 2, 4, 6))
    return [r, g, b, a]
```

So LIGHTS.json already stores **[R, G, B, A]**, and the T-18 rows divide by 255 in that order
(`diffuse.R` ← element 0). The MODLOG's "BGRA" describes the *raw serialised* layout, not the stored
array — the doc's wording is loose, the arithmetic is right.

Sanity check on a channel where the answer is known:

```
BrakeLightL  LightColor [255, 38, 0, 0]  -> proposed diffuse 1.000, 0.149, 0.000   (red)
LWheelLight  LightColor [160, 180, 255, 0] -> proposed diffuse 0.627, 0.706, 1.000  (blue-white)
HeadLight1   LightColor [138, 197, 246, 255] -> proposed diffuse 0.541, 0.773, 0.965
```

A brake lamp read as BGRA would come out blue; it comes out red, and the blue wheel lamp stays blue.
The channel order is coherent end to end.

**Verdict: HOLDS.** Only the prose ("`LightColor` is FColor BGRA") needs the word "raw" — the list
the tool reads is already RGBA.

---

## A7 · An entry's bone is enough to place its lamp

**The result rests on:** §3's "Anchors are `LIGHTS.json`'s `jc3_anchor`, built from the socket's
bone (G1-17), which is why a head socket can ride a door bone" — i.e. the bone path is the placement,
with no per-socket offset carried anywhere in the row.

**Test 1 — the anchors are not distinct.** Counted over the 28 entries:

```
$ python - <<'EOF'   (LIGHTS.json, Playable_Batmobile_SF)
12  sportsmuscle_body  |sportsmuscle_LOD1|body|Winch_DOOR_Mesh|Winch_DOOR_Mesh_LIG
 4  sportsmuscle_wheel_f_l  ...|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG
 3  sportsmuscle_wheel_f_r  ...|Wheel_Frnt_Right_Disc|Wheel_Frnt_Right_Disc_LIG
 2  sportsmuscle_body  ...|Batmobile_Rig_Weapons_Drone_Decoder|..._LIG
 2  sportsmuscle_body  ...|Batmobile_Chassis|Batmobile_Chassis_LIG
 2  sportsmuscle_body  (no anchor)
 1  machine gun / 1 rear-left susp / 1 rear-right susp
EOF
```

Twelve entries — including **six of the 22 mapped rows**: T-L8 and T-L9 (primary headlights, left and
right), T-L11 and T-L12 (secondary headlights, left and right), T-L18 and T-L19 (battle heads, left
and right) — all name the **same** node.

**Test 2 — the sockets they come from are far apart.**

```
HeadLight1  socket_location [21.286633, 45.192657, -44.25]
HeadLight2  socket_location [28.216906, -38.593201, -61.0]
distance 85.72 cm
```

Two headlamps 0.86 m apart, one `deformable_transform` between them. Nothing in the row record (or in
the custom-entry member list, which has the same single path) carries a local offset.

**Test 3 — the doc's own verify says this must not happen.** The verify cell for all four headlight
rows is "Q-1 #7: **one beam per side** on the road, haze cone visible at dusk". The built car would
have one beam point (or two coincident ones) at the door-bone origin. `Winch_DOOR_Mesh` is also an
animated bone — `ANIMATIONS.md` lists `Batmobile_V2_Winch_Door_Open` with tracks
`Winch_DOOR_Mesh`, `Batmobile_Bone_Chair_Rot_001` — so the point can move as well.

**Verdict: BROKEN** for the placement claim. The anchor is a faithful copy of the socket's **bone**,
but a socket is bone + local offset, and the offset is dropped. The fix is a per-lamp node (the doc
already invents node names for the new parts) or an offset field beside the path; without it the
head, secondary and battle pairs are one lamp.

---

## A8 · "BmAK puts two `SpotLightComponent`s on each head socket"

**The result rests on:** the done section's third bullet ("`headlight_f_l_01` and `headlight_f_l_02`
each carry a point row and a volumetric row, and BmAK puts **two `SpotLightComponent`s on each head
socket**"), which is the reason the typed entry maps to `_01` and the stripped one to `_02`.

**Test.**

```
$ python - <<'EOF'   (LIGHTS.json, SF, non-flare components per entry)
HeadLight1  VEHLT_HeadLight        2 spots  B 0.15 R 6000.0 and B 0.15 R 1800.0
HeadLight2  VEHLT_HeadLight        1 spot   B 0.00 R 0.1
HeadLight1  (stripped)             1 spot   B 1.0  R 1024.0
HeadLight2  (stripped)             1 spot   B 1.0  R 1024.0
HeadLight1  VEHLT_BattleModeLight  1 spot   B 5.0  R 1024.0
HeadLight2  VEHLT_BattleModeLight  1 spot   B 5.0  R 1024.0
```

`HeadLight1` does carry two (the point + volumetric pair); `HeadLight2` carries **one**, at
brightness 0.0 and radius 0.1 cm — a component that emits nothing. The donor's structure is
asymmetric, and the "two per socket" sentence is what justifies the two-cluster mapping.

**Verdict: WEAK.** The mapping still works (each typed entry gets one cluster, each stripped entry
the other), but the stated reason is false for one of the two typed sockets, and that socket is the
one whose lamp is dark (A9).

---

## A9 · A donor component's brightness does not change the mapping

**The result rests on:** the rows' `class` (`decoded` for T-L8…T-L20) and the proposal text, which
keeps each target row's lit members regardless of the BmAK `Brightness` printed beside them.

**Test.** The six entries that ship at brightness 0:

```
$ python - <<'EOF'   (LIGHTS.json, SF)
entries with B=0: 6
  HeadLight2 / VEHLT_HeadLight          B 0.0  R 0.1     -> T-L9   mapped, "keep row 19's members"
  LWheelLight / VEHLT_HeadLight         B 0.0  R 0.0     -> T-L13  mapped, custom, r 2 ang 10
  RWheelLight / VEHLT_HeadLight         B 0.0  R 0.0     -> T-L14  mapped, custom, r 2 ang 10
  BattleModeSpotLight / BattleModeLight B 0.0  R 4500    -> T-L17  mapped, add a row
  LWheelLight / BattleModeLight         B 0.0  R 2048    -> T-L20  mapped, custom, r 2 ang 10
  BattleModeSpotLight / ForensicsLight  B 0.0  R 0.0     -> T-L21  omitted (forensics)
```

Five of the six are mapped rows, and each is proposed as a **lit** JC3 light: the rows print
"B 0.0" in the BmAK column and then "keep row 19's members" / "custom entry … r 2 ang 10". The doc
never says "the donor ships this lamp dark, so the build adds light the donor does not have". For
the battle lamps that is defensible — they are meant to be off until battle mode — but for the
pursuit-side `LWheelLight`/`RWheelLight` (R 0.0, cone 0.0) and `HeadLight2` (R 0.1) there is no mode
to switch them on, so the arch lamps and the right primary lamp would simply be lit where the donor's
are dead.

**Verdict: WEAK.** The values are honestly printed; the consequence is not drawn. One sentence per
dark row ("donor B 0, R 0 — the JC3 row is lit and the build will show it") is the R4 fix, and it
also tells Q-1 #7 what to expect.

---

## A10 · "0 rows sharing a lamp"

**The result rests on:** the PASS line's "0 sharing a lamp" and §7's `rows sharing a lamp | 0`.

**Test.** The metric excludes flare rows *before* it compares targets:

```
$ sed -n '518,528p' Tools/scripts/t18_lights.py
    for row in rows:
        if row["kind"] == "omitted":
            continue
        names = [t["name"] for t in row["targets"]]
        if light_component(entries[row["entry_index"]]) is None:
            row["kind"] = "flare"
            row["shared_with"] = next((owner[n] for n in names if n in owner), None)
            continue
        key = tuple(sorted(names))
        if key in seen:
            row["kind"] = "shared"
```

So `shared_rows` counts only *light-bearing* rows with an identical target tuple. The eight flare
rows are excluded and each is stamped `shared_with` the lamp it rides:

```
T-L25  Sport_Muscle_Headlight_Volume_Left  (rides T-L8)
T-L27  Sport_Muscle_Headlight_Volume_Left  (rides T-L8)   <- same target as T-L25
T-L26 / T-L29  Volume_Right               (rides T-L9)
T-L31 / T-L32  right wheel arch           (rides T-L14)
T-L33 / T-L34  left wheel arch            (rides T-L13)
```

Four targets, eight rows, two rows per target — visible in the doc's own "8 flare rows" and "rides
it" cells.

**Verdict: WEAK** (label, not data). "0 sharing a lamp" next to "8 flare rows … rides it" reads as a
contradiction. Say "0 light-bearing rows share a target; 8 flare entries ride 6 lamps" and the
number is both true and informative.

---

## A11 · The custom entries are G2-33's recipe from "the donor's shipped steady `HeadLight` point lamp (`lights[2]`)"

**The result rests on:** §4's member table — every member except behaviour/part/anchor/colour is
"G2-33 §7a recipe, copied from the donor's shipped steady `HeadLight` point lamp (module
`lights[2]`)" — and `preset_id 0`.

**Test 1 — the provenance is exact.**

```
$ python - <<'EOF'   (LIGHTS.json entry vanilla_reference, LWheelLight)
preset_id 2763198432, range 2.0, falloff_start 0.0, near_cap 1.0, multiplier 1.0,
min_luminosity 0, light_type 0, blinking 0, angle 10.0, cast_shadows 0,
projected_texture_index -1, volumetric_mode 0, volume_intensity 1.0
$ python - <<'EOF'   (lights.xml, row 3 / Dash_Light = preset 2763198432)
behavior HeadLight, part sportsmuscle_body, range 2, angle 10, multiplier 1, diffuse 0.803,0.908,1
```

The template is the donor's own **`Dash_Light`** row — a real shipped `HeadLight` point lamp, index 3
of 21 (the doc says `lights[2]`, 0-based: correct).

**Test 2 — what that means for the lamps it is copied onto.** `angle` 10, `range` 2. The two battle
head lamps (T-L18/T-L19) come from donor components with `OuterConeAngle` 35 and `Radius` 1024; the
boot lamp from 60 / 400; the arch lamps have no cone at all. All five custom entries take the
dashboard lamp's 10° cone. That is the documented "no unit bridge, so the shipped JC3 number is
kept" decision — but the "shipped JC3 number" here is a *dashboard* lamp's, chosen by recipe, not a
number for a headlamp.

**Verdict: HOLDS on provenance, WEAK on the consequence.** §4 should state that the cone/range of
every custom lamp is the dashboard template's (2 / 10°), so Q-1 #7 expects narrow beams and B-03
knows what it is copying.

---

## A12 · The parts claims

**The result rests on:** §5 — `sportsmuscle_body` `part_index 0`, `has_lights 1`, `Land_Body`;
wheels 26/27, `has_lights 0`, `Land_Wheel`; new `_arch` parts at 42/43, `Land_Light`, parent 26/27;
and §4's "`PARTS_TABLE.jsonl` donor parts module: 42 records 0..41".

**Test.**

```
$ python - <<'EOF'   (PARTS_TABLE.jsonl, the v0300 sportsmuscle record)
parts 42, indices 0..41
sportsmuscle_body      i 0   dt Land_Body   lights 1
sportsmuscle_wheel_f_l i 26  dt Land_Wheel  lights 0
sportsmuscle_wheel_f_r i 27  dt Land_Wheel  lights 0
```

The donor module really has 42 part records 0..41, the body really ships `lights 1`, the wheels
`lights 0`, and 42/43 are the next free indices. The new parts' names, `Land_Light`, and the parents
are this card's proposal, labelled `derived` in §4 — correct.

**Verdict: HOLDS.** (The doc says `has_lights`; the field is `lights` in the table — same thing, and
G2-33 calls it `has_lights`.)

---

## A13 · The "JC3 value" column is what the row will build

**The result rests on:** §3's column header "JC3 value" and the proposal cells "keep row 13's
members, repoint … ; diffuse -> …".

**Test.** For T-L8 the doc prints `JC3 value: diffuse 0.604,0.604,0.953 r 1.5 ang 60.0 +
diffuse 0.604,0.604,0.953 r 7.5 ang 15.0`, and proposes "keep row 13's members … diffuse ->
0.541,0.773,0.965". The two sides:

```
$ python - <<'EOF'   (entity.xml object Sport_Muscle_Headlight_Point_Left)
diffuse 0.6039,0.6039,0.9529  multiplier 0.5  radius 1.5  spot_angle 60  spot_inner_angle 0
$ python - <<'EOF'   (lights.xml module row 13, same preset)
behavior HeadLight  part sportsmuscle_headlight_f_l_01  part_index 34
range 2  angle 10  multiplier 1  diffuse 1,1,1
```

So "JC3 value" = the `.epe` object (radius 1.5 / spot_angle 60 / multiplier 0.5), while "keep row
13's members" = the module row (range 2 / angle 10 / multiplier 1). They differ on every number
except diffuse — and the proposal replaces the diffuse anyway. The doc's §6 does name the cause
("whether a preset overrides the entry's own members: UNKNOWN … both sides are therefore built"),
but the column heading invites the reading that the printed value is the one the build gets.

**Verdict: WEAK** (presentation). Rename the column "donor object's members" and add a
"row's members (kept)" column, or mark the kept numbers in the proposal. B-03/B-04 will read this
table.

---

## A14 · The forensics rig is "12 entries"

**The result rests on:** T-L21/T-L22/T-L23 — "the `VEHLT_ForensicsLight` rig (12 entries) is a
scanner mode, not the car's lights; the card keeps it out".

**Test.**

```
$ python - <<'EOF'   (LIGHTS.json by_type across the four rigs)
VEHLT_ForensicsLight 12   = 3 per rig (SF, MK2, Funhouse, Joker)
Playable_Batmobile_SF entries with type VEHLT_ForensicsLight: 3  (T-L21, T-L22, T-L23)
```

The 12 is the fleet total; this rig has 3, which is exactly what the three omitted rows cover. The
card's scope is the rig (28), so the omission is complete — the number is just borrowed from another
denominator.

**Verdict: WEAK** (a fleet count in a per-rig row). "3 of this rig's entries (12 across the four
rigs)" is the precise sentence.

---

## A15 · T-L24 keeps the dashboard's behaviour

**The result rests on:** T-L24 — BmAK `Dashboard_Light` `VEHLT_Interior` → `TailLight`, JC3 target
`Dash_Light` (row 2), proposal "keep row 2's members".

**Test.**

```
$ python - <<'EOF'   (LIGHTS.json, Dashboard_Light)
socket Dashboard_Light  type VEHLT_Interior  behavior TailLight  behavior_source "enum VEHLT_Interior"
$ python - <<'EOF'   (entity.xml object Dash_Light)
diffuse 1,0.9765,0.9176  multiplier 0.2  near_cap 0.1
$ python - <<'EOF'   (lights.xml module row 2, preset 2763198432 = Dash_Light)
behavior HeadLight  range 2  angle 10  multiplier 1  diffuse 0.803,0.908,1
```

The BmAK behaviour is `TailLight`; the JC3 target's behaviour is `HeadLight`. JC3's nine behaviours
have no `Interior`, so `TailLight` is the closest mapping (G1-17) — but the row then keeps a
`HeadLight` row, i.e. the panel light comes on with the headlights, not with the running lights. The
row prints both behaviours and never says they differ.

**Verdict: WEAK** (R5 shape: the nearest *behaviour* was chosen on the BmAK side, then a different
behaviour's row is kept on the JC3 side). Either accept the headlight behaviour explicitly with the
reason, or point the dashboard at a `TailLight` row.

---

## A16 · The counts

**The result rests on:** §1's "distinct `SVehicleLight` targets **18** = 11 shipped module rows + 1
unreferenced graph object + 6 custom", "donor side: 21 module rows, 22 objects, 2 objects no row
uses, 1 row preset the graph does not instantiate", and the PASS line's "ledger 28/28".

**Test.**

```
$ python - <<'EOF'   (lights.xml / entity.xml)
module rows 21 ; SVehicleLight objects 22 ; unreferenced 2 (Rear_Break, Front_Secondary_Head)
rows resolving 20 ; unresolved 1 (3358775008)
$ python - <<'EOF'   (T_ROWS.jsonl)
T-L rows 41 ; of these T-L8…T-L35 = 28 ; dispositions next 14 / out 14 (T-14 doc in STATUS.md:
28 rows, 14 queued, 14 out)
```

11 + 1 + 6 = 18 targets; 22 mapped rows over 18 targets with 8 flares riding 4 of them: 22 − 8 = 14
light-bearing rows over 18 targets — consistent (some rows have two targets, e.g. T-L8's point +
volume). `STATUS.md`'s T-14 line (28 / 0 / 0 / 0 / 14 / 0 / 14 / 14) matches the ledger.

**Verdict: HOLDS.**

---

## A17 · The two `…c` sockets are absent from the mesh

**The result rests on:** T-L28/T-L30 — "`HeadLight1c`/`HeadLight2c` are flare objects on a socket the
shipped mesh does not have (LIGHTS.json `problems`)".

**Test.**

```
$ python - <<'EOF'   (LIGHTS.json.problems)
"Playable_Batmobile_SF/...: socket HeadLight1c does not exist in the shipped mesh"
"Playable_Batmobile_SF/...: socket HeadLight2c does not exist in the shipped mesh"
(+ the same pair for MK2, Funhouse, Joker)
```

**Verdict: HOLDS.**

---

## A18 · The anchors are usable

**The result rests on:** §3's "every one carries `anchor_state = needs-lig-bone` until the rig has
the bone (LGT-1 §5)" and §6's "whether an anchor chain resolves through the parts module: UNKNOWN
until the §112 probe".

**Test.**

```
$ python - <<'EOF'   (LIGHTS.json)
anchor_state for all mapped SF entries: "needs-lig-bone: the assembled part has no bone hierarchy yet"
$ grep -n "no ._LIG. node\|CarLight" Working/Translation/T14_LIGHTS.md §5
the body "already ships has_lights = 1, but its meshes have no CarLight block and no _LIG node"
```

So no row in this card is placeable yet: the node name is a target for B-04 to create. That is
declared, and the §5 light-part list is the handoff. The one thing not declared is that the node
*positions* are B-04's to choose — which is where A7's collapse has to be fixed, or B-04 will
faithfully build one node for six lamps.

**Verdict: HOLDS as declared, with the A7 consequence attached.**

---

## What this challenge did not test

- **Anything in-game.** R6 forbids a launch before phase V exits; Q-1 #7 is the probe that would
  settle A7 (one beam or two) and A9 (which lamps are dark).
- **Whether the JC3 renderer reads the module rows or the `.epe` objects** (A13): G2-33 §8 records it
  as UNKNOWN; both sides are carried by design.
- **The `CarLight` block's bytes** (MODLOG §102d): the doc says a block must be copied from a vanilla
  light part, never authored — nothing here challenges that.
- **The other three rigs** (A2): only the Joker's 17-entry difference was measured; whether MK2 and
  Funhouse truly match SF entry for entry was not compared row by row.
- **Whether `Winch_DOOR_Mesh` moves in play** (A7): the animation exists (`Batmobile_V2_Winch_Door_Open`)
  but whether our build will animate it is T-12/B-02's question.

## Reproduce

```
python Tools/scripts/t18_lights.py --check       # A1: PASS, exit 0
python Tools/scripts/t_rows.py check             # A1/A16: 198 rows, check ok
```

The heredocs above are read-only; the XML and hash probes parse the same donor files the generator
reads and write nothing.

Nothing in the repo, `Builds/`, `E:/Modding/JustCause3/_grab`, `E:/Modding/ArkhamKnight/_grab` or `D:/Games` was
written, and no process was launched.
