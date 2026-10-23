r"""grab_native.py - what the *executable* carries for the Batmobile classes (G1-1 evidence).

The cooked packages strip the class definitions: `RVehicleBatmobile`, `RVehicleSimBatmobile` and the
`RBatmobile*` gameplay classes are imported from `BmScript`, which is not shipped as a package. The
property *names* therefore live in `BatmanAK.exe`'s native class registration, not in any `.upk`.

This tool establishes what the binary does and does not expose, so G1-1's disposition rests on a
measurement instead of an assumption:

  * UE3 registers native functions as `<Class><U?A?>exec<Function>` strings. Those are plain ASCII in
    the image, so the vehicle classes' native API can be enumerated exactly.
  * The same image does **not** carry a class-qualified property table: the only strings that start
    with a vehicle class name are the `exec` entries (plus the class names themselves). Property names
    such as `Mass`/`Grip` do not appear as fields of any such table.

Writes `Research/BatmobileGrab/NATIVE.json` + `NATIVE.md`.

Usage:
    python Tools/scripts/grab_native.py --write
    python Tools/scripts/grab_native.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
EXE = r"E:\Games\Batman - Arkham Knight\Binaries\Win64\BatmanAK.exe"

# The classes G1-1 is about, plus the two the binary revealed (subclasses of RVehicleBatmobile that
# appear in no shipped package's class list).
TARGETS = ("RVehicleBatmobile", "RVehicleSimBatmobile", "RVehicleBatmobileBase",
           "RVehicleBatmobilePredictor")
PREFIX = re.compile(rb"([AU]?)(RVehicle[A-Za-z0-9_]*?|RBatmobile[A-Za-z0-9_]*?)exec([A-Za-z0-9_]+)")


class NativeError(Exception):
    pass


def scan(path: str) -> dict:
    data = open(path, "rb").read()
    classes: dict[str, set[str]] = {}
    for m in PREFIX.finditer(data):
        ua, cls, fn = (m.group(i).decode("ascii") for i in (1, 2, 3))
        classes.setdefault(ua + cls, set()).add(fn)
    # A class name on its own is also in the image (the registration table); record which targets
    # appear at all, because a missing one would mean the class is not native.
    names = {}
    for t in TARGETS:
        naked = data.count(t.encode("ascii"))
        names[t] = naked
    return {"image": path, "size": len(data),
            "classes": {k: sorted(v) for k, v in sorted(classes.items())},
            "name_mentions": names}


def prop_strings(path: str) -> dict:
    """What a property table would look like if it existed: `ClassName` + property, no `exec`.

    UE3 native registrations for properties are `FProperty` objects built from bare names, so a
    class-qualified `<Class><Property>` string would be the only in-image way to bind name to offset.
    Count those: for every target class, strings that start with the class name and are *not* exec.
    """
    data = open(path, "rb").read()
    out = {}
    for t in TARGETS:
        rx = re.compile(re.escape(t.encode("ascii")) + rb"[A-Z][A-Za-z0-9_]{2,60}")
        hits = {m.group().decode("ascii") for m in rx.finditer(data)}
        out[t] = sorted(h for h in hits
                        if "exec" not in h and not h.endswith(t) and not h.startswith("RVehicleBatmobileBase")
                        and not h.startswith("RVehicleBatmobilePredictor"))
    return out


def build() -> dict:
    if not os.path.isfile(EXE):
        raise NativeError("no executable at %s" % EXE)
    doc = scan(EXE)
    doc["schema"] = 1
    doc["generated_by"] = "grab_native.py"
    doc["property_table_candidates"] = prop_strings(EXE)
    doc["summary"] = {
        "classes": len(doc["classes"]),
        "functions": sum(len(v) for v in doc["classes"].values()),
        "target_classes_found": [t for t, n in doc["name_mentions"].items() if n],
        "property_table_strings": sum(len(v) for v in doc["property_table_candidates"].values()),
    }
    return doc


def check(doc: dict) -> list[str]:
    bad = []
    if not doc["classes"]:
        bad.append("no native functions found")
    for t in ("RVehicleBatmobile", "RVehicleSimBatmobile"):
        if not doc["name_mentions"].get(t):
            bad.append("%s not named in the image" % t)
    if doc["summary"]["property_table_strings"]:
        bad.append("class-qualified property strings exist: %s"
                   % doc["property_table_candidates"])
    # The five sim entry points the grab already relied on must be present. The class key carries
    # the UE3 prefix the image uses (`URVehicleSimBatmobile`), so match by suffix.
    sim = set()
    for k, v in doc["classes"].items():
        if k.endswith("RVehicleSimBatmobile"):
            sim.update(v)
    for fn in ("Boost", "SetSuspensionForDriveMode", "SetDriveMode",
               "ForceUpdateTyreFriction", "SkidToStop"):
        if fn not in sim:
            bad.append("RVehicleSimBatmobile.%s missing from the native table" % fn)
    return bad


def write_md(doc: dict) -> None:
    L = ["# What the executable carries for the Batmobile classes (G1-1 evidence)", "",
         "Generated by `Tools/scripts/grab_native.py` from `%s` (%d bytes)."
         % (os.path.basename(doc["image"]), doc["size"]), "",
         "The cooked packages import `RVehicleBatmobile`, `RVehicleSimBatmobile` and the `RBatmobile*`",
         "classes from `BmScript`, which is not shipped. UE3 registers **native functions** as",
         "`<Class>exec<Function>` ASCII strings, so the binary's side of those classes is readable even",
         "though the packages are not.", "",
         "| fact | value |", "|---|---|",
         "| vehicle classes with native functions | **%d** |" % doc["summary"]["classes"],
         "| native functions | **%d** |" % doc["summary"]["functions"],
         "| class-qualified *property* strings | **%d** |" % doc["summary"]["property_table_strings"],
         "", "## Classes and functions", "",
         "| class | functions |", "|---|---|"]
    for k, v in doc["classes"].items():
        if not k.endswith(("RVehicleBatmobile", "RVehicleBatmobileBase",
                           "RVehicleBatmobilePredictor", "RVehicleSimBatmobile")):
            continue
        L.append("| `%s` | %d |" % (k, len(v)))
    L += ["", "### Full lists", ""]
    for k, v in doc["classes"].items():
        if not k.endswith(("RVehicleBatmobile", "RVehicleBatmobileBase",
                           "RVehicleBatmobilePredictor", "RVehicleSimBatmobile")):
            continue
        L += ["**`%s`** (%d)" % (k, len(v)), "", "```"]
        L += ["  " + fn for fn in v]
        L += ["```", ""]
    L += ["## What this settles", "",
          "The binary exposes the classes' *behaviour* (the native API) and not their *layout*: there is",
          "no class-qualified property string in the image, so no name can be bound to an offset without",
          "disassembling the registration code. That is the same wall `OFFSETS.md` records from the",
          "package side, now measured from the other side too.", "",
          "Two class names appear here that no shipped package lists - `RVehicleBatmobileBase` and",
          "`RVehicleBatmobilePredictor` - which fixes the parent/subclass relation the offsets belong to.",
          ""]
    open(os.path.join(OUT, "NATIVE.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    bad = check(doc)
    if a.write:
        with open(os.path.join(OUT, "NATIVE.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        write_md(doc)
    print("%d classes, %d native functions, %d property-table strings"
          % (doc["summary"]["classes"], doc["summary"]["functions"],
             doc["summary"]["property_table_strings"]))
    for k, v in doc["classes"].items():
        print("  %-32s %d" % (k, len(v)))
    if bad:
        print("\nFAIL")
        for b in bad:
            print(" ", b)
        sys.exit(1)
    print("checks: target classes named, sim entry points present, no property table - ok")


if __name__ == "__main__":
    main()
