"""appearance_pipeline.py - one command: grab -> convert -> import -> verify -> progress %.

Steps (each one fails the run if it fails):
  1. grab      appearance_grab.py        one umodel export of the playable Batmobile mesh, every
                                         material/texture it reaches (dynamic: no hand lists)
  2. factors   inside bat_assemble.py    every BmAK factor -> a JC3 input, 0 unhandled allowed
  3. convert   inside bat_assemble.py    textures -> .ddsc (BC1 / BC5 / BC3 glass), budget fitted
  4. import    bat_assemble.py           25 RBMs (5 parts x 5 LODs), VERIFY PASS each
  5. verify    spec_check.py             every block input decoded back and compared with its spec
  6. progress  appearance_progress.py    components transferred / total, as a percentage

It never deploys. The output is a staged build under Working/Appearance/build; deploy is a
separate, deliberate step.

Usage: python Tools/scripts/appearance_pipeline.py [--skip-grab] [--force-grab] [--out DIR]
       [--body-tris ...] [--wheel-tris ...] [--budget-safety ...]
"""
import argparse
import datetime
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
SCRIPTS = os.path.join(ROOT, "Tools", "scripts")
GAME_TREE = os.path.join(ROOT, "Builds", "test-003", "aaf", "models", "jc_vehicles", "01_land",
                         "v0300_car_kensington_sportsmuscle")
GRAB = os.path.join(ROOT, "Working", "Appearance", "grab")
SRC = os.path.join(GRAB, "Playable_Batmobile_SF")

TEMPLATES = {
    "--body-template": os.path.join(GAME_TREE, "sportsmuscle_body_lod1.rbm"),
    "--wheel-template": os.path.join(GAME_TREE, "sportsmuscle_wheel_f_l_lod1.rbm"),
    "--window-template": os.path.join(GAME_TREE, "sportsmuscle_door_f_l_window_lod1.rbm"),
    "--land-xml": os.path.join(ROOT, "Research", "PartsForensics", "patched_land_global.xml"),
    "--budget-xml": os.path.join(ROOT, "Research", "Budgets", "vanilla_budgets.xml"),
    "--vanilla-toc": os.path.join(ROOT, "Research", "SerpenteToc", "vanilla_civilian_01.ee.toc"),
}


def run(step, cmd, log, cwd=ROOT, echo=True):
    t0 = time.time()
    line = f"\n===== [{datetime.datetime.now():%H:%M:%S}] {step}: {' '.join(cmd)}\n"
    with open(log, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace")
        for out in p.stdout:
            f.write(out)
            f.flush()
            if echo:
                sys.stdout.write(out if step != "assemble" else "")
                sys.stdout.flush()
        code = p.wait()
    dt = time.time() - t0
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"----- {step}: exit {code} in {dt:.1f}s\n")
    print(f"[{step}] exit {code} in {dt:.1f}s")
    if code != 0:
        raise SystemExit(f"{step} FAILED (exit {code}) - see {os.path.relpath(log, ROOT)}")
    return dt


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "Working", "Appearance", "build"))
    ap.add_argument("--skip-grab", action="store_true", help="reuse Working/Appearance/grab as it is")
    ap.add_argument("--force-grab", action="store_true", help="re-export from the game even if a grab exists")
    ap.add_argument("--body-tris", default="43000,6000,3000,1500,800")
    ap.add_argument("--wheel-tris", default="2500,1000,400,200,100")
    ap.add_argument("--budget-safety", type=float, default=1.0,
                    help="model cap as a fraction of the game's Model HARD budget "
                         "(1.0 = the hard cap itself, BUD-1 standing; 0.9 = the old guard)")
    ap.add_argument("--no-verify", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    log = os.path.join(a.out, "pipeline.log")
    open(log, "w", encoding="utf-8").write(f"appearance pipeline {datetime.datetime.now():%Y-%m-%d %H:%M}\n")
    times = {}

    missing = [f"{k} {v}" for k, v in TEMPLATES.items() if not os.path.exists(v)]
    if missing:
        raise SystemExit("missing input(s):\n  " + "\n  ".join(missing))

    # 1. grab ---- dynamic source of truth
    if a.skip_grab and os.path.isdir(GRAB):
        print("[grab] skipped (--skip-grab)")
    else:
        g = [PY, os.path.join(SCRIPTS, "appearance_grab.py")] + (["--force"] if a.force_grab else [])
        times["grab"] = run("grab", g, log)
    pskx = os.path.join(SRC, "SkeletalMesh3", "Batmobile_V2.pskx")
    if not os.path.exists(pskx):
        raise SystemExit("grab produced no Batmobile_V2.pskx at " + pskx)

    # 2-4. factors + convert + import (one pass, one transform)
    asm = [PY, os.path.join(SCRIPTS, "bat_assemble.py"), pskx,
           "--src-dir", SRC, "--out", a.out,
           "--body-tris", a.body_tris, "--wheel-tris", a.wheel_tris,
           "--budget-safety", str(a.budget_safety)]
    for k, v in TEMPLATES.items():
        asm += [k, v]
    times["assemble"] = run("assemble", asm, log, echo=False)

    # 5. verify the blocks against the specs
    if not a.no_verify:
        times["verify"] = run("verify", [PY, os.path.join(SCRIPTS, "spec_check.py"), a.out,
                                         TEMPLATES["--body-template"]], log, echo=True)

    # 6. progress %
    times["progress"] = run("progress", [PY, os.path.join(SCRIPTS, "appearance_progress.py"),
                                        "--build", a.out], log, echo=True)

    print(f"\nstaged build: {os.path.relpath(a.out, ROOT)}  "
          f"({', '.join(f'{k} {v:.0f}s' for k, v in times.items())})")
    print("NOT deployed - the dropzone is untouched.")


if __name__ == "__main__":
    main()
