#!/usr/bin/env python
"""G2-26 probe: get the vanilla `profile/*.onlinec` out of the archives and see what they are.

Read-only. Writes the extracted (game) bytes to `E:/Modding/JustCause3/_grab/rebeldrop/` (outside the
repo, R10) and prints the header + whether the bytes are an ADF v4 file or a packfile with
inner files.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402

RAW = os.environ.get("JC3_RAW", r"E:/Modding/JustCause3/_grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
OUT = os.path.join(RAW, "rebeldrop")


def main() -> int:
    rows = jc3index.load_index(os.path.join(ROOT, "Research", "JC3Grab"))
    for path in ("profile/item.onlinec", "profile/task.onlinec"):
        hits = [r for r in rows if r.get("path") == path]
        print(path, "rows", len(hits))
        for r in hits:
            raw = jc3grab.read_entry(r, GAME)
            print("  archive", r["archive"], "size", len(raw), "head", raw[:16].hex())
            os.makedirs(OUT, exist_ok=True)
            dst = os.path.join(OUT, path.replace("/", "_"))
            with open(dst, "wb") as fh:
                fh.write(raw)
            print("  wrote", dst)
            try:
                adf = jc3adf.Adf(raw)
                print("  ADF v4:", adf.total, "types", len(adf.types),
                      "instances", len(adf.instances),
                      "root", adf.instances[0]["name"], adf.type_name(adf.instances[0]["type"]))
                names = [t["name"] for t in adf.types.values()]
                print("  type names:", names[:12])
            except Exception as exc:                       # noqa: BLE001 - probe
                print("  not a bare ADF:", exc)
                try:
                    stream, entries = jc3detail.inner_files(raw)
                    print("  inner files", len(entries), [e[0] for e in entries][:8])
                except Exception as exc2:                  # noqa: BLE001
                    print("  not a packfile either:", exc2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
