"""chase_calibrate.py - calibrate `smart_search.py` on values the project already knows.

The point of calibration is to catch the two ways a search+judge pair lies: it misses a value that
is really there (low recall) or it "finds" literals that are not the member's default (low
precision). Every case is therefore one of three kinds:

  positive  a member decoded by the G1 readers: serialised in all four packages, value agreeing on
            all four, with owner + field offset (source `MODES.json`)
  found     a chase row already marked FOUND with a literal value, the value being re-verified
            against the chase file line that records it (source: that line)
  negative  a member whose data proves no scalar literal default exists - either absent from every
            package (`FOOTAGE.md`/`MODES.json`, "not serialised") or a multi-point curve / config
            struct whose value is not a scalar. Every found=true on a negative is a false positive.

`--build` writes E:/Modding/_shared/gamedata/BmAKgrab/chase/calib.jsonl (game-derived, outside the repo) from those
records; it is not hand-edited. `--run` calls `smart_search.py` once per case and stores its JSON
under E:/Modding/_shared/gamedata/BmAKgrab/chase/calib_runs/<judge>/<prompt-version>/<case>.json; `--score` reads those
files; `--render` writes the generated block of the report; `--check` re-scores, re-renders and
compares against the report on disk *and* re-verifies every known value against its provenance, so
no number in the report is typed (R11).

Two judges (`--judge`), each in its own run folder so they never overwrite each other:
  qwen  `chase_judge.PROMPT` on llama-server :8080, folder `calib_runs/<ss.PROMPT_VERSION>[_v1search]`
  jeb   Jebadiah 9B v2.1 (`jeb_judge.py`) on llama-server :8081, folder
        `calib_runs/jeb_<jeb_judge.prompt_version()>[_v1search]`
`--score`/`--render`/`--check` cover every stored run of both judges side by side.

`--sweep` re-thresholds stored Jeb `p` values (no model call); `--compare` lists the cases the two
judges decide differently, with the provenance's own answer.

Usage
  python Tools/scripts/chase/chase_calibrate.py --build
  python Tools/scripts/chase/chase_calibrate.py --run [--judge jeb] [--threshold 0.5] [--max 15] [--only P,F,N]
  python Tools/scripts/chase/chase_calibrate.py --score
  python Tools/scripts/chase/chase_calibrate.py --render [--report <path>]  # write the report block
  python Tools/scripts/chase/chase_calibrate.py --check  [--report <path>]  # re-score + verify report
  python Tools/scripts/chase/chase_calibrate.py --sweep 0.3,0.4,0.5,0.6,0.7,0.8,0.9
  python Tools/scripts/chase/chase_calibrate.py --compare
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
import chase_candidates as cc  # noqa: E402
import chase_judge as cj       # noqa: E402
import jeb_judge as jj         # noqa: E402
import smart_search as ss      # noqa: E402

BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
CHASE = os.path.join(BAT, "chase")
MODES = os.path.join(BAT, "MODES.json")
OUT_DIR = os.path.join(r"E:\Modding\_shared\gamedata\BmAKgrab", "chase")
CALIB = os.path.join(OUT_DIR, "calib.jsonl")
RUNS = os.path.join(OUT_DIR, "calib_runs")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "smart-search.md")
BEGIN, END = "<!-- CALIB-BEGIN -->", "<!-- CALIB-END -->"
SEED = 0.0
JUDGES = ("qwen", "jeb")

# family (b): chase rows already FOUND with a literal, the (file, line) that records the value
FOUND_CASES = [
    ("F-7", "AirControl", "0.05", "chase-01.md", 21),
    ("F-11", "BattleModeCamFOV", "60.0", "chase2-02.md", 17),
    ("F-16", "StrafeCooldown", "0.75", "chase2-02.md", 22),
    ("F-18", "StrafeForce", "0.0", "chase2-03.md", 20),
    ("F-22", "StrafeFwdCorrectionForce", "3000.0", "chase2-03.md", 24),
    ("F-31", "BattleModeWidth", "265.0", "chase2-05.md", 58),
    ("F-33", "BattleModeHeight", "250.0", "chase2-05.md", 9),
    ("F-35", "ImpactShakeAbandonedVehicleFactor", "3.0", "chase2-05.md", 11),
]
# family (c): negatives. Each one's value is not a scalar literal by the data, so any found=true
# that reports one is a false positive:  a multi-point curve / a 24-field config struct
# (MODES.json, MECHANICS.md), a runtime state (the chase row itself), or a name / object reference
# (FOUND as an FName / null in chase-04 / chase2-03).
NEG_CASES = [
    ("F-39", "TurnOnSpotSteeringSpeedCurve", "FInterpCurveFloat",
     "FOOTAGE F-39 + MODES.json: FInterpCurveFloat, not serialised"),
    ("F-40", "BattleModeMoving", "bool",
     "chase-05.md:206: a runtime state, not an authored default"),
    ("F-25", "ImpactRoadAssistTimer", "float",
     "chase-04.md: a timer, runtime value, no authored literal"),
    ("F-30", "BattleModeTransformationAnimName", "FName",
     "chase-04.md:161: FOUND as an FName string, not a number"),
    ("F-23", "TransformationAnimNode", "AnimNodeSequence",
     "chase2-03.md:173: FOUND as a null object reference"),
    ("F-49", "TransformationAnimNode", "AnimNodeSequence",
     "FOOTAGE F-49: object reference, no literal default"),
    ("F-24", "StrafeTarget", "RVehicle", "chase2-03.md:185: FOUND as a null object reference"),
    ("F-8", "BattleModeCamConfig", "FFreeCameraConfig",
     "chase-01.md:305: FFreeCameraConfig, 24 members, not a scalar"),
    ("MODES", "BattleModeVSpeedCurve", "FInterpCurveFloat",
     "MODES.json: 3-point curve (0->60, 600->40, 1200->30), not a scalar"),
    ("MECH", "StandardTorqueVSpeedCurve", "FInterpCurveFloat",
     "MECHANICS.md:104: 6 curve points on RVehicleSimBatmobile, not a scalar"),
]


def jload(path):
    return json.load(open(path, encoding="utf-8"))


def fnum(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


# ---------------------------------------------------------------------------------------- build
def modes_fields():
    return {f["field"]: f for f in jload(MODES)["fields"]}


def build() -> list[dict]:
    cases: list[dict] = []
    F = modes_fields()
    # (a) positives: serialised, all four packages agree, scalar
    picks = []
    for f in jload(MODES)["fields"]:
        if f["declared_type"] not in ("float", "int") or not f.get("serialized"):
            continue
        vals = {k: v for k, v in (f.get("values") or {}).items() if v is not None}
        if len(vals) != 4 or len(set(vals.values())) != 1:
            continue
        picks.append(f)
    picks.sort(key=lambda f: (f["declaring_class"], f["offset"]))
    sim = [f for f in picks if f["declaring_class"] == "RVehicleSimBatmobile"]
    base = [f for f in picks if f["declaring_class"] == "RVehicleBatmobileBase"]
    chosen = sim + base[:4] + [f for f in picks if f["declared_type"] == "int"]
    seen = set()
    for f in chosen:
        if f["field"] in seen:
            continue
        seen.add(f["field"])
        val = list({k: v for k, v in f["values"].items() if v is not None}.values())[0]
        cases.append({
            "id": f"P{len(cases) + 1:02d}", "kind": "positive", "family": "a",
            "member": f["field"], "owner": f["declaring_class"], "offset": hex(f["offset"]),
            "type": f["declared_type"], "known": fnum(val),
            "provenance": f"Research/BatmobileGrab/MODES.json:{f['field']} "
                          f"(values on all four packages, {fnum(val)})"})
    # (b) found: owner/offset from the FOOTAGE row, value re-verified against the chase line
    footage = {r["id"]: r for r in cc.parse_footage()}
    for fid, member, value, fname, line_no in FOUND_CASES:
        row = footage.get(fid) or {}
        if not row.get("offset") or not row.get("owner"):
            print(f"skipping {fid}: FOOTAGE row has no declared owner/offset", file=sys.stderr)
            continue
        cases.append({
            "id": f"F{fid.split('-')[1]}", "kind": "found", "family": "b",
            "member": member, "owner": row["owner"], "offset": row["offset"],
            "type": row["type"] or "float", "known": value,
            "provenance": f"Research/BatmobileGrab/chase/{fname}:{line_no}"})
    # (c) negatives
    n = 0
    for fid, member, ftype, why in NEG_CASES:
        n += 1
        if fid == "MODES":
            f = F.get(member) or {}
            owner, off = f.get("declaring_class"), hex(f["offset"]) if f else None
            prov = f"Research/BatmobileGrab/MODES.json:{member} ({why})"
        elif fid == "MECH":
            owner, off = "RVehicleSimBatmobile", "0x1f0"
            prov = f"Research/BatmobileGrab/MECHANICS.md:{member} ({why})"
        else:
            row = footage.get(fid) or {}
            owner, off = row.get("owner"), row.get("offset")
            prov = f"Research/BatmobileGrab/FOOTAGE.md:{fid} ({why})"
        if not off or not owner:
            print(f"skipping negative {fid}: no owner/offset", file=sys.stderr)
            n -= 1
            continue
        cases.append({"id": f"N{n:02d}", "kind": "negative", "family": "c",
                      "member": member, "owner": owner, "offset": off, "type": ftype,
                      "known": None, "provenance": prov})
    return cases


def cmd_build() -> int:
    cases = build()
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CALIB, "w", encoding="utf-8", newline="\n") as fh:
        for c in cases:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    kinds = {}
    for c in cases:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print(f"wrote {CALIB}: {len(cases)} cases {kinds}")
    return 0


def load_calib() -> list[dict]:
    return [json.loads(l) for l in open(CALIB, encoding="utf-8") if l.strip()]


# ------------------------------------------------------------------------------- run folders
# One folder suffix per search half, so the pre-change run (`current`), the frozen v1 half and the
# table-route run are all scored side by side instead of overwriting each other.
SEARCH_SUFFIXES = {"current": "", "v1": "_v1search", "table": "_tablesearch"}


def run_dir(search_name: str = "current", judge: str = "qwen") -> str:
    """`<prompt version>[_v1search]`; Jeb gets its own `jeb_`-prefixed folder keyed on
    `jeb_judge.prompt_version()`, so the two judges' runs never share a directory."""
    if judge == "jeb":
        name = "jeb_" + jj.prompt_version()
    else:
        name = ss.PROMPT_VERSION
    suffix = SEARCH_SUFFIXES.get(search_name, "_" + search_name.replace("-", "") + "search")
    return os.path.join(RUNS, name + suffix)


