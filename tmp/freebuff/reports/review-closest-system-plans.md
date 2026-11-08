STATUS: done. Read-only review: the six plans were not edited. Findings are labelled
**decoded / derived / switch / UNKNOWN** and each carries the file that would settle it.

# Adversarial review — the closest-system plans (2026-11-06)

Scope: `air-control-closest-system-plan.md`, `ram-assist-closest-system-plan.md`,
`paint-gaps-closest-system-plan.md`, `lock-hold-salvo-closest-system-plan.md`,
`reticle-opt-in-build-plan.md`, `app-dropped-classes-plans-a.md`. Method: read each plan, then check
its load-bearing claims against `Working/Translation/T_ROWS.jsonl`, `Research/challenge/card-T-10.md`,
`Tools/scripts/factors.py`, `tmp/freebuff/reports/lock-hold-and-salvo-carrier.json`, and
`QA1_RESULTS.md`/`T_PLAN.md` where a plan cites a measurement. No game launch, no build, no install.

**Verdict:** the plans are unusually disciplined about *listing* unknowns — every one has an UNKNOWN
table with a settler. The weakness is in the labels on the **carry** steps: four plans call a
cross-engine numeric match "decoded", and three call a normalised or clamped value "exact". One
finding is serious enough to change a build decision (§2.1): the ledger row the ram plan is built on
is `blocked`, not `out`, and its own text names the members the plan claims are the mechanism.

## 0. Findings by severity

| sev | plan | finding | correct label |
|---|---|---|---|
| **HIGH** | ram | "T-RA1's road-assist torque and angle are already carried, exactly" — but `T_ROWS.jsonl:103` records T-RA1 as **`blocked`**: "no road-assist/dodge/shove/kill-flip member … every nearest JC3 member is continuous and target-less: `drift.max_drift_torque` 0x48 …" — i.e. the ledger explicitly rejects the drift torque as the road-assist carrier | **derived** at best (numeric equality), **UNKNOWN** as mechanism |
| **HIGH** | ram | the plan's rate is **2000/s**; the ledger's T-DM7 decision is **100000/s** "declared switch (3.4× BmAK's 150-speed damage)" (`T_ROWS.jsonl:95`). Two build values for one row, and the plan never mentions the ledger's | divergence, must be reconciled |
| **HIGH** | air, ram | both open with "Both are `out` in `T_ROWS.jsonl`" — today only T-RA1 is off `out` in the other direction; T-AC1 `next` (`:102`), T-SR1 `next` (`:104`), T-DM7 `next` (`:95`), T-RA1 `blocked` (`:103`) | stale citation |
| **MED** | paint | "exact" for reflectivity channels 2/3 rests on the `F0_d = 0.04` convention the same report labels ASSUMED | derived under an assumed constant |
| **MED** | paint | edge mask called "exact per value" while `EdgeMask_Metalicity` 2.0 is clamped to 1.0 in the same table | closest / clamped |
| **MED** | air | `turn/pitch_steering_factor` 0.2286 is written as a build value while all 77 shipped rows are 0 — non-zero behaviour is unverified | UNKNOWN acceptance |
| **MED** | lock | the 40° cone is used as the range gate while the same plan's D10/U6 says the AutoAim angle unit is UNKNOWN | internal contradiction |
| **MED** | reticle | "Everything is drawn; nothing is left as 'JC3 cannot'" while U2/U6/U7 gate the marker path | plan, not closure |
| **LOW** | reticle | "2.0 s = 60 ticks at 30 fps / 0.033 s" — 60 × 0.033 = 1.98 s | arithmetic slip |
| **LOW** | reticle | `hud_i46.dds` 1,044,608 B at 1024×1020 is ~1 B/px, not BC1's 0.5 B/px | unresolved unit |
| **LOW** | air | "read heading from the minimap arrow (the project's heading readout)" — 0 hits in `QA1_RESULTS.md`/`T_PLAN.md`; `qa1_hud.py` reads speed only | UNKNOWN instrument |
| **LOW** | app | D2's "exact route `GeneralMkIII Reflectivity_1`" is blocked until the block has a serialiser (the paint plan calls this REFL-WRITE-1) | blocked route |

## 1. Air control

