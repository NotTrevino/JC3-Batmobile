"""bm_rc4_lights.py - D-03: every light in `Builds/bm-RC4-lights`, built on `bm-RC4-parts`.

The brief: build every light in the RC4 tree from the light plans
(`headlight-beam-plan.md`, `taillight-brake-reverse-plan.md`,
`underglow-and-accent-lights-plan.md`, `muzzle-and-forensics-lights.md`,
`lens-flare-carriers.md`, `apply-light-rows.md`) and `LIGHTS.md` / `LIGHTS.json`.

This step owns one file: the vehicle's `VehicleDynamicLights` module.

  * The row set is `bm_lightrig.plan()` (B-07's generator, unchanged): the T-18 map against the
    donor module, re-hosted on the parts `bm-RC4-parts` actually built. It is imported, not
    forked, so a value that B-07 owns is not retyped here.
  * The plans then replace the shipped donor numbers where they give one (`OVERRIDES`), and add
    the reverse pair (`reverse_rows`) the tail plan calls an addition.
  * No geometry is written. The `CarLight` emitter blocks are B-03's, already inside the lamp RBMs
    `bm-RC4-parts` carries; this step counts them as the flare carrier's file-level proof.
  * Nothing is launched and nothing is installed.

Usage
    python Tools/scripts/bm_rc4_lights.py --write
    python Tools/scripts/bm_rc4_lights.py --check
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_lightrig as L                              # noqa: E402
import jc3adf                                        # noqa: E402
import rbm_geom as R                                  # noqa: E402
import rbmhdr                                        # noqa: E402
from eetoc import read_toc, sarc_dir, unaaf          # noqa: E402

BASE = "bm-RC4-parts"                 # D-02 tree: the parts split the lights hang on
TAG = "bm-RC4-lights"                 # this step
SPEC = os.path.join(ROOT, "Working", "Lights", "bm_rc4_lights.json")
WORK = os.path.join(ROOT, "tmp", "d03")
CARD = "D-03"
EE = L.EE
MODULE = L.MODULE
MODULE_NAME = L.MODULE_NAME
PARTS_MODULE = L.PARTS_MODULE
FLOATS, INTS, STRINGS, MEMBERS = L.FLOATS, L.INTS, L.STRINGS, L.MEMBERS

# The eight lamp parts B-03 cut; the headlight and tail-strip ones are the flare carriers.
LAMP_PARTS = ("sportsmuscle_headlight_f_l", "sportsmuscle_headlight_f_r",
              "sportsmuscle_wheel_f_l_arch", "sportsmuscle_wheel_f_r_arch",
              "sportsmuscle_wheel_r_l_arch", "sportsmuscle_wheel_r_r_arch",
              "sportsmuscle_tailstrip_r_l", "sportsmuscle_tailstrip_r_r")

# --------------------------------------------------------------------------- plan overlays
# Keyed by the B-07 row's origin (stable against a part re-index), not by row number. Every
# value is the plan's own number; `src` names the row of the plan it came from.
def beam_row(reach: float, falloff: float, halo: bool) -> dict:
    d = {
        "range": (reach, "headlight-beam-plan §3: BmAK radius 6000 cm -> 60 m" if reach == 60.0 else
                  "headlight-beam-plan §3: BmAK second spot 1800 cm -> 18 m"),
        "angle": (70.0, "headlight-beam-plan §3: BmAK outer cone 70 deg (shipped JC3 max is 50; "
                       "writable, U-1)"),
        "falloff_start": (falloff, "headlight-beam-plan §3: BmAK falloff 1.0 -> 0.8 / 2.0 -> 0.0 "
                                   "(look-alike, flagged G)"),
        "multiplier": (1.0, "headlight-beam-plan §3: Brightness 0.15 -> multiplier 1.0 (G: no "
                            "decoded bridge; fleet mode)"),
        "light_type": (1, "headlight-beam-plan §3: a cone; the fleet's light_type 1 rows are the "
                          "cones"),
        "cast_shadows": (0, "headlight-beam-plan §3: BmAK CastShadows False"),
        "volumetric_mode": (1 if halo else 0,
                            "lens-flare-carriers §5.1 / §2.3: volumetric halo is one of the three "
                            "decoded flare carriers"),
        "volume_intensity": (0.002 if halo else 1.0,
                             "lens-flare-carriers §2.3: volume_intensity ships 0.001-0.0025"),
    }
    return d


OVERRIDES = {
    ("donor-row 8", ("T-L25", "T-L27", "T-L8")): beam_row(60.0, 0.8, True),
    ("donor-row 13", ("T-L8",)): beam_row(18.0, 0.0, False),
    ("donor-row 20", ("T-L26", "T-L29", "T-L9")): beam_row(60.0, 0.8, True),
    ("donor-row 19", ("T-L9",)): beam_row(18.0, 0.0, False),
    # battle headlights: underglow-and-accent §1 table (red, Brightness 5.0, radius 1024 cm,
    # inner 10 / outer 35), on T-L22's member recipe for the same component shape.
    ("custom (T-L18)", ("T-L18",)): {
        "range": (10.24, "underglow-and-accent §1: BmAK battle radius 1024 cm -> 10.24 m"),
        "angle": (35.0, "underglow-and-accent §1: battle outer cone 35 deg"),
        "falloff_start": (0.8, "muzzle-and-forensics T-L22: the fleet mode for a shadow-casting "
                               "cone"),
        "multiplier": (5.0, "muzzle-and-forensics T-L22: BmAK Brightness 5.0 -> multiplier 5 (12 "
                            "shipped rows use it)"),
        "light_type": (1, "muzzle-and-forensics T-L22: all 723 cone rows"),
        "cast_shadows": (1, "underglow-and-accent §1: BmAK CastDynamicShadows True"),
        "volumetric_mode": (1, "muzzle-and-forensics T-L22: the two shadow rows ship volumetric 1"),
        "volume_intensity": (0.02, "muzzle-and-forensics T-L22: the two shadow rows ship 0.02"),
    },
    ("custom (T-L19)", ("T-L19",)): None,          # filled from the T-L18 table below
    # battle wheel arch: underglow-and-accent §4 ("entry B": 2048 cm, 15 deg, brightness 0.0)
    ("custom (T-L20)", ("T-L20",)): {
        "range": (20.48, "underglow-and-accent §4: battle wheel radius 2048 cm -> 20.48 m"),
        "angle": (15.0, "underglow-and-accent §4: battle wheel outer cone 15 deg"),
        "falloff_start": (0.0, "underglow-and-accent §4: falloff_start 0"),
        "multiplier": (1.0, "underglow-and-accent §4: multiplier 1 (BmAK brightness is 0.0)"),
        "light_type": (1, "underglow-and-accent §4: a 15 deg cone"),
        "cast_shadows": (0, "underglow-and-accent §1: battle wheel CastDynamicShadows True is "
                            "BmAK's flag; left 0 because the shipped battle-wheel row it maps "
                            "(T-L20) carries no shadow proof"),
    },
    # boot / interior reached and coned from the same plan
    ("custom (T-L35)", ("T-L35",)): {
        "range": (4.0, "underglow-and-accent §4: boot reach 400 cm -> 4.0 m"),
        "angle": (60.0, "underglow-and-accent §4: boot outer cone 60 deg"),
        "falloff_start": (0.8, "underglow-and-accent §4: falloff 0.8 (G)"),
        "multiplier": (1.0, "underglow-and-accent §4: multiplier 1"),
        "light_type": (1, "the module's own convention, angle > 10 -> light_type 1"),
    },
    ("donor-row 2", ("T-L24",)): {
        "range": (0.8, "underglow-and-accent §4: interior reach 80 cm -> 0.8 m"),
        "angle": (45.0, "underglow-and-accent §4: interior outer cone 45 deg"),
        "falloff_start": (0.8, "underglow-and-accent §4: falloff 0.8 (G)"),
        "multiplier": (1.0, "underglow-and-accent §4: multiplier 1"),
        "light_type": (1, "the module's own convention, angle > 10 -> light_type 1"),
    },
}
OVERRIDES[("custom (T-L19)", ("T-L19",))] = dict(OVERRIDES[("custom (T-L18)", ("T-L18",))])

# The reverse pair: the tail plan calls it an addition (BmAK has no reverse lamp; its cue is
# audio), and the `Reverse` behaviour is the only carrier. Vanilla `Reverse` tuple.
REVERSE = (
    {"part": "sportsmuscle_tailstrip_r_l", "row": "T-L15", "side": "left"},
    {"part": "sportsmuscle_tailstrip_r_r", "row": "T-L16", "side": "right"},
)
REVERSE_VALUES = {
    "behavior": "Reverse", "diffuse.R": 1.0, "diffuse.G": 1.0, "diffuse.B": 1.0,
    "range": 2.0, "falloff_start": 0.0, "near_cap": 1.0, "multiplier": 1.0,
    "min_luminosity": 0.0, "light_type": 0, "blinking": 0, "angle": 10.0,
    "cast_shadows": 0, "projected_texture_index": -1, "volumetric_mode": 0,
    "volume_intensity": 1.0, "uvscale.u": 1.0, "uvscale.v": 1.0, "preset_id": 0,
}

BLOCKED = [
    {"what": "underglow / underbody lamp", "plan": "underglow-and-accent-lights-plan §1.2, §5",
     "why": "BmAK ships no underglow (0 of 21 sockets, 0 `underglow|neon` hits, 0 class-default "
            "members). Its low accent is the `Batmobile_V3_Emissive` wheel material, which is an "
            "emissive map, not a lamp. Building one would be a feature, and the plan says do not."},
    {"what": "brake state", "plan": "taillight-brake-reverse-plan §2.1",
     "why": "JC3 has no `BRAKE` action and no `BrakeLight` behaviour; BmAK does not change the "
            "lamp for braking either (it adds a flare + a particle trail). Nothing to place."},
    {"what": "lamp-bound flare sprite (T-24)", "plan": "lens-flare-carriers §2.4, §5.2",
     "why": "`effects/flare/headlight_flare_01.effc` exists in 160 vehicle bundles, but no light "
            "member points at an effect and `.effc` carries no strings, so the sprite cannot be "
            "bound from this module. Unproven (`T-24`)."},
    {"what": "orphan flare rows HeadLight1c / HeadLight2c (T-L28, T-L30)",
     "plan": "lens-flare-carriers §3, §5.3",
     "why": "Both rows have a null socket and a null bone in LIGHTS.json, and the body part has "
            "neither a `_LIG` node nor a `CarLight` block: there is no anchor to hang an entry on."},
]


# --------------------------------------------------------------------------- domain ledger
# The one question the build could not answer from a decode: does anything shipped render a reach
# above 50 m or a cone above 50 deg? `LIGHT_SYSTEM.json` counts every shipped
# `VehicleDynamicLights` entry, so a value in no census bucket is writable but unproven. These
# labels ride on the rows they touch; `--check` re-reads the census and fails if a label and the
# census ever disagree (a value that ships may not be called out-of-domain, and vice versa).
CENSUS = os.path.join(ROOT, "Research", "JC3Grab", "LIGHT_SYSTEM.json")


def beam_claim(reach: float, falloff: float) -> dict:
    """The two beam rows' stand-ins, and the reach/angle pair when they leave the shipped set."""
    members = {
        "angle": {"kind": "out-of-domain", "v": 70.0,
                  "why": "BmAK's outer cone is 70 deg (M); the fleet's widest cone is 50 deg, so "
                         "this is a legal float with no shipped carrier - U-1, a claim"},
        "multiplier": {"kind": "stand-in", "v": 1.0,
                       "why": "the fleet mode (2,188 of 3,217 entries), not a decode: no "
                              "Brightness -> multiplier bridge exists and BmAK's Brightness is "
                              "0.15 - U-2"},
        "falloff_start": {"kind": "stand-in", "v": falloff,
                          "why": "BmAK's falloff 1.0/2.0 is a spot exponent; JC3's "
                                 "falloff_start is the fraction where falloff begins. Different "
                                 "quantity, so this is a look-alike, not a port - U-3"},
    }
    if reach > 50.0:
        members["range"] = {"kind": "out-of-domain", "v": reach,
                            "why": "BmAK reaches 6000 cm -> 60 m (D on an M); the fleet's "
                                   "longest reach is 50 m, so nothing shipped renders this - "
                                   "U-1, a claim"}
    return members


