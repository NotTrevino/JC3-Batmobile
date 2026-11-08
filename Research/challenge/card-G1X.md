# Assumption challenge — card G1X · G1 exit gate

Written 2026-10-30. Read-only review: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified; the only file written is this one. No game was launched,
nothing was installed into `D:\Games`, nothing was committed.

**In scope:** `GRAB_BACKLOG.md` §0.5 (R1–R14), §1 (the 75 feature codes), §5's gate paragraph
(lines 570–573), the §12 row (line 1292), `MODLOG.md` §"G1X · G1 exit gate — passed"
(lines 9019–9140), and the card's output `Tools/scripts/g1x_gate.py`. Checks made against the G1
files it points at (`Research/BatmobileGrab/*`), `Working/vendor/BmSDK/*.g.cs`, and the JC3-side
docs where a cross-reading was needed.

**Card as written** (§5): *"`grab_model.py check`, `grab_weapons.py --check`,
`grab_anims.py --check`, `grab_lights.py --check` green; every feature code in §1 that names a
BmAK source has rows in a G1 file or a proven absence. Write a MODLOG section 'G1X' listing the
files."*

---

## VERDICT

**The mechanical result reproduces exactly; the claim it is taken to prove does not hold for
every code.**

Reproduced this session, verbatim:

```
$ python Tools/scripts/g1x_gate.py --check
codes 75: 56 from G1 files, 19 proven absences (no BmAK source); PASS        EXIT=0
```

All four sub-gates are green (quoted in §13 below), and the 75-row MODLOG table is
character-for-character identical to `g1x_gate.py --markdown` (0 differing rows). So the card did
what it said, and the artefacts on disk are consistent with each other.

What does **not** survive is the step from "the gate is green" to "every feature code has its
BmAK value or a proven absence":

| # | assumption | verdict |
|---|---|---|
| 1 | a needle hit means the code's lore value is carried | **BROKEN** — 51 of 56 needles are plain words; two of them survive deletion of the whole fact |
| 2 | ANI-4's turbine is the `fan` bone (R5) | **BROKEN** — the only `fan` bones are four `Wheel_*_Fan`; "turbine" appears nowhere in the grab |
| 3 | ANI-7's steering yoke bone exists (R5) | **BROKEN** — `COCKPIT.md` states there is no yoke; the needle matches that sentence |
| 4 | APP-1 "5 LODs" comes from `MESHES.md` | **BROKEN** — the BmAK mesh ships 3 LODs; 5 is the build-side target |
| 5 | "56 satisfied" counts carried facts | **BROKEN** — ARM-5/AUD-6/AUD-7 are satisfied by documents recording an *absence* |
| 6 | the 19 absences are "proven" | **BROKEN as a class** — passed unconditionally by the script, never tested; 4 reasons contradicted by the repo |
| 7 | sideswipe targeting is runtime because `OFFSETS.json` has 0 rows | **WEAK** — that file cannot contain a named tag by construction; conclusion survives on other evidence |
| 8 | Health 1200 is fleet-wide ("all 3 archetypes") | **WEAK** — there are four `RVehicleBatmobile` archetypes; the Joker has no row |
| 9 | the ram/impact numbers are usable as decoded | **WEAK** — every value is there, no unit is stated anywhere |
| 10 | those values' provenance class can be called `decoded` | **WEAK** — they are `sdk-layout`, which is not one of R4's six classes |
| 11 | the gate's file for a code is the file §1 names | **WEAK** — diverges for APP-2, DIM-1, CAM-1/CAM-2, LGT-1, ANI-4/ANI-7 |
| 12 | "every feature code in §1" = the gate's 75 rows | **HOLDS** — set equality verified |
| 13 | the four sub-gates are green and the MODLOG table is generated | **HOLDS** — re-run; table identical |

