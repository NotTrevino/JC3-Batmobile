"""damage_audit.py - is the build's damage block inside the values the game ships?

The test-087 regression was a value that looked sourced (`class`: 156/156 land vehicles
ship 1) and turned collision damage on. The build's *previous* state was five values
outside every shipped range, written by hand and recorded as ordinary keeps. Neither was
visible in the ledger, because the ledger records where a number came from, not whether
the game can be expected to do anything sane with it.

This check closes that hole for `VehicleDamage`: it reads the shipped range from
`Research/JC3Grab/VOCABULARY.md` and fails when a build value sits outside it without a
declaration in `Working/Translation/damage_switches.json`. A declaration is a promise that
the value is a deliberate switch (an off switch, a saturation cap), not a translation.

Usage:
  python damage_audit.py                        # audit Working/Translation/current.json
  python damage_audit.py --build Builds/test-085 # decode a build tree first
  python damage_audit.py --json                 # machine-readable

Exit 0: every out-of-domain value is declared, and every declaration still applies.
Exit 1: an undeclared out-of-domain value, or a declaration that no longer matches.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
VOCAB = os.path.join(ROOT, "Research", "JC3Grab", "VOCABULARY.md")
CURRENT = os.path.join(ROOT, "Working", "Translation", "current.json")
SWITCHES = os.path.join(ROOT, "Working", "Translation", "damage_switches.json")

ROW_RE = re.compile(r"^\|\s*`([a-z_]+)`\s*\|\s*([a-z0-9]+)\s*\|\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*\.\.\s*"
                    r"(-?[\d.]+(?:e[+-]?\d+)?)\s*\(.*?\)\s*\|\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*\|\s*$")
NUM = (int, float)


def load_ranges(path: str = VOCAB) -> dict[str, dict]:
    """Every VehicleDamage member with its shipped min/max and the donor's value."""
    ranges: dict[str, dict] = {}
    inside = False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            inside = line.strip() == "## `VehicleDamage`"
            continue
        if not inside:
            continue
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        member, kind, lo, hi, donor = m.groups()
        ranges[member] = {"type": kind, "min": float(lo), "max": float(hi),
                          "donor": float(donor)}
    if not ranges:
        raise SystemExit(f"no VehicleDamage table found in {path}")
    return ranges


def build_values(doc: dict, members: set[str]) -> dict[str, dict]:
    """member -> {value, module} for every VehicleDamage member in the decoded build."""
    seen: dict[str, dict] = {}
    for name, mod in doc.get("modules", {}).items():
        for path, value in mod.get("values", {}).items():
            if path in members and isinstance(value, NUM):
                seen.setdefault(path, {"value": value, "module": name})
    return seen


def load_switches(path: str = SWITCHES) -> dict[str, dict]:
    if not os.path.exists(path):
        return {}
    doc = json.load(open(path, encoding="utf-8"))
    return {k: v for k, v in doc.get("switches", {}).items() if not k.startswith("_")}


def audit(build_doc: dict, ranges: dict[str, dict], switches: dict[str, dict],
          build_tag: str | None = None) -> tuple[list, list]:
    """`build_tag`: which build is being audited (e.g. `bm-009`), or None for the live snapshot.

    A declaration may carry `"build": "<tag>"` when the deviation exists only in that staged build
    (B-09's `max_health` 36000 does: the live dropzone still ships 2000). Such a declaration is
    enforced for its own build and ignored elsewhere - it is a fact about one build, not a licence
    for the value to appear anywhere."""
    def applies(d):
        if not d:
            return False
        scoped = d.get("builds") or ([d["build"]] if d.get("build") else [])
        return bool(scoped) and build_tag in scoped

    values = build_values(build_doc, set(ranges))
    problems: list[str] = []
    rows: list[dict] = []
    for member in sorted(values):
        v = values[member]["value"]
        r = ranges[member]
        inside = r["min"] <= v <= r["max"]
        declared = switches.get(member)
        if declared and declared.get("build"):
            declared = declared if applies(declared) else None
        row = {"member": member, "value": v, "min": r["min"], "max": r["max"],
               "donor": r["donor"], "module": values[member]["module"],
               "inside": inside, "declared": bool(declared)}
        rows.append(row)
        if not inside and not declared:
            problems.append(f"{member} = {v:g} is outside the shipped {r['min']:g}..{r['max']:g}"
                            f" and is not declared in {os.path.basename(SWITCHES)}")
        if not inside and declared:
            want = declared.get("value")
            if isinstance(want, NUM) and abs(float(want) - float(v)) > 1e-6:
                problems.append(f"{member}: declared switch value {want} but the build has {v:g}")
            if not declared.get("why") or not declared.get("row"):
                problems.append(f"{member}: switch declaration needs both `why` and `row`")
        if inside and declared:
            problems.append(f"{member}: declared as a switch but {v:g} is inside the shipped "
                            f"{r['min']:g}..{r['max']:g} - remove the declaration")
    for member, d in switches.items():
        if member in values or (d.get("build") and d.get("build") != build_tag):
            continue
        problems.append(f"{member}: declared in {os.path.basename(SWITCHES)} but absent "
                        f"from the build")
    return rows, problems


