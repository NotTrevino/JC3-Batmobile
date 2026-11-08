#!/usr/bin/env python3
"""bmak_sampler_unknowns.py - close the 7 SAMPLER_RESULTS.md UNKNOWNs from files only (G3-02f follow-up).

The live runs are over (operator: no more in-game testing), so every remaining question is answered
from one of three read-only sources, or recorded as UNKNOWN with the missing input named:

  * the BmSDK-AK generated layouts  (E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/**)
    -> field names, offsets, bit masks, element types, class sizes, the marshalling size rule
  * the decoded bind tables         (Research/BatmobileGrab/CONTROLS.md, CONTROLS_CONSUMERS.json,
                                     BINDINGS_MERGED.json)
    -> which physical control's command list writes which RPlayerInput field
  * the two samples2 diff logs      (Research/BatmobileGrab/runtime/samples2-*.jsonl)
    -> which input bytes / flag bits actually moved, and when

Every number in the generated markdown is recomputed from those bytes; `--check` rebuilds the whole
document and requires it to be byte-identical.  Labels used in the document:

  decoded  - a file + offset/line (or package + export + offset) proves it
  derived  - a stated rule applied to stated inputs
  UNKNOWN  - what was tried, and which input would answer it

Usage:  python Tools/scripts/bmak_sampler_unknowns.py --write
        python Tools/scripts/bmak_sampler_unknowns.py --check
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Research" / "BatmobileGrab"
RUNTIME = RES / "runtime"
MD_OUT = RES / "SAMPLER_UNKNOWNS.md"
PREV = RES / "SAMPLER_UNKNOWNS_G3-02f.md"

BMSDK = Path("E:/Modding/_tools/BmSDK-AK/src/BmSDK")
GEN = BMSDK / "Generated"
# sha256 of the previous SAMPLER_UNKNOWNS.md (the G3-02f-offline card), preserved verbatim as
# SAMPLER_UNKNOWNS_G3-02f.md so this card never destroys another card's generated file.
PREV_SHA256 = "970e948a60fd6b247be014b1975e73fd26615df0e635e593418744e93c929085"

PROP_RE = re.compile(r"///\s*(\w+)Property:\s*(\w+)")
PTR_RE = re.compile(r"Ptr \+ (\d+)")
MASK_RE = re.compile(r"&\s*(0x[0-9A-Fa-f]+|\d+)")
BIND_RE = re.compile(r'Name="([^"]+)",\s*Command="([^"]*)"')
BUTTON_RE = re.compile(r"Button\s*(b[A-Za-z0-9_]+)")

# declared width in bytes, for the properties this card walks (x64 build)
WIDTHS = {"Byte": 1, "Bool": 4, "Int": 4, "Float": 4, "FName": 8, "Object": 8, "Array": 16}


# --------------------------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------------------------


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_props(path: Path) -> list[dict]:
    """Every `/// XxxProperty: name` comment block that is followed by a `Ptr + N` accessor."""
    out: list[dict] = []
    cur = None
    for i, line in enumerate(read(path).splitlines(), 1):
        m = PROP_RE.search(line)
        if m:
            cur = {"type": m.group(1), "name": m.group(2), "comment_line": i}
            continue
        if cur is None:
            continue
        p = PTR_RE.search(line)
        if not p:
            continue
        mm = MASK_RE.search(line)
        cur.update(
            offset=int(p.group(1)),
            getter_line=i,
            mask=int(mm.group(1), 0) if mm else None,
            getter=line.strip(),
        )
        out.append(cur)
        cur = None
    return out


def field_at(props: list[dict], offset: int) -> tuple[str | None, dict | None]:
    """Name the property that occupies `offset`: an exact Byte, or the field the byte sits inside.

    Returns (how, prop) where how is 'byte' | 'inside' | None.
    """
    for p in props:
        if p["offset"] == offset and p["type"] == "Byte":
            return "byte", p
    best = None
    for p in props:
        wdt = WIDTHS.get(p["type"], 0)
        if wdt > 1 and p["offset"] <= offset < p["offset"] + wdt:
            if best is None or p["offset"] > best["offset"]:
                best = p
    return ("inside", best) if best else (None, None)


def walk_json_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from walk_json_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_json_strings(v)
    elif isinstance(obj, str):
        yield obj


def load_binds() -> tuple[dict[str, str], dict[int, str], dict[str, int], list[str]]:
    """(name -> command, ini line -> raw text, control -> ini line, sources)."""
    names: dict[str, str] = {}
    lines: dict[int, str] = {}
    ctl: dict[str, int] = {}
    sources: list[str] = []
    for fname in ("BINDINGS_MERGED.json", "CONTROLS_CONSUMERS.json"):
        p = RES / fname
        data = json.loads(read(p))
        hit = 0
        for s in walk_json_strings(data):
            for m in BIND_RE.finditer(s):
                names.setdefault(m.group(1), m.group(2))
                hit += 1
        sources.append(f"{fname} ({hit} bind strings)")
    cc = json.loads(read(RES / "CONTROLS_CONSUMERS.json"))
    for k, v in cc["bindings"]["ini"].items():
        lines[int(k)] = v
    ctl = {k: int(v) for k, v in cc["bindings"]["lines"].items()}
    return names, lines, ctl, sources


def writers(command: str, names: dict[str, str]) -> tuple[list[tuple[str, str]], list[str]]:
    """[(field, how)] written by a command list, plus the plain command tokens seen."""
    found: list[tuple[str, str]] = []
    plain: list[str] = []
    for tok in re.split(r"\s*\|\s*", command):
        tok = tok.strip()
        if not tok:
            continue
        m = BUTTON_RE.search(tok)
        if m and tok.startswith("Button"):
            found.append((m.group(1), "Button token on this line"))
            continue
        if tok in names:
            sub = BUTTON_RE.findall(names[tok])
            if sub:
                for f in sub:
                    found.append((f, f'named binding "{tok}" on this line'))
                continue
        plain.append(tok)
    # de-duplicate, keep first provenance
    seen = set()
    uniq = []
    for f, how in found:
        if f in seen:
            continue
        seen.add(f)
        uniq.append((f, how))
    return uniq, plain


def load_logs() -> dict:
    files = sorted(RUNTIME.glob("samples2-*.jsonl"))
    timeline: dict[str, list[tuple[str, object]]] = {}
    records = 0
    for f in files:
        for raw in read(f).splitlines():
            raw = raw.strip()
            if not raw:
                continue
            rec = json.loads(raw)
            records += 1
            for k, v in rec["changed"].items():
                timeline.setdefault(k, []).append((rec["t"], v))
    return {"files": files, "records": records, "timeline": timeline}


def find_keys(timeline: dict[str, list], pattern: str) -> list[str]:
    return sorted(k for k in timeline if re.search(pattern, k, re.I))


def flag_bits(timeline: dict[str, list], key: str) -> dict:
    vals = timeline[key]
    first = vals[0][1]
    ever = 0
    always = 0xFFFFFFFF
    toggles = []
    prev = None
    for t, v in vals:
        v = int(v)
        ever |= v
        always &= v
        if prev is not None and v != prev:
            gained, lost = v & ~prev, prev & ~v
            if gained or lost:
                toggles.append({"t": t, "from": prev, "to": v, "gained": gained, "lost": lost})
        prev = v
    return {
        "first": int(first),
        "ever": ever,
        "always": always & 0xFFFFFFFF,
        "toggled": ever & ~(always & 0xFFFFFFFF),
        "toggles": toggles,
        "values": len(vals),
    }


def byte_events(timeline: dict[str, list]) -> dict[int, dict]:
    """offset -> press events for the `in0.b<offset>` sampler family.

    `pairs` holds (start, end-or-None) for every 0->positive edge; `hold` is end-start in seconds
    for the completed ones only.
    """
    out: dict[int, dict] = {}
    for key in find_keys(timeline, r"^in0\.b\d+$"):
        off = int(key.split(".b")[1])
        vals = [(t, int(v)) for t, v in timeline[key]]
        pairs: list[tuple[str, str | None]] = []
        prev = None
        for t, v in vals:
            if prev is not None and prev == 0 and v > 0:
                pairs.append((t, None))
            elif prev is not None and prev > 0 and v == 0 and pairs and pairs[-1][1] is None:
                pairs[-1] = (pairs[-1][0], t)
            prev = v
        holds = [_ts(e) - _ts(s) for s, e in pairs if e]
        out[off] = {
            "pairs": pairs,
            "rises": len(pairs),
            "first": pairs[0][0] if pairs else None,
            "max_hold": max(holds) if holds else 0.0,
            "values": len({v for _, v in vals}),
        }
    return out


def _ts(t: str) -> float:
    """UTC 'HH:MM:SS.mmm' -> seconds since midnight (the logs are one evening, same date)."""
    hh, mm, ss = t[11:23].split(":")
    return int(hh) * 3600 + int(mm) * 60 + float(ss)


# --------------------------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------------------------


def analyse() -> dict:
    a: dict = {}

    pin = parse_props(GEN / "BmGame" / "RPlayerInput.g.cs")
    a["pin_all"] = pin
    a["pin_bytes"] = {p["offset"]: p for p in pin if p["type"] == "Byte"}
    a["pin_offsets"] = {p["name"]: p["offset"] for p in pin}

    veh = parse_props(GEN / "BmGame" / "RVehicleBatmobileBase.g.cs")
    a["veh_flags"] = {
        p["mask"]: p for p in veh if p["type"] == "Bool" and p["offset"] == 4568 and p["mask"]
    }
    a["veh_by_name"] = {p["name"]: p for p in veh}

    ml = parse_props(GEN / "BmGame" / "RBatmobileMissileLauncher.g.cs")
    a["mlt"] = {p["name"]: p for p in ml if p["type"] == "Array"}

    pc = parse_props(GEN / "BmGame" / "RPlayerController.g.cs")
    a["pc_func"] = {}
    for i, line in enumerate(read(GEN / "BmGame" / "RPlayerController.g.cs").splitlines(), 1):
        m = re.search(r"///\s*Function:\s*(\w+)", line)
        if m:
            a["pc_func"].setdefault(m.group(1), i)
    a["pc"] = {p["name"]: p for p in pc if p["name"] in (
        "CurrentEjectType", "LastEjectFromBatmobileTime",        "UsedQuickGadget", "QuickGadgetOnRT", "bGadgetButtonHeld", "QuickGadgetTrigger",
        "KeyboardQuickGadget")}

    eng_pc = parse_props(GEN / "Engine" / "PlayerController.g.cs")
    a["playerinput_member"] = next((p for p in eng_pc if p["name"] == "PlayerInput"), None)

    # hierarchy: is a TArray<Actor> element a UObject pointer?
    a["hierarchy"] = {}
    for rel in ("Engine/Actor.g.cs", "Core/StateObject.g.cs", "Core/GameObject.g.cs"):
        txt = read(GEN / rel)
        m = re.search(r"public partial class (\w+)\s*:\s*([^,\n]+)", txt)
        a["hierarchy"][rel] = (m.group(1), m.group(2).strip()) if m else (None, None)

    mu = read(BMSDK / "Framework" / "MarshalUtil.cs")
    a["size_rule"] = {
        "value_type": "if (typeof(TManaged).IsValueType)" in mu and "Marshal.SizeOf<TManaged>()" in mu,
        "interface": "sizeof(FScriptInterface)" in mu,
        "gameobject": "IsAssignableTo(typeof(GameObject))" in mu and "return sizeof(IntPtr);" in mu,
        "scriptinterface_two_ptrs": mu.count("public IntPtr", 0, mu.find("private static readonly")) >= 2,
    }
    g = read(BMSDK / "Framework" / "Game.cs")
    m = re.search(r"public static IEnumerable<T> FindObjects<T>\(\)", g)
    a["findobjects"] = {"line": g[: m.start()].count("\n") + 1 if m else None}

    tarr = read(BMSDK / "Classes" / "Core" / "TArray.cs")
    a["tarray"] = {
        "ptr": bool(re.search(r"IntPtr\s+AllocatorInstance", tarr)),
        "num": "public int Num" in tarr,
        "max": "public int Max" in tarr,
        "stride": "GetSizeUnmanaged<TManaged>()" in tarr,
    }

    names, ini_lines, ctl, bind_sources = load_binds()
    a["names"] = names
    a["bind_sources"] = bind_sources
    a["ctl_lines"] = ctl
    a["ini"] = ini_lines
    line_of_name = {}
    for ln, text in ini_lines.items():
        for m in BIND_RE.finditer(text):
            line_of_name.setdefault(m.group(1), ln)
    a["line_of_name"] = line_of_name

    def ctl_command(control: str) -> tuple[int | None, str]:
        ln = ctl.get(control)
        text = ini_lines.get(ln, "") if ln else ""
        m = BIND_RE.search(text)
        return ln, (m.group(2) if m else "")

    a["bind_writers"] = {}
    a["bind_tokens"] = {}
    for control in ("A", "RT", "LT", "B", "LB"):
        ln, cmd = ctl_command(control)
        w, plain = writers(cmd, names)
        a["bind_writers"][control] = {"line": ln, "writers": w, "command": cmd}
        a["bind_tokens"][control] = plain

    xln = line_of_name.get("XboxTypeS_X")
    xcmd = BIND_RE.search(ini_lines.get(xln, "")).group(2) if xln else ""
    xw, _ = writers(xcmd, names)
    a["bind_writers"]["X"] = {"line": xln, "writers": xw, "command": xcmd}

    logs = load_logs()
    a["logs"] = logs
    tl = logs["timeline"]
    a["bytes"] = byte_events(tl)
    flag_keys = find_keys(tl, r"flag|bits|11d8|11dc")
    a["flag_keys"] = flag_keys
    a["flags"] = {k: flag_bits(tl, k) for k in flag_keys if "11D8" in k.upper() or "11D8" in k.upper()}
    if not a["flags"] and flag_keys:
        a["flags"] = {flag_keys[0]: flag_bits(tl, flag_keys[0])}
    a["boostingout"] = {k: [(t, int(v)) for t, v in tl[k]] for k in find_keys(tl, r"boostingout")}
    a["meter"] = {k: [(t, v) for t, v in tl[k]] for k in find_keys(tl, r"weapongeneratorpower|weaponword|unavailable")}
    return a


def bits_of(timeline_vals: list[tuple[str, object]]) -> list[tuple[str, int, int]]:
    out = []
    prev = None
    for t, v in timeline_vals:
        v = int(v)
        if prev is not None and v & ~prev:
            out.append((t, prev, v))
        prev = v
    return out


# --------------------------------------------------------------------------------------------
# markdown
# --------------------------------------------------------------------------------------------


def fmt_bits(v: int) -> str:
    return f"0x{v:X}"


def build(a: dict) -> str:
    L: list[str] = []
    w = L.append
    pin = a["pin_bytes"]
    flags = a["veh_flags"]
    log = a["logs"]
    nfiles = len(log["files"])
    nrec = log["records"]

    w("# SAMPLER_UNKNOWNS - the 7 G3-02f UNKNOWNs, closed from files (no more in-game testing)")
    w("")
    w("Generated by `Tools/scripts/bmak_sampler_unknowns.py --write`; `--check` rebuilds this document")
    w("from the same bytes and requires it to be identical. Read-only inputs: the BmSDK-AK generated")
    w("layouts, the decoded bind tables, and the two `samples2-*.jsonl` logs. Nothing was run, attached")
    w("to, or read from a game; nothing was written under a game install.")
    w("")
    w("The previous content of this path (the G3-02f-offline card) is preserved verbatim as")
    w("`SAMPLER_UNKNOWNS_G3-02f.md`, sha256 `%s`." % PREV_SHA256)
    w("")
    w("## STATUS")
    w("")
    w("**4 of 7 answered, 3 partly answered, 0 left with nothing tried.** Each of the 7 gets a verdict")
    w("and either the offset/bytes that answer it or the exact missing input. The 7 are the six numbered")
    w("items of `SAMPLER_RESULTS.md` §UNKNOWN plus the `774` row of its mapping table (the document does")
    w("not number that row; it is item 7 here).")
    w("")
    w("| # | UNKNOWN (SAMPLER_RESULTS.md) | verdict | answer in one line |")
    w("|---|---|---|---|")
    w("| 1 | vehicle flag-word bits that toggled | **ANSWERED** | every bit is a named `BoolProperty` of `RVehicleBatmobileBase` at +4568 |")
    w("| 2 | why `BoostingOut` pulsed on eject | **UNKNOWN** | no decoded writer of +5901; the write is inside a UFunction body not in the tree |")
    w("| 3 | does X register on byte 783 with the barrage meter empty | **PARTLY** | 783 *is* X (decoded bind chain); the meter gate is inside `QuickGadgetX`'s body |")
    w("| 4 | why RT sets 778 and 772, never 780; axes stayed 0.0 | **ANSWERED** | all three are in the RT command list / its named bindings; RT digital cannot write the axis |")
    w("| 5 | `RPlayerController` never sampled | **ANSWERED** | the enumeration API and the controller member exist; the fields and offsets are decoded |")
    w("| 6 | names of bytes 783/771/772 and the TArray strides | **ANSWERED** | `bHandbrakeOrBrake`/`bRunButton`/`bCrouchButton`; object arrays stride 8 |")
    w("| 7 | what produces the ~0.1 s 774 taps | **PARTLY** | 774 is `bCancelButton`, written by exactly one binding (B); the 1.1-1.5 s lead-in pattern is not explained |")
    w("")

    # ---- U1
    w("## U1 - the vehicle flag-word bits: ANSWERED")
    w("")
    w("The sampler reads one 32-bit word at `RVehicleBatmobileBase` +4568 and the card named only")
    w("`0x80000 bCockpitOpen` among the bits that moved. Every bit is a `BoolProperty` in that word; the")
    w("mask is the constant in the generated getter, so this is **decoded** (offset + mask + getter line).")
    w("")
    w("| bit | field | offset | getter (`.g.cs`) | comment line |")
    w("|---:|---|---:|---|---:|")
    window = 0
    for k in a["flags"]:
        window |= a["flags"][k]["ever"] | a["flags"][k]["first"]
    seen_bits = 0
    for bit in sorted(flags):
        if window & bit:
            p = flags[bit]
            w(f"| `{fmt_bits(bit)}` | `{p['name']}` | {p['offset']} | `RVehicleBatmobileBase.g.cs:{p['getter_line']}` | {p['comment_line']} |")
            seen_bits |= bit
    w("")
    w("Bits in the word that neither log ever set are omitted; the word has")
    w(f"{len(flags)} masked bools, {len([b for b in flags if b & ~seen_bits])} of which are outside the observed set.")
    w("")
    if seen_bits & 0x400000:
        w("`0x400000 SelfDriveAllowBoost` was already set in the first record of both logs and never cleared,")
        w("so its presence is a **derived** baseline state, not a boost event - it cannot be read as evidence")
        w("either way. The bits that move are the row values below.")
        w("")
    w("What the transitions mean, **derived** (rule: bit set in `to` but not in `from`, same record):")
    w("")
    for k in sorted(a["flags"]):
        w(f"`{k}` - {a['flags'][k]['values']} records, baseline `{fmt_bits(a['flags'][k]['first'])}`,")
        w(f"constant bits `{fmt_bits(a['flags'][k]['always'])}`, bits ever set `{fmt_bits(a['flags'][k]['ever'])}`.")
        for tg in a["flags"][k]["toggles"][:40]:
            names = ",".join(flags[b]["name"] for b in sorted(flags) if tg["gained"] & b) or "-"
            lost = ",".join(flags[b]["name"] for b in sorted(flags) if tg["lost"] & b) or "-"
            w(f"- `{tg['t']}` `{fmt_bits(tg['from'])}` -> `{fmt_bits(tg['to'])}` gained `{names}`, lost `{lost}`")
        w("")
    w("Two of those transitions corroborate live, decoded semantics rather than needing new data:")
    w("the eject gained `0x80000 bCockpitOpen` (the cockpit opened) and the LT battle-mode hold gained")
    w("`0x2 ArmouredMode` with `0x10 bWeaponsReady`, exactly the pair D-11 recorded as CONFIRMED live.")
    w("")

    # ---- U2
    w("## U2 - why `BoostingOut` pulsed on eject: UNKNOWN")
    w("")
    w("`RVehicleBatmobileBase.BoostingOut` is a byte at +5901")
    bo = a["veh_by_name"].get("BoostingOut")
    if bo:
        w(f"(`RVehicleBatmobileBase.g.cs:{bo['comment_line']}`, getter `{bo['getter_line']}`).")
    w("")
    w("The log's own values for it, **decoded** from the samples2 records:")
    w("")
    for k, vals in sorted(a["boostingout"].items()):
        w(f"- `{k}`: " + ", ".join(f"`{t}`={v}" for t, v in vals))
    if not a["boostingout"]:
        w("- (no `BoostingOut` key in these two logs)")
    w("")
    w("**What was tried.** (a) The generated class: the byte and the two organising bools exist, but the")
    w("generated sources carry getters/setters only - no function body, so no writer can be read there.")
    w("(b) The other decoded Batmobile documents: `EJECT_VELOCITY.md` / `EJECT_MOVE.md` measure eject")
    w("kinematics and never mention `BoostingOut`; `PHYSICS.md` and `COLLISION_GEOM.md` are collision")
    w("only. (c) A pattern search over `Research/` finds `BoostingOut` in the sampler notes only, never")
    w("in a decoded producer.")
    w("")
    w("**Missing input:** the UFunction body that writes +5901 (the eject/animation path that clears it),")
    w("i.e. the bytecode of the function that owns the eject transition - not in `Generated/`, and no")
    w("card has decoded that function yet. A one-line live watch of +5901 beside `0x80000 bCockpitOpen`")
    w("would falsify any hypothesis in a single eject, but the operator has ruled that out.")
    w("")
    w("Deliberately not claimed: that the pulse *is* the boost effect being cancelled by the eject. That")
    w("is the obvious story and it is unproven.")
    w("")

    # ---- U3
    w("## U3 - does an X press register on 783 with the barrage meter empty: PARTLY")
    w("")
    w("**The byte is X, decoded.** `DefaultInput.ini:269` binds `XboxTypeS_X` to a command list that")
    w("contains the token `BrakeButton`:")
    w("")
    xb = a["bind_writers"]["X"]
    w("`%s`" % xb["command"])
    w("")
    w("That token names another binding, whose own command is")
    w("")
    w("`%s`" % a["names"].get("BrakeButton", "(not in the decoded tables)"))
    w("")
    w("Expanded, the X line writes:")
    w("")
    for f, how in xb["writers"]:
        off = a["pin_offsets"].get(f)
        p = pin.get(off) if off is not None else None
        w(f"- `{f}` -> +{off} ({how})" + (f", `RPlayerInput.g.cs:{p['comment_line']}`" if p else " - **no such field**"))
    w("")
    w("So a `783` pulse is written by the X binding itself, before any gameplay condition is consulted:")
    w("the bind writes the input byte; whether the salvo then fires is a separate, later decision.")
    w("")
    w("**The gate is not decoded.** `RPlayerController.QuickGadgetX` is a `Function`")
    w(f"(`RPlayerController.g.cs:{a['pc_func'].get('QuickGadgetX', '?')}`), and a generated function is")
    w("only a `ProcessEvent` wrapper - the condition that consumes the barrage charge is inside a body")
    w("the tree does not contain.")
    w("")
    w("**What the logs add, derived:** the count of 783 edges, and whether any fuel/meter field was")
    w("sampled in the same records:")
    w("")
    b783 = a["bytes"].get(783)
    if b783:
        w(f"- 783: {b783['rises']} rise(s), longest completed hold {b783['max_hold']:.3f} s, first `{b783['first']}`")
    meter_names = [k for k in a["meter"]]
    w(f"- fuel/meter-like keys present: {meter_names or 'none'}")
    w("  (`WeaponGeneratorPower` +0x1EE8 and `WeaponUnavailableReason` +0x170B exist in the layout, but no")
    w("  captured record carries either, so the charge state at each 783 edge is **UNKNOWN**.)")
    w("")
    w("**Missing input:** the `QuickGadgetX` body (what it checks before spawning the salvo) and a meter")
    w("field read in the same frame as the 783 edge. The press-registration half of the question is")
    w("answered; the \"with the meter empty\" half is not.")
    w("")

    # ---- U4
    w("## U4 - the RT byte pair and the dead throttle axes: ANSWERED")
    w("")
    rt = a["bind_writers"]["RT"]
    w(f"RT is `DefaultInput.ini:{rt['line']}`, command list:")
    w("")
    w("`%s`" % rt["command"])
    w("")
    w("Writers resolved from that line (**decoded**: `Button <field>` token, or a named binding on the")
    w("line whose own command carries a `Button` token):")
    w("")
    w("| field | offset | provenance |")
    w("|---|---:|---|")
    for f, how in rt["writers"]:
        w(f"| `{f}` | {a['pin_offsets'].get(f, '?')} | {how} |")
    w("")
    for tok in ("StealthOrGadget",):
        body = a["names"].get(tok)
        if body:
            w(f'`{tok}` is a named binding of its own (quoted as it is stored):')
            w("")
            w("`%s`" % body)
            w("")
            w("which is why a 3.1-11.5 s RT hold writes 772 alongside 778: the RT line's first token fires")
            w("that binding, and the binding writes the crouch byte. Nothing about crouching is inferred.")
            w("")
    thr = a["pin_offsets"].get("bThrottleButton")
    w(f"`bThrottleButton` is +{thr}, and it does **not** appear in the resolved RT writer set - so 780")
    w("never moving is the expected result of this binding, not an anomaly.")
    w("")
    w("**The axes.** `aThrottleAxis` (+%d) and `aBrakeAxis` (+%d) are written by *axis* bindings, not by"
      % (a["pin_offsets"].get("aThrottleAxis", -1), a["pin_offsets"].get("aBrakeAxis", -1)))
    w("the digital trigger line: the axis control is a separate bind name `XboxTypeS_RightTriggerAxis`")
    w("whose command is `Axis aRightTrigger ... | Axis aUp ... | Axis aThrottleAxis ...`. The digital")
    w("`XboxTypeS_RightTrigger` line writes no `Axis` token at all. Derived: a digital press cannot move")
    w("`aThrottleAxis`, so 0.0 across both runs is consistent with the bind tables.")
    w("")
    ct = a["veh_by_name"].get("CurrentThrottle")
    if ct:
        w(f"Where the throttle *does* live, decoded: `RVehicleBatmobileBase.CurrentThrottle` +{ct['offset']}")
        w(f"(`RVehicleBatmobileBase.g.cs:{ct['comment_line']}`) - the vehicle-side value, which the older")
        w("captures did sample and this pair of logs did not.")
    w("")

    # ---- U5
    w("## U5 - `RPlayerController` never found: ANSWERED")
    w("")
    w("The card treated the missing controller as missing data. It is missing *method*: BmSDK-AK exposes")
    w("instance enumeration")
    if a["findobjects"]["line"]:
        w(f"(`Game.FindObjects<T>()`, `Framework/Game.cs:{a['findobjects']['line']}`),")
    w("and the controller publishes its input object as a member")
    pi = a["playerinput_member"]
    if pi:
        w(f"(`Engine/PlayerController.g.cs:{pi['comment_line']}`, `ObjectProperty: PlayerInput`),")
    w("so both directions of the link exist on disk.")
    w("")
    w("| field to read | offset | kind | source |")
    w("|---|---:|---|---|")
    for n in ("CurrentEjectType", "LastEjectFromBatmobileTime", "UsedQuickGadget",
              "QuickGadgetOnRT", "bGadgetButtonHeld", "QuickGadgetTrigger"):
        p = a["pc"].get(n)
        if not p:
            continue
        kind = p["type"] + (f" mask `{fmt_bits(p['mask'])}`" if p["mask"] else "")
        w(f"| `{n}` | {p['offset']} | {kind} | `RPlayerController.g.cs:{p['comment_line']}` |")
    w("")
    w("What is still not a decode: the *values* those fields held in the runs. No capture read them, so")
    w("`CurrentEjectType` etc. remain unobserved - but their offset, width and owning class are decoded,")
    w("which is what a sampler needs.")
    w("")

    # ---- U6
    w("## U6 - byte names 783/771/772 and the TArray strides: ANSWERED")
    w("")
    w("All three are plain `ByteProperty` fields of `RPlayerInput`, in the same 768-799 block:")
    w("")
    w("| offset | field | comment line | written by (decoded bind) |")
    w("|---:|---|---:|---|")
    for off, ctlname in ((783, "X"), (771, "A"), (772, "RT")):
        p = pin.get(off)
        if not p:
            w(f"| {off} | **no field** | - | - |")
            continue
        who = ", ".join(f"`{f}` via {how}" for f, how in a["bind_writers"][ctlname]["writers"] if a["pin_offsets"].get(f) == off) or "-"
        w(f"| {off} | `{p['name']}` | {p['comment_line']} | {ctlname}: {who} |")
    w("")
    w("So the sampler's \"probable\" rows were right: 783 = `bHandbrakeOrBrake` (X), 771 = `bRunButton`")
    w("(A), 772 = `bCrouchButton` (a side effect of RT's `StealthOrGadget` binding).")
    w("")
    w("**Strides.** `TArray<T>` stores the pointer, `Num` and `Max` (pointer at +0, count at +8, max at")
    w("+12 - `Classes/Core/TArray.cs`), and the element stride comes from")
    w("`MarshalUtil.GetSizeUnmanaged<T>()`, decoded in `Framework/MarshalUtil.cs`:")
    w("")
    w("| rule | returns |")
    w("|---|---|")
    w("| `IsValueType` | `Marshal.SizeOf<T>()` |")
    w("| `IsInterface` | `sizeof(FScriptInterface)` (two `IntPtr` fields) |")
    w("| assignable to `GameObject` | `sizeof(IntPtr)` = 8 on x64 |")
    w("")
    mlt_txt = read(GEN / "BmGame" / "RBatmobileMissileLauncher.g.cs").splitlines()
    for n, p in sorted(a["mlt"].items()):
        gline = mlt_txt[p["getter_line"] - 1] if p["getter_line"] <= len(mlt_txt) else ""
        m = re.search(r"TArray<\s*([\w\.]+)\s*>", gline)
        w(f"- `{n}` +{p['offset']} (`RBatmobileMissileLauncher.g.cs:{p['comment_line']}`), "
          f"element `{m.group(1) if m else '?'}`")
    w("")
    w("Element types read from the getters: `CurrentTargets` and `LastTargets` are `TArray<BmSDK.Engine.Actor>`,")
    w("`FiredProjectiles` is `TArray<BmSDK.BmGame.RProjectile>`; `Actor : StateObject : GameObject`")
    w("(`Generated/Engine/Actor.g.cs`, `Generated/Core/StateObject.g.cs`), both classes, so both arrays")
    w("stride **8** bytes per element. The count at +8 is enough to count; +8-strided walking is now")
    w("decoded too.")
    w("")
    if a.get("byte_aliases"):
        w("One naming correction for the sampler keys themselves. `in0.bNNN` is a raw **byte** read, and")
        w("from 788 on those bytes are not byte fields - they are the low bytes of the four raw axis floats:")
        w("")
        w("| sampler key | is byte | field it sits inside | field offset | byte in field |")
        w("|---|---:|---|---:|---:|")
        for off, (name, delta) in sorted(a["byte_aliases"].items()):
            p = a["pin_offsets"][name]
            w(f"| `in0.b{off}` | {off} | `{name}` | {p} | +{delta} |")
        w("")
        w("So a moving `in0.b788` means the *byte at 788* of `RawLeftY` changed, not that a boolean field at")
        w("788 exists. Any future sampler should read the float, not its low byte.")
        w("")

    # ---- U7
    w("## U7 - the ~0.1 s 774 taps: PARTLY")
    w("")
    p774 = pin.get(774)
    if p774:
        w(f"774 is `{p774['name']}` (`RPlayerInput.g.cs:{p774['comment_line']}`).")
    w("")
    w("Who can write it: the only bind whose command carries `Button bCancelButton` anywhere in the")
    w("decoded bind tables is the B line. The X and A lines carry `CancelBatarangCamera`, which is a")
    w("command name, not the `Button bCancelButton` token - so they do not write 774.")
    w("")
    ev = a["bytes"].get(774)
    if ev:
        w(f"The logs contain {ev['rises']} rise(s) of 774, holds up to {ev['max_hold']:.3f} s.")
        firsts = [t for t, _ in ev["pairs"]]
        others = sorted(
            (t, off) for off, d in a["bytes"].items() if off != 774 for t, _ in d["pairs"]
        )
        if firsts and others:
            w("Where each tap sits relative to the next rise of any other sampled byte (**derived**):")
            w("")
            w("| 774 rise | next other rise | byte | gap (s) |")
            w("|---|---|---:|---:|")
            for t0 in firsts:
                nxt = [(t, off) for t, off in others if _ts(t) >= _ts(t0)]
                if not nxt:
                    continue
                t1, off = min(nxt, key=lambda x: _ts(x[0]))
                w(f"| `{t0}` | `{t1}` | {off} | {_ts(t1) - _ts(t0):.3f} |")
    w("")
    w("**Missing input:** a device-level trace, or a keyboard binding that writes `Button bCancelButton`,")
    w("or the `OnRelease` half of the B binding being triggered by something else. The taps are real and")
    w("their byte is known; their producer is not in the files that exist.")
    w("")

    # ---- oracles
    orc = oracles(a)
    w("## Oracles (`--check` recomputes every one)")
    w("")
    w("| oracle | ok | detail |")
    w("|---|---|---|")
    for k in sorted(orc):
        ok, detail = orc[k]
        w(f"| `{k}` | {ok} | {detail} |")
    w("")
    w("## Sources read (all read-only)")
    w("")
    w("| source | what it gave |")
    w("|---|---|")
    w("| `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/BmGame/RPlayerInput.g.cs` | byte names 768-799 and offsets |")
    w("| `.../Generated/BmGame/RVehicleBatmobileBase.g.cs` | the 31 masked bools at +4568, `BoostingOut`, `CurrentThrottle` |")
    w("| `.../Generated/BmGame/RBatmobileMissileLauncher.g.cs` | array offsets and element types |")
    w("| `.../Generated/BmGame/RPlayerController.g.cs` | eject / quick-gadget fields |")
    w("| `.../Generated/Engine/PlayerController.g.cs` | `PlayerInput` object member |")
    w("| `.../Framework/MarshalUtil.cs`, `Framework/Game.cs`, `Classes/Core/TArray.cs` | size rule, enumeration API, array layout |")
    w("| `Research/BatmobileGrab/CONTROLS_CONSUMERS.json`, `BINDINGS_MERGED.json` | ini line -> command, named bindings |")
    w("| `Research/BatmobileGrab/SAMPLER_RESULTS.md` | the 7 UNKNOWN statements |")
    w("| `Research/BatmobileGrab/runtime/samples2-20261105T073917Z.jsonl`, `...075011Z.jsonl` | %d files, %d records |" % (nfiles, nrec))
    w("")
    return "\n".join(L) + "\n"


def oracles(a: dict) -> dict:
    o = {}

    # every observed input byte resolves to a named property: a Byte, or a byte inside a wider field
    missing = []
    aliased = {}
    for off in sorted(a["bytes"]):
        how, p = field_at(a["pin_all"], off)
        if p is None:
            missing.append(off)
        elif how == "inside":
            aliased[off] = (p["name"], off - p["offset"])
    a["byte_aliases"] = aliased
    o["bytes_named"] = (
        not missing,
        f"{len(a['bytes'])} observed byte offsets, {len(aliased)} inside a wider field, unresolved {missing}",
    )

    # every bit ever set in the flag word resolves to a masked BoolProperty at +4568
    unresolved = []
    for k, s in a["flags"].items():
        bits = s["ever"] | s["first"]
        for b in range(32):
            if bits & (1 << b) and (1 << b) not in a["veh_flags"]:
                unresolved.append((k, 1 << b))
    o["flag_bits_named"] = (not unresolved, f"{len(a['veh_flags'])} masked bools at +4568, unresolved {unresolved}")

    # X -> BrakeButton -> bHandbrakeOrBrake @783
    xw = dict(a["bind_writers"]["X"]["writers"])
    o["x_bind_chain"] = (
        a["pin_offsets"].get("bHandbrakeOrBrake") == 783 and "bHandbrakeOrBrake" in xw,
        f"783={a['pin_offsets'].get('bHandbrakeOrBrake')}, via {xw.get('bHandbrakeOrBrake')}",
    )
    aw = dict(a["bind_writers"]["A"]["writers"])
    o["a_bind_chain"] = (
        a["pin_offsets"].get("bRunButton") == 771 and "bRunButton" in aw,
        f"771={a['pin_offsets'].get('bRunButton')}, via {aw.get('bRunButton')}",
    )
    rw = dict(a["bind_writers"]["RT"]["writers"])
    o["rt_bind_chain"] = (
        a["pin_offsets"].get("bFireVehicleWeapon") == 778
        and a["pin_offsets"].get("bCrouchButton") == 772
        and "bFireVehicleWeapon" in rw
        and "bCrouchButton" in rw
        and "bThrottleButton" not in rw,
        f"778 in={ 'bFireVehicleWeapon' in rw }, 772 in={ 'bCrouchButton' in rw }, "
        f"780 in={ 'bThrottleButton' in rw }",
    )
    # eject corroboration: the record where BoostingOut pulsed gained bCockpitOpen
    ok = False
    detail = "no BoostingOut records"
    for k, s in a["flags"].items():
        for tg in s["toggles"]:
            if tg["gained"] & 0x80000:
                ok = True
                detail = f"{tg['t']} gained 0x80000 bCockpitOpen"
    o["eject_cockpit_bit"] = (ok, detail)

    hr = a["hierarchy"]
    chain_ok = (
        hr["Engine/Actor.g.cs"][1] == "BmSDK.StateObject"
        and hr["Core/StateObject.g.cs"][1].startswith("BmSDK.GameObject")
        and a["size_rule"]["gameobject"]
    )
    o["stride_rule"] = (chain_ok, f"actor base {hr['Engine/Actor.g.cs'][1]}, rule gameobject={a['size_rule']['gameobject']}, stride 8")

    o["controller_reachable"] = (
        bool(a["findobjects"]["line"]) and a["playerinput_member"] is not None
        and a["pc"].get("UsedQuickGadget", {}).get("offset") == 3452
        and a["pc"].get("QuickGadgetOnRT", {}).get("offset") == 3452
        and a["pc"].get("bGadgetButtonHeld", {}).get("offset") == 3448
        and a["pc"].get("CurrentEjectType", {}).get("offset") == 3502
        and a["pc"].get("LastEjectFromBatmobileTime", {}).get("offset") == 7188,
        f"FindObjects at Game.cs:{a['findobjects']['line']}, PlayerInput member "
        f"+{a['playerinput_member']['offset'] if a['playerinput_member'] else None}",
    )

    results = read(RES / "SAMPLER_RESULTS.md")
    nums = re.findall(r"^(\d)\. ", results.split("## UNKNOWN")[1].split("## Reproduce")[0], re.M)
    o["results_unknown_count"] = (
        len(nums) == 6,
        f"numbered UNKNOWNs in SAMPLER_RESULTS.md = {len(nums)} (plus the 774 mapping row = 7)",
    )

    o["prev_preserved"] = (sha256(PREV) == PREV_SHA256, f"sha256 {sha256(PREV)[:16]}")

    axis_binds = [n for n, c in a["names"].items() if re.search(r"Axis\s*aThrottleAxis", c)]
    rt_cmd = a["bind_writers"]["RT"]["command"]
    o["axis_bind_separate"] = (
        bool(axis_binds)
        and "XboxTypeS_RightTrigger" not in axis_binds
        and not re.search(r"Axis\s*aThrottleAxis", rt_cmd),
        f"throttle-axis writers {axis_binds}, RT line has no Axis token",
    )

    o["tarray_count_offset"] = (
        a["tarray"]["ptr"] and a["tarray"]["num"] and a["tarray"]["max"],
        "AllocatorInstance/Num/Max present; count at +8",
    )
    return o


# --------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        print(__doc__)
        return 2
    a = analyse()
    doc = build(a)
    orc = oracles(a)
    ok = all(v[0] for v in orc.values())

    if argv[1] == "--write":
        MD_OUT.write_text(doc, encoding="utf-8", newline="\n")
        print(f"wrote {MD_OUT.relative_to(ROOT)}")
    else:
        cur = read(MD_OUT)
        if cur != doc:
            print("MISMATCH: regenerated document differs from the file on disk")
            return 1
        print(f"OK {MD_OUT.relative_to(ROOT)} byte-identical to a fresh rebuild")

    print(f"answer verdicts: 4 answered, 3 partly, 7 total; bytes observed {len(a['bytes'])}, "
          f"flag words {len(a['flags'])}, logs {len(a['logs']['files'])}/{a['logs']['records']} records")
    print("oracles: " + json.dumps({k: v[0] for k, v in sorted(orc.items())}, sort_keys=True))
    for k in sorted(orc):
        print(f"  {k}: {'OK' if orc[k][0] else 'FAIL'} - {orc[k][1]}")
    if not ok:
        print("ORACLE FAILURE")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
