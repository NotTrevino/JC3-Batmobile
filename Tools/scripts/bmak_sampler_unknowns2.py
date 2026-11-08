"""bmak_sampler_unknowns2.py - the three partly-answered SAMPLER_UNKNOWNS rows, re-routed (7207).

`Research/BatmobileGrab/SAMPLER_UNKNOWNS.md` marks three rows PARTLY/UNKNOWN and names the input
each one lacks.  This card takes those three (U2, U3, U7) and tries a *different* file route for
each missing input:

  U2  "the UFunction body that writes RVehicleBatmobileBase+5901 (BoostingOut)"
      route: the BmAK bytecode walks in `CONTROLS_CONSUMERS.json` (produced from BmGame.upk),
             function `DrivingMode.EjectFromVehicle`.
  U3  "the QuickGadgetX body and a meter field read in the same frame as the 783 edge"
      route: the decoded `DrivingMode.QuickGadgetX` body and the `SelectVehicleWeapon` call chain,
             plus a re-read of the runtime records for a generator/meter key.
  U7  "a device trace, a keyboard binding that writes `Button bCancelButton`, or the OnRelease
      half of the B binding"
      route: every decoded reference to `RPlayerInput.bCancelButton` (function + byte offset) and
             a re-read of all 374 bind lines for a writer.

Labels: decoded (file + offset/line), derived (stated rule + inputs), UNKNOWN (what was tried,
where the answer would be).  The script reads only; the game is never run.

Usage
    python Tools/scripts/bmak_sampler_unknowns2.py --write
    python Tools/scripts/bmak_sampler_unknowns2.py --check   # rebuilds and compares byte-for-byte
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Research" / "BatmobileGrab"
RUNTIME = RES / "runtime"
MD = RES / "SAMPLER_UNKNOWNS2.md"

BMSDK = Path("E:/Modding/_tools/BmSDK-AK/src/BmSDK")
GEN = BMSDK / "Generated" / "BmGame"
PROP_RE = re.compile(r"///\s*(\w+)Property:\s*(\w+)")
PTR_RE = re.compile(r"Ptr \+ (\d+)")
BIND_RE = re.compile(r'Name="([^"]+)",\s*Command="([^"]*)"')


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def props(path: Path) -> dict[str, dict]:
    """`name -> {type, offset, comment_line, getter_line}` from a generated .g.cs."""
    out: dict[str, dict] = {}
    cur = None
    for i, line in enumerate(read(path).splitlines(), 1):
        m = PROP_RE.search(line)
        if m:
            cur = {"type": m.group(1), "comment_line": i}
            name = m.group(2)
            continue
        if cur is None:
            continue
        p = PTR_RE.search(line)
        if not p:
            continue
        cur.update(offset=int(p.group(1)), getter_line=i)
        out[name] = cur
        cur = None
    return out


def ts(t: str) -> float:
    hh, mm, ss = t[11:23].split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


def transitions(vals: list[tuple[str, int]]) -> dict:
    pairs, prev = [], None
    for t, v in vals:
        if prev is not None and prev == 0 and v > 0:
            pairs.append((t, None))
        elif prev is not None and prev > 0 and v == 0 and pairs and pairs[-1][1] is None:
            pairs[-1] = (pairs[-1][0], t)
        prev = v
    holds = [ts(e) - ts(s) for s, e in pairs if e]
    return {"rises": len(pairs), "first": pairs[0][0] if pairs else None,
            "max_hold": max(holds) if holds else 0.0, "pairs": pairs}


def analyse() -> dict:
    a: dict = {}
    cc = json.loads(read(RES / "CONTROLS_CONSUMERS.json"))
    a["cc"] = cc

    # --- U2: the eject body's references to BoostingOut
    veh = props(GEN / "RVehicleBatmobileBase.g.cs")
    a["boosting_out"] = veh.get("BoostingOut")
    w = cc["walks"]["DrivingMode.EjectFromVehicle"]
    a["eject"] = {
        "export": w["export"], "script_bytes": w["script_bytes"],
        "sites": [{"at": r["at"], "token": r["token"]}
                  for r in w["refs"] if r.get("ref") == "RVehicleBatmobileBase.BoostingOut"],
        "calls": [r.get("call") for r in w["refs"] if "call" in r],
    }

    # --- U3: the X handler body and the gate chain
    q = cc["walks"]["DrivingMode.QuickGadgetX"]
    a["qgx"] = {"export": q["export"], "script_bytes": q["script_bytes"],
                "refs": q["refs"], "constants": q["constants"]}
    sw = cc["walks"]["DrivingMode.SelectVehicleWeapon"]
    a["sel"] = {
        "export": sw["export"], "script_bytes": sw["script_bytes"],
        "calls": [{"at": r["at"], "call": r.get("call") or r.get("ref", "").split(".")[-1]}
                  for r in sw["refs"]
                  if r.get("token") in ("EX_FinalFunction", "EX_VirtualFunction")],
    }
    pin = props(GEN / "RPlayerInput.g.cs")
    a["b783"] = pin.get("bHandbrakeOrBrake")
    a["b774"] = pin.get("bCancelButton")
    a["pc_func"] = {}
    for i, line in enumerate(read(GEN / "RPlayerController.g.cs").splitlines(), 1):
        m = re.search(r"///\s*Function:\s*(QuickGadgetX)\b", line)
        if m and m.group(1) not in a["pc_func"]:
            a["pc_func"][m.group(1)] = i

    # --- U7: every decoded reference to bCancelButton and every bind writer
    pc = cc["property_consumers"]["RPlayerInput.bCancelButton"]
    per: dict[str, int] = {}
    for r in pc:
        per[r["function"]] = per.get(r["function"], 0) + 1
    a["cancel"] = {"refs": len(pc), "per_function": per,
                   "tokens": sorted({r["token"] for r in pc}),
                   "offsets": sorted({r["at"] for r in pc})}
    writers = [ln for ln, txt in cc["bindings"]["ini"].items()
               if "Button bCancelButton" in txt]
    a["cancel_writers"] = sorted(writers, key=int)
    a["bind_total"] = len(cc["bindings"]["ini"])
    a["bind_device"] = {ln: (BIND_RE.search(cc["bindings"]["ini"][ln]).group(1)
                             if BIND_RE.search(cc["bindings"]["ini"][ln]) else "?")
                        for ln in writers}

    # --- logs: the 774 taps, the 783 edges, and whether a meter key was ever sampled
    timeline: dict[str, list[tuple[str, int]]] = {}
    files = sorted(RUNTIME.glob("samples2-*.jsonl"))
    records = 0
    for f in files:
        for raw in read(f).splitlines():
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            records += 1
            for k, v in rec["changed"].items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    timeline.setdefault(k, []).append((rec["t"], int(v)))
    a["logs"] = {"files": [f.name for f in files], "records": records}
    a["tap774"] = transitions(timeline.get("in0.b774", []))
    a["edge783"] = transitions(timeline.get("in0.b783", []))
    a["meter_keys"] = sorted(k for k in timeline
                             if re.search(r"generatorpower|unavailable|weaponpower", k, re.I))
    a["weaponword"] = sorted(k for k in timeline if re.search(r"missilelauncher\d\.weaponword$", k, re.I))
    return a


def build(a: dict) -> str:
    L: list[str] = []
    w = L.append
    bo, ej = a["boosting_out"], a["eject"]
    q, sel = a["qgx"], a["sel"]
    ca = a["cancel"]
    taps, edges = a["tap774"], a["edge783"]
    w("# SAMPLER_UNKNOWNS2 - the three partly-answered rows, re-routed through other files (7207)")
    w("")
    w("Generated by `Tools/scripts/bmak_sampler_unknowns2.py --write`; `--check` rebuilds this")
    w("document from the same bytes and requires it to be identical. Read-only inputs: the BmAK")
    w("bytecode walks in `CONTROLS_CONSUMERS.json`, the BmSDK-AK layouts, the decoded bind table, and")
    w("the two `samples2-*.jsonl` runtime records. Nothing was run, attached to, or read from a live")
    w("game; nothing under a game install was written. `SAMPLER_UNKNOWNS.md` is left untouched.")
    w("")
    w("## STATUS")
    w("")
    w("| U | missing input (SAMPLER_UNKNOWNS.md) | different route tried | result |")
    w("|---|---|---|---|")
    w(f"| U2 | the UFunction body that writes `BoostingOut` +{bo['offset'] if bo else 5901} | "
      f"the BmAK bytecode walk of `DrivingMode.EjectFromVehicle` (export {ej['export']}, "
      f"{ej['script_bytes']} script bytes) | **still-missing** for the write; 3 reference sites "
      f"found at {', '.join(str(s['at']) for s in ej['sites'])} - a reference is not a write |")
    w(f"| U3 | the `QuickGadgetX` body and a meter field in the same frame as the 783 edge | "
      f"the decoded `QuickGadgetX` body (export {q['export']}, {q['script_bytes']} script bytes) and "
      f"the `SelectVehicleWeapon` call chain | **found-with-bytes** for the press path (no meter "
      f"branch in the X handler); **still-missing** for the meter value |")
    w(f"| U7 | a device trace, a keyboard writer of `Button bCancelButton`, or the B OnRelease | "
      f"all {ca['refs']} decoded refs to `bCancelButton` + all {a['bind_total']} bind lines | "
      f"**still-missing** for the producer; all {ca['refs']} refs are in "
      f"{len(ca['per_function'])} functions and none is a bind writer |")
    w("")

    # U2
    w("## U2 - the writer of `BoostingOut` (+%d)" % (bo["offset"] if bo else 5901))
    w("")
    if bo:
        w(f"`RVehicleBatmobileBase.BoostingOut` is a `{bo['type']}Property` at +{bo['offset']} "
          f"(`RVehicleBatmobileBase.g.cs:{bo['comment_line']}`, getter `{bo['getter_line']}`) - "
          f"unchanged from the first card.")
    w("")
    w(f"The new route is the decoded body of `DrivingMode.EjectFromVehicle` (export {ej['export']}, "
      f"{ej['script_bytes']} script bytes). Its aligned bytecode walk contains "
      f"**{len(ej['sites'])} tokens naming `BoostingOut`** at script offsets "
      f"{', '.join(str(s['at']) for s in ej['sites'])}, in "
      f"{len(ej['sites']) // 2} `EX_LocalVariable`+`EX_InstanceVariable` pairs:")
    w("")
    w("| script offset | token |")
    w("|---:|---|")
    for s in ej["sites"]:
        w(f"| {s['at']} | `{s['token']}` |")
    w("")
    w("The body also calls, in byte order: " + ", ".join(
        f"`{c}`" for c in ej["calls"] if c) + ".")
    w("")
    w("**Why this is still not the writer.** Every reference is the same `Local`+`Instance` pair;")
    w("the walk records no `EX_Let`/`EX_LetBool` token at any of the three sites (the walk is a")
    w("left-to-right reference scan, not a control-flow decoder - the same limitation that makes")
    w("`GiveMaxEnergy`'s decoded assignment show as three bare `EX_InstanceVariable` tokens).")
    w("A reference in the eject body therefore proves the eject path *touches* the field, but it")
    w("does not prove the direction. The writer stays UNKNOWN.")
    w("")
    w("**Where it would be found:** the same export's expression tree, decoded with a Let-aware")
    w("walker (`EX_Let` 0x0F / `EX_LetBool` 0x14 in the repo's token table) - i.e. the next step is")
    w("a decoder upgrade, not another file.")

    # U3
    w("")
    w("## U3 - X on 783 with the barrage meter empty")
    w("")
    w(f"The `QuickGadgetX` handler is export {q['export']}, **{q['script_bytes']} script bytes**. Its")
    w("whole decoded body is one virtual call:")
    w("")
    for r in q["refs"]:
        w(f"- at script offset {r['at']}: `{r['token']}` `{r.get('call')}` "
          f"(operand: {r.get('operand')})")
    w("")
    consts = ", ".join(str(c.get("value")) for c in (q.get("constants") or [])) or "none"
    w(f"Body constants: {consts}. There is **no branch, no field read and no generator term in the")
    w("handler**: the X binding's registration on 783 is unconditional (`bHandbrakeOrBrake` is")
    w(f"written by the bind, +{a['b783']['offset'] if a['b783'] else 783}), and the handler only")
    w("selects weapon slot 2. This is the byte-level answer to the first half of the row.")
    w("")
    w(f"The gate chain that follows, decoded from `SelectVehicleWeapon` (export {sel['export']}, "
      f"{sel['script_bytes']} script bytes):")
    w("")
    w("| script offset | call |")
    w("|---:|---|")
    for c in sel["calls"]:
        w(f"| {c['at']} | `{c['call']}` |")
    w("")
    w("`ReadyToFire` is a virtual call at two sites and `TryToFireWeapon` at two; the salvo")
    w("gate therefore lives in a `ReadyToFire` state body (name-match candidates `Holstered`, ")
    w("`InfiniteMissiles`, `Primed`), not in the handler and not in `SelectVehicleWeapon`.")
    w("")
    w(f"**Meter value.** The records carry no generator key: meter-like keys present = "
      f"{a['meter_keys'] or 'none'}; the only launcher keys are {a['weaponword'] or 'none'}. "
      f"`WeaponGeneratorPower` and `WeaponUnavailableReason` exist in the layout but were never")
    w("sampled, so the charge at each 783 edge stays UNKNOWN. The 783 edges themselves are")
    w(f"decoded from the same records: {edges['rises']} rise(s), longest hold "
      f"{edges['max_hold']:.3f} s, first `{edges['first']}`.")
    w("")
    w("**Still-missing:** one sampled `WeaponGeneratorPower` (or a decoded `ReadyToFire` state body)")
    w("in the same frame as the 783 edge.")

    # U7
    w("")
    w("## U7 - what produces the ~0.1 s 774 taps")
    w("")
    w(f"774 is `bCancelButton` (`RPlayerInput.g.cs:"
      f"{a['b774']['comment_line'] if a['b774'] else '?'}`). The new route is every decoded")
    w(f"reference to that property: **{ca['refs']} refs in {len(ca['per_function'])} functions**, "
      f"tokens {', '.join('`'+t+'`' for t in ca['tokens'])}:")
    w("")
    w("| function | refs |")
    w("|---|---:|")
    for fn, n in sorted(ca["per_function"].items()):
        w(f"| `{fn}` | {n} |")
    w("")
    w(f"All {a['bind_total']} ini lines in the decoded consumer table were re-read for a writer: "
      f"**{len(a['cancel_writers'])} line(s)** contain `Button bCancelButton` "
      f"(line {', '.join(a['cancel_writers'])} on "
      f"{', '.join(a['bind_device'][k] for k in a['cancel_writers'])}). No keyboard line, no other")
    w("button and no named binding writes the byte anywhere in the decoded table - the three")
    w("functions above read it (menu wheel tick, button-name mapping, special-move override).")
    w("")
    w(f"The taps are real and unchanged: {taps['rises']} rise(s), longest hold "
      f"{taps['max_hold']:.3f} s, first `{taps['first']}`. Their producer is still UNKNOWN: a")
    w("read reference cannot explain a write, and the only decoded writer is the physical B line.")
    w("")
    w("**Where it would be found:** a device-level trace at the same timestamps, or a Let-aware")
    w("decode of `RGadgetSelectBM3.Tick` (the menu wheel may synthesise the byte), or the native")
    w("input path in `BatmanAK.exe` - none of which exists in the files read here.")
    w("")
    w("## Oracles")
    w("")
    o = oracles(a)
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k in sorted(o):
        w(f"| `{k}` | {o[k][0]} | {o[k][1]} |")
    w("")
    w("## Sources read")
    w("")
    w("| source | what it gave |")
    w("|---|---|")
    w("| `Research/BatmobileGrab/CONTROLS_CONSUMERS.json` | the decoded walks (export, script bytes, refs, calls) and `property_consumers` |")
    w("| `Research/BatmobileGrab/SAMPLER_UNKNOWNS.md` | the three missing-input statements |")
    w("| `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/BmGame/RVehicleBatmobileBase.g.cs` | `BoostingOut` offset/type |")
    w("| `.../Generated/BmGame/RPlayerInput.g.cs` | 783 and 774 field names |")
    w("| `.../Generated/BmGame/RPlayerController.g.cs` | `QuickGadgetX` function line |")
    w(f"| `Research/BatmobileGrab/runtime/{', '.join(a['logs']['files'])}` | {a['logs']['records']} records: 774 taps, 783 edges, meter-key census |")
    w("")
    return "\n".join(L) + "\n"


def oracles(a: dict) -> dict:
    o = {}
    bo = a["boosting_out"]
    ej = a["eject"]
    o["boostingout_offset"] = (bool(bo) and bo["offset"] == 5901,
                               f"offset {bo['offset'] if bo else None}")
    o["eject_ref_sites"] = (len(ej["sites"]) == 6 and
                            [s["at"] for s in ej["sites"]] == [332, 338, 388, 394, 457, 463],
                            f"{len(ej['sites'])} refs at {[s['at'] for s in ej['sites']]}")
    o["quickgadgetx_body"] = (a["qgx"]["script_bytes"] == 10 and
                              len(a["qgx"]["refs"]) == 1 and
                              a["qgx"]["refs"][0].get("call") == "SelectVehicleWeapon",
                              f"{a['qgx']['script_bytes']} script bytes, "
                              f"{len(a['qgx']['refs'])} call(s)")
    calls = [c["call"] for c in a["sel"]["calls"]]
    o["ready_before_fire"] = (calls.count("ReadyToFire") == 2 and
                              calls.count("TryToFireWeapon") == 2,
                              f"ReadyToFire {calls.count('ReadyToFire')}x, "
                              f"TryToFireWeapon {calls.count('TryToFireWeapon')}x")
    o["cancel_refs"] = (a["cancel"]["refs"] == 14 and
                        len(a["cancel"]["per_function"]) == 3,
                        f"{a['cancel']['refs']} refs in {len(a['cancel']['per_function'])} functions")
    o["cancel_bind_writer"] = (a["cancel_writers"] == ["268"] and
                               a["bind_device"].get("268") == "XboxTypeS_B",
                               f"writers {a['cancel_writers']} on "
                               f"{a['bind_device'].get('268')}")
    o["no_meter_key"] = (not a["meter_keys"], f"meter-like keys {a['meter_keys']}")
    o["tap_count"] = (a["tap774"]["rises"] == 5, f"{a['tap774']['rises']} rises of 774")
    return o


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        print(__doc__)
        return 2
    a = analyse()
    doc = build(a)
    o = oracles(a)
    ok = all(v[0] for v in o.values())
    if argv[1] == "--write":
        MD.write_text(doc, encoding="utf-8", newline="\n")
        print(f"wrote {MD.relative_to(ROOT)} ({len(doc.splitlines())} lines)")
    else:
        cur = read(MD)
        if cur != doc:
            print("MISMATCH: regenerated document differs from the file on disk")
            return 1
        print(f"OK {MD.relative_to(ROOT)} byte-identical to a fresh rebuild")
    print("oracles: " + json.dumps({k: v[0] for k, v in sorted(o.items())}, sort_keys=True))
    for k in sorted(o):
        print(f"  {k}: {'OK' if o[k][0] else 'FAIL'} - {o[k][1]}")
    if not ok:
        print("ORACLE FAILURE")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv))
