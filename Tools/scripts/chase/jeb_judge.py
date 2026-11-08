r"""jeb_judge.py - the chase judge on Jebadiah (a decision model: one forward pass, P(true), no generated text).

Same question as chase_judge.PROMPT ("does this snippet SET the default of `member`?") but asked as a typed
`noul` question: instructions + two criteria, state = the candidate. Returns the same verdict shape as
chase_judge (found true/false, value, why) plus `p` (P(true)). Triage only: every found=true is still
verified against the source offset (R4). Jeb cannot quote the literal, so `value` is read from the snippet
by regex and left empty when no single literal is visible; `lit` carries that regex literal whether or not
the verdict was found, so a threshold sweep of stored `p` values needs no model call.

The state Jeb sees is a **trimmed window** (`window()`): ~600 tokens (`WINDOW_CHARS`) — for disassembly
about 12 lines (`WINDOW_LINES`) — centred on the store for this member, with the annotate comment kept
(it sits on the store's own line). A snippet already inside the character budget is passed unchanged, so
a short text record is not line-trimmed for nothing. Jeb's training prompt limit is 2,048 tokens; whole
20-40 line snippets were cut there, which is why the short-window retest exists. `WINDOW_LINES`,
`WINDOW_CHARS` and `WINDOW_SPEC` are part of `prompt_version()`, so a window change gets its own run
folder instead of overwriting the previous calibration.

Server: E:\AI\agent_jebadiah-9b-q5.bat (llama-server, port 8081). Needs `pip install jebadiah-decide`.
"""
import functools
import hashlib
import json
import os
import re

THRESHOLD = 0.5          # P(true) >= this -> found; calibrate with chase_calibrate.py (--judge jeb)
BACKEND_URL = "http://127.0.0.1:8081"
WINDOW_LINES = 12        # disassembly lines kept, centred on the store for the member
WINDOW_CHARS = 2400      # ~600 tokens at ~4 chars/token; Jeb's training prompt limit is 2,048
WINDOW_SPEC = "anchor=store|member;gate=chars"   # what window() does, for prompt_version()

INSTRUCTIONS = (
    "Does this snippet SET the default value of the member `{member}` (declared on `{owner}`, type {type}, "
    "field offset {offset})? It is a default only if the literal value is visible in the snippet and is stored "
    "into [reg+{offset}] (or, for text, a key=value assignment of `{member}`) in constructor/initialisation code. "
    "It is NOT a default if the number is just the field offset, a count, a value from a register or memory with "
    "no constant visible, a store into a stack local ([rsp+..]/[rbp+..]), a per-frame update (+=, -=, times delta "
    "time), or a record written by a search tool (offset maps, name counts, verdicts)."
)
CRITERIA = {
    "true": "a literal default for the member is visibly stored into the member's field in initialisation code",
    "false": "anything else: offset table, count, register/memory value, stack local, per-frame update or tool record",
}
_NUM = re.compile(r"(?:=\s*(?:float\s+)?|\bfloat\s+|,\s*)(-?\d+(?:\.\d+)?(?:e[-+]?\d+)?)", re.I)


def question(c: dict) -> dict:
    fields = {k: c.get(k, "?") for k in ("member", "owner", "type", "offset")}
    return {"type": "noul", "instructions": INSTRUCTIONS.format(**fields), "criteria": CRITERIA}


def _anchor(lines: list[str], offset: str | None, member: str | None = None) -> int:
    """Index of the line that stores into the member: the offset with a store/bracket, else the line
    that names the member (a text record's field key), else the annotate comment
    (`; [0x..] = float X`), else the first line carrying a float literal."""
    off = (offset or "").lower().replace("0x", "").lstrip("0")
    for i, ln in enumerate(lines):
        low = ln.lower()
        if off and off in low.replace("0x", "") and "[" in low and ("=" in low or "," in low):
            return i
    if member:
        for i, ln in enumerate(lines):
            if member in ln:
                return i
    for i, ln in enumerate(lines):
        if re.search(r";\s*\[0x[0-9a-f]+\]\s*=\s*float", ln, re.I):
            return i
    for i, ln in enumerate(lines):
        if "= float" in ln:
            return i
    return 0


