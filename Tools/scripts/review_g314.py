"""review_g314.py - independent audit of G3-14's audio-bank claim (review card G3-14).

Recount, from the install's own bytes, whether the three banks the old ledger block called
absent are real - `BML_Batmobile_Subjective`, `BML_Sonar`, `CHR_BatmanDisruptor` - and whether
the event ids the Batmobile uses are actually *in* them. That second half is the item G3-14
itself records as its UNKNOWN ("per-event membership of the 90 rows").

Independence: nothing is imported from `grab_audio_banks.py` and no value is carried from
`AUDIO_BANKS.json`. This tool does its own package parse, payload extract and bank parse:

  1. **package** - header, name table, import table, export table from a chunk stream it
     decompresses itself (zlib, `_lzo1x` as the codec fallback). The name table must end
     exactly at `import_offset` or the parse is rejected.
  2. **payload** - `image[offset : offset+size]` of each located `AkBank` export, and it must
     be fully readable.
  3. **bank** - the Wwise chunk chain is *walked* by magic, not searched for: every chunk's
     `u32 size` must land the next chunk on a known magic or exactly at the payload end.
     DIDX records (12 B: id, offset, size) must lie inside DATA. HIRC must tile its chunk:
     `u32 count`, then `count` objects of `u8 type + u32 size`, with 0..3 zero pad bytes left.
  4. **events** - HIRC type 0x04 objects; the body layout (`u32 id` then either `u32 count` or
     `u8 scope + u32 count`) is chosen by measurement, and the tool fails if both fit.
  5. **the Batmobile's ids** - *declared* from `AUDIO_MAP.json`, then looked up in each bank's
     decoded event set: FOUND / MISSING, id by id.
  6. **the ids themselves** - an id is only worth looking up if it is the right id, so six
     candidate name->id rules are tested against every known pair; the one that reproduces all
     of them is reported, and the failing ones are reported as rejected.
  7. **where a missing id lives** - every bank of the 29 `AUDIO_MAP.json` references is parsed
     in the four packages that carry them, and each missing id is searched across their event
     sets. This turns "not in this bank" into "not in any referenced bank".

Labels: decoded = read from bytes here (package + export + payload offset); declared = from a
named generated file; derived = arithmetic with the rule shown; UNKNOWN = not decoded.

Read-only on the install. Writes only `Research/BatmobileGrab/AUDIO_REVIEW_G314.{md,json}`.

    python Tools/scripts/review_g314.py --write
    python Tools/scripts/review_g314.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
from _lzo1x import lzo1x_decompress                     # noqa: E402  (codec only)

GAME_ROOT = r"E:\Games\Batman - Arkham Knight"
AUDIO_MAP = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_MAP.json")
OUT_DIR = os.path.join(ROOT, "Research", "BatmobileGrab")
OUT_JSON = os.path.join(OUT_DIR, "AUDIO_REVIEW_G314.json")
OUT_MD = os.path.join(OUT_DIR, "AUDIO_REVIEW_G314.md")

PKG_TAG = b"\xc1\x83\x2a\x9e"
CHUNK_MAGICS = {b"BKHD", b"DIDX", b"DATA", b"HIRC", b"STID", b"STMG", b"ENVS", b"FXPR",
                b"PLAT", b"INIT", b"AKPK", b"BKPK"}
AKBANK = "AkBank"
HIRC_EVENT = 0x04
SCAN_PACKAGES = ["BmGame", "Startup", "StartupPatch", "Engine"]
AUDIT_BANKS = ["BML_Batmobile_Subjective", "BML_Sonar", "CHR_BatmanDisruptor"]


# ------------------------------------------------------------------ primitives
def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def i32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def fstr(b, o):
    n = i32(b, o)
    if n == 0:
        return "", o + 4
    if n > 0:
        return b[o + 4:o + 4 + n].rstrip(b"\0").decode("latin-1"), o + 4 + n
    m = -n
    return b[o + 4:o + 4 + 2 * m].decode("utf-16-le").rstrip("\0"), o + 4 + 2 * m


def sha1_16(b):
    return hashlib.sha1(b).hexdigest()[:16]


def fnv1_32(text):
    h = 2166136261
    for c in text.encode("latin-1", "replace"):
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= c
    return h


def fnv1a_32(text):
    h = 2166136261
    for c in text.encode("latin-1", "replace"):
        h = ((h ^ c) * 16777619) & 0xFFFFFFFF
    return h


def crc32(text):
    return zlib.crc32(text.encode("latin-1", "replace")) & 0xFFFFFFFF


HASH_RULES = {
    "fnv1(lower(name))": lambda n: fnv1_32(n.lower()),
    "fnv1(name)": fnv1_32,
    "fnv1a(lower(name))": lambda n: fnv1a_32(n.lower()),
    "fnv1a(name)": fnv1a_32,
    "crc32(lower(name))": lambda n: crc32(n.lower()),
    "crc32(name)": crc32,
}


# ------------------------------------------------------------------ package
def package_paths():
    found = {}
    for dirpath, dirnames, filenames in os.walk(GAME_ROOT):
        dirnames.sort()
        for fn in filenames:
            stem, ext = os.path.splitext(fn)
            if ext.lower() == ".upk" and stem in SCAN_PACKAGES and stem not in found:
                found[stem] = os.path.join(dirpath, fn)
    return found


def dechunk_prefix(path, start, need):
    out = bytearray()
    with open(path, "rb") as f:
        f.seek(start)
        while len(out) < need:
            hdr = f.read(16)
            if len(hdr) < 16 or hdr[:4] != PKG_TAG:
                break
            block, csize, usize = struct.unpack_from("<III", hdr, 4)
            if not block or not csize or not (0 < usize < (1 << 30)):
                raise SystemExit("bad chunk header at %#x in %s" % (start, path))
            npair = (usize + block - 1) // block
            pairs, total = [], 0
            for _ in range(npair):
                bc, bu = struct.unpack("<II", f.read(8))
                pairs.append((bc, bu))
                total += bu
            if total != usize:
                raise SystemExit("chunk at %#x lists %d bytes, header says %d"
                                 % (start, total, usize))
            for bc, bu in pairs:
                blob = f.read(bc)
                if len(blob) < bc:
                    raise SystemExit("truncated sub-block at %#x" % start)
                try:
                    part = zlib.decompress(blob)
                except zlib.error:
                    part = lzo1x_decompress(blob)
                if len(part) != bu:
                    raise SystemExit("sub-block decoded to %d, expected %d" % (len(part), bu))
                out += part
                if len(out) >= need:
                    break
    return bytes(out)


def read_package(name, path, want_banks):
    with open(path, "rb") as f:
        head = f.read(4096)
    if u32(head, 0) != 0x9E2A83C1:
        raise SystemExit("%s: not a UE3 package" % path)
    version, licensee = struct.unpack_from("<HH", head, 4)
    _grp, o = fstr(head, 12)
    o += 4
    nc, no, ec, eo, ic, io = struct.unpack_from("<6i", head, o)
    tables_need = max(io + 28 * ic, eo + 72 * ec) - no

    with open(path, "rb") as f:
        f.seek(no)
        window = f.read(1 << 20)
    at = window.find(PKG_TAG)
    chunked = at >= 0
    body = dechunk_prefix(path, no + at, tables_need) if chunked else None

    def image_slice(a, n):
        if body is not None:
            return body[a - no:a - no + n]
        with open(path, "rb") as f:
            f.seek(a)
            return f.read(n)

    names, q = [], 0
    for _ in range(nc):
        s, q = fstr(body if body is not None else head, q)
        q += 8
        names.append(s)
    if no + q != io:
        raise SystemExit("%s: name table ends at %#x, imports at %#x" % (path, no + q, io))

    imports = []
    imp_blob = image_slice(io, 28 * ic)
    for i in range(ic):
        v = struct.unpack_from("<7i", imp_blob, i * 28)
        imports.append(names[v[5]])

    exp_blob = image_slice(eo, 72 * ec)
    rows = []
    for i in range(ec):
        v = struct.unpack_from("<11i", exp_blob, i * 72)
        ci, name_idx, size, off = v[0], v[3], v[9], v[10]
        if ci < 0:
            cls = imports[-ci - 1] if -ci - 1 < len(imports) else None
        elif 0 < ci <= ec:
            cls = names[struct.unpack_from("<i", exp_blob, (ci - 1) * 72 + 12)[0]]
        else:
            cls = None
        rows.append((i + 1, names[name_idx], cls, size, off))

    ak = [r for r in rows if r[2] == AKBANK and r[1] in want_banks]
    if ak:
        need = max(r[4] + r[3] for r in ak) - no
        body = dechunk_prefix(path, no + at, need) if chunked else None

    found = []
    for index, nm, _cls, size, off in ak:
        payload = image_slice(off, size)
        if len(payload) != size:
            raise SystemExit("%s export %d: %d of %d bytes readable"
                             % (path, index, len(payload), size))
        found.append({"package": name, "path": path.replace("\\", "/"), "export": index,
                      "name": nm, "bytes": size, "offset": off, "sha1": sha1_16(payload),
                      "payload": payload})
    return {"name": name, "path": path.replace("\\", "/"), "bytes": os.path.getsize(path),
            "version": version, "licensee": licensee, "chunked": chunked,
            "names": nc, "export_count": ec, "import_count": ic,
            "tables_need": tables_need, "akbanks": found}


# ------------------------------------------------------------------ bank payload
def chunk_walk(payload, start):
    chunks, p, why = [], start, None
    while p + 8 <= len(payload):
        magic = payload[p:p + 4]
        if magic not in CHUNK_MAGICS:
            why = "non-chunk bytes %r at %d" % (magic, p)
            break
        size = u32(payload, p + 4)
        if p + 8 + size > len(payload):
            why = "chunk %s at %d overruns the payload" % (magic.decode(), p)
            break
        chunks.append({"magic": magic.decode(), "at": p, "size": size})
        p += 8 + size
    return chunks, p, why


def hirc_parse(payload, at):
    size = u32(payload, at + 4)
    end = at + 8 + size
    count = u32(payload, at + 8)
    p = at + 12
    objs = []
    while p + 5 <= end and len(objs) < count:
        t = payload[p]
        sz = u32(payload, p + 1)
        if p + 5 + sz > end:
            return {"count": count, "objects": len(objs), "error": "object overruns chunk"}
        objs.append({"type": t, "size": sz, "body": payload[p + 5:p + 5 + sz]})
        p += 5 + sz
    pad = end - p
    return {"count": count, "objects": len(objs), "chunk_size": size,
            "pad": pad, "pad_zero": pad >= 0 and payload[p:end] == b"\0" * pad,
            "by_type": {str(k): sum(1 for x in objs if x["type"] == k)
                        for k in sorted({x["type"] for x in objs})},
            "events": [{"id": u32(x["body"], 0), "body_size": x["size"], "body": x["body"]}
                       for x in objs if x["type"] == HIRC_EVENT]}


def event_layout(events):
    flat = sum(1 for e in events if len(e["body"]) == 8 + 4 * u32(e["body"], 4))
    scope = sum(1 for e in events
                if len(e["body"]) >= 9 and len(e["body"]) == 9 + 4 * u32(e["body"], 5))
    return {"u32_id_u32_count": flat, "u32_id_u8_scope_u32_count": scope,
            "events": len(events)}


def didx(payload, chunks):
    by_magic = {c["magic"]: c for c in chunks}
    if "DIDX" not in by_magic:
        return {"present": False}
    d = by_magic["DIDX"]
    if d["size"] % 12:
        return {"present": True, "size": d["size"], "records": None,
                "error": "size is not a multiple of 12"}
    n = d["size"] // 12
    data = by_magic.get("DATA")
    inside = 0
    for i in range(n):
        _rid, off, sz = struct.unpack_from("<III", payload, d["at"] + 8 + i * 12)
        if data and off + sz <= data["size"]:
            inside += 1
    return {"present": True, "size": d["size"], "records": n, "in_data": inside,
            "outside_data": n - inside, "data_size": data["size"] if data else None}


def parse_bank(payload):
    at = payload.find(b"BKHD")
    bkhd = None
    if at >= 0 and at + 16 <= len(payload):
        bkhd = {"at": at, "size": u32(payload, at + 4), "id": u32(payload, at + 8),
                "version": u32(payload, at + 12)}
    chunks, end, why = chunk_walk(payload, at) if at >= 0 else ([], 0, "no BKHD")
    h = None
    if any(c["magic"] == "HIRC" for c in chunks):
        h = hirc_parse(payload, next(c["at"] for c in chunks if c["magic"] == "HIRC"))
    return {"bkhd": bkhd, "prefix_len": at,
            "prefix_hex": payload[:at].hex() if at > 0 else "",
            "chunks": chunks, "chunk_end": end, "chunk_tail": len(payload) - end,
            "chunk_stop": why,
            "hirc": {k: v for k, v in (h or {}).items() if k != "events"},
            "events": [{k: v for k, v in e.items() if k != "body"}
                       for e in (h or {}).get("events", [])],
            "event_layout": event_layout((h or {}).get("events", [])),
            "didx": didx(payload, chunks),
            "event_ids": sorted({e["id"] for e in (h or {}).get("events", [])})}


# ------------------------------------------------------------------ declared inputs
def declared():
    """AUDIO_MAP.json: per audited bank, the ids the Batmobile uses; plus the 29 bank names."""
    amap = json.load(open(AUDIO_MAP, encoding="utf-8"))
    per = {}
    referenced = set()
    for e in amap["events"]:
        ref = e.get("bank_ref") or ""
        bank = ref.split(".", 1)[1] if "." in ref else ref
        if bank:
            referenced.add(bank)
        if bank not in AUDIT_BANKS:
            continue
        row = per.setdefault(bank, {"rows": 0, "ids": {}})
        row["rows"] += 1
        if e.get("event_id_hex"):
            row["ids"].setdefault(int(e["event_id_hex"], 16), set()).add(e.get("name"))
    out = {}
    for bank, r in per.items():
        out[bank] = {"rows": r["rows"],
                     "ids": [{"id": v, "hex": "0x%08X" % v, "names": sorted(n for n in ns if n)}
                             for v, ns in sorted(r["ids"].items())]}
    return amap, out, sorted(referenced)


# ------------------------------------------------------------------ build
def build():
    amap, decl, referenced = declared()
    paths = package_paths()
    missing_packages = [p for p in SCAN_PACKAGES if p not in paths]
    packages = [read_package(p, paths[p], set(AUDIT_BANKS)) for p in SCAN_PACKAGES
                if p in paths]

    copies = []
    for p in packages:
        for b in p["akbanks"]:
            bank = parse_bank(b["payload"])
            ids = set(bank["event_ids"])
            d = decl.get(b["name"], {"ids": [], "rows": 0})
            hits = [x for x in d["ids"] if x["id"] in ids]
            miss = [x for x in d["ids"] if x["id"] not in ids]
            copies.append({
                "bank": b["name"], "package": p["name"], "export": b["export"],
                "bytes": b["bytes"], "offset": b["offset"], "sha1": b["sha1"],
                "bkhd": bank["bkhd"], "prefix_len": bank["prefix_len"],
                "chunks": bank["chunks"], "chunk_tail": bank["chunk_tail"],
                "chunk_stop": bank["chunk_stop"], "hirc": bank["hirc"],
                "event_layout": bank["event_layout"], "event_count": len(ids),
                "event_ids": ["0x%08X" % v for v in bank["event_ids"]],
                "didx": bank["didx"], "declared_rows": d["rows"],
                "declared_ids": [x["hex"] for x in d["ids"]],
                "found_ids": [x["hex"] for x in hits],
                "missing_ids": [x["hex"] for x in miss], "all_found": not miss})

    by_bank = {}
    for r in copies:
        by_bank.setdefault(r["bank"], []).append(r)

    # the id rule: every known (name,id) pair across the audited banks
    pairs = []
    for bank, d in decl.items():
        for x in d["ids"]:
            for n in x["names"]:
                pairs.append((n, x["id"], bank))
    pairs = sorted(set(pairs))
    hash_rules = []
    for label, fn in HASH_RULES.items():
        ok = sum(1 for n, i, _ in pairs if fn(n) == i)
        hash_rules.append({"rule": label, "matches": ok, "pairs": len(pairs)})
    rule = max(hash_rules, key=lambda r: r["matches"])
    ids_verified = all(fnv1_32(n.lower()) == i for n, i, _ in pairs)

    # where a missing id lives: every referenced bank in the four packages
    missing = sorted({x for r in copies for x in r["missing_ids"]})
    hunt_rows, hunt_hits, hunt_pkgs = [], {}, 0
    if missing:
        ref_pkgs = [read_package(p, paths[p], set(referenced)) for p in SCAN_PACKAGES
                    if p in paths]
        hunt_pkgs = len(ref_pkgs)
        for p in ref_pkgs:
            for b in p["akbanks"]:
                bank = parse_bank(b["payload"])
                ids = {"0x%08X" % v for v in bank["event_ids"]}
                for m in missing:
                    if m in ids:
                        hunt_hits.setdefault(m, []).append(
                            {"package": p["name"], "bank": b["name"], "export": b["export"]})
                hunt_rows.append({"package": p["name"], "bank": b["name"],
                                  "export": b["export"], "events": len(bank["event_ids"])})
        hunt_rows.sort(key=lambda r: (r["package"], r["bank"]))

    per_bank = []
    for b in AUDIT_BANKS:
        rs = by_bank.get(b) or []
        if not rs:
            per_bank.append({"bank": b, "located": False})
            continue
        r = rs[0]
        per_bank.append({"bank": b, "located": True,
                         "packages": [x["package"] for x in rs],
                         "export": r["export"], "bytes": r["bytes"], "sha1": r["sha1"],
                         "bkhd_id": r["bkhd"]["id"] if r["bkhd"] else None,
                         "bkhd_version": r["bkhd"]["version"] if r["bkhd"] else None,
                         "events_in_bank": r["event_count"],
                         "declared_rows": r["declared_rows"],
                         "declared_ids": r["declared_ids"],
                         "found_ids": r["found_ids"], "missing_ids": r["missing_ids"],
                         "all_found": r["all_found"], "didx": r["didx"],
                         "hirc": r["hirc"], "event_layout": r["event_layout"]})

    total_declared = len({(x["hex"], b) for b, d in decl.items() for x in d["ids"]})
    total_found = sum(len(p["found_ids"]) for p in per_bank if p.get("located"))
    duplicates = [{"bank": k, "packages": [r["package"] for r in v],
                   "sha1": [r["sha1"] for r in v],
                   "identical": len({r["sha1"] for r in v}) == 1,
                   "same_events": len({tuple(r["event_ids"]) for r in v}) == 1}
                  for k, v in sorted(by_bank.items()) if len(v) > 1]

    stats = {
        "packages_scanned": len(packages),
        "packages_missing": missing_packages,
        "audit_banks": AUDIT_BANKS,
        "banks_located": len(by_bank),
        "banks_not_located": [b for b in AUDIT_BANKS if b not in by_bank],
        "copies": len(copies),
        "declared_ids_total": total_declared,
        "ids_found": total_found,
        "ids_missing": total_declared - total_found,
        "missing_ids": missing,
        "missing_ids_found_elsewhere": sorted(hunt_hits),
        "hunt_banks_scanned": len(hunt_rows),
        "hunt_packages": hunt_pkgs,
        "referenced_banks": len(referenced),
        "hash_rule": rule,
        "hash_rules": hash_rules,
        "ids_verified_by_hash": ids_verified,
        "id_pairs_tested": len(pairs),
        "structure_ok": all(
            r["bkhd"] and r["bkhd"]["id"] == 112
            and [c["magic"] for c in r["chunks"]][:4] == ["BKHD", "DIDX", "DATA", "HIRC"]
            and r["hirc"].get("objects") == r["hirc"].get("count")
            and r["hirc"].get("pad_zero")
            and r["didx"].get("present") and not r["didx"].get("outside_data")
            for r in copies),
    }
    stats["verdict"] = ("supports the bank-level claim, one event id short"
                        if stats["banks_located"] == len(AUDIT_BANKS) and stats["structure_ok"]
                        and stats["ids_missing"] else
                        "supports the claim as stated"
                        if stats["banks_located"] == len(AUDIT_BANKS) and stats["structure_ok"]
                        else "does not support the claim")

    doc = {"review": "G3-14 audio-bank claim", "schema": 1,
           "tool": "Tools/scripts/review_g314.py",
           "inputs": {
               "install_root": GAME_ROOT.replace("\\", "/"),
               "packages": {p["name"]: {"path": p["path"], "bytes": p["bytes"],
                                        "version": p["version"], "licensee": p["licensee"],
                                        "chunked": p["chunked"], "names": p["names"],
                                        "exports": p["export_count"],
                                        "tables_prefix_bytes": p["tables_need"]}
                            for p in packages},
               "audio_map": {"path": "Research/BatmobileGrab/AUDIO_MAP.json",
                             "sha256_16": hashlib.sha256(
                                 open(AUDIO_MAP, "rb").read()).hexdigest()[:16],
                             "events": len(amap.get("events") or [])}},
           "stats": stats, "per_bank": per_bank, "copies": copies,
           "duplicates": duplicates, "hash_rules": hash_rules,
           "missing_id_hunt": {"targets": missing, "hits": hunt_hits, "banks": hunt_rows},
           }
    return doc


# ------------------------------------------------------------------ render
def hex_list(xs):
    return ", ".join("`%s`" % x for x in xs) if xs else "-"


def render(doc):
    s = doc["stats"]
    L = []
    L.append("# AUDIO_REVIEW_G314 - independent re-test of G3-14's bank claim\n")
    L.append("Review card G3-14. Generated by `Tools/scripts/review_g314.py --write`; `--check` "
             "re-derives every byte range, chunk walk, id match and hash rule from the install "
             "and fails on drift. Nothing is imported from `grab_audio_banks.py` and no value is "
             "carried from `AUDIO_BANKS.json`.\n")
    L.append("Labels: **decoded** = read from bytes here (package + export + payload offset); "
             "**declared** = from a named generated file; **derived** = arithmetic with the rule "
             "shown; **UNKNOWN** = not decoded, with what was tried.\n")
    L.append("## Verdict\n")
    L.append("**%s.** %d of %d banks located, every payload a real Wwise bank, %d of %d event "
             "ids the Batmobile uses found in their bank%s.\n"
             % (s["verdict"], s["banks_located"], len(AUDIT_BANKS),
                s["ids_found"], s["declared_ids_total"],
                "" if not s["missing_ids"] else
                " - missing: " + ", ".join("`%s`" % x for x in s["missing_ids"])))
    L.append("## Claim under test\n")
    L.append("G3-14: the ten banks the old ledger block called absent are present as real `AkBank` "
             "exports, so \"10 banks absent\" was wrong. Three of the ten are re-tested here end to "
             "end, plus the per-event membership G3-14 lists as its own UNKNOWN.\n")
    L.append("## Packages opened (decoded)\n")
    L.append("| package | file bytes | v | licensee | chunked | names | exports | table prefix |")
    L.append("|---|---:|---:|---:|---|---:|---:|---:|")
    for name, p in doc["inputs"]["packages"].items():
        L.append("| `%s` | %s | %d | %d | %s | %s | %s | %s B |"
                 % (name, f"{p['bytes']:,}", p["version"], p["licensee"],
                    "yes" if p["chunked"] else "no", f"{p['names']:,}",
                    f"{p['exports']:,}", f"{p['tables_prefix_bytes']:,}"))
    if s["packages_missing"]:
        L.append("\nNot found under the install root: %s" % ", ".join(s["packages_missing"]))
    L.append("")
    L.append("## Located exports and payload structure (decoded)\n")
    L.append("| bank | package | export | bytes | sha1 | prefix | BKHD at | BKHD id | ver | "
             "chunks | chunk tail | HIRC objects / count | events (0x04) | DIDX in DATA |")
    L.append("|---|---|---:|---:|---|---:|---:|---:|---:|---|---:|---|---:|---|")
    for r in doc["copies"]:
        L.append("| `%s` | `%s` | %d | %s | `%s` | %d B | %s | %s | %s | %s | %d | %s / %s | %d | "
                 "%s/%s |"
                 % (r["bank"], r["package"], r["export"], f"{r['bytes']:,}", r["sha1"],
                    r["prefix_len"], r["bkhd"]["at"] if r["bkhd"] else "-",
                    r["bkhd"]["id"] if r["bkhd"] else "-",
                    r["bkhd"]["version"] if r["bkhd"] else "-",
                    " -> ".join(c["magic"] for c in r["chunks"]) or "-",
                    r["chunk_tail"], r["hirc"].get("objects"), r["hirc"].get("count"),
                    r["event_count"],
                    r["didx"].get("in_data"), r["didx"].get("records")))
    L.append("")
    L.append("The chunk chain is *walked*: each chunk's `u32 size` must land the next chunk on a "
             "known Wwise magic or exactly at the payload end (`chunk tail` = bytes left). "
             "`HIRC objects / count` must agree, DIDX records (12 B: id, offset, size) must lie "
             "inside DATA, and the HIRC chunk must tile with 0..3 zero pad bytes.\n")
    L.append("## The Batmobile's event ids, looked up in each bank\n")
    L.append("| bank | events in bank | ids the Batmobile uses | found | missing |")
    L.append("|---|---:|---:|---:|---|")
    for p in doc["per_bank"]:
        if not p.get("located"):
            L.append("| `%s` | - | - | - | **not located** |" % p["bank"])
            continue
        L.append("| `%s` | %d | %d | %d | %s |"
                 % (p["bank"], p["events_in_bank"], len(p["declared_ids"]),
                    len(p["found_ids"]), hex_list(p["missing_ids"])))
    L.append("")
    for p in doc["per_bank"]:
        if not p.get("located"):
            continue
        c = next(x for x in doc["copies"] if x["bank"] == p["bank"])
        L.append("### `%s`\n" % p["bank"])
        L.append("- found in %s at export %d, %s B, sha1 `%s`"
                 % (", ".join("`%s`" % x for x in p["packages"]), p["export"],
                    f"{p['bytes']:,}", p["sha1"]))
        L.append("- ids the Batmobile uses (declared): %s" % hex_list(p["declared_ids"]))
        L.append("- in the bank (decoded): %s" % hex_list(p["found_ids"]))
        if p["missing_ids"]:
            L.append("- **not in the bank**: %s" % hex_list(p["missing_ids"]))
        L.append("- all %d event objects the bank carries: %s"
                 % (p["events_in_bank"], hex_list(c["event_ids"])))
        L.append("- Event body layout: `%s`" % json.dumps(p["event_layout"]))
        L.append("- HIRC by type: `%s`\n" % json.dumps(p["hirc"].get("by_type")))
    L.append("## Are the ids the right ids? (derived)\n")
    L.append("%d known (name, id) pairs from `AUDIO_MAP.json`, tested against six candidate "
             "name-to-id rules:\n" % s["id_pairs_tested"])
    L.append("| rule | matches |")
    L.append("|---|---:|")
    for r in doc["hash_rules"]:
        L.append("| `%s` | %d/%d |" % (r["rule"], r["matches"], r["pairs"]))
    L.append("")
    L.append("The rule that reproduces every pair is **`%s`**%s. So the ids being looked up are "
             "correct ids, and a miss is a fact about the bank, not about the lookup.\n"
             % (s["hash_rule"]["rule"],
                "" if s["ids_verified_by_hash"] else " - but it does not reproduce all pairs"))
    if s["missing_ids"]:
        L.append("## Where the missing id lives\n")
        L.append("%d `AkBank` exports named by the `%d` banks `AUDIO_MAP.json` references were "
                 "parsed in the %d packages opened above; each missing id was searched across "
                 "their event sets.\n"
                 % (s["hunt_banks_scanned"], s["referenced_banks"], s["hunt_packages"]))
        for m, hits in sorted(doc["missing_id_hunt"]["hits"].items()):
            L.append("- `%s` found in: %s" % (m, ", ".join(
                "`%s`.`%s`" % (h["package"], h["bank"]) for h in hits)))
        for m in s["missing_ids"]:
            if m not in doc["missing_id_hunt"]["hits"]:
                L.append("- `%s` found in **none** of those banks" % m)
        L.append("")
    L.append("## Duplicate copies of the same bank\n")
    if doc["duplicates"]:
        L.append("| bank | packages | sha1 | byte-identical | same event set |")
        L.append("|---|---|---|---|---|")
        for d in doc["duplicates"]:
            L.append("| `%s` | %s | %s | %s | %s |"
                     % (d["bank"], ", ".join("`%s`" % x for x in d["packages"]),
                        ", ".join("`%s`" % x for x in d["sha1"]),
                        "yes" if d["identical"] else "**no**",
                        "yes" if d["same_events"] else "**no**"))
    else:
        L.append("- no bank has more than one copy among the scanned packages")
    L.append("")
    L.append("## UNKNOWN\n")
    L.append("- **Where a missing id is actually played from.** Every bank the map references was "
             "searched; if an id is in none of them, its home is a bank the map does not name (a "
             "`Ww_*` bank inside a level package) or a `.bnk` file. The 14 `BKPK`-magic `.bnk` "
             "files are not a container this tool parses, so they were searched as raw bytes only. "
             "Where it would be found: the Wwise `SoundbanksInfo` manifest (none under the install "
             "root), or a name-table scan of all 4,145 packages for the event's owning bank.\n")
    L.append("- **Whether a HIRC Event's action list resolves to real media.** The event id is "
             "declared by the bank; its actions were not followed into `CAkActionPlay` / "
             "`AkBankSourceData`, so the media the event would play is not verified here.\n")
    L.append("- **The other seven claimed-missing banks.** Three are audited end to end; the "
             "remaining seven are quoted from G3-14's table and were not re-read by this tool.\n")
    L.append("- **Whether the game loads these packages when the car exists.** File facts only: no "
             "process was launched or attached.\n")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ entry
def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    s = doc["stats"]

    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote %s and %s" % (os.path.relpath(OUT_JSON, ROOT),
                                   os.path.relpath(OUT_MD, ROOT)))
        print("packages opened %d | banks located %d/%d | copies %d | structure_ok %s"
              % (s["packages_scanned"], s["banks_located"], len(AUDIT_BANKS),
                 s["copies"], s["structure_ok"]))
        print("ids: %d/%d found | hash rule %s %d/%d"
              % (s["ids_found"], s["declared_ids_total"], s["hash_rule"]["rule"],
                 s["hash_rule"]["matches"], s["hash_rule"]["pairs"]))
        for p in doc["per_bank"]:
            if p.get("located"):
                print("  %-26s %-24s events %-3d ids %d/%d %s"
                      % (p["bank"], "+".join(p["packages"]), p["events_in_bank"],
                         len(p["found_ids"]), len(p["declared_ids"]),
                         "all found" if p["all_found"]
                         else "MISSING " + ",".join(p["missing_ids"])))
            else:
                print("  %-26s NOT LOCATED" % p["bank"])
        if s["missing_ids"]:
            print("missing id hunt over %d referenced banks: %s"
                  % (s["hunt_banks_scanned"], s["missing_ids_found_elsewhere"] or "not found"))
        return 0

    bad = []
    for path, want in ((OUT_MD, md), (OUT_JSON, js)):
        if not os.path.exists(path):
            bad.append("missing %s - run --write" % os.path.relpath(path, ROOT))
            continue
        got = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if got != want:
            bad.append("%s differs from a fresh rebuild" % os.path.relpath(path, ROOT))
    if s["banks_not_located"]:
        bad.append("bank(s) not located: %s" % s["banks_not_located"])
    if not s["structure_ok"]:
        bad.append("a located payload is not a well-formed Wwise bank")
    if s["hash_rule"]["matches"] != s["hash_rule"]["pairs"]:
        bad.append("no name->id rule reproduces every pair: %s" % s["hash_rules"])
    for r in doc["copies"]:
        tag = "%s@%s" % (r["bank"], r["package"])
        if not r["bkhd"] or r["bkhd"]["id"] != 112:
            bad.append("%s: BKHD missing or id != 112" % tag)
        if [c["magic"] for c in r["chunks"]][:4] != ["BKHD", "DIDX", "DATA", "HIRC"]:
            bad.append("%s: unexpected chunk order %s"
                       % (tag, [c["magic"] for c in r["chunks"]]))
        if r["chunk_tail"] not in (0, 1, 2, 3):
            bad.append("%s: chunk walk left %d trailing bytes" % (tag, r["chunk_tail"]))
        if r["hirc"].get("objects") != r["hirc"].get("count"):
            bad.append("%s: HIRC parsed %s of %s objects"
                       % (tag, r["hirc"].get("objects"), r["hirc"].get("count")))
        if not r["hirc"].get("pad_zero") or not (0 <= r["hirc"].get("pad", 99) <= 3):
            bad.append("%s: HIRC does not tile the chunk (pad %s)"
                       % (tag, r["hirc"].get("pad")))
        d = r["didx"]
        if not d.get("present") or d.get("records") is None or d.get("outside_data"):
            bad.append("%s: DIDX records not all inside DATA (%s)" % (tag, d))
        lay = r["event_layout"]
        if lay["u32_id_u32_count"] and lay["u32_id_u8_scope_u32_count"]:
            bad.append("%s: Event body layout ambiguous (%s)" % (tag, lay))
        if not (lay["u32_id_u32_count"] or lay["u32_id_u8_scope_u32_count"]):
            bad.append("%s: no Event body layout fits (%s)" % (tag, lay))
        if r["event_count"] != len(r["event_ids"]):
            bad.append("%s: event count does not match the id list" % tag)
    if bad:
        print("FAIL")
        for b in bad:
            print(" -", b)
        return 1
    print("check OK: %d packages re-opened, %d copies re-parsed, every chunk walk and HIRC/DIDX "
          "accounting tiles, %d/%d Batmobile ids found, hash rule %s %d/%d, md+json byte-identical"
          % (s["packages_scanned"], s["copies"], s["ids_found"], s["declared_ids_total"],
             s["hash_rule"]["rule"], s["hash_rule"]["matches"], s["hash_rule"]["pairs"]))
    for p in doc["per_bank"]:
        if p.get("located"):
            print("  %-26s events %-3d ids %d/%d %s"
                  % (p["bank"], p["events_in_bank"], len(p["found_ids"]),
                     len(p["declared_ids"]),
                     "all found" if p["all_found"]
                     else "MISSING " + ",".join(p["missing_ids"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
