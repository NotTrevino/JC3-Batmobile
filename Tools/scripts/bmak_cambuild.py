"""bmak_cambuild.py - pack the CAM-1 candidate into a test .ee/.toc + installer.

**BATCH F (2026-10-23) — un-withdrawn with the decoded composition.** `bmak_camfile.py`
now emits the corrected values (rest camera 7.00 m behind / 1.30 m up, FOV 55 … 63 vertical,
108 km/h interp) and `guard()` fails closed on wrong inputs instead of refusing: the 400/400
cm chase config plus a green `bmak_camdecode.py --check`. The packaging path below is
unchanged; test-091 is the first batch built through it since the probe (test-086) was
withdrawn.

The candidate is two files from `bmak_camfile.py`: a modified `.ctunec` and a donor
`.epe` whose `SharedCarCamera` path now says `bat_base.ctune`.  This tool turns that
pair into a dropzone package derived from a named base build, then proves the
package before anyone copies it into the game.

    python Tools/scripts/bmak_cambuild.py pack --base Builds/test-090 --tag test-091
    python Tools/scripts/bmak_cambuild.py verify --build Builds/test-091

Steps
  1. guard     base .ee/.toc match the hashes in the base installer
  2. candidate rebuild into a temp dir (bmak_camfile.run), never trusting stale output
  3. stage     copy base aaf; replace the .epe; add bat_base.ctunec; register it in @files.xml
  4. pack      SmallPack aaf -> .ee
  5. toc       eetoc patch from the base .toc (the new tune gets a real record before the .epe)
  6. verify    unpack round-trip: only .epe / @files.xml changed, the new tune is present,
               the .epe differs at exactly the 2 ref bytes, every .toc record matches the .ee
  7. receipt   Builds/<tag>/receipt.json + install.ps1 (Install / Verify / Rollback<base> / Status)

Nothing is written to the game here.  `install.ps1 -Action Install` asserts size AND
sha256 before it copies, and refuses a running JustCause3.exe.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bmak_camfile as CAM  # noqa: E402
import eetoc  # noqa: E402

GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
CAM_REL = "editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec"
FILES_XML = "@files.xml"
SIZE = 5968


class Fail(SystemExit):
    pass


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest().upper()


def file_sha(path: str) -> str:
    return sha(open(path, "rb").read())


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise Fail(f"{os.path.basename(cmd[0])} exited {r.returncode}\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r


def walk_hashes(root: str) -> dict[str, str]:
    out = {}
    for d, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = file_sha(p)
    return out


def read_installer_hashes(path: str) -> tuple[str, str]:
    s = open(path, encoding="utf-8-sig").read()
    ee = re.search(r"\$EeSha\s*=\s*'([0-9A-Fa-f]{64})'", s)
    toc = re.search(r"\$TocSha\s*=\s*'([0-9A-Fa-f]{64})'", s)
    if not (ee and toc):
        raise Fail(f"{path}: no pinned EeSha/TocSha")
    return ee.group(1).upper(), toc.group(1).upper()


def toc_summary(ee_path: str, toc_path: str) -> dict:
    # compare exits 1 on a normal baseline difference (external files left in the .ee),
    # so this one reads stdout without treating the exit code as failure.
    r = subprocess.run([sys.executable, os.path.join(HERE, "eetoc.py"), "compare", ee_path, toc_path, "-q"],
                       capture_output=True, text=True)
    m = re.search(r"ee=(\d+)\s+toc=(\d+)\s+only_in_ee=(\d+)\s+only_in_toc=(\d+)\s+offset/size_mismatch=(\d+)",
                  r.stdout)
    if not m:
        raise Fail("eetoc compare produced no summary:\n" + r.stdout[-1000:])
    return dict(zip(("ee", "toc", "only_in_ee", "only_in_toc", "mismatch"), map(int, m.groups())))


def register_candidate(aaf: str) -> str:
    """Add the tune to @files.xml right after car_base.ctunec, preserving CRLF/BOM."""
    p = os.path.join(aaf, *FILES_XML.split("/"))
    raw = open(p, "rb").read()
    text = raw.decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in text else "\n"
    if f'name="{CAM_REL}"' in text:
        raise Fail("@files.xml already lists bat_base.ctunec")
    needle = 'editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec'
    at = text.find(needle)
    if at < 0:
        raise Fail("car_base.ctunec is not in @files.xml")
    end = text.find(eol, at)
    if end < 0:
        raise Fail("@files.xml has no EOL after car_base")
    win = CAM_REL.replace("/", "\\")
    line = f'  <file name="{CAM_REL}">{win}</file>'
    text = text[:end] + eol + line + text[end:]
    out = (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + text.encode("utf-8")
    open(p, "wb").write(out)
    return line


def check_built(out: str, base: str, cam_sha: str, epe_rel: str) -> list[tuple[str, bool, str]]:
    ee = os.path.join(out, EE)
    toc = ee + ".toc"
    verify = os.path.join(out, "verify")
    base_aaf = os.path.join(base, "aaf")
    checks: list[tuple[str, bool, str]] = []

    # ---- unpack round-trip: what the game reads equals what we staged ----------------
    if os.path.isdir(verify):
        shutil.rmtree(verify)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee, verify])
    staged, packed = walk_hashes(os.path.join(out, "aaf")), walk_hashes(verify)
    listed = set()
    xml = open(os.path.join(out, "aaf", FILES_XML), encoding="utf-8-sig").read()
    for m in re.finditer(r'<file name="([^"]+)"(?: size="\d+")?\s*(?:/>|>([^<]*)</file>)', xml):
        if m.group(2):
            listed.add(m.group(1))
    missing = sorted(n for n in listed if n not in packed)
    checks.append(("pack/unpack: every registered file unpacked", not missing,
                   f"{len(packed)} packed, {len(missing)} missing"))

    # SmallPack rewrites @files.xml's size attributes; every payload must survive unchanged.
    changed = sorted(k for k in set(staged) & set(packed)
                     if k != FILES_XML and staged[k] != packed[k])
    checks.append(("pack/unpack: payloads byte-exact", not changed, f"{len(changed)} differ"))

    # ---- exactly the intended tree change vs base -----------------------------------
    base_h = walk_hashes(base_aaf)
    added = sorted(set(packed) - set(base_h))
    removed = sorted(set(base_h) - set(packed))
    diff = sorted(k for k in set(base_h) & set(packed) if base_h[k] != packed[k])
    # base trees carry files @files.xml does not register (front wheels lod4/5); SmallPack
    # never packs those, so they are inert by design, not a packing loss.
    lost = [k for k in removed if k in listed]
    checks.append(("aafdiff: only bat_base.ctunec added", added == [CAM_REL], str(added)))
    checks.append(("aafdiff: nothing registered was lost", not lost, f"{len(lost)} lost, {len(removed)} unlisted"))
    checks.append(("aafdiff: only .epe + @files.xml changed", diff == sorted([epe_rel, FILES_XML]),
                   str(diff)))

    # ---- the two payloads ------------------------------------------------------------
    got_cam = packed.get(CAM_REL)
    checks.append(("bat_base.ctunec is byte-exact", got_cam == cam_sha, (got_cam or "missing")[:16]))
    epe = os.path.join(verify, *epe_rel.split("/"))
    blob = open(epe, "rb").read()
    base_blob = open(os.path.join(base_aaf, *epe_rel.split("/")), "rb").read()
    nbytes = sum(1 for a, b in zip(base_blob, blob) if a != b)
    ref_ok = (blob.count(b"bat_base.ctune") == 1 and blob.count(b"car_base.ctune") == 0)
    checks.append((".epe: 2 ref bytes changed, none else", nbytes == 2 and len(blob) == len(base_blob),
                   f"{nbytes} bytes differ, size {len(blob)}"))
    checks.append((".epe: points at bat_base.ctune once", ref_ok,
                   f"old={blob.count(b'car_base.ctune')} new={blob.count(b'bat_base.ctune')}"))

    # ---- .toc: the new tune must be internal, everything else as in base -------------
    cmp, base_cmp = toc_summary(ee, toc), toc_summary(os.path.join(base, EE),
                                                      os.path.join(base, EE + ".toc"))
    checks.append((".toc: one new record", cmp["toc"] == base_cmp["toc"] + 1,
                   f"{cmp['toc']} vs base {base_cmp['toc']}"))
    checks.append((".toc: external baseline unchanged",
                   (cmp["only_in_toc"], cmp["only_in_ee"], cmp["mismatch"]) ==
                   (0, base_cmp["only_in_ee"], base_cmp["mismatch"]),
                   f"only_in_toc {cmp['only_in_toc']}, only_in_ee {cmp['only_in_ee']}, "
                   f"mismatch {cmp['mismatch']}"))
    recs = {n: (o, s) for n, o, s in eetoc.read_toc(open(toc, "rb").read())}
    real = {n: (o, s) for n, o, s in eetoc.sarc_dir(eetoc.unaaf(open(ee, "rb").read()))}
    checks.append((".toc: bat_base.ctunec internal at its real offset",
                   recs.get(CAM_REL) == real.get(CAM_REL) and recs[CAM_REL][0] > 0,
                   str(recs.get(CAM_REL))))
    # car_base is external in the base .toc (offset 0 = read from the archives); the new
    # record must not change that shared file's routing.
    base_recs = {n: (o, s) for n, o, s in eetoc.read_toc(open(os.path.join(base, EE + ".toc"), "rb").read())}
    car = "editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec"
    checks.append((".toc: car_base.ctunec record unchanged", recs.get(car) == base_recs.get(car),
                   str(recs.get(car))))
    return checks


def installer_text(tag: str, base_tag: str, build_dir: str, ee_sha: str, toc_sha: str,
                   ee_size: int, toc_size: int) -> str:
    return f"""<#
    {tag} installer: CAM-1 per-entity camera tune (bat_base.ctunec + epe ref).
    Close the game first. Rollback{base_tag[5:]} restores {base_tag}.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback{base_tag[5:]}','Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$GameDir = 'D:\\Games\\Just Cause 3'
