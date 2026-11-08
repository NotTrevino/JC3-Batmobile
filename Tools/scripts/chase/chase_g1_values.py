"""chase_g1_values.py - G1 value chase (chase-03): F-17…F-24 on RVehicleBatmobileBase.

The eight rows are fields the class declares but no shipped archetype serialises
(MODES.md §6), so the only places a value can come from are:

  route 1  a class default the G1 readers skipped - a `Default__*` object in a cooked
           package, a parent-class default, or a value carried by another package
  route 2  the native code in `BatmanAK.exe` - a constructor that sets the field, or a
           function that compares against a literal
  route 3  footage, when the quantity is visible in a capture
  route 4  published sources, as a cross-check only

This tool does 1 and 2 read-only and records what it found, with the address and the
decoded bytes, so the chase doc can cite a measurement instead of a memory.

Route 2 works on the field *offsets* from `BMSDK_OFFSETS.json` / `MODES.md`: property names
live in BmScript (not shipped) and are 0 occurrences in the image, but the compiled code
addresses the fields by displacement, so the strafe block's constructor shows up as a run of
stores to `+11E4h`…`+1208h` in one function.

Usage:
  python chase_g1_values.py packages   # route 1: CDO / parent-default inventory
  python chase_g1_values.py scan       # route 2: displacement-store scan in the .text
  python chase_g1_values.py report     # both, plus the JSON record
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "chase")
GRAB = os.path.join(r"E:\Modding\_gamedata\BmAKgrab", "chase")
EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"
OBJECTS = os.path.join(ROOT, "Research", "BatmobileGrab", "objects.jsonl")
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")

# the eight rows, with the offset MODES.md / BMSDK_OFFSETS.json declares
FIELDS = {
    "F-17": ("StrafeRight", 0x11EC, "Vector3", 12),
    "F-18": ("StrafeForce", 0x11F8, "float", 4),
    "F-19": ("StrafeTorque", 0x11FC, "float", 4),
    "F-20": ("StrafeDuration", 0x1200, "float", 4),
    "F-21": ("StrafeTime", 0x1204, "float", 4),
    "F-22": ("StrafeFwdCorrectionForce", 0x1208, "float", 4),
    "F-23": ("TransformationAnimNode", 0x1494, "AnimNodeSequence", 8),
    "F-24": ("StrafeTarget", 0x14E4, "RVehicle", 8),
}
# the strafe block also holds these, so a constructor should set them in the same run
CONTEXT = {"StrafeCooldown": 0x11E4}


def pe_sections(path: str) -> tuple[bytes, list[dict]]:
    data = open(path, "rb").read()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "not a PE"
    coff = e_lfanew + 4
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    opt = coff + 20
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    sec = opt + opt_size
    sections = []
    for i in range(nsec):
        off = sec + i * 40
        name = data[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
        chars = struct.unpack_from("<I", data, off + 36)[0]
        sections.append({"name": name, "va": va, "vsize": vsize, "raw_size": raw_size,
                         "raw_ptr": raw_ptr, "chars": chars})
    return data, sections


def rva_of(sections: list[dict], file_off: int) -> int | None:
    for s in sections:
        if s["raw_ptr"] <= file_off < s["raw_ptr"] + s["raw_size"]:
            return s["va"] + (file_off - s["raw_ptr"])
    return None


def section_of(sections: list[dict], file_off: int) -> str:
    for s in sections:
        if s["raw_ptr"] <= file_off < s["raw_ptr"] + s["raw_size"]:
            return s["name"]
    return "?"


def is_exec(sections: list[dict], file_off: int) -> bool:
    for s in sections:
        if s["raw_ptr"] <= file_off < s["raw_ptr"] + s["raw_size"]:
            return bool(s["chars"] & 0x20000000)
    return False


def scan_stores(data: bytes, sections: list[dict], disp: int, size: int) -> list[dict]:
    """`C7` = mov r/m32, imm32 and `F3 0F 11` = movss r/m32, xmm. mod=10 => disp32."""
    hits = []
    d = struct.pack("<I", disp)
    for kind, needle in (("mov-imm32", b"\xc7"), ("movss", b"\xf3\x0f\x11")):
        start = 0
        while True:
            i = data.find(needle + b"", start)
            if i < 0:
                break
            start = i + 1
            if not is_exec(sections, i):
                continue
            p = i + len(needle)
            modrm = data[p]
            mod = (modrm >> 6) & 3
            reg = (modrm >> 3) & 7
            rm = modrm & 7
            if mod != 2:
                continue
            if kind == "mov-imm32" and reg != 0:
                continue
            q = p + 1
            if rm == 4:  # SIB
                q += 1
            if data[q:q + 4] != d:
                continue
            if kind == "mov-imm32":
                imm = data[q + 4:q + 4 + size]
                if len(imm) < size:
                    continue
                hits.append({"kind": kind, "file_off": i,
                             "rva": rva_of(sections, i), "section": section_of(sections, i),
                             "bytes": data[i:q + 4 + size].hex(),
                             "imm": int.from_bytes(imm, "little"),
                             "imm_f32": struct.unpack("<f", imm[:4])[0] if size == 4 else None})
            else:
                hits.append({"kind": kind, "file_off": i,
                             "rva": rva_of(sections, i), "section": section_of(sections, i),
                             "bytes": data[i:q + 4].hex(), "imm": None, "imm_f32": None})
    return hits


def route1() -> dict:
    """What the cooked packages hold for these fields, CDOs included."""
    rows = [json.loads(l) for l in open(OBJECTS, encoding="utf-8")]
    cdo = [r for r in rows if str(r.get("name", "")).startswith("Default__")]
    vehicle_cdo = [r for r in cdo if "Vehicle" in str(r.get("class", "")) or
                   "Vehicle" in str(r.get("name", ""))]
    names = {name for name, _o, _t, _s in FIELDS.values()}
    carried = []
    for r in rows:
        tags = r.get("tags") or []
        for t in tags:
            fn = t.get("name") if isinstance(t, dict) else None
            if fn in names:
                carried.append({"package": r.get("package"), "object": r.get("name"),
                                "field": fn})
    declared = json.load(open(OFFSETS, encoding="utf-8")) if os.path.exists(OFFSETS) else {}
    return {
        "packages_scan": len(rows),
        "default_objects": len(cdo),
        "vehicle_class_defaults": [{"package": r["package"], "name": r["name"],
                                    "class": r["class"], "tags": r["tag_count"]}
                                   for r in vehicle_cdo],
        "objects_carrying_a_chased_field": carried,
        "declared_table": type(declared).__name__,
    }


def native_report() -> dict:
    data, sections = pe_sections(EXE)
    out = {"image": EXE, "size": len(data),
           "sections": [{"name": s["name"], "va": hex(s["va"]), "raw": hex(s["raw_ptr"]),
                         "vsize": s["vsize"], "exec": bool(s["chars"] & 0x20000000)}
                        for s in sections],
           "fields": {}}
    for row, (name, off, typ, size) in FIELDS.items():
        hits = scan_stores(data, sections, off, size if size == 4 else 4)
        out["fields"][row] = {"name": name, "offset": hex(off), "type": typ,
                              "name_in_image": data.count(name.encode("ascii")),
                              "hits": hits[:40], "hit_count": len(hits)}
    ctx = {}
    for name, off in CONTEXT.items():
        hits = scan_stores(data, sections, off, 4)
        ctx[name] = {"offset": hex(off), "hit_count": len(hits), "hits": hits[:20]}
    out["context"] = ctx
    return out


def dump(rva: int, length: int) -> None:
    """Hex+ASCII of a window, with the offset stores it contains named."""
    data, sections = pe_sections(EXE)
    target = None
    for s in sections:
        if s["va"] <= rva < s["va"] + s["raw_size"]:
            target = s
            break
    if target is None:
        raise SystemExit(f"rva {rva:#x} is not in a section")
    off = target["raw_ptr"] + (rva - target["va"])
    blob = data[off:off + length]
    for i in range(0, len(blob), 16):
        chunk = blob[i:i + 16]
        hexs = " ".join(f"{b:02x}" for b in chunk)
        print(f"{rva + i:#08x}  {hexs:<48}  " + "".join(
            chr(b) if 32 <= b < 127 else "." for b in chunk))
    print("--- stores in this window ---")
    for row, (name, fo, typ, size) in FIELDS.items():
        for h in scan_stores(blob, [{"name": target["name"], "va": 0,
                                     "raw_ptr": 0, "raw_size": len(blob),
                                     "chars": 0x20000000}], fo, 4):
            print(f"  {row} {name} +{fo:#x} at rva {rva + h['file_off']:#x} imm {h['imm']} "
                  f"f32 {h['imm_f32']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["packages", "scan", "report", "dump"])
    ap.add_argument("rva", nargs="?", type=lambda x: int(x, 0))
    ap.add_argument("length", nargs="?", type=lambda x: int(x, 0), default=256)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(GRAB, exist_ok=True)
    if a.cmd == "dump":
        dump(a.rva, a.length)
        return
    if a.cmd in ("packages", "report"):
        print(json.dumps(route1(), indent=1))
    if a.cmd in ("scan", "report"):
        rep = native_report()
        print(json.dumps({k: rep[k] for k in ("size",)}, indent=1))
        for row, f in rep["fields"].items():
            print(f"{row} {f['name']} +{f['offset']}: name_in_image {f['name_in_image']}, "
                  f"stores {f['hit_count']}")
            for h in f["hits"][:6]:
                print("   ", h["kind"], "rva", hex(h["rva"]) if h["rva"] else None,
                      "imm", h["imm"], "f32", h["imm_f32"], h["bytes"])
        for name, c in rep["context"].items():
            print(f"context {name} +{c['offset']}: {c['hit_count']}")
            for h in c["hits"][:6]:
                print("   ", h["kind"], hex(h["rva"]) if h["rva"] else None, h["imm"],
                      h["imm_f32"])
        with open(os.path.join(GRAB, "g1_chase_native.json"), "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
        print("wrote", os.path.join(GRAB, "g1_chase_native.json"))


if __name__ == "__main__":
    main()
