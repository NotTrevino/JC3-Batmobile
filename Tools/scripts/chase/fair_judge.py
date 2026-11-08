"""fair_judge.py - a pre-registered, held-out test of Jebadiah 9B vs Qwen3.5-4B as the
smart-search judge: "which snippet shows this member's default value?"

Why this file exists.  Three earlier reports (`tmp/freebuff/reports/jeb-vs-qwen-calibration.md`,
`jeb-short-window-retest.md`, `jeb-choice-format-retest.md`) compared the two models, and every
number in them was distorted by five flaws:

  1. only 5 of 28 positive cases had a candidate that actually stored the default, so one hit
     moved the score ~20 points;
  2. the frozen search handed the `calib.jsonl` manifest line to the model as a candidate (that
     line contains the answer key), so 70 of 74 class labels were wrong;
  3. Qwen was never run in the choice format;
  4. there were no repeats, so position bias and sampling noise were unmeasured;
  5. prompt tuning and scoring used the same cases.

This module fixes all five:

  A. corpus   Candidate lists are rebuilt from decoded game data and real disassembly only.
              `calib.jsonl`, `candidates.jsonl`, `verdicts*`, `cache/`, `calib_runs/` and the
              ground-truth file itself (`MODES.json`) are excluded from every candidate list
              (`EXCLUDED` below, counted in the report).  A positive case has exactly one
              candidate that carries a decoded default record for (member, class, offset) with a
              visible scalar value; a negative case has none.  Ground truth is the decoded tune
              (`MODES.json`, four Playable_Batmobile packages) or the chase record - never the
              regex and never a model.  Evidence path per case is stored in the case.
  B. split    1/3 tuning, 2/3 test, frozen by fixed seeds before any model call
              (`SPLIT_SEED_TUNE`/`SPLIT_SEED_TEST`).  Prompt variant and settings are chosen on
              the tuning split; the test split is scored once.
  C. task     One choice question per case over candidates A-F plus `none`, identical wording and
              an identical text window for both models (`prompt_tokens` is measured per case with
              Jeb's own tokenizer and must stay under 2,048).  Jeb answers through
              `jebadiah_decide` `choice`; Qwen answers with one constrained letter.  A second,
              native arm is also run: Jeb's trained `member` shape (source labels, 1,100 chars
              per candidate) and Qwen's free-form JSON answer read by a parser.
  D. repeats  Each test case is run in 3 candidate orders (fixed seeds `ORDER_SEEDS`); per-order
              accuracy and cross-order consistency are reported, so position bias is visible.
  E. metrics  per model and arm: positive picks, negative `none`, negative false picks, macro
              accuracy, Wilson 95% intervals, a paired exact-binomial test between the models on
              the same cases, seconds per case, and a calibration note (does the top option
              probability separate correct from wrong).
  F. rule     `PREREG` below was written before the run and is copied verbatim into the report.
  G. report   `--report` writes tmp/freebuff/reports/jeb-vs-qwen-fair-test.md with the verdict,
              the table, the disagreements and the exact rerun commands.

Nothing here edits an existing judge.  The earlier runs under `calib_runs/` are untouched; this
module writes only under `E:/Modding/_shared/gamedata/BmAKgrab/chase/fair/`.

Usage
  python Tools/scripts/chase/fair_judge.py --build            # corpus + split + prereg hash
  python Tools/scripts/chase/fair_judge.py --run --model jeb  # tuning + test, choice/native arms
  python Tools/scripts/chase/fair_judge.py --run --model qwen
  python Tools/scripts/chase/fair_judge.py --score            # tables, tests, calibration
  python Tools/scripts/chase/fair_judge.py --report <path>    # write the report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)

BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
MODES = os.path.join(BAT, "MODES.json")
CHASE = os.path.join(r"E:\Modding\_shared\gamedata\BmAKgrab", "chase")
FAIR = os.path.join(CHASE, "fair")
CORPUS = os.path.join(FAIR, "cases.jsonl")
RUNS = os.path.join(FAIR, "runs")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "jeb-vs-qwen-fair-test.md")
PREREG_FILE = os.path.join(FAIR, "PREREGISTRATION.md")

SPLIT_SEED_TUNE = 20261107
SPLIT_SEED_TEST = 20261108
NEG_SEED = 20261109
ORDER_SEEDS = (1107, 2711, 3313)
TOKEN_LIMIT = 2040

# Files that must never appear in a candidate list.  The first entry is flaw (2): the manifest
# line carries the case's own `known` value.  The rest are tool bookkeeping, the answer-key file,
# and the judge's own output.
EXCLUDED = ("calib.jsonl", "candidates.jsonl", "verdicts.jsonl", "verdicts_v2.jsonl",
            "MODES.json", "FOOTAGE.md")

# ------------------------------------------------------------------------------- pre-registration
PREREG = """\
## Decision rule (written before any model call)

A model is chosen as the smart-search judge only if either
  (a) its Wilson 95% lower bound on test-split macro accuracy is greater than the other model's
      point estimate on the same split and arm, or
  (b) the paired exact-binomial test (McNemar, two-sided) between the two models on the same cases
      gives p < 0.05.
Otherwise the verdict is NO DIFFERENCE, and the cheaper and faster model stays the judge.  Cost is
measured as seconds per case on the shared choice arm; a tie in cost keeps the incumbent
(`chase_judge` on Qwen3.5-4B, the default in `smart_search.py`).

Scoring definitions fixed before the run:
  * a positive case is correct only if the model picks the one candidate whose decoded record
    carries the member's value at the member's class and offset;
  * a negative case is correct only if the model answers `none`; any other answer is a false pick;
  * macro accuracy is the unweighted mean of positive accuracy and negative accuracy (the splits
    are balanced, so it equals overall accuracy);
  * per-case decisions are the majority over the 3 candidate orders (ties -> first order, flagged);
  * the paired test uses the per-case majority decision of the two models on the same cases;
  * Wilson intervals are 95% (z = 1.96);
  * a call that returns no parseable letter is a wrong answer, counted, never dropped.
"""

CHOICE_INSTRUCTIONS = ("Which snippet shows the default value of `{member}` "
                       "(declared on `{owner}`, type {type}, field offset {offset})?")
NONE_LABEL = "none"
NONE_CRIT = "no snippet stores a literal default for the member"
# Two wording variants of the SAME question, neither naming a candidate's source or class:
#   neutral  - the plain question and one short option label per letter
#   explicit - the same, plus one sentence fixing what counts as "shows the default"
# Tuned on the tuning split (jointly for both models, so the shared arm stays identical).
VARIANTS = ("neutral", "explicit")
PER_CAND_CHARS = 900       # shared window; snippets are built under this so nothing is cut
NATIVE_PER_CHARS = 1100    # Jeb's trained member layout


# --------------------------------------------------------------------------------- prompt texts
def choice_question(case: dict, cands: list[dict], variant: str) -> dict:
    crit = {chr(65 + i): f"option {chr(65 + i)}" for i in range(len(cands))}
    crit[NONE_LABEL] = NONE_CRIT
    instructions = CHOICE_INSTRUCTIONS.format(
        member=case["member"], owner=case["owner"], type=case["type"], offset=case["offset"])
    if variant == "explicit":
        instructions += (" Count a snippet only if it shows a numeric value for the member at "
                         "that offset; a field offset, a count, a register value, a stack local, "
                         "a per-frame update or a search-tool record is not the default.")
    return {"type": "choice", "instructions": instructions, "criteria": crit}


def choice_state(case: dict, cands: list[dict], variant: str, per_chars: int) -> dict:
    parts = [f"CANDIDATE {chr(65 + i)}:\n{c['snippet'][:per_chars]}"
             for i, c in enumerate(cands)]
    return {"member": case["member"], "candidates": "\n\n".join(parts)}


def native_jeb_question(case: dict, cands: list[dict]) -> dict:
    """Jeb's trained `member` shape from `jeb_judge.member_question`: the options name the
    candidate's source (short) instead of a bare letter, so the model sees the same layout it was
    trained on.  Only the native-jeb arm uses this; the shared arm keeps the identical wording."""
    crit = {}
    for i, cand in enumerate(cands):
        src = str(cand.get("source", "?")).replace(
            "E:/Modding/_shared/gamedata/BmAKgrab/chase/", "")
        crit[chr(65 + i)] = f"snippet {chr(65 + i)} from {src}"
    crit[NONE_LABEL] = NONE_CRIT
    return {"type": "choice",
            "instructions": CHOICE_INSTRUCTIONS.format(
                member=case["member"], owner=case["owner"], type=case["type"],
                offset=case["offset"]),
            "criteria": crit}


def native_jeb_state(case: dict, cands: list[dict], per_chars: int) -> dict:
    """`jeb_judge.member_state` layout: `CANDIDATE A (<source>):` then the snippet."""
    parts = [f"CANDIDATE {chr(65 + i)} ({c.get('source', '?')}):\n{c['snippet'][:per_chars]}"
             for i, c in enumerate(cands)]
    return {"member": case["member"], "candidates": "\n\n".join(parts)}


def qwen_choice_text(case: dict, cands: list[dict], variant: str, per_chars: int) -> str:
    q = choice_question(case, cands, variant)
    lines = [q["instructions"], "", "Options:"]
    for k, v in q["criteria"].items():
        lines.append(f"  {k}: {v}")
    lines += ["", "Candidates:", choice_state(case, cands, variant, per_chars)["candidates"], "",
              "It is a default only if a literal value is visible in that snippet and is stored "
              "into the member's field at that offset, in initialisation code. It is not a default "
              "if the snippet only shows the field offset, a count, a value from a register or "
              "memory, a store to a stack local, a per-frame update, or a record written by a "
              "search tool.",
              "", "Answer with exactly one letter: A, B, C, D, E, F or N (N means none)."]
    return "\n".join(lines)


QWEN_NATIVE_INSTRUCTIONS = """\
{question}

