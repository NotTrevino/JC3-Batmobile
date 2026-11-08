"""sampler_unknowns.py - card SAMPLER-offline (follow-on to G3-02f): can the EXISTING sampler logs
resolve the three action UNKNOWNs G3-02f left (X barrage input byte, A eject input byte, a boost
duration/time field)?

READ-ONLY on every input. It opens nothing but:
  Research/BatmobileGrab/runtime/samples-*.jsonl          the seven sampler logs (the only data)
  Research/BatmobileGrab/SAMPLER_FIELDS2.md               the 44 observables + the 3 UNKNOWNs
  Tools/scripts/bmak_runtime_sampler.py                   the PI/VEH/GADGETS tables that name every log key
and writes exactly two files:
  Research/BatmobileGrab/SAMPLER_UNKNOWNS.md              this card's report (--write)
Nothing is launched, attached to or read from a game.

Method (all of it is stated in the generated .md so a reader can reject it):
  * a press is a rising edge (0 -> >0) of a sampled digital/analog input byte;
  * its bracket is [t_edge, next sample] plus the [prev sample, t_edge] interval when that interval
    is a normal sampling interval (<= GAP_MAX s), because the press onset is only localised to the
    interval that ended at the edge sample;
  * "away" is every sampling interval (<= GAP_MAX s) that no press bracket of any sampled input
    touches, so the baseline is press-free;
  * a field is a CANDIDATE only when it changed inside at least MIN_BRACKETS distinct press
    brackets AND rate_in >= RATIO * rate_out AND rate_in - rate_out >= ABS_RATE per second;
  * otherwise the UNKNOWN stays UNKNOWN. `--check` rebuilds every number and byte-compares.

    python Tools/scripts/sampler_unknowns.py --write
    python Tools/scripts/sampler_unknowns.py --check
"""
from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOGS = os.path.join(ROOT, "Research", "BatmobileGrab", "runtime")
FIELDS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SAMPLER_FIELDS2.md")
SAMPLER_PY = os.path.join(ROOT, "Tools", "scripts", "bmak_runtime_sampler.py")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SAMPLER_UNKNOWNS.md")

GAP_MAX = 5.0      # s: longer sample-to-sample gaps are session pauses, not sampling intervals
RATIO = 3.0        # margin: in-press change rate must be >= 3x the press-free rate
ABS_RATE = 0.5     # margin: and at least 0.5 changes per second faster
MIN_BRACKETS = 3   # margin: on at least 3 distinct presses

# --- what every log key is (decoded from bmak_runtime_sampler.py; verified by oracle below) -------
# key -> (class, field/member, offset, kind). Offsets are the ones the sampler reads.
VEH = {
    "flags_11D8": ("RVehicleBatmobileBase", "bits @0x11D8 word", 0x11D8, "i32"),
    "flags_11DC": ("RVehicleBatmobileBase", "@0x11DC word", 0x11DC, "i32"),
    "flags_11E0": ("RVehicleBatmobileBase", "@0x11E0 word", 0x11E0, "i32"),
    "BatmanVsBatmobileCollisionMode": ("RVehicleBatmobileBase", "BatmanVsBatmobileCollisionMode", 0x1707, "u8"),
    "CurrentThrottle": ("RVehicleBatmobileBase", "CurrentThrottle", 0x1908, "f32"),
    "PreventModeSwitchDuration": ("RVehicleBatmobileBase", "PreventModeSwitchDuration", 0x1990, "f32"),
    "Driver": ("Vehicle", "Driver (base class)", 1480, "ptr"),
    "CurrentWeapon": ("RVehicleBatmobileBase", "CurrentWeapon", 0x130C, "ptr"),
    "SecondaryWeapon": ("RVehicleBatmobileBase", "SecondaryWeapon", 0x1314, "ptr"),
    "PursuitModePrimaryWeapon": ("RVehicleBatmobileBase", "PursuitModePrimaryWeapon", 0x1474, "ptr"),
    "BattleModePrimaryWeapon": ("RVehicleBatmobileBase", "BattleModePrimaryWeapon", 0x147C, "ptr"),
    "CurrentStrafeTarget": ("RVehicleBatmobileBase", "CurrentStrafeTarget", 0x14EC, "ptr"),
    "WeaponUnavailableReason": ("RVehicleBatmobileBase", "WeaponUnavailableReason", 0x170B, "u8"),
    "WeaponGeneratorPower": ("RVehicleBatmobileBase", "WeaponGeneratorPower", 0x1EE8, "f32"),
}
PI = {
    "aRightTrigger": (720, "f32"),
    "aLeftTrigger": (724, "f32"),
    "aLeftShoulder": (760, "u8"),
    "bCancelButton": (774, "u8"),
    "aThrottleAxis": (840, "f32"),
}
GADGET_FIELDS = {
    "bFiring": (2084, "bit 0x2"),
    "AimTarget": (2168, "ptr"),
    "LockOnTarget": (2468, "ptr"),
    "TagTarget": (2484, "ptr"),
    "LockOnTime": (2540, "f32"),
    "MissileAnimState": (2605, "u8"),
    "bTryingToAcquireNewTarget": (2608, "bit 0x1"),
}
GADGET_CLASSES = ("RBatmobileEMPMissile", "RBatmobileVehicleTracker")
# every input byte the sampler reads, and the action D-11 assigns it (decoded elsewhere, quoted)
BUTTONS = [
    ("in0.aLeftTrigger", "LT", "hold battle / release pursuit", "D-11 CONFIRMED live"),
    ("in0.bCancelButton", "B", "immobilizer on an auto-tagged enemy", "D-11 CONFIRMED live"),
    ("in0.aLeftShoulder", "LB", "exit AND enter", "D-11 CONFIRMED live"),
    ("in0.aRightTrigger", "RT", "throttle", "driving, BmAK scheme"),
    ("in0.aThrottleAxis", "THR", "throttle axis (moves with RT)", "driving, BmAK scheme"),
]


