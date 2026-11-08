"""chase2_04_native.py - chase2-04 route (b): what WRITES the field, and what seeds it?

chase-04 (first pass) matched only the two narrow store forms `movss [reg+disp32], xmm` and
`mov dword [reg+disp32], imm32`, and concluded that the single store to `[reg+0x1758]` is the
`subss` decrement of `ImpactRoadAssistTimer`. That is enough to say "no immediate default is written"
but not enough to say where the timer's value COMES FROM: a seed can also arrive as

  * a 16-byte SSE copy  (`movups/movaps/movdqu [reg+disp], xmm`) whose range covers the field,
  * an 8-byte copy       (`movsd/movq/movlps/movhps`), 
  * an x87 store         (`fstp dword [reg+disp]`, `fstp qword ...`),
  * a general-register copy of the float bits (`mov [reg+disp], eax`).

This script therefore scans for EVERY store whose memory range **overlaps** [off, off+4), not just
the exact 4-byte forms. Candidate displacements are collected as raw little-endian 32-bit values in
[off-32, off+4), each window is disassembled from the preceding INT3 padding (so no instruction is
started mid-bytes), and an instruction is kept only if Capstone shows a memory write whose
displacement plus operand width covers `off`. For each kept store it prints:

    VA, instruction bytes, mnemonic + operands, and — when the source is an xmm register loaded from
    a RIP-relative address or an immediate — the constant that feeds it.

Then it dumps the whole enclosing function (padding → `ret`) so the seeding logic around the store is
visible, and lists the direct call sites of that function (call rel32 targets), because the caller is
where a "start the countdown" value would be written from.

Read-only static analysis of the shipped exe: opened `rb`, never patched, never run.

Usage:
  python Tools/scripts/chase/chase2_04_native.py 0x1758 [--fn] [--callers] [--json OUT.json]
"""
import argparse
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chase09_native as n9  # sections / off_to_va / va_to_off / window_start / disasm  # noqa: E402

EXE = n9.EXE
OUT = r"E:\Modding\_gamedata\BmAKgrab\chase\chase2_04_native.json"

# operand widths, so a wide store can be tested for overlap with the 4-byte field
WIDTH = [
    (r"\b(movups|movaps|movdqu|movdqa|movntps|movntdq)\b", 16),
    (r"\b(movsd|movq|movlps|movhps|movlpd|movhpd|movntq|fstp qword|fst qword|fld qword)\b", 8),
    (r"\b(movss|movd|fstp dword|fst dword|fild dword|fistp dword)\b", 4),
    (r"\b(mov byte|movzx byte|fstp dword)\b", 1),
    (r"\bxmm\b", 16),
    (r"\bymm\b", 32),
]
# mnemonics that never write memory of interest (loads) are excluded by checking operand position
STORE_PREFIX = re.compile(r"^(mov|fst|fild|fist|stos|push|vmov)")

MEM = re.compile(r"\[([^\]]+)\]")


def mem_operand(op_str: str):
    """(index, text) of the memory operand in an Intel-syntax operand list, or (None, '')."""
    depth = 0
    cur = []
    ops = []
    for ch in op_str:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            ops.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        ops.append("".join(cur).strip())
    for i, o in enumerate(ops):
        if "[" in o:
            return i, o, ops
    return None, "", ops


def width_of(ins: dict, mem_text: str) -> int:
    text = f"{ins['mnemonic']} {ins['op_str']}"
    for pat, w in WIDTH:
        if re.search(pat, text):
            return w
    # plain `mov dword ptr [...]` / `mov qword ptr [...]`
    m = re.search(r"\b(dword|qword|word|byte) ptr", mem_text)
    if m:
        return {"dword": 4, "qword": 8, "word": 2, "byte": 1}[m.group(1)]
    # register source: infer from the register name
    src = mem_text.split(", ")[-1] if "," in ins["op_str"] else ""
    for pat, w in ((r"\b[re]?[abcd]x\b|\be[sd]i\b|\be[sb]p\b", 4), (r"\b[r8-9]|r1[0-5]", 4)):
        if re.search(pat, src):
            return 4
    return 0


def disp_in(ins: dict):
    """Displacement (unsigned) of the first memory operand, plus its register string."""
    m = re.search(r"\[\s*([a-z0-9]+)\s*\+\s*(0x[0-9a-f]+)\s*\]", ins["op_str"])
    if m:
        return int(m.group(2), 16), m.group(1)
    m = re.search(r"\[\s*([a-z0-9]+)\s*\]", ins["op_str"])
    if m:
        return 0, m.group(1)
    return None, None


def rip_value(exe, secs, image_base, ins, rows, idx):
    """Resolve a RIP-relative operand of `ins` to the 4 bytes it points at."""
    m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", ins["op_str"])
    if not m:
        return None
    nxt = rows[idx + 1]["addr"] if idx + 1 < len(rows) else None
    if nxt is None:
        return None
    target = nxt + int(m.group(1), 16)
    toff = n9.va_to_off(secs, image_base, target)
    if toff is None or toff + 4 > len(exe):
        return None
    bits = exe[toff:toff + 4]
    return {"target": target, "file_off": toff,
            "u32": struct.unpack("<I", bits)[0],
            "f32": round(struct.unpack("<f", bits)[0], 6),
            "bytes": bits.hex(" ")}


