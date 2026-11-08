"""bm_leaf.py - B-13b: give a built entity tree its own standalone leaf (D-6 = standalone).

D-6 (resolved 2026-10-28, user): a standalone entity, no Serpente replacement. Every build so far
ships the entity as the donor leaf `v0300_car_kensington_sportsmuscle_civilian_01`; the Rebel Drop
item (B-13) names `v0300_car_kensington_sportsmuscle_batmobile` (hash_jenkins 443190071).

What the files say a leaf is (evidence, all re-checked by --check):
  * the shipped convention: each of the donor's three vanilla leaves (`civilian_01`, `debug`,
    `signature_preorder`) ships `<leaf>.ee`, `.ee.toc`, `.epe`, `.stringlookup` under its own name
    (`Research/JC3Grab/INDEX.jsonl`), and the preorder `.epe` root carries `name` = its leaf and
    `name_hash` = hash_jenkins(leaf) (-1282903249);
  * inside a built `.ee`, exactly three inner files are named after the leaf (`.epe`,
    `.stringlookup`, `.ee.fmod_guids`), `@files.xml` lists them, and the only other occurrence of
    the leaf (string or 32-bit hash) in all 685 inner files is the `.epe` root's `name`/`name_hash`;
  * inner names are otherwise independent of the outer leaf (STANDALONE.md section 4.3), and the
    `.ee.toc` is optional (section 4.4: the shipped mod has 20 `.ee`, 0 `.toc`).

So the rename is: those three files, their `@files.xml` entries, and the `.epe` root's `name` and
`name_hash` - edited through `ConvertProperty` (the round trip B-05 proved), never by byte patch.
Nothing else changes: model bytes, textures and every other inner file are copied unchanged, so the
budgets are the input tree's (R9, reported, delta 0). The donor leaf is absent from the output, so
vanilla Serpentes stay vanilla; nothing is added to any traffic table (WLD-8).

UNKNOWN, not decided here: whether the game resolves a NEW leaf from the Rebel Drop item hash
(STANDALONE.md section 4) - the Q-1 probe.

Usage
    python Tools/scripts/bm_leaf.py --write [--src Builds/bm-005] [--tag bm-013b]
    python Tools/scripts/bm_leaf.py --check [--tag bm-013b]
As a module (B-14 applies it to the merged tree):
    bm_leaf.rename_tree(src_aaf, dst_aaf) -> dict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from rbmhdr import hash_jenkins  # noqa: E402

GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
CONV = os.path.join(GIBBED, "Gibbed.JustCause3.ConvertProperty.exe")
DIR = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
OLD = "v0300_car_kensington_sportsmuscle_civilian_01"
# Q-1a 2026-11-02: a NEW leaf never spawns (vanilla donor .ee+.toc at ..._batmobile: empty drop). The dropzone
# only overrides paths the archives already hold; every Rebel Drop mod addition (goat, pinata, tank_wreck...)
# is an existing leaf, most with no registry record. So the Batmobile takes the unused vanilla leaf
# ..._debug (base archive; debug proto tables only: no traffic, not in the vanilla drop menu).
NEW = "v0300_car_kensington_sportsmuscle_debug"
INNER = [".epe", ".stringlookup", ".ee.fmod_guids"]
TAG = "bm-013b"                 # --tag writes the same rename into another build line
OUT = os.path.join(ROOT, "Builds", TAG)


def receipt_file() -> str:
    """Where this tree's leaf record lives.

    bm-013b's tree is leaf-only and keeps receipt.json; a combined line (bm-RC4-rebel) also holds
    bm_rebel's receipt.json in the same folder, so the leaf record sits beside it.
    """
    if TAG == "bm-013b":
        return os.path.join(OUT, "receipt.json")
    return os.path.join(OUT, "receipt-leaf.json")
WORK = os.environ.get("JC3_RAW", "E:/Modding/_shared/gamedata/JC3grab") + "/b13b"   # scratch XML, outside the repo


def s32(v: int) -> int:
    return v - (1 << 32) if v >= 1 << 31 else v


def sha(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def conv(*a: str) -> None:
    r = subprocess.run([CONV, *a], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ConvertProperty {a[0]} failed: {(r.stdout + r.stderr)[-800:]}")


def leaf_hits(aaf: str, leaf: str) -> list[str]:
    """Every inner file whose NAME or BYTES carry the leaf (string or 32-bit hash)."""
    hb = hash_jenkins(leaf.encode()).to_bytes(4, "little")
    out = []
    for dp, _, fs in os.walk(aaf):
        for f in fs:
            p = os.path.join(dp, f)
            r = os.path.relpath(p, aaf).replace("\\", "/")
            if leaf in r:
                out.append("name:" + r)
            b = open(p, "rb").read()
            if leaf.encode() in b or (f != "@files.xml" and hb in b):
                out.append("bytes:" + r)
    return sorted(set(out))


def root_fields(xml: str) -> dict:
    t = open(xml, encoding="utf-8").read()
    n = re.search(r'<value name="name" type="string">([^<]*)</value>', t)
    h = re.search(r'<value name="name_hash" type="int">(-?\d+)</value>', t)
    return {"name": n.group(1) if n else None, "name_hash": int(h.group(1)) if h else None}


def rename_tree(src: str, dst: str) -> dict:
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    os.makedirs(WORK, exist_ok=True)
    for ext in INNER:
        a, b = os.path.join(dst, DIR + OLD + ext), os.path.join(dst, DIR + NEW + ext)
        if not os.path.exists(a):
            raise SystemExit(f"missing in the source tree: {DIR + OLD + ext}")
        os.rename(a, b)
    fx = os.path.join(dst, "@files.xml")
    t = open(fx, encoding="utf-8-sig").read()
    n_fx = t.count(OLD)
    open(fx, "w", encoding="utf-8-sig", newline="\n" if "\r\n" not in t else "").write(t.replace(OLD, NEW))
    epe = os.path.join(dst, DIR + NEW + ".epe")
    x_in, x_out, x_rt = (os.path.join(WORK, n) for n in ("leaf_in.xml", "leaf_out.xml", "leaf_rt.xml"))
    conv("--e", epe, x_in)
    before = root_fields(x_in)
    if before != {"name": OLD, "name_hash": s32(hash_jenkins(OLD.encode()))}:
        raise SystemExit(f"the .epe root is not the donor's: {before}")
    t = open(x_in, encoding="utf-8").read()
    t2 = t.replace(f'<value name="name" type="string">{OLD}</value>',
                   f'<value name="name" type="string">{NEW}</value>', 1)
    t2 = t2.replace(f'<value name="name_hash" type="int">{before["name_hash"]}</value>',
                    f'<value name="name_hash" type="int">{s32(hash_jenkins(NEW.encode()))}</value>', 1)
    open(x_out, "w", encoding="utf-8").write(t2)
    conv("-i", x_out, epe)
    conv("--e", epe, x_rt)
    rt = open(x_rt, encoding="utf-8").read()
    changed = [i for i, (p, q) in enumerate(zip(t.splitlines(), rt.splitlines())) if p != q]
    return {"src": os.path.relpath(src, ROOT).replace("\\", "/"),
            "dst": os.path.relpath(dst, ROOT).replace("\\", "/"),
            "renamed": [DIR + OLD + e + " -> " + DIR + NEW + e for e in INNER],
            "files_xml_entries": n_fx,
            "epe_before": before, "epe_after": root_fields(x_rt),
            "xml_lines": len(t.splitlines()), "xml_lines_rt": len(rt.splitlines()),
            "xml_lines_changed": changed, "epe_sha256": sha(epe)}


def pack(aaf: str, ee: str) -> None:
    for exe, a, b in (("SmallPack", aaf, ee), ("SmallUnpack", ee, ee + ".verify")):
        if exe == "SmallUnpack" and os.path.exists(b):
            shutil.rmtree(b)
        r = subprocess.run([os.path.join(GIBBED, f"Gibbed.JustCause3.{exe}.exe"), a, b],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"{exe} failed: {(r.stdout + r.stderr)[-400:]}")


def verify_manifest(aaf: str) -> dict:
    fx = open(os.path.join(aaf, "@files.xml"), encoding="utf-8-sig").read()
    listed = set(re.findall(r'name="([^"]+)"', fx))
    on_disk = {os.path.relpath(os.path.join(dp, n), aaf).replace("\\", "/")
               for dp, _, fs in os.walk(aaf) for n in fs if n != "@files.xml"}
    return {"dangling": sorted(listed - on_disk), "unlisted": sorted(on_disk - listed)}


def verify(aaf: str, src_aaf: str) -> dict:
    """The four acceptance checks, as data."""
    new_epe = os.path.join(aaf, DIR + NEW + ".epe")
    x = os.path.join(WORK, "leaf_check.xml")
    conv("--e", new_epe, x)
    f = root_fields(x)
    old_hits, new_hits = leaf_hits(aaf, OLD), leaf_hits(aaf, NEW)
    fx = open(os.path.join(aaf, "@files.xml"), encoding="utf-8-sig").read()
    listed = re.findall(r'name="([^"]+)"', fx)
    on_disk = sorted(os.path.relpath(os.path.join(dp, n), aaf).replace("\\", "/")
                     for dp, _, fs in os.walk(aaf) for n in fs if n != "@files.xml")
    same = 0; diff = []
    for r in on_disk:
        q = r.replace(NEW, OLD)
        a, b = os.path.join(aaf, r), os.path.join(src_aaf, q)
        if os.path.exists(b) and sha(a) == sha(b):
            same += 1
        else:
            diff.append(r)
    return {"epe_decodes": True, "epe_root": f,
            "epe_root_ok": f == {"name": NEW, "name_hash": s32(hash_jenkins(NEW.encode()))},
            "donor_leaf_refs": old_hits,
            "new_leaf_refs": new_hits,
            "files_xml_listed": len(listed), "files_on_disk": len(on_disk),
            "dangling": sorted(set(listed) - set(on_disk)),
            "unlisted": sorted(set(on_disk) - set(listed)),
            "unchanged_vs_src": same, "changed_vs_src": diff}


def main() -> int:
    global TAG, OUT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tag", default=TAG, help="build tag to write/check (default bm-013b)")
    ap.add_argument("--src", default=None,
                    help="source build (default Builds/bm-005 on --write; the receipt's base on --check)")
    a = ap.parse_args()
    if a.tag != TAG:
        TAG = a.tag
        OUT = os.path.join(ROOT, "Builds", TAG)
    if a.check and not a.src:
        rp = receipt_file()
        a.src = json.load(open(rp))["base"] if os.path.exists(rp) else "Builds/bm-005"
    a.src = a.src or "Builds/bm-005"
    src_tag = os.path.join(ROOT, a.src)
    src_aaf, dst_aaf = os.path.join(src_tag, "aaf"), os.path.join(OUT, "aaf")
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        res = rename_tree(src_aaf, dst_aaf)
        ee = os.path.join(OUT, NEW + ".ee")
        pack(dst_aaf, ee)
        v = verify(dst_aaf, src_aaf)
        vv = verify(ee + ".verify", src_aaf)
        base = json.load(open(os.path.join(src_tag, "receipt.json"))) if os.path.exists(
            os.path.join(src_tag, "receipt.json")) else {}
        rec = {"schema": 1, "card": "B-13b", "tag": TAG, "base": a.src, "leaf": NEW,
               "leaf_hash": hash_jenkins(NEW.encode()), "donor_leaf": OLD,
               "donor_hash": hash_jenkins(OLD.encode()), "rename": res,
               "ee": {"file": os.path.relpath(ee, ROOT).replace("\\", "/"), "sha256": sha(ee),
                      "bytes": os.path.getsize(ee)},
               "check_tree": v, "check_packed": vv,
               "budgets": {"inherited_from": a.src, "delta_kb": 0,
                           "base": base.get("budgets", "not in the base receipt"),
                           "note": "rename only: no model or texture bytes change (R9 figure is the base's)"},
               "toc": "not written: optional (STANDALONE.md 4.4); B-14 writes the RC's .toc",
               "unknown": ["whether the game resolves a NEW leaf from the Rebel Drop item hash (Q-1)"]}
        json.dump(rec, open(receipt_file(), "w"), indent=1)
        shutil.rmtree(ee + ".verify", ignore_errors=True)
        print(json.dumps({k: rec[k] for k in ("leaf", "leaf_hash", "ee")}, indent=1))
    if a.check or a.write:
        rec = json.load(open(receipt_file()))
        v = verify(dst_aaf, src_aaf)
        # The manifest gaps are the SOURCE's (bm-005: 19 size-only shared-texture lines, 4 wheel lod4/5
        # .rbm on disk but unlisted): this card must add none, so compare against the source's own.
        sv = verify_manifest(src_aaf)
        new_dangling = sorted(set(v["dangling"]) - {d.replace(OLD, NEW) for d in sv["dangling"]})
        new_unlisted = sorted(set(v["unlisted"]) - {d.replace(OLD, NEW) for d in sv["unlisted"]})
        print(f"    source manifest gaps (inherited, not this card's): dangling {len(sv['dangling'])}, "
              f"unlisted {sv['unlisted']}")
        ok = (v["epe_root_ok"] and not v["donor_leaf_refs"] and not new_dangling and not new_unlisted
              and v["changed_vs_src"] == [DIR + NEW + ".epe"]
              and rec["ee"]["sha256"] == sha(os.path.join(OUT, NEW + ".ee")))
        print(f"(1) epe {DIR + NEW}.epe decodes: root {v['epe_root']} ok={v['epe_root_ok']}")
        print(f"(2) NEW dangling {len(new_dangling)} | NEW unlisted {len(new_unlisted)} | "
              f"@files.xml {v['files_xml_listed']} = on disk {v['files_on_disk']} | "
              f"donor-leaf refs {len(v['donor_leaf_refs'])} | new-leaf refs {v['new_leaf_refs']}")
        print(f"(3) vs {a.src}: {v['unchanged_vs_src']} files byte-identical, changed {v['changed_vs_src']}")
        print(f"(4) budgets: inherited from {rec['budgets']['inherited_from']}, delta 0 KB "
              f"(base model {rec['budgets']['base'].get('model_kb') if isinstance(rec['budgets']['base'], dict) else '?'} KB)")
        print(("PASS" if ok else "FAIL") + f": {TAG} leaf {NEW} ({hash_jenkins(NEW.encode())})")
        return 0 if ok else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