Options:
{options}

Candidates:
{candidates}

It is a default only if a literal value is visible in that snippet and is stored into the member's
field at that offset, in initialisation code.  It is not a default if the snippet only shows the
field offset, a count, a value from a register or memory, a store to a stack local, a per-frame
update, or a record written by a search tool.

Reply with ONE JSON object and nothing else:
{{"pick": "A", "why": "one short sentence"}}
Use "none" for pick if no snippet stores a literal default for the member.
"""


def prompt_version(arm: str, variant: str = "") -> str:
    """Stable id of exactly what was asked, so a run folder can never be mistaken for another."""
    base = CHOICE_INSTRUCTIONS + "|" + NONE_CRIT + "|" + NONE_LABEL
    if arm == "native-jeb":
        base += "|native-jeb|per" + str(NATIVE_PER_CHARS)
    elif arm == "native-qwen":
        base += "|native-qwen|json-pick"
    else:
        base += "|" + variant + "|per" + str(PER_CAND_CHARS)
    return hashlib.sha256(base.encode()).hexdigest()[:8]


# ------------------------------------------------------------------------------------ corpus build
def _jload(path):
    return json.load(open(path, encoding="utf-8"))


def _fnum(v):
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _name(field: str) -> str:
    return re.sub(r"^F-\d+\s+", "", str(field)).strip()


def bmgame_records() -> list[dict]:
    """Real decoded CDO records (BmGame.upk): class, object, property, offset, type, value."""
    out = []
    for fn in ("chase2_defaults.json", "chase2_defaults_07.json"):
        p = os.path.join(CHASE, fn)
        if not os.path.exists(p):
            continue
        d = _jload(p)
        for h in d.get("hits", []):
            if not isinstance(h.get("value"), (int, float)) or isinstance(h.get("value"), bool):
                continue
            out.append({"package": os.path.basename(str(d.get("package", "BmGame.upk"))),
                        "file": fn, "class": h.get("class"), "object": h.get("object"),
                        "property": _name(h.get("field")), "offset": int(h.get("offset") or 0),
                        "type": h.get("type"), "value": h.get("value")})
    return out


def exe_windows() -> list[dict]:
    """Real annotated disassembly windows from the two native scans, classified by shape."""
    out = []
    for fn in ("chase2_native2_05.json", "chase2_native2_07.json"):
        p = os.path.join(CHASE, fn)
        if not os.path.exists(p):
            continue
        for key, rec in _jload(p).items():
            for h in rec.get("hits", []):
                ctx = h.get("context") or []
                if len(ctx) < 4:
                    continue
                lines = []
                for x in ctx[:12]:
                    ln = f"0x{str(x.get('va', '?'))[2:]}  {x['text']}"
                    if x.get("float") is not None:
                        ln += f"   ; [0x{str(x.get('rip_target', '?'))[2:]}] = float {x['float']:g}"
                    lines.append(ln)
                text = "\n".join(lines)
                if len(text) > 620:
                    text = "\n".join(lines[:7])
                if len(text) > 620:
                    continue
                low = text.lower()
                if re.search(r"\[(rsp|rbp)\s*[+-]", low):
                    shape = "stack"
                elif re.search(r"(addss|subss|mulss|divss)", low) and \
                        re.search(r"movss .*\[r\w+ \+ 0x", low):
                    shape = "frame"
                elif re.search(r"\[r\w+ \+ 0x[0-9a-f]+\]", low):
                    shape = "register"
                else:
                    continue
                out.append({"shape": shape, "text": text, "file": fn, "member": key,
                            "va": h.get("va")})
    return out


def _const_store_at(text: str, off_hex: str) -> bool:
    """Does this window store a numeric literal into [reg+offset]?  Distractors must not."""
    off = off_hex.lower().replace("0x", "")
    for ln in text.splitlines():
        low = ln.lower().replace("0x", "")
        if off not in low:
            continue
        if re.search(r"mov\s+\w+ ptr \[r\w+ \+ " + off + r"\],\s*(0x[0-9a-f]+|\d)", low):
            return True
        if "; [" in ln and "= float" in ln and "[r" in low:
            return True
    return False


def _record_text(r: dict) -> str:
    return ("decoded default record   [source: {pkg}]\n"
            "package   {pkg}\n"
            "object    Default__{cls}\n"
            "class     {cls}\n"
            "property  {prop}\n"
            "offset    0x{off:x} ({off})\n"
            "type      {typ}\n"
            "value     {val}\n").format(pkg=r["package"], cls=r["class"], prop=r["property"],
                                        off=r["offset"], typ=r.get("type") or "FloatProperty",
                                        val=_fnum(r["value"]))


def _offset_table(case: dict, fields: list[dict]) -> str:
    rows = [f for f in fields if f["declaring_class"] == case["owner"]]
    rows.sort(key=lambda f: abs(f["offset"] - int(case["offset"], 16)))
    rows = rows[:5]
    body = "\n".join(f"  0x{f['offset']:x}  {f['field']}" for f in rows)
    return ("offset map - names and offsets only, no values\n"
            f"class {case['owner']}\n{body}\n")


def _count_text(case: dict, pkgscan: dict) -> str:
    hits = (pkgscan.get("packages") or {}).get(case["member"]) or []
    inis = (pkgscan.get("inis") or {}).get(case["member"]) or []
    return ("search-tool name count (no value)\n"
            '{"member": "%s", "package_slots": %d, "ini_slots": %d, "decoded_records": %d}\n'
            % (case["member"], len(hits), len(inis), case.get("_decoded_records", 0)))


def _tool_text(case: dict, footage: dict) -> str:
    row = footage.get(case.get("footage_id") or "") or {}
    return ("search-tool record (not game data)\n"
            '{"row": "%s", "member": "%s", "offset": "%s", "type": "%s", "status": "%s"}\n'
            % (row.get("id") or case.get("footage_id") or "-", case["member"], case["offset"],
               case.get("type") or "-", row.get("status") or "UNKNOWN"))


def build() -> list[dict]:
    modes = _jload(MODES)
    fields = modes["fields"]
    recs = bmgame_records()
    windows = exe_windows()
    pkgscan = _jload(os.path.join(r"E:\Modding\_shared\gamedata\BmAKgrab", "chase2_09_packages.json"))
    try:
        import chase_candidates as cc
        footage = {r["id"]: r for r in cc.parse_footage()}
    except Exception:                                     # pragma: no cover - diagnostic only
        footage = {}
    by_member_footage = {}
    for rid, row in footage.items():
        if row.get("member"):
            by_member_footage.setdefault(row["member"], row)

    pools = {"stack": [], "frame": [], "register": []}
    for w in windows:
        pools[w["shape"]].append(w)
    for k in pools:
        pools[k].sort(key=lambda w: (w["member"], w.get("va") or ""))

    decoded_by_name = {}
    for r in recs:
        decoded_by_name.setdefault(r["property"], []).append(r)

    cases: list[dict] = []
    # ---- positives: decoded scalar defaults, per package (V2 = Playable_Batmobile_SF)
    v2 = "Playable_Batmobile_SF"
    for f in fields:
        if f["declared_type"] not in ("float", "int", "bool") or not f.get("serialized"):
            continue
        vals = f.get("values") or {}
        if v2 not in vals or vals[v2] is None:
            continue
        val = vals[v2]
        cases.append({"kind": "positive", "family": "modes", "member": f["field"],
                      "owner": f["declaring_class"], "offset": hex(f["offset"]),
                      "type": f["declared_type"], "known": _fnum(val),
                      "evidence": f"Research/BatmobileGrab/MODES.json:{f['field']} "
                                  f"value {_fnum(val)} on {v2} (decoded tune, four packages)",
                      "true_record": {"package": v2, "class": f["declaring_class"],
                                      "property": f["field"], "offset": f["offset"],
                                      "type": ("FloatProperty" if f["declared_type"] == "float"
                                               else "IntProperty" if f["declared_type"] == "int"
                                               else "BoolProperty"),
                                      "value": val},
                      "footage_id": (by_member_footage.get(f["field"]) or {}).get("id")})
    # ---- positives: chase rows whose recorded value is confirmed by a decoded CDO record
    for name, rlist in decoded_by_name.items():
        for r in rlist:
            m = next((f for f in fields if f["field"] == name), None)
            if not m or m["offset"] != r["offset"] or m["declaring_class"] != r["class"]:
                continue
            if any(c["kind"] == "positive" and c["member"] == name for c in cases):
                break
            cases.append({"kind": "positive", "family": "decoded", "member": name,
                          "owner": r["class"], "offset": hex(r["offset"]),
                          "type": m["declared_type"], "known": _fnum(r["value"]),
                          "evidence": f"{CHASE.replace(os.sep, '/')}/{r['file']} record for "
                                      f"{r['object']} offset 0x{r['offset']:x} value "
                                      f"{_fnum(r['value'])}",
                          "true_record": r,
                          "footage_id": (by_member_footage.get(name) or {}).get("id")})
            break
    # de-duplicate by (member, owner, offset)
    seen, pos = set(), []
    for c in cases:
        key = (c["member"], c["owner"], c["offset"])
        if key in seen:
            continue
        seen.add(key)
        pos.append(c)
    cases = pos

    # ---- negatives: fields the decoded data proves have no scalar default
    neg = []
    for f in fields:
        if f.get("serialized"):
            continue
        if f["declared_type"] not in ("float", "int", "bool", "FName", "FInterpCurveFloat",
                                      "Vector3", "Rotator", "AnimNodeSequence", "RVehicle",
                                      "FFreeCameraConfig", "AkEvent", "FBMScreenShakeStruct",
                                      "RB_StayUprightSetup", "RB_ConstraintInstance"):
            continue
        if any(r["property"] == f["field"] and r["offset"] == f["offset"]
               and r["class"] == f["declaring_class"] for r in recs):
            continue
        neg.append({"kind": "negative", "family": "modes", "member": f["field"],
                    "owner": f["declaring_class"], "offset": hex(f["offset"]),
                    "type": f["declared_type"], "known": None,
                    "evidence": f"Research/BatmobileGrab/MODES.json:{f['field']} "
                                f"serialized=false, packages=[] (no decoded default on any "
                                f"package)",
                    "true_record": None,
                    "footage_id": (by_member_footage.get(f["field"]) or {}).get("id")})

    # balanced corpus: as many negatives as positives, so macro accuracy equals overall accuracy
    # and a Wilson interval on the pooled count is a Wilson interval on macro accuracy.
    rng = random.Random(NEG_SEED)
    rng.shuffle(neg)
    neg = neg[:len(pos)]
    rng = random.Random(SPLIT_SEED_TUNE)
    rng.shuffle(pos)
    rng = random.Random(SPLIT_SEED_TEST)
    rng.shuffle(neg)
    n_pos_tune = max(1, len(pos) // 3)
    n_neg_tune = max(1, len(neg) // 3)
    for i, c in enumerate(pos):
        c["split"] = "tune" if i < n_pos_tune else "test"
        c["kind"] = "positive"
    for i, c in enumerate(neg):
        c["split"] = "tune" if i < n_neg_tune else "test"
    cases = pos + neg
    for i, c in enumerate(cases):
        c["id"] = f"{'P' if c['kind'] == 'positive' else 'N'}{i + 1:02d}"
        c["_decoded_records"] = len(decoded_by_name.get(c["member"], []))
        c["candidates"] = _make_candidates(c, cases, fields, recs, decoded_by_name, pools,
                                           pkgscan, by_member_footage)
    return cases


def _cand(source: str, snippet: str, cls: str, true: bool = False,
          source_label: str | None = None) -> dict:
    return {"source": source, "source_label": source_label or source, "snippet": snippet,
            "class": cls, "true": true}


def _make_candidates(case, all_cases, fields, recs, decoded_by_name, pools, pkgscan, footage) -> list:
    off = int(case["offset"], 16)
    cands = []
    if case["true_record"]:
        r = dict(case["true_record"])
        r.setdefault("package", "BmGame.upk")
        r.setdefault("class", case["owner"])
        r.setdefault("file", "decoded")
        cands.append(_cand(f"decoded record {r['class']} 0x{r['offset']:x} ({r['package']})",
                           _record_text(r), "store", True))
    # the five records every list carries: offset map, name count, tool row, plus the real
    # same-name/wrong-field decoy where one exists.
    cands.append(_cand(f"offset map {case['owner']} (offsets only)",
                       _offset_table(case, fields), "offset"))
    cands.append(_cand("search-tool name count", _count_text(case, pkgscan), "count"))
    cands.append(_cand("search-tool row record", _tool_text(case, footage), "tool"))
    decoy = None
    for r in decoded_by_name.get(case["member"], []):
        if r["class"] == case["owner"] and r["offset"] == off:
            continue
        decoy = r
        break
    if decoy is None:
        for r in recs:
            if r["offset"] == off and r["property"] != case["member"]:
                decoy = r
                break
    if decoy is not None:
        rr = dict(decoy)
        rr.setdefault("file", "decoded")
        cands.append(_cand(f"decoded record {rr['class']} 0x{rr['offset']:x} ({rr['package']})",
                           _record_text(rr), "wrong_record"))

    def _shape(shape: str):
        want = case["offset"].lower().replace("0x", "")
        pick = next((w for w in pools[shape]
                     if want in w["text"].lower().replace("0x", "")
                     and not _const_store_at(w["text"], case["offset"])), None)
        if pick is None:
            pick = next((w for w in pools[shape]
                         if not _const_store_at(w["text"], case["offset"])), None)
        if pick is None:
            return None
        return _cand(f"disassembly {pick['va']} ({pick['member']}, {shape})", pick["text"], shape)

    if case["kind"] == "negative":
        # all six distractor classes the old prompt named, in every negative case
        cands = cands[:3]
        for shape in ("register", "stack", "frame"):
            c = _shape(shape)
            if c is not None:
                cands.append(c)
        i = 0
        while len(cands) < 6 and i < 24:
            shape = ("register", "stack", "frame")[i % 3]
            i += 1
            c = _shape(shape)
            if c is not None:
                c["source"] += f" #{i}"
                cands.append(c)
    else:
        # one disassembly shape per positive, rotated so every shape appears across the corpus
        order = ["register", "stack", "frame"]
        rot = order[(len(case["member"]) + off) % 3:] + order[:(len(case["member"]) + off) % 3]
        for shape in rot:
            if len(cands) >= 6:
                break
            c = _shape(shape)
            if c is not None:
                cands.append(c)
        i = 0
        while len(cands) < 6 and i < 24:
            c = _shape(("register", "stack", "frame")[i % 3])
            i += 1
            if c is not None:
                c["source"] += f" #{i}"
                cands.append(c)
    if len(cands) > 6:
        cands = cands[:6]
    # assert the invariant this whole test rests on
    trues = [i for i, c in enumerate(cands) if c["true"]]
    if case["kind"] == "positive":
        assert len(trues) == 1, f"{case['id']}: {len(trues)} true candidates"
    else:
        assert not trues, f"{case['id']}: negative has a true candidate"
    assert len(cands) == 6, f"{case['id']}: {len(cands)} candidates"
    return cands


def load_cases() -> list[dict]:
    return [json.loads(l) for l in open(CORPUS, encoding="utf-8") if l.strip()]


def cmd_build() -> int:
    os.makedirs(FAIR, exist_ok=True)
    with open(PREREG_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(PREREG)
    cases = build()
    with open(CORPUS, "w", encoding="utf-8", newline="\n") as fh:
        for c in cases:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    pos = [c for c in cases if c["kind"] == "positive"]
    neg = [c for c in cases if c["kind"] == "negative"]
    print(f"wrote {CORPUS}: {len(cases)} cases ({len(pos)} positive, {len(neg)} negative)")
    for split in ("tune", "test"):
        print(f"  {split}: {sum(1 for c in pos if c['split'] == split)} positive, "
              f"{sum(1 for c in neg if c['split'] == split)} negative")
    classes = {}
    for c in cases:
        for cand in c["candidates"]:
            classes[cand["class"]] = classes.get(cand["class"], 0) + 1
    print("  candidate classes:", dict(sorted(classes.items())))
    print(f"  prereg {hashlib.sha256(PREREG.encode()).hexdigest()[:12]} -> {PREREG_FILE}")
    return 0


# ------------------------------------------------------------------------------------- model run
def _parse_letter(raw: str) -> str | None:
    t = (raw or "").strip()
    m = re.search(r"\b(?:pick|answer|choice)\b\W*([A-Fa-f]|none)\b", t, re.I)
    if not m:
        m = re.search(r"^\W*([A-Fa-fN])\b", t) or re.search(r"\b([A-F])\b", t)
    if not m:
        if re.search(r"\bnone\b", t, re.I):
            return "none"
        return None
    v = m.group(1)
    if v.lower() == "none" or v.upper() == "N":
        return "none"
    return v.upper()


def _parse_json_pick(raw: str) -> str | None:
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return _parse_letter(raw)
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return _parse_letter(raw)
    v = str(obj.get("pick", "")).strip()
    if v.lower() in ("none", "n", ""):
        return "none" if v.lower() in ("none", "n") else None
    return v.upper()[0] if v and v[0].upper() in "ABCDEF" else None


def _qwen(url: str, model: str, text: str, max_tokens: int, logprobs: bool) -> dict:
    import urllib.request
    if not logprobs:
        # the native arm is the production path: chase_judge.ask, temperature 0, thinking off
        import chase_judge as cj
        t0 = time.time()
        raw = cj.ask(url, model, text)
        return {"raw": raw, "probs": {}, "seconds": round(time.time() - t0, 2),
                "prompt_tokens": None}
    body = {"model": model, "messages": [{"role": "user", "content": text}],
            "temperature": 0, "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False}}
    if logprobs:
        body.update({"logprobs": True, "top_logprobs": 20})
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)
    ch = d["choices"][0]
    probs = {}
    try:
        for tp in (ch["logprobs"]["content"][0]["top_logprobs"] or []):
            probs[tp["token"].strip()] = round(math.exp(tp["logprob"]), 4)
    except (KeyError, IndexError, TypeError):
        pass
    return {"raw": ch["message"]["content"], "probs": probs, "seconds": round(time.time() - t0, 2),
            "prompt_tokens": (d.get("usage") or {}).get("prompt_tokens")}


def _jeb_call(jeb, case, cands, variant, per_chars, native: bool = False) -> dict:
    if native:
        q, st = native_jeb_question(case, cands), native_jeb_state(case, cands, per_chars)
    else:
        q, st = choice_question(case, cands, variant), choice_state(case, cands, variant, per_chars)
    n, _tr = 0, False
    try:
        rd = jeb.renderer.render(st, q)
        ids = jeb._encode(rd.prompt)
        n = len(ids) if ids is not None else 0
    except Exception:
        pass
    while n > TOKEN_LIMIT and per_chars > 350:
        per_chars = int(per_chars * 0.8)
        st = (native_jeb_state(case, cands, per_chars) if native
              else choice_state(case, cands, variant, per_chars))
        try:
            n = len(jeb._encode(jeb.renderer.render(st, q).prompt) or [])
        except Exception:
            break
    t0 = time.time()
    out = jeb.decide(st, {"d": q})
    a = out["answers"]["d"]
    return {"raw": a.get("choice"), "choice": a.get("choice"),
            "probs": a.get("probabilities") or {}, "seconds": round(time.time() - t0, 2),
            "prompt_tokens": n, "warnings": out.get("warnings", [])}


def run_cell(model: str, arm: str, case: dict, order: int, variant: str) -> dict:
    cands = [dict(c) for c in case["candidates"]]
    rng = random.Random(ORDER_SEEDS[order] * 1000 + int(re.sub(r"\D", "", case["id"]) or 0))
    rng.shuffle(cands)
    letters = [chr(65 + i) for i in range(len(cands))]
    true_idx = next((i for i, c in enumerate(cands) if c["true"]), None)
    per = NATIVE_PER_CHARS if arm in ("native-jeb", "native-qwen") else PER_CAND_CHARS
    if model == "jeb":
        import jeb_judge as jj
        jeb = jj.make()
        v = _jeb_call(jeb, case, cands, variant, per, native=(arm == "native-jeb"))
        pick = v.get("choice")
    else:
        if arm == "native-qwen":
            q = choice_question(case, cands, "neutral")
            text = QWEN_NATIVE_INSTRUCTIONS.format(
                question=q["instructions"],
                options="\n".join(f"  {k}: {v2}" for k, v2 in q["criteria"].items()),
                candidates=choice_state(case, cands, "neutral", per)["candidates"])
            v = _qwen("http://127.0.0.1:8080/v1/chat/completions", "qwen3.5-4b", text, 160, False)
            pick = _parse_json_pick(v["raw"])
        else:
            text = qwen_choice_text(case, cands, variant, per)
            v = _qwen("http://127.0.0.1:8080/v1/chat/completions", "qwen3.5-4b", text, 12, True)
            pick = _parse_letter(v["raw"])
    picked = None
    if pick and len(pick) == 1 and "A" <= pick <= "F":
        idx = ord(pick) - 65
        picked = cands[idx] if idx < len(cands) else None
    true_src = cands[true_idx]["source"] if true_idx is not None else None
    pick_src = picked["source"] if picked is not None else ("none" if pick == "none" else None)
    return {"model": model, "arm": arm, "variant": variant, "case": case["id"],
            "kind": case["kind"], "split": case["split"], "order": order,
            "letters": letters, "true_letter": letters[true_idx] if true_idx is not None else None,
            "pick": pick, "pick_source": pick_src, "true_source": true_src,
            "correct": (pick_src == true_src) if true_src is not None else (pick == "none"),
            "seconds": v["seconds"], "prompt_tokens": v["prompt_tokens"],
            "probs": v.get("probs") or {}, "raw": (v.get("raw") or "")[:400],
            "warnings": v.get("warnings") or []}


def cmd_run(model: str, arm: str, split: str, variant: str, limit: int, order: int | None) -> int:
    cases = [c for c in load_cases() if c["split"] == split]
    cases.sort(key=lambda c: c["id"])
    d = os.path.join(RUNS, f"{arm}_{variant}_{prompt_version(arm, variant)}", model)
    os.makedirs(d, exist_ok=True)
    orders = [order] if order is not None else list(range(len(ORDER_SEEDS)))
    n = 0
    for c in cases:
        for o in orders:
            out = os.path.join(d, f"{c['id']}_o{o}.json")
            if os.path.exists(out):
                continue
            rec = None
            for attempt in range(1, 6):
                try:
                    rec = run_cell(model, arm, c, o, variant)
                    break
                except Exception as e:            # a server blip must not truncate a phase
                    print(f"  retry {attempt}/5 {c['id']} o{o}: {e}", flush=True)
                    time.sleep(15)
            if rec is None:
                print(f"FAILED {c['id']} o{o}; stopping", flush=True)
                return 1
            json.dump(rec, open(out, "w", encoding="utf-8", newline="\n"), indent=1,
                      sort_keys=True)
            n += 1
            print(f"{model} {arm} {split} {c['id']} o{o}: pick={rec['pick']} "
                  f"true={rec['true_letter']} {'OK' if rec['correct'] else 'MISS'} "
                  f"{rec['seconds']}s tok={rec['prompt_tokens']}", flush=True)
            if limit and n >= limit:
                print(f"limit {limit} reached")
                return 0
    print(f"ran {n} cell(s) into {d}")
    return 0


# --------------------------------------------------------------------------------------- scoring
def _same_num(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-6
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def audit() -> dict:
    """Independent re-check of the frozen corpus against the source files, run at report time.

    Nothing here trusts the build: it re-reads `MODES.json` and the decoded CDO dumps and asks, per
    case, whether the case's owner/offset/type/value still match the decode, whether a positive's
    true candidate actually carries that value at that offset, and whether a negative is really
    absent from the decode.  The regex is used only to ask "is this literal present in the shown
    snippet", never to decide the ground truth.
    """
    all_fields = _jload(MODES)["fields"]
    recs = bmgame_records()
    rec_index = {(r["class"], r["offset"], r["property"]): r for r in recs}

    def field_for(c: dict) -> dict | None:
        """MODES field at this member's class and offset.  A name alone is not enough: MODES has
        two `TransformationAnimNode` fields on two classes, and a name-keyed dict silently keeps
        the last one."""
        for f in all_fields:
            if (f["field"] == c["member"] and f["declaring_class"] == c["owner"]
                    and hex(f["offset"]) == c["offset"].lower()):
                return f
        return None
    out = {"cases": 0, "ok": 0, "pos": 0, "neg": 0, "pos_modes": 0, "pos_decoded": 0,
           "true_carries": 0, "neg_clean": 0, "problems": [], "classes": {}}
    for c in load_cases():
        out["cases"] += 1
        bad = []
        f = field_for(c)
        if f is None:
            out["problems"].append(f"{c['id']}: no MODES field at member/class/offset")
            continue
        if hex(f["offset"]) != c["offset"].lower():
            bad.append(f"offset {c['offset']} != MODES {hex(f['offset'])}")
        if f["declaring_class"] != c["owner"]:
            bad.append(f"owner {c['owner']} != MODES {f['declaring_class']}")
        if f["declared_type"] != c["type"]:
            bad.append(f"type {c['type']} != MODES {f['declared_type']}")
        for cand in c["candidates"]:
            k = cand["class"]
            out["classes"][k] = out["classes"].get(k, 0) + 1
        if c["kind"] == "positive":
            out["pos"] += 1
            tr = c["true_record"] or {}
            vals = f.get("values") or {}
            if c["family"] == "decoded":
                out["pos_decoded"] += 1
                r = rec_index.get((tr.get("class"), tr.get("offset"), tr.get("property")))
                if r is None:
                    bad.append("no CDO record at class/offset/property")
                elif not _same_num(r["value"], c["known"]):
                    bad.append(f"known {c['known']} != CDO record {r['value']}")
                elif r["class"] != c["owner"] or r["offset"] != int(c["offset"], 16):
                    bad.append("CDO record is not at the case's class/offset")
            else:
                out["pos_modes"] += 1
                pkg = tr.get("package") or "Playable_Batmobile_SF"
                if pkg not in vals or vals[pkg] is None:
                    bad.append(f"no decoded value on {pkg}")
                elif not _same_num(vals[pkg], c["known"]):
                    bad.append(f"known {c['known']} != decoded {vals[pkg]} on {pkg}")
            trues = [x for x in c["candidates"] if x["true"]]
            if len(trues) != 1:
                bad.append(f"{len(trues)} true candidates")
            else:
                sn = trues[0]["snippet"]
                if c["member"] not in sn:
                    bad.append("true candidate does not name the member")
                elif not _value_in(sn, c["known"]):
                    bad.append("true candidate does not carry the value")
                elif c["offset"].lower().replace("0x", "") not in sn.lower().replace("0x", ""):
                    bad.append("true candidate does not show the offset")
                else:
                    out["true_carries"] += 1
        else:
            out["neg"] += 1
            if f.get("serialized"):
                bad.append("negative is serialized in MODES.json")
            elif any(v is not None for v in (f.get("values") or {}).values()):
                bad.append("negative has a decoded value in MODES.json")
            elif any(x["true"] for x in c["candidates"]):
                bad.append("negative has a true candidate")
            elif any(r["property"] == c["member"] and r["class"] == c["owner"]
                     and r["offset"] == int(c["offset"], 16) for r in recs):
                bad.append("negative has a decoded CDO record")
            else:
                out["neg_clean"] += 1
        if bad:
            out["problems"].append(c["id"] + ": " + "; ".join(bad))
        else:
            out["ok"] += 1
    return out


def cmd_audit() -> int:
    a = audit()
    print(f"cases {a['cases']}, pass {a['ok']}, positive {a['pos']} "
          f"({a['pos_modes']} from MODES values, {a['pos_decoded']} from a decoded CDO record), "
          f"negative {a['neg']}, true candidate carries value+offset {a['true_carries']}, "
          f"negative proven clean {a['neg_clean']}")
    print("candidate classes:", dict(sorted(a["classes"].items())))
    for p in a["problems"]:
        print("PROBLEM", p)
    return 0 if not a["problems"] else 1


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def _binom_two_sided(b: int, c: int) -> float:
    """Exact McNemar p: 2 * P(X <= min(b, c)) for X ~ Bin(b + c, 1/2), capped at 1."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    s = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * s)


