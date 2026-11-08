#!/usr/bin/env python
"""t7_weapons.py - T-11: weapons translation (doc `T-7`) and the weapon edit list.

Reads the grab evidence and regenerates

    Working/Translation/T7_WEAPONS.md          one row per WPN code + the two decision rows
    Working/Translation/t7_weapons_edits.json  the numeric edits, the structural list, the withdrawals

Inputs (all existing repo research files; no game data is opened or written):

    Research/BatmobileGrab/WEAPONS.json        G1-08/G1-09  every field of every weapon/projectile
    Research/BatmobileGrab/HUD_INTERFACES.json G1-08        BmAK HUD setters (primary/secondary/special)
    Research/BatmobileGrab/SOCKETS_JC3.json    G1-13        muzzle/missile sockets in JC3 metres
    Research/JC3Grab/WEAPONS.jsonl             G2-10        25 weapon ids, every decoded member
    Research/JC3Grab/WEAPON_WIRING.jsonl       G2-11        slot pointers, bindings, fire points
    Research/JC3Grab/JC3_HUD_WEAPONS.json      G2-25        slots, reticle, cooldown, heat, lock-on
    Research/JC3Grab/DAMAGE_MODEL.json         G2-28        hits-to-kill on both sides
    Research/JC3Grab/EMP.json                  G2-16        the EMP carrier
    Research/JC3Grab/G2X.json                  G2X          the proven absences WPN-6…WPN-10

For every WPN code the card lists twelve aspects - carrier, slot, weapon point, fire rate, damage by
effect, projectile speed, spread curve, heat/overheat, lock-on, explosion radius/impulse, effects,
sounds.  Each aspect is emitted with its R4 class (`decoded`, `decoded (fleet)`, `derived`, `class`,
`read`) or `UNKNOWN` plus the surface that was searched, so nothing is filled in from memory.

Usage
    python Tools/scripts/t7_weapons.py --write
    python Tools/scripts/t7_weapons.py --check
    python Tools/scripts/t7_weapons.py show rows|edits|bmak|jc3
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab")
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
TRANS = os.path.join(ROOT, "Working", "Translation")
OUT_MD = os.path.join(TRANS, "T7_WEAPONS.md")
OUT_JSON = os.path.join(TRANS, "t7_weapons_edits.json")
BASE_PKG = "Playable_Batmobile_SF"
DONOR_EE = "v0300_car_kensington_sportsmuscle_signature_preorder.ee"
TANK_EE = "v0201_car_capstone_mediumtank_military_01.ee"

CLASSES = ("decoded", "decoded (fleet)", "derived", "class", "read", "UNKNOWN")


# --------------------------------------------------------------------------------------------- #
# readers
# --------------------------------------------------------------------------------------------- #
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Bmak:
    """The four BmAK packages, read through G1-08's `WEAPONS.json`."""

    def __init__(self):
        self.doc = load_json(os.path.join(BMAK, "WEAPONS.json"))
        self.objects = {}
        for o in self.doc["objects"]:
            self.objects.setdefault(o["name"], []).append(o)
        self.projectiles = {p["name"]: p for p in self.doc["projectiles"]}
        self.hud = load_json(os.path.join(BMAK, "HUD_INTERFACES.json"))
        self.sockets = load_json(os.path.join(BMAK, "SOCKETS_JC3.json"))

    def obj(self, name, pkg=BASE_PKG):
        for o in self.objects.get(name, []):
            if o["package"] == pkg:
                return o
        return None

    def field(self, name, path):
        """(status, value) for one object field: serialized / absent / missing-object."""
        o = self.obj(name)
        if o is None:
            return "missing-object", None
        for f in o["fields"]:
            if f["path"] == path:
                if f.get("ref"):
                    return "serialized", "ref:" + str(f["ref"].get("path"))
                return "serialized", f.get("value")
        return "absent", None

    def v(self, name, path):
        return self.field(name, path)[1]

    def searched(self, projectile, quantity):
        """The 'searched' list G1-09 records for a quantity that has no field."""
        p = self.projectiles.get(projectile) or {}
        entry = (p.get("values") or {}).get(quantity) or {}
        return entry.get("searched") or [], entry.get("field")

    def socket(self, name):
        for s in self.sockets["sockets"]:
            if s["socket"] == name:
                return s
        return None


class Jc3:
    """The 25 vehicle weapon ids, read through G2-10's `WEAPONS.jsonl`."""

    def __init__(self):
        rows = load_jsonl(os.path.join(JC3, "WEAPONS.jsonl"))
        self.rows = {r["id"]: r for r in rows}
        self.flat = {wid: self._flat(r) for wid, r in self.rows.items()}
        self.wiring = load_jsonl(os.path.join(JC3, "WEAPON_WIRING.jsonl"))
        self.hud = load_json(os.path.join(JC3, "JC3_HUD_WEAPONS.json"))
        self.damage = load_json(os.path.join(JC3, "DAMAGE_MODEL.json"))
        self.emp = load_json(os.path.join(JC3, "EMP.json"))
        self.g2x_doc = load_json(os.path.join(JC3, "G2X.json"))

    @staticmethod
    def _flat(row):
        out = {}
        for tune in row["tunes"]:
            for inst in tune["instances"]:
                for r in inst["rows"]:
                    if len(r) == 3 and r[2] != "" and not str(r[1]).startswith("A["):
                        out[r[0]] = r[2]
        return out

    def get(self, wid, member, default=None):
        return self.flat.get(wid, {}).get(member, default)

    def summary(self, wid):
        return self.rows[wid].get("summary") or {}

    def presets(self, wid):
        return self.rows[wid].get("presets") or []

    def autoaim_members(self, wid):
        """Every member name of the id's AutoAim (`autoaim*`) sources, contexts kept."""
        names = set()
        for src in self.rows[wid]["sources"]:
            if "AutoAim" not in (src.get("classes") or []):
                continue
            for inst in (src.get("decode") or {}).get("instances", []):
                for r in inst.get("rows") or []:
                    if len(r) == 3:
                        names.add(r[0])
        return sorted(names)

    def autoaim_lock_members(self, wid):
        return [m for m in self.autoaim_members(wid) if "lock" in m.lower()]

    def entity(self, needle):
        for w in self.wiring:
            if needle in w["entity"]:
                return w
        raise SystemExit(f"no wiring row for {needle}")

    def g2x(self, code):
        for f in self.g2x_doc["features"]:
            if f["code"] == code:
                return f
        raise SystemExit(f"no G2X feature {code}")


# --------------------------------------------------------------------------------------------- #
# formatting helpers
# --------------------------------------------------------------------------------------------- #
def num(v, digits=3):
    if v is None:
        return "UNKNOWN"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    return str(v)


def cell(text):
    """One markdown table cell: no pipes, no newlines (the ledger splits cells on `|`)."""
    return str(text).replace("|", "/").replace("\n", " ").strip()


def rot_units_to_deg(units):
    """UE3 rotator 65536 units = 360 degrees."""
    return round(units * 360.0 / 65536.0, 4)


def aspect(name, bmak, jc3, transform, cls, note=""):
    if cls not in CLASSES:
        raise SystemExit(f"bad class {cls!r} on aspect {name!r}")
    return {"aspect": name, "bmak": bmak, "jc3": jc3, "transform": transform, "class": cls,
            "note": note}


# --------------------------------------------------------------------------------------------- #
# rows
# --------------------------------------------------------------------------------------------- #
def row_wpn1(B, J):
    o = "Batmobile_Heavy_Cannon_Primary"
    p = "Batmobile_Heavy_Cannon_Primary_Projectile"
    rate = B.v(o, "RVehicleWeapon.FiringInterval")
    charge = B.v(o, "RBatmobileHeavyCannon.ChargeUpTime")
    lock_angle = B.v(o, "RBatmobileHeavyCannon.LockOnAngle")
    lethal = B.v(o, "RVehicleWeapon.LethalRadius")
    recoil = B.v(o, "RBatmobileHeavyCannon.RecoilImpulse")
    dmg = B.v(p, "Projectile.Damage")
    speed = B.v(p, "Projectile.Speed")
    maxspeed = B.v(p, "Projectile.MaxSpeed")
    momentum = B.v(p, "Projectile.MomentumTransfer")
    turret_dmg = B.v(p, "RBasicProjectile.TurretShotDamage")
    radius = B.v(p, "Projectile.DamageRadius")
    wid = "w602_mediumtank_canon"
    j_rate = float(J.get(wid, "fire_rate"))
    j_vel = float(J.get(wid, "velocity"))
    j_dmg = float(J.get(wid, "bullet_weapon[0].tuning.base_tuning.damage"))
    j_blast = J.get(wid, "PlayerDamage")
    j_radius = J.get(wid, "PlayerDamageRadius")
    j_imp = float(J.get(wid, "bullet_weapon[0].tuning.base_tuning.impulse"))
    hits_bmak = J.damage["arm_targets"]["bmak_ratio"]["heavy_cannon_hits"]
    health = J.damage["arm_targets"]["bmak_ratio"]["health"]
    shell = J.damage["arm_targets"]["tank_shell_damage"]
    feet = J.damage["table"]["medium_tank"]["tank_cannon"]["primary"]
    tank_max = J.damage["vehicles"]["medium_tank"]["max_health"]
    shots = B.socket("CannonMuzzle")
    a = [
        aspect("carrier", f"`RBatmobileHeavyCannon` `{o}` (4 packages, 165 fields) + projectile `{p}`",
               f"`{wid}` - the medium tank's cannon, 7 carriers, 175 decoded tune rows, blast "
               f"{num(j_blast)} in {num(j_radius)} m", "clone the tune under a private path (R7: "
               "never edit a shipped weapon file in place)", "decoded",
               "G2X WPN-1 needle `w602_mediumtank_canon`"),
        aspect("slot", "one gadget of the HUD's primary/secondary pair (`UC_SetPrimaryWeapon`)",
               "`main_weapon` (id:851CAABE) - the slot the medium tank binds w602 to",
               "point the root's `main_weapon` at the clone", "decoded",
               "the donor binds its w618 missile to the same slot, so the slot count is T-WP13's"),
        aspect("weapon point", f"`CannonMuzzle` on bone `{shots['bone']}`, part `batmobile_cannon` "
               f"(T-12 P-02)", f"socket {[round(x, 4) for x in shots['position_m']]} m, forward "
               f"{[round(x, 3) for x in shots['forward_jc3']]}", "place an `SWeaponPoint` at the "
               "socket in B-05", "decoded", "G1-13 socket, one of the 65 placed"),
        aspect("fire rate", f"`FiringInterval` {num(rate)} s", f"`fire_rate` {num(j_rate)} s",
               f"1:1 (both seconds): {num(j_rate)} -> {num(rate)} s between shots", "decoded",
               "an edit, see the edits file"),
        aspect("damage by effect",
               f"`Health` {num(health)} / `Damage` {num(dmg)} = **{hits_bmak} shell hits** to "
               f"destroy the Batmobile",
               f"medium tank `max_health` {num(tank_max)}; a shell ({num(shell)} in 8 m) kills a "
               f"stock tank in {feet['H0']} hits (H0/H2) / {feet['H1']} (H1)",
               "the ratio 24:2 = 12x is carried by the **health** row (T-14 needs `max_health` "
               "36000), never by the weapon's damage: the cloned cannon keeps 1500", "derived",
               "translation rule 2 - translate by effect, not by the raw number"),
        aspect("projectile speed", f"`Projectile.Speed` {num(speed)} UU/s = "
               f"{num(speed / 100.0, 1)} m/s, `MaxSpeed` {num(maxspeed)} = "
               f"{num(maxspeed / 100.0, 1)} m/s",
               f"`velocity` {num(j_vel)} (the member's unit is not stated in any decoded file)",
               f"{num(j_vel)} -> {num(speed / 100.0, 1)}", "derived",
               "UE3 UU = 1 cm is the one transform's unit; the JC3 member's unit is inferred "
               "from the 360..900 band of the 25 ids and is confirmed by the Q-3 flight-time take"),
        aspect("spread curve", "no inaccuracy member on the heavy cannon (`InaccuracyVsTime` "
               "is the Vulcan's, `Points` 274 B struct-serialized and **not decoded**)",
               "`scatter_minimum`/`_maximum` 0.6/0.6, `_per_shot` 0, `_recover_rate` 0.4, "
               "`_reset_time` 1.15", "no fit: the BmAK points are UNKNOWN, so the shipped JC3 "
               "scatter is kept", "UNKNOWN",
               "G1-23 records the Vulcan curve only; the cannon has no inaccuracy series in "
               "`WEAPONS.json`"),
        aspect("heat / overheat", "no heat member on the heavy cannon (one shot per press)",
               f"`heat` block of JC3_HUD_WEAPONS.json is empty: 0 params with heat", "none",
               "decoded (fleet)", "G2-10 and G2-25 both report no overheat member anywhere"),
        aspect("charge", f"`ChargeUpTime` {num(charge)} s, `ChargeMaxDamageRadius` "
               f"{num(B.v(o, 'RBatmobileHeavyCannon.ChargeMaxDamageRadius'))}",
               "no charge member in the 175 decoded rows", "no carrier: named omission",
               "UNKNOWN", "a charged shot is BmAK behaviour with no JC3 member"),
        aspect("lock-on", f"`LockOnAngle` {num(lock_angle)} deg, `LockOnTimeMin` "
               f"{num(B.v(o, 'RBatmobileHeavyCannon.LockOnTimeMin'))} s, `LockOnTimeMax` "
               f"{num(B.v(o, 'RBatmobileHeavyCannon.LockOnTimeMax'))} s",
               "the AutoAim block carries sticky-aim angles only: "
               f"{len(J.autoaim_lock_members(wid))} lock members", "no numeric carrier",
               "UNKNOWN", "JC3's lock-on is the HUD POI (T-WP3)"),
        aspect("blast / explosion", f"`DamageRadius` {num(radius)} (no blast), impact particle "
               f"`{B.v(p, 'RBasicProjectile.ImpactExplosion')}`, muzzle "
               f"`{B.v(o, 'RBatmobileHeavyCannon.FireFX')}`",
               f"blast {num(j_blast)} in {num(j_radius)} m (its own `ForcePulseSettings` bundle)",
               "keep the JC3 blast: BmAK has no radial damage, only a direct hit", "decoded",
               "the blast is what makes 2 hits lethal - see the damage aspect"),
        aspect("impulse", f"`MomentumTransfer` {num(momentum)} + `RecoilImpulse` "
               f"{num(recoil)}", f"`impulse` {num(j_imp)} on the direct hit, no blast impulse "
               "member", "no bridge: the shove is dropped", "UNKNOWN",
               "WLD-5's shove has no member on the JC3 cannon"),
        aspect("effects", "`Batmobile_canonMuzzleflash`, `Batmobile_HeavyCannon_Impact`",
               "`tank_canon_muzzleflash.effc` (11 vehicles) at CannonMuzzle, the 7-variant "
               "`tank_explosive_*` family on the hit", "the T-17 rows T-FX10 / T-FX15 own them",
               "decoded", "T-17 already chose them"),
        aspect("sounds", "`Play_BML_HeavyCannon_Fire`, `_Reload`, `LockOnBeepSound`, "
               "`LockedOnSound`", "`weapons.bank` + the tank's own `Fire`/`ReloadStart` "
               "attached effects", "T-16 owns the mapping", "decoded",
               "G2-24: the tune carries no audio, the sound is on the vehicle"),
    ]
    return dict(id="T-WP1", code="WPN-1", title="Heavy Cannon (`RBatmobileHeavyCannon`)",
                jc3=[wid], socket="CannonMuzzle", part="batmobile_cannon", dispo="next",
                now="the donor graph's only weapon pointer is w618 on main_weapon; the car has no "
                    "cannon geometry, so nothing can fire (T-FX10's 'absent until the T-11 clone')",
                proposed="clone w602 under a private path, bind it to `main_weapon`, set fire_rate "
                         "2 and velocity 400, and place `SWeaponPoint` at CannonMuzzle (B-05/B-06)",
                aspects=a,
                verify="Q-3 #3: a shell fired at a wall leaves from CannonMuzzle (not the car "
                       "origin) and kills a stock tank in the predicted 2 hits, 3/3",
                why=f"heavy cannon = `{wid}` on main_weapon, fire_rate 1.75->2 and velocity "
                    f"500->400 from the BmAK values; damage stays ship-set because the 24:2 "
                    f"ratio is T-14's health row (T7_WEAPONS.md section 4)")


