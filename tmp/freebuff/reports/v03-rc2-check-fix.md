# v03-rc2-check-fix - why `v03_wiring_rc2.py --check` failed, and the fix

## STATUS

**done - fixed and deterministic. `--check` now exits 0 twice in a row, and its two documents
regenerate byte for byte. The failure was not a timestamp in the document, a path separator or an
unsorted set: `bm_audio.py`'s manifest embeds `installer.dropzone_at_build`, a live probe of the game
dropzone (presence, byte size, mtime), and `v03_wiring_rc2.py` fed that verdict into its documents.
Four lines drifted, all in that one field.**

Files written / changed:

- `Tools/scripts/v03_wiring_rc2.py` - G4 now gates on the wiring-relevant part of `bm_audio --check`
  and excludes the volatile manifest-record line (new `split_audio_fails()`, plus fixed document
  prose). No other logic touched.
- `Builds/bm-RC2/verify/wiring.json`, `Builds/bm-RC2/verify/wiring.md` - regenerated with `--write`.
  These two are that script's own outputs; the build itself (`.ee`, `.toc`, receipt, drop tree,
  banks, manifest, `install.ps1`) was **not** written or regenerated.
- `tmp/freebuff/reports/v03-rc2-check-fix.md` (this card).

Revert: `git checkout -- Tools/scripts/v03_wiring_rc2.py` restores the old gate; the two files under
`Builds/bm-RC2/verify/` are regenerated artefacts and revert the same way.

---

## 1. The state on arrival

The brief reports `--check` failing on "wiring.md does not match the regenerated text (2 document
mismatches)". Run on arrival, the documents already matched; the live red one was **G4**:

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && PYTHONIOENCODING=utf-8 python Tools/scripts/v03_wiring_rc2.py --check; echo "check_exit=$?"
PASS G1: 9 SWeaponPoint, part refs dangling 0
PASS G2: 63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
PASS G3: 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
FAIL G4: bm_audio --check rc=1 (1 failure line(s): 0 GUID/event/tune, 1 manifest); .ee.fmod_guids == B-11's: True
PASS G5: item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
FAIL: dangling 0, gate failures 1
PASS documents: wiring.json and wiring.md match the regenerated text
check_exit=1
```

So the document comparison was green, and the exit code was still 1 because the script returns
non-zero whenever a gate is red. The gate that was red was the one that *copies* `bm_audio.py --check`
into the document - which is the same defect the brief describes, one level up: the document embeds
a value that is not a property of the build.

## 2. The exact lines that differ

`bm_audio.py`'s own check compares the whole record it re-derives against
`Working/Audio/bm_bank_manifest.json`. Diffing them line by line
(`tmp/freebuff/scratch/manifest_diff.py`, which calls `bm_audio.build(write=False)` and diffs
`json.dumps(public(doc), indent=1)`) gives **4 changed lines, all in `installer.dropzone_at_build`**:

```
on-disk 4218 lines, re-derived 4220 lines
--- manifest-on-disk
+++ re-derived
@@ -4002,8 +4002,10 @@
     "present": true,
     "bytes": 210781376,
-    "mtime": "2026-10-14 15:33:28"
+    "mtime": "2026-11-02 21:48:39"
    },
    "weapons.bank": {
-    "present": false
+    "present": true,
+    "bytes": 177586080,
+    "mtime": "2026-11-02 21:48:41"
    }
   }

