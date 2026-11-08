# Independent review - G2-19 (Driver seat and pose)

Reviewer: independent (did not author the card). Mode: read-only - `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` and every game path untouched; this file is the only one written. No game
launched, nothing committed.

Card: `GRAB_BACKLOG.md` §2.3 "G2-19 · Driver seat and pose · S · deps: G2-18, G1-19".
Row: `GRAB_BACKLOG.md:1302` (`done`). MODLOG: intended change `:11450`, done `:11544`.

## VERDICT

**minor issues.** The card answers its Done clause with real decoded evidence and every number I
spot-checked is correct. Two things keep it off "sound":

1. `jc3seat.py --check` has **no invariants**. It regenerates the md/json and compares them
   byte-for-byte with what is on disk, so it fails only if the files are stale - never if a
   derived value is wrong. The card's Done claim ("candidate fits the `Driver` hip") is therefore
   not verified by the Done command at all; it is verified by this review, by hand.
2. The method that produces the headline candidate - "a seat's height is its hull box centre" -
   is justified in the doc by the very agreement it is used to claim (`10 mm from the hip`), with
   n = 2 vehicles. That is an inference presented as method (R4), and one sentence built on it
   ("JC3's car seats ship at one height whatever the class") overstates a 3-part sample.

## Check output (verbatim)

```
$ python Tools/scripts/jc3seat.py --check
PASS: 34 driver points | 40 pose classes (382 clip names) | 36 MOD selectors | seat boxes 4 | candidate v0300_car_kensington_sportsmuscle (10 mm from the hip), json match True, md match True
exit=0
```

Outputs named in the row all exist:

```
-rw-r--r-- 1 User 197121 41458 Oct 28 03:41 Research/JC3Grab/SEAT.json
-rw-r--r-- 1 User 197121 14634 Oct 28 03:41 Research/JC3Grab/SEAT.md
-rwxr-xr-x 1 User 197121 28385 Oct 28 03:40 Tools/scripts/jc3seat.py
```

`Research/JC3Grab/README.md` has the promised section (`:745`) and Files row (`:939`).

## Issues

### 1. `--check` is a staleness test, not a check (the Done criterion is unguarded)

`jc3seat.py:531-556`: the only assertions are `os.path.exists` and `disk != text` for the two
files. There is no `invariants()` and no expected-value table, unlike the sibling cards
(`jc3moving.py` asserts table row counts and proof rules; `jc3emp.py` asserts every pulse/tune
value). Consequences:

* The md's `10 mm` cell, the `34` driver points, the `382` clips and the seat heights would all
  regenerate cleanly if the derivation were wrong - `PASS` means "the files match a fresh build",
  not "the numbers are right".
* The card's Done clause - "a candidate pose that fits the Batmobile's `Driver` socket height
  (G1-19)" - has no machine form. A regression that moved the candidate to a 500 mm delta would
  still print `PASS … (500 mm from the hip)`.

This is the review's main finding: the Done check looks green but tests only that the files were
written by the current code.

### 2. Circular justification of the seat-height method (R4)

`SEAT.md:124-127` and the tool docstring (`jc3seat.py:18-21`): "The donor's seat-box centre sits
10 mm from the Batmobile's `Driver` socket hip, **which is what makes the box centre a usable seat
height**". The 10 mm agreement is the *result* the method is supposed to establish, and it is a
single-vehicle coincidence (the two `v0300` boxes are the left and right of one car). A hull box
centre being a seat height is an assumption - a hull spans cushion to headrest, so its centre
depends on the model, not on the seat surface. It is a reasonable assumption and the doc is
transparent that the comparison quantity is the centre; it is not transparent that the method is
chosen *because* it lands near the target. Under R4 the pairing is `inferred`, and a 10 mm match
between an assumed proxy and a measured hip should be reported as "the proxy happens to agree",
not as validation.

### 3. "JC3's car seats ship at one height whatever the class" overstates the sample

`SEAT.md:140-141` (template `jc3seat.py:415-416`): the three `Land_Seat` parts are
0.855 / 0.855 / 0.894 m, "a span of 39 mm". But two of the three are the left and right seat of the
**same car** (`sportsmuscle_f_l_seat`, `_f_r_seat`), so the evidence is **two vehicles**: one
muscle car at 0.855 and one hot hatch at 0.894. That is not "whatever the class" - it is one
observation per class. The tank and the supercar contribute nothing (no seat part / no hull), so
the sentence generalises from n=2. Reword to "the two shipped cars with a seat hull sit within
39 mm of each other" and the claim is safe.

### 4. Typed numbers in the generated doc (R11)

Three counts in `SEAT.md` are literals in the template rather than values from the build:

| text | line | derivable from |
|---|---|---|
| "container holds 31 `.vmodc` modules and the fleet's module vocabulary is 52 types" | `SEAT.md:19` (`jc3seat.py:344`) | `len(entity["modules"])`, the fleet type census |
| "a span of 39 mm" | `SEAT.md:141` (`jc3seat.py:416`) | the three `centre_m[1]` values in `SEAT.json` |
| "0.865 m" in §7 item 4 | `jc3seat.py:484` | `driver_socket.position_m[1]` |

All three are correct today (31 modules, 52 fleet types, 0.8647 hip), so `--check` passes - which
is exactly the failure mode R11 exists for. The rest of the doc's numbers are computed
(`382 = sum(clips[*].count)`, `40 = len(clips)`, `34 = points.count`, `183` selectors, `4` boxes).

