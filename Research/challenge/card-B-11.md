# Assumption challenge — backlog card B-11 (audio bank)

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–76), the **B-11** card (§8, line 1074), its **§12**
row (line 1340), MODLOG §"B-11 start — intended change" (17183, 17389, 17436), §"B-11 · Audio bank —
done" (17469–17612) and §"B-11 · done — independent verification" (17613–17800), and the card's
outputs: `Tools/scripts/bm_audio.py`, `Working/Audio/bm_bank_manifest.json`, `Builds/bm-004/`
(`banks/vehicles.bank`, `banks/weapons.bank`, `aaf/`, `receipt.json`, `install.ps1`), plus its
inputs `Working/Translation/t12_audio_map.json` (T-16), `Research/JC3Grab/JC3_AUDIO.md` §10 and
`Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` (the in-repo vanilla copy).

**Read-only:** nothing was modified except this file. No game launch, nothing written under
`D:/Games`, no commit, no secrets. All commands are read-only Python/`fsb5`/`jc3audio` reads over
files in the tree.

**Two limits, stated up front.**
1. `weapons.bank`'s vanilla source is `E:\Modding\JustCause3\_grab\audio\weapons.bank` (outside the repo, R10),
   so the weapons side can be verified **only against the built file and the manifest**, never
   against its source. The vehicles side can be verified end-to-end because its source is in-repo.
2. `python Tools/scripts/bm_audio.py --check` was **not** re-run: `build(write=False)` copies both
   banks through a temp directory (≈388 MB) to compare, which is outside this session's read-only
   mandate. Every number below is an independent re-read instead.

---

## VERDICT summary

**The file mechanics are exactly as advertised — I reproduced the bank hashes, both FSB5 parses,
all five payload hashes, the 4/4 event GUIDs in `EVTS` + `TLNB`, the 758-byte `.ee.fmod_guids`, and
the 590-file identity tree. What the mechanics hide is what the swap does to the sound.** The
manifest's own `measured` block shows that three of the five replacements did not fit their slots:
two loop samples were **padded with silence** (149,503 frames = 44.5 % of the 7.0 s chassis-creak
loop; 80,213 frames = 50.0 % of the 3.34 s minigun loop), two door samples were **trimmed** (3,325
and 2,961 frames), and the minigun was driven into **3.53 % clipping**. The card's summary sentence
"0 clipped/padded" is refuted by the card's own manifest. Separately, the loudness gate measures the
**mono** payload before channel replication, so the one stereo slot ships 3.01 LU above the number
the manifest calls delivered; and the W-03 weapon sample has no GUID, is not in the entity's
45-GUID pin list (which does not name the weapons bank at all), and is half silence.

Of 16 assumptions tested: **10 HOLD, 2 WEAK, 4 BROKEN** — and again the split is systematic:
every *container/code* claim holds (hashes, counts, parse, GUIDs, installer), while four claims
about what the swap *does to the sound* or *who it affects* break.

