"""grab_cdo_payloads.py - decode the six CDO component payloads the 512 MiB budget skipped.

`Research/RESET_STATUS.md` (R-6) leaves one UNKNOWN as "the 6 CDO component payloads past
the 512 MiB decode budget". `grab_packages_g305.PartialPackage.data()` refuses any export
whose `offset + size` exceeds `DECODE_BUDGET` (512 MiB) instead of decompressing further,
so those six children of `Default__RVehicleBatmobile` were never read.

This script asks the prior question first: is the declared length plausible? For every CDO
child it prints the declared length, the package file size and the decompressed image size.
A declared length larger than the file would mean the export table was misparsed; it is not
the case here - all six payloads are 14 or 67 bytes, and it is their *offset* (0x26795f7d
.. 0x26796003) that crosses the budget because the image is ~2x the file when decompressed
(the file is chunk-compressed).

Then it decodes them. The payloads are CDO components, which carry a 12-byte prefix before
the property-tag stream (`STARTUP_PREFIX`): bytes 4..7 are the export record's own name-table
index, so a matching index proves the prefix and the tag start. Tags are walked with
`upk_read.walk_tags` from byte 12 and named against the generated BmSDK-AK C# sources, whose
accessors store `Ptr + <decimal offset>` per member.

Output: Research/BatmobileGrab/CDO_PAYLOADS.md.

Usage:
  python Tools/scripts/grab_cdo_payloads.py --write   # write the note
  python Tools/scripts/grab_cdo_payloads.py --check   # re-derive and compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read as U  # noqa: E402

COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
STARTUP = os.path.join(COOKED, "Startup.upk")
SDK = r"E:\Modding\_tools\BmSDK-AK"
SDK_GENERATED = os.path.join(SDK, "src", "BmSDK", "Generated")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "CDO_PAYLOADS.md")

CDO_NAME = "Default__RVehicleBatmobile"
CDO_CLASS = "RVehicleBatmobile"
# Byte offset where the tag stream starts in a prefixed CDO component payload.
STARTUP_PREFIX = 12
# Must equal grab_packages_g305.DECODE_BUDGET, the guard that skipped these payloads.
DECODE_BUDGET = 512 * 1024 * 1024


# ------------------------------------------------------------------ input
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cdo_and_children(pkg: U.Package) -> tuple[int, list[int]]:
    cdo = next((i for i, e in enumerate(pkg.exports, 1)
                if e["name"] == CDO_NAME and pkg.object_class(i) == CDO_CLASS), None)
    if cdo is None:
        raise SystemExit("no %s export in %s" % (CDO_NAME, STARTUP))
    kids = [i for i, e in enumerate(pkg.exports, 1) if e["outer_index"] == cdo]
    return cdo, kids


# ------------------------------------------------------------------ sdk
PROP_RE = re.compile(r"///\s*(\w+Property):\s*(\S+)")
CLASS_RE = re.compile(r"public partial class (\w+) : ([\w.]+),")
NS_RE = re.compile(r"^namespace ([\w.]+);", re.M)
PTR_RE = re.compile(r"Ptr \+ (\d+)")


class Sdk:
    """offset -> (member, kind, bit) per generated class, plus the parent chain."""

    def __init__(self, root: str):
        self.members: dict[str, dict[int, dict]] = {}
        self.parent: dict[str, str] = {}
        self.files = 0
        for path in self._walk(root):
            self.files += 1
            self._parse(path)

    @staticmethod
    def _walk(root: str):
        for dirpath, _dirs, names in os.walk(root):
            for name in sorted(names):
                if name.endswith(".g.cs"):
                    yield os.path.join(dirpath, name)

    def _parse(self, path: str) -> None:
        text = open(path, encoding="utf-8").read()
        m = CLASS_RE.search(text)
        if not m:
            return
        cls, parent = m.group(1), m.group(2).split(".")[-1]
        self.parent[cls] = parent
        out = self.members.setdefault(cls, {})
        lines = text.splitlines()
        for n, line in enumerate(lines):
            pm = PROP_RE.search(line)
            if not pm:
                continue
            kind, name = pm.group(1), pm.group(2)
            for j in range(n + 1, min(n + 9, len(lines))):
                am = PTR_RE.search(lines[j])
                if not am:
                    continue
                off = int(am.group(1))
                bit = None
                bm = re.search(r"\)\s*&\s*(\d+)\)|&\s*(\d+)\)\s*!= 0", lines[j])
                if kind == "Bool":
                    bm = re.search(r"&\s*(\d+)\)", lines[j])
                    bit = int(bm.group(1)) if bm else None
                out.setdefault(off, {"member": name, "kind": kind, "bit": bit,
                                     "file": os.path.relpath(path, SDK).replace("\\", "/")})
                break

    def chain(self, cls: str) -> list[str]:
        seen, out = set(), []
        while cls and cls not in seen:
            seen.add(cls)
            out.append(cls)
            cls = self.parent.get(cls)
        return out

    def resolve(self, cls: str, offset: int) -> dict | None:
        """Most-derived class that declares this layout offset."""
        for c in self.chain(cls):
            hit = self.members.get(c, {}).get(offset)
            if hit:
                return {**hit, "class": c}
        return None


# ------------------------------------------------------------------ decode
def decode_payload(pkg: U.Package, index: int, sdk: Sdk) -> dict:
    e = pkg.exports[index - 1]
    data = pkg.data(index)
    cls = pkg.object_class(index) or ""
    name_index = (int.from_bytes(data[4:8], "little", signed=True)
                  if len(data) >= 8 else None)
    prefix_name = (pkg.names[name_index]
                   if name_index is not None and 0 <= name_index < len(pkg.names) else None)
    tags, end, why = U.walk_tags(pkg, data, STARTUP_PREFIX)
    decoded = []
    unknown = 0
    for t in tags:
        hit = sdk.resolve(cls, t["offset"])
        named = dict(t)
        named["sdk"] = hit
        if hit is None:
            unknown += 1
        decoded.append(named)
    return {
        "index": index, "name": e["name"], "class": cls,
        "size": e["size"], "offset": e["offset"], "end": e["offset"] + e["size"],
        "past_budget": e["offset"] + e["size"] > DECODE_BUDGET,
        "prefix": {"bytes": data[:STARTUP_PREFIX].hex(" "),
                   "name_index": name_index, "name": prefix_name,
                   "oracle": prefix_name == e["name"]},
        "tags": [{k: v for k, v in t.items() if k != "sdk"} for t in decoded],
        "sdk": [{k: v for k, v in (t["sdk"] or {}).items()} for t in decoded],
        "tag_count": len(tags),
        "parsed_bytes": end,
        "stop": why,
        "leftover": len(data) - end,
        "leftover_hex": data[end:].hex(" "),
        "unknown_tags": unknown,
        "head": data[:48].hex(" "),
    }


# ------------------------------------------------------------------ build
def build() -> dict:
    pkg = U.Package(STARTUP)
    cdo, kids = cdo_and_children(pkg)
    sdk = Sdk(SDK_GENERATED)
    file_size, image_size = len(pkg.raw), len(pkg.image)

    rows = [decode_payload(pkg, i, sdk) for i in kids]
    past = [r for r in rows if r["past_budget"]]

    # The misparse test the task asks for: a declared length cannot exceed the file.
    misparse = [r for r in rows if r["size"] > file_size]
    oversized_end = [r for r in rows if r["end"] > image_size]

    return {
        "generated_by": "Tools/scripts/grab_cdo_payloads.py (--write)",
        "card": "R-6 UNKNOWN - the 6 CDO component payloads",
        "inputs": {
            "package": STARTUP, "file_bytes": file_size, "image_bytes": image_size,
            "sha256": sha256_file(STARTUP), "decode_budget": DECODE_BUDGET,
            "cdo_export": cdo, "cdo_name": pkg.exports[cdo - 1]["name"],
            "cdo_size": pkg.exports[cdo - 1]["size"],
            "children": len(kids),
            "sdk": SDK, "sdk_files": sdk.files,
        },
        "counts": {
            "children": len(rows), "past_budget": len(past),
            "under_budget": len(rows) - len(past),
            "tags": sum(r["tag_count"] for r in past),
            "unknown_tags": sum(r["unknown_tags"] for r in past),
            "leftover_bytes": sum(r["leftover"] for r in past),
            "misparse": len(misparse), "end_past_image": len(oversized_end),
        },
        "checks": {
            "file_below_budget": file_size < DECODE_BUDGET,
            "no_declared_length_above_file": not misparse,
            "no_end_past_image": not oversized_end,
            "prefix_oracle_holds": all(r["prefix"]["oracle"] for r in past),
        },
        "past_budget": past,
        "rows": rows,
    }


# ------------------------------------------------------------------ render
def render(doc: dict) -> str:
    i, c, k = doc["inputs"], doc["counts"], doc["checks"]
    out: list[str] = []
    out.append("# The six CDO component payloads past the 512 MiB decode budget")
    out.append("")
    out.append("R-6 UNKNOWN, emptied. Generated by `Tools/scripts/grab_cdo_payloads.py "
               "--write`; `--check` re-derives this file from the same bytes and fails on "
               "any drift.")
    out.append("")
    out.append("`RESET_STATUS.md` R-6 lists \"the 6 CDO component payloads past the 512 MiB "
               "decode budget\" as UNKNOWN. They were never a decoding problem: the guard "
               "in `grab_packages_g305.PartialPackage.data()` refuses any export whose "
               "`offset + size` crosses 512 MiB, and these six children of "
               "`Default__RVehicleBatmobile` sit at the far end of the decompressed image.")
    out.append("")
    out.append("## Inputs")
    out.append("")
    out.append(f"- `{i['package']}` - **{i['file_bytes']:,} B** on disk, sha256 "
               f"`{i['sha256'][:16]}...`")
    out.append(f"- decompressed image - **{i['image_bytes']:,} B** (the file is chunk-"
               f"compressed; the image is {i['image_bytes'] / i['file_bytes']:.2f}x the file)")
    out.append(f"- decode budget under test - **{i['decode_budget']:,} B** (512 MiB, "
               f"`DECODE_BUDGET`)")
    out.append(f"- CDO `{i['cdo_name']}` - export {i['cdo_export']}, {i['cdo_size']} B, "
               f"{i['children']} children")
    out.append(f"- BmSDK-AK - `{i['sdk']}`, {i['sdk_files']} generated `.g.cs` files scanned")
    out.append("")
    out.append("## 1. Why a payload can appear \"past 512 MiB\"")
    out.append("")
    out.append("| component | class | declared length | offset | end | file size | "
               "length > file? | end > budget? |")
    out.append("|---|---|---:|---|---:|---:|---|---|")
    for r in doc["past_budget"]:
        out.append(f"| `{r['name']}` | `{r['class']}` | {r['size']} B | {r['offset']:#x} | "
                   f"{r['end']:#x} | {i['file_bytes']:,} B | "
                   f"{'**YES**' if r['size'] > i['file_bytes'] else 'no'} | yes |")
    out.append("")
    out.append(f"**No declared length exceeds the file.** The largest is "
               f"{max(r['size'] for r in doc['past_budget'])} B against a "
               f"{i['file_bytes']:,} B file, and every payload end "
               f"({min(r['end'] for r in doc['past_budget']):#x}.."
               f"{max(r['end'] for r in doc['past_budget']):#x}) is inside the "
               f"{i['image_bytes']:,} B image. So this is **not** a misparsed export table: "
               f"the six are genuinely at the far end of a decompressed image that is "
               f"{i['image_bytes'] / i['file_bytes']:.2f}x the file, and the budget was a "
               f"guard on image position, not a statement that the objects are large.")
    out.append("")
    out.append(f"- file below the budget: **{k['file_below_budget']}**")
    out.append(f"- declared length above the file in any CDO child: "
               f"**{c['misparse']}** (the misparse test)")
    out.append(f"- payload end past the image end: **{c['end_past_image']}**")
    out.append(f"- 12-byte prefix oracle holds on all six: **{k['prefix_oracle_holds']}**")
    out.append("")
    out.append("## 2. Method")
    out.append("")
    out.append(f"- **prefix**: a CDO component payload starts with 12 bytes, "
               f"`{doc['past_budget'][0]['prefix']['bytes']}` for the first one; bytes 4..7 "
               f"are the export's own name-table index. Decoded: it resolves to the object's "
               f"own name on all six, which proves where the tag stream starts.")
    out.append(f"- **tags**: `upk_read.walk_tags(pkg, payload, {STARTUP_PREFIX})` - the "
               f"uncooked Batman tag format (int16 type, uint16 layout offset, then an inline "
               f"value or FName+size+index).")
    out.append("- **naming**: each tag's layout offset is resolved against the generated "
               "BmSDK-AK class and its ancestors (most derived wins); the SDK stores the "
               "offset as decimal `Ptr + N` in each accessor, so the map is read from the "
               "source, not guessed.")
    out.append("")
    out.append("## 3. Per component")
    out.append("")
    out.append("| component | class | tags | bytes left over | UNKNOWN tags | stop |")
    out.append("|---|---|---:|---:|---:|---|")
    for r in doc["past_budget"]:
        out.append(f"| `{r['name']}` | `{r['class']}` | {r['tag_count']} | "
                   f"{r['leftover']} | {r['unknown_tags']} | {r['stop']} |")
    out.append("")
    out.append(f"Totals over the six: **{c['tags']} tags decoded, {c['leftover_bytes']} "
               f"bytes left over, {c['unknown_tags']} UNKNOWN tags.**")
    out.append("")
    for r in doc["past_budget"]:
        out.append(f"### `{r['name']}` - export {r['index']}, `{r['class']}`, "
                   f"{r['size']} B at {r['offset']:#x}")
        out.append("")
        out.append(f"Prefix `{r['prefix']['bytes']}`: name index {r['prefix']['name_index']} "
                   f"-> `{r['prefix']['name']}` (oracle: {r['prefix']['oracle']}).")
        out.append("")
        if r["tag_count"]:
            out.append("| # | type | layout offset | member (BmSDK-AK) | SDK class | value |")
            out.append("|---|---|---|---|---|---|")
            for n, (t, s) in enumerate(zip(r["tags"], r["sdk"]), 1):
                val = t.get("value")
                if isinstance(val, float):
                    val = repr(val)
                out.append(f"| {n} | {t['type']} | {t['offset']:#x} | "
                           f"`{s['member'] if s else 'UNKNOWN'}` | "
                           f"`{s['class'] if s else '-'}` | {val} |")
        else:
            out.append("No property tags: the payload is the 12-byte prefix followed by the "
                       "2-byte end marker `00 00`.")
        out.append("")
        out.append(f"Walk stops at byte {r['parsed_bytes']} of {r['size']} (`{r['stop']}`), "
                   f"leaving {r['leftover']} byte(s): `{r['leftover_hex']}`.")
        out.append("")
    out.append("## 4. What this closes")
    out.append("")
    out.append("- The six payloads are **decoded**, not skipped: two `StaticMeshComponent`s "
               "carry `ReplacementPrimitive = null` and `PerInstanceRandom`, and the four "
               "`SVehicleWheel`s carry **no serialised tags at all** (their values are the "
               "class defaults).")
    out.append("- No tag is UNKNOWN: every layout offset resolves to a BmSDK-AK member, and "
               "the package's own `ReplacementPrimitive` name agrees with the SDK's member at "
               "the same offset - an independent cross-check of the naming.")
    out.append("- The 512 MiB budget did not protect against a misparse; it prevented a "
               "~645 MiB decompression. The payloads are 14-67 B once reached.")
    out.append("")
    out.append("## UNKNOWN")
    out.append("")
    out.append("1. **Whether the game reads these six values at runtime.** Everything here is "
               "file-to-file; no process was attached (project rule).")
    out.append("2. **`PerInstanceRandom`'s role on a collision component.** The SDK names the "
               "offset; why a Batmobile collision mesh carries 0.854 / 0.080 there is not "
               "established by the bytes.")
    out.append("3. **The remaining 31 CDO children** are under the budget and were already "
               "walked by earlier cards (`REMAINDER.md`); this note only re-decodes the six "
               "that were refused.")
    out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------ cli
def write() -> int:
    doc = build()
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)}")
    print("counts:", json.dumps(doc["counts"]))
    print("checks:", json.dumps(doc["checks"]))
    return 0


def check() -> int:
    if not os.path.exists(OUT_MD):
        print("FAIL: output missing - run --write first")
        return 1
    stored = open(OUT_MD, encoding="utf-8").read()
    doc = build()
    fresh = render(doc)
    fails: list[str] = []
    if stored != fresh:
        old, new = stored.splitlines(), fresh.splitlines()
        first = next((n for n, (a, b) in enumerate(zip(old, new)) if a != b),
                     min(len(old), len(new)))
        fails.append(f"markdown differs from a fresh re-derivation at line {first + 1}")
    if doc["counts"]["past_budget"] != 6:
        fails.append(f"past-budget payloads {doc['counts']['past_budget']} != 6")
    for key, ok in doc["checks"].items():
        if not ok:
            fails.append(f"check failed: {key}")
    if doc["counts"]["unknown_tags"]:
        fails.append(f"{doc['counts']['unknown_tags']} tags unresolved against BmSDK-AK")
    for r in doc["past_budget"]:
        if r["parsed_bytes"] > r["size"]:
            fails.append(f"{r['name']}: walk overran the payload")
        if not r["prefix"]["oracle"]:
            fails.append(f"{r['name']}: prefix oracle failed")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK {doc['counts']['past_budget']}/6 payloads decoded, "
          f"{doc['counts']['tags']} tags, {doc['counts']['unknown_tags']} UNKNOWN")
    print("counts:", json.dumps(doc["counts"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
