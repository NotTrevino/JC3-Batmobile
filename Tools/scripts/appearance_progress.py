"""appearance_progress.py - how much of the BmAK Batmobile appearance is IN the JC3 build.

One component per transferable artifact, status read from the build itself (never from a log):

  geometry   5 parts x 5 LODs = 25 meshes   -> file exists AND decodes (rbm_geom, byte re-encode)
  materials  19 used BmAK materials         -> a block of the spec's type in every part that uses it
  textures   38 unique bound texture objects -> a converted .ddsc exists at the expected path
  factors    321 BmAK factors               -> disposition from factors.py, per factor

Statuses: transferred | partial (an approximation rule carries only part of the meaning) |
missing (should be there, is not) | excluded (no JC3 equivalent; the reason is listed).

overall % = (transferred + 0.5 * partial) / total, i.e. an approximation can never count as a
full transfer. The report also prints the strict and the transferable-only percentages, because
"excluded" components are not failures - they are things JC3 has no slot for.

Usage: python Tools/scripts/appearance_progress.py [--build DIR] [--json OUT] [--md OUT]
"""
import argparse
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import rbm_geom as R  # noqa: E402

LODS = 5
BUILD = os.path.join(ROOT, "Working", "Appearance", "build")
MANIFEST = os.path.join(ROOT, "Working", "Appearance", "grab_manifest.json")


def _tex_stem(path):
    return os.path.splitext(os.path.basename(path))[0].lower()


def _converted_stems(asm):
    """Every stem the build actually converted (assembly.json textures: VFS -> local .ddsc)."""
    out = {}
    for vfs, local in asm.get("textures", {}).items():
        if os.path.exists(os.path.join(ROOT, local)):
            out[_tex_stem(vfs)] = local
    return out


def geometry(asm):
    rows, bad = [], []
    for part in asm["plan"]:
        for lod in range(1, LODS + 1):
            p = os.path.join(BUILD, f"{part}_lod{lod}.rbm")
            name = f"{part}_lod{lod}"
            if not os.path.exists(p):
                rows.append({"component": name, "status": "missing", "why": "no .rbm written"})
                continue
            try:
                raw = open(p, "rb").read()
                m = R.decode(raw)
                ok = m.write() == raw
                why = f"{len(m.blocks)} blocks, {os.path.getsize(p)} B" + ("" if ok else "; re-encode differs")
                rows.append({"component": name, "status": "transferred" if ok else "partial", "why": why})
                if not ok:
                    bad.append(name)
            except Exception as e:  # noqa: BLE001 - a broken file is the result we want to report
                rows.append({"component": name, "status": "missing", "why": f"decode failed: {e}"})
                bad.append(name)
    return rows, bad


def materials(asm, specs, converted):
    rows = []
    for mat, spec in specs.items():
        parts = [p for p, items in asm["plan"].items() if any(i["material"] == mat for i in items)]
        if not parts:
            rows.append({"component": mat, "status": "missing", "why": "not in any part's plan"})
            continue
        missing = []
        for slot, t in spec["textures"].items():
            if "tga" in t:
                stem = _tex_stem(t["tga"])
                if t.get("kind") == "glass":
                    stem += "_glass"
                else:
                    if t.get("alpha_tga"):
                        stem += "_a"
                    if slot in ("s2", "s3") and t.get("kind", "mask") == "mask":
                        stem += "_msk"
                if stem not in converted:
                    missing.append(slot)
            elif "solid" in t:
                c = tuple(int(round(x * 255)) for x in t["solid"][:3])
                if "solid_%02x%02x%02x" % c not in converted:
                    missing.append(slot)
        if missing:
            rows.append({"component": mat, "status": "partial",
                         "why": f"block in {len(parts)} part(s), slots not converted: {','.join(missing)}"})
        else:
            rows.append({"component": mat, "status": "transferred",
                         "why": f"{spec['block']} in {len(parts)} part(s), {len(spec['textures'])} slots bound"})
    return rows


def textures(specs, converted):
    """One row per unique texture the used materials bind, disposition from the first material."""
    seen = {}
    for mat, spec in specs.items():
        for d in spec["dispositions"]:
            if not d["factor"].startswith("tex:") or d["value"] in (None, "None"):
                continue
            t = d["value"]
            cur = seen.setdefault(t, {"disposition": d["disposition"], "factor": d["factor"],
                                      "target": d["target"], "materials": []})
            cur["materials"].append(mat)
    rows = []
    for t, info in sorted(seen.items()):
        disp = info["disposition"]
        stem = t.lower()
        hit = next((v for k, v in converted.items()
                    if k in (stem, stem + "_a", stem + "_msk", stem + "_glass", stem + "_a_msk")), None)
        if disp == "mapped":
            rows.append({"component": t, "status": "transferred" if hit else "missing",
                         "why": info["target"] + ("" if hit else " -- no .ddsc written")})
        elif disp == "approximated":
            rows.append({"component": t, "status": "partial", "why": info["target"]})
        elif disp == "missing-on-disk":
            rows.append({"component": t, "status": "missing", "why": info["target"]})
        else:
            rows.append({"component": t, "status": "excluded", "why": info["target"]})
    return rows


