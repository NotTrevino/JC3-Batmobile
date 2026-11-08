"""chase04_native.py - route 2: are the F-25..F-32 field offsets written with a float constant in
the shipped executable?

Read-only static scan (no patching, no running the game). Finds instructions that store an
immediate to `[reg + disp32]` where disp32 is the field offset the card names, and prints the
immediate as a float:

    C7 8x <disp32> <imm32>        mov dword ptr [r64+disp32], imm32
    F3 0F 11 8x <disp32>          movss dword ptr [r64+disp32], xmm

`BatmanAK.exe` is read in place; nothing is written.

Usage:
    python Tools/scripts/chase/chase04_native.py 0x1758 0x11e4
"""
import struct
import sys

EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"


def scan(exe: bytes, disp: int, limit: int = 40):
    pat = struct.pack("<I", disp)
    hits = []
    start = 0
    while True:
        i = exe.find(pat, start)
        if i < 0:
            break
        start = i + 1
        pre3 = exe[i - 3:i]
        pre4 = exe[i - 4:i]
        cand = None
        if len(pre4) == 4 and pre4[0] == 0xC7 and (pre4[1] & 0xC0) == 0x80:
            imm = exe[i + 4:i + 8]
            if len(imm) == 4:
                cand = ("mov dword [reg+0x%x], imm32" % disp, struct.unpack("<f", imm)[0],
                        struct.unpack("<I", imm)[0])
        elif (len(pre4) == 4 and pre4[0] == 0xF3 and pre4[1:3] == b"\x0f\x11"
              and (pre4[3] & 0xC0) == 0x80):
            cand = ("movss [reg+0x%x], xmm (modrm %02x)" % (disp, pre4[3]), None, None)
        elif len(pre3) == 3 and pre3[0] == 0xC7 and (pre3[1] & 0xC0) == 0x80:
            imm = exe[i + 4:i + 8]
            if len(imm) == 4:
                cand = ("mov dword [reg+0x%x], imm32" % disp, struct.unpack("<f", imm)[0],
                        struct.unpack("<I", imm)[0])
        if cand:
            hits.append((i, cand))
            if len(hits) >= limit:
                break
    return hits


def main():
    offs = [int(x, 0) for x in sys.argv[1:]] or [0x1758, 0x176c, 0x1770, 0x1774, 0x1778,
                                                 0x193c, 0x1994, 0x1998]
    exe = open(EXE, "rb").read()
    print(f"{EXE}: {len(exe)} bytes")
    for off in offs:
        hits = scan(exe, off)
        print(f"\n-- disp 0x{off:x} ({off}): {len(hits)} store-form hit(s)")
        for addr, (what, f, bits) in hits[:12]:
            print(f"   file 0x{addr:08x}  {what}  float={f!r} bits=0x{bits:08x}"
                  if bits is not None else f"   file 0x{addr:08x}  {what}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
