#!/usr/bin/env python3
"""t_row_evidence3.py - evidence audit of resolved T rows 91..145 (the third and last slice).

Same method and the same status vocabulary as `Tools/scripts/t_row_evidence.py` (rows 1..40)
and `t_row_evidence2.py` (rows 41..90).  Those scripts, their outputs and `T_ROWS.jsonl` are
read-only here; this script writes only `Working/Translation/ROW_EVIDENCE_AUDIT3.md`.

The ledger has no `evidence` field: a row's evidence is the file named anywhere in its cells
or in `why`, exactly as in the two earlier audits.

**Resolved** = disposition `keep`, `edit`, `epe`, `out` or `superseded` (145 of 198 rows);
`next` (40) and `blocked` (13) are not resolved.  Rows 91..145 of that resolved list (55 rows)
are audited here.

**One correction to the earlier two scripts, forced by this slice.**  They read the quoted
value from `cells[4]` unconditionally.  That is right only for the T-1 / T-2b table shape.  This
slice is drawn from six other documents whose tables have different columns (T-14 has nine
columns), so the value column is now read from the *table header the row sits under* in its own
document, never from a fixed index:

    value column  = the column whose header names the BmAK side ("BmAK ..." / "values" /
                    any "... value" column), first match in header order
    member column = attachment / slot / member / JC3 target / JC3 carrier / source, first match

The mapping used for every row is printed in the document, and the rows whose status would
change under the old blind `cells[4]` read are listed (derived, this slice only).

What is tested per row, unchanged:

  * every `.md/.json/.jsonl/.py/.csv/.txt` path named in the row, resolved directly from the repo
    root, or by a unique basename, or - when a basename occurs more than once - by content: the
    candidate that accounts for the most of the row's quoted values, if that candidate is unique;
  * the quoted numbers from the value cell, compared **by value** in three grades:
      exact   equal to a number in the file (`2.570` == `2.57`)
      rounded a number in the file rounds to it at the quoted precision (`2.4589` -> `2.459`)
      absent  no number in the file is either
    Numbers under 3 digits are weak and are used only when the row has no strong number at all;
  * when a row quotes no number, the backticked member/identifier tokens (containing `.` or `_`,
    >= 6 chars) from the member cell, as normalised substrings.  A token that is only the cited
    file's own name is not counted.

Statuses: OK / OK (rounded) / OK (weak) / OK (member name) / PARTIAL (some quoted numbers absent) /
VALUE-NOT-FOUND / DEAD PATH / NO PATH (the row names no file at all) / NOT-TESTABLE (a file is
named but the row quotes nothing searchable).

**NO PATH grouped by document**: after the per-row audit, the rows that cite no file are counted
per document (T-1, T-2b, T-3, ...) and the document that lacks a cited source most often - by
count and by share of its audited rows - is named.  The same grouping is also shown for all 145
resolved rows, labelled as context rather than as this audit's finding.

A numeric match proves the digits are in the file, not that the file still means what the row
says; "a value that differs" in the sense of the same field holding another number needs the
field's row/key, which the ledger does not name - that stays UNKNOWN.

`--check` re-reads the ledger, re-resolves every path, re-tests every token, re-derives the
document grouping, asserts the oracles below, asserts that the two earlier scripts, their two
audits and the ledger are unchanged, and compares the document byte-for-byte.

    python Tools/scripts/t_row_evidence3.py --write
    python Tools/scripts/t_row_evidence3.py --check
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
WORK = os.path.join(ROOT, "Working", "Translation")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
OUT = os.path.join(WORK, "ROW_EVIDENCE_AUDIT3.md")
PREV_SCRIPTS = [os.path.join(HERE, "t_row_evidence.py"), os.path.join(HERE, "t_row_evidence2.py")]
PREV_AUDITS = [os.path.join(WORK, "ROW_EVIDENCE_AUDIT.md"),
               os.path.join(WORK, "ROW_EVIDENCE_AUDIT2.md")]
DOCS = {"T-1": "T1_TRANSLATION.md", "T-2b": "T2_TRANSLATION.md", "T-3": "T3_COVERAGE.md",
        "T-13": "T13_FX.md", "T-14": "T14_LIGHTS.md", "T-7": "T7_WEAPONS.md",
        "T-20": "T15_WORLD.md", "T-15": "T11_MODES.md"}

RESOLVED = ("keep", "edit", "epe", "out", "superseded")
SKIP = 90
PICK = 55
# sha256 of the read-only inputs, as recorded by the two earlier audits: if either differs, a
# ledger or script edit happened between the audits and this slice is no longer comparable.
LEDGER_SHA_FIRST_AUDIT = "8996b60a5370d932f437fd138d23dc15358d41e24e1026306d7b02172dc0e5f4"
# `jsonl` must precede `json` in the alternation, or `objects.jsonl` is read as `objects.json`
# and reported dead; the first two scripts had the longer suffix last.
REF = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:jsonl|json|md|py|csv|txt))")
# A citation of a binary artefact (an .effc, .ee, .bank, .bin ...) is still a citation, but a
# text resolver cannot open it. NO PATH rows that name one are counted separately so the
# per-document grouping does not call a cited row uncited.
REF_ANY = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:effc|ee|aaf|bank|bnk|wem|dds|rbm|pfx|toc|cst|blk|bin|pck|bak|wav|ogg|mp3|xml|ini|as|ys|hash))\b",
                     re.IGNORECASE)
TEXT_EXT = (".md", ".json", ".jsonl", ".py", ".csv", ".txt")
COLOUR_Q = re.compile(r"\d+\s*,\s*\d+\s*,\s*\d+")
NUM = re.compile(r"-?\d+(?:\.\d+)?")
BACKTICK = re.compile(r"`([^`]+)`")
ROW_RE = re.compile(r"^\|\s*(T-[A-Z]{1,3}\d+)\s*\|")
SEP_RE = re.compile(r"^\|[\s:|-]+\|\s*$")

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


def split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


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


def headers_by_id() -> dict[str, list[str]]:
    """{row id: the header cells of the table the row sits under, in its own document}."""
    out: dict[str, list[str]] = {}
    for tag, name in DOCS.items():
        path = os.path.join(WORK, name)
        header: list[str] | None = None
        lines = open(path, encoding="utf-8").read().splitlines()
        for i, line in enumerate(lines):
            if not line.startswith("|"):
                continue
            if i + 1 < len(lines) and SEP_RE.match(lines[i + 1]):
                header = split_cells(line)
                continue
            m = ROW_RE.match(line)
            if m and header is not None:
                out.setdefault(m.group(1), header)
    return out


def column_of(headers: list[str], kind: str) -> int:
    low = [h.lower() for h in headers]
    if kind == "value":
        for test in (lambda h: "bmak" in h and ("colour" in h or "(" in h),
                     lambda h: h.strip().startswith("values"),
                     lambda h: "bmak" in h,
                     lambda h: "value" in h):
            for i, h in enumerate(low):
                if test(h):
                    return i
    else:
        for key in ("attachment", "slot", "member", "jc3 target", "jc3 carrier",
                    "source", "carrier"):
            for i, h in enumerate(low):
                if key in h:
                    return i
    return 4 if kind == "value" else 2


def refs_of(row: dict) -> list[str]:
    text = " ".join(str(c) for c in row["cells"]) + " " + str(row.get("why", ""))
    out: list[str] = []
    for m in REF.finditer(text):
        if m.group(1) not in out:
            out.append(m.group(1))
    return out


def numbers_of(text: str) -> tuple[list[str], list[str]]:
    value = norm(text)
    strong: list[str] = []
    weak: list[str] = []
    for tok in NUM.findall(value):
        bucket = strong if len(tok.lstrip("-").replace(".", "")) >= 3 else weak
        if tok not in strong and tok not in weak:
            bucket.append(tok)
    return strong, weak


def members_of(text: str) -> list[str]:
    out: list[str] = []
    for quoted in BACKTICK.findall(str(text)):
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
    earlier_ids = [r["id"] for r in resolved[:SKIP]]
    headers = headers_by_id()

    ok(len(rows) == 198, f"ledger holds 198 rows ({len(rows)})", str(len(rows)))
    ok(len(resolved) == 145, f"{len(resolved)} rows are resolved under the stated rule "
       "(keep/edit/epe/out/superseded; next and blocked excluded)", str(len(resolved)))
    ok(len(picked) == PICK, f"resolved rows 91..145 selected ({len(picked)})")
    ok(all(r["dispo"] in RESOLVED for r in picked), "every audited row is resolved")
    ok(not ({r["id"] for r in picked} & set(earlier_ids)),
       "no audited id appears among rows 1..90",
       str(sorted({r["id"] for r in picked} & set(earlier_ids))))
    ok(ledger_sha == LEDGER_SHA_FIRST_AUDIT,
       "T_ROWS.jsonl sha256 equals the one the first audit recorded "
       f"({LEDGER_SHA_FIRST_AUDIT[:16]}...)", ledger_sha)
    ok(all(r["id"] in headers for r in picked),
       "every audited row was found under a table header in its own document",
       str([r["id"] for r in picked if r["id"] not in headers]))
    ok(all(len(headers[r["id"]]) == len(r["cells"]) for r in picked),
       "every row's header has the same column count as the row",
       str([(r["id"], len(headers[r["id"]]), len(r["cells"])) for r in picked
            if r["id"] in headers and len(headers[r["id"]]) != len(r["cells"])]))
    prev_ok = all(os.path.isfile(p) for p in PREV_SCRIPTS + PREV_AUDITS)
    ok(prev_ok, "the two earlier scripts and their two audits all exist (read, never written)")
    prev_sha = {os.path.relpath(p, ROOT).replace("\\", "/"): sha_of(p)
                for p in PREV_SCRIPTS + PREV_AUDITS if os.path.isfile(p)}

    index = build_index()
    opened: dict[str, File] = {}
    audit: list[dict] = []
    for row in picked:
        refs = refs_of(row)
        binary = sorted({t for t in REF_ANY.findall(" ".join(str(c) for c in row["cells"])
                                                   + " " + str(row.get("why", "")))
                         if not t.lower().endswith(TEXT_EXT)})
        hdr = headers.get(row["id"], [])
        vi = column_of(hdr, "value")
        mi = column_of(hdr, "member")
        value_text = str(row["cells"][vi]) if vi < len(row["cells"]) else ""
        member_text = str(row["cells"][mi]) if mi < len(row["cells"]) else ""
        quad = bool(COLOUR_Q.search(value_text))
        strong, weak = numbers_of(value_text)
        members = members_of(member_text)
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
                paths.append({"ref": ref, "path": None, "how": "dead", "candidates": 0,
                              "file": None})
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
                              "how": f"AMBIGUOUS: {len(files)} candidates",
                              "candidates": len(files), "file": f})

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

        def status_for(graded_, exact_, rounded_, absent_, members_, member_hits_) -> tuple[str, str]:
            if not refs:
                return ("NO PATH",
                        "the row names no file; its evidence is a decoded value, not a citation")
            if dead:
                return "DEAD PATH", "not found: " + ", ".join(dead)
            if graded_ and not absent_ and not rounded_:
                return "OK", f"all {len(exact_)} quoted number(s) found"
            if graded_ and not absent_:
                return ("OK (rounded)",
                        f"{len(exact_)} exact, {len(rounded_)} by rounding at the quoted "
                        f"precision ({', '.join(rounded_[:4])})")
            if graded_ and (exact_ or rounded_):
                return ("PARTIAL", f"{len(exact_) + len(rounded_)} of {len(graded_)} found; "
                                   "absent: " + ", ".join(absent_[:5]))
            if graded_:
                return ("VALUE-NOT-FOUND",
                        "none of " + ", ".join(list(graded_)[:4]) + " occurs in the named file")
            if members_:
                if member_hits_:
                    return ("OK (member name)",
                            f"no number quoted; member name found: {member_hits_[0]}")
                return ("VALUE-NOT-FOUND", "no number quoted; none of the member names occurs: "
                                           + ", ".join(members_[:3]))
            return ("NOT-TESTABLE", "a file is named but the row quotes nothing searchable")

        status, note = status_for(graded, exact, rounded, absent, members, member_hits)
        if status == "NO PATH" and binary:
            note = ("names no text file this audit can open; it names only non-text artefact(s): "
                    + ", ".join(binary[:3]))
        if ambiguous and status.startswith("OK"):
            status = status[:-1] + ", ambiguous path)" if status.endswith(")") else \
                status + " (ambiguous path)"
            note += (f"; {ambiguous[0]['candidates']} same-name files, content did not single "
                     "one out")

        # the reading audits 1-2 used, on this row only (derived comparison, never a substitute)
        legacy_strong, legacy_weak = numbers_of(str(row["cells"][4])
                                                if len(row["cells"]) > 4 else "")
        legacy_members = members_of(str(row["cells"][2]) if len(row["cells"]) > 2 else "")
        lg = {t: best_grade(t) for t in (legacy_strong or legacy_weak)}
        l_exact = [t for t, (g, _w) in lg.items() if g == EXACT]
        l_rounded = [t for t, (g, _w) in lg.items() if g == ROUNDED]
        l_absent = [t for t, (g, _w) in lg.items() if g == ABSENT]
        l_hits = [t for t in legacy_members if best_grade(t)[0] != ABSENT]
        legacy_status, _ln = status_for(lg, l_exact, l_rounded, l_absent,
                                        legacy_members, l_hits)
        if ambiguous and legacy_status.startswith("OK"):
            legacy_status = legacy_status[:-1] + ", ambiguous path)" \
                if legacy_status.endswith(")") else legacy_status + " (ambiguous path)"

        audit.append({"id": row["id"], "dispo": row["dispo"], "doc": row["doc"],
                      "refs": refs, "binary": binary, "paths": paths,
                      "numbers": list(graded),
                      "exact": exact, "rounded": rounded, "absent": absent,
                      "members": members, "member_hits": member_hits,
                      "status": status, "note": note, "value": value_text[:120],
                      "vcol": vi, "mcol": mi, "headers": hdr, "quad": quad,
                      "legacy_status": legacy_status})

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
    ok(all(a["vcol"] < len(a["headers"]) for a in audit),
       "every value column index lies inside its own table header")
    ok(all(a["quad"] == bool(COLOUR_Q.search(a["value"])) for a in audit),
       "every row's colour-quadruple flag matches its own value cell")

    # ------------------------------------------------------------------ the document
    no_path = [a for a in audit if a["status"] == "NO PATH"]
    dead_rows = [a for a in audit if a["status"] == "DEAD PATH"]
    not_found = [a for a in audit if a["status"] == "VALUE-NOT-FOUND"]
    partial = [a for a in audit if a["status"] == "PARTIAL"]
    cited = [a for a in audit if a["refs"]]
    same_name = [(a, p) for a in audit for p in a["paths"] if p["candidates"] > 1]

    def count(prefix: str) -> int:
        return sum(1 for a in audit if a["status"].startswith(prefix))

    # per-document grouping of NO PATH (this slice), plus the whole resolved ledger as context
    def group(items: list[dict]) -> list[dict]:
        out = []
        for doc in dict.fromkeys([r["doc"] for r in resolved]):
            sub = [a for a in items if a["doc"] == doc]
            if not sub:
                continue
            np_ = [a for a in sub if a["status"] == "NO PATH"]
            b = [a for a in np_ if a.get("binary")]
            n = len(np_)
            out.append({"doc": doc, "rows": len(sub), "no_path": n,
                        "no_path_binary": len(b), "no_path_text": n - len(b),
                        "cited": len(sub) - n,
                        "share": (100.0 * n / len(sub)) if sub else 0.0,
                        "share_text": (100.0 * (n - len(b)) / len(sub)) if sub else 0.0,
                        "ids": [a["id"] for a in np_]})
        return out

    slice_groups = group(audit)
    full = group([{"doc": r["doc"], "id": r["id"],
                   "status": "NO PATH" if not refs_of(r) else "cited"} for r in resolved])
    worst_by_count = max(slice_groups, key=lambda g: (g["no_path"], g["rows"]))
    worst_by_share = max(slice_groups, key=lambda g: (g["share"], g["no_path"]))
    worst_text = max(slice_groups, key=lambda g: (g["no_path_text"], g["rows"]))
    worst_text_share = max(slice_groups, key=lambda g: (g["share_text"], g["no_path_text"]))
    ok(sum(g["rows"] for g in slice_groups) == PICK,
       "the per-document groups cover every audited row")
    ok(sum(g["no_path"] for g in slice_groups) == len(no_path),
       "the per-document NO PATH counts sum to the NO PATH total",
       str(sum(g["no_path"] for g in slice_groups)))
    ok(sum(g["no_path_binary"] + g["no_path_text"] for g in slice_groups) == len(no_path),
       "the artefact/nothing split sums to the NO PATH total")
    ok(all(not a["refs"] for a in no_path),
       "no NO PATH row also resolved a text citation")
    ok(all(a["binary"] for a in no_path if "non-text artefact" in a["note"]),
       "every NO PATH note naming an artefact has one recorded")
    ok(len(full) == 8, f"all 8 documents of the ledger appear in the context table ({len(full)})")

    L: list[str] = []
    ap = L.append
    ap("# T-row evidence audit - resolved rows 91..145")
    ap("")
    ap("Generated by `python Tools/scripts/t_row_evidence3.py --write`; re-derived and compared")
    ap("byte-for-byte by `--check`. Read-only: `Working/Translation/T_ROWS.jsonl` was opened")
    ap(f"(sha256 `{ledger_sha}`, the same one the first audit recorded), never written. The two")
    ap("earlier scripts and their audits were read and hashed, never written:")
    for name, digest in prev_sha.items():
        ap(f"* `{name}` sha256 `{digest}`")
    ap("")
    ap(f"**{len(audit)} rows audited: {count('OK')} fully found ({count('OK (rounded')} by "
       f"rounding, {count('OK (weak')} on a weak token, {count('OK (member')} on a member name), "
       f"{len(partial)} partial, {len(not_found)} with no quoted value in the file, "
       f"{len(dead_rows)} dead path, {len(no_path)} citing no file at all, "
       f"{count('NOT-TESTABLE')} not testable.**")
    ap("")
    ap("Same method and status vocabulary as the first two audits, applied to rows 91..145 of the")
    ap("resolved list (rows 1..90 are in `ROW_EVIDENCE_AUDIT.md` and `ROW_EVIDENCE_AUDIT2.md`).")
    ap("The ledger has no `evidence` field, so a row's evidence is read as *the file it names")
    ap("anywhere in its cells or `why`*. Resolved = disposition `keep`, `edit`, `epe`, `out` or")
    ap("`superseded` (145 of 198 rows); `next` and `blocked` are excluded by that rule.")
    ap("")
    ap("## Where the quoted value is read from")
    ap("")
    ap("The two earlier scripts read the value from `cells[4]`. That is the T-1 / T-2b table")
    ap("shape. In this slice it happens to be right for T-7 (`values`), T-20 (`carrier and")
    ap("value`) and T-14 (the BmAK colour/cone/radius column), and wrong for T-3 and T-13")
    ap("(index 4 is `now`) and T-15 (index 4 is `JC3 carrier`; the value is 3). This audit")
    ap("therefore reads the value from the table header the row sits under in its own document:")
    ap("")
    ap("| doc | document | header | value column read | member column read |")
    ap("|---|---|---|---|---|")
    for doc in dict.fromkeys(a["doc"] for a in audit):
        a = next(x for x in audit if x["doc"] == doc)
        ap(f"| {doc} | `{DOCS[doc]}` | {' | '.join(a['headers'])} | "
           f"{a['vcol']} (`{a['headers'][a['vcol']]}`) | {a['mcol']} "
           f"(`{a['headers'][a['mcol']]}`) |")
    ap("")
    ap("Every row's header has exactly the same column count as the row (an oracle below), so no")
    ap("row in this slice is a split cell. The statuses are otherwise the first script's, with no")
    ap("new vocabulary.")
    ap("")
    ap(f"## Rows with VALUE-NOT-FOUND or NO PATH ({len(not_found) + len(no_path)} of "
       f"{len(audit)})")
    ap("")
    for a in audit:
        if a["status"] in ("VALUE-NOT-FOUND", "NO PATH"):
            ap(f"* `{a['id']}` ({a['doc']}, {a['dispo']}) - **{a['status']}** - {a['note']}")
    ap("")
    ap("## The 55 rows")
    ap("")
    ap("| # | id | doc | dispo | evidence ref(s) | resolved to | quoted numbers | status | note |")
    ap("|---:|---|---|---|---|---|---|---|---|")
    for i, a in enumerate(audit, start=91):
        refs = ", ".join(f"`{r}`" for r in a["refs"]) or "-"
        dest = ", ".join(f"`{p['path']}`" for p in a["paths"] if p["path"]) or "-"
        toks = ", ".join(a["numbers"][:3]) or ", ".join(a["members"][:2]) or "-"
        ap(f"| {i} | `{a['id']}` | {a['doc']} | {a['dispo']} | {refs} | {dest} | {toks} | "
           f"{a['status']} | {a['note']} |")
    ap("")
    ap("## Rows citing no file (NO PATH)")
    ap("")
    only_binary = [a for a in no_path if a["binary"]]
    nothing = [a for a in no_path if not a["binary"]]
    ap(f"{len(no_path)} of the {len(audit)} rows are NO PATH under the first script's reading: the")
    ap("row names no `.md/.json/.jsonl/.py/.csv/.txt` file, so nothing can be opened and no quoted")
    ap("number can be re-tested from the ledger alone. Two different things sit behind that label:")
    ap("")
    ap(f"**{len(only_binary)} name a non-text artefact only** (an `.effc`, `.ee`, `.bank`, `.bin`")
    ap("this text resolver cannot read). They do cite something; the citation is just not text:")
    ap("")
    for a in only_binary:
        ap(f"* `{a['id']}` ({a['doc']}, {a['dispo']}) - "
           f"{', '.join(f'`{b}`' for b in a['binary'][:3])}")
    if not only_binary:
        ap("None.")
    ap("")
    ap(f"**{len(nothing)} name nothing at all** - no text file, no binary artefact:")
    ap("")
    for a in nothing:
        ap(f"* `{a['id']}` ({a['doc']}, {a['dispo']}) - {a['value'].replace('|', '/')}")
    if not nothing:
        ap("None.")
    ap("")
    ap("## NO PATH grouped by document")
    ap("")
    ap("Counted over this slice's 55 audited rows, grouped by the document the ledger assigns the")
    ap("row to (`doc`), not by the document a row mentions:")
    ap("")
    ap("| doc | rows audited | NO PATH | only a non-text artefact | names nothing | "
       "names nothing, share | NO PATH ids |")
    ap("|---|---:|---:|---:|---:|---:|---|")
    for g in slice_groups:
        ids = ", ".join(f"`{i}`" for i in g["ids"]) or "-"
        ap(f"| {g['doc']} | {g['rows']} | {g['no_path']} | {g['no_path_binary']} | "
           f"{g['no_path_text']} | {g['share_text']:.0f}% | {ids} |")
    ap("")
    if no_path:
        ap(f"**By the letter of the rule - NO PATH, text or binary - the answer is "
           f"`{worst_by_count['doc']}`**, with {worst_by_count['no_path']} of its "
           f"{worst_by_count['rows']} audited rows ({worst_by_count['share']:.0f}%).")
        ap("")
        ap("But that reading overstates it, because "
           f"{worst_by_count['no_path_binary']} of those name an `.effc` the resolver cannot")
        ap("open. Counting only rows that name **nothing at all**, the documents lack a cited")
        ap(f"source in this order - **most often `{worst_text['doc']}`**, "
           f"{worst_text['no_path_text']} of {worst_text['rows']} "
           f"({worst_text['share_text']:.0f}%):")
        ap("")
        for g in sorted(slice_groups, key=lambda g: (-g["no_path_text"], g["doc"])):
            ap(f"* `{g['doc']}`: {g['no_path_text']} of {g['rows']} name nothing "
               f"({g['share_text']:.0f}%); {g['no_path_binary']} more name only an artefact")
        ap("")
        if worst_text_share["doc"] != worst_text["doc"]:
            ap(f"By share of its own audited rows the worst is `{worst_text_share['doc']}` "
               f"({worst_text_share['share_text']:.0f}%).")
        else:
            ap(f"The same document is also the worst by share "
               f"({worst_text_share['share_text']:.0f}% of its audited rows).")
        tied = [g["doc"] for g in slice_groups if g["no_path"] == worst_by_count["no_path"]]
        if len(tied) > 1:
            ap("The NO PATH count is tied: " + ", ".join(f"`{d}`" for d in tied) + ".")
    else:
        ap("No row in this slice cites nothing, so the grouping is empty.")
    ap("")
    ap("Read this with the slice's composition in mind: this is the tail of the resolved list, so")
    ap("it is dominated by the later documents (T-14, T-13, T-20, T-15, T-7), and a document with")
    ap("few rows here can still be the worst across the whole ledger. For context only - not this")
    ap("audit's finding, and derived by the same `refs_of` reading - the same count over all 145")
    ap("resolved rows is:")
    ap("")
    ap("| doc | resolved rows | NO PATH | share |")
    ap("|---|---:|---:|---:|")
    for g in full:
        ap(f"| {g['doc']} | {g['rows']} | {g['no_path']} | {g['share']:.0f}% |")
    worst_full = max(full, key=lambda g: (g["no_path"], g["rows"]))
    ap("")
    ap(f"Across the whole resolved ledger the largest absolute count is `{worst_full['doc']}` "
       f"({worst_full['no_path']} of {worst_full['rows']}); the largest share is "
       f"`{max(full, key=lambda g: (g['share'], g['no_path']))['doc']}`.")
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
    quads = [a for a in audit if a["quad"]]
    ap("## Quoted colour quadruples (not a value test)")
    ap("")
    ap("`norm()` strips thousands separators, so a BmAK colour written `255,255,255,0` becomes")
    ap("the single token `2552552550`, which no file contains. The statuses of the rows below")
    ap(f"are therefore not evidence about their colour: {len(quads)} rows quote a quadruple.")
    ap("")
    for a in quads:
        ap(f"* `{a['id']}` ({a['doc']}) - {a['status']} - value `{a['value'][:80]}`")
    if not quads:
        ap("None.")
    ap("")
    ap("Any VALUE-NOT-FOUND or PARTIAL above that names a long comma-free token is this artefact,")
    ap("not an absent colour. A colour test needs the components compared separately, which this")
    ap("audit does not do.")
    ap("")
    legacy_diff = [a for a in audit if a["legacy_status"] != a["status"]]
    ap("## Where the earlier scripts' fixed columns would have differed (derived)")
    ap("")
    ap(f"On these {len(audit)} rows, reading as the first two audits did - `cells[4]` for the")
    ap(f"value, `cells[2]` for member names - would change {len(legacy_diff)} status(es). The")
    ap("difference can come from either column, so each line names both the result and the column:")
    ap("")
    if legacy_diff:
        for a in legacy_diff:
            ap(f"* `{a['id']}` ({a['doc']}): `cells[4]` -> {a['legacy_status']}, "
               f"header column {a['vcol']} -> {a['status']}")
    else:
        ap("None: for this slice the two readings agree.")
    ap("")
    ap("This is a fact about the reading, not a defect in any row, and it does not change the")
    ap("earlier audits' verdicts on rows 1..90 - those are their own slice and were not re-run.")
    ap("")
    ap("## Dead paths")
    ap("")
    if dead_rows:
        for a in dead_rows:
            ap(f"* `{a['id']}` - {a['note']}")
    else:
        ap(f"None. Every path named by the {len(cited)} rows that cite a file exists on disk:")
        ap("directly, by a unique basename, or by content among same-name files.")
        ap("One citation needed the suffix order fixed first: `T-MD4` cites `objects.jsonl`, which")
        ap("`Research/BatmobileGrab/objects.jsonl` satisfies. The first two scripts' pattern lists")
        ap("`json` before `jsonl`, so it would have truncated that to `objects.json` and reported a")
        ap("dead path; this slice has no dead path once the longer suffix is matched first.")
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
    ap("* **Rows 1..90 of the resolved set** - audited by the two earlier scripts; not re-run here.")
    ap("* **Whether the cited decode is still what the build ships** - that is `t_rows.py check`")
    ap("  and the per-card `--check` scripts' business.")
    ap("* **Why a document has no cited source.** The grouping counts the ledger's own claim of")
    ap("  evidence; it does not say whether a citation was omitted or the row is uncitable.")
    ap("")
    ap("## Oracles re-run by `--check`")
    ap("")
    for c in checks:
        ap(f"* {'PASS' if c['ok'] else 'FAIL'} {c['oracle']}")
    ap("")
    ap("## Labels")
    ap("")
    ap("Decoded: the ledger rows, the cited files' contents, the table headers and the resolved")
    ap("paths, the sha256 of the read-only inputs. Derived: the statuses and counts, the column")
    ap("mapping, the rounding comparison, the content-disambiguation scores, the per-document")
    ap("grouping and the `cells[4]` comparison. UNKNOWN: a differing value behind a named field, a")
    ap("row with no file, anything behind a citation that is still ambiguous, and why any given")
    ap("document lacks a citation.")
    ap("")
    text = "\n".join(L)

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    print("statuses: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    print("no-path by doc: " + ", ".join(f"{g['doc']} {g['no_path']}/{g['rows']}"
                                         for g in slice_groups))
    print(f"worst by count {worst_by_count['doc']} ({worst_by_count['no_path']}), "
          f"worst by share {worst_by_share['doc']} ({worst_by_share['share']:.0f}%)")
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
    print("PASS document: ROW_EVIDENCE_AUDIT3.md matches the regenerated text")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write ROW_EVIDENCE_AUDIT3.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