def factors(specs):
    rows = []
    for mat, spec in specs.items():
        for d in spec["dispositions"]:
            if d["factor"].startswith("tex:"):
                continue          # counted once per texture above
            disp = d["disposition"]
            if disp == "mapped":
                st = "transferred"
            elif disp == "approximated":
                st = "partial"
            elif disp in ("no-jc3-equivalent", "engine-global"):
                st = "excluded"
            else:
                st = "missing"
            rows.append({"component": f"{mat}:{d['factor']}", "status": st, "why": d["target"] or ""})
    return rows


def summarise(rows):
    out = {"total": len(rows), "transferred": 0, "partial": 0, "missing": 0, "excluded": 0}
    for r in rows:
        out[r["status"]] += 1
    out["percent"] = round(100.0 * (out["transferred"] + 0.5 * out["partial"]) / out["total"], 1) if out["total"] else 0.0
    transferable = out["total"] - out["excluded"]
    out["percent_transferable"] = round(100.0 * (out["transferred"] + 0.5 * out["partial"]) / transferable, 1) \
        if transferable else 0.0
    out["percent_strict"] = round(100.0 * out["transferred"] / out["total"], 1) if out["total"] else 0.0
    return out


def main():
    global BUILD
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", default=BUILD)
    ap.add_argument("--json")
    ap.add_argument("--md")
    a = ap.parse_args()
    BUILD = a.build

    asm = json.load(open(os.path.join(BUILD, "assembly.json")))
    specs = json.load(open(os.path.join(BUILD, "factors.json")))["materials"]
    converted = _converted_stems(asm)

    classes = {}
    classes["geometry"], bad_geom = geometry(asm)
    classes["materials"] = materials(asm, specs, converted)
    classes["textures"] = textures(specs, converted)
    classes["factors"] = factors(specs)
    total = [r for rs in classes.values() for r in rs]
    overall = summarise(total)

    source = {}
    if os.path.exists(MANIFEST):
        man = json.load(open(MANIFEST))
        source = {"counts": man.get("counts", {}), "package": man.get("package"),
                  "variants": man.get("variants", []),
                  "merged_props": len(man.get("merged_props", []))}

    rows = {"generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "build": os.path.relpath(BUILD, ROOT), "source": source,
            "classes": {k: {"summary": summarise(v), "components": v} for k, v in classes.items()},
            "overall": overall}
    js = a.json or os.path.join(BUILD, "..", "progress.json")
    md = a.md or os.path.join(BUILD, "..", "progress.md")
    json.dump(rows, open(js, "w", encoding="utf-8"), indent=1)

    lines = [f"# BmAK Batmobile -> JC3 appearance transfer ({rows['generated']})", "",
             f"build: `{rows['build']}`", ""]
    if source:
        c = source.get("counts", {})
        lines += [f"grab: {c.get('SkeletalMesh', 0)} mesh, {c.get('Material', 0)} masters, "
                  f"{c.get('MaterialInstance', c.get('MaterialInstanceConstant', 0))} instances, "
                  f"{c.get('Texture2D', 0)} textures "
                  f"in `{source.get('package')}` ({source.get('merged_props', 0)} props dumps merged)", ""]
    lines += ["| class | components | transferred | partial | missing | excluded | % |",
              "|---|---|---|---|---|---|---|"]
    for k, v in classes.items():
        s = rows["classes"][k]["summary"]
        lines.append(f"| {k} | {s['total']} | {s['transferred']} | {s['partial']} | {s['missing']} | "
                     f"{s['excluded']} | {s['percent']:.1f}% |")
    lines += [f"| **overall** | **{overall['total']}** | **{overall['transferred']}** | **{overall['partial']}** | "
              f"**{overall['missing']}** | **{overall['excluded']}** | **{overall['percent']:.1f}%** |", "",
              f"strict (transferred only): **{overall['percent_strict']:.1f}%**   |   "
              f"of everything JC3 has a slot for: **{overall['percent_transferable']:.1f}%**", ""]
    for k in classes:
        gaps = [r for r in classes[k] if r["status"] in ("missing", "partial", "excluded")]
        if not gaps:
            continue
        lines += [f"## {k}: what is not fully transferred", "", "| component | status | why |", "|---|---|---|"]
        for r in gaps:
            lines.append(f"| {r['component']} | {r['status']} | {r['why']} |")
        lines.append("")
    open(md, "w", encoding="utf-8").write("\n".join(lines))

    print(f"build {rows['build']}")
    print(f"{'class':10} {'total':>6} {'ok':>6} {'part':>6} {'miss':>6} {'excl':>6} {'%':>7}")
    for k in classes:
        s = rows["classes"][k]["summary"]
        print(f"{k:10} {s['total']:6} {s['transferred']:6} {s['partial']:6} {s['missing']:6} "
              f"{s['excluded']:6} {s['percent']:7.1f}")
    print(f"{'OVERALL':10} {overall['total']:6} {overall['transferred']:6} {overall['partial']:6} "
          f"{overall['missing']:6} {overall['excluded']:6} {overall['percent']:7.1f}")
    print(f"strict {overall['percent_strict']:.1f}%  |  of transferable {overall['percent_transferable']:.1f}%")
    def _rel(p):
        try:
            return os.path.relpath(p, ROOT)
        except ValueError:
            return os.path.abspath(p)

    print("progress ->", _rel(js), "and", _rel(md))
    for r in total:
        if r["status"] == "missing":
            print("  MISSING", r["component"], "--", r["why"])
    sys.exit(1 if overall["missing"] or bad_geom else 0)


if __name__ == "__main__":
    main()
