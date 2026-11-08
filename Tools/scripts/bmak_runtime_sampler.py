"""bmak_runtime_sampler.py - G3-02d: READ-ONLY runtime observation of BmAK's Batmobile controls.

Opens BatmanAK.exe with PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION only (no write, no injection, no
debugger attach - the exe's single IsDebuggerPresent import is not involved). Finds objects through the engine's
own tables and logs every change of the watched fields, with timestamps, while the user presses the inputs.

Sources (every offset is decoded elsewhere, not guessed):
  GNames 0x3A208B8 / GObjObjects 0x340CBE4 (module-relative)  BmSDK-AK main-bm4 GameDefine.Steam.cs (MIT)
    -> VALIDATED at start: GNames[0] must read "None", or the sampler stops (wrong build).
  UObject (pack 4): +0x08 ObjectFlags, +0x3C Name (FName index,number), +0x44 Class      BmSDK UObject.h
  FNameEntry: +0 Index (bit 0x2 = text by pointer), +12 text or pointer                 BmSDK FName.cs
  GObjObjects: 785000 inline pointers, then Unk, Num, Max (int32)                        BmSDK TObjArray.cs
  RVehicleBatmobileBase: 0x11D8/0x11DC/0x11E0 bool words, 0x1707 BatmanVsBatmobileCollisionMode,
    0x1908 CurrentThrottle, 0x1990 PreventModeSwitchDuration           Research/BatmobileGrab/BMSDK_OFFSETS.json
  Vehicle.Driver +1480                                                  BMSDK_OFFSETS.json
  Controller.Pawn +668, PlayerController.PlayerInput +1240, RPlayerController.LastTriggerAmount +7232,
  RPlayerInput aRightTrigger +720, aLeftTrigger +724, aLeftShoulder +760, bCancelButton +774, aThrottleAxis +840
                                                                        BmSDK Generated/*.g.cs
Out: Research/BatmobileGrab/runtime/samples-<utc>.jsonl (one line per change) + console transitions.

    python bmak_runtime_sampler.py --probe     # validate globals + list the found objects, then exit
    python bmak_runtime_sampler.py             # sample until Ctrl+C
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as W
import datetime
import json
import os
import struct
import sys
import time

GNAMES, GOBJ = 0x3A208B8, 0x340CBE4
GOBJ_INLINE = 785000
U_FLAGS, U_NAME, U_CLASS = 0x08, 0x3C, 0x44
RF_CDO = 0x80
VEH = {"flags_11D8": (0x11D8, "I"), "flags_11DC": (0x11DC, "I"), "flags_11E0": (0x11E0, "I"),
       "BatmanVsBatmobileCollisionMode": (0x1707, "B"), "CurrentThrottle": (0x1908, "f"),
       "PreventModeSwitchDuration": (0x1990, "f"), "Driver": (1480, "Q"),
       # weapons / targeting (BMSDK_OFFSETS.json RVehicleBatmobileBase)
       "CurrentWeapon": (0x130C, "Q"), "SecondaryWeapon": (0x1314, "Q"),
       "PursuitModePrimaryWeapon": (0x1474, "Q"), "BattleModePrimaryWeapon": (0x147C, "Q"),
       "CurrentStrafeTarget": (0x14EC, "Q"), "WeaponUnavailableReason": (0x170B, "B"),
       "WeaponGeneratorPower": (0x1EE8, "f")}
PTRS = {"CurrentWeapon", "SecondaryWeapon", "PursuitModePrimaryWeapon", "BattleModePrimaryWeapon",
        "CurrentStrafeTarget", "LockOnTarget", "TagTarget", "AimTarget"}
# BmSDK Generated/BmGame: RVehicleWeapon.bFiring +2084 bit 0x2, AimTarget +2168 (both gadgets inherit it);
# RBatmobileEMPMissile LockOnTarget +2468, TagTarget +2484, LockOnTime +2540, MissileAnimState +2605,
# bTryingToAcquireNewTarget +2608 bit 0x1
GADGETS = {"RBatmobileEMPMissile": {"weaponflags": (2084, "I"), "AimTarget": (2168, "Q"), "LockOnTarget": (2468, "Q"),
                                    "TagTarget": (2484, "Q"), "LockOnTime": (2540, "f"),
                                    "MissileAnimState": (2605, "B"), "acquireflags": (2608, "I")},
           "RBatmobileVehicleTracker": {"weaponflags": (2084, "I"), "AimTarget": (2168, "Q")}}
BITS_11D8 = {0x2: "ArmouredMode", 0x4: "ArmouredModeOld", 0x8: "bTransforming", 0x10: "bWeaponsReady",
             0x4000: "bBoostLocked", 0x8000: "bBattleModeLocked", 0x10000: "bLockInBattleMode",
             0x80000: "bCockpitOpen", 0x40000000: "DisabledByEMP"}
PC = {"LastTriggerAmount": (7232, "f"), "Pawn": (668, "Q"), "PlayerInput": (1240, "Q")}
PI = {"aRightTrigger": (720, "f"), "aLeftTrigger": (724, "f"), "aLeftShoulder": (760, "B"),
      "bCancelButton": (774, "B"), "aThrottleAxis": (840, "f")}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "Research", "BatmobileGrab", "runtime")

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
PROCESS_VM_READ, PROCESS_QUERY_LIMITED = 0x0010, 0x1000


def find_pid(name="BatmanAK.exe"):
    arr = (W.DWORD * 4096)(); got = W.DWORD()
    psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(got))
    for pid in arr[: got.value // 4]:
        h = k32.OpenProcess(PROCESS_QUERY_LIMITED, False, pid)
        if not h:
            continue
        buf = ctypes.create_unicode_buffer(520); n = W.DWORD(520)
        ok = k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
        k32.CloseHandle(h)
        if ok and buf.value.lower().endswith(name.lower()):
            return pid
    return None


class Proc:
    def __init__(self, pid):
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED, False, pid)
        if not self.h:
            raise SystemExit(f"OpenProcess(read-only) failed: {ctypes.get_last_error()}")
        mods = (ctypes.c_void_p * 1024)(); need = W.DWORD()
        psapi.EnumProcessModulesEx(self.h, mods, ctypes.sizeof(mods), ctypes.byref(need), 0x03)
        self.base = mods[0]

    def read(self, addr, n):
        buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
        if not k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)) or got.value != n:
            return None
        return buf.raw

    def u(self, addr, fmt):
        b = self.read(addr, struct.calcsize("<" + fmt))
        return None if b is None else struct.unpack("<" + fmt, b)[0]


LOC = os.path.join(OUT, "globals.json")
U_INDEX = 0x30


def data_section(exe_path):
    """(rva, size) of the PE's .data section, read from the file on disk (no pefile needed)."""
    with open(exe_path, "rb") as f:
        h = f.read(4096)
    pe = struct.unpack_from("<I", h, 0x3C)[0]
    nsec, opt = struct.unpack_from("<H", h, pe + 6)[0], struct.unpack_from("<H", h, pe + 20)[0]
    sec = pe + 24 + opt
    for i in range(nsec):
        name = h[sec + 40 * i: sec + 40 * i + 8].rstrip(b"\0")
        vsize, rva = struct.unpack_from("<II", h, sec + 40 * i + 8)
        if name == b".data":
            return rva, vsize
    raise SystemExit("no .data section")


