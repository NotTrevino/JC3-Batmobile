# Landmark map: ARMOUR/DAMAGE and WORLD INTEGRATION (as of 2026-11-08)

Read-only survey. Every claim cites a path under `E:\Modding\JustCause3\JC3-Batmobile`. UNKNOWN = no file read settles it.
Abbreviations: GB = `GRAB_BACKLOG.md`; TF = `tmp/freebuff/reports/`; Q = `tmp/freebuff/queue/`; TR = `Working/Translation/`; RJ = `Research/JC3Grab/`; RB = `Research/BatmobileGrab/`.
Status words: done / partial / queued / todo / blocked. "queued" = a brief exists in `tmp/freebuff/queue/` but produced no output yet (checked: `Working/RC5/` does not exist, `Builds/bm-RC5-damage|world|survival` do not exist; only `Builds/bm-RC5-audio` and `-entity` exist).

## 0. Findings that change the picture (read first)

1. **D-6 "standalone entity" is disproven in game.** MODLOG 2026-11-02 (line ~19682): "A NEW entity path does not spawn, whatever its content. D-6's 'standalone new path' is disproven in game." The shipped RC4 therefore replaces the vanilla, unregistered, traffic-free `v0300_car_kensington_sportsmuscle_debug` leaf (hash 1621485476) (`Builds/bm-RC4/receipt.json` leaf; `Builds/bm-RC4-rebel/`; `TF/standalone-entity-spawn-check-plan.md`). The backlog D-6 row (GB line 1799 region) and T15_WORLD still say "standalone"; T-WLD1/T-WLD4/T-WLD6 text mixes the dead `_batmobile` leaf (443190071) and the live `_debug` leaf. The `_debug` leaf in RC4 is **untested at runtime** (`Builds/bm-RC4/receipt.json` not_done: "runtime load, Rebel Drop resolution and the Q takes are untested"). Consequence: every extra Rebel Drop entry (D-5 skins MK2/Jokerfied) needs another vanilla leaf to hijack.
2. **D-8 (water = sink and stall, "Rico swims out") is overturned by the operator's 2026-11-08 play facts**: the car does not swim, driving into water teleports it to land, the engine does not fail (memory `bmak-gameplay-facts.md`; `TF/water-flip-damage-remote-plans-v2.md` §1.2 names W-O1..W-O3). T-WLD13/T-WLD14 are ledger `keep` ("sinks") and now wrong. GB D-8 row not yet re-resolved.
3. **STATUS.md "T-14: 28 rows, 26 queued" is not the damage card.** Those 28 rows are `T-L8..T-L35` (lamp rows) filed under doc label `T-14` in `TR/T_ROWS.jsonl`. The damage rows are `T-DM1..T-DM6` (doc T-2b) and `T-DM7..T-DM9` (doc T-3). Damage translation completeness cannot be read from the STATUS T-14 line.
4. **`TR/T10_DAMAGE.md` is stale on T-DM7**: it says `out`; `T_ROWS.jsonl` T-DM7 is `next` ("moved off out: `rotor_collision.damage_to_other_per_second` 100000/s"), carrier `TF/carrier-ram-and-dodge.md`.
5. **Health scale is contested.** T-14 option B ships `max_health` 36000 (24 heavy-cannon hits x 1500; shipped domain 500..4000) with `invulnerable` 0 (`TR/T10_DAMAGE.md` §1, §7). Brief 9171 asks for the BmAK 1200 scale "as the closest member allows (damage multipliers instead of 30x health)" and says review 8399 item 3 flagged it. Which damage model is real (H0 armour ignored / H1 percentage gate / H2 threshold) is UNKNOWN until Q1-DM-A/B/C.
6. **The plan for traffic/AI reaction has 3 contradicted claims** (`TF/traffic-ai-claims-audit.md`): B2 `impact_damage_factor 1 -> 2.25` (build is 0, `RJ/DAMAGE_MODEL.md:50`), B3 `impact_armor 0@0` (build is 5000@100, `:43`), and 4 not 11 `civilian/` trees. B2 also conflicts in direction with T-DM8 (T-DM8 uses `impact_damage_factor` as INCOMING collision damage = 0; the traffic plan uses it as the DEALER multiplier). Direction is UNKNOWN.
7. **Installer state.** V-06-RC2 FAIL (Rollback091 deletes 9 payload files, `Builds/bm-RC2/verify/dropzone_sim.md`). `install_v2` needs fixes (bare string-prefix guard, rollback deletes any manifest path, `TF/install-v2-review.md`). `install_v3` is done on copies and passes x3 (`Working/Installer/install_v3.ps1`, `Tools/scripts/install_v3.py --check`) but is NOT adopted by any build's `install.ps1`; operator decision pending (GB tracker "install_v3"). The live dropzone already holds the RC2 payload: do NOT run Rollback091 there (GB V-06-RC2 row). `Builds/bm-RC4/receipt.json` installed=false.
8. **No RC5 damage/world tree exists.** Briefs 9171, 9173, 9124, 9050 are queued and AFTER-gated on 9033/9101 reports; `APPROVED_Q.txt` does not exist (`tmp/freebuff/APPROVED_Q.txt` absent).
9. **Death look (ARM-6) is a named omission in T-14** ("BmAK side has no decoded effect/sound path", `TR/T10_DAMAGE.md` §4) although `GB` §1.3 lists `DeathExplosionSoundArray` as lore source and the operator describes a violent explosion that kills passengers. This is reopened in 9171.
10. **Visible damage vs lore.** BmAK has no visible damage stages (operator). The build keeps donor smoke/burn thresholds (1050/250), 24 `Land_*` part damage types on 59-61 parts (T-DM4/T-DM5). JC3 will show smoke/fire/part detachment; this contradicts the operator fact and is not on any row (see NEW-ARM-05).

