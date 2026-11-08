# T-rows evidence-path audit

Scope: every record in `Working/Translation/T_ROWS.jsonl` whose `dispo` is `keep` or `next` must name at least one evidence path that exists on disk. Records with no path token at all are marked `MISSING_PATH`. The ledger was read only; it was not edited.

- Input: `Working/Translation/T_ROWS.jsonl` (199 records; 138 with `dispo` `keep` or `next`).
- Output: `Working/Prep/t_rows_evidence.tsv` — 140 data rows, columns `row_id, dispo, evidence_path, path_exists, note`.
- Parser: `C:\Users\User\AppData\Local\Temp\t_rows_evidence_audit.py` (outside the repository), run from the repository root against the ledger.

## Summary — rows per outcome

| outcome | records | meaning |
|---|---:|---|
| PASS | 22 | at least one parsed evidence path exists on disk |
| MISSING_PATH | 116 | record names no path token at all |
| NO_EXISTING | 0 | paths named, but none resolves to a file on disk |
| **total** | **138** | every `keep`/`next` record |

TSV token rows: **140** — 23 with `path_exists = yes`, 117 with `path_exists = no` (the 116 `MISSING_PATH` placeholder rows plus the single unresolved token, `files.xml`).

## Method

1. Parse each non-empty line as JSON; keep records with `dispo` in `{keep, next}`.
2. The evidence text is the **last** element of `cells`. The cells array is ragged (6–17 entries; multi-line and comma-split fields occur), so the last element — not a fixed index — is the evidence field.
3. Extract path-looking tokens with `[A-Za-z0-9_./-]+`: a token qualifies if its basename has a known file extension (`md`, `json`, `jsonl`, `py`, `xml`, `ee`, `rbm`, `effc`, `upk`, `tsv`, `txt`, …) or it starts with a known directory (`Research/`, `Working/`, `tmp/`, `Tools/`, `reports/`, `effects/`). Backticks, trailing punctuation and `:line` / `:start-end` suffixes are stripped; a bare extension such as `` `.ee` `` is not treated as a path.
4. Resolve against the repository root:
   - tokens containing `/` are tested **only** as `<root>/<token>`;
   - bare filenames are tested at `<root>/<name>` first, then in a fixed set of evidence directories (`reports`, `tmp/freebuff/reports`, `Research`, `Research/JC3Grab`, `Research/BatmobileGrab`, `Working`, `Working/Translation`, `Working/Prep`, `Working/Lights`, `Working/Appearance` + `/build` + `/factors`, `Working/Factors`, `Working/Assembled`, `Tools`, `Tools/scripts`).
5. A record with zero tokens gets one `MISSING_PATH` row. A record passes if at least one of its tokens exists.

A full-tree basename walk was attempted first and abandoned: `os.walk` over the repository did not finish within 25 s on this drive, so the bare-filename resolution is limited to the candidate directories above. `MULTIPLE(n)` notes therefore count matches within that candidate set, not every copy in the tree.

## Records with an existing evidence path (22)

`T-G1` (`stations.json`), `T-G4`, `T-ST2`, `T-ST4`, `T-E2`, `T-B1`, `T-A3` (keep-audit reports), `T-P3` (`T22_REOPEN.md` + `t22_reopen.py`), `T-MA1` (`verify_install.py`), `T-MA2` (`factors.json`), `T-MA3` (`factors.json`), `T-MA4` and `T-MA6` (`spec_check.py`), `T-LG2` (`t2_lg2.py`), `T-LG6` (`LIGHT_SYSTEM.md`), `T-FX3` (`T_FX3B.md`), `T-CO1` (`jc3hkx.py`), `T-CO2` (`t22_reopen.py`), `T-CO3` (`t22_collision.py`), `T-K4` and `T-DR1` (`keep-audit-steering-and-drift.md`), `T-PA9` (`ENTITIES.md`).

Two notes worth reading:

- **`T-G1`** cites `stations.json`; two copies match in the candidate set (`Working/Appearance/build/stations.json` first). Seven copies exist in `Working/Appearance/*` and `Working/Assembled/`, so the token identifies a family of build outputs, not one file.
- **`T-MA2`** also cites `@files.xml`, which resolved as `files.xml` and is **not present** anywhere in the candidate set. The record still passes on `factors.json`. `T-MA2` is the only record with an unresolved named file.

## Records with no evidence path (116)

These records name no file or directory at all; their evidence text is a probe/test description (or a bare word such as `derived`, `same`, `—`). They do not currently satisfy the rule.

`T-G2 T-G3 T-M3 T-S3 T-S4 T-S5 T-R2 T-R3 T-ST3 T-ST5 T-ST6 T-E5 T-B2 T-B3 T-B4 T-A1 T-K2 T-K3 T-P2 T-MA5 T-MA7 T-LG1 T-LG3 T-AU1 T-AU2 T-AU3 T-FX1 T-FX2 T-FX5 T-DM1 T-DM3 T-DM4 T-DM5 T-DM6 T-G6 T-S6 T-ST7 T-EF1 T-DM7 T-DM8 T-DM9 T-AU5 T-AC1 T-SR1 T-FX9 T-FX10 T-FX11 T-FX12 T-FX13 T-FX14 T-FX15 T-FX16 T-FX20 T-L8 T-L9 T-L10 T-L11 T-L12 T-L13 T-L14 T-L15 T-L16 T-L17 T-L18 T-L19 T-L20 T-L21 T-L22 T-L23 T-L24 T-L25 T-L26 T-L27 T-L29 T-L31 T-L32 T-L33 T-L34 T-L35 T-WP1 T-WP2 T-WP3 T-WP4 T-WP5 T-WP7 T-WP8 T-WP9 T-WP10 T-WP11 T-WP12 T-WP13 T-WP14 T-WLD1 T-WLD2 T-WLD3 T-WLD4 T-WLD5 T-WLD6 T-WLD7 T-WLD11 T-WLD12 T-WLD13 T-WLD14 T-WLD15 T-WLD16 T-WLD18 T-WLD19 T-MD1 T-MD2 T-MD3 T-MD4 T-MD9 T-MD10 T-MD11 T-MD12 T-MD15`

This is a content observation, not a parser failure: the evidence cells are probe descriptions or bare words (`derived`, `same`, `—`), and they contain no filename or slash-prefixed path. Member names such as `light_type` or `preset_id` also appear in some cells, but a member is not a path.

## Integrity and checks

- `Working/Translation/T_ROWS.jsonl` sha256 before and after: `220dead9b019863a9d3113de5e29cf6d0040e01c2df84da5090d67f8865d5b7a` (unchanged).
- `Working/Translation/T_ROWS.jsonl.bak-b13` sha256: `9936b1fffe6d51309f273188a59171e3bdeb3b0f3089e2476d6e11c48d6c25aa` (not opened for write).
- Outcomes sum to 138 = number of `keep`/`next` records: 22 + 116 + 0.
- TSV header is exactly the five requested columns; 140 data rows; every `MISSING_PATH` row has an empty `evidence_path` and `path_exists = no`.
- Parser script lives outside the repository; the report and TSV are the only files written by this task besides the report mirror.
