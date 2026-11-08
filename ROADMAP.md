# ROADMAP — Arkham Knight Batmobile in Just Cause 3, to a finished product

Written 2026-11-08 (day 33 of the project) by Claude from 8 landmark audits. Every task row,
with stage, status, blocker, size and evidence path, is in `Working/Roadmap/<landmark>.md`.
This file is the overview: landmarks, critical path, root blockers, pace, and the dates.
Dates are **estimates**, not measurements. Where this file and `GRAB_BACKLOG.md` disagree on a
fact, the evidence file wins (backlog rule).

| landmark map | rows | open | new tasks |
|---|---:|---:|---:|
| `Working/Roadmap/appearance.md` | 120 | 81 | 41 |
| `Working/Roadmap/weapons.md` | 140 | 83 | 47 |
| `Working/Roadmap/handling.md` (handling, physics, collision) | 127 | 69 | 26 |
| `Working/Roadmap/sound.md` | 61 | 48 | 27 |
| `Working/Roadmap/modes_controls_anim.md` (modes, controls, eject, moving parts) | 103 | 71 | 29 |
| `Working/Roadmap/hud_cam_lights_fx.md` (HUD, camera, lights, effects) | 169 | 127 | 80 |
| `Working/Roadmap/damage_world.md` (armour, damage, Rebel Drop, world) | 98 | 74 | 36 |
| `Working/Roadmap/integration.md` (verify, pilot, test, release, pipeline) | 101 | 68 | 28 |
| **total** | **~919** | **~621** | **314** |

The counts are approximate. They come from grepping the table rows in each map, and a few rows
appear in two maps (the HUD rows in weapons, for example).

---

## 1. Where the project is (day 33)

| stage | state | evidence |
|---|---|---|
| GRAB (BmAK + JC3) | desk-complete: 423/423 offsets, 19,203/20,128 BmAK objects; 81,953/81,953 JC3 entries, 6,045 modules, 77,611 geometry blocks | `STATUS.md` |
| TRANSLATE | 148/221 rows resolved, 15 blocked, 1 assumed, **0 behaviour-verified** | `STATUS.md`, `T_ROWS.jsonl` (199 lines, `t_rows.py check` passes) |
| BUILD | RC1–RC4 built Nov 5–7. **RC4 has the pursuit set only, `complete: false`.** RC5 exists only as `bm-RC5-audio` and `bm-RC5-entity`; its merge checker `bm_rc5.py` is not written | `Builds/bm-RC4/receipt.json` |
| VERIFY | V-01, V-02, V-03, V-05 and V-06 ran. The reds are V-04 (loop seam, fixed in RC5-audio), the V-05 T-ST7 steering miss, and V-06-RC2 (rollback deletes files; `install_v3` passes on copies but no build uses it yet) | `integration.md` §2 |
| PILOT | the cards are written and reviewed, but have never been run on a stock car (Q-0) | `Working/Q/PILOT/` |
| TEST | **banned** until `tmp/freebuff/APPROVED_Q.txt` exists. Nothing has been seen in game since the 2026-11-02 reset | `Working/Q/APPROVAL_REQUEST.md` |
| RELEASE | not started. R-1 allows a pipeline-only release (no game files) | backlog §10 |

## 2. Pace (measured, not assumed)

| period | what happened | throughput |
|---|---|---|
| Oct 7–23 | build-and-look era: 91 `test-0xx` builds, in-game tuning by screenshot | ~5 builds/day |
| Oct 24 | unified backlog written | — |
| Oct 27–31 | Freebuff lanes start; G1/G2 grab completion | **~55 briefs/day** (18, 69, 80, 62, 47) |
| Nov 2 | research reset (stop building on guesses) | — |
| Nov 3–8 | G3 grabs, ledger apply, RC1→RC4 in 3 days, RC5 campaign queued | **~105 briefs/day** (112, 42, 123, 142, 110, 47 partial) |

