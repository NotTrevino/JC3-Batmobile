"""chase_candidates.py - the SEARCH half of the two-stage G1 value chase (no judging).

The local judge (`Tools/scripts/chase/chase_judge.py`) answers one hit at a time; it only needs
candidates.  This tool produces them, one JSON object per line:

  {"id": "F-18#0001", "row": "F-18", "member": "StrafeForce", "owner": "RVehicleBatmobileBase",
   "offset": "0x11f8", "type": "float", "source": "exe 0x14123abcd" | "<path>:<offset>",
   "snippet": "<disassembly window or text context>", "route": "exe" | "text"}

What it does, in order:

  1. reads every `F-` row of `Research/BatmobileGrab/FOOTAGE.md` that is still `UNKNOWN` and not
     closed in any `Research/BatmobileGrab/chase/chase-NN.md` / `chase2-NN.md`, and takes the
     member name, owning class, type and field offset out of the row's own text
     (`declared on `Owner` at 0xNN as `type``);
  2. **route EXE** - for a row with an offset, every store site for that displacement in
     `BatmanAK.exe` (read only): `movss [reg+disp32], xmm` and `mov dword [reg+disp32], imm32`
     (plus the disp8 forms when the offset is < 0x80), using `chase09_native.py`'s own scanner
     (`find_stores`, `window_start`, `disasm`, `sections`, ... - imported, not copied), each
     disassembled from the INT3 padding before it to ~40 instructions after, with every
     RIP-relative float constant the window reads resolved and printed inline.  Sites are then
     rejected mechanically before they can reach the judge (`store_verdict`): a stack-frame base
     (`rsp`, or `rbp`, or any register loaded from them), a read of the same displacement earlier
     in the window (`+=`, delta-scaled updates), a computed value (arithmetic on the source
     register), a store with no literal visible in the window (field copy / register-sourced), and
     a literal that is the field offset itself or within 0x40 of it.  The per-rule counts are
     printed with the row counts;
  3. **route TEXT** - every whole-word, case-insensitive occurrence of the member name in
     **game-derived text only**: the install's `Config/**` and `Localization/**` and the
     non-chase `.txt`/`.config` dumps under `E:\\Modding\\_shared\\gamedata\\BmAKgrab` - never `.json`/`.jsonl`/
     `.md`/`.csv`/`.log` and never anything under `_BmAKgrab/chase`, since a hit in our own offset
     maps, name-scan counts or verdicts is the question echoed back.  A JSON-shaped hit line is
     dropped as bookkeeping.  20 lines (or a 1 KB window for a minified line) of context;
  4. writes `E:\\Modding\\_shared\\gamedata\\BmAKgrab\\chase\\candidates.jsonl` (game-derived data stays outside the
     repo), capped at 400 candidates per row - the ones whose window names the owning class or
     shows a constructor-like pattern first, with the overflow count printed;
  5. `--check` re-runs the whole scan and requires the file to be byte-identical and every id to be
     unique.

Nothing here judges a candidate, and nothing writes to the game folder: the executable and the
ini files are opened read-only.

Usage:
  python Tools/scripts/chase/chase_candidates.py --write        # scan, write the JSONL, print counts
  python Tools/scripts/chase/chase_candidates.py --check        # re-scan, compare, verify ids
  python Tools/scripts/chase/chase_candidates.py --list-rows    # the row plan only (no scan)
  python Tools/scripts/chase/chase_candidates.py --member StrafeForce --owner RVehicleBatmobileBase \
         --offset 0x11f8 --type float [--routes exe,text] [--out x.jsonl]   # ONE member

The one-member mode is also importable (`member_candidates`); `smart_search.py` judges its output.
The row-plan output above is unchanged by it.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import chase09_native as native  # noqa: E402  (the EXE scanner, reused not copied)

FOOTAGE = os.path.join(ROOT, "Research", "BatmobileGrab", "FOOTAGE.md")
CHASE_DIR = os.path.join(ROOT, "Research", "BatmobileGrab", "chase")
OUT = os.path.join(r"E:\Modding\_shared\gamedata\BmAKgrab", "chase", "candidates.jsonl")
GAME_CFG = os.path.join(r"E:\Games\Batman - Arkham Knight", "BmGame", "Config")
GAME_BIN = os.path.join(r"E:\Games\Batman - Arkham Knight", "Binaries", "Win64")
TEXT_ROOT = os.path.join(r"E:\Modding\_shared\gamedata\BmAKgrab")

MAX_PER_ROW = 400
SNIPPET_CAP = 12 * 1024
TEXT_CONTEXT_LINES = 20
BINARY_WINDOW = 1024
EXE_WINDOW_AFTER = 40          # instructions after the store
# v2 corpus rule: game-derived text only.  Everything the project wrote about the question -
# `_BmAKgrab/chase/**` (candidate lists, verdicts, selftest, offset maps, name scans) and every
# `.json`/`.jsonl`/`.md`/`.csv`/`.log` - is excluded, because a hit in our own bookkeeping is the
# question echoed back.  Twelve of v1's twenty-two false positives were made of exactly that.
TEXT_EXTS = (".txt", ".config", ".cfg", ".ini", ".int")
TEXT_SKIP_DIRS = ("chase", "cache", "calib_runs", "__pycache__")
TEXT_SKIP_EXTS = (".json", ".jsonl", ".md", ".log", ".csv")

GAME_LOC = os.path.join(r"E:\Games\Batman - Arkham Knight", "BmGame", "Localization")

DECLARED_RE = re.compile(r"declared on `([^`]+)` at (0x[0-9a-fA-F]+) as `([^`]+)`")
TICK_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
FROW_RE = re.compile(r"^\|\s*(F-\d+)\s*\|")
# a row is closed when a chase file says so on a line that names it
CLOSE_MARKERS = ("FOUND", "RESOLVED", "Closed:")
OPEN_MARKERS = ("STILL UNKNOWN", "STATUS: STILL UNKNOWN")


# --------------------------------------------------------------------------------------- FOOTAGE
def parse_footage() -> list[dict]:
    rows = []
    for line in open(FOOTAGE, encoding="utf-8"):
        m = FROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        text = " ".join(cells)
        d = DECLARED_RE.search(text)
        member = owner = ftype = None
        offset = None
        if d:
            owner, offset, ftype = d.group(1), d.group(2).lower(), d.group(3)
        # the member name: a bare identifier in the question cell, else the first backticked
        # identifier there, else the first backticked name in the evidence that is neither the
        # owning class nor the type (F-4 names its function in the question, F-68 a field in prose)
        q = cells[1].strip().strip("`")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", q):
            member = q
        else:
            names = TICK_RE.findall(cells[1])
            if not names:
                names = [n for n in TICK_RE.findall(cells[3])
                         if n not in (owner, ftype) and not n[0].islower()]
            member = names[0] if names else None
        if owner is None:
            om = re.search(r"declared on `([^`]+)`", text)
            owner = om.group(1) if om else None
        rows.append({"id": m.group(1), "question": cells[1], "source": cells[2],
                     "evidence": cells[3], "status": cells[4], "code": cells[5],
                     "member": member, "owner": owner, "offset": offset, "type": ftype,
                     "text": text})
    return rows


def expand_ids(line: str) -> list[str]:
    """F ids on a line, with `F-a ... F-b` / `F-a to F-b` ranges expanded (the chase files state a
    result once for a run of rows: `Rows F-9 ... F-16 should move to RESOLVED`)."""
    ids = re.findall(r"\bF-(\d+)\b", line)
    out = {int(i) for i in ids}
    for a, b in re.findall(r"\bF-(\d+)\s*(?:…|\.\.\.|–|-|to)\s*F-(\d+)\b", line):
        lo, hi = sorted((int(a), int(b)))
        out.update(range(lo, hi + 1))
    return [f"F-{i}" for i in sorted(out)]


def chase_closures() -> tuple[dict[str, list[tuple[str, int, str]]],
                              dict[str, list[tuple[str, int, str]]], list[str]]:
    """(closed, opened, files): per F id the (file, line, text) lines that say FOUND / resolved,
    and the lines that say STILL UNKNOWN.  A line that re-opens a row wins over an earlier FOUND.
    Both the summary tables and the per-row `## F-n` sections are read."""
    closed: dict[str, list] = {}
    opened: dict[str, list] = {}
    files = sorted(glob.glob(os.path.join(CHASE_DIR, "chase-*.md"))
                   + glob.glob(os.path.join(CHASE_DIR, "chase2-*.md")))
    heading_re = re.compile(r"^##\s+(F-\d+)\b")
    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        section = None
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            h = heading_re.match(line)
            if h:
                section = h.group(1)
            ids = expand_ids(line)
            if section and section not in ids:
                ids.append(section)
            if not ids:
                continue
            if any(m in line for m in OPEN_MARKERS):
                for fid in ids:
                    opened.setdefault(fid, []).append((rel, i, line.strip()))
            elif any(m in line for m in CLOSE_MARKERS):
                for fid in ids:
                    closed.setdefault(fid, []).append((rel, i, line.strip()))
    return closed, opened, files


def plan_rows() -> tuple[list[dict], list[dict], list[dict], list[dict], list[str]]:
    """(to chase, closed in a chase, not UNKNOWN in FOOTAGE, no member name, chase files read)."""
    rows = parse_footage()
    closed, opened, files = chase_closures()
    chase, excluded, unknown_status, nomember = [], [], [], []
    for r in rows:
        if "UNKNOWN" not in r["status"]:
            unknown_status.append({**r, "why": f"FOOTAGE status is {r['status']}"})
            continue
        if r["id"] in closed:
            f, ln, text = closed[r["id"]][0]
            reopened = r["id"] in opened
            r["closed_at"] = f"{f}:{ln}: {text[:160]}"
            r["reopened_at"] = (f"{opened[r['id']][0][0]}:{opened[r['id']][0][1]}"
                                if reopened else None)
            if not reopened:
                excluded.append({**r, "why": f"closed in {f}:{ln} - {text[:140]}"})
                continue
        if not r["member"]:
            nomember.append({**r, "why": "no member name in the row text"})
            continue
        chase.append(r)
    return chase, excluded, unknown_status, nomember, files


# -------------------------------------------------------------------------------------- EXE route
def disp8_stores(exe: bytes, disp: int, limit: int) -> list[dict]:
    """The disp8 forms of the two store shapes, when the displacement fits in one byte.

    `chase09_native.find_stores` packs the displacement as a 32-bit pattern, so it only sees
    disp32 sites; this is the one addition, and it reuses the same window/disassembly helpers.
    """
    hits = []
    d = bytes([disp])
    for m in re.finditer(rb"\xf3\x0f\x11[\x40-\x7f]", exe):
        i = m.start()
        if exe[i + 3] == disp:
            hits.append({"off": i, "disp_at": i + 3,
                         "what": "movss [reg+0x%x], xmm (disp8)" % disp})
            if len(hits) >= limit:
                return hits
    for m in re.finditer(rb"\xc7[\x40-\x7f]" + re.escape(d), exe):
        hits.append({"off": m.start(), "disp_at": m.start() + 2,
                     "what": "mov dword [reg+0x%x], imm32 (disp8)" % disp})
        if len(hits) >= limit:
            break
    return hits


def exe_window(exe: bytes, secs, image_base: int, off: int, after: int) -> list[dict]:
    """Disassemble from the INT3 padding before the store to ~`after` instructions past it.

    A window that starts on an undecodable byte yields nothing (Capstone stops at the first bad
    instruction), so the start walks forward until the run covers the store - a hit that sits in
    data still returns its best window instead of an empty snippet.
    """
    base = native.window_start(exe, off)
    rows: list[dict] = []
    for shift in range(0, 128):
        rows = native.disasm(exe, secs, image_base, base + shift,
                             min(len(exe), off + 0x400))
        addrs = [r["off"] for r in rows if r["off"] is not None]
        if addrs and max(addrs) >= off:
            break
    past = 0
    keep = []
    for r in rows:
        keep.append(r)
        if r["off"] is not None and r["off"] > off:
            past += 1
            if past >= after:
                break
    return keep


def annotate(exe: bytes, secs, image_base: int, rows: list[dict], store_off: int) -> str:
    """Disassembly text with every RIP-relative float constant resolved inline."""
    out = []
    for i, r in enumerate(rows):
        note = ""
        m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", r["op_str"])
        if m and i + 1 < len(rows):
            target = rows[i + 1]["addr"] + int(m.group(1), 16)
            toff = native.va_to_off(secs, image_base, target)
            if toff is not None and toff + 4 <= len(exe):
                bits = exe[toff:toff + 4]
                f = __import__("struct").unpack("<f", bits)[0]
                i32 = __import__("struct").unpack("<I", bits)[0]
                note = f"   ; [0x{target:x}] = float {f!r} (0x{i32:08x})"
        mark = ">> " if r["off"] == store_off else "   "
        out.append(f"{mark}0x{r['addr']:x}  {r['mnemonic']:<8} {r['op_str']}{note}")
    return "\n".join(out)


def constructor_like(snippet: str) -> bool:
    """A window that looks like object initialisation rather than a per-frame update: a vtable
    style `lea reg, [rip+...]` followed by a store through a register, or the owner's name."""
    return bool(re.search(r"lea\s+\w+, \[rip", snippet)) and "call" not in snippet


