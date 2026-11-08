#!/usr/bin/env python3
"""t10_damage.py - T-14: the damage and armour translation (rows T-DM1…T-DM9, ARM-1…6).

The card asks for one decision that G2-28 left open and for the three remaining ARM rows:

  * T-DM9 small-arms immunity - choose between root `invulnerable` = 1 (whole-vehicle *if the
    gate is honoured*, which is unproven for a vehicle root) and the armour channels + health
    scale, and show **both** options' hits-to-kill tables from the G2-28 model;
  * ARM-4 wheels unbreakable - the part/skew members and their values;
  * ARM-5 regeneration - only if both sides have a member;
  * ARM-6 death look - the effects/sound rows.

Every number is recomputed from the G2-28 sources, never typed in: the build's own values
come from `Working/Translation/current.json` (decoded from `Builds/test-091`), the arm
damage and the three model formulas from `Tools/scripts/damage_predict.py`, the BmAK ratio
from `Research/BatmobileGrab/DAMAGE_RULES.json` (G1-14), the shipped domains and counts from
`Research/JC3Grab/VOCABULARY.md`, the wheel-member census from
`Research/BatmobileGrab/BMSDK_OFFSETS.json`.

The card's Done line is model-conditional: ARM-1 fails under H0 (armour ignored) and ARM-2
fails under H1 (percentage gate). `--check` **prints** those two cells and requires each one
to name the Q-1 probe that decides its model, instead of dropping them from the test. A
failing cell with no probe is a failure; so is a probe for a cell that now passes.

Usage:
  python Tools/scripts/t10_damage.py --write    # write the doc, the edits json, fix the switch file
  python Tools/scripts/t10_damage.py --check    # recompute and compare (exit 1 on any drift)
  python Tools/scripts/t10_damage.py dump       # print the payload
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import damage_predict as dp                      # noqa: E402
import damage_audit as da                        # noqa: E402

OUT = os.path.join(ROOT, "Working", "Translation")
DOC = os.path.join(OUT, "T10_DAMAGE.md")
JSON_OUT = os.path.join(OUT, "t10_damage_edits.json")
CURRENT = os.path.join(OUT, "current.json")
SWITCHES = os.path.join(OUT, "damage_switches.json")
ROWS = os.path.join(OUT, "T_ROWS.jsonl")
VOCAB = os.path.join(ROOT, "Research", "JC3Grab", "VOCABULARY.md")
BMSDK = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")

# The two options the card names.
INVULNERABLE = 1
SMALL_ARMS_SETUP = 200          # Q1-DM-B: 200 pistol rounds on the body
VISIBLE_LOSS = 0.05             # "no visible loss": under 5 % of the pool
ARM2_TOLERANCE_PCT = 20.0       # the card's +-20 % of the BmAK hit count

# The probe that separates every model miss.  ARM-1 under H0 means the armour members are
# ignored, which the fleet census refutes and Q1-DM-B tests on the bullet channel; ARM-2
# under H1 means the percentage gate, which Q1-DM-A separates from the threshold model.
PENDING_PROBES = {
    ("ARM-1", "H0"): "Q1-DM-B",
    ("ARM-2", "H1"): "Q1-DM-A",
}

# Option A's scope is an inference from the member name plus the prop usage; the research
# file that decoded the field says so (DAMAGE_MECHANISMS.md section 4).
OPTION_A_GATE = ("cannot-be-damaged gate, whole-vehicle **if honoured** - unproven for a "
                 "vehicle root: nothing in the shipped vehicle fleet uses it and the evidence "
                 "for 1 comes from `CDamageController` props (`DAMAGE_MECHANISMS.md` section 4)")


def load_current() -> dict:
    doc = json.load(open(CURRENT, encoding="utf-8"))
    vals: dict[str, object] = {}
    for name, mod in doc.get("modules", {}).items():
        for path, value in mod.get("values", {}).items():
            vals.setdefault(path, value)
    return vals


def rows_now() -> dict[str, dict]:
    """The T-DM rows as the ledger holds them (id -> record)."""
    out = {}
    for line in open(ROWS, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("id", "").startswith("T-DM"):
            out[r["id"]] = r
    return out


# ---------------------------------------------------------------------------------------------
# VOCABULARY.md: the shipped ranges and the counts the doc quotes

VOCAB_ROW = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*([A-Za-z0-9\[\]]+)\s*\|\s*"
    r"(-?[\d.]+(?:e[+-]?\d+)?)\s*\.\.\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*\([^)]*\)\s*\|"
    r"\s*(-?[\d.]+(?:e[+-]?\d+)?)\s*\|\s*$")


def vocab_rows() -> dict[str, dict]:
    """path -> {type, min, max, donor} for every vocabulary row with a range."""
    out: dict[str, dict] = {}
    for line in open(VOCAB, encoding="utf-8"):
        m = VOCAB_ROW.match(line.strip())
        if not m:
            continue
        path, kind, lo, hi, donor = m.groups()
        out[path] = {"type": kind, "min": float(lo), "max": float(hi), "donor": float(donor)}
    if not out:
        raise SystemExit("no ranged rows found in %s" % VOCAB)
    return out


def domain(vocab: dict[str, dict], path: str) -> str:
    if path not in vocab:
        raise SystemExit("VOCABULARY.md has no ranged row for %s" % path)
    r = vocab[path]
    return "%g..%g" % (r["min"], r["max"])


def vocab_types() -> int:
    """Number of `## `Class`` sections in VOCABULARY.md (the '52-type' vocabulary)."""
    n = 0
    for line in open(VOCAB, encoding="utf-8"):
        if re.match(r"^##\s+`[^`]+`", line):
            n += 1
    return n


def sdk_wheel_stats() -> dict:
    """Wheel-named members in BmAK's SDK binding, and whether any is a damage field."""
    doc = json.load(open(BMSDK, encoding="utf-8"))
    names: set[str] = set()
    entries = 0
    for cls in doc.get("classes", {}).values():
        for prop in cls.get("properties", []):
            name = prop.get("name", "")
            if "wheel" in name.lower():
                entries += 1
                names.add(name)
    hits = sorted(n for n in names
                  if re.search(r"damage|health|broken|destruct", n, re.I))
    return {"names": len(names), "entries": entries, "hits": len(hits), "hit_names": hits}