# Keyed by the same stable (origin, t18_rows) key as OVERRIDES, so a re-index cannot move a label.
MARKS = {
    ("donor-row 8", ("T-L25", "T-L27", "T-L8")):
        {"status": "out-of-domain", "members": beam_claim(60.0, 0.8)},
    ("donor-row 13", ("T-L8",)):
        {"status": "out-of-domain", "members": beam_claim(18.0, 0.0)},
    ("donor-row 20", ("T-L26", "T-L29", "T-L9")):
        {"status": "out-of-domain", "members": beam_claim(60.0, 0.8)},
    ("donor-row 19", ("T-L9",)):
        {"status": "out-of-domain", "members": beam_claim(18.0, 0.0)},
    # T-L17 carries the donor graph object's own numbers: no plan gives this row values, so calling
    # it a BmAK translation would invent a bridge. Its 60 deg cone is also outside the shipped set.
    ("graph-object (T-L17)", ("T-L17",)):
        {"status": "donor-carried", "members": {
            "range": {"kind": "donor-carried", "v": 10.0,
                      "why": "graph object `Front_Secondary_Head`.radius; no plan gives T-L17 "
                             "numbers, so it is carried, not translated"},
            "angle": {"kind": "donor-carried", "v": 60.0,
                      "why": "graph object `.spot_angle`; carried, and also outside the fleet's "
                             "50 deg top - donor-carried AND out of domain"},
            "volume_intensity": {"kind": "donor-carried", "v": 0.25,
                                 "why": "graph object `.volume_intensity`; carried, not "
                                        "translated"},
        }},
}


