import json

BUDGETS = {1: 20000, 2: 8000, 3: 3000, 4: 1500, 5: 800}
for i, t in BUDGETS.items():
    s = {"pskx": "Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx",
         "keep": ["Mainbody", "WheelArchs", "Undercarriage", "Glass",
                  "Emissive", "Body_Decals", "Upgrades", "Worn"],
         "split": None, "components": None,
         "fit": {"mode": "length",
                 "to": "Builds/test-003/aaf/models/jc_vehicles/01_land/"
                       "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod5.rbm"},
         "template": {"rbm": "Builds/test-003/aaf/models/jc_vehicles/01_land/"
                             "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm",
                      "block": 6, "writer": "deform"},
         "plain": True, "tris": t,
         "obj": "Working/Batmobile/import_plain_lod%d.obj" % i,
         "out": "Working/Batmobile/import_plain_lod%d.rbm" % i}
    json.dump(s, open("Working/Batmobile/specs/body_plain_lod%d.json" % i, "w"), indent=1)
print("5 specs written")
