"""ledger_provenance.py - add the provenance dimension to the G3-11 ledger audit.

`Working/Translation/LEDGER_AUDIT.md` (GRB-G3-11) gives every row of
`Working/Translation/T_ROWS.jsonl` a verdict from the bytes in `Builds/bm-RC1/aaf`.
Review-G3-11 found that 35 of the 85 TRANSLATED verdicts rest on a file this build
never edited: the value is present in a *built* file, but that file is an inherited
copy (`owner_card` = `base (bm-005 lineage)` / an earlier build) or, for T-DM1, a
file the build's own B-18 step reverted to vanilla bytes.

This script adds the missing dimension. For every TRANSLATED row it records:

  file        the file the row's evidence came from (parsed from LEDGER_AUDIT's
              evidence string, so it is the same file the old verdict rested on)
  aaf entry   the `receipt.aaf.list[]` entry for that file - path, sha256
  owner_card  the receipt's per-file provenance string, verbatim
  verdict     edited by this build / inherited / vanilla

Definitions (stated so a reader can re-run them):

  vanilla      the file is one the receipt's `b18` block lists in
               `reverted_to_vanilla`, or its owner_card contains `(vanilla bytes)`.
               The built bytes are the game's, not a translation.
  edited       the file's bytes differ from *every* earlier build's copy of the same
               file, or its owner_card names a card that this build's own steps
               record as writing bytes. Both are facts about the file, not about the
               row's value: an edited file can still carry a donor value.
  inherited    neither of the above: the bytes are identical to an earlier build's
               copy, or the owner_card names only that lineage. "Inherited" means
               "not edited by bm-RC1"; whether a *different* earlier build set the
               value is not claimed.

Byte comparison: the same aaf-relative path is looked for in each earlier build on
disk (`bm-013b` down to `bm-001`), first as-is and then with `/batmobile/` removed -
B-18 moved 51 files into that directory and the move itself does not change the
bytes (checked: `00_shared/modules/vehicle_common.vmodc` is byte-identical across
bm-RC1, bm-013b and bm-005). A file present in no earlier build is reported as
`no earlier copy`, and the verdict then rests on `owner_card` alone.

Which cards count as writers is derived, not hard-coded: the card ids are read from
`receipt.steps`, and a card is excluded when its own step says it wrote nothing -
B-18 (move + vanilla revert), B-04L (`ported: False`), B-17 (`SKIPPED`).

Read-only: T_ROWS.jsonl, the receipt and both audit files are opened for reading and
never written. The only output is LEDGER_PROVENANCE.md.

Usage:
  python Tools/scripts/ledger_provenance.py --write   # write LEDGER_PROVENANCE.md
  python Tools/scripts/ledger_provenance.py --check   # re-derive and compare, exit 1 on drift
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

import ledger_audit as la  # noqa: E402

LEDGER = la.LEDGER
BUILD = la.BUILD
AAF = la.AAF
RECEIPT = la.RECEIPT
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_PROVENANCE.md")

# Earlier builds on disk, newest first. bm-013b is the immediate predecessor.
PRIOR = ("bm-013b", "bm-009", "bm-008", "bm-007", "bm-006", "bm-005",
         "bm-004", "bm-002", "bm-001")

VANILLA_MARK = "(vanilla bytes)"
PROV = ("edited by this build", "inherited", "vanilla")
RECOMMEND = {"edited by this build": "TRANSLATED (unchanged)",
             "inherited": "CARRIED (value is the earlier build's)",
             "vanilla": "NOT TRANSLATED (vanilla bytes)"}


# ------------------------------------------------------------------ basics
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_receipt() -> dict:
    with open(RECEIPT, encoding="utf-8") as f:
        return json.load(f)


def cited_file(evidence: str) -> str | None:
    """The aaf-relative path a LEDGER_AUDIT evidence string points at.

    Value evidence   `<relpath>:<member> = <value>`
    String evidence  `<relpath>@0x<OFF>: '<token>'`
    """
    s = str(evidence)
    m = re.match(r"^([A-Za-z0-9_./\-]+?)(?::|@0x)", s)
    if not m:
        return None
    return m.group(1).replace("\\", "/")


def owner_tokens(owner_card: str) -> set[str]:
    """`B-02/B-03/B-04+B-04L+B-18` -> {B-02, B-03, B-04, B-04L, B-18} (upper-case)."""
    s = re.sub(r"\([^)]*\)", " ", owner_card)
    return {t.upper() for t in re.split(r"[+/,\s]+", s) if t}


def build_cards(receipt: dict) -> tuple[set[str], set[str], dict[str, str]]:
    """(writer cards, non-writer cards, card -> the step text that says why)."""
    cards: dict[str, str] = {}
    for step in receipt.get("steps", []):
        if isinstance(step, dict):
            card = step.get("card")
            if card:
                cards[str(card)] = json.dumps(step, sort_keys=True)
            continue
        m = re.match(r"^([A-Za-z]+\d*-[0-9A-Za-z]+):", str(step))
        if m and not m.group(1).lower().startswith("bm-"):
            cards[m.group(1)] = str(step)

    non_writers: dict[str, str] = {}
    for card, text in cards.items():
        if card.upper() == "B-18":
            non_writers[card] = "moves files into .../batmobile/ and reverts to vanilla; no value edit"
        elif "SKIPPED" in text:
            non_writers[card] = "step says SKIPPED"
        elif "'ported': False" in text or '"ported": false' in text:
            non_writers[card] = "step says ported: False (no bytes written)"
    writers = {c for c in cards if c not in non_writers}
    return writers, set(non_writers), non_writers


def find_prior(build: str, rel: str) -> tuple[str | None, str | None, int | None]:
    """(path, sha256, size) in that build, tolerating the B-18 move into batmobile/."""
    variants = [rel]
    if "/batmobile/" in rel:
        variants.append(rel.replace("/batmobile/", "/"))
    for v in variants:
        p = os.path.join(ROOT, "Builds", build, "aaf", v.replace("/", os.sep))
        if os.path.exists(p):
            return v, sha256_file(p), os.path.getsize(p)
    return None, None, None


def byte_state(rel: str, rc_sha: str, rc_size: int) -> tuple[str, str, dict[str, int]]:
    """(state, detail, {build: size}) against every earlier build's copy."""
    found: list[tuple[str, str, int]] = []
    for build in PRIOR:
        _path, sha, size = find_prior(build, rel)
        if sha:
            found.append((build, sha, size))
    if not found:
        return "no earlier copy", "no file at this path in " + ", ".join(PRIOR), {}
    sizes = {b: n for b, _sha, n in found}
    matches = [b for b, sha, _n in found if sha == rc_sha]
    if matches:
        return (f"same as {matches[0]}",
                f"sha256 identical to {', '.join(matches)} ({rc_size:,} B)", sizes)
    prior_sizes = ", ".join(sorted({f"{n:,} B" for _b, _s, n in found}))
    return ("differs from every earlier copy",
            f"differs from {', '.join(b for b, _s, _n in found)}: "
            f"{rc_size:,} B here vs {prior_sizes}", sizes)