def locate(p: Proc, exe_path):
    """GOG/unknown build: find GNames and GObjObjects in .data by self-validating structure (read-only)."""
    rva, size = data_section(exe_path)
    blob = bytearray()
    for o in range(0, size, 1 << 20):
        blob += p.read(p.base + rva + o, min(1 << 20, size - o)) or b"\0" * min(1 << 20, size - o)
    q = lambda off: struct.unpack_from("<Q", blob, off)[0]
    isptr = lambda v: 0x10000 < v < 0x7FFFFFFFFFFF

    def text(e):
        flag = p.u(e, "i")
        if flag is None:
            return None
        raw = p.read(p.u(e + 12, "Q"), 32) if flag & 0x2 else p.read(e + 12, 32)
        return raw.split(b"\0")[0] if raw else None
    gnames = None
    for off in range(0, len(blob) - 16, 8):           # TArray<FNameEntry*>: Data, Num, Max
        d = q(off); num, mx = struct.unpack_from("<ii", blob, off + 8)
        if not isptr(d) or not (10000 < num <= mx < 5_000_000):
            continue
        a = p.read(d, 16)
        if a and text(struct.unpack_from("<Q", a, 0)[0]) == b"None" and \
                text(struct.unpack_from("<Q", a, 8)[0]) == b"ByteProperty":
            gnames = rva + off; break
    gobj, gobj_kind = None, None
    def objs_ok(base_addr_reader, n=16):
        for k in range(n):
            o = base_addr_reader(k)
            if not isptr(o) or p.u(o + U_INDEX, "i") != k:
                return False
        return True
    # Steam's GObjObjects (0x340CBE4) is only 4-byte aligned: step 4, not 8.
    for off in range(0, len(blob) - 136, 4):
        a0 = q(off)
        if not isptr(a0):
            continue
        # (a) inline array of UObject*: obj[k].Index == k
        if isptr(q(off + 8)) and objs_ok(lambda k: q(off + 8 * k)):
            gobj, gobj_kind = rva + off, "inline"; break
        # (b) TArray{Data, Num, Max}: Data[k].Index == k
        num, mx = struct.unpack_from("<ii", blob, off + 8)
        if 50000 < num <= mx < 5_000_000:
            arr = p.read(a0, 8 * 16)
            if arr and objs_ok(lambda k: struct.unpack_from("<Q", arr, 8 * k)[0]):
                gobj, gobj_kind = rva + off, "tarray"; break
    if gnames is None or gobj is None:
        raise SystemExit(f"locate failed: GNames {hex(gnames) if gnames else None}, GObjObjects {gobj}")
    rec = {"exe": exe_path, "GNames_rva": hex(gnames), "GObjObjects_rva": hex(gobj), "GObjObjects_kind": gobj_kind,
           "how": "GNames: .data TArray{Data,Num,Max} with [0]='None',[1]='ByteProperty'; GObjObjects: 16 objects "
                  "with UObject.Index (+0x30) == array position, inline or via TArray Data (4-byte step)"}
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(LOC, "w"), indent=1)
    print("located:", rec)
    return gnames, gobj


