"""chase2_native.py - read-only xref/PE helper for the chase second pass (BatmanAK.exe).

The first pass looked for a {name, function pointer} pair in `.data` and found none. This tool
takes the opposite route: UE3 registers a native function with
`FNativeFunctionRegistrar::RegisterFunction(Class, "Name", &execName)`, so the **caller of the
registration** holds a RIP-relative reference to the name string and a `lea` of the `exec*` body.
Finding the reference to the string therefore anchors the function.

Commands
  sections                      - PE section table (name, VA, raw offset, sizes)
  string <text>                 - find a NUL-terminated ASCII string, print file offset + VA
  xref <text>                   - every RIP-relative reference to that string's VA, with a
                                  disassembly window around each (capstone)
  disasm <va> [--len N]         - disassemble N bytes at a VA
  ptr <va>                      - every qword equal to that VA, per section
  ptrtable <va> [--span N]      - dump a pointer table starting at VA (N qwords, .rdata only)
  func <va> [--len N]           - the .pdata function containing VA, disassembled from its start
  stores <va_lo> <va_hi>        - every immediate store into [reg+disp] in a VA range, with
                                  the displacement, the immediate and the instruction bytes
  findimm <disp> [--imm HEX]     - every `c7 /0 [reg+disp], imm32` in .text (optionally only one
                                  immediate), each with the .pdata function that contains it

Everything is read-only: the exe is opened `rb` and never written. No game is launched.
"""
from __future__ import annotations

import argparse
import re
import struct
import sys

import capstone

EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"


def load() -> tuple[bytearray, list[dict], int]:
    data = bytearray(open(EXE, "rb").read())
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not a PE"
    coff = e_lfanew + 4
    nsec, = struct.unpack_from("<H", data, coff + 2)
    opt_size, = struct.unpack_from("<H", data, coff + 16)
    opt = coff + 20
    magic, = struct.unpack_from("<H", data, opt)
    assert magic == 0x20B, "expected PE32+"
    image_base, = struct.unpack_from("<Q", data, opt + 24)
    sec = opt + opt_size
    sections = []
    for i in range(nsec):
        off = sec + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rawsize, raw = struct.unpack_from("<IIII", data, off + 8)
        sections.append({"name": name, "va": va, "vsize": vsize, "raw": raw, "rawsize": rawsize})
    return data, sections, image_base


def off_to_va(sections: list[dict], image_base: int, off: int) -> int | None:
    for s in sections:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return image_base + s["va"] + (off - s["raw"])
    return None


def va_to_off(sections: list[dict], image_base: int, va: int) -> int | None:
    rva = va - image_base
    for s in sections:
        if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
            return s["raw"] + (rva - s["va"])
    return None


def find_string(data: bytes, text: str) -> list[int]:
    needle = text.encode() + b"\0"
    out, i = [], 0
    while True:
        i = data.find(needle, i)
        if i < 0:
            return out
        out.append(i)
        i += 1


def text_span(sections: list[dict], name: str = ".text") -> tuple[int, int]:
    for s in sections:
        if s["name"] == name:
            return s["raw"], s["raw"] + s["rawsize"]
    raise SystemExit("no .text")