### 5. §7 has two items numbered 4

`SEAT.md:199` and `:203`: "4. **The supercar's seat hull.**" and then again "4. **Whether the
Batmobile's hip …**". Cosmetic, but this is the UNKNOWN list a later card will cite by number.

### 6. "3 skeleton files in total" is imprecise

`SEAT.md:13` / MODLOG `:11571`: the index has **3 files under `jc_skeletons/`** but only **one**
is a `.bsk` (`characters/gen_male.bsk`); the other two are `.hikcc`. The machine file records both
counts faithfully (`card_inputs`: `jc_skeletons/` 3, `jc_skeletons/vehicles/` 0), so the doc's
sentence is a wording slip, not a data error - and the card's substantive claim (`0`
`jc_skeletons/vehicles/*.bsk`, none for vehicles) is confirmed below.

### 7. The JSON cannot explain its own null row

`SEAT.json` `seats[2]` is `{"vehicle": "v0401_car_mugello_racingsupercar"}` and nothing else: no
`part`, no reason. The md explains ("no compound instance carries its index 19 or 22"), but a
consumer reading the machine file sees a bare vehicle row and cannot tell "no hull" from "not
attempted". A `reason` field would make the absence auditable.

## Spot-checks

| # | value in the doc | verified against | result |
|---|---|---|---|
| 1 | 34 driver-named objects, prefixes entry 10 / exit 14 / interaction 1 / point 3 / transition 4 / trigger 2 | `SEAT.json` `points.count` = 34, `points.rows` = 34 | match |
| 2 | 40 pose classes, 382 clip names | `SEAT.json` `len(clips)` = 40; `sum(clips[*].count)` = **382** | match |
| 3 | seat heights 0.855 / 0.855 / 0.894 / tank hatch 2.879, candidate 10 mm from hip | `SEAT.json` `seats[]`: 0.8551, 0.8550, 0.8941, 2.8787; `candidate.nearest.delta_m` = **0.0096**; hip `0.864732` | match |
| 4 | "donor container holds 31 `.vmodc` modules" | decoded donor entity: `len(modules)` = **31**, 26 types in that entity | match |
| 5 | "the fleet's module vocabulary is 52 types" | census over 232 decoded entities: **52** distinct module types, none seat/pose/animation (the one regex hit, `ExtendedExposedVariables`, matches "pose" inside "Exposed") | match |
| 6 | "0 `jc_statemachine/vehicles/*`; 0 `jc_skeletons/vehicles/*.bsk`; 142 state-machine files; 7 vehicle `.ban`; 2 rico/vehicle `.ban`" | `INDEX.jsonl` (81,952 rows): `jc_statemachine/` 142, `jc_statemachine/vehicles/` **0**, `jc_skeletons/vehicles/` **0**, `/vehicle/*.ban` **7**, `/rico/vehicle/*.ban` **2** | match |
| 7 | "4 seat boxes" | `SEAT.json`: 5 rows, 4 with `centre_m` | match |
| 8 | 36 MOD selectors, 183 vehicle states, 9 seat conditions, 4 IK targets | `SEAT.json` `selectors`: mods 36, states 183, seats 9, ik 4 | match |
| 9 | "v0201's only candidate is `mediumtank_hatch`, class `Land_Door`, 2.879 m" | `SEAT.json` row: part `mediumtank_hatch`, `part_class` `Land_Door`, centre y 2.8787 | match |

## What holds up

* The card's central finding is well evidenced and behaviour-first: the vehicle carries the
  *attach* (`entry.driver` + 33 siblings with state strings) and the *character* carries the pose
  (`rico_base.afsmb` conditions/IK/MOD selectors over `rico_base.asb` clip paths). It explicitly
  refuses to claim a clip: "This is a candidate, not a decision" (§4), and §7 item 1 records the
  vehicle→class mapping as UNKNOWN rather than inferring it from the entity name.
* The two card "In" items that do not exist are reported with counts (0 `jc_statemachine/vehicles`,
  0 `jc_skeletons/vehicles`) instead of being quietly dropped - the right handling of a wrong
  input list.
* `v0201` is handled honestly: `mediumtank_hatch` is a `Land_Door`, so its 2.879 m is a door roof
  and the tank's seat height stays UNKNOWN. This is the R5 trap (a member whose name suggests a
  seat) avoided on the record.
* `v0401`'s missing hull is reported with the two candidate indices, not smoothed over.
* The two self-bugs recorded in MODLOG (substring `seat`/`hatch` matching `racinghothatch`;
  U+2212 minus signs) show the numbers were audited before shipping.

## Limits of this review

* Read-only, so I did not tamper with `SEAT.json`/`SEAT.md` to re-test the failure mode.
  `MODLOG.md:11598-11601` records both tamper attempts failing with `SEAT.json stale` / `SEAT.md
  stale` and exit 1, and a restore returning PASS - consistent with `main()` as written.
* I did not re-decode `rico_base.asb`/`.afsmb` (2.6 MB / 327 KB inside the archives); the clip
  counts are checked against `SEAT.json`, which is the artifact the card publishes, not against the
  container bytes. The 183-state/36-selector split therefore rests on the card's own decode.
* The claim that no compound instance carries `v0401`'s seat index (19 or 22) was not re-derived
  from the `.physicsc`; I confirmed only that `SEAT.json` has no hull row for that vehicle.
* "Which of `car/low`, `car/med`, `car/circuit` plays" is untestable from files; the card's
  UNKNOWN there is correct and is the phase-Q item.
