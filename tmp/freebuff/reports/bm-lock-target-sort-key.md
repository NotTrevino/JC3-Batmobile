# BmAK lock ordering — does the launcher data rank lock candidates?

**Scope:** BmAK only. The JC3 side (T-WP3b) is not re-opened here; it is cited only where it makes a
claim about the BmAK numbers.

**VERDICT: UNKNOWN.** `RBatmobileMissileLauncher` carries **gates and counters, not a comparator**.
No field, array order or stored key in the three archetypes ranks one lock candidate against another
by health, distance, angle or class; the only health-adjacent logic is an alive/dead cull in a script
on the *Joker* subclass. The bytes therefore **neither prove nor refute** "highest health locks first" —
they are silent, because the ranking is not stored. They *partly* support the operator's working
hypothesis (nearest to the crosshair), because aim angle and range exist as **admission gates**, but
the tie-break-by-proximity half has no data member either.

Read-only: no game launched, no archive or install written, `objects.jsonl`, `WEAPONS.md`,
`BMSDK_OFFSETS.json` and `GRAB_BACKLOG.md` untouched.

## 1. What is already claimed

| claim | where | status after this read |
|---|---|---|
| BmAK `MaxTargets` is **8** | `tmp/freebuff/reports/T-WP3b.md:56`; `Working/Translation/T_WP3B_LOCKON.md:212` | **half right**: 8 is the *Joker instance* only (`WEAPONS.md:1081`); the *Joker class-default* is **16** (`WEAPONS.md:1116`). The base launcher sets it nowhere, so its value is not in the dump. |
| nothing in BmAK's weapon data counts targets | same lines | wrong for BmAK: `MaxTargets` 0x95C, `MaxTargetsPerLevel` 0xA20, `CurrentTargets`/`LastTargets` arrays and `NthTarget` all exist (table 2). The claim is about JC3 only, and stays true there. |
| lock angle 40 deg / lock range 12000 UU = 120 m | `T_WP3B_LOCKON.md` §4.1, `WEAPONS.md:1028-1029` | confirmed, `objects.jsonl` tags agree on all three variants. |
| no statement anywhere about lock *ordering* | both reports, full text | confirmed: neither file claims an order, so there is nothing to contradict here. |

## 2. Every key that exists on the launcher, with offset and value

Class `RBatmobileMissileLauncher`, `size` 2648, super `RVehicleWeapon`
(`Research/BatmobileGrab/BMSDK_OFFSETS.json`, class block `RBatmobileMissileLauncher`). Values are the
tags actually serialised on the archetype, identical in all three variants:

* `Playable_BatmobileFunhouse_SF` — `objects.jsonl:5209`
* `Playable_BatmobileMK2_SF` — `objects.jsonl:14150`
* `Playable_Batmobile_SF` — `objects.jsonl:19641`

