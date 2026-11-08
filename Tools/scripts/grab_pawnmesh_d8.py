"""grab_pawnmesh_d8.py - G3-02e follow-up: name the float at `[Pawn.Mesh + 0xd8]` that
`0x140063e90` compares against -0.707 / +0.707 in BatmanAK.exe, and say which state it measures.

Static only: the executable is read, the game is never run or attached to.

THREE INDEPENDENT SOURCES, each one able to contradict the others
  1. the layout (`E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated`, plus `BMSDK_OFFSETS.json`):
     `Pawn.Mesh` is at 0x38c and is declared `SkeletalMeshComponent`; the class chain of
     `RVehicleBatmobileBase` reaches `Pawn`, and 0x38c is declared once on that chain. In the
     `SkeletalMeshComponent` -> `MeshComponent` -> `PrimitiveComponent` -> `ActorComponent` ->
     `Component` chain no property *starts* at 0xd8; 0xd8 lies inside
     `PrimitiveComponent.LocalToWorld` (0xb0, 64 bytes, `FMatrix` = XPlane/YPlane/ZPlane/WPlane at
     0/16/32/48 of 16 bytes each), at 0xb0+40 = ZPlane+8 = the Z member of the Z plane.
  2. the comparing function: `mov rax,[rbx+0x38c]` ; `movss xmm1,[rax+0xd8]` ;
     `comiss xmm1,-0.707` ; `comiss xmm1,+0.707` with the branch semantics decoded from the bytes.
  3. the rest of .text: functions that load `[pawn+0x38c]` and then read `[mesh+0xd0]`,
     `[mesh+0xd4]`, `[mesh+0xd8]` as one vector triple (and the same for the rows at 0xb0 and
     0xc0) - a matrix row, not a scalar field. Their compare constants against the same element
     are collected; a cosine stays inside [-1,1].
  4. the sampler logs under `Research/BatmobileGrab/runtime/`: checked for a field that lines up
     (a mesh/matrix key, a sampled value near +-0.707, and the gate fields the sampler does watch).

Outputs (never hand-edited):
  Research/BatmobileGrab/PAWNMESH_D8.json
  Research/BatmobileGrab/PAWNMESH_D8.md

Usage
  uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_pawnmesh_d8.py --write
  uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_pawnmesh_d8.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from grab_controls_native import EXE, Image, fmt_ins  # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
SDK = os.path.join(OUT, "BMSDK_OFFSETS.json")
GEN = r"E:\Modding\_tools\BmSDK-AK\src\BmSDK\Generated"
RUNTIME = os.path.join(OUT, "runtime")
MD = os.path.join(OUT, "PAWNMESH_D8.md")
JS = os.path.join(OUT, "PAWNMESH_D8.json")

IMPL = 0x140063E90            # TryToChangeMode implementation (decoded in G3-02e)
MESH_SLOT = 0x38C             # Pawn.Mesh (decoded in BMSDK_OFFSETS.json)
FLOAT_OFF = 0xD8              # the float under test
COMPARES = {0x140063F04: 0x141BF1CDC, 0x140063F22: 0x141BCE8F8}   # -0.707, +0.707
EPILOGUE_REJECT = 0x140063FBE  # `xor eax,eax` -> return 0
EPILOGUE_ACCEPT = 0x140063FAE  # `mov eax,1`
VEHICLE_CLASS = "RVehicleBatmobileBase"
MESH_CLASS = "SkeletalMeshComponent"
# displacements of the mesh matrix that the rest of .text uses
MATRIX = {"row0": [0xB0, 0xB4, 0xB8, 0xBC], "row1": [0xC0, 0xC4, 0xC8, 0xCC],
          "row2": [0xD0, 0xD4, 0xD8, 0xDC], "row3": [0xE0, 0xE4, 0xE8, 0xEC]}


# ---------------------------------------------------------------- 1. layout: SDK dump
def sdk_chain(sdk: dict, cls: str) -> list[str]:
    out, seen = [], set()
    while cls and cls not in seen and cls in sdk["classes"]:
        seen.add(cls)
        out.append(cls)
        cls = sdk["classes"][cls].get("super")
    return out


def sdk_props_at(sdk: dict, cls: str, off: int) -> list[dict]:
    rows = []
    for c in sdk_chain(sdk, cls):
        for p in sdk["classes"][c].get("properties", []):
            if p.get("offset") == off:
                rows.append({"class": c, "name": p["name"], "kind": p["kind"],
                             "type": p.get("type"), "mask": p.get("mask")})
    return rows


def sdk_section(sdk: dict) -> dict:
    chain = sdk_chain(sdk, VEHICLE_CLASS)
    at_slot = sdk_props_at(sdk, VEHICLE_CLASS, MESH_SLOT)
    pawn = sdk["classes"].get("Pawn", {})
    pawn_mesh = [p for p in pawn.get("properties", []) if p.get("offset") == MESH_SLOT]
    chain_at_float = sdk_props_at(sdk, VEHICLE_CLASS, FLOAT_OFF)
    return {
        "vehicle_chain": chain,
        "pawn_in_chain": "Pawn" in chain,
        "pawn_mesh_entries": [{"name": p["name"], "kind": p["kind"], "type": p.get("type"),
                               "offset": p.get("offset")} for p in pawn_mesh],
        "props_at_mesh_slot_on_vehicle_chain": at_slot,
        "props_at_float_offset_on_vehicle_chain": chain_at_float,
        "sdk_classes": len(sdk["classes"]),
        "mesh_class_present_in_sdk_dump": MESH_CLASS in sdk["classes"],
        "source": SDK,
    }


# ---------------------------------------------------------------- 1b. layout: .g.cs
def parse_gcs(path: str) -> dict:
    """Class name, base, size and every `Ptr + N` property with its `/// <Kind>: name` comment."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    head = "\n".join(lines[:20])
    m_cls = re.search(r"public partial class (\w+) : ([\w\.]+)", head)
    m_size = re.search(r"\(size = (\d+)\)", head)
    # Class-scope property blocks are indented 4 spaces, but a struct declared inside the same
    # file is indented 4 spaces too and its members 8 (and use `paramsPtr` for function params).
    # Such blocks are skipped whole: otherwise a nested struct's offsets are read as class
    # properties and shadow the real member at the same offset.
    props, last, i, SKIP = [], None, 0, re.compile(
        r"^    (public )?(partial )?(record )?struct (\w+)\s*$")
    while i < len(lines):
        line = lines[i]
        if SKIP.match(line):
            i += 1
            while i < len(lines) and lines[i].rstrip() != "    }":
                i += 1
            i += 1
            continue
        c = re.match(r"    /// (\w+): (\w+)$", line)
        if c:
            last = {"kind": c.group(1), "name": c.group(2), "line": i + 1}
            i += 1
            continue
        for n in re.findall(r"(?<!\w)Ptr \+ (\d+)\)", line):
            if last:
                props.append({"offset": int(n), "name": last["name"], "kind": last["kind"],
                              "line": last["line"], "uses": i + 1})
        i += 1
    return {"file": os.path.relpath(path, GEN).replace("\\", "/"),
            "class": m_cls.group(1) if m_cls else None,
            "base": m_cls.group(2).split(".")[-1] if m_cls else None,
            "size": int(m_size.group(1)) if m_size else None,
            "props": props}


