"""jc3fleet.py - the fleet table and the donor matrix (GRB-G2-5 / T-1 input).

Purely derived: reads the decodes already produced by `jc3grab.py` (module
values) and `jc3detail.py` (body bounds) and writes ONE table per land vehicle
with the quantities a donor choice actually depends on:

    body L × W × H      longest `.rbm` in the bundle
    wheelbase, track    `land_global.base_wheel_hardpoint_positions`
    hub height          same quads (`y`)
    tyre radius/width   `land_global.front/rear_wheels.*`
    mass                `rigid_body.mass`
    top speed           `vehicle_misc.official_top_speed` (+ `transmission.top_speed`)
    steering            `land_steering.t_to_full_steer_s`, `steer_angle_*`
    engine              `land_engine.max_rpm` / `optimal_rpm`

`land_global` is chosen over its `*_ai` twin on purpose: the AI copy carries
different values (`front_wheels.mass` 75 vs 25 on the Serpente).

Ranking is Euclidean distance over the four geometric quantities the Batmobile
already has, each normalised by the Batmobile's own value:

    length 7.026 m · wheelbase 5.029 m · track 2.416 m · tyre radius 0.6826 m

That is a *nearest-shape* ranking, not a verdict: it says which shipped vehicle
is the least wrong starting point, so T-1 can decide with a number instead of a
feeling.

Usage:
  python jc3fleet.py report
  python jc3fleet.py check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")

BATMOBILE = {
    "length": 7.026,
    "wheelbase": 5.029,
    "track": 2.416,
    "tyre_radius": 0.6826,
}


def load(dirname: str) -> list[dict]:
    d = os.path.join(RAW, dirname)
    if not os.path.isdir(d):
        raise SystemExit(f"no {dirname} grab under {d}")
    return [json.load(open(os.path.join(d, fn), encoding="utf-8"))
            for fn in sorted(os.listdir(d)) if fn.endswith(".json")]


def pick_land_global(mods: list[dict]) -> dict | None:
    """The player copy of `land_global`, never the `_ai` twin."""
    cands = [m for m in mods if m.get("type") == "LandGlobal"
             and not m["file"].endswith("_ai.vmodc")]
    if not cands:
        return None
    # two non-AI copies exist on a few entities (shared + local); prefer the local one
    cands.sort(key=lambda m: ("00_shared" in m["file"], m["file"]))
    return cands[0]


def rows_of(mod: dict) -> dict:
    out: dict[str, object] = {}
    for r in mod["rows"]:
        p = r["path"]
        if p.startswith("base_wheel_hardpoint_positions"):
            out[p] = r["value"]
        else:
            out[p] = r["value"]
    return out


def station_geometry(rows: dict) -> dict | None:
    pts = {}
    for k, v in rows.items():
        if not k.startswith("base_wheel_hardpoint_positions["):
            continue
        idx = int(k.split("[", 1)[1].split("]", 1)[0])
        axis = int(k.rsplit("[", 1)[1].rstrip("]"))
        pts.setdefault(idx, [0.0, 0.0, 0.0])[axis] = float(v)
    if len(pts) < 2:
        return None
    xs = [p[0] for p in pts.values()]
    ys = [p[1] for p in pts.values()]
    zs = [p[2] for p in pts.values()]
    hub = sum(ys) / len(ys)
    half = max(abs(x) for x in xs)
    return {
        "wheels": len(pts),
        "hub_y": round(hub, 4),
        "half_track": round(half, 4),
        "track": round(2 * half, 4),
        "z_rear": round(min(zs), 4),
        "z_front": round(max(zs), 4),
        "wheelbase": round(max(zs) - min(zs), 4),
    }


def module(mods: list[dict], typ: str, skip_ai: bool = True) -> dict | None:
    cands = [m for m in mods if m.get("type") == typ
             and not (skip_ai and m["file"].endswith("_ai.vmodc"))]
    if not cands:
        return None
    cands.sort(key=lambda m: ("00_shared" in m["file"], m["file"]))
    return cands[0]


def val(m: dict | None, name: str):
    if not m:
        return None
    for r in m["rows"]:
        if r["path"] == name:
            return r["value"]
    return None


def body_bounds(detail: list[dict]) -> dict[str, tuple[float, float, float]]:
    out = {}
    for d in detail:
        best = max((m for m in d["meshes"] if "size_m" in m),
                   key=lambda m: m["size_m"]["z"], default=None)
        if best:
            s = best["size_m"]
            out[d["entity"]] = (s["x"], s["y"], s["z"])
    return out


def build_rows() -> list[dict]:
    ents = load("entities")
    detail = {d["entity"]: d for d in load("detail")}
    bodies = body_bounds(list(detail.values()))
    out = []
    for d in ents:
        mods = d["modules"]
        lg = pick_land_global(mods)
        if not lg:
            continue
        rows = rows_of(lg)
        geo = station_geometry(rows)
        if not geo:
            continue
        rb = module(mods, "RigidBody")
        tr = module(mods, "Transmission")
        vm = module(mods, "VehicleMisc")
        le = module(mods, "LandEngine")
        ls = module(mods, "LandSteering")
        body = bodies.get(d["entity"])
        rec = {
            "entity": d["entity"],
            "category": "land" if "/01_land/" in d["entity"] else
                        ("air" if "/02_air/" in d["entity"] else "sea"),
            "body": body,
            **geo,
            "tyre_radius": val(lg, "front_wheels.radius"),
            "tyre_width_front": val(lg, "front_wheels.width"),
            "tyre_width_rear": val(lg, "rear_wheels.width"),
            "ground_clearance": val(lg, "ground_clearance"),
            "mass": val(rb, "mass"),
            "inertia_yaw": val(rb, "unit_inertia_yaw"),
            "top_speed": val(vm, "official_top_speed"),
            "transmission_top_speed": val(tr, "top_speed"),
            "gears": val(tr, "gears"),
            "max_rpm": val(le, "max_rpm"),
            "steer_time": val(ls, "t_to_full_steer_s"),
            "steer_min_deg": val(ls, "steer_angle_min_speed_deg"),
            "steer_max_deg": val(ls, "steer_angle_max_speed_deg"),
        }
        if body:
            rec["length"] = body[2]
            rec["width"] = body[0]
            rec["height"] = body[1]
            diffs = []
            for k in ("length", "wheelbase", "track", "tyre_radius"):
                v = rec.get(k)
                if v:
                    diffs.append(((v - BATMOBILE[k]) / BATMOBILE[k]) ** 2)
            rec["score"] = round(math.sqrt(sum(diffs) / len(diffs)), 4) if diffs else None
        out.append(rec)
    return out


def cmd_report(a) -> int:
    fleet = build_rows()
    land = [r for r in fleet if r["category"] == "land" and r.get("score") is not None]
    land.sort(key=lambda r: r["score"])
    lines = ["# JC3 fleet — geometry, handling and the donor matrix", "",
             f"Derived from the decode in this folder by `Tools/scripts/jc3fleet.py`.",
             f"**{len(fleet)}** vehicles have a `land_global` station set; **{len(land)}** of them are",
             "land vehicles with a measurable body, which is the set that can host the Batmobile.", "",
             "Batmobile targets (from the built mod): length **7.026 m**, wheelbase **5.029 m**,",
             "track **2.416 m**, tyre radius **0.6826 m**. `score` is the RMS relative error over",
             "those four; lower is closer. It ranks *shape*, not behaviour.", "",
             "## Nearest shapes", "",
             "| # | entity | score | L×W×H | wheelbase | track | tyre Ø | mass | top |",
             "|---|---|---|---|---|---|---|---|---|"]

    def short(ent: str) -> str:
        return f"{ent.rsplit('/', 2)[-2]}/{ent.rsplit('/', 1)[-1]}".replace(".ee", "")

    for i, r in enumerate(land[:20], 1):
        body = f"{r['length']:.2f}×{r['width']:.2f}×{r['height']:.2f}"
        tyre = f"{2 * r['tyre_radius']:.2f}" if r.get("tyre_radius") else ""
        lines.append(f"| {i} | `{short(r['entity'])}` | {r['score']} | {body} | "
                     f"{r['wheelbase']} | {r['track']} | {tyre} | {r.get('mass') or ''} | "
                     f"{r.get('top_speed') or ''} |")
    lines.append("")

    donor = [r for r in land if "v0300_car_kensington_sportsmuscle_civilian_01" in r["entity"]]
    if donor:
        r = donor[0]
        rank = land.index(r) + 1
        lines += ["## Current donor", "",
                  f"`{short(r['entity'])}` ranks **{rank} of {len(land)}** by shape. "
                  f"Wheelbase {r['wheelbase']} m against the Batmobile's 5.029 m, track {r['track']} m "
                  f"against 2.416 m, tyre Ø {2 * r['tyre_radius']:.2f} m against 1.365 m.", ""]

    lines += ["## All land vehicles", "",
              "| entity | L | W | H | wheelbase | track | hub y | tyre r | mass | top |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(land, key=lambda r: -(r.get("length") or 0)):
        lines.append(f"| `{short(r['entity'])}` | {r.get('length')} | {r.get('width')} | "
                     f"{r.get('height')} | {r['wheelbase']} | {r['track']} | {r['hub_y']} | "
                     f"{r.get('tyre_radius')} | {r.get('mass') or ''} | {r.get('top_speed') or ''} |")
    lines.append("")

    missing = [r for r in fleet if r["category"] == "land" and not r.get("body")]
    lines += ["## Notes", "",
              f"- {len(fleet) - len(land)} vehicles have stations but no comparable body "
              f"(air/sea, or no mesh bounds).",
              f"- {len(missing)} land vehicles lack a body bound; they are in the fleet table but "
              "cannot be scored.",
              "- `land_global` stations are named members, so this table is a decode, not a "
              "heuristic: the Serpente's four quads match its `.physicsc` copy to the last digit.",
              ""]

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "FLEET.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"FLEET.md: {len(fleet)} vehicles with stations, {len(land)} scored land vehicles")
    return 0


def cmd_check(a) -> int:
    fleet = {r["entity"]: r for r in build_rows()}
    problems = []
    key = ("editor/entities/jc_vehicles/01_land/"
           "v0300_car_kensington_sportsmuscle/"
           "v0300_car_kensington_sportsmuscle_civilian_01.ee")
    r = fleet.get(key)
    if not r:
        problems.append("donor missing from the fleet table")
    else:
        print(f"donor: wheels={r['wheels']} wheelbase={r['wheelbase']} track={r['track']} "
              f"tyre_r={r['tyre_radius']} mass={r['mass']} top={r['top_speed']} "
              f"score={r.get('score')}")
        for k, want in (("wheelbase", 3.003), ("track", 1.77)):
            if abs(r[k] - want) > 1e-3:
                problems.append(f"{k} {r[k]} != {want}")
        if r["mass"] != 975:
            problems.append(f"mass {r['mass']} != 975")
        if r["tyre_radius"] != 0.379999995:
            problems.append(f"tyre_radius {r['tyre_radius']} != 0.38")
        if r["wheels"] != 4:
            problems.append(f"wheels {r['wheels']} != 4")
    if len(fleet) < 140:
        problems.append(f"only {len(fleet)} vehicles with stations")
    if problems:
        for p in problems:
            print("FAIL", p)
        return 1
    print(f"check ok: {len(fleet)} vehicles")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="write FLEET.md")
    r.set_defaults(func=cmd_report)
    c = sub.add_parser("check", help="assert the donor's geometry")
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
