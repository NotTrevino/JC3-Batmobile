# Independent review — card B-06 · Weapon entities (private copies)

**Reviewer:** not the author. Read-only: no backlog, MODLOG, `Research/`, `Tools/` or game file was
edited; the only file written is this review. The card's own `--check` was run as instructed (it
regenerates its scratch `tmp/b06/built.xml`); nothing else in the repo changed. No game launch, no
commit.

**VERDICT: needs rework.** The tune work itself is careful and every edited byte is correct, but the
card's headline check now **fails**: `bm-006` was built from the **pre-rework** `bm-005` graph, so its
delivered `.epe` still carries B-05's superseded members while the dependency has moved on. The
failure is reproducible with the exact command in the §12 row, and the script's own base-integrity
guard cannot detect the cause (it compares the base file to itself).

---

## Check output (verbatim)

```
$ python Tools/scripts/bm_weapons.py --check
FAIL: the built .epe differs from the re-derived plan: 6 object(s) missing, 6 unexpected, e.g. missing [\"('SWeaponPoint', 'attach.vehicle', (('_object_id', 'EC9CC816=FFFF8003'), ('fire_effect', (0.0,)), ('id:5C19E7E0', 'batmobile_cannon'), ('id:61ECCE72', (-1.0,)), ('id:80201E4D', 'batmobile_turret'), ('id:8C547250', (0.0,)), ('id:D04059E6', (-405742323.0,)), ('name', 'attach.vehicle'), ('name_hash', (2049066765.0,)), ('type', (4.0,)), ('world', (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -0.054057, 0.002083, 1.0))))\", \"('SWeaponPoint', 'attach.vehicle', (('_object_id', 'B8D99B2D=FFFF8006'), ('fire_effect', (0.0,)), ('id:5C19E7E0', 'batmobile_machine_gun'), ('id:61ECCE72', (-1.0,)), ('id:80201E4D', 'batmobile_turret'), ('id:8C547250', (0.0,)), ('id:D04059E6', (-405742323.0,)), ('name', 'attach.vehicle'), ('name_hash', (2049066765.0,)), ('type', (4.0,)), ('world', (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -0.054057, 0.002083, 1.0))))\"] / unexpected [\"('SWeaponPoint', 'attach.vehicle', (('_object_id', 'EC9CC816=FFFF8003'), ('fire_effect', (0.0,)), ('id:5C19E7E0', 'batmobile_cannon'), ('id:61ECCE72', (-1.0,)), ('id:80201E4D', 'batmobile_turret'), ('id:8C547250', (0.0,)), ('id:A90F5E74', 'weapon_anchor'), ('id:D04059E6', (-405742323.0,)), ('name', 'attach.vehicle'), ('name_hash', (2049066765.0,)), ('type', (4.0,)), ('world', (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -0.054057, 0.002083, 1.0))))\", \"('SWeaponPoint', 'attach.vehicle', (('_object_id', 'B8D99B2D=FFFF8006'), ('fire_effect', (0.0,)), ('id:5C19E7E0', 'batmobile_machine_gun'), ('id:61ECCE72', (-1.0,)), ('id:80201E4D', 'batmobile_turret'), ('id:8C547250', (0.0,)), ('id:A90F5E74', 'weapon_anchor'), ('id:D04059E6', (-405742323.0,)), ('name', 'attach.vehicle'), ('name_hash', (2049066765.0,)), ('type', (4.0,)), ('world', (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, -0.054057, 0.002083, 1.0))))\"]
CHECK_EXIT=1 (1 failure(s))
EXIT=1
```

```
$ python Tools/scripts/jc3weapons.py --check --root Builds/bm-006
Builds\bm-006: 2 tune file(s) under editor/entities/jc_weapons
  w602_batmobile_cannon.wtunec       fire_rate  2            (T-WP1 expected 2       ) ok
      row fire_rate, decoded class
  w602_batmobile_cannon.wtunec       velocity   400          (T-WP1 expected 400     ) ok
      row velocity, derived class
  w603_batmobile_vulcan.wtunec       fire_rate  0.138        (T-WP2 expected 0.138   ) ok
      row fire_rate, decoded class
check ok: 3/3 edit(s) re-read from the built tunes, 2/2 tune file(s) decode
EXIT=0
```

The card's §12 row quotes both commands as passing. The second still does; the first does not.

---

## Issues

### 1. BLOCKING — `bm-006` carries the pre-rework B-05 graph, so the card's own Done gate fails

* Where: `Builds/bm-006/aaf/…/v0300_…_civilian_01.epe`, and `Working/Weapons/manifest.json` →
  `base.epe_sha256` / `base.bytes` / `base.classes`.
* What: the manifest records base `d118c0aa29167a5e…`, 124,520 B, 47 classes — the **pre-rework**
  B-05 build. The current dependency `Builds/bm-005/…epe` is `f4abe91da0bc3ce3…`, 124,488 B, 46
  classes. B-06 was written at 04:49; B-05's rework landed at 06:16. The delivered graph therefore
  predates the fixes it depends on.