**Bottom line:** G1X passes its own gate, but the gate is a text-presence test, not a value test.
Four of the 56 "satisfied" rows are wrong or empty as stated (ANI-4, ANI-7, APP-1's LOD count,
and the ARM-5/AUD-6 "satisfied by absence" pair), and 4 of the 19 "proven absences" are asserted
against the class dump or against §1's own carrier column. The honest exit state is
**56 → 52 satisfied, 19 → 23 absences, with 2 needing a re-decode**, not "passed". The fix is
mechanical and cheap: anchor needles on a line that states the fact (or a value), and give every
`not-g1` row a search (class dump + CHAIN + OFFSETS) so "proven" means something.

---

## 1. A needle hit means the code's lore value is carried

**Why the card rests on it.** `g1x_gate.check()` is the whole proof of the second half of the
gate:

```python
primary = read_text(os.path.join(G1, r["files"][0]))
ok = r["needle"].lower() in primary.lower()
```

One case-insensitive substring, in the first file named, anywhere in it.

**Test.** Enumerate every `g1` row: count the occurrences of its needle and print the line the
first hit lands on.

```
$ python - <<'EOF'   # imports g1x_gate, prints code / file / occurrences / needle / first hit line
APP-1   MESHES.md      n=36  LOD    | # Batmobile meshes - geometry and every LOD (G1-4, G1-5)
APP-2   SLOTS.md       n=18  CarPaint | | 0 | `BatmobileV3_Wheel_V2_MIC` | MaterialInstanceConstant | ...
ANI-5   ANIMATIONS.md  n=952 fin    | * `fins/air-brakes` - `Aero_Flap*` / `Jet_Fins`.
ANI-4   BONES.md       n=16  fan    | | 6 | `Wheel_Frnt_Left_Fan` | `Wheel_Parent_F_L` | -1.211 | ...
ANI-7   COCKPIT.md     n=3   yoke   | | **yoke / steering control** | **- none -** | - | **absent**...
FX-4    DAMAGE_RULES.md n=11 Death  | `PersistentOptions`, `DDA_DeathsInRoom` - Batmobile health ...
LGT-1   LIGHTS.md      n=2   cone   | | package | socket | type | component | ... | inner cone | outer cone | ...
```

Distribution: **56 g1 rows, 5 numeric needles** (`MK2`, `7.026`, `1.36`, `1200`, `60`), **51 plain
words** (`bone`, `wheel`, `collision`, `Door`, `weapon`, `speed`, `battle`, `emissive` …). A word
needle cannot fail while the file still talks about the topic at all.

**Removal test (in memory, no file written).** Delete every line that states the fact, then ask
whether the needle still matches:

```
Research/BatmobileGrab/ANIMATIONS.md | needle 'fin'  | lines removed 87 (Jet_Fin|Aero_Flap|fins/air-brakes) | matches remaining 920 | gate would pass: True
Research/BatmobileGrab/DAMAGE_RULES.md | needle 'Death' | lines removed 8 (DeathExplosion) | matches remaining 3 | gate would pass: True
Research/BatmobileGrab/BONES.md | needle 'fan' | lines removed 16 (Wheel_\w*_Fan) | matches remaining 0 | gate would pass: False
Research/BatmobileGrab/COCKPIT.md | needle 'yoke' | lines removed 30 (blank lines) | matches remaining 3 | gate would pass: True
```

The `fin` matches that keep the gate green are `_L_Finger` ×426, `Face_Finale` ×52,
`Final_Takedown_*`, i.e. 920 of 952 — the fin rows are 23. FX-4's surviving matches are
`DDA_DeathsInRoom` (line 283) and `death`/`destroy` inside a regex listing (line 421). ANI-7's only
three hits are the sentence saying the yoke does not exist.

**Verdict: BROKEN.** The gate answers "does this file mention this word", which is neither
"the file carries the value" nor "the value is still there". Two of its 56 rows (ANI-5, FX-4) pass
by accident; one (ANI-7) passes on its own negation.

---