def row_wpn2(B, J):
    o = "Batmobile_Cannon_V2"
    wid = "w603_mediumtank_mgun"
    alt = "w619_buggy_mgun"
    rate = B.v(o, "RVehicleWeapon.FiringInterval")
    dmg = B.v(o, "RBatmobileCannon.ChainGunDamage")
    up = B.v(o, "RBatmobileCannon.UpgradedDamage")
    inacc = B.v(o, "RBatmobileCannon.InaccuracyAngle")
    spin = B.v(o, "RBatmobileCannon.ChainGunMaxSpinSpeed")
    heat = B.v(o, "RBatmobileCannon.HeatUpPerSecond")
    off = B.v(o, "RBatmobileCannon.OverheatOffValue")
    mom = B.v(o, "RBatmobileCannon.ImpactMomentum")
    j_rate = float(J.get(wid, "fire_rate"))
    j_vel = J.get(wid, "velocity")
    j_dmg = J.get(wid, "bullet_weapon[0].tuning.base_tuning.damage")
    j_veh = J.get(wid, "bullet_weapon[0].tuning.base_tuning.vehicle_damage_factor")
    j_sc = [J.get(wid, f"bullet_weapon[0].tuning.base_tuning.scatter.scatter_{k}") for k in
            ("minimum", "maximum", "per_shot", "recover_rate", "reset_time")]
    a = [
        aspect("carrier", f"`RBatmobileCannon` `{o}` (5 instances, 280 fields)",
               f"`{wid}` (the tank's coax MG, 7 carriers) and `{alt}` (the only driver-fired car "
               f"MG with a `GatlingGun` part, 1 carrier)",
               "clone w603 for the gun; the barrel spin is a part behaviour (T-12 P-03), not a "
               "weapon member", "decoded", "G2X WPN-2 needle `w603_mediumtank_mgun`"),
        aspect("slot", "one gadget of the primary/secondary pair",
               "`secondary (id:00568A74)` - the slot the medium tank binds w603 to",
               "point the root's second driver slot at the clone", "decoded",
               "G2-11 section 2d: tank = w602 main_weapon + w603 secondary"),
        aspect("weapon point", "`ChainGunMuzzle`, shells from `ChainGunShells`",
               f"socket {[round(x, 4) for x in B.socket('ChainGunMuzzle')['position_m']]} m on "
               "`Batmobile_Rig_Weapons_Machine_Gun_01`",
               "`SWeaponPoint` at the socket, parented to `batmobile_machine_gun`", "decoded",
               "G1-13"),
        aspect("fire rate", f"`FiringInterval` {num(rate)} s (the combo interval is the same "
               f"value)", f"`fire_rate` {num(j_rate)} s", f"{num(j_rate)} -> {num(rate)}",
               "decoded", "~7.25 rounds/s, an edit"),
        aspect("damage by effect", f"`ChainGunDamage` {num(dmg)} (upgraded {num(up)}) - a "
               "per-round number with no target health behind it",
               f"`damage` {num(j_dmg)} direct, vehicle factor {num(j_veh)}", "keep the clone's "
               "damage: BmAK gives no soldier/vehicle health to ratio against", "UNKNOWN",
               "no BmAK health for anything the Vulcan shoots: a raw ratio would be invented"),
        aspect("projectile speed", "hitscan (no projectile archetype on the Vulcan)",
               f"`velocity` {num(j_vel)}", "keep", "decoded (fleet)",
               "w603's own tracer velocity 750 is the shipped value"),
        aspect("spread curve", f"`InaccuracyAngle` {num(inacc)} rad-ish plus "
               "`InaccuracyVsTime` 0/0.5/1.5/2.5 s -> 0/0/1.5/3.0 (G1-23)",
               f"`scatter` {num(j_sc[0])}/{num(j_sc[1])} per-shot {num(j_sc[2])} recover "
               f"{num(j_sc[3])} reset {num(j_sc[4])}", "shape maps, numbers do not: w603's "
               "scatter is constant, so the growing curve needs w620's per-shot member; the "
               "BmAK point units are unknown", "derived",
               "the *shape* (0 for the first second, then a ramp) is the behaviour to keep"),
        aspect("heat / overheat", f"`HeatUpPerSecond` {num(heat)} = **no overheat** "
               f"(`OverheatOffValue` {num(off)}); `HeatBarStart` [0.79, 0.68] and `HeatBarSize` "
               "[0.125, 0.03] are HUD bar geometry", "0 heat params in the HUD API, no overheat "
               "member in any tune", "both sides absent: the bar geometry is WPN-12's", "decoded",
               "G1-23's revised reading: HeatUpPerSecond 0.0 means the bloom is the only growth"),
        aspect("lock-on", "none (a gun)", "`autoaim_vehicle_mgun` sticky-aim preset",
               "sticky aim only, no lock", "decoded", "G2-10 section 9"),
        aspect("blast / explosion", "none - no projectile", "none (a bullet weapon)",
               "none", "decoded", ""),
        aspect("impulse", f"`ImpactMomentum` {num(mom)}, `RecoilImpulse` "
               f"{num(B.v(o, 'RBatmobileCannon.RecoilImpulse'))}",
               f"`impulse` 60 per hit", "no bridge (units)", "UNKNOWN",
               "the number is BmAK's momentum, not a JC3 impulse"),
        aspect("effects", "`Batmobile_Muzzleflash_Tracer`, `ChainGun_BulletCasing`, "
               "`Batmobile_RiotSuppressor_Tracer`", "`helicopter_minigun_muzzleflash.effc` (15 "
               "vehicles) at ChainGunMuzzle; no casing effect exists in the fleet",
               "T-17 rows T-FX11 (flash) and T-FX13 (casings = out)", "decoded", ""),
        aspect("sounds", "`Play_Minigun_Fire`, `_Overheat`, `_Cooled`, combo in/out",
               "`weapons.bank` machine-gun events", "T-16", "decoded", ""),
        aspect("barrel spin", f"`ChainGunMaxSpinSpeed` {num(spin)}, accel "
               f"{num(B.v(o, 'RBatmobileCannon.ChainGunSpinAccel'))}, decel "
               f"{num(B.v(o, 'RBatmobileCannon.ChainGunSpinDecel'))}",
               "`GatlingGun` part behaviour driven by `weapon_rpm` (racing boat, helicopters)",
               "the part row T-12 P-03 owns the geometry; no weapon member", "decoded",
               "there is no JC3 spin-speed member: the rate is code"),
    ]
    return dict(id="T-WP2", code="WPN-2", title="Vulcan chain gun (`RBatmobileCannon`)",
                jc3=[wid, alt], socket="ChainGunMuzzle", part="batmobile_machine_gun",
                dispo="next",
                now="no Vulcan in the build and the donor's second driver slot "
                    "(`id:00568A74`) is empty",
                proposed="clone w603, bind it to the second driver slot, set fire_rate 0.138, and "
                         "spin the T-12 P-03 barrels from `weapon_rpm`",
                aspects=a,
                verify="Q-3 #3: the Vulcan fires from ChainGunMuzzle, the barrels spin while "
                       "firing and the burst lands the predicted rounds on an APC, 3/3",
                why=f"Vulcan = `{wid}` on the second driver slot with fire_rate 0.1->0.138; the "
                    f"barrel spin is the T-12 part; heat is a proven absence on both sides")


def row_wpn3(B, J):
    o = "Batmobile_Missile_Launcher"
    wid = "w618_sportsmuscle_missile"
    angle = B.v(o, "RBatmobileMissileLauncher.LockOnAngle")
    rng = B.v(o, "RBatmobileMissileLauncher.LockOnRange")
    cool = B.v(o, "RVehicleWeapon.WeaponCoolDown")
    p = "Batmobile_Missile_Projectile"
    dmg = B.v(p, "Projectile.Damage")
    mom = B.v(p, "Projectile.MomentumTransfer")
    maxspeed, _ = B.field(p, "Projectile.MaxSpeed")
    j_dmg = J.get(wid, "missile_weapon[0].tuning.base_tuning.damage")
    j_vel = J.get(wid, "velocity")
    j_imp = J.get(wid, "missile_weapon[0].tuning.base_tuning.impulse")
    j_blast = J.get(wid, "PlayerDamage")
    j_radius = J.get(wid, "PlayerDamageRadius")
    j_turn = J.get(wid, "missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed")
    donor = J.entity(DONOR_EE)
    points = len(donor["weapons"][0]["points"])
    a = [
        aspect("carrier", f"`RBatmobileMissileLauncher` `{o}` (3 instances, 48 fields) + "
               f"`RBatmobileMissile` `{p}`", f"`{wid}` - **the donor chassis's own missile**, 1 "
               f"carrier, 4 fire points, blast {num(j_blast)} in {num(j_radius)} m", "clone "
               "under a private path", "decoded", "G2X WPN-3 needle `w618_sportsmuscle_missile`"),
        aspect("slot", "lock-on barrage, one gadget slot",
               "`main_weapon` **today** in the donor (1 driver slot, 1 weapon) - the cannon "
               "wants the same slot", "the slot count is T-WP13's: with 2 slots the missiles "
               "must move to the second", "decoded",
               "G2-11: the donor binds w618 to main_weapon and nothing else"),
        aspect("weapon point", f"`MissileL`/`MissileR` and the 4 `MissileLaunchSockets`",
               f"{points} type-2 fire points on the donor, each paired by position with a "
               "muzzle", "parent them to `batmobile_missile_pod_l/r` (T-12 P-14/P-15)", "decoded",
               "G2-12: 4 points, one muzzleflash .effc"),
        aspect("fire rate", f"no `FiringInterval`; `WeaponCoolDown` {num(cool)} s is the "
               "barrage cooldown", f"`fire_rate` {num(j_vel and J.get(wid, 'fire_rate'))} s, "
               f"`missile_per_shot` 1", "no mapping: a 20 s barrage cooldown and a 0.5 s shot "
               "interval are different beats", "UNKNOWN",
               "BmAK has no per-missile interval in `WEAPONS.json`"),
        aspect("damage by effect", f"`Damage` {num(dmg)} x 1200 health = 5 missile hits",
               f"`damage` {num(j_dmg)} per missile", "the health ratio is T-14's", "derived",
               "same rule as the cannon: no raw number crosses"),
        aspect("projectile speed", f"no `Projectile.Speed` (`{maxspeed}`), no `AccelRate` on "
               f"this archetype (searched: {B.searched(p, 'speed')[0]})", f"`velocity` "
               f"{num(j_vel)}", "keep the JC3 speed: BmAK gives no missile speed", "UNKNOWN",
               "G1-09 records the field as absent, not as zero"),
        aspect("spread curve", "none (guided)", f"`scatter` 0/0, `turning_speed` {num(j_turn)}",
               "keep unguided: the donor's missile is `autoaim_vehicle_no_lockon_missile`",
               "decoded (fleet)", "G2-12 and G2-10 both record turning 0"),
        aspect("heat / overheat", "none", "none", "none", "decoded (fleet)", ""),
        aspect("lock-on", f"`LockOnAngle` {num(angle)} deg, `LockOnRange` {num(rng)} UU = "
               f"**{num(rng / 100.0, 1)} m**, salvo count = curve param "
               f"`{B.v(o, 'RBatmobileMissileLauncher.MissileNumberParameter')}` (value not in any "
               "file)", "HUD POI `POI_TYPE_LOCK_ON_TARGET` 21, 1.5 s rotation, 0.5 s "
               "`MCI_missile_locked`; the weapon's AutoAim preset is "
               f"`{J.presets(wid)[0]}` = **no lock-on**", "the lock marker exists, the lock "
               "time/range do not: named gap", "UNKNOWN",
               "G2-25: the AutoAim -> POI link is unwritten; 0 lock members in the AutoAim block"),
        aspect("blast / explosion", f"impact `{B.v(p, 'RBatmobileMissile.ExplosionTemplate')}`, "
               f"momentum {num(mom)}", f"blast {num(j_blast)} in {num(j_radius)} m, impulse "
               f"{num(j_imp)}", "keep the JC3 blast + impulse", "decoded", ""),
        aspect("effects", "`Batmobile_Rocket_Muzzle`, `RocketTrail`, "
               "`Batmobil_Rocket_Explosion`", "`missile_trail_car` (2 vehicles, on the donor) at "
               "MissileL/R", "T-17 T-FX14", "decoded", ""),
        aspect("sounds", "`Play_Batmobile_ApRocket_Fire`, `Lock_Beep`, `Locked`",
               "`weapons.bank` missile events", "T-16", "decoded", ""),
    ]
    return dict(id="T-WP3", code="WPN-3", title="Missile launcher (`RBatmobileMissileLauncher`)",
                jc3=[wid], socket="MissileL + MissileR", part="batmobile_missile_pod_l/r",
                dispo="next",
                now="the donor binding survives in the build, but there is no `SWeaponPoint` at "
                    "our pods and no missile geometry on the car (T-12 P-14/P-15 are shells)",
                proposed="clone w618, move it to the free driver slot (T-WP13), and place the 4 "
                         "fire points on the pod parts",
                aspects=a,
                verify="Q-3 #3: 4 missiles leave the two pods and hit what the reticle covers; "
                       "a stock car takes the predicted 2, 3/3 salvos",
                why=f"missiles = the donor's own `{wid}` (4 fire points, blast 1100 in 8 m); "
                    f"lock-on has a marker but no time/range member, so it is UNKNOWN")


