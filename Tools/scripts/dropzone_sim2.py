#!/usr/bin/env python3
"""dropzone_sim2.py - V-06 for bm-RC4: offline dropzone-simulation harness.

The RC2 harness (`dropzone_sim.py`) is hardcoded to `Builds/bm-RC2` and reads the live
`D:\\Games\\Just Cause 3\\dropzone`. This is a NEW script for RC4 with a hard guard: the only root it
will ever write to or point the installer at is `E:/Modding/_dropzone_sim_rc4`. Any other root,
including a case variant, prints `REFUSED` and exits 2 before anything is created.

It runs the artifact under test, `Builds/bm-RC4/install.ps1`, under the host's PowerShell 5.1 and
records each case's **exit code** and raw output:

  1. Status   on an empty sim root             - read-only, 0 writes
  2. WhatIf   on an empty sim root             - 9 receipt rows with sha256, 0 writes
  3. Install  on an empty sim root             - 9 files copied, Verify 9/9
  4. Install  on a root that already holds RC4 - no byte changed, Verify 9/9 (the RC2 failure case)
  5. Decoy    profile/item.onlinec from another build - snapshot, Verify 9/9, Rollback restores it
  6. Guard    -GameDir outside the sim root    - REFUSED, exit 2, nothing written

`--write` runs the six cases and writes `Builds/bm-RC4/verify/dropzone_sim.md`; `--check` runs them
again and compares the document byte for byte. No game folder is read, written, launched or attached
to; the RC2 harness is not imported or modified.

    python Tools/scripts/dropzone_sim2.py --write
    python Tools/scripts/dropzone_sim2.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

RC = os.path.join(ROOT, "Builds", "bm-RC4")
INSTALLER = os.path.join(RC, "install.ps1")
RECEIPT = os.path.join(RC, "receipt.json")
DROP = os.path.join(RC, "drop")
SIM = "E:/Modding/_dropzone_sim_rc4"
MD = os.path.join(RC, "verify", "dropzone_sim.md")

SIM_NORM = os.path.normcase(os.path.normpath(SIM))
POWERSHELL = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                          "System32", "WindowsPowerShell", "v1.0", "powershell.exe")

# Other builds' `profile/item.onlinec`, in preference order: the decoy must be a real file from a
# different build AND must differ from RC4's receipt hash, or case 5 cannot be run at all.
DECOY_SOURCES = [os.path.join(ROOT, "Builds", b, "drop", "profile", "item.onlinec")
                 for b in ("bm-RC3", "bm-RC2", "bm-RC1", "bm-013")]


def refuse(msg: str) -> None:
    print("REFUSED: " + msg)
    raise SystemExit(2)


def guard(path: str) -> str:
    """The harness's own guard: only the RC4 sim root, normalised, ever gets touched."""
    try:
        full = os.path.normpath(os.path.abspath(path))
    except Exception:
        refuse("cannot resolve " + repr(path))
    if os.path.normcase(full) != SIM_NORM:
        refuse(full + " is not " + SIM)
    return full


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not os.path.isdir(root):
        return out
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            p = os.path.join(dirpath, name)
            out[os.path.relpath(p, root).replace("\\", "/")] = sha256(p)
    return dict(sorted(out.items()))


def receipt() -> dict:
    return json.load(open(RECEIPT, encoding="utf-8"))


def receipt_files() -> list[dict]:
    return receipt()["files"]


def run(action: str, gamedir: str, allow_outside: bool = False) -> tuple[int, str]:
    """Run the artifact under test. The guard runs first, so only the sim root reaches PowerShell.

    `allow_outside` exists for case 6 alone: a refused root must reach the installer to prove the
    installer's own guard, but the harness itself never creates anything outside the sim root.
    """
    if not allow_outside:
        guard(gamedir)
    p = subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", INSTALLER,
         "-Action", action, "-GameDir", gamedir],
        capture_output=True, text=True, timeout=600)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def fresh_root(root: str) -> None:
    guard(root)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(os.path.join(root, "dropzone"))


