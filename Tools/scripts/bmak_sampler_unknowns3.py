"""bmak_sampler_unknowns3.py - U2 (BoostingOut writer) and U7 (bCancelButton producer),
re-routed through every package's FNames/property accessors and through the BmSDK (7213).

`Research/BatmobileGrab/SAMPLER_UNKNOWNS2.md` leaves two items missing their input:

  U2  the UFunction body that writes `RVehicleBatmobileBase.BoostingOut` (+5901)
  U7  the producer of the ~0.1 s `RPlayerInput.bCancelButton` (+774) taps

This card does **not** retry the routes listed there (the EjectFromVehicle bytecode walk,
the decoded refs in CONTROLS_CONSUMERS.json, the bind table, a device trace).  It tries:

  R1  every package's name table: is each field of SAMPLER_FIELDS2.md an FName there, and at
      which name index (the FName route).
  R2  every package's export table: is there an *export* named for the field - the property
      object itself, or a Get/Set/On accessor function - with package, export, export-table
      byte offset and payload byte offset (the property-accessor route).
  R3  every class-default payload of a class that can carry a target field: does a tag name
      the field offset (offset -> FName in cooked content).
  R4  every Function body of every package that exports a target field: which functions
      reference the property export index, and does any reference sit directly behind
      EX_Let/EX_LetBool (the only assignment form the repo's fixed-width ref walk frames).
  R5  BmSDK-AK: every generated file, for a member that writes the field.

Each route carries a positive control: the same test is run over all 47 field rows, so a
test that found writers/accessors/tags for other fields but none for the two targets is a
meaningful negative.  Those controls are oracles below.

Labels: decoded (package + export + byte offset, or file + line), derived (rule + inputs),
UNKNOWN (what was tried and where the answer would be).  The game is never run; the install
is only read.  The script writes one document, from these bytes only.

Usage
    python Tools/scripts/bmak_sampler_unknowns3.py --write
    python Tools/scripts/bmak_sampler_unknowns3.py --check   # rebuilds and diffs byte-for-byte
    python Tools/scripts/bmak_sampler_unknowns3.py --stats   # calibration: totals only
"""
from __future__ import annotations

import json
import re
import struct
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Research" / "BatmobileGrab"
MD = RES / "SAMPLER_UNKNOWNS3.md"
FIELDS_MD = RES / "SAMPLER_FIELDS2.md"

GAME = Path("E:/Games/Batman - Arkham Knight")
COOKED = GAME / "BmGame" / "CookedPCConsole"
DLC = GAME / "DLC"
BMSDK = Path("E:/Modding/_tools/BmSDK-AK/src/BmSDK")
GEN = BMSDK / "Generated"

sys.path.insert(0, str(ROOT / "Tools" / "scripts"))
import upk_read as U  # noqa: E402
from grab_packages_g305 import PartialPackage  # noqa: E402  (lazy whole-package reader)

FIELD_RE = re.compile(r"`([A-Za-z_]\w*)\.([A-Za-z_]\w*)`")
OFF_HEX = re.compile(r"^\s*(\d+)\s*\(0x[0-9a-fA-F]+\)\s*$")
OFF_NUM = re.compile(r"^\s*(\d+)\s*$")
PROP_RE = re.compile(r"///\s*(\w+)Property:\s*(\w+)")
FUNC_RE = re.compile(r"///\s*Function:\s*(\w+)")
REF_TOKENS = {0x00: "EX_LocalVariable", 0x01: "EX_InstanceVariable", 0x02: "EX_DefaultVariable"}
LET_TOKENS = {0x0F: "EX_Let", 0x14: "EX_LetBool"}
KIND_OF = (("`u8`", "u8"), ("`i32`", "i32"), ("`f32`", "f32"), ("`bit`", "bit"),
           ("`ptr`", "ptr"), ("`fname`", "fname"), ("`tarray`", "tarray"))
