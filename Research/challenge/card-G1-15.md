# G1-15 · Audio by feature, decoded to WAV — assumption challenge

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), card **G1-15** (line 485), its §12 row (line 1283),
`MODLOG.md` §"G1-15 · Audio by feature, decoded to WAV" (intended + done, lines 8310–8380),
and the card's outputs: `Research/BatmobileGrab/AUDIO_FEATURES.{json,md}`,
`Tools/scripts/bmak_audio_features.py`, plus `AUDIO_MAP.json`, `AUDIO.md`, `objects.jsonl`,
`MECHANICS.md`, the loose banks in `Working/Audio/`, and the Arkham Knight install under
`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole`.

Read-only apart from this file. No game launched, nothing written to any game folder, no commit.
Quoted output is verbatim from commands run in this session.

---

## VERDICT

The card's *measurement* half is sound and reproducible: the FNV-1 id rule is pinned by
elimination (361/361 rows, FNV-1a 0/361), the loudness meter hits the BS.1770 anchor exactly
(−3.01 LUFS for a 0 dBFS 997 Hz sine), and all 423 WAVs are on disk at 48 kHz with durations and
peaks that re-measure to the stored digits. Its *inventory* half does not hold. Three separate
claims that "no such audio exists" are falsified by objects already in the repo:

* **`winch` is not empty.** `RBatmobileWinch` in all three Batmobile packages names five events:
  `Engine.Play_BML_WinchDetach`, `…WinchFire`, `…Winch_Attatch`, `…Winch_Cable`,
  `…Winch_Cable_Tension`.
* **`emp` is not empty.** `RBatmobileEMPMissile` names `Engine.Play_Batmobile_ApRocket_Fire`,
  `…ApRocket_Flight`, `…ApRocket_Up`.
* **The 24 streamed rows are recoverable, and are not "all voice".** 16 of them are voice and 8
  are engine; and **16 of 16** voice rows point at a RIFF/WAVE payload inside
  `English(US)/INT_*.wad`, keyed by **FNV-1 of the bank name** — the card's own hash, never applied
  to the 3.6 GB of `WWAD` archives it never opened.

| # | assumption | verdict |
|---|---|---|
| A1 | Wwise ids are FNV-1 of the lower-case name | HOLDS |
| A2 | "the 361 events" are the car's events | **WEAK→BROKEN** (361 rows = 118 events, 4 packages; `Engine.*` events invisible) |
| A3 | "no winch event ships" | **BROKEN** (5 named winch events referenced by `RBatmobileWinch`) |
| A4 | "no EMP sound ships" | **BROKEN** (3 named rocket events referenced by `RBatmobileEMPMissile`) |
| A5 | "no horn event ships" | WEAK (true of names; the horn rule does fire on 2 lock-beep events and is preempted) |
| A6 | the 24 streamed rows have no bytes on disk | **BROKEN for the 16 voice rows** (INT wads, bank-name key) |
| A7 | "the 24 streamed rows are all voice lines" | **BROKEN** (16 voice + 8 engine) |
| A8 | "every one of the 447 media ids is decoded to a 48 kHz WAV" | **BROKEN** (423/447, its own summary says so) |
| A9 | the RTPC entry layout and its 5 anchors | HOLDS (with an unstated false-positive risk) |
| A10 | "19 AkParameterName columns" back the 22 named params | **BROKEN** (7 from `AkParameterName`, 15 hash-matched from name tables) |
| A11 | "the BML_Winch parameters ship" | **BROKEN as stated** (no such bound param; the *events* ship) |
| A12 | roots, peaks and integrated loudness are measured correctly | HOLDS |
| A13 | 423 WAVs, 48 kHz, 971.4 s | HOLDS |
| A14 | one feature group per event, by name rule | WEAK (3 ambiguous names; name-not-behaviour) |
| A15 | the loop bit is genuinely unknown | HOLDS (declared, probed, not guessed) |
| A16 | the 90 `missing-bank` rows are explicit | HOLDS, but 6 groups are empty because of grab coverage, not the car |

---

## A1 — Wwise ids are FNV-1 of the lower-case name — HOLDS

**Claim.** "Wwise ids are FNV-1 of the lower-case name (offset `0x811C9DC5`, prime `0x01000193`,
XOR then multiply): it reproduces **118/118** event ids in `AUDIO_MAP.json`."

