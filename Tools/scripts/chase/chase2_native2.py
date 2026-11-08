"""chase2_native2.py - second pass, native route: who reads `FFreeCameraConfig.maxPitch`?

The first pass left two things UNKNOWN that only code can answer:
  * the unit of `maxPitch` / `MinPitch` (6000 / -8000, 6000 / -14000, 14500 / -14000);
  * whether any code writes `BattleModeCamFOV` (0x4fd0) at runtime.

`chase04_native.py` looked for *store* forms (`c7 8x` / `f3 0f 11 8x`). A class default that the
engine merely *reads* never appears there, so this tool searches the other way: for every occurrence
of the 32-bit displacement in `.text`, it tries the load forms

    f3 0f 10 8x <disp32>    movss  xmm, [reg+disp32]
    8b 8x       <disp32>    mov    r32, [reg+disp32]
    f3 0f 59 / 0f 59        mulss  xmm, ...
    0f 57 / 0f 57           xorps  (zeroing)

and disassembles forward from a match so the scale constant a `mulss`/`mulsd` uses is visible. A
rotation field multiplied by 360/65536 proves rotator units; one multiplied by 0.0174533 proves
degrees.

All absolute offsets are class-layout offsets, so the engine reaches `this->BattleModeCamConfig
.maxPitch` as `[reg + 0x3df4 + 0x4c] = [reg + 0x3e40]`: the struct base plus the member's relative
offset. Each config's fields are searched at struct base + member offset for all three configs.

Read-only. No game launched, nothing patched.

Usage:
    python Tools/scripts/chase/chase2_native2.py
    python Tools/scripts/chase/chase2_native2.py --disp 0x3e40 0x4fd0 --json OUT.json
"""
import argparse
import json
import os
import struct
import sys

import capstone

EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"
DEFAULT_JSON = r"E:\Modding\_shared\gamedata\BmAKgrab\chase\chase2_native2.json"

# struct base + relative member offset, for the three FFreeCameraConfig instances and the two FOVs
FFCC_BASES = {"BattleModeCamConfig": 0x3DF4, "BattleModeWinchCamConfig": 0x3E9C,
              "BattleModeAbseilingCamConfig": 0x3F44}
MEMBERS = {"maxPitch": 76, "MinPitch": 80,
           "MinFreeCameraDistance": 84, "MaxFreeCameraDistance": 88}
EXTRA = {"BattleModeCamFOV": 0x4FD0, "BattleModeWinchCamFOV": 0x4FD4}
# the struct bases themselves: a compiler may `lea rax,[rcx+3df4h]` once and then address members
# as [rax+4ch], so the bases must be searched as well as the flattened offsets.
BASES = {"BattleModeCamConfig base": 0x3DF4, "BattleModeWinchCamConfig base": 0x3E9C,
         "BattleModeAbseilingCamConfig base": 0x3F44}


def targets():
    out = []
    for cfg, base in FFCC_BASES.items():
        for m, rel in MEMBERS.items():
            out.append((f"{cfg}.{m}", base + rel))
    out += list(EXTRA.items())
    return out


def load():
    raw = open(EXE, "rb").read()
    e_lfanew = struct.unpack_from("<I", raw, 0x3C)[0]
    assert raw[e_lfanew:e_lfanew + 4] == b"PE\0\0"
    nsec = struct.unpack_from("<H", raw, e_lfanew + 6)[0]
    opt = e_lfanew + 24
    image_base = struct.unpack_from("<Q", raw, opt + 24)[0]
    sec = opt + struct.unpack_from("<H", raw, e_lfanew + 20)[0]
    secs = []
    for i in range(nsec):
        at = sec + 40 * i
        name = raw[at:at + 8].rstrip(b"\0").decode("latin-1")
        vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", raw, at + 8)
        secs.append({"name": name, "va": vaddr, "vsize": vsize,
                     "raw": raddr, "rawsize": rsize})
    return raw, secs, image_base


