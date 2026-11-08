"""chase2_08_native.py - second pass, native route for F-60/F-62/F-63/F-64.

The first pass (`chase-08.md` §3) stopped because the *property names* are absent from
`BatmanAK.exe`, so there is no string anchor to the code that initialises the field. That is true of
the property names, but not of the **class** names: `RVehicleSimBatmobile` occurs once as UTF-16,
which is the `IMPLEMENT_CLASS` / `GetPrivateStaticClass` name literal. UE3.5 passes that literal to
the class registration together with the class's `InternalConstructor<T>` function pointer, so an
xref to the UTF-16 string anchors the constructor and the constructor is where a native-only
default (`AirControlTimeInAir` and friends, which no cooked package serialises) is written.

Commands
  namerefs <Class> [--wide]      every ASCII/UTF-16 occurrence of the class name, its VA, and every
                                 RIP-relative xref in .text with a disassembly window
  func <va> [--len N]            disassemble the .pdata function that contains `va` (whole function)
  stores <va> --disp 0x4bc       inside one function, every write whose displacement is `disp`
  scan <disp> [--text-only]      every `movss [reg+disp], xmm` / `mov [reg+disp], imm32` site in
                                 .text, with the containing .pdata function

Read-only: the exe is opened `rb`, nothing is written. No game launched.
"""
import argparse
import struct
import sys

import capstone

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
import chase2_native as N  # noqa: E402

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
MD.detail = True


def xrefs_to(data, sections, image_base, va, span=(0x200, 0x200)):
    """RIP-relative instructions in .text whose target is `va`."""
    lo, hi = N.text_span(sections)
    lo, hi = lo + span[0], hi - span[1]
    out = []
    for i in range(lo, hi):
        b = data[i]
        # 48 8d /r (lea r64) or 48 8b /r (mov r64) with modrm.mod == 00 and rm == 101 (RIP)
        if b != 0x48 or i + 7 > len(data):
            continue
        op = data[i + 1]
        if op not in (0x8D, 0x8B, 0x89, 0x3D, 0x05):
            continue
        modrm = data[i + 2]
        if (modrm & 0xC7) != 0x05:
            continue
        disp, = struct.unpack_from("<i", data, i + 3)
        if image_base + (i + 7) + disp == va:
            out.append(i)
    return out


def show(data, sections, image_base, off, before=16, after=120):
    print(f"  file 0x{off:08x}  va 0x{N.off_to_va(sections, image_base, off) or 0:x}")
    for ins in MD.disasm(bytes(data[off - before:off + after]),
                         (N.off_to_va(sections, image_base, off) or 0) - before):
        print(f"    {ins.address:#014x}  {ins.mnemonic:<8} {ins.op_str}")


def namerefs(a):
    data, sections, image_base = N.load()
    wide = a.text.encode("utf-16-le")
    narrow = a.text.encode() + b"\0"
    hits = []
    for label, needle in (("utf16", wide), ("ascii", narrow)):
        i = 0
        while True:
            i = data.find(needle, i)
            if i < 0:
                break
            hits.append((label, i))
            i += 1
    print(f"{a.text}: {len(hits)} literal(s)")
    for label, off in hits:
        va = N.off_to_va(sections, image_base, off)
        print(f"\n== {label} literal at file 0x{off:08x}  va 0x{va:x}")
        if label != "utf16":
            print("   (ASCII has no class-registration role; listed for completeness)")
        refs = xrefs_to(data, sections, image_base, va)
        print(f"   {len(refs)} RIP-relative xref(s)")
        for r in refs:
            show(data, sections, image_base, r)
            fbeg, fend = N.pdata_function(data, sections, image_base,
                                          N.off_to_va(sections, image_base, r))
            if fbeg:
                print(f"   .pdata function {fbeg:#x}..{fend:#x}")


def disasm_func(a):
    data, sections, image_base = N.load()
    beg, end = N.pdata_function(data, sections, image_base, a.va)
    if not beg:
        raise SystemExit("no .pdata entry contains that VA")
    start = N.va_to_off(sections, image_base, beg)
    stop = N.va_to_off(sections, image_base, end)
    if a.len:
        stop = min(stop, start + a.len)
    print(f"function {beg:#x}..{end:#x} ({stop - start} bytes)")
    for ins in MD.disasm(bytes(data[start:stop]), beg):
        print(f"  {ins.address:#014x}  {ins.mnemonic:<8} {ins.op_str}")


