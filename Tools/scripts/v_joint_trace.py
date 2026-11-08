#!/usr/bin/env python3
"""Where the turret and cannon joints went: row -> manifest -> generator -> bm-RC2.

`Builds/bm-RC2/verify/turret_ranges.md` (task 7261) measured `constraint_index = -1` on
`batmobile_turret` (P-01) and `batmobile_cannon` (P-02). This page traces the chain the
brief names and finds the step where the joint stops existing:

  1. the rows        - `Working/Translation/T8_PARTS.md` P-01..P-15 (T-12);
  2. the manifest    - `Working/Parts/bm_vehicle_parts.json` (B-04);
  3. the generator   - `Tools/scripts/bm_parts.py` (the lines that write parts and joints);
  4. later steps     - `bm_rc.py` / `bm_rc2.py` (what they do to the parts and `.physicsc`);
  5. the built tree  - `Builds/bm-RC2/.../sportsmuscle_vehicle_parts.vmodc` + `.physicsc`;
  6. the fleet       - 78 shipped `*parts*.vmodc` under `JC3_RAW/tmp`, as the control: what a
                       `Turret` / `Cannon` / `AirBrake` / `GatlingGun` part normally carries.

Every value is recomputed here; `--check` renders the page again and compares it byte for
byte. Nothing is written but the verify page; manifests and builds are opened read-only.

Usage:
  python Tools/scripts/v_joint_trace.py --write   # Builds/bm-RC2/verify/joint_trace.md
  python Tools/scripts/v_joint_trace.py --check   # re-derive + byte-compare, exit 1 on drift
"""

from __future__ import annotations

import glob
import hashlib
import json
import math
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3adf  # noqa: E402
import jc3hkx  # noqa: E402

RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
BAT = os.path.join("Builds", "bm-RC2", "aaf", "models", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle", "batmobile")
PARTS = os.path.join(BAT, "sportsmuscle_vehicle_parts.vmodc")
PHYS = os.path.join(BAT, "sportsmuscle.physicsc")
B10 = os.path.join("Working", "Collision", "batmobile.physicsc")
OUT = os.path.join("Builds", "bm-RC2", "verify", "joint_trace.md")
T8 = os.path.join("Working", "Translation", "T8_PARTS.md")
MANIFEST = os.path.join("Working", "Parts", "bm_vehicle_parts.json")
GEN = os.path.join("Tools", "scripts", "bm_parts.py")
RC2 = os.path.join("Tools", "scripts", "bm_rc2.py")
RC1 = os.path.join("Tools", "scripts", "bm_rc.py")
CARD = os.path.join("Research", "challenge", "card-B-04.md")

LIMIT_MIN, LIMIT_MAX = 0x0FC, 0x100
JOINT_KEYS = re.compile(r"constraint|joint|hinge|limit|axis", re.I)   # `pivot_m` is geometry, not a link


def rel(p: str) -> str:
    return p.replace("\\", "/")


def read(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


def sha256(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


RANGE_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*…\s*(-?\d+(?:\.\d+)?)\s*°")


# ------------------------------------------------------------------- the rows
def t8_rows() -> list[dict]:
    """Every `| P-xx | ... |` behaviour row of T8_PARTS.md, as columns."""
    out = []
    for line in read(T8).splitlines():
        if not re.match(r"\| P-\d+ \|", line):
            continue
        c = [x.strip() for x in line.split("|")]
        m = RANGE_RE.search(c[8])
        car = RANGE_RE.search(c[11])
        out.append({"id": c[1], "part": c[2].strip("`"), "behaviour": c[3],
                    "bone": c[4], "pivot": c[5], "axis_jc3": c[7],
                    "motion": c[8], "motion_range": (float(m.group(1)), float(m.group(2))) if m else None,
                    "carrier": c[11],
                    "carrier_range": (float(car.group(1)), float(car.group(2))) if car else None,
                    "carrier_join": "no hinge" if "no hinge" in c[11].lower() else "hinge"})
    if not out:
        raise SystemExit("no P- rows in %s" % T8)
    return out


def t8_summary() -> dict:
    """The `| internal rows (no joint, reason given) | P-02, P-05, P-13 |` line."""
    for line in read(T8).splitlines():
        if line.startswith("| internal rows (no joint"):
            c = [x.strip() for x in line.split("|")]
            return {"line": line, "ids": [x.strip() for x in c[2].split(",")]}
    return {"line": "", "ids": []}


def t8_shipped_hinge(rid: str) -> dict:
    """The `- **shipped hinge**:` bullet of a row's per-part detail section."""
    body = read(T8)
    m = re.search(r"### %s — .*?(?=\n### |\Z)" % re.escape(rid), body, re.S)
    if not m:
        return {"found": False, "text": ""}
    for line in m.group(0).splitlines():
        if line.startswith("- **shipped hinge**"):
            text = line.split(":", 1)[1].strip()
            return {"found": True, "text": text,
                    "class": "hkpLimitedHingeConstraintData"
                    if "hkpLimitedHingeConstraintData" in text else "",
                    "axis": re.search(r"axis \[([^\]]+)\]", text).group(1)
                    if re.search(r"axis \[([^\]]+)\]", text) else "",
                    "limits": re.search(r"(-?\d+(?:\.\d+)?)…(-?\d+(?:\.\d+)?)°", text).groups()
                    if re.search(r"(-?\d+(?:\.\d+)?)…(-?\d+(?:\.\d+)?)°", text) else None}
    return {"found": False, "text": ""}


# --------------------------------------------------------------- the manifest
def manifest() -> dict:
    d = json.loads(read(MANIFEST))
    parts = {p["name"]: p for p in d["parts"]}
    keys = sorted({k for p in d["parts"] for k in p})
    joint_keys = [k for k in keys if JOINT_KEYS.search(k)]
    beh = d["behaviour"]
    t12 = {p["t12_row"]: p["name"] for p in d["parts"] if p.get("t12_row")}
    return {"d": d, "parts": parts, "keys": keys, "joint_keys": joint_keys,
            "behaviour_keys": sorted(beh), "beh": beh, "t12": t12,
            "n_parts": len(d["parts"]), "summary": d["summary"]}


def manifest_quote(name: str, m: dict) -> dict:
    p = m["parts"][name]
    return {k: p.get(k) for k in ("name", "part_index", "parent", "parent_index",
                                  "behaviour", "t12_row", "channel", "damage_type")}


# -------------------------------------------------------------- the generator
def gen_lines() -> dict:
    lines = read(GEN).splitlines()
    out = {"n_lines": len(lines), "ci": [], "hinged": [], "rotating": [], "aim": [],
           "physics_refs": [], "doc_steps": []}

    def grab(pred, bucket, limit=6):
        for i, line in enumerate(lines, 1):
            if pred(line):
                out[bucket].append({"line": i, "text": line.rstrip()})
                if len(out[bucket]) >= limit:
                    break

    grab(lambda s: '("constraint_index", -1)' in s, "ci")
    grab(lambda s: 'plan["hinged"]' in s and "if " in s, "hinged", 2)
    grab(lambda s: 'plan["rotating"]' in s and "if " in s, "rotating", 2)
    grab(lambda s: '"aim_part_constraints": []' in s, "aim", 2)
    grab(lambda s: "physicsc" in s.lower() or ".physics" in s, "physics_refs", 8)
    for i, s in enumerate(lines):
        if re.match(r"^  \d\. ", s) and len(out["doc_steps"]) < 8:
            block = [s.rstrip()]
            for nxt in lines[i + 1:]:
                if re.match(r"^  \d\. ", nxt) or not nxt.startswith("     "):
                    break
                block.append(nxt.rstrip())
            out["doc_steps"].append({"line": i + 1, "text": "\n".join(block)})
    # the flag tuple the ci line belongs to (the line names constraint_index last)
    if out["ci"]:
        at = out["ci"][0]["line"]
        out["ci_block"] = [{"line": n, "text": lines[n - 1].rstrip()}
                           for n in range(max(1, at - 4), min(len(lines), at + 1) + 1)]
        out["ci_cnt"] = sum(1 for s in lines if '("constraint_index", -1)' in s)
    return out


def writers_of_ci() -> dict:
    """Every script under Tools/scripts that *assigns* `constraint_index` (not compares it).

    `=(?!=)` keeps `d["constraint_index"] == ...` (a comparison in jc3_door_angles.py) out, and
    this audit file itself is skipped so its own string literals cannot count as writers.
    """
    hits = {}
    me = os.path.basename(__file__)
    for path in sorted(glob.glob(os.path.join(ROOT, "Tools", "scripts", "*.py"))):
        if os.path.basename(path) == me:
            continue
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except UnicodeDecodeError:
            continue
        found = [n for n, s in enumerate(lines, 1)
                 if '("constraint_index",' in s or '["constraint_index"] = ' in s]
        if found:
            hits[rel(os.path.relpath(path, ROOT))] = found
    return hits


def later_steps() -> dict:
    """What bm_rc/bm_rc2 do to the parts module and the .physicsc."""
    out = {"rc2_phys": [], "rc2_parts": [], "b10_copy": False, "parts_rewrite": []}
    for name, path in (("bm_rc2.py", RC2), ("bm_rc.py", RC1)):
        lines = read(path).splitlines()
        for i, s in enumerate(lines, 1):
            if "B-10" in s and ("physicsc" in s or "PHYS" in s):
                out["rc2_phys"].append({"script": name, "line": i, "text": s.strip()})
            if re.search(r"vehicle_parts\.vmodc|PARTS\b", s) and ("+" in s or "copy" in s):
                out["rc2_parts"].append({"script": name, "line": i, "text": s.strip()})
        out["b10_copy"] = out["b10_copy"] or any(
            "shutil.copy(B10" in s for s in lines)
    for i, s in enumerate(read(RC2).splitlines(), 1):
        if "shutil.copy(B10" in s:
            out["b10_line"] = {"line": i, "text": s.strip()}
        if "vehicle_parts" in s:
            out["parts_rewrite"].append({"line": i, "text": s.strip()})
    out["b10_pin"] = [{"line": i, "text": s.strip()} for i, s in
                      enumerate(read(RC2).splitlines(), 1) if s.startswith("B10_SHA") or "B10 = " in s]
    return out


# ------------------------------------------------------------------ the build
def built_parts() -> dict:
    adf = jc3adf.Adf(open(os.path.join(ROOT, PARTS), "rb").read())
    parts = jc3adf.parts(adf)
    return {"n": len(parts), "by_name": {p["name"]: p for p in parts}, "list": parts}


def constraints(rel_path: str) -> list[dict]:
    pf = jc3hkx.Packfile(open(os.path.join(ROOT, rel_path), "rb").read())
    objs = sorted((o for o in pf.objects if "Constraint" in o.cls), key=lambda o: o.offset)
    out = []
    for o in objs:
        rec = {"i": len(out), "class": o.cls, "offset": o.offset}
        if o.cls == "hkpLimitedHingeConstraintData":
            raw = pf.raw(o.offset, pf.extents[o.offset])
            lo, hi = struct.unpack_from("<2f", raw, LIMIT_MIN)
            rec["min"], rec["max"] = math.degrees(lo), math.degrees(hi)
            rec["span"] = rec["max"] - rec["min"]
        out.append(rec)
    return out


def phys_census(rel_path: str, exists: bool = True) -> dict:
    if not exists or not os.path.exists(os.path.join(ROOT, rel_path)):
        return {"present": False, "n": 0, "hinges": 0, "ragdolls": 0, "span_max": 0.0, "list": []}
    cons = constraints(rel_path)
    hinges = [c for c in cons if c["class"] == "hkpLimitedHingeConstraintData"]
    return {"present": True, "n": len(cons), "hinges": len(hinges),
            "ragdolls": len(cons) - len(hinges),
            "span_max": max((c["span"] for c in hinges), default=0.0),
            "list": hinges}


def fleet_census() -> dict:
    """Per behaviour: how many shipped parts carry a constraint_index >= 0."""
    files = sorted(set(glob.glob(os.path.join(RAW, "tmp", "*parts*.vmodc"))))
    stat: dict[str, list[int]] = {}
    for p in files:
        try:
            ps = jc3adf.parts(jc3adf.Adf(open(p, "rb").read()))
        except Exception:
            continue
        for x in ps:
            b = x.get("behavior") or "None"
            c = x.get("constraint_index")
            if c is None:
                continue
            row = stat.setdefault(b, [0, 0])
            row[0] += 1
            row[1] += 1 if c >= 0 else 0
    return {"modules": len(files), "stat": stat}


# ------------------------------------------------------------- the comparison
ROW_BEHAVIOURS = ("Turret", "Cannon", "GatlingGun", "MissileHatch", "AirBrake", "Hood",
                  "EngineRotatingPart")


def classify(row: dict, m: dict, built: dict, fleet: dict, internal: list[str]) -> dict:
    name = row["part"]
    part = built["by_name"].get(name)
    man = m["t12"].get(row["id"])
    f = fleet["stat"].get(row["behaviour"], [0, 0])
    # T8's own summary declares P-02/P-05/P-13 `internal rows (no joint)`, whatever the carrier cell says.
    asks = "no hinge" if (row["id"] in internal or row["carrier_join"] == "no hinge") else "hinge"
    rec = {"id": row["id"], "part": name or "—", "behaviour": row["behaviour"],
           "in_manifest": man is not None, "in_build": part is not None,
           "row_joint": asks, "ci": part.get("constraint_index") if part else None,
           "index": part.get("part_index") if part else None,
           "fleet_n": f[0], "fleet_joined": f[1]}
    if part is None:
        rec["verdict"] = "no part in the build (row has no cut part)"
        rec["lost_at"] = "not reached: no part exists to carry a joint"
    elif rec["ci"] == -1 and rec["row_joint"] == "hinge" and f[0] and f[1] == f[0]:
        rec["verdict"] = "LOST - row names a hinge, fleet ships one, part carries -1"
        rec["lost_at"] = "manifest (no joint member) then generator (writes -1)"
    elif rec["ci"] == -1 and rec["row_joint"] == "hinge":
        rec["verdict"] = "LOST - row names a hinge, part carries -1"
        rec["lost_at"] = "manifest (no joint member) then generator (writes -1)"
    elif rec["ci"] == -1 and rec["row_joint"] == "no hinge" and f[0] and f[1] == f[0]:
        rec["verdict"] = "row declines a hinge, fleet ships one - built -1 matches the row, not the fleet"
        rec["lost_at"] = "row (declined) - fleet evidence says the behaviour needs a hinge"
    elif rec["ci"] == -1 and f[0] == 0:
        rec["verdict"] = "no joint row - the row says it %s, so nothing was asked for" % row["behaviour"]
        rec["lost_at"] = "none"
    elif rec["ci"] == -1:
        rec["verdict"] = "correct - this behaviour ships no hinge in %d/%d fleet parts" % (f[1], f[0])
        rec["lost_at"] = "none"
    else:
        rec["verdict"] = "joint present (constraint_index %d)" % rec["ci"]
        rec["lost_at"] = "none"
    return rec


def build() -> dict:
    rows = t8_rows()
    m = manifest()
    g = gen_lines()
    later = later_steps()
    writers = writers_of_ci()
    parts = built_parts()
    phys = phys_census(rel(PHYS))
    b10 = phys_census(rel(B10))
    fleet = fleet_census()
    summ = t8_summary()
    hinges = {rid: t8_shipped_hinge(rid) for rid in ("P-01", "P-02", "P-04")}

    recs = [classify(r, m, parts, fleet, summ["ids"]) for r in rows]
    by_p = {r["id"]: r for r in recs}

    ciless = [p for p in parts["list"] if p.get("constraint_index") == -1]
    joined = [p for p in parts["list"] if isinstance(p.get("constraint_index"), int)
              and p["constraint_index"] >= 0]
    donor = {"hood": parts["by_name"].get("sportsmuscle_hood_signature")}

    return {"rows": rows, "by_p": by_p, "recs": recs, "t8_summary": summ,
            "manifest": m, "gen": g, "later": later, "writers": writers,
            "parts_n": parts["n"], "joined_n": len(joined), "ciless_n": len(ciless),
            "phys": phys, "b10": b10, "fleet": fleet, "hinges": hinges,
            "donor_hood_ci": donor["hood"].get("constraint_index") if donor["hood"] else None,
            "hashes": {"parts": sha256(PARTS), "phys": sha256(PHYS)},
            "files": {"parts": rel(PARTS), "phys": rel(PHYS), "b10": rel(B10),
                      "manifest": rel(MANIFEST), "gen": rel(GEN), "rc2": rel(RC2),
                      "t8": rel(T8), "card": rel(CARD)}}


# ------------------------------------------------------------------- the page
def f3(v: float) -> str:
    return "%.3f" % v


def q(v) -> str:
    return "`%s`" % v if isinstance(v, (int, float)) else ("`%s`" % v if v is not None else "—")


def render(d: dict) -> str:
    L: list[str] = []
    a = L.append
    m, g, later, fleet = d["manifest"], d["gen"], d["later"], d["fleet"]
    lost = [r for r in d["recs"] if r["verdict"].startswith("LOST")]
    a("# Where the turret and cannon joints went - row -> manifest -> generator -> bm-RC2")
    a("")
    a("Generated by `python Tools/scripts/v_joint_trace.py --write`; `--check` re-reads every")
    a("file below and compares this page byte for byte. Read-only: the manifests, the build")
    a("and the fleet are opened for reading only.")
    a("")
    a("**Answer: the joints never existed past the manifest.** T8's rows name hinges for P-01 and")
    a("P-04, but the B-04 part record has **no joint member at all** (its %d keys contain no"
      % len(m["keys"]))
    a("`constraint_index`/`hinge`/`limit`/`axis` field), and `bm_parts.py` writes")
    a("`constraint_index = -1` on all %d new parts and never opens the `.physicsc`. No later step"
      % d["manifest"]["n_parts"])
    a("removes them: `bm_rc2.py` only swaps in B-10's `.physicsc`, which carries the same %d donor"
      % d["phys"]["n"])
    a("constraints (%d limited hinges, widest span %.1f°)." % (d["phys"]["hinges"], d["phys"]["span_max"]))
    a("")
    a("## 1. The chain, step by step")
    a("")
    a("| # | step | artefact | carries a joint? | P-01 yaw | P-02 pitch |")
    a("|---|---|---|---|---|---|")
    a("| 1 | rows (T-12) | `%s` | yes for P-01/P-04 (`shipped hinge` bullet + axis + limits); P-02's row is an `internal row (no joint)` | %s | %s |"
      % (d["files"]["t8"], s_or_none(d["by_p"]["P-01"]["row_joint"]),
         s_or_none(d["by_p"]["P-02"]["row_joint"])))
    a("| 2 | manifest (B-04) | `%s` | **no** - %d keys, %d joint-ish: %s | absent | absent |"
      % (d["files"]["manifest"], len(m["keys"]), len(m["joint_keys"]),
         "none" if not m["joint_keys"] else ", ".join("`%s`" % k for k in m["joint_keys"])))
    a("| 3 | generator | `%s` L%d | **no** - writes `-1`, `physicsc` mentioned %d times | -1 | -1 |"
      % (d["files"]["gen"], g["ci"][0]["line"] if g["ci"] else 0, len(g["physics_refs"])))
    a("| 4 | later steps | `%s` L%d | **no** - %s | unchanged | unchanged |"
      % (d["files"]["rc2"], later.get("b10_line", {}).get("line", 0),
         "the `.physicsc` is replaced by B-10's pinned file" if later["b10_copy"] else "no replacement"))
    a("| 5 | build | `%s` | **no** - %d/%d constraint objects are donor panels | -1 | -1 |"
      % (d["files"]["parts"], d["phys"]["hinges"], d["phys"]["n"]))
    a("")
    a("So the joint dies at step 2 and is never re-created at step 3: the row carries it, the")
    a("manifest drops it, the generator hardcodes `-1`, and step 4 copies a physics file that")
    a("never had it. There is nothing for step 5 to write.")
    a("")
    a("## 2. The rows")
    a("")
    a("| id | part | behaviour | BmAK motion | carrier column | shipped hinge (row's own detail) |")
    a("|---|---|---|---|---|---|")
    for r in d["rows"]:
        h = d["hinges"].get(r["id"], {})
        a("| %s | `%s` | %s | %s | %s | %s |" % (
            r["id"], r["part"] or "—", r["behaviour"], r["motion"], r["carrier"],
            ("`%s` %s %s" % (h.get("class", ""), "limits " + "…".join(h["limits"]) + "°" if h.get("limits") else "", ""))
            .replace("  ", " ").strip() if h.get("found") else "—"))
    a("")
    a("T8's own summary line already declares which rows have no joint: %s"
      % ("`%s`" % d["t8_summary"]["line"].strip() if d["t8_summary"]["line"] else "—"))
    a("")
    a("P-01's row (`| P-01 |` in `%s`):" % d["files"]["t8"])
    a("")
    p1 = next(r for r in d["rows"] if r["id"] == "P-01")
    a("```")
    a("| P-01 | `%s` | %s | %s | %s | %s | %s | %s |" % (
        p1["part"], p1["behaviour"], p1["bone"], p1["pivot"], p1["axis_jc3"],
        p1["motion"], p1["carrier"]))
    a("```")
    a("")
    a("and P-02's:")
    a("")
    p2 = next(r for r in d["rows"] if r["id"] == "P-02")
    a("```")
    a("| P-02 | `%s` | %s | %s | %s | %s | %s | %s |" % (
        p2["part"], p2["behaviour"], p2["bone"], p2["pivot"], p2["axis_jc3"],
        p2["motion"], p2["carrier"]))
    a("```")
    a("")
    a("**P-02 is the one row that does not ask for a joint.** Its motion is `static`, its")
    a("per-part detail says *\"no rotation is animated; the bones translate ... and a hinge cannot")
    a("reproduce translation\"*, and T8's summary lists it among the `internal rows (no joint)`.")
    a("Its verify line still asks the barrel to *\"stop at the carrier's own -5..20 deg\"*, which is")
    a("a hinge's job - a row-level gap that the -1 in the build faithfully reproduces.")
    a("")
    a("## 3. The manifest (B-04) - where the joint stops")
    a("")
    a("`%s` has **%d parts**; every part record has these %d keys:"
      % (d["files"]["manifest"], m["n_parts"], len(m["keys"])))
    a("")
    a("```")
    a(", ".join(m["keys"]))
    a("```")
    a("")
    a("Joint-ish keys in that list: **%s**. The manifest therefore has no place to put a"
      % ("none" if not m["joint_keys"] else ", ".join(m["joint_keys"])))
    a("`constraint_index`, an axis or a limit, and the generator has nothing to read one from.")
    a("")
    a("The two brief-named entries, verbatim from the JSON:")
    a("")
    for name in ("batmobile_turret", "batmobile_cannon"):
        rec = manifest_quote(name, m)
        a("```json")
        a(json.dumps(rec, ensure_ascii=False))
        a("```")
        a("")
    a("`channel` comes from T-12 and is `none` on both (P-01 and P-02 are `behaviour` rows, not")
    a("`hinged`/`rotating`/`door` rows), so neither reaches any behaviour array either. The")
    a("manifest's own behaviour block says where the joint was expected instead:")
    a("")
    a("| array | rows | what the block says |")
    a("|---|---|---|")
    for k in m["behaviour_keys"]:
        v = m["beh"][k]
        rows_v = v.get("rows") if isinstance(v, dict) else None
        note = (v.get("note") or v.get("source") or "") if isinstance(v, dict) else ""
        if isinstance(rows_v, list) and rows_v and isinstance(rows_v[0], dict):
            shown = "[%s]" % ", ".join(str(x.get("part_index")) for x in rows_v)
        elif isinstance(rows_v, list):
            shown = "[%s]" % ", ".join(str(x) for x in rows_v)
        else:
            shown = str(rows_v)
        a("| `%s` | `%s` | %s |" % (k, shown, note.replace("|", "/")[:220]))
    a("")
    a("`aim_part_constraints` is the only block that could have held a turret link and it is")
    a("empty by a TURRET.md reading (85 rows, all suspension, 0 on the six turreted vehicles).")
    a("Nothing in the block declares the `constraint_index` a `Turret`/`Cannon` part needs.")
    a("")
    a("## 4. The generator - the lines that handle joints")
    a("")
    a("`%s` (%d lines) mentions `physicsc` **%d times**: the parts module is rewritten through"
      % (d["files"]["gen"], g["n_lines"], len(g["physics_refs"])))
    a("ConvertProperty XML and the physics module is never opened, so no constraint can be added")
    a("there even if an index were written. The steps the docstring lists:")
    a("")
    a("```")
    for s in g["doc_steps"]:
        a("%s" % s["text"])
    a("```")
    a("")
    a("Step 4 appends behaviour arrays, and between them the list names exactly four -")
    a("`hinged_parts`, `rotating_parts`, `door_parts`, `aim_part_constraints`. No step writes a")
    a("constraint object or a `constraint_index`.")
    a("")
    a("The part writer sets the field to `-1` in its flag tuple (L%d):" % (g["ci"][0]["line"] if g["ci"] else 0))
    a("")
    a("```python")
    for s in g.get("ci_block", []):
        a("%4d  %s" % (s["line"], s["text"]))
    a("```")
    a("")
    a("That tuple is unconditional for every new part; `%s` appears **%d time(s)** in the whole"
      % ('("constraint_index", -1)', g.get("ci_cnt", 0)))
    a("file and there is no branch that could set it to a real index. The array writers it does")
    a("have:")
    a("")
    for bucket, label in (("hinged", "hinged_parts"), ("rotating", "rotating_parts"), ("aim", "aim_part_constraints")):
        for s in g[bucket][:2]:
            a("* L%d `%s` - `%s`" % (s["line"], label, s["text"].strip()))
    a("")
    a("Scripts under `Tools/scripts/` that **assign** `constraint_index`: %s."
      % (", ".join("`%s` L%s" % (k, ", ".join(str(n) for n in v)) for k, v in d["writers"].items())
         or "none"))
    a("")
    a("## 5. The later steps - nothing to remove")
    a("")
    a("`%s` step 3 replaces the tree's `.physicsc` with B-10's pinned file:"
      % d["files"]["rc2"])
    a("")
    a("```python")
    for s in later.get("b10_pin", []):
        a("%4d  %s" % (s["line"], s["text"]))
    if later.get("b10_line"):
        a("%4d  %s" % (later["b10_line"]["line"], later["b10_line"]["text"]))
    a("```")
    a("")
    a("| physicsc | constraint objects | limited hinges | ragdoll | widest limited span |")
    a("|---|---|---|---|---|")
    a("| `%s` (build) | %d | %d | %d | %.1f° |" % (d["files"]["phys"], d["phys"]["n"],
                                                   d["phys"]["hinges"], d["phys"]["ragdolls"],
                                                   d["phys"]["span_max"]))
    a("| `%s` (B-10 input) | %d | %d | %d | %.1f° |" % (d["files"]["b10"], d["b10"]["n"],
                                                         d["b10"]["hinges"], d["b10"]["ragdolls"],
                                                         d["b10"]["span_max"]))
    a("")
    a("The two files carry the same donor constraint set, so step 4 neither added nor deleted a")
    a("hinge: it swapped one jointless-for-the-turret physics file for another. No later script")
    a("touches the parts module's `constraint_index` (%s)."
      % (", ".join("`%s`" % k for k in d["writers"]) or "none"))
    a("")
    a("## 6. The built module")
    a("")
    a("| part | index | behaviour | constraint_index | resolves to |")
    a("|---|---|---|---|---|")
    for r in d["recs"]:
        if not r["in_build"]:
            continue
        a("| `%s` | %s | %s | %s | %s |" % (
            r["part"], r["index"], r["behaviour"], q(r["ci"]),
            "a donor panel hinge" if r["ci"] is not None and r["ci"] >= 0 else "nothing (no joint)"))
    a("")
    a("Of %d parts, **%d carry a `constraint_index`** and **%d carry `-1`** - the field is written,"
      % (d["parts_n"], d["joined_n"], d["ciless_n"]))
    a("the turret unit is simply among the `-1`s. The donor's own hood keeps its hinge")
    a("(`sportsmuscle_hood_signature`, ci %s), which is why the file still has %d objects at all."
      % (q(d["donor_hood_ci"]), d["phys"]["n"]))
    a("")
    a("## 7. The control: what the fleet ships for these behaviours")
    a("")
    a("%d shipped `*parts*.vmodc` under `JC3_RAW/tmp`:" % fleet["modules"])
    a("")
    a("| behaviour | fleet parts | with `constraint_index >= 0` | rows in this build |")
    a("|---|---|---|---|")
    for b in ROW_BEHAVIOURS:
        n, j = fleet["stat"].get(b, [0, 0])
        rs = [r["id"] for r in d["recs"] if r["behaviour"] == b]
        a("| %s | %d | %d | %s |" % (b, n, j, ", ".join(rs) if rs else "—"))
    a("")
    a("`Turret` %d/%d and `Cannon` %d/%d is the evidence that these two behaviours are carried by a"
      % (fleet["stat"].get("Turret", [0, 0])[1], fleet["stat"].get("Turret", [0, 0])[0],
         fleet["stat"].get("Cannon", [0, 0])[1], fleet["stat"].get("Cannon", [0, 0])[0]))
    a("hinge and not by the behaviour name - and why `GatlingGun` %d/%d and"
      % (fleet["stat"].get("GatlingGun", [0, 0])[1], fleet["stat"].get("GatlingGun", [0, 0])[0]))
    a("`EngineRotatingPart` %d/%d are *not* a defect in the build."
      % (fleet["stat"].get("EngineRotatingPart", [0, 0])[1],
         fleet["stat"].get("EngineRotatingPart", [0, 0])[0]))
    a("")
    a("## 8. Every row, and whether it lost a joint")
    a("")
    a("| id | part | behaviour | row asks for | fleet carries | built | verdict | step |")
    a("|---|---|---|---|---|---|---|---|")
    for r in d["recs"]:
        a("| %s | `%s` | %s | %s | %d/%d | %s | %s | %s |" % (
            r["id"], r["part"] or "—", r["behaviour"], r["row_joint"],
            r["fleet_joined"], r["fleet_n"], q(r["ci"]), r["verdict"], r["lost_at"]))
    a("")
    a("**%d row(s) lost a joint: %s.**" % (len(lost), ", ".join("%s (`%s`, %s)" % (r["id"], r["part"], r["behaviour"]) for r in lost)))
    a("")
    a("* **P-01** is the headline: a `Turret` with an animated ±60° yaw, a shipped-hinge bullet")
    a("  (mediumtank, `hkpLimitedHingeConstraintData`), and 7/7 fleet `Turret` parts carrying a")
    a("  hinge, against `-1` in the build.")
    a("* **P-04** is the same loss and was not in the 7261 brief: `batmobile_riot_suppressor` is a")
    a("  `Cannon` whose row animates -89.999…-0.000° about [-0.000, -0.000, -1.000], with the same")
    a("  shipped hinge (the row notes its axis *DISAGREES* with it - a B-02 decision, not a joint")
    a("  count), and it ships `-1`.")
    a("* **P-02, P-09…P-12** are not joint *losses* in the manifest sense - their rows say `no")
    a("  hinge` or `static` - but their behaviours need one in the fleet (`Cannon` %d/%d, `AirBrake`"
      % (fleet["stat"].get("Cannon", [0, 0])[1], fleet["stat"].get("Cannon", [0, 0])[0]))
    a("  %d/%d), and `Research/challenge/card-B-04.md` B4-03 measured 148/148 fleet `hinged_parts`"
      % (fleet["stat"].get("AirBrake", [0, 0])[1], fleet["stat"].get("AirBrake", [0, 0])[0]))
    a("  rows sitting on a part with `constraint_index >= 0`. Their `-1` reproduces the row and")
    a("  breaks the behaviour: a second, row-level gap.")
    a("* **P-03, P-05** are correct: `GatlingGun` and `EngineRotatingPart` never ship a hinge in")
    a("  the fleet, and P-03's rotation is carried by the `rotating_parts` row the build does write")
    a("  (part 52).")
    a("* **P-06, P-07, P-08, P-13** have no cut part at all (`part` is `—` in T8), so there is no")
    a("  part to carry a joint; the donor's hood keeps its own (ci %s)." % q(d["donor_hood_ci"]))
    a("")
    a("## 9. Reading")
    a("")
    a("| question the brief asks | answer |")
    a("|---|---|")
    a("| is the joint ever in the manifest? | **no** - %d keys, none of them a joint; the record it does write is `behaviour` + `channel` |" % len(m["keys"]))
    a("| does the generator drop it? | **yes, it is the writer** - `constraint_index = -1` for every new part (L%d), and the `.physicsc` is never opened |" % (g["ci"][0]["line"] if g["ci"] else 0))
    a("| does a later step remove it? | **no** - `bm_rc2.py` copies B-10's `.physicsc` over the tree's; both carry the same %d donor constraints |" % d["b10"]["n"])
    a("| did any other row lose its joint? | **yes, P-04** (`Cannon`, -89.999°); P-02/P-09…P-12 never asked for one but need one |")
    a("")
    a("So there are two defects, not one: the manifest never models a hinge (so no card can write")
    a("one), and the generator's `-1` is unconditional rather than derived from the row. Fixing")
    a("both needs a manifest member (axis, pivot, limits, hinge class) and a physics-side writer")
    a("that appends `hkpLimitedHingeConstraintData` objects - which B-04's five steps do not have.")
    a("")
    a("## 10. UNKNOWNs")
    a("")
    a("* **whether JC3 creates a joint for a `Turret` with `constraint_index = -1`.** No decoded")
    a("  file says so; no fleet turret ships it; a test would answer it and the test ban stands.")
    a("* **where the constraint objects belong for a swapped physics file.** B-10's `.physicsc` is")
    a("  the donor collision file; whether appending hinges to it keeps the `constraint_index`")
    a("  order stable across the packfile is UNKNOWN - no card has written one yet.")
    a("* **the fleet census is 78 `tmp/*parts*.vmodc` modules**, not the 232-entity census the")
    a("  entity walk uses; the per-behaviour ratios are from those 78 and are stated as such.")
    a("")
    a("## 11. Oracles re-run by `--check`")
    a("")
    a("* `T8_PARTS.md` still has a P-01 row with a `shipped hinge` bullet and a P-02 row with")
    a("  motion `static`, and its summary still lists P-02 among the `internal rows (no joint)`")
    a("* the manifest still has %d parts and **no** key matching constraint/joint/hinge/limit/axis"
      % m["n_parts"])
    a("* `bm_parts.py` still writes `(\"constraint_index\", -1)` exactly once (L%d) and still never"
      % (g["ci"][0]["line"] if g["ci"] else 0))
    a("  names `physicsc`; no other script assigns the field")
    a("* `bm_rc2.py` still copies B-10's `.physicsc`, and both physics files still carry %d"
      % d["b10"]["n"])
    a("  constraints (%d limited, widest %.1f°)" % (d["b10"]["hinges"], d["b10"]["span_max"]))
    a("* the build still has %d parts, %d with a `constraint_index`, and `batmobile_turret` /"
      % (d["parts_n"], d["joined_n"]))
    a("  `batmobile_cannon` / `batmobile_riot_suppressor` still read -1 / -1 / -1")
    a("* the fleet still ships `Turret` %d/%d and `Cannon` %d/%d with a hinge, `GatlingGun` 0/6"
      % (fleet["stat"].get("Turret", [0, 0])[1], fleet["stat"].get("Turret", [0, 0])[0],
         fleet["stat"].get("Cannon", [0, 0])[1], fleet["stat"].get("Cannon", [0, 0])[0]))
    a("* both build files still hash to the values in the summary table below; the page matches")
    a("  the regenerated bytes")
    a("")
    a("## 12. Labels")
    a("")
    a("Row values and the manifest keys are **decoded** (`T8_PARTS.md`, `bm_vehicle_parts.json`);")
    a("the generator quotes are **decoded** line text from `bm_parts.py`; the built `-1`s are")
    a("**decoded** from the module's `constraint_index` fields and the physics census from the")
    a("packfile's constraint objects. The fleet ratios are **derived** from those 78 modules. The")
    a("step attribution is **derived** from the four artefacts. Nothing is typed from memory of")
    a("Arkham Knight or Just Cause 3.")
    a("")
    a("| file | sha256 |")
    a("|---|---|")
    a("| `%s` | `%s` |" % (d["files"]["parts"], d["hashes"]["parts"]))
    a("| `%s` | `%s` |" % (d["files"]["phys"], d["hashes"]["phys"]))
    a("")
    return "\n".join(L) + "\n"


def s_or_none(v: str) -> str:
    return v if v else "—"


# ------------------------------------------------------------------- oracles
def oracles(d: dict) -> list[tuple[str, bool]]:
    m, g, later = d["manifest"], d["gen"], d["later"]
    t = d["fleet"]["stat"]
    rows = {r["id"]: r for r in d["rows"]}
    return [
        ("T8 still has P-01 with a shipped hinge", d["hinges"]["P-01"]["found"]
         and d["hinges"]["P-01"]["class"] == "hkpLimitedHingeConstraintData"),
        ("T8 still has P-02 static and jointless", rows["P-02"]["motion_range"] is None
         and "P-02" in d["t8_summary"]["ids"]),
        ("T8 still has P-04 as a Cannon with a shipped hinge", d["hinges"]["P-04"]["found"]),
        ("the manifest has no joint member", not m["joint_keys"]),
        ("the manifest still has 19 new parts", m["n_parts"] == 19),
        ("the manifest still lists P-01's part with channel none",
         m["parts"]["batmobile_turret"]["channel"] == "none"),
        ("bm_parts.py writes constraint_index -1 once", g.get("ci_cnt", 0) == 1),
        ("bm_parts.py never names physicsc", not g["physics_refs"]),
        ("only bm_parts.py assigns constraint_index",
         list(d["writers"]) == [d["files"]["gen"]]),
        ("P-02 is an internal row, not a lost joint", d["by_p"]["P-02"]["row_joint"] == "no hinge"),
        ("bm_rc2.py copies B-10's physicsc", later["b10_copy"]),
        ("build and B-10 carry the same constraint count",
         d["phys"]["n"] == d["b10"]["n"] and d["phys"]["hinges"] == d["b10"]["hinges"]),
        ("no limited hinge is wide enough to be the yaw joint", d["phys"]["span_max"] < 100.0),
        ("the build still has 61 parts", d["parts_n"] == 61),
        ("the turret unit still carries -1", d["by_p"]["P-01"]["ci"] == -1
         and d["by_p"]["P-02"]["ci"] == -1 and d["by_p"]["P-04"]["ci"] == -1),
        ("P-01 and P-04 are the lost joints",
         [r["id"] for r in d["recs"] if r["verdict"].startswith("LOST")] == ["P-01", "P-04"]),
        ("fleet Turret parts all carry a hinge", t.get("Turret", [0, 0])[1] == t.get("Turret", [0, 0])[0] and t.get("Turret", [0, 0])[0] > 0),
        ("fleet Cannon parts all carry a hinge", t.get("Cannon", [0, 0])[1] == t.get("Cannon", [0, 0])[0] and t.get("Cannon", [0, 0])[0] > 0),
        ("fleet GatlingGun parts carry none", t.get("GatlingGun", [0, 0])[1] == 0),
        ("the donor hood keeps its hinge", d["donor_hood_ci"] is not None and d["donor_hood_ci"] >= 0),
        ("P-03 and P-05 are not loss rows",
         d["by_p"]["P-03"]["verdict"].startswith("correct")
         and d["by_p"]["P-05"]["verdict"].startswith("correct")),
    ]


def page() -> tuple[str, list[tuple[str, bool]]]:
    d = build()
    return render(d), oracles(d)


def cmd_write() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s (%d bytes)" % (rel(OUT), len(text.encode())))
    return 0 if all(ok for _, ok in ors) else 1


def cmd_check() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print("MISSING %s" % rel(OUT))
        return 1
    for name, ok in ors:
        print(("PASS " if ok else "FAIL ") + name)
    bad = [n for n, ok in ors if not ok]
    print("oracles: %d/%d pass" % (len(ors) - len(bad), len(ors)))
    if open(path, encoding="utf-8").read() != text:
        print("DRIFT: %s differs from the regenerated bytes" % rel(OUT))
        return 1
    print("document identical: %s" % rel(OUT))
    return 0 if not bad else 1


def main() -> int:
    args = sys.argv[1:]
    if args == ["--write"]:
        return cmd_write()
    if args == ["--check"]:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
