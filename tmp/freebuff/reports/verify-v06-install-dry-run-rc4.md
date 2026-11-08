# V-06 - install dry run on bm-RC4, simulated dropzone only

**STATUS: done.** All six required cases ran the real `Builds/bm-RC4/install.ps1` against
`E:/Modding/_dropzone_sim_rc4` and matched their expected exit code: Status 0, WhatIf 0, Install on
an empty root 0, Install over an installed root 0, decoy Install 0 with Rollback restoring it, and the
guard negative **2**. The generated record is `Builds/bm-RC4/verify/dropzone_sim.md`, and its
`--check` re-runs all eight probes and compares the document byte for byte (exit 0). No game folder
was read, written, launched or attached to; `D:/Games` and `E:/Games` were never passed to the
installer.

## 1. Artifact and receipt (decoded from the files)

| fact | value |
|---|---|
| installer | `Builds/bm-RC4/install.ps1`, **6,535 B** |
| sha256 | `b4589d40f3bed7c1dd2300d2698790c4fc9fee7e5213398a00ebad3aded15382` |
| receipt | `Builds/bm-RC4/receipt.json`, **schema 2**, **9 files**, tag `bm-RC4` |
| `drop/` | **9 files**, every one equal to its receipt sha256 |
| `.ee` | `b72690d3...a557b`, **11,225,533 B** |
| `.toc` | `cde0678e...5535`, **68,675 B** |

**Two brief values do not match the artifact, and are disclosed rather than reconciled:**

* the brief's installer hash `df23485d65f358e14ea8d0b5037d42f0` is **32 hex characters** (MD5
  length, and not this file's MD5 `10a8c40734a9b5aeecaa0d5a239205e6` either); the artifact's SHA-256
  is the 64-character value above;
* the brief's `.ee` size **11,225,534 B** is **one byte above** the receipt's and the built file's
  **11,225,533 B**. The receipt, `drop/` and the file agree with each other, so the artifact is
  internally consistent; the brief value is stale or mistyped.

## 2. The two host facts, re-proved (not assumed)

```
powershell -NoProfile -Command '$PSVersionTable.PSVersion.ToString();
  (Get-Command Get-FileHash -ErrorAction SilentlyContinue) -ne $null'
5.1.19041.6456
False
```

* **`Get-FileHash` is absent on this host's PowerShell 5.1** - the command object does not exist
  (`False`), which is the module-load failure that made the RC2 code path abort before snapshotting.
* The RC4 artifact does not use it: `HashOf()` is
  `[System.Security.Cryptography.SHA256]::Create()` over `[IO.File]::OpenRead($p)`, and no
  `Get-FileHash` occurs anywhere in `install.ps1`. Case 5 is the proof it works end to end: a
  differing target is hashed, backed up and restored.
* **`Get-Parts()` splits with the IO API, not a regex**:
  `[IO.Path]::GetFullPath($p).Replace([char]'/', [IO.Path]::DirectorySeparatorChar)
  .Split([IO.Path]::DirectorySeparatorChar)`. The forward-slash probe
  (`-GameDir E:/Modding/_dropzone_sim_rc4`) is accepted, exit 0 - a regex would have split on the
  wrong separator or on the drive colon.

## 3. Cases and exit codes

| # | case | action | expected | measured | result |
|---|---|---|---:|---:|---|
| 1 | Status, empty sim root | `Status` | 0 | **0** | PASS - 9 `absent` rows, **0 writes** |
| 2 | WhatIf, empty sim root | `WhatIf` | 0 | **0** | PASS - 9 rows `<path> <sha256> add`, `wrote 0 files, 9 listed`, **0 writes** |
| 3 | Install, empty sim root | `Install` | 0 | **0** | PASS - `installed 9/9`, all 9 hashes equal the receipt, Verify **0**, `verified 9/9` |
| 4 | Install over an installed root (the RC2 failure case) | `Install` | 0 | **0** | PASS - **no byte changed**, Verify **0**, `verified 9/9` |
| 5 | Decoy `profile/item.onlinec` | `Install` -> `Verify` -> `Rollback` | 0 | **0 / 0 / 0** | PASS - `backed up profile\item.onlinec`, Verify `verified 9/9`, Rollback restores the decoy byte-for-byte and removes only the **8** files that did not exist |
| 6 | Guard negative `E:/Modding/not_the_sim` | `Status` | 2 | **2** | PASS - prints `REFUSED: ...`, creates nothing |
| 6b | forward-slash form (probe) | `WhatIf` | - | **0** | accepted (normalisation) |
| 6b | case variant `E:/MODDING/_DROPZONE_SIM_RC4` (probe) | `WhatIf` | - | **0** | accepted (Windows path identity) |

