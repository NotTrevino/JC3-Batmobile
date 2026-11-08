# Correction 8394 — the lights module's out-of-domain values (DONE)

**Status: labelled, not "fixed" — there is nothing to fix by invention.** The 24-row light module
(`Builds/bm-RC4-lights`, 7,105 B internal at `.toc` offset **16,499,504**) still writes
`range 60 / angle 70` on its two headlight-beam rows. Those rows are now marked as **out-of-domain
claims** in the lights ledger and in `Working/Q/PREDICTIONS_LOOKS.md`; the `multiplier 1.0` and
`falloff_start` members are marked **stand-ins**; row 11 (`T-L17`) is marked **donor-carried**, not
translated. No lamp was added and no value was changed.

## 1. What was wrong

`build-d03-lights-and-flares.md` §3 printed the beam rows as if the plan's numbers were shipped
values, with U-1..U-3 only in its §8 UNKNOWN table. The ledger carried the flags in each member's
`src` string but had no machine-readable statement, so a reader (or a later gate) could not tell a
decoded value from a measured-out-of-domain claim. Review 8399 established the set as a **measured
out-of-domain / stand-in set**, not a set of UNKNOWNs.

The measurement is the fleet census, re-read from `Research/JC3Grab/LIGHT_SYSTEM.json` →
`module.value_census` (every shipped `VehicleDynamicLights` entry, **3,217** rows):

| member | our value | shipped census | rows at the shipped maximum |
|---|---:|---|---:|
| `range` | **60.0** (rows 2, 10) | buckets 0.1 … **50** | 66 at 50 |
| `angle` | **70.0** (rows 2, 5, 9, 10) | buckets 10 … **50** | 74 at 50 |
| `multiplier` | 1.0 | 2,188 at 1 | fleet mode, not a decode |
| `falloff_start` | 0.8 / 0.0 | 2,210 at 0.8, 744 at 0 | shipped value, wrong quantity |

So the census **cannot** prove the domain: nothing shipped reaches past 50 m or 50°. It cannot
disprove it either — 60 and 70 are legal floats. That is exactly why the honest label is
"out-of-domain claim", not "decoded" and not "UNKNOWN".

The other three items were also stand-ins rather than decodes:

- **`multiplier 1.0`** is the fleet mode (2,188 of 3,217). BmAK's `Brightness` is **0.15** and no
  Brightness → multiplier bridge exists; the value is a look-alike.
- **`falloff_start 0.8`** is not BmAK's falloff. BmAK's is a spot exponent (1.0 / 2.0); JC3's is the
  fraction where falloff starts — a different quantity.
- **Row 11 (`T-L17`)** keeps the donor graph object's own numbers (`radius 10`, `spot_angle 60`,
  `volume_intensity 0.25`) because no plan gives the row values. Its 60° cone is also outside the
  shipped set (`angle` 60 ships 0 times), and `volume_intensity` 0.25 ships 0 times — so it is
  donor-carried **and** out of domain, and saying "translated" would invent a bridge.

Unchanged, and deliberately so: `T-L28`/`T-L30` remain blocked (null socket **and** null bone, no
`_LIG` node and no `CarLight` block on the body part); the underglow is deliberately absent (BmAK
ships no underglow; its low accent is an emissive wheel material); the lamp-bound flare sprite
cannot be attached (no effect member on a lamp, `T-24`); the forensics entries stay
behaviour-`None` carriers on the body, so no forensics rig was added.

## 2. The change

Four files, all generator-owned or generated:

| file | change | why this file |
|---|---|---|
| `Tools/scripts/bm_rc4_lights.py` | new `MARKS` table (keyed by the same stable `(origin, t18_rows)` key as `OVERRIDES`), `beam_claim()`, `domain_ledger()`; `plan()` attaches `rows[].claim` and `domain`; `--check` re-reads the census and the packed rows | it is the D-03 generator; the row plan must carry the label, not a note beside it |
| `Working/Lights/bm_rc4_lights.json` | regenerated: each of rows 2/5/9/10 carries `claim.status = "out-of-domain"`, row 11 `claim.status = "donor-carried"`, plus the top-level `domain` block (census, shipped maxima, per-member labels, verdict) | the build's own light ledger |
| `Tools/scripts/v05_looks.py` | reads the D-03 ledger; 4 new oracles; new Q-1 line `Q1-7b` (`status = out-of-domain`); header counts a third status; new "Out-of-domain claims" section | `PREDICTIONS_LOOKS.md` is generated, so the label must live in the generator |
| `Working/Q/PREDICTIONS_LOOKS.md` | regenerated: **35 lines — 25 predicted, 1 out-of-domain, 9 UNKNOWN** | the pre-test look sheet |

The new line, verbatim:

