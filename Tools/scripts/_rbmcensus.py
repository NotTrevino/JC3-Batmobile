import hashlib
import os

def H(p):
    try:
        return os.path.getsize(p), hashlib.sha256(open(p, "rb").read()).hexdigest()[:10]
    except Exception:
        return None


b059 = "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-059/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
b062 = "E:/Modding/JustCause3/JC3-Batmobile/Builds/test-062/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
ts = "E:/Modding/JustCause3/JC3-Batmobile/Working/TrueScale/"
am = "E:/Modding/JustCause3/JC3-Batmobile/Working/Assembled/"
files = ["sportsmuscle_body_lod%d.rbm" % i for i in range(1, 6)]
files += ["sportsmuscle_wheel_f_l_lod%d.rbm" % i for i in range(1, 6)]
files += ["sportsmuscle_wheel_f_r_lod1.rbm", "sportsmuscle_engine_lod1.rbm",
          "sportsmuscle_door_l_lod1.rbm", "sportsmuscle_chassis_lod1.rbm"]
for f in files:
    r059 = H(b059 + f)
    r062 = H(b062 + f)
    base = f.replace("sportsmuscle_body_lod", "body_lod").replace("sportsmuscle_wheel_f_l_lod", "wheel_f_l_lod").replace("sportsmuscle_wheel_f_r_lod", "wheel_f_r_lod").replace("sportsmuscle_", "")
    rts = H(ts + base) if os.path.exists(ts + base) else None
    ram = H(am + base) if os.path.exists(am + base) else None
    flag = ""
    if r059 and r062 and r059 == r062:
        flag = "SAME59/62"
    print("%-34s 059=%s 062=%s TS=%s AM=%s %s" % (f, r059, r062, rts, ram, flag))
