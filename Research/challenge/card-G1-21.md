# Assumption challenge — backlog card G1-21 (modes and transformation values)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-21 card, its §12 row,
the `MODLOG.md` `G1-21 · done` entry and the `G1-21 rework` entries, the generator
`Tools/scripts/grab_modes.py`, the artifacts `Research/BatmobileGrab/MODES.json` + `MODES.md`, and
the inputs `BMSDK_OFFSETS.json`, `OFFSETS.json`, `objects.jsonl`, `Working/Translation/T_ROWS.jsonl`,
`REGISTRATION.md`. Nothing was launched, written into `D:/Games`, or committed. The only file
written is this one.

## VERDICT

**One BROKEN item, and it is in the counting method, not in a value.** The card's central numbers
all reproduce: 107 declared family fields, 46 serialised, 61 with no value, and every quoted
magnitude — 600, 540, 120, 90000, 30000, 2000, 10000, 8000, 150000, 0.75/1.25, 30°, 20 cm,
−200/−400 — is present in the cooked tag streams with the offset its name claims.

The foundational assumption (a third-party SDK dump's offsets are this build's tag offsets) turned
out to be **much better evidenced than the card says**: 42 named tags in the vehicle/sim archetypes
sit at exactly the offset the dump declares for that name, including five on
`RVehicleBatmobileBase` — the class `REGISTRATION.md` says cannot be reproduced by a layout walk.
That test is not in the card and should be.

What does not hold: `same_in_all_four` is computed from `t["value"]`, which is `None` for a struct,
so the two struct fields count as "identical in all four packages" on `{None} == {None}`. The
number 31 happens to be right (I verified both structurally); the test cannot fail.

| # | assumption | verdict |
|---|---|---|
| A1 | the BMSDK dump's offsets are this build's cooked tag offsets | **HOLDS** — 42/42 named tags confirm it, incl. 5 on the class the layout walk cannot reproduce |
| A2 | the 61 "no value" fields really have no value anywhere | **HOLDS** — name search over all 20,128 objects: 0 hits |
| A3 | a number is bound to its name by offset alone (floats carry no name) | **HOLDS**, residual risk small and bracketed by A1's name-confirmed structs |
| A4 | "identical in all four packages = 31" | **BROKEN as a method** — 2 of the 31 are structs compared as `None==None`; the number survives only because the two structs are in fact identical |
| A5 | "46 serialised **with per-package values**" | **WEAK** — 2 of the 46 store `values: null` and one global struct; the page prints `— — — —` for one of them |
| A6 | units come from the field's name (`conv`) | **HOLDS as a convention**, correctly labelled; "never guessed" in the MODLOG is too strong |
| A7 | the curve is `cm/s -> factor`, points `(0→60, 600→40, 1200→30)` | **HOLDS as inference** — the x axis is corroborated by three other cm/s fields |
| A8 | "107 declared family fields" is the complete family set | **HOLDS** — set difference against the dump is empty both ways |
| A9 | "no tag ⇒ the class default runs" (why the value is UNKNOWN) | **HOLDS as conservative** — mechanism unverified, conclusion correct either way |
| A10 | the Done line is satisfied on rows `T-BM1` … | **WEAK** — `T-BM1` is `superseded`, and `T-12`/`T-15` are not ledger rows |
| A11 | front/rear binding of the `TurnOnSpot` ±0.8 pair | **HOLDS by declaration order** |
| A12 | the per-package machinery detects real differences | **HOLDS** — Joker 0.666 vs 0.5, −400 vs −200, 0.75 vs 0.333 all caught |

Counts: 8 HOLDS, 3 WEAK, 1 BROKEN (method only).

## Method note

The card has a gate, so the challenge runs against the machine:

```
$ python Tools/scripts/grab_modes.py --check
OK: 107 declared, 46 serialised, 61 not serialised; 29/29 checks; md byte-identical
EXIT=0
```

`md byte-identical` means `MODES.md` is rendered from `MODES.json` and compared byte for byte, so
every line quoted below is generated, not typed.

---

## A1 — the dump's offsets are this build's cooked offsets. **HOLDS**

The whole card is one idea: `BMSDK_OFFSETS.json` gives a class, a member name and an absolute
offset; `objects.jsonl` gives a cooked archetype's tags as bare `(offset, type, value)` triples. Bind
them by offset and you have decoded values. If the dump were a different build, every name would sit
next to the wrong number and nothing downstream could tell.

