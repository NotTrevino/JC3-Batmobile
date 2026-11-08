"""bm_rebel.py - B-13: the Batmobile's Rebel Drop entry, name, icon and unlock (D-6 = standalone).

Card (GRAB_BACKLOG.md B-13): add the "Batmobile" entry per REBELDROP.md; strings and icon per
NAMES.md; standalone entity path per D-6. Done: decoded item.onlinec/task.onlinec show the new
entries; the entity paths they name exist in the build.

Inputs (all read from the PATCH layer through the index; outputs only under Builds/bm-013, R7/R10):
  profile/item.onlinec       196 items; the donor is the item whose Name = hash(donor leaf)
  profile/task.onlinec       591 tasks; the donor unlocks through task 1361701860 threshold[0]
  profile/online.stringlookup  11 languages (written by jc3strings_write, never ConvertAdf)
  textures/ui/vehicle_icons/<donor leaf>.ddsc   the icon, byte-copied under the new leaf (T-WLD5)
  Builds/bm-013b             the standalone entity (B-13b) whose leaf the item names

What is written, and the evidence for each choice (R4):
  item   one 128 B record cloned from the donor (every field kept unless listed):
           Name, UIName  = hash(leaf) 443190071          vanilla: UIName = Name = hash(leaf)
           UIDescription = hash(leaf + "_desc")          vanilla: donor 2073308658 = hash(donor_desc)
           UIDisplayOrder = 12                           jc3rebeldrop recipe.free_order (max+1)
           UIImagePath   = the new leaf                  icon copied to vehicle_icons/<leaf>.ddsc
           UIVideoPath   = the DONOR's string (kept)     no video asset exists for the new leaf;
                                                         a missing video path is UNKNOWN in the UI
         appended after the 196 records (the array is not sorted by Name: checked at run time);
         string-hash table gains <leaf> and <leaf>_desc, as the vanilla table carries both.
  task   one ItemReward (1, 0, 1, 0 - the starters' own values) appended to the REPEATABLE reward of
         task 1980624442 (type 100): vanilla's own starter grant - its repeatable reward hands out the
         vehicles every save has from the start (oldjeep/technical/oldtruck rebel, fishing boat, bus
         heli, private plane) plus starter weapons.
         Q-1a history: (1) ItemReward on the donor's unlock (task 1361701860 threshold[0], "bring to
         garage"): LOCKED on a save that had already passed it. (2) no reward at all (shipped mod's
         pattern, REBELDROP.md s6): "Err: No Valid locking reason" - the menu needs a granting task.
  text   two pairs in all 11 languages: hash(leaf) -> NAME, hash(leaf_desc) -> BLURB (English in every
         language: no translations exist; the user can change both in Working/World/bm_rebel_text.json).

UNKNOWN (Q-1): whether the menu resolves a NEW leaf from the item hash; whether a save that already
unlocked the Serpente grants the new reward; how the UI treats the donor video for this entry.

Usage
    python Tools/scripts/bm_rebel.py --write [--tag bm-RC4-rebel]
    python Tools/scripts/bm_rebel.py --check [--tag bm-RC4-rebel]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from rbmhdr import hash_jenkins  # noqa: E402
import adf_append  # noqa: E402
import jc3strings_write  # noqa: E402

DONOR = "v0300_car_kensington_sportsmuscle_civilian_01"
import bm_leaf  # noqa: E402
LEAF = bm_leaf.NEW            # the existing vanilla leaf the Batmobile occupies (bm_leaf.py)
CATEGORY = (7, 1492769243)    # UIFlag + UIFlagDescription of vanilla group 7 (armoredjeep, armoredtransport,
                              # technicaljeep, buggy rebel): "military" (user 2026-11-02); donor's 5 = sports
UNLOCK_TASK = 1361701860      # the donor's own unlock (not used for the Batmobile, see docstring)
STARTER_TASK = 1980624442     # type 100; its repeatable reward is vanilla's starter grant
FREE_ORDER = 12
TAG = "bm-013"
ENTITY_TAG_NAME = "bm-013b"     # the B-13b tree that ships the standalone entity
OUT = os.path.join(ROOT, "Builds", TAG)
DROP = os.path.join(OUT, "drop")
TEXT = os.path.join(ROOT, "Working", "World", "bm_rebel_text.json")
ENTITY_TAG = os.path.join(ROOT, "Builds", ENTITY_TAG_NAME)


def set_tags(tag: str, entity_tag: str | None = None) -> None:
    """--tag / --entity-tag: write the same drop into another build line.

    A refreshed line (bm-RC4-rebel) keeps both outputs in one tree, so its entity tag defaults to
    the drop tag; the bm-013 default keeps its own bm-013b entity tree.
    """
    global TAG, OUT, DROP, ENTITY_TAG
    TAG = tag
    OUT = os.path.join(ROOT, "Builds", TAG)
    DROP = os.path.join(OUT, "drop")
    ENTITY_TAG = os.path.join(ROOT, "Builds", entity_tag or TAG)
ENTITY_EE = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/" + LEAF + ".ee"
ICON_DIR = "textures/ui/vehicle_icons/"
FILES = ["profile/item.onlinec", "profile/task.onlinec", "profile/online.stringlookup",
         ICON_DIR + LEAF + ".ddsc"]
DEFAULT_TEXT = {"name": "BATMOBILE",
                "blurb": "Arkham Knight's armoured Batmobile: pursuit speed, a battle-mode turret, "
                         "and armour that shrugs off small arms."}

H = lambda s: hash_jenkins(s.encode())
ITEM_FIELDS = [("Name", "I", 0), ("BaseName", "I", 4), ("DlcId", "i", 8), ("Type", "i", 12),
               ("Purchasable", "i", 16), ("Consumable", "i", 20), ("Rewardable", "i", 24),
               ("Collectable", "i", 28), ("FeatsOff", "Q", 32), ("FeatsN", "Q", 40),
               ("Region", "I", 48), ("RebelDropTimer", "i", 52), ("MaxInventory", "i", 56),
               ("UIType", "i", 60), ("UIFlag", "i", 64), ("UIDisplayOrder", "i", 68),
               ("UIName", "I", 72), ("UIDescription", "I", 76), ("UITypeDescription", "I", 80),
               ("UIFlagDescription", "I", 84), ("UIImagePath", "Q", 88), ("UIVideoPath", "Q", 96),
               ("UIPar0", "f", 104), ("UIPar1", "f", 108), ("UIPar2", "f", 112), ("UIPar3", "f", 116),
               ("UIPar4", "f", 120)]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_vfs(path: str) -> bytes:
    import jc3strings, jc3weapons, jc3index  # noqa: E401
    idx = jc3strings.load_index()
    row = idx.get(path)
    if row is None:
        raise SystemExit(f"{path} not in the index")
    if path.startswith("profile/") and row["mount"] != "patch":
        raise SystemExit(f"{path}: expected the patch layer, index gives {row['mount']}")
    return jc3weapons.read_row(row, jc3index.DEFAULT_GAME)


def items(blob: bytes) -> list[dict]:
    D = struct.unpack_from("<I", blob, struct.unpack_from("<I", blob, 12)[0] + 8)[0]
    off, n = struct.unpack_from("<QQ", blob, D)
    out = []
    for i in range(n):
        o = D + off + 128 * i
        r = {k: struct.unpack_from("<" + t, blob, o + p)[0] for k, t, p in ITEM_FIELDS}
        for k in ("UIImagePath", "UIVideoPath"):
            s = D + r[k]
            r[k + "_s"] = blob[s:blob.index(b"\0", s)].decode("latin-1")
        r["_raw"] = blob[o:o + 128]
        out.append(r)
    return out


def tasks_rewards(blob: bytes) -> list[dict]:
    D = struct.unpack_from("<I", blob, struct.unpack_from("<I", blob, 12)[0] + 8)[0]
    off, n = struct.unpack_from("<QQ", blob, D)
    out = []
    for i in range(n):
        t = off + 112 * i
        name, = struct.unpack_from("<I", blob, D + t)
        groups = [("repeatable", t + 24)]
        th_off, th_n = struct.unpack_from("<QQ", blob, D + t + 56)
        groups += [(f"threshold[{j}]", th_off + 40 * j + 8) for j in range(th_n)]
        for where, rew in groups:
            hdr = rew + 16
            a_off, a_n = struct.unpack_from("<QQ", blob, D + hdr)
            ents = [struct.unpack_from("<IiiiI", blob, D + a_off + 20 * k) for k in range(a_n)]
            out.append({"task": i, "name": name, "where": where, "header_rel": hdr, "items": ents})
    return out


SPAWN = "settings/spawn_vehicle_defs.bin"
SPAWN_TAGS = "vehicle,batmobile"   # matches 0 of the 41 traffic selectors in global/global.blo (jc3traffic.matches)
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")


def read_vfs_any(path: str) -> bytes:
    import jc3strings, jc3weapons, jc3index  # noqa: E401
    return jc3weapons.read_row(jc3strings.load_index()[path], jc3index.DEFAULT_GAME)


def spawn_record(blob: bytes) -> bytes:
    """B-13c (Q-1a 2026-11-02): clone the donor's record in the ground-vehicle spawn table for LEAF.

    Evidence: the donor's item Name hash occurs in exactly 3 game files - item.onlinec, task.onlinec and
    settings/spawn_vehicle_defs.bin (RTPC; record = entity path + tags + select + debug + 2 vecs + name).
    The debug Serpente is only in spawn_vehicle_proto_defs.bin and a drop item naming it delivered nothing,
    as did a new leaf with no record. Tags `vehicle,batmobile` so no traffic selector picks it (TRAFFIC.md);
    the two vecs are the donor's (UNKNOWN: drop clearance box; the Batmobile is larger)."""
    import subprocess, tempfile, xml.etree.ElementTree as ET
    w = tempfile.mkdtemp(prefix="b13c_", dir=os.environ.get("JC3_RAW", "E:/Modding/_shared/gamedata/JC3grab"))
    src, x, out = (os.path.join(w, n) for n in ("in.bin", "in.xml", "out.bin"))
    open(src, "wb").write(blob)
    if subprocess.run([CONV, "--e", src, x], capture_output=True).returncode:
        raise SystemExit("B-13c: ConvertProperty export failed")
    tree = ET.parse(x)
    objs = {o.get("name"): o for o in tree.iter("object")}
    if LEAF in objs:
        raise SystemExit(f"B-13c: {LEAF} already has a spawn record")
    import copy
    d = objs[DONOR]
    parent = next(p for p in tree.iter() if d in list(p))
    c = copy.deepcopy(d)
    c.set("name", LEAF)
    vals = {v.get("name") or v.get("id"): v for v in c.findall("value")}
    vals["entity"].text = ENTITY_EE.replace("/", "\\")
    vals["tags"].text = SPAWN_TAGS
    vals["debug"].text = "vehicle|ground|rebel"
    vals["select"].text = "1"
    vals["F71C2A21"].text = LEAF
    parent.insert(list(parent).index(d) + 1, c)
    tree.write(x, encoding="utf-8", xml_declaration=True)
    if subprocess.run([CONV, "--i", x, out], capture_output=True).returncode:
        raise SystemExit("B-13c: ConvertProperty import failed")
    return open(out, "rb").read()


