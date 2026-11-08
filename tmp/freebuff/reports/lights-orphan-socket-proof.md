# Lights orphan sockets — proof that `HeadLight1c` / `HeadLight2c` are absent

STATUS: done — **both names are absent from the shipped mesh.** Definite answers, not UNKNOWN: neither is a
`SkeletalMeshSocket` in any decoded cooked mesh, neither is a bone, neither is in the built light manifest;
both exist only as archetype light-entry references, and they are exactly the two flare rows T-L28 and T-L30.
Deliverable: `Working/Lights/ORPHAN_SOCKETS.md`.

## Answer

| name | in the shipped mesh? | present where | first byte offset | rows that point at it |
|---|---|---|---|---|
| `HeadLight1c` | **NO** | `LIGHTS.json` (6 entries, 3 packages) → `LIGHT_SOCKETS.json` `.missing[]` → `SOCKETS_JC3.json` `.orphan_light_refs[]` | 58904 in `LIGHTS.json`; 1323 in `LIGHT_SOCKETS.json`; 4795 in `SOCKETS_JC3.json` | **T-L28** (`sportsmuscle_body` · no anchor, orphan socket) |
| `HeadLight2c` | **NO** | same chain | 63257; 1629; 5073 | **T-L30** (same anchor cell) |

## Files searched (all of them, with the count)

| file | size | 1c | 2c |
|---|---:|---:|---:|
| `Research/BatmobileGrab/SKINS.json` — cooked `Sockets` arrays, `Playable_Batmobile_SF` + 3 showcase skins | 701,523 B | **0** | **0** |
| `Research/BatmobileGrab/BONES.json` — 180 bones | 397,600 B | **0** | **0** |
| `Working/Appearance/build_lights/lights_manifest.json` — built manifest | 100,768 B | **0** | **0** |
| `Research/BatmobileGrab/LIGHTS.json` — 101 archetype light entries | 275,931 B | 6 | 6 |
| `Research/BatmobileGrab/LIGHT_SOCKETS.json` | 62,867 B | 6 (all `.missing[]`) | 6 (all `.missing[]`) |
| `Research/BatmobileGrab/SOCKETS_JC3.json` | 69,890 B | 3 (all `.orphan_light_refs[]`) | 3 (idem) |
| `Research/BatmobileGrab/SOCKETS_JC3.md` / `LIGHT_SOCKETS.md` / `LIGHTS-sockets.md` | — | listed as orphans | listed as orphans |
| JC3 donor mesh socket list | — | **no such file exists in the repo** | idem |

The HeadLight vocabulary actually decoded in the mesh: `HeadLight1`, `1a`, `1b`, `2`, `2a`, `2b` — all on
`Winch_DOOR_Mesh` at the nose/door, coordinates `-0.452,0.694,-2.977` … `0.416,0.612,-3.007`
(`SOCKETS_JC3.md:62-67`). There is **no third "c" socket** in either triple.

## The two rows

`Working/Translation/T_ROWS.jsonl`:

```
T-L28 | `HeadLight1c` VEHLT_HeadLight → HeadLight
   socket/cell: `sportsmuscle_body` · no anchor (orphan socket)
   why: socket and bone are null (`LIGHTS.json` problems); the carrier is the donor's body-hosted `HeadLight`
        pattern (rows 3/10 at `dashboard_LIG`/`front_primary_LIG`) and our body has no `_LIG` node with
        0 `CarLight` blocks in the 25 assembled RBMs … so it waits on B-03 (block)
T-L30 | `HeadLight2c` VEHLT_HeadLight → HeadLight
   socket/cell: `sportsmuscle_body` · no anchor (orphan socket)
   why: same body-hosted pattern and the same missing `_LIG` node + `CarLight` block as T-L28 … waits on B-03/B-04
```

B-25 (`GRAB_BACKLOG.md:1587-1607`) asks for exactly this: "Prove the two orphan sockets (`HeadLight1c`,
`HeadLight2c`) are absent from the shipped mesh before authoring anything on them", and its done-line
requires "the two orphan sockets are recorded absent". That condition is now met by
`Working/Lights/ORPHAN_SOCKETS.md`.

## Consequence for the body-hosted light pattern

The two entries carry no position (`socket` set, `bone: None`, `recorded: None`, `table: None`), so a build
cannot hang a flare on them. The pattern B-25 names instead is part-side: a `CarLight` block on the body part
(or `has_lights = 1`), the technique the wheel-arch recipe uses (G2-33 §7). That carrier never resolves a
socket name, so the missing 1c/2c do not block it; what blocks it on our side is the build state T-L28/T-L30
record — **0 `CarLight` blocks in the 25 assembled RBMs and no `_LIG` node**, i.e. B-03/B-04.
Substituting `HeadLight1b`/`2b` for the orphans would be a name swap with nothing to validate it against (the
six real sockets are door/nose sockets; the orphans have no recorded location), so this proof explicitly does
not authorise that.

## Commands run, verbatim

```
$ sed -n '1587,1607p' GRAB_BACKLOG.md                    # B-25 card
$ grep -n -B2 -A2 "HeadLight1c\|HeadLight2c" tmp/freebuff/reports/LIGHTS-sockets.md
  37:## Socket missing (6 rows, all `HeadLight1c` / `HeadLight2c`)
  39:`HeadLight1c` and `HeadLight2c` appear in **none** of the four cooked tables.

$ python - <<'EOF'   # byte scan of the six JSONs
  Working/Appearance/build_lights/lights_manifest.json  (100768 B)  HeadLight1c:0@-  HeadLight2c:0@-
  Research/BatmobileGrab/SKINS.json                     (701523 B)  HeadLight1c:0@-  HeadLight2c:0@-
  Research/BatmobileGrab/LIGHTS.json                    (275931 B)  HeadLight1c:6@58904  HeadLight2c:6@63257
  Research/BatmobileGrab/BONES.json                     (397600 B)  HeadLight1c:0@-  HeadLight2c:0@-
  Research/BatmobileGrab/LIGHT_SOCKETS.json             ( 62867 B)  HeadLight1c:6@1323  HeadLight2c:6@1629
  Research/BatmobileGrab/SOCKETS_JC3.json               ( 69890 B)  HeadLight1c:3@4795  HeadLight2c:3@5073
  HeadLight* vocabulary per file:
    SKINS.json / lights_manifest.json: HeadLight1, 1a, 1b, 2, 2a, 2b
    LIGHTS.json / LIGHT_SOCKETS.json / SOCKETS_JC3.json: … plus 1c, 2c (referenced, never resolved)
EOF

$ ls Research/JC3Grab | grep -i socket ; ls Working | grep -i socket     # both empty: no donor socket list on disk
```

## UNKNOWNs

1. **Why the archetype references names no mesh carries** — not decided; the same gap `LIGHT_SOCKETS.md`
   UNKNOWN 3 records.
2. **The MK2 / Joker / Funhouse cooked socket tables** are undecoded, so those three meshes' socket content
   beyond "the archetype names them" is unverified. SKINS.json's four tables are the whole decoded set.
3. **The JC3 donor's own socket list** is absent from the repo; nothing here claims the donor lacks the
   names, only that no placement row exists for them.

## Change record

- **Intended change:** none to game data or build inputs — this is a proof document plus its DONE report.
- **Files written:** `Working/Lights/ORPHAN_SOCKETS.md`, `tmp/freebuff/reports/lights-orphan-socket-proof.md`.
- **Why these files:** the brief names both paths.
- **Revert:** delete the two files. Nothing else was touched; no game, no build.