## 1. Task table

### 1A. ARMOUR / DAMAGE

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G1-14 | BmAK damage rules, Health 1200, ArmourModeDamageReduction (0), regen answer | GRAB | done | - | T-14, G2-28 | M | `RB/DAMAGE_RULES.md` + `bmak_damage.py --check`; GB tracker G1-14 |
| G2-28 | JC3 damage model chain, hits-to-kill 9 arms x 3 vehicles x 3 models | GRAB | done (7 chain steps all carry an UNKNOWN) | - | T-14 | M | `RJ/DAMAGE_MODEL.md`, `damage_predict.py --check` |
| (mech) | Damage mechanisms: `invulnerable` int32 at epe+1167, 0 on 233 roots, shipped =1 only by 10 CDamageController | GRAB | done | - | T-DM9 | S | `RJ/DAMAGE_MECHANISMS.md`, STATUS.md |
| G3-06d | Damage component: 4 `RVisualDamageComponent` exports (native triage) | GRAB | todo | G3-06 | ARM-2/3 evidence | S | GB tracker G3-06d; `RB/NATIVE_TRIAGE.md` §4 |
| NEW-ARM-01 | Read `HealthRecoverRate` values (TArray<float> @+8220, per difficulty); needs running BmAK CDO. Answers ARM-5 "regen: UNKNOWN" | GRAB | blocked | BmSDK hook offset 0x5B7220 invalid on this exe (QUEUE_MAP 7995); runtime read not allowed on repack; GOG copy path 7992-7994 | ARM-5 | M | `RB/DAMAGE_RULES.md` §5; `tmp/freebuff/QUEUE_MAP.md` |
| NEW-ARM-02 | Locate the BmAK death sequence: bodies of `TakeDamage` death branch, `DeathExplosionSoundArray`, explosion class/delay, passenger-kill (exe consumer UNKNOWN) | GRAB | todo | G1-22 native remainder | T-DM-death, 9171 | M | GB §1.3 ARM-6; `TR/T10_DAMAGE.md` §4 |
| T-DM1 | `max_health` 2000 -> 36000 (switch) | TRANSLATE | partial (ledger next; pending Q1-DM-A; conflicts with 9171) | Q1-DM-A, operator ruling on 1200-scale | B-09, 9171 | S | `TR/T10_DAMAGE.md` §5; `TR/damage_switches.json` |
| T-DM2 | bullet armour 5000@99 (fleet max) | TRANSLATE | done (edit applied) | - | - | S | `TR/T10_DAMAGE.md` §5 |
| T-DM3 | bullet_heavy 5@20 donor carry (no decoded weapon writes the channel) | TRANSLATE | partial | find a `bullet_heavy` writer in G2-11 weapons | ARM-1 cheaper route | S | `TR/T10_DAMAGE.md` §7 |
| T-DM4 | explosion/smoke/burn thresholds 4000/4000/1050/250 (fleet max) | TRANSLATE | partial (smoke/burn visual conflict) | NEW-ARM-05 | - | S | `TR/T_ROWS.jsonl` T-DM4 |
| T-DM5 | part damage types (24 `Land_*`), 42 parts bm-009 / 61 bm-RC2 | TRANSLATE | partial (donor carry; may produce visible part damage) | NEW-ARM-05 | B-09 | S | `TR/T10_DAMAGE.md`, `TF/keep-audit-damage-collision.md` |
| T-DM6 | `deform_scale` 0 (no panel crumple) | TRANSLATE | done (switch declared; BmAK deform UNKNOWN) | - | - | S | `TR/damage_switches.json` |
| T-DM7 | outgoing ram damage (`rotor_collision.damage_to_other_per_second`, speed band 20->150, strafe 2.25, boost 2.0) | TRANSLATE | partial (row next, doc stale; whether CCar evaluates block UNKNOWN) | exe consumer; direction conflict with traffic plan | NEW-ARM-08 | M | `TF/tdm7-contact-damage-speed-band.md`, `TR/T_ROWS.jsonl` |
| T-DM8 | ramming never damages Batmobile: `impact_damage_factor` 0 switch | TRANSLATE | done (keep 0; behaviour unverified) | - | Q-3 A11 | S | `TR/T_ROWS.jsonl` T-DM8 |
| T-DM9 | small-arms immunity: option B channels + max_health; option A `invulnerable` unproven for vehicle root | TRANSLATE | partial (decided, not game-confirmed) | Q1-DM-A/B/C | ARM-1, ARM-2 | M | `TR/T10_DAMAGE.md` §1 |
| T-14 | damage/armour translation card (T-DM1..9, ARM-4/5/6) | TRANSLATE | done at desk; 0 behaviour-verified | - | B-09 | M | `TR/T10_DAMAGE.md`, `t10_damage.py --check`; GB T-14 row |
| ARM-4 / T-14 wheels | wheels indestructible: `front/rear_wheels_damage.skew_health` 200 -> 400 (ceiling; no off switch exists) | TRANSLATE | partial (labelled "not proven unbreakable") | Q test | - | S | `TR/T10_DAMAGE.md` §2 |
| ARM-5 | regeneration: JC3 has no member (0 hits, 52-type vocabulary); BmAK rate value UNKNOWN, awarded per XP event not per second | TRANSLATE | blocked | NEW-ARM-01; closest-system rule (never "no system": find closest e.g. repair via mission/Rebel Drop respawn) | - | S | `RB/DAMAGE_RULES.md` §5; `TR/T10_DAMAGE.md` §3 |
| ARM-6 | death explosion / destroyed car look+sound | TRANSLATE | blocked (named omission, reopened) | NEW-ARM-02 | 9171 | M | `TR/T10_DAMAGE.md` §4; Q/9171 |
| B-09 | private health module + damage types | BUILD | done on bm-009; RC4 carries it (59 parts, 19 types) | - | RC5 damage | S | `Working/Damage/bm_health.json`, `Builds/bm-RC4-damage-collision/`, `bm_health.py --check` |
| NEW-ARM-03 | Resolve health-scale ruling: 36000 max_health vs multiplier route to 1200; document which one ships; update T-DM1 | TRANSLATE | todo | operator (see c-Q1), Q1-DM-A | 9171 | S | Q/9171; `TR/T10_DAMAGE.md` §7 |
| NEW-ARM-04 | Death route: zero health -> violent explosion -> passengers die -> no drivable wreck. Carrier candidates: root CForcePulse `car_explosion_medium.ftune` (500 dmg / 5 m), `OnExploded` usage, `explosion_delay_s`; Rico-kill dependency UNKNOWN | BUILD | queued (9171) | 9033, 9101 reports; NEW-ARM-02 | Q-1 #6 | M | `TF/health-to-explosion-no-crash-damage-plan.md`; Q/9171 |
| 9171 | RC5 damage tree: `Builds/bm-RC5-damage`, `Tools/scripts/rc5_damage.py`, branch record `Working/RC5/branches/` (scaffold doc missing: `TF/rc5-scaffold-and-merge-script.md` is brief 9100, not yet run) | BUILD | queued | 9100, 9101, 9033 | 9190, 9179 | M | `Q/9171-rc5-health-explosion-no-crash.txt` |
| NEW-ARM-05 | Suppress visible damage stages (smoke/burn/part detach/mesh swap) to match "no visible stages": audit smoke/burn thresholds, `OnPartReachedDamageState` usage, part damage types, `mshswap` | TRANSLATE | todo | decision on armour-plate plan (overruled where it contradicts observation) | 9171 | M | `TF/armour-plates-and-deformation-plan.md`; `RJ/USAGES.md`; GB memory facts |
| NEW-ARM-06 | Fall damage, fire, train/water/script kills: confirm "crashes never damage" covers falls, hits by trains, mission kill zones; map `vehicle_damage` fields | TRANSLATE | todo | - | Q-3 A11 | S | `TF/collision-impact-effects-plan.md`; `RJ/DAMAGE_MECHANISMS.md` |
| NEW-ARM-07 | Define "heavy weapon" set for JC3 attackers (enemy rifles/MG/helicopter MG vs missiles/tank/RPG/mines) vs BmAK; produce per-attacker hits-to-kill on final build | TRANSLATE | todo | NEW-ARM-03 | Q-3 #2 | M | `TR/T10_DAMAGE.md` option B table (shotgun 144/pull is the gate) |
| NEW-ARM-08 | Outgoing ram damage + kill-flip/sideswipe numbers onto the build (ties T-DM7, 9123 air-control/ram) | BUILD | queued (9123) | T-DM7 direction | Q-3 A11 | M | Q/9123; `RB/DAMAGE_RULES.md` §3.3.1 |
| NEW-ARM-09 | Armour mode (battle mode) damage reduction: BmAK value 0 in every package; record as "no effect"; confirm battle-mode armour has no JC3 consequence beyond the 45 cm wider collision box | TRANSLATE | done at desk (value 0), not a row | - | - | S | `RB/DAMAGE_RULES.md` §3; `TR/T11_MODES.md` |
| NEW-ARM-10 | Health bar HUD link (top-left in battle mode, `UC_SetHealth`): JC3 HUD has no entity->hud caller | BUILD | blocked (HUD lane) | 9160 HUD build | Q-1 #5 | M | `STATUS.md` (HUD bridge); `OPERATOR_PRIORITIES.md` HUD leads |
| NEW-ARM-11 | Respawn/persistence: BmAK persists Batmobile health (`LoadHealth`); JC3 Rebel Drop re-delivers a fresh car; decide cooldown (`RebelDropTimer` 1800, unit UNKNOWN) and record named omission | TRANSLATE | todo | - | WLD-1 | S | `RB/DAMAGE_RULES.md` §4; `TR/T15_WORLD.md` T-WLD3 |
| NEW-ARM-12 | Re-run `damage_audit.py` + hits-to-kill table on the merged RC5; fixes for contradictions between T10_DAMAGE.md / T_ROWS (T-DM7) / STATUS T-14 label | VERIFY | todo | 9171, 9190 | 9193 | S | `Tools/scripts/damage_audit.py`, `damage_predict.py --root` |
| Q1-DM-A/B/C | In-game probes deciding H0/H1/H2 (percentage gate vs threshold vs armour ignored): pistol 200 rounds, tank cannon count | TEST | todo | APPROVED_Q, V-07 | T-DM1, T-DM9 | M | `TR/T10_DAMAGE.md` §1 |
| Q-1#6 | Self-damage test (pistol/rifle/MG, RPG/grenade; re-spawn after destruction; death effect/sound) | TEST | todo | APPROVED_Q | ARM-1/2/4/6 | M | GB §9b Q-1 item 6 |
| Q-3#1,#2 | Ram a wall/cars 40/80 km/h (ARM-3, WLD-5); 5-star heat >= 2 min survival; tank shells vs prediction | TEST | todo | Q-2 | ARM-2/3 | M | GB §9b Q-3 |
| Q-4-DMG | Fix loop for damage (one value at a time) | TEST | todo | Q-1/Q-3 | QX | M | GB §9b Q-4 |
| NEW-ARM-13 | Damage pilot cards (spawn, shoot, count magazines, record bar, destruction, explosion video) | PILOT | todo | Q-PILOT, 9194 | Q-1 #6 | S | GB Q-PILOT; `Working/Q/PILOT/` |

