"""grab_footage_gaps.py - what the files answer, what the footage measures (G1-23).

The card: for each `UNKNOWN`/`native` value left by G1-08, G1-14 and G1-21, measure it from
Arkham Knight gameplay or footage - source file name + timestamp, frame count at a known fps,
at least three samples - or let it stay `UNKNOWN` **with the reason**. Stop rule (R4): a file
value always beats footage; footage never overrides it.

Two corrections of 2026-10-26 changed the answer this tool records:

  * **Vulcan heat.** `RBatmobileCannon.HeatUpPerSecond` ships **0.0**: no per-second heat is
    configured, so nothing in the object adds heat with time. Whether a per-shot input exists in
    native code is not excluded by the grab - the observed "fires forever" is the user's note,
    the mechanism is UNKNOWN. The bloom the player sees is *time*-based -
    `InaccuracyVsTime` (decoded points: 0 s/0.0, 0.5 s/0.0, 1.5 s/1.5, 2.5 s/3.0, linear)
    on top of `InaccuracyAngle` 0.1 - and `(InaccuracyVsHeat)` matches no field because heat
    never rises. Both rows are therefore **file-answered**, not footage gaps.
  * **Air control.** The Batmobile *does* leave the ground - ramps (`Actor.bIsVehicleJumpRamp`)
    and ledges - and `RVehicleBatmobileBase` carries `bUsedAirControlDuringJump`,
    `JumpRampUpwardForce` and `JumpRampRightingTorque`. The earlier `UNREACHABLE` reason was
    wrong. The captures in `C:\\Users\\User\\Videos\\Captures` show three ramp jumps with
    up/down/right steer, and the air time is measured here.

The five captures live outside the project and are **never copied in** (they are game footage).
The tool reads their timing with `ffprobe` and computes every sample from presentation
timestamps, because the captures are variable-framerate: nominal 60 fps, ~30 fps of unique
frames. Frame counts are therefore reported next to the PTS span that produced them.

Reason codes:
    FILE-VALUE    the machine sources answer it; no footage is used (R4)
    MEASURED      closed by footage in this record, >= 3 samples
    NOT-IN-CLIP   measurable in principle, but the event is not in the available clips
    VALUE-NATIVE  a native/engine parameter with no on-screen unit; behaviour is observable,
                  the number is not
    UNDOCUMENTED  the value exists but its unit is unnamed; no clip in the set disambiguates it
    WRONG-SCOPE   a declared field another card owns (the camera family)
    NATIVE        the deciding code lives in the executable, not in the grab

Usage:
    python Tools/scripts/grab_footage_gaps.py --write
    python Tools/scripts/grab_footage_gaps.py --check
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
OBJECTS = os.path.join(OUT, "objects.jsonl")
WEAPONS = os.path.join(OUT, "WEAPONS.json")
OFFSETS = os.path.join(OUT, "OFFSETS.json")
MODES = os.path.join(OUT, "MODES.json")
DAMAGE_MD = os.path.join(OUT, "DAMAGE_RULES.md")

SCHEMA = 2
GENERATOR = "grab_footage_gaps.py"
DECISION = ("2026-10-26 - user corrections: `HeatUpPerSecond` 0.0 is the answer (no overheat, "
            "bloom is time-based), and the Batmobile does go airborne off ramps and ledges, so "
            "the air-control rows are reachable; captures in C:\\Users\\User\\Videos\\Captures")

REASONS = {
    "FILE-VALUE": "the machine sources answer it; no footage is used (R4)",
    "MEASURED": "closed by footage in this record, >= 3 samples",
    "NOT-IN-CLIP": "measurable in principle, but the event is not in the available clips",
    "VALUE-NATIVE": "a native/engine parameter with no on-screen unit; behaviour is observable, "
                    "the number is not",
    "UNDOCUMENTED": "the value exists but its unit is unnamed; no clip in the set disambiguates it",
    "WRONG-SCOPE": "a declared field another card owns (camera family, T-CAM rows); listed so the "
                   "`BattleMode*` prefix is complete, not measured here",
    "NATIVE": "the deciding code is native to the executable, not in the grab "
              "(`DAMAGE_RULES.md` - only footage could show the behaviour)",
}

VIDEO_EXT = (".mp4", ".webm", ".mkv", ".avi", ".m4v", ".mov")

# The gameplay captures.  Outside the workspace on purpose: never copied into the repo.
CAPTURES = r"C:\Users\User\Videos\Captures"
SOURCES = [
    {"file": "Batman\u2122_ Arkham Knight Air steer up 2-5s.mp4", "kind": "air",
     "role": "ramp jump, pitch up", "air": (3.200, 4.467)},
    {"file": "Batman\u2122_ Arkham Knight Air steer down 2-5s.mp4", "kind": "air",
     "role": "ramp jump, pitch down", "air": (3.300, 4.467)},
    {"file": "Batman\u2122_ Arkham Knight Air steer right 3-6s.mp4", "kind": "air",
     "role": "ramp jump, yaw right", "air": (5.000, 6.200)},
    {"file": "Batman\u2122_ Arkham Knight VulcanFire_10s-15s.mp4", "kind": "vulcan",
     "role": "battle mode, lock and Vulcan fire"},
    {"file": "Batman\u2122_ Arkham Knight Battlemode entry_6-20s. Movement 20-29s Boost "
             "30-38s.mp4", "kind": "battlemode",
     "role": "battle-mode entry, movement and boost"},
]

# The Vulcan capture frames the reticle and the lock, not the muzzle: the fire interval is a
# file value (`ComboFiringInterval` 0.138 s) and is not claimed from footage (R4).
VULCAN_OUT_OF_FRAME = ("the lock reticle and the target are in frame and the muzzle is not, "
                       "so no fire interval is claimed from the capture - "
                       "`ComboFiringInterval` 0.138 s stays a file value (R4)")

# G1-14's native entry points that are not footage gaps. Each is a gate or a setter (or a
# return value with no file default), so there is no observable quantity to measure; the note
# lists them so "every UNKNOWN/native" is accounted for instead of silently dropped.
NATIVE_UNTRACED = {
    "CanBatmobileDoImpactDamage":
        "native gate that `CalculateAndStoreImpactDamage` does not reference (DAMAGE_RULES.md \u00a73.3) - "
        "whether an impact is allowed at all is decided elsewhere, and there is no number to measure",
    "GetDamageMod":
        "native encounter multiplier read by `TakeDamage` (DAMAGE_RULES.md \u00a73.1 step 3) - "
        "`ARM-2`'s hits-to-kill depends on its return value, which is not in the grab and no "
        "tank shell lands on the car in the captures: UNKNOWN",
    "SetArmouredMode":
        "native setter - switches the armoured-mode flag; the number it enables is "
        "`ArmourModeDamageReduction`, already a G1-21 row",
    "SetDamageLevel":
        "native setter - stores the damage level the caller computed; it carries no value of its own",
}

KNOWN_NON_AK = {
    "Working/Camera/shots/cam1_take1.mkv":
        "Just Cause 3 camera-probe take, 1280x720 30 fps 90.17 s - frame-verified as the "
        "Just Cause 3 main menu, not Arkham Knight gameplay",
}
TOOLTIP_DIR = "Autodesk 3ds Max"

# Frame-snapping tolerance: the recorded boundary is a visual call, snapped to the nearest
# frame; more than this and the clip no longer matches the record.
SNAP_S = 0.05


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe_frames(path):
    """[(index, pts)] for every decoded video frame, in presentation order."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "frame=pts_time", "-of", "csv=p=0", path])
    out = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(float(line))
        except ValueError:
            continue
    return out


