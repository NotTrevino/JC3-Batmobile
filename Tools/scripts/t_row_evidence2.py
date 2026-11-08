#!/usr/bin/env python3
"""t_row_evidence2.py - evidence audit of resolved T rows 41..90 (the second slice).

Same method and the same status vocabulary as `Tools/scripts/t_row_evidence.py` (which audited
rows 1..40). That script, `T_ROWS.jsonl` and `ROW_EVIDENCE_AUDIT.md` are read-only here; this
script writes only `Working/Translation/ROW_EVIDENCE_AUDIT2.md`.

The ledger has no `evidence` field: a row's evidence is the file named anywhere in its cells (the
source-member cell, the value cell, the verify cell) or in `why`.

**Resolved** = disposition `keep`, `edit`, `epe`, `out` or `superseded` (145 of 198 rows);
`next` and `blocked` are not resolved. Rows 41..90 of that resolved list are audited here.

What is tested per row, unchanged from the first script:

  * every `.md/.json/.jsonl/.py/.csv/.txt` path named in the row, resolved directly from the repo
    root, or by a unique basename, or - when a basename occurs more than once - by content: the
    candidate that accounts for the most of the row's quoted values, if that candidate is unique;
  * the quoted numbers from the value cell, compared **by value** in three grades:
      exact   equal to a number in the file (`2.570` == `2.57`)
      rounded a number in the file rounds to it at the quoted precision (`2.4589` -> `2.459`)
      absent  no number in the file is either
    Numbers under 3 digits are weak and are used only when the row has no strong number at all;
  * when a row quotes no number, the backticked member/identifier tokens (containing `.` or `_`,
    >= 6 chars) from the source cell, as normalised substrings. A token that is only the cited
    file's own name is not counted.

Statuses: OK / OK (rounded) / OK (weak) / OK (member name) / PARTIAL (some quoted numbers absent) /
VALUE-NOT-FOUND / DEAD PATH / NO PATH (the row names no file at all) / NOT-TESTABLE (a file is
named but the row quotes nothing searchable).

A numeric match proves the digits are in the file, not that the file still means what the row says;
"a value that differs" in the sense of the same field holding another number needs the field's
row/key, which the ledger does not name - that stays UNKNOWN.

`--check` re-reads the ledger, re-resolves every path, re-tests every token, asserts the oracles
below, asserts that the first script, the ledger and the first audit are unchanged, and compares
the document byte-for-byte.

    python Tools/scripts/t_row_evidence2.py --write
    python Tools/scripts/t_row_evidence2.py --check
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
OUT = os.path.join(ROOT, "Working", "Translation", "ROW_EVIDENCE_AUDIT2.md")
PREV_SCRIPT = os.path.join(HERE, "t_row_evidence.py")
PREV_AUDIT = os.path.join(ROOT, "Working", "Translation", "ROW_EVIDENCE_AUDIT.md")

RESOLVED = ("keep", "edit", "epe", "out", "superseded")
SKIP = 40
PICK = 50
# sha256 of T_ROWS.jsonl as recorded in the first audit's header; if it differs, a ledger edit
# happened between the two audits and this slice is no longer comparable with the first.
LEDGER_SHA_FIRST_AUDIT = "8996b60a5370d932f437fd138d23dc15358d41e24e1026306d7b02172dc0e5f4"
REF = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|json|jsonl|py|csv|txt))")
NUM = re.compile(r"-?\d+(?:\.\d+)?")
BACKTICK = re.compile(r"`([^`]+)`")

EXACT, ROUNDED, ABSENT = 2, 1, 0


def norm(text: str) -> str:
    return (text.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
            .replace(",", ""))


def is_num(tok: str) -> bool:
    return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", tok))


def decimals(tok: str) -> int:
    return len(tok.split(".")[1]) if "." in tok else 0


def sha_of(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


class File:
    """A cited file: normalised text, the numbers in it, and the three-grade value test."""

    def __init__(self, path: str):
        self.path = path
        self.body = norm(open(path, encoding="utf-8", errors="replace").read())
        self.numbers = [float(t) for t in NUM.findall(self.body)]
        base = os.path.basename(path)
        self.names = {base, base.rsplit(".", 1)[0]}

    def grade(self, tok: str) -> int:
        if tok in self.names:
            return ABSENT  # citing a script proves nothing by the script naming itself
        if not is_num(tok):
            return ROUNDED if norm(tok) in self.body else ABSENT
        value = float(tok)
        if any(abs(n - value) <= 1e-9 * max(1.0, abs(value)) for n in self.numbers):
            return EXACT
        tol = 0.5 * 10 ** (-decimals(tok)) + 1e-12
        if any(abs(n - value) <= tol for n in self.numbers):
            return ROUNDED
        return ABSENT

    def count(self, toks: list[str]) -> int:
        return sum(1 for t in toks if self.grade(t) != ABSENT)


def build_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__", "Builds")]
        for fn in files:
            index.setdefault(fn, []).append(os.path.join(dirpath, fn))
    return index


def refs_of(row: dict) -> list[str]:
    text = " ".join(str(c) for c in row["cells"]) + " " + str(row.get("why", ""))
    out: list[str] = []
    for m in REF.finditer(text):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out


def numbers_of(row: dict) -> tuple[list[str], list[str]]:
    value = norm(str(row["cells"][4]) if len(row["cells"]) > 4 else "")
    strong: list[str] = []
    weak: list[str] = []
    for tok in NUM.findall(value):
        bucket = strong if len(tok.lstrip("-").replace(".", "")) >= 3 else weak
        if tok not in strong and tok not in weak:
            bucket.append(tok)
    return strong, weak


def members_of(row: dict) -> list[str]:
    out: list[str] = []
    for quoted in BACKTICK.findall(str(row["cells"][2])):
        q = quoted.strip()
        if len(q) >= 6 and ("." in q or "_" in q) and q not in out:
            out.append(q)
    return out


def main(write: bool) -> int:
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    raw = open(LEDGER, "rb").read()
    ledger_sha = hashlib.sha256(raw).hexdigest()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    resolved = [r for r in rows if r["dispo"] in RESOLVED]
    picked = resolved[SKIP:SKIP + PICK]
    first_ids = [r["id"] for r in resolved[:SKIP]]

    ok(len(rows) == 198, f"ledger holds 198 rows ({len(rows)})", str(len(rows)))
    ok(len(resolved) == 145, f"{len(resolved)} rows are resolved under the stated rule "
       "(keep/edit/epe/out/superseded; next and blocked excluded)", str(len(resolved)))
    ok(len(picked) == PICK, f"resolved rows 41..90 selected ({len(picked)})")
    ok(all(r["dispo"] in RESOLVED for r in picked),
       "every audited row is resolved")
    ok(not ({r["id"] for r in picked} & set(first_ids)),
       "no audited id appears among the first audit's 40 resolved rows",
       str(sorted({r["id"] for r in picked} & set(first_ids))))
    ok(ledger_sha == LEDGER_SHA_FIRST_AUDIT,
       "T_ROWS.jsonl sha256 equals the one recorded in the first audit "
       f"({LEDGER_SHA_FIRST_AUDIT[:16]}...)", ledger_sha)

    index = build_index()
    opened: dict[str, File] = {}
    audit: list[dict] = []
    for row in picked:
        refs = refs_of(row)
        strong, weak = numbers_of(row)
        members = members_of(row)
        paths: list[dict] = []
        for ref in refs:
            direct = os.path.join(ROOT, ref)
            if os.path.isfile(direct):
                paths.append({"ref": ref, "path": os.path.relpath(direct, ROOT).replace("\\", "/"),
                              "how": "direct", "candidates": 1,
                              "file": opened.setdefault(direct, File(direct))})
                continue
            cand = sorted(index.get(os.path.basename(ref), []))
            if not cand:
                # The shared path regex lists `json` before `jsonl`, so a row citing `X.jsonl`
                # yields ref `X.json`. A dead ref is therefore re-tried with one more `l`; the
                # status stays DEAD PATH (the method's verdict) and the real file is recorded
                # as a hint so the document can say what the row actually pointed at.
                alt = sorted(index.get(os.path.basename(ref) + "l", []))
                hint = None
                if len(alt) == 1:
                    hf = opened.setdefault(alt[0], File(alt[0]))
                    hint = {"path": os.path.relpath(alt[0], ROOT).replace("\\", "/"),
                            "hits": [t for t in (strong or weak) if hf.grade(t) != ABSENT]}
                paths.append({"ref": ref, "path": None, "how": "dead", "candidates": 0,
                              "file": None, "hint": hint})
                continue
            files = [opened.setdefault(p, File(p)) for p in cand]
            if len(files) == 1:
                paths.append({"ref": ref,
                              "path": os.path.relpath(cand[0], ROOT).replace("\\", "/"),
                              "how": "basename", "candidates": 1, "file": files[0]})
                continue
            toks = strong or weak
            exact_of = {f.path: sum(1 for t in toks if f.grade(t) == EXACT) for f in files}
            scored = sorted(((exact_of[f.path], f.count(toks), f.path, f) for f in files),
                            key=lambda t: (t[0], t[1]), reverse=True)
            best = (scored[0][0], scored[0][1])
            winners = [t for t in scored if (t[0], t[1]) == best]
            if best != (0, 0) and len(winners) == 1:
                _e, _n, _p, f = winners[0]
                paths.append({"ref": ref, "path": os.path.relpath(f.path, ROOT).replace("\\", "/"),
                              "how": f"basename x{len(files)}, resolved by content "
                                     f"({best[0]} exact value(s))", "candidates": len(files),
                              "file": f})
            else:
                f = files[0]
                paths.append({"ref": ref, "path": os.path.relpath(f.path, ROOT).replace("\\", "/"),
                              "how": f"AMBIGUOUS: {len(files)} candidates", "candidates": len(files),
                              "file": f})

        live = [p for p in paths if p["file"] is not None]

        def best_grade(tok: str) -> tuple[int, str]:
            top, where = ABSENT, ""
            for p in live:
                g = p["file"].grade(tok)
                if g > top:
                    top, where = g, os.path.basename(p["path"])
            return top, where

        graded = {tok: best_grade(tok) for tok in (strong or weak)}
        exact = [t for t, (g, _w) in graded.items() if g == EXACT]
        rounded = [t for t, (g, _w) in graded.items() if g == ROUNDED]
        absent = [t for t, (g, _w) in graded.items() if g == ABSENT]
        member_hits = [t for t in members if best_grade(t)[0] != ABSENT]
        dead = [p["ref"] for p in paths if p["path"] is None]
        ambiguous = [p for p in paths if "AMBIGUOUS" in p["how"]]

        if not refs:
            status = "NO PATH"
            note = "the row names no file; its evidence is a decoded value, not a citation"
        elif dead:
            status = "DEAD PATH"
            note = "not found: " + ", ".join(dead)
        elif graded and not absent and not rounded:
            status = "OK"
            note = f"all {len(exact)} quoted number(s) found"
        elif graded and not absent:
            status = "OK (rounded)"
            note = (f"{len(exact)} exact, {len(rounded)} by rounding at the quoted precision "
                    f"({', '.join(rounded[:4])})")
        elif graded and (exact or rounded):
            status = "PARTIAL"
            note = (f"{len(exact) + len(rounded)} of {len(graded)} found; absent: "
                    + ", ".join(absent[:5]))
        elif graded:
            status = "VALUE-NOT-FOUND"
            note = "none of " + ", ".join(list(graded)[:4]) + " occurs in the named file"
        elif members:
            if member_hits:
                status = "OK (member name)"
                note = f"no number quoted; member name found: {member_hits[0]}"
            else:
                status = "VALUE-NOT-FOUND"
                note = "no number quoted; none of the member names occurs: " + ", ".join(members[:3])
        else:
            status = "NOT-TESTABLE"
            note = "a file is named but the row quotes nothing searchable"
        if ambiguous and status.startswith("OK"):
            if status.endswith(")"):
                status = status[:-1] + ", ambiguous path)"
            else:
                status += " (ambiguous path)"
            note += f"; {ambiguous[0]['candidates']} same-name files, content did not single one out"
        audit.append({"id": row["id"], "dispo": row["dispo"], "refs": refs, "paths": paths,
                      "numbers": list(graded), "exact": exact, "rounded": rounded,
                      "absent": absent, "members": members, "member_hits": member_hits,
                      "status": status, "note": note, "value": str(row["cells"][4])[:120]})

    # ------------------------------------------------------------------ oracles on the audit itself
    ok(len(audit) == PICK, f"every selected row has an audit line ({len(audit)})")
    by_status: dict[str, int] = {}
    for a in audit:
        by_status[a["status"]] = by_status.get(a["status"], 0) + 1
    ok(sum(by_status.values()) == PICK, f"statuses sum to {PICK}", str(by_status))
    ok(all(not a["absent"] for a in audit if a["status"].startswith("OK")),
       "no OK row has a quoted number absent")
    ok(all(a["absent"] for a in audit if a["status"] == "PARTIAL"),
       "every PARTIAL row names at least one absent number")
    ok(all(p["file"] is not None for a in audit for p in a["paths"] if p["how"] != "dead"),
       "every non-dead citation opened a real file")
    ambiguous_all = [p for a in audit for p in a["paths"] if "AMBIGUOUS" in p["how"]]
    ok(all(p["candidates"] > 1 for p in ambiguous_all),
       f"{len(ambiguous_all)} same-name path(s) left ambiguous, each with its candidate count")
    content_picked = [p for a in audit for p in a["paths"] if "resolved by content" in p["how"]]
    ok(all(p["candidates"] > 1 for p in content_picked),
       f"{len(content_picked)} same-name path(s) resolved by content, candidates recorded")
    ok(all(a["numbers"] or a["members"] or a["status"] in ("NO PATH", "NOT-TESTABLE")
           for a in audit),
       "every audited row quotes a number/member, names no file, or is not testable")
    ok(os.path.isfile(PREV_SCRIPT) and os.path.isfile(PREV_AUDIT),
       "the first script and the first audit both exist (they are read, never written)")
    prev_script_sha, prev_audit_sha = sha_of(PREV_SCRIPT), sha_of(PREV_AUDIT)

    # ------------------------------------------------------------------ the document
    no_path = [a for a in audit if a["status"] == "NO PATH"]
    dead_rows = [a for a in audit if a["status"] == "DEAD PATH"]
    not_found = [a for a in audit if a["status"] == "VALUE-NOT-FOUND"]
    partial = [a for a in audit if a["status"] == "PARTIAL"]
    cited = [a for a in audit if a["refs"]]
    flagged = [a for a in audit if a["status"] in ("VALUE-NOT-FOUND", "NO PATH")]
    same_name = [(a, p) for a in audit for p in a["paths"] if p["candidates"] > 1]
    hinted = [(a, p) for a in audit for p in a["paths"] if p.get("hint")]

    def count(prefix: str) -> int:
        return sum(1 for a in audit if a["status"].startswith(prefix))

    L: list[str] = []
    ap = L.append
    ap("# T-row evidence audit - resolved rows 41..90")
    ap("")
    ap("Generated by `python Tools/scripts/t_row_evidence2.py --write`; re-derived and compared")
    ap("byte-for-byte by `--check`. Read-only: `Working/Translation/T_ROWS.jsonl` was opened")
    ap(f"(sha256 `{ledger_sha}`, the same one the first audit recorded), never written.")
    ap("The first slice's script and output are unchanged by this run:")
    ap(f"`Tools/scripts/t_row_evidence.py` sha256 `{prev_script_sha}`,")
    ap(f"`Working/Translation/ROW_EVIDENCE_AUDIT.md` sha256 `{prev_audit_sha}`.")
    ap("")
    ap(f"**{len(audit)} rows audited: {count('OK')} fully found ({count('OK (rounded')} by "
       f"rounding, {count('OK (weak')} on a weak token, {count('OK (member')} on a member name), "
       f"{len(partial)} partial, {len(not_found)} with no quoted value in the file, "
       f"{len(dead_rows)} dead path, {len(no_path)} citing no file at all, "
       f"{count('NOT-TESTABLE')} not testable.**")
    ap("")
    ap("Same method and status vocabulary as the first audit, applied to rows 41..90 of the")
    ap("resolved list (rows 1..40 are in `ROW_EVIDENCE_AUDIT.md`). The ledger has no `evidence`")
    ap("field, so a row's evidence is read as *the file it names anywhere in its cells or `why`*.")
    ap("")
    ap("Resolved = disposition `keep`, `edit`, `epe`, `out` or `superseded` (145 of 198 rows);")
    ap("`next` and `blocked` are excluded by that rule.")
    ap("")
    ap(f"## Rows with VALUE-NOT-FOUND or NO PATH ({len(flagged)} of {len(audit)})")
    ap("")
    ap("Every row in this slice carrying one of those two statuses, with its id:")
    ap("")
    for a in flagged:
        ap(f"* `{a['id']}` ({a['dispo']}) - **{a['status']}** - {a['note']}")
    if not flagged:
        ap("None.")
    ap("")
    ap("## The 50 rows")
    ap("")
    ap("| # | id | dispo | evidence ref(s) | resolved to | quoted numbers | status | note |")
    ap("|---:|---|---|---|---|---|---|---|")
    for i, a in enumerate(audit, start=41):
        refs = ", ".join(f"`{r}`" for r in a["refs"]) or "-"
        dest = ", ".join(f"`{p['path']}`" for p in a["paths"] if p["path"]) or "-"
        toks = ", ".join(a["numbers"][:3]) or ", ".join(a["members"][:2]) or "-"
        ap(f"| {i} | `{a['id']}` | {a['dispo']} | {refs} | {dest} | {toks} | {a['status']} | "
           f"{a['note']} |")
    ap("")
    ap("## Rows citing no file")
    ap("")
    ap(f"{len(no_path)} of the {len(audit)} rows name no file at all. Their evidence is a decoded")
    ap("value plus a member path (`T_ROWS.jsonl` cell 3), not a citation, so nothing can be opened")
    ap("and no quoted number can be re-tested from the ledger alone:")
    ap("")
    for a in no_path:
        ap(f"* `{a['id']}` ({a['dispo']}) - {a['value'].replace('|', '/')}")
    ap("")
    ap("## Quoted values absent from the cited file (partial matches)")
    ap("")
    ap("The only shape of \"a value that differs\" the ledger lets this audit prove: the row quotes")
    ap("numbers, and the cited file does not account for some of them after the rounded comparison.")
    ap("")
    if partial:
        for a in partial:
            dest = ", ".join(f"`{p['path']}`" for p in a["paths"] if p["path"])
            ap(f"* `{a['id']}` ({a['dispo']}): {a['note']} - in {dest}")
    else:
        ap("None.")
    ap("")
    ap("## No quoted value found at all")
    ap("")
    if not_found:
        for a in not_found:
            dest = ", ".join(f"`{p['path']}`" for p in a["paths"] if p["path"])
            ap(f"* `{a['id']}` ({a['dispo']}): {a['note']} - in {dest}")
    else:
        ap("None.")
    ap("")
    ap("A numeric absence can also agree with the row: a row that quotes a value it says is")
    ap("**missing**, or cites a script rather than that script's output, fails this presence test")
    ap("without being wrong. The test cannot tell the two apart; each line above is for hand check.")
    ap("")
    ap("## Dead paths")
    ap("")
    if dead_rows:
        for a in dead_rows:
            ap(f"* `{a['id']}` - {a['note']}")
        if hinted:
            ap("")
            ap(f"**Caveat on {len(hinted)} of these.** They end in `.json` and a file with the same")
            ap("stem plus `.jsonl` exists, so the ref was truncated by the shared path regex")
            ap("(`(?:md|json|jsonl|...)` matches `json` inside `jsonl`) before the lookup. The")
            ap("real file is opened here and the row's quoted tokens tested against it; the")
            ap("statuses above are left as the shared method produces them, so this slice stays")
            ap("comparable with the first audit:")
            ap("")
            for a, p in hinted:
                h = p["hint"]
                found = ", ".join(h["hits"]) if h["hits"] else "none"
                ap(f"* `{a['id']}` -> `{p['ref']}` means `{h['path']}`; quoted token(s) found "
                   f"there: {found}")
            ap("")
            ap("So neither dead ref is a missing evidence file; the missing thing is the fourth")
            ap("character of the extension in the ledger text.")
    else:
        ap(f"None. Every path named by the {len(cited)} rows that cite a file exists on disk:")
        ap("directly, by a unique basename, or by content among same-name files.")
    ap("")
    ap("## Same-name citations")
    ap("")
    for a, p in same_name:
        ap(f"* `{a['id']}` -> `{p['ref']}`: {p['candidates']} files carry that name; {p['how']};")
        ap(f"  this audit used `{p['path']}`")
    if not same_name:
        ap("None: no cited basename occurs more than once in the repo.")
    ap("")
    ap("## What this does not test")
    ap("")
    ap("* **A field holding a different number.** Proving the file disagrees needs the field's")
    ap("  row/key, which the ledger does not name, so it is UNKNOWN rather than clean.")
    ap("* **Rows 1..40 and 91..145 of the resolved set** - out of scope by the card.")
    ap("* **Whether the cited decode is still what the build ships** - that is `t_rows.py check`")
    ap("  and the per-card `--check` scripts' business.")
    ap("")
    ap("## Oracles re-run by `--check`")
    ap("")
    for c in checks:
        ap(f"* {'PASS' if c['ok'] else 'FAIL'} {c['oracle']}")
    ap("")
    ap("## Labels")
    ap("")
    ap("Decoded: the ledger rows, the cited files' contents, the resolved paths, the sha256 of the")
    ap("three read-only inputs. Derived: the statuses and counts, the rounding comparison, the")
    ap("content-disambiguation scores. UNKNOWN: a differing value behind a named field, a row with")
    ap("no file, and anything behind a citation that is still ambiguous.")
    ap("")
    text = "\n".join(L)

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    print("statuses: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    if failed:
        return 1
    if write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(OUT, ROOT).replace(os.sep, '/')}")
        return 0
    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if current != text:
        for line in difflib.unified_diff(current.splitlines(), text.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        print("FAIL document differs from the regenerated text")
        return 1
    print("PASS document: ROW_EVIDENCE_AUDIT2.md matches the regenerated text")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write ROW_EVIDENCE_AUDIT2.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