def domain_ledger(pl: dict) -> dict:
    """The rows' labels against the shipped census, with the census's own maxima re-read."""
    system = json.load(open(CENSUS, encoding="utf-8"))
    census = system["module"]["value_census"]
    hist = {m: {float(k): int(v) for k, v in census[m].items()}
            for m in ("range", "angle", "multiplier", "falloff_start", "volume_intensity")}

    def ships(member: str, v) -> int:
        for k, n in hist.get(member, {}).items():
            if abs(k - float(v)) <= 1e-6:
                return n
        return 0

    labels = []
    for row in pl["rows"]:
        claim = row.get("claim")
        if not claim:
            continue
        for member, mk in claim["members"].items():
            labels.append({"index": row["index"], "origin": row["origin"], "member": member,
                           "kind": mk["kind"], "v": mk["v"],
                           "ships_in_fleet": ships(member, mk["v"]), "why": mk["why"]})

    max_r, max_a = max(hist["range"]), max(hist["angle"])
    return {
        "question": ("can the fleet census prove `range` 60 m / `angle` 70 deg renders? (its "
                     "shipped maxima are 50 m and 50 deg)"),
        "source": ("Research/JC3Grab/LIGHT_SYSTEM.json -> module.value_census (every shipped "
                   "`VehicleDynamicLights` entry)"),
        "entries": int(system["module"]["entries"]),
        "shipped_max": {"range": max_r, "angle": max_a},
        "shipped_rows_at_max": {"range": hist["range"][max_r],
                                "angle": hist["angle"][max_a]},
        "verdict": ("no. No shipped entry reaches past 50 m or 50 deg, so the census cannot show "
                    "that 60 m / 70 deg renders; those rows are labelled out-of-domain claims, "
                    "not decoded values. `multiplier` 1.0 and `falloff_start` 0.8/0.0 are "
                    "stand-ins, and T-L17 (row 11) is donor-carried."),
        "labels": labels,
    }