def row_wpn4(B, J):
    o = "Batmobile_EMP_Missile_Launcher"
    p = "Batmobile_EMPMissile_Projectile_ForCars"
    dur = B.v(o, "RBatmobileEMPMissile.MissileLockOnDuration")
    civ = B.v(o, "RBatmobileEMPMissile.CivilianMissileLockOnDuration")
    sock = B.v(o, "RPursuitModeMissileLauncher.LaunchSocketName")
    rot = B.v(o, "RPursuitModeMissileLauncher.LaunchRotationOffset")
    emp = J.emp
    a = [
        aspect("carrier", f"`RBatmobileEMPMissile` `{o}` (3 instances, 63 fields) + `{p}`",
               "`CEMPWeapon` `w702`/`w503` exist but neither tune has an EMP field; the EMP "
               "effect itself is an **entity-level `CForcePulse`** copy (G2-16)",
               "two objects, not one: the missile clone (w618) + a `CForcePulse` copy", "decoded",
               "G2X WPN-4 needle `w702`"),
        aspect("slot", "pursuit-mode missile gadget",
               "no weapon slot for the pulse; the missile takes a driver slot", "T-WP13 owns the "
               "count", "decoded", ""),
        aspect("weapon point", f"`LaunchSocketName` = **`{sock}`**, `LaunchRotationOffset` "
               f"{rot} = {num(rot_units_to_deg(rot[0]), 2)} deg",
               f"socket `{sock}` is not a muzzle: it is the battle spotlight bone (and the 0.247 / 0.485 / -2.018 "
               f"muzzle is `w603_mediumtank_mgun`'s `fire_position_0`; the cannon's own is 0 / 0.3739 / "
               f"-5.8174, `Research/JC3Grab/WEAPON_WIRING.md` line 316)",
               "a new `SWeaponPoint` at the socket with the -20 deg pitch", "decoded",
               "G1-13 places BattleModeSpotLight at [0.0004, 1.8346, -0.0664] m"),
        aspect("fire rate", "`bInstantFire` true, one press = one missile", "`fire_rate` 0.5 s "
               "(the w618 clone)", "keep", "decoded", ""),
        aspect("damage by effect", "`Projectile.Damage` absent on the ForCars archetype "
               f"(searched: {B.searched(p, 'damage')[0]}): the missile **disables**, it does not "
               "damage", "the pulse tune does 100 player damage in 25 m (`truck_emp.ftune`)",
               "no damage to translate", "UNKNOWN",
               "the disable is the behaviour and it has no member"),
        aspect("projectile speed", f"no speed/accel on `{p}`", "`velocity` 360 (the clone)",
               "keep", "UNKNOWN", "G1-09 records both fields absent"),
        aspect("spread curve", "guided, none", "`scatter` 0/0", "none", "decoded", ""),
        aspect("heat / overheat", "none", "none", "none", "decoded (fleet)", ""),
        aspect("lock-on", f"`MissileLockOnDuration` {num(dur)} s (civilian {num(civ)} s), "
               f"`LoseLockXBonus` {num(B.v(o, 'RBatmobileEMPMissile.LoseLockXBonus'))} / Y "
               f"{num(B.v(o, 'RBatmobileEMPMissile.LoseLockYBonus'))}",
               "the same POI marker as WPN-3; no duration member", "no numeric carrier",
               "UNKNOWN", "as WPN-3"),
        aspect("blast / explosion", f"`ExplosionTemplate` `{B.v(p, 'RBatmobileMissile.ExplosionTemplate')}`",
               "`CForcePulse` `EMP` on `truck_emp.ftune`: 100 player damage held at full radius "
               "in 25 m, **no duration, target class or disable member**",
               "copy the pulse; the disable is a named omission", "decoded",
               "G2-16's answer: the effect is an entity-level copy, not a weapon-slot copy"),
        aspect("effects", "`ChargeParticle` on the burst, `RocketTrail` on the missile",
               "`explosion_emp_flatbed.effc` / `epe_emp_powering_up`", "T-17", "decoded", ""),
        aspect("sounds", "`Play_Batmobile_ApRocket_Fire`, `Immobiliser_Impact`", "the EMP "
               "truck's events", "T-16", "decoded", ""),
    ]
    return dict(id="T-WP4", code="WPN-4",
                title="EMP missile launcher (`RBatmobileEMPMissile`, launcher half)",
                jc3=["w618_sportsmuscle_missile", "CForcePulse"],
                socket="BattleModeSpotLight",
                part="batmobile_missile_pod_l/r", dispo="next",
                now="neither the missile nor a pulse object is in the build",
                proposed="**launcher only (operator ruling 4, 2026-11-06: the row is split so the "
                         "launcher ships)**: clone w618 and copy the entity `CForcePulse`, then "
                         "transplant the Fire Leech's guidance - `w143_rpg_fire_leach.wtune` "
                         "`missile_turning_speed` 300, `_random` 60, `missile_acceleration` "
                         "30->65 over `_time` 0.2->10, `_acceleration_random` 2->5 (5 values; w618's "
                         "own `missile_turning_speed` is 0, so the shipped missile cannot home) - "
                         "and give it a NEW lock-on `AutoAim` tune with the fleet lock-on preset's "
                         "classes (`CanTargetVehicles` 1, `CanTargetRigidObjects` 1, "
                         "`CanTargetCharacters` **0** - w143's own 1 would lock pedestrians, which "
                         "BmAK does not), w143's 0.12/0.15 cone, `MaxAimDistance` 120 m; every "
                         "fire-block value stays w618's (damage 1500, velocity 360, range 300, "
                         "fire rate 0.5). Entity members: one more `CCar` root with "
                         "`main_weapon` = the w618 EMP clone and `id:00568A74` free or used by the "
                         "Vulcan (T-WP13), a `SWeaponPoint` at `BattleModeSpotLight` with the "
                         "-20 deg pitch, and the `CForcePulse` object copied from `truck_emp` "
                         "(T-WP5). The disable half is T-WP15",
                aspects=a,
                verify="Q-3 #3 + Q-EMP-3: the EMP missile leaves the pods and the round turns "
                       "(w618 alone flies straight); the pulse fires; the lock cone acquires a "
                       "car and NEVER a pedestrian. A 2.0 s held lock and an 8-target salvo are "
                       "NOT this row's gate - they have no member (cards B-24 / B-25)",
                why="launcher half of T-WP4, unblocked by operator ruling 4 and by the Fire Leech "
                    "(`w143`) carrying the guided flight (turning speed 300, no no-turning-time) "
                    "and the acquisition cone (AutoAim 0.12/0.15 = the fleet lock-on preset); the "
                    "disable half is T-WP15 (named omission) and the lock hold / salvo / reticle "
                    "link are cards B-24 / B-25 (`tmp/freebuff/reports/wp4-fire-leech.md`)")


def row_wp15(B, J):
    """T-WP4's disable half after the operator's split. No single member on either side, so the
    reconciled 2026-11-08 route is composed (pulse + `w702_emp` clone) and the row is `next`, not
    `out`: the launcher ships, the stall is B-18, and only the duration is UNKNOWN."""
    a = [
        aspect("carrier", "`RBatmobileEMPMissile` `Batmobile_EMP_Missile_Launcher`: the missile's "
               "disable half (`SetDisabledByEMP`, `DisableEnemyDuration` @2400 - the field "
               "serialises no value in the three packages)",
               "**no carrier**: `SetDisabledByEMP` is a state NAME on `RVehicleBatmobileBase`, no "
               "EMP-named member exists on any NPC `RVehicle*` class, and 0 of the fleet's 88 "
               "vehicle weapon components is a `CEMPWeapon`",
               "named omission - nothing to write", "UNKNOWN",
               "`Working/Translation/T_WP4C_TRACKER_EMP.md` (marker `no EMP-named member exists`)"),
        aspect("duration / target filter", "`MissileLockOnDuration` 2.0 s (civilian 1.0), "
               "`DisableEnemyDuration`, `MaxTargets` 8, `TargetSwitchName`",
               "no duration, timer or target-count member in any weapon tune or `AutoAim` block",
               "no mapping", "UNKNOWN", "cards B-24 / B-25"),
        aspect("what JC3 does have", "a weapon gadget that disables an NPC vehicle",
               "the engine's own `CEMPWeapon` (`w702_emp`) exists as a class but 0 of 88 vehicle "
               "weapon components is one, and the fleet's EMP is the truck's entity-level "
               "`CForcePulse` (a blast, not a disable)",
               "the route is T-WP5's card B-18 (clone `w702_emp` onto a driver slot); this row "
               "records the absence rather than owning the build", "decoded",
               "`Research/JC3Grab/EMP.json`; `tmp/freebuff/reports/immobiliser-and-emp-trigger.md`"),
    ]
    return dict(id="T-WP15", code="WPN-4b",
                title="EMP disable / Immobilizer (`RBatmobileEMPMissile`, disable half)",
                jc3=[], socket="-", part="-", dispo="next",
                now="nothing disables an NPC vehicle yet: the composed route is the pulse + the "
                    "`w702_emp` clone (B-18)",
                proposed="**composed route, not an omission** (reconciled 2026-11-08, "
                         "`tmp/freebuff/reports/emp-immobiliser-forcepulse-plans-v2.md`): the "
                         "disable is two carriers, not one member - the entity `CForcePulse` + "
                         "`truck_emp.ftune` applies the stall (T-WP5) and the stalled state is "
                         "written through a cloned `CEMPWeapon` (`w702_emp`) on the second driver "
                         "slot; `is_disabled_by_emp` has 0 bindings in the 1,941 vehicle entries, "
                         "so no NPC flag is written, the clone is the writer, and the launcher "
                         "still ships as T-WP4",
                aspects=a,
                verify="UNKNOWN · the disable duration only: `DisableEnemyDuration` @2400 serialises "
                       "no value in the three packages, and the four probes Q-EMP-1…4 (pilot cards "
                       "only, nothing launched) are the source that settles it",
                why="the disable half of T-WP4 after operator ruling 4 (2026-11-06): no member "
                    "disables an NPC vehicle on either side, so the row records the absence and "
                    "leaves the blast to T-WP4 and the `CEMPWeapon` route to T-WP5 - proof "
                    "`Research/JC3Grab/EMP.json` (the fleet's EMP is the truck's `CForcePulse`, a "
                    "blast) and `Working/Translation/T_WP4C_TRACKER_EMP.md` (no EMP-named "
                    "`RVehicle*` member, 0 of 88 weapon components a `CEMPWeapon`)")


def row_wpn5(B, J):
    o = "Batmobile_EMP_Burst"
    a = [
        aspect("carrier", f"`RBatmobileEMP` `{o}` (3 instances, 36 fields)",
               "entity-level `CForcePulse` object on `truck_emp.ftune` (G2-16), 307 pulses on "
               "232 vehicles (G2-17)", "add a `CForcePulse` + its explosion tune to our entity",
               "decoded", "G2X WPN-5 needle `weapon-slot copy`"),
        aspect("slot", "a weapon-gadget press (`WeaponCoolDown` "
               f"{num(B.v(o, 'RVehicleWeapon.WeaponCoolDown'))} s)", "**no slot**: the pulse is "
               "an entity object", "nothing to bind", "decoded",
               "G2-16: no weapon component on the EMP truck and no pointer from trigger to pulse"),
        aspect("weapon point", "wheels: `MaterialToUpdateWhenPresent` swaps the wheel material "
               f"`{B.v(o, 'RVehicleWeapon.MaterialToUpdateWhenPresent')}`",
               "the pulse's own position: `(0, 2.0356, 0.6992)` on the truck", "place it at the "
               "car centre; the wheel material swap has no member", "decoded",
               "the material swap is BmAK-only"),
        aspect("fire rate", f"`WeaponCoolDown` {num(B.v(o, 'RVehicleWeapon.WeaponCoolDown'))} s",
               "no weapon, no rate", "none", "decoded", ""),
        aspect("damage by effect", "radial stun/push, no damage number in `WEAPONS.json`",
               "pulse: 100 player damage in 25 m, held at full radius", "keep the pulse's own "
               "numbers", "decoded", "G2-16"),
        aspect("projectile speed", "none (a burst around the car)", "none", "none", "decoded",
               ""),
        aspect("spread curve", "none", "none", "none", "decoded", ""),
        aspect("heat / overheat", "none", "none", "none", "decoded (fleet)", ""),
        aspect("lock-on", "none", "none", "none", "decoded", ""),
        aspect("blast / explosion", f"`ImpulseComponent` "
               f"`{B.v(o, 'RBatmobileEMP.ImpulseComponent')}` (undecoded array, 4 rows)",
               "the pulse's tune (`EMP`, 100 / 25 m)", "the impulse stays BmAK's", "UNKNOWN",
               "`EMPFireSwitch` and `FireParticle` are undecoded arrays in G1-08"),
        aspect("effects", "`ChargeParticle`, `Batmobile_Seismic_Sonar*` family", "`EMP` "
               "`explosion_*.effc`", "T-17", "decoded", ""),
        aspect("sounds", "`Play_Batmobile_EMP`", "the truck's `emp` events", "T-16", "decoded",
               ""),
        aspect("closest chain", "`RBatmobileEMP`: `DisableEnemyDuration` @2400, `EMPImpulse` "
               "@2512, `EMPVehicleImpulse` @2528 - all three serialise no value in the three "
               "packages, so BmAK does not carry its own disable numbers either",
               "**closest system, member by member**: the entity `CForcePulse` `EMP` "
               "(`SettingsFile` = `truck_emp.ftune`: 8 numbers, player and AI 100 damage in "
               "25 m held at full radius) at `world` `(0, 2.0356, 0.6992)`, plus the three "
               "flags `id:4912FC04` 0 / `id:AE6F7EFF` 1 / `id:CF4F7880` 1 - a combination "
               "unique among all 307 pulses - and `id:D3DDD766` -> `CMaterialEffectTable` "
               "`emp_flatbed_table` (`explosion_emp_flatbed.effc`) + `id:060AAA81` 20 / "
               "`id:24872388` 100 / `id:530046B3` 10 / `id:9865E7F2` 100 / `id:A1B0DAF9` 2",
               "copy the object, the tune and the flag values unchanged; what the flags mean is "
               "Q-EMP-2's question, not a value to guess", "decoded",
               "`Research/JC3Grab/EMP.md` sections 2 and 7; `Research/JC3Grab/FORCEPULSE.md` "
               "sections 1, 3, 4"),
        aspect("trigger", "a gadget press; `ChargingEMP` / `bButtonPressed` are runtime bool "
               "bits, not a serialised input",
               "no member fires a pulse: 293 of 307 pulses are owned by an explosion pointer "
               "`id:B5AE7986`, the 14 unowned have no pointer at all, and 0 of 23 tunes is a "
               "horn, collision or scan path",
               "the trigger is card B-18's work: the engine's own `CEMPWeapon` hit path, or a "
               "graph rule (the mm340 `BOMB_JEEP` pulse is the only graph-held pulse)",
               "UNKNOWN",
               "`Research/JC3Grab/FORCEPULSE.md` section 4.3; "
               "`tmp/freebuff/reports/immobiliser-and-emp-trigger.md` section 7"),
        aspect("build card", "the disable itself is engine state: `is_disabled_by_emp` is in "
               "`JustCause3.exe`'s vehicle-variable vocabulary @0x24EA080, next to "
               "`engine_damage` and `is_frozen`",
               "`CEMPWeapon` (`.?AVCEMPWeapon@@` @0x2D6E058) ships as `w702_emp` (id 702, type "
               "6, 500 damage / 50 m, 3 `CBarrelSpinWeaponComponent`) and `w503_turret_emp` "
               "(503, type 2, 500 / 750 m); 0 of the fleet's 88 vehicle weapon components is a "
               "`CEMPWeapon`, and 0 assets bind the state (0 literal hits in 1,941 entries, 0 "
               "hash hits in 1,307)",
               "**card B-18**: clone `w702_emp.wtunec`, mount it on the second driver slot "
               "`id:00568A74`, then probes Q-EMP-1…4 measure whether the engine stalls a car and "
               "for how long", "decoded",
               "`Research/JC3Grab/EMP.md` section 6; `Research/JC3Grab/EMP_DISABLE.json`; "
               "`tmp/freebuff/reports/immobiliser-and-emp-trigger.md` sections 6-8"),
        aspect("BmAK-exact", "no: the burst's effect, its 100/25 m numbers and its flags are "
               "carried, but the disable's duration, impulses and power-level charge serialise "
               "no value on BmAK's own side and no JC3 asset writes the disable state",
               "the row is `next`, not exact; B-18 plus the four probes is the work that would "
               "make it exact, and none of them runs under the test ban",
               "**not BmAK-exact today**", "derived",
               "only 12 of the burst's 36 offsets are tagged (`EMP_DISABLE.json` -> "
               "`bmak.serialized`)"),
    ]
    return dict(id="T-WP5", code="WPN-5", title="EMP burst - closest chain: entity `CForcePulse` "
                "+ the engine's `CEMPWeapon` disable (B-18)",
                jc3=["CForcePulse"], socket="car centre", part="body", dispo="next",
                now="no pulse object in the build",
                proposed="**closest system**: copy `CForcePulse` `EMP` + `truck_emp.ftune` "
                         "(100 in 25 m at full radius; cooldown 2.0 s, four burst stages to 250 / 30 / 30 cm, lifetime 0.2-4.0 s, spawn distance 0-1500, `tmp/freebuff/reports/emp-immobiliser-forcepulse-plans-v2.md`) + the unique flag triple, and reach the "
                         "disable through a cloned `CEMPWeapon` (`w702_emp`) on the second driver "
                         "slot; the trigger is card B-18, not a value",
                aspects=a,
                verify="Q-EMP-1…4 (B-18): does the engine's own `w702_emp` stall a stock car, "
                       "does the pulse alone, is a `CEMPWeapon` accepted on a car, and how long "
                       "the state lasts (the only source for `DisableEnemyDuration`)",
                why="moved off `blocked`: the effect half is decoded end to end (object, tune, "
                    "flags, material table) and the missing half is one named capability - the "
                    "writer of `is_disabled_by_emp` - which is BUILD card B-18 with probes "
                    "Q-EMP-1…4. BmAK-exact: no (disable duration UNKNOWN on both sides)")


