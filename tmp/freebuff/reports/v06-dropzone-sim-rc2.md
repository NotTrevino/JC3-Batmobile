STATUS: partial — `WhatIf`, `Install` and `Verify` pass on a faithful copy of the live dropzone, but `Rollback091` does **not** restore the copy byte-for-byte: it removed the 9 files it had just overwritten (11 -> 2), because `Install` had backed none of them up. Everything was offline on copies under `E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2*`; no game folder was written and the game was not launched.


V-06 repeated for `Builds/bm-RC2`, per the brief. The copy was verified byte-identical to the live dropzone
(11/11 sha256) before anything ran, and every `-GameDir` was checked by a guard before each action.

## Result against the four requested confirmations

| confirmation | result |
|---|---|
| `WhatIf` lists exactly the receipt's files | PASS — 9/9, all `same`, `wrote 0 files, 9 listed` |
| `Install` adds/replaces exactly those | PASS — `installed 9/9`, nothing else in the tree changed (11 files before and after) |
| `Verify` | PASS — `verified 9/9` |
| `Rollback091` restores byte-for-byte | **FAIL** — 9 `removed`, `files: 11 -> 2`, `missing=9 changed=0` |

**Root cause (decoded):** `install.ps1` line 49 backs a target up only when it exists **and** its hash differs
from the receipt; line 66's `elseif` makes `Rollback091` delete any target without a backup. The copied live
dropzone already held all nine payload files byte-identically (that is why `WhatIf` said `same`), so no backup
existed and rollback deleted all nine — including both ~200 MB FMOD banks.

**Consequence for the real install:** the live dropzone is currently in exactly that "already contains the
build" state, so running `Rollback091` against `D:\Games\Just Cause 3` today would delete those nine files,
with only a leftover `vehicles.bank.bm-RC1-backup` to rebuild one of them from. This needs a fix before RC2 is
pitched as revertible.

**Isolated (supplementary pass):** in a separate sim folder where all nine targets differed from the receipt,
`Install` wrote 9 `backed up` + 9 `installed` and `Rollback091` wrote 9 `restored`, giving
`missing=0 extra=0 changed=0 identical=9` — the backup/restore machinery works; the defect is the no-backup case.

## Files written

- `Builds/bm-RC2/verify/dropzone_sim.md` — the requested page: verdict, guard, every command, verbatim output.
- `Tools/scripts/dropzone_sim.py` — new harness: `--snapshot ROOT OUT`, `--compare A B`, `--check`.
- `tmp/freebuff/reports/v06-dropzone-sim-rc2.md` — this report.
- `tmp/freebuff/scratch/v06rc2/` — the captured logs and sha256 snapshots every block above is read from.
- Sim folders (outside the project, deletable): `E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2` (post-rollback state, 2 files)
  and `E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_tamper` (post-rollback state, 9 tampered files restored).

No `Builds/bm-RC2` source file was edited; the tree was run exactly as shipped.

## Commands and verbatim output

Guard (the same function guarded all seven runs):

```
guard() {
  printf 'GameDir argument = %s\n' "$1"
  case "$1" in
    'E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2'|'E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2_tamper') echo 'GUARD OK: approved sim folder under E:\Modding, not a game folder' ;;
    *) echo 'GUARD REFUSED: not an approved sim folder'; exit 9 ;;
  esac
  case "$1" in *[Gg]ames*) echo 'GUARD REFUSED: game path'; exit 9 ;; esac
}
```

### Copy the live dropzone

```
S=tmp/freebuff/scratch/v06rc2
LIVE='D:\Games\Just Cause 3\dropzone'
SIM='E:\Modding\JustCause3\_dropzone_sims\_dropzone_sim_rc2'
rm -rf /e/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2
mkdir -p /e/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2/dropzone
cp -a "/d/Games/Just Cause 3/dropzone/." "/e/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2/dropzone/"; echo "cp exit=$?"
python Tools/scripts/dropzone_sim.py --snapshot "$SIM\\dropzone" "$S/sim_before.json"
python Tools/scripts/dropzone_sim.py --compare "$S/live.json" "$S/sim_before.json"
( cd "/e/Modding/JustCause3/_dropzone_sims/_dropzone_sim_rc2/dropzone" && find . -type f -exec sha256sum {} + | sort ) > "$S/sim_before.sha"
diff "$S/live.sha" "$S/sim_before.sha" && echo "sha256sum live vs copy: identical (11 files)"
```