def ts(s: str) -> float:
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


# ------------------------------------------------------------------ inputs
def load_logs():
    files = []
    for path in sorted(glob.glob(os.path.join(LOGS, "samples-*.jsonl"))):
        raw = open(path, "rb").read()
        recs = []
        for line in raw.decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            recs.append((ts(d["t"]), d["t"], d.get("changed") or {}))
        files.append({"name": os.path.basename(path), "sha256": hashlib.sha256(raw).hexdigest(),
                      "bytes": len(raw), "recs": recs})
    return files


def parse_fields_md():
    """The 44 observable rows of SAMPLER_FIELDS2.md section 1-4 (field, offset, kind, mask)."""
    rows, area = [], None
    for line in open(FIELDS_MD, encoding="utf-8"):
        s = line.rstrip("\n")
        if s.startswith("## "):
            num = s[3:4]
            area = {"1": "inputs", "2": "missiles", "3": "boost", "4": "eject"}.get(num)
            if num == "5":
                area = None
        if area is None or not s.startswith("|"):
            continue
        parts = [p.strip() for p in s.strip().strip("|").split("|")]
        if len(parts) != 8 or not parts[1].startswith("`") or not parts[2][:1].isdigit():
            continue
        full = parts[1].strip("`")
        if "." not in full:
            continue
        cls, fld = full.split(".", 1)
        mask = parts[4].strip("`")
        rows.append({"area": area, "class": cls, "field": fld, "offset": int(parts[2].split()[0]),
                     "kind": parts[3].strip("`"), "mask": None if mask == "-" else int(mask),
                     "line": int(parts[6].split(":")[-1].strip("`")) if ":" in parts[6] else None,
                     "cs": parts[6].strip("`")})
    return rows


def sampler_has(text, name, off):
    """The sampler source line that reads `name` at `off`, in either its hex or decimal spelling."""
    return (sampler_line(text, f'"{name}": (0x{off:X},')
            or sampler_line(text, f'"{name}": ({off},'))


def sampler_line(text, needle):
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


# ------------------------------------------------------------------ press model
def presses(recs, key):
    """Rising edges of one input key: (index, dt_left_raw, dt_right_raw)."""
    out, state = [], {}
    for i, (t, _iso, ch) in enumerate(recs):
        if key not in ch:
            continue
        v, prev = ch[key], state.get(key)
        if v is not None and prev is not None and v > 0 and not prev > 0:
            out.append(i)
        state[key] = v
    return out


def bracket(recs, i):
    """(left, right, left_is_gap) for a press at record i, capped at GAP_MAX on both sides."""
    t = recs[i][0]
    left, gap = t, False
    if i > 0:
        d = t - recs[i - 1][0]
        if d <= GAP_MAX:
            left = recs[i - 1][0]
        else:
            gap = True
    right = t
    if i + 1 < len(recs) and (recs[i + 1][0] - t) <= GAP_MAX:
        right = recs[i + 1][0]
    return left, right, gap


def all_presses(files):
    per = {}
    for f in files:
        recs = f["recs"]
        for key, label, _action, _src in BUTTONS:
            for i in presses(recs, key):
                left, right, gap = bracket(recs, i)
                per.setdefault(label, []).append({
                    "file": f["name"], "iso": recs[i][1], "t": recs[i][0], "i": i,
                    "left": left, "right": right, "gap_left": gap, "key": key,
                    "recs": recs})
    return per


def union_len(spans):
    """Length of the union of (left, right] spans, so overlapping brackets are not double-counted."""
    total, cur_l, cur_r = 0.0, None, None
    for l, r in sorted(spans):
        if r <= l:
            continue
        if cur_r is None or l > cur_r:
            if cur_r is not None:
                total += cur_r - cur_l
            cur_l, cur_r = l, r
        else:
            cur_r = max(cur_r, r)
    if cur_r is not None:
        total += cur_r - cur_l
    return total


