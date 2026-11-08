"""chase09_native.py - route 2 for F-65/F-66 (and F-67/F-68): what does the executable store?

Read-only static analysis of `BatmanAK.exe`: finds `movss [reg+disp32], xmm` / `mov dword
[reg+disp32], imm32` sites for the field offsets the card names, then disassembles a small window
around each with Capstone (x86-64) and resolves any RIP-relative float the store is fed from.  The
window starts at the nearest run of INT3 padding before the hit, so the disassembly is not started
mid-instruction.

No patching, no running the game, nothing written.

Usage:
  python Tools/scripts/chase/chase09_native.py 0x6dc 0x6e0
"""
import struct
import sys

EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"


def sections(exe: bytes):
    e_lfanew = struct.unpack_from("<I", exe, 0x3C)[0]
    nsec = struct.unpack_from("<H", exe, e_lfanew + 6)[0]
    opt = e_lfanew + 24
    image_base = struct.unpack_from("<Q", exe, opt + 24)[0]
    out = []
    sec = opt + struct.unpack_from("<H", exe, e_lfanew + 20)[0]
    for i in range(nsec):
        at = sec + 40 * i
        name = exe[at:at + 8].rstrip(b"\x00").decode("latin-1")
        vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", exe, at + 8)
        out.append({"name": name, "vaddr": vaddr, "vsize": vsize,
                    "raddr": raddr, "rsize": rsize})
    return image_base, out


def off_to_va(secs, image_base, off):
    for s in secs:
        if s["raddr"] <= off < s["raddr"] + s["rsize"]:
            return image_base + s["vaddr"] + (off - s["raddr"])
    return None


def va_to_off(secs, image_base, va):
    for s in secs:
        base = image_base + s["vaddr"]
        if base <= va < base + s["vsize"]:
            return s["raddr"] + (va - base)
    return None


def find_stores(exe: bytes, disp: int, limit: int = 40):
    pat = struct.pack("<I", disp)
    hits = []
    start = 0
    while True:
        i = exe.find(pat, start)
        if i < 0:
            break
        start = i + 1
        pre4, pre3 = exe[i - 4:i], exe[i - 3:i]
        kind = None
        if len(pre4) == 4 and pre4[0] == 0xC7 and (pre4[1] & 0xC0) == 0x80:
            kind = ("mov dword [reg+0x%x], imm32" % disp, len(pre4))
        elif (len(pre4) == 4 and pre4[0] == 0xF3 and pre4[1:3] == b"\x0f\x11"
              and (pre4[3] & 0xC0) == 0x80):
            kind = ("movss [reg+0x%x], xmm" % disp, len(pre4))
        elif len(pre3) == 3 and pre3[0] == 0xC7 and (pre3[1] & 0xC0) == 0x80:
            kind = ("mov dword [reg+0x%x], imm32" % disp, len(pre3))
        if kind:
            hits.append({"off": i - kind[1], "disp_at": i, "what": kind[0]})
            if len(hits) >= limit:
                break
    return hits


def window_start(exe: bytes, off: int, back: int = 0x200):
    """Start of the disassembly window: the last INT3 run before `off`, else `off - back`."""
    lo = max(0, off - back)
    i = off - 1
    while i > lo:
        if exe[i] in (0xCC, 0x90) and exe[i - 1] in (0xCC, 0x90):
            return i + 1
        i -= 1
    return lo


def disasm(exe: bytes, secs, image_base, start_off: int, end_off: int):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    va = off_to_va(secs, image_base, start_off)
    code = exe[start_off:end_off]
    out = []
    for ins in md.disasm(code, va or start_off):
        out.append({"addr": ins.address, "off": va_to_off(secs, image_base, ins.address),
                    "mnemonic": ins.mnemonic, "op_str": ins.op_str})
        if len(out) > 400:
            break
    return out


def floats_near(exe, secs, image_base, ins):
    """RIP-relative memory operands carrying a float, and any immediate seen as a float."""
    import re
    found = []
    m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", ins["op_str"])
    if m:
        target = ins["addr"] + 0  # filled by caller with the instruction length
        found.append(("rip", int(m.group(1), 16)))
    m = re.search(r", (0x[0-9a-f]+)$", ins["op_str"])
    if m:
        found.append(("imm", int(m.group(1), 16)))
    return found


def main():
    offs = [int(x, 0) for x in sys.argv[1:]] or [0x6dc, 0x6e0]
    exe = open(EXE, "rb").read()
    image_base, secs = sections(exe)
    print(f"{EXE}: {len(exe)} bytes, image base 0x{image_base:x}, "
          f"sections {', '.join(s['name'] for s in secs)}")
    for disp in offs:
        hits = find_stores(exe, disp)
        print(f"\n-- disp 0x{disp:x} ({disp}): {len(hits)} store-form hit(s)")
        for h in hits:
            start = window_start(exe, h["off"])
            rows = disasm(exe, secs, image_base, start, min(len(exe), h["off"] + 0x60))
            print(f"   file 0x{h['off']:08x} -> VA 0x{off_to_va(secs, image_base, h['off']):x}  "
                  f"{h['what']}")
            for ins in rows:
                if ins["off"] is None:
                    continue
                if ins["off"] > h["off"] + 0x30 or ins["off"] < h["off"] - 0x120:
                    continue
                note = ""
                # resolve a rip-relative float load: compute the target from the next instruction
                import re
                m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", ins["op_str"])
                if m:
                    nxt = rows[rows.index(ins) + 1]["addr"] if rows.index(ins) + 1 < len(rows) else None
                    if nxt:
                        t = nxt + int(m.group(1), 16)
                        toff = va_to_off(secs, image_base, t)
                        if toff is not None and toff + 4 <= len(exe):
                            bits = exe[toff:toff + 4]
                            note = (f"   ; [0x{toff:08x}] = float "
                                    f"{struct.unpack('<f', bits)[0]!r} (0x{struct.unpack('<I', bits)[0]:08x})")
                print(f"      VA 0x{ins['addr']:x}  {ins['mnemonic']:<8} {ins['op_str']}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