def gcs_chain(cls: str) -> list[dict]:
    out, seen, cur = [], set(), cls
    while cur and cur not in seen:
        seen.add(cur)
        path = os.path.join(GEN, "Engine", cur + ".g.cs")
        if not os.path.exists(path):
            path = os.path.join(GEN, "Core", cur + ".g.cs")
        if not os.path.exists(path):
            break
        info = parse_gcs(path)
        out.append(info)
        cur = info["base"]
    return out


def gcs_span(chain: list[dict], off: int) -> dict | None:
    """The property whose [offset, offset+width) contains `off`; width = next start, else class size."""
    for info in chain:
        starts = sorted({p["offset"] for p in info["props"]})
        for p in info["props"]:
            if p["offset"] == off:
                return {"class": info["class"], "name": p["name"], "kind": p["kind"],
                        "offset": p["offset"], "inside": False, "file": info["file"],
                        "line": p["line"]}
        for s in starts:
            nxt = next((x for x in starts if x > s), info["size"])
            if s < off < nxt:
                owner = next(p for p in info["props"] if p["offset"] == s)
                return {"class": info["class"], "name": owner["name"], "kind": owner["kind"],
                        "offset": s, "inside": True, "width": nxt - s, "delta": off - s,
                        "file": info["file"], "line": owner["line"],
                        "next_offset": nxt}
    return None


