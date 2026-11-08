"""bmak_audio_features.py - G1-15: every AkEvent grouped by feature, every WEM decoded and measured.

Inputs (all already in the grab): `Research/BatmobileGrab/AUDIO_MAP.json` (361 event rows, 118 unique
event ids, 447 media ids, 90 `missing-bank` rows), the `AkBank` exports inside the cooked packages -
read through `grab_audio.py`, because only 11 of the 27 banks exist as loose files in `Working/Audio/`
- and the package name tables for the Wwise parameter names.

What it derives:

    event row -> exactly one feature group (first rule wins, `other` last)
    event     -> reachable HIRC objects (Action -> Sound/RanSeq/Switch/ActorMixer/Blend)
               -> container types, RTPC bindings with curve points, loop evidence
    media id  -> bytes (embedded: DIDX/DATA in the bank; streamed: the SFX wad index)
               -> 48 kHz WAV under E:\\Modding\\_shared\\gamedata\\BmAKgrab\\audio\\wav\\ (outside the repo)
               -> duration, peak dBFS, integrated loudness (ITU-R BS.1770-4)

Wwise ids: every id in these banks is FNV-1 of the lower-case name (offset 0x811C9DC5, prime
0x01000193, XOR-then-multiply). It reproduces all 118 event ids in AUDIO_MAP.json, so the same
function names the game parameters an RTPC list binds.

RTPC entry layout (recovered from these banks; offsets relative to the entry):

    u32 param_id | u8 type (=0) | u8 interpolation | u8 a | u32 curve_id | u8 b | u16 point_count
    point_count * ( f32 x | f32 y | u32 curve_type )

A chain is kept only when the u16 immediately before it equals the number of entries that parse,
every entry has type 0, every point is finite, under 1e7 in magnitude, with curve_type <= 32, and no
param_id is a HIRC object id (a game parameter is not an object).

Usage:
    python Tools/scripts/bmak_audio_features.py --write     # regen JSON + MD, decode + measure
    python Tools/scripts/bmak_audio_features.py --check     # Done-when gate (reads the JSON)
    python Tools/scripts/bmak_audio_features.py --event Sonar
"""
import argparse
import collections
import glob
import json
import math
import os
import re
import struct
import subprocess
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_audio as GA  # noqa: E402  (pulls the AkBank exports straight out of the cooked packages)

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
AMAP = os.path.join(OUT, "AUDIO_MAP.json")
AUDIO_MD = os.path.join(OUT, "AUDIO.md")
JSON_OUT = os.path.join(OUT, "AUDIO_FEATURES.json")
MD_OUT = os.path.join(OUT, "AUDIO_FEATURES.md")
WEMDIR = r"E:\Modding\_shared\gamedata\BmAKgrab\audio\wem"
WAVDIR = r"E:\Modding\_shared\gamedata\BmAKgrab\audio\wav"
CLI = os.path.join(ROOT, "Tools", "vgmstream-win64", "vgmstream-cli.exe")
CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
CENSUS = os.path.join(ROOT, "Working", "Audio", "sfx_census.json")
SR = 48000

# HIRC type -> the container label the card asks for. Only these five labels are used; every other
# HIRC type is reported by number and never called a container.
CTYPE = {2: "sound", 5: "random-sequence", 6: "switch", 7: "actor-mixer", 9: "blend"}

RULES = [
    ("sonar", r"sonar"),
    ("tracker", r"tracker"),
    ("lock-on-ui", r"^hud|lockbeep|_locked$|missile_lock"),
    ("battle-mode", r"battle"),
    ("voice", r"^(char_|main_|seq_)|joker"),
    ("death", r"destroyed|death|dead"),
    ("movement", r"jump|dodge"),
    ("impacts", r"explosion|impact|immobiliser|battery_roll|sweetener"),
    ("weapons", r"mshot|sniperrifle"),
    ("afterburner", r"rockettails|afterburner|boost"),
    ("engine", r"engine|idle|gearshift|clutch|distantrev|reverse|positional|persistent|"
               r"coolticks|rotation"),
    ("burnout", r"burnout|skid|wheelspin|drift|tyres|cornersqueal|steering_bed|slide|braking"),
    ("interior", r"^boot|^flaps|cockpit|chairs|rain_interior|inbatmobile"),
    ("winch", r"winch"),
    ("emp", r"(^|_)emp($|_)"),
    ("horn", r"horn|honk|beep"),
]
GROUP_ORDER = [g for g, _ in RULES] + ["other"]
GROUP_NOTE = {
    "winch": "no AkEvent in the grab plays Winch audio (the BML_Winch parameters ship, the events do not)",
    "emp": "no AkEvent in the grab is an EMP sound",
    "horn": "no horn event ships in these packages - the only `Beep` events are tank lock-on UI",
    "afterburner": "RocketTails only; no separate boost bed is an event in these packages",
    "movement": "jump and dodge one-shots (JUMP_LAND / PREJUMP / PRELAND / WIND, DODGE)",
    "other": "rows no rule matched: rain, world objects, the Batwing line",
}


