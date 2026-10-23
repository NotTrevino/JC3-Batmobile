"""verify_install.py - read the INSTALLED .ee the way the game reads it, and prove the build is live.

Hashes prove "the right file was copied". They do not prove the game will read 19 materials, because
the game reads every inner file through the neighbouring `.ee.toc` (name -> offset, size). A build can
be hash-correct and still show the old car if a `.toc` record points at the vanilla bytes.

So this walks the deployed pair exactly like the engine:
  1. guards    installed .ee/.toc hashes equal the build's receipt
  2. baseline  the external/archives baseline (files the .toc sends to the archives) is bit-identical
               to the base build's: this build may not move or "fix" a module it did not intend to
  3. meshes    body LODs and wheel LODs decode THROUGH THEIR TOC RECORD: body 17 blocks, wheels 5
  4. bytes     every replaced mesh and added texture, read through the .toc, is byte-identical to the
               staged aaf copy - i.e. the engine will read the build, not the old bytes
  5. textures  every texture a decoded block references exists in the SARC at a real size AND is
               internal (nonzero .toc offset)
  6. report    block/material and texture inventories for the build record

    python Tools/scripts/verify_install.py --build Builds/test-078
    python Tools/scripts/verify_install.py --build Builds/test-078 --json Working/verify_078.json

Exit code is 1 if any check fails. Read-only: nothing in the game folder is written.
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))
import eetoc  # noqa: E402
import rbm_geom as R  # noqa: E402

EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
DEFAULT_EE = os.path.join(
    "D:\\Games\\Just Cause 3", "dropzone", "editor", "entities", "jc_vehicles", "01_land",
    "v0300_car_kensington_sportsmuscle", EE)

BODY_BLOCKS = 17
WHEEL_BLOCKS = 5
TEX_PREFIX = "textures/batmobile/"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True, help="Builds/<tag> whose receipt pins the install")
    ap.add_argument("--ee", default=DEFAULT_EE, help="installed .ee (default: the live dropzone path)")
    ap.add_argument("--json", help="also write the findings here")
    a = ap.parse_args()

    bdir = a.build if os.path.isabs(a.build) else os.path.join(ROOT, a.build)
    rec = json.load(open(os.path.join(bdir, "receipt.json")))
    checks = []

    def check(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))

    # 1. installed bytes == the build's own receipt
    ee_sha, toc_sha = sha256(a.ee), sha256(a.ee + ".toc")
    check("installed .ee matches receipt",
          ee_sha == rec["ee"]["sha256"].upper(), f"{ee_sha[:16]}...")
    check("installed .toc matches receipt",
          toc_sha == rec["toc"]["sha256"].upper(), f"{toc_sha[:16]}...")

    # 2. the .toc describes the .ee we just hashed, and the archives baseline did not move
    sarc = eetoc.unaaf(open(a.ee, "rb").read())
    real = {n: (o, s) for n, o, s in eetoc.sarc_dir(sarc)}
    toc = {n: (o, s) for n, o, s in eetoc.read_toc(open(a.ee + ".toc", "rb").read())}
    bad = {n for n in set(real) & set(toc) if real[n] != toc[n]}
    only_ee = set(real) - set(toc)

    bdir_base = os.path.join(ROOT, rec["base"])
    b_ee = os.path.join(bdir_base, EE)
    b_sarc = eetoc.unaaf(open(b_ee, "rb").read())
    b_real = {n: (o, s) for n, o, s in eetoc.sarc_dir(b_sarc)}
    b_toc = {n: (o, s) for n, o, s in eetoc.read_toc(open(b_ee + ".toc", "rb").read())}
    b_bad = {n for n in set(b_real) & set(b_toc) if b_real[n] != b_toc[n]}
    b_only_ee = set(b_real) - set(b_toc)
    check("external/archives baseline identical to the base build",
          bad == b_bad and only_ee == b_only_ee,
          f"{len(toc)} records; .toc->archives {len(bad)} (base {len(b_bad)}), "
          f"unlisted {len(only_ee)} (base {len(b_only_ee)}), "
          f"bytes moved: {sorted(bad ^ b_bad)[:3] or 'none'}")
    check("no file the base build listed went missing",
          not (set(b_toc) - set(toc)),
          f"{len(set(b_toc) - set(toc))} lost")

    def read_inner(name):
        """The bytes the engine would get for `name`: seek the .toc record, slice the SARC."""
        off, size = toc[name]
        if off + size > len(sarc):
            raise SystemExit(f"{name}: .toc says {off}+{size}, SARC is {len(sarc)} - out of bounds")
        return sarc[off:off + size]

    # 3. decode the meshes that carry the Batmobile, through their .toc records
    body = [n for n in toc if n.rsplit("/", 1)[-1].startswith("sportsmuscle_body_lod")]
    wheels = [n for n in toc if "sportsmuscle_wheel" in n and n.endswith(".rbm")]
    body_counts, wheel_counts, mats, tex_refs = {}, {}, {}, set()
    for n in sorted(body) + sorted(wheels):
        m = R.decode(read_inner(n))
        short = n.rsplit("/", 1)[-1]
        if n in body:
            body_counts[short] = len(m.blocks)
        else:
            wheel_counts[short] = len(m.blocks)
        for b in m.blocks:
            mats[R.BLOCK_NAMES.get(b.type_hash, hex(b.type_hash))] = \
                mats.get(R.BLOCK_NAMES.get(b.type_hash, hex(b.type_hash)), 0) + 1
            for t in getattr(b, "textures", []) or []:
                tex_refs.add(t)

    check(f"body LODs decode with {BODY_BLOCKS} blocks each",
          len(body) == 5 and all(v == BODY_BLOCKS for v in body_counts.values()),
          f"{len(body)} LODs {sorted(set(body_counts.values()))}")
    check(f"wheel meshes decode with {WHEEL_BLOCKS} blocks each",
          wheels and all(v == WHEEL_BLOCKS for v in wheel_counts.values()),
          f"{len(wheels)} files {sorted(set(wheel_counts.values()))}")

    # 4. the bytes the engine reads are the bytes this build staged
    aaf = os.path.join(bdir, "aaf")
    staged = sorted(body) + sorted(wheels)
    wrong = []
    for n in staged:
        p = os.path.join(aaf, *n.split("/"))
        if not os.path.exists(p):
            wrong.append(f"{n} (not in aaf)")
        elif read_inner(n) != open(p, "rb").read():
            wrong.append(n)
    check("every replaced mesh read via the .toc equals the staged aaf copy",
          not wrong, f"{len(staged)} meshes, {len(wrong)} differ")

    bm = sorted(t for t in tex_refs if TEX_PREFIX in t)
    tmissing = [t for t in bm if t not in real]
    tex_wrong = [t for t in bm if t in toc and os.path.exists(os.path.join(aaf, *t.split("/")))
                 and read_inner(t) != open(os.path.join(aaf, *t.split("/")), "rb").read()]
    in_aaf = [t for t in bm if os.path.exists(os.path.join(aaf, *t.split("/")))]
    check("every referenced batmobile texture is in the .ee, byte-identical to aaf",
          bm and not tmissing and not tex_wrong and len(in_aaf) == len(bm),
          f"{len(bm)} referenced, {len(tmissing)} missing, {len(tex_wrong)} differ, "
          f"{len(in_aaf)} staged")
    external = [t for t in bm if t in toc and toc[t][0] == 0]
    zero = [t for t in bm if t in real and real[t][1] == 0]
    check("all of them are internal (nonzero .toc offset), none empty",
          not external and not zero, f"{len(external)} external, {len(zero)} empty")

    # 5. inventory for the record
    print(f"\nbody block counts   : {json.dumps(body_counts, sort_keys=True)}")
    print(f"wheel block counts  : {len(wheel_counts)} files, "
          f"{sorted(set(wheel_counts.values()))} blocks")
    print(f"material blocks     : {json.dumps(mats, sort_keys=True)}")
    print(f"batmobile textures  : {len(bm)} distinct, "
          f"{sum(real[t][1] for t in bm if t in real) / 1024:.0f} KB")
    glass = [t for t in bm if "glass" in t or "window" in t]
    print(f"glass/transparent   : {glass or 'none referenced by the decoded blocks'}")

    ok = all(c[1] for c in checks)
    print(f"\n{'ALL CHECKS PASS' if ok else 'CHECKS FAILED'}  ({sum(c[1] for c in checks)}/{len(checks)})")
    if a.json:
        out = a.json if os.path.isabs(a.json) else os.path.join(ROOT, a.json)
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        json.dump({"build": rec.get("tag"), "ee": ee_sha, "toc": toc_sha,
                   "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks],
                   "body_blocks": body_counts, "wheel_blocks": wheel_counts,
                   "materials": mats, "textures": bm}, open(out, "w"), indent=1)
        print(f"wrote {os.path.relpath(out, ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
