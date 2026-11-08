"""sampler_fields2.py - G3-02f: BmSDK offsets needed to observe the Batmobile's X (missile barrage),
Y (boost), missile-launcher state, booster state and A-button eject live.

Source of every offset: the BmSDK-AK generated C# layouts (MIT),
E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/**/*.g.cs. Each field below is read out of its
`/// <Type>Property: <name>` comment block and the `Ptr + N` in the getter; the line number reported
is the comment line. Nothing here comes from general knowledge of UE3: a field that is not in these
files is reported as UNKNOWN, with what was scanned.

Kind -> how to read it live:
  u8      read 1 byte at offset              (ByteProperty)
  i32     read 4 bytes at offset             (IntProperty)
  f32     read 4 bytes at offset             (FloatProperty)
  bit     read 4 bytes (int) at offset, AND with the mask, != 0   (BoolProperty)
  ptr     read 8 bytes at offset             (Object/ComponentProperty)
  fname   read 8 bytes at offset (index, number)  (NameProperty)
  tarray  pointer at +0, Num (count) at +8, Max at +12  (BmSDK Classes/Core/TArray.cs NativeData)
  struct  raw bytes at offset (width derived from the next field)

    python Tools/scripts/sampler_fields2.py --write
    python Tools/scripts/sampler_fields2.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BMSDK = os.environ.get("BMSDK_DIR", r"E:/Modding/_tools/BmSDK-AK/src/BmSDK")
GEN = os.path.join(BMSDK, "Generated")
OUT_MD = os.path.join("Research", "BatmobileGrab", "SAMPLER_FIELDS2.md")
OUT_JSON = os.path.join("Research", "BatmobileGrab", "SAMPLER_FIELDS2.json")
GCS = lambda rel: "BmSDK/Generated/" + rel

CLASS_FILES = {
    "RPlayerInput": "BmGame/RPlayerInput.g.cs",
    "RVehicleWeapon": "BmGame/RVehicleWeapon.g.cs",
    "RBatmobileMissileLauncher": "BmGame/RBatmobileMissileLauncher.g.cs",
    "RBatmobileBooster": "BmGame/RBatmobileBooster.g.cs",
    "RVehicleBatmobileBase": "BmGame/RVehicleBatmobileBase.g.cs",
    "RPlayerController": "BmGame/RPlayerController.g.cs",
}
CLASS_SIZES = {"RPlayerInput": 872, "RVehicleWeapon": 2396, "RBatmobileMissileLauncher": 2648,
               "RBatmobileBooster": 2400, "RVehicleBatmobileBase": 8352}

KIND = {"Byte": "u8", "Int": "i32", "Float": "f32", "Bool": "bit", "Object": "ptr",
        "Component": "ptr", "Name": "fname", "Array": "tarray", "Struct": "struct", "Str": "fstring"}

# (class, field) -> (offset, mask, comment line); None means "do not assert this one".
EXPECT = {
    ("RPlayerInput", "bVehicleBoostButton"): (781, None, 944),
    ("RPlayerInput", "bBatmobileEjectModifier"): (786, None, 989),
    ("RPlayerInput", "bReadyGadgetButton"): (773, None, 872),
    ("RPlayerInput", "bGadgetSelectWheel"): (784, None, 971),
    ("RPlayerInput", "bThrottleButton"): (780, None, 935),
    ("RPlayerInput", "bBrakeButton"): (782, None, 953),
    ("RPlayerInput", "bHandBrakeButton"): (776, None, 899),
    ("RPlayerInput", "bHandbrakeOrBrake"): (783, None, 962),
    ("RPlayerInput", "bFireVehicleWeapon"): (778, None, 917),
    ("RPlayerInput", "bFireVehicleSecondaryWeapon"): (779, None, 926),
    ("RPlayerInput", "bArmouredMode"): (777, None, 908),
    ("RPlayerInput", "aThrottleAxis"): (840, None, 1124),
    ("RPlayerInput", "aBrakeAxis"): (844, None, 1133),
    ("RPlayerInput", "aRightTrigger"): (720, None, 665),
    ("RPlayerInput", "aLeftTrigger"): (724, None, 674),
    ("RPlayerInput", "aLeftShoulder"): (760, None, 755),
    ("RPlayerInput", "bCancelButton"): (774, None, 881),
    ("RVehicleWeapon", "bFiring"): (2084, 2, 637),
    ("RVehicleWeapon", "ContinuousFire"): (2084, 1, 628),
    ("RVehicleWeapon", "FiringInterval"): (2088, None, 718),
    ("RVehicleWeapon", "CoolDown"): (2092, None, 727),
    ("RVehicleWeapon", "WeaponCoolDown"): (2096, None, 736),
    ("RVehicleWeapon", "AimTarget"): (2168, None, 835),
    ("RBatmobileMissileLauncher", "MaxTargets"): (2396, None, 291),
    ("RBatmobileMissileLauncher", "CurrentTargets"): (2400, None, 300),
    ("RBatmobileMissileLauncher", "LastTargets"): (2416, None, 309),
    ("RBatmobileMissileLauncher", "LockOnAngle"): (2432, None, 318),
    ("RBatmobileMissileLauncher", "LockOnRange"): (2436, None, 327),
    ("RBatmobileMissileLauncher", "InitialFireDelay"): (2440, None, 336),
    ("RBatmobileMissileLauncher", "FireInterval"): (2444, None, 345),
    ("RBatmobileMissileLauncher", "CooldownDelay"): (2448, None, 354),
    ("RBatmobileMissileLauncher", "NthTarget"): (2560, None, 477),
    ("RBatmobileMissileLauncher", "LastState"): (2564, None, 486),
    ("RBatmobileMissileLauncher", "CurrentLevel"): (2588, None, 504),
    ("RBatmobileMissileLauncher", "MaxTargetsPerLevel"): (2592, None, 513),
    ("RBatmobileMissileLauncher", "MissileSockets"): (2608, None, 522),
    ("RBatmobileMissileLauncher", "CurrentMissileSocket"): (2624, None, 531),
    ("RBatmobileMissileLauncher", "InfinitMissilesTime"): (2628, None, 540),
    ("RBatmobileMissileLauncher", "FiredProjectiles"): (2632, None, 549),
    ("RBatmobileBooster", "bBoosting"): (2396, 1, 82),
    ("RBatmobileBooster", "bWarming"): (2396, 2, 91),
    ("RVehicleBatmobileBase", "BatmanVsBatmobileCollisionMode"): (5895, None, 6758),
    ("RVehicleBatmobileBase", "BoostingOut"): (5901, None, 6812),
    ("RVehicleBatmobileBase", "MaxEjectType"): (5902, None, 6821),
    ("RVehicleBatmobileBase", "EjectUpDist"): (6032, None, 7004),
    ("RVehicleBatmobileBase", "LastBoostPickupTime"): (6580, None, 7527),
    ("RVehicleBatmobileBase", "InfiniteBoost"): (4568, 536870912, 4716),
    ("RVehicleBatmobileBase", "bBoostLocked"): (4568, 16384, 4581),
    ("RVehicleBatmobileBase", "AfterburnerSystem"): (4636, None, 5298),
    ("RVehicleBatmobileBase", "OverrideNextEject"): (5604, None, 6373),
    ("RPlayerController", "LastEjectFromBatmobileTime"): (None, None, 31720),
    ("RPlayerController", "UsedQuickGadget"): (None, None, 26194),
    ("RPlayerController", "CurrentEjectType"): (None, None, 28120),
}

# area, role, class, field, extra note
OBSERVABLES = [
    ("inputs", "Y held (boost) - the digital button byte", "RPlayerInput", "bVehicleBoostButton",
     "D-11 user mapping: Y = boost in pursuit; the field name is the only RPlayerInput member that "
     "names the vehicle boost"),
    ("inputs", "Y context - throttle/brake for a boost make/break comparison", "RPlayerInput",
     "bThrottleButton", "read with bBrakeButton/aThrottleAxis to tell a boost from a coast"),
    ("inputs", "Y context - brake", "RPlayerInput", "bBrakeButton", ""),
    ("inputs", "Y context - analog throttle", "RPlayerInput", "aThrottleAxis", ""),
    ("inputs", "Y context - analog brake", "RPlayerInput", "aBrakeAxis", ""),
    ("inputs", "combat context - primary fire", "RPlayerInput", "bFireVehicleWeapon", ""),
    ("inputs", "combat context - secondary fire", "RPlayerInput", "bFireVehicleSecondaryWeapon", ""),
    ("inputs", "eject - modifier byte beside the eject", "RPlayerInput", "bBatmobileEjectModifier",
     "the only eject-named input field in RPlayerInput; what button it modifies is not in the layout"),
    ("inputs", "handbrake (control sample, unchanged behaviour)", "RPlayerInput", "bHandBrakeButton", ""),
    ("missiles", "target count ceiling", "RBatmobileMissileLauncher", "MaxTargets",
     "the array Max may exceed this; compare Num against it"),
    ("missiles", "targets currently held (array; read Num at +8)", "RBatmobileMissileLauncher",
     "CurrentTargets", "pointer +0, Num +8, Max +12"),
    ("missiles", "targets on the previous frame (array)", "RBatmobileMissileLauncher", "LastTargets",
     "compare with CurrentTargets to see a re-target"),
    ("missiles", "firing flag", "RVehicleWeapon", "bFiring",
     "inherited by both missile and booster: RBatmobileBooster : RVehicleWeapon"),
    ("missiles", "continuous-fire flag (same word as bFiring)", "RVehicleWeapon", "ContinuousFire", ""),
    ("missiles", "cooldown remaining", "RVehicleWeapon", "CoolDown", "per-weapon timer"),
    ("missiles", "weapon cooldown (second timer)", "RVehicleWeapon", "WeaponCoolDown",
     "distinct from CoolDown; which one gates the barrage is UNKNOWN"),
    ("missiles", "fire interval", "RVehicleWeapon", "FiringInterval", ""),
    ("missiles", "cooldown configured for the launcher", "RBatmobileMissileLauncher", "CooldownDelay", ""),
    ("missiles", "initial delay before the first missile", "RBatmobileMissileLauncher", "InitialFireDelay", ""),
    ("missiles", "spacing between missiles in a volley", "RBatmobileMissileLauncher", "FireInterval",
     "note: a different field from RVehicleWeapon.FiringInterval"),
    ("missiles", "index of the next target to fire at", "RBatmobileMissileLauncher", "NthTarget", ""),
    ("missiles", "launcher state name", "RBatmobileMissileLauncher", "LastState",
     "FName: read index and number; resolve through GNames"),
    ("missiles", "current target level", "RBatmobileMissileLauncher", "CurrentLevel",
     "with MaxTargetsPerLevel, the per-level target cap"),
    ("missiles", "per-level target cap (array)", "RBatmobileMissileLauncher", "MaxTargetsPerLevel", ""),
    ("missiles", "missile sockets (array)", "RBatmobileMissileLauncher", "MissileSockets", ""),
    ("missiles", "socket index in use", "RBatmobileMissileLauncher", "CurrentMissileSocket", ""),
    ("missiles", "unlimited-missiles window", "RBatmobileMissileLauncher", "InfinitMissilesTime",
     "seconds of free fire; 0 when inactive"),
    ("missiles", "missiles in flight (array)", "RBatmobileMissileLauncher", "FiredProjectiles", ""),
    ("missiles", "lock-on cone", "RBatmobileMissileLauncher", "LockOnAngle", ""),
    ("missiles", "lock-on range", "RBatmobileMissileLauncher", "LockOnRange", ""),
    ("missiles", "aim target inherited from the weapon base", "RVehicleWeapon", "AimTarget", ""),
    ("boost", "boost active", "RBatmobileBooster", "bBoosting",
     "the booster object's own flag; setter is the afterburner code"),
    ("boost", "boost warming up", "RBatmobileBooster", "bWarming", "same int word as bBoosting"),
    ("boost", "boost locked (cannot engage)", "RVehicleBatmobileBase", "bBoostLocked",
     "same int word as InfiniteBoost"),
    ("boost", "boost permanently allowed", "RVehicleBatmobileBase", "InfiniteBoost", ""),
    ("boost", "afterburner particle component", "RVehicleBatmobileBase", "AfterburnerSystem",
     "non-null while the effect exists; not an activity flag"),
    ("boost", "last boost pickup time", "RVehicleBatmobileBase", "LastBoostPickupTime",
     "a timestamp, not a duration"),
    ("boost", "boosting-out state byte", "RVehicleBatmobileBase", "BoostingOut",
     "byte, not the bBoosting bit"),
    ("eject", "eject type configured", "RVehicleBatmobileBase", "MaxEjectType", ""),
    ("eject", "eject upward distance", "RVehicleBatmobileBase", "EjectUpDist", ""),
    ("eject", "forced next eject", "RVehicleBatmobileBase", "OverrideNextEject",
     "object pointer; non-null forces a scripted eject"),
    ("eject", "eject type chosen at the last eject", "RPlayerController", "CurrentEjectType",
     "player-controller side; offset resolved here, value observed live"),
    ("eject", "time of the last eject from the Batmobile", "RPlayerController",
     "LastEjectFromBatmobileTime", ""),
    ("eject", "last eject/exit time comparison for X use", "RPlayerController", "UsedQuickGadget",
     "bit; the QuickGadgetX handler sets it, but no per-button field exists"),
]

CANDIDATES = [
    ("RPlayerInput", "bReadyGadgetButton", 773,
     "a gadget button byte, but the layout does not say it is X (could be the gadget-wheel open)"),
    ("RPlayerInput", "bGadgetSelectWheel", 784, "the gadget wheel input, not the X action"),
    ("RPlayerInput", "bCancelButton", 774, "cancel; the live sampler already watches this one"),
    ("RPlayerController", "UsedQuickGadget", None,
     "set by the QuickGadgetX handler; a consequence of X, not the input byte"),
]

UNKNOWNS = [
    ("X (missile barrage) input byte",
     "all {n_in} top-level property blocks of RPlayerInput were parsed; there is no field named "
     "*QuickGadgetX*, *XButton*, *Barrage* or similar. RPlayerController.QuickGadgetX is a Function "
     "(BmSDK/Generated/BmGame/RPlayerController.g.cs:491), not a field, so the byte the X binding "
     "writes is not in the layout",
     "answer from RPlayerInput's bind table or BmGame/Config/BmInput.ini - neither is in these files"),
    ("A (eject) input byte",
     "RPlayerInput has bBatmobileEjectModifier (786) and no bAButton / bActionButton / bEjectButton; "
     "grep over the whole Generated tree finds no such property",
     "same place as X: the bind table / BmInput.ini; the modifier byte at 786 is decoded but its "
     "trigger button is not"),
    ("boost duration / boost time field",
     "RBatmobileBooster has only bBoosting and bWarming (2 fields, size 2400); "
     "RVehicleBatmobileBase.GetBoostPct is a Function (g.cs:3084), not a field, and "
     "LastBoostPickupTime (6580) is a timestamp. grep over Generated finds no BoostTimer/BoostTime field",
     "observe bBoosting transitions and measure the interval instead of reading a timer"),
    ("TArray element stride for CurrentTargets / FiredProjectiles",
     "the layouts give the array offset and the element type but not the element size; "
     "BmSDK MarshalUtil.GetSizeUnmanaged<T> would, and is not in the generated tree",
     "needed only to walk the targets, not to count them"),
]


# ------------------------------------------------------------------ parse
def parse_class(rel: str) -> dict:
    path = os.path.join(GEN, rel)
    lines = open(path, encoding="utf-8-sig").read().splitlines()
    size = flags = None
    for l in lines[:14]:
        m = re.search(r"size = (\d+)", l)
        if m:
            size = int(m.group(1))
        m = re.search(r"flags = (\d+)", l)
        if m:
            flags = int(m.group(1))
    fields = []
    for i, l in enumerate(lines):
        m = re.match(r" {4}///\s*(\w+?)Property:\s*(\w+)\s*$", l)
        if not m:
            continue
        typ, name = m.group(1), m.group(2)
        for j in range(i + 1, min(i + 10, len(lines))):
            g = re.search(r"Ptr \+ (\d+)", lines[j])
            if not g:
                continue
            mk = re.search(r"Ptr \+ \d+\)\s*&\s*(0x[0-9A-Fa-f]+|\d+)", lines[j])
            sig = lines[j - 1] if lines[j - 1].lstrip().startswith("public") else lines[j]
            em = re.search(r"TArray<([^>]+)>", sig)
            fields.append({
                "name": name, "type": typ, "kind": KIND.get(typ, "?"),
                "offset": int(g.group(1)),
                "mask": int(mk.group(1), 0) if mk else None,
                "line": i + 1, "signature": sig.strip(),
                "element": em.group(1).strip() if em else None,
            })
            break
    offs = sorted({f["offset"] for f in fields})
    for f in fields:
        nxt = next((o for o in offs if o > f["offset"]), size or 0)
        f["width"] = nxt - f["offset"]
    return {"file": GCS(rel), "size": size, "flags": flags, "fields": fields}


def build() -> dict:
    classes, index = {}, {}
    for cls, rel in CLASS_FILES.items():
        parsed = parse_class(rel)
        classes[cls] = parsed
        for f in parsed["fields"]:
            index[(cls, f["name"])] = f
    tarr = open(os.path.join(BMSDK, "Classes", "Core", "TArray.cs"), encoding="utf-8-sig").read().splitlines()
    tlines = {}
    for k, l in enumerate(tarr, 1):
        for key in ("AllocatorInstance", "Num", "Max"):
            if re.search(r"public\s+\w+\s+%s;" % key, l):
                tlines.setdefault(key, k)

    def obs(area, role, cls, field, note):
        f = index[(cls, field)]
        return {"area": area, "role": role, "class": cls, "field": field,
                "offset": f["offset"], "kind": f["kind"], "mask": f["mask"],
                "width": f["width"], "element": f["element"],
                "cs_file": classes[cls]["file"], "cs_line": f["line"], "note": note,
                "label": "decoded (%s:%d, %s @%d%s)" % (
                    classes[cls]["file"], f["line"], f["kind"], f["offset"],
                    "" if f["mask"] is None else ", mask %#x" % f["mask"])}

    doc = {
        "schema": 1,
        "card": "G3-02f - BmSDK offsets for the BmAK runtime sampler: X (barrage), Y (boost), "
                "missile launcher, booster, A (eject)",
        "source": "BmSDK-AK generated layouts (MIT), E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated",
        "labels": {"decoded": "read from the named .g.cs comment line + the Ptr + N in its getter",
                   "derived": "computed from decoded facts (widths from the next field, offsets from TArray.cs)",
                   "UNKNOWN": "no such field exists in the layouts read; what was scanned is stated"},
        "classes": {k: {"file": v["file"], "size": v["size"], "flags": v["flags"],
                        "fields": len(v["fields"])} for k, v in classes.items()},
        "observables": [obs(*o) for o in OBSERVABLES],
        "candidates": [dict(zip(("class", "field", "offset", "why"), c),
                            label="decoded field, UNKNOWN binding") for c in CANDIDATES],
        "unknowns": [{"what": u[0],
                      "tried": u[1].replace("{n_in}", str(len(classes["RPlayerInput"]["fields"]))),
                      "where_it_would_be": u[2]} for u in UNKNOWNS],
        "tarray_layout": {"allocator": tlines.get("AllocatorInstance"), "num": tlines.get("Num"),
                          "max": tlines.get("Max"),
                          "offsets": {"data": 0, "count": 8, "max": 12},
                          "file": "BmSDK/Classes/Core/TArray.cs"},
        "readers": {
            "u8": "byte at offset", "i32": "int32 at offset", "f32": "float32 at offset",
            "bit": "int32 at offset & mask != 0", "ptr": "pointer at offset",
            "fname": "int32 index at offset (and int32 number at offset+4)",
            "tarray": "count = int32 at offset+8", "struct": "raw bytes at offset",
        },
    }
    doc["oracles"] = oracles(classes, index, doc)
    return doc


def oracles(classes, index, doc) -> dict:
    out = {}

    def add(key, ok, detail):
        out[key] = {"ok": bool(ok), "detail": detail}

    bad = []
    for (cls, field), (off, mask, line) in sorted(EXPECT.items()):
        f = index.get((cls, field))
        if f is None:
            bad.append("%s.%s missing" % (cls, field))
            continue
        if off is not None and f["offset"] != off:
            bad.append("%s.%s offset %d != %d" % (cls, field, f["offset"], off))
        if mask is not None and f["mask"] != mask:
            bad.append("%s.%s mask %r != %r" % (cls, field, f["mask"], mask))
        if f["line"] != line:
            bad.append("%s.%s line %d != %d" % (cls, field, f["line"], line))
    add("expected_offsets", not bad, {"checked": len(EXPECT), "failures": bad})

    bad = []
    for cls, parsed in classes.items():
        lines = open(os.path.join(GEN, CLASS_FILES[cls]),
                     encoding="utf-8-sig").read().splitlines()
        for f in parsed["fields"]:
            if not re.match(r"\s*///\s*\w+Property:\s*%s\s*$" % re.escape(f["name"]),
                            lines[f["line"] - 1]):
                bad.append("%s.%s @%d" % (cls, f["name"], f["line"]))
    add("line_points_at_comment", not bad, {"failures": bad[:10], "count": len(bad)})

    bad = [("%s.%s" % (c, f["name"])) for c, p in classes.items() for f in p["fields"]
           if p["size"] and (f["width"] <= 0 or f["offset"] + f["width"] > p["size"])]
    add("widths_fit_class", not bad, {"failures": bad[:10]})

    bad = []
    for c, p in classes.items():
        seen = set()
        for f in p["fields"]:
            key = (f["offset"], f["mask"] if f["mask"] is not None else -1)
            if key in seen:
                bad.append("%s offset %d mask %r twice" % (c, f["offset"], f["mask"]))
            seen.add(key)
        for f in p["fields"]:
            if f["mask"] is not None and (f["mask"] & (f["mask"] - 1)) != 0:
                bad.append("%s.%s mask %#x not a single bit" % (c, f["name"], f["mask"]))
    add("mask_uniqueness", not bad, {"failures": bad[:10]})

    bad = []
    for c, p in classes.items():
        offs = [f["offset"] for f in p["fields"]]
        if offs != sorted(offs):
            bad.append(c + " not ascending")
    add("offsets_ascending", not bad, {"failures": bad})

    sizes_bad = {c: (classes[c]["size"], CLASS_SIZES[c]) for c in CLASS_SIZES
                 if classes[c]["size"] != CLASS_SIZES[c]}
    add("class_sizes", not sizes_bad, {"expected": CLASS_SIZES, "mismatch": sizes_bad})

    t = doc["tarray_layout"]
    seq = [t["allocator"], t["num"], t["max"]]
    add("tarray_layout", all(seq) and seq == sorted(seq) and seq[1] == seq[0] + 1
        and seq[2] == seq[1] + 1,
        {"lines": seq, "offsets": t["offsets"],
         "rule": "IntPtr,int,int sequential -> 0/8/12 (x64)"})

    bad = [o["field"] for o in doc["observables"] if (o["class"], o["field"]) not in index]
    add("observables_resolve", not bad, {"count": len(doc["observables"]), "missing": bad})

    keys = [(o["class"], o["field"]) for o in doc["observables"]]
    add("observables_unique", len(keys) == len(set(keys)),
        {"count": len(keys), "unique": len(set(keys))})

    names = {u["what"].split(" ")[0] for u in doc["unknowns"]}
    add("unknowns_present", {"X", "A", "boost"} <= names,
        {"unknowns": [u["what"] for u in doc["unknowns"]]})

    add("booster_inherits_weapon", classes["RBatmobileBooster"]["size"] == 2400
        and index[("RVehicleWeapon", "bFiring")]["offset"] < 2400,
        {"rule": "RBatmobileBooster : RVehicleWeapon, so bFiring/CoolDown are inherited at the same offsets",
         "bFiring": index[("RVehicleWeapon", "bFiring")]["offset"]})

    add("collision_mode_offset_matches_sampler",
        index[("RVehicleBatmobileBase", "BatmanVsBatmobileCollisionMode")]["offset"] == 0x1707,
        {"layout": index[("RVehicleBatmobileBase", "BatmanVsBatmobileCollisionMode")]["offset"],
         "sampler": 0x1707, "note": "bmak_runtime_sampler.py VEH uses 0x1707; the layout says 5895"})
    return out


# ------------------------------------------------------------------ render
def render(doc: dict) -> str:
    L = []
    A = L.append
    A("# BmSDK offsets for the BmAK sampler - X (barrage), Y (boost), missiles, booster, A (eject)")
    A("")
    A("**Card:** G3-02f. **Source:** `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated` (BmSDK-AK, MIT),")
    A("read from the `/// <Type>Property:` comment and the `Ptr + N` getter of each field.")
    A("Every offset below is `decoded` at the `.g.cs` file and line in its row; the line number is the")
    A("comment line. `Width` is `derived` (distance to the next field, last field to the class size).")
    A("")
    A("| class | .g.cs | size | fields parsed |")
    A("|---|---|---|---|")
    for k, v in doc["classes"].items():
        A("| `%s` | `%s` | %d | %d |" % (k, v["file"], v["size"], v["fields"]))
    A("")
    A("## How to read each kind live")
    A("")
    A("| kind | read |")
    A("|---|---|")
    for k, v in doc["readers"].items():
        A("| `%s` | %s |" % (k, v))
    A("")
    A("`tarray`: pointer at +0, **count at +8**, Max at +12 - `BmSDK/Classes/Core/TArray.cs:%s-%s`" % (
        doc["tarray_layout"]["allocator"], doc["tarray_layout"]["max"]))
    A("(`AllocatorInstance`, `Num`, `Max` in a sequential struct, so x64 offsets 0/8/12).")
    A("")
    areas = [("inputs", "1. Inputs - `RPlayerInput` (Y decoded; X and A UNKNOWN)"),
             ("missiles", "2. Missile launcher - `RBatmobileMissileLauncher` and its base `RVehicleWeapon`"),
             ("boost", "3. Booster - `RBatmobileBooster` and the vehicle's boost flags"),
             ("eject", "4. Eject - vehicle and player-controller side")]
    for area, title in areas:
        A("## " + title)
        A("")
        A("| role | field | offset | kind | mask | width | .g.cs line | label |")
        A("|---|---|---|---|---|---|---|---|")
        for o in doc["observables"]:
            if o["area"] != area:
                continue
            A("| %s | `%s.%s` | %d (%#x) | `%s` | %s | %d | `%s:%d` | %s |" % (
                o["role"], o["class"], o["field"], o["offset"], o["offset"], o["kind"],
                "-" if o["mask"] is None else str(o["mask"]),
                o["width"], o["cs_file"], o["cs_line"], o["label"]))
        A("")
        extra = [o for o in doc["observables"] if o["area"] == area and o["note"]]
        for o in extra:
            A("- `%s.%s`: %s" % (o["class"], o["field"], o["note"]))
        if extra:
            A("")
    A("## 5. Candidates - the field exists, the binding does not")
    A("")
    A("| field | offset | why it is not claimed |")
    A("|---|---|---|")
    for c in doc["candidates"]:
        A("| `%s.%s` | %s | %s |" % (c["class"], c["field"],
                                     "-" if c["offset"] is None else c["offset"], c["why"]))
    A("")
    A("## 6. UNKNOWN - no such field in these layouts")
    A("")
    for i, u in enumerate(doc["unknowns"], 1):
        A("%d. **%s** - tried: %s. Where it would be: %s." % (i, u["what"], u["tried"],
                                                               u["where_it_would_be"]))
    A("")
    A("## 7. Oracles (`--check` re-runs all of them)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k, v in doc["oracles"].items():
        A("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:240]))
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"

    if args.write:
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote %s and %s" % (OUT_MD, OUT_JSON))
        print("classes: %s" % {k: v["size"] for k, v in doc["classes"].items()})
        print("observables: %d; candidates: %d; unknowns: %d"
              % (len(doc["observables"]), len(doc["candidates"]), len(doc["unknowns"])))
        bad = [k for k, o in doc["oracles"].items() if not o["ok"]]
        print("oracles: %d/%d ok%s" % (len(doc["oracles"]) - len(bad), len(doc["oracles"]),
                                       "" if not bad else " FAILED: " + ", ".join(bad)))
        return 0 if not bad else 1

    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    have_md = open(OUT_MD, encoding="utf-8").read()
    if stored != json.loads(js):
        fails.append("SAMPLER_FIELDS2.json is stale (BmSDK layouts changed)")
    if have_md != md:
        fails.append("SAMPLER_FIELDS2.md is stale (BmSDK layouts changed)")
    for k, o in doc["oracles"].items():
        if not o["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(o["detail"])[:300]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK %d classes, %d observables, %d candidates, %d unknowns; md+json byte-identical to a "
          "fresh rebuild" % (len(doc["classes"]), len(doc["observables"]),
                             len(doc["candidates"]), len(doc["unknowns"])))
    print("oracles: %s" % json.dumps({k: v["ok"] for k, v in doc["oracles"].items()},
                                     sort_keys=True))
    for area in ("inputs", "missiles", "boost", "eject"):
        rows = [(o["class"], o["field"], o["offset"], o["mask"]) for o in doc["observables"]
                if o["area"] == area]
        print("%s: %d fields, offsets %s" % (area, len(rows), [r[2] for r in rows]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
