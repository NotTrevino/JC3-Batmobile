# Sound regrab → swap slots — the JC3 carrier for each weapon and gadget cue

**STATUS: done (planning only, report only).** No file was written outside this report, no bank was built, no
script was added, no game was launched. Every carrier below is either an event GUID decoded from a JC3 entity or a
sample slot measured in `Working/Translation/T12_AUDIO.md`; where neither exists the row says so and names the
closest system and the exact missing capability.

Labels used in every row: **decoded** = read from the cited file/line, bank section or WAV header; **derived** =
computed from decoded facts with the rule stated; **UNKNOWN** = not established, with what was tried.

---

## 1. The nine sounds at a glance

| # | sound (BmAK role) | BmAK event · id · bank | new media in the regrab? | JC3 swap carrier | slot frames / s | plan |
|---|---|---|---|---|---|---|
| S1 | lock beep — **pursuit circle shrinking** | `Play_HUD_Missile_Lock` · `0x274D2DAA` · `UI_InGame` | **yes** — 2 WEMs, 0.3247 / 0.7575 s, mono | `weapons.bank` #381 `jc3_w143_fire_leach_target_lock` (idx0 380) | 6,400 / 0.1333 | trim 0.3247 → 0.1333 (keep 41 %), fade 2/8 ms |
| S2 | lock beep — **battle diamond** | `Play_Tank_Heavy_LockBeep` · `0x39553BB8` · `VEH_Tank_Heavy` | **yes** — 3 WEMs, 0.1832 / 0.4523 / 3.6330 s | `weapons.bank` #469 `jc3_wpn_minigun_endclick` | 8,081 / 0.1684 | trim 0.1832 → 0.1684 (keep 92 %), no loop |
| S3 | locked tone (diamond closes) | `Play_Tank_Heavy_Locked` · `0xEDFB1D8F` (+ `Stop_VEH_Tank_Heavy_Locked` `0x12D072C1`) | **yes** — 3 WEMs, 0.1832 / 0.4215 / 3.6330 s | `weapons.bank` #631 `jc3_wpn_tank_cannon_loaded_01` | 18,942 / 0.3946 | trim 0.4215 → 0.3946 (keep 94 %) |
| S4 | missile salvo | **none** — `RBatmobileMissile`/launcher bind no launch event in the grab (`Engine.Play_Batmobile_ApRocket_Fire`, missing-object) | **no** | `w618` fire event `84232d53-cea8-2d44-86a1-b92ff2402743` → #1047/#699/#561/#743 `jc3_wpn_missile_fire_01..04` + #1125 `…trail_rear_loop` | 65,031 / 62,712 / 62,860 / 72,142 / 145,641 | **no payload** — slots reserved, stock stays |
| S5 | EMP missile impact (the "Immobiliser" string) | `Play_Batmobile_Immobiliser_Impact` · `0xBD404E03` · `VFX_Tank_Explosion` | **yes** — 91 WEMs, 0.5310 – 6.1027 s | `effects.bank` `explosion` `d167a490-2252-4b4c-8662-8dcb27901f0c` (effects/464) | **UNKNOWN** — that bank's slots are not measured by T12 | swap impossible in a shared bank → **B-26** per-entity override |
| S6 | EMP burst (discharge at the car) | `Engine.Play_Batmobile_EMP` via `RVehicleWeapon.FireStartEvent` / `IndividualFireEvent`, **missing-object** | **no** | `effects.bank` `dynamic_break_electric` `77009170-11ad-a949-a478-f9358d245bb7` (effects/245) | **UNKNOWN** | no BmAK media exists; nothing to swap |
| S7 | tracker fire / tag | `Play_Disruptor_Vehicle_Tracking_Fire` · `0x8EA6FCA0` · `CHR_BatmanDisruptor` (+ `Play_Batmobile_Tracker_Deploy` · `0x4F380472`) | **yes** — 18 WEMs 0.2712 – 0.8595 s; deploy 1 WEM 0.8286 s | `weapons.bank` #150 `jc3_wpn_tank_cannon_loaded_02` (tag) and #468 `jc3_wpn_tank_cannon_loaded_unload_02` (deploy) | 21,629 / 0.4506 and 58,867 / 1.2264 | tag: trim ≤ 0.4506, pad shorter variants; deploy: pad 0.8286 → 1.2264 |
| S8 | sonar pulse | `Play_BML_Sonar_Pulse_Search` · `0x97CBF248` / `Pulse_Full` · `0xFFCC9813` · `BML_Sonar` | **yes** — 7 WEMs each, 0.0459 – 0.1863 s, 4–5 ch | **no uncontested slot** — closest is #381 (S1) | — | **deferred**: operator lead makes sonar the lowest-priority weapon |
| S9 | cannon fire + reload | `Engine.Play_BML_HeavyCannon_Fire` / `…_Reload` (member-bound, **missing-object**); vehicle-side `Fire` `ef8f8aaa-…` / `ReloadStart` `55051774-…` | **no** for the bound names | `weapons.bank` #847/#41 `jc3_wpn_mntd_tank_cannon_medium_01/02` (fire), #631/#150 `…loaded_01/02`, #923/#468 `…loaded_unload_01/02` | 81,701 / 68,764; 18,942 / 21,629; 66,812 / 58,867 | **no payload** — carriers named, stock stays |
| S10 | Vulcan spin + loop | `Play_Batmobile_MShot` `0x92AA4121` (resolved, `BML_Engine`, 5 WEMs) + `Engine.Play_Minigun_Fire` (FireLoopingEvent, missing-object) | **no new** (already resolved before this card) | `w619` `fire_sound_combi` `53e8d43a-0f09-434b-bf92-4239ffd243a8` → #408 loop, #559 barrel, #469 endclick | 160,337 / 92,901 / 8,081 | loop-tile #408 and #559 (T12 **zero-padded** them — see §5) |

Counting the request: **5 of the nine cues have usable new media** (S1, S2/S3, S5, S7, S8); **S4, S6 and S9 do
not**, because the events BmAK's own members point at are `missing-object` — they are not among the 350 events the
regrab extracted, and the ten claim banks do not contain them.

---

## 2. Sources, and what each one supplies