The card cites a build match indirectly — `OFFSETS.json` says *"offsets generated from the running
game; build match measured in REGISTRATION.md"* — and `REGISTRATION.md` measures it:

```
**Why it is the same build (measured):**
- `RVehicleSimBatmobile`: dump size 1220; the upk walk lands on 0x104 + 0x3C0 = 0x4C4 = 1220, and
  *all 165* declared rows land on the same offset in the dump. 147 match by name directly; the
  other 18 are bools that share one bitfield word ...
- The native anchors agree: `SetDriveMode` writes the byte at `0x3B0` = `DriveMode` ...
```

That covers `RVehicleSimBatmobile`. But `REGISTRATION.md` also records that **seven classes cannot
be reproduced from the shipped declaration, `RVehicleBatmobileBase` among them** — and that is the
class declaring most of this card's fields (`KillFlipTorque`, `ImpactShake`, `BattleModeWidth`, the
`Strafe*` block). For those, the evidence is the dump alone.

So I tested the vehicle class directly, using a property the card never uses: **a struct tag carries
its own name in the cooked stream.** If the dump's offsets are right, every named tag must sit at
the offset the dump declares for that exact name:

```
$ python ... (every named tag on the RVehicleBatmobile / RVehicleSimBatmobile rows, vs BMSDK)
named tags on vehicle/sim rows: 42
 4 pkg RVehicleSimBatmobile  off  260 (0x104) TorqueVSpeedCurve        -> CONFIRMED RVehicleSimCar
 4 pkg RVehicleSimBatmobile  off  536 (0x218) BattleModeVSpeedCurve    -> CONFIRMED RVehicleSimBatmobile
 4 pkg RVehicleBatmobile     off 7208 (0x1c28) ImpactShake             -> CONFIRMED RVehicleBatmobileBase
 4 pkg RVehicleBatmobile     off 6596 (0x19c4) ExplosiveImpactScreenShake -> CONFIRMED RVehicleBatmobileBase
 4 pkg RVehicleBatmobile     off 7432 (0x1d08) DeathExplosionSoundArray -> CONFIRMED RVehicleBatmobileBase
 3 pkg RVehicleBatmobile     off 8184 (0x1ff8) WeaponGeneratorMeshPackage -> CONFIRMED RVehicleBatmobileBase
 3 pkg RVehicleBatmobile     off 8200 (0x2008) WeaponGeneratorMesh     -> CONFIRMED RVehicleBatmobileBase
 ... (42 rows, no mismatch)
```

**42/42.** Five of them are on `RVehicleBatmobileBase`, at offsets that bracket the class across
0x19c4…0x2008, and one of those is `ImpactShake` at 0x1c28 — a field the card itself reports. The
foundational assumption therefore holds with direct, name-level evidence, including for the class
`REGISTRATION.md` calls unreproducible. Verdict HOLDS. **This test is missing from `MODES.md`,** and
it is the one piece of evidence a reviewer would most want: without it, "same build" is a citation
to another card's prose.

## A2 — "61 declared-only fields have no value anywhere in the files". **HOLDS**

The card asserts absence 61 times. Absence is the easy claim to get wrong by searching too little.
The strongest available search is by name, because when a tag has a name it is exactly the field's
name. I searched every tag name in all four packages for all 65 fields that are either not
serialised or missing in some package:

```
$ python ... (65 field names, all 20,128 objects, any class, any offset)
fields to test: 65 (not serialised + per-package gaps)
carried by name anywhere: 0
```

Zero hits. So `BattleModeWidth`/`Length`/`Height`, `BattleModeMaxSpeed`, all eight `Strafe*`,
`BattleModeMaxSteering`, `TransformationRotation`, `JumpRampUpwardForce` and the rest really are
absent, and the Joker's five missing tags really are missing rather than present at another offset.
Note the split the card gets right: 61 declared-only **plus 5** serialised in three of four — the
page reports them as different things (`no` in the serialised column vs `yes` with a `—` in Joker),
which is why I tested both.

This HOLDS, but only as strongly as A3 allows: a float tag carries no name, so this search can only
find *struct and object* tags. For numbers, the absence claim is an absence of a tag at an offset,
which is A3's problem.

## A3 — numbers are bound to names by offset alone. **HOLDS, with the risk stated**

This is the card's weakest link by construction: `456 → TurnOnSpotFrontTorqueFactor` is a claim no
name in the file supports, because the cooked stream has no name for a `FloatProperty`. A four-byte
layout error inside the class would silently move every name onto its neighbour — and the value
would still look like a float.

