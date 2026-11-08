"""missing_rows.py - propose the ledger rows that ALB-2 and T-13 never wrote.

`Working/Translation/LEDGER_AUDIT.md` (GRB-G3-11) found two stretches of work that left no
line in `Working/Translation/T_ROWS.jsonl`: the ALB-2 paint albedo gain (MODLOG §107) and the
T-13 interaction placement (`Working/Translation/T9_INTERACTION.md`).  Both are real, both
produced shipped values, neither is traceable from the ledger.

This tool does **not** edit the ledger and takes **no** translation decision.  It:

  1. proves the gap from `T_ROWS.jsonl` (`--check` fails if a row for either subject appears,
     so the proposal goes stale the moment someone writes the real rows);
  2. lists every value the two subjects used, each classified
       decoded  - a file and the place inside it (JSON pointer / section / package export)
       derived  - a rule plus its inputs, recomputed here
       literal  - hand-entered in the tool or the log, cited by file:line
       decision - a user decision recorded in a file
     and, where a number is computable, recomputes it from the source instead of copying it;
  3. renders the missing rows in the ledger's own row shape
     (`cells = [id, BmAK source, JC3 target, transform, now, proposed, confidence, verify]`,
     `GRAB_BACKLOG.md` §7) with a proposed disposition, so whoever owns the ledger can splice
     them in unchanged.

Refuses to guess: anything not in a file is emitted as UNKNOWN with what was tried.

Usage:
    python Tools/scripts/missing_rows.py --write
    python Tools/scripts/missing_rows.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
AUDIT = os.path.join(WORK, "LEDGER_AUDIT.md")
VALUES = os.path.join(ROOT, "Research", "BatmobileGrab", "VALUES.json")
FACTORS = os.path.join(ROOT, "Tools", "scripts", "factors.py")
T9PY = os.path.join(ROOT, "Tools", "scripts", "t9_interaction.py")
T9JSON = os.path.join(WORK, "t9_interaction.json")
T9MD = os.path.join(WORK, "T9_INTERACTION.md")
INTERACTION = os.path.join(ROOT, "Research", "JC3Grab", "INTERACTION.json")
COCKPIT = os.path.join(ROOT, "Research", "BatmobileGrab", "COCKPIT.md")
MODLOG = os.path.join(ROOT, "MODLOG.md")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
PLAN = os.path.join(ROOT, "MODDING_PLAN.md")
BUILD = os.path.join(ROOT, "Builds", "bm-RC1")

MD_NAME = "MISSING_ROWS.md"
JSON_NAME = "MISSING_ROWS.json"
SCHEMA = 1

# ids this proposal claims; none of them may exist in the ledger
PROPOSED_IDS = ["T-AB1", "T-AB2", "T-AB3",
                "T-IN1", "T-IN2", "T-IN3", "T-IN4", "T-IN5"]
# the FX document already owns the ledger label "T-13" (T13_FX.md, T-17), so the
# interaction rows need a label of their own; see §4 of the render
IN_DOC = "T-13i"


# ------------------------------------------------------------------ small helpers
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def read(p: str) -> str:
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def sha256(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def line_of(path: str, pattern: str) -> int:
    rx = re.compile(pattern)
    for i, ln in enumerate(read(path).splitlines(), 1):
        if rx.search(ln):
            return i
    raise SystemExit(f"missing_rows: {rel(path)} has no line matching {pattern!r}")


def src_line(path: str, pattern: str) -> str:
    """'file:line' for a literal that lives in a tool."""
    return f"{rel(path)}:{line_of(path, pattern)}"


# ------------------------------------------------------------------ sRGB transfer (re-implemented)
def srgb8(c: float) -> tuple[int, str]:
    """linear 0..1 -> 8-bit sRGB, the transform ALB-2 wraps its gain in."""
    c = max(0.0, min(1.0, float(c)))
    s = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return int(round(round(s * 255) / 255 * 255)), "%02x" % int(round(round(s * 255) / 255 * 255))


def hex_bytes(vals) -> str:
    return "0x" + "".join(srgb8(v)[1] for v in vals)


# ------------------------------------------------------------------ ALB-2
def alb2() -> dict:
    vals = json.load(open(VALUES, encoding="utf-8"))
    paint = vals["paint"]
    base = [round(float(x), 6) for x in paint["base_colour"][:3]]
    eff = [round(float(x), 6) for x in paint["effective_base_colour"][:3]]
    gain_now = float(paint["albedo_gain"])
    mod = read(MODLOG)
    # the ALB-2 change line: the literal gain and the byte pair it names
    m_gain = re.search(r"`PAINT_ALBEDO_GAIN = ([0-9.]+)`", mod)
    m_bytes = re.search(r"0x([0-9a-f]{2})/0x([0-9a-f]{2})/0x([0-9a-f]{2}) -> "
                        r"0x([0-9a-f]{2})/0x([0-9a-f]{2})/0x([0-9a-f]{2})", mod)
    if not m_gain or not m_bytes:
        raise SystemExit("missing_rows: MODLOG §107 no longer states the gain and the byte pair")
    gain_lit = float(m_gain.group(1))
    before = tuple(int(m_bytes.group(i), 16) for i in (1, 2, 3))
    after = tuple(int(m_bytes.group(i), 16) for i in (4, 5, 6))

    # the transfer's coefficients must still be the ones in factors.srgb8()
    fac = read(FACTORS)
    for lit in ("12.92", "0.0031308", "1.055", "(1 / 2.4)", "0.055"):
        if lit not in fac:
            raise SystemExit(f"missing_rows: factors.py srgb8 lost the literal {lit!r}")
    if 'ALBEDO_GAIN = VALUES["paint"]["albedo_gain"]' not in fac:
        raise SystemExit("missing_rows: factors.py no longer reads the gain from VALUES.json")

    out_lit = hex_bytes([x * gain_lit for x in eff])
    out_now = hex_bytes([x * gain_now for x in eff])
    # the gain as applied in test-081 must reproduce the byte pair MODLOG records
    if tuple(int(out_lit[i:i + 2], 16) for i in (2, 4, 6)) != after:
        raise SystemExit(f"missing_rows: srgb8(effective x {gain_lit}) = {out_lit}, "
                         f"MODLOG says {after}")
    if tuple(int(out_now[i:i + 2], 16) for i in (2, 4, 6)) == after:
        raise SystemExit("missing_rows: the current gain reproduces the ALB-2 byte; the two "
                         "generations are not distinct, re-read the card")

    # which solid albedo the shipped aaf actually binds
    bound = {"solid_" + out_now[2:]: 0, "solid_" + out_lit[2:]: 0}
    named = {"solid_" + out_now[2:]: [], "solid_" + out_lit[2:]: []}
    aaf = os.path.join(BUILD, "aaf")
    for dirpath, _dirs, files in os.walk(aaf):
        for fn in files:
            p = os.path.join(dirpath, fn)
            if os.path.getsize(p) > 8 << 20:
                continue
            blob = open(p, "rb").read()
            for name in bound:
                if name.encode() in blob:
                    named[name].append(fn)
                    if fn.lower().endswith(".rbm"):
                        bound[name] += 1
    if not bound["solid_" + out_now[2:]]:
        raise SystemExit("missing_rows: no built RBM names the current solid albedo")
    stray = [fn for fn in named["solid_" + out_lit[2:]] if not fn.lower().endswith(".rbm")]

    return {
        "card": "ALB-2", "title": "paint albedo gain",
        "log": {"section": "MODLOG §107", "gain_line": line_of(MODLOG, r"`PAINT_ALBEDO_GAIN = "),
                "bytes_line": line_of(MODLOG, r"0x83/0x7d/0x86")},
        "values": [
            {"value": "base colour [%s, %s, %s, 1.0]" % tuple(paint["base_colour"][:3]),
             "kind": "decoded",
             "source": "`Research/BatmobileGrab/VALUES.json` paint.base_colour, whose own source "
                       "string names `Material0_BaseColour` on the MIC via the parent chain "
                       "(G1-11 / bm_colchain). " + paint["source"]["base_colour"]},
            {"value": "Diffuse_Adjust [2.2, 2.0, 2.0]",
             "kind": "decoded",
             "source": "`Research/BatmobileGrab/VALUES.json` paint.source.base_colour - the "
                       "multiplier is recorded there as the derivation input"},
            {"value": "effective colour [%s, %s, %s]" % tuple(eff),
             "kind": "derived",
             "source": "base x Diffuse_Adjust, 6 dp - `Tools/scripts/grab_values.py` "
                       "(`paint.effective_base_colour`)"},
            {"value": "sRGB EOTF: 12.92c if c<=0.0031308 else 1.055c^(1/2.4)-0.055",
             "kind": "literal",
             "source": src_line(FACTORS, r"s = 12\.92 \* c if c <= 0\.0031308") +
                       " - hand-written in `srgb8()`, not read from any file (the standard's "
                       "piecewise transfer)"},
            {"value": "PAINT_ALBEDO_GAIN = %g" % gain_lit,
             "kind": "literal",
             "source": "`MODLOG.md`:%d (§107) - the one hand-entered number of ALB-2, chosen after "
                       "measuring test-080 (body 12/16 luma vs grass 85; reference car 22/22 vs "
                       "road 12)" % line_of(MODLOG, r"`PAINT_ALBEDO_GAIN = ")},
            {"value": "albedo byte %s (from %s)" % (out_lit, "0x%02x%02x%02x" % before),
             "kind": "derived",
             "source": "srgb8(effective x %g) - reproduces the byte pair `MODLOG.md`:%d records"
                       % (gain_lit, line_of(MODLOG, r"0x83/0x7d/0x86"))},
            {"value": "gain now in force %g" % gain_now,
             "kind": "decoded",
             "source": "`Research/BatmobileGrab/VALUES.json` paint.albedo_gain - " +
                       paint["source"]["albedo_gain"] + " (GRB-6 replaced the hand-set gain)"},
            {"value": "albedo byte now built %s" % out_now,
             "kind": "derived",
             "source": "srgb8(effective x %g)" % gain_now},
            {"value": "built bindings: %s in %d RBM file(s), %s in %d"
                      % ("solid_" + out_now[2:], bound["solid_" + out_now[2:]],
                         "solid_" + out_lit[2:], bound["solid_" + out_lit[2:]]),
             "kind": "decoded",
             "source": "byte scan of `Builds/bm-RC1/aaf` - the paint slot of the shipped "
                       "materials names the current solid; the ALB-2 one is bound by no RBM and "
                       "survives only in the packaging lists (%s)"
                       % (", ".join(stray) or "none")},
        ],
        "literal_gain": gain_lit, "gain_now": gain_now,
        "byte_lit": out_lit, "byte_now": out_now,
        "bound": bound, "effective": eff, "base": base, "stray": stray,
    }


# ------------------------------------------------------------------ T-13 interaction
def py_literal(path: str, name: str) -> tuple[str, int]:
    rx = re.compile(r"^%s = (.+?)(?:\s+#.*)?$" % re.escape(name))
    for i, ln in enumerate(read(path).splitlines(), 1):
        m = rx.match(ln)
        if m:
            return m.group(1).strip(), i
    raise SystemExit(f"missing_rows: {rel(path)} has no top-level {name} = ...")


def t13() -> dict:
    doc = json.load(open(T9JSON, encoding="utf-8"))
    inter = json.load(open(INTERACTION, encoding="utf-8"))
    md = read(T9MD)

    lits = {}
    for name in ("BAND", "SIDE_MARGIN", "SIDE_CLEARANCE", "SIDE_Y", "SIDE_Z",
                 "ROOF_Z", "HOOD_Z", "UP_COS", "DRIVER", "DROP"):
        text, ln = py_literal(T9PY, name)
        lits[name] = {"text": text, "line": ln}
    band = tuple(float(x) for x in re.findall(r"[0-9.]+", lits["BAND"]["text"]))
    if band != (0.05, 0.30):
        raise SystemExit(f"missing_rows: card band moved: {band}")
    clearance_side = float(lits["SIDE_CLEARANCE"]["text"])
    margin = float(lits["SIDE_MARGIN"]["text"])
    side_y, side_z = float(lits["SIDE_Y"]["text"]), float(lits["SIDE_Z"]["text"])
    roof_z, hood_z = float(lits["ROOF_Z"]["text"]), float(lits["HOOD_Z"]["text"])
    driver = tuple(float(x) for x in
                   re.findall(r"-?[0-9.]+", lits["DRIVER"]["text"].split("  #")[0]))

    # ---- the donor clearances, from the grab this placement was built on
    areas = {a["name"]: a for a in inter["stunt_areas"]["areas"]}
    gaps = {k: float(areas[k]["center_gap_m"]) for k in ("front_area", "main_area")}
    # The grab file was regenerated after the placement was built (2026-11-02 vs 2026-10-28), so the
    # digests differ.  Reconcile on the inputs the placement actually used instead of trusting either
    # digest: same object count, same two donor gaps.  Anything else is a fail.
    digests = {"build": doc["source_digest"], "current": inter["digest"],
               "reconciled": doc["source_digest"] == inter["digest"]}
    if not digests["reconciled"]:
        if len(inter["points"]) != doc["counts"]["objects"]:
            raise SystemExit("missing_rows: the regenerated grab has a different object count")
        for kind, area in (("hood", "front_area"), ("roof", "main_area")):
            if abs(float(doc["anchors"][kind]["donor_gap_m"]) - gaps[area]) > 1e-9:
                raise SystemExit(f"missing_rows: {area} gap moved between grab digests")

    # ---- the placement as shipped, re-derived from the object rows
    rows = doc["objects"]
    placed = [r for r in rows if r["disposition"] == "placed"]
    dropped = [r for r in rows if str(r["disposition"]).startswith("dropped")]
    socket = [r for r in rows if r["disposition"] == "socket"]
    unknown = [r for r in rows if r["disposition"] == "unknown"]
    if (len(rows), len(placed), len(dropped), len(socket), len(unknown)) != (85, 77, 6, 1, 1):
        raise SystemExit("missing_rows: the placement's counts moved")
    for r in dropped:
        if not any(k in r["name"] for k in ("pull.out", "pulled.out")):
            raise SystemExit(f"missing_rows: {r['name']} dropped without a D-9 reason")
    inband = [r for r in placed
              if band[0] <= r["measure"]["nearest_m"] <= band[1] and not r["measure"]["inside"]]
    if len(inband) != len(placed):
        raise SystemExit("missing_rows: a placed object left the card's band")

    # every transform == anchor surface + normal x clearance (4 dp)
    for r in placed:
        a, cl, t = r["anchor"], r["clearance"], r["transform"]
        for k in range(3):
            want = a["surface"][k] + a["normal"][k] * cl["m"]
            if abs(round(want, 4) - t["pos_m"][k]) > 2e-4:
                raise SystemExit(f"missing_rows: {r['name']} pos {k} is not surface+normal*clearance")
        fwd = t["forward"]
        yaw = round(__import__("math").degrees(__import__("math").atan2(fwd[0], -fwd[2])), 3)
        if abs(yaw - t["yaw_deg"]) > 2e-3:
            raise SystemExit(f"missing_rows: {r['name']} yaw is not atan2(forward.x,-forward.z)")

    anchors = doc["anchors"]
    clear = {k: sorted({r["clearance"]["m"] for r in placed if r["anchor"]["kind"] == k})
             for k in anchors}
    kinds = {k: sorted({r["clearance"].get("source") for r in placed
                        if r["anchor"]["kind"] == k}) for k in anchors}
    for k in ("hood", "roof"):
        if any("decoded" not in s for s in kinds[k]):
            raise SystemExit(f"missing_rows: {k} clearance is no longer donor-decoded")
    for k in ("left", "right"):
        if any("chosen" not in s for s in kinds[k]):
            raise SystemExit(f"missing_rows: {k} clearance is no longer marked chosen")

    # the render's own text must still say the side clearance is chosen
    if "0.1 m - chosen" not in md or "UNKNOWN" not in md:
        raise SystemExit("missing_rows: T9_INTERACTION.md no longer labels the side clearance")

    return {
        "card": "T-13", "title": "interaction placement", "doc": rel(T9MD),
        "grab_digest": doc["source_digest"], "grab_file": rel(INTERACTION),
        "grab_digests": digests,
        "mesh": doc["mesh"], "counts": doc["counts"], "decision": doc["decision"],
        "band": list(band), "margin": margin, "side_clearance": clearance_side,
        "stations": {"side_y": side_y, "side_z": side_z, "roof_z": roof_z, "hood_z": hood_z},
        "driver": list(driver), "gaps": gaps,
        "anchors": anchors, "clearances": clear, "kinds": kinds,
        "objects": len(rows), "placed": len(placed), "dropped": len(dropped),
        "socket": len(socket), "unknown": len(unknown), "in_band": len(inband),
        "lits": lits,
        "values": [
            {"value": "grab digests: build %s, file now %s"
                      % (digests["build"], digests["current"]),
             "kind": "decoded",
             "source": "`%s` source_digest (recorded at build time) vs `%s` digest (regenerated "
                       "2026-11-02); reconciled here on the inputs used - %d objects and the two "
                       "donor gaps agree" % (rel(T9JSON), rel(INTERACTION), len(inter["points"]))},
            {"value": "clearance band %g..%g m" % band,
             "kind": "literal",
             "source": "the card's Done rule (`GRAB_BACKLOG.md` T-13: \"nearest hull triangle >= "
                       "0.05 m and <= 0.3 m\"), encoded at " + src_line(T9PY, r"^BAND = ")},
            {"value": "donor stunt-area gaps: front_area %g m, main_area %g m"
                      % (gaps["front_area"], gaps["main_area"]),
             "kind": "decoded",
             "source": "`%s` stunt_areas.areas[*].center_gap_m (grab digest %s, G2-18) - the only "
                       "donor clearances any decoded file carries"
                       % (rel(INTERACTION), inter["digest"])},
            {"value": "SIDE_MARGIN = %g m" % margin,
             "kind": "literal",
             "source": src_line(T9PY, r"^SIDE_MARGIN = ") +
                       " - band floor + 10 mm so a re-measure stays above 0.05"},
            {"value": "hood clearance %s m (target %g)"
                      % (", ".join("%g" % x for x in clear["hood"]),
                         max(gaps["front_area"], margin)),
             "kind": "derived",
             "source": "target = max(donor gap %g, SIDE_MARGIN %g), then the normal offset is "
                       "solved so the nearest hull triangle is exactly that far away "
                       "(`solve_offset`, 4 mm tolerance)" % (gaps["front_area"], margin)},
            {"value": "roof clearance %s m (target %g)"
                      % (", ".join("%g" % x for x in clear["roof"]),
                         max(gaps["main_area"], margin)),
             "kind": "derived",
             "source": "same rule with the main_area gap %g m" % gaps["main_area"]},
            {"value": "SIDE_CLEARANCE = %g m (chosen, not decoded)" % clearance_side,
             "kind": "literal",
             "source": src_line(T9PY, r"^SIDE_CLEARANCE = ") +
                       " - the donor's side clearance is in no decoded file (G2-18 decoded only "
                       "the three stunt areas), so the value sits inside the card band and is "
                       "labelled chosen in `%s` §2 and §6" % rel(T9MD)},
            {"value": "side clearance as solved: left %s m, right %s m"
                      % (", ".join("%g" % x for x in clear["left"]),
                         ", ".join("%g" % x for x in clear["right"])),
             "kind": "derived",
             "source": "the chosen %g m pushed along the anchor normal and re-measured against the "
                       "hull (target 0.10, solved offset %s)"
                       % (clearance_side, clear["right"])},
            {"value": "stations: SIDE_Y %g, SIDE_Z %g, ROOF_Z %g, HOOD_Z %g"
                      % (side_y, side_z, roof_z, hood_z),
             "kind": "literal",
             "source": "%s, %s, %s, %s - each chosen inside a decoded range: the tub y 0.676..2.029 "
                       "and the `Driver` z in `COCKPIT.md` §2/§3, and the front-deck z of G2-18's "
                       "front_area centre"
                       % (src_line(T9PY, r"^SIDE_Y = "), src_line(T9PY, r"^SIDE_Z = "),
                          src_line(T9PY, r"^ROOF_Z = "), src_line(T9PY, r"^HOOD_Z = "))},
            {"value": "anchor surfaces: hood %s, roof %s, left %s, right %s"
                      % (anchors["hood"]["surface"], anchors["roof"]["surface"],
                         anchors["left"]["surface"], anchors["right"]["surface"]),
             "kind": "derived",
             "source": "ray cast against `%s` (%d triangles, %d vertices, bbox %s..%s): topmost "
                       "body hit on a vertical ray at (x, z), first hit on a horizontal ray at "
                       "(y, z) - `top_hit`/`side_hit` in `%s`"
                       % (doc["mesh"]["file"], doc["mesh"]["triangles"], doc["mesh"]["vertices"],
                          doc["mesh"]["bbox"][0], doc["mesh"]["bbox"][1], rel(T9PY))},
            {"value": "Driver socket %s m, forward (0, 0, -1)" % (list(driver),),
             "kind": "decoded",
             "source": "`%s` §2 `Driver` socket: bone `Batmobile_Chassis`, (121.9658, 0.25, "
                       "84.25) cm in the bone frame through the one `bat_assemble` transform "
                       "(G1-19, `grab_cockpit.py`)" % rel(COCKPIT)},
            {"value": "UP_COS = cos(%s)" % lits["UP_COS"]["text"].split("(")[-1].rstrip(")"),
             "kind": "literal",
             "source": src_line(T9PY, r"^UP_COS = ") + " - the card's \"normals within 20 deg of "
                       "up\", a card constant, not a game number"},
            {"value": "%d objects: %d placed, %d dropped, %d socket, %d unknown, %d in band"
                      % (len(rows), len(placed), len(dropped), len(socket), len(unknown), len(inband)),
             "kind": "derived",
             "source": "`classify()` in `%s` applied to the %d donor objects of `%s`, then the "
                       "band/inside test against the hull"
                       % (rel(T9PY), inter["counts"]["objects"], rel(INTERACTION))},
            {"value": "D-9 = no: hijack objects dropped (%s)"
                      % [r["name"] for r in dropped],
             "kind": "decision",
             "source": "`%s` decision block - \"%s\"; user decision 2026-10-28, `GRAB_BACKLOG.md` "
                       "§D-9" % (rel(T9JSON), doc["decision"]["status"])},
            {"value": "transform rule: pos = anchor surface + normal x clearance; forward "
                      "(0,0,-1) on hood/roof, (-normal.x,0,0) on the sides; yaw = "
                      "atan2(forward.x, -forward.z)",
             "kind": "derived",
             "source": "`%s` §2 (frame) and §6 (yaw convention) - verified here for all %d "
                       "placed objects" % (rel(T9MD), len(placed))},
            {"value": "seat.passenger1: no transform",
             "kind": "unknown",
             "source": "`COCKPIT.md` §1 - one cockpit tub, one seat, so there is no passenger-seat "
                       "location to place it on"},
        ],
    }


# ------------------------------------------------------------------ the gap
def gap(alb: dict, intr: dict) -> dict:
    rows = [json.loads(l) for l in read(LEDGER).splitlines() if l.strip()]
    ids = {r["id"] for r in rows}
    hit = [i for i in PROPOSED_IDS if i in ids]
    if hit:
        raise SystemExit(f"missing_rows: the ledger already has {hit} - the proposal is stale")
    t13 = [r for r in rows if r["doc"] == "T-13"]
    fx = [r for r in t13 if r["id"].startswith("T-FX")]
    if not t13 or len(fx) != len(t13):
        raise SystemExit("missing_rows: the ledger's doc T-13 is no longer FX-only")
    already = [r["id"] for r in rows if r["doc"] == IN_DOC]
    if already:
        raise SystemExit(f"missing_rows: doc {IN_DOC} already has rows {already}")

    def mentions(*words):
        out = []
        for r in rows:
            blob = json.dumps(r, ensure_ascii=False).lower()
            if any(w in blob for w in words):
                out.append(r["id"])
        return out

    # "interaction" also matches `WaterInteraction.will_sink` (T-WLD13), a different sense
    inter_mentions = mentions("interaction object", "interaction.seat", "pull.out")
    alb_mentions = mentions("albedo_gain")
    if "GRB-6" not in read(PLAN):
        raise SystemExit("missing_rows: GRB-6 is not a card any more (MODDING_PLAN.md)")
    audit = read(AUDIT)
    m = re.search(r"\| T-13 \| (\d+) \| (\d+) \| (\d+) \|", audit)
    if not m:
        raise SystemExit("missing_rows: LEDGER_AUDIT.md no longer tabulates doc T-13")
    aud = tuple(int(m.group(i)) for i in (1, 2, 3))
    if sum(aud) != len(t13):
        raise SystemExit("missing_rows: the audit's T-13 counts and the ledger disagree")
    return {
        "ledger": rel(LEDGER), "ledger_rows": len(rows), "ledger_sha256": sha256(LEDGER),
        "proposed_ids_absent": PROPOSED_IDS,
        "doc_T13_rows": len(t13), "doc_T13_fx_rows": len(fx),
        "audit_T13_tiers": {"TRANSLATED": aud[0], "GUESSED": aud[1], "NOT_TRANSLATED": aud[2]},
        "doc_T13i_rows": 0,
        "interaction_mentions": sorted(set(inter_mentions)),
        "albedo_mentions": sorted(set(alb_mentions)),
        "note": "the only ledger rows that mention the interaction placement are T-20 rows that "
                "point at it (T-WLD8); no row carries its values, and no row carries the ALB-2 "
                "gain at all",
    }


# ------------------------------------------------------------------ the proposed rows
def rows(alb: dict, intr: dict) -> list[dict]:
    out = [
        {"id": "T-AB1", "doc": "T-2b",
         "section": "1. Appearance - 185 materials, 405 textures, 19 slots",
         "cells": ["T-AB1",
                   "BmAK authors the paint for a rain-wet night scene (linear luma 0.0533); on "
                   "JC3's shaded side it is the darkest object in a bright scene",
                   "the generated solid albedo `s0` of every paint block",
                   "linear colour x `PAINT_ALBEDO_GAIN` **before** sRGB encoding",
                   "0x43/0x40/0x45 (test-079/080, gain 1.0)",
                   "0x83/0x7d/0x86 (gain %g, test-081)" % alb["literal_gain"],
                   "literal",
                   "daylight screenshot: body luma above the road (MODLOG §107 measured 12/16 vs "
                   "grass 85; reference 22/22 vs road 12)"],
         "dispo": "superseded", "superseded_by": "GRB-6",
         "why": "GRB-6 removed the hand-set gain: VALUES.json now carries %g, the vanilla paint "
                "luma / authored paint luma ratio, and factors.py reads only that file"
                % alb["gain_now"]},
        {"id": "T-AB2", "doc": "T-2b",
         "section": "1. Appearance - 185 materials, 405 textures, 19 slots",
         "cells": ["T-AB2",
                   "authored paint colour `Material0_BaseColour` = [0.02579, 0.02579, 0.03] linear "
                   "x `Diffuse_Adjust` [2.2, 2.0, 2.0]",
                   "the paint colour the gain and the sRGB encode are applied to",
                   "x `Diffuse_Adjust`, then x gain, then sRGB encode",
                   "effective [%.6g, %.6g, %.6g]" % tuple(alb["effective"]),
                   "unchanged: the same effective colour, now scaled by the derived gain",
                   "decoded",
                   "074/078/079/080/081 all encode from this colour; the gain is the only variable "
                   "that ever moved"],
         "dispo": "keep",
         "why": "the input colour is decoded and unchanged; only the gain applied to it moved "
                "(T-AB1) - the build carries it"},
        {"id": "T-AB3", "doc": "T-2b",
         "section": "1. Appearance - 185 materials, 405 textures, 19 slots",
         "cells": ["T-AB3",
                   "the authored colour is a night value; the 8-bit sRGB albedo is what the engine "
                   "samples",
                   "`CarPaintMM` s0 Diffuse of the 17 body blocks",
                   "srgb8(effective x gain)",
                   "%s (ALB-2)" % alb["byte_lit"],
                   "%s (%d RBM files bind it; %s is bound by no RBM, only by the packaging lists)"
                   % (alb["byte_now"], alb["bound"]["solid_" + alb["byte_now"][2:]],
                      "solid_" + alb["byte_lit"][2:]),
                   "derived",
                   "noon screenshot: paint readable, not black (078 failed), not grey (ALB-2's "
                   "over-correction)"],
         "dispo": "superseded", "superseded_by": "GRB-6",
         "why": "the built materials now name %s (%d files); %s is a stale texture in the same "
                "build - a row stating the ALB-2 byte would describe an unused file"
                % ("solid_" + alb["byte_now"][2:], alb["bound"]["solid_" + alb["byte_now"][2:]],
                   "solid_" + alb["byte_lit"][2:])},
    ]
    side = intr["clearances"]
    out += [
        {"id": "T-IN1", "doc": IN_DOC, "section": "5. The Done rule",
         "cells": ["T-IN1",
                   "every donor interaction object sits on the Serpente shell; the gap to the "
                   "skin is the quantity that has to survive the body swap",
                   "the 77 placed `entry/exit/transition/point/trigger/seat` objects of the "
                   "Batmobile `.epe`",
                   "nearest hull triangle >= %g m and <= %g m, point outside the hull"
                   % tuple(intr["band"]),
                   "0 rows in the ledger; the rule lives only in `%s` §5" % intr["doc"],
                   "%d/%d placed objects inside the band, 0 inside the hull"
                   % (intr["in_band"], intr["placed"]),
                   "literal",
                   "Q-1 #3: Rico enters from both sides; re-measure the %d transforms against "
                   "body_lod1" % intr["placed"]],
         "dispo": "epe",
         "why": "the placement is an entity-graph edit (%d transforms in the `.epe`, written by "
                "B-05); the band is the card's Done rule" % intr["placed"]},
        {"id": "T-IN2", "doc": IN_DOC, "section": "2. Method",
         "cells": ["T-IN2",
                   "G2-18 decoded the donor's gap to the shell for the three stunt areas only: "
                   "front_area %g m, main_area %g m" % (intr["gaps"]["front_area"],
                                                        intr["gaps"]["main_area"]),
                   "hood anchors (`*hood*`) and roof anchors (`*stunt*`)",
                   "target = max(donor gap, %g m), then solve the normal offset against the hull"
                   % intr["margin"],
                   "no ledger row; the numbers exist only in `%s` §2" % intr["doc"],
                   "hood %s m, roof %s m" % (", ".join("%g" % x for x in side["hood"]),
                                             ", ".join("%g" % x for x in side["roof"])),
                   "decoded + derived",
                   "hood/roof objects read 0.0573/0.1453 m from the hull and stay in band "
                   "(`%s` §4)" % intr["doc"]],
         "dispo": "epe",
         "why": "donor-decoded clearances, solved onto the Batmobile shell; written by B-05"},
        {"id": "T-IN3", "doc": IN_DOC, "section": "2. Method",
         "cells": ["T-IN3",
                   "the donor's side clearance is in no decoded file (G2-18 decoded the stunt "
                   "areas only)",
                   "left/right cockpit-side anchors at y %g, z %g"
                   % (intr["stations"]["side_y"], intr["stations"]["side_z"]),
                   "a chosen %g m inside the band, pushed along the surface normal"
                   % intr["side_clearance"],
                   "no ledger row; labelled chosen in `%s` §2/§6" % intr["doc"],
                   "left %s m, right %s m (chosen, not decoded)"
                   % (", ".join("%g" % x for x in side["left"]),
                      ", ".join("%g" % x for x in side["right"])),
                   "literal",
                   "side objects read ~0.097/0.100 m from the hull and stay in band"],
         "dispo": "epe",
         "why": "the only unsourced number of the placement, declared as chosen; B-05 writes it"},
        {"id": "T-IN4", "doc": IN_DOC, "section": "1. Decision applied",
         "cells": ["T-IN4",
                   "the Serpente's 85 interaction objects include hijack and passenger-seat "
                   "objects the Batmobile has no place for",
                   "`interaction.seat.driver` (the `Driver` socket) and 6 hijack objects",
                   "D-9 = no: `*pull.out*`/`*pulled.out*` dropped; the seat uses the decoded "
                   "socket %s m" % (intr["driver"],),
                   "no ledger row; `%s` records the decision and the socket" % intr["doc"],
                   "%d dropped, %d socket, %d UNKNOWN (`seat.passenger1`, one-seat cockpit)"
                   % (intr["dropped"], intr["socket"], intr["unknown"]),
                   "decision + decoded",
                   "hijack interactions absent in game; the seated pose starts at the socket "
                   "(COCKPIT.md §2)"],
         "dispo": "epe",
         "why": "user decision 2026-10-28 (D-9) plus the CAP-19 socket; B-05 writes the graph"},
        {"id": "T-IN5", "doc": IN_DOC, "section": "4. Every object",
         "cells": ["T-IN5",
                   "the donor objects carry world positions that are mostly inherited container "
                   "origins (70 of 85), so they are placed by role, not copied",
                   "each placed object's transform (pos, forward, up, yaw)",
                   "pos = anchor surface + normal x clearance; forward (0,0,-1) on hood/roof, "
                   "(-normal.x,0,0) on the sides; yaw = atan2(forward.x, -forward.z)",
                   "no ledger row; the rule is prose in `%s` §2/§6" % intr["doc"],
                   "%d transforms re-derived and checked" % intr["placed"],
                   "derived",
                   "every transform re-derives from its anchor at 4 dp (`missing_rows.py "
                   "--check`)"],
         "dispo": "epe",
         "why": "the placement rule, not a single value; recorded so a later edit cannot move an "
                "anchor silently"},
    ]
    for r in out:
        if len(r["cells"]) != 8:
            raise SystemExit(f"missing_rows: {r['id']} has {len(r['cells'])} cells, not 8")
    return out


# ------------------------------------------------------------------ render
def render(alb: dict, intr: dict, g: dict, rws: list[dict]) -> tuple[str, dict]:
    L = []
    A = L.append
    A("# Missing ledger rows - ALB-2 and T-13 (proposal)")
    A("")
    A("Generated by `Tools/scripts/missing_rows.py --write`; `--check` re-derives every number")
    A("below from the source files and fails on drift. **The ledger is not touched**: no row here")
    A("is in `Working/Translation/T_ROWS.jsonl`, and no translation decision is taken - the")
    A("disposition each row carries is a *proposal* for whoever owns the ledger.")
    A("")
    A("## The gap, measured")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| ledger rows | %d (`sha256 %s...`) |" % (g["ledger_rows"], g["ledger_sha256"][:16]))
    A("| rows with `doc` = `T-13` | %d - all of them `T-FX*` (the T-17 effects document "
      "`T13_FX.md`) |" % g["doc_T13_rows"])
    A("| rows with `doc` = `%s` | 0 |" % IN_DOC)
    A("| proposed ids already in the ledger | 0 (`%s`) |" % ", ".join(PROPOSED_IDS))
    A("| ledger rows mentioning an interaction object / `pull.out` | %s |"
      % (", ".join("`%s`" % i for i in g["interaction_mentions"]) or "none"))
    A("| ledger rows carrying the albedo gain | %s |"
      % (", ".join("`%s`" % i for i in g["albedo_mentions"]) or "none"))
    A("")
    A("`LEDGER_AUDIT.md` tabulates doc `T-13` as %d/%d/%d (translated/guessed/not translated); "
      "those 17 rows are the"
      % (g["audit_T13_tiers"]["TRANSLATED"], g["audit_T13_tiers"]["GUESSED"],
         g["audit_T13_tiers"]["NOT_TRANSLATED"]))
    A("effects rows, so the audit's \"T-13\" and the interaction card of the same name are two")
    A("different subjects. The interaction card's values reach the ledger only as prose inside")
    A("`T-WLD8` (a T-20 world row that points at the placement), and ALB-2 reaches it nowhere.")
    A("")
    A("## 1. ALB-2 - every value it used")
    A("")
    A("| value | kind | source |")
    A("|---|---|---|")
    for v in alb["values"]:
        A("| %s | %s | %s |" % (v["value"], v["kind"], v["source"]))
    A("")
    A("The one hand-entered number is `PAINT_ALBEDO_GAIN = %g`; everything downstream of it is "
      "arithmetic."
      % alb["literal_gain"])
    A("`MAT-1` (gloss 0.45), the glass tint and the metallic channel are **not** part of ALB-2 and "
      "are not")
    A("listed here (the log is explicit that ALB-2 touched only the generated solid albedos).")
    A("")
    A("## 2. T-13 interaction - every value it used")
    A("")
    A("| value | kind | source |")
    A("|---|---|---|")
    for v in intr["values"]:
        A("| %s | %s | %s |" % (v["value"], v["kind"], v["source"]))
    A("")
    A("Placed objects by anchor (the whole table is in `%s` §4):" % intr["doc"])
    A("")
    A("| anchor | clearance (m) | source | objects |")
    A("|---|---|---|---|")
    for k in ("hood", "roof", "left", "right"):
        n = sum(1 for r in json.load(open(T9JSON, encoding="utf-8"))["objects"]
                if r["anchor"] and r["anchor"].get("kind") == k)
        A("| `%s` | %s | %s | %d |" % (k, ", ".join("%g" % x for x in intr["clearances"][k]),
                                       intr["kinds"][k][0], n))
    A("")
    A("## 3. The proposed rows")
    A("")
    A("Cells are the ledger's shape: `[id, BmAK source, JC3 target, transform, now, proposed, "
      "confidence, verify]`.")
    A("")
    for r in rws:
        A("### `%s` (%s, proposed `%s`)" % (r["id"], r["doc"], r["dispo"]))
        A("")
        A("* section: %s" % r["section"])
        A("* why: %s" % r["why"])
        if r.get("superseded_by"):
            A("* `superseded_by`: `%s` - the card is `MODDING_PLAN.md`:%d ('Re-derive every "
              "constant the pipeline currently hardcodes ... delete the manual constants', DONE); "
              "the ledger's `SUPERSEDED` table needs the entry before the row can be spliced in"
              % (r["superseded_by"], line_of(PLAN, r"\| \*\*GRB-6\*\* .* Re-derive every")))
        A("")
        A("| cell | text |")
        A("|---|---|")
        for name, cell in zip(("id", "BmAK source", "JC3 target", "transform", "now", "proposed",
                               "confidence", "verify"), r["cells"]):
            A("| %s | %s |" % (name, cell))
        A("")
    A("## 4. Why the interaction rows use the doc label `%s`" % IN_DOC)
    A("")
    A("`t_rows.py` parses `T13_FX.md` under the tag `T-13`, and that document already owns 17")
    A("rows. `t9_interaction.py` also stamps its output `\"card\": \"T-13\"` because the backlog")
    A("calls the interaction card T-13 (`GRAB_BACKLOG.md` §7). Writing the interaction rows with")
    A("`doc` = `T-13` would merge two cards in every per-document count, so this proposal labels")
    A("them `" + IN_DOC + "`. That is a bookkeeping choice, not a translation decision: if the "
      "ledger owner")
    A("prefers to re-tag the FX rows as `T-17`, the same eight rows splice in unchanged with")
    A("`doc` = `T-13`.")
    A("")
    A("## 5. What would make this proposal wrong")
    A("")
    A("* A row with one of the proposed ids appears in `T_ROWS.jsonl` - `--check` fails.")
    A("* Doc `%s` gains rows, or the ledger's `T-13` gains a non-`T-FX` row - `--check` fails."
      % IN_DOC)
    A("* `VALUES.json`'s gain, `MODLOG` §107's literal, or either transfer byte pair changes - "
      "`--check` fails.")
    A("* `t9_interaction.py`'s constants (band, clearances, stations, socket) or its counts move -")
    A("  `--check` fails.")
    A("* A placed transform stops equalling `surface + normal x clearance`, or a yaw stops being")
    A("  `atan2(forward.x, -forward.z)` - `--check` fails.")
    A("")
    A("## 6. UNKNOWNs")
    A("")
    A("* **The donor's side clearance** (left/right). G2-18 decoded the stunt areas only, so the")
    A("  side value is the chosen %g m and is labelled chosen, not decoded." % intr["side_clearance"])
    A("* **A per-side station spread.** One station per side (y %g, z %g); the donor's world "
      "positions are" % (intr["stations"]["side_y"], intr["stations"]["side_z"]))
    A("  mostly inherited container origins (70 of 85), so there is nothing finer to copy.")
    A("* **Which gain a future build will use.** The ledger row for ALB-2 can only state what")
    A("  ALB-2 did (%g); GRB-6's derived %g is a different card and is already covered by `T-MA3`."
      % (alb["literal_gain"], alb["gain_now"]))
    A("  Note `T-MA3`'s own cells pair the derived gain with the ALB-2 byte pair (%s), which no "
      "gain reproduces;" % alb["byte_lit"])
    A("  this proposal does not edit that row, it only records the arithmetic.")
    A("* **The exact luma operands behind %g.** VALUES.json's source string quotes them at 4 dp "
      "(0.1837 / 0.0533" % alb["gain_now"])
    A("  = %g), so the unrounded operands are not recoverable from that file - recorded as decoded, "
      "not derived." % (0.1837 / 0.0533))
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/missing_rows.py --write")
    A("python Tools/scripts/missing_rows.py --check")
    A("```")
    A("")
    md = "\n".join(L) + "\n"

    doc = {
        "schema": SCHEMA, "generator": "missing_rows.py",
        "subjects": ["ALB-2", "T-13"],
        "gap": g,
        "alb2": {k: alb[k] for k in ("card", "title", "log", "literal_gain", "gain_now",
                                      "byte_lit", "byte_now", "bound", "values")},
        "t13": {k: intr[k] for k in ("card", "title", "doc", "grab_digest", "grab_file",
                                      "grab_digests", "mesh",
                                      "counts", "decision", "band", "margin", "side_clearance",
                                      "stations", "driver", "gaps", "anchors", "clearances",
                                      "kinds", "objects", "placed", "dropped", "socket",
                                      "unknown", "in_band", "values")},
        "rows": rws,
        "ledger_untouched": True,
    }
    return md, doc


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("use --write or --check")

    alb = alb2()
    intr = t13()
    g = gap(alb, intr)
    rws = rows(alb, intr)
    md, doc = render(alb, intr, g, rws)

    md_path = os.path.join(WORK, MD_NAME)
    json_path = os.path.join(WORK, JSON_NAME)
    if a.write:
        with open(md_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(json_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"wrote {rel(md_path)} ({md.count(chr(10))} lines)")
        print(f"wrote {rel(json_path)}")
        print("proposed rows: %d (%s)" % (len(rws), ", ".join(r["id"] for r in rws)))
        print("ledger rows %d, none of the proposed ids present; ledger not modified"
              % g["ledger_rows"])
        return 0

    fails = []
    if not os.path.exists(md_path) or not os.path.exists(json_path):
        fails.append("outputs missing - run --write")
    else:
        if read(md_path) != md:
            fails.append(f"{MD_NAME} differs from a fresh render")
        if json.load(open(json_path, encoding="utf-8")) != doc:
            fails.append(f"{JSON_NAME} differs from a fresh render")
    # the ledger must still be missing the rows (this is the proposal's whole premise)
    if g["doc_T13i_rows"] or any(i in {r["id"] for r in
                                       (json.loads(l) for l in read(LEDGER).splitlines() if l.strip())}
                                 for i in PROPOSED_IDS):
        fails.append("the ledger now has the rows - retire this proposal")
    print("OK: ledger %d rows, doc T-13 = %d FX rows, doc %s = 0"
          % (g["ledger_rows"], g["doc_T13_fx_rows"], IN_DOC))
    print("OK: ALB-2 gain %g -> %s (literal, MODLOG:%d); current gain %g -> %s in %d RBM(s); "
          "ALB-2 byte bound by %d RBM(s), named only in %s"
          % (alb["literal_gain"], alb["byte_lit"], alb["log"]["gain_line"], alb["gain_now"],
             alb["byte_now"], alb["bound"]["solid_" + alb["byte_now"][2:]],
             alb["bound"]["solid_" + alb["byte_lit"][2:]], ", ".join(alb["stray"]) or "none"))
    print("OK: T-13 %d objects, %d placed all in %g..%g m, %d dropped, %d socket, %d unknown; "
          "side clearance %g chosen"
          % (intr["objects"], intr["placed"], intr["band"][0], intr["band"][1],
             intr["dropped"], intr["socket"], intr["unknown"], intr["side_clearance"]))
    print("OK: 8 proposed rows (%s), each 8 cells" % ", ".join(r["id"] for r in rws))
    for f in fails:
        print("FAIL", f)
    if not fails:
        print("CHECK_EXIT=0")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