* Measured consequence in the delivered `.epe` (exported to OS temp, parsed):
  ```
  w602_mediumtank_canon         weapon_type 2
  w603_mediumtank_mgun          weapon_type 2
  w618_sportsmuscle_missile     weapon_type 1   ← pre-rework (B-05 rework sets 2)
  w618_sportsmuscle_missile_emp weapon_type 1   ← idem
  ```
  and 4 `attach.vehicle` points still carry `id:A90F5E74 = weapon_anchor` — the donor-only third
  ref that B-05's rework deliberately **omitted** and recorded in `declared[]`.
* Why it matters: `4 attach points + 2 w618 components = 6` — exactly the "6 missing / 6 unexpected"
  in the failure. The card's "objects 467 -> 467 … sha `b89fea2d…`" remains internally true, but the
  artefact no longer matches its dependency, and the `weapon_anchor` string names a part B-04 does
  not provide (a dangling part binding B-05 had already removed).
* Fix: re-run `bm_weapons.py --write` against the reworked `bm-005`, then re-run both checks; update
  the manifest/receipt/§12 sha and sizes.

### 2. MAJOR (code) — the "base build changed" guard can never fire

* Where: `Tools/scripts/bm_weapons.py`, `build()` line 253 and `check()` line 556.
* What: line 253 stores `"epe_sha256": sha256(open(BASE_EPE).read())` in the freshly derived `doc`;
  line 556 then compares `sha256(open(BASE_EPE).read())` to that same value. Both operands come from
  the same run, so the check is a tautology. The manifest's recorded base sha (`d118c0aa…`) is never
  compared, and `Builds/bm-006/receipt.json` stores only `"base": "Builds/bm-005"` (no sha), so no
  artefact witnesses which base bytes produced the build.
* Why it matters: this is precisely the guard that should have produced a one-line "the base build
  changed — a card may not edit its dependency" failure instead of a 6-object graph diff. As written,
  a card can silently rebuild on a moved dependency, which is what happened.
* Fix: compare `BASE_EPE` against the sha recorded in the manifest (or a checked-in base record),
  and store the base sha in the receipt.

### 3. MODERATE — the card's Done clause is not what `--check` verifies

* Where: card §8 B-06 `Done:` ("every weapon path the `.epe` names **exists in the build**") vs
  `Tools/scripts/bm_weapons.py` `done_paths()` lines 368–388 and the PASS line.
* What: of 9 paths, only **2** are private and actually present in `Builds/bm-006`. The other 7 are
  classified `shared` if they appear in `INDEX.jsonl`, the APC graph or `SIGNATURE_DIFF.json` — none
  of them is required to exist in the build. Checked: the APC body model path
  `models/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_body.model_xml`
  has **0** hits in `INDEX.jsonl` and resolves only because it is a string in the APC's shipped
  graph. The private test also succeeds via a name substitution: the graph names `….wtune`, the file
  is `….wtunec` (`candidates = [p, p.replace(".wtune", ".wtunec")]`).
* Why it matters: not false data — the output line honestly says "7 shipped … 0 dangling" — but the
  card's Done wording ("exists in the build") is stronger than the gate, and a reader of §12 sees
  "0 dangling" and concludes all nine paths are in the build. Two of the seven are B-05's deliberate
  APC leftovers (M2 grip point, body model, collision `.pfx`), i.e. exactly the paths that are *not*
  Batmobile files.
* Fix: either reword the Done criterion to "private paths exist in the build; shipped paths resolve
  in the shipped index/graphs", or require the shared leftovers to be private copies (they are not,
  and the manifest marks them `UNCHANGED` with reasons — so rewording is the honest option).

### 4. MINOR — two of four components still name shared shipped tunes, and the missile carrier class is wrong

* Where: `Working/Weapons/manifest.json` `weapons[]` (T-WP3/T-WP4 `copy: false`), MODLOG limits.
* What: the card's Do says "for each cloned JC3 weapon: copy its `.ee`/tunes to a new private path".
  Only `w602` and `w603` get copies. `w618` keeps
  `…/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtune` (shared, R7-safe because nothing is
  edited). This is declared as a limit, but the §12 phrasing "2 private tune copies" plus a green
  check reads as complete coverage of four components.
* Additional dependency risk B-06 inherits without comment: B-05's `w618` objects are
  `CBulletWeaponBase` clones of the APC (0 `CMissileWeaponBase` in the graph), yet they are now
  pointed at a missile tune and a no-lock-on missile autoaim preset. A tune path named on a
  bullet-weapon component is a name-level match, not a demonstrated behaviour (R5). B-05's rework
  report calls this a residual observation; B-06's manifest and MODLOG do not repeat it.
* Fix: say in the B-06 record that the `w618` tune decision cannot be validated until the carrier
  class is fixed in B-05, and do not count `w618` toward the card's "each cloned weapon" Do.

### 5. MINOR — stale numbers in generated artefacts (R11 scope)