What makes this HOLDS rather than WEAK is A1's result. The five name-confirmed structs on
`RVehicleBatmobileBase` sit at 0x19c4, 0x1c28, 0x1d08, 0x1ff8, 0x2008 — a span that encloses the
numeric block this card reads (`KillFlipTorque` 0x1c18, `KillFlipTorqueDuration` 0x1c1c,
`KillKeepyUpFactor` 0x1c20 …, `BattleModeImpactMaxDamagePow` 0x1aec). A layout that had slipped by
one slot anywhere in that range could not leave `KillFlipTorque` at 0x1c18 and its *duration* at
0x1c1c while `ImpactShake` still lands exactly on 0x1c28. The neighbouring-offset structure itself
is also authored-looking: `0x1ae4` 540 / `0x1ae8` 120 / `0x1aec` 0.5, then `0x1c18` −200 / `0x1c1c`
0.5 / `0x1c20` 10 / `0x1c24` 0.75 — each run is a sensible triple, which a shifted mapping would
scramble into noise.

Residual risk: a name swap between two same-typed adjacent floats (e.g. front/rear, see A11) is
undetectable from the data and is not detected here either. Small, and unavoidable.

## A4 — "identical in all four packages = 31" is computed from `None`. **BROKEN (method)**

```python
# grab_modes.py:337-348
per_pkg[r["package"]] = t.get("value")          # StructProperty -> None
...
cooked = [(pkg, per_pkg.get(pkg)) for pkg, _short in PACKAGES if pkg in per_pkg]
"same_in_all_four": len(cooked) == 4 and len({json.dumps(v) for _p, v in cooked}) == 1,
```

For a `StructProperty`, `t.get("value")` is `None` — the struct's content is in `props`/`items`,
not in `value`. So for the two struct fields the set is `{None}` and the flag is `True` no matter
what the four structs contain:

```
$ python ... (recompute from the record)
serialised 46 occ==4 41
occ4 with values 39 identical across all four 29      <- by actual value
recorded same_in_all_four: 31                          <- 29 + the 2 structs
serialised with no per-package values: ['ImpactShake', 'BattleModeVSpeedCurve']
```

The **number 31 is right**, and I checked the two independently rather than trusting the flag:

```
$ python ... (the ImpactShake tag at 7208 in each package, full tag JSON)
Playable_BatmobileFunhouse_SF sha1 0a18705f0454 len 862
Playable_BatmobileJoker_SF    sha1 0a18705f0454 len 862
Playable_BatmobileMK2_SF      sha1 0a18705f0454 len 862
Playable_Batmobile_SF         sha1 0a18705f0454 len 862
all identical: True

$ python ... (BattleModeVSpeedCurve, points per package)
Playable_BatmobileFunhouse_SF -> [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]]
Playable_BatmobileJoker_SF    -> [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]]
Playable_BatmobileMK2_SF      -> [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]]
Playable_Batmobile_SF         -> [[0.0, 60.0], [600.0, 40.0], [1200.0, 30.0]]
all equal: True
```

So: no wrong number shipped, but the flag is a test that cannot fail. If the Joker's `ImpactShake`
had differed (it carries 7 members, one of them a nested `AdvancedOptions` — plenty of room to
differ), the page would still have counted it in the 31. Verdict **BROKEN as a method**: the check
in `grab_modes.py:348` must compare `struct_props(t)` / `curve_points(t)`, not `t["value"]`. This is
a three-line generator fix, and it is the sort of thing the card's own `--check` should catch and
does not, because `--check` re-renders from the same record.

## A5 — "46 serialised **with per-package values**". **WEAK**

The MODLOG sentence is too strong for two of the 46. `ImpactShake` and `BattleModeVSpeedCurve` store

```
"values": {"Playable_BatmobileFunhouse_SF": null, "Playable_BatmobileJoker_SF": null,
           "Playable_BatmobileMK2_SF": null, "Playable_Batmobile_SF": null}
```

with the content held once, globally, in `struct` — no package attribution anywhere. The rendered
table then prints

```
| `ImpactShake` | 0x1c28 | `FBMScreenShakeStruct` | struct | — | — | — | — | yes |
```

four dashes and "yes". A reader sees "no value in any package, serialised in all". The struct's
members are printed in a later section (§`ImpactShake`, offsets 0x4…0x90 with 0.33,
[150,150,30], [1000,1000,200], …) but with no statement of which package they came from. Since I
verified all four are identical (A4), nothing is wrong — but the record cannot tell you that, and
"with per-package values" is untrue of these two. Verdict WEAK (representation), fix = store the
struct per package like the scalars, or say "one global struct, verified identical in all four".

