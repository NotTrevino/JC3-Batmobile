import json

BODY_KEEP = ["Mainbody", "WheelArchs", "Undercarriage", "Glass", "Emissive",
             "Body_Decals", "Upgrades", "Worn", "Turret", "Cockpit",
             "Cockpit_Seat", "Battery", "Power_Cell"]
BODY_EXCLUDE = ["Wheel_V2", "Tyre", "Discbreak", "Master_Flip"]
# Discbreak faces belong to the wheel spec (same position, drawn once); the flip
# metadata is not geometry. Cockpit/seats/batteries/turret join the body shell.
# NOTE: wheel mats (Wheel_V2/Tyre) excluded -> wheels; Cockpit_Master_Flip_Data
# (100 faces of metadata) excluded. Discbreak included harmlessly (its faces
# live at the wheels; same reasoning as before — positions decide, names don't).
BUDGETS = {1: 20000, 2: 8000, 3: 3000, 4: 1500, 5: 800}
for i, t in BUDGETS.items():
    s = {"pskx": "Playable_Batmobile_SF/SkeletalMesh3/Batmobile_V2.pskx",
         "keep": BODY_KEEP, "exclude": BODY_EXCLUDE,
         "split": None, "components": None,
         "fit": {"mode": "length",
                 "to": "Builds/test-003/aaf/models/jc_vehicles/01_land/"
                       "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod5.rbm"},
         "template": {"rbm": "Builds/test-003/aaf/models/jc_vehicles/01_land/"
                             "v0300_car_kensington_sportsmuscle/sportsmuscle_body_lod1.rbm",
                      "block": 6, "writer": "deform"},
         "plain": True, "tris": t,
         "obj": "Working/Batmobile/full_plain_lod%d.obj" % i,
         "out": "Working/Batmobile/full_plain_lod%d.rbm" % i}
    json.dump(s, open("Working/Batmobile/specs/body_full_lod%d.json" % i, "w"), indent=1)

wheel = json.load(open("Working/Batmobile/specs/wheel.json"))
wheel["expect"] = {"bytes-of": "Working/Batmobile/bat_wheel_2k5.rbm",
                   "out": "Working/Batmobile/bat_wheel_2k5.rbm"}
wheel["out"] = "Working/Batmobile/check_wheel.rbm"
wheel["obj"] = "Working/Batmobile/check_wheel.obj"
json.dump(wheel, open("Working/Batmobile/specs/wheel.json", "w"), indent=1)

for i in BUDGETS:
    p = "Working/Batmobile/specs/body_plain_lod%d.json" % i
    s = json.load(open(p))
    s["expect"] = {"bytes-of": "Working/Batmobile/lod/plain_lod%d.rbm" % i,
                   "out": s["out"]}
    json.dump(s, open(p, "w"), indent=1)
print("specs: 1 wheel + 5 plain (regression) + 5 full (new)")
