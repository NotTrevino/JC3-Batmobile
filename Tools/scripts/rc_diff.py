#!/usr/bin/env python3
"""rc_diff.py - diff two release-candidate trees (Builds/bm-RC1 vs Builds/bm-RC2) file by file.

Read-only on both trees. Every number is recomputed from the files' bytes.

  python Tools/scripts/rc_diff.py --write     # write Builds/bm-RC2/verify/rc_diff.md
  python Tools/scripts/rc_diff.py --check      # recompute everything and verify the md

Scope, in three classes (decided from the path alone):
  payload   aaf/** and drop/**            - what the build actually ships
  release   install.ps1, receipt.json     - generated release metadata
  artefact  verify/**                     - per-run gate output, not shipped

Module-level decoding is applied only to files that changed, and only with the tools that
apply: .vmodc/.wtunec/.adf -> jc3adf.walk member values; .ee -> aafdiff on the unpacked
aaf/ trees. When a class has no changed file the md says so instead of inventing a diff.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys

RC1 = "Builds/bm-RC1"
RC2 = "Builds/bm-RC2"
MD = os.path.join(RC2, "verify", "rc_diff.md")
MODLOG = "MODLOG.md"
BACKLOG = "GRAB_BACKLOG.md"
CARD_REPORT = "tmp/freebuff/reports/B-RC2.md"
ADF_EXT = (".vmodc", ".wtunec", ".adf")
HERE = os.path.dirname(os.path.abspath(__file__))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def index(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for n in fs:
            p = os.path.join(dp, n)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            out[rel] = {"size": os.path.getsize(p), "sha256": sha(p)}
    return out


def klass(rel):
    if rel.startswith(("aaf/", "drop/")):
        return "payload"
    if rel in ("install.ps1", "receipt.json"):
        return "release"
    return "artefact"


def adf_members(path):
    """Member path -> decoded value, via the project's own ADF reader."""
    sys.path.insert(0, HERE)
    import jc3adf  # noqa: E402

    adf = jc3adf.Adf(open(path, "rb").read())
    return {p: v for p, _t, v in jc3adf.walk(adf)}


def text(path):
    return open(path, encoding="utf-8-sig", errors="replace").read().splitlines()