def judge_of(directory: str) -> str:
    return "jeb" if os.path.basename(directory.rstrip("\\/")).startswith("jeb_") else "qwen"


def search_of(directory: str) -> str:
    tpath = os.path.join(directory, "_search.txt")
    if os.path.exists(tpath):
        try:
            return jload(tpath).get("search", "current")
        except (OSError, ValueError):
            pass
    base = os.path.basename(directory.rstrip("\\/"))
    for name, suffix in SEARCH_SUFFIXES.items():
        if suffix and base.endswith(suffix):
            return name
    return "current"


def version_of(directory: str) -> str:
    b = os.path.basename(directory.rstrip("\\/"))
    if judge_of(directory) == "jeb":
        b = b[len("jeb_"):]
    for suffix in SEARCH_SUFFIXES.values():
        if suffix and b.endswith(suffix):
            return b[:-len(suffix)]
    return b


def run_dirs(judge: str | None = None, search_name: str | None = None) -> list[str]:
    out = []
    for d in sorted(glob.glob(os.path.join(RUNS, "*"))):
        b = os.path.basename(d)
        if not os.path.isdir(d):
            continue
        if not (re.fullmatch(r"(?:jeb_)?[0-9a-f]{8}", b)
                or os.path.exists(os.path.join(d, "_search.txt"))):
            continue
        if judge and judge_of(d) != judge:
            continue
        if search_name and search_of(d) != search_name:
            continue
        out.append(d)
    return out