def pdata_function(data: bytes, sections: list[dict], image_base: int, va: int) -> tuple[int | None, int | None]:
    """The .pdata RUNTIME_FUNCTION (begin, end) that contains `va`, as VAs."""
    pd = next((s for s in sections if s["name"] == ".pdata"), None)
    if pd is None:
        return None, None
    rva = va - image_base
    count = pd["vsize"] // 12
    lo, hi = 0, count - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        off = pd["raw"] + mid * 12
        begin, end, _unwind = struct.unpack_from("<III", data, off)
        if rva < begin:
            hi = mid - 1
        elif rva >= end:
            lo = mid + 1
        else:
            return image_base + begin, image_base + end
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sections")
    p_str = sub.add_parser("string")
    p_str.add_argument("text")
    p_x = sub.add_parser("xref")
    p_x.add_argument("text")
    p_x.add_argument("--before", type=int, default=24)
    p_x.add_argument("--after", type=int, default=120)
    p_d = sub.add_parser("disasm")
    p_d.add_argument("va", type=lambda s: int(s, 0))
    p_d.add_argument("--len", type=int, default=160)
    p_p = sub.add_parser("ptr")
    p_p.add_argument("va", type=lambda s: int(s, 0))
    p_t = sub.add_parser("ptrtable")
    p_t.add_argument("va", type=lambda s: int(s, 0))
    p_t.add_argument("--span", type=int, default=24)
    p_f = sub.add_parser("func")
    p_f.add_argument("va", type=lambda s: int(s, 0))
    p_f.add_argument("--len", type=int, default=0, help="cap the disassembly (default: to the end)")
    p_s = sub.add_parser("stores")
    p_s.add_argument("lo", type=lambda s: int(s, 0))
    p_s.add_argument("hi", type=lambda s: int(s, 0))
    p_i = sub.add_parser("findimm")
    p_i.add_argument("disp", type=lambda s: int(s, 0))
    p_i.add_argument("--imm", type=lambda s: int(s, 0), default=None)
    p_i.add_argument("--text-only", action="store_true", default=True)
    a = ap.parse_args()

    data, sections, image_base = load()

    if a.cmd == "sections":
        print("image base", hex(image_base))
        for s in sections:
            print(f"{s['name']:8} va {hex(image_base + s['va']):>12} vsize {s['vsize']:#08x} "
                  f"raw {s['raw']:#010x} rawsize {s['rawsize']:#08x}")
        return 0

    if a.cmd == "string":
        for off in find_string(data, a.text):
            print(f"file {off:#010x}  va {hex(off_to_va(sections, image_base, off))}")
        return 0

    if a.cmd == "xref":
        offs = find_string(data, a.text)
        if not offs:
            print("string not found")
            return 1
        targets = [off_to_va(sections, image_base, o) for o in offs]
        print("string VAs", [hex(t) for t in targets])
        lo, hi = text_span(sections)
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        md.detail = False
        found = 0
        for prefix in (0x48, 0x4C):
            pat = bytes([prefix, 0x8D])
            i = lo
            while True:
                i = data.find(pat, i, hi)
                if i < 0:
                    break
                modrm = data[i + 2]
                if (modrm & 0xC7) == 0x05:
                    disp, = struct.unpack_from("<i", data, i + 3)
                    inst_va = off_to_va(sections, image_base, i)
                    tgt = inst_va + 7 + disp
                    if tgt in targets:
                        found += 1
                        start = max(lo, i - a.before)
                        stop = min(hi, i + a.after)
                        print(f"\n== xref at VA {hex(inst_va)} (file {i:#x}) -> {hex(tgt)}")
                        for ins in md.disasm(bytes(data[start:stop]), off_to_va(sections, image_base, start)):
                            mark = ">>" if ins.address == inst_va else "  "
                            print(f"{mark} {ins.address:#012x}  {ins.mnemonic:8} {ins.op_str}")
                i += 1
        print(f"\n{found} xref(s)")
        return 0

    if a.cmd == "findimm":
        lo, hi = text_span(sections)
        pat = bytes([0xC7])
        disp = struct.pack("<I", a.disp)
        n = 0
        i = lo
        while True:
            i = data.find(pat, i, hi)
            if i < 0:
                break
            if i + 10 <= hi and 0x80 <= data[i + 1] <= 0x87 and data[i + 2:i + 6] == disp:
                imm, = struct.unpack_from("<i", data, i + 6)
                if a.imm is None or (imm & 0xFFFFFFFF) == (a.imm & 0xFFFFFFFF):
                    va = off_to_va(sections, image_base, i)
                    start, end = pdata_function(data, sections, image_base, va)
                    fval = struct.unpack("<f", struct.pack("<I", imm & 0xFFFFFFFF))[0]
                    print(f"{va:#012x}  {data[i:i + 10].hex()}  disp={a.disp:#x} imm={imm:#x} ({fval:g})  fn {start and hex(start)}+{va - start if start else 0:#x}")
                    n += 1
            i += 1
        print(f"{n} store(s)")
        return 0

    if a.cmd == "func" or a.cmd == "stores":
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        if a.cmd == "func":
            start, end = pdata_function(data, sections, image_base, a.va)
            if start is None:
                print("VA not in any .pdata function")
                return 1
            print(f"function {hex(start)} .. {hex(end)}  ({(end - start)} bytes)")
            stop = end if not a.len else min(end, start + a.len)
            lo = va_to_off(sections, image_base, start)
            for ins in md.disasm(bytes(data[lo:va_to_off(sections, image_base, stop)]), start):
                print(f"{ins.address:#012x}  {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")
            return 0
        lo_off = va_to_off(sections, image_base, a.lo)
        hi_off = va_to_off(sections, image_base, a.hi)
        n = 0
        for ins in md.disasm(bytes(data[lo_off:hi_off]), a.lo):
            if ins.mnemonic not in ("mov", "movss", "movsd", "movups", "movaps"):
                continue
            if "[" not in ins.op_str or "," not in ins.op_str:
                continue
            dst, src = ins.op_str.split(",", 1)
            dst, src = dst.strip(), src.strip()
            if not dst.startswith(("dword ptr [", "qword ptr [", "word ptr [", "byte ptr [",
                                  "xmmword ptr [")):
                continue
            if not (src.startswith(("0x", "-")) or re.fullmatch(r"-?\d+", src)):
                continue
            n += 1
            disp = dst.split("+")[-1].split("]")[0] if "+" in dst else "0"
            print(f"{ins.address:#012x}  {ins.bytes.hex():<20} {dst:28} <- {src:10} disp={disp}")
        print(f"{n} immediate store(s)")
        return 0

    if a.cmd == "disasm":
        off = va_to_off(sections, image_base, a.va)
        if off is None:
            print("VA not mapped")
            return 1
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        for ins in md.disasm(bytes(data[off:off + a.len]), a.va):
            print(f"{ins.address:#012x}  {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")
        return 0

    if a.cmd == "ptr":
        q = struct.pack("<Q", a.va)
        i = 0
        n = 0
        while True:
            i = data.find(q, i)
            if i < 0:
                break
            n += 1
            secname = next((s["name"] for s in sections
                            if s["raw"] <= i < s["raw"] + s["rawsize"]), "?")
            print(f"file {i:#010x}  {secname}  va {hex(off_to_va(sections, image_base, i))}")
            i += 1
        print(f"{n} hit(s)")
        return 0

    if a.cmd == "ptrtable":
        off = va_to_off(sections, image_base, a.va)
        if off is None:
            print("VA not mapped")
            return 1
        for k in range(a.span):
            q, = struct.unpack_from("<Q", data, off + 8 * k)
            print(f"+{k * 8:#04x}  {hex(a.va + 8 * k)}  {q:#018x}", end="")
            if image_base <= q < image_base + 0x4000000:
                print("  -> code/data VA")
            else:
                print()
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