def stores(a):
    data, sections, image_base = N.load()
    beg, end = N.pdata_function(data, sections, image_base, a.va)
    if not beg:
        raise SystemExit("no .pdata entry contains that VA")
    start = N.va_to_off(sections, image_base, beg)
    stop = N.va_to_off(sections, image_base, end)
    n = 0
    for ins in MD.disasm(bytes(data[start:stop]), beg):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.disp == a.disp:
                n += 1
                print(f"  {ins.address:#014x}  {ins.mnemonic:<8} {ins.op_str}"
                      f"   bytes {ins.bytes.hex()}")
    print(f"{n} reference(s) to +{a.disp:#x} in {a.va:#x}..{end:#x}")


def dispwindow(a):
    """Every [reg+disp] reference in the function containing `va`, for disp in [lo, hi]."""
    data, sections, image_base = N.load()
    beg, end = N.pdata_function(data, sections, image_base, a.va)
    if not beg:
        raise SystemExit("no .pdata entry contains that VA")
    start = N.va_to_off(sections, image_base, beg)
    stop = N.va_to_off(sections, image_base, end)
    print(f"function {beg:#x}..{end:#x}")
    seen = {}
    for ins in MD.disasm(bytes(data[start:stop]), beg):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and a.lo <= op.mem.disp <= a.hi:
                seen.setdefault(op.mem.disp, []).append(
                    (ins.address, f"{ins.mnemonic} {ins.op_str}"))
    for disp in sorted(seen):
        print(f"  +{disp:#06x}:")
        for addr, txt in seen[disp]:
            print(f"      {addr:#014x}  {txt}")
    print(f"{len(seen)} distinct displacement(s) in [{a.lo:#x}, {a.hi:#x}]")


def scan(a):
    data, sections, image_base = N.load()
    lo, hi = N.text_span(sections)
    disp = struct.pack("<I", a.disp)
    hits = []
    for i in range(lo, hi - 12):
        if data[i] == 0xF3 and data[i + 1] == 0x0F and data[i + 2] == 0x11 and data[i + 3] & 0xC0 == 0x80:
            if data[i + 4:i + 8] == disp:
                hits.append((i, "movss [reg+disp], xmm"))
        elif data[i] == 0xC7 and data[i + 1] & 0xC0 == 0x80:
            if data[i + 2:i + 6] == disp:
                hits.append((i, "mov [reg+disp], imm32"))
    print(f"-- disp {a.disp:#x}: {len(hits)} store-form hit(s)")
    for off, kind in hits:
        va = N.off_to_va(sections, image_base, off)
        beg, end = N.pdata_function(data, sections, image_base, va)
        print(f"   file 0x{off:08x}  {kind}  func {('0x%x' % beg) if beg else '?'}")
        for ins in MD.disasm(bytes(data[off - 12:off + 16]), va - 12):
            print(f"     {ins.address:#014x}  {ins.mnemonic:<8} {ins.op_str}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("namerefs")
    p.add_argument("text")
    p = sub.add_parser("func")
    p.add_argument("va", type=lambda s: int(s, 0))
    p.add_argument("--len", type=int, default=0)
    p = sub.add_parser("stores")
    p.add_argument("va", type=lambda s: int(s, 0))
    p.add_argument("--disp", type=lambda s: int(s, 0), required=True)
    p = sub.add_parser("dispwindow")
    p.add_argument("va", type=lambda s: int(s, 0))
    p.add_argument("--lo", type=lambda s: int(s, 0), default=0x300)
    p.add_argument("--hi", type=lambda s: int(s, 0), default=0x500)
    p = sub.add_parser("scan")
    p.add_argument("disp", type=lambda s: int(s, 0))
    a = ap.parse_args()
    {"namerefs": namerefs, "func": disasm_func, "stores": stores, "scan": scan,
     "dispwindow": dispwindow}[a.cmd](a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
