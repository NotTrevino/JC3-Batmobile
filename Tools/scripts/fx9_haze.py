"""fx9_haze.py - is there a heat-haze / distortion carrier among JC3's effects? (T-FX9)

T-FX9 ("out") says JC3 has no haze path.  The earlier test was a keyword scan of
the 955 `EffectRTSystem` `.effc` *paths* (`haze`, `steam`, `heat`), which found one
file and called it a heater.  This tool answers the same question at the level the
format actually stores:

  1. **paths**   - keyword scan over all 955 distinct `.effc` paths.
  2. **content** - every string value in every one of those 955 files.  The format
                   is ADF v4; if a texture or shader name were stored, it would be
                   a `String` (0x8955583E) value and would show up here.
  3. **textures** - `.trim` records are named `<texture>.<grid>.trim`, so the trim
                   pool is the only place JC3 names a texture.  Scan all of them
                   for distortion/refraction words.
  4. **shader ids** - the renderer's identity for a material is
                   `Instantiators[].RenderInfos[].RenderBlockTypeHash` (uint32).
                   Count the distinct values over the 955 so "which shader" can be
                   answered as a set of ids instead of a name.
  5. **candidates** - full emitter census of the effects that could carry heat
                   shimmer (car exhaust, jet/turbine exhaust, rotor wash, fire,
                   Bavarium trails, the `car_speedrom_heater` effect itself).
  6. **BmAK side** - which of the 206 BmAK particle systems carry a distortion or
                   steam material (`PARTICLES_FEATURES.json`), since the `heat-steam`
                   feature group itself ships 0 systems.

Read-only: opens the game archives through `jc3fx`, never writes to a game folder.

Usage:
  python fx9_haze.py write --write
  python fx9_haze.py check --check
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3fx  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
TABLE = os.path.join(OUT, "FX_TABLE.jsonl")
BM = os.path.join(ROOT, "Research", "BatmobileGrab", "PARTICLES_FEATURES.json")
MD = os.path.join(OUT, "FX9_HAZE.md")
JS = os.path.join(OUT, "FX9_HAZE.json")

PATH_WORDS = ("haze", "steam", "heat", "distort", "refract", "vapor", "vapour",
              "shimmer", "warp", "exhaust", "afterburner", "jet", "turbine",
              "bavarium", "fire", "smoke", "rotor")
TRIM_WORDS = ("dist", "refract", "haze", "heat", "steam", "vapor", "vapour",
              "warp", "shimmer", "blur")
CANDIDATES = [
    "effects/jc_vehicles/exhaust/car_speedrom_heater.effc",
    "effects/jc_vehicles/exhaust/car_cycle_base.effc",
    "effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc",
    "effects/jc_vehicles/exhaust/jet_exhaust_base.effc",
    "effects/jc_vehicles/exhaust/jet_cargo_exhaust_base.effc",
    "dlc/bavarium_sea_heist/effects/jc_vehicles/exhaust/rocketboat_jet_exhaust.effc",
    "effects/jc_vehicles/exhaust/helicopter_base.effc",
    "effects/jc_vehicles/damage/dmg_fire_engine.effc",
    "effects/jc_vehicles/traversal_air/rotor_wash_asphalt.effc",
    "effects/trails/bavarium_trail_03.effc",
    "effects/fire/generic_fire_single_01.effc",
    "effects/jc_environments/structures/military/bavarium_refinery_explosion.effc",
]
IDX_RE = jc3fx.IDX_RE


def load_table() -> list[dict]:
    return [json.loads(l) for l in open(TABLE, encoding="utf-8") if l.strip()]


def best_effc(tab: list[dict]) -> dict[str, dict]:
    best: dict[str, dict] = {}
    for r in tab:
        if r.get("ext") != ".effc" or r.get("error") or r.get("root") != "EffectRTSystem":
            continue
        cur = best.get(r["path"])
        if cur is None or jc3fx.MOUNT_RANK[r["mount"]] > jc3fx.MOUNT_RANK[cur["mount"]]:
            best[r["path"]] = r
    return best


def array_len(rows, prefix: str) -> int:
    top = -1
    for p, _t, _v in rows:
        if p.startswith(prefix):
            m = IDX_RE.search(p, len(prefix) - 2)
            if m:
                top = max(top, int(m.group(1)))
    return top + 1


def scan() -> dict:
    tab = load_table()
    effc = best_effc(tab)
    idx = jc3fx.pick_by_path(jc3fx.load_index(jc3fx.DEFAULT_OUT))

    path_hits = {w: sorted(p for p in effc if w in p.lower()) for w in PATH_WORDS}

    trim_names = collections.Counter()
    for r in tab:
        if r.get("ext") == ".trim":
            trim_names[r["path"]] += 1
    trim_dist = {}
    for w in TRIM_WORDS:
        hits = sorted(n for n in trim_names if w in n.lower())
        if hits:
            trim_dist[w] = hits

    by_container: dict[str, list[dict]] = {}
    for r in effc.values():
        by_container.setdefault(r["container"], []).append(r)

    block = collections.Counter()
    type_h = collections.Counter()
    strings: dict[str, int] = {}
    cand_rows: dict[str, list] = {}
    want = set(CANDIDATES)
    decoded = 0
    for container, group in sorted(by_container.items()):
        try:
            if container:
                blob = jc3fx.read_row(idx[container], jc3fx.DEFAULT_GAME)
                items = dict(jc3fx.inner_fx(blob, jc3fx.EXTS))
            else:
                items = {g["source"]: jc3fx.read_row(idx[g["source"]], jc3fx.DEFAULT_GAME)
                         for g in group}
                items = {g["path"]: items[g["source"]] for g in group}
        except Exception as e:                                   # noqa: BLE001
            print(f"CONTAINER FAIL {container!r}: {e}", flush=True)
            continue
        for r in group:
            data = items.get(r["path"])
            if data is None:
                continue
            try:
                rr = jc3fx.decode(data)["_rows"]
            except Exception as e:                               # noqa: BLE001
                print(f"DECODE FAIL {r['path']}: {e}", flush=True)
                continue
            decoded += 1
            seen_b = set()
            seen_t = set()
            for p, _t, v in rr:
                if isinstance(v, str) and v:
                    strings[v] = strings.get(v, 0) + 1
                if not isinstance(v, int):
                    continue
                if p.endswith("RenderBlockTypeHash"):
                    seen_b.add(v)
                if p.endswith("TypeHash"):
                    seen_t.add(v)
            for h in seen_b:
                block[str(h)] += 1
            for h in seen_t:
                type_h[str(h)] += 1
            if r["path"] in want:
                cand_rows[r["path"]] = (len(data), rr)
        items = None

    candidates = []
    for path in CANDIDATES:
        if path not in cand_rows:
            candidates.append({"path": path, "missing": True,
                               "containers": sum(1 for r in tab if r["path"] == path)})
            continue
        size, rr = cand_rows[path]
        blocks = collections.Counter()
        for p, _t, v in rr:
            if p.endswith("RenderBlockTypeHash"):
                blocks[str(v)] += 1
        mp = [v for p, _t, v in rr if p.endswith("MaxParticles")]
        tflags = [v for p, _t, v in rr if p.endswith("EmitterTemplates")or False]
        tflags = [v for p, _t, v in rr if p.endswith(".Flags")
                  and p.startswith("EmitterTemplates[")]
        eflags = [v for p, _t, v in rr if p.endswith(".Flags") and p.startswith("Emitters[")]
        candidates.append({
            "path": path,
            "size": size,
            "rows": len(rr),
            "containers": sum(1 for r in tab if r["path"] == path),
            "instantiators": array_len(rr, "Instantiators["),
            "emitters": array_len(rr, "Emitters["),
            "templates": array_len(rr, "EmitterTemplates["),
            "max_particles": mp,
            "template_flags": tflags,
            "emitter_flags": eflags,
            "blocks": dict(blocks),
            "properties": [v for p, _t, v in rr if p.startswith("Properties[")],
            "output_buffer_size": [v for p, _t, v in rr if p.endswith("OutputBufferSize")],
            "trim_index": [v for p, _t, v in rr if p.endswith("TrimIndex")],
        })

    bm = json.load(open(BM, encoding="utf-8"))
    seen = set()
    dist_systems = []
    exhaust_systems = []
    for s in bm["systems"]:
        if s["name"] in seen:
            continue
        mats = [m for m in s.get("materials") or []
                if any(w in str(m).lower() for w in ("distort", "steam", "refract"))]
        if mats:
            seen.add(s["name"])
            dist_systems.append({"name": s["name"], "group": s["group"],
                                 "emitters": (s.get("emitters") or {}).get("total"),
                                 "lifetime": s.get("lifetime"),
                                 "materials": mats})
    for s in bm["systems"]:
        if s["name"] in seen:
            continue
        if s["group"] == "afterburner-exhaust":
            seen.add(s["name"])
            exhaust_systems.append({"name": s["name"], "group": s["group"],
                                    "emitters": (s.get("emitters") or {}).get("total"),
                                    "kinds": (s.get("emitters") or {}).get("kinds"),
                                    "lifetime": s.get("lifetime"),
                                    "materials": s.get("materials")})

    doc = {
        "effc_paths": len(effc),
        "effc_rows_in_table": sum(1 for r in tab if r.get("ext") == ".effc"),
        "files_decoded": decoded,
        "string_values": len(strings),
        "string_examples": dict(list(strings.items())[:10]),
        "path_hits": {w: {"n": len(v), "paths": v[:12]} for w, v in path_hits.items()},
        "trim_records": sum(1 for r in tab if r.get("ext") == ".trim"),
        "trim_names": len(trim_names),
        "trim_distortion": trim_dist,
        "trim_distortion_containers": {
            w: {n: sum(1 for r in tab if r.get("ext") == ".trim" and r["path"] == n)
                for n in hits} for w, hits in trim_dist.items()},
        "block_hashes": dict(block),
        "type_hashes": len(type_h),
        "candidates": candidates,
        "bmak_distortion_systems": dist_systems,
        "bmak_afterburner_systems": exhaust_systems,
        "bmak_heat_steam": next(
            (g for g in bm["groups"]
             if isinstance(g, dict)
             and "heat-steam" in (str(g.get("group", "")), str(g.get("name", "")))),
            None),
    }
    doc["digest"] = hashlib.sha1(
        json.dumps({k: v for k, v in doc.items() if k != "digest"},
                   sort_keys=True).encode()).hexdigest()
    return doc


# ------------------------------------------------------------------------ write
def want(e) -> dict[str, str]:
    """Which sources a candidate is carried by, rendered for the md."""
    return e.get("blocks") or {}


def write_md(doc: dict) -> str:
    L = []
    A = L.append
    A("# T-FX9 / B08-14 - is there a heat-haze carrier in JC3's effects?")
    A("")
    A("Regenerated by `python Tools/scripts/fx9_haze.py --write`; `--check` re-scans the")
    A("archives and re-derives every number and the digest below. Read-only.")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A(f"| distinct `.effc` paths with root `EffectRTSystem` | **{doc['effc_paths']}** |")
    A(f"| of those, decoded this run | {doc['files_decoded']} |")
    A(f"| **string values found in all of them** | **{doc['string_values']}** |")
    A(f"| distinct `RenderBlockTypeHash` (material/shader identity) | **{len(doc['block_hashes'])}** |")
    A(f"| distinct `TypeHash` (emitter/modifier classes) | {doc['type_hashes']} |")
    A(f"| `.trim` records / distinct texture names | {doc['trim_records']} / **{doc['trim_names']}** |")
    A(f"| digest | `{doc['digest']}` |")
    A("")
    A("## 1. Path keywords over the 955")
    A("")
    A("| word | paths |")
    A("|---|---:|")
    for w, v in doc["path_hits"].items():
        A(f"| `{w}` | {v['n']} |")
    A("")
    for w, v in doc["path_hits"].items():
        if v["n"] and w in ("haze", "steam", "heat", "distort", "refract"):
            A(f"* `{w}`: " + ", ".join(f"`{p}`" for p in v["paths"]))
    A("")
    A("## 2. Strings inside the files")
    A("")
    A(f"**{doc['string_values']}** non-empty string values across all "
      f"{doc['files_decoded']} files. A `.effc` is ADF v4 and a texture or shader name")
    A("would be a `String` (`0x8955583E`) value; there are none, so no effect file can")
    A("name a texture or a shader. Material identity is the hash table below.")
    A("")
    A("## 3. Texture pool (`.trim` names)")
    A("")
    A("`.trim` files are named `<texture>.<grid>.trim`, so the pool is the only place")
    A("JC3 names a texture. Words with hits:")
    A("")
    A("| word | distinct names | names |")
    A("|---|---:|---|")
    for w, hits in doc["trim_distortion"].items():
        names = sorted({h.rsplit("/", 1)[-1] for h in hits})
        A(f"| `{w}` | {len(names)} | " + ", ".join(f"`{n}`" for n in names) + " |")
    A("")
    A("## 4. Render-block hashes")
    A("")
    A("| hash | effects using it |")
    A("|---|---:|")
    for h, n in sorted(doc["block_hashes"].items(), key=lambda kv: -kv[1]):
        A(f"| `{h}` | {n} |")
    A("")
    A("## 5. Candidate emitter settings")
    A("")
    A("| effect | bytes | containers | inst | emit | tmpl | MaxParticles | template Flags | emitter Flags | blocks (batches) | Properties |")
    A("|---|---:|---:|---:|---:|---:|---|---|---|---|---|")
    for c in doc["candidates"]:
        if c.get("missing"):
            A(f"| `{c['path'].rsplit('/', 1)[-1]}` | - | {c.get('containers', 0)} | - | - | - | - | - | - | not decoded | - |")
            continue
        A(f"| `{c['path'].rsplit('/', 1)[-1]}` | {c['size']} | {c['containers']} | "
          f"{c['instantiators']} | {c['emitters']} | {c['templates']} | "
          f"{c['max_particles']} | {c['template_flags']} | {c['emitter_flags']} | "
          f"{c['blocks']} | {c['properties']} |")
    A("")
    A("## 6. BmAK side")
    A("")
    A(f"`heat-steam` feature group: `{json.dumps(doc['bmak_heat_steam'])[:200]}`")
    A("")
    A("Systems carrying a distortion/steam material:")
    A("")
    A("| system | group | emitters | lifetime | materials |")
    A("|---|---|---:|---|---|")
    for s in doc["bmak_distortion_systems"]:
        A(f"| `{s['name']}` | {s['group']} | {s['emitters']} | {s['lifetime']} | "
          f"{', '.join(f'`{m}`' for m in s['materials'])} |")
    A("")
    A("`afterburner-exhaust` group:")
    A("")
    A("| system | emitters | kinds | lifetime | materials |")
    A("|---|---:|---|---|---|")
    for s in doc["bmak_afterburner_systems"]:
        A(f"| `{s['name']}` | {s['emitters']} | {s['kinds']} | {s['lifetime']} | "
          f"{', '.join(f'`{m}`' for m in s['materials'] or [])} |")
    A("")
    return "\n".join(L)


def cmd_write(_a) -> int:
    doc = scan()
    with open(JS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    md = write_md(doc)
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
        if not md.endswith("\n"):
            f.write("\n")
    print(f"wrote {MD}")
    print(f"wrote {JS}")
    print(f"effc {doc['effc_paths']} strings {doc['string_values']} "
          f"blocks {len(doc['block_hashes'])} trims {doc['trim_names']} digest {doc['digest']}")
    return 0


def cmd_check(_a) -> int:
    if not os.path.exists(JS):
        raise SystemExit("no FX9_HAZE.json - run --write first")
    old = json.load(open(JS, encoding="utf-8"))
    new = scan()
    gates = [
        ("effc_paths", new["effc_paths"] == old["effc_paths"]),
        ("files_decoded", new["files_decoded"] == old["files_decoded"]),
        ("string_values_zero", new["string_values"] == 0),
        ("string_values_same", new["string_values"] == old["string_values"]),
        ("block_hashes_same", new["block_hashes"] == old["block_hashes"]),
        ("type_hashes_same", new["type_hashes"] == old["type_hashes"]),
        ("trim_names_same", new["trim_names"] == old["trim_names"]),
        ("trim_distortion_same", new["trim_distortion"] == old["trim_distortion"]),
        ("candidates_same", new["candidates"] == old["candidates"]),
        ("bmak_same", new["bmak_distortion_systems"] == old["bmak_distortion_systems"]),
        ("digest_same", new["digest"] == old["digest"]),
        ("md_matches", write_md(new).rstrip("\n") ==
         open(MD, encoding="utf-8").read().rstrip("\n")),
    ]
    bad = 0
    for name, ok in gates:
        print(f"  {name:22s} {'PASS' if ok else 'FAIL'}")
        bad += 0 if ok else 1
    print(f"gates {len(gates) - bad}/{len(gates)} pass")
    return 1 if bad else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="regenerate FX9_HAZE.md/.json")
    w.add_argument("--write", action="store_true", help=argparse.SUPPRESS)
    w.set_defaults(func=cmd_write)
    c = sub.add_parser("check", help="re-scan and compare every number")
    c.add_argument("--check", action="store_true", help=argparse.SUPPRESS)
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()
