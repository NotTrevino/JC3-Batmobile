"""t5_build.py - pack an edit-applied aaf tree into a numbered build (T-5).

The module-build sibling of `deploy.py` (which builds appearance/mesh changes and
refuses to move a module). Here the only things that may move are `.vmodc`
modules, so the checks are inverted:

  1. pack       SmallPack the staged aaf -> `<tag>/<ee>`
  2. unpack     SmallUnpack it back and diff against the *base build's own*
                unpacked tree: added/removed must be empty, and every changed
                path must be one of the modules `t5_apply.py` edited
  3. toc        patch the base build's `.toc` from the new `.ee`; a module whose
                re-encoded size changed shifts later records, so the `.toc` is
                rebuilt, not copied
  4. guard      every internal `.toc` record (offset > 0) must equal the `.ee`
                member it names, byte for byte in offset and size
  5. receipt    `receipt.json` + `install.ps1` (Install / Verify / Rollback<base> / Status)

Nothing is written to the game here.

Usage:
  python t5_build.py --aaf Builds/test-084/aaf --base Builds/test-083 --tag test-084
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from eetoc import read_toc, sarc_dir, unaaf  # noqa: E402

GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
GAME = r"D:\Games\Just Cause 3"
DROP = ("dropzone\\editor\\entities\\jc_vehicles\\01_land\\"
        "v0300_car_kensington_sportsmuscle")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sh(*args: str) -> None:
    r = subprocess.run(list(args), capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"{args[0]} failed: {r.stdout[-300:]!r} {r.stderr[-300:]!r}")


def members(ee_path: str) -> dict[str, tuple[int, int]]:
    return {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee_path, "rb").read()))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aaf", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--applied", default=os.path.join(ROOT, "Working", "Translation", "t5_applied.json"))
    a = ap.parse_args()

    tag_dir = os.path.join(ROOT, "Builds", a.tag)
    os.makedirs(tag_dir, exist_ok=True)
    ee = os.path.join(tag_dir, EE)
    base_ee = os.path.join(ROOT, a.base, EE)
    shutil.rmtree(os.path.join(tag_dir, "verify"), ignore_errors=True)

    applied = json.load(open(a.applied, encoding="utf-8"))["applied"]
    edited = {r["file"] for r in applied}
    aaf_abs = os.path.join(ROOT, a.aaf)
    edited_rel = {os.path.relpath(p, aaf_abs).replace("\\", "/").lower() for p in edited}

    print("pack ...")
    sh(os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"),
       os.path.join(ROOT, a.aaf), ee)
    print("unpack ...")
    sh(os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"),
       ee, os.path.join(tag_dir, "verify"))

    # 2. the packed tree may differ from the base only in the edited modules
    r = subprocess.run([sys.executable, os.path.join(HERE, "aafdiff.py"),
                        os.path.join(ROOT, a.base, "verify"), os.path.join(tag_dir, "verify"),
                        "--hash"], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"aafdiff failed: {r.stderr[-400:]}")
    changed = []
    for line in r.stdout.splitlines():
        if not line.startswith("|") or "Bytes A" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4 or set(cells[0]) <= set("-: "):
            continue
        changed.append(cells[3].strip("`"))
    changed_low = {p.lower() for p in changed}
    unexpected = [p for p in changed if p.lower() not in edited_rel]
    missing = [p for p in edited_rel if p not in changed_low]
    if unexpected or missing:
        raise SystemExit(f"diff outside the edit list: extra {unexpected}, missing {missing}")
    print(f"diff: {len(changed)} changed, all in the edit list")

    # 3. rebuild the .toc from the base build's own
    print("toc ...")
    toc = ee + ".toc"
    base_toc = base_ee + ".toc"
    sh(sys.executable, os.path.join(HERE, "eetoc.py"), "patch", ee, base_toc, "--base-ee",
       base_ee, "-o", toc)
    real = members(ee)
    recs = read_toc(open(toc, "rb").read())
    bad = [(n, (o, s), real.get(n)) for n, o, s in recs if o and real.get(n) != (o, s)]
    if bad:
        raise SystemExit(f"{len(bad)} internal .toc record(s) disagree with the .ee: {bad[:3]}")
    base_names = [n for n, _o, _s in read_toc(open(base_toc, "rb").read())]
    if base_names != [n for n, _o, _s in recs]:
        raise SystemExit("the .toc record list changed; a module build must not add or drop files")

    base_rec_path = os.path.join(ROOT, a.base, "receipt.json")
    base_rec = json.load(open(base_rec_path, encoding="utf-8")) if os.path.exists(base_rec_path) else {}

    checks = [
        {"name": "pack/unpack round-trip", "ok": True,
         "detail": f"{len(os.listdir(os.path.join(tag_dir, 'verify')))} top-level entries"},
        {"name": "only edited modules differ", "ok": True, "detail": f"{len(changed)} changed"},
        {"name": "every internal .toc record matches the .ee", "ok": True,
         "detail": f"{sum(1 for _n, o, _s in recs if o)} internal of {len(recs)}"},
        {"name": "toc record list identical to base", "ok": True, "detail": f"{len(recs)} records"},
    ]

    receipt = {
        "tag": a.tag,
        "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "base": a.base,
        "src": a.aaf,
        "ee": {"bytes": os.path.getsize(ee), "sha256": sha256(ee)},
        "toc": {"bytes": os.path.getsize(toc), "sha256": sha256(toc), "records": len(recs),
                "ee_entries": len(real),
                "external_only_in_ee": len(set(real) - {n for n, _o, _s in recs})},
        "replaced": base_rec.get("replaced", {}),
        "textures": base_rec.get("textures", 0),
        "modules_changed": sorted(changed),
        "edits": len(applied),
        "budgets": base_rec.get("budgets", {}),
        "checks": checks,
        "installed": False,
    }
    with open(os.path.join(tag_dir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)

    installer = f"""<#
    {a.tag} installer: T-1 change set ({len(applied)} edits over {len(changed)} modules).
    Close the game first. Rollback{a.base.split('-')[-1]} restores the base build.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback{a.base.split('-')[-1]}','Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$GameDir = '{GAME}'