def omission(B, J, code, rid, title, cls_name, object_name, jc3_line, why_proof, note):
    """One named-omission row: BmAK fields on one side, a proven absence on the other."""
    o = object_name
    fields = []
    obj = B.obj(o) if o else None
    if obj:
        for f in obj["fields"]:
            v = f.get("value")
            if f.get("ref"):
                v = "ref:" + str(f["ref"].get("path"))
            if v not in (None, "", "ref:None"):
                fields.append(f"`{f['path']}` {num(v) if not isinstance(v, str) else v}")
    shown = fields[:5]
    g = J.g2x(code)
    a = [
        aspect("carrier", f"`{cls_name}` `{o}`: " + (", ".join(shown) + (
            f" (+{len(fields) - len(shown)} more fields)" if len(fields) > len(shown) else "")
            if fields else "fields listed in G1-08"),
               f"**proven absence** - {g['fact']}" + (f" (proof {jc3_line})" if jc3_line
                                                    and jc3_line != "-" else ""),
               "named omission", "UNKNOWN",
               f"G2X {code}: {', '.join(g['files'])}"
               + (f" (must not contain {', '.join(g['must_not'])})" if g["must_not"] else "")),
        aspect("slot", "no JC3 slot can carry it", "-", "-", "UNKNOWN", ""),
        aspect("weapon point", "-", "-", "-", "UNKNOWN", ""),
    ]
    if note:
        a.append(aspect("what remains", note, "-", "-", "decoded", ""))
    return dict(id=rid, code=code, title=title, jc3=[], socket="-", part="-", dispo="out",
                now="nothing on either side: there is no JC3 member to carry it",
                proposed="named omission - the absence is the record",
                aspects=a, verify="none: nothing to fire, nothing to verify - the absence is the "
                                  "record", why=why_proof)


def row_wp7(B, J):
    """WPN-7: the drone hacker. No allegiance class exists, but the systems that do the job do."""
    o = "Drone_Hacker"
    cooldown = B.v(o, "RVehicleWeapon.WeaponCoolDown")
    mesh = B.v(o, "RInventoryGadget.Mesh")
    a = [
        aspect("carrier", f"`RBatmobileAllegianceSwitcher` `{o}` (3 packages, 13 fields, 39 "
               f"field rows, identical in every package): `BatmobileHackerEffect` -> "
               f"`Particles.DroneHacker_Beam`, `SuccessfulHackEffect` -> "
               f"`Particles.DroneHacker_Success`, `BatmobileHackerEffectHvyTank` -> "
               f"`Particles.CobraHacker_Beam`, `SuccessfulHackEffectHvyTank` -> "
               f"`Particles.CobraHacker_Success`, `WeaponCoolDown` {num(cooldown)} s, "
               f"`RInventoryGadget.Mesh` -> `{mesh}`",
               "**closest system**: `SAttachedEffect` on the drone-side weapon entity (`Effect` + "
               "`Usage` + optional `world`, 5,342 objects in 232 `.epe` graphs) plus the SAM "
               "context-act hack as the interaction shape (`CInteractionGraph` with a `use_item` "
               "exit state, 2 `CInteractionTrigger` volumes, "
               "`rico_contextact_hack_sam{,_enter,_exit}.anim`)",
               "no allegiance member exists: the beam and success effects become two "
               "`SAttachedEffect` rows, and the hack itself is an authored interaction", "decoded",
               "`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP7 table; "
               "`Research/JC3Grab/GADGETS_HACK_TRACK.md`"),
        aspect("slot", f"a weapon-gadget press (`WeaponCoolDown` {num(cooldown)} s)",
               "`burst_cooldown` in the cloned weapon tune (22 rows in the fleet) and one of the "
               "2 driver slots; the slot count itself is T-WP13",
               "the trigger maps to the tune's cooldown member; the 1.0 s value has no unit "
               "bridge, so it is carried as the tune's own number", "decoded",
               "`Research/JC3Grab/WEAPONS.jsonl`; `Research/JC3Grab/JC3_HUD_WEAPONS.md`"),
        aspect("weapon point", f"`RInventoryGadget.Mesh` `{mesh}` - the gadget mesh rides the "
               f"mount, no muzzle is named",
               "`SWeaponPoint` fire positions on the weapon entity (8 in the SAM dump), and the "
               "gadget mesh is shipped inside the weapon `.ee`",
               "author a beam socket and a second success attachment; no JC3 file names a drone "
               "beam", "decoded", "`Research/JC3Grab/WEAPON_WIRING.jsonl` section 2b"),
        aspect("target side", "the whole point of the gadget: the target changes side "
               "(`RBatmobileAllegianceSwitcher`) - an aircraft for the heavy-tank variant",
               "**0 loyalty members**: no `allegiance`/`owner` in 295 decoded `.ee` wiring dumps; "
               "`faction` exists only on weapon points (5 on the SAM turret's "
               "`CTurretWeaponComponent`), camera, light and physics structs; `ignore_faction` / "
               "`sides` are camera hints",
               "the side flip is authored on the target's weapon points and its reader recorded - "
               "card B-19; what the SAM hack does to ownership at runtime is UNKNOWN",
               "UNKNOWN", "`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` lead 1"),
        aspect("friendly drone", "BmAK has no friendly-drone mechanic; the hack is the mechanic",
               "`Item.Name` = `hash_jenkins(leaf)` (REBELDROP.md section 4) spawns an entity from "
               "the radial drop: 196 vanilla items, 0 name a drone; the artwork and drop video "
               "already ship (`v2901_drone_eden_elitedrone_rebeldrop.ddsc` / `.bikc`, 2 assets)",
               "a player-side drone is a build choice, not a decode (B-19 step 4); its side is "
               "the same missing member as above", "decoded",
               "`Research/JC3Grab/REBELDROP.md` section 4; report lead 2"),
        aspect("hud line", "`NotEnoughEnergyThought` -> "
               "`Lines.Char_Batman_Misc_Cobra_Barrage_Energy_B_01`",
               "`CreatePoi(type, use_progress_bar, is_minor, label)` on `ui/hud.gfx` (32 "
               "`POI_TYPE_*` constants); a 'thought' element does not exist",
               "the line becomes a POI label or a HUD string; T-19 owns the HUD", "decoded",
               "`Research/JC3Grab/JC3_HUD_WEAPONS.md` section 5"),
        aspect("sounds", "`HackingSound`, `SucessfullHackSound`, `BeamPositionalSound` (Ww/Wwise "
               "events), plus `DroneHackerMaterial` -> `Materials.DroneHacker_Beam_INST`",
               "0 audio members and 0 material members in the 444 decoded weapon-tune member "
               "paths; the `.effc` carries the texture and the entity's audio module the events",
               "asset-side only (T-16/T-17 + B-17's writer)", "decoded",
               "`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` 'weapon-tune audio' row"),
        aspect("build card", "the gadget itself is 13 fields on one class; the behaviour is "
               "native",
               "the three pieces exist separately (two `SAttachedEffect` rows, the context-act "
               "graph, a weapon-entity tune) and no file composes them",
               "**card B-19**: effects + interaction + the authored side flip; a probe build "
               "records whether the side flip holds", "derived",
               "`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` leads 1-2"),
        aspect("BmAK-exact", "no: beam/success effects, cadence and the HUD line are carried; "
               "the allegiance switch - the gadget's whole behaviour - has no member on either "
               "side (BmAK's class is native code)",
               "the row is `next`, not exact; B-19 is what would close it",
               "**not BmAK-exact today**", "derived",
               "`Research/JC3Grab/ENTITIES.md` (0-class census for `allegian`/`hacker`/`hijack`)"),
    ]
    return dict(id="T-WP7", code="WPN-7",
                title="Drone hacker - closest chain: `SAttachedEffect` beam + the context-act hack "
                      "+ an authored side flip (B-19)",
                jc3=[], socket="-", part="-", dispo="next",
                now="nothing: no allegiance class, no beam effect, no hack interaction",
                proposed="**closest system**: two `SAttachedEffect` rows (beam `Usage` `Fire` "
                         "4131019937, success value-driven) on the drone-side entity, the SAM "
                         "context-act graph as the interaction, and the side flip authored on the "
                         "target's weapon points - card B-19",
                aspects=a,
                verify="B-19 probe: hack a stock drone and record whether its weapon points stop "
                       "firing for its own side - the one thing no file can decide",
                why="moved off `out`: the systems that do the job are decoded (the `SAttachedEffect` "
                    "beam/success pair, the SAM context-act hack, `faction` on weapon points) and "
                    "the one missing member - allegiance/ownership - is BUILD card B-19. "
                    "BmAK-exact: no")


def row_wp8(B, J):
    """WPN-8: the seismic sonar. A visible pulse is the half JC3 can carry; B-20 authors the rest."""
    o = "Batmobile_Sonar"
    a = [
        aspect("carrier", f"`RBatmobileSonar` `{o}` (3 objects, 22 fields, 66 field rows, 0 "
               f"differences across the three packages): `ScanParticle` -> "
               f"`Particles.Batmobile_Seismic_Sonar` (205 B), `BlastParticle` -> "
               f"`Batmobile_Seismic_Sonar_Charged` (217 B), `ScanSound`/`BlastSound` -> "
               f"`Play_BML_Sonar_Pulse_Search` / `_Full`, charge `Rumble_Lp` + `Stop`, scanner "
               f"`Turn_On` / `Turn_Off`, `RInventoryGadget.Mesh` -> `{o}.GadgetMesh`",
               "**closest system**: a `CForcePulse` on the car (307 pulses / 232 entities) with a "
               "zero-damage `.ftunec` copied from `gen_explosion_5m_nodamage.ftune` (0 damage / "
               "5 m, 2 pulses), its `CMaterialEffectTable` hook, a private `.effc` for the ring "
               "and the `BML_Sonar` bank",
               "copy the pulse + tune; the six sound events import as audio assets; the ring is "
               "an authored `.effc` (B-17's writer)", "decoded",
               "`tmp/freebuff/reports/sonar-and-scan-pulse.md` sections 1, 2.1, 4; "
               "`Research/JC3Grab/FORCEPULSE.md` section 3"),
        aspect("slot", "a gadget press with a charge and a blast; `ChargingScreenShake` 10000 / "
               "[4,4,4] / [40,40,40] / true and `BlastScreenShake` [0,70,70] ...",
               "no slot: the pulse is an entity object; the shake class exists "
               "(`CameraShakeModifierParams` in the `.ctunec` family) with undecoded fields",
               "the charge/blast shake is system-level only - its values convert through no "
               "decoded field", "UNKNOWN",
               "`Research/JC3Grab/FX.md` `.ctunec` class list; report section 2.4"),
        aspect("radius", "no radius member on the class at all: the sonar owns particles, six "
               "sound events, two shake structs and a mesh",
               "`PlayerDamageRadius` 1.5..50 m across the 23 `.ftunec` tunes (5 m in the "
               "zero-damage precedent); `AIDamage`/`AIDamageRadius` and the two "
               "`*RadiusPercentageMax` flags",
               "the radius is a design value copied from a shipped 0-damage tune, not a decode",
               "derived", "report section 2.1; `FORCEPULSE.md` section 3"),
        aspect("reveal", "the sonar reveals the surroundings - script/native, no serialised "
               "member, and the treadmark half (`BasicScanEffect` -> `Engine.Tire_Track_Pulse_P`, "
               "`BasicScanSound` -> `Play_BML_Sonar_Forensics_Pulse`) is `missing-object` on "
               "BmAK's own side",
               "`CreatePoi(type, use_progress_bar, is_minor, label)`: 32 `POI_TYPE_*` constants, "
               "`POI_TYPE_LOCK_ON_TARGET` 21 is the only one with a decoded look, and **0 decoded "
               "script creates a scan/reveal POI**; `CAimPOIWeaponComponent` (11 builds) is the "
               "only POI-shaped vehicle component",
               "the reveal is card B-20's work: a trigger plus an authored marker renderer; "
               "chaos-object markers, enemy spotting and a scanner effect are all UNKNOWN",
               "UNKNOWN", "report sections 2.2 and 2.5; `JC3_HUD_WEAPONS.md` section 5"),
        aspect("audio", "`BML_Sonar` bank: 6 events - Pulse_Search `0x97CBF248`, Pulse_Full "
               "`0xFFCC9813`, Rumble_Lp `0x2A77A8B4`, Stop `0x835146BE`, Turn_On `0x02EE7381`, "
               "Turn_Off `0x265FE0CD`",
               "no JC3 sonar bank or event: the bank imports as material and is fired by the same "
               "code that fires the pulse",
               "**named carrier, not a gap**: `BmGame.BML_Sonar`, 355,830 B, BKHD id 112, 7 HIRC "
               "event objects, 6 distinct names, all ids verify as `fnv1(lower(name))` "
               "(18 references = 6 x 3 packages)", "decoded",
               "`Research/BatmobileGrab/AUDIO_BANKS2.md:154-159,169`; report section 1a"),
        aspect("trigger", "charge, then blast; `ScannerOn`/`ScannerOff` imply a mode toggle",
               "0 of the 307 pulses is a scan, horn or collision path - every one is an explosion "
               "blast, and 14 have no owner pointer",
               "a vehicle action that fires the pulse, plus the scanner on/off state: card B-20",
               "UNKNOWN", "`FORCEPULSE.md` section 4; report section 4"),
        aspect("build card", "the operator lead (2026-11-06): outside a mission the sonar is \"just "
               "a good-looking pulse\", and treadmark tracking is mission-dependent",
               "the base behaviour composes from three portable pieces: the 0-damage pulse, an "
               "`.effc` ring and the `BML_Sonar` bank",
               "**card B-20**: pulse + private effect + bank import + the authored trigger and "
               "marker; the treadmark row stays out of scope by the operator's own lead",
               "derived", "report section 4"),
        aspect("BmAK-exact", "no: the pulse look, its 0-damage numbers and all six sound events "
               "are carried; the reveal and the treadmark tracking are absent",
               "the row is `next`, not exact; B-20 closes the base behaviour, the treadmark row is "
               "a separate later one (its BmAK assets are `missing-object`)",
               "**not BmAK-exact today**", "derived",
               "report sections 1a and 2.5"),
    ]
    return dict(id="T-WP8", code="WPN-8",
                title="Seismic sonar - closest chain: 0-damage `CForcePulse` + the `BML_Sonar` bank "
                      "(B-20)",
                jc3=["CForcePulse"], socket="car centre", part="body", dispo="next",
                now="nothing: no pulse, no ring, no sonar sound",
                proposed="**closest system**: the entity `CForcePulse` with "
                         "`gen_explosion_5m_nodamage.ftune` (0 / 5 m), a private ring `.effc` "
                         "and the `BML_Sonar` bank, fired by an authored vehicle action - card B-20",
                aspects=a,
                verify="B-20 probe: fire the pulse at a parked car and record push-only behaviour "
                       "(no damage) and that the six events play; the reveal has no probe until "
                       "the marker exists",
                why="moved off `out`: the base sonar is a visible pulse and every piece of it is "
                    "named (pulse object, 0-damage tune precedent, ring effect, 6 verified sound "
                    "events); the reveal is BUILD card B-20. BmAK-exact: no")