### 1B. WORLD INTEGRATION

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| G2-26 | Rebel Drop data recipe (`Item.Name` = Jenkins hash of leaf = spawn binding; no cost field) | GRAB | done | - | B-13 | S | `RJ/REBELDROP.md`, `jc3rebeldrop.py --check` |
| G2-27 | Standalone entity: load yes, hash UNKNOWN; later disproven in game | GRAB | done, **conclusion superseded** | - | D-6 | M | `RJ/STANDALONE.md`; MODLOG ~19682 |
| G2-29 | Traffic/AI/spawning (donor matches 1 of 41 selectors) | GRAB | done | - | D-9, T-WLD18/19 | S | `RJ/TRAFFIC.md` |
| G2-31 | Water behaviour (will_sink 189/232, donor buoyancy 2, drag 100) | GRAB | done | - | WLD-6 | S | `RJ/WATER.md`, `jc3water.py --check` |
| G2-32 | Names/icons/strings (`profile/online.stringlookup`, pair keyed by leaf hash, 11 languages) | GRAB | done | - | WLD-2 | S | `RJ/NAMES.md` |
| G2-34 | Tether/airlift/winch carriers (`CVehicleCargoBay` 7 members; helicopters 0/23; no tether member) | GRAB | done | - | WLD-7 | S | `RJ/TETHER.md`; `TF/winch-and-tether.md` |
| 9050 | Static exe analysis: how the game swaps/spawns a vehicle entity at runtime (U1); needed for mode pair, also for summon/spawn | GRAB | queued | - (no AFTER) | 9130, summon route | M | `Q/9050-exe-entity-swap-consumer.txt` |
| NEW-WLD-01 | Decode `ai/bts/*.btc` vehicle micro-behaviour bodies (`car_drive_to_point.btc` goal member) - index has names only | GRAB | todo | .btc format decode (0 bodies read) | summon/homing | L | `TF/summon-drive-in-closest-system.md` §7; `TF/traffic-ai-claims-audit.md` |
| NEW-WLD-02 | Decode `settings/factions.bin`, `global/heat.blo`, `settings/heat.gadfc` (AI/heat reaction to the Batmobile) | GRAB | todo | - | AI reaction rows | M | `TF/traffic-and-ai-reaction-to-batmobile-plan.md` §controls 4,5 |
| NEW-WLD-03 | Confirm JC3 can run mod-authored vehicle script/graph (`.gsc/.gdc`) from the dropzone: needed by water watcher, flip, homing. Absence would block 4 behaviours | GRAB | todo | - | NEW-WLD-12/13, flip | M | `Q/9124`; UNKNOWN (no file read states a graph writer exists) |
| T-20 | World translation card (19 rows, 8/8 WLD codes) | TRANSLATE | done at desk | - | B-13 | S | `TR/T15_WORLD.md`, `t15_world.py --check` |
| T-WLD1/2/3 | Rebel Drop item record, unlock reward on task 1361701860 (Type 19), UI profile | TRANSLATE | partial (next; leaf text outdated: 443190071 vs live 1621485476) | NEW-WLD-04 | B-13 | S | `TR/T15_WORLD.md` rows |
| T-WLD4/5/6 | Name "Batmobile", icon, blurb: `online.stringlookup` pair + `vehicle_icons/<leaf>.ddsc` | TRANSLATE | partial (V-RC2-strings: name+blurb in 11 languages, blurb English in all 11 = real compromise; icon = copy of donor 18,688 B) | translations; icon art | B-13, release | M | `Builds/bm-RC2/verify/strings.md`, `strings_languages.md`; `TR/T_WLD4B_STRINGS.md` |
| T-WLD7 | Category captions stay "SPORTS CAR(S)" | TRANSLATE | stale (category moved to military UIFlag 7 after leaf change) | reconcile | - | S | MODLOG ~19690 |
| T-WLD8/9/10 | Entry/exit/stunt-point nodes on real sides/roof (T-13 placement, 77/85 in band; 6 hijack objects dropped per D-9) | TRANSLATE | done (epe) | - | B-05 | S | `TR/T9_INTERACTION.md` |
| T-WLD11 | Stunt AREAS (3 areas, 22 vertices = bit copy of DeformPoints): verdict UNKNOWN, R-2 candidates fail O-1/O-2 | TRANSLATE | blocked | whether runtime recomputes `vertices3D_local` (UNKNOWN) | WLD-4 | M | `TR/T_WLD11_AREAS.md`, `T_WLD11B_SURFACES.md` |
| T-WLD12 | Mass 975 -> 6000 (unit UNKNOWN); crush/shove depends on hull set | TRANSLATE | partial | B-10 hull (2 of 3 BmAK boxes lack shape instance) | WLD-5 | S | `TR/T15_WORLD.md`; `Builds/bm-RC4/receipt.json` |
| T-WLD13/14 | Water "sinks / engine stalls" | TRANSLATE | **overturned** | operator decision; replace by NEW-WLD-12 | - | S | `TF/water-flip-damage-remote-plans-v2.md` §1.2 |
| T-WLD15 | Tether with 6 t car: closest = `CVehicleCargoBay` + grapple (native) | TRANSLATE | partial | in-game test | WLD-7 | S | `TR/T15_WORLD.md`; `TF/winch-and-tether.md` |
| T-WLD16 | Cargo plane/boat carry the car (6000 = 15% / 6% / 40% of bodies) | TRANSLATE | done (keep) | Q test | - | S | `TR/T15_WORLD.md` |
| T-WLD17 | Helicopter airlift: 0/23 helicopters have a bay | TRANSLATE | blocked | native alternative UNKNOWN (BmAK airlift of Batmobile not shown in any read file) | WLD-7 | M | `TR/T15_WORLD.md` |
| T-WLD18/19 | No traffic record for the new leaf; donor traffic record untouched | TRANSLATE | done (keep) | - | - | S | `TR/T15_WORLD.md`; `RJ/TRAFFIC.md` |
| B-13 | Rebel Drop entry (197 items, UIDisplayOrder 12, unlock + starter grant, name/blurb, icon) | BUILD | done at file level, runtime UNTESTED | Q-1a on `_debug` leaf | RC5 | M | `Builds/bm-013/drop/`, `Builds/bm-RC4-rebel/`, `bm_rebel.py --check` |
| NEW-WLD-04 | Re-issue D-6 and rebase all world rows on the `_debug` leaf (hash 1621485476): T-WLD1/4/5/6/7, backlog D-6/B-13 text | TRANSLATE | todo | operator acknowledges D-6 disproof | everything WLD | S | MODLOG ~19682; `Builds/bm-RC4/receipt.json` |
| NEW-WLD-05 | Skins as extra drop entries (D-5): find N more vanilla unregistered `_debug` leaves; each needs its own .ee/.toc/entity | BUILD | blocked | D-6 disproof (no new paths) | APP-8 | M | GB D-5; `RJ/STANDALONE.md` s4.1 |
| NEW-WLD-06 | Translate the Batmobile blurb into 10 non-English languages (compromise "real") or obtain BmAK localisation text; name stays "Batmobile" | BUILD | todo | operator ruling on text source | release | S | `Builds/bm-RC2/verify/strings_languages.md` |
| NEW-WLD-07 | Real Batmobile icon (render from mesh, `.ddsc` 18,688 B format) instead of copy of the Serpente icon | BUILD | todo | texture writer proven (T-WLD5 only copies donor) | WLD-2 | M | `TR/T15_WORLD.md` T-WLD5 |
| NEW-WLD-08 | Other name sites: in-vehicle HUD name, map/radar icon (green/cop/military arrows), notifications | TRANSLATE | todo | 9160, 8706 HUD leads | WLD-2 | M | `RJ/NAMES.md`; `OPERATOR_PRIORITIES.md` |
| NEW-WLD-09 | Unlock grant behaviour on existing saves: does the repeatable starter reward re-fire? and rollback with the car owned | VERIFY | todo | Q-1 | release | S | MODLOG ~19668 (UNKNOWN stated) |
| NEW-WLD-10 | NPC theft / enemy hijack of the empty Batmobile (D-9 only covers pulling Rico out): confirm 6 hijack objects dropped is sufficient, AI cannot enter parked car | TRANSLATE | todo | NEW-WLD-02 | Q-3 #6 | M | GB D-9; `TR/T9_INTERACTION.md` |
| NEW-WLD-11 | AI/traffic reaction (civilians flee/swerve, enemy targeting of the car): no member found; plan v2 with audited numbers; decide closest system (`impact_damage_factor`, heat) | TRANSLATE | queued (8789 plan exists; audit found 3 errors) | NEW-WLD-02, direction of `impact_damage_factor` | 9173 | M | `TF/traffic-ai-claims-audit.md`; `TF/traffic-and-ai-reaction-to-batmobile-plan.md` |
| NEW-WLD-12 | Water: suppress sink (`will_sink` 0, APC precedent) + water-entry teleport to nearest land, engine kept; watcher on `sinking_progress` >= 0.30 / in-water exit state; ring search 8-40 m (all chosen numbers) | BUILD | queued (9124) | NEW-WLD-03, D-8 re-resolution, 9101 | Q-3 #4 | L | `TF/water-entry-teleport-closest-system-plan.md`; Q/9124 |
| NEW-WLD-13 | Summon/arrival: Rebel Drop is the summon; drive-in via `car_drive_to_point.btc` (goal member UNKNOWN); skid stop; LB homing | BUILD | queued (9173), partial | NEW-WLD-01, 9050 | Q-3 | L | `TF/summon-drive-in-closest-system.md`; Q/9173 |
| NEW-WLD-14 | Remote drive: written halt for remote driving, static overlay 100 m, 150 m limit; homing partial. Needs operator accept of halt | TRANSLATE | queued (9124); halts proposed | operator acceptance | - | S | `TF/remote-control-range-static-overlay-plan.md` §6 |
| NEW-WLD-15 | Stuck/flip recovery (thrusters right the car) - world survival, part of 9124 | BUILD | queued (9124) | NEW-WLD-03 | Q | M | `TF/flip-recovery-idle-timer-and-thruster-plan.md`; `TF/stuck-flip-build-plan-merge.md` |
| NEW-WLD-16 | Weather/night/rain/surfaces (wet material, headlamp cone copy, skid ribbons vs `dust_trail_<surface>.effc`) rows | TRANSLATE | queued (9174) | 9142 lights | - | M | `TF/weather-and-night-plan.md`; `TF/surface-skids-and-tracks-plan.md` |
| NEW-WLD-17 | Tether on a 6 t car in game; helicopter-hook replacement; BatmobileWinch model = grapple (operator lead) | VERIFY | todo | Q-3 #5 | WLD-7 | M | `TF/apply-winch-tether-rows.md`; `OPERATOR_PRIORITIES.md` |
| NEW-WLD-18 | Stunt-area decision: write R-2 candidate vs accept named omission (roof standing relies on `point.stunt*` nodes only) | TRANSLATE | todo | T-WLD11 UNKNOWN | Q-1 #3 | S | `TR/T_WLD11_AREAS.md` |
| NEW-WLD-19 | Compatibility with Rebel Drop mod V5.3 and other mods overriding `profile/item.onlinec`, `task.onlinec`, `online.stringlookup` (same files as our dropzone) | VERIFY | todo | - | release | S | `GB` G2-26 In; `Research/1456340180_Rebel-Drop-Mod-V5.3/` |
| RC5-world | Build `Builds/bm-RC5-world`: spawn/traffic rows, summon route, item+string rows (`rc5_world.py`) | BUILD | queued (9173) | 9101, 9100, summon plan | 9190 | L | `Q/9173-rc5-world-spawn-traffic-summon.txt` |
| RC5-survival | `Builds/bm-RC5-survival`: water teleport, flip, remote (`rc5_survival.py`) | BUILD | queued (9124) | 9120 handling | 9190 | L | `Q/9124-rc5-flip-water-remote.txt` |
| 9174 | surface / weather / impact FX | BUILD | queued | 9142 | 9190 | M | `Q/9174-rc5-surface-weather-impact-fx.txt` |
| 9179 | review of RC5 body+world builds | VERIFY | queued | 9171-9174 | 9190 | S | `Q/9179-review-rc5-body-and-world-builds.txt` |