$EeT = Join-Path $GameDir '{DROP}\\{EE}'
$EeSha = '{receipt["ee"]["sha256"]}'
$TocSha = '{receipt["toc"]["sha256"]}'
$B = '{tag_dir}'
switch ($Action) {{
    'Install' {{
        Copy-Item -LiteralPath (Join-Path $B '{EE}') -Destination $EeT -Force
        Copy-Item -LiteralPath (Join-Path $B '{EE}.toc') -Destination ($EeT + '.toc') -Force
        Write-Host 'deployed {a.tag}: T-1 change set'
    }}
    'Verify' {{
        & python '{os.path.join(ROOT, "Tools", "scripts", "verify_install.py")}' --build $B
    }}
    'Rollback{a.base.split('-')[-1]}' {{
        & (Join-Path '{os.path.join(ROOT, a.base)}' 'install.ps1') -Action Install
    }}
    'Status' {{
        $e = if (Test-Path -LiteralPath $EeT) {{ (Get-FileHash -LiteralPath $EeT).Hash }} else {{ 'none' }}
        $t = if (Test-Path -LiteralPath ($EeT + '.toc')) {{ (Get-FileHash -LiteralPath ($EeT + '.toc')).Hash }} else {{ 'none' }}
        Write-Host "dropzone .ee : $e"
        Write-Host "dropzone .toc: $t"
        if ($e -eq $EeSha -and $t -eq $TocSha) {{ Write-Host '  == {a.tag} (all match)' }}
    }}
}}
"""
    with open(os.path.join(tag_dir, "install.ps1"), "w", encoding="utf-8") as f:
        f.write(installer)

    print(f"{a.tag}: {os.path.getsize(ee)} B .ee, {len(recs)} .toc records, "
          f"{len(changed)} module(s), {len(applied)} edit(s)")


if __name__ == "__main__":
    main()
