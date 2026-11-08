"""grab_controls_native2.py - G3-02e: BmAK native mode flags, the 0.707 test, the dispatch and
the exit/eject route (static analysis of BatmanAK.exe; the game is never run).

Reuses `grab_controls_native.py` (G3-02c) for the PE image, .pdata function bounds, the exec
registration arrays, direct-call scans and rip-relative resolution - the same decoders, not a fork.

WHAT IS DECODED (every number has the address it came from)
  (a) `[vehicle+0x11d8]` is the bool bitfield word of `RVehicleBatmobileBase`: the BmSDK-AK dump
      (BMSDK_OFFSETS.json) gives **32** BoolProperties at that offset, each with its mask, and
      beyond doubt `0x10 = bWeaponsReady`, `0x8000 = bBattleModeLocked`. Every instruction in
      .text that touches the word is listed with its mask resolved to that name, split into
      writers (or/and/xor/mov to memory) and readers (test/cmp/mov from memory). Writes whose
      source is a register are resolved through the last immediate load into that register inside
      the same function and labelled derived.
  (b) the `+-0.707` test in the TryToChangeMode implementation 0x140063e90: the request FName is
      compared against 0x240 (`BattleMode`, decoded in G3-02c), then the float
      `[[this+0x38c]+0xd8]` is compared against -0.707 and +0.707. The object at `[this+0x38c]`
      is named only if a class reachable from `RVehicleBatmobileBase` by `super` declares a
      property there; `[obj+0xd8]` is named only if the same test passes for that class.
  (c) the exec thunk 0x140501f60 has **0** direct E8/E9 callers, and so has every other entry of
      the two registration arrays (347 ARPlayerController, 75 ARVehicleBatmobileBase): exec
      thunks are dispatched, never called. The 8-byte occurrences of the code pointer are data.
  (d) the three exit/eject execs (SetBatmobileExit 0x1404bdde0,
      CheckSpaceToGetOutOfBatmobile 0x140548f10, ModifyEjectUpLoc 0x140548d90) have 0 direct
      callers and share **no** callee with the DrivingPlayerMove body, so the executable contains
      no native route from the driving input handler to them; the native input->mode-change link
      is decoded (5 call sites into 0x140063e90 inside the body).

Usage:
  uv run --with numpy --with pefile --with capstone python Tools/scripts/grab_controls_native2.py --write
  uv run --with numpy --with pefile --with capstone python Tools/scripts/grab_controls_native2.py --check
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

import grab_controls_native as gcn  # noqa: E402
from grab_controls_native import EXE, Image, direct_calls, exec_entry, array_of, fmt_ins  # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
SDK = os.path.join(OUT, "BMSDK_OFFSETS.json")
MD = os.path.join(OUT, "CONTROLS_NATIVE2.md")
JS = os.path.join(OUT, "CONTROLS_NATIVE2.json")

VEHICLE_CLASS = "RVehicleBatmobileBase"
FLAG_OFF = 0x11D8
IMPL = 0x140063E90
THUNK = 0x140501F60
BODY = 0x140254560
COMPARES = {0x140063F04: 0x141BF1CDC, 0x140063F22: 0x141BCE8F8}
EXITS = {"exit_set": "ARVehicleBatmobileBaseexecSetBatmobileExit",
         "exit_check": "ARVehicleBatmobileBaseexecCheckSpaceToGetOutOfBatmobile",
         "eject_up": "ARVehicleBatmobileBaseexecModifyEjectUpLoc"}
MODE_CONST = 0x240  # BattleMode, decoded in G3-02c


# ---------------------------------------------------------------- dump lookups
def load_sdk() -> dict:
    return json.load(open(SDK, encoding="utf-8"))


def chain(sdk: dict, cls: str) -> list[str]:
    out, seen = [], set()
    while cls and cls not in seen and cls in sdk["classes"]:
        seen.add(cls)
        out.append(cls)
        cls = sdk["classes"][cls].get("super")
    return out


def props_at(sdk: dict, cls: str, off: int) -> list[dict]:
    """Properties at `off` on the class or a super of it, nearest class first."""
    rows = []
    for c in chain(sdk, cls):
        rows += [{"class": c, "name": p["name"], "kind": p["kind"], "mask": p.get("mask"),
                  "type": p.get("type")}
                 for p in sdk["classes"][c].get("properties", []) if p.get("offset") == off]
    return rows


def props_at_anywhere(sdk: dict, off: int) -> list[dict]:
    rows = []
    for c, e in sdk["classes"].items():
        rows += [{"class": c, "name": p["name"], "kind": p["kind"], "mask": p.get("mask")}
                 for p in e.get("properties", []) if p.get("offset") == off]
    return rows


def flag_masks(sdk: dict) -> dict[int, dict]:
    out = {}
    for p in sdk["classes"][VEHICLE_CLASS]["properties"]:
        if p.get("offset") == FLAG_OFF and p.get("mask"):
            out[int(p["mask"])] = {"name": p["name"], "kind": p["kind"]}
    return dict(sorted(out.items()))


def effective_mask(mnemonic: str, imm: int) -> int:
    """The bits an immediate write changes: `or`/`xor` set `imm`, `and` clears `~imm`."""
    if mnemonic == "and":
        return (~imm) & 0xFFFFFFFF
    return imm


def bit_names(masks: dict, bits: int) -> list[str]:
    """A field name only for an exact mask (a single bit, or the whole field)."""
    if not bits:
        return []
    if bits in masks:
        return [masks[bits]["name"]]
    return []


# ---------------------------------------------------------------- (a) flag word
def flag_sites(img: Image, masks: dict) -> dict:
    tva, tvs, tpo, trs, _ = img.text
    tb = img.data[tpo:tpo + trs]
    pat = struct.pack("<I", FLAG_OFF)
    hits, i = [], tb.find(pat)
    while i >= 0:
        hits.append(tva + i)
        i = tb.find(pat, i + 1)
    funcs: dict = {}
    unmapped = 0
    for va in hits:
        f = None
        for back in range(2, 8):
            f = img.func_of(va - back) or f
        if not f:
            unmapped += 1
            continue
        funcs.setdefault(f, []).append(va)
    writes, reads, computed, tests = [], [], [], []
    covered = {f: set() for f in funcs}
    for f in sorted(funcs):
        ins = img.decode(f[0], f[1])
        for occ in funcs[f]:
            if any(x.address <= occ < x.address + x.size for x in ins):
                covered[f].add(occ)
        for k, x in enumerate(ins):
            if "11d8" not in x.op_str:
                continue
            m = re.match(r"(byte|dword) ptr \[(r\w+) \+ 0x11d8\], (0x[0-9a-f]+)$", x.op_str)
            rec = {"at": x.address, "in_function": [f[0], f[1]], "text": fmt_ins(x),
                   "mnemonic": x.mnemonic}
            if m and x.mnemonic in ("or", "and", "xor", "mov"):
                imm = int(m.group(3), 16)
                eff = effective_mask(x.mnemonic, imm)
                rec.update({"kind": "write", "immediate": imm, "effective_mask": eff,
                            "names": bit_names(masks, eff), "width": m.group(1),
                            "rule": "and clears ~imm; or/xor/mov set imm"})
                writes.append(rec)
            elif re.match(r"(byte|dword) ptr \[(r\w+) \+ 0x11d8\], (e|r)\w+$", x.op_str) and \
                    x.mnemonic in ("or", "and", "xor", "mov"):
                src = x.op_str.rsplit(", ", 1)[1]
                imm = None
                for y in reversed(ins[max(0, k - 30):k]):
                    mm = re.match(r"%s, (0x[0-9a-f]+)$" % re.escape(src), y.op_str)
                    if y.mnemonic == "mov" and mm:
                        imm = int(mm.group(1), 16)
                        break
                rec.update({"kind": "write_computed", "source": src, "mask_from_load": imm,
                            "names": bit_names(masks, imm) if imm else [],
                            "rule": "last `mov <src>, imm` within 30 instructions in the function"})
                computed.append(rec)
            else:
                rec.update({"kind": "read"})
                reads.append(rec)
        # immediate tests within 16 instructions of a word reference (register or memory form:
        # `test byte ptr [r+0x11d8], 0x10`, `mov eax,[r+0x11d8]; test al, 0x10` both land here)
        for k, x in enumerate(ins):
            if "11d8" not in x.op_str:
                continue
            # registers that hold the word after this instruction (32- and 8-bit forms)
            regs = set()
            m0 = re.match(r"(\w+), (dword|byte) ptr \[r\w+ \+ 0x11d8\]$", x.op_str)
            if m0:
                r = m0.group(1)
                regs.add(r)
                aliases = {"eax": ("al",), "ebx": ("bl",), "ecx": ("cl",), "edx": ("dl",),
                           "esi": ("sil",), "edi": ("dil",), "ebp": ("bpl",), "esp": ("spl",)}
                regs.update(aliases.get(r, (r + "b",)))
            for y in ins[k + 1:k + 17]:
                mm = re.search(r", (0x[0-9a-f]+)$", y.op_str)
                if not (y.mnemonic == "test" and mm):
                    continue
                dst = y.op_str.split(",")[0].strip()
                if "11d8" not in y.op_str and dst not in regs:
                    continue
                imm = int(mm.group(1), 16)
                tests.append({"at": y.address, "in_function": [f[0], f[1]],
                              "text": fmt_ins(x) + " ; " + fmt_ins(y), "mask": imm,
                              "names": bit_names(masks, imm)})
    matched = sum(len(v) for v in covered.values())
    return {"disp_occurrences": len(hits), "functions": len(funcs),
            "outside_functions": unmapped, "in_functions": len(hits) - unmapped,
            "matched_to_an_instruction": matched,
            "unmatched_in_functions": (len(hits) - unmapped) - matched,
            "writes": sorted(writes, key=lambda r: r["at"]),
            "computed_writes": sorted(computed, key=lambda r: r["at"]),
            "reads": sorted(reads, key=lambda r: r["at"]),
            "register_tests": sorted(tests, key=lambda r: r["at"])}


# ---------------------------------------------------------------- (b) 0.707 site
def call_target_set(img: Image) -> set:
    """One pass over .text: every E8/E9 rel32 target. Used only to answer 'is this address the
    target of any call' in bulk; the single-site answers are re-checked with the verified
    `gcn.direct_calls`."""
    tva, tvs, tpo, trs, _ = img.text
    tb = img.data[tpo:tpo + trs]
    out = set()
    for m in re.finditer(rb"[\xe8\xe9]", tb):
        i = m.start()
        if i + 5 > len(tb):
            continue
        out.add(tva + i + 5 + struct.unpack_from("<i", tb, i + 1)[0])
    return out


def impl_analysis(img: Image, sdk: dict) -> dict:
    f = img.func_of(IMPL)
    ins = list(img.decode(f[0], f[1]))
    rows = [{"at": x.address, "text": fmt_ins(x)} for x in ins]
    comparisons, float_sources = [], []
    for x in ins:
        if x.mnemonic == "movss" and "xmm1" in x.op_str:
            float_sources.append({"at": x.address, "text": fmt_ins(x), "src": x.op_str})
        m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", x.op_str)
        if not m:
            continue
        d = int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
        ea = x.address + x.size + d
        if img.sec(ea) != ".rdata":
            continue
        val = struct.unpack_from("<f", img.data, img.fo(ea))[0]
        if x.mnemonic == "comiss":
            comparisons.append({"at": x.address, "const_va": ea, "value": round(val, 6),
                                "text": fmt_ins(x)})
    # the chain [this+0x38c] -> [obj+0xd8]
    load_obj = next((x for x in ins
                     if x.mnemonic == "mov" and re.search(r"\[rbx \+ 0x38c\]$", x.op_str)), None)
    load_float = next((x for x in ins
                       if x.mnemonic == "movss" and re.search(r"\[rax \+ 0xd8\]", x.op_str)), None)
    slot = {"load_object": fmt_ins(load_obj) if load_obj else None,
            "load_float": fmt_ins(load_float) if load_float else None,
            "object_slot_props": props_at(sdk, VEHICLE_CLASS, 0x38C),
            "object_slot_anywhere": props_at_anywhere(sdk, 0x38C),
            "float_slot_props": props_at(sdk, VEHICLE_CLASS, 0xD8),
            "float_slot_anywhere": props_at_anywhere(sdk, 0xD8)[:12]}
    # which class of object is at +0x38c is only claimed if the chain proves it
    chain_hit = [p for p in slot["object_slot_props"]]
    slot["object_named"] = chain_hit[0] if len(chain_hit) == 1 else None
    slot["float_named"] = None
    if slot["object_named"]:
        cand = props_at(sdk, slot["object_named"]["class"], 0xD8)
        if len(cand) == 1:
            slot["float_named"] = cand[0]
    # request-mode compare: mov qword ptr [rsp + 0x30], 0x240 ; cmp rdx, [rsp + 0x30]
    mode_cmp = []
    for k, x in enumerate(ins):
        if x.mnemonic == "mov" and x.op_str.startswith("qword ptr [rsp + 0x30], 0x"):
            imm = int(x.op_str.rsplit(", ", 1)[1], 16)
            nxt = ins[k + 1:k + 4]
            mode_cmp.append({"at": x.address, "constant": imm,
                             "equal_to_battle_mode": imm == MODE_CONST,
                             "next": [fmt_ins(y) for y in nxt]})
    # other field reads in the implementation, named from the chain
    fields = []
    for x in ins:
        for m in re.finditer(r"\[rbx \+ (0x[0-9a-f]+)\]", x.op_str):
            off = int(m.group(1), 16)
            props = props_at(sdk, VEHICLE_CLASS, off)
            fields.append({"at": x.address, "text": fmt_ins(x), "offset": off,
                           "props": [p["name"] for p in props][:4]})
    return {"function": [f[0], f[1]], "disassembly": rows, "comparisons": comparisons,
            "float_sources": float_sources, "slot": slot, "mode_compare": mode_cmp,
            "vehicle_fields": fields}


# ---------------------------------------------------------------- (c) dispatch
def dispatch(img: Image) -> dict:
    e = exec_entry(img, "ARPlayerControllerexecDrivingPlayerMove")
    arr = array_of(img, e["entry_va"]) if e else []
    code_refs = img.ptr_refs(e["code_va"]) if e else []
    e2 = exec_entry(img, "ARVehicleBatmobileBaseexecTryToChangeMode")
    arr2 = array_of(img, e2["entry_va"]) if e2 else []
    targets = call_target_set(img)
    def fleet(arr):
        return {"entries": len(arr),
                "code_in_text": sum(1 for x in arr if img.sec(x["code_va"]) == ".text"),
                "zero_direct_callers": sum(1 for x in arr if x["code_va"] not in targets),
                "rule": "membership in the one-pass E8/E9 target set of .text"}
    return {"thunk": THUNK, "body": BODY,
            "direct_callers_of_thunk": direct_calls(img, THUNK),
            "direct_callers_of_body": direct_calls(img, BODY),
            "registration": {"entry_va": e["entry_va"] if e else None,
                             "name_string_va": e["name_string_va"] if e else None,
                             "slot": hex(e["entry_va"]) if e else None},
            "code_pointer_data_refs": [{"at": hex(v), "section": img.sec(v)} for v in code_refs],
            "arplayercontroller_table": fleet(arr),
            "vehicle_table": fleet(arr2),
            "rule": "an exec thunk reached only through data has no direct caller; the script VM "
                    "dispatches it by FName through ProcessEvent"}


# ---------------------------------------------------------------- (d) exit route
def exit_route(img: Image, dpm_callees: set, targets: set) -> dict:
    out = {}
    for key, name in EXITS.items():
        e = exec_entry(img, name)
        if not e:
            out[key] = {"name": name, "present": False}
            continue
        f = img.func_of(e["code_va"])
        callees = []
        for x in img.decode(f[0], f[1]):
            if x.mnemonic in ("call", "jmp") and x.op_str.startswith("0x"):
                t = int(x.op_str, 16)
                callees.append({"at": x.address, "target": t, "section": img.sec(t)})
        cs = {c["target"] for c in callees}
        arr = array_of(img, e["entry_va"])
        out[key] = {"name": name, "present": True, "code_va": e["code_va"],
                    "function": [f[0], f[1]], "array_entries": len(arr),
                    "direct_callers": ([] if e["code_va"] not in targets
                                       else direct_calls(img, e["code_va"])),
                    "caller_check": "one-pass E8/E9 target set, then verified sites if any",
                    "callees": callees,
                    "callees_shared_with_driving_move": sorted(hex(x) for x in (cs & dpm_callees)),
                    "native_link_to_input": bool(cs & dpm_callees)}
    dpm = img.func_of(BODY)
    into_mode = [{"at": x.address, "target": int(x.op_str, 16)}
                 for x in img.decode(dpm[0], dpm[1])
                 if x.mnemonic == "call" and x.op_str.startswith("0x")
                 and int(x.op_str, 16) == IMPL]
    out["_input_to_mode"] = {"body": [dpm[0], dpm[1]], "call_sites_to_TryToChangeMode": into_mode,
                             "count": len(into_mode)}
    return out


def callees_of(img: Image, va: int) -> set:
    f = img.func_of(va)
    return {int(x.op_str, 16) for x in img.decode(f[0], f[1])
            if x.mnemonic in ("call", "jmp") and x.op_str.startswith("0x")}


# ---------------------------------------------------------------- build
def build() -> dict:
    img = Image(EXE)
    sdk = load_sdk()
    masks = flag_masks(sdk)
    flags = flag_sites(img, masks)
    imp = impl_analysis(img, sdk)
    disp = dispatch(img)
    dpm_callees = callees_of(img, BODY)
    targets = call_target_set(img)
    exits = exit_route(img, dpm_callees, targets)
    oracles = {
        "flag_word_is_one_documented_bitfield": {
            "ok": len(masks) == len({m for m in masks}) and 0x10 in masks and 0x8000 in masks,
            "detail": {"masked_fields": len(masks), "distinct_masks": len({m for m in masks}),
                       "bits_0x10_0x8000": [masks.get(0x10, {}).get("name"),
                                            masks.get(0x8000, {}).get("name")],
                       "dump_rows_without_mask": [p["name"] for p in sdk["classes"]
                                                  [VEHICLE_CLASS]["properties"]
                                                  if p.get("offset") == FLAG_OFF
                                                  and not p.get("mask")]},
        },
        "every_decoded_flag_reference_is_an_instruction_operand": {
            # writes + computed writes + reads are exactly the instructions whose operand text
            # carries the displacement; the byte occurrences that no instruction covers are
            # reported separately (they are data inside .text, not references).
            "ok": flags["matched_to_an_instruction"] >= len(flags["writes"])
                  + len(flags["computed_writes"]) + len(flags["reads"]),
            "detail": {"occurrences": flags["disp_occurrences"],
                       "in_functions": flags["in_functions"],
                       "instruction_refs": len(flags["writes"])
                       + len(flags["computed_writes"]) + len(flags["reads"]),
                       "matched_to_an_instruction": flags["matched_to_an_instruction"],
                       "outside_functions": flags["outside_functions"],
                       "unmatched_in_functions": flags["unmatched_in_functions"]},
        },
        "mode_compare_constants_are_pm_0_707": {
            "ok": all(abs(abs(c["value"]) - 0.707) < 1e-5 and
                      COMPARES.get(c["at"]) == c["const_va"] for c in imp["comparisons"]),
            "detail": [{"at": hex(c["at"]), "const": hex(c["const_va"]), "value": c["value"]}
                       for c in imp["comparisons"]],
        },
        "float_load_chain": {
            "ok": bool(imp["slot"]["load_object"] and imp["slot"]["load_float"]),
            "detail": {"object": imp["slot"]["load_object"], "float": imp["slot"]["load_float"]},
        },
        "exec_thunks_have_no_direct_caller": {
            "ok": not disp["direct_callers_of_thunk"]
                  and disp["arplayercontroller_table"]["zero_direct_callers"]
                  == disp["arplayercontroller_table"]["entries"]
                  and disp["vehicle_table"]["zero_direct_callers"]
                  == disp["vehicle_table"]["entries"],
            "detail": {"thunk": len(disp["direct_callers_of_thunk"]),
                       "arplayercontroller": disp["arplayercontroller_table"],
                       "vehicle": disp["vehicle_table"]},
        },
        "exit_natives_have_no_native_input_link": {
            "ok": all(not v.get("direct_callers") and not v.get("native_link_to_input")
                      for k, v in exits.items() if isinstance(v, dict) and v.get("present")),
            "detail": {k: {"direct": len(v.get("direct_callers") or []),
                           "shared": v.get("callees_shared_with_driving_move")}
                       for k, v in exits.items() if isinstance(v, dict) and v.get("present")},
        },
    }
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_controls_native2.py --write",
        "card": "GRB-G3-02e BmAK native mode flags, 0.707 test, exit route (static)",
        "image": {"path": EXE, "size": len(img.data), "base": hex(img.base)},
        "flag_word": {"class": VEHICLE_CLASS, "offset": FLAG_OFF,
                      "masks": [{"mask": m, **v} for m, v in masks.items()],
                      "sites": flags, "class_chain": chain(sdk, VEHICLE_CLASS)},
        "mode_change": {"impl": IMPL, "impl_function": imp["function"],
                        "comparisons": imp["comparisons"], "float_sources": imp["float_sources"],
                        "slot": imp["slot"], "mode_compare": imp["mode_compare"],
                        "vehicle_fields": imp["vehicle_fields"],
                        "disassembly": imp["disassembly"]},
        "dispatch": disp,
        "exit_route": exits,
        "oracles": oracles,
        "unknowns": [
            "the meaning of the float at [[this+0x38c]+0xd8]: the chain `[this+0x38c]` is "
            "decoded, but %s" % (
                "the object at that slot is not declared by any class reachable from "
                "RVehicleBatmobileBase by `super`, so its class is UNKNOWN and `+0xd8` cannot be "
                "named" if not imp["slot"]["object_named"] else
                "the dump declares no property at +0xd8 on that class"),
            "whether the -0.707/+0.707 comparisons mean pitch, direction or a normalised dot "
            "product: the instruction only proves a float compare, not its source semantics",
            "which computed writes set bit 0x8000: writers whose source is a register are "
            "resolved only to the last immediate load in the same function, and where that "
            "immediate is not the bit the data flow is UNKNOWN",
            "the script side of exit/eject: the three execs have no direct native caller and no "
            "callee shared with DrivingPlayerMove, so their input route is in unrealscript "
            "(BmGame.upk), which this card does not decode",
        ],
    }


# ---------------------------------------------------------------- render
def hx(v):
    return "-" if v is None else "%#x" % v


def render(doc: dict) -> str:
    fw = doc["flag_word"]
    m = doc["mode_change"]
    d = doc["dispatch"]
    x = doc["exit_route"]
    o = []
    w = o.append
    w("# BmAK mode flags, the 0.707 test and the exit route (G3-02e)")
    w("")
    w("Generated by `Tools/scripts/grab_controls_native2.py --write` from `BatmanAK.exe` "
      "(%d bytes, base %s) and `BMSDK_OFFSETS.json`. Static only: the game is never run."
      % (doc["image"]["size"], doc["image"]["base"]))
    w("")
    w("## (a) `[vehicle+0x11d8]`: the bool bitfield word")
    w("")
    w("`%s` declares **%d** `BoolProperty` members at `%s`, each with its mask in the dump - one "
      "32-bit word. Decoded facts, not a declaration-order guess:" % (fw["class"], len(fw["masks"]),
                                                                    hx(fw["offset"])))
    w("")
    w("| mask | field |")
    w("|---|---|")
    for v in fw["masks"]:
        w("| %s | `%s` |" % (hx(v["mask"]), v["name"]))
    mask_names = {v["mask"]: v["name"] for v in fw["masks"]}
    w("")
    w("Accesses of the word in .text: **%d** immediate write sites, **%d** computed writes, "
      "**%d** read sites, **%d** `test` instructions near a reference, over %d occurrences of "
      "the displacement in %d functions (%d outside every .pdata function)." %
      (len(fw["sites"]["writes"]), len(fw["sites"]["computed_writes"]),
       len(fw["sites"]["reads"]), len(fw["sites"]["register_tests"]),
       fw["sites"]["disp_occurrences"], fw["sites"]["functions"],
       fw["sites"]["outside_functions"]))
    w("")
    w("Writers of the two bits the mode gate uses:")
    w("")
    w("| bit | field | write sites |")
    w("|---|---|---|")
    for bit in (0x10, 0x8000):
        sites = [s for s in fw["sites"]["writes"] + fw["sites"]["computed_writes"]
                 if s.get("effective_mask") == bit or s.get("mask_from_load") == bit]
        w("| %s | `%s` | %s |" % (hx(bit), mask_names.get(bit, "?"),
                                  ", ".join("%s in %s" % (hx(s["at"]), hx(s["in_function"][0]))
                                            for s in sites) or "none as an immediate"))
    w("")
    w("Every write site, with the mask resolved (computed rows carry the rule):")
    w("")
    w("| at | function | instruction | bits changed | field | class of write |")
    w("|---|---|---|---|---|---|")
    for s in fw["sites"]["writes"] + fw["sites"]["computed_writes"]:
        w("| %s | %s | `%s` | %s | %s | %s |" %
          (hx(s["at"]), hx(s["in_function"][0]), s["text"],
           hx(s.get("effective_mask", s.get("mask_from_load"))),
           ", ".join("`%s`" % n for n in s.get("names", [])) or "-", s["kind"]))
    w("")
    w("Reads and register tests of the gate bits (mode path):")
    w("")
    w("| at | function | instruction | mask | field |")
    w("|---|---|---|---|---|")
    for s in fw["sites"]["register_tests"]:
        w("| %s | %s | `%s` | %s | %s |" %
          (hx(s["at"]), hx(s["in_function"][0]), s["text"], hx(s["mask"]),
           ", ".join("`%s`" % n for n in s["names"]) or "-"))
    w("")
    w("## (b) the `+-0.707` test in 0x%x" % doc["mode_change"]["impl"])
    w("")
    w("- function %s-%s; request FName compared against %s (`BattleMode`): %s" %
      (hx(m["impl_function"][0]), hx(m["impl_function"][1]),
       ", ".join("%s at %s" % (hx(c["constant"]), hx(c["at"])) for c in m["mode_compare"]) or "-",
       "decoded" if any(c["equal_to_battle_mode"] for c in m["mode_compare"]) else "no"))
    w("- float loads: %s" % ("; ".join("`%s`" % s["text"] for s in m["float_sources"]) or "-"))
    w("- comparisons: %s" % ("; ".join("`%s` -> %s = %s" % (s["text"], hx(s["const_va"]), s["value"])
                                      for s in m["comparisons"]) or "-"))
    w("- slot chain: `%s` then `%s`" % (m["slot"]["load_object"], m["slot"]["load_float"]))
    w("- `[this+0x38c]` named from the class chain: %s" %
      ("`%s` (%s.%s)" % (m["slot"]["object_named"]["name"], m["slot"]["object_named"]["class"],
                         m["slot"]["object_named"]["kind"])
       if m["slot"]["object_named"] else "UNKNOWN (no reachable class declares this offset)"))
    w("- `[obj+0xd8]` named: %s" % ("`%s` (%s.%s)" % (m["slot"]["float_named"]["name"],
                                                     m["slot"]["float_named"]["class"],
                                                     m["slot"]["float_named"]["kind"])
                                    if m["slot"]["float_named"] else "UNKNOWN"))
    w("- the other vehicle fields the implementation reads: %s" %
      (", ".join(sorted({"%s=%s" % (hx(f["offset"]), "/".join(f["props"]) or "UNKNOWN")
                         for f in m["vehicle_fields"]}))[:600]))
    w("")
    w("## (c) who calls `DrivingPlayerMove` (0x%x)" % d["thunk"])
    w("")
    w("- direct `call`/`jmp` sites to the thunk: **%d**; to the body 0x%x: **%d** (the one jmp is "
      "the thunk's own tail jump)." % (len(d["direct_callers_of_thunk"]), d["body"],
                                       len(d["direct_callers_of_body"])))
    w("- the thunk's code pointer appears as data %d time(s): %s" %
      (len(d["code_pointer_data_refs"]),
       ", ".join("%s in %s" % (r["at"], r["section"]) for r in d["code_pointer_data_refs"])))
    w("- registration table: %s (%d entries, %d with code in .text, %d with zero direct callers)" %
      (d["registration"]["slot"], d["arplayercontroller_table"]["entries"],
       d["arplayercontroller_table"]["code_in_text"],
       d["arplayercontroller_table"]["zero_direct_callers"]))
    w("- vehicle table (TryToChangeMode's class): %d entries, %d with zero direct callers" %
      (d["vehicle_table"]["entries"], d["vehicle_table"]["zero_direct_callers"]))
    w("")
    w("## (d) the exit/eject route")
    w("")
    w("| exec | code | direct callers | callees | shared with DrivingPlayerMove |")
    w("|---|---|---|---|---|")
    for k, v in x.items():
        if not isinstance(v, dict) or not v.get("present"):
            continue
        w("| `%s` | %s | %d | %d | %s |" %
          (v["name"], hx(v["code_va"]), len(v["direct_callers"]), len(v["callees"]),
           ", ".join(v["callees_shared_with_driving_move"]) or "none"))
    w("")
    w("- the DrivingPlayerMove body calls TryToChangeMode's implementation at %s (%d sites) - the "
      "native input->mode-change link." % (", ".join(hx(s["at"]) for s in
                                                     x["_input_to_mode"]["call_sites_to_TryToChangeMode"]),
                                           x["_input_to_mode"]["count"]))
    w("- no exit/eject exec has a direct caller or a callee shared with that body, so the "
      "executable holds no native route from the driving input handler to them.")
    w("")
    w("## Oracles (each can fail; `--check` re-runs them)")
    w("")
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k, v in doc["oracles"].items():
        w("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:300]))
    w("")
    w("## UNKNOWN")
    w("")
    for i, u in enumerate(doc["unknowns"], 1):
        w("%d. %s" % (i, u))
    w("")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    md = render(doc)
    if a.write:
        with open(JS, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        with open(MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote CONTROLS_NATIVE2.md and CONTROLS_NATIVE2.json")
        print("flag masks:", len(doc["flag_word"]["masks"]),
              "write sites:", len(doc["flag_word"]["sites"]["writes"]),
              "computed:", len(doc["flag_word"]["sites"]["computed_writes"]),
              "register tests:", len(doc["flag_word"]["sites"]["register_tests"]))
        print("0.707 comparisons:", [(hex(c["at"]), c["value"])
                                     for c in doc["mode_change"]["comparisons"]])
        print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
        return 0
    fails = []
    if not (os.path.exists(MD) and os.path.exists(JS)):
        print("FAIL: outputs missing - run --write")
        return 1
    stored = json.load(open(JS, encoding="utf-8"))
    if json.dumps(stored, sort_keys=True) != json.dumps(doc, sort_keys=True):
        fails.append("re-derivation differs from CONTROLS_NATIVE2.json")
    if open(MD, encoding="utf-8").read() != render(stored):
        fails.append("CONTROLS_NATIVE2.md is not the render of the JSON")
    for k, v in stored["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(v["detail"])[:200]))
    dump_masks = sum(1 for p in load_sdk()["classes"][VEHICLE_CLASS]["properties"]
                     if p.get("offset") == FLAG_OFF and p.get("mask"))
    if len(stored["flag_word"]["masks"]) != dump_masks:
        fails.append("flag mask count %d is not the dump's %d" %
                     (len(stored["flag_word"]["masks"]), dump_masks))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK %d flag masks, %d write sites, %d comparisons, %d exit execs" %
          (len(stored["flag_word"]["masks"]), len(stored["flag_word"]["sites"]["writes"]),
           len(stored["mode_change"]["comparisons"]),
           sum(1 for v in stored["exit_route"].values()
               if isinstance(v, dict) and v.get("present"))))
    print("oracles:", {k: v["ok"] for k, v in stored["oracles"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