class Engine:
    def __init__(self, p: Proc, gnames=GNAMES, gobj=GOBJ, kind="inline"):
        self.p = p
        # slot base: inline array lives at the global; a TArray's Data pointer is read from it
        self.slots = p.base + gobj if kind == "inline" else p.u(p.base + gobj, "Q")
        self.gobj = gobj
        self.names_arr = p.u(p.base + gnames, "Q")
        if not self.names_arr or self.name(0) != "None":
            raise SystemExit(f"GNames validation FAILED (entry 0 = {self.name(0)!r}) - not the BmSDK Steam build; "
                             "stop, offsets do not apply")
        self.num = None   # walked, not read: the inline capacity differs per build
        self._cls = {}

    def name(self, idx):
        e = self.p.u(self.names_arr + 8 * idx, "Q") if self.names_arr else None
        if not e:
            return None
        flag = self.p.u(e, "i") or 0
        if flag & 0x2:
            ptr = self.p.u(e + 12, "Q"); raw = self.p.read(ptr, 96) if ptr else None
        else:
            raw = self.p.read(e + 12, 96)
        return raw.split(b"\0")[0].decode("latin-1") if raw else None

    def obj_name(self, o):
        b = self.p.read(o + U_NAME, 8)
        if not b:
            return None
        i, n = struct.unpack("<ii", b); s = self.name(i)
        return s if not n else f"{s}_{n - 1}"

    def class_name(self, o):
        c = self.p.u(o + U_CLASS, "Q")
        if c not in self._cls:
            self._cls[c] = self.obj_name(c) if c else None
        return self._cls[c]

    def find(self, wanted):
        out = {w: [] for w in wanted}
        CH, zeros, i = 4096, 0, 0
        while i < 3_000_000 and zeros < 50_000:         # walk until a long empty tail
            raw = self.p.read(self.slots + 8 * i, 8 * CH)
            if not raw:
                break
            for k, o in enumerate(struct.unpack(f"<{CH}Q", raw)):
                if not o:
                    zeros += 1; continue
                zeros = 0
                if self.p.u(o + U_INDEX, "i") != i + k:   # every live slot must hold its own index
                    continue
                cn = self.class_name(o)
                if cn in out and not ((self.p.u(o + U_FLAGS, "i") or 0) & RF_CDO):
                    out[cn].append(o)
            i += CH
        self.num = i
        return out


