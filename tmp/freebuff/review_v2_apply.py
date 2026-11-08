#!/usr/bin/env python
"""review_v2_apply.py -- the queue rewrite of the v2-apply wave review (2026-11-08).

Applies, per brief, exact string replacements plus one appended provenance line. Idempotent: a
brief that already carries the marker is refused, never edited twice. Run from the repo root:

    python tmp/freebuff/review_v2_apply.py

Nothing else is touched: no DONE header is changed, no brief is deleted or reordered, and the only
structural edits are the two AFTER lists named in EDITS ('9130' gains two, '9140' loses one,
'9194' gains six).
"""
import io
import os
import sys

QUEUE = "tmp/freebuff/queue"
MARK = "Updated by review v2-apply (2026-11-08):"

# file -> (list of (old, new), appended line)
EDITS = {
    "9105-rc5-lock-hold-salvo-reticle.txt": ([
        ("covers the held lock of 2.0 s with the 8-target salvo: BmAK carries MissileLockOnDuration "
         "and MaxTargets, JC3 carries neither (AutoAimSettings has 22 members, missile_per_shot is 1).",
         "covers the held lock of 2.0 s and the barrage: BmAK carries MissileLockOnDuration and "
         "MaxTargets, JC3 carries neither (AutoAimSettings has 22 members, missile_per_shot is 1). "
         "Operator 2026-11-08: the barrage auto-fires at full lock (no separate fire press) and the "
         "target count is 1/4/7/10 by upgrade level, so build the fully upgraded 10; the decoded "
         "MaxTargets 8 is kept beside it and never overwritten (CONFLICT on record)."),
        ("and the composed salvo of eight rounds",
         "and the composed salvo at the lore maximum of ten rounds, with the decoded MaxTargets 8 "
         "carried beside it"),
        ("Build per reports/lock-hold-salvo-reticle-plan-v2.md: the pursuit circle",
         "Pursuit carries one fire slot and the lock/salvo is that slot's weapon (operator "
         "2026-11-08), so the reticle and the salvo are pursuit behaviour, not a battle one. Build "
         "per reports/lock-hold-salvo-reticle-plan-v2.md: the pursuit circle"),
    ], "autofire at full lock, 1/4/7/10 targets by level, decoded MaxTargets 8 kept as a conflict, pursuit-only slot"),

    "9110-rc5-cannon-vulcan-riot-pods.txt": ([
        ("Riot mode: base damage 0 with an impulse and a 0.75 s cadence on a second weapon entity "
         "(B-15 note in the task 8305 text under tmp/freebuff/done).",
         "Riot mode: base damage 0 with an impulse and a 0.75 s cadence on a second weapon entity "
         "(B-15 note in the task 8305 text under tmp/freebuff/done). The cannon, the Vulcan and the "
         "riot pods are battle-only: pursuit fires the EMP missile and nothing else (operator "
         "2026-11-08), so every set written here is gated to battle."),
        ("Missile pods and barrage: eight targets, reports/missile-pod-salvo-plan.md.",
         "Missile pods and barrage: auto-fire at full lock, targets 1/4/7/10 by upgrade level (build "
         "10), with the decoded 8 recorded beside the conflict, reports/missile-pod-salvo-plan.md."),
        ("Done line: all members read back",
         "Binds (operator 2026-11-08): RT = cannon, RB = Vulcan. Done line: all members read back"),
    ], "battle-only gating, RT/RB binds, barrage 1/4/7/10 with auto-fire"),

    "9130-rc5-mode-pair-and-swap.txt": ([
        ("Close B-12. RC4 ships the pursuit set only;",
         "Close B-12. Operator facts of 2026-11-08 change the pair's content: pursuit carries the "
         "EMP missile alone while battle carries the rest, so the two variants must differ in their "
         "weapon sets and not only in their handling; armour is identical in both modes, so T-MD10 "
         "is mode-invariant and is not a battle scalar; and the transform takes about 2 s with a "
         "near-instant speed loss, so the swap carries health and ammunition, never velocity, and "
         "the animation and the HUD must cover the 2 s window. RC4 ships the pursuit set only;"),
        ("AFTER: E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-drive-modes-and-yaw.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-suspension-travel.md, ",
         "AFTER: E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-drive-modes-and-yaw.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-suspension-travel.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-cannon-vulcan-riot-pods.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-lock-hold-salvo-reticle.md, "),
    ], "per-mode weapon sets, mode-invariant armour, 2 s transform with speed loss; AFTER gains the two weapon branches the per-mode decision depends on"),

    "9143-rc5-paint-channels.txt": ([
        ("Operator rule: the body colour is the exact decoded BmAK colour; JC3's brighter lighting "
         "makes it look different and that is accepted, the combine rule is low priority.",
         "Operator rule: the body colour is the exact decoded BmAK colour; JC3's brighter lighting "
         "makes it look different and that is accepted, the combine rule is low priority. Target "
         "(operator 2026-11-08, reports/operator-facts-ledger-impact.md F6): dark gunmetal satin with "
         "a specular edge response, carbon-weave insets and white chevron decals. The white-violet "
         "RC result is rejected on lightness and on hue. Whether carbon-weave and chevron carriers "
         "exist is still a check, so name the closest member or the exact missing card for each "
         "instead of dropping them."),
    ], "gunmetal satin target, carbon-weave insets and white chevrons added as acceptance, RC white-violet rejected"),

    "9170-rc5-controls-entry-exit-eject.txt": ([
        ("eject is a double press of A (Eject Into Glide) with the car breaking straight",
         "eject has three levels - hold A to charge the height, tap A for a higher eject, double-tap "
         "A for the lowest (operator 2026-11-08; Eject Into Glide) - with the car breaking straight"),
        ("Find which carrier holds each action",
         "The keymap carries the binding only: the three eject levels are runtime logic, so name the "
         "code or graph that selects them (mode card NEW-MOD-2 in "
         "Working/Roadmap/modes_controls_anim.md is answered by this fact; NEW-MOD-5's window length "
         "stays open). Find which carrier holds each action"),
    ], "three-level eject replaces the double-press-only reading, with the level logic called out as code"),

    "9171-rc5-health-explosion-no-crash.txt": ([
        ("a destroyed car is not left drivable.",
         "a destroyed car is not left drivable. Health also regenerates out of combat and returns "
         "full on re-summon (operator 2026-11-08): the mechanism is required lore, carried on RB-9, "
         "while the rate value stays UNKNOWN (NEW-ARM-01 in Working/Roadmap/damage_world.md). The "
         "explosion is instant at zero health, so do not add the donor's engine-fire or smoke "
         "stages: T-FX22 and T-FX23 are dropped, and the .effc decode stays as reference only."),
    ], "out-of-combat regen and full health on re-summon added, burn/smoke stages dropped (T-FX22/23)"),

    "9194-rc5-pilot-cards-refresh.txt": ([
        ("AFTER: E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-gate-vx-approval-request.md",
         "AFTER: E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-gate-vx-approval-request.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-lock-hold-salvo-reticle.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-cannon-vulcan-riot-pods.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-mode-pair-and-swap.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-paint-channels.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-controls-entry-exit-eject.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-health-explosion-no-crash.md"),
        ("Add cards for the new behaviours the branches predict",
         "Cards must also encode the operator facts of 2026-11-08 (reports/operator-facts-ledger-impact.md): "
         "pursuit fires only the EMP missile, the eject has three levels, the body is gunmetal satin "
         "with carbon-weave insets and white chevrons, the barrage auto-fires at full lock with "
         "1/4/7/10 targets, RT is the cannon and RB the Vulcan, and Working/Q/PILOT/CONTROLS.md is "
         "refreshed to match. Add cards for the new behaviours the branches predict"),
    ], "encodes the six operator facts into the cards and CONTROLS.md; AFTER gains the six branches whose bands it reads"),

    "9140-rc5-texture-rows.txt": ([
        ("AFTER: E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-scaffold-and-merge-script.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/locate-missing-pixel-sets.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/paint-plans-v2.md",
         "AFTER: E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/rc5-scaffold-and-merge-script.md, "
         "E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/paint-plans-v2.md"),
    ], "AFTER loses reports/locate-missing-pixel-sets.md, which does not exist; the pixel-set source is Working/Appearance/PIXEL_LOCATE.md, already cited in the body"),

    "9120-rc5-handling-values.txt": ([
        ("nitro_boost torque_multiplier 6.3 with heat_boost and nitro_boost_upgraded grip 1.5 and "
         "extra 80",
         "nitro_boost torque_multiplier 6.3 with heat_boost and nitro_boost_upgraded grip 1.5 and "
         "extra 80 (the boost grip and speed block is the donor decode applied by the v2 pass, "
         "reports/boost-selector-and-moving-parts-plans-v2.md)"),
    ], "the boost grip/speed cells now cite the v2 donor decode that set them"),

    "9123-rc5-air-control-and-ram.txt": ([
        ("Tree Builds/bm-RC5-movement, script Tools/scripts/rc5_movement.py",
         "The ledger rows this serves are T-AC1 (air control) and T-RA1 (ram assist), both moved to "
         "next by the v2 apply pass with the corrected D3/D4 numbers. "
         "Tree Builds/bm-RC5-movement, script Tools/scripts/rc5_movement.py"),
    ], "names the two ledger rows the v2 pass moved to next"),

    "9124-rc5-flip-water-remote.txt": ([
        ("For each, name the JC3 mechanism the plan chose",
         "The rows this serves are T-WT1 (water entry) and T-FR1 (flip recovery after an idle wait), "
         "both moved to next by the v2 apply pass; the remote half stays halted with the written "
         "reason in the plan, which is a note and not a disposition of out. For each, name the JC3 "
         "mechanism the plan chose"),
    ], "names the two row ids the v2 pass moved to next and restates that the halted remote half is a note, not an out"),

    "9172-rc5-moving-parts-animation.txt": ([
        ("Moving parts P-01 to P-15 (Working/Translation/T8_PARTS.md, PARTS_ANIM_COVERAGE.md).",
         "Moving parts P-01 to P-15 (Working/Translation/T8_PARTS.md, PARTS_ANIM_COVERAGE.md), as "
         "the v2 apply pass left those cells: read the ledger rows before the older plan tables."),
    ], "points the part rows at the post-v2 ledger cells"),

    "9160-rc5-hud-build.txt": ([
        ("First establish by bytes which of these can be authored: hud.gfx rewrite",
         "reports/hud-gfx-ffdec-roundtrip.md (2026-11-08) already answers the rewrite half offline: "
         "FFDec 26.4.0 re-saves ui/hud.gfx keeping the CFX header, the 2,405-tag order and the single "
         "DoABC byte-identical, with 839 of 839 exported shapes SVG-identical after the re-encode; a "
         "receipted payload sits in Builds/probe-L0/P3-hud-gfx/payload/ui/hud.gfx (one text tag "
         "edited, chid 2241). The open question is the loader, not the writer, and it is listed there "
         "as UNKNOWN. First establish by bytes which of these can be authored: hud.gfx rewrite"),
    ], "cites the FFDec round-trip report and the built P3 payload as the answered rewrite half"),
}


def main():
    touched = []
    for name, (pairs, tail) in sorted(EDITS.items()):
        path = os.path.join(QUEUE, name)
        if not os.path.exists(path):
            print("MISSING brief: %s" % name)
            return 2
        with io.open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
        if MARK in text:
            print("skip (already applied): %s" % name)
            continue
        for old, new in pairs:
            if old not in text:
                print("FAIL %s: anchor not found: %r" % (name, old[:70]))
                return 1
            text = text.replace(old, new, 1)
        if not text.endswith("\n"):
            text += "\n"
        text += MARK + " " + tail + "\n"
        with io.open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        touched.append(name)
        print("edited: %s" % name)
    print("\n%d brief(s) edited" % len(touched))
    return 0


if __name__ == "__main__":
    sys.exit(main())