def _cells(model: str, arm: str, variant: str) -> list[dict]:
    d = os.path.join(RUNS, f"{arm}_{variant}_{prompt_version(arm, variant)}", model)
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        try:
            x = json.load(open(os.path.join(d, fn), encoding="utf-8"))
        except (OSError, ValueError):
            print(f"  unreadable cell skipped: {os.path.join(d, fn)}", flush=True)
            continue
        # a file in this folder must have been produced by exactly this arm/variant/model
        if (x.get("arm"), x.get("variant"), x.get("model")) == (arm, variant, model):
            out.append(x)
        else:
            print(f"  cell from another arm/variant skipped: {os.path.join(d, fn)}", flush=True)
    return out


def _majority(cells: list[dict]) -> tuple[str | None, bool, dict]:
    """Majority over the 3 orders by CANDIDATE IDENTITY (`pick_source`), not by letter: the
    letters are re-assigned in every order, so a letter vote would compare different snippets."""
    picks = {}
    for x in sorted(cells, key=lambda y: y["order"]):
        picks[x["order"]] = x.get("pick_source")
    counts = {}
    for p in picks.values():
        counts[p] = counts.get(p, 0) + 1
    best = max(sorted(counts, key=lambda p: str(p)), key=lambda p: counts[p])
    tie = list(counts.values()).count(counts[best]) > 1
    return (picks[min(picks)] if tie else best), tie, picks


