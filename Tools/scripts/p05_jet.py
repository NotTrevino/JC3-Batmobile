"""Check P-05's card (Working/Translation/P05_JET.md) against its decoded sources.

    python Tools/scripts/p05_jet.py --check

Re-derives every figure the card states from:

  Working/Translation/T8_PARTS.json            P-05 row, bones, joint, behaviour, variable, faces
  Working/Parts/bm_vehicle_parts.json          part 60, parent, behaviour hash
  Research/BatmobileGrab/BONES.json            JetSMove index/parent, jet chain length
  Research/BatmobileGrab/ANIMATIONS.json       JetSMove translation, max jet rotation, AnimTrees
  Research/BatmobileGrab/BMSDK_OFFSETS.json    SVehicle.EngineRPM / RVehicleSimCar.EngineRPMCurve
  tmp/freebuff/scratch/p05_upk.json            Playable_Batmobile* jet names/exports (probe cache)
  tmp/freebuff/scratch/p05_bmgame.json         BmGame.upk jet names/export (probe cache)
  Working/Translation/T8_PARTS.md:50           the row itself
  GRAB_BACKLOG.md:219                          the ANI-4 donor row
  Working/Translation/PARTS_ANIM_COVERAGE.md:44  the unverified "driven by engine_rpm" claim

Exit 0 = every derived figure appears in the card; 1 = drift (FAIL lines printed).
No package, build or research file is written.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOC = os.path.join(ROOT, "Working", "Translation", "P05_JET.md")
CACHE = os.path.join(ROOT, "tmp", "freebuff", "scratch")
Bm = os.path.join(ROOT, "Research", "BatmobileGrab")


def load(rel: str):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def line(rel: str, n: int) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        for i, text in enumerate(fh, 1):
            if i == n:
                return text.rstrip("\n")
    return ""


def derive() -> list[tuple[str, bool, str]]:
    """(label, ok, detail) — ok is the fact itself, as the card must state it."""
    facts: list[tuple[str, bool, str]] = []

    t8 = load("Working/Translation/T8_PARTS.json")
    p05 = next(r for r in t8["rows"] if r.get("id") == "P-05")
    facts += [
        ("P-05 part", p05["part"] == "batmobile_jet", "batmobile_jet"),
        ("P-05 behaviour", p05["behaviour"] == "EngineRotatingPart", p05["behaviour"]),
        ("P-05 variable", p05["variable"] == "engine_rpm", p05["variable"]),
        ("P-05 bones", p05["bones"] == ["JetSMove"], "`JetSMove`"),
        ("P-05 joint", p05["joint"] is None, "`null`"),
        ("P-05 no sequence", p05["animation_sequences"] == [], "animation_sequences: []"),
        ("P-05 faces", p05["faces_lod0"] == 6272, str(p05["faces_lod0"])),
        ("P-05 carrier", p05["carrier_chassis"] == "v0506_car_solar_oldtractor", p05["carrier_chassis"]),
        ("P-05 translation", p05["translation"]["JetSMove"]["max_cm"] == 40.163, "40.1633 cm"),
    ]

    t8md = line("Working/Translation/T8_PARTS.md", 50)
    facts.append(("T8 row line 50", "| P-05 | `batmobile_jet` | EngineRotatingPart |" in t8md,
                  "T8_PARTS.md:50"))
    ani4 = line("GRAB_BACKLOG.md", 219)
    facts.append(("ANI-4 donor line", "ANI-4" in ani4 and "EngineRotatingPart" in ani4 and "engine_rpm" in ani4,
                  "GRAB_BACKLOG.md:219")) 
    cov = line("Working/Translation/PARTS_ANIM_COVERAGE.md", 44)
    facts.append(("coverage claim line", "the spin itself is driven by `engine_rpm`" in cov,
                  "PARTS_ANIM_COVERAGE.md:44"))

    parts = load("Working/Parts/bm_vehicle_parts.json")
    jet = next(p for p in parts["parts"] if p.get("name") == "batmobile_jet")
    facts += [
        ("build part index", jet["part_index"] == 60, "part_index 60"),
        ("build parent", jet["parent"] == "sportsmuscle_body", jet["parent"]),
        ("build behaviour", jet["behaviour"] == "EngineRotatingPart", jet["behaviour"]),
        ("build hash", jet["behaviour_hash"] == 1813315288, "1813315288"),
    ]

    bones = load("Research/BatmobileGrab/BONES.json")["bones"]
    jet_bones = [b for b in bones if "jet" in b["name"].lower()]
    jsm = next(i for i, b in enumerate(bones) if b["name"] == "JetSMove")
    facts += [
        ("JetSMove index", jsm == 40, "#40"),
        ("JetSMove parent", bones[jsm]["parent"] == "Batmobile_Chassis_Mesh", bones[jsm]["parent"]),
        ("jet chain length", len(jet_bones) == 22, "22 bones"),
        ("nozzle count", sum(1 for b in jet_bones if "Nozzle_" in b["name"]) == 18, "18 nozzle bones"),
    ]

    anim = load("Research/BatmobileGrab/ANIMATIONS.json")
    seqs = anim["sequences"]
    jsm_moves = []
    max_rot = 0.0
    max_rot_bone = ""
    max_rot_seq = ""
    for s in seqs:
        for b in s.get("moved_bones") or []:
            if "jet" not in b.get("bone", "").lower():
                continue
            if b.get("bone") == "JetSMove":
                jsm_moves.append((s["name"], s["package"], s.get("export_index"), b.get("dpos_cm"), b.get("drot_deg")))
            if abs(b.get("drot_deg", 0.0)) > max_rot:
                max_rot = abs(b["drot_deg"])
                max_rot_bone = b["bone"]
                max_rot_seq = s["name"]
    tracker = next(m for m in jsm_moves if m[0] == "Batmobile_V2_Bat_Tracker")
    facts += [
        ("JetSMove translation", abs(tracker[3] - 40.1633) < 1e-9, "40.1633 cm"),
        ("JetSMove never rotates", all(m[4] == 0.0 for m in jsm_moves), "0.0"),
        ("max jet rotation", abs(max_rot - 20.014) < 1e-9, "20.014"),
        ("max rotation bone", max_rot_bone == "Batmobile_Rig_Jet_Nozzle_003", max_rot_bone),
        ("max rotation sequence", max_rot_seq == "Batmobile_V2_Back_Door_Close", max_rot_seq),
        ("AnimTrees carry no jet control", all("jet" not in json.dumps(t).lower() for t in anim["trees"]),
         "3 AnimTrees"),
    ]

    offs = load("Research/BatmobileGrab/BMSDK_OFFSETS.json")["classes"]
    sv = {p["name"]: p for p in offs["SVehicle"]["properties"]}
    rv = {p["name"]: p for p in offs["RVehicleSimCar"]["properties"]}
    jet_members = [f"{c}.{p['name']}" for c, v in offs.items() for p in v["properties"] if "jet" in p["name"].lower()]
    facts += [
        ("SVehicle.EngineRPM", sv["EngineRPM"]["offset"] == 1840, "1840"),
        ("RVehicleSimCar.EngineRPMCurve", rv["EngineRPMCurve"]["offset"] == 280, "280"),
        ("no jet member", jet_members == [], "member contains"),
    ]

    upk = json.load(open(os.path.join(CACHE, "p05_upk.json"), encoding="utf-8"))
    sf = upk["packages"]["Playable_Batmobile_SF.upk"]
    names = {n["name"]: n["index"] for n in sf["names"]}
    facts += [
        ("SF jet names", len(sf["names"]) == 28, "28 jet names"),
        ("SF jet exports", sf["exports"] == [], "0 jet exports"),
        ("SF JetSMove name", names.get("JetSMove") == 1608, "1608"),
        ("SF jet mesh name", names.get("MESH_Batmobile_Jet_V01") == 1857, "name index 1857"),
        ("all packages 0 jet exports",
         all(v["exports"] == [] for k, v in upk["packages"].items() if not k.endswith("_Std_SF.upk")),
         "0 jet exports"),
    ]

    bmg = json.load(open(os.path.join(CACHE, "p05_bmgame.json"), encoding="utf-8"))
    bnames = {n["name"]: n["index"] for n in bmg["names"]}
    mesh = next(e for e in bmg["exports"] if e["name"] == "MESH_Batmobile_Jet_V01")
    facts += [
        ("BmGame JetSMove name", bnames.get("JetSMove") == 46114, "46114"),
        ("BmGame jet mesh name", bnames.get("MESH_Batmobile_Jet_V01") == 50803, "50803"),
        ("BmGame jet mesh export", mesh["index"] == 176021 and mesh["class"] == "StaticMesh",
         "176021"),
    ]
    return facts


def check() -> int:
    with open(DOC, encoding="utf-8") as fh:
        doc = fh.read()
    facts = derive()
    failed = 0
    for label, ok, detail in facts:
        if not ok:
            print(f"FAIL  {label}: source value is {detail!r}")
            failed += 1
            continue
        # every derived figure must appear as text in the card
        token = str(detail)
        if token and token not in doc:
            print(f"FAIL  {label}: {token!r} missing from P05_JET.md")
            failed += 1
        else:
            print(f"PASS  {label}: {detail}")
    for lab in ("DECODED", "DERIVED", "UNKNOWN"):
        if lab not in doc:
            print(f"FAIL  label {lab} missing from P05_JET.md")
            failed += 1
    print(f"\n{len(facts)} source facts, {failed} failure(s)")
    return 1 if failed else 0


def main() -> int:
    if "--check" in sys.argv:
        return check()
    for label, ok, detail in derive():
        print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")
    print("\nrun with --check to verify Working/Translation/P05_JET.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