def snap(p, o, fields):
    return {k: p.u(o + off, fmt) for k, (off, fmt) in fields.items()}


def bits(v):
    return [n for m, n in BITS_11D8.items() if v is not None and v & m]


def main():
    pid = find_pid()
    if not pid:
        raise SystemExit("BatmanAK.exe is not running")
    p = Proc(pid)
    exe = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"
    if "--locate" in sys.argv or os.path.exists(LOC):
        if "--locate" in sys.argv or not os.path.exists(LOC):
            locate(p, exe)
        j = json.load(open(LOC))
        e = Engine(p, int(j["GNames_rva"], 16), int(j["GObjObjects_rva"], 16), j.get("GObjObjects_kind", "inline"))
    else:
        e = Engine(p)
    objs = e.find(["RVehicleBatmobile", "RPlayerController", "RPlayerInput", "RBatmobileEMPMissile", "RBatmobileVehicleTracker"])
    print(f"attached read-only to pid {pid}, base {p.base:#x}; GNames OK; walked {e.num} object slots")
    print({k: [hex(x) for x in v] for k, v in objs.items()})
    if "--probe" in sys.argv:
        for v in objs["RVehicleBatmobile"]:
            s = snap(p, v, VEH); print("vehicle", hex(v), e.obj_name(v), s, bits(s["flags_11D8"]))
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "samples-" + datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + ".jsonl")
    last, t_find = {}, time.time()
    with open(path, "w", encoding="utf-8") as f:
        print("logging to", path, "- Ctrl+C to stop")
        while True:
            if time.time() - t_find > 10:
                objs = e.find(["RVehicleBatmobile", "RPlayerController", "RPlayerInput", "RBatmobileEMPMissile", "RBatmobileVehicleTracker"]); t_find = time.time()
            now = {}
            for i, v in enumerate(objs["RVehicleBatmobile"]):
                for k, val in snap(p, v, VEH).items():
                    # object pointers -> "Class:Name" so the log names the weapon / target, not an address
                    now[f"veh{i}.{k}"] = (f"{e.class_name(val)}:{e.obj_name(val)}" if val else None) \
                        if k in PTRS else val
                now[f"veh{i}.bits11D8"] = ",".join(bits(now[f"veh{i}.flags_11D8"]))
            for i, c in enumerate(objs["RPlayerController"]):
                for k, val in snap(p, c, PC).items():
                    now[f"pc{i}.{k}"] = val
            for cls, fields in GADGETS.items():
                for i, g in enumerate(objs.get(cls, [])):
                    for k, val in snap(p, g, fields).items():
                        if k in PTRS:
                            val = f"{e.class_name(val)}:{e.obj_name(val)}" if val else None
                        elif k == "weaponflags":
                            k, val = "bFiring", bool(val & 0x2) if val is not None else None
                        elif k == "acquireflags":
                            k, val = "bTryingToAcquireNewTarget", bool(val & 0x1) if val is not None else None
                        now[f"{cls}{i}.{k}"] = round(val, 3) if isinstance(val, float) else val
            # GOG: no object of class exactly RPlayerController was found; the input object is sampled directly
            for i, pi in enumerate(objs["RPlayerInput"]):
                for k, val in snap(p, pi, PI).items():
                    now[f"in{i}.{k}"] = round(val, 3) if isinstance(val, float) else val
            for k in list(now):
                if isinstance(now[k], float):
                    now[k] = round(now[k], 3)
            ch = {k: v for k, v in now.items() if last.get(k) != v}
            if ch:
                rec = {"t": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z", "changed": ch}
                f.write(json.dumps(rec) + "\n"); f.flush()
                show = {k: v for k, v in ch.items() if not k.endswith(("Pawn", "PlayerInput", "Driver")) or True}
                print(rec["t"][11:23], show)
            last = now
            time.sleep(0.05)


if __name__ == "__main__":
    main()
