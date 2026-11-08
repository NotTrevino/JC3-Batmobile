"""bm_build.py - B-01: the phase-B build scaffold. One card = one build step = one `aafdiff`.

`GRAB_BACKLOG.md` §8 (`B-01`): "create Tools/scripts/bm_build.py that (1) copies Builds/test-091/aaf
to Builds/bm-0NN/aaf, (2) applies a named list of edit files in order (t1_apply.py / t5_apply.py
style, each with its own *_current.json snapshot), (3) packs (t5_build.py), (4) writes receipt.json,
install.ps1 (Install/Verify/Rollback091) without running it. Out: tool + Builds/bm-001/ (identity
build: no edits) as the control. Done: bm-001 .ee/.toc are byte-identical to test-091's."

The scaffold is deliberately thin: it adds no new packer and no new edit format. Packing and the
`.toc` rebuild stay `t5_build.py` (the module-build path), the edits stay `t5_apply.py` (which re-reads
every edited module and size-checks it) with `t1_apply.py` validating each list first, and every
snapshot is written inside the build's own directory so a later step never reads another build's
`*_current.json`.

Edit spec (`--edits`, repeatable, applied in the order given):

    {"schema": 1,
     "tag": "bm-004",
     "steps": [{"applier": "t5_apply",
                "edits": "Working/Translation/T8_PARTS.json",
                "current": "Working/Translation/t5b_current.json"}]}

`applier` is one of `t5_apply` (apply) / `t1_apply` (validate only, no file changes). Each step's
`current` snapshot is copied into `<build>/snapshots/<name>_current.json` before use, so the build
records what it applied against.

R9 (polish pass, 2026-11-01): the packer (`t5_build.py`) carries `replaced` / `textures` / `budgets`
forward from the base receipt. When the base receipt has no such key (`Builds/test-091`, the phase-B
base) that produces empty defaults that read like measurements. This scaffold now measures all three
on THIS build and writes them:

  budgets.model  = every .rbm reachable from the built parts module that is NOT byte-identical to the
                   vanilla Serpente's (`bm_budget.measure`, the method calibrated on test-065/081/085/091)
  budgets.texture= resident `.ddsc` records in the built `.toc` (`v01_gates.g_budget`'s method)
  replaced       = `.rbm` files in the build tree whose bytes differ from the base build's
  textures       = `.ddsc` files the same comparison finds changed, plus the resident total

`--check` re-measures the source-tree digest, the budgets and `installed`, and compares `.ee`/`.toc`
with the base build on disk as well as with the hashes pinned in the receipt.

Originals (B-12, 2026-11-07): D-2 was reopened as two variants, so the scaffold now carries a
`--variant pursuit|battle` declaration. The flag adds no new edit format: a variant is still an
ordinary edit spec (schema 1) plus three keys -

    {"schema": 1, "card": "B-12", "variant": "battle",
     "planned_files": ["editor/.../x.vmodc"],
     "rows": [{"row": "T-MD6", "carry": "composed", "why": "..."}],
     "steps": [{"applier": "t5_apply", "edits": "...", "current": "..."}]}

`planned_files` is the contract the cross-variant `aafdiff` is held to (see
`Tools/scripts/b12_variant_diff.py`): the diff between the `pursuit` and `battle` trees must list
those paths and nothing else. `rows` records, per variant-table row, whether the build carries it
exactly, by closest-system composition, on the same unbuilt switch, or not at all. The declaration
is written to `<build>/variant.json` and copied into the receipt, so a later reader can check the
diff without re-deriving the plan.

Usage:
    python Tools/scripts/bm_build.py --tag bm-001 --check           # re-read + compare (no writes)
    python Tools/scripts/bm_build.py --tag bm-004 --edits s.json    # a later step
    python Tools/scripts/bm_build.py --tag bm-001                  # identity control, no edits
    python Tools/scripts/bm_build.py --base bm-RC4-base --tag bm-RC4-modes/battle \
           --variant battle --edits Working/Translation/b12_variant_battle.json
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
from eetoc import read_toc  # noqa: E402

EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
GAME = r"D:\Games\Just Cause 3"
DROP = ("dropzone\\editor\\entities\\jc_vehicles\\01_land\\"
        "v0300_car_kensington_sportsmuscle")
BASE_DEFAULT = "test-091"          # the live build the phase-B lineage starts from
BATCH_SHEET = "Working/Translation/build_batches.json"   # what `--batches` records
LEDGER = "Working/Translation/T_ROWS.jsonl"
SCHEMA = 1
CAP_MODEL_KB = 4915.0               # R9: vehicle Model hard wall (vanilla asset_memory_budgets)
CAP_TEX_KB = 7065.0                 # R9: vehicle Texture hard wall
VARIANT_NAMES = ("pursuit", "battle")   # B-12: D-2's two variants
CARRY = ("exact", "composed", "same_switch", "not_built")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def tree_digest(root: str) -> dict:
    """Every file under `root`, hashed, in path order -> one digest over the list."""
    rows = []
    for dirpath, _dirs, files in os.walk(root):
        for n in files:
            p = os.path.join(dirpath, n)
            rows.append((os.path.relpath(p, root).replace("\\", "/"), os.path.getsize(p),
                         sha256_file(p)))
    rows.sort()
    blob = "\n".join(f"{n}\t{s}\t{h}" for n, s, h in rows).encode("utf-8")
    return {"files": len(rows), "bytes": sum(s for _n, s, _h in rows),
            "digest": hashlib.sha256(blob).hexdigest().upper()}


def tree_hashes(root: str) -> dict:
    """{relpath: sha256} for every file under `root` (the comparison the budgets/replaced need)."""
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for n in files:
            p = os.path.join(dirpath, n)
            out[os.path.relpath(p, root).replace("\\", "/")] = sha256_file(p)
    return out


def measure_budgets(tag_dir: str) -> dict:
    """R9 for this build, measured: model = non-vanilla reachable mesh KB; texture = resident .ddsc."""
    import bm_budget
    aaf = os.path.join(tag_dir, "aaf")
    model = bm_budget.measure(aaf)
    toc = read_toc(open(os.path.join(tag_dir, EE + ".toc"), "rb").read())
    tex_kb = sum(s for n, o, s in toc if o and n.endswith(".ddsc")) / 1024.0
    return {
        "model_non_vanilla_kb": model["non_vanilla_kb"],
        "model_reachable_kb": model["reachable_kb"],
        "model_rbm": model["rbm"],
        "model_cap_kb": CAP_MODEL_KB,
        "texture_resident_kb": round(tex_kb, 1),
        "texture_cap_kb": CAP_TEX_KB,
        "method": ("model = non-vanilla .rbm reachable from the parts module (bm_budget.measure, "
                   "calibrated on builds that rendered); texture = internal .ddsc records in the "
                   "built .toc (v01_gates.g_budget). Measured by bm_build.py on this build."),
    }


def measure_deltas(tag_dir: str, base_dir: str) -> tuple[dict, dict]:
    """(replaced, textures) as measured against the base build's own `aaf` tree."""
    mine = tree_hashes(os.path.join(tag_dir, "aaf"))
    base = tree_hashes(os.path.join(base_dir, "aaf"))
    changed = sorted(n for n, h in mine.items() if base.get(n) != h)
    rbm = [n for n in changed if n.endswith(".rbm")]
    ddsc = [n for n in changed if n.endswith(".ddsc")]
    replaced = {"body": sum(1 for n in rbm if "wheel" not in os.path.basename(n)),
                "wheel": sum(1 for n in rbm if "wheel" in os.path.basename(n)),
                "source": f"measured: .rbm bytes differ from {rel(base_dir)}'s own aaf tree"}
    textures = {"changed_by_this_step": len(ddsc),
                "resident_in_tree": sum(1 for n in mine if n.endswith(".ddsc")),
                "source": f"measured: .ddsc bytes differ from {rel(base_dir)}'s own aaf tree"}
    return replaced, textures


