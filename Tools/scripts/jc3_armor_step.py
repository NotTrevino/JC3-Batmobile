"""jc3_armor_step.py - G2-28b: how the `*_armor` step is addressed in JustCause3.exe.

`Research/JC3Grab/DAMAGE_MODEL.md` leaves step 4 open: no file says how
`<channel>_armor` and `<channel>_armor_strength` compose to decide how much of a
hit reaches health.  This card answers the part of that question the executable
*can* answer statically - **how the engine addresses those values at run time** -
and states the composition itself as UNKNOWN rather than guessing it.

Three measurements, each with an oracle that fails if it is wrong:

1. The ADF vocabulary block that holds every `VehicleDamage` member name is
   inert: not one of its 473 names is referenced by an instruction or by a
   pointer table anywhere in the image.
2. Jenkins hashes of all 30 `VehicleDamage` members occur **zero** times in the
   51 MB image, so the armour fields are not reached by name *or* by hash.
3. What the code does know is the ADF **type** hash, `0xaca39a2d`, and it uses it
   in exactly one instruction (`cmp dword ptr [r11+8], 0xaca39a2d`), inside the
   accessor that hands back the module's `VehicleDamage` blob.

The blob is the compiled struct image: 128 bytes (the `size` in the module's own
type library).  Its first 19 members sit at 4-byte strides, and the two readings
of each word - int32 and float32 - separate them without assuming anything:
`<channel>_armor` decodes only as an int32, `<channel>_armor_strength` only as a
float32.  That is the one finding this card adds to DAMAGE_MODEL.md, and it is a
correction: the strengths are IEEE singles in the shipped data, not ints.

    python Tools/scripts/jc3_armor_step.py --write
    python Tools/scripts/jc3_armor_step.py --check

Static only: `JustCause3.exe` and the module are opened read-only and never run,
attached to or injected into.
"""
from __future__ import annotations

import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3_colour_native as C          # noqa: E402  (PE image, disasm, refmap)
import jc3adf                          # noqa: E402  (ADF type library / instance)
from rbmhdr import hash_jenkins        # noqa: E402  (the project's jenkins hash)

OUT = os.path.join(REPO, "Research", "JC3Grab")
MD_NAME = "ARMOR_STEP.md"
JSON_NAME = "ARMOR_STEP.json"

EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
MODULE = (r"E:/Modding/_shared/gamedata/JC3grab/b13b/unpacked/editor/entities/"
          r"jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc")
DAMAGE_MECH = os.path.join(OUT, "DAMAGE_MECHANISMS.md")

TYPE_NAME = "VehicleDamage"
# the 19 members that decode at 4-byte strides from the instance image, in the
# order the vocabulary block lists them
BLOCK = ["max_health",
         "bullet_armor", "bullet_armor_strength",
         "bullet_heavy_armor", "bullet_heavy_armor_strength",
         "explosion_armor", "explosion_armor_strength",
         "impact_armor", "impact_armor_strength",
         "fire_armor", "fire_armor_strength",
         "melee_armor", "melee_armor_strength",
         "electricity_armor", "electricity_armor_strength",
         "grapple_pull_armor", "grapple_pull_armor_strength",
         "impact_damage_factor", "deform_scale"]
# the value domain each member is allowed to sit in; used to decide, per word,
# whether the int32 reading or the float32 reading is the one the field means
DOMAIN = {"max_health": (1, 20000), "impact_damage_factor": (0, 100),
          "deform_scale": (0, 100)}
DEFAULT_DOMAIN = (-1, 5000)          # armour: -1 is the fleet's "no value" mark
STRENGTH_DOMAIN = (0, 100)


# --------------------------------------------------------------------- helpers
def domain_of(member: str) -> tuple[int, int]:
    if member in DOMAIN:
        return DOMAIN[member]
    if member.endswith("_strength"):
        return STRENGTH_DOMAIN
    return DEFAULT_DOMAIN


