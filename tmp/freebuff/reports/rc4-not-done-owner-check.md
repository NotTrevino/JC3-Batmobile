# RC4 not_done → RC5 owner check, and the blocked ledger rows

**STATUS: done (report only).** No queue file, ledger row, receipt or build tree was created or
edited. Every claim below is a mapping of an existing record to an existing brief, or a proposal where
none exists.

**Provenance / reversibility.** New file, `tmp/freebuff/reports/rc4-not-done-owner-check.md`
= `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc4-not-done-owner-check.md`. It is the output path the
brief names. **Revert = delete this file.**

## 0. Counts, and one correction to the brief's premise

| what | count | source |
|---|---:|---|
| `Builds/bm-RC4/receipt.json` → `not_done` | **6** lines (one of them carries four sub-cards) | `python -c` read of the receipt, §1 |
| queue briefs inside the two windows (9100-9199, 7940-7989) | **64** | `ls tmp/freebuff/queue` (§2 of the run log) |
| `T_ROWS.jsonl` rows with `dispo == blocked` | **27** | `t_rows.py check` prints `blocked 27` |
| T6 (HUD/camera) blocked rows | **4** | `Working/Translation/T6_HUD_CAMERA.md` + `STATUS.md` §"Translation rows by document" (`T6 HUD/camera | 37 | … | 4`) |
| **blocked translation rows in total** | **31** | 27 + 4; this is `STATUS.md`'s `rows blocked 31 / 260` |