def batches_record() -> dict:
    """The phase-B sheet, frozen into the scaffold receipt: what every later step consumes.

    `T-23` closes with 17 payloads + 2 records over 24 B steps, so a scaffold that does not say
    which of them it is the base for cannot be audited later. This records, from
    `Working/Translation/build_batches.json` (the generated sheet, not the prose):

      * each step's id and `serves` codes;
      * the edit files it applies, with their row counts, or the declared no-payload reason;
      * the sheet's and the ledger's digests, as provenance;
      * `consumed`, the list later steps append to.

    `--check` re-derives the step list and fails if the sheet no longer agrees with the receipt, or
    if a consumed step's edit files are not among the build's applied steps.
    """
    path = os.path.join(ROOT, BATCH_SHEET)
    if not os.path.exists(path):
        raise SystemExit(f"{BATCH_SHEET} missing: run `t23_closeout.py --write` first")
    doc = json.load(open(path, encoding="utf-8"))
    batches = doc.get("batches") or doc
    steps = batches.get("steps") or []
    payloads = batches.get("payloads") or {}
    no_payload = batches.get("no_payload_steps") or {}
    out = []
    for st in steps:
        sid = st["id"]
        files = [{"file": n, "rows": payloads[n]["rows"], "values": payloads[n]["values"]}
                 for n in sorted(payloads) if sid in (payloads[n].get("steps") or [])]
        out.append({"id": sid, "serves": st.get("serves", ""),
                    "edits": files, "values": sum(f["values"] for f in files),
                    "no_payload_reason": None if files else no_payload.get(sid)})
    missing = [s["id"] for s in out if not s["edits"] and not s["no_payload_reason"]]
    if missing:
        raise SystemExit(f"batches: {', '.join(missing)} apply no edit and declare no reason")
    return {"sheet": BATCH_SHEET, "sheet_sha256": sha256_file(path),
            "ledger": {"path": LEDGER,
                        "sha256": sha256_file(os.path.join(ROOT, LEDGER)) if
                        os.path.exists(os.path.join(ROOT, LEDGER)) else None,
                        "rows": sum(1 for l in open(os.path.join(ROOT, LEDGER), encoding="utf-8")
                                    if l.strip()) if os.path.exists(os.path.join(ROOT, LEDGER))
                        else None},
            "steps": out, "consumed": [],
            "how_to_consume": ("a later step appends its step id to bm.batches.consumed in this "
                              "receipt; bm_build.py --check then fails if the id is not a recorded "
                              "step, is consumed twice, or its edit files are not among the "
                              "build's applied steps")}


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{os.path.basename(cmd[1] if cmd[0] == sys.executable else cmd[0])} "
                         f"failed:\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    tail = [l for l in r.stdout.strip().splitlines() if l.strip()][-2:]
    for line in tail:
        print("   " + line)