| # | Assumption (stated or silent) | Verdict |
|---|---|---|
| B11-01 | a swapped payload may be forced to the slot's frame count (trim/pad) without changing what is heard | **BROKEN** — two loops gain 3.1 s / 1.67 s of silence (44.5 % / 50.0 % of the loop), two door sounds lose 69 / 62 ms; the original #279 is 100 % audible |
| B11-02 | "each payload re-measured as the map measured it … and **0 clipped/padded**" | **BROKEN** — the manifest records 149,503 + 80,213 padded frames, 3,325 + 2,961 trimmed, `clip_pct` 3.53; the map has no clip/pad field to "say so" |
| B11-03 | the delivered loudness is the map's number (LU delta 0.00) | **HOLDS** for what it is — and stronger than claimed: for the three mono slots the delivered LUFS equals the **original slot's** measured LUFS exactly (−21.85 / −11.02 / −10.33). The 0.00 delta itself is tautological (same function, same bytes) |
| B11-04 | loudness is measured in the same channel convention the slot plays in | **WEAK/BROKEN** — the gate measures a mono payload; slot #408 is 2 ch, and the built 2 ch payload measures **−2.86 LUFS** against the manifest's −5.87 (3.01 LU = the BS.1770 channel sum) |
| B11-05 | "no `.fev` project ships", so a bank cannot be authored (route b impossible) | **HOLDS** — 0 `.fev`/`.fdp` entries in the 81,952-entry index; `master.banklist` is the only bank-list file |
| B11-06 | `tune→sample` is stored nowhere, so the sample inside a tune must be chosen by name | **HOLDS** — independently: 0 of 257 vehicle tunes and 0 of 377 weapon tunes contain any FSB5 wave GUID |
| B11-07 | Done 1: "every mapped event resolves" | **HOLDS** mechanically — 4/4 vehicle GUIDs present in `EVTS` **and** `TLNB` (257 events / 257 tunes); W-03 resolves only as a slot name |
| B11-08 | the chosen slot is the sound the feature plays (R5) | **WEAK** — 3 of 5 slots are `slot_confidence: candidate` "name match"; only A-02 has an in-game proven swap (test-060 indices 56/150/355). The card admits it, but the *result* rests on it |
| B11-09 | W-03 delivers the Batmobile's Vulcan sound | **BROKEN** — no GUID, absent from the 45-GUID pin list, and that list names banks `vehicles/character/effects` only, not `weapons`; the payload is 50 % silence and 3.53 % clipped |
| B11-10 | swapping a sample in the global bank affects only the Batmobile | **BROKEN (unstated)** — the banks are one global file each (both carried in the archives, installed as a loose override); the four chosen names are generic donor samples (`jc3_veh_door_tank_open_03`, `…premium_nitro_loop`, `…chassis_spin_creaks_loop_fast`). Every vehicle that uses them changes too, and the count is UNKNOWN because tune→wave is not stored |
| B11-11 | R7: the vanilla bank is never edited in place | **HOLDS** — the build ships copies; the source hash is re-verified, the installer backs up and restores |
| B11-12 | `Builds/bm-004/aaf` is bm-001's identity tree | **HOLDS** — 590 files each, 0 added / 0 removed / 0 changed |
| B11-13 | `.ee.fmod_guids` re-emitted byte-identical, so no `.ee`/`.toc` change is needed | **HOLDS** — 758 B, identical to the `.ee`'s own inner entry, 45 GUIDs, all four mapped event GUIDs present |
| B11-14 | sample counts (649 + 1,228) and both file sizes unchanged | **HOLDS** for vehicles (source in repo, re-parsed 649); **WEAK** for weapons (1,228 re-parsed, but the source is outside the repo and cannot be compared) |
| B11-15 | the installer handles and rolls back the bank (old AUD-5) | **HOLDS** — pins match the built files, `Rollback091` restores backups or removes added files, and the test-091 re-install is guarded by `-GameDir`; rehearsals still on disk in `tmp/b11/` |
| B11-16 | a loose `dropzone\sound\fmod_banks\*.bank` overrides the archived bank with no `.toc` | **HOLDS** on the recorded evidence (test-060, MODLOG §71) — not re-testable here without launching, and not re-derived by this card |

---

## 1. B11-01 — the payload may be forced into the slot's frame count

**Why the card rests on it.** `bm_audio.py`'s docstring and the Done-2 logic: *"the payload is
rebuilt (`mono_48k` → gain → trim/zero-pad → PCM16)"*, written over the sample's own `data:` block,
*"never touching the FSB5 header — so sample counts (649 + 1,228) and both file sizes are
unchanged"*. The header carries each sample's frame count, so the replacement **must** match it; the
code enforces this (`if s.samples != e["frames"]: raise`).

**Test — what the map's frame count does to each source.** The manifest records it per slot:

```
$ python  # manifest slots: measured block
A-06 vehicles#7   jc3_veh_door_tank_open_03                   frames=  29954 src=  33279 trimmed=  3325 padded=     0 clip%=0.0
A-07 vehicles#98  jc3_veh_door_tank_close_01                  frames=  24933 src=  27894 trimmed=  2961 padded=     0 clip%=0.0
A-02 vehicles#151 jc3_veh_land_premium_nitro_loop             frames= 154818 src= 154819 trimmed=     1 padded=     0 clip%=0.1
A-05 vehicles#279 jc3_veh_lave_chassis_spin_creaks_loop_fast  frames= 336000 src= 186497 trimmed=     0 padded=149503 clip%=0.0
W-03 weapons#408  jc3_wpn_minigun_fire_close_loop_04          frames= 160337 src=  80124 trimmed=     0 padded= 80213 clip%=3.53
```