**The brief says 15; the files say 31 (27 ledger + 4 T6).** I could not reproduce 15 from any counter:
`t_rows.py check` prints `blocked 27`, and `STATUS.md` prints `31 / 260`. The nearest 15-shaped figure
in the repo is the build-batch gate's `4 blocked` (`t23_closeout.py`: `75 codes (58 carried, 3 named
omission, 4 blocked, 10 documented)`) and the `T-15` document alone (`6`), neither of which is 15. So
this report covers **all 31**, which contains any 15-row subset. If the operator meant a specific 15,
the list below is the superset to pick it from.

---

## 1. What was read (read-only)

```
Builds/bm-RC4/receipt.json            # not_done, 6 lines, schema 2, tag RC4
tmp/freebuff/queue/                   # all 64 briefs in the two named windows
Working/Translation/T_ROWS.jsonl      # 244 rows; dispo blocked = 27
Working/Translation/T6_HUD_CAMERA.md  # 4 blocked rows (T-HUD5, T-HUD11, T-CAM8, T-CAM9, T-CAM11 named; see §4)
STATUS.md                             # blocked 31 / 260, per-document table
GRAB_BACKLOG.md                       # card titles B-10, B-12, B-17…B-20, B-24…B-26
python Tools/scripts/t_rows.py check            -> exit 0, "ledger 244 rows | … blocked 27 …"
python Tools/scripts/t23_closeout.py --check    -> exit 0, "gate TX: 75 codes (… 4 blocked …)"
```

Every "owner" below is a **brief that names the row id, or names the receipt item's own card number, or
states the item's subject and claims it in its Done line**. A brief that merely touches the topic is
marked "subject only" and is not counted as an owner.

---

## 2. Table 1 — RC4 `not_done` items that have an owner

| # | receipt `not_done` item (verbatim) | owner brief | the sentence that covers it | verdict |
|---|---|---|---|---|
| 1 | "12 of 23 texture rows are unfaithful (4 chapter masks + 8 missing pixel sets): the tree is NOT complete" | **`9140-rc5-texture-rows.txt`** | "Texture rows still unfaithful in RC4 (Builds/bm-RC4-appearance/texture_ledger.json): four chapter masks, eight missing pixel sets and the Leather ramp's sampler." — Done line: "the unfaithful count falls from 12 of 23 with each remaining row carrying its card and the file that would settle it" | **owned** (closes as "each remaining row carded", not as 0 unfaithful — the Done line allows that) |
| 2 | "B-10 shape set is incomplete: 1 of 3 BmAK boxes carried - chassis box 1 and the weapons-pod box have no hull shape instance: 2 of 3 boxes missing, 0 free hull slots (62 donor bodies over 54 hull objects)" | **`9141-rc5-collision-boxes.txt`** | "RC4 collision carries only one of the three BmAK boxes: the drivable asset Physics.Batmobile_V3_Physics has 2 bodies, 3 boxes and 1 constraint, but the JC3 file has 62 donor bodies over 54 hull objects with no free slot, so the chassis box 1 and the weapons-pod box have no shape instance and the constraint was omitted" — Done line: "three of three boxes present within 5 cm of BmAK and the constraint carried or its exact missing capability written" | **owned** |
| 3 | "B-12/D-2 modes: this RC is the pursuit set only. The pursuit/battle pair is built as a separate, unmerged payload in Builds/bm-RC4-modes (aafdiff = the 2 planned files); 0 rows are carried exactly, 2 are composed (T-MD5, T-MD6), 2 ride the same unbuilt switch (T-MD10, T-MD11) and 4 are not built (T-MD7, T-MD13, T-MD8, T-MD14)" | **`9130-rc5-mode-pair-and-swap.txt`** | "RC4 ships the pursuit set only; Builds/bm-RC4-modes/pursuit and /battle exist unmerged, with 0 rows exact, two composed (T-MD5, T-MD6), two on the same switch (T-MD10, T-MD11) and four unbuilt (T-MD7, T-MD13, T-MD8, T-MD14) (reports/correction-8398-unshipped-cards.md)." | **owned** — the paraphrase is verbatim-grade |
| 4a | "B-17..B-20 are declared no-payload in BUILD_BATCHES and ship no payload in this RC" → **B-17** | **`9102-rc5-effect-writer-payloads.txt`** | "B-17 has shipped no payload in RC4 although the writer proof exists (reports/effc-format-writable.md; python Tools/scripts/effc_writer.py check carries 95 of 95 files byte-identical)." | **owned** |
| 4b | … → **B-18** | **`9107-rc5-emp-burst-and-disable.txt`** | "Rank three: the EMP burst (RBatmobileEMP: cooldown 2.0 s, four stages growing to 250, 30, 30 cm …)" + "The disable half must be composed, not left out" | **owned** |
| 4c | … → **B-19** | **`9108-rc5-hacker-and-sam-hack.txt`** | "Rank four: the hacker. Operator facts: a hacked SAM turret stops firing at the player and fires at enemies, aircraft only" | **owned** |
| 4d | … → **B-20** | **`9109-rc5-sonar-pulse.txt`** (the full pulse) **and `9102`** (a plan note only) | 9109: "Rank five: sonar, the lowest-ranked weapon. … Build in Builds/bm-RC5-sonar: a damage-free pulse copied from gen_explosion_5m_nodamage, the authored ring effect through the effect writer, the six audio events bound to the pulse, and the reveal markers." 9102: "and the sonar ring only as a plan note since it needs a new effect" | **owned by 9109**; 9102 is explicitly partial |
| 5a | "B-25 and B-26 are cards only; neither has a payload in this RC" → **B-25** | **`9142-rc5-lights-flares-beams.txt`** | "RC4's 24-row lamp module writes range 60 and angle 70 (outside the shipped maximum of 50 and 50) … the 17 lens-flare entries have no payload; T-L28 and T-L30 are blocked with a null socket and bone … and the B-25 card of GRAB_BACKLOG.md lines 1587 to 1607" | **owned** |
| 5b | … → **B-26** | **`9150-rc5-audio-override-and-layers.txt`** | "Build the B-26 route of GRAB_BACKLOG.md: a private effects-class bank and a per-entity SAttachedEffect or SDynamicAttachedEffect binding that leaves the 45 GUIDs unchanged" | **owned** |
| 6 | "runtime load, Rebel Drop resolution and the Q takes are untested" | **none in either window** | 9190/9191/9192 verify the *payload*; 9193 writes the approval request and 9194 refreshes the cards, but no brief in 9100-9199 or 7940-7989 runs a load, a Rebel Drop resolution or a Q take. 9193 only *recommends* the repointing: "Add a short section saying which of the existing Q briefs (8600 to 8605, still gated on the RC4 gate report) must be repointed to the RC5 reports" | **ORPHAN** → §3 |

**B-25 number collision, flagged.** The receipt's `B-25` is `GRAB_BACKLOG.md:1587` — *Lens flares and
the light units* (owner 9142). `Research/specs/B-25.md` is the **lock reticle** (owner 9105). Both are
owned, by different briefs; `tmp/freebuff/queue/7947-record-inconsistencies-diffs.txt` already lists
"the B-15/B-17/B-24/B-25 number collisions with Research/specs/" as a record defect. Do not read one as
the other.

---

## 3. Table 2 — `not_done` gaps (no owner): proposed briefs

No queue file is created. Each row is a brief that does not exist, written so it can be pasted into
`tmp/freebuff/queue/` when the operator wants it.

### G-1 · proposes `9196-rc5-supervised-runtime-session.txt` (the receipt's item 6)

- **Title:** *RC5 supervised runtime session: load, Rebel Drop resolution and the Q takes.*
- **Why no owner:** the only briefs that test anything are 8600-8606, all outside both windows and
  `gated`/`held`; 9193 is forbidden to edit them ("do not edit the Q briefs") and creates no
  replacement, so RC5 would reach an approval request with nobody queued to run it.
- **Inputs:** `reports/rc5-merge-release-candidate.md` (the receipt and `install.ps1`),
  `reports/rc5-verify-files-wiring-audio.md`, `reports/rc5-verify-geometry-predictions-install.md`,
  `reports/rc5-pilot-cards-refresh.md`, `Working/Q/PILOT/LAUNCH.md`, `Working/Q/PILOT/SPAWN_BATMOBILE.md`,
  `Working/Q/PILOT/CONSOLE_RECEIPT.md`, `tmp/freebuff/APPROVED_Q.txt` (operator-written, never by a lane),
  and the held Q briefs 8600/8606 as the shape to repoint.
- **Done check:** one recorded session in which (a) the RC5 drop loads with the console spawn route and
  the entity name/hash is logged, (b) Rebel Drop leaf **1621485476** resolves to the RC5 entity (or the
  failure is named with the log line), (c) every Q take the cards list is either run with its numeric
  band filled or marked UNKNOWN with the reason; `APPROVED_Q.txt` is present and signed before the first
  launch, and no lane writes it.

### G-2 · proposes `9197-rc5-winchet-tether.txt` (T-WP6, blocked row — see §4)

- **Title:** *Vehicle-side winch and tether: anchor, drum, attach/reel/release.*
- **Why no owner:** 9170 owns only the **button** ("the winch is on d-pad right replacing mission
  select"); no brief builds the `CVehicleCargoBay`-style anchor at `WinchOrigin`, the
  `transport_rope_winch` drum, or the pull loop.
- **Inputs:** `Working/Translation/T7_WEAPONS.md` `T-WP6` row and §4 of the same file,
  `Working/Translation/T_WP13B.md` §7, `Research/JC3Grab/TETHER.md`,
  `Research/JC3Grab/TETHER.json` (4 entities, 40 part rows), `Research/specs/B-16.md`,
  `Research/BatmobileGrab/SOCKETS_JC3.md` (`WinchOrigin` 286.554, 0, 59.0 cm),
  `reports/hook-gamepad-scoping.md` (7983) for the input event.
- **Done check:** the anchor object, its 7 members and the drum are written into a private tree and read
  back; the attach/reel/release members are either named with file+offset or written as one exact
  missing-capability card; a pilot sentence with a band for "fire at a pole and hold the 6,000-mass car".

### G-3 · proposes `9198-rc5-helicopter-airlift.txt` (T-WLD17, blocked row — see §4)

- **Title:** *Helicopter airlift of the Batmobile: bay census, native attach rule, or the card.*
- **Why no owner:** the only queue hits for "helicopter" are the radar icon brief (7956) and the HUD
  build (9160); nothing touches airlift.
- **Inputs:** `Working/Translation/T15_WORLD.md` `T-WLD17` row, `Research/JC3Grab/TETHER.md` §1 (the
  12 `CVehicleCargoBay` vehicles and the mass ratios), `Research/JC3Grab/FLEET.md`, the
  `bay_helicopters = []` census, `reports/native-hook-design-jc3mp-contract.md`.
- **Done check:** every one of the 23 helicopters is listed with cargo-bay evidence (today 0 carry
  one); either a route that makes a cloned bay accept the car is named by member, or the exact missing
  native attach rule is written as a card; one probe sentence.

### G-4 · proposes `9195-rc5-camera-springs-and-shake.txt` (T-CAM8, T-CAM9, T-CAM11 — see §4)

- **Title:** *Camera springs, head impulse and boost shake: the three blocked T6 rows.*
- **Why no owner:** no brief in either window mentions a camera analysis (the only "camera" hit is
  9122's *yaw toward aim*, which is steering, not camera).
- **Inputs:** `Working/Translation/T6_HUD_CAMERA.md` rows T-CAM8/9/11, `Research/JC3Grab/` camera-shake
  material (`AddCameraShake`, the `.ctunec`/`CameraShakeModifierParams` family), `Research/BatmobileGrab/`
  camera values (`DrivingHeadImpulseFactor` 0.5, `DrivingCamDriftOrientationFactor` 0.15,
  `DrivingCamSmoothingStrength` 30/12/10000, `BatmobileBoostCameraShake` 35, `WheelSpin` 50×50×25 0.1 s),
  `reports/cameras-per-mode-plan.md`.
- **Done check:** for each of the three rows either a written member with its unit bridge (shown, with
  error) or an exact card naming the missing capability and the file that would settle it; no row left
  as "blocked, no unit bridge".

### G-5 · proposes `9189-rc5-steering-response-curve.txt` (T-CT4 — see §4)

- **Title:** *In-car steering response curve: the capture set T-CT4 waits for.*
- **Why no owner:** 9120 writes the steer time (0.25 s and 0.091 s) but never claims T-CT4; T-CT4's own
  `why` says a rate cannot be written "before the capture set (U6)".
- **Inputs:** the T-CT4 row, `reports/rc5-handling-values.md` (the steer cells), the U6 capture set named
  in `Research/JC3Grab/INPUT.md`/`CONTROLS.md`, `reports/controls-entry-exit-eject-plans-v2.md`.
- **Done check:** the curve is written into the handling tree and read back, or the capture step is
  queued as a pilot card with its numeric band; T-CT4's disposition changes from `blocked` to `next`
  only with that evidence.

---

## 4. Table 3 — the blocked translation rows, with an owner or none

27 ledger rows (`dispo == blocked`) plus the 4 T6 rows. "Owner" = the brief that names the row id, or —
marked *(subject)* — the brief that states the row's own subject and claims it.

| row | doc | why it is blocked (abbreviated from `T_ROWS.jsonl` / T6) | owner brief | basis |
|---|---|---|---|---|
| **T-RA1** | T-3 | no road-assist, dodge, shove or kill-flip member exists at any layer | **`9123-rc5-air-control-and-ram.txt`** | **id**: "The ledger rows this serves are T-AC1 (air control) and T-RA1 (ram assist), both moved to next by the v2 apply pass" |
| **T-RC1** | T-3 | remote control halted: no input carrier, no overlay element, arrival route UNKNOWN | **`9124-rc5-flip-water-remote.txt`** | **subject**, and it *keeps* the halt: "the remote half stays halted with the written reason in the plan, which is a note and not a disposition of out" |
| **T-RC2** | T-3 | the 150 m hard stop and the static overlay are halted by the plan | **`9124`** | **subject** (same sentence) |
| **T-CT1** | T-3 | enter = Y / exit = LB; the pair ships on one button; no keymap writer | **`9170-rc5-controls-entry-exit-eject.txt`** + **`7983`** | **subject**: "Controls inside the Batmobile, built from reports/controls-entry-exit-eject-plans-v2.md" |
| **T-CT2** | T-3 | eject = double press of A; no hold/duration/tap field in any binding row | **`9170`** + **`7949-eject-levels-decoded.txt`** | **subject**: "the three eject levels are runtime logic" |
| **T-CT3** | T-3 | winch = d-pad right, displacing `USE_VEHICLE_MOD` | **`9170`** (button only) | **subject**: "the winch is on d-pad right replacing mission select" |
| **T-CT4** | T-3 | steering axes decoded, but BmAK's response curve needs the capture set (U6) | **none** | 9120 writes a steer time but never claims the row → §3 **G-5** |
| **T-CT5** | T-3 | the keymap writer: 0 of 575 scripts writes a bin | **`9170`** | **subject**: "write the edits into Builds/bm-RC5-controls with Tools/scripts/rc5_controls.py (--write, --check)" |
| **T-MS1** | T-3 | the mode swap waits on U1: no selector member | **`9130-rc5-mode-pair-and-swap.txt`** + **`7984`** | **subject**: "solve that either with the trigger the exe study found or with a composed script route, and say which" |
| **T-TX1** | T-3 | Micropattern_A: 0 of 61 grab `.tga` carry the stem | **`9140-rc5-texture-rows.txt`** | **subject**: "eight missing pixel sets" |
| **T-TX2** | T-3 | Micropattern_A_Normal: same pixels gap, no substitute | **`9140`** | **subject** (same) |
| **T-TX3** | T-3 | Micropattern_B: same pixels gap | **`9140`** | **subject** (same) |
| **T-TX4** | T-3 | Micropattern_C: same pixels gap | **`9140`** | **subject** (same) |
| **T-TX9** | T-3 | Body_Damage_ChapterMask: no chapter selector | **`9140`** | **subject**: "four chapter masks" |
| **T-TX10** | T-3 | Weaponry_Damage_ChapterMask: same gap | **`9140`** | **subject** (same) |
| **T-TX11** | T-3 | WheelArch_Damage_ChapterMask: same gap | **`9140`** | **subject** (same) |
| **T-TX12** | T-3 | Undercarriage_Damage_ChapterMask: same gap | **`9140`** | **subject** (same) |
| **T-L28** | T-14 | null socket/bone; body-hosted `_LIG` + `CarLight` pattern missing | **`9142-rc5-lights-flares-beams.txt`** | **id**: "T-L28 and T-L30 are blocked with a null socket and bone" |
| **T-L30** | T-14 | same as T-L28 | **`9142`** | **id** (same) |
| **T-WP6** | T-7 | the winch entity-graph clone is buildable, but no JC3 data pulls | **none** | 9170 owns the button only → §3 **G-2** |
| **T-WLD17** | T-20 | `bay_helicopters` = `[]`; 0 of 23 helicopters has a bay | **none** | no brief mentions airlift → §3 **G-3** |
| **T-MD5** | T-15 | a hybrid cannot hold a second speed curve | **`9130`** | **id** (receipt-paraphrased: "two composed (T-MD5, T-MD6)") |
| **T-MD6** | T-15 | the cap needs a second value set; no member is a speed cap | **`9130`** | **id** (same) |
| **T-MD7** | T-15 | four of six factors land on the battle entity; two slip scales have no member | **`9130`** | **id**: "four unbuilt (T-MD7, T-MD13, T-MD8, T-MD14)" |
| **T-MD8** | T-15 | the turn on the spot has no data carrier | **`9130`** | **id**: "the turn on the spot T-MD8" — but see the note below |
| **T-MD13** | T-15 | the pose is a per-entity constant; the animation is not | **`9130`** | **id**: "the transformation stance T-MD13" |
| **T-MD14** | T-15 | battle audio needs a second entity and a consumer for the new `Usage` hash | **`9130`** | **id**: "the battle audio switch T-MD14" |
| **T-HUD5** | T6 | the HUD supports the cannon state, but the entity had no weapon component | **`9101`** (component) + **`9110`** (weapons) + **`9160`** (clips) | **subject**; no brief names the row |
| **T-HUD11** | T6 | 2 clips exist, the 3 special-weapon states have no member, the launcher was bound to no slot | **`9110`** + **`9160`** | **subject**; the slot half is D-7's, which `reports/weapons-per-mode-redesign.md` re-proposes |
| **T-CAM8** | T6 | no head-impulse or drift-orientation member | **none** | → §3 **G-4** |
| **T-CAM9** | T6 | no unit bridge from smoothing strength to the JC3 springs | **none** | → §3 **G-4** |
| **T-CAM11** | T6 | no numeric bridge for the boost/wheel-spin shake | **none** | → §3 **G-4** |

**Totals:** 27 rows owned (T-RA1, T-RC1, T-RC2, T-CT1, T-CT2, T-CT3, T-CT5, T-MS1, T-TX1…4, T-TX9…12,
T-L28, T-L30, T-MD5, T-MD6, T-MD7, T-MD8, T-MD13, T-MD14, T-HUD5, T-HUD11) = **27**; owned with no
closure (9124 keeps the halt by design) = **2** (T-RC1, T-RC2); **orphans = 4** (T-CT4, T-WP6,
T-WLD17, T-CAM8/9/11 → the last counted as one subject group, three rows).

### Notes that change how those 27 read

1. **T-MD8 is owned but the brief itself calls it a named omission.** `9130` says "the transformation
   stance T-MD13, the turn on the spot T-MD8"; `T_ROWS.jsonl` says the pivot "stays a named omission in
   both variants and the row waits on a native mechanism". So 9130 must either build it or convert the
   row to `out` with that reason — see the mode-pair report of the weapons redesign for why the
   variant pair exists at all.
2. **`9123`'s premise disagrees with the ledger.** It says T-AC1 and T-RA1 are "both moved to next by
   the v2 apply pass", but `T_ROWS.jsonl` still carries `T-RA1 | blocked`. T-AC1 is not in the blocked
   set at all. The brief owns the row; the record is stale. Fix in the ledger's inputs
   (`Tools/scripts/t_rows.py`), not in the row by hand.
3. **Two review briefs may mutate the owner briefs.** `9119` may "edit them in place" for 9120-9174,
   and `9179` may "edit them in place wherever a tree name, file count or budget they cite is now
   wrong" for 9190-9194. Any ownership claim above is against the briefs as they read on disk today.

---

## 5. UNKNOWNs

| # | what is unknown | what would settle it |
|---|---|---|
| 1 | which 15 rows the brief meant, if not a subset of these 31 | the operator's source list; no counter in the repo prints 15 (`t_rows` 27, `STATUS` 31, gate 4) |
| 2 | whether 9140's "each remaining row carrying its card" is an accepted close for the receipt's "texture rows are unfaithful" | the receipt's own `complete` derivation in 9190: "The receipt's complete flag may be true only if not_done is empty by derivation" — a carded refusal is not empty |
| 3 | whether 9124's halted remote rows can ever leave `blocked` without a new decision | the plan's written halt reason; the row's own `why` says the halt is intentional, so probably `out` is the honest disposition |
| 4 | whether the 4 T6 rows belong to the same 260-row denominator the brief uses | `STATUS.md` counts them inside 260; `T_ROWS.jsonl` does not hold them, so the two sources cannot be added without the T6 doc |

---

## 6. Check run and limits

```
python Tools/scripts/t_rows.py check            -> exit 0
  "ledger 244 rows | edit 16 next 120 keep 30 epe 38 re-read 0 blocked 27 out 6 superseded 7 | edits 35 over 16 rows"
  "check ok"
python Tools/scripts/t23_closeout.py --check    -> exit 0
  "gate TX: 75 codes (58 carried, 3 named omission, 4 blocked, 10 documented, 0 unmapped) | 244 ledger rows | assumed 1 (0 unsigned) | decisions 11/11 answered | 20 artefacts (17 payloads + 3 records) over 24 B steps"
  "siblings: t_rows.py check exit 0 | status_audit.py --check exit 0 | bmak_coverage.py --check exit 0"
ls tmp/freebuff/queue/*.txt | wc -l             -> 70 files (64 inside the two named windows)
```

**Not done:** no `tmp/freebuff/queue/9189/9195/9196/9197/9198` file was created (proposals only, §3); no
`T_ROWS.jsonl`, `STATUS.md`, receipt, brief or build tree was edited; nothing was launched or installed.
**COMPROMISES:** none. Two owned items (T-RC1, T-RC2) stay blocked on purpose, which is recorded here as
a design note rather than a compromise.
