"""t1_current.py - dump a build's `.vmodc` values so the translation table quotes the build,
not a memory of the build.

Reuses `jc3grab.decode_vmodc` (Gibbed ConvertAdf -> XML -> flat rows) on files that are
already unpacked in the repo, instead of reading them back out of the game archives.

Usage:
  python t1_current.py <build-dir> [-o out.json]

`<build-dir>` is the folder that contains `editor/` (e.g. `Builds/test-083/aaf`).
Output (default `Working/Translation/current.json`):
  { "modules": { "<type>": {"file": ..., "values": {member_path: value}} },
    "files": [...] }
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jc3grab import decode_vmodc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_OUT = os.path.join(ROOT, "Working", "Translation", "current.json")


def dump(build: str) -> dict:
    work = os.path.join(os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab"), "tmp_t1")
    os.makedirs(work, exist_ok=True)
    modules: dict[str, dict] = {}
    files = []
    seen: dict[str, int] = {}
    for dirpath, _dirs, names in os.walk(build):
        for fn in sorted(names):
            if not fn.endswith(".vmodc"):
                continue
            path = os.path.join(dirpath, fn)
            files.append(os.path.relpath(path, build).replace("\\", "/"))
            with open(path, "rb") as f:
                blob = f.read()
            tag = fn[:-6]
            if tag in seen:
                seen[tag] += 1
                tag = f"{tag}#{seen[tag]}"
            else:
                seen[tag] = 0
            mods = decode_vmodc(blob, work, tag)
            if mods is None:
                modules[tag] = {"file": fn, "error": "convertadf-failed"}
                continue
            for m in mods:
                key = m.get("type") or m["instance"]
                if key in modules and "values" in modules[key]:
                    key = f"{key} ({fn})"
                modules[key] = {
                    "file": fn,
                    "instance": m["instance"],
                    "values": {r["path"]: r["value"] for r in m["rows"]},
                }
    return {"build": os.path.abspath(build), "modules": modules, "files": files}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("build", help="folder containing editor/ (e.g. Builds/test-083/aaf)")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT)
    a = ap.parse_args()
    doc = dump(a.build)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    bad = [k for k, v in doc["modules"].items() if "error" in v]
    print(f"{len(doc['modules'])} module types from {len(doc['files'])} files -> {a.out}")
    if bad:
        print("refused:", ", ".join(bad))


if __name__ == "__main__":
    main()
