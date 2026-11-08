# BmAK native/untagged remainder — triage of the 157 non-stub exports

Card `G3-06c`. Tool: `Tools/scripts/bmak_native_triage.py` (`--write` / `--check`).
Output: `Research/BatmobileGrab/NATIVE_TRIAGE.md` + `.json`; the 157-row ranking is §2 there and
the byte reads are §3. This note is the short form.

Card ids: `G3-06b` was already `CLASS_DEFAULTS.md`, so this pass is **`G3-06c`** and its five
sub-cards are `G3-06d`…`G3-06h`, inserted into `GRAB_BACKLOG.md` §12 after the `G3-06` family.

## 1. The 925, split by shape (not opinion)

`REMAINDER.json` (G3-06) already walked all 925 untagged exports of the BmAK grab:

| shape | exports | what the bytes show |
|---|---:|---|
| `empty_stub` | 768 | 2-byte `Package` payload — no properties exist to decode |
| `native_record` | 152 | a payload no property-tag stream explains |
| `closes_from_offset` | 5 | a tag stream that closes, but only from an offset |

**157 non-stub remainder** = 152 + 5. Reachability from `REMAINDER.json`'s own walk: **6**
reachable from the drivable car's chain, **3** undecided, **148** in a package that walk never
visits.

Packages of the 157: `Playable_BatmobileJoker_SF` 132, `Playable_Batmobile_SF` 9,
`Playable_BatmobileFunhouse_SF` 8, `Playable_BatmobileMK2_SF` 8.
Classes: 81 class-default property descriptors, 22 script code (`Function`/`State`), 15
`RInteractionComponent`, 13 `FaceFXAnimSet`, 6 parts/light/particle components, 5 audio
components, 4 `RVisualDamageComponent`, 4 weapon-adjacent, 2 physics/threat components, 5 other.

## 2. Ranking rule (stated, therefore re-derivable)

`score = 100 × feature weight + reachability + package bonus + size/200 (cap 20)`

- feature weights: weapons 5, handling 5, damage 4, audio 4, HUD 3, interactions 2,
  parts/animation 2, descriptor 0, facial animation 0, other 1;
- reachability: +200 reachable from the drivable chain, +20 undecided, else 0;
- package: +60 for `Playable_Batmobile_SF` (the drivable car); the MK2/Joker/Funhouse copies are
  separate assets (APP-8) and score nothing;
- `Function` and `State` are BmScript code, never data, so they weigh 1 whatever their owner is
  named — this removed the false “weapons” rank that the Joker launcher's script functions took in
  the first pass, where all fifteen leaders came from one optional skin package.

The ranking lives in the tool, not in this note: `--check` re-derives the order.

## 3. The top fifteen, read with `upk_read.py`

| rank | export | class | size | verdict |
|---:|---|---|---:|---|
| 1 | `Playable_Batmobile_SF` #157 `Vehicle.Batmobile.VehicleSound` | `AkVehicleSound` | 6 B | **derived** — empty component stub |
| 2 | `Playable_Batmobile_SF` #5283 `Vehicle.Batmobile.VisDmgComp` | `RVisualDamageComponent` | 6 B | **derived** — empty component stub |
| 3 | `Playable_BatmobileJoker_SF` #72 `BmScript.RBatmobileMissileLauncherJoker` | unresolved | 212 B | **UNKNOWN** — no tag stream |
| 4 | `Playable_BatmobileJoker_SF` #74 `BmScript.RJokerMissileTarget` | unresolved | 128 B | **UNKNOWN** |
| 5 | `Playable_BatmobileJoker_SF` #117 `…NewHydraPFX1` | `ParticleSystemComponent` | 62 B | **UNKNOWN** |
| 6 | `Playable_BatmobileJoker_SF` #120 `…GadgetMesh` | `SkeletalMeshComponent` | 58 B | **UNKNOWN** |
| 7 | `Playable_BatmobileJoker_SF` #502 `…CollisionCylinder` | `CylinderComponent` | 46 B | **UNKNOWN** |
| 8 | `Playable_BatmobileJoker_SF` #3182 `…ThreatComp` | `RVehicleThreatComponent` | 14 B | **UNKNOWN** |
| 9 | `Playable_Batmobile_SF` #5021 `Vehicle.Batmobile.XrayLightComponent` | `PointLightComponent` | 6 B | **derived** — empty component stub |
| 10 | `Playable_Batmobile_SF` #5125 `Vehicle.Batmobile.Interactions` | `RInteractionComponent` | 6 B | **derived** |
| 11 | `Playable_Batmobile_SF` #5126 `Vehicle.Batmobile.ZapperInt` | `RInteractionComponent` | 6 B | **derived** |
| 12 | `Playable_BatmobileJoker_SF` #139 `…DialogueComponent` | `AkDialogueComponent` | 14 B | **UNKNOWN** |
| 13 | `Playable_BatmobileFunhouse_SF` #155 `Vehicle.BatmobileFunhouse.VehicleSound` | `AkVehicleSound` | 6 B | **derived** |
| 14 | `Playable_BatmobileFunhouse_SF` #5369 `…VisDmgComp` | `RVisualDamageComponent` | 6 B | **derived** |
| 15 | `Playable_BatmobileJoker_SF` #274 `Vehicle.JokersBatmobile.VehicleSound` | `AkVehicleSound` | 6 B | **derived** |