Source: mtimes in `tmp/freebuff/done/` (852 briefs) and `tmp/freebuff/reports/` (757 reports).
Desk throughput has roughly **doubled**. What it cannot speed up:
1. **Serial chains.** The ledger-apply chain (9031→9032→9033) and the RC5 merge
   (9100 → 91xx → 9190 → 9191/9192 → 9193) gate everything behind them, so throughput there is
   about one brief at a time.
2. **In-game sessions.** Agents pilot and the operator supervises (operator ruling 2026-11-08).
   Each fix loop costs at least one rebuild, install and drive.
3. **Capability spikes.** Seven tools or engine facts that no file proves (§4).

## 3. Landmarks (the finished product, in order of when each can be verified in game)

Each landmark is done only when its in-game checks pass (Q) with recordings, never when the files merely look right.

| # | landmark | done when | depends on | target (est.) |
|---|---|---|---|---|
| L0 | **Pipeline running + first real-game evidence** | lanes restarted; a narrow RC4 probe session answers U-probes P1–P8 (§5) | operator: restart lanes, approve RC4 probes, Q-0 on a stock car | **Nov 9–14** |
| L1 | **RC5 desk candidate (VX)** | 9033, 9100–9179, 9190–9193 done; V-01..V-06 green on RC5 | L0 results folded into briefs | **Nov 14–21** |
| L2 | **Appearance** (body, true scale, gunmetal satin paint, glass with visible glowing cockpit, emissives, moving-part cuts) | Q-1 looks pass vs the operator screenshot reference; paint accepted | 9143 paint, 9140 textures, 9142 lights, 9172 parts; G3-07 or screenshot calibration | **Nov 28 – Dec 8** |
| L3 | **Pursuit handling** (torque, 209 mph boost, steering 0.25 s, drift, brakes, suspension, landing, flip thrusters) | Q-2 takes A2–A9 pass the V-05 bands | 9120–9124, 9141 collision; oracle for collision | **Dec 5 – Dec 22** (tune loop) |
| L4 | **Rank-1 weapons: tracker + Immobiliser (EMP missile)**, then booster mesh, EMP burst | Q-3 EMP probes pass: tag → lock circle → missile → permanent disable (unarmoured) / stun (armoured) | 9100→9101→9102→9103→9104→9105→9107; HUD marker (9160) | **Dec 1 – Dec 12** |
| L5 | **Sound** (turbine-led engine layers, afterburner, weapon sounds, cabin, impacts) | listening takes pass with recordings | NEW-AUD-1 media re-grab, 9150, NEW-AUD-4 per-entity override probe; FSB5 writer for full layers | swaps **Dec 1–10**; full layers **Jan** (tool spike) |
| L6 | **Damage & world** (small-arms immune, 1200 HP scale, instant explosion at 0, regen out of combat, no crash damage, water teleport, Rebel Drop entry + name, no NPC hijack, traffic exclusion) | Q-3 world/damage checks pass | 9171, 9173, 9124; script-logic carrier (NEW-WLD-03) for water teleport / flip / regen | **Dec 8 – Dec 22** |
| L7 | **HUD & camera** (health top-left in battle, afterburner + cooldown gauges left, no speedometer, radar icon set, lock diamond/circle, cannon reload circle, Vulcan bloom crosshair, tracker signal; chase camera per mode) | HUD probes + Q-3 combat HUD pass | **Scaleform write spike** (NEW-HUD-4), entity→HUD bridge, ADF append writer | **Dec 15 – Jan 20** |
| L8 | **Battle mode** (LT hold, 2 s transform: turret rises + wheels reconfigure, near-instant slowdown, nose follows camera, turn on the spot, RT cannon / RB Vulcan / barrage auto-fire at lock with 1/4/7/10 by level, hacker, sonar, battle camera FOV) | Q mode-swap and battle combat checks pass | **mode-switch spike** (9050 exe study → swap route or native hook ruling), keymap writer, joints (JOINTS-v2 merged) | **Jan 5 – Feb 15** (highest risk) |
| L9 | **Remaining gadgets** (hacker/SAM hack, sonar pulse, winch, riot suppressor, missile pods) | Q combat checks pass | L8 for the battle-only ones; winch plan (NEW-WPN-15) | **Jan – Feb** |
| L10 | **Skins** (MK2, Jokerfied, Funhouse as extra Rebel Drop entries) | each skin spawns, within budget | the final car (L2–L8); per-entity budget question | **+1 week after L8** |
| L11 | **Release** | R-1 pipeline package rebuilds from the user's own copies (paths not hard-coded), KB note (R-2), receipt `complete: true` or every gap closed | QX | **+3–5 days after L10** |