def row_wp9(B, J):
    """WPN-9: the vehicle tracker. A weapon entity + tune + HUD tracker, with two named gaps."""
    o = "Vehicle_Tracker"
    mesh = B.v(o, "RInventoryGadget.Mesh")
    a = [
        aspect("carrier", f"`RPursuitModeMissileLauncher` `{o}` (3 packages, 7 fields) + the "
               f"tracker projectile (16 fields): `ProjectileArchetype` -> "
               f"`Projectiles.Batmobile_Tracker_Projectile`, `LaunchSocketName` = "
               f"`BattleModeSpotLight`, `LaunchRotationOffset` [5461, 0, 0], "
               f"`RInventoryGadget.Mesh` -> `{mesh}`",
               "**closest system**: a mounted weapon entity `.ee` plus "
               "`missile_weapon[0].tuning.missile_base_tuning.*` (the homing numbers that exist) "
               "and a `SWeaponPoint` whose `world` matrix carries the fire direction",
               "clone a missile tune under a private path and add the fire position; the rest is "
               "the projectile entity", "decoded",
               "`tmp/freebuff/reports/hacker-and-tracker-gadgets.md` T-WP9 table; "
               "`Research/JC3Grab/WEAPONS.jsonl`"),
        aspect("weapon point", "`LaunchSocketName` `BattleModeSpotLight` with "
               "`LaunchRotationOffset` [5461, 0, 0] = **30.0 deg** (5461/65536 x 360)",
               "`SWeaponPoint.world` (a 4x4 matrix; 8 fire positions in the SAM dump) and the "
               "`BattleModeSpotLight` socket, which the lights rig also uses",
               "bake 30.0 deg into the matrix; the build must decide the socket's two uses "
               "(launch and spotlight), T-L17 already places the light", "derived",
               "`Research/BatmobileGrab/SOCKETS_JC3.json`; `Research/JC3Grab/WEAPON_WIRING.jsonl`"),
        aspect("homing", "`RBatmobileMissile`: an unnamed homing bool true, `HomingDelay` 0.2, "
               "`AccelRate` 30000.0, `Projectile.MaxSpeed` 20000.0, `Trail`/`Mesh` on the "
               "projectile",
               "`missile_base_tuning.missile_loose_lock_distance` and "
               "`meters_times_speed_in_front_of_target` are the only homing-adjacent members; "
               "**no homing flag, delay or damage member** in 444 decoded tune member paths",
               "the homing behaviour is authored on the projectile entity (card B-21) and which "
               "member the engine reads is UNKNOWN - a probe records it", "UNKNOWN",
               "report 'tracker projectile' table; `Research/JC3Grab/WEAPONS.md`"),
        aspect("hud readout", "a distance readout and a yellow or grey circle on the tracked "
               "vehicle",
               "`CreatePoi(type, use_progress_bar, is_minor, label)`: 32 `POI_TYPE_*`, "
               "`POI_TYPE_LOCK_ON_TARGET` 21 (one rotating reticle, 1.5 s per turn); the "
               "mission tracker graphs `graphs/mission/mm130/mm130_tracker.gdc/.gsc` and "
               "`graphs/spawner_group_tracker.gsc` (37 random-encounter graphs) create them; "
               "`CAimPOIWeaponComponent` on 11 fleet vehicles is the only vehicle-side POI "
               "reference",
               "**no distance member**: `CreatePoi` takes type, progress bar, minor flag and "
               "label only, so the readout is a HUD element (T-19) fed by a tracker graph; the "
               "marker's colour/shape must be authored (no separate marker art ships)",
               "derived", "report lead 3; `JC3_HUD_WEAPONS.md` section 5"),
        aspect("damage", "`MyDamageType` 0 (null), `DamageRadius` 0.0, "
               "`MomentumTransfer` 500.0",
               "the weapon tune's `damage` / `impulse` members exist but JC3 has no "
               "`MomentumTransfer` shape; a 0-damage tracker round is the closest form",
               "damage crosses through T-14's health ratio; the 500 momentum has no bridge",
               "derived", "`Research/JC3Grab/DAMAGE_MODEL.md` section 3"),
        aspect("build card", "the gadget's identity is the projectile archetype; its job is the "
               "track, not the damage",
               "its three pieces are separate systems: the weapon entity + tune, the projectile "
               "entity's mesh/trail, and the HUD tracker graph",
               "**card B-21**: the weapon entity + 30 deg fire position, the authored homing on "
               "the projectile, and the tracker graph + distance HUD element", "derived",
               "report 'tracker projectile' table and lead 3"),
        aspect("BmAK-exact", "no: the fire position, the 30 deg rotator and the launch socket "
               "are exact, but the homing flag/delay and the distance readout have no member",
               "the row is `next`, not exact; B-21 closes it", "**not BmAK-exact today**",
               "derived", "report T-WP9 and projectile tables"),
    ]
    return dict(id="T-WP9", code="WPN-9",
                title="Vehicle tracker - closest chain: mounted weapon entity + `missile_base_tuning` "
                      "+ a HUD tracker graph (B-21)",
                jc3=[], socket="BattleModeSpotLight", part="batmobile_missile_pod_l/r",
                dispo="next",
                now="nothing: no tracker projectile, no tracked-vehicle marker",
                proposed="**closest system**: a weapon entity with the tracker tune on the "
                         "`BattleModeSpotLight` socket (30 deg baked into the `SWeaponPoint` "
                         "matrix), authored homing on the projectile and a mission-style tracker "
                         "graph creating a lock-on POI plus a distance HUD element - card B-21",
                aspects=a,
                verify="B-21 probe: fire at a moving car and record whether the round homes and "
                       "whether a POI with a live distance appears",
                why="moved off `out`: the launcher, the fire position and the HUD POI system are "
                    "decoded, and the two missing pieces (the homing flag, a distance member) are "
                    "BUILD card B-21. BmAK-exact: no")


def row_wpn11(B, J):
    g = J.g2x("WPN-11")
    a = [
        aspect("carrier", "`RBatmobileBooster` `Batmobile_Booster` (4 instances, 8 fields): the "
               "gadget mesh only", f"`arcade.nitro_boost` on 145/232 vehicles (G2-23): torque "
               "x2, grip x2, push, blend 0.2 s, +40 km/h", "already translated as T-B2/T-B3",
               "decoded", "G2X WPN-11 needle `nitro_boost`"),
        aspect("slot", "a gadget, not a weapon", "nitro is a button, not a slot", "none",
               "decoded", ""),
        aspect("weapon point", "no muzzle; `Afterburner` socket for the flame (G1-13)",
               "`EngineNitro` usage on the donor", "T-17 T-FX7", "decoded", ""),
        aspect("fire rate", "none", "`nitro_boost` timings (T-B rows)", "-", "decoded", ""),
        aspect("damage by effect", "none", "none", "-", "decoded", ""),
        aspect("projectile speed", "none", "none", "-", "decoded", ""),
        aspect("spread curve", "none", "none", "-", "decoded", ""),
        aspect("heat / overheat", "none", "none", "-", "decoded", ""),
        aspect("lock-on", "none", "none", "-", "decoded", ""),
        aspect("blast / explosion", "none", "none", "-", "decoded", ""),
        aspect("effects", "`Batwing_Exhaust_P` family (G1-16)", "`car_cycle_base_dual_nitrous`",
               "T-17 T-FX7", "decoded", ""),
        aspect("sounds", "`BML_Burnout` (G1-15)", "the nitro samples test-060 swapped", "T-16",
               "decoded", ""),
        aspect("geometry", "`Batmobile_Booster.GadgetMesh` - a cockpit gadget mesh",
               "no gadget mesh member: nitro has no visible gadget", "the mesh is a part row "
               "(B-04); the boost itself is live", "UNKNOWN", ""),
    ]
    return dict(id="T-WP11", code="WPN-11", title="Booster / afterburner (`RBatmobileBooster`)",
                jc3=["nitro_boost"], socket="Afterburner", part="batmobile_jet", dispo="keep",
                now="live: test-091 carries the nitro block (T-B2/T-B3); no gadget mesh",
                proposed="keep; the gadget mesh is a cockpit part row (B-04)",
                aspects=a,
                verify="Q-2 A9: 0-100 with and without boost; the take already owns T-B1/T-B3",
                why="the afterburner is JC3 nitro, live since test-091 (T-B2/T-B3); the gadget "
                    "mesh stays a cockpit part")


def row_wpn12(B, J):
    hud = J.hud
    wpn12 = hud["wpn12"]
    setters = sorted({s["name"] for s in B.hud["HudModuleBatmobile"]["setters"]})
    radial = sorted({s["name"] for s in B.hud["RadialGadgetSelect"]["setters"]})
    gaps = [w for w in wpn12 if "no JC3 member" in (w.get("limit") or "")
            or w["disposition"].startswith("named omission")]
    a = [
        aspect("carrier", f"`HudModuleBatmobile` {len(setters)} setters incl. "
               f"{', '.join('`%s`' % s for s in ('UC_SetPrimaryWeapon', 'UC_SetSecondaryWeapon', 'UC_SetSpecialWeapons', 'UC_SetCannonCoolDown', 'UC_SetMachineGunAccuracyFrame') if s in setters)}; "
               f"`RadialGadgetSelect` {len(radial)} setters incl. `UC_SelectWheelGadget`",
               f"{hud['slots']['count']} clips (`MCI_vehicle_weapons0/1`), {len(wpn12)} mapped "
               f"elements, heat = {hud['heat']['body_mentions']} body mentions",
               "the HUD translation is T-19; this row records the API facts it needs", "decoded",
               "G2X WPN-12 needle `MCI_vehicle_weapons0`"),
        aspect("slot", "BmAK: primary + secondary + **3 special-weapon states** "
               "(`UC_SetSpecialWeapons(int, int, int)`)",
               f"JC3: **{hud['slots']['count']} slots**, `E_NUM_WEAPON_SLOTS` "
               f"{hud['slots']['on_foot_slots']} is the on-foot wheel", "2 of 5 BmAK slots have "
               "a member", "decoded", "the special-weapon states are the ones T-WP13 counts"),
        aspect("weapon point", "radial gadget wheel (index-based: `UC_UpdateSelectedIndex`)",
               "fixed two-clip array, no wheel", "no wheel member", "decoded", ""),
        aspect("fire rate", "-", "`UpdateVehicleWeapons` cooldown arg "
               f"`weapon_cooldown` (0..1); bar {hud['cooldown']['bar_frames']} frames",
               "-", "decoded", ""),
        aspect("damage by effect", "`UC_SetHealth`, `UC_SetImpactDamageFlash`",
               "the vehicle health bar", "T-14/T-19", "decoded", ""),
        aspect("projectile speed", "-", "-", "-", "UNKNOWN", ""),
        aspect("spread curve", "`UC_SetMachineGunAccuracyFrame(int)` - an accuracy frame index",
               "`UpdateWeaponReticle(shape, ...)` 14 shapes / 5 look states", "shape id UNKNOWN",
               "decoded", "G2-25"),
        aspect("heat / overheat", "`HeatBarStart`/`HeatBarSize` on the Vulcan object",
               f"0 heat params (`params_with_heat` {hud['heat']['params_with_heat']})",
               "no heat bar member: named omission", "decoded (fleet)",
               "WPN-12's heat is a stated absence on both sides"),
        aspect("lock-on", "`LockedOnSound`/`LockOnBeepSound` on three weapons",
               f"one `POI_TYPE_LOCK_ON_TARGET` {hud['lockon']['lock_on_type']}, rotation "
               f"{hud['lockon']['lock_on_rotation_time']} s, banner "
               f"{hud['lockon']['missile_locked_timer']} s", "marker only", "decoded", "G2-25"),
        aspect("blast / explosion", "-", "-", "-", "UNKNOWN", ""),
        aspect("effects", "-", "-", "-", "UNKNOWN", ""),
        aspect("sounds", "`LockOnBeepProportionParam` `BML_AP_Rocket_Lock` RTPC",
               "`dlc_wingsuit_weapon_ready` on the cooldown bar", "T-16", "decoded", ""),
        aspect("what the API does not carry", f"{len(gaps)} of {len(wpn12)} mapped elements have "
               "no JC3 member", "; ".join(f"`{w['element']}`" for w in gaps), "-", "decoded",
               "quoted from G2-25's own wpn12 table"),
    ]
    return dict(id="T-WP12", code="WPN-12", title="Weapon HUD (`HudModuleBatmobile`)",
                jc3=["hud.gfx"], socket="-", part="-", dispo="next",
                now="the donor's HUD: 2 clips, no heat bar, one lock POI",
                proposed="T-19 maps the 2 slots, the reticle, the cooldown bar and the lock "
                         "marker; heat is a named omission",
                aspects=a,
                verify="Q-1 #5 / Q-3 #3: the slot icons, the reticle and the cooldown bar follow "
                       "the weapon that is firing; pass = 2 slots show the 2 bound ids",
                why="WPN-12's API facts (2 slots, reticle, cooldown, no heat, one lock marker) "
                    "with the hud.gfx translation handed to T-19, which lists T-11 as a dep")


def row_slots(B, J):
    donor, tank = J.entity(DONOR_EE), J.entity(TANK_EE)
    dslots = donor["roots"][0]["slots"]
    tslots = tank["roots"][0]["slots"]
    donor_slot = next(k for k, v in dslots.items() if v.get("target"))
    tank_main = [k for k, v in tslots.items() if (v.get("target") or "").startswith("w602")][0]
    tank_second = [k for k, v in tslots.items() if (v.get("target") or "").startswith("w603")][0]
    hud = J.hud
    a = [
        aspect("carrier", "11 weapon classes + 1 HUD code; D-7 says **every weapon in both "
               "modes**", f"{len(J.wiring)} armed entities, **max {max(w['counts']['driver_slots'] for w in J.wiring)} "
               f"driver slots**, no active-slot index and no next/previous weapon action "
               "anywhere in the `.epe`", "no carrier for 11 weapons", "UNKNOWN",
               "G2-11 section 2a/b: the only slot data in the files is the two root pointers"),
        aspect("slot", f"BmAK: primary + secondary + 3 special states (`UC_SetSpecialWeapons`), "
               "selected through the wheel", f"`{tank_main}` -> w602, `{tank_second}` -> w603; "
               f"the donor uses `{donor_slot}` -> w618; HUD draws {hud['slots']['count']} clips",
               "2 slots, and both are used by the cannon + Vulcan pair the tank proves",
               "decoded", "the tank is the only land vehicle with 2"),
        aspect("weapon point", "-", f"{sum(len(w['weapons'][0]['points']) for w in (donor, tank))} "
               "fire points across the two carriers", "-", "decoded", ""),
        aspect("fire rate", "-", "-", "-", "UNKNOWN", ""),
        aspect("damage by effect", "-", "-", "-", "UNKNOWN", ""),
        aspect("projectile speed", "-", "-", "-", "UNKNOWN", ""),
        aspect("spread curve", "-", "-", "-", "UNKNOWN", ""),
        aspect("heat / overheat", "-", "-", "-", "UNKNOWN", ""),
        aspect("lock-on", "-", "-", "-", "UNKNOWN", ""),
        aspect("blast / explosion", "-", "-", "-", "UNKNOWN", ""),
        aspect("effects", "-", "-", "-", "UNKNOWN", ""),
        aspect("sounds", "-", "-", "-", "UNKNOWN", ""),
        aspect("the answer D-7 asked for", "all 11 gadgets, both modes, no per-mode split",
               "2 driver slots; a 3rd would need a root property no file has and a HUD clip the "
               "movie does not create", "**no mechanism carries 11**: the row is blocked, not "
               "translated", "UNKNOWN",
               "three ways out, none in the files: extra root pointer (absent), a switching "
               "action (absent), or 2 slots (contradicts D-7)"),
    ]
    return dict(id="T-WP13", code="D-7", title="Slot capacity — 8 forced slots for every BmAK "
                                         "weapon",
                jc3=["main_weapon", "id:00568A74", "CCar"], socket="-", part="-", dispo="next",
                now="the build carries the donor's single driver slot (w618 on main_weapon)",
                proposed="**forced (operator ruling 3, 2026-11-06)**: the two reference graphs "
                         "carry 2 non-null slot pointers each and a shield that is NOT a slot "
                         "(Imperator: 3 `BavariumShield` parts + 1 usage + 2 effects + 1 sound; "
                         "Urga Mstitel: 1 part), so a third slot is a design decision, not a "
                         "decoded value. Build **four `CCar` roots on the one entity**, each with "
                         "`main_weapon` (`id:851CAABE`) and `id:00568A74` non-null = **8 slots** "
                         "for the 8 slot-able BmAK objects (heavy cannon, V2 cannon, missile "
                         "launcher, EMP launcher, tracker, Joker cannon, Joker V2, Joker "
                         "launcher); the 4 `mounted_weapon`/`mounted_weapon_2` pointers stay "
                         "null (no graph mixes driver and gunner slots), and only decoded "
                         "property names are used - 0 invented. Multi-root precedent: "
                         "`v4603_plane_urga_cargotransport_military_cargo_tank` (`CAirPlane` + "
                         "`CCar`). The 5 non-slot gadgets keep their own objects: `CForcePulse` "
                         "(T-WP5), `arcade.nitro_boost` (T-WP11), winch (B-22… B-16), sonar "
                         "(B-20), hacker (B-19). Points needed: `RiotSuppressorMuzzle` (socket "
                         "exists, 0.389 / 1.451 / 0.142, no point) and the Joker weapons' "
                         "points (no Joker socket decoded) - both gaps, not values",
                aspects=a,
                verify="Q-3 #3: every one of the 8 slot ids fires its own weapon from its own "
                       "point, in both modes; a root that does not fire is recorded as UNKNOWN "
                       "(no entity states which input drives which root)",
                why="the slot row moves off `blocked` on operator ruling 3: JC3's 2 driver slots "
                    "are a convention (the reference vehicles' third weapon is a Bavarium "
                    "shield PART, not a slot), so 8 slots are forced as four `CCar` roots x two "
                    "decoded pointers, with the 5 gadgets carried outside the slot space "
                    "(`tmp/freebuff/reports/wp13-slots-force.md`)")


