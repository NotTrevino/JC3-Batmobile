# LIGHTS-sockets — re-check of LIGHTS.md's socket → bone step

**STATUS: DONE.** `Tools/scripts/bmak_light_sockets.py --write` and `--check` both exit 0, **8/8
oracles pass**, and the stored `Research/BatmobileGrab/LIGHT_SOCKETS.md` / `.json` are byte-identical
to a fresh recompute.

Reviewed card: `Research/BatmobileGrab/LIGHTS.md`. Inputs (never edited):
`LIGHTS.json` (101 entries, 21 distinct sockets, 4 packages), `SKINS.json` (cooked `Sockets`
arrays: name → `bone`, `location_uu`), `BONES.json` (180 bones with bind transforms). All reads are
of the project's own decoded JSON; no game process was started.

## The premise needed one correction, and it changed the method

The card says "248 sockets". The 248 is SKINS.md's **total socket records across all tables**; the
distinct socket names in the four tables are **66**, and the 21 names LIGHTS.md uses are all among
them. More important: **the four cooked tables disagree with each other** about the same socket
name, so a socket read from one mesh cannot verify a light of another package. My first pass
borrowed the `playable` table for packages that have none, which produced a bogus
`314 cm` delta and a bogus bone (`Winch_DOOR_Mesh`) for HeadLight1 on three packages. That pass was
discarded rather than published: the script now scores a row **only** against its own package's
table, and lists the rest as unverified.

## Coverage (101 rows, unchanged totals)

| package | entries | verified in own table | socket missing | no table for | bone differs | bone not in rig | > 1 cm |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Playable_Batmobile_SF` | 28 | 26 | 2 | 0 | 0 | 0 | 0 |
| `Playable_BatmobileMK2_SF` | 28 | 0 | 2 | 26 | 0 | 0 | 0 |
| `Playable_BatmobileJoker_SF` | 17 | 0 | 0 | 17 | 0 | 0 | 0 |
| `Playable_BatmobileFunhouse_SF` | 28 | 0 | 2 | 26 | 0 | 0 | 0 |

`SKINS.json` decodes tables for `Playable_Batmobile_SF` and the three `Showcase_Batmobiles_*` skins.
The `Playable_BatmobileMK2/Joker/Funhouse_SF` packages LIGHTS.md covers are **not** those showcase
packages, so **73 of 101 rows are unverified**, not verified-wrong. Substituting showcase data was
rejected for the reason in the next section.

## Socket missing (6 rows, all `HeadLight1c` / `HeadLight2c`)

`HeadLight1c` and `HeadLight2c` appear in **none** of the four cooked tables. Every other socket
resolves in at least one table, so these two names are absent from the meshes SKINS.json decoded.

## Position check (26 verified rows)

Both interpretations of LIGHTS' `socket_location` are measured and the data chooses:

| interpretation | median error |
|---|---:|
| raw socket offset vs recorded | **0.000 cm** |
| world point (`bone.bind + R·offset`) vs recorded | 312.400 cm |

Chosen: **raw**. **0 rows exceed 1 cm.** But this is a **consistency** result, not independent
confirmation — LIGHTS.md was built from the same `SKINS.json` arrays, so 0.000 cm says the card
copied its source faithfully, and that its numbers are raw socket-relative vectors rather than world
points. The position check cannot detect a wrong parent bone, because a wrong bone does not move the
raw offset.

## The finding that is not circular: 6 sockets have different parents in different meshes

| socket | `playable` | `standard` | `mk2` | `jokerfied` | LIGHTS bones |
|---|---|---|---|---|---|
| `HeadLight1` | `Winch_DOOR_Mesh` | `Winch_DOOR_Mesh` | `Batmobile_Chassis` | `Batmobile_Chassis` | `Winch_DOOR_Mesh` (playable), `Batmobile_Chassis` (other 3) |
| `HeadLight1a` | `Winch_DOOR_Mesh` | `Winch_DOOR_Mesh` | `Batmobile_Chassis` | `Batmobile_Chassis` | `Winch_DOOR_Mesh` / `Batmobile_Chassis` |
| `HeadLight1b` | `Winch_DOOR_Mesh` | `Winch_DOOR_Mesh` | `Batmobile_Chassis` | `Batmobile_Chassis` | `Winch_DOOR_Mesh` / `Batmobile_Chassis` |
| `HeadLight2` | `Winch_DOOR_Mesh` | `Winch_DOOR_Mesh` | `Batmobile_Chassis` | `Batmobile_Chassis` | `Winch_DOOR_Mesh` / `Batmobile_Chassis` |
| `HeadLight2a` | `Winch_DOOR_Mesh` | `Winch_DOOR_Mesh` | `Batmobile_Chassis` | `Batmobile_Chassis` | `Winch_DOOR_Mesh` / `Batmobile_Chassis` |
| `HeadLight2b` | `Winch_DOOR_Mesh` | `Winch_DOOR_Mesh` | `Batmobile_Chassis` | `Batmobile_Chassis` | `Winch_DOOR_Mesh` / `Batmobile_Chassis` |

The locations differ as well, and the two candidate points are each unique to their family:

- `Winch_DOOR_Mesh` at `(21.287, 45.193, -44.250)` — `playable`, `standard`;
- `Batmobile_Chassis` at `(320.680, 38.578, 51.000)` — `mk2`, `jokerfied`.

Neither point appears under any other socket name in any table, so this is **not** an off-by-one
name/offset shift inside one array; the two mesh families genuinely record different socket data for
the same name. LIGHTS.md inherits the split exactly: its `Playable_Batmobile_SF` rows say
`Winch_DOOR_Mesh`, its MK2/Joker/Funhouse rows say `Batmobile_Chassis` for the same socket name and
the same raw offset.

That matters for translation: a light entity resolves its socket **by name**, so on the playable car
the headlights hang off the winch-door bone at a point 44 cm *below* the car origin and 21 cm back,
whereas on the other three they hang off the chassis 3.2 m forward at 51 cm up. One of the two
attributions is wrong, and a wrong parent moves the light's world position by the distance between
the two bones — which is exactly the failure the "> 1 cm" test cannot see.

## What the oracles cover, and what they do not

`--check` re-runs all 8 (each is listed with its evidence in `LIGHT_SOCKETS.md` §Oracles):

1. 101 entries / 21 sockets / 4 packages parse;
2. 101 rows = 26 scored + 6 missing + 69 no-table + 0 bone-not-in-rig (accounting is total);
3. every scored row compares the cooked `BoneName` with LIGHTS' bone (26/26 agree — see the caveat
   above: it agrees because both come from the same table);
4. every socket bone is one of BONES.json's 180 (0 outside the rig);
5. both position interpretations measured, smaller-median chosen;
6. no row is scored against another package's mesh;
7. all six orphan-flagged rows are unresolved and listed;
8. the cross-mesh tables are compared, not merged (6 conflicts found).

## UNKNOWNs

1. **Which headlight parent is correct.** The cooked tables disagree and this card does not decide;
   it establishes that the disagreement is real and that LIGHTS.md inherited it.
2. **Socket data for `Playable_BatmobileMK2/Joker/Funhouse_SF`.** No table was decoded for those
   three packages; their 73 rows stay unverified. Decoding those packages' own `Sockets` arrays is
   the next step, not a substitution.
3. **Why `HeadLight1c` / `HeadLight2c` exist as sockets in LIGHTS.md but in no decoded table.** Not
   claimed; possibly a name in a mesh SKINS.json did not cover.

## Reproduce

```
uv run python Tools/scripts/bmak_light_sockets.py --write
uv run python Tools/scripts/bmak_light_sockets.py --check
```