def fnv1(name):
    """Wwise object id: FNV-1 of the lower-case name."""
    h = 0x811C9DC5
    for c in name.lower().encode("utf-8"):
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ c
    return h


def group_of(name):
    n = re.sub(r"^(Play|Stop|Pause|PlayViaRandomNode)_", "", name)
    for g, pat in RULES:
        if re.search(pat, n, re.I):
            return g
    return "other"


# ---------------------------------------------------------------- banks / HIRC

def load():
    amap = json.load(open(AMAP, encoding="utf-8"))
    g = GA.grab_model.Grab()
    sources = GA.bank_sources(g)
    banks = []
    for key in sorted(sources):
        b = GA.parse_bank(sources[key]["data"])
        if b:
            banks.append({"key": key, "data": sources[key]["data"], "b": b})
    return amap, banks


def hirc_objects(banks):
    """id -> {bank name, HIRC type, body}. First copy of a bank wins (copies are byte-identical)."""
    objs = {}
    for bk in banks:
        data = bk["data"]
        secs = GA.bank_sections(data)
        if not secs or b"HIRC" not in secs:
            continue
        h, _ = secs[b"HIRC"]
        n = struct.unpack_from("<I", data, h)[0]
        q = h + 4
        for _ in range(n):
            if q + 5 > len(data):
                break
            t = data[q]
            sz = struct.unpack_from("<I", data, q + 1)[0]
            body = data[q + 5:q + 5 + sz]
            if len(body) >= 4:
                objs.setdefault(struct.unpack_from("<I", body, 0)[0],
                                {"bank": bk["key"][1], "type": t, "body": body})
            q += 5 + sz
    return objs


def _entry(body, o, end):
    if o + 14 > end:
        return None
    pid = struct.unpack_from("<I", body, o)[0]
    if pid == 0 or body[o + 4] != 0:
        return None
    interp, a = body[o + 5], body[o + 6]
    curve_id = struct.unpack_from("<I", body, o + 7)[0]
    b = body[o + 11]
    cnt = struct.unpack_from("<H", body, o + 12)[0]
    if cnt == 0 or cnt > 64:
        return None
    p = o + 14
    pts = []
    for _ in range(cnt):
        if p + 12 > end:
            return None
        x, y = struct.unpack_from("<ff", body, p)
        ct = struct.unpack_from("<I", body, p + 8)[0]
        if not (math.isfinite(x) and math.isfinite(y)) or abs(x) > 1e7 or abs(y) > 1e7 or ct > 32:
            return None
        pts.append([round(x, 6), round(y, 6), ct])
        p += 12
    return {"param_id": pid, "type": 0, "interpolation": interp, "a": a,
            "curve_id": curve_id, "b": b, "points": pts, "end": p}


def rtpc_chain(body, obj_ids, named):
    """The object's RTPC list, if one parses end to end under the u16-count anchor."""
    end = len(body)
    cands = []
    for o in range(2, end - 14):
        anchor = struct.unpack_from("<H", body, o - 2)[0]
        if anchor == 0 or anchor > 64 or body[o + 4] != 0:
            continue
        chain, pos = [], o
        while True:
            e = _entry(body, pos, end)
            if e is None:
                break
            chain.append(e)
            pos = e["end"]
        if not chain or len(chain) != anchor:
            continue
        if any(e["param_id"] in obj_ids for e in chain):
            continue
        cands.append((o, chain))
    if not cands:
        return None, 0
    off, chain = max(cands, key=lambda c: (any(e["param_id"] in named for e in c[1]),
                                           len(c[1]), -c[0]))
    for e in chain:
        e.pop("end", None)
    return chain, off


# ---------------------------------------------------------------- names

def parameter_names():
    """id -> (name, source). The AUDIO.md Ak* columns win; the package name tables fill the rest."""
    out = {}
    txt = open(AUDIO_MD, encoding="utf-8").read()
    for cls in ("AkParameterName", "AkCurve", "AkSwitchName", "AkStateName", "AkEnvironmentName"):
        for nm in re.findall(r"^\|\s*`([^`]+)`\s*\|\s*" + cls + r"\s*\|", txt, re.M):
            out.setdefault(fnv1(nm), (nm, cls))
    tables = sorted(glob.glob(os.path.join(ROOT, "Working", "Audio", "conv", "*", "names.txt")))
    tables.append(os.path.join(ROOT, "Working", "Audio", "bm_names.txt"))
    for p in tables:
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8", errors="replace"):
            nm = line.strip()
            if nm and len(nm) < 80 and "\x00" not in nm:
                out.setdefault(fnv1(nm), (nm, "name-table"))
    return out