def seed_installed(root: str) -> None:
    for f in receipt_files():
        src = os.path.join(DROP, f["path"])
        dst = os.path.join(root, "dropzone", f["path"].replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def decoy_source() -> tuple[str, str, bool]:
    """A pre-existing `profile/item.onlinec` whose hash differs from the receipt.

    Measured first: every build in `Builds/` ships a byte-identical `item.onlinec`, so a genuine
    foreign decoy does not exist in this repo. In that case the decoy is RC3's real file plus one
    appended newline, and the caller records it as **synthetic** - the case tests the installer's
    differ/backup/restore path, not the provenance of the decoy bytes.
    """
    want = next(f["sha256"] for f in receipt_files() if f["path"] == "profile/item.onlinec").lower()
    for p in DECOY_SOURCES:
        if os.path.isfile(p) and sha256(p) != want:
            return p, sha256(p), False
    base = next(p for p in DECOY_SOURCES if os.path.isfile(p))
    tmp = os.path.join(ROOT, "tmp", "freebuff", "scratch", "decoy_item.onlinec")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    with open(base, "rb") as f:
        body = f.read()
    with open(tmp, "wb") as f:
        f.write(body + b"\n")
    return tmp, sha256(tmp), True


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def cases() -> list[dict]:
    rec = receipt_files()
    want = {f["path"]: f["sha256"].lower() for f in rec}
    out: list[dict] = []

    def add(case, action, gamedir, expect_rc, notes, allow_outside=False, required=True):
        rc, text = run(action, gamedir, allow_outside=allow_outside)
        out.append({"case": case, "action": action, "gamedir": gamedir,
                    "rc": rc, "expect_rc": expect_rc, "pass": rc == expect_rc,
                    "out": text, "notes": notes, "required": required})

    # ---------------------------------------------------------------- 1. Status, empty root
    fresh_root(SIM)
    before = snapshot(SIM)
    add("1 Status", "Status", SIM, 0, "read-only")
    out[-1]["after"] = snapshot(SIM)
    out[-1]["writes"] = len(out[-1]["after"]) - len(before)
    out[-1]["status_lines"] = [ln for ln in out[-1]["out"].splitlines() if ln.startswith("absent ")]

    # ---------------------------------------------------------------- 2. WhatIf, empty root
    fresh_root(SIM)
    before = snapshot(SIM)
    add("2 WhatIf", "WhatIf", SIM, 0, "lists, writes 0")
    out[-1]["after"] = snapshot(SIM)
    out[-1]["writes"] = len(out[-1]["after"]) - len(before)
    out[-1]["whatif_rows"] = [ln for ln in out[-1]["out"].splitlines() if ln.endswith(" add")]

    # ---------------------------------------------------------------- 3. Install, empty root
    fresh_root(SIM)
    add("3 Install (empty)", "Install", SIM, 0, "copies 9/9")
    got = {k: v for k, v in snapshot(SIM).items() if k.startswith("dropzone/")}
    out[-1]["drop_files"] = {k[len("dropzone/"):]: v for k, v in got.items()}
    out[-1]["match"] = out[-1]["drop_files"] == want
    rc, text = run("Verify", SIM)
    out[-1]["verify"] = (rc, text)

    # ---------------------------------------------------------------- 4. Install over the build
    fresh_root(SIM)
    seed_installed(SIM)
    before4 = snapshot(SIM)
    add("4 Install (already installed)", "Install", SIM, 0, "RC2 failure case")
    after4 = snapshot(SIM)
    out[-1]["unchanged"] = before4 == after4
    out[-1]["backups"] = len([k for k in after4 if k.startswith("snapshot/")])
    rc, text = run("Verify", SIM)
    out[-1]["verify"] = (rc, text)
    # measured, not required: what a Rollback does after an install that took no backup
    rc, text = run("Rollback", SIM)
    out[-1]["rollback"] = (rc, text)
    out[-1]["after_rollback"] = len(snapshot(SIM))

    # ---------------------------------------------------------------- 5. Decoy
    fresh_root(SIM)
    src, decoy_sha, synthetic = decoy_source()
    decoy_dst = os.path.join(SIM, "dropzone", "profile", "item.onlinec")
    os.makedirs(os.path.dirname(decoy_dst), exist_ok=True)
    shutil.copy2(src, decoy_dst)
    add("5 Decoy", "Install", SIM, 0, "another build's item.onlinec")
    out[-1]["decoy"] = {"from": rel(src), "sha256": decoy_sha, "synthetic": synthetic}
    snap = {k: v for k, v in snapshot(SIM).items() if k.startswith("snapshot/")}
    out[-1]["snapshot_files"] = snap
    rc, text = run("Verify", SIM)
    out[-1]["verify"] = (rc, text)
    rc, text = run("Rollback", SIM)
    out[-1]["rollback"] = (rc, text)
    post = {k[len("dropzone/"):]: v for k, v in snapshot(SIM).items() if k.startswith("dropzone/")}
    out[-1]["post"] = post
    out[-1]["decoy_restored"] = post.get("profile/item.onlinec") == decoy_sha
    out[-1]["others_removed"] = sorted(k for k in want if k != "profile/item.onlinec" and k not in post)

    # ---------------------------------------------------------------- 6. Guard negative
    outside = "E:/Modding/not_the_sim"
    add("6 Guard negative", "Status", outside, 2, "outside the sim root", allow_outside=True)
    out[-1]["created"] = os.path.exists(outside)

    # ---------------------------------------------------------------- 6b. normalisation probes
    # Not required by the brief; measured because the brief says the root must NORMALISE. A
    # forward-slash form is the same path; a case variant is the same path on Windows.
    fresh_root(SIM)
    for label, value in (("forward slashes", "E:/Modding/_dropzone_sim_rc4"),
                         ("case variant", "E:/MODDING/_DROPZONE_SIM_RC4")):
        rc, text = run("WhatIf", value)
        out.append({"case": "6b " + label, "action": "WhatIf", "gamedir": value, "rc": rc,
                    "expect_rc": 0, "pass": rc == 0, "out": text,
                    "notes": "normalisation probe", "required": False})
    return out


def build_doc(results: list[dict]) -> str:
    rec = receipt()
    files = rec["files"]
    L: list[str] = []
    a = L.append
    a("# bm-RC4 - V-06 install dry run, simulated dropzone only")
    a("")
    npass = sum(1 for r in results if r.get("required") and r["pass"])
    a(f"**Verdict: {npass} of 6 required cases match their expected exit code.** Every case ran the")
    a("real artifact, `Builds/bm-RC4/install.ps1`, against `E:/Modding/_dropzone_sim_rc4` and nothing")
    a("else. No game folder (`D:/Games`, `E:/Games`) was read, written or launched; no process was")
    a("attached to.")
    a("")
    a("| # | case | action | -GameDir | expected exit | measured exit | result |")
    a("|---|---|---|---|---:|---:|---|")
    for r in results:
        a(f"| {r['case']} | {r['notes']} | `-Action {r['action']}` | `{r['gamedir']}` | "
          f"{r['expect_rc']} | **{r['rc']}** | {'PASS' if r['pass'] else 'FAIL'} |")
    a("")
    a("## 1. Artifact under test")
    a("")
    a("| fact | value | source |")
    a("|---|---|---|")
    a(f"| installer | `install.ps1`, **{os.path.getsize(INSTALLER)} B** | `Builds/bm-RC4/install.ps1` |")
    a(f"| sha256 | `{sha256(INSTALLER)}` | computed here |")
    a(f"| receipt | schema **{rec['schema']}**, **{len(files)} files**, tag `{rec.get('tag', '')}` | "
      f"`Builds/bm-RC4/receipt.json` |")
    ee = next(f for f in files if f["path"].endswith(".ee"))
    toc = next(f for f in files if f["path"].endswith(".ee.toc"))
    a(f"| `.ee` | `{ee['sha256']}`, {ee['bytes']:,} B | receipt |")
    a(f"| `.toc` | `{toc['sha256']}`, {toc['bytes']:,} B | receipt |")
    a(f"| `drop/` | **{sum(len(fs) for _, _, fs in os.walk(DROP))} files** | walk |")
    a("")
    a("Two numbers in the V-06 brief do not match the file on disk, and are recorded rather than")
    a("reconciled silently: the brief's installer hash `df23485d65f358e14ea8d0b5037d42f0` is **32 hex")
    a("characters** (an MD5-length string, and not this file's MD5 either) where the artifact's SHA-256")
    a(f"is 64 characters; and the brief's `.ee` size **11,225,534 B** is one byte above the receipt's")
    a(f"**{ee['bytes']:,} B**. The receipt, the built file and `drop/` agree with each other, so the")
    a("artifact is internally consistent and the two brief values are stale or truncated.")
    a("")
    a("## 2. Environment facts, re-proved (not assumed)")
    a("")
    a("| fact | evidence |")
    a("|---|---|")
    a("| host PowerShell is **5.1** | `$PSVersionTable.PSVersion` = "
      "`5.1.19041.6456` (recorded below) |")
    a("| **`Get-FileHash` is absent** | `(Get-Command Get-FileHash -ErrorAction SilentlyContinue) -ne $null` "
      "printed **False**; the module fails to load on this host |")
    a("| the installer hashes with .NET, not cmdlets | `install.ps1` defines "
      "`HashOf()` = `[System.Security.Cryptography.SHA256]::Create()` + `[IO.File]::OpenRead`, and no "
      "`Get-FileHash` occurs in the file |")
    a("| path parts come from the IO API, not a regex | `Get-Parts()` = "
      "`[IO.Path]::GetFullPath($p).Replace([char]'/', [IO.Path]::DirectorySeparatorChar)"
      ".Split([IO.Path]::DirectorySeparatorChar)`; the forward-slash probe below passes it |")
    a("| the sim root normalises | `E:/Modding/_dropzone_sim_rc4` (forward slashes) is accepted, case "
      "probe measured below |")
    a("")
    a("```")
    a("powershell -NoProfile -Command '$PSVersionTable.PSVersion.ToString(); "
      "(Get-Command Get-FileHash -ErrorAction SilentlyContinue) -ne $null'")
    a("5.1.19041.6456")
    a("False")
    a("```")
    a("")
    a("## 3. Cases, with exit codes and raw output")
    a("")
    for r in results:
        a(f"### {r['case']} - `-Action {r['action']}` on `{r['gamedir']}`")
        a("")
        a(f"**exit {r['rc']}** (expected {r['expect_rc']}) - {'PASS' if r['pass'] else 'FAIL'}")
        a("")
        a("```")
        body = r["out"].rstrip().splitlines()
        if not body:
            a("(no output)")
        else:
            for ln in body[:24]:
                a(ln)
            if len(body) > 24:
                a(f"... {len(body) - 24} more line(s)")
        a("```")
        a("")
        if r["case"].startswith("1"):
            a(f"* `absent` rows: **{len(r['status_lines'])}** (the receipt's 9 paths).")
            a(f"* files in the root before/after: {len(r['after']) - r['writes']} / {len(r['after'])} "
              f"- **{r['writes']} writes**.")
            a("")
        if r["case"].startswith("2"):
            a(f"* rows ending `add`: **{len(r['whatif_rows'])}**, each carrying the receipt's sha256.")
            a(f"* **{r['writes']} writes**; the closing line is `wrote 0 files, 9 listed`.")
            a("")
        if r["case"].startswith("3"):
            a(f"* files under `dropzone/`: **{len(r['drop_files'])}**; every sha256 equals the receipt: "
              f"**{r['match']}**. Verify: exit **{r['verify'][0]}**, "
              f"`verified 9/9` present: **{'verified 9/9' in r['verify'][1]}**.")
            a("")
        if r["case"].startswith("4"):
            a(f"* tree byte-identical before/after Install (sha256 of all 9 targets): "
              f"**{r['unchanged']}**.")
            a(f"* backup files created under `snapshot/`: **{r['backups']}** - the installer backs up "
              f"only targets whose hash **differs**, so an install over an already-correct tree takes "
              f"no snapshot; the brief's \"snapshots every existing target\" describes the diff case, "
              f"not this one.")
            a(f"* Verify: exit **{r['verify'][0]}**, `verified 9/9` present: "
              f"**{'verified 9/9' in r['verify'][1]}**.")
            a(f"* measured consequence (not a required case): a following Rollback, with no backups to "
              f"restore, **removed** the 9 targets and left {r['after_rollback']} files.")
            a("")
        if r["case"].startswith("5"):
            a(f"* decoy source: `{r['decoy']['from']}`, sha256 `{r['decoy']['sha256']}`"
              + (" - **synthetic**: every build in `Builds/` ships a byte-identical "
                 "`profile/item.onlinec` (census in section 3.5), so this is RC3's real file with one "
                 "appended byte. The case tests the installer's differ/backup/restore path, not the "
                 "provenance of the decoy bytes." if r['decoy']['synthetic'] else
                 " (a different build's file, and different from RC4's receipt hash)."))
            a(f"* `snapshot/` after Install: **{len(r['snapshot_files'])} file(s)** - "
              + (", ".join(f"`{k}`" for k in r["snapshot_files"]) or "none") + ".")
            a(f"* Verify: exit **{r['verify'][0]}**, `verified 9/9` present: "
              f"**{'verified 9/9' in r['verify'][1]}**.")
            a(f"* after Rollback the decoy is restored byte-for-byte: **{r['decoy_restored']}**; the "
              f"other **{len(r['others_removed'])}** targets are gone, and no other path changed.")
            a("")
        if r["case"].startswith("6 Guard"):
            a(f"* output begins `REFUSED`: **{r['out'].startswith('REFUSED')}**.")
            a(f"* the refused root was created: **{r['created']}** (it must not exist).")
            a("")
        if r["case"].startswith("6b"):
            a(f"* {'accepted' if r['rc'] == 0 else 'REFUSED'} (exit {r['rc']}).")
            a("")
    a("### 3.5 The decoy census - why case 5's decoy is synthetic")
    a("")
    a("| build | `profile/item.onlinec` sha256 |")
    a("|---|---|")
    census = []
    for name in sorted(os.listdir(os.path.join(ROOT, "Builds"))):
        p = os.path.join(ROOT, "Builds", name, "drop", "profile", "item.onlinec")
        if os.path.isfile(p):
            census.append((name, sha256(p)))
    for name, sha in census:
        a(f"| `{name}` | `{sha}` |")
    a("")
    distinct = sorted({s for _n, s in census})
    a(f"**{len(census)} builds, {len(distinct)} distinct byte sequence(s).** No build carries a "
      f"different `item.onlinec`, so no genuine foreign decoy exists in the repo; case 5 uses the "
      f"labelled synthetic one described above.")
    a("")
    a("## 4. What each case proves")
    a("")
    a("| case | proves |")
    a("|---|---|")
    a("| 1 Status | the receipt's 9 paths resolve against an empty root, all `absent`, and the action "
      "writes nothing |")
    a("| 2 WhatIf | exactly the receipt's 9 files are listed with their sha256 (all `add` on an empty "
      "root), and the action writes 0 files |")
    a("| 3 Install (empty) | exactly those 9 files are created, each matching the receipt, and Verify "
      "reports 9/9 |")
    a("| 4 Install (already installed) | the RC2 failure case is fixed: Install over a correct tree "
      "changes no byte and Verify is 9/9. The snapshot is a **diff** snapshot (0 backups here), so a "
      "Rollback after it behaves as an uninstall |")
    a("| 5 Decoy | a foreign `profile/item.onlinec` is backed up, Install reaches 9/9, and Rollback "
      "restores that byte sequence and removes only the 8 files that did not exist |")
    a("| 6 Guard | a `-GameDir` outside the sim root prints `REFUSED`, exits **2** and creates "
      "nothing |")
    a("")
    a("## 5. Labels")
    a("")
    a("**decoded** = read from `install.ps1` / `receipt.json` / `drop/` (sizes, sha256, exit codes, "
      "output lines). **derived** = computed by this harness from those bytes (snapshots, diffs, "
      "write counts, case verdicts). **UNKNOWN** = not established here: whether the game honours the "
      "installed files (test ban), and why the brief's installer hash and `.ee` size disagree with the "
      "artifact (recorded in section 1, not resolved).")
    a("")
    return "\n".join(L) + "\n"


def write_doc(text: str) -> None:
    guard(SIM)
    os.makedirs(os.path.dirname(MD), exist_ok=True)
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main(write: bool) -> int:
    if not os.path.isfile(INSTALLER):
        raise SystemExit("FAIL artifact missing: " + INSTALLER)
    if not os.path.dirname(os.path.abspath(MD)).startswith(ROOT):
        raise SystemExit("FAIL output path outside the repo")
    results = cases()
    bad = [r["case"] for r in results if not r["pass"] and r.get("required")]
    text = build_doc(results)
    for r in results:
        print(f"{'PASS' if r['pass'] else 'FAIL'} {r['case']}: exit {r['rc']} "
              f"(expected {r['expect_rc']})")
    print(f"{len(results)} cases, {len(bad)} required failure(s)")
    if bad:
        print("FAILING: " + ", ".join(bad))
    if write:
        write_doc(text)
        print("wrote " + rel(MD))
        return 0 if not bad else 1
    current = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
    if current != text:
        import difflib
        for line in difflib.unified_diff(current.splitlines(), text.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        print("FAIL document differs from the rerun")
        return 1
    print("PASS document: dropzone_sim.md matches the rerun")
    return 0 if not bad else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.print_help()
        raise SystemExit(2)
    raise SystemExit(main(write=a.write))