$EeT = Join-Path $GameDir 'dropzone\\editor\\entities\\jc_vehicles\\01_land\\v0300_car_kensington_sportsmuscle\\{EE}'
$EeSha = '{ee_sha}'
$TocSha = '{toc_sha}'
$EeSize = {ee_size}
$TocSize = {toc_size}
$B = '{build_dir}'
function Test-Artifact {{
    $a = @(
        @{{ P = (Join-Path $B '{EE}'); Size = $EeSize; Sha = $EeSha }},
        @{{ P = (Join-Path $B '{EE}.toc'); Size = $TocSize; Sha = $TocSha }}
    )
    foreach ($x in $a) {{
        if (-not (Test-Path -LiteralPath $x.P)) {{ throw "artifact missing: $($x.P)" }}
        if ((Get-Item -LiteralPath $x.P).Length -ne $x.Size) {{ throw "size mismatch: $($x.P)" }}
        if ((Get-FileHash -LiteralPath $x.P -Algorithm SHA256).Hash -ne $x.Sha) {{ throw "sha256 mismatch: $($x.P)" }}
    }}
}}
switch ($Action) {{
    'Install' {{
        if (Get-Process -Name JustCause3 -ErrorAction SilentlyContinue) {{ throw 'close Just Cause 3 first' }}
        Test-Artifact
        Copy-Item -LiteralPath (Join-Path $B '{EE}') -Destination $EeT -Force
        Copy-Item -LiteralPath (Join-Path $B '{EE}.toc') -Destination ($EeT + '.toc') -Force
        Write-Host 'deployed {tag}: CAM-1 candidate'
    }}
    'Verify' {{
        if (-not (Test-Path -LiteralPath $EeT)) {{ throw 'nothing installed' }}
        $e = (Get-FileHash -LiteralPath $EeT).Hash
        $t = (Get-FileHash -LiteralPath ($EeT + '.toc')).Hash
        if ($e -ne $EeSha -or $t -ne $TocSha) {{ throw 'dropzone differs from {tag}' }}
        & python (Join-Path $B '..\\..\\Tools\\scripts\\bmak_cambuild.py') verify --build $B
    }}
    'Rollback{base_tag[5:]}' {{
        & (Join-Path (Join-Path $B '..\\{base_tag}') 'install.ps1') -Action Install
    }}
    'Status' {{
        $e = if (Test-Path -LiteralPath $EeT) {{ (Get-FileHash -LiteralPath $EeT).Hash }} else {{ 'none' }}
        $t = if (Test-Path -LiteralPath ($EeT + '.toc')) {{ (Get-FileHash -LiteralPath ($EeT + '.toc')).Hash }} else {{ 'none' }}
        Write-Host "dropzone .ee : $e"
        Write-Host "dropzone .toc: $t"
        if ($e -eq $EeSha -and $t -eq $TocSha) {{ Write-Host '  == {tag} (all match)' }}
    }}
}}
"""


def pack(args) -> int:
    base, tag = os.path.abspath(args.base), args.tag
    out = os.path.join(ROOT, "Builds", tag)
    if not os.path.isdir(base):
        raise Fail(f"base build missing: {base}")
    base_ee, base_toc = os.path.join(base, EE), os.path.join(base, EE + ".toc")
    want_ee, want_toc = read_installer_hashes(os.path.join(base, "install.ps1"))
    got = (file_sha(base_ee), file_sha(base_toc))
    if got != (want_ee, want_toc):
        raise Fail(f"base guard failed\n  .ee  want {want_ee} got {got[0]}\n  .toc want {want_toc} got {got[1]}")
    if os.path.exists(out):
        if not args.force:
            raise Fail(f"{out} exists; pass --force to rebuild it")
        shutil.rmtree(out)
    os.makedirs(out)

    tmp = tempfile.mkdtemp(prefix="cambuild_")
    try:
        data = CAM.run(CAM.SRC_CTUNEC, CAM.DONOR_EPE, tmp, None)
        cam_src = data["output"]["ctunec"]
        epe_src = data["epe"]["output"]
        cam_sha = file_sha(cam_src)
        if os.path.getsize(cam_src) != SIZE:
            raise Fail(f"candidate .ctunec is {os.path.getsize(cam_src)} B, expected {SIZE}")

        aaf = os.path.join(out, "aaf")
        shutil.copytree(os.path.join(base, "aaf"), aaf)
        # The candidate is built from the donor tree; what must land in *this* build is
        # its path inside an aaf. Resolving the donor path against the base instead
        # (relpath(donor_epe, base/aaf)) escapes into Builds/<donor>/ whenever
        # base != donor and wrote the patched .epe into test-085 (fixed 2026-10-23).
        donor_norm = CAM.DONOR_EPE.replace("\\", "/")
        if "/aaf/" not in donor_norm:
            raise Fail(f"donor epe is not inside an aaf tree: {CAM.DONOR_EPE}")
        epe_rel = donor_norm.split("/aaf/", 1)[1]
        dst_epe = os.path.join(aaf, *epe_rel.split("/"))
        if not (os.path.abspath(dst_epe) + os.sep).startswith(os.path.abspath(aaf) + os.sep):
            raise Fail(f"stage path escapes the new tree: {dst_epe}")
        if not os.path.exists(dst_epe):
            raise Fail(f"base tree lost {epe_rel}")
        shutil.copyfile(epe_src, dst_epe)
        dst_cam = os.path.join(aaf, *CAM_REL.split("/"))
        os.makedirs(os.path.dirname(dst_cam), exist_ok=True)
        shutil.copyfile(cam_src, dst_cam)
        xml_line = register_candidate(aaf)

        ee = os.path.join(out, EE)
        run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee])
        run([sys.executable, os.path.join(HERE, "eetoc.py"), "patch", ee, base_toc,
             "--base-ee", base_ee, "-o", ee + ".toc"])

        checks = check_built(out, base, cam_sha, epe_rel)
        for name, ok, detail in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {name:50} {detail}")
        bad = [c for c in checks if not c[1]]
        if bad:
            raise Fail(f"{len(bad)} verification(s) failed")

        ee_h, toc_h = file_sha(ee), file_sha(ee + ".toc")
        receipt = {
            "tag": tag,
            "built": datetime.datetime.now().isoformat(timespec="seconds"),
            "base": os.path.relpath(base, ROOT).replace(os.sep, "/"),
            "src": f"Builds/{tag}/aaf",
            "ee": {"bytes": os.path.getsize(ee), "sha256": ee_h},
            "toc": {"bytes": os.path.getsize(ee + ".toc"), "sha256": toc_h},
            "candidate": {
                "ctunec": CAM_REL, "ctunec_bytes": SIZE, "ctunec_sha256": cam_sha,
                "epe": epe_rel, "epe_ref": "car_base.ctune -> bat_base.ctune",
                "edits": [{"member": e["member"], "index": e["index"], "row": e["row"],
                           "old": e["old"], "new": e["new"]} for e in CAM.EDITS],
            },
            "files_xml_added": xml_line.strip(),
            "checks": [{"name": n, "ok": k, "detail": d} for n, k, d in checks],
        }
        json.dump(receipt, open(os.path.join(out, "receipt.json"), "w"), indent=1)
        open(os.path.join(out, "install.ps1"), "w", newline="\r\n").write(
            installer_text(tag, os.path.basename(base), out, ee_h, toc_h,
                           os.path.getsize(ee), os.path.getsize(ee + ".toc")))
        print(f"ee:  {ee}  {os.path.getsize(ee)} B  {ee_h[:16]}")
        print(f"toc: {ee}.toc  {os.path.getsize(ee + '.toc')} B  {toc_h[:16]}")
        print(f"installer: {os.path.join(out, 'install.ps1')}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


def verify(args) -> int:
    out = os.path.abspath(args.build)
    receipt = json.load(open(os.path.join(out, "receipt.json")))
    base = os.path.join(ROOT, receipt["base"])
    ee = os.path.join(out, EE)
    checks = [(f"{EE} hash", file_sha(ee) == receipt["ee"]["sha256"], file_sha(ee)[:16]),
              (f"{EE}.toc hash", file_sha(ee + ".toc") == receipt["toc"]["sha256"],
               file_sha(ee + ".toc")[:16])]
    epe_rel = receipt["candidate"]["epe"]
    checks += check_built(out, base, receipt["candidate"]["ctunec_sha256"], epe_rel)
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:50} {detail}")
    bad = [c for c in checks if not c[1]]
    if bad:
        raise Fail(f"{len(bad)} verification(s) failed")
    print(f"{receipt['tag']}: {len(checks)}/{len(checks)} checks pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack", help="build Builds/<tag> from a base build")
    p.add_argument("--base", default=os.path.join(ROOT, "Builds", "test-085"))
    p.add_argument("--tag", default="test-086")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("verify", help="re-run every check on a built tag")
    p.add_argument("--build", required=True)
    a = ap.parse_args()
    return pack(a) if a.cmd == "pack" else verify(a)


if __name__ == "__main__":
    raise SystemExit(main())