# ------------------------------------------------------------------- mechanical rejections (v2)
# v1 sent every hit at a displacement to the model and the model believed the nearest float in the
# window (22/22 wrong).  These checks are arithmetic, so they belong here: a hit that fails one is
# never shown to the judge.
FILTERS: dict[str, int] = {}
MEM_RE = re.compile(r"\[([a-z0-9]+)(?:\s*(?:\+|-)\s*(0x[0-9a-f]+|\d+))?\]")
XMM_RE = re.compile(r"^xmm\d+$")
IMM_RE = re.compile(r"^(0x[0-9a-f]+|\d+)$")
STACK_MOVES = {  # reg <- rsp/rbp, i.e. the register is a frame pointer after this
    "lea", "mov", "movups", "movaps", "movdqa", "movdqu"}
OFFSET_SLACK = 0x40      # an immediate this close to the displacement is the offset, not a value


def reset_filters() -> None:
    FILTERS.clear()


def drop(rule: str) -> str:
    FILTERS[rule] = FILTERS.get(rule, 0) + 1
    return rule


def operands(row: dict) -> list[str]:
    return [p.strip() for p in row["op_str"].split(",")]


def mem_operand(op: str):
    m = MEM_RE.search(op)
    if not m:
        return None
    return m.group(1), (int(m.group(2), 0) if m.group(2) else 0)


