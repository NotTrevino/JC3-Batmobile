"""g2x_gate.py - the G2 exit gate: every feature code in section 1 has a JC3 carrier, or a
proven absence (G2X).

The backlog's gate is:

    every new reader has `--check` green; P0-2 census re-run; every feature code in section 1 has a
    JC3 carrier with evidence or a proven absence. MODLOG section "G2X".

This tool is all three halves.

1.  **Readers.**  The 24 scripts the G2 cards wrote (`jc3weapons.py` ... `jc3tether.py`) plus the
    P0-2 census are run as subprocesses in their own `--check` mode.  A non-zero exit, or no line
    starting with `PASS` / `OK` / `check ok` (the first such line is the verdict; readers such as
    `damage_predict.py` print more lines under it), fails the gate.  The pass/fail comparison uses
    the reader's **status** (command, exit, verdict, ok); the full verdict sentence is recorded as
    evidence but is not compared, so a reworded PASS cannot turn a green gate red.  `--no-readers`
    reuses the recorded block and says so ("recorded") in the `--check` summary line; the two
    artefacts are only written by `--write`, which always re-runs the readers (`readers_mode` in
    the JSON records which mode produced the file).
2.  **Carriers.**  One row per feature code in `GRAB_BACKLOG.md` section 1.  The code set is
    **parsed from section 1 itself** (`section1_codes()`), never typed, so a new or renamed code
    fails the gate instead of being skipped.  Each row names the generated file that carries the
    JC3 mechanism and a needle that must still be in it.  A regenerated doc that drops the fact
    fails here, which is the point: the gate is re-derivable, not remembered.  A needle's strength
    is derived and printed (`number` / `identifier` / `phrase` / `word`), so the summary cannot
    imply stronger evidence than the weakest row has.
3.  **Proven absences.**  A negative cannot be a needle.  Those rows instead name the census
    surface that is complete (the 103-class fleet class inventory in `ENTITIES.md`, the
    1,421-member module vocabulary in `VOCABULARY.md`), one word per named file that must be
    there to prove that surface was read (`anchor`, or `anchors` parallel to `files`), and the
    words that would name the mechanism if JC3 had one.  Any of those
    words appearing fails the row.  What this proves is that the mechanism is not in the fleet's
    decoded space; it does not prove the engine could not do it in native code, and every row
    where that distinction matters says so in its fact cell.

Rows whose *value* waits on a section 11 decision carry the decision id.  The gate reports the
decision's state from the backlog itself and does not count the row as a gap: section 7 rule 6
makes the decision a phase-T block (`blocked: D-n`), not a phase-G2 one.

Usage:
    python Tools/scripts/g2x_gate.py --write      # regenerate G2X.md + G2X.json
    python Tools/scripts/g2x_gate.py --check      # re-run readers, re-derive rows, compare
    python Tools/scripts/g2x_gate.py --check --no-readers   # rows only (fast; says "recorded")
    python Tools/scripts/g2x_gate.py --markdown   # print the md (runs the readers)
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
TR = os.path.join(ROOT, "Working", "Translation")
OUT_MD = os.path.join(JC3, "G2X.md")
OUT_JSON = os.path.join(JC3, "G2X.json")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
PY = sys.executable

# --------------------------------------------------------------------------------------------
# 1. The readers this gate runs.  (label, argv tail).  Every one is a G2 card's own --check.
# --------------------------------------------------------------------------------------------
READERS = [
    ("G2-10 weapons", ["jc3weapons.py", "--check"]),
    ("G2-11 wiring", ["jc3wiring.py", "--check"]),
    ("G2-12 signature diff", ["jc3sigdiff.py", "--check"]),
    ("G2-13 turret", ["jc3turret.py", "--check"]),
    ("G2-14 moving parts", ["jc3moving.py", "--check"]),
    ("G2-15 doors", ["jc3doors.py", "--check"]),
    ("G2-16 EMP", ["jc3emp.py", "--check"]),
    ("G2-17 force pulse", ["jc3forcepulse.py", "--check"]),
    ("G2-18 interaction", ["jc3interact.py", "--check"]),
    ("G2-19 seat", ["jc3seat.py", "--check"]),
    ("G2-20 eject", ["jc3eject.py", "--check"]),
    ("G2-21 tank turn", ["jc3tankturn.py", "--check"]),
    ("G2-22/23 usage + nitro", ["jc3usage.py", "--check"]),
    ("G2-24 audio", ["jc3audio.py", "--check"]),
    ("G2-25 HUD weapons", ["jc3hudwpn.py", "--check"]),
    ("G2-26 rebel drop", ["jc3rebeldrop.py", "--check"]),
    ("G2-27 standalone", ["jc3standalone.py", "--check"]),
    ("G2-28 damage model", ["damage_predict.py", "--check"]),
    ("G2-29 traffic", ["jc3traffic.py", "--check"]),
    ("G2-29 physics write", ["jc3hkx.py", "write", "--check"]),
    ("G2-31 water", ["jc3water.py", "--check"]),
    ("G2-32 names", ["jc3strings.py", "--check"]),
    ("G2-33 lights", ["jc3lights.py", "--check"]),
    ("G2-34 tether", ["jc3tether.py", "--check"]),
]
CENSUS = ("P0-2 feature census", ["jc3_feature_census.py", "--check"])
OK_PREFIXES = ("PASS", "OK", "check ok")

# --------------------------------------------------------------------------------------------
# 2. The 75 feature codes of section 1.
#
#    kind    "needle"     -> files[0] must contain needle (case-insensitive)
#            "vocab-scan" -> files[0] must contain anchor, and none of must_not may appear
#    verdict "carrier"    -> JC3 mechanism exists, with the file that proves it
#            "absence"    -> no JC3 mechanism in the decoded fleet; the fact says what is absent
#    decision             -> section 11 id whose answer the *value* waits on (never the carrier)
# --------------------------------------------------------------------------------------------
F = "Research/JC3Grab"
T = "Working/Translation"
ROWS = [
    # ---- 1.1 appearance -------------------------------------------------------------------
    dict(code="APP-1", kind="needle", verdict="carrier", files=[F + "/GEOMETRY.md"], needle="56136",
         fact="56,136 meshes over 233 entities decode (GEOMETRY.md, a fleet count, not the "
              "Batmobile body); 806,529 material slots are counted per block"),
    dict(code="APP-2", kind="needle", verdict="carrier", files=[F + "/GEOMETRY.md"],
         needle="CarPaintMM", fact="CarPaintMM blocks re-encode byte-exact, so paint is editable"),
    dict(code="APP-3", kind="needle", verdict="carrier", files=[F + "/GEOMETRY.md"],
         needle="Window", fact="12,028 Window (glass) blocks decoded, canopy is a material switch"),
    dict(code="APP-4", kind="needle", verdict="carrier", files=[F + "/LIGHT_SYSTEM.md"],
         needle="CarLight", fact="CarLight block format (11,367 blocks) + the wheel-arch recipe with a source per member"),
    dict(code="APP-5", kind="needle", verdict="carrier", files=[F + "/PARTS_TABLE.md"],
         needle="11643", fact="11,643 part rows, each with its own model: moving parts are separate meshes"),
    dict(code="APP-6", kind="needle", verdict="carrier", files=[F + "/TURRET.md"], needle="179",
         fact="turret yaw +-179 / cannon -5..20 reach the battle pose as part angles; which drop "
              "entry carries it is section 11 D-2's answer, not this row's", decision="D-2"),
    dict(code="APP-7", kind="needle", verdict="carrier", files=[F + "/DAMAGE_MODEL.md"],
         needle="deform_scale", fact="deform_scale is a real module switch (0 in the build = no crumple)"),
    dict(code="APP-8", kind="needle", verdict="carrier", files=[F + "/REBELDROP.md"], needle="45 items",
         fact="the 3 shipped mod variants add 39+45+45 drop items, so extra entries are a solved path",
         decision="D-5"),
    # ---- 1.2 dimensions and mass ----------------------------------------------------------
    dict(code="DIM-1", kind="needle", verdict="carrier", files=[F + "/FLEET.md"], needle="wheelbase",
         fact="per-vehicle geometry/handling table: body box, wheelbase, track"),
    dict(code="DIM-2", kind="needle", verdict="carrier", files=[F + "/PHYSICS.md"], needle="land_global",
         fact="station quads agree with land_global wheel data, so the wheel radius is a readable member"),
    dict(code="DIM-3", kind="needle", verdict="carrier", files=[F + "/TETHER.md"], needle="975",
         fact="232-mass census, donor 975; the unit is UNKNOWN, so 6 t is a class row, not a decode"),
    dict(code="DIM-4", kind="needle", verdict="carrier", files=[F + "/PHYSICS_WRITE.md"],
         needle="54 hulls", fact="the hull writer round-trips all 54 hulls byte-identically"),
    # ---- 1.3 armour and damage ------------------------------------------------------------
    dict(code="ARM-1", kind="needle", verdict="carrier", files=[F + "/DAMAGE_MODEL.md"],
         needle="shotgun", fact="the arm census sets the ARM-1 gate (shotgun 144/pull): the ceiling is a domain argument, not a member"),
    dict(code="ARM-2", kind="needle", verdict="carrier", files=[F + "/DAMAGE_MODEL.md"], needle="2000",
         fact="three health profiles with their channels; the build already carries the tank's 2000 HP"),
    dict(code="ARM-3", kind="needle", verdict="carrier", files=[F + "/DAMAGE_MODEL.md"],
         needle="impact_damage_factor", fact="the impact switch exists and ships at 0 in the build (shipped range 1..12)"),
    dict(code="ARM-4", kind="needle", verdict="carrier", files=[F + "/DAMAGE_MODEL.md"],
         needle="Land_Wheel", fact="part damage table with the Land_Wheel row (the build's one change: instantly_damaged_by_bullets 1->0)"),
    dict(code="ARM-5", kind="vocab-scan", verdict="absence", files=[F + "/VOCABULARY.md"],
         anchor="max_health", must_not=["regen", "recover"],
         fact="no health-regeneration member in the 52-type / 1,421-path vocabulary: ARM-5 is a named omission"),
    dict(code="ARM-6", kind="needle", verdict="carrier", files=[F + "/USAGES.md"], needle="OnExploded",
         fact="OnExploded (2 vehicles) / Explosion (23) usage names exist: the death effect is selected by a usage key on the entity"),
    # ---- 1.4 weapons and gadgets ----------------------------------------------------------
    dict(code="WPN-1", kind="needle", verdict="carrier", files=[F + "/WEAPONS.md"],
         needle="w602_mediumtank_canon", fact="tank cannon tune, fully decoded (25 ids)"),
    dict(code="WPN-2", kind="needle", verdict="carrier", files=[F + "/WEAPONS.md"],
         needle="w603_mediumtank_mgun", fact="tank MG tune; barrel spin is a part behaviour (GatlingGun)"),
    dict(code="WPN-3", kind="needle", verdict="carrier", files=[F + "/WEAPONS.md"],
         needle="w618_sportsmuscle_missile", fact="the donor chassis's own missile weapon, tune + wiring decoded"),
    dict(code="WPN-4", kind="needle", verdict="carrier", files=[F + "/EMP.md"], needle="w702",
         fact="CEMPWeapon w702/w503 exist, but neither tune carries an EMP field: the missile half is the effect"),
    dict(code="WPN-5", kind="needle", verdict="carrier", files=[F + "/EMP.md"], needle="weapon-slot copy",
         fact="the EMP burst is an entity-level CForcePulse copy, which a car can carry"),
    dict(code="WPN-6", kind="vocab-scan", verdict="absence",
         files=[F + "/VOCABULARY.md", F + "/ENTITIES.md"],
         anchors=["max_health", "CPartProp"], must_not=["winch"],
         fact="no winch member path in the 52-type / 1,421-path vocabulary and no winch class in the 103-class fleet census (0 occurrences in both, measured); rope/winch geometry ships on 4 entities (TETHER.md §4) but no part can pull: WPN-6 is a named omission"),
    dict(code="WPN-7", kind="vocab-scan", verdict="absence", files=[F + "/ENTITIES.md"],
         anchor="CBulletWeaponBase", must_not=["allegian", "hacker", "hijack"],
         fact="no allegiance-switch class in the 103-class fleet census: named omission"),
    dict(code="WPN-8", kind="vocab-scan", verdict="absence", files=[F + "/ENTITIES.md"],
         anchor="CForcePulse", must_not=["sonar"],
         fact="no sonar class in the 103-class census; CForcePulse is the shockwave half only"),
    dict(code="WPN-9", kind="vocab-scan", verdict="absence", files=[F + "/ENTITIES.md"],
         anchor="CPOI", must_not=["tracker", "tracking"],
         fact="no tracker class in the 103-class census (the only 'track' is CMusicTrack): named omission"),
    dict(code="WPN-10", kind="vocab-scan", verdict="absence", files=[F + "/VOCABULARY.md"],
         anchor="part_damage_types", must_not=["lethal", "tranquil", "incapacit"],
         fact="no non-lethal flag in the member space: the riot-suppressor mode is a named omission",
         decision="D-3"),
    dict(code="WPN-11", kind="needle", verdict="carrier", files=[F + "/USAGES.md"], needle="nitro_boost",
         fact="arcade.nitro_boost on 145/232 vehicles: the booster gadget is nitro"),
    dict(code="WPN-12", kind="needle", verdict="carrier", files=[F + "/JC3_HUD_WEAPONS.md"],
         needle="MCI_vehicle_weapons0", fact="two weapon slots, reticle shapes, cooldown; heat is a stated absence"),
    # ---- 1.5 handling ---------------------------------------------------------------------
    dict(code="HDL-1", kind="needle", verdict="carrier", files=[F + "/VOCABULARY.md"],
         needle="official_top_speed", fact="vehicle_misc.official_top_speed is a readable member"),
    dict(code="HDL-2", kind="needle", verdict="carrier", files=[F + "/VOCABULARY.md"],
         needle="LandEngine", fact="LandEngine + Transmission modules carry the torque curve"),
    dict(code="HDL-3", kind="needle", verdict="carrier", files=[F + "/VOCABULARY.md"],
         needle="LandSteering", fact="LandSteering / Brakes / Suspension / CustomLandGlobal.drift are readable"),
    dict(code="HDL-4", kind="needle", verdict="carrier", files=[F + "/USAGES.md"], needle="40 km/h",
         fact="nitro_boost adds a flat km/h on top of torque and grip"),
    dict(code="HDL-5", kind="needle", verdict="carrier", files=[F + "/VOCABULARY.md"],
         needle="suspension", fact="Suspension module: length / min_length / strength / compression"),
    dict(code="HDL-6", kind="vocab-scan", verdict="absence", files=[F + "/VOCABULARY.md"],
         anchor="takeoff_pitch_damping", must_not=["air_control", "upright"],
         fact="land vehicles carry gravity_multiplier_* and takeoff_pitch_damping (n=145) but no yaw authority; righting_torque exists only in DriverLean (n=23 aircraft). Air control / self-righting = named omission (T-AC1, T-SR1)"),
    # ---- 1.6 modes ------------------------------------------------------------------------
    dict(code="MOD-1", kind="needle", verdict="carrier", files=[F + "/USAGES.md"], needle="nitro_boost",
         fact="pursuit mode is the default drive: arcade.nitro_boost (145/232) is the afterburner, the EMP burst is the entity copy (G2-16) and ram immunity is the switch (G2-28)"),
    dict(code="MOD-2", kind="needle", verdict="carrier", files=[F + "/TANKTURN.md"],
         needle="named omission", fact="turret/cannon parts carry the weapons; turn-on-the-spot is a named omission; the pursuit/battle split is section 11 D-2's answer, not this row's", decision="D-2"),
    dict(code="MOD-3", kind="needle", verdict="carrier", files=[F + "/EJECT.md"], needle="moving.parachute",
         fact="exit.driver.moving.parachute is the fast exit on 221/232 vehicles; the upward launch has no member"),
    dict(code="MOD-4", kind="needle", verdict="carrier", files=[F + "/DOORS.md"], needle="canopy",
         fact="door behaviour + part index + limited hinge in the .physicsc: the canopy can open"),
    dict(code="MOD-5", kind="needle", verdict="carrier", files=[F + "/TRAFFIC.md"], needle="ambient",
         fact="the donor is civilian traffic (ambient selector); a standalone entity avoids NPC copies"),
    # ---- 1.7 sound ------------------------------------------------------------------------
    dict(code="AUD-1", kind="needle", verdict="carrier", files=[F + "/JC3_AUDIO.md"], needle="LandAudio",
         fact="engine_running_sound attached effect + LandAudio.min_rpm/max_rpm (1,000/10,000)"),
    dict(code="AUD-2", kind="needle", verdict="carrier", files=[F + "/JC3_AUDIO.md"],
         needle="exhaust_upgrade_nitrous", fact="nitro/burnout events on exhaust_upgrade_nitrous*; three samples already swapped"),
    dict(code="AUD-3", kind="vocab-scan", verdict="absence", files=[F + "/JC3_AUDIO_EVENTS.json"],
         anchor="speedwind_sound_player", must_not=["cabin", "interior"],
         fact="no cabin/interior event name in the 45-event donor census (0 occurrences of either, measured); the nearest is speedwind_sound_player: named omission unless a bank swap adds one"),
    dict(code="AUD-4", kind="needle", verdict="carrier", files=[F + "/JC3_AUDIO.md"],
         needle="deferred with D-2",
         fact="no mode-switch event exists in the donor; the transform sting exists only if a second variant ships",
         decision="D-2"),
    dict(code="AUD-5", kind="needle", verdict="carrier", files=[F + "/JC3_AUDIO.md"], needle="weapons.bank",
         fact="weapon .ee SAttachedEffect + weapons.bank samples: per-weapon sound has a carrier"),
    dict(code="AUD-6", kind="needle", verdict="carrier", files=[F + "/JC3_AUDIO.md"],
         needle="wheel_suspension_", fact="JC3's own tyre/impact events are kept (BmAK has no impact bank)"),
    dict(code="AUD-7", kind="needle", verdict="carrier", files=[F + "/JC3_AUDIO.md"], needle="horn",
         fact="horn is a per-model SAttachedEffect (178) to delete; 0 radio objects in the fleet"),
    # ---- 1.8 animation --------------------------------------------------------------------
    dict(code="ANI-1", kind="needle", verdict="carrier", files=[F + "/PARTS_TABLE.md"], needle="wheel",
         fact="wheel slots per part: spin and steer are part-level, already live in test-091"),
    dict(code="ANI-2", kind="needle", verdict="carrier", files=[F + "/TURRET.md"], needle="Cannon",
         fact="Turret/Cannon parts with pivots, axes and limits on 8 vehicles"),
    dict(code="ANI-3", kind="needle", verdict="carrier", files=[F + "/MOVING_PARTS.md"], needle="GatlingGun",
         fact="GatlingGun behaviour driven by weapon_rpm (racing boat driver-fired)"),
    dict(code="ANI-4", kind="needle", verdict="carrier", files=[F + "/MOVING_PARTS.md"],
         needle="EngineRotatingPart", fact="EngineRotatingPart driven by engine_rpm (v0506 tractor fan)"),
    dict(code="ANI-5", kind="needle", verdict="carrier", files=[F + "/MOVING_PARTS.md"], needle="AirBrake",
         fact="AirBrake exists but is proven only on a CAirPlane: land use is a Q probe"),
    dict(code="ANI-6", kind="needle", verdict="carrier", files=[F + "/DOORS.md"], needle="MissileHatch",
         fact="16 MissileHatch doors on the monorail missile car; the trigger is code-side"),
    dict(code="ANI-7", kind="needle", verdict="carrier", files=[F + "/MOVING_PARTS.md"],
         needle="SteeringWheel", fact="SteeringWheel driven by steering_turn, proven on 9 chassis"),
    dict(code="ANI-8", kind="needle", verdict="carrier", files=[F + "/DOORS.md"], needle="canopy",
         fact="the same door behaviour covers the canopy on entry/exit"),
    dict(code="ANI-9", kind="needle", verdict="carrier", files=[F + "/SEAT.md"], needle="0.855",
         fact="seat part candidate 0.855 m, 10 mm under the BmAK Driver hip; pose via rico_base"),
    # ---- 1.9 world interaction ------------------------------------------------------------
    dict(code="WLD-1", kind="needle", verdict="carrier", files=[F + "/REBELDROP.md"], needle="hash_jenkins",
         fact="Item.Name = jenkins hash of the entity leaf; the recipe for a Batmobile entry exists"),
    dict(code="WLD-2", kind="needle", verdict="carrier", files=[F + "/NAMES.md"], needle="KERNER SERPENTE R",
         fact="name/blurb pairs keyed by the leaf hash, 11 languages, plus the icon key rule"),
    dict(code="WLD-3", kind="needle", verdict="carrier", files=[F + "/INTERACTION.md"], needle="entry.driver",
         fact="85 entry/exit/point objects with their transforms; the Batmobile verdict per point"),
    dict(code="WLD-4", kind="needle", verdict="carrier", files=[F + "/INTERACTION.md"], needle="stunt",
         fact="3 active stunt-area triangle sets with their welds; point.stunt* objects decoded"),
    dict(code="WLD-5", kind="needle", verdict="carrier", files=[F + "/TETHER.md"], needle="6000",
         fact="mass is a readable member: donor 975, the build's 6 t class target 6,000 = 6.154x the donor, compared as a ratio because the unit is UNKNOWN"),
    dict(code="WLD-6", kind="needle", verdict="carrier", files=[F + "/WATER.md"], needle="will_sink",
         fact="will_sink + buoyancy + the fleet-wide water-entry damage and 30 s engine shut-down"),
    dict(code="WLD-7", kind="needle", verdict="carrier", files=[F + "/TETHER.md"],
         needle="Can a vehicle be carried",
         fact="a vehicle can be carried by the 12 CVehicleCargoBay vehicles (cargo plane, transport boat, flatbed) and the donor's mass is 6.154x under the target; helicopter airlift is UNKNOWN (0 cargo bays on 23 helicopters)"),
    dict(code="WLD-8", kind="needle", verdict="carrier", files=[F + "/TRAFFIC.md"],
         needle="spawn_vehicle_defs", fact="the donor's traffic record is in spawn_vehicle_defs.bin; a standalone leaf never enters it"),
    # ---- 1.10 lights, effects, camera, HUD ------------------------------------------------
    dict(code="LGT-1", kind="needle", verdict="carrier", files=[F + "/LIGHT_SYSTEM.md"],
         needle="VehicleDynamicLights", fact="3,217 light entries + CarLight blocks + the wheel-arch recipe"),
    dict(code="LGT-2", kind="needle", verdict="carrier", files=[F + "/LIGHT_SYSTEM.md"],
         needle="VEHLT_BattleModeLight", fact="the battle spotlight is the same socket's second behaviour value",
         decision="D-2"),
    dict(code="FX-1", kind="needle", verdict="carrier", files=[F + "/USAGES.md"], needle="EngineNitro",
         fact="EngineNitro usage -> dynamic_nitrous, 9 nitrous .effc paths: the flame has a slot"),
    dict(code="FX-2", kind="needle", verdict="carrier", files=[F + "/SIGNATURE_DIFF.md"],
         needle="muzzleflash", fact="the armed Serpente's own muzzleflash .effc, paired to its 4 fire points"),
    dict(code="FX-3", kind="needle", verdict="carrier", files=[F + "/VOCABULARY.md"], needle="tire_effects",
         fact="vehiclecommon.tire_effects (23 members): skid and smoke thresholds are readable"),
    dict(code="FX-4", kind="needle", verdict="carrier", files=[F + "/USAGES.md"], needle="Explosion",
         fact="Explosion / OnExploded / OnPartExplode usages: the death effect is an entity attachment"),
    dict(code="CAM-1", kind="needle", verdict="carrier", files=[T + "/T6_HUD_CAMERA.md"],
         needle="car_base.ctune", fact="car_base.ctune decoded: 13 T-CAM rows, chase camera built in test-091"),
    dict(code="CAM-2", kind="needle", verdict="carrier", files=[T + "/T6_HUD_CAMERA.md"], needle="T-CAM10",
         fact="no battle-camera member (T-CAM10 out): the carrier is a second .ctune per variant",
         decision="D-2"),
    dict(code="HUD-1", kind="needle", verdict="carrier", files=[T + "/T6_HUD_CAMERA.md"], needle="MCI_speedo",
         fact="MCI_speedo, InitVehicleNitrous and the vehicle health bar all exist in hud.gfx"),
    dict(code="HUD-2", kind="needle", verdict="carrier", files=[F + "/JC3_HUD_WEAPONS.md"],
         needle="MCI_vehicle_weapons0", fact="2 weapon slots, 14 reticle shapes, one lock-on POI"),
]

# The feature codes are PARSED from §1 (`section1_codes`), not typed. This regex is the only
# shape assumption: a table row of §1 whose first cell is a feature code.
CODE_ROW_RE = re.compile(r"^\|\s*([A-Z]{2,4}-\d+)\s*\|")


def section1_codes():
    """The feature codes of `GRAB_BACKLOG.md` §1, in file order, parsed from its table rows.

    §1 is the only definition of the requirement set. A row list that agrees with a copied
    literal agrees by hand, which is what an exit gate must not rely on.
    """
    out, in_s1 = [], False
    for line in read_text(BACKLOG).splitlines():
        if line.startswith("## 1. "):
            in_s1 = True
            continue
        if in_s1 and line.startswith("## 2. "):
            break
        if in_s1:
            m = CODE_ROW_RE.match(line)
            if m:
                out.append(m.group(1))
    if not out:
        raise SystemExit("GRAB_BACKLOG.md §1: no feature codes parsed")
    return out


def family_text(codes):
    """'APP 8, DIM 4, …' in §1 order, derived from the parsed codes."""
    order, counts = [], {}
    for c in codes:
        fam = c.split("-")[0]
        if fam not in counts:
            order.append(fam)
            counts[fam] = 0
        counts[fam] += 1
    return ", ".join("%s %d" % (f, counts[f]) for f in order)


def needle_kind(needle):
    """How strong a needle is: a number catches data drift, a short word catches almost nothing."""
    if not re.search(r"[A-Za-z]", needle):
        return "number"
    if " " in needle:
        return "phrase"
    if re.search(r"[_.:/*-]", needle) or re.search(r"\d", needle) or len(needle) >= 8:
        return "identifier"
    return "word"


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


# --------------------------------------------------------------------------------------------
# section 11 decisions
# --------------------------------------------------------------------------------------------
def decisions():
    """Parse the section 11 register: id -> resolved flag + the recommendation cell."""
    text = read_text(BACKLOG)
    m = re.search(r"^## 11\..*?$(.*?)^---", text, re.S | re.M)
    out = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        if not line.startswith("| D-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        out[cells[0]] = {"resolved": "resolved" in cells[3].lower(),
                         "recommendation": cells[3], "blocks": cells[4]}
    return out


# --------------------------------------------------------------------------------------------
# rows
# --------------------------------------------------------------------------------------------
def check_rows():
    problems, table = [], []
    for r in ROWS:
        row = dict(r)
        row.setdefault("decision", None)
        row.setdefault("anchor", None)
        row.setdefault("anchors", None)
        row.setdefault("must_not", [])
        missing = [f for f in r["files"] if not os.path.isfile(os.path.join(ROOT, f))]
        if missing:
            problems.append("%s: missing %s" % (r["code"], ", ".join(missing)))
            row.update(pass_=False, detail="missing " + ", ".join(missing))
            table.append(row)
            continue
        first = read_text(os.path.join(ROOT, r["files"][0]))
        if r["kind"] == "needle":
            ok = r["needle"].lower() in first.lower()
            detail = "%r in %s" % (r["needle"], r["files"][0]) if ok \
                else "%r not in %s" % (r["needle"], r["files"][0])
            row["needle_kind"] = needle_kind(r["needle"])
        else:
            # every named file carries its own anchor, so a two-file absence proves both surfaces
            # were read; `anchors` runs parallel to `files` and defaults to the single `anchor`.
            anchors = r.get("anchors") or [r["anchor"]] * len(r["files"])
            if len(anchors) != len(r["files"]):
                problems.append("%s: %d anchors for %d files" % (
                    r["code"], len(anchors), len(r["files"])))
            texts = [(f, first if f == r["files"][0] else read_text(os.path.join(ROOT, f)))
                     for f in r["files"]]
            unread = ["%r in %s" % (a, f) for (f, t), a in zip(texts, anchors)
                      if a.lower() not in t.lower()]
            hits = ["%r in %s" % (w, f) for f, t in texts for w in r["must_not"]
                    if w.lower() in t.lower()]
            ok = not unread and not hits and len(anchors) == len(r["files"])
            if unread:
                detail = "anchor missing: %s (census surface not read)" % ", ".join(unread)
            elif hits:
                detail = "the absence is refuted: " + ", ".join(hits)
            else:
                detail = "no %s in %s (anchors %s present)" % (
                    "/".join(r["must_not"]), " + ".join(r["files"]),
                    ", ".join("%r" % a for a in anchors))
            row["needle_kind"] = "scan"
            row["anchors"] = anchors
        if not ok:
            problems.append("%s: %s" % (r["code"], detail))
        row.update(pass_=ok, detail=detail)
        table.append(row)
    # the row list must match §1 as parsed from the backlog, so a new code cannot be skipped
    got = [r["code"] for r in table]
    codes = section1_codes()
    missing_codes = [c for c in codes if c not in got]
    extra_codes = [c for c in got if c not in codes]
    if missing_codes:
        problems.append("section 1 codes with no row: " + ", ".join(missing_codes))
    if extra_codes:
        problems.append("rows for codes not in section 1: " + ", ".join(extra_codes))
    if len(codes) != len(set(codes)):
        problems.append("duplicate codes in section 1: "
                        + ", ".join(sorted({c for c in codes if codes.count(c) > 1})))
    if len(got) != len(set(got)):
        problems.append("duplicate rows: " + ", ".join(sorted({c for c in got if got.count(c) > 1})))
    return table, problems


# --------------------------------------------------------------------------------------------
# readers
# --------------------------------------------------------------------------------------------
def run_reader(label, argv):
    cmd = [PY, os.path.join(HERE, argv[0])] + argv[1:]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
    lines = [l.strip() for l in (proc.stdout or "").splitlines() if l.strip()]
    verdicts = [l for l in lines if l.startswith(OK_PREFIXES)]
    # the verdict line is not always the last one (`damage_predict.py` prints 3 lines under a
    # PASS), so take the first line that starts with a verdict word and keep the tail too.
    last = verdicts[0] if verdicts else (lines[-1] if lines else "")
    verdict = next((p for p in OK_PREFIXES if verdicts and verdicts[0].startswith(p)), "")
    ok = proc.returncode == 0 and bool(verdicts)
    return {"label": label, "command": " ".join(["python", "Tools/scripts/" + argv[0]] + argv[1:]),
            "exit": proc.returncode, "verdict": verdict, "summary": last, "ok": ok}


def run_readers(recorded=None):
    out, problems = [], []
    for label, argv in READERS + [CENSUS]:
        if recorded is not None:
            prev = next((r for r in recorded if r["command"] == " ".join(
                ["python", "Tools/scripts/" + argv[0]] + argv[1:])), None)
            if prev is not None:
                out.append(prev)
                if not prev.get("ok"):
                    problems.append("%s: recorded red" % label)
                continue
        r = run_reader(label, argv)
        out.append(r)
        if not r["ok"]:
            problems.append("%s: exit %d, last line %r" % (label, r["exit"], r["summary"]))
    return out, problems


# --------------------------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------------------------
def build(readers, mode="re-run"):
    table, problems = check_rows()
    decs = decisions()
    for r in table:
        if r["decision"]:
            d = decs.get(r["decision"])
            if d is None:
                problems.append("%s: decision %s is not in section 11" % (r["code"], r["decision"]))
                r["decision_state"] = "not in section 11"
            else:
                r["decision_state"] = "resolved" if d["resolved"] else "open"
    carriers = [r for r in table if r["verdict"] == "carrier"]
    absences = [r for r in table if r["verdict"] == "absence"]
    gated = [r for r in table if r["decision"]]
    census = readers[-1]
    doc = {
        "schema": 1,
        "generated_by": "Tools/scripts/g2x_gate.py --write",
        "readers_mode": mode,          # per-run diagnostic, not part of the artefact comparison
        "section": "GRAB_BACKLOG.md section 6, G2 exit gate (G2X)",
        "readers": readers,
        "census": {"command": census["command"], "summary": census["summary"], "ok": census["ok"]},
        "features": [{k: r.get(k) for k in ("code", "kind", "verdict", "files", "needle",
                                           "anchor", "anchors", "must_not", "fact", "decision",
                                           "decision_state", "needle_kind", "pass_", "detail")}
                     for r in table],
        "summary": {
            "codes": len(table),
            "carrier": len(carriers),
            "absence": len(absences),
            "decision_gated": len(gated),
            "decision_ids": sorted({r["decision"] for r in gated}),
            "decision_open": sorted({r["decision"] for r in gated
                                     if r.get("decision_state") != "resolved"}),
            "readers": len(readers),
            "readers_green": len([r for r in readers if r["ok"]]),
            "section1_codes": len(section1_codes()),
            "families": family_text(section1_codes()),
            "needle_kinds": {k: len([r for r in table if r.get("needle_kind") == k])
                             for k in ("number", "identifier", "phrase", "word", "scan")},
            "problems": len(problems),
            "verdict": "PASS" if not problems else "FAIL",
        },
    }
    return doc, problems


def markdown(doc):
    s = doc["summary"]
    a = []
    a.append("# G2X — the G2 exit gate")
    a.append("")
    a.append("Generated by `Tools/scripts/g2x_gate.py --write`; `--check` re-derives every row and")
    a.append("re-runs every reader. The backlog's gate (`GRAB_BACKLOG.md` §6, last paragraph) has")
    a.append("three clauses and this file answers them in order:")
    a.append("")
    a.append("1. every new reader has `--check` green (§1),")
    a.append("2. the P0-2 census is re-run (§1, last row),")
    a.append("3. every feature code in §1 has a JC3 carrier with evidence or a proven absence (§2).")
    a.append("")
    a.append("| item | value |")
    a.append("|---|---|")
    k = s["needle_kinds"]
    a.append("| feature codes | **%d** (parsed from §1: %s) |" % (s["codes"], s["families"]))
    a.append("| carrier with evidence | **%d** |" % s["carrier"])
    a.append("| evidence strength | numbers %d · identifiers %d · phrases %d · short words %d "
             "(a needle is only as strong as what it keys on) |"
             % (k["number"], k["identifier"], k["phrase"], k["word"]))
    a.append("| proven absence | **%d** (no such mechanism in the decoded fleet) |" % s["absence"])
    a.append("| codes whose value waits on a §11 decision | **%d** (%s) |"
             % (s["decision_gated"], ", ".join(s["decision_ids"])))
    a.append("| decisions still open | **%d** (%s) |"
             % (len(s["decision_open"]), ", ".join(s["decision_open"]) or "none"))
    a.append("| readers run | **%d / %d green** |" % (s["readers_green"], s["readers"]))
    a.append("| problems | **%d** |" % s["problems"])
    a.append("| verdict | **%s** |" % s["verdict"])
    a.append("")
    a.append("The decision column never weakens a row: a carrier is a *mechanism*, and §7 rule 6")
    a.append("makes the decision a phase-T block (`blocked: D-n`), not a phase-G2 one. Each row under")
    a.append("a decision names the mechanism that ships whichever option wins; the `state` column is")
    a.append("read from §11 on every run, so a resolved decision here changes no row.")
    a.append("")
    a.append("## 1. Readers re-run")
    a.append("")
    a.append("| reader | command | exit | verdict |")
    a.append("|---|---|---|---|")
    for r in doc["readers"]:
        a.append("| %s | `%s` | %d | %s |" % (r["label"], r["command"], r["exit"],
                                              r.get("verdict") or "-"))
    a.append("")
    a.append("The pass/fail comparison uses that status (command, exit, verdict). The full verdict")
    a.append("sentence of each reader is recorded in `G2X.json` `readers[].summary` at the last")
    a.append("`--write`; it is evidence, not part of the comparison, so a reworded PASS cannot turn")
    a.append("a green gate red.")
    a.append("")
    a.append("The G2-1…G2-9 archive readers (`jc3index.py check`, `jc3fx.py check`,")
    a.append("`jc3hkx.py check --all`, `jc3geom.py check`, `jc3parts.py`) are the §0.7 standing gates;")
    a.append("they are not re-run here because they are not new to phase G2 and every G2 card that")
    a.append("reads their output runs its own `--check` above.")
    a.append("")
    a.append("## 2. Every feature code")
    a.append("")
    a.append("`kind` says how the row is checked: `needle` = the named file must still contain the")
    a.append("string; `vocab-scan` = every named file must contain its own anchor (proof the")
    a.append("complete census was read) and none of the must-not-exist words may appear in **any** of")
    a.append("them, which is the proven-absence form. `strength` is derived from the needle: a")
    a.append("`number` fails when the data drifts, an `identifier` when the member is renamed, a")
    a.append("`phrase`/`word` only when the text changes; a `scan` row is a negative scan, not a")
    a.append("needle.")
    a.append("")
    a.append("| code | verdict | kind | strength | evidence | what satisfies it | decision | state |")
    a.append("|---|---|---|---|---|---|---|---|")
    for r in doc["features"]:
        ev = "`%s`" % r["files"][0]
        if r["kind"] == "needle":
            what = "%s — needle `%s`" % (r["fact"], r["needle"])
        else:
            what = "%s — must not contain %s" % (r["fact"], ", ".join("`%s`" % w for w in r["must_not"]))
        a.append("| %s | %s | %s | %s | %s | %s | %s | %s |"
                 % (r["code"], r["verdict"], r["kind"], r.get("needle_kind") or "-", ev,
                    what.replace("|", "\\|"), r["decision"] or "-", r.get("decision_state") or "-"))
    a.append("")
    a.append("## 3. The absences, stated once")
    a.append("")
    a.append("These are the codes where the fleet's decoded space contains no mechanism. They are")
    a.append("accounted for, not deferred: each names the surface that was searched and the nearest")
    a.append("real member, and each is a named omission in the phase-T row it feeds.")
    a.append("")
    for r in doc["features"]:
        if r["verdict"] == "absence":
            a.append("- **%s** — %s (`%s`)" % (r["code"], r["fact"], r["files"][0]))
    a.append("")
    a.append("## 4. What the gate still cannot prove")
    a.append("")
    a.append("* A proven absence is an absence of **names in the decoded fleet**, not of engine")
    a.append("  capability. Every row that leans on native code says so: turn-on-the-spot (G2-21),")
    a.append("  the eject launch (G2-20), the effect trigger names (G2-22), the graph bytecode (G2-17).")
    a.append("* Three rows carry a value the files do not give: the mass unit (DIM-3, G2-34 says")
    a.append("  UNKNOWN), the explosion-threshold semantics (G2-28 step 7) and whether the module or")
    a.append("  the `.epe` light list renders (G2-33). None is filled in here.")
    waiting = [r for r in doc["features"]
               if r["decision"] and r.get("decision_state") != "resolved"]
    wait_txt = ""
    if waiting:
        wait_txt = ", and %s wait on %s" % (
            ", ".join(r["code"] for r in waiting),
            ", ".join(sorted({r["decision"] for r in waiting})))
    a.append("* The carrier is not the build: HUD-1/HUD-2 need the entity -> `hud.gfx` bridge, which")
    a.append("  is game code (`JC3_HUD_WEAPONS.md`)%s." % wait_txt)
    a.append("")
    return "\n".join(a) + "\n"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--markdown", action="store_true")
    ap.add_argument("--no-readers", action="store_true",
                    help="reuse the recorded reader results (fast, for a tamper test)")
    a = ap.parse_args()

    if a.write:
        readers, problems = run_readers()
        doc, row_problems = build(readers, "re-run")
        problems += row_problems
        doc["summary"]["problems"] = len(problems)
        doc["summary"]["verdict"] = "PASS" if not problems else "FAIL"
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, sort_keys=False)
            fh.write("\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(markdown(doc))
        for p in problems:
            print("FAIL " + p)
        s = doc["summary"]
        print("wrote %s + %s (%d codes: %d carrier, %d absence, %d decision-gated; "
              "readers %d/%d re-run)"
              % (rel(OUT_MD), rel(OUT_JSON), s["codes"], s["carrier"], s["absence"],
                 s["decision_gated"], s["readers_green"], s["readers"]))
        return 1 if problems else 0

    if not os.path.isfile(OUT_JSON) or not os.path.isfile(OUT_MD):
        print("FAIL G2X.json / G2X.md missing - run --write first")
        return 1
    mode = "recorded" if a.no_readers else "re-run"
    recorded = None
    if a.no_readers:
        recorded = json.load(open(OUT_JSON, encoding="utf-8"))["readers"]
    readers, problems = run_readers(recorded)
    doc, row_problems = build(readers, mode)
    problems += row_problems

    if a.markdown:
        print(markdown(doc), end="")
        return 0

    on_disk = json.load(open(OUT_JSON, encoding="utf-8"))
    json_ok = on_disk.get("features") == doc["features"]
    if not json_ok:
        stale = [f["code"] for f, o in zip(doc["features"], on_disk.get("features", []))
                 if f != o]
        problems.append("G2X.json stale: rows differ for %s" % (", ".join(stale) or "unknown"))
    notes = []
    if on_disk.get("summary") != doc["summary"]:
        json_ok = False
        problems.append("G2X.json stale: summary block differs")

    def reader_status(rs):
        return [{k: r.get(k) for k in ("label", "command", "exit", "verdict", "ok")} for r in rs]

    if reader_status(on_disk.get("readers", [])) != reader_status(doc["readers"]):
        json_ok = False
        problems.append("G2X.json stale: readers block differs (status)")
    else:
        drift = [x["label"] for x, y in zip(doc["readers"], on_disk.get("readers", []))
                 if x.get("summary") != y.get("summary")]
        if drift:
            notes.append("%d reader summary line(s) changed since --write (%s); the recorded text in "
                         "G2X.json is from the last write - run --write to refresh it"
                         % (len(drift), ", ".join(drift)))
    if {k: (on_disk.get("census") or {}).get(k) for k in ("command", "ok")} != \
            {k: doc["census"].get(k) for k in ("command", "ok")}:
        json_ok = False
        problems.append("G2X.json stale: census block differs (status)")
    md_on_disk = read_text(OUT_MD)
    md_now = markdown(doc)
    md_ok = md_on_disk == md_now
    if not md_ok:
        import difflib
        diff = list(difflib.unified_diff(md_on_disk.splitlines(), md_now.splitlines(),
                                         "G2X.md on disk", "re-derived", n=0))[:12]
        problems.append("G2X.md stale: " + " / ".join(diff[:8]))
    for p in problems:
        print("FAIL " + p)
    for n in notes:
        print("NOTE " + n)
    s = doc["summary"]
    print("%s: %d codes (%d carrier, %d absence, %d decision-gated) in %d files | readers %d/%d "
          "green (%s) | census %s | json match %s, md match %s"
          % ("PASS" if not problems else "FAIL", s["codes"], s["carrier"], s["absence"],
             s["decision_gated"], len({f for r in doc["features"] for f in r["files"]}),
             s["readers_green"], s["readers"], mode, "ok" if doc["census"]["ok"] else "RED",
             json_ok, md_ok))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