| source | what it gave this report | label |
|---|---|---|
| `tmp/freebuff/reports/bmak-banks-media-regrab.md` | 15 bank payloads, 350 events, 327 with media, 516 WEM/WAV; the per-event media table for the 26 ledger ids; the note that `Play_Tank_Heavy_LockBeep`/`Locked`/`Stop_*` **share one beep set** | decoded |
| `Research/BatmobileGrab/AUDIO_REGRAB.json` | per-event `event_id_hex`, `media[]` with `wem`, `wav_path`, `duplicate_of`; 619 event rows over 15 payloads | decoded |
| `Research/BatmobileGrab/WEAPONS.md` §… | which BmAK member fires each cue: `RBatmobileHeavyCannon.FireSound` (line 895), `RVehicleWeapon.ReloadSound` (919), the lock pair (920-924, 986-990), `FireLoopingEvent` = `Engine.Play_Minigun_Fire` (728/749), `FireStartEvent`/`IndividualFireEvent` = `Engine.Play_Batmobile_EMP` (801/802), `RBatmobileMissile.ExlposionSound` = `…Immobiliser_Impact` (168), tracker fire (1204) | decoded |
| `Research/BatmobileGrab/AUDIO_FEATURES.md` | group census (lock-on-ui 6 events / sonar 6 / tracker 2 / weapons 3); **"no AkEvent in the grab is an EMP sound"** (line 251); `Play_Batmobile_MShot` resolved in `BML_Engine` with 5 WEMs and RTPC `0x7D530EF5` 0→1, 0.5→0, 1→0 | decoded |
| `Working/Translation/T12_AUDIO.md` + `t12_audio_map.json` | the 34 measured slot candidates, 15 of them in `weapons.bank`, with frames/channels/LUFS/peak/`stretch_ratio`; the W-01…W-07 weapon rows; the rule that **event→tune is stored but tune→sample is not** | decoded |
| `Research/JC3Grab/JC3_AUDIO.md` §7 | the only weapon **event GUIDs** that are decoded: `w618` `fire`/`fire2..4` = `84232d53-…`, `w619` `fire_sound_combi` = `53e8d43a-…`; the medium tank `.epe` `Fire` = `ef8f8aaa-f95b-7846-9c25-f0c8f4bab301`, `ReloadStart` = `55051774-e5bc-7348-a20c-9a8fdd3dabe8`; `w602`/`w603` carry no sound at all | decoded |
| `tmp/freebuff/reports/jc3-community-writers-check.md` (c) | Fmod Bank Tools: payload swap only, duration-capped; `fmod_studio_F.dll` export list; "no FEV authoring without an `.fdp`" | decoded |
| `GRAB_BACKLOG.md` §8 B-26 (lines 1608-1625) | the per-entity audio override: 21 of 45 pinned GUIDs, `effects` 19 + `character` 2, shared banks cannot be swapped per car | decoded |
| `tmp/freebuff/reports/native-hook-design-jc3mp-contract.md` | the 26-entry address table (A1–A26) — **contains no audio symbol**; the whole design is spawn/input/HUD/oracle | decoded |

---

## 3. The swap rule set (what "swap in place" actually permits)

### 3.1 The length constraint

**Decoded, `tmp/freebuff/reports/jc3-community-writers-check.md` §1(c)**, quoting the Fmod Bank Tools README:

> "To rebuild the bank files, you will need to replace the wav files with your own that has the same file type,
> bitrate etc. **THE DURATION MUST BE SAME OR LESS THAN ORIGINAL AUDIO.**"

and, same section: "It also has a known bank-version/size failure mode (issue #13 … ). This is the same ceiling
B-11 already works under: **payload swap only**."

**Derived, and stricter than the tool's own wording:** our route is not the tool's rebuild, it is
`Tools/scripts/_apply_audio.py` writing the PCM **in place** — "a replacement must be PCM16/48 kHz and **exactly
the original frame count**" (`Research/JC3Grab/JC3_AUDIO.md` §10 route a, proven at test-060 on FSB5 indices
56/150/355). The FSB5 sample header and the offsets of every following sample stay untouched, so a shorter payload
is not allowed even though the community tool tolerates it.

Consequences that decide every row below:

| rule | value | label |
|---|---|---|
| encoding | 16-bit little-endian PCM, 48,000 Hz — all 34 measured slots | decoded (T12 slot table) |
| channels | the slot's own (mono slots 559/631/923/468/150/1125; stereo the rest) — a stereo source is downmixed before writing | decoded |
| frames | **exactly** the slot's frame count; shorter → zero-pad, longer → trim (T12 `stretch_ratio`) | derived |
| byte size | unchanged; the bank's `FSB5` sizes, `DIDX`/`DATA` offsets and the FEV graph are not touched | decoded |
| gain | `gain_db = slot_LUFS − delivered_LUFS`, gate ±1 LU (T12), applied **before** the PCM16 clip test | decoded (T12 method) |
| loop point | **no candidate carries an FSB5 loop field** — 0 of 34, not even the three slots whose names say
`loop` (T12 "Sample slots measured", closing note) — so a swap **cannot move a loop point** | decoded |

### 3.2 What cannot be done, and therefore is not planned

* **No new event, no new GUID.** The banks are FEV v56 b50 and no `.fdp` ships, so event authoring is blocked at
  the source (writers check §3.3). Every carrier below is an **existing** event or an **existing** sample slot.
* **No per-vehicle swap of `effects.bank` / `character.bank`.** 21 of the 45 donor GUIDs live there and the banks
  are shared by every vehicle in the game (keep-audit §3). That is exactly what **B-26** exists for, and it
  "**ships nothing in the release candidate**" (`GRAB_BACKLOG.md:1609`).
* **No repointing of a GUID.** B-26's own rule: "Do NOT rename or repoint a GUID: the events are code-fired and
  their names are not in the bank" (`GRAB_BACKLOG.md:1618`).

---

## 4. Per-sound plan

### S1 — lock beep, pursuit circle shrinking

* **BmAK (decoded).** `RVehicleWeapon.LockOnBeepSound` / `LockedOnSound` resolve to the `ww_veh_tank_heavy` pair on
  the heavy cannon (WEAPONS.md 920-924); the **pursuit** launcher's own cue is
  `RBatmobileMissileLauncher.LockOnSound` = `Engine.Play_RiotSuppressor_Select` (WEAPONS.md 1032) and the
  per-weapon `Engine.Play_Batmobile_ApRocket_Lock_Beep` (850-854) — both **missing-object**. The cue that the
  regrab actually delivered for this reticle is `Play_HUD_Missile_Lock` `0x274D2DAA` in `UI_InGame`, 2 WEMs:
  `0x232FC5F7` = 15,584 fr / 0.3247 s and `0x1D3788FA` = 36,359 fr / 0.7575 s, mono.
