"""grab_audio.py - every Batmobile AkEvent -> bank -> WEM map (GRB-9).

The grab holds 361 `AkEvent` objects (118 unique event ids) with their bank reference and attenuation
radius. The banks these events live in are shipped as `AkBank` exports: most inside the 15 Batmobile
packages, the vehicle beds (`BML_Batmobile`, `BML_Battlemode`, `BML_Tyres`) in `Engine.upk`.

This tool parses each bank's Wwise sections (BKHD/DIDX/DATA/HIRC/STID), walks

    Event (HIRC 4) -> Action (HIRC 3) -> Sound (HIRC 2) or RanSeq (HIRC 5) -> media id

and joins it with the grab, so the 9 hand-picked pairs in `Working/Audio/EVENTMAP.md` can be replaced by
a complete, reproducible map:

    Research/BatmobileGrab/AUDIO_MAP.json   one row per AkEvent, with bank, actions, media ids and sizes
    Research/BatmobileGrab/AUDIO_MAP.md     the same as review tables + the missing list

Struct layouts are the ones verified against these banks (offsets in bytes):

    HIRC object     u8 type, u32 size, body
    Event  (4)      u32 id, u32 action count, u32 action ids[count]
    Action (3)      u32 id, u8 scope, u8 ?, u32 target id
    Sound  (2)      u32 id, u32 plugin id, u8 stream type, ... u32 media id at 9
    RanSeq (5)      u32 id, ..., playlist of Sound ids
    DIDX            {u32 media id, u32 offset, u32 size}

An event whose bank is not on disk (the `Ww_BML_*` packages the imports point at) is reported as
`missing-bank`; nothing is guessed.

Usage:
    python Tools/scripts/grab_audio.py --write
    python Tools/scripts/grab_audio.py --check
    python Tools/scripts/grab_audio.py --event Play_BML_Sonar_Turn_On
"""
import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_model          # noqa: E402
import upk_read as U       # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
GAME = os.path.join(ROOT, "Working", "Appearance", "grab", "..", "..", "..")   # only for relpath below
COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
EXTRA_PACKAGES = ("Engine",)          # vehicle beds live here, not in the vehicle packages
SECTIONS = (b"BKHD", b"DIDX", b"DATA", b"HIRC", b"STID", b"ENVS", b"PLAT", b"INIT", b"STMG")

_pkgs = {}


def package(name):
    if name not in _pkgs:
        _pkgs[name] = U.Package(os.path.join(COOKED, name + ".upk"))
    return _pkgs[name]


def bank_sections(data):
    o = data.find(b"BKHD")
    if o < 0:
        return None
    secs = {}
    while o + 8 <= len(data):
        tag = data[o:o + 4]
        size = struct.unpack_from("<I", data, o + 4)[0]
        if tag not in SECTIONS or o + 8 + size > len(data):
            break
        secs[tag] = (o + 8, size)
        o += 8 + size
    return secs