```text
compare tmp/freebuff/scratch/v06rc2/live.json -> tmp/freebuff/scratch/v06rc2/sim_before.json
  files: 11 -> 11
  MISSING editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee
  MISSING editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee.toc
  MISSING profile/item.onlinec
  MISSING profile/online.stringlookup
  MISSING profile/task.onlinec
  MISSING settings/spawn_vehicle_defs.bin
  MISSING sound/fmod_banks/vehicles.bank
  MISSING sound/fmod_banks/vehicles.bank.bm-RC1-backup
  MISSING sound/fmod_banks/weapons.bank
  MISSING textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc
  MISSING videos/corona_video.bikc
  EXTRA   dropzone/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee
  EXTRA   dropzone/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee.toc
  EXTRA   dropzone/profile/item.onlinec
  EXTRA   dropzone/profile/online.stringlookup
  EXTRA   dropzone/profile/task.onlinec
  EXTRA   dropzone/settings/spawn_vehicle_defs.bin
  EXTRA   dropzone/sound/fmod_banks/vehicles.bank
  EXTRA   dropzone/sound/fmod_banks/vehicles.bank.bm-RC1-backup
  EXTRA   dropzone/sound/fmod_banks/weapons.bank
  EXTRA   dropzone/textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc
  EXTRA   dropzone/videos/corona_video.bikc
  missing=11 extra=11 changed=0 identical=0
```

### `-Action WhatIf`

```
guard "$SIM"
pwsh -NoProfile -File Builds/bm-RC2/install.ps1 -Action WhatIf -GameDir "$SIM" 2>&1 | tee "$S/whatif.log"; echo "whatif exit=${PIPESTATUS[0]}"
```

```text
editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee 886A7919E205FC3B94E8EA1629587777CD62E3F3061CA4FC404F8B8CA09F9E2B same
editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee.toc 601AFB97837CCF996B2436E614D2B53411755A51D20580CF387C5D17F9D8DF6F same
profile\item.onlinec 239D6B6D2425FB8C1F4883FCCE7A70CF82BC9ED339182A179EDB477D8B550A6C same
profile\online.stringlookup 6DCDF0CE1AF304B6A77EBCB319E53A59FCAAFED6BF329CA2E9821483D3C60BC4 same
profile\task.onlinec 9250E2712478D50C649A32FBF0A5AB90931A25B1FE9EBAF98C7E38AD89CAE6C2 same
settings\spawn_vehicle_defs.bin 797391DCEF5FB5B6911C40A73D4B0691C876277681B2D51BD0A4EB6157043CF3 same
sound\fmod_banks\vehicles.bank 76D67BCEF81C8D297082B9CB026E9E995762FB2F72E3B2C2D7F5A1570E2F00A7 same
sound\fmod_banks\weapons.bank 5B8A7605A8B70CA211DEFA3C8856A1AB26B4276E11ECC46A4147AF245F7A7D78 same
textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc 5096FB74D8FCCE49B26FAD8DD269D48FEA7BE3859CA1C5DD692A0532FAE5058F same
wrote 0 files, 9 listed
```

### `-Action Install`

```
guard "$SIM"
pwsh -NoProfile -File Builds/bm-RC2/install.ps1 -Action Install -GameDir "$SIM" 2>&1 | tee "$S/install.log"; echo "install exit=${PIPESTATUS[0]}"
```

```text
installed editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee
installed editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee.toc
installed profile\item.onlinec
installed profile\online.stringlookup
installed profile\task.onlinec
installed settings\spawn_vehicle_defs.bin
installed sound\fmod_banks\vehicles.bank
installed sound\fmod_banks\weapons.bank
installed textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
installed 9/9
```

### `-Action Verify`

```
guard "$SIM"
pwsh -NoProfile -File Builds/bm-RC2/install.ps1 -Action Verify -GameDir "$SIM" 2>&1 | tee "$S/verify.log"; echo "verify exit=${PIPESTATUS[0]}"
```

```text
ok editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee
ok editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee.toc
ok profile\item.onlinec
ok profile\online.stringlookup
ok profile\task.onlinec
ok settings\spawn_vehicle_defs.bin
ok sound\fmod_banks\vehicles.bank
ok sound\fmod_banks\weapons.bank
ok textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
verified 9/9
```

### `-Action Rollback091`

```
guard "$SIM"
pwsh -NoProfile -File Builds/bm-RC2/install.ps1 -Action Rollback091 -GameDir "$SIM" 2>&1 | tee "$S/rollback.log"; echo "rollback exit=${PIPESTATUS[0]}"
```

```text
removed editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee
removed editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee.toc
removed profile\item.onlinec
removed profile\online.stringlookup
removed profile\task.onlinec
removed settings\spawn_vehicle_defs.bin
removed sound\fmod_banks\vehicles.bank
removed sound\fmod_banks\weapons.bank
removed textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
```

```
python Tools/scripts/dropzone_sim.py --compare "$S/sim_before.json" "$S/sim_after_rollback.json"
```

```text
compare tmp/freebuff/scratch/v06rc2/sim_before.json -> tmp/freebuff/scratch/v06rc2/sim_after_rollback.json
  files: 11 -> 2
  MISSING editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee
  MISSING editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee.toc
  MISSING profile/item.onlinec
  MISSING profile/online.stringlookup
  MISSING profile/task.onlinec
  MISSING settings/spawn_vehicle_defs.bin
  MISSING sound/fmod_banks/vehicles.bank
  MISSING sound/fmod_banks/weapons.bank
  MISSING textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc
  missing=9 extra=0 changed=0 identical=2
```

### Supplementary tamper pass (all nine targets differ from the receipt)