* **Derived pairing.** Pursuit mode is the missile-launcher mode (WPN-3), so its beep is the HUD missile-lock cue;
  battle mode is the cannon mode (WPN-1), so its beep is the `VEH_Tank_Heavy` pair. The reticle *shape* (circle vs
  diamond) is HUD-side and is **not** in either event — the pairing is by weapon, not by decoded field.
* **JC3 carrier (decoded).** `weapons.bank` sample #381 (index_0based 380) `jc3_w143_fire_leach_target_lock`,
  6,400 fr, 2 ch, **0.1333 s**, LUFS −14.02, peak −5.58 dBFS. It is the only lock-named sample among the 34
  measured slots and is already T12's single candidate for W-07. **The event that plays it is UNKNOWN** —
  `weapons.bank`'s `EVTS` names are not decoded by any card (T12 decodes the slot table for that bank only), and
  the sample is reached by name, not by the tune graph (tune→sample is not stored).
* **Trim plan.** Take the **short** source (`0x232FC5F7`, 0.3247 s), not the 0.7575 s one. Cut to 6,400 frames:
  keep the first 0.1333 s, apply a 2 ms fade-in and an 8 ms cosine fade-out so the truncation does not click
  (V-04's gate: "no click > −40 dBFS at the loop point" generalised to the tail). Keep 41 % of the source — the
  beep's attack and first tone survive, its second tone does not. **If the audition says the two-tone beep is
  essential, this slot cannot carry it** and S1 needs a longer ping slot (see §5).
* **Loop.** No — one-shot, and the slot has no loop field.

### S2 — lock beep, battle diamond

* **BmAK (decoded).** `Play_Tank_Heavy_LockBeep` `0x39553BB8`, `VEH_Tank_Heavy`, package `Startup`, 3 media:
  `0x1E31ACDB` 8,793 fr / **0.1832 s**, `0x1818E97F` 21,712 fr / 0.4523 s, `0x1764ACFD` 174,383 fr / 3.6330 s,
  all mono. `Stop_VEH_Tank_Heavy_LockBeep` `0x9279017E` = the 8,793-frame file.
* **JC3 carrier (decoded).** `weapons.bank` #469 (idx0 468) `jc3_wpn_minigun_endclick`, 8,081 fr, 2 ch,
  **0.1684 s**, LUFS −15.02, peak −0.10 dBFS. Chosen for duration fit, not for name: 8,793 → 8,081 frames is a
  **0.92 factor**, the closest fit in the bank to a 0.18 s beep.
* **Trim plan.** Trim 712 frames (14.8 ms) off the tail, 2 ms fade-in, 8 ms fade-out. No time-stretch: a 0.92
  ratio stretched (rather than trimmed) would raise pitch 8.7 %, audible on a pure beep.
* **Gain.** T12 already measured this slot: `gain_db −8.59`, `delivered −31.80 LUFS`, **Δ −16.78 LU — outside the
  ±1 LU gate** (T12 summary: "slots outside the ±1 LU gate … weapons#469"). A BmAK beep at −15 LUFS into a slot
  measured at −15.02 LUFS is near-perfect, so the −8.59 gain was computed for a *different* source and **must be
  recomputed** for this payload (rule: `slot − delivered`). Do not reuse T12's number.
* **Conflict.** #469 is one of W-03's three Vulcan candidates (the stop click). Taking it for the lock beep costs
  the Vulcan its end click — see §5.

### S3 — locked tone

* **BmAK (decoded).** `Play_Tank_Heavy_Locked` `0xEDFB1D8F`, 3 media: `0x1E31ACDB` (shared with the beep!),
  `0x35DC8DD2` 20,231 fr / **0.4215 s**, `0x1764ACFD` (shared). `Stop_VEH_Tank_Heavy_Locked` `0x12D072C1` = the
  3.633 s file. The regrab report notes the sharing explicitly: "the lock family reuses one beep set".
* **JC3 carrier (decoded).** `weapons.bank` #631 (idx0 630) `jc3_wpn_tank_cannon_loaded_01`, 18,942 fr, 1 ch,
  **0.3946 s**, LUFS −13.38, peak −0.03 dBFS. 20,231 → 18,942 frames = **0.94 factor**.
* **Trim plan.** Cut 1,289 frames (26.9 ms) from the tail; 2 ms in, 10 ms out. Because 0x1E31ACDB is shared with
  S2, the two payloads must be **different trims of two different media** (S2 uses 0x1E31ACDB, S3 uses 0x35DC8DD2)
  or the locked tone collapses into a second beep.
* **Loop.** No.

### S4 — missile salvo

* **BmAK (decoded).** No missile-launch event exists in the four vehicle packages: `AUDIO_FEATURES.md` weapons
  group is `Play_BatSniperRifle_Vehicle_Tracking_Fire`, `Play_Batmobile_MK2_MShot`, `Play_Batmobile_MShot` — three
  events, none a missile. The launcher's members that *would* be it are `missing-object`:
  `Engine.Play_Batmobile_ApRocket_Fire` (`RVehicleWeapon.IndividualFireEvent`, WEAPONS.md 864) and
  `Engine.Play_RiotSuppressor_Select` (LockOnSound, 1049). `Play_Batmobile_RocketTails` `0x6D02C4D5` (10 WEMs,
  1.3136 – 10.7530 s) is the **afterburner**, already used by A-02's nitro slots — it is not a missile.
* **JC3 carrier (decoded).** `w618`'s own `.ee.fmod_guids` binds `fire`/`fire2`/`fire3`/`fire4` to one GUID,
  `84232d53-cea8-2d44-86a1-b92ff2402743` (`JC3_AUDIO.md` §7). The four fire samples are the four slots a salvo
  rounds-robins through, **derived** (four `_fire_0N` variants in one bank, same family as the four `fire`
  attachment points on the `w618` `.epe` — G2-12 / `SIGNATURE_DIFF`: "4 type-2 fire points each paired by
  position with its muzzle"), and the loop behind the projectile is #1125:

  | slot | name | fr | ch | s | LUFS |
  |---:|---|---:|---:|---:|---:|
  | #1047 | `jc3_wpn_missile_fire_01` | 65,031 | 2 | 1.3548 | −6.05 |
  | #699 | `jc3_wpn_missile_fire_02` | 62,712 | 2 | 1.3065 | −6.89 |
  | #561 | `jc3_wpn_missile_fire_03` | 62,860 | 2 | 1.3096 | −5.72 |
  | #743 | `jc3_wpn_missile_fire_04` | 72,142 | 2 | 1.5030 | −5.27 |
  | #1125 | `jc3_wpn_missile_trail_rear_loop` | 145,641 | 1 | 3.0342 | −9.49 |

* **Plan.** Reserve all five. **Nothing is written** — there is no BmAK payload to write, so the stock salvo stays
  (T12 W-04 `named omission`, and this report does not overturn it).
* **Trim/loop if a payload ever arrives.** Fire variants: trim to each slot's exact count (the four counts differ
  by up to 9,430 frames, so one source needs four different trims). Trail: **loop-tile**, not pad (see §5).

### S5 — EMP missile impact (the "Immobiliser" string)

* **BmAK (decoded).** `Play_Batmobile_Immobiliser_Impact` `0xBD404E03`, `VFX_Tank_Explosion`, package `BmGame`,
  **91 media**, 0.5310 – 6.1027 s (first three: `0x22BEDC05` 25,486 fr mono 0.5310 s; `0x39F8A6CB` 32,249 fr 5 ch
  0.6719 s; `0x33650107` 36,155 fr 5 ch 0.7532 s). Bound by `RBatmobileMissile.ExlposionSound` (WEAPONS.md 168),
  resolved in all three Batmobile packages. This is the only cue in the request whose BmAK name carries the
  **"Immobiliser"** string; it shares 88 of its media ids with `Play_Batmobile_HeavyCannon_Explosion`, i.e. the
  bank reuses one explosion pool.
* **JC3 carrier (decoded).** `effects.bank` `explosion` `d167a490-2252-4b4c-8662-8dcb27901f0c`, bank ordinal
  `effects/464` — the exact same-meaning role (keep-audit's lore-exact list, and T12 A-15's carrier). **The sample
  slot behind that GUID is UNKNOWN**: T12 measures slots only for `vehicles.bank` and `weapons.bank`; `effects.bank`
  has 1,524 samples and no slot table exists in the repo.
* **Why no in-place copy works.** `effects.bank` is shared by every vehicle (`jc3-community-writers-check`; B-26's
  own text: "the 19 effects and 2 character GUIDs … cannot be replaced by a bank swap"). Swapping that slot would
  give every vehicle in JC3 the Batmobile's EMP impact.
* **Plan.** Carrier stays vanilla in RC4; the intended route is **B-26**: one `SAttachedEffect` /
  `SDynamicAttachedEffect` per entity pointing at a private `effects`-class bank, the GUID kept unchanged
  (`GRAB_BACKLOG.md:1614-1619`). B-26 currently "ships nothing in the release candidate" because "no private
  effects-class bank is bound". **Gap named, not accepted.**
* **Trim/loop if B-26 lands.** Pick the **2-channel** media (the mono `0x22BEDC05` would need an up-mix for a
  stereo slot); trim to the slot's count; no loop.

### S6 — EMP burst

* **BmAK (decoded, and negative).** On the EMP launcher, `RVehicleWeapon.FireStartEvent` **and**
  `IndividualFireEvent` both point at `Engine.Play_Batmobile_EMP` (WEAPONS.md 801-802, 813-814) — status
  **missing-object** in all packages. `AUDIO_FEATURES.md:251` states it flatly: **"no AkEvent in the grab is an EMP
  sound"**, and the `RBatmobileEMP` row in `WEAPONS.md:78` is a 3-package gadget with **0** audio-resolved members
  (the 34 audio members list, line 574, contains no `RBatmobileEMP.*` row other than `ImpulseComponent`, which is
  not audio).
* **Consequence.** The regrab did **not** deliver an EMP burst: there is no BmAK media for it to carry. Any row
  claiming an EMP burst swap would be inventing a source.
* **Closest JC3 system (decoded).** `effects.bank` `dynamic_break_electric` `77009170-11ad-a949-a478-f9358d245bb7`
  (`effects/245`) — the electric-crackle role keep-audit already nominates as the nearest for `Immobiliser_Impact`
  and which T12 keeps vanilla (A-19). No slot measured.
* **Plan.** Record as a **stated absence on the BmAK side** (source missing), not as a JC3 limit: the card that must
  produce it is the one that finds `Play_Batmobile_EMP`'s media (a bank outside the ten claim banks). Until then,
  nothing is swapped.

### S7 — tracker fire / tag

* **BmAK (decoded).** Two events, two jobs:
  * `Play_Batmobile_Tracker_Deploy` `0x4F380472`, `CHR_BatmanDisruptor`, **1 media**: `0x3F39B9FB`, 39,775 fr,
    1 ch, **0.8286 s** — the deploy/tag.
  * `Play_Disruptor_Vehicle_Tracking_Fire` `0x8EA6FCA0`, **18 media**, 0.2712 – 0.8595 s (mono and stereo mixed:
    `0x0CB90691` 13,017 fr mono 0.2712 s, `0x14B6D8B7` 16,239 fr 2 ch 0.3383 s, `0x3BB67FFD` 18,614 fr mono
    0.3878 s …) — the tracking shot.
  * The declared twin `0x6BB2C66E` (`Play_BatSniperRifle_Vehicle_Tracking_Fire`) is carried by **no bank**; the
    cooked twin is `0x8EA6FCA0` (regrab §5, oracle O-6 PASS). Use the cooked id.
* **JC3 carriers (decoded).**
  * tag/deploy → `weapons.bank` #468 `jc3_wpn_tank_cannon_loaded_unload_02`, 58,867 fr, 1 ch, **1.2264 s**,
    LUFS −19.83.
  * tracking fire → `weapons.bank` #150 `jc3_wpn_tank_cannon_loaded_02`, 21,629 fr, 1 ch, **0.4506 s**,
    LUFS −14.54.
  Both are **mono**, which matches the deploy media; the tracking-fire set mixes mono and stereo, so the stereo
  variants are downmixed (see §3.1).
* **Trim plan.**
  * deploy 0.8286 → 1.2264 s: **pad** 19,092 frames of silence (0.3978 s) after an 8 ms fade-out. Padding a
    one-shot is safe — the event fires once.
  * tracking fire: the 13,017/16,239/18,614-frame variants (≤ 0.3878 s) **fit under** 0.4506 s and are padded; the
    long variants (0.8595 s = 41,256 fr) must be trimmed to 21,629 fr (keep 52 %) or dropped in favour of a short
    variant. Recommendation: **use a short variant** rather than trim the long one — the bank gives 18 variants,
    so the fit exists without cutting.
* **Loop.** No.

### S8 — sonar pulse

* **BmAK (decoded).** `BML_Sonar`, package `BmGame`, 355,830 B, 7 HIRC events / 6 named:
  `Pulse_Search` `0x97CBF248` (7 media, 0.0459 – 0.1863 s), `Pulse_Full` `0xFFCC9813` (7 media, same span),
  `Rumble_Lp` `0x2A77A8B4` (3 media, 0.0676 – 0.0887 s, 4 ch), `Stop_Rumble_Lp` `0x835146BE`,
  `Turn_On` `0x02EE7381` / `Turn_Off` `0x265FE0CD` (22 media each, up to 0.1863 s for the pulse part and 3.9100 s
  for the longest). The media are **4–5 channel and very short** — they are Wwise multi-channel transients, not
  stereo beds.
* **What the pulse binds to (decoded).** `RBatmobileSonar.ScanSound` = `Ww_BML_Sonar.Play_BML_Sonar_Pulse_Search`,
  `BlastSound` = `…Pulse_Full`, `ChargeStart`/`Stop` = `Rumble_Lp`/`Stop_` (sonar report §1 table).
* **JC3 carrier.** There is **no sonar slot** among the 34 measured candidates, and no sonar role in any decoded
  `.epe` (sonar report: "there is no reveal/highlight carrier in JC3's vehicle data"). The closest slot by shape is
  **#381** (6,400 fr / 0.1333 s), the same one S1 needs.
* **Derived decision.** The operator lead in `sonar-and-scan-pulse.md` fixes the priority: the base sonar is the
  lowest-priority weapon in the ranking. So **the two lock beeps take #381-family slots and the sonar waits**; the
  gap is written as a new card, not as an accepted limit.
* **Plan if the sonar gets a slot.** Use `Pulse_Search` `0x97CBF248`, the **5-channel 0.1863 s** variant
  (`0x151497F7` 3,793 fr is the 0.079 s one; take the longest of the seven), downmix 5 → 2 ch, trim to the slot,
  10 ms fade-out. `Rumble_Lp`/`Turn_On` have **no** carrier at all (they are charge/scanner states with no JC3
  event to host them).

### S9 — cannon fire and reload

* **BmAK (decoded).** The heavy cannon's own members are `missing-object`:
  `RBatmobileHeavyCannon.FireSound` = `Engine.Play_BML_HeavyCannon_Fire` (WEAPONS.md 895, 939, 958, 1003),
  `RVehicleWeapon.ReloadSound` = `Engine.Play_BML_HeavyCannon_Reload` (919, 940), with
  `ReloadSoundDuration` **0.4 s** on the Batmobile/MK2 and **0.5 s** on the Joker (925, 991). Neither event is in
  the regrab's 350.
  The `VEH_Tank_Heavy` bank that *was* decoded holds 41 events / 40 media — 8 of them carry 34 media ids and 2
  carry 12 — but only 4 are named (the lock family) and **no decoded field says which of the other 37 is cannon
  fire vs reload** (the bank stores no event names, `JC3_AUDIO.md` §1). So "the cannon sound is in the regrab" is
  **not** established.
* **JC3 carriers (decoded).** Two layers, both in `weapons.bank`, both already T12 rows:

  | layer | event | slots | fr | s |
  |---|---|---|---:|---:|
  | muzzle/fire | medium tank `.epe` `Fire` = `ef8f8aaa-f95b-7846-9c25-f0c8f4bab301` | #847 `…mntd_tank_cannon_medium_01`, #41 `…_02` | 81,701 / 68,764 | 1.7021 / 1.4326 |
  | loaded (one-shot click) | same `Fire` graph | #631 `…tank_cannon_loaded_01`, #150 `…_02` | 18,942 / 21,629 | 0.3946 / 0.4506 |
  | reload/unload | `ReloadStart` = `55051774-e5bc-7348-a20c-9a8fdd3dabe8` | #923 `…loaded_unload_01`, #468 `…_02` | 66,812 / 58,867 | 1.3919 / 1.2264 |

* **Trim plan (when a payload exists).** The two fire variants are reloaded at the same event, so they must be
  trimmed to **their own** counts (81,701 vs 68,764 — a 12,937-frame difference); a single trim cannot fill both.
  Reload: 66,812 and 58,867 frames for a 0.4 s (19,200 fr) BmAK reload — the slot is **3.5× longer than the
  reload duration the donor itself declares**, so the payload must be padded ~2.3 s or the slot left stock. That is
  a real mismatch to record: the JC3 reload sample is a 1.2–1.4 s mechanical sequence, the BmAK reload is a 0.4 s
  click.
* **Plan.** No payload → stock stays (T12 W-05/W-06 `named omission`), carriers named as above.

### S10 — Vulcan spin and loop

* **BmAK (decoded).** `Play_Batmobile_MShot` `0x92AA4121`, resolved in `BML_Engine`, 5 WEMs
  (`0x180D3398`, `0x098BBFE1`, `0x209CCD2A`, `0x0A276ED9`, `0x341AA130`), container `random-sequence` + `sound`,
  RTPC `0x7D530EF5` 0→1, 0.5→0, 1→0. The *looping* member is separate and missing:
  `RVehicleWeapon.FireLoopingEvent` = `Engine.Play_Minigun_Fire` (728, 749), combo = `Play_Minigun_Combo_Fire`,
  overheat/cooled = `Play_Minigun_Overheat`/`Play_Minigun_Cooled` — all **missing-object**. So BmAK's spin-up is not a decoded
  asset; the MShot set is the fire one-shot T12 already mapped.
* **JC3 carriers (decoded).** `w619` `fire_sound_combi` = `53e8d43a-0f09-434b-bf92-4239ffd243a8`:

  | slot | name | fr | ch | s | T12 gain | T12 Δ LU |
  |---:|---|---:|---:|---:|---:|---:|
  | #408 | `jc3_wpn_minigun_fire_close_loop_04` | 160,337 | 2 | 3.3404 | +1.13 | −0.57 |
  | #559 | `jc3_wpn_minigun_barrel_motor_loop` | 92,901 | 1 | 1.9354 | −6.92 | −0.32 |
  | #469 | `jc3_wpn_minigun_endclick` | 8,081 | 2 | 0.1684 | −8.59 | −16.78 |

* **Loop plan (the important part).** T12's `stretch_ratio` for these two slots is **2.0011** and **1.1595**, i.e.
  the MShot payload was **zero-padded** to reach the slot length. For a slot whose name says *loop* that is wrong:
  half of #408 (1.67 s of 3.34 s) is silence, so the loop clicks in and out of silence every cycle. The correct
  plan for **#408 and #559** is:
  1. downmix the MShot WEM to the slot's channel count (2 ch for #408, mono for #559);
  2. **tile** the burst — repeat it whole — until the accumulated length ≥ slot frames, then cut at exactly
     160,337 / 92,901 frames. Never cut mid-transient: choose the tile boundary at the burst's quietest 10 ms;
  3. crossfade the **seam** (last 10 ms of tile *n* against the first 10 ms of tile *n+1*) and, for the payload's
     end→start seam, make sample 0 and sample N−1 continuous (equal-phase crossfade) — the slot has **no loop
     field** to move, so the seam has to be baked in;
  4. gate: no discontinuity > −40 dBFS at the seam (V-04's own rule).
* **#469 (end click).** If S2 takes #469 for the battle beep, the Vulcan loses its stop click. The end click is
  already the worst slot in the bank (Δ −16.78 LU, gain −8.59), so it is the cheapest of the three to lose — but
  the loss must be recorded, not silently taken.

---

## 5. Slot budget — where the demand exceeds the supply

The measured `weapons.bank` candidate set is **15 slots** (T12 §"Sample slots measured"). The request touches 12
of them, and three of those are wanted by two sounds each.

| slot | stock identity | wanted by | T12 status | this report |
|---:|---|---|---|---|
| #381 | leach target lock, 0.1333 s | S1, S8 | W-07 candidate | **S1** (sonar deferred) |
| #469 | minigun end click, 0.1684 s | S2, S10 | W-03 candidate | **S2** |
| #631 | tank cannon loaded 01, 0.3946 s | S3, S9 | W-01 candidate | **S3** |
| #150 | tank cannon loaded 02, 0.4506 s | S7, S9 | W-01/W-05 candidate | **S7 (tag)** |
| #468 | tank cannon loaded/unload 02, 1.2264 s | S7, S9 | W-06 candidate | **S7 (deploy)** |
| #923 | tank cannon loaded/unload 01, 1.3919 s | S9 | W-06 candidate | S9 (reserved, no payload) |
| #847 / #41 | tank cannon medium 01 / 02 | S9 | W-01 candidate | S9 (reserved, no payload) |
| #408 / #559 | minigun fire loop / barrel motor | S10 | **W-03 `mapped`** (chosen: #408) | S10 (loop-tiled) |
| #1047/#699/#561/#743 | missile fire 01–04 | S4 | W-04 candidates | S4 (reserved, no payload) |
| #1125 | missile trail rear loop | S4 | W-04 candidate | S4 (reserved, no payload) |

**Derived conclusion.** Eleven distinct short/medium slots are demanded by nine sounds; only a subset can ship
because each sound needs its own identity. The two structural gaps this exposes:

1. **One short UI slot is one too few.** S1 and S8 both want the only lock/ping-shaped slot. Priority resolves it
   (lock beeps first, sonar is the lowest-ranked weapon), but the sonar's pulse then has **no** carrier.
2. **Closing either gap needs a capability that does not exist in the repo:** an FSB5 **add-sample** writer
   (`jc3-community-writers-check` §3.3: "new events and new samples" is the open gap; RB-8's recommendation stands)
   or B-26's per-entity private bank. Neither may be assumed here.

---

## 6. Which sounds the native hook could play directly instead

**The condition in the brief is not met: the design report finds no audio entry point.**

* `tmp/freebuff/reports/native-hook-design-jc3mp-contract.md` (identical twin:
  `jc3mp-native-hooks-design.md`) is the design report. Its §1 verdict table has rows for RB-4, RB-5, RB-6, RB-7,
  RB-9 and the handling switch; **there is no audio row**, and the §4 address table **A1–A26** contains
  `CSpawnSystem`, the event runner, the flip call site, `CGraphicsEngine`, `CInputDeviceManager`, `CUIManager`,
  `CDebugRenderer`, `CClock`, the player chain, the aim position, the build gate, the HWND, the game state — and
  **not one `fmod`/`FMOD` symbol**. The §9 UNKNOWN list does not mention audio either. **Decoded by reading the
  table.**
* The only FMOD evidence in the repo is the binary survey in `jc3-community-writers-check.md` §1(c), read-only
  from `D:/Games/Just Cause 3/fmod_studio_F.dll` (5,230,592 B, 2017-02-04):

  > "exports include `FMOD_Studio_System_Create`, `FMOD_Studio_EventDescription_Create`, `FMOD_System_Create` (the
  > Studio 1.x API); strings: `FMOD Studio` ×2, `FMOD Ex` ×0, `FSB4`, `FSB5`, `FSBANK`; **no `EventSystem_Create`
  > export** (the FMOD Ex/Designer API) was found."

  and the derived caveat: "the shipped runtime is **FMOD Studio 1.x**, while the shipped *data* is FEV v56. How a
  Studio runtime consumes an FEV event bank is **UNKNOWN**".

* Note the newer correction in the same repo: the earlier claim that JC3 is "FMOD Studio" was marked as a guess
  and the bank bytes are FEV (`MODLOG.md:11641`). So we have a Studio-shaped DLL and Designer-shaped data, and
  **nothing decoded bridges them**.

**Therefore: no sound in this request can be claimed playable directly today.** What would make it possible, and in
what order:

| step | what it would establish | status |
|---|---|---|
| 1. `grep -a -o "FMOD_Studio_[A-Za-z_]*\|EventSystem_Create" JustCause3.exe` | whether the **EXE** (not just the DLL) imports the Studio API — the one-minute test already proposed as E-c(i) in the writers check, **not yet run** | not run (out of scope: read-only survey, no launch) |
| 2. `GetProcAddress` on `fmod_studio_F.dll` for `FMOD_Studio_System_Create` + find the engine's **system handle** | whether a second/private event system can be created inside the process | UNKNOWN — the handle is a global no card has located |
| 3. bank-load path | whether a private **Studio** bank (buildable in FMOD Studio, unlike an FEV) can be loaded and played alongside the game's FEV banks | UNKNOWN — no Studio bank ships, and JC3 reads `sound/fmod_banks/*.bank` + `master.banklist` |

If step 1 and 2 land, the cues that suit **direct playback** are the graph-free one-shots, because they need no
tune, no RTPC and no 3D attenuation the game already applies:

| sound | fits direct play? | why |
|---|---|---|
| S1 pursuit lock beep | **best candidate** | 0.32 s mono one-shot, UI (2D), no RTPC on `Play_HUD_Missile_Lock` (none decoded) |
| S2/S3 battle beep + locked | best candidate | 0.18 / 0.42 s mono one-shots, no RTPC |
| S6 EMP burst | candidate **if** a source is ever found | one-shot |
| S7 tracker deploy/tag | candidate | 0.83 s / 0.27-0.86 s one-shots (the deploy is mono, the fire set has 4–5 ch variants to downmix) |
| S8 sonar pulse | candidate | 0.19 s transient; **but** it is a 4–5 ch Wwise file, so it would need the downmix done by us either way |
| S5 EMP impact | **poor** | 91 variants, 0.5–6.1 s, 5-channel; the event's attenuation and the explosion mix are the tune graph's |
| S9 cannon fire/reload | **poor** | the stock gun's event already carries the 3D position and the muzzle; a direct 2D play would detach the sound from the gun |
| S10 Vulcan loop + spin | **poor** | needs a looping voice plus the barrel spin's pitch/loop behaviour — exactly what `FireLoopingEvent`'s graph does |
| S4 missile salvo + trail | **poor** | the trail is a 3 s loop attached to the projectile |

So even in the best case the hook replaces the **short UI one-shots** (S1, S2, S3, S7, S8) and leaves the
weapon-fixture sounds (S4, S5, S9, S10) on the bank-swap route — which is the opposite of what a "play it directly"
plan would be chosen for. **Report only: nothing here is claimed, and no code was written.**

---

## 7. UNKNOWNs

1. **The event that plays each `weapons.bank` sample.** T12 stores event→tune and proves tune→sample is not
   stored (0 / 649); `weapons.bank`'s `EVTS` names were never decoded. Tried: `JC3_AUDIO_EVENTS.json` (45 donor
   events only, all `vehicles`/`character`/`effects`), `T12_AUDIO.md` W-rows (slot names only),
   `JC3_AUDIO.md` §7 (`w618`/`w619` GUIDs only). Where it would be found: an `EVTS` name table (absent) or the
   weapon `.epe` `SAttachedEffect` bindings for the other carriers.
2. **Which of `VEH_Tank_Heavy`'s 37 unnamed events is cannon fire vs reload.** The bank stores no event names
   (`JC3_AUDIO.md` §1: "the body starts with the 16-byte event GUID, no name string"). Tried: `AUDIO_MAP.json`
   (only 4 of 41 named), `AUDIO_REGRAB.json` (`event_name: null` for the rest). Where: a Wwise `SoundbanksInfo`
   manifest (absent) or audition of the 34-media families.
3. **The slot index behind `effects.bank`'s `explosion` (`effects/464`) and `dynamic_break_electric`
   (`effects/245`).** T12 measures `vehicles` + `weapons` slots only. Tried: `t12_audio_map.json` `slots` (34 rows,
   none in `effects`). Where: an `effects.bank` slot census (1,524 samples) — a measurement pass, not a decode gap.
4. **Whether the two lock beeps are the circle and the diamond.** Derived from which weapon each is bound to
   (pursuit = missile launcher, battle = heavy cannon); no decoded HUD field names the reticle shape per event.
   Where: `Working/HUD/` reticle documents plus an in-game audition (Q-1), which the test ban forbids.
5. **Whether a `weapons.bank` swap is loaded from the dropzone.** Route c is asserted from the bank's own size/name
   table (`JC3_AUDIO.md` §10), but no test has installed a modified `weapons.bank`; only `vehicles.bank` was
   proven (test-060). UNKNOWN pending Q-1.
6. **Whether `fmod_studio_F.dll` is the consumer of the FEV banks** (see §6). Where: the EXE import table.
7. **The perceived result of every trim in §4.** No listening was done (the regrab's own UNKNOWN 3: "the file level
   only … no judgement that a cue is the 'right' lock beep"). All trims are arithmetic, gated by V-04.

---

## 8. COMPROMISES

None accepted. The three rows without a payload (S4 missile salvo, S6 EMP burst, S9 cannon fire/reload) are
recorded as **BmAK-side absences** with the exact member names that point outside the regrab, and the one row
without a free slot (S8 sonar) is deferred by the operator's own priority lead, not dropped. The EMP impact (S5)
has a payload but no legal carrier inside a shared bank; that is written as B-26's gap ("no private effects-class
bank is bound"), not as a JC3 limit.

---

## 9. Commands run for this report (verbatim)

```
$ python - <<'EOF'   # event names per regrab bank (AUDIO_REGRAB.json)
... print(e['bank'], e['event_id_hex'], e.get('event_name'), media count)
EOF
## BML_Batmobile_Subjective 4   Play_Batmobile_Jump_Land / _PreJump / _PreLand / _Wind
## BML_Impacts 1                Play_Batmobile_Destroyed
## BML_Sonar 6                  Play_BML_Sonar_Pulse_Full / Pulse_Search / Rumble_Lp / Turn_Off / Turn_On / Stop_Rumble_Lp
## CHR_BatmanAlerts 1           Play_HUD_fail
## CHR_BatmanDisruptor 1        Play_Batmobile_Tracker_Deploy
## UI_InGame 1                  Play_HUD_Missile_Lock
## VEH_Tank_Heavy 4             Play_Tank_Heavy_LockBeep / Locked / Stop_LockBeep / Stop_Locked
## VEH_Tank_Missiles 2          Play_Batmobile_RocketTails / Stop_
## VFX_Tank_Explosion 4         Play_Batmobile_HeavyCannon_Explosion / Immobiliser_Impact / Play_Explosion_2D / Barrage_Sweetener

$ python - <<'EOF'   # slot table, weapons bank (t12_audio_map.json)
EOF
41  jc3_wpn_mntd_tank_cannon_medium_02   68764 2  41/847 both candidate
150 jc3_wpn_tank_cannon_loaded_02        21629 1
381 jc3_w143_fire_leach_target_lock       6400 2
408 jc3_wpn_minigun_fire_close_loop_04  160337 2  chosen=True (W-03)
468 jc3_wpn_tank_cannon_loaded_unload_02 58867 1
469 jc3_wpn_minigun_endclick               8081 2
559 jc3_wpn_minigun_barrel_motor_loop    92901 1
561 jc3_wpn_missile_fire_03              62860 2
631 jc3_wpn_tank_cannon_loaded_01        18942 1
699 jc3_wpn_missile_fire_02              62712 2
743 jc3_wpn_missile_fire_04              72142 2
847 jc3_wpn_mntd_tank_cannon_medium_01   81701 2
923 jc3_wpn_tank_cannon_loaded_unload_01 66812 1
1047 jc3_wpn_missile_fire_01             65031 2
1125 jc3_wpn_missile_trail_rear_loop    145641 1

$ python - <<'EOF'   # media durations per event, from wav_path headers
EOF
Play_Tank_Heavy_LockBeep              VEH_Tank_Heavy       0x39553BB8 media=  3  dur 0.1832..3.6330 s
Play_Tank_Heavy_Locked                VEH_Tank_Heavy       0xEDFB1D8F media=  3  dur 0.1832..3.6330 s
Stop_VEH_Tank_Heavy_LockBeep          VEH_Tank_Heavy       0x9279017E media=  1  dur 0.1832..0.1832 s
Stop_VEH_Tank_Heavy_Locked            VEH_Tank_Heavy       0x12D072C1 media=  1  dur 3.6330..3.6330 s
Play_HUD_Missile_Lock                 UI_InGame            0x274D2DAA media=  2  dur 0.3247..0.7575 s
Play_BML_Sonar_Pulse_Search           BML_Sonar            0x97CBF248 media=  7  dur 0.0459..0.1863 s
Play_BML_Sonar_Pulse_Full             BML_Sonar            0xFFCC9813 media=  7  dur 0.0459..0.1863 s
Play_BML_Sonar_Rumble_Lp              BML_Sonar            0x2A77A8B4 media=  3  dur 0.0676..0.0887 s
Stop_BML_Sonar_Rumble_Lp              BML_Sonar            0x835146BE media=  3  dur 0.0676..0.0887 s
Play_BML_Sonar_Turn_On                BML_Sonar            0x02EE7381 media= 22  dur 0.0459..3.9100 s
Play_BML_Sonar_Turn_Off               BML_Sonar            0x265FE0CD media= 22  dur 0.0459..3.9100 s
Play_Batmobile_Tracker_Deploy         CHR_BatmanDisruptor  0x4F380472 media=  1  dur 0.8286..0.8286 s
Play_Disruptor_Vehicle_Tracking_Fire  CHR_BatmanDisruptor  0x8EA6FCA0 media= 18  dur 0.2712..0.8595 s
Play_Batmobile_Immobiliser_Impact     VFX_Tank_Explosion   0xBD404E03 media= 91  dur 0.5310..6.1027 s
Play_Batmobile_HeavyCannon_Explosion  VFX_Tank_Explosion   0xDD424156 media= 88  dur 0.5310..6.1027 s
Play_Batmobile_RocketTails            VEH_Tank_Missiles    0x6D02C4D5 media= 10  dur 1.3136..10.7530 s
Stop_Batmobile_RocketTails            VEH_Tank_Missiles    0x4334B8A3 media=  5  dur 5.8554..10.7530 s

$ grep -n "FireLoopingEvent|FireStartEvent|IndividualFireEvent|ReloadSound|LockOnBeepSound|LockedOnSound|FireSound|UntagWarningEvent" Research/BatmobileGrab/WEAPONS.md
895:| `RBatmobileHeavyCannon.FireSound` | 0x0984 | ObjectNCRProperty | `Engine.Play_BML_HeavyCannon_Fire` |
919:| `RVehicleWeapon.ReloadSound` | 0x08A0 | ObjectNCRProperty | `Engine.Play_BML_HeavyCannon_Reload` |
920:| `RVehicleWeapon.LockOnBeepSound` | 0x08C8 | ObjectNCRProperty | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` |
922:| `RVehicleWeapon.LockedOnSound` | 0x08D8 | ObjectNCRProperty | `ww_veh_tank_heavy.Play_Tank_Heavy_Locked` |
925:| `RVehicleWeapon.ReloadSoundDuration` | 0x08F0 | FloatProperty | 0.4000000059604645 |
941:| `RVehicleWeapon.LockOnBeepSound` | `ww_veh_tank_heavy.Play_Tank_Heavy_LockBeep` | AkEvent | resolved |
801:| `RVehicleWeapon.FireStartEvent` | 0x0880 | ObjectNCRProperty | `Engine.Play_Batmobile_EMP` |
802:| `RVehicleWeapon.IndividualFireEvent` | 0x0898 | ObjectNCRProperty | `Engine.Play_Batmobile_EMP` |
728:| `RVehicleWeapon.FireLoopingEvent` | 0x0890 | ObjectNCRProperty | `Engine.Play_Minigun_Fire` |
168:| `RBatmobileMissile.ExlposionSound` | `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` | AkEvent | resolved |

$ grep -rn "FMOD_Studio_System_Create|EventSystem_Create" tmp/freebuff/reports/*.md Research/JC3Grab/*.md
tmp/freebuff/reports/jc3-community-writers-check.md:148:- exports include `FMOD_Studio_System_Create`, `FMOD_Studio_EventDescription_Create`, `FMOD_System_Create`
tmp/freebuff/reports/jc3-community-writers-check.md:151:- no `EventSystem_Create` export (the FMOD Ex/Designer API) was found.
tmp/freebuff/reports/jc3-community-writers-check.md:319:(i) `grep -a -o "FMOD_Studio_[A-Za-z_]*\|EventSystem_Create" JustCause3.exe` — **not run**
```

**Files written:** this report only.