## 2. ANI-4 — "the turbine is the `fan` bone in BONES.md" (R5: name read as behaviour)

**Why the card rests on it.** MODLOG, G1X section: *"each was re-pointed at the doc that actually
holds it (… the turbine is the `fan` bone in `BONES.md` …)"*, and the G1X table row is
`ANI-4 | BONES.md | turbine fan bone`.

**Test.**

```
$ grep -n -i "fan" Research/BatmobileGrab/BONES.md
48:| 6 | `Wheel_Frnt_Left_Fan` | `Wheel_Parent_F_L` | ...
58:| 16 | `Wheel_Frnt_Right_Fan` | ...
65:| 23 | `Wheel_Rear_Left_Fan` | ...
112:| 70 | `Wheel_Rear_Right_Fan` | ...

$ grep -ril "turbine" Research/BatmobileGrab
(no output — including every .md and .json in the folder)
```

All four `fan` bones are children of `Wheel_Parent_*` — wheel bones, not the rear turbine. With
those 16 lines removed, the needle has **0** matches (§1 table). So "fan" never referred to a
turbine anywhere in the grab; the identity was inferred from the substring, and there is no
`turbine` row, bone, mesh or animation in the whole G1 folder.

**Verdict: BROKEN.** ANI-4 ("turbine fan spins with engine RPM") has no BmAK carrier that the
files show. The requirement may still be real — the rear of the AK Batmobile does have a turbine
in the game — but G1X records it as decoded, and the data on disk does not contain it. It belongs
in the 19 absences (`UNKNOWN`, no BmAK row) until a bone or mesh is found.

---

## 3. ANI-7 — "steering yoke bone" (R5)

**Why the card rests on it.** Table row: `ANI-7 | COCKPIT.md, BONES.md | steering yoke bone`,
needle `yoke`, first file `COCKPIT.md`.

**Test.**

```
$ grep -n -i -C2 "yoke" Research/BatmobileGrab/COCKPIT.md
24:| **yoke / steering control** | **- none -** | - | **absent**: the box |x| < 0.17,
    y 1.00..1.30, z -1.60..-1.10 holds **4 faces of any material** (section 6) |
92-## 6. Gaps - stated, not smoothed
94:1. **No yoke / steering control.** The hand box ... contains **4 faces of any material**
   ... Consequence for ANI-9: the seated pose has nothing to grip; a grip point, if one is
   wanted, must come from the JC3 side (G2-19).

$ grep -icE "steer|yoke" Research/BatmobileGrab/BONES.md
0
```

The needle matches the gap statement, and `BONES.md` — the second file the gate only checks for
existence — contains no steer or yoke bone at all.

**Verdict: BROKEN.** ANI-7's requirement ("steering yoke turns with steering") is satisfied by
nothing: the cockpit has no yoke geometry and the rig has no yoke bone. It is an absence the card
counts as a fact. (R5 exactly: the member's name was read as its behaviour — here even the name is
absent.)

---

## 4. APP-1 — "5 LODs, 19 material slots", attributed to `MESHES.md`

**Why the card rests on it.** MODLOG table: `| APP-1 | MESHES.md, SLOTS.json | 5 LODs, 19
material slots |`. §1 line 124 says the same: "all 5 LODs, 19 material slots".

**Test.**

```
$ python - <<'EOF'  # MESHES.json, generated by grab_meshes.py
Playable_Batmobile_SF Batmobile_V2 lods= 3 [0, 1, 2] materials= 19
...
EOF
$ grep -rn -iE "5 lod|five lod|LOD3|LOD4" Research/BatmobileGrab
(no output)
$ grep -n "LOD" Research/BatmobileGrab/MESHES.md | head -3
1:# Batmobile meshes - geometry and every LOD (G1-4, G1-5)
8:| mesh | package | vertices | LOD0 | LOD1 | LOD2 | bones | materials | size (m) |
```