def text() -> dict:
    if not os.path.exists(TEXT):
        os.makedirs(os.path.dirname(TEXT), exist_ok=True)
        json.dump(DEFAULT_TEXT | {"_note": "B-13 entry text; English in all 11 languages. Edit, then "
                                  "re-run bm_rebel.py --write."}, open(TEXT, "w"), indent=1)
    return json.load(open(TEXT, encoding="utf-8"))


def build() -> dict:
    t = text()
    item_in, task_in = read_vfs("profile/item.onlinec"), read_vfs("profile/task.onlinec")
    str_in, icon = read_vfs("profile/online.stringlookup"), read_vfs(ICON_DIR + DONOR + ".ddsc")

    # ---- item.onlinec
    its = items(item_in)
    donor = [r for r in its if r["Name"] == H(DONOR)]
    if len(donor) != 1:
        raise SystemExit(f"donor item count {len(donor)}")
    donor = donor[0]
    if H(LEAF) in {r["Name"] for r in its}:
        raise SystemExit("the Batmobile item already exists in the input")
    if FREE_ORDER in {r["UIDisplayOrder"] for r in its}:
        raise SystemExit(f"UIDisplayOrder {FREE_ORDER} is taken")
    if donor["UIDescription"] != H(DONOR + "_desc") or donor["UIName"] != donor["Name"]:
        raise SystemExit("the donor does not follow the UIName/UIDescription convention")
    sorted_names = [r["Name"] for r in its] == sorted(r["Name"] for r in its)
    a = adf_append.Append(item_in)
    rec = bytearray(donor["_raw"])
    img = a.add_string(LEAF)
    for k, v in (("Name", H(LEAF)), ("UIName", H(LEAF)), ("UIDescription", H(LEAF + "_desc")),
                 ("UIDisplayOrder", FREE_ORDER), ("UIImagePath", img),
                 ("UIFlag", CATEGORY[0]), ("UIFlagDescription", CATEGORY[1])):
        fmt, pos = next((f, p) for n, f, p in ITEM_FIELDS if n == k)
        struct.pack_into("<" + fmt, rec, pos, v)
    i_off, i_n = a.array(0)
    old = bytes(a.data[i_off:i_off + 128 * i_n])
    recs = [old[128 * i:128 * i + 128] for i in range(i_n)] + [bytes(rec)]
    if sorted_names:
        recs.sort(key=lambda r: struct.unpack_from("<I", r, 0)[0])
    new_off = a.add(b"".join(recs), 8)
    a.repoint(0, new_off, len(recs))
    a.add_string_hash(LEAF, H(LEAF))
    a.add_string_hash(LEAF + "_desc", H(LEAF + "_desc"))
    item_out = a.build()

    # ---- task.onlinec
    rw = [r for r in tasks_rewards(task_in) if any(e[0] == H(DONOR) for e in r["items"])]
    if len(rw) != 1 or rw[0]["name"] != UNLOCK_TASK:
        raise SystemExit(f"donor unlock not where expected: {[(r['name'], r['where']) for r in rw]}")
    rw = [r for r in tasks_rewards(task_in) if r["name"] == STARTER_TASK and r["where"] == "repeatable"]
    if len(rw) != 1 or not any(e[0] == H("v0000_car_autostraad_oldjeep_rebel_01") for e in rw[0]["items"]):
        raise SystemExit("starter grant not where expected")
    rw = rw[0]
    b = adf_append.Append(task_in)
    ents = rw["items"] + [(H(LEAF), 1, 0, 1, 0)]
    t_off = b.add(b"".join(struct.pack("<IiiiI", *e) for e in ents), 8)
    b.repoint(rw["header_rel"], t_off, len(ents))
    b.add_string_hash(LEAF, H(LEAF))
    task_out = b.build()

    # ---- settings/spawn_vehicle_defs.bin (B-13c): the Rebel Drop resolves item Name -> a record HERE
    spawn_in = read_vfs_any(SPAWN)
    spawn_out = spawn_record(spawn_in)

    # ---- online.stringlookup
    langs = jc3strings_write.LANG_ORDER
    edits = {H(LEAF): {i: t["name"] for i in range(len(langs))},
             H(LEAF + "_desc"): {i: t["blurb"] for i in range(len(langs))}}
    str_out = jc3strings_write.write(str_in, edits)

    if os.path.exists(DROP):
        shutil.rmtree(DROP)
    outs = {"profile/item.onlinec": item_out, "profile/task.onlinec": task_out,
            "profile/online.stringlookup": str_out, ICON_DIR + LEAF + ".ddsc": icon, SPAWN: spawn_out}
    for p, data in outs.items():
        os.makedirs(os.path.dirname(os.path.join(DROP, p)), exist_ok=True)
        open(os.path.join(DROP, p), "wb").write(data)
    ins = {"profile/item.onlinec": item_in, "profile/task.onlinec": task_in,
           "profile/online.stringlookup": str_in, ICON_DIR + DONOR + ".ddsc": icon, SPAWN: spawn_in}
    return {"schema": 1, "card": "B-13", "tag": TAG, "leaf": LEAF, "leaf_hash": H(LEAF),
            "desc_hash": H(LEAF + "_desc"),
            "entity": os.path.relpath(ENTITY_TAG, ROOT).replace("\\", "/") + "/" + os.path.basename(ENTITY_EE),
            "entity_vfs": ENTITY_EE, "text": {k: t[k] for k in ("name", "blurb")},
            "item_array_sorted_by_name": sorted_names, "unlock": f"task {STARTER_TASK} repeatable (starter grant)", "inputs": {p: {"bytes": len(v), "sha256": sha(v)} for p, v in ins.items()},
            "files": {p: {"file": f"Builds/{TAG}/drop/{p}", "bytes": len(v), "sha256": sha(v)}
                      for p, v in outs.items()},
            "decisions": {"UIVideoPath": "donor's string kept (no video asset for the new leaf)",
                          "icon": "byte copy of the donor icon under the new leaf (T-WLD5); a real icon is open",
                          "languages": "English text in all 11 languages"},
            "unknown": ["whether the menu resolves a NEW leaf from the item hash (Q-1)",
                        "whether the starter grant re-fires on an existing save (repeatable; Q-1a re-test)",
                        "how the UI treats the donor video path on this entry"]}


