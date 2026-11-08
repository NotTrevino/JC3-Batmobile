#!/usr/bin/env python3
"""v03_wiring_rc2.py - V-03 wiring gates on `Builds/bm-RC2` (offline, read-only).

The original `v03_wiring.py` hardcodes `Builds/bm-RC1` and has no build argument, so this
sibling runs the same five gates on bm-RC2 and adds what the card asks for: every dangling
reference is reported with the carrier **file** and the **byte offset** where the reference
is written, not just a message.

Gates (same definitions as v03_wiring.py):
  G1 points   every SWeaponPoint part reference names a part in the built parts module
  G2 ids      every non-null objectid resolves to an object of the same graph (or one the
              vanilla donor .epe also references cross-file)
  G3 refs     every asset path in the .epe and the edited .vmodc modules resolves in the
              build (`<path>` or `<path>c`) or in Research/JC3Grab/INDEX.jsonl
  G4 audio    bm_audio.py --check + `.ee.fmod_guids` == B-11's (GUID/event/tune failures
              are counted separately from the manifest-record failure)
  G5 drop     Rebel Drop item hash = hash(leaf) and the leaf .ee/.toc/icon ship in the drop tree

Outputs (the card's paths):
  Builds/bm-RC2/verify/wiring.json
  Builds/bm-RC2/verify/wiring.md

  python Tools/scripts/v03_wiring_rc2.py --write
  python Tools/scripts/v03_wiring_rc2.py --check
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
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_leaf      # noqa: E402
import bm_parts     # noqa: E402
import bm_rebel     # noqa: E402
import eetoc        # noqa: E402
import jc3adf       # noqa: E402
import jc3index     # noqa: E402
import jc3weapons   # noqa: E402
import jc3strings   # noqa: E402

TAG = "bm-RC2"
RC = os.path.join(ROOT, "Builds", TAG)
OUTD = os.path.join(RC, "verify")
DIR, OLD, NEW = bm_leaf.DIR, bm_leaf.OLD, bm_leaf.NEW
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
PATH_RE = re.compile(r"^[a-z0-9_]+(/[a-z0-9_.\-]+)+\.[a-z_]+$")
OBJ_RE = re.compile(r"<value (?:id|name)=\"([^\"]+)\" type=\"objectid\">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<")


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
    """Byte forms a reference can take in its carrier (text, or a packed objectid)."""
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


VOLATILE_AUDIO = re.compile(r"bm_bank_manifest\.json differs from the re-derived record"
                          r"|dropzone_at_build")


def split_audio_fails(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split `bm_audio.py --check` FAIL lines into gating failures and volatile manifest drift.

    The manifest records `installer.dropzone_at_build`: the presence, byte size and mtime of the
    banks in the live game dropzone at build time. Re-probing them later cannot reproduce the
    snapshot - the game and any installer rewrite that directory - so that comparison is
    environment state, not build state, and must not decide this gate or enter these documents.

    Every other line - bank, sample, payload, frames, name, duration, event, tune, GUID,
    fmod_guids, install.ps1 - stays gating.
    """
    gating: list[str] = []
    volatile: list[str] = []
    for l in lines:
        if not l.startswith("FAIL:"):
            continue
        (volatile if VOLATILE_AUDIO.search(l) else gating).append(l)
    return gating, volatile


