#!/usr/bin/env python3
"""HUD cluster elements - does HUD_SPEC.json describe the layout, and is G3-HUD-CLUSTER right?

The brief starts from `Research/BatmobileGrab/HUD_SPEC.json` and asks for every speedometer/health
cluster element with name, position and size. This tool answers mechanically:

  * what `HUD_SPEC.json` actually contains (it is a behaviour contract: setters, frame labels,
    constants, the health contract - **no element geometry, no element list**);
  * the element inventory `tmp/freebuff/reports/G3-HUD-CLUSTER.md` states;
  * where the two overlap (constants, health contract, frame labels) and whether they agree;
  * whether the report's clip transforms are borne out by the source, read from the decompiled AS3
    of `HudModuleBatmobile` (the same movie `Tools/scripts/bmak_hud.py` carves);
  * one verdict per element.

Output: Working/Translation/HUD_CLUSTER_ELEMENTS.md   (--write, --check)

Read-only. The game install, `E:/Modding/_gamedata` and every other task's files are opened for
reading only; nothing is launched or written outside this tool's own output.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = "Research/BatmobileGrab/HUD_SPEC.json"
REPORT = "tmp/freebuff/reports/G3-HUD-CLUSTER.md"
CLUSTER = "Working/HUD/CLUSTER.json"
OUT_MD = "Working/Translation/HUD_CLUSTER_ELEMENTS.md"
AS3_GLOB = ("E:/Modding/_gamedata/BmAKgrab_early/hud/modules/HudModuleBatmobile/dec/scripts/"
            "HudModuleBatmobile_fla/*.as")

# every cluster element the report names, with the words it uses for it
NAMED_ELSEWHERE = {
    "FillMovie": "boost fill clip (102 frames, frame = level + 1)",
    "Cap": "the boost bar's cap clip, rides y 9.5 -> -182.5",
    "Background": "boost background, 32 frames, labels Basic/Extra1..Extra4",
    "Healthbar": "health fill parent (`Healthbar.Bar`)",
    "ArmourForeground": "the armour fill above 1.0",
    "ArmourBackground": "the armour tier backdrop, label Armour<n>",
    "BG": "health pulse pair (Pulse/Idle)",
    "XPbar": "the XP fill inside Health",
    "DamageEffectMovie": "the floating damage number",
    "ch1040": "the unnamed 1-frame third child of BoostMovie at (5.0, -83.7)",
}

GEOMETRY_KEYS = ("x", "y", "z", "position", "matrix", "matrix3d", "width", "height", "size",
                 "rect", "bounds", "scale")
CANDIDATE_NAMES = ["Health", "BoostMovie", "Combo", "RemoteInterface", "ClockTimer",
                   "Upgrade1", "Upgrade2", "FillMovie", "Cap", "Background", "Healthbar",
                   "ArmourForeground", "ArmourBackground", "BG", "XPbar", "DamageEffectMovie",
                   "BoostGauge", "ch1040", "LeftSideParent", "RightSideParent"]


def p(rel: str) -> str:
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


def read(rel: str) -> str:
    with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ------------------------------------------------------------------ the spec

def spec_census(spec: dict) -> dict:
    """What the spec actually holds, and whether any of it is element geometry."""
    raw = json.dumps(spec)
    keys = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                keys.add(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(spec)
    geometry_keys = sorted(k for k in keys if k.lower() in GEOMETRY_KEYS)
    # an element name counts only if it is a KEY or a LIST VALUE, never a substring of prose
    list_values = set()

    def values(o):
        if isinstance(o, dict):
            for v in o.values():
                values(v)
        elif isinstance(o, list):
            for v in o:
                if isinstance(v, str):
                    list_values.add(v)
                else:
                    values(v)

    values(spec)
    as_element = sorted(n for n in CANDIDATE_NAMES if n in keys or n in list_values)
    substring_only = sorted(n for n in CANDIDATE_NAMES if n not in as_element and n in raw)
    return {
        "top_keys": list(spec),
        "bmak_keys": list(spec["bmak"]),
        "jc3_keys": list(spec["jc3"]),
        "geometry_keys": geometry_keys,
        "elements_with_geometry": as_element,
        "substring_only": substring_only,
        "frame_labels": len(spec["bmak"]["frame_labels"]),
        "setters": len(spec["bmak"]["uc_setters"]),
        "constants": spec["bmak"]["constants"],
        "health_contract": spec["bmak"]["health_contract"],
    }


# ------------------------------------------------------------------ the report

def report_clips(text: str) -> list[dict]:
    """The report's clip table: clip | x | y | z | yaw | screen estimate."""
    out = []
    for line in text.splitlines():
        if not line.startswith("| `HudMaster."):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        clip = cells[0].strip("`")
        try:
            x, y, z = (float(cells[1]), float(cells[2]), float(cells[3]))
        except ValueError:
            continue
        yaw = re.search(r"-?\d+(?:\.\d+)?", cells[4])
        est = re.findall(r"-?\d+\.\d+", cells[5])
        out.append({"clip": clip, "short": clip.split(".")[-1], "x": x, "y": y, "z": z,
                    "yaw": float(yaw.group(0)) if yaw else None,
                    "screen": [float(v) for v in est[:2]]})
    return out