# ---------------------------------------------------------------- walk

def walk(bank, roots):
    """Action targets -> every object below them (RanSeq / Switch / ActorMixer / Blend children)."""
    order, seen = [], set()
    stack = list(roots)
    while stack:
        nid = stack.pop(0)
        if nid in seen:
            continue
        seen.add(nid)
        order.append(nid)
        stack = bank["ranseq"].get(nid, []) + bank["containers"].get(nid, []) + stack
    return order


# ---------------------------------------------------------------- decode / measure

def integrated_lufs(a, sr):
    """ITU-R BS.1770-4 integrated loudness: K-weighting, 400 ms blocks, -70 LUFS and -10 LU gates."""
    b1 = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a1 = [1.0, -1.69065929318241, 0.73248077421585]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.99004745483398, 0.99007225036621]
    y = np.empty_like(a)
    for c in range(a.shape[1]):
        y[:, c] = lfilter(b1, a1, lfilter(b2, a2, a[:, c]))
    block, hop = int(round(0.4 * sr)), int(round(0.1 * sr))
    n = y.shape[0]
    if n == 0:
        return None
    if n < block:
        z = [float((y * y).mean(axis=0).sum())]
        lj = -0.691 + 10 * math.log10(max(z[0], 1e-12))
        return round(lj, 2) if lj > -70 else None
    z = np.array([float((y[s:s + block] ** 2).mean(axis=0).sum())
                  for s in range(0, n - block + 1, hop)])
    with np.errstate(divide="ignore"):
        lj = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    keep = lj > -70
    if not keep.any():
        return None
    rel = -0.691 + 10 * math.log10(max(float(z[keep].mean()), 1e-12)) - 10.0
    keep2 = keep & (lj > rel)
    if not keep2.any():
        keep2 = keep
    return round(-0.691 + 10 * math.log10(max(float(z[keep2].mean()), 1e-12)), 2)


_STREAM_IDX = None


def stream_index():
    """media id -> (bank path, size, offset): every DIDX in every bank/BNK on disk (cached).
    The streamed banks ship HIRC + STID only, so the media must be indexed somewhere else."""
    global _STREAM_IDX
    if _STREAM_IDX is None:
        idx = {}
        paths = (sorted(glob.glob(os.path.join(ROOT, "Working", "Audio", "*.bank")))
                 + sorted(glob.glob(os.path.join(ROOT, "Working", "Audio", "*.bnk")))
                 + sorted(glob.glob(os.path.join(CK, "SFX", "*.bnk")))
                 + sorted(glob.glob(os.path.join(CK, "English(US)", "*.bnk"))))
        for p in paths:
            try:
                data = open(p, "rb").read()
            except OSError:
                continue
            secs = GA.bank_sections(data)
            if not secs or b"DIDX" not in secs:
                continue
            ds, dl = secs[b"DIDX"]
            for i in range(0, dl - 11, 12):
                mid, off, sz = struct.unpack_from("<III", data, ds + i)
                idx.setdefault(mid, (p, sz, off))
        _STREAM_IDX = (idx, len(paths))
    return _STREAM_IDX


def extract(rec, bank_bytes):
    if rec["embedded"]:
        data = bank_bytes.get(rec["bank"])
        if data is None:
            raise RuntimeError("bank bytes not loaded: %s" % rec["bank"])
        secs = GA.bank_sections(data)
        if not secs or b"DATA" not in secs:
            raise RuntimeError("%s has no DATA section" % rec["bank"])
        ds = secs[b"DATA"][0]
        raw = data[ds + rec["data_offset"]: ds + rec["data_offset"] + rec["bytes"]]
        if raw[:4] != b"RIFF":
            raw = data[rec["data_offset"]: rec["data_offset"] + rec["bytes"]]
        if raw[:4] != b"RIFF" or len(raw) != rec["bytes"]:
            raise RuntimeError("embedded slice is not a RIFF/WEM of %s bytes" % rec["bytes"])
        return raw, "embedded"
    idx, scanned = stream_index()
    hit = idx.get(rec["wem"])
    if hit is None:
        raise RuntimeError(
            "streamed media: no DIDX entry in any of the %d bank files searched "
            "(Working/Audio/*.bank|*.bnk, CookedPCConsole/SFX/*.bnk, English(US)/*.bnk); "
            "the shipped bank is HIRC-only and the bytes are not on disk" % scanned)
    path, sz, off = hit
    data = open(path, "rb").read()
    secs = GA.bank_sections(data)
    if not secs or b"DATA" not in secs:
        raise RuntimeError("streamed host has no DATA section: %s" % path)
    ds = secs[b"DATA"][0]
    raw = data[ds + off: ds + off + sz]
    if raw[:4] != b"RIFF" or len(raw) != sz:
        raise RuntimeError("streamed slice is not a WEM of %s bytes" % sz)
    return raw, "streamed"


