"""chase_verify.py - re-derive every found=true hit of the local-LLM triage, and sample the rest.

Verifies the 22 `found: true` verdicts in `E:\\Modding\\_gamedata\\BmAKgrab\\chase\\verdicts.jsonl` against
their named source: a text file line, or an executable VA.  Nothing is written to the game folder,
nothing is launched, nothing is patched; the exe is opened read-only.

What the exe side does (this is the part chase09_native.py could not do):
  * parses the PE exception directory (.pdata) so every VA gets its **exact** function bounds -
    no INT3-padding guesswork, no starting a disassembly mid-instruction;
  * disassembles the whole enclosing function and finds the instruction that *covers* the claimed
    VA, so a VA the model invented shows up as "no instruction starts here";
  * resolves RIP-relative float constants and prints the store's base register and displacement;
  * profiles the function: which displacements it touches, how wide, and whether `this` (rcx) is
    spilled to a callee-saved register at entry - the shape of a constructor vs. an update routine;
  * checks each touched displacement against the owning class's declared layout
    (`BMSDK_OFFSETS.json`) and flags a 4-byte scalar access that lands *inside* a struct/pointer
    field, which no initialiser of that class could do.

Usage:
  python Tools/scripts/chase/chase_verify.py --va 0x140034dc3 0x14016b9e0
  python Tools/scripts/chase/chase_verify.py --sites 0x2f0 0x2cc 0x2e4      # store-form controls
  python Tools/scripts/chase/chase_verify.py --line "path:3887"
  python Tools/scripts/chase/chase_verify.py --sample 20 --seed 20261029
  python Tools/scripts/chase/chase_verify.py --hits                      # all found=true, grouped
"""
import json
import os
import random
import re
import struct
import sys

EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CHASE = r"E:\Modding\_gamedata\BmAKgrab\chase"
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")


# ---------------------------------------------------------------- PE

def pe(exe):
    e_lfanew = struct.unpack_from("<I", exe, 0x3C)[0]
    nsec = struct.unpack_from("<H", exe, e_lfanew + 6)[0]
    opt = e_lfanew + 24
    image_base = struct.unpack_from("<Q", exe, opt + 24)[0]
    ddir_count = struct.unpack_from("<I", exe, opt + 108)[0]
    ddir_at = opt + 112
    sec_at = opt + struct.unpack_from("<H", exe, e_lfanew + 20)[0]
    secs = []
    for i in range(nsec):
        at = sec_at + 40 * i
        name = exe[at:at + 8].rstrip(b"\x00").decode("latin-1")
        vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", exe, at + 8)
        chars = struct.unpack_from("<I", exe, at + 36)[0]
        secs.append({"name": name, "vaddr": vaddr, "vsize": vsize,
                     "raddr": raddr, "rsize": rsize,
                     "exec": bool(chars & 0x20000000)})
    dirs = []
    for i in range(min(ddir_count, 16)):
        dirs.append(struct.unpack_from("<II", exe, ddir_at + 8 * i))
    return image_base, secs, dirs


def off_to_va(secs, image_base, off):
    for s in secs:
        if s["raddr"] <= off < s["raddr"] + s["rsize"]:
            return image_base + s["vaddr"] + (off - s["raddr"])
    return None


def va_to_off(secs, image_base, va):
    for s in secs:
        base = image_base + s["vaddr"]
        if base <= va < base + s["vsize"]:
            d = va - base
            if d < s["rsize"]:
                return s["raddr"] + d
    return None