**Test.** Recompute both variants over all 361 rows:

```
FNV-1 reproduces 361/361 ; FNV-1a reproduces 0/361
distinct event names: 118 distinct ids: 118
```

The variant is pinned by elimination (XOR-then-multiply, not multiply-then-XOR), and the rule
holds on every row rather than on the 118 distinct names alone.

**Result: HOLDS.** This is the strongest single fact in the card, and it is what makes A6's
missed key the more surprising.

## A2 — "the 361 events" are the car's events — WEAK, and broken at the edges

**Claim.** Card "In": *"`AUDIO_MAP.json` (361 events, 447 WEMs)"*; Done: *"every one of the 361
events is in exactly one feature group"*.

**Test.** Two counts, one scope:

```
AUDIO_MAP rows by package: {'Playable_BatmobileFunhouse_SF': 90, 'Playable_BatmobileJoker_SF': 89,
                            'Playable_BatmobileMK2_SF': 91, 'Playable_Batmobile_SF': 91}
distinct event names: 118
```

So "361 events" are 361 *package-event rows* (each event appears ~3× across the skins) over
**118** distinct events, and every one of them is an `AkEvent` **object inside the four Playable
packages**. Events the car *references by path* into other packages are outside that set — for
example, from `objects.jsonl`:

```
"Engine.Play_Batmobile_ApRocket_Fire"      12 references
"Engine.Play_Batmobile_ApRocket_Flight"    14 references
"Engine.Play_Batmobile_ApRocket_Up"         8 references
"Engine.Play_BML_WinchDetach" / WinchFire / Winch_Attatch / Winch_Cable / Winch_Cable_Tension
```

None of those eight names occurs in `AUDIO_MAP.json` (`grep -c "Play_Batmobile_ApRocket_Fire"
AUDIO_MAP.json` → `0`), and `Play_Batmobile_ApRocket_Fire`'s id `0x73EA0A36` is in none of the 41
exported banks or the loose `.bnk` files.

Against a check inside the card's own scope, the inventory is complete: every `Play_*Batmobile*`
name referenced in `objects.jsonl` that could be matched appears in the 118 (84 distinct names,
0 missing). The gap is exactly the cross-package path references.

**Result: WEAK for the wording, BROKEN for the downstream reading.** "361 events" overstates the
number of distinct sounds 3× and hides that the car's own winch/EMP audio lives in a package the
inventory does not read.

## A3 — "winch: no event plays one" — BROKEN

**Claim** (`AUDIO_FEATURES.md`, and `GROUP_NOTE["winch"]` inside the script):
*"no AkEvent in the grab plays Winch audio (the BML_Winch parameters ship, the events do not)"*;
MODLOG: *"winch / emp / horn stay empty — no event in these packages plays one"*.

**Test.** Read the winch weapon object in `objects.jsonl`:

```
rows referencing Batmobile_Winch: 3
 Playable_Batmobile_SF      RBatmobileWinch Batmobile_Winch
   Play_ refs: ['Engine.Play_BML_WinchDetach', 'Engine.Play_BML_WinchFire',
                'Engine.Play_BML_Winch_Attatch', 'Engine.Play_BML_Winch_Cable',
                'Engine.Play_BML_Winch_Cable_Tension']
 Playable_BatmobileMK2_SF   RBatmobileWinch Batmobile_Winch   (same five)
 Playable_BatmobileFunhouse_SF RBatmobileWinch Batmobile_Winch (same five)
```

Five winch events, referenced from the car's own winch weapon in every skin. They are absent from
the 118 only because their `AkEvent` objects live in the `Engine` package, which `AUDIO_MAP` does
not inventory as events.

**Result: BROKEN.** The empty `winch` group is an artefact of the inventory's package scope, and
the note asserts the opposite of what the repo already contains. This matters directly to AUD-7
and to any winch implementation: the plan would be told the donor has no winch audio.

## A4 — "emp: no EMP sound ships" — BROKEN

**Claim.** `AUDIO_FEATURES.md` group note: *"no AkEvent in the grab is an EMP sound"*.

**Test.** `MECHANICS.md` and `objects.jsonl`, EMP missile launcher rows (all three packages):