def find_overlapping_stores(exe: bytes, secs, image_base: int, off: int, back: int = 0x30):
    """Every store whose [disp, disp+width) covers one byte of [off, off+4)."""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = False
    cands = []
    seen = set()
    for disp in range(max(0, off - back), off + 4):
        pat = struct.pack("<I", disp)
        start = 0
        while True:
            i = exe.find(pat, start)
            if i < 0:
                break
            start = i + 1
            # the disp32 ends at i+4; the instruction starts at most 11 bytes earlier
            for lo in range(i - 11, i + 1):
                if lo < 0:
                    continue
                ws = n9.window_start(exe, lo, back=0x200)
                rows = n9.disasm(exe, secs, image_base, ws, min(len(exe), i + 0x30))
                for k, ins in enumerate(rows):
                    d, reg = disp_in(ins)
                    if d is None or d != disp:
                        continue
                    # `ins["addr"]` is a VA; containment has to be tested in file offsets
                    if ins["off"] is None or not (ins["off"] <= i <= ins["off"] + 10):
                        continue
                    if not STORE_PREFIX.match(ins["mnemonic"]):
                        continue
                    idx, mem, ops = mem_operand(ins["op_str"])
                    if idx is None:
                        continue
                    w = width_of(ins, mem)
                    if not w:
                        continue
                    # Intel syntax: the memory operand is the destination only when it is
                    # written first (`mov dword ptr [rcx+0x1758], xmm0`); idx 1 is a load.
                    if idx != 0:
                        continue
                    if not (d < off + 4 and d + w > off):
                        continue
                    key = (ins["addr"], w)
                    if key in seen:
                        continue
                    seen.add(key)
                    notes = []
                    for j, prev in enumerate(rows[:k]):
                        if prev["mnemonic"].startswith("movss") or prev["mnemonic"].startswith("movups"):
                            rv = rip_value(exe, secs, image_base, prev, rows, j)
                            if rv:
                                notes.append({"from": prev["op_str"], "const": rv})
                    cands.append({"va": ins["addr"], "file_off": n9.va_to_off(secs, image_base, ins["addr"]),
                                  "text": f"{ins['mnemonic']} {ins['op_str']}".strip(),
                                  "width": w, "disp": d, "reg": reg, "notes": notes})
                    break
    return sorted({c["va"]: c for c in cands}.values(), key=lambda c: c["va"])


def function_bounds(exe: bytes, off: int):
    """Padding-delimited body around `off`: (start_off, end_off) at the next INT3 run after it."""
    start = n9.window_start(exe, off, back=0x1200)
    i = off + 1
    while i < len(exe) - 1:
        if exe[i] in (0xCC, 0x90) and exe[i + 1] in (0xCC, 0x90) and exe[i + 2] in (0xCC, 0x90):
            return start, i
        i += 1
    return start, min(len(exe), off + 0x800)


def callers_of(exe: bytes, secs, image_base: int, va: int):
    """Direct `call rel32` sites whose target is `va`."""
    hits = []
    for i in range(len(exe) - 5):
        if exe[i] != 0xE8:
            continue
        rel = struct.unpack_from("<i", exe, i + 1)[0]
        site = n9.off_to_va(secs, image_base, i)
        if site is None:
            continue
        if site + 5 + rel == va:
            hits.append(site)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("offs", nargs="+", type=lambda s: int(s, 0))
    ap.add_argument("--json", default=OUT)
    a = ap.parse_args()
    exe = open(EXE, "rb").read()
    image_base, secs = n9.sections(exe)
    print(f"{EXE}: {len(exe):,} B, image base 0x{image_base:x}")
    report = {"exe": EXE, "exe_bytes": len(exe), "image_base": image_base, "rows": []}
    for off in a.offs:
        print(f"\n=== offset 0x{off:x} ({off}) ===")
        stores = find_overlapping_stores(exe, secs, image_base, off)
        print(f"{len(stores)} store(s) overlap [0x{off:x}, 0x{off+4:x})")
        row = {"offset": off, "stores": []}
        for s in stores:
            raw = exe[s["file_off"]:s["file_off"] + 12] if s["file_off"] is not None else b""
            print(f"  VA 0x{s['va']:x}  file 0x{s['file_off']:08x}  width {s['width']}  "
                  f"{s['text']}")
            print(f"      bytes {raw[:8].hex(' ')}")
            for n in s["notes"]:
                print(f"      fed by `{n['from']}` -> const at file 0x{n['const']['file_off']:08x} "
                      f"= {n['const']['f32']!r} (0x{n['const']['u32']:08x})")
            s = dict(s, bytes=raw[:8].hex(" "))
            row["stores"].append(s)
        if stores:
            va = stores[0]["va"]
            f_off = n9.va_to_off(secs, image_base, va)
            s0, s1 = function_bounds(exe, f_off)
            print(f"  enclosing function 0x{s0:08x}..0x{s1:08x} "
                  f"({s1 - s0} B, VA 0x{n9.off_to_va(secs, image_base, s0):x})")
            row["function"] = {"start_off": s0, "end_off": s1,
                               "start_va": n9.off_to_va(secs, image_base, s0),
                               "end_va": n9.off_to_va(secs, image_base, s1)}
            for ins in n9.disasm(exe, secs, image_base, s0, min(len(exe), s1)):
                print(f"    VA 0x{ins['addr']:x}  {ins['mnemonic']:<8} {ins['op_str']}")
            cls = callers_of(exe, secs, image_base, n9.off_to_va(secs, image_base, s0))
            print(f"  callers of the function entry: {len(cls)}")
            for c in cls[:20]:
                print(f"    call site VA 0x{c:x}")
            row["callers"] = cls
        report["rows"].append(row)
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w", encoding="utf8", newline="\n") as f:
        json.dump(report, f, indent=1)
    print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