# --------------------------------------------------------------------------- helpers
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def configure() -> None:
    """Point bm_lightrig's own globals at this step's tree, so its encoder is reused as-is."""
    L.BASE_TAG, L.PACK_TAG, L.TAG = BASE, BASE, TAG
    L.SPEC = SPEC
    L.WORK = WORK


def aaf(tag: str) -> str:
    return os.path.join(ROOT, "Builds", tag, "aaf")


def module_in(tag: str) -> str:
    return os.path.join(aaf(tag), MODULE.replace("/", os.sep))


def decode_parts(path: str) -> dict[int, dict]:
    adf = jc3adf.Adf(open(path, "rb").read())
    return {int(p["part_index"]): p for p in jc3adf.parts(adf)}


def hj(text: str) -> int:
    return rbmhdr.hash_jenkins(text.encode("ascii"))


def plan() -> dict:
    configure()
    pl = L.plan()

    # 1. the plans' values, on the rows they name
    for row in pl["rows"]:
        key = (row["origin"], tuple(row["t18_rows"]))
        ov = OVERRIDES.get(key)
        if ov is None:
            continue
        for m, (v, src) in ov.items():
            if m not in MEMBERS:
                raise SystemExit(f"{key}: {m} is not one of the module's 25 members")
            row["members"][m] = {"v": v, "class": "plan", "src": src}

    # 2. the reverse pair, appended on the tail parts the T-L15/T-L16 rows already use
    for spec in REVERSE:
        host = next(r for r in pl["rows"] if r["t18_rows"] == [spec["row"]])
        part = host["part"]
        if part["name"] != spec["part"]:
            raise SystemExit(f"reverse {spec['side']}: tail row {spec['row']} is on "
                             f"{part['name']}, not {spec['part']}")
        anchor = host["members"]["deformable_transform"]["v"]
        vals = dict(REVERSE_VALUES)
        members = {}
        for m in MEMBERS:
            if m == "behavior_hash":
                members[m] = {"v": hj(vals["behavior"]), "class": "derived",
                              "src": "rbmhdr.hash_jenkins('Reverse')"}
            elif m in ("part", "part_hash", "part_index"):
                members[m] = {"v": {"part": part["name"], "part_hash": hj(part["name"]),
                                    "part_index": part["part_index"]}[m],
                              "class": "decoded",
                              "src": f"the built parts module (D-02), the same host as "
                                     f"{spec['row']}"}
            elif m in ("deformable_transform", "deformable_transform_hash"):
                members[m] = {"v": anchor if m == "deformable_transform" else hj(anchor),
                              "class": "decoded",
                              "src": f"{spec['row']}'s anchor (this part is the reverse lamp's "
                                     f"nearest lit carrier)"}
            else:
                members[m] = {"v": vals[m], "class": "decoded",
                              "src": "taillight-brake-reverse-plan §3.2 (vanilla `Reverse` tuple; "
                                     "an addition, not a BmAK translation)"}
        pl["rows"].append({"index": len(pl["rows"]), "origin": f"custom (D-03 reverse {spec['side']})",
                           "t18_rows": [spec["row"] + "+reverse"], "part": part,
                           "anchor": anchor, "members": members})

    # 3. the domain labels, on the rows the census cannot vouch for
    for row in pl["rows"]:
        marks = MARKS.get((row["origin"], tuple(row["t18_rows"])))
        if marks:
            row["claim"] = {"status": marks["status"], "members": marks["members"]}

    pl["card"] = CARD
    pl["generator"] = "Tools/scripts/bm_rc4_lights.py"
    pl["scope"] = ("every light entry in the RC4 tree: headlight beams, tail, reverse, accents, "
                   "muzzle, forensics and the flare carriers")
    pl["module"]["rows_after"] = len(pl["rows"])
    pl["build"] = {"tag": TAG, "base": f"Builds/{BASE}"}
    pl["plans"] = {
        "headlight": "tmp/freebuff/reports/headlight-beam-plan.md",
        "tail_brake_reverse": "tmp/freebuff/reports/taillight-brake-reverse-plan.md",
        "underglow_accent": "tmp/freebuff/reports/underglow-and-accent-lights-plan.md",
        "muzzle_forensics": "tmp/freebuff/reports/muzzle-and-forensics-lights.md",
        "lens_flare": "tmp/freebuff/reports/lens-flare-carriers.md",
        "rows": "tmp/freebuff/reports/apply-light-rows.md",
        "values": "Research/BatmobileGrab/LIGHTS.md + LIGHTS.json",
    }
    pl["overrides"] = [
        {"origin": o, "t18_rows": list(t), "members": {m: {"v": v, "src": s}
                                                       for m, (v, s) in ov.items()}}
        for (o, t), ov in OVERRIDES.items()]
    pl["blocked"] = BLOCKED
    counts = {}
    for r in pl["rows"]:
        b = r["members"]["behavior"]["v"]
        counts[b] = counts.get(b, 0) + 1
    pl["counts"] = {"rows": len(pl["rows"]), "by_behavior": counts,
                    "parts": sorted({r["part"]["name"] for r in pl["rows"]}),
                    "t18_rows_covered": sorted({t for r in pl["rows"] for t in r["t18_rows"]})}
    pl["domain"] = domain_ledger(pl)
    return pl


