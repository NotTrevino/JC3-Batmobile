# V-04 audio gates on `Builds/bm-RC4`

`python Tools/scripts/v04_audio_rc4.py --write` measures; `--check` re-derives every
number and asserts the result. Offline and read-only: no bank is written, nothing is
installed and no game is launched.

**PASS: 5/5 loudness, 2/3 loop (vehicles#279 RED), 24/45 events resolved** - 5 swapped samples in 2 built banks, 3 of them `_loop`.

## The two banks in the tree

| bank | bytes | sha256 | receipt match |
|---|---|---|---|
| `sound/fmod_banks/vehicles.bank` | 210,781,376 | `aab92ca03f8cbbfe...` | PASS |
| `sound/fmod_banks/weapons.bank` | 177,586,080 | `d05b74ed9111ecad...` | PASS |

`character.bank` and `effects.bank` are **not** in this tree, so the 21 donor GUIDs
below have no carrier here (B-26).

## Gate summary

| gate | result |
|---|---|
| decode | GREEN |
| length | GREEN |
| loudness | GREEN |
| loop | RED |
| tail | GREEN |
| length | 5/5 within 1 frame of the source span |
| loudness | 5/5 within 1 LU of the vanilla event |
| loop wrap | **2/3** below the -40 dBFS rule |

## Per sample, decoded from the built bank

| slot | name | frames / span | d frames | LUFS built / vanilla | d LU | loudness |
|---|---|---|---|---|---|---|
| `vehicles#7` | `jc3_veh_door_tank_open_03` | 29954 / 29954 | +0 | -21.85 / -21.85 | +0.00 | PASS |
| `vehicles#98` | `jc3_veh_door_tank_close_01` | 24933 / 24933 | +0 | -11.02 / -11.02 | +0.00 | PASS |
| `vehicles#151` | `jc3_veh_land_premium_nitro_loop` | 154818 / 154818 | +0 | -10.33 / -10.33 | +0.00 | PASS |
| `vehicles#279` | `jc3_veh_lave_chassis_spin_creaks_loop_fast` | 336000 / 336000 | +0 | -20.45 / -20.25 | -0.20 | PASS |
| `weapons#408` | `jc3_wpn_minigun_fire_close_loop_04` | 160337 / 160337 | +0 | -5.3 / -5.3 | +0.00 | PASS |

Length is measured against `span = src_frames + padded_frames - trimmed_frames`
(the WAV after B-11's documented trim/tile, V-04/3); against the raw WAV a swap cannot
pass because the slot keeps its frame count.

## Loop wrap, per `_loop` sample

| slot | seam, decoded record | seam, payload after the codec header | vanilla seam | interior p99 | header frames | verdict |
|---|---|---|---|---|---|---|
| `vehicles#151` | **-18.18 dBFS** | -8.67 dBFS | -17.24 dBFS | -10.99 dBFS | 30 | PASS |
| `vehicles#279` | **-24.96 dBFS** | -38.03 dBFS | -41.24 dBFS | -46.07 dBFS | 16 | RED |
| `weapons#408` | **-55.74 dBFS** | -39.48 dBFS | -11.13 dBFS | -11.54 dBFS | 23 | PASS |

The gate is V-04's: a click is a decoded end->start step above -40 dBFS **and**
above the payload's own p99 interior step. The payload-domain column is the same step
with the record's codec header (decoded as audio by the decoder) dropped.

* `weapons#408` - **PASS**: record step -55.74 dBFS and payload step -39.48 dBFS, loudness +0.00 LU against vanilla; its p99 is -11.54 dBFS, so the payload-domain step is inside its own interior distribution.
* `vehicles#279` - **RED**: record step -24.96 dBFS is above the -40 dBFS rule and above this payload's own p99 (-46.07 dBFS), so it is an outlier click, not the noise floor; the payload-domain step is -38.03 dBFS, still above -40.

**So the loop gate is 2/3, not 3/3.** A run that reports 3/3 has measured a
different domain, dropped the p99 rule, or gated the wrong tree.

## Where the quoted dBFS come from

The review quotes `-28.27` record / `-39.68` payload for `vehicles#279` and `-61.21` for
`weapons#408`. Those are **`Builds/bm-004c`'s bytes**, and this script re-derives them
there:

| slot | tree | record | payload | p99 | matches `audio_004c.json` | decoded sha == json |
|---|---|---|---|---|---|---|
| `vehicles#279` | `Builds/bm-004c/banks` | -28.27 | -39.68 | -46.01 | YES | YES |
| `weapons#408` | `Builds/bm-004c/banks` | -61.21 | -50.75 | -11.54 | YES | YES |

`bm-RC4`'s banks were rebuilt from the manifest, so the same measurement on this
tree gives the numbers in the table above (`vehicles#279` record -24.96, payload -38.03; `weapons#408` record -55.74, payload -39.48). The verdict is the
same - #279 above the rule and above its p99, #408 fixed - but the magnitudes belong to
the tree they were measured on. The `sha_matches_json` column shows bm-004c is still the
tree those numbers describe.

## The 45 pinned GUIDs

* `.ee.fmod_guids`: **45/45** present (re-emitted).
* resolved in the built banks: **24/45** (character 2, effects 19, vehicles 24).
* donor banks not built: **21** (effects + character) - **B-26**, named per GUID in the JSON.

| bank | GUIDs | resolved | status |
|---|---|---|---|
| `character` | 2 | 0 | donor bank not built - B-26 (per-entity override) |
| `effects` | 19 | 0 | donor bank not built - B-26 (per-entity override) |
| `vehicles` | 24 | 24 | resolved in the built bank |

Every resolved GUID has both its FEV event and its tune table row in the built
bank; the 21 donor GUIDs have no event row to resolve because their bank is not in
this tree.

## Not a failure of this build

`python Tools/scripts/bm_audio.py --check` targets `Builds/bm-004` and probes the live
install, whose two banks were overwritten by later test installs (2026-11-02 21:48:39);
its derivation diff is 0. It measures a different tree, so it is not evidence against
`Builds/bm-RC4`.

## Limits

* **No game run.** These are decoded bytes: whether the engine honours the loop is
  UNKNOWN (test ban).
* **`vehicles#279` stays RED** on the card's rule: record step -24.96 dBFS against -40 and p99 -46.07 dBFS.
  It is recorded, not bent.
* **The exact magnitudes in the review are bm-004c's**, reproduced above; the RC4 tree's
  own numbers differ by 1-5 dB because its banks are rebuilt bytes. Neither number is
  adjusted to match the other.
* **The 21 donor GUIDs' audio** needs B-26's per-entity bank override, whose mechanism
  is not decoded; no substitute is counted as resolved here.
* Loop points of the three `_loop` slots are still not carried in FSB5 LOOP metadata
  (`v04_loops.py`): the whole payload is the loop, as measured.
