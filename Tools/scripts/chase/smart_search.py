"""smart_search.py - one call: search ONE arbitrary member, judge every candidate, rank the hits.

Stage 1 (search)  `chase_candidates.member_candidates(member, owner, offset, type, routes)` - the
                  same EXE store scanner and text scanner the row chase uses, plus the decoded-table
                  route (`table`: the BmAK value tables and decoded CDO/default dumps, trimmed to
                  the row that names the member), ranked so a decoded-table hit first, then a hit
                  whose window names the owning class or looks like object initialisation.
Stage 2 (judge)   `chase_judge.PROMPT` / `ask` / `parse` - one request per candidate to the local
                  llama-server (default `http://127.0.0.1:8080`, model `qwen3.5-4b`). The judge only
                  triages; a `found=true` still has to be verified against the address it names
                  before any value enters a record (R4).

Offline         if `GET <base>/health` does not answer in 3 s the tool prints `judge offline`,
                lists the candidates **unjudged** and exits 3. Nothing is invented and no partial
                verdict is written to the cache.
Cache           every verdict is stored at E:/Modding/_shared/gamedata/BmAKgrab/chase/cache/<xx>/<sha256>.json,
                sha256 = the exact prompt text (the snippet plus the question and the model name).
                A repeated query costs nothing; a prompt revision changes the hash, so a stale
                verdict can never be reused after the judge's prompt changes.

Usage
  python Tools/scripts/chase/smart_search.py --member AirControl --owner Pawn --offset 0x448 \
         --type float [--max N] [--routes exe,text,table] [--url http://127.0.0.1:8080] \
         [--model qwen3.5-4b] [--json-out <path>] [--no-cache] [--quiet]

Exit codes: 0 = judged (whatever the verdicts), 2 = bad arguments, 3 = judge offline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chase_candidates as cc  # noqa: E402  (the search half - imported, never re-implemented)
import chase_judge as cj       # noqa: E402  (the judge kit - imported, never re-implemented)
import jeb_judge as jj         # noqa: E402  (optional Jebadiah decision-model judge, --judge jeb)

CACHE = os.path.join(r"E:\Modding\_shared\gamedata\BmAKgrab", "chase", "cache")
DEFAULT_URL = "http://127.0.0.1:8080"
PROMPT_VERSION = hashlib.sha256(cj.PROMPT.encode()).hexdigest()[:8]


def prompt_for(c: dict) -> str:
    return cj.PROMPT.format(**{k: c.get(k, "?") for k in
                               ("member", "owner", "type", "offset", "source", "snippet")})


def cache_key(prompt: str, model: str) -> str:
    return hashlib.sha256((model + "\0" + prompt).encode("utf-8")).hexdigest()


def cache_path(key: str) -> str:
    return os.path.join(CACHE, key[:2], key + ".json")


def cache_read(key: str):
    try:
        return json.load(open(cache_path(key), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def cache_write(key: str, rec: dict) -> None:
    path = cache_path(key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, sort_keys=True)
        fh.write("\n")


def judge_online(base: str, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(base.rstrip("/") + "/health", timeout=timeout) as r:
            return json.load(r).get("status") == "ok"
    except (urllib.error.URLError, OSError, ValueError):
        return False


def search_mod(name: str):
    """The search half to use: the live `chase_candidates`, or the frozen `chase_candidates_v1`
    (calibration only - it shows what the judge does when a candidate list is not pre-filtered)."""
    if name == "v1":
        import chase_candidates_v1 as v1
        return v1
    return cc


def search(member: str, owner: str | None = None, offset: str | None = None,
           ftype: str | None = None, routes: tuple[str, ...] = cc.ROUTES,
           max_n: int = 40, search_name: str = "current") -> list[dict]:
    mod = search_mod(search_name)
    cands = mod.member_candidates(member, owner, offset, ftype, routes)
    return cands[:max_n] if max_n else cands


def literal_in(snippet: str, expect: str) -> bool:
    """Does the snippet contain the expected literal? Calibration only (`--expect`): it separates a
    search miss (the value is not in any candidate) from a judge miss (it is there and was refused)."""
    try:
        x = float(expect)
    except (TypeError, ValueError):
        return expect.strip().strip("\"'") in snippet
    num = re.escape(expect.strip().lstrip("-"))
    pat = r"(?<![\d.])-?" + num + r"(?:\.0+)?(?![\d])"
    return re.search(pat, snippet) is not None


def run(member: str, owner: str | None = None, offset: str | None = None,
        ftype: str | None = None, routes: tuple[str, ...] = cc.ROUTES, max_n: int = 40,
        base: str = DEFAULT_URL, model: str = "qwen3.5-4b", use_cache: bool = True,
        expect: str | None = None, progress=None, search_name: str = "current",
        judge: str = "qwen", threshold: float = jj.THRESHOLD) -> dict:
    """Search + judge one member. Returns the full record; never raises for an offline judge."""
    t0 = time.time()
    jeb = None
    if judge == "jeb":
        base = base if base != DEFAULT_URL else jj.BACKEND_URL
        model = "jebadiah-9b"
    cands = search(member, owner, offset, ftype, routes, max_n, search_name)
    rec = {"query": {"member": member, "owner": owner, "offset": offset, "type": ftype,
                     "routes": list(routes), "max": max_n, "model": model, "expect": expect,
                     "search": search_name,
                     "judge": judge, "prompt_version": jj.prompt_version() if judge == "jeb" else PROMPT_VERSION, "judged_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
           "candidates": len(cands), "judged": 0, "cache_hits": 0, "offline": False,
           "verdicts": [], "seconds": 0.0}
    if expect is not None:
        rec["reach"] = any(literal_in(c["snippet"], expect) for c in cands)
        rec["reach_sources"] = [c["source"] for c in cands if literal_in(c["snippet"], expect)]
    if not cands or not judge_online(base):
        rec["offline"] = bool(cands)
        rec["seconds"] = round(time.time() - t0, 2)
        rec["unjudged"] = [{"source": c["source"], "route": c["route"]} for c in cands]
        return rec
    url = base.rstrip("/") + "/v1/chat/completions"
    t_judge = 0.0
    if judge == "jeb":
        jeb = jj.make(base)
    for c in cands:
        prompt = jj.prompt_id(c) + f"|{threshold}" if judge == "jeb" else prompt_for(c)
        key = cache_key(prompt, model)
        hit = cache_read(key) if use_cache else None
        if hit is not None:
            rec["cache_hits"] += 1
            v = hit
        else:
            t = time.time()
            if judge == "jeb":
                parsed = jj.judge(jeb, c, threshold)
                raw = ""
            else:
                raw = cj.ask(url, model, prompt)
                parsed = cj.parse(raw)
            t_judge += time.time() - t
            v = {"p": parsed.get("p") if parsed else None, "found": parsed["found"] if parsed else None,
                 "value": parsed.get("value") if parsed else None,
                 "why": parsed.get("why") if parsed else None}
            # jeb: the regex literal is kept even when the verdict is not found (threshold sweeps
            # read it), and `warnings` carries the 2048-token snippet-cut flags for counting.
            if parsed and parsed.get("lit") is not None:
                v["lit"] = parsed["lit"]
            if parsed and parsed.get("warnings"):
                v["warnings"] = parsed["warnings"]
            if parsed is None:
                v["raw"] = raw[:500]
            v.update({"id": c["id"], "source": c["source"], "route": c["route"],
                      "prompt_version": PROMPT_VERSION})
            if use_cache:
                cache_write(key, v)
        if progress:
            progress(c, v)
        rec["judged"] += 1
        rec["verdicts"].append({**v, "id": c["id"], "source": c["source"], "route": c["route"]})
    rec["seconds"] = round(time.time() - t0, 2)
    rec["judge_seconds"] = round(t_judge, 2)
    rec["found"] = [v for v in rec["verdicts"] if v.get("found") is True]
    rec["unparsable"] = [v for v in rec["verdicts"] if v.get("found") is None]
    return rec


def print_result(rec: dict, quiet: bool = False) -> None:
    q = rec["query"]
    print(f"{q['member']} ({q['owner'] or '-'}, {q['type'] or '-'}, {q['offset'] or '-'}): "
          f"{rec['candidates']} candidates, {rec['judged']} judged, "
          f"{rec['cache_hits']} from cache, prompt v{PROMPT_VERSION}")
    if rec["offline"]:
        print("judge offline")
        for c in rec.get("unjudged", []):
            print(f"  {c['route']:<4} {c['source']}")
        print(f"counts: candidates {rec['candidates']}, judged 0, judge offline, "
              f"seconds {rec['seconds']}")
        return
    if not rec["candidates"]:
        print("no candidates (nothing at this offset/name in the corpus)")
        print(f"counts: candidates 0, judged 0, seconds {rec['seconds']}")
        return
    found = sorted(rec["found"], key=lambda v: (v.get("value") in (None, ""), v["source"]))
    print(f"found=true {len(found)}:")
    for v in found:
        print(f"  {v['source']}  value={v.get('value')!r}  {v.get('why') or ''}")
    if not quiet:
        print("judged false:")
        for v in rec["verdicts"]:
            if v.get("found") is False:
                print(f"  {v['source']}  {v.get('why') or ''}")
        if rec["unparsable"]:
            print("unparsable:")
            for v in rec["unparsable"]:
                print(f"  {v['source']}  {(v.get('raw') or '')[:80]!r}")
    judged = rec["judged"] or 1
    print(f"counts: candidates {rec['candidates']}, judged {rec['judged']} "
          f"(cache {rec['cache_hits']}), found {len(found)}, unparsable {len(rec['unparsable'])} "
          f"({len(rec['unparsable']) / judged:.1%}), seconds {rec['seconds']} "
          f"(judge {rec.get('judge_seconds', 0)} -> {(rec.get('judge_seconds') or 0) / judged:.2f} s/candidate)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--member", required=True)
    ap.add_argument("--owner")
    ap.add_argument("--offset")
    ap.add_argument("--type", dest="ftype")
    ap.add_argument("--routes", default="exe,text,table",
                    help="comma list of routes: exe,text,table (default all three; "
                         "`exe,text` reproduces the old search)")
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--model", default="qwen3.5-4b")
    ap.add_argument("--judge", default="qwen", choices=("qwen", "jeb"),
                    help="qwen = chase_judge prompt on llama-server :8080; jeb = Jebadiah decision model on :8081")
    ap.add_argument("--threshold", type=float, default=jj.THRESHOLD, help="jeb: P(true) cut-off")
    ap.add_argument("--json-out")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--expect", help="calibration only: the known value, to record whether any "
                                      "candidate snippet contains it (a search miss vs a judge miss)")
    ap.add_argument("--search", dest="search_name", default="current",
                    choices=("current", "v1", "table"),
                    help="search half: `current` (exe + text + table routes), `table` (the same, run "
                         "as its own calibration folder) or the frozen `v1` (calibration only)")
    a = ap.parse_args()
    routes = tuple(r.strip() for r in a.routes.split(",") if r.strip())
    bad = [r for r in routes if r not in cc.ROUTES]
    if bad:
        print(f"unknown route(s) {bad}; known: {','.join(cc.ROUTES)}", file=sys.stderr)
        return 2
    rec = run(a.member, a.owner, a.offset, a.ftype, routes, a.max, a.url, a.model,
              not a.no_cache, a.expect, search_name=a.search_name,
              judge=a.judge, threshold=a.threshold)
    print_result(rec, a.quiet)
    if a.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.json_out)), exist_ok=True)
        with open(a.json_out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rec, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print(f"wrote {a.json_out}", file=sys.stderr)
    return 3 if rec["offline"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