def window(snippet: str, offset: str | None = None, member: str | None = None,
           max_lines: int = WINDOW_LINES, max_chars: int = WINDOW_CHARS) -> str:
    """Trim a snippet to a window that fits Jeb's prompt limit: at most `max_chars` characters
    (~600 tokens) and, when a trim is needed, at most `max_lines` lines, centred on the member's
    store (the annotate comment stays: it is on that line). A snippet already inside the character
    budget is returned unchanged: the budget is tokens, so a short text record needs no line cap."""
    if len(snippet) <= max_chars:
        return snippet
    lines = snippet.splitlines()
    a = _anchor(lines, offset, member)
    lo = hi = a
    while (hi - lo + 1) < min(max_lines, len(lines)):
        grew = False
        if hi + 1 < len(lines) and sum(len(x) + 1 for x in lines[lo:hi + 2]) <= max_chars:
            hi += 1
            grew = True
        if (hi - lo + 1) < max_lines and lo > 0 and \
                sum(len(x) + 1 for x in lines[lo - 1:hi + 1]) <= max_chars:
            lo -= 1
            grew = True
        if not grew:
            break
    out = lines[lo:hi + 1]
    while out and sum(len(x) + 1 for x in out) > max_chars:
        if (a - lo) < (hi - a):
            out.pop(0)
        else:
            out.pop()
    return "\n".join(out)


def state(c: dict) -> dict:
    return {"source": c.get("source", "?"),
            "snippet": window(c.get("snippet", ""), c.get("offset"), c.get("member"))}


def prompt_id(c: dict) -> str:
    """stable text of what is asked, for cache keys"""
    return json.dumps([question(c), state(c)], sort_keys=True)


def prompt_version(mode: str = "noul") -> str:
    """Question + criteria + the window spec: a window change must get its own run folder.
    Each mode has its own version, so a choice run never overwrites a noul run."""
    if mode == "class":
        return hashlib.sha256(("class|" + CLASS_INSTRUCTIONS + "|" + json.dumps(CLASS_CRITERIA, sort_keys=True)
                               + f"|win{WINDOW_LINES}x{WINDOW_CHARS}").encode()).hexdigest()[:8]
    if mode == "member":
        return hashlib.sha256(("member|" + MEMBER_INSTRUCTIONS + f"|chars{MEMBER_CHARS}").encode()).hexdigest()[:8]
    return hashlib.sha256((INSTRUCTIONS + json.dumps(CRITERIA) +
                           f"|win{WINDOW_LINES}x{WINDOW_CHARS}|{WINDOW_SPEC}").encode()).hexdigest()[:8]


def make(url: str = BACKEND_URL, size: str = "9b"):
    from jebadiah_decide import Jeb
    return Jeb("llama-server", size=size, url=url)


def literal(snippet: str):
    m = re.search(r";\s*\[0x[0-9a-f]+\]\s*=\s*float\s+(-?[\d.eE+-]+)", snippet) or _NUM.search(snippet)
    return m.group(1) if m else ""


def judge(jeb, c: dict, threshold: float = THRESHOLD, mode: str = "noul") -> dict:
    if mode == "class":
        return judge_class(jeb, c)
    out = jeb.decide(state(c), {"d": question(c)})
    a = out["answers"]["d"]
    p = float(a["noul"])
    found = p >= threshold
    lit = literal(c.get("snippet", ""))
    return {"found": found, "value": lit if found else "", "lit": lit, "p": round(p, 4),
            "why": f"jeb P(true)={p:.3f} (threshold {threshold})", "warnings": out.get("warnings", [])}