def rip_float(exe: bytes, secs, image_base: int, rows: list[dict], idx: int):
    """The float a `movss xmm, [rip+..]` reads (RIP target = the end of that instruction)."""
    m = re.search(r"\[rip \+ (0x[0-9a-f]+)\]", rows[idx]["op_str"])
    if not m or idx + 1 >= len(rows):
        return None
    target = rows[idx + 1]["addr"] + int(m.group(1), 16)
    toff = native.va_to_off(secs, image_base, target)
    if toff is None or toff + 4 > len(exe):
        return None
    import struct
    return struct.unpack("<f", exe[toff:toff + 4])[0]


def traced_literal(exe: bytes, secs, image_base: int, rows: list[dict], idx: int):
    """What the store at rows[idx] writes: ('imm'|'float'|'zero', value) or (kind, None).

    `kind` is `computed` when the source register was produced by arithmetic (a per-frame update),
    `memory` when it was loaded from non-constant memory (a field copy) and `opaque` when the
    window does not show where it came from.  Only the first three kinds carry a literal.
    """
    ops = operands(rows[idx])
    if len(ops) < 2:
        return "opaque", None
    src = ops[1]
    if IMM_RE.match(src):
        return "imm", int(src, 0)
    reg = src
    for j in range(idx - 1, max(-1, idx - 40), -1):
        r = rows[j]
        parts = operands(r)
        if not parts or parts[0] != reg:
            continue
        mn, rhs = r["mnemonic"], (parts[1] if len(parts) > 1 else "")
        if mn in ("pxor", "xorps", "xorpd") and rhs == reg:
            return "zero", 0.0
        if IMM_RE.match(rhs):
            return "imm", int(rhs, 0)
        if mn == "movss" and "[rip" in rhs:
            v = rip_float(exe, secs, image_base, rows, j)
            return ("float", v) if v is not None else ("memory", None)
        if XMM_RE.match(rhs) and mn in ("movss", "movaps", "movups", "movsd"):
            reg = rhs
            continue
        if mn in ("addss", "subss", "mulss", "divss", "addps", "mulps", "cvtsi2ss",
                  "cvtsi2sd", "cvtss2sd", "unpcklps", "shufps", "movlhps", "movhlps"):
            return "computed", None
        if "[" in rhs or "[" in r["op_str"].split(",", 1)[-1]:
            return "memory", None
        return "opaque", None
    return "opaque", None


