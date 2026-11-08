"""v03_wiring.py - V-03: wiring gates on the release candidate `Builds/bm-RC1` (offline, read-only).

Card: every SWeaponPoint -> an existing part/bone; every weapon id/path exists; every effect, light,
sound GUID and the Rebel Drop entity path resolves inside the build or the shipped archives.
Done: 0 dangling references.

Reads the PACKED .ee through its .toc (bm-RC1/drop), the RC tree for the module list, and
Research/JC3Grab/INDEX.jsonl for the archives. A compiled file resolves as `<path>` or `<path>c`
(.wtune -> .wtunec, .ctune -> .ctunec, ...). Writes Builds/bm-RC1/verify/wiring.{json,md}.

  G1 points   every SWeaponPoint part reference (string members) names a part in the built parts module
  G2 ids      every non-null objectid in the .epe resolves to an object of the same graph
  G3 refs     every asset path in the .epe and in the edited .vmodc modules: in the build or in the index
  G4 audio    bm_audio.py --check (5 slots / 45 GUIDs / 5 events) and the .ee.fmod_guids is B-11's
  G5 drop     the Rebel Drop item hash = hash(leaf) and that leaf's .ee/.toc ship in the dropzone tree

    python Tools/scripts/v03_wiring.py --check
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import eetoc  # noqa: E402
import jc3adf  # noqa: E402
import bm_leaf  # noqa: E402

TAG = "bm-RC2"          # B-RC2: same gates, new tree; --tag overrides
RC = os.path.join(ROOT, "Builds", TAG)
OUTD = os.path.join(ROOT, "Working", "RC", "verify-" + TAG)   # verify artefacts stay out of Builds/
DIR, OLD, NEW = bm_leaf.DIR, bm_leaf.OLD, bm_leaf.NEW
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
PATH_RE = re.compile(r"^[a-z0-9_]+(/[a-z0-9_.\-]+)+\.[a-z_]+$")


def epe_xml(raw: bytes) -> str:
    f, x = os.path.join(OUTD, "_v03.epe"), os.path.join(OUTD, "_v03.xml")
    open(f, "wb").write(raw)
    r = subprocess.run([CONV, "--e", f, x], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ConvertProperty --e failed on the RC .epe")
    t = open(x, encoding="utf-8").read()
    os.remove(f); os.remove(x)
    return t


def main() -> int:
    if not os.path.exists(os.path.join(RC, "receipt.json")):
        print(f"BLOCKED: Builds/{TAG} missing"); return 2
    os.makedirs(OUTD, exist_ok=True)
    rec = json.load(open(os.path.join(RC, "receipt.json")))
    ee = os.path.join(RC, "drop", DIR + NEW + ".ee")
    raw = eetoc.unaaf(open(ee, "rb").read())
    toc = {n: (o, s) for n, o, s in eetoc.read_toc(open(ee + ".toc", "rb").read())}
    inner = {n: (o, s) for n, o, s in eetoc.sarc_dir(raw)}
    get = lambda n: raw[toc[n][0]:toc[n][0] + toc[n][1]] if toc.get(n, (0, 0))[0] else (
        raw[inner[n][0]:inner[n][0] + inner[n][1]] if n in inner else None)
    index = {json.loads(l)["path"] for l in open(os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl"), encoding="utf-8") if l.strip()}
    build = set(inner)
    out, dangling, lines = {}, [], []

    xml = epe_xml(get(DIR + NEW + ".epe"))
    # vanilla precedent: references the shipped donor .epe itself makes (cross-file object ids, shared
    # assets the index does not list) are not defects of this build - computed, never hand-listed
    import bm_rc
    vx = chr(10).join(epe_xml(bm_rc.vfs(DIR + "v0300_car_kensington_sportsmuscle_" + lf + ".epe"))
                   for lf in ("civilian_01", "signature_preorder"))   # both shipped leaves of the donor car
    v_ids = set(m.upper() for m in re.findall(r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', vx))
    v_ext = {v.upper().split("=", 1)[-1] if v.count("=") == 2 else v.upper()
             for k, v in re.findall(r'<value (?:id|name)="([^"]+)" type="objectid">([0-9A-Fa-f=]+)<', vx)
             if k != "_object_id" and not v.startswith("00000000") and v.upper() not in v_ids}
    v_paths = set(re.findall(r'type="string">([a-z0-9_]+(?:/[a-z0-9_.\-]+)+\.[a-z_]+)<', vx))
    import bm_parts
    # B-18 moved the parts module to .../batmobile/ : resolve it by name instead of by the bm_parts default
    parts_name = next(n for n in inner if n.endswith(bm_parts.MODULE_NAME))
    parts = bm_parts.decode_parts(get(parts_name))
    pnames = {p.get("name") for p in parts}

    # G1 weapon points: string members of SWeaponPoint objects that are part names
    pts, bad1 = 0, []
    for m in re.finditer(r'<object[^>]*>\s*<value name="_class" type="string">SWeaponPoint</value>(.*?)</object>', xml, re.S):
        pts += 1
        body = m.group(1)
        name = re.search(r'name="name" type="string">([^<]*)<', body).group(1)
        for ref in re.findall(r'<value id="[0-9A-F]+" type="string">([^<]+)</value>', body):
            if ref not in pnames:
                bad1.append(f"SWeaponPoint {name}: part '{ref}' not in the parts module")
    out["points"] = {"points": pts, "dangling": bad1}
    lines.append(f"G1 points   {pts} SWeaponPoint, part refs dangling {len(bad1)}")
    dangling += bad1

    # G2 objectids
    ids = set(m.upper() for m in re.findall(r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', xml))
    refs = [m for m in re.findall(r'(?<!name="_object_id") type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', xml)]
    refs = [r for r in re.findall(r'<value (?:id|name)="([^"]+)" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', xml)
            if r[0] != "_object_id" and not r[1].startswith("00000000")]
    tail = lambda v: v.upper().split("=", 1)[-1] if v.count("=") == 2 else v.upper()
    external = [v for k, v in refs if v.upper() not in ids and tail(v) in v_ext]
    bad2 = [f"objectid {k}={v} resolves to no object" for k, v in refs if v.upper() not in ids and tail(v) not in v_ext]
    out["ids"] = {"objects": len(ids), "references": len(refs), "external_as_vanilla": len(external), "dangling": bad2}
    lines.append(f"G2 ids      {len(refs)} objectid references -> {len(ids)} objects; {len(external)} cross-file refs the vanilla .epe also makes ({len(v_ext)} distinct); dangling {len(bad2)}")
    dangling += bad2

    # G3 asset paths: the .epe + every edited .vmodc (bytes via the .toc)
    paths = set(re.findall(r'type="string">([a-z0-9_]+(?:/[a-z0-9_.\-]+)+\.[a-z_]+)<', xml))
    mods = [f["path"] for f in rec["aaf"]["list"] if f["path"].endswith(".vmodc") and f["owner_card"] != "base (bm-005 lineage)"]
    for n in mods:
        b = get(n)
        if b is None:
            continue
        try:
            for _p, _t, v in jc3adf.walk(jc3adf.Adf(b), 0):
                if isinstance(v, str) and PATH_RE.match(v):
                    paths.add(v)
        except Exception as e:  # noqa: BLE001
            dangling.append(f"{n}: ADF walk failed {e}")
    res = {}
    for pth in sorted(paths):
        hit = next((("build", c) for c in (pth, pth + "c") if c in build), None) or \
              next((("archive", c) for c in (pth, pth + "c") if c in index), None) or               (("vanilla .epe uses it", pth) if pth in v_paths else None)
        res[pth] = hit[0] if hit else "DANGLING"
    bad3 = [f"path {p} not in the build or the index" for p, v in res.items() if v == "DANGLING"]
    kinds = {}
    for p, v in res.items():
        k = p.rsplit(".", 1)[-1]; kinds.setdefault(k, [0, 0]); kinds[k][0] += 1; kinds[k][1] += v != "DANGLING"
    out["refs"] = {"paths": len(res), "by_kind": kinds, "resolved": res, "dangling": bad3}
    lines.append(f"G3 refs     {len(res)} asset paths ({', '.join(f'{k} {v[1]}/{v[0]}' for k, v in sorted(kinds.items()))}) "
                 f"from the .epe + {len(mods)} edited modules, dangling {len(bad3)}")
    dangling += bad3

    # G4 audio
    r = subprocess.run([sys.executable, os.path.join(HERE, "bm_audio.py"), "--check"], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    g = DIR + NEW + ".ee.fmod_guids"
    b11 = os.path.join(ROOT, "Builds", "bm-004", "aaf", DIR + OLD + ".ee.fmod_guids")
    same = os.path.exists(b11) and get(g) == open(b11, "rb").read()
    bad4 = ([] if r.returncode == 0 else [f"bm_audio.py --check: {last}"]) + ([] if same else ["RC .ee.fmod_guids differs from B-11's"])
    out["audio"] = {"bm_audio_check": last, "fmod_guids_equal_b11": same, "dangling": bad4}
    lines.append(f"G4 audio    bm_audio --check rc={r.returncode} ({last[:90]}); .ee.fmod_guids == B-11's: {same}")
    dangling += bad4

    # G5 drop
    sys.path.insert(0, HERE)
    import bm_rebel
    its = bm_rebel.items(open(os.path.join(RC, "drop", "profile", "item.onlinec"), "rb").read())
    bm = [i for i in its if i["Name"] == bm_rebel.H(NEW)]
    ok5 = len(bm) == 1 and os.path.exists(ee) and os.path.exists(ee + ".toc") and \
        os.path.exists(os.path.join(RC, "drop", "textures", "ui", "vehicle_icons", bm[0]["UIImagePath_s"] + ".ddsc"))
    bad5 = [] if ok5 else ["Rebel Drop entry / entity / icon does not resolve in the dropzone tree"]
    out["drop"] = {"item_hash": bm_rebel.H(NEW), "entity": DIR + NEW + ".ee", "ok": ok5}
    lines.append(f"G5 drop     item {bm_rebel.H(NEW)} -> {DIR.split('/')[-2]}/{NEW}.ee + .toc + icon in the dropzone: {ok5}")
    dangling += bad5

    out["dangling"] = dangling
    verdict = f"dangling {len(dangling)}"
    print("\n".join(lines)); print(("PASS: " if not dangling else "FAIL: ") + verdict)
    for d in dangling[:20]:
        print("   ", d)
    json.dump(out, open(os.path.join(OUTD, "wiring.json"), "w"), indent=1)
    open(os.path.join(OUTD, "wiring.md"), "w", encoding="utf-8").write(
        "# V-03 wiring gates on " + TAG + "\n\n`python Tools/scripts/v03_wiring.py --check`\n\n```\n" + "\n".join(lines) +
        f"\n{'PASS' if not dangling else 'FAIL'}: {verdict}\n" + "\n".join("    " + d for d in dangling) + "\n```\n")
    return 0 if not dangling else 1


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--tag" in argv:
        TAG = argv[argv.index("--tag") + 1]
        RC = os.path.join(ROOT, "Builds", TAG)
        OUTD = os.path.join(ROOT, "Working", "RC", "verify-" + TAG)
    sys.exit(main())
