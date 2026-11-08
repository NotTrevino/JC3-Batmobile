# Correction 4/9 - the 21 donor GUIDs (B-26) and the `vehicles#279` loop compromise

Date: 2026-11-07. Build: `Builds/bm-RC4` (banks `vehicles.bank` 210,781,376 B and
`weapons.bank` 177,586,080 B only). Audio tree: `Builds/bm-RC4-audio`.
Decision: **option (b), proof of absence** - no per-entity bank override is decoded, so nothing is
shipped for the 21; and `vehicles#279` is recorded as a named loop compromise in the card's own
domain. **No 3/3 loop claim exists anywhere after this record.**

## 1. The measured split (unchanged)

| bank | GUIDs | resolved in the built bank | carrier in this tree |
|---|---:|---:|---|
| `vehicles` | 24 | 24 | `vehicles.bank` |
| `weapons` | - | - | `weapons.bank` (the weapons' own events, not one of the 45 vehicle pins) |
| `character` | 2 | 0 | **none** - donor bank not built |
| `effects` | 19 | 0 | **none** - donor bank not built |
| **total** | **45** | **24** | **24/45**, 21 donor |

`Builds/bm-RC4-audio/events.json` names each of the 45 rows with `guid`, `bank`, `epe`, `markers`,
`in_fmod_guids`, `event_present`, `tune_present`, `status` and `mapped_slot`; the 21 donor rows carry
`status = "donor bank '<bank>' not built - B-26 (per-entity bank override)"` and
`event_present: null` (a `null` here means "no carrier to look in", not "looked and absent").
`in_fmod_guids` is 45/45 for all rows. The manifest is `Working/Audio/bm_bank_manifest_rc4.json`.

## 2. The 21 GUIDs, with the bank each one lives in

| # | GUID | bank | `.epe` role | mapped slot |
|---:|---|---|---|---|
| 1 | `d87e18de-2eb5-d243-a398-7fb69ccf6638` | character | `dynamic_burn_roof` | none |
| 2 | `d8a4e0fb-2270-9a45-9b07-998820fbb487` | character | UNKNOWN | none |
| 3 | `5e3f7a6d-81a9-1a40-ae0c-871a65a9b50c` | effects | UNKNOWN | none |
| 4 | `7bcce25f-c1ef-3142-941f-ba3108eaf3d2` | effects | UNKNOWN | none |
| 5 | `b6467bf6-a5e6-064e-b95a-de72922d2c4a` | effects | UNKNOWN | none |
| 6 | `a61f100e-e793-b04b-92a9-506c5f467283` | effects | UNKNOWN | none |
| 7 | `fd665c9f-629f-c944-9b4a-17965cec1509` | effects | `dynamic_break_window` | none |
| 8 | `4eb19c73-dc19-f748-b679-75bb183e0408` | effects | UNKNOWN | none |
| 9 | `94ad2147-2ce3-1f4c-bd51-ff324dba3de5` | effects | UNKNOWN | none |
| 10 | `77009170-11ad-a949-a478-f9358d245bb7` | effects | `dynamic_break_light_on` | none |
| 11 | `78a954b8-920f-1d4c-b1b4-03eacb16b90f` | effects | UNKNOWN | none |
| 12 | `844fb573-5a8d-8a4e-b989-5276030657cc` | effects | `fire_post_explosion` | none |
| 13 | `deca52af-98bc-6349-b6a4-1a16df3f62f8` | effects | UNKNOWN | none |
| 14 | `d167a490-2252-4b4c-8662-8dcb27901f0c` | effects | UNKNOWN | none |
| 15 | `8bd22a32-bc56-dd46-9131-28279f02686e` | effects | `dynamic_trail_large` | none |
| 16 | `f04a7623-759b-c342-970c-8b6e0d401154` | effects | UNKNOWN | none |
| 17 | `1f4a53c2-bf65-e445-bff0-abef23484ae4` | effects | UNKNOWN | none |
| 18 | `55d6b34f-fc0c-5a4c-928a-6d9f494ecccb` | effects | UNKNOWN | none |
| 19 | `650d4611-9965-024c-9daf-ce3e1f15ddb9` | effects | UNKNOWN | none |
| 20 | `09fa9fa3-218e-3041-9029-b69b82b63768` | effects | UNKNOWN | none |
| 21 | `db007316-ebd7-ae4a-a849-612ef7c87ee6` | effects | UNKNOWN | none |

`UNKNOWN` is the honest role: `Research/BatmobileGrab/AUDIO_BANKS.md` pairs 23 of the 45 GUIDs with
an `.epe` object name; the rest are code-fired with no name in the bank or the `.epe`. No role was
invented to fill the column.

## 3. Every mechanism searched, with its negative result

| # | mechanism | result | evidence |
|---:|---|---|---|
| 1 | Swap the sample payloads inside `effects.bank` / `character.bank` | **No.** These two banks are shared by every vehicle in the game; swapping them changes breaks, explosions and smoke for all traffic, not just the Batmobile. The proven in-place technique (test-060) applies to `vehicles.bank`, which is the 24 already green. | `Research/JC3Grab/JC3_AUDIO.md` §2, §8(a); `tmp/freebuff/reports/keep-audit-audio-fx.md` §3; backlog card B-26 |
| 2 | Author a private `effects`-class bank plus a new `.ee.fmod_guids` | **No.** The banks are FMOD Designer/Ex FEV v56 build 50, not Studio: events, tunes, parameters and DSP live in the FEV graph and no `.fev` project ships; a new bank would have to reproduce that graph. | `JC3_AUDIO.md` §1, §8(b) |
| 3 | Bind the bank per entity (`SAttachedEffect` / `SDynamicAttachedEffect`) | **No field exists.** The `.epe` does bind 23 of the 45 GUIDs as attached effects (that is how they fire), but the decoded EPE/GPCD schema carries **no bank member**: `Working/Audio/gpcd_schema.json` (38,073 B, 5 classes `SVehicleWheel`, `SVehicle`, `SVehicleSimBase`, `AkVehicleSoundInfo`, `RVehicleSimBatmobile`) contains **0 occurrences of "bank"**, and `Working/Audio/epe_true.json` (2,311 B) contains **0**. There is nothing to point at a private bank. | measured this run; `JC3_AUDIO.md` §1 |
| 4 | Redirect through `.ee.fmod_guids` | **No.** Its meaning is not decoded: the file is `version 1`, 3 bank names, 45 GUIDs, 0 trailing bytes; whether it is a preload list or a redirect is UNKNOWN, so it cannot be used as an override channel. | `JC3_AUDIO.md` §1 (line 91 note) |
| 5 | Loader-level list (`master.banklist`) | **No.** A plain 26-line, 434 B text list of bank files: it can tell the loader about another file, but it is global, has no entity dimension, and nothing here can author the bank's contents anyway. | `JC3_AUDIO.md` §8(b) |
| 6 | Repoint/rename the 21 GUIDs at donor samples | **Forbidden.** The events are code-fired and their names are not stored in the bank, so a repointed GUID is a silently wrong event rather than a mapped one; the card says do not rename or repoint. | `JC3_AUDIO.md` §1; card B-26 step 3 |

So the 21 are blocked on **an undecoded engine mechanism**, not on a bake, a gain or a manifest
row. That is why nothing was shipped: the alternative (a) requires proving a per-entity override
exists, and mechanisms 3-5 are exactly the places it would live; all three are empty.

**What would unblock it:** one of (i) a per-entity bank field found in a decoded `.epe`/GPCD class
that this export does not contain, (ii) a decoded `.ee.fmod_guids` redirect semantic, or (iii) a
test-060-style in-place swap proven not to be shared (i.e. evidence that JC3 loads a per-entity
`effects` bank instance). None is present today.

## 4. `vehicles#279`: named loop compromise, not a 3/3

| tree | record step (card's gate) | payload column (card's definition) | payload frame-0 join | p99 interior | verdict |
|---|---:|---:|---:|---:|---|
| `Builds/bm-RC4` (this build) | **-24.96** | **-38.03** | -74.75 | -46.07 | **RED** |
| `Builds/bm-004c` (the tree the review quotes) | -28.27 | **-39.68** | -60.77 | -46.01 | RED |

* The card's gate is `record step > -40 dBFS AND record step > p99`, which is RED on both trees.
  `weapons#408` is fixed on both (record -55.74 on RC4, -61.21 on 004c; loudness +0.00 LU).
* **The quoted -39.68 is bm-004c's number, not this build's.** This script re-derives it from
  bm-004c's own bytes and matches `Builds/bm-004c/verify/audio_004c.json` exactly (decoded sha and
  all three dBFS values); `bm-RC4`'s rebuilt banks measure -38.03 in the same column. Both are
  reported; neither is adjusted to match the other.
