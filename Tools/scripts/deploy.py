"""deploy.py - the ONE deploy path: guard -> stage -> pack -> patch .toc -> verify -> receipt.

Replaces ad-hoc `_build_*.ps1` copies. Every build is derived from a named base build whose
artifacts are hash-pinned by that build's own installer, so a tree that has drifted (or a
dropzone that holds something else) stops the build instead of silently producing a mixed car.

    python Tools/scripts/deploy.py build --base Builds/test-077 \\
        --src Working/Appearance/build --tag test-078

Steps and checks
  1. guard      base .ee/.toc match the hashes embedded in the base installer; the live dropzone
                (if present) matches the base too, unless --allow-live-drift
  2. stage      copy base aaf, replace the 25 mesh files, add the converted textures to the tree
                AND to @files.xml (SmallPack drops unregistered files)
  3. pack       SmallPack aaf -> .ee
  4. patch      eetoc patch from the vanilla .toc, same --internal set as the base build
  5. verify     aafdiff vs base (only meshes/textures/@files.xml may change; no module may move),
                every RBM re-encodes byte-identically, block counts, texture refs resolve, every
                texture is listed in the .toc at a real offset, model + texture budgets
  6. receipt    Builds/<tag>/receipt.json + install.ps1 (Install / Verify / Rollback<base> / Status)
                `-Action Verify` runs verify_install.py: the installed pair is read through its .toc
                and every replaced mesh/texture is compared with the staged aaf copy

Nothing is written to the game here; the installer does that and needs explicit human action.
"""
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import rbm_geom as R  # noqa: E402

GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
VEH_DIR = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
BUDGET_XML = os.path.join(ROOT, "Research", "Budgets", "vanilla_budgets.xml")
VANILLA_TOC = os.path.join(ROOT, "Research", "SerpenteToc", "vanilla_civilian_01.ee.toc")
BASE_EE = os.path.join(ROOT, "Builds", "test-003", EE)
# same set test-077 internalised relative to the vanilla .toc (MODLOG 097)
INTERNAL = ["sportsmuscle_civilian_01.epe", "sportsmuscle_land_global.vmodc",
            "sportsmuscle_land_engine.vmodc", "sportsmuscle_transmission.vmodc",
            "sportsmuscle_vehicle_misc.vmodc", "sportsmuscle_custom_land_global.vmodc",
            "sportsmuscle_land_aerodynamics.vmodc", "sportsmuscle_land_steering.vmodc",
            "sportsmuscle_suspension.vmodc"]
WHEEL_RE = re.compile(r"^sportsmuscle_wheel_([fr]_[lr])(mshswap)?_lod(\d)\.rbm$")
BODY_RE = re.compile(r"^sportsmuscle_body_lod(\d)\.rbm$")


class Fail(SystemExit):
    pass


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()