| # | claim (quoted) | label given | problem | correct label | settles |
|---|---|---|---|---|---|
| A1 | "D1 **8000** … decoded value, 1:1" | decoded | 8000 is decoded on the BmAK side; the equivalence "both are the maximum yaw torque of their system" is an argument, not a read. The JC3 member is a **ground drift-state** torque | **derived carry** (value decoded, pairing assumed) | `JustCause3.exe` Drift consumer; Q-AC-1 |
| A2 | `turn/pitch_steering_factor` = **0.2286** | derived normaliser | labelled honestly, then treated as a build number. All 77 shipped rows are `0..0` — no shipped evidence the consumer honours a non-zero factor | **UNKNOWN acceptance** (write, then observe) | `Research/JC3Grab/VOCABULARY.md` ranges (0..0, n=77); `JustCause3.exe` Aerodynamics consumer |
| A3 | "copy the car's shipped `LandAerodynamics` constants" into an `AerodynamicSurface` | decoded | four members (`air_density`, `frontal_area`, `drag_coefficient`, `lift_coefficient`) are copied **by name across two different types**; same-name ≠ same semantics | **derived / name-mapped** | `jc3adf.py info` on both types; the exe's surface consumer |
| A4 | "8000 is an engine torque **gain** … a per-frame authority" | asserted | a purpose-column reading from `MODES.md`, not a decoded unit; the report then uses it to reject the 6600.7 impulse-budget reading | **derived assumption** | `MODES.md` purpose cell (documentation, not a unit); the exe's use of the 8000 constant |
| A5 | "T-SR1's leg is a value problem, not a carrier problem" | derived | 0 cars ship `DriverLean` (`card-T-10.md` A4 = 18 bikes + 5 boats, 0 aircraft) — carrier acceptance by a `CCar` is precisely the open question, and the ledger says so | **UNKNOWN (carrier)** | module-type lookup in `JustCause3.exe`; Q-AC-2 load probe |
| A6 | landing "roll ≤ 30° / pitch ±15°" | design tolerance (honest) | used as a pass/fail gate in Q-AC-1, so a design number decides a decoded row | **authored**, keep, but mark the row's verdict "partial" if only this fails | `STAGES.md` (a design tolerance is not a decode) |
| A7 | "read heading from the minimap arrow (the project's heading readout)" | stated as project fact | no such instrument is recorded: `grep -i "minimap arrow\|heading"` over `QA1_RESULTS.md` and `T_PLAN.md` → 0 hits; the only instrument (`qa1_hud.py`) reads speed | **UNKNOWN** | a heading instrument that does not exist yet; the minimap decode is not in `Research/JC3Grab/` |
| A8 | "Both are `out` in `T_ROWS.jsonl`" | citation | both are `next` today (`:102`, `:104`) | stale | `Working/Translation/T_ROWS.jsonl:102,104` |
| A9 | "pitch fades as the car slows in the air, which is a **compromise** against BmAK" | compromise | the aero law is speed²; BmAK is constant authority. Calling it a compromise hides that the gap is unclosed | **gap** | no JC3 constant-authority member exists (`VOCABULARY.md` 0 `air_control` rows); the exe's air-control path |

Good as written: the drift-state airborne survival is U1 with Q-AC-1 named; `CForcePulse` is rejected
on decoded evidence (`FORCEPULSE.md`, 0/23 collision triggers); `DriverLean` is not used for steering.

## 2. Ram assist and road assist

### 2.1 The road-assist claim contradicts the ledger (highest-severity finding)

The plan's §5.1 table says three values are "**exact match, decoded**":

| BmAK | value | mapped to | plan's verdict |
|---|---:|---|---|
| `ImpactRoadAssistMaxTorque` (class default) | 15000 | `drift.counter_steer_torque_brake` | exact match, decoded |
| `ImpactRoadAssistMaxTorque` (archetype) | 30000 | `drift.counter_steer_torque_handbrake` | exact match, decoded |
| `ImpactRoadAssistMaxAngle` | 45 | `drift.max_drift_angle_deg` | exact match, decoded |

