# Cargo bay attach rule — who consumes the bay's enable event?

Row pair: `Working/Translation/T_ROWS.jsonl`:180 (`T-WLD15`) and :182 (`T-WLD17`), read before
anything else together with `tmp/freebuff/reports/winch-and-tether.md` (sections 2, 3, 7). Both
rows state the native attach rule is UNKNOWN; T-WLD17 is `blocked` on data because 0 of 23
helicopters carries a `CVehicleCargoBay`.

## The bay as decoded

12 objects on 12 entities (cargo plane 6, transport boat 4, monorail flatbed 2), exactly 7
members — `_object_id`, `disable`, `enable`, `enabled`, `name`, `name_hash`, `world`
(`Research/JC3Grab/TETHER.md`:66, `TETHER.json`:16). `enabled = 1` on all 12; `enable` and
`disable` are **empty on all 12** (`TETHER.md`:68-69: “the fields are the same on all twelve”).
No capacity, no mass limit, no attach-state member.

## The INDEX.jsonl search, quoted by line

`Research/JC3Grab/INDEX.jsonl` is a **packfile path index**: 81,952 lines of
`path` / `hash` / `archive` / `mount` / `offset` / `size` / `source`. Line 1 is
`accomplishments/accomplishment_template.bin`, hash `04D48C22`, source `gibbed-filelist`.
Its `hash` is the file hash, not an entity `name_hash`, so it cannot be queried by object name.

| query | hits | lines (path, hash) |
|---|---|---|
| `VehicleCargoBay` | 0 | **none** |
| `cargobay` | 1 | L60171 `models/jc_vehicles/02_air/v4603_plane_urga_cargotransport/cargotransport_cargobay_lod1.rbm` (C6F4E9F4) |
| `cargo_bay` | 0 | **none** |
| `enable` | 7 | L13345 `animations/jc_characters/dialogue/archive/eng/mission_mm130_dial_main_flagenabled.ban` (20DDD571); L13349 `animations/jc_characters/dialogue/archive/eng/mission_mm130_dial_main_returnflagenabled.ban` (6816D7C4); L39151 `graphs/military/cent_com_enabler.gdc` (5FD6A848); L39152 `graphs/military/cent_com_enabler.gsc` (C3815E5C); L39413 `graphs/mission/modules/mext_persistent_enabler.gdc` (F14028D0); L39414 `graphs/mission/modules/mext_persistent_enabler.gsc` (381F3BC4); … 1 more |
| `dualtether` | 2 | L39088 `graphs/dualtether_test_to_vehicle.gdc` (547AF41F); L39089 `graphs/dualtether_test_to_vehicle.gsc` (7A039EEA) |
| `bay.cargo` | 0 | **none** |

What that means, in order:

1. **`VehicleCargoBay` has no INDEX hit at all.** The object name, and therefore its
   `name_hash`, cannot be traced through INDEX: the only cargo-bay path in 81,952 lines is L60171
   `models/jc_vehicles/02_air/v4603_plane_urga_cargotransport/cargotransport_cargobay_lod1.rbm`
   (hash `C6F4E9F4`, a mesh). A model path is not a consumer.
2. **`enable` has 7 hits, none of them a bay.** They are dialogue-archive paths (L13345, L13349)
   and graph files about something else (`graphs/military/cent_com_enabler.gdc/.gsc`, L39151-52).
   No path names a bay enable consumer.
3. **`dualtether` has the graph pair** `graphs/dualtether_test_to_vehicle.gdc/.gsc` — the only
   vehicle-tether script in the index, and unread (`winch-and-tether.md` §6) → UNKNOWN.
4. The bay's numeric `name_hash` value is **not decoded anywhere in the corpus**:
   `TETHER.json` records the member *name* only. So there is no value to search even in an index
   that could hold one — that is a second, independent reason the search returns nothing.

## Consumers that do exist in the data

The bay is referenced only by objects that decorate or point at it, never by an enable handler:

* `CInteractionGraphPointNode · point.bay.cargo.hold / doors` — 6 each, only on the planes.
* `CInteractionGraphEntry · entry.reel.to.stunt.bay.cargo.hold / doors` — 6 each
  (`TETHER.json`:21-22). These are interaction-graph entries (`CInteractionGraphEntry` is 5,535
  fleet-wide, `ENTITIES.md`:13) used for the reel-to-stunt prompt/state; they carry no mass,
  class or attach-state member and do not call `enable`.
