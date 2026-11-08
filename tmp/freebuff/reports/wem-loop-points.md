STATUS: done — the three V-04 loop points are **not** in the WAV (no `smpl` chunk) and **not on these three samples** (no FSB5 `LOOP` chunk), though the bank format carries them for 41 other samples; the loop region the data defines is the whole payload (`0 … frames−1`), and at that join only the minigun is below −40 dBFS as built. `Builds/bm-RC1/verify/loops.md` and `Tools/scripts/v04_loops.py --check` (87/87, exit 0) are written; no row, bank or payload was edited.

## Where the loop points live (answer)

| place the brief named | what the bytes say |
|---|---|
| Wwise bank event/sound structure | **Not Wwise.** Both banks are `RIFF` / `FEV ` / `FMT ` containers around an FSB5 sample bank (58 B of magic read from offset 0), i.e. FMOD Designer FEV v56 build 50 — the same format `Research/JC3Grab/JC3_AUDIO.md` §10 records. No byte says Wwise. |
| loop start/end in the bank | They live in the **per-sample FSB5 metadata chunk type 3 (`LOOP`), two little-endian uint32 (start, end)**. The built banks do carry them: `vehicles.bank` 29 samples, `weapons.bank` 12 (41 total, every pair `0 ≤ start < end ≤ frames`). |
| loop start/end on our three | **Absent.** `vehicles#151` and `vehicles#279` carry only type 13 (a 4-byte float gain, e.g. `00 00 80 3f` = 1.0); `weapons#408` carries type 5 (`00 00 00 00`) + type 13. No type 3. The vanilla record at the same bank+index is byte-identical, so B-11's splice did not remove it — the shipped payload never had one. |
| WAV `smpl` chunk | **Absent on all three.** `EC2FD42B.wav`, `0C69336B.wav`, `098BBFE1.wav` each contain exactly `fmt ` (16 B) + `data` — nothing else. |

Example pairs proving the format is read correctly (from the same built banks):

| bank | sample | frames | LOOP (start, end) | bytes |
|---|---|---:|---|---|
| vehicles | `jc3_vehicle_horn_truck_06_loop` #10 | 50,140 | (17,341, 50,136) | `bd 43 00 00 d8 c3 00 00` |
| vehicles | `jc3_vehicle_horn_car_08_loop` #78 | 53,519 | (10,303, 53,516) | `3f 28 00 00 0c d1 00 00` |
| weapons | `jc3_weapon_rpg_rocket_trail_loop_02` #84 | 138,148 | (87,542, 138,147) | `f6 55 01 00 a3 1b 02 00` |
| weapons | `jc3_w617_vintagefighter_mgun_loop` #186 | 154,245 | (14,000, 146,244) | `b0 36 00 00 44 3b 02 00` |

Consequence: for the three slots the loop region is the **whole payload** — start sample 0, end `frames−1`:

| slot | frames | loop region | length |
|---|---:|---|---|
| `vehicles#151` `jc3_veh_land_premium_nitro_loop` | 154,818 | 0 … 154,817 | 3.225375 s |
| `vehicles#279` `jc3_veh_lave_chassis_spin_creaks_loop_fast` | 336,000 | 0 … 335,999 | 7.0 s |
| `weapons#408` `jc3_wpn_minigun_fire_close_loop_04` | 160,337 | 0 … 160,336 | 3.340354 s |

## Does the loop end join the loop start within −40 dBFS?

| slot | last→first step (as built) | ≤ −40? | own interior p99 | outlier? | verdict |
|---|---:|---|---:|---|---|
| vehicles#151 nitro | **−18.18 dBFS** | no | −10.99 | no | above −40 but inside its own step distribution |
| vehicles#279 creaks | **−16.95 dBFS** | no | −46.01 | **yes** | **click** |
| weapons#408 minigun | **−63.27 dBFS** | yes | −8.86 | no | joins cleanly |

