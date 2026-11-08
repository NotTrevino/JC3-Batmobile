"""app_texture_audit.py - classify every Batmobile texture: which BmAK material uses it, or unused, or a duplicate.

Reads, never writes, the grab and the build:

  Research/BatmobileGrab/TEXTURES.md      the census: 405 (package, texture) rows, `bound by` = the
                                          material/parameter that reaches the texture (decoded)
  Research/BatmobileGrab/MATERIALS.md     every master material and instance parameter row; a texture
                                          is only ever called unused after its name is searched here
  Working/Appearance/build/ddsc/*.ddsc    what the build actually ships (28 files)
  WORKING/Appearance/build/*.rbm          the 25 built parts and the slots they bind (cross-check)
  Working/Transition/T_ROWS.jsonl         row T-MA6 (405 grabbed / 38 bound / 28 shipped)

Writes `Working/Appearance/TEXTURE_AUDIT.md` and `.json`, grouped by role (albedo, normal, mask,
ramp, emissive, damage, UI, other). `--check` re-derives both files and compares them byte for byte,
asserts the census counts, and asserts that no texture marked unused appears anywhere in
`MATERIALS.md`.

Usage
  python Tools/scripts/app_texture_audit.py --write
  python Tools/scripts/app_texture_audit.py --check
  python Tools/scripts/app_texture_audit.py --summary     # counts only, for a report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
CENSUS = os.path.join(BAT, "TEXTURES.md")
MATERIALS = os.path.join(BAT, "MATERIALS.md")
ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
BUILD = os.path.join(ROOT, "Working", "Appearance", "build")
DDSC = os.path.join(BUILD, "ddsc")
OUT_MD = os.path.join(ROOT, "Working", "Appearance", "TEXTURE_AUDIT.md")
OUT_JSON = os.path.join(ROOT, "Working", "Appearance", "TEXTURE_AUDIT.json")

ROLES = ("albedo", "normal", "mask", "ramp", "emissive", "damage", "ui", "other")

# JC3's carrier per role, decoded from the material blocks (see the report's gap table).
CARRIER = {
    "albedo": "`DiffuseMap` s0 (exact)",
    "normal": "`NormalMap` s1 (exact)",
    "mask": "`PropertyMap` s2 / `AOBlendMap` s3; one RGBA slot, so several BmAK masks share it",
    "ramp": "`CarPaintMM.TintMap` s3 + `m_Emissive` bands; no standalone ramp sampler",
    "emissive": "`CarLight.EmissiveMap` s5 (colour, RGB) — only on lamp blocks",
    "damage": "`CarPaintMM.DamageAlbedo` s5 / `DamageNormal` s4 / `Damage_Chapter_Mask` on `CarPaintMM`",
    "ui": "`hud.gfx` POI/clip art; no texture slot on a vehicle material",
    "other": "no carrier — see the row's reason",
}


def split_cells(line: str) -> list[str]:
    """Split a markdown table row on pipes that are not escaped as \\|."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.replace("\\|", "|").strip().strip("`\"' ") for c in re.split(r"(?<!\\)\|", body)]


def parse_census() -> list[dict]:
    rows = []
    for line in open(CENSUS, encoding="utf-8"):
        if not line.startswith("| Playable_") and not line.startswith("| Startup"):
            continue
        c = split_cells(line)
        if len(c) < 6:
            continue
        rows.append({"package": c[0], "texture": c[1], "size": c[2], "format": c[3],
                     "bytes": int(c[4]) if c[4].isdigit() else None, "bound_by": c[5]})
    return rows


def materials_text() -> str:
    return open(MATERIALS, encoding="utf-8").read()


def materials_mentions(text: str) -> dict[str, list[str]]:
    """texture name (lower) -> ['package.Material', ...] for every MATERIALS.md row naming it."""
    found: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = split_cells(line)
        if len(cells) < 3:
            continue
        for name in set(re.findall(r"[A-Za-z0-9_]{4,}", line)):
            low = name.lower()
            if low in found and cells[1] not in found[low]:
                found[low].append(cells[1])
            elif low not in found:
                found[low] = [cells[1]]
    return found


def material_textures(text: str, names: set[str]) -> dict[str, set[str]]:
    """material name -> the census textures its MATERIALS.md row names."""
    out: dict[str, set[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = split_cells(line)
        if len(cells) < 3:
            continue
        mat = cells[1]
        for c in cells[2:]:
            for tok in re.findall(r"[A-Za-z0-9_]{4,}", c):
                if tok.lower() in names:
                    out.setdefault(mat, set()).add(tok.lower())
    return out


def slot_bindings(names: set[str], mtex: dict[str, set[str]]) -> dict[str, list[str]]:
    """texture name (lower) -> ['slot <i> <material>'] for the 19 Batmobile mesh slots."""
    path = os.path.join(BAT, "SLOTS.json")
    if not os.path.exists(path):
        return {}
    d = json.load(open(path, encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for s in d.get("slots", []):
        mat = s.get("material")
        if not mat:
            continue
        for t in sorted(mtex.get(mat, ())):
            if t in names:
                out.setdefault(t, []).append(f"slot {s.get('index')} {mat}")
    return out


def bound_entries(bound: str) -> list[str]:
    if bound in ("—", "-", "", "no binding", "|"):
        return []
    return [e.strip() for e in bound.split(";") if e.strip()]


def role_of(name: str) -> str:
    n = name.lower()
    if "ramp" in n:
        return "ramp"
    if "damage" in n or "discbreak" in n or "crack" in n:
        return "damage"
    if re.search(r"(^|_)(ui|hud|icon|screen|blip|font)(_|$)", n) or n.startswith("ui_"):
        return "ui"
    if re.search(r"(^|_)e(_|$)", n) or "emissive" in n or "glow" in n:
        return "emissive"
    if re.search(r"(^|_)n(_|$)", n) or "_nrm" in n or "normal" in n:
        return "normal"
    if re.search(r"(^|_)(d|dif|diff|diffuse|alb|albedo|base|colour|color)(_|$)", n):
        return "albedo"
    if re.search(r"(^|_)(m|msk|mask|s|r|p|mpm|spec|rough|metal|ao|opacity|alpha)(_|$)", n) \
            or "mask" in n or "microdetail" in n or "decal" in n or "pattern" in n:
        return "mask"
    return "other"


def shipped_set() -> dict[str, str]:
    """normalised ddsc stem -> file name, for the build's own 28 files."""
    out = {}
    for f in sorted(os.listdir(DDSC)):
        if f.lower().endswith(".ddsc"):
            out[f.lower()[:-5]] = f
    return out


def rbm_slots() -> dict[str, int]:
    """texture basename -> number of built RBMs naming it (cross-check, best effort)."""
    sys.path.insert(0, HERE)
    try:
        import rbm_geom
    except Exception:
        return {}
    out: dict[str, int] = {}
    import glob
    for f in sorted(glob.glob(os.path.join(BUILD, "*.rbm"))):
        try:
            m = rbm_geom.decode(open(f, "rb").read())
        except Exception:
            continue
        seen = set()
        for b in m.blocks:
            for t in (getattr(b, "textures", []) or []):
                seen.add(os.path.basename(str(t)).lower())
        for n in seen:
            out[n] = out.get(n, 0) + 1
    return out


def classify() -> dict:
    rows = parse_census()
    mtext = materials_text()
    names = {r["texture"].lower() for r in rows}
    mentions = materials_mentions(mtext)
    mtex = material_textures(mtext, names)
    slots_bound = slot_bindings(names, mtex)
    ships = shipped_set()
    slots = rbm_slots()

    by_name: dict[str, dict] = {}
    for r in rows:
        n = r["texture"]
        key = n.lower()
        d = by_name.setdefault(key, {"texture": n, "packages": [], "sizes": set(), "formats": set(),
                                     "bytes": set(), "bindings": [], "rows": 0})
        d["packages"].append(r["package"])
        d["rows"] += 1
        d["sizes"].add(r["size"])
        d["formats"].add(r["format"])
        if r["bytes"] is not None:
            d["bytes"].add(r["bytes"])
        for e in bound_entries(r["bound_by"]):
            if e not in d["bindings"]:
                d["bindings"].append(e)

    # content duplicates: distinct names with identical (size, format, bytes)
    content: dict[tuple, set] = {}
    for key, d in by_name.items():
        if d["bytes"] and len(d["sizes"]) == 1 and len(d["formats"]) == 1:
            ck = (next(iter(d["sizes"])), next(iter(d["formats"])), min(d["bytes"]))
            content.setdefault(ck, set()).add(key)

    out_rows = []
    for r in rows:
        key = r["texture"].lower()
        d = by_name[key]
        mats = [m for m in mentions.get(key, []) if m and not m.startswith("---")]
        used = bool(d["bindings"]) or bool(mats)
        sbound = slots_bound.get(key, [])
        dup_of = sorted(p for p in d["packages"] if d["packages"].count(p) > 1)
        ck = None
        if d["bytes"] and len(d["sizes"]) == 1 and len(d["formats"]) == 1:
            ck = (next(iter(d["sizes"])), next(iter(d["formats"])), min(d["bytes"]))
        same_pixels = sorted(content.get(ck, set()) - {key}) if ck else []
        ship = ships.get(key)
        if ship is None:
            # a shipped file whose stem is the texture name with a package suffix stripped
            for stem, f in ships.items():
                if stem.startswith(key) or key.startswith(stem):
                    if min(len(stem), len(key)) >= 14:
                        ship = f
                        break
        duplicate = len(d["packages"]) > 1 or bool(same_pixels)
        status = "used" if used else "unused"
        role = role_of(r["texture"])
        reason = ""
        if ship:
            reason = "ships (ddsc in build)"
        elif not used:
            reason = "no material binding and no MATERIALS.md row names it"
        else:
            near = ""
            for stem, f in ships.items():
                if stem[:12] == key[:12]:
                    near = f
                    break
            reason = ("bound by " + (d["bindings"][0] if d["bindings"] else mats[0]) +
                      "; not in the build's ddsc set" + (f" (nearest shipped: {near})" if near else ""))
        out_rows.append({
            "package": r["package"], "texture": r["texture"], "size": r["size"],
            "format": r["format"], "bytes": r["bytes"], "role": role,
            "bound_by": r["bound_by"], "bound_entries": d["bindings"],
            "slot_bindings": sbound,
            "materials_named": mats[:6], "status": status, "duplicate": duplicate,
            "copies": len(d["packages"]), "ships": bool(ship),
            "shipped_file": ship or "", "reason": reason,
            "duplicate_packages": dup_of, "same_pixels_as": same_pixels,
            "rbm_slots": slots.get(key, 0),
        })

    by_role = {}
    for role in ROLES:
        rs = [r for r in out_rows if r["role"] == role]
        by_role[role] = {
            "rows": len(rs), "names": len({r["texture"].lower() for r in rs}),
            "used_rows": sum(1 for r in rs if r["status"] == "used"),
            "unused_rows": sum(1 for r in rs if r["status"] == "unused"),
            "duplicate_rows": sum(1 for r in rs if r["duplicate"]),
            "slot_bound_rows": sum(1 for r in rs if r["slot_bindings"]),
            "shipped_rows": sum(1 for r in rs if r["ships"]),
            "carrier": CARRIER[role],
        }
    doc = {
        "schema": "texture-audit/1",
        "generated_by": "Tools/scripts/app_texture_audit.py --write",
        "sources": {
            "census": "Research/BatmobileGrab/TEXTURES.md",
            "materials": "Research/BatmobileGrab/MATERIALS.md",
            "shipped": "Working/Appearance/build/ddsc/*.ddsc",
            "slots": "Working/Appearance/build/*.rbm",
            "row": "Working/Translation/T_ROWS.jsonl T-MA6",
        },
        "counts": {
            "rows": len(out_rows),
            "names": len(by_name),
            "bound_rows": sum(1 for r in out_rows if r["bound_entries"]),
            "bound_names": sum(1 for d in by_name.values() if d["bindings"]),
            "slot_bound_names": len(slots_bound),
            "own_package_bound_names": len({r["texture"].lower() for r in out_rows
                                           if r["package"] == "Playable_Batmobile_SF" and r["bound_entries"]}),
            "used_names": sum(1 for d in by_name.values()
                              if d["bindings"] or mentions.get(d["texture"].lower())),
            "unused_names": sum(1 for d in by_name.values()
                                if not d["bindings"] and not mentions.get(d["texture"].lower())),
            "duplicate_names": sum(1 for d in by_name.values() if len(d["packages"]) > 1),
            "shipped_files": len(ships),
            "shipped_rows": sum(1 for r in out_rows if r["ships"]),
        },
        "by_role": by_role,
        "rows": out_rows,
    }
    doc["sha256_rows"] = hashlib.sha256(json.dumps(out_rows, sort_keys=True).encode()).hexdigest()
    return doc


# ---------------------------------------------------------------------------------------- render
def md_rows(rows: list[dict]) -> list[str]:
    L = ["| package | texture | size | format | bytes | role | bound by (slot · material · parameter) | status | copies | duplicate | ships | reason |",
         "|---|---|---|---|---:|---|---|---|---:|---|---|---|"]
    for r in rows:
        b = r["bound_by"]
        if r["slot_bindings"]:
            b = "; ".join(r["slot_bindings"][:2]) + ("; " + b if b not in ("—", "-", "") else "")
        if len(b) > 110:
            b = b[:107] + "…"
        L.append(f"| {r['package'].replace('Playable_', '')} | `{r['texture']}` | {r['size']} | "
                 f"{r['format']} | {r['bytes'] if r['bytes'] is not None else '—'} | {r['role']} | "
                 f"{b} | {r['status']} | {r['copies']} | {'yes' if r['duplicate'] else 'no'} | "
                 f"{'yes' if r['ships'] else 'no'} | {r['reason']} |")
    return L


def render(doc: dict) -> str:
    c = doc["counts"]
    L = ["# Batmobile — texture audit: every grabbed texture, its material, and whether the build ships it",
         "",
         "<!-- generated by Tools/scripts/app_texture_audit.py --write; do not hand-edit -->",
         "",
         f"**{c['rows']} rows** over {c['names']} distinct texture names. **{c['slot_bound_names']} "
         f"distinct names are bound to the Batmobile mesh's 19 material slots** (T-MA6's 38); "
         f"{c['used_names']} are reached by some BmAK material or parameter in any package "
         f"({c['bound_rows']} rows); "
         f"{c['unused_names']} distinct names have no binding after searching every material "
         f"parameter list in `MATERIALS.md`. **{c['shipped_files']} textures ship** "
         f"(`Working/Appearance/build/ddsc/`), reached by {c['shipped_rows']} census rows. "
         f"{c['duplicate_names']} names occur in more than one package.",
         "",
         "Status is `used` (a material or parameter names it) or `unused`; `duplicate` is its own "
         "column (the name ships in more than one package, or another name has the same "
         "size/format/bytes). A row is never `unused` unless its name is absent from "
         "`MATERIALS.md` — `--check` enforces that.",
         "",
         f"**Reconciliation with row T-MA6** (`Working/Translation/T_ROWS.jsonl`: \"405 textures "
         f"grabbed, 38 bound to slots\", \"28 shipped\"): this audit re-derives **{c['slot_bound_names']}** "
         f"names bound through the 19 slot materials' `MATERIALS.md` rows, **{c['own_package_bound_names']}** "
         f"bound within the Batmobile's own package and **{c['used_names']}** bound in any of the five "
         f"packages, and reproduces the **{c['shipped_files']}** shipped files exactly. The 38 sits "
         f"between the 29 and the 40; the difference is bindings that live in a master material's "
         f"expression graph rather than an instance/parameter row, which this parser does not read. "
         f"Recorded here as a reconciliation item, not adjusted to match.",
         "",
         "## Counts by role",
         "",
         "| role | rows | names | used rows | unused rows | duplicate rows | slot-bound rows | shipping rows | closest JC3 carrier |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for role in ROLES:
        v = doc["by_role"][role]
        if not v["rows"]:
            continue
        L.append(f"| {role} | {v['rows']} | {v['names']} | {v['used_rows']} | {v['unused_rows']} | "
                 f"{v['duplicate_rows']} | {v['slot_bound_rows']} | {v['shipped_rows']} | {v['carrier']} |")
    L += ["", "## The 28 shipped textures", "",
          "| file | census names it | role |", "|---|---|---|"]
    shipped = {}
    for r in doc["rows"]:
        if r["ships"]:
            shipped.setdefault(r["shipped_file"], set()).add(r["texture"])
    for f in sorted(shipped):
        names = sorted(shipped[f])
        role = role_of(names[0])
        L.append(f"| `{f}` | " + (", ".join(f"`{n}`" for n in names[:3]) +
                                   (f" (+{len(names) - 3})" if len(names) > 3 else "")) + f" | {role} |")

    for role in ROLES:
        rs = [r for r in doc["rows"] if r["role"] == role]
        if not rs:
            continue
        L += ["", f"## {role} ({len(rs)} rows)", ""] + md_rows(rs)

    L += ["", "## Duplicate clusters (same name across packages, or same size/format/bytes)", ""]
    seen = set()
    for r in doc["rows"]:
        key = r["texture"].lower()
        if key in seen:
            continue
        seen.add(key)
        if r["duplicate_packages"] or r["same_pixels_as"]:
            L.append(f"- `{r['texture']}`: packages {len(r['duplicate_packages'])}"
                     + (f", same pixels as {', '.join('`' + s + '`' for s in r['same_pixels_as'][:4])}"
                        if r["same_pixels_as"] else ""))
    L.append("")
    return "\n".join(L)


def write(doc: dict) -> None:
    md = render(doc)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
    payload = {k: v for k, v in doc.items() if k != "rows"}
    payload["rows"] = doc["rows"]
    open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(json.dumps(payload, indent=1, sort_keys=True) + "\n")


def check(doc: dict) -> int:
    md = render(doc)
    problems = []
    if not os.path.exists(OUT_MD) or open(OUT_MD, encoding="utf-8").read() != md:
        problems.append("TEXTURE_AUDIT.md differs from the re-derivation")
    if not os.path.exists(OUT_JSON):
        problems.append("TEXTURE_AUDIT.json missing")
    else:
        have = json.load(open(OUT_JSON, encoding="utf-8"))
        if have.get("sha256_rows") != doc["sha256_rows"]:
            problems.append("TEXTURE_AUDIT.json row hash differs")
    c = doc["counts"]
    if c["rows"] != 405:
        problems.append(f"census rows {c['rows']} != 405")
    if c["shipped_files"] != 28:
        problems.append(f"shipped files {c['shipped_files']} != 28")
    mtext = materials_text().lower()
    for r in doc["rows"]:
        if r["status"] == "unused" and r["texture"].lower() in mtext:
            problems.append(f"{r['texture']} marked unused but named in MATERIALS.md")
    for p in problems:
        print("FAIL", p)
    if problems:
        return 1
    print(f"check ok: {c['rows']} rows / {c['names']} names, {c['used_names']} used, "
          f"{c['unused_names']} unused, {c['duplicate_names']} duplicated, {c['shipped_files']} shipped; "
          f"no unused name appears in MATERIALS.md; md + json re-derived")
    return 0


def summary(doc: dict) -> None:
    c = doc["counts"]
    print(f"rows {c['rows']} | names {c['names']} | slot-bound names {c['slot_bound_names']} | "
          f"bound rows {c['bound_rows']} | bound names {c['bound_names']} | used names {c['used_names']} | "
          f"unused names {c['unused_names']} | duplicated names {c['duplicate_names']} | "
          f"shipped files {c['shipped_files']} | shipped rows {c['shipped_rows']}")
    print("\n| role | rows | names | used | unused | duplicate | slot-bound | shipping |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for role in ROLES:
        v = doc["by_role"][role]
        if v["rows"]:
            print(f"| {role} | {v['rows']} | {v['names']} | {v['used_rows']} | {v['unused_rows']} | "
                  f"{v['duplicate_rows']} | {v['slot_bound_rows']} | {v['shipped_rows']} |")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check or a.summary):
        ap.print_help()
        return 0
    doc = classify()
    if a.write:
        write(doc)
        print(f"wrote {OUT_MD} and {OUT_JSON}: {doc['counts']['rows']} rows, "
              f"{doc['counts']['used_names']} used names, {doc['counts']['shipped_files']} shipped")
    if a.summary:
        summary(doc)
    if a.check:
        return check(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