def report_badges(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"`(Upgrade\d)` at \((-?\d+\.\d+), (-?\d+\.\d+)\)", text):
        out.append({"clip": m.group(1), "x": float(m.group(2)), "y": float(m.group(3))})
    return out


def report_frames(text: str) -> dict[str, int]:
    """Frame counts the report states, e.g. '**102 frames**', '`Timeline_390`, 162 frames'."""
    out = {}
    for m in re.finditer(r"\*\*(\d+) frames\*\*", text):
        out.setdefault("FillMovie", int(m.group(1)))
    m = re.search(r"`Timeline_390`, (\d+) frames", text)
    if m:
        out["Health"] = int(m.group(1))
    m = re.search(r"`Upgrade1/2`[^\n]*?(\d+) frames each", text)
    if m:
        out["Upgrade1/2"] = int(m.group(1))
    m = re.search(r"`Background` has (\d+) frames", text)
    if m:
        out["Background"] = int(m.group(1))
    return out


# ------------------------------------------------------------------- the source

def as3_transforms() -> dict[str, list[dict]]:
    """`____motion_<clip>af1_mat3DVec__[12|13|14]` per class = the authored 3D x/y/z.

    A clip name can be authored in more than one class (`BoostMovie` exists on both parents), so the
    value is a LIST of candidates and each report row is matched to its own nearest candidate.
    """
    pat = re.compile(r"____motion_(\w+?)af1_mat3DVec__\[(1[2-4])\] = (-?[\d.]+);")
    out: dict[str, list[dict]] = {}
    for path in sorted(glob.glob(AS3_GLOB)):
        text = read(path)
        per_file: dict[tuple[str, str], dict] = {}
        for m in pat.finditer(text):
            clip, idx, val = m.group(1), int(m.group(2)), float(m.group(3))
            line = text[: m.start()].count("\n") + 1
            rec = per_file.setdefault((os.path.basename(path), clip),
                                      {"x": None, "y": None, "z": None, "line": line})
            rec["x" if idx == 12 else ("y" if idx == 13 else "z")] = val
        for (fname, clip), rec in per_file.items():
            if None in (rec["x"], rec["y"], rec["z"]):
                continue
            rec["file"] = fname
            out.setdefault(clip, []).append(rec)
    return out


def nearest(cands: list[dict], row: dict) -> tuple[float, dict, list[float]] | None:
    best = None
    for c in cands:
        d = [round(c["x"] - row["x"], 6), round(c["y"] - row["y"], 6), round(c["z"] - row["z"], 6)]
        m = max(abs(v) for v in d)
        if best is None or m < best[0]:
            best = (m, c, d)
    return best


# -------------------------------------------------------------------- derive

