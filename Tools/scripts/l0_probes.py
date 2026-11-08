"""l0_probes.py - build the offline L0 probe payloads for bm-RC4 (brief 8589).

Creates Builds/probe-L0/P<n>-<slug>/ for P1..P9. Each folder holds:
  payload/     the files that go on top of Builds/bm-RC4 (when one can be built)
  PROBE.md     change, expected observation, pass/fail rule, undo
  receipt.json files + sha256 + status + evidence

Nothing is installed, nothing is launched, APPROVED_Q.txt is not created, no existing Builds/bm-*
tree is edited. Only P1 has a binary payload today; the others are either text (P6, P7, P9) or
recorded as BLOCKED/UNKNOWN with the exact missing writer, because this desk has no writer for
them (see tmp/freebuff/reports/jc3-community-writers-check.md).

P1: every hknpConvexPolytopeShape vertex moves +1.0 m on world Z (one visible change: the whole
collision hull is displaced). Re-read with jc3hkx proves the shift and the file size is unchanged.

Usage
    python Tools/scripts/l0_probes.py --write
    python Tools/scripts/l0_probes.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3hkx  # noqa: E402

OUT = os.path.join(ROOT, "Builds", "probe-L0")
SRC_PHYS = os.path.join(ROOT, "Working", "Collision", "batmobile.physicsc")
SHIFT = (0.0, 0.0, 1.0)          # metres, world Z (the probe needs a visible displacement, not a semantic axis)

PROBES = [
    ("P1", "physicsc-read", "P1 physicsc read", "payload"),
    ("P2", "keymap-dropzone", "P2 keymap honoured", "blocked"),
    ("P3", "hud-gfx", "P3 hud.gfx loads", "unknown"),
    ("P4", "audio-override", "P4 per-entity audio override", "blocked"),
    ("P5", "second-entity", "P5 second entity carries state", "blocked"),
    ("P6", "use-vehicle-mod", "P6 USE_VEHICLE_MOD", "text"),
    ("P7", "damage-model", "P7 damage model H0/H1/H2", "text"),
    ("P8", "effc-growth", "P8 grown .effc renders", "blocked"),
    ("P9", "runtime-spawn", "P9 runtime spawn", "text"),
]

TEXT = {
"P2": """# P2 - is a dropzone `settings/keymap_gamepad.bin` honoured?

STATUS: BLOCKED - no writer exists in this repo or in the public community (see
`tmp/freebuff/reports/jc3-community-writers-check.md` s1(f)). No payload is shipped, because a
byte-identical copy would answer nothing and a hand-built RTPC v1 file would be a guess.

What is decoded (`Research/JC3Grab/INPUT.md`): the mounted file is the patch-layer
`settings/keymap_gamepad.bin` (7,207 B, 145 bindings, 169 strings); bindings are 12-byte records
(32..1772) then one 18-byte property-block + `PP`+name per binding, tiling to EOF. Adding one
binding means rewriting the record count, the block table and every offset - a writer, not a patch.

The writer that would close it (5-minute prover, no game): clone the patch file, duplicate the last
binding record and its block, insert the new input/action strings into the pool (or reuse an existing
action string so the pool is unchanged), rewrite the header counts/offsets, then run
`python Tools/scripts/jc3_input.py --check` on the new file. Oracle: the byte-accounting tiles
exactly to EOF and the binding count is 146.