`MESHES.md`/`MESHES.json` document **three** LODs for `Batmobile_V2` (299,837 / 144,857 / 21,720
faces). The number 5 appears in the backlog only as a *build* target — line 1007, "Emit 5 LODs per
part with the same decimation settings as the body", i.e. the JC3 side. The 19 material slots half
is solid (`SLOTS.md` rows 0–18, `MESHES.json` `"materials": 19`).

**Verdict: BROKEN for the LOD count.** A JC3-side build setting has been copied into a row that
claims to be satisfied by the BmAK grab. Either APP-1's text becomes "3 LODs shipped, 5 emitted",
or the fact string is corrected. This is the R11 failure mode in miniature: a typed number in a
table that is supposed to be generated.

---

## 5. "56 satisfied by G1 files" counts carried facts

**Why the card rests on it.** The gate's summary line and the MODLOG headline
("75 codes: 56 satisfied by G1 files, 19 proven absences") present 56 as codes whose BmAK value is
in hand.

**Test.** Read what the three "absence-shaped" satisfied rows actually point at.

```
$ sed -n '299,312p' Research/BatmobileGrab/DAMAGE_RULES.md
## 5. Regeneration - answered: a mechanism exists, its value does not ship
- `RVehicleBatmobileBase.HealthRecoverRate` is a **TArray<float> at +8220** ...
- **No archetype overrides it** ... the shipped number is whatever the native CDO ... holds.
...
Verdict for the row: **mechanism = yes (decoded), value = unknown from the files**

$ grep -n -A3 "BML_Impacts" Research/BatmobileGrab/AUDIO_FEATURES.md
729:### `Engine.BML_Impacts` (4)
731:`Play_Batmobile_Destroyed`, `Play_Batmobile_Destroyed`, `Play_Batmobile_Destroyed`, `Play_Batmobile_Destroyed`

$ sed -n '253,256p' Research/BatmobileGrab/AUDIO_FEATURES.md
### horn
no horn event ships in these packages - the only `Beep` events are tank lock-on UI
```

- **ARM-5** is "satisfied" by a section whose verdict is *value = unknown*.
- **AUD-6** is "satisfied" by "impact bank absent" — and the file it points at shows
  `Engine.BML_Impacts` **exists** as a switch with 4 rows, all `Play_Batmobile_Destroyed`. The
  bank is not absent; it carries only death sounds. §1's "`BML_Impacts` is **absent** (T-AU3)" and
  the gate's "impact bank absent (named omission)" are both contradicted by line 729.
- **AUD-7** is "satisfied" by the sentence "no horn event ships".

**Verdict: BROKEN as a count.** Three of the 56 are conclusions about absence, not decoded values,
and one of them (AUD-6) rests on a fact the same folder refutes. The gate has three outcomes in
practice — fact present, absence recorded, absence asserted — and only two words.

---

## 6. The 19 "proven absences" are proven

**Why the card rests on it.** MODLOG: "Codes that name no BmAK source at all … are the 'proven
absence' half and carry their reason." The reasons are hand-written strings; nothing tests them.

**Test 1 — structurally, they cannot fail:**

```python
for r in rows():
    if r["kind"] == "not-g1":
        table.append({**r, "pass": True, "detail": r["absence_reason"]})
        continue
```

`pass: True` unconditionally, for every `None`-file row, whatever the data says. The docstring's
"checked, not just assumed" for the WLD family is a comment, not a check.

**Test 2 — four of the nineteen are contradicted by the repo.**

*(a) DIM-3, "BmAK carries no absolute mass".* There is a `Mass` member:

```
$ sed -n '4497,4506p' Working/vendor/BmSDK/Pawn.g.cs
    /// FloatProperty: Mass
    public unsafe float Mass
    {
        get { return BmSDK.Framework.MarshalUtil.ToManaged<float>(Ptr + 1004); }
```

