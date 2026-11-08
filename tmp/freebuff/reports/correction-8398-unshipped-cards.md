# Correction 8398 — RC4's claim must match its bytes

STATUS: done. Option **(b)** was taken: **no merge**. The release candidate is recorded as the
**pursuit set only**, with the pursuit/battle pair as a **separate, unmerged payload** in
`Builds/bm-RC4-modes/`, and every payload-free card now says **"no payload in RC4"** with its
reason in the card, the tracker, the receipt and `BUILD_BATCHES`. No card was marked done and no
feature was added to make one look shipped.

## 1. What the evidence says

`bm-RC4`'s `.ee`/`.toc` were not touched by this correction (`Builds/bm-RC4` receipt unchanged:
`complete: false`, 506 `.toc` records). The claim/byte mismatch was in the describing text:

| group | bytes | claim being made |
|---|---|---|
| **B-12 / D-2 modes** | `Builds/bm-RC4-modes/pursuit` and `/battle` exist; `aafdiff` = exactly the 2 planned files; each receipt says `0` exact rows, `2` composed, `2` same-switch, `4` not built | the RC's `not_done` said only "has no payload: this is one tree", which understated a **built** pair and did not say it is unmerged |
| **B-17…B-20** | `BUILD_BATCHES` §4: values `0`, `-` edit files | declared no-payload already; the tracker rows did not say "no payload in RC4" |
| **B-25 lens flares / light units** | card only; the flare sprite cannot be attached (no effect member on a lamp); units unproven | card and tracker read as ordinary `todo`, no RC statement |
| **B-26 per-entity audio** | card only; the 21 pinned GUIDs stay donor | same |

`build-d13` §5.4–§5.5 and `build-d12` §0 already carried the facts; the receipt, the cards, the
tracker, `BUILD_BATCHES`' B-12 row and `STATUS.md` did not all repeat them.

## 2. Why not merge

Merging `bm-RC4-modes/battle` into the RC would double the entity (a second `v0300` leaf) and the
swap trigger is **UNKNOWN** (`mode-switch-carriers.md` §7 U1) — no decoded member selects a variant
at runtime. Merging would therefore ship a second car nothing can switch to, double the entity
count, and leave the name/hash conflict unresolved. The evidence does not support it, so the RC
stays one tree.

## 3. What changed (each says "no payload in RC4", none says done)

* `Builds/bm-RC4/receipt.json` + its generator `Tools/scripts/bm_rc4.py`:
  * new `modes` block: `rc_set: "pursuit"`, `merged_into_rc: false`, both built trees,
    `aafdiff_planned_files: 2`, `rows_exact: 0`, `rows_composed: [T-MD5, T-MD6]`,
    `rows_same_switch: [T-MD10, T-MD11]`, `rows_not_built: [T-MD7, T-MD13, T-MD8, T-MD14]`;
  * `cards_without_payload` now lists **B-12, B-17, B-18, B-19, B-20, B-25, B-26** with reasons;
  * `not_done` carries the modes sentence and the B-17…B-20 no-payload sentence;
  * `--check` asserts the new set and the modes block.
* `Working/Translation/BUILD_BATCHES.md` §4: B-12's `15 values` → **`0`**, basis "no payload in
  RC4: pair built separately and unmerged …"; B-25/B-26 rows name their RC reason. The 24-step
  table and the B-17…B-20 `-` declarations are unchanged and now match the receipt.
* `GRAB_BACKLOG.md`: B-12 tracker row says **no payload in RC4** with the four row counts and keeps
  `todo`; B-17…B-20 tracker rows say **no payload in RC4** (declared in `BUILD_BATCHES` §4);
  B-25/B-26 cards and new tracker rows say **no payload in RC4** with the blocker that prevents a
  payload (no effect member on a lamp / 21 GUIDs stay donor).
* `STATUS.md` + `Tools/scripts/status_audit.py`: a generated section "`bm-RC4` — what its bytes
  actually carry" reads the receipt: pursuit set only, pair unmerged, row counts, no-payload cards,
  `complete: false`.
* `tmp/freebuff/reports/build-d13-release-candidate-4.md` §5.4 already states the pair is built but
  unmerged; the diff below does not change it.

Not touched: `Builds/bm-RC4` bytes, `Builds/bm-RC4-modes` bytes, any game install.

## 4. Checks run

```
$ python Tools/scripts/status_audit.py --write   # then --check
$ python Tools/scripts/bm_rc4.py --check
$ python Tools/scripts/b12_variants.py --check
$ python Tools/scripts/t23_closeout_inventory.py --check
```

Results are recorded in the task's completion message; any red is reported there rather than
papered over. `b12_variants.py --check` is expected to remain red for its own reason (the card is
live and unbuilt), not because of this correction.

## 5. Limits

* Nothing was launched; the mode swap stays UNKNOWN, and the two mode trees are unproven in play.
* `B-25`'s flare attachment and `B-26`'s per-entity bank are still unproven mechanisms - the cards
  stay `todo`, with the blocker named.
* `complete: false` stands; the texture gaps, B-10 gate and D-08 conflict are untouched.

## 6. Revert

Revert `Builds/bm-RC4/receipt.json`, `Tools/scripts/bm_rc4.py`, `Working/Translation/BUILD_BATCHES.md`
and the `GRAB_BACKLOG.md`/`STATUS.md` edits, and restore the previous `status_audit.py` block. The
RC `.ee` is unchanged by this correction, so no rebuild is needed. `Builds/bm-RC4-modes` is
untouched and can be deleted separately if the pair is abandoned.