```
guard "$TAM"
pwsh -NoProfile -File Builds/bm-RC2/install.ps1 -Action Install -GameDir "$TAM" 2>&1 | tee "$S/tamper_install.log"; echo "install exit=${PIPESTATUS[0]}"
```

```text
backed up editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee
installed editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee
backed up editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee.toc
installed editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_debug.ee.toc
backed up profile\item.onlinec
installed profile\item.onlinec
backed up profile\online.stringlookup
installed profile\online.stringlookup
backed up profile\task.onlinec
installed profile\task.onlinec
backed up settings\spawn_vehicle_defs.bin
installed settings\spawn_vehicle_defs.bin
backed up sound\fmod_banks\vehicles.bank
installed sound\fmod_banks\vehicles.bank
backed up sound\fmod_banks\weapons.bank
installed sound\fmod_banks\weapons.bank
backed up textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
installed textures\ui\vehicle_icons\v0300_car_kensington_sportsmuscle_debug.ddsc
installed 9/9
```

### Live dropzone untouched

```
python Tools/scripts/dropzone_sim.py --compare "$S/live.json" "$S/live_after.json"
```

```text
compare tmp/freebuff/scratch/v06rc2/live.json -> tmp/freebuff/scratch/v06rc2/live_after.json
  files: 11 -> 11
  missing=0 extra=0 changed=0 identical=11
```

### `--check`

```
python Tools/scripts/dropzone_sim.py --check
```

```text
V-06 RC2 --check  (everything below is recomputed from disk; decoded/derived only)
PASS install.ps1 $Files == receipt.json files (separators normalised)  9 rows vs 9
PASS Builds/bm-RC2/drop matches the receipt byte-for-byte  9/9
PASS sim baseline == live dropzone (read-only walk)  11 files, missing=0 extra=0 changed=0
PASS after Install the copy is byte-identical to baseline  changed=0 extra=0 missing=0
PASS after Rollback091 exactly the receipt's files are gone, none changed  missing=9 extra=0 changed=0
PASS the files Rollback091 removed are exactly the receipt set
PASS tamper pass: Rollback091 restores a differing baseline byte-for-byte  9 files, missing=0 extra=0 changed=0
PASS dropzone_sim.md lists every receipt path  9/9
PASS dropzone_sim.md records -Action WhatIf
PASS dropzone_sim.md records -Action Install
PASS dropzone_sim.md records -Action Verify
PASS dropzone_sim.md records -Action Rollback091
PASS dropzone_sim.md embeds whatif.log verbatim  10 lines
PASS dropzone_sim.md embeds install.log verbatim  10 lines
PASS dropzone_sim.md embeds verify.log verbatim  10 lines
PASS dropzone_sim.md embeds rollback.log verbatim  9 lines
PASS dropzone_sim.md embeds tamper_install.log verbatim  19 lines
PASS dropzone_sim.md embeds tamper_verify.log verbatim  10 lines
PASS dropzone_sim.md embeds tamper_rollback.log verbatim  9 lines
CRITERIA (measured, not asserted):
  WhatIf lists exactly the receipt's files : PASS (9/9, all 'same')
  Install adds/replaces exactly those      : PASS (9/9, 0 backups)
  Verify                                   : PASS (9/9)
  Rollback091 restores byte-for-byte       : FAIL (9 pre-existing files removed, baseline had 11)
check PASS  (0 failing assertion(s))
```

## UNKNOWNs

1. **The live dropzone's pre-RC2 state.** `E:\Modding\_dropzone_sim` (RC1's copy) is gone, and no dropzone
   backup is referenced in the receipt, so "byte-for-byte" had to be measured against today's live dropzone,
   which already contains the payload. Tried: `ls /e/Modding`, `grep -rn _dropzone_sim` (only RC1's MODLOG
   summary: 4 files, 212 MB, no hashes).
2. **Who installed the nine files into the live dropzone.** Content equals RC2's receipt; history is not
   recorded anywhere in the tree.
3. **Provenance of `vehicles.bank.bm-RC1-backup` and the 0-byte `videos/corona_video.bikc`.** Neither is in the
   receipt. An RC1 `Install` with no rollback fits the name and RC1's MODLOG note, but that is a hypothesis.
4. **Whether the game loads this tree.** Test ban: not launched, not tested.
5. **Whether `Install`'s un-rolled-back-backup guard (line 50) fires on a real install.** Not reached: the live
   dropzone has an `.bm-RC1-backup`, not an `.bm-RC2-backup`, and no target differed from the receipt.

## Limitations

- The failing criterion is reported, not fixed: the brief is to run `Builds/bm-RC2/install.ps1` as shipped, and
  editing an existing `Builds/bm-*` tree is forbidden by `tmp/freebuff/INSTRUCTIONS.md` §3.
- Two earlier harness passes (empty copy, then a copy nested one level deep) are labelled invalid in the md §12
  and kept as `empty_*.log` / `nested_*.log` in the scratch folder.
- No game launch, no write under `D:/Games` or `E:/Games`, no git, no network.