No archetype serialises it (`OFFSETS.json` has no field at offset 1004 across its 423 rows), so
the *value* is indeed not in the files — the same status FOOTAGE.md gives the `AirControl*`
fields ("declared … **not serialised**"). The card states a stronger, name-level claim than the
data supports, and it did not do the class-dump search it did for AirControl.

*(b) ARM-1, "play behaviour T-DM9; no BmAK value".* The same folder decodes a shield mechanism:

```
$ sed -n '285,290p' Research/BatmobileGrab/DAMAGE_RULES.md
- **The weapon generator is the shield**: `TakeDamage` calls
  `DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)` ... which reads
  `WeaponGeneratorPower`, `bWeaponGeneratorShielding`, `WeaponUnavailableReason`, ...
```

That is a behaviour row with a take, which is what R5 asks for; calling ARM-1 "no BmAK source"
because no number is attached discards it.

*(c) APP-7, "user rule R1; BmAK has no deform".* The grab ships damage-state geometry and masks:
`MESHES.md` lists `Batmobile_V3_Destroyed` (57,101 verts), `SLOTS.md` shows
`Damage_Chapter_Mask` textures on the body, and `ASSETS.md` lists a `Damage_States` package.
"Deform" and "damage states" are not the same thing, and the requirement is a user decision
(R1 says do not conform to JC3 mechanics) — but the *reason* "BmAK has no deform" is an
unsupported claim sitting next to shipped destroyed-mesh evidence.

*(d) HDL-6, "air control has no JC3 member yet".* §1's own HDL-6 row names its carriers:
"`gravity_multiplier_*`, `takeoff_pitch_damping` — re-check". The absence reason contradicts the
row it is excusing.

**Verdict: BROKEN as a class.** 4 of 19 reasons are contradicted (DIM-3, ARM-1, APP-7, HDL-6);
the remaining 15 (WLD-1…8 by construction of the 3-column table, HDL-1/3/4/5 as project/wiki
values, MOD-5 as a rule, ANI-1 as live behaviour) are correctly out of scope for a BmAK grab, but
they are "not a BmAK question", not "searched and not found".

---

## 7. Sideswipe: "`OFFSETS.json` carries 0 rows ⇒ runtime state, not archetype defaults"

**Why the card rests on it.** MODLOG opens with the sideswipe/ram paragraph, and
`DAMAGE_RULES.md` §3.3.1 closes with: *"`OFFSETS.json` carries **0** rows for any of these: they
are runtime state and script functions, not serialised defaults. So … choosing the victim … is
native and not readable from the files."*

**Test.**

```
$ grep -c -i "sideswipe" Research/BatmobileGrab/OFFSETS.json
0
$ python - <<'EOF'   # what OFFSETS.json actually contains
423 fields | decisions: {'named-sdk': 380, 'named-element': 40, 'named': 3}
classes: RBatmobileAllegianceSwitcher … RBatmobileWinch, RVehicleBatmobile, RVehicleSimBatmobile, SVehicleWheel
EOF
$ sed -n '311,318p' Tools/scripts/grab_offsets.py
        for path, t in g.tags(r):
            if t.get("name") or "offset" not in t or "value" not in t:
                continue
```