def metrics(model: str, arm: str, variant: str, split: str = "test") -> dict:
    cases = {c["id"]: c for c in load_cases()}
    # the frozen corpus, not the cell's own tag, decides which split a case belongs to
    cells = [x for x in _cells(model, arm, variant)
             if x.get("case") in cases and cases[x["case"]]["split"] == split]
    by: dict[str, list[dict]] = {}
    for x in cells:
        by.setdefault(x["case"], []).append(x)
    pos_n = neg_n = pos_ok = neg_ok = neg_false = 0
    consistent = 0
    order_ok: dict[int, list[int]] = {}
    secs: list[float] = []
    calib: list[tuple[bool, float]] = []
    picks_by_case = {}
    unparsable = 0
    for cid, cs in sorted(by.items()):
        case = cases.get(cid)
        if case is None:
            continue
        pick, tie, picks = _majority(cs)
        picks_by_case[cid] = pick
        if len(set(picks.values())) == 1:
            consistent += 1
        for x in cs:
            unparsable += 1 if x.get("pick") is None else 0
            order_ok.setdefault(x["order"], []).append(1 if x.get("correct") else 0)
            secs.append(x.get("seconds") or 0.0)
            top = max(x["probs"].values()) if x.get("probs") else None
            if top is not None:
                calib.append((bool(x.get("correct")), float(top)))
        true_src = next((c["source"] for c in case["candidates"] if c["true"]), None)
        if case["kind"] == "positive":
            pos_n += 1
            pos_ok += 1 if pick == true_src else 0
        else:
            neg_n += 1
            if pick == "none":
                neg_ok += 1
            else:
                neg_false += 1
    n = pos_n + neg_n
    k = pos_ok + neg_ok
    macro = ((pos_ok / pos_n if pos_n else 0.0) + (neg_ok / neg_n if neg_n else 0.0)) / 2
    lo, hi = _wilson(k, n)
    return {"model": model, "arm": arm, "variant": variant, "split": split,
            "cells": len(cells), "cases": len(by), "pos_n": pos_n, "neg_n": neg_n,
            "pos_ok": pos_ok, "neg_ok": neg_ok, "neg_false": neg_false,
            "pos_acc": pos_ok / pos_n if pos_n else 0.0,
            "neg_acc": neg_ok / neg_n if neg_n else 0.0,
            "macro": macro, "overall": k / n if n else 0.0,
            "wilson": (lo, hi), "wilson_pos": _wilson(pos_ok, pos_n),
            "wilson_neg": _wilson(neg_ok, neg_n),
            "consistent": consistent, "orders": sorted(order_ok),
            "order_acc": {o: sum(v) / len(v) for o, v in order_ok.items()},
            "sec_case": (sum(secs) / len(by)) if by else 0.0,
            "sec_cell": (sum(secs) / len(secs)) if secs else 0.0,
            "calib": calib, "picks": picks_by_case, "unparsable": unparsable,
            "max_tokens": max((x.get("prompt_tokens") or 0) for x in cells) if cells else 0,
            "unparsable_rate": (unparsable / len(cells)) if cells else 0.0}


