"""bmak_reg.py - disassemble the native class registration in BatmanAK.exe (G1-1).

`NATIVE.md` counts the `<Class>exec<Function>` strings the image carries.  This tool goes the
rest of the way and reads the *registration tables* those strings belong to, because that is
where a class's reflected properties would have to live if the executable carried them at all:

  * UE3 registers a native class by handing the engine an array of 16-byte
    `{ const ANSICHAR* Name; void* Code; }` entries terminated by a null name - one entry per
    native `exec` function, nothing else.
  * The arrays are located by finding the 8-byte pointers to the `...exec...` string bodies
    inside the image's data sections, then walking each run of `{name-in-strings, code-in-.text}`
    pairs to its terminator.
  * The entries are then decoded, the array's code pointer is disassembled with capstone (x86-64)
    to show what the registration does with the records, and every field offset the natives touch
    is scanned for a name that could be bound to it.

Output is `Research/BatmobileGrab/REGISTRATION.json` (+ a Markdown section printed by `--md`).

Usage:
    python Tools/scripts/bmak_reg.py --write
    python Tools/scripts/bmak_reg.py --check
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"

TARGETS = ("RVehicleSimBatmobile", "RVehicleBatmobileBase", "RVehicleBatmobilePredictor",
           "RVehicleBatmobile", "SVehicleWheel")
EXEC_RX = re.compile(rb"[AU]?(RVehicle[A-Za-z0-9_]*?|SVehicle[A-Za-z0-9_]*?)exec([A-Za-z0-9_]+)")


class Image:
    """Minimal PE32+ reader: header, image base, sections, RVA <-> offset."""

    def __init__(self, path):
        self.data = open(path, "rb").read()
        d = self.data
        if d[:2] != b"MZ":
            raise ValueError("not a PE image")
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        if d[pe:pe + 4] != b"PE\0\0":
            raise ValueError("bad PE signature")
        nsec, = struct.unpack_from("<H", d, pe + 6)
        optsz, = struct.unpack_from("<H", d, pe + 20)
        opt = pe + 24
        magic, = struct.unpack_from("<H", d, opt)
        if magic != 0x20B:
            raise ValueError("not PE32+ (magic %#x)" % magic)
        self.base, = struct.unpack_from("<Q", d, opt + 24)
        self.entry, = struct.unpack_from("<I", d, opt + 16)
        sec = opt + optsz
        self.sections = []
        for k in range(nsec):
            o = sec + 40 * k
            name = d[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
            vsize, vaddr, rsize, roff = struct.unpack_from("<IIII", d, o + 8)
            chars, = struct.unpack_from("<I", d, o + 36)
            self.sections.append({"name": name, "vaddr": vaddr, "vsize": vsize,
                                  "raw": roff, "rawsize": rsize, "chars": chars})

    def section_of(self, va):
        rva = va - self.base
        for s in self.sections:
            if s["vaddr"] <= rva < s["vaddr"] + max(s["vsize"], s["rawsize"]):
                return s
        return None

    def off(self, va):
        s = self.section_of(va)
        if not s:
            return None
        o = s["raw"] + (va - self.base - s["vaddr"])
        return o if 0 <= o < len(self.data) else None

    def va(self, off):
        for s in self.sections:
            if s["raw"] <= off < s["raw"] + s["rawsize"]:
                return self.base + s["vaddr"] + (off - s["raw"])
        return None

    def qwords_in(self, names=(".rdata", ".data")):
        """{va: qword} for every 8 bytes of the given sections."""
        vals = {}
        for s in self.sections:
            if s["name"] not in names:
                continue
            buf = self.data[s["raw"]:s["raw"] + s["rawsize"]]
            n = len(buf) // 8
            for i, q in enumerate(struct.unpack("<%dQ" % n, buf[:n * 8])):
                vals[s["vaddr"] + i * 8] = q
        return vals

    def cstr(self, va, limit=256):
        o = self.off(va)
        if o is None:
            return None
        end = self.data.find(b"\0", o, o + limit)
        if end < 0:
            return None
        try:
            return self.data[o:end].decode("ascii")
        except UnicodeDecodeError:
            return None

    def is_text(self, va):
        s = self.section_of(va)
        return bool(s) and s["name"] == ".text"


def exec_strings(img):
    """{class: {function: [va, ...]}} for every `...exec...` string in the image."""
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    for m in EXEC_RX.finditer(img.data):
        cls, fn = m.group(1).decode(), m.group(2).decode()
        va = img.va(m.start())
        if va:
            out[cls][fn].append(va)
    return out


def find_arrays(img, strings):
    """Walk every table of {name-ptr, code-ptr} pairs that names an exec string."""
    ptr_to_fn = {}
    for cls, fns in strings.items():
        for fn, vas in fns.items():
            for va in vas:
                ptr_to_fn[va] = (cls, fn)
    q = img.qwords_in()
    starts = []
    for va, val in q.items():
        if val in ptr_to_fn:
            code = q.get(va + 8)
            if code is not None and img.is_text(code):
                starts.append(va)
    # group into contiguous runs of 16-byte entries
    starts.sort()
    used, arrays = set(), []
    for s in starts:
        if s in used:
            continue
        base = s
        while base - 16 in starts:
            base -= 16
        entries, cur = [], base
        while cur in starts and cur not in used:
            name = q[cur]
            code = q[cur + 8]
            entries.append({"va": cur, "name_va": name, "code_va": code,
                            "name": ptr_to_fn.get(name, (None, img.cstr(name)))[1],
                            "class": ptr_to_fn.get(name, (None, None))[0]})
            used.add(cur)
            cur += 16
        arrays.append({"va": base, "entries": entries,
                       "terminator": _terminator(img, q, cur)})
    return arrays, q


def _terminator(img, q, va):
    """The null entry that ends the array: both qwords zero, or a null name."""
    name, code = q.get(va), q.get(va + 8)
    return {"va": va, "name": name, "code": code,
            "null": name == 0 and (code in (0, None))}


def disasm(img, va, count=40):
    try:
        import capstone
    except ImportError:                                   # pragma: no cover
        return []
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = False
    o = img.off(va)
    if o is None:
        return []
    out = []
    for ins in md.disasm(img.data[o:o + count * 8], va):
        out.append({"va": ins.address, "bytes": ins.bytes.hex(),
                    "text": "%s %s" % (ins.mnemonic, ins.op_str)})
        if len(out) >= count:
            break
    return out


def scan_fields(img, entries, depth=2, limit=300, lo=0x100, hi=0xA00):
    """Offsets of the object that the natives of these classes touch.

    A UE3 `exec` thunk receives `this` in RCX and forwards to the real implementation, so the dump
    walks the thunk and up to `depth` call targets.  Every `[reg + disp]` whose displacement falls
    in the reflected-field window is recorded with its width and whether it was read or written;
    the register is not resolved (that would need data flow), so the map is evidence, not proof:
    an offset is only used when its function set and width agree with a candidate property.
    """
    try:
        import capstone
    except ImportError:                                   # pragma: no cover
        return {}
    ctx = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    ctx.detail = True
    usage = collections.defaultdict(list)

    def walk(va, name, cls, level):
        o = img.off(va)
        if o is None or level > depth:
            return
        calls = []
        for ins in ctx.disasm(img.data[o:o + limit * 8], va):
            written = bool(ins.operands) and ins.operands[0].type == capstone.x86.X86_OP_MEM \
                and ins.mnemonic in ("mov", "movss", "movsd", "add", "sub", "and", "or",
                                     "xor", "inc", "dec", "movzx", "movsx", "movaps")
            for k, op in enumerate(ins.operands):
                if op.type != capstone.x86.X86_OP_MEM or not op.mem.base:
                    continue
                disp = op.mem.disp
                if not lo <= disp < hi:
                    continue
                usage[disp].append({"class": cls, "function": name,
                                    "width": op.size,
                                    "access": "write" if (written and k == 0) else "read",
                                    "va": ins.address,
                                    "insn": "%s %s" % (ins.mnemonic, ins.op_str)})
            if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
                calls.append(int(ins.op_str, 16))
            if ins.mnemonic == "ret" and ins.address > va + 0x40:
                break
        for c in list(dict.fromkeys(calls))[:3]:
            walk(c, name, cls, level + 1)

    for e in entries:
        walk(e["code_va"], e["name"], e["class"], 0)
    out = {}
    for disp in sorted(usage):
        rows = usage[disp]
        funcs = collections.OrderedDict()
        for r in rows:
            funcs.setdefault((r["function"], r["access"]), r)
        out["%#06x" % disp] = {
            "widths": sorted({r["width"] for r in rows}),
            "functions": [{"name": k[0], "class": v["class"], "access": k[1],
                           "insn": v["insn"], "va": v["va"]} for k, v in funcs.items()],
        }
    return out


def build():
    img = Image(EXE)
    strings = exec_strings(img)
    arrays, q = find_arrays(img, strings)
    # keep arrays that name a target class
    targets = [a for a in arrays
               if any(e["class"] in TARGETS for e in a["entries"])]
    doc = {
        "schema": 1, "generated_by": "bmak_reg.py",
        "image": {"path": EXE, "size": len(img.data), "base": img.base,
                  "sections": [{k: s[k] for k in ("name", "vaddr", "vsize", "raw", "rawsize")}
                               for s in img.sections]},
        "exec_strings": {c: {f: v for f, v in fns.items()} for c, fns in strings.items()
                         if c in TARGETS},
        "arrays": [{"va": a["va"], "count": len(a["entries"]),
                    "classes": sorted({e["class"] for e in a["entries"] if e["class"]}),
                    "entries": a["entries"], "terminator": a["terminator"]}
                   for a in targets],
        "summary": {
            "arrays": len(targets),
            "entries": sum(len(a["entries"]) for a in targets),
            "classes": sorted({e["class"] for a in targets for e in a["entries"] if e["class"]}),
            "property_entries": 0,
        },
    }
    # every entry's name must be an exec string; a property table would show up as a name that
    # is not `...exec...` and an 8-byte value pair, so count anything that breaks the shape
    odd = [e for a in targets for e in a["entries"] if e["class"] is None]
    doc["summary"]["non_exec_names"] = len(odd)
    entries = [e for a in targets for e in a["entries"]]
    doc["field_usage"] = scan_fields(img, entries)
    doc["summary"]["offsets_touched"] = len(doc["field_usage"])
    doc["summary"]["watch"] = watch(doc["field_usage"])
    return doc, img


WATCH = (0x3B0, 0x3B1, 0x4A8)


def watch(usage):
    """The offsets this grab cares about, with whatever the natives do to them."""
    out = {}
    for off in WATCH:
        u = usage.get("%#06x" % off)
        out["%#06x" % off] = ["%s (%s)" % (f["name"], f["access"]) for f in u["functions"]] \
            if u else []
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--listing", metavar="CLASS", help="disassemble the registration code")
    a = ap.parse_args()
    doc, img = build()
    print("arrays: %d, entries: %d, classes: %s" % (
        doc["summary"]["arrays"], doc["summary"]["entries"],
        ", ".join(doc["summary"]["classes"])))
    for arr in doc["arrays"]:
        print("  array %#x  %3d entries  %s" % (arr["va"], arr["count"], arr["classes"]))
        if a.listing:
            for e in arr["entries"]:
                print("     %-26s -> %#x" % (e["name"], e["code_va"]))
    if a.listing:
        arr = [x for x in doc["arrays"] if a.listing in "".join(x["classes"])]
        for entry in arr[0]["entries"] if arr else []:
            print("\n-- %s thunk at %#x" % (entry["name"], entry["code_va"]))
            for ins in disasm(img, entry["code_va"], 12):
                print("   %#x  %-24s %s" % (ins["va"], ins["bytes"], ins["text"]))
    for off, users in doc.get("summary", {}).get("watch", {}).items():
        print("  watch %s: %s" % (off, ", ".join(users) if users else "no native touches it"))
    if a.write:
        path = os.path.join(OUT, "REGISTRATION.json")
        json.dump(doc, open(path, "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(path, ROOT))
    if a.check:
        path = os.path.join(OUT, "REGISTRATION.json")
        old = json.load(open(path, encoding="utf-8"))
        bad = []
        if old["summary"]["arrays"] != doc["summary"]["arrays"]:
            bad.append("array count %s != %s" % (old["summary"]["arrays"],
                                                 doc["summary"]["arrays"]))
        if old["summary"]["entries"] != doc["summary"]["entries"]:
            bad.append("entry count %s != %s" % (old["summary"]["entries"],
                                                 doc["summary"]["entries"]))
        if old["summary"]["non_exec_names"] or doc["summary"]["non_exec_names"]:
            bad.append("a registration entry is not an exec name")
        if old["exec_strings"] != doc["exec_strings"]:
            bad.append("exec strings changed")
        if old["field_usage"].keys() != doc["field_usage"].keys():
            bad.append("touchable offsets changed: %d vs %d" % (len(old["field_usage"]),
                                                                len(doc["field_usage"])))
        if bad:
            print("FAIL")
            for b in bad:
                print("  ", b)
            return 1
        print("check: %d arrays, %d entries, %d offsets touched - ok" % (
            doc["summary"]["arrays"], doc["summary"]["entries"],
            doc["summary"]["offsets_touched"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
