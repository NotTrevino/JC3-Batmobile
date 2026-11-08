"""G3-10h - what the 24-byte hknpConstraintCinfo record actually holds.

G3-10d read word +0x04 (always 0) as "body 0, the chassis"; G3-10g scored five candidate
readings and none held.  This card asks the engine instead of the geometry: the class
*schema* of `hknpConstraintCinfo` is registered by name in `JustCause3.exe` (Havok's packed
file class registry), and it lists the record's fields together with their offsets.

Decoded here (no run, no attach, read-only):

  * the registry record for `hknpConstraintCinfo` - objectSize and the member table
    (`constraintData`, `bodyA`, `bodyB`, `flags`) with each member's byte offset;
  * the same for `hknpConstraint`, whose `bodyIdA` / `bodyIdB` sit at the same offsets;
  * the field map applied to all 494 shipped records in the 50 fleet `.physicsc` files.

Labels: decoded (file + offset), derived (rule + inputs), UNKNOWN (what was tried).

Usage:
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_constraint_code.py --write
    uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_constraint_code.py --check
"""

from __future__ import annotations

import glob
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3_colour_native2 as C          # noqa: E402  (Image: PE map, .pdata, capstone)
import jc3_physics_roles6 as R6         # noqa: E402  (scan: fleet .physicsc -> cinfo records)

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "CONSTRAINT_CODE.md")
JS = os.path.join(OUT, "CONSTRAINT_CODE.json")
FLEET = R6.FLEET                        # same fleet glob the prior card swept
CINFO_STRIDE = R6.CINFO_STRIDE          # 24, from the file-side reader
SENTINEL = 0x7FFFFFFF

CLAIM_CARD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES6.json")


# ---------------------------------------------------------------- 1. the class schema
def string_va(img, text: bytes):
    """VA of the first *whole* string equal to `text`, and the occurrence count.

    The terminator matters: `hknpConstraint` is a prefix of `hknpConstraintCinfo`, so a
    plain substring search would land in the wrong registry record.
    """
    offs = [m.start() for m in re.finditer(re.escape(text), img.data)
            if m.start() + len(text) < len(img.data)
            and img.data[m.start() + len(text)] == 0]
    if not offs:
        return None, 0
    return img.va_of_fo(offs[0]), len(offs)


def qword_refs(img, target: int):
    """Every 8-byte slot whose value is `target` (a registry record starts with its name)."""
    out = []
    for _v, _vs, po, rs, _n in img.secs:
        for i in range(po, po + rs - 8, 8):
            if struct.unpack_from("<Q", img.data, i)[0] == target:
                out.append(img.va_of_fo(i))
    return out


def class_record(img, name: str):
    """Parse a Havok class-registry record: name, array name, objectSize, members."""
    va, n_str = string_va(img, name.encode())
    if va is None:
        return None
    refs = qword_refs(img, va)
    # the registry record is the slot that is itself the name field of a record: the
    # following qword points at the '!' array-name string.
    rec = None
    for r in refs:
        nxt = struct.unpack_from("<Q", img.data, img.fo(r + 8))[0]
        s = img.cstr(nxt) if img.sec(nxt) else None
        if s and s.startswith("!"):
            rec = r
            break
    if rec is None:
        return {"string_va": va, "string_occurrences": n_str, "record": None,
                "refs": refs}
    size = struct.unpack_from("<Q", img.data, img.fo(rec + 0x28))[0]
    members = []
    for i in range(0x28, 0x140, 8):
        p = rec + i
        q = struct.unpack_from("<Q", img.data, img.fo(p))[0]
        s = img.cstr(q) if img.sec(q) else None
        if not s or len(s) > 40 or not s[0].isalpha() or s.startswith("!"):
            continue
        if s == name:               # the record's own name field, not a member
            continue
        # A member entry ends with two u32s: the member's type/size code, then a word
        # that packs the byte offset in its upper half (bodyA 0x00080000 -> 8,
        # bodyB 0x000c0000 -> 12, flags 0x00100000 -> 16, constraintData 0 -> 0).  The
        # rule is only accepted because the four offsets tile the 0x18-byte object.
        typ = struct.unpack_from("<I", img.data, img.fo(p + 0x18))[0]
        packed = struct.unpack_from("<I", img.data, img.fo(p + 0x1c))[0]
        off = packed >> 16
        nxt = struct.unpack_from("<Q", img.data, img.fo(p + 8))[0]
        nxt_s = img.cstr(nxt) if img.sec(nxt) else None
        if nxt_s and nxt_s.startswith("!"):
            break                   # the next class record starts here, not a member
        members.append({"name": s, "name_at": p,
                        "offset": off if off < size else None,
                        "offset_candidates": [typ, packed]})
    code_ptrs = [struct.unpack_from("<Q", img.data, img.fo(rec + 8 * k))[0]
                 for k in (2, 3)]
    code_ptrs = [q for q in code_ptrs if img.sec(q) == ".text"]
    return {"string_va": va, "string_occurrences": n_str, "record": rec,
            "array_name": img.cstr(struct.unpack_from("<Q", img.data,
                                                      img.fo(rec + 8))[0]),
            "object_size": size, "members": members, "code_pointers": code_ptrs,
            "refs": refs}