| member | offset | type | value in the built data | key for ordering? |
|---|---|---|---|---|
| `LockOnAngle` | **0x0980** | float | **40.0** — `objects.jsonl:5209`, `:14150`, `:19641`; `WEAPONS.md:1028` | **Gate, not a key.** A cone the candidate must be inside; nothing compares two candidates' angles. |
| `LockOnRange` | **0x0984** | float | **12000.0** (120 m) — `objects.jsonl:5209`; `WEAPONS.md:1029` | **Gate.** Max acquisition distance. No per-candidate distance is stored, so no distance ordering and no proximity tie-break exist here. |
| `RVehicleWeapon.LethalRange` | **0x0900** | float | **12000.0** — `objects.jsonl:5209` | Gate, same number as `LockOnRange`; damage reach, not a sort. |
| `RVehicleWeapon.WeaponCoolDown` | **0x0830** | float | **20.0** — `objects.jsonl:5209` | Timing. |
| `MaxTargets` | **0x095C** | int | **not set** on any of the three launchers; **8** on `Batmobile_JokerMissile_Launcher` (`WEAPONS.md:1081`), **16** on `Default__RBatmobileMissileLauncherJoker` (`WEAPONS.md:1116`) | **Cap, not a key.** "How many", never "which first". |
| `CurrentTargets` | **0x0960** | Actor[] | not serialised (runtime array) | Holds the acquired list. **Its order is not written by any field** — this is the array whose sequence a runtime probe would have to observe. |
| `LastTargets` | **0x0970** | Actor[] | not serialised | Previous frame's list — evidence of a current/last pair, no comparator. |
| `NthTarget` | **0x0A00** | int | not serialised | Index of the next missile's target; indexes the list, does not order it. |
| `MaxTargetsPerLevel` | **0x0A20** | int[] | array, payload not decoded (`WEAPONS.md:1087`) | Per-upgrade cap. |
| `RVehicleWeapon.AimTarget` | **0x0878** | Actor | not serialised | The single actor currently aimed at — one pointer, no ranking. |
| `TargetSwitchName` / `LastTargetSwitchName` | 0x09BC / 0x09C4 | AkSwitchName | `Ww_Batmobile_Target.Batmobile_Target` / `..._Last` (`objects.jsonl:5209`) | Audio: two states (current / previous). Confirms multi-lock, says nothing about order. |
| `MissileNumberParameter` | 0x09CC | AkParameterName | `Ww_Parameters.BML_NumberOfTargets` (`objects.jsonl:5209`) | Audio count parameter. |

## 3. The four candidate keys, tested

| candidate key | member on the launcher or its super? | offset / value | verdict |
|---|---|---|---|
| **health** | **no.** `RVehicleWeapon` declares 57 properties and `RBatmobileMissileLauncher` 34; none matches `health`/`damage`/`hp`. `Health` (offset 1144) / `HealthMax` (1148) exist on `Actor` (`BMSDK_OFFSETS.json`, `"name"` rows at lines 4959 / 4966) but no launcher member reads them. | — | **absent as a key.** The hypothesis has no data carrier: nothing could store "highest health". The only health-flavoured logic is `RBatmobileMissileLauncherJoker.CheckForDeadThugs` (`objects.jsonl:5628`), a **script** (Joker variant only) whose local is `Thug` (`:5626`) — an alive/dead **cull**, not a ranking, and not present on the base launcher. |
| **distance** | `LockOnRange` 0x0984 | 12000.0 | **gate only.** Sieve at 120 m; no candidate distance is stored, so nothing to compare and no tie-break. |
| **angle to reticle** | `LockOnAngle` 0x0980 | 40.0 | **gate only.** Same shape: a cone test, not an ordering. |
| **class** | none on the launcher. The Joker CDO does carry `RInventoryGadget.TargetClass` = `"BatmobileMissileLauncherJoker"` (`WEAPONS.md:1122`) | — | **absent as a candidate key.** That string names the gadget's own inventory class, not a filter over targets. Class-shaped behaviour exists only as the `CheckForDeadThugs`/`IsHeavyWeaponValid` scripts on the Joker subclass (`objects.jsonl:5607`, `:5628`). |

## 4. If no sort key exists — the search that establishes it

Searches run over the whole decode, not just the launcher:

* `"name": "…(sort|priority|nearest|closest|target)…"` in `Research/BatmobileGrab/BMSDK_OFFSETS.json` —
  **16 hits, none an ordering**: `TranslucencySortPriority`, `DepthPriorityGroup` (×2),
  `bAutoGrapplePointsAreLowPriority`, `ComponentArrayPriority`, `bAgeSorted`, `InvestigationPriorityOverride`,
  `TargetFOV`, `ZipLineTargetOffset`, `TargetScreenLoc`, `TargetActor`, `AlwaysHitTarget`, … All rendering,
  camera or single-pointer members. No `TargetSort*`, no `TargetPriority`, no `NearestTarget`.
