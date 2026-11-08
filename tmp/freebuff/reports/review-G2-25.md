# Independent review — G2-25 · HUD vehicle-weapons API

Reviewer: independent read-only pass (did not write the card). Date 2026-10-28.
Card: `GRAB_BACKLOG.md:732` (`G2-25 · HUD vehicle-weapons API`, S, deps G2-11, serves HUD-2,
WPN-12). Tracker row: `GRAB_BACKLOG.md:1308` (`G2-25 | done`).
Journal: `MODLOG.md:10106` (intended change), `MODLOG.md:10265` (done).
Outputs reviewed: `Research/JC3Grab/JC3_HUD_WEAPONS.md` (20,073 B), `Research/JC3Grab/JC3_HUD_WEAPONS.json`
(21,751 B), `Tools/scripts/jc3hudwpn.py` (58,206 B), README registration `README.md:485`/`934`.

## VERDICT: needs rework

Not for the content — the API reading is correct, and I verified its four load-bearing numbers against
the decompiled `hud.as` itself. But **the card's Done check fails today**: `jc3hudwpn.py --check`
exits 1 with `JC3_HUD_WEAPONS.json stale; md differs`. The cause is a design flaw, not a data error:
the script copies the live `| T-HUD5 |` row out of `Working/Translation/T6_HUD_CAMERA.md`
(`jc3hudwpn.py:312`) into both artefacts, and a later card (T-19) rewrote that row, so the gate can
never stay green while the row is edited by anyone else. Until the row is snapshotted (or the card is
regenerated with the snapshot stored in the json), a `done` row in §12 points at a red check.

## Check output (verbatim)

Command: `python Tools/scripts/jc3hudwpn.py --check`

```
FAIL: JC3_HUD_WEAPONS.json stale; md differs: @@ -190,3 +190,3 @@
 |  ``` | -| T-HUD5 | `UC_SetCannonCoolDown(0…4)`, heavy reticle, special weapon states | `InitVehicleWeapons` / `UpdateVehicleWeapons` (2 slots) | categorical | no weapon component on the mod | **blocked**: the HUD supports it, the entity does not | decoded | fire the cannon, reticle cooldown | | +| T-HUD5 | `UC_SetCannonCoolDown(0…4)`, heavy reticle, special weapon states | `InitVehicleWeapons` / `UpdateVehicleWeapons` (2 slots) | categorical | no weapon component on the mod | **blocked**: the HUD supports it (G2-25: 2 slots, `InitVehicleWeapons` / `UpdateVehicleWeapons`, cooldown) but the entity still has no weapon component - T-11/B-05, slots per D-7 (`Research/JC3Grab/JC3_HUD_WEAPONS.md`) | decoded | fire the cannon, reticle cooldown | |
