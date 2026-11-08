"""bmak_runtime_sampler2.py - G3-02f follow-up: READ-ONLY sampler for the inputs/gadget state sampler 1 never read.

Reuses bmak_runtime_sampler (same read-only OpenProcess, same GNames/GObjObjects validation). Nothing is written to
the game. Offsets are the decoded ones in Research/BatmobileGrab/SAMPLER_FIELDS2.md (BmSDK-AK Generated/*.g.cs).

What is new vs sampler 1:
  * RPlayerInput raw button bytes 768..799 (every byte, change-logged as in0.b<offset>) - this is how the X / Y / A
    bytes are FOUND (press one button at a time, read which byte flips). The X and A bytes are UNKNOWN in the layout.
  * RBatmobileBooster (bBoosting/bWarming word), RBatmobileMissileLauncher (targets, state, cooldowns, arrays' Num),
    eject fields on the vehicle and the controller, boost fields on the vehicle.

    python bmak_runtime_sampler2.py --check    # offsets below == SAMPLER_FIELDS2.md rows (no game needed)
    python bmak_runtime_sampler2.py --probe    # attach, list objects found per class, one snapshot, exit
    python bmak_runtime_sampler2.py            # log changes to Research/BatmobileGrab/runtime/samples2-<utc>.jsonl
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmak_runtime_sampler as s1  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIELDS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SAMPLER_FIELDS2.md")
OUT = s1.OUT

# class -> {log key: (qualified name in SAMPLER_FIELDS2.md, offset, struct fmt)}
FIELDS = {
    "RPlayerInput": {
        "bReadyGadgetButton": ("RPlayerInput.bReadyGadgetButton", 773, "B"),
        "bBatmobileEjectModifier": ("RPlayerInput.bBatmobileEjectModifier", 786, "B"),
        "bVehicleBoostButton": ("RPlayerInput.bVehicleBoostButton", 781, "B"),
        "bFireVehicleWeapon": ("RPlayerInput.bFireVehicleWeapon", 778, "B"),
        "bFireVehicleSecondaryWeapon": ("RPlayerInput.bFireVehicleSecondaryWeapon", 779, "B"),
        "bGadgetSelectWheel": ("RPlayerInput.bGadgetSelectWheel", 784, "B"),
        "aThrottleAxis": ("RPlayerInput.aThrottleAxis", 840, "f"),
        "aBrakeAxis": ("RPlayerInput.aBrakeAxis", 844, "f"),
    },
    "RBatmobileBooster": {
        "boostword": ("RBatmobileBooster.bBoosting", 2396, "I"),     # bit 1 bBoosting, bit 2 bWarming
        "CoolDown": ("RVehicleWeapon.CoolDown", 2092, "f"),
    },
    "RBatmobileMissileLauncher": {
        "weaponword": ("RVehicleWeapon.bFiring", 2084, "I"),          # bit 2 bFiring, bit 1 ContinuousFire
        "CoolDown": ("RVehicleWeapon.CoolDown", 2092, "f"),
        "WeaponCoolDown": ("RVehicleWeapon.WeaponCoolDown", 2096, "f"),
        "NthTarget": ("RBatmobileMissileLauncher.NthTarget", 2560, "i"),
        "LastStateIdx": ("RBatmobileMissileLauncher.LastState", 2564, "i"),
        "CurrentLevel": ("RBatmobileMissileLauncher.CurrentLevel", 2588, "i"),
        "CurrentMissileSocket": ("RBatmobileMissileLauncher.CurrentMissileSocket", 2624, "i"),
        "InfinitMissilesTime": ("RBatmobileMissileLauncher.InfinitMissilesTime", 2628, "f"),
        "CurrentTargetsNum": ("RBatmobileMissileLauncher.CurrentTargets", 2400 + 8, "i"),   # TArray Num at +8
        "LastTargetsNum": ("RBatmobileMissileLauncher.LastTargets", 2416 + 8, "i"),
        "FiredProjectilesNum": ("RBatmobileMissileLauncher.FiredProjectiles", 2632 + 8, "i"),
        "AimTarget": ("RVehicleWeapon.AimTarget", 2168, "Q"),
    },
    "RVehicleBatmobile": {
        "BoostingOut": ("RVehicleBatmobileBase.BoostingOut", 5901, "B"),
        "MaxEjectType": ("RVehicleBatmobileBase.MaxEjectType", 5902, "B"),
        "EjectUpDist": ("RVehicleBatmobileBase.EjectUpDist", 6032, "f"),
        "OverrideNextEject": ("RVehicleBatmobileBase.OverrideNextEject", 5604, "Q"),
        "LastBoostPickupTime": ("RVehicleBatmobileBase.LastBoostPickupTime", 6580, "f"),
        "AfterburnerSystem": ("RVehicleBatmobileBase.AfterburnerSystem", 4636, "Q"),
        "boostflags11D8": ("RVehicleBatmobileBase.bBoostLocked", 0x11D8, "I"),
    },
    "RPlayerController": {
        "CurrentEjectType": ("RPlayerController.CurrentEjectType", 3502, "B"),
        "LastEjectFromBatmobileTime": ("RPlayerController.LastEjectFromBatmobileTime", 7188, "f"),
        "quickgadgetword": ("RPlayerController.UsedQuickGadget", 3452, "I"),
    },
}
PTR_KEYS = {"AimTarget", "OverrideNextEject", "AfterburnerSystem"}
RAW_LO, RAW_HI = 768, 800          # RPlayerInput button-byte region (773..790 hold the known buttons)


def check():
    md = open(FIELDS_MD, encoding="utf-8").read()
    bad, n = [], 0
    for cls, fs in FIELDS.items():
        for key, (qual, off, _fmt) in fs.items():
            n += 1
            m = re.search(r"\| `" + re.escape(qual) + r"` \| (\d+)\b", md)
            if not m:
                bad.append(f"{cls}.{key}: {qual} not in SAMPLER_FIELDS2.md"); continue
            want = int(m.group(1))
            if "Num" in key:
                want += 8                         # the md row gives the TArray start; Num is +8
            if want != off:
                bad.append(f"{cls}.{key}: script {off} != md {want}")
    print(f"checked {n} fields against SAMPLER_FIELDS2.md; {len(bad)} mismatches")
    for b in bad:
        print("  ", b)
    return 1 if bad else 0


def main():
    if "--check" in sys.argv:
        raise SystemExit(check())
    pid = s1.find_pid()
    if not pid:
        raise SystemExit("BatmanAK.exe is not running")
    p = s1.Proc(pid)
    j = json.load(open(s1.LOC)) if os.path.exists(s1.LOC) else None
    e = s1.Engine(p, int(j["GNames_rva"], 16), int(j["GObjObjects_rva"], 16), j.get("GObjObjects_kind", "inline")) \
        if j else s1.Engine(p)
    classes = list(FIELDS)
    objs = e.find(classes)
    print(f"attached read-only to pid {pid}; objects per class:",
          {c: [hex(x) for x in v] for c, v in objs.items()})
    missing = [c for c in classes if not objs[c]]
    if missing:
        print("NOT FOUND (no live instance now; they are re-searched every 10 s):", missing)

    def snapshot():
        now = {}
        for cls, fs in FIELDS.items():
            for i, o in enumerate(objs.get(cls, [])):
                for key, (_q, off, fmt) in fs.items():
                    v = p.u(o + off, fmt)
                    if key in PTR_KEYS:
                        v = f"{e.class_name(v)}:{e.obj_name(v)}" if v else None
                    elif key == "LastStateIdx" and v is not None:
                        v = e.name(v)
                    now[f"{cls}{i}.{key}"] = round(v, 3) if isinstance(v, float) else v
                if cls == "RPlayerInput":
                    raw = p.read(o + RAW_LO, RAW_HI - RAW_LO)
                    if raw:
                        for k, b in enumerate(raw):
                            now[f"in{i}.b{RAW_LO + k}"] = b
        return now

    if "--probe" in sys.argv:
        print(json.dumps(snapshot(), indent=1))
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "samples2-" + datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + ".jsonl")
    last, t_find = {}, time.time()
    with open(path, "w", encoding="utf-8") as f:
        print("logging to", path, "- Ctrl+C to stop")
        print("MARKERS: type a label (e.g. 'X reverse start') + Enter right as you press; it is logged with a timestamp")

        def markers():
            for line in sys.stdin:
                rec = {"t": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
                       "marker": line.strip()}
                f.write(json.dumps(rec) + "\n"); f.flush()
                print(rec["t"][11:23], "MARKER", rec["marker"])
        threading.Thread(target=markers, daemon=True).start()
        while True:
            if time.time() - t_find > 10:
                objs = e.find(classes); t_find = time.time()
            now = snapshot()
            ch = {k: v for k, v in now.items() if last.get(k) != v}
            if ch:
                rec = {"t": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z", "changed": ch}
                f.write(json.dumps(rec) + "\n"); f.flush()
                print(rec["t"][11:23], ch)
            last = now
            time.sleep(0.05)


if __name__ == "__main__":
    main()
