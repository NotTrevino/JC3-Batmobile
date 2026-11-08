# EMP burst experiments - do the stated results hold up against the files they cite?

Card: 8821-emp-burst-route-result-check. 2026-11-08.

## Count

**5 experiments (E1-E5): 0 CONFIRMED, 0 CONTRADICTED, 5 UNKNOWN.**

The premise of the brief does not hold: `tmp/freebuff/reports/emp-burst-fire-route-experiments.md`
does **not** state a result for any experiment. It states a **PASS/FAIL band** for each
(`:60`, `:77`, `:93`, `:108`, `:124`) and then records, in its own checks table, that the experiments
were never run:

> `:217` `| game launched / packed / installed | **no** - the experiments are specified, not run (test ban); nothing written outside this file |`

and again at `:48`:

> `:48` `Each card is one edit, one launch, one observation; PASS/FAIL is a number, not an impression.`

So there is no stated result to confirm or contradict, and no run log to open: the build tree every
card depends on — `Builds/test-092` (`:46`) — **does not exist** (`glob Builds/test-09*` returns 0
files). All five are therefore **UNKNOWN**, and the honest reason is *not* "the cited log is absent"
but "the report itself says no result was produced". Marking any of them CONFIRMED would be inventing
a result; marking one CONTRADICTED would be inventing a failed run.

Path note: the brief writes `Reports/…`; no `reports/` directory exists at the repository root
(`glob reports/*.md` returns two unrelated files). The report and this audit both live under
`tmp/freebuff/reports/`, which is also the path on the card's DONE line.

## One row per experiment

"A cited log" = the run log the card implies; "cited file" = the evidence file the card's steps name.
The cited files are real and say what the card says they say (see §2) — what is missing is any
statement of what happened when the card was executed.

| # | experiment (route) | result the report states | cited log the step implies | log present? | cited file(s) | cited file present? | status | matching line quoted from the cited file |
|---|---|---|---|---|---|---|---|---|
| E1 | `CEMPWeapon` in the secondary driver slot — route (b) | **none** — only a band: "PASS = the APC stops moving and stops firing within 1 s … on 3/3 attempts" (`:60-62`) | `Builds/test-092` pack + one launch (`:56`, `:58`) | **no** — `Builds/test-09*` absent | `EMP.md` §6, `WEAPON_WIRING.md` | yes | **UNKNOWN** | `EMP.md:164` `| class | CEMPWeapon | CEMPWeapon |` — and `EMP.md:215` `no \`CEMPWeapon\` appears among the fleet's vehicle weapon` (the gap E1 was meant to close, not a result) |
| E2 | EMP tune on a weapon-owned pulse — route (a) | **none** — band only: "PASS = the EMP effect (`explosion_emp_flatbed`) plays … on 3/3" (`:77-79`) | pack, install, fire the missile (`:83`) | **no** | `FORCEPULSE.md` §4.2, `EMP_DISABLE.json` §pulse | yes | **UNKNOWN** | `EMP_DISABLE.json` → `pulse.flag_triples` = `{"0,0,0":16,"0,1,1":1,"1,0,0":278,"1,0,1":12}`, `pulse.pulses` = `307`; `FORCEPULSE.md:197` `| \`CMissileWeaponBase\` | 25 |` — the decode the card is built on, not an outcome |
| E3 | truck's use-item graph on the car — route (c) | **none** — band only: "PASS = the `ui_activate_emp` prompt appears within 2 s on 5/5 stops" (`:93-94`) | pack, install, stop in the box, observe prompt (`:97`) | **no** | `EMP.md` §3/§7 | yes | **UNKNOWN** | `EMP.md:81` `| prompt | \`ui_activate_emp\` |`, `EMP.md:82` `| \`trigger.use_item\` (\`CInteractionTrigger\`) position | \`(0, 1.3507, 2.396)\` |` — the donor's shape, not a test |
| E4 | flag triple alone at 0 damage on the car's own pulse — route (e) | **none** — band only: "PASS = the cop stops without taking damage, on 3/3" (`:108-109`) | pack, install, detonate (`:114`) | **no** | `FORCEPULSE.md` §3 | yes | **UNKNOWN** | `FORCEPULSE.md:195` `| \`CCar\` | 126 |` (the pattern the card copies); no 0-damage EMP-flagged run is recorded anywhere in the file |
| E5 | is there a graph node that fires a pulse — route (d) | **none** — band only: "PASS = one node names the pulse object id … FAIL = no node names it" (`:124-125`) | the `.gdc`/`.gsc` decode itself (`:126`), no game launch | **no** — no decode output file exists | `v4603_plane_urga_cargotransport_mm340.ee`, `FORCEPULSE.md` §4.2 | `.ee` is **outside this repo** (not opened); `FORCEPULSE.md` yes | **UNKNOWN** | `FORCEPULSE.md:280` `exactly 1 reference that is not the owner` — the pointer E5 would decode, **not** its node list; the decode step was never run, so no PASS/FAIL exists |

Rows E1-E4 fail the same way: the report's own §6 says no game was launched (`:217`). Row E5 is
file-only and *could* have been run without the test ban, but no decode output is cited and none
exists, so it is UNKNOWN for the same practical reason — no stated result.

## 2. What the report does state, and which parts do check out

Not experiment results, but the decode claims each card rests on — these are the only "results" in
the file, and **all of them verify** against the cited files. Worth separating, because it means the
experiments are well-founded even though none has been run.