### Case 4 - measured, and narrower than the brief's wording

The tree is byte-identical after the second Install and Verify is 9/9, which is the RC2 failure
fixed. But the installer's snapshot is a **diff** snapshot: it backs up a target only when
`(HashOf $d) -ne $sha`, so an install over an already-correct tree creates **0** files under
`snapshot/`, not 9. "Snapshots every existing target" describes the differing case (case 5), not this
one. Measured consequence, recorded but not required: a **Rollback** immediately after that install
has no backups to restore, so it **removed all 9 targets** and left the root empty - i.e. after an
install-over-install, Rollback is an uninstall. This is a finding about the artifact's semantics, not
a test failure; nothing in the six cases depends on it.

### Case 5 - the decoy had to be synthetic, and says so

Census (section 3.5 of the generated record): **6 builds** in `Builds/` carry
`drop/profile/item.onlinec` and all **6** are byte-identical, so no genuine foreign decoy exists in
the repo. The case therefore uses RC3's real file **plus one appended byte**
(sha256 `839a155d205fa60628e8f767175b198067de82f106d9ba4515e788135c8209cf`) and labels it
**synthetic**. What it proves is the installer path that matters: a pre-existing differing target is
hashed, copied to `snapshot/profile/item.onlinec`, replaced, verified, and restored byte-for-byte by
`Rollback`, while the eight files that did not exist are removed and no other path changes.

## 4. Commands run

```
python Tools/scripts/dropzone_sim2.py --write
  PASS 1 Status: exit 0 (expected 0)
  PASS 2 WhatIf: exit 0 (expected 0)
  PASS 3 Install (empty): exit 0 (expected 0)
  PASS 4 Install (already installed): exit 0 (expected 0)
  PASS 5 Decoy: exit 0 (expected 0)
  PASS 6 Guard negative: exit 2 (expected 2)
  PASS 6b forward slashes: exit 0 (expected 0)
  PASS 6b case variant: exit 0 (expected 0)
  8 cases, 0 required failure(s)
  wrote Builds/bm-RC4/verify/dropzone_sim.md

python Tools/scripts/dropzone_sim2.py --check
  ... same eight PASS lines ...
  PASS document: dropzone_sim.md matches the rerun
  exit 0
```

The harness's own guard (`guard()` in `Tools/scripts/dropzone_sim2.py`) runs before every action and
refuses any root whose normalised path is not `E:/Modding/_dropzone_sim_rc4`, so an accidental
`D:/Games` or `E:/Games` value cannot reach PowerShell. Case 6 is the only place a non-sim path is
passed through, and it is, by design, a REFUSED assertion that creates nothing.

## 5. Files written and revert

| file | what | revert |
|---|---|---|
| `Tools/scripts/dropzone_sim2.py` | new RC4 harness (the RC2 `dropzone_sim.py` is untouched) | delete the file |
| `Builds/bm-RC4/verify/dropzone_sim.md` | generated record, every case's exit code and raw output | delete the file |
| `E:/Modding/_dropzone_sim_rc4/` | disposable sim root, left holding the last case's tree | delete the folder |
| `tmp/freebuff/scratch/decoy_item.onlinec` | the synthetic decoy bytes | delete the file |

No `Builds/bm-*` tree other than the disposable sim root was written; `install.ps1`, the receipt,
`drop/`, the ledger and every research file are read-only inputs.

## 6. UNKNOWNs

* **Whether the game honours the installed files** - the test ban stands; no install ran against a
  game folder and no process was launched or attached to.
* **The brief's installer hash and `.ee` size** - not explained by the artifact (section 1). Both are
  recorded; resolving them needs the document that produced them (review 8399), not a re-hash.
* **A genuine foreign `profile/item.onlinec`** - none exists in the repo (6 builds, 1 distinct byte
  sequence), so case 5's restore path is proven on a labelled synthetic decoy rather than a real
  other-build payload.
* **Rollback semantics after an install-over-install** - measured (removes all nine when no backups
  exist), but whether that is intended behaviour or a defect is a decision for the card owner.