def layout_section() -> dict:
    chain = gcs_chain(MESH_CLASS)
    span = gcs_span(chain, FLOAT_OFF)
    starts_at_float = [{"class": i["class"], "name": p["name"], "kind": p["kind"]}
                       for i in chain for p in i["props"] if p["offset"] == FLOAT_OFF]
    fmatrix = parse_gcs(os.path.join(GEN, "Core", "GameObject.g.cs"))
    # FMatrix / FPlane live in Core/GameObject.g.cs as record structs; parse them by name
    src = open(os.path.join(GEN, "Core", "GameObject.g.cs"), encoding="utf-8",
               errors="replace").read()
    def struct_block(name: str) -> dict:
        m = re.search(r"record struct %s\s*\{(.*?)\n    \}" % name, src, re.S)
        body = m.group(1) if m else ""
        size = re.search(r"Size = (\d+)", src[max(0, m.start() - 200):m.start()]) if m else None
        members = {}
        for mm in re.finditer(r"/// (\w+): (\w+).*?(?<!\w)Ptr \+ (\d+)\)", body, re.S):
            members[int(mm.group(3))] = mm.group(2)
        # string keys, so the render of a freshly built doc equals the render of the stored JSON
        return {"present": bool(m), "size": int(size.group(1)) if size else None,
                "members": {str(k): v for k, v in sorted(members.items())}}
    return {
        "mesh_class": MESH_CLASS,
        "gcs_chain": [{"class": i["class"], "base": i["base"], "size": i["size"],
                       "file": i["file"]} for i in chain],
        "span_at_float_offset": span,
        "props_starting_at_float_offset": starts_at_float,
        "float_offset": FLOAT_OFF,
        "fmatrix": struct_block("FMatrix"),
        "fplane": struct_block("FPlane"),
        "vehicle_chain_gcs": [
            {"class": i["class"], "base": i["base"], "size": i["size"]}
            for i in (gcs_chain(VEHICLE_CLASS)[:6])],
    }


# ---------------------------------------------------------------- 2. the comparing function
def impl_section(img: Image) -> dict:
    f = img.func_of(IMPL)
    ins = list(img.decode(f[0], f[1]))
    rows = [{"at": x.address, "text": fmt_ins(x)} for x in ins]
    mesh_load = next((x for x in ins if x.mnemonic == "mov" and re.search(
        r"qword ptr \[\w+ \+ 0x38c\]$", x.op_str)), None)
    float_load = next((x for x in ins if x.mnemonic == "movss" and re.search(
        r"\[rax \+ 0xd8\]$", x.op_str)), None)
    compares = []
    for k, x in enumerate(ins):
        if x.mnemonic not in ("comiss", "ucomiss"):
            continue
        m = re.search(r"rip ([+-]) (0x[0-9a-f]+)", x.op_str)
        if not m:
            continue
        d = int(m.group(2), 16) * (1 if m.group(1) == "+" else -1)
        ea = x.address + x.size + d
        if img.sec(ea) != ".rdata":
            continue
        val = struct.unpack_from("<f", img.data, img.fo(ea))[0]
        nxt = ins[k + 1] if k + 1 < len(ins) else None
        tgt = int(nxt.op_str, 16) if nxt and nxt.op_str.startswith("0x") else None
        compares.append({"at": x.address, "text": fmt_ins(x), "const_va": ea,
                         "value": round(val, 6), "next": fmt_ins(nxt) if nxt else None,
                         "branch": nxt.mnemonic if nxt else None,
                         "branch_target": tgt,
                         "target_is_reject": tgt == EPILOGUE_REJECT,
                         "expected_const_va": COMPARES.get(x.address),
                         "operand_is_memory": "ptr [" in x.op_str.split(", ")[-1]})
    gate = []
    for x in ins:
        for off, name in ((0x112C, "MatineeControlRefCount"), (0x11DC, "flags_11DC"),
                          (0x11D8, "flags_11D8"), (0x1D18, "BatmobileStuckTime"),
                          (0x1D20, "BatmobileStuckTimeFlip"), (0x1990, "PreventModeSwitchDuration"),
                          (0x1494, "TransformationAnimNode")):
            if re.search(r"\[\w+ \+ 0x%x\]" % off, x.op_str):
                gate.append({"at": x.address, "text": fmt_ins(x), "offset": off, "field": name})
                break
    return {"function": [f[0], f[1]], "disassembly": rows,
            "mesh_load": fmt_ins(mesh_load) if mesh_load else None,
            "float_load": fmt_ins(float_load) if float_load else None,
            "compares": compares, "gate_reads": gate,
            "epilogues": {"reject": EPILOGUE_REJECT, "accept": EPILOGUE_ACCEPT}}