# =============================================================================================
# Choice modes (2026-11-07).  The noul mode above asks a long open question and the model answers
# P("true") -- on the shipped example that shape scores the correct answer only 0.15-0.20.  These
# modes copy the two shapes `jebadiah_decide/defaults.EXAMPLE` was trained on instead: a short
# instruction and one short criterion per option, answered as `choice`.
#   class   one question per candidate: which of the seven classes does this snippet belong to?
#   member  one question per case: which candidate (A..F) shows the member's default, or none?
# Both are scored on the *choice* (and separately on the regex literal), never on the literal
# alone, so a regex miss cannot count as a Jeb miss.
# =============================================================================================
CLASS_KEYS = ("default", "offset", "count", "runtime", "stack", "frame", "tool")
CLASS_CRITERIA = {
    "default": "a literal stored into the member's field, in initialisation code",
    "offset": "a number equal to the field offset, from an offset table",
    "count": "how many files or packages contain the name",
    "runtime": "a value from a register or memory, no constant visible",
    "stack": "a store into a stack local ([rsp+..] or [rbp+..])",
    "frame": "the field is changed by arithmetic every frame",
    "tool": "a record written by the search tool, not the game",
}
CLASS_INSTRUCTIONS = "What is this snippet showing for `{member}` (field offset {offset})?"
MEMBER_INSTRUCTIONS = ("Which snippet shows the default value of `{member}` "
                       "(declared on `{owner}`, type {type}, field offset {offset})?")
MEMBER_CHARS = 1100      # per candidate; six of them stay inside 2,048 prompt tokens
MEMBER_NONE = "none"
PROMPT_TOKEN_LIMIT = 2040


def class_question(c: dict) -> dict:
    return {"type": "choice",
            "instructions": CLASS_INSTRUCTIONS.format(member=c.get("member", "?"),
                                                      offset=c.get("offset", "?")),
            "criteria": dict(CLASS_CRITERIA)}


def class_state(c: dict) -> dict:
    return {"source": c.get("source", "?"),
            "snippet": window(c.get("snippet", ""), c.get("offset"), c.get("member"))}


def member_question(c: dict, cands: list[dict]) -> dict:
    crit = {}
    for i, cand in enumerate(cands):
        src = str(cand.get("source", "?")).replace("E:/Modding/_shared/gamedata/BmAKgrab/chase/", "")
        crit[chr(65 + i)] = f"snippet {chr(65 + i)} from {src}"
    crit[MEMBER_NONE] = "no snippet stores a literal default for the member"
    return {"type": "choice",
            "instructions": MEMBER_INSTRUCTIONS.format(
                member=c.get("member", "?"), owner=c.get("owner") or "-",
                type=c.get("type") or "-", offset=c.get("offset", "?")),
            "criteria": crit}


def member_state(c: dict, cands: list[dict], per_chars: int = MEMBER_CHARS) -> dict:
    parts = []
    for i, cand in enumerate(cands):
        body = window(cand.get("snippet", ""), cand.get("offset") or c.get("offset"),
                      c.get("member"), max_lines=10, max_chars=per_chars)
        parts.append(f"CANDIDATE {chr(65 + i)} ({cand.get('source', '?')}):\n{body}")
    return {"member": c.get("member", "?"), "candidates": "\n\n".join(parts)}


def _tokens(jeb, state, q) -> tuple[int, bool]:
    """Prompt size the model actually receives (the renderer truncates states over its own
    limit, but the contract here is that our window fits *before* that happens)."""
    rd = jeb.renderer.render(state, q)
    ids = jeb._encode(rd.prompt)
    return (len(ids) if ids is not None else 0), bool(rd.truncated)


def judge_class(jeb, c: dict) -> dict:
    q = class_question(c)
    st = class_state(c)
    n, tr = _tokens(jeb, st, q)
    for _ in range(8):
        if n <= PROMPT_TOKEN_LIMIT:
            break
        st = {"source": st["source"],
              "snippet": window(c.get("snippet", ""), c.get("offset"), c.get("member"),
                               max_lines=8, max_chars=max(600, int(len(st["snippet"]) * 0.75)))}
        n, tr = _tokens(jeb, st, q)
    out = jeb.decide(st, {"d": q})
    a = out["answers"]["d"]
    probs = a.get("probabilities") or {}
    return {"mode": "class", "class": a["choice"], "confidence": a.get("confidence"),
            "p_default": probs.get("default"), "probabilities": probs,
            "prompt_tokens": n, "truncated": tr, "warnings": out.get("warnings", [])}


