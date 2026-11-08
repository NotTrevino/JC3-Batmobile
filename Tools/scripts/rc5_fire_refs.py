#!/usr/bin/env python3
"""rc5_fire_refs.py - settle the four dangling `F30CCB1C` owner links for the RC5 merge.

`Tools/scripts/v03_wiring_rc4.py` G2 reports four occurrences of
`4DAE31AE=FFFF05DA` that resolve to no object in `Builds/bm-RC4`.  This tool decides,
from bytes, what each occurrence is and emits the edit list the later 3-way `.epe`
merge applies.

What the bytes say
------------------
* The carrier is **not** an `SAttachedEffect` and **not** one of the three extra
  `CCar` roots.  `F30CCB1C` is a direct member of each of the four inlined
  `CBulletWeaponBase` objects (`w602_mediumtank_canon`, `w603_mediumtank_mgun`,
  `w618_sportsmuscle_missile`, `w618_sportsmuscle_missile_emp`), i.e. the weapon's
  **owner link** to the vehicle root that owns it.
* `4DAE31AE=FFFF05DA` is defined as the `CCar` root of the **APC's own** `.epe`
  (`E:/Modding/_shared/gamedata/JC3grab/epe_schema/apc_debug.epe`), whose weapon
  `w206_mounted_capstone_m2hm` carries that same self-reference.  B-05 cloned the APC
  weapon and copied the owner link into a graph where that object does not exist.
* The vanilla donor graph has **no** `F30CCB1C` member at all.  The medium-tank
  weapon names these clones carry, the preorder Serpente, and `Builds/bm-RC3`
  (B-16 already applied) all leave the link **null**.

The edit is therefore the B-16 cleanup, not a clone and not a gate change: set the
four owner links to null (`00000000=00000000`, 8 zero bytes each).  Nothing is cloned
under the three roots, and the gate keeps its rule.

Output (only this file):

    Builds/bm-RC5-entity/fire_refs.json

`Builds/bm-RC4` is read, never written.  `--write` emits the edit list; `--check`
re-runs the G2 logic of `v03_wiring_rc4.py` over the patched members and requires zero
dangling, and re-emits the JSON to compare byte for byte.

Usage:
    python Tools/scripts/rc5_fire_refs.py --write
    python Tools/scripts/rc5_fire_refs.py --check
"""
from __future__ import annotations

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

TAG = "bm-RC5-entity"
RC4 = "Builds/bm-RC4"
SOURCE = os.path.join(RC4, "aaf/editor/entities/jc_vehicles/01_land/"
                           "v0300_car_kensington_sportsmuscle/"
                           "v0300_car_kensington_sportsmuscle_debug.epe")
DONOR = ("Builds/bm-RC4-base/aaf/editor/entities/jc_vehicles/01_land/"
         "v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_civilian_01.epe")
APC = r"E:\Modding\_shared\gamedata\JC3grab\epe_schema\apc_debug.epe"
OUT_DIR = os.path.join(ROOT, "Builds", TAG)
OUT = os.path.join(OUT_DIR, "fire_refs.json")

CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")

BAD = "4DAE31AE=FFFF05DA"
NULL = "00000000"
MEMBER = "F30CCB1C"

# The same two patterns v03_wiring_rc4.py uses for G2.
OBJ_RE = re.compile(r'<value (?:id|name)="([^"]+)" type="objectid">'
                    r'([0-9A-Fa-f]+=[0-9A-Fa-f]+)<')
