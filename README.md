# Arkham Knight Batmobile → Just Cause 3

A lore-accurate port of the **Batman: Arkham Knight Batmobile** into **Just Cause 3**: the true-scale body, pursuit
and battle modes, the BmAK weapons and gadgets, the handling, sound, HUD and camera. It is built from each player's
own copies of both games. **This repository ships no game files.** It holds the research, the translation ledger,
the build scripts and the agent work queue that produce the mod.

## Status (2026-11-08)

| stage | state |
|---|---|
| Grab: decode BmAK and catalogue JC3 | done on the desk: 423/423 BmAK offsets, 81,953/81,953 JC3 archive entries named |
| Translate: one ledger row per BmAK feature | 148/221 rows resolved, 0 verified in game yet |
| Build | release candidates RC1–RC4 built offline; RC5 in progress |
| Native hook | started: built on [jc3-console-thingy](https://github.com/aaronkirkham/jc3-console-thingy) v1.1, whose addresses match the 2025-12-17 JC3 exe |
| In-game testing | starting now, agent-piloted |

The live plan is [`ROADMAP.md`](ROADMAP.md): 12 landmarks (appearance, handling, weapons, sound, HUD, battle mode,
skins, release …), with root blockers and a self-updating completion estimate (`Tools/scripts/project_eta.py`).
Every remaining task is queued as a brief in `tmp/freebuff/queue/`, with dependencies.

## Help wanted

If you have played or modded **either game**, there is a concrete task you could take on:

- **Steam Arkham Knight + BmSDK:** read six live Batmobile values that the cooked files don't hold: the LT hold time,
  the eject charge window, the steering curve at speed, the health regen rate, the summon numbers, and the physics asset
  in use. A read-only reader is in `Tools/scripts/` (brief 7976). Our GOG copy lacks 22 BmSDK addresses.
- **JC3 reverse engineering (2025-12-17 exe):** the vehicle object (health, velocity, transform), the handling/tune
  struct for per-mode handling, seating the player in a spawned vehicle, and part transforms at runtime.
- **Avalanche formats:** appending a new ADF type (camera shake), growing a `.effc` (new emitters), and FMOD/FSB5 sample
  authoring for JC3's banks.
- **Scaleform:** does a re-saved `ui/hud.gfx` load from the dropzone?
- **Players:** BmAK gameplay facts the files can't answer: lock timings, eject heights, transform details. The facts
  gathered so far are in `ROADMAP.md` §7.

Open an issue or a discussion with what you know. Evidence beats memory: say what you measured and how.

## Rules this project keeps

- No game files, extracted assets or decompiled code in the repo. The pipeline rebuilds from your own installs.
- Every value carries its provenance (decoded / derived / UNKNOWN). Nothing is filled in from memory.
- Lore accuracy first. Where JC3 has no direct system, the closest system is named and the build closes the gap.

## Credits

Built with [Gibbed's JC3 tools](https://github.com/gibbed), [Deca](https://github.com/kk49/deca),
[JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler), [UE Viewer (umodel)](https://www.gildor.org/en/projects/umodel),
[BmSDK-AK](https://github.com/Team-BmSDK/BmSDK-AK), [jc3-console-thingy](https://github.com/aaronkirkham/jc3-console-thingy)
(MIT) and [universal-modder](https://github.com/rehan-remade/universal-modder). Batman: Arkham Knight © Warner Bros. /
Rocksteady; Just Cause 3 © Square Enix / Avalanche Studios. This is a fan project with no affiliation.