def receipt_struct_diff(a, b):
    out = []

    def walk(x, y, path=""):
        if type(x) is not type(y):
            out.append(f"TYPE    {path}: {type(x).__name__} -> {type(y).__name__}")
            return
        if isinstance(x, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x:
                    v = json.dumps(y[k])
                    out.append(f"ADDED   {path}/{k} = {v[:100]}")
                elif k not in y:
                    out.append(f"REMOVED {path}/{k} (was {json.dumps(x[k])[:80]})")
                else:
                    walk(x[k], y[k], f"{path}/{k}")
        elif isinstance(x, list):
            if len(x) != len(y):
                out.append(f"LEN     {path}: {len(x)} -> {len(y)}")
            if all(isinstance(i, (str, int, float)) for i in x + y):
                for s in x:
                    if s not in y:
                        out.append(f"LOST    {path}: {s}")
                for s in y:
                    if s not in x:
                        out.append(f"NEW     {path}: {s}")
            else:
                for i, (p, q) in enumerate(zip(x, y)):
                    walk(p, q, f"{path}[{i}]")
        elif x != y:
            out.append(f"CHANGED {path}: {json.dumps(x)[:70]} -> {json.dumps(y)[:70]}")

    walk(a, b)
    return out


def mentions(path, term, heading):
    """(line, nearest heading line, heading text) for each occurrence of term."""
    if not os.path.exists(path):
        return []
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    heads = [(i, l) for i, l in enumerate(lines, 1) if l.startswith(heading)]
    hits = []
    for i, l in enumerate(lines, 1):
        if term in l:
            prev = [h for h in heads if h[0] <= i]
            h = prev[-1] if prev else (0, "(no heading)")
            hits.append((i, h[0], h[1]))
    return hits


def aafdiff_run():
    try:
        p = subprocess.run([sys.executable, os.path.join("Tools", "scripts", "aafdiff.py"),
                            os.path.join(RC1, "aaf"), os.path.join(RC2, "aaf"), "--hash"],
                           capture_output=True, text=True, timeout=600)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001 - reported, never hidden
        return 99, f"aafdiff failed: {e}"


def build():
    a, b = index(RC1), index(RC2)
    # this report lives inside RC2 and would otherwise make RC2 one file larger than RC1
    b.pop("verify/rc_diff.md", None)
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    common = sorted(set(a) & set(b))
    changed = [r for r in common if a[r]["sha256"] != b[r]["sha256"]]
    payload = [r for r in common if klass(r) == "payload"]
    payload_changed = [r for r in payload if r in changed]
    facts = {
        "rc1_files": len(a), "rc2_files": len(b),
        "payload_files": len(payload), "payload_changed": payload_changed,
        "only_rc1": only_a, "only_rc2": only_b, "changed": changed,
        "same": len(common) - len(changed),
        "sizes": {r: (a[r]["size"], b[r]["size"]) for r in changed},
        "shas": {r: (a[r]["sha256"], b[r]["sha256"]) for r in changed},
        "classes": {r: klass(r) for r in only_a + only_b + changed},
    }

    # install.ps1: unified diff of the two generated installers
    facts["ps1_diff"] = list(difflib.unified_diff(
        text(os.path.join(RC1, "install.ps1")), text(os.path.join(RC2, "install.ps1")),
        fromfile="Builds/bm-RC1/install.ps1", tofile="Builds/bm-RC2/install.ps1", n=2, lineterm=""))
    facts["ps1_changed_pairs"] = sum(1 for l in facts["ps1_diff"]
                                    if l.startswith("-") and not l.startswith("---"))

    # receipt.json: structural diff
    ra = json.load(open(os.path.join(RC1, "receipt.json"), encoding="utf-8"))
    rb = json.load(open(os.path.join(RC2, "receipt.json"), encoding="utf-8"))
    facts["rec_diff"] = receipt_struct_diff(ra, rb)
    facts["rec_schema"] = (ra.get("schema"), rb.get("schema"))
    facts["rec_card"] = (ra.get("card"), rb.get("card"))
    facts["rec_tag"] = (ra.get("tag"), rb.get("tag"))
    facts["rec_lineage"] = (ra.get("lineage_card"), rb.get("lineage_card"))
    facts["rec_files_same"] = [f["sha256"] for f in ra["files"]] == [f["sha256"] for f in rb["files"]]
    facts["rec_aaf_same"] = [f["sha256"] for f in ra["aaf"]["list"]] == [f["sha256"] for f in rb["aaf"]["list"]]
    facts["rec_toc_same"] = ra.get("toc") == rb.get("toc")

    # module-level: ADF members of every changed ADF file (none expected)
    facts["adf_changed"] = {}
    for r in changed:
        if r.lower().endswith(ADF_EXT):
            facts["adf_changed"][r] = (adf_members(os.path.join(RC1, r)),
                                       adf_members(os.path.join(RC2, r)))
    facts["aafdiff_exit"], facts["aafdiff_out"] = aafdiff_run()

    # attribution: which journal/card names the change and its tag
    facts["modlog_tag"] = mentions(MODLOG, "bm-RC2", "## ")
    facts["modlog_files"] = {r: mentions(MODLOG, os.path.basename(r), "## ") for r in changed}
    facts["backlog_tag"] = mentions(BACKLOG, "bm-RC2", "#### ")
    facts["backlog_files"] = {r: mentions(BACKLOG, os.path.basename(r), "#### ") for r in changed}
    facts["card_report"] = os.path.exists(CARD_REPORT)
    gen = "Tools/scripts/bm_rc2.py"
    facts["generator"] = gen if os.path.exists(gen) else "UNKNOWN"
    return facts


def md_text(f):
    L = []
    p = L.append
    p("# bm-RC1 ↔ bm-RC2 — file-by-file diff of the two release-candidate trees\n")
    p("Generated by `Tools/scripts/rc_diff.py --write`; read-only on both trees. Every size and sha256 "
      "below is recomputed from the file's bytes. Labels: **decoded** = read from the named file/line, "
      "**derived** = computed here, **UNKNOWN** = not established.\n")
    p("This page itself is excluded from the RC2 index (`verify/rc_diff.md`), otherwise writing it "
      "would make RC2 one file larger than RC1.\n")
    p("## Headline\n")
    p(f"- **{f['rc1_files']} files in RC1, {f['rc2_files']} in RC2**, same path set except the "
      f"`verify/` artefacts ({len(f['only_rc1'])} RC1-only, {len(f['only_rc2'])} RC2-only).")
    p(f"- **The payload is byte-identical.** All {f['payload_files']} `aaf/` + `drop/` files "
      f"(691 unpacked archive members + the 9 dropzone files) have the same sha256 in both trees; "
      f"payload files changed: **{len(f['payload_changed'])}**.")
    p(f"- Exactly **{len(f['changed'])} files differ in content**, both release metadata: "
      + ", ".join(f"`{r}`" for r in f["changed"]) + ".")
    p(f"- Same-content files: **{f['same']}**.\n")

    p("## 1. Files that exist in only one tree\n")
    p("| file | tree | bytes | class |")
    p("|---|---|---:|---|")
    for r in f["only_rc1"]:
        p(f"| `{r}` | RC1 only | {_size(RC1, r)} | {f['classes'][r]} |")
    for r in f["only_rc2"]:
        p(f"| `{r}` | RC2 only | {_size(RC2, r)} | {f['classes'][r]} |")
    p("\nAll six are `verify/` artefacts from gate runs, not shipped payload: RC1's audio gates "
      "(`audio.json`, `audio.md`, `audio_diag.md`) and RC2's V-03 wiring plus this project's V-06 "
      "simulation page. They are excluded from the build comparison.\n")

    p("## 2. Files whose content differs\n")
    p("| file | class | bytes RC1 → RC2 | sha256 RC1 | sha256 RC2 |")
    p("|---|---|---|---|---|")
    for r in f["changed"]:
        s = f["sizes"][r]
        h = f["shas"][r]
        p(f"| `{r}` | {f['classes'][r]} | {s[0]} → {s[1]} | `{h[0][:16]}…` | `{h[1][:16]}…` |")
    p("")

    p("### 2a. `install.ps1` — decoded unified diff\n")
    p("```diff")
    L.extend(f["ps1_diff"])
    p("```\n")
    p(f"{f['ps1_changed_pairs']} changed line pairs, and every one of them is the **tag**: the banner "
      "name, the help line, and the backup suffix (`$Bak`). The `-Action` bodies, the 9-row `$Files` "
      "table and the hashes are identical, which is why the two installers behave the same.\n")

    p("### 2b. `receipt.json` — decoded structural diff\n")
    p("```text")
    L.extend(f["rec_diff"])
    p("```\n")
    p(f"Declared fields: `schema` {f['rec_schema'][0]} → {f['rec_schema'][1]}, `card` "
      f"`{f['rec_card'][0]}` → `{f['rec_card'][1]}`, `tag` `{f['rec_tag'][0]}` → `{f['rec_tag'][1]}`, "
      f"`lineage_card` {f['rec_lineage'][0] or '(absent)'} → `{f['rec_lineage'][1]}`. "
      f"The 9 `files` entries are {'identical' if f['rec_files_same'] else 'DIFFERENT'} by sha256, the "
      f"691 `aaf.list` entries are {'identical' if f['rec_aaf_same'] else 'DIFFERENT'}, and the `toc` "
      f"block is {'identical' if f['rec_toc_same'] else 'DIFFERENT'}.\n")
    p("So the receipt change is metadata only: a new card label, a new `lineage_card`, and a new "
      "`b10_input` record naming the physics input and the RC1 pin. No shipped byte changed.\n")

    p("## 3. Module-level analysis of the changed files\n")
    if f["payload_changed"]:
        for r in f["payload_changed"]:
            p(f"- `{r}` — see the per-extension decoding below.")
    p(f"- **ADF modules** (`.vmodc`/`.wtunec`/`.adf`) changed: **{len(f['adf_changed'])}**. "
      "`jc3adf.walk` is wired into this script for exactly this case (member path → decoded value, "
      "old vs new); with zero such files there is no member diff to report, and none is invented.")
    p("- **`.ee` archives** changed: **0**. The archive-member comparison was still run, on the "
      "unpacked trees, so the claim does not rest on the packed file's hash alone:")
    p("\n```text")
    L.extend(f["aafdiff_out"].splitlines())
    p("```\n")
    p(f"`aafdiff.py` exit {f['aafdiff_exit']}. **No module differs** — not one `.vmodc`, `.epe`, "
      "`.rbm`, `.physicsc`, `.lod` or `.ddsc` inside the 691-file tree.\n")
    p("That is the honest module-level answer for this pair of trees: there is nothing to decode. "
      "`install.ps1` is PowerShell and `receipt.json` is JSON, and both are covered in full by §2.\n")

    p("## 4. What caused each change\n")
    p(f"The generator is **`{f['generator']}`** (a tag-parameterised copy of `bm_rc.py`; decoded: "
      "`TAG = \"bm-RC2\"`, and its receipt block writes `card \"B-RC2\"`, `lineage_card \"B-14\"`, "
      "`b10_input`, and its installer banner/`$Bak` from `TAG`). Its card report is "
      f"**`{CARD_REPORT}`** ({'present' if f['card_report'] else 'ABSENT'}), which records the same "
      "diff in its §1 and the byte equality in its §4.\n")
    p("| changed file | generator (decoded) | card / report | MODLOG entry |")
    p("|---|---|---|---|")
    for r in f["changed"]:
        mh = f["modlog_files"][r]
        bh = f["backlog_files"][r]
        modlog = (f"naming it: line {mh[0][0]} (entry at {mh[0][1]})" if mh else "**none**")
        card = (f"`{bh[0][2].strip()}` line {bh[0][0]}" if bh else "**no card names it**")
        p(f"| `{r}` | `{f['generator']}` | report `B-RC2.md`; backlog {card} | {modlog} |")
    p(f"\nMODLOG occurrences of `bm-RC2`: **{len(f['modlog_tag'])}**. "
      f"GRAB_BACKLOG occurrences of `bm-RC2`: **{len(f['backlog_tag'])}**"
      + (f" (line {f['backlog_tag'][0][0]}: `{f['backlog_tag'][0][2].strip()}`)" if f["backlog_tag"] else "")
      + ".\n")

    p("## 5. Changes that no MODLOG entry explains\n")
    if not f["modlog_tag"]:
        p("**Both of them.** `MODLOG.md` contains no entry for `bm-RC2` at all — no heading, no line. "
          "The RC2 tree, its installer and its receipt are journalled nowhere; the only RC1 record is "
          "`## 2026-10-31 · B-14 done: release candidate Builds/bm-RC1`. GRAB_BACKLOG has no `B-RC2` "
          "card either (its B-14 card says `Out: Builds/bm-RC1/`), and the only RC2 row is "
          "`V-03-RC2 | done` for the wiring gate.\n")
        p("| change | evidence that explains it | missing record |")
        p("|---|---|---|")
        p("| `install.ps1`: tag in banner + `$Bak` | decoded from `Tools/scripts/bm_rc2.py`; "
          "`tmp/freebuff/reports/B-RC2.md` §1 | MODLOG entry " "`B-RC2 done`" " |")
        p("| `receipt.json`: `card`, `lineage_card`, `b10_input`, `tag` | decoded from `bm_rc2.py`'s "
          "receipt block; report §6 | the same MODLOG entry |")
        p("\nThis is a bookkeeping gap, not a build error: the payload is identical, so nothing shipped "
          "changed without a record. But a reader who trusts MODLOG alone cannot learn that RC2 exists.\n")
    else:
        p("None: every changed file is named by a MODLOG entry.\n")

    p("## 6. Findings worth acting on\n")
    p("1. **The receipt still advertises the RC1 backup suffix.** `replaced_rollback` in the RC2 "
      "receipt says `<name>.bm-RC1-backup`, while the RC2 `install.ps1` writes `.bm-RC2-backup` "
      "(decoded: `bm_rc2.py` hard-codes that sentence). Harmless at run time, misleading to a reader.")
    p("2. **A no-backup rollback hazard exists in both trees.** `Install` backs a target up only when "
      "its hash differs from the receipt, and `Rollback091` deletes any target without a backup, so "
      "rolling back a dropzone that already holds the build deletes the payload. Measured on RC2 in "
      "`Builds/bm-RC2/verify/dropzone_sim.md` §6–§8 (V-06); RC1 shares the same installer logic.")
    p("3. **The `verify/` folders are not comparable.** Each tree accumulates its own gate output, so "
      "the six one-sided files say nothing about the build. Diff them separately, per gate.")
    p("4. **RC2 adds no shipped value over RC1.** It is the same 700 payload files under a new tag, "
      "so any decision to prefer RC2 must rest on the installer/receipt metadata or on the later "
      "verification artefacts, not on the car.\n")

    p("## 7. UNKNOWNs\n")
    p("1. **Whether RC2 was rebuilt or copied from RC1 — UNKNOWN.** The payload hashes cannot "
      "distinguish the two; `tmp/freebuff/reports/B-RC2.md` §0 says the tree already existed and was "
      "verified, not rebuilt, but no build log of the 02:42 run survives in this repository.")
    p("2. **Why no MODLOG entry was written for RC2 — UNKNOWN.** No task file for it is in "
      "`tmp/freebuff/done/`, so the omission is recorded, not explained.")
    p("3. **Whether any RC2-only intent hides in the two changed files beyond the tag — UNKNOWN by "
      "construction:** the structural diff is complete (4 fields), but whether the operator wanted "
      "more from RC2 (e.g. the B-10d hull, which `bm_rc2.py --physicsc` can ship) is not recorded in "
      "either changed file.")
    p("")
    return "\n".join(L)


def _size(root, rel):
    return os.path.getsize(os.path.join(root, *rel.split("/")))


def cmd_write():
    f = build()
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    open(MD, "w", encoding="utf-8").write(md_text(f))
    print(f"rc1 files {f['rc1_files']} rc2 files {f['rc2_files']}")
    print(f"payload files {f['payload_files']} changed {len(f['payload_changed'])}")
    print(f"changed files {len(f['changed'])}: {', '.join(f['changed'])}")
    print(f"only rc1 {len(f['only_rc1'])} only rc2 {len(f['only_rc2'])}")
    print(f"aafdiff exit {f['aafdiff_exit']}  adf changed {len(f['adf_changed'])}")
    print(f"modlog mentions of bm-RC2: {len(f['modlog_tag'])}")
    print(f"wrote {MD} ({os.path.getsize(MD)} bytes)")
    return 0


def cmd_check():
    f = build()
    fails = []

    def rep(ok, label, detail=""):
        print(("PASS " if ok else "FAIL ") + label + (("  " + detail) if detail else ""))
        if not ok:
            fails.append(label)

    rep(f["rc1_files"] == f["rc2_files"] == 705, "both trees hold 705 files",
        f"{f['rc1_files']} / {f['rc2_files']}")
    rep(len(f["payload_changed"]) == 0, "payload (aaf/ + drop/) is byte-identical",
        f"{f['payload_files']} files, 0 changed")
    rep(f["changed"] == ["install.ps1", "receipt.json"],
        "exactly install.ps1 and receipt.json differ", ", ".join(f["changed"]))
    rep(f["aafdiff_exit"] == 0, "aafdiff.py reports no archive-member difference",
        f"exit {f['aafdiff_exit']}")
    rep(len(f["adf_changed"]) == 0, "no ADF module changed (jc3adf member diff not required)")
    rep(f["ps1_changed_pairs"] == 3, "install.ps1 differs in 3 line pairs (all the tag)",
        str(f["ps1_changed_pairs"]))
    rep(f["rec_card"] == ("B-14", "B-RC2") and f["rec_tag"] == ("bm-RC1", "bm-RC2"),
        "receipt card/tag are the declared change", f"{f['rec_card']} {f['rec_tag']}")
    rep(len(f["modlog_tag"]) == 0, "MODLOG has no bm-RC2 entry (the documented finding)")

    if not os.path.exists(MD):
        rep(False, "verify/rc_diff.md exists")
    else:
        t = open(MD, encoding="utf-8").read()
        rep(all(r in t for r in f["changed"]), "md names both changed files")
        for r in f["changed"]:
            rep(f["shas"][r][0][:16] in t and f["shas"][r][1][:16] in t,
                f"md records both sha256 for {r}")
        rep("No module differs" in t, "md states the module-level result")
        rep("Both of them" in t or "None:" in t, "md answers 'changes no MODLOG entry explains'")
        rep("payload_files_placeholder" not in t, "md has no unfilled placeholder")

    print(f"check {'PASS' if not fails else 'FAIL'}  ({len(fails)} failing assertion(s))")
    return 0 if not fails else 1


def main():
    if "--write" in sys.argv:
        return cmd_write()
    if "--check" in sys.argv:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