def table_for(veh: dict, arms: dict) -> dict:
    """arm -> primary component's H0/H1/H2 under the three G2-28 models."""
    out = {}
    for key in sorted(arms):
        pred = dp.predict(veh, arms[key])
        prim = pred.get("primary") or {}
        out[key] = {
            "channel": prim.get("channel"),
            "damage": prim.get("damage"),
            "armor": prim.get("armor"),
            "strength": prim.get("strength"),
            "H0": prim.get("H0"),
            "H1": prim.get("H1"),
            "H2": prim.get("H2"),
        }
    return out


def build_payload() -> dict:
    p = dp.build_payload()
    veh = copy.deepcopy(p["vehicles"]["build_test-091"])
    arms = p["arms"]
    cur = load_current()
    vocab = vocab_rows()

    # ARM-2: the BmAK ratio is 1200 / 50 = 24 heavy-cannon hits.
    bmak_hits = int(p["arm_targets"]["bmak_ratio"]["heavy_cannon_hits"])
    shell = float(p["arm_targets"]["tank_shell_damage"])
    fleet_max_health = int(round(float(p["arm_targets"]["fleet_max_health"])))

    # The chosen scale is G2-28's own record of 24 hits x the shell damage (H0's answer).
    health_scale = int(round(float(p["arm_targets"]["max_health_needed"])))
    if health_scale != int(round(bmak_hits * shell)):
        raise SystemExit("max_health_needed %d is not %d x %s" % (health_scale, bmak_hits, shell))

    expl_armor = float(veh["channels"].get("explosion", {}).get("armor") or 0.0)
    expl_strength = float(veh["channels"].get("explosion", {}).get("strength") or 0.0)
    per_hit = {"H0": shell,
               "H1": shell * (1.0 - min(expl_strength, 100.0) / 100.0),
               "H2": shell}
    health_needed = {m: int(round(bmak_hits * per_hit[m] - (expl_armor if m == "H2" else 0.0)))
                     for m in per_hit}
    if health_scale != health_needed["H0"]:
        raise SystemExit("chosen max_health %d is not the H0 answer %d"
                         % (health_scale, health_needed["H0"]))

    opt_b_veh = copy.deepcopy(veh)
    opt_b_veh["max_health"] = health_scale
    table_b = table_for(opt_b_veh, arms)
    table_now = {k: v["primary"] for k, v in p["table"]["build_test-091"].items()}

    # the fleet-maximum health table: what 4 000 (the shipped ceiling) would give
    fleet_veh = copy.deepcopy(veh)
    fleet_veh["max_health"] = fleet_max_health
    table_fleet = table_for(fleet_veh, arms)

    def dev(model: str) -> float | None:
        h = table_b["tank_cannon"][model]
        if not isinstance(h, (int, float)):
            return None
        return round((h - bmak_hits) / bmak_hits * 100.0, 2)

    # ARM-1: how much of the pool a 200-round pistol burst takes under each model.
    pistol = table_b["pistol"]
    loss = {}
    for model in dp.MODELS:
        h = pistol[model]
        loss[model] = None if h is None else round(SMALL_ARMS_SETUP / float(h) * 100.0, 4)
    # H1's damage per pistol round, from the same channel values the model uses.
    pistol_h1_per_round = round(float(pistol["damage"]) *
                                (1.0 - min(float(pistol["strength"]), 100.0) / 100.0), 6)

    ok_arm1 = {m: (loss[m] is None or loss[m] <= VISIBLE_LOSS * 100.0) for m in dp.MODELS}
    ok_arm2 = {m: (dev(m) is not None and abs(dev(m)) <= ARM2_TOLERANCE_PCT)
               for m in dp.MODELS}

    pending = []
    for code, ok in (("ARM-1", ok_arm1), ("ARM-2", ok_arm2)):
        for m in dp.MODELS:
            if ok[m]:
                continue
            pending.append({
                "code": code,
                "model": m,
                "probe": PENDING_PROBES.get((code, m)),
                "value": loss[m] if code == "ARM-1" else table_b["tank_cannon"][m],
                "criterion": ("< %g %%" % round(VISIBLE_LOSS * 100.0, 6))
                             if code == "ARM-1" else
                             ("\u00b1%g %% of %d hits" % (ARM2_TOLERANCE_PCT, bmak_hits)),
                "resolution": ("H0 ignores the armour members; the fleet census says armour is "
                               "used, and Q1-DM-B tests the bullet gate")
                              if code == "ARM-1" else
                              ("H1 needs max_health %d for the %d-hit ratio; Q1-DM-A decides "
                               "percentage vs threshold" %
                               (health_needed["H1"], bmak_hits)),
            })

    rows = []
    ledger = rows_now()

    def row(id_, member, action, frm, to, why, dom, src):
        rows.append({"id": id_, "member": member, "action": action, "from": frm, "to": to,
                     "why": why, "domain": dom, "source": src,
                     "ledger_dispo": (ledger.get(id_) or {}).get("dispo")})

    row("T-DM1", "max_health", "edit", veh["max_health"], health_scale,
        "ARM-2 at the BmAK ratio: %d heavy-cannon hits x %s shell damage = %d (the H0 answer; "
        "H2 needs %d, H1 %d). %d is outside the shipped %s domain, so it is a declared "
        "switch, not a translated value, and it is **pending Q1-DM-A**: if the percentage "
        "gate ships, the value is %d."
        % (bmak_hits, shell, health_scale, health_needed["H2"], health_needed["H1"],
           health_scale, domain(vocab, "max_health"), health_needed["H1"]),
        domain(vocab, "max_health"), "DAMAGE_MODEL.json arm_targets.max_health_needed")
    row("T-DM2", "bullet_armor / bullet_armor_strength", "keep",
        "%s @ %s" % (cur.get("bullet_armor"), cur.get("bullet_armor_strength")),
        "%s @ %s" % (cur.get("bullet_armor"), cur.get("bullet_armor_strength")),
        "already the fleet maximum on both members (armour %g, strength %g); with max_health "
        "%d small arms take %.2f %% of the pool per %d rounds under H1, %.2f %% under H0, "
        "and nothing under H2"
        % (vocab["bullet_armor"]["max"], vocab["bullet_armor_strength"]["max"],
           health_scale, loss.get("H1") or 0.0, SMALL_ARMS_SETUP, loss.get("H0") or 0.0),
        "%s @ %s" % (domain(vocab, "bullet_armor"),
                     domain(vocab, "bullet_armor_strength")),
        "VOCABULARY.md VehicleDamage")
    row("T-DM3", "bullet_heavy_armor / bullet_heavy_armor_strength", "keep",
        "%s @ %s" % (cur.get("bullet_heavy_armor"), cur.get("bullet_heavy_armor_strength")),
        "%s @ %s" % (cur.get("bullet_heavy_armor"), cur.get("bullet_heavy_armor_strength")),
        "unchanged: the per-channel split ARM-1 needs is the bullet / bullet_heavy pair, and "
        "no G2-11 weapon component is decoded into bullet_heavy yet (UNKNOWN -> no row)",
        "%s @ %s" % (domain(vocab, "bullet_heavy_armor"),
                     domain(vocab, "bullet_heavy_armor_strength")),
        "VOCABULARY.md VehicleDamage")
    row("T-DM4", "explosion_threshold / npc_explosion_threshold / smoke_threshold", "keep",
        "%s / %s / %s" % (cur.get("explosion_threshold"), cur.get("npc_explosion_threshold"),
                          cur.get("smoke_threshold")),
        "same", "per-hit damage thresholds, independent of the health pool: %d does not move "
        "them" % health_scale,
        " / ".join(domain(vocab, k) for k in ("explosion_threshold",
                                              "npc_explosion_threshold",
                                              "smoke_threshold")),
        "VOCABULARY.md VehicleDamage")
    row("T-DM5", "part_damage_types (%d) + the part join" % len(veh["part_damage_types"]),
        "keep", "%d types" % len(veh["part_damage_types"]),
        "%d types" % len(veh["part_damage_types"]),
        "carried from the donor; the wheel members below are the only part rows T-14 touches",
        "fleet", "current.json")
    row("T-DM6", "deform_scale", "keep", cur.get("deform_scale"), cur.get("deform_scale"),
        "cosmetic off switch (no panel crumple), already declared in damage_switches.json",
        "%s (declared switch)" % domain(vocab, "deform_scale"),
        "Working/Translation/damage_switches.json")
    row("T-DM7", "outgoing ram damage", "out", "-", "-",
        "unchanged: G2-28 found no outgoing ram-damage member; the only impact member is "
        "incoming (impact_damage_factor)",
        "-", "Research/JC3Grab/DAMAGE_MODEL.md")
    row("T-DM8", "impact_damage_factor", "keep", cur.get("impact_damage_factor"),
        cur.get("impact_damage_factor"),
        "incoming collision damage off (BmAK: ramming does not scratch it); declared switch",
        "%s (declared switch)" % domain(vocab, "impact_damage_factor"),
        "Working/Translation/damage_switches.json")
    invuln = veh["root"].get("invulnerable")
    if invuln is None:
        raise SystemExit("the build's root invulnerable is not decoded in DAMAGE_MODEL.json")
    row("T-DM9", "CCar.invulnerable / the armour channels", "decide",
        "invulnerable %s (root, decoded from the build's .epe)" % invuln,
        "invulnerable stays %s; ARM-1 and ARM-2 carried by channels + max_health" % invuln,
        "option B chosen. Option A sets invulnerable = %d, whose whole-vehicle scope is "
        "whole-vehicle only if honoured and is unproven for a vehicle root "
        "(DAMAGE_MECHANISMS.md section 4); under it the tank cannon reads 'never' and ARM-2's "
        "%d-hit ratio cannot exist. Under B the ratio deviation is H0 %.2f %%, H1 %.2f %%, "
        "H2 %.2f %%; the %d scale is pending Q1-DM-A (18000 under H1)."
        % (INVULNERABLE, bmak_hits, dev("H0") or 0.0, dev("H1") or 0.0, dev("H2") or 0.0,
           health_scale),
        "invulnerable %s (decoded); channels as T-DM2" % invuln,
        "DAMAGE_MECHANISMS.md + DAMAGE_MODEL.json")

    # ARM-4: wheels. Both axles ship skew_health 200; the shipped maximum is the ceiling.
    skew_members = ["front_wheels_damage.skew_health", "rear_wheels_damage.skew_health"]
    for k in skew_members:
        domain(vocab, k)  # raises if the member leaves the vocabulary
    skew_target = int(vocab[skew_members[0]]["max"])
    wheel_rows = {k: v for k, v in vocab.items() if "wheels_damage." in k}
    broken = {k: v for k, v in wheel_rows.items() if "broken_wheel" in k}
    health_rows = {k: v for k, v in wheel_rows.items() if "broken_wheel" not in k}
    if sorted(health_rows) != sorted(skew_members):
        raise SystemExit("the non-broken wheel-damage ranged members changed: %s"
                         % sorted(health_rows))
    sdk = sdk_wheel_stats()
    no_switch_words = sorted(k for k in vocab
                             if "wheels_damage." in k
                             and re.search(r"bwheel|indestruct", k, re.I))
    wheels = []
    for k in skew_members:
        wheels.append({"member": k, "from": cur.get(k), "to": skew_target,
                       "action": "edit" if cur.get(k) != skew_target else "keep"})
    wheel_note = (
        "`skew_health` is the only wheel-damage **health** member with a shipped range (%s) "
        "and it is now at the maximum (%d) on both axles; the other %d wheel-damage members "
        "with ranges are the broken-wheel fractions (%s, %s), which move a broken wheel, not "
        "its health. **No off switch exists on either side**: JC3's vocabulary has %d "
        "`wheels_damage` rows and %d hits for `bWheel`/`indestruct`, and the %d distinct "
        "wheel-named members in BmAK's SDK binding (%d entries) include %d damage, health, "
        "broken or destruct fields. So ARM-4 lands at the fleet ceiling, not proven "
        "unbreakable; the broken-wheel fractions stay at the build's values."
        % (domain(vocab, skew_members[0]), skew_target, len(broken),
           domain(vocab, [k for k in broken if "friction" in k][0]),
           domain(vocab, [k for k in broken if "radius" in k][0]),
           len(wheel_rows), len(no_switch_words),
           sdk["names"], sdk["entries"], sdk["hits"]))

    declared = [k for k in da.load_switches() if k not in ("bullet_armor_strength",)]
    payload = {
        "schema": 1,
        "generated_by": "Tools/scripts/t10_damage.py",
        "card": "T-14",
        "decision": {
            "row": "T-DM9",
            "chosen": "B: armour channels + max_health scale, invulnerable stays 0",
            "rejected": "A: CCar.invulnerable = 1",
            "why": "A has no decoded arithmetic: if the gate is honoured it stops the tank "
                   "cannon too, so ARM-2's %d-hit ratio cannot exist, and its whole-vehicle "
                   "scope is unproven for a vehicle root (DAMAGE_MECHANISMS.md section 4). "
                   "B's hits come from the decoded channels and the health model." % bmak_hits,
            "invulnerable_now": invuln,
            "max_health_chosen": health_scale,
            "max_health_for_ratio": health_needed,
            "option_a_gate": OPTION_A_GATE,
        },
        "bmak": {
            "health": p["arm_targets"]["bmak_ratio"]["health"],
            "heavy_cannon_damage": p["arm_targets"]["bmak_ratio"]["heavy_cannon_damage"],
            "heavy_cannon_hits": bmak_hits,
            "tank_shell_damage": shell,
            "source": p["arm_targets"]["bmak_ratio"]["source"],
        },
        "vocab": {
            "types": vocab_types(),
            "fleet_max_health": fleet_max_health,
            "wheels_damage_rows": len(wheel_rows),
            "hits_at_fleet_max_health": {
                "H0": table_fleet["tank_cannon"]["H0"],
                "H1": table_fleet["tank_cannon"]["H1"],
                "H2": table_fleet["tank_cannon"]["H2"],
            },
            "pistol_h1_damage_per_round": pistol_h1_per_round,
        },
        "options": {
            "A_invulnerable": {
                "setting": "CCar.invulnerable = %d" % INVULNERABLE,
                "rule": OPTION_A_GATE,
                "table": {k: "never, if the gate applies (unproven for a vehicle root)"
                          for k in sorted(arms)},
                "arm2": "Fails if the gate applies: 'never' is not %d hits; the gate's scope "
                        "is UNKNOWN for a vehicle root" % bmak_hits,
            },
            "B_channels": {
                "setting": "max_health %d, invulnerable 0, channels as T-DM2" % health_scale,
                "table": table_b,
                "arm2_deviation_pct": {m: dev(m) for m in dp.MODELS},
                "max_health_for_ratio": health_needed,
                "per_hit_explosion": {m: round(per_hit[m], 6) for m in per_hit},
                "small_arms_pool_loss_pct_200_rounds": loss,
            },
        },
        "table_before": table_now,
        "rows": rows,
        "arm4_wheels": {"edits": wheels, "note": wheel_note,
                        "target": skew_target,
                        "broken_wheel_members": len(broken)},
        "arm5_regen": {
            "jcs_member": None,
            "bmak_member": "RVehicleBatmobileBase.HealthRecoverRate (TArray<float> @ +8220)",
            "bmak_value": "UNKNOWN - no archetype overrides it; the native CDO is not shipped",
            "verdict": "named omission: JC3's VehicleDamage has no recovery member (0 hits for "
                       "recover/regen over the %d-type vocabulary), so there is nothing to "
                       "write; BmAK's rate is awarded per experience event, not a per-second "
                       "regen" % vocab_types(),
        },
        "arm6_death": {
            "jcs_rows": "owned by T-17 (effects) and T-16 (audio)",
            "bmak_datasource": "none decoded: G1-14 covers incoming-damage rules, not the death "
                               "effect or sound; no destroyed-state effect path exists in the "
                               "Batmobile packages' record",
            "verdict": "named omission with owner: T-14 writes no death-look row because the "
                       "BmAK side has no decoded effect/sound path to translate",
        },
        "switch_file": {
            "stale_declarations": ["bullet_armor_strength"],
            "declared": sorted(declared),
            "declared_count": len(declared),
            "why": "T-DM2 moved it 100 -> 99, which is inside the shipped 0..99, so the "
                   "declaration is no longer a switch; damage_audit.py fails while it stays",
            "pending": {"max_health": health_scale},
            "pending_why": "%d is out of domain and must be declared when a build carries it; "
                           "declaring it now would fail the audit against the current build, "
                           "which still ships %s" % (health_scale, cur.get("max_health")),
            "done_clause": "PARTIAL: %d declarations, 1 pending (`max_health` %d) until a "
                           "build carries it" % (len(declared), health_scale),
        },
        "pending": pending,
        "done": {
            "arm1": "H1/H2 pass; H0 fails (%.3f %% of the pool >= %g %%)%s"
                    % (loss["H0"], round(VISIBLE_LOSS * 100.0, 6),
                       "; pending Q1-DM-B" if not ok_arm1["H0"] else ""),
            "arm2": "H0/H2 pass; H1 fails (%s hits vs %d, %+.2f %%)%s"
                    % (table_b["tank_cannon"]["H1"], bmak_hits, dev("H1") or 0.0,
                       "; pending Q1-DM-A" if not ok_arm2["H1"] else ""),
        },
        "checks": {
            "arm2_within_20pct": ok_arm2,
            "small_arms_no_visible_loss": ok_arm1,
            "visible_loss_pct": round(VISIBLE_LOSS * 100.0, 6),
            "arm2_tolerance_pct": ARM2_TOLERANCE_PCT,
        },
    }
    return payload