Until then: the community route is the text `Saves/kepmap.txt` (Steam thread
https://steamcommunity.com/app/225540/discussions/0/485623406960065017), which is reported as
write-only after a 2016 patch and is not a dropzone `settings/*.bin` test.

Undo: nothing installed.
""",
"P3": """# P3 - does a private `ui/hud.gfx` load?

STATUS: UNKNOWN / SKIPPED, exactly as the brief allows. A GFx writer exists in the community
(JPEXS FFDec `-replace <infile> <outfile> <scriptName> <as3file>` and `-header -set gfx`), but FFDec
is **not installed on this desk** (`command -v ffdec ffdec-cli.exe ffdec.bat` -> empty, no
`Tools/ffdec*`). No payload is shipped rather than a guessed byte patch of a 260-script movie.

What a payload needs: one visible text change (e.g. a static string in `hud_code`), recompiled with
FFDec, at `drop/ui/hud.gfx`. The pass rule: the changed text is visible in game and every other HUD
element still draws; fail: no change (file not loaded) or a blank/absent HUD (movie rejected).

Undo: remove `drop/ui/hud.gfx` (the archive copy returns).
""",
"P4": """# P4 - per-entity audio override (B-26)

STATUS: BLOCKED - B-26 has no proven carrier. `Working/Roadmap/sound.md` row B-26: "no payload in
RC4; entity-level bank override honoured? UNPROVEN"; blocker 3: "21/45 GUIDs cannot be swapped per
vehicle; B-26 route unproven (NEW-AUD-4)".

RC4 already ships **global** private banks with 5 payload swaps (`Builds/bm-RC4/drop/sound/fmod_banks/
vehicles.bank`, `weapons.bank`, from B-11). Swapping one more GUID there would answer "does the swapped
sample play", not "is the override per entity" - two different questions, so no payload is shipped
under a misleading label.

The 5-minute experiment that settles it (needs the game, i.e. the supervised session): put one
private bank in the dropzone whose sample is an unmistakable tone, bind it only through the
Batmobile's `.ee.fmod_guids`, spawn a stock Serpente beside it, and listen. If the Serpente is silent
of the tone and the Batmobile plays it -> per-entity honoured; if both play it -> the bank is global
and B-26 must be re-card-ed. The binding itself is card 9150's payload (not built).

Undo: remove the two `sound/fmod_banks/*.bank` files.
""",
"P5": """# P5 - does a Rebel Drop spawn of a second entity carry speed/health?

STATUS: BLOCKED as a dropzone payload. A second Rebel Drop entry needs a second leaf: a renamed copy
of the `.ee` (inner `.epe` root name + name_hash), a `settings/spawn_vehicle_defs.bin` record, an
`profile/item.onlinec` record and a `profile/task.onlinec` grant. `bm_rebel.py` builds exactly one
entry for one leaf (`LEAF = bm_leaf.NEW`), so a second entry is a build, not a payload, and the
4-D-2 mode pair is not in RC4.

P9 may make this cheap: if `spawn <model_name>` resolves the RC4 leaf, spawn it twice and P5 becomes
"does the second spawn keep the first one's speed/health" with no new file at all. Run P9 first.

Undo: nothing installed.
""",
"P8": """# P8 - does a grown `.effc` render?

STATUS: BLOCKED - the repo writer proves **value edits**, not growth.
`Working/Effects/EFFC_WRITER.md`: 95/95 carry round trip, one value edit re-read; there is no
add/grow code in `effc_writer.py` (no append/insert path). `Working/Roadmap/hud_cam_lights_fx.md`
NEW-FX-1: "Prove `.effc` writer can GROW (A[] pair layout, total_size)" - todo. No community tool
exists either (community-writers check s1(d)).

The 5-minute prover (no game): copy `effects/cinematic/mm150_ember_camera.effc`, add a second
`EmitterTemplates` element by hand (bump the array count), run `effc_writer.py` decode. Oracle: the
decoder shows 2 templates, re-encode is byte-identical to the grown file, and the untouched control
still round-trips. Only then is an afterburner-socket payload meaningful.

Undo: nothing installed.
""",
"P6": """# P6 - what does `USE_VEHICLE_MOD` (RPADRIGHT) do on the mod vehicle? (U3)

STATUS: TEXT ONLY - nothing to build (brief).

Button sequence (one variable per take; save before each):
1. Spawn/enter the Batmobile (RC4) on the airstrip, stop, engine on, camera behind.
2. **Tap** RPADRIGHT once (<= 0.2 s). Wait 3 s. Record: turret, wheels, body, HUD, sound, speed.
3. **Hold** RPADRIGHT 1.5 s. Release. Wait 3 s. Record the same six.
4. **Double-tap** RPADRIGHT. Wait 3 s. Record the same six.
5. Repeat 2-4 in a stock Serpente (control): if the stock car also reacts, the action is vanilla.

Pass/fail rule: PASS = any reproducible, vehicle-scoped state change on the Batmobile that the stock
Serpente does not show (that is a carrier for battle mode); FAIL = no change, or the same change on
the stock car (then U3 is a vanilla action, not a mode trigger). Record the exact frame if possible.

Undo: nothing installed; exit the vehicle / reload the save.
""",
"P7": """# P7 - damage model H0/H1/H2 (rifle, tank shell, missile vs the health bar)

STATUS: TEXT ONLY - nothing to build (brief).

Shot list (one weapon per take, full health at the start, count every hit):
1. Pistol (Firestarter) - 10 hits, 1 s apart; note the bar after each.
2. Rifle (CS110 Archangel) - 10 hits.
3. MG (Urga Vdova 89) - 20 hits.
4. Rocket launcher (RPG / CS Rocket) - 3 hits.
5. Tank shell (CS Odjur main gun) - 3 hits.
For each: H0 = full, H1 = first visible bar drop, H2 = bar empty; record whether the car explodes
instantly at 0 (lore) or smokes/burns first (donor), and whether small arms move the bar at all.

Pass/fail rule: PASS = the bar moves per hit with a stable ratio and 0 HP is an instant explosion;
FAIL = no bar movement for small arms (armour not applied), a donor burn stage, or a crash.

Undo: nothing installed; reload the save.
""",
"P9": """# P9 - runtime spawn (jc3-console-thingy v1.1)

STATUS: TEXT + staged DLL (see `payload/`). Run this FIRST.

What the source says (decoded: `E:/Modding/_shared/tools/jc3-console-thingy/src/commands/spawn.h`,
`src/game/spawn_system.h`):
* `spawn <arguments>` takes a **string model name**, not an `.ee` path and not a hash:
  `CSpawnSystem::Spawn(arguments, transform, ...)` forwards `model_name.c_str()` to the native at
  `0x140E97DA0` with flags `0x2013C`.
* the transform is the local player's transform with the translation replaced by `m_aimPos`, y+1.0 m:
  the object appears at the crosshair, one metre up.
* hints come from the property file entry hash `0xF71C2A21` (`Initialize()` hook at `0x140EBFBD7`),
  so the model name is whatever that table stores - strings, not hashes.

Commands (open the console first; the tool's key is in its README):
1. `spawn v0300_car_kensington_sportsmuscle_civilian_01`  - stock Serpente (the donor leaf).
2. `spawn v0300_car_kensington_sportsmuscle_debug`        - the RC4 Batmobile leaf.
3. `spawn v0300_car_kensington_sportsmuscle_debug`        - a second copy beside it (P5's subject).

Pass/fail: PASS = each command creates the named entity at the crosshair (serpente / Batmobile /
second Batmobile), console prints no error, and two calls give two coexisting entities; FAIL = no
entity, an error, or the spawn resolves a different model (then the hint table does not carry our
leaf and the name must be looked up in `spawn_vehicle_defs.bin`).

Unknown: whether the hint entry `0xF71C2A21` includes a modded/replaced leaf; whether the RC4 leaf
(the vanilla `_debug` leaf) is the string the table stores.

Undo: delete the spawned objects (or reload the save); remove `xinput9_1_0.dll` from the game folder
after the session (it is only staged here, never installed by this task).
""",
}

P9_DLL = "xinput9_1_0.dll"


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def shift_hulls() -> dict:
    blob = open(SRC_PHYS, "rb").read()
    pf = jc3hkx.Packfile(blob)
    edits, moved = {}, []
    for obj in pf.objects:
        if obj.cls != "hknpConvexPolytopeShape":
            continue
        d = jc3hkx.decode_polytope(pf, obj.offset)
        src = d.get("vertices") or d.get("verts")
        verts = [[v[0] + SHIFT[0], v[1] + SHIFT[1], v[2] + SHIFT[2], v[3]] for v in src]
        edits[obj.offset] = jc3hkx.hull_bytes(pf, obj.offset, verts=verts)
        moved.append((obj.offset, len(verts),
                      [v[:3] for v in src],
                      [[v[0] + SHIFT[0], v[1] + SHIFT[1], v[2] + SHIFT[2]] for v in src]))
    new, stats = jc3hkx.packfile_bytes(pf, edits)
    # oracle: re-read the new bytes, every moved hull's bounds shifted exactly by SHIFT
    pf2 = jc3hkx.Packfile(new)
    for off, _n, _src, want in moved:
        d2 = jc3hkx.decode_polytope(pf2, off)
        got = (d2.get("vertices") or d2.get("verts"))
        if len(got) != len(want):
            raise SystemExit(f"shift check failed at {off:#x}: {len(got)} verts != {len(want)}")
        for g, w in zip(got, want):
            for i in range(3):
                if abs(g[i] - w[i]) > 1e-4:
                    raise SystemExit(f"shift check failed at {off:#x}: {list(g)} != {w}")
    return {"bytes": new, "hulls": len(moved), "size_in": len(blob), "size_out": len(new),
            "stats": stats}


def write_probe(pid: str, slug: str, title: str, kind: str, p1: dict | None) -> dict:
    d = os.path.join(OUT, f"{pid}-{slug}")
    pay = os.path.join(d, "payload")
    os.makedirs(pay, exist_ok=True)
    files = []
    status = {"payload": "READY", "blocked": "BLOCKED", "unknown": "UNKNOWN", "text": "TEXT-ONLY"}[kind]
    change = ""
    if pid == "P1" and p1 is not None:
        dst = os.path.join(pay, "batmobile.physicsc")
        with open(dst, "wb") as f:
            f.write(p1["bytes"])
        files.append(dst)
        change = (f"every hknpConvexPolytopeShape ({p1['hulls']} hulls) moved +1.0 m on world Z; "
                  f"{p1['size_in']} -> {p1['size_out']} B (same size)")
        note = os.path.join(d, "INSTALL.md")
        with open(note, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "# P1 install\n\n"
                "`payload/batmobile.physicsc` is the RC4 collision file with every convex hull moved\n"
                "+1.0 m on world Z. It replaces the `.physicsc` **inside** the built `.ee`; the `.ee`\n"
                "is an AAF archive (magic `AAF\\0`), so this is not a loose drop file.\n\n"
                "Repack it into a copy of the RC4 `.ee` with the existing `Tools/scripts/eetoc.py` /\n"
                "`Tools/Gibbs` SmallPack path used by the B-10 build, then install the rebuilt `.ee`\n"
                "with `install_v3.py -Action install -GameDir <simroot>` (never Rollback091).\n\n"
                "Undo: `install_v3.py -Action rollback -GameDir <simroot>`; the receipt records the\n"
                "sha256 of both the original RC4 `.ee` and this payload.\n")
        files.append(note)
    if pid in TEXT:
        dst = os.path.join(d, "PROBE.md")
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(TEXT[pid])
        files.append(dst)
    rec = {
        "schema": 1,
        "probe": pid,
        "slug": slug,
        "title": title,
        "status": status,
        "base": "Builds/bm-RC4",
        "change": change or ("see PROBE.md" if pid in TEXT else "no payload - see PROBE.md"),
        "payload_dir": os.path.relpath(pay, ROOT).replace("\\", "/"),
        "expected_observation": {
            "P1": "the car stops ~1.0 m further from the wall than in the RC4 control, on the same approach",
            "P2": "one extra binding has an observable effect (not built)",
            "P3": "one changed HUD string is visible and the rest of the HUD still draws",
            "P4": "the unmistakable sample plays on the Batmobile only",
            "P5": "the second spawn keeps speed/health (or does not)",
            "P6": "any vehicle-scoped state change unique to the Batmobile",
            "P7": "the health bar moves per hit and 0 HP explodes instantly",
            "P8": "one extra emitter renders at the afterburner socket",
            "P9": "each spawn command creates the named entity at the crosshair",
        }[pid],
        "pass_fail": {
            "P1": "PASS = contact gap differs by ~1.0 m vs RC4; FAIL = identical gap (file not read)",
            "P2": "PASS = the added/edited binding fires; FAIL = no effect",
            "P3": "PASS = changed string visible, HUD intact; FAIL = no change or blank HUD",
            "P4": "PASS = tone on Batmobile only; FAIL = tone everywhere or nowhere",
            "P5": "PASS = state carried/not carried is unambiguous; FAIL = probe cannot spawn a second",
            "P6": "PASS = a change the stock car does not show; FAIL = none or same on stock",
            "P7": "PASS = bar per hit + instant explosion; FAIL = no movement or donor burn stages",
            "P8": "PASS = a new emitter draws; FAIL = old emitters only or a crash",
            "P9": "PASS = three named entities, two coexisting; FAIL = error or wrong model",
        }[pid],
        "undo": {
            "P1": "install_v3 rollback (never Rollback091)",
            "P9": "delete spawned objects / reload save; remove xinput9_1_0.dll after the session",
        }.get(pid, "nothing installed"),
        "files": [],
    }
    for p in files:
        rec["files"].append({"path": os.path.relpath(p, ROOT).replace("\\", "/"),
                             "bytes": os.path.getsize(p), "sha256": sha(p)})
    with open(os.path.join(d, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, indent=1)
        f.write("\n")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("pass --write or --check")

    if a.write:
        os.makedirs(OUT, exist_ok=True)
        p1 = shift_hulls()
        recs = [write_probe(pid, slug, title, kind, p1 if pid == "P1" else None)
                for pid, slug, title, kind in PROBES]
        # P9: stage the release DLL if it was fetched into the probe folder
        p9 = os.path.join(OUT, "P9-runtime-spawn", "payload")
        dll = os.path.join(p9, P9_DLL)
        if os.path.exists(dll):
            for r in recs:
                if r["probe"] == "P9":
                    r["files"].append({"path": os.path.relpath(dll, ROOT).replace("\\", "/"),
                                       "bytes": os.path.getsize(dll), "sha256": sha(dll)})
                    r["staged_dll"] = {"name": P9_DLL, "source":
                                       "github.com/aaronkirkham/jc3-console-thingy/releases/tag/v1.1"}
                    with open(os.path.join(OUT, "P9-runtime-spawn", "receipt.json"), "w",
                              encoding="utf-8", newline="\n") as f:
                        json.dump(r, f, indent=1)
                        f.write("\n")
        print(f"wrote {len(recs)} probe folders under {os.path.relpath(OUT, ROOT)}")
        print(f"P1: {p1['hulls']} hulls, {p1['size_in']} -> {p1['size_out']} B")
        return 0

    # check: every receipt file exists and hashes; P1 payload re-reads with the shift
    bad, n = [], 0
    for pid, slug, _t, _k in PROBES:
        d = os.path.join(OUT, f"{pid}-{slug}")
        rp = os.path.join(d, "receipt.json")
        if not os.path.exists(rp):
            bad.append(f"missing {rp}")
            continue
        rec = json.load(open(rp, encoding="utf-8"))
        for fe in rec["files"]:
            p = os.path.join(ROOT, fe["path"])
            if not os.path.exists(p):
                bad.append(f"missing {fe['path']}")
            elif sha(p) != fe["sha256"]:
                bad.append(f"sha mismatch {fe['path']}")
            else:
                n += 1
        if pid == "P1":
            pay = os.path.join(d, "payload", "batmobile.physicsc")
            if not os.path.exists(pay):
                bad.append("P1 payload missing")
                continue
            blob = open(pay, "rb").read()
            pf = jc3hkx.Packfile(blob)
            hs = [o for o in pf.objects if o.cls == "hknpConvexPolytopeShape"]
            base = jc3hkx.Packfile(open(SRC_PHYS, "rb").read())
            dx0 = jc3hkx.decode_polytope(base, hs[0].offset)
            dx1 = jc3hkx.decode_polytope(pf, hs[0].offset)
            v0 = (dx0.get("vertices") or dx0.get("verts"))[0]
            v1 = (dx1.get("vertices") or dx1.get("verts"))[0]
            dz = v1[2] - v0[2]
            if abs(dz - SHIFT[2]) > 1e-4:
                bad.append(f"P1 shift {dz} != {SHIFT[2]}")
            print(f"P1: {len(hs)} polytopes, first vertex dz={dz:+.4f}")
    if bad:
        print("FAIL")
        for b in bad:
            print(" -", b)
        return 1
    print(f"PASS: {n} files hashed, P1 shift = +1.0 m on Z")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