# ---------------------------------------------------------------- 3. the rest of .text
def mesh_sites(img: Image) -> dict:
    """Every .pdata function that loads [pawn+0x38c] and then touches the mesh matrix."""
    tva, tvs, tpo, trs, _ = img.text
    tb = img.data[tpo:tpo + trs]
    pat = struct.pack("<I", MESH_SLOT)
    hits, i = [], tb.find(pat)
    while i >= 0:
        hits.append(tva + i)
        i = tb.find(pat, i + 1)
    funcs, outside = set(), 0
    for va in hits:
        f = None
        for back in range(2, 8):
            f = img.func_of(va - back) or f
        if f:
            funcs.add(f)
        else:
            outside += 1
    disps = {d for row in MATRIX.values() for d in row}
    reads, d8_sites, triples, loaded = [], [], {}, set()
    for f in sorted(funcs):
        ins = list(img.decode(f[0], f[1]))
        mesh_regs, seen_load = set(), False
        for k, x in enumerate(ins):
            m0 = re.match(r"(\w+), qword ptr \[\w+ \+ 0x38c\]$", x.op_str)
            if x.mnemonic == "mov" and m0:
                mesh_regs.add(m0.group(1))
                seen_load = True
                loaded.add(f)
                continue
            if not seen_load:
                continue
            for dm in re.finditer(r"\[(\w+) \+ (0x[0-9a-f]+)\]", x.op_str):
                reg, off = dm.group(1), int(dm.group(2), 16)
                if reg not in mesh_regs or off not in disps:
                    continue
                if x.mnemonic not in ("movss", "movaps", "movups", "comiss", "ucomiss",
                                      "addss", "subss", "mulss", "movsd"):
                    continue
                rec = {"at": x.address, "in_function": [f[0], f[1]], "text": fmt_ins(x),
                       "offset": off}
                if x.mnemonic in ("comiss", "ucomiss"):
                    # two shapes: `comiss xmm, [rip+const]` (element in a register) and
                    # `comiss xmm, [mesh+0xd8]` with the constant loaded into the other register
                    cm = re.search(r"rip ([+-]) (0x[0-9a-f]+)", x.op_str)
                    if cm:
                        d = int(cm.group(2), 16) * (1 if cm.group(1) == "+" else -1)
                        rec["const_va"] = x.address + x.size + d
                        rec["const"] = round(struct.unpack_from(
                            "<f", img.data, img.fo(rec["const_va"]))[0], 6)
                    else:
                        other = x.op_str.split(", ")[0].strip()
                        for y in reversed(ins[max(0, k - 12):k]):
                            lm = re.match(r"%s, dword ptr \[rip ([+-]) (0x[0-9a-f]+)\]$"
                                          % re.escape(other), y.op_str)
                            if y.mnemonic == "movss" and lm:
                                d = int(lm.group(2), 16) * (1 if lm.group(1) == "+" else -1)
                                rec["const_va"] = y.address + y.size + d
                                rec["const"] = round(struct.unpack_from(
                                    "<f", img.data, img.fo(rec["const_va"]))[0], 6)
                                rec["const_load"] = fmt_ins(y)
                                break
                elif re.search(r"rip ([+-]) (0x[0-9a-f]+)", x.op_str):
                    cm = re.search(r"rip ([+-]) (0x[0-9a-f]+)", x.op_str)
                    d = int(cm.group(2), 16) * (1 if cm.group(1) == "+" else -1)
                    rec["const_va"] = x.address + x.size + d
                    rec["const"] = round(struct.unpack_from(
                        "<f", img.data, img.fo(rec["const_va"]))[0], 6)
                reads.append(rec)
                if off == FLOAT_OFF:
                    d8_sites.append(rec)
        got = {r["offset"] for r in reads if r["in_function"] == [f[0], f[1]]}
        for row, offs in MATRIX.items():
            if all(o in got for o in offs[:3]):
                triples.setdefault(row, []).append(f[0])
    consts = sorted({r["const"] for r in d8_sites if "const" in r})
    return {"mesh_slot": MESH_SLOT, "disp_occurrences": len(hits), "functions": len(funcs),
            "functions_with_mesh_load": len(loaded),
            "outside_functions": outside,
            "matrix_row_triples": {k: [hex(v) for v in vs] for k, vs in triples.items()},
            "d8_reads": d8_sites, "matrix_reads": reads,
            "d8_compare_constants": consts,
            "functions_in_triples": sorted({v for vs in triples.values() for v in vs})}


# ---------------------------------------------------------------- 4. sampler logs
def sampler_section() -> dict:
    files = sorted(glob.glob(os.path.join(RUNTIME, "samples-*.jsonl")))
    keys, near, lines = set(), [], 0
    for path in files:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            lines += 1
            rec = json.loads(line)
            for k, v in rec.get("changed", {}).items():
                keys.add(k)
                if isinstance(v, float) and abs(abs(v) - 0.707) < 2e-3:
                    near.append({"file": os.path.basename(path), "t": rec.get("t"),
                                 "key": k, "value": v})
    meshish = sorted(k for k in keys if re.search(r"mesh|matrix|localtoworld|l2w|upaxis|tilt",
                                                  k, re.I))
    names = ("flags_11D8", "flags_11DC", "PreventModeSwitchDuration")
    gate_keys = sorted({k for k in keys for n in names if k.split(".")[-1] == n})
    return {"files": len(files), "records": lines, "keys": len(keys),
            "mesh_named_keys": meshish,
            "values_near_pm_0707": near,
            "gate_fields_sampled": gate_keys,
            "note": "the sampler's field list is bmak_runtime_sampler.py VEH/PC/PI/GADGETS; "
                    "no mesh or matrix field exists in it"}


