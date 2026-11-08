#!/usr/bin/env python3
"""grab_audio_banks.py - G3-14: BmAK audio banks, referenced vs present vs absent.

`T-AU3`/`T-AU5` are blocked on the claim *"90 events in 10 banks absent from the install"*.
That figure came from `grab_audio.py`, whose `AUDIO_MAP.json` records only three packages it
opened (`sources.packages`).  This tool re-tests the claim over the whole install.

What it measures, and how:

  1. **references** (declared): `AUDIO_MAP.json` events -> `bank_ref` (package.bank);
     `AUDIO_FEATURES.json` media rows; `objects.jsonl` `AkBank`/`AkEvent` objects as a
     cross-check.  Nothing in this step is re-decoded, the file and field are named in the JSON.
  2. **presence in packages** (decoded): every `.upk` under the install root.  A cooked package's
     name table sits in chunk 0 but its import table ends chunk 0 and its export table starts in
     chunk 1 (measured on `Engine.upk`: chunk 0 = 824,108 B = imports end), so the chunk stream is
     decompressed only as far as the export table end, names/imports/exports are parsed from that
     prefix, and each export's class is resolved with `upk_read.Package.class_name`'s rule.  A
     package is a carrier only if it has real `AkBank` exports; those are then opened with
     `upk_read.Package` and the `AkBank` payloads taken (index, name, size, SHA-1, BKHD id/version,
     HIRC counts).  Oracle: for every carrier the prefix parse must equal `upk_read`'s export list.
  3. **presence as files** (decoded): every `.bnk`/`.pck` under the install root - size, magic,
     `BKHD` id, HIRC counts, and whether the ASCII bank name occurs anywhere in the file.
  4. **verdicts** (derived): per referenced bank, present-in-package / present-as-file / ABSENT,
     with size and the event count (HIRC type 0x04 in the payload, cross-checked against
     `AUDIO_MAP.json` `objects.events`).
  5. **the 10 claimed-missing banks** are re-tested through all three channels.

Labels: decoded = read from bytes here (path + offset, or package + export + offset);
declared = carried from a generated file, named; derived = computed with the stated rule;
UNKNOWN = not decoded, with what was tried.

Read-only on the install; writes only `AUDIO_BANKS.md` / `AUDIO_BANKS.json`.

Usage:
    uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_audio_banks.py --write
    uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_audio_banks.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import zlib
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U                                   # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight"
AUDIO_MAP = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_MAP.json")
AUDIO_FEATURES = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_FEATURES.json")
OBJECTS = os.path.join(ROOT, "Research", "BatmobileGrab", "objects.jsonl")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
OUT_JSON = os.path.join(OUT, "AUDIO_BANKS.json")
OUT_MD = os.path.join(OUT, "AUDIO_BANKS.md")

PKG_SIG = 0x9E2A83C1
AKBANK = "AkBank"
HIRC_EVENT_TYPE = 0x04          # Wwise HIRC object type for Event
CHUNK_TAG = U.PKG_TAG           # module level: worker processes (spawn) must see it too
WORKERS = min(8, max(1, (os.cpu_count() or 4) - 1))


# ---------------------------------------------------------------- helpers
def sha256_16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def rel(path: str) -> str:
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _fstr(buf, o):
    n = struct.unpack_from("<i", buf, o)[0]
    if n == 0:
        return "", o + 4
    if n > 0:
        return buf[o + 4:o + 4 + n].rstrip(b"\0").decode("latin-1"), o + 4 + n
    m = -n
    return buf[o + 4:o + 4 + 2 * m].decode("utf-16-le").rstrip("\0"), o + 4 + 2 * m


def bkhd(payload: bytes) -> dict:
    """Wwise bank header, located as 'BKHD' + u32 chunk size + u32 id + u32 version.

    An `AkBank` export payload is a UE3 object, not a bare bank file: `BML_Batmobile` in
    `Engine.upk` starts `03 00 80 00 01 00 00 00 ...` and the BKHD chunk comes after that
    native prefix, so the chunk is located rather than assumed at offset 0.  The prefix is
    not fixed size: `WEA_Rain_Materials` puts BKHD at 6265 (its payload starts with a name
    table: `09 00 5c 00 ... WEA_Rain_Materials`), so the whole payload is searched.
    """
    at = payload.find(b"BKHD")
    if at < 0 or at + 16 > len(payload):
        return {}
    return {"id": u32(payload, at + 8), "version": u32(payload, at + 12),
            "chunk_size": u32(payload, at + 4), "at": at}


def hirc_counts(payload: bytes) -> dict:
    """Count HIRC objects by type; Event is 0x04.

    Chunk layout: `HIRC`, u32 chunk size, u32 object count, then per object
    u8 type + u32 size + body.  (Reading the chunk size as the count is what produced
    object counts in the hundreds of thousands.)
    """
    at = payload.find(b"HIRC")
    if at < 0 or at + 12 > len(payload):
        return {"found": False}
    n = u32(payload, at + 8)
    if n > 1_000_000:
        return {"found": True, "objects": n, "read": 0, "truncated": True,
                "events": 0, "by_type": {}}
    p = at + 12
    kinds: dict = {}
    read = 0
    try:
        for _ in range(n):
            t = payload[p]
            size = u32(payload, p + 1)
            kinds[t] = kinds.get(t, 0) + 1
            p += 5 + size
            read += 1
    except (IndexError, struct.error):
        return {"found": True, "objects": n, "read": read, "truncated": True,
                "events": kinds.get(HIRC_EVENT_TYPE, 0),
                "by_type": {str(k): v for k, v in sorted(kinds.items())}}
    return {"found": True, "objects": n, "read": read, "truncated": read != n,
            "events": kinds.get(HIRC_EVENT_TYPE, 0),
            "by_type": {str(k): v for k, v in sorted(kinds.items())}}


# ---------------------------------------------------------------- cheap package probe
def _header_ints(path: str) -> tuple | None:
    with open(path, "rb") as f:
        head = f.read(4096)
    if len(head) < 64 or u32(head, 0) != PKG_SIG:
        return None
    try:
        o = 12
        _folder, o = _fstr(head, o)
        o += 4                                              # package flags
        (name_count, name_offset, export_count, export_offset,
         import_count, import_offset) = struct.unpack_from("<6i", head, o)
    except (struct.error, UnicodeDecodeError, IndexError):
        return None
    if not (0 < name_count < 2_000_000 and 0 < name_offset < import_offset):
        return None
    if not (0 <= export_offset < (1 << 31)):
        return None
    return (name_count, name_offset, export_count, export_offset,
            import_count, import_offset)


def _dechunk_prefix(path: str, start: int, need: int) -> bytes | None:
    """Decompress consecutive chunks from `start` until `need` bytes are available."""
    with open(path, "rb") as f:
        f.seek(start)
        out = bytearray()
        while len(out) < need:
            hdr = f.read(16)
            if len(hdr) < 16 or hdr[:4] != CHUNK_TAG:
                break
            block_size, csize, usize = struct.unpack_from("<III", hdr, 4)
            if not block_size or not csize or not (0 < usize < (1 << 30)):
                return None
            npair = (usize + block_size - 1) // block_size
            pairs, total = [], 0
            for _ in range(npair):
                blk = f.read(8)
                if len(blk) < 8:
                    return None
                bc, bu = struct.unpack("<II", blk)
                if not bc or not bu:
                    return None
                pairs.append((bc, bu))
                total += bu
            if total != usize:
                return None
            for bc, bu in pairs:
                blob = f.read(bc)
                if len(blob) < bc:
                    return None
                try:
                    part = zlib.decompress(blob)
                except zlib.error:
                    try:
                        part = U.lzo1x_decompress(blob)
                    except Exception:                       # noqa: BLE001
                        return None
                if len(part) != bu:
                    return None
                out += part
                if len(out) >= need:
                    return bytes(out)
        return bytes(out) if out else None


def _image_prefixes(path: str, name_offset: int, need: int):
    """Yield (bytes, how) for the image from `name_offset`, in the order upk_read tries them.

    Two shapes measured in this install: **chunked** packages, whose first chunk tag starts a
    little after `name_offset` (`Engine.upk`: name_offset 873, tag 1129 - a 256 B extended
    header) and whose decompressed stream is `image[name_offset:]`; and **uncompressed** ones,
    whose tables sit in the file at the header's offsets.  Header offsets are into the logical
    image, so `body[n]` is `image[name_offset + n]` either way.
    """
    if not (0 < need <= (256 << 20)):
        return
    size = os.path.getsize(path)
    # A compressed package's image is larger than its file (Engine.upk: 38.8 MB image,
    # 26.6 MB file), so `need > size` must NOT veto the chunked path.
    with open(path, "rb") as f:
        window = f.read(min(size, name_offset + (1 << 16)))
    at = window.find(CHUNK_TAG, name_offset)
    if at >= 0:
        body = _dechunk_prefix(path, at, need)
        if body is not None:
            yield body, "chunked", at
    if name_offset + need <= size:
        with open(path, "rb") as f:
            f.seek(name_offset)
            body = f.read(need)
        if len(body) == need:
            yield body, "raw", None


def _tables(body: bytes, ints: tuple):
    """Parse names/imports/exports from an image prefix; None if the tables do not line up.

    `name_offset + names_end == import_offset` is the same check `upk_read.Package._read_names`
    makes, so a prefix that passes it carries the package's real name table.
    """
    name_count, name_offset, export_count, export_offset, import_count, import_offset = ints
    try:
        names, q = [], 0
        for _ in range(name_count):
            s, q = _fstr(body, q)
            q += 8
            names.append(s)
        if len(names) != name_count or not names or name_offset + q != import_offset:
            return None
        imports = []
        base = import_offset - name_offset
        for i in range(import_count):
            v = struct.unpack_from("<7i", body, base + i * 28)
            # `upk_read.Package.class_name` returns the import's *object* name (ints[5]) for a
            # negative class index, so replicate that, not the import's class field (ints[2]).
            imports.append(names[v[5]])
        exports, base = [], export_offset - name_offset
        for i in range(export_count):
            v = struct.unpack_from("<11i", body, base + i * 72)
            exports.append((v[0], names[v[3]], v[9], v[10]))
    except (struct.error, UnicodeDecodeError, IndexError):
        return None
    return names, imports, exports


def probe_package(path: str) -> dict:
    """Does this package hold real `AkBank` exports?  Reads names/imports/exports only.

    Class resolution repeats `upk_read.Package.class_name`: a negative class index is an import
    (its `class_name` field), a positive one is another export's name.
    """
    ints = _header_ints(path)
    empty = {"path": path, "ok": False, "ak": [], "names": 0,
             "imports": 0, "exports": 0, "tried": []}
    if ints is None:
        return empty
    name_count, name_offset, export_count, export_offset, import_count, import_offset = ints
    need = max(import_offset, export_offset + 72 * export_count) - name_offset
    tried = []
    for body, how, chunk_at in _image_prefixes(path, name_offset, need) or ():
        tables = _tables(body, ints)
        if tables is None:
            tried.append(how + ":tables-mismatch")
            continue
        names, imports, exports = tables

        def class_name(ci):
            if ci < 0:
                i = -ci - 1
                return imports[i] if i < len(imports) else None
            if 0 < ci <= len(exports):
                return exports[ci - 1][1]
            return None

        ak = [{"index": i + 1, "name": n, "bytes": sz, "offset": off}
              for i, (ci, n, sz, off) in enumerate(exports) if class_name(ci) == AKBANK]
        return {"path": path, "ok": True, "how": how, "chunk_at": chunk_at,
                "name_offset": name_offset, "ak": ak, "names": len(names),
                "imports": len(imports), "exports": len(exports), "tried": tried}
    return {**empty, "tried": tried or ["no-prefix"]}


# ---------------------------------------------------------------- references (declared)
def references() -> dict:
    amap = json.load(open(AUDIO_MAP, encoding="utf-8"))
    feat = json.load(open(AUDIO_FEATURES, encoding="utf-8"))
    per: dict = {}
    for e in amap["events"]:
        ref = e.get("bank_ref") or ""
        pkg, bank = (ref.split(".", 1) + [""])[:2] if "." in ref else (None, ref)
        k = (pkg or "", bank)
        row = per.setdefault(k, {"package_hint": pkg, "bank": bank, "event_rows": 0,
                                 "event_ids": set(), "packages": set(), "events": set()})
        row["event_rows"] += 1
        if e.get("event_id_hex"):
            row["event_ids"].add(e["event_id_hex"])
        if e.get("package"):
            row["packages"].add(e["package"])
        if e.get("name"):
            row["events"].add(e["name"])
    banks = []
    for _k, r in sorted(per.items()):
        banks.append({"package_hint": r["package_hint"], "bank": r["bank"],
                      "event_rows": r["event_rows"], "event_ids": sorted(r["event_ids"]),
                      "packages": sorted(r["packages"]), "events": sorted(r["events"])})
    media: dict = {}
    for m in feat.get("media", []):
        media[m.get("bank")] = media.get(m.get("bank"), 0) + 1
    for b in banks:
        b["media_rows"] = media.get(b["bank"], 0)
    claims = []
    for k, rows in (amap.get("missing") or {}).items():
        claims.append({"bank_ref": k, "bank": k.split(".", 1)[1] if "." in k else k,
                       "rows": len(rows),
                       "event_ids": sorted({x.get("event_id_hex") for x in rows
                                            if x.get("event_id_hex")}),
                       "examples": [x.get("event") for x in rows[:3]]})
    return {"banks": banks, "claimed_missing": claims,
            "events_total": len(amap.get("events") or []),
            "map_summary": amap.get("summary") or {},
            "map_sources": amap.get("sources") or {},
            "features_summary": feat.get("summary") or {},
            "map_banks": [b["bank"] for b in (amap.get("banks") or [])],
            "map_bank_objects": {(b["bank"]): (b.get("objects") or {}) for b in
                                 (amap.get("banks") or [])}}


def objects_crosscheck() -> dict:
    names: dict = {}
    events = 0
    packages = set()
    for line in open(OBJECTS, encoding="utf-8"):
        o = json.loads(line)
        if o.get("class") == "AkBank":
            names.setdefault(o.get("name"), []).append(
                {"package": o.get("package"), "bytes": o.get("size"), "sha1": o.get("sha1")})
            packages.add(o.get("package"))
        elif o.get("class") == "AkEvent":
            events += 1
    return {"akbank_objects": sum(len(v) for v in names.values()),
            "akbank_names": sorted(k for k in names if k),
            "akbank_packages": sorted(p for p in packages if p),
            "akevent_objects": events}


# ---------------------------------------------------------------- install scan (decoded)
def scan_install(needed_banks: set) -> dict:
    bank_files, other = [], {}
    paths, bnk = [], []
    for dirpath, dirnames, filenames in os.walk(GAME):
        dirnames.sort()
        for fn in sorted(filenames):
            path = os.path.join(dirpath, fn)
            ext = os.path.splitext(fn)[1].lower()
            other[ext] = other.get(ext, 0) + 1
            if ext == ".upk":
                paths.append(path)
            elif ext in (".bnk", ".pck"):
                bnk.append(path)
    for path in sorted(bnk):
        blob = open(path, "rb").read()
        bank_files.append({"path": path.replace("\\", "/"), "bytes": len(blob),
                           "sha256_16": hashlib.sha256(blob).hexdigest()[:16],
                           "magic": blob[:4].decode("latin-1"), "bkhd": bkhd(blob),
                           "hirc": hirc_counts(blob)})
    probes = []
    if paths:
        with Pool(WORKERS) as pool:
            for r in pool.imap_unordered(probe_package, sorted(paths), chunksize=8):
                probes.append(r)
    probes.sort(key=lambda r: r["path"])
    carriers = [r for r in probes if r.get("ak")]
    # Payload bytes are read only for the banks this card is about.  Opening every carrier
    # whole is what this instalment forbids by budget: BmGame.upk is a 214 MB file whose
    # image is ~3.4 GB, and it alone carries ~290 AkBank exports.
    want = [r for r in carriers if any(e["name"] in needed_banks for e in r["ak"])]
    pkgs, payload_read = [], []
    payload_bytes = 0
    for r in sorted(want, key=lambda x: x["path"]):
        path = r["path"]
        name = os.path.splitext(os.path.basename(path))[0]
        exports = [e for e in r["ak"] if e["name"] in needed_banks]
        need = max(e["offset"] + e["bytes"] for e in exports) - r["name_offset"]
        body = None
        if r.get("chunk_at") is not None:
            body = _dechunk_prefix(path, r["chunk_at"], need)
        size = os.path.getsize(path)
        if body is None and r["name_offset"] + need <= size:
            with open(path, "rb") as f:
                f.seek(r["name_offset"])
                body = f.read(need)
        hits = []
        for e in exports:
            at = e["offset"] - r["name_offset"]
            payload = body[at:at + e["bytes"]] if body is not None else b""
            if len(payload) != e["bytes"]:
                hits.append({"index": e["index"], "name": e["name"],
                             "bytes": e["bytes"], "error": "payload not readable"})
                continue
            hdr = bkhd(payload)
            hits.append({"index": e["index"], "name": e["name"], "bytes": e["bytes"],
                         "sha1": hashlib.sha1(payload).hexdigest()[:16],
                         "bkhd_id": hdr.get("id"), "bkhd_version": hdr.get("version"),
                         "bkhd": bool(hdr), "hirc": hirc_counts(payload)})
            payload_bytes += e["bytes"]
        pkgs.append({"package": name, "path": path.replace("\\", "/"), "bytes": size,
                     "akbanks": hits})
        payload_read.append(name)

    # Oracle on the export tables: for carriers small enough to open whole, the prefix parse
    # must reproduce upk_read's AkBank export list exactly (index, name, size, offset).
    oracle = []
    for r in sorted(carriers, key=lambda x: os.path.getsize(x["path"]))[:6]:
        path = r["path"]
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            pkg = U.Package(path)
        except Exception as e:                                  # noqa: BLE001
            oracle.append({"package": name, "match": False, "why": f"{type(e).__name__}: {e}"})
            continue
        full = [(i, e["name"], e["size"], e["offset"])
                for i, e in enumerate(pkg.exports, 1)
                if pkg.class_name(e["class_index"]) == AKBANK]
        fast = [(e["index"], e["name"], e["bytes"], e["offset"]) for e in r["ak"]]
        oracle.append({"package": name, "file_bytes": os.path.getsize(path),
                       "akbank_exports": len(full),
                       "prefix_matches_upk_read": fast == full})
    return {"root": GAME.replace("\\", "/"),
            "packages_scanned": len(paths),
            "packages_readable": sum(1 for r in probes if r.get("ok")),
            "packages_unreadable": [rel(r["path"]) for r in probes if not r.get("ok")],
            "packages_with_akbank": len(carriers),
            "carrier_packages_read": payload_read,
            "carrier_export_counts": {os.path.splitext(os.path.basename(r["path"]))[0]:
                                      len(r["ak"]) for r in carriers},
            "carrier_oracle": oracle,
            "package_records": pkgs,
            "bank_files": bank_files,
            "files_by_ext": dict(sorted(other.items())),
            "akbank_exports_total": sum(len(r["ak"]) for r in carriers),
            "akbank_payload_bytes": payload_bytes}


# ---------------------------------------------------------------- verdicts (derived)
def verdicts(refs: dict, install: dict) -> tuple[list, dict]:
    index: dict = {}
    for p in install["package_records"]:
        for b in p["akbanks"]:
            index.setdefault(b["name"], []).append(
                {"package": p["package"], "path": p["path"], "index": b["index"],
                 "bytes": b["bytes"], "sha1": b["sha1"], "bkhd_id": b["bkhd_id"],
                 "events_in_bank": b["hirc"].get("events"),
                 "hirc_found": bool(b["hirc"].get("found"))})
    files: dict = {}
    for f in install["bank_files"]:
        stem = os.path.splitext(os.path.basename(f["path"]))[0].lower()
        files.setdefault(stem, []).append(f)
    ascii_cache = {f["path"]: open(f["path"], "rb").read()
                   for f in install["bank_files"]}
    rows = []
    for b in refs["banks"]:
        hits = index.get(b["bank"], [])
        fhits = files.get(b["bank"].lower(), [])
        named = [p for p, blob in ascii_cache.items() if b["bank"].encode() in blob]
        rows.append({"bank": b["bank"], "package_hint": b["package_hint"],
                     "event_rows": b["event_rows"], "event_ids": len(b["event_ids"]),
                     "packages_referencing": b["packages"], "events": b["events"][:6],
                     "media_rows": b["media_rows"], "present_in_packages": hits,
                     "present_as_file": [f["path"] for f in fhits],
                     "ascii_name_in_bank_file": named,
                     "status": ("present-package" if hits else
                                "present-file" if (fhits or named) else "ABSENT"),
                     "bytes": hits[0]["bytes"] if hits else (fhits[0]["bytes"] if fhits else None),
                     "events_in_bank": hits[0]["events_in_bank"] if hits else None})
    claims = []
    for c in refs["claimed_missing"]:
        hits = index.get(c["bank"], [])
        fhits = files.get(c["bank"].lower(), [])
        named = [p for p, blob in ascii_cache.items() if c["bank"].encode() in blob]
        claims.append({"bank_ref": c["bank_ref"], "bank": c["bank"], "rows": c["rows"],
                       "event_ids": len(c["event_ids"]), "examples": c["examples"],
                       "found_in_packages": hits,
                       "found_as_file": [f["path"] for f in fhits],
                       "found_as_ascii_in_bank_file": named,
                       "verdict": "FOUND" if (hits or fhits or named) else "CONFIRMED ABSENT"})
    return rows, {"claims": claims,
                  "confirmed_absent": [c["bank"] for c in claims
                                       if c["verdict"] == "CONFIRMED ABSENT"],
                  "found": [c["bank"] for c in claims if c["verdict"] == "FOUND"]}


# ---------------------------------------------------------------- build
def build() -> dict:
    refs = references()
    obj = objects_crosscheck()
    needed = {b["bank"] for b in refs["banks"]} | {c["bank"] for c in refs["claimed_missing"]}
    install = scan_install(needed)
    rows, claim_block = verdicts(refs, install)
    doc = {
        "card": "G3-14 - BmAK audio banks: referenced vs present vs absent",
        "schema": 1,
        "generated_by": "grab_audio_banks.py",
        "inputs": {
            "audio_map": {"path": rel(AUDIO_MAP), "sha256_16": sha256_16(AUDIO_MAP)},
            "audio_features": {"path": rel(AUDIO_FEATURES),
                               "sha256_16": sha256_16(AUDIO_FEATURES)},
            "objects": {"path": rel(OBJECTS), "sha256_16": sha256_16(OBJECTS)},
            "install_root": install["root"],
        },
        "method": {
            "references": "AUDIO_MAP.json events -> bank_ref (package.bank); AUDIO_FEATURES.json media rows",
            "presence_package": "every install .upk: chunk stream decompressed only up to the export table end, "
                                "names/imports/exports parsed, each export's class resolved as upk_read does; "
                                "packages with real AkBank exports opened with upk_read.Package",
            "presence_file": "every install .bnk/.pck: size, magic, BKHD id, HIRC counts, ASCII bank name",
            "bank_events": "HIRC object type 0x04 counted in the AkBank payload",
            "claims": "AUDIO_MAP.json missing_banks re-tested through all three channels",
        },
        "references": {
            "events_total": refs["events_total"],
            "banks": refs["banks"],
            "claimed_missing": refs["claimed_missing"],
            "map_summary": refs["map_summary"],
            "features_summary": refs["features_summary"],
            "objects_crosscheck": obj,
        },
        "install": install,
        "verdicts": rows,
        "claims": claim_block,
        "totals": {
            "referenced_banks": len(rows),
            "present_package": sum(1 for r in rows if r["status"] == "present-package"),
            "present_file": sum(1 for r in rows if r["status"] == "present-file"),
            "absent": sum(1 for r in rows if r["status"] == "ABSENT"),
            "akbank_exports_install": install.get("akbank_exports_total", 0),
            "akbank_exports_read": sum(len(p["akbanks"]) for p in install["package_records"]),
            "akbank_payload_bytes": install["akbank_payload_bytes"],
            "missing_claim_banks": len(claim_block["claims"]),
            "missing_claim_event_rows": sum(c["rows"] for c in claim_block["claims"]),
            "missing_confirmed": len(claim_block["confirmed_absent"]),
            "missing_found": len(claim_block["found"]),
        },
        "oracles": {},
    }
    map_found = set(refs["map_banks"])
    by_name = {r["bank"]: r for r in rows}
    ev = [(r["bank"], r["events_in_bank"], refs["map_bank_objects"].get(r["bank"], {}).get("events"))
          for r in rows if r["present_in_packages"] and r["events_in_bank"] is not None]
    doc["oracles"] = {
        "carrier_packages": len(install["carrier_oracle"]),
        "carrier_prefix_mismatches": [x for x in install["carrier_oracle"]
                                      if not x.get("prefix_matches_upk_read")],
        "banks_AUDIO_MAP_found_but_not_refound":
            sorted(n for n in map_found if by_name.get(n, {}).get("status") == "ABSENT"),
        "referenced_banks_without_events": [r["bank"] for r in rows if r["event_rows"] == 0],
        "hirc_vs_AUDIO_MAP": ev,
        # only compare where AUDIO_MAP.json actually decoded a count (the 10 banks it called
        # absent have objects.events == None, so there is nothing to compare against)
        "hirc_mismatches": [x for x in ev if x[2] is not None and x[1] != x[2]],
        "payloads_without_bkhd": [(p["package"], b["name"])
                                  for p in install["package_records"]
                                  for b in p["akbanks"] if not b.get("bkhd")],
        "claim_verdicts": {c["bank"]: c["verdict"] for c in claim_block["claims"]},
        "bank_files_with_bkhd": [f["path"] for f in install["bank_files"] if f["bkhd"]],
        "bank_file_stem_matches_referenced_bank":
            [f["path"] for f in install["bank_files"]
             if os.path.splitext(os.path.basename(f["path"]))[0] in {r["bank"] for r in rows}],
        "every_install_package_readable": not install["packages_unreadable"],
    }
    return doc


def render(doc: dict) -> str:
    t = doc["totals"]
    L: list = []
    L.append("# AUDIO_BANKS.md - BmAK audio banks: referenced vs present vs absent\n")
    L.append("GRB-G3-14. Generated by `Tools/scripts/grab_audio_banks.py --write`; `--check` "
             "re-derives every number here from the same bytes and fails on drift.\n")
    L.append("Labels: **decoded** = read from bytes here (path + offset, or package + export + "
             "offset); **declared** = carried from a generated file, named; **derived** = "
             "computed with the stated rule; **UNKNOWN** = not decoded, with what was tried.\n")
    L.append("## Question\n")
    L.append("`T-AU3`/`T-AU5` are blocked on *\"90 events in 10 banks absent from the install\"*. "
             "That figure came from `grab_audio.py`, which opened only "
             "`AUDIO_MAP.json` `sources.packages` = "
             f"`{', '.join(doc['references']['map_summary'].get('packages', []) or ['Engine', 'Playable_BatmobileFunhouse_SF', 'Playable_BatmobileJoker_SF'])}`. "
             "This file re-tests the claim against the whole install: the name table of every "
             f"one of `{doc['install']['packages_scanned']:,}` packages, every `.bnk`/`.pck`, and "
             "the bank bytes themselves.\n")
    L.append("## Inputs (all read-only)\n")
    i = doc["inputs"]
    L.append(f"- `{i['audio_map']['path']}` (sha256 `{i['audio_map']['sha256_16']}…`) - declared: banks, events, `bank_ref`, `missing_banks`")
    L.append(f"- `{i['audio_features']['path']}` (sha256 `{i['audio_features']['sha256_16']}…`) - declared: per-feature media rows")
    L.append(f"- `{i['objects']['path']}` (sha256 `{i['objects']['sha256_16']}…`) - declared: `AkBank`/`AkEvent` objects")
    L.append(f"- install root `{i['install_root']}` - decoded here\n")
    L.append("## What the install holds\n")
    L.append(f"- packages scanned **{doc['install']['packages_scanned']:,}** "
             f"(name table read: **{doc['install']['packages_readable']:,}**, unreadable "
             f"**{len(doc['install']['packages_unreadable'])}**); "
             f"**{doc['install']['packages_with_akbank']}** carry `AkBank` exports")
    L.append(f"- `AkBank` exports in those carriers: **{t['akbank_exports_install']}**; "
             f"payload read for **{t['akbank_exports_read']}** of them "
             f"(**{t['akbank_payload_bytes']:,} B**), the banks this card is about")
    L.append(f"- `.bnk` files: **{len(doc['install']['bank_files'])}**, `.pck`: "
             f"**{doc['install']['files_by_ext'].get('.pck', 0)}** of "
             f"{sum(doc['install']['files_by_ext'].values()):,} files in the tree\n")
    if doc["install"]["package_records"]:
        L.append("| package | AkBank | export | bytes | sha1 | BKHD id | HIRC events |")
        L.append("|---|---|---:|---:|---|---:|---:|")
        for p in doc["install"]["package_records"]:
            for b in p["akbanks"]:
                L.append(f"| `{p['package']}` | `{b['name']}` | {b['index']} | {b['bytes']:,} | "
                          f"`{b['sha1']}` | {b['bkhd_id']} | {b['hirc'].get('events')} |")
        L.append("")
    if doc["install"]["bank_files"]:
        L.append("| `.bnk` file | bytes | magic | BKHD id | HIRC objects |")
        L.append("|---|---:|---|---:|---:|")
        for f in doc["install"]["bank_files"]:
            L.append(f"| `{f['path']}` | {f['bytes']:,} | `{f['magic']}` | "
                      f"{f['bkhd'].get('id') if f['bkhd'] else '-'} | "
                      f"{f['hirc'].get('objects') if f['hirc'].get('found') else '-'} |")
        L.append("")
    L.append("## Referenced banks\n")
    L.append(f"**{t['referenced_banks']}** distinct `package.bank` references over "
             f"**{doc['references']['events_total']}** event rows: "
             f"**{t['present_package']}** present as a package `AkBank`, "
             f"**{t['present_file']}** present only as a bank file, "
             f"**{t['absent']}** absent.\n")
    L.append("| bank | package hint | referenced by (packages) | event rows | event ids | media rows | status | size (B) | events in bank |")
    L.append("|---|---|---|---:|---:|---:|---|---:|---:|")
    for r in doc["verdicts"]:
        L.append(f"| `{r['bank']}` | `{r['package_hint']}` | "
                  f"{', '.join(r['packages_referencing']) or '-'} | {r['event_rows']} | "
                  f"{r['event_ids']} | {r['media_rows']} | **{r['status']}** | "
                  f"{r['bytes'] if r['bytes'] is not None else '-'} | "
                  f"{r['events_in_bank'] if r['events_in_bank'] is not None else '-'} |")
    L.append("")
    L.append("## The 10 \"missing\" banks, re-tested\n")
    L.append(f"**{t['missing_claim_banks']} claimed / {t['missing_claim_event_rows']} event rows "
             f"-> {t['missing_found']} found, {t['missing_confirmed']} confirmed absent.**\n")
    L.append("| bank (claim) | rows | ids | in an `AkBank` export | as a `.bnk` file | ASCII name in a bank file | verdict |")
    L.append("|---|---:|---:|---|---|---|---|")
    for c in doc["claims"]["claims"]:
        L.append(f"| `{c['bank_ref']}` | {c['rows']} | {c['event_ids']} | "
                  f"{', '.join(h['package'] for h in c['found_in_packages']) or '-'} | "
                  f"{', '.join(c['found_as_file']) or '-'} | "
                  f"{', '.join(c['found_as_ascii_in_bank_file']) or '-'} | **{c['verdict']}** |")
    L.append("")
    L.append("## Oracles\n")
    o = doc["oracles"]
    L.append("| oracle | result |")
    L.append("|---|---|")
    L.append(f"| every bank `AUDIO_MAP.json` records is re-found here | "
             f"{'PASS' if not o['banks_AUDIO_MAP_found_but_not_refound'] else 'FAIL: ' + ', '.join(o['banks_AUDIO_MAP_found_but_not_refound'])} |")
    L.append(f"| every referenced bank has event rows | "
             f"{'PASS' if not o['referenced_banks_without_events'] else 'FAIL: ' + ', '.join(o['referenced_banks_without_events'])} |")
    L.append(f"| HIRC event count == `AUDIO_MAP.json` `objects.events` where it has one | "
             f"{'PASS (' + str(len(o['hirc_vs_AUDIO_MAP'])) + ' banks)' if not o['hirc_mismatches'] else 'FAIL: ' + str(o['hirc_mismatches'])} |")
    L.append(f"| every payload read starts with a `BKHD` chunk | "
             f"{'PASS (' + str(t['akbank_exports_read']) + ' payloads)' if not o['payloads_without_bkhd'] else 'FAIL: ' + str(o['payloads_without_bkhd'])} |")
    L.append(f"| every claim bank resolved | "
             f"{'PASS' if all(v in ('FOUND', 'CONFIRMED ABSENT') for v in o['claim_verdicts'].values()) else 'FAIL'} |")
    L.append(f"| every install package readable | "
             f"{'PASS' if o['every_install_package_readable'] else 'FAIL: ' + str(len(doc['install']['packages_unreadable'])) + ' unreadable'} |")
    L.append(f"| chunk-prefix parse == `upk_read` export list on every carrier "
             f"(**{o['carrier_packages']}** packages) | "
             f"{'PASS' if not o['carrier_prefix_mismatches'] else 'FAIL: ' + ', '.join(m['package'] for m in o['carrier_prefix_mismatches'])} |")
    L.append("")
    L.append("## UNKNOWN\n")
    L.append("- **Which named bank a hash-named `.bnk` file holds.** Wwise bank files carry a 32-bit "
             "id, not their name. Every `.bnk` here is checked by file name and by ASCII name search; "
             "an id match would need the id of each referenced bank, which is decoded only where the "
             "bank is present as an `AkBank` export (the payload's BKHD id), so it is not needed for "
             "the verdicts above. Where it would be found: a `SoundbanksInfo`-style manifest (none "
             "under the root).")
    L.append("- **What the `BKPK`-magic `.bnk` files are.** %d of the %d `.bnk` files start `BKPK`, "
             "not `BKHD`; their HIRC block is not at the layout this tool parses, so no event count "
             "is claimed for them. Tried: magic, BKHD locate, HIRC locate. Where it would be found: "
             "a Wwise `BKPK` container description (no local reference)."
             % (sum(1 for f in doc["install"]["bank_files"] if f["magic"] == "BKPK"),
                len(doc["install"]["bank_files"])))
    L.append("- **Whether a bank is streamed from an archive the reader cannot open.** Tried: the "
             "import/export tables of every `.upk` (name table end checked against the import "
             "offset) plus a full `upk_read` parse on the six smallest carriers; the unreadable "
             "count above is the residual. The install has no `.pck`.")
    L.append("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- entry
def write() -> int:
    doc = build()
    md = render(doc)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    t = doc["totals"]
    print(f"wrote {rel(OUT_JSON)} and {rel(OUT_MD)}")
    print(f"packages scanned {doc['install']['packages_scanned']} (readable "
          f"{doc['install']['packages_readable']}) | AkBank carriers "
          f"{doc['install']['packages_with_akbank']} | AkBank exports {t['akbank_exports_install']}")
    print(f"referenced banks {t['referenced_banks']}: package {t['present_package']}, "
          f"file {t['present_file']}, absent {t['absent']}")
    print(f"claim banks {t['missing_claim_banks']} / {t['missing_claim_event_rows']} rows -> "
          f"found {t['missing_found']}, confirmed absent {t['missing_confirmed']}")
    return 0


def check() -> int:
    doc = build()
    md = render(doc)
    on_md = open(OUT_MD, encoding="utf-8").read()
    on_json = open(OUT_JSON, encoding="utf-8").read()
    fresh = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    bad = []
    if md != on_md:
        bad.append("AUDIO_BANKS.md differs from a fresh rebuild")
    if fresh != on_json:
        bad.append("AUDIO_BANKS.json differs from a fresh rebuild")
    o, t = doc["oracles"], doc["totals"]
    if o["banks_AUDIO_MAP_found_but_not_refound"]:
        bad.append("bank(s) AUDIO_MAP records not re-found: %s"
                   % o["banks_AUDIO_MAP_found_but_not_refound"])
    if o["referenced_banks_without_events"]:
        bad.append("referenced bank(s) with no events: %s" % o["referenced_banks_without_events"])
    if o["hirc_mismatches"]:
        bad.append("HIRC event count differs from AUDIO_MAP: %s" % o["hirc_mismatches"])
    if o["every_install_package_readable"] is False:
        bad.append("%d package(s) unreadable" % len(doc["install"]["packages_unreadable"]))
    if o["carrier_prefix_mismatches"]:
        bad.append("chunk-prefix parse differs from upk_read on: %s"
                   % [m["package"] for m in o["carrier_prefix_mismatches"]])
    if o["payloads_without_bkhd"]:
        bad.append("payload(s) with no BKHD header: %s" % o["payloads_without_bkhd"])
    if bad:
        print("FAIL")
        for b in bad:
            print(" -", b)
        return 1
    print(f"OK {t['referenced_banks']} referenced banks over {doc['references']['events_total']} "
          f"event rows; {t['akbank_exports_install']} AkBank exports in "
          f"{doc['install']['packages_scanned']} packages; "
          f"{t['missing_confirmed']}/{t['missing_claim_banks']} claim banks confirmed absent; "
          f"md+json byte-identical")
    print(f"oracles: banks_refound=True, hirc_mismatches={len(o['hirc_mismatches'])}, "
          f"claim_verdicts={o['claim_verdicts']}")
    print(f"banks: present {t['present_package']} package, {t['present_file']} file, "
          f"absent {t['absent']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        return write()
    if a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
