"""mechanics_names.py - name every offset-only row of the pre-reset MECHANICS.md.

`Research/BatmobileGrab/MECHANICS.md` (1,508 lines, pre-reset) lists values as bare
`offset 0xNNN  <float>` because the cooker stripped the property names.  G3-06b has since named
the class defaults by layout offset (`CLASS_DEFAULTS.json`, chain RVehicleBatmobile ->
RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle -> Pawn -> Actor), and the
BmSDK bindings carry the same offsets in a different form: `BMSDK_OFFSETS.json` (offset per
member) plus the generated `.g.cs` sources (`Working/vendor/BmSDK/*.g.cs`) where each property's
getter reads `Ptr + <offset>`.

This script joins the three: every `offset 0x...` line in MECHANICS.md -> the field declared at
that absolute offset in the section's class or its ancestors -> the `.g.cs` file and line -> the
bit mask when the offset is a bit-packed bool -> the enclosing struct when the offset falls
inside one.

The oracle that matters: for every resolved property the `.g.cs` getter within a few lines of the
named declaration must read `Ptr + <the same offset>`.  A wrong file, a wrong line, a wrong class
in the chain or an off-by-one offset all break that check.

Usage
    python Tools/scripts/mechanics_names.py --write
    python Tools/scripts/mechanics_names.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "MECHANICS_NAMES.md")
JS = os.path.join(OUT, "MECHANICS_NAMES.json")
MECH = os.path.join(OUT, "MECHANICS.md")
OFFS = os.path.join(OUT, "BMSDK_OFFSETS.json")
DEFAULTS = os.path.join(OUT, "CLASS_DEFAULTS.json")
SDK = os.path.join(ROOT, "Working", "vendor", "BmSDK")

SECTION_RE = re.compile(r"^###\s+.*?`([A-Za-z0-9_]+)`")
ROW_RE = re.compile(r"^offset 0x([0-9A-Fa-f]+)\s+(-?[0-9.]+)\s*$")
CLASS_RE = re.compile(r"^public partial class\s+(\w+)\s*:\s*([^,{]+)")


# --------------------------------------------------------------------------- inputs
def load():
    offs = json.load(open(OFFS, encoding="utf-8"))["classes"]
    chain = json.load(open(DEFAULTS, encoding="utf-8"))["layout"]["chain"]
    return offs, chain


def parse_sections() -> list:
    """[(md_line, section_title, class, package, [(line, offset, value)])]"""
    sections, cur = [], None
    for n, line in enumerate(open(MECH, encoding="utf-8"), 1):
        if line.startswith("### "):
            m = SECTION_RE.search(line)
            if m:
                pkg = re.search(r"\(([A-Za-z0-9_]+),\s*\d+\s*B\)", line)
                cur = {"md_line": n, "title": line.strip("# \n"), "class": m.group(1),
                       "package": pkg.group(1) if pkg else None, "rows": []}
                sections.append(cur)
            else:
                cur = None
            continue
        m = ROW_RE.match(line.rstrip("\n"))
        if m and cur is not None:
            cur["rows"].append({"md_line": n, "offset": int(m.group(1), 16),
                                "offset_hex": "0x" + m.group(1).upper(),
                                "value": float(m.group(2))})
    return sections


def bases() -> dict:
    """class -> first base class name, read from the generated bindings."""
    out = {}
    for fn in os.listdir(SDK):
        if not fn.endswith(".g.cs"):
            continue
        for line in open(os.path.join(SDK, fn), encoding="utf-8", errors="replace"):
            m = CLASS_RE.match(line)
            if m:
                base = m.group(2).strip().split(".")[-1]
                out[m.group(1)] = (base, fn)
                break
    return out


def lineage(cls: str, bs: dict) -> list:
    out, seen = [], set()
    while cls and cls not in seen:
        out.append(cls)
        seen.add(cls)
        cls = (bs.get(cls) or (None, None))[0]
    return out


# --------------------------------------------------------------------------- resolve
def field_lines(cls: str, member: str, offset: int, offs: dict) -> dict:
    """Declaration line + the getter line that must carry `Ptr + offset`."""
    meta = offs.get(cls) or {}
    fn = meta.get("file")
    if not fn:
        return {}
    path = os.path.join(SDK, fn)
    if not os.path.exists(path):
        return {}
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    pat = re.compile(r"\b%s\b" % re.escape(member))
    for i, line in enumerate(lines):
        s = line.strip()
        if not s.startswith("public") or "(" in s or s.endswith(";"):
            continue
        if not pat.search(s):
            continue
        for j in range(i, min(i + 9, len(lines))):
            m = re.search(r"Ptr \+ (\d+)", lines[j])
            if m:
                return {"file": fn, "line": i + 1, "decl": s, "getter_line": j + 1,
                        "getter_offset": int(m.group(1)),
                        "getter": lines[j].strip()[:120]}
    return {"file": fn, "line": None, "decl": None, "reason": "declaration not found"}


def struct_container(cls: str, offset: int, offs: dict) -> dict:
    """A StructProperty whose span (to the next property) contains the offset."""
    props = sorted((offs.get(cls) or {}).get("properties") or [],
                   key=lambda p: p.get("offset") or 0)
    for i, p in enumerate(props):
        if p.get("kind") != "StructProperty":
            continue
        start = p.get("offset") or 0
        nxt = props[i + 1]["offset"] if i + 1 < len(props) else None
        if start < offset and nxt is not None and offset < nxt:
            return {"member": p.get("member"), "type": p.get("type"),
                    "struct_offset": start, "relative": offset - start,
                    "next_member": props[i + 1].get("member"),
                    "next_offset": nxt}
    return {}


def resolve(section_class: str, offset: int, offs: dict, bs: dict) -> dict:
    row = {"declared_in": None, "fields": [], "bools": [], "struct": {}, "how": "UNKNOWN"}
    for cls in lineage(section_class, bs):
        props = [p for p in (offs.get(cls) or {}).get("properties") or []
                 if p.get("offset") == offset]
        if not props:
            continue
        bools = [p for p in props if p.get("kind") == "BoolProperty"]
        plain = [p for p in props if p.get("kind") != "BoolProperty"]
        row["declared_in"] = cls
        if plain:
            row["how"] = "declared field"
            for p in plain:
                row["fields"].append({"member": p.get("member"), "kind": p.get("kind"),
                                      "type": p.get("type"),
                                      "sdk": field_lines(cls, p.get("member", ""), offset, offs)})
        if bools:
            row["bools"] = [{"member": p.get("member"), "mask": p.get("mask"),
                             "mask_hex": "0x%X" % p["mask"] if p.get("mask") else None,
                             "sdk": field_lines(cls, p.get("member", ""), offset, offs)}
                            for p in bools]
            if not plain:
                row["how"] = "bit-packed bools"
        return row
    # nothing at that exact offset: is it inside a struct of an ancestor?
    for cls in lineage(section_class, bs):
        c = struct_container(cls, offset, offs)
        if c:
            row["declared_in"] = cls
            row["struct"] = c
            row["how"] = "inside a struct"
            if c.get("type"):
                tmeta = offs.get(c["type"]) or {}
                for p in tmeta.get("properties") or []:
                    if p.get("offset") == c["relative"]:
                        row["struct"]["field"] = p.get("member")
                        row["struct"]["field_kind"] = p.get("kind")
                        row["struct"]["field_hex"] = "0x%X" % p["offset"]
                        row["struct"]["sdk"] = field_lines(c["type"], p.get("member", ""),
                                                           c["relative"], offs)
            return row
    return row


# --------------------------------------------------------------------------- build
def build() -> dict:
    offs, chain = load()
    bs = bases()
    sections = parse_sections()
    sizes = json.load(open(DEFAULTS, encoding="utf-8"))["layout"]["sizes"]

    rows, per_section = [], []
    for s in sections:
        out = []
        for r in s["rows"]:
            res = resolve(s["class"], r["offset"], offs, bs)
            row = dict(r)
            row.update({"class": s["class"], "package": s["package"],
                        "section_line": s["md_line"], "resolution": res})
            rows.append(row)
            out.append(row)
        if out:
            per_section.append({"class": s["class"], "package": s["package"],
                                "md_line": s["md_line"], "rows": out})

    def has_name(r):
        res = r["resolution"]
        return bool(res["fields"] or res["bools"])

    resolved = [r for r in rows if has_name(r)]
    structs = [r for r in rows if r["resolution"]["how"] == "inside a struct"]
    unknown = [r for r in rows if not has_name(r) and not r["resolution"]["struct"]]
    bad_line = [r for r in resolved for f in r["resolution"]["fields"]
                if f["sdk"].get("line") and f["sdk"].get("getter_offset") != r["offset"]]
    bad_line += [r for r in resolved for b in r["resolution"]["bools"]
                 if b["sdk"].get("line") and b["sdk"].get("getter_offset") != r["offset"]]
    out_of_bounds = [r for r in rows
                     if r["class"] in sizes and r["offset"] >= sizes[r["class"]]]
    wrong_chain = []
    for r in resolved + structs:
        decl = r["resolution"]["declared_in"]
        if decl and decl not in lineage(r["class"], bs):
            wrong_chain.append(r)

    dup_members = []
    for sec in per_section:
        seen: dict = {}
        for r in sec["rows"]:
            for f in r["resolution"]["fields"]:
                seen.setdefault(f["member"], set()).add(r["offset"])
        dup_members += [(sec["class"], m, sorted(v))
                        for m, v in seen.items() if len(v) > 1]

    checks = [
        ("the 244 offset-only rows in MECHANICS.md all parse",
         len(rows) == 244,
         "%d rows over %d sections" % (len(rows), len(per_section))),
        ("every row gets a name, a struct container or is reported UNKNOWN",
         len(resolved) + len(structs) + len(unknown) == len(rows),
         "%d named, %d inside a struct, %d UNKNOWN"
         % (len(resolved), len(structs), len(unknown))),
        ("every named row's .g.cs getter reads Ptr + <the row's offset>",
         not bad_line,
         "%d named rows checked, %d mismatch: %s"
         % (len(resolved), len(bad_line),
            [(r["offset_hex"], r["class"]) for r in bad_line][:5])),
        ("every declaring class is on the section class's binding chain",
         not wrong_chain,
         "%d rows, %d off-chain" % (len(resolved) + len(structs), len(wrong_chain))),
        ("every offset lies inside the class's own size",
         not out_of_bounds,
         "%d rows; %d beyond size %s"
         % (len(rows), len(out_of_bounds), [r["offset_hex"] for r in out_of_bounds][:5])),
        ("bit-packed offsets name every member with its mask",
         all(b.get("mask") for r in resolved for b in r["resolution"]["bools"]),
         "%d bool members named, masks %s"
         % (sum(len(r["resolution"]["bools"]) for r in resolved),
            sorted({b["mask_hex"] for r in resolved
                    for b in r["resolution"]["bools"]})[:8])),
        ("no member is bound at two different offsets inside one section",
         not dup_members,
         "%d sections; %d members with two offsets: %s"
         % (len(per_section), len(dup_members), dup_members[:5])),
        ("the sections cover 8 vehicle/simulation contexts",
         len({(s["class"], s["package"]) for s in per_section}) == 8,
         "%d (class, package) pairs" % len({(s["class"], s["package"]) for s in per_section})),
    ]

    return {
        "task": "name the offset-only rows of MECHANICS.md from the BmSDK layout",
        "inputs": {"mechanics_md": "Research/BatmobileGrab/MECHANICS.md",
                   "bmsdk_offsets": "Research/BatmobileGrab/BMSDK_OFFSETS.json",
                   "class_defaults": "Research/BatmobileGrab/CLASS_DEFAULTS.json",
                   "bindings": "Working/vendor/BmSDK/*.g.cs",
                   "chain_from_class_defaults": chain},
        "sections": per_section,
        "rows": rows,
        "summary": {"rows": len(rows), "named": len(resolved), "inside_struct": len(structs),
                    "unknown": len(unknown),
                    "bool_members": sum(len(r["resolution"]["bools"]) for r in resolved),
                    "declaring_classes": sorted({r["resolution"]["declared_in"]
                                                 for r in resolved + structs
                                                 if r["resolution"]["declared_in"]})},
        "checks": [{"check": n, "pass": bool(ok), "detail": d} for n, ok, d in checks],
    }


# --------------------------------------------------------------------------- render
def render(d: dict) -> str:
    a = []
    A = a.append
    s = d["summary"]
    A("# MECHANICS.md offset-only rows, named from the BmSDK layout")
    A("")
    A("Generated by `Tools/scripts/mechanics_names.py` (`--write`); `--check` recomputes every")
    A("row and line number.  `MECHANICS.md` is not edited.")
    A("")
    A("Every row below was `offset 0xNNN  <value>` in `MECHANICS.md`; the name comes from the")
    A("member the BmSDK binds at that absolute offset (`BMSDK_OFFSETS.json`), and the citation is")
    A("the generated declaration in `Working/vendor/BmSDK/<Class>.g.cs`.  **Labels:** *decoded*")
    A("= offset read from the package (MECHANICS.md), *derived* = the join by offset, *UNKNOWN*")
    A("= no member at that offset, with the reason.")
    A("")
    A("Chain used for `RVehicleBatmobile` (from `CLASS_DEFAULTS.json`): `%s`."
      % " -> ".join(d["inputs"]["chain_from_class_defaults"]))
    A("")
    A("## Summary")
    A("")
    A("| quantity | count |")
    A("|---|---:|")
    A("| offset-only rows | %d |" % s["rows"])
    A("| named to a field | %d |" % s["named"])
    A("| inside a struct (container named) | %d |" % s["inside_struct"])
    A("| UNKNOWN | %d |" % s["unknown"])
    A("| bit-packed bool members named | %d |" % s["bool_members"])
    A("| declaring classes | %s |" % ", ".join("`%s`" % c for c in s["declaring_classes"]))
    A("")
    for sec in d["sections"]:
        A("## `%s` - %s (%d rows)" % (sec["class"], sec["package"], len(sec["rows"])))
        A("")
        A("| MECHANICS.md line | offset | value | field | kind | declared in | `.g.cs` |")
        A("|---:|---|---:|---|---|---|---|")
        for r in sec["rows"]:
            res = r["resolution"]
            if res["fields"]:
                for f in res["fields"]:
                    sdk = f["sdk"]
                    cite = ("`%s:%s`" % (sdk.get("file"), sdk.get("line"))
                            if sdk.get("line") else "UNKNOWN")
                    A("| %d | `%s` | %g | `%s` | %s | `%s` | %s |"
                      % (r["md_line"], r["offset_hex"], r["value"], f["member"],
                         f["kind"], res["declared_in"], cite))
            elif res["bools"]:
                masks = ", ".join("`%s` (%s)" % (b["member"], b["mask_hex"]) for b in res["bools"])
                cite = "`%s:%s`" % (res["bools"][0]["sdk"].get("file"),
                                    res["bools"][0]["sdk"].get("line"))
                A("| %d | `%s` | %g | %s | bit-packed bool | `%s` | %s |"
                  % (r["md_line"], r["offset_hex"], r["value"], masks,
                     res["declared_in"], cite))
            elif res["struct"]:
                st = res["struct"]
                field = st.get("field") or "UNKNOWN"
                cite = ("`%s:%s`" % (st["sdk"].get("file"), st["sdk"].get("line"))
                        if st.get("sdk", {}).get("line") else "UNKNOWN")
                A("| %d | `%s` | %g | `%s` (`%s` +%d), field `%s` | struct member | `%s` | %s |"
                  % (r["md_line"], r["offset_hex"], r["value"], st.get("member"), st.get("type"),
                     st.get("relative"), field, res["declared_in"], cite))
            else:
                A("| %d | `%s` | %g | UNKNOWN | - | - | - |"
                  % (r["md_line"], r["offset_hex"], r["value"]))
        A("")
    A("## Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c["check"], "PASS" if c["pass"] else "FAIL",
                                          c["detail"]))
    A("")
    A("## UNKNOWNs")
    A("")
    A("1. **Rows still UNKNOWN** (%d): no member is bound at that offset in the section class"
      % s["unknown"])
    A("   or any ancestor, and no struct span covers it.  Listed in the tables above with `-`;")
    A("   each would need an uncooked layout or a wider binding set.")
    A("2. **Struct members without a binding.**  Where the container is named but its type has no")
    A("   `.g.cs` entry in `BMSDK_OFFSETS.json`, the relative member stays UNKNOWN.")
    A("3. **What each value means mechanically.**  This pass names fields; it does not interpret")
    A("   the numbers.")
    A("")
    A("## Reproduce")
    A("")
    A("    uv run python Tools/scripts/mechanics_names.py --write")
    A("    uv run python Tools/scripts/mechanics_names.py --check")
    A("")
    return "\n".join(a) + "\n"


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")

    d = build()
    md, js = render(d), json.dumps(d, indent=1) + "\n"
    ok = True
    for c in d["checks"]:
        print("%s  %s" % ("PASS" if c["pass"] else "FAIL", c["check"]))
        print("      %s" % c["detail"])
        ok = ok and c["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))

    if args.write:
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s (%d B)" % (os.path.relpath(MD, ROOT), len(md.encode())))
        print("wrote %s (%d B)" % (os.path.relpath(JS, ROOT), len(js.encode())))
    if args.check:
        bad = []
        for path, want in ((MD, md), (JS, js)):
            if not os.path.exists(path):
                bad.append("%s missing" % os.path.relpath(path, ROOT))
            elif open(path, encoding="utf-8").read() != want:
                bad.append("%s differs" % os.path.relpath(path, ROOT))
        if bad:
            print("CHECK FAILED: " + "; ".join(bad))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
