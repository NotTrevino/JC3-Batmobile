"""jc3weapons.py - every vehicle weapon tune in the game, decoded (G2-10).

The fleet's 25 weapon ids are three kinds of ADF v4 tune, all readable with `jc3adf.py`:

  * `WeaponTuning`      - the weapon itself: fire rate, burst, magazine, damage, recoil,
                          scatter, projectile speed/gravity/lifetime, per-shot impulse,
                          missile homing, AI target priorities, UI reticle numbers
  * `AutoAim`           - the sticky-aim / lock-on block (angle thresholds, stick strengths,
                          distance window, target-class switches)
  * `ForcePulseSettings`- the blast: player and AI damage with radius and falloff

Where they live is the card's first surprise.  **No `jc_explosions/` tree exists in the archives**:
every weapon blast is a `.ftunec` *inside* an `.ee` bundle, and only two `.ftunec` files exist as
standalone archive entries (a test explosion and a barrel).  Likewise 8 of the 22 archive ids
(`w601`-`w607`, `w614`) ship **no bundle of their own** - they are loose patch `.wtunec` overrides
whose base copy sits inside the carrier vehicle's `.ee`:

    patch  editor/entities/jc_weapons/06_vehicle/w601_helicopter_missile/w601_helicopter_missile.wtunec
    base   inside v2200_helicopter_capstone_assault_*.ee -> same inner path

and the 3 `+_impact` ids are not weapons at all: they are the `SettingsFile` of a `CForcePulse`
object (`w604_helicopter_mgun_impact.ftune` on the `v2601`/`v2602` helicopters), i.e. the impact
blast a bullet weapon carries.

Attribution is structural, not guessed:

  * a tune file inside `jc_weapons/06_vehicle/<id>/` belongs to that id (its own directory),
  * a tune file inside any `.ee` belongs to the id its basename names, and to no other id
    (tokens must chain by prefix, so `w606_heavyheli_missile` is `w606_heavyhelicopter_missile`
    but `w613_bombs` is not `w613_fighterbomber_missile_ground_lockon`),
  * a tune file in a bundle that names no id is a **shared** tune (`autoaim_vehicle_*`): it is
    decoded once in the shared table with the containers that embed it.  Binding a shared tune to
    one weapon is wiring, and that is G2-11.

`--write` decodes every tune, extracts the containers and their tune files to
`E:\\Modding\\_shared\\gamedata\\JC3grab\\weapons\\<id>\\` (R10: game bytes stay outside the repo) and writes
`Research/JC3Grab/WEAPONS.jsonl` + `WEAPONS.md`.  `--check` re-reads the archives, re-derives both
files and compares them byte-for-byte, and re-hashes every extracted copy.

Usage:
  python Tools/scripts/jc3weapons.py --write
  python Tools/scripts/jc3weapons.py --check
  python Tools/scripts/jc3weapons.py dump <id or substring> [--max N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import DEFAULT_GAME, MOUNT_RANK  # noqa: E402
import eetoc  # noqa: E402
import jc3adf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
INDEX = os.path.join(OUT, "INDEX.jsonl")
CENSUS = os.path.join(OUT, "FEATURE_CENSUS.json")
TABLE = os.path.join(OUT, "WEAPONS.jsonl")
DOC = os.path.join(OUT, "WEAPONS.md")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
WROOT = os.path.join(RAW, "weapons")
WEP_DIR = "editor/entities/jc_weapons/06_vehicle/"
TUNE_EXT = (".wtunec", ".ftunec")
HEAT_RE = re.compile(r"heat|cool\b|cooldown|temperature", re.I)
IDX_RE = re.compile(r"\[\d+\]")


# ------------------------------------------------------------------- game side
def load_rows() -> list[dict]:
    with open(INDEX, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def best_by_path(rows: list[dict]) -> dict[str, dict]:
    """One winning copy per path: patch > dlc > base."""
    best: dict[str, dict] = {}
    for r in rows:
        cur = best.get(r["path"])
        if cur is None or MOUNT_RANK[r["mount"]] > MOUNT_RANK[cur["mount"]]:
            best[r["path"]] = r
    return best


def read_row(r: dict, game: str) -> bytes:
    arc = os.path.join(game, r["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(r["offset"])
        blob = f.read(r["size"])
    if len(blob) != r["size"]:
        raise IOError(f"short read {len(blob)} != {r['size']} for {r['path']}")
    return blob


def unpack(blob: bytes) -> tuple[bytes, list[tuple[str, int, int]]]:
    stream = eetoc.unaaf(blob)
    return stream, eetoc.sarc_dir(stream)


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


# ----------------------------------------------------------------- decode side
def decode_tune(blob: bytes) -> dict:
    """All instances of one `.wtunec`/`.ftunec`, each as [path, type, value] rows."""
    adf = jc3adf.Adf(blob)
    instances = []
    for i, inst in enumerate(adf.instances):
        rows = [[p, t, v] for p, t, v in jc3adf.walk(adf, i)]
        instances.append({"name": inst["name"], "class": adf.type_name(inst["type"]),
                          "size": inst["size"], "rows": rows})
    digest = sha1("\n".join(f"{p}\t{t}\t{v}" for inst in instances
                            for p, t, v in inst["rows"]).encode("latin-1", "replace"))
    return {"instances": instances, "digest": digest,
            "classes": [i["class"] for i in instances]}


def tokens(name: str) -> list[str]:
    return name.split("_")


def same_id(base: str, wid: str) -> bool:
    """True when a tune basename names this weapon id.

    Tokens must chain by prefix (`w606_heavyheli_missile` -> `w606_heavyhelicopter_missile`,
    `w604_helicopter_mgun_impact` -> `w604_helicopter_mgun`), and the `wNNN` token must be
    equal, so two weapons never collide.
    """
    a, b = tokens(base), tokens(wid)
    if not a or not b or a[0] != b[0]:
        return False
    if len(a) > len(b):
        a, b = b, a
    return all(b[i].startswith(a[i]) for i in range(len(a)))


PREFIXES = ("autoaim_", "default_", "attach_", "static_")


def resolve_id(base: str, ids: list[str], spell_map: dict[str, str],
               aliases: dict[str, str]) -> list[str]:
    """Which id a tune basename names.

    Order: the census's own spelling map and alias table, then the same with a wrapper prefix
    stripped (`autoaim_w613_bombs` -> `w613_bombs`), then the token chain, then - only if one id
    shares the `wNNN` token - that id.  Exact spelling wins over the chain, so a bundle's base
    tune is not also credited to a more general id (`w604_helicopter_mgun_impact.ftunec` is the
    impact blast, not one more copy of `w604_helicopter_mgun`'s weapon).
    """
    cands = [base] + [base[len(p):] for p in PREFIXES if base.startswith(p)]
    for c in cands:
        if c in aliases:
            return [aliases[c]]
        if c in spell_map:
            return [spell_map[c]]
    core = cands[-1]
    hits = [i for i in ids if same_id(core, i)]
    if len(hits) == 1:
        return hits
    if len(hits) > 1:
        ta = tokens(core)

        def chain(wid: str) -> int:
            tb = tokens(wid)
            n = 0
            while n < min(len(ta), len(tb)) and (tb[n].startswith(ta[n]) or ta[n].startswith(tb[n])):
                n += 1
            return n

        return [max(hits, key=lambda i: (chain(i), -abs(len(tokens(i)) - len(ta))))]
    same_num = [i for i in ids if tokens(i)[0] == tokens(core)[0]]
    return same_num if len(same_num) == 1 else []


def tune_files(stream: bytes, entries: list[tuple[str, int, int]]) -> list[tuple[str, bytes]]:
    out = []
    for name, off, size in sorted(entries):
        if os.path.splitext(name)[1].lower() in TUNE_EXT and size:
            out.append((name, stream[off:off + size]))
    return out


# ---------------------------------------------------------------- collect side
def collect(game: str) -> tuple[list[dict], list[dict], dict]:
    """Decode everything. Returns (weapon rows in census order, shared-tune rows, stats)."""
    rows = load_rows()
    best = best_by_path(rows)
    with open(CENSUS, encoding="utf-8") as f:
        census = json.load(f)
    ids = [e["id"] for e in census["weapon_ids"]["ids"]]
    ent_count = {e["id"]: e["entities"] for e in census["weapon_ids"]["ids"]}
    aliases = census["weapon_ids"]["aliases"]
    spell_map = {s: e["id"] for e in census["weapon_ids"]["ids"] for s in e["spellings"]}
    carriers = [e["entity"] for e in census["armed_entities"]]

    # id -> source records; a source is one physical file (archive entry or inner file)
    sources: dict[str, list[dict]] = {i: [] for i in ids}
    shared: dict[str, dict] = {}
    embedded: dict[str, set[str]] = {}          # container -> shared tune basenames it embeds
    tune_count = 0

    def add_source(wid: str, path: str, container: str, mount: str, data: bytes,
                   origin: str) -> None:
        nonlocal tune_count
        inst = decode_tune(data)["instances"]
        rec = {
            "_inst": inst,                        # dropped for non-authoritative copies
            "path": path,
            "container": container,                 # "" = standalone archive entry
            "mount": mount,
            "size": len(data),
            "sha1": sha1(data),
            "origin": origin,                       # patch | bundle | bundle-base
            "classes": sorted({i["class"] for i in inst}),
            "instances": [{"name": i["name"], "class": i["class"], "rows": len(i["rows"])}
                          for i in inst],
            "rows": sum(len(i["rows"]) for i in inst),
            "digest": sha1("\n".join(f"{p}\t{t}\t{v}" for i in inst
                                     for p, t, v in i["rows"]).encode("latin-1", "replace")),
        }
        sources[wid].append(rec)
        tune_count += 1

    # 1. the id's own directory: every archive file in it belongs to the id
    dir_files: dict[str, list[dict]] = {i: [] for i in ids}
    for r in rows:
        if not r["path"].startswith(WEP_DIR):
            continue
        rest = r["path"][len(WEP_DIR):]
        if "/" not in rest:
            continue
        wid, fname = rest.split("/", 1)
        if wid not in dir_files:
            continue
        dir_files[wid].append(r)
        if os.path.splitext(fname)[1].lower() in TUNE_EXT:
            add_source(wid, r["path"], "", r["mount"], read_row(best[r["path"]], game),
                       "patch")

    # 2. every container: the id's own `.ee` and every armed vehicle `.ee`
    containers = sorted({WEP_DIR + i + "/" + i + ".ee" for i in ids if WEP_DIR + i + "/" + i + ".ee" in best}
                        | {c for c in carriers if c in best})
    for path in containers:
        stream, entries = unpack(read_row(best[path], game))
        mount = best[path]["mount"]
        for name, data in tune_files(stream, entries):
            base = os.path.splitext(os.path.basename(name))[0]
            hit = resolve_id(base, ids, spell_map, aliases)
            if hit:
                for wid in hit:
                    origin = "bundle" if path == WEP_DIR + wid + "/" + wid + ".ee" else "bundle-base"
                    add_source(wid, name, path, mount, data, origin)
            else:
                rec = shared.setdefault(base, {"name": name, "sources": [],
                                               "containers": []})
                rec["containers"].append(path)
                embedded.setdefault(path, set()).add(base)
                add_shared(rec, name, path, mount, data)
                tune_count += 1

    # 3. standalone copies: every 00_shared tune, so a preset no bundle embeds still shows up
    for r in rows:
        if not r["path"].endswith(TUNE_EXT) or WEP_DIR in r["path"]:
            continue
        if "/jc_weapons/00_shared/" not in r["path"]:
            continue
        base = os.path.splitext(os.path.basename(r["path"]))[0]
        rec = shared.setdefault(base, {"name": r["path"], "sources": [], "containers": []})
        rec["standalone"] = {"path": r["path"], "mount": r["mount"]}
        rec["sources"] = [{"path": r["path"], "mount": r["mount"], "container": "",
                           "size": r["size"],
                           "sha1": sha1(read_row(best[r["path"]], game))}]
        if "decode" not in rec:
            rec["decode"] = decode_tune(read_row(best[r["path"]], game))
            tune_count += 1

    # 4. authoritative copy per (id, class): patch beats bundle; standalone patch tune wins
    for wid in ids:
        by_class: dict[str, list[dict]] = {}
        for s in sources[wid]:
            for cls in s["classes"]:
                by_class.setdefault(cls, []).append(s)
        for cls, cand in by_class.items():
            rank = {"patch": 0, "bundle": 1, "bundle-base": 2}
            win = sorted(cand, key=lambda s: (rank[s["origin"]], MOUNT_RANK[s["mount"]]))[0]
            win.setdefault("authoritative", []).append(cls)

    # 5. keep the decoded members of the authoritative copy; base copies keep digest + count
    for wid in ids:
        for s in sources[wid]:
            inst = s.pop("_inst")
            if s.get("authoritative"):
                s["decode"] = {"instances": inst}

    # 6. rows
    weapon_rows = []
    for wid in ids:
        src = sources[wid]
        weapon_rows.append({
            "id": wid,
            "archive": bool(dir_files[wid]),
            "spellings": [e["spellings"] for e in census["weapon_ids"]["ids"] if e["id"] == wid][0],
            "entities": ent_count[wid],
            "carriers": [c for c in carriers if any(
                s["container"] == c for s in src)],
            "dir_files": [{"path": r["path"], "mount": r["mount"], "size": r["size"]}
                          for r in sorted(dir_files[wid], key=lambda r: r["path"])],
            "sources": src,
            # shared tunes the id's own bundle embeds (a bundle carries its weapon's presets;
            # which preset a component binds is wiring, so G2-11 owns it)
            "presets": sorted(embedded.get(WEP_DIR + wid + "/" + wid + ".ee", set())),
            "tunes": [{"class": cls, "path": s["path"], "container": s["container"],
                       "mount": s["mount"], "instances": s["decode"]["instances"]}
                      for s in src if s.get("authoritative")
                      for cls in s["authoritative"]],
        })
    for rec in weapon_rows:
        rec["kind"] = kind_of(rec)
        rec["summary"] = summarize(rec)

    shared_rows = []
    for base, rec in sorted(shared.items()):
        shared_rows.append({
            "name": base,
            "path": (rec.get("decode") and rec.get("standalone", {}).get("path")) or None,
            "mount": rec.get("standalone", {}).get("mount"),
            "containers": sorted(set(rec["containers"])),
            "sources": rec.get("sources", []),
            "tunes": [{"class": cls, "instances": [i for i in rec["decode"]["instances"]
                                                    if i["class"] == cls]}
                      for cls in (sorted({i["class"] for i in rec["decode"]["instances"]})
                                  if "decode" in rec else [])],
        })
    stats = {"ids": len(ids), "archive_ids": sum(1 for r in weapon_rows if r["archive"]),
             "tune_files": tune_count, "containers": len(containers),
             "weapon_bundles": sum(1 for c in containers if c.startswith(WEP_DIR)),
             "carrier_bundles": sum(1 for c in containers if not c.startswith(WEP_DIR)),
             "shared": len(shared_rows), "aliases": aliases,
             "tune_kinds": sorted({c for r in weapon_rows for t in r["tunes"]
                                   for c in [t["class"]]})}
    return weapon_rows, shared_rows, stats


def add_shared(rec: dict, name: str, container: str, mount: str, data: bytes) -> None:
    """Record one embedded copy of a shared tune (decoded in place if it is the first)."""
    rec["sources"].append({"path": name, "container": container, "mount": mount,
                           "size": len(data), "sha1": sha1(data)})
    if "decode" not in rec:
        rec["decode"] = decode_tune(data)


# -------------------------------------------------------------- derived values
def flat(inst: dict) -> dict:
    return {p: v for p, t, v in inst["rows"]}


def blocks(inst: dict) -> dict[str, str]:
    """The tuning block prefixes present in a WeaponTuning instance, e.g. {'bullet': 'bullet_weapon[0].tuning.'}."""
    out = {}
    for kind in ("missile", "grenade", "bullet", "fow"):
        nums = sorted({int(m.group(1)) for p, _t, _v in inst["rows"]
                       for m in [re.match(rf"{kind}_weapon\[(\d+)\]", p)] if m})
        if nums:
            out[kind] = [f"{kind}_weapon[{n}].tuning." for n in nums]
    return out


def kind_of(rec: dict) -> str:
    wt = next((t for t in rec["tunes"] if t["class"] == "WeaponTuning"), None)
    if not wt:
        return "impact" if any(t["class"] == "ForcePulseSettings" for t in rec["tunes"]) else "none"
    kinds = []
    for inst in wt["instances"]:
        kinds += list(blocks(inst))
    return "+".join(sorted(set(kinds))) or "empty"


def summarize(rec: dict) -> dict:
    """The scalars the tables quote, straight from the authoritative instances."""
    out: dict = {}
    wt = next((t for t in rec["tunes"] if t["class"] == "WeaponTuning"), None)
    if wt:
        inst = wt["instances"][0]
        f = flat(inst)
        out["weapon_instances"] = len(wt["instances"])
        out["weapon_rows"] = len(inst["rows"])
        for k in ("magazine_size", "max_range", "reload_time_scale", "velocity", "fire_rate",
                  "burst_count", "burst_cooldown", "fully_automatic", "aim_timer_override",
                  "unlimited_ammo"):
            out[k] = f.get(k)
        out["trigger_sensitivity"] = [f.get(f"trigger_sensitivity[{i}]") for i in (0, 1)]
        out["ui"] = {k: f.get(f"UISettings.{k}") for k in
                     ("scatter_at_smallest", "scatter_at_biggest", "reticle_size_smallest",
                      "reticle_size_biggest", "reticle_offset_in_fov_fraction")}
        bl = blocks(inst)
        out["blocks"] = {k: len(v) for k, v in bl.items()}
        for kind, prefixes in bl.items():
            for n, pre in enumerate(prefixes):
                tag = kind if len(prefixes) == 1 else f"{kind}[{n}]"
                # the AI tuning is a sibling of the player one: `<block>[i].tuning` and
                # `<block>[i].ai_tuning`, not `tuning.ai_tuning`
                struct_pre = pre[: -len("tuning.")]
                for side, side_pre in (("player", pre), ("ai", struct_pre + "ai_tuning.")):
                    base = side_pre + "base_tuning."
                    out[f"{tag}.{side}.damage"] = f.get(base + "damage")
                    out[f"{tag}.{side}.impulse"] = f.get(base + "impulse")
                    out[f"{tag}.{side}.vehicle_damage_factor"] = f.get(base + "vehicle_damage_factor")
                    out[f"{tag}.{side}.object_damage_factor"] = f.get(base + "object_damage_factor")
                    out[f"{tag}.{side}.vehicle_impulse_factor"] = f.get(base + "vehicle_impulse_factor")
                    out[f"{tag}.{side}.object_impulse_factor"] = f.get(base + "object_impulse_factor")
                    out[f"{tag}.{side}.recoil_pitch"] = [f.get(base + f"recoil.recoil_pitch[{i}]") for i in (0, 1)]
                    out[f"{tag}.{side}.recoil_yaw"] = [f.get(base + f"recoil.recoil_yaw[{i}]") for i in (0, 1)]
                    out[f"{tag}.{side}.scatter"] = {
                        k: f.get(base + "scatter." + k) for k in
                        ("scatter_minimum", "scatter_maximum", "scatter_per_shot",
                         "scatter_recover_rate", "scatter_reset_time")}
                base = pre + "missile_base_tuning."
                out[f"{tag}.missile.turning_speed"] = f.get(base + "missile_turning_speed")
                out[f"{tag}.missile.acceleration"] = [f.get(base + f"missile_acceleration[{i}]") for i in (0, 1)]
                out[f"{tag}.missile.acceleration_time"] = [f.get(base + f"missile_acceleration_time[{i}]") for i in (0, 1)]
                out[f"{tag}.missile.no_turning_time"] = f.get(base + "missile_no_turning_time")
                out[f"{tag}.missile.detonation_time"] = f.get(base + "missile_detonation_time")
                out[f"{tag}.missile.loose_lock_distance"] = f.get(base + "missile_loose_lock_distance")
                out[f"{tag}.missile.per_shot"] = f.get(base + "missile_per_shot")
                out[f"{tag}.missile.detonate_on_impact"] = f.get(base + "detonate_on_impact")
                out[f"{tag}.missile.gravity"] = f.get(base + "gravity")
                base = pre + "bullet_base_tuning."
                for k in ("tracer_fire_velocity", "tracer_fire_length", "tracer_time_to_live",
                          "ricochet_chance", "ricochet_count", "bullets_per_shot",
                          "bullets_per_tracer", "gravity_on", "gravity_strength",
                          "headshot_multiplier", "bullet_is_explosive", "smoke_trail_tile_size",
                          "tracer_texture_type"):
                    out[f"{tag}.bullet.{k}"] = f.get(base + k)
                out[f"{tag}.ai.target_priorities"] = {
                    k: f.get(struct_pre + "ai_tuning.ai_base_tuning." + k) for k in
                    ("character_target_priority", "land_vehicle_target_priority",
                     "sea_vehicle_target_priority", "air_vehicle_target_priority",
                     "tank_target_priority", "machine_gun_priority")}
                out[f"{tag}.ai.optimal_range"] = f.get(struct_pre + "ai_tuning.ai_base_tuning.optimal_range")
                out[f"{tag}.ai.range"] = [f.get(struct_pre + f"ai_tuning.ai_base_tuning.range[{i}]") for i in (0, 1)]
                out[f"{tag}.ai.threat_value"] = f.get(struct_pre + "ai_tuning.ai_base_tuning.threat_value")
    aa = next((t for t in rec["tunes"] if t["class"] == "AutoAim"), None)
    if aa:
        f = flat(aa["instances"][0])
        out["autoaim"] = f
    fp = next((t for t in rec["tunes"] if t["class"] == "ForcePulseSettings"), None)
    if fp:
        out["blast"] = flat(fp["instances"][0])
    return out


# --------------------------------------------------------------------- writing
def extract(rows: list[dict], game: str) -> list[dict]:
    """Write every weapon `.ee`, its tune files and the loose patch tunes to WROOT."""
    best = best_by_path(load_rows())
    written = []
    for rec in rows:
        dest = os.path.join(WROOT, rec["id"])
        for r in rec["dir_files"]:
            data = read_row(best[r["path"]], game)
            target = os.path.join(dest, os.path.basename(r["path"]))
            written.append(write_bytes(target, data, r["path"], r["mount"]))
        for s in rec["sources"]:
            if s["origin"] == "patch":
                continue                    # already written from dir_files
            data = container_file(s, best, game)
            tag = os.path.splitext(os.path.basename(s["container"]))[0] if s["container"] else "standalone"
            target = os.path.join(dest, f"{tag}__{os.path.basename(s['path'])}")
            written.append(write_bytes(target, data, s["path"], s["mount"]))
    return written


def container_file(s: dict, best: dict, game: str) -> bytes:
    if not s["container"]:
        return read_row(best[s["path"]], game)
    stream, entries = unpack(read_row(best[s["container"]], game))
    for name, off, size in entries:
        if name == s["path"]:
            return stream[off:off + size]
    raise SystemExit(f"{s['path']} not inside {s['container']}")


def write_bytes(path: str, data: bytes, src: str, mount: str) -> dict:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and open(path, "rb").read() == data:
        pass
    else:
        with open(path, "wb") as f:
            f.write(data)
    return {"path": path.replace("\\", "/"), "source": src, "mount": mount,
            "size": len(data), "sha1": sha1(data)}


def read_doc(rows: list[dict], shared: list[dict], stats: dict,
             extraction: list[dict]) -> list[str]:
    """Generate WEAPONS.md (the card's Out) - all counts come from the decode."""
    ids = [r["id"] for r in rows]
    no_heat = sorted({p for r in rows for t in r["tunes"] for i in t["instances"]
                      for p, _ty, _v in i["rows"] if HEAT_RE.search(p)} |
                     {p for r in shared for t in r["tunes"] for i in t["instances"]
                      for p, _ty, _v in i["rows"] if HEAT_RE.search(p)})
    L: list[str] = []
    a = L.append
    a("# JC3 vehicle weapon catalogue (G2-10)")
    a("")
    a("Generated by `Tools/scripts/jc3weapons.py` from the archives; `--check` re-reads them and")
    a("compares. One row per weapon id in `WEAPONS.jsonl`, with every decoded member of every")
    a("authoritative tune; this file is the reading of those rows.")
    a("")
    a("Three ADF v4 tune classes carry the fleet's weapons:")
    a("")
    a("| class | what it is | instances decoded |")
    a("|---|---|---|")
    tune_class_count = {c: sum(1 for r in rows for t in r["tunes"] if t["class"] == c)
                        for c in stats["tune_kinds"]}
    a(f"| `WeaponTuning` | the weapon: fire rate, burst, magazine, damage, recoil, scatter, "
      f"projectile, homing, AI priorities, reticle | {tune_class_count.get('WeaponTuning', 0)} ids |")
    a(f"| `AutoAim` | sticky-aim / lock-on block | {tune_class_count.get('AutoAim', 0)} ids "
      f"+ {sum(1 for s in shared if any(t['class'] == 'AutoAim' for t in s['tunes']))} shared tunes |")
    a(f"| `ForcePulseSettings` | the blast: player/AI damage, radius, falloff | "
      f"{tune_class_count.get('ForcePulseSettings', 0)} ids |")
    a("")
    a("## 1. Where the tunes live")
    a("")
    a(f"`INDEX.jsonl` has **{stats['index_rows'] if 'index_rows' in stats else len(load_rows()):,}** rows; "
      f"**{sum(len(r['dir_files']) for r in rows)}** of them sit under `{WEP_DIR}` "
      f"({stats['archive_ids']} of the {stats['ids']} ids have their own directory, "
      f"{sum(1 for r in rows for f in r['dir_files'] if f['path'].endswith('.ee'))} of those carry an `.ee`). "
      f"The other ids ship as loose patch `.wtunec` overrides and their base copy lives inside the "
      f"carrier `.ee`. {stats['containers']} `.ee` bundles were opened "
      f"({stats['weapon_bundles']} weapon bundles + {stats['carrier_bundles']} armed vehicles).")
    a("")
    a("Two things the card expected that are not there, recorded so nobody re-litigates them:")
    a("")
    a("* **No `editor/entities/jc_explosions/` tree.** The weapon blasts are `.ftunec` files inside")
    a("  `.ee` bundles; the whole game has exactly two standalone `.ftunec` archive entries, neither")
    a("  a weapon (`gen_explosion_0.5m_nodamage`, `structures/barrel_explosion`).")
    a("* **The 3 `+_impact` ids are blast tunes, not weapons.** Each is the `SettingsFile` of a")
    a("  `CForcePulse` object on the vehicles that fire the matching gun "
      "(`w604_helicopter_mgun_impact` on 3 `v2601` + 9 `v2602`/`v2604` helicopters per the census).")
    a("")
    a("| weapon id | archive dir | kind | blocks | entities | authoritative sources | preset in its own bundle |")
    a("|---|---|---|---|---:|---|---|")
    for r in rows:
        blocks_s = ", ".join(f"`{k}`x{v}" for k, v in r["summary"].get("blocks", {}).items()) or "-"
        srcs = ", ".join(f"{'patch' if s['origin'] == 'patch' else 'bundle'}"
                         f"({', '.join(s['classes'])})" for s in r["sources"]
                         if s.get("authoritative")) or "-"
        a(f"| `{r['id']}` | {'yes' if r['archive'] else 'no'} | {r['kind']} | {blocks_s} | "
          f"{r['entities']} | {srcs} | {', '.join(f'`{s}`' for s in r['presets']) or '-'} |")
    a("")
    a("## 2. Firing, magazine and ammo")
    a("")
    a("| weapon id | block | fire_rate (s) | burst | burst_cd | full-auto | magazine | reload_scale | max_range | velocity | unlimited_ammo | aim_timer_override |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        if "fire_rate" not in s:
            continue
        a(f"| `{r['id']}` | {r['kind']} | {num(s['fire_rate'])} | {num(s['burst_count'])} | "
          f"{num(s['burst_cooldown'])} | {num(s['fully_automatic'])} | {num(s['magazine_size'])} | "
          f"{num(s['reload_time_scale'])} | {num(s['max_range'])} | {num(s['velocity'])} | "
          f"{num(s['unlimited_ammo'])} | {num(s['aim_timer_override'])} |")
    a("")
    a("`fire_rate` is the seconds between shots (0.1 on the buggy MG is 10 shots/s), `magazine_size` "
      "-1 means no magazine, `unlimited_ammo` 1 means the weapon never runs dry, and `reload_time_scale` "
      "0 means no reload step is scaled in.")
    a("")
    a("## 3. Damage, impulse and the scaled sides")
    a("")
    a("| weapon id | block | player dmg | player veh x | player obj x | player impulse | AI dmg | AI veh x | AI obj x | AI impulse |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        for tag in sorted({k.split(".")[0] for k in s if ".player.damage" in k}):
            a(f"| `{r['id']}` | {tag} | {num(s.get(f'{tag}.player.damage'))} | "
              f"{num(s.get(f'{tag}.player.vehicle_damage_factor'))} | "
              f"{num(s.get(f'{tag}.player.object_damage_factor'))} | "
              f"{num(s.get(f'{tag}.player.impulse'))} | {num(s.get(f'{tag}.ai.damage'))} | "
              f"{num(s.get(f'{tag}.ai.vehicle_damage_factor'))} | "
              f"{num(s.get(f'{tag}.ai.object_damage_factor'))} | {num(s.get(f'{tag}.ai.impulse'))} |")
    a("")
    a("Every weapon carries two tunings: `<block>[i].tuning` (player) and its sibling `ai_tuning`, each")
    a("with `base_tuning.damage` / `.impulse` and the two scaling factors - a vehicle hit multiplies")
    a("by `vehicle_damage_factor`, an object hit by `object_damage_factor`. The two sides differ:")
    a("the AI side is what an NPC-fired copy of the same weapon does.")
    a("")
    a("## 4. Recoil and spread")
    a("")
    a("| weapon id | block | side | recoil_pitch | recoil_yaw | scatter min/max/per-shot | scatter recover/reset |")
    a("|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        for tag in sorted({k.split(".")[0] for k in s if ".player.recoil_pitch" in k}):
            for side in ("player", "ai"):
                sc = s.get(f"{tag}.{side}.scatter", {})
                a(f"| `{r['id']}` | {tag} | {side} | "
                  f"{pair(s.get(f'{tag}.{side}.recoil_pitch'))} | {pair(s.get(f'{tag}.{side}.recoil_yaw'))} | "
                  f"{num(sc.get('scatter_minimum'))}/{num(sc.get('scatter_maximum'))}/"
                  f"{num(sc.get('scatter_per_shot'))} | {num(sc.get('scatter_recover_rate'))}/"
                  f"{num(sc.get('scatter_reset_time'))} |")
    a("")
    a("## 5. Projectile: missiles")
    a("")
    a("| weapon id | block | turning_speed | accel | accel_time | no_turn_time | detonation_time | loose_lock_dist | per_shot | detonate_on_impact | gravity |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        for tag in sorted({k.split(".")[0] for k in s if ".missile.turning_speed" in k}):
            a(f"| `{r['id']}` | {tag} | {num(s.get(f'{tag}.missile.turning_speed'))} | "
              f"{pair(s.get(f'{tag}.missile.acceleration'))} | {pair(s.get(f'{tag}.missile.acceleration_time'))} | "
              f"{num(s.get(f'{tag}.missile.no_turning_time'))} | {num(s.get(f'{tag}.missile.detonation_time'))} | "
              f"{num(s.get(f'{tag}.missile.loose_lock_distance'))} | {num(s.get(f'{tag}.missile.per_shot'))} | "
              f"{num(s.get(f'{tag}.missile.detonate_on_impact'))} | {num(s.get(f'{tag}.missile.gravity'))} |")
    a("")
    a("`missile_turning_speed` 0 with `missile_acceleration` 0 is a straight-flying rocket; both "
      "arrays are an acceleration ramp ([value at t0, value at t1] with `missile_acceleration_time`).")
    a("")
    a("## 6. Projectile: bullets and tracers")
    a("")
    a("| weapon id | block | tracer_velocity | tracer_length | ttl | ricochet_chance | ricochet_count | bullets_per_shot | gravity_on | gravity_strength | headshot x | explosive |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        for tag in sorted({k.split(".")[0] for k in s if ".bullet.tracer_fire_velocity" in k}):
            a(f"| `{r['id']}` | {tag} | {num(s.get(f'{tag}.bullet.tracer_fire_velocity'))} | "
              f"{num(s.get(f'{tag}.bullet.tracer_fire_length'))} | {num(s.get(f'{tag}.bullet.tracer_time_to_live'))} | "
              f"{num(s.get(f'{tag}.bullet.ricochet_chance'))} | {num(s.get(f'{tag}.bullet.ricochet_count'))} | "
              f"{num(s.get(f'{tag}.bullet.bullets_per_shot'))} | {num(s.get(f'{tag}.bullet.gravity_on'))} | "
              f"{num(s.get(f'{tag}.bullet.gravity_strength'))} | {num(s.get(f'{tag}.bullet.headshot_multiplier'))} | "
              f"{num(s.get(f'{tag}.bullet.bullet_is_explosive'))} |")
    a("")
    a("## 7. AI targeting and reticle")
    a("")
    a("| weapon id | block | optimal_range | range[0..1] | threat | char | land | sea | air | tank | mg |")
    a("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        for tag in sorted({k.split(".")[0] for k in s if ".ai.target_priorities" in k}):
            tp = s[f"{tag}.ai.target_priorities"]
            a(f"| `{r['id']}` | {tag} | {num(s.get(f'{tag}.ai.optimal_range'))} | "
              f"{pair(s.get(f'{tag}.ai.range'))} | {num(s.get(f'{tag}.ai.threat_value'))} | "
              + " | ".join(num(tp.get(k)) for k in
                           ("character_target_priority", "land_vehicle_target_priority",
                            "sea_vehicle_target_priority", "air_vehicle_target_priority",
                            "tank_target_priority", "machine_gun_priority")) + " |")
    a("")
    a("Reticle numbers (`UISettings`) per id:")
    a("")
    a("| weapon id | scatter_at_smallest/biggest | reticle_size_smallest/biggest | reticle_offset_in_fov_fraction | trigger_sensitivity |")
    a("|---|---|---|---|---|")
    for r in rows:
        s = r["summary"]
        if "ui" not in s:
            continue
        ui = s["ui"]
        a(f"| `{r['id']}` | {num(ui.get('scatter_at_smallest'))}/{num(ui.get('scatter_at_biggest'))} | "
          f"{num(ui.get('reticle_size_smallest'))}/{num(ui.get('reticle_size_biggest'))} | "
          f"{num(ui.get('reticle_offset_in_fov_fraction'))} | {pair(s.get('trigger_sensitivity'))} |")
    a("")
    a("## 8. Blast (`ForcePulseSettings`)")
    a("")
    a("| weapon id | player damage | AI damage | player radius | AI radius | radius %max | radius min |")
    a("|---|---|---|---|---|---|---|")
    for r in rows:
        b = r["summary"].get("blast")
        if not b:
            continue
        a(f"| `{r['id']}` | {num(b.get('PlayerDamage'))} | {num(b.get('AIDamage'))} | "
          f"{num(b.get('PlayerDamageRadius'))} | {num(b.get('AIDamageRadius'))} | "
          f"{num(b.get('PlayerDamageRadiusPercentageMax'))} | {num(b.get('PlayerDamageRadiusMin'))} |")
    a("")
    a("Ids with **no blast** of their own: " + ", ".join(
        f"`{r['id']}`" for r in rows if "blast" not in r["summary"]) + ".")
    a("")
    a("A bullet weapon carries its blast as a separate id: `w604_helicopter_mgun_impact`,")
    a("`w610_fighterjet_mgun_impact` and `w617_vintagefighter_mgun_impact` are the impact blasts of")
    a("those three guns (their `CForcePulse.SettingsFile`), so the gun id itself has no blast row")
    a("and the blast id has no firing row. That is the census's 25 ids, 26 spellings, exactly.")
    a("")
    a("## 9. Lock-on / sticky aim (`AutoAim`)")
    a("")
    a("An `AutoAim` tune is not one flat block: it carries one sub-block per **shooter context**")
    a("(the state the shooter is in when the trigger goes down), each with the same member set.")
    a("Only three ids ship their own preset; the rest bind a shared one (section 13).")
    a("")
    for r in rows:
        aa_tune = next((t for t in r["tunes"] if t["class"] == "AutoAim"), None)
        aa = r["summary"].get("autoaim")
        if not aa or not aa_tune:
            continue
        members: list[str] = []
        for p, _ty, _v in aa_tune["instances"][0]["rows"]:
            if "." in p and p.split(".", 1)[1] not in members:
                members.append(p.split(".", 1)[1])
        ctxs: list[str] = []
        for p, _ty, _v in aa_tune["instances"][0]["rows"]:
            if "." in p and p.split(".", 1)[0] not in ctxs:
                ctxs.append(p.split(".", 1)[0])
        a(f"### `{r['id']}`")
        a("")
        a(f"Source: `{aa_tune['path']}` ({len(members)} members x {len(ctxs)} contexts).")
        a("")
        a("| member | " + " | ".join(ctxs) + " |")
        a("|---" * (len(ctxs) + 1) + "|")
        for m in members:
            a(f"| `{m}` | " + " | ".join(num(aa.get(f"{c}.{m}")) for c in ctxs) + " |")
        a("")
    aa_shared = [s for s in shared if s["name"].startswith("autoaim_")]
    a(f"**{len(shared)} tunes in the fleet's bundles name no weapon id**, in two groups. "
      f"The {len(aa_shared)} `autoaim_*` files are the sticky-aim / lock-on **presets** a weapon")
    a("component binds (that binding is wiring, so G2-11 owns it); the rest are other weapons and")
    a("explosion tunes a vehicle bundle happens to carry. Their members are printed verbatim in")
    a("section 13.")
    a("")
    a("| shared tune | kind | class | standalone path | embedded in |")
    a("|---|---|---|---|---|")
    for s in shared:
        cls = "/".join(sorted({t["class"] for t in s["tunes"]})) or "?"
        a(f"| `{s['name']}` | {'preset' if s['name'].startswith('autoaim_') else 'other'} | "
          f"`{cls}` | "
          f"{('`' + s['path'] + '`') if s['path'] else '-'} | "
          f"{len(s['containers']) if s['containers'] else 'not embedded'} |")
    a("")
    a("A preset with no container is shipped but unused by an armed vehicle")
    a("(`autoaim_pistol`, `autoaim_rpg`, `autoaim_smg`, ... are the player weapons').")
    a("")
    a("## 10. What the card asked for, and where it is")
    a("")
    a("| card item | member(s) | note |")
    a("|---|---|---|")
    a("| fire rate | `fire_rate` | seconds per shot |")
    a("| burst | `burst_count`, `burst_cooldown`, `fully_automatic` | |")
    a("| damage per hit | `<block>[i].tuning.base_tuning.damage` (player) and `ai_tuning.base_tuning.damage` | plus `vehicle_damage_factor` / `object_damage_factor` |")
    a("| damage type | **not in the tune** | no member of any of the decoded classes matches `damage.?type`; JC3 types damage on the part and the health module (`PARTS_TABLE.jsonl` `dt`, `DAMAGE_MECHANISMS.md`), not on the weapon |")
    a("| projectile speed | `velocity`, `tracer_fire_velocity`, `missile_acceleration[]` | |")
    a("| projectile gravity | `missile_base_tuning.gravity`, `bullet_base_tuning.gravity_on`/`gravity_strength` | |")
    a("| projectile lifetime | `missile_detonation_time`, `tracer_time_to_live` | |")
    a("| spread | `scatter.*` (min/max/per shot/recover/reset/clamps) | |")
    a("| recoil | `recoil.*` (pitch/yaw, first shot, precision, recover) | |")
    a("| ammo / clip / reload | `magazine_size`, `reload_time_scale`, `unlimited_ammo` | -1 = no magazine |")
    a("| overheat (heat per shot, cool rate) | **proven absent** | see below |")
    a("| lock-on range | `MaxAimDistance`, `AlwaysTargetDistance`, `missile_loose_lock_distance` | |")
    a("| lock-on angle | `AngleThresholdNewTarget`, `AngleThresholdCurrentTarget`, `StickyAimStartAngle` | |")
    a("| lock-on time | **no member** | the AutoAim block has no time field; `SnapAimTarget` is the only candidate and its unit is not proven, so it is `UNKNOWN` (Q-1 candidate) |")
    a("| homing | `missile_turning_speed`, `missile_no_turning_time`, `missile_per_shot`, `detonate_on_impact` | turning_speed 0 = no homing |")
    a("| explosion radius and damage | `PlayerDamage`/`PlayerDamageRadius`/`AIDamage`/`AIDamageRadius` (+ `*PercentageMax`, `*Min`) | |")
    a("| impulse | `base_tuning.impulse` + `vehicle_impulse_factor`/`object_impulse_factor` | |")
    a("")
    a("**Overheat is absent, and that is a file answer.** No member of any decoded class names")
    a("heat, cooling or temperature; the single cooldown-shaped member is ")
    a(f"`burst_cooldown`{'' if no_heat else ' (a burst gap, not heat)'}, and no weapon tunes a temperature ")
    a("anywhere. JC3 weapons therefore have no heat model at all: a JC3 Vulcan fires until its")
    a("ammo runs out, and BmAK's `HeatUpPerSecond` / `OverheatOffValue` (grab record) has no JC3")
    a("counterpart to copy - a heat-carrying Batmobile Vulcan is a BmAK-side behaviour, and the")
    a("Vulcan's bloom curve is the JC3-shaped half.")
    if no_heat:
        a("")
        a("Members that matched anyway, for the record: " +
          ", ".join(f"`{p}`" for p in no_heat) + ".")
    a("")
    a("## 11. Extraction and validation")
    a("")
    a(f"`--write` extracted **{len(extraction)} files** ({sum(e['size'] for e in extraction):,} B) to "
      f"`{WROOT.replace(chr(92), '/')}` - the weapon `.ee` bundles, the loose patch tunes and every")
    a("base or bundle copy of a tune, named `<container-stem>__<inner-name>`. Game bytes stay")
    a("outside the repo (R10); this file and `WEAPONS.jsonl` are the summary.")
    a("")
    a("`--check` re-reads every container out of the archives, re-derives this file and")
    a("`WEAPONS.jsonl` and compares both byte-for-byte, then re-hashes every extracted file.")
    a("")
    a("## 12. Member vocabulary (every decoded member path, indices collapsed)")
    a("")
    a("| class | member path | type | ids | min | max |")
    a("|---|---|---|---|---|---|")
    for line in vocab_lines(rows, shared):
        a(line)
    a("")
    a("## 13. Shared tune members (the lock-on presets, verbatim)")
    a("")
    a("One table per `autoaim_*` preset, in the same context layout as section 9 (every preset")
    a("carries the same member set). The presets are printed in full because they are the only")
    a("lock-on numbers in the game; the other shared tunes (explosion and other-weapon tunes a")
    a("bundle happens to carry) are listed by class and member count, decoded in")
    a("`WEAPONS_SHARED.json`.")
    a("")
    for s in shared:
        if not s["tunes"] or not s["name"].startswith("autoaim_"):
            continue
        a(f"### `{s['name']}`")
        a("")
        if s["path"]:
            a(f"Standalone: `{s['path']}` (mount {s['mount']}); embedded in "
              f"{len(s['containers'])} container(s).")
        else:
            a(f"Embedded only, in {len(s['containers'])} container(s).")
        a("")
        inst = s["tunes"][0]["instances"][0]
        members: list[str] = []
        ctxs: list[str] = []
        vals: dict = {}
        for p, _ty, v in inst["rows"]:
            vals[p] = v
            if "." not in p:
                continue
            ctx, mem = p.split(".", 1)
            if ctx not in ctxs:
                ctxs.append(ctx)
            if mem not in members:
                members.append(mem)
        a("| member | " + " | ".join(ctxs) + " |")
        a("|---" * (len(ctxs) + 1) + "|")
        for m in members:
            a(f"| `{m}` | " + " | ".join(num(vals.get(f"{c}.{m}")) for c in ctxs) + " |")
        a("")
    a("| other shared tune | class | members | embedded in |")
    a("|---|---|---|---|")
    for s in shared:
        if not s["tunes"] or s["name"].startswith("autoaim_"):
            continue
        cls = "/".join(sorted({t["class"] for t in s["tunes"]}))
        a(f"| `{s['name']}` | `{cls}` | {len(s['tunes'][0]['instances'][0]['rows'])} | "
          f"{len(s['containers'])} |")
    a("")
    return L


def vocab_lines(rows: list[dict], shared: list[dict]) -> list[str]:
    seen: dict[tuple[str, str], dict] = {}

    def note(cls: str, p: str, ty: str, v, wid: str | None) -> None:
        st = seen.setdefault((cls, IDX_RE.sub("[]", p)),
                             {"ids": set(), "types": set(), "min": None, "max": None})
        st["types"].add(ty)
        if wid:
            st["ids"].add(wid)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            st["min"] = v if st["min"] is None else min(st["min"], v)
            st["max"] = v if st["max"] is None else max(st["max"], v)

    for r in rows:
        for t in r["tunes"]:
            for inst in t["instances"]:
                for p, ty, v in inst["rows"]:
                    note(t["class"], p, ty, v, r["id"])
    for s in shared:
        for t in s["tunes"]:
            for inst in t["instances"]:
                for p, ty, v in inst["rows"]:
                    note(t["class"], p, ty, v, None)
    out = []
    for (cls, path), st in sorted(seen.items()):
        lo = "" if st["min"] is None else f"{st['min']:.6g}"
        hi = "" if st["max"] is None else f"{st['max']:.6g}"
        n = len(st["ids"]) if st["ids"] else "shared"
        out.append(f"| `{cls}` | `{path}` | {'/'.join(sorted(st['types']))} | {n} | {lo} | {hi} |")
    return out


def num(v) -> str:
    if v is None:
        return "?"
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def pair(v) -> str:
    if not isinstance(v, list):
        return num(v)
    return "[" + ", ".join(num(x) for x in v) + "]"


# ------------------------------------------------------------------ commands
def build(game: str, write: bool) -> tuple[list[dict], list[dict], dict, list[dict], list[str]]:
    rows, shared, stats = collect(game)
    stats["index_rows"] = len(load_rows())
    extraction = extract(rows, game) if write else load_extraction()
    lines = read_doc(rows, shared, stats, extraction)
    return rows, shared, stats, extraction, lines


def load_extraction() -> list[dict]:
    p = os.path.join(OUT, TABLE)
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding="utf-8"):
        if line.strip():
            rec = json.loads(line)
            out += rec.get("extracted", [])
    return out


def cmd_write(a) -> int:
    rows, shared, stats, extraction, lines = build(a.game, True)
    for rec in rows:
        rec["extracted"] = [e for e in extraction
                            if os.path.dirname(e["path"]).replace("\\", "/")
                            .endswith("/" + rec["id"])]
    with open(TABLE, "w", encoding="utf-8", newline="\n") as f:
        for rec in rows:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    with open(os.path.join(OUT, "WEAPONS_SHARED.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(shared, f, indent=1, sort_keys=True)
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"WEAPONS.jsonl: {len(rows)} ids, {sum(len(r['sources']) for r in rows)} sources, "
          f"{sum(r['summary'].get('weapon_rows', 0) for r in rows)} weapon rows; "
          f"{len(shared)} shared tunes; {len(extraction)} files extracted")
    ids_no_tune = [r["id"] for r in rows if not r["tunes"]]
    if ids_no_tune:
        print(f"WARNING: no tune for {ids_no_tune}")
    return 0


def cmd_check(a) -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: no {TABLE} - run --write first")
        return 1
    old = [json.loads(line) for line in open(TABLE, encoding="utf-8") if line.strip()]
    rows, shared, stats, extraction, lines = build(a.game, False)
    for rec in rows:
        rec["extracted"] = [e for e in extraction
                            if os.path.dirname(e["path"]).replace("\\", "/")
                            .endswith("/" + rec["id"])]
    bad = 0
    if len(old) != len(rows):
        print(f"FAIL: {len(old)} rows on disk, {len(rows)} re-derived")
        bad += 1
    for o, n in zip(old, rows):
        if o != n:
            print(f"FAIL: {o['id']} changed")
            for k in sorted(set(o) | set(n)):
                if o.get(k) != n.get(k) and k != "extracted":
                    print(f"   field {k}: {str(o.get(k))[:120]} != {str(n.get(k))[:120]}")
            bad += 1
    new_md = "\n".join(lines) + "\n"
    on_disk = open(DOC, encoding="utf-8").read() if os.path.exists(DOC) else ""
    if on_disk != new_md:
        print("FAIL: WEAPONS.md changed")
        import difflib
        for line in list(difflib.unified_diff(on_disk.splitlines(), new_md.splitlines(),
                                              "WEAPONS.md", "re-derived", lineterm=""))[:20]:
            print("   " + line)
        bad += 1
    ext = load_extraction()
    for e in ext:
        if not os.path.exists(e["path"]):
            print(f"FAIL: extracted file missing: {e['path']}")
            bad += 1
            continue
        data = open(e["path"], "rb").read()
        if len(data) != e["size"] or sha1(data) != e["sha1"]:
            print(f"FAIL: extracted file changed: {e['path']}")
            bad += 1
    print(f"{'PASS' if not bad else 'FAIL'}: {len(rows)} ids, {len(ext)} extracted files, "
          f"{len(shared)} shared tunes, md {len(new_md.splitlines())} lines")
    return 1 if bad else 0


def cmd_check_root(a) -> int:
    """`--check --root <build>`: re-read the tunes a build ships, against T-11's edits.

    Build mode touches **no archive**: it walks `<root>/aaf/editor/entities/jc_weapons/**/*.wtunec`,
    decodes each file with the same `decode_tune` the catalogue uses, and compares every edit in
    `Working/Translation/t7_weapons_edits.json` against the copy whose `wNNN` token matches the
    edit's `scope` (`weapon tune clone of \\`w602_mediumtank_canon\\``). One line per edit, printing
    the value read and the value T-11 expects, so a failed write is visible as a number.
    """
    root = a.root if os.path.isabs(a.root) else os.path.join(ROOT, a.root)
    base = os.path.join(root, "aaf", "editor", "entities", "jc_weapons")
    if not os.path.isdir(base):
        print(f"FAIL: no {base} - not a build tree with weapon files")
        return 1
    t7 = os.path.join(ROOT, "Working", "Translation", "t7_weapons_edits.json")
    if not os.path.exists(t7):
        print(f"FAIL: no {t7}")
        return 1
    edits = json.load(open(t7, encoding="utf-8"))["edits"]
    tunes = []
    for dirpath, _dirs, files in os.walk(base):
        for f in sorted(files):
            if f.endswith(TUNE_EXT):
                p = os.path.join(dirpath, f)
                tunes.append({"path": p, "file": f,
                              "rel": os.path.relpath(p, root).replace(os.sep, "/")})
    rows_by_tune = {}
    bad = 0
    for t in tunes:
        try:
            rows_by_tune[t["file"]] = decode_tune(open(t["path"], "rb").read())
        except Exception as exc:                      # noqa: BLE001 - report, never crash a gate
            print(f"FAIL: {t['rel']} does not decode: {exc}")
            bad += 1
    print(f"{os.path.relpath(root, ROOT) if root.startswith(ROOT) else root}: "
          f"{len(tunes)} tune file(s) under editor/entities/jc_weapons")
    for e in edits:
        m = re.search(r"`(w\d{3})", e.get("scope", ""))
        if not m:
            print(f"FAIL: {e['row']} {e['member']}: no wNNN token in scope {e.get('scope')!r}")
            bad += 1
            continue
        tok = m.group(1)
        hit = [t for t in tunes if t["file"].startswith(tok + "_")]
        if len(hit) != 1:
            print(f"FAIL: {e['row']} {e['member']}: {len(hit)} built tune(s) for {tok}")
            bad += 1
            continue
        t = hit[0]
        dec = rows_by_tune.get(t["file"])
        if dec is None:
            bad += 1
            continue
        vals = [(row[0], float(row[2])) for inst in dec["instances"] for row in inst["rows"]
                if row[1] == "float" and row[0].rsplit(".", 1)[-1] == e["member"]]
        if len(vals) != 1:
            print(f"FAIL: {t['file']} {e['member']}: {len(vals)} float row(s) with that leaf name")
            bad += 1
            continue
        path, got = vals[0]
        want = float(e["new"])
        ok = abs(got - want) <= 1e-6 * max(1.0, abs(want))
        print(f"  {t['file']:34s} {e['member']:10s} {got:<12.6g} "
              f"({e['row']} expected {want:<8.6g}) {'ok' if ok else 'MISMATCH'}")
        print(f"      row {path}, {e['conf']} class")
        if not ok:
            bad += 1
    print(f"{'check ok' if not bad else 'FAIL'}: {len(edits) - bad}/{len(edits)} edit(s) re-read "
          f"from the built tunes, {len(tunes)}/{len(tunes)} tune file(s) decode")
    return 1 if bad else 0


def cmd_dump(a) -> int:
    rows, shared, _stats, _ext, _lines = build(a.game, False)
    hit = [r for r in rows if a.want.lower() in r["id"].lower()]
    hit += [s for s in shared if a.want.lower() in s["name"].lower()]
    if not hit:
        raise SystemExit(f"no weapon id matches {a.want!r}")
    for r in hit:
        print(f"=== {r.get('id') or r.get('name')}  kind={r.get('kind', 'shared')}  "
              f"entities={r.get('entities', '?')}  archive={r.get('archive', '?')}")
        for s in r.get("sources", []):
            print(f"  source {s['mount']:5s} {s['origin'] if s.get('origin') else 'embedded':11s} "
                  f"{s['path']}  ({s['size']} B, {s['rows']} rows)")
        for t in r.get("tunes", []):
            for i in t["instances"]:
                print(f"  [{t['class']}] {i['name']} ({len(i['rows'])} rows)")
                for p, ty, v in i["rows"][:a.max]:
                    print(f"    {p:72s} {ty:8s} {v}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true", help="decode, extract and write the records")
    p.add_argument("--check", action="store_true", help="re-read the archives and compare")
    p.add_argument("--game", default=os.environ.get("JC3_GAME", DEFAULT_GAME))
    p.add_argument("--root", metavar="BUILD",
                   help="with --check: re-read a build's `.wtunec` files instead of the archives "
                        "(no archive is touched); proves T-11's edits landed in the copies")
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("want")
    d.add_argument("--max", type=int, default=40)
    a = p.parse_args()
    if a.cmd == "dump":
        return cmd_dump(a)
    if a.check and a.root:
        return cmd_check_root(a)
    if a.write:
        if a.root:
            raise SystemExit("--write does not take --root: build files are written by the card's "
                             "own generator (e.g. bm_weapons.py)")
        return cmd_write(a)
    if a.check:
        return cmd_check(a)
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
