# Independent review — card B-11 · Audio bank (read-only)

Reviewer pass over a card this agent did not write. Scope read: `GRAB_BACKLOG.md` §0.5 (R1–R14,
lines 59–76), the B-11 card (§8, lines 1074–1080), the §12 `B-11` row (line 1340); MODLOG
`## B-11 · Audio bank — done (2026-10-31)` (line 17469) and `## B-11 · done — independent
verification (2026-10-31)` (line 17615); outputs `Tools/scripts/bm_audio.py` (686 lines),
`Working/Audio/bm_bank_manifest.json`, `Builds/bm-004/{receipt.json, install.ps1, banks/, aaf/}`,
the card's spec doc `Research/specs/B-11.md`, and input doc `Research/JC3Grab/JC3_AUDIO.md` §10
(route claim). Nothing was edited; no game launch, no install, no commit, no secrets. Tamper
tests and installer rehearsals were **not** re-run (read-only mandate: only this file was written).

## VERDICT: minor issues

The build is real and green: every `Out:` path exists, `--check` re-derives everything from the
T-16 map and passes on the artefacts on disk, and every number I spot-checked ties back to the
map, the manifest or the raw files. The card's two data Done criteria (event resolution, sample
count/lengths) are genuinely enforced by `--check`. The findings below are wording/evidence gaps,
not fabricated results.

## Check output (verbatim)

Command: `python Tools/scripts/bm_audio.py --check`

```
PASS: 5 mapped rows, 5 slots in 2 banks (1877 samples), 5 events resolved, max LU delta 0.00 <= 0.05 | banks vehicles 210,781,376 B, weapons 177,586,080 B (size unchanged True) | .ee.fmod_guids 758 B, 45 GUIDs | installer 2 bank(s) + rollback
EXIT=0
```

Byte-for-byte identical to the `PASS` line quoted in MODLOG line 17497 and in
`Research/specs/B-11.md` §3. (First run of this review; the tree was quiet — no sibling-lane race
during this pass.)

### Out paths / evidence named in the row

| named in §12 row or card `Out:` | exists | size |
|---|---|---|
| `Working/Audio/bm_bank_manifest.json` | yes | 134,347 B |
| `Builds/bm-004/receipt.json` | yes | 9,112 B |
| `Builds/bm-004/install.ps1` | yes | 4,497 B |
| `Builds/bm-004/banks/vehicles.bank` | yes | 210,781,376 B |
| `Builds/bm-004/banks/weapons.bank` | yes | 177,586,080 B |
| `Builds/bm-004/aaf` (identity tree) | yes | 590 files, 22,011,703 B |
| `Tools/scripts/bm_audio.py --check` | yes, exit 0 | — |
| MODLOG §"B-11 · Audio bank — done" | yes, line 17469 | — |
| `Research/JC3Grab/JC3_AUDIO.md` §10 (route source) | yes, line 222 "Ship routes", route b = **no**, recommendation "route a + c" | — |

### Done criterion vs what `--check` actually verifies

| card Done criterion | enforced by `--check`? | where |
|---|---|---|
| 1 — every mapped event resolves | **yes.** `build()` raises if any mapped row fails to resolve (bm_audio.py:374-386); `check()` re-reads the written banks and asserts each GUID is in `EVTS` and `TLNB` (bm_audio.py:593-603); the guid-less W-03 row's slot is covered by the name/frames assertions (bm_audio.py:571-581) |
| 2 — sample count/lengths match the manifest | **yes.** manifest byte-compared to the re-derived record (bm_audio.py:631-636), sample count re-read from each written bank with `fsb5`, per-slot frames/name/duration re-read with vgmstream, payload bytes re-hashed against `payload_sha256` (bm_audio.py:557-591) |
| 3 — the installer handles and rolls back the bank | **no.** `check()` only compares `install.ps1` text to the regenerated text, the four action names and the two bank pins (bm_audio.py:604-618). The install/backup/verify/rollback behaviour is evidenced solely by the offline rehearsals quoted in MODLOG (C1–C5, D1–D3) — real, but not re-runnable from `--check` (see issue 2) |

## Issues

**1. §12 row: "0 clipped/padded where the map says so" is at best ambiguous, at worst false**
- File/line: `GRAB_BACKLOG.md:1340` (B-11 row), clause `each payload re-measured as the map measured it, **max LU delta 0.00 ≤ 0.05** and 0 clipped/padded where the map says so`.
- The manifest's own `measured` block contradicts the literal reading ("nothing clipped, nothing
  padded"): `A-02 vehicles #151 clip_pct 0.1`; `W-03 weapons #408 clip_pct 3.53, padded_frames
  80,213`; `A-05 vehicles #279 padded_frames 149,503`.
- The charitable reading — "0 *difference* vs the map's clip/pad figures" — is true: for all five
  slots `manifest.measured` equals the map's `clip_pct`/`padded_frames`/`trimmed_frames`
  exactly (verified against `Working/Translation/t12_audio_map.json` chosen slots).
- Why it matters: a reader takes the clause as a measured quality claim (R4: no value without
  provenance — as written it does not say what is 0). Also relevant to R11 readers: the claim does
  not appear in `--check` output at all, so it is a typed value in a row of counts. Fix = reword to
  "clip/pad figures equal the map's (delta 0)".

**2. Spec doc claims `--check` proves all three Done criteria; it proves two**
- File/line: `Research/specs/B-11.md:121` — `python Tools/scripts/bm_audio.py --check     # all three Done criteria on the artefacts on disk`.
- `--check` never executes `install.ps1` (bm_audio.py `check()`, lines 551-641: text equality,
  action names, pins only). Done 3 is proven by the recorded PowerShell rehearsals in MODLOG
  (lines 17560-17600), which need a manual re-run to re-verify.