def main(write: bool) -> int:
    if not os.path.exists(os.path.join(RC, "receipt.json")):
        print("BLOCKED: Builds/bm-RC2 missing")
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
    epe_name = DIR + NEW + ".epe"
    epe_blob = get(epe_name)
    tmp = tempfile.mkdtemp(prefix="v03rc2_")
    try:
        xml = epe_xml(epe_blob, tmp)
        vx = "\n".join(
            epe_xml(jc3weapons.read_row(jc3strings.load_index()[DIR + "v0300_car_kensington_sportsmuscle_" + lf + ".epe"],
                                        jc3index.DEFAULT_GAME), tmp)
            for lf in ("civilian_01", "signature_preorder"))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    v_ids = set(m.upper() for m in re.findall(r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', vx))
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
        off, how = locate(carrier_blob, value)
        dangling.append({"gate": gid, "kind": kind, "value": value,
                         "file": carrier, "offset": off,
                         "offset_hex": ("0x%x" % off) if off is not None else None,
                         "method": how, "message": message})

    # G1 weapon points
    pts, bad1 = 0, []
    for m in re.finditer(r'<object[^>]*>\s*<value name="_class" type="string">SWeaponPoint</value>(.*?)</object>',
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
         "%d objectid references -> %d objects; %d cross-file refs the vanilla .epe also makes "
         "(%d distinct); dangling %d" % (len(refs), len(ids), len(external), len(v_ext), len(bad2)))

    # G3 asset paths (the .epe + every edited .vmodc)
    paths: dict[str, tuple[str, bytes | None]] = {}
    for pth in set(re.findall(r'type="string">([a-z0-9_]+(?:/[a-z0-9_.\-]+)+\.[a-z_]+)<', xml)):
        paths.setdefault(pth, (epe_name, epe_blob))
    mods = [f["path"] for f in rec["aaf"]["list"]
            if f["path"].endswith(".vmodc") and f["owner_card"] != "base (bm-005 lineage)"]
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
        hit = next((("build", c) for c in (pth, pth + "c") if c in build), None) or \
              next((("archive", c) for c in (pth, pth + "c") if c in index), None) or \
              (("vanilla .epe uses it", pth) if pth in v_paths else None)
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

    # G4 audio: bm_audio's verdict, split into GUID/event/tune failures vs the manifest record
    r = subprocess.run([sys.executable, os.path.join(HERE, "bm_audio.py"), "--check"],
                       capture_output=True, text=True)
    out_lines = [l for l in (r.stdout or "").strip().splitlines() if l]
    gating, volatile = split_audio_fails(out_lines)
    guid_fails = [l for l in gating
                  if re.search(r"(bank|event|tune|GUID|payload|sample|frames|name|duration)", l)]
    other_fails = [l for l in gating if l not in guid_fails]
    g = DIR + NEW + ".ee.fmod_guids"
    b11 = os.path.join(ROOT, "Builds", "bm-004", "aaf", DIR + OLD + ".ee.fmod_guids")
    same = os.path.exists(b11) and get(g) == open(b11, "rb").read()
    audio_ok = not gating and same
    gate("G4", audio_ok,
         "%d gating failure(s) (%d bank/sample/event/GUID, %d other); manifest record excluded "
         "(live installer.dropzone_at_build snapshot, volatile); .ee.fmod_guids == B-11's: %s"
         % (len(gating), len(guid_fails), len(other_fails), same))
    audio_failures = []
    if not same:
        audio_failures.append({"gate": "G4", "file": g,
                               "offset": None, "message": ".ee.fmod_guids differs from B-11's"})
    for l in gating:
        audio_failures.append({"gate": "G4", "file": "Working/Audio/bm_bank_manifest.json",
                               "offset": None, "message": l})

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

    doc = {
        "schema": 1, "card": "V-03", "build": TAG,
        "ee": {"path": os.path.relpath(ee, ROOT).replace(os.sep, "/"), "sha256": sha(ee),
               "toc": os.path.relpath(ee + ".toc", ROOT).replace(os.sep, "/"),
               "toc_sha256": sha(ee + ".toc"), "inner_entries": len(inner),
               "toc_entries": len(toc)},
        "receipt": {"path": os.path.relpath(os.path.join(RC, "receipt.json"), ROOT).replace(os.sep, "/"),
                    "sha256": sha(os.path.join(RC, "receipt.json")),
                    "card": rec.get("card"), "tag": rec.get("tag")},
        "epe": {"file": epe_name, "sha256": hashlib.sha256(epe_blob or b"").hexdigest(),
                "xml_lines": len(xml.splitlines()), "objects": len(ids)},
        "gates": gates,
        "gate_failures": audio_failures,
        "dangling": dangling,
        "counts": {"points": pts, "objectid_refs": len(refs), "paths": len(res),
                   "edited_modules": len(mods), "dangling": len(dangling),
                   "gate_failures": len(audio_failures)},
        "verdict": "PASS" if not dangling and not audio_failures else "FAIL",
    }
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"

    L: list[str] = []
    A = L.append
    A("# V-03 wiring gates on %s" % TAG)
    A("")
    A("Generated by `Tools/scripts/v03_wiring_rc2.py --write`; `--check` re-reads the packed")
    A("`.ee`, re-decodes every module, re-runs every gate and compares both artefacts byte for")
    A("byte. Offline and read-only: no install script, no game process.")
    A("")
    A("```")
    for x in gates:
        A(("PASS " if x["ok"] else "FAIL ") + x["gate"] + " " + x["line"])
    A("%s: dangling %d, gate failures %d" % (doc["verdict"], len(dangling), len(audio_failures)))
    A("```")
    A("")
    A("## Dangling references (file + offset)")
    A("")
    if dangling:
        A("| gate | kind | value | file | offset | how found |")
        A("|---|---|---|---|---:|---|")
        for x in dangling:
            A("| %s | %s | `%s` | `%s` | %s | %s |"
              % (x["gate"], x["kind"], x["value"].replace("|", "\\|"), x["file"],
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
            A("| %s | `%s` | %s | %s |" % (x["gate"], x["file"],
                                          "n/a (record)" if x["offset"] is None else "0x%x" % x["offset"],
                                          x["message"].replace("|", "\\|")))
    else:
        A("None.")
    A("")
    if audio_failures:
        A("%d gating audio failure(s), listed above - build defects, not environment drift."
          % len(audio_failures))
    else:
        A("The audio gate is green on every wiring-relevant value: no bank, sample, payload,")
        A("frames, name, duration, event, tune or GUID failure, and the `.ee.fmod_guids` of this")
        A("build is byte-identical to B-11's.")
    A("")
    A("`bm_audio.py`'s **manifest-record comparison is excluded from this gate.** That record")
    A("embeds `installer.dropzone_at_build`: the *presence, byte size and mtime* of the banks in")
    A("the live game dropzone as it stood at build time. Re-probing them later cannot reproduce")
    A("the snapshot - the game and any installer rewrite that directory - so the comparison drifts")
    A("with the machine, not with the build. It is environment state: feeding it back in would")
    A("make `--check` non-deterministic. The observed drift is named in the card")
    A("(`tmp/freebuff/reports/v03-rc2-check-fix.md`), never in this document.")
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
    A("* Whether bm-RC2 loads in play and the wired points/fx/audio behave - the test ban")
    A("  forbids launching the game; this gate is static.")
    A("* `bm_audio.py --check` still exits 1 while its manifest record's")
    A("  `installer.dropzone_at_build` snapshot differs from the live dropzone. That is exactly")
    A("  the exclusion above; it is not a wiring fact and this document does not depend on it.")
    A("* No field here is a timestamp, a path separator or a live probe, so `--check` is")
    A("  deterministic: it regenerates the document byte for byte on any machine.")
    A("")
    md = "\n".join(L) + "\n"

    for x in gates:
        print(("PASS " if x["ok"] else "FAIL ") + x["gate"] + ": " + x["line"])
    print("%s: dangling %d, gate failures %d" % (doc["verdict"], len(dangling), len(audio_failures)))
    for x in dangling:
        print("   %s  file=%s offset=%s  %s" % (x["gate"], x["file"],
                                                x["offset_hex"] or "UNKNOWN", x["message"]))

    jp, mp = os.path.join(OUTD, "wiring.json"), os.path.join(OUTD, "wiring.md")
    if write:
        open(jp, "w", encoding="utf-8", newline="\n").write(js)
        open(mp, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote Builds/%s/verify/wiring.json + wiring.md" % TAG)
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