# --------------------------------------------------------------------------- build
def carlight_census(root_aaf: str) -> dict:
    """`CarLight` blocks per lamp part, read from the lamp LOD1 RBMs in the tree."""
    out = {}
    base = os.path.join(root_aaf, "models", "jc_vehicles", "01_land",
                        "v0300_car_kensington_sportsmuscle")
    for name in LAMP_PARTS:
        lods = {}
        for i in (1, 2, 3):
            p = os.path.join(base, f"{name}_lod{i}.rbm")
            if not os.path.exists(p):
                continue
            m = R.decode(open(p, "rb").read())
            lods[f"lod{i}"] = {"bytes": os.path.getsize(p), "blocks": len(m.blocks),
                               "block_names": m.block_names(),
                               "car_light_blocks": sum(
                                   1 for b in m.blocks
                                   if R.BLOCK_NAMES.get(b.type_hash) == "CarLight")}
        out[name] = {"lods": lods,
                     "car_light_blocks": sum(x["car_light_blocks"] for x in lods.values())}
    return out


def write_build(pl: dict) -> int:
    tdir = os.path.join(ROOT, "Builds", TAG)
    if not os.path.exists(module_in(BASE)):
        raise SystemExit(f"base build incomplete: {rel(module_in(BASE))}")
    if os.path.exists(tdir):
        raise SystemExit(f"Builds/{TAG} exists (remove it to rebuild)")
    os.makedirs(tdir)
    aaf_out = os.path.join(tdir, "aaf")
    shutil.copytree(aaf(BASE), aaf_out)

    work = os.path.join(WORK, "build")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    fresh = os.path.join(work, MODULE_NAME)
    info = L.encode(pl, fresh, work)
    shutil.copyfile(fresh, os.path.join(aaf_out, MODULE.replace("/", os.sep)))
    print(f"module {MODULE_NAME}: {info['base_bytes']} -> {info['bytes']} B "
          f"({info['delta_bytes']:+d}), {len(pl['rows'])} rows")

    # pack the same aaf with the new module, then re-derive the .toc against the base .ee
    ee = os.path.join(tdir, EE)
    L.run([os.path.join(L.GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf_out, ee], "SmallPack")
    L.run([os.path.join(L.GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee,
           os.path.join(tdir, "verify")], "SmallUnpack")
    base_ee = os.path.join(ROOT, "Builds", BASE, EE)
    L.run([sys.executable, os.path.join(HERE, "eetoc.py"), "patch", ee, base_ee + ".toc",
           "--base-ee", base_ee, "-o", ee + ".toc"], "eetoc patch")
    toc = ee + ".toc"
    recs = read_toc(open(toc, "rb").read())
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    bad = [(n, (o, s), real.get(n)) for n, o, s in recs if o and real.get(n) != (o, s)]
    if bad:
        raise SystemExit(f"{len(bad)} .toc record(s) disagree with the .ee: {bad[:3]}")
    mod_rec = next((x for x in recs if x[0] == MODULE), None)
    if not mod_rec or mod_rec[1] == 0:
        raise SystemExit("the lights module has no internal .toc record")

    r = L.run([sys.executable, os.path.join(HERE, "aafdiff.py"),
               os.path.join(ROOT, "Builds", BASE, "verify"), os.path.join(tdir, "verify"),
               "--hash"], "aafdiff")
    changed = []
    for line in r.splitlines():
        if not line.startswith("|") or "Bytes A" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        changed.append(cells[3].strip("`"))
    print(f"packed diff {len(changed)} inner file(s) vs {BASE}: {changed}")

    census = carlight_census(aaf_out)
    pl["build"].update({
        "aaf": rel(aaf_out), "ee_bytes": os.path.getsize(ee), "ee_sha256": sha256_file(ee),
        "toc_bytes": os.path.getsize(toc), "toc_sha256": sha256_file(toc),
        "toc_records": len(recs), "changed_inner_files": changed,
        "module": {k: info[k] for k in ("bytes", "sha256", "base_bytes", "delta_bytes")},
        "module_toc_record": {"name": mod_rec[0], "offset": mod_rec[1], "size": mod_rec[2]},
        "car_light_census": census,
        "installed": False,
    })
    os.makedirs(os.path.dirname(SPEC), exist_ok=True)
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pl, f, indent=1)

    receipt = {
        "schema": 1, "card": CARD, "tag": TAG,
        "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "base": f"Builds/{BASE}", "aaf": rel(aaf_out),
        "ee": {"bytes": os.path.getsize(ee), "sha256": sha256_file(ee)},
        "toc": {"bytes": os.path.getsize(toc), "sha256": sha256_file(toc), "records": len(recs)},
        "module": {"path": MODULE, "bytes": info["bytes"], "sha256": info["sha256"],
                   "base_bytes": info["base_bytes"], "delta_bytes": info["delta_bytes"],
                   "rows_before": pl["module"]["rows_before"],
                   "rows_after": len(pl["rows"]),
                   "toc_offset": mod_rec[1], "toc_size": mod_rec[2]},
        "modules_changed": changed,
        "edits": len(pl["rows"]), "dropped_rows": len(pl["dropped"]),
        "car_light_census": census,
        "blocked": [b["what"] for b in BLOCKED],
        "installed": False,
        "not_deployed": True,
    }
    with open(os.path.join(tdir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    with open(os.path.join(tdir, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# bm-RC4-lights installer - generated by bm_rc4_lights.py, never run.\n"
                f"# Install: copy {EE} and {EE}.toc into the game's dropzone path.\n"
                "param([string]$Action = 'Status')\nWrite-Host 'not run'\n")
    print(f"{TAG}: .ee {receipt['ee']['bytes']} B, .toc {receipt['toc']['bytes']} B / "
          f"{len(recs)} records, module record offset {mod_rec[1]} / {mod_rec[2]} B")
    return 0


# --------------------------------------------------------------------------- check
def check() -> int:
    fails: list[str] = []
    tdir = os.path.join(ROOT, "Builds", TAG)
    for p in (SPEC, os.path.join(tdir, "receipt.json"), module_in(TAG)):
        if not os.path.exists(p):
            print(f"FAIL: {rel(p)} missing (run --write)")
            return 1
    pl = plan()
    stored = json.load(open(SPEC, encoding="utf-8"))
    if json.dumps(stored["rows"], sort_keys=True) != json.dumps(pl["rows"], sort_keys=True):
        fails.append("the stored row plan differs from the re-derived one")

    tmp = os.path.join(WORK, "check")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    fresh = os.path.join(tmp, MODULE_NAME)
    info = L.encode(pl, fresh, tmp)
    built = open(module_in(TAG), "rb").read()
    if open(fresh, "rb").read() != built:
        fails.append("the built module differs from the re-derived plan")

    ee = os.path.join(tdir, EE)
    real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
    o = real[MODULE][0]
    packed = unaaf(open(ee, "rb").read())[o:o + real[MODULE][1]]
    if packed != built:
        fails.append("the module inside the packed .ee differs from the aaf's")
    recs = {n: (x, s) for n, x, s in read_toc(open(ee + ".toc", "rb").read())}
    off, size = recs.get(MODULE, (0, 0))
    if off == 0 or real.get(MODULE) != (off, size) or size != len(built):
        fails.append(f"the .toc record for the module is {off}/{size}, the .ee has "
                     f"{real.get(MODULE)}")
    unpacked = open(os.path.join(tdir, "verify", MODULE.replace("/", os.sep)), "rb").read()
    if unpacked != packed:
        fails.append("the unpacked verify/ copy differs from the module inside the .ee")

    rows = L.decode_module_bytes(packed)
    parts = decode_parts(os.path.join(tdir, "aaf", PARTS_MODULE.replace("/", os.sep)))
    for i, r in enumerate(rows):
        p = parts.get(int(r["part_index"]))
        if p is None or p["name"] != r["part"]:
            fails.append(f"row {i}: part {r['part']!r} does not match index {r['part_index']}")
            continue
        if int(p["has_lights"]) != 1:
            fails.append(f"row {i}: part {p['name']} has has_lights = {p['has_lights']}")
        for m, fn in (("part_hash", lambda: hj(r["part"])),
                      ("behavior_hash", lambda: hj(r["behavior"])),
                      ("deformable_transform_hash", lambda: hj(r["deformable_transform"]))):
            if int(r[m]) != fn():
                fails.append(f"row {i}: {m} mismatch")

    # the plans' numbers, re-read from the built module
    def rows_of(part: str, behavior: str, angle: float) -> list[dict]:
        return [r for r in rows if r["part"] == part and r["behavior"] == behavior
                and abs(float(r["angle"]) - angle) < 1e-6]

    for part, n in (("sportsmuscle_headlight_f_l", 1), ("sportsmuscle_headlight_f_r", 1)):
        if len(rows_of(part, "HeadLight", 70.0)) != 2:
            fails.append(f"{part}: expected the two 70-degree beam entries, found "
                         f"{len(rows_of(part, 'HeadLight', 70.0))}")
    reaches = sorted(float(r["range"]) for r in rows if r["part"].startswith("sportsmuscle_headlight")
                     and float(r["angle"]) == 70.0)
    if reaches != [18.0, 18.0, 60.0, 60.0]:
        fails.append(f"headlight reaches {reaches} != [18, 18, 60, 60]")
    if len([r for r in rows if r["behavior"] == "Reverse"]) != 2:
        fails.append("the reverse pair is not in the module")
    for r in rows:
        if r["behavior"] == "Reverse" and r["part"] not in ("sportsmuscle_tailstrip_r_l",
                                                           "sportsmuscle_tailstrip_r_r"):
            fails.append(f"reverse row on {r['part']}, not a tail strip")
    if len([r for r in rows if r["behavior"] == "None"]) != 4:
        fails.append("expected 4 behaviour-None rows (muzzle + forensics spot + 2 forensics heads)")
    if len(rows) != len(pl["rows"]):
        fails.append(f"{len(rows)} entries, planned {len(pl['rows'])}")

    # the domain ledger: the stored labels, the census they rest on, and the packed values
    dom = pl["domain"]
    if json.dumps(stored.get("domain"), sort_keys=True) != json.dumps(dom, sort_keys=True):
        fails.append("the stored domain ledger differs from the re-derived one")
    if dom["shipped_max"] != {"range": 50.0, "angle": 50.0}:
        fails.append(f"the fleet census's shipped max changed: {dom['shipped_max']} - "
                     f"re-check every out-of-domain label")
    for lab in dom["labels"]:
        if lab["kind"] == "out-of-domain" and lab["ships_in_fleet"]:
            fails.append(f"row {lab['index']} {lab['member']} {lab['v']} is labelled "
                         f"out-of-domain but ships {lab['ships_in_fleet']}x - relabel it")
        if lab["kind"] == "stand-in" and not lab["ships_in_fleet"]:
            fails.append(f"row {lab['index']} {lab['member']} {lab['v']} is labelled a stand-in "
                         f"but ships 0x - the fleet-mode claim is stale")
    tl17 = next((r for r in pl["rows"] if r["t18_rows"] == ["T-L17"]), None)
    if not tl17 or (tl17.get("claim") or {}).get("status") != "donor-carried":
        fails.append("row 11 (T-L17) is not marked donor-carried")
    for r in [x for x in pl["rows"] if x.get("claim")]:
        got = rows[r["index"]]
        if got["behavior"] != r["members"]["behavior"]["v"]:
            fails.append(f"row {r['index']}: the packed row is not the labelled one")
        for m, mk in r["claim"]["members"].items():
            a = float(got[m]) if m in FLOATS else got[m]
            if abs(float(a) - float(mk["v"])) > 1e-6:
                fails.append(f"row {r['index']} {m}: packed {a!r} != claimed label {mk['v']!r}")

    # R7-style: the only inner file that differs from the base tree is the lights module
    other = []
    for dirpath, _d, files in os.walk(aaf(BASE)):
        for n in files:
            p = os.path.join(dirpath, n)
            rp = os.path.relpath(p, aaf(BASE)).replace("\\", "/")
            if rp == MODULE:
                continue
            q = os.path.join(tdir, "aaf", rp.replace("/", os.sep))
            if not os.path.exists(q) or sha256_file(p) != sha256_file(q):
                other.append(rp)
    if other:
        fails.append(f"{len(other)} file(s) other than the lights module changed: {other[:5]}")

    census = carlight_census(os.path.join(tdir, "aaf"))
    missing = [k for k, v in census.items() if not v or v["car_light_blocks"] < 1]
    if missing:
        fails.append(f"lamp parts with no CarLight block: {missing}")

    kinds = {}
    for r in rows:
        kinds[r["behavior"]] = kinds.get(r["behavior"], 0) + 1
    print(f"rows   {len(rows)} ({len(pl['rows'])} planned)  behaviours {kinds}")
    print(f"parts  {len({r['part'] for r in rows})} distinct, all has_lights = 1: "
          f"{sorted({r['part'] for r in rows})}")
    print(f"module {info['bytes']} B {info['sha256'][:16]}..., .toc record {off}/{size}, "
          f".ee {os.path.getsize(ee)} B")
    print(f"flare  CarLight blocks per lamp part: {census}")
    statuses: dict[str, int] = {}
    for r in pl["rows"]:
        c = r.get("claim")
        if c:
            statuses[c["status"]] = statuses.get(c["status"], 0) + 1
    print(f"domain {sum(statuses.values())} marked rows {statuses}; fleet census {dom['entries']} "
          f"entries, shipped max range {dom['shipped_max']['range']} m / angle "
          f"{dom['shipped_max']['angle']} deg")
    print(f"R7     files other than the lights module changed: {len(other)}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print("PASS: every entry names a lit part, the plans' numbers are in the built module, and "
          "only the lights module differs from the base tree")
    print("CHECK_EXIT=0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    return write_build(plan()) if a.write else check()


if __name__ == "__main__":
    sys.exit(main())