def newest_run(judge: str = "qwen", search_name: str | None = None) -> str | None:
    ds = run_dirs(judge, search_name)
    return ds[-1] if ds else None


# ------------------------------------------------------------------------------------------ run
def cmd_run(max_n: int, only: str, search_name: str = "current", judge: str = "qwen",
            threshold: float = jj.THRESHOLD, fresh: bool = False) -> int:
    cases = load_calib()
    d = run_dir(search_name, judge)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "_search.txt"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"search": search_name, "judge": judge, "threshold": threshold,
                   "prompt": jj.prompt_version() if judge == "jeb" else ss.PROMPT_VERSION,
                   "model": "jebadiah-9b" if judge == "jeb" else "qwen3.5-4b"}, fh)
    log = open(os.path.join(d, "run.log"), "a", encoding="utf-8")
    n = 0
    for c in cases:
        if only and c["kind"][0].upper() not in only.upper():
            continue
        out = os.path.join(d, c["id"] + ".json")
        if os.path.exists(out):
            continue
        cmd = [sys.executable, os.path.join(HERE, "smart_search.py"),
               "--member", c["member"], "--offset", c["offset"], "--type", c["type"],
               "--max", str(max_n), "--json-out", out, "--quiet",
               "--judge", judge, "--threshold", str(threshold)]
        if c.get("owner"):
            cmd += ["--owner", c["owner"]]
        if c.get("known") is not None:
            cmd += ["--expect", c["known"]]
        cmd += ["--search", search_name]
        if fresh:
            cmd += ["--no-cache"]
        t0 = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True)
        line = (f"{c['id']} {c['member']}: rc={p.returncode} "
                f"{(p.stdout.strip().splitlines() or [''])[-1][:120]} [{time.time() - t0:.0f}s]")
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()
        n += 1
    log.close()
    print(f"ran {n} case(s) into {d}")
    return 0