def store_verdict(exe: bytes, secs, image_base: int, rows: list[dict], idx: int,
                  disp: int) -> tuple[str | None, object]:
    """(rule, None) when the hit must not reach the judge, else (None, the literal)."""
    ops = operands(rows[idx])
    dst = mem_operand(ops[0]) if ops else None
    if dst is None:
        return drop("dest-not-memory"), None
    base = dst[0]
    if base == "rsp":
        return drop("stack-base-rsp"), None
    if base == "rbp":
        return drop("stack-base-rbp"), None
    for j in range(idx - 1, max(-1, idx - 60), -1):
        r = rows[j]
        parts = operands(r)
        if len(parts) < 2 or parts[0] != base:
            continue
        if r["mnemonic"] in STACK_MOVES and re.search(r"\b(?:rsp|rbp)\b", parts[1]):
            return drop("stack-frame-reg"), None
        if parts[0] == base and r["mnemonic"] not in STACK_MOVES:
            break                                   # the base was set some other way: not a frame
    # a read of the same displacement before the store is the field's own value coming back
    reads = ("addss", "subss", "mulss", "divss", "add", "sub", "inc", "dec", "and", "or",
             "xor", "cmp", "test", "comiss", "ucomiss")
    for j in range(idx - 1, max(-1, idx - 40), -1):
        r = rows[j]
        for k, op in enumerate(operands(r)):
            mem = mem_operand(op)
            if not mem or mem[1] != disp:
                continue
            if k > 0 or r["mnemonic"] in reads:
                return drop("read-modify-write"), None
    kind, value = traced_literal(exe, secs, image_base, rows, idx)
    if kind == "computed":
        return drop("computed-value"), None
    if kind not in ("imm", "float", "zero"):
        return drop("no-literal-in-window"), None
    if value is not None and abs(float(value) - disp) <= OFFSET_SLACK:
        return drop("immediate-is-offset"), None
    return None, value


def exe_candidates(row: dict, exe: bytes, secs, image_base: int) -> tuple[list[dict], int]:
    disp = int(row["offset"], 16)
    hits = native.find_stores(exe, disp, limit=MAX_PER_ROW)
    if disp < 0x80:
        hits += disp8_stores(exe, disp, max(1, MAX_PER_ROW - len(hits)))
    hits.sort(key=lambda h: h["off"])
    cands = []
    for h in hits:
        rows = exe_window(exe, secs, image_base, h["off"], EXE_WINDOW_AFTER)
        idx = next((i for i, r in enumerate(rows) if r["off"] == h["off"]), None)
        if idx is None:
            drop("window-misses-store")
            continue
        rule, _value = store_verdict(exe, secs, image_base, rows, idx, disp)
        if rule:
            continue
        snippet = annotate(exe, secs, image_base, rows, h["off"])
        va = native.off_to_va(secs, image_base, h["off"])
        cands.append({"source": f"exe 0x{va:x}", "snippet": snippet,
                      "hint": constructor_like(snippet) or (row["owner"] or " ") in snippet})
    return cands, len(hits)