def row_riot(B, J):
    """WPN-10: no non-lethal carrier exists, so the row takes the closest system (a zero-damage
    impulse round) and names the gap. Operator rule 2026-11-06: a compromise is not accepted
    where a lore-accurate route exists; the report found none, so this is the closest-system
    case, not the rewritten-carrier case."""
    sup = "Batmobile_Cannon_V2"
    o = B.obj(sup)
    fields = []
    for f in (o["fields"] if o else []):
        v = f.get("value")
        if f.get("ref"):
            v = "ref:" + str(f["ref"].get("path"))
        if v not in (None, "", "ref:None") and f["path"].startswith("RBatmobileCannon.Riot"):
            fields.append(f"`{f['path']}` {num(v) if not isinstance(v, str) else v}")
    a = [
        aspect("carrier", f"`RBatmobileCannon (riot fields)` `{sup}`: " + ", ".join(fields[:5])
               + (f" (+{len(fields) - 5} more riot fields)" if len(fields) > 5 else ""),
               "**closest system, not a found non-lethal carrier**: a private bullet-tune copy "
               "with `base_tuning.damage` = 0, `base_tuning.impulse` kept high and "
               "`vehicle_impulse_factor` / `object_impulse_factor`; the only shipped 0-damage "
               "tune is the pulse `gen_explosion_5m_nodamage.ftune` (0/0, 5 m, push only)",
               "no non-lethal property exists - zero damage is not a lethality flag, and damage "
               "is typed on the part, not the weapon", "derived",
               "`tmp/freebuff/reports/non-lethal-cannon-carrier.md` sections 2-4; "
               "`Research/JC3Grab/WEAPONS.md:84-112,425-450`; "
               "`Research/JC3Grab/FORCEPULSE.md` section 3"),
        aspect("mode toggle", "riot is a second mode on the same cannon",
               "no per-weapon mode member: the toggle is a second weapon entity/slot",
               "slot count is T-WP13 (blocked), so the toggle is a BUILD gap", "UNKNOWN", ""),
        aspect("fire rate", f"`RiotSuppressorFiringInterval` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorFiringInterval'))} s vs the lethal "
               f"{num(B.v(sup, 'RVehicleWeapon.FiringInterval'))} s",
               "`fire_rate` (seconds per shot)", "direct", "decoded",
               "`Research/JC3Grab/WEAPONS.md` tuning members"),
        aspect("lock-on cone", f"`RiotSuppressorLockOnAngle` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorLockOnAngle'))} deg",
               "`AngleThresholdNewTarget` / `AngleThresholdCurrentTarget` / "
               "`StickyAimStartAngle`", "which member is the 7.5 deg cone is UNKNOWN", "derived",
               "`Research/JC3Grab/WEAPONS.md:441`"),
        aspect("knock-back", f"`RiotSuppressorVillainImpulse` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorVillainImpulse'))}, "
               f"`ImpactMomentum` {num(B.v(sup, 'RBatmobileCannon.ImpactMomentum'))}",
               "`base_tuning.impulse` + `vehicle_impulse_factor` / `object_impulse_factor`",
               "the factors clamp at 1, so the absolute impulse is the lever; unit UNKNOWN",
               "derived", "`Research/JC3Grab/WEAPONS.md` impulse table"),
        aspect("damage", f"`ChainGunDamage` {num(B.v(sup, 'RBatmobileCannon.ChainGunDamage'))} "
               "(riot mode has no damage number of its own)",
               "`base_tuning.damage` = 0", "a 0-damage *bullet* is unproven; only the pulse ships 0",
               "derived", "`Research/JC3Grab/FORCEPULSE.md` section 3"),
        aspect("effects", "gel `Riot_Suppressor.Anti_firearm_gel_Miss`, tracer, casing",
               "`.effc` assets attached on the weapon-entity side, not tune members",
               "asset only - T-17 owns the effect tables", "decoded", ""),
        aspect("sounds", "`Play_RiotSuppressor_Bolt`, `Play_RiotSupressor_Impacts`",
               "no JC3 weapon sound member for these", "both are missing-object in the grab",
               "decoded", "`Research/BatmobileGrab/WEAPONS.md` resolved/missing refs"),
        aspect("what remains", "operator rule 2026-11-06: compromises are not accepted where a "
               "lore-accurate route exists",
               "the report searched every non-lethal route (stun, taser, shock, tranq, bean-bag, "
               "ragdoll, water cannon, electricity channel) and found none",
               "BUILD card `Research/specs/B-15.md`: one tune copy (damage 0 + impulse) + a "
               "second weapon entity for the toggle", "derived",
               "`tmp/freebuff/reports/non-lethal-cannon-carrier.md` section 6"),
    ]
    return dict(id="T-WP10", code="WPN-10", title="Riot suppressor - closest carrier: zero-damage "
                "impulse round (no non-lethal flag exists)",
                jc3=[], socket="-", part="-", dispo="next",
                now="nothing carries a non-lethal mode: every fleet bullet damages people and "
                    "vehicles",
                proposed="**closest system, not a found non-lethal carrier**: fire a private "
                         "cannon-tune copy with `base_tuning.damage` 0 and the BmAK impulse/cadence "
                         "(0.75 s) plus the gel VFX; the lethal/riot toggle becomes a second "
                         "weapon entity (gap in B-15)",
                aspects=a,
                verify="Q-1: fire the 0-damage copy at a pedestrian and a car; record whether HP "
                       "drops and whether the target is pushed - the one thing the data cannot "
                       "decide",
                why="the 2026-11-06 operator rule forbids accepting a compromise where a "
                    "lore-accurate route exists; the non-lethal report found no stun/taser/"
                    "ragdoll/water/electrical carrier in any decoded tune or module, so the row "
                    "takes the nearest mechanism (0 damage + impulse) and the gap moves to "
                    "`Research/specs/B-15.md` instead of staying a named omission")


def row_winch(B, J):
    """WPN-6: translated row. The anchor object, rope mesh and VFX/SFX are decoded and buildable;
    the pull loop (force, length clamp, reel, release) is not data in JC3 - card B-16."""
    o = "Batmobile_Winch"
    obj = B.obj(o)
    fields = []
    for f in (obj["fields"] if obj else []):
        v = f.get("value")
        if f.get("ref"):
            v = "ref:" + str(f["ref"].get("path"))
        if v not in (None, "", "ref:None"):
            fields.append(f"`{f['path']}` {num(v) if not isinstance(v, str) else v}")
    a = [
        aspect("carrier", f"`RBatmobileWinch` `{o}`: " + ", ".join(fields[:5])
               + (f" (+{len(fields) - 5} more fields)" if len(fields) > 5 else ""),
               "**closest system (entity graph, not a class)**: a `CVehicleCargoBay`-style anchor "
               "object with 7 members (`world`, `enabled`, `enable`, `disable`, `name`, "
               "`name_hash`, `_object_id`) at the `WinchOrigin` socket, plus the "
               "`transport_rope_winch` mesh as the drum",
               "JC3 has no winch class and no winch member: the anchor is an object to add, not a "
               "value to write", "derived",
               "`Research/JC3Grab/TETHER.md` sections 2 and 4; "
               "`tmp/freebuff/reports/winch-and-tether.md` section 6"),
        aspect("anchor", "`WinchOrigin` socket on `Batmobile_Chassis`: relative (286.554, 0, 59.0) "
               "cm, rotation identity; four `HangFromRope_*` sockets at z 460.50 cm on the wheels",
               "`CVehicleCargoBay.world` (4x4 transform; shipped bays use 4 distinct worlds)",
               "the object can carry the transform, but nothing binds a rope to it", "decoded",
               "`Research/BatmobileGrab/SOCKETS_JC3.json` (WinchOrigin); "
               "`Research/JC3Grab/TETHER.md` section 2"),
        aspect("rope geometry", "two `RSimpleRopeComponent`s per package - `ProjectileRope` @0x0A18 "
               "-> `RopeComponent0`, `StubRope` @0x0A10 -> `RopeComponent1`; material "
               "`VFX_Generic.fx_Winch_M_lit_INST` @560, float 3.5 @680, stub float "
               "0.8690145611763 @364 (names UNKNOWN)",
               "`transport_rope_winch` part (part_index 26 on the 4 `v1602_boat_urga_transport` "
               "entities, `Boat_Generic`, no behaviour, 6 model files)",
               "JC3 supplies a static mesh only: no reel, no length, no segment chain", "decoded",
               "`Research/BatmobileGrab/WEAPONS.md:1242-1243,1265-1266`; `TETHER.md` section 4"),
        aspect("length", "function `RestoreOldRopeLengthIfShorter` on `RBatmobileWinch` - a "
               "function, not a member; no length value decoded",
               "no length member in any of the 53 module types or in either attach object",
               "native on both sides", "UNKNOWN", "MODLOG section 87 (class default unreachable)"),
        aspect("force / pull", "18 fields, none decoded as a force; feat bound >= ~2 t "
               "(MODLOG section 86)",
               "no tether/winch force in any table; the only numbers are the damage gate "
               "`grapple_pull_armor` (-1..0) and `grapple_pull_armor_strength` (0..100.0)",
               "the pull loop is code: 0 of 67 part behaviours pulls or reels", "decoded",
               "`Research/JC3Grab/ARMOR_STEP.md:182-183`; `TETHER.md` section 4"),
        aspect("release", "`HolsterWinch` script stub; `WinchPullType` byte (values UNKNOWN)",
               "`CVehicleCargoBay.disable` (empty event on all 12) and "
               "`CGrapplingHookPropData.disable_event` (empty on all 33)",
               "no file wires a release", "decoded", "`TETHER.md` sections 2-3"),
        aspect("trigger", "operator decision 2026-11-05: d-pad RIGHT, replacing Mission Select",
               "`RELEASE_GRAPPLE` (RPADRIGHT / V) and `VEHICLE_RELEASE_GRAPPLE` (LPADDOWN) exist; "
               "no vehicle action calls a winch", "needs a script-side action", "decoded",
               "`Research/JC3Grab/INPUT.md:169,175`; `DRIVE_CARRIERS.md:196`"),
        aspect("what remains", "the winch's own numbers live in the unreachable `BmGame` class "
               "default (`WinchPullType`, length and force are script-side)",
               "the entity-graph half is buildable now (B-05 step, plan in "
               "`Research/specs/B-16.md`); the pull loop, reel and release are a code-level "
               "capability no JC3 file supplies", "BUILD card B-16", "derived",
               "`tmp/freebuff/reports/winch-and-tether.md` sections 6-8"),
    ]
    return dict(id="T-WP6", code="WPN-6",
                title="Power winch - anchor object and drum mesh are buildable; the pull loop is "
                      "code-level (B-16)",
                jc3=[], socket="WinchOrigin", part="winch_door", dispo="blocked",
                now="no winch: nothing on the car pulls, and no JC3 vehicle has a winch member",
                proposed="**translated to the closest system**: add a `CVehicleCargoBay`-style "
                         "anchor at `WinchOrigin` (286.554, 0, 59.0 cm on `Batmobile_Chassis`), the "
                         "`transport_rope_winch` drum mesh and BmAK's two `RSimpleRopeComponent`s; "
                         "the pull loop/reel/release is the code gap in `Research/specs/B-16.md`",
                aspects=a,
                verify="Q-3 #5: fire the winch at a pole - no pull until B-16's loop exists; then "
                       "record whether the cable holds the 6,000 mass car",
                why="the winch is no longer an omission: the entity-graph half is decoded and "
                    "buildable, and the missing half is named exactly - a pull loop with force, "
                    "length clamp and release, which 0 of 53 module types and 0 of 67 part "
                    "behaviours provide (`Research/specs/B-16.md`)")


def row_d3(B, J):
    """D-3 (lethality): the 2026-10-28 'accept JC3 lethality' decision is superseded by the
    2026-11-06 operator rule. The report found no non-lethal carrier, so the row records the
    closest system and the build card that closes the gap."""
    g = J.g2x("WPN-10")
    sup = "Batmobile_Cannon_V2"
    a = [
        aspect("carrier", f"`RBatmobileCannon` riot mode: `RiotSuppressorLockOnAngle` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorLockOnAngle'))}, "
               f"`RiotSuppressorFiringInterval` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorFiringInterval'))}, gel impact "
               f"`{B.v(sup, 'RBatmobileCannon.RiotSuppressorImpactEffect')}`",
               f"**no non-lethal property in the vocabulary** ({g['fact']}); the closest system "
               "is a 0-damage bullet tune + impulse (T-WP10)",
               "no non-lethal property; a 0-damage bullet is unproven", "derived",
               f"G2X WPN-10: {', '.join(g['files'])} (must not contain "
               f"{', '.join(g['must_not'])})"),
        aspect("slot", "the riot mode is a second mode on the same weapon",
               "no per-weapon mode member", "none - no mode to slot", "UNKNOWN", ""),
        aspect("weapon point", "-", "-", "-", "UNKNOWN", ""),
        aspect("fire rate", f"`RiotSuppressorFiringInterval` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorFiringInterval'))} s vs the lethal "
               f"{num(B.v(sup, 'RVehicleWeapon.FiringInterval'))} s", "no non-lethal mode to rate",
               "none", "decoded", "the two rates differ, so the mode is a real behaviour"),
        aspect("damage by effect", "non-lethal rounds stop people, damage vehicles",
               "every JC3 bullet damages both: JC3 lethality accepted (D-3)", "none",
               "UNKNOWN", ""),
        aspect("projectile speed", "-", "-", "-", "UNKNOWN", ""),
        aspect("spread curve", "-", "-", "-", "UNKNOWN", ""),
        aspect("heat / overheat", "-", "-", "-", "UNKNOWN", ""),
        aspect("lock-on", f"`RiotSuppressorLockOnAngle` "
               f"{num(B.v(sup, 'RBatmobileCannon.RiotSuppressorLockOnAngle'))} deg",
               "the AutoAim block has no lethality field", "none", "UNKNOWN", ""),
        aspect("blast / explosion", "-", "-", "-", "UNKNOWN", ""),
        aspect("effects", "gel `Riot_Suppressor.Anti_firearm_gel_Miss`, gel casings, fear-gas "
               "family (G1-16)", "no gel effect path", "T-17 keeps them out", "decoded", ""),
        aspect("sounds", "`Play_RiotSuppressor_Bolt`, `_Impacts`", "no non-lethal event",
               "T-16", "decoded", ""),
        aspect("the answer D-3 asked for", "accept JC3 lethality, no toggle (user, 2026-10-28) - "
               "superseded by the operator rule 2026-11-06",
               "**closest system taken, not a found non-lethal carrier**: the zero-damage impulse "
               "tune; the toggle has no member and becomes a second weapon entity",
               "BUILD gap: `Research/specs/B-15.md`", "derived",
               "`tmp/freebuff/reports/non-lethal-cannon-carrier.md`; operator rule 2026-11-06"),
    ]
    return dict(id="T-WP14", code="D-3",
                title="Lethality - closest carrier: zero-damage impulse round; the toggle is a "
                      "build gap (B-15)",
                jc3=[], socket="-", part="-", dispo="next",
                now="one lethal mode: every fleet bullet damages people and vehicles",
                proposed="**closest system, not a found non-lethal carrier**: `base_tuning.damage` "
                         "0 + `base_tuning.impulse` on a private cannon tune, plus a second weapon "
                         "entity for the riot/lethal toggle (gap `Research/specs/B-15.md`)",
                aspects=a,
                verify="Q-1: 0-damage copy fired at a pedestrian and a car; record HP and "
                       "knock-back - a toggle cannot be tested until B-15's second entity exists",
                why="D-3 resolved 2026-10-28 (accept JC3 lethality, no toggle) is superseded by "
                    "the 2026-11-06 operator rule. No non-lethal flag, stun state or damage type "
                    "exists in any decoded tune or module (proof "
                    "`tmp/freebuff/reports/non-lethal-cannon-carrier.md`), so the row takes the "
                    "closest system - a 0-damage impulse round - and the missing toggle moves to "
                    "BUILD card `Research/specs/B-15.md`")


