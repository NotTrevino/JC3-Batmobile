# lights-rig-vs-sockets - the 18 built bm-RC2 lights entries vs the BmAK rig

## STATUS

**done - the built module has 18 entries and no `socket` member, so the socket name cannot be
looked up on the modules; the parts module (61 parts, 4,071 member paths) has no socket table
either. Colour equals the BmAK `LightColor` printed in LIGHTS.md on 17/18 entries (the single
exception is entry 11 / T-L17, whose built colour is the graph object's own diffuse where the doc
prints the CDO fallback); intensity is equal on 2/18, both coincidences, because the module has
no brightness member and B-07 bridges no unit. `--check` PASS.**

Files written:

- `Builds/bm-RC2/verify/lights_vs_bmak.md` (9,778 B / 9,768 chars - the audit page; the only file written under the build)
- `Tools/scripts/v_lights_rc2.py` (`--write` / `--check`; read-only on the build otherwise)
- `tmp/freebuff/reports/lights-rig-vs-sockets.md` (this card)

Untouched: every byte of `Builds/bm-RC2` except the new `verify/lights_vs_bmak.md`. No game
launched or attached (INSTRUCTIONS §3).

---

## 1. What the checks can see (decoded, not assumed)

| item | value | how |
|---|---|---|
| built module | `aaf/editor/entities/.../modules/generated/batmobile/v0300_car_kensington_sportsmuscle_lights.vmodc` | `jc3adf.walk` |
| entries | **18** | walked `lights[n].behavior` until the path stops |
| members per entry | 25, `socket` **absent** | the walked member-name set |
| module sha256 | `D4E6610B0EA33A77C0B7A6FA6740779E…` | sha256 |
| built parts module | 61 parts / 4,071 member paths, `*socket*` paths **0** | `jc3adf.parts` + walk |
| sockets named by entries | **13 distinct** (T-18, rig `Playable_Batmobile_SF`) | `t14_lights.json` |
| T-18 rows / components | 28 / **36** | T-18 summary |
| LIGHTS.md rig table | 28 rows / **36 components** | counted from the doc, `\|`-aware split |
| anchor bones | 7 distinct, **0** are part names in the build | `deformable_transform` |

So a JC3 lights entry binds a **part**, not a socket: `part`, `part_hash`, `part_index`. The
socket name survives only in the T-18 row that owns the entry and in the anchor's last node
(`|…|<bone>|<bone>_LIG`). The brief's first check therefore has one decoded answer for all 18
entries, and what *is* checkable on the build - the part exists at its index with
`has_lights = 1` and its hash - was checked per entry: **18/18**.

## 2. The 18 entries

| # | behavior | socket(s) | part (index, has_lights) | built colour | BmAK colour | colour equal | built mult | BmAK brightness | intensity equal |
|---:|---|---|---|---|---|---|---:|---|---|
| 0 | HeadLight | `Dashboard_Light` | `sportsmuscle_body` (0, 1) | 172 245 255 | 172 245 255 | yes | 1 | 5 | no |
| 1 | TailLight | `BrakeLightR` | `sportsmuscle_tailstrip_r_r` (49, 1) | 255 38 0 | 255 38 0 | yes | 2 | 1 | no |
| 2 | HeadLight | `HeadLight1`, `HeadLight1a`, `HeadLight1b` | `sportsmuscle_headlight_f_l` (44, 1) | 138 197 246 | 138 197 246 | yes | 2 | -, -, 0.15 | no |
| 3 | HeadLight | `HeadLight2` | `sportsmuscle_headlight_f_r` (45, 1) | 223 91 75 | 223 91 75 | yes | 1 | 1 | yes (coincidence) |
| 4 | HeadLight | `HeadLight1` | `sportsmuscle_headlight_f_l` (44, 1) | 223 91 75 | 223 91 75 | yes | 2 | 1 | no |
| 5 | HeadLight | `HeadLight1` | `sportsmuscle_headlight_f_l` (44, 1) | 138 197 246 | 138 197 246 | yes | 1 | 0.15 | no |
| 6 | HeadLight | `HeadLight2` | `sportsmuscle_headlight_f_r` (45, 1) | 223 91 75 | 223 91 75 | yes | 2 | 1 | no |
| 7 | HeadLight | `HeadLight1` | `sportsmuscle_headlight_f_l` (44, 1) | 223 91 75 | 223 91 75 | yes | 1 | 1 | yes (coincidence) |
| 8 | TailLight | `BrakeLightL` | `sportsmuscle_tailstrip_r_l` (48, 1) | 255 38 0 | 255 38 0 | yes | 2 | 1 | no |
| 9 | HeadLight | `HeadLight2` | `sportsmuscle_headlight_f_r` (45, 1) | 160 180 255 | 160 180 255 | yes | 1 | 0 | no |
| 10 | HeadLight | `HeadLight2`, `HeadLight2a`, `HeadLight2b` | `sportsmuscle_headlight_f_r` (45, 1) | 160 180 255 | 160 180 255 | yes | 2 | -, -, 0 | no |
| 11 | HeadLight | `BattleModeSpotLight` | `sportsmuscle_body` (0, 1) | **154 154 243** | **255 255 255** | **NO** | 1 | 0 | no |
| 12 | HeadLight | `LWheelLight` | `sportsmuscle_wheel_f_l_arch` (42, 1) | 160 180 255 | 160 180 255 | yes | 1 | 0 | no |
| 13 | HeadLight | `RWheelLight` | `sportsmuscle_wheel_f_r_arch` (43, 1) | 160 180 255 | 160 180 255 | yes | 1 | 0 | no |
| 14 | HeadLight | `HeadLight1` | `sportsmuscle_headlight_f_l` (44, 1) | 255 0 0 | 255 0 0 | yes | 1 | 5 | no |
| 15 | HeadLight | `HeadLight2` | `sportsmuscle_headlight_f_r` (45, 1) | 255 0 0 | 255 0 0 | yes | 1 | 5 | no |
| 16 | HeadLight | `LWheelLight` | `sportsmuscle_wheel_f_l_arch` (42, 1) | 255 0 0 | 255 0 0 | yes | 1 | 0 | no |
| 17 | TailLight | `BootLight` | `sportsmuscle_body` (0, 1) | 152 255 225 | 152 255 225 | yes | 1 | 5 | no |

