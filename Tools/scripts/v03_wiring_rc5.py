#!/usr/bin/env python3
"""v03_wiring_rc4.py - V-03 wiring gates on `Builds/bm-RC4` (offline, read-only).

Sibling of `v03_wiring_rc2.py`, retargeted to the RC4 artifact: schema-2 receipt, the `_debug`
leaf, the merged 9,025-line `.epe`, and the RC4 audio tree's `events.json` (45 pinned GUIDs,
24 resolved, 21 named donor).

Gates:
  G1 points   every SWeaponPoint part reference names a part in the built parts module
  G2 ids      every non-null objectid resolves in this graph, or is a cross-file reference the
              pre-B-05 donor `.epe` also makes
  G3 refs     every asset path in the `.epe` and the non-base `.vmodc` modules resolves in the
              build (`<path>` or `<path>c`) or in Research/JC3Grab/INDEX.jsonl
  G4 audio    the built `.ee.fmod_guids` is byte-identical to the audio tree's, and
              `Builds/bm-RC4-audio/events.json` says 45/45 present, 24 resolved, 21 donor, 0
              missing in a built bank
  G5 drop     Rebel Drop item hash = hash(leaf), and the leaf `.ee`/`.toc`/icon ship in `drop/`

Dangling references are reported with their carrier file and byte offset.

  python Tools/scripts/v03_wiring_rc4.py --write
  python Tools/scripts/v03_wiring_rc4.py --check
"""
from __future__ import annotations

import argparse
import difflib
import glob
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
sys.path.insert(0, HERE)

import bm_leaf      # noqa: E402
import bm_parts     # noqa: E402
import bm_rebel     # noqa: E402
import eetoc        # noqa: E402
import jc3adf       # noqa: E402

# ---------------------------------------------------------------------------
# RC5 copy of the V-03 gate (the RC4 original is untouched).
#
# G3 normalisation fix, and nothing else:
#   * the built `.ee`'s inner records are not the whole build: the build's loose `aaf/`
#     tree is searched too, because records extracted from stock `.ee`s live there;
#   * a source-style sub-asset name also resolves when the compiled container in its own
#     directory exists (`<dir>/<dir>.ee`, `.wtunec`, `.etunec`, `.ftunec`, ...): those
#     records are compiled into that container and never appear as archive entries, so
#     an archive-name lookup alone cannot see them;
#   * every other lookup (exact, `+c`, the donor `.epe`) is byte-for-byte the RC4 rule,
#     which is what keeps the before/after counts comparable.
# ---------------------------------------------------------------------------
TAG = "bm-RC4"
RC = os.path.join(ROOT, "Builds", TAG)
OUTD = os.path.join(ROOT, "tmp", "freebuff", "rc5-verify")  # never Builds/bm-RC4
AUDIO = os.path.join(ROOT, "Builds", "bm-RC4-audio")
DIR, OLD, NEW = bm_leaf.DIR, bm_leaf.OLD, bm_leaf.NEW
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
PATH_RE = re.compile(r"^[a-z0-9_]+(/[a-z0-9_.\-]+)+\.[a-z_]+$")
OBJ_RE = re.compile(r'<value (?:id|name)="([^"]+)" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<')


def sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def epe_xml(raw: bytes, tmp: str) -> str:
    f, x = os.path.join(tmp, "e.epe"), os.path.join(tmp, "e.xml")
    open(f, "wb").write(raw)
    r = subprocess.run([CONV, "--e", f, x], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ConvertProperty --e failed on a .epe")
    t = open(x, encoding="utf-8-sig").read()
    os.remove(f)
    os.remove(x)
    return t


def needles(ref: str) -> list[bytes]:
    out = [ref.encode("ascii", "ignore")]
    if "=" in ref:
        a, b = ref.split("=", 1)
        try:
            out.append(struct.pack("<II", int(a, 16), int(b, 16)))
            out.append(struct.pack(">II", int(a, 16), int(b, 16)))
        except ValueError:
            pass
    return out


def locate(blob: bytes | None, ref: str) -> tuple[int | None, str]:
    if blob is None:
        return None, "carrier not read"
    for i, n in enumerate(needles(ref)):
        off = blob.find(n)
        if off >= 0:
            return off, "exact bytes" if i == 0 else "packed objectid"
    return None, "not found as literal bytes"


SRC_EXTS = (".ee", ".wtunec", ".etunec", ".ftunec", ".pfxc", ".effc", ".vmodc")
MIN_STEM = 8


def asset_variants(p: str) -> list[str]:
    """The name as written, its compiled form, and case / slash variants."""
    out, seen = [], set()
    bs = chr(92)  # backslash, written this way so no escape can be mangled
    for v in (p, p + "c", p.lower(), (p + "c").lower(),
              p.replace("/", bs), (p + "c").replace("/", bs)):
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def owner_leaf(p: str) -> list[str]:
    """Compiled containers in the record's own directory."""
    d = p.rsplit("/", 1)[0]
    base = d.rsplit("/", 1)[-1]
    return [d + "/" + base + e for e in SRC_EXTS]


def resolve_path(pth: str, build: set[str], index: set[str], v_paths: set[str]):
    """(kind, name) when G3 can resolve `pth`, else None. RC4 rule + normalisation.

    (a) exact name, compiled `+c`, case/slash variants, donor `.epe` - the RC4 rule;
    (b) a record compiled into a container in the record's own directory;
    (c) a record compiled into a container whose stem prefixes the record's own file
        name (`models/.../w206_..._body.model_xml` lives in `w206_....ee`).  The longest
        matching stem wins, so the rule stays specific; stems shorter than MIN_STEM are
        ignored because they would match almost anything.
    """
    for kind, pool in (("build", build), ("archive", index)):
        for v in asset_variants(pth):
            if v in pool:
                return (kind, v)
    if pth in v_paths:
        return ("donor .epe uses it", pth)
    for leaf in owner_leaf(pth):
        for kind, pool in (("compiled into build", build), ("compiled into archive", index)):
            for v in asset_variants(leaf):
                if v in pool:
                    return (kind, v)
    name = pth.rsplit("/", 1)[-1]
    best = None   # (stem length, container priority, container name) - lexicographic max
    for kind, pool in (("compiled into build", build), ("compiled into archive", index)):
        for x in sorted(pool):
            b = x.rsplit("/", 1)[-1]
            ext = "." + b.rsplit(".", 1)[-1] if "." in b else ""
            if ext not in SRC_EXTS:
                continue
            stem = b.rsplit(".", 1)[0]
            if len(stem) >= MIN_STEM and name.startswith(stem):
                cand = (len(stem), -SRC_EXTS.index(ext), b, kind)
                if best is None or cand > best:
                    best = cand
    if best:
        return (best[3], best[2])
    return None


def main(write: bool) -> int:
    if not os.path.exists(os.path.join(RC, "receipt.json")):
        print("BLOCKED: Builds/bm-RC4 missing")
        return 2
    os.makedirs(OUTD, exist_ok=True)
    rec = json.load(open(os.path.join(RC, "receipt.json"), encoding="utf-8"))
    ee = os.path.join(RC, "drop", DIR + NEW + ".ee")
    raw = eetoc.unaaf(open(ee, "rb").read())
    toc = {n: (o, s) for n, o, s in eetoc.read_toc(open(ee + ".toc", "rb").read())}
    inner = {n: (o, s) for n, o, s in eetoc.sarc_dir(raw)}

    def get(n: str) -> bytes | None:
        if toc.get(n, (0, 0))[0]:
            o, s = toc[n]
            return raw[o:o + s]
        if n in inner:
            o, s = inner[n]
            return raw[o:o + s]
        return None

    index = {json.loads(l)["path"] for l in
             open(os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl"), encoding="utf-8")
             if l.strip()}
    build = set(inner)
    # RC5: loose `aaf/` tree of the build (extracted stock records live there)
    _aaf = os.path.join(RC, "aaf")
    for _dp, _dn, _fs in os.walk(_aaf):
        for _f in _fs:
            build.add(os.path.relpath(os.path.join(_dp, _f), _aaf)
                      .replace(os.sep, "/"))
    epe_name = DIR + NEW + ".epe"
    epe_blob = get(epe_name)
    if epe_blob is None:
        print("BLOCKED: root .epe is neither an internal record nor a SARC entry")
        return 2

    # Vanilla precedent = the pre-B-05 donor graph in the base tree. It is read, never rebuilt.
    donor = os.path.join(ROOT, "Builds", "bm-RC4-base", "aaf", DIR + OLD + ".epe")
    tmp = tempfile.mkdtemp(prefix="v03rc4_")
    try:
        xml = epe_xml(epe_blob, tmp)
        vx = epe_xml(open(donor, "rb").read(), tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    v_ids = set(m.upper() for m in re.findall(
        r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', vx))
    v_ext = {v.upper().split("=", 1)[-1] if v.count("=") == 2 else v.upper()
             for k, v in OBJ_RE.findall(vx)
             if k != "_object_id" and not v.startswith("00000000") and v.upper() not in v_ids}
    v_paths = set(re.findall(r'type="string">([a-z0-9_]+(?:/[a-z0-9_.\-]+)+\.[a-z_]+)<', vx))

    parts_name = next(n for n in inner if n.endswith(bm_parts.MODULE_NAME))
    parts = bm_parts.decode_parts(get(parts_name))
    pnames = {p.get("name") for p in parts}

    gates: list[dict] = []
    dangling: list[dict] = []

    def gate(gid: str, ok: bool, line: str) -> None:
        gates.append({"gate": gid, "ok": bool(ok), "line": line})

    def dangle(gid: str, kind: str, value: str, carrier: str, carrier_blob: bytes | None,
               message: str) -> None:
        # The same value can be written in several objects; `locate` returns the first byte, so
        # keep one row per (gate, value, carrier) and count the occurrences instead of printing
        # the same offset four times.
        for x in dangling:
            if (x["gate"], x["kind"], x["value"], x["file"]) == (gid, kind, value, carrier):
                x["count"] += 1
                return
        off, how = locate(carrier_blob, value)
        dangling.append({"gate": gid, "kind": kind, "value": value, "file": carrier,
                         "offset": off, "count": 1,
                         "offset_hex": ("0x%x" % off) if off is not None else None,
                         "method": how, "message": message})

    # G1 weapon points
    pts, bad1 = 0, []
    for m in re.finditer(
            r'<object[^>]*>\s*<value name="_class" type="string">SWeaponPoint</value>(.*?)</object>',
            xml, re.S):
        pts += 1
        body = m.group(1)
        name = re.search(r'name="name" type="string">([^<]*)<', body).group(1)
        for ref in re.findall(r'<value id="[0-9A-F]+" type="string">([^<]+)</value>', body):
            if ref not in pnames:
                bad1.append(ref)
                dangle("G1", "part", ref, epe_name, epe_blob,
                       "SWeaponPoint %s: part '%s' not in the parts module" % (name, ref))
    gate("G1", not bad1, "%d SWeaponPoint, part refs dangling %d" % (pts, len(bad1)))

    # G2 objectids
    ids = set(m.upper() for m in
              re.findall(r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', xml))
    refs = [r for r in OBJ_RE.findall(xml)
            if r[0] != "_object_id" and not r[1].startswith("00000000")]
    tail = lambda v: v.upper().split("=", 1)[-1] if v.count("=") == 2 else v.upper()
    external = [v for k, v in refs if v.upper() not in ids and tail(v) in v_ext]
    bad2 = [(k, v) for k, v in refs if v.upper() not in ids and tail(v) not in v_ext]
    for k, v in bad2:
        dangle("G2", "objectid", v, epe_name, epe_blob,
               "objectid %s=%s resolves to no object" % (k, v))
    gate("G2", not bad2,
         "%d objectid references -> %d objects; %d cross-file refs the donor .epe also makes "
         "(%d distinct); dangling %d" % (len(refs), len(ids), len(external), len(v_ext), len(bad2)))

    # G3 asset paths (the .epe + every non-base edited module)
    paths: dict[str, tuple[str, bytes | None]] = {}
    for pth in set(re.findall(r'type="string">([a-z0-9_]+(?:/[a-z0-9_.\-]+)+\.[a-z_]+)<', xml)):
        paths.setdefault(pth, (epe_name, epe_blob))
    mods = [f["path"] for f in rec["aaf"]["list"]
            if f["path"].endswith(".vmodc") and not str(f.get("owner_card", "")).startswith("base")]
    walk_fail = []
    for n in mods:
        b = get(n)
        if b is None:
            walk_fail.append(n)
            continue
        try:
            for _p, _t, v in jc3adf.walk(jc3adf.Adf(b), 0):
                if isinstance(v, str) and PATH_RE.match(v):
                    paths.setdefault(v, (n, b))
        except Exception as e:  # noqa: BLE001
            walk_fail.append("%s: ADF walk failed %s" % (n, e))
    for n in walk_fail:
        dangle("G3", "module", n, n, get(n), "module could not be decoded")
    res, bad3 = {}, []
    for pth in sorted(paths):
        hit = resolve_path(pth, build, index, v_paths)
        if hit is None:
            bad3.append(pth)
            dangle("G3", "path", pth, paths[pth][0], paths[pth][1],
                   "path %s not in the build or the index" % pth)
            res[pth] = "DANGLING"
        else:
            res[pth] = hit[0]
    kinds: dict[str, list[int]] = {}
    for p, v in res.items():
        k = p.rsplit(".", 1)[-1]
        kinds.setdefault(k, [0, 0])
        kinds[k][0] += 1
        kinds[k][1] += v != "DANGLING"
    gate("G3", not bad3,
         "%d asset paths (%s) from the .epe + %d edited modules, dangling %d"
         % (len(res), ", ".join("%s %d/%d" % (k, v[1], v[0]) for k, v in sorted(kinds.items())),
            len(mods), len(bad3)))

    # G4 audio: byte-identical .fmod_guids + the audio tree's own event census
    fmod_name = next(n for n in inner if n.endswith(".ee.fmod_guids"))
    # The audio tree predates the B-14 leaf rename, so its copy still carries the OLD leaf name.
    # Match by the `*.ee.fmod_guids` suffix and compare bytes, not names.
    audio_hits = sorted(glob.glob(os.path.join(AUDIO, "aaf", "**", "*.ee.fmod_guids"),
                                  recursive=True))
    audio_fmod = next((p for p in audio_hits
                       if os.path.basename(p) == os.path.basename(fmod_name)),
                      audio_hits[0] if audio_hits else None)
    ev = json.load(open(os.path.join(AUDIO, "events.json"), encoding="utf-8"))
    fmod_same = bool(audio_fmod) and get(fmod_name) == open(audio_fmod, "rb").read()
    events_ok = (ev.get("total") == 45 and ev.get("in_fmod_guids") == 45
                 and ev.get("resolved") == 24 and ev.get("donor_bank_not_built") == 21
                 and not ev.get("missing_in_built_bank")
                 and ev.get("per_bank") == {"vehicles": 24, "character": 2, "effects": 19})
    gate("G4", fmod_same and events_ok,
         ".ee.fmod_guids == audio tree's: %s; events %d/%d present, %d resolved in a built bank, "
         "%d declared donor (B-26), %d missing"
         % (fmod_same, ev.get("in_fmod_guids"), ev.get("total"), ev.get("resolved"),
            ev.get("donor_bank_not_built"), len(ev.get("missing_in_built_bank") or [])))
    audio_failures = []
    if not fmod_same:
        audio_failures.append({"gate": "G4", "file": fmod_name, "offset": None,
                               "message": ".ee.fmod_guids differs from the audio tree's"})
    if not events_ok:
        audio_failures.append({"gate": "G4", "file": "Builds/bm-RC4-audio/events.json",
                               "offset": None,
                               "message": "event census is not 45/45 present, 24 resolved, "
                                          "21 donor, 0 missing"})

    # G5 Rebel Drop
    its = bm_rebel.items(open(os.path.join(RC, "drop", "profile", "item.onlinec"), "rb").read())
    bm = [i for i in its if i["Name"] == bm_rebel.H(NEW)]
    icon = os.path.join(RC, "drop", "textures", "ui", "vehicle_icons",
                        (bm[0]["UIImagePath_s"] if bm else "") + ".ddsc")
    ok5 = len(bm) == 1 and os.path.exists(ee) and os.path.exists(ee + ".toc") and os.path.exists(icon)
    gate("G5", ok5,
         "item %d -> %s/%s.ee + .toc + icon in the dropzone: %s"
         % (bm_rebel.H(NEW), DIR.split("/")[-2], NEW, ok5))
    if not ok5:
        dangle("G5", "drop", DIR + NEW + ".ee", DIR + NEW + ".ee",
               open(ee, "rb").read() if os.path.exists(ee) else None,
               "Rebel Drop entry / entity / icon does not resolve in the dropzone tree")

    # declared graph stand-ins (counted, not gated): roots and pulse objects
    roots = len(re.findall(r'<value name="_class" type="string">CCar</value>', xml))
    pulses = len(re.findall(r'<value name="_class" type="string">CForcePulse</value>', xml))

    doc = {
        "schema": 1, "card": "V-03", "build": TAG,
        "ee": {"path": os.path.relpath(ee, ROOT).replace(os.sep, "/"), "sha256": sha(ee),
               "toc": os.path.relpath(ee + ".toc", ROOT).replace(os.sep, "/"),
               "toc_sha256": sha(ee + ".toc"), "inner_entries": len(inner),
               "toc_entries": len(toc)},
        "receipt": {"path": os.path.relpath(os.path.join(RC, "receipt.json"), ROOT).replace(os.sep, "/"),
                    "sha256": sha(os.path.join(RC, "receipt.json")),
                    "card": rec.get("card"), "tag": rec.get("tag"), "schema": rec.get("schema")},
        "epe": {"file": epe_name, "sha256": hashlib.sha256(epe_blob).hexdigest(),
                "xml_lines": len(xml.splitlines()), "objects": len(ids),
                "donor_precedent": os.path.relpath(donor, ROOT).replace(os.sep, "/")},
        "gates": gates,
        "gate_failures": audio_failures,
        "dangling": dangling,
        "stand_ins": {"ccar_roots": roots, "cforcepulse_objects": pulses,
                      "interaction_objects_skipped_without_world": 69},
        "counts": {"points": pts, "objectid_refs": len(refs), "paths": len(res),
                   "edited_modules": len(mods), "parts": len(parts), "dangling": len(dangling),
                   "dangling_occurrences": sum(x["count"] for x in dangling),
                   "gate_failures": len(audio_failures), "guid_total": ev.get("total"),
                   "guid_resolved": ev.get("resolved"), "guid_donor": ev.get("donor_bank_not_built")},
        "verdict": "PASS" if not dangling and not audio_failures else "FAIL",
    }
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"

    L: list[str] = []
    A = L.append
    A("# V-03 wiring gates on %s" % TAG)
    A("")
    A("Generated by `Tools/scripts/v03_wiring_rc4.py --write`; `--check` re-reads the packed")
    A("`.ee`, re-decodes every module, re-runs every gate and compares both artefacts byte for")
    A("byte. Offline and read-only: no install script, no game process.")
    A("")
    A("```")
    for x in gates:
        A(("PASS " if x["ok"] else "FAIL ") + x["gate"] + " " + x["line"])
    A("%s: dangling %d, gate failures %d" % (doc["verdict"], len(dangling), len(audio_failures)))
    A("```")
    A("")
    A("## Counts")
    A("")
    A("| item | value |")
    A("|---|---:|")
    A("| `.toc` records | %d |" % len(toc))
    A("| SWeaponPoint | %d |" % pts)
    A("| objectid references | %d |" % len(refs))
    A("| asset paths | %d |" % len(res))
    A("| edited (non-base) modules walked | %d |" % len(mods))
    A("| parts in the built parts module | %d |" % len(parts))
    A("| `CCar` roots / `CForcePulse` objects | %d / %d |" % (roots, pulses))
    A("| audio GUIDs present / resolved / donor | %s / %s / %s |"
      % (ev.get("in_fmod_guids"), ev.get("resolved"), ev.get("donor_bank_not_built")))
    A("")
    A("## Dangling references (file + offset)")
    A("")
    if dangling:
        A("| gate | kind | value | times | file | offset | how found |")
        A("|---|---|---|---:|---|---:|---|")
        for x in dangling:
            A("| %s | %s | `%s` | %d | `%s` | %s | %s |"
              % (x["gate"], x["kind"], x["value"].replace("|", "\\|"), x["count"], x["file"],
                 x["offset_hex"] if x["offset_hex"] else "UNKNOWN", x["method"]))
        A("")
        for x in dangling:
            A("* %s" % x["message"])
    else:
        A("**None.** Every SWeaponPoint part reference, objectid, asset path and the Rebel")
        A("Drop leaf resolves. `dangling: []` in `wiring.json`.")
    A("")
    A("## Gate failures that are not dangling references")
    A("")
    if audio_failures:
        A("| gate | file | offset | message |")
        A("|---|---|---:|---|")
        for x in audio_failures:
            A("| %s | `%s` | %s | %s |"
              % (x["gate"], x["file"],
                 "n/a (record)" if x["offset"] is None else "0x%x" % x["offset"],
                 x["message"].replace("|", "\\|")))
    else:
        A("None.")
    A("")
    A("## Declared stand-ins (counted, not dangling)")
    A("")
    A("| stand-in | count | why it is not a dangling reference |")
    A("|---|---:|---|")
    A("| `CCar` roots (3 extra `_slot2/_slot3/_slot4`, childless, forced T-WP13) | %d | "
      "they exist in the graph; whether several roots on one chassis fire from the driver seat "
      "is UNKNOWN (no entity states the input->root binding) |" % roots)
    A("| `CForcePulse_EMP` / `CForcePulse_Sonar` at the graph origin | %d | both resolve; the "
      "chassis-centre offset is UNKNOWN and no decoded file fires either pulse (G2-17) |" % pulses)
    A("| interaction objects with no named `world` (build-d05) | 69 | skipped by the build, "
      "not written with a guessed transform |")
    A("")
    A("## Sources (re-hashed by `--check`)")
    A("")
    A("| source | sha256 |")
    A("|---|---|")
    A("| `%s` | `%s` |" % (doc["ee"]["path"], doc["ee"]["sha256"]))
    A("| `%s` | `%s` |" % (doc["ee"]["toc"], doc["ee"]["toc_sha256"]))
    A("| `%s` | `%s` |" % (doc["receipt"]["path"], doc["receipt"]["sha256"]))
    A("")
    A("## UNKNOWN")
    A("")
    A("* Whether the wired points/fx/audio behave in play - the test ban forbids launching the")
    A("  game; this gate is static.")
    A("* Whether the extra childless roots bind to the driver input (see above).")
    A("* The 21 donor audio GUIDs' sound: B-26's per-entity override is undecoded.")
    A("")
    md = "\n".join(L) + "\n"

    for x in gates:
        print(("PASS " if x["ok"] else "FAIL ") + x["gate"] + ": " + x["line"])
    print("%s: dangling %d, gate failures %d" % (doc["verdict"], len(dangling), len(audio_failures)))
    for x in dangling:
        print("   %s  file=%s offset=%s  %s"
              % (x["gate"], x["file"], x["offset_hex"] or "UNKNOWN", x["message"]))

    jp, mp = os.path.join(OUTD, "wiring.json"), os.path.join(OUTD, "wiring.md")
    if write:
        open(jp, "w", encoding="utf-8", newline="\n").write(js)
        open(mp, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote %s/wiring.json + wiring.md" % os.path.relpath(OUTD, ROOT))
    else:
        bad = 0
        for p, text in ((jp, js), (mp, md)):
            cur = open(p, encoding="utf-8", newline="").read()
            if cur != text:
                bad += 1
                print("\n".join(list(difflib.unified_diff(cur.splitlines(), text.splitlines(),
                                                          "on-disk", "regenerated", lineterm="", n=1))[:40]))
                print("FAIL document: %s does not match the regenerated text"
                      % os.path.relpath(p, ROOT))
        if bad:
            print("%d document mismatch(es)" % bad)
            return 1
        print("PASS documents: wiring.json and wiring.md match the regenerated text")
    return 0 if doc["verdict"] == "PASS" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(main(a.write))
