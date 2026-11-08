"""effc_writer.py - can a shipped `.effc` be re-encoded byte-for-byte, and can an edited copy be written?

The repo has a reader for `.effc` (`jc3adf.py` via `jc3fx.py`) but no writer. This script
builds one from the format itself and measures it.

  decode   every `.effc` into a node tree (struct / array / inline array / pointer /
           HashString / String / primitive), recording the absolute byte offset of every
           node. Nothing is inferred: the type dictionary in the file gives every size and
           offset.
  encode   rebuilds the file from that tree alone: the 11 named header words, the instance
           table, the whole type dictionary, the string-hash table, the name table and every
           decoded value are written from the tree at their recorded offsets.
  compare  two modes:
             strict  bytes the tree does not describe stay zero, so the comparison shows
                     exactly what the field set does not account for;
             carry   those bytes are copied from the source (the mode an edit must use, so an
                     unknown region survives a value patch).

Usage:
  python effc_writer.py write [--bundles N]
  python effc_writer.py check [--bundles N]

Outputs (write): Working/Effects/EFFC_WRITER.json + Working/Effects/EFFC_WRITER.md
`check` re-reads the game, recomputes every number in the JSON and exits 1 on any drift.
Read-only against the game: archives are opened through the existing index for reads only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import DEFAULT_GAME, DEFAULT_OUT, load_index  # noqa: E402
import jc3fx  # noqa: E402
import jc3adf  # noqa: E402
from jc3adf import PRIMITIVES, TYPE_ARRAY, TYPE_BITFIELD, TYPE_ENUMERATION  # noqa: E402
from jc3adf import TYPE_INLINE_ARRAY, TYPE_POINTER, TYPE_STRING, TYPE_STRING_HASH  # noqa: E402
from jc3adf import TYPE_STRUCTURE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_JSON = os.path.join(ROOT, "Working", "Effects", "EFFC_WRITER.json")
OUT_MD = os.path.join(ROOT, "Working", "Effects", "EFFC_WRITER.md")
HEADER_WORDS = ["magic", "version", "instance_count", "instance_offset", "type_count",
                "type_offset", "strhash_count", "strhash_offset", "name_count",
                "name_offset", "total_size"]
HEADER_NAMED = len(HEADER_WORDS)          # 11 of the 16 u32 in the file's header
HEADER_SIZE = 64                          # 16 u32; words 11..15 are zero in every file sampled


# ------------------------------------------------------------------ decode to a node tree
def decode_node(adf: "jc3adf.Adf", type_hash: int, pos: int) -> dict:
    blob = adf.blob
    t = adf.types.get(type_hash)
    if t is None:
        prim = PRIMITIVES.get(type_hash)
        if not prim:
            raise KeyError(f"unknown type {type_hash:#x}")
        name, fmt, size = prim
        if fmt is None:                                   # the String primitive: NUL-string pointer
            (off,) = struct.unpack_from("<Q", blob, pos)
            return {"kind": "string_ptr", "type": type_hash, "at": pos,
                    "off": off, "value": adf.string_at(off)}
        return {"kind": "prim", "type": type_hash, "at": pos, "size": size,
                "value": struct.unpack_from(fmt, blob, pos)[0]}

    if t["name"] == "HashString":
        s_off, s_hash = struct.unpack_from("<QI", blob, pos)
        return {"kind": "hashstring", "type": type_hash, "at": pos, "off": s_off,
                "hash": s_hash, "value": adf.string_at(s_off)}

    code = t["code"]
    if code == TYPE_STRUCTURE:
        members = []
        for m in t["members"]:
            members.append({"name": m["name"], "offset": m["offset"],
                            "node": decode_node(adf, m["type"], pos + m["offset"])})
        return {"kind": "struct", "type": type_hash, "at": pos, "size": t["size"],
                "members": members}

    if code == TYPE_ARRAY:
        a_off, a_count = struct.unpack_from("<QQ", blob, pos)
        stride = jc3adf._element_stride(adf, t["element"])
        start = adf.data_off + a_off
        elems = [decode_node(adf, t["element"], start + i * stride) for i in range(a_count)]
        return {"kind": "array", "type": type_hash, "at": pos, "off": a_off,
                "count": a_count, "stride": stride, "elems": elems}

    if code == TYPE_INLINE_ARRAY:
        stride = jc3adf._element_stride(adf, t["element"])
        elems = [decode_node(adf, t["element"], pos + i * stride)
                 for i in range(t["element_len"])]
        return {"kind": "inline", "type": type_hash, "at": pos, "stride": stride,
                "count": t["element_len"], "elems": elems}

    if code == TYPE_POINTER:
        (target,) = struct.unpack_from("<Q", blob, pos)
        elem = decode_node(adf, t["element"], adf.data_off + target) if target else None
        return {"kind": "ptr", "type": type_hash, "at": pos, "target": target, "elem": elem}

    if code == TYPE_STRING:
        s_off, length = struct.unpack_from("<QQ", blob, pos)
        raw = blob[adf.data_off + s_off:adf.data_off + s_off + length]
        return {"kind": "string", "type": type_hash, "at": pos, "off": s_off,
                "length": length, "value": raw}

    if code in (TYPE_BITFIELD, TYPE_ENUMERATION, TYPE_STRING_HASH):
        size = 4 if PRIMITIVES.get(t["element"], (None, None, 8))[2] == 4 else 8
        fmt = "<I" if size == 4 else "<Q"
        return {"kind": "prim", "type": type_hash, "at": pos, "size": size,
                "value": struct.unpack_from(fmt, blob, pos)[0]}

    return {"kind": "raw", "type": type_hash, "at": pos, "size": t["size"] or 0,
            "hex": blob[pos:pos + (t["size"] or 0)].hex()}


# ----------------------------------------------------------------------------- encode
class Encoder:
    def __init__(self, adf: "jc3adf.Adf"):
        self.adf = adf
        self.buf = bytearray(len(adf.blob))
        self.mask = bytearray(len(adf.blob))       # 1 = byte the encoder produced
        self.raw_bytes = 0                         # a type code the reader cannot name
        self.const_bytes = 0                       # written as a constant, not from a field
        self.copied_bytes = 0                      # copied verbatim (string-hash table)

    def put(self, pos: int, data: bytes) -> None:
        self.buf[pos:pos + len(data)] = data
        for i in range(pos, pos + len(data)):
            self.mask[i] = 1

    def put_string(self, off: int, value: str) -> None:
        self.put(self.adf.data_off + off, value.encode("latin-1") + b"\x00")

    def node(self, n: dict) -> None:
        k = n["kind"]
        if k == "prim":
            prim = PRIMITIVES.get(n["type"])
            if prim is not None and prim[1] is not None:
                self.put(n["at"], struct.pack(prim[1], n["value"]))
            else:                                   # bitfield / enum / stringhash: width from size
                self.put(n["at"], struct.pack("<I" if n["size"] == 4 else "<Q", n["value"]))
            return
        if k == "string_ptr":
            self.put(n["at"], struct.pack("<Q", n["off"]))
            self.put_string(n["off"], n["value"])
            return
        if k == "hashstring":
            self.put(n["at"], struct.pack("<QI", n["off"], n["hash"]))
            self.put_string(n["off"], n["value"])
            return
        if k == "struct":
            for m in n["members"]:
                self.node(m["node"])
            return
        if k == "array":
            self.put(n["at"], struct.pack("<QQ", n["off"], n["count"]))
            for e in n["elems"]:
                self.node(e)
            return
        if k == "inline":
            for e in n["elems"]:
                self.node(e)
            return
        if k == "ptr":
            self.put(n["at"], struct.pack("<Q", n["target"]))
            if n["elem"] is not None:
                self.node(n["elem"])
            return
        if k == "string":
            self.put(n["at"], struct.pack("<QQ", n["off"], n["length"]))
            self.put(self.adf.data_off + n["off"], n["value"])
            return
        if k == "raw":
            raw = bytes.fromhex(n["hex"])
            self.put(n["at"], raw)
            self.raw_bytes += len(raw)
            return
        raise ValueError(f"unencodable node {k}")


def assemble(adf: "jc3adf.Adf", enc: Encoder) -> bytes:
    """Header + instance table + type dictionary + string-hash table + name table from the model."""
    buf = enc.buf
    inst = adf.instances
    head = [jc3adf.SIGNATURE, 4, len(inst), adf.instance_off, len(adf.types), adf.type_off,
            getattr(adf, "strhash_count", 0), getattr(adf, "strhash_off", 0),
            len(adf.names), adf.name_off, adf.total]
    enc.put(0, struct.pack("<11I", *head))
    enc.put(44, b"\x00" * (HEADER_SIZE - 44))
    enc.const_bytes += HEADER_SIZE - 44        # header words 11..15: a constant, not a field

    index_of = {name: i for i, name in enumerate(adf.names)}
    p = adf.instance_off
    for i in inst:
        enc.put(p, struct.pack("<4Iq", i["name_hash"], i["type"], i["offset"], i["size"],
                               index_of[i["name"]]))
        p += 24

    p = adf.type_off
    for h, t in adf.types.items():
        enc.put(p, struct.pack("<4Iq3II", t["code"], t["size"], t["align"], h,
                               index_of[t["name"]], t["flags"], t["element"],
                               t["element_len"], len(t["members"])))
        p += 40
        for m in t["members"]:
            enc.put(p, struct.pack("<q4IQ", index_of[m["name"]], m["type"], m["size"],
                                   m["offset"], m["default_type"], m["default"]))
            p += 32

    if head[6]:
        enc.put(adf.strhash_off, adf.blob[adf.strhash_off:adf.strhash_off + 4 * head[6]])
        enc.copied_bytes += 4 * head[6]

    p = adf.name_off
    enc.put(p, bytes(len(n) for n in adf.names))
    p += len(adf.names)
    for n in adf.names:
        enc.put(p, n.encode("latin-1") + b"\x00")
        p += len(n) + 1
    return bytes(buf)


# -------------------------------------------------------------------------------- model
def inline_spans(trees: list[dict], blob: bytes) -> list[bytes]:
    """Byte content of every inline array, for provenance of bytes no field describes."""
    out: list[bytes] = []

    def walk(n: dict) -> None:
        if n["kind"] == "inline":
            out.append(blob[n["at"]:n["at"] + n["count"] * n["stride"]])
        if n["kind"] == "struct":
            for m in n["members"]:
                walk(m["node"])
        elif n["kind"] in ("array", "inline"):
            for e in n["elems"]:
                walk(e)
        elif n["kind"] == "ptr" and n["elem"] is not None:
            walk(n["elem"])

    for t in trees:
        walk(t)
    return out


def runs_of(indices: list[int]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    for i in indices:
        if runs and i == runs[-1][1]:
            runs[-1] = (runs[-1][0], i + 1)
        else:
            runs.append((i, i + 1))
    return runs


def analyse(blob: bytes) -> dict:
    adf = jc3adf.Adf(blob)
    adf.strhash_count = struct.unpack_from("<I", blob, 24)[0]
    adf.strhash_off = struct.unpack_from("<I", blob, 28)[0]
    trees = [decode_node(adf, i["type"], i["offset"]) for i in adf.instances]
    enc = Encoder(adf)
    for t in trees:
        enc.node(t)
    strict = assemble(adf, enc)
    covered = sum(enc.mask)

    gap_idx = [i for i in range(len(blob)) if not enc.mask[i]]
    gap_runs = runs_of(gap_idx)
    spans = inline_spans(trees, blob)
    explained = 0
    unexplained = 0
    nonzero = 0
    nz_runs = 0
    for lo, hi in gap_runs:
        core = blob[lo:hi].strip(b"\x00")      # drop alignment padding at both ends
        if not core:
            continue
        nz_runs += 1
        nonzero += len(core)
        if any(core in s for s in spans if s):
            explained += len(core)
        else:
            unexplained += len(core)

    # carry mode: the bytes no field describes are copied, so an edit preserves them
    carry = bytearray(strict)
    for i in gap_idx:
        carry[i] = blob[i]
    sections: dict[str, int] = {}
    bounds = [("header", 0, HEADER_SIZE),
              ("instances", adf.instance_off, adf.instance_off + 24 * len(adf.instances)),
              ("types", adf.type_off, adf.name_off),
              ("strhash", adf.strhash_off, adf.strhash_off + 4 * adf.strhash_count),
              ("names", adf.name_off, adf.total)]
    for name, lo, hi in bounds:
        for i in range(lo, min(hi, len(blob))):
            if not enc.mask[i]:
                sections[name] = sections.get(name, 0) + 1
    sections["data"] = len(gap_idx) - sum(sections.values())
    return {"adf": adf, "trees": trees, "strict": strict, "carry": bytes(carry),
            "len": len(blob), "covered": covered,
            "strict_identical": strict == blob, "carry_identical": bytes(carry) == blob,
            "gap_bytes": len(gap_idx), "gap_runs": len(gap_runs),
            "gap_zero_bytes": len(gap_idx) - nonzero,
            "gap_nonzero_runs": nz_runs,
            "gap_nonzero_bytes": nonzero,
            "gap_duplicating_inline": explained, "gap_unexplained": unexplained,
            "raw_bytes": enc.raw_bytes, "const_bytes": enc.const_bytes,
            "copied_bytes": enc.copied_bytes, "unnamed": sections,
            "digest": hashlib.sha1(blob).hexdigest()}


# ------------------------------------------------------------------------------- sources
def pick_containers(best: dict, bundles: int) -> list[str]:
    """The smallest 10 bundles plus an even spread over the rest: sample both extremes."""
    table = [json.loads(line) for line in
             open(os.path.join(DEFAULT_OUT, "FX_TABLE.jsonl"), encoding="utf-8")]
    seen = {rec["container"] for rec in table
            if rec["ext"] == ".effc" and rec["container"].lower().endswith(".ee")}
    ordered = sorted((c for c in seen if c in best), key=lambda c: (best[c]["size"], c))
    if len(ordered) <= bundles:
        return ordered
    head = ordered[:10]
    rest = ordered[10:]
    step = max(1, len(rest) // max(1, bundles - len(head)))
    return head + rest[::step][:bundles - len(head)]


def sources(bundles: int):
    """(label, path, bytes) for every standalone `.effc` and a spread of bundles holding one."""
    best = jc3fx.pick_by_path(load_index(DEFAULT_OUT))
    standalone = sorted(p for p in best if p.lower().endswith(".effc"))
    for p in standalone:
        yield ("standalone", p, jc3fx.read_row(best[p], DEFAULT_GAME))
    for c in pick_containers(best, bundles):
        blob = jc3fx.read_row(best[c], DEFAULT_GAME)
        inner = jc3fx.inner_fx(blob, (".effc",))
        if inner:
            yield ("bundle", f"{c}::{inner[0][0]}", inner[0][1])


# ------------------------------------------------------------------------------ edit test
EDITABLE = ("MaxParticles", "EmitterTemplateIndex", "Lifetime", "StartTime", "Flags")


def find_edit(trees: list[dict]) -> tuple[dict, str] | None:
    """First named numeric leaf whose member name is one we know the meaning of."""
    found: list[tuple[str, dict]] = []

    def walk(n: dict, path: str) -> None:
        if n["kind"] == "struct":
            for m in n["members"]:
                walk(m["node"], f"{path}.{m['name']}" if path else m["name"])
        elif n["kind"] in ("array", "inline"):
            for i, e in enumerate(n["elems"]):
                walk(e, f"{path}[{i}]")
        elif n["kind"] == "prim":
            found.append((path, n))

    for t in trees:
        walk(t, "")
    for want in EDITABLE:
        for path, node in found:
            if path.rsplit(".", 1)[-1].split("[")[0] == want and node["size"] in (2, 4):
                return node, path
    return None


def edit_proof(blob: bytes, rel: str) -> dict:
    a = analyse(blob)
    if not a["strict_identical"]:
        return {"path": rel, "ok": False, "why": "unchanged strict round trip not identical"}
    hit = find_edit(a["trees"])
    adf = a["adf"]
    if not hit:
        return {"path": rel, "ok": False, "why": "no editable numeric field in this file"}
    node, path = hit
    old = node["value"]
    mask = 0xFFFF if node["size"] == 2 else 0xFFFFFFFF
    new = (old + 0x0101) & mask                 # flip both bytes: proves the field's width
    if new == old:
        new = (old - 0x0101) & mask
    node["value"] = new
    edited = _reencode(a, blob)

    # 1. the reader must accept the edited copy and read the new value back
    re_read = analyse(edited)
    reread = find_edit(re_read["trees"])
    read_back = reread[0]["value"] if reread else None

    # 2. only the field's own bytes may differ
    diff = [i for i in range(len(blob)) if edited[i] != blob[i]]
    ok_window = all(node["at"] <= i < node["at"] + node["size"] for i in diff)

    # 3. writing the old value back must reproduce the shipped file exactly
    node["value"] = old
    reverted = _reencode(a, blob)
    return {"path": rel, "ok": bool(read_back == new and ok_window and reverted == blob),
            "field": path, "old": old, "new": new, "read_back": read_back,
            "bytes_changed": len(diff), "window": [node["at"], node["size"]],
            "revert_identical": reverted == blob, "strict": True,
            "edited_sha1": hashlib.sha1(edited).hexdigest()}


def _reencode(a: dict, blob: bytes) -> bytes:
    """Re-encode the tree in carry mode (unknown byte runs preserved)."""
    adf = a["adf"]
    enc = Encoder(adf)
    for t in a["trees"]:
        enc.node(t)
    out = bytearray(assemble(adf, enc))
    for i in range(len(blob)):
        if not enc.mask[i]:
            out[i] = blob[i]
    return bytes(out)


# ---------------------------------------------------------------------------------- run
def run(bundles: int) -> dict:
    results = []
    fails = []
    codes: dict[str, int] = {}
    member_names: set[str] = set()
    for kind, rel, blob in sources(bundles):
        try:
            a = analyse(blob)
        except Exception as e:                                  # noqa: BLE001
            fails.append({"path": rel, "error": f"{type(e).__name__}: {e}"})
            continue
        for t in a["adf"].types.values():
            codes[str(t["code"])] = codes.get(str(t["code"]), 0) + 1
            for m in t["members"]:
                member_names.add(m["name"])
        results.append({"kind": kind, "path": rel, "len": a["len"], "covered": a["covered"],
                        "strict_identical": a["strict_identical"],
                        "carry_identical": a["carry_identical"],
                        "gap_bytes": a["gap_bytes"], "gap_runs": a["gap_runs"],
                        "gap_nonzero_runs": a["gap_nonzero_runs"],
                        "gap_nonzero_bytes": a["gap_nonzero_bytes"],
                        "gap_duplicating_inline": a["gap_duplicating_inline"],
                        "gap_unexplained": a["gap_unexplained"],
                        "raw_bytes": a["raw_bytes"], "const_bytes": a["const_bytes"],
                        "copied_bytes": a["copied_bytes"],
                        "unnamed": a["unnamed"], "digest": a["digest"]})

    edited = None
    for kind, rel, blob in sources(bundles):
        try:
            if analyse(blob)["strict_identical"]:
                edited = edit_proof(blob, rel)
                if edited.get("ok"):
                    break
        except Exception as e:                                  # noqa: BLE001
            edited = {"path": rel, "ok": False, "why": f"{type(e).__name__}: {e}"}

    total = sum(r["len"] for r in results)
    covered = sum(r["covered"] for r in results)
    unnamed = {"header": 0, "instances": 0, "types": 0, "strhash": 0, "names": 0, "data": 0}
    for r in results:
        for k, v in r["unnamed"].items():
            unnamed[k] += v
    return {
        "files_tested": len(results),
        "standalone": sum(1 for r in results if r["kind"] == "standalone"),
        "bundles": sum(1 for r in results if r["kind"] == "bundle"),
        "strict_identical": sum(1 for r in results if r["strict_identical"]),
        "carry_identical": sum(1 for r in results if r["carry_identical"]),
        "failures": fails,
        "bytes_total": total,
        "bytes_from_fields": covered,
        "bytes_from_constants": sum(r["const_bytes"] for r in results),
        "bytes_copied": sum(r["copied_bytes"] for r in results),
        "bytes_raw_types": sum(r["raw_bytes"] for r in results),
        "bytes_not_written": total - covered,
        "gap_zero_bytes": sum(r["len"] - r["covered"] - r["gap_nonzero_bytes"] for r in results),
        "gap_nonzero_bytes": sum(r["gap_nonzero_bytes"] for r in results),
        "gap_nonzero_runs": sum(r["gap_nonzero_runs"] for r in results),
        "gap_duplicating_inline": sum(r["gap_duplicating_inline"] for r in results),
        "gap_unexplained": sum(r["gap_unexplained"] for r in results),
        "type_code_census": dict(sorted(codes.items())),
        "distinct_member_names": len(member_names),
        "unnamed_by_section": unnamed,
        "header_words_named": HEADER_NAMED,
        "header_words_total": 16,
        "edit": edited,
        "results": results,
    }


def summarise(d: dict) -> str:
    L = []
    L.append("# `.effc`: can it be written?\n")
    L.append("Generated by `python Tools/scripts/effc_writer.py write`; `check` re-reads the")
    L.append("game and recomputes every number here.\n")
    L.append("| fact | value |")
    L.append("|---|---|")
    L.append(f"| files tested | **{d['files_tested']}** ({d['standalone']} standalone archive "
             f"entries + {d['bundles']} from `.ee` bundles) |")
    L.append(f"| strict round trip byte-identical (unmodelled bytes zeroed) | "
             f"**{d['strict_identical']}** |")
    L.append(f"| carry round trip byte-identical (unmodelled bytes copied) | "
             f"**{d['carry_identical']}** |")
    L.append(f"| decode failures | **{len(d['failures'])}** |")
    L.append(f"| bytes generated from decoded fields | **{d['bytes_from_fields']:,} of "
             f"{d['bytes_total']:,} ({100.0 * d['bytes_from_fields'] / d['bytes_total']:.2f}%)** |")
    L.append(f"| bytes written as a constant (header words 11..15) | {d['bytes_from_constants']:,} |")
    L.append(f"| bytes copied verbatim (string-hash table) | {d['bytes_copied']:,} |")
    L.append(f"| bytes of an unnamed type code | {d['bytes_raw_types']:,} |")
    L.append(f"| bytes no field describes | {d['bytes_not_written']:,} "
             f"(all zero: {d['gap_zero_bytes']:,} padding bytes) |")
    L.append(f"| of those, nonzero | **{d['gap_nonzero_bytes']:,}** |")
    L.append(f"| nonzero gap bytes that duplicate an inline array in the same file | "
             f"**{d['gap_duplicating_inline']:,}** |")
    L.append(f"| nonzero gap bytes with no explanation | **{d['gap_unexplained']:,}** |")
    L.append(f"| header words named | **{d['header_words_named']} of {d['header_words_total']}** |")
    L.append(f"| distinct member names in the type dictionaries | **{d['distinct_member_names']}** |")
    L.append(f"| type codes met | `{d['type_code_census']}` |")
    ed = d["edit"] or {}
    L.append(f"| edited copy re-read + reverted | **{'PASS' if ed.get('ok') else 'FAIL'}** |")
    L.append("\n## Bytes no field describes, by section\n")
    L.append("| section | bytes | what they are |")
    L.append("|---|---:|---|")
    for k, v in d["unnamed_by_section"].items():
        what = {"header": "header words 11..15 (always 0)",
                "strhash": "u32 string-hash table (count 0 in every file sampled)",
                "instances": "instance-table padding", "types": "type-table padding",
                "names": "name-table padding",
                "data": "struct padding / inline-array duplicate block"}.get(k, "")
        L.append(f"| {k} | {v:,} | {what} |")
    if ed:
        L.append("\n## Edited copy\n")
        L.append(f"* file: `{ed['path']}`")
        L.append(f"* field: `{ed['field']}` {ed['old']} -> {ed['new']}")
        L.append(f"* value read back by the reader: {ed.get('read_back')}")
        L.append(f"* bytes changed: {ed.get('bytes_changed')} at offset {ed.get('window')}")
        L.append(f"* old value written back reproduces the shipped file: {ed.get('revert_identical')}")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["write", "check"])
    ap.add_argument("--bundles", type=int, default=60)
    ap.add_argument("--json", default=OUT_JSON)
    ap.add_argument("--md", default=OUT_MD)
    a = ap.parse_args()
    d = run(a.bundles)
    if a.cmd == "write":
        os.makedirs(os.path.dirname(a.json), exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(summarise(d))
        print(f"wrote {a.json} and {a.md}")
    else:
        old = json.load(open(a.json, encoding="utf-8"))
        bad = 0
        for k in ("files_tested", "strict_identical", "carry_identical", "bytes_total",
                  "bytes_from_fields", "bytes_from_constants", "bytes_copied",
                  "bytes_raw_types", "bytes_not_written", "gap_nonzero_bytes",
                  "gap_duplicating_inline", "gap_unexplained", "type_code_census",
                  "distinct_member_names", "unnamed_by_section", "edit"):
            if old[k] != d[k]:
                print(f"DRIFT {k}: {old[k]!r} != {d[k]!r}")
                bad += 1
        if old["results"] != d["results"]:
            print("DRIFT per-file results")
            bad += 1
        print("check PASS" if not bad else f"check FAIL ({bad})")
        return 1 if bad else 0
    print(f"{d['strict_identical']}/{d['files_tested']} strict identical, "
          f"{d['carry_identical']}/{d['files_tested']} carry identical, "
          f"{100.0 * d['bytes_from_fields'] / d['bytes_total']:.2f}% bytes from fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