# ------------------------------------------------------------------------------------- TEXT route
def text_files() -> list[str]:
    """The TEXT corpus: game-derived config and script text, never our own analysis.

    Roots are the install's `BmGame/Config` (recursively - the `PC/` subdirectory holds its own
    `PCGame.ini` etc.), `BmGame/Localization` and `Binaries/Win64`, plus the non-chase `.txt` /
    `.config` dumps under the grab tree (mesh/AnimSet text, which is game content).  Excluded by
    rule: every `.json`/`.jsonl`/`.md`/`.csv`/`.log` (all project-written records) and every path
    under `_BmAKgrab/chase` (candidates, verdicts, cache, calib runs, selftest).
    """
    out = []
    for root, pats in ((GAME_CFG, ("*.ini", "*.int", "*.cfg", "*.txt")),
                       (GAME_LOC, ("*.int",)),
                       (GAME_BIN, ("*.ini", "*.int"))):
        for pattern in pats:
            out += glob.glob(os.path.join(root, "**", pattern), recursive=True)
    for base, dirs, files in os.walk(TEXT_ROOT):
        dirs[:] = sorted(d for d in dirs if d not in TEXT_SKIP_DIRS)
        for name in sorted(files):
            ext = os.path.splitext(name)[1].lower()
            if ext in TEXT_SKIP_EXTS or ext not in TEXT_EXTS:
                continue
            out.append(os.path.join(base, name))
    keep = []
    for path in sorted(set(out)):
        low = path.lower().replace("\\", "/")
        if "/_bmakgrab/chase/" in low:
            continue
        if os.path.splitext(low)[1] in TEXT_SKIP_EXTS:
            continue
        keep.append(path)
    return keep


def json_shaped(line: str) -> bool:
    """A JSON/CSV record is bookkeeping, not a default assignment (`"Member": 1200` is an offset
    map, `"Member": 1` a package count).  Game config/script text is `key=value` or a script
    statement, so a JSON-shaped hit line is dropped instead of being shown to the judge."""
    s = line.strip()
    return bool(s) and (s[0] in "{[<" or bool(re.match(r"^\"[^\"]+\"\s*:", s)))


def hit_line(data: bytes, at: int, length: int) -> str:
    lo = data.rfind(b"\n", 0, at) + 1
    hi = data.find(b"\n", at + length)
    return data[lo:len(data) if hi < 0 else hi].decode("utf-8", "replace")


def word_pattern(names: list[str]) -> re.Pattern:
    alts = b"|".join(re.escape(n.encode()) for n in sorted(set(names)))
    return re.compile(rb"(?<![A-Za-z0-9_])(?:" + alts + rb")(?![A-Za-z0-9_])", re.IGNORECASE)


