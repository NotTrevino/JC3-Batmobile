"""t23_closeout.py - T-23: the ledger close-out (gate TX) and the phase-B build batch list.

`GRAB_BACKLOG.md` §7 T-23 asks for four things and one gate:

  1. `t_rows.py check`, `status_audit.py --write` then `--check`   (run by the caller, reported here)
  2. confirm `rows assumed` = 0 except signed-off rows
  3. every G1 feature row assigned to a T row                        (`bmak_coverage.py`, T-23)
  4. the build batch list: which edit file goes into which build step

and gate **TX**: all checks green, every §1 feature code maps to >= 1 row, and D-1...D-10 are
answered or their rows are `blocked: D-n`.

This tool is the single writer of:

  `Working/Translation/BUILD_BATCHES.md`   the batch list, generated
  `Working/Translation/build_batches.json` the same record, for a machine

and it re-derives the three gate answers from the files that own them - `GRAB_BACKLOG.md` §1
(the 75 feature codes), §7/§8 (the T and B cards), §11 (the decision register) and
`Working/Translation/T_ROWS.jsonl` (the ledger).  Nothing is typed that a file can answer;
the only declared tables are the **glue** (which row carries a code, which step applies a
payload), and every entry in them is checked for existence, so a stale pointer fails the gate.

The `assumed` count comes from `status_audit.py` itself (`build()["t"]["total"]`), not from a
second implementation: two counters that disagree is how a status file starts lying.

Both outputs embed **live** dispositions: every number below is re-read from `T_ROWS.jsonl`, §1,
§7, §8 and §11 on each run.  A later edit to one of those files moves the numbers, so `--check`
fails until `--write` is re-run - that is the whole point of the byte comparison, and it means a
`done` card is not a frozen page.  `--check` therefore also runs the three sibling checks the
card's Done names (`t_rows.py check`, `status_audit.py --check`, `bmak_coverage.py --check`) and
fails on any non-zero exit, so "all checks green" is one command and not six claims.

Usage:
  python Tools/scripts/t23_closeout.py --write    # regenerate the two outputs
  python Tools/scripts/t23_closeout.py --check    # re-derive, compare, run the siblings, gate TX
  python Tools/scripts/t23_closeout.py --gate     # gate TX only (status lines, exit code)
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
OUT_MD = os.path.join(WORK, "BUILD_BATCHES.md")
OUT_JSON = os.path.join(WORK, "build_batches.json")

DOCS = {n: os.path.join(WORK, n) for n in (
    "T1_TRANSLATION.md", "T2_TRANSLATION.md", "T3_COVERAGE.md", "T6_HUD_CAMERA.md",
    "T7_WEAPONS.md", "T8_PARTS.md", "T9_INTERACTION.md", "T10_DAMAGE.md", "T11_MODES.md",
    "T12_AUDIO.md", "T13_FX.md", "T14_LIGHTS.md", "T15_WORLD.md")}

FAMILIES = ("APP", "DIM", "ARM", "WPN", "HDL", "MOD", "AUD", "ANI", "WLD", "LGT", "FX", "CAM",
            "HUD")
CODE_RE = re.compile(r"^\|\s*((?:%s)-\d+)\s*\|" % "|".join(FAMILIES))
CARD_RE = re.compile(r"^####\s+(T-\d+|B-\d+)\s+·\s+(.*?)\s{2,}(\S+)\s+·\s+deps:\s*(.*?)\s+·\s+serves:\s*(.*)$")
ROW_RE = re.compile(r"^\|\s*(T-[A-Z]{1,3}\d+|[APW]-\d\d)\s*\|")
DISPO_CARRIED = {"edit", "next", "keep", "epe", "re-read"}

# ---------------------------------------------------------------------------------------------
# The only declared table: which row (or document anchor) carries each §1 feature code.
# `--check` fails if the document is missing, the anchor is not in it, or the ledger row does
# not exist, so this cannot drift away from the tables.  An anchor that is a row id is looked
# up in the ledger when it is a ledger row; a document-only row (P-01, A-01, the T-9 tables)
# is reported as `documented` with its doc, never as carried.
# ---------------------------------------------------------------------------------------------
CODE_ROWS: dict[str, list[tuple[str, str, str]]] = {
    "APP-1": [("T2_TRANSLATION.md", "T-MA1", "19 material slots -> one CarPaintMM block per LOD"),
              ("T1_TRANSLATION.md", "T-G1", "body at the mesh-measured 7.026 x 3.495 x 2.271 m")],
    "APP-2": [("T2_TRANSLATION.md", "T-MA3", "authored base colour -> CarPaintMM diffuse"),
              ("T2_TRANSLATION.md", "T-MA4", "authored gloss, clamped to the vanilla cap")],
    "APP-3": [("T2_TRANSLATION.md", "T-MA5", "canopy -> Window block, empty slots as tint")],
    "APP-4": [("T14_LIGHTS.md", "T-L8", "head-lamp lens row"),
              ("T14_LIGHTS.md", "T-L13", "wheel-arch lamp (custom preset)"),
              ("T14_LIGHTS.md", "T-L24", "dashboard lamp"),
              ("T14_LIGHTS.md", "T-L35", "boot lamp")],
    "APP-5": [("T8_PARTS.md", "P-01", "turret part"), ("T8_PARTS.md", "P-03", "Vulcan part"),
              ("T8_PARTS.md", "P-07", "missile hatch part"), ("T8_PARTS.md", "P-09", "aero flap"),
              ("T1_TRANSLATION.md", "T-P1", "parts by bone name")],
    "APP-6": [("T11_MODES.md", "T-MD13", "transformation pose - named omission"),
              ("T11_MODES.md", "T-MD15", "one hybrid car carries the battle set")],
    "APP-7": [("T2_TRANSLATION.md", "T-DM6", "deform_scale 0 - the car never crumples")],
    "APP-8": [("T2_TRANSLATION.md", "T-MA7", "palette tints (the skin route)"),
              ("T15_WORLD.md", "T-WLD1", "D-5: a skin is an extra drop entry")],

    "DIM-1": [("T1_TRANSLATION.md", "T-G1", "body, wheelbase and track")],
    "DIM-2": [("T1_TRANSLATION.md", "T-G2", "tyre diameter (D-1 resolved: keep the PSKX)")],
    "DIM-3": [("T1_TRANSLATION.md", "T-M1", "mass, 6 t class")],
    "DIM-4": [("T1_TRANSLATION.md", "T-P3", "hull set from the 11 driveable boxes"),
              ("T2_TRANSLATION.md", "T-CO2", "the largest box fits one donor hull"),
              ("T2_TRANSLATION.md", "T-CO3", "per-part collision bindings")],

    "ARM-1": [("T3_COVERAGE.md", "T-DM9", "small arms do not move the bar")],
    "ARM-2": [("T10_DAMAGE.md", "T-DM1", "max_health 36000 for the BmAK 24-hit ratio"),
              ("T10_DAMAGE.md", "T-DM4", "explosion/smoke/burn thresholds")],
    "ARM-3": [("T3_COVERAGE.md", "T-DM8", "impact_damage_factor 0 - ramming never hurts it")],
    "ARM-4": [("T1_TRANSLATION.md", "T-P2", "per-part damage types"),
              ("T2_TRANSLATION.md", "T-DM5", "the 24-type join, wheels at the fleet ceiling")],
    "ARM-5": [("T10_DAMAGE.md", "ARM-5 — regeneration",
               "regen is a named omission: no recovery member on either side")],
    "ARM-6": [("T10_DAMAGE.md", "ARM-6 — death look", "death look is a named omission"),
              ("T13_FX.md", "T-FX21", "death explosion effect")],

    "WPN-1": [("T7_WEAPONS.md", "T-WP1", "heavy cannon -> w602 clone")],
    "WPN-2": [("T7_WEAPONS.md", "T-WP2", "Vulcan -> w603 clone on the second driver slot")],
    "WPN-3": [("T7_WEAPONS.md", "T-WP3", "missiles -> the donor's own w618")],
    "WPN-4": [("T7_WEAPONS.md", "T-WP4", "EMP missile - blocked on the disable behaviour")],
    "WPN-5": [("T7_WEAPONS.md", "T-WP5", "EMP burst - blocked on the firing moment")],
    "WPN-6": [("T7_WEAPONS.md", "T-WP6", "winch - named omission")],
    "WPN-7": [("T7_WEAPONS.md", "T-WP7", "allegiance switcher - named omission")],
    "WPN-8": [("T7_WEAPONS.md", "T-WP8", "sonar - named omission")],
    "WPN-9": [("T7_WEAPONS.md", "T-WP9", "vehicle tracker - named omission")],
    "WPN-10": [("T7_WEAPONS.md", "T-WP10", "riot suppressor - named omission under D-3")],
    "WPN-11": [("T7_WEAPONS.md", "T-WP11", "afterburner = JC3 nitro, live since test-091")],
    "WPN-12": [("T7_WEAPONS.md", "T-WP12", "weapon HUD API facts"),
               ("T6_HUD_CAMERA.md", "T-HUD5", "the HUD rows")],

    "HDL-1": [("T1_TRANSLATION.md", "T-E5", "top speed, signed-off wiki row")],
    "HDL-2": [("T1_TRANSLATION.md", "T-E1", "rpm band"), ("T1_TRANSLATION.md", "T-E3", "curve shape"),
              ("T1_TRANSLATION.md", "T-B1", "boost torque multiplier")],
    "HDL-3": [("T1_TRANSLATION.md", "T-ST1", "steer angle vs speed"),
              ("T1_TRANSLATION.md", "T-R1", "tyre friction"), ("T1_TRANSLATION.md", "T-K1", "brakes"),
              ("T1_TRANSLATION.md", "T-S3", "suspension stroke")],
    "HDL-4": [("T1_TRANSLATION.md", "T-B2", "nitro extra speed 43.2 km/h")],
    "HDL-5": [("T1_TRANSLATION.md", "T-S3", "0.70 m stroke, the BmAK travel")],
    "HDL-6": [("T3_COVERAGE.md", "T-AC1", "air control - closest system (drift torque + aero)"),
              ("T3_COVERAGE.md", "T-SR1", "self-righting - closest system (DriverLean + stabilizer)")],

    "MOD-1": [("T11_MODES.md", "T-MD1", "afterburner"), ("T11_MODES.md", "T-MD2", "Immobilizer"),
              ("T11_MODES.md", "T-MD3", "ram immunity")],
    "MOD-2": [("T11_MODES.md", "T-MD9", "turret/cannon aim"), ("T11_MODES.md", "T-MD10", "armour"),
              ("T11_MODES.md", "T-MD11", "battle camera FOV inside the delivered band"),
              ("T11_MODES.md", "T-MD12", "battle lamps ride HeadLight")],
    "MOD-3": [("T9_INTERACTION.md", "exit.driver.moving.parachute", "the moving exit T-13 places"),
              ("T15_WORLD.md", "T-WLD9", "the 26 exit objects")],
    "MOD-4": [("T8_PARTS.md", "P-06", "canopy hinge"), ("T2_TRANSLATION.md", "T-PA5", "door_parts map")],
    "MOD-5": [("T15_WORLD.md", "T-WLD19", "the donor's traffic record is left alone"),
              ("T9_INTERACTION.md", "hijack objects", "D-9: the 6 hijack objects are dropped")],

    "AUD-1": [("T12_AUDIO.md", "A-01", "engine start/idle/rev into LandAudio's window")],
    "AUD-2": [("T12_AUDIO.md", "A-02", "nitro sample swap, live since test-060")],
    "AUD-3": [("T12_AUDIO.md", "A-11", "interior layer - named omission")],
    "AUD-4": [("T12_AUDIO.md", "W-08", "battle-mode events - blocked (D-2 hybrid)")],
    "AUD-5": [("T12_AUDIO.md", "W-01", "cannon"), ("T12_AUDIO.md", "W-03", "Vulcan"),
              ("T12_AUDIO.md", "W-07", "lock-on UI")],
    "AUD-6": [("T12_AUDIO.md", "A-09", "tyre/impact layer - named omission")],
    "AUD-7": [("T12_AUDIO.md", "A-13", "horn removed")],

    "ANI-1": [("T2_TRANSLATION.md", "T-PA4", "wheel_parts slots, spin/steer/suspension"),
              ("T8_PARTS.md", "P-05", "turbine")],
    "ANI-2": [("T8_PARTS.md", "P-01", "turret yaw"), ("T8_PARTS.md", "P-02", "cannon pitch")],
    "ANI-3": [("T8_PARTS.md", "P-03", "Vulcan barrels through GatlingGun")],
    "ANI-4": [("T8_PARTS.md", "P-05", "turbine fan through EngineRotatingPart")],
    "ANI-5": [("T8_PARTS.md", "P-09", "air-brake flaps (family P-09...P-12)")],
    "ANI-6": [("T8_PARTS.md", "P-07", "left missile hatch"), ("T8_PARTS.md", "P-08", "right missile hatch")],
    "ANI-7": [("T8_PARTS.md", "P-13", "steering yoke - static, no bone")],
    "ANI-8": [("T8_PARTS.md", "P-06", "canopy on entry (MOD-4)")],
    "ANI-9": [("T9_INTERACTION.md", "interaction.seat.driver", "Driver socket / seat transform")],

    "WLD-1": [("T15_WORLD.md", "T-WLD1", "the Rebel Drop item"), ("T15_WORLD.md", "T-WLD2", "the unlock link"),
              ("T15_WORLD.md", "T-WLD3", "the item field class")],
    "WLD-2": [("T15_WORLD.md", "T-WLD4", "name pair - blocked"), ("T15_WORLD.md", "T-WLD5", "icon"),
              ("T15_WORLD.md", "T-WLD6", "blurb - blocked"), ("T15_WORLD.md", "T-WLD7", "category caption")],
    "WLD-3": [("T15_WORLD.md", "T-WLD8", "entry points on the real sides"),
              ("T15_WORLD.md", "T-WLD9", "exit points")],
    "WLD-4": [("T15_WORLD.md", "T-WLD10", "stunt points on the roof"),
              ("T15_WORLD.md", "T-WLD11", "the 3 stunt areas - blocked")],
    "WLD-5": [("T15_WORLD.md", "T-WLD12", "mass 6000")],
    "WLD-6": [("T15_WORLD.md", "T-WLD13", "the donor sinks (D-8)"),
              ("T15_WORLD.md", "T-WLD14", "water kill/stall constants")],
    "WLD-7": [("T15_WORLD.md", "T-WLD15", "no vehicle-side tether member"),
              ("T15_WORLD.md", "T-WLD16", "cargo bay share"), ("T15_WORLD.md", "T-WLD17", "no airlift")],
    "WLD-8": [("T15_WORLD.md", "T-WLD18", "spawn table untouched"),
              ("T15_WORLD.md", "T-WLD19", "traffic record untouched")],

    "LGT-1": [("T14_LIGHTS.md", "T-L8", "head lamp"), ("T14_LIGHTS.md", "T-L15", "brake lamp"),
              ("T14_LIGHTS.md", "T-L13", "wheel-arch lamp"), ("T14_LIGHTS.md", "T-L24", "dashboard"),
              ("T14_LIGHTS.md", "T-L35", "boot")],
    "LGT-2": [("T14_LIGHTS.md", "T-L17", "battle spot"), ("T14_LIGHTS.md", "T-L18", "battle head L"),
              ("T14_LIGHTS.md", "T-L19", "battle head R"), ("T14_LIGHTS.md", "T-L20", "battle arch")],

    "FX-1": [("T13_FX.md", "T-FX7", "afterburner flame"), ("T13_FX.md", "T-FX8", "always-on exhaust"),
             ("T13_FX.md", "T-FX9", "heat haze - out")],
    "FX-2": [("T13_FX.md", "T-FX10", "cannon muzzle flash"), ("T13_FX.md", "T-FX11", "Vulcan flash"),
             ("T13_FX.md", "T-FX14", "missile trail"), ("T13_FX.md", "T-FX15", "cannon impact")],
    "FX-3": [("T13_FX.md", "T-FX17", "tyre kick-up"), ("T13_FX.md", "T-FX18", "slide dust"),
             ("T13_FX.md", "T-FX19", "wall-scrape sparks")],
    "FX-4": [("T13_FX.md", "T-FX21", "death explosion"), ("T13_FX.md", "T-FX22", "burn states"),
             ("T13_FX.md", "T-FX23", "engine smoke")],

    "CAM-1": [("T6_HUD_CAMERA.md", "T-CAM5", "the chase composition"),
              ("T6_HUD_CAMERA.md", "T-CAM2", "FOV 85/95 horizontal -> 54.5/63.1"),
              ("T6_HUD_CAMERA.md", "T-CAM12", "the 400 cm spring boom")],
    "CAM-2": [("T6_HUD_CAMERA.md", "T-CAM10", "battle FOV 60 - inside the band"),
              ("T11_MODES.md", "T-MD11", "the value needs no change, only a mode switch")],

    "HUD-1": [("T6_HUD_CAMERA.md", "T-HUD1", "speed"), ("T6_HUD_CAMERA.md", "T-HUD2", "nitro meter"),
              ("T6_HUD_CAMERA.md", "T-HUD3", "health bar")],
    "HUD-2": [("T6_HUD_CAMERA.md", "T-HUD5", "weapon slots/reticle, completed by T-19"),
              ("T6_HUD_CAMERA.md", "T-HUD11", "weapon slots"), ("T6_HUD_CAMERA.md", "T-HUD14", "reticle"),
              ("T6_HUD_CAMERA.md", "T-HUD18", "missile lock")],
}

# ---------------------------------------------------------------------------------------------
# The build batch list (card step 4).  `BATCH_PAYLOADS` is the glue between an edit file on disk
# and the phase-B card that applies it; `BATCH_KIND` says whether a file is a build payload or a
# record the build does not consume.
# ---------------------------------------------------------------------------------------------
BATCH_PAYLOADS: dict[str, list[str]] = {
    "T8_PARTS.json": ["B-02", "B-04"],
    "appearance_plan.json": ["B-02", "B-03"],
    "t14_lights.json": ["B-03", "B-04", "B-05", "B-07"],
    "t16_collision.json": ["B-10"],
    "t7_weapons_edits.json": ["B-05", "B-06"],
    "t9_interaction.json": ["B-05"],
    "t10_damage_edits.json": ["B-05", "B-09"],
    "t17_fx.json": ["B-08"],
    "t12_audio_map.json": ["B-11"],
    "t11_variants.json": ["B-12"],
    "t15_world.json": ["B-13"],
    "t19_hud.json": [],
    "t1_handling.json": ["B-24"],
    "t14_lights_keepaudit.json": ["B-07"],
    "t12_audio_keepaudit.json": ["B-11"],
    "t10_damage_keepaudit.json": ["B-09"],
    "t16_collision_keepaudit.json": ["B-10"],
}
BATCH_KIND = {
    "T8_PARTS.json": "payload",
    "appearance_plan.json": "payload",
    "t14_lights.json": "payload",
    "t16_collision.json": "payload",
    "t7_weapons_edits.json": "payload",
    "t9_interaction.json": "payload",
    "t10_damage_edits.json": "payload",
    "t17_fx.json": "payload",
    "t12_audio_map.json": "payload",
    "t11_variants.json": "payload",
    "t15_world.json": "payload",
    "t19_hud.json": "payload",
    "t1_handling.json": "payload",
    "t14_lights_keepaudit.json": "payload",
    "t12_audio_keepaudit.json": "payload",
    "t10_damage_keepaudit.json": "payload",
    "t16_collision_keepaudit.json": "payload",
    "T10_OPEN_ROWS.json": "record",
    "damage_switches.json": "record",
    # T-22 / B-10 plan: the reopened collision shape edits are a plan until B-10 applies them.
    "t22_shape_edits.json": "record",
}
# files the card text names as the step's own gate, not part of the payload count
NO_PAYLOAD_STEPS = {
    "B-01": "scaffold: copies test-091 and applies no new value (identity control)",
    "B-14": "release candidate: receipts and installer only",
    # cards opened after this sheet was written: each names its own build gate and has no edit file
    # yet, so there is nothing for the payload table to point at.
    # §8 cards B-17...B-20 were also written before the payload table: each is a build gate whose
    # module does not exist yet, and each names the ledger row it will close when it runs.
    "B-17": "effect writer: the private `.effc` copies and FX-1…4 are written by the writer run (T-FX1/T-FX2)",
    "B-18": "EMP disable: the immobiliser + burst write is the card's own gate; T-WP15 has no value until it runs",
    "B-19": "drone hacker: the allegiance-flip rows are blocked on the T-11 module, per card B-19",
    "B-20": "sonar pulse: the pulse/reveal rows are written by the card's own step, per card B-20",
    "B-21": "vehicle tracker: the weapon entity + POI graph are the card's own output (T-WP9)",
    "B-22": "droop and up-travel: one `max_length_offset` write in a private copy, per card B-22",
    "B-23": "per-mode rate: no suspension edit exists while B-12 is unbuilt (card B-23)",
    "B-25": "lens flares and light units: part-side emitters + one probe build, per card B-25",
    "B-26": "per-entity audio override: private bank + binding rows + two takes, per card B-26",
}
BASE_APPLIED = ("t5_applied.json", "t5b_applied.json", "t5c_applied.json", "t5d_applied.json",
                "t5e_applied.json")


def rd(path: str) -> str:
    return open(path, encoding="utf-8").read()


SIBLING_CHECKS = (
    ("t_rows.py check", ("t_rows.py", "check")),
    ("status_audit.py --check", ("status_audit.py", "--check")),
    ("bmak_coverage.py --check", ("bmak_coverage.py", "--check")),
)


def sibling_checks() -> list[dict]:
    """The other checks the card's Done names, run here so gate TX is one command."""
    out = []
    for label, argv in SIBLING_CHECKS:
        cmd = [sys.executable, os.path.join(HERE, argv[0]), *argv[1:]]
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        lines = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()]
        out.append({"check": label, "exit": p.returncode, "last": lines[-1] if lines else ""})
    return out