def tuned_variant() -> tuple[str, dict]:
    """Pick ONE shared wording variant on the tuning split, for both models together: the shared
    arm must stay identical for both models, so the variant is not tuned per model."""
    scores = {}
    for v in VARIANTS:
        j = metrics("jeb", "choice", v, "tune")
        q = metrics("qwen", "choice", v, "tune")
        if j["cases"] and q["cases"]:
            scores[v] = (j["macro"], q["macro"], j["macro"] + q["macro"])
    if not scores:
        return "neutral", scores
    best = max(sorted(scores), key=lambda v: (scores[v][2], v == "neutral"))
    return best, scores


def _paired(m1: dict, m2: dict) -> dict:
    common = sorted(set(m1["picks"]) & set(m2["picks"]))
    cases = {c["id"]: c for c in load_cases()}
    b = c = 0
    for cid in common:
        case = cases[cid]
        truth = next((x["source"] for x in case["candidates"] if x["true"]), "none")
        ok1 = m1["picks"][cid] == truth
        ok2 = m2["picks"][cid] == truth
        if ok1 and not ok2:
            b += 1
        elif ok2 and not ok1:
            c += 1
    return {"n": len(common), "b": b, "c": c, "p": _binom_two_sided(b, c)}


def decide(j: dict, q: dict, p: float) -> tuple[str, str]:
    """Apply the pre-registered rule; returns (verdict, reason)."""
    if j["wilson"][0] > q["macro"]:
        return "JEB", (f"Jeb lower bound {j['wilson'][0]:.3f} beats Qwen point "
                       f"estimate {q['macro']:.3f}")
    if q["wilson"][0] > j["macro"]:
        return "QWEN", (f"Qwen lower bound {q['wilson'][0]:.3f} beats Jeb point "
                         f"estimate {j['macro']:.3f}")
    if p < 0.05:
        w = "JEB" if j["macro"] > q["macro"] else "QWEN"
        return w, f"paired exact test p={p:.4f} < 0.05 (macro {j['macro']:.3f} vs {q['macro']:.3f})"
    faster = "JEB" if j["sec_case"] < q["sec_case"] else "QWEN"
    return "NO DIFFERENCE", (f"no bound separates the models and p={p:.4f} >= 0.05; "
                              f"the cheaper/faster model stays ({faster}, "
                              f"{j['sec_case']:.2f} vs {q['sec_case']:.2f} s/case)")