# --------------------------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------------------------- #
def build_edits(B, J):
    """The numeric edits, re-derived from both sides (never typed)."""
    cannon, vulcan = "w602_mediumtank_canon", "w603_mediumtank_mgun"
    edits = [
        {"row": "T-WP1", "kind": "number", "scope": f"weapon tune clone of `{cannon}`",
         "member": "fire_rate",
         "old": float(J.get(cannon, "fire_rate")),
         "new": float(B.v("Batmobile_Heavy_Cannon_Primary", "RVehicleWeapon.FiringInterval")),
         "conf": "decoded",
         "behaviour": "BmAK fires the 60 mm cannon every FiringInterval seconds; JC3's "
                      "`fire_rate` is the same quantity in the same unit (seconds between shots)",
         "take": "Q-3 #3: six consecutive shots at a wall, timed from the recording; pass = "
                 "2.0 s +-0.15 between rounds",
         "why": "the only unit that converts 1:1 between the engines on this weapon"},
        {"row": "T-WP1", "kind": "number", "scope": f"weapon tune clone of `{cannon}`",
         "member": "velocity",
         "old": float(J.get(cannon, "velocity")),
         "new": round(float(B.v("Batmobile_Heavy_Cannon_Primary_Projectile", "Projectile.Speed"))
                      / 100.0, 3),
         "conf": "derived",
         "behaviour": "the shell leaves the muzzle at 400 m/s (40000 UE units/s at 1 UU = 1 cm, "
                      "the unit `bat_assemble.py` uses for the whole car)",
         "take": "Q-3 #3: time a shell to a wall 40 m away; pass = 0.10 s +-0.02 (400 m/s), and "
                 "the same shell reaches a target at 100 m inside 0.30 s",
         "why": "cm/s -> m/s is exact; whether JC3's `velocity` is m/s is inferred from the "
                "25-id band 360..900, so the class is `derived` and the take can fail it"},
        {"row": "T-WP2", "kind": "number", "scope": f"weapon tune clone of `{vulcan}`",
         "member": "fire_rate",
         "old": float(J.get(vulcan, "fire_rate")),
         "new": float(B.v("Batmobile_Cannon_V2", "RVehicleWeapon.FiringInterval")),
         "conf": "decoded",
         "behaviour": "the Vulcan fires 1/0.138 = 7.25 rounds a second (BmAK FiringInterval)",
         "take": "Q-3 #3: hold the trigger 2 s into a wall; pass = 14 +-1 impacts and no "
                 "overheat (the BmAK heat rate is 0)",
         "why": "same unit; the tank's 0.1 s is 10 rounds/s and would out-fire the BmAK gun"},
    ]
    structural = [
        {"row": "T-WP1", "kind": "entity", "what": "`SWeaponPoint` at `CannonMuzzle`",
         "note": "B-05 places it; the socket is G1-13's, not a typed coordinate"},
        {"row": "T-WP1", "kind": "entity", "what": "root `main_weapon` -> the cannon clone",
         "note": "the medium tank's own binding (G2-11 2d)"},
        {"row": "T-WP2", "kind": "entity",
         "what": "root `id:00568A74` -> the Vulcan clone + `SWeaponPoint` at `ChainGunMuzzle`",
         "note": "the medium tank's second driver slot"},
        {"row": "T-WP3", "kind": "entity",
         "what": "4 `SWeaponPoint`s at the donor's own fire points, parented to the pod parts",
         "note": "G2-12 decoded the 4 positions; T-12 P-14/P-15 are the parts"},
        {"row": "T-WP4", "kind": "entity",
         "what": "`SWeaponPoint` at `BattleModeSpotLight` with the -20 deg pitch + a "
                 "`CForcePulse` copy",
         "note": "the launcher's own `LaunchSocketName`, G2-16's pulse"},
        {"row": "T-WP5", "kind": "entity", "what": "a `CForcePulse` object + its blast tune",
         "note": "no trigger in the files: the row is blocked"},
    ]
    not_numeric = [
        {"row": "T-WP1", "field": "`LethalRadius` 175", "why": "the unit is not in any file "
         "(metres? UE units? a screen radius?) - no bridge"},
        {"row": "T-WP3", "field": "`LockOnRange` 12000", "why": "UU -> 120 m would be exact, but "
         "JC3 has no lock-range member to write it to"},
        {"row": "T-WP3", "field": "`MissileNumberParameter` (salvo count)", "why": "a curve "
         "parameter name; the value is in a curve `WEAPONS.json` does not decode"},
        {"row": "T-WP2", "field": "`ImpactMomentum` 60000 / `RecoilImpulse`", "why": "momentum "
         "and impulse are different quantities in the two engines"},
        {"row": "T-WP1", "field": "`ChargeUpTime` 2.5 s", "why": "no charge member in JC3's 25 "
         "tunes"},
        {"row": "T-WP14", "field": "`RiotSuppressor*` rates", "why": "no non-lethal mode to "
         "write them into"},
    ]
    return {"_comment": "T-11 weapon edits: the values that cross the engine boundary with a "
                        "class and a take that can fail. Nothing here is a damage number - "
                        "damage travels as the 24:2 ratio through T-14's health row.",
            "source": "Working/Translation/T7_WEAPONS.md (generated by Tools/scripts/t7_weapons.py)",
            "card": "T-11",
            "edits": edits, "structural": structural, "not_numeric": not_numeric,
            "counts": {"edits": len(edits), "rows_with_edits": len({e["row"] for e in edits}),
                       "structural": len(structural), "not_numeric": len(not_numeric)}}


def build():
    B, J = Bmak(), Jc3()
    rows = [row_wpn1(B, J), row_wpn2(B, J), row_wpn3(B, J), row_wpn4(B, J), row_wp15(B, J),
            row_wpn5(B, J),
            row_winch(B, J),
            row_wp7(B, J), row_wp8(B, J), row_wp9(B, J),
            row_riot(B, J),
            row_wpn11(B, J), row_wpn12(B, J), row_slots(B, J), row_d3(B, J)]
    edits = build_edits(B, J)

    # BmAK side: the 11 gadget classes as G1-08 counted them
    bmak_classes = [{"name": c["name"], "kind": c["kind"], "objects": c["objects"],
                     "instances": c["instances"], "fields": c["fields"]}
                    for c in B.doc["classes"] if c["kind"] == "gadget"]
    # JC3 side: only the ids this doc uses, with their numbers
    used = sorted({wid for r in rows for wid in r["jc3"] if wid in J.rows})
    jc3_ids = []
    for wid in used:
        s = J.summary(wid)
        jc3_ids.append({"id": wid, "kind": J.rows[wid]["kind"],
                        "entities": J.rows[wid]["entities"],
                        "presets": J.presets(wid),
                        "velocity": s.get("velocity"), "fire_rate": s.get("fire_rate"),
                        "burst_count": s.get("burst_count"), "magazine_size":
                        s.get("magazine_size"), "max_range": s.get("max_range"),
                        "player_damage": J.get(wid, "PlayerDamage"),
                        "player_damage_radius": J.get(wid, "PlayerDamageRadius"),
                        "vehicle_damage_factor": J.get(
                            wid, "bullet_weapon[0].tuning.base_tuning.vehicle_damage_factor")
                        or J.get(wid, "missile_weapon[0].tuning.base_tuning.vehicle_damage_factor"),
                        "scatter": [J.get(wid, f"{'bullet' if J.rows[wid]['kind'] == 'bullet' else 'missile'}_weapon[0].tuning.base_tuning.scatter.scatter_{k}")
                                    for k in ("minimum", "maximum", "per_shot",
                                              "recover_rate", "reset_time")],
                        "direct_damage": J.get(
                            wid, "bullet_weapon[0].tuning.base_tuning.damage") or
                            J.get(wid, "missile_weapon[0].tuning.base_tuning.damage"),
                        "impulse": J.get(
                            wid, "bullet_weapon[0].tuning.base_tuning.impulse") or
                            J.get(wid, "missile_weapon[0].tuning.base_tuning.impulse"),
                        "turning_speed": J.get(
                            wid, "missile_weapon[0].tuning.missile_base_tuning.missile_turning_speed"),
                        "autoaim_members": len(J.autoaim_members(wid)),
                        "autoaim_lock_members": J.autoaim_lock_members(wid),
                        "fire_points": next((len(w["weapons"][0]["points"]) for w in J.wiring
                                             if w["weapons"] and w["weapons"][0]["name"] == wid),
                                            None)})
    doc = {
        "schema": 1,
        "generator": "Tools/scripts/t7_weapons.py",
        "card": "T-11",
        "inputs": {
            "bmak_weapons": "Research/BatmobileGrab/WEAPONS.json (G1-08/G1-09)",
            "bmak_hud": "Research/BatmobileGrab/HUD_INTERFACES.json (G1-08)",
            "sockets": "Research/BatmobileGrab/SOCKETS_JC3.json (G1-13)",
            "jc3_weapons": "Research/JC3Grab/WEAPONS.jsonl (G2-10)",
            "jc3_wiring": "Research/JC3Grab/WEAPON_WIRING.jsonl (G2-11)",
            "jc3_hud": "Research/JC3Grab/JC3_HUD_WEAPONS.json (G2-25)",
            "damage": "Research/JC3Grab/DAMAGE_MODEL.json (G2-28)",
            "emp": "Research/JC3Grab/EMP.json (G2-16)",
            "g2x": "Research/JC3Grab/G2X.json (G2X)",
        },
        "decisions": {
            "D-7": "resolved 2026-10-28: every BmAK weapon in both battle and pursuit modes; "
                   "T-11 answers the slot question in T-WP13",
            "D-3": "resolved 2026-10-28: accept JC3 lethality, no toggle; the riot "
                   "suppressor stays a named omission (T-WP10) and T-WP14 records the decision",
        },
        "bmak_classes": bmak_classes,
        "jc3_ids": jc3_ids,
        "autoaim": {
            "probe_id": "w609_fighterjet_missile_air_lockon",
            "members": len(J.autoaim_members("w609_fighterjet_missile_air_lockon")),
            "lock_members": J.autoaim_lock_members("w609_fighterjet_missile_air_lockon"),
        },
        "slots": {
            "driver": [k for k in J.entity(DONOR_EE)["roots"][0]["slots"]],
            "driver_count_max": max(w["counts"]["driver_slots"] for w in J.wiring),
            "donor_binding": {k: v.get("target") for k, v in
                              J.entity(DONOR_EE)["roots"][0]["slots"].items()},
            "tank_binding": {k: v.get("target") for k, v in
                             J.entity(TANK_EE)["roots"][0]["slots"].items()},
            "armed_entities": len(J.wiring),
            "hud_clips": J.hud["slots"]["count"],
        },
        "rows": rows,
        "edits": edits,
    }
    doc["summary"] = summarise(doc, edits)
    return doc


def summarise(d, edits):
    rows = d["rows"]
    aspects = [a for r in rows for a in r["aspects"]]
    by_class = {}
    for a in aspects:
        by_class[a["class"]] = by_class.get(a["class"], 0) + 1
    return {
        "rows": len(rows),
        "wpn_codes": sum(1 for r in rows if r["code"].startswith("WPN-")),
        "decision_rows": sum(1 for r in rows if not r["code"].startswith("WPN-")),
        "with_carrier": sum(1 for r in rows if r["dispo"] in ("next", "keep", "edit")),
        "omissions": sum(1 for r in rows if r["dispo"] == "out"),
        "blocked": [r["id"] for r in rows if r["dispo"] == "blocked"],
        "aspects": len(aspects),
        "aspects_by_class": dict(sorted(by_class.items())),
        "unknown_aspects": by_class.get("UNKNOWN", 0),
        "edits": edits["counts"]["edits"],
        "structural": edits["counts"]["structural"],
        "not_numeric": edits["counts"]["not_numeric"],
        "bmak_gadget_classes": len(d["bmak_classes"]),
        "jc3_ids_used": len(d["jc3_ids"]),
        "sockets": sorted({r["socket"] for r in rows if r["socket"] not in ("-",)}),
        "driver_slots_max": d["slots"]["driver_count_max"],
    }