# ---------------------------------------------------------------- build
def build() -> dict:
    img = Image(EXE)
    sdk = json.load(open(SDK, encoding="utf-8"))
    lay = layout_section()
    sdksec = sdk_section(sdk)
    imp = impl_section(img)
    sites = mesh_sites(img)
    samp = sampler_section()
    span = lay["span_at_float_offset"]
    fm, fp = lay["fmatrix"], lay["fplane"]
    row2 = sorted(o for o in MATRIX["row2"])
    oracles = {
        "pawn_mesh_is_the_slot": {
            "ok": (sdksec["pawn_in_chain"] and len(sdksec["pawn_mesh_entries"]) == 1
                   and sdksec["pawn_mesh_entries"][0]["offset"] == MESH_SLOT
                   and sdksec["pawn_mesh_entries"][0]["type"] == MESH_CLASS
                   and len(sdksec["props_at_mesh_slot_on_vehicle_chain"]) == 1
                   and sdksec["props_at_mesh_slot_on_vehicle_chain"][0]["name"] == "Mesh"),
            "detail": {"chain": sdksec["vehicle_chain"],
                       "pawn_mesh": sdksec["pawn_mesh_entries"],
                       "at_0x38c_on_chain": sdksec["props_at_mesh_slot_on_vehicle_chain"]},
        },
        "no_property_starts_at_0xd8_in_the_mesh_chain": {
            "ok": not lay["props_starting_at_float_offset"] and span is not None
                  and span["name"] == "LocalToWorld" and span["inside"],
            "detail": {"span": span, "props_starting_at_0xd8":
                       lay["props_starting_at_float_offset"],
                       "chain": [c["class"] for c in lay["gcs_chain"]]},
        },
        "0xd8_is_the_third_float_of_the_local_to_world_z_plane": {
            # decoded: LocalToWorld at 0xb0, width 64, ZPlane at +32, FPlane size 16 with W at +12
            # -> 0xd8 = 0xb0+40 = ZPlane+8, i.e. the plane float between the first two and W
            "ok": (span is not None and span["name"] == "LocalToWorld"
                   and span["class"] == "PrimitiveComponent"
                   and span["delta"] == 40 and fm["size"] == 64 and span["width"] == 64
                   and fm["members"].get("32") == "ZPlane" and fp["size"] == 16
                   and fp["members"].get("12") == "W"
                   and 32 <= span["delta"] < 48 and (span["delta"] - 32) != 12),
            "detail": {"span_offset": span["offset"] if span else None,
                       "delta_from_field": span["delta"] if span else None,
                       "delta_in_zplane": (span["delta"] - 32) if span else None,
                       "fmatrix": fm, "fplane": fp,
                       "rule": "FPlane is 16 bytes with only W declared (+12); the Z member at +8 "
                               "is derived from that size and the W offset, not named in the dump"},
        },
        "compare_constants_are_pm_0_707": {
            "ok": len(imp["compares"]) == 2
                  and all(c["expected_const_va"] == c["const_va"] for c in imp["compares"])
                  and all(abs(abs(c["value"]) - 0.707) < 1e-5 for c in imp["compares"]),
            "detail": [{"at": hex(c["at"]), "const_va": hex(c["const_va"]), "value": c["value"]}
                       for c in imp["compares"]],
        },
        "branch_reject_semantics_are_decoded": {
            # comiss xmm1, const ; jb <reject>  => reject when xmm1 < const (CF set)
            "ok": len(imp["compares"]) == 2
                  and all(c["branch"] == "jb" and c["target_is_reject"] and c["operand_is_memory"]
                          for c in imp["compares"]),
            "detail": [{"at": hex(c["at"]), "branch": c["branch"],
                        "target": hex(c["branch_target"]) if c["branch_target"] else None,
                        "rule": "comiss xmm1,const sets CF when xmm1<const; jb takes CF"}
                       for c in imp["compares"]],
        },
        "mesh_matrix_is_read_as_rows_elsewhere": {
            "ok": all(all(o in [r["offset"] for r in sites["matrix_reads"]]
                          for o in offs[:3]) for offs in MATRIX.values()),
            "detail": {"row_triples": sites["matrix_row_triples"],
                       "rule": "a function that reads [mesh+0xb0],[+0xb4],[+0xb8] (and the same "
                               "for 0xc0 and 0xd0) treats the block as rows of three floats"},
        },
        "d8_compare_constants_stay_inside_unit_range": {
            "ok": bool(sites["d8_compare_constants"])
                  and all(-1.001 <= c <= 1.001 for c in sites["d8_compare_constants"]),
            "detail": {"constants": sites["d8_compare_constants"],
                       "rule": "a cosine of an angle stays in [-1,1]; a distance or a degree "
                               "value would not"},
        },
        "sampler_has_no_mesh_field": {
            "ok": not samp["mesh_named_keys"] and not samp["values_near_pm_0707"],
            "detail": {"files": samp["files"], "records": samp["records"],
                       "keys": samp["keys"], "mesh_named_keys": samp["mesh_named_keys"],
                       "near_pm_0707": samp["values_near_pm_0707"][:5]},
        },
    }
    return {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_pawnmesh_d8.py --write",
        "card": "G3-02e follow-up: the float at [Pawn.Mesh+0xd8] and the state it measures",
        "image": {"path": EXE, "size": len(img.data), "base": hex(img.base)},
        "layout": {"sdk": sdksec, "gcs": lay},
        "comparing_function": imp,
        "text_sites": {k: v for k, v in sites.items() if k != "matrix_reads"},
        "sampler": samp,
        "answer": {
            "slot": "[this+0x38c] = Pawn.Mesh (ComponentProperty, SkeletalMeshComponent)",
            "member": "PrimitiveComponent.LocalToWorld.ZPlane(+8)",
            "member_z_named": "ZPlane.Z (the Z naming is derived: FPlane declares only W at +12)",
            "byte_index": "0xd8 = 0xb0 + 40 = ZPlane(+32) + 8",
            "label": "decoded (layout) + decoded (instruction), meaning derived",
            "state": "the mesh's world orientation: the Z component of the mesh's local +Z (up) "
                     "axis = cos of the angle between the Batmobile's up axis and world up "
                     "(+1 upright, 0 on its side, -1 on its roof)",
        },
        "oracles": oracles,
        "unknowns": [
            "whether the Batmobile's LocalToWorld carries a non-unit Z scale: if it does, the "
            "value is scaleZ*cos(tilt) and the 0.707 thresholds would be scale-relative. The dump "
            "declares the matrix, not how the scale is folded in. Told apart by reading the lengths "
            "of the three LocalToWorld rows on a live mesh.",
            "row-versus-column reading of the element: `FMatrix` is declared as four FPlanes "
            "(XPlane/YPlane/ZPlane/WPlane), so element 10 is ZPlane.Z either way and for an "
            "orthonormal basis the two readings give the same scalar; only the axis naming "
            "(local Z vs world Z) differs and the bytes cannot separate them.",
            "which component of the angle the test means in gameplay terms (pitch-only vs "
            "pitch+roll combined) is not separable from LocalToWorld.Z.Z alone: it is the total "
            "tilt of the up axis, and splitting pitch from roll needs the other elements.",
            "why the -0.707 branch exists (the BatmobileStuckTimeFlip >= BatmobileStuckTime "
            "exemption): the two timer fields are decoded by name, but their writers/tick logic "
            "are not decoded here.",
        ],
    }