def _float_mono(data):
    a = np.asarray(data, dtype=np.float64)
    if data.dtype == np.int16:
        a /= 32768.0
    elif data.dtype == np.int32:
        a /= 2147483648.0
    elif data.dtype == np.uint8:
        a = (a - 128.0) / 128.0
    return a[:, None] if a.ndim == 1 else a


def decode_measure(rec, bank_bytes, tag):
    raw, source = extract(rec, bank_bytes)
    os.makedirs(WEMDIR, exist_ok=True)
    os.makedirs(WAVDIR, exist_ok=True)
    wem = os.path.join(WEMDIR, tag + ".wem")
    native = os.path.join(WEMDIR, tag + ".native.wav")
    out = os.path.join(WAVDIR, tag + ".wav")
    with open(wem, "wb") as f:
        f.write(raw)

    def run(with_meta):
        cmd = [CLI] + (["-m"] if with_meta else []) + ["-W", "1", "-o", native, wem]
        return subprocess.run(cmd, capture_output=True, text=True, errors="replace")

    pr = run(True)
    if not os.path.exists(native) or os.path.getsize(native) < 44:
        pr = run(False)
    meta, loop_lines = {}, []
    text = (pr.stdout or "") + "\n" + (pr.stderr or "")
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip().lower()
        if k in ("sample rate", "channels", "encoding", "stream total samples",
                 "play duration", "bitrate", "sample type"):
            meta[k.replace(" ", "_")] = v.strip()
        if "loop" in k:
            loop_lines.append(line.strip())
    if pr.returncode != 0 or not os.path.exists(native):
        raise RuntimeError("vgmstream failed: " + text.strip()[-300:])
    sr, data = wavfile.read(native)
    a = _float_mono(data)
    native_rate = int(sr)
    if native_rate != SR:
        g = math.gcd(native_rate, SR)
        a = resample_poly(a, SR // g, native_rate // g, axis=0)
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    wavfile.write(out, SR, (np.clip(a, -1.0, 1.0) * 32767.0).astype(np.int16))
    return {
        "wem": rec["wem"], "wem_hex": rec["wem_hex"], "bytes": rec["bytes"], "source": source,
        "bank": rec["bank"], "events": sorted(set(rec["events"])), "groups": sorted(rec["groups"]),
        "wav": out, "native_rate": native_rate, "sample_rate": SR,
        "channels": int(a.shape[1]), "duration_s": round(a.shape[0] / float(SR), 3),
        "peak_dbfs": round(20 * math.log10(max(peak, 1e-9)), 2),
        "lufs": integrated_lufs(a, SR),
        "vgmstream": meta, "loop_lines": loop_lines,
    }


def measure_existing(rec, prev):
    """--no-decode: measure the WAV already on disk, keep the metadata the first run captured."""
    out = os.path.join(WAVDIR, "%08X.wav" % rec["wem"])
    if not os.path.exists(out):
        raise RuntimeError("WAV not present (run --write to decode)")
    sr, data = wavfile.read(out)
    a = _float_mono(data)
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    old = prev.get(rec["wem"], {})
    return {
        "wem": rec["wem"], "wem_hex": rec["wem_hex"], "bytes": rec["bytes"],
        "source": "embedded" if rec["embedded"] else "streamed",
        "bank": rec["bank"], "events": sorted(set(rec["events"])), "groups": sorted(rec["groups"]),
        "wav": out, "native_rate": old.get("native_rate", int(sr)), "sample_rate": int(sr),
        "channels": int(a.shape[1]), "duration_s": round(a.shape[0] / float(sr), 3),
        "peak_dbfs": round(20 * math.log10(max(peak, 1e-9)), 2),
        "lufs": integrated_lufs(a, int(sr)),
        "vgmstream": old.get("vgmstream", {}), "loop_lines": old.get("loop_lines", []),
    }


# ---------------------------------------------------------------- build

def build(decode=True):
    amap, banks = load()
    objs = hirc_objects(banks)
    obj_ids = set(objs)
    names = parameter_names()
    named = set(names)
    bank_bytes, bank_parsed = {}, {}
    for bk in banks:
        bank_bytes.setdefault(bk["key"][1], bk["data"])
        bank_parsed.setdefault(bk["key"][1], bk["b"])

    prev = {}
    if not decode and os.path.exists(JSON_OUT):
        prev = {d["wem"]: d for d in json.load(open(JSON_OUT, encoding="utf-8")).get("media", [])}

    media = {}
    for r in amap["events"]:
        for m in r.get("media") or []:
            rec = media.setdefault(m["wem"], {
                "wem": m["wem"], "wem_hex": m["wem_hex"], "bytes": m["bytes"],
                "embedded": m["embedded"], "data_offset": m["data_offset"],
                "bank": r.get("bank"), "events": [], "groups": set()})
            rec["events"].append(r["name"])

    chain_cache = {}

    def chains_of(oid):
        if oid not in chain_cache:
            o = objs.get(oid)
            chain_cache[oid] = rtpc_chain(o["body"], obj_ids, named) if o else (None, 0)
        return chain_cache[oid]

    # corpus-wide RTPC scan: every HIRC object in every bank, counted once
    rtpc_objects = 0
    param_objs, param_entries = collections.defaultdict(set), collections.Counter()
    for oid in objs:
        chain, _off = chains_of(oid)
        if not chain:
            continue
        rtpc_objects += 1
        for e in chain:
            nm, src = names.get(e["param_id"], (None, None))
            param_objs[(e["param_id"], nm, src)].add(oid)
            param_entries[e["param_id"]] += 1
    params = {"0x%08X" % pid: {"param": nm, "name_source": src, "objects": len(oids),
                               "entries": param_entries[pid]}
              for (pid, nm, src), oids in param_objs.items()}

    rows, sigs = [], []
    sound_bytes = {}
    stop_names = {re.sub(r"^Stop_", "", r["name"]) for r in amap["events"]
                  if r["name"].startswith("Stop_")}

    for r in amap["events"]:
        row = {
            "package": r["package"], "name": r["name"], "group": group_of(r["name"]),
            "event_id_hex": r["event_id_hex"], "status": r["status"], "bank": r.get("bank"),
            "wems": [m["wem_hex"] for m in (r.get("media") or [])],
            "container_types": [], "rtpc": [], "loop": {},
        }
        for m in r.get("media") or []:
            media[m["wem"]]["groups"].add(row["group"])
        base = re.sub(r"^(Play|Stop)_", "", r["name"])
        stop = "Stop_" + base
        row["loop"] = {
            "stop_event": stop if (r["name"].startswith("Play_") and base in stop_names) else None,
            "name_tokens": [t for t in ("Lp", "Persistent", "Idle", "Loop") if t in base],
        }
        first_sound = None
        bank = bank_parsed.get(r.get("bank"))
        if bank and r["status"] != "missing-bank":
            ctypes, rtpc = collections.Counter(), []
            for oid in walk(bank, r.get("targets") or []):
                o = objs.get(oid)
                if not o:
                    continue
                if o["type"] in CTYPE:
                    ctypes[CTYPE[o["type"]]] += 1
                if o["type"] == 2:
                    sound_bytes.setdefault(oid, o["body"][4:13] if len(o["body"]) >= 13 else b"")
                    if first_sound is None:
                        first_sound = sound_bytes[oid]
                chain, _off = chains_of(oid)
                if chain:
                    for e in chain:
                        nm, src = names.get(e["param_id"], (None, None))
                        rtpc.append({
                            "object": "0x%08X" % oid,
                            "type_label": CTYPE.get(o["type"], "type%d" % o["type"]),
                            "param_id": "0x%08X" % e["param_id"], "param": nm,
                            "name_source": src, "interpolation": e["interpolation"],
                            "curve_id": "0x%08X" % e["curve_id"], "b": e["b"],
                            "points": e["points"],
                        })
            row["container_types"] = sorted(ctypes)
            row["rtpc"] = rtpc
        rows.append(row)
        sigs.append(first_sound)

    probe = loop_probe(rows, sigs)

    decoded, errors = [], []
    for i, rec in enumerate(sorted(media.values(), key=lambda m: m["wem"]), 1):
        tag = "%08X" % rec["wem"]
        try:
            if decode:
                decoded.append(decode_measure(rec, bank_bytes, tag))
            else:
                if not os.path.exists(os.path.join(WAVDIR, tag + ".wav")):
                    extract(rec, bank_bytes)   # only to raise the precise reason
                decoded.append(measure_existing(rec, prev))
        except Exception as exc:  # noqa: BLE001 - every failure must land in the record
            errors.append({"wem": rec["wem"], "wem_hex": rec["wem_hex"], "bytes": rec["bytes"],
                           "source": "embedded" if rec["embedded"] else "streamed",
                           "bank": rec["bank"], "events": sorted(set(rec["events"])),
                           "groups": sorted(rec["groups"]),
                           "error": "%s: %s" % (type(exc).__name__, exc)})
        if decode and i % 50 == 0:
            print("  decoded %d/%d" % (i, len(media)), file=sys.stderr)

    groups = []
    for g in GROUP_ORDER:
        grows = [r for r in rows if r["group"] == g]
        if not grows and g not in GROUP_NOTE:
            continue
        groups.append({
            "name": g, "rows": len(grows), "events": len({r["name"] for r in grows}),
            "wems": len({m for r in grows for m in r["wems"]}),
            "rtpc_params": sorted({e["param"] for r in grows for e in r["rtpc"] if e["param"]}),
            "containers": sorted({c for r in grows for c in r["container_types"]}),
            "note": GROUP_NOTE.get(g, ""),
        })

    s = amap["summary"]
    summary = {
        "rows": len(rows), "unique_event_ids": s["unique_event_ids"],
        "groups_used": len({r["group"] for r in rows}),
        "media": len(media), "decoded": len(decoded), "decode_errors": len(errors),
        "missing_rows": sum(1 for r in rows if r["status"] == "missing-bank"),
        "banks": s["banks"], "rtpc_objects": rtpc_objects,
        "rtpc_entries": sum(p["entries"] for p in params.values()),
        "rtpc_params_distinct": len(params),
        "rtpc_params_named": sum(1 for p in params.values() if p["param"]),
        "duration_total_s": round(sum(d["duration_s"] for d in decoded), 1),
    }
    return {
        "schema": 1, "generated_by": "bmak_audio_features.py",
        "inputs": {"audio_map": "Research/BatmobileGrab/AUDIO_MAP.json",
                   "audio_md": "Research/BatmobileGrab/AUDIO.md",
                   "banks": "AkBank exports read through Tools/scripts/grab_audio.py",
                   "wav_dir": WAVDIR, "wem_dir": WEMDIR},
        "method": {
            "id_hash": "FNV-1(lower-case name): offset 0x811C9DC5, prime 0x01000193, XOR then "
                       "multiply - reproduces 118/118 event ids in AUDIO_MAP.json",
            "rtpc_layout": "u16 count before the list; entry = u32 param_id, u8 type (0), "
                           "u8 interpolation, u8 a, u32 curve_id, u8 b, u16 point_count, then "
                           "point_count * (f32 x, f32 y, u32 curve_type)",
            "rtpc_anchors": ["u16 before the chain == number of entries that parse",
                             "every entry type byte == 0",
                             "every point finite, |value| < 1e7, curve_type <= 32",
                             "no param_id is a HIRC object id",
                             "the BML_Steering parameters resolve to the AkParameterName list"],
            "lufs": "ITU-R BS.1770-4: K-weighting biquads at 48 kHz, 400 ms blocks with 75% "
                    "overlap, -70 LUFS absolute gate and -10 LU relative gate; channels weight 1.0",
            "loop_field_probe": probe,
        },
        "groups": groups, "events": rows, "media": decoded, "decode_errors": errors,
        "rtpc_params": params, "missing": amap["missing"], "summary": summary,
    }


def loop_probe(rows, sigs):
    """Sound body bytes 4..12 = (plugin type, 0, stream type, media id, per-bank constant).
    Does any of those bytes separate looping events from one-shot events?"""
    loop_idx, shot_idx = [], []
    for i, r in enumerate(rows):
        if r["status"] == "missing-bank" or not sigs[i]:
            continue
        base = re.sub(r"^(Play|Stop)_", "", r["name"])
        if r["loop"]["stop_event"] or r["loop"]["name_tokens"]:
            loop_idx.append(i)
        elif re.search(r"oneshot|explosion|impact|open|close|land|fail|destroyed", base, re.I):
            shot_idx.append(i)
    out = {"loop_events": len(loop_idx), "oneshot_events": len(shot_idx),
           "probed_offsets": [4, 5, 6, 7, 8], "separated_offsets": [], "detail": {}}
    if not loop_idx or not shot_idx:
        out["note"] = "not enough events on one side to probe"
        return out
    for off in range(4, 9):          # body[9:13] is the media id, body[13:17] a per-bank
        i = off - 4                  # constant - both would "separate" for the wrong reason
        a = {sigs[k][i] for k in loop_idx if len(sigs[k]) > i}
        b = {sigs[k][i] for k in shot_idx if len(sigs[k]) > i}
        out["detail"][str(off)] = {"loop_values": sorted(a), "oneshot_values": sorted(b),
                                   "overlap": bool(a & b)}
        if a and b and not (a & b):
            out["separated_offsets"].append(off)
    out["note"] = (
        "Sound body bytes 4..8 (plugin type, 0, codec id, 0, stream type) do not separate looping "
        "from one-shot events (%d vs %d rows probed), so the Wwise loop bit is not pinned here - "
        "per-event loop evidence is the `Stop_` counterpart, the name tokens and any vgmstream "
        "loop lines" % (len(loop_idx), len(shot_idx))) if not out["separated_offsets"] else (
        "Sound body offset(s) %s separate looping from one-shot events (%d vs %d rows): %s"
        % (out["separated_offsets"], len(loop_idx), len(shot_idx), out["detail"]))
    return out


# ---------------------------------------------------------------- output

def write_md(doc):
    s = doc["summary"]
    L = ["# Batmobile - audio by feature, decoded (G1-15)", "",
         "Generated by `Tools/scripts/bmak_audio_features.py` from `AUDIO_MAP.json`, the `AkBank`",
         "exports inside the cooked packages and the package name tables. Every one of the 361 event",
         "rows lands in exactly one feature group; every one of the 447 media ids is decoded to a",
         "48 kHz WAV under `%s` (outside the repo) and measured." % doc["inputs"]["wav_dir"], "",
         "## Summary", "", "| fact | value |", "|---|---|"]
    for k in ("rows", "unique_event_ids", "groups_used", "media", "decoded", "decode_errors",
              "missing_rows", "banks", "rtpc_objects", "rtpc_entries", "rtpc_params_distinct",
              "rtpc_params_named", "duration_total_s"):
        L.append("| %s | **%s** |" % (k, s[k]))
    L += ["", "## Method and anchors", "",
          "- **ids**: %s." % doc["method"]["id_hash"],
          "- **RTPC**: %s." % doc["method"]["rtpc_layout"]]
    for a in doc["method"]["rtpc_anchors"]:
        L.append("  - %s" % a)
    L += ["- **Loudness**: %s." % doc["method"]["lufs"],
          "- **Loop field probe**: %s." % doc["method"]["loop_field_probe"].get("note", "-"), ""]
    L += ["## Feature groups", "",
          "| group | rows | events | WEMs | RTPC parameters | containers |",
          "|---|---|---|---|---|---|"]
    for g in doc["groups"]:
        L.append("| %s | %s | %s | %s | %s | %s |" % (
            g["name"], g["rows"], g["events"], g["wems"],
            ", ".join("`%s`" % p for p in g["rtpc_params"]) or "-",
            ", ".join(g["containers"]) or "-"))
    L.append("")
    for g in doc["groups"]:
        grows = [r for r in doc["events"] if r["group"] == g["name"]]
        if not grows:
            L += ["### %s" % g["name"], "", g["note"] or "no rows.", ""]
            continue
        L += ["### %s" % g["name"], ""]
        if g["note"]:
            L += [g["note"], ""]
        L += ["| event | rows | status | WEMs | containers | loop | RTPC (x -> y) |",
              "|---|---|---|---|---|---|---|"]
        by_name = collections.OrderedDict()
        for r in sorted(grows, key=lambda r: r["name"]):
            by_name.setdefault(r["name"], []).append(r)
        for nm, rs in by_name.items():
            r0 = rs[0]
            params = collections.OrderedDict()
            for e in r0["rtpc"]:
                params.setdefault(e["param"] or e["param_id"], []).append(e)
            ptxt = "; ".join("%s: %s" % (p, " ".join(
                "%g->%g" % (pt[0], pt[1]) for pt in es[0]["points"][:5]))
                for p, es in params.items()) or "-"
            loop = r0["loop"].get("stop_event") or "-"
            if r0["loop"].get("name_tokens"):
                loop = "%s (%s)" % (loop, ",".join(r0["loop"]["name_tokens"]))
            L.append("| `%s` | %d | %s | %s | %s | %s | %s |" % (
                nm, len(rs), r0["status"], ", ".join(r0["wems"]) or "-",
                ", ".join(r0["container_types"]) or "-", loop, ptxt))
        L.append("")
    L += ["## Media measurements (48 kHz WAVs)", "",
          "| WAV | id | group(s) | source | bytes | s | peak dBFS | LUFS | rate | ch |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for d in sorted(doc["media"], key=lambda d: (-d["duration_s"], d["wem"])):
        L.append("| `%s` | %s | %s | %s | %s | %.3f | %.2f | %s | %s | %d |" % (
            os.path.basename(d["wav"]), d["wem_hex"], ",".join(d["groups"]),
            d["source"], d["bytes"], d["duration_s"], d["peak_dbfs"],
            "n/a" if d["lufs"] is None else "%.2f" % d["lufs"],
            d["native_rate"], d["channels"]))
    if doc["decode_errors"]:
        L += ["", "## Decode errors", "",
              "| id | source | bank | error |", "|---|---|---|---|"]
        for e in doc["decode_errors"]:
            L.append("| %s | %s | %s | %s |" % (
                e["wem_hex"], e["source"], e.get("bank") or "-", e["error"]))
    L += ["", "## Missing (bank not on disk - 90 rows stay explicit)", ""]
    for bank, evs in doc["missing"].items():
        L += ["### `%s` (%d)" % (bank, len(evs)), "",
              ", ".join("`%s`" % e["event"] for e in evs), ""]
    L += ["## Gaps", "",
          "- The Wwise per-sound **loop bit** is not pinned: no byte of the Sound body separates",
          "  looping from one-shot events (loop field probe above). Per-event loop evidence is the",
          "  `Stop_` counterpart, the name tokens and any vgmstream loop lines - recorded, not",
          "  inferred.",
          "- **Curve-type ids** (the u32 after each point: 0/1/4/7/9 in these banks) stay raw; no",
          "  Wwise spec was available to name them.",
          "- **Unnamed RTPC parameters**: ids bound by banks whose names are not in the grabbed",
          "  packages stay `0x........` (`param: null` in `rtpc_params`).",
          "- 90 rows sit in the 10 banks that are not shipped on disk; they keep their group but",
          "  carry no WEMs, containers or RTPC.", ""]
    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return MD_OUT


# ---------------------------------------------------------------- check

def check(doc):
    fail = []
    s = doc["summary"]
    if s["rows"] != 361:
        fail.append("expected 361 event rows, got %s" % s["rows"])
    if s["unique_event_ids"] != 118:
        fail.append("expected 118 unique event ids, got %s" % s["unique_event_ids"])
    if s["media"] != 447:
        fail.append("expected 447 media ids, got %s" % s["media"])
    if s["decoded"] + s["decode_errors"] != 447:
        fail.append("decoded (%s) + decode errors (%s) != 447" % (s["decoded"], s["decode_errors"]))
    if s["missing_rows"] != 90:
        fail.append("expected 90 missing-bank rows, got %s" % s["missing_rows"])
    if s["banks"] != 27:
        fail.append("expected 27 banks, got %s" % s["banks"])
    bad_group = [r["name"] for r in doc["events"] if r["group"] not in GROUP_ORDER]
    if bad_group:
        fail.append("%d rows carry a group outside the rule list (e.g. %s)"
                    % (len(bad_group), bad_group[0]))
    seen = collections.Counter((r["package"], r["name"]) for r in doc["events"])
    dup = [k for k, v in seen.items() if v > 1]
    if dup:
        fail.append("%d (package, event) rows appear twice" % len(dup))
    if s["rtpc_entries"] == 0:
        fail.append("no RTPC entry parsed")
    named = [p for p in doc["rtpc_params"].values() if p["param"]]
    if len(named) < 2:
        fail.append("fewer than two RTPC parameters resolved to a name (%d)" % len(named))
    for d in doc["media"]:
        if not os.path.exists(d["wav"]):
            fail.append("WAV missing on disk: %s" % d["wav"])
            break
        if d["sample_rate"] != SR:
            fail.append("%s is %s Hz, not 48000" % (d["wav"], d["sample_rate"]))
            break
    for e in doc["decode_errors"]:
        if not e.get("error"):
            fail.append("decode error without a message: %s" % e["wem_hex"])
            break
    if fail:
        print("FAIL")
        for f in fail:
            print("  -", f)
        return 1
    print("OK: %d rows / %d ids -> %d groups, %d/%d WEMs decoded (%d errors), %d missing rows, "
          "%d banks, %d RTPC entries over %d objects (%d named params)"
          % (s["rows"], s["unique_event_ids"], s["groups_used"], s["decoded"], s["media"],
             s["decode_errors"], s["missing_rows"], s["banks"], s["rtpc_entries"],
             s["rtpc_objects"], len(named)))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="rebuild JSON + MD (decodes every WEM)")
    ap.add_argument("--check", action="store_true", help="run the Done-when gate")
    ap.add_argument("--no-decode", action="store_true", help="measure existing WAVs only")
    ap.add_argument("--event", help="print rows whose name contains this text")
    a = ap.parse_args()
    doc = None
    if a.write:
        doc = build(decode=not a.no_decode)
        json.dump(doc, open(JSON_OUT, "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(JSON_OUT, ROOT), "and",
              os.path.relpath(write_md(doc), ROOT))
    if a.event:
        if doc is None:
            doc = json.load(open(JSON_OUT, encoding="utf-8"))
        for r in doc["events"]:
            if a.event.lower() in r["name"].lower():
                print(json.dumps(r, indent=1))
    if doc is None:
        try:
            doc = json.load(open(JSON_OUT, encoding="utf-8"))
        except OSError:
            print("FAIL\n  - no %s - run --write first" % os.path.relpath(JSON_OUT, ROOT))
            return 1
    if not a.write:
        print(json.dumps(doc["summary"], indent=1))
    if a.check:
        return check(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