## 4. Root blockers (what blocks everything else)

Ordered by how much they block. "Operator" items can only be cleared by you.

| # | blocker | blocks | who clears it | how |
|---|---|---|---|---|
| RB-1 | **Freebuff lanes stalled.** The watchdog logs `F6 lanes 0 < cap 3 with 3 ready briefs` every 2 min; `running/` is empty; the last brief finished at 03:50 and there was no work through 15:01Z. E1: brief 8906 deadlocked on a producer in `low/`. E4: only 3 ready briefs. `NO_RESTOCK` is set | all desk work | operator (restart lanes / allow restock); Claude can write fillers | check `tmp/freebuff/watchdog.log`, `driver-L*.log`; fix the E6 classifier in the freebuff skill |
| RB-2 | **Test ban.** `APPROVED_Q.txt` is absent, and the Q briefs 8600–8605 still point at RC4 full sessions | every TEST row (~150) | operator (said yes to RC4 probes; the marker file is not written yet) | write a **narrow probe brief** first, then the marker (§5) |
| RB-3 | **Serial apply chain** 9031 → 9032 → 9033 → 9100 | every RC5 build row | lanes | keep fillers flowing in parallel; nothing else can run ahead of 9100 |
| RB-4 | **Mode switching at runtime UNKNOWN** (U1). 0 selectors in 52 module types; a second entity via Rebel Drop works but arrives at rest | battle mode, battle weapons, battle HUD, battle audio/camera/lamps, D-2 | 9050 exe study, then the operator ruling on a native hook (NEW-MOD-1) | §6 Q4 |
| RB-5 | **Input is a global keymap** (`settings/keymap_gamepad.bin`); no keymap writer; LT-hold / A-hold-charge are not expressible as decoded; whether a dropzone keymap is honoured is UNKNOWN | D-11, every weapon bind, eject | probe P2 + keymap writer tool | |
| RB-6 | **No Scaleform writer**: no tool recompiles `hud.gfx`; whether a private copy loads is UNKNOWN; the entity→HUD caller is native | all of L7 | spike NEW-HUD-4 + probe P3 | |
| RB-7 | **No runtime oracle** (G3-07 open; `jc3oracle.py` absent) | collision truth, colour truth, live mass | static route exhausted → read-only attach (operator authorisation) | §6 Q5 |
| RB-8 | **Audio authoring ceiling**: FMOD FEV v56 with no project and no FSB5 writer, so only in-place sample swaps are possible; 21/45 GUIDs sit in shared banks | full engine layers, battle audio | spike NEW-AUD-5; probe P4 | |
| RB-9 | **No script-logic carrier found** for "when X do Y" (water teleport, flip thrusters, regen timer, summon/homing); `.btc` bodies undecoded | L6 parts, flip | NEW-WLD-03, NEW-WLD-01 | |
| RB-10 | **Writers missing**: ADF append (camera shake), `.effc` emitter growth (sonar ring, EMP lightning, booster plume), `.physicsc` hull/constraint append (2 of 3 collision boxes, turret hinges) | effects, collision, joints | tool spikes | |
| RB-11 | **Budgets**: model 4,791/4,915 KB (only 124 KB spare); silhouette passes by 0.0004 pp; three texture totals disagree | booster mesh, tracker, flares, collision boxes, skins | NEW-APP-8 reconcile; LOD/texture trims | |
| RB-12 | **Colour bridge**: no decoded UE3 → CarPaintMM conversion; material graphs stripped | L2 paint acceptance | operator screenshot as reference (§7) + G3-07 or calibration takes | |