`grab_offsets.py` **skips every tag that carries its own name**. `OFFSETS.json` is by
construction a file of *unnamed* fields resolved through the SDK layout; a named member such as
`SideSwipeTargetsList` could never appear in it. So "0 rows in OFFSETS.json" is not evidence about
the archetype — it is a property of the extractor. (The same non-sequitur is used in §5 for
`HealthRecoverRate`: "absent from `CHAIN.json` (0 mentions) and from the 423-field `OFFSETS.json`
binding (0 rows)".)

**The conclusion nevertheless survives, on different evidence I did find:**

```
$ grep -c -i "sideswipe" Research/BatmobileGrab/CHAIN.json
0
$ python - <<'EOF'   # no offset row in the 4779..4950 window either
classes near 4700-4950: RVehicleBatmobile ×6 (none at 4779 or 4900)
EOF
$ grep -n "SideSwipe" Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs | head -5
4779: /// BoolProperty: SideSwipeInSweetSpot
5595: /// ObjectProperty: SideSwipeTargetsList
1458: /// Function: GetCurrentSideSwipeTarget
1476: /// Function: GetSideSwipeTarget
```

So: the members are real declarations (types confirmed: `RInteractionClass`, `bool`, and function
signatures), no named tag in `CHAIN.json`, no unnamed field at their offsets. Runtime/native is
the right conclusion — but the card reached it by an argument that cannot distinguish "not
serialised" from "not searched".

**R5 rider.** The §3.3.1 table's *roles* ("the candidate set a sideswipe picks from", "true on the
frames the hit lands in the sweet spot") are names read as behaviour. The class dump gives the
type, not the semantics. `CrushedThisFrame`/`BouncedThisFrame` per-frame contact state is a
plausible reading, not a decoded one.

**Verdict: WEAK.** Conclusion holds, reasoning is invalid; the role column is name-inference and
should say so.

---

## 8. "`Pawn.Health` = 1200 on all 3 Batmobile archetypes" is fleet-wide

**Why the card rests on it.** ARM-2's satisfying fact is "Health 1200 and the damage rules", and
the MODLOG repeats the number without qualifier.

**Test.**

```
$ grep -n "Pawn.Health" Research/BatmobileGrab/DAMAGE_RULES.md
280:- **`Pawn.Health` = 1200** on all **3** Batmobile archetypes (`BatmobileFunhouse`, `Batmobile_MK2`, `Batmobile`).
574:| ... `BatmobileFunhouse` | `Pawn.Health` | IntProperty | 1200 | sdk-layout |
627:| ... `Batmobile_MK2`       | `Pawn.Health` | IntProperty | 1200 | sdk-layout |
654:| ... `Batmobile`           | `Pawn.Health` | IntProperty | 1200 | sdk-layout |

$ grep -oE "Playable_Batmobile[A-Za-z0-9_]*_SF\.[A-Za-z0-9_]+" Research/BatmobileGrab/DAMAGE_RULES.md | sed 's/.*_SF\.//' | sort -u | grep -i batmobile
Batmobile
BatmobileFunhouse
Batmobile_MK2
JokersBatmobile
$ grep -c "JokersBatmobile.*Health" Research/BatmobileGrab/DAMAGE_RULES.md
0
```

Four `RVehicleBatmobile` archetypes ship; the doc's own §3.3 table gives the Joker's impact
values, and APP-8 (the Jokerfied skin) is an optional variant of this mod. The Joker archetype has
no Health row — either it does not serialise one (value = native CDO, i.e. UNKNOWN) or it was not
looked at. "All 3" is a sample presented as the fleet.

**Verdict: WEAK.** 1200 is solid for the three; the claim's scope word is wrong. If the Joker
variant is ever built (APP-8, D-5), ARM-2 does not cover it.

---

## 9. The ram/impact numbers are "already decoded" (unit convention)

**Why the card rests on it.** MODLOG: *"the outgoing half was already decoded — `ImpactMinDamageSpeed`
/ `ImpactMaxDamageSpeed` 20/150 (Joker 40/180), `BattleModeImpactMinDamageSpeed` /
`MaxDamageSpeed` 120/540 …"*. The values are real (§3.3 table and the 1200-style rows). The card
then treats them as translation-ready.

**Test.**

```
$ grep -n -iE "km/h|cm/s|mph|units?:" Research/BatmobileGrab/DAMAGE_RULES.md
(no output)
```

The unit table in §3.3 has a `shipped` and a `Joker` column and no unit row. Compare
`CAMERA.md`, which does state its convention:

```
33:Units: FOV is degrees; `*InterpMaxSpeed` is UE3 cm/s (3000 = 30 m/s = 108 km/h);
   `*MaxExtraTranslation` ...
```

Read as UE3 cm/s, `ImpactMinDamageSpeed` 20 = 0.72 km/h and `ImpactMaxDamageSpeed` 150 =
5.4 km/h, i.e. max ram damage below walking pace. Read as km/h, 20→150 km/h is a plausible damage
ramp and 540 km/h in battle mode is an unreachable cap (normal for a tuning curve). The two
readings differ by a factor of 3.6 and the difference is the whole feature.

**Verdict: WEAK.** Values decoded, unit not. This is exactly the class of gap the backlog asks to
be written down (R4: "`assumed` is not buildable"), and it is written down nowhere in the file the
card points at.

---

## 10. Values labelled `sdk-layout` can be called "decoded"

**Why the card rests on it.** ARM-2/ARM-5's facts come from the big tables in `DAMAGE_RULES.md`,
where every such row ends `… | sdk-layout`. The MODLOG calls them "decoded".

**Test.**

```
$ python -c "...OFFSETS.json decision counts..."
decisions: Counter({'named-sdk': 380, 'named-element': 40, 'named': 3})
$ sed -n '420,424p' Research/BatmobileGrab/DAMAGE_RULES.md
   gave the row its name (`sdk-layout` = class-dump layout, `stream` = the tag stream itself).
```

The value is read from the tag stream at an offset; the *name* comes from the SDK class layout.
R4's allowed classes are `decoded`, `decoded (fleet)`, `derived`, `class`, `epe`, `read`
(`T_PLAN.md` line 25) — `sdk-layout` is none of them, so either the doc's own label is a seventh
class the rule does not know, or these rows should be `read`.

**The naming oracle is real, which is why this is WEAK and not BROKEN:**

```
$ sed -n '184,190p' Research/BatmobileGrab/REGISTRATION.md
- `RVehicleSimBatmobile`: dump size 1220; ... *all 165* declared rows land on the same offset in
  the dump. 147 match by name directly; the other 18 are bools that share one bitfield word ...
```

147/165 name matches plus anchored native writes (`SetDriveMode` at 0x3B0) is a decent
independent check that offset→name is right for this build.

**Verdict: WEAK.** The numbers are trustworthy by the registry oracle; the word "decoded" and the
class name `sdk-layout` are not reconcilable with R4 as written.

---

## 11. The gate's file for a code is the file §1 names as its lore source

**Why the card rests on it.** The card's criterion is "every feature code in §1 that names a BmAK
source has rows in a G1 file". The gate encodes a hand-typed `(code, [files], needle, fact)` table;
nothing compares it with §1's third column.

**Test.** Diff the two by hand for the codes where they should agree:

| code | §1 lore source | gate's file | finding |
|---|---|---|---|
| APP-2 | `MATERIALS.md`, `VALUES.json` | `SLOTS.md` (needle `CarPaint`) | `grep -c -i carpaint MATERIALS.md VALUES.json` → **0** and **0**; `SLOTS.md` only names the block, no parameters |
| DIM-1 | "PSKX at real cm (`bat_assemble.py`)" | `POSES.md` (`7.026`) | 7.026 ✓; but 5.029 wheelbase / 2.416 / 2.569 track appear **only** in `Research/JC3Grab/` (the built mod), not in any BatmobileGrab doc |
| CAM-1 / CAM-2 | `bat_base.ctunec` (a JC3 tune) | `CAMERA.md` | gate is right and §1 is stale — `CAMERA.md` decodes `BattleModeCamFOV 60`; CAM-1's `BmAK` values exist there too |
| LGT-1 | "`SVehicleLight` in `.epe`" | `LIGHTS.md` (`cone`) | fine — LIGHTS.md has the cone/radius/colour rows |
| ANI-4 / ANI-7 | bone / cockpit bone | `BONES.md`, `COCKPIT.md` | the files are right, the facts are not (§2, §3) |

**Verdict: WEAK.** Two codes (APP-2, DIM-1) are pointed at a file that does not hold the value §1
promises; two (CAM-1/2) show §1 is the stale side. The gate does not check that the two describe
the same code, so this drift is invisible to `--check` and would survive any regeneration.

---

## 12. "Every feature code in §1" really is the gate's 75 rows

**Test.**

```
$ awk 'NR>=120 && NR<=575' GRAB_BACKLOG.md | grep -oE '\b(APP|DIM|ARM|WPN|HDL|MOD|AUD|ANI|LGT|FX|CAM|HUD|WLD)-[0-9]+\b' | sort -u | wc -l
75
$ python Tools/scripts/g1x_gate.py --check
codes 75: 56 from G1 files, 19 proven absences (no BmAK source); PASS
```

Set equality between the code names in §1 and `G1_ROWS` + `WLD_CODES` (75), no code in one and
missing from the other, no duplicate.

**Verdict: HOLDS.** The coverage claim is true: every code in §1 is represented exactly once, and
the 56/19 split sums to 75.

---

## 13. The four sub-gates are green and the MODLOG table is the generated one

**Why the card rests on it.** The gate as defined in §5 is *four* commands plus the code table; the
card's own script cannot run any of them (it never imports or spawns the readers). The MODLOG
quotes them instead.

**Test — re-ran all four, plus the MODLOG-vs-`--markdown` diff.**

```
$ python Tools/scripts/grab_model.py check
OK: grab output matches schema 6 and its own summary.                              EXIT=0
$ python Tools/scripts/grab_weapons.py --check
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences,
      10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows        EXIT=0
$ python Tools/scripts/grab_anims.py --check
PASS: 253 sequences, 13 sets, 3 trees, 253 PSA sequences, 3147888 keys, 309 notifies
      (204 sound, 35 script); 253/253 named, 253 bone lists, 253 mechanisms;
      13/13 keyframe files present                                                   EXIT=0
$ python Tools/scripts/grab_lights.py --check
OK: 101 entries / 4 rigs, 6 orphan sockets, 0 missing bones
OK: 36 Batmobile-rig components carry colour and intensity (schema 2)                EXIT=0

$ python - <<'EOF'   # MODLOG G1X table vs g1x_gate.py --markdown
MODLOG rows: 75 gate rows: 75 codes equal: True differing: 0 []
EOF
```

All four are green and every number matches the MODLOG text (the MODLOG omits two parentheticals —
"(9 launcher targets, 1 unfired)" and "253 bone lists, 253 mechanisms" — with the numbers
identical). The 75-row table is not hand-maintained drift: it equals the generator's output.

**Verdict: HOLDS**, with one caveat worth recording: because `--check` does not run the readers,
a future session that trusts "`g1x_gate.py --check` green" alone has verified only the text
presence of 56 words. The card's own Done line should say which command proves what.

---

## What would make this card honest (no new facts needed)

1. Give the 51 word-needles a *line anchor* — the claim's own sentence, or a value — and add a
   negative needle where the fact is an absence (`"no horn"`, `"value does not ship"`). This alone
   turns ANI-4, ANI-5, ANI-7, FX-4 and AUD-6 red.
2. Move ANI-4 and ANI-7 to the absence half with `UNKNOWN` and the reason ("no turbine bone/mesh
   in the grab"; "`COCKPIT.md` §6: no yoke"). Count becomes 54/21.
3. Split the two halves properly: `fact present` / `absence recorded` / `absence asserted`, and
   make the third pass only with a search log (class dump + `CHAIN.json` + an offset window).
   DIM-3, ARM-1, APP-7 and HDL-6 then get their reasons fixed instead of silently passing.
4. Correct APP-1 to "3 LODs shipped (5 emitted by the build)" and drop "5 LODs" from the fact
   string.
5. State the unit for `Impact*Speed` (or mark it UNKNOWN) and keep `sdk-layout` out of the word
   "decoded", per R4.