* **Definitional finding, recorded rather than used to flip the verdict:** the "payload" column is
  not the payload's frame-0 -> frame-(N-1) join. For the same slot, the raw record payload's own
  first/last step is -74.75 dBFS while the card's payload column is -38.03 dB, with the decoder's
  frame count equal to the payload's (`shift` = 16 frames for #279). The column therefore measures
  a step `shift` frames inside the loop. The true frame-0 join is **below** -40 on RC4. The card's
  ruling still stands as recorded (RED, 2/3), because changing a card's threshold to turn a red
  green is not this correction's job - but the -39.68 / -38.03 figure is a `shift`-offset step and
  whoever tunes #279 should be told that before chasing it.
* **Named compromise:** `vehicles#279` (`jc3_veh_lave_chassis_spin_creaks_loop_fast`) keeps the
  card's RED. The payload's own join is not smoothed further because doing so would change the
  vanilla timbre (the phase trim already applied is the derived fix; a second trim moves the
  creak pattern). It is recorded as a loop compromise, not as a pass.

### The 3/3 that existed and is now gone

`Builds/bm-RC4-audio/verify/audio.json` read `ALL GREEN`, `loop_pass: 3`. Cause: `gates_for()` in
`Tools/scripts/b11_rc4_audio.py` wrapped `v04_audio.seam()` (already dBFS) in `db()` again - printing
`27.94` where the record step is `-24.96` - and took the payload column from the raw record bytes
instead of the template's decode domain. Fixed to the card's definitions (`record = seam(pcm)`,
`payload = seam(pcm[shift:])`, p99 on the decoded payload, raw join kept separately as
`seam_payload_firstlast_dbfs`). Rebuilt and re-checked:

```
python Tools/scripts/b11_rc4_audio.py --write
RED: loop: 5/5 loudness, 2/3 loop, 2 banks (1,877 samples)
  vehicles#279 drop 932 frames -> payload seam -74.75 dBFS (was -39.68); gate agrees True
python Tools/scripts/b11_rc4_audio.py --check
CHECK PASS - RED: loop: 5/5 loudness, 2/3 loop, 2 banks, events 24/45 resolved
```

`verify/audio.json` now reads `RED: loop 2/3` with `vehicles#279 loop_ok: false`
(payload -38.03, record -24.96) and `weapons#408 loop_ok: true` (payload -39.48, record -55.74).
The rebuilt banks reproduced the same byte sizes (1,877 samples) and the check passes against them.

## 5. Verification run

```
python Tools/scripts/b11_rc4_audio.py --write     -> RED: loop 2/3, wrote banks + verify/audio.*
python Tools/scripts/b11_rc4_audio.py --check     -> CHECK PASS - RED: loop: 2/3 loop
python Tools/scripts/v04_audio_rc4.py --check     -> PASS: 5/5 loudness, 2/3 loop, 24/45, 45/45
```

And the RC4 receipt itself, read from disk (not re-derived by this correction):
`Builds/bm-RC4/receipt.json` holds `conflicts: []` (0) and `complete: false`, with both bank shas
still matching its `files` entries - V-04's check passes that comparison on every run.

## 6. Limits

* **No game run** (test ban): whether an entity-level bank override is honoured cannot be tested, so
  the 21 remain UNKNOWN-by-mechanism rather than proven-impossible. The mechanism census above says
  where it would have to live and that all three sites are empty.
* The 21 GUIDs' donor audio is **not** removed: a stock car and the Batmobile still share it. That
  is the stated gap on `T-AU2`.
* The loop alignment finding (section 4) is a measurement of this decoder (`vgmstream`) and this
  writer; it is not a claim about how the engine joins the loop at runtime.

## 7. Revert

```
git checkout Tools/scripts/b11_rc4_audio.py
# and restore Working/Audio/bm_bank_manifest_rc4.json + Builds/bm-RC4-audio by re-running the
# previous generator, or by rebuilding: python Tools/scripts/b11_rc4_audio.py --write
```

`Builds/bm-RC4` is untouched by this correction (its receipt and both banks are unchanged); V-04's
report pair is regenerated with `v04_audio_rc4.py --write` if its re-stamped manifest sha needs it.