## 5. First move: the RC4 probe session (L0, operator approved 2026-11-08)

One supervised, agent-piloted session on RC4. Each probe has one variable (R13) and a 5-minute
answer that unblocks a long chain. Prerequisites: Q-0 passes on a **stock** Serpente (pilot cards
work), saves backed up (`um backup`), and `install_v3` used rather than Rollback091.

| probe | question | unblocks |
|---|---|---|
| P1 | Does the game read our `batmobile.physicsc`? (drive into a wall at a known offset; screenshot the contact gap) | RB-7, collision chain, T-22/B-10 |
| P2 | Is a dropzone `keymap_gamepad.bin` honoured? (add one harmless binding) | RB-5, all binds |
| P3 | Does a private `ui/hud.gfx` copy load? (a visible text change) | RB-6, all of L7 |
| P4 | Does a per-entity audio bank override play? (one swapped GUID) | RB-8, B-26 |
| P5 | Does a Rebel Drop spawn of a second entity carry speed/health? (U2) | RB-4 fallback design |
| P6 | What does `USE_VEHICLE_MOD` (RPADRIGHT) do on the mod vehicle? (U3) | RB-4 / mode trigger |
| P7 | Damage model H0/H1/H2: rifle, tank shell, missile hits vs the health bar | ARM rows, NEW-ARM-03 |
| P8 | Does a grown `.effc` (one added emitter) render? | RB-10 effects |

Result: about 8 UNKNOWNs become facts, and roughly 6 multi-week branches either collapse to
S-sized build tasks or turn into confirmed tool spikes. **Doing this before RC5 is the biggest
schedule lever available.**

## 5b. Update 2026-11-08 (later): rulings, lanes, wheel-reinvention check

- Lanes restarted (driver `--parallel 3 --model auto`, 47/53 h) and `NO_RESTOCK` lifted.
- Native hooks are **permitted** (decision Q4 answered yes): L8 no longer depends on a data-only swap route.
- Queued: 7970 (JC3MP as a runtime platform), 7971 (existing JC3 format writers), 7972 (UE3 runtime tools for the GOG BmAK: the 22 unknown BmSDK addresses), 7973 (pilot-card wheel check, gates Q-0), 8589 (L0 probe payloads, offline), 8606 (supervised RC4 probe session). Full sessions 8601-8605 and 8699 are in `queue/held/`.
- **Lead: JC3MP.** Public packages use `WebUIWindow` (CEF overlay), `jcmp.ui.HideHud`, key capture through the WebUI, server-side `vehicle.Destroy` / `SetOccupant`, `vehicle.health`, settable `angularVelocity`, and `localPlayer.controlsEnabled` / `SetAbilityEnabled`. If it loads our entity, it could carry RB-4 (despawn/spawn swap with copied velocity), RB-6 (an HTML HUD), RB-7 (live readout), and RB-9 (water teleport, regen, flip logic). Caveats: it is multiplayer (a local private server), it probably needs a Steam-owned JC3 (the install holds `steam_api64.rne`), and gamepad input and custom-entity spawning are UNKNOWN. 7970 settles these.
- **7970 result:** on capability JC3MP covers RB-5, RB-6, RB-7 and RB-9 (partly RB-4; no gamepad input member; no in-place transform). It is **blocked on platform**: it needs a Steam-owned JC3, and the operator's JC3 is a repack of Steam build 20206564 (emulator layout). Using it as the product would also change the release from a single-player mod to a JC3MP server pack. Routes: (a) buy JC3 on Steam and use JC3MP at least as the runtime oracle and test harness; (b) native hooks on the repack exe (permitted 2026-11-08).
- **JC3MP attempt (operator: try anyway):** SteamCMD installed the dedicated server (app 619960, anonymous) at `E:/Modding/_tools/jc3mp-server`. The client was refused: `Failed to install app '619910' (No subscription)`. Fallback per the operator: a native hook modelled on the JC3MP API contract.
- **Native hook base found:** `aaronkirkham/jc3-console-thingy` v1.1 (MIT, 2026-01-11) was re-addressed for the 2025-12-17 unprotected exe. `Tools/scripts/exe_addr_check.py` shows every address lands on a function start or call site in the operator's `JustCause3.exe`, so the repack exe is that official build. It provides runtime spawning of any entity, plus the player, input, UI, debug renderer and clock managers. Brief 7974 designs the hook. Probe P9 (spawn our entity at runtime) runs first in 8606. `xforce/jc3-handling-editor` (2017 addresses, invalid now) shows the runtime handling structures to re-find.
- `APPROVED_Q.txt` is still unwritten on purpose: it is written when the operator is ready to supervise.