# --------------------------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------------------------- #
def render_md(d: dict) -> str:
    s = d["summary"]
    L = ["# Weapons translation (T-11)", "",
         "Generated by `Tools/scripts/t7_weapons.py` from `Research/BatmobileGrab/WEAPONS.json` "
         "(G1-08/G1-09), `SOCKETS_JC3.json` (G1-13), `HUD_INTERFACES.json`, and "
         "`Research/JC3Grab/WEAPONS.jsonl` (G2-10), `WEAPON_WIRING.jsonl` (G2-11), "
         "`JC3_HUD_WEAPONS.json` (G2-25), `DAMAGE_MODEL.json` (G2-28), `EMP.json` (G2-16) and "
         "`G2X.json`. `--check` re-reads all nine, re-derives this file and "
         "`t7_weapons_edits.json`, compares both byte-for-byte and cross-checks `T_ROWS.jsonl`.",
         "",         "One row per WPN code plus one for each decision the card has to answer with a "
         "carrier: `T-WP1`…`T-WP12` for WPN-1…WPN-12, `T-WP15` for WPN-4b (the EMP disable, split "
         "from its launcher by operator ruling 4), `T-WP13` for D-7 (the slot count, forced by "
         "ruling 3) and `T-WP14` for D-3 (resolved: JC3 lethality, no toggle - the named "
         "omission).", "",
         "| item | value |", "|---|---|",
         f"| rows | **{s['rows']}** = {s['wpn_codes']} WPN codes + {s['decision_rows']} decision "
         f"rows |",
         f"| rows with a JC3 carrier | {s['with_carrier']} "
         f"({s['omissions']} named omissions, {len(s['blocked'])} blocked: "
         f"{', '.join(s['blocked'])}) |",
         f"| aspects with a class | **{s['aspects']}** = "
         + ", ".join(f"{k} {v}" for k, v in s["aspects_by_class"].items()) + " |",
         f"| numeric edits | {s['edits']} over the two cloned tunes + {s['structural']} "
         f"structural items + {s['not_numeric']} withdrawn values |",
         f"| BmAK gadget classes | {s['bmak_gadget_classes']} (G1-08's 11) |",
         f"| JC3 weapon ids used | {s['jc3_ids_used']} of the fleet's 25 |",
         f"| sockets used | {', '.join('`%s`' % x for x in s['sockets'])} |",
         f"| driver slots in the fleet | **{s['driver_slots_max']}** |",
         "",
         "## 1. The join between the two sides",
         "",
         "The card's twelve aspects are answered per row in section 3. Only three quantities "
         "bridge exactly between the two engines on this subject; the rest are reported rather "
         "than converted:",
         "",
         "| quantity | BmAK member and unit | JC3 member and unit | bridge |",
         "|---|---|---|---|",
         "| shot interval | `RVehicleWeapon.FiringInterval`, seconds | `fire_rate`, seconds | "
         "**exact 1:1** |",
         "| projectile speed | `Projectile.Speed`, UE units/s (1 UU = 1 cm) | `velocity`, unit "
         "unstated | **/100**, class `derived` |",
         "| rotator | `LaunchRotationOffset`, UE rotator units (65536 = 360 deg) | degrees | "
         "**exact** |",
         "| damage | `Projectile.Damage` against 1200 health | `damage`/blast against a vehicle "
         "health pool | **none** - the ratio is T-14's health row |",
         "| impulse / momentum | `MomentumTransfer`, `ImpactMomentum` | `impulse` | **none** |",
         "| heat | `HeatUpPerSecond` 0.0 (no overheat) | no heat member at all | both absent |",
         "| lock-on | `LockOnAngle`/`LockOnTime`/`LockOnRange` | AutoAim sticky-aim angles only, "
         "HUD POI marker | **none** for time/range |",
         "",
         "### The 11 BmAK gadget classes (G1-08)",
         "",
         "| class | instances | fields |", "|---|---|---|"]
    for c in d["bmak_classes"]:
        L.append(f"| `{c['name']}` | {c['instances']} | {c['fields']} |")
    L += ["", "### The JC3 ids this card uses (G2-10)", "",
          "| id | kind | entities | fire points | velocity | fire_rate s | player damage / "
          "radius | scatter min/max/per-shot | AutoAim preset | lock members |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for j in d["jc3_ids"]:
        sc = "/".join(num(x, 3) for x in j["scatter"]) if any(j["scatter"]) else "-"
        L.append(f"| `{j['id']}` | {j['kind']} | {j['entities']} | "
                 f"{j['fire_points'] if j['fire_points'] is not None else '-'} | "
                 f"{num(j['velocity'], 1)} | {num(j['fire_rate'], 3)} | "
                 f"{num(j['player_damage'])} / {num(j['player_damage_radius'], 1)} m | {sc} | "
                 f"{', '.join('`%s`' % p for p in j['presets']) or '-'} | "
                 f"{j['autoaim_members']} ({len(j['autoaim_lock_members'])} lock) |")
    L += ["",
          "`AutoAim` is a **sticky-aim** block: per shooter context it carries "
          "`AngleThresholdNewTarget`, `StickyAimStrength` and five more angles, and **no lock "
          "duration and no lock range** - so JC3's lock-on lives in the HUD POI (one "
          "`POI_TYPE_LOCK_ON_TARGET`, 1.5 s rotation, 0.5 s `MCI_missile_locked`), not in a "
          "weapon member (G2-25).", "",
          "## 2. The two decisions this card must answer", "",
          "| decision | the question | what the files say | the row |",
          "|---|---|---|---|",
          f"| **D-7** | how do all 11 weapons take JC3's driver slots, in both modes? | the fleet "
          f"has **{d['slots']['driver_count_max']} driver slots** at most (medium and Bavarium "
          f"tank: `main_weapon` + `id:00568A74`); there is no active-slot index, no next/previous "
          f"weapon action and no weapon group anywhere in the 232 `.epe` graphs (G2-11 section "
          f"2b); the HUD has 2 clips (G2-25). BmAK itself has primary + secondary + **3 "
          f"special-weapon states** and a radial wheel (`UC_SelectWheelGadget`) | **T-WP13** - "
          f"blocked: no mechanism carries 11 |",
          f"| **D-3** | lethality: accept JC3 lethality, or keep a non-lethal mode? | no "
          f"non-lethal flag, damage type or weapon mode exists in the 52-type / 1,421-path "
          f"vocabulary (G2X WPN-10); **resolved 2026-10-28 (user): accept JC3 lethality, no "
          f"toggle**, and the riot suppressor stays a named omission | **T-WP14** - out: no "
          f"toggle, decision recorded |",
          "",
          "`T-WP13` is `blocked`, not `out`: D-7's requirement stands and the user's decision "
          "stands, but no decoded member can carry it - that is the outcome D-7 asked T-11 to "
          "look for. `T-WP14` is `out` because D-3 is resolved the other way: the user withdrew "
          "the toggle, so there is no feature left to carry and the row records the decision.",
          "",
          "**What the slots can carry.** The medium tank is the only land vehicle with two "
          "driver weapons, and it binds **w602 to `main_weapon` and w603 to `secondary "
          "(id:00568A74)`** - exactly the cannon + Vulcan pair WPN-1/WPN-2 need. That is the "
          "strongest evidence-based assignment available, and it leaves WPN-3's missiles (the "
          "donor's own `main_weapon` today) without a slot. Anything beyond two weapons has no "
          "carrier in the files.", "",
          "## 3. The rows", "",
          "Cells: the BmAK source with its values, the JC3 carrier, the slot and the weapon "
          "point, the values that cross, what the build carries now, the proposal, and the "
          "class plus the probe that can fail it. Classes are R4's (`decoded`, `decoded "
          "(fleet)`, `derived`, `class`, `read`, `UNKNOWN`).", "",
          "| id | BmAK source | JC3 carrier | slot and weapon point | values | now | proposed | "
          "class and verify |", "|---|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        L.append(row_table_line(r))
    L += ["", "## 4. Every aspect, with its class", ""]
    for r in d["rows"]:
        L.append(f"### {r['id']} — {r['code']} · {r['title']}")
        L.append("")
        L.append(f"- **BmAK object**: {r['aspects'][0]['bmak']}")
        L.append(f"- **JC3 carrier**: {r['aspects'][0]['jc3']}")
        L.append("")
        L.append("| aspect | BmAK | JC3 | transform | class |")
        L.append("|---|---|---|---|---|")
        for a in r["aspects"]:
            L.append(f"| {a['aspect']} | {cell(a['bmak'])} | {cell(a['jc3'])} | "
                     f"{cell(a['transform'])} | **{a['class']}** |")
        notes = [a for a in r["aspects"] if a["note"]]
        if notes:
            L.append("")
            for a in notes:
                L.append(f"- *{a['aspect']}*: {a['note']}")
        L.append("")
        L.append(f"- **verify**: {cell(r['verify'])}")
        L.append("")
    e = d["edits"]
    L += ["## 5. The edit list (`t7_weapons_edits.json`)", "",
          f"{e['counts']['edits']} numeric edits over {e['counts']['rows_with_edits']} rows, "
          f"{e['counts']['structural']} structural items for B-05/B-06 and "
          f"{e['counts']['not_numeric']} values that were looked at and withdrawn.", "",
          "| row | scope | member | old | new | class | take |", "|---|---|---|---|---|---|---|"]
    for x in e["edits"]:
        L.append(f"| `{x['row']}` | {cell(x['scope'])} | `{x['member']}` | {num(x['old'])} | "
                 f"**{num(x['new'])}** | {x['conf']} | {cell(x['take'])} |")
    L += ["", "Structural (entity graph, placed in B-05/B-06 - not module edits):", "",
          "| row | what | note |", "|---|---|---|"]
    for x in e["structural"]:
        L.append(f"| `{x['row']}` | {cell(x['what'])} | {cell(x['note'])} |")
    L += ["", "Withdrawn values (looked at, no bridge, no edit):", "",
          "| row | value | why |", "|---|---|---|"]
    for x in e["not_numeric"]:
        L.append(f"| `{x['row']}` | {cell(x['field'])} | {cell(x['why'])} |")
    L += ["", "## 6. What the files do not give (UNKNOWN)", "",
          f"1. **No lock-on time or range on the JC3 side.** The `AutoAim` block is sticky aim "
          f"(angles and strength per shooter context): {d['autoaim']['members']} member names on "
          f"`{d['autoaim']['probe_id']}`, of which {len(d['autoaim']['lock_members'])} contain "
          f"'lock'. BmAK's `MissileLockOnDuration` and `LockOnRange` are therefore reported, not "
          f"written (T-WP3/T-WP4).",
          "2. **No data-side disable state for the Immobilizer.** `CEMPWeapon` w702/w503 exist "
          "but carry no EMP field, the pulse tune has no duration, target class or disable "
          "member (G2-16), and `is_disabled_by_emp` (exe 0x24EA080) has 0 asset bindings: the "
          "writer is B-18's probe build, not a value.",
          "3. **No trigger for the entity pulse.** 14 of the fleet's 307 `CForcePulse` objects "
          "have no owner pointer and the firing moment is UNKNOWN (G2-17): B-18 (EMP) and B-20 "
          "(sonar) author the trigger; no file supplies one.",
          "4. **No damage ratio for anything the Vulcan shoots.** BmAK gives no soldier, APC or "
          "helicopter health, so WPN-2's damage is the clone's shipped number; only the tank "
          "ratio (1200/50) exists and it belongs to T-14.",
          "5. **No soldier target number.** Q-3 #3 asks for shots-to-kill a soldier; no file on "
          "either side has a soldier health value, so that half of the take is a recording, not "
          "a prediction.",
          "6. **`InaccuracyVsTime` points are not decoded** (the struct is 274 B in "
          "`WEAPONS.json` with `named_by` but no point list). WPN-2's spread row keeps JC3's "
          "numbers and records the shape from G1-23.",
          "7. **JC3's `velocity` unit is not stated** in any decoded file. The /100 bridge is "
          "`derived` and the Q-3 flight-time take is what can fail it.",
          "8. **The tracks and textures of the muzzle flashes** are T-17's rows; this card only "
          "names the effect each weapon rides.",
          "",
          "## 7. Reproduce", "", "```",
          "python Tools/scripts/t7_weapons.py --write   # regenerate T7_WEAPONS.md + "
          "t7_weapons_edits.json",
          "python Tools/scripts/t7_weapons.py --check   # Done-when gate",
          "python Tools/scripts/t7_weapons.py show rows|edits|bmak|jc3",
          "```", "",
          "The rows enter the ledger as doc `T-7` through `Tools/scripts/t_rows.py` "
          "(`DOCS` + `DISPO`); `T_ROWS.jsonl` and `STATUS.md` are regenerated by their own "
          "tools, never edited here.", ""]
    return "\n".join(L)


def row_table_line(r: dict) -> str:
    a = {x["aspect"]: x for x in r["aspects"]}
    carrier = a["carrier"]
    slot = a.get("slot") or a["carrier"]
    point = a.get("weapon point") or a["carrier"]
    rate = a.get("fire rate")
    dmg = a.get("damage by effect")
    values = "; ".join(x for x in [
        f"rate: {rate['transform']}" if rate and rate["class"] != "UNKNOWN"
        and rate["transform"] not in ("-", "none", "keep") else None,
        f"damage: {dmg['transform']}" if dmg and dmg["transform"] not in ("-", "none") else None,
    ] if x)
    classes = []
    for key in ("carrier", "slot", "weapon point", "fire rate", "damage by effect"):
        if key in a and a[key]["class"] not in classes:
            classes.append(a[key]["class"])
    lead = classes[0] if classes else "UNKNOWN"
    return ("| " + " | ".join(cell(x) for x in [
        r["id"], carrier["bmak"], carrier["jc3"], f"{slot['jc3']} · {point['jc3']}",
        values or "-", r.get("now") or "-", r.get("proposed") or "-",
        f"{lead} · {r['verify']}"]) + " |")


# --------------------------------------------------------------------------------------------- #
# invariants
# --------------------------------------------------------------------------------------------- #
def invariants(d: dict) -> list:
    bad = []
    s = d["summary"]
    codes = {r["code"] for r in d["rows"]}
    for n in range(1, 13):
        if f"WPN-{n}" not in codes:
            bad.append(f"WPN-{n} has no row")
    for code in ("D-7", "D-3"):
        if code not in codes:
            bad.append(f"decision {code} has no row")
    if s["rows"] != 15:
        bad.append(f"{s['rows']} rows, expected 15 (12 WPN codes + WPN-4b + D-7 + D-3)")
    ids = [r["id"] for r in d["rows"]]
    if len(ids) != len(set(ids)):
        bad.append("duplicate row ids")
    for r in d["rows"]:
        if r["dispo"] not in ("next", "keep", "out", "blocked", "edit", "epe", "superseded",
                             "re-read"):
            bad.append(f"{r['id']}: bad disposition {r['dispo']}")
        if not r["verify"]:
            bad.append(f"{r['id']}: no verify cell")
        if not r["why"]:
            bad.append(f"{r['id']}: no why")
        for a in r["aspects"]:
            if a["class"] not in CLASSES:
                bad.append(f"{r['id']}: aspect {a['aspect']} class {a['class']}")
            if a["class"] != "UNKNOWN" and not a["bmak"]:
                bad.append(f"{r['id']}: aspect {a['aspect']} has a class but no BmAK side")
        if r["dispo"] == "out" and not any("Research/" in x["why"] for x in [r]):
            bad.append(f"{r['id']}: out row without a proof path")
    # the carrier ids must exist in G2-10 and the sockets in G1-13
    jc3_ids = {j["id"] for j in d["jc3_ids"]}
    for r in d["rows"]:
        for wid in r["jc3"]:
            if wid.startswith("w") and wid not in jc3_ids:
                bad.append(f"{r['id']}: carrier {wid} missing from the JC3 table")
    sockets = {x["socket"] for x in json.load(open(os.path.join(BMAK, "SOCKETS_JC3.json"),
                                                   encoding="utf-8"))["sockets"]}
    for r in d["rows"]:
        for name in [n.strip() for n in r["socket"].split("+")]:
            if name in ("-", "car centre"):
                continue
            if name not in sockets:
                bad.append(f"{r['id']}: socket {name} not in G1-13")
    # edits must name a real JC3 member and a row that exists
    for x in d["edits"]["edits"]:
        if x["row"] not in ids:
            bad.append(f"edit for unknown row {x['row']}")
        wid = x["scope"].split("`")[1]
        member = x["member"]
        rows = [json.loads(line) for line in open(os.path.join(JC3, "WEAPONS.jsonl"),
                                                  encoding="utf-8") if line.strip()]
        flat = {r["id"]: Jc3._flat(r) for r in rows}
        if member not in flat.get(wid, {}):
            bad.append(f"edit {x['row']}: {wid} has no member {member}")
        if abs(float(x["old"]) - float(flat[wid][member])) > 1e-9:
            bad.append(f"edit {x['row']}: old {x['old']} is not {wid}'s {member}")
    return bad


# --------------------------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------------------------- #
def dump_json(d, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=False, ensure_ascii=False)
        f.write("\n")


def cmd_write() -> int:
    d = build()
    bad = invariants(d)
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    md = render_md(d)
    dump_json(d["edits"], OUT_JSON)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    s = d["summary"]
    print(f"T7_WEAPONS.md + t7_weapons_edits.json: {s['rows']} rows "
          f"({s['wpn_codes']} WPN + {s['decision_rows']} decisions), {s['aspects']} aspects "
          f"({s['unknown_aspects']} UNKNOWN), {s['edits']} edits, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: T7_WEAPONS.md / t7_weapons_edits.json missing - run --write")
        return 1
    have = load_json(OUT_JSON)
    d = build()
    bad = invariants(d)
    if have != d["edits"]:
        diff = [k for k in sorted(set(have) | set(d["edits"]))
                if have.get(k) != d["edits"].get(k)]
        bad.append("t7_weapons_edits.json stale: " + ",".join(diff))
    md = render_md(d)
    got = open(OUT_MD, encoding="utf-8").read()
    if md != got:
        ud = list(difflib.unified_diff(got.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(ud[2:8]))
    # the ledger must carry every row with the disposition this doc gives it
    ledger_path = os.path.join(TRANS, "T_ROWS.jsonl")
    if os.path.exists(ledger_path):
        ledger = {json.loads(line)["id"]: json.loads(line)
                  for line in open(ledger_path, encoding="utf-8") if line.strip()}
        for r in d["rows"]:
            row = ledger.get(r["id"])
            if row is None:
                bad.append(f"{r['id']} missing from T_ROWS.jsonl (run t_rows.py build)")
            elif row["dispo"] != r["dispo"]:
                bad.append(f"{r['id']} ledger disposition {row['dispo']} != {r['dispo']}")
    else:
        bad.append("no T_ROWS.jsonl")
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    s = d["summary"]
    print(f"PASS: {s['rows']} rows = {s['wpn_codes']} WPN codes + {s['decision_rows']} decision "
          f"rows ({s['with_carrier']} with a JC3 carrier, {s['omissions']} named omissions, "
          f"{len(s['blocked'])} blocked) | {s['aspects']} aspects classified, "
          f"{s['unknown_aspects']} UNKNOWN | {s['edits']} edits + {s['structural']} structural + "
          f"{s['not_numeric']} withdrawn | {s['jc3_ids_used']} JC3 ids, "
          f"{s['driver_slots_max']} driver slots | ledger 14/14 | json match True, md match True")
    return 0


def cmd_show(what: str) -> int:
    d = build()
    key = {"rows": "rows", "edits": "edits", "bmak": "bmak_classes", "jc3": "jc3_ids"}.get(what)
    if key is None:
        print("one of: rows, edits, bmak, jc3")
        return 2
    print(json.dumps(d[key], indent=1, ensure_ascii=False)[:40000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    sh = sub.add_parser("show")
    sh.add_argument("what", nargs="?", default="rows")
    a = p.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    if a.cmd == "show":
        return cmd_show(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
