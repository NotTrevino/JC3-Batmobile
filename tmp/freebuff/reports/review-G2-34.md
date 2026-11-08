# Review — G2-34 · Tether, airlift and winch carriers

Reviewer: independent (not the card author). Read-only: nothing in `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/`, `Tools/` or the game was modified. Only this file was written.

- Card: `GRAB_BACKLOG.md:815` (Out = `Research/JC3Grab/TETHER.md`; Done = "WLD-7 has values;
  WPN-6 has a carrier or a proven absence")
- Row: `GRAB_BACKLOG.md:1317`
- MODLOG done section: `MODLOG.md:10918`
- Outputs: `Research/JC3Grab/TETHER.md` (264 lines), `Research/JC3Grab/TETHER.json` (2,513
  lines), `Tools/scripts/jc3tether.py` (678 lines), plus the README section at
  `Research/JC3Grab/README.md:689` and the Files row at `:943`

## VERDICT

**minor issues** — the card's two answers are supported by the data I re-read independently
(the mass census with its stated UNKNOWN unit, the 12 cargo bays, the compound cargo-tank
entity, the absence of any tether tune, the winch geometry with no mechanic). The problems are
local and fixable in the prose plus one line of the script: one attribution is factually wrong
(`tether_tear7` is on the train flatbed, not "one truck"), two headings claim more than the
section bodies admit, one headline number is a hard-coded literal that `--check` can never
falsify, four numbers in the prose are typed rather than derived, and the "no vehicle part can
pull another vehicle" conclusion is not reconciled with the wagon-coupling behaviours the same
paragraph prints. Nothing here invalidates the WPN-6 "carrier, no mechanic" answer or the
WLD-7 mass table.

## Check output (verbatim)

Command: `python Tools/scripts/jc3tether.py --check`

```
PASS: 232 masses (donor 975, target 6000, 1 multi-body), bays 12 on 12 entities / 0 helicopters, hooks 33 on 3 entities, compound 1, rope/winch parts 40 (10 names) + 12 winch LODs, tether-ish module types 0/53, winch classes 0, index tether 335 (7 non-dialogue) / winch 0
```

Exit status: 0. This matches the string quoted in the MODLOG done section word for word (the
MODLOG block wraps it over four lines; the real output is one line — cosmetic only).

Every Out path exists: `Research/JC3Grab/TETHER.md` (264 lines, as the MODLOG says),
`Research/JC3Grab/TETHER.json`, `Tools/scripts/jc3tether.py`. The card names only the `.md`; the
`--check` needs the `.json` as well, and the §12 row lists only the `.md`, unlike the sibling
rows (`G2-27`, `G2-28`, …) that name both.

## Issues

1. **`Research/JC3Grab/TETHER.md:142` — wrong entity for `tether_tear7`.** "`tether_tear`,
   `tether_tear7` and `tether_yank` … are object names on the loose cargo of one truck." Direct
   scan of the `.epe` graphs: `tether_yank` x2 + `tether_tear` x2 are on
   `v0505_car_solar_oldtruck_commercial_cargo_random` (the truck), but `tether_tear7` x2 is on
   `v5602_train_urga_monorailflatbed_military_containers_rigidobject` (the train flatbed
   container). The six names are on **two** entities of **two different vehicle families**, not
   one truck. The table directly above (lines 118-122) already shows three entities, so the
   prose also contradicts its own table. `README.md:705-707` repeats the same grouping.

2. **`TETHER.md:116` — "a cargo truck" for two truck entities.** The table under it lists
   `…_cargo_barrel` **and** `…_cargo_random`. The count "3 entities" is right; the description
   silently drops one. `README.md:706` drops it too ("a cargo truck's loose barrels and a
   flatbed's container prop").

3. **`TETHER.md:53` — heading "Can a vehicle be carried? Yes - by the cargo plane, boat and
   flatbed" overstates.** The only decoded evidence of a carried vehicle is one plane entity
   (`v4603 … military_cargo_tank`). For the boat (4 bays) and the flatbed (2 of 4 bays) the data
   shows a `CVehicleCargoBay` object and nothing carried, no bay interaction point (the doc says
   so itself at line 88) and no attach rule (§6: UNKNOWN). The body text hedges; the heading does
   not. "Yes for the cargo plane; a bay and no evidence of a carried vehicle on the boat and the
   flatbed" would be the supportable claim.

4. **`TETHER.md:82` — heading "The proof that a vehicle rides in a bay" proves something
   weaker.** What the data proves is that one *entity* contains two vehicle roots
   (`CAirPlane` + `CCar`) and two bodies — a carried vehicle is part of the plane's entity. It
   does not tie that `CCar` to the `CVehicleCargoBay` transform (the bay has 7 members and an
   empty event pair, and §6 of the same doc records "what carries a vehicle into a bay" as
   UNKNOWN). Heading and §6 contradict each other; the heading should say "inside", not "in a
   bay".

5. **`TETHER.md:177` — the conclusion outruns the census it is drawn from.** "None is a winch,
   rope, tow or reel, so no vehicle part can pull another vehicle." The first clause is true of
   the 67 named behaviours; the second is an inference, and the very census the doc prints
   contains `FrontWagonCoupling` 5, `FrontWagonCouplingLinked` 5, `RearWagonCoupling` 12,
   `TrainCargo` 60 and `Elevator` 36 — by name, a wagon coupling *is* a vehicle-to-vehicle
   linkage, and `Elevator` is the exact mechanism §86 bounds the BmAK winch against. Either name
   and dismiss those three behaviours, or weaken the sentence to "no vehicle part is a winch,
   rope, tow or reel".

6. **R5 — three behaviours are read off names, not measured.**
   - `TETHER.md:142-143`: "They mark *which prop may be torn off or yanked*" — inferred from
     `tether_tear` / `CGrapplingHookPropData`; the measured facts are only "empty
     enable/disable events, 5 non-numeric members".
   - `TETHER.md:178-179`: "`CargoBayDoor` - 28 parts that open a bay door and stop" — inferred
     from the behaviour name.
   - `TETHER.md:64-69`: "So the bay carries a name hash and a transform, then stops" — a
     name-derived absence. It is phrased as "no member", which is defensible, but the
     consequence ("no capacity, no mass limit") is a behaviour claim from a member list.
   In each case the honest form is "the member/behaviour is named X; what it does is UNKNOWN" or
   an explicit "no member for Y exists" (the latter is what §2 mostly does correctly).

7. **R4/R11 — `functional_winch_classes: 0` is a literal, not a measurement.**
   `Tools/scripts/jc3tether.py:287` sets `"functional_winch_classes": 0` by hand;
   `:584` asserts that literal against `0`; `:487` prints it into `TETHER.md:180` "Functional
   winch classes anywhere in the fleet: **0**". No scan of class names exists in the script, so
   `--check` would still print 0 if a winch class appeared tomorrow. The number is *true* — I
   scanned all 104 `.epe` classes across the 232 detail graphs and none contains winch / rope /
   tether / tow (the only grapple class is `CGrapplingHookPropData` x33) — but as published it is
   a typed value dressed as a derived one. The neighbouring `bmak` string (`:288`) is also typed
   prose, but it is explicitly labelled "quoted not re-derived", so that one is within the rules.

8. **R11 — four typed numbers in prose under a sentence claiming none are typed.**
   `TETHER.md:4` says "Every number below is re-derived by `--check`", yet:
   - `TETHER.md:30` "plane 40,000 + carried tank 25,000" — both typed into
     `jc3tether.py:328` as a plain string; the payload's `compound_masses` is
     `[25000, 40000]` with no plane/tank labels. The attribution happens to be right (all six
     cargo-plane entities weigh 40,000; only the `military_cargo_tank` entity also carries a
     25,000 body — verified in the raw entity caches), but that evidence is nowhere in the doc or
     the script.
   - `TETHER.md:48` "all 335 `tether` names" — typed; `idx['tether']` exists.
   - `TETHER.md:69` "the same fields on all twelve" — typed 12; `car['bays']` exists.
   - `TETHER.md:107` "all six planes, identical" — typed 6; `len(car['bay_points'])` is 6.
   All four current values match the data; none of them can fail when the data changes, which is
   exactly what R11 is meant to prevent.

9. **`CGrapplingHookPropData` object names look like a decoder default.** 27 of the 33 objects in
   the §3 name table are named `GrapplingHookPropData` (18) or `CGrapplingHookPropData` (9) — the
   name equals the class. The doc presents these as measured object names without a note, and the
   `tether_*` count (6) that `--check` guards depends on this naming. Worth one caveat line: it
   is not established whether these are shipped names or the decoder's fallback, and the six
   `tether_*` objects carry only two distinct `name_hash` values per entity (both
   `tether_yank` objects share 561058116).

10. **Done criterion vs what `--check` verifies.** Done = "WLD-7 has values; WPN-6 has a carrier
    or a proven absence". `--check` verifies the census (232 masses, 12 bays, 33 hooks, 40 parts,
    335 tether paths, 53 module types) plus md/json byte equality. It does not test "WLD-7 has
    values" (half of WLD-7 is UNKNOWN, honestly recorded in §1/§6), and "proven absence" rides on
    the literal of issue 7. As a regression guard the check is strong; as a test of the Done
    sentence it is indirect. The MODLOG should say the green light is a census guard, not a proof
    of the card's Done line.

11. **`MODLOG.md:10918` Done block wraps the check output over four lines** inside the fenced
    block, so a copy-paste of "the exact output" does not reproduce. Cosmetic, but the rest of
    the log's convention is one-line verbatim output.

## Spot-checks

| value in the doc | where I verified it |
|---|---|
| `TETHER.md:55-70` — **12 `CVehicleCargoBay` objects on 12 entities** (6 plane, 4 boat, 2 flatbed), `enabled = 1`, `enable`/`disable` empty, four distinct world transforms counting 4 / 6 / 1 / 1 | Independent scan of `E:/Modding/JustCause3/_grab/detail/*.json`: exactly one `CVehicleCargoBay` per entity on 12 entities; `enable = ''`, `disable = ''`, `enabled = 1` on all 12; the four transform strings and their 4/6/1/1 split match `TETHER.json:carriers.bay_worlds` |
| `TETHER.md:48, 206-214` — **335 `tether` paths, 7 non-dialogue, 0 `winch`**, and the 7 listed paths | Independent scan of `Research/JC3Grab/INDEX.jsonl`: 335 paths containing `tether`, 7 without `dialogue` (the `t_challenge_dual_tether_alpha_dif.hmddsc` decal, the `.gdc`/`.gsc` graph pair, 2 upgrade icons, 2 upgrade videos), 0 containing `winch` |
| `TETHER.md:175-180` — **11,643 part rows, 7,367 `None`, 67 distinct named behaviours, `CargoBayDoor` x28** | Independent scan of `Research/JC3Grab/PARTS_TABLE.jsonl`: 11,643 rows, 67 distinct non-`None` behaviours, `CargoBayDoor` 28 (also surfaced the wagon couplings of issue 5: 5 + 5 + 12) |
| `TETHER.md:30, 43` — compound entity = **40,000 plane + 25,000 tank**, donor 975 = **6.154x**, 15.0 % / 6.0 % / 40.0 % | Raw entity caches: all 6 `v4603_plane_urga_cargotransport` entities 40,000, only `…_military_cargo_tank` also 25,000; 6000/975 = 6.1538, 6000/40000 = 15.0 %, 6000/100000 = 6.0 %, 6000/15000 = 40.0 % |
| `TETHER.md:186` quoted **MODLOG §86 = "elevator bound (>= ~2 t class)"** | `MODLOG.md:4446` "**Elevator lift** bounds the WINCH (force >= elevator + 2 occupants ≈ 2 t"; the doc correctly labels it BmAK and does not transfer it to JC3 |
| `TETHER.md:180` **0 functional winch classes** | Independent scan of `.epe` class names (104 distinct): none contains winch / rope / tether / tow — true, but see issue 7 on how it is produced |

## Not verified

- The tamper test recorded in the MODLOG (`bays` 12 → 13 → `FAIL: TETHER.json stale`; a boat-row
  number → md diff `FAIL`; both restored → PASS) was not re-run, because it requires writing to
  `TETHER.json` / `TETHER.md`, which this review may not touch. The `--check` code path that
  produces those two failures was read (`jc3tether.py:626-645`) and is consistent with the
  recorded messages.
- No archive was opened and no game was launched, per the review rules; every number above comes
  from the decoded caches under `E:/Modding/JustCause3/_grab` and the repo's own JSONL tables.