* `(besttarget|sorttarget|gettarget|findtarget|validtarget|targetsort|targetpriority|selecttarget)` on member
  names — **0 hits.** `ValidTargets` / `InvalidTargets` do exist, but on **`RBatmobileWinch`**
  (0x0A3C / 0x0A6C), not the launcher.
* `(Health|Damage)` on member names — **0 on the launcher chain**; all hits are on Actor, projectile or the
  cannon's damage curve.
* Launcher function-ish script names — `IsHeavyWeaponValid` (`objects.jsonl:5607`), `GenerateFakeTargets`
  (`:5623`), `CheckForDeadThugs` (`:5628`): validity and fake-target generation, **no ordering routine**.
* Archetype tag sweep: `MaxTargets` 0x95C appears as a tag on **11 records** in `objects.jsonl`
  (cannon bools at 2396, heavy-cannon projectile refs, and the two Joker launcher ints 8/16) — **none on
  `RBatmobileMissileLauncher`**. The base class-default export `Default__RBatmobileMissileLauncher` is
  **absent from the dump** (only the 3 archetypes and the Joker CDO exist), which is why the base
  `MaxTargets` value cannot be quoted.

**File a runtime check would need:** none in this repo settles it. `BMSDK_OFFSETS.json` is a property
table with no function bodies, and the aim manager lives in the engine binary, not the grab. To confirm,
a probe must log the **order of `CurrentTargets` (0x0960) at the moment of acquisition**, across
`MaxTargets` (0x95C, set per-instance) candidates placed at varied health, distance and off-axis angle.
The nearest artefact to start from is `Research/BatmobileGrab/objects.jsonl` record `5209` for the
launcher and the broken-out `RVehicleWeapon.g.cs` offsets, both already complete; the missing piece is
the write side, i.e. `RVehicleWeapon::UpdateAimTarget` in the engine, not in the dump.

## 5. Where the files agree, disagree, say nothing

**Against the operator's working hypothesis** (nearest to the crosshair locks first, proximity breaks ties):

* *Agree, as far as gates go:* `LockOnAngle` **40.0** (0x0980) makes off-crosshair targets inadmissible,
  and `LockOnRange` **12000.0** (0x0984) makes remote targets inadmissible. Both are consistent with
  "the one nearest the crosshair wins" whenever only one target is inside the cone.
* *Say nothing:* nothing ranks two targets both inside the cone. There is no angle array, no distance
  array, no sort weight — the candidate list is a bare `Actor[]` (`CurrentTargets` 0x0960).
* *Therefore, two targets at equal angle:* the data predicts nothing about which is chosen; the tie is
  resolved outside the files.

**Against "highest health locks first":**

* *Say nothing, not disagree:* no health member anywhere on the chain, so the hypothesis is not
  representable in this data. It is not refuted — native code may read `Actor.Health` — but there is
  **zero data support** for it, while the angle/range gates at least have members.
* *Weak contrary signal:* the only per-target logic in the whole launcher family is
  `CheckForDeadThugs` (a dead/alive cull), i.e. a *validity* test, which is the shape you would expect
  in front of an order the engine computes — not a health comparison.

**Method caveat that applies to both:** these are serialised archetype tags only. A comparison done in
native code leaves no trace here, so "absent from the data" is not "absent from the game".

## 6. Limits

Static read of `Research/BatmobileGrab/objects.jsonl`, `Research/BatmobileGrab/WEAPONS.md`,
`Research/BatmobileGrab/BMSDK_OFFSETS.json`, `tmp/freebuff/reports/T-WP3b.md`,
`Working/Translation/T_WP3B_LOCKON.md`. `CurrentTargets`, `LastTargets`, `NthTarget`, `AimTarget` and
`MaxTargets` are runtime-only and are not in any export, so their live values are UNKNOWN. No player-side
observation was performed (the test ban stands); the operator's own note is explicitly marked uncertain
and was used only as the hypothesis under test.
