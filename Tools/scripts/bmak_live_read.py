#!/usr/bin/env python3
"""bmak_live_read.py - READ-ONLY live read of six Batmobile values from the GOG Arkham Knight copy.

What it does (and nothing else)
  * OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION) on BatmanAK.exe, whose image path must be
    under E:\\Games\\BmAK-GOG-sdk (the operator-approved GOG copy). No write, no injection, no debugger, no
    dll, no input. This module never references WriteProcessMemory.
  * Walks the two primitives the GOG build already has, runtime-validated in
    tmp/freebuff/reports/bmsdk-gog-address-hunt.md:
        GNames     0x3A8E978   (entry 0 must be "None" - validated before every read)
        GObjObjects 0x347ACA4   (inline array; every live slot holds its own index at UObject.Index +0x30)
    Both are image-base offsets (module + offset), not absolute addresses.
  * Finds the live Batmobile instances by class name and prints named properties. Every name/offset/type is
    read at run time from Research/BatmobileGrab/BMSDK_OFFSETS.json - nothing is hardcoded here except the
    class/member names in SPEC below, and --check recomputes every offset from that JSON.

The six values the operator asked for, and what this script can actually say about each
  V1 LT battle-mode hold time - no property named *ModeSwitchHold*/"HoldTime" exists in BMSDK_OFFSETS.json,
     so the hold time itself is UNKNOWN; the script reads the adjacent decoded values instead (role labels:
     "nearest" vs "context" vs "value").  See Research/BatmobileGrab/ENTITY... no: see the DONE report.
  V2 eject charge window - same shape: MaxEjectType/EjectUpDist are decoded, the four RSpecialMoveConfig
     eject moves are named carriers (their durations live in RSpecialMoveConfig, which is not in the JSON).
  V3 steering curve at speed - FInterpCurveFloat read as a TArray of points; the 20-byte point stride is
     *derived* and is accepted only when the parse validates (InVal non-decreasing, InterpMode <= 4),
     otherwise the raw floats are printed and the parse is rejected.
  V4 HealthRecoverRate - ArrayProperty(float): reads TArray{Data,Num,Max} and the Num floats.
  V5 summon/homing numbers - RemoteCallIn state + RemoteSafePointLocation, RBatmobileMissile.HomingDelay.
  V6 physics asset in use - the view-mesh component pointer is resolved, then its first 0x600 bytes are
     scanned at 8-byte alignment for any pointer that lands on a live object of class "PhysicsAsset" (the
     class name comes from GNames, not from a guessed offset). Every PhysicsAsset object named *Batmobile*
     is listed as well.

Usage
    python Tools/scripts/bmak_live_read.py --check        # no game needed; verifies offsets + globals + ledger
    python Tools/scripts/bmak_live_read.py --selftest     # game running: proves the walker on 3 known classes
    python Tools/scripts/bmak_live_read.py                # game running: prints the six values
    python Tools/scripts/bmak_live_read.py --json out.json
    python Tools/scripts/bmak_live_read.py --any-build     # bypass the GOG-path guard (not used in the brief)

Exit codes: 0 ok, 1 --check mismatch, 2 exe/globals problem, 3 game not running (values UNKNOWN), 4 selftest fail.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bmak_runtime_sampler as s1  # noqa: E402  (read-only Proc/Engine, same OpenProcess flags)

GOG_ROOT = r"E:\Games\BmAK-GOG-sdk"
GOG_EXE_REL = os.path.join("Binaries", "Win64", "BatmanAK.exe")
GNAMES, GOBJ, GOBJ_KIND = 0x3A8E978, 0x347ACA4, "inline"
ADDR_REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "bmsdk-gog-address-hunt.md")
OFFSETS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
GRAB_OFFSETS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "OFFSETS.json")
LEDGER = os.path.join(ROOT, "tmp", "freebuff", "pre_t10", "T_ROWS.jsonl")

# ---------------------------------------------------------------------------------------------------------
# SPEC: what to read. `mode` says how to decode; `role` says whether the member IS the value ("value"),
# the closest decoded member when the exact one is absent ("nearest"), a named carrier object ("carrier"),
# or context ("context"). Offsets are NOT here: they come from BMSDK_OFFSETS.json by class+member.
# ---------------------------------------------------------------------------------------------------------
SPEC = [
    {
        "id": "V1",
        "label": "LT battle-mode hold time",
        "ledger_kw": r"battle mode|mode switch|transform",
        "items": [
            ("RVehicleBatmobileBase", "PreventModeSwitchDuration", "nearest", "float"),
            ("RVehicleBatmobileBase", "LastBattleModeControlledTime", "context", "float"),
            ("RVehicleBatmobileBase", "bBattleModeControlled", "context", "word"),
        ],
    },
    {
        "id": "V2",
        "label": "eject charge window (hold A to charge, tap A higher)",
        "ledger_kw": r"\beject",
        "items": [
            ("RVehicleBatmobileBase", "MaxEjectType", "nearest", "byte"),
            ("RVehicleBatmobileBase", "EjectUpDist", "nearest", "float"),
            ("RVehicleBatmobile", "EjectUpMove", "carrier", "ptr"),
            ("RVehicleBatmobile", "EjectToSpotMove", "carrier", "ptr"),
            ("RVehicleBatmobile", "EjectForwardMove", "carrier", "ptr"),
            ("RVehicleBatmobileBase", "OverrideNextEject", "context", "ptr"),
        ],
    },
    {
        "id": "V3",
        "label": "steering curve at speed",
        "ledger_kw": r"\bsteer",
        "items": [
            ("RVehicleSimBatmobile", "StandardSteeringSpeedCurve", "value", "curve"),
            ("RVehicleSimBatmobile", "BoostSteeringSpeedCurve", "context", "curve"),
            ("RVehicleSimBatmobile", "HandbrakeSteeringSpeedCurve", "context", "curve"),
            ("RVehicleSimBatmobile", "BattleModeSteerAngleFactor", "context", "float"),
            ("RVehicleSimCar", "SteerSpeedVsSpeedCurve", "value", "curve"),
            ("RVehicleSimCar", "SteeringReductionFactor", "context", "float"),
            ("RVehicleSimCar", "SteeringReductionSpeed", "context", "float"),
        ],
    },
    {
        "id": "V4",
        "label": "HealthRecoverRate (regen)",
        "ledger_kw": r"health|regen|recover",
        "items": [
            ("RVehicleBatmobileBase", "HealthRecoverRate", "value", "arrayf"),
            ("RVehicleBatmobileBase", "LowHealthWarningLevel", "context", "int"),
            ("RVehicle", "MaxHealth", "context", "int"),
        ],
    },
    {
        "id": "V5",
        "label": "summon / homing numbers",
        "ledger_kw": r"summon|homing|missile|tracker",
        "items": [
            ("RVehicleBatmobileBase", "RemoteCallIn", "value", "word"),
            ("RVehicleBatmobileBase", "RemoteSafePointLocation", "context", "vec3"),
            ("RVehicleBatmobileBase", "RemoteSafePointRotation", "context", "vec3"),
            ("RBatmobileMissile", "HomingDelay", "value", "float"),
            ("RBatmobileMissile", "bHoming", "context", "word"),
        ],
    },
    {
        "id": "V6",
        "label": "physics asset the running car uses",
        "ledger_kw": r"physics",
        "items": [
            ("RVehicleBatmobileBase", "BatmobileViewMesh", "carrier", "ptr"),
        ],
        "physics_asset": True,
    },
]
WANT_CLASSES = sorted({c for v in SPEC for (c, _m, _r, _k) in v["items"]} | {"Class", "PhysicsAsset"})
REV_CLASSES = {"PhysicsAsset"}
FMT = {"float": "f", "int": "i", "byte": "B", "word": "I"}


# ---------------------------------------------------------------------------------------------------------
# spec resolution + --check (no game needed)
# ---------------------------------------------------------------------------------------------------------
def load_offsets():
    d = json.load(open(OFFSETS_JSON, encoding="utf-8"))
    return d["classes"], d.get("schema"), d.get("source")


def resolve(classes):
    """[(value_id, item dict)] with offset/kind/type filled from BMSDK_OFFSETS.json."""
    out, missing = [], []
    for v in SPEC:
        for (cls, member, role, mode) in v["items"]:
            props = {p["name"]: p for p in classes.get(cls, {}).get("properties", [])}
            p = props.get(member)
            if not p:
                missing.append(f"{v['id']} {cls}.{member}")
                continue
            out.append({"value": v["id"], "cls": cls, "member": member, "role": role, "mode": mode,
                        "offset": int(p["offset"]), "kind": p["kind"], "type": p.get("type")})
    return out, missing


def check():
    classes, schema, source = load_offsets()
    items, missing = resolve(classes)
    bad = []
    print(f"BMSDK_OFFSETS.json schema {schema!r}, source {source!r}, {len(classes)} classes")

    # 1. every spec member exists, with the expected property kind for its decode mode
    kind_ok = {"float": "FloatProperty", "int": "IntProperty", "byte": "ByteProperty",
               "word": "BoolProperty", "ptr": None, "arrayf": "ArrayProperty", "curve": "StructProperty",
               "vec3": "StructProperty"}
    for it in items:
        want = kind_ok[it["mode"]]
        if want and it["kind"] != want:
            # bools and pointers are allowed to differ: 0x11D8-style bool words are BoolProperty, pointers vary
            bad.append(f"{it['cls']}.{it['member']}: kind {it['kind']} != {want} for mode {it['mode']}")
        if it["member"] == "HealthRecoverRate" and it["type"] != "float":
            bad.append("HealthRecoverRate is not float[]")
        if it["mode"] == "curve" and it["type"] != "FInterpCurveFloat":
            bad.append(f"{it['cls']}.{it['member']}: curve type {it['type']} != FInterpCurveFloat")
    print(f"spec items resolved: {len(items)}; unresolved: {len(missing)}")
    for m in missing:
        bad.append("missing member " + m)

    # 2. the GOG globals in this file equal the ones decoded in the address-hunt report (text, not memory)
    txt = open(ADDR_REPORT, encoding="utf-8", errors="ignore").read()
    for sym, val in (("GNames", GNAMES), ("GObjObjects", GOBJ)):
        m = re.search(r"inline constexpr uintptr_t " + sym + r"\s*=\s*0x([0-9A-Fa-f]+)", txt)
        if not m:
            bad.append(f"{sym} not found in {os.path.relpath(ADDR_REPORT, ROOT)}")
        elif int(m.group(1), 16) != val:
            bad.append(f"{sym}: file 0x{val:X} != report 0x{int(m.group(1), 16):X}")
        else:
            print(f"{sym} 0x{val:X} == bmsdk-gog-address-hunt.md")

    # 3. the six values still map onto ledger rows (row ids are read from the ledger, never invented)
    gaps = []
    if os.path.exists(LEDGER):
        rows = []
        for line in open(LEDGER, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        gaps = []
        for v in SPEC:
            hits = [r["id"] for r in rows
                    if re.search(v["ledger_kw"],
                                 " ".join(str(c) for c in r.get("cells", [])) + " " + r.get("section", ""), re.I)]
            print(f"{v['id']} {v['label']!r}: ledger rows {hits or 'NONE'}")
            if not hits:
                gaps.append(f"{v['id']} ({v['label']})")
        print(f"ledger GAPs (value feeds no existing row - a new row is needed): {gaps or 'none'}")
    else:
        print("ledger not found, ledger join skipped:", os.path.relpath(LEDGER, ROOT))

    # 4. the two JSONs must describe the same classes for the spec classes (cross-file oracle)
    g = json.load(open(GRAB_OFFSETS_JSON, encoding="utf-8"))
    gfields = {(f.get("class"), f.get("member")) for f in g.get("fields", [])}
    gclasses = {c for (c, _m) in gfields if c}
    for it in items:
        if it["cls"] in gclasses:
            note = "also in OFFSETS.json" if (it["cls"], it["member"]) in gfields else "class only"
            print(f"  cross-file: {it['cls']}.{it['member']} {note}")

    print(f"\n--check: {len(bad)} problem(s), {len(gaps)} ledger gap(s)")
    for b in bad:
        print("  ", b)
    return 1 if bad else 0


# ---------------------------------------------------------------------------------------------------------
# read-only walker (own copy: it must also record CDOs and a reverse class->name map, which Engine.find drops)
# ---------------------------------------------------------------------------------------------------------
def walk(e, p, want, rev_classes, max_slots=3_000_000):
    found = {c: [] for c in want}
    rev = {}
    CH, zeros, i = 4096, 0, 0
    while i < max_slots and zeros < 50_000:
        raw = p.read(e.slots + 8 * i, 8 * CH)
        if not raw:
            break
        for k, o in enumerate(struct.unpack(f"<{CH}Q", raw)):
            if not o:
                zeros += 1
                continue
            zeros = 0
            if p.u(o + s1.U_INDEX, "i") != i + k:      # a live slot holds its own index
                continue
            cn = e.class_name(o)
            if cn in want:
                found[cn].append(o)          # CDOs are kept: --selftest needs Default__<class>
            if cn in rev_classes:
                rev[o] = (cn, e.obj_name(o))
        i += CH
    return found, rev, i


def describe(e, ptr):
    if not ptr:
        return None
    cls, nm = e.class_name(ptr), e.obj_name(ptr)
    if not cls and not nm:
        return f"0x{ptr:x} (not an object)"
    return f"{cls}:{nm}"


def read_curve(p, base):
    d = p.u(base, "Q")
    num, mx = p.u(base + 8, "i"), p.u(base + 12, "i")
    out = {"Data": hex(d) if d else None, "Num": num, "Max": mx}
    if not d or num is None or num <= 0 or num > 4096:
        out["points"] = None
        return out
    n = min(num, 8)
    raw = p.read(d, 4 * n)
    out["first_floats"] = [round(x, 5) for x in struct.unpack("<%df" % n, raw)] if raw else None
    # derived layout: FInterpCurvePointFloat = InVal, OutVal, ArriveTangent, LeaveTangent (4x float) + byte mode
    pts = []
    blob = p.read(d, 20 * min(num, 16))
    if blob:
        ok = True
        for j in range(0, len(blob) - 19, 20):
            iv, ov, at, lt = struct.unpack_from("<4f", blob, j)
            mode = blob[j + 16]
            pts.append({"InVal": round(iv, 5), "OutVal": round(ov, 5), "Arrive": round(at, 4),
                        "Leave": round(lt, 4), "InterpMode": mode})
            if mode > 4 or not (-1e6 < iv < 1e6) or not (-1e6 < ov < 1e6):
                ok = False
        for a, b in zip(pts, pts[1:]):
            if b["InVal"] < a["InVal"]:
                ok = False
        out["points"] = pts if ok else None
        out["points_rejected"] = None if ok else "stride-20 parse failed validation (InVal/mode)"
    return out


def read_item(p, e, base, it):
    off = it["offset"]
    mode = it["mode"]
    a = base + off
    if mode in FMT:
        return p.u(a, FMT[mode])
    if mode == "ptr":
        v = p.u(a, "Q")
        return {"ptr": hex(v) if v else None, "object": describe(e, v)}
    if mode == "vec3":
        raw = p.read(a, 12)
        return [round(x, 4) for x in struct.unpack("<3f", raw)] if raw else None
    if mode == "arrayf":
        d, num, mx = p.u(a, "Q"), p.u(a + 8, "i"), p.u(a + 12, "i")
        rec = {"Data": hex(d) if d else None, "Num": num, "Max": mx}
        if d and num and 0 < num <= 4096:
            raw = p.read(d, 4 * min(num, 128))
            rec["values"] = [round(x, 5) for x in struct.unpack("<%df" % min(num, 128), raw)] if raw else None
        return rec
    if mode == "curve":
        return read_curve(p, a)
    raise AssertionError(mode)


def live(p, insts):
    """Drop class-default objects (playing a CDO would be reading template values); keep them if nothing else."""
    real = [a for a in insts if not ((p.u(a + s1.U_FLAGS, "i") or 0) & s1.RF_CDO)]
    return real or list(insts)


def read_all(p, e, found, rev):
    """{value_id: [(item, instance_addr, decoded)]} plus the per-value UNKNOWN notes."""
    res = {}
    for v in SPEC:
        rows = []
        for it in [i for i in ITEMS if i["value"] == v["id"]]:
            insts = live(p, found.get(it["cls"]) or []) or live(p, found.get(inherited_parent(it["cls"])) or [])
            for addr in insts[:4]:
                rows.append((it, addr, read_item(p, e, addr, it)))
            if not insts:
                rows.append((it, None, "NO LIVE INSTANCE of " + it["cls"]))
        entry = {"label": v["label"], "rows": rows}
        if v.get("physics_asset"):
            entry["physics_asset"] = physics_assets(p, e, found, rev)
        res[v["id"]] = entry
    return res


def inherited_parent(cls):
    """RVehicleBatmobileBase's properties are readable from a RVehicleBatmobile instance (UE3 keeps the
    inherited offset), so an instance of the child satisfies an item declared on the parent."""
    return {"RVehicleBatmobileBase": "RVehicleBatmobile", "RVehicleSimCar": "RVehicleSimBatmobile"}.get(cls, cls)


def physics_assets(p, e, found, rev):
    out = {"named_objects": [[hex(a), r[0], r[1]] for a, r in rev.items() if "batmobile" in (r[1] or "").lower()],
           "scanned": []}
    comp_cls = "RVehicleBatmobileBase"
    comp_off = next((i["offset"] for i in ITEMS if i["member"] == "BatmobileViewMesh"), None)
    for addr in (found.get(comp_cls) or found.get("RVehicleBatmobile") or [])[:4]:
        comp = p.u(addr + comp_off, "Q") if comp_off is not None else None
        if not comp:
            continue
        blob = p.read(comp, 0x600)
        hits = []
        if blob:
            for j in range(0, len(blob) - 7, 8):
                v = struct.unpack_from("<Q", blob, j)[0]
                if v in rev:
                    hits.append({"component": describe(e, comp), "offset_in_component": hex(j),
                                 "class": rev[v][0], "object": rev[v][1]})
        out["scanned"].append({"vehicle": hex(addr), "component": describe(e, comp), "hits": hits})
    return out


# ---------------------------------------------------------------------------------------------------------
# live session
# ---------------------------------------------------------------------------------------------------------
ITEMS = []


def gog_exe():
    return os.path.join(GOG_ROOT, GOG_EXE_REL)


def image_path(pid):
    import ctypes
    import ctypes.wintypes as W
    h = s1.k32.OpenProcess(s1.PROCESS_QUERY_LIMITED, False, pid)
    if not h:
        return None
    buf = ctypes.create_unicode_buffer(520)
    n = W.DWORD(520)
    ok = s1.k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
    s1.k32.CloseHandle(h)
    return buf.value if ok else None


def attach(any_build=False):
    pid = s1.find_pid("BatmanAK.exe")
    if not pid:
        return None, None, None
    img = image_path(pid) or ""
    if not any_build and not os.path.normcase(img).startswith(os.path.normcase(GOG_ROOT)):
        raise SystemExit(f"refusing: pid {pid} image {img!r} is not under {GOG_ROOT!r} (use --any-build)")
    p = s1.Proc(pid)
    e = s1.Engine(p, GNAMES, GOBJ, GOBJ_KIND)
    return pid, p, e


def selftest(p, e):
    """Three classes known from the grab: each UClass object must exist under class 'Class', and its
    'Default__<name>' CDO must exist under that same class. Both come from GNames/GObjObjects only."""
    names = ["RVehicleBatmobile", "RVehicleSimBatmobile", "RBatmobileMissileLauncher"]
    found, _rev, slots = walk(e, p, set(names) | {"Class"}, set())
    bad = []
    print(f"walked {slots} object slots; found class objects for {names}")
    for n in names:
        cls_objs = [a for a in found.get("Class", []) if e.obj_name(a) == n]
        cdos = [a for a in found.get(n, []) if e.obj_name(a) == "_".join(["Default", "", n])]
        print(f"  {n}: UClass objects {len(cls_objs)} at {[hex(a) for a in cls_objs][:3]}; "
              f"CDOs {len(cdos)} at {[hex(a) for a in cdos][:3]}")
        if not cls_objs:
            bad.append(f"{n}: no UClass object named {n}")
        if not cdos:
            bad.append(f"{n}: no Default__{n} CDO")
    print(f"selftest: {'PASS' if not bad else 'FAIL'}")
    for b in bad:
        print("  ", b)
    return 0 if not bad else 4


def show(res, e):
    for vid, entry in res.items():
        print(f"\n== {vid}  {entry['label']}")
        for it, addr, val in entry["rows"]:
            tag = f"{it['cls']}.{it['member']} +{it['offset']} ({it['kind']}/{it['type']})"
            inst = "no instance" if addr is None else describe(e, addr)
            print(f"  [{it['role']:7}] {tag}\n            on {inst}\n            = {val}")
        if "physics_asset" in entry:
            pa = entry["physics_asset"]
            print("  [value  ] objects of class PhysicsAsset named *batmobile*:", pa["named_objects"] or "NONE")
            for sc in pa["scanned"]:
                print(f"            view mesh {sc['component']} on {sc['vehicle']}: "
                      f"PhysicsAsset pointers {sc['hits'] or 'NONE in first 0x600 bytes'}")

    print("""