```
Playable_Batmobile_SF | Batmobile_EMP_Missile_Launcher | RBatmobileEMPMissile | 1 | MissileLaunchSockets |
  Projectiles.Batmobile_EMPMissile_Projectile_ForCars; Ww_CHR_BatmanAlerts.Play_HUD_fail;
  Conversation.Main_Ch03_S24_Cityx_Pt3_Callcar; Projectiles.Batmobile_EMPMissile_Projectile_ForCars;
  Engine.Play_Batmobile_ApRocket_Fire
```

and the same object also references `Engine.Play_Batmobile_ApRocket_Flight` and
`…ApRocket_Up`. Three EMP rocket events, named by the launcher that the mod has to re-implement.

**Result: BROKEN** for the same reason as A3 (scope), with the extra wrinkle that `Play_HUD_fail`
— which *is* in the 118 and is grouped `lock-on-ui` — is one of the EMP launcher's own sounds.

## A5 — "honk/horn" — WEAK

**Test.** Token search over the 118 names:

```
winch     0  []
emp       0  []
horn      0  []
honk      0  []
radio     0  []
nitro     0  []
boost     0  []
beep      8  ['Play_Tank_Heavy_LockBeep', 'Stop_VEH_Tank_Heavy_LockBeep', ...]
```

and the rule table itself:

```
distinct events: 118 | matched by >1 rule: 3
   Play_BattlemodeEngine          ['battle-mode', 'engine']
   Play_Tank_Heavy_LockBeep       ['lock-on-ui', 'horn']
   Stop_VEH_Tank_Heavy_LockBeep   ['lock-on-ui', 'horn']
```

So the horn rule *does* fire — twice — and is preempted by `lock-on-ui` because `lock-on-ui`
comes first in `RULES`. The group is empty by rule order, not only by absence.

**Result: WEAK.** "No horn event ships in these packages" is true of the names actually present
(no `Horn`/`Honk` token anywhere, no horn reference in `objects.jsonl`), which is what AUD-7
needs. But `horn`'s zero in the table is partly a precedence artefact and should not be quoted as
evidence on its own.

## A6 — The 24 streamed rows have no bytes on disk — BROKEN for the voice half

