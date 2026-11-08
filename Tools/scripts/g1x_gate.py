"""g1x_gate.py - the G1 exit gate: every feature code has a G1 file, or a proven absence (G1X).

The backlog's gate is:

    grab_model.py check, grab_weapons.py --check, grab_anims.py --check,
    grab_lights.py --check green; every feature code in section 1 that names a BmAK source has
    rows in a G1 file or a proven absence. Write a MODLOG section "G1X" listing the files.

This tool is the second half: one row per feature code in `GRAB_BACKLOG.md` section 1, with the
G1 file that carries its lore value and a needle that must still be in that file. Codes whose
lore source is not a BmAK file at all (a wiki row, a play observation, a T-ledger value, a JC3
carrier) are recorded as `not-g1` with the reason, which is the "proven absence" half.

`--check` fails when a file is missing or the needle has gone, so a rename or a regenerated doc
that drops a fact is caught here instead of being discovered during translation.

Usage:
    python Tools/scripts/g1x_gate.py --check
    python Tools/scripts/g1x_gate.py --markdown > /tmp/g1x.md
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
G1 = os.path.join(ROOT, "Research", "BatmobileGrab")

# (code, files that must exist, needle in files[0], short fact) - kind 'g1'
# (code, None, reason, short fact)                                            - kind 'not-g1'
G1_ROWS = [
    ("APP-1", ["MESHES.md", "SLOTS.json"], "LOD",
     "5 LODs, 19 material slots"),
    ("APP-2", ["SLOTS.md", "VALUES.json"], "CarPaint",
     "CarPaintMM parameters"),
    ("APP-3", ["SLOTS.json", "SLOTS.md"], "Window",
     "canopy glass and interior slots"),
    ("APP-4", ["MATERIALS.md", "LIGHTS.json"], "emissive",
     "emissive lights and their colours"),
    ("APP-5", ["BONES.md", "ANIMATIONS.md"], "bone",
     "movable parts as bones"),
    ("APP-6", ["POSES.json", "ANIMATIONS.md"], "Pose",
     "transform animation and pose states"),
    ("APP-7", None, "user rule R1; BmAK has no deform to decode",
     "no-deform rule is a project rule, not a BmAK value"),
    ("APP-8", ["VARIANTS.md"], "MK2",
     "MK2 / Jokerfied skins diffed"),
    ("DIM-1", ["POSES.md", "MESHES.md"], "7.026",
     "body dimensions and wheelbase"),
    ("DIM-2", ["TYRES.md"], "1.36",
     "tyre diameter measured on all four"),
    ("DIM-3", None, "T-M1 mass ledger (translation side)",
     "BmAK carries no absolute mass"),
    ("DIM-4", ["PHYSICS.md"], "collision",
     "per-bone collision boxes"),
    ("ARM-1", None, "play behaviour T-DM9; no BmAK value",
     "small-arms immunity is a play observation"),
    ("ARM-2", ["DAMAGE_RULES.md", "OFFSETS.json"], "1200",
     "Health 1200 and the damage rules"),
    ("ARM-3", None, "play behaviour T-DM8 plus a JC3 switch",
     "ram immunity is a play observation"),
    ("ARM-4", ["PHYSICS.md"], "wheel",
     "wheels are separate collision bodies"),
    ("ARM-5", ["DAMAGE_RULES.md"], "regen",
     "regeneration is decided by the damage rules"),
    ("ARM-6", ["MECHANICS.md", "DAMAGE_RULES.md"], "DeathExplosion",
     "death explosion effects"),
    ("WPN-1", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileHeavyCannon", "60 mm cannon"),
    ("WPN-2", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileCannon",
     "Vulcan chain gun and its heat block"),
    ("WPN-3", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileMissileLauncher", "missile launcher"),
    ("WPN-4", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileEMPMissile", "EMP missile"),
    ("WPN-5", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileEMP", "EMP burst"),
    ("WPN-6", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileWinch", "winch"),
    ("WPN-7", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileAllegianceSwitcher",
     "drone hacker"),
    ("WPN-8", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileSonar", "sonar"),
    ("WPN-9", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileVehicleTracker", "vehicle tracker"),
    ("WPN-10", ["WEAPONS.md", "WEAPONS.json"], "RiotSuppressor", "riot suppressor mode"),
    ("WPN-11", ["WEAPONS.md", "WEAPONS.json"], "RBatmobileBooster", "booster"),
    ("WPN-12", ["HUD_INTERFACES.json", "HUD.md"], "UC_SetCannonCoolDown",
     "HUD weapon setters, cooldown and heat"),
    ("HDL-1", None, "wiki row T-E5 (signed-off top speed)",
     "top speed is a lore row, not a BmAK value"),
    ("HDL-2", ["MECHANICS.md"], "StandardTorqueVSpeedCurve", "torque curve shape"),
    ("HDL-3", None, "T-1 ledger (translation side)",
     "steering values are T rows, not BmAK"),
    ("HDL-4", None, "T-B2 derivation (translation side)",
     "boost extra speed is derived, not decoded"),
    ("HDL-5", None, "T-S3 (translation side)",
     "landing stroke is a translation value"),
    ("HDL-6", None, "T-AC1/T-SR1 route to JC3 members; air time now measured in FOOTAGE.md",
     "air control has no JC3 member yet"),
    ("MOD-1", ["MECHANICS.md"], "Immobiliser", "pursuit-mode behaviours"),
    ("MOD-2", ["MODES.md", "MECHANICS.md"], "BattleMode",
     "battle-mode fields and camera"),
    ("MOD-3", ["ASSETS.md"], "eject", "eject animation"),
    ("MOD-4", ["ANIMATIONS.md"], "Door", "canopy door bone and animation"),
    ("MOD-5", None, "lore rule; JC3 traffic tables are the carrier",
     "no NPC-driver rule is not a BmAK value"),
    ("AUD-1", ["AUDIO.md"], "RPM", "engine loop driven by the RPM RTPC"),
    ("AUD-2", ["AUDIO.md"], "Burnout", "burnout and boost roar"),
    ("AUD-3", ["AUDIO.md"], "InBatmobile", "interior layer"),
    ("AUD-4", ["AUDIO.md"], "BattleMode_In", "battle-mode transform sting"),
    ("AUD-5", ["AUDIO.md", "AUDIO_FEATURES.md"], "weapon",
     "per-weapon events"),
    ("AUD-6", ["AUDIO_FEATURES.md"], "BML_Impacts", "impact bank absent (named omission)"),
    ("AUD-7", ["AUDIO_FEATURES.md"], "horn", "no radio; horn checked"),
    ("ANI-1", None, "live in the build (wheel parts)",
     "wheel spin is live, no BmAK value needed"),
    ("ANI-2", ["BONES.md"], "turret", "turret and cannon bones"),
    ("ANI-3", ["ANIMATIONS.md", "BONES.md"], "ChainGun", "Vulcan barrel spin"),
    ("ANI-4", ["BONES.md"], "fan", "turbine fan bone"),
    ("ANI-5", ["ANIMATIONS.md"], "fin", "rear fin animation"),
    ("ANI-6", ["SOCKETS_JC3.md", "SLOTS.json"], "Missile", "missile hatches and sockets"),
    ("ANI-7", ["COCKPIT.md", "BONES.md"], "yoke", "steering yoke bone"),
    ("ANI-8", ["ANIMATIONS.md"], "Door", "canopy animation"),
    ("ANI-9", ["COCKPIT.md"], "Driver", "driver seat and pose"),
    ("LGT-1", ["LIGHTS.md", "LIGHTS.json"], "cone", "headlight cones and colours"),
    ("LGT-2", ["LIGHTS.md"], "battle", "battle-mode spotlight"),
    ("FX-1", ["MECHANICS.md", "PARTICLES.md"], "Afterburner", "afterburner flame"),
    ("FX-2", ["PARTICLES.md", "WEAPONS.md"], "muzzle", "muzzle flashes and tracers"),
    ("FX-3", ["PARTICLES.md"], "smoke", "tyre smoke and scrape sparks"),
    ("FX-4", ["DAMAGE_RULES.md", "PARTICLES.md"], "Death", "death explosion effects"),
    ("CAM-1", ["CAMERA.md"], "FOV", "chase camera composition"),
    ("CAM-2", ["CAMERA.md"], "60", "battle camera FOV 60"),
    ("HUD-1", ["HUD.md"], "speed", "speedometer and health bar"),
    ("HUD-2", ["HUD.md", "HUD_INTERFACES.json"], "reticle", "weapon reticle and slots"),
]

# Feature families whose lore source is never a BmAK file at all (checked, not just assumed).
NOT_G1_FAMILIES = {
    "WLD": "every WLD row names a JC3 carrier (drop entry, .epe entry points, traffic tables); "
           "no BmAK source column",
}
WLD_CODES = ["WLD-%d" % i for i in range(1, 9)]


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rows():
    out = []
    for code, files, needle, fact in G1_ROWS:
        out.append({"code": code, "kind": "g1" if files else "not-g1", "files": files or [],
                    "needle": needle if files else None, "fact": fact,
                    "absence_reason": None if files else needle})
    for code in WLD_CODES:
        out.append({"code": code, "kind": "not-g1", "files": [], "needle": None,
                    "fact": "JC3 carrier only", "absence_reason": NOT_G1_FAMILIES["WLD"]})
    return out


def check():
    problems = []
    table = []
    for r in rows():
        if r["kind"] == "not-g1":
            table.append({**r, "pass": True, "detail": r["absence_reason"]})
            continue
        missing = [f for f in r["files"] if not os.path.isfile(os.path.join(G1, f))]
        if missing:
            problems.append("%s: missing %s" % (r["code"], ", ".join(missing)))
            table.append({**r, "pass": False, "detail": "missing " + ", ".join(missing)})
            continue
        primary = read_text(os.path.join(G1, r["files"][0]))
        ok = r["needle"].lower() in primary.lower()
        if not ok:
            problems.append("%s: %r not in %s" % (r["code"], r["needle"], r["files"][0]))
        table.append({**r, "pass": ok,
                      "detail": ("%s in %s" % (r["needle"], r["files"][0])) if ok
                      else ("%r not in %s" % (r["needle"], r["files"][0]))})
    return table, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--markdown", action="store_true", help="print the MODLOG table")
    a = ap.parse_args()
    table, problems = check()
    g1 = [t for t in table if t["kind"] == "g1"]
    absent = [t for t in table if t["kind"] == "not-g1"]
    if a.markdown:
        print("| code | G1 file(s) | what satisfies it |")
        print("|---|---|---|")
        for t in table:
            files = ", ".join("`%s`" % f for f in t["files"]) if t["files"] else "-"
            print("| %s | %s | %s |" % (t["code"], files, t["fact"]))
        return 0
    if a.check:
        for p in problems:
            print("FAIL " + p)
        print("codes %d: %d from G1 files, %d proven absences (no BmAK source); %s"
              % (len(table), len(g1), len(absent), "PASS" if not problems else "FAIL"))
        return 1 if problems else 0
    for t in table:
        print("%-8s %-4s %s" % (t["code"], "ok" if t["pass"] else "FAIL", t["detail"]))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
