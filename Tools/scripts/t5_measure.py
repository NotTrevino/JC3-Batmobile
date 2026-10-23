"""t5_measure.py - read the T-5 rows back out of the INSTALLED build (T-5).

`verify_install.py` proves the right bytes are deployed and the meshes decode.
This proves the *values* the translation table claims are the values the engine
will load: for every edit in `t5_applied.json`, take the module's bytes from the
installed `.ee` **through its `.toc` record**, decode them with Gibbed, and
compare the member with the row's `new` value.

A value that only exists in the staging tree is not shipped; a value read through
a stale `.toc` offset is not shipped either. This is the offline half of T-5 -
handling (0-100 km/h, understeer, ride height, shift points) still needs a
driver, and this script names those rows instead of pretending they passed.

Usage:
  python t5_measure.py --build Builds/test-084
  python t5_measure.py --build Builds/test-084 --ee <path to .ee> --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from eetoc import read_toc, sarc_dir, unaaf  # noqa: E402
from t5_apply import decode, paths, same  # noqa: E402

EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
DROP = os.path.join(r"D:\Games\Just Cause 3", "dropzone", "editor", "entities",
                    "jc_vehicles", "01_land", "v0300_car_kensington_sportsmuscle", EE)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True)
    ap.add_argument("--ee", default=DROP)
    ap.add_argument("--applied", default=os.path.join(ROOT, "Working", "Translation",
                                                     "t5_applied.json"))
    ap.add_argument("--json", help="write the per-row measurement here")
    a = ap.parse_args()

    with open(a.applied, encoding="utf-8") as f:
        applied = json.load(f)["applied"]

    sarc = unaaf(open(a.ee, "rb").read())
    toc = {n: (o, s) for n, o, s in read_toc(open(a.ee + ".toc", "rb").read())}
    have = {n: (o, s) for n, o, s in sarc_dir(sarc)}

    rows, bad = [], []
    cache: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as td:
        for e in applied:
            name = e["file"].replace("\\", "/")
            name = next((n for n in toc if n.endswith("/" + name.rsplit("/", 1)[-1])), None)
            if name is None:
                bad.append(f"{e['row']}: {os.path.basename(e['file'])} not in the .toc")
                continue
            off, size = toc[name]
            if not off:
                bad.append(f"{e['row']}: {name} is external in the .toc (reads archives, not this build)")
                continue
            if have.get(name) != (off, size):
                bad.append(f"{e['row']}: .toc {off}+{size} != .ee {have.get(name)}")
                continue
            if name not in cache:
                vm = os.path.join(td, "m.vmodc")
                with open(vm, "wb") as f:
                    f.write(sarc[off:off + size])
                root = ET.fromstring(decode(vm, os.path.join(td, "m.xml")))
                cache[name] = paths(root.find("instances/instance"))
            table = cache[name]
            el = table.get(e["member"])
            if el is None:
                bad.append(f"{e['row']}: {e['member']} missing from {name}")
                continue
            got = (el.text or "").strip()
            ok = same(e["new"], got, el.get("type") or "")
            rows.append({"row": e["row"], "module": e["module"], "member": e["member"],
                         "expected": e["new"], "actual": float(got) if ok else got,
                         "ok": ok, "file": name, "offset": off, "size": size})
            if not ok:
                bad.append(f"{e['row']}: {e['member']} = {got}, wanted {e['new']}")

    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"build": a.build, "ee": a.ee, "rows": rows,
                       "problems": bad}, f, indent=1)

    print(f"{len(rows)} / {len(applied)} rows read back through the .toc, "
          f"{sum(1 for r in rows if r['ok'])} equal to the table's `new`")
    for r in rows:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  {mark} {r['row']:7s} {r['module']}.{r['member']:42s} = {r['actual']}")
    if bad:
        print("\nFAIL")
        for b in bad:
            print(" ", b)
        sys.exit(1)


if __name__ == "__main__":
    main()
