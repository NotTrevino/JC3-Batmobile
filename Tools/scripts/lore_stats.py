"""lore_stats.py - convert lore Batmobile stats into JC3 module values, units derived from the game. §72.

Units, each derived from the Serpente's own LIVE modules (patched land_engine, .ee copies of the rest):
  vehicle_misc.official_top_speed     km/h  -- equals the in-game stat screen (250; user-confirmed)
  transmission.top_speed              km/h  -- physics cap: Serpente gearing gives 333 km/h at the 7,000
                                               rpm upshift (0.77 x 3.91, tyre 0.38 m); the cap is 320
  land_engine.torque_factor_at_optimal_rpm  N·m peak torque -- 490 N·m @ 5,000 rpm with the 0.84 falloff
                                               to 7,300 rpm peaks at ~422 hp: a muscle car
  custom_land_global.extra_top_speed  km/h boost -- 250 + 80 = 330 ~ the 320 cap (+32%)
  land_aerodynamics.frontal_area      m²    -- the Serpente body mesh rasterises to 2.25 m² vs field 2.4
                                               (field also covers wheels/bumpers: x1.067)
  land_steering.max_speed_kmph        km/h

Conversions (every factor printed in the report):
  official_top_speed  := lore top speed
  extra_top_speed     := each tier x (afterburner km/h / Serpente's 80 km/h) -- keeps the tier pattern
  transmission.top_speed := lore top speed x (1 + afterburner%)        (cap includes boost)
  final_drive         := gearing that puts the 7,000 rpm upshift in top gear at the cap x (333/320),
                         the Serpente's own drivetrain-over-cap margin, on the TRUE tyre radius
  peak torque         := Serpente torque x (lore bhp / Serpente peak bhp)   (curve shape kept)
  frontal_area        := measured Batmobile body area x 1.067
  drag_coefficient    := solved so top speed ∝ cbrt(P / (Cd·A)) holds against the Serpente
                         calibration (250 km/h, 422 hp, Cd 0.33, 2.4 m²) -- lore gives power and top
                         speed but no Cd, so Cd is the one free parameter
  max_speed_kmph (steering) := scaled by the top-speed ratio
NOT changed: mass (no lore source), suspension (tuned to the unchanged mass), 0-60 (no measurement).

Writes in place at ConvertAdf offset-in-file, every old value asserted, same size.
Usage: python lore_stats.py <lore.json> <stations.json> <live_dir> <out_dir> --batmobile-area M2
"""
import argparse
import json
import math
import os
import shutil
import struct
import xml.etree.ElementTree as ET

PRE = "v0300_car_kensington_sportsmuscle_"


def fields(xml_path):
    """[(name, offset, value)] for every primitive with a file offset, in file order."""
    out = []
    for m in ET.parse(xml_path).getroot().iter("member"):
        if m.get("offset-in-file") and m.get("gbltype") == "Primitive":
            out.append((m.get("name"), int(m.get("offset-in-file"), 16), m.text))
    return out


def get(F, name, i=0):
    return float([v for n, _, v in F if n == name][i])


def gear_list(xml_path):
    """transmission gear ratios: the unnamed floats after `nitrous_gears`, up to the first 0."""
    F = fields(xml_path)
    k = [n for n, _, _ in F].index("nitrous_gears")
    r = []
    for n, _, v in F[k + 1:]:
        if float(v) == 0:
            break
        r.append(float(v))
    return r


