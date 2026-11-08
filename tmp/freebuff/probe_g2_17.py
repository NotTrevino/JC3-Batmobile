#!/usr/bin/env python
"""G2-17 probe: independent census of `CForcePulse` straight from the cached Gibbed XML.

The card's script (`Tools/scripts/jc3forcepulse.py`) gets its members from
`jc3wiring.decode_epe`, i.e. the parsed `Obj.props`. This probe re-reads the same
`.xml` files with ElementTree and counts `<value>` elements directly, so the member
union / tune set / cross-references can be confirmed without trusting the parser
under test. It writes `tmp/freebuff/G2-17_probe.json` and prints a summary.
"""
from __future__ import annotations

import glob
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import jc3grab  # noqa: E402
import jc3index  # noqa: E402
import jc3detail  # noqa: E402
import jc3wiring  # noqa: E402

RAW = os.environ.get("JC3_RAW", r"E:/Modding/JustCause3/_grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
CACHE = os.path.join(RAW, "wiring", "epe")
OUT = os.path.join(ROOT, "tmp", "freebuff", "G2-17_probe.json")
SKIP = {"_class", "tags"}


def entities() -> list[str]:
    out = []
    for p in sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json"))):
        if p.endswith("detail_index.json"):
            continue
        with open(p, encoding="utf-8") as fh:
            out.append(json.load(fh).get("entity") or os.path.basename(p))
    return sorted(out)


def xml_for(ee: str, rows) -> str:
    slug = ee.rsplit("/", 1)[-1]
    path = os.path.join(CACHE, slug + ".xml")
    if not os.path.exists(path):
        jc3wiring.decode_epe(ee, rows, GAME)   # regenerates the cache file
    return path


def main() -> int:
    rows = jc3index.load_index(os.path.join(ROOT, "Research", "JC3Grab"))
    member_union = Counter()
    value_counts = Counter()
    tunes = Counter()
    names = Counter()
    refs = []
    ref_classes = Counter()
    pulses = 0
    per_entity = {}
    for ee in entities():
        tree = ET.parse(xml_for(ee, rows))
        root = tree.getroot()
        oid_cls = {}
        for obj in root.iter("object"):
            o = obj.find("./value[@name='_object_id']")
            c = obj.find("./value[@name='_class']")
            if o is not None:
                oid_cls[o.text or ""] = c.text if c is not None else ""
        found = []

        def cls_of(el):
            v = el.find("./value[@name='_class']")
            return v.text if v is not None else ""

        def walk(node, ancestors):
            for child in node:
                if child.tag != "object":
                    continue
                if cls_of(child) == "CForcePulse":
                    vals = [v for v in child if v.tag == "value"]
                    props = {}
                    for v in vals:
                        key = v.get("id") or v.get("name") or ""
                        props[key] = (v.text or "")
                        if key not in SKIP:
                            member_union[key] += 1
                    value_counts[len([k for k in props if k not in SKIP])] += 1
                    found.append({"oid": props.get("_object_id", ""),
                                  "name": props.get("name", ""),
                                  "settings": props.get("SettingsFile", ""),
                                  "props": props,
                                  "parent": ancestors[-1] if ancestors else None})
                    walk(child, ancestors + [props.get("name", "")])
                    continue
                walk(child, ancestors + [child.get("name", "")])

        walk(root, [])
        pulses += len(found)
        for f in found:
            names[f["name"]] += 1
            tunes[f["settings"]] += 1
            # what does id:D3DDD766 point at?
            tgt = f["props"].get("D3DDD766", "")
            if tgt in ("", "00000000"):
                ref_classes["(null)"] += 1
            else:
                hit = oid_cls.get(tgt)
                ref_classes[hit or "(not in graph)"] += 1
        if found:
            per_entity[ee] = len(found)

        # cross-references: any non-pulse value text containing a pulse oid
        oids = {f["oid"] for f in found if f["oid"] and f["oid"] != "00000000"}
        if not oids:
            continue
        for obj in root.iter("object"):
            if cls_of(obj) == "CForcePulse":
                continue
            c = obj.find("./value[@name='_class']")
            cname = c.text if c is not None else ""
            nm = obj.find("./value[@name='name']")
            nm = nm.text if nm is not None else ""
            for v in obj.findall("./value"):
                key = v.get("id") or v.get("name") or ""
                txt = v.text or ""
                for oid in oids:
                    if oid and oid in txt:
                        refs.append({"entity": ee, "class": cname, "object": nm,
                                     "member": key, "oid": oid,
                                     "is_owner_pointer": key == "B5AE7986"})

    doc = {
        "graphs": len(entities()),
        "entities_with_pulses": len(per_entity),
        "pulses": pulses,
        "member_union": dict(sorted(member_union.items())),
        "member_union_size": len(member_union),
        "value_counts_per_pulse": dict(sorted(value_counts.items())),
        "tunes": dict(sorted(tunes.items())),
        "tune_count": len(tunes),
        "names": dict(sorted(names.items())),
        "refs": refs,
        "refs_owner": sum(1 for r in refs if r["is_owner_pointer"]),
        "refs_other": sum(1 for r in refs if not r["is_owner_pointer"]),
        "d3ddd766_target_classes": dict(sorted(ref_classes.items())),
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"graphs {doc['graphs']} / with pulses {doc['entities_with_pulses']} / pulses {pulses}")
    print(f"member union {doc['member_union_size']}: {sorted(member_union)}")
    print(f"values per pulse (excluding _class/tags): {doc['value_counts_per_pulse']}")
    print(f"tunes {doc['tune_count']}")
    print(f"names {doc['names']}")
    print(f"refs owner-pointer {doc['refs_owner']} / other {doc['refs_other']}")
    for r in refs:
        if not r["is_owner_pointer"]:
            print("  other ref:", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
