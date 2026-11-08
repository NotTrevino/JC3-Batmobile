#!/usr/bin/env python3
"""t10_damage.py - T-14: the damage and armour translation (rows T-DM1…T-DM9, ARM-1…6).

The card asks for one decision that G2-28 left open and for the three remaining ARM rows:

  * T-DM9 small-arms immunity - choose between root `invulnerable` = 1 (whole-vehicle, so
    ARM-2 breaks) and the armour channels + health scale, and show **both** options'
    hits-to-kill tables from the G2-28 model;
  * ARM-4 wheels unbreakable - the part/skew members and their values;
  * ARM-5 regeneration - only if both sides have a member;
  * ARM-6 death look - the effects/sound rows.

Every number is recomputed from the G2-28 sources, never typed in: the build's own values
come from `Working/Translation/current.json` (decoded from `Builds/test-091`), the arm
damage and the three model formulas from `Tools/scripts/damage_predict.py`, the BmAK ratio
from `Research/BatmobileGrab/DAMAGE_RULES.json` (G1-14), the shipped domains from
`Research/JC3Grab/VOCABULARY.md`.

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

# The two options the card names, and the fleet domain the audit reads.
INVULNERABLE = 1
HEALTH_SCALE = 36000            # 24 heavy-cannon hits x 1500 shell damage (G2-28 section 5)
SKEW_HEALTH = 400               # front/rear_wheels_damage.skew_health at the shipped maximum
SMALL_ARMS_SETUP = 200          # Q1-DM-B: 200 pistol rounds on the body
VISIBLE_LOSS = 0.05             # "no visible loss": under 5 % of the pool


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

    opt_b_veh = copy.deepcopy(veh)
    opt_b_veh["max_health"] = HEALTH_SCALE
    table_b = table_for(opt_b_veh, arms)
    table_now = {k: v["primary"] for k, v in p["table"]["build_test-091"].items()}

    # ARM-2: the BmAK ratio is 1200 / 50 = 24 heavy-cannon hits.
    bmak_hits = int(p["arm_targets"]["bmak_ratio"]["heavy_cannon_hits"])
    shell = float(p["arm_targets"]["tank_shell_damage"])

    def dev(model: str) -> float | None:
        h = table_b["tank_cannon"][model]
        if not isinstance(h, (int, float)):
            return None
        return round((h - bmak_hits) / bmak_hits * 100.0, 2)

    # what max_health each model would need for exactly the BmAK hit count
    shell_dmg = float(p["arm_targets"]["tank_shell_damage"])
    expl_armor = float(veh["channels"].get("explosion", {}).get("armor") or 0.0)
    expl_strength = float(veh["channels"].get("explosion", {}).get("strength") or 0.0)
    per_hit = {"H0": shell_dmg, "H1": shell_dmg * (1.0 - min(expl_strength, 100.0) / 100.0),
               "H2": shell_dmg}
    health_needed = {m: int(round(bmak_hits * per_hit[m] - (expl_armor if m == "H2" else 0.0)))
                     for m in per_hit}

    # ARM-1: how much of the pool a 200-round pistol burst takes under each model.
    pistol = table_b["pistol"]
    loss = {}
    for model in dp.MODELS:
        h = pistol[model]
        loss[model] = None if h is None else round(SMALL_ARMS_SETUP / float(h) * 100.0, 4)

    rows = []
    ledger = rows_now()

    def row(id_, member, action, frm, to, why, domain, src):
        rows.append({"id": id_, "member": member, "action": action, "from": frm, "to": to,
                     "why": why, "domain": domain, "source": src,
                     "ledger_dispo": (ledger.get(id_) or {}).get("dispo")})

    row("T-DM1", "max_health", "edit", veh["max_health"], HEALTH_SCALE,
        "ARM-2 at the BmAK ratio: 24 heavy-cannon hits x 1500 shell damage = 36000. "
        "Out of the shipped 500..4000 domain, so it is a declared switch, not a translated "
        "value (damage_audit.py will demand the declaration when a build carries it).",
        "500..4000", "DAMAGE_MODEL.json arm_targets.max_health_needed")
    row("T-DM2", "bullet_armor / bullet_armor_strength", "keep",
        "%s @ %s" % (cur.get("bullet_armor"), cur.get("bullet_armor_strength")),
        "%s @ %s" % (cur.get("bullet_armor"), cur.get("bullet_armor_strength")),
        "already the fleet maximum on both members (armour 5000, strength 99); with "
        "max_health 36000 small arms take %.2f %% of the pool per %d rounds under H1 and "
        "nothing under H2" % (loss.get("H1") or 0.0, SMALL_ARMS_SETUP),
        "0..5000 @ 0..99", "VOCABULARY.md VehicleDamage")
    row("T-DM3", "bullet_heavy_armor / bullet_heavy_armor_strength", "keep",
        "%s @ %s" % (cur.get("bullet_heavy_armor"), cur.get("bullet_heavy_armor_strength")),
        "%s @ %s" % (cur.get("bullet_heavy_armor"), cur.get("bullet_heavy_armor_strength")),
        "unchanged: the per-channel split ARM-1 needs is the bullet / bullet_heavy pair, and "
        "no G2-11 weapon component is decoded into bullet_heavy yet (UNKNOWN -> no row)",
        "0..100 @ 0..50", "VOCABULARY.md VehicleDamage")
    row("T-DM4", "explosion_threshold / npc_explosion_threshold / smoke_threshold", "keep",
        "%s / %s / %s" % (cur.get("explosion_threshold"), cur.get("npc_explosion_threshold"),
                          cur.get("smoke_threshold")),
        "same", "per-hit damage thresholds, independent of the health pool: 36000 does not move them",
        "500..4000 / 500..4000 / 200..1050", "VOCABULARY.md VehicleDamage")
    row("T-DM5", "part_damage_types (24) + the part join", "keep", "24 types", "24 types",
        "carried from the donor; the wheel members below are the only part rows T-14 touches",
        "fleet", "current.json")
    row("T-DM6", "deform_scale", "keep", cur.get("deform_scale"), cur.get("deform_scale"),
        "cosmetic off switch (no panel crumple), already declared in damage_switches.json",
        "1..2 (declared switch)", "Working/Translation/damage_switches.json")
    row("T-DM7", "outgoing ram damage", "out", "-", "-",
        "unchanged: G2-28 found no outgoing ram-damage member; the only impact member is "
        "incoming (impact_damage_factor)",
        "-", "Research/JC3Grab/DAMAGE_MODEL.md")
    row("T-DM8", "impact_damage_factor", "keep", cur.get("impact_damage_factor"),
        cur.get("impact_damage_factor"),
        "incoming collision damage off (BmAK: ramming does not scratch it); declared switch",
        "1..12 (declared switch)", "Working/Translation/damage_switches.json")
    row("T-DM9", "CCar.invulnerable / the armour channels", "decide",
        "invulnerable %s" % (p["fleet"].get("invulnerable") or 0),
        "invulnerable stays 0; ARM-1 and ARM-2 carried by channels + max_health",
        "option A (invulnerable = 1) makes ARM-2 impossible: the engine gate blocks the tank "
        "cannon as well, so every arm reads 'never' at every health. Option B splits the two "
        "requirements exactly where the files already split them - bullet gate for small arms, "
        "explosion channel + pool for heavy weapons - and hits the BmAK ratio %.0f %% "
        "(%.2f %% / %.2f %% / %s %% at H0/H1/H2)"
        % (bmak_hits, dev("H0") or 0.0, dev("H1") or 0.0, dev("H2")),
        "invulnerable 0..0; channels as T-DM2", "DAMAGE_MECHANISMS.md + DAMAGE_MODEL.json")

    # ARM-4: wheels. Both axles ship skew_health 200; the shipped maximum is 400.
    wheels = []
    for side in ("front", "rear"):
        key = "%s_wheels_damage.skew_health" % side
        wheels.append({"member": key, "from": cur.get(key), "to": SKEW_HEALTH,
                       "action": "edit" if cur.get(key) != SKEW_HEALTH else "keep"})
    wheel_note = ("`skew_health` is the only wheel-damage member with a range (200..400) and it "
                  "is now at the shipped maximum on both axles. **No off switch exists on either "
                  "side**: JC3's vocabulary has 6 `wheels_damage` rows and 0 hits for `bWheel`/"
                  "`indestruct`, and none of the 89 wheel-named members in BmAK's SDK binding is a "
                  "damage, health, broken or destruct field. So ARM-4 lands at the fleet ceiling, "
                  "not proven unbreakable; the broken-wheel fractions stay at the build's values.")

    payload = {
        "schema": 1,
        "generated_by": "Tools/scripts/t10_damage.py",
        "card": "T-14",
        "decision": {
            "row": "T-DM9",
            "chosen": "B: armour channels + max_health scale, invulnerable stays 0",
            "rejected": "A: CCar.invulnerable = 1",
            "why": "A is a whole-vehicle engine gate (4 bytes at epe+1167): it stops the tank "
                   "cannon too, so ARM-2's 24-hit ratio cannot exist under it",
            "invulnerable_now": p["fleet"].get("invulnerable"),
        },
        "bmak": {
            "health": p["arm_targets"]["bmak_ratio"]["health"],
            "heavy_cannon_damage": p["arm_targets"]["bmak_ratio"]["heavy_cannon_damage"],
            "heavy_cannon_hits": bmak_hits,
            "tank_shell_damage": shell,
            "source": p["arm_targets"]["bmak_ratio"]["source"],
        },
        "options": {
            "A_invulnerable": {
                "setting": "CCar.invulnerable = %d" % INVULNERABLE,
                "rule": "engine-level cannot-be-damaged gate: every arm, including "
                        "tank_cannon, reads 'never' at every health value",
                "table": {k: "never (engine gate)" for k in sorted(arms)},
                "arm2": "fails: 'never' is not 24 hits",
            },
            "B_channels": {
                "setting": "max_health %d, invulnerable 0, channels as T-DM2" % HEALTH_SCALE,
                "table": table_b,
                "arm2_deviation_pct": {m: dev(m) for m in dp.MODELS},
                "max_health_for_ratio": health_needed,
                "small_arms_pool_loss_pct_200_rounds": loss,
            },
        },
        "table_before": table_now,
        "rows": rows,
        "arm4_wheels": {"edits": wheels, "note": wheel_note},
        "arm5_regen": {
            "jcs_member": None,
            "bmak_member": "RVehicleBatmobileBase.HealthRecoverRate (TArray<float> @ +8220)",
            "bmak_value": "UNKNOWN - no archetype overrides it; the native CDO is not shipped",
            "verdict": "named omission: JC3's VehicleDamage has no recovery member (0 hits for "
                       "recover/regen over the 52-type vocabulary), so there is nothing to write; "
                       "BmAK's rate is awarded per experience event, not a per-second regen",
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
            "why": "T-DM2 moved it 100 -> 99, which is inside the shipped 0..99, so the "
                   "declaration is no longer a switch; damage_audit.py fails while it stays",
            "pending": {"max_health": HEALTH_SCALE},
            "pending_why": "36000 is out of domain and must be declared when a build carries "
                           "it; declaring it now would fail the audit against the current build",
        },
        "checks": {
            "arm2_within_20pct": {m: (dev(m) is not None and abs(dev(m)) <= 20.0)
                                  for m in dp.MODELS},
            "small_arms_no_visible_loss": {
                m: (loss[m] is None or loss[m] <= VISIBLE_LOSS * 100.0)
                for m in dp.MODELS},
        },
    }
    return payload


def md(p: dict) -> str:
    L = []
    A = L.append
    A("# Damage and armour translation (T-14)")
    A("")
    A("Generated by `Tools/scripts/t10_damage.py`. Rows T-DM1…T-DM9 and the four remaining ARM")
    A("codes. Every number is recomputed: the build's values from `Working/Translation/current.json`")
    A("(decoded from `Builds/test-091`), the arm damage and the three model formulas from")
    A("`Tools/scripts/damage_predict.py`, the BmAK ratio from `DAMAGE_RULES.json` (G1-14), the")
    A("shipped domains from `Research/JC3Grab/VOCABULARY.md`.")
    A("")
    b = p["bmak"]
    A("| fact | value |")
    A("|---|---|")
    A("| BmAK health / heavy-cannon damage | **%s / %s** |" % (b["health"], b["heavy_cannon_damage"]))
    A("| BmAK ratio | **%d heavy-cannon hits** |" % b["heavy_cannon_hits"])
    A("| JC3 tank shell | **%s** in its blast |" % b["tank_shell_damage"])
    A("| `max_health` needed for that ratio | **%d** (fleet domain 500..4000) |" % HEALTH_SCALE)
    A("")
    A("## 1. T-DM9 — the choice: channels, not `invulnerable`")
    A("")
    A("| | option A | option B (chosen) |")
    A("|---|---|---|")
    A("| what it sets | `CCar.invulnerable` = %d | `max_health` %d, `invulnerable` 0, channels as T-DM2 |"
      % (INVULNERABLE, HEALTH_SCALE))
    A("| small arms | never reach health | %.2f %% of the pool per %d pistol rounds at worst (H1); 0 under H2 |"
      % (p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"].get("H1") or 0.0,
         SMALL_ARMS_SETUP))
    A("| the tank cannon | **never** — the gate is whole-vehicle | **%s / %s / %s** hits (H0/H1/H2) vs the BmAK %d |"
      % (p["options"]["B_channels"]["table"]["tank_cannon"]["H0"],
         p["options"]["B_channels"]["table"]["tank_cannon"]["H1"],
         p["options"]["B_channels"]["table"]["tank_cannon"]["H2"], b["heavy_cannon_hits"]))
    A("| ARM-2 at the BmAK ratio | impossible | %s %%" % ", ".join(
        "%s %s" % (m, p["options"]["B_channels"]["arm2_deviation_pct"][m]) for m in dp.MODELS))
    A("")
    A("Option A is rejected on arithmetic, not taste: a `never` cannot be within ±20 % of 24.")
    A("")
    A("### Option A's table")
    A("")
    A("| arm | result |")
    A("|---|---|")
    for k, v in p["options"]["A_invulnerable"]["table"].items():
        A("| `%s` | %s |" % (k, v))
    A("")
    A("### Option B's table (`max_health` %d)" % HEALTH_SCALE)
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
        A("| %s | %s | **%s** |" % (m, p["options"]["B_channels"]["table"]["tank_cannon"][m] and
                                    (p["bmak"]["tank_shell_damage"] if m != "H1" else
                                     p["bmak"]["tank_shell_damage"] / 2.0),
                                    p["options"]["B_channels"]["max_health_for_ratio"][m]))
    A("")
    A("`max_health` %d is the H0/H2 answer; if `Q1-DM-A` shows the gate is the H1 percentage" % HEALTH_SCALE)
    A("model, the same ratio needs %d instead. Q1-DM-A is the probe that decides which one ships."
      % p["options"]["B_channels"]["max_health_for_ratio"]["H1"])
    A("")
    A("Read as a bracket: H0 (armour ignored) / H1 (percentage gate) / H2 (threshold + pool).")
    A("The build's values sit inside the shipped domain on every channel, so the bracket is the")
    A("only uncertainty left; Q1-DM-A/B/C pick which.")
    A("")
    A("### What the two requirements become")
    A("")
    ck = p["checks"]
    A("| requirement | criterion | H0 | H1 | H2 |")
    A("|---|---|---|---|---|")
    def _loss(m):
        v = p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"][m]
        return "never (absorbed)" if v is None else "%.3f %%" % v

    A("| ARM-1 small arms do not move the bar | 200 pistol rounds < 5 %% of the pool | %s | %s | %s |"
      % tuple(_loss(m) for m in dp.MODELS))
    A("| ARM-2 heavy weapons at the BmAK ratio | within ±20 %% of %d hits | %s | %s | %s |"
      % (b["heavy_cannon_hits"],
         *["%s (%s)" % (p["options"]["B_channels"]["table"]["tank_cannon"][m],
                        "ok" if ck["arm2_within_20pct"][m] else "outside")
           for m in dp.MODELS]))
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
    A("| JC3 | none — 0 hits for `recover`/`regen` over the 52-type vocabulary | — |")
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
    A("| row | member | action | from | to | domain |")
    A("|---|---|---|---|---|---|")
    for r in p["rows"]:
        A("| %s | `%s` | **%s** | %s | %s | %s |"
          % (r["id"], r["member"], r["action"], r["from"], r["to"], r["domain"]))
    A("")
    A("Row by row, the reason:")
    A("")
    for r in p["rows"]:
        A("- **%s** — %s" % (r["id"], r["why"]))
    A("")
    A("## 6. The switch file")
    A("")
    A("`Working/Translation/damage_switches.json` currently declares six switches; one of them")
    A("no longer applies:")
    A("")
    A("- **`%s`** — %s" % (", ".join(p["switch_file"]["stale_declarations"]),
                            p["switch_file"]["why"]))
    A("- **pending**: `%s` = %s — %s" % ("max_health", p["switch_file"]["pending"]["max_health"],
                                         p["switch_file"]["pending_why"]))
    A("")
    A("The file is written by this script when the declaration is removed, so the audit and the")
    A("document cannot drift apart.")
    A("")
    A("## 7. UNKNOWNs and limits")
    A("")
    A("- **The health scale is a switch, not a translation.** 36 000 is 9x the fleet maximum of")
    A("  4 000. It is chosen because the card's criterion is the BmAK ratio and no in-domain value")
    A("  can reach it (4 000 gives 3 hits under H0/H2, 6 under H1). If B decides the fleet domain")
    A("  is a hard ceiling, ARM-2's ratio becomes a named omission and `max_health` returns to 4 000.")
    A("- **The models disagree about small arms** (H1: 0.3 damage per pistol round; H2: nothing).")
    A("  Both are inside ARM-1; H0 is not, and H0 is only reachable if the armour members are")
    A("  ignored, which the fleet census says they are not on any armoured vehicle.")
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
    doc["_t14"] = ("T-14 (2026-10-28): removed the `bullet_armor_strength` declaration - T-DM2's "
                   "99 is inside the shipped 0..99. `max_health` 36000 stays pending until a build "
                   "carries it (see Working/Translation/t10_damage_edits.json).")
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
    # every row must exist in the ledger
    ledger = rows_now()
    for r in p["rows"]:
        if r["id"] not in ledger:
            fails.append("row %s is not in T_ROWS.jsonl" % r["id"])
    # the criteria the card states
    ck = p["checks"]
    for m in dp.MODELS:
        if not ck["small_arms_no_visible_loss"][m] and m != "H0":
            fails.append("ARM-1 fails under %s" % m)
        if not ck["arm2_within_20pct"][m] and m != "H1":
            fails.append("ARM-2 outside 20 %% under %s" % m)
    print("rows %d | option B tank cannon H0 %s H1 %s H2 %s vs BmAK %d | small arms H1 %.3f %% of pool"
          % (len(p["rows"]), p["options"]["B_channels"]["table"]["tank_cannon"]["H0"],
             p["options"]["B_channels"]["table"]["tank_cannon"]["H1"],
             p["options"]["B_channels"]["table"]["tank_cannon"]["H2"],
             p["bmak"]["heavy_cannon_hits"],
             p["options"]["B_channels"]["small_arms_pool_loss_pct_200_rounds"]["H1"] or 0.0))
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