Against it, `T_ROWS.jsonl:103` (T-RA1, `blocked`) says: "**none at any layer** — no
road-assist/dodge/shove/kill-flip member in the 52-type / 1,421-path vocabulary … Every nearest JC3
member is continuous and target-less: `drift.max_drift_torque` 0x48, `arcade.nitro_boost.push_force`,
`arcade.turbo_jump.*` …".

So the ledger has already ruled that the drift block is *not* the road-assist mechanism, and the plan
reverses that ruling on the strength of three equal numbers. Numeric equality across two engines is
the weakest possible evidence of mechanism identity — 15000/30000/45 being also the class default and
the archetype of one BmAK member strengthens the coincidence reading, not the identity one.

* Correct label: **derived (value coincidence); UNKNOWN (mechanism)**.
* Settles: the Drift consumer in `JustCause3.exe` (does counter-steer torque fire after a wall
  deflection, or only inside the drift state?) and Q-RA-1's "with and without drift entry" variant —
  which the plan already writes, so the experiment exists; the label is what is wrong.
* Consequence for the build: road assist cannot be listed as "no write / already carried". It is a
  mechanism probe, and `T_ROWS.jsonl:103`'s `blocked` should stay until the probe runs.

### 2.2 Further findings

| # | claim | label given | problem | correct label | settles |
|---|---|---|---|---|---|
| R1 | "**Proven (decoded):** the module is in the module set of all 232 vehicles … So on a car the block is loaded" | decoded | correct as **loaded**; the sentence is then read as "the channel exists" in §0's answer | keep decoded, add: loaded ≠ evaluated | `T_ROWS.jsonl:95` already says "UNKNOWN (evaluated on a `CCar`)" |
| R2 | rate **2000/s** | derived | built on "contact time at 80 km/h = 1.1 m / 22.222" — the 1.1 m engagement length has **no cited source**; and the ledger's own decision is 100000/s as a declared switch | derived from an uncited assumption; **diverges from the ledger** | `T_ROWS.jsonl:95`; a frame count from Q-RAM-1A's video, or the collision extents in `.physicsc` |
| R3 | "use `min_rpm` as the speed gate: `min_rpm` = 1260" | derived | the §0 answer presents the gate as the plan's design while §2.2 shows H2 (rotor RPM) makes it *never fire* on a car; the two-stage probe is right, the headline is not | derived, conditional; **UNKNOWN** which input | Q-RAM-1B; `JustCause3.exe` RotorCollision consumer |
| R4 | 15000 → brake, 30000 → handbrake | decoded | two BmAK values (class default, archetype) assigned to two members by choice, not by any decoded correspondence | **switch / authored pairing** | `Research/BatmobileGrab/DAMAGE_RULES.md` + the Drift consumer |
| R5 | "`rotor_collision` … offsets 0x130/0x134/0x138/0x13C" with values read back | decoded | the strongest decode in either ram/air plan — floats read at absolute offsets with the dump printed | **decoded, correct** | re-runnable `jc3adf.py dump` / `struct.unpack_from` (`§8`, printed) |
| R6 | `PMDodgeForce` 6000 → `nitro_boost.push_force` | decoded value | "force→force" is asserted; the unit is declared UNKNOWN two lines later, and the plan's own arithmetic shows it cannot be a dodge | value decoded, **carry speculative** | `JustCause3.exe` dodge consumer; Q-DG-1 displacement |
| R7 | `BattleDodgeImpulse` 100000 → `turbo_jump.*` "keep" | decoded | "shape fits (impulse + speed + multiplier)" is a shape argument over four unnamed multipliers | derived shape match | the tune's member names via `jc3adf.py info` |
| R8 | "Both are `out` (`T_ROWS.jsonl:95,103`)" | citation | `:95` is `next`, `:103` is `blocked` | stale | `T_ROWS.jsonl:95,103` |

## 3. Paint gaps