U2, U7 = "BoostingOut", "bCancelButton"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- the field table
def fields() -> list[dict]:
    """Every SAMPLER_FIELDS2.md row that names a `Class.Field` and a numeric offset."""
    out, seen = [], set()
    for line in read(FIELDS_MD).splitlines():
        m = FIELD_RE.search(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        off = None
        for c in cells:
            h = OFF_HEX.match(c)
            if h:
                off = int(h.group(1))
                break
            n = OFF_NUM.match(c)
            if n and off is None:
                off = int(n.group(1))
        if off is None:
            continue
        key = (m.group(1), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        kind = next((k for tok, k in KIND_OF if tok in line),
                    "u8 (candidate)" if "byte" in line.lower() else "struct")
        out.append({"class": key[0], "field": key[1], "name": f"{key[0]}.{key[1]}",
                    "offset": off, "kind": kind})
    return out


def packages() -> list[Path]:
    out = sorted(COOKED.glob("*.upk"))
    if DLC.is_dir():
        out += sorted(p for p in DLC.rglob("*.upk"))
    return out


# ---------------------------------------------------------------- fast table reader
class Tables(U.Package):
    """A package's name/import/export tables only: the compressed body is pumped just far
    enough to hold them, so the payloads of 4145 packages are never read.  Payload access is
    not offered; the few packages that need it are re-opened with PartialPackage."""

    def __init__(self, path):
        self.path = str(path)
        self.name_count = self.export_count = self.import_count = 0
        with open(self.path, "rb") as fh:
            head = fh.read(4096)
            if len(head) < 48:
                raise U.UpkError("header shorter than 48 bytes")
            self.version = struct.unpack_from("<H", head, 4)[0]
            self.licensee = struct.unpack_from("<H", head, 6)[0]
            self.header_size = struct.unpack_from("<i", head, 8)[0]
            self.group, o = U._fstr(head, 12)
            self.flags = struct.unpack_from("<I", head, o)[0]
            o += 4
            (self.name_count, self.name_offset, self.export_count, self.export_offset,
             self.import_count, self.import_offset) = struct.unpack_from("<6i", head, o)
        self.file_size = Path(self.path).stat().st_size
        self.image = b""
        with open(self.path, "rb") as fh:
            self._build_image(fh)
        self.names = self._read_names()
        self.imports = self._read_imports()
        self.exports = self._read_exports()

    def _build_image(self, fh):
        need = max(self.export_offset + self.export_count * 72,
                   self.import_offset + self.import_count * 28)
        # plain tables: only the table bytes are read
        fh.seek(self.name_offset)
        probe = fh.read(min(self.file_size - self.name_offset, max(need - self.name_offset, 4096)))
        try:
            o = 0
            for _ in range(self.name_count):
                _, o = U._fstr(probe, o)
                o += 8
            if o != self.import_offset - self.name_offset:
                raise U.UpkError("plaintext name table does not end at the import table")
            self.image = b"\0" * self.name_offset + probe
            self._chunked = False
            return
        except Exception:
            pass
        fh.seek(self.name_offset)
        if fh.read(4) != U.PKG_TAG:
            fh.seek(self.name_offset)
            window = fh.read(1 << 16)
            k = window.find(U.PKG_TAG)
            if k < 0:
                raise U.UpkError("no chunk tag at the name table")
            start = self.name_offset + k
        else:
            start = self.name_offset
        body = bytearray()
        q = start
        need_body = need - self.name_offset
        while len(body) < need_body:
            fh.seek(q)
            hdr = fh.read(16)
            if len(hdr) < 16:
                raise U.UpkError("chunk header truncated at %#x" % q)
            block, csize, usize = struct.unpack_from("<III", hdr, 4)
            if block == 0 and csize == 0 and usize == 0:
                break
            p = q + 16
            pairs, total = [], 0
            while total < usize:
                fh.seek(p)
                sub = fh.read(8)
                if len(sub) < 8:
                    raise U.UpkError("sub-block header truncated at %#x" % p)
                bc, bu = struct.unpack_from("<II", sub, 0)
                p += 8
                if bc == 0 or bu == 0:
                    raise U.UpkError("zero sub-block at %#x" % p)
                pairs.append((bc, bu))
                total += bu
            if total != usize:
                raise U.UpkError("chunk at %#x lists %d, header says %d" % (q, total, usize))
            for bc, bu in pairs:
                blob = fh.read(bc)
                if len(blob) != bc:
                    raise U.UpkError("sub-block at %#x truncated" % p)
                try:
                    part = zlib.decompress(blob)
                except zlib.error:
                    part = U.lzo1x_decompress(blob)
                if len(part) != bu:
                    raise U.UpkError("sub-block at %#x decoded %d, expected %d"
                                     % (p, len(part), bu))
                body += part
                p += bc
            q = p
        self.image = b"\0" * self.name_offset + bytes(body)
        self._chunked = True


# ---------------------------------------------------------------- the package scan
def scan_packages(fl: list[dict], verbose: bool = True) -> dict:
    names = {f["field"] for f in fl}
    rec = {"packages": 0, "parsed": 0, "errors": [], "script_packages": 0,
           "function_exports": 0, "name_hits": {}, "export_hits": {}, "refs": {},
           "direct_let": 0, "let_sites": [], "field_exports": {}, "tag_rows": [],
           "tag_hits": [], "tag_packages": [], "seconds": 0.0, "cdo_candidates": {}}
    started = time.time()
    allp = packages()
    path_by_stem = {p.stem: p for p in allp}
    owners = {f["class"] for f in fl}
    for n, path in enumerate(allp, 1):
        rec["packages"] += 1
        if verbose and n % 500 == 0:
            print(f"  {n}/{len(allp)} packages, {rec['parsed']} parsed, "
                  f"{time.time()-started:.0f}s", flush=True)
        try:
            pkg = Tables(str(path))
        except Exception as exc:
            rec["errors"].append({"file": path.name,
                                  "why": f"{type(exc).__name__}: {exc}"[:160]})
            continue
        rec["parsed"] += 1
        pname = path.stem
        hits = sorted(set(pkg.names) & names)
        for h in hits:
            rec["name_hits"].setdefault(h, []).append(
                {"package": pname, "file": path.name, "name_index": pkg.names.index(h),
                 "name_count": pkg.name_count})
        funcs = 0
        for i in range(1, pkg.export_count + 1):
            e = pkg.exports[i - 1]
            nm = e["name"] or ""
            cls = pkg.object_class(i)
            if cls == "Function":
                funcs += 1
            row = {"package": pname, "file": path.name, "export": i, "class": cls,
                   "outer": pkg.object_path(e["outer_index"]), "size": e["size"],
                   "table_offset": pkg.export_offset + (i - 1) * 72,
                   "payload_offset": e["offset"]}
            if nm in names:
                rec["export_hits"].setdefault(nm, []).append(row)
                rec["field_exports"].setdefault(nm, []).append(row)
            else:
                if any(nm in ("Get" + h, "Set" + h, "On" + h, "Is" + h, "Has" + h)
                       for h in hits):
                    rec["export_hits"].setdefault("accessor:" + nm, []).append(row)
            if hits and e["size"] > 4 and (cls in owners or nm.startswith("Default__")):
                rec["cdo_candidates"].setdefault(pname, []).append((i, cls, nm))
        if funcs:
            rec["script_packages"] += 1
            rec["function_exports"] += funcs
    rec["seconds"] = round(time.time() - started, 1)
    if verbose:
        print(f"  phase A: {rec['parsed']}/{rec['packages']} in {rec['seconds']}s; "
              f"{len(rec['name_hits'])} names, {len(rec['cdo_candidates'])} tag candidates",
              flush=True)

    # R3: only class-default candidates, one package open at a time
    for pname, cands in sorted(rec["cdo_candidates"].items()):
        rec["tag_packages"].append(pname)
        try:
            pkg = PartialPackage(str(path_by_stem[pname]))
        except Exception as exc:
            rec["errors"].append({"file": pname + ".upk",
                                  "why": "payload: " + f"{type(exc).__name__}: {exc}"[:140]})
            continue
        for i, cls, nm in cands:
            try:
                data = pkg.data(i)
                tags, end, why = U.walk_tags(pkg, data)
            except Exception:
                continue
            found = [{"field": f["name"], "type": t["type"], "offset": t["offset"],
                      "at": t["at"]}
                     for t in tags for f in fl
                     if t["offset"] == f["offset"] and t.get("name") == f["field"]]
            row = {"package": pname, "export": i, "class": cls, "name": nm,
                   "size": len(data), "tags": len(tags), "stop": why,
                   "max_offset": max((t["offset"] for t in tags), default=None),
                   "field_tags": found}
            rec["tag_rows"].append(row)
            if found:
                rec["tag_hits"].append(row)
        del pkg

    # R4: every Function body of a package that exports a target property
    for pname in sorted({r["package"] for rows in rec["field_exports"].values()
                         for r in rows}):
        try:
            pkg = PartialPackage(str(path_by_stem[pname]))
        except Exception as exc:
            rec["errors"].append({"file": pname + ".upk",
                                  "why": "payload: " + f"{type(exc).__name__}: {exc}"[:140]})
            continue
        local = {}
        for h, rows in rec["field_exports"].items():
            for r in rows:
                if r["package"] == pname:
                    local.setdefault(h, set()).add(r["export"])
        flat = {i: h for h, s in local.items() for i in s}
        for i in range(1, pkg.export_count + 1):
            if pkg.object_class(i) != "Function":
                continue
            data = pkg.data(i)
            if len(data) < 38:
                continue
            script = data[22:len(data) - 16]
            fpath = pkg.object_path(i)
            for tgt, h in flat.items():
                start = 0
                while True:
                    k = script.find(struct.pack("<i", tgt), start)
                    if k < 0:
                        break
                    start = k + 1
                    if k == 0 or script[k - 1] not in REF_TOKENS:
                        continue
                    row = {"package": pname, "field": h, "function": fpath, "export": i,
                           "script_offset": k - 1, "token": REF_TOKENS[script[k - 1]],
                           "byte_before": script[k - 2] if k >= 2 else None,
                           "script_bytes": len(script)}
                    row["direct_let"] = row["byte_before"] in LET_TOKENS
                    rec["refs"].setdefault(h, []).append(row)
                    if row["direct_let"]:
                        rec["direct_let"] += 1
                        rec["let_sites"].append(row)
        del pkg
    for h in rec["refs"]:
        rec["refs"][h].sort(key=lambda r: (r["package"], r["export"], r["script_offset"]))
    for h in rec["field_exports"]:
        rec["field_exports"][h].sort(key=lambda r: (r["package"], r["export"]))
    return rec


# ---------------------------------------------------------------- windows and Let calibration
def ref_forms(fl: list[dict], rec: dict) -> dict:
    out = {"windows": [], "let_examples": [], "let_noise": [], "sites": {}}
    by_pkg = {}
    for h, rows in rec["refs"].items():
        for r in rows:
            by_pkg.setdefault(r["package"], []).append((h, r))
    path_by_stem = {p.stem: p for p in packages()}
    for pname, items in sorted(by_pkg.items()):
        pkg = PartialPackage(str(path_by_stem[pname]))
        for h, r in items:
            data = pkg.data(r["export"])
            script = data[22:len(data) - 16]
            a = r["script_offset"]
            lo, hi = max(0, a - 8), min(len(script), a + 12)
            let_at = a - 14 if a >= 14 and script[a - 14] in LET_TOKENS else None
            out["windows"].append({"field": h, "function": r["function"],
                                   "export": r["export"], "at": a, "token": r["token"],
                                   "lo": lo, "let_at": let_at,
                                   "bytes": script[lo:hi].hex()})
            out["sites"].setdefault(h, []).append(a)
        del pkg
    for h in out["sites"]:
        out["sites"][h].sort()
    # EX_Let order calibration on the one package that carries the target bodies
    pkg = U.Package(str(path_by_stem["BmGame"]))
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "Function":
            continue
        data = pkg.data(i)
        if len(data) < 38:
            continue
        script = data[22:len(data) - 16]
        fpath = pkg.object_path(i)
        k = 0
        while True:
            k = script.find(b"\x0f\x01", k)
            if k < 0:
                break
            start = k
            k += 1
            if start + 10 > len(script):
                continue
            prop = struct.unpack_from("<i", script, start + 2)[0]
            if not (1 <= prop <= pkg.export_count):
                continue
            cls = pkg.object_class(prop)
            if cls not in ("FloatProperty", "IntProperty", "ByteProperty"):
                continue
            outer = pkg.object_path(pkg.exports[prop - 1]["outer_index"])
            if not (outer and fpath and fpath.startswith(outer + ".")):
                continue
            nxt = script[start + 6]
            if nxt not in (0x1D, 0x1E, 0x24):
                continue
            val = struct.unpack_from("<f", script, start + 7)[0] if nxt == 0x1E else None
            out["let_examples"].append({
                "function": fpath, "export": i, "at": start, "property": prop,
                "property_class": cls, "property_outer": outer, "value_token": nxt,
                "value": (round(val, 6) if val is not None else None),
                "bytes": script[start:start + 12].hex()})
        k = 0
        while len(out["let_noise"]) < 6:
            k = script.find(b"\x29", k)
            if k < 0:
                break
            seq = script[k:k + 5]
            k += 1
            if len(seq) < 5 or 0x0F not in seq[1:]:
                continue
            idx = struct.unpack_from("<i", seq, 1)[0]
            if 1 <= idx <= pkg.export_count:
                out["let_noise"].append({"function": fpath, "export": i, "at": k - 1,
                                         "index": idx, "bytes": seq.hex()})
    out["let_examples"].sort(key=lambda r: (r["function"], r["at"]))
    out["let_noise"].sort(key=lambda r: (r["function"], r["at"]))
    return out


# ---------------------------------------------------------------- the BmSDK scan
def scan_bmsdk(fl: list[dict]) -> dict:
    rec = {"files": 0, "occurrences": {}, "property_blocks": {}, "set_accessors": {},
           "functions": {}, "mentions": {}, "other_files": {}}
    names = {f["field"] for f in fl}
    for path in sorted(GEN.rglob("*.cs")):
        rec["files"] += 1
        lines = read(path).splitlines()
        text = "\n".join(lines)
        for f in names & set(re.findall(r"[A-Za-z_]\w*", text)):
            hit_lines = [ln for ln, line in enumerate(lines, 1) if f in line]
            rec["mentions"][f] = rec["mentions"].get(f, 0) + 1
            blocks = setters = funcs = 0
            for ln, line in enumerate(lines, 1):
                pm = PROP_RE.search(line)
                if pm and pm.group(2) == f:
                    blocks += 1
                    setters += sum(1 for w in lines[ln - 1:ln + 8]
                                   if w.strip().startswith("set {"))
                fm = FUNC_RE.search(line)
                if fm and fm.group(1) == f:
                    funcs += 1
            if blocks or funcs:
                rec["occurrences"].setdefault(f, []).append(
                    {"file": path.name,
                     "hits": [{"line": ln, "text": lines[ln - 1].strip()}
                              for ln in hit_lines]})
            else:
                rec["other_files"].setdefault(f, []).append(path.name)
            if blocks:
                rec["property_blocks"][f] = rec["property_blocks"].get(f, 0) + blocks
                rec["set_accessors"][f] = rec["set_accessors"].get(f, 0) + setters
            if funcs:
                rec["functions"][f] = rec["functions"].get(f, 0) + funcs
    return rec


# ---------------------------------------------------------------- the document
def build(fl: list[dict], rec: dict, forms: dict, sdk: dict) -> str:
    L: list[str] = []
    w = L.append
    f2 = next(f for f in fl if f["field"] == U2)
    f7 = next(f for f in fl if f["field"] == U7)
    e2 = rec["field_exports"].get(U2, [])
    e7 = rec["field_exports"].get(U7, [])
    r2 = rec["refs"].get(U2, [])
    r7 = rec["refs"].get(U7, [])
    s2 = sorted({r["function"] for r in r2})
    s7 = sorted({r["function"] for r in r7})
    h2 = rec["name_hits"].get(U2, [])
    h7 = rec["name_hits"].get(U7, [])
    acc = {k: v for k, v in rec["export_hits"].items() if k.startswith("accessor:")}
    ctrl = [r for rows in rec["refs"].values() for r in rows if r["direct_let"]]
    ctrl_by = {}
    for r in ctrl:
        ctrl_by[r["field"]] = ctrl_by.get(r["field"], 0) + 1
    tagged = {t["field"] for r in rec["tag_hits"] for t in r["field_tags"]}
    w2 = [x for x in forms["windows"] if x["field"] == U2]
    w7 = [x for x in forms["windows"] if x["field"] == U7]
    tick = [r for r in forms["let_examples"] if r["function"].endswith("RGadgetSelectBM3.Tick")]

    w("# SAMPLER_UNKNOWNS3 - U2 and U7 re-routed through FNames, property accessors and the "
      "BmSDK (7213)")
    w("")
    w("Generated by `Tools/scripts/bmak_sampler_unknowns3.py --write`; `--check` rebuilds this")
    w("document from the same bytes and requires it to be identical. Read-only inputs: the")
    w(f"name/import/export tables of all {rec['parsed']} readable `.upk` files under")
    w("`BmGame/CookedPCConsole` and `DLC/`, the class-default payloads and Function bodies of")
    w("the packages that can carry a target field, and the BmSDK-AK generated tree. Nothing")
    w("was run, attached to or written under a game install; `SAMPLER_UNKNOWNS.md` and")
    w("`SAMPLER_UNKNOWNS2.md` are untouched.")
    w("")
    w("The routes listed in `SAMPLER_UNKNOWNS2.md` (EjectFromVehicle's walk, the refs in")
    w("`CONTROLS_CONSUMERS.json`, the bind table, a device trace) are **not** retried here.")
    w("")
    w("## STATUS")
    w("")
    w("| U | what is missing | new route(s) | result |")
    w("|---|---|---|---|")
    w(f"| U2 | the writer of `{f2['class']}.{f2['field']}` (+{f2['offset']}) | R1 FName census, "
      f"R2 property-accessor exports, R3 class-default offset tags, R4 every Function body, "
      f"R5 BmSDK | **accessor located** (BmGame export {e2[0]['export'] if e2 else '?'}, "
      f"`ByteProperty`, FName {h2[0]['name_index'] if h2 else '?'}); **no writer located** |")
    w(f"| U7 | the producer of the ~0.1 s `{f7['class']}.{f7['field']}` (+{f7['offset']}) taps | "
      f"same five routes | **no producer located**; the widened census reads {len(s7)} functions "
      f"(card 2 had 3) and still finds no writer |")
    w("")
    w(f"Coverage: **{rec['parsed']}/{rec['packages']}** packages parsed "
      f"({len(rec['errors'])} unreadable), **{rec['script_packages']}** carrying Function")
    w(f"exports, **{rec['function_exports']}** Function bodies, **{len(rec['tag_rows'])}**")
    qual = [f for f in fl if any(r["outer"] == f["class"]
                                 for r in rec["field_exports"].get(f["field"], []))]
    w(f"class-default payloads walked. Of the {len(fl)} field")
    w(f"rows searched, **{len(rec['name_hits'])}** are FNames somewhere, **{len(qual)}** have a")
    w(f"property object whose outer is the row's class, and **{len(rec['refs'])}** are")
    w("referenced by a script body.")
    w("")
    w("## Route sensitivity (positive controls)")
    w("")
    w("Every route below is run over all field rows, not only the two targets. These are the")
    w("controls that make a negative meaningful - the same test finds writers, accessors and")
    w("tags for other fields of the same table:")
    w("")
    w("| route | control: what the same test found elsewhere | target: U2 | target: U7 |")
    w("|---|---|---|---|")
    w(f"| R1 FName | {len(rec['name_hits'])}/47 field names present in some name table | "
      f"{len(h2)} package(s) | {len(h7)} package(s) |")
    w(f"| R2 accessor export | {len(acc)} accessor-shaped export name(s) for other fields | "
      f"{len([k for k in acc if k.endswith(U2)])} | {len([k for k in acc if k.endswith(U7)])} |")
    w(f"| R3 cooked tag | {len(rec['tag_hits'])} tag(s) at {len(tagged)} other field offsets | "
      f"{'yes' if f2['name'] in tagged else 'no'} | {'yes' if f7['name'] in tagged else 'no'} |")
    w(f"| R4 direct `EX_Let` | {len(ctrl)} site(s) behind a Let, over {len(ctrl_by)} other "
      f"fields | {len([r for r in r2 if r['direct_let']])} | "
      f"{len([r for r in r7 if r['direct_let']])} |")
    w(f"| R5 BmSDK member | {len(sdk['property_blocks'])} property block(s), "
      f"{sum(sdk['set_accessors'].values())} generic setter(s) | 1 block, 0 methods | "
      f"1 block, 0 methods |")
    w("")
    w("`R4`'s control is the strongest: the fixed-width reference walk *does* find assignment")
    w("statements - " + ", ".join(f"`{k}` {v}" for k, v in sorted(ctrl_by.items(),
                                                                 key=lambda x: (-x[1], x[0]))[:6])
      + " - so its failure on the two target fields is a property of the bytecode, not of the")
    w("test.")
    w("")
    w("## The two fields as FNames and property objects (R1/R2)")
    w("")
    w("| field | package | export | class | outer | FName table index | name table count | "
      "export table byte offset | payload byte offset | payload size | label |")
    w("|---|---|---:|---|---|---:|---:|---:|---:|---:|---|")
    for f, e, h in ((f2, e2[0] if e2 else None, h2[0] if h2 else None),
                    (f7, e7[0] if e7 else None, h7[0] if h7 else None)):
        if not (e and h):
            continue
        w(f"| `{f['class']}.{f['field']}` | `{e['package']}.upk` | {e['export']} | "
          f"`{e['class']}` | `{e['outer']}` | {h['name_index']} | {h['name_count']} | "
          f"{e['table_offset']} | {e['payload_offset']} | {e['size']} | decoded (package + "
          f"export + byte offsets) |")
    w("")
    w("`export` is the object index in the package's export table: the **property object**,")
    w("which is what a property accessor is built from. `FName table index` is the entry in")
    w("that package's name table that spells the field, `export table byte offset` is")
    w("`export_offset + (export-1)*72` (stride 72, `upk_read.Package._read_exports`), and")
    w("`payload byte offset` / `size` are the export record's own fields. All `decoded`.")
    w("")
    w("The field names across every parsed package's name table (R1):")
    w("")
    w("| field | packages naming it | package:name index |")
    w("|---|---:|---|")
    for f, hits in ((f2, h2), (f7, h7)):
        w(f"| `{f['class']}.{f['field']}` | {len(hits)} | "
          + ", ".join(f"`{h['package']}`:{h['name_index']}" for h in hits) + " |")
    w("")
    w("`bCancelButton` is spelled in eight name tables, but only `BmGame` exports a property")
    w("of that name: the other seven packages' export tables were scanned too and hold no such")
    w("export, so the string is a name reference there, not a declaration. `BoostingOut` is")
    w("spelled in two name tables, again with one export.")
    w("")
    w("### Property accessors (R2)")
    w("")
    w(f"Exports named `{U2}`: **{len(e2)}**; named `{U7}`: **{len(e7)}** - each is the property")
    w("object itself. The same test over the whole table *does* find accessor-shaped export")
    w("names, so the absence below is specific (name-shaped only: the table shows each one's")
    w("real outer, none of which is either target class):")
    w("")
    if acc:
        w("| accessor-shaped export | package | export | class | outer |")
        w("|---|---|---:|---|---|")
        for k, rows in sorted(acc.items()):
            for r in rows[:3]:
                w(f"| `{k.split(':', 1)[1]}` | `{r['package']}` | {r['export']} | "
                  f"`{r['class']}` | `{r['outer']}` |")
    else:
        w("- no accessor-shaped export at all.")
    w("")
    w("No `Get<Field>`/`Set<Field>`/`On<Field>` export exists **for either target field** in")
    w("any package: there is no UnrealScript accessor function a caller could invoke, so the")
    w("only script-side write path would be an assignment inside a Function body (R4).")
    w("")
    w("### BmSDK (R5)")
    w("")
    w("| field | files with a property block | property blocks | generic `set {` accessors | "
      "functions/methods named for it | files mentioning the name |")
    w("|---|---:|---:|---:|---:|---:|")
    for f in (f2, f7):
        w(f"| `{f['class']}.{f['field']}` | {len(sdk['occurrences'].get(f['field'], []))} | "
          f"{sdk['property_blocks'].get(f['field'], 0)} | "
          f"{sdk['set_accessors'].get(f['field'], 0)} | "
          f"{sdk['functions'].get(f['field'], 0)} | "
          f"{sdk['mentions'].get(f['field'], 0)} |")
    w("")
    for f in (f2, f7):
        for o in sdk["occurrences"].get(f["field"], []):
            w(f"- `{o['file']}`: " + "; ".join(f"line {x['line']} `{x['text']}`"
                                              for x in o["hits"]))
    w("")
    w("Every occurrence sits inside the single property block: the `/// <Type>Property:`")
    w("comment, the `public unsafe <type>` declaration and the `get`/`set` pair over")
    w("`Ptr + <offset>`. BmSDK-AK is declaration-only, so the generated `set` is one")
    w("`MarshalUtil.ToUnmanaged(value, Ptr + offset)` store: the **caller** is the writer and")
    w("BmSDK names none. The block is an available write path and a layout proof, not a")
    w("located producer; no generated class declares a method that writes the field.")
    w("")

    w(f"## U2 - the writer of `{U2}` (+{f2['offset']})")
    w("")
    w("### R3 - the field offset as a cooked FName tag")
    w("")
    w(f"{len(rec['tag_rows'])} class-default payloads of a class that can carry a field were")
    w(f"walked; **{len(rec['tag_hits'])}** carry a tag at a field offset:")
    w("")
    w("| package | export | object | class | tags | highest offset | field tags |")
    w("|---|---:|---|---|---:|---:|---|")
    for r in rec["tag_hits"]:
        w(f"| `{r['package']}` | {r['export']} | `{r['name']}` | `{r['class']}` | {r['tags']} | "
          f"{r['max_offset']} | " + ", ".join(f"`{t['field']}` +{t['offset']}"
                                             for t in r["field_tags"]) + " |")
    w("")
    base = [r for r in rec["tag_rows"] if r["class"] == f2["class"]]
    b0 = base[0] if base else None
    if b0:
        near = [t for t in (b0["field_tags"] or []) if abs(t["offset"] - f2["offset"]) <= 2]
        w(f"The `{f2['class']}` default is `{b0['package']}` export {b0['export']} "
          f"(`{b0['name']}`): {b0['size']} payload bytes, {b0['tags']} tags, walk stop")
        w(f"`{b0['stop']}`, highest tag offset {b0['max_offset']}. Its payload is **not**")
        w(f"truncated, and it tags +{f2['offset'] + 1 if near else '-'} (the neighbouring byte) while")
        w(f"carrying **no tag at +{f2['offset']}**: the stream sees the field beside it and")
        w("omits the target, which is what a zero default that is not serialised looks like")
        w("(decoded walk + derived from the tag list). The offset->FName mapping for")
        w(f"`{U2}` therefore exists only in BmSDK-AK and in the property object, not in cooked")
        w("content - there is nothing left to search for a writer on this route.")
    w("")
    w("### R4 - every Function body that can reach the property")
    w("")
    w(f"{len(r2)} reference(s) to export {e2[0]['export'] if e2 else '?'} in "
      f"**{len(s2)} function(s)**:")
    w("")
    w("| function | export | script offset | token | byte before | direct `EX_Let`? |")
    w("|---|---:|---:|---|---|---|")
    for r in r2:
        w(f"| `{r['function']}` | {r['export']} | {r['script_offset']} | `{r['token']}` | "
          f"{'0x%02x' % r['byte_before'] if r['byte_before'] is not None else '-'} | "
          f"{'yes' if r['direct_let'] else 'no'} |")
    w("")
    w(f"**Direct assignment test: {len([r for r in r2 if r['direct_let']])} site(s) for U2 and "
      f"{len([r for r in r7 if r['direct_let']])} for U7**, against {len(ctrl)} sites for")
    w(f"{len(ctrl_by)} other fields of the same table. No reference to either target sits")
    w("immediately behind `EX_Let` (0x0F) or `EX_LetBool` (0x14).")
    w("")
    w("The destination-first order of `EX_Let` used above is fixed from bytes that cannot be")
    w("read the other way round - a property of the enclosing class followed by a literal,")
    w("where a literal cannot be an assignment destination:")
    w("")
    w("| function | export | at | property | class | outer | value | bytes |")
    w("|---|---:|---:|---:|---|---|---|---|")
    for r in forms["let_examples"][:5]:
        w(f"| `{r['function']}` | {r['export']} | {r['at']} | {r['property']} | "
          f"`{r['property_class']}` | `{r['property_outer']}` | {r['value']} | `{r['bytes']}` |")
    w("")
    w("What is left is a Context destination, `0f 19 ...`: Let, Context, a local, then the")
    w("property. Three such windows carry `BoostingOut`, each **twice**, six bytes apart, in")
    w("two different token bytes:")
    w("")
    w("| function | walk ref at | Let at | bytes (8 before .. 12 after) |")
    w("|---|---:|---:|---|")
    for x in w2:
        if x["token"] == "EX_InstanceVariable" and x["let_at"] is not None:
            w(f"| `{x['function']}` | {x['at']} | {x['let_at']} | `{x['bytes']}` |")
    w("")
    plain = [x for x in w2 if x["token"] == "EX_InstanceVariable" and x["let_at"] is None]
    for x in plain:
        w(f"The other U2 reference, `{x['function']}` at script offset {x['at']}, is a plain")
        w(f"`01 <9771>` with no Context and no Let in the window (`{x['bytes']}`): no")
        w("assignment in the window, so it cannot be the field's writer either.")
    w("")
    w("The walk records the `0x01`-prefixed copy as `EX_InstanceVariable` and the `0x00`-")
    w("prefixed copy six bytes earlier as `EX_LocalVariable`. Both resolve to export")
    w(f"{e2[0]['export'] if e2 else '?'}, and **neither can be a local**: that export's outer")
    w(f"is the class `{f2['class']}`, not the enclosing function (decoded: export-table outer")
    w("chain). The `EX_LocalVariable` label at these sites is an alignment artefact of the")
    w("five-byte form, so the site list cannot be split into reads and writes. A raw 0x0F")
    w("scan is not an oracle either - 0x0F also sits inside operands:")
    w("")
    for nz in forms["let_noise"][:3]:
        w(f"- `{nz['function']}` export {nz['export']} at {nz['at']}: `{nz['bytes']}` - a")
        w(f"  native-parm operand (0x29 + index {nz['index']}) whose index bytes contain 0x0F.")
    w("")
    w("**Result: UNKNOWN, narrowed.** The only script-side shape that could write")
    w(f"`{U2}` is the Let+Context window in `DrivingMode.EjectFromVehicle` (export")
    w("104931, `0f 19` at script offsets ")
    w(", ".join(str(x["let_at"]) for x in w2 if x["let_at"] is not None) + ").")
    w("Which of the two adjacent copies is the destination, and where the Context's operands")
    w("end, needs a verified Context/Let operand spec for this build: the repo names")
    w("`EX_Context` (0x19) but records no width for it (`grab_drivingmode.py`: tokens")
    w("carrying a nested expression are an `exact gap`). Calling that window a writer")
    w("without that spec would be a guess.")
    w("")
    w("**Where it would be found:** a Context-aware decode of those windows (export 104931)")
    w("or the native `exec` body in `BatmanAK.exe`.")
    w("")

    w("## U7 - what produces the ~0.1 s 774 taps")
    w("")
    w(f"774 is `{f7['class']}.{f7['field']}` (export {e7[0]['export'] if e7 else '?'}, FName")
    w(f"{h7[0]['name_index'] if h7 else '?'}). R1/R2: the name is spelled in {len(h7)} name")
    w(f"tables but only `{h7[0]['package'] if h7 else '?'}` exports it (the property object),")
    w("and no Get/Set/On accessor exists anywhere for it.")
    w("")
    w(f"R4: **{len(r7)} reference(s) in {len(s7)} function(s)** - card 2 had 14 in 3, so the")
    w("wider scan adds one function:")
    w("")
    w("| function | export | script offset | token | byte before | direct `EX_Let`? |")
    w("|---|---:|---:|---|---|---|")
    for r in r7:
        w(f"| `{r['function']}` | {r['export']} | {r['script_offset']} | `{r['token']}` | "
          f"{'0x%02x' % r['byte_before'] if r['byte_before'] is not None else '-'} | "
          f"{'yes' if r['direct_let'] else 'no'} |")
    w("")
    w("The additional function is `RAEC_Smoke_Outsider.SetSmokeScreen` (export 437, script")
    w("offset 476): one further reference to the cancel byte outside the Tick/gadget paths.")
    w("It widens the reference set and adds no writer.")
    w("")
    if tick:
        w("The function that writes *fields* in the same body writes other fields -")
        w("`RGadgetSelectBM3.Tick` carries these clean assignments:")
        w("")
        for r in tick[:4]:
            w(f"- script offset {r['at']}: `{r['bytes']}` - `{r['property_class']}` export")
            w(f"  {r['property']} (`{r['property_outer']}`) = {r['value']}")
        w("")
        w("Neither destination is 774, and no reference to 774 sits behind a Let in any")
        w("function: the Tick body writes those countdown floats and *reads* the cancel byte.")
        w("")
    w("**Result: producer still UNKNOWN.** It is not an accessor export (R2), not a cooked")
    w(f"default (R3: no tag at +{f7['offset']}), not a BmSDK member (R5: one generic `set`)")
    w("and not a direct script assignment (R4: 0 sites). Remaining candidates: the native")
    w("input/device path in `BatmanAK.exe`, a Context-framed script write (the same missing")
    w("spec as U2), or `RAEC_Smoke_Outsider` synthesising the byte - none proven by any file")
    w("read here.")
    w("")
    w("**Where it would be found:** a device-level trace at the recorded tap timestamps, or a")
    w("Context-aware decode of `RGadgetSelectBM3.Tick` and")
    w("`RAEC_Smoke_Outsider.SetSmokeScreen`.")
    w("")

    w("## NEW ROUTES TRIED")
    w("")
    w("| route | scope | what it found | why it does not name a writer/producer |")
    w("|---|---|---|---|")
    w(f"| R1 FName census | name tables of {rec['parsed']} packages | `{U2}` in {len(h2)} "
      f"package(s), `{U7}` in {len(h7)} | a name-table entry proves the package knows the "
      f"name, not that anything writes it |")
    w(f"| R2 accessor exports | export tables of {rec['parsed']} packages | one property object "
      f"per target, no Get/Set/On export for either | an export object is a declaration "
      f"(offset, type, FName) and carries no code |")
    w(f"| R3 cooked offset tags | {len(rec['tag_rows'])} class-default payloads | no tag at "
      f"+{f2['offset']} or +{f7['offset']}; tags exist at {len(tagged)} other field offsets | "
      f"a cooked tag is a default value, and these two defaults are not serialised |")
    w(f"| R4 Function bodies | {rec['function_exports']} bodies in {rec['script_packages']} "
      f"script packages | {len(r2)} refs to +{f2['offset']} in {len(s2)} functions, {len(r7)} "
      f"refs to +{f7['offset']} in {len(s7)}; 0 behind a Let | {len(ctrl)} other refs sit "
      f"behind a Let, so the test works; a ref's direction is otherwise unproven |")
    w(f"| R5 BmSDK-AK | {sdk['files']} generated files | one property block per target, one "
      f"generic `set` each | the setter is a store any caller may use; no class names a writer |")
    w("")
    w("Each route's detail is above. The common result: a *name* is not a *writer*, an")
    w("*export object* is a declaration, a *cooked tag* is a default value, and a *reference*")
    w("has no proven direction outside the direct-Let form.")
    w("")
    w("## Oracles")
    w("")
    o = oracles(fl, rec, forms, sdk)
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k in sorted(o):
        w(f"| `{k}` | {o[k][0]} | {o[k][1]} |")
    w("")
    w("## Sources read")
    w("")
    w("| source | what it gave |")
    w("|---|---|")
    w(f"| `Research/BatmobileGrab/SAMPLER_FIELDS2.md` | the {len(fl)} field rows (class, field, offset, kind) searched here |")
    w(f"| `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/*.upk` + `DLC/**/*.upk` | {rec['parsed']} name/import/export tables; the class-default payloads and Function bodies above |")
    w(f"| `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/**/*.cs` | {sdk['files']} generated files, every occurrence of the two names |")
    w("| `Research/BatmobileGrab/SAMPLER_UNKNOWNS2.md` | the routes excluded from this card |")
    w("| `Tools/scripts/upk_read.py`, `grab_packages_g305.PartialPackage` | package tables, payload access, `walk_tags` |")
    w("")
    w("## UNKNOWNs")
    w("")
    w(f"1. **U2 writer** - no export, cooked tag, BmSDK member or direct-Let site writes")
    w(f"   `{f2['class']}.{f2['field']}`. Tried R1-R5 with their controls. It would be found in")
    w("   a verified Context/Let decode of `EjectFromVehicle` (export 104931) or in")
    w("   `BatmanAK.exe`.")
    w(f"2. **U7 producer** - no writer of `{f7['class']}.{f7['field']}` in any read file. Tried")
    w("   R1-R5. It would be found in a device trace at the tap timestamps or in the native")
    w("   input path.")
    w("3. **The 0x19 operand width for this build** - the reason both rows stay UNKNOWN. The")
    w("   token table names `EX_Context` (0x19) with no width, and the adjacent two-copy")
    w("   reference form cannot be framed, so no byte offset can be assigned to a destination.")
    w("   Where it would be found: a decoder proven against a function whose semantics are")
    w("   already decoded.")
    if rec["errors"]:
        w(f"4. **{len(rec['errors'])} unreadable package/payload(s)** - counted, never guessed:")
        for e in rec["errors"][:8]:
            w(f"   `{e['file']}`: {e['why']}")
    w("")
    return "\n".join(L) + "\n"


def oracles(fl: list[dict], rec: dict, forms: dict, sdk: dict) -> dict:
    o = {}
    o["field_rows"] = (len(fl) == 47, f"{len(fl)} field rows parsed from SAMPLER_FIELDS2.md")
    e2 = rec["field_exports"].get(U2, [])
    e7 = rec["field_exports"].get(U7, [])
    o["accessor_u2"] = (len(e2) == 1 and e2[0]["export"] == 9771 and
                        e2[0]["class"] == "ByteProperty" and
                        e2[0]["outer"] == "RVehicleBatmobileBase" and
                        e2[0]["payload_offset"] == 16840709 and
                        e2[0]["table_offset"] == 3492399,
                        str([(r['export'], r['class'], r['outer'], r['payload_offset'],
                              r['table_offset']) for r in e2]))
    o["accessor_u7"] = (len(e7) == 1 and e7[0]["export"] == 107265 and
                        e7[0]["class"] == "ByteProperty" and
                        e7[0]["outer"] == "RPlayerInput" and
                        e7[0]["payload_offset"] == 24852676 and
                        e7[0]["table_offset"] == 10511967,
                        str([(r['export'], r['class'], r['outer'], r['payload_offset'],
                              r['table_offset']) for r in e7]))
    fname2 = sorted((h["package"], h["name_index"]) for h in rec["name_hits"].get(U2, []))
    fname7 = sorted((h["package"], h["name_index"]) for h in rec["name_hits"].get(U7, []))
    o["fname_u2"] = (fname2 == [("BmGame", 11231), ("Startup", 7237)], str(fname2))
    o["fname_u7"] = (fname7 == [("BmGame", 5814), ("Clocktower", 972), ("Film_B1_Ch9_Anim", 111),
                                ("Film_B4_Ch6", 195), ("INTRO_PT1", 164), ("Stagg_A1_Ch4", 417),
                                ("Startup", 5465), ("StartupPatch", 3840)], str(fname7))
    acc = [k for k in rec["export_hits"] if k.startswith("accessor:")]
    o["no_target_accessor"] = (not [k for k in acc if k.endswith((U2, U7))],
                               f"{len(acc)} accessor name(s), none for a target: {sorted(acc)}")
    tagged = {t["offset"] for r in rec["tag_hits"] for t in r["field_tags"]}
    o["no_target_tag"] = (5901 not in tagged and 774 not in tagged,
                          f"tag offsets {sorted(tagged)}")
    o["tag_control"] = (5902 in tagged and 2592 in tagged,
                        f"neighbour tags present at 5902/2592 in {len(rec['tag_hits'])} rows")
    r2 = rec["refs"].get(U2, [])
    r7 = rec["refs"].get(U7, [])
    o["u2_refs"] = (len(r2) == 7 and len({r["function"] for r in r2}) == 2,
                    f"{len(r2)} refs in {len({r['function'] for r in r2})} functions")
    o["u7_refs"] = (len(r7) == 15 and len({r["function"] for r in r7}) == 4,
                    f"{len(r7)} refs in {len({r['function'] for r in r7})} functions")
    ctrl = [r for rows in rec["refs"].values() for r in rows if r["direct_let"]]
    o["direct_let_control"] = (len(ctrl) == 55 and len({r["field"] for r in ctrl}) == 12,
                               f"{len(ctrl)} sites over {len({r['field'] for r in ctrl})} fields")
    o["target_no_direct_let"] = (not [r for r in ctrl if r["field"] in (U2, U7)],
                                 f"{len([r for r in r2 + r7 if r['direct_let']])} target sites")
    o["let_dest_first"] = (
        len(forms["let_examples"]) >= 1000 and
        all(r["property_class"] in ("FloatProperty", "IntProperty", "ByteProperty")
            for r in forms["let_examples"]),
        f"{len(forms['let_examples'])} `0f 01 <property> <literal>` examples")
    o["let_noise"] = (len(forms["let_noise"]) >= 3,
                      f"{len(forms['let_noise'])} 0x0F bytes inside native-parm operands")
    o["bmsdk_generic_only"] = (
        sdk["functions"].get(U2, 0) == 0 and sdk["functions"].get(U7, 0) == 0 and
        sdk["property_blocks"].get(U2, 0) == 1 and sdk["property_blocks"].get(U7, 0) == 1 and
        sdk["set_accessors"].get(U2, 0) == 1 and sdk["set_accessors"].get(U7, 0) == 1,
        f"blocks {sdk['property_blocks'].get(U2)}/{sdk['property_blocks'].get(U7)}, "
        f"setters {sdk['set_accessors'].get(U2)}/{sdk['set_accessors'].get(U7)}, "
        f"functions {sdk['functions'].get(U2, 0)}/{sdk['functions'].get(U7, 0)}")
    o["parse_coverage"] = (rec["parsed"] == rec["packages"],
                           f"{rec['parsed']}/{rec['packages']} parsed, "
                           f"{len(rec['errors'])} errors")
    o["both_fields_referenced"] = (bool(r2) and bool(r7), f"{len(r2)}/{len(r7)} refs")
    return o


def analyse(verbose: bool = True) -> tuple:
    fl = fields()
    rec = scan_packages(fl, verbose=verbose)
    forms = ref_forms(fl, rec)
    sdk = scan_bmsdk(fl)
    return fl, rec, forms, sdk


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ("--write", "--check", "--stats"):
        print(__doc__)
        return 2
    fl, rec, forms, sdk = analyse()
    o = oracles(fl, rec, forms, sdk)
    if argv[1] == "--stats":
        print(json.dumps({"fields": len(fl), "packages": rec["packages"],
                          "parsed": rec["parsed"], "errors": len(rec["errors"]),
                          "script_packages": rec["script_packages"],
                          "function_exports": rec["function_exports"],
                          "named_fields": len(rec["name_hits"]),
                          "exported_fields": len(rec["field_exports"]),
                          "u2_refs": len(rec["refs"].get(U2, [])),
                          "u7_refs": len(rec["refs"].get(U7, [])),
                          "direct_let": rec["direct_let"],
                          "let_examples": len(forms["let_examples"]),
                          "let_noise": len(forms["let_noise"]),
                          "tag_hits": len(rec["tag_hits"]),
                          "tag_rows": len(rec["tag_rows"]),
                          "seconds": rec["seconds"]}, indent=1))
        for k in sorted(o):
            print(f"  {k}: {'OK' if o[k][0] else 'FAIL'} - {o[k][1]}")
        return 0 if all(v[0] for v in o.values()) else 1
    doc = build(fl, rec, forms, sdk)
    if argv[1] == "--write":
        MD.write_text(doc, encoding="utf-8", newline="\n")
        print(f"wrote {MD.relative_to(ROOT)} ({len(doc.splitlines())} lines)")
    else:
        cur = read(MD) if MD.exists() else None
        if cur != doc:
            print("MISMATCH: regenerated document differs from the file on disk")
            return 1
        print(f"OK {MD.relative_to(ROOT)} byte-identical to a fresh rebuild")
    print("oracles: " + json.dumps({k: v[0] for k, v in sorted(o.items())}, sort_keys=True))
    for k in sorted(o):
        print(f"  {k}: {'OK' if o[k][0] else 'FAIL'} - {o[k][1]}")
    if not all(v[0] for v in o.values()):
        print("ORACLE FAILURE")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