**Test — what the original slots sounded like.** Reading the vanilla bank in the repo and counting
non-zero frames per slot:

```
$ python  # Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank, the slots bm-004 replaces
7   jc3_veh_door_tank_open_03                  frames 29954  audible 22404  silent_tail 7550  (74.8 % audible)
98  jc3_veh_door_tank_close_01                 frames 24933  audible 24906  silent_tail 27    (99.9 %)
151 jc3_veh_land_premium_nitro_loop            frames 154818 audible 154788 silent_tail 30    (100.0 %)
279 jc3_veh_lave_chassis_spin_creaks_loop_fast frames 336000 audible 335984 silent_tail 16    (100.0 %)
```

**Test — what the build ships.** Reading the built bank:

```
#279 ... payload_sha_ok=True changed_bytes=658175
     audible_frames=186497/336000  silent_tail=149503  LUFS orig=-20.25  built_whole=-20.45  built_audible=-20.25
#408 ... payload_sha_ok=True
     audible_frames=160248/160337  silent_tail≈80213  clip_frac=0.0353
```

**Result.** Slot #279 was a 7.0 s loop that was **100 % audible** in the shipped bank; the build
replaces it with 3.885 s of creak followed by **3.115 s of digital silence inside the loop**. Slot
#408 was 3.34 s and is replaced by 1.67 s of minigun followed by 1.67 s of silence. Slot #7's
157 ms silent tail is replaced by sound, and #7/#98 lose 69/62 ms off the end. The "same length"
property that keeps the header valid is exactly what makes three of the five swaps audibly wrong,
and no Done check looks at the waveform — Done 2 checks `frames`, name, rate, channels, duration and
the payload hash, all of which are satisfied by construction.

**Verdict: BROKEN** for the sound; **HOLDS** for the container.

---

## 2. B11-02 — "0 clipped/padded where the map says so"

**Why the card rests on it.** §12 row and MODLOG 17469: *"each payload re-measured as the map
measured it, **max LU delta 0.00 ≤ 0.05** and **0 clipped/padded** where the map says so"*.

**Test 1 — does the map carry a clip/pad field?**

```
$ python  # slot keys in Working/Translation/t12_audio_map.json (chosen slot of A-02)
{'bank','index_1based','name','frames','rate','channels','gain_db','delivered_lufs',
 'src_lufs','chosen','loop_start','loop_end'}
```

There is no `clip_pct`, `padded_frames` or `trimmed_frames` in the map — those numbers exist only in
the manifest, computed by the generator. "where the map says so" has no referent.

**Test 2 — the manifest's own numbers** (quoted in §1 above): 149,503 + 80,213 padded frames,
3,325 + 2,961 trimmed frames, `clip_pct` 3.53 on W-03. The clean-run `PASS` line the card prints
(`max LU delta 0.00 <= 0.05`) does not mention any of them.

**Result.** The sentence is false on the card's own artefact. Zero LU delta is also inevitable: the
generator refuses to write unless `|measured − map| ≤ 0.05`, and `measured` is recomputed by the
same function on the same bytes — the check can only ever print 0.00 (see B11-03).

**Verdict: BROKEN.**

---

## 3. B11-03 — the delivered loudness is the map's number

**Why the card rests on it.** The five-row table in MODLOG 17469 has a column `LUFS (map / rebuilt)`
with identical pairs, and the PASS line reads `max LU delta 0.00`.

**Test.** Measure the **original** slot and the **built** slot with the project's own BS.1770
function (`bmak_audio_features.integrated_lufs`):

```
#7   LUFS orig=-21.85  built=-21.85  map=-21.85
#98  LUFS orig=-11.02  built=-11.02  map=-11.02
#151 LUFS orig=-10.33  built=-10.33  map=-10.33
#279 LUFS orig=-20.25  built=-20.45  map=-20.45   (audible part of the build: -20.25)
```