def epe_damage_module(build: str) -> str | None:
    """The module the entity's `.epe` `damage` property names, resolved back to a tree path.

    The property is `type byte, Jenkins("damage"), uint32 value` where the value is the Jenkins
    hash of the module's full vfs path (jc3_damage_search.epe_fields; MODLOG §101c). The hash is
    not invertible, so every `.vmodc` in the tree is hashed and matched. Without this the audit
    reads whichever `VehicleDamage` module `t1_current.dump` yields first - which is the *shared*
    `lave_health_medium.vmodc` even after a private copy is the one the entity points at."""
    sys.path.insert(0, HERE)
    import jc3_damage_search  # noqa: E402
    from rbmhdr import hash_jenkins  # noqa: E402
    epe = None
    for dirpath, _dirs, names in os.walk(build):
        for fn in sorted(names):
            if fn.endswith(".epe"):
                epe = os.path.join(dirpath, fn)
                break
        if epe:
            break
    if not epe:
        return None
    want = None
    for row in jc3_damage_search.epe_fields(epe, names=["damage"]):
        if row["type"] == "0x0e":
            want = row["int"]
    if want is None:
        return None
    for dirpath, _dirs, names in os.walk(build):
        for fn in sorted(names):
            if not fn.endswith(".vmodc"):
                continue
            vfs = os.path.relpath(os.path.join(dirpath, fn), build).replace("\\", "/")
            cut = vfs.find("editor/")          # `--build` may be the tree root or its parent
            if cut > 0:
                vfs = vfs[cut:]
            if (hash_jenkins(vfs.encode()) & 0xFFFFFFFF) == want:
                return vfs
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", help="folder containing editor/ (decoded via t1_current.py)")
    ap.add_argument("--current", default=CURRENT)
    ap.add_argument("--vocab", default=VOCAB)
    ap.add_argument("--switches", default=SWITCHES)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.build:
        sys.path.insert(0, HERE)
        from t1_current import dump  # noqa: E402
        doc = dump(a.build)
        target = epe_damage_module(a.build)
        if target:
            base = target.rsplit("/", 1)[-1]
            keep = {k: v for k, v in doc["modules"].items() if v.get("file") == base}
            if keep:
                doc = dict(doc, modules=keep)
                print(f"module     {target}  (the .epe `damage` hash)")
            else:
                print(f"WARN: the .epe names {target}, which this build did not decode")
    else:
        if not os.path.exists(a.current):
            raise SystemExit(f"no {a.current}; run t1_current.py <build> first")
        doc = json.load(open(a.current, encoding="utf-8"))

    ranges = load_ranges(a.vocab)
    switches = load_switches(a.switches)
    tag = os.path.basename(os.path.normpath(a.build)) if a.build else None
    if tag == "aaf":        # `--build <tag>/aaf`: the build is the folder above the tree
        tag = os.path.basename(os.path.dirname(os.path.normpath(a.build)))
    rows, problems = audit(doc, ranges, switches, tag)

    if a.json:
        print(json.dumps({"values": rows, "problems": problems}, indent=1))
        return 1 if problems else 0

    print(f"{'member':32} {'build':>9} {'shipped':>13} {'donor':>8}  verdict")
    for r in rows:
        verdict = "inside" if r["inside"] else ("switch" if r["declared"] else "OUT OF DOMAIN")
        print(f"{r['member']:32} {r['value']:>9g} {r['min']:>6g}..{r['max']:<6g} "
              f"{r['donor']:>8g}  {verdict}")
    out = sum(1 for r in rows if not r["inside"])
    print(f"\n{len(rows)} members, {out} outside the shipped range, "
          f"{sum(1 for r in rows if r['declared'])} declared switches")
    for p in problems:
        print("FAIL", p)
    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("check ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