ID_RE = re.compile(r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<')

# Files whose definition of the target id was searched (each read-only).
TARGET_FILES = [
    ("source", SOURCE),
    ("donor", DONOR),
    ("apc", APC),
    ("rc3", "Builds/bm-RC3/aaf/editor/entities/jc_vehicles/01_land/"
            "v0300_car_kensington_sportsmuscle/"
            "v0300_car_kensington_sportsmuscle_debug.epe"),
    ("bm-008", "Builds/bm-008/aaf/editor/entities/jc_vehicles/01_land/"
               "v0300_car_kensington_sportsmuscle/"
               "v0300_car_kensington_sportsmuscle_civilian_01.epe"),
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rel(p: str) -> str:
    return p.replace("\\", "/")


def to_xml(blob: bytes, tmp: str, name: str) -> str:
    """Convert one .epe blob to XML in a temp dir; returns the text."""
    e = os.path.join(tmp, name + ".epe")
    x = os.path.join(tmp, name + ".xml")
    with open(e, "wb") as f:
        f.write(blob)
    r = subprocess.run([CONV, "--e", e, x], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ConvertProperty --e failed on %s: %s" % (name, r.stderr.strip()))
    with open(x, encoding="utf-8-sig") as f:
        text = f.read()
    os.remove(e)
    os.remove(x)
    return text


def xml_file(path: str, tmp: str, name: str) -> str:
    with open(path, "rb") as f:
        return to_xml(f.read(), tmp, name)


def head_of(lines: list[str], n: int) -> str:
    """The object's own header: its `<object>` line plus the following `<value>` lines.

    Stops at the next `<object>`/`</object>` so a fixed-width window cannot read a
    sibling object's `_class`/`_object_id` (which made the container read as `CCar`
    and mislabelled each weapon's parent).
    """
    out = [lines[n - 1]]
    for ln in lines[n:]:
        s = ln.lstrip()
        if s.startswith("<object") or s.startswith("</object>"):
            break
        out.append(ln)
    return "\n".join(out)


def object_chain(xml: str) -> list[dict]:
    """Every object with depth, class, name, _object_id and its enclosing chain."""
    lines = xml.splitlines()
    out, stack = [], []
    for n, ln in enumerate(lines, 1):
        m = re.match(r"^(\t*)<object", ln)
        if m:
            o = {"line": n, "depth": len(m.group(1)),
                 "parent": stack[-1] if stack else None}
            head = head_of(lines, n)
            cls = re.search(r'name="_class" type="string">([^<]+)<', head)
            nm = re.search(r'name="name" type="string">([^<]*)<', head)
            oid = ID_RE.search(head)
            o["class"] = cls.group(1) if cls else None
            o["name"] = nm.group(1) if nm else None
            o["oid"] = oid.group(1) if oid else None
            out.append(o)
            stack.append(o)
            continue
        m = re.match(r"^(\t*)</object>", ln)
        if m and stack and len(m.group(1)) == stack[-1]["depth"]:
            stack.pop()
    return out


def member_values(xml: str) -> list[tuple[int, str]]:
    """(xml line, value) for every `F30CCB1C` objectid member, in document order."""
    out = []
    for n, ln in enumerate(xml.splitlines(), 1):
        m = re.search(r'<value id="%s" type="objectid">([^<]+)<' % MEMBER, ln)
        if m:
            out.append((n, m.group(1)))
    return out


def g2(xml: str, donor_xml: str) -> dict:
    """The exact G2 rule of v03_wiring_rc4.py, returned as counts + dangling rows."""
    ids = {m.upper() for m in ID_RE.findall(xml)}
    refs = [(k, v) for k, v in OBJ_RE.findall(xml)
            if k != "_object_id" and not v.startswith("00000000")]
    v_ids = {m.upper() for m in ID_RE.findall(donor_xml)}
    ext = set()
    for k, v in OBJ_RE.findall(donor_xml):
        if k == "_object_id" or v.startswith("00000000") or v.upper() in v_ids:
            continue
        ext.add(v.upper().split("=", 1)[-1] if v.count("=") == 2 else v.upper())
    tail = lambda v: v.upper().split("=", 1)[-1] if v.count("=") == 2 else v.upper()
    bad = [(k, v) for k, v in refs if v.upper() not in ids and tail(v) not in ext]
    return {"objects": len(ids), "refs": len(refs), "donor_external_tails": len(ext),
            "dangling": len(bad),
            "rows": [{"member": k, "value": v} for k, v in bad]}


def patch(blob: bytes, offset: int) -> bytes:
    return blob[:offset] + b"\x00" * 8 + blob[offset + 8:]


def build() -> dict:
    src = open(SOURCE, "rb").read()
    tmp = tempfile.mkdtemp(prefix="rc5fire_")
    try:
        xml = to_xml(src, tmp, "src")
        donor_xml = xml_file(DONOR, tmp, "donor")
        apc_xml = xml_file(APC, tmp, "apc") if os.path.exists(APC) else None

        # ---- every carrier of the member, in document order
        stack, found = [], []
        lines = xml.splitlines()
        for n, ln in enumerate(lines, 1):
            m = re.match(r"^(\t*)<object", ln)
            if m:
                head = head_of(lines, n)
                cls = re.search(r'name="_class" type="string">([^<]+)<', head)
                nm = re.search(r'name="name" type="string">([^<]*)<', head)
                oid = ID_RE.search(head)
                stack.append({"depth": len(m.group(1)),
                              "class": cls.group(1) if cls else None,
                              "name": nm.group(1) if nm else None,
                              "oid": oid.group(1) if oid else None})
                continue
            mm = re.search(r'<value id="%s" type="objectid">([^<]+)<' % MEMBER, ln)
            if mm:
                found.append({"xml_line": n, "value": mm.group(1),
                              "carrier": {k: v for k, v in stack[-1].items()
                                          if k != "depth"} if stack else None,
                              "chain": [s["class"] for s in stack],
                              "ancestors": [{"class": s["class"], "name": s["name"],
                                             "oid": s["oid"]} for s in stack[:-1]]})
            m = re.match(r"^(\t*)</object>", ln)
            if m and stack and len(m.group(1)) == stack[-1]["depth"]:
                stack.pop()

        # ---- packed occurrences of the bad id, in file order
        packed = struct.pack("<II", 0x4DAE31AE, 0xFFFF05DA)
        offsets, i = [], src.find(packed)
        while i >= 0:
            offsets.append(i)
            i = src.find(packed, i + 1)

        bad_idx = [j for j, m in enumerate(found) if m["value"] == BAD]
        bad_members = [found[j] for j in bad_idx]
        if len(offsets) != len(bad_members):
            raise SystemExit("packed occurrences %d != XML members %d (values %s)"
                             % (len(offsets), len(bad_members),
                                [m["value"] for m in found]))

        # ---- prove offset -> carrier by patching one occurrence at a time.
        # The packed order is not the XML document order, so the mapping is measured
        # rather than assumed: each offset must turn exactly one member null, and the
        # four mappings must be a bijection onto the four bad members.
        by_member, rank = {}, {}
        for k, off in enumerate(offsets):
            one = to_xml(patch(src, off), tmp, "p%d" % k)
            vals = [v for _l, v in member_values(one)]
            changed = [j for j, (a, b) in enumerate(zip([m["value"] for m in found], vals))
                       if a != b]
            if len(changed) != 1:
                raise SystemExit("patching 0x%x changed members %s, expected exactly one "
                                 "(all members %s)"
                                 % (off, changed, [m["value"] for m in found]))
            j = changed[0]
            if j in by_member:
                raise SystemExit("packed offsets 0x%x and 0x%x both patch member %d"
                                 % (by_member[j], off, j))
            by_member[j] = off
            rank[j] = k
        if sorted(by_member) != bad_idx:
            raise SystemExit("offsets patch members %s, bad members are %s"
                             % (sorted(by_member), bad_idx))

        occurrences = []
        for k, j in enumerate(bad_idx):
            off = by_member[j]
            m = bad_members[k]
            c = m["carrier"] or {}
            occurrences.append({
                "index": k,
                "member": MEMBER,
                "offset": off,
                "offset_hex": "0x%x" % off,
                "carrier_class": c.get("class"),
                "carrier_name": c.get("name"),
                "carrier_object_id": c.get("oid"),
                "xml_line": m["xml_line"],
                "packed_rank": rank[j],
                "chain": m["chain"],
                "ancestors": m["ancestors"],
                "old_value": BAD,
                "new_value": NULL,
                "verdict": "real_defect",
                "why": ("owner link on a cloned CBulletWeaponBase: the target is the APC "
                        "entity's own CCar root, which this graph does not define; the "
                        "medium-tank / Serpente / RC3 convention is null"),
                "proved_by": "patching this offset alone turns exactly this member null",
            })

        # ---- who defines the target, and what each build left in the member
        defs, members_by_file = [], {}
        for label, path in TARGET_FILES:
            text = {"source": xml, "donor": donor_xml, "apc": apc_xml}.get(label)
            if label == "apc" and apc_xml is None:
                defs.append({"file": rel(path), "label": label, "read": False,
                             "defines": None, "values": []})
                continue
            if text is None:
                if not os.path.exists(path):
                    defs.append({"file": rel(path), "label": label, "read": False,
                                 "defines": None, "values": []})
                    continue
                text = xml_file(path, tmp, label.replace("-", ""))
            members_by_file[label] = sorted({v for _l, v in member_values(text)})
            roots = [o for o in object_chain(text) if o["class"] == "CCar"]
            root = next((o for o in roots if o["oid"] == BAD), None)
            defs.append({"file": rel(path), "label": label, "read": True,
                         "defines": root is not None,
                         "class": root["class"] if root else None,
                         "name": root["name"] if root else None,
                         "values": members_by_file[label]})

        # ---- G2 before / after
        before = g2(xml, donor_xml)
        patched = src
        for off in offsets:
            patched = patch(patched, off)
        after = g2(to_xml(patched, tmp, "patched"), donor_xml)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if after["dangling"]:
        raise SystemExit("patched graph still dangles: %s" % after["rows"])

    return {
        "schema": 1,
        "card": "RC5",
        "purpose": "settle the four dangling F30CCB1C owner links before the 3-way .epe merge",
        "source": {"path": rel(SOURCE), "sha256": sha(src), "bytes": len(src),
                   "writes": False},
        "member": MEMBER,
        "target": {
            "value": BAD,
            "defined_in_source": False,
            "definitions": defs,
        },
        "occurrences": occurrences,
        "edit_list": [{
            "file": rel(SOURCE),
            "offset": o["offset"],
            "offset_hex": o["offset_hex"],
            "length": 8,
            "from_hex": struct.pack("<II", 0x4DAE31AE, 0xFFFF05DA).hex(),
            "to_hex": "0000000000000000",
            "from_value": BAD,
            "to_value": NULL,
            "carrier_class": o["carrier_class"],
            "carrier_name": o["carrier_name"],
        } for o in occurrences],
        "g2": {"before": before, "after": after,
               "rule": "v03_wiring_rc4.py G2: every non-null objectid resolves locally or "
                       "is a cross-file tail the donor .epe also makes"},
        "precedent": {
            "donor_member_count": len(member_values(donor_xml)),
            "donor_values": members_by_file.get("donor", []),
            "rc3_values": members_by_file.get("rc3", []),
            "bm008_values": members_by_file.get("bm-008", []),
            "b16": "MODLOG 2026-10-31 / GRAB_BACKLOG B-16: 4 owner links -> null, "
                   "medium-tank + preorder Serpente convention",
            "apc_self_reference": members_by_file.get("apc", []),
        },
        "counts": {"occurrences": len(occurrences),
                   "real_defects": sum(1 for o in occurrences if o["verdict"] == "real_defect"),
                   "false_positives": sum(1 for o in occurrences
                                          if o["verdict"] == "false_positive"),
                   "edits": len(occurrences),
                   "dangling_before": before["dangling"],
                   "dangling_after": after["dangling"]},
        "never_written": [rel(RC4)],
        "verdict": "PASS" if after["dangling"] == 0 else "FAIL",
    }


def dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def main(write: bool) -> int:
    doc = build()
    text = dump(doc)
    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s" % rel(OUT))
        print("%d occurrences, %d real defect(s), %d false positive(s); G2 dangling %d -> %d"
              % (doc["counts"]["occurrences"], doc["counts"]["real_defects"],
                 doc["counts"]["false_positives"], doc["counts"]["dangling_before"],
                 doc["counts"]["dangling_after"]))
        for o in doc["occurrences"]:
            print("  %s %-26s %s  %s -> %s" % (o["offset_hex"], o["carrier_name"],
                                               o["carrier_class"], o["old_value"],
                                               o["new_value"]))
        return 0

    if not os.path.exists(OUT):
        print("MISSING %s" % rel(OUT))
        return 1
    stored = open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    ok = stored == text
    if not ok:
        print("DIFFERS: regenerated %d bytes, stored %d" % (len(text), len(stored)))
    if doc["g2"]["after"]["dangling"]:
        print("FAIL: patched graph still has %d dangling" % doc["g2"]["after"]["dangling"])
        ok = False
    print("%s: %d occurrences, G2 dangling %d -> %d, edit list %s"
          % ("OK" if ok else "BAD", doc["counts"]["occurrences"],
             doc["counts"]["dangling_before"], doc["counts"]["dangling_after"],
             "matches" if ok else "differs"))
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: rc5_fire_refs.py --write|--check")
    raise SystemExit(main(sys.argv[1] == "--write"))