# ---------------------------------------------------------------------------------------- score
def same(known, value) -> bool:
    if value is None:
        return False
    a, b = str(known).strip(), str(value).strip().strip("\"'")
    if not b:
        return False
    try:
        return abs(float(b) - float(a)) <= 1e-6
    except ValueError:
        return a.lower() == b.lower()


def score(directory: str | None = None) -> dict:
    # score the directory asked for, else the newest run that exists (the judge's prompt can be
    # revised by another session while a run is in flight, so the prompt in force now is not
    # necessarily the one that produced the stored verdicts)
    if not directory:
        ds = run_dirs()
        d = ds[-1] if ds else run_dir()
    else:
        d = directory
    cases = load_calib()
    rows, tot_judged, tot_null, tot_true, tot_right, tot_jsec, tot_uncached = [], 0, 0, 0, 0, 0.0, 0
    for c in cases:
        path = os.path.join(d, c["id"] + ".json")
        if not os.path.exists(path):
            rows.append({**c, "run": False})
            continue
        r = jload(path)
        found = [v for v in r.get("verdicts", []) if v.get("found") is True]
        nulls = [v for v in r.get("verdicts", []) if v.get("found") is None]
        right = wrong = 0
        for v in found:
            if c["kind"] == "negative":
                wrong += 1
            elif same(c["known"], v.get("value")):
                right += 1
            else:
                wrong += 1
        tot_judged += r.get("judged", 0)
        tot_uncached += max(0, r.get("judged", 0) - r.get("cache_hits", 0))
        tot_null += len(nulls)
        tot_true += len(found)
        tot_right += right
        tot_jsec += r.get("judge_seconds", 0.0)
        rows.append({**c, "run": True, "candidates": r.get("candidates", 0),
                     "judged": r.get("judged", 0), "found": len(found), "right": right,
                     "wrong": wrong, "null": len(nulls), "reach": r.get("reach"),
                     "warnings": sum(len(v.get("warnings") or []) for v in r.get("verdicts", [])),
                     "recall": (1.0 if right else 0.0)
                     if c["kind"] != "negative" else None,
                     "hit": (1.0 if (found and c["kind"] == "negative") else 0.0)})
    pos = [r for r in rows if r["run"] and r["kind"] != "negative"]
    neg = [r for r in rows if r["run"] and r["kind"] == "negative"]
    kpos = [r for r in rows if r["run"] and r["kind"] == "positive"]
    kfound = [r for r in rows if r["run"] and r["kind"] == "found"]
    reached = [r for r in pos if r.get("reach")]
    recall = sum(r["recall"] for r in pos) / len(pos) if pos else 0.0
    recall_reached = (sum(r["recall"] for r in reached) / len(reached)) if reached else 0.0
    precision = tot_right / tot_true if tot_true else 0.0

    def mean(rs):
        return sum(r["recall"] for r in rs) / len(rs) if rs else 0.0

    return {"dir": d, "judge": judge_of(d), "prompt": version_of(d), "search": search_of(d),
            "rows": rows, "cases": len(rows), "ran": sum(1 for r in rows if r["run"]),
            "positives": len(pos), "negatives": len(neg),
            "pos_n": len(kpos), "pos_recall": mean(kpos),
            "pos_right": sum(1 for r in kpos if r["recall"] == 1.0),
            "found_n": len(kfound), "found_recall": mean(kfound),
            "found_right": sum(1 for r in kfound if r["recall"] == 1.0),
            "neg_n": len(neg), "neg_fp": sum(1 for r in neg if r["found"]),
            "neg_fp_verdicts": sum(r["found"] for r in neg),
            "reach": len(reached), "recall_reached": recall_reached,
            "judged": tot_judged, "found_true": tot_true, "right": tot_right,
            "recall": recall, "precision": precision,
            "unparsable_n": tot_null,
            "unparsable": tot_null / tot_judged if tot_judged else 0.0,
            "sec_per_candidate": tot_jsec / tot_uncached if tot_uncached else 0.0,
            "warnings": sum(r.get("warnings", 0) for r in rows if r["run"]),
            "snippet_cuts": sum(1 for r in rows if r["run"]
                                for v in jload(os.path.join(d, r["id"] + ".json")).get("verdicts", [])
                                if any("cut to" in w for w in (v.get("warnings") or []))),
            "uncached": tot_uncached, "cache_hits": tot_judged - tot_uncached}