| claim in the report | cited file | verified? | matching line |
|---|---|---|---|
| 4 flag triples over 307 pulses: `0,0,0` 16 / `0,1,1` 1 / `1,0,0` 278 / `1,0,1` 12 (`:73`, `:213`) | `Research/JC3Grab/EMP_DISABLE.json` | **yes**, byte-identical | `pulse.flag_triples` = `{"0,0,0":16,"0,1,1":1,"1,0,0":278,"1,0,1":12}`, `pulse.pulses` = `307` |
| `is_disabled_by_emp` = **0** hash occurrences in the `.ee` corpus (`:182`, `:213`) | same | **yes** | `data.hash_occurrences` = `{"electricity_armor":1,"invulnerable":289,"is_disabled_by_emp":0,"is_in_water":160}` |
| `CEMPWeapon` 6 tokens at `0x23E9428`; `.?AVCEMPWeapon@@` at `0x2D6E058` (`:32`) | same | **yes** | `exe.tokens`: `"CEMPWeapon": {"occurrences": 6, "offset": "0x23E9428"}`, `".?AVCEMPWeapon@@": {"offset": "0x2D6E058"}` |
| `SetVehiclePartVulnerability` at `0x241B020` (`:184`) | same | **yes** | `exe.tokens` → `"SetVehiclePartVulnerability": {"offset": "0x241B020", "occurrences": 1}` |
| engine shutdown delays: car **30 s**, boat/bike/heli/plane **5 s**, "`WATER.md` lines 229-233" (`:186`, `:215`) | `Research/JC3Grab/WATER.md` | **yes**, and the line range is exact | `WATER.md:229` `| \`boat_common.engine_shut_down_delay_s\` | \`5\` x232 |` … `WATER.md:230` `| \`car_common.engine_shut_down_delay_s\` | \`30\` x232 |` … `WATER.md:233` `| \`plane_common.engine_shut_down_delay_s\` | \`5\` x232 |` |
| shipped pulse-owner pattern **25** missile / **29** bullet / **126** `CCar` (`:33`, `:120`, §3.1 #4) | `Research/JC3Grab/FORCEPULSE.md` | **yes** | `FORCEPULSE.md:197` `| \`CMissileWeaponBase\` | 25 |`, `:194` `| \`CBulletWeaponBase\` | 29 |`, `:195` `| \`CCar\` | 126 |` |
| "the fleet's **only** non-owner pulse reference" (`:120`, `:123`) | same | **yes** | `FORCEPULSE.md:280` `exactly 1 reference that is not the owner` |
| `w503_turret_emp` is class `CEMPWeapon` with a `CTurretWeaponComponent`; no `CEMPWeapon` among the fleet's 88 vehicle weapon components (`:52`, `:213`) | `Research/JC3Grab/EMP.md` | **yes** | `EMP.md:164` `| class | CEMPWeapon | CEMPWeapon |`; `EMP.md:223` `the 88 vehicle weapon components in` |
| use-item donor: state `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp`, trigger box `(0, 1.3507, 2.396)` (`:88`) | same | **yes** | `EMP.md:80-82` `| \`entry.use_item\` … | \`S_STUNT_USE_ITEM_VEHICLE\` |` / `| prompt | \`ui_activate_emp\` |` / `| \`trigger.use_item\` … | \`(0, 1.3507, 2.396)\` |` |

**One thing not checked:** E5's donor entity
`v4603_plane_urga_cargotransport_mm340.ee` lives in the external game-data tree, not in this
repository. It was not opened, so even the *existence* of that pointer is unverified here — which
makes E5 UNKNOWN twice over (no result stated, and its primary artefact outside the repo).

## 3. What would turn each row into a real CONFIRMED/CONTRADICTED

| # | the missing artefact | then the status becomes |
|---|---|---|
| E1 | a `Builds/test-092` install plus a run log recording "APC stopped ≤ 1 s, stayed 2 s, 3/3" | CONFIRMED if the log shows 3/3 within the band; CONTRADICTED if the APC kept driving |
| E2 | same build, a missile-impact log with `explosion_emp_flatbed` + a ≥ 2 s stop | CONFIRMED / CONTRADICTED on that evidence |
| E3 | a run log of 5 stops showing the prompt and the pulse | CONFIRMED / CONTRADICTED |
| E4 | a detonation log with a 5 m cop car, 0 damage, car stopped | CONFIRMED / CONTRADICTED |
| E5 | the `.gdc`/`.gsc` node-list decode **output file** for the mm340 graph | CONFIRMED if a node names the pulse id; CONTRADICTED if none does |

Until one of those files exists, no row can honestly carry CONFIRMED, and none does.

## 4. Checks run

| check | result |
|---|---|
| experiments in the report | 5 (`E1`…`E5`, `:50`-`:129`) |
| stated outcomes | **0** — every card has a PASS/FAIL *band* only |
| report's own run status | `:217` "experiments are specified, not run (test ban)" |
| `Builds/test-092` / `Builds/test-091` | **absent** (`glob Builds/test-09*` → 0 files) |
| run logs cited | none cited, none found |
| cited evidence files | 5 of 5 in-repo files present (`EMP.md`, `EMP_DISABLE.json`, `FORCEPULSE.md`, `WATER.md`, `WEAPON_WIRING.md`); the `.ee` donor is outside the repo and unopened |
| decode claims re-checked | 9 of 9 match the cited file, quoted in §2 |
| game launched / anything built or packed | **no** — this audit read files only; nothing written outside this file |

## 5. Verdict

The experiments are **not wrong**, they are **unrun**. The audit finds no contradiction anywhere —
every decodable premise confirms — but it also finds **no experiment result to confirm**, and the
report says so itself. If the card expected CONFIRMED rows, the expectation was based on a report
that does not exist: this one is a plan with pass bands, not a log with outcomes. The next real step
is E1 or E5, because E1 is the only route with a firing button and E5 is the only one that needs no
game launch.