| # | claim | label given | problem | correct label | settles |
|---|---|---|---|---|---|
| P1 | reflectivity "**exact** where the channel's albedo may change (channels 2 and 3)" | exact | exact only inside the model `F0 = 0.04(1−m)+albedo·m`, whose `F0_d = 0.04` the same report labels ASSUMED; the shader branch itself is not decoded | **derived under an ASSUMED constant** | `Research/JC3Grab/` DXBC of `carpaintmm` (layout only today) |
| P2 | channel 3 "F0 0.0200, error **0**, +0.02 on a black channel" | exact | "error 0" ignores the diffuse cost stated in the same row, and the 0.02 albedo is clamped into a channel whose base is black | exact in F0, **not** exact in look | A/B frames; `app-per-pixel-reflectivity.md` §9 |
| P3 | "wet family … **look-exact** for a fixed wet state" | look-exact | "look-exact" is a visual judgement with no measurement in the report; every other wet number is derived | **UNKNOWN** until a frame comparison | A/B render under rain, plus `TEST_WETNESS_FACTOR` @104's real value |
| P4 | "`Rain_Constant` 1 → scene factor, **exact by neutrality**" | exact | "1 = neutral" is an assumption about an undecoded scale | **UNKNOWN** | a runtime constant dump of `deferred_clusteredlightingtunable` |
| P5 | edge mask "**exact per value**" | exact | the same table writes `EdgeMask_Metalicity` 2.0 as **1.0 (clamped)** — a clamped value cannot be exact | **closest / clamped**; the 2.0 must be recorded as an out-of-domain input | `Research/BatmobileGrab/COLOUR_PARAMS.md` §2–§3; `carpaintmm` header range |
| P6 | wet F0 0.0128 "is not baked because … would darken the charcoal 2×" | closest | this is an accepted residual, not a closest system; the number never reaches the asset | **declared gap**, residual +0.0272 to the ledger | the same shader decode; a clearcoat lobe measurement |
| P7 | gloss cap "is a project convention, not a format limit" | asserted | **verified**: `Tools/scripts/factors.py:165` reads `GLOSS_CAP = VALUES["paint"]["gloss_cap"]`, a VALUES.json constant, and clamps at `:256` | **decoded (code), correct** | `Tools/scripts/factors.py:165,256`; `Working/Appearance/VALUES.json` |
| P8 | texture budget 3,953.6 + 128 + 512 = 4,593.6 of 4,648 | derived | arithmetic checks out (BC1 512² = 128 KB, 1024² = 512 KB) | **derived, correct** | `MODLOG` §103b cap |
| P9 | "the donor palette itself ships 0.45 on 8 of 10 tints" | decoded | not re-checked here | decoded (cited) | `Working/Palette/serpente_palette.xml` |

## 4. Lock hold and salvo

| # | claim | label given | problem | correct label | settles |
|---|---|---|---|---|---|
| L1 | "`aim_timer_override` @108 … **derived** — `MissileLockOnDuration` 2.0 carried 1:1 into the only root-level timer member" | derived | a repurpose: the member is an *aim* timer whose consumer is U1 in the same report. 1:1 is a value decision, not arithmetic | **switch** (value derived, semantics UNKNOWN) | `JustCause3.exe` WeaponTuning consumer (the 4.0 constant); Q-LOCK-1 |
| L2 | §0: "carry the **hold** on `aim_timer_override` … gated by a 2.0 s `STimerComponent`" | carried | two carriers are shipped because neither is proven; the one-line composition states it as done | conditional; keep, label "two unproven carriers" | U1 + Q-LOCK-1 |
| L3 | "D2 **1.33** → two muzzles fire twice per salvo" | derived | assumes the pattern distributes projectiles round-robin across points; no file says how a 6-point pattern maps 8 projectiles | **UNKNOWN** | `JustCause3.exe` weapon-fire consumer; Q-LOCK-2 (8 markers/8 launches) |
| L4 | "carries **−1 (unlimited)** and lets the 40° cone do the gating, because the cone is the one quantity both sides name in degrees" | reasoned | contradicts D10/U6 in the same report: the AutoAim angle unit (0.15 turns vs radians) is UNKNOWN, so the cone is **not** a decoded 40° | **UNKNOWN**; the justification is void | `T_WP3B_LOCKON.md` §3; a cone-entry probe at a measured angle |
| L5 | "`missile_per_shot` 8 over 6 muzzles is a legal combination … `w123` fires 6 from one muzzle" | decoded precedent | correct decode, and it proves projectiles-per-muzzle is unclamped — but not that *one trigger* fires across a pattern | decoded (precedent), **UNKNOWN (per trigger)** | `lock-hold-and-salvo-carrier.json`; Q-LOCK-2 |
| L6 | markers "authored into a private `ui/hud.gfx` … driven by `UC_SetLockonValue`" | plan | those setter names are **BmAK's** (`HUD.md` §5.1), not JC3's; the JC3 calls are `UC_SetLockonValue`/`UC_SetHealthValue` from the reticle plan — the two reports use overlapping-but-different APIs | cross-check needed | `tmp/freebuff/reports/reticle-opt-in-build-plan.md` §3; the JC3 `hud.gfx` script dump |
| L7 | `missile_turning_speed` 150 from `w609`; "the Fire Leech's own turning speed is UNKNOWN" | decoded donor / UNKNOWN own | correct, and the settler is named | **correct labelling** | `T-WP3b.md`; `t_lock_salvo.py` |