def parse_bank(data):
    """Sections + the HIRC object maps + the DIDX media index. Returns None for a non-bank blob."""
    secs = bank_sections(data)
    if not secs or b"HIRC" not in secs:
        return None
    objs = collections.defaultdict(list)
    h, _ = secs[b"HIRC"]
    count = struct.unpack_from("<I", data, h)[0]
    q = h + 4
    for _ in range(count):
        if q + 5 > len(data):
            break
        t = data[q]
        size = struct.unpack_from("<I", data, q + 1)[0]
        objs[t].append(data[q + 5:q + 5 + size])
        q += 5 + size
    didx = {}
    if b"DIDX" in secs:
        ds, dl = secs[b"DIDX"]
        for i in range(0, dl - 11, 12):
            mid, off, size = struct.unpack_from("<III", data, ds + i)
            didx[mid] = {"offset": off, "size": size}
    bkhd = {}
    if b"BKHD" in secs:
        bs, bl = secs[b"BKHD"]
        if bl >= 8:
            bid, ver = struct.unpack_from("<II", data, bs)
            bkhd = {"id": bid, "version": ver}
    sounds, streams, events, actions, ranseq, containers = {}, {}, {}, {}, {}, {}
    # every HIRC id -> object type, so a container's child list can be validated
    object_type = {}
    for t, bodies in objs.items():
        for b in bodies:
            if len(b) >= 4:
                object_type[struct.unpack_from("<I", b, 0)[0]] = t
    for b in objs.get(2, []):
        if len(b) < 12:
            continue
        sid = struct.unpack_from("<I", b, 0)[0]
        stream_type = b[8]
        # Sound: plugin id at 4, stream type at 8, media/file id at 9 (the only u32 that is a DIDX id
        # in every embedded sound of these banks; streamed sounds keep the same file id)
        file_id = struct.unpack_from("<I", b, 9)[0]
        if file_id not in didx:
            for off in range(10, min(len(b) - 3, 40)):
                v = struct.unpack_from("<I", b, off)[0]
                if v in didx:
                    file_id = v
                    break
        sounds[sid] = file_id
        streams[sid] = stream_type
    sound_ids = set(sounds)
    for b in objs.get(5, []):
        if len(b) < 8:
            continue
        rid = struct.unpack_from("<I", b, 0)[0]
        playlist = []
        for off in range(0, len(b) - 3):
            v = struct.unpack_from("<I", b, off)[0]
            if v in sound_ids and v not in playlist:
                playlist.append(v)
        ranseq[rid] = playlist
    # ActorMixer / SwitchContainer / LayerContainer: the child graph between Action and Sound. Their
    # layouts differ by Wwise version, but every child id must be a HIRC object of a playable type, so
    # scanning the body for such ids reconstructs the graph without guessing a version.
    playable = {2, 5, 6, 7, 9}
    for t in (6, 7, 9):
        for b in objs.get(t, []):
            if len(b) < 4:
                continue
            cid = struct.unpack_from("<I", b, 0)[0]
            kids = []
            for off in range(4, len(b) - 3):
                v = struct.unpack_from("<I", b, off)[0]
                if v != cid and object_type.get(v) in playable and v not in kids:
                    kids.append(v)
            containers[cid] = kids
    for b in objs.get(3, []):
        if len(b) < 10:
            continue
        actions[struct.unpack_from("<I", b, 0)[0]] = struct.unpack_from("<I", b, 6)[0]
    for b in objs.get(4, []):
        if len(b) < 8:
            continue
        eid = struct.unpack_from("<I", b, 0)[0]
        n = struct.unpack_from("<I", b, 4)[0]
        if n > 4096 or 8 + 4 * n > len(b):
            continue
        events[eid] = [struct.unpack_from("<I", b, 8 + 4 * k)[0] for k in range(n)]
    return {"sections": {k.decode(): (v[0], v[1]) for k, v in secs.items()}, "bkhd": bkhd,
            "didx": didx, "events": events, "actions": actions, "sounds": sounds,
            "streams": streams, "ranseq": ranseq, "containers": containers}


def _walk(bank, node, seen, out):
    if node in seen:
        return
    seen.add(node)
    if node in bank["sounds"]:
        if bank["sounds"][node]:
            out.append(bank["sounds"][node])
        return
    for child in bank["ranseq"].get(node, []):
        _walk(bank, child, seen, out)
    for child in bank["containers"].get(node, []):
        _walk(bank, child, seen, out)


def resolve(bank, eid):
    """Actions -> targets -> Sound / RanSeq / container -> media ids, all verified against DIDX."""
    out, targets = [], []
    for a in bank["events"].get(eid, []):
        t = bank["actions"].get(a)
        if t is None:
            continue
        targets.append(t)
        _walk(bank, t, set(), out)
    return targets, list(dict.fromkeys(out))