## 6. Decisions still needed from the operator

Gameplay facts answered on 2026-11-08 are in memory (`bmak-gameplay-facts`) and §7. Still open:

1. **Restart the lanes / lift `NO_RESTOCK`** (RB-1).
2. **Write `APPROVED_Q.txt` for the RC4 probe batch only** once the probe brief and Q-0 exist (RB-2).
3. **Pilot calibration values** that are UNKNOWN in the repo: menu keys, save slot, stock Serpente
   spawn route, airfield coordinates, windowed flag (NEW-INT-20).
4. **Native hook allowed?** If 9050 finds no data route for an in-place LT swap, a native hook (R17) is
   the only lore-exact carrier. Yes or no decides whether L8 takes about 3 weeks or 6+.
5. **Read-only memory attach to the running JC3** for the oracle (RB-7)?
6. **Steam copy of BmAK** for BmSDK live scraping? It answers LT hold time, the A-charge window,
   the steering curve, regen rate and summon numbers. Without it these come from footage.
7. **Global keymap side effects**: a rebind also changes on-foot controls unless a hook scopes it.
   (This is a lead question, not a compromise: is any on-foot binding sacred?)
8. **Fix-loop cap**: the backlog says one extra session per planned session before you decide.
   Keep that?

## 7. Facts from the operator that change tasks (2026-11-08)

| fact | changes |
|---|---|
| Pursuit mode fires **only the EMP missile**; tracking on/off and boost are pursuit-exclusive (not weapons); the tracker HUD persists across the mode switch | **D-7 ("all weapons in both modes") contradicts lore**: per-mode weapon sets are correct. Re-open D-7; weapons map NEW-WPN-9/34; T-WP13 slot pressure drops (pursuit needs 1 fire slot) |
| Gamepad (Xbox) | bind the gamepad first; M+K is secondary (NEW-WPN-32) |
| EMP burst: tap, fixed stun; **permanent disable for unarmoured vehicles** | 9107 disable half: no charge levels |
| Engine identity leans **turbine whine** | the engine layer priority in 9150 / NEW-AUD layers |
| Transform: **turret rises + wheels/body reconfigure, ~2 s**; swap causes a **near-instant slowdown** | B-12/9130: a momentum loss on swap is lore, so the second-entity route's "arrives at rest" problem shrinks (the state carried is health/ammo, not speed) |
| Eject: **hold A to charge, tap A to eject higher; a plain double-tap gives the lowest eject**. JC3 donor = hold A + parachute | 9170 eject: two-level eject; the backlog's "hold A" and the menu's "double-press" are both partial |
| Canopy: **interior visible with glowing screens** | NEW-APP-12 cockpit interior + emissive screens are required, not optional |
| Paint: **dark gunmetal satin, specular edges, carbon-weave insets, white chevron decals, rain beading** (operator screenshot) | APP-2 pass criterion = gunmetal satin, not flat black; the white-violet RC result was too light *and* wrong in hue; check the chevrons and carbon insets exist in the slots (APP question 10) |
| Barrage **auto-fires at full lock**; targets per upgrade level 1/4/7/10 | 9105 lock/salvo; pick the max level (10) for a fully upgraded car unless told otherwise |
| Armour **identical in both modes** | `ArmourModeDamageReduction` needs reconciling (player fact vs decoded); T-MD rows |
| Regen: **out of combat over time; full on re-summon / after death** | ARM-5 is no longer UNKNOWN-maybe-absent: a closest carrier is required (regen timer → RB-9) |
| Battle binds: **RT cannon, RB Vulcan** | T-WP13 / 9110 binds |
| Death: **instant explosion at 0 HP** | 9171; drop the donor smoke/burn stages (T-FX22/23 conflict) |

