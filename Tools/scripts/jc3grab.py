"""jc3grab.py - decode JC3 vehicle entities into named values (GRB-G2-2/G2-3).

`jc3index.py` (G2-1) turns any VFS path into (archive, offset, size).  This
script takes it from there:

  1. read the entity's `.ee` out of the archive (patch copy wins),
  2. un-wrap the AAF container and read its SARC directory,
  3. for every inner `.vmodc`, decode it with Gibbed's ConvertAdf into XML and
     walk `<instances>` into flat `instance.member.path = value` rows,
  4. record every other inner file name/size/magic, so the inventory is
     complete even for the files we do not decode.

Value rows keep the XML's own names, which is the whole point: JC3 names what
it stores, so "mass", "spring_strength_base", "friction_multiplier" arrive
labelled instead of as floats at an offset.

Raw decodes stay OUTSIDE the repo (`--raw`, default E:/Modding/_JC3grab);
the repo gets only the derived tables written by `report`.

Usage:
  python jc3grab.py build --entity <dir-or-.ee path>   # one entity (all variants)
  python jc3grab.py build --all [--limit N]            # every vehicle entity
  python jc3grab.py report                             # VOCABULARY.md + ranges
  python jc3grab.py check
  python jc3grab.py summary
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from typing import Iterator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jc3index import DEFAULT_GAME, DEFAULT_OUT, load_index, MOUNT_RANK  # noqa: E402
from eetoc import unaaf, sarc_dir  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
CONVERT = os.path.join(TOOLS, "Gibbed", "Gibbed.JustCause3.ConvertAdf.exe")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")

NUMERIC = {"float", "int8", "int16", "int32", "int64", "uint8", "uint16",
           "uint32", "uint64", "double", "bool"}


# ---------------------------------------------------------------- archive side

def resolve(path: str, rows: list[dict]) -> dict | None:
    hit = [r for r in rows if r["path"].lower() == path.lower().replace("\\", "/")]
    if not hit:
        return None
    return sorted(hit, key=lambda r: MOUNT_RANK[r["mount"]])[-1]


def read_entry(r: dict, game: str) -> bytes:
    arc = os.path.join(game, r["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(r["offset"])
        data = f.read(r["size"])
    if len(data) != r["size"]:
        raise SystemExit(f"short read {len(data)} != {r['size']} for {r['path']}")
    return data


def inner_files(raw: bytes) -> tuple[bytes, list[tuple[str, int, int]]]:
    """Un-AAF an .ee and return its SARC stream plus (name, offset, size)."""
    stream = unaaf(raw)
    return stream, sarc_dir(stream)


# ------------------------------------------------------------------ XML side

def text_of(el: ET.Element) -> str:
    return (el.text or "").strip()


def value_of(el: ET.Element):
    t = el.get("type", "")
    s = text_of(el)
    if t in NUMERIC:
        if s == "":
            return 0
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return s
    return s


def walk(el: ET.Element, prefix: str, out: list[dict]) -> None:
    """Flatten a member tree; unnamed array elements get [i]."""
    idx = 0
    for ch in el:
        if ch.tag != "member":
            continue
        name = ch.get("name")
        if name:
            p = f"{prefix}.{name}" if prefix else name
        else:
            p = f"{prefix}[{idx}]"
            idx += 1
        kids = [k for k in ch if k.tag == "member"]
        if kids:
            walk(ch, p, out)
        else:
            out.append({"path": p, "type": ch.get("type", ""), "value": value_of(ch)})


def parse_instances(xml_path: str) -> list[dict]:
    root = ET.parse(xml_path).getroot()
    insts = root.find("instances")
    modules = []
    if insts is None:
        return modules
    for inst in insts:
        if inst.tag != "instance":
            continue
        name = inst.get("name", "?")
        rows: list[dict] = []
        for mem in inst:
            if mem.tag != "member":
                continue
            mn = mem.get("name", "")
            base = "" if mn == name else mn
            walk(mem, base, rows)
        modules.append({
            "instance": name,
            "type": inst.get("type-name") or inst.get("type", ""),
            "rows": rows,
        })
    return modules


def decode_vmodc(data: bytes, workdir: str, tag: str) -> list[dict] | None:
    """ConvertAdf one module to XML and parse it.  Returns None on failure."""
    src = os.path.join(workdir, tag + ".vmodc")
    dst = os.path.join(workdir, tag + ".xml")
    with open(src, "wb") as f:
        f.write(data)
    r = subprocess.run([CONVERT, "--e", src, dst], capture_output=True)
    if r.returncode != 0 or not os.path.exists(dst):
        return None
    try:
        return parse_instances(dst)
    finally:
        for p in (src, dst):
            try:
                os.remove(p)
            except OSError:
                pass


# ------------------------------------------------------------------ entity

def slug_of(ee_path: str) -> str:
    parent = ee_path.rsplit("/", 1)[0].rsplit("/", 1)[-1]
    stem = ee_path.rsplit("/", 1)[-1]
    return f"{parent}/{stem}"


def grab_ee(ee_path: str, rows: list[dict], opt) -> dict:
    r = resolve(ee_path, rows)
    if r is None:
        raise SystemExit(f"not in index: {ee_path}")
    raw = read_entry(r, opt.game)
    stream, entries = inner_files(raw)
    files = []
    modules = []
    work = os.path.join(RAW, "tmp")
    os.makedirs(work, exist_ok=True)
    for name, off, size in entries:
        blob = stream[off:off + size]
        files.append({
            "path": name,
            "size": size,
            "magic": blob[:4].decode("ascii", "replace") if all(32 <= c < 127 for c in blob[:4]) else blob[:4].hex().upper(),
        })
        if name.endswith(".vmodc"):
            tag = os.path.basename(name)[:-6]
            mods = decode_vmodc(blob, work, tag)
            if mods is None:
                modules.append({"file": name, "error": "convertadf-failed"})
                continue
            for m in mods:
                m["file"] = name
                modules.append(m)
    return {
        "entity": ee_path,
        "source": {"archive": r["archive"], "offset": r["offset"], "size": r["size"]},
        "ee_stream_bytes": len(stream),
        "inner_files": len(files),
        "files": files,
        "modules": modules,
    }


def vehicle_every_ee(rows: list[dict], only: str | None) -> list[str]:
    out = []
    for r in rows:
        p = r["path"]
        if not p.startswith("editor/entities/jc_vehicles/"):
            continue
        if not p.endswith(".ee"):
            continue
        if only and only.lower() not in p.lower():
            continue
        out.append(p)
    return sorted(set(out))


def write_entity(doc: dict, opt) -> str:
    slug = slug_of(doc["entity"]).replace("/", "__")
    d = os.path.join(RAW, "entities")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, slug + ".json")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=0)
    return p


def cmd_build(a) -> int:
    rows = load_index(a.index)
    if a.entity:
        targets = [p for p in vehicle_every_ee(rows, None)
                   if a.entity.replace("\\", "/").lower() in p.lower()
                   or a.entity.replace("\\", "/").lower() == p.rsplit("/", 1)[0].lower()]
        if not targets:
            raise SystemExit(f"no .ee matches {a.entity}")
    else:
        targets = vehicle_every_ee(rows, None)
    if a.limit:
        targets = targets[:a.limit]
    print(f"{len(targets)} .ee to grab")
    index = []
    for i, p in enumerate(targets, 1):
        try:
            doc = grab_ee(p, rows, a)
        except SystemExit as e:
            print(f"[{i}/{len(targets)}] {p}: {e}")
            continue
        outp = write_entity(doc, a)
        ok = sum(1 for m in doc["modules"] if "error" not in m)
        index.append({
            "entity": p,
            "inner_files": doc["inner_files"],
            "modules": ok,
            "errors": len(doc["modules"]) - ok,
            "path": os.path.relpath(outp, RAW).replace("\\", "/"),
        })
        print(f"[{i}/{len(targets)}] {os.path.basename(p)}: "
              f"{doc['inner_files']} files, {ok} modules")
    os.makedirs(RAW, exist_ok=True)
    with open(os.path.join(RAW, "grab_index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, indent=1)
        f.write("\n")
    return 0


# ---------------------------------------------------------------- reporting

def load_all() -> list[dict]:
    d = os.path.join(RAW, "entities")
    if not os.path.isdir(d):
        raise SystemExit(f"nothing grabbed yet under {d}")
    out = []
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                out.append(json.load(f))
    return out


def module_key(m: dict) -> str:
    """Group by instance type where available - that is the schema name."""
    return m.get("type") or m.get("instance") or "(unknown)"


def cmd_report(a) -> int:
    docs = load_all()
    if a.entity:
        docs = [d for d in docs if a.entity.lower() in d["entity"].lower()]

    donor: dict[tuple[str, str], object] = {}
    if a.donor:
        for d in docs:
            if a.donor.lower() in d["entity"].lower():
                for m in d["modules"]:
                    if "error" in m:
                        continue
                    t = module_key(m)
                    for row in m["rows"]:
                        donor[(t, re.sub(r"\[\d+\]", "[]", row["path"]))] = row["value"]
                break
    # catalogue: type -> member path -> type + values across entities
    cat: dict[str, dict[str, dict]] = {}
    for d in docs:
        for m in d["modules"]:
            if "error" in m:
                continue
            t = module_key(m)
            slot = cat.setdefault(t, {})
            for row in m["rows"]:
                p = re.sub(r"\[\d+\]", "[]", row["path"])
                e = slot.setdefault(p, {"type": row["type"], "vals": []})
                v = row["value"]
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    e["vals"].append(v)
                elif isinstance(v, str) and len(e["vals"]) < 400:
                    e["vals"].append(v)

    def stat(vals):
        nums = [v for v in vals if isinstance(v, (int, float))]
        strs = [v for v in vals if isinstance(v, str)]
        if nums:
            nums_sorted = sorted(nums)
            mn, mx = nums_sorted[0], nums_sorted[-1]
            med = nums_sorted[len(nums_sorted) // 2]
            return f"{mn:g} .. {mx:g} (med {med:g}, n={len(nums)})"
        if strs:
            uniq = sorted(set(strs))
            head = ", ".join(uniq[:4])
            more = f" (+{len(uniq) - 4})" if len(uniq) > 4 else ""
            return f"{len(uniq)} strings: {head}{more}"
        return "-"

    lines = ["# JC3 vehicle module vocabulary", "",
             f"Derived from **{len(docs)}** decoded `.ee` entities by `Tools/scripts/jc3grab.py`.",
             "Each block is a module instance type; each row is a member path with its",
             "type and the range seen across every decoded entity.", ""]
    for t in sorted(cat):
        lines.append(f"## `{t}`")
        lines.append("")
        lines.append("| member | type | fleet range | donor |")
        lines.append("|---|---|---|---|")
        for p in sorted(cat[t]):
            e = cat[t][p]
            dv = donor.get((t, p), "")
            lines.append(f"| `{p}` | {e['type']} | {stat(e['vals'])} | {dv} |")
        lines.append("")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "VOCABULARY.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"VOCABULARY.md: {len(cat)} module types, "
          f"{sum(len(v) for v in cat.values())} member paths, from {len(docs)} entities")
    return 0


def cmd_summary(a) -> int:
    docs = load_all()
    tot_inner = sum(d["inner_files"] for d in docs)
    mods = [m for d in docs for m in d["modules"]]
    ok = [m for m in mods if "error" not in m]
    rows = sum(len(m["rows"]) for m in ok)
    print(f"entities {len(docs)}  inner files {tot_inner}  modules {len(ok)}/{len(mods)} "
          f"decoded  value rows {rows}")
    ext: dict[str, int] = {}
    for d in docs:
        for f in d["files"]:
            e = os.path.splitext(f["path"])[1].lower()
            ext[e] = ext.get(e, 0) + 1
    print("inner file types:", ", ".join(f"{k} {v}" for k, v in
          sorted(ext.items(), key=lambda kv: -kv[1])[:14]))
    return 0


def cmd_check(a) -> int:
    """Re-grab the donor entity and assert values the project already relies on."""
    rows = load_index(a.index)
    probe = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
             "v0300_car_kensington_sportsmuscle_civilian_01.ee")
    doc = grab_ee(probe, rows, a)
    problems = []
    if doc["inner_files"] != 566:
        problems.append(f"inner files {doc['inner_files']} != 566")
    ok = [m for m in doc["modules"] if "error" not in m]
    bad = [m for m in doc["modules"] if "error" in m]
    if len(ok) != 30:
        problems.append(f"decoded modules {len(ok)} != 30")
    # the one module ConvertAdf cannot parse is the parts table (G2-7)
    if len(bad) != 1 or not bad[0]["file"].endswith("_vehicle_parts.vmodc"):
        problems.append(f"unexpected failures: {[b['file'] for b in bad]}")

    def find(inst_sub, member):
        for m in ok:
            if inst_sub.lower() in (m["instance"] + " " + m.get("type", "")).lower():
                for r in m["rows"]:
                    if r["path"].endswith(member):
                        return r["value"]
        return None

    # values the project has already acted on (MODLOG §70, land_global 1600 B)
    mass = find("RigidBody", "mass")
    if mass != 975:
        problems.append(f"rigid_body.mass {mass} != 975 (vanilla Serpente)")
    top = find("VehicleMisc", "official_top_speed")
    if top != 250:
        problems.append(f"vehicle_misc.official_top_speed {top} != 250")
    print(f"probe: {doc['inner_files']} inner files, {len(ok)} modules decoded, "
          f"{len(bad)} refused, mass={mass}, official_top_speed={top}")
    if problems:
        for p in problems:
            print("FAIL", p)
        return 1
    print("check ok")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="grab one entity, or --all")
    b.add_argument("--entity", help="vehicle dir or .ee path substring")
    b.add_argument("--all", action="store_true", help="every jc_vehicles .ee")
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--index", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)

    r = sub.add_parser("report", help="write VOCABULARY.md from what is grabbed")
    r.add_argument("--entity", help="restrict to entities matching this substring")
    r.add_argument("--donor", help="entity substring whose values fill the donor column")
    r.set_defaults(func=cmd_report)

    s = sub.add_parser("summary", help="print grab statistics")
    s.set_defaults(func=cmd_summary)

    c = sub.add_parser("check", help="re-grab the donor and assert known values")
    c.add_argument("--game", default=DEFAULT_GAME)
    c.add_argument("--index", default=DEFAULT_OUT)
    c.set_defaults(func=cmd_check)

    a = ap.parse_args()
    if not hasattr(a, "game"):
        a.game = DEFAULT_GAME
    if not hasattr(a, "index"):
        a.index = DEFAULT_OUT
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