### 1C. INSTALLER, ROLLBACK, MERGE, VERIFY, RELEASE

| id | task | stage | status | blocked by | blocks | size | evidence path |
|---|---|---|---|---|---|---|---|
| V-06 / V-06-RC2 | install dry run on a copy; RC2 FAIL (Rollback091 deletes files) | VERIFY | FAIL / blocked | install_v3 adoption | V-07 | S | `Builds/bm-RC2/verify/dropzone_sim.md` |
| install_v2 | review: guard bare string prefix, rollback deletes any manifest path | VERIFY | needs fixes (superseded) | - | - | S | `TF/install-v2-review.md` |
| install_v3 | guard fixed, rollback sha256-identical x3 (copies only) | BUILD | done on copies; NOT adopted | operator decision | all installs | S | `Working/Installer/install_v3.ps1`, `install_v3.py --check` |
| NEW-WLD-20 | Adopt install_v3 into each RC `install.ps1` generator (`bm_rc4.py`/`bm_rc.py`), regenerate receipt, re-run `dropzone_sim2.py` | BUILD | todo | operator decision on adoption | V-06 RC5 | M | `Tools/scripts/bm_rc4.py`; `TF/install-v3-guard-fix.md` |
| NEW-WLD-21 | Restore the live dropzone to a known state (it already holds RC2 payload; Rollback091 would delete) via install_v3 `Rollback` after backup | BUILD | todo | NEW-WLD-20, operator approval | Q-1 | S | GB tracker V-06-RC2 row |
| NEW-WLD-22 | Install `Rollback` when the car is owned/active in a save (missing-entity risk) | VERIFY | todo | Q-1 | release | S | UNKNOWN (no file) |
| 9190 | merge RC5 branches into a release candidate | BUILD | queued | 9171-9174, 9179 etc | 9191 | L | `Q/9190-rc5-merge-release-candidate.txt` |
| 9191/9192 | verify files/wiring/audio; geometry/predictions/install | VERIFY | queued | 9190 | 9193 | M | Q/9191, Q/9192 |
| 9193 | gate VX + approval request refresh | VERIFY | queued | 9191, 9192 | APPROVED_Q | S | `Working/Q/APPROVAL_REQUEST.md` |
| APPROVED_Q | operator writes `tmp/freebuff/APPROVED_Q.txt` | TEST | todo | 9193 | Q-1..Q-3 | S | file absent |
| 9194 | pilot cards refresh | PILOT | queued | 9193 | Q | S | Q/9194 |
| Q-PILOT | cards per atomic action | PILOT | todo | VX | Q | M | GB Q-PILOT |
| Q-0..Q-5 | in-game campaign (Q-1 static looks ~45 min, Q-2 driving, Q-3 world+combat ~45 min, fix loop, showcase) | TEST | todo | APPROVED_Q | QX | L | GB §9b; Q/8600-8605 |
| QX | all Q checks pass or named omissions accepted | TEST | todo | Q-1..Q-4 | R-1 | - | GB §9b |
| R-1 | release = pipeline only (no AK-extracted assets, `RELEASE.md`, `um publish check`) | RELEASE | todo | QX | R-2 | S | GB §10 |
| R-2 | KB field note | RELEASE | todo | QX | - | S | GB §10 |
| NEW-WLD-23 | Release portability: repack vs GOG vs Steam exe differences (BmSDK hook invalid on repack), JC3 patch level, dropzone location | RELEASE | todo | - | R-1 | M | `tmp/freebuff/QUEUE_MAP.md` 7995 |