class Patch:
    def __init__(self, live, out, module):
        self.src = os.path.join(live, PRE + module + ".vmodc")
        self.dst = os.path.join(out, PRE + module + ".vmodc")
        self.F = fields(self.src.replace(".vmodc", ".xml"))
        self.b = bytearray(open(self.src, "rb").read())
        self.log = []

    def set(self, name, fn, kind="f"):
        hits = [(o, v) for n, o, v in self.F if n == name]
        if not hits:
            raise SystemExit(f"{self.src}: no member {name}")
        for o, v in hits:
            old = struct.unpack_from("<" + kind, self.b, o)[0]
            if abs(old - float(v)) > 1e-3 * max(1, abs(old)):
                raise SystemExit(f"{name} @{o:#x}: file {old} vs xml {v}")
            new = fn(old)
            struct.pack_into("<" + kind, self.b, o, new)
            self.log.append(f"{name} {old:g} -> {new:g}")

    def write(self):
        open(self.dst, "wb").write(bytes(self.b))
        return self.log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lore")
    ap.add_argument("stations")
    ap.add_argument("live")
    ap.add_argument("out")
    ap.add_argument("--batmobile-area", type=float, required=True, help="rasterised body frontal area, m²")
    ap.add_argument("--serpente-area-mesh", type=float, default=2.25)
    a = ap.parse_args()
    L = json.load(open(a.lore))
    S = json.load(open(a.stations))
    os.makedirs(a.out, exist_ok=True)
    x = lambda m: os.path.join(a.live, PRE + m + ".xml")

    eng, trn, msc = fields(x("land_engine")), fields(x("transmission")), fields(x("vehicle_misc"))
    aer, clg, ste = fields(x("land_aerodynamics")), fields(x("custom_land_global")), fields(x("land_steering"))
    gears = gear_list(x("transmission"))
    up_rpm = 7000.0                                   # transmission upshift rpm (all gears)
    r_old, fd_old, g_top = 0.38, get(trn, "final_drive"), gears[-1]
    r_new = sum(c["radius"] for c in S["corners"].values()) / 4

    # ---- Serpente calibration
    v_off_s, cap_s = get(msc, "official_top_speed"), get(trn, "top_speed")
    T_s, opt, mx = get(eng, "torque_factor_at_optimal_rpm"), get(eng, "optimal_rpm"), get(eng, "max_rpm")
    f_max = get(eng, "torque_factor_at_max_rpm")
    P_s = max(T_s * (1 - (1 - f_max) * (r - opt) / (mx - opt)) * r * math.pi / 30 for r in range(int(opt), int(mx) + 1, 10))
    hp_s = P_s / 745.7
    drive_s = up_rpm / 60 * 2 * math.pi * r_old / (g_top * fd_old) * 3.6
    margin = drive_s / cap_s
    boost_s = [get(clg, "extra_top_speed", i) for i in range(3)]
    Cd_s, A_s = get(aer, "drag_coefficient"), get(aer, "frontal_area")

    # ---- Batmobile targets
    v_off = L["top_speed_kmh"]
    ab = L["afterburner_pct"] / 100.0
    cap = v_off * (1 + ab)
    fd = up_rpm / 60 * 2 * math.pi * r_new / (g_top * cap * margin / 3.6)
    torque = T_s * L["power_bhp"] / hp_s
    A = a.batmobile_area * A_s / a.serpente_area_mesh
    P_ratio = L["power_bhp"] / hp_s
    Cd = Cd_s * A_s / A * P_ratio / (v_off / v_off_s) ** 3
    boost_scale = ab * v_off / boost_s[0]          # absolute km/h: +30% of 336 = +101 vs the Serpente's +80
    steer_scale = v_off / v_off_s

    print("Serpente calibration: peak %.0f hp, drivetrain %.0f km/h vs cap %.0f (margin %.3f), "
          "boost %s = +%.0f%%" % (hp_s, drive_s, cap_s, margin, boost_s, 100 * boost_s[0] / v_off_s))
    print("Batmobile: tyre r %.4f m, cap %.1f km/h, final drive %.4f (was %.2f), torque %.0f N·m "
          "(x%.3f), area %.2f m², Cd %.4f (was %.2f)" % (r_new, cap, fd, fd_old, torque, P_ratio, A, Cd, Cd_s))
    check = (v_off_s ** 3 * P_ratio * (Cd_s * A_s) / (Cd * A)) ** (1 / 3)
    print("  check: model top speed %.1f km/h (target %.1f)" % (check, v_off))

    report = []
    p = Patch(a.live, a.out, "vehicle_misc"); p.set("official_top_speed", lambda o: v_off); report += p.write()
    p = Patch(a.live, a.out, "transmission")
    p.set("top_speed", lambda o: cap); p.set("final_drive", lambda o: fd); report += p.write()
    p = Patch(a.live, a.out, "land_engine"); p.set("torque_factor_at_optimal_rpm", lambda o: torque); report += p.write()
    p = Patch(a.live, a.out, "custom_land_global"); p.set("extra_top_speed", lambda o: o * boost_scale); report += p.write()
    p = Patch(a.live, a.out, "land_aerodynamics")
    p.set("frontal_area", lambda o: A); p.set("drag_coefficient", lambda o: Cd); report += p.write()
    p = Patch(a.live, a.out, "land_steering"); p.set("max_speed_kmph", lambda o: o * steer_scale); report += p.write()
    for line in report:
        print("  " + line)
    json.dump({"lore": L, "derived": {"cap_kmh": cap, "final_drive": fd, "torque_nm": torque,
                                      "frontal_area_m2": A, "drag_coefficient": Cd,
                                      "serpente_peak_hp": hp_s, "drivetrain_margin": margin},
               "edits": report}, open(os.path.join(a.out, "lore_stats_report.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