def load_specs(paths: list[str]) -> list[dict]:
    steps = []
    for path in paths:
        doc = json.load(open(path, encoding="utf-8"))
        if doc.get("schema") != SCHEMA:
            raise SystemExit(f"{path}: schema {doc.get('schema')}, expected {SCHEMA}")
        for st in doc.get("steps") or []:
            if st.get("applier") not in ("t5_apply", "t1_apply"):
                raise SystemExit(f"{path}: applier {st.get('applier')!r} is not t5_apply/t1_apply")
            for key in ("edits", "current"):
                if not os.path.exists(os.path.join(ROOT, st[key])):
                    raise SystemExit(f"{path}: {key} {st[key]} does not exist")
            st = dict(st, spec=path)
            steps.append(st)
    return steps


def load_variant(name: str, spec_paths: list[str]) -> dict:
    """Read the `--variant` declaration out of the edit specs, requiring every spec to agree.

    Raises rather than defaults: a variant build whose spec does not say which variant it is
    cannot be diffed against its sibling, which is the whole point of B-12.
    """
    if name not in VARIANT_NAMES:
        raise SystemExit(f"--variant {name}: not one of {', '.join(VARIANT_NAMES)}")
    if not spec_paths:
        raise SystemExit(f"--variant {name} needs an --edits spec that declares it")
    planned: list[str] = []
    rows: list[dict] = []
    specs = []
    for path in spec_paths:
        doc = json.load(open(path, encoding="utf-8"))
        if doc.get("variant") != name:
            raise SystemExit(f"{path}: declares variant {doc.get('variant')!r}, "
                             f"--variant says {name!r}")
        specs.append({"spec": rel(os.path.join(ROOT, path)), "card": doc.get("card"),
                      "steps": len(doc.get("steps") or [])})
        for f in doc.get("planned_files") or []:
            if f not in planned:
                planned.append(f)
        for r in doc.get("rows") or []:
            if r.get("carry") not in CARRY:
                raise SystemExit(f"{path}: row {r.get('row')} carry {r.get('carry')!r} "
                                 f"is not one of {', '.join(CARRY)}")
            rows.append(r)
    ids = [r.get("row") for r in rows]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"--variant {name}: rows declared twice: {', '.join(dupes)}")
    return {
        "name": name, "specs": specs, "planned_files": planned, "rows": rows,
        "counts": {c: sum(1 for r in rows if r.get("carry") == c) for c in CARRY} | {
            "files": len(planned), "rows": len(rows)},
        "method": ("planned_files = exactly what `aafdiff --hash` between the pursuit and battle "
                   "trees must list (Tools/scripts/b12_variant_diff.py); rows = the variant "
                   "table's rows and how this build carries each one"),
    }