```

Exit code **1**. (The MODLOG's archived run at `MODLOG.md:10320` was green on 2026-10-27; the row it
quotes has since changed.) All Out paths exist, the README section and `Files` row are present, and
the Done criterion — "each BmAK HUD element in WPN-12 has a JC3 element or a stated absence" — is what
the json's `wpn12` list of 5 rows encodes (3 map, 1 stated absence, 1 partial), so the criterion and
the check do match. The check's *inputs* are the problem, not its assertions.

## Issues

1. **The check is red; the card cannot be `done` under its own gate.** `jc3hudwpn.py:312` reads the
   live row `next(ln for ln in t6.splitlines() if ln.startswith("| T-HUD5 |"))` from
   `Working/Translation/T6_HUD_CAMERA.md:24`, embeds it in the doc's §7 fenced block
   (`JC3_HUD_WEAPONS.md:190-192`) and stores it in `JC3_HUD_WEAPONS.json` (`rows.t_hud5`). T-19 later
   rewrote that row to add "G2-25: 2 slots … T-11/B-05, slots per D-7", so the rebuilt pair no longer
   equals the files. Fix: store the quoted row **and its digest** in the json, compare the digest, and
   keep the doc's snapshot; or regenerate and drop the "said this before the card ran" framing.

2. **Provenance trap if it is simply regenerated.** `JC3_HUD_WEAPONS.md:188` introduces the block as
   *"T-HUD5 … said this before the card ran"*. After a plain `--write` that sentence would print
   **T-19's** text as if it were the pre-G2-25 state — a false historical claim created by a
   regeneration. The quote must be frozen with its date (or dropped) before the gate is re-run.

3. **Minor: `rows.t_hud5` is the one non-derived number pair in the json.** Everything else in both
   artefacts is parsed from the decompiled scripts or the repo's own tables; this row is a foreign
   working document's text. It is fine for context, but it should not be a byte-compared input
   (R11: numbers generated from data, not from another doc's mutable row).

## Spot-checks

| value in the doc | where verified |
|---|---|
| `InitVehicleWeapons` **9** arguments with those defaults; `UpdateVehicleWeapons` **6** (`JC3_HUD_WEAPONS.md:14-15`, §1-2) | `E:/Modding/_JC3grab/hud/dec/scripts/hud.as:5030` and `:5160` — the signatures match the doc character for character (arg names, types and defaults) |
| vehicle HUD has **2 slots**, and `E_NUM_WEAPON_SLOTS = 7` is the on-foot wheel (`JC3_HUD_WEAPONS.md` §3) | `hud.as:4951` builds `m_WeaponsArray` from exactly `MCI_vehicle_weapons0, MCI_vehicle_weapons1`; `hud.as:429` `E_NUM_WEAPON_SLOTS:* = 7`, used only by the 7-slot loops at `:5426`/`:5536` |
| the only call sites are **2 demo calls inside `TestConstructor`** (`JC3_HUD_WEAPONS.md` §8) | `grep -rn "InitVehicleWeapons\|UpdateVehicleWeapons"` over all 260 `.as` files: definitions plus `hud.as:7535/7536` only, and the enclosing function is `TestConstructor` at `hud.as:7394` |
| lock-on is **one POI**, `POI_TYPE_LOCK_ON_TARGET = 21`, rotated once per **1.5 s** | `hud.as:1011` `POI_TYPE_LOCK_ON_TARGET:int = 21`; `hud_code/poi.as:75` `LOCK_ON_TARGET_ROTATION_TIME:Number = 1.5` |
| **0** heat parameters and **0** heat mentions in the bodies (`JC3_HUD_WEAPONS.md` §7, "stated absence") | scanned `hud.as:5030-5250` (both functions and their helpers): **0** occurrences of `heat`; the movie's heat code is the police system (`MCI_heat_container`, `HEAT_STATE_RESTRICTED`, `hud.as:3133-3158`, `hud_code/heat/`) |
| 260 scripts, `hud.as` **11,295** lines, **14** reticle shapes, **5** look states | `find … -name "*.as" \| wc -l` = **260**; `wc -l hud.as` = **11,295**; `JC3_HUD_WEAPONS.json` `reticle.shapes` = 14 keys, `reticle.look` = 5 `ECrosshairLook_*` constants |

## Rules

R4: the doc is explicit about what is native and therefore UNKNOWN (the entity → HUD caller, the
reticle shape id for a vehicle cannon, the 5-state → 0..1 pinning), which is the right treatment of
a name-vs-behaviour gap (R5) — `UC_SetCannonCoolDown(0…4)` and `weapon_cooldown 0..1` are correctly
kept as different shapes rather than mapped by name. R11: the only typed, non-derived input is the
T-HUD5 row (issue 3), and it is exactly what breaks the check.

## Limits of this review

Read-only: I ran `--check`, read the decompiled `hud.as`/`poi.as` lines cited above, and compared the
json's shape/look/slot data with the raw scripts; I did not edit anything, did not re-run the tamper
tests at `MODLOG.md:10328-10330`, and did not re-derive the icon census (`INDEX.jsonl`) or the BmAK
`HUD_INTERFACES.json` side. No archive was opened, no game launched, nothing committed.
