# Operator priorities and leads (verbatim from the operator, with dates)

Source: operator messages of 2026-11-05 (14:33Z, 14:42Z) in the Claude chat for this project. Kept in the repo so every lane and later chat can read them.

## Weapon ranking (highest priority first)
1. **Tracker + EMP missile** (the EMP missile does not work without the tracker)
2. **Booster mesh**
3. **EMP burst**
4. **Hacker** ("not many drones in JC3")
5. **Sonar** (lowest; mission-dependent in BmAK - tracking treadmarks on the road; outside missions it is just a good-looking pulse, operator 2026-11-06)

The ranking orders weapon work (translation, build, test); it never removes a weapon. All BmAK weapons are required (operator 2026-11-06). The other weapons (cannon, Vulcan, riot mode, missile pods) are not ranked here: they are not below sonar by default; ask the operator before ranking them.

## HUD leads (Batmobile)
- Health bar: top left, in battle mode.
- Afterburner gauge: left, in pursuit mode; the afterburner's second (quick-recharge / cooldown speed-up) cooldown gauge sits to the left of the afterburner.
- The Batmobile has no speedometer: disable JC3's.
- Radar / minimap icons: cops have their own icon; tracked vehicles have their own green icon; military vehicles have their own icon; hacked vehicles change from red to green; icons are mostly arrows that point the direction the vehicle faces (pointer-like); tanks have bigger arrows; helicopters have their own icon (an arrow with spinning blades).

## Open question from the operator (2026-11-05)
"How do we know immobilizer missiles are EMP missiles? or is that effective transplant functionality?" - to be answered from BmAK data (queue brief 8706).

## Leads on "JC3 has no system" rows (2026-11-06)
- Winch: model = Rico's grappling hook / tether.
- Hacker / allegiance: SAM sites can be hacked and then target enemy aircraft; drones cannot be hacked but can be Rebel Dropped as your own; tracker: some missions and random encounters track a vehicle with a distance readout and a yellow or grey circle above it.
- Two modes: no lead.
- Fire Leech (JC3): lock-on HUD, heat-seeks after firing (carrier lead for the lock-on missile).

## Compromise protocol
2026-11-05: compromises need the operator's approval, relayed through Claude; each lane notes its recommended compromise.
2026-11-06 (later, supersedes where stricter): lore accuracy is the only option; "JC3 has no system" is never an answer; find the closest JC3 system and let the build close the gap (see `STAGES.md`).

## Steam copy of BmAK for BmSDK live scraping (operator question 2026-11-06)
BmSDK-AK (Team-BmSDK, cloned at `E:/Modding/_shared/tools/BmSDK-AK`) supports **Steam copies only**; its README says EGS/GOG do not work. This project uses its generated class dump for offsets (`Tools/scripts/bmsdk_offsets.py`, `BMSDK_OFFSETS.json`), but only statically. The installed copy is GOG (the same cooked packages as Steam, version 1.999, Season Pass included), so no package data is missing; what a Steam copy adds is the **running game's object memory**: live runtime values of the Batmobile (the vehicle sim, the physics asset the engine actually uses, the 925 native/untagged objects, event-to-bank links, final material values). That is the "runtime oracle" the 2026-11-02 reset findings said was missing, and a route to the drivable collision. Not started: needs the operator to obtain a Steam copy and to decide that launching BmAK (not JC3) for read-only scraping is allowed.

## Answer to the operator's immobilizer question (report 8706, 2026-11-06)
Yes: the data makes the Immobiliser the EMP missile (`RBatmobileEMPMissile` fires the immobilising round; BmAK puts the "Immobiliser" string on that round's impact sound), not an effective transplant. The tracker is a separate launcher (`RBatmobileVehicleTracker`) on the same button and socket and is the half that tags the target - consistent with the ranking "tracker + EMP missile". Source: `tmp/freebuff/reports/immobilizer-vs-emp-missile.md` (read-only report, no `--check` script, not a tracker flip).

## Rulings of 2026-11-08 (roadmap session, relayed by Claude)
- **Lanes:** restart approved; `NO_RESTOCK` lifted.
- **RC4 probes now:** approved. Agents pilot under operator supervision. If piloting fails or proves too time-consuming, the operator returns to manual piloting. `APPROVED_Q.txt` is written only once the operator is present to supervise. Full sessions 8601-8605 and 8699 are held in `queue/held/`; the approval releases only Q-0 (8600) and the probe session (8606).
- **Piloting needs a web search for both games first** (wheel-reinvention check): brief 7973, which now gates Q-0. Briefs 7970-7972 cover the JC3MP runtime, JC3 community writers, and BmAK UE3 runtime tools.
- **Native hooks permitted**, "as is likely for any other bright idea that may speed up the project". Native code (R17) is no longer excluded from closest-system routes (mode swap, input scoping, HUD feed).
- **BmAK copies:** the DODI repack is incompatible with BmSDK; GOG worked better (BmSDK runtime starts, but 22 of 25 native addresses are still UNKNOWN; reports `bmsdk-gog-*.md`). There is no Steam copy.
- **JC3 install** (operator 2026-11-08): a repack based on Steam BuildID 20206564 (2025-12-17), not Steam-owned. The install holds `steam_api64.rne` and `steam_emu.ini`. JC3MP requires owning JC3 on Steam (SteamDB `MustOwnAppToPurchase` 225540; FAQ: "Steam must be running"), so the JC3MP route is blocked on this install (`tmp/freebuff/reports/jc3mp-runtime-platform-check.md`).
- **JC3MP** (operator 2026-11-08: "try JC3MP anyway; if it fails, native hooks based on it"): the client was refused by Steam (No subscription). The fallback is a native hook modelled on the JC3MP contract, built on jc3-console-thingy v1.1, whose addresses match the operator's exe (brief 7974).
- **Full in-game campaign approved** (operator 2026-11-08: "write APPROVED_Q_FULL too, i'll supervise"): `tmp/freebuff/APPROVED_Q_FULL.txt` gates every in-game brief from the all-work queue. Agents pilot; the operator supervises.