* `Working/Weapons/manifest.json` `base`: `bytes 124520`, `classes 47` — both belong to the old
  B-05 graph. B-06's `built.classes` is also `47` because `bm_weapons.py` counts `{o.cls}` including
  the classless root (B-05's rework corrected this to 46).
* §12's `".epe` 124,520 -> 124,776 B"` is accurate only relative to the pre-rework base.
* `aafdiff` (687 identical / 2 new / 2 changed) and the re-encode measurement (14,224 -> 14,208 B)
  appear in prose only; no `--check` re-derives them. They were re-measured for this review and are
  correct against the current tree (691 vs 689 files, 2 new + 2 changed), but they are one-off
  measurements, not gated counts.

### 6. MINOR — member label "autoaim" is looser than the decode

* `Working/Weapons/manifest.json` and §12 call `id:6D4C8277` "autoaim"; `Research/JC3Grab/
  WEAPON_WIRING.md:16` decodes it as **`autoaim_tuning_file`** (`6D4C8277`), which is the name with
  provenance. The values written are the correct autoaim presets; only the label/evidence citation
  is imprecise. (`id:AA7096C9` = `tuning_file` is hash-verified: `hash_jenkins("tuning_file") =
  0xAA7096C9`.)

### 7. Not re-run (read-only constraint)

The 5-case tamper harness `tmp/b06_tamper.py` exists (5,604 B, written 04:51) but mutates and restores
`Builds/bm-006`; it was **not** executed for this review. The tamper table in MODLOG is therefore
accepted as recorded, not independently reproduced.

---

## Spot-checks

| # | Value in the card/doc | Where verified | Result |
|---|---|---|---|
| 1 | `w602 … fire_rate 1.75 -> 2` at `0xA0` | bytes of `Builds/bm-006/…/w602_batmobile_cannon.wtunec`; source `E:/Modding/_JC3grab/weapons/w602_mediumtank_canon/w602_mediumtank_canon.wtunec` | built `struct.unpack('<f', 0xA0) = 2.0`; source = `1.75` — matches |
| 2 | `w602 … velocity 500 -> 400` at `0x9C` | same two files | built = `400.0`; source = `500.0` — matches |
| 3 | `w603 … fire_rate 0.1 -> 0.138` at `0xA0` | `…/w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec` vs source | built = `0.1379999965` (float32 0.138); source = `0.10000000149` — matches |
| 4 | copy sizes `14,224` / `14,223` B, unchanged by the patch | `os.path.getsize` on both copies | 14,224 and 14,223; both equal their sources — matches |
| 5 | `.epe` `b89fea2d…`, 124,776 B | `sha256sum` / `ls` on `Builds/bm-006/…epe` | exact match |
| 6 | "both private tunes registered in `@files.xml`" | `Builds/bm-006/aaf/@files.xml` lines 706–707 | both `w602_batmobile_cannon.wtunec` and `w603_batmobile_vulcan.wtunec` listed — matches |
| 7 | "inner ADF instance name still reads `<shipped basename>.wtune`" (UNKNOWN whether load-bearing) | `ConvertAdf -e` of the private copy to temp | `<instance name="w602_mediumtank_canon.wtune" …>` — limit confirmed, UNKNOWN correctly declared |
| 8 | Out paths exist | on disk | `Working/Weapons/manifest.json`, `Builds/bm-006/receipt.json`, `Tools/scripts/bm_weapons.py`, `Tools/scripts/jc3weapons.py`, 2 weapon files — all present |

---

## What is sound

* **R7 is respected.** The shipped tunes are byte-identical to their recorded sha1 (asserted by
  `--check`), and the two edits land in private copies under
  `editor/entities/jc_weapons/06_vehicle/w6xx_batmobile_<name>/`.
* **The offsets and values are decoded, not guessed.** `0xA0` and `0x9C` are the `offset-in-file`
  `ConvertAdf -e` reports; `fire_rate` is documented as seconds-between-shots in
  `Research/JC3Grab/WEAPONS.md` and T7's 1:1 behaviour row, so the unit bridge is evidence-backed
  (R4/R5 pass for these three numbers).
* **Size-preserving patching is measured and justified**, with the rejected re-encode (14,224 ->
  14,208 B) recorded.
* **The manifest and receipt are generated**, not hand-written, and `--check` compares the manifest
  to the re-derived plan.
* **The remaining UNKNOWNs are declared** (inner ADF name, loose-`.epe` install), not dressed up.

## What must change before the row can read `done`

1. Rebuild from the current `bm-005` (`f4abe91d…`), which removes `weapon_anchor` and sets the w618
   `weapon_type` to 2; re-run both checks to green.
2. Make the base-integrity check compare against the **recorded** base sha, and record the base sha
   in `receipt.json`.
3. Update the stale base numbers in the manifest/§12 and reword the Done criterion to match what is
   actually verified (private paths in the build; shipped paths in the shipped index).
4. State in B-06's own record that `w618`'s tune choice rides on B-05's wrong carrier class.