## A6 — units come from the field's name. **HOLDS as a convention**

Every field carries `unit` + `unit_basis` (`conv` / `engine` / `type` / `none`), and the page
publishes the basis table, which is the honest form of a name-based guess. `conv` is still an
inference, and the MODLOG's "Units are given with their basis, **never guessed**" oversells it — a
name convention *is* a guess with a documented basis. But the inference is corroborated inside the
data, which is more than most unit claims get:

- `TurningModeMaxSpeed` 600 cm/s, `BattleModeImpactMaxDamageSpeed` 540 cm/s,
  `BattleModeImpactMinDamageSpeed` 120 cm/s, and the curve's x values 0 / 600 / 1200 cm/s — four
  independent fields, one coherent scale (6 m/s, 5.4 m/s, 1.2 m/s, 12 m/s). If any of these were
  m/s the others would be absurd by two orders of magnitude.

```
| `BattleModeImpactMaxDamageSpeed` | 0x1ae4 | `float` | cm/s | 540 | 540 | 540 | 540 | yes |
| `BattleModeImpactMinDamageSpeed` | 0x1ae8 | `float` | cm/s | 120 | 120 | 120 | 120 | yes |
```

- `engine` magnitudes are carried as shipped and never converted (10000, 150000, 90000, 8000,
  −200) — no conversion is inventable, so nothing is invented.
- 5 fields are explicitly `none` (`AirControl`, `BattleModeYawOffset` 0, `ArmourModeDamageReduction`
  "int, undocumented scale", `BattleModeThrottleSpeed`, `BattleModeSteerBiasRate`), including the
  one value a lesser card would have happily called "0% damage".

Verdict HOLDS as a labelled convention. It would be WEAK if the page printed the units as read
facts; it does not.

## A7 — the curve is `cm/s → factor` with points `(0→60, 600→40, 1200→30)`. **HOLDS as inference**

The pairs are read in `FInterpCurve` layout order (`InVal`, `OutVal`), so the pairing is structural.
The *meaning* of each axis is inferred, and the x axis is the part that can be tested: 600 and 1200
are exactly `TurningModeMaxSpeed` and 2× it, in a card where every other speed is cm/s. The y axis
is labelled `factor` from the monotone falloff 60 → 40 → 30, which is what a drive-force falloff
looks like; nothing contradicts it, and the card does not pretend it is documented. Verdict HOLDS as
an inference carried with its label (`curve (cm/s -> factor)`).

## A8 — "107 declared family fields" is complete. **HOLDS**

The count is only meaningful if the family prefix list catches exactly the declarations. Test both
directions against the dump:

```
$ python ... (every BMSDK property whose name starts with one of the 17 family prefixes)
BMSDK family-named properties: 107
MODES fields: 107
in BMSDK not in MODES: [] 0
in MODES not in BMSDK: [] 0
```

Exact set equality. So the inventory is not a sample — it is every family-named declaration in the
41-class dump, with nothing dropped and nothing invented. (The 17 prefixes are a superset of the
card's list: the card asks for 13 patterns, the record adds `ImpactRoadAssist*`, `ImpactShake*`,
`KillKeepyUp*`, `JumpNoRamp*`, `VehicleShovingTorque` — which is why the record can answer more than
the Done line asks.)

## A9 — "no tag at that offset ⇒ the class default runs". **HOLDS as conservative**

This is the one claim in the card that is a statement about the *cooker*, not about the files, and
it is unverifiable from anything on disk. The reasoning is nonetheless self-consistent: a tag is
present in three packages and absent in Joker, so the three carry a value that differs from the
class default (that is why it was serialised), and the Joker carries the default. The five fields
behave exactly that way in three packages and not in the fourth:

```
BattleDodgeImpulse 0x1914 | 150000 | 150000 | — | 150000 | yes
ArmourModeDamageReduction 0x1918 | 0 | 0 | — | 0 | yes
PMDodgeTorque 0x1fdc | 6000 | 6000 | — | 6000 | yes
```

and the Joker archetype is the *same class* with the *same tag count* as the other three (37 tags
each, all `RVehicleSimBatmobile`), so this is not a different-class artefact. The conclusion drawn —
`UNKNOWN`, never 0 — is right under either mechanism (default runs, or tag lost), which is what makes
this safe: the card refuses the dangerous inference even though it offers a mechanism. Verdict
HOLDS as conservative; the mechanism itself stays WEAK/unverified.