def ledger() -> list[dict]:
    rows = [json.loads(l) for l in rd(LEDGER).splitlines() if l.strip()]
    return rows


def ledger_index(rows: list[dict]) -> dict[str, dict]:
    return {r["id"]: r for r in rows}


def parse_codes(text: str) -> list[tuple[str, str, str]]:
    """§1 -> [(code, requirement, lore source)] in file order."""
    out, in_s1 = [], False
    for line in text.splitlines():
        if line.startswith("## 1. "):
            in_s1 = True
            continue
        if in_s1 and line.startswith("## 2. "):
            break
        if not in_s1:
            continue
        m = CODE_RE.match(line)
        if m:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append((m.group(1), cells[1] if len(cells) > 1 else "",
                        cells[2] if len(cells) > 2 else ""))
    return out


def parse_cards(text: str, section: str) -> list[dict]:
    """The `#### ID · title size · deps · serves` cards of §7 (`T`) or §8 (`B`)."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(section))
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("## ") and i > start), len(lines))
    cards, cur = [], None
    for line in lines[start:end]:
        m = CARD_RE.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip(), "size": m.group(3),
                   "deps": m.group(4).strip(), "serves": m.group(5).strip(), "body": []}
            cards.append(cur)
        elif cur is not None:
            cur["body"].append(line)
    for c in cards:
        body = c.pop("body")
        c["out"] = ""
        c["done"] = ""
        key = None
        for line in body:
            s = line.strip()
            low = s.lower()
            if low.startswith(("in:", "do:", "out:", "done", "review input:", "stop:")):
                key = "out" if low.startswith("out:") else ("done" if low.startswith("done") else None)
                text = s.split(":", 1)[-1].strip() if ":" in s else s
                if key == "out":
                    c["out"] = text
                elif key == "done":
                    c["done"] = text
                continue
            if s.startswith("#") or s.startswith("---"):
                key = None
                continue
            if key and s:
                c[key] = (c[key] + " " + s).strip()
        c["cards_served"] = expand_serves(c["serves"])
    return cards


def expand_serves(text):
    """`WPN-1...12`, `LGT-1/2`, `APP-5/6` -> the codes they mean.  `all` and a bare family
    (`ANI`) name no code, so they cannot satisfy the gate by accident."""
    out = []
    for raw in re.split(r"[,;]", text):
        tok = raw.strip().strip("`")
        if not tok or tok == "all":
            continue
        m = re.match(r"([A-Z]{2,4})-(\d+)(?:…|\.\.\.)(\d+)$", tok)
        if m:
            fam, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            out += [fam + "-" + str(i) for i in range(a, b + 1)]
            continue
        m = re.match(r"([A-Z]{2,4})-(\d+)(?:/(\d+))+$", tok)
        if m:
            fam, first = m.group(1), int(m.group(2))
            rest = [int(x) for x in re.findall(r"/(\d+)", tok)]
            out += [fam + "-" + str(i) for i in [first] + rest]
            continue
        if re.fullmatch(r"[A-Z]{2,4}-\d+", tok):
            out.append(tok)
    return sorted(set(out))


def parse_decisions(text: str) -> list[dict]:
    out, in_s11 = [], False
    for line in text.splitlines():
        if line.startswith("## 11. "):
            in_s11 = True
            continue
        if in_s11 and line.startswith("## 12. "):
            break
        if not in_s11 or not line.startswith("| D-"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = re.match(r"D-(\d+)", cells[0])
        if not m:
            continue
        resolved = re.search(r"resolved\s+(\d{4}-\d{2}-\d{2})", cells[3])
        out.append({"id": "D-" + m.group(1), "question": cells[1], "data": cells[2],
                    "answer": cells[3], "blocks": cells[4] if len(cells) > 4 else "",
                    "resolved": resolved.group(1) if resolved else None})
    return out


def doc_row_state(doc: str, anchor: str, index: dict[str, dict]) -> dict:
    """What the file says about one anchor.

    A ledger row answers with its disposition.  A row that lives in a phase-T document but not
    in the ledger (`P-01`, `A-01`, the T-9 tables) is read from its own line: the disposition
    words the row prints decide, so a `blocked` or a named omission is never reported as
    carried just because the row exists.
    """
    if anchor in index:
        return {"anchor": anchor, "doc": doc, "state": index[anchor]["dispo"], "source": "ledger"}
    lines = rd(DOCS[doc]).splitlines()
    line, at = "", -1
    for i, l in enumerate(lines):
        if anchor in l:
            line, at = l, i
            break
    if line.lstrip().startswith("#") and at >= 0:
        # a section anchor: the heading plus the first paragraph of its body
        line = " ".join(lines[at:at + 8])
    low = line.lower()
    if "named omission" in low:
        state = "named omission"
    elif "blocked" in low:
        state = "blocked"
    elif "**out**" in low or "| out |" in low:
        state = "out"
    elif any(k in low for k in ("`next`", "`keep`", "`mapped`", "`epe`", "`edit`",
                                "kept vanilla", "`remove`")):
        state = "carried (document row)"
    else:
        state = "documented"
    return {"anchor": anchor, "doc": doc, "state": state, "source": "doc"}


def feature_gate(codes, index, problems) -> dict:
    out = {}
    for code, requirement, source in codes:
        anchors = CODE_ROWS.get(code)
        if not anchors:
            problems.append(f"{code}: no row mapped (§1 feature code with no CODE_ROWS entry)")
            out[code] = {"requirement": requirement, "rows": [], "state": "unmapped"}
            continue
        found = []
        for doc, anchor, note in anchors:
            path = DOCS.get(doc)
            if not path or not os.path.exists(path):
                problems.append(f"{code}: {doc} does not exist")
                continue
            if anchor not in rd(path):
                problems.append(f"{code}: {doc} has no `{anchor}`")
                continue
            found.append({**doc_row_state(doc, anchor, index), "note": note})
        states = {f["state"] for f in found}
        if not found:
            # every declared anchor is missing (each one already a problem above): no row at all
            state = "unmapped"
        elif states & (DISPO_CARRIED | {"carried (document row)"}):
            state = "carried"
        elif "blocked" in states:
            state = "blocked"
        elif states <= {"out", "named omission"}:
            state = "named omission"
        elif states == {"documented"}:
            # the row exists but states no disposition, so it carries no behaviour (R4/R5):
            # reporting it as `carried` is exactly what the old carried set did, and it lied.
            state = "documented"
        else:
            state = "unknown"
            problems.append(f"{code}: rows exist but none of them states a disposition (R4)")
        out[code] = {"requirement": requirement, "source": source, "rows": found, "state": state,
                     "cards": []}
    stale = sorted(set(CODE_ROWS) - {c[0] for c in codes})
    for code in stale:
        problems.append(f"{code}: CODE_ROWS names a code §1 does not have")
    return out


def code_key(code: str) -> tuple[str, int]:
    fam, num = code.split("-")
    return fam, int(num)


def doc_stats(features: dict) -> dict:
    """How much of the map rests on a document row that is not a ledger row (the review's §3/§4).

    `anchors` counts distinct (document, anchor) pairs; `by_state` is how many of them state what.
    The three code counts say how far the document rows reach into the map, so the MODLOG no longer
    has to type them (R11)."""
    seen: dict[tuple[str, str], set[str]] = {}
    for v in features.values():
        for r in v["rows"]:
            if r["source"] == "doc":
                seen.setdefault((r["doc"], r["anchor"]), set()).add(r["state"])
    by_state = collections.Counter(next(iter(s)) if len(s) == 1 else "mixed" for s in seen.values())
    carried = [c for c, v in features.items() if v["state"] == "carried"]
    return {"anchors": len(seen), "by_state": dict(sorted(by_state.items())),
            "carried_total": len(carried),
            "carried_codes_with_doc_anchor": sum(
                1 for c in carried if any(r["source"] == "doc" for r in features[c]["rows"])),
            "codes_with_doc_anchor": sum(
                1 for v in features.values() if any(r["source"] == "doc" for r in v["rows"]))}


def assumed_gate(problems) -> dict:
    """The `assumed` count as `status_audit.py` counts it - one implementation, not two."""
    sys.path.insert(0, HERE)
    import status_audit  # noqa: E402
    d = status_audit.build()
    total = d["t"]["total"]
    rows = ledger()
    assumed_rows = []
    for r in rows:
        conf = r["cells"][6] if len(r["cells"]) > 6 else r["cells"][4]
        if status_audit.row_kind(conf) == "assumed":
            assumed_rows.append({"id": r["id"], "conf": conf, "why": r["why"],
                                 "signed_off": "signed off" in " ".join(r["cells"]).lower()})
    unsigned = [a["id"] for a in assumed_rows if not a["signed_off"]]
    if unsigned:
        problems.append(f"assumed rows without a sign-off: {', '.join(unsigned)}")
    return {"count": total["assumed"], "in_scope": d["t"]["in_scope"],
            "rows": assumed_rows, "unsigned": unsigned,
            "evidenced": total["evidenced"], "blocked": total["blocked"], "out": total["out"],
            "superseded": total["superseded"], "rows_total": total["rows"],
            "next": d["t"]["next_rows"]}


def decision_gate(decisions, index, problems) -> list[dict]:
    out = []
    for dec in decisions:
        cited = sorted({r["id"] for r in index.values()
                        if dec["id"] in " ".join(r.get("cells", [])) + " " + r.get("why", "")})
        blocked = sorted({r["id"] for r in index.values()
                          if re.search(r"blocked:\s*%s\b" % re.escape(dec["id"]),
                                       " ".join(r.get("cells", [])) + " " + r.get("why", ""))})
        state = "answered" if dec["resolved"] else ("blocked rows" if blocked else "UNANSWERED")
        if not dec["resolved"] and not blocked:
            problems.append(f"{dec['id']}: not resolved in §11 and no row says `blocked: {dec['id']}`")
        out.append({**dec, "state": state, "cited_rows": cited, "blocked_rows": blocked})
    if len(decisions) != 11:
        problems.append(f"§11 has {len(decisions)} decisions, expected D-1...D-11")
    return out


# where an edit file may sit: the translation work dirs, plus Working/Prep for the collision plan
# record of T-22 (Working/Prep/t22_shape_edits.json).
def PATCH_DIRS(name: str) -> tuple[str, ...]:
    return (os.path.join(WORK, name),
            os.path.join(ROOT, "Working", "Appearance", name),
            os.path.join(ROOT, "Working", "Prep", name))


def payload_rows(path: str) -> tuple[int, int]:
    """(rows, values) of an edit file, read from its own record."""
    d = json.load(open(path, encoding="utf-8"))
    for key in ("rows", "edits", "objects", "components", "parts", "variants", "switches"):
        v = d.get(key)
        if isinstance(v, (list, dict)):
            return len(v), len(v)
    return 0, 0


def discover_payloads(problems) -> dict:
    """Every `Working/**/*.json` whose own `card` field is a T card must be in the batch list."""
    found = {}
    for base, dirs, files in os.walk(os.path.join(ROOT, "Working")):
        dirs[:] = [x for x in dirs if x not in ("__pycache__",)]
        for name in files:
            if not name.endswith(".json"):
                continue
            path = os.path.join(base, name)
            if os.path.abspath(path) == os.path.abspath(OUT_JSON):
                continue  # this tool's own output, not a payload
            try:
                d = json.load(open(path, encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(d, dict) and re.match(r"T-\d+", str(d.get("card", ""))):
                found[name] = path
    for name, path in found.items():
        if name not in BATCH_KIND:
            problems.append(f"{name}: produced by {json.load(open(path, encoding='utf-8'))['card']}"
                            f" but not named in BATCH_PAYLOADS/BATCH_KIND")
    return found


def batch_gate(cards_b, problems) -> dict:
    known_b = {c["id"] for c in cards_b}
    payloads = {}
    for name, steps in BATCH_PAYLOADS.items():
        path = None
        for cand in PATCH_DIRS(name):
            if os.path.exists(cand):
                path = cand
                break
        if not path:
            problems.append(f"{name}: named in the batch list but not on disk")
            continue
        rows, values = payload_rows(path)
        for step in steps:
            if step not in known_b:
                problems.append(f"{name}: assigned to {step}, which §8 does not have")
        payloads[name] = {"path": os.path.relpath(path, ROOT).replace("\\", "/"),
                          "kind": BATCH_KIND.get(name, "payload"), "steps": steps,
                          "rows": rows, "values": values}
    for name, kind in BATCH_KIND.items():
        if kind != "record" or name in payloads:
            continue
        path = None
        for cand in PATCH_DIRS(name):
            if os.path.exists(cand):
                path = cand
                break
        if not path:
            problems.append(f"{name}: named as a record but not on disk")
            continue
        rows, values = payload_rows(path)
        rel = os.path.relpath(path, ROOT).split(os.sep)
        payloads[name] = {"path": "/".join(rel), "kind": kind, "steps": [],
                          "rows": rows, "values": values}
    used = {s for v in BATCH_PAYLOADS.values() for s in v}
    for c in cards_b:
        if c["id"] not in used and c["id"] not in NO_PAYLOAD_STEPS:
            problems.append(f"{c['id']}: no payload and not declared as a no-payload step")
    for step in NO_PAYLOAD_STEPS:
        if step not in known_b:
            problems.append(f"{step}: declared a no-payload step but §8 does not have it")
    base = []
    for name in BASE_APPLIED:
        path = os.path.join(WORK, name)
        if not os.path.exists(path):
            continue
        applied = json.load(open(path, encoding="utf-8")).get("applied", [])
        tag = "-"
        if applied and applied[0].get("file"):
            m = re.search(r"Builds[\\/](test-\d+)", applied[0]["file"])
            if m:
                tag = m.group(1)
        base.append({"file": name, "values": len(applied),
                     "rows": len({e.get("row") for e in applied if e.get("row")}), "build": tag})
    return {"payloads": payloads, "base": base, "no_payload_steps": NO_PAYLOAD_STEPS}


def gate() -> tuple[dict, list[str]]:
    problems: list[str] = []
    text = rd(BACKLOG)
    codes = parse_codes(text)
    cards_t = parse_cards(text, "## 7. ")
    cards_b = parse_cards(text, "## 8. ")
    decisions = parse_decisions(text)
    rows = ledger()
    index = ledger_index(rows)

    features = feature_gate(codes, index, problems)
    served: dict[str, list[str]] = collections.defaultdict(list)
    for c in cards_t:
        for code in c["cards_served"]:
            if code in features:
                served[code].append(c["id"])
    for code, entry in features.items():
        entry["cards"] = sorted(set(served.get(code, [])))

    assumed = assumed_gate(problems)
    decs = decision_gate(decisions, index, problems)
    discover_payloads(problems)
    batch = batch_gate(cards_b, problems)

    if len(codes) != 75:
        problems.append(f"§1 has {len(codes)} feature codes, expected 75")
    t23 = next((c for c in cards_t if c["id"] == "T-23"), None)
    if not t23:
        problems.append("T-23 is not a card in §7")

    dispo = collections.Counter(r["dispo"] for r in rows)
    states = collections.Counter(v["state"] for v in features.values())
    d = {"card": "T-23", "schema": 2, "generated_by": "Tools/scripts/t23_closeout.py",
         "sources": {"backlog": "GRAB_BACKLOG.md §1/§7/§8/§11", "ledger": "T_ROWS.jsonl",
                     "assumed": "status_audit.py"},
         "gate": {
             "codes": len(codes),
             "codes_carried": states.get("carried", 0),
             "codes_omitted": states.get("named omission", 0),
             "codes_blocked": states.get("blocked", 0),
             "codes_documented": states.get("documented", 0),
             "codes_unknown": states.get("unknown", 0),
             "codes_unmapped": states.get("unmapped", 0),
             "blocked_codes": sorted((c for c, v in features.items() if v["state"] == "blocked"),
                                     key=code_key),
             "documented_codes": sorted((c for c, v in features.items()
                                         if v["state"] == "documented"), key=code_key),
             "doc_rows": doc_stats(features),
             "rows": len(rows), "dispositions": dict(sorted(dispo.items())),
             "assumed": assumed, "decisions": decs,
             "problems": problems},
         "features": features,
         "batches": {**batch, "steps": [
             {"id": c["id"], "title": c["title"], "size": c["size"], "deps": c["deps"],
              "serves": c["serves"], "out": c["out"], "done": c["done"]} for c in cards_b]},
         "t_cards": [{"id": c["id"], "title": c["title"], "out": c["out"]} for c in cards_t]}
    return d, problems


# --------------------------------------------------------------------------------------------- render
def render_json(d: dict) -> str:
    return json.dumps(d, indent=1, ensure_ascii=False) + "\n"


def render_md(d: dict) -> str:
    g = d["gate"]
    a = g["assumed"]
    L = ["# Build batches and the phase-T close-out (T-23)", "",
         "Generated by `Tools/scripts/t23_closeout.py`; `--check` re-derives this file byte for",
         "byte and runs gate TX. Every number below is read from a file named beside it: the",
         "feature codes from `GRAB_BACKLOG.md` §1, the dispositions from",
         "`Working/Translation/T_ROWS.jsonl`, the `assumed` count from `status_audit.py` itself,",
         "the row and value counts from each edit file's own record.", "",
         "**Every disposition on this page is live.** The states, the blocked/documented lists and",
         "the ledger counts are re-read from §1, §7, §8, §11 and `T_ROWS.jsonl` on each run, so any",
         "later edit to one of those files moves them: `--check` then fails until",
         "`python Tools/scripts/t23_closeout.py --write` is re-run. This page is not frozen by the",
         "card being `done`, and it is not the gate - the command is.", "",
         "## 1. Gate TX", "",
         "| check | result | source |", "|---|---|---|",
         f"| §1 feature codes | **{g['codes']}** codes, "
         f"{g['codes_carried']} carried, {g['codes_omitted']} named omission, "
         f"{g['codes_blocked']} blocked, {g['codes_documented']} documented (no disposition), "
         f"{g['codes_unknown']} unknown, {g['codes_unmapped']} unmapped | §1 + §2 of this file |",
         f"| every code maps to a row | {'PASS' if g['codes_unmapped'] == 0 else 'FAIL'} | table 2 |",
         f"| blocked codes | {', '.join(g['blocked_codes']) or 'none'} | table 2 |",
         f"| documented codes (a row exists, it states no disposition) | "
         f"{', '.join(g['documented_codes']) or 'none'} | table 2 |",
         f"| document rows | {g['doc_rows']['anchors']} distinct anchors - "
         + ", ".join(f"{v} {k}" for k, v in g["doc_rows"]["by_state"].items())
         + f"; {g['doc_rows']['carried_codes_with_doc_anchor']} of the "
         f"{g['doc_rows']['carried_total']} carried codes take one, "
         f"{g['doc_rows']['codes_with_doc_anchor']} codes touch one | table 2 |",
         f"| ledger rows | {g['rows']} = "
         + ", ".join(f"{k} {v}" for k, v in d["gate"]["dispositions"].items()) + " | `T_ROWS.jsonl` |",
         f"| rows assumed | **{a['count']}** of {a['in_scope']} in scope, "
         f"{len(a['rows'])} row(s): "
         + (", ".join(f"`{r['id']}`" for r in a["rows"]) or "none")
         + f", unsigned {len(a['unsigned'])} | `status_audit.py` |",
         f"| decisions D-1...D-10 | "
         + ", ".join(f"{x['id']} {x['state']}" for x in g["decisions"]) + " | §11 |",
         f"| problems | {len(g['problems'])} | this file, last line |", ""]

    L += ["## 2. §1 feature code -> rows", "",
          "One line per §1 code: the T rows (or the document anchor) that carry it, read from the",
          "documents that own them. `state` is the ledger's disposition where the row is a ledger",
          "row; a row that lives in a phase-T document but not in the ledger is `documented` - the",
          "row exists and is checked for, it is simply outside the ledger's 198. A document row that",
          "states no disposition does not carry its code (R4: no value without provenance, R5:",
          "behaviour before member), so a code whose rows all read `documented` is listed as",
          "`documented` in §1 rather than counted as carried.", "",
          "| code | state | rows | cards that serve it |", "|---|---|---|---|"]
    for code in sorted(d["features"], key=lambda c: (c.split("-")[0], int(c.split("-")[1]))):
        f = d["features"][code]
        rows = "; ".join(f"`{r['anchor']}` ({r['state']})" for r in f["rows"])
        cards = ", ".join(f["cards"]) or "-"
        L.append(f"| {code} | {f['state']} | {rows} | {cards} |")
    L += ["", "## 3. What the base tree already carries", "",
          "`Builds/test-091` is the phase-B base. These values are already applied and read back; a",
          "B step copies them, it does not re-apply them.", "",
          "| applied record | build | values | rows |", "|---|---|---:|---:|"]
    for b in d["batches"]["base"]:
        L.append(f"| `{b['file']}` | {b['build']} | {b['values']} | {b['rows']} |")
    L += ["", "## 4. Phase-B steps: which edit file goes into which step", "",
          "One B card = one build step = one `aafdiff` whose changed-file list is exactly what the",
          "card names (`GRAB_BACKLOG.md` §8). The payload column is the edit file the step applies;",
          "the rows and values are read from that file's own record. The decisions column names the",
          "§11 decision(s) whose `blocks` cell names the step, so a resolved decision that changed",
          "a card's design is visible at the step that carries it.", "",
          "| step | build | payload (rows / values) | decisions | gate |",
          "|---|---|---|---|---|"]
    step_of = collections.defaultdict(list)
    for name, p in d["batches"]["payloads"].items():
        for step in p["steps"]:
            step_of[step].append(f"`{name}` ({p['rows']} / {p['values']})")
    for c in d["batches"]["steps"]:
        num = int(c["id"].split("-")[1])
        build = f"`Builds/bm-{num:03d}/`"
        payload = ", ".join(sorted(step_of.get(c["id"], [])))
        if not payload:
            payload = "- " + d["batches"]["no_payload_steps"].get(c["id"], "NOTHING ASSIGNED")
        decs = [x["id"] + (" (resolved)" if x["resolved"] else " (open)")
                for x in d["gate"]["decisions"]
                if re.search(r"\b%s\b" % re.escape(c["id"]), x["blocks"])]
        L.append(f"| {c['id']} · {c['title']} | {build} | {payload} | "
                 f"{', '.join(decs) or '-'} | {c['done']} |")
    L += ["", "### Steps in card order, with dependencies", "",
          "| step | size | deps | serves | out |", "|---|---|---|---|---|"]
    for c in d["batches"]["steps"]:
        L.append(f"| {c['id']} | {c['size']} | {c['deps']} | {c['serves']} | {c['out'] or '-'} |")
    no_payload = d["batches"].get("no_payload_steps") or {}
    L += ["", "### Every phase-B step and the edits it consumes", "",
          "One line per §8 step: the edit files it applies (`rows` each, `values` summed), or the",
          "declared reason it applies none. Every file on disk appears at least once here unless",
          "no step names it, and those are listed in §5."]
    L += ["", "| step | serves | edits (rows each) | values | basis |", "|---|---|---|---:|---|"]
    for c in d["batches"]["steps"]:
        files = [n for n, p in sorted(d["batches"]["payloads"].items()) if c["id"] in p["steps"]]
        if files:
            edits = ", ".join(f"`{n}` ({d['batches']['payloads'][n]['rows']})" for n in files)
            vals = str(sum(d["batches"]["payloads"][n]["values"] for n in files))
            basis = "applies the payload"
        else:
            edits, vals = "-", "0"
            basis = no_payload.get(c["id"], "**no edit file and no declaration**")
        L.append(f"| {c['id']} | {c['serves']} | {edits} | {vals} | {basis} |")

    gaps = [n for n, p in d["batches"]["payloads"].items() if not p["steps"]]
    L += ["", "## 5. Artefacts no phase-B step names", ""]
    if gaps:
        L += ["Named here rather than dropped. The `kind` decides what the hole costs: a `payload` is",
              "an edit file phase B never writes; a `record` is evidence phase B does not consume, so",
              "no step is missing by design and its rows reach the build only through the card that",
              "reads them.", ""]
        for n in sorted(gaps, key=lambda n: (d["batches"]["payloads"][n]["kind"], n)):
            p = d["batches"]["payloads"][n]
            if n == "t19_hud.json":
                why = ("no B-01...B-14 card writes `hud.gfx`, so the HUD rows need a step B-15 "
                       "(or a clause in B-13) before phase V can gate them.")
            elif p["kind"] == "payload":
                why = "no B card names it, so phase B never writes this edit file."
            else:
                why = "a record, not an edit file: no step is missing by design."
            L.append(f"- `{n}` - {p['kind']}, {p['rows']} rows / {p['values']} values, "
                     f"`{p['path']}`: {why}")
        pay = [n for n in gaps if d["batches"]["payloads"][n]["kind"] == "payload"]
        L += ["", f"{len(gaps)} artefact(s) with no step: {len(pay)} payload(s), "
              f"{len(gaps) - len(pay)} record(s)."]
    else:
        L.append("- none: every artefact is named by at least one B card.")
    L += ["", "## 6. Records the build does not consume", ""]
    for n, p in sorted(d["batches"]["payloads"].items()):
        if p["kind"] == "record":
            L.append(f"- `{n}` - {p['rows']} rows, a decision record; the values it records are "
                     "already in the base tree or are the decision itself.")
    L += ["", "## 7. How to regenerate and check", "",
          "```", "python Tools/scripts/t23_closeout.py --write    # writes this file + build_batches.json",
          "python Tools/scripts/t23_closeout.py --check    # re-derives, compares, runs the three",
          "                                                # siblings below, then gate TX",
          "python Tools/scripts/t_rows.py check            # ledger sums (run by --check)",
          "python Tools/scripts/status_audit.py --check    # STATUS.md current (run by --check)",
          "python Tools/scripts/bmak_coverage.py --check   # every G1 feature row -> a T row (run by --check)",
          "```", "",
          "Gate TX is that one command now: the three sibling checks, the two byte comparisons and the",
          "code/assumed/decision/batch gates. `--gate` prints the same status lines without the sibling",
          "runs or the file comparison, for a quick read. A failing row stops phase B.", ""]
    if d["gate"]["problems"]:
        L += ["## Problems", ""] + [f"- {p}" for p in d["gate"]["problems"]] + [""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="regenerate BUILD_BATCHES.md + json")
    ap.add_argument("--check", action="store_true", help="re-derive, compare, run gate TX")
    ap.add_argument("--gate", action="store_true", help="gate TX only")
    a = ap.parse_args()

    d, problems = gate()
    md, js = render_md(d), render_json(d)
    if a.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print(f"wrote {OUT_MD}\nwrote {OUT_JSON}")
    sibs = []
    if a.check:
        bad = []
        if not os.path.exists(OUT_MD) or rd(OUT_MD) != md:
            bad.append("BUILD_BATCHES.md differs from the re-derived record (regenerate with "
                       "--write: every disposition on it is live)")
        if not os.path.exists(OUT_JSON) or rd(OUT_JSON) != js:
            bad.append("build_batches.json differs from the re-derived record (regenerate with "
                       "--write: every disposition in it is live)")
        sibs = sibling_checks()
        for s in sibs:
            if s["exit"] != 0:
                bad.append(f"{s['check']} exits {s['exit']}: {s['last']}")
        problems = problems + bad
    g = d["gate"]
    acts = collections.Counter(p["kind"] for p in d["batches"]["payloads"].values())
    print(f"gate TX: {g['codes']} codes ({g['codes_carried']} carried, {g['codes_omitted']} named "
          f"omission, {g['codes_blocked']} blocked, {g['codes_documented']} documented, "
          f"{g['codes_unmapped']} unmapped) | "
          f"{g['rows']} ledger rows | assumed {g['assumed']['count']} "
          f"({len(g['assumed']['unsigned'])} unsigned) | decisions "
          f"{sum(1 for x in g['decisions'] if x['state'] == 'answered')}/{len(g['decisions'])} "
          f"answered | "
          f"{len(d['batches']['payloads'])} artefacts ({acts.get('payload', 0)} payloads + "
          f"{acts.get('record', 0)} records) over {len(d['batches']['steps'])} B steps")
    if sibs:
        print("siblings: " + " | ".join(f"{s['check']} exit {s['exit']}" for s in sibs))
    if problems:
        for p in problems:
            print("FAIL", p)
        print(f"{len(problems)} problem(s)")
        return 1
    print(f"gate TX ok: every §1 code maps to a row, assumed rows are signed off, "
          f"D-1...D-{len(g['decisions'])} answered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