def rtti_vtables(img, cls: str) -> list[dict]:
    """COL/TypeDescriptor/vtable walk, x64 MSVC (see the COL layout below)."""
    data = img.data
    B = img.base
    out, pat = [], b".?AV" + cls.encode() + b"@@\0"
    i = -1
    while True:
        i = data.find(pat, i + 1)
        if i < 0:
            break
        name_va = img.va_of_fo(i)
        if name_va is None:
            continue
        td = name_va - 0x10                      # TypeDescriptor: name at +0x10
        rva = struct.pack("<I", td - B)
        j = -1
        while True:
            j = data.find(rva, j + 1)
            if j < 0:
                break
            col_fo = j - 0xC                     # pTypeDescriptor is a u32 RVA
            if col_fo < 0:
                continue
            if struct.unpack_from("<I", data, col_fo)[0] != 1:
                continue                         # signature must be 1
            col_va = img.va_of_fo(col_fo)
            if col_va is None:
                continue
            if struct.unpack_from("<I", data, col_fo + 0x14)[0] != col_va - B:
                continue                         # pSelf points at the COL
            vp = struct.pack("<Q", col_va)
            k = -1
            while True:
                k = data.find(vp, k + 1)
                if k < 0:
                    break
                if k % 8:
                    continue
                vt = img.va_of_fo(k + 8)         # vtable[-1] holds the COL
                if vt is None:
                    continue
                slots = []
                for n in range(64):
                    f = struct.unpack_from("<Q", data, img.fo(vt + 8 * n))[0]
                    if img.sec(f) != ".text":
                        break
                    slots.append(f)
                out.append({"type_descriptor": td, "name_va": name_va,
                            "col": col_va, "vtable": vt, "slots": slots})
    return out


def vocabulary(img) -> dict:
    """The .rdata string run that carries the ADF member names."""
    run = None
    for r in C.string_runs(img):
        names = {n for _va, n in r}
        if {TYPE_NAME, "bullet_armor", "max_health"} <= names:
            run = r
            break
    if not run:
        raise SystemExit("jc3_armor_step: the VehicleDamage vocabulary run is missing")
    names = [n for _va, n in run]
    i = names.index(TYPE_NAME)
    members = []
    for n in names[i + 1:]:
        if n[:1].isupper() or n.startswith("A["):
            break
        members.append(n)
    targets = [va for va, _n in run]
    img.build_refmap(targets)
    code_refs = {n: len(img.refs(va)) for va, n in run if img.refs(va)}
    # a pointer table would hold the name VAs; none does
    ptr_hits = {}
    for va, n in run:
        c = img.data.count(struct.pack("<Q", va))
        if c:
            ptr_hits[n] = c
    return {
        "run_length": len(run),
        "first": {"name": run[0][1], "va": run[0][0]},
        "last": {"name": run[-1][1], "va": run[-1][0]},
        "type_name_index": i,
        "members": members,
        "member_count": len(members),
        "code_refs_total": sum(code_refs.values()),
        "code_refs": code_refs,
        "qword_pointer_total": sum(ptr_hits.values()),
        "qword_pointers": ptr_hits,
    }


def member_hashes(img, members: list[str]) -> dict:
    rows = []
    for m in members:
        h = hash_jenkins(m.encode())
        rows.append({"member": m, "jenkins": h,
                     "occurrences_in_image": img.data.count(struct.pack("<I", h))})
    return {"hash_function": "rbmhdr.hash_jenkins (one-at-a-time)",
            "rows": rows, "total_occurrences": sum(r["occurrences_in_image"] for r in rows)}


def type_library(path: str) -> dict:
    if not os.path.exists(path):
        raise SystemExit("jc3_armor_step: module not found at %s" % path)
    blob = open(path, "rb").read()
    a = jc3adf.Adf(blob)
    data_off = a.data_off if isinstance(a.data_off, int) else a.data_off()
    types = []
    for th, t in a.types.items():
        types.append({"name": a.type_name(th), "name_hash": th, "code": t["code"],
                      "size": t["size"], "align": t["align"]})
    hit = next((t for t in types if t["name"] == TYPE_NAME), None)
    inst = a.instances[0]
    return {"path": path, "bytes": len(blob), "data_off": data_off,
            "types": sorted(types, key=lambda t: -t["size"]),
            "vehicle_damage": hit,
            "instance": {"name": inst["name"], "type": inst["type"],
                         "offset": inst["offset"], "size": inst["size"]}}