def verdict_for(owner_card: str, tokens: set[str], writers: set[str],
                state: str, vanilla_paths: set[str], rel: str) -> tuple[str, str]:
    if rel in vanilla_paths or VANILLA_MARK in owner_card:
        return "vanilla", "receipt b18 lists the file in reverted_to_vanilla" \
            if rel in vanilla_paths else "owner_card says (vanilla bytes)"
    named = sorted(t for t in tokens if t in {w.upper() for w in writers})
    if state.startswith("differs"):
        extra = f"; owner_card names {', '.join(named)}" if named else \
            "; owner_card names no writer of this build"
        return "edited by this build", "bytes differ from every earlier copy" + extra
    if named:
        return "edited by this build", f"owner_card names {', '.join(named)}"
    if state.startswith("same"):
        return "inherited", ("bytes identical to an earlier build and owner_card "
                             "names no writer of this build")
    return "inherited", "owner_card names no writer of this build; no earlier copy to compare"


# ------------------------------------------------------------------ build
def build() -> dict:
    rows = la.load_rows()
    audit = la.build(rows)                      # the same verdicts G3-11 published
    receipt = load_receipt()
    aaf = {e["path"]: e for e in receipt["aaf"]["list"]}
    writers, non_writers, why = build_cards(receipt)
    vanilla_paths = set(receipt.get("b18", {}).get("reverted_to_vanilla", []))

    entries: list[dict] = []
    for a in audit["rows"]:
        if a["verdict"] != "TRANSLATED":
            continue
        rel = cited_file(a["evidence"])
        if not rel or rel not in aaf:
            entries.append({"id": a["id"], "doc": a["doc"], "dispo": a["dispo"],
                            "tier": a["tier"], "file": rel or "",
                            "aaf": None, "owner_card": "",
                            "prov": "UNKNOWN",
                            "basis": "cited file is not a receipt.aaf.list[] entry"})
            continue
        entry = aaf[rel]
        tokens = owner_tokens(entry["owner_card"])
        rc_size = os.path.getsize(os.path.join(AAF, rel.replace("/", os.sep)))
        state, detail, prior_sizes = byte_state(rel, entry["sha256"], rc_size)
        prov, basis = verdict_for(entry["owner_card"], tokens, writers, state,
                                  vanilla_paths, rel)
        entries.append({"id": a["id"], "doc": a["doc"], "dispo": a["dispo"],
                        "tier": a["tier"], "file": rel,
                        "aaf": {"path": entry["path"], "sha256": entry["sha256"]},
                        "owner_card": entry["owner_card"],
                        "byte_state": state, "byte_detail": detail,
                        "bytes": rc_size, "prior_sizes": prior_sizes,
                        "prov": prov, "basis": basis})

    counts = {p: 0 for p in PROV}
    counts["UNKNOWN"] = 0
    by_tier: dict[str, dict[str, int]] = {}
    for e in entries:
        counts[e["prov"]] = counts.get(e["prov"], 0) + 1
        by_tier.setdefault(e["prov"], {})
        by_tier[e["prov"]][e["tier"]] = by_tier[e["prov"]].get(e["tier"], 0) + 1

    # per cited file
    files: dict[str, dict] = {}
    for e in entries:
        f = files.setdefault(e["file"], {"rows": [], "owner_card": e["owner_card"],
                                         "prov": e["prov"],
                                         "byte_state": e.get("byte_state", "?"),
                                         "sha256": (e["aaf"] or {}).get("sha256", "")})
        f["rows"].append(e["id"])

    downgrade = [e for e in entries if e["prov"] in ("inherited", "vanilla")]
    vanilla_rows = [e for e in entries if e["prov"] == "vanilla"]

    # reconciliation with review-G3-11's 35: the review classified by owner_card only
    review_inherited = [e for e in entries
                        if e["aaf"] and not (owner_tokens(e["owner_card"])
                                             & {w.upper() for w in writers})]
    owner_only_base = [e for e in review_inherited
                       if "base" in e["owner_card"].lower()]
    owner_missing_writer = [e for e in entries
                            if e["aaf"] and e["prov"] == "edited by this build"
                            and not (owner_tokens(e["owner_card"])
                                     & {w.upper() for w in writers})]
    card_but_unchanged = [e for e in entries
                          if e["aaf"] and e["prov"] == "edited by this build"
                          and (owner_tokens(e["owner_card"])
                               & {w.upper() for w in writers})
                          and str(e.get("byte_state", "")).startswith("same as")]

    return {
        "generated_by": "Tools/scripts/ledger_provenance.py (--write)",
        "card": "GRB-G3-11 provenance dimension",
        "inputs": {
            "ledger": {"path": "Working/Translation/T_ROWS.jsonl", "rows": len(rows),
                       "sha256": sha256_file(LEDGER)},
            "audit": {"path": "Working/Translation/LEDGER_AUDIT.md",
                      "verdicts": audit["counts"]["verdicts"]},
            "build": {"path": "Builds/bm-RC1", "card": receipt.get("card"),
                      "tag": receipt.get("tag"),
                      "receipt_sha256": sha256_file(RECEIPT),
                      "aaf_entries": len(receipt["aaf"]["list"])},
            "prior_builds": list(PRIOR),
        },
        "rules": {
            "translated_set": "the 85 rows LEDGER_AUDIT marks TRANSLATED, unchanged",
            "cited_file": "parsed from the audit's evidence string (path before ':' or '@0x')",
            "vanilla": "file in receipt.b18.reverted_to_vanilla, or owner_card has (vanilla bytes)",
            "edited": "bytes differ from every earlier build's copy, or owner_card names a "
                      "card this build's steps record as writing",
            "inherited": "bytes identical to an earlier build, or owner_card names only "
                         "that lineage; means not edited by bm-RC1",
            "writer_cards": ", ".join(sorted(writers)),
            "non_writer_cards": "; ".join(f"{c} ({why[c]})" for c in sorted(non_writers)),
        },
        "counts": {"translated": len(entries), "provenance": counts,
                   "by_tier": by_tier},
        "rows": entries,
        "files": {k: v for k, v in sorted(files.items())},
        "downgrade": [e["id"] for e in downgrade],
        "reconcile": {
            "review_inherited": len(review_inherited),
            "review_base": len(owner_only_base),
            "vanilla": len(vanilla_rows),
            "owner_missing_writer": [e["id"] for e in owner_missing_writer],
            "owner_missing_writer_bytes": (owner_missing_writer[0].get("bytes")
                                           if owner_missing_writer else None),
            "owner_missing_writer_prior": (owner_missing_writer[0].get("prior_sizes", {})
                                           if owner_missing_writer else {}),
            "card_but_unchanged": [e["id"] for e in card_but_unchanged],
        },
        "vanilla_rows": [e["id"] for e in vanilla_rows],
    }