## 2. (a) Done, with evidence

- G1-14 damage rules decoded (Health 1200 on 3 archetypes, ArmourModeDamageReduction 0, 14 entry points, regen "mechanism yes, value UNKNOWN"): `RB/DAMAGE_RULES.md` §4-5.
- G2-26/27/28/29/31/32/34 grabs: `RJ/REBELDROP.md`, `STANDALONE.md`, `DAMAGE_MODEL.md`, `TRAFFIC.md`, `WATER.md`, `NAMES.md`, `TETHER.md`.
- T-14 desk card and T-20 desk card: `TR/T10_DAMAGE.md`, `TR/T15_WORLD.md` (19 rows, 8/8 WLD).
- T-WLD8/9/10 entry/exit/stunt nodes in the entity graph (T-13): `TR/T9_INTERACTION.md`.
- B-09 health module (`Working/Damage/bm_health.json`), B-13 Rebel Drop files (`Builds/bm-013`, `bm-RC4-rebel`), both carried by `Builds/bm-RC4`.
- Verified offline: V-RC2-strings 18/18 (name 60A5E7A4, blurb F34BA8E8, 11 languages) `Builds/bm-RC2/verify/strings.md`; V-03-RC2 wiring dangling 0; V-06-fix and install_v3 on copies.
- Probe done in game: new leaf never spawns -> `_debug` leaf; the starter grant unlocks the car (MODLOG ~19668-19690).
- Closest-system plans written: `TF/health-to-explosion-no-crash-damage-plan.md`, `water-entry-teleport-closest-system-plan.md`, `remote-control-range-static-overlay-plan.md`, `summon-drive-in-closest-system.md`, `winch-and-tether.md`, `standalone-spawn-census-check.md`, `traffic-ai-claims-audit.md`, `weather-and-night-plan.md`, `surface-skids-and-tracks-plan.md`.
- Behaviour-verified: ZERO rows (`STATUS.md`).