def bank_sources(g):
    """(package, name) -> {data, origin, copies, also_in}. The grab's embedded banks plus the extra
    packages, deduplicated by content: the same bank is shipped inside three or four vehicles."""
    import hashlib
    raw = []
    for r in g.find(class_="AkBank"):
        if (r.get("size") or 0) < 1000:
            continue
        try:
            data = package(r["package"]).data(r["index"])
        except (OSError, U.UpkError):
            continue
        raw.append(((r["package"], r["name"]), data, "package", r["size"]))
    for name in EXTRA_PACKAGES:
        try:
            pk = package(name)
        except (OSError, U.UpkError):
            continue
        for i, e in enumerate(pk.exports, 1):
            if pk.object_class(i) != "AkBank" or e["size"] < 1000:
                continue
            raw.append(((name, e["name"]), pk.data(i), name + ".upk", e["size"]))
    out, by_sha = {}, {}
    for key, data, origin, size in raw:
        h = hashlib.sha1(data).hexdigest()
        if h in by_sha:
            first = out[by_sha[h]]
            first["copies"] += 1
            first["also_in"].append("%s:%s" % key)
            continue
        by_sha[h] = key
        out[key] = {"data": data, "origin": origin, "size": size, "copies": 1, "also_in": []}
    return out


def events(g):
    """One record per AkEvent object: the cooked struct is offset-only, so the fields are positional."""
    out = []
    for r in g.find(class_="AkEvent"):
        eid = radius = bank = None
        for p, t in g.tags(r):
            if t.get("type") == "IntProperty" and t.get("offset") == 0x54:
                eid = t.get("value") & 0xFFFFFFFF
            elif t.get("type") == "FloatProperty" and t.get("offset") == 0x64:
                radius = t.get("value")
            elif t.get("type") == "ObjectNCRProperty" and t.get("offset") == 0x5C:
                bank = t.get("ref")
        out.append({"package": r["package"], "name": r["name"], "outer": r.get("outer"),
                    "event_id": eid, "event_id_hex": "0x%08X" % eid if eid is not None else None,
                    "bank_ref": bank, "attenuation_radius": radius})
    return out