def apply_steps(tag_dir: str, steps: list[dict]) -> list[dict]:
    """Apply (or validate) each edit list in order; every step gets its own snapshot."""
    snap = os.path.join(tag_dir, "snapshots")
    os.makedirs(snap, exist_ok=True)
    applied: list[dict] = []
    tree = os.path.join(tag_dir, "aaf")
    for i, st in enumerate(steps, 1):
        name = f"{i:02d}_{os.path.splitext(os.path.basename(st['edits']))[0]}"
        current = os.path.join(snap, f"{name}_current.json")
        shutil.copyfile(os.path.join(ROOT, st["current"]), current)
        print(f" step {i}: {st['applier']} {st['edits']} (snapshot {rel(current)})")
        if st["applier"] == "t1_apply":
            run([sys.executable, os.path.join(HERE, "t1_apply.py"),
                 "--edits", os.path.join(ROOT, st["edits"]), "--current", current])
            applied.append({"step": i, "applier": "t1_apply", "edits": st["edits"],
                            "current": rel(current), "rows": 0, "validate_only": True})
            continue
        out = os.path.join(snap, f"{name}_applied.json")
        # t5_apply writes into a COPY of the tree (never the source); with --out == the tree in
        # place it would copy onto itself, so the build tree is passed as --aaf and edited in place
        run([sys.executable, os.path.join(HERE, "t5_apply.py"), "--aaf", tree,
             "--edits", os.path.join(ROOT, st["edits"]), "--current", current, "--json", out])
        rows = len(json.load(open(out, encoding="utf-8"))["applied"])
        applied.append({"step": i, "applier": "t5_apply", "edits": st["edits"],
                        "current": rel(current), "applied": rel(out), "rows": rows})
    return applied