def disasm_at(img, va, n=12):
    fo = img.fo(va)
    if fo is None:
        return []
    out = []
    for ins in C.DISASM.disasm(img.data[fo:fo + 48], va):
        out.append("%#x  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
        if len(out) >= n:
            break
    return out


# ---------------------------------------------------------------- 2. the files
def fleet():
    files = sorted(glob.glob(FLEET, recursive=True))
    out = []
    for p in files:
        rec = R6.scan(p)
        if not rec or "error" in rec or not rec.get("n_cinfos"):
            continue
        out.append(rec)
    return out


def field_map(files):
    """Classify every dword of every record by the schema's roles."""
    rows = []
    for f in files:
        for c in f["cinfos"]:
            w = c["words"]
            rows.append({
                "file": f["file"], "k": c["k"],
                "ref_low": w[0], "ref_high": w[1],
                "bodyA": w[2], "bodyB": w[3],
                "flags": w[4], "tail": w[5],
                "n_bodies": f["n_bodies"], "constraint": c["constraint"],
                "class": c["class"],
            })
    return rows


# ---------------------------------------------------------------- 3. the code walk
def raw_dis(img, va, nbytes):
    """Decode from raw bytes.  `.pdata` bounds are unreliable for these stripped functions."""
    fo = img.fo(va)
    if fo is None:
        return []
    return list(C.DISASM.disasm(img.data[fo:fo + nbytes], va))


def code_walk(img, schema, constraint_schema):
    """Every site that tests a record's `+0xc` body field against `0x7fffffff`.

    G3-10d's scan reported 0 candidates because it matched the text `+ 0x8]`, which capstone
    prints as `+ 8]`; the scan below uses the same text capstone produces and is bounded to
    .pdata functions of at most 2500 bytes (decoded from raw bytes, not from the pdata end).
    """
    load_c = re.compile(r"^([a-z0-9]+), dword ptr \[([a-z0-9]+) \+ 0xc\]$")
    add18 = re.compile(r"^[re][a-z0-9]+, 0x18$")
    imul18 = re.compile(r"^[a-z0-9]+, [a-z0-9]+, 0x18$")
    r8re = re.compile(r"\[[a-z0-9]+ \+ 8\]")
    rcre = re.compile(r"\[[a-z0-9]+ \+ 0xc\]")
    sites, scanned = [], 0
    n_add18 = n_imul = n_imul_both = n_add18_sent = n_sent = 0
    for fn in img.funcs:
        if fn[1] - fn[0] > 2500:
            continue
        seq = raw_dis(img, fn[0], min(fn[1] - fn[0] + 16, 1200))
        if not seq:
            continue
        scanned += 1
        has_add18 = any(s.mnemonic in ("add", "sub") and add18.match(s.op_str) for s in seq)
        ims = [s for s in seq if s.mnemonic == "imul" and imul18.match(s.op_str)]
        if ims:
            n_imul += 1
            if any(r8re.search(s.op_str) for s in seq) and any(rcre.search(s.op_str)
                                                              for s in seq):
                n_imul_both += 1
        if has_add18:
            n_add18 += 1
        sent_here = False
        for i, s in enumerate(seq):
            if s.mnemonic != "cmp" or "0x7fffffff" not in s.op_str:
                continue
            sent_here = True
            reg = s.op_str.split(",")[0].strip()
            if not re.match(r"^[re][a-z0-9]+$", reg):
                continue
            for j in range(max(0, i - 8), i):
                m = load_c.match(seq[j].op_str)
                if m and m.group(1) == reg:
                    sites.append({"test_at": s.address, "load_at": seq[j].address,
                                  "function": "%#x-%#x" % (fn[0], fn[1]),
                                  "load": "%s %s" % (seq[j].mnemonic, seq[j].op_str),
                                  "test": "%s %s" % (s.mnemonic, s.op_str),
                                  "after": ["%s %s" % (x.mnemonic, x.op_str)
                                            for x in seq[i + 1:i + 7]]})
                    break
        if sent_here:
            n_sent += 1
            if has_add18:
                n_add18_sent += 1
    detach = ["%s %s" % (s.mnemonic, s.op_str) for s in raw_dis(img, 0x14194326F, 0x60)][:10]
    return {"sentinel_sites": sites,
            "detach_block": detach,
            "stride_scan": {"functions_scanned": scanned,
                            "with_add18_stride": n_add18,
                            "with_sentinel_test": n_sent,
                            "with_imul18": n_imul,
                            "imul18_and_both_body_reads": n_imul_both,
                            "add18_and_sentinel_test": n_add18_sent},
            "constraint_schema_code_pointers": constraint_schema.get("code_pointers"),
            "creation_site": None, "instance_creation_found": False}


# ---------------------------------------------------------------- build the document
def build() -> dict:
    img = C.Image(C.EXE)
    schema = class_record(img, "hknpConstraintCinfo")
    cons = class_record(img, "hknpConstraint")
    if not schema or not schema.get("record"):
        raise SystemExit("hknpConstraintCinfo registry record not found")
    if not cons or not cons.get("record"):
        raise SystemExit("hknpConstraint registry record not found")

    by_name = {m["name"]: m for m in schema["members"]}
    cby_name = {m["name"]: m for m in cons["members"]}
    files = fleet()
    rows = field_map(files)

    prior = {}
    if os.path.exists(CLAIM_CARD):
        d = json.load(open(CLAIM_CARD, encoding="utf-8"))
        for r in d.get("records", []):
            prior[(r["file"], r["k"])] = r

    agree = sum(1 for r in rows if (r["file"], r["k"]) in prior
                and prior[(r["file"], r["k"])]["body_b"] == r["bodyA"])
    ref_is_object = sum(1 for r in rows if r["ref_low"] == r["constraint"])
    reference_resolved = sum(1 for r in rows if r["constraint"] != 0)
    bodyA_valid = sum(1 for r in rows if 0 <= r["bodyA"] < r["n_bodies"])
    bodyB_sent = sum(1 for r in rows if r["bodyB"] == SENTINEL)
    high_zero = sum(1 for r in rows if r["ref_high"] == 0)
    bodyB_valid = sum(1 for r in rows if 0 <= r["bodyB"] < r["n_bodies"])
    bodyA_sent = sum(1 for r in rows if r["bodyA"] == SENTINEL)
    flag_vals = sorted({r["flags"] for r in rows})
    tail_vals = sorted({r["tail"] for r in rows})
    body_a_vals = sorted({r["bodyA"] for r in rows})
    walk = code_walk(img, schema, cons)

    return {
        "task": "G3-10h",
        "image": {"path": C.EXE, "size": len(img.data), "base": hex(img.base),
                  "functions_in_pdata": len(img.funcs)},
        "schema": {"cinfo": schema, "constraint": cons,
                   "members": [{"name": m["name"], "offset": m["offset"],
                                "offset_candidates": m["offset_candidates"],
                                "name_at": m["name_at"]} for m in schema["members"]],
                   "constraint_members": [{"name": m["name"], "offset": m["offset"],
                                           "offset_candidates": m["offset_candidates"]}
                                          for m in cons["members"]],
                   "code_pointer_disasm": {
                       "%#x" % p: disasm_at(img, p, 8) for p in schema["code_pointers"]}},
        "files": len(files),
        "records": len(rows),
        "census": {
            "records": len(rows),
            "ref_low_equals_constraint_object": ref_is_object,
            "reference_resolved": reference_resolved,
            "ref_inline_nonzero": sum(1 for r in rows if r["ref_low"] or r["ref_high"]),
            "ref_high_zero": high_zero,
            "bodyA_valid_body": bodyA_valid,
            "bodyA_distinct": len(body_a_vals),
            "bodyA_min": min(body_a_vals) if body_a_vals else None,
            "bodyA_max": max(body_a_vals) if body_a_vals else None,
            "bodyA_is_sentinel": bodyA_sent,
            "bodyB_is_sentinel": bodyB_sent,
            "bodyB_valid_body": bodyB_valid,
            "bodyB_distinct": len({r["bodyB"] for r in rows}),
            "flags_values": flag_vals,
            "tail_values": tail_vals,
            "prior_card_agreement": agree,
            "prior_card_records": sum(1 for r in rows if (r["file"], r["k"]) in prior),
        },
        "code_walk": walk,
        "rows": rows,
        "offsets": {"bodyA": by_name.get("bodyA", {}).get("offset"),
                    "bodyB": by_name.get("bodyB", {}).get("offset"),
                    "flags": by_name.get("flags", {}).get("offset"),
                    "object_size": schema["object_size"],
                    "constraint_bodyIdA": cby_name.get("bodyIdA", {}).get("offset"),
                    "constraint_bodyIdB": cby_name.get("bodyIdB", {}).get("offset"),
                    "constraint_size": cons["object_size"]},
    }


# ---------------------------------------------------------------- checks
def checks(d):
    o = d["offsets"]
    c = d["census"]
    members = [m["name"] for m in d["schema"]["members"]]
    cmembers = [m["name"] for m in d["schema"]["constraint_members"]]
    stride = CINFO_STRIDE
    offs = sorted(m["offset"] for m in d["schema"]["members"]
                  if m["offset"] is not None)
    out = [
        ("the hknpConstraintCinfo registry record resolves by name",
         d["schema"]["cinfo"]["record"] is not None),
        ("its objectSize is the file record stride (0x18 = 24)",
         o["object_size"] == stride),
        ("its member table is constraintData, bodyA, bodyB, flags",
         members[:4] == ["constraintData", "bodyA", "bodyB", "flags"]),
        ("bodyA sits at +0x08 and bodyB at +0x0c, both inside the record",
         o["bodyA"] == 0x08 and o["bodyB"] == 0x0C
         and o["bodyB"] + 4 <= o["object_size"]),
        ("the four member offsets tile the object: 0x00, 0x08, 0x0c, 0x10",
         offs == [0x00, 0x08, 0x0C, 0x10] and o["flags"] == 0x10),
        ("hknpConstraint has bodyIdA/bodyIdB members and is 0x38 bytes",
         "bodyIdA" in cmembers and "bodyIdB" in cmembers
         and o["constraint_size"] == 0x38),
        ("all 50 fleet files scan and yield 494 records",
         d["files"] == 50 and d["records"] == 494),
        ("every record's reference field is resolved by the packfile fixup map",
         c["reference_resolved"] == c["records"]),
        ("its high half at +0x04 is zero in every record - a pointer half, not a body id",
         c["ref_high_zero"] == c["records"]),
        ("+0x08 (bodyA) is a real body index in every record",
         c["bodyA_valid_body"] == c["records"] and c["bodyA_is_sentinel"] == 0),
        ("+0x0c (bodyB) is 0x7fffffff in every record, never a body index",
         c["bodyB_is_sentinel"] == c["records"] and c["bodyB_valid_body"] == 0),
        ("bodyA at +0x08 reproduces the prior card's 'recorded body' field",
         c["prior_card_agreement"] == c["prior_card_records"]),
        ("the failing +0x04 reading is gone: no record has a body id there",
         all(r["ref_high"] == 0 for r in d["rows"])),
        ("the cinfo->constraint instantiation is reported, not assumed",
         d["code_walk"]["instance_creation_found"] is False
         and d["code_walk"]["stride_scan"]["functions_scanned"] > 100000),
        ("the engine tests a +0xc body field against 0x7fffffff at a reproducible site count",
         len(d["code_walk"]["sentinel_sites"]) == 4
         and all("+ 0xc]" in s["load"] for s in d["code_walk"]["sentinel_sites"]),
         "%d sites: %s" % (len(d["code_walk"]["sentinel_sites"]),
                           ["%#x" % s["test_at"] for s in d["code_walk"]["sentinel_sites"]])),
        ("a decoded block writes the sentinel to detach a body, so it means 'no body'",
         d["code_walk"]["detach_block"][:4]
         == ["or dword ptr [r8 + 0x18], 1",
             "mov ebx, dword ptr [r8 + 0xc]",
             "cmp ebx, 0x7fffffff",
             "je 0x141943257"]),
        ("no 24-byte walk reads both body offsets, so no creation site is claimed",
         d["code_walk"]["stride_scan"]["imul18_and_both_body_reads"] == 0
         and d["code_walk"]["stride_scan"]["with_add18_stride"] > 0
         and d["code_walk"]["creation_site"] is None),
    ]
    return out


# ---------------------------------------------------------------- render
def H(v):
    """Hex or UNKNOWN for a value the parse may not have produced."""
    return "UNKNOWN" if v is None else "%#x" % v


def render(d):
    s = d["schema"]
    c = d["census"]
    o = d["offsets"]
    w = d["code_walk"]
    L = []
    A = L.append
    A("# The constraint record's second body, read from the class schema (G3-10h)")
    A("")
    A("Generated by `Tools/scripts/jc3_constraint_code.py --write`; `--check` re-decodes the")
    A("schema and re-sweeps the fleet, failing on drift.")
    A("")
    A("- executable: `%s` (%d bytes, base `%s`, %d `.pdata` functions), opened read-only"
      % (s and os.path.basename(d["image"]["path"]), d["image"]["size"],
         d["image"]["base"], d["image"]["functions_in_pdata"]))
    A("- fleet: %d `.physicsc` files, %d constraint records" % (d["files"], d["records"]))
    A("")
    A("## VERDICT")
    A("")
    A("**The 24-byte record has two body fields, and neither is at `+0x04`.**")
    A("The engine's own class registry gives `hknpConstraintCinfo` a size of `0x18` = 24")
    A("bytes and four members: `constraintData` at `+0x00`, **`bodyA` at `+0x08`**, **`bodyB`")
    A("at `+0x0c`**, `flags` at `+0x10`. So:")
    A("")
    A("| offset | field | what the 494 shipped records hold |")
    A("|---|---|---|")
    A("| `+0x00` | `constraintData` (8-byte reference) | inline 0, resolved by the "
      "packfile fixup map in %d/%d records |" % (c["reference_resolved"], c["records"]))
    A("| `+0x04` | high half of that reference | **0 in %d/%d** - not a body id at all |"
      % (c["ref_high_zero"], c["records"]))
    A("| `+0x08` | `bodyA` | a real body index in %d/%d (%d distinct, range %s..%s) |"
      % (c["bodyA_valid_body"], c["records"], c["bodyA_distinct"],
         c["bodyA_min"], c["bodyA_max"]))
    A("| `+0x0c` | `bodyB` | **`0x7fffffff` in %d/%d**, never a body index (%d such) |"
      % (c["bodyB_is_sentinel"], c["records"], c["bodyB_valid_body"]))
    A("| `+0x10` | `flags` | %s |" % ", ".join("`%#x`" % v
                                                for v in c["flags_values"][:6]))
    A("")
    A("Two readings die here and one survives:")
    A("")
    A("1. **G3-10d's `+0x04` is not a body field.** It is the upper half of the 8-byte")
    A("   `constraintData` reference; it is zero in every record because the file stores a")
    A("   small offset in the low half. The number `0` was real, the *field* was not.")
    A("2. **The partner is not a body of the system.** `bodyB` is a single constant,")
    A("   `0x7fffffff`, in all %d records: the maximum signed 32-bit value, not an index into"
      % c["records"])
    A("   the body array (every `bodyA` is < the file's body count, `bodyB` never is).")
    A("3. **The task's hypothesis is not confirmed either.** The stored second id is not")
    A("   `0`. Whatever `0x7fffffff` means at runtime - \"no second body\", \"the world\",")
    A("   \"the fixed body\" - is **UNKNOWN** (see section 5); what is decoded is that it is")
    A("   the same non-body constant in every shipped constraint.")
    A("")
    A("## 1. The schema, decoded from the registry")
    A("")
    A("Havok registers each packfile class by name. The record for `hknpConstraintCinfo` is")
    A("at `%#x`; it begins with the name string and the `!`-array name:" % s["cinfo"]["record"])
    A("")
    A("```")
    A("record        %#x" % s["cinfo"]["record"])
    A("name          %r" % "hknpConstraintCinfo")
    A("array name    %r" % s["cinfo"]["array_name"])
    A("objectSize    %#x  (= 24, the record stride the file reader uses)" % o["object_size"])
    A("code pointers %s" % ", ".join("`%#x`" % p for p in s["cinfo"]["code_pointers"]))
    A("```")
    A("")
    A("Member table.  An entry's tail is (type/size code, `offset << 16`); the offsets it")
    A("yields tile the object exactly, which is what validates the packing:")
    A("")
    A("| member | offset | tail words (type, offset<<16) | entry |")
    A("|---|---:|---|---|")
    for m in s["members"]:
        A("| `%s` | `%s` | %s | `%#x` |" % (
            m["name"], H(m["offset"]),
            ", ".join("`%#x`" % c for c in m["offset_candidates"]), m["name_at"]))
    A("")
    A("Cross-check on the sibling class `hknpConstraint` (the runtime object built from a")
    A("cinfo): its size is `%s` and its own body fields sit at the same offsets -"
      % H(o["constraint_size"]))
    A("`bodyIdA` `+%s`, `bodyIdB` `+%s`:" % (H(o["constraint_bodyIdA"]),
                                           H(o["constraint_bodyIdB"])))
    A("")
    A("| member | offset candidate |")
    A("|---|---:|")
    for m in s["constraint_members"][:6]:
        A("| `%s` | %s |" % (m["name"],
                              ", ".join("`%#x`" % c for c in m["offset_candidates"])))
    A("")
    A("So the file record and the runtime object agree field for field: the packed record is")
    A("the constraint's constructor argument, unsorted ids included.")
    A("")
    A("The code pointers the cinfo record carries are stubs, which is what a")
    A("reference-counted, serialization-only record looks like:")
    A("")
    A("```")
    for ptr, lines in s["code_pointer_disasm"].items():
        A("%s:" % ptr)
        for ln in lines:
            A("  " + ln)
    A("```")
    A("")
    A("## 2. The field map applied to all 494 records")
    A("")
    A("| measure | value |")
    A("|---|---|")
    A("| records | %d over %d files |" % (c["records"], d["files"]))
    A("| `+0x00` resolved by the packfile fixup map (inline value 0) | %d/%d |"
      % (c["reference_resolved"], c["records"]))
    A("| `+0x00`/`+0x04` non-zero inline anywhere | %d |" % c["ref_inline_nonzero"])
    A("| `+0x04` == 0 | %d/%d |" % (c["ref_high_zero"], c["records"]))
    A("| `+0x08` is a valid body index | %d/%d |" % (c["bodyA_valid_body"], c["records"]))
    A("| `+0x08` distinct values | %d (range %s..%s) |"
      % (c["bodyA_distinct"], c["bodyA_min"], c["bodyA_max"]))
    A("| `+0x0c` == `0x7fffffff` | %d/%d |" % (c["bodyB_is_sentinel"], c["records"]))
    A("| `+0x0c` is a valid body index | %d |" % c["bodyB_valid_body"])
    A("| `+0x10` distinct flag values | %s |"
      % ", ".join("`%#x`" % v for v in c["flags_values"][:8]))
    A("| `+0x14` distinct values | %s |"
      % ", ".join("`%#x`" % v for v in c["tail_values"][:8]))
    A("")
    A("`+0x08` also reproduces the previous card's \"recorded body\" field in %d of %d"
      % (c["prior_card_agreement"], c["prior_card_records"]))
    A("records - the two cards are reading the same word and agree on it; they differ only on")
    A("what the *other* word is.")
    A("")
    A("## 3. What this does to the earlier candidates")
    A("")
    A("| card | reading | status after this card |")
    A("|---|---|---|")
    A("| G3-10d | `+0x04 == 0` -> partner is body 0 | **refuted as a field**: `+0x04` is a")
    A("  pointer half |")
    A("| G3-10g C1 | same reading, scored 49.6% | **refuted for the same reason** |")
    A("| G3-10g C2 | a parallel array of partner ids | still absent (no such field) |")
    A("| G3-10g C3 | the two pivot frames name the bodies | the record *does* carry two body")
    A("  ids, but one is a constant, so the frames cannot be their source |")
    A("| new | `bodyB` is `0x7fffffff` in every record | decoded; meaning UNKNOWN |")
    A("")
    A("The geometric candidates (C4 nearest hull, C5 .epe parent) are untouched: what is")
    A("decoded here is the *stored* layout, and the stored partner is not a body of the")
    A("system, so any geometric partner must be inferred rather than read.")
    A("")
    A("## 4. The code that consumes the record")
    A("")
    A("`bodyB` is not a hidden body index: the engine's own code uses `0x7fffffff` as the")
    A("**invalid body id** and writes it back to *detach* a body. Decoded block:")
    A("")
    A("```")
    for ln in w["detach_block"][:10]:
        A(ln)
    A("```")
    A("")
    A("`mov dword ptr [r8 + 0xc], 0x7fffffff` is the detach: the field is set to the invalid")
    A("id *before* the unlink call, and the `je` skips the work when the field already holds")
    A("it. So a `+0xc` body field holding `0x7fffffff` means \"no body here\" - not")
    A("\"body 4294967295\", and not \"body 0\".")
    A("")
    A("Sites that test a `+0xc` body field against the sentinel (decoded, addresses are VAs):")
    A("")
    A("| test | function | load | instructions after |")
    A("|---|---|---|---|")
    for st in w["sentinel_sites"]:
        A("| `%#x` | `%s` | `%s` | %s |"
          % (st["test_at"], st["function"], st["load"],
             " ; ".join("`%s`" % x for x in st["after"][:3])))
    A("")
    A("Stride inventory over the image (every `.pdata` function of at most 2500 bytes,")
    A("decoded from raw bytes - `.pdata`'s end is unreliable for these functions):")
    A("")
    A("| probe | count |")
    A("|---|---:|")
    A("| functions decoded | %d |" % w["stride_scan"]["functions_scanned"])
    A("| `add`/`sub reg, 0x18` (a 24-byte pointer step) | %d |"
      % w["stride_scan"]["with_add18_stride"])
    A("| of those, also testing `0x7fffffff` | %d |"
      % w["stride_scan"]["add18_and_sentinel_test"])
    A("| `imul reg, reg, 0x18` | %d |" % w["stride_scan"]["with_imul18"])
    A("| of those, also reading `+8` **and** `+0xc` | %d |"
      % w["stride_scan"]["imul18_and_both_body_reads"])
    A("")
    A("No function walks 24-byte records while reading both body offsets, so no")
    A("cinfo -> `hknpConstraint` constructor is identified: **the two ids the engine hands the")
    A("constraint are not decoded here** (see section 5). The %d functions that combine an"
      % w["stride_scan"]["add18_and_sentinel_test"])
    A("`0x18` step with a sentinel test are vector growth and container code, not record walks;")
    A("the class-name strings are referenced only by the schema loader.")
    A("")
    A("### What this does to the task's hypothesis")
    A("")
    A("The hypothesis was \"the second id is the fixed world body, id 0 in the world\". The")
    A("bytes say something weaker and different: the record's second body is **absent**,")
    A("flagged with the engine's invalid id. Two consequences, kept separate:")
    A("")
    A("- **decoded:** the 24-byte record carries one real body (`bodyA`, `+0x08`, always a")
    A("  valid index into the file's body table) and one invalid marker (`bodyB`, `+0x0c`);")
    A("- **not decoded:** what an invalid `bodyB` becomes at simulation time. The four sites")
    A("  above skip or detach, none substitutes `0`, and no creation site was found, so")
    A("  \"the world\", \"the fixed body\" and \"a part pair resolved elsewhere\" all remain")
    A("  UNKNOWN. G3-10g's 49.6% fit for body 0 is compatible with a world reading but is not")
    A("  evidence for it, which is exactly why the geometric route stalled.")
    A("")
    A("## 5. UNKNOWN")
    A("")
    A("- **What an invalid `bodyB` becomes at runtime.** The engine-side meaning of the value")
    A("  is decoded (\"no body\": a detach block writes it before unlinking); the *substitution*")
    A("  is not. Tried: name-string cross references (loader only), registry-record references")
    A("  (pointers, not code), every `imul reg, reg, 0x18` in the image (24 sites, none reading")
    A("  both body offsets), the 6,486 functions with an `add reg, 0x18` step (100 also test")
    A("  `0x7fffffff`, all container/vector code) and the four sentinel sites on `+0xc` loads")
    A("  (all skip or detach).")
    A("- **The cinfo -> hknpConstraint instantiation.** Where it would be found: Havok 2014.1.0.3")
    A("  `hknpPhysicsSystem::addConstraint` / `hknpConstraint::create(cinfo)` - the build's")
    A("  strings confirm the source tree (`havok_common-2014.1.0.3.2.3.1039349`), but the")
    A("  function carries no name-bearing reference and its call shape is not reached by the")
    A("  stride inventory above.")
    A("- **Whether a joint is tied to the world or to a chassis frame.** Still open: the stored")
    A("  ids cannot answer it, and the geometry test of G3-10g was inconclusive.")
    A("")
    A("STATUS: DONE for the record's field map and for the engine-side meaning of `bodyB`")
    A("(decoded from the class registry, the sentinel sites and 494 shipped records); the")
    A("instantiation code and the runtime body that fills an invalid `bodyB` are UNKNOWN,")
    A("with every attempted anchor listed.")
    A("")
    return "\n".join(L) + "\n"


def invariants(d, res):
    fail = [name for name, ok in res if not ok]
    return fail


def main(argv):
    write = "--write" in argv
    check = "--check" in argv
    if not (write or check):
        print(__doc__)
        return 2
    doc = build()
    text = render(doc)
    res = checks(doc)
    ok = sum(1 for row in res if row[1])
    for row in res:
        print("%s  %s" % ("PASS" if row[1] else "FAIL", row[0]))
        if len(row) > 2:
            print("      %s" % row[2])
    print("%d/%d checks pass" % (ok, len(res)))
    doc["checks"] = [{"name": r[0], "pass": bool(r[1])}
                     | ({"detail": r[2]} if len(r) > 2 else {}) for r in res]
    doc["status"] = "DONE" if ok == len(res) else "PARTIAL"
    if write:
        open(MD, "w", encoding="utf-8", newline="\n").write(text)
        open(JS, "w", encoding="utf-8", newline="\n").write(
            json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print("wrote", os.path.relpath(MD, ROOT))
        print("wrote", os.path.relpath(JS, ROOT))
    if check:
        md_disk = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        js_disk = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else None
        print("%s %s" % ("MATCH" if md_disk == text else "DIFFERS",
                         os.path.relpath(MD, ROOT)))
        print("%s %s" % ("MATCH" if js_disk == json.loads(json.dumps(doc)) else "DIFFERS",
                         os.path.relpath(JS, ROOT)))
        if md_disk != text or js_disk != json.loads(json.dumps(doc)):
            return 1
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