def functions(exe, secs, image_base, dirs):
    """RUNTIME_FUNCTION table: [(begin_va, end_va)] sorted."""
    rva, size = dirs[3]                       # IMAGE_DIRECTORY_ENTRY_EXCEPTION
    off = None
    for s in secs:
        if s["vaddr"] <= rva < s["vaddr"] + s["vsize"]:
            off = s["raddr"] + (rva - s["vaddr"])
            break
    if off is None:
        return []
    out = []
    for i in range(size // 12):
        b, e, u = struct.unpack_from("<III", exe, off + 12 * i)
        if b or e:
            out.append((image_base + b, image_base + e))
    out.sort()
    return out


def enclosing(fns, va):
    lo, hi = 0, len(fns) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        b, e = fns[mid]
        if va < b:
            hi = mid - 1
        elif va >= e:
            lo = mid + 1
        else:
            return fns[mid]
    return None


# ---------------------------------------------------------------- disassembly

def disasm_function(exe, secs, image_base, b_va, e_va):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    o = va_to_off(secs, image_base, b_va)
    if o is None:
        return []
    code = exe[o:o + min(e_va - b_va, 0x8000)]
    out = []
    for ins in md.disasm(code, b_va):
        if ins.address >= e_va:
            break
        out.append(ins)
    return out


MEM = re.compile(r"(?:byte|word|dword|qword|xmmword|tbyte)? ?ptr \[([a-z0-9]+)(?: \+ (0x[0-9a-f]+))?\]")
RIP = re.compile(r"\[rip \+ (0x[0-9a-f]+)\]")
IMM_END = re.compile(r", (0x[0-9a-f]+|-?\d+)$")


def operand_mem(op_str):
    m = MEM.search(op_str)
    if not m:
        return None
    return m.group(1), (int(m.group(2), 16) if m.group(2) else 0)


def resolve_rip(exe, secs, image_base, ins, op_str):
    m = RIP.search(op_str)
    if not m:
        return None
    target = ins.address + ins.size + int(m.group(1), 16)
    toff = va_to_off(secs, image_base, target)
    if toff is None or toff + 4 > len(exe):
        return ("va", target, None)
    bits = exe[toff:toff + 4]
    f = struct.unpack("<f", bits)[0]
    return ("va", target, f)


def is_store(ins):
    op = ins.op_str
    if not op or "[" not in op:
        return False
    if ins.mnemonic.startswith(("mov", "vmov")) and ", " in op:
        dst, _, src = op.partition(", ")
        return "[" in dst and "]" in dst.split(",")[0]
    if ins.mnemonic in ("fstp", "fst", "stosd", "stosq", "push"):
        return "[" in op
    return ins.mnemonic in ("or", "and", "xor", "add", "sub", "inc", "dec") and op.startswith(("byte", "word", "dword", "qword"))


def width_of(ins):
    op = ins.op_str
    for w, n in (("byte ptr", 1), ("word ptr", 2), ("dword ptr", 4), ("qword ptr", 8), ("xmmword ptr", 16)):
        if op.startswith(w):
            return n
    if ins.mnemonic.startswith("movss"):
        return 4
    if ins.mnemonic.startswith("movsd"):
        return 8
    return None


# ------------------------------------------------------- native symbol table
#
# The image carries the UE3 native-function table: 16-byte {char* name, void* fn}
# records in .rdata, with names spelled `<Prefix><Class>exec<Function>`
# (e.g. "URVehicleSimBatmobileexecSkidToStop").  That is the only symbol source in an
# otherwise stripped image, and it is what makes class attribution possible at all.

NAME_OK = re.compile(rb"^[A-Za-z0-9_:<>.@$\-]{4,150}$")


def symbol_table(exe, secs, image_base):
    out = {}
    exec_ranges = [(s["raddr"], s["raddr"] + s["rsize"])
                   for s in secs if s["exec"] and s["rsize"]]

    def in_text(off):
        return any(a <= off < b for a, b in exec_ranges)

    for s in secs:
        if s["exec"] or not s["rsize"] or s["name"] not in (".rdata", ".data"):
            continue
        start, end = s["raddr"], s["raddr"] + s["rsize"]
        for k in range(start, end - 16, 16):
            nva, fva = struct.unpack_from("<QQ", exe, k)
            if not (0 <= fva - image_base < len(exe)):
                continue
            noff = va_to_off(secs, image_base, nva)
            if noff is None or not (0x41 <= exe[noff] <= 0x7a):
                continue
            z = exe.find(b"\x00", noff, noff + 160)
            if z < 0:
                continue
            cand = exe[noff:z]
            if not NAME_OK.match(cand):
                continue
            fo = va_to_off(secs, image_base, fva)
            if fo is None or not in_text(fo):
                continue
            out.setdefault(fva, cand.decode("latin-1"))
    return out


# ---------------------------------------------------------------- layout

def layouts():
    d = json.load(open(OFFSETS, encoding="utf-8"))["classes"]
    out = {}
    for name, c in d.items():
        props = sorted(c["properties"], key=lambda p: p["offset"])
        out[name] = props
    return out


STRUCT_SIZE = {"FInterpCurveFloat": 0x14, "Vector3": 0x0c, "FVector": 0x0c,
               "Rotator": 0x0c, "FRotator": 0x0c, "FInterpCurveVector": 0x14}


def field_at(props, disp):
    """The declared field containing `disp`, and whether disp is its exact start."""
    for p in props:
        size = STRUCT_SIZE.get(p.get("type"), 8 if p["kind"] == "ObjectProperty" else 4)
        if p["offset"] <= disp < p["offset"] + size:
            return p, disp == p["offset"]
    return None, False


def layout_note(props, disp, width):
    p, exact = field_at(props, disp)
    if p is None:
        return f"0x{disp:x} is past the last declared field"
    if exact:
        return f"0x{disp:x} = {p['member']} ({p['type']}); exact field start, {width}-byte access"
    size = STRUCT_SIZE.get(p.get("type"), 8 if p["kind"] == "ObjectProperty" else 4)
    return (f"0x{disp:x} lands INSIDE {p['member']} ({p['type']}, {size} B, starts 0x{p['offset']:x}) "
            f"- a {width}-byte scalar store here is not {p['member']}")


# ---------------------------------------------------------------- report pieces

def show_va(exe, secs, image_base, fns, va, ctx_after=10, ctx_before=8, syms=None):
    syms = syms or {}
    r = enclosing(fns, va)
    print(f"\n== VA 0x{va:x}")
    if r is None:
        print("   NOT inside any function in the .pdata table")
        return
    b, e = r
    nm = syms.get(b)
    print(f"   function 0x{b:x} .. 0x{e:x}  ({e - b} bytes)  "
          f"[{'native: ' + nm if nm else 'unnamed - not in the native table'}]")
    for fn_va, fn_name in sorted(syms.items()):
        if va < fn_va < e:
            print(f"   inner native entry at 0x{fn_va:x}: {fn_name}")
    ins = disasm_function(exe, secs, image_base, b, e)
    if not ins:
        print("   disassembly produced nothing")
        return
    idx = None
    for i, x in enumerate(ins):
        if x.address <= va < x.address + x.size:
            idx = i
            break
    if idx is None:
        print("   no instruction covers this VA (bad address / data)")
        return
    if ins[idx].address != va:
        print(f"   NOTE: no instruction starts at 0x{va:x}; the claimed VA is "
              f"{va - ins[idx].address} byte(s) into 0x{ins[idx].address:x}")
    for i in range(max(0, idx - ctx_before), min(len(ins), idx + ctx_after + 1)):
        x = ins[i]
        tail = ""
        r32 = resolve_rip(exe, secs, image_base, x, x.op_str)
        if r32:
            _, tva, f = r32
            if f is not None:
                tail = f"   ; [0x{tva:x}] = float {f!r}"
        mark = ">>" if i == idx else "  "
        print(f"   {mark} 0x{x.address:x}  {x.mnemonic:<8} {x.op_str}{tail}")
    t = ins[idx]
    mem = operand_mem(t.op_str)
    print(f"   -- claimed instruction is a {'STORE' if is_store(t) else 'NON-STORE'} "
          f"({t.mnemonic}); width {width_of(t)}; memory operand {mem}")
    # function profile
    bases = {}
    for x in ins:
        m = MEM.search(x.op_str)
        if not m:
            continue
        base = m.group(1)
        disp = int(m.group(2), 16) if m.group(2) else 0
        st = is_store(x) and x.op_str.startswith(("byte", "word", "dword", "qword", "xmmword")) or "[" in x.op_str.split(",")[0]
        bases.setdefault(base, []).append((disp, width_of(x), is_store(x)))
    print("   -- displacements touched per base register (store/load):")
    for base, rows in sorted(bases.items(), key=lambda kv: -len(kv[1]))[:4]:
        disp = sorted({r[0] for r in rows if r[0] >= 0x100})
        shown = ", ".join(f"0x{d:x}" for d in disp[:18]) + (" ..." if len(disp) > 18 else "")
        print(f"      {base}: {len(rows)} access(es), {len(disp)} distinct disp>=0x100: {shown}")
    # this-pointer / frame-pointer probe
    head = " ; ".join(f"{x.mnemonic} {x.op_str}" for x in ins[:12])
    print(f"   -- entry (12): {head}")
    this_reg = None
    frame_reg = None
    for x in ins[:40]:
        m = re.match(r"(r[a-z0-9]+), rcx$", x.op_str)
        if m and x.mnemonic == "mov" and m.group(1) in ("rbx", "rbp", "rsi", "rdi", "r12", "r13", "r14", "r15"):
            this_reg = this_reg or m.group(1)
        m = re.match(r"rbp, rsp$", x.op_str)
        if x.mnemonic == "mov" and m:
            frame_reg = "rsp"
        m = re.match(r"rbp, \[rsp \+ (0x[0-9a-f]+)\]$", x.op_str)
        if x.mnemonic == "lea" and m:
            frame_reg = "lea rsp+" + m.group(1)
    print(f"   -- rcx spilled to {this_reg or 'nothing in the first 40 ins'}; "
          f"rbp = frame pointer ({frame_reg or 'not established in the first 40 ins'})")
    if mem:
        print(f"   -- store base '{mem[0]}' is "
              f"{'the stack frame, not an object' if mem[0] in ('rsp', 'rbp') and mem[0] != this_reg else ('this (' + this_reg + ')' if mem[0] == this_reg else 'neither this nor the frame')}")
    calls = [x.op_str for x in ins if x.mnemonic == "call"][:4]
    named = [(c, syms.get(int(c, 16))) for c in calls if c.startswith("0x")]
    print(f"   -- first calls: {calls}")
    print(f"   -- named call targets: {[(c, n) for c, n in named if n] or 'none'}")
    return ins


def show_line(spec):
    path, _, ln = spec.rpartition(":")
    if not os.path.exists(path):
        print(f"\n== {spec}\n   FILE MISSING: {path}")
        return
    lines = open(path, "r", encoding="utf-8", errors="replace").read().splitlines()
    n = int(ln)
    print(f"\n== {spec}  ({len(lines)} lines in file)")
    for i in range(max(0, n - 3), min(len(lines), n + 2)):
        mark = ">>" if i + 1 == n else "  "
        print(f"   {mark} {i + 1}: {lines[i][:240]}")


def hits():
    cand = {json.loads(l)["id"]: json.loads(l)
            for l in open(os.path.join(CHASE, "candidates.jsonl"), encoding="utf-8")}
    ver = [json.loads(l) for l in open(os.path.join(CHASE, "verdicts.jsonl"), encoding="utf-8")]
    found = [v for v in ver if v.get("found") is True]
    print(f"candidates {len(cand)} | verdicts {len(ver)} | found=true {len(found)}")
    for v in found:
        c = cand[v["id"]]
        print(f"{v['id']}\t{c['row']}\t{c['member']}\t{c['owner']}\t{c['offset']}\t"
              f"{c['type']}\t{v['source']}\t{str(v.get('value'))[:40]}\t{c.get('route')}")
    return found, cand


def sample(n, seed):
    cand = {json.loads(l)["id"]: json.loads(l)
            for l in open(os.path.join(CHASE, "candidates.jsonl"), encoding="utf-8")}
    ver = [json.loads(l) for l in open(os.path.join(CHASE, "verdicts.jsonl"), encoding="utf-8")]
    rest = [v for v in ver if v.get("found") is not True]
    rnd = random.Random(seed)
    pick = rnd.sample(rest, min(n, len(rest)))
    print(f"found=false pool {len(rest)} | sample {len(pick)} (seed {seed})")
    for v in pick:
        c = cand[v["id"]]
        print(f"\n-- {v['id']}  {c['row']} {c['member']} @0x{int(c['offset'], 16):x} "
              f"({c['type']}, {c['owner']})  route {c.get('route')}")
        print(f"   source: {v['source']}")
        print(f"   why:    {v.get('why')}")
        s = c["snippet"]
        print(f"   snippet ({len(s)} B): {s[:400].replace(chr(10), ' | ')}")
    return pick


def sites(offs, exe, secs, image_base):
    import importlib.util
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chase09_native.py")
    spec = importlib.util.spec_from_file_location("chase09_native", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for d in offs:
        hs = mod.find_stores(exe, d, limit=60)
        print(f"\n-- displacement 0x{d:x} ({d}): {len(hs)} store-form hit(s)")
        for h in hs[:30]:
            print(f"   file 0x{h['off']:08x} -> VA 0x{off_to_va(secs, image_base, h['off']):x}  {h['what']}")


TYPE_WIDTH = {"float": 4, "int": 4, "bool": 1, "FInterpCurveFloat": 20, "Vector3": 12}


def match_class(exe, secs, image_base, fns, va, cls, props, force_reg=None):
    """Is the function containing `va` shaped like code over `cls` (and is it a ctor)?"""
    r = enclosing(fns, va)
    if r is None:
        print(f"\n== 0x{va:x}: not in the .pdata table")
        return
    b, e = r
    ins = disasm_function(exe, secs, image_base, b, e)
    this_reg = force_reg
    for x in ([] if force_reg else ins[:40]):
        m = re.match(r"(rbx|rbp|rsi|rdi|r12|r13|r14|r15), rcx$", x.op_str)
        if m and x.mnemonic == "mov":
            this_reg = m.group(1)
            break
    print(f"\n== 0x{va:x} in function 0x{b:x}..0x{e:x} ({len(ins)} ins); this -> {this_reg}; "
          f"class {cls} ({len(props)} declared fields)")
    if this_reg is None:
        print("   no rcx spill in the first 40 instructions: no `this` register to test")
        return
    exact = inside = unknown = other = 0
    rows = []
    seen = {}
    for x in ins:
        m = MEM.search(x.op_str)
        if not m or m.group(1) != this_reg:
            continue
        d = int(m.group(2), 16) if m.group(2) else 0
        if d < 0x100:
            continue
        w = width_of(x)
        if d not in seen:
            seen[d] = (w, is_store(x))
    for d, (w, st) in sorted(seen.items()):
        p, ex = field_at(props, d)
        if p is None:
            note = "past last field"
            unknown += 1
        elif ex:
            tw = TYPE_WIDTH.get(p.get("type"), 8 if p["kind"] == "ObjectProperty" else 4)
            ok = (w is None) or (w == tw) or (p.get("type") == "FInterpCurveFloat" and w == 8)
            note = f"{p['member']} ({p['type']})" + ("" if ok else f"  WIDTH {w} != {tw}")
            if ok:
                exact += 1
            else:
                other += 1
        else:
            note = f"INSIDE {p['member']} ({p['type']}) - no initialiser of {cls} writes here"
            inside += 1
        rows.append((d, w, st, note))
    for d, w, st, note in rows[:40]:
        print(f"   0x{d:x}  w{w}  {'STORE' if st else 'load '}  {note}")
    print(f"   -- {exact} displacement(s) are exact {cls} field starts, {other} width-mismatched, "
          f"{inside} land inside another field, {unknown} past the last field")
    vtable = [x for x in ins[:20] if x.mnemonic == "mov" and x.op_str.startswith("qword ptr [")
              and x.op_str.endswith(", rax")]
    first_store = next((i for i, x in enumerate(ins) if is_store(x)), None)
    print(f"   -- constructor markers: vtable-shaped store in first 20 ins: "
          f"{[x.op_str for x in vtable] or 'none'}; first store at ins #{first_store}")


def screen(exe, secs, image_base, fns):
    """Every found=false exe hit: is the instruction a store to the row offset from a literal?"""
    cand = {json.loads(l)["id"]: json.loads(l)
            for l in open(os.path.join(CHASE, "candidates.jsonl"), encoding="utf-8")}
    ver = [json.loads(l) for l in open(os.path.join(CHASE, "verdicts.jsonl"), encoding="utf-8")]
    pool = [v for v in ver if v.get("found") is not True and cand[v["id"]].get("route") == "exe"]
    print(f"found=false exe hits: {len(pool)}")
    stat = {"va_bad": 0, "not_store": 0, "wrong_disp": 0, "stack": 0, "nonliteral": 0, "literal": 0}
    lits = []
    cache = {}
    for v in pool:
        c = cand[v["id"]]
        m = re.search(r"0x([0-9a-f]+)", v["source"])
        if not m:
            stat["va_bad"] += 1
            continue
        va = int(m.group(1), 16)
        r = enclosing(fns, va)
        if r is None:
            stat["va_bad"] += 1
            continue
        if r not in cache:
            cache[r] = disasm_function(exe, secs, image_base, r[0], r[1])
        ins = cache[r]
        t = next((x for x in ins if x.address <= va < x.address + x.size), None)
        if t is None or not is_store(t):
            stat["not_store"] += 1
            continue
        mem = operand_mem(t.op_str)
        want = int(c["offset"], 16)
        if not mem or mem[1] != want:
            stat["wrong_disp"] += 1
            continue
        if mem[0] in ("rsp", "rbp"):
            stat["stack"] += 1
            continue
        rip = resolve_rip(exe, secs, image_base, t, t.op_str)
        imm = IMM_END.search(t.op_str)
        if rip and rip[2] is not None:
            stat["literal"] += 1
            lits.append((v["id"], c["row"], c["member"], c["offset"], va, r[0],
                         f"{t.mnemonic} {t.op_str}", f"rip float {rip[2]!r}"))
        elif imm:
            stat["literal"] += 1
            lits.append((v["id"], c["row"], c["member"], c["offset"], va, r[0],
                         f"{t.mnemonic} {t.op_str}", f"imm {imm.group(1)}"))
        else:
            stat["nonliteral"] += 1
    print("   " + "  ".join(f"{k}={n}" for k, n in stat.items()))
    for row in lits:
        print("   LITERAL-STORE %s %s %s @%s  VA 0x%x fn 0x%x  %s  <- %s" % row)


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    exe = None

    def load():
        nonlocal exe
        if exe is None:
            exe = open(EXE, "rb").read()
        return exe

    cmd = argv[0]
    if cmd == "--hits":
        hits()
        return 0
    if cmd == "--sample":
        n = int(argv[1]) if len(argv) > 1 else 20
        seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 20261029
        sample(n, seed)
        return 0
    if cmd == "--line":
        for spec in argv[1:]:
            show_line(spec)
        return 0
    if cmd == "--sites":
        exe = load()
        image_base, secs, _ = pe(exe)
        sites([int(x, 0) for x in argv[1:]], exe, secs, image_base)
        return 0
    if cmd == "--va":
        exe = load()
        image_base, secs, dirs = pe(exe)
        fns = functions(exe, secs, image_base, dirs)
        print(f"{EXE}: {len(exe)} B, image base 0x{image_base:x}, "
              f"{len(secs)} sections, {len(fns)} runtime functions")
        for a in argv[1:]:
            va = int(a, 0)
            show_va(exe, secs, image_base, fns, va, syms=symbol_table(exe, secs, image_base))
        return 0
    if cmd == "--screen":
        exe = load()
        image_base, secs, dirs = pe(exe)
        screen(exe, secs, image_base, functions(exe, secs, image_base, dirs))
        return 0
    if cmd == "--match":
        exe = load()
        image_base, secs, dirs = pe(exe)
        fns = functions(exe, secs, image_base, dirs)
        lay = layouts()
        va = int(argv[1], 0)
        cls = argv[2]
        reg = argv[3] if len(argv) > 3 else None
        match_class(exe, secs, image_base, fns, va, cls, lay[cls], reg)
        return 0
    if cmd == "--symbols":
        exe = load()
        image_base, secs, _ = pe(exe)
        syms = symbol_table(exe, secs, image_base)
        pat = re.compile(argv[1], re.I) if len(argv) > 1 else re.compile(".")
        sel = {va: n for va, n in syms.items() if pat.search(n)}
        print(f"native table: {len(syms)} named functions; {len(sel)} match {pat.pattern!r}")
        for va, n in sorted(sel.items()):
            print(f"   0x{va:x}  {n}")
        return 0
    if cmd == "--raw":
        exe = load()
        image_base, secs, _ = pe(exe)
        start = int(argv[1], 0)
        ln = int(argv[2], 0) if len(argv) > 2 else 0x40
        o = va_to_off(secs, image_base, start)
        print(f"\n== raw bytes at VA 0x{start:x} (file 0x{o:x}), {ln} B")
        print("   " + exe[o:o + ln].hex(" "))
        from capstone import Cs, CS_ARCH_X86, CS_MODE_64
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        for x in md.disasm(exe[o:o + ln], start):
            print(f"   0x{x.address:x}  {x.mnemonic:<8} {x.op_str}")
        return 0
    if cmd == "--layout":
        props = layouts()
        cls = argv[1]
        disp = int(argv[2], 0)
        width = int(argv[3]) if len(argv) > 3 else 4
        print(layout_note(props[cls]["properties"] if isinstance(props[cls], dict) else props[cls], disp, width))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