Also already in memory and still valid: water teleports to land (overturns D-8 "sink and stall"; T-WLD13/14 are stale), flip thrusters after a rest, no crash damage, the Vulcan has bloom with no lockout, the cannon has a reload circle, and the lock diamond/circle behaviour.

## 8. Record inconsistencies to fix (found by the audits)

- `STATUS.md`: event `0x6BB2C66E` is listed UNKNOWN but is resolved (tracker AkEvent twin, `sound.md` item 5); the winch is listed `out` but the ledger says `blocked`; the live build is test-090 here but test-091 in the backlog; ledger size is quoted as 198/199/216/221 in different places; and the "T-14: 28 rows" are lamp rows, not damage rows.
- `GRAB_BACKLOG.md`: §0.7 prose says 81,952/81,953 (now 81,953); D-6 "standalone" was disproven in game (RC4 replaces a vanilla `_debug` leaf); D-8 was overturned; the B-12 card calls turn-on-the-spot a "named omission" (forbidden by `STAGES.md`); B-15/B-17/B-24/B-25 numbers collide with `Research/specs/`.
- `T10_DAMAGE.md` says T-DM7 is `out`; the ledger says `next`.
- Q briefs 8600–8605 name RC4 and `install_v3.ps1`; repoint them after L0.

## 9. Bottom line: how long

- **Spent:** 33 days. That bought complete grab and translation on the desk, plus four release candidates.
  Very little of the remaining work is like that: it is tool spikes and in-game loops.
- **Playable, verified pursuit Batmobile** (looks, handling, Immobiliser + tracker, boost, sound swaps, damage, Rebel Drop):
  **about 4–6 weeks → mid to late December 2026.**
- **Finished product** (battle mode, full HUD, all weapons and gadgets, full audio layers, skins, release):
  **about 10–14 weeks → late January to mid February 2027**, so the whole project runs about
  4 months. Most likely: **early February 2027.**
- **What moves the date most:**
  - Earlier: the L0 probes come back yes (keymap, HUD, per-entity audio and the `.effc` all honoured); 9050 finds a data swap route; lanes run without stalls.
  - Later: no swap route and no hook allowed (L8 has no lore-exact carrier); the Scaleform write fails; agent piloting fails Q-0 and the operator has to drive every session.

## 10. Live estimate (2026-11-08, later)

The finish date is now computed, not typed: `python Tools/scripts/project_eta.py --print` reads
`Working/Roadmap/landmarks.json` (desk/game days per landmark, the queue briefs that measure each one) and the
finished briefs in `tmp/freebuff/done/`. It writes `tmp/freebuff/eta.json`, which the Freebuff GUI shows as
"~N days till project completion" to the right of the emergency and reset timers. The GUI recomputes it every 10 min.
First value: **~73 days, 2027-01-20 (range 2027-01-08 to 2027-02-07)**, at a measured 128 briefs/day. It is earlier
than §9's "early February" because jc3-console-thingy gives the native hook a proven base for this exe.
If no landmark advances, the date slips by itself. When a landmark's in-game checks pass, set `"done": true` in
`landmarks.json`; add new briefs to a landmark's `briefs` list so they count.