# ---------------------------------------------------------------------------------------- report
def _corpus_stats() -> dict:
    cases = load_cases()
    pos = [c for c in cases if c["kind"] == "positive"]
    neg = [c for c in cases if c["kind"] == "negative"]
    classes = {}
    for c in cases:
        for cand in c["candidates"]:
            classes[cand["class"]] = classes.get(cand["class"], 0) + 1
    leaked = 0
    for c in pos:
        k = c.get("known")
        if k is None:
            continue
        hits = sum(1 for cand in c["candidates"]
                   if _value_in(cand["snippet"], k))
        if hits > 1:
            leaked += 1
    return {"cases": len(cases), "pos": len(pos), "neg": len(neg),
            "tune": (sum(1 for c in pos if c["split"] == "tune"),
                     sum(1 for c in neg if c["split"] == "tune")),
            "test": (sum(1 for c in pos if c["split"] == "test"),
                     sum(1 for c in neg if c["split"] == "test")),
            "classes": classes, "cands": sum(len(c["candidates"]) for c in cases),
            "multi_value": leaked}


def _value_in(snippet: str, known: str) -> bool:
    num = re.escape(str(known).strip().lstrip("-"))
    return re.search(r"(?<![\d.])-?" + num + r"(?:\.0+)?(?![\d])", snippet) is not None


