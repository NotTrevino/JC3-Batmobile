"""G3-02c - Batmobile controls in the native code of BatmanAK.exe (static, read-only).

What it does (all from the executable bytes; nothing is run, attached or injected)
  * Reads the UE3 native-function registration arrays for the classes that own the Batmobile
    controls (`ARPlayerController`, `ARVehicleBatmobileBase`, `ARBatmobileEMPMissile`) and maps each
    `<Class>exec<Function>` name to its code address (`{name ptr, code ptr}` pairs, 16 bytes each).
  * Confirms which control-related function names exist as native code at all (a name with 0 hits
    in the image is script-only or absent).
  * Resolves the mode-change path: the native `TryToChangeMode` thunk, the implementation it calls,
    the native callers of that implementation, and the FName constant each caller passes.
  * Resolves those FName constants to strings: the predefined-name registration code is
    `lea rcx, "<name>"; ...; mov edx, <index>; call <register>` (decoded per name).
  * Lists the float constants and the vtable-slot calls inside the mode-change implementation.
  * Follows the exec thunk of `ARPlayerController.DrivingPlayerMove(float)` to its body and lists the
    flag tests in the 12 instructions before each mode call.

What it does not do
  * It does not resolve who calls `DrivingPlayerMove` (no script caller in BmGame.upk; no native
    caller found by a direct-call scan). It does not resolve the vehicle flag bits to the input.
  * Every fact is `decoded` (address + bytes/disassembly, or a file + byte offset), `derived`
    (computed from decoded facts, rule stated), or `UNKNOWN` (what was tried).

Outputs (never hand-edited):
  Research/BatmobileGrab/CONTROLS_NATIVE.json
  Research/BatmobileGrab/CONTROLS_NATIVE.md

Usage
    uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_controls_native.py --write
    uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_controls_native.py --check
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import struct
import sys

import numpy as np
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"

# Names whose presence in the image decides "native or script-only".
NATIVE_NAMES = {
    "trytochange": "ARVehicleBatmobileBaseexecTryToChangeMode",
    "exit_set": "ARVehicleBatmobileBaseexecSetBatmobileExit",
    "exit_check": "ARVehicleBatmobileBaseexecCheckSpaceToGetOutOfBatmobile",
    "cockpit_check": "ARVehicleBatmobileBaseexecCheckSpaceAboveBatmobileCockpit",
    "cockpit_open": "ARVehicleBatmobileBaseexecIsCockpitOpen",
    "eject_up": "ARVehicleBatmobileBaseexecModifyEjectUpLoc",
    "battle_active": "ARVehicleBatmobileBaseexecIsInActiveBattleMode",
    "battle_factor": "ARVehicleBatmobileBaseexecGetBattleModeFactor",
    "driving_move": "ARPlayerControllerexecDrivingPlayerMove",
    "driving_rumble": "ARPlayerControllerexecUpdateDrivingRumble",
    "pre_input": "ARPlayerControllerexecPreProcessInput",
    "emp_dumb": "ARBatmobileEMPMissileexecGetDumbFireTarget",
    "emp_lock": "ARBatmobileEMPMissileexecSwitchLockOnTarget",
    "emp_origin": "ARBatmobileEMPMissileexecGetAutoTargetOrigin",
    "emp_rotation": "ARBatmobileEMPMissileexecGetAutoTargetRotation",
}

# Script-side names the user's controls would need. Counted as ASCII substrings of the image.
ABSENT_PROBES = [
    "ToggleBattleMode", "EjectFromVehicle", "SelectVehicleWeapon", "ReleaseVehicleWeapon",
    "ExitVehicle", "BatmobileFireButton", "QuickGadgetB", "aLeftTrigger", "aLeftShoulder",
    "XboxTypeS_LeftTrigger", "XboxTypeS_LeftShoulder", "RBatmobileVehicleTracker",
    "RBatmobileMissileLauncher", "RBatmobileEMPMissile", "RPursuitModeMissileLauncher",
]

# Predefined-name strings whose registration constant is wanted (the mode names and two neighbours).
NAME_PROBES = ["CinematicMode", "DrivingMode", "RadioMode", "BattleMode", "PursuitMode"]

DISASM = Cs(CS_ARCH_X86, CS_MODE_64)


class Image:
    def __init__(self, path: str):
        self.data = open(path, "rb").read()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(self.base + s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData,
                      s.SizeOfRawData, s.Name.rstrip(b"\0").decode())
                     for s in self.pe.sections]
        self.text = [s for s in self.secs if s[4] == ".text"][0]
        pd = [s for s in self.pe.sections if s.Name.rstrip(b"\0") == b".pdata"][0]
        raw = self.data[pd.PointerToRawData:pd.PointerToRawData + pd.SizeOfRawData]
        fn = []
        for i in range(0, len(raw) - 11, 12):
            b, e, _ = struct.unpack_from("<III", raw, i)
            if b:
                fn.append((self.base + b, self.base + e))
        fn.sort()
        self.fstarts = [f[0] for f in fn]
        self.funcs = fn

    def fo(self, va):
        for v, vs, po, rs, _ in self.secs:
            if v <= va < v + vs:
                return (va - v) + po
        return None

    def sec(self, va):
        for v, vs, po, rs, n in self.secs:
            if v <= va < v + vs:
                return n
        return None

    def u64(self, va):
        return struct.unpack_from("<Q", self.data, self.fo(va))[0]

    def cstr(self, va, maxlen=256):
        fo = self.fo(va) if va else None
        if fo is None:
            return None
        end = self.data.find(b"\0", fo, fo + maxlen)
        return None if end < 0 else self.data[fo:end].decode("latin1")

    def func_of(self, va):
        i = bisect.bisect_right(self.fstarts, va) - 1
        if i < 0:
            return None
        s, e = self.funcs[i]
        return (s, e) if s <= va < e else None

    def ptr_refs(self, target):
        out = []
        pat = struct.pack("<Q", target)
        i = self.data.find(pat)
        while i >= 0:
            out.append(self._va_of_fo(i))
            i = self.data.find(pat, i + 1)
        return [x for x in out if x]

    def _va_of_fo(self, off):
        for v, vs, po, rs, _ in self.secs:
            if po <= off < po + rs:
                return v + (off - po)
        return None

    def decode(self, s, e):
        fo = self.fo(s)
        code = self.data[fo:fo + (e - s)]
        return list(DISASM.disasm(code, s))

    def count(self, ascii_name: str) -> int:
        return self.data.count(ascii_name.encode("ascii"))


def fmt_ins(ins):
    return "%#x: %s %s" % (ins.address, ins.mnemonic, ins.op_str)


def exec_entry(img: Image, name: str):
    """Code VA registered under an exec name, plus the entry VA. None if not a native name."""
    nva = None
    for m in re.finditer(re.escape(name.encode("ascii")) + rb"\x00", img.data):
        va = img._va_of_fo(m.start())
        if va is None or img.cstr(va) != name:
            continue
        # the string must start a NUL-terminated entry (preceded by NUL or start of section)
        if m.start() == 0 or img.data[m.start() - 1] == 0:
            nva = va
            break
    if nva is None:
        return None
    for slot in img.ptr_refs(nva):
        if img.sec(slot) in (".data", ".rdata"):
            code = img.u64(slot + 8)
            if img.sec(code) == ".text":
                return {"name": name, "name_string_va": nva, "entry_va": slot, "code_va": code}
    return None


def array_of(img: Image, entry_va: int):
    """Walk one registration array from the entry that holds `name`, both ways, to its zero pair."""
    s = entry_va
    while True:
        n = img.u64(s - 16)
        t = img.cstr(n) if n else None
        if not t or "exec" not in t:
            break
        s -= 16
    out, cur = [], s
    while True:
        n, c = img.u64(cur), img.u64(cur + 8)
        if n == 0 and c == 0:
            break
        out.append({"entry_va": cur, "name": img.cstr(n), "code_va": c})
        cur += 16
    return out


def rip_refs(img: Image, target: int):
    """Instructions whose rip-relative operand resolves to `target` (verified by decoding the function)."""
    tva, tvs, tpo, trs, _ = img.text
    tb = np.frombuffer(img.data[tpo:tpo + trs], dtype=np.uint8)
    n = len(tb) - 8
    disp = np.lib.stride_tricks.sliding_window_view(tb, 4)[:n].copy().view("<i4").ravel().astype(np.int64)
    idx = np.arange(n, dtype=np.int64)
    found = []
    for k in range(0, 8):
        for i in np.nonzero(tva + idx + 4 + k + disp == target)[0]:
            end = tva + int(i) + 4 + k
            f = img.func_of(tva + int(i))
            if not f:
                continue
            for ins in img.decode(f[0], f[1]):
                if ins.address + ins.size == end and "rip" in ins.op_str:
                    found.append(ins.address)
                    break
    return sorted(set(found))


def direct_calls(img: Image, target: int):
    """E8 call / E9 jmp sites whose rel32 lands on `target`, verified to start an instruction."""
    tva, tvs, tpo, trs, _ = img.text
    tb = img.data[tpo:tpo + trs]
    out = []
    for m in re.finditer(rb"[\xe8\xe9]", tb):
        i = m.start()
        if i + 5 > len(tb):
            continue
        dst = tva + i + 5 + struct.unpack_from("<i", tb, i + 1)[0]
        if dst == target:
            va = tva + i
            f = img.func_of(va)
            if f:
                for ins in img.decode(f[0], f[1]):
                    if ins.address == va:
                        out.append({"at": va, "op": ins.mnemonic})
                        break
    return out


def name_constants(img: Image):
    """For each predefined-name string, the `mov edx, imm` that follows its `lea rcx, [rip+..]`."""
    rows = []
    for name in NAME_PROBES:
        cands = []
        for m in re.finditer(re.escape(name.encode("ascii")) + rb"\x00", img.data):
            cand = img._va_of_fo(m.start())
            if cand and img.sec(cand) == ".rdata":
                cands.append(cand)
        if not cands:
            rows.append({"name": name, "string_va": None})
            continue
        # the image holds more than one copy of a name; keep every copy that has code references
        hit = False
        for va in cands:
            for lea in rip_refs(img, va):
                f = img.func_of(lea)
                ins = img.decode(f[0], f[1])
                pos = [i for i, x in enumerate(ins) if x.address == lea]
                if not pos:
                    continue
                p = pos[0]
                for q in ins[p + 1:p + 8]:
                    m2 = re.match(r"edx, (0x[0-9a-f]+)$", q.op_str)
                    if q.mnemonic == "mov" and m2:
                        hit = True
                        rows.append({"name": name, "string_va": va, "lea_at": lea,
                                     "mov_edx_at": q.address, "index": int(m2.group(1), 16),
                                     "lea": fmt_ins(ins[p]), "mov": fmt_ins(q)})
                        break
        if not hit:
            rows.append({"name": name, "string_va": cands[0], "index": None})
    return rows


def mode_call_sites(img: Image, impl: int, thunk: int):
    """Native callers of the implementation, with the FName constant written just before each call."""
    rows = []
    thunk_start = img.func_of(thunk)[0]
    for c in direct_calls(img, impl):
        if c["op"] != "call":
            continue
        f = img.func_of(c["at"])
        if f[0] == thunk_start:
            continue  # the thunk's own dispatch call is reported as the thunk, not as a mode caller
        ins = img.decode(f[0], f[1])
        pos = [i for i, x in enumerate(ins) if x.address == c["at"]][0]
        imm = None
        for q in reversed(ins[max(0, pos - 8):pos]):
            m = re.match(r"qword ptr \[rbp \+ 0x180\], (0x[0-9a-f]+)$", q.op_str)
            if m and q.mnemonic == "mov":
                imm = int(m.group(1), 16)
                break
        window = [fmt_ins(x) for x in ins[max(0, pos - 12):pos + 1]]
        rows.append({"call_at": c["at"], "in_function": [f[0], f[1]], "fname_constant": imm,
                     "window_before": window})
    return rows


def thunk_targets(img: Image, code: int):
    f = img.func_of(code)
    out = []
    for ins in img.decode(f[0], f[1]):
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            t = int(ins.op_str, 16)
            out.append({"at": ins.address, "op": ins.mnemonic, "target": t,
                        "target_is_text": img.sec(t) == ".text"})
    return out


def float_constants(img: Image, fn):
    rows = []
    for ins in img.decode(fn[0], fn[1]):
        m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
        if m and ins.mnemonic in ("comiss", "ucomiss", "mulss", "addss", "subss", "movss"):
            d = int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
            ea = ins.address + ins.size + d
            if img.sec(ea) == ".rdata":
                val = struct.unpack_from("<f", img.data, img.fo(ea))[0]
                rows.append({"at": ins.address, "text": fmt_ins(ins), "const_va": ea, "value": round(val, 6)})
    return rows


def vtable_calls(img: Image, fn):
    rows = []
    for ins in img.decode(fn[0], fn[1]):
        m = re.match(r"qword ptr \[(r\w+) \+ (0x[0-9a-f]+)\]$", ins.op_str)
        if ins.mnemonic == "call" and m:
            rows.append({"at": ins.address, "base": m.group(1), "offset": int(m.group(2), 16),
                         "slot": int(m.group(2), 16) // 8})
    return rows


def search_present(img: Image):
    return {n: img.count(n) for n in ABSENT_PROBES}


def derive(img: Image) -> dict:
    natives = {}
    for key, name in NATIVE_NAMES.items():
        e = exec_entry(img, name)
        if e is None:
            natives[key] = {"name": name, "present": False}
            continue
        arr = array_of(img, e["entry_va"])
        natives[key] = {"name": name, "present": True, "entry_va": e["entry_va"],
                        "code_va": e["code_va"], "array_entries": len(arr),
                        "direct_calls_to_code": len(direct_calls(img, e["code_va"])),
                        "name_pointer_refs": len(img.ptr_refs(e["name_string_va"]))}

    # TryToChangeMode: the exec thunk, then its one non-indirect callee (the implementation)
    ttm = natives["trytochange"]
    thunk = ttm["code_va"]
    tt = thunk_targets(img, thunk)
    impl_rows = [t for t in tt if t["op"] == "call" and t["target_is_text"]]
    impl = impl_rows[0]["target"] if impl_rows else None
    impl_fn = img.func_of(impl) if impl else None
    mode = {
        "thunk": thunk, "thunk_targets": tt, "impl": impl,
        "impl_function": list(impl_fn) if impl_fn else None,
        "impl_float_constants": float_constants(img, impl_fn) if impl_fn else [],
        "impl_vtable_calls": vtable_calls(img, impl_fn) if impl_fn else [],
        "impl_direct_callers": direct_calls(img, impl) if impl else [],
        "callers": mode_call_sites(img, impl, thunk) if impl else [],
        "name_constants": name_constants(img),
    }

    # ARPlayerController.DrivingPlayerMove(float): exec thunk -> body
    dpm = natives["driving_move"]
    body_rows = thunk_targets(img, dpm["code_va"]) if dpm.get("present") else []
    body = None
    for t in body_rows:
        if t["op"] == "jmp" and t["target_is_text"] and img.func_of(t["target"]) and \
           img.func_of(t["target"])[0] == t["target"]:
            body = t["target"]
    dpm_out = {"thunk": dpm.get("code_va"), "thunk_targets": body_rows, "body": body,
               "body_direct_callers": direct_calls(img, body) if body else [],
               "body_names_in_image": None}

    return {
        "image": {"path": EXE, "size": len(img.data), "base": hex(img.base)},
        "natives": natives,
        "absent_or_present_names": search_present(img),
        "mode_change": mode,
        "driving_player_move": dpm_out,
    }


def hx(v):
    return "-" if v is None else "%#x" % v


def render(doc: dict) -> str:
    n = doc["natives"]
    m = doc["mode_change"]
    d = doc["driving_player_move"]
    L = []
    w = L.append
    w("# Batmobile controls in the native code (G3-02c)")
    w("")
    w("Generated by `Tools/scripts/grab_controls_native.py --write` from `BatmanAK.exe` "
      "(%d bytes, image base %s). Do not edit by hand; `--check` re-derives and compares." %
      (doc["image"]["size"], doc["image"]["base"]))
    w("")
    w("Labels: `decoded` = read from the executable (address, bytes or disassembly); `derived` = "
      "computed here from decoded facts (rule given); `UNKNOWN` = not decodable here, see the list.")
    w("")
    w("## Native function presence")
    w("")
    w("| key | exec name | present | code | array entries | direct calls to code |")
    w("|---|---|---|---|---|---|")
    for k, v in n.items():
        if v.get("present"):
            w("| %s | `%s` | yes | %s | %d | %d |" % (k, v["name"], hx(v["code_va"]),
                                                     v["array_entries"], v["direct_calls_to_code"]))
        else:
            w("| %s | `%s` | no | - | - | - |" % (k, v["name"]))
    w("")
    w("Script-side and class names counted as ASCII substrings of the image (decoded):")
    w("")
    for k, v in doc["absent_or_present_names"].items():
        w("- `%s`: %d" % (k, v))
    w("")
    w("## Mode change (`TryToChangeMode`)")
    w("")
    w("- exec thunk `ARVehicleBatmobileBase.TryToChangeMode` at %s; its only non-indirect callee is %s "
      "(decoded: `call` at %s)." % (hx(m["thunk"]), hx(m["impl"]),
                                    hx(next((t["at"] for t in m["thunk_targets"] if t["target"] == m["impl"]), None))))
    w("- the implementation's direct native callers, with the FName constant written before each call:")
    w("")
    w("| call at | in function | FName constant | window (decoded, 12 instructions before) |")
    w("|---|---|---|---|")
    for c in m["callers"]:
        w("| %s | %s-%s | %s | `%s` |" % (hx(c["call_at"]), hx(c["in_function"][0]), hx(c["in_function"][1]),
                                         hx(c["fname_constant"]), " ; ".join(c["window_before"][-4:])))
    w("")
    w("Predefined-name constants (decoded: `lea rcx, \"<name>\"` followed by `mov edx, <index>`):")
    w("")
    for r in m["name_constants"]:
        if r.get("string_va") is None:
            w("- `%s`: string not found" % r["name"])
        else:
            w("- `%s` = %s (lea at %s, mov at %s)" % (r["name"], hx(r["index"]), hx(r["lea_at"]),
                                                    hx(r["mov_edx_at"])))
    w("")
    w("Float constants in the implementation (decoded from `rip`-relative operands):")
    w("")
    for f in m["impl_float_constants"]:
        w("- %s  -> %s = %s" % (hx(f["at"]), hx(f["const_va"]), f["value"]))
    w("")
    w("Vtable-slot calls in the implementation (decoded; the class of each vtable is not resolved):")
    w("")
    for v in m["impl_vtable_calls"]:
        w("- %s `call qword ptr [%s + %s]` (slot %d)" % (hx(v["at"]), v["base"], hx(v["offset"]), v["slot"]))
    w("")
    w("## ARPlayerController.DrivingPlayerMove(float)")
    w("")
    w("- exec thunk %s; its jump target is the body %s (decoded)." % (hx(d["thunk"]), hx(d["body"])))
    w("- direct native callers of the body: %d (decoded: E8/E9 scan of .text)" % len(d["body_direct_callers"]))
    w("")
    w("## UNKNOWN")
    w("")
    w("- the caller of `DrivingPlayerMove` (not an export of BmGame.upk; no native direct caller)")
    w("- what the float parameter is (the body moves it into xmm11 and passes it to two helpers; no threshold on it)")
    w("- the meaning of the vehicle flag bits the body tests (`[vehicle+0x11d8]` bits 0x10 and 0x8000)")
    w("- the identity of the vtable behind the implementation's `call [+0x1120]` and `call [+0x280]`")
    w("- the identity of the weapon classes behind SelectVehicleWeapon / ReleaseVehicleWeapon (script-only)")
    w("")
    return "\n".join(L) + "\n"


def check(doc: dict, md: str):
    bad = []
    p_json = os.path.join(OUT, "CONTROLS_NATIVE.json")
    p_md = os.path.join(OUT, "CONTROLS_NATIVE.md")
    if not os.path.exists(p_json) or not os.path.exists(p_md):
        return ["missing output files; run with --write first"]
    if json.load(open(p_json, encoding="utf-8")) != json.loads(json.dumps(doc)):
        bad.append("CONTROLS_NATIVE.json differs from the re-derived data")
    if open(p_md, encoding="utf-8").read() != md:
        bad.append("CONTROLS_NATIVE.md differs from the re-derived note")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    img = Image(EXE)
    doc = derive(img)
    md = render(doc)
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "CONTROLS_NATIVE.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        with open(os.path.join(OUT, "CONTROLS_NATIVE.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote CONTROLS_NATIVE.json and CONTROLS_NATIVE.md")
    if a.check:
        bad = check(doc, md)
        if bad:
            print("FAIL")
            for b in bad:
                print(" ", b)
            sys.exit(1)
        print("check: re-derived output matches the note - ok")


if __name__ == "__main__":
    main()