> `Q1-7b` | D-03 lights ledger, LIGHT_SYSTEM census | beam rows 2/10: range 60 m, angle 70 deg
> (rows 5/9 also 70 deg); multiplier 1.0 and falloff 0.8/0.0 are stand-ins; row 11 (T-L17) is
> donor-carried | the beam lights the road at 60 m and the 70 deg cone renders; if it clips at 50 m
> or reads as a hard circle, the claim fails and the plan's fallback 50/50 applies | out-of-domain

Rows 5 and 9 are labelled too: they take the same 70° cone from the same plan, so leaving them
unmarked would have been the same error on quieter rows. Their `range` 18 m is **not** labelled —
18 ships (2 rows) and is a straight 1800 cm ÷ 100 conversion.

## 3. Checks

```
$ python -        # pre-flight: re-encode the new plan next to the existing build
rows 24 bytes 7105 byte-identical to build: True
census entries 3217 max {'range': 50.0, 'angle': 50.0}
PREFLIGHT_EXIT=0

$ python Tools/scripts/bm_rc4_lights.py --write
module ..._lights.vmodc: 6337 -> 7105 B (+768), 24 rows
bm-RC4-lights: .ee 11179037 B, .toc 60806 B / 604 records, module record offset 16499504 / 7105 B
WRITE_EXIT=0

$ python Tools/scripts/bm_rc4_lights.py --check
rows   24 (24 planned)  behaviours {'HeadLight': 15, 'TailLight': 3, 'None': 4, 'Reverse': 2}
module 7105 B 01405084AEFE1DDF..., .toc record 16499504/7105, .ee 11179037 B
domain 5 marked rows {'out-of-domain': 4, 'donor-carried': 1}; fleet census 3217 entries,
       shipped max range 50.0 m / angle 50.0 deg
R7     files other than the lights module changed: 0
PASS: every entry names a lit part, the plans' numbers are in the built module, and only the
      lights module differs from the base tree
CHECK_EXIT=0

$ python Tools/scripts/v05_looks.py --write   # 31/31 oracles, wrote the doc
$ python Tools/scripts/v05_looks.py --check
31/31 oracles pass
PASS document: PREDICTIONS_LOOKS.md matches the regenerated text
V05_CHECK_EXIT=0
```

What the checks now enforce, so the labels cannot rot:

- the stored `domain` block equals a fresh derivation, and the stored rows (labels included) equal
  the re-derived ones;
- the census's shipped maxima are still **50.0 / 50.0** — a changed census fails the check rather
  than leaving a stale label;
- every `out-of-domain` label must ship **0** times and every `stand-in` must ship **> 0** times in
  the census; a value that starts shipping turns the check red with "relabel it";
- every labelled row's value is re-read from the **packed `.ee`'s** module and must equal the
  claimed number; row 11 must resolve to `T-L17` and be `donor-carried`;
- the module is byte-identical to a fresh re-encode, and its `.toc` record is still
  **offset 16,499,504 / size 7,105**, equal to the `.ee` directory entry and the module's length;
- `CarLight` census unchanged: 24 blocks over 8 lamp parts; R7: 0 files other than the light
  module differ from `bm-RC4-parts`.

`Builds/bm-RC4-lights` was regenerated from the plan (the rebuild reproduced the same module
sha256 `01405084AEFE1DDF…` and the same offset/size), so the ledger, the receipt and the tree agree.

## 4. Revert

As briefed: revert `Working/Lights/bm_rc4_lights.json` **and** `Builds/bm-RC4-lights`; the module
is regenerated from the plan. Because the labels are generator output, reverting the JSON alone is
not durable — a `--write` would put them back. To revert the labelling itself, drop `MARKS` /
`domain_ledger()` from `Tools/scripts/bm_rc4_lights.py`, then `rm -rf Builds/bm-RC4-lights` and
re-run `--write` (same module bytes, no `claim`/`domain` keys). For `PREDICTIONS_LOOKS.md`, drop the
`RCLIGHTS` oracle block, `Q1-7b` and the out-of-domain section from `Tools/scripts/v05_looks.py`,
then re-run `--write`. Nothing in the game folder was read or written (`installed: false`).

## 5. Limits

- The census counts **values shipped in the module**, not pixels. It settles that 60 m / 70° is
  unshipped; it cannot settle that the engine renders it. Only the one night look named in U-1 can,
  and until it does the row stays a claim.
- Which side the renderer reads (module vs `.epe` `SVehicleLight`) is still UNKNOWN (`U-4`), so the
  claim is about the module's numbers only.
- `multiplier` remains a look-alike: a side-by-side against BmAK's Brightness 0.15 lamp is the only
  thing that would turn `stand-in` into a decode, and no such bridge is documented in the install.
- Row 11 stays a donor value on purpose. Nothing in this correction makes it a translation, and the
  report reads that way.

Updated by review 8399: the 60 m / 70 deg values, the Brightness→multiplier gap and the donor
row 11 are a measured out-of-domain / stand-in set, recorded as such here and in the two ledgers.