SUMMARY_COLS = ("| judge | prompt | search | cases run | reachable | positive recall | found recall "
                "| precision | negative FP (cases / verdicts) | unparsable | s/candidate |")


def summary_row(s: dict) -> str:
    return (f"| {s['judge']} | `{s['prompt']}` | {s['search']} | {s['ran']}/{s['cases']} | "
            f"{s['reach']}/{s['positives']} | {s['pos_recall']:.3f} ({s['pos_right']}/{s['pos_n']}) | "
            f"{s['found_recall']:.3f} ({s['found_right']}/{s['found_n']}) | "
            f"{s['precision']:.3f} | "
            f"{s['neg_fp']}/{s['neg_n']} / {s['neg_fp_verdicts']} | "
            f"{s['unparsable_n']} ({s['unparsable']:.3f}) | {s['sec_per_candidate']:.2f} |")


def cmd_score() -> int:
    scores = all_scores()
    if not scores:
        print("no run directories under " + RUNS)
        return 1
    print(SUMMARY_COLS)
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for s in scores:
        print(summary_row(s))
    for s in scores:
        print(f"\n### {s['judge']} prompt `{s['prompt']}` (search {s['search']}) cases {s['dir']}")
        for r in s["rows"]:
            if not r["run"]:
                print(f"  {r['id']} {r['member']}: NO RUN")
                continue
            print(f"  {r['id']:<5} {r['kind']:<8} {r['member']:<36} known={r['known']!s:<12} "
                  f"cand={r['candidates']:<3} reach={r.get('reach')!s:<5} found={r['found']:<2} "
                  f"right={r['right']} wrong={r['wrong']} unparsable={r['null']}")
    return 0