So by the card's number: **1 of 3 passes** (the minigun). By V-04's actual rule (−40 **and** an
outlier against the payload's own p99): **only the creaks is a defect** — the nitro's step is louder
than −40 but quieter than 99 % of its own interior steps, i.e. that payload is simply that noisy.

**A correction V-04 needs.** The built record is not the payload alone: it is
`vanilla[0:slack] + payload[0:len−slack]`, reproduced **byte for byte** for all three slots. The
record's surplus over `frames × channels × 2` (60 / 32 / 92 B = 30 / 16 / 23 frames) therefore sits
*in front of* the new payload, and the same number of frames is dropped off its end. The sample that
actually precedes the loop start is `payload[frames−1−shift]`:

| slot | record bytes | PCM bytes | surplus | shift | join is | payload's own wrap |
|---|---:|---:|---:|---:|---|---:|
| vehicles#151 | 309,696 | 309,636 | 60 B | 30 fr | `payload[154,787]` → `vanilla[0]` | −16.36 dBFS |
| vehicles#279 | 672,032 | 672,000 | 32 B | 16 fr | `payload[335,983]` → `vanilla[0]` | −17.5 dBFS |
| weapons#408 | 641,440 | 641,348 | 92 B | 23 fr | `payload[160,313]` → `vanilla[0]` | −28.14 dBFS |

On the payload's own end **none of the three passes −40** (−16.36 / −17.5 / −28.14), so the
minigun's clean result is an artifact of the dropped frames landing on a quiet moment, not a property
of its loop. The creaks' click is a **tile cut**: its slot (336,000) is longer than its source
(186,497), the fill repeats with a 2,048-frame crossfade, and the truncation lands at source sample
**151,550 of 186,497** — mid-loop — then jumps to sample 0. The minigun's cut lands at source sample
4,184 of 80,124. Fixing either is a build change (fill to whole copies, or cut at a zero crossing);
it is recorded, not made.

## Files written

| file | what |
|---|---|
| `Tools/scripts/v04_loops.py` | new tool, `--write` / `--check`: parses both banks' FSB5 sample headers, counts LOOP chunks, decodes the six streams, rebuilds each payload, measures every step, and re-derives the tiling arithmetic |
| `Builds/bm-RC1/verify/loops.md` | 11,978 B: the loop-point answer with the chunk bytes, the 41-pair census, the three records, the splice-offset reconstruction, the seam table, the tile-cut explanation, the FEV event/tune row, UNKNOWNs |
| `tmp/freebuff/reports/wem-loop-points.md` | this report |

`Builds/bm-RC1/verify/loops.md` is the only file added inside a build tree, because the brief names
that path; it is a verify document, not a payload. `--check` asserts both banks still hash to B-11's
`written` sha256 (`vehicles` `76d67bcef81c8d29…`, `weapons` `5b8a7605a8b70ca2…`), so nothing shipped
changed. No install, no launch, no game.

## Commands run (verbatim)

```
cd /e/Modding/JC3-Batmobile && set -o pipefail && echo "=== write ===" && python Tools/scripts/v04_loops.py --write; echo "write exit=$?"; echo "=== check ===" && python Tools/scripts/v04_loops.py --check | grep -E "FAIL|check:" ; echo "check exit=${PIPESTATUS[0]}"
```
```
=== write ===
wrote Builds/bm-RC1/verify/loops.md (11927 bytes)
  vehicles#151 jc3_veh_land_premium_nitro_loop: loop 0..154817, join payload[154787]->vanilla[0], as built -18.18 dBFS, own -16.36 dBFS
  vehicles#279 jc3_veh_lave_chassis_spin_creaks_loop_fast: loop 0..335999, join payload[335983]->vanilla[0], as built -16.95 dBFS, own -17.5 dBFS
  weapons#408 jc3_wpn_minigun_fire_close_loop_04: loop 0..160336, join payload[160313]->vanilla[0], as built -63.27 dBFS, own -28.14 dBFS
write exit=0
=== check ===
check: all assertions passed
check exit=0
```

The full assertion list (87 PASS, exit 0), tail:

```
PASS jc3_veh_lave_chassis_spin_creaks_loop_fast: loop region is the whole payload (0..335999)
PASS jc3_veh_lave_chassis_spin_creaks_loop_fast: vgmstream reports no loop line
PASS jc3_veh_lave_chassis_spin_creaks_loop_fast: vanilla[:slack] + payload[:len-slack] reproduces the built stream byte for byte
PASS jc3_veh_lave_chassis_spin_creaks_loop_fast: the shift is the surplus over the PCM (16 frames)
PASS jc3_veh_lave_chassis_spin_creaks_loop_fast: the join's last sample is payload[frames-1-shift]
PASS jc3_wpn_minigun_fire_close_loop_04: built record carries no LOOP chunk
PASS jc3_wpn_minigun_fire_close_loop_04: the vanilla record at the same index carries none either
PASS jc3_wpn_minigun_fire_close_loop_04: built and vanilla metadata are identical (the swap kept the header)
PASS jc3_wpn_minigun_fire_close_loop_04: the source WAV has no smpl chunk
PASS jc3_wpn_minigun_fire_close_loop_04: loop region is the whole payload (0..160336)
PASS jc3_wpn_minigun_fire_close_loop_04: vgmstream reports no loop line
PASS jc3_wpn_minigun_fire_close_loop_04: vanilla[:slack] + payload[:len-slack] reproduces the built stream byte for byte
PASS jc3_wpn_minigun_fire_close_loop_04: the shift is the surplus over the PCM (23 frames)
PASS jc3_wpn_minigun_fire_close_loop_04: the join's last sample is payload[frames-1-shift]
PASS as built, minigun joins below -40 dBFS (-63.27)
PASS nitro exceeds -40 (-18.18) but stays under its own p99
PASS creaks exceeds -40 (-16.95) and its own p99 (-46.01)
PASS jc3_veh_land_premium_nitro_loop: the payload's own wrap is above -40 (-16.36 dBFS)
PASS jc3_veh_lave_chassis_spin_creaks_loop_fast: the payload's own wrap is above -40 (-17.5 dBFS)
PASS jc3_wpn_minigun_fire_close_loop_04: the payload's own wrap is above -40 (-28.14 dBFS)
PASS creaks' own wrap is an outlier against its own p99 (-17.5 vs -46.01)
PASS nitro's and the minigun's own wraps stay inside their own p99
PASS creaks is tiled and cut mid-source at 151550
PASS nitro is not tiled (its slot fits its span)
PASS vehicles.bank still hashes to B-11's written sha256 (build untouched)
PASS weapons.bank still hashes to B-11's written sha256 (build untouched)
PASS Builds/bm-RC1/verify/loops.md matches a fresh render (every number re-derived)
PASS the report carries the LOOP-chunk table

check: all assertions passed
check exit=0
```

Probes that found the structure (before the tool existed) are reproducible from the tool: the
record-surplus scan, the metadata dump, and `vgmstream -s IDX -m` on the bank.

## Labels

- **Decoded:** `RIFF`/`FEV `/`FMT `/`FSB5` magic and the FSB5 header fields; the per-sample metadata
  chunk types and their bytes; the 41 LOOP pairs; the three records' metadata; the WAV chunk lists;
  each decoded stream's PCM (first/last bytes, int16 values); the record surplus per slot; the
  manifest's event/tune GUIDs and body sizes.
- **Derived:** the loop region (0…frames−1) from the absence of both loop fields; the
  `vanilla[0:slack] + payload[0:len−slack]` reconstruction (asserted byte-exact, so the offset is
  proven, not assumed); the −40 dBFS comparisons and the p99 outlier test; the tiling arithmetic
  (period, copies, cut sample); "the minigun's pass is an artifact" (its own wrap is −28.14).
- **UNKNOWN:** the four items in the report's §7 — see below.

## UNKNOWNs

1. **Whether the game loops these three at all, and over what region.** The sample carries no loop
   pair, so either the engine loops the whole payload or the FEV tune does; no decoded field decides
   it and no game was run (test ban). Where it would be found: a Q-1 #7 take, or a decode of the FEV
   playback/loop fields — not present in `jc3audio.py` today.
2. **What the FEV tune bodies contain** (181 B for A-02, 92 B for A-05; W-03 has no donor GUID and
   resolves through its slot). Only GUIDs, the tune→event link and sizes are decoded, so a loop count
   or mode could live there unread.
3. **Whether −40 dBFS is the right bar for these payloads.** The nitro is where the number and the
   ear may disagree; only a take could settle it.
4. **What the record surplus (32–92 B) is.** It is measured per record and used as the offset, and
   the reconstruction proves its *effect*, but its meaning (padding vs per-sample trailer) is not
   decoded.

## Bug found in V-04's own tool (not fixed — another task's file)

`Tools/scripts/v04_audio.py:124` parses vgmstream's loop line with
`int(s.split(":", 1)[1].split("(")[0].strip())`, which raises
`ValueError: invalid literal for int() with base 10: '17341 samples'` on any sample that **does**
carry a `LOOP` chunk (`loop start: 17341 samples (0:00.361)`). V-04 only ever decoded the five
swapped slots, none of which has the chunk, so it never hit this — but it means V-04 cannot decode a
looped sample at all, which is why its "no loop line" evidence could never have been positive.
Reported here; `v04_audio.py` was not modified.

## COMPROMISES

None. No value guessed, no payload or bank written, no install, no launch. The one build tree file
added is the verify document the brief names, and the shipped banks are hash-verified unchanged.