## 3. (b) BLOCKERS, root-first

1. **Operator's 3 decisions/approvals**: APPROVED_Q.txt (gates every TEST item); install_v3 adoption; re-resolution of D-8 (teleport) and D-6 (leaf reality). Nothing downstream can finish without these.
2. **No RC5 damage/world trees exist.** Chain: 9033 apply wave -> 9100 scaffold + 9101 entity roots -> 9171/9173/9124 -> 9179 review -> 9190 merge -> 9191/9192 -> 9193. All 9xxx still queued.
3. **JC3 script/graph authoring unknown (NEW-WLD-03)**: water watcher, flip thrusters, homing and any "when X do Y" behaviour need a runtime logic carrier; no file read proves a mod can add one. If absent, 4 behaviours become gap-closing hard problems (not "no system", per the closest-system rule).
4. **`.btc` behaviour tree bodies undecoded (NEW-WLD-01)**: homing/summon goal member.
5. **Damage model (H0/H1/H2) unknown** until Q1-DM-A/B/C; health-scale ruling (NEW-ARM-03) cannot be finalised at desk.
6. **Death-sequence data absent (NEW-ARM-02)**: BmAK explosion/passenger-kill path in the exe.
7. **BmAK runtime reads blocked** (HealthRecoverRate value): BmSDK hook invalid on repack exe; gated by queue 7992-7995 and the game block on in-game research.
8. **Installer adoption** (V-06-RC2 FAIL stays until install_v3 is wired into the RC generator) and the live dropzone is already in "do not Rollback091" state.
9. **Collision hull incomplete** (2 of 3 BmAK boxes lack shape instance, 1 constraint omitted) limits WLD-5 shove/crush credibility.