def md(p: dict) -> str:
    L = []
    A = L.append
    b = p["bmak"]
    d = p["decision"]
    health = d["max_health_chosen"]
    A("# Damage and armour translation (T-14)")
    A("")
    A("Generated by `Tools/scripts/t10_damage.py`. Rows T-DM1…T-DM9 and the four remaining ARM")
    A("codes. Every number is recomputed: the build's values from `Working/Translation/current.json`")
    A("(decoded from `Builds/test-091`), the arm damage and the three model formulas from")
    A("`Tools/scripts/damage_predict.py`, the BmAK ratio from `DAMAGE_RULES.json` (G1-14), the")
    A("shipped domains and counts from `Research/JC3Grab/VOCABULARY.md`, the wheel-member census")
    A("from `Research/BatmobileGrab/BMSDK_OFFSETS.json`.")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| BmAK health / heavy-cannon damage | **%s / %s** |" % (b["health"], b["heavy_cannon_damage"]))
    A("| BmAK ratio | **%d heavy-cannon hits** |" % b["heavy_cannon_hits"])
    A("| JC3 tank shell | **%s** in its blast |" % b["tank_shell_damage"])
    A("| `max_health` for that ratio | **%d** (H0; H1 %d, H2 %d) — shipped domain %s |"
      % (health, d["max_health_for_ratio"]["H1"], d["max_health_for_ratio"]["H2"],
         p["rows"][0]["domain"]))
    A("")
    A("## 0. What the card's Done line actually reads today")
    A("")
    A("The card asks for a predicted table in which small arms show no visible loss and heavy")
    A("weapons sit within ±%g %% of the BmAK ratio. The three candidate health models do not"
      % p["checks"]["arm2_tolerance_pct"])
    A("agree, so the status is model-conditional and is printed here rather than hidden:")
    A("")
    A("| Done clause | status |")
    A("|---|---|")
    A("| ARM-1 small arms do not move the bar | %s |" % p["done"]["arm1"])
    A("| ARM-2 heavy weapons at the BmAK ratio | %s |" % p["done"]["arm2"])
    A("| every switch recorded in `damage_switches.json` | %s |"
      % p["switch_file"]["done_clause"])
    A("")
    A("`--check` prints the same three lines and fails if a failing cell has no pending probe,")
    A("or if a probe is listed for a cell that passes.")
    A("")
    A("## 1. T-DM9 — the choice: channels, not `invulnerable`")
    A("")
    A("| | option A | option B (chosen) |")
    A("|---|---|---|")
    A("| what it sets | `CCar.invulnerable` = %d | `max_health` %d, `invulnerable` 0, channels as T-DM2 |"
      % (INVULNERABLE, health))
    A("| small arms | never reach health *if the gate applies* | %s %% of the pool per %d pistol rounds under H0, %s %% under H1, %s under H2 |"
      % (("%.3f" % p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H0"]),
         SMALL_ARMS_SETUP,
         ("%.3f" % p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H1"]),
         "never (absorbed)"
         if p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H2"] is None
         else "%.3f %%" % p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H2"]))
    A("| the tank cannon | **never** *if the gate applies*; the gate's scope is UNKNOWN for a vehicle root | **%s / %s / %s** hits (H0/H1/H2) vs the BmAK %d |"
      % (p["options"]["B_channels"]["table"]["tank_cannon"]["H0"],
         p["options"]["B_channels"]["table"]["tank_cannon"]["H1"],
         p["options"]["B_channels"]["table"]["tank_cannon"]["H2"], b["heavy_cannon_hits"]))
    A("| ARM-2 at the BmAK ratio | impossible if the gate applies | %s %%"
      % ", ".join("%s %s" % (m, p["options"]["B_channels"]["arm2_deviation_pct"][m])
                  for m in dp.MODELS))
    A("")
    A("Option B is chosen because it is the only option with decoded arithmetic: its hits come")
    A("from the decoded armour channels and shell damage. Option A is not rejected on a")
    A("measured `never` — the `invulnerable` flag's whole-vehicle scope is an inference from its")
    A("name and its prop usage, and `DAMAGE_MECHANISMS.md` section 4 states it is **unproven")
    A("for a vehicle root** (nothing in the shipped vehicle fleet uses it; the evidence for `1`")
    A("comes from `CDamageController` props). If the gate is not honoured, option A's table is")
    A("UNKNOWN;")
    A("if it is, ARM-2 cannot exist. Either way A adds nothing decoded.")
    A("")
    A("### Option A's table")
    A("")
    A("| arm | result |")
    A("|---|---|")
    for k, v in p["options"]["A_invulnerable"]["table"].items():
        A("| `%s` | %s |" % (k, v))
    A("")
    A(p["options"]["A_invulnerable"]["arm2"] + ".")
    A("")
    A("")
    A("### Option B's table (`max_health` %d)" % health)
    A("")
    A("| arm | channel | damage | armour @ strength | H0 | H1 | H2 |")
    A("|---|---|---:|---|---:|---:|---:|")
    for k in sorted(p["options"]["B_channels"]["table"]):
        t = p["options"]["B_channels"]["table"][k]
        A("| `%s` | %s | %s | %s @ %s | %s | %s | %s |"
          % (k, t["channel"], t["damage"], t["armor"], t["strength"],
             dp.fmt_hits(t["H0"]), dp.fmt_hits(t["H1"]), dp.fmt_hits(t["H2"])))
    A("")
    A("What `max_health` each model would need for exactly %d tank-cannon hits:" % b["heavy_cannon_hits"])
    A("")
    A("| model | per-hit on the explosion channel | `max_health` for %d hits |" % b["heavy_cannon_hits"])
    A("|---|---:|---:|")
    for m in dp.MODELS:
        A("| %s | %s | **%s** |"
          % (m, p["options"]["B_channels"]["per_hit_explosion"][m],
             p["options"]["B_channels"]["max_health_for_ratio"][m]))
    A("")
    A("`max_health` %d is the H0 answer; H2 needs %d, and under H1 the same ratio needs %d."
      % (health, d["max_health_for_ratio"]["H2"], d["max_health_for_ratio"]["H1"]))
    A("Q1-DM-A is the probe that decides percentage gate vs threshold. The chosen %d gives"
      % health)
    A("%s hits under H1 — outside the ±%g %% band, which is why H1 needs %d."
      % (p["options"]["B_channels"]["table"]["tank_cannon"]["H1"],
         p["checks"]["arm2_tolerance_pct"], d["max_health_for_ratio"]["H1"]))
    A("")
    A("Read as a bracket: H0 (armour ignored) / H1 (percentage gate) / H2 (threshold + pool).")
    A("The build's values sit inside the shipped domain on every channel, so the bracket is the")
    A("only uncertainty left; Q1-DM-A/B/C pick which.")
    A("")
    A("### What the two requirements become")
    A("")
    A("| requirement | criterion | H0 | H1 | H2 |")
    A("|---|---|---|---|---|")
    def _loss(m):
        v = p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"][m]
        return "never (absorbed)" if v is None else "%.3f %%" % v

    def _mark(code, m, text):
        ok = (p["checks"]["small_arms_no_visible_loss"] if code == "ARM-1"
              else p["checks"]["arm2_within_20pct"])[m]
        if ok:
            return text
        probe = next((e["probe"] for e in p["pending"]
                      if e["code"] == code and e["model"] == m), None)
        return "%s (FAIL%s)" % (text, ", pending %s" % probe if probe else ", no probe")

    A("| ARM-1 small arms do not move the bar | %d pistol rounds < %g %% of the pool | %s | %s | %s |"
      % (SMALL_ARMS_SETUP, round(VISIBLE_LOSS * 100.0, 6),
         _mark("ARM-1", "H0", _loss("H0")), _mark("ARM-1", "H1", _loss("H1")),
         _mark("ARM-1", "H2", _loss("H2"))))
    A("| ARM-2 heavy weapons at the BmAK ratio | within ±%g %% of %d hits | %s | %s | %s |"
      % (p["checks"]["arm2_tolerance_pct"], b["heavy_cannon_hits"],
         _mark("ARM-2", "H0", "%s" % p["options"]["B_channels"]["table"]["tank_cannon"]["H0"]),
         _mark("ARM-2", "H1", "%s" % p["options"]["B_channels"]["table"]["tank_cannon"]["H1"]),
         _mark("ARM-2", "H2", "%s" % p["options"]["B_channels"]["table"]["tank_cannon"]["H2"])))
    A("")
    A("The FAIL cells are the model bracket, not an unacknowledged miss: each names the Q-1")
    A("probe that decides its model. If H1 ships, `max_health` becomes %d; if H0 ships, ARM-1"
      % d["max_health_for_ratio"]["H1"])
    A("cannot be met by any armour value (armour is ignored) and becomes a named omission.")
    A("")
    A("## 2. ARM-4 — wheels")
    A("")
    for w in p["arm4_wheels"]["edits"]:
        A("- `%s`: **%s** → **%s** (%s)" % (w["member"], w["from"], w["to"], w["action"]))
    A("")
    A(p["arm4_wheels"]["note"])
    A("")
    A("## 3. ARM-5 — regeneration")
    A("")
    A("| side | member | value |")
    A("|---|---|---|")
    A("| JC3 | none — 0 hits for `recover`/`regen` over the %d-type vocabulary | — |"
      % p["vocab"]["types"])
    A("| BmAK | `%s` | %s |" % (p["arm5_regen"]["bmak_member"], p["arm5_regen"]["bmak_value"]))
    A("")
    A(p["arm5_regen"]["verdict"] + ".")
    A("")
    A("## 4. ARM-6 — death look")
    A("")
    A(p["arm6_death"]["verdict"] + ".")
    A("")
    A("| side | where |")
    A("|---|---|")
    A("| JC3 rows | %s |" % p["arm6_death"]["jcs_rows"])
    A("| BmAK | %s |" % p["arm6_death"]["bmak_datasource"])
    A("")
    A("## 5. The nine rows")
    A("")
    A("| row | member | action | from | to | domain | ledger |")
    A("|---|---|---|---|---|---|---|")
    for r in p["rows"]:
        A("| %s | `%s` | **%s** | %s | %s | %s | %s |"
          % (r["id"], r["member"], r["action"], r["from"], r["to"], r["domain"],
             r["ledger_dispo"] if r["ledger_dispo"] is not None else "UNKNOWN"))
    A("")
    A("`action` is what T-14 does to the row. `ledger` is the disposition `T_ROWS.jsonl` holds")
    A("(generated by `t_rows.py`): `next` means the value is decided here and a later build")
    A("card writes it; `edit` is reserved for rows already in `t1_edits.json` (T-DM2's applied")
    A("edit); `out` means no JC3 expression exists. T-14 rework moved T-DM1 from `keep` and")
    A("T-DM9 from `blocked` to `next`; the `T3_COVERAGE.md` cells still carry T-3's original")
    A("'blocked pending the write' text, so the ledger here is the current state.")
    A("")
    A("Row by row, the reason:")
    A("")
    for r in p["rows"]:
        A("- **%s** — %s" % (r["id"], r["why"]))
    A("")
    A("## 6. The switch file")
    A("")
    A("`Working/Translation/damage_switches.json` declares %d switches: %s."
      % (p["switch_file"]["declared_count"],
         ", ".join("`%s`" % k for k in p["switch_file"]["declared"])))
    A("`bullet_armor_strength` is no longer one of them — this script removed it: %s."
      % p["switch_file"]["why"])
    A("")
    A("- **pending**: `%s` = %s — %s"
      % ("max_health", p["switch_file"]["pending"]["max_health"],
         p["switch_file"]["pending_why"]))
    A("")
    A("**Done clause 2 (every switch recorded) is PARTIAL, not met:** %d declarations are in"
      % p["switch_file"]["declared_count"])
    A("the file and `max_health` %d is pending until a build carries it."
      % p["switch_file"]["pending"]["max_health"])
    A("")
    A("## 7. UNKNOWNs and limits")
    A("")
    A("- **The health scale is a switch, not a translation.** %d is %gx the fleet maximum of"
      % (health, health / p["vocab"]["fleet_max_health"]))
    A("  %d. It is chosen because the card's criterion is the BmAK ratio and no in-domain value"
      % p["vocab"]["fleet_max_health"])
    A("  can reach it (%d gives %s hits under H0, %s under H1, %s under H2). If B decides the"
      % (p["vocab"]["fleet_max_health"],
         p["vocab"]["hits_at_fleet_max_health"]["H0"],
         p["vocab"]["hits_at_fleet_max_health"]["H1"],
         p["vocab"]["hits_at_fleet_max_health"]["H2"]))
    A("  fleet domain is a hard ceiling, ARM-2's ratio becomes a named omission and `max_health`")
    A("  returns to %d." % p["vocab"]["fleet_max_health"])
    A("- **The models disagree about small arms** (H1: %s damage per pistol round; H2: nothing;"
      % p["vocab"]["pistol_h1_damage_per_round"])
    A("  H0: %.3f %% of the pool per %d rounds). H1/H2 are inside ARM-1; H0 is not, and H0 is"
      % (p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H0"],
         SMALL_ARMS_SETUP))
    A("  only reachable if the armour members are ignored, which the fleet census says they are")
    A("  not on any armoured vehicle.")
    A("- **Option A's gate scope is UNKNOWN for a vehicle root.** The flag is decoded as an")
    A("  int32 (`epe+1167`) with the game's own value; whether a `CCar` root honours it is not")
    A("  proven (`DAMAGE_MECHANISMS.md` section 4). The card's choice does not depend on it:")
    A("  option B is the only option whose numbers come from decoded fields.")
    A("- **`bullet_heavy` is unused** because no G2-11 weapon component is decoded into that")
    A("  channel; if one is, it is the cheaper way to ARM-1 and this row should be revisited.")
    A("- **Wheels are at the ceiling, not proven unbreakable** (section 2).")
    A("- **ARM-5 and ARM-6 are named omissions with owners**, not gaps this card can close.")
    A("")
    return "\n".join(L) + "\n"


def write_switches(p: dict) -> tuple[bool, list[str]]:
    doc = json.load(open(SWITCHES, encoding="utf-8"))
    sw = doc.get("switches", {})
    removed = []
    for name in p["switch_file"]["stale_declarations"]:
        if name in sw:
            sw.pop(name)
            removed.append(name)
    doc["switches"] = sw
    doc["_t14"] = ("T-14 (2026-10-29): removed the `bullet_armor_strength` declaration - "
                   "T-DM2's 99 is inside the shipped 0..99. `max_health` %d stays pending until "
                   "a build carries it (see Working/Translation/t10_damage_edits.json)."
                   % p["switch_file"]["pending"]["max_health"])
    open(SWITCHES, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n")
    return bool(removed), removed


def cmd_dump(p: dict) -> int:
    print(json.dumps(p, indent=1, sort_keys=True))
    return 0


def cmd_write() -> int:
    p = build_payload()
    doc = md(p)
    open(JSON_OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(p, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    open(DOC, "w", encoding="utf-8", newline="\n").write(doc)
    changed, removed = write_switches(p)
    print("wrote %s (%d lines)" % (os.path.relpath(DOC, ROOT), doc.count("\n")))
    print("wrote %s" % os.path.relpath(JSON_OUT, ROOT))
    print("switch file: removed %s" % (", ".join(removed) if removed else "nothing"))
    tc = p["options"]["B_channels"]["table"]["tank_cannon"]
    print("option B tank cannon: H0 %s H1 %s H2 %s (BmAK %d)"
          % (tc["H0"], tc["H1"], tc["H2"], p["bmak"]["heavy_cannon_hits"]))
    return 0


def cmd_check() -> int:
    p = build_payload()
    fails = []
    doc = md(p)
    if not os.path.exists(DOC):
        fails.append("%s missing" % os.path.relpath(DOC, ROOT))
    elif open(DOC, encoding="utf-8").read() != doc:
        fails.append("%s stale: the regenerated text differs" % os.path.basename(DOC))
    want = json.dumps(p, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if not os.path.exists(JSON_OUT):
        fails.append("%s missing" % os.path.basename(JSON_OUT))
    elif open(JSON_OUT, encoding="utf-8").read() != want:
        fails.append("%s stale: the payload differs" % os.path.basename(JSON_OUT))
    # the switch file must already have the stale declarations gone
    sw = json.load(open(SWITCHES, encoding="utf-8")).get("switches", {})
    for name in p["switch_file"]["stale_declarations"]:
        if name in sw:
            fails.append("%s still declares `%s`, which is now inside the shipped range"
                         % (os.path.basename(SWITCHES), name))
    # every row must exist in the ledger, and the doc must show the ledger's disposition
    ledger = rows_now()
    for r in p["rows"]:
        if r["id"] not in ledger:
            fails.append("row %s is not in T_ROWS.jsonl" % r["id"])
        elif r["ledger_dispo"] != ledger[r["id"]].get("dispo"):
            fails.append("row %s: ledger says %s, the record says %s"
                         % (r["id"], ledger[r["id"]].get("dispo"), r["ledger_dispo"]))
    # every failing Done cell must name an existing, matching probe; no probe may be stale
    probe_ids = {x["id"] for x in dp.PROBES}
    failing = {(code, m)
               for code, ok in (("ARM-1", p["checks"]["small_arms_no_visible_loss"]),
                                ("ARM-2", p["checks"]["arm2_within_20pct"]))
               for m in dp.MODELS if not ok[m]}
    listed = {(e["code"], e["model"]) for e in p["pending"]}
    for e in p["pending"]:
        if not e["probe"]:
            fails.append("%s fails under %s with no pending probe" % (e["code"], e["model"]))
        elif e["probe"] not in probe_ids:
            fails.append("pending probe %s is not in damage_predict.PROBES" % e["probe"])
    if listed != failing:
        fails.append("pending list %s does not match the failing cells %s"
                     % (sorted(listed), sorted(failing)))
    for key in PENDING_PROBES:
        if key not in failing:
            fails.append("PENDING_PROBES lists %s %s but that cell passes now" % key)
    if p["switch_file"]["pending"] and "PARTIAL" not in p["switch_file"]["done_clause"]:
        fails.append("the switch Done clause must be reported as PARTIAL while a switch is "
                     "pending")
    print("rows %d | option B tank cannon H0 %s H1 %s H2 %s vs BmAK %d | small arms H0 %s H1 %s "
          "H2 %s"
          % (len(p["rows"]), p["options"]["B_channels"]["table"]["tank_cannon"]["H0"],
             p["options"]["B_channels"]["table"]["tank_cannon"]["H1"],
             p["options"]["B_channels"]["table"]["tank_cannon"]["H2"],
             p["bmak"]["heavy_cannon_hits"],
             "%.3f %%" % p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H0"],
             "%.3f %%" % p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H1"],
             "never" if p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H2"]
             is None else "%.3f %%"
             % p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H2"]))
    def cell(code: str, m: str) -> str:
        ok = (p["checks"]["small_arms_no_visible_loss"] if code == "ARM-1"
              else p["checks"]["arm2_within_20pct"])[m]
        probe = next((e["probe"] for e in p["pending"]
                      if e["code"] == code and e["model"] == m), None)
        if code == "ARM-1":
            v = p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"][m]
            text = "never (absorbed)" if v is None else "%.3f %% of the pool" % v
        else:
            text = "%s hits" % p["options"]["B_channels"]["table"]["tank_cannon"][m]
            dv = p["options"]["B_channels"]["arm2_deviation_pct"][m]
            if dv is not None:
                text += " (%+.2f %%)" % dv
        return ("%s %s" % (m, "pass" if ok else "FAIL")) + " " + text + (
            " pending %s" % probe if not ok else "")

    print("ARM-1 small arms (criterion < %g %% of the pool): %s"
          % (round(VISIBLE_LOSS * 100.0, 6),
             " | ".join(cell("ARM-1", m) for m in dp.MODELS)))
    print("ARM-2 heavy weapons (criterion ±%g %% of %d hits): %s"
          % (p["checks"]["arm2_tolerance_pct"], p["bmak"]["heavy_cannon_hits"],
             " | ".join(cell("ARM-2", m) for m in dp.MODELS)))
    print("switch file: %d declared, %d pending (%s %s) - Done clause 2 PARTIAL"
          % (p["switch_file"]["declared_count"], len(p["switch_file"]["pending"]),
             ", ".join(p["switch_file"]["pending"]),
             p["switch_file"]["pending"]["max_health"]))
    if fails:
        for f in fails:
            print("FAIL", f)
        return 1
    print("md match True, json match True, switch file clean True")
    print("check ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("dump", nargs="?", choices=["dump"], help=argparse.SUPPRESS)
    ap.add_argument("--dump", dest="dump_flag", action="store_true")
    a = ap.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    return cmd_dump(build_payload())


if __name__ == "__main__":
    sys.exit(main())
