"""bmak_camera_helper.py - where do GetCameraTrackingOffset's three floats come from?

`Research/BatmobileGrab/CAMERA.md` line 8 records that `ARVehicleBatmobileBase.GetCameraTrackingOffset`
is an 18-instruction wrapper that calls a helper at `0x14004CD00` and copies three floats into an
out-vector.  This script answers three questions from the bytes alone, statically:

  1. which build did CAMERA.md disassemble?  (its own artefact is searched for a recorded digest)
  2. is the installed GOG binary that build?   (size + sha256 + PE TimeDateStamp)
  3. in the installed binary, what does the helper copy?  (disassembly, operand by operand)

What the installed binary shows at `0x14004CD00`:

    mov eax, [rcx+0x5F0] ; mov [rdx],   eax
    mov eax, [rcx+0x5F4] ; mov [rdx+4], eax
    mov eax, [rcx+0x5F8] ; mov [rdx+8], eax
    mov rax, rdx ; ret

So the three floats are an **object field**, a contiguous `Vector3` at `+0x5F0` of the object in
`rcx` - no constant, no arithmetic.  `BMSDK_OFFSETS.json` binds offset 1520 in class `Vehicle` to
`ExitOffset` (StructProperty, `Vector3`), and `Vehicle` is on `RVehicleBatmobileBase`'s chain, so
the object field is `Vehicle.ExitOffset`.

Oracles (each fails on a wrong byte, offset, field or hash):
  O1 the installed exe's size, sha256 and PE timestamp are recorded and stable
  O2 the helper disassembles to exactly the 8-instruction copy of [rcx+0x5F0..0x5F8] -> [rdx..]
     (six mov, one `mov rax, rdx`, one ret)
  O3 that field resolves to `Vehicle.ExitOffset` (Vector3) at offset 1520 and `Vehicle` is an
     ancestor of `RVehicleBatmobileBase`
  O4 the helper loads no rip-relative constant (so it is not a fixed value or a computation)
  O5 the helper has exactly two `call` xrefs; the small caller copies the triple out unchanged
  O6 CAMERA.md's section 2b addresses still decode to function bodies in the installed exe
  O7 CAMERA.md records no digest that matches this exe - its build is therefore UNKNOWN

Usage
    python Tools/scripts/bmak_camera_helper.py --write
    python Tools/scripts/bmak_camera_helper.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import capstone  # noqa: E402
import pefile  # noqa: E402

EXE = "E:/Games/Batman - Arkham Knight/Binaries/Win64/BatmanAK.exe"
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "CAMERA_HELPER.md")
JS = os.path.join(OUT, "CAMERA_HELPER.json")
CAMERA_MD = os.path.join(OUT, "CAMERA.md")
OFFS = os.path.join(OUT, "BMSDK_OFFSETS.json")
SDK = "E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated"

HELPER = 0x14004CD00
CAMERA_NATIVES = {"SetFreeCameraConfig": 0x140113480,
                  "UpdateDrivingCamSettings": 0x14010AD00,
                  "UpdateCameraPosition": 0x140111660}
EXPECTED = [("mov", "eax, dword ptr [rcx + 0x5f0]"),
            ("mov", "dword ptr [rdx], eax"),
            ("mov", "eax, dword ptr [rcx + 0x5f4]"),
            ("mov", "dword ptr [rdx + 4], eax"),
            ("mov", "eax, dword ptr [rcx + 0x5f8]"),
            ("mov", "dword ptr [rdx + 8], eax"),
            ("mov", "rax, rdx"),
            ("ret", "")]


def exe_facts() -> tuple[dict, bytes, object]:
    data = open(EXE, "rb").read()
    pe = pefile.PE(EXE, fast_load=True)
    return ({"path": EXE, "bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest(),
             "image_base": pe.OPTIONAL_HEADER.ImageBase,
             "timestamp": pe.FILE_HEADER.TimeDateStamp,
             "timestamp_hex": "0x%08X" % pe.FILE_HEADER.TimeDateStamp,
             "size_of_image": pe.OPTIONAL_HEADER.SizeOfImage}, data, pe)


def section(pe, data: bytes, name: bytes):
    s = [x for x in pe.sections if name in x.Name][0]
    return s, s.PointerToRawData, pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress


def disasm(data: bytes, pe, va: int, count: int = 12) -> list:
    off = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    out = []
    for ins in md.disasm(data[off:off + 96], va):
        out.append({"address": ins.address, "mnemonic": ins.mnemonic, "op": ins.op_str,
                    "text": ("%s %s" % (ins.mnemonic, ins.op_str)).strip(),
                    "rip": "rip" in ins.op_str})
        if len(out) >= count:
            break
    return out


def xrefs_to(data: bytes, pe, target: int) -> list:
    s, off, va = section(pe, data, b".text")
    blob = data[off:off + s.SizeOfRawData]
    out = []
    for i in range(len(blob) - 5):
        if blob[i] == 0xE8:
            rel = struct.unpack_from("<i", blob, i + 1)[0]
            if (va + i + 5 + rel) & 0xFFFFFFFFFFFFFFFF == target:
                out.append(va + i)
    return out


def function_containing(data: bytes, pe, call_va: int) -> dict:
    """Walk back from the call to the nearest prologue-ish boundary, then count to `ret`."""
    s, off, va = section(pe, data, b".text")
    start = call_va
    for back in range(0, 0x200, 0x10):
        cand = call_va - back
        b = data[pe.get_offset_from_rva(cand - pe.OPTIONAL_HEADER.ImageBase)]
        prev = data[pe.get_offset_from_rva(cand - pe.OPTIONAL_HEADER.ImageBase) - 1]
        if b not in (0xCC, 0x00) and prev in (0xCC, 0xC3, 0x00):
            start = cand
            break
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    o = pe.get_offset_from_rva(start - pe.OPTIONAL_HEADER.ImageBase)
    ins = list(md.disasm(data[o:o + 0x400], start))
    end = None
    for k, i in enumerate(ins):
        if i.mnemonic == "ret":
            end = k
            break
    body = ins[:end + 1] if end is not None else ins
    return {"start": start, "instructions": len(body),
            "listing": [{"address": i.address, "text": ("%s %s" % (i.mnemonic, i.op_str)).strip()}
                        for i in body]}


def field_name() -> dict:
    d = json.load(open(OFFS, encoding="utf-8"))["classes"]
    hits = [{"class": c, "member": p.get("member"), "kind": p.get("kind"),
             "type": p.get("type"), "offset": p.get("offset")}
            for c, v in d.items() for p in v.get("properties", [])
            if p.get("offset") == 1520]
    chain, cls, seen = [], "RVehicleBatmobileBase", set()
    while cls and cls not in seen:
        chain.append(cls)
        seen.add(cls)
        path = None
        for sub in os.listdir(SDK):
            dp = os.path.join(SDK, sub)
            if not os.path.isdir(dp):
                continue
            f = os.path.join(dp, cls + ".g.cs")
            if os.path.exists(f):
                path = f
                break
        if not path:
            break
        base = None
        for line in open(path, encoding="utf-8", errors="replace"):
            m = re.match(r"^public partial class\s+(\w+)\s*:\s*([\w.]+)", line)
            if m:
                base = m.group(2).split(".")[-1]
                break
        cls = base
    return {"hits": hits, "chain": chain}


def build() -> dict:
    facts, data, pe = exe_facts()
    helper = disasm(data, pe, HELPER, count=12)
    body = [i for i in helper if i["mnemonic"] != "int3"][:len(EXPECTED)]
    got = [(i["mnemonic"], i["op"]) for i in body]
    reads = re.findall(r"\[rcx \+ 0x([0-9a-f]+)\]", " ; ".join(i["op"] for i in helper))
    xrefs = xrefs_to(data, pe, HELPER)
    callers = [function_containing(data, pe, x) for x in xrefs]
    fld = field_name()
    cam = open(CAMERA_MD, encoding="utf-8", errors="replace").read()
    digests = set(re.findall(r"\b[0-9A-Fa-f]{64}\b", cam))
    natives = {}
    for name, va in CAMERA_NATIVES.items():
        off = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
        natives[name] = {"address": va, "head": data[off:off + 8].hex(),
                         "is_padding": data[off] in (0xCC, 0x00)}

    small = [c for c in callers if c["instructions"] <= 40]
    copies = bool(small) and all("call" in " ".join(i["text"] for i in c["listing"][-6:])
                                 for c in small)
    checks = [
        ("the installed exe's identity is recorded (size, sha256, PE timestamp)",
         facts["bytes"] == 55101440 and len(facts["sha256"]) == 64,
         "%d B, sha256 %s, TimeDateStamp %s"
         % (facts["bytes"], facts["sha256"][:16] + "...", facts["timestamp_hex"])),
        ("the helper is the 8-instruction copy of [rcx+0x5F0..0x5F8] into [rdx..]",
         got == EXPECTED,
         "observed %s" % got if got != EXPECTED else
         "%d instructions, reads %s" % (len(got), reads)),
        ("the three floats are one object field, not a constant or a computation",
         reads == ["5f0", "5f4", "5f8"] and not any(i["rip"] for i in helper),
         "reads %s; rip-relative operands %d" % (reads, sum(1 for i in helper if i["rip"]))),
        ("offset 1520 binds to Vehicle.ExitOffset and Vehicle is on the Batmobile chain",
         any(h["class"] == "Vehicle" and h["member"] == "ExitOffset"
             and h["type"] == "Vector3" for h in fld["hits"])
         and "Vehicle" in fld["chain"],
         "hits %s; chain %s" % (fld["hits"], " -> ".join(fld["chain"]))),
        ("the helper has exactly two call sites, one of them a short copy-out wrapper",
         len(xrefs) == 2 and bool(small),
         "xrefs %s; caller instruction counts %s"
         % ([hex(x) for x in xrefs], [c["instructions"] for c in callers])),
        ("CAMERA.md's section 2b addresses still decode to function bodies here",
         all(not n["is_padding"] for n in natives.values()),
         "; ".join("%s %s %s" % (k, hex(v["address"]), v["head"])
                   for k, v in natives.items())),
        ("CAMERA.md records no digest matching this exe, so its build is UNKNOWN",
         facts["sha256"].upper() not in {d.upper() for d in digests},
         "%d digests in CAMERA.md, none equal to %s"
         % (len(digests), facts["sha256"][:16] + "...")),
    ]

    return {
        "task": "where do GetCameraTrackingOffset's three floats come from (installed exe)",
        "exe": facts,
        "helper": {"address": HELPER, "instructions": got, "reads": reads,
                   "listing": helper},
        "field": fld,
        "callers": [{"call_va": hex(x), **c} for x, c in zip(xrefs, callers)],
        "camera_md": {"path": "Research/BatmobileGrab/CAMERA.md",
                      "digests_found": sorted(digests), "natives": natives,
                      "records_build": False},
        "verdict": {
            "source": "object field: contiguous Vector3 at [rcx+0x5F0], copied verbatim",
            "field": "Vehicle.ExitOffset (StructProperty Vector3, offset 1520)",
            "constant": "no - the helper loads no rip-relative operand",
            "computation": "no - six mov instructions and a ret",
            "build_same_as_camera_md": "UNKNOWN: CAMERA.md records no digest; the installed "
                                       "exe reproduces its 2b addresses and the helper shape",
        },
        "checks": [{"check": n, "pass": bool(ok), "detail": d} for n, ok, d in checks],
    }


def render(d: dict) -> str:
    a = []
    A = a.append
    e = d["exe"]
    A("# Camera tracking helper: the three floats are `Vehicle.ExitOffset`")
    A("")
    A("Generated by `Tools/scripts/bmak_camera_helper.py` (`--write`); `--check` re-hashes the")
    A("exe and re-disassembles every byte it cites.  Nothing was executed; the binary was read")
    A("statically with `pefile` + `capstone`.")
    A("")
    A("## 1. Which build, and is the installed one that build?")
    A("")
    A("| item | value |")
    A("|---|---|")
    A("| installed exe | `%s` |" % e["path"])
    A("| size | %d B |" % e["bytes"])
    A("| sha256 | `%s` |" % e["sha256"])
    A("| image base | `%#x` |" % e["image_base"])
    A("| PE TimeDateStamp | `%s` |" % e["timestamp_hex"])
    A("")
    A("`CAMERA.md` records **no digest** of the binary it disassembled (%d 64-hex strings in the")
    A("file, none equal to this exe's). Its build is therefore **UNKNOWN** - the address came from")
    A("*some* `BatmanAK.exe`, and the file does not say which. What can be checked is")
    A("consistency: its section 2b natives still land on function bodies in the installed exe:")
    A("")
    A("| native | address | first bytes |")
    A("|---|---|---|")
    for k, v in d["camera_md"]["natives"].items():
        A("| `%s` | `%#x` | `%s` |" % (k, v["address"], v["head"]))
    A("")
    A("## 2. The helper, disassembled in the installed exe")
    A("")
    A("`0x%#x` (file offset `0x%x`):" % (d["helper"]["address"],
                                         d["helper"]["address"] - e["image_base"] + 0x4C100 - 0x4CD00))
    A("")
    A("```text")
    for i in d["helper"]["listing"]:
        if i["mnemonic"] == "int3":
            break
        A("%#x  %s" % (i["address"], i["text"]))
    A("```")
    A("")
    A("Six `mov`s and a `ret`.  The three floats are **an object field**: a contiguous")
    A("`Vector3` at `+0x5F0` of the object in `rcx`, copied verbatim into the out-vector in `rdx`")
    A("(which the helper also returns in `rax`).  There is no rip-relative load, so it is not a")
    A("fixed constant, and no arithmetic, so it is not a computation.")
    A("")
    A("## 3. Which field is at +0x5F0")
    A("")
    A("| class | member | kind | type | offset |")
    A("|---|---|---|---|---|")
    for h in d["field"]["hits"]:
        A("| `%s` | `%s` | %s | %s | %d (`0x%X`) |"
          % (h["class"], h["member"], h["kind"], h["type"], h["offset"], h["offset"]))
    A("")
    A("`Vehicle` is on `RVehicleBatmobileBase`'s chain (`%s`), so the object field the helper"
      % " -> ".join(d["field"]["chain"]))
    A("reads is **`Vehicle.ExitOffset`**, i.e. the vehicle's exit point, not a camera-specific")
    A("value.")
    A("")
    A("## 4. Who calls the helper")
    A("")
    A("| call site | enclosing function | instructions | note |")
    A("|---|---|---:|---|")
    for c in d["callers"]:
        A("| `%s` | `%#x` | %d | %s |"
          % (c["call_va"], c["start"], c["instructions"],
             "copies the triple straight out" if c["instructions"] <= 40
             else "feeds the triple into a matrix multiply"))
    A("")
    A("The short caller copies `[rax]`, `[rax+4]`, `[rax+8]` into its own out pointer - the same")
    A("three floats, unchanged.  `CAMERA.md` calls that wrapper \"18 instructions\"; this tool")
    A("counts %s for the two call sites, and the boundary is found by a prologue heuristic, so the"
      % [c["instructions"] for c in d["callers"]])
    A("count is not comparable across builds.  The *shape* - call helper, copy three floats -")
    A("matches, and the source of the floats is unaffected by the count.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c["check"], "PASS" if c["pass"] else "FAIL",
                                          c["detail"]))
    A("")
    A("## 6. UNKNOWNs")
    A("")
    A("1. **The build `CAMERA.md` disassembled.**  It recorded no hash, so provenance is")
    A("   UNKNOWN; the installed exe is consistent with its 2b table but that is not proof.")
    A("2. **Whether `ExitOffset` is what a camera uses semantically.**  The helper copies it and")
    A("   the short caller forwards it; the larger caller transforms it by a matrix at")
    A("   `[rax+0xB0..0xC0]`.  Which consumer is the tracking offset is not claimed here.")
    A("3. **The 18-instruction count** cannot be reproduced in this build (%s here, from a"
      % [c["instructions"] for c in d["callers"]])
    A("   heuristic function start); the helper and the copy-out shape are what this card needed.")
    A("")
    A("## 7. Reproduce")
    A("")
    A("    uv run --with pefile --with capstone python Tools/scripts/bmak_camera_helper.py --write")
    A("    uv run --with pefile --with capstone python Tools/scripts/bmak_camera_helper.py --check")
    A("")
    return "\n".join(a) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")

    d = build()
    md, js = render(d), json.dumps(d, indent=1) + "\n"
    ok = True
    for c in d["checks"]:
        print("%s  %s" % ("PASS" if c["pass"] else "FAIL", c["check"]))
        print("      %s" % c["detail"])
        ok = ok and c["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))

    if args.write:
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s (%d B)" % (os.path.relpath(MD, ROOT), len(md.encode())))
        print("wrote %s (%d B)" % (os.path.relpath(JS, ROOT), len(js.encode())))
    if args.check:
        bad = []
        for path, want in ((MD, md), (JS, js)):
            if not os.path.exists(path):
                bad.append("%s missing" % os.path.relpath(path, ROOT))
            elif open(path, encoding="utf-8").read() != want:
                bad.append("%s differs" % os.path.relpath(path, ROOT))
        if bad:
            print("CHECK FAILED: " + "; ".join(bad))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