"Built colour" is `diffuse × 255`, rounded, so it compares exactly with `LightColor`. Entries 2
and 10 collect three T-18 rows each (`T-L25/T-L27/T-L8` on HeadLight1/1a/1b, `T-L26/T-L29/T-L9`
on HeadLight2/2a/2b); both the lamp colour and the built colour agree across those rows.

## 3. The two findings

**Entry 11 (T-L17, `BattleModeSpotLight`) is the one colour mismatch.** Built `154 154 243` is
`0.6039 / 0.6039 / 0.9529 × 255` - exactly the T-L17 graph object `Front_Secondary_Head`'s own
`diffuse`, which B-07 adopts for that entry (`TL17_MEMBERS["diffuse.R"] = ("object", …)`).
LIGHTS.md prints `BattleModeSpotLight` as `[255, 255, 255]` because that spot component does not
serialise `LightColor` and the value falls back to `Default__LightComponent` (CDO). Two BmAK
sources disagree for this lamp; the build follows the graph object, the doc prints the CDO
fallback. Not a build error against B-07's stated rule, but it is not "equal to the LIGHTS.md
value" either - hence NO in the table.

**Intensity is not bridged at all.** The 25-member entry has no `brightness`; the nearest member
is `multiplier`, which still holds the donor row's 1.0/2.0 convention while the BmAK `Brightness`
values are 0, 0.15, 1 and 5. The two "yes" cells (entries 3 and 7) are arithmetic coincidences
(1.0 vs 1.0), not adopted values. B-07 says this outright ("no unit bridge - `range`/`angle`/
`multiplier` stay the shipped numbers … only the colour is adopted", G2-33 §8), so the brief's
intensity-equality criterion fails by design, documented rather than hidden.

**And the anchors are not on the model:** 18/18 entries carry a `needs-lig-bone` anchor state,
and none of the 7 anchor bones is a part name in the built parts module - consistent with
LIGHTS.md's own note that the assembled part has no bone hierarchy yet (LGT-1).

## 4. Commands (verbatim)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/v_lights_rc2.py --write; echo "write_exit=$?"; python Tools/scripts/v_lights_rc2.py --check; echo "check_exit=$?"
wrote Builds/bm-RC2/verify/lights_vs_bmak.md (9768 chars)
entries 18, lamp entries 18, colour equal 17, intensity equal 2, needs-lig 18
write_exit=0
entries 18  sockets 13  parts ok 18/18  colour 17/18  intensity 2/18  needs-lig 18/18
PASS: 18 entries, 18/18 parts present and lit, colour 17/18 equal (exception entry 11 / T-L17, documented), intensity and socket-carriage reported as measured
CHECK_EXIT=0
check_exit=0
```

Earlier runs, kept so the final pass is not the only evidence:

```
$ python Tools/scripts/v_lights_rc2.py --write
FileNotFoundError: ...\Builds\bm-RC2\editor\entities\..._lights.vmodc
```
(path lacked the `aaf/` prefix - the module lives under `Builds/bm-RC2/aaf/…`)

```
$ python Tools/scripts/v_lights_rc2.py --write
KeyError: 'part_hash'
```
(the decoded member list in the report did not yet include `part_hash`)

```
$ python Tools/scripts/v_lights_rc2.py --write
TypeError: unsupported format string passed to tuple.__format__
```
(a list of colour triples was handed to the 8-bit formatter)

The first full run also reported `LIGHTS.md rig table | 2 rows, 2 components`, because the doc
escapes pipes inside anchor cells (`\|sportsmuscle_LOD1\|…`); the split now uses
`(?<!\\)\|` and the same table reads 28 rows / 36 components, matching T-18's summary.

## 5. UNKNOWNs (with what was tried)

1. **Whether JC3 accepts these entries at all.** The module schema has no socket member, so a
   "socket on the built model" cannot be expressed in this artefact; whether the engine resolves
   the anchor chain is a runtime question, and no game was launched (§3).
2. **What `multiplier` renders as.** It is a shipped member B-07 keeps, but no file carries a
   brightness bridge, so BmAK `Brightness` 5.0 vs multiplier 1.0 has no computed in-game effect here.
3. **The orphan sockets.** `HeadLight1c` / `HeadLight2c` are in no cooked mesh
   (`LIGHT_SOCKETS.md` UNKNOWN 3); no built entry uses them, so nothing is claimed about them.
4. **Whether the anchors resolve at load.** All 18 point at `|…|<bone>|<bone>_LIG`; the bone is
   absent from the built parts module, and whether LGT-1's bone pass is carried in this RC2 tree
   is outside this card.