UNKNOWN (no property named for it in BMSDK_OFFSETS.json / OFFSETS.json - do not read these as the value):
  V1 the LT hold duration itself; V2 the eject charge window / charge time itself (only MaxEjectType and the
  RSpecialMoveConfig carrier objects are named); V5 homing speed/accel constants beyond HomingDelay.""")


def run_steps():
    exe = gog_exe()
    return f"""
BatmanAK.exe is not running, so the six values are UNKNOWN. Nothing was launched (the brief allows launching
the GOG copy, but no launch was needed to write and check this reader).

Run steps (operator):
  1. start the game from the GOG copy:  "{exe}"
     (read-only attach is allowed from briefs 7993-7994; this script only reads)
  2. once the Batmobile is spawned and being driven, in another shell:
         cd {ROOT}
         uv run python Tools/scripts/bmak_live_read.py --selftest
         uv run python Tools/scripts/bmak_live_read.py --json Research/BatmobileGrab/live_batmobile.json
  3. to stop: close the game yourself. This script never kills a process; if a kill is ever needed it must be
     taskkill /PID <the exact pid printed by this script> - never by image name.
Expected exe path: {exe} (exists: {os.path.exists(exe)})
"""


def main(argv):
    global ITEMS
    ap = argparse.ArgumentParser(description="read-only live read of six Batmobile values (GOG AK)")
    ap.add_argument("--check", action="store_true", help="verify spec offsets against the JSONs (no game)")
    ap.add_argument("--selftest", action="store_true", help="prove the walker on three known classes")
    ap.add_argument("--json", metavar="PATH", help="write the decoded values as JSON")
    ap.add_argument("--any-build", action="store_true", help="skip the GOG-path guard")
    a = ap.parse_args(argv)

    if a.check:
        return check()

    classes, _schema, _src = load_offsets()
    ITEMS, missing = resolve(classes)
    if missing:
        print("spec members missing from BMSDK_OFFSETS.json:", missing)
        return 2

    pid, p, e = attach(a.any_build)
    if not pid:
        print(run_steps())
        return 3
    print(f"attached READ-ONLY to pid {pid}, image {image_path(pid)}, base {p.base:#x}")
    print(f"GNames {GNAMES:#x} validated (entry 0 = {e.name(0)!r}), GObjObjects {GOBJ:#x} ({GOBJ_KIND})")

    if a.selftest:
        return selftest(p, e)

    found, rev, slots = walk(e, p, set(WANT_CLASSES), REV_CLASSES)
    print(f"walked {slots} slots; live instances: { {k: len(v) for k, v in found.items()} }")
    print(f"PhysicsAsset objects in the process: {len(rev)}")
    res = read_all(p, e, found, rev)
    show(res, e)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"pid": pid, "image": image_path(pid), "GNames": hex(GNAMES), "GObjObjects": hex(GOBJ),
                       "values": {k: {"label": v["label"],
                                      "rows": [{"class": i["cls"], "member": i["member"], "role": i["role"],
                                                "offset": i["offset"], "kind": i["kind"], "type": i["type"],
                                                "instance": describe(e, ad) if ad else None,
                                                "value": val} for i, ad, val in v["rows"]],
                                      **({"physics_asset": v["physics_asset"]} if "physics_asset" in v else {})}
                                  for k, v in res.items()}}, f, indent=1)
        print("wrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