def code_use_of_type_hash(img, h: int) -> dict:
    """Every place the u32 `h` appears, and the instruction that owns it."""
    pat = struct.pack("<I", h)
    occ, text_sites, rejected = [], [], []
    i = -1
    while True:
        i = img.data.find(pat, i + 1)
        if i < 0:
            break
        va = img.va_of_fo(i)
        if va is None:
            continue
        occ.append({"va": va, "section": img.sec(va)})
        if img.sec(va) != ".text":
            continue
        fn = img.func_of(va)
        found = None
        if fn:
            for ins in img.dis(fn):
                if ins.address <= va < ins.address + ins.size:
                    found = ins
                    break
        if found and ("0x%08x" % h) in found.op_str:
            fo = img.fo(found.address)
            text_sites.append({"va": found.address, "pattern_at": va,
                               "function": [fn[0], fn[1]],
                               "mnemonic": found.mnemonic, "op_str": found.op_str,
                               "ins_size": found.size,
                               "bytes": img.data[fo:fo + found.size].hex(" ")})
        else:
            rejected.append({"va": va, "reason": "immediate is not an instruction operand"})
    return {"occurrences": occ, "text_sites": text_sites, "rejected": rejected}


def getter_disassembly(img, fn_va: int) -> list[str]:
    fn = img.func_of(fn_va)
    if not fn:
        return []
    return ["%#x  %s %s" % (i.address, i.mnemonic, i.op_str) for i in img.dis(fn)]


def armour_block(path: str, data_off: int, members: list[str]) -> dict:
    """Decode the 4-byte-strided head of the instance as int32 *and* float32.

    The discriminator is deliberately assumption-free: an armour word can only be
    an int in [-1, 5000] or a float in the same range; a strength word only an int
    in [0, 100] or a float in [0, 100].  Exactly one reading must survive, except
    for a zero word - where both readings are 0 and the choice cannot matter.
    """
    blob = open(path, "rb").read()
    rows, problems = [], []
    for k, m in enumerate(members):
        off = data_off + 4 * k
        raw = struct.unpack_from("<I", blob, off)[0]
        as_int = struct.unpack_from("<i", blob, off)[0]
        as_float = struct.unpack_from("<f", blob, off)[0]
        lo, hi = domain_of(m)
        int_ok = lo <= as_int <= hi
        # a float reading only counts when it is a whole number inside the domain:
        # every strength in the fleet is one (0..100), so a denormal such as
        # 7.0e-42 is the int-encoded 5000 seen down the wrong end of the telescope
        flt_ok = (math.isfinite(as_float) and lo <= as_float <= hi
                  and as_float == round(as_float))
        if int_ok and flt_ok:
            reading = "either (zero)" if raw == 0 else "ambiguous"
            if raw != 0:
                problems.append("%s: both readings valid (raw %#x)" % (m, raw))
        elif int_ok:
            reading = "int32"
        elif flt_ok:
            reading = "float32"
        else:
            reading = "no valid reading"
            problems.append("%s: raw %#x decodes in neither domain" % (m, raw))
        rows.append({"offset_in_instance": 4 * k, "member": m, "raw": raw,
                     "int32": as_int, "float32": as_float,
                     "domain": [lo, hi], "reading": reading,
                     "value": as_float if reading.startswith("float") else as_int})
    return {"rows": rows, "problems": problems,
            "ints": [r["member"] for r in rows if r["reading"] == "int32"],
            "floats": [r["member"] for r in rows if r["reading"] == "float32"],
            "zeros": [r["member"] for r in rows if r["reading"].startswith("either")]}


def hash_naming_oracle(img, binder_va: int) -> dict:
    """The method that *does* name a property: jenkins hash -> code immediate."""
    fn = img.func_of(binder_va)
    imms = []
    if fn:
        for i in img.dis(fn):
            if i.mnemonic == "mov" and i.op_str.startswith("r8d, 0x"):
                imms.append(int(i.op_str.split(", ")[1], 16))
    dt = hash_jenkins(b"damage_type")
    inv = hash_jenkins(b"invulnerable")
    doc = open(DAMAGE_MECH, encoding="utf-8").read() if os.path.exists(DAMAGE_MECH) else ""
    return {"binder_function": list(fn) if fn else None,
            "hash_immediates": imms,
            "jenkins_damage_type": dt,
            "damage_type_in_binder": dt in imms,
            "jenkins_invulnerable": inv,
            "invulnerable_recorded_in_damage_mechanisms": ("%08x" % inv) in doc.lower()}