def walk_hashes(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = sha(p)
    return out


def read_installer_hashes(ps1):
    s = open(ps1, encoding="utf-8-sig", errors="replace").read()
    ee = re.search(r"\$EeSha\s*=\s*'([0-9A-Fa-f]{64})'", s)
    toc = re.search(r"\$TocSha\s*=\s*'([0-9A-Fa-f]{64})'", s)
    if not (ee and toc):
        raise Fail(f"{ps1}: no $EeSha/$TocSha pins found - base build is not hash-pinned")
    return ee.group(1).upper(), toc.group(1).upper()


def toc_records(path):
    d = open(path, "rb").read()
    o, rows = 0, {}
    while o < len(d):
        n = struct.unpack_from("<I", d, o)[0]
        o += 4
        name = d[o:o + n].decode("latin1")
        o += n
        off, size = struct.unpack_from("<II", d, o)
        o += 8
        rows[name] = (off, size)
    return rows


def winpath(p):
    return os.path.abspath(p).replace("/", "\\")


def add_to_manifest(aaf, vfs_names):
    """SmallPack packs only what @files.xml lists: register each new texture (internal)."""
    p = os.path.join(aaf, "@files.xml")
    xml = open(p, encoding="utf-8-sig").read()
    added = 0
    for vfs in vfs_names:
        if f'name="{vfs}"' in xml:
            continue
        win = vfs.replace("/", "\\")
        line = f'  <file name="{vfs}">{win}</file>\r\n'
        xml = xml.replace("</files>", line + "</files>")
        added += 1
    open(p, "w", encoding="utf-8-sig", newline="").write(xml)
    return added


def run(cmd, check=True, **kw):
    r = subprocess.run(cmd, cwd=kw.pop("cwd", ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    if check and r.returncode != 0:
        raise Fail(f"{' '.join(cmd)} failed ({r.returncode})\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r


def toc_summary(ee, toc):
    """eetoc compare's counts. A vanilla-path override keeps ~98 files in the .ee that the
    .toc deliberately reads from the archives (offset 0) - that is the normal baseline, so the
    numbers are compared against the BASE build rather than against zero."""
    r = run([sys.executable, os.path.join(ROOT, "Tools", "scripts", "eetoc.py"), "compare",
             ee, toc, "-q"], check=False)
    m = re.search(r"ee=(\d+)\s+toc=(\d+)\s+only_in_ee=(\d+)\s+only_in_toc=(\d+)\s+offset/size_mismatch=(\d+)",
                  r.stdout or "")
    if not m:
        raise Fail("eetoc compare produced no summary:\n" + (r.stdout or "")[-1000:] + (r.stderr or "")[-1000:])
    return {k: int(v) for k, v in zip(("ee", "toc", "only_in_ee", "only_in_toc", "mismatch"), m.groups())}


def build(a):
    base = os.path.join(ROOT, a.base)
    src = os.path.join(ROOT, a.src)
    out = os.path.join(ROOT, "Builds", a.tag)
    for p, what in ((base, "--base"), (src, "--src")):
        if not os.path.isdir(p):
            raise Fail(f"{what} {p} does not exist")

    # ---- 1. guard ----------------------------------------------------------------
    base_ee = os.path.join(base, EE)
    base_toc = base_ee + ".toc"
    want_ee, want_toc = read_installer_hashes(os.path.join(base, "install.ps1"))
    got_ee, got_toc = sha(base_ee), sha(base_toc)
    if (got_ee, got_toc) != (want_ee, want_toc):
        raise Fail(f"BASE DRIFT: {a.base} does not match its own installer pins\n"
                   f"  .ee  want {want_ee} got {got_ee}\n  .toc want {want_toc} got {got_toc}")
    live = os.path.join(a.game, "dropzone", "editor", "entities", "jc_vehicles", "01_land",
                        "v0300_car_kensington_sportsmuscle", EE)
    if os.path.exists(live):
        live_ee, live_toc = sha(live), sha(live + ".toc")
        if (live_ee, live_toc) != (want_ee, want_toc):
            msg = (f"LIVE DROPZONE DRIFT: the game holds something other than {a.base}\n"
                   f"  .ee  want {want_ee} got {live_ee}\n  .toc want {want_toc} got {live_toc}")
            if not a.allow_live_drift:
                raise Fail(msg + "\n  (rerun with --allow-live-drift to build anyway; it is recorded)")
            print("WARNING:", msg)
        else:
            print(f"guard: live dropzone == {a.base}")
    else:
        print("guard: no live dropzone file (clean install)")

    # ---- 2. stage ----------------------------------------------------------------
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    aaf = os.path.join(out, "aaf")
    shutil.copytree(os.path.join(base, "aaf"), aaf)
    mdir = os.path.join(aaf, *VEH_DIR.split("/"))

    replaced = {"body": 0, "wheel": 0}
    for i in range(1, 6):
        s = os.path.join(src, f"body_lod{i}.rbm")
        d = os.path.join(mdir, f"sportsmuscle_body_lod{i}.rbm")
        if not (os.path.exists(s) and os.path.exists(d)):
            raise Fail(f"body lod{i}: missing {s if not os.path.exists(s) else d}")
        shutil.copyfile(s, d)
        replaced["body"] += 1
    for name in sorted(os.listdir(mdir)):
        m = WHEEL_RE.match(name)
        if not m:
            continue
        corner, lod = m.group(1), int(m.group(3))
        s = os.path.join(src, f"wheel_{corner}_lod{lod}.rbm")
        if not os.path.exists(s):
            raise Fail(f"wheel source missing for {name}: {s}")
        shutil.copyfile(s, os.path.join(mdir, name))
        replaced["wheel"] += 1
    if replaced != {"body": 5, "wheel": 34}:      # 20 wheel RBMs + 14 mshswap RBMs
        raise Fail(f"expected 5 body + 34 wheel files, got {replaced}")

    asm = json.load(open(os.path.join(src, "assembly.json")))
    tex = asm["textures"]
    for vfs, local in tex.items():
        local = local if os.path.isabs(local) else os.path.join(ROOT, local)
        if not os.path.exists(local):
            raise Fail(f"texture {vfs}: {local} does not exist")
        dst = os.path.join(aaf, *vfs.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(local, dst)
    listed = add_to_manifest(aaf, list(tex))
    overlays = {}
    for spec in a.overlay:
        vfs, sep, local = spec.partition("=")
        if not sep or not os.path.exists(local):
            raise Fail(f"--overlay {spec!r}: expected VFS_PATH=EXISTING_FILE")
        dst = os.path.join(aaf, *vfs.split("/"))
        if not os.path.exists(dst):
            raise Fail(f"--overlay {vfs}: not a file in the base tree")
        shutil.copyfile(local, dst)
        overlays[vfs] = local
    print(f"stage: body {replaced['body']}, wheels {replaced['wheel']}, textures {len(tex)} "
          f"({listed} newly registered in @files.xml)" + (f", overlays {len(overlays)}" if overlays else ""))

    # ---- 3. pack -----------------------------------------------------------------
    ee_out = os.path.join(out, EE)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallPack.exe"), aaf, ee_out])
    if not os.path.exists(ee_out) or os.path.getsize(ee_out) == 0:
        raise Fail("SmallPack produced nothing")

    # ---- 4. .toc ------------------------------------------------------------------
    # unpack round-trip: what the game will read must equal what we staged
    verify_dir = os.path.join(out, "verify")
    if os.path.isdir(verify_dir):
        shutil.rmtree(verify_dir)
    run([os.path.join(GIBBED, "Gibbed.JustCause3.SmallUnpack.exe"), ee_out, verify_dir])
    rt_base, rt_out = walk_hashes(aaf), walk_hashes(verify_dir)
    rt_missing = sorted(set(rt_base) - set(rt_out))
    # SmallPack only packs what @files.xml lists; vanilla lists wheels only to lod3 (front) / lod4
    # (rear), so those unlisted files are inert by design. Anything ELSE missing is a packing loss.
    base_recs = toc_records(base_toc)
    rt_unlisted = [k for k in rt_missing if k not in base_recs]
    rt_lost = [k for k in rt_missing if k in base_recs]
    rt_diff = [k for k in set(rt_base) & set(rt_out) if k != "@files.xml" and rt_base[k] != rt_out[k]]
    roundtrip = not rt_lost and not rt_diff
    the_texture_ok = all(k in rt_out for k in tex) and not any(k in rt_missing for k in tex)

    toc_out = ee_out + ".toc"
    cmd = [sys.executable, os.path.join(ROOT, "Tools", "scripts", "eetoc.py"), "patch",
           ee_out, VANILLA_TOC, "--base-ee", BASE_EE, "-o", toc_out]
    for n in INTERNAL:
        cmd += ["--internal", n]
    run(cmd)
    toc_cmp = toc_summary(ee_out, toc_out)
    base_cmp = toc_summary(base_ee, base_toc)

    # ---- 5. verify ---------------------------------------------------------------
    checks = []
    base_h = walk_hashes(os.path.join(base, "aaf"))
    out_h = walk_hashes(aaf)
    added = sorted(set(out_h) - set(base_h))
    removed = sorted(set(base_h) - set(out_h))
    changed = sorted(k for k in set(base_h) & set(out_h) if base_h[k] != out_h[k])
    ok_added = all(k.startswith("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/batmobile/")
                   for k in added)
    # a rebase onto a build that already carries the appearance (078+) legitimately *replaces*
    # textures too (glass tint, solid albedos), so staged textures are an allowed change - nothing
    # else is.
    ok_changed = all(BODY_RE.match(os.path.basename(k)) or WHEEL_RE.match(os.path.basename(k))
                     or k == "@files.xml" or k in tex or k in overlays for k in changed)
    checks.append(("aafdiff: added only batmobile textures", ok_added, f"{len(added)} added"))
    checks.append(("aafdiff: changed only body/wheel RBMs + @files.xml", ok_changed, f"{len(changed)} changed"))
    checks.append(("aafdiff: nothing removed", not removed, f"{len(removed)} removed"))
    mods = [k for k in changed + removed
            if k.startswith(("editor/", "animations/")) and k not in overlays]
    checks.append(("modules and animation data untouched", not mods, f"{len(mods)} module files differ"))
    checks.append(("pack/unpack round-trip is byte-exact", roundtrip and the_texture_ok,
                   f"{len(rt_out)} files, {len(rt_unlisted)} unlisted-by-design not packed, "
                   f"{len(rt_lost)} lost, {len(rt_diff)} corrupt"))

    def rbm_path(part, lod):
        stem = "sportsmuscle_body" if part == "body" else "sportsmuscle_" + part
        return os.path.join(mdir, f"{stem}_lod{lod}.rbm")

    blocks = {}
    for part in ["body"] + [f"wheel_{c}" for c in ("f_l", "f_r", "r_l", "r_r")]:
        for lod in range(1, 6):
            p = rbm_path(part, lod)
            raw = open(p, "rb").read()
            m = R.decode(raw)
            if m.write() != raw:
                checks.append((f"{os.path.basename(p)} re-encode", False, "bytes differ"))
            blocks.setdefault(part, []).append(len(m.blocks))
    checks.append(("body LOD block counts", blocks["body"] == [17] * 5, str(blocks["body"])))
    checks.append(("wheel LOD block counts", all(v == [5] * 5 for v in blocks.values() if v != blocks["body"]),
                   str({k: v for k, v in blocks.items() if k != "body"})))

    # every texture a block references must exist in the packed tree
    missing = []
    for part in blocks:
        m = R.decode(open(rbm_path(part, 1), "rb").read())
        for b in m.blocks:
            for t in getattr(b, "textures", []) or []:
                if t.startswith(VEH_DIR + "/textures/batmobile/"):
                    if not os.path.exists(os.path.join(aaf, *t.split("/"))):
                        missing.append(t)
    checks.append(("every batmobile texture reference resolves", not missing, f"{len(missing)} missing"))

    recs = toc_records(toc_out)
    unlisted = [v for v in tex if v not in recs or recs[v][0] == 0]
    checks.append(("every new texture is internal in the .toc", not unlisted, f"{len(unlisted)} unlisted"))
    # only textures the base does not already list become new records; a rebase onto 078 adds 3-4,
    # not all 28 (the rest were listed by 078 itself)
    new_tex = [v for v in tex if v not in base_recs]
    checks.append((".toc: +N records for the new textures",
                   toc_cmp["toc"] - base_cmp["toc"] == len(new_tex),
                   f"{toc_cmp['toc']} vs base {base_cmp['toc']} (+{len(new_tex)} new of {len(tex)})"))
    checks.append((".toc: external baseline unchanged",
                   (toc_cmp["only_in_toc"], toc_cmp["only_in_ee"], toc_cmp["mismatch"]) ==
                   (0, base_cmp["only_in_ee"], base_cmp["mismatch"]),
                   f"only_in_ee {toc_cmp['only_in_ee']}/{base_cmp['only_in_ee']}, "
                   f"mismatch {toc_cmp['mismatch']}/{base_cmp['mismatch']}"))

    import bat_assemble as BA  # budget helpers, same numbers the pipeline used
    model_kb = sum(os.path.getsize(rbm_path(p, i)) for p in blocks for i in range(1, 6)) / 1024
    model_cap = BA.budget_value(BUDGET_XML, a.vehicle_class, "Model") * a.budget_safety
    checks.append(("model budget", model_kb <= model_cap, f"{model_kb:.0f} / {model_cap:.0f} KB"))
    tex_kb = sum(os.path.getsize(os.path.join(src, "ddsc", os.path.basename(v))) for v in tex) / 1024
    tex_cap = BA.texture_budget_kb(BUDGET_XML, a.vehicle_class, VANILLA_TOC)   # already x0.9
    checks.append(("texture budget", tex_kb <= tex_cap, f"{tex_kb:.0f} / {tex_cap:.0f} KB"))

    bad = [c for c in checks if not c[1]]
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:52} {detail}")
    if bad:
        raise Fail(f"{len(bad)} verification(s) failed")

    # ---- 6. receipt + installer ---------------------------------------------------
    ee_h, toc_h = sha(ee_out), sha(toc_out)
    receipt = {
        "tag": a.tag, "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "base": a.base, "src": a.src,
        "ee": {"bytes": os.path.getsize(ee_out), "sha256": ee_h},
        "replaced": replaced, "textures": len(tex), "textures_new_in_manifest": listed,
        "aafdiff": {"added": len(added), "changed": len(changed), "removed": len(removed)},
        "toc": {"bytes": os.path.getsize(toc_out), "sha256": toc_h, "records": toc_cmp["toc"],
                "ee_entries": toc_cmp["ee"], "external_only_in_ee": toc_cmp["only_in_ee"],
                "external_mismatch": toc_cmp["mismatch"]},
        "budgets": {"model_kb": round(model_kb), "model_cap_kb": round(model_cap),
                    "model_safety": a.budget_safety,
                    "texture_kb": round(tex_kb), "texture_cap_kb": round(tex_cap)},
        "checks": [{"name": n, "ok": bool(o), "detail": d} for n, o, d in checks],
        "installed": False,
    }
    json.dump(receipt, open(os.path.join(out, "receipt.json"), "w", encoding="utf-8"), indent=1)

    ps1 = f"""<#
    {a.tag} installer: {len(tex)} textures + 25 meshes from {a.src}, based on {a.base}.
    Modules, physics and land_global are untouched. Close the game first.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback{os.path.basename(a.base).split('-')[-1]}','Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$GameDir = '{a.game}'
$EeT = '{winpath(os.path.join(a.game, "dropzone", "editor", "entities", "jc_vehicles", "01_land", "v0300_car_kensington_sportsmuscle", EE))}'
$EeSha = '{ee_h}'
$TocSha = '{toc_h}'
$B = '{winpath(out)}'
switch ($Action) {{
    'Install' {{
        Copy-Item -LiteralPath (Join-Path $B '{EE}') -Destination $EeT -Force
        Copy-Item -LiteralPath (Join-Path $B '{EE}.toc') -Destination ($EeT + '.toc') -Force
        Write-Host 'deployed {a.tag}: per-material Batmobile appearance'
        Write-Host "next: install.ps1 -Action Verify  (reads the installed .ee through its .toc)"
    }}
    'Verify' {{
        python '{winpath(os.path.join(ROOT, "Tools", "scripts", "verify_install.py"))}' --build $B
        if ($LASTEXITCODE -ne 0) {{ throw "verify_install FAILED ($LASTEXITCODE) - do not trust this install" }}
    }}
    'Rollback{os.path.basename(a.base).split('-')[-1]}' {{
        powershell -NoProfile -ExecutionPolicy Bypass -File '{winpath(os.path.join(base, "install.ps1"))}' -Action Install
    }}
    'Status' {{
        $e = if (Test-Path -LiteralPath $EeT) {{ (Get-FileHash -LiteralPath $EeT).Hash }} else {{ 'none' }}
        $t = if (Test-Path -LiteralPath ($EeT + '.toc')) {{ (Get-FileHash -LiteralPath ($EeT + '.toc')).Hash }} else {{ 'none' }}
        Write-Host "dropzone .ee : $e"; Write-Host "dropzone .toc: $t"
        if ($e -eq $EeSha -and $t -eq $TocSha) {{ Write-Host '  == {a.tag} (all match)' }}
    }}
}}
"""
    open(os.path.join(out, "install.ps1"), "w", encoding="utf-8-sig", newline="").write(ps1)

    print(f"\n{a.tag}: {receipt['ee']['bytes']:,} B {ee_h}")
    print(f"          {receipt['toc']['bytes']:,} B {toc_h}")
    print(f"receipt -> {os.path.relpath(os.path.join(out, 'receipt.json'), ROOT)}")
    print("NOT installed. Run install.ps1 -Action Install when approved.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--base", required=True, help="e.g. Builds/test-077")
    b.add_argument("--src", required=True, help="an appearance_pipeline.py output dir")
    b.add_argument("--tag", required=True)
    b.add_argument("--game", default=r"D:\Games\Just Cause 3")
    b.add_argument("--vehicle-class", default="Vehicle-*HD*")
    b.add_argument("--allow-live-drift", action="store_true")
    b.add_argument("--budget-safety", type=float, default=1.0,
                   help="model cap as a fraction of the game's Model HARD budget "
                        "(must match the value the pipeline was run with)")
    b.add_argument("--overlay", action="append", default=[], metavar="VFS=FILE",
                   help="replace one more file in the staged aaf (probe builds); repeatable. "
                        "The overlay file counts as an allowed change in the aafdiff checks.")
    a = ap.parse_args()
    if a.cmd == "build":
        build(a)


if __name__ == "__main__":
    main()