# ------------------------------------------------------------------ render
def render_md(doc: dict) -> str:
    inp, c = doc["inputs"], doc["counts"]
    out: list[str] = []
    out.append("# Ledger provenance - which file each TRANSLATED row rests on")
    out.append("")
    out.append("GRB-G3-11 (provenance dimension). Generated by "
               "`Tools/scripts/ledger_provenance.py --write`; `--check` re-derives this "
               "file from the same inputs and fails on any drift.")
    out.append("")
    out.append("Review-G3-11 accepted the 85 TRANSLATED verdicts as byte checks but "
               "found that 35 of them rest on a file bm-RC1 never edited. This file "
               "adds that dimension; it changes no verdict in "
               "`LEDGER_AUDIT.md`, `T_ROWS.jsonl` or the receipt.")
    out.append("")
    out.append("## Inputs")
    out.append("")
    out.append(f"- ledger `{inp['ledger']['path']}` - {inp['ledger']['rows']} rows, "
               f"sha256 `{inp['ledger']['sha256'][:16]}...`")
    out.append(f"- audit `{inp['audit']['path']}` - verdicts "
               + ", ".join(f"{k} {v}" for k, v in inp["audit"]["verdicts"].items()))
    out.append(f"- build `{inp['build']['path']}` (card {inp['build']['card']}, tag "
               f"{inp['build']['tag']}) - receipt sha256 "
               f"`{inp['build']['receipt_sha256'][:16]}...`, "
               f"{inp['build']['aaf_entries']} aaf entries")
    out.append("- earlier builds compared byte for byte: "
               + ", ".join(f"`{b}`" for b in inp["prior_builds"]))
    out.append("")
    out.append("## Counts")
    out.append("")
    out.append("| provenance of the cited file | rows | tiers | status to record |")
    out.append("|---|---|---|---|")
    for p in PROV:
        tiers = ", ".join(f"{k} {v}" for k, v in sorted(c["by_tier"].get(p, {}).items())) or "-"
        out.append(f"| {p} | {c['provenance'].get(p, 0)} | {tiers} | {RECOMMEND[p]} |")
    if c["provenance"].get("UNKNOWN"):
        out.append(f"| UNKNOWN | {c['provenance']['UNKNOWN']} | - | not resolved |")
    out.append(f"| **total TRANSLATED** | **{c['translated']}** | | |")
    out.append("")
    out.append(f"Rows whose status must be downgraded: **{len(doc['downgrade'])}** "
               f"({len(doc['downgrade']) - len(doc['vanilla_rows'])} inherited, "
               f"{len(doc['vanilla_rows'])} vanilla).")
    out.append("")
    out.append("## Method")
    out.append("")
    for key, text in doc["rules"].items():
        out.append(f"- **{key}**: {text}")
    out.append("")
    out.append("The verdict is about the **file**, not the value. A file this build "
               "edited can still carry a donor value (the `.epe` tokens are the donor's "
               "graph names), and a file this build did not edit can hold a value an "
               "earlier build wrote. What the verdict settles is the audit's own "
               "definition - \"present in a built file\" - and whether the build in "
               "question is the one that produced that file.")
    out.append("")
    out.append("## Rows whose status must be downgraded")
    out.append("")
    out.append(f"{len(doc['downgrade'])} rows cite a file bm-RC1 did not edit. Every one "
               "of those files is in the build, so the audit's literal test (\"present in "
               "a built file\") passes; what fails is the reading that this build produced "
               "the value. The recommendation column is what the ledger should say.")
    out.append("")
    out.append("| id | doc | dispo | tier | cited file | owner_card | provenance | basis |")
    out.append("|---|---|---|---|---|---|---|---|")
    for e in doc["rows"]:
        if e["prov"] not in ("inherited", "vanilla"):
            continue
        f = e["file"].replace("editor/entities/jc_vehicles/", "E/") \
                      .replace("models/jc_vehicles/", "M/")
        out.append(f"| {e['id']} | {e['doc']} | {e['dispo']} | {e['tier']} | `{f}` | "
                   f"{e['owner_card']} | **{e['prov']}** | {e['basis']} |")
    out.append("")
    out.append("## Cited files")
    out.append("")
    out.append("| cited file | n | row ids | owner_card | provenance | bytes vs earlier builds |")
    out.append("|---|---|---|---|---|---|")
    for path, f in doc["files"].items():
        short = path.replace("editor/entities/jc_vehicles/01_land/"
                             "v0300_car_kensington_sportsmuscle/", "E/v0300/") \
                    .replace("editor/entities/jc_vehicles/00_shared/", "E/shared/") \
                    .replace("models/jc_vehicles/01_land/"
                             "v0300_car_kensington_sportsmuscle/", "M/v0300/")
        out.append(f"| `{short}` | {len(f['rows'])} | {', '.join(f['rows'])} | "
                   f"{f['owner_card']} | {f['prov']} | {f['byte_state']} |")
    out.append("")
    out.append("## Every TRANSLATED row")
    out.append("")
    out.append("| id | doc | dispo | tier | cited file | owner_card | provenance |")
    out.append("|---|---|---|---|---|---|---|")
    for e in doc["rows"]:
        short = (e["file"] or "").replace(
            "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/", "E/v0300/") \
            .replace("editor/entities/jc_vehicles/00_shared/", "E/shared/") \
            .replace("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/", "M/v0300/")
        out.append(f"| {e['id']} | {e['doc']} | {e['dispo']} | {e['tier']} | "
                   f"`{short}` | {e['owner_card'] or '-'} | {e['prov']} |")
    out.append("")
    out.append("## Reconciliation with review-G3-11's 35")
    out.append("")
    r = doc["reconcile"]
    out.append(f"- **The review's 35** = {r['review_base']} rows whose `owner_card` "
               f"literally contains `base` + {r['vanilla']} vanilla row.")
    out.append(f"- **By `owner_card` alone, {r['review_inherited']} rows** name no card "
               f"this build records as writing: the {r['review_base']} base rows, the "
               f"{r['vanilla']} vanilla row, and "
               f"{r['review_inherited'] - r['review_base'] - r['vanilla']} rows whose card "
               f"names only earlier-build ids without the word `base` "
               f"(`B-02/B-03/B-04+B-04L+B-18` for the parts module, `B-07+B-18` for the "
               f"lights module).")
    if r["owner_missing_writer"]:
        prior = ", ".join(sorted({f"{n:,} B"
                                 for n in r["owner_missing_writer_prior"].values()}))
        out.append(f"- **{len(r['owner_missing_writer'])} parts rows raised on the bytes**: "
                   + ", ".join(f"`{i}`" for i in r["owner_missing_writer"])
                   + " cite `sportsmuscle_vehicle_parts.vmodc`, whose `owner_card` "
                     "(`B-02/B-03/B-04+B-04L+B-18`) names only B-04L, and B-04L's own "
                     "step says `ported: False`. The built file is "
                   + f"{r['owner_missing_writer_bytes']:,} B"                     + f" while the earlier copies are {prior}, so a card of this build "
                     "(B-04R, which records 61 re-parted parts) did write it and the "
                     "receipt does not say so. These rows stay `edited by this build` "
                     "on the bytes, not on the card.")
    out.append(f"- **Downgrade set = {len(doc['downgrade'])}** = the review's "
               f"{r['review_base'] + r['vanilla']} + "
               f"{len(doc['downgrade']) - r['review_base'] - r['vanilla']} lights row "
               f"(`B-07+B-18`, bytes identical to bm-007). The "
               f"{len(r['owner_missing_writer'])} parts rows are in neither set: the "
               f"review's `base`-string test missed them and the bytes raise them.")
    if r["card_but_unchanged"]:
        out.append("- Card named but bytes unchanged vs the immediate predecessor: "
                   + ", ".join(f"`{i}`" for i in r["card_but_unchanged"])
                   + " - the card wrote the same bytes in both builds, so the file is "
                     "still this build's output.")
    out.append("")
    out.append("## UNKNOWN")
    out.append("")
    out.append("1. **Whether an earlier build wrote an inherited value.** The receipt "
               "records only the last owner; `bm-005`..`bm-013b` are compared by hash "
               "only, so \"inherited\" means \"bm-RC1 did not change these bytes\", not "
               "\"no build ever did\". Where the value came from needs those builds' "
               "own cards.")
    out.append("2. **Whether the game reads any of these files.** Every verdict here is "
               "file-to-file; no runtime observation is involved.")
    out.append("3. **Which cell of a comma-shifted row a value came from** - unchanged "
               "from LEDGER_AUDIT.md; this script inherits the audit's evidence strings.")
    out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------ cli