**Result.** For the three slots without padding, the replacement's loudness is exactly the loudness
of the sample it replaces — a genuine, better-than-claimed result (the map's `delivered_lufs` is the
donor slot's level, and the swap is level-neutral). For #279 the 0.2 LU gap is precisely the padding:
the whole padded buffer reads −20.45 while the audible part still reads −20.25, so the "match" is
measured over silence. The `0.00` column is not evidence of anything by itself — it is what the gate
forces.

**Verdict: HOLDS** (the loudness is right for 3 of 5, and within 0.2 LU for the fourth) but **the
proof offered is circular**; the padding in #279 is what the number hides.

---

## 4. B11-04 — loudness measured in the channel convention the slot plays in

**Why the card rests on it.** The loudness gate runs in `payload()` on the mono array
(`integrated_lufs(q[:, None], RATE)`) **before** the payload is replicated to the slot's channels:

```
pcm = np.clip(e["payload"] * 32768.0, ...)
if int(e["channels"]) > 1:
    pcm = np.repeat(pcm[:, None], int(e["channels"]), axis=1).reshape(-1)
```

**Test.** The manifest and the built bank for the one stereo slot:

```
slot 408: jc3_wpn_minigun_fire_close_loop_04 frames 160337 ch 2
payload_sha_ok True
audible_frames=160248/160337 clip_frac=0.0353
LUFS (built, 2 ch, BS.1770 channel sum) = -2.86   audible = -2.54   map (mono) = -5.87
```

The gap is 3.01 dB = `10·log10(2)`, exactly the correlation sum of the same mono signal in two
channels; `integrated_lufs` sums channel power (`z = (y**2).mean(axis=0).sum()`).

**Result.** The gate compares a **mono** measurement with a **stereo** delivery. Either the map's
−5.87 was measured on the original stereo slot (in which case the dual-mono replacement is 3 LU
hotter than the sound it replaces), or it was measured mono (in which case the map and the delivered
stereo are in different units, and the other 3 mono slots are the only ones where the comparison is
meaningful). The built slot cannot distinguish the two because the vanilla weapons bank is outside
the repo — but the 3.01 LU discrepancy is real and is recorded nowhere in the manifest, whose
`written` block does record `channels: 2` next to a mono loudness.

**Verdict: WEAK** (would be BROKEN if the original #408 is stereo at ≈ −5.87; unprovable here).

---

## 5. B11-05 — "no `.fev` project ships", so route b is impossible

**Why the card rests on it.** `JC3_AUDIO.md` §10 route b is the *only* way to add a new event or
author a bank; if a `.fev` existed, B-11 could ship authored events instead of swapping donor
samples, and W-03's missing GUID would not be an open item.

**Test.** Search the full archive index (81,952 entries) for a project file:

```
$ grep -c "\.fev\|\.fdp" Research/JC3Grab/INDEX.jsonl
0
$ grep -n "banklist" Research/JC3Grab/INDEX.jsonl
sound/fmod_banks/master.banklist  archives_win64/game5  base   460 B
sound/fmod_banks/master.banklist  patch_win64/game5     patch  434 B
```

Both banks themselves are in the archives (`sound/fmod_banks/vehicles.bank` base 210,803,872 B /
patch 210,781,376 B; `weapons.bank` base 177,586,144 B / patch 177,586,080 B), and the only
bank-list is the 26-line text file — no authoring project.

**Result.** The claim holds over the whole census, not a sample. (It says "nothing *here* can author
the graph", which is accurate: the FEV graph is inside the bank and no project ships.)

**Verdict: HOLDS.**

---

## 6. B11-06 — `tune→sample` is stored nowhere

**Why the card rests on it.** It is the reason the sample is picked by name rather than decoded, and
the reason B11-08 is a WEAK and not a BROKEN.

**Test.** Parse every tune body and look for any of the bank's wave GUIDs in any 16-byte window:

```
$ python  # jc3audio.section_entries(TLNS/TMLN) + fev_waves
vehicles waves 649 tunes 257 tunes carrying a wave GUID: 0
weapons waves 1228 tunes 377 tunes carrying a wave GUID: 0
```

**Result.** Reproduced independently, and stronger than the card's own figure (it cites 0/649 wave
GUIDs in tune chunks; the tune count is 257/377). The link from an event's tune to the FSB5 sample
is not in the file.

**Verdict: HOLDS.**

---

## 7. B11-07 — Done 1, "every mapped event resolves"

**Why the card rests on it.** The card's Done line.

**Test 1 — the event store, re-parsed from the built banks with no manifest involvement.** My first
pass compared the manifest's *dashed* GUIDs against `fev_events`' *undashed* hex and printed `False`
for all four; normalising the way `bm_audio.py` does (`g = guid.replace("-", "")`) gives:

```
vehicles events 257 tunes 257
    A-06 500e1421… in events True in tunes True
    A-07 f58a18f7… in events True in tunes True
    A-02 f74ea43b… in events True in tunes True
    A-05 1f867af8… in events True in tunes True
    (tune GUIDs present: 90df05e8…, e506bb42…, 20bf6f75…, 5f655385…)
weapons events 377 tunes 377
    W-03 guid None
```

**Test 2 — the detour is worth recording**: the GUID comparison is format-sensitive, and the check's
own PASS is the only place the normalisation lives. A reader comparing raw hex will conclude the
events are missing (I did, for one command).

**Result.** 4/4 vehicle rows resolve twice over, exactly as claimed. W-03 resolves as a *slot name*
only — see B11-09. Note that "resolves" means "the GUID exists in `EVTS` and has a `TLNB` row"; it
does not mean the sample that was swapped is the one the tune plays (B11-06, B11-08).

**Verdict: HOLDS** (for the claim as written).

---

## 8. B11-08 — the chosen slot is the sound the feature plays (R5)

**Why the card rests on it.** Five features are "mapped" and five samples swapped; AUD-2/5/6 are
delivered by those swaps.

**Test.** The T-16 map records how each slot was chosen:

```
A-02 slot_confidence=proven   slot_method=proven swap: test-060 replaced FSB5 indices 56/150/355
                              (0-based) with these names' payloads and the bank still parsed + decoded
A-06 slot_confidence=candidate slot_method=name match: an armoured hinged shell is the tank door set;
                              the car-door start samples are the fallback if the tank door reads too heavy
A-05 slot_confidence=candidate slot_method=name match: the only `chassis_spin` sample in vehicles.bank
A-07 slot_confidence=candidate slot_method=name match: same family as A-06 so the open/close pair is coherent
W-03 slot_confidence=candidate slot_method=name match: `minigun_fire_close_loop` is the vehicle/player
                              minigun fire loop
```

**Result.** One of five swaps rests on an in-game observation; the other four rest on the sample's
name. The card says so in "What is deliberately not claimed" (1) and routes the disagreement to a
T-16 row — that is honest, but the *result* (the Batmobile now sounds like this) is still a name
match, and for A-06 the map itself calls the chosen tank door a risk ("if the tank door reads too
heavy").

**Verdict: WEAK** (stated, not hidden).

---

## 9. B11-09 — W-03 delivers the Batmobile's Vulcan

**Why the card rests on it.** `GRAB_BACKLOG.md:1075`: *"weapon sounds per T-11"*; the §12 row counts
W-03 as one of the five delivered swaps.

**Test 1 — is the sample referenced?**

```
W-03 guid None            (map, and manifest)
Mapped event GUIDs in the .ee's 45-GUID list:
    A-06 True  A-07 True  A-02 True  A-05 True
    any weapons GUID? []
the .fmod_guids names banks: ['vehicles', 'character', 'effects']   ← no 'weapons'
```

**Test 2 — what the sample is.**

```
W-03 weapons#408 frames=160337 src=80124 padded=80213 clip%=3.53
built slot: audible 160248/160337, clip_frac 0.0353
```

**Result.** Two separate gaps. (a) The swapped sample is not pinned by anything the Batmobile ships:
the entity's `.fmod_guids` covers the three vehicle banks and contains none of the weapon events, and
W-03 has no GUID at all. Whether the Vulcan the Batmobile will mount (B-06, not built) even uses
`weapons.bank` slot 408 is UNKNOWN — tune→wave is not stored (B11-06), so "through its slot" is a
name, not a route. (b) The payload itself is half silence and 3.5 % clipped, so even if a tune does
play it, the loop is wrong.

**Verdict: BROKEN** (as a delivered requirement; the card names the missing GUID as an open item but
counts W-03 among the five done swaps).

---

## 10. B11-10 — a swapped bank sample affects only the Batmobile

**Why the card rests on it.** Nothing in the card states the opposite; the build is presented as
"the Batmobile's sound". The outputs are two **whole-game** files.

**Test.**

```
$ grep -n "sound/fmod_banks/vehicles.bank" Research/JC3Grab/INDEX.jsonl
base  archives_win64/game1  offset 143159296  size 210803872
patch patch_win64/game5     offset 460482560  size 210781376
$ grep -n "sound/fmod_banks/weapons.bank" Research/JC3Grab/INDEX.jsonl
base  archives_win64/game0  offset 166060032  size 177586144
patch patch_win64/game6     offset 73531392   size 177586080
```

```
$ sed -n 10,14p Builds/bm-004/install.ps1
param(… [string]$GameDir = 'D:\Games\Just Cause 3')
$BankDir = Join-Path $GameDir 'dropzone\sound\fmod_banks'
```

The four vehicle samples are generic donor names, not Batmobile-specific:
`jc3_veh_door_tank_open_03`, `jc3_veh_door_tank_close_01` (the **tank** door pair),
`jc3_veh_land_premium_nitro_loop` (the premium-car nitro bed), and
`jc3_veh_lave_chassis_spin_creaks_loop_fast`. Replacing them in a global bank replaces them for
every vehicle whose tune uses those samples — every tank's door, every premium car's nitro, every
Lave chassis creak. How many that is cannot be decoded (0/257 tunes carry a wave GUID), which is
the point: the blast radius is **unknown**, not zero.

**Result.** The card's R7 framing ("private copies") protects the *vanilla file* but not the *game's
sound*: installing bm-004 is a global audio change made for one vehicle. Contrast B-09, where the
same class of issue (a shared module internalised in one entity's `.ee`) at least hit only the
entities that reference that module — here there is one bank for the whole game. The receipt and
§12 say nothing about it.

**Verdict: BROKEN (unstated), impact UNKNOWN.**

---

## 11. B11-11 — R7: the vanilla bank is never edited in place

**Test.**

```
vehicles built  210,781,376 B  sha 296c6cfe1a9af285   (manifest written[0])
vehicles source 210,781,376 B  sha 6161104d8909b7b0   (Working/Audio/jc3bank/…, unchanged)
weapons  built  177,586,080 B  sha 58e9db3e38f8124c   (manifest written[1])
install.ps1: backs up any existing bank to <name>.bm-004-backup before overwriting;
             Rollback091 restores it, or removes a bank this build added
```

The source hash is recomputed by the generator and recorded (`source_sha256`); no source file is
opened for writing anywhere in `bm_audio.py`.

**Result.** The build ships copies; the vanilla files are read-only inputs; the installer's backup
branch is real. R7 is kept for the file.

**Verdict: HOLDS.**

---

## 12. B11-12 — `Builds/bm-004/aaf` is bm-001's identity tree

**Test** (size + sha256 per file):

```
$ python  # walk both aaf trees
bm-001 files 590   bm-004 files 590
added []   removed []   changed []
```

**Result.** Byte-identical, 590/590.

**Verdict: HOLDS.**

---

## 13. B11-13 — `.ee.fmod_guids` is byte-identical, so no `.ee`/`.toc` edit is needed

**Test.** Compare the loose file in the build with the entry inside bm-001's `.ee`, and count:

```
Builds/bm-004/aaf/…/…civilian_01.ee.fmod_guids   758 B  sha 44ca5563…
Builds/bm-001/aaf/…/…civilian_01.ee.fmod_guids   758 B  sha 44ca5563…   identical bm-004 vs bm-001: True
inner entry in Builds/bm-001/<ee>: 758 B   equal to the loose copy: True
manifest: {"bytes": 758, "version": 1, "banks": ["vehicles","character","effects"], "count": 45}
mapped event GUIDs present in the 45: A-02/A-05/A-06/A-07 all True
```

**Result.** The file is the entity's own pin list, unchanged, and it contains the four events the
swaps sit under — so the "no `.ee`/`.toc` change is needed" conclusion is right *for the vehicle
events*. (It is also why nothing pins W-03: the list does not cover the weapons bank — B11-09.)

**Verdict: HOLDS.**

---

## 14. B11-14 — sample counts and file sizes unchanged

**Test.**

```
vehicles built  samples 649  bytes 210,781,376  sha 296c6cfe…  == manifest written[0]
vehicles source samples 649  bytes 210,781,376
weapons  built  samples 1228 bytes 177,586,080  sha 58e9db3e…  == manifest written[1]
slot data blocks: #7 59,968 B built / 59,968 B source, frames 29954/29954, name match
                  #98 49,920/49,920, #151 309,696/309,696, #279 672,032/672,032
all samples: 48 kHz, header mode PCM16 (2); 506 mono / 143 stereo (vehicles), 884/344 (weapons)
```

**Result.** Reproduced for vehicles against the in-repo source; for weapons only the built side can
be read (the source is `E:\Modding\JustCause3\_grab\...`, outside the repo). The "every donor sample is
16-bit PCM at 48 kHz" census holds for both banks.

**Verdict: HOLDS** for vehicles; **WEAK** for weapons (source unavailable here — a limitation, not a
finding).

---

## 15. B11-15 — the installer handles and rolls back the bank

**Test.** Read `install.ps1` end to end:

```
'Install'  DepBank vehicles.bank 296c6cfe… ; DepBank weapons.bank 58e9db3e…
           (existing bank → copy to .bm-004-backup unless already the pinned hash; then copy in
            and re-hash, throw on mismatch)
'Verify'   pins both hashes, throws on any difference
'Rollback091' UnBank both (restore backup, else remove "added by this build"),
              re-install test-091 only if $GameDir -eq 'D:\Games\Just Cause 3'
'Status'   prints both hashes + backup presence
```

Rehearsal artefacts remain in `tmp/b11/` (`runA`, `runC`, `runD`, `check.log`, `check.txt`,
`artifacts.sha`). The real dropzone bank hash quoted in MODLOG (`0bd0b2c6…`) is not re-checked here
(no reads outside the repo).

**Result.** The four actions the card names exist, the pins are the built files' hashes, and the
only branch that touches the real install is guarded by the `-GameDir` comparison. The recorded
rehearsals (Install → backup → Verify → Rollback restoring both bytes; Install into an empty dir →
Rollback removing both) match the code.

**Verdict: HOLDS.**

---

## 16. B11-16 — a loose bank overrides the archived one with no `.toc`

**Why the card rests on it.** Route a + c (`JC3_AUDIO.md` §10) says the bank is *"loaded as a loose
override at sound/fmod_banks/vehicles.bank with no .toc"*. If the engine instead prefers the
archive, the whole card ships nothing.

**Test.** The archives do carry both banks (§10 above), so this is not "a file the archives lack" —
it is an override. The only evidence is in-game: MODLOG §71 (test-060) replaced FSB5 payloads and
the bank was heard, and this card explicitly does not install or launch (R6). Nothing in the repo
lets me re-derive an engine load-order rule.

**Result.** The claim is single-sourced to a recorded in-game observation, and the card correctly
refuses to install. It is the one load-bearing fact that only a launch can settle — and the card's
Done 3 rehearses the *installer*, not the engine.

**Verdict: HOLDS** (recorded), with that caveat named.

---

## 17. What holds, and what the card should say instead

**Holds, and is well built:** the bank copies, the `.toc`-free install, the payload hashes, the FSB5
parse (649/1,228, 48 kHz PCM16), the 257/257 + 377/377 event/tune graph, the `.ee.fmod_guids`
identity, the identity tree, the installer's backup/rollback, and — better than claimed — the fact
that three of the five swaps are exactly as loud as the sample they replace.

**What the report should say instead of the current summary:**

1. **Say the slot length was forced.** Three of five payloads are truncated or zero-padded; two
   loops lose 44.5 % and 50 % of their loop to silence (#279, #408). Either pick slots whose length
   matches the source, loop the source to fill, crossfade, or record the padding as a known defect
   for V-04/Q-1. `padded_frames`/`trimmed_frames`/`clip_pct` are already in the manifest — put them
   in the §12 row and stop printing "0 clipped/padded".
2. **Say the loudness gate is mono.** Add the 2-channel measurement for stereo slots, or measure
   after replication, or state that only mono slots are level-matched. #408 currently ships ≈ 3 LU
   above its target.
3. **Say W-03 is a slot, not a sound.** No GUID, not in the `.fmod_guids`, no owning weapon entity
   yet (B-06), half silence. It should be `blocked`/`named omission` on the same footing as the 11
   named omissions, not one of the five delivered swaps.
4. **Say the banks are global.** The four swapped samples belong to tanks, premium cars and Lave
   chassis; installing bm-004 changes those for every vehicle whose tune uses them, and the number
   is UNKNOWN because tune→wave is not stored. That is a fleet-wide side effect of the same class as
   B-09's shared health module, and it belongs in §12 next to "private copies (R7)".

---

*Read-only pass; only this file was written. No game launch, nothing under `D:/Games`, no commit,
no secrets. Every number quoted is from this session except where the text says `[recorded]`.*