def probe_stream(path):
    """Container-level facts only (no full decode): geometry, nominal rate, frame count."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
             "-show_entries", "format=duration", "-of", "json", path])
    doc = json.loads(r.stdout or "{}")
    st = (doc.get("streams") or [{}])[0]
    return {"width": st.get("width"), "height": st.get("height"),
            "r_frame_rate": st.get("r_frame_rate"),
            "frames": int(st["nb_frames"]) if st.get("nb_frames") else None,
            "duration": float(doc["format"]["duration"]) if doc.get("format") else None}


def video_scan():
    """(arkham candidates, known non-AK, tooltip clips) under the project root."""
    ak, known, tooltips = [], [], []
    for base, _dirs, names in os.walk(ROOT):
        for n in names:
            if not n.lower().endswith(VIDEO_EXT):
                continue
            rel = os.path.relpath(os.path.join(base, n), ROOT).replace(os.sep, "/")
            if TOOLTIP_DIR in rel:
                tooltips.append(rel)
            elif rel in KNOWN_NON_AK:
                known.append(rel)
            else:
                ak.append(rel)
    return ak, known, tooltips


def weapon_field_values(weapons):
    """{(object key, field path): value} plus a path-only shortlist."""
    out = {}
    for o in weapons.get("objects", []):
        for f in o.get("fields") or []:
            out[(o["key"], f["path"])] = f.get("value")
            out.setdefault(f["path"], f.get("value"))
    return out


def first_value(values, path):
    """First non-None value for a path, across every object that carries it."""
    if values.get(path) is not None:
        return values.get(path)
    for k, v in values.items():
        if isinstance(k, tuple) and len(k) == 2 and k[1] == path and v is not None:
            return v
    return None


def field_array(weapons, path):
    """(decoded points, declared count) for the first array tag at a path."""
    for o in weapons.get("objects", []):
        for f in o.get("fields") or []:
            if f["path"] != path and not f["path"].startswith(path + "."):
                continue
            arr = f.get("array")
            if not arr:
                continue
            pts = []
            for item in arr.get("items") or []:
                vals = [x.get("value") for x in item if x.get("type") == "FloatProperty"]
                if len(vals) >= 2:
                    pts.append([vals[0], vals[1]])
            return pts or None, arr.get("count")
    return None, None


def curve_points(weapons):
    """{object key: [(in, out), ...]} for InaccuracyVsTime, read from the decoded arrays."""
    out = {}
    for o in weapons.get("objects", []):
        for f in o.get("fields") or []:
            if f["path"] != "InaccuracyVsTime.Points" or not f.get("array"):
                continue
            pts = []
            for item in f["array"]["items"]:
                vals = [x.get("value") for x in item if x.get("type") == "FloatProperty"]
                if len(vals) >= 2:
                    pts.append((vals[0], vals[1]))
            if pts:
                out[o["key"]] = pts
    return out


def air_samples():
    """Measure each ramp jump: frames between the first airborne frame and first contact."""
    samples = []
    for s in SOURCES:
        if s["kind"] != "air":
            continue
        path = os.path.join(CAPTURES, s["file"])
        pts = probe_frames(path)
        if not pts:
            samples.append({"clip": s["file"], "missing": True})
            continue
        t0, t1 = s["air"]
        i0 = min(range(len(pts)), key=lambda i: abs(pts[i] - t0))
        i1 = min(range(len(pts)), key=lambda i: abs(pts[i] - t1))
        samples.append({
            "clip": s["file"], "role": s["role"],
            "start_visual_s": t0, "end_visual_s": t1,
            "first_air_frame": i0, "first_air_pts": round(pts[i0], 4),
            "first_contact_frame": i1, "first_contact_pts": round(pts[i1], 4),
            "snap_error_s": max(abs(pts[i0] - t0), abs(pts[i1] - t1)),
            "frames_airborne": i1 - i0 + 1,
            "air_time_s": round(pts[i1] - pts[i0], 4),
            "nominal_60fps_frames": round((pts[i1] - pts[i0]) * 60, 1),
            "frames_total": len(pts),
            "missing": False,
        })
    return samples


def build():
    weapons = json.load(open(WEAPONS, encoding="utf-8"))
    offsets = json.load(open(OFFSETS, encoding="utf-8"))
    modes = json.load(open(MODES, encoding="utf-8"))
    rows_objects = [json.loads(l) for l in open(OBJECTS, encoding="utf-8") if l.strip()]
    values = weapon_field_values(weapons)
    curves = curve_points(weapons)

    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    rows = []

    def add(gap, card, source, file_side, code, note="", status=None, samples=None):
        rid = "F-%d" % (len(rows) + 1)
        rows.append({"id": rid, "gap": gap, "card": card, "source": source,
                     "file_side": file_side,
                     "status": status or ("MEASURED" if code == "MEASURED" else
                                          ("RESOLVED" if code == "FILE-VALUE" else "UNKNOWN")),
                     "reason_code": code, "reason": REASONS[code],
                     "note": note, "samples": samples or []})
        return rid

    # ---- 0. sources ---------------------------------------------------------
    source_rows = []
    for s in SOURCES:
        path = os.path.join(CAPTURES, s["file"])
        exists = os.path.isfile(path)
        info = probe_stream(path) if exists else {}
        source_rows.append({"file": s["file"], "kind": s["kind"], "role": s["role"],
                            "path": path, "exists": exists, "bytes": os.path.getsize(path)
                            if exists else None, "frames": info.get("frames") or 0,
                            "duration_s": round(info["duration"], 3) if info.get("duration")
                            else None,
                            "width": info.get("width"), "height": info.get("height"),
                            "nominal_fps": info.get("r_frame_rate")})
    check("all five Arkham Knight captures are present at the recorded path",
          all(r["exists"] for r in source_rows),
          "%d/%d present" % (sum(1 for r in source_rows if r["exists"]), len(source_rows)))
    check("every capture is 1920x1080 (the recorded geometry)",
          all(r["width"] == 1920 and r["height"] == 1080 for r in source_rows),
          sorted({"%sx%s" % (r["width"], r["height"]) for r in source_rows}))
    check("the captures are nominal 60 fps but variable-framerate (why PTS is used)",
          all(r["nominal_fps"] in ("60/1", "60000/1001") for r in source_rows)
          and all(r["duration_s"] and r["frames"] / r["duration_s"] < 45
                  for r in source_rows),
          ", ".join("%d frames / %.1fs" % (r["frames"], r["duration_s"])
                    for r in source_rows if r["duration_s"]))

    # ---- 1. the card's quantities the files already answer ------------------
    answered = []
    for q in weapons.get("field_index", []):
        if not q.get("matches"):
            continue
        # The card's example: take the first matched field that actually carries a decoded
        # value (a field whose contents are not decoded is not an answer), so the note never
        # prints "20 answered" over rows that show no number. If no matched field decodes, the
        # row keeps the first match and is marked as evidence-less-but-not-a-gap.
        paths = [p for p in (q.get("fields") or []) if p]
        path, example, array_points, array_count = (paths[0] if paths else None), None, None, None
        for cand in paths:
            pts, cnt = field_array(weapons, cand)
            val = first_value(values, cand)
            if pts or val is not None:
                path, example, array_points, array_count = cand, val, pts, cnt
                break
        if path and example is None and array_points is None:
            _pts, array_count = field_array(weapons, path)
        answered.append({"quantity": q["quantity"], "pattern": q["pattern"],
                         "matches": q["matches"], "example_field": path,
                         "example_value": example, "array_points": array_points,
                         "array_count": array_count,
                         "decoded": bool(example is not None or array_points)})

    # ---- 2. weapons and damage ---------------------------------------------
    zero = {q["quantity"]: q for q in weapons.get("field_index", []) if not q.get("matches")}
    check("WEAPONS.json still reports exactly the two zero quantities",
          set(zero) == {"projectile lifetime", "inaccuracy-vs-heat"}, sorted(zero))

    add("projectile lifetime (flight time from muzzle to impact)",
        "G1-08 / G1-09", "WEAPONS.json field_index",
        "`(LifeSpan|Lifetime)` matches **%d** fields across the 62 weapon objects - no projectile "
        "carries a lifetime; WEAPONS.md \u00a74 records the absence per projectile and claims no "
        "class default" % zero["projectile lifetime"]["matches"],
        "NOT-IN-CLIP",
        "the Vulcan capture's impacts are distant and no projectile is in frame")

    # inaccuracy-vs-heat: the files answer it, because heat never rises.
    heat = values.get("RBatmobileCannon.HeatUpPerSecond")
    over = values.get("RBatmobileCannon.OverheatOffValue")
    angle = values.get("RBatmobileCannon.InaccuracyAngle")
    base_curve = curves.get("Playable_Batmobile_SF.Batmobile_Cannon_V2") or []
    check("HeatUpPerSecond still ships 0.0 across the cannon objects",
          heat == 0.0 and sum(1 for k, v in values.items()
                              if isinstance(k, str) and k.endswith("HeatUpPerSecond")
                              and v == 0.0) >= 1, repr(heat))
    check("the InaccuracyVsTime curve is decoded and matches the recorded points",
          base_curve == [(0.0, 0.0), (0.5, 0.0), (1.5, 1.5), (2.5, 3.0)], str(base_curve))
    check("InaccuracyAngle still reads 0.1 (the base spread the curve grows from)",
          round(angle, 6) == 0.1 if isinstance(angle, float) else False, repr(angle))

    add("inaccuracy-vs-heat (spread growth as the Vulcan heats)",
        "G1-08", "WEAPONS.json field_index + InaccuracyVsTime.Points + user note",
        "`(InaccuracyVsHeat)` matches **%d** fields and no heat term is configured: "
        "`HeatUpPerSecond` is **0.0**, so nothing in this object drives a heat axis. The bloom is "
        "*time*-based: `InaccuracyAngle` **0.1** plus `InaccuracyVsTime` = (0 s, 0.0), "
        "(0.5 s, 0.0), (1.5 s, 1.5), (2.5 s, 3.0), linear - the curve ships values, and the "
        "reticle bloom over the capture's firing sequence is consistent with a time-driven "
        "curve (no footage number is used on it)"
        % zero["inaccuracy-vs-heat"]["matches"], "FILE-VALUE")

    heat_paths = [k for k in values if isinstance(k, str) and k.endswith("HeatUpPerSecond")]
    heat_zero = [k for k in heat_paths if values.get(k) == 0.0]
    add("Vulcan time-to-overheat from cold",
        "G1-08", "WEAPONS.json objects[] + user note",
        "**no per-second heat is configured.** `HeatUpPerSecond` = **0.0** in %d of %d cannon "
        "objects, with `OverheatOffValue` = %s and a `ChainGunOverheatSound` reference on the "
        "same object - so an overheat path is wired, but this field adds no heat per second. "
        "Whether another input (a per-shot add in native code) exists is **not** excluded by "
        "the grab. The *observed* outcome, in play the gun fires seemingly forever, is your "
        "2026-10-26 note; the causal path from these files is UNKNOWN."
        % (len(heat_zero), len(heat_paths), over), "FILE-VALUE")

    radial = "ShouldRadialDamageHit" in open(DAMAGE_MD, encoding="utf-8").read()
    check("DAMAGE_RULES.md still names ShouldRadialDamageHit as native", radial, str(radial))
    add("how a radial hit is decided (`ShouldRadialDamageHit`)",
        "G1-14", "DAMAGE_RULES.md \u00a74",
        "native function - `ShouldRadialDamageHit` is **%s** in the record, so the decision is "
        "in the executable, not in any tagged object" % ("named as native" if radial
                                                         else "MISSING"), "NATIVE")

    health = next((f for f in offsets.get("fields", [])
                   if f.get("field_name") == "Health" and f.get("class") == "RVehicleBatmobile"),
                  None)
    health_val = health["values"] if health else None
    check("Health still reads 1200 in every OFFSETS.json package",
          bool(health_val) and len(health_val) == (health.get("count") or len(health_val))
          and all(v == 1200 for v in health_val), repr(health_val))
    tank = [r for r in rows_objects
            if "tank" in r["name"].lower()
            and (("Proj" in (r.get("class") or "")) or "Weapon" in (r.get("class") or "")
                 or "Shell" in r["name"] or "Cannon" in r["name"])]
    check("no tank weapon/shell object in the grab", not tank, "%d found" % len(tank))
    add("tank shells to destroy the Batmobile",
        "G1-14 / ARM-2", "OFFSETS.json + objects.jsonl",
        "`RVehicleBatmobile.Health` = **%s** (%s, %d packages) but the grab holds **%d** tank "
        "weapon or shell objects - the incoming damage lives in the enemy packages, so shells "
        "to kill is 1200 / (a number these files do not carry); no tank is hit in the captures"
        % (health_val, health["type"] if health else "?", health["count"] if health else 0,
           len(tank)), "NOT-IN-CLIP")

    # ---- 3. the air-control measurement ------------------------------------
    samples = air_samples()
    good = [s for s in samples if not s["missing"]]
    air_times = [s["air_time_s"] for s in good]
    check("three ramp jumps are measured (one sample per jump, three for the gap)",
          len(good) == 3 and len({s["clip"] for s in good}) == 3,
          "%d samples over %d clips" % (len(good), len({s["clip"] for s in good})))
    check("every air sample snapped to a frame within %.2f s" % SNAP_S,
          all(s["snap_error_s"] <= SNAP_S for s in good),
          ", ".join("%.3f" % s["snap_error_s"] for s in good))
    check("the air samples agree within 0.1 s of each other",
          max(air_times) - min(air_times) <= 0.1 if air_times else False,
          "min %.3f max %.3f" % (min(air_times), max(air_times)) if air_times else "none")
    check("the Batmobile is airborne for over a second in every sample (air control has a "
          "window)", all(t >= 1.0 for t in air_times), str(air_times))

    # Every number in this row is formatted from the samples it sits next to (R11).
    mean_air = sum(air_times) / len(air_times) if air_times else 0.0
    sample_list = " / ".join("%.3f" % t for t in air_times)
    frames_seen = [s["frames_airborne"] for s in good]
    measured_row = add(
        "time airborne on a ramp/ledge jump (the observable for the air-control window)",
        "G1-21", "captures (PTS) + WEAPONS/MODES absence",
        "**measured: %.3f s mean** across three ramp jumps (%s s), %s unique frames each at "
        "the captures' ~31 fps cadence. That is the *airborne window* and nothing more: the "
        "samples time the car between leaving the ramp and touching ground, so they do not "
        "show that pitch/yaw input changes the attitude - the clips' names (`air steer "
        "up/down/right`) are the only evidence for steering, and `bUsedAirControlDuringJump` "
        "is a member name, not an observation (R5). `AirControlTimeInAir`, "
        "`AirControlInterpTime` and the six `AirControl*` torque factors have **no value in "
        "the files** (MODES.json: declared, not serialised in any archetype or class default), "
        "so steering authority stays UNKNOWN from the files and from this record; what is "
        "measured is that the car is airborne for over a second per jump, and the value that "
        "runs in that window is a native default"
        % (mean_air, sample_list,
           "%d-%d" % (min(frames_seen), max(frames_seen)) if frames_seen else "?"),
        "MEASURED", samples=good)
    check("the F-6 row quotes the samples it carries (R11)",
          any(r["id"] == measured_row and sample_list in r["file_side"] for r in rows),
          "%s s" % sample_list)
    air_rows = [r for r in rows if r["gap"].startswith("time airborne")]
    check("the air-control rows are MEASURED, not UNKNOWN (the corrected premise)",
          bool(air_rows) and all(r["status"] == "MEASURED" for r in air_rows),
          "%d air row(s)" % len(air_rows))

    # ---- 4. every mode field with no value in the files ---------------------
    not_serialised = [f for f in modes["fields"] if not f["serialized"]]
    check("MODES.json still reports 61 not-serialised fields", len(not_serialised) == 61,
          "%d" % len(not_serialised))
    for f in not_serialised:
        code = "VALUE-NATIVE"
        note = ""
        if f["declaring_class"] == "R3rdPersonCamera":
            code, note = "WRONG-SCOPE", "camera family"
        elif f["field"].startswith("AirControl") or f["field"].startswith("Jump"):
            note = ("reachable: ramps/ledges launch the car (air time measured in %s)" %
                    measured_row)
        add(f["field"], "G1-21", "MODES.json",
            "declared on `%s` at %#x as `%s`, **not serialised** in any of the four archetypes "
            "or their class defaults - no file value exists (MODES.md, %d fields carry no value)"
            % (f["declaring_class"], f["offset"], f["declared_type"], len(not_serialised)),
            code, note)

    # ---- 5. units the field name does not document --------------------------
    undocumented = [f for f in modes["fields"] if f["unit_basis"] == "none"]
    check("MODES.json still reports 5 undocumented units", len(undocumented) == 5,
          "%d" % len(undocumented))
    for f in undocumented:
        state = ("serialised, value %s" % next(iter(f["values"].values()))) if f["values"] \
            else "not serialised"
        add("unit of `%s`" % f["field"], "G1-21", "MODES.json",
            "declared `%s` on `%s`, %s; the name does not say what the number counts, so "
            "MODES.md marks it `undocumented` and does not guess"
            % (f["declared_type"], f["declaring_class"], state), "UNDOCUMENTED")

    # ---- row-level invariants ---------------------------------------------
    check("every row is RESOLVED, MEASURED, or UNKNOWN with a reason",
          all(r["status"] in ("RESOLVED", "MEASURED", "UNKNOWN")
              and r["reason_code"] in REASONS for r in rows), "%d rows" % len(rows))
    check("every MEASURED row carries >= 3 samples",
          all(len(r["samples"]) >= 3 for r in rows if r["status"] == "MEASURED"),
          "%d measured row(s)" % sum(1 for r in rows if r["status"] == "MEASURED"))
    file_answered = {q["quantity"].lower() for q in answered}
    measured_rows = [r for r in rows if r["status"] == "MEASURED"]
    check("no footage-measured row duplicates a quantity the files answer (R4)",
          all(not any(a in r["gap"].lower() or r["gap"].lower() in a
                      for a in file_answered) for r in measured_rows),
          "%d measured row(s) against %d file-answered quantities"
          % (len(measured_rows), len(file_answered)))
    check("every file-resolved row cites a machine source, never footage (R4)",
          all("captur" not in r["source"].lower() for r in rows
              if r["status"] == "RESOLVED"),
          "%d resolved row(s)" % sum(1 for r in rows if r["status"] == "RESOLVED"))
    check("the row count ties back to the three source records",
          len(rows) == 5 + len(not_serialised) + 1 + len(undocumented),
          "%d = 5 card quantities + %d mode fields + 1 measured + %d units"
          % (len(rows), len(not_serialised), len(undocumented)))
    vids, known_vids, tooltips = video_scan()
    check("no Arkham Knight footage inside the workspace (captures stay outside)",
          not vids,
          "%d candidate(s); %d known non-AK (frame-verified), %d 3ds Max tooltip clips"
          % (len(vids), len(known_vids), len(tooltips)))
    check("the known non-AK take is still accounted for",
          all(os.path.isfile(os.path.join(ROOT, p)) for p in KNOWN_NON_AK),
          "%d file(s)" % len(KNOWN_NON_AK))
    vulcan_files = {s["file"] for s in SOURCES if s["kind"] == "vulcan"}
    check("no measured sample comes from the Vulcan capture (muzzle out of frame)",
          bool(VULCAN_OUT_OF_FRAME.strip())
          and not any(x["clip"] in vulcan_files for r in rows for x in r["samples"]),
          "0 samples; %d Vulcan capture(s)" % len(vulcan_files))
    natives_md = set()
    for line in open(DAMAGE_MD, encoding="utf-8"):
        if "**native**" not in line:
            continue
        # Only the `Class.Function` table rows; other native lines carry hex/field mentions.
        m = re.match(r"\s*\|\s*`([A-Za-z_][\w.]*)`\s*\|", line)
        if m:
            natives_md.add(m.group(1).split(".")[-1])
    named_in_rows = set()
    for r in rows:
        named_in_rows |= set(re.findall(r"`([A-Za-z_]\w*)`", r["gap"]))
    unaccounted = sorted(natives_md - named_in_rows - set(NATIVE_UNTRACED))
    check("every native entry point in DAMAGE_RULES.md is a row or explicitly out of scope",
          natives_md and not unaccounted,
          "%d native(s), unaccounted: %s" % (len(natives_md), unaccounted or "none"))

    by_reason = {k: sum(1 for r in rows if r["reason_code"] == k) for k in REASONS}
    doc = {
        "schema": SCHEMA,
        "generated_by": GENERATOR,
        "decision": DECISION,
        "summary": {
            "rows": len(rows),
            "resolved_by_files": sum(1 for r in rows if r["status"] == "RESOLVED"),
            "measured": sum(1 for r in rows if r["status"] == "MEASURED"),
            "measured_samples": sum(len(r["samples"]) for r in rows),
            "by_reason": by_reason,
            "answered_by_files": len(answered),
            "answered_decoded": sum(1 for q in answered if q["decoded"]),
            "video_files": len(vids),
            "video_known_non_ak": len(known_vids),
            "video_tooltips": len(tooltips),
            "air_time_mean_s": round(sum(air_times) / len(air_times), 4) if air_times else None,
            "air_time_min_s": min(air_times) if air_times else None,
            "air_time_max_s": max(air_times) if air_times else None,
        },
        "sources": source_rows,
        "captures_dir": CAPTURES,
        "vulcan_note": VULCAN_OUT_OF_FRAME,
        # The file-side numbers the note quotes, so the prose renders them instead of typing
        # them (R11).
        "file_values": {
            "heat_up_per_second": heat,
            "overheat_off_value": over,
            "inaccuracy_angle": angle,
            "inaccuracy_curve": [[t, v] for t, v in base_curve],
            "heatbar_start": values.get("HeatBarStart"),
            "heatbar_size": values.get("HeatBarSize"),
            "chain_gun_overheat_sound": values.get("RBatmobileCannon.ChainGunOverheatSound"),
        },
        "natives_md": sorted(natives_md),
        "natives_out_of_scope": NATIVE_UNTRACED,
        "answered": answered,
        "rows": rows,
        "reasons": REASONS,
        "checks": checks,
    }
    return doc


def fmt_num(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return "%.6g" % v
    return str(v)


def fmt_val(v):
    if v is None:
        return "—"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(fmt_num(x) for x in v) + "]"
    return fmt_num(v)


def write_markdown(doc):
    s = doc["summary"]
    lines = []
    a = lines.append
    a("# Footage and file answers - the G1-23 gap list (G1-23)")
    a("")
    a("Generated by `Tools/scripts/grab_footage_gaps.py`. The card asks for each `UNKNOWN`/native")
    a("value left by G1-08, G1-14 and G1-21 to be measured from Arkham Knight gameplay or footage")
    a("- source file name + timestamp, frame count at a known fps, at least three samples - **or**")
    a("to stay `UNKNOWN` with the reason. Stop rule (R4): a file value always beats footage;")
    a("footage never overrides it.")
    a("")
    a("> **Corrections (2026-10-26), from your two notes plus the capture folder.**")
    a(">")
    a("> 1. **No per-second heat is configured.** `HeatUpPerSecond` ships **0.0**, so nothing")
    a(">    in the object adds heat with time; the bloom that grows is the time-based")
    a(">    `InaccuracyVsTime` curve. Your note that the gun fires seemingly forever is the")
    a(">    observation; whether a per-shot heat add exists in native code is **UNKNOWN** - the")
    a(">    overheat path is still wired (`OverheatOffValue`, `ChainGunOverheatSound`).")
    a("> 2. **The Batmobile does go airborne**, off ramps (`Actor.bIsVehicleJumpRamp`) and")
    a(">    ledges, so the air-control rows are reachable - the earlier `UNREACHABLE` reason was")
    a(">    wrong. Three ramp jumps are measured below.")
    a(">")
    a("> Sources: `%s` - five Arkham Knight captures, read in place and never copied in."
      % doc["captures_dir"])
    a("")
    a("| fact | value |")
    a("|---|---|")
    a("| gap rows | **%d** |" % s["rows"])
    a("| closed by a file value | **%d** |" % s["resolved_by_files"])
    a("| measured from footage | **%d row, %d samples** |" % (s["measured"], s["measured_samples"]))
    a("| air time (three ramp jumps) | **%.3f s mean** (%.3f - %.3f) |"
      % (s["air_time_mean_s"], s["air_time_min_s"], s["air_time_max_s"]))
    a("| quantities the files *do* answer (not gaps) | %d (%d with a decoded value) |"
      % (s["answered_by_files"], s["answered_decoded"]))
    for code, n in sorted(s["by_reason"].items()):
        a("| reason `%s` | %d |" % (code, n))
    a("")
    a("## 1. The captures (outside the workspace, never copied in)")
    a("")
    a("`%s`" % doc["captures_dir"])
    a("")
    a("| file | frames | duration | nominal | role |")
    a("|---|---:|---:|---|---|")
    for r in doc["sources"]:
        a("| `%s` | %d | %.2f s | %s | %s |"
          % (r["file"], r["frames"], r["duration_s"] or 0, r["nominal_fps"], r["role"]))
    a("")
    a("All five are **variable-framerate**: nominal 60 fps, but only 37-38 unique frames per")
    a("1.2 s (a ~31 fps cadence). Every sample here is therefore computed from presentation")
    a("timestamps, with the frame indices recorded next to the PTS span - a frame count alone")
    a("would be wrong by a third.")
    a("")
    a("On the Vulcan capture, %s." % doc["vulcan_note"])
    a("")

    fv = doc["file_values"]
    a("## 2. The Vulcan: no per-second heat is configured")
    a("")
    a("`RBatmobileCannon.HeatUpPerSecond` = **%s** in the cannon objects - that is the"
      % fmt_num(fv["heat_up_per_second"]))
    a("per-*second* term, and 0 removes it: nothing here adds heat with time. An overheat path is")
    a("still wired - `OverheatOffValue` **%s**, a `ChainGunOverheatSound` reference"
      % fmt_num(fv["overheat_off_value"]))
    a("(import ref %s), and the HUD bar (`HeatBarStart` %s, `HeatBarSize` %s) - which is why"
      " the"
      % (fmt_val(fv["chain_gun_overheat_sound"]), fmt_val(fv["heatbar_start"]),
         fmt_val(fv["heatbar_size"])))
    a("observed *\"it never overheats, it fires forever\"* (your 2026-10-26 note) is compatible")
    a("with this object. It is **not** proof that no other heat input exists: a per-shot add in")
    a("native code is not excluded by the grab, so the mechanism is **UNKNOWN** and the")
    a("observation stays yours.")
    a("")
    a("The spread that does grow is the time curve that ships:")
    a("")
    a("| `InaccuracyVsTime` point | in (s) | out |")
    a("|---|---:|---:|")
    for i, (tin, tout) in enumerate(fv["inaccuracy_curve"] or []):
        a("| p%d | %s | %s |" % (i, fmt_num(tin), fmt_num(tout)))
    a("")
    a("on top of `InaccuracyAngle` **%s**. The `(InaccuracyVsHeat)` pattern matches **0**"
      % fmt_num(fv["inaccuracy_angle"]))
    a("fields: there is no heat axis in the object for it to drive. Two rows are therefore")
    a("closed by the files, and no footage number is used on them (R4).")
    a("")

    a("## 3. The air-control measurement")
    a("")
    a("Each sample: the first frame with the car clear of the ramp, and the first frame with")
    a("ground contact (impact sparks / wheels down). Boundaries were read off timestamp-burned")
    a("contact sheets at 15 fps, then snapped to the nearest decoded frame. Frame indices are")
    a("0-based within each clip.")
    a("")
    a("| clip | first air (frame / PTS) | first contact (frame / PTS) | frames | air time | nominal 60 fps |")
    a("|---|---|---|---:|---:|---:|")
    for r in doc["rows"]:
        if r["status"] != "MEASURED":
            continue
        for x in r["samples"]:
            a("| `%s` | %d / %.3f s | %d / %.3f s | %d | **%.3f s** | %.1f |"
              % (x["clip"], x["first_air_frame"], x["first_air_pts"],
                 x["first_contact_frame"], x["first_contact_pts"],
                 x["frames_airborne"], x["air_time_s"], x["nominal_60fps_frames"]))
    a("")
    a("Mean **%.3f s**, spread **%.3f s**. What this measures is the airborne window: the car"
      % (s["air_time_mean_s"], s["air_time_max_s"] - s["air_time_min_s"]))
    a("is off the ground for over a second on every jump. It does **not** measure steering")
    a("authority - the clips are named `air steer up / down / right`, and that naming is the")
    a("only evidence that input changed the attitude, so \"controllable in the air\" is an")
    a("inference, not a measurement here. `bUsedAirControlDuringJump` is a member name, not an")
    a("observation (R5). The `AirControl*` *values* are declared on `RVehicleSimBatmobile` /")
    a("`Pawn` and serialised in no archetype or class default, so they stay `VALUE-NATIVE` and")
    a("how much authority they carry is **UNKNOWN** from the files.")
    a("")

    a("## 4. What the files already answer (not gaps)")
    a("")
    a("The card's own examples that the files already hold - R4 means footage would never be")
    a("used on these. **%d of %d carry a decoded value**; the rest are field-present with"
      % (sum(1 for q in doc["answered"] if q.get("decoded")), len(doc["answered"])))
    a("contents this walker does not decode, which is still not a footage gap (a footage")
    a("measurement could not invent them either):")
    a("")
    a("| quantity | fields | example | value |")
    a("|---|---|---|---|")
    for q in doc["answered"]:
        v = q["example_value"]
        if q.get("array_points"):
            pts = q["array_points"]
            v = "%d points, %s" % (len(pts),
                                     ", ".join("%.1f->%.1f" % tuple(p) for p in pts))
        elif v is None:
            v = ("array present, contents not decoded (%s entries)" % q["array_count"]
                 if q.get("array_count") else "field present, contents not decoded")
        elif isinstance(v, float):
            v = "%.4g" % v
        a("| %s | %d | `%s` | %s |" % (q["quantity"], q["matches"], q["example_field"], v))
    a("")

    def section(title, subset, intro):
        a("## %s" % title)
        a("")
        for line in intro:
            a(line % {"n": len(subset)} if "%" in line else line)
        a("")
        a("| id | gap | card | what the files say | status | reason |")
        a("|---|---|---|---|---|---|")
        for r in subset:
            a("| %s | %s | %s | %s | **%s** | `%s` |" % (
                r["id"], r["gap"], r["card"],
                (r["file_side"] + (" - *%s*" % r["note"] if r["note"] else "")).replace("|", "/"),
                r["status"], r["reason_code"]))
        a("")

    section("5. Weapons and damage (G1-08, G1-09, G1-14)",
            [r for r in doc["rows"] if r["card"] != "G1-21"],
            ["The five card quantities with no file value split three ways: two are closed by",
             "the files (the Vulcan pair), one is a native decision, two need an event the",
             "captures do not contain."])
    a("### G1-14's other native entry points")
    a("")
    a("`DAMAGE_RULES.md` records %d native functions; `ShouldRadialDamageHit` is a row above (its"
      % len(doc["natives_md"]))
    a("body is two parameter descriptors, so the decision is in `BatmanAK.exe`). The rest are")
    a("gates, setters or a return value with no file default - none has an observable quantity,")
    a("so they are recorded here rather than silently dropped:")
    a("")
    a("| native | why it is not a footage gap |")
    a("|---|---|")
    for name in sorted(doc["natives_out_of_scope"]):
        a("| `%s` | %s |" % (name, doc["natives_out_of_scope"][name]))
    a("")
    section("6. Mode fields with no value in the files (G1-21)",
            [r for r in doc["rows"] if r["card"] == "G1-21" and not r["gap"].startswith("unit of")],
            ["The %(n)d rows here: the 61 fields `MODES.json` reports as declared but **not",
             "serialised** in any archetype or class default, plus the measured air-time row.",
             "The value that runs comes from a native default, which is not in this grab."])
    section("7. Units the field name does not document (G1-21)",
            [r for r in doc["rows"] if r["gap"].startswith("unit of")],
            ["`MODES.md` reports these rather than guessing them; no clip in the set settles",
             "what the number counts."])

    a("## 8. Reason codes")
    a("")
    a("| code | meaning |")
    a("|---|---|")
    for code, text in doc["reasons"].items():
        a("| `%s` | %s |" % (code, text))
    a("")

    a("## 9. Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for c in doc["checks"]:
        a("| %s | %s | %s |" % (c["name"], "PASS" if c["pass"] else "FAIL", c["detail"]))
    a("")
    a("%d/%d checks passed." % (sum(1 for c in doc["checks"] if c["pass"]),
                                len(doc["checks"])))
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write FOOTAGE.json and FOOTAGE.md")
    ap.add_argument("--check", action="store_true",
                    help="re-read every file side and source, compare with the record on disk")
    args = ap.parse_args()
    if not args.write and not args.check:
        args.check = True

    doc = build()
    json_path = os.path.join(OUT, "FOOTAGE.json")
    md_path = os.path.join(OUT, "FOOTAGE.md")

    if args.write:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(write_markdown(doc))
        print("wrote FOOTAGE.json (%d rows) and FOOTAGE.md" % doc["summary"]["rows"])
        return 0

    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(json_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    with open(json_path, encoding="utf-8") as fh:
        if json.load(fh) != doc:
            print("STALE: FOOTAGE.json does not match a fresh build (run --write)")
            return 1
    if open(md_path, encoding="utf-8").read() != write_markdown(doc):
        print("STALE: FOOTAGE.md does not match a fresh render (run --write)")
        return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    s = doc["summary"]
    print("OK: %d rows, %d file-resolved, %d measured (%d samples), reasons %s; %d/%d checks; "
          "md byte-identical"
          % (s["rows"], s["resolved_by_files"], s["measured"], s["measured_samples"],
             s["by_reason"], len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