def check() -> int:
    rec = json.load(open(os.path.join(OUT, "receipt.json")))
    bad = 0
    def ok(c, msg):
        nonlocal bad
        print(("PASS " if c else "FAIL ") + msg)
        bad += 0 if c else 1
    for p, f in rec["files"].items():
        ok(sha(open(os.path.join(ROOT, f["file"]), "rb").read()) == f["sha256"], f"sha256 {p}")
    item_in, item_out = read_vfs("profile/item.onlinec"), open(os.path.join(DROP, "profile/item.onlinec"), "rb").read()
    a, b = items(item_in), items(item_out)
    new = [r for r in b if r["Name"] == H(LEAF)]
    ok(len(b) == len(a) + 1 and len(new) == 1, f"item.onlinec decodes: {len(a)} -> {len(b)} items, 1 Batmobile")
    strip = lambda r: {k: v for k, v in r.items() if k not in ("_raw", "UIImagePath", "UIVideoPath")}
    old_same = [strip(r) for r in a] == [strip(r) for r in b if r["Name"] != H(LEAF)]
    ok(old_same, "all 196 vanilla items decode to the same values")
    if new:
        n, d = new[0], next(r for r in b if r["Name"] == H(DONOR))
        print("     Batmobile: " + json.dumps({k: n[k] for k in ("Name", "UIName", "UIDescription",
              "UIDisplayOrder", "Type", "UIType", "UIFlag", "RebelDropTimer", "Rewardable",
              "UIImagePath_s", "UIVideoPath_s")}))
        same = [k for k, _, _ in ITEM_FIELDS if k not in ("Name", "UIName", "UIDescription",
                "UIDisplayOrder", "UIImagePath", "UIFlag", "UIFlagDescription") and n[k] == d[k]]
        ok(len(same) == len(ITEM_FIELDS) - 7 and (n["UIFlag"], n["UIFlagDescription"]) == CATEGORY, f"the other {len(same)} fields equal the donor's")
        ok(n["UIImagePath_s"] == LEAF and os.path.exists(os.path.join(DROP, ICON_DIR + LEAF + ".ddsc")),
           f"icon path names {ICON_DIR}{LEAF}.ddsc, present in the build")
    t_in = tasks_rewards(read_vfs("profile/task.onlinec"))
    t_out = tasks_rewards(open(os.path.join(DROP, "profile/task.onlinec"), "rb").read())
    ok(len(t_in) == len(t_out), f"task.onlinec decodes: {len(t_out)} reward groups")
    diffs = [(x, y) for x, y in zip(t_in, t_out) if x["items"] != y["items"]]
    ok(len(diffs) == 1 and diffs[0][1]["name"] == STARTER_TASK and diffs[0][1]["where"] == "repeatable"
       and diffs[0][1]["items"] == diffs[0][0]["items"] + [(H(LEAF), 1, 0, 1, 0)],
       f"only task {STARTER_TASK} repeatable changed: +1 ItemReward for the Batmobile")
    import subprocess, tempfile
    w = tempfile.mkdtemp(prefix="b13c_chk_", dir=os.environ.get("JC3_RAW", "E:/Modding/_shared/gamedata/JC3grab"))
    xs = []
    for tag, data in (("in", read_vfs_any(SPAWN)), ("out", open(os.path.join(DROP, SPAWN), "rb").read())):
        open(os.path.join(w, tag + ".bin"), "wb").write(data)
        subprocess.run([CONV, "--e", os.path.join(w, tag + ".bin"), os.path.join(w, tag + ".xml")], capture_output=True)
        xs.append(open(os.path.join(w, tag + ".xml"), encoding="utf-8").read().splitlines())
    import difflib
    added = [l[1:].strip() for l in difflib.unified_diff(xs[0], xs[1], lineterm="", n=0)
             if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in difflib.unified_diff(xs[0], xs[1], lineterm="", n=0)
               if l.startswith("-") and not l.startswith("---")]
    ok(not removed and len(added) == 9 and f'name="{LEAF}"' in added[0]
       and any(SPAWN_TAGS in a for a in added) and any(LEAF + ".ee" in a for a in added),
       f"{SPAWN}: +1 record for {LEAF} (9 XML lines), nothing else changed")
    import jc3traffic, json as _j
    J = _j.load(open(os.path.join(ROOT, "Research", "JC3Grab", "TRAFFIC.json")))
    def _sel(o):
        if isinstance(o, dict):
            if "selectors" in o and isinstance(o["selectors"], list):
                yield from o["selectors"]
            for v in o.values():
                yield from _sel(v)
        elif isinstance(o, list):
            for v in o:
                yield from _sel(v)
    sels = list(_sel(J))
    hits = [x["text"] for x in sels if jc3traffic.matches(x, set(SPAWN_TAGS.split(",")))["ok"]]
    ok(len(sels) == 41 and not hits, f"tags {SPAWN_TAGS!r} match 0 of {len(sels)} traffic selectors {hits}")
    r = subprocess.run([sys.executable, os.path.join(HERE, "stringlookup_compare.py"),
                        os.path.join(os.environ.get("JC3_RAW", "E:/Modding/_shared/gamedata/JC3grab"), "strings_rt", "online.stringlookup"),
                        os.path.join(DROP, "profile/online.stringlookup")], capture_output=True, text=True)
    print("     " + r.stdout.strip().replace("\n", "\n     "))
    ok(r.returncode == 0 and "pairs 14712 14734" in r.stdout, "online.stringlookup: 22 pairs added, nothing else changed")
    ee = os.path.join(ENTITY_TAG, os.path.basename(ENTITY_EE))
    ok(os.path.exists(ee), "the entity the item names exists in the build: "
       + os.path.relpath(ee, ROOT).replace("\\", "/"))
    r = subprocess.run([sys.executable, os.path.join(HERE, "bm_leaf.py"), "--check",
                        "--tag", os.path.basename(ENTITY_TAG)], capture_output=True, text=True)
    ok(r.returncode == 0, "bm_leaf.py --check: " + (r.stdout.strip().splitlines() or ["?"])[-1])
    print(("PASS" if not bad else "FAIL") + f": B-13 {bad} failure(s)")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tag", default=TAG, help="build tag to write/check (default bm-013)")
    ap.add_argument("--entity-tag", default=None,
                    help="build tag holding the standalone .ee (default: --tag)")
    a = ap.parse_args()
    if a.tag != TAG or a.entity_tag:
        set_tags(a.tag, a.entity_tag)
    if a.write:
        rec = build()
        json.dump(rec, open(os.path.join(OUT, "receipt.json"), "w"), indent=1)
        print(f"wrote {TAG}: " + ", ".join(f"{p} {f['bytes']:,} B" for p, f in rec["files"].items()))
    if a.check or a.write:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
