"""t5_apply.py - apply the T-1 edit list to a build tree, in one pass (T-5).

`Working/Translation/t1_edits.json` names the change set as `(module, member, old, new)`.
`t1_apply.py` *validates* that list against `current.json`. This script *performs* it:

  decode  each target `.vmodc` with Gibbed's ConvertAdf to XML
  resolve the member path inside the decoded instance - dotted structures and
          inline-array items (`front_wheels.mass`, `upshift_rpm[0]`)
  assert  the element's current value equals `old` (the list's own guard)
  write   the new value at that element's `offset-in-file` anchor, so the XML
          around it is untouched (Gibbed re-imports the same layout)
  encode  back over the same file and assert the `.vmodc` size did not change
  reread  decode again and assert every edited member now reads `new`

Nothing is packed, installed or launched here: packing the `.ee`, patching its
`.toc` and the receipt are the caller's job (see `Working/Translation/T5_BUILD.md`).

Usage:
  python t5_apply.py --aaf Builds/test-083/aaf --out Builds/test-084/aaf
  python t5_apply.py --aaf Builds/test-083/aaf --check-only
  python t5_apply.py --aaf ... --out ... --json Working/Translation/t5_applied.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "Working", "Translation")
GIBBED = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertAdf.exe")

TOL = 1e-4


def decode(vmodc: str, xml: str) -> str:
    r = subprocess.run([GIBBED, "--e", vmodc, xml], capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"decode failed: {vmodc}\n{r.stdout[-300:]}{r.stderr[-300:]}")
    with open(xml, encoding="utf-8-sig") as f:
        return f.read()


def encode(xml: str, vmodc: str) -> None:
    r = subprocess.run([GIBBED, "--i", xml, vmodc], capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"import failed: {vmodc}\n{r.stdout[-300:]}{r.stderr[-300:]}")


def paths(instance: ET.Element) -> dict[str, ET.Element]:
    """{flattened member path: element} for every primitive in the instance.

    A structure member contributes its name; an inline-array item has no name of
    its own, so it is addressed by the parent's name plus its index.
    """
    out: dict[str, ET.Element] = {}

    def walk(node: ET.Element, prefix: list[str]) -> None:
        for i, kid in enumerate(node.findall("member")):
            name = kid.get("name")
            if name:
                path = prefix + [name]
            elif prefix:
                path = prefix[:-1] + [f"{prefix[-1]}[{i}]"]
            else:
                path = [f"[{i}]"]
            if kid.get("offset-in-file"):
                out[".".join(path)] = kid
            else:
                walk(kid, path)

    walk(instance, [])
    # The instance wraps its members in one structural member named after the
    # instance (`LandGlobal`, `v0300_..._sportsmusc`); the table calls a member
    # by its path *inside* the module, so that wrapper is not part of the key.
    strip = (instance.get("name") or "") + "."
    if strip != ".":
        out = {k[len(strip):] if k.startswith(strip) else k: v for k, v in out.items()}
    return out


def same(old, text: str, kind: str) -> bool:
    if kind.startswith("int") or kind.startswith("uint"):
        return int(text) == int(old)
    return abs(float(text) - float(old)) <= TOL * max(1.0, abs(float(old)))


def fmt(new, kind: str) -> str:
    if kind.startswith("int") or kind.startswith("uint"):
        return str(int(new))
    return format(float(new), ".9g")


def apply_file(vmodc: str, edits: list[dict], check_only: bool) -> list[dict]:
    with tempfile.TemporaryDirectory() as td:
        xml = os.path.join(td, "in.xml")
        text = decode(vmodc, xml)
        root = ET.fromstring(text)
        inst = root.find("instances/instance")
        if inst is None:
            raise SystemExit(f"no instance in {vmodc}")
        table = paths(inst)
        before_values = {k: (v.text or "").strip() for k, v in table.items()}
        for e in edits:
            el = table.get(e["member"])
            if el is None:
                raise SystemExit(f"{e['row']}: no member {e['member']!r} in {os.path.basename(vmodc)}")
            kind = el.get("type") or ""
            cur = (el.text or "").strip()
            if not same(e["old"], cur, kind):
                raise SystemExit(f"{e['row']}: {e['member']} holds {cur!r} "
                                 f"({kind}), list expects {e['old']!r}")
            if check_only:
                continue
            off = el.get("offset-in-file")
            pat = re.compile(r'(<member\b[^>]*offset-in-file="%s"[^>]*>)([^<]*)(</member>)' % off)
            hits = pat.findall(text)
            if len(hits) != 1:
                raise SystemExit(f"{e['row']}: anchor {off} matched {len(hits)} times")
            text = pat.sub(lambda m: m.group(1) + fmt(e["new"], kind) + m.group(3), text, count=1)
        if check_only:
            return [{"row": e["row"], "member": e["member"], "old": e["old"],
                     "new": e["new"], "file": vmodc, "applied": False} for e in edits]

        before = os.path.getsize(vmodc)
        with open(xml, "w", encoding="utf-8") as f:
            f.write(text)
        encode(xml, vmodc)
        after = os.path.getsize(vmodc)

        back = decode(vmodc, os.path.join(td, "out.xml"))
        back_root = ET.fromstring(back)
        back_paths = paths(back_root.find("instances/instance"))

        # A size change is allowed only when every other member is unchanged:
        # Gibbed's writer may normalise trailing padding, nothing else.
        touched = {e["member"] for e in edits}
        if set(before_values) != set(back_paths):
            raise SystemExit(f"{os.path.basename(vmodc)}: member set changed "
                             f"({len(before_values)} -> {len(back_paths)})")
        moved = []
        for key, was in before_values.items():
            if key in touched:
                continue
            now = (back_paths[key].text or "").strip()
            kind = back_paths[key].get("type") or ""
            try:
                if kind.startswith("int") or kind.startswith("uint"):
                    changed = int(was) != int(now)
                else:
                    changed = abs(float(was) - float(now)) > TOL * max(1.0, abs(float(was)))
            except ValueError:
                changed = was != now          # strings, hashes, enum names
            if changed:
                moved.append((key, was, now))
        if moved:
            raise SystemExit(f"{os.path.basename(vmodc)}: untouched members moved: {moved[:4]}")

        out = []
        for e in edits:
            el = back_paths[e["member"]]
            kind = el.get("type") or ""
            got = (el.text or "").strip()
            if not same(e["new"], got, kind):
                raise SystemExit(f"{e['row']}: re-read {e['member']} = {got!r}, wanted {e['new']!r}")
            out.append({"row": e["row"], "module": e["module"], "member": e["member"],
                        "old": e["old"], "new": e["new"], "file": vmodc,
                        "kind": kind, "applied": True})
        for r in out:
            r["size_before"], r["size_after"] = before, after
            r["members_unchanged"] = len(before_values) - len(touched)
        return out


def locate(aaf: str, basename: str) -> str:
    hits = []
    for dirpath, _dirs, files in os.walk(aaf):
        if basename in files:
            hits.append(os.path.join(dirpath, basename))
    if len(hits) != 1:
        raise SystemExit(f"{basename}: {len(hits)} copies under {aaf}")
    return hits[0]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aaf", required=True, help="unpacked build tree to read from")
    ap.add_argument("--out", help="copy of that tree to write into (never the source)")
    ap.add_argument("--edits", default=os.path.join(BASE, "t1_edits.json"))
    ap.add_argument("--current", default=os.path.join(BASE, "current.json"))
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--json", help="write the applied list here")
    a = ap.parse_args()

    with open(a.edits, encoding="utf-8") as f:
        edits = json.load(f)["edits"]
    with open(a.current, encoding="utf-8") as f:
        current = json.load(f)["modules"]

    groups: dict[str, list[dict]] = {}
    for e in edits:
        mod = current.get(e["module"])
        if not mod:
            raise SystemExit(f"{e['row']}: module {e['module']} not in current.json")
        groups.setdefault(locate(a.aaf, mod["file"]), []).append(e)

    if a.out and not a.check_only:
        shutil.copytree(a.aaf, a.out, dirs_exist_ok=True)
        groups = {locate(a.out, os.path.basename(k)): v for k, v in groups.items()}

    applied: list[dict] = []
    for path in sorted(groups):
        applied.extend(apply_file(path, groups[path], a.check_only))
        print(f"{'OK  ' if a.check_only else 'FILE'} {os.path.basename(path)}: "
              f"{len(groups[path])} edit(s)")

    if a.json and not a.check_only:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"source": a.edits, "base": a.aaf, "applied": applied}, f, indent=1)

    print(f"{len(applied)} edit(s) over {len(groups)} module(s)"
          f"{' validated' if a.check_only else ' applied, re-read and size-checked'}")


if __name__ == "__main__":
    main()
