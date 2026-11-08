"""rc4_pins.py - authoritative, byte-derived pins for `Builds/bm-RC4`, plus the stale-literal list.

Three numbers circulate for the RC4 `.ee` (11,225,532 / 11,225,533 / 11,225,534 B) and three for
`receipt.json` (211,711 / 215,445 / 217,652 B). This script treats the bytes on disk as the only
authority: every pin is stat()/sha256()'d from the tree, the build's own `receipt.json` is read as
the witness, and every other value found in the prose is reported as a stale literal with the file
and line that holds it.

No existing pin, report or build file is edited. `--write` only writes the two files under
`tmp/freebuff/` that the RC5 scaffold consumes:

    python Tools/scripts/rc4_pins.py --write   # derive pins -> tmp/freebuff/rc5-pins.json
    python Tools/scripts/rc4_pins.py --check   # re-derive, compare, print the stale list

Exit 0 = the pins file matches the bytes (--check, stale literals are printed, not fatal);
1 = drift or missing pins file; 2 = the RC4 tree is missing.

Why the stale list is not a failure: RC4's pins must not be rewritten (RC5 consumes the list), so
finding the old literals is the expected outcome. What --check enforces is that the *authoritative*
values still describe the bytes.
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
RC = os.path.join(ROOT, "Builds", "bm-RC4")
DROP = os.path.join(RC, "drop")
AAFDIR = os.path.join(RC, "aaf")
RECEIPT = os.path.join(RC, "receipt.json")
INSTALL = os.path.join(RC, "install.ps1")
PINS = os.path.join(ROOT, "tmp", "freebuff", "rc5-pins.json")
STALE = os.path.join(ROOT, "tmp", "freebuff", "rc5-stale-pins.json")

# Roots scanned for stale literals: the four named in the task, plus the verification reports where
# the 215,445 B receipt figure actually lives.
SCAN_ROOTS = [os.path.join(ROOT, p) for p in (
    "Tools/scripts", "Working/Q", "Working/Translation", "tmp/freebuff/queue/done",
    "tmp/freebuff/reports")]
# This script and the reconcile report quote the stale values on purpose.
EXCLUDE = {os.path.abspath(__file__),
           os.path.join(ROOT, "tmp", "freebuff", "reports", "rc5-size-pins-reconcile.md")}
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache"}

# Values that are NOT the artifact, with the evidence that retired them. Authoritative values are
# computed by derive(); these are only the retired claims.
STALE_CLAIMS = [
    {"pin": "ee", "value": 11225534,
     "why": "build-d13's pin, paired there with sha256 a233c93d... (a different .ee); the RC4 rebuild "
            "at 12:59:52 shipped b72690d3... at 11,225,533 B, so this is +1 B of the artifact"},
    {"pin": "ee", "value": 11225532,
     "why": "V-01 read this during the concurrent rebuild (the file was 0 B, then absent, then "
            "11,225,532); the final pack at 12:59:52 is 11,225,533 B"},
    {"pin": "receipt_json", "value": 211711,
     "why": "build-d13's receipt pin; the receipt was rewritten to 217,652 B at 13:00:07"},
    {"pin": "receipt_json", "value": 215445,
     "why": "V-01's snapshot of the pre-final receipt; 2,207 B short of the 217,652 B on disk"},
    {"pin": "install_sha256", "value": "df23485d65f358e14ea8d0b5037d42f0",
     "why": "32 hex characters where a sha256 has 64, and it matches neither install.ps1's SHA-256 "
            "nor its MD5; brief-only value"},
]


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def stat_sha(p: str) -> dict:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return {"path": rel(p), "bytes": os.path.getsize(p), "sha256": h.hexdigest()}


def find_ee() -> str:
    base = os.path.join(DROP, "editor", "entities", "jc_vehicles", "01_land")
    hits = [os.path.join(dp, n) for dp, _dn, fs in os.walk(base) for n in fs
            if n.endswith(".ee")]
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one .ee under {rel(base)}, found {len(hits)}")
    return hits[0]


def walk_files(root: str):
    for dp, dn, fs in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for n in sorted(fs):
            yield os.path.join(dp, n)


def derive() -> dict:
    for p in (RC, DROP, RECEIPT, INSTALL):
        if not os.path.exists(p):
            print(f"MISSING: {rel(p)} (the RC4 tree is not there)", file=sys.stderr)
            raise SystemExit(2)
    ee = find_ee()
    ee_stat = stat_sha(ee)
    toc_stat = stat_sha(ee + ".toc")
    inst_stat = stat_sha(INSTALL)
    rec_stat = stat_sha(RECEIPT)

    drop = [dict(stat_sha(p), drop_path=os.path.relpath(p, DROP).replace("\\", "/"))
            for p in walk_files(DROP)]
    drop.sort(key=lambda d: d["drop_path"])
    aaf_n = sum(1 for _ in walk_files(AAFDIR))
    tree_n = sum(1 for _ in walk_files(RC))
    tree_b = sum(os.path.getsize(p) for p in walk_files(RC))

    rec = json.load(open(RECEIPT, encoding="utf-8-sig"))
    by_path = {f["path"]: f for f in rec.get("files", [])}
    ee_rel = os.path.relpath(ee, DROP).replace("\\", "/")
    rec_ee = by_path.get(ee_rel, {})
    mismatched = [d["drop_path"] for d in drop
                  if d["drop_path"] not in by_path
                  or by_path[d["drop_path"]].get("bytes") != d["bytes"]
                  or by_path[d["drop_path"]].get("sha256") != d["sha256"]]

    witness = {
        "receipt_schema": rec.get("schema"),
        "receipt_tag": rec.get("tag"),
        "receipt_file_entries": len(rec.get("files", [])),
        "receipt_ee_bytes": rec_ee.get("bytes"),
        "receipt_ee_sha256": rec_ee.get("sha256"),
        "receipt_says_bytes": rec_ee.get("bytes") == ee_stat["bytes"],
        "receipt_says_sha256": rec_ee.get("sha256") == ee_stat["sha256"],
        "drop_entries_matching_receipt": len(drop) - len(mismatched),
        "drop_mismatches": mismatched,
        "step_naming_the_pack": next((s for s in rec.get("steps", []) if ".ee (" in s), ""),
    }

    pins = {
        "ee": ee_stat,
        "ee_toc": toc_stat,
        "install_ps1": inst_stat,
        "install_sha256": inst_stat["sha256"],
        "install_sha256_hex_chars": len(inst_stat["sha256"]),
        "receipt_json": rec_stat,
        "drop_files": len(drop),
        "drop_total_bytes": sum(d["bytes"] for d in drop),
        "tree_files": tree_n,
        "tree_total_bytes": tree_b,
        "aaf_files": aaf_n,
    }
    return {"schema": 1, "build": "Builds/bm-RC4", "derived_from": "bytes on disk",
            "witness": witness, "pins": pins, "drop": drop}


def forms(pin: str, value) -> list[str]:
    """Literal shapes a value takes in prose: bare and thousands-separated, or hex."""
    if isinstance(value, int):
        return [str(value), f"{value:,}"]
    return [str(value)]


def authoritative(doc: dict, pin: str):
    p = doc["pins"]
    if pin == "ee":
        return p["ee"]["bytes"]
    if pin == "ee_toc":
        return p["ee_toc"]["bytes"]
    if pin == "receipt_json":
        return p["receipt_json"]["bytes"]
    if pin == "install_ps1":
        return p["install_ps1"]["bytes"]
    if pin == "install_sha256":
        return p["install_sha256"]
    raise KeyError(pin)


def candidates(doc: dict) -> list[dict]:
    pins = ("ee", "ee_toc", "install_ps1", "install_sha256", "receipt_json")
    out = [{"pin": p, "value": authoritative(doc, p), "state": "AUTHORITATIVE",
            "why": "measured from the bytes"} for p in pins]
    out += [dict(c, state="STALE") for c in STALE_CLAIMS]
    return out


def pattern(value) -> re.Pattern:
    if isinstance(value, int):
        alts = "|".join(re.escape(f) for f in forms("", value))
        return re.compile(r"(?<![\d,])(?:" + alts + r")(?![\d])")
    return re.compile(r"(?<![0-9a-fA-F])" + re.escape(str(value)) + r"(?![0-9a-fA-F])",
                      re.IGNORECASE)


def readable(p: str) -> bool:
    try:
        if os.path.getsize(p) > 8 << 20:
            return False
        with open(p, "rb") as f:
            return b"\x00" not in f.read(8192)
    except OSError:
        return False


def scan(doc: dict) -> list[dict]:
    cands = [(c, pattern(c["value"])) for c in candidates(doc)]
    rows = []
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for path in walk_files(root):
            if os.path.abspath(path) in EXCLUDE or not readable(path):
                continue
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                for cand, rx in cands:
                    for m in rx.finditer(line):
                        rows.append({"file": rel(path), "line": i, "pin": cand["pin"],
                                     "literal": m.group(0), "state": cand["state"],
                                     "why": cand["why"],
                                     "excerpt": line.strip()[:200]})
    return rows


def show(doc: dict, rows: list[dict]) -> None:
    p, w = doc["pins"], doc["witness"]
    print("AUTHORITATIVE PINS (bytes on disk)")
    print(f"  .ee            {p['ee']['bytes']:,} B  {p['ee']['sha256']}")
    print(f"  .ee.toc        {p['ee_toc']['bytes']:,} B  {p['ee_toc']['sha256']}")
    print(f"  install.ps1    {p['install_ps1']['bytes']:,} B  {p['install_ps1']['sha256']}")
    print(f"  receipt.json   {p['receipt_json']['bytes']:,} B  {p['receipt_json']['sha256']}")
    print(f"  drop           {p['drop_files']} files, {p['drop_total_bytes']:,} B")
    print(f"  tree           {p['tree_files']} files, {p['tree_total_bytes']:,} B "
          f"(aaf {p['aaf_files']})")
    print(f"WITNESS receipt: schema {w['receipt_schema']} {w['receipt_tag']!r}, "
          f"{w['receipt_file_entries']} file entries; says .ee {w['receipt_ee_bytes']:,} B = "
          f"{w['receipt_says_bytes']}, sha256 equal = {w['receipt_says_sha256']}; "
          f"{w['drop_entries_matching_receipt']}/{p['drop_files']} drop entries match")
    if w["drop_mismatches"]:
        print(f"  DRIFT: {w['drop_mismatches']}")

    stale = [r for r in rows if r["state"] == "STALE"]
    auth = [r for r in rows if r["state"] == "AUTHORITATIVE"]
    print(f"\nSTALE LITERALS ({len(stale)} occurrences; the artifact is "
          f"{p['ee']['bytes']:,} B .ee / {p['receipt_json']['bytes']:,} B receipt.json)")
    if not stale:
        print("  none")
    for r in sorted(stale, key=lambda r: (r["file"], r["line"], r["pin"])):
        print(f"  {r['file']}:{r['line']}  {r['pin']} = {r['literal']}  -- {r['why']}")
    print(f"\nAUTHORITATIVE LITERALS already in prose ({len(auth)} occurrences)")
    for r in sorted(auth, key=lambda r: (r["file"], r["line"], r["pin"])):
        print(f"  {r['file']}:{r['line']}  {r['pin']} = {r['literal']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="derive the pins and write the two files")
    g.add_argument("--check", action="store_true", help="re-derive and compare with the pins file")
    a = ap.parse_args()

    doc = derive()
    rows = scan(doc)

    if a.write:
        os.makedirs(os.path.dirname(PINS), exist_ok=True)
        for path, payload in ((PINS, doc), (STALE, {"schema": 1, "build": doc["build"],
                                                    "authoritative": doc["pins"],
                                                    "rows": rows})):
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(payload, f, indent=1, sort_keys=True)
                f.write("\n")
            print(f"wrote {rel(path)}")
        show(doc, rows)
        return 0

    if not os.path.exists(PINS):
        print(f"FAIL: {rel(PINS)} missing (run --write)", file=sys.stderr)
        return 1
    want = json.load(open(PINS, encoding="utf-8"))
    drift = []
    for k, v in want["pins"].items():
        got = doc["pins"].get(k)
        if got != v:
            drift.append(f"{k}: pin {v} != bytes {got}")
    if want.get("drop") != doc["drop"]:
        drift.append("drop file list/hashes differ from the pins file")
    show(doc, rows)
    if drift:
        print("\nFAIL: the bytes no longer match the pins file", file=sys.stderr)
        for d in drift:
            print(f"  {d}", file=sys.stderr)
        return 1
    print(f"\nPASS: {rel(PINS)} matches the bytes "
          f"({doc['pins']['tree_files']} files re-hashed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