def foff(secs, image_base, va):
    for s in secs:
        base = image_base + s["va"]
        if base <= va < base + max(s["vsize"], s["rawsize"]):
            return s["raw"] + (va - base)
    return None


def va(secs, image_base, off):
    for s in secs:
        if s["raw"] <= off < s["raw"] + s["rawsize"]:
            return image_base + s["va"] + (off - s["raw"])
    return None


def float_at(secs, raw, image_base, addr):
    o = foff(secs, image_base, addr)
    if o is None or o + 4 > len(raw):
        return None
    return struct.unpack_from("<f", raw, o)[0]


def scan(disp, md, secs, raw, image_base, text):
    """Every instruction in .text whose memory displacement is exactly `disp`."""
    pat = struct.pack("<I", disp)
    hits = []
    start = text["raw"]
    end = min(len(raw), text["raw"] + text["rawsize"])
    blob = raw
    i = blob.find(pat, start, end)
    while i >= 0:
        for back in (3, 4, 5, 6, 7, 8, 9, 10, 11):
            s = i - back
            if s < 0:
                continue
            insn = next(md.disasm(blob[s:s + 16], va(secs, image_base, s), count=1), None)
            if insn is None or insn.address + insn.size != va(secs, image_base, i + 4):
                continue
            if not any(o.type == capstone.x86.X86_OP_MEM and o.mem.disp == disp
                       and o.mem.base != 0 for o in insn.operands):
                continue
            hits.append({"va": "0x%x" % insn.address, "bytes": insn.bytes.hex(),
                         "text": f"{insn.mnemonic} {insn.op_str}"})
            break
        i = blob.find(pat, i + 1, end)
    return hits


def context(md, raw, secs, image_base, va_str, n=14):
    """Disassemble forward and resolve RIP-relative float operands (the scale constants)."""
    addr = int(va_str, 16)
    o = foff(secs, image_base, addr)
    if o is None:
        return []
    out = []
    for insn in md.disasm(raw[o:o + 120], addr, count=n):
        row = {"va": "0x%x" % insn.address, "text": f"{insn.mnemonic} {insn.op_str}"}
        for op in insn.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
                tgt = insn.address + insn.size + op.mem.disp
                f = float_at(secs, raw, image_base, tgt)
                row["rip_target"] = "0x%x" % tgt
                if f is not None and f == f and abs(f) < 1e12:
                    row["float"] = f
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--disp", nargs="*", help="extra displacements as 0x.. (default: the pitch/FOV set)")
    ap.add_argument("--json", default=DEFAULT_JSON)
    a = ap.parse_args()

    raw, secs, image_base = load()
    text = next(s for s in secs if s["name"] == ".text")
    print(f"{os.path.basename(EXE)}: {len(raw):,} bytes, image base 0x{image_base:x}, "
          f".text raw 0x{text['raw']:x}..0x{text['raw'] + text['rawsize']:x}")

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True
    md.skipdata = False

    want = [(n, int(d, 0)) for n, d in (pair.split("=") for pair in a.disp)] if a.disp \
        else targets() + list(BASES.items())
    out = {}
    for name, disp in want:
        hits = scan(disp, md, secs, raw, image_base, text)
        # raw occurrence count: distinguishes "no such offset in code" from "encoded some other way"
        pat = struct.pack("<I", disp)
        nraw = raw.count(pat, text["raw"], text["raw"] + text["rawsize"])
        print(f"\n-- {name} @ 0x{disp:x}: {len(hits)} load/store site(s); "
              f"{nraw} raw occurrence(s) of the 4 bytes in .text")
        for h in hits:
            print(f"   {h['va']}  {h['bytes']:<20} {h['text']}")
            ctx = context(md, raw, secs, image_base, h["va"])
            for row in ctx:
                extra = ""
                if "float" in row:
                    extra = "   ; rip->%s = %r" % (row["rip_target"], row["float"])
                print(f"        {row['va']}  {row['text']:<44}{extra}")
            h["context"] = ctx
        out[name] = {"disp": disp, "raw_occurrences_in_text": nraw, "hits": hits}

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
