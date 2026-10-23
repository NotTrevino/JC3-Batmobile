import hashlib
import os
import re


def H(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]


b059 = "E:/Modding/JC3-Batmobile/Builds/test-059/aaf"
b062 = "E:/Modding/JC3-Batmobile/Builds/test-062/aaf"
x59 = open(b059 + "/@files.xml", encoding="utf-8").read()
x62 = open(b062 + "/@files.xml", encoding="utf-8").read()
pat = re.compile(r'name="([^"]+)"')
f59 = set(pat.findall(x59))
f62 = set(pat.findall(x62))
print("files59:", len(f59), "files62:", len(f62))
added = sorted(f62 - f59)
removed = sorted(f59 - f62)
print("added:", len(added))
for a in added[:25]:
    print("  +", a)
print("removed:", len(removed))
for a in removed[:25]:
    print("  -", a)
pal = "/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc"
for t, r in [("059", b059), ("062", b062)]:
    p = r + pal
    print(t, "palette", os.path.getsize(p), H(p))
m62 = b062 + "/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm"
print("062 body_lod1:", os.path.getsize(m62), H(m62))
for q in ["E:/Modding/JC3-Batmobile/Working/Assembled/body_lod1.rbm",
          "E:/Modding/JC3-Batmobile/Working/TrueScale/body_lod1.rbm",
          "E:/Modding/JC3-Batmobile/Builds/test-059/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm"]:
    print("  ", q.split("/")[-2], os.path.getsize(q), H(q))