## 5. Reticle opt-in

| # | claim | label given | problem | correct label | settles |
|---|---|---|---|---|---|
| T1 | "**That is the whole data opt-in**: 22 `AutoAimSettings` values, five missile fields, the carrier class and one slot" | presented as closed | four unknowns (U1, U2, U6, U7) gate whether any of it fires; "whole" overstates | **plan** | the same table's U1–U7 |
| T2 | "**Everything is drawn; nothing is left as 'JC3 cannot'**" | closure claim | the marker path depends on a `label` token native code may not pass (U2) and on native POI creation (U7); 0 `CreatePoi(21)` calls means the path is unproven, not solved | **plan with UNKNOWN delivery channel** | a HUD trace of `hud_code/poi.as` + the native caller |
| T3 | "2.0 s = **60 ticks** at 30 fps / **0.033 s**" | derived | 60 × 0.033 = 1.98 s; 60 frames at 30 fps = 2.000 s. The 0.033 is BmAK's `TickDeltaTime` and does not belong in a JC3 frame count | **derived, arithmetic slip** | `HUD_SPEC.json` (frame rate per movie) |
| T4 | "0.25 s square-in (**7.5 frames**)" | derived | half a frame cannot be authored; the split is a choice | **authored** | the edited timeline itself |
| T5 | "largest `hud_i46.dds` **1,044,608 B**, 1024×1020" | decoded | 1024×1020 at ~1 B/px is not BC1 (0.5 B/px = 522 KB); either the atlas is another format or one number is misread | **UNKNOWN unit** | the DDS header (`dwFlags`/`DXT` fourcc) via `upk_read.py`/`ddsc` reader |
| T6 | "six art variants selected by authored `label` tokens (the only per-POI string channel)" | derived | consistent with the `CreatePoi(type, use_progress_bar, is_minor, label)` signature; "the only" is as strong as the script dump | **derived, correct** | `hud_code/poi.as` |
| T7 | "root binding `secondary` (`id:00568A74`) … count unbound weapons = 0" | decoded | a specific slot id for this car; not re-checked here | decoded (cited) | `Research/JC3Grab/WEAPON_WIRING.jsonl` |
| T8 | R-9 "2.0 s hold" moved into the HUD while "fire gating stays engine-side" | plan | honest split; but a HUD-only timer cannot enforce the hold, so the card must not grade the hold from the marker | **plan, correct** | Q-LOCK-1 (missile leaves 1.6–2.4 s) |

## 6. Dropped appearance classes

| # | claim | label given | problem | correct label | settles |
|---|---|---|---|---|---|
| D1 | D2 "closest + gap + action … **exact route** `GeneralMkIII Reflectivity_1`" | route | the exact route needs a serialiser for that block; the paint plan calls this REFL-WRITE-1 and ships without it | **blocked route** | `Tools/` RBM writer; `app-reflectance-f0.md` §1.2 |
| D2 | D1 "two authored block states (chapter A/B)" | closest + action | no runtime chapter switching; the chapter→state map is `[UNKNOWN]` (its own 2.7) | **authored**, correctly disclosed | `BmGame/CookedPCConsole` MIC swaps; `upk_read.py` |
| D3 | D3 "banded `s2` + per-band vectors, **error measured**" | route | the measurement is planned, not performed | route, measurement pending | §4.2 census + `spec_check.py` |
| D4 | "Row counts are `appearance_plan.json .components[rule]` [decoded]" | decoded | plausible and cited | **correct** | `Working/Appearance/appearance_plan.json` |
| D5 | compromises 1–10 | listed | the strongest honesty block in any of the six plans; #1 (`F0_d`), #4 (chapter states), #8 (streak does not travel with the view) are exactly the right disclosures | **correct practice** | — |
| D6 | D5 "consumed, 0 new slots, 0 KB" | derived | depends on the ramp being synthesised (compromise 9) | derived, disclosed | `Research/BatmobileGrab/TEXTURES.md` (0 aniso entries) |