def write_installer(tag_dir: str, tag: str, base_tag: str, receipt: dict) -> None:
    """Install / Verify / Rollback<base> - generated, never run here (R6)."""
    base_rel = rel(os.path.join(ROOT, "Builds", f"test-{base_tag}"))
    body = f"""<#
    {tag} installer (B-01 scaffold build). Generated by Tools/scripts/bm_build.py, never run.
    Close the game before -Action Install. Rollback{base_tag} restores {base_tag}.
    NOTE: Rollback{base_tag} is itself an install - it runs {base_rel}/install.ps1 -Action Install,
    so it is covered by the same "never run before phase Q" limit and has never been exercised.
#>
[CmdletBinding()]
param([ValidateSet('Install','Verify','Rollback{base_tag}','Status')][string]$Action = 'Status')
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
        Write-Host 'deployed {tag}'
    }}
    'Verify' {{
        & python '{os.path.join(ROOT, "Tools", "scripts", "verify_install.py")}' --build $B
    }}
    'Rollback{base_tag}' {{
        & (Join-Path '{os.path.join(ROOT, "Builds", "test-" + base_tag)}' 'install.ps1') -Action Install
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
    with open(os.path.join(tag_dir, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True, help="e.g. bm-001 (Builds/bm-001/)")
    ap.add_argument("--base", default=BASE_DEFAULT, help=f"base build tag (default {BASE_DEFAULT})")
    ap.add_argument("--edits", action="append", default=[], help="edit spec JSON (repeatable, in order)")
    ap.add_argument("--force", action="store_true", help="replace an existing Builds/<tag>/")
    ap.add_argument("--batches", action="store_true",
                    help="record the phase-B sheet (build_batches.json) in the receipt, so every "
                         "later step can prove it consumed its batch")
    ap.add_argument("--check", action="store_true",
                    help="no writes: re-read the build and compare it with its own receipt")
    ap.add_argument("--variant", choices=list(VARIANT_NAMES),
                    help="B-12: declare this tree as one of D-2's two variants; every --edits "
                         "spec must declare the same variant (writes <build>/variant.json)")
    a = ap.parse_args()

    base_dir = os.path.join(ROOT, "Builds", a.base)
    tag_dir = os.path.join(ROOT, "Builds", a.tag)
    base_ee = os.path.join(base_dir, EE)
    for p in (os.path.join(base_dir, "aaf"), base_ee, base_ee + ".toc"):
        if not os.path.exists(p):
            raise SystemExit(f"base build incomplete: {rel(p)} missing")

    if a.check:
        return check(tag_dir, base_ee)

    if os.path.exists(tag_dir):
        if not a.force:
            raise SystemExit(f"{rel(tag_dir)} exists (use --force to rebuild it)")
        shutil.rmtree(tag_dir)
    os.makedirs(tag_dir)

    specs = load_specs(a.edits)
    variant = load_variant(a.variant, a.edits) if a.variant else None
    if a.tag == "bm-001" and specs:
        raise SystemExit("bm-001 is the identity control: it must apply no edit list")

    print(f"copy {rel(os.path.join(base_dir, 'aaf'))} -> {rel(os.path.join(tag_dir, 'aaf'))}")
    shutil.copytree(os.path.join(base_dir, "aaf"), os.path.join(tag_dir, "aaf"))
    src_tree = tree_digest(os.path.join(tag_dir, "aaf"))
    print(f"  {src_tree['files']} files, {src_tree['bytes']} B, digest {src_tree['digest'][:16]}…")

    applied = apply_steps(tag_dir, specs)
    if not applied:
        # t5_build insists on an applied list; an identity step has one with no rows
        json.dump({"source": None, "base": rel(os.path.join(tag_dir, "aaf")), "applied": []},
                  open(os.path.join(tag_dir, "applied.json"), "w", encoding="utf-8"), indent=1)
        print(" no edit steps: identity build (applied.json has 0 rows)")

    print("pack (t5_build.py) ...")
    run([sys.executable, os.path.join(HERE, "t5_build.py"),
         "--aaf", rel(os.path.join(tag_dir, "aaf")), "--base", rel(base_dir), "--tag", a.tag,
         "--applied", rel(os.path.join(tag_dir, "applied.json")) if not applied
         else os.path.join(ROOT, applied[-1]["applied"])])
    if applied:
        # later steps each wrote their own applied list; merge them for the receipt
        rows = []
        for st in applied:
            if st.get("applied"):
                rows.extend(json.load(open(os.path.join(ROOT, st["applied"]), encoding="utf-8"))["applied"])
        json.dump({"source": [s["edits"] for s in applied], "applied": rows},
                  open(os.path.join(tag_dir, "applied.json"), "w", encoding="utf-8"), indent=1)

    receipt = json.load(open(os.path.join(tag_dir, "receipt.json"), encoding="utf-8"))
    ee, toc = os.path.join(tag_dir, EE), os.path.join(tag_dir, EE + ".toc")
    # R9 + R4: measure the packer's carried-forward fields on THIS build (see the docstring)
    budgets = measure_budgets(tag_dir)
    replaced, textures = measure_deltas(tag_dir, base_dir)
    textures["resident_kb"] = budgets["texture_resident_kb"]
    receipt["budgets"] = budgets
    receipt["replaced"] = replaced
    receipt["textures"] = textures
    identity = {"ee_identical_to_base": sha256_file(ee) == sha256_file(base_ee),
                "toc_identical_to_base": sha256_file(toc) == sha256_file(base_ee + ".toc"),
                "base_ee_sha256": sha256_file(base_ee),
                "base_toc_sha256": sha256_file(base_ee + ".toc")}
    tree_after = tree_digest(os.path.join(tag_dir, "aaf"))
    receipt["bm"] = {
        "card": "B-01",
        "tag": a.tag,
        "base": rel(base_dir),
        "src_tree": src_tree,           # the copy of the base tree, before the edit steps
        "src_tree_after": tree_after,  # the tree as packed (== src_tree for an identity build)
        "edit_steps": applied,
        "rows_applied": sum(st.get("rows") or 0 for st in applied),
        "identity": identity,
        "installer_actions": ["Install", "Verify", f"Rollback{a.base.split('-')[-1]}", "Status"],
        "installed": False,
    }
    if variant:
        receipt["bm"]["variant"] = variant
    if a.batches:
        receipt["bm"]["batches"] = batches_record()
    # the identity check is a *control*: it can only be demanded of a build that applies no edits
    receipt["checks"] = receipt.get("checks", []) + [
        {"name": "tree copied from the base build", "ok": src_tree["files"] > 0,
         "detail": f"{src_tree['files']} files"},
        {"name": "R9 model budget",
         "ok": budgets["model_non_vanilla_kb"] <= CAP_MODEL_KB,
         "detail": f"non-vanilla {budgets['model_non_vanilla_kb']:,} KB of {CAP_MODEL_KB:,.0f} KB "
                   f"(reachable {budgets['model_reachable_kb']:,} KB)"},
        {"name": "R9 texture budget",
         "ok": budgets["texture_resident_kb"] <= CAP_TEX_KB,
         "detail": f"resident {budgets['texture_resident_kb']:,} KB of {CAP_TEX_KB:,.0f} KB"},
        {"name": "no edit step outside the named list", "ok": True,
         "detail": f"{len(applied)} step(s), {receipt['bm']['rows_applied']} rows"},
    ]
    if not applied:
        receipt["checks"].append({
            "name": f"{a.tag} .ee/.toc byte-identical to {a.base}",
            "ok": identity["ee_identical_to_base"] and identity["toc_identical_to_base"],
            "detail": ("both identical" if identity["ee_identical_to_base"]
                       and identity["toc_identical_to_base"] else
                       f"ee {identity['ee_identical_to_base']}, "
                       f"toc {identity['toc_identical_to_base']}")})
    if variant:
        receipt["checks"].append({
            "name": "variant spec matches --variant",
            "ok": variant["name"] == a.variant and bool(variant["specs"]),
            "detail": (f"{variant['name']}: {variant['counts']['exact']} exact, "
                       f"{variant['counts']['composed']} composed, "
                       f"{variant['counts']['same_switch']} same-switch, "
                       f"{variant['counts']['not_built']} not built; "
                       f"{len(variant['planned_files'])} planned file(s)")})
        with open(os.path.join(tag_dir, "variant.json"), "w", encoding="utf-8",
                  newline="\n") as f:
            json.dump(variant, f, indent=1)
    with open(os.path.join(tag_dir, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    write_installer(tag_dir, a.tag, a.base.split("-")[-1], receipt)

    print(f"{a.tag}: .ee {receipt['ee']['bytes']} B {receipt['ee']['sha256'][:16]}…, "
          f".toc {receipt['toc']['bytes']} B, {receipt['toc']['records']} records, "
          f"{len(applied)} edit step(s)")
    for c in receipt["checks"]:
        print(f"  {c['name']:<52} {'PASS' if c['ok'] else 'FAIL'}  ({c['detail']})")
    if a.tag == "bm-001" and not (identity["ee_identical_to_base"] and identity["toc_identical_to_base"]):
        raise SystemExit("B-01 identity control FAILED: bm-001 differs from test-091")
    if applied and identity["ee_identical_to_base"]:
        raise SystemExit(f"{a.tag} applied edits but its .ee is identical to the base: nothing moved")
    return 0 if all(c["ok"] for c in receipt["checks"]) else 1


def check(tag_dir: str, base_ee: str) -> int:
    """--check: re-read the build's files and compare them with its own receipt.

    Re-derives (never trusts) the `.ee`/`.toc` sizes and hashes, byte-identity against the base build
    on disk as well as against the hashes pinned in the receipt, the `.toc` record count, the source
    tree digest, the R9 budgets, the `replaced`/`textures` provenance, `installed: false`, and the
    installer's actions. One `PASS`/`FAIL` line per assertion, then the summary.
    """
    if not os.path.isdir(tag_dir):
        print(f"FAIL: {rel(tag_dir)} does not exist")
        return 1
    receipt = json.load(open(os.path.join(tag_dir, "receipt.json"), encoding="utf-8"))
    ee, toc = os.path.join(tag_dir, EE), os.path.join(tag_dir, EE + ".toc")
    bad = []
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append((name, ok, detail))
        if not ok:
            bad.append(f"{name}: {detail}")

    sizes = {}
    for name, path, rec in ((".ee", ee, receipt["ee"]), (".toc", toc, receipt["toc"])):
        if not os.path.exists(path):
            add(f"{name} present", False, "missing")
            sizes[name] = None
            continue
        sizes[name] = (os.path.getsize(path), sha256_file(path))
        add(f"{name} re-read from disk", sizes[name][0] == rec["bytes"],
            f"{sizes[name][0]:,} B of receipt {rec['bytes']:,} B")
        add(f"{name} sha256 matches the receipt", sizes[name][1] == rec["sha256"],
            f"{sizes[name][1][:16]}… of {rec['sha256'][:16]}…")

    bm = receipt.get("bm", {})
    identity = bm.get("identity", {})
    if identity and sizes.get(".ee") and sizes.get(".toc"):
        # the pinned hashes are the *base's*: an edited build is expected to differ, so the
        # assertion is that the verdict the receipt recorded still holds, not that it is "identical"
        recorded = (bool(identity["ee_identical_to_base"]), bool(identity["toc_identical_to_base"]))
        pinned = (sizes[".ee"][1] == identity["base_ee_sha256"],
                  sizes[".toc"][1] == identity["base_toc_sha256"])
        add("identity verdict still holds (pinned base hashes)", pinned == recorded,
            f"ee {pinned[0]}, toc {pinned[1]} (receipt recorded {recorded})")
        base_dir = os.path.join(ROOT, bm["base"])
        if os.path.exists(os.path.join(base_dir, EE)):
            disk = (sha256_file(ee) == sha256_file(os.path.join(base_dir, EE)),
                    sha256_file(toc) == sha256_file(os.path.join(base_dir, EE + ".toc")))
            add(f"identity verdict still holds ({bm['base']} on disk)", disk == recorded,
                f"ee {disk[0]}, toc {disk[1]} (receipt recorded {recorded})")
            if bm.get("tag") == "bm-001":
                add("bm-001 identity control", all(disk), "both files identical to the base")
        elif bm.get("tag") == "bm-001":
            add("bm-001 identity control", False, f"base build {bm['base']} is not on disk")

    src = bm.get("src_tree_after") or bm.get("src_tree") or {}
    if src:
        now = tree_digest(os.path.join(tag_dir, "aaf"))
        add("source tree digest re-measured", now == {k: src[k] for k in ("files", "bytes", "digest")},
            f"{now['files']} files, {now['bytes']:,} B, {now['digest'][:16]}…")

    bud = receipt.get("budgets") or {}
    add("R9 model budget present", isinstance(bud.get("model_non_vanilla_kb"), (int, float)),
        f"{bud.get('model_non_vanilla_kb')} KB")
    add("R9 model budget green",
        isinstance(bud.get("model_non_vanilla_kb"), (int, float))
        and 0 <= bud["model_non_vanilla_kb"] <= CAP_MODEL_KB,
        f"non-vanilla {bud.get('model_non_vanilla_kb')} KB of {CAP_MODEL_KB:,.0f} KB "
        f"(reachable {bud.get('model_reachable_kb')} KB)")
    add("R9 texture budget present", isinstance(bud.get("texture_resident_kb"), (int, float)),
        f"{bud.get('texture_resident_kb')} KB")
    add("R9 texture budget green",
        isinstance(bud.get("texture_resident_kb"), (int, float))
        and 0 < bud["texture_resident_kb"] <= CAP_TEX_KB,
        f"resident {bud.get('texture_resident_kb')} KB of {CAP_TEX_KB:,.0f} KB")
    add("budgets carry their method", bool(bud.get("method")), str(bud.get("method"))[:60] + "…")

    rep, tex = receipt.get("replaced") or {}, receipt.get("textures") or {}
    add("replaced measured, not a carried default",
        isinstance(rep, dict) and "source" in rep and "body" in rep and "wheel" in rep,
        f"body {rep.get('body')}, wheel {rep.get('wheel')}" if isinstance(rep, dict) else str(rep))
    add("textures measured, not a carried default",
        isinstance(tex, dict) and "source" in tex and "changed_by_this_step" in tex,
        f"changed {tex.get('changed_by_this_step')}, resident {tex.get('resident_in_tree')} of "
        f"{tex.get('resident_kb')} KB" if isinstance(tex, dict) else str(tex))

    add("installed: false", receipt.get("installed") is False and bm.get("installed") is False,
        f"receipt {receipt.get('installed')}, bm {bm.get('installed')}")

    bat = bm.get("batches")
    if bat:
        fresh = batches_record()
        want = {s["id"]: s for s in bat.get("steps") or []}
        have = {s["id"]: s for s in fresh["steps"]}
        add("recorded batch steps match the sheet", want == have,
            f"{len(want)} recorded of {len(have)} in {BATCH_SHEET}")
        cons = list(bat.get("consumed") or [])
        add("no batch consumed twice", len(cons) == len(set(cons)), f"consumed {cons or 'none'}")
        add("consumed ids are recorded steps", set(cons) <= set(want), f"consumed {cons or 'none'}")
        applied_files = {os.path.basename(st.get("edits") or "")
                         for st in (bm.get("edit_steps") or [])}
        gaps = [f"{c}:{e['file']}" for c in cons for e in want[c]["edits"]
                if e["file"] not in applied_files]
        add("each consumed batch's edits were applied here", not gaps,
            f"{len(cons)} consumed" + (f", missing {gaps}" if gaps else ""))

    if not os.path.exists(os.path.join(tag_dir, "install.ps1")):
        add("install.ps1 present", False, "missing")
    else:
        with open(os.path.join(tag_dir, "install.ps1"), encoding="utf-8") as f:
            ps = f.read()
        for action in bm.get("installer_actions", []):
            add(f"install.ps1 action {action!r}", f"'{action}'" in ps, "declared")

    recs = read_toc(open(toc, "rb").read()) if os.path.exists(toc) else []
    add(".toc record count recomputed", not recs or len(recs) == receipt["toc"]["records"],
        f"{len(recs)} of receipt {receipt['toc']['records']}")

    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" ({detail})" if detail else ""))
    print(f"{'PASS' if not bad else 'FAIL'}: {rel(tag_dir)} re-read against its receipt "
          f"({receipt['ee']['sha256'][:16]}…, {len(recs)} .toc records)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
