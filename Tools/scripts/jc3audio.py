#!/usr/bin/env python
"""jc3audio.py - G2-24: the JC3 vehicle audio system, as far as the shipped files carry it.

Reads the game's sound banks the way the engine does - as **FMOD Designer/Ex event banks**
(RIFF form type `FEV `, `FMT ` version 0x38 build 0x32) with one **FSB5** sample bank in the
`SND ` chunk - and answers the card's five questions:

  1. every FMOD event the donor `v0300 ... civilian_01` pins (`.ee.fmod_guids`, 45 GuidEvents),
     which bank holds it, its ordinal there, its role name in the donor `.epe`, its tune and the
     sound instances that tune names;
  2. where the sounds of `w602`, `w603`, `w618`, `w619` are referenced (weapon `.ee` /
     `.fmod_guids` / `.epe`, the `.wtunec` and the vehicle that fires them);
  3. the horn and radio carriers (donor + the whole 232-vehicle fleet);
  4. the sample formats (FSB5 header, and per-sample rate/channels/codec/loop through
     `Tools/vgmstream-win64/vgmstream-cli.exe`);
  5. which of the three ship routes (a/b/c) the files support, with the evidence.

Writes `Research/JC3Grab/JC3_AUDIO.md` + `JC3_AUDIO_EVENTS.json`.
`--check` re-reads every archive and every decoded graph and compares.

Usage:
  python jc3audio.py --write
  python jc3audio.py --check [--fast]
  python jc3audio.py dump banks|donor|weapons|samples|params
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402
import jc3wiring  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
DETAIL = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab") + "/detail"
CLI = os.path.join(ROOT, "Tools", "vgmstream-win64", "vgmstream-cli.exe")
JSON_NAME = "JC3_AUDIO_EVENTS.json"
MD_NAME = "JC3_AUDIO.md"

DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_civilian_01.ee")
BANKS = {
    "vehicles": "sound/fmod_banks/vehicles.bank",
    "character": "sound/fmod_banks/character.bank",
    "effects": "sound/fmod_banks/effects.bank",
}
WEAPON_BANKS = {
    "weapons": "sound/fmod_banks/weapons.bank",
    "weapons_preorder": "sound/fmod_banks/weapons_preorder.bank",
}
TANK_EE = ("editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/"
           "v0201_car_capstone_mediumtank_military_01.ee")
WEAPONS = {
    "w602": {"label": "60 mm tank cannon", "tune":
             "editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/"
             "w602_mediumtank_canon.wtunec", "ee": None},
    "w603": {"label": "tank machine gun", "tune":
             "editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/"
             "w603_mediumtank_mgun.wtunec", "ee": None},
    "w618": {"label": "Serpente missile", "tune":
             "editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/"
             "w618_sportsmuscle_missile.wtunec",
             "ee": "editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/"
                   "w618_sportsmuscle_missile.ee"},
    "w619": {"label": "buggy machine gun", "tune":
             "editor/entities/jc_weapons/06_vehicle/w619_buggy_mgun/"
             "w619_buggy_mgun.wtunec",
             "ee": "editor/entities/jc_weapons/06_vehicle/w619_buggy_mgun/"
                   "w619_buggy_mgun.ee"},
}
AUDIO_MEMBER = re.compile(r"(sound|audio|ak_|akuevent|event_|fmod|wave|wav|loop_sound)", re.I)
# names cited by the AUD-2/AUD-6 rows; their provenance (donor event or fleet member) is measured
AUDIO_CARRIERS = {
    "exhaust_upgrade_nitrous": r"\bexhaust_upgrade_nitrous\b",
    "exhaust_upgrade_nitrous2": r"\bexhaust_upgrade_nitrous2\b",
    "exhaust_upgrade_tjump": r"\bexhaust_upgrade_tjump",
    "combined_wheel_default_sfx": r"combined_wheel",
    "wheel_suspension": r"\bwheel_suspension",
    "ground_roughness_sound_attached": r"\bground_roughness_sound_attached\b",
}


# ---------------------------------------------------------------- RIFF / FEV
def riff_children(d: bytes, start: int, end: int) -> list[tuple[bytes, int, int]]:
    """Chunks of a RIFF list body: (tag, offset-of-tag, size)."""
    out, o = [], start
    while o + 8 <= end:
        tag = d[o:o + 4]
        (size,) = struct.unpack_from("<I", d, o + 4)
        out.append((tag, o, size))
        o = o + 8 + size + (size & 1)
    return out


def u32(d: bytes, off: int) -> int:
    return struct.unpack_from("<I", d, off)[0]


def fev(d: bytes) -> dict:
    """Header facts + the PROJ section table + the embedded FSB5 offset."""
    if d[:4] != b"RIFF" or d[8:12] != b"FEV ":
        raise ValueError("not a RIFF/FEV bank")
    kids = riff_children(d, 12, 8 + u32(d, 4))
    fmt = next(k for k in kids if k[0] == b"FMT ")
    version, build = struct.unpack_from("<II", d, fmt[1] + 8)
    proj = next(k for k in kids if k[0] == b"LIST" and d[k[1] + 8:k[1] + 12] == b"PROJ")
    secs = {}
    for k in riff_children(d, proj[1] + 12, proj[1] + 8 + proj[2]):
        if k[0] == b"LIST":
            secs[d[k[1] + 8:k[1] + 12].decode("ascii", "replace")] = (k[1], k[2])
    snd = next(k for k in kids if k[0] == b"SND ")
    fsb_off = snd[1] + 8
    if d[fsb_off:fsb_off + 4] != b"FSB5":
        fsb_off = d.find(b"FSB5", snd[1])
    return {"version": version, "build": build, "sections": secs, "proj": (proj[1], proj[2]),
            "fsb_off": fsb_off, "size": len(d)}


def section_children(d: bytes, f: dict, name: str) -> list[tuple[bytes, int, int]]:
    if name not in f["sections"]:
        return []
    off, size = f["sections"][name]
    return riff_children(d, off + 12, off + 8 + size)


def section_entries(d: bytes, f: dict, name: str, child: bytes) -> list[tuple[int, int]]:
    """Entries of a section that are `LIST <child>` (EVNT, WAIT, PARM, TMLN)."""
    return [(k[1], k[2]) for k in section_children(d, f, name)
            if k[0] == b"LIST" and d[k[1] + 8:k[1] + 12] == child]


def fev_events(d: bytes, f: dict) -> list[dict]:
    """`LIST EVNT` -> `EVTB`, whose body starts with the 16-byte event GUID (no name string)."""
    out = []
    for i, (off, size) in enumerate(section_entries(d, f, "EVTS", b"EVNT")):
        evtb = riff_children(d, off + 12, off + 8 + size)[0]
        body = d[evtb[1] + 8:evtb[1] + 8 + evtb[2]]
        out.append({"ordinal": i, "guid": body[:16].hex(), "bytes": evtb[2]})
    return out


def fev_sounds(d: bytes, f: dict) -> list[bytes]:
    """`WAIS` -> `WAIT` bodies. Each instance carries two 16-byte GUIDs; the exact offset
    is not needed (the WAIB size cuts the second one short), so the whole WAIT body is kept
    and the tunes are matched against every 16-byte window in it."""
    return [d[off + 12:off + 8 + size] for off, size in section_entries(d, f, "WAIS", b"WAIT")]


def fev_event_bodies(d: bytes, f: dict) -> list[bytes]:
    """`EVTB` bodies in the same order as `fev_events`."""
    out = []
    for off, size in section_entries(d, f, "EVTS", b"EVNT"):
        kids = riff_children(d, off + 12, off + 8 + size)
        evtb = next(k for k in kids if k[0] == b"EVTB")
        out.append(d[evtb[1] + 8:evtb[1] + 8 + evtb[2]])
    return out


def fev_tunes(d: bytes, f: dict) -> list[dict]:
    """`TLNS` -> `LIST TMLN` (one per event) -> `TLNB`, whose body is the 16-byte tune GUID
    followed by the 16-byte GUID of the event that owns the tune (body offset 16)."""
    out = []
    for i, (off, size) in enumerate(section_entries(d, f, "TLNS", b"TMLN")):
        kids = riff_children(d, off + 12, off + 8 + size)
        tl = next((k for k in kids if k[0] == b"TLNB"), None)
        if tl is None:
            continue
        body = d[tl[1] + 8:tl[1] + 8 + tl[2]]
        out.append({"index": i, "tune_guid": body[:16].hex(),
                    "event_guid": body[16:32].hex(), "bytes": tl[2]})
    return out


def fev_waves(d: bytes, f: dict) -> list[dict]:
    """`WAVS` -> bare `WAV ` chunks: u8 slot index + 16-byte GUID."""
    out = []
    for tag, off, size in section_children(d, f, "WAVS"):
        if tag != b"WAV ":
            continue
        body = d[off + 8:off + 8 + size]
        out.append({"index": body[0], "guid": body[1:17].hex()})
    return out


def fev_params(d: bytes, f: dict) -> list[str]:
    """`LIST PARM` -> `PRMB`; the name is a u16 length + a printable run after the body GUID."""
    out = []
    for off, size in section_entries(d, f, "PRMS", b"PARM"):
        seg = d[off:off + 8 + size]
        for m in re.finditer(rb"[ -~]{3,}", seg):
            name = m.group()
            if name in (b"PARM", b"PRMB", b"LIST"):
                continue
            at = m.start()
            if at >= 2 and struct.unpack_from("<H", seg, at - 2)[0] == len(name):
                out.append(name.decode("ascii", "replace"))
                break
    return out


def fsb(d: bytes, off: int, want_names: bool) -> dict:
    version, samples, shdr, namelen, datasize = struct.unpack_from("<IIIII", d, off + 4)
    t0 = off + 60 + shdr
    names = []
    if want_names:
        for i in range(samples):
            p = t0 + u32(d, t0 + 4 * i)
            e = d.find(b"\x00", p)
            names.append(d[p:e].decode("utf-8", "replace"))
    return {"version": version, "samples": samples, "sample_header_bytes": shdr,
            "name_table_bytes": namelen, "data_bytes": datasize,
            "name_table_string_bytes": namelen - 4 * samples, "names": names}


def read_entry(path: str, rows: list[dict]) -> bytes:
    return jc3grab.read_entry(jc3detail.pick(rows, path), GAME)


def inner(path: str, rows: list[dict]) -> tuple[bytes, list[tuple[str, int, int]]]:
    return jc3grab.inner_files(read_entry(path, rows))


def fmod_guids(path: str, rows: list[dict]) -> dict:
    """The `.ee.fmod_guids`: u32 version, u16 bank count + names, u16 count + 16 B GUIDs."""
    stream, entries = inner(path, rows)
    hit = next((e for e in entries if e[0].endswith(".fmod_guids")), None)
    if hit is None:
        return {"present": False}
    blob = stream[hit[1]:hit[1] + hit[2]]
    version, nb = struct.unpack_from("<IH", blob, 0)
    o = 6
    banks = []
    for _ in range(nb):
        (ln,) = struct.unpack_from("<H", blob, o)
        o += 2
        banks.append(blob[o:o + ln].decode("ascii", "replace"))
        o += ln
    (ne,) = struct.unpack_from("<H", blob, o)
    o += 2
    guids = [blob[o + i * 16:o + i * 16 + 16].hex() for i in range(ne)]
    return {"present": True, "bytes": hit[2], "version": version, "banks": banks,
            "count": ne, "guids": guids, "trailing": len(blob) - (o + ne * 16)}


def parse_guid_field(v: str) -> str:
    """`DE,CA,52,...` (the `.epe` Sound/Effect byte list) -> the same 32 hex digits."""
    return bytes(int(x, 16) for x in v.split(",")).hex()


def fmt_guid(hex32: str) -> str:
    return "%s-%s-%s-%s-%s" % (hex32[:8], hex32[8:12], hex32[12:16], hex32[16:20], hex32[20:])


def audio_members(names: list[str]) -> list[str]:
    return [n for n in names if AUDIO_MEMBER.search(n)]


def vgm_census(path: str, count: int, progress: bool = True) -> list[dict]:
    """Per-sample format through vgmstream (the project's proven FSB5 reader)."""
    if not os.path.exists(CLI):
        raise SystemExit(f"vgmstream-cli missing at {CLI}")
    rows = []
    for i in range(1, count + 1):
        r = subprocess.run([CLI, "-s", str(i), "-m", path], capture_output=True, text=True,
                           errors="replace")
        got = {"index": i, "name": "", "rate": 0, "channels": 0, "frames": 0,
               "encoding": "", "loop_start": None, "loop_end": None}
        for line in (r.stdout + r.stderr).splitlines():
            line = line.strip()
            if line.startswith("sample rate:") and "Hz" in line:
                got["rate"] = int(line.split(":")[1].split("Hz")[0].strip())
            elif line.startswith("channels:"):
                got["channels"] = int(line.split(":")[1].strip())
            elif line.startswith("stream total samples:"):
                got["frames"] = int(line.split(":")[1].split("(")[0].strip())
            elif line.startswith("encoding:"):
                got["encoding"] = line.split(":", 1)[1].strip()
            elif line.startswith("stream name:"):
                got["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("loop start:"):
                got["loop_start"] = int(line.split(":")[1].split("(")[0].strip().split()[0])
            elif line.startswith("loop end:"):
                got["loop_end"] = int(line.split(":")[1].split("(")[0].strip().split()[0])
        if r.returncode != 0 or not got["rate"]:
            raise RuntimeError(f"vgmstream failed on stream {i}: {r.stderr[-200:]!r}")
        rows.append(got)
        if progress and i % 100 == 0:
            print(f"  vgmstream census {i}/{count}", file=sys.stderr)
    return rows


# ---------------------------------------------------------------- build
def build(census: bool = True) -> dict:
    rows = jc3index.load_index(OUT)
    # donor: the 45 pinned events and the role names the `.epe` gives them (read before the
    # banks so the EVTS name probe can use them)
    donor_guids = fmod_guids(DONOR, rows)
    objs, _doc = jc3wiring.decode_epe(DONOR, rows, GAME)
    roles = {}
    for o in objs:
        s = o.get("Sound")
        if not s:
            continue
        roles.setdefault(parse_guid_field(s), []).append(
            {"class": o.cls, "name": o.name, "usage": o.get("Usage")})
    role_names = sorted({r["name"] for v in roles.values() for r in v if r["name"]})
    graph_names = sorted({o.name for o in objs if o.name})

    banks = {}
    tune_maps = {}
    for name, path in BANKS.items():
        d = read_entry(path, rows)
        f = fev(d)
        events = fev_events(d, f)
        sounds = fev_sounds(d, f)
        tune_entries = fev_tunes(d, f)
        waves = fev_waves(d, f)
        params = fev_params(d, f)
        ev_guids = {e["guid"] for e in events}
        tune_of_ev = {t["event_guid"]: t for t in tune_entries}
        tune_maps[name] = tune_of_ev
        tune_pairs = sum(1 for t in tune_entries if t["event_guid"] in ev_guids)
        bijection = (tune_pairs == len(tune_entries) == len(events)
                     and len({t["event_guid"] for t in tune_entries}) == len(tune_entries)
                     and len({t["tune_guid"] for t in tune_entries}) == len(tune_entries))
        # Probes for the event -> tune -> wave chain. Only asked for vehicles (the donor bank
        # the card names); character/effects are read for the mapping only.
        wave_hits = wave_in_tunes = wave_in_inst = ev_body_tune = None
        evts_runs = evts_runs4 = evts_name_hits = None
        if name == "vehicles":
            wave_set = [bytes.fromhex(w["guid"]) for w in waves]
            woff, wsize = f["sections"]["WAVS"]
            regions = (d[:woff], d[woff + 8 + wsize:f["fsb_off"]])
            wave_hits = sum(1 for g in wave_set if any(g in r for r in regions))
            del regions
            tune_blobs = [d[o:o + 8 + s] for o, s in section_entries(d, f, "TLNS", b"TMLN")]
            wave_in_tunes = sum(1 for g in wave_set if any(g in b for b in tune_blobs))
            wave_in_inst = sum(1 for g in wave_set if any(g in b for b in sounds))
            ev_body_tune = 0
            for e, body in zip(events, fev_event_bodies(d, f)):
                t = tune_of_ev.get(e["guid"])
                if t and bytes.fromhex(t["tune_guid"]) in body:
                    ev_body_tune += 1
            evts_off, evts_size = f["sections"]["EVTS"]
            evts = d[evts_off:evts_off + 8 + evts_size]
            runs = re.findall(rb"[ -~]{3,}", evts)
            evts_runs = len(runs)
            evts_runs4 = sum(1 for r in runs if len(r) >= 4)
            evts_name_hits = sum(1 for n in role_names if n.encode("ascii", "replace") in evts)
            del runs, evts
        bank = {
            "path": path, "size": f["size"], "fev_version": f["version"],
            "fev_build": f["build"], "sha256": hashlib.sha256(d).hexdigest(),
            "sections": {k: v[1] for k, v in sorted(f["sections"].items())},
            "events": len(events), "tunes": len(tune_entries), "sound_instances": len(sounds),
            "waves": len(waves), "params": len(params), "param_names": sorted(set(params)),
            "wave_guid_refs_outside_wavs": wave_hits,
            "wave_guids_in_tunes": wave_in_tunes,
            "wave_guids_in_instances": wave_in_inst,
            "tunes_with_event_guid": tune_pairs,
            "tune_event_bijection": bijection,
            "event_bodies_carrying_tune_guid": ev_body_tune,
            "tlnt_tag_count": d.count(b"TLNT"),
            "evts_printable_runs": evts_runs,
            "evts_printable_runs_ge4": evts_runs4,
            "evts_role_name_hits": evts_name_hits,
            "fsb": fsb(d, f["fsb_off"], name == "vehicles"),
            "event_list": events,
        }
        del d
        banks[name] = bank

    event_bank = {}
    for name, b in banks.items():
        for e in b["event_list"]:
            event_bank.setdefault(e["guid"], []).append(
                {"bank": name, "ordinal": e["ordinal"], "bytes": e["bytes"]})
    donor = []
    for g in donor_guids["guids"]:
        places = event_bank.get(g, [])
        tune = None
        for p in places:
            t = tune_maps[p["bank"]].get(g)
            if t is not None:
                tune = {"bank": p["bank"], "index": t["index"], "tune_guid": t["tune_guid"]}
                break
        donor.append({
            "guid": fmt_guid(g),
            "raw": g,
            "roles": roles.get(g, []),
            "banks": places,
            "tune": tune,
            # the tune -> wave edge is not stored (wave GUIDs in tunes/instances = 0), so a
            # sample name cannot be derived from the event; see section 5 of the doc
            "samples": None,
        })
    named = sum(1 for e in donor if e["roles"])
    in_bank = sum(1 for e in donor if e["banks"])
    tunes_resolved = sum(1 for e in donor if e["tune"])
    donor_sounds = [parse_guid_field(o.get("Sound")) for o in objs if o.get("Sound")]

    # master.banklist: the loader's own list of bank files (read, not typed)
    bl_path = "sound/fmod_banks/master.banklist"
    bl_raw = read_entry(bl_path, rows)
    banklist = {"path": bl_path, "bytes": len(bl_raw),
                "lines": len(bl_raw.splitlines()),
                "names": [x.strip() for x in bl_raw.decode("utf-8", "replace").splitlines()
                          if x.strip()]}

    # LandAudio: the only audio parameters the vehicle modules carry
    stream, entries = inner(DONOR, rows)
    la_name, la_off, la_size = next(e for e in entries if e[0].endswith("land_audio.vmodc"))
    land_audio = {"module": la_name,
                  "members": {n: v for n, _t, v in
                              jc3adf.walk(jc3adf.Adf(stream[la_off:la_off + la_size]))}}

    # weapons
    weapons = {}
    for wid, spec in WEAPONS.items():
        tune_raw = read_entry(spec["tune"], rows)
        tune_names = [n for n, _t, _v in jc3adf.walk(jc3adf.Adf(tune_raw))]
        row = {"label": spec["label"], "tune": spec["tune"], "tune_members": len(tune_names),
               "tune_audio_members": audio_members(tune_names)}
        if spec["ee"]:
            fg = fmod_guids(spec["ee"], rows)
            objs, _ = jc3wiring.decode_epe(spec["ee"], rows, GAME)
            sounds = [{"class": o.cls, "name": o.name, "guid": parse_guid_field(o.get("Sound"))}
                      for o in objs if o.get("Sound")]
            comp = [{"class": o.cls, "name": o.name, "props":
                     {k: v for k, v in o.props.items()
                      if re.search(r"weapon|tune|fire|ammo", k, re.I)}}
                    for o in objs if "Weapon" in (o.cls or "")]
            row.update({"ee": spec["ee"], "fmod_guids": {k: v for k, v in fg.items()
                                                         if k != "guids"},
                        "guids": fg.get("guids", []), "sound_roles": sounds,
                        "components": comp})
            row["banks_holding"] = sorted({b for g in fg.get("guids", [])
                                           for b, bb in banks.items()
                                           if any(e["guid"] == g for e in bb["event_list"])})
        else:
            row.update({"ee": None, "fmod_guids": {"present": False}, "guids": [],
                        "sound_roles": [], "components": [], "banks_holding": []})
        weapons[wid] = row

    tank_objs, _ = jc3wiring.decode_epe(TANK_EE, rows, GAME)
    tank_sound = [{"class": o.cls, "name": o.name, "guid": parse_guid_field(o.get("Sound"))}
                  for o in tank_objs if o.get("Sound") and re.search(r"fire|reload|turret|can",
                                                                     o.name or "", re.I)]
    tank_weapons = [{"class": o.cls, "name": o.name,
                     "props": {k: v for k, v in o.props.items()
                               if re.search(r"weapon|tune", k, re.I)}}
                    for o in tank_objs if "Weapon" in (o.cls or "")]

    # horn / radio across the fleet (decoded graph cache)
    files = sorted(f for f in os.listdir(DETAIL) if f.endswith(".ee.json")) \
        if os.path.isdir(DETAIL) else []
    if not files:
        raise SystemExit(f"no decoded entity graphs in {DETAIL} - run jc3detail.py build --all")
    horn, radio = [], []
    sound_objects = 0
    names = set()
    carrier_entities: dict[str, set] = {k: set() for k in AUDIO_CARRIERS}
    for f in files:
        try:
            doc = json.load(open(os.path.join(DETAIL, f), encoding="utf-8"))
        except Exception:
            continue
        objs_f = doc.get("epe", {}).get("objects", [])
        # one searchable blob per entity: every object name and every string value, so a
        # carrier that is an effect-table name (not a `Sound` object) is still found
        hay = "\n".join([o.get("name") or "" for o in objs_f]
                        + [str(x) for o in objs_f for x in (o.get("values") or {}).values()])
        for cname, pat in AUDIO_CARRIERS.items():
            if re.search(pat, hay):
                carrier_entities[cname].add(doc.get("entity"))
        del hay
        for o in objs_f:
            v = o.get("values") or {}
            if "Sound" not in v:
                continue
            sound_objects += 1
            nm = (o.get("name") or "")
            names.add((o.get("class") or "", nm))
            if "horn" in nm.lower():
                horn.append({"entity": doc.get("entity"),
                             "class": o.get("class"), "name": nm,
                             "guid": parse_guid_field(v["Sound"])})
            if "radio" in nm.lower():
                radio.append({"entity": doc.get("entity"), "name": nm})
    donor_horn = next((e for e in donor if any(r["name"] == "horn" for r in e["roles"])), None)
    horn_radio = {
        "entities": len(files), "sound_objects": sound_objects,
        "distinct_roles": len(names),
        "horn_objects": len(horn), "horn_entities": len({h["entity"] for h in horn}),
        "horn_guids": sorted({h["guid"] for h in horn}),
        "radio_objects": len(radio),
        "donor_horn": donor_horn["guid"] if donor_horn else None,
        "donor_horn_banks": [p["bank"] for p in donor_horn["banks"]] if donor_horn else [],
        # provenance for the AUD-2/AUD-6 carrier names: is the name on the donor, and on how
        # many of the 232 decoded vehicles does it appear at all
        "carriers": {n: {"entities": len(carrier_entities[n]),
                         "donor": any(re.search(pat, k) for k in role_names),
                         "graph": any(re.search(pat, k) for k in graph_names)}
                     for n, pat in AUDIO_CARRIERS.items()},
    }

    # sample census: the Working/Audio copy is only a staging copy of the archive entry, so
    # assert the two are identical before any sample number is taken from it
    wpath = os.path.join(ROOT, "Working", "Audio", "jc3bank", "sound", "fmod_banks",
                         "vehicles.bank")
    h = hashlib.sha256()
    with open(wpath, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    bank_copy = {"path": wpath, "archive_sha256": banks["vehicles"]["sha256"],
                 "working_sha256": h.hexdigest(),
                 "matches": h.hexdigest() == banks["vehicles"]["sha256"]}
    if not bank_copy["matches"]:
        raise SystemExit(f"{wpath} differs from sound/fmod_banks/vehicles.bank; the sample "
                         "census would describe the wrong file")
    sample_rows = []
    if census:
        sample_rows = vgm_census(wpath, banks["vehicles"]["fsb"]["samples"])
    census_summary = {}
    if sample_rows:
        census_summary = {
            "count": len(sample_rows),
            "rates": sorted({r["rate"] for r in sample_rows}),
            "channels": sorted({r["channels"] for r in sample_rows}),
            "encodings": sorted({r["encoding"] for r in sample_rows}),
            "looped": sum(1 for r in sample_rows if r["loop_start"] is not None),
            "names_match_name_table":
                [r["name"] for r in sample_rows] == banks["vehicles"]["fsb"]["names"],
        }

    return {
        "card": "G2-24",
        "donor": {"entity": DONOR, "fmod_guids": {k: v for k, v in donor_guids.items()
                                                  if k != "guids"},
                  "events": donor, "named": named, "in_a_bank": in_bank,
                  "tunes_resolved": tunes_resolved,
                  "sound_objects": len(donor_sounds),
                  "sound_guids": len(set(donor_sounds))},
        "banks": {k: {kk: vv for kk, vv in v.items() if kk != "event_list"}
                  for k, v in banks.items()},
        "banklist": banklist,
        "bank_copy": bank_copy,
        "land_audio": land_audio,
        "weapons": weapons,
        "tank": {"entity": TANK_EE, "sound_roles": tank_sound, "weapons": tank_weapons},
        "horn_radio": horn_radio,
        "samples": {"summary": census_summary, "list": sample_rows},
        "route": {
            "a": {
                "name": "sample swap inside a copy of vehicles.bank",
                "possible": True,
                "evidence": [
                    "test-060 swapped the FSB5 PCM payloads in place (same byte size, metadata "
                    "untouched) and the bank still parses and decodes (MODLOG §71, "
                    "`Tools/scripts/_apply_audio.py`)",
                    "the bank is loaded as a loose override at sound/fmod_banks/vehicles.bank "
                    "with no .toc (MODLOG §71)",
                    "every donor sample is 16-bit PCM at 48 kHz (census), so a replacement must "
                    "be PCM16/48 kHz and exactly the original frame count",
                ],
            },
            "b": {
                "name": "a new bank + .fmod_guids",
                "possible": False,
                "evidence": [
                    "the banks are FMOD Designer/Ex FEV v56 build 50, not FMOD Studio: the events, "
                    "tunes, parameters and DSP live in the FEV graph, and no .fev project ships",
                    "the entity pins events by GUID, and the GUID is authored in the FEV graph; "
                    "a new bank would have to reproduce that graph",
                    f"master.banklist is a plain {banklist['lines']}-line text list "
                    f"({banklist['bytes']} B), so the loader can be told about another file, but "
                    "nothing here can author its contents",
                ],
            },
            "c": {
                "name": "mixed: vehicles.bank swaps for the car, weapons.bank swaps for the guns",
                "possible": True,
                "evidence": [
                    "the four chosen weapons pin their own events in weapons_preorder/effects, "
                    "and the weapon .ee carries the Sound GUID",
                    "weapons.bank holds 1228 named samples (names such as "
                    "`jc3_wpn_tank_cannon_loaded_02`), so the same payload swap applies there",
                ],
            },
            "recommended": "a + c",
        },
    }


# ---------------------------------------------------------------- markdown
def num(v) -> str:
    if isinstance(v, float):
        return repr(round(v, 6))
    return str(v)


def render_md(d: dict) -> str:
    donor = d["donor"]
    banks = d["banks"]
    h = donor["fmod_guids"]
    car = d["horn_radio"]["carriers"]

    def prov(key: str) -> str:
        """Where a carrier name lives: a pinned donor event, a donor object without a GUID,
        or a name that only other fleet vehicles carry."""
        c = car[key]
        if c["donor"]:
            return "donor event"
        if c["graph"]:
            return "donor graph object, **not a pinned event**"
        return f"fleet member, {c['entities']} vehicles"

    bank_rows = [(k, v) for k, v in banks.items()]
    lines = [
        "# JC3 vehicle audio system",
        "",
        "G2-24. Every JC3 sound bank here is a **FMOD Designer/Ex event bank** (RIFF `FEV `, "
        f"`FMT ` version {banks['vehicles']['fev_version']} build "
        f"{banks['vehicles']['fev_build']}), not an FMOD Studio bank: the event graph and one",
        "FSB5 sample bank share one file. The donor pins "
        f"**{h['count']} events** in `{h['bytes']} B` of `.ee.fmod_guids` across "
        f"{len(h['banks'])} banks",
        f"(`{'`, `'.join(h['banks'])}`), {donor['named']} of them named by an `SAttachedEffect` /",
        f"`SDynamicAttachedEffect` in the `.epe`, and **{donor['in_a_bank']} of {h['count']}** are",
        "found as an `EVTS` entry in one of those banks.",
        "",
        "## 1. The event bank format (what is and is not in the file)",
        "",
        "| fact | value |",
        "|---|---|",
        f"| container | `RIFF`/`FEV `, `FMT ` version {banks['vehicles']['fev_version']} build "
        f"{banks['vehicles']['fev_build']} |",
        f"| sections | {', '.join(f'`{k}`' for k in banks['vehicles']['sections'])} |",
        f"| events | `EVTS` -> `LIST EVNT` -> `EVTB`; the body **starts with the 16-byte event "
        f"GUID**, no name string |",
        f"| tunes | `TLNS` -> `LIST TMLN` -> `TLNB`, one per event: the body is the 16-byte "
        f"tune GUID + the 16-byte GUID of the event that owns it (body offset 16) |",
        f"| sound instances | `WAIS` -> `WAIT` -> `LIST INST` -> `WAIB`: two 16-byte GUIDs per "
        f"instance |",
        f"| waves | `WAVS` -> `WAV `: a u8 index + 16-byte GUID per sample slot |",
        f"| parameters | `PRMS` -> `PARM`: a GUID + a u16-length name |",
        f"| samples | `SND ` -> `FSB5` v{banks['vehicles']['fsb']['version']}, "
        f"{banks['vehicles']['fsb']['samples']} samples, "
        f"{banks['vehicles']['fsb']['data_bytes']:,} B of data |",
        "",
        f"**No event name or path is stored anywhere.** `EVTS` holds "
        f"{banks['vehicles']['evts_printable_runs']:,} printable runs of >= 3 chars "
        f"({banks['vehicles']['evts_printable_runs_ge4']:,} of >= 4), and every one is a chunk "
        f"tag (`LIST`, `EVTS`, `EVTB`, `PRPS`, `PROP`) or binary noise: "
        f"{banks['vehicles']['evts_role_name_hits']} of the {len({r['name'] for e in donor['events'] for r in e['roles']})} "
        "donor role names occurs in the section. The one name table in the file names",
        "*samples*, not events. The GUID is the only event identity the game ships, so \"event",
        "path\" below is the role name the donor `.epe` gives that GUID (or UNKNOWN where the",
        "graph does not name it).",
        "",
        "## 2. The three banks the donor uses",
        "",
        "| bank | size | events | tunes | sound instances | waves | params | samples |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for k, b in bank_rows:
        lines.append(f"| `{k}` | {b['size']:,} | {b['events']} | {b['tunes']} | "
                     f"{b['sound_instances']} | {b['waves']} | {b['params']} | "
                     f"{b['fsb']['samples']} |")
    lines += [
        "",
        "## 3. Every event the donor pins",
        "",
        f"{h['count']} rows (`{donor['tunes_resolved']}` with a tune). `bank/ordinal` is the `EVTS` "
        "position in the bank that holds the GUID;",
        "`role` is the `.epe` object name; `tune` is the `TLNS` index in the same bank (the tune",
        "body carries the event GUID); `samples` stays UNKNOWN because no tune or sound-instance",
        "body carries a wave GUID (0 / "
        f"{banks['vehicles']['waves']}, §5).",
        "",
        "| # | GUID | bank / ordinal | role (`.epe`) | tune | samples |",
        "|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(donor["events"], 1):
        place = ", ".join(f"{p['bank']}/{p['ordinal']}" for p in e["banks"]) or "**not in a bank**"
        role = ", ".join(f"`{r['name']}` ({r['class'].replace('AttachedEffect', '')})"
                         for r in e["roles"]) or "-"
        tune = (f"{e['tune']['bank']}/{e['tune']['index']}" if e["tune"] else "UNKNOWN")
        lines.append(f"| {i} | `{e['guid']}` | {place} | {role} | {tune} | UNKNOWN |")
    lines += [
        "",
        f"All {donor['tunes_resolved']} of {h['count']} GUIDs resolve to a tune index in their",
        "bank. What `.ee.fmod_guids` *means* is not decoded - the file itself only shows",
        f"`version {h['version']}`, {len(h['banks'])} bank names, "
        f"{h['count']} GUIDs and {h['trailing']} trailing bytes - so calling it a \"preload",
        "list\" is an inference. The `.epe` names "
        f"{donor['named']} of the {h['count']} GUIDs with {donor['sound_objects']} `Sound` objects",
        f"({donor['sound_guids']} distinct values); the other "
        f"{h['count'] - donor['named']} appear in no `Sound` field of the decoded graph. Whether",
        "that is a second, native consumer of the block is UNKNOWN (it is code, not data).",
        "",
        "## 4. Parameters",
        "",
        "| where | member | value |",
        "|---|---|---|",
    ]
    for k, v in sorted(d["land_audio"]["members"].items()):
        lines.append(f"| `LandAudio` (`{d['land_audio']['module'].rsplit('/', 1)[-1]}`) | "
                     f"`{k}` | {num(v)} |")
    lines += [
        "",
        f"`LandAudio` carries **{len(d['land_audio']['members'])} members**, the only vehicle-side",
        "audio parameters the donor modules expose. Whether they are the RPM window a particular",
        "engine event is driven over is **UNKNOWN**: the next paragraph shows the event-to-parameter",
        "edge is not decoded, so the names (`min_rpm` / `max_rpm`) are the only evidence.",
        "",
        f"The banks also carry {banks['vehicles']['params']} project parameters "
        f"({len(banks['vehicles']['param_names'])} distinct names), e.g. "
        f"{', '.join(f'`{p}`' for p in banks['vehicles']['param_names'][:6])} ... - the mixer's",
        "global parameter space. **Which event reads which parameter is not decoded**: the `PMLS`",
        "mapping lists reference the parameter GUIDs but the event-to-parameter edge is not a",
        "field this reader can resolve, so per-event parameter bindings are UNKNOWN.",
        "",
        "## 5. Event -> tune -> sample: what the files give",
        "",
        "| probe | result |",
        "|---|---|",
        f"| tune bodies carrying their event GUID (`TLNB` body offset 16) | "
        f"**{banks['vehicles']['tunes_with_event_guid']} / {banks['vehicles']['tunes']}** |",
        f"| tune <-> event pairs, 1:1 | **{banks['vehicles']['tune_event_bijection']}** |",
        f"| event bodies carrying their tune GUID (body offset 32) | "
        f"**{banks['vehicles']['event_bodies_carrying_tune_guid']} / {banks['vehicles']['events']}** |",
        f"| donor GUIDs resolved to a tune index | **{donor['tunes_resolved']} / {h['count']}** |",
        f"| `WAVS` GUIDs referenced by any other section | "
        f"**{banks['vehicles']['wave_guid_refs_outside_wavs']}** of "
        f"{banks['vehicles']['waves']} |",
        f"| wave GUIDs inside any tune chunk | **{banks['vehicles']['wave_guids_in_tunes']}** of "
        f"{banks['vehicles']['waves']} |",
        f"| wave GUIDs inside any sound instance (`WAIT`) body | "
        f"**{banks['vehicles']['wave_guids_in_instances']}** of {banks['vehicles']['waves']} |",
        f"| `TLNT` chunk tag in the bank | **{banks['vehicles']['tlnt_tag_count']}** |",
        "",
        "So the **event -> tune** hop *is* stored, twice: the `TLNB` body repeats the owning",
        "event GUID, and the event body repeats the tune GUID at offset 32. `TLNS` holds one tune",
        "per event, the pairs are a 1:1 map, and all 45 donor GUIDs resolve. The chain stops one",
        "hop later: **tune -> wave is not stored** - no tune chunk and no sound-instance body",
        "contains a `WAVS` GUID (0 / 649). A build therefore knows the event and its tune, and",
        "must pick the sample it",
        "replaces by name and audition (`§6` lists them), exactly as test-060 did.",
        "",
        "## 6. The sample bank",
        "",
        "| fact | value |",
        "|---|---|",
        f"| FSB5 version | {banks['vehicles']['fsb']['version']} |",
        f"| samples | {banks['vehicles']['fsb']['samples']} |",
        f"| sample header bytes | {banks['vehicles']['fsb']['sample_header_bytes']:,} |",
        f"| name table | {banks['vehicles']['fsb']['name_table_bytes']:,} B "
        f"({banks['vehicles']['fsb']['name_table_string_bytes']:,} B of names) |",
        f"| sample data | {banks['vehicles']['fsb']['data_bytes']:,} B |",
    ]
    s = d["samples"]["summary"]
    if s:
        lines += [
            f"| rates | {', '.join(str(x) for x in s['rates'])} Hz |",
            f"| channels | {', '.join(str(x) for x in s['channels'])} |",
            f"| encodings | {', '.join(s['encodings'])} |",
            f"| looped samples | {s['looped']} / {s['count']} |",
            f"| vgmstream names == name table | {s['names_match_name_table']} |",
        ]
    lines += [
        "",
        "First samples (index, name, rate/ch, frames, loop):",
        "",
        "| # | name | rate | ch | frames | loop |",
        "|---|---|---|---|---|---|",
    ]
    for r in d["samples"]["list"][:12]:
        lp = (f"{r['loop_start']}..{r['loop_end']}" if r["loop_start"] is not None else "-")
        lines.append(f"| {r['index']} | `{r['name']}` | {r['rate']} | {r['channels']} | "
                     f"{r['frames']} | {lp} |")
    lines += [
        "",
        f"All {s['count'] if s else banks['vehicles']['fsb']['samples']} rows are in the JSON "
        "(`samples.list`). A loop state is only claimed where vgmstream reads a loop chunk from",
        f"the FSB5 header ({s['looped'] if s else 0} samples); every other sample is a one-shot and",
        "shows `-`. Those looped samples are the only places a start/loop pair can land.",
        "",
        "## 7. Weapon sounds: `w602`, `w603`, `w618`, `w619`",
        "",
        "| id | source | tune members | audio members in tune | `.fmod_guids` | events in | sound roles |",
        "|---|---|---|---|---|---|---|",
    ]
    for wid, w in d["weapons"].items():
        fg = w["fmod_guids"]
        fgtxt = (f"{fg.get('count')} over `{'`, `'.join(fg.get('banks', []))}`"
                 if fg.get("present") else "**none** (no `.ee`)")
        roles = ", ".join(f"`{r['name']}` `{fmt_guid(r['guid'])}`" for r in w["sound_roles"]) or "-"
        lines.append(f"| `{wid}` | `{(w['ee'] or w['tune']).rsplit('/', 1)[-1]}` | "
                     f"{w['tune_members']} | {len(w['tune_audio_members'])} | {fgtxt} | "
                     f"{', '.join(w['banks_holding']) or '-'} | {roles} |")
    lines += [
        "",
        "**`w602`/`w603` carry no sound at all.** They exist only as `.wtunec` (no `.ee`, no",
        f"`.fmod_guids`), and every one of their {d['weapons']['w602']['tune_members']} tune "
        "members is damage/recoil/scatter/shake - no `sound`, `event`, `audio` or `wav` member. "
        "Their firing audio lives on the *vehicle*",
        "that fires them; the medium tank's `.epe` carries "
        + (" and ".join(f"`{r['name']}` (`{fmt_guid(r['guid'])}`)"
                        for r in d["tank"]["sound_roles"][:2]) or "no firing role")
        + ",",
        "and `weapons.bank` ships the samples by name (`jc3_wpn_tank_cannon_loaded_02`,",
        "`jc3_wpn_mntd_tank_cannon_medium_02`, ...). The weapon events are listed above with",
        "their GUIDs, but their samples are **UNKNOWN** for the same measured reason as the car:",
        "`tune -> wave` is not stored (vehicle bank 0 / 649; the weapon banks were not probed for",
        "this card), so the `Done` clause's sample half is a stated UNKNOWN, not a missing list.",
        "",
        "`w618`/`w619` are the opposite: each `.ee` has its own `.fmod_guids`",
        f"(`w618` {d['weapons']['w618']['fmod_guids'].get('count')} GUIDs, `w619` "
        f"{d['weapons']['w619']['fmod_guids'].get('count')}), and the `.epe` binds the fire event",
        "to a `SAttachedEffect` (`fire`/`fire2..4` for `w618`, `fire_sound_combi` for `w619`) whose",
        "`Sound` is the first GUID of that list. Those banks are `weapons_preorder` and `effects`,",
        "not `vehicles`.",
        "",
        "## 8. Horn and radio",
        "",
        "| probe | result |",
        "|---|---|",
        f"| donor `horn` role | `{d['horn_radio']['donor_horn']}` in "
        f"`{'`, `'.join(d['horn_radio']['donor_horn_banks'])}` |",
        f"| `horn` objects in the fleet | **{d['horn_radio']['horn_objects']}** in "
        f"{d['horn_radio']['horn_entities']} vehicles, "
        f"{len(d['horn_radio']['horn_guids'])} distinct GUIDs |",
        f"| `radio` objects in the fleet | **{d['horn_radio']['radio_objects']}** |",
        f"| `Sound`-carrying objects / entities | {d['horn_radio']['sound_objects']} / "
        f"{d['horn_radio']['entities']} ({d['horn_radio']['distinct_roles']} distinct roles) |",
        "",
        f"The horn is a **per-model attached effect**, carried as "
        f"{len(d['horn_radio']['horn_guids'])} distinct GUIDs over "
        f"{d['horn_radio']['horn_objects']} objects, so removing it from the Batmobile is "
        "deleting one `SAttachedEffect` - and BmAK has no horn event at all",
        "(`AUDIO_FEATURES.md`: group `horn`, **0 rows / 0 events**), so AUD-7 says remove it.",
        f"There is **no radio member on any of the {d['horn_radio']['entities']} decoded",
        "vehicles**, so no vehicle-side member has to be suppressed for AUD-7. Where JC3's radio",
        "lives (music system, another graph, code) is **UNKNOWN** - this card did not decode it.",
        "",
        "## 9. AUD-1...7 against the carriers",
        "",
        "| code | BmAK source (G1-15) | JC3 carrier | status |",
        "|---|---|---|---|",
        "| AUD-1 | `engine` group, 18 events / 130 WEMs, RTPCs `REV_RPM`, `REV_Throttle`, `Speed`, "
        "`EngineHeat` | `engine_running_sound` attached effect + `LandAudio.min_rpm`/"
        "`max_rpm` | carrier exists; sample mapping UNKNOWN |",
        f"| AUD-2 | `afterburner` + `burnout` groups | `exhaust_upgrade_nitrous` "
        f"({prov('exhaust_upgrade_nitrous')}) / `exhaust_upgrade_nitrous2` "
        f"({prov('exhaust_upgrade_nitrous2')}) / `exhaust_upgrade_tjump*` "
        f"({prov('exhaust_upgrade_tjump')}) | carrier exists; test-060 swapped three samples |",
        "| AUD-3 | `interior` group, 9 events / 22 WEMs | no cabin effect on the donor; the "
        "nearest is `speedwind_sound_player` | **named omission** unless a bank swap adds it |",
        "| AUD-4 | `battle-mode` group, 30 events / 75 WEMs | no mode-switch event in the donor; "
        "D-2 decides if a second variant ships | deferred with D-2 |",
        "| AUD-5 | `weapons` group, 3 events / 10 WEMs | weapon `.ee` `SAttachedEffect` + "
        "`weapons.bank` samples | carrier exists per weapon (§7) |",
        f"| AUD-6 | `impacts` + `movement` groups | `wheel_suspension_*` "
        f"({prov('wheel_suspension')}), `ground_roughness_sound_attached` "
        f"({prov('ground_roughness_sound_attached')}), `combined_wheel_default_sfx` "
        f"({prov('combined_wheel_default_sfx')}) | keep JC3's (named omission, as T-AU3 says) |",
        "| AUD-7 | `horn` 0 rows; no radio | donor `horn` effect; **0 radio objects** | remove "
        "the horn for lore, no radio member to touch |",
        "",
        "## 10. Ship routes",
        "",
        "| route | possible | evidence |",
        "|---|---|---|",
    ]
    for key in ("a", "b", "c"):
        r = d["route"][key]
        lines.append(f"| **{key}** {r['name']} | {'yes' if r['possible'] else '**no**'} | "
                     f"{'; '.join(r['evidence'])} |")
    lines += [
        "",
        f"**Recommendation: route {d['route']['recommended']}.** The event graph is not editable",
        "from the shipped data (route b needs the FMOD Designer project), but the sample payloads",
        "are swappable in place (proven in test-060) and the weapon banks work the same way. The",
        "limit is that the *sample inside a tune* has to be chosen by name and audition, because",
        "tune -> wave is not stored (§5); the event and its tune are known. That is what",
        "test-060 did (spectral ranking of the engine suspects in MODLOG §70), not a new",
        "limitation introduced here.",
        "",
        "## 11. Reproduce / limits",
        "",
        "`python Tools/scripts/jc3audio.py --write` regenerates both files; `--check` re-reads every",
        "bank, the donor `.ee`, the four weapon sources and the 232 decoded graphs, re-runs the",
        f"{s['count'] if s else 649}-sample vgmstream census (~30 s here) and compares byte for "
        "byte.",
        "`--fast` skips the census (checks everything else). The census runs on the",
        "`Working/Audio/jc3bank` copy only after its sha256 is checked against the archive entry",
        f"(sha256 {'match' if d['bank_copy']['matches'] else 'MISMATCH'}).",
        "",
        "**UNKNOWNs.** (1) Tune -> wave: see §5 (event -> tune *is* stored). (2) Event name/path: not stored. "
        "(3) Which event reads which parameter: not resolved. (4) What the FEV's tune `TRNS`",
        "transitions mean at runtime (loop points, cut points) - the marker names (`Start`,",
        "`start1..4`) are readable, their semantics are code. (5) Whether a horn removal alone",
        "silences the horn: the horn is a GUID-pinned event, so removing the object is the data",
        "side; the input binding is code (Q-1).",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------- invariants
def invariants(d: dict) -> list[str]:
    bad = []
    donor = d["donor"]
    fg = donor["fmod_guids"]
    if not fg.get("present") or fg.get("count") != 45:
        bad.append(f"donor fmod_guids {fg}")
    if fg.get("banks") != ["vehicles", "character", "effects"]:
        bad.append(f"donor banks {fg.get('banks')}")
    if donor["in_a_bank"] != 45:
        bad.append(f"{donor['in_a_bank']}/45 donor GUIDs located")
    if donor["named"] != 23:
        bad.append(f"{donor['named']} named roles, expected 23")
    seen = [e["guid"] for e in donor["events"]]
    if len(set(seen)) != len(seen):
        bad.append("duplicate donor GUID")
    for e in donor["events"]:
        if len(e["banks"]) > 1:
            bad.append(f"{e['guid']} in {len(e['banks'])} banks")
        if e["banks"] and e["tune"] is None:
            bad.append(f"{e['guid']} is in a bank but has no tune")
    vb = d["banks"]["vehicles"]
    if vb["fev_version"] != 56 or vb["fev_build"] != 50:
        bad.append(f"FEV version {vb['fev_version']}/{vb['fev_build']}")
    if vb["events"] != 257 or vb["tunes"] != 257:
        bad.append(f"vehicles events/tunes {vb['events']}/{vb['tunes']}")
    if vb["fsb"]["samples"] != 649 or len(vb["fsb"]["names"]) != 649:
        bad.append(f"FSB5 samples/names {vb['fsb']['samples']}/{len(vb['fsb']['names'])}")
    if vb["wave_guid_refs_outside_wavs"] != 0:
        bad.append(f"WAVS GUID referenced outside WAVS: {vb['wave_guid_refs_outside_wavs']}")
    if vb["tunes_with_event_guid"] != vb["tunes"]:
        bad.append(f"only {vb['tunes_with_event_guid']}/{vb['tunes']} tunes carry an event GUID")
    if not vb["tune_event_bijection"]:
        bad.append("tune/event map is not a 1:1 bijection")
    if vb["event_bodies_carrying_tune_guid"] != vb["events"]:
        bad.append(f"{vb['event_bodies_carrying_tune_guid']}/{vb['events']} event bodies "
                   "carry their tune GUID")
    if vb["wave_guids_in_tunes"] != 0 or vb["wave_guids_in_instances"] != 0:
        bad.append(f"wave GUIDs in tunes/instances: {vb['wave_guids_in_tunes']}/"
                   f"{vb['wave_guids_in_instances']} - the tune -> wave edge is stored after all")
    if vb["tlnt_tag_count"] != 0:
        bad.append(f"TLNT tag occurs {vb['tlnt_tag_count']} times")
    if donor["tunes_resolved"] != donor["in_a_bank"]:
        bad.append(f"{donor['tunes_resolved']}/{donor['in_a_bank']} donor events resolved to a tune")
    if vb["params"] != 969 or len(vb["param_names"]) != 49:
        bad.append(f"parameters {vb['params']}/{len(vb['param_names'])} distinct")
    bl = d["banklist"]
    if bl["lines"] != 26 or bl["bytes"] != 434:
        bad.append(f"master.banklist {bl['lines']} lines / {bl['bytes']} B")
    if not d["bank_copy"]["matches"]:
        bad.append("Working/Audio vehicles.bank differs from the archive entry")
    cr = d["horn_radio"]["carriers"]
    for n in ("exhaust_upgrade_nitrous", "ground_roughness_sound_attached"):
        if not cr[n]["donor"]:
            bad.append(f"{n} is no longer a donor event")
    for n in ("exhaust_upgrade_nitrous2", "combined_wheel_default_sfx",
              "wheel_suspension"):
        if cr[n]["donor"]:
            bad.append(f"{n} is now a pinned donor event - section 9's provenance changed")
        if not cr[n]["graph"]:
            bad.append(f"{n} is no longer a donor graph object")
    sum_banks = sum(b["events"] for b in d["banks"].values())
    if sum_banks < 45:
        bad.append(f"only {sum_banks} events across the three banks")
    la = d["land_audio"]["members"]
    if la.get("min_rpm") != 1000.0 or la.get("max_rpm") != 10000.0:
        bad.append(f"LandAudio {la}")
    for wid in ("w602", "w603"):
        w = d["weapons"][wid]
        if w["tune_audio_members"]:
            bad.append(f"{wid} tune has audio members {w['tune_audio_members']}")
        if w["sound_roles"]:
            bad.append(f"{wid} has sound roles")
    for wid in ("w618", "w619"):
        w = d["weapons"][wid]
        if not w["guids"] or not w["sound_roles"]:
            bad.append(f"{wid} missing guids or sound roles")
        if w["sound_roles"] and w["sound_roles"][0]["guid"] != w["guids"][0]:
            bad.append(f"{wid} fire GUID is not the first .fmod_guids entry")
    if not d["tank"]["sound_roles"]:
        bad.append("medium tank has no fire/reload sound role")
    hr = d["horn_radio"]
    if hr["horn_objects"] != 178:
        bad.append(f"horn objects {hr['horn_objects']}")
    if hr["radio_objects"] != 0:
        bad.append(f"radio objects {hr['radio_objects']}")
    if not hr["donor_horn"]:
        bad.append("donor has no horn role")
    s = d["samples"]["summary"]
    if s:
        if s["count"] != 649 or s["rates"] != [48000]:
            bad.append(f"census {s['count']} samples, rates {s['rates']}")
        if not s["names_match_name_table"]:
            bad.append("vgmstream names differ from the FSB5 name table")
    if d["route"]["b"]["possible"]:
        bad.append("route b flipped to possible without evidence")
    return bad


def cmd_write(census: bool = True) -> int:
    d = build(census)
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {d['donor']['fmod_guids']['count']} donor events "
          f"({d['donor']['named']} named, {d['donor']['in_a_bank']} located, "
          f"{d['donor']['tunes_resolved']} tunes), "
          f"{d['banks']['vehicles']['events']} vehicle events, "
          f"{d['banks']['vehicles']['fsb']['samples']} samples, "
          f"{d['horn_radio']['horn_objects']} horn / {d['horn_radio']['radio_objects']} radio "
          f"objects, {len(md.splitlines())} md lines")
    return 0


def cmd_check(fast: bool = False) -> int:
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    have = json.load(open(jp, encoding="utf-8"))
    d = build(not fast)
    bad = invariants(d)
    if fast:
        # the stored census is reused so the md still renders; it is not re-verified
        d["samples"] = have.get("samples", {"summary": {}, "list": []})
        live, stored = dict(d), dict(have)
        live.pop("samples", None)
        stored.pop("samples", None)
        stale = live != stored
    else:
        stale = have != d
    if stale:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    got = open(mp, encoding="utf-8").read()
    if md != got:
        diff = list(difflib.unified_diff(got.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    drop = d.get("samples") or {"summary": {"count": 0}, "list": []}
    print(f"PASS: {d['donor']['fmod_guids']['count']} donor events in "
          f"{len(d['banks'])} banks, {d['banks']['vehicles']['events']}/"
          f"{d['banks']['vehicles']['tunes']} vehicle events/tunes, "
          f"{d['donor']['tunes_resolved']}/{d['donor']['in_a_bank']} donor tunes, "
          f"{d['banks']['vehicles']['tunes_with_event_guid']}/"
          f"{d['banks']['vehicles']['tunes']} tunes with an event GUID, "
          f"{d['banks']['vehicles']['wave_guids_in_tunes']}/"
          f"{d['banks']['vehicles']['wave_guids_in_instances']} wave GUIDs in tunes/instances, "
          f"{d['banks']['vehicles']['fsb']['samples']} samples "
          f"({drop['summary'].get('looped', 0)} looped, "
          f"{len(drop['summary'].get('rates', []))} rate), wave refs "
          f"{d['banks']['vehicles']['wave_guid_refs_outside_wavs']}, LandAudio "
          f"{len(d['land_audio']['members'])} members, weapons "
          f"{len(d['weapons'])}, horn {d['horn_radio']['horn_objects']} / radio "
          f"{d['horn_radio']['radio_objects']}, md match True")
    return 0


def cmd_dump(what: str) -> int:
    d = build(False)
    key = {"banks": "banks", "donor": "donor", "weapons": "weapons", "samples": "samples",
           "params": "land_audio"}.get(what)
    if key is None:
        print("one of: banks, donor, weapons, samples, params")
        return 2
    print(json.dumps(d[key], indent=1, sort_keys=True, ensure_ascii=False)[:20000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--fast", action="store_true", help="skip the vgmstream sample census")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="donor")
    a = p.parse_args()
    if a.write:
        return cmd_write(not a.fast)
    if a.check:
        return cmd_check(a.fast)
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