def judge_member(jeb, c: dict, cands: list[dict]) -> dict:
    q = member_question(c, cands)
    per = MEMBER_CHARS
    st = member_state(c, cands, per)
    n, tr = _tokens(jeb, st, q)
    while n > PROMPT_TOKEN_LIMIT and per > 350:
        per = int(per * 0.8)
        st = member_state(c, cands, per)
        n, tr = _tokens(jeb, st, q)
    out = jeb.decide(st, {"d": q})
    a = out["answers"]["d"]
    probs = a.get("probabilities") or {}
    return {"mode": "member", "choice": a["choice"], "confidence": a.get("confidence"),
            "probabilities": probs, "prompt_tokens": n, "truncated": tr,
            "warnings": out.get("warnings", [])}


# ------------------------------------------------------------------------- choice calibration run
CALIB = r"E:/Modding/_shared/gamedata/BmAKgrab/chase/calib.jsonl"
RUNS = r"E:/Modding/_shared/gamedata/BmAKgrab/chase/calib_runs"


def _calib_cases() -> list[dict]:
    return [json.loads(l) for l in open(CALIB, encoding="utf-8") if l.strip()]


def _cands(c: dict, max_n: int = 6, search_name: str = "v1") -> list[dict]:
    import smart_search as ss
    return _cands_cached(c["member"], c.get("owner"), c["offset"], c.get("type"),
                         max_n, search_name)


@functools.lru_cache(maxsize=256)
def _cands_cached(member: str, owner: str | None, offset: str | None, ftype: str | None,
                   max_n: int, search_name: str) -> list[dict]:
    """The frozen search half is deterministic; scoring asks for the same list twice (class and
    member modes), so it is searched once per case per process."""
    import smart_search as ss
    return ss.search(member, owner, offset, ftype, ("exe", "text"), max_n, search_name)


def _reach(c: dict, cands: list[dict]) -> list[str]:
    import smart_search as ss
    if c.get("known") is None:
        return []
    return [x["source"] for x in cands if ss.literal_in(x.get("snippet", ""), c["known"])]


def choice_dir(mode: str, search_name: str = "v1") -> str:
    suffix = "" if search_name == "current" else "_" + search_name.replace("-", "") + "search"
    return os.path.join(RUNS, f"jeb_{mode}_{prompt_version(mode)}{suffix}")