## 7. Wording that accepts a limit instead of closing the gap

Each line below should name the gap and its settler, not a "compromise":

| plan | wording | why it is an acceptance | rewrite as |
|---|---|---|---|
| ram | "the build therefore buys the 20 km/h floor … and **accepts the inverted ramp** as a declared compromise" | a speed→damage law is a real missing member; "compromise" makes it look chosen | "gap: no member converts contact speed (`VOCABULARY.md`, 0 rows); settler = the impact consumer in `JustCause3.exe`" |
| ram | "150 km/h ceiling … **no max-rpm member** … **Gap.**" | correct already — use this as the model | — |
| air | "It fades as the car slows in the air, which is a **compromise** against BmAK" | speed² is an engine law; the gap is constant authority | "gap: no constant-authority member; settler = the aero/air-control consumer" |
| paint | "look-exact for a fixed **wet state**; not switchable at runtime" | "look-exact" without a comparison frame is an acceptance dressed as precision | "authored wet bake; runtime switching UNKNOWN; settler = `TEST_WETNESS_FACTOR` dump + A/B frames" |
| paint | "the wet F0 target is not baked because … would destroy the diffuse" | a residual, not a closest system | "declared residual +0.0272 in F0; ledger value, not a bake error" |
| lock | "carries **−1 (unlimited)** and lets the 40° cone do the gating" | substitutes one unverified quantity for another | "range UNKNOWN (12000 unit unknown); −1 is a switch; settler = cone-entry probe" |
| reticle | "Everything is drawn; nothing is left as 'JC3 cannot'" | the opposite failure: declares closure while the delivery channel is unknown | "all art is authored; the delivery channel (label token, native POI) is UNKNOWN; settlers U2/U7" |
| app | "two authored drop entries, because no runtime script may run" | a build limitation, correctly disclosed — but it is still a limit | keep, and add the settler (`COLOUR.md` §6 open item: the runtime dirt writer) |

## 8. What the plans get right (so the fixes stay narrow)

* Every plan has an UNKNOWN table with a named settler and a pilot card; the ram plan's **two-stage
  probe** (`min_rpm` 0 → 1260) is the correct design for an undecidable gate, and is the model for
  the road-assist question it currently mislabels.
* The ram plan's `rotor_collision` decode is the only claim in six reports backed by printed bytes
  (`struct.unpack_from` at 0x130/0x134/0x138/0x13C) — keep it as the standard for "decoded".
* `F0_d = 0.04` is labelled ASSUMED wherever it is used; `paint` and `app` both list every compromise.
* The paint plan's gloss-cap finding is verifiable in the code (`factors.py:165,256`) and is labelled
  as a project convention rather than a format limit — correct.
* The reticle plan's "authored, not decoded" treatment of the six art variants is the right pattern
  for HUD work, and U3 (free POI ids) is a genuinely useful unknown.

## 9. Not checked

* No number was re-derived from the binaries: the BmAK 8000/2.0/8/40° reads, the JC3 member offsets
  and the `hud.gfx` sizes are taken as reported. Only the items in this file's "settles" column would
  prove them.
* `T-RA1`'s `blocked` verdict is quoted, not adjudicated — this review argues the plan must not
  contradict it, not that the ledger is right.
* No launch, so every "proves the channel" sentence remains conditional, exactly as the plans say.

## 10. Change statement and revert

* **Intended change:** add this one review file; no plan, ledger row, `Tools/` script or build was
  edited.
* **File:** `tmp/freebuff/reports/review-closest-system-plans.md` — the brief names this path.
* **Revert:** delete this file.