def build():
    g = grab_model.Grab()
    rows = events(g)
    sources = bank_sources(g)
    parsed, banks_meta, by_bank_id = {}, [], {}
    for key, src in sorted(sources.items(), key=lambda kv: kv[0][0] != "Engine"):
        b = parse_bank(src["data"])
        if not b:
            continue
        bid = (key[1], b["bkhd"].get("id"))
        if bid[1] and bid in by_bank_id:
            # the same bank shipped in another vehicle package: keep one copy, name the rest
            prev = banks_meta[by_bank_id[bid]]
            prev["copies"] += 1
            prev["also_in"].append("%s:%s" % key)
            continue
        if bid[1]:
            by_bank_id[bid] = len(banks_meta)
        parsed[key] = b
        banks_meta.append({"package": key[0], "bank": key[1], "origin": src["origin"],
                           "bytes": src["size"], "copies": 1, "also_in": [],
                           "bkhd": b["bkhd"],
                           "objects": {"events": len(b["events"]), "actions": len(b["actions"]),
                                       "sounds": len(b["sounds"]), "ranseq": len(b["ranseq"])},
                           "media": len(b["didx"])})
    by_id = collections.defaultdict(list)
    for key, b in parsed.items():
        for eid in b["events"]:
            by_id[eid].append(key)
    resolved_rows, missing = [], collections.OrderedDict()
    for r in rows:
        eid = r["event_id"]
        banks = by_id.get(eid, [])
        # prefer the bank the event object references, then Engine.upk, then any other
        ref_name = (r["bank_ref"] or "").split(".")[-1]
        banks = sorted(banks, key=lambda k: (k[1] != ref_name, k[0] not in EXTRA_PACKAGES))
        if not banks:
            r = dict(r, status="missing-bank", bank=None, bank_origin=None, media=[])
            missing.setdefault(r["bank_ref"] or "(no bank ref)", []).append(
                {"package": r["package"], "event": r["name"], "event_id_hex": r["event_id_hex"]})
            resolved_rows.append(r)
            continue
        key = banks[0]
        targets, media = resolve(parsed[key], eid)
        media_rows = []
        for m in media:
            d = parsed[key]["didx"].get(m)
            media_rows.append({"wem": m, "wem_hex": "0x%08X" % m,
                               "embedded": d is not None,
                               "data_offset": d["offset"] if d else None,
                               "bytes": d["size"] if d else None})
        if media_rows and any(m["embedded"] for m in media_rows):
            status = "resolved"
        elif media_rows:
            status = "streamed"       # media id known, bytes live outside the bank
        else:
            status = "no-media"       # event has no playable media (state/switch-only entry)
        resolved_rows.append(dict(r, status=status, bank=key[1], bank_package=key[0],
                                  bank_origin=sources[key]["origin"], targets=targets,
                                  media=media_rows, duplicate_of=[{"package": k[0], "bank": k[1]}
                                                                  for k in banks[1:]]))
    ids = collections.Counter(r["event_id"] for r in rows)
    summary = {
        "rows": len(rows),
        "unique_event_ids": len(ids),
        "resolved_rows": sum(1 for r in resolved_rows if r["status"] == "resolved"),
        "resolved_ids": len({r["event_id"] for r in resolved_rows if r["status"] == "resolved"}),
        "streamed_rows": sum(1 for r in resolved_rows if r["status"] == "streamed"),
        "no_media_rows": sum(1 for r in resolved_rows if r["status"] == "no-media"),
        "missing_rows": sum(1 for r in resolved_rows if r["status"] == "missing-bank"),
        "missing_ids": len({r["event_id"] for r in resolved_rows if r["status"] == "missing-bank"}),
        "missing_banks": sorted(missing.keys()),
        "media": len({m["wem"] for r in resolved_rows for m in r["media"]}),
        "media_entries": len({(r["bank_package"], r["bank"], m["wem"])
                              for r in resolved_rows for m in r["media"]}),
        "media_bytes": sum({(r["bank_package"], r["bank"], m["wem"]): (m["bytes"] or 0)
                            for r in resolved_rows for m in r["media"]}.values()),
        "banks": len(banks_meta),
        "bytes": sum(b["bytes"] for b in banks_meta),
        "by_package": dict(collections.Counter(r["package"] for r in resolved_rows)),
        "by_event_id": dict(collections.Counter(r["event_id_hex"] for r in resolved_rows)),
    }
    return {"schema": 1, "generated_by": "grab_audio.py",
            "sources": {"packages": sorted({b["package"] for b in banks_meta}),
                        "cooked": os.path.relpath(COOKED, ROOT) if COOKED.startswith(ROOT) else COOKED},
            "banks": banks_meta, "events": resolved_rows,
            "missing": {k: v for k, v in missing.items()}, "summary": summary}