## 4. (c) Open questions for the operator (player-only knowledge)

Damage:
1. How many tank-cannon hits (or missiles) destroy the Batmobile in BmAK, in pursuit mode vs battle mode? (The decoded ratio is 24 heavy-cannon hits of 50 against 1200; is that how it feels?)
2. Does regular enemy gunfire (rifles, MG, helicopter MG) truly leave the health bar still? What about mines, explosive barrels, a missile from a helicopter, a tank shell, and drone/Batwing fire?
3. Is there any health recovery you have seen (repair by driving to a point, upgrade/XP, a pickup, time out of combat)? Does the bar refill after you leave and re-summon the car?
4. When it explodes: how long between the bar hitting zero and the blast? Does the passenger always die, and is there a fall or flip first? Does the wreck disappear at once or leave debris/fire? Does Batman die or is it a game over/retry?
5. Does battle (armour) mode make the car noticeably tougher than pursuit, or is it the same toughness?
6. Do tyres ever get shot/burst? Does fire, smoke or sparks show when low on health, or truly nothing visible?
7. Do falls from height, trains, deep ocean drop or being pinned between vehicles ever hurt it?
8. How does ramming feel: do enemy cars and civilians get launched or destroyed? Can it knock down fences, posts, barricades and walls; what stops it?