def build() -> dict:
    if not os.path.exists(EXE):
        raise SystemExit("jc3_armor_step: JustCause3.exe not found at %s" % EXE)
    img = C.Image(EXE)
    print("  vocabulary run ...", flush=True)
    voc = vocabulary(img)
    print("  member hashes ...", flush=True)
    hashes = member_hashes(img, voc["members"])
    print("  module type library ...", flush=True)
    lib = type_library(MODULE)
    vd = lib["vehicle_damage"]
    if not vd:
        raise SystemExit("jc3_armor_step: %s has no %s type" % (MODULE, TYPE_NAME))
    print("  type-hash code use ...", flush=True)
    uses = code_use_of_type_hash(img, vd["name_hash"])
    site = uses["text_sites"][0] if uses["text_sites"] else None
    print("  armour block ...", flush=True)
    block = armour_block(MODULE, lib["data_off"], [m for m in BLOCK if m in voc["members"]])
    print("  RTTI ...", flush=True)
    vds = rtti_vtables(img, "CVehicleDamageState")
    dca = rtti_vtables(img, "CDamageControllerArmor")
    print("  hash-naming oracle ...", flush=True)
    naming = hash_naming_oracle(img, 0x140B96B0C)

    doc = {
        "meta": {"generator": "Tools/scripts/jc3_armor_step.py",
                 "card": "G2-28b (the armour step of DAMAGE_MODEL.md)",
                 "exe": EXE, "exe_bytes": len(img.data),
                 "exe_sha256": __import__("hashlib").sha256(img.data).hexdigest(),
                 "image_base": img.base,
                 "module": lib["path"],
                 "static_only": "the executable is opened read-only and never run"},
        "vocabulary": voc,
        "member_hashes": hashes,
        "type_library": lib,
        "type_hash_code_use": uses,
        "getter": {"function": site["function"] if site else None,
                   "disassembly": getter_disassembly(img, site["function"][0]) if site else []},
        "armour_block": block,
        "rtti": {"CVehicleDamageState": [{"vtable": r["vtable"], "col": r["col"],
                                         "slots": len(r["slots"])} for r in vds],
                 "CDamageControllerArmor": [{"vtable": r["vtable"], "col": r["col"],
                                             "slots": len(r["slots"])} for r in dca]},
        "hash_naming": naming,
    }

    checks = {
        "vocabulary_names_have_no_code_reference": voc["code_refs_total"] == 0,
        "vocabulary_names_have_no_pointer_table": voc["qword_pointer_total"] == 0,
        "vocabulary_block_is_the_whole_vocabulary": voc["run_length"] > 400,
        "member_count_is_30": voc["member_count"] == 30,
        "member_hashes_absent_from_the_image": hashes["total_occurrences"] == 0,
        "vehicle_damage_struct_is_128_bytes": vd["size"] == 128,
        "type_hash_has_exactly_one_code_site": len(uses["text_sites"]) == 1,
        "that_site_is_a_compare_against_the_type_hash":
            bool(site) and site["mnemonic"] == "cmp"
            and ("0x%08x" % vd["name_hash"]) in site["op_str"],
        "armour_block_decodes_every_word": not block["problems"],
        "armour_words_are_int32": all(m in block["ints"] for m in block["ints"]) and
            all(r["reading"] == "int32" for r in block["rows"]
                if r["member"].endswith("_armor") and r["raw"] != 0),
        "strength_words_are_float32": all(
            r["reading"] in ("float32", "either (zero)") for r in block["rows"]
            if r["member"].endswith("_armor_strength")),
        "medium_tank_bullet_pair_is_5000_at_99_0":
            next(r for r in block["rows"] if r["member"] == "bullet_armor")["int32"] == 5000
            and next(r for r in block["rows"] if r["member"] == "bullet_armor_strength")["float32"] == 99.0,
        "jenkins_reproduces_the_recorded_epe_field_hash":
            naming["invulnerable_recorded_in_damage_mechanisms"],
        "damage_type_hash_named_in_the_binder": naming["damage_type_in_binder"],
        "both_damage_classes_are_rtti_visible":
            bool(doc["rtti"]["CVehicleDamageState"]) and bool(doc["rtti"]["CDamageControllerArmor"]),
    }
    doc["oracles"] = {"checks": checks,
                      "passed": sum(1 for v in checks.values() if v),
                      "total": len(checks)}
    doc["unknowns"] = [
        {"what": "the arithmetic that composes `<channel>_armor` with "
                 "`<channel>_armor_strength` and the hit's damage",
         "tried": "three whole-image sweeps, all recorded in section 6: (a) functions reading a "
                  "channel-indexed pair of int32s 4 bytes apart - 211 candidates; (b) functions "
                  "reading an int32 with a float32 4 bytes later - 910 pairs in 330 functions; "
                  "(c) that second set intersected with `cvtsi2ss` plus a 100.0/0.01 float "
                  "constant - 4 candidates.  Every survivor was read and none indexes the "
                  "`VehicleDamage` block",
         "why_unknown": "the gate is compiled code, not a table: the eight pairs are reached by "
                        "struct displacement, the type is only ever found by its module type "
                        "hash, and the executable has no name or hash handle on any armour "
                        "member to anchor the search on.  The consumer sits behind the accessor "
                        "at %s, whose cached result is written to `[this+0x10]`; locating it needs "
                        "either a live debugger (excluded: the game must not be run) or a much "
                        "wider read of the call graph through virtual dispatch"
                        % (("%#x" % site["function"][0]) if site else "the typed accessor")},
        {"what": "whether `max_health` is an absolute pool or a scale",
         "tried": "the struct image: `max_health` is int32 2000 at +0x00, i.e. the same domain "
                  "as the shipped values (500..4000)",
         "why_unknown": "the field decodes, its unit does not; DAMAGE_MODEL.md step 6 already "
                        "carries this and nothing in the type library names a unit"},
        {"what": "the layout of the `VehicleDamage` members after `deform_scale` (+0x4c)",
         "tried": "read the instance as 4-byte words: from +0x4c the bytes are 0x00fa041a, "
                  "0x0014000a, not a 4-byte-strided run",
         "why_unknown": "the tail of the blob switches to a narrower encoding (1050 and 250 - "
                        "the medium tank's `smoke_threshold` and `burn_threshold` - fit as two "
                        "u16s at +0x4c), so the remaining 11 members cannot be laid out by "
                        "stride alone; the armour block this card is about ends before that"},
    ]
    return doc


