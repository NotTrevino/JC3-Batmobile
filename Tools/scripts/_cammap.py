"""CAMMAP: JC3 camera members x BmAK equivalents, evidence-tagged."""
import json, os

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
cam = json.load(open(os.path.join(A, "jc3_cam.json")))

def val(name, occ=0):
    vs = [m["val"] for m in cam if m["name"] == name]
    return vs[occ] if len(vs) > occ else "?"

ROWS = [
 ("CameraPosition/LookAtPoint/RotationPoint", "vec3 refs (offsets 12/36/48)",
  "R3rdPersonCamera states: DrivingCamera / BattleModeCamera (+HeadOffset struct)",
  "state names + BattleModeHeadOffset scraped (GPCD); distances in native serials",
  "[scraped-schema]"),
 ("FollowCameraRange/UpCameraRange/RightCameraRange", "range structs",
  "BattleModeCamera vs DrivingCamera framing (per-state distances)",
  "state names scraped; numeric distances open", "[scraped-schema]"),
 ("FOV (+FOVVelocityRange/FOVZoomAdjustment -5)", val("FOVZoomAdjustment"),
  "FOVFrequency (AkParameterName) + BattleModeCamera zoom fns (ToggleCameraZoom/AllowZoomCamera/SetZoom)",
  "FOVFrequency name scraped; functions scraped (GPCD)", "[scraped-schema]"),
 ("Yaw/Pitch/Roll springs + Drift variants", "0.08/0.12/1.0 (+drift 0.08)",
  "Camera spring params in R3rdPersonCamera states (native serials)",
  "state names scraped; values open", "[scraped-schema]"),
 ("LagCameraRelativity/VelocityScale", "1 / 30",
  "Lag params per camera state (native)", "values open", "[scraped-schema]"),
 ("ReCenterDelay/Speed + MinTimeForHalfTurn", "0 / 0.5 / 2s",
  "Camera recentre per state (native)", "values open", "[scraped-schema]"),
 ("Collision* (fudge/pitch/distance/water)", "pitch cam + water check",
  "Camera collision per state (native)", "values open", "[scraped-schema]"),
 ("CarCameraRef=DrivingCamera (Serpente .epe)", "driving cam ref",
  "R3rdPersonCamera.DrivingCamera state; the epe's SharedCarCamera names the tune",
  "scraped + path proven (car_base.ctune), 8 class tunes decoded", "[proven]"),
 ("Hijack framings (L/R + transitions)", "framing files",
  "KEEP (Batmobile has no hijack cameras; entry is remote-called)",
  "-", "[none]"),
 ("Cockpit view", "no JC3 cockpit cam for cars",
  "Batmobile_V2_Cockpit_Open/Close + Interior views (mesh-side views)",
  "names scraped; views are art not cam objects", "[scraped-schema]"),
 ("Camera shake events", "crash/drift shake via game code",
  "AddCameraShake API + shake params (Scale/PlaySpace); Batmobile shake tuning in native serials",
  "API scraped (GPCD); values open", "[scraped-schema]"),
 ("ListenerHeadRelativity 0.5", val("ListenerHeadRelativity"),
  "Audio listener on camera (shared engine behavior)",
  "same engine role", "[role]"),
]

lines = ["# JC3 Serpente x BmAK Batmobile CAMMAP v1",
         "",
         "Rule: JC3 side fully inventoried (`_cam_inv.py` -> `jc3_cam.json`, 159 members, "
         "car_base.ctunec + all 8 class tunes + Serpente refs). BmAK side = R3rdPersonCamera states + params "
         "[scraped]. Tags as stated.",
         "",
         "| JC3 member | JC3 value | BmAK equivalent | BmAK value | evidence |",
         "|------------|-----------|-----------------|------------|----------|"]
for jm, jv, be, bv, ev in ROWS:
    lines.append("| %s | %s | %s | %s | %s |" % (jm, jv, be, bv, ev))
open(os.path.join(A, "CAMMAP.md"), "w").write("\n".join(lines) + "\n")
json.dump([{"jc3": jm, "jc3val": jv, "bmak": be, "bmakval": bv, "ev": ev} for jm, jv, be, bv, ev in ROWS],
          open(os.path.join(A, "cammap.json"), "w"), indent=1)
print("cammap rows:", len(ROWS))