Totals over the fifteen: **8 derived, 7 UNKNOWN, 0 decoded** — no export of the remainder has a
property stream that closes over its own payload.

- The eight **derived** rows are 6-byte component exports: a 2-byte tag terminator plus a 4-byte
  tail. A component's values live on its archetype/CDO, not in the export (G3-06 §C's 30/34 B
  descriptor oracle); the members are named in `BMSDK_OFFSETS.json`, and the *value* would need
  the runtime (G3-07b). `Vehicle.Batmobile.VisDmgComp` and `Vehicle.Batmobile.VehicleSound` are
  therefore names for components the damage (T-DM/ARM) and audio rows already describe — not new
  numbers.
- The seven **UNKNOWN** rows are the Joker package's `BmScript.Default__*` component objects plus
  two unresolved class exports (`RJokerMissileTarget`, `RBatmobileMissileLauncherJoker`); their
  payloads are not property streams (the walk ends at byte 0). They settle with
  `Tools/scripts/grab_packages_g305.py` (PartialPackage) for the export layout and the BmScript
  dump in `NATIVE.md` §A; G3-07b is only needed if a value is wanted.

None of the fifteen changes a ledger value: the reachable six name components the rows already
account for, and the Joker package's script is code for an optional skin (APP-8).

## 4. The G1 percentage question — answered

| bucket | exports | why it does not move the Batmobile |
|---|---:|---|
| 2-byte `Package` stubs | 768 | nothing to decode |
| class-default descriptors | 81 | a descriptor names a default; the value is not on disk |
| another package's asset | 148 | the drivable car's walk never reaches it |
| script code / unresolved | 22 | BmScript bytecode, not a vehicle factor |
| vehicle-relevant remainder | 15 | named cards `G3-06d`…`G3-06h` in `GRAB_BACKLOG.md` §12 |

G1's 19,203 / 20,128 does **not** move: 768 of the 925 have no payload, 81 are descriptors, 148
belong to other assets, 22 are code, and the last 15 name components whose values live on
archetypes the project already decoded. The evidence is this table plus `NATIVE_TRIAGE.md`
§2/§3, re-derivable with `--check`.

Residual UNKNOWN, stated rather than smoothed: the 7 Joker-package payloads above. They are
`G3-06g`'s subject and the only part of this pass a future decode can still add to.

## 5. Checks run

- `python Tools/scripts/bmak_native_triage.py --write` — wrote `NATIVE_TRIAGE.md` / `.json`
  (925 = 768 + 157; 152 native + 5 closes; 15 read; 8 derived / 7 UNKNOWN).
- `python Tools/scripts/bmak_native_triage.py --check` — `check ok`: page and record re-derived
  and compared byte for byte, the count identities asserted, and every top-fifteen row required
  to have a verdict and a settling tool.
- `GRAB_BACKLOG.md` §12 — `G3-06c` (done) and `G3-06d`…`G3-06h` (todo) inserted after the
  `G3-06`/`G3-06b` rows.