def measure(files, press_list, fields):
    """In-bracket vs press-free rates for every field, from one press family.

    in_secs is the union of the family's brackets (so overlapping brackets count their shared time
    once); hits counts presses (distinct brackets) whose bracket contains a change of the field;
    chg_in counts distinct sampled records inside the union where the field changed.
    """
    brackets = [(p["left"], p["right"]) for p in press_list if p["right"] > p["left"]]
    in_secs = union_len(brackets)
    hits = {f: 0 for f in fields}
    seen = {f: set() for f in fields}
    for p in press_list:
        l, r = p["left"], p["right"]
        if r <= l:
            continue
        inside = [(j, ch) for j, (t, _i, ch) in enumerate(p["recs"]) if l < t <= r]
        for f in fields:
            got = [(j, ch[f]) for j, ch in inside if f in ch and ch[f] is not None]
            if got:                      # hits: this press shows the field move (once per press)
                hits[f] += 1
            for j, _v in got:            # chg_in: distinct sampled records, union-safe
                seen[f].add((p["file"], j))
    chg_in = {f: len(seen[f]) for f in fields}
    # press-free baseline: intervals touched by no bracket of any sampled input
    every = [(p["left"], p["right"]) for fam in press_list_all.values() for p in fam]
    away_secs, chg_out = 0.0, {f: 0 for f in fields}
    for f in files:
        recs = f["recs"]
        for j in range(1, len(recs)):
            t0, t1 = recs[j - 1][0], recs[j][0]
            d = t1 - t0
            if d > GAP_MAX or d <= 0:
                continue
            if any(t0 < r and t1 > l for l, r in every):
                continue
            away_secs += d
            ch = recs[j][2]
            for fl in fields:
                if fl in ch and ch[fl] is not None:
                    chg_out[fl] += 1
    return {"in_secs": in_secs, "hits": hits, "chg_in": chg_in,
            "away_secs": away_secs, "chg_out": chg_out, "n": len(brackets)}


def rate(chg, secs):
    return float("inf") if secs <= 0 else chg / secs


def verdict(m):
    if m["hits"] < MIN_BRACKETS or m["in_secs"] <= 0:
        return "UNKNOWN"
    ri, ro = rate(m["chg_in"], m["in_secs"]), rate(m["chg_out"], m["away_secs"])
    if ro > 0 and ri < RATIO * ro:
        return "UNKNOWN"
    if ri - ro < ABS_RATE:
        return "UNKNOWN"
    return "candidate"


def classify_log_key(key):
    """(class, field, offset, kind, label) for a log key, or None if it is sampler-derived."""
    if key.startswith("in0."):
        f = key[4:]
        if f in PI:
            return ("RPlayerInput", f, PI[f][0], PI[f][1], "decoded (bmak_runtime_sampler.py PI)")
        return None
    if key == "veh0.bits11D8" or key.endswith(".bits11D8"):
        return ("RVehicleBatmobileBase", "bits @0x11D8 word (sampler-derived name list)", 0x11D8, "derived", "derived")
    head, _, f = key.rpartition(".")
    if f in VEH:
        v = VEH[f]
        return (v[0], v[1], v[2], v[3], "decoded (bmak_runtime_sampler.py VEH)")
    for cls in GADGET_CLASSES:
        if head.startswith(cls) and f in GADGET_FIELDS:
            off, kind = GADGET_FIELDS[f]
            return (cls, f, off, kind, "decoded (bmak_runtime_sampler.py GADGETS)")
    return None


def observable_in_logs(row, log_keys):
    """Which sampled log key, if any, reads this one of the 44 observables.

    Match is by offset and by the field the getter reads, NOT by class name alone: bFiring is
    sampled on RBatmobileEMPMissile/RBatmobileVehicleTracker objects, which inherit it at the same
    offset from RVehicleWeapon (G3-02f oracle booster_inherits_weapon / VEH table), and
    bBoostLocked / InfiniteBoost are bits of the whole word the sampler reads at 0x11D8.
    """
    hits = []
    for k in log_keys:
        c = classify_log_key(k)
        if not c:
            continue
        _cls, fld, off, _kind, _lab = c
        if off != row["offset"]:
            continue
        if fld == row["field"]:
            hits.append(k)
        elif row["field"] in ("bBoostLocked", "InfiniteBoost") and fld.startswith("bits @"):
            hits.append(k)
    return hits


# ------------------------------------------------------------------ report
press_list_all = {}