# --------------------------------------------------------------------------------------- report
def render_block(scores: list[dict]) -> str:
    L = [BEGIN, "<!-- generated by Tools/scripts/chase/chase_calibrate.py --render; do not hand-edit -->",
         "", SUMMARY_COLS,
         "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in scores:
        L.append(summary_row(s))
    for s in scores:
        L += ["", f"### Cases — {s['judge']} prompt `{s['prompt']}` (search {s['search']})", "",
              "| id | kind | member | owner | offset | type | known | candidates | value in a candidate | found=true | right | wrong | unparsable |",
              "|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|"]
        for r in s["rows"]:
            if not r["run"]:
                L.append(f"| {r['id']} | {r['kind']} | `{r['member']}` | {r['owner'] or '-'} | "
                         f"{r['offset']} | {r['type']} | {r['known'] if r['known'] is not None else '—'} "
                         f"| — | — | — | — | — | — |")
                continue
            L.append(f"| {r['id']} | {r['kind']} | `{r['member']}` | {r['owner'] or '-'} | "
                     f"{r['offset']} | {r['type']} | "
                     f"{r['known'] if r['known'] is not None else '—'} | {r['candidates']} | "
                     f"{'yes' if r.get('reach') else ('no' if r['known'] is not None else '—')} | "
                     f"{r['found']} | {r['right']} | {r['wrong']} | {r['null']} |")
        fam = {}
        for r in s["rows"]:
            if not r["run"]:
                continue
            d = fam.setdefault(r["family"], {"n": 0, "recal": 0, "found": 0, "right": 0,
                                             "wrong": 0, "judged": 0})
            d["n"] += 1
            d["recal"] += 1 if (r["recall"] == 1.0) else 0
            d["found"] += r["found"]
            d["right"] += r["right"]
            d["wrong"] += r["wrong"]
            d["judged"] += r["judged"]
        L += ["", f"Per family ({s['judge']} `{s['prompt']}`): "
                  + ", ".join(f"{k}: {v['n']} cases, {v['recal']} recalled, "
                              f"{v['found']} found=true ({v['right']} right)"
                              for k, v in sorted(fam.items()))]
    L.append(END)
    return "\n".join(L)


def all_scores() -> list[dict]:
    """One entry per stored run directory, both judges: `<qwen hash>[_v1search]` and
    `jeb_<jeb hash>[_v1search]`.  Anything else under `calib_runs` (a hand-made comparison
    directory, a stray scratch run) is not a run and is not scored."""
    return [score(d) for d in run_dirs()]


def write_block(report: str = REPORT) -> str:
    block = render_block(all_scores())
    text = open(report, encoding="utf-8").read() if os.path.exists(report) else ""
    if BEGIN in text and END in text:
        head, rest = text.split(BEGIN, 1)
        _old, tail = rest.split(END, 1)
        text = head + block + tail
    else:
        text = text.rstrip() + "\n\n## Calibration (generated)\n\n" + block + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
    open(report, "w", encoding="utf-8", newline="\n").write(text)
    return block


def cmd_render(report: str = REPORT) -> int:
    block = write_block(report)
    print(f"rendered {len(block)} B into {report}")
    return 0


# ----------------------------------------------------------------------- sweep and disagreement
def _stored_pairs(directory: str) -> list[tuple[dict, dict]]:
    out = []
    for c in load_calib():
        path = os.path.join(directory, c["id"] + ".json")
        if os.path.exists(path) and os.path.getsize(path) > 0:
            out.append((c, jload(path)))
    return out


def sweep(thresholds: list[float], directory: str | None = None) -> list[dict]:
    """Re-threshold stored Jeb `p` values.  No model call: `found` is recomputed as p >= t and the
    verdict's own `value`/`lit` (the regex literal read from the snippet) is what is compared."""
    d = directory or newest_run("jeb")
    if not d:
        raise SystemExit("no jeb run on disk to sweep")
    pairs = _stored_pairs(d)
    out = []
    for t in thresholds:
        row = {"threshold": t, "pos_n": 0, "pos_right": 0, "found_n": 0, "found_right": 0,
               "neg_n": 0, "neg_fp": 0, "neg_fp_verdicts": 0, "found_true": 0,
               "missed_at_t": 0}
        for c, r in pairs:
            vs = [v for v in r.get("verdicts", [])
                  if v.get("p") is not None and float(v["p"]) >= t]
            row["found_true"] += len(vs)
            if c["kind"] == "negative":
                row["neg_n"] += 1
                row["neg_fp"] += 1 if vs else 0
                row["neg_fp_verdicts"] += len(vs)
            else:
                key = "pos" if c["kind"] == "positive" else "found"
                row[key + "_n"] += 1
                if any(same(c["known"], v.get("lit") or v.get("value")) for v in vs):
                    row[key + "_right"] += 1
        out.append(row)
    return out


def best_threshold(rows: list[dict]) -> dict:
    """Highest recall at zero false positives; ties broken by the *lower* threshold (the most
    permissive setting that still keeps the negatives clean)."""
    ok = [r for r in rows if r["neg_fp"] == 0] or rows
    return max(ok, key=lambda r: ((r["pos_right"] + r["found_right"])
                                  / max(1, r["pos_n"] + r["found_n"]), -r["threshold"]))


def cmd_sweep(spec: str) -> int:
    thrs = [float(x) for x in spec.split(",") if x.strip()]
    d = newest_run("jeb")
    if not d:
        print("no jeb run on disk", file=sys.stderr)
        return 1
    rows = sweep(thrs, d)
    pairs = _stored_pairs(d)
    print(f"sweep of stored P(true) in {d} (no model call)\n")
    print("| threshold | positive recall | found recall | negatives with a false positive | "
          "false-positive verdicts | found=true total |")
    print("|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['threshold']:.1f} | {r['pos_right']}/{r['pos_n']} | "
              f"{r['found_right']}/{r['found_n']} | {r['neg_fp']}/{r['neg_n']} | "
              f"{r['neg_fp_verdicts']} | {r['found_true']} |")
    b = best_threshold(rows)
    print(f"\nbest at zero false positives: threshold {b['threshold']:.1f} -> "
          f"positive recall {b['pos_right']}/{b['pos_n']}, "
          f"found recall {b['found_right']}/{b['found_n']}, "
          f"false positives {b['neg_fp']}/{b['neg_n']}")
    # failure-mode detail from the same stored files, still no model call
    ps = {k: [] for k in ("positive", "found", "negative")}
    tot = cut = warn = 0
    for c, r in pairs:
        for v in r.get("verdicts", []):
            tot += 1
            if v.get("warnings"):
                warn += 1
                cut += any("cut to" in w for w in v["warnings"])
            if v.get("p") is not None:
                ps[c["kind"]].append((float(v["p"]), c["id"], v.get("source")))
    print(f"\nstored verdicts {tot}; with warnings {warn}, of them snippet cut to Jeb's "
          f"2,048-token limit {cut}")
    for k in ("positive", "found", "negative"):
        lst = sorted(ps[k], reverse=True)
        if not lst:
            continue
        hi, cid, src = lst[0]
        print(f"- {k}: {len(lst)} verdicts, max P(true) {hi:.3f} ({cid} {src}), "
              f"verdicts at or above 0.5: {sum(1 for p in lst if p[0] >= 0.5)}")
    return 0


def cmd_compare() -> int:
    q = newest_run("qwen")
    j = newest_run("jeb")
    cases = load_calib()
    if not q or not j:
        print(f"need both judges on disk (qwen {q}, jeb {j})", file=sys.stderr)
        return 1
    print(f"| case | kind | known | qwen found=true (value) | jeb found=true (p, value) | provenance says |")
    print("|---|---|---|---|---|---|")
    n = 0
    for c in cases:
        qp = os.path.join(q, c["id"] + ".json")
        jp = os.path.join(j, c["id"] + ".json")
        if not (os.path.exists(qp) and os.path.exists(jp)):
            continue
        qr, jr = jload(qp), jload(jp)
        qf = [v for v in qr.get("verdicts", []) if v.get("found") is True]
        jf = [v for v in jr.get("verdicts", []) if v.get("found") is True]
        qsig = sorted((v.get("source"), str(v.get("value"))) for v in qf)
        jsig = sorted((v.get("source"), str(v.get("value"))) for v in jf)
        if qsig == jsig:
            continue
        n += 1
        qtxt = "; ".join(f"{v.get('source')} = {v.get('value')!r}" for v in qf) or "-"
        jtxt = "; ".join(f"{v.get('source')} p={v.get('p')} = {v.get('value')!r}" for v in jf) or "-"
        if c["kind"] == "negative":
            right = []
            if not qf:
                right.append("qwen")
            if not jf:
                right.append("jeb")
            verdict = ("both right (no literal default exists)" if len(right) == 2 else
                       (right[0] + " right (no literal default exists)" if right else
                        "both wrong (no literal default exists)"))
        else:
            right = []
            if any(same(c["known"], v.get("value")) for v in qf):
                right.append("qwen")
            if any(same(c["known"], v.get("value")) for v in jf):
                right.append("jeb")
            verdict = ("both right" if len(right) == 2 else
                       (right[0] + " right" if right else "neither right") +
                       ("" if right else f" (known {c['known']})"))
            if right and c["known"] is not None:
                verdict += f" ({c['known']})"
        print(f"| {c['id']} | {c['kind']} | {c['known'] if c['known'] is not None else '-'} | "
              f"{qtxt} | {jtxt} | {verdict} |")
    print(f"\n{n} case(s) where the two judges disagree")
    return 0


def verify_provenance() -> list[str]:
    bad = []
    for c in load_calib():
        prov = c["provenance"]
        # dispatch on the file the provenance *starts* with: a FOOTAGE row's parenthetical may name
        # MODES.json (`FOOTAGE F-39 + MODES.json: ...`) and must not be read as a MODES field.
        if prov.startswith("Research/BatmobileGrab/FOOTAGE.md:"):
            fid = prov.split("FOOTAGE.md:")[1].split(" ")[0]
            row = next((r for r in cc.parse_footage() if r["id"] == fid), None)
            if row is None:
                bad.append(f"{c['id']}: {fid} not in FOOTAGE.md")
            elif row.get("offset") != c["offset"] or row.get("owner") != c["owner"]:
                bad.append(f"{c['id']}: {fid} declares {row.get('owner')}/{row.get('offset')}, "
                           f"case says {c['owner']}/{c['offset']}")
        elif "MODES.json:" in prov:
            field = prov.split("MODES.json:")[1].split(" ")[0]
            f = modes_fields().get(field)
            if not f:
                bad.append(f"{c['id']}: {field} not in MODES.json")
                continue
            if c["known"] is not None:
                vals = {fnum(v) for v in (f.get("values") or {}).values() if v is not None}
                if c["known"] not in vals:
                    bad.append(f"{c['id']}: MODES.json {field} has {sorted(vals)}, "
                               f"case says {c['known']}")
        elif "/chase/" in prov:
            path, line = prov.rsplit(":", 1)
            p = os.path.join(ROOT, path.replace("/", os.sep))
            lines = open(p, encoding="utf-8").read().splitlines()
            ln = int(line)
            if ln - 1 >= len(lines) or str(c["known"]) not in lines[ln - 1]:
                bad.append(f"{c['id']}: {path}:{line} does not contain {c['known']!r}")
        elif "MECHANICS.md:" in prov:
            name = prov.split("MECHANICS.md:")[1].split(" ")[0]
            md = open(os.path.join(BAT, "MECHANICS.md"), encoding="utf-8").read()
            if f"`{name}`" not in md or "6 curve points" not in md:
                bad.append(f"{c['id']}: MECHANICS.md no longer carries {name} / 6 curve points")
    return bad


def cmd_check(report: str = REPORT) -> int:
    problems = verify_provenance()
    block = render_block(all_scores())
    text = open(report, encoding="utf-8").read() if os.path.exists(report) else ""
    if BEGIN not in text or END not in text:
        problems.append(f"report {report} has no calibration block")
    else:
        have = text.split(BEGIN, 1)[1].split(END, 1)[0]
        want = block.split(BEGIN, 1)[1].split(END, 1)[0]
        if have != want:
            problems.append("report calibration block differs from the re-scored block")
    scores = all_scores()
    if not scores:
        problems.append("no run directories under " + RUNS)
    for j in sorted({s["judge"] for s in scores}):
        latest = [s for s in scores if s["judge"] == j][-1]
        if latest["ran"] < latest["cases"]:
            # only each judge's newest run has to be complete; older ones are history
            problems.append(f"{j} prompt {latest['prompt']}: "
                            f"{latest['cases'] - latest['ran']} case(s) without a run")
    for p in problems:
        print("FAIL", p)
    if problems:
        return 1
    for s in scores:
        print(f"{s['judge']} {s['prompt']} ({s['search']}): pos recall {s['pos_recall']:.3f} "
              f"({s['pos_right']}/{s['pos_n']}), found recall {s['found_recall']:.3f} "
              f"({s['found_right']}/{s['found_n']}), negative FP {s['neg_fp']}/{s['neg_n']} "
              f"({s['neg_fp_verdicts']} verdicts), unparsable {s['unparsable_n']}, "
              f"{s['sec_per_candidate']:.2f} s/candidate")
    print(f"check ok: {len(scores)} run(s); {len(load_calib())} cases, provenance re-verified, "
          f"report block matches")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sweep", metavar="T[,T...]",
                    help="re-threshold stored Jeb P(true) values, e.g. 0.3,0.4,...,0.9")
    ap.add_argument("--compare", action="store_true",
                    help="cases where the two judges' found=true sets differ")
    ap.add_argument("--judge", default="qwen", choices=JUDGES,
                    help="which judge --run drives (qwen :8080, jeb :8081)")
    ap.add_argument("--threshold", type=float, default=jj.THRESHOLD,
                    help="jeb only: P(true) cut-off for found=true")
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--only", default="")
    ap.add_argument("--fresh", action="store_true", help="--run without the verdict cache")
    ap.add_argument("--search", dest="search_name", default="current",
                    choices=("current", "v1", "table"))
    ap.add_argument("--report", default=REPORT, help="report file --render/--check use")
    a = ap.parse_args()
    if a.build:
        return cmd_build()
    if a.run:
        return cmd_run(a.max, a.only, a.search_name, a.judge, a.threshold, a.fresh)
    if a.score:
        return cmd_score()
    if a.render:
        return cmd_render(a.report)
    if a.check:
        return cmd_check(a.report)
    if a.sweep:
        return cmd_sweep(a.sweep)
    if a.compare:
        return cmd_compare()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