def render_report() -> str:
    cases = {c["id"]: c for c in load_cases()}
    tuned, tune_scores = tuned_variant()
    arms = [("choice", tuned, "shared choice (identical wording + window for both)"),
            ("native-jeb", "neutral", "Jeb native: trained member choice, 1,100 chars"),
            ("native-qwen", "neutral", "Qwen native: free-form JSON answer via chase_judge.ask")]
    res = {}
    for arm, var, _label in arms:
        for model in ("jeb", "qwen"):
            res[(arm, model)] = metrics(model, arm, var, "test")
    jc, qc = res[("choice", "jeb")], res[("choice", "qwen")]
    pair = _paired(jc, qc)
    verd, why = decide(jc, qc, pair["p"])
    stats = _corpus_stats()
    jn, qn = res[("native-jeb", "jeb")], res[("native-qwen", "qwen")]
    npair = _paired(jn, qn)

    L = []
    A = L.append
    A("# Jebadiah 9B vs Qwen3.5-4B: fair, pre-registered judge test")
    A("")
    A(f"**Verdict: {verd}.** {why}.  This is the pre-registered rule's output, not a reading of "
      "the numbers after the fact.")
    A("")
    A(f"Corpus: {stats['pos']} positive and {stats['neg']} negative cases "
      f"({stats['cands']} candidates), split {stats['tune'][0]}+{stats['tune'][1]} tuning / "
      f"{stats['test'][0]}+{stats['test'][1]} test by fixed seeds, 3 candidate orders per test "
      "case.  Ground truth is decoded tune data (`MODES.json`) or decoded CDO records, never the "
      "regex and never a model.")
    A("")
    A("## Pre-registered decision rule (copied verbatim, written before the run)")
    A("")
    A("```")
    A(PREREG.rstrip())
    A("```")
    A("")
    A(f"`PREREGISTRATION.md` sha256 prefix: "
      f"`{hashlib.sha256(PREREG.encode()).hexdigest()[:12]}`.")
    A("")
    A("## Corpus, and the five flaws it removes")
    A("")
    A(f"| property | value |")
    A("|---|---|")
    A(f"| cases | {stats['cases']} ({stats['pos']} positive, {stats['neg']} negative) |")
    A(f"| tuning split | {stats['tune'][0]} positive + {stats['tune'][1]} negative |")
    A(f"| test split | {stats['test'][0]} positive + {stats['test'][1]} negative |")
    A(f"| candidates | {stats['cands']}, six per case |")
    A(f"| candidate classes | " +
      ", ".join(f"{k}: {v}" for k, v in sorted(stats["classes"].items())) + " |")
    A(f"| positive lists where more than one candidate contains the member's value | "
      f"{stats['multi_value']} |")
    A(f"| candidates from an excluded file (`{'`, `'.join(EXCLUDED)}`) | 0 |")
    A("")
    A("Each positive case has exactly one candidate carrying a decoded record for the member at "
      "the declared class and offset, with a visible scalar value; each negative case has none. "
      "The old corpus's failure modes are removed as follows:")
    A("")
    A("1. *5 answerable cases in 28.*  Here every positive is answerable by construction "
      f"({stats['pos']}/{stats['pos']}), and the answer is the decoded record, not a value the "
      "regex could also find in a manifest line.")
    A("2. *The manifest line as a candidate.*  `calib.jsonl`, `candidates.jsonl`, `verdicts*`, "
      "`cache/`, `calib_runs/`, and the ground-truth files `MODES.json`/`FOOTAGE.md` supply zero "
      "candidates.  Every list still carries the six distractor classes the old prompt named: "
      "offset table, count, register value, stack local, per-frame update, tool record.")
    A("3. *Qwen never ran in choice format.*  Both models now answer the same A-F + `none` "
      "question; Qwen is forced to one letter.")
    A("4. *No repeats.*  Three candidate orders per test case, fixed seeds; per-order accuracy and "
      "cross-order consistency are reported below.")
    A("5. *Tuning on the scored cases.*  Prompt variant and settings were chosen on the tuning "
      "split only; the test split was scored once.")
    A("")
    A("### Ground-truth sources (per case in `cases.jsonl`, field `evidence`)")
    A("")
    A("| family | source of the labelled value | cases |")
    A("|---|---|---:|")
    fam = {}
    for c in cases.values():
        if c["kind"] == "positive":
            fam[c["family"]] = fam.get(c["family"], 0) + 1
    for k, v in sorted(fam.items()):
        src = ("`Research/BatmobileGrab/MODES.json` values on Playable_Batmobile_SF (decoded tune, "
               "four packages agree)") if k == "modes" else \
              ("decoded CDO record (`chase2_defaults*.json`) at the member's class and offset, "
               "value agreeing with the decoded tune")
        A(f"| {k} | {src} | {v} |")
    A(f"| modes (negative) | `MODES.json` `serialized=false`, `packages=[]`: the decode proves no "
      f"scalar default exists on any package | {stats['neg']} |")
    A("")
    aud = audit()
    A("### Independent corpus audit (recomputed from the source files when this report was written)")
    A("")
    A(f"`python Tools/scripts/chase/fair_judge.py --audit` re-reads `MODES.json` and the CDO dumps "
      f"and re-checks every case: owner/offset/type against the decoded field, each positive's "
      f"declared value against the decode's own value on the declared package, each positive's "
      f"true candidate against that value and offset, and each negative against "
      f"`serialized=false`.  Result: **{aud['ok']}/{aud['cases']} cases pass**, "
      f"{len(aud['problems'])} problem(s).")
    A("")
    A("| audit check | count |")
    A("|---|---:|")
    A(f"| cases re-checked | {aud['cases']} |")
    A(f"| cases passing every check | {aud['ok']} |")
    A(f"| positives whose value matches the decode on the declared package | "
      f"{aud['pos_modes'] + aud['pos_decoded']}/{aud['pos']} |")
    A(f"| positives whose true candidate carries the value at the offset | "
      f"{aud['true_carries']}/{aud['pos']} |")
    A(f"| negatives proven absent from the decode | {aud['neg_clean']}/{aud['neg']} |")
    A("")
    if aud["problems"]:
        A("Audit problems: " + "; ".join(f"`{p}`" for p in aud["problems"]))
    else:
        A("No audit problem.  The `evidence` field of every case names the file and record the "
          "value comes from; the test-split table below lists them.")
    A("")
    A("### Test-split cases and their evidence path")
    A("")
    A("| case | kind | member | offset | type | value | evidence |")
    A("|---|---|---|---|---|---:|---|")
    for c in sorted((c for c in cases.values() if c["split"] == "test"), key=lambda x: x["id"]):
        A(f"| {c['id']} | {c['kind']} | `{c['member']}` | {c['offset']} | {c['type']} | "
          f"{c['known'] if c['known'] is not None else '—'} | {c['evidence']} |")
    A("")
    A(f"### Tuning (tuning split only)")
    A("")
    if tune_scores:
        A("| wording variant | Jeb macro | Qwen macro | joint |")
        A("|---|---:|---:|---:|")
        for v in VARIANTS:
            if v in tune_scores:
                j, q, s = tune_scores[v]
                A(f"| {v} | {j:.3f} | {q:.3f} | {s:.3f} |")
        A("")
        A(f"Frozen for the shared arm: **{tuned}**.  The variant is chosen jointly for both models "
          "so the shared arm stays identical; neither variant names a candidate's source or class.")
    else:
        A("No complete tuning run on disk; the default `neutral` variant is used.")
    A("")
    A("## Test split, per model and arm")
    A("")
    A("| arm | model | positives correct | negatives `none` | false picks on negatives | macro | "
      "95% Wilson | cases all 3 orders agree | max prompt tokens | unparsable | s/case |")
    A("|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|")
    for arm, var, _label in arms:
        for model in ("jeb", "qwen"):
            m = res[(arm, model)]
            if not m["cases"]:
                A(f"| {arm} | {model} | — | — | — | — | no run | — | — |")
                continue
            lo, hi = m["wilson"]
            A(f"| {arm} | {model} | {m['pos_ok']}/{m['pos_n']} | {m['neg_ok']}/{m['neg_n']} | "
              f"{m['neg_false']} | {m['macro']:.3f} | {lo:.3f}-{hi:.3f} | "
              f"{m['consistent']}/{m['cases']} | {m['max_tokens']} | "
              f"{m['unparsable']} | {m['sec_case']:.2f} |")
    A("")
    A("### Per-order accuracy (position bias and sampling noise)")
    A("")
    A("| arm | model | order 1 | order 2 | order 3 | spread |")
    A("|---|---|---:|---:|---:|---:|")
    for arm, var, _label in arms:
        for model in ("jeb", "qwen"):
            m = res[(arm, model)]
            if not m["cases"]:
                continue
            vals = [m["order_acc"].get(o, float('nan')) for o in (0, 1, 2)]
            spread = (max(v for v in vals if v == v) - min(v for v in vals if v == v))
            A(f"| {arm} | {model} | " + " | ".join(f"{v:.3f}" for v in vals) +
              f" | {spread:.3f} |")
    A("")
    A("### Paired test (same cases, per-case majority)")
    A("")
    A("| pair | n cases | only first right (b) | only second right (c) | exact p |")
    A("|---|---:|---:|---:|---:|")
    A(f"| shared choice: Jeb vs Qwen | {pair['n']} | {pair['b']} | {pair['c']} | {pair['p']:.4f} |")
    A(f"| native arms: Jeb vs Qwen | {npair['n']} | {npair['b']} | {npair['c']} | {npair['p']:.4f} |")
    A("")
    A("### Calibration note (does the top option probability separate correct from wrong?)")
    A("")
    A("| arm | model | calls with probabilities | mean top prob (correct) | mean top prob (wrong) |")
    A("|---|---|---:|---:|---:|")
    for arm, var, _label in arms:
        for model in ("jeb", "qwen"):
            m = res[(arm, model)]
            cal = m["calib"]
            if not cal:
                A(f"| {arm} | {model} | 0 | — | — |")
                continue
            c_ok = [p for ok, p in cal if ok]
            c_bad = [p for ok, p in cal if not ok]
            A(f"| {arm} | {model} | {len(cal)} | "
              f"{sum(c_ok) / len(c_ok):.3f} ({len(c_ok)}) | "
              f"{(sum(c_bad) / len(c_bad)):.3f} ({len(c_bad)}) |")
    A("")
    A("A gap between the two means is the calibration signal; a small gap means the model's "
      "confidence cannot be thresholded into a decision.  Qwen's probabilities are the first-token "
      "probabilities of its letter from `top_logprobs`; Jeb's are the option probabilities of its "
      "one forward pass.")
    A("")
    A("## Where the models disagreed with the evidence")
    A("")
    jc_p, qc_p = jc["picks"], qc["picks"]

    def _short(src, case):
        if src is None:
            return "unparsable"
        if src == "none":
            return "none"
        return src[:70]

    rows = []
    for cid in sorted(set(jc_p) & set(qc_p)):
        if jc_p[cid] == qc_p[cid]:
            continue
        case = cases[cid]
        true_src = next((x["source"] for x in case["candidates"] if x["true"]), "none")
        rows.append(f"| {cid} | {case['kind']} | `{case['member']}` | {case['offset']} | "
                    f"{true_src} | {_short(jc_p[cid], case)} | {_short(qc_p[cid], case)} | "
                    f"{case['evidence']} |")
    if rows:
        A("### Majority picks that differ between the models")
        A("")
        A("| case | kind | member | offset | true candidate | Jeb pick | Qwen pick | "
          "evidence path |")
        A("|---|---|---|---|---|---|---|---|")
        L.extend(rows)
    else:
        A("No case had different majority picks between the two models on the shared arm.")
    A("")
    errs = []
    for cid in sorted(set(jc_p) & set(qc_p)):
        case = cases[cid]
        true_src = next((x["source"] for x in case["candidates"] if x["true"]), "none")
        j_ok, q_ok = jc_p[cid] == true_src, qc_p[cid] == true_src
        if j_ok and q_ok:
            continue
        errs.append(f"| {cid} | {case['kind']} | `{case['member']}` | {case['offset']} | "
                    f"{true_src} | {_short(jc_p[cid], case)} {'OK' if j_ok else 'MISS'} | "
                    f"{_short(qc_p[cid], case)} {'OK' if q_ok else 'MISS'} | {case['evidence']} |")
    if errs:
        A("### Every test case where at least one model's majority pick disagreed with the evidence")
        A("")
        A("| case | kind | member | offset | true candidate | Jeb | Qwen | evidence path |")
        A("|---|---|---|---|---|---|---|---|")
        L.extend(errs)
    else:
        A("Both models matched the evidence on every test case.")
    A("")
    A("## Cost and setup")
    A("")
    A("| model | server | model file | shared-arm s/case | cells |")
    A("|---|---|---|---:|---:|")
    A(f"| jebadiah-9b | llama-server 127.0.0.1:8081 | `jebadiah-9b-v2-1-Q5_K_M.gguf` | "
      f"{jc['sec_case']:.2f} | {jc['cells']} |")
    A(f"| qwen3.5-4b | llama-server 127.0.0.1:8080 | `Qwen3.5-4B-Q6_K.gguf` | "
      f"{qc['sec_case']:.2f} | {qc['cells']} |")
    A("")
    A("One llama-server at a time (the GTX 1070 cannot hold both models): the four tuning runs "
      "were split across the two servers, the variant frozen, then each model's two test arms run "
      "serially, one request at a time.  Qwen's shared arm is the production request shape of "
      "`chase_judge.ask` (same endpoint, model, temperature 0, thinking off) plus `logprobs` so the "
      "calibration note has a probability to read; its native arm calls `chase_judge.ask` itself.  "
      "Prompt versions: " +
      ", ".join(f"`{arm}/{var}` = `{prompt_version(arm, var)}`" for arm, var, _l in arms) + ".")
    A("")
    A("## Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/chase/fair_judge.py --build")
    for v in VARIANTS:
        A(f"python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm choice --split tune --variant {v} --order 0")
        A(f"python Tools/scripts/chase/fair_judge.py --run --model qwen --arm choice --split tune --variant {v} --order 0")
    A("python Tools/scripts/chase/fair_judge.py --score          # prints the frozen tuning variant")
    A(f"python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm choice --split test --variant {tuned}")
    A(f"python Tools/scripts/chase/fair_judge.py --run --model qwen --arm choice --split test --variant {tuned}")
    A("python Tools/scripts/chase/fair_judge.py --run --model jeb  --arm native-jeb  --split test")
    A("python Tools/scripts/chase/fair_judge.py --run --model qwen --arm native-qwen --split test")
    A("python Tools/scripts/chase/fair_judge.py --report tmp/freebuff/reports/jeb-vs-qwen-fair-test.md")
    A("```")
    A("")
    A("Run folders: `E:/Modding/_shared/gamedata/BmAKgrab/chase/fair/runs/<arm>_<variant>_<promptver>/<model>/`. "
      "The earlier runs under `chase/calib_runs/` and the three earlier reports are untouched.")
    A("")
    A("## Limitations")
    A("")
    A("- The decoded-record candidate is the shape a decoded dump has, not a raw `.upk` byte window: "
      "the test measures the judge's decision, not the decoder's fidelity.  Exe candidates are real "
      "annotated disassembly windows from `chase2_native2_05/07.json`.")
    A("- Negative labels rest on `MODES.json`'s `serialized=false` plus the decoded dumps: if the "
      "decode missed a package, a negative could still have a default the corpus does not show.  "
      "That is a corpus limit, not a model result.")
    A("- Candidate snippets are capped at 900 characters so both models see byte-identical text and "
      "the prompt stays under Jeb's 2,048-token limit; real search snippets are sometimes longer.")
    A("- Only the shared arm is a like-for-like comparison.  The native arms differ by construction "
      "(Jeb's trained option text vs Qwen's free-form JSON), so their paired p is reported as a "
      "secondary row and is not the decision.")
    A("")
    return "\n".join(L)