World:
9. Water: teleports to where (the shore nearest the entry, last road, the player)? After how many seconds or metres? Does it also happen in shallow puddles/rivers? Does Batman die or lose health? Is there a message/sound/effect?
10. Does the car appear at a fixed spot when summoned (rear, front of the player, from an off-screen road), does it jump over obstacles, and how long does it take from LB press to arrival?
11. Can enemies or NPCs get in or steal it? Do they shoot at it? How do civilian cars and police react to the Batmobile (flee, ignore, attack)?
12. Does it ever appear in traffic, and does it persist after you leave (despawn distance)?
13. Winch/tow: is there any airlift or tow behaviour for the Batmobile you can describe (e.g. Batwing carry, winch cable)?
14. Weather: any rain or night look changes you remember (wet body, lights)? Do tyres leave tracks or skid marks you can see on all road types?
15. Acceptance items: do you accept written halts for remote driving (static overlay, 150 m limit) given the Rebel Drop is the summon? Do you accept the English-only blurb until translations exist?

## 5. (d) Risks

- Entity leaf/replacement risk: `_debug` leaf is unproven at runtime; if the hash/archive path behaves differently than in the probe, WLD-1/2/8 and the whole Rebel Drop route fail. Also any other mod touching `profile/*.onlinec` collides.
- Visible-damage conflict (NEW-ARM-05) and health scale 36000 vs 1200 may make the car feel wrong and break lore accuracy.
- Occupant kill on explosion may be impossible with JC3 data (500 player damage in 5 m radius is damage, not a scripted kill).
- Teleport-to-land requires a runtime trigger that data may not carry (NEW-WLD-03). If unavailable the fallback is not "sink and stall" (overturned).
- Graph/script behaviours are chosen numbers (0.30, 0.15 s, 3.0 s, 8-40 m ring) with no decoded BmAK values (`TF/water-entry-teleport-closest-system-plan.md`).
- 36 unexplained entity diffs in V-RC2-entity (root CCar rename, added palette member), 34 dropped CPartProp (`Builds/bm-RC2/verify/entity_diff.md`, `entity_unexplained.md`) could hide damage-related objects.
- Rollback with owned/active car in a save; save corruption. Always `um backup` first (GB §9b).
- Release legality: AK assets cannot be shared (R-1); only pipeline releasable, so the end product is rebuild-from-own-copies.
- Tooling debt: stale checkers (`v05_driving`, `t_boost_rows`, `t_vnf_six`) and the T-14 label confusion inflate or hide progress; STATUS counts "evidenced" rows, not verified.
- Platform differences: repack vs GOG vs Steam exe (BmSDK hook invalid).
- 12 of 23 texture rows unfaithful (RC4 `complete: false`) and mode pair unmerged: world tests will run on an incomplete RC.

## 6. (e) Remaining effort (this landmark only)

Counts from the tables (approximate): ~35 desk/build/verify work items (S 20, M 12, L 3-4) plus 6 operator-gated test items.

- Agent briefs: desk (grab/translate/reconcile) ~14 sessions; build/RC5 (9171, 9173, 9124, 9174, 9050, merge, installer adoption, NEW-* builds) ~18 sessions incl. rework; verify ~6 sessions. Total about 38-45 agent-sessions, plus ~15 repair sessions after the first verify (RC4 history shows repeated red/repair loops).
- At ~100 small-model briefs/day the queue is not the limit; serial dependencies are (9033 -> 9100 -> 9101 -> 9171/9173/9124 -> 9179 -> 9190 -> 9191/9192 -> 9193; QUEUE_MAP notes the apply chain is serial). Estimated calendar: desk and build to RC5 merge 4-6 days; verify and approval request 1-2 days; operator approval latency unbounded.
- Operator in-game: Q-1 (~45 min), Q-2, Q-3 (~45 min) = 3 sessions, plus 2-3 fix-loop sessions (Q-4 caps at one extra per original) = 5-6 sessions, 1 per day realistically => 5-6 calendar days plus waits between fixes (1-2 days each for rebuilds). Q1-DM-A/B/C can be folded into Q-1 #6 so no extra session.
- Release R-1/R-2: 1-2 days.
- **Total calendar for ARM+WLD to a released, verified product: about 14-20 days** if the operator is available daily and the 9xxx chain does not stall; with two or more repair loops expect 25-30. Biggest uncertainties: NEW-WLD-03 (graph authoring), NEW-ARM-02 (death path), and the D-6/D-8 re-resolutions.