**Claim** (`AUDIO_FEATURES.json` `decode_errors[*].error`, MODLOG):
*"streamed media: no DIDX entry in any of the 14 bank files searched
(Working/Audio/*.bank|*.bnk, CookedPCConsole/SFX/*.bnk, English(US)/*.bnk); the shipped bank is
HIRC-only and the bytes are not on disk"*, and *"there are no loose `.wem` files or matching
wad-index entries"*.

**Test.** The search space is 14 `.bnk` files. The install also carries **22 `WWAD` archives**
that were never opened:

```
wads: 22   (SFX/SFX_1.wad 1,705,156,608 B; English(US)/INT_*.wad ~1.9 GB total)
header: 57 57 41 44 | version 2 | u64 count | ... | u64 index_len | ... | u64 file_size
entry (20 B): u32 id | u32 size | u32 pad | u64 offset     (offsets tile the file exactly)
```

The index id is **FNV-1 of the bank name**, not the Wwise media id — which is why the card's
media-id lookup could not see it. Re-running its own hash over the 10 banks that own the 24
errors:

```
bank                                                     wad        entrysz
DLG_CHAR_BATMAN_MISC_COBRA_BARRAGE                       INT_2.wad  49152      RIFF/WAVE
DLG_MAIN_CH10_S05_JOKER_A1_WAREHOUSE_TWO_FACE_GORDON_OUTRO INT_8.wad
DLG_MAIN_CH10_S08_GOTHAM_ALF_PLEAD                       INT_8.wad  1728512    RIFF/WAVE
BML_Engine                                               -          NO ENTRY
VEH_Batmobile_MK2_Engine                                 -          NO ENTRY

(control) dialogue bank keys found: 16 of 16
engine-bank candidates tested: 15 | hits: 0
```

Every one of the 16 voice error rows has a `WWAD` entry under `fnv1(bank_name)` whose bytes start
`52 49 46 46 … 57 41 56 45` (RIFF/WAVE), 40 KB–1.7 MB in size. The two engine banks do not match
by any key I tried (bank, `bank_<name>`, `<name>.bnk`, the event names).

**Result: BROKEN** for the *conclusion* "the bytes are not on disk", which is true only for the
search space that was used. The 16 dialogue lines are on disk and recoverable without touching
the game's own bytes; the claim should read "not found in the banks searched; the streamed bytes
live in `INT_*.wad` under the bank-name hash".

## A7 — "the 24 streamed rows are all voice lines" — BROKEN

**Test.**

```
errors: 24   groups: Counter({'voice': 16, 'engine': 8})
banks: DLG_MAIN_... (6 banks, 16 rows) | BML_Engine 4 | VEH_Batmobile_MK2_Engine 4
engine rows: Play_Batmobile_Positional | Play_Batmobile_Engine_Transition_In/Out,
             Play_Batmobile_MK2_Positional, Play_Batmobile_MK2_Engine_Transition_In/Out,
             Play_Batmobile_Reverse
```

Eight of the 24 are the **positional engine loops** — the single most important audio asset for a
driving mod — and they are the two banks that A6 could not recover.

**Result: BROKEN.** The MODLOG sentence is wrong, and it happens to conceal the more serious of
the two gaps.

## A8 — "every one of the 447 media ids is decoded to a 48 kHz WAV" — BROKEN

**Claim** (`AUDIO_FEATURES.md` line 3–4):

> "every one of the 447 media ids is decoded to a 48 kHz WAV under
> `E:\Modding\ArkhamKnight\_grab\audio\wav` (outside the repo) and measured."

**Test.** The same file's Summary table says `decoded 423`, `decode_errors 24`, and the JSON has
24 `decode_errors` entries. The two statements cannot both be true.

**Result: BROKEN** as prose (the table and the JSON are right, the sentence is wrong). WAVs on
disk are 423, not 447.

## A9 — The RTPC layout — HOLDS, with an unstated risk

**Claim.** Entry = `u32 param_id | u8 type(0) | u8 interp | u8 a | u32 curve_id | u8 b | u16
points | points*(f32 x, f32 y, u32 curve_type)`, kept only under five anchors: the preceding u16
equals the parsed entry count; every type byte 0; every point finite, |v| < 1e7, curve_type ≤ 32;
no `param_id` is a HIRC object id; `BML_Steering` resolves to an `AkParameterName`.

**Test.** 261 objects / 506 entries / 41 distinct parameters, and the recovered vocabulary is
coherent for a vehicle rig — `Speed` (56 objects), `REV_RPM` (37), `RainDensity` (34),
`BML_Slide` (14), `Occlusion` (12), `BML_Air`, `BML_WheelSpeed`, `REV_Throttle`, `REV_Gear`,
`BML_Steering*`, `BML_TurretSpeed*`, `Drift`, `EngineHeat`, `Startup`, `Pause`. Curve shapes are
parameter-shaped (`BML_Steering` −1→200, 0→−200, 1→200; `Drift` 0→0, 50000→−1). Two ids account
for the bulk (`Speed` 66 entries, `REV_RPM` 62).

The honest caveat the card does not state: the u16 anchor is a *filter*, not an independent
verification. A run of bank bytes that happens to be preceded by a u16 equal to its parse length
and passes four weak range checks is accepted as an RTPC list, and nothing on disk can distinguish
it from a real one. The evidence that this did not happen is statistical (41 params over 506
entries, all vehicle-plausible), not structural.

**Result: HOLDS** as a description of what was recovered; the 1.8 % hit rate (261 of 14 498 HIRC
objects) and the coherent vocabulary are the support, not the anchors alone.

## A10 — "19 AkParameterName columns" — BROKEN

**Claim** (MODLOG): *"22 of the 41 bound ids resolve (the 19 `AkParameterName` columns plus
`REV_RPM`, `Drift`, `EngineHeat`, … from the package name tables)"*.

**Test.** The record's own `name_source` field:

```
name sources: {'name-table': 15, None: 19, 'AkParameterName': 7}
AkParameterName rows in AUDIO.md: 74
```

So 7 names are decoded from `AkParameterName` objects, 15 come from hashing a bag of candidate
strings (`Working/Audio/conv/*/names.txt`, 4.6k–84.8k lines each, plus `bm_names.txt`), and 19 are
unnamed. `AUDIO.md` has 74 `AkParameterName` rows, not 19, and only 7 of them intersect the bound
ids.

**Result: BROKEN** for the breakdown. The *count* (22) is right. Under R4 the 15 hash-matched
names are `derived`, not `decoded`: the match is strong evidence (≈200k candidates against 41 ids
is a ~0.2 % false-positive risk) but it is a hash search, not a read of a name field.

## A11 — "the BML_Winch parameters ship" — BROKEN as stated

**Test.** Hash the obvious candidates and look for them among the 41 bound parameter ids:

```
BML_Winch          0x4f717830 -> no
BML_WinchSpeed     0x8e2041b9 -> no
BML_WinchLength    0xe23c2844 -> no
Winch              0x2d3d9074 -> no
BML_Winch_Length   0x9d5df76f -> no
```

No winch parameter is bound anywhere in these banks. What ships is five winch **events** (A3).

**Result: BROKEN as stated.** The parenthetical was presumably meant to reassure AUD-7 that the
rig is reachable; it names the wrong thing and, by doing so, hides the events that do exist.

## A12 — Roots, peaks and loudness — HOLDS

**Test 1 — reproduction.** Re-measured four WAVs from disk:

```
0x00011285 dur 2.673/2.673 peak -0.41/-0.41 lufs -13.26/-13.26
0x000E70C2 dur 1.028/1.028 peak -0.00/-0.00 lufs -6.92/-6.92
0x001BD1C9 dur 2.954/2.954 peak -0.31/-0.31 lufs -11.97/-11.97
0x3FD15056 dur 0.751/0.751 peak -9.05/-9.05 lufs -25.38/-25.38
```

**Test 2 — calibration against the standard's own anchor.** A 997 Hz sine at 0 dBFS peak must
read −3.01 LUFS under BS.1770. The card's `integrated_lufs()`:

```
sine amp 1.0 -> -3.01 LUFS
sine amp 0.1 -> -23.01 LUFS
sine amp 0.5 -> -9.03 LUFS
```

The −3.01 result is the BS.1770 reference value, so the K-weighting and the −0.691 offset are
calibrated, not merely self-consistent.

**Test 3 — the 24th "None".** One row has `lufs: null`: `0x35210EF7`, 0.027 s, peak −84.29 dBFS
(`Play_BatWing_VS_Batwing`). Below the −70 LUFS absolute gate, correctly null rather than 0.

**Result: HOLDS.**

## A13 — 423 WAVs, 48 kHz, 971.4 s — HOLDS

```
wav files on disk: 423
JSON media rows whose wav is missing: 0
declared sample rates: Counter({48000: 423})
native rates: [(48000, 423)]
duration total: 971.4
```

All native rates are 48 kHz, so no resampling path is exercised — worth noting because the
`resample_poly` branch is therefore untested, not proven.

**Result: HOLDS.**

## A14 — One feature group per event, by name — WEAK

**Claim.** "every one of the 361 events is in exactly one feature group (or `other`)", first rule
wins.

**Test.** The assignment is a *name* regex, not a behaviour (R5):

```
battle-mode rows: 120 (30 distinct)  — Play_BattleMode_In_A…F, Out_A…H, InRev_*, OutRev_*, Play_BattlemodeEngine
voice        (20): … Play_Joker_Foley_Gun, Play_Joker_Foley_Gun_Up  ← gun foley, not voice
interior      (9): Play_Boot_Close/Open, Play_Chairs_In/Out, Play_CockpitClose/Open, Play_Flaps_Close/Open, Play_Batmobile_Rain_Interior
burnout      (10): … Play_Batmobile_Steering_Bed, Play_Batmobile_CornerSqueal
3 names match more than one rule (battle/engine, lock-on/horn ×2)
rows whose stored group != recomputed: 0
```

Most of it is right and defensible (`Boot/Cockpit/Flaps` really are the interior parts,
`BattleMode_*` really is battle mode, the `MK2` variants sit beside their base names). The
failures are the name coincidences: `Play_Joker_Foley_Gun` is Joker's *gun*, not a voice line;
`Play_BattlemodeEngine` is an engine bank chosen into `battle-mode` by rule order;
`Steering_Bed` is a looped steering sound filed under `burnout`.

**Result: WEAK.** Correct where names are unambiguous, wrong on a handful of name coincidences,
and — because it is name-only — it cannot be challenged in-game per R5 without a listening pass.

## A15 — The loop bit is genuinely unknown — HOLDS

**Claim.** The Wwise loop flag is not pinned; the probe over 8 loop vs 32 one-shot rows found no
separating byte; per-event loop evidence is the `Stop_` counterpart, the name tokens and any
vgmstream loop lines.

**Test.** The stored probe detail:

```
loop_events 8, oneshot_events 32
offset 4: loop {1} vs oneshot {1}   overlap
offset 5: {0} vs {0}                offset 6: {4} vs {4}
offset 7: {0} vs {0}                offset 8: {0} vs {0}
separated_offsets: []
```

Every probed byte has one value on both sides, and the two media-id/per-bank bytes were
deliberately excluded. The claim is a declared gap, not a guess, and `loop.stop_event` /
`loop.name_tokens` are separate labelled derivations.

**Result: HOLDS** as diligence. (It also means no downstream card should assume a loop *except*
where a `Stop_` counterpart or an `Lp`/`Persistent` token exists.)

## A16 — The 90 `missing-bank` rows are explicit — HOLDS, but the empty groups are misleading

**Claim.** "the 90 `missing-bank` rows stay explicit"; groups `sonar`, `tracker`, `lock-on-ui`,
`death`, `impacts`, `afterburner` therefore show 0 WEMs.

**Test.** All 90 rows carry `bank: null` and a named `bank_ref`:

```
Engine.BML_Sonar 18 | Engine.BML_Batmobile_Subjective 16 | Engine.VEH_Tank_Heavy 16
Engine.VFX_Tank_Explosion 14 | Engine.CHR_BatmanDisruptor 7 | Engine.VEH_Tank_Missiles 6
Engine.BML_Impacts 4 | Engine.UI_InGame 4 | Engine.CHR_BatmanAlerts 3 | Engine.OBJ_Rolling_Objects 2
26 distinct events
```

None of the 26 event ids occurs in any of the 41 exported banks or the 14 loose files, and
`objects.jsonl` holds no `AkBank` row under any of those names (only a `Package` stub
`Ww_BML_Batmobile_Subjective`). The local `Engine.upk` (26.5 MB) contains none of the 27 bank
names at all — not even `BML_Batmobile`, which *was* extracted — so it cannot arbitrate whether
the retail game ships these banks.

The problem is presentation, not the flag: the table shows `sonar 18 rows / 0 WEMs`, `afterburner
6 / 0`, `impacts 16 / 0` with no marker that the emptiness is a bank-coverage gap. A reader of
`AUDIO_FEATURES.md` takes away "this car has no sonar, no afterburner, no impact audio", when the
events (`Play_BML_Sonar_*`, `Play_Batmobile_RocketTails`, `Play_Batmobile_HeavyCannon_Explosion`,
`Play_Batmobile_Destroyed`) exist with valid FNV ids and simply have no bank in the grab.

**Result: HOLDS for the rows, WEAK for the table's meaning.**

---

## Cross-cutting notes

* **R11.** Every number in `AUDIO_FEATURES.{json,md}` is generated by one script and reproduces
  (`--check` prints the same summary). The failures above are all *interpretation* claims in prose
  and in one group note, not generated counts.
* **Smallest fixes that would close the real gaps**, in value order:
  1. Add the 8 cross-package event names found in `objects.jsonl` (`Engine.Play_BML_Winch*`,
     `Engine.Play_Batmobile_ApRocket_*`) to the card's inventory, either as rows with
     `status: referenced-only` or by extending `AUDIO_MAP`'s scope. That alone turns `winch` and
     `emp` from empty to populated, and it is the difference between "the donor has no winch
     audio" and "five winch events exist".
  2. Read `English(US)/INT_*.wad` with the `WWAD` index (id = FNV-1 of the bank name) and decode
     the 16 voice rows it holds. That is the same hash the script already trusts.
  3. Say "24 streamed rows remain undecoded: 16 voice (bytes present in the INT wads, keyed by
     bank name) and 8 engine (not found)" instead of "the bytes are not on disk".
  4. Label the 15 hash-matched parameter names `derived` (name table) and the 7
     `AkParameterName` ones `decoded`, per R4.
* **Not decidable here:** whether `Engine.BML_Sonar`, `Engine.BML_Batmobile_Subjective` and the
  other eight banks exist in the retail install (the local `Engine.upk` shows none of the 27 bank
  names, including ones that were extracted), and whether any chain accepted by A9's anchors is a
  false positive. Both need a bank-level export the grab does not carry.