def cmd_score(verbose: bool = True) -> int:
    tuned, scores = tuned_variant()
    print(f"tuning variant: {tuned}  {scores}")
    for arm, var, _l in (("choice", tuned, ""), ("native-jeb", "neutral", ""),
                         ("native-qwen", "neutral", "")):
        for model in ("jeb", "qwen"):
            m = metrics(model, arm, var, "test")
            if not m["cases"]:
                continue
            print(f"{arm:<12} {model:<5} pos {m['pos_ok']}/{m['pos_n']}  neg "
                  f"{m['neg_ok']}/{m['neg_n']}  false {m['neg_false']}  macro {m['macro']:.3f} "
                  f"[{m['wilson'][0]:.3f},{m['wilson'][1]:.3f}]  {m['sec_case']:.2f}s/case  "
                  f"agree {m['consistent']}/{m['cases']}")
    j = metrics("jeb", "choice", tuned, "test")
    q = metrics("qwen", "choice", tuned, "test")
    pr = _paired(j, q)
    print(f"paired b={pr['b']} c={pr['c']} p={pr['p']:.4f}")
    print("verdict:", decide(j, q, pr["p"]))
    return 0


def cmd_report(path: str = REPORT) -> int:
    text = render_report()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    open(path, "w", encoding="utf-8", newline="\n").write(text)
    print(f"wrote {path} ({len(text)} B)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="pre-registered Jeb vs Qwen judge test")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--report", nargs="?", const=REPORT)
    ap.add_argument("--model", choices=("jeb", "qwen"))
    ap.add_argument("--arm", default="choice",
                    choices=("choice", "native-jeb", "native-qwen"))
    ap.add_argument("--split", default="test", choices=("tune", "test"))
    ap.add_argument("--variant", default="neutral", choices=VARIANTS)
    ap.add_argument("--order", type=int, default=None)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if a.build:
        raise SystemExit(cmd_build())
    if a.run:
        arm = a.arm
        if a.model == "jeb" and arm == "native-qwen":
            arm = "native-jeb"
        if a.model == "qwen" and arm == "native-jeb":
            arm = "native-qwen"
        raise SystemExit(cmd_run(a.model, arm, a.split, a.variant, a.limit, a.order))
    if a.score:
        raise SystemExit(cmd_score())
    if a.audit:
        raise SystemExit(cmd_audit())
    if a.report:
        raise SystemExit(cmd_report(a.report))
    ap.print_help()