# ---------------------------------------------------------------- render
def hx(v):
    return "-" if v is None else "%#x" % v


def render(doc: dict) -> str:
    lay, sdk = doc["layout"]["gcs"], doc["layout"]["sdk"]
    imp, sites, samp = doc["comparing_function"], doc["text_sites"], doc["sampler"]
    span, fm, fp = lay["span_at_float_offset"], lay["fmatrix"], lay["fplane"]
    o = []
    w = o.append
    w("# The float at `[Pawn.Mesh + 0xd8]` (G3-02e follow-up)")
    w("")
    w("Generated by `Tools/scripts/grab_pawnmesh_d8.py --write` from `BatmanAK.exe` (%d bytes, base "
      "%s), `BMSDK_OFFSETS.json` and the BmSDK-AK generated layout. Static only: the game is never "
      "run or attached." % (doc["image"]["size"], doc["image"]["base"]))
    w("")
    w("## Answer")
    w("")
    w("**`[Pawn.Mesh + 0xd8]` is the third float of `PrimitiveComponent.LocalToWorld.ZPlane`** "
      "(`0xd8 = 0xb0 + 40 = ZPlane(+32) + 8`) - the last vector component of the third row of the "
      "mesh component's local-to-world matrix, i.e. the world-Z component of the mesh's own up "
      "(+Z) axis. The dump declares `FPlane` as 16 bytes with only `W` at +12, so the name `Z` "
      "for the float at +8 is derived from that size and offset, not decoded.")
    w("")
    w("- it measures the Batmobile's **orientation relative to world up**: `cos(angle)` between "
      "the mesh's local +Z axis and world +Z. `+1` = upright, `0` = on its side (90 deg), `-1` = "
      "on its roof (180 deg). It is a pose, not a speed, throttle or mode flag.")
    w("- the decoded test in `%s` requires it `>= -0.707` (else reject) and, when "
      "`BatmobileStuckTimeFlip < BatmobileStuckTime`, also `>= +0.707` (else reject): a mode "
      "change is refused when the car is more than 135 deg from upright, and refused when it is "
      "more than 45 deg from upright unless the flip timer has run out." % hx(imp["function"][0]))
    w("")
    w("| step | value | label |")
    w("|---|---|---|")
    w("| `[this+0x38c]` | `Pawn.Mesh`, `ComponentProperty`, type `SkeletalMeshComponent` (%d) | "
      "decoded (BMSDK_OFFSETS.json Pawn.Mesh offset 908; unique at the slot on the "
      "`RVehicleBatmobileBase` chain) |" % MESH_SLOT)
    w("| mesh class | `SkeletalMeshComponent` -> `MeshComponent` -> `PrimitiveComponent` -> "
      "`ActorComponent` -> `Component` | decoded (.g.cs base clauses) |")
    w("| member at `0xd8` | `%s` at `%s`, `%s`, width %s - `0xd8` is *inside* it at +%s | "
      "decoded (%s:%s) |" % (span["name"], hx(span["offset"]), span["kind"], span["width"],
                             span["delta"], span["file"], span["line"]))
    w("| offset inside the matrix | `0xd8 - 0xb0 = 40 = ZPlane(+32) + 8` | decoded (FMatrix size "
      "%s, planes at %s; FPlane size %s, W at %s - so +8 is the plane's third vector component) |"
      % (fm["size"], fm["members"], fp["size"], fp["members"]))
    w("| what it is | cos of the tilt of the mesh's up axis against world up | derived (a unit "
      "basis row's Z component is the cosine of that axis against world Z) |")
    w("")
    w("No property *starts* at `0xd8` anywhere in the mesh's class chain")
    w("(%s), so there is one candidate span and no rival field at that offset."
      % ", ".join("`%s`" % c["class"] for c in lay["gcs_chain"]))
    w("")
    w("## 1. The layout chain (decoded)")
    w("")
    w("| class | base | size | file |")
    w("|---|---|---|---|")
    for c in lay["gcs_chain"]:
        w("| `%s` | `%s` | %s | `%s` |" % (c["class"], c["base"], c["size"], c["file"]))
    w("")
    w("`Pawn.Mesh`: %s." % json.dumps(sdk["pawn_mesh_entries"]))
    w("")
    w("Classes of the vehicle chain (BMSDK_OFFSETS.json): %s - `Mesh` is declared once at `0x38c` "
      "on it: %s." % (" -> ".join("`%s`" % c for c in sdk["vehicle_chain"]),
                      json.dumps(sdk["props_at_mesh_slot_on_vehicle_chain"])))
    w("")
    w("The mesh's own fields in the .g.cs chain: %d class(es), and the properties whose span "
      "contains `0xd8`: one (`%s.%s`). Properties starting exactly at `0xd8`: %d."
      % (len(lay["gcs_chain"]), span["class"], span["name"],
         len(lay["props_starting_at_float_offset"])))
    w("")
    w("```")
    w("PrimitiveComponent.g.cs:%d  StructProperty: LocalToWorld  (FMatrix, 64 bytes, at 0x%x)"
      % (span["line"], span["offset"]))
    w("  +0x00 XPlane (16)   +0x10 YPlane (16)   +0x20 ZPlane (16)   +0x30 WPlane (16)")
    w("  FPlane: +12 W only, so the plane float at +8 is the third vector component (Z)")
    w("  0xd8 - 0xb0 = 0x28 = 40 = 0x20 (ZPlane) + 8")
    w("```")
    w("")
    w("## 2. The comparing function `%s` (decoded)" % hx(imp["function"][0]))
    w("")
    w("- `%s`" % imp["mesh_load"])
    w("- `%s`" % imp["float_load"])
    for c in imp["compares"]:
        w("- `%s` -> `%s` = %s ; `%s` -> %s" % (c["text"], hx(c["const_va"]), c["value"],
                                               c["next"], "reject (return 0)"
                                               if c["target_is_reject"] else "fall through"))
    w("")
    w("Branch rule: `comiss xmm1, const` sets CF when `xmm1 < const`, and `jb` takes CF, so each "
      "row above rejects *below* its constant (%s)." %
      ", ".join("%s at %s" % (c["value"], hx(c["at"])) for c in imp["compares"]))
    w("")
    w("Other vehicle fields the same function reads around the test (decoded, named from the "
      "class chain):")
    w("")
    w("| at | instruction | offset | field |")
    w("|---|---|---|---|")
    for g in imp["gate_reads"]:
        w("| %s | `%s` | %s | `%s` |" % (hx(g["at"]), g["text"], hx(g["offset"]), g["field"]))
    w("")
    w("## 3. The same element read elsewhere in .text (decoded)")
    w("")
    w("The displacement bytes `8c 03 00 00` occur %d time(s) in .text, inside %d .pdata function(s) "
      "(%d occurrence(s) outside every .pdata function); %d of those functions really contain a "
      "`mov reg, [x+0x38c]` load. The %d read(s) below are those that follow such a load on the "
      "loaded register." % (sites["disp_occurrences"], sites["functions"],
                             sites["outside_functions"], sites["functions_with_mesh_load"],
                             len(sites["d8_reads"])))
    w("")
    w("| matrix row | displacements | functions reading all three |")
    w("|---|---|---|")
    for row, vs in sites["matrix_row_triples"].items():
        w("| `%s` | %s | %d (%s) |" % (row, ", ".join(hx(x) for x in MATRIX[row][:3]),
                                       len(vs), ", ".join(vs[:6])))
    w("")
    w("Every read of the `0xd8` element after a `[pawn+0x38c]` load:")
    w("")
    w("| at | function | instruction | compared constant |")
    w("|---|---|---|---|")
    for r in sites["d8_reads"]:
        w("| %s | %s | `%s` | %s |" % (hx(r["at"]), hx(r["in_function"][0]), r["text"],
                                       r.get("const", "-")))
    w("")
    w("A `-` in the last column means the comparison happens on a register copy: the constant is "
      "then in an instruction that does not name the mesh (that is the case for the primary site "
      "`0x140063efc`, whose two constants are decoded in section 2).")
    w("")
    w("Constants compared against this element anywhere in .text: %s - all inside `[-1, 1]`, "
      "which a cosine satisfies and a distance or a degree value would not." %
      ", ".join(str(c) for c in sites["d8_compare_constants"]))
    w("")
    w("## 4. The sampler logs (checked, nothing lines up for this float)")
    w("")
    w("- files: %d, records: %d, distinct keys: %d (`%s`)"
      % (samp["files"], samp["records"], samp["keys"], RUNTIME))
    w("- keys naming a mesh/matrix/LocalToWorld/up-axis/tilt: %d %s"
      % (len(samp["mesh_named_keys"]), samp["mesh_named_keys"] or ""))
    w("- sampled float values within 2e-3 of +-0.707: %d" % len(samp["values_near_pm_0707"]))
    w("- %s" % samp["note"])
    w("- the sampler does watch part of the same gate: `veh*.flags_11D8` (bit `0x2` = "
      "`ArmouredMode`, tested at `0x140063f45`) and `veh*.PreventModeSwitchDuration` (`0x1990`, "
      "compared to 0 at `0x140063f7e`), so the gate's other inputs are observable - only the mesh "
      "element is not sampled.")
    w("")
    w("## Oracles (each can fail; `--check` re-runs them)")
    w("")
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k, v in doc["oracles"].items():
        w("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:400]))
    w("")
    w("## If the layout had given two candidates")
    w("")
    w("It gives one span, so the answer is not split. The two readings that remain and cannot be "
      "separated from the bytes are listed as UNKNOWN: (a) whether `LocalToWorld` carries a "
      "non-unit Z scale - told apart by reading the row lengths live; (b) whether the element is "
      "read as \"local Z in world\" or \"world Z in local\" - for an orthonormal basis both are "
      "the same scalar, told apart only by naming the axes against a live rotation.")
    w("")
    w("## UNKNOWN")
    w("")
    for i, u in enumerate(doc["unknowns"], 1):
        w("%d. %s" % (i, u))
    w("")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    md = render(doc)
    if a.write:
        with open(JS, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False)
        with open(MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote PAWNMESH_D8.md and PAWNMESH_D8.json")
        print("member:", doc["answer"]["member"])
        print("compares:", [(hex(c["at"]), c["value"]) for c in doc["comparing_function"]["compares"]])
        print("d8 read sites:", len(doc["text_sites"]["d8_reads"]),
              "row triples:", {k: len(v) for k, v in doc["text_sites"]["matrix_row_triples"].items()})
        print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
        return 0
    fails = []
    if not (os.path.exists(MD) and os.path.exists(JS)):
        print("FAIL: outputs missing - run --write")
        return 1
    stored = json.load(open(JS, encoding="utf-8"))
    if json.dumps(stored, sort_keys=True) != json.dumps(doc, sort_keys=True):
        fails.append("re-derivation differs from PAWNMESH_D8.json")
    if open(MD, encoding="utf-8").read() != render(stored):
        fails.append("PAWNMESH_D8.md is not the render of the JSON")
    for k, v in stored["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(v["detail"])[:200]))
    if stored["answer"]["member"] != "PrimitiveComponent.LocalToWorld.ZPlane(+8)":
        fails.append("answer no longer names the matrix element")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK: %s ; %d compare(s) ; %d d8 read site(s) ; oracles all true"
          % (stored["answer"]["member"], len(stored["comparing_function"]["compares"]),
             len(stored["text_sites"]["d8_reads"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