def write_md(doc):
    s = doc["summary"]
    L = ["# Batmobile - AkEvent -> bank -> WEM (GRB-9)", "",
         "Generated by `Tools/scripts/grab_audio.py` from the 361 `AkEvent` objects in the grab and the "
         "`AkBank` exports they live in. Every row is resolved through Wwise HIRC: "
         "Event -> Action -> Sound/RanSeq -> DIDX media id, then checked against the bank's own media "
         "index and DATA section. This replaces the 9 hand-picked pairs in `Working/Audio/EVENTMAP.md`.",
         "", "## Summary", "", "| fact | value |", "|---|---|"]
    for k in ("rows", "unique_event_ids", "resolved_rows", "resolved_ids", "streamed_rows",
              "no_media_rows", "missing_rows", "missing_ids", "media", "media_entries",
              "media_bytes", "banks", "bytes"):
        L.append("| %s | **%s** |" % (k, s[k]))
    L += ["", "Statuses: `resolved` = media id present in the bank's DIDX/DATA; `streamed` = media id known "
          "but its bytes are outside the bank; `no-media` = the event resolves to no Sound (state/switch "
          "entry); `missing-bank` = the bank is not shipped on disk.",
          "", "Missing banks: " + (", ".join("`%s`" % b for b in s["missing_banks"]) or "none"), ""]
    L += ["## Banks parsed", "",
          "| package | bank | origin | copies | bytes | events | sounds | ranseq | media |",
          "|---|---|---|---|---|---|---|---|---|"]
    for b in doc["banks"]:
        L.append("| %s | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
            b["package"], b["bank"], b["origin"], b["copies"], b["bytes"],
            b["objects"]["events"], b["objects"]["sounds"], b["objects"]["ranseq"], b["media"]))
    L += ["", "## Events", ""]
    for pkg in sorted({e["package"] for e in doc["events"]}):
        L += ["### %s" % pkg, "",
              "| event | id | bank | WEMs | bytes | status |",
              "|---|---|---|---|---|---|"]
        for e in doc["events"]:
            if e["package"] != pkg:
                continue
            wems = ", ".join("`%s`" % m["wem_hex"] for m in e["media"]) or "-"
            size = sum(m["bytes"] or 0 for m in e["media"])
            L.append("| `%s` | %s | %s | %s | %s | %s |" % (
                e["name"], e["event_id_hex"], e["bank"] or "-", wems, size or "-", e["status"]))
        L.append("")
    L += ["## Missing (bank not on disk)", ""]
    if not doc["missing"]:
        L.append("none.")
    for bank, evs in doc["missing"].items():
        L.append("### `%s`" % bank)
        L.append("")
        L.append(", ".join("`%s`" % e["event"] for e in evs))
        L.append("")
    open(os.path.join(OUT, "AUDIO_MAP.md"), "w", encoding="utf-8").write("\n".join(L))
    return os.path.join(OUT, "AUDIO_MAP.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--event", help="show every row whose name contains this text")
    a = ap.parse_args()
    doc = build()
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        json.dump(doc, open(os.path.join(OUT, "AUDIO_MAP.json"), "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(os.path.join(OUT, "AUDIO_MAP.json"), ROOT), "and",
              os.path.relpath(write_md(doc), ROOT))
    if a.event:
        for e in doc["events"]:
            if a.event.lower() in e["name"].lower():
                print(json.dumps(e, indent=1))
    print(json.dumps({k: v for k, v in doc["summary"].items()
                      if k not in ("by_package", "by_event_id")}, indent=1))
    if a.check:
        fail, s = [], doc["summary"]
        if s["rows"] != 361:
            fail.append("expected 361 AkEvent rows, got %d" % s["rows"])
        if s["unique_event_ids"] != 118:
            fail.append("expected 118 unique event ids, got %d" % s["unique_event_ids"])
        if (s["resolved_rows"] + s["streamed_rows"] + s["no_media_rows"] + s["missing_rows"]
                != s["rows"]):
            fail.append("status counts do not add up to the row count")
        if any(not e["media"] for e in doc["events"] if e["status"] == "resolved"):
            fail.append("a row claims resolved without a media id")
        if any(e["media"] for e in doc["events"] if e["status"] == "no-media"):
            fail.append("a no-media row carries a media id")
        if any(not e["bank_ref"] for e in doc["events"] if e["status"] == "missing-bank"):
            fail.append("a missing row has no bank reference to report")
        if not doc["banks"]:
            fail.append("no bank parsed")
        if fail:
            print("FAIL")
            for f in fail:
                print("  -", f)
            return 1
        print("OK: %d rows / %d ids -> %d resolved (%d ids), %d streamed, %d no-media, "
              "%d missing (%d ids), %d WEMs, %d banks"
              % (s["rows"], s["unique_event_ids"], s["resolved_rows"], s["resolved_ids"],
                 s["streamed_rows"], s["no_media_rows"], s["missing_rows"], s["missing_ids"],
                 s["media"], s["banks"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
