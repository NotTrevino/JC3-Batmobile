"""Dynamic grab of the BmAK Batmobile appearance set (MODLOG 102).

One umodel export of the standard playable Batmobile skeletal mesh pulls in every
object reachable from it: the mesh, its materials, their parent masters and every
texture those bind, across package boundaries (Startup.upk included). That is the
whole appearance set - no hand-written material or texture lists.

umodel drops references it cannot load to "None" (unresolved imports), which would
lose the parent chain and the unbound texture names the factor rules need. Where the
older reference export (Playable_Batmobile_SF/) kept them, this step merges the
richer .props.txt back in and records that it did.

Usage:  python Tools/scripts/appearance_grab.py [--force]
Writes: Working/Appearance/grab/**, Working/Appearance/grab_manifest.json
"""
import argparse
import glob
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
UMODEL = r"C:\Users\User\source\repos\UEViewer\umodel.exe"
PACKAGE = "Playable_Batmobile_SF"
MESH = "Batmobile_V2"
OUT = os.path.join(ROOT, "Working", "Appearance", "grab")
REFERENCE = os.path.join(ROOT, "Playable_Batmobile_SF")

CLASS_DIRS = {
    "SkeletalMesh3": "SkeletalMesh",
    "Material3": "Material",
    "MaterialInstanceConstant": "MaterialInstance",
    "Texture2D": "Texture2D",
}
PROPS = ".props.txt"


def _non_none(path):
    """How many parameter/parent assignments are actually resolved in a props dump."""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return -1
    return text.count("ParameterValue =") + text.count("Parent =") - text.count("= None")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def export(force):
    if os.path.isdir(OUT) and os.listdir(OUT) and not force:
        print("grab exists (use --force to re-export):", OUT)
        return
    os.makedirs(OUT, exist_ok=True)
    cmd = [UMODEL, "-export", "-out=" + OUT, "-path=" + GAME,
           PACKAGE + ".upk", MESH, "SkeletalMesh"]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = os.path.join(ROOT, "Working", "Appearance", "grab_umodel.log")
    open(log, "w", encoding="utf-8").write((r.stdout or "") + (r.stderr or ""))
    if r.returncode != 0:
        raise SystemExit("umodel export failed, see " + log)
    for line in (r.stdout or "").splitlines():
        if "not found" in line.lower():
            print("  umodel:", line.strip())


def merge_reference():
    """Prefer the props dump that resolves more references (the older export kept
    references umodel now collapses to None)."""
    merged = []
    for new in glob.glob(os.path.join(OUT, "**", "*" + PROPS), recursive=True):
        # OUT/<Package>/<Class>/<name>.props.txt -> REFERENCE/<Class>/<name>.props.txt
        rel = os.path.relpath(new, OUT)
        parts = rel.split(os.sep)
        if len(parts) < 3:
            continue
        ref = os.path.join(REFERENCE, *parts[1:])
        if not os.path.exists(ref):
            continue
        if _non_none(ref) > _non_none(new):
            open(new, "wb").write(open(ref, "rb").read())
            merged.append({"file": rel, "resolved_before": _non_none(new),
                           "resolved_after": _non_none(ref)})
    return merged


def inventory():
    rows = []
    for cls_dir, cls in CLASS_DIRS.items():
        for path in sorted(glob.glob(os.path.join(OUT, "**", cls_dir, "*"), recursive=True)):
            if not os.path.isfile(path) or path.endswith(PROPS):
                continue
            rel = os.path.relpath(path, OUT)
            rows.append({
                "class": cls,
                "name": os.path.splitext(os.path.basename(path))[0],
                "package": rel.split(os.sep)[0],
                "file": rel,
                "bytes": os.path.getsize(path),
                "sha256": _sha256(path),
                "props": os.path.exists(path + PROPS),
            })
    return rows


def variants():
    """Appearance counts of the other Batmobile packages, so the scope is on record."""
    out = []
    for name in ("Playable_Batmobile_SF", "Playable_BatmobileMK2_SF", "Playable_BatmobileJoker_SF"):
        r = subprocess.run([UMODEL, "-list", "-path=" + GAME, name + ".upk"],
                           capture_output=True, text=True)
        counts = {}
        for line in (r.stdout or "").splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[3] in ("SkeletalMesh", "Material", "MaterialInstanceConstant", "Texture2D"):
                counts[parts[3]] = counts.get(parts[3], 0) + 1
        out.append({"package": name, "counts": counts})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-variants", action="store_true")
    a = ap.parse_args()

    export(a.force)
    merged = merge_reference()
    rows = inventory()
    by_class = {}
    for r in rows:
        by_class.setdefault(r["class"], []).append(r)
    manifest = {
        "game": GAME,
        "umodel": UMODEL,
        "package": PACKAGE,
        "mesh": MESH,
        "root": os.path.relpath(OUT, ROOT),
        "reference": os.path.relpath(REFERENCE, ROOT),
        "merged_props": merged,
        "counts": {k: len(v) for k, v in sorted(by_class.items())},
        "objects": rows,
        "variants": [] if a.no_variants else variants(),
    }
    path = os.path.join(ROOT, "Working", "Appearance", "grab_manifest.json")
    json.dump(manifest, open(path, "w", encoding="utf-8"), indent=1)
    print("grab:", manifest["counts"], "merged props:", len(merged))
    print("manifest ->", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
