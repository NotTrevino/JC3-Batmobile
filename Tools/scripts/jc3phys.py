"""jc3phys.py - wheel stations out of JC3's Havok `.physicsc` (GRB-G2-8).

`.physicsc` is **not** an RTPC property file: every one of the 233 in the game
starts with `57E0E057` and carries `__classnames__` / `__types__` / `__data__`,
i.e. it is a Havok 2014 binary packfile (`hk_2014.1.0-r1`).  ConvertProperty
cannot read it, and a full packfile reader (type library + object graph) is a
project of its own.

What *is* recoverable without one is the one datum the project already moves by
hand: the **four wheel-station quads**. Each is a `float4 (x, y, z, 1.0)` in the
data section, and together they form a rectangle:

    (+a, y, z_rear, 1)  (-a, y, z_rear, 1)
    (+a, y, z_front, 1) (-a, y, z_front, 1)

so `track = 2a` and `wheelbase = z_front - z_rear`. The layout is confirmed
against the Serpente, whose stations this project already knows from MODLOG §65
(`x 0.885, y 0.4, z -1.557 / +1.446` -> track 1.77 m, wheelbase 3.003 m).

The detector is deliberately strict, because `w == 1.0` also appears in every
transform row of every matrix in the file:

  * candidate = aligned float4 with `w == 1.0`, `|x| 0.05..3`, `y 0.05..2.5`,
    `|z| 0.05..8`;
  * candidates are grouped by `y` (the hub height is identical for all four
    wheels of a vehicle);
  * a group is a station set only if it holds **exactly four** quads with one
    distinct `|x|` present at both signs and two distinct `z`, each at both
    signs.

`check` re-derives the Serpente's numbers and fails if they move.

Usage:
  python jc3phys.py build --all
  python jc3phys.py report
  python jc3phys.py check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jc3index import DEFAULT_GAME, DEFAULT_OUT, load_index, MOUNT_RANK  # noqa: E402
from eetoc import unaaf, sarc_dir  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")

SERPENTE = {
    "entity": ("editor/entities/jc_vehicles/01_land/"
               "v0300_car_kensington_sportsmuscle/"
               "v0300_car_kensington_sportsmuscle_civilian_01.ee"),
    "x": 0.885, "y": 0.4, "z": (-1.557, 1.446),
}


def find_stations(blob: bytes) -> list[dict]:
    cands = []
    for i in range(0, len(blob) - 15, 4):
        x, y, z, w = struct.unpack_from("<4f", blob, i)
        if w != 1.0:
            continue
        if not (0.05 < abs(x) < 3.0 and 0.05 < y < 2.5 and 0.05 < abs(z) < 8.0):
            continue
        cands.append((i, x, y, z))
    groups: dict[float, list] = {}
    for t in cands:
        groups.setdefault(round(t[2], 3), []).append(t)
    out = []
    for y, g in groups.items():
        if len(g) != 4:
            continue
        xs = {round(abs(t[1]), 3) for t in g}
        if len(xs) != 1:
            continue
        if {t[1] > 0 for t in g} != {True, False}:
            continue
        zs = {round(t[3], 3) for t in g}
        if len(zs) != 2:
            continue
        a = xs.pop()
        z1, z2 = sorted(zs)
        out.append({
            "x": a,
            "y": y,
            "z_rear": z1,
            "z_front": z2,
            "track_m": round(2 * a, 4),
            "wheelbase_m": round(z2 - z1, 4),
            "quads_at": sorted(t[0] for t in g),
        })
    return out


def physics_of(ee_path: str, rows: list[dict], game: str) -> list[dict]:
    hits = [r for r in rows if r["path"] == ee_path]
    if not hits:
        raise SystemExit(f"not in index: {ee_path}")
    r = sorted(hits, key=lambda r: MOUNT_RANK[r["mount"]])[-1]
    with open(os.path.join(game, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        raw = f.read(r["size"])
    stream, entries = unaaf(raw), None
    entries = sarc_dir(stream)
    out = []
    for name, off, size in entries:
        if not name.endswith(".physicsc"):
            continue
        blob = stream[off:off + size]
        out.append({
            "file": name,
            "size": size,
            "havok": blob[:4].hex().upper() == "57E0E057",
            "stations": find_stations(blob),
        })
    return out


def vehicle_ees(rows: list[dict], only: str | None) -> list[str]:
    out = set()
    for r in rows:
        p = r["path"]
        if p.startswith("editor/entities/jc_vehicles/") and p.endswith(".ee"):
            if not only or only.lower() in p.lower():
                out.add(p)
    return sorted(out)


def slug(p: str) -> str:
    parent = p.rsplit("/", 1)[0].rsplit("/", 1)[-1]
    return f"{parent}__{p.rsplit('/', 1)[-1]}"


def cmd_build(a) -> int:
    rows = load_index(a.index)
    targets = vehicle_ees(rows, a.entity)
    if a.limit:
        targets = targets[:a.limit]
    os.makedirs(os.path.join(RAW, "phys"), exist_ok=True)
    print(f"{len(targets)} entities")
    for i, p in enumerate(targets, 1):
        try:
            docs = physics_of(p, rows, a.game)
        except Exception as e:
            print(f"[{i}/{len(targets)}] {os.path.basename(p)}: ERROR {e}")
            continue
        n = sum(len(d["stations"]) for d in docs)
        with open(os.path.join(RAW, "phys", slug(p) + ".json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump({"entity": p, "physics": docs}, f, indent=0)
        print(f"[{i}/{len(targets)}] {os.path.basename(p)}: {len(docs)} file(s), "
              f"{n} station set(s)")
    return 0


def load_phys() -> list[dict]:
    d = os.path.join(RAW, "phys")
    if not os.path.isdir(d):
        raise SystemExit(f"nothing grabbed under {d}")
    return [json.load(open(os.path.join(d, fn), encoding="utf-8"))
            for fn in sorted(os.listdir(d)) if fn.endswith(".json")]


def land_global_stations() -> dict[str, dict]:
    """The named station set per entity, from the module grab (`land_global.vmodc`)."""
    d = os.path.join(RAW, "entities")
    out: dict[str, dict] = {}
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(d, fn), encoding="utf-8"))
        cands = [m for m in doc["modules"] if m.get("type") == "LandGlobal"
                 and not m["file"].endswith("_ai.vmodc")]
        if not cands:
            continue
        cands.sort(key=lambda m: ("00_shared" in m["file"], m["file"]))
        pts: dict[int, list[float]] = {}
        for r in cands[0]["rows"]:
            k = r["path"]
            if not k.startswith("base_wheel_hardpoint_positions["):
                continue
            idx = int(k.split("[", 1)[1].split("]", 1)[0])
            axis = int(k.rsplit("[", 1)[1].rstrip("]"))
            pts.setdefault(idx, [0.0, 0.0, 0.0])[axis] = float(r["value"])
        if len(pts) < 2:
            continue
        xs = [p[0] for p in pts.values()]
        zs = [p[2] for p in pts.values()]
        out[doc["entity"]] = {
            "x": round(max(abs(x) for x in xs), 4),
            "y": round(sum(p[1] for p in pts.values()) / len(pts), 4),
            "z_rear": round(min(zs), 4),
            "z_front": round(max(zs), 4),
        }
    return out


def body_size() -> dict[str, tuple[float, float, float]]:
    """Longest mesh bounds per entity, from the jc3detail grab (if present)."""
    d = os.path.join(RAW, "detail")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        if not fn.endswith(".json"):
            continue
        doc = json.load(open(os.path.join(d, fn), encoding="utf-8"))
        best = max((m for m in doc["meshes"] if "size_m" in m),
                   key=lambda m: m["size_m"]["z"], default=None)
        if best:
            s = best["size_m"]
            out[doc["entity"]] = (s["x"], s["y"], s["z"])
    return out


def cmd_report(a) -> int:
    docs = load_phys()
    body = body_size()
    lines = ["# JC3 wheel stations from `.physicsc`", "",
             f"Recovered by `Tools/scripts/jc3phys.py` from **{len(docs)}** entity bundles.",
             "`.physicsc` is a Havok 2014 packfile, so these are read structurally (four",
             "`float4` station quads forming a rectangle), not via a full Havok reader.", ""]

    lg = land_global_stations()
    agree, disagree = [], []
    for d in docs:
        for f in d["physics"][:1]:
            for s in f["stations"]:
                ref = lg.get(d["entity"])
                if not ref:
                    continue
                same = (abs(s["x"] - ref["x"]) < 1e-3 and abs(s["y"] - ref["y"]) < 1e-3
                        and abs(s["z_rear"] - ref["z_rear"]) < 1e-3
                        and abs(s["z_front"] - ref["z_front"]) < 1e-3)
                (agree if same else disagree).append(d["entity"])

    found, multi, none = 0, 0, 0
    rows = []
    for d in docs:
        sets = [s for f in d["physics"] for s in f["stations"]]
        if len(sets) == 1:
            found += 1
            s = sets[0]
            b = body.get(d["entity"])
            ratio = round(s["wheelbase_m"] / b[2], 3) if b and b[2] else ""
            rows.append((d["entity"], s, b, ratio))
        elif sets:
            multi += 1
        else:
            none += 1

    lines += [f"One station set: **{found}** entities; more than one: {multi}; none: {none}.", "",
              f"Cross-check against the named `land_global.base_wheel_hardpoint_positions`: "
              f"**{len(agree)} agree**, {len(disagree)} disagree "
              f"({len(lg)} entities have named stations).", ""]
    if disagree:
        lines += ["Disagreements: " + ", ".join(f"`{e.rsplit('/', 3)[-2]}`" for e in disagree), ""]
    if rows:
        wbs = sorted(r[1]["wheelbase_m"] for r in rows)
        trs = sorted(r[1]["track_m"] for r in rows)
        lines += ["| quantity | min | median | max |", "|---|---|---|---|",
                  f"| wheelbase (m) | {wbs[0]} | {wbs[len(wbs)//2]} | {wbs[-1]} |",
                  f"| track (m) | {trs[0]} | {trs[len(trs)//2]} | {trs[-1]} |", ""]

        ratios = sorted(r[3] for r in rows if r[3] != "")
        if ratios:
            lines += [f"wheelbase / body length: {ratios[0]} … {ratios[-1]} "
                      f"(median {ratios[len(ratios)//2]}) — a plausibility check, not a rule.", ""]

        lines += ["## Land vehicles", "",
                  "| entity | track | wheelbase | hub y | body x×y×z | wb/length |",
                  "|---|---|---|---|---|---|"]
        land = [r for r in rows if "/01_land/" in r[0]]
        land.sort(key=lambda r: r[1]["wheelbase_m"])
        for ent, s, b, ratio in land:
            bs = f"{b[0]} × {b[1]} × {b[2]}" if b else ""
            lines.append(f"| `{ent.rsplit('/', 2)[-2]}/{ent.rsplit('/', 1)[-1]}` | "
                         f"{s['track_m']} | {s['wheelbase_m']} | {s['y']} | {bs} | {ratio} |")
        lines.append("")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "PHYSICS.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"PHYSICS.md: {found} entities with one station set, {multi} with several, {none} with none")
    return 0


def cmd_check(a) -> int:
    rows = load_index(a.index)
    docs = physics_of(SERPENTE["entity"], rows, a.game)
    problems = []
    sets = [s for f in docs for s in f["stations"]]
    print(f"donor: {len(docs)} physicsc, {len(sets)} station set(s)")
    for s in sets:
        print(f"  x={s['x']} y={s['y']} z={s['z_rear']}..{s['z_front']} "
              f"track={s['track_m']} wheelbase={s['wheelbase_m']}")
    if len(sets) != 1:
        problems.append(f"expected exactly one station set, got {len(sets)}")
    else:
        s = sets[0]
        if abs(s["x"] - SERPENTE["x"]) > 1e-3:
            problems.append(f"x {s['x']} != {SERPENTE['x']}")
        if abs(s["y"] - SERPENTE["y"]) > 1e-3:
            problems.append(f"y {s['y']} != {SERPENTE['y']}")
        if (round(s["z_rear"], 3), round(s["z_front"], 3)) != SERPENTE["z"]:
            problems.append(f"z {s['z_rear']}..{s['z_front']} != {SERPENTE['z']}")
    for f in docs:
        if not f["havok"]:
            problems.append(f"{f['file']} is not tagged 57E0E057")
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
    b = sub.add_parser("build", help="read station quads from every vehicle's physicsc")
    b.add_argument("--entity", help="substring filter")
    b.add_argument("--all", action="store_true")
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--index", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)
    r = sub.add_parser("report", help="write PHYSICS.md")
    r.set_defaults(func=cmd_report)
    c = sub.add_parser("check", help="assert the Serpente's known stations")
    c.add_argument("--game", default=DEFAULT_GAME)
    c.add_argument("--index", default=DEFAULT_OUT)
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