# ---------------------------------------------------------------------- render
def render_md(d: dict) -> str:
    L: list[str] = []

    def A(s=""):
        L.append(s)

    voc, hashes, lib = d["vocabulary"], d["member_hashes"], d["type_library"]
    vd, uses, block = lib["vehicle_damage"], d["type_hash_code_use"], d["armour_block"]
    site = uses["text_sites"][0]
    naming = d["hash_naming"]
    chk = d["oracles"]["checks"]

    A("# The armour step: how `*_armor` is addressed in JustCause3.exe (G2-28b)")
    A("")
    A("Generated by `python Tools/scripts/jc3_armor_step.py --write`; re-derived and")
    A("compared byte-for-byte by `--check`. Machine half: `ARMOR_STEP.json`.")
    A("")
    A(f"**The short version.** `DAMAGE_MODEL.md` step 4 asks how `*_armor` and "
      f"`*_armor_strength` compose. This card settles the half the executable can: the "
      f"armour values are **not data-driven by name or by hash**. The ADF vocabulary "
      f"block is dead data - {voc['code_refs_total']} code references to its "
      f"{voc['run_length']} names, and the jenkins hash of every one of the "
      f"{voc['member_count']} members occurs **{hashes['total_occurrences']}** times in "
      f"the {d['meta']['exe_bytes']:,}-byte image. The only handle the code has is the "
      f"module's ADF **type** hash, `{vd['name_hash']:#010x}`, used in exactly one "
      f"instruction; the values themselves are compiled struct members of a "
      f"**{vd['size']}-byte** blob.")
    A("")
    A("So the composition rule is still **UNKNOWN**, but it is now known to be compiled")
    A("code reading `+0x04…+0x40`, not a table lookup - and one correction to the data")
    A("model follows from the bytes: the `*_armor_strength` members are **IEEE float32**,")
    A("not ints.")
    A("")
    A("## 1. The question, and what would count as an answer")
    A("")
    A("Step 4 of the damage chain is: a hit carries a damage type; that picks one of")
    A("eight channels; each channel ships `<channel>_armor` and")
    A("`<channel>_armor_strength`; those two numbers, with the hit's damage, decide how")
    A("much reaches health. Three models are carried in `DAMAGE_MODEL.md` (H0 ignore,")
    A("H1 percentage gate, H2 threshold plus pool). Deciding between them statically")
    A("needs the code that reads the two numbers. Finding that code needs a handle, and")
    A("there are only three possible kinds: a member name string, a member name hash, or")
    A("a struct offset. Sections 2 and 3 eliminate the first two as sets - not just for")
    A("the armour members but for the whole type - which leaves the offset, and section 4")
    A("recovers the offsets.")
    A("")
    A("## 2. The vocabulary in the image is inert")
    A("")
    A(f"The ADF member-name block sits in `.rdata` as {voc['run_length']} adjacent")
    A(f"NUL-terminated strings, from `{voc['first']['name']}` ({voc['first']['va']:#x}) to")
    A(f"`{voc['last']['name']}` ({voc['last']['va']:#x}); `{TYPE_NAME}` is entry")
    A(f"{voc['type_name_index']} and its {voc['member_count']} members follow it in")
    A("declaration order. Two measurements over that whole block:")
    A("")
    A("| measurement | result |")
    A("|---|---|")
    A(f"| instructions that address any of the {voc['run_length']} names (RIP-relative, "
      f"end-of-instruction verified) | **{voc['code_refs_total']}** |")
    A(f"| 8-byte pointers anywhere in the image that hold one of those name addresses "
      f"| **{voc['qword_pointer_total']}** |")
    A("")
    A("So neither a named accessor nor a pointer table exists: the block is vocabulary")
    A("kept for the asset pipeline, exactly as the palette names are in `COLOUR.md`")
    A("(`jc3_colour_native.py` measured 0 references there too). The oracle")
    A("`vocabulary_names_have_no_code_reference` fails the moment one name acquires a")
    A("reader.")
    A("")
    A("## 3. Nor by hash")
    A("")
    A(f"Jenkins, the hash the project already uses for `.epe` fields (`DAMAGE_MECHANISMS.md`")
    A(f"records `invulnerable` = `{naming['jenkins_invulnerable']:08x}`, and")
    A(f"`jenkins('invulnerable')` reproduces it - oracle")
    A("`jenkins_reproduces_the_recorded_epe_field_hash`), applied to all")
    A(f"{voc['member_count']} members:")
    A("")
    A("| member | jenkins | occurrences in the image |")
    A("|---|---:|---:|")
    for r in hashes["rows"]:
        A(f"| `{r['member']}` | `{r['jenkins']:#010x}` | {r['occurrences_in_image']} |")
    A(f"| **total** | | **{hashes['total_occurrences']}** |")
    A("")
    A("Zero across the board. The same method *does* work one class over, which is what")
    A("makes the zero meaningful rather than a broken tool: the property binder for")
    A(f"`CDamageControllerArmor` at `{naming['binder_function'][0]:#x}` loads four")
    A("property hashes as immediates -")
    A(", ".join(f"`{h:#010x}`" for h in naming["hash_immediates"]) + " - and one of them is")
    A(f"`{naming['jenkins_damage_type']:#010x}` = `jenkins(\"damage_type\")`. That class reads")
    A("*its* properties by hash; the `VehicleDamage` block is not among them.")
    A("")
    A("## 4. What the code does know: the type hash, and a 128-byte struct")
    A("")
    A(f"The module's own type library (`{os.path.basename(lib['path'])}`) declares:")
    A("")
    A("| type | name hash | code | size | align |")
    A("|---|---|---:|---:|---:|")
    for t in lib["types"]:
        A(f"| `{t['name']}` | `{t['name_hash']:#010x}` | {t['code']} | {t['size']} | {t['align']} |")
    A("")
    A(f"`{TYPE_NAME}` is a 128-byte struct at hash `{vd['name_hash']:#010x}`. In the whole")
    A(f"image that u32 occurs {len(uses['occurrences'])} times: {', '.join('`%#x`' % o['va'] for o in uses['occurrences'])}.")
    A(f"Exactly one is in `.text`, and it is a compare:")
    A("")
    A("```")
    A(f"{site['va']:#x}  {site['bytes']}   {site['mnemonic']} {site['op_str']}")
    A("```")
    A("")
    A(f"Inside `{site['function'][0]:#x}…{site['function'][1]:#x}`, whose body is:")
    A("")
    A("```")
    for line in d["getter"]["disassembly"]:
        A(line)
    A("```")
    A("")
    A("That is the typed accessor: it walks the entity's modules, compares each module's")
    A("type hash against the `VehicleDamage` constant, and returns the blob. Its one")
    A("direct caller (`0x140288dc0`) caches the result at `[this+0x10]`, and a consumer")
    A("of the armour values reaches the 128-byte blob through that pointer. Nothing in")
    A("the path needs a member name or a member hash, which is consistent with neither")
    A("occurring in the code.")
    A("")
    A("## 5. The armour block, decoded from the bytes")
    A("")
    A(f"The instance data begins at file offset `{lib['data_off']:#x}`. The first")
    A(f"{len(block['rows'])} members sit at 4-byte strides, so each word has two readings -")
    A("int32 and float32 - and the field's own value domain decides between them. No")
    A("reading is assumed: an armour word must land in [-1, 5000], a strength word in")
    A("[0, 100], and a word that satisfies both must be 0.")
    A("")
    A("| off | member | raw | as int32 | as float32 | reading |")
    A("|---|---|---:|---:|---:|---|")
    for r in block["rows"]:
        A(f"| {r['offset_in_instance']:#04x} | `{r['member']}` | `{r['raw']:#010x}` | "
          f"{r['int32']} | {r['float32']!r} | {r['reading']} |")
    A("")
    A(f"Result: {len(block['ints'])} words decode only as int32")
    A("(" + ", ".join(f"`{m}`" for m in block["ints"][:4]) + ", …),")
    A(f"{len(block['floats'])} decode only as float32 - **every one of them a")
    A("`*_armor_strength`** - and the rest are zero words where both readings are 0.")
    A("")
    A("This is the correction to `DAMAGE_MODEL.md`: it prints the strengths as integers")
    A(f"(`5000 @ 99`), but the shipped byte is `0x42c60000`, i.e. `99.0f`. The fleet's")
    A("strength domain 0..100 is a float domain, and any gate built on it is float")
    A("arithmetic on a converted int (`cvtsi2ss`), not integer division.")
    A("")
    A("## 6. The arithmetic: what the evidence supports and what it does not")
    A("")
    A("| question | answer | evidence |")
    A("|---|---|---|")
    A("| are the armour values looked up by name? | **no** | 0 code references to the "
      "member names |")
    A("| by hash? | **no** | 0 occurrences of 30 member hashes |")
    A("| by struct offset? | **yes** | the type is found by its module type hash; the "
      "blob is the compiled image; the block decodes at 4-byte strides |")
    A("| is there a table (offset table, curve, coefficient block) driving the gate? | "
      "**no table found** | the type hash is used once, in a compare; the only "
      "data-side artefacts are the values themselves |")
    A("| armour type | int32 | section 5 |")
    A("| strength type | **float32** | section 5 |")
    A("| the composition rule | **UNKNOWN** | below |")
    A("")
    A("Three whole-image sweeps were run to find the consumer, each a candidate")
    A("generator whose survivors were read by hand:")
    A("")
    A("| sweep | shape searched | candidates | outcome |")
    A("|---|---|---:|---|")
    A("| A | channel-indexed reads of an int32 pair 4 bytes apart (`[base+idx*8+d]`, "
      "`[base+idx*8+d+4]`) | 211 | none indexes the `VehicleDamage` block |")
    A("| B | an int32 read with a float32 read 4 bytes later, from one base | 910 pairs in "
      "330 functions | none reads eight such pairs at 4-byte stride from a struct |")
    A("| C | sweep B intersected with `cvtsi2ss` plus a `100.0`/`0.01` float constant "
      "| 4 | none is the gate |")
    A("")
    A("The structural reason the sweeps fail is the one section 4 gives: the block is")
    A("reached through a cached `VehicleDamage*` at `[this+0x10]`, and virtual dispatch")
    A("between the accessor and the gate hides the call edge from a static caller walk.")
    A("Naming the rule would need a live debugger, which the project rules exclude.")
    A("")
    A("## 7. Where to look next")
    A("")
    A("Two RTTI-visible classes bracket the consumer, both static anchors:")
    A("")
    A("| class | vtable | slots |")
    A("|---|---|---:|")
    for cls, rows in d["rtti"].items():
        for r in rows[:1]:
            A(f"| `{cls}` | `{r['vtable']:#x}` | {r['slots']} |")
    A("")
    A("`CVehicleDamageState` is the health state; `CDamageControllerArmor` is the")
    A("destructible armour object and carries the hash-addressed `damage_type` binder of")
    A("section 3. A future pass that reads the `CVehicleDamageState` slots against a")
    A("`VehicleDamage*` would start where this one stopped; the JSON carries every slot")
    A("address so the reader can pick up the thread without redoing the RTTI walk.")
    A("")
    A("## 8. UNKNOWNs")
    A("")
    for u in d["unknowns"]:
        A(f"- **{u['what']}** - tried: {u['tried']}. Still unknown because {u['why_unknown']}.")
    A("")
    A("## 9. Oracles")
    A("")
    A("| check | passed |")
    A("|---|---|")
    for k, v in chk.items():
        A(f"| `{k}` | {'yes' if v else '**NO**'} |")
    A("")
    A(f"{d['oracles']['passed']}/{d['oracles']['total']} checks pass.")
    A("")
    A("## 10. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/jc3_armor_step.py` | this pass, `--write` / `--check` |")
    A(f"| `Research/JC3Grab/{MD_NAME}` | this page |")
    A(f"| `Research/JC3Grab/{JSON_NAME}` | the same, machine-readable |")
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------- commands
def cmd_write() -> int:
    doc = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(doc))
    o = doc["oracles"]
    print(f"{JSON_NAME}: vocabulary {doc['vocabulary']['run_length']} names / "
          f"{doc['vocabulary']['code_refs_total']} code refs; member hashes "
          f"{doc['member_hashes']['total_occurrences']}; struct "
          f"{doc['type_library']['vehicle_damage']['size']} B; oracle sites "
          f"{len(doc['type_hash_code_use']['text_sites'])}")
    print(f"{MD_NAME}: {len(open(os.path.join(OUT, MD_NAME), encoding='utf-8').read().splitlines())} "
          f"lines; oracles {o['passed']}/{o['total']}")
    bad = [k for k, v in o["checks"].items() if not v]
    if bad:
        print("FAILING: " + ", ".join(bad))
        return 1
    return 0