* `CPartProp · cargotransport_cargobay` (6), `SAttachedEffect · DoorOpening/ClosingStart/EndCargoBay`
  (10 each), `CSoundLayerEmitter · SoundLayer_CargoBay` (6), `CSpeaker · Speaker_inside_cargobay*`
  (6), `CNamedPoint · respawn_point_for_rico_in_cargobay` (1) — mesh, door VFX, audio, spawn point.

The only decoded proof that a vehicle rides in another vehicle is the compound entity
`v4603_plane_urga_cargotransport_military_cargo_tank` (`CAirPlane` ×1 + `CCar` ×1, bodies
25,000 + 40,000, `TETHER.md` §2). It is a **separate entity bundle**, not a bay event: nothing in
it carries a mass threshold, a class filter or an attach flag either.

## Does the consumer check mass, class or attach state?

**UNKNOWN — no consumer is present in the data.** Three concrete findings bound the answer:

1. All 12 shipped bays ship `enable`/`disable` empty, so no event name exists to hook; no entity,
   graph or script in the grab names one (the INDEX searches above).
2. No member that could express a gate exists on the bay — the 7 members are identity, transform,
   on/off and the empty event pair. There is no `max_mass`, no allowed-class list, no `attached`.
3. The only numeric gate near this system is elsewhere: `grapple_pull_armor` (-1..0) and
   `grapple_pull_armor_strength` (0..100) on 233 entities — damage gates for Rico's grapple, not
   bay attach (`winch-and-tether.md` §3.3).

So the attach rule (if any) is engine code consuming an event that data never names. It cannot be
shown to check mass, class or attach state from these files, and it cannot be shown not to.

## What a helicopter would need wired to reach the same attach

1. **A bay object on the helicopter entity**: a clone of `CVehicleCargoBay` with the same 7
   members, `world` placed at a hold point, `enabled = 1`, `enable`/`disable` left empty to match
   the fleet (`Research/specs/B-16.md` §1 row 1, §2 step 4).
2. **A consumer for that event** — the missing piece. Either the native class already listens for
   it on any entity (probe required), or the build must implement attach/release itself, in which
   case the helicopter route stops being a data clone and becomes a code feature (B-16 §2 step 3).
3. **Carry physics**: the bay has no mass or force member, so the holder's own `RigidBody` and the
   attach constraint would have to carry a 6,000 kg car. BmAK's winch feat bound is ≥ ~2 t, i.e.
   below the car (`winch-and-tether.md` §5), so no shipped number lifts it.

## Verdict

**UNKNOWN, and the gap is real data absence, not a missed search.** No INDEX.jsonl hit ties the
bay's `name_hash` or `enable` member to any consumer (0 hits for the object name; the one cargo-bay
path is a `.rbm` mesh, L60171); the event lists are empty on all 12 bays; and the corpus does not
decode the bay's hash value at all. A helicopter therefore needs a bay clone **plus** a consumer
that the data does not define.

**File that would settle it:** the native side, not another table. Within this project the
remaining lead is the unread graph pair `graphs/dualtether_test_to_vehicle.gdc/.gsc` (INDEX.jsonl,
`dualtether` hits) — if any shipped script fires a bay event, it is there. If it does not, only a
runtime probe settles it: clone the bay onto a helicopter and drive a car at the hold point
(`Research/specs/B-16.md` §2 step 4, gate BX), which is the probe T-WLD17 already prescribes.

## Sources (paths and lines)

* `Working/Translation/T_ROWS.jsonl`:180 (T-WLD15), :182 (T-WLD17) — the blocked rows.
* `Research/JC3Grab/TETHER.md`:66 (7 members), :68-69 (same on all twelve), §2 (carriers, compound
  cargo-tank entity, 0 helicopter bays), §6 (unread graph pair).
* `Research/JC3Grab/TETHER.json`:16 (`bay_members` incl. `name_hash`), :21-22 (bay graph entries).
* `Research/JC3Grab/INDEX.jsonl` — 81,952 lines; L1 (schema), L60171 (only cargo-bay path);
  `VehicleCargoBay` 0 hits; `enable` 7 unrelated hits (L13345, L13349, L39151-52, …).
* `Research/JC3Grab/ENTITIES.md`:13 (`CInteractionGraphEntry` 5,535), :92 (`CVehicleCargoBay` 12).
* `Research/specs/B-16.md` §1-§2 — bay clone and the probe that would settle the attach rule.
* `tmp/freebuff/reports/winch-and-tether.md` §2-§3, §5-§7 — the prior decode this task extends.