DIFFERS top-level key: installer
  installer.dropzone_at_build: on-disk {"vehicles.bank": {"present": true, "bytes": 210781376, "mtime": "2026-10-14 15:33:28"}, "weapons.bank": {"present": false}}
  installer.dropzone_at_build: re-derived {"vehicles.bank": {"present": true, "bytes": 210781376, "mtime": "2026-11-02 21:48:39"}, "weapons.bank": {"present": true, "bytes": 177586080, "mtime": "2026-11-02 21:48:41"}

second build in-process identical: True
```

Named precisely:

- `vehicles.bank.mtime`: recorded `2026-10-14 15:33:28`, live `2026-11-02 21:48:39` (the file was
  touched, size unchanged at 210,781,376 B);
- `weapons.bank.present`: recorded `false`, live `true`;
- `weapons.bank.bytes` / `weapons.bank.mtime`: absent in the record, live `177586080` /
  `2026-11-02 21:48:41`.

Nothing else differs: no document timestamp, no Windows `\` vs `/` (the manifest is written with
`json.dumps`, and this field's path is the game-install probe), no set iteration order (`sort_keys`
is not used but the field order is the dict's construction order, and it is identical on both sides),
no hash drift in the banks. `bm_audio.build()` is deterministic **within** a process and across
runs; only the environment probe moves.

**Cause:** `dropzone_probe()` (`Tools/scripts/bm_audio.py`) records `st_size` and
`datetime.fromtimestamp(st.st_mtime)` of the live `dropzone/sound/fmod_banks` directory. That
snapshot can never be re-derived later - the game and any installer rewrite the directory - so the
comparison drifts with the machine. It is environment state, not build state.

**Why it surfaced here:** G4 embedded `bm_audio --check`'s `rc` and its per-category failure counts
in `wiring.md`/`wiring.json`. So the wiring documents carried a value that changes when the game
writes its dropzone: exactly the "manifest metadata drift" hypothesis in the brief.

## 3. The fix

In `Tools/scripts/v03_wiring_rc2.py` only:

1. New `split_audio_fails(lines)` classifies `bm_audio --check`'s `FAIL:` lines: the
   manifest-record line (matched by `bm_bank_manifest.json differs from the re-derived record` or
   `dropzone_at_build`) is **volatile**; everything else - bank, sample, payload, frames, name,
   duration, event, tune, GUID, `fmod_guids`, `install.ps1` - is **gating**.
2. G4 now passes on `not gating and same` (same = `.ee.fmod_guids` equals B-11's), and reports
   `0 gating failure(s) (0 bank/sample/event/GUID, 0 other); manifest record excluded ...`.
3. The document's audio paragraph and its UNKNOWN are fixed prose: no `rc`, no failure counts, no
   mtimes, no paths from the probe. (The measured drift is named here, in this card, not in the
   regenerated document.)
4. A latent bug in the old classification is gone with it: the old code counted a failure only if it
   matched a keyword list, so a line like `install.ps1 is stale against the re-derived text` would
   have been counted as neither GUID nor manifest and silently dropped from both totals. Now
   "everything not volatile" gates, and the "other" count is reported.

The build is untouched: no write under `Builds/bm-RC2` except the two `verify/` documents,
`Working/Audio/bm_bank_manifest.json` not rewritten, no bank or `install.ps1` regenerated, no game
launched (INSTRUCTIONS.md §3).

## 4. Verbatim: write, then two checks

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/v03_wiring_rc2.py --write; echo "write_exit=$?"
PASS G1: 9 SWeaponPoint, part refs dangling 0
PASS G2: 63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
PASS G3: 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
PASS G4: 0 gating failure(s) (0 bank/sample/event/GUID, 0 other); manifest record excluded (live installer.dropzone_at_build snapshot, volatile); .ee.fmod_guids == B-11's: True
PASS G5: item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
PASS: dangling 0, gate failures 0
wrote Builds/bm-RC2/verify/wiring.json + wiring.md
write_exit=0
```

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/v03_wiring_rc2.py --check; echo "check1_exit=$?"
PASS G1: 9 SWeaponPoint, part refs dangling 0
PASS G2: 63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
PASS G3: 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
PASS G4: 0 gating failure(s) (0 bank/sample/event/GUID, 0 other); manifest record excluded (live installer.dropzone_at_build snapshot, volatile); .ee.fmod_guids == B-11's: True
PASS G5: item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
PASS: dangling 0, gate failures 0
PASS documents: wiring.json and wiring.md match the regenerated text
check1_exit=0
```

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/v03_wiring_rc2.py --check; echo "check2_exit=$?"
PASS G1: 9 SWeaponPoint, part refs dangling 0
PASS G2: 63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
PASS G3: 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
PASS G4: 0 gating failure(s) (0 bank/sample/event/GUID, 0 other); manifest record excluded (live installer.dropzone_at_build snapshot, volatile); .ee.fmod_guids == B-11's: True
PASS G5: item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
PASS: dangling 0, gate failures 0
PASS documents: wiring.json and wiring.md match the regenerated text
check2_exit=0
```

The exclusion did not blunt the gate - real audio defects still fail it:

```
$ PYTHONIOENCODING=utf-8 python -c "... v03_wiring_rc2.split_audio_fails(...)"
gating  : ['FAIL: vehicles.bank #12: payload bytes differ from the manifest (sha256)', 'FAIL: install.ps1 is stale against the re-derived text']
volatile: ['FAIL: Working/Audio/bm_bank_manifest.json differs from the re-derived record']
OK: manifest drift excluded, payload + install.ps1 still gate
```

(synthetic lines, so no build file was touched; the assertion also covers the case the old keyword
classifier would have dropped.)

## 5. UNKNOWN (with what was tried)

1. **Whether the dropzone drift matters for an install.** `bm_audio.py --check` still exits 1 on the
   manifest record. That field only describes what the dropzone looked like at build time; whether a
   `weapons.bank` that appeared afterwards changes `Install`/`Rollback091` behaviour is not tested -
   the test ban forbids running the installer or the game, and reading the installer text only shows
   it pins and verifies the *banks this build wrote*. The record was left as it is; rewriting it
   would be regenerating the audio manifest, which the brief forbids ("do not change the build").
2. **Whether `bm_audio.py` itself should ignore `installer.dropzone_at_build` in its own check.** Not
   changed: B-11's card depends on that comparison, and the brief scopes the fix to this script.
   Doing it would make `bm_audio --check` green too, but it is a separate decision with its own
   audit trail. Named here so it is not silently forgotten.
3. **Whether the dropzone's `weapons.bank` appearing on 2026-11-02 was ours, the game's or an
   installer's.** No record in the repository: the manifest's snapshot is the only witness and it
   holds no provenance. Would need the dropzone directory's own history, which this project does not
   keep.
4. **Play behaviour** - untested, test ban (§3).