def text_context(data: bytes, at: int, length: int) -> tuple[str, int, bool]:
    """20 lines around the hit, or a 1 KB byte window when the 'line' is minified."""
    line_start = data.rfind(b"\n", 0, at) + 1
    line_end = data.find(b"\n", at + length)
    line_end = len(data) if line_end < 0 else line_end
    line = data[line_start:line_end]
    if len(line) > 800:
        lo, hi = max(0, at - BINARY_WINDOW // 2), min(len(data), at + length + BINARY_WINDOW // 2)
        # mark the hit itself: a minified window gives the judge no other landmark
        block = (data[lo:at].decode("utf-8", "replace") + " >>> "
                 + data[at:at + length].decode("utf-8", "replace") + " <<< "
                 + data[at + length:hi].decode("utf-8", "replace"))
        return block, line_start, True
    pos = line_start
    for _ in range(TEXT_CONTEXT_LINES // 2):
        prev = data.rfind(b"\n", 0, max(0, pos - 1))
        if prev < 0:
            break
        pos = prev + 1
    end = line_end
    for _ in range(TEXT_CONTEXT_LINES // 2):
        nxt = data.find(b"\n", end + 1)
        if nxt < 0:
            break
        end = nxt
    block = data[pos:end].decode("utf-8", "replace")
    # prefix the line the hit is on, so the hit is visible in 20 lines of defaults
    rel = at - pos
    ls = block.rfind("\n", 0, rel) + 1
    block = block[:ls] + ">>> " + block[ls:]
    return block, line_start, False


def text_matches(names: list[str], files: list[str]) -> dict[str, list[tuple[str, int, int]]]:
    """One pass over the corpus: name (lower) -> [(path, offset, length)].  Scanning every file
    once for all names at once is what keeps a 90 MB JSON corpus affordable."""
    regex = word_pattern(names)
    wanted = {n.lower() for n in names}
    out: dict[str, list[tuple[str, int, int]]] = {n: [] for n in wanted}
    for path in files:
        try:
            data = open(path, "rb").read()
        except OSError:
            continue
        for m in regex.finditer(data):
            name = m.group(0).decode("utf-8", "replace").lower()
            if name in wanted:
                out[name].append((path, m.start(), len(m.group(0))))
    return out


def text_candidates(row: dict, hits: dict[str, list[tuple[str, int, int]]]) -> list[dict]:
    cands = []
    for path, at, length in hits.get(row["member"].lower(), []):
        try:
            data = open(path, "rb").read()
        except OSError:
            continue
        line = hit_line(data, at, length)
        if json_shaped(line):
            drop("text-json-record")
            continue
        # the member has to be the left-hand side of an assignment on its own line: an input
        # binding (`Bindings=(Name="StrafeRight",...)`) or a section header carrying the word is
        # not a default, and v1 showed the judge will read a name where it was asked for a value.
        if not re.match(r"^\s*[+.\-!]?\s*" + re.escape(row["member"]) + r"\s*=", line, re.I):
            drop("text-not-an-assignment")
            continue
        snippet, _near, _min = text_context(data, at, length)
        line = data.count(b"\n", 0, at) + 1
        cands.append({"source": f"{path.replace(os.sep, '/')}:{line}",
                      "snippet": snippet, "hint": (row["owner"] or " ") in snippet})
        if len(cands) >= MAX_PER_ROW * 4:
            break
    return cands


# --------------------------------------------------------------- TABLE route (v3, smart search)
# The decoded game-data tables and dumps the text route never read: the BmAK value tables under
# `Research/BatmobileGrab/*.md` and the grab's decoded default/CDO JSON dumps.  Trimmed to the one
# row/record that names the member - the diagnosis (`tmp/freebuff/reports/smart-search-recall-
# diagnosis.md` section 3) shows 19 of the 20 positive values live in `MODES.md`, which no route
# read, and the calibration/analysis files the old route offered instead are the answer key.
TABLE_MD = os.path.join(ROOT, "Research", "BatmobileGrab")
TABLE_JSON_GLOBS = ("chase2_defaults*.json", "g1_chase_native*.json", "chase2_native2*.json",
                    "sim_cdo*.json", "svehicle_cdo.json", "camera_cdo.json", "wheel_cdo.json",
                    "vehiclebase_cdo.json", "value_cdo_08*.json")
# the search tool's own output: a hit there is the question echoed back, not evidence
TABLE_SKIP = ("calib", "chase2_verify", "namescan", "verdict", "pkg_", "chase2_04", "selftest")
TABLE_MAX = 6


def table_files() -> list[str]:
    """The decoded table/dump corpus: `Research/BatmobileGrab/*.md` (not its chase/ notes) plus the
    grab's decoded JSON dumps (top level and `chase/`, where the CDO extracts live), minus every
    file the search tool itself wrote."""
    out = [p for p in glob.glob(os.path.join(TABLE_MD, "*.md"))
           if not any(s in os.path.basename(p).lower() for s in TABLE_SKIP)]
    for pattern in TABLE_JSON_GLOBS:
        for base in (TEXT_ROOT, os.path.join(TEXT_ROOT, "chase")):
            out += [p for p in glob.glob(os.path.join(base, pattern))
                    if not any(s in os.path.basename(p).lower() for s in TABLE_SKIP)]
    return sorted(dict.fromkeys(out))


def json_record(text: str, at: int) -> str:
    """The smallest `{...}` block containing the hit (the enclosing default record), else its line."""
    start = text.rfind("{", 0, at)
    if start < 0:
        lo = text.rfind("\n", 0, at) + 1
        hi = text.find("\n", at)
        return text[lo:len(text) if hi < 0 else hi]
    depth = 0
    for i in range(start, min(len(text), start + 4000)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:start + 2000]


def table_candidates(row: dict, files: list[str]) -> list[dict]:
    """One or two row-trimmed candidates from each decoded table/dump that names this member."""
    member = row["member"]
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(member) + r"(?![A-Za-z0-9_])")
    cands = []
    for path in files:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        shown = path.replace(os.sep, "/")
        for m in list(pat.finditer(text))[:2]:
            line_no = text.count("\n", 0, m.start()) + 1
            if path.lower().endswith(".md"):
                lo = text.rfind("\n", 0, m.start()) + 1
                hi = text.find("\n", m.end())
                line = text[lo:len(text) if hi < 0 else hi].strip()
                if not line.startswith("|") or set(line) <= set("|-: "):
                    continue
                snippet = (f"decoded BmAK value table, row tagged >>> ({shown}):\n"
                           + line.replace(member, ">>>" + member, 1))
            else:
                snippet = (f"decoded default/field record, member tagged >>> ({shown}):\n"
                           + json_record(text, m.start()).replace(member, ">>>" + member, 1))
            cands.append({"source": f"{shown}:{line_no}", "snippet": snippet, "hint": True,
                          "route": "table"})
        if len(cands) >= TABLE_MAX:
            break
    return cands[:TABLE_MAX]


# ------------------------------------------------------------------- one member (smart search)
# `table` is a selectable route (default on): it is the one that carries the decoded value, and the
# old text route never read it.  `exe` and `text` stay available, so `--routes exe,text` reproduces
# the pre-2026-11-06 search exactly.
ROUTES = ("exe", "text", "table")


def member_candidates(member: str, owner: str | None = None, offset: str | None = None,
                      ftype: str | None = None,
                      routes: tuple[str, ...] = ROUTES) -> list[dict]:
    """Candidates for ONE arbitrary member - the same two routes and the same record shape as the
    row scan, callable from another tool (`smart_search.py` imports this) or from the CLI.

    `member` names the field, `owner` the declaring class (used for the owner-name hint), `offset`
    the field offset as `0x..`/int (needed by the exe route), `ftype` the declared type.

    Two deliberate differences from the row scan, neither of which touches its output:
      * the candidate list is **ranked** - hits whose window names the owning class or looks like
        object initialisation come first, because a single query is judged top-down and a member's
        own store site is otherwise buried behind every same-displacement hit in the binary;
      * ids are `<member>#NNNN` and no row-plan filter runs (any member can be searched, including
        one with no FOOTAGE row).
    """
    if offset and not str(offset).lower().startswith("0x"):
        offset = hex(int(offset, 0))
    row = {"id": member, "member": member, "owner": owner,
           "offset": offset.lower() if offset else None, "type": ftype}
    cands: list[dict] = []
    if "exe" in routes and row["offset"]:
        exe = open(native.EXE, "rb").read()
        image_base, secs = native.sections(exe)
        c, _n = exe_candidates(row, exe, secs, image_base)
        cands += c
    if "text" in routes:
        # Never let the search read its own or the judge's artefacts: a verdict/selftest/cache file
        # is output, not evidence, and a hit in one would be a self-fulfilling match (the row scan
        # excludes only `verdicts*` because its artefact predates these files; this call is new, so
        # it excludes them properly).
        skip = ("verdict", "selftest", os.sep + "cache" + os.sep, os.sep + "calib_runs" + os.sep)
        files = [f for f in text_files() if not any(s in f for s in skip)]
        cands += text_candidates(row, text_matches([member], files))
    if "table" in routes:
        cands += table_candidates(row, table_files())
    # rank: decoded table/dump row first (it is the value), then owner/constructor-looking windows,
    # then everything else; stable inside a rank.  The table route has to lead or `--max 6` would let
    # a binary full of same-displacement hits crowd it out.
    rank = lambda c: 0 if c.get("route") == "table" else (1 if c["hint"] else 2)  # noqa: E731
    ranked = sorted(cands, key=rank)
    out = []
    for i, c in enumerate(ranked[:MAX_PER_ROW], 1):
        snippet = c["snippet"]
        if len(snippet) > SNIPPET_CAP:
            snippet = snippet[:SNIPPET_CAP] + "\n… [truncated at 12 KB]"
        out.append({"id": f"{member}#{i:04d}", "row": member, "member": member,
                    "owner": owner, "offset": row["offset"], "type": ftype,
                    "source": c["source"], "snippet": snippet,
                    "route": c.get("route") or
                             ("exe" if c["source"].startswith("exe ") else "text"),
                    "hint": c["hint"]})
    return out


# --------------------------------------------------------------------------------------- assemble
def scan() -> tuple[list[dict], dict]:
    reset_filters()
    chase, excluded, unknown_status, nomember, chfiles = plan_rows()
    exe = open(native.EXE, "rb").read()
    image_base, secs = native.sections(exe)
    files = text_files()
    hits = text_matches(sorted({r["member"] for r in chase}), files)

    out, counts, overflow = [], {}, {}
    for r in chase:
        counts[r["id"]] = 0
        overflow[r["id"]] = 0
        cands = []
        if r["offset"]:
            c, n = exe_candidates(r, exe, secs, image_base)
            cands += c
        cands += text_candidates(r, hits)
        if len(cands) > MAX_PER_ROW:
            keep = [c for c in cands if c["hint"]][:MAX_PER_ROW]
            if len(keep) < MAX_PER_ROW:
                keep += [c for c in cands if c not in keep][:MAX_PER_ROW - len(keep)]
            overflow[r["id"]] = len(cands) - MAX_PER_ROW
            cands = keep
        for i, c in enumerate(cands, 1):
            snippet = c["snippet"]
            if len(snippet) > SNIPPET_CAP:
                snippet = snippet[:SNIPPET_CAP] + "\n… [truncated at 12 KB]"
            out.append({"id": f"{r['id']}#{i:04d}", "row": r["id"], "member": r["member"],
                        "owner": r["owner"], "offset": r["offset"], "type": r["type"],
                        "source": c["source"], "snippet": snippet,
                        "route": "exe" if c["source"].startswith("exe ") else "text"})
        counts[r["id"]] = len(cands)
    meta = {"rows": len(chase), "excluded": len(excluded), "no_member": len(nomember),
            "candidates": len(out), "overflow": overflow, "counts": counts,
            "chase_files": [os.path.relpath(f, ROOT).replace("\\", "/") for f in chfiles],
            "excluded_rows": excluded, "no_member_rows": nomember,
            "text_files": len(files), "exe_bytes": len(exe), "image_base": image_base,
            "filters": dict(sorted(FILTERS.items()))}
    return out, meta


def filters_table(meta: dict) -> str:
    """Per-rule counts: what the search refused to show the judge."""
    f = meta["filters"]
    lines = ["| filter | dropped |", "|---|---:|"]
    for k in sorted(f):
        lines.append(f"| {k} | {f[k]} |")
    lines.append(f"| **total** | **{sum(f.values())}** |")
    return "\n".join(lines)


def counts_table(meta: dict) -> str:
    rows = sorted(meta["counts"], key=lambda x: int(x[2:]))
    lines = ["| row | candidates | overflow |", "|---|---:|---:|"]
    for r in rows:
        lines.append(f"| {r} | {meta['counts'][r]} | {meta['overflow'].get(r, 0)} |")
    lines.append(f"| **total** | **{meta['candidates']}** | "
                 f"**{sum(meta['overflow'].values())}** |")
    zero = [r for r in rows if meta["counts"][r] == 0]
    lines += ["", "**rows with 0 candidates:** " + (", ".join(zero) if zero else "none")]
    return "\n".join(lines)


def render(out: list[dict]) -> str:
    return "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="scan and write candidates.jsonl")
    ap.add_argument("--check", action="store_true", help="re-scan, compare, verify unique ids")
    ap.add_argument("--list-rows", action="store_true", help="print the row plan and stop")
    ap.add_argument("--member", help="search ONE member instead of the row plan (smart search)")
    ap.add_argument("--owner", help="the member's declaring class")
    ap.add_argument("--offset", help="the member's field offset, e.g. 0x11f8")
    ap.add_argument("--type", dest="ftype", help="the member's declared type, e.g. float")
    ap.add_argument("--routes", default="exe,text,table",
                    help="comma list: exe,text,table (default all three; `exe,text` = the old search)")
    ap.add_argument("--out", help="write the candidates here as JSONL (default: stdout)")
    a = ap.parse_args()

    if a.member:
        routes = tuple(r.strip() for r in a.routes.split(",") if r.strip())
        bad = [r for r in routes if r not in ROUTES]
        if bad:
            print(f"unknown route(s) {bad}; known: {', '.join(ROUTES)}", file=sys.stderr)
            return 2
        cands = member_candidates(a.member, a.owner, a.offset, a.ftype, routes)
        text = render(cands)
        if a.out:
            os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
            open(a.out, "w", encoding="utf-8", newline="\n").write(text)
            print(f"wrote {a.out} ({len(text)} B)")
        else:
            sys.stdout.write(text)
        print(f"{a.member}: {len(cands)} candidates "
              f"({sum(1 for c in cands if c['route'] == 'exe')} exe, "
              f"{sum(1 for c in cands if c['route'] == 'text')} text; routes "
              f"{','.join(routes)})", file=sys.stderr)
        return 0

    if a.list_rows:
        chase, excluded, unknown_status, nomember, chfiles = plan_rows()
        print(f"chase files: {len(chfiles)}")
        print(f"to chase: {len(chase)} | closed in a chase: {len(excluded)} | "
              f"not UNKNOWN in FOOTAGE: {len(unknown_status)} | no member: {len(nomember)}")
        for r in chase:
            print(f"  {r['id']:6} {r['member'] or '-':34} {r['owner'] or '-':26} "
                  f"{r['offset'] or '-':8} {r['type'] or '-'}")
        for r in excluded:
            print(f"  EXCLUDED {r['id']:6} {r['why'][:110]}")
        for r in nomember:
            print(f"  NO-MEMBER {r['id']:6} {r['question'][:80]}")
        return 0

    out, meta = scan()
    text = render(out)
    print(f"rows chased {meta['rows']} | excluded {meta['excluded']} | no member {meta['no_member']}"
          f" | candidates {meta['candidates']} | text files {meta['text_files']} "
          f"| exe {meta['exe_bytes']} B")
    print(counts_table(meta))
    print(filters_table(meta))
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8", newline="\n").write(text)
        print(f"wrote {OUT} ({len(text)} B)")
    if a.check:
        problems = []
        if not os.path.exists(OUT):
            problems.append(f"{OUT} does not exist")
        else:
            have = open(OUT, encoding="utf-8").read()
            if have != text:
                n = min(len(have), len(text))
                at = next((i for i in range(n) if have[i] != text[i]), n)
                problems.append(f"{os.path.basename(OUT)} differs from the re-derived scan at "
                                f"char {at}")
        ids = [c["id"] for c in out]
        if len(ids) != len(set(ids)):
            problems.append("duplicate ids")
        for c in out:
            if set(c) < {"id", "row", "member", "owner", "offset", "type", "source", "snippet"}:
                problems.append(f"{c['id']}: missing a judge field")
                break
        if problems:
            for p in problems:
                print("FAIL", p)
            return 1
        print(f"check ok: {len(out)} candidates, {len(set(ids))} unique ids, "
              f"{len(text)} B, byte-identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
