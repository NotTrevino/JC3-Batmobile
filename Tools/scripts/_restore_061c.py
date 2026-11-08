"""Restore variant: TrueScale body+wheels (+mshswap diet dupes, 062-pattern)."""
import os
import shutil

R = r"E:\Modding\JustCause3\JC3-Batmobile"
src59 = os.path.join(R, "Builds", "test-059", "aaf")
dst = os.path.join(R, "Builds", "test-061")
m = os.path.join("models", "jc_vehicles", "01_land", "v0300_car_kensington_sportsmuscle")
ts = os.path.join(R, "Working", "TrueScale")
if os.path.exists(dst):
    import shutil as _s
    _s.rmtree(dst)
shutil.copytree(os.path.join(R, "Builds", "test-059", "aaf"), os.path.join(dst, "aaf"))
n = 0
for i in range(1, 6):
    shutil.copy(os.path.join(ts, "body_lod%d.rbm" % i),
                os.path.join(dst, "aaf", m, "sportsmuscle_body_lod%d.rbm" % i))
    n += 1
for corner in ["f_l", "f_r", "r_l", "r_r"]:
    for lod in range(1, 6):
        sp = os.path.join(ts, "wheel_%s_lod%d.rbm" % (corner, lod))
        if not os.path.exists(sp):
            continue
        shutil.copy(sp, os.path.join(dst, "aaf", m, "sportsmuscle_wheel_%s_lod%d.rbm" % (corner, lod)))
        n += 1
        # mshswap <- same diet bytes (062 pattern), where vanilla has the slot
        ms = os.path.join(dst, "aaf", m, "sportsmuscle_wheel_%smshswap_lod%d.rbm" % (corner, lod))
        if os.path.exists(ms):
            shutil.copy(sp, ms)
            n += 1
# lore modules + patched land_global
mod = os.path.join(dst, "aaf", "editor", "entities", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle", "modules", "default")
shutil.copy(os.path.join(R, "Working", "Movement", "live",
                         "v0300_car_kensington_sportsmuscle_land_global.vmodc"), mod)
for mm in ["custom_land_global", "land_aerodynamics", "land_engine", "land_steering",
           "transmission", "vehicle_misc"]:
    shutil.copy(os.path.join(R, "Working", "Movement", "out",
                             "v0300_car_kensington_sportsmuscle_%s.vmodc" % mm), mod)
    n += 1
print("files placed:", n)