## A10 — the Done line is anchored to `T-BM1`. **WEAK**

The card's completion criterion is "every field named in rows T-BM1, T-AC1, T-RA1, T-SR1 appears
with its value". `T-BM1` is retired:

```
$ python ... (T_ROWS.jsonl)
T-BM1 | superseded | superseded_by: ['T-12', 'T-15']
T-AC1 | out
T-RA1 | out
T-SR1 | out
```

and the successors are not ledger rows — over 198 rows there is no `T-12` and no `T-15`
(`['T-FX12', 'T-FX15', 'T-L12', 'T-L15', 'T-WP12', 'T-WLD12', 'T-WLD15', 'T-MD12', 'T-MD15']` is
the full list of id matches). `T-15` exists only as a backlog card (`GRAB_BACKLOG.md` §"T-15 ·
Modes translation"), which depends on D-2 and has not run.

So the card satisfies a *retired* requirement whose replacement has not been written yet. The
values themselves are present and correct; what is stale is the anchor, and the §12 row still
frames its evidence on `T-BM1`'s `(9)/(3)/(2)`. Verdict WEAK — resolves when T-15 lands as a row,
at which point the Done line should cite it. (The `TurnOnSpot*` values are unaffected either way:
`T-BM1`'s note that turn-on-the-spot "stays a named omission — no tank-only member" is a JC3-side
statement, not a claim that the BmAK values do not exist.)

## A11 — front/rear binding of the `TurnOnSpot` ±0.8 pair. **HOLDS by declaration**

```
456: 0.8      TurnOnSpotFrontTorqueFactor
460: -0.8     TurnOnSpotRearTorqueFactor
464: 2.0      TurnOnSpotModeEngineBrakingFactor
```

The symmetric pair is the classic coin flip: nothing in the values says which end of the car gets
+0.8. The binding here comes from the dump's declaration order at those two offsets, which A1
supports at 42 named points including neighbours in the same class. If the assignment were reversed
the translation would apply opposite torque to front and rear — a visible gameplay bug, invisible in
this data. HOLDS by declaration, and the card is not at fault for it; but it is worth knowing that
`MODES.md` gives no reader any way to see that the front/rear binding is positional.

## A12 — the per-package machinery detects real differences. **HOLDS**

The rework's issue 7 was "one package's value printed as the field's". The current page shows four
columns and the differences are caught, including the Joker's deliberate retune:

```
| `BattleModeImpactMaxDamagePow` | 0x1aec | `float` | factor        | 0.5 | 0.5 | 0.666 | 0.5 | yes |
| `KillFlipTorque`               | 0x1c18 | `float` | engine torque | -200 | -200 | -400 | -200 | yes |
| `KillFlipTorqueDuration`       | 0x1c1c | `float` | s             | 0.5 | 0.5 | 0.75 | 0.5 | yes |
| `ImpactRoadAssistEnemyDuration`| 0x1760 | `float` | s             | 0.333 | 0.333 | 0.75 | 0.333 | yes |
```

(The final column is headed **`serialised`**, not "identical", so `yes` next to four different
values means "a tag matched" — I checked the header before calling this a contradiction, and it is
not one.) These four are exactly the fields excluded from the 31, and their values are plausible
tunings (Joker hits 1/3 harder, flips twice as hard, for 50 % longer). Verdict HOLDS — this is the
machinery working, and it is the best argument that the card's numbers are read rather than assumed.

---

## What a rework would have to touch

1. **A4 (the only BROKEN):** `same_in_all_four` must compare the struct payload
   (`json.dumps(struct_props(t))`, `json.dumps(curve_points(t))`), not `t["value"]`. Then 31 stays
   31 — verified — but the flag can fail.
2. **A1 (missing evidence):** add the 42/42 named-tag test to `MODES.md` (and to
   `REGISTRATION.md`'s build-match section): it is the direct proof that the dump's offsets are this
   build's, and it covers `RVehicleBatmobileBase`, the class that section currently leaves open.
3. **A5:** store the two structs per package, or print "one global struct, verified identical in all
   four" next to the `— — — —` row; and soften "46 serialised **with per-package values**".
4. **A6:** drop "never guessed" from the MODLOG sentence; keep "given with their basis".
5. **A10:** move the Done-line anchor from `T-BM1` to `T-12`/`T-15` when those rows exist, and say
   so in the §12 row.

None of these change a single shipped number. The card's decode is sound; its self-audit is a step
short in exactly one place (A4), and its strongest evidence (A1) is sitting unused in the tag
stream.