- Why it matters: the reproduction section tells the next reader that one command re-checks
  rollback behaviour; it does not. Fix = point criterion 3 at the rehearsal steps (as §3 of the
  same doc already does correctly).

**3. `receipt.json` is row evidence but is never validated by `--check`**
- File: `Tools/scripts/bm_audio.py` — written at lines 664-675, never read in `check()`
  (551-641); the §12 row lists `Builds/bm-004/receipt.json` first among its evidence.
- Why it matters: a stale or tampered receipt (bank sizes, shas, `installed: false`) would leave
  `--check` green, so the receipt's numbers are not regenerated/compared the way the manifest's
  are. Current receipt is consistent (spot-check 6), so this is a coverage gap, not a wrong value.

**4. PASS line says "5 events resolved" although only 4 rows have an event**
- File/line: `Tools/scripts/bm_audio.py:629` (`{s['resolved']} events resolved`); manifest
  `summary.resolved = 5`.
- W-03's resolution is "the sample with that name exists in the bank" (bm_audio.py:383-385) —
  name presence, not an event resolving. Under R5 (behaviour before member/name) a sample name in
  an FSB5 table is not the behaviour "the event resolves".
- Mitigation (why this stays *minor*): it is disclosed in the manifest (`"note": "weapon row:
  resolves through its slot, not a donor GUID"`), in MODLOG ("a mapped event that silently
  'resolved' through a GUID it does not have would be a lie"), and in the §12 row ("W-03 through
  its slot, no donor GUID by T-11"). Nothing is hidden; only the summary word over-reaches.

**5. Claims not re-verifiable in this read-only pass (recorded, not held against the card)**
- The 5/5 tamper tests and both installer rehearsals (MODLOG, spec §3) were not re-run — doing so
  would require writing to `Builds/bm-004/` or running PowerShell, outside a read-only review.
- Statements about the real game directory (`D:\Games` bank still `0bd0b2c6…`, mtime
  2026-10-14) were not inspected — the game install is outside this project folder.

No other R4/R5 problems found: every `UNKNOWN` is declared instead of guessed (`tune→sample`
UNKNOWN, W-03 has no donor GUID, loudness gate deferred to V-04); the route claim (no `.fev`
project ships → payload swap in a private copy) matches `JC3_AUDIO.md` §10; both source banks are
untouched (R7, spot-check 5); source banks and build banks are gitignored, so no game file is
tracked (R10); MODLOG carries both the done entry and an independent verification entry (R14).

## Spot-checks

| # | value in doc/row/MODLOG | where verified | result |
|---|---|---|---|
| 1 | `vehicles.bank #151 jc3_veh_land_premium_nitro_loop` **154,818 frames** (§12 row, MODLOG table) | `t12_audio_map.json` chosen slot `frames: 154818` == manifest `slots[].frames 154818` == independent `fsb5` read of `Builds/bm-004/banks/vehicles.bank` sample 151 (`frames 154818`); `--check` also re-reads it via vgmstream | MATCH |
| 2 | bank sizes/shas: **210,781,376 B `296c6cfe…`**, **177,586,080 B `58e9db3e…`** (§12 row, MODLOG, receipt) | `sha256sum`/`stat` on `Builds/bm-004/banks/*.bank`: `296c6cfe1a9af285…`, `58e9db3e38f8124c…`, sizes exact; receipt carries the same pairs | MATCH |
| 3 | **`.ee.fmod_guids` 758 B, version 1, banks vehicles/character/effects, 45 GUIDs** (§12 row, spec §1 row 9) | parsed the file myself: 758 bytes, `version 1`, banks `['vehicles','character','effects']`, `count 45`, 0 trailing bytes; sha `44ca55635ad83fdb…` = MODLOG artefact table | MATCH |
| 4 | sample counts **649 + 1,228** (§12 row) | `fsb5` on built `vehicles.bank` = 649 samples; `--check` reports `(1877 samples)` total → 1,228 weapons; `fsb_at` 57,295,680 / 6,153,504 as quoted | MATCH |
| 5 | "two **private copies** of the shipped banks (R7)" — sources unchanged | current sha of `Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` = `6161104d8909b7b0…` and `E:\Modding\JustCause3\_grab\audio\weapons.bank` = `ab537a7cfc4c4b25…`, both equal the manifest's recorded `source_sha256` | MATCH (no in-place edit) |
| 6 | "`Builds/bm-004/aaf` is bm-001's identity tree" (§12 row) | full walk: 590 files vs 590, identical paths, identical sizes, **0 byte-differing files** (including the re-emitted `.fmod_guids`) | MATCH |
| 7 | MODLOG artefact table shas `3d26950f…` (install.ps1), `ab685a1d…` (manifest), `1437e6a0…` (receipt) | `sha256sum` on the three files | MATCH |
| 8 | clip/pad claim vs data (issue 1) | map chosen slots: `clip_pct` 0.0/0.0/0.1/0.0/3.53, `padded_frames` 0/0/0/149,503/80,213 — identical to manifest `measured`; contradicts a literal "0 clipped/padded" | MISMATCH with literal wording, MATCH with map |
| 9 | spec §1 row 10: bm-001 `.ee` **10,737,057 B, `6AB8275F…`** | `os.path.getsize` + sha256 of `Builds/bm-001/v0300_car_kensington_sportsmuscle_civilian_01.ee` → 10737057 B, `6ab8275f…` | MATCH |

Checks run: `python Tools/scripts/bm_audio.py --check` (exit 0), `t12_audio` inputs read directly,
file/sha/parse spot-checks above. Checks not run: tamper suite, PowerShell installer rehearsals,
anything touching `D:\Games`.