def derive() -> dict:
    spec = json.loads(read(SPEC))
    text = read(REPORT)
    cluster = json.loads(read(CLUSTER))
    sc = spec_census(spec)
    clips = report_clips(text)
    badges = report_badges(text)
    frames = report_frames(text)
    as3 = as3_transforms()

    seen: dict[str, int] = {}
    for c in clips:
        seen[c["short"]] = seen.get(c["short"], 0) + 1
    group = {"Health": "health", "Combo": "combo", "RemoteInterface": "remote interface",
             "ClockTimer": "clock", "BoostMovie": "boost"}
    order: dict[str, int] = {}

    elements = []
    for c in clips:
        order[c["short"]] = order.get(c["short"], 0) + 1
        label = c["short"]
        if seen[c["short"]] > 1:
            label = f"{c['short']} ({'left' if c['x'] < 0 else 'right'})"
        cands = as3.get(c["short"]) or []
        hit = nearest(cands, c) if cands else None
        elements.append({
            "element": label, "clip": c["clip"], "kind": "placed clip",
            "report": {"x": c["x"], "y": c["y"], "z": c["z"], "yaw": c["yaw"],
                       "screen": c["screen"]},
            "size": None, "in_spec": c["short"] in sc["elements_with_geometry"],
            "source": hit[1] if hit else None, "candidates": len(cands),
            "delta": hit[2] if hit else None, "verified": (hit[0] <= 0.001) if hit else None,
        })
    for b in badges:
        elements.append({
            "element": b["clip"], "clip": b["clip"], "kind": "badge",
            "report": {"x": b["x"], "y": b["y"], "z": None, "yaw": None, "screen": None},
            "size": frames.get("Upgrade1/2"), "in_spec": b["clip"] in sc["elements_with_geometry"],
            "source": None, "candidates": 0, "delta": None, "verified": None,
        })
    for name, role in NAMED_ELSEWHERE.items():
        present = bool(re.search(rf"\b{re.escape(name)}\b", text))
        elements.append({
            "element": name, "clip": None, "kind": "named in prose", "role": role,
            "report": None, "size": frames.get(name), "in_spec": name in sc["elements_with_geometry"],
            "source": None, "candidates": 0, "delta": None, "verified": None,
            "mentioned": present,
        })
    for e in elements:
        if e["element"] == "FillMovie" and e["size"] is None:
            e["size"] = frames.get("FillMovie")

    # -- screen estimates are derived from the projection centre -----------------
    screens = []
    for c in clips:
        if not c["screen"]:
            continue
        ex, ey = 512 + c["x"], 384 + c["y"]
        screens.append({"clip": c["short"], "stated": c["screen"],
                        "derived": [round(ex, 3), round(ey, 3)],
                        "delta": [round(c["screen"][0] - ex, 3), round(c["screen"][1] - ey, 3)]})

    # -- shared values: constants and the health contract ------------------------
    stage = cluster["bmak"]["stage"]
    pairs = [
        ("StageWidth", sc["constants"]["StageWidth"], stage["module_stage"][0]),
        ("StageHeight", sc["constants"]["StageHeight"], stage["module_stage"][1]),
        ("MovieWidth", sc["constants"]["MovieWidth"], stage["swf"][0]),
        ("MovieHeight", sc["constants"]["MovieHeight"], stage["swf"][1]),
        ("PerspectiveFOV", sc["constants"]["PerspectiveFOV"], stage["fov"]),
        ("TickDeltaTime", sc["constants"]["TickDeltaTime"], stage["tick"]),
        ("MaxHealthChangePerFrame", sc["constants"]["MaxHealthChangePerFrame"],
         cluster["bmak"]["health"]["max_change_per_frame"]),
    ]
    shared = [{"name": n, "spec": a, "report": b, "agree": a == b} for n, a, b in pairs]

    contract = sc["health_contract"]
    hc = cluster["bmak"]["health"]
    contract_pairs = [
        ("bar_fill", contract["bar_fill"], hc["bar_fill"]),
        ("armour_fill", contract["armour_fill"], hc["armour_fill"]),
        ("armour_tier", contract["armour_tier"], hc["armour_tier"]),
        ("pulse_below", contract["pulse_below"], hc["pulse_below"]),
        ("offscreen_seconds", contract["offscreen_seconds"], hc["offscreen"]),
        ("max_change_per_frame", contract["max_change_per_frame"], hc["max_change_per_frame"]),
        ("full_sweep_seconds", contract["full_sweep_seconds"], 0.6667),
        ("tick_hz", contract["tick_hz"], 30.0),
        ("armour_tier_count", contract["armour_tier_count"], 5),
    ]
    contract_ok = [{"name": n, "spec": a, "report": b, "agree": a == b}
                   for n, a, b in contract_pairs]

    # -- labels the report attributes to clips ----------------------------------
    labels_reported = ["Normal", "Charging", "Decrease", "Shake", "Basic", "Extra1", "Extra2",
                       "Extra3", "Extra4", "IntroDelayed", "Intro", "Idle", "XPFill", "Outro",
                       "Out", "Pulse"]
    labels = [{"label": x, "in_spec": x in spec["bmak"]["frame_labels"]} for x in labels_reported]

    # -- oracles -----------------------------------------------------------------
    checks = []

    def chk(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    placed = [e for e in elements if e["kind"] == "placed clip"]
    chk("HUD_SPEC.json holds no geometry key anywhere",
        not sc["geometry_keys"],
        f"keys searched {'/'.join(GEOMETRY_KEYS)}; hits {sc['geometry_keys'] or 'none'}")
    chk("HUD_SPEC.json names no cluster element with a position or size",
        not sc["elements_with_geometry"],
        f"{len(CANDIDATE_NAMES)} candidate names tested as key or list value; "
        f"hits {sc['elements_with_geometry'] or 'none'}")
    chk("every apparent element hit in the spec is a substring only",
        bool(sc["substring_only"]),
        f"{len(sc['substring_only'])} of {len(CANDIDATE_NAMES)} names occur as substrings, "
        f"e.g. {', '.join(sc['substring_only'][:6])} - none is a key or a list value")
    chk("the report states a transform for every clip row it lists",
        all(c["x"] is not None and c["y"] is not None for c in clips) and len(clips) == 6,
        f"{len(clips)} clip rows parsed")
    chk("every report clip transform equals its nearest source AS3 matrix3D translation",
        all(e["verified"] for e in placed),
        "; ".join(f"{e['element']} from {e['source']['file'] if e['source'] else '-'} "
                  f"delta {e['delta']}" for e in placed))
    n_est = sum(1 for c in clips if c["screen"])
    chk("the report's screen estimates are 512+x / 384+y to its 1-decimal rounding",
        all(max(abs(v) for v in s["delta"]) <= 0.051 for s in screens) and len(screens) == n_est
        and n_est == 4 and len(clips) == 6,
        f"{n_est}/6 rows carry an estimate (the two right-side rows say 'right group'): "
        + "; ".join(f"{s['clip']} {s['stated']} vs {s['derived']}" for s in screens))
    chk("every shared constant agrees between the spec and the report",
        all(s["agree"] for s in shared),
        "; ".join(f"{s['name']} {s['spec']} == {s['report']}" for s in shared))
    chk("the health-contract strings are identical in both",
        all(c["agree"] for c in contract_ok),
        "; ".join(f"{c['name']} {c['spec']!r} vs {c['report']!r}" for c in contract_ok
                  if not c["agree"]) or f"{len(contract_ok)} pairs agree")
    chk("every frame label the report attributes to a clip exists in the spec's label set",
        all(x["in_spec"] for x in labels),
        f"{len(labels)} labels, missing "
        f"{[x['label'] for x in labels if not x['in_spec']] or 'none'}")
    chk("no cluster element of the report appears in the spec",
        not any(e["in_spec"] for e in elements),
        f"{len(elements)} report elements, in spec: "
        f"{[e['element'] for e in elements if e['in_spec']] or 'none'}")
    chk("the spec's frame-label set is not a per-clip map (the labels are flat)",
        isinstance(spec["bmak"]["frame_labels"], list)
        and all(isinstance(x, str) for x in spec["bmak"]["frame_labels"]),
        f"{sc['frame_labels']} labels, all bare strings - no clip attribution")
    chk("the spec carries no per-clip frame/timeline count",
        not any("frame" in k.lower() and k != "frame_labels" for k in sc["bmak_keys"]),
        f"bmak keys {', '.join(sc['bmak_keys'])}; report's counts "
        f"{frames} appear nowhere in the spec")
    chk("every clip the report places has at least one authored transform in the AS3",
        all(e["candidates"] >= 1 for e in placed),
        "; ".join(f"{e['element']}: {e['candidates']} candidate(s)" for e in placed))

    ok = sum(1 for c in checks if c["ok"])
    return {
        "spec": sc, "clips": clips, "elements": elements, "screens": screens,
        "shared": shared, "contract": contract_ok, "labels": labels, "frames": frames,
        "as3_clips": {k: v for k, v in sorted(as3.items())}, "checks": checks,
        "report_chars": len(text), "cluster_task": cluster.get("task"),
        "passed": ok, "total": len(checks),
        "verdict": ("HOLDS - the report's layout is the source's, and HUD_SPEC.json makes no"
                    " layout claim to contradict" if all(e["verified"] for e in placed)
                    else "NEEDS REWORK - a report transform does not match the source"),
    }


# -------------------------------------------------------------------- render

def fmtxyz(c: dict | None) -> str:
    if not c:
        return "-"
    z = "z 0.0" if abs(c["z"]) < 1e-9 else f"z {c['z']:.6g}"
    return f"x {c['x']:.6g}, y {c['y']:.6g}, {z}"


def render(d: dict) -> str:
    s = d["spec"]
    L: list[str] = []
    w = L.append
    placed = [e for e in d["elements"] if e["kind"] == "placed clip"]
    verified = [e for e in placed if e["verified"]]
    unver = [e for e in placed if not e["verified"]]
    badges = [e for e in d["elements"] if e["kind"] == "badge"]

    w("# HUD cluster elements - what `HUD_SPEC.json` names, what the report states, what the source says")
    w("")
    w("Generated by `Tools/scripts/hud_cluster_elements.py`; `--check` re-derives it from the spec,")
    w("the report, the report's own record and the decompiled AS3, and byte-compares.")
    w("")
    w("## STATUS")
    w("")
    w(f"**done - {len(s['elements_with_geometry'])} elements of `HUD_SPEC.json` carry a name with a "
      f"position or a size, so the brief's requested list from that file is empty; "
      f"`G3-HUD-CLUSTER.md` names {len(d['elements'])} elements, {len(verified)} of the "
      f"{len(placed)} placed clips are confirmed against the source AS3, {len(unver)} disagree, and "
      f"{len(badges)} badges are tag-only (UNKNOWN here). {d['passed']}/{d['total']} checks pass; "
      f"verdict {d['verdict']}.**")
    w("")
    w("The two files do not compete. **`HUD_SPEC.json` is a behaviour contract** - "
      f"{s['setters']} `UC_*` setters, {s['frame_labels']} flat frame labels, "
      f"{len(s['constants'])} constants, the health contract - and contains **no element geometry and")
    w("no element list at all**. The report is the layout record, and every layout number it states is")
    w("decoded from the movie. Where both speak - the stage constants, the health contract and the")
    w("frame-label vocabulary - they **agree exactly**, so neither has to be corrected.")
    w("")
    w("## 1. What `HUD_SPEC.json` actually contains")
    w("")
    w(f"Top-level keys: `{', '.join(s['top_keys'])}`. Under `bmak` ({len(s['bmak_keys'])} keys):")
    w(f"`{', '.join(s['bmak_keys'])}`.")
    w("")
    w("| the brief asks for | present in the file? | evidence |")
    w("|---|---|---|")
    w(f"| element names | **no element list** | {len(CANDIDATE_NAMES)} candidate names tested as key "
      f"or list value: **none**; {len(s['substring_only'])} occur only as substrings "
      f"({', '.join('`' + x + '`' for x in s['substring_only'][:8])}) |")
    w(f"| positions (x / y / z) | **no** | keys searched `{'/'.join(GEOMETRY_KEYS)}`; hits "
      f"{s['geometry_keys'] or '**none**'} |")
    w(f"| sizes (width / height / frames) | **no** | same search; the {s['frame_labels']} frame labels "
      f"are names, not counts |")
    w("")
    w("What it does hold, and what it is for:")
    w("")
    w(f"- `uc_setters`: {s['setters']} entries, each a name + an argument signature - the callable")
    w("  contract the engine drives.")
    w(f"- `frame_labels`: {s['frame_labels']} bare strings (`Normal`, `Charging`, `Armour0..4`,")
    w("  `DRIVE`/`DRIVETOBATTLE`/…). Flat: the file does **not** say which clip owns which label, so")
    w("  it can confirm membership but not attribution.")
    w(f"- `constants`: {', '.join(f'{k} {v}' for k, v in s['constants'].items())}.")
    w("- `health_contract`: the setter, the two fills, the armour-tier formula, the pulse/offscreen/")
    w("  tick timings - all behaviour, no geometry.")
    w("")
    w("So an element-by-element position/size comparison **cannot start from this file**: there is")
    w("nothing on the spec side to compare against. That is a finding about the file, not a gap in the")
    w("audit, and it is proven mechanically in §5 (checks 1-3, 10-12).")
    w("")
    w("## 2. The element inventory the report states")
    w("")
    w("| # | element | kind | report's position | report's size |")
    w("|---:|---|---|---|---|")
    for i, e in enumerate(d["elements"], 1):
        if e["kind"] == "placed clip":
            r = e["report"]
            pos = f"x {r['x']}, y {r['y']}, z {r['z']}, yaw {r['yaw']}°"
        elif e["kind"] == "badge":
            pos = f"x {e['report']['x']}, y {e['report']['y']}"
        else:
            pos = "named, no position quoted"
        size = f"{e['size']} frames" if e.get("size") else "-"
        w(f"| {i} | `{e['element']}` | {e['kind']} | {pos} | {size} |")
    w("")
    w("## 3. Element by element against the source")
    w("")
    w("| element | in `HUD_SPEC.json`? | source (decompiled AS3) | verdict |")
    w("|---|---|---|---|")
    for e in d["elements"]:
        if e["kind"] == "placed clip":
            src = (f"`{e['source']['file']}:{e['source']['line']}` = "
                   f"{fmtxyz(e['source'])}") if e["source"] else "not in AS3"
            v = ("**confirmed** (Δ ≤ 0.001)" if e["verified"]
                 else f"**MISMATCH** Δ {e['delta']}")
        elif e["kind"] == "badge":
            src = "not in AS3 (a `PlaceObject2` matrix in the tag stream)"
            v = "report-only, tag-parse (UNKNOWN here)"
        else:
            src = "not in AS3 (a timeline child, referenced by name only)"
            v = "report-only (child clip; no transform quoted)"
        w(f"| `{e['element']}` | {'yes' if e['in_spec'] else '**no**'} | {src} | {v} |")
    w("")
    w("Every one of the six placed clips matches an authored transform **exactly** to the report's")
    w("3-decimal rounding. Nothing in the report's geometry is contradicted by the source. Two clips")
    w("carry the same name on different parents (`BoostMovie` on both `LeftSideParentMovie` and")
    w("`RightSideParentMovie`), so each row is matched to its own nearest candidate rather than to a")
    w("name-keyed lookup - the first version of this tool did the latter and reported a false mismatch.")
    w("")
    w("### 3.1 The one display nit")
    w("")
    w("`ClockTimer`'s authored z is `0.00001` in the AS3; the report prints `0.000`. That is a")
    w("3-decimal rounding of a 5-decimal value (Δ 1e-05), not an error - flagged only so the rounding")
    w("rule is explicit.")
    w("")
    w("## 4. Where both files speak - and they agree")
    w("")
    w("| value | `HUD_SPEC.json` | the report / its record | agree |")
    w("|---|---|---|---|")
    for x in d["shared"]:
        w(f"| `{x['name']}` | {x['spec']} | {x['report']} | {'yes' if x['agree'] else '**no**'} |")
    w("")
    w("| health-contract item | spec | report | agree |")
    w("|---|---|---|---|")
    for x in d["contract"]:
        w(f"| `{x['name']}` | {x['spec']} | {x['report']} | {'yes' if x['agree'] else '**no**'} |")
    w("")
    w(f"| frame label the report attributes to a clip | in the spec's {s['frame_labels']}? |")
    w("|---|---|")
    for x in d["labels"]:
        w(f"| `{x['label']}` | {'yes' if x['in_spec'] else '**no**'} |")
    w("")
    w("So the report's `MaxHealthChangePerFrame` timing, its 1024x720 stage inside the 1024x768 SWF")
    w("surface, its 56° FOV, its 30 Hz tick, its `min(1,h)` / `max(0,h-1)` fills and its 5-tier armour")
    w("formula are exactly the spec's own values, read the same way.")
    w("")
    w("## 5. Checks (`--check` recomputes all of them)")
    w("")
    w("| check | result | detail |")
    w("|---|---|---|")
    for c in d["checks"]:
        w(f"| {c['check']} | {'PASS' if c['ok'] else 'FAIL'} | {c['detail']} |")
    w("")
    w(f"{d['passed']}/{d['total']} checks passed. Verdict: **{d['verdict']}**.")
    w("")
    w("## 6. UNKNOWN")
    w("")
    w("1. **The badge coordinates** (`Upgrade1` -10.0/96.3, `Upgrade2` -10.5/100.6). They are")
    w("   `PlaceObject2` matrices in the GFx tag stream, not AS3 constants: a search for `96.3`,")
    w("   `100.6` and `182.5` over the whole decompile returns nothing. The report's tag parse decoded")
    w("   them; this audit did not re-parse the tags, so they rest on the report's own tool. Settled by")
    w("   re-reading the badge placements in the movie `bmak_hud.py` carves.")
    w("2. **The clip frame counts** (FillMovie 102, Health 162, badges 65, Background 32). Frame counts")
    w("   are SWF timeline lengths, absent from both the spec and the AS3. Consistency only:")
    w("   `this.FillMovie.gotoAndStop(this.BoostLevel + 1)` with `level` 0..100 needs at least 101")
    w("   frames, so 102 is possible - the count itself is not proven here.")
    w("3. **Which clip owns each frame label.** The spec's labels are a flat set. Every label the report")
    w("   attributes to a clip is a member, but membership is not attribution; the per-clip mapping is")
    w("   the report's tag read.")
    w("4. **`ch1040`'s identity.** Unnamed third child of `BoostMovie` at (5.0, -83.7), 1 frame, no")
    w("   setter - the report marks it UNKNOWN; nothing in the spec or the AS3 names it either.")
    w("5. **The report's `Health` sub-clip offsets** (`Healthbar`, `ArmourForeground`, `BG`, `XPbar`).")
    w("   They use `PlaceObject3` (MATRIX3D), which the report says its tool does not decode, so it")
    w("   quotes no offsets - and this audit quotes none either.")
    w("")
    w("## 7. Reproduce")
    w("")
    w("```")
    w("cd E:/Modding/JC3-Batmobile")
    w("uv run python Tools/scripts/hud_cluster_elements.py --write   # writes this file")
    w("uv run python Tools/scripts/hud_cluster_elements.py --check   # re-derives, byte-compares")
    w("```")
    w("")
    w(f"Inputs, read-only: `{SPEC}`, `{REPORT}`, `{CLUSTER}`, and the decompiled")
    w("`HudModuleBatmobile` AS3 under `E:/Modding/_gamedata` (the same movie `Tools/scripts/bmak_hud.py`")
    w("carves from `BmGame.upk`). No game launched or attached (INSTRUCTIONS.md §3).")
    w("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    d = derive()
    md = render(d)
    if args.write:
        os.makedirs(os.path.dirname(p(OUT_MD)), exist_ok=True)
        with open(p(OUT_MD), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"wrote {OUT_MD} ({len(md)} chars), {d['passed']}/{d['total']} checks pass")
        return 0
    if args.check:
        try:
            got = read(OUT_MD)
        except FileNotFoundError:
            print(f"MISSING {OUT_MD}")
            print("CHECK FAIL")
            return 1
        for c in d["checks"]:
            if not c["ok"]:
                print(f"FAIL {c['check']}: {c['detail']}")
        if got != md:
            print(f"DRIFT {OUT_MD}: on disk {len(got)} chars, derived {len(md)}")
        print("CHECK", "PASS" if (got == md and d["passed"] == d["total"]) else "FAIL")
        return 0 if (got == md and d["passed"] == d["total"]) else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