def write() -> int:
    doc = build()
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)}")
    print("provenance:", doc["counts"]["provenance"])
    print("downgrade:", len(doc["downgrade"]), "rows")
    return 0


def check() -> int:
    if not os.path.exists(OUT_MD):
        print("FAIL: output missing - run --write first")
        return 1
    stored = open(OUT_MD, encoding="utf-8").read()
    doc = build()
    fresh = render_md(doc)
    fails: list[str] = []
    if stored != fresh:
        old = stored.splitlines()
        new = fresh.splitlines()
        first = next((i for i, (a, b) in enumerate(zip(old, new)) if a != b),
                     min(len(old), len(new)))
        fails.append(f"markdown differs from a fresh re-derivation at line {first + 1}")
    if doc["counts"]["translated"] != 85:
        fails.append(f"TRANSLATED rows {doc['counts']['translated']} != 85")
    total = sum(doc["counts"]["provenance"].values())
    if total != doc["counts"]["translated"]:
        fails.append(f"provenance counts {total} != TRANSLATED rows")
    if len({e["id"] for e in doc["rows"]}) != len(doc["rows"]):
        fails.append("duplicate row ids")
    for e in doc["rows"]:
        if not e["file"]:
            fails.append(f"{e['id']}: no cited file")
        elif not os.path.exists(os.path.join(AAF, e["file"].replace("/", os.sep))):
            fails.append(f"{e['id']}: cited file absent from the build")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {doc['counts']['translated']}/{doc['counts']['translated']} TRANSLATED rows "
          f"with provenance")
    print("provenance:", doc["counts"]["provenance"])
    print("downgrade:", len(doc["downgrade"]), "rows")
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