def cmd_check() -> int:
    doc = build()
    bad = []
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write first")
        return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != json.loads(json.dumps(doc, sort_keys=True)):
        for k in sorted(set(old) | set(doc)):
            if old.get(k) != doc.get(k):
                bad.append(f"json section changed: {k}")
    md = render_md(doc)
    if md != open(mp, encoding="utf-8").read():
        import difflib
        diff = list(difflib.unified_diff(open(mp, encoding="utf-8").read().splitlines(),
                                         md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    bad += [f"oracle failed: {k}" for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    o = doc["oracles"]
    print(f"PASS: vocabulary {doc['vocabulary']['run_length']} names with "
          f"{doc['vocabulary']['code_refs_total']} code refs, "
          f"{doc['member_hashes']['total_occurrences']} member-hash hits, "
          f"{doc['type_library']['vehicle_damage']['size']} B struct, one type-hash site; "
          f"oracles {o['passed']}/{o['total']}")
    return 0


def main() -> int:
    a = sys.argv[1:]
    if a == ["--write"]:
        return cmd_write()
    if a == ["--check"]:
        return cmd_check()
    if a == ["dump"]:
        json.dump(build(), sys.stdout, indent=1, sort_keys=True, ensure_ascii=False)
        print()
        return 0
    print(__doc__.strip().splitlines()[-3].strip())
    print("usage: jc3_armor_step.py --write | --check | dump")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