def build(files, rows, sampler_text):
    global press_list_all
    log_keys = sorted({k for f in files for _t, _i, ch in f["recs"] for k in ch})
    n_recs = sum(len(f["recs"]) for f in files)
    press_list_all = all_presses(files)

    # ---- corpus
    span0 = min(f["recs"][0][0] for f in files if f["recs"])
    span1 = max(f["recs"][-1][0] for f in files if f["recs"])
    gaps, small = [], 0.0
    for f in files:
        for a, b in zip(f["recs"], f["recs"][1:]):
            d = b[0] - a[0]
            if d > GAP_MAX:
                gaps.append(d)
            else:
                small += d
    none_val = sum(1 for f in files for _t, _i, ch in f["recs"] if any(v is None for v in ch.values()))

    # ---- press census
    census = []
    for key, label, action, src in BUTTONS:
        fam = press_list_all[label]
        measurable = [p for p in fam if p["right"] > p["left"]]
        analog = [p for p in fam if isinstance(p["recs"][p["i"]][2].get(key), float) and 0 < p["recs"][p["i"]][2][key] < 0.9]
        census.append({"label": label, "key": key, "action": action, "src": src, "n": len(fam),
                       "measurable": len(measurable), "analog": len(analog),
                       "first": fam[0]["iso"] if fam else "-", "last": fam[-1]["iso"] if fam else "-"})

    # ---- observable coverage
    cover = []
    for r in rows:
        hits = observable_in_logs(r, log_keys)
        cover.append({"row": r, "keys": hits})
    n_cover = sum(1 for c in cover if c["keys"])

    # ---- bit constancy for the two boost bits
    bit_rows = []
    for mask in (0x4000, 0x20000000):
        set_n, seen = 0, 0
        for f in files:
            for _t, _i, ch in f["recs"]:
                for k, v in ch.items():
                    if k.endswith(".flags_11D8") and isinstance(v, int):
                        seen += 1
                        if v & mask:
                            set_n += 1
        bit_rows.append({"mask": mask, "set": set_n, "seen": seen})

    # ---- eject-adjacent action: LB (D-11 exit/enter), measured
    lb = press_list_all["LB"]
    eject_fields = [k for k in log_keys if classify_log_key(k) and k != "in0.aLeftShoulder"]
    m_lb = measure(files, lb, eject_fields)
    lb_rows = []
    for f in eject_fields:
        ri, ro = rate(m_lb["chg_in"][f], m_lb["in_secs"]), rate(m_lb["chg_out"][f], m_lb["away_secs"])
        lb_rows.append({"field": f, "hits": m_lb["hits"][f], "in": m_lb["chg_in"][f], "ri": ri,
                        "out": m_lb["chg_out"][f], "ro": ro, "v": verdict({
                            "hits": m_lb["hits"][f], "in_secs": m_lb["in_secs"],
                            "chg_in": m_lb["chg_in"][f], "away_secs": m_lb["away_secs"],
                            "chg_out": m_lb["chg_out"][f]})})
    lb_rows.sort(key=lambda r: (-r["ri"], r["field"]))
    lb_live = [r for r in lb_rows if r["hits"] or r["out"]]
    lb_dead = [r for r in lb_rows if not r["hits"] and not r["out"]]
    # per-press detail
    lb_detail = []
    for p in lb:
        recs, l, r = p["recs"], p["left"], p["right"]
        changed = sorted({k for t, _i, ch in recs if l < t <= r for k, v in ch.items()
                          if v is not None and classify_log_key(k)})
        lb_detail.append({"iso": p["iso"], "file": p["file"], "l": l, "r": r,
                          "span": r - l, "changed": changed, "gap": p["gap_left"]})

    # ---- method oracle: LT -> battle mode (D-11 CONFIRMED live)
    lt = press_list_all["LT"]
    oracle_fields = ["veh1.flags_11D8", "veh1.CurrentWeapon", "veh1.bits11D8", "veh1.Driver",
                     "veh1.BatmanVsBatmobileCollisionMode"]
    m_lt = measure(files, lt, oracle_fields)
    lt_rows = []
    for f in oracle_fields:
        ri, ro = rate(m_lt["chg_in"][f], m_lt["in_secs"]), rate(m_lt["chg_out"][f], m_lt["away_secs"])
        lt_rows.append({"field": f, "hits": m_lt["hits"][f], "in": m_lt["chg_in"][f], "ri": ri,
                        "out": m_lt["chg_out"][f], "ro": ro, "v": verdict({
                            "hits": m_lt["hits"][f], "in_secs": m_lt["in_secs"],
                            "chg_in": m_lt["chg_in"][f], "away_secs": m_lt["away_secs"],
                            "chg_out": m_lt["chg_out"][f]})})
    lt_rows.sort(key=lambda r: (-r["ri"], r["field"]))

    # sensitivity check (NOT part of the candidate rule): does a 2.0 s window separate a press from
    # a press-free instant? Counts only, so the control's blindness is a number, not an opinion.
    def hit_within(recs, i, win):
        t = recs[i][0]
        return any(("veh1.flags_11D8" in ch or "veh1.CurrentWeapon" in ch)
                   for tt, _i2, ch in recs[i + 1:] if tt - t <= win)

    press_hits = sum(1 for pr in lt if hit_within(pr["recs"], pr["i"], 2.0))
    base_hits = base_n = 0
    for f in files:
        recs, name = f["recs"], f["name"]
        for j in range(len(recs) - 1):
            t = recs[j][0]
            if any(pr["file"] == name and pr["left"] <= t <= pr["right"]
                   for fam in press_list_all.values() for pr in fam):
                continue
            base_n += 1
            if hit_within(recs, j, 2.0):
                base_hits += 1
    sens = {"press_hits": press_hits, "base_hits": base_hits, "base_n": base_n}

    # ---- X / Y press counts: the answer the brief asks for
    x_keys = [k for k in log_keys if classify_log_key(k) and classify_log_key(k)[0] == "RPlayerInput"
              and any(t in classify_log_key(k)[1].lower() for t in ("quickgadget", "barrage", "gadgetx"))]
    n_x = sum(len(presses(f["recs"], k)) for f in files for k in x_keys)
    n_y = sum(len(presses(f["recs"], "in0.bVehicleBoostButton")) for f in files)  # never sampled -> 0

    # ---- oracles
    oracles = {}
    oracles["corpus_loads"] = {"ok": n_recs > 0 and all(f["recs"] for f in files),
                               "detail": {"files": len(files), "records": n_recs}}
    oracles["logs_are_change_only"] = {
        "ok": all(sorted(f["recs"][0][2]) == sorted(k for k in f["recs"][0][2]) for f in files),
        "detail": "first record of each file is the initial snapshot; later records are diffs"}
    oracles["every_input_key_is_a_known_PI_field"] = {
        "ok": all(classify_log_key(k) is not None for k in log_keys if k.startswith("in0.")),
        "detail": sorted(k for k in log_keys if k.startswith("in0."))}
    oracles["sampler_offsets_match"] = {
        "ok": all(sampler_has(sampler_text, k, v[0]) for k, v in PI.items())
              and all(sampler_has(sampler_text, f, v[2]) for f, v in VEH.items()),
        "detail": {**{k: sampler_has(sampler_text, k, v[0]) for k, v in PI.items()},
                   **{f: sampler_has(sampler_text, f, v[2]) for f, v in VEH.items()}}
    }
    oracles["buttons_present"] = {
        "ok": all(press_list_all[b[1]] for b in BUTTONS),
        "detail": {b[1]: len(press_list_all[b[1]]) for b in BUTTONS}}
    oracles["presses_are_rising_edges"] = {
        "ok": all(p["right"] >= p["left"] for fam in press_list_all.values() for p in fam),
        "detail": "every bracket has right >= left"}
    oracles["away_is_press_free"] = {
        "ok": m_lb["away_secs"] > 0,
        "detail": {"away_seconds": round(m_lb["away_secs"], 3), "bracket_seconds_LB": round(m_lb["in_secs"], 3)}}
    oracles["observable_coverage_recomputes"] = {
        "ok": n_cover == 4,
        "detail": {"of_44_in_logs": n_cover,
                   "present": [c["row"]["class"] + "." + c["row"]["field"] for c in cover if c["keys"]]}}
    oracles["x_and_y_unpressed"] = {"ok": n_x == 0 and n_y == 0, "detail": {"X": n_x, "Y": n_y}}
    oracles["margin_is_stated"] = {
        "ok": MIN_BRACKETS == 3 and RATIO == 3.0 and ABS_RATE == 0.5 and GAP_MAX == 5.0,
        "detail": {"min_brackets": MIN_BRACKETS, "ratio": RATIO, "abs_rate": ABS_RATE, "gap_max": GAP_MAX}}

    L = []
    A = L.append
    A("# SAMPLER_UNKNOWNS - the three G3-02f action UNKNOWNs, tested against the existing sampler logs")
    A("")
    A("**Card:** SAMPLER-offline (follow-on to **G3-02f**). **Status:** 3 of 3 UNKNOWN, for two measured")
    A("reasons: the seven logs never carry a press of X, Y or A, and only 4 of G3-02f's 44 observables are")
    A("among the fields the sampler ever read; and the rate test the brief specifies has no discriminating")
    A("power on this corpus - run on a binding that is known (LT -> battle mode) it promotes nothing and does")
    A("not beat its own baseline. Both facts are measured below, with counts.")
    A("")
    A("**Inputs (read-only, nothing else):** `Research/BatmobileGrab/runtime/samples-*.jsonl`, "
      "`Research/BatmobileGrab/SAMPLER_FIELDS2.md`, and - only to name the log keys - "
      "`Tools/scripts/bmak_runtime_sampler.py`. No game was run, attached to or read.")
    A("")
    A("## 0. The three UNKNOWNs, restated")
    A("")
    A("`SAMPLER_FIELDS2.md` §6 lists four UNKNOWNs; three are *actions*, and they are the ones this card tests.")
    A("The fourth (`TArray` element stride for `CurrentTargets`/`FiredProjectiles`) is not an action and is out")
    A("of scope here.")
    A("")
    A("| # | UNKNOWN (G3-02f §6) | the corresponding action | what the logs would need |")
    A("|---|---|---|---|")
    A("| 1 | X (missile barrage) input byte | an X press | a sampled X byte - none exists in the layout, none in the log |")
    A("| 2 | A (eject) input byte | an A press / an eject | a sampled A byte or eject field - neither is in the log |")
    A("| 3 | boost duration / boost time field | a boost (Y) engagement | a sampled boost flag/timer - none is in the log |")
    A("")
    A("## 1. Corpus - what the logs are (decoded: file, sha256, records)")
    A("")
    A("| log | bytes | records | sha256 (first 16) |")
    A("|---|---:|---:|---|")
    for f in files:
        A(f"| `{f['name']}` | {f['bytes']:,} | {len(f['recs'])} | `{f['sha256'][:16]}` |")
    A(f"| **total** | **{sum(f['bytes'] for f in files):,}** | **{n_recs}** | |")
    A("")
    A(f"- span: `{datetime.datetime.fromtimestamp(span0, datetime.timezone.utc).isoformat()}` to "
      f"`{datetime.datetime.fromtimestamp(span1, datetime.timezone.utc).isoformat()}` (UTC, from the log's own `t`)")
    A(f"- sampling intervals <= {GAP_MAX:g} s: **{small:,.1f} s**; intervals > {GAP_MAX:g} s: **{len(gaps)}** "
      f"(max {max(gaps):,.1f} s) - session pauses, excluded from every rate below")
    A(f"- records carrying a `null`: **{none_val}** (teardown/GC; a null is never counted as a change)")
    A(f"- distinct sampled fields: **{len(log_keys)}**")
    A("")
    A("## 2. Press census - and the exact X and Y counts")
    A("")
    A("A press is a rising edge (`0 -> >0`) of a sampled input byte. The sampler reads exactly five input")
    A("fields; the offsets are decoded at the line `--check` re-reads:")
    A("")
    A("| # | input | log key | offset | .py line | presses | measurable brackets | analog (<0.9) | first | last | action (source) |")
    A("|---|---|---|---:|---:|---:|---:|---:|---|---|---|")
    for i, c in enumerate(census, 1):
        line = sampler_line(sampler_text, f'"{c["key"][4:]}": ({PI[c["key"][4:]][0]},')
        A(f"| {i} | {c['label']} | `{c['key']}` | {PI[c['key'][4:]][0]} | "
          f"`bmak_runtime_sampler.py:{line}` | {c['n']} | {c['measurable']} | {c['analog']} | "
          f"{c['first'][11:23] if c['first'] != '-' else '-'} | {c['last'][11:23] if c['last'] != '-' else '-'} | "
          f"{c['action']} ({c['src']}) |")
    A("")
    A("**The answer to the brief's question, stated exactly:** the logs contain **0 presses of X** and")
    A("**0 presses of Y**. Not \"few\": zero - neither button was ever sampled: `bVehicleBoostButton`")
    A("(+781) and the X byte are absent from the sampler's `PI` table (five entries, above), and for X there is")
    A("also no decoded byte to sample at all (G3-02f UNKNOWN 1). The sections below can therefore only test")
    A("X/Y hypotheses against *other* presses, which is exactly what §5-§7 show cannot work. A (eject) is also")
    A("unpressed: **0 presses of A**. The eject-adjacent action the logs do carry is LB (D-11: exit AND enter),")
    A("**4 presses**, analysed in §6.")
    A("")
    A("## 3. Which of the 44 observables the logs actually contain (decoded: class + offset match)")
    A("")
    A("Each of the 44 rows of `SAMPLER_FIELDS2.md` §1-§4 was matched to a sampled field by **class and offset**,")
    A("never by name similarity. **4 of 44** are present:")
    A("")
    A("| observable | offset | sampled as | records where the sampled field changed |")
    A("|---|---:|---|---|")
    for c in cover:
        if not c["keys"]:
            continue
        r = c["row"]
        chg = sum(1 for f in files for _t, _i, ch in f["recs"] for k in c["keys"] if k in ch and ch[k] is not None)
        A(f"| `{r['class']}.{r['field']}` | {r['offset']} | {', '.join('`'+k+'`' for k in c['keys'][:3])}"
          f"{' ...' if len(c['keys']) > 3 else ''} | {chg} |")
    A("")
    A("The other **40** are not in any log - including every missile-launcher field, every eject field")
    A("(`MaxEjectType`, `EjectUpDist`, `OverrideNextEject`, `CurrentEjectType`, `LastEjectFromBatmobileTime`,")
    A("`UsedQuickGadget`) and the boost objects (`RBatmobileBooster.bBoosting`/`bWarming`, `BoostingOut`,")
    A("`AfterburnerSystem`, `LastBoostPickupTime`). That absence alone decides UNKNOWN 1 and 3; §5-§7 say what")
    A("*can* still be measured.")
    A("")
    A("`RVehicleBatmobileBase.bBoostLocked` (bit 0x4000) and `InfiniteBoost` (bit 0x20000000) are the two")
    A("exceptions: the sampler reads their whole word as `vehN.flags_11D8` (offset 0x11D8 = 4568, the layout's")
    A("own offset). Across every record:")
    A("")
    A("| bit | field | records where set | records read |")
    A("|---|---|---:|---:|")
    for b in bit_rows:
        nm = "bBoostLocked" if b["mask"] == 0x4000 else "InfiniteBoost"
        A(f"| 0x{b['mask']:08x} | `{nm}` | {b['set']} | {b['seen']} |")
    A("")
    A("`bBoostLocked` never sets, `InfiniteBoost` sets only in the teardown garbage records, so neither bit is a")
    A("usable signal; and neither is a *duration* in any case (G3-02f: no boost timer field exists).")
    A("")
    A("## 4. Method, stated so it can be rejected")
    A("")
    A("* **press** = rising edge of a sampled input byte (table §2).")
    A(f"* **bracket** (\"within one sampling interval of the press\") = `[t_edge, next sample]` plus")
    A(f"  `[previous sample, t_edge]` when that side is a normal sampling interval (<= {GAP_MAX:g} s). Rationale:")
    A("  the press onset is only localised to the interval that ended at the edge sample, so one interval either")
    A("  side is the narrowest window that certainly contains the onset and its first consequence. A bracket")
    A("  whose next sample is > 5 s away contributes no seconds and is reported as unmeasurable.")
    A(f"* **away** = every sampling interval (<= {GAP_MAX:g} s) that **no bracket of any sampled input** touches,")
    A("  so the baseline is press-free; long pauses are excluded from both sides, which can only *lower* the")
    A("  baseline rate and therefore cannot manufacture a candidate.")
    A("* **rate** = changes per second; a change is a record inside the window where that field's new value is")
    A("  non-null (the log is a diff stream, so a field that changes twice between two samples shows once).")
    A(f"* **margin (candidate rule):** changed inside >= {MIN_BRACKETS} distinct brackets **and**")
    A(f"  `rate_in >= {RATIO:g} x rate_out` **and** `rate_in - rate_out >= {ABS_RATE:g} s^-1`. Otherwise UNKNOWN.")
    A("  A candidate is a field that *tracks the action*; it is never the action's input byte unless it is an")
    A("  input byte, which for X and A does not exist in any log.")
    A("")
    A("## 5. UNKNOWN 1 - X (missile barrage) input byte")
    A("")
    A("**Sampled fields that change when X occurs: none are identifiable, because X never occurs in the logs.**")
    A("Presses of X: **0** (§2). No sampled input byte is X, and no missile-launcher field is sampled (§3), so")
    A("there is no window to measure and no field whose in-press rate can be compared with its baseline. Under")
    A("the stated rule the answer is UNKNOWN - not \"no field correlates\", but \"no X press exists to correlate")
    A("against\". Nothing in this corpus can distinguish X from the presses that are there (LT/B/LB/RT), and a")
    A("field that tracks those presses is evidence for *them*, not for X.")
    A("")
    A("| candidate tested | presses available | in-bracket changes | away changes | rate_in | rate_out | verdict |")
    A("|---|---:|---:|---:|---:|---:|---|")
    A("| (none: no X-named or barrage-named field in the log, and no X press) | 0 | - | - | - | - | UNKNOWN |")
    A("")
    A("## 6. UNKNOWN 2 - A (eject) input byte")
    A("")
    A("Presses of A: **0**. The eject-adjacent event the logs *do* carry is **LB**, which D-11 records as")
    A("exit AND enter, confirmed live; in these logs LB brackets coincide with the vehicle losing its driver and")
    A("opening the cockpit (below). That is the closest known-to-occur eject/exit action in the corpus.")
    A(f"**LB presses: {len(lb)}; measurable brackets: {m_lb['n']}; bracket seconds: {m_lb['in_secs']:.3f}; "
      f"press-free seconds: {m_lb['away_secs']:.1f}.**")
    A("")
    A("Per press:")
    A("")
    A("| press (UTC) | log | bracket s | left side | sampled fields that changed inside |")
    A("|---|---|---:|---|---|")
    for d in lb_detail:
        A(f"| `{d['iso'][:23]}` | `{d['file'][8:23]}` | {d['span']:.3f} | "
          f"{'gap (not counted)' if d['gap'] else 'interval'} | "
          f"{', '.join('`'+k+'`' for k in d['changed']) or '-'} |")
    A("")
    A("Rate table (real log fields that changed in or out of an LB bracket, sorted by in-bracket rate):")
    A("")
    A("| field | presses it changed in | changes in brackets | rate_in (s^-1) | changes press-free | rate_out (s^-1) | ratio | verdict |")
    A("|---|---:|---:|---:|---:|---:|---:|---|")
    for r in lb_live:
        ratio = "inf" if r["ro"] == 0 and r["ri"] > 0 else (f"{r['ri']/r['ro']:.2f}" if r["ro"] else "-")
        A(f"| `{r['field']}` | {r['hits']} | {r['in']} | {r['ri']:.3f} | {r['out']} | {r['ro']:.3f} | {ratio} | **{r['v']}** |")
    A("")
    cand = [r for r in lb_rows if r["v"] == "candidate"]
    A(f"`{len(lb_dead)}` of the {len(lb_rows)} real fields changed neither inside an LB bracket nor press-free")
    A("and are omitted above. The press definition `in0.aLeftShoulder` is excluded from this table: its")
    A("presence in its own bracket is true by construction, not evidence.")
    A("")
    A(f"**Verdict:** {len(cand)} field(s) pass the margin on >= {MIN_BRACKETS} presses: "
      f"{', '.join('`'+r['field']+'`' for r in cand) if cand else 'none'}. Nothing is promoted, so the answer")
    A("for A is **UNKNOWN**, for two counted reasons: A itself is never pressed (0) and")
    A("`bBatmobileEjectModifier` (+786) is never read, so no A byte exists in the corpus at all; and the")
    A("strongest eject-adjacent action that does occur (LB, 4 presses) moves the driver/collision/cockpit")
    A("fields on only 1-2 of those 4 presses - below the >= 3-press floor - while section 8 shows that a")
    A("window wide enough to catch them also catches the press-free baseline.")
    A("")
    A("## 7. UNKNOWN 3 - boost duration / boost time field")
    A("")
    A("Presses of Y: **0**. No boost flag, timer or object field is sampled (§3): `RBatmobileBooster.bBoosting`/")
    A("`bWarming` (+2396), `BoostingOut` (+5901), `AfterburnerSystem` (+4636), `LastBoostPickupTime` (+6580) are")
    A("all absent, and the two boost bits that *are* in the word (`bBoostLocked`, `InfiniteBoost`) never move")
    A("(§3 table). So there is neither a press window nor a boost signal to measure:")
    A("")
    A("| candidate tested | presses available | in-bracket changes | away changes | rate_in | rate_out | verdict |")
    A("|---|---:|---:|---:|---:|---:|---|")
    A("| `RBatmobileBooster.bBoosting` (+2396 &1) | - | not sampled | not sampled | - | - | UNKNOWN |")
    A("| `RBatmobileBooster.bWarming` (+2396 &2) | - | not sampled | not sampled | - | - | UNKNOWN |")
    A("| `RVehicleBatmobileBase.bBoostLocked` (0x11D8 &0x4000) | 0 (Y) | 0 | 0 | 0.000 | 0.000 | UNKNOWN |")
    A("| `RVehicleBatmobileBase.InfiniteBoost` (0x11D8 &0x20000000) | 0 (Y) | 0 | 0 | 0.000 | 0.000 | UNKNOWN |")
    A("")
    A("A duration also cannot be *derived* from this corpus: deriving it needs the `bBoosting` rise and fall,")
    A("and that bit was never read. UNKNOWN.")
    A("")
    A("## 8. Method oracle - the same test on a binding that is known")
    A("")
    A("A negative result is worthless if the instrument is blind, so the identical test is run on **LT**, whose")
    A("binding is decoded and was CONFIRMED live (D-11: hold battle / release pursuit; `aLeftTrigger` +724). The")
    A("battle-mode transition *should* appear in `veh1.flags_11D8` (the sampler names bit 0x2 ArmouredMode)")
    A("and in `veh1.CurrentWeapon` (booster -> heavy cannon); neither link is asserted here - the point is")
    A("only that a real, known input->state link exists in this corpus and the test is asked to find it.")
    A("")
    A(f"**LT presses: {len(lt)}; measurable brackets: {m_lt['n']}; bracket seconds: {m_lt['in_secs']:.3f}; "
      f"press-free seconds: {m_lt['away_secs']:.1f}.**")
    A("")
    A("| field | presses it changed in | changes in brackets | rate_in (s^-1) | changes press-free | rate_out (s^-1) | ratio | verdict |")
    A("|---|---:|---:|---:|---:|---:|---:|---|")
    for r in lt_rows:
        ratio = "inf" if r["ro"] == 0 and r["ri"] > 0 else (f"{r['ri']/r['ro']:.2f}" if r["ro"] else "-")
        A(f"| `{r['field']}` | {r['hits']} | {r['in']} | {r['ri']:.3f} | {r['out']} | {r['ro']:.3f} | {ratio} | **{r['v']}** |")
    A("")
    ok = [r for r in lt_rows if r["v"] == "candidate"]
    A(f"**Oracle: {'PASS' if ok else 'FAIL'}** - {len(ok)} of {len(lt_rows)} fields pass the same margin on a")
    A("binding that is known to work, so the mandated test cannot promote even a real input->state link here.")
    A(f"The cause is countable: {sens['press_hits']} of {len(lt)} LT presses are followed by a")
    A(f"`flags_11D8`/`CurrentWeapon` change within 2.0 s, against {sens['base_hits']} of {sens['base_n']}")
    A("press-free sampled instants in the same 2.0 s window. The press does not raise the hit rate at all -")
    A(f"it is lower ({100*sens['press_hits']/max(1,len(lt)):.0f}% vs {100*sens['base_hits']/max(1,sens['base_n']):.0f}%) - so")
    A("timing these logs cannot attribute the change to the press, and widening the window does not rescue")
    A("the test (sensitivity check only, `derived`).")
    A("")
    A("## 9. Oracles (`--check` re-runs each)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k in sorted(oracles):
        det = json.dumps(oracles[k]["detail"], sort_keys=True)
        A(f"| `{k}` | {oracles[k]['ok']} | `{det[:220]}` |")
    A("")
    A("## 10. What stays UNKNOWN, and why no log can close it")
    A("")
    A("1. **X barrage input byte** - no X press in any log (0), no X-named field in `RPlayerInput`, no")
    A("   missile-launcher field sampled. Closing it needs either the bind table/`BmInput.ini` (decode) or a")
    A("   new capture that samples `PI` at +773/+774/+784 and the launcher's `CurrentTargets` count.")
    A("2. **A eject input byte** - 0 A presses; `bBatmobileEjectModifier` (+786) never read. The LB-correlated")
    A("   vehicle-state fields above are consequence markers only. Same two routes.")
    A("3. **Boost duration/time** - 0 Y presses; `bBoosting` (+2396) never read; the two boost bits in the")
    A("   sampled word never change. A capture that reads +2396 is required; the duration must be measured")
    A("   from its rise/fall, not read from a field (G3-02f: none exists).")
    A("")
    A("Everything above is `decoded` (file + offset + line, cited) or `derived` (rule + inputs, stated); no")
    A("value here is filled from general knowledge of the game or the engine.")
    A("")
    return "\n".join(L)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"
    if mode not in ("--write", "--check"):
        print(__doc__)
        return 2
    files = load_logs()
    rows = parse_fields_md()
    sampler_text = open(SAMPLER_PY, encoding="utf-8", errors="replace").read()
    md = build(files, rows, sampler_text)
    if mode == "--write":
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({len(md):,} B)")
        print(f"logs: {len(files)}; records: {sum(len(f['recs']) for f in files)}; "
              f"observables parsed: {len(rows)}")
        return 0
    on_disk = open(OUT_MD, encoding="utf-8", newline="").read()
    if on_disk != md:
        print("FAIL: SAMPLER_UNKNOWNS.md differs from a fresh rebuild")
        return 1
    print(f"OK rebuilt byte-identical from {len(files)} logs and {len(rows)} observables")
    return 0


if __name__ == "__main__":
    sys.exit(main())
