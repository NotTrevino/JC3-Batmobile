"""ledger_audit.py - reconcile T_ROWS.jsonl against the built bm-RC1 aaf (GRB-G3-11).

The translation ledger (`Working/Translation/T_ROWS.jsonl`, 198 rows) is the claim.
This script checks every claim against the bytes that were actually built
(`Builds/bm-RC1/aaf`, 691 files, receipt.json = the build's own step/file list)
and gives each row exactly one verdict:

  TRANSLATED     the row's value (or its carried asset path) is present in a built
                 file, at a member the row names - evidence is file + member + value
  GUESSED        same presence, but the row's own provenance is chosen / assumed /
                 tuned / by hand / unsourced / probe (the value exists but was not
                 decoded or derived from a BmAK source)
  NOT TRANSLATED everything else, with the reason that applies

Evidence tiers, strongest first (`tier` in the JSON):

  value   a built ADF member (module / parts / tune) whose path matches a member the
          row names, holding a number (rtol 1e-4) or string the row states
  member  such a member exists but holds a different value
  string  a token the row names (an asset path, a part name, a socket) appears
          literally in a built file, reported with its byte offset
  none    nothing found; `note` says what the row's claim would need

Constant cells of a row are `[id, BmAK source, JC3 target, transform, now, proposed,
confidence, verify]` (section 7 of GRAB_BACKLOG.md), but the JSONL was written by
splitting markdown table rows on commas, so prose with a comma shifts every later
cell. The audit therefore reads the row as one text blob and matches members,
numbers and tokens by content, never by cell index - indexing would read a comma
in a sentence as a value.

Matching rules (stated so a reader can re-run them):

  member match  both sides are split on '.' after removing `[...]` and '/'. A match is
                either a *contiguous* slice of the other, or a suffix of one equal to a
                prefix of the other (the second case is what lets a container hint like
                `land_global.base_wheel_hardpoint_positions` reach the leaf
                `base_wheel_hardpoint_positions[0].y`). So `land_global.front/rear_wheels.radius`
                matches `front_wheels.radius` and `parts[0].parent_part_index` matches
                `parent_part_index`. Container members decode to '' and are ignored; only
                leaves carry a value.
  value match   a number in the row equals the built number with
                |b - v| <= max(1e-9, 1e-4 * |v|); tokens with one digit are ignored
                ("1" matches too much), strings compare exactly.
  string match  the token is >= 8 chars and contains '/' or '_', searched as ASCII
                bytes in the built file - never in an ADF file, whose name table lists
                every declared member whether a value was built or not.

Text normalisation: U+2212 becomes '-', en/em dashes, '+-', 'x' and NBSP become spaces,
so "−0.3" reads as -0.3 and "3–8 t" does not read as -8.

Read-only: T_ROWS.jsonl is opened for reading, the build is never touched. Outputs
are the two files under Working/Translation/.

Usage:
  python Tools/scripts/ledger_audit.py --write   # write LEDGER_AUDIT.md + .json
  python Tools/scripts/ledger_audit.py --check   # verify the outputs, exit 1 on fail
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_parts  # noqa: E402
import jc3adf  # noqa: E402
import rtpcdump  # noqa: E402

LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
BUILD = os.path.join(ROOT, "Builds", "bm-RC1")
AAF = os.path.join(BUILD, "aaf")
RECEIPT = os.path.join(BUILD, "receipt.json")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_AUDIT.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_AUDIT.json")

# Provenance words that make a found value GUESSED rather than TRANSLATED.
GUESS_MARKERS = ("by hand", "hand-set", "hand set", "chosen", "assum", "unsourced",
                 "estimate", "approx", "guess", "tuned", "not law", "probe",
                 "picked", "eyeball", "trial")
# A row that declares itself out / superseded was not meant to be built.
NOT_BUILT = ("next", "blocked")

ADF_EXT = (".vmodc", ".etunec", ".ctunec", ".ftunec", ".wtunec")
HINT_RE = re.compile(r"`([^`]+)`")
NUM_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
# The ledger is hand-written markdown: it uses U+2212 for negatives, en/em dashes for
# ranges, +- and x for dimensions. Normalise before reading numbers, or "−0.3" is
# invisible to the matcher while "3–8" would read as -8.
CHAR_MAP = {"\u2212": "-", "\u2013": " ", "\u2014": " ", "\u00b1": " ",
            "\u00d7": " ", "\u00a0": " ", "\uff0b": "+"}


def clean_text(s: str) -> str:
    for src, dst in CHAR_MAP.items():
        s = s.replace(src, dst)
    return s

VERDICTS = ("TRANSLATED", "GUESSED", "NOT TRANSLATED")


# ------------------------------------------------------------------ basics
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows() -> list[dict]:
    with open(LEDGER, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def row_text(r: dict) -> str:
    parts = [str(c) for c in r.get("cells", [])]
    parts.append(str(r.get("why", "")))
    return clean_text(" | ".join(parts))


def norm_segs(s: str) -> list[str]:
    """`parts[0].parent_part_index` -> [parts, parent_part_index]; '/' -> '.'."""
    s = re.sub(r"\[[^\]]*\]", "", s)
    s = s.replace("/", ".").replace("*", "")
    return [x for x in s.lower().split(".") if x]


def contiguous(small: list[str], big: list[str]) -> bool:
    if not small or len(small) > len(big):
        return False
    for i in range(len(big) - len(small) + 1):
        if big[i:i + len(small)] == small:
            return True
    return False


def path_matches(hint: list[str], built: list[str]) -> bool:
    if contiguous(hint, built) or contiguous(built, hint):
        return True
    for k in range(1, len(hint)):                        # hint carries a scope prefix
        if hint[k:] == built[:len(hint) - k]:
            return True
    for k in range(1, len(built)):                       # built carries one
        if built[k:] == hint[:len(built) - k]:
            return True
    return False


def hints_of(text: str) -> list[list[str]]:
    out: list[list[str]] = []
    for span in HINT_RE.findall(text):
        s = span.strip().strip("*").strip()
        if not s or " " in s or "." not in s:
            continue
        if s.endswith((".effc", ".lod", ".ddsc", ".rbm", ".vmodc", ".epe", ".bank")):
            continue                                     # asset path, not a member
        if not re.fullmatch(r"[A-Za-z_][\w.\-\[\]/*]*", s):
            continue
        segs = norm_segs(s)
        if len(segs) < 2:
            continue
        if segs not in out:
            out.append(segs)
    return out


def tokens_of(text: str) -> list[str]:
    out: list[str] = []
    for span in HINT_RE.findall(text):
        s = span.strip().strip("*").strip()
        if len(s) < 8 or " " in s:
            continue
        if "/" not in s and "_" not in s:
            continue
        if s not in out:
            out.append(s)
    return out


def nums_of(text: str) -> list[tuple[str, float, bool]]:
    """(literal, value, strong) for every number in the row.

    `strong` is False for a single-digit integer ("0".."9"): those match so many built
    values that they are only trusted when the row's hint selects exactly one built
    member, where the member match is already specific.
    """
    out: list[tuple[str, float, bool]] = []
    seen: set[str] = set()
    for m in NUM_RE.findall(text):
        if m in seen:
            continue
        seen.add(m)
        digits = re.sub(r"[-.]", "", m).lstrip("0")
        dec = len(m.split(".")[1]) if "." in m else 0
        try:
            out.append((m, float(m), len(digits) >= 2 or dec >= 1))
        except ValueError:
            pass
    return out


# ------------------------------------------------------------- built evidence
def built_adf_rows() -> tuple[list[tuple[str, list[str], str, object]], list[str], list[str]]:
    """(relfile, segments, type, value) for every ADF file in the build.

    `*_ai.vmodc` siblings are excluded from the evidence: they are the AI driver's copy of
    a module, so a row about the vehicle's own tuning that matched only there would be
    citing the wrong file. They are listed separately so the exclusion is visible.
    """
    rows: list[tuple[str, list[str], str, object]] = []
    files: list[str] = []
    excluded: list[str] = []
    for dirpath, _dirs, names in os.walk(AAF):
        for name in sorted(names):
            if not name.endswith(ADF_EXT):
                continue
            if name.endswith("_ai.vmodc"):
                excluded.append(os.path.relpath(os.path.join(dirpath, name), AAF)
                                .replace("\\", "/"))
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, AAF).replace("\\", "/")
            files.append(rel)
            try:
                adf = jc3adf.Adf(open(path, "rb").read())
                walked = list(jc3adf.walk(adf))
            except Exception as exc:                      # noqa: BLE001
                files[-1] = f"{rel} (DECODE FAILED: {exc})"
                continue
            for member, typ, value in walked:
                rows.append((rel, norm_segs(member), typ, value))
    return rows, files, sorted(excluded)


def built_parts_rows() -> tuple[list[tuple[str, list[str], str, object]], str]:
    """The parts module decoded with bm_parts.decode_parts: parts[i].<field>."""
    rel = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
           "batmobile/sportsmuscle_vehicle_parts.vmodc")
    path = os.path.join(AAF, rel.replace("/", os.sep))
    if not os.path.exists(path):
        return [], ""
    parts = bm_parts.decode_parts(open(path, "rb").read())
    rows: list[tuple[str, list[str], str, object]] = []
    for i, part in enumerate(parts):
        for key, value in part.items():
            typ = "string" if isinstance(value, str) else "float" if isinstance(value, float) else "int"
            rows.append((rel, norm_segs(f"parts[i].{key}"), typ, value))
    return rows, f"{len(parts)} parts"


def built_epe_note() -> str:
    rel = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
           "v0300_car_kensington_sportsmuscle_debug.epe")
    path = os.path.join(AAF, rel.replace("/", os.sep))
    if not os.path.exists(path):
        return "absent"
    nodes = rtpcdump.parse_rtpc(open(path, "rb").read())
    props = sum(len(n.props) for n in nodes)
    return f"{len(nodes)} RTPC nodes / {props} properties (name hashes unresolved)"


# Files whose whole job is to list names, so any token is found in them by construction
# and a hit says nothing about the row. Not searched.
NAME_TABLES = ("@files.xml",)
NAME_SUFFIXES = (".stringlookup", ".fmod_guids")


def string_index() -> dict[str, bytes]:
    """Every built non-ADF file small enough to scan, keyed by relpath.

    ADF files are excluded on purpose: their header carries the *name table* of every
    declared member, so any member name a row mentions is present in the file whether
    or not a value was built. Those rows are covered by the member/value tiers instead.
    """
    out: dict[str, bytes] = {}
    for dirpath, _dirs, names in os.walk(AAF):
        for name in names:
            if name in NAME_TABLES or name.endswith(NAME_SUFFIXES) or name.endswith(ADF_EXT):
                continue
            path = os.path.join(dirpath, name)
            if os.path.getsize(path) > 16 << 20:
                continue
            out[os.path.relpath(path, AAF).replace("\\", "/")] = open(path, "rb").read()
    return out


# ---------------------------------------------------------------- classify
def classify(row: dict, adf_rows, parts_rows, blobs, receipt_steps) -> dict:
    text = row_text(row)
    hints = hints_of(text)
    tokens = tokens_of(text)
    numbers = nums_of(text)
    dispo = row.get("dispo", "")
    markers = [m for m in GUESS_MARKERS if m in text.lower()]

    matches: list[tuple[str, str, object]] = []
    for rel, segs, typ, value in adf_rows + parts_rows:
        if value is None or (isinstance(value, str) and not value):
            continue                                     # container / empty leaf: no value
        if not any(path_matches(h, segs) for h in hints):
            continue
        matches.append((rel, ".".join(segs), value))

    # A single matched member makes even a 1-digit row number trustworthy.
    one_member = len({(rel, path) for rel, path, _v in matches}) == 1
    value_hits: list[str] = []
    member_hits: list[str] = []
    string_hits: list[str] = []

    for rel, path, value in matches:
        member_hits.append(f"{rel}:{path} = {value!r}")
        if isinstance(value, (int, float)):
            for literal, num, strong in numbers:
                if not strong and not one_member:
                    continue
                if abs(float(value) - num) <= max(1e-9, 1e-4 * abs(num)):
                    value_hits.append(f"{rel}:{path} = {value!r} (row says {literal})")
                    break
        elif isinstance(value, str):
            if value in text:
                value_hits.append(f"{rel}:{path} = {value!r} (row text)")

    token_list = list(tokens)
    for hid in hints:                                    # dotted member names also count
        token_list.append(".".join(hid))
    for token in token_list:
        if len(token) < 8:
            continue
        needle = token.encode("ascii", "replace")
        for rel, blob in blobs.items():
            off = blob.find(needle)
            if off >= 0:
                string_hits.append(f"{rel}@0x{off:X}: '{token}'")
                break
    # prefer an asset path over a bare name: a path in the build is carried data,
    # a name can be a label any of several rows share.
    string_hits.sort(key=lambda s: 0 if "/" in s.split(": '")[-1] else 1)

    receipt_mentions = [s for s in receipt_steps if row.get("id") in s]

    if value_hits and markers:
        verdict, tier = "GUESSED", "value"
        evidence = value_hits[0]
    elif value_hits:
        verdict, tier = "TRANSLATED", "value"
        evidence = value_hits[0]
    elif string_hits and markers:
        verdict, tier = "GUESSED", "string"
        evidence = string_hits[0]
    elif string_hits:
        verdict, tier = "TRANSLATED", "string"
        evidence = string_hits[0]
    elif dispo in ("out", "superseded"):
        verdict, tier = "NOT TRANSLATED", "none"
        evidence = f"ledger dispo={dispo} (declared not built): {row.get('why', '')[:120]}"
    elif member_hits:
        verdict, tier = "NOT TRANSLATED", "member"
        evidence = (f"member present, no row number matches: {member_hits[0]}"
                    + (f" (+{len(member_hits) - 1} more member(s))" if len(member_hits) > 1 else ""))
    elif dispo in NOT_BUILT:
        verdict, tier = "NOT TRANSLATED", "none"
        evidence = (f"ledger dispo={dispo} (not built); no member among {len(hints)} row "
                    f"member(s) and no carried token in the aaf")
    else:
        verdict, tier = "NOT TRANSLATED", "none"
        evidence = (f"no member/value/token match in the aaf "
                    f"(dispo={dispo}, {len(hints)} member hint(s))")

    notes = []
    if dispo in NOT_BUILT and verdict == "TRANSLATED":
        notes.append("built ahead of the ledger (dispo says not built)")
    if dispo in ("keep", "edit", "epe") and verdict == "NOT TRANSLATED":
        if not hints and not tokens:
            notes.append("prose claim: no member and no token to check")
        else:
            notes.append("ledger claims built but no evidence found")
    if markers:
        notes.append("provenance markers: " + ", ".join(sorted(set(markers))))
    if receipt_mentions:
        notes.append("receipt step mentions " + row.get("id", ""))
    if not hints:
        notes.append("row names no dotted member (prose target)")

    return {
        "id": row.get("id"),
        "doc": row.get("doc"),
        "section": row.get("section"),
        "dispo": dispo,
        "edits": row.get("edits"),
        "verdict": verdict,
        "tier": tier,
        "evidence": evidence,
        "hints": [".".join(h) for h in hints],
        "value_hits": value_hits[:4],
        "member_hits": [m for m in member_hits if m not in value_hits][:4],
        "string_hits": string_hits[:4],
        "provenance_markers": sorted(set(markers)),
        "receipt_mentions": receipt_mentions,
        "notes": notes,
    }


# ------------------------------------------------------------------ report
def build(rows: list[dict]) -> dict:
    adf_rows, adf_files, adf_excluded = built_adf_rows()
    parts_rows, parts_note = built_parts_rows()
    blobs = string_index()
    receipt = json.load(open(RECEIPT, encoding="utf-8"))
    steps = [str(s) for s in receipt.get("steps", [])]

    audited = [classify(r, adf_rows, parts_rows, blobs, steps) for r in rows]

    counts: dict[str, int] = {v: 0 for v in VERDICTS}
    by_doc: dict[str, dict[str, int]] = {}
    tiers: dict[str, int] = {}
    for a in audited:
        counts[a["verdict"]] += 1
        by_doc.setdefault(a["doc"], {v: 0 for v in VERDICTS})[a["verdict"]] += 1
        tiers[a["tier"]] = tiers.get(a["tier"], 0) + 1

    return {
        "generated_by": "Tools/scripts/ledger_audit.py (--write)",
        "card": "GRB-G3-11 ledger reconciliation",
        "inputs": {
            "ledger": {"path": "Working/Translation/T_ROWS.jsonl", "rows": len(rows),
                       "sha256": sha256_file(LEDGER)},
            "build": {"path": "Builds/bm-RC1", "receipt_sha256": sha256_file(RECEIPT),
                      "aaf_files": len(blobs), "adf_files": len(adf_files),
                      "adf_rows": len(adf_rows), "adf_ai_excluded": adf_excluded,
                      "parts": parts_note,
                      "epe": built_epe_note(),
                      "receipt_steps": len(steps)},
        },
        "rules": {
            "member_match": "segments (split on '.' after removing [...] and '/') overlap as a "
                            "contiguous slice, either direction",
            "value_match": "|built - row| <= max(1e-9, 1e-4*|row|); 1-digit tokens ignored; "
                           "strings exact",
            "string_match": "token >= 8 chars with '/' or '_' found as ASCII bytes",
            "guessed": "value or string found AND the row carries one of "
                       + ", ".join(GUESS_MARKERS),
            "not_translated": "no evidence; dispo out/superseded = declared, next/blocked = "
                              "not built, otherwise no match",
        },
        "counts": {"rows": len(audited), "verdicts": counts, "tiers": tiers,
                   "by_doc": by_doc},
        "rows": audited,
    }


def render_md(doc: dict) -> str:
    inp = doc["inputs"]
    c = doc["counts"]
    out: list[str] = []
    out.append("# Ledger reconciliation - T_ROWS.jsonl vs the built bm-RC1 aaf")
    out.append("")
    out.append("GRB-G3-11. Generated by `Tools/scripts/ledger_audit.py --write`; "
               "`--check` re-derives this from the same inputs and fails on any drift.")
    out.append("")
    out.append("## Inputs")
    out.append("")
    out.append(f"- ledger `{inp['ledger']['path']}` - {inp['ledger']['rows']} rows, "
               f"sha256 `{inp['ledger']['sha256'][:16]}...`")
    out.append(f"- build `{inp['build']['path']}` - receipt sha256 "
               f"`{inp['build']['receipt_sha256'][:16]}...`, {inp['build']['receipt_steps']} steps")
    out.append(f"- aaf {inp['build']['aaf_files']} non-ADF files scanned for carried strings; "
               f"{inp['build']['adf_files']} ADF files decoded with `jc3adf` = "
               f"{inp['build']['adf_rows']} member rows")
    if inp['build'].get('adf_ai_excluded'):
        out.append(f"- excluded from member evidence: {len(inp['build']['adf_ai_excluded'])} "
                   f"`*_ai.vmodc` AI-driver module(s)")
    out.append(f"- parts module decoded with `bm_parts.decode_parts` = {inp['build']['parts']}")
    out.append(f"- `.epe` via `rtpcdump` = {inp['build']['epe']}")
    out.append("")
    out.append("## Verdicts")
    out.append("")
    out.append("| verdict | rows |")
    out.append("|---|---|")
    for v in VERDICTS:
        out.append(f"| {v} | {c['verdicts'][v]} |")
    out.append(f"| **total** | **{c['rows']}** |")
    out.append("")
    out.append("Tiers: " + ", ".join(f"{k} {v}" for k, v in sorted(c["tiers"].items()))
               + " (`value` = member + value, `string` = carried token, "
                 "`member` = member without the value, `none` = no evidence).")
    out.append("")
    out.append("| doc | TRANSLATED | GUESSED | NOT TRANSLATED |")
    out.append("|---|---|---|---|")
    for docname in sorted(c["by_doc"]):
        d = c["by_doc"][docname]
        out.append(f"| {docname} | {d['TRANSLATED']} | {d['GUESSED']} | {d['NOT TRANSLATED']} |")
    out.append("")
    out.append("## Method")
    out.append("")
    for key, text in doc["rules"].items():
        out.append(f"- **{key}**: {text}")
    out.append("")
    out.append("A row's cells are `[id, BmAK source, JC3 target, transform, now, proposed, "
               "confidence, verify]` (GRAB_BACKLOG.md section 7), but the JSONL was written by "
               "splitting markdown rows on commas, so a comma inside a sentence shifts every "
               "later cell. The audit reads the row as text and matches by content, never by "
               "cell index.")
    out.append("")
    out.append("## Rows")
    out.append("")
    out.append("| id | doc | dispo | verdict | tier | evidence |")
    out.append("|---|---|---|---|---|---|")
    for a in doc["rows"]:
        ev = str(a["evidence"]).replace("|", "\\|")
        out.append(f"| {a['id']} | {a['doc']} | {a['dispo']} | {a['verdict']} | "
                   f"{a['tier']} | {ev} |")
    out.append("")
    def noted(row: dict, prefix: str) -> bool:
        return any(str(n).startswith(prefix) for n in row["notes"])

    ahead = [a for a in doc["rows"] if noted(a, "built ahead of the ledger")]
    missing = [a for a in doc["rows"] if noted(a, "ledger claims built but no evidence found")]
    prose = [a for a in doc["rows"] if noted(a, "prose claim")]
    guessed = [a for a in doc["rows"] if a["verdict"] == "GUESSED"]
    out.append("## Findings")
    out.append("")
    out.append(f"### Built ahead of the ledger ({len(ahead)})")
    out.append("")
    for a in ahead:
        out.append(f"- `{a['id']}` (dispo {a['dispo']}) - {a['evidence']}")
    if not ahead:
        out.append("- none")
    out.append("")
    out.append(f"### Ledger claims built, no evidence found ({len(missing)})")
    out.append("")
    for a in missing:
        out.append(f"- `{a['id']}` ({a['doc']}) - {a['evidence']}")
    if not missing:
        out.append("- none")
    out.append("")
    out.append(f"### Prose claims, nothing machine-checkable ({len(prose)})")
    out.append("")
    for a in prose:
        out.append(f"- `{a['id']}` ({a['doc']}, dispo {a['dispo']}) - {a['evidence']}")
    if not prose:
        out.append("- none")
    out.append("")
    out.append(f"### GUESSED - value present, provenance chosen ({len(guessed)})")
    out.append("")
    for a in guessed:
        out.append(f"- `{a['id']}` - {a['evidence']} - markers: "
                   f"{', '.join(a['provenance_markers'])}")
    if not guessed:
        out.append("- none")
    out.append("")
    return "\n".join(out)


def write() -> int:
    rows = load_rows()
    doc = build(rows)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    print("verdicts:", doc["counts"]["verdicts"])
    print("tiers:", doc["counts"]["tiers"])
    return 0


def check() -> int:
    fails: list[str] = []
    if not os.path.exists(OUT_JSON) or not os.path.exists(OUT_MD):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    rows = load_rows()
    fresh = build(rows)

    if len(stored["rows"]) != len(rows):
        fails.append(f"stored rows {len(stored['rows'])} != ledger rows {len(rows)}")
    ids = [a["id"] for a in stored["rows"]]
    if len(set(ids)) != len(ids):
        fails.append("duplicate ids in the audit")
    if len(stored["rows"]) != 198:
        fails.append(f"expected 198 rows, got {len(stored['rows'])}")

    for a in stored["rows"]:
        if a["verdict"] not in VERDICTS:
            fails.append(f"{a['id']}: bad verdict {a['verdict']!r}")
        if not str(a.get("evidence", "")).strip():
            fails.append(f"{a['id']}: empty evidence")

    recount: dict[str, int] = {v: 0 for v in VERDICTS}
    for a in stored["rows"]:
        recount[a["verdict"]] += 1
    if recount != stored["counts"]["verdicts"]:
        fails.append(f"counts header {stored['counts']['verdicts']} != recounted {recount}")

    stored_by_id = {a["id"]: a for a in stored["rows"]}
    fresh_by_id = {a["id"]: a for a in fresh["rows"]}
    if set(stored_by_id) != set(fresh_by_id):
        fails.append("row ids differ between the stored audit and the live ledger")
    drift = [i for i in stored_by_id
             if i in fresh_by_id and stored_by_id[i]["verdict"] != fresh_by_id[i]["verdict"]]
    if drift:
        fails.append("stale verdicts (inputs changed?): " + ", ".join(sorted(drift)[:10]))

    md = open(OUT_MD, encoding="utf-8").read()
    for a in stored["rows"]:
        line = f"| {a['id']} | {a['doc']} | {a['dispo']} | {a['verdict']} | {a['tier']} |"
        if line not in md:
            fails.append(f"{a['id']}: row line missing from the markdown")
            break
    if md.count("\n| ") < 198:
        fails.append("markdown has fewer table rows than the ledger")

    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {len(stored['rows'])}/{len(rows)} rows classified")
    print("verdicts:", stored["counts"]["verdicts"])
    print("tiers:", stored["counts"]["tiers"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