def run_choice(mode: str, max_n: int = 6, search_name: str = "v1", limit: int = 0) -> str:
    import time
    jeb = make()
    d = choice_dir(mode, search_name)
    os.makedirs(d, exist_ok=True)
    n = 0
    for c in _calib_cases():
        out = os.path.join(d, c["id"] + ".json")
        if os.path.exists(out):
            continue
        t0 = time.time()
        cands = _cands(c, max_n, search_name)
        reach = _reach(c, cands)
        rec = {"mode": mode, "prompt_version": prompt_version(mode), "search": search_name,
               "case": {k: c.get(k) for k in ("id", "kind", "family", "member", "owner",
                                              "offset", "type", "known", "provenance")},
               "candidates": len(cands), "reach_sources": reach, "rows": []}
        if mode == "class":
            for cand in cands:
                v = judge_class(jeb, {**c, **cand})
                expected = "default" if cand["source"] in reach else "not-default"
                v.update({"source": cand["source"], "route": cand.get("route"),
                          "expected": expected,
                          "correct": (v["class"] == "default") == (expected == "default")})
                rec["rows"].append(v)
                print(f"{c['id']} {cand['source'][-40:]:<40} -> {v['class']:<8} "
                      f"exp {expected:<11} {'OK' if v['correct'] else 'MISS'}", flush=True)
        else:
            v = judge_member(jeb, c, cands)
            pick = v["choice"]
            idx = ord(pick) - 65 if len(pick) == 1 and "A" <= pick <= "F" else None
            chosen = cands[idx] if idx is not None and idx < len(cands) else None
            right = (chosen is not None and chosen["source"] in reach) if c.get("kind") != "negative" \
                else (pick == MEMBER_NONE)
            lit = literal(chosen.get("snippet", "")) if chosen else ""
            v.update({"source": chosen["source"] if chosen else None, "expected_sources": reach,
                      "correct": bool(right), "literal": lit,
                      "literal_matches": bool(chosen is not None and c.get("known") is not None
                                              and _same_literal(c["known"], lit))})
            rec["rows"].append(v)
            print(f"{c['id']} pick {pick:<5} {'OK' if right else 'MISS'} "
                  f"lit={lit!r} known={c.get('known')}", flush=True)
        rec["seconds"] = round(time.time() - t0, 2)
        json.dump(rec, open(out, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
        n += 1
        if limit and n >= limit:
            break
    print(f"ran {n} case(s) into {d}", flush=True)
    return d


def _same_literal(known, lit) -> bool:
    try:
        return bool(lit) and abs(float(str(known)) - float(str(lit))) <= 1e-6
    except (TypeError, ValueError):
        return str(known).strip().lower() == str(lit).strip().lower()


def _stores_default(c: dict, cand: dict) -> bool:
    """Does this candidate *store* the member's known literal into the member's field?

    This is the ground truth the class labels encode: the literal is in the snippet AND it sits
    on a line addressing the member's offset (`[reg+0xNNN]` with the literal), or -- for a text
    record -- a `value` key carrying it. Literal presence alone is not enough: an exe snippet can
    mention the value inside a stack store or an unrelated constant, and Jeb refusing that is
    correct, not a miss.
    """
    known = c.get("known")
    if known is None:
        return False
    import smart_search as ss
    sn = cand.get("snippet", "")
    if not ss.literal_in(sn, known):
        return False
    num = re.escape(str(known).strip().lstrip("-"))
    lit = re.compile(r"(?<![\d.])-?" + num + r"(?:\.0+)?(?![\d])")
    off = (c.get("offset") or "").lower().replace("0x", "").lstrip("0")
    for ln in sn.splitlines():
        if off and off in ln.lower().replace("0x", "") and "[" in ln and lit.search(ln):
            return True
    if c.get("member") and c["member"] in sn and re.search(r'"?value"?\s*[:=]\s*' + num, sn):
        return True
    return False


def score_choice(mode: str, search_name: str = "v1") -> dict:
    """Two independent scores: the model's choice, and the regex literal on its own.

    Expected labels come from `_stores_default` (literal *and* the field store), not from the
    stored `reach_sources` alone, so a candidate that merely contains the number is scored as a
    non-default and Jeb refusing it counts as right. The old literal-present label is kept as
    `reach_*` so both readings can be reported: it is the label the earlier runs used, and it is
    satisfied by the `calib.jsonl` manifest line itself, which the frozen search returns as a
    candidate.
    """
    d = choice_dir(mode, search_name)
    rows, tot = [], {"cases": 0, "chosen": 0, "literal": 0, "cand": 0, "cand_ok": 0,
                     "tp": 0, "fp": 0, "fn": 0, "tn": 0, "cut": 0, "max_tokens": 0,
                     "reach_ok": 0, "reach_pos": 0, "reach_neg_fp": 0}
    for c in _calib_cases():
        p = os.path.join(d, c["id"] + ".json")
        if not os.path.exists(p):
            rows.append({**c, "run": False})
            continue
        r = json.load(open(p, encoding="utf-8"))
        cands = _cands(c, 6, search_name)
        store = {x.get("source"): _stores_default(c, x) for x in cands}
        tot["cases"] += 1
        rs = r.get("rows", [])
        if mode == "class":
            for v in rs:
                exp = bool(store.get(v.get("source")))
                got = v.get("class") == "default"
                v["expected"] = "default" if exp else "not-default"
                v["correct"] = exp == got
                tot["cand"] += 1
                tot["cand_ok"] += 1 if v["correct"] else 0
                tot["max_tokens"] = max(tot["max_tokens"], v.get("prompt_tokens") or 0)
                tot["cut"] += 1 if v.get("truncated") else 0
                tot["tp"] += 1 if exp and got else 0
                tot["fp"] += 1 if (not exp) and got else 0
                tot["fn"] += 1 if exp and not got else 0
                tot["tn"] += 1 if (not exp) and not got else 0
            hit = any(v["correct"] and v["expected"] == "default" for v in rs)
            picked = next((v["class"] for v in rs if v.get("expected") == "default"), None)
            reach = set(r.get("reach_sources") or [])
            rhit = any(v.get("class") == "default" and v.get("source") in reach for v in rs)
            if c.get("kind") == "negative":
                tot["reach_neg_fp"] += 1 if rhit else 0
            else:
                tot["reach_pos"] += 1
                tot["reach_ok"] += 1 if rhit else 0
            rows.append({**c, "run": True, "hit": hit, "picked": picked, "literal": None,
                         "reach_hit": rhit,
                         "rows": rs, "store_sources": [k for k, vv in store.items() if vv]})
        else:
            v = rs[0] if rs else {}
            src = v.get("source")
            if c.get("kind") == "negative":
                hit = v.get("choice") == MEMBER_NONE
            else:
                hit = bool(store.get(src))
            tot["max_tokens"] = max(tot["max_tokens"], v.get("prompt_tokens") or 0)
            tot["cut"] += 1 if v.get("truncated") else 0
            tot["chosen"] += 1 if hit else 0
            tot["literal"] += 1 if v.get("literal_matches") else 0
            reach = set(r.get("reach_sources") or [])
            if c.get("kind") == "negative":
                rhit = v.get("choice") == MEMBER_NONE
                tot["reach_neg_fp"] += 0 if rhit else 1
            else:
                rhit = src in reach
                tot["reach_pos"] += 1
                tot["reach_ok"] += 1 if rhit else 0
            rows.append({**c, "run": True, "hit": bool(hit), "reach_hit": bool(rhit),
                         "picked": v.get("choice"),
                         "literal": v.get("literal"), "literal_ok": bool(v.get("literal_matches")),
                         "rows": rs, "store_sources": [k for k, vv in store.items() if vv]})
    return {"mode": mode, "dir": d, "version": prompt_version(mode), "rows": rows, **tot}


def print_choice_scores(search_name: str = "v1") -> None:
    for mode in ("class", "member"):
        s = score_choice(mode, search_name)
        if not s["cases"]:
            print(f"{mode}: no stored run in {s['dir']}")
            continue
        print(f"\n### mode `{mode}` prompt `{s['version']}` ({s['dir']})")
        print(f"cases {s['cases']}, max prompt tokens {s['max_tokens']}, truncated {s['cut']}")
        if mode == "class":
            prec = s["tp"] / (s["tp"] + s["fp"]) if (s["tp"] + s["fp"]) else 0.0
            rec = s["tp"] / (s["tp"] + s["fn"]) if (s["tp"] + s["fn"]) else 0.0
            print(f"candidate class accuracy {s['cand_ok']}/{s['cand']}; default-class TP {s['tp']} "
                  f"FP {s['fp']} FN {s['fn']} TN {s['tn']} -> precision {prec:.3f} recall {rec:.3f}")
            pos = [r for r in s["rows"] if r.get("run") and r["kind"] != "negative"]
            neg = [r for r in s["rows"] if r.get("run") and r["kind"] == "negative"]
            print(f"case-level: default found on {sum(1 for r in pos if r['hit'])}/{len(pos)} "
                  f"non-negative cases; false-positive cases {sum(1 for r in neg if r['hit'])}/{len(neg)}")
            print(f"case-level, literal-present label: {s['reach_ok']}/{s['reach_pos']} non-negative, "
                  f"{s['reach_neg_fp']}/{len(neg)} negatives with a wrong default")
        else:
            print(f"right candidate (store label) {s['chosen']}/{s['cases']}; "
                  f"right candidate (literal-present label) {s['reach_ok']}/{s['reach_pos']} "
                  f"non-negative + {s['reach_neg_fp']} neg FP; "
                  f"literal also matched {s['literal']}/{s['cases']}")
        print("| id | kind | pick | chosen right | literal | literal-present |")
        print("|---|---|---|---:|---:|---:|")
        for r in s["rows"]:
            if not r.get("run"):
                print(f"| {r['id']} | {r['kind']} | NO RUN | — | — | — |")
                continue
            print(f"| {r['id']} | {r['kind']} | {r.get('picked') if r.get('picked') is not None else ('default' if r.get('hit') else '-')} "
                  f"| {'yes' if r['hit'] else 'no'} | {r.get('literal') or '—'} "
                  f"| {'yes' if r.get('reach_hit') else 'no'} |")


# ------------------------------------------------------------- old noul runs: rank-based view
def _auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    s = 0.0
    for a in pos:
        for b in neg:
            s += 1.0 if a > b else (0.5 if a == b else 0.0)
    return s / (len(pos) * len(neg))


def rank_view(directory: str) -> None:
    """AUC of per-case best P(true), and the case-level sweep 0.05..0.5 that was never run."""
    cases = _calib_cases()
    per = []
    for c in cases:
        p = os.path.join(directory, c["id"] + ".json")
        if not os.path.exists(p):
            continue
        r = json.load(open(p, encoding="utf-8"))
        vs = [v for v in r.get("verdicts", []) if v.get("p") is not None]
        if not vs:
            continue
        best = max(vs, key=lambda v: float(v["p"]))
        per.append({"id": c["id"], "kind": c["kind"], "known": c.get("known"),
                    "best_p": float(best["p"]), "best_lit": best.get("lit") or "",
                    "best_source": best.get("source"), "reach_sources": r.get("reach_sources") or []})
    pos = [x["best_p"] for x in per if x["kind"] == "positive"]
    fnd = [x["best_p"] for x in per if x["kind"] == "found"]
    neg = [x["best_p"] for x in per if x["kind"] == "negative"]
    a_pos, a_all = _auc(pos, neg), _auc(pos + fnd, neg)
    print(f"\n{directory}")
    print(f"AUC P(true) positive-vs-negative {a_pos:.3f}" if a_pos is not None else "AUC unavailable")
    print(f"AUC P(true) (positive+found)-vs-negative {a_all:.3f}" if a_all is not None else "")
    print(f"cases with p: {len(per)} (pos {len(pos)}, found {len(fnd)}, neg {len(neg)})")
    print("| threshold | positive hit | found hit | negative FP |")
    print("|---:|---:|---:|---:|")
    t = 0.05
    while t <= 0.5001:
        ph = sum(1 for x in per if x["kind"] == "positive" and x["best_p"] >= t)
        fh = sum(1 for x in per if x["kind"] == "found" and x["best_p"] >= t)
        nf = sum(1 for x in per if x["kind"] == "negative" and x["best_p"] >= t)
        print(f"| {t:.2f} | {ph}/{len(pos)} | {fh}/{len(fnd)} | {nf}/{len(neg)} |")
        t = round(t + 0.05, 2)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Jebadiah judge: noul, class-choice, member-choice")
    ap.add_argument("--calib", choices=("class", "member"), help="run that choice mode on calib.jsonl")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--rank", metavar="DIR", help="AUC + 0.05..0.5 sweep of a stored noul run")
    ap.add_argument("--max", type=int, default=6)
    ap.add_argument("--search", dest="search_name", default="v1")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--versions", action="store_true")
    a = ap.parse_args()
    if a.versions:
        for m in ("noul", "class", "member"):
            print(m, prompt_version(m))
    if a.calib:
        run_choice(a.calib, a.max, a.search_name, a.limit)
    if a.summary:
        print_choice_scores(a.search_name)
    if a.rank:
        rank_view(a.rank)
