"""t2_facts.py - the measured facts behind T-2 (appearance, assembly, audio, damage).

T-2 translates the half of the grab T-1 does not cover: materials and textures, parts and
sockets, lights, audio, effects, damage, collision, weapons. Every number in that document is
printed by this script from files already on disk, so a stale claim shows up as a diff instead
of as prose.

Inputs (all in-repo, no game files):
  Working/Translation/current.json      build 083 module values (Tools/scripts/t1_current.py)
  Research/BatmobileGrab/SLOTS.json     19 material slots, 13 instances, 38 textures
  Research/BatmobileGrab/LIGHTS.json    101 BmAK light entries across 4 rigs
  Research/BatmobileGrab/PHYSICS.json   32 RB_BodySetup bodies per package
  Research/BatmobileGrab/AUDIO_MAP.json 27 banks, 361 event rows, 447 media
  Research/JC3Grab/VOCABULARY.md        fleet ranges for the members T-2 cites

Usage:
  python t2_facts.py            # write Working/Translation/T2_FACTS.md
  python t2_facts.py check      # regenerate in memory and compare with the committed file
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TRANS = os.path.join(ROOT, "Working", "Translation")
GRAB = os.path.join(ROOT, "Research", "BatmobileGrab")
OUT = os.path.join(TRANS, "T2_FACTS.md")

# Members T-2 quotes, in document order. Fleet ranges come from VOCABULARY.md.
FLEET_ROWS = [
    "VehicleDamage.max_health",
    "VehicleDamage.bullet_armor_strength",
    "VehicleDamage.bullet_heavy_armor_strength",
    "VehicleDamage.explosion_threshold",
    "VehicleDamage.smoke_threshold",
    "VehicleDamage.burn_threshold",
    "VehicleDamage.part_damage_types[].initial_health",
    "VehicleDamage.part_damage_types[].damaged_health",
    "VehicleDamage.part_damage_types[].loosen_health",
    "VehicleDamage.part_damage_types[].type.string",
    "VehicleDynamicLights.lights[].range",
    "VehicleDynamicLights.lights[].angle",
    "VehicleDynamicLights.lights[].multiplier",
    "VehicleDynamicLights.lights[].behavior",
    "Palette.tints[].specular_gloss",
    "EffectAttachments.all_effects[].effect.string",
    "EffectAttachments.part_effects[].effects_count",
    "VehicleMisc.official_top_speed",
    "VehicleParts.parts[].has_world_collision_shape",
    "VehicleParts.parts[].world_collision_body_id",
]


def load(name: str):
    with open(os.path.join(GRAB, name), encoding="utf-8") as f:
        return json.load(f)


def build_modules() -> dict:
    with open(os.path.join(TRANS, "current.json"), encoding="utf-8") as f:
        return json.load(f)["modules"]


def count_list(values: dict, prefix: str) -> int:
    idx = [int(m.group(1)) for k in values for m in [re.match(re.escape(prefix) + r"\[(\d+)\]", k)] if m]
    return max(idx) + 1 if idx else 0


def fleet_ranges() -> dict[str, str]:
    """Parse VOCABULARY.md into {member_path: 'type | range | donor'}."""
    out: dict[str, str] = {}
    module = ""
    with open(os.path.join(ROOT, "Research", "JC3Grab", "VOCABULARY.md"), encoding="utf-8") as f:
        for line in f:
            head = re.match(r"^## `([^`]+)`", line)
            if head:
                module = head.group(1)
                continue
            m = re.match(r"^\| `([^`]+)` \| ([^|]+) \| ([^|]+) \| ([^|]*) \|$", line.rstrip("\n"))
            if m:
                member, typ, rng, donor = (x.strip() for x in m.groups())
                key = f"{module}.{member}"
                if key not in out:
                    out[key] = f"{typ} | {rng} | {donor or '—'}"
    return out


def build_section(mods: dict) -> list[str]:
    rows = [
        ("VehicleDamage", "health profile + 24 part damage types"),
        ("VehicleDynamicLights", "lights"),
        ("EffectAttachments", "effect table"),
        ("Palette", "paint tints"),
        ("LandAudio", "audio"),
        ("Decals", "decals"),
        ("DeformPoints", "deform points"),
        ("VehicleMisc", "misc"),
        ("WaterInteraction", "water interaction"),
        ("sportsmuscle_vehicle_parts", "parts (G2-7)"),
    ]
    lines = ["## Build 083 — the modules T-2 translates", "",
             "| module | values | what it holds |", "|---|---|---|"]
    for name, what in rows:
        m = mods.get(name)
        if m is None:
            lines.append(f"| `{name}` | — | not in the build |")
        elif "error" in m:
            lines.append(f"| `{name}` | **decode failed** | {what} — {m['error']} |")
        else:
            lines.append(f"| `{name}` | {len(m['values'])} | {what} |")

    v = mods["VehicleDamage"]["values"]
    lines += ["", "### Damage (build 083)", "",
              "| member | value |", "|---|---|"]
    for k in ("max_health", "bullet_armor_strength", "bullet_heavy_armor_strength",
              "explosion_threshold", "smoke_threshold", "burn_threshold", "burn_duration_s",
              "explosion_delay_s", "deform_scale"):
        if k in v:
            lines.append(f"| `{k}` | {v[k]} |")
    n = count_list(v, "part_damage_types")
    lines += ["", f"`part_damage_types`: **{n}** entries", "",
              "| # | type | initial_health | damaged_health | loosen_health |", "|---|---|---|---|---|"]
    for i in range(n):
        g = lambda s: v.get(f"part_damage_types[{i}].{s}")  # noqa: E731
        lines.append(f"| {i} | `{g('type.string')}` | {g('initial_health')} | "
                     f"{g('damaged_health')} | {g('loosen_health')} |")

    lv = mods["VehicleDynamicLights"]["values"]
    nl = count_list(lv, "lights")
    lines += ["", f"### Lights (build 083) — **{nl}** entries", "",
              "| # | behavior | preset_id | range | angle | diffuse R,G,B |", "|---|---|---|---|---|---|"]
    for i in range(nl):
        g = lambda s: lv.get(f"lights[{i}].{s}")  # noqa: E731
        rgb = f"{g('diffuse.R')}, {g('diffuse.G')}, {g('diffuse.B')}"
        lines.append(f"| {i} | `{g('behavior')}` | {g('preset_id')} | {g('range')} | "
                     f"{g('angle')} | {rgb} |")

    ev = mods["EffectAttachments"]["values"]
    ne, npart, nuse = (count_list(ev, "all_effects"), count_list(ev, "part_effects"),
                       count_list(ev, "usage_effects"))
    effects = sorted({val for k, val in ev.items() if re.fullmatch(r"all_effects\[\d+\]\.effect\.string", k)})
    usages = [ev.get(f"usage_effects[{i}].usage.string") for i in range(nuse)]
    lines += ["", f"### Effects (build 083) — **{ne}** effect rows over "
                  f"**{npart}** parts, **{nuse}** usage rows", "",
              f"distinct effects ({len(effects)}): " + ", ".join(f"`{e}`" for e in effects), "",
              "usages: " + ", ".join(f"`{u}`" for u in usages)]

    pv = mods["Palette"]["values"]
    nt = count_list(pv, "tints")
    lines += ["", f"### Palette (build 083) — **{nt}** tints", "",
              "| # | name | specular_gloss | clear_coat | metallic |", "|---|---|---|---|---|"]
    for i in range(nt):
        g = lambda s: pv.get(f"tints[{i}].{s}")  # noqa: E731
        lines.append(f"| {i} | `{g('name.string')}` | {g('specular_gloss')} | "
                     f"{g('clear_coat')} | {g('metallic')} |")

    mv = mods["VehicleMisc"]["values"]
    lines += ["", "### Misc that T-2 touches", "", "| member | value |", "|---|---|"]
    for k in ("official_top_speed", "max_landing_speed_kmph", "full_nitro_use_time",
              "full_nitro_refill_time"):
        lines.append(f"| `{k}` | {mv.get(k)} |")
    av = mods["LandAudio"]["values"]
    lines += ["", "`LandAudio` members: " + ", ".join(f"`{k}` = {v}" for k, v in av.items())]
    return lines


def bmak_section() -> list[str]:
    slots = load("SLOTS.json")["summary"]
    lights = load("LIGHTS.json")["summary"]
    phys = load("PHYSICS.json")
    audio = load("AUDIO_MAP.json")["summary"]
    phys_pkg = next(iter(phys.values()))
    lines = ["## BmAK — what T-2 has to translate from", "",
             "### Materials and textures (`SLOTS.json`)", "",
             "| item | value |", "|---|---|"]
    for k in ("slots", "instances", "textures", "lod0_faces", "slots_with_geometry",
              "slots_without_geometry", "lods", "lod_maps_identity"):
        lines.append(f"| {k} | {slots.get(k)} |")
    lines += ["", "### Lights (`LIGHTS.json`)", "",
              f"entries **{lights['entries']}** across **{lights['vehicles']}** rigs; "
              f"orphan sockets **{lights['orphan_sockets']}**; missing bones "
              f"**{lights['missing_bones']}**", "",
              "| by type | n |", "|---|---|"]
    for k, v in sorted(lights["by_type"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines += ["", "| disposition | n |", "|---|---|"]
    for k, v in sorted(lights["by_disposition"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    lines += ["", "| part the light names | n |", "|---|---|"]
    for k, v in sorted(lights["by_part"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")

    lines += ["", "### Collision bodies (`PHYSICS.json`)", "",
              "| package | bodies | boxes | spheres |", "|---|---|---|---|"]
    tot = 0
    for pkg, d in phys.items():
        bodies = d["bodies"]
        tot += len(bodies)
        lines.append(f"| {pkg} | {len(bodies)} | {sum(b.get('boxes', 0) for b in bodies)} | "
                     f"{sum(b.get('spheres', 0) for b in bodies)} |")
    first = phys_pkg["bodies"][0]
    lines += ["", f"total bodies **{tot}**; largest body box "
                  f"{max(phys_pkg['bodies'], key=lambda b: max(b['extents']))['extents']} cm "
                  f"(bone `{first['bone']}` is {first['extents']} cm)"]

    lines += ["", "### Audio (`AUDIO_MAP.json`)", "", "| item | value |", "|---|---|"]
    for k in ("banks", "bytes", "rows", "unique_event_ids", "resolved_rows", "resolved_ids",
              "streamed_rows", "no_media_rows", "missing_rows", "missing_ids", "media",
              "media_bytes"):
        lines.append(f"| {k} | {audio.get(k)} |")
    lines += ["", "missing banks: " + ", ".join(f"`{b}`" for b in audio["missing_banks"])]
    return lines


def fleet_section() -> list[str]:
    rows = fleet_ranges()
    lines = ["## JC3 fleet — the shipped range behind each T-2 row", "",
             "Rows are quoted from `VOCABULARY.md`; the range column keeps its `(n=…)` sample size.", "",
             "| member | type | fleet range | donor |", "|---|---|---|---|"]
    missing = []
    for m in FLEET_ROWS:
        if m in rows:
            typ, rng, donor = (x.strip() for x in rows[m].split("|"))
            lines.append(f"| `{m}` | {typ} | {rng} | {donor} |")
        else:
            missing.append(m)
    if missing:
        lines += ["", "**not in VOCABULARY.md** (never decoded in the fleet sample): "
                      + ", ".join(f"`{m}`" for m in missing)]
    return lines


def render() -> str:
    mods = build_modules()
    parts = ["# T-2 facts — generated, do not edit", "",
             "`Tools/scripts/t2_facts.py` · inputs: `current.json`, `Research/BatmobileGrab/*.json`, "
             "`Research/JC3Grab/VOCABULARY.md`. Any number in `T2_TRANSLATION.md` that is not here is "
             "marked as an assumption there.", ""]
    parts += build_section(mods)
    parts += [""] + bmak_section()
    parts += [""] + fleet_section()
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    text = render()
    if len(argv) > 1 and argv[1] == "check":
        try:
            with open(OUT, encoding="utf-8") as f:
                old = f.read()
        except FileNotFoundError:
            print(f"missing {OUT}")
            return 1
        if old != text:
            print(f"stale: {OUT} differs from a fresh run of t2_facts.py")
            return 1
        print(f"ok: {os.path.relpath(OUT, ROOT)} is current")
        return 0
    os.makedirs(TRANS, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
