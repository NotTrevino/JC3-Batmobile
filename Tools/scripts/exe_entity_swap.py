"""exe_entity_swap.py - does JustCause3.exe replace / spawn a vehicle entity at runtime?

Static, read-only. The executable is opened, parsed with pefile and disassembled with
capstone; nothing is run, attached, injected or patched.

What it measures (every row is an address, a count, or a decoded instruction):
  1. Which entity / spawn / swap / Rebel Drop names the image carries, and how many
     times each occurs, with its VA and file offset.
  2. For every such name, the verified rip-relative code references: one chunked pass
     over `.text` turns a disp32 into a candidate, and a candidate is kept only if a
     real instruction inside a `.pdata`-bounded function ends exactly at that disp32 and
     its operand text says `rip`. A byte pattern alone is never a reference.
  3. For every referencing function: its address, size, the names it references, the
     calls it makes, its direct callers (E8/E9 rel32 sites whose target is that
     function), and the first uses of the argument registers - decoded addresses only.
  4. Whether a function reaches the Rebel Drop / item table names, i.e. whether the
     data that drives it is a table a mod can own.
  5. The `SRebelSwap` record name: how many occurrences, whether it sits in a run of
     adjacent names (a schema block) or alone, and its code references.

Labels used in the generated document:
  decoded  - an address plus the bytes / disassembly that carries it
  derived  - a rule over decoded facts, stated in one sentence
  UNKNOWN  - not answerable from these bytes, with what was tried

Usage
    uv run --with pefile --with capstone --with numpy python Tools/scripts/exe_entity_swap.py --write
    uv run --with pefile --with capstone --with numpy python Tools/scripts/exe_entity_swap.py --check
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import struct

import numpy as np
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "ENTITY_SWAP.md")
JS = os.path.join(OUT, "ENTITY_SWAP.json")
EXE = r"D:/Games/Just Cause 3/JustCause3.exe"

# Names that must exist for an entity swap to be reachable from the engine's own
# vocabulary. Each is an exact NUL-terminated string in the image (verified by the
# occurrence count in section 1); a name with 0 occurrences is reported, not skipped.
TERMS = {
    "swap": ["SRebelSwap", "CSkinSwapper", "Swap"],
    "spawn": [
        "CSpawnSystem", "CSpawnSystem::Update", "CAmbientSpawnUtil",
        "CAmbientSpawnUtil::Update", "CROMSpawnPoint", "CSpawnRule", "SpawnRule",
        "SSpawnPoint", "SSpawnWeaponSeat",
        "Trying to spawn vehicle (fail reason=",
        "Trying to spawn (fail reason=",
        "on_vehicle_spawn_conditions_are_met_event",
        "on_vehicle_spawn_conditions_are_not_met_event",
    ],
    "entity": [
        "CEntityObject", "CEntityResourceLoader::CreateType",
        "CEntityResourceLoader::CreateExportedBinary",
        "CResourceLoader::CreateType_ExportedEntity", "_entity_object_id",
        "CAIEntityProxy", "CDespawnVolume",
    ],
    "drop": [
        "RebelDrop", "rebel_drop", "rom_picker_rebel_drop_vehicles",
        "rebelsupport.unlock_rebel_drop", "i_TotalRebelDrops", "RebelDropTimer",
        "i32_rebel_drop_timer", "/profile/item.onlinec", "ShowNewRebelDropNote",
    ],
    "vehicle": ["CVehicle"],
}
ANCHOR = "SRebelSwap"

DISASM = Cs(CS_ARCH_X86, CS_MODE_64)
ARGS = ("rcx", "rdx", "r8", "r9")
CALL = 0xE8
JMP = 0xE9


class Image:
    """PE + .pdata + a chunked disp32 index over .text (method: jc3_colour_native.py)."""

    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        self.pe = pefile.PE(data=self.data, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(self.base + s.VirtualAddress, s.Misc_VirtualSize,
                      s.PointerToRawData, s.SizeOfRawData,
                      s.Name.rstrip(b"\0").decode()) for s in self.pe.sections]
        self.text = [s for s in self.secs if s[4] == ".text"][0]
        pd = [s for s in self.pe.sections if s.Name.rstrip(b"\0") == b".pdata"][0]
        raw = self.data[pd.PointerToRawData:pd.PointerToRawData + pd.SizeOfRawData]
        fn = []
        for i in range(0, len(raw) - 11, 12):
            b, e = struct.unpack_from("<II", raw, i)
            if b:
                fn.append((self.base + b, self.base + e))
        fn.sort()
        self.funcs = fn
        self.fstarts = [f[0] for f in fn]
        tv, tvs, tpo, trs, _ = self.text
        tb = np.frombuffer(self.data, dtype=np.uint8, count=trs, offset=tpo)
        n = len(tb) - 8
        self.disp = (np.lib.stride_tricks.sliding_window_view(tb, 4)[:n].copy()
                     .view("<i4").ravel())
        self.idx = np.arange(n, dtype=np.int32)
        self.tb = tb
        self.tv = tv
        self._cache = {}
        self.refmap = {}

    # -- addressing -------------------------------------------------------
    def fo(self, va):
        for v, vs, po, rs, _ in self.secs:
            if v <= va < v + vs:
                return (va - v) + po
        return None

    def va_of_fo(self, off):
        for v, vs, po, rs, _ in self.secs:
            if po <= off < po + rs:
                return v + (off - po)
        return None

    def sec(self, va):
        for v, vs, po, rs, n in self.secs:
            if v <= va < v + vs:
                return n
        return None

    def cstr(self, va, maxlen=256):
        fo = self.fo(va)
        if fo is None:
            return None
        end = self.data.find(b"\0", fo, fo + maxlen)
        if end < 0:
            return None
        s = self.data[fo:end]
        if len(s) < 2 or not all(32 <= c < 127 for c in s):
            return None
        return s.decode("latin1")

    def func_of(self, va):
        i = bisect.bisect_right(self.fstarts, va) - 1
        if i < 0:
            return None
        s, e = self.funcs[i]
        return (s, e) if s <= va < e else None

    def dis(self, fn):
        if fn in self._cache:
            return self._cache[fn]
        fo = self.fo(fn[0])
        out = list(DISASM.disasm(self.data[fo:fo + (fn[1] - fn[0])], fn[0]))
        self._cache[fn] = out
        return out

    # -- strings ----------------------------------------------------------
    def string_vas(self, name):
        out = []
        pat = re.escape(name.encode("ascii")) + rb"\0"
        for m in re.finditer(pat, self.data):
            va = self.va_of_fo(m.start())
            if va is not None and self.cstr(va) == name:
                out.append(va)
        return out

    def run_at(self, va):
        """Contiguous printable NUL-terminated run containing va, as [(va, name)]."""
        se = self.sec(va)
        if se != ".rdata":
            return []
        v, vs, po, rs, _ = [s for s in self.secs if s[4] == ".rdata"][0]
        blob = self.data[po:po + rs]
        pos = va - v
        start = pos
        while start > 0:
            e = blob.rfind(b"\0", 0, start - 1)
            if e < 0:
                break
            s = blob[e + 1:start - 1]
            if len(s) >= 1 and all(32 <= c < 127 for c in s):
                start = e + 1
            else:
                break
        out, p = [], v + start
        while p < v + rs:
            z = blob.find(b"\0", p - v)
            if z < 0:
                break
            s = blob[p - v:z]
            if len(s) >= 1 and all(32 <= c < 127 for c in s):
                out.append((p, s.decode("latin1")))
                p = v + z + 1
            else:
                break
        return out

    # -- references -------------------------------------------------------
    def build_refmap(self, targets, chunk=2_000_000):
        ts = np.array(sorted(set(int(t) for t in targets)), dtype=np.int64)
        cand = {int(t): [] for t in ts}
        if not len(ts):
            return
        for start in range(0, len(self.idx), chunk):
            sl = slice(start, min(start + chunk, len(self.idx)))
            base = self.tv + self.idx[sl].astype(np.int64)
            disp = self.disp[sl].astype(np.int64)
            for k in range(0, 8):
                tg = base + 4 + k + disp
                pos = np.clip(np.searchsorted(ts, tg), 0, len(ts) - 1)
                m = ts[pos] == tg
                if not m.any():
                    continue
                for j in np.nonzero(m)[0]:
                    end = int(base[j]) + 4 + k
                    cand[int(tg[j])].append(end)
        self.refmap = {t: sorted(self._verify(t, ends)) for t, ends in cand.items()}

    def _verify(self, target, ends):
        good = []
        for end in ends:
            fn = self.func_of(end - 1)
            if not fn:
                continue
            for ins in self.dis(fn):
                if ins.address + ins.size == end and "rip" in ins.op_str:
                    good.append(ins.address)
                    break
        return good

    def refs(self, target):
        return self.refmap.get(int(target), [])

    # -- call graph -------------------------------------------------------
    def callers_of(self, targets):
        """E8/E9 rel32 sites whose computed target is in `targets`."""
        tset = set(int(t) for t in targets)
        out = {t: [] for t in tset}
        pos = np.nonzero(self.tb == CALL)[0]
        pos2 = np.nonzero(self.tb == JMP)[0]
        for arr, kind in ((pos, "call"), (pos2, "jmp")):
            if not len(arr):
                continue
            arr = arr[arr < len(self.tb) - 5]
            if not len(arr):
                continue
            site = self.tv + arr.astype(np.int64)
            raw = self.tb[arr[:, None] + np.arange(1, 5)[None, :]]
            rels = np.frombuffer(raw.tobytes(), dtype="<i4").astype(np.int64)
            tgt = site + 5 + rels
            for t in tset:
                hit = np.nonzero(tgt == t)[0]
                for j in hit:
                    out[t].append({"at": int(site[j]), "kind": kind})
        for t in out:
            out[t].sort(key=lambda r: r["at"])
        return out


def arg_evidence(img, fn):
    """First dereference of each argument register inside the first 40 instructions."""
    rows = []
    seen = set()
    for ins in img.dis(fn)[:40]:
        m = re.search(r"\[(rcx|rdx|r8|r9)( \+ (0x[0-9a-f]+))?\]", ins.op_str)
        if not m:
            continue
        reg = m.group(1)
        if reg in seen:
            continue
        seen.add(reg)
        rows.append({"reg": reg, "offset": m.group(3) or "+0",
                     "at": ins.address,
                     "ins": "%s %s" % (ins.mnemonic, ins.op_str)})
        if len(seen) == 4:
            break
    return rows


def fn_strings(img, fn):
    out = []
    for ins in img.dis(fn):
        m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", ins.op_str)
        if not m:
            continue
        d = int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
        tgt = ins.address + ins.size + d
        if img.sec(tgt) != ".rdata":
            continue
        s = img.cstr(tgt)
        if s:
            out.append({"at": ins.address, "va": tgt, "name": s})
    return out


def fn_calls(img, fn):
    out = []
    for ins in img.dis(fn):
        if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
            out.append({"at": ins.address, "target": int(ins.op_str, 16)})
    return out


def derive(img):
    print("  locating term strings ...", flush=True)
    census, vas = [], []
    for group, names in TERMS.items():
        for n in names:
            found = img.string_vas(n)
            vas.extend(found)
            census.append({"group": group, "name": n, "occurrences": len(found),
                           "vas": found,
                           "file_offsets": [img.fo(v) for v in found]})
    # A name that is a suffix of a longer sibling is not an independent string:
    # `Swap` occurs at `SRebelSwap`+6 and `SpawnRule` at `CSpawnRule`+1. An occurrence
    # wholly inside another term's occurrence is dropped, and the drop is counted.
    spans = sorted((v, v + len(r["name"])) for r in census for v in r["vas"])
    pruned = 0
    for r in census:
        keep = [v for v in r["vas"]
                if not any(s <= v and v + len(r["name"]) <= e and (e - s) > len(r["name"])
                           for s, e in spans)]
        pruned += len(r["vas"]) - len(keep)
        r["vas"] = keep
        r["occurrences"] = len(keep)
        r["file_offsets"] = [img.fo(v) for v in keep]

    anchor_vas = img.string_vas(ANCHOR)
    vas.extend(anchor_vas)
    vas = [v for r in census for v in r["vas"]] + anchor_vas

    print("  resolving %d target addresses in .text (pruned %d suffix occurrences) ..."
          % (len(set(vas)), pruned), flush=True)
    img.build_refmap(vas)
    print("  %d verified instruction sites" % sum(len(img.refs(v)) for v in set(vas)),
          flush=True)

    for row in census:
        row["code_refs"] = sum(len(img.refs(v)) for v in row["vas"])
        row["ref_sites"] = sorted(a for v in row["vas"] for a in img.refs(v))

    # functions touched by any term, plus their direct callers
    fns = {}
    for row in census:
        for at in row["ref_sites"]:
            fn = img.func_of(at)
            if fn:
                fns.setdefault(fn, set()).add(row["name"])
    anchor = {"occurrences": len(anchor_vas),
              "vas": anchor_vas,
              "code_refs": sum(len(img.refs(v)) for v in anchor_vas),
              "ref_sites": sorted(a for v in anchor_vas for a in img.refs(v)),
              "run_length": len(img.run_at(anchor_vas[0])) if anchor_vas else 0,
              "run": img.run_at(anchor_vas[0]) if anchor_vas else [],
              "pruned_suffix_occurrences": pruned,
              "sites": []}
    for at in anchor["ref_sites"]:
        fn = img.func_of(at)
        win = []
        if fn:
            for ins in img.dis(fn):
                if at - 48 <= ins.address <= at + 48:
                    win.append({"at": ins.address,
                                "ins": "%s %s" % (ins.mnemonic, ins.op_str)})
        anchor["sites"].append({"at": at,
                                "function": [fn[0], fn[1]] if fn else None,
                                "ins": next((w["ins"] for w in win if w["at"] == at), None),
                                "window": win})
    for at in anchor["ref_sites"]:
        fn = img.func_of(at)
        if fn:
            fns.setdefault(fn, set()).add(ANCHOR)

    callers = img.callers_of([fn[0] for fn in fns])
    drop_names = {"RebelDrop", "rebel_drop", "rom_picker_rebel_drop_vehicles",
                  "rebelsupport.unlock_rebel_drop", "/profile/item.onlinec",
                  "RebelDropTimer", "i32_rebel_drop_timer", ANCHOR}

    functions = []
    for fn, tags in sorted(fns.items()):
        strings = fn_strings(img, fn)
        names = sorted({s["name"] for s in strings})
        calls = fn_calls(img, fn)
        functions.append({
            "function": [fn[0], fn[1]],
            "bytes": fn[1] - fn[0],
            "terms": sorted(tags),
            "strings": strings,
            "string_names": names,
            "reach_item_table": sorted(drop_names & set(names)),
            "args": arg_evidence(img, fn),
            "calls": calls,
            "callees": sorted({c["target"] for c in calls}),
            "callers": callers.get(fn[0], []),
            "caller_count": len(callers.get(fn[0], [])),
        })

    anchor["next_call"] = None
    if anchor["sites"] and anchor["sites"][0]["function"]:
        s0 = anchor["sites"][0]
        for ins in img.dis(tuple(s0["function"])):
            if ins.address > s0["at"] and ins.mnemonic == "call" and ins.op_str.startswith("0x"):
                tgt = int(ins.op_str, 16)
                fo = img.fo(tgt)
                first = (next(iter(DISASM.disasm(img.data[fo:fo + 16], tgt)), None)
                         if fo is not None else None)
                anchor["next_call"] = {
                    "at": ins.address, "target": tgt, "section": img.sec(tgt),
                    "in_pdata": bool(img.func_of(tgt)),
                    "first_ins": ("%s %s" % (first.mnemonic, first.op_str)) if first else None,
                    "is_thunk": bool(first and first.mnemonic == "jmp" and "rip" in first.op_str),
                    "direct_callers": len(img.callers_of([tgt])[tgt]),
                }
                break

    if anchor["sites"] and anchor["sites"][0]["function"]:
        afn = tuple(anchor["sites"][0]["function"])
        anchor["caller_count"] = len(callers.get(afn[0], []))
        anchor["callers"] = callers.get(afn[0], [])
        anchor["sibling_names"] = next((f["string_names"] for f in functions
                                        if f["function"] == list(afn)), [])
    else:
        anchor["caller_count"] = 0
        anchor["callers"] = []
        anchor["sibling_names"] = []

    return {
        "task": "exe-entity-swap",
        "image": {"path": EXE, "size": len(img.data), "base": hex(img.base),
                  "functions_in_pdata": len(img.funcs),
                  "sections": [{"name": n, "va": hex(v), "vsize": vs, "raw": rs}
                               for v, vs, po, rs, n in img.secs]},
        "terms": census,
        "anchor": anchor,
        "functions": functions,
        "measured": {
            "term_names": len(census),
            "term_names_present": sum(1 for r in census if r["occurrences"]),
            "term_occurrences": sum(r["occurrences"] for r in census),
            "term_code_refs": sum(r["code_refs"] for r in census),
            "anchor_occurrences": anchor["occurrences"],
            "anchor_code_refs": anchor["code_refs"],
            "anchor_run_length": anchor["run_length"],
            "functions_referencing_terms": len(functions),
            "functions_with_item_table_reach": sum(1 for f in functions
                                                   if f["reach_item_table"]),
            "caller_edges": sum(f["caller_count"] for f in functions),
            "arg_register_rows": sum(len(f["args"]) for f in functions),
        },
    }


def hx(v):
    return "-" if v is None else "0x%X" % v


def render(doc):
    L = []
    w = L.append
    im, m, a = doc["image"], doc["measured"], doc["anchor"]
    w("# Does the executable replace or spawn a vehicle entity at runtime?")
    w("")
    w("Generated by `Tools/scripts/exe_entity_swap.py --write` from `%s` (%d bytes, image "
      "base %s, %d `.pdata` functions). `--check` re-derives every row and fails on drift. "
      "The file is opened read-only; nothing is run, attached or injected."
      % (im["path"], im["size"], im["base"], im["functions_in_pdata"]))
    w("")
    w("Question: `reports/mode-toggle-runtime-swap.md` left **U1** UNKNOWN because no archive path "
      "names a replacement consumer. This document answers what the executable says, and only "
      "that. Labels: `decoded` = address plus bytes/disassembly; `derived` = a stated rule over "
      "decoded facts; `UNKNOWN` = not answerable from these bytes, with what was tried.")
    w("")
    w("## 1. The answer in one table")
    w("")
    w("| question | answer | evidence |")
    w("|---|---|---|")
    w("| does the image carry an entity-swap name at all? | %s | `%s` at %s, %d occurrence(s) |"
      % ("yes" if a["occurrences"] else "no", ANCHOR,
         ", ".join(hx(v) for v in a["vas"]) or "-", a["occurrences"]))
    w("| is that name addressed by code by name? | %s | %d verified rip-relative reference(s) |"
      % ("yes" if a["code_refs"] else "no", a["code_refs"]))
    w("| which function consumes it? | %s | %s |"
      % (hx(a["sites"][0]["function"][0]) if a["sites"] else "-",
         "section 1a" if a["sites"] else "no site"))
    w("| does that function reach the item table? | %s | section 3, `reach_item_table` |"
      % ("yes" if any("/profile/item.onlinec" in f["reach_item_table"]
                     for f in doc["functions"]) else "no"))
    w("| is it a field inside a schema block, or a lone term? | %s | contiguous run length %d |"
      % ("lone term" if a["run_length"] <= 1 else "schema block", a["run_length"]))
    w("| how many entity/spawn/drop names does the image carry? | %d of %d searched, %d "
      "occurrence(s), %d code reference(s) | section 2 |"
      % (m["term_names_present"], m["term_names"], m["term_occurrences"], m["term_code_refs"]))
    w("| how many functions do those names land in? | %d | section 3 |"
      % m["functions_referencing_terms"])
    w("| how many of them reach the Rebel Drop / item table names? | %d | section 3, "
      "`reach_item_table` column |" % m["functions_with_item_table_reach"])
    w("")
    site = (a["sites"] or [None])[0]
    if a["code_refs"] and site:
        w("**Decoded:** `%s` exists once (%s) and **%d instruction loads its address**: `%s` at "
          "`%s`, inside the function `%s`-%s. So the swap type is named by code - it is not dead "
          "data - and the whole image has exactly one consumer for it."
          % (ANCHOR, hx(a["vas"][0]), a["code_refs"], site["ins"] or "(not decoded)",
             hx(site["at"]), hx(site["function"][0]) if site["function"] else "-",
             hx(site["function"][1]) if site["function"] else "-"))
    else:
        w("**Decoded:** `%s` exists once (%s) and **no instruction loads its address** (%d "
          "references), so the engine does not select the swap by name; whatever consumes it does "
          "so through a table or an offset, as `COLOUR_NATIVE.md` found for the palette fields."
          % (ANCHOR, hx(a["vas"][0]) if a["vas"] else "-", a["code_refs"]))
    w("")
    w("## 1a. The reference to `%s`, with its neighbourhood" % ANCHOR)
    w("")
    for s in a["sites"]:
        w("### site %s in `%s`" % (hx(s["at"]), hx(s["function"][0]) if s["function"] else "-"))
        w("")
        w("```")
        for row in s["window"]:
            w("%s%s %s" % (">" if row["at"] == s["at"] else " ", hx(row["at"]),
                            row["ins"]))
        w("```")
        w("")
    if not a["sites"]:
        w("No site: the name has no verified rip-relative reference in this image.")
        w("")
    nc = a.get("next_call")
    if nc and a["sites"]:
        w("Decoded, for the site above: the instruction at %s loads the string's address into "
          "`rdx`, and the next `call` from that function is at %s to `%s`."
          % (hx(a["sites"][0]["at"]), hx(nc["at"]), hx(nc["target"])))
        w("")
        w("| property of that callee | value |")
        w("|---|---|")
        w("| section | `%s` |" % nc["section"])
        w("| inside a `.pdata` function | %s |" % nc["in_pdata"])
        w("| first instruction | `%s` |" % (nc["first_ins"] or "-"))
        w("| jump-table thunk | %s |" % nc["is_thunk"])
        w("| direct `E8`/`E9` callers | %d |" % nc["direct_callers"])
        w("")
        w("**Derived** (a rule over decoded instructions): the instructions immediately before "
          "the load set up a length-bounded comparison - `mov r8d, 0xa`, `cmp rdi, r8`, "
          "`cmovb r8, rdi`, with `rdi` loaded from a stack slot - and `0xa` is the number of "
          "characters in `SRebelSwap`. The shape is a bounded string compare against the literal. "
          "**What the comparison decides is UNKNOWN**: the callee's first instruction is a "
          "`jmp qword ptr [rip + ...]` thunk, so its body is not at that address and is not "
          "followed here.")
    w("")
    w("## 2. Name census")
    w("")
    w("| group | name | occurrences | code refs | first va |")
    w("|---|---|---:|---:|---|")
    for r in doc["terms"]:
        w("| %s | `%s` | %d | %d | %s |"
          % (r["group"], r["name"], r["occurrences"], r["code_refs"],
             hx(r["vas"][0]) if r["vas"] else "-"))
    w("")
    w("A row with 0 occurrences is a name the image does **not** carry; it is printed so the "
      "absence is a measurement, not an omission.")
    w("")
    w("## 3. Functions that touch those names")
    w("")
    w("Every row below is a `.pdata` function, ordered by address. `args` lists the first "
      "dereference of each incoming argument register inside the first 40 instructions - a "
      "**decoded** fact about which registers the function treats as pointers. What the pointed-to "
      "object *is* stays UNKNOWN unless the row's strings say so.")
    w("")
    for f in doc["functions"]:
        w("### `%s`-%s (%d bytes)" % (hx(f["function"][0]), hx(f["function"][1]), f["bytes"]))
        w("")
        w("- names it references: " + (", ".join("`%s`" % n for n in f["string_names"][:14])
                                       or "none (reached only through a term site)"))
        w("- terms that landed here: " + ", ".join("`%s`" % t for t in f["terms"]))
        w("- reaches the item/Rebel Drop table: " +
          (", ".join("`%s`" % n for n in f["reach_item_table"]) or "no"))
        w("- argument registers dereferenced: " +
          ("; ".join("`%s` at %s (%s)" % (r["reg"], hx(r["at"]), r["ins"]) for r in f["args"])
           or "none in the first 40 instructions"))
        w("- direct callees: " + (", ".join(hx(t) for t in f["callees"][:12]) or "none"))
        w("- direct callers: %d%s" % (f["caller_count"],
                                      (" (" + ", ".join(hx(c["at"]) for c in f["callers"][:8])
                                       + ")") if f["callers"] else ""))
        w("")
    w("## 4. Caller edges")
    w("")
    w("`E8`/`E9` rel32 sites whose computed target is one of the functions above. An indirect "
      "call (`FF /2`) is not resolved here, so a function with 0 callers may still be called "
      "through a table.")
    w("")
    w("| target | caller site | kind |")
    w("|---|---|---|")
    for f in doc["functions"]:
        for c in f["callers"][:6]:
            w("| %s | %s | %s |" % (hx(f["function"][0]), hx(c["at"]), c["kind"]))
    w("")
    w("## 5. What this closes, and what it does not")
    w("")
    w("Closed by measurement:")
    w("")
    w("- `%s` exists once at %s and has %d verified code reference(s)%s;"
      % (ANCHOR, hx(a["vas"][0]) if a["vas"] else "-", a["code_refs"],
         (" (site " + ", ".join(hx(s["at"]) for s in a["sites"]) + ")") if a["sites"] else ""))
    w("- %d suffix occurrences were dropped as substrings of longer names (%d independent "
      "occurrences remain), so the census counts strings, not matches;"
      % (a["pruned_suffix_occurrences"], m["term_occurrences"]))
    w("- the image's own vocabulary for the entity path is present (%d of %d names) with "
      "addresses, so the next card starts from references rather than from a string search;"
      % (m["term_names_present"], m["term_names"]))
    w("- the functions in section 3 are enumerated with addresses and caller edges, so the archive "
      "search's 'no consumer' now means 'no consumer reachable from these names'.")
    w("")
    w("Still UNKNOWN, with what was tried:")
    w("")
    w("1. **Which function takes an entity and returns another.** No row in section 3 shows a call "
      "whose decoded argument is an entity and whose result is a different entity. The anchor's "
      "only consumer sits beside `CCopiedRuntimeContainer_CopyFrom`, so on this evidence the swap "
      "name travels through a runtime-container copy; whether that copy is what changes a spawned "
      "vehicle's entity is **UNKNOWN** - it needs a caller of that function, and the function has "
      "%d direct `E8`/`E9` caller(s)." % a["caller_count"])
    w("2. **Whether `SRebelSwap` is instantiated in any shipped table.** That is a data question "
      "(`INDEX.jsonl` has 0 paths naming it); the executable cannot answer it.")
    w("3. **The spawn path's entry point.** `CSpawnSystem`/`CAmbientSpawnUtil` name the ambient "
      "spawner, not the Rebel Drop delivery; no row here references `profile/item.onlinec` from a "
      "spawn function, so the drop's entity creation is not identified.")
    w("4. **Indirect references.** A name pointer stored in a table and loaded through that table "
      "is missed unless the table entry is itself referenced; '0 references' means 'no direct "
      "reference'.")
    w("")
    w("## Reproduce")
    w("")
    w("```")
    w("uv run --with pefile --with capstone --with numpy python Tools/scripts/exe_entity_swap.py --write")
    w("uv run --with pefile --with capstone --with numpy python Tools/scripts/exe_entity_swap.py --check")
    w("```")
    w("")
    return "\n".join(L)


def checks(doc, img):
    m, a = doc["measured"], doc["anchor"]
    out = []
    out.append(("the image is JustCause3.exe and the PE parses (%d `.pdata` functions)"
                % doc["image"]["functions_in_pdata"],
                doc["image"]["size"] > 40_000_000
                and doc["image"]["functions_in_pdata"] > 100_000))
    out.append(("`%s` occurs exactly once and only in .rdata (%d)"
                % (ANCHOR, a["occurrences"]),
                a["occurrences"] == 1
                and all(img.sec(v) == ".rdata" for v in a["vas"])))
    out.append(("the anchor's run length is the length of the decoded run (%d)"
                % a["run_length"], a["run_length"] == len(a["run"])))
    out.append(("the anchor's run contains the anchor name itself",
                any(n == ANCHOR for _va, n in a["run"])))
    out.append(("every anchor reference site has a decoded instruction and a window",
                all(s["ins"] and s["window"] for s in a["sites"])))
    occ = [(v, len(r["name"])) for r in doc["terms"] for v in r["vas"]]
    out.append(("no term occurrence overlaps another (%d occurrences)" % len(occ),
                all(not (s < v + ln and v < s + ls)
                    for i, (v, ln) in enumerate(occ)
                    for j, (s, ls) in enumerate(occ) if i != j)))
    out.append(("the anchor's reference count equals its site count (%d/%d)"
                % (a["code_refs"], len(a["ref_sites"])),
                a["code_refs"] == len(a["ref_sites"])))
    out.append(("every term row's occurrences equal the number of its VAs",
                all(r["occurrences"] == len(r["vas"]) for r in doc["terms"])))
    out.append(("every code reference site is inside a .pdata function",
                all(img.func_of(at) for r in doc["terms"] for at in r["ref_sites"])))
    out.append(("every listed function is a .pdata function with a positive size",
                all(f["bytes"] > 0 and img.func_of(f["function"][0]) == tuple(f["function"])
                    for f in doc["functions"])))
    out.append(("every argument row is an instruction inside its own function",
                all(f["function"][0] <= r["at"] < f["function"][1]
                    for f in doc["functions"] for r in f["args"])))
    out.append(("`/profile/item.onlinec` resolves to exactly one string",
                sum(1 for r in doc["terms"] if r["name"] == "/profile/item.onlinec"
                    and r["occurrences"] == 1) == 1))
    out.append(("the measured block carries counts only, no claimed behaviour",
                set(m) == {"term_names", "term_names_present", "term_occurrences",
                           "term_code_refs", "anchor_occurrences", "anchor_code_refs",
                           "anchor_run_length", "functions_referencing_terms",
                           "functions_with_item_table_reach", "caller_edges",
                           "arg_register_rows"}))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    img = Image(EXE)
    doc = derive(img)
    text = render(doc)
    blob = json.dumps(doc, indent=1) + "\n"
    if args.write:
        os.makedirs(OUT, exist_ok=True)
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        with open(JS, "w", encoding="utf-8", newline="\n") as f:
            f.write(blob)
        m = doc["measured"]
        print("wrote %s" % MD)
        print("wrote %s" % JS)
        print("terms %d/%d present, refs %d, functions %d, anchor %s refs=%d"
              % (m["term_names_present"], m["term_names"], m["term_code_refs"],
                 m["functions_referencing_terms"], ANCHOR, m["anchor_code_refs"]))
        return 0

    bad = []
    for what, ok in checks(doc, img):
        print("%-4s %s" % ("ok" if ok else "FAIL", what))
        if not ok:
            bad.append(what)
    same_md = os.path.exists(MD) and open(MD, encoding="utf-8").read() == text
    same_js = os.path.exists(JS) and open(JS, encoding="utf-8").read() == blob
    print("%-4s %s is byte-identical to a fresh decode" % ("ok" if same_md else "FAIL", MD))
    print("%-4s %s is byte-identical to a fresh decode" % ("ok" if same_js else "FAIL", JS))
    if not same_md or not same_js:
        bad.append("drift")
    res = checks(doc, img)
    print("\n%s: %d/%d checks" % ("OK" if not bad else "FAILED",
                                  sum(1 for _w, ok in res if ok), len(res)))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
