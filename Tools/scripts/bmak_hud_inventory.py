"""bmak_hud_inventory.py - inventory the HUD from the engine's roster, not from a name guess.

The first HUD grab carved two movies from a hand-written list. That list was an assertion: the
game runs **25 `RHudModule*` classes**, and each class names its own movie in its class default
object (`RHudModuleBatmobile` -> `HudModuleBatmobile.Image`). A grab driven by `HudModule*`
filenames therefore misses every module whose movie is named differently (`RadialGadgetSelect`)
and every module whose movie it never thought to look for.

This tool does what the old list could not:

  roster       read `BmGame.upk`, list every `RHudModule*` class, its CDO's `SwfMovie` reference,
               its `Set*` / `CachedFunction_*` surface -> the authoritative module list
  build        carve the union of (a) every `HudModule*`/container movie and (b) every movie a
               native module points at; one directory per movie, keyed so two movies in one
               package (`HudModuleDownloadProgress.Image` vs `...HudModuleDownload_Batman`)
               cannot overwrite each other
  interface    read the decompiled scripts, extract every `UC_*` setter with its signature ->
               `HUD_INTERFACES.json`, then bind each native class to the movie whose setters it
               calls (a class's `CachedFunction_X` names must appear as `UC_X` in the movie)
  check        re-read the game, compare roster + carved bytes, and list roster movies that are
               not carved (a gap is data, not a silent omission)
  decompile    run ffdec over every carved movie (needs java + ffdec.jar)

Record: `Research/BatmobileGrab/HUD_INVENTORY.json`. Movies stay outside the repository.

Usage:
  python Tools/scripts/bmak_hud_inventory.py roster
  python Tools/scripts/bmak_hud_inventory.py build
  python Tools/scripts/bmak_hud_inventory.py interface
  python Tools/scripts/bmak_hud_inventory.py check
  python Tools/scripts/bmak_hud_inventory.py decompile
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upk_read import Package, export_summary  # noqa: E402
import bmak_hud  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Research" / "BatmobileGrab" / "HUD_INVENTORY.json"
IFACE = ROOT / "Research" / "BatmobileGrab" / "HUD_INTERFACES.json"
DEC = Path(os.environ.get("BMAK_HUD_OUT", r"E:/Modding/_gamedata/BmAKgrab_early/hud")) / "modules"
FFDEC = Path(os.environ.get("FFDEC", r"E:/Modding/_tools/ffdec/ffdec.jar"))
PACKAGES = ("BmGame.upk", "Startup.upk")
HUD_CLASS = "RHudModule"
# Movies that are HUD even without a module naming them: the container document, the shared
# prompt HUD, and the gadget wheel (its module caches no function names, so it is carved on
# the strength of the movie being in-game HUD -- if no class matches it, the gap is reported).
EXTRA_MOVIES = ("ModularHudBm3.Image", "StoryModeHUD.HUD", "RadialGadgetSelect.Image")


def movie_key(path: str) -> str:
    """Directory name for a movie: `X.Image` -> `X`, other sub-movies keep their suffix."""
    base, _, suffix = path.partition(".")
    if suffix in ("", "Image", "HUD"):
        return base
    if suffix.startswith(base):
        suffix = suffix[len(base):].lstrip("_")
    return f"{base}_{suffix}" if suffix else base


def movies() -> list[dict]:
    rows = []
    for pkg_name in PACKAGES:
        pkg = Package(str(bmak_hud.GAME / "BmGame" / "CookedPCConsole" / pkg_name))
        for i in range(1, pkg.export_count + 1):
            if pkg.object_class(i) != "SwfMovie":
                continue
            path = pkg.object_path(i)
            short = path.split(".")[0]
            rows.append({"package": pkg_name, "object": path, "short": short,
                         "key": movie_key(path),
                         "size": pkg.exports[i - 1]["size"]})
    rows.sort(key=lambda r: r["object"])
    return rows


_OWNERS: list[dict] | None = None


def owners() -> list[dict]:
    """Every class default object that names a SwfMovie, HUD class or not.

    The `RHudModule*` name is not the only owner: `RGFxMovieRadialGadgetSelect` owns the gadget
    wheel movie, and a module can own more than one movie (`RHudModuleDownloadProgress` names both
    the progress movie and its `HudModuleDownload_Batman` extension). Reading only the first tag
    or only the module namespace loses both facts.
    """
    global _OWNERS
    if _OWNERS is not None:
        return _OWNERS
    pkg = Package(str(bmak_hud.GAME / "BmGame" / "CookedPCConsole" / "BmGame.upk"))
    rows = []
    for i, e in enumerate(pkg.exports, 1):
        if not e["name"].startswith("Default__"):
            continue
        try:
            tags = export_summary(pkg, i, max_tags=200)["tags"]
        except Exception:
            continue
        movies = [t["ref"] for t in tags if t.get("ref_class") == "SwfMovie" and t.get("ref")]
        if movies:
            rows.append({"class": e["name"][len("Default__"):], "movies": sorted(set(movies))})
    _OWNERS = rows
    return rows


def roster() -> list[dict]:
    """Every native HUD module class, its movie references and its callable surface."""
    pkg = Package(str(bmak_hud.GAME / "BmGame" / "CookedPCConsole" / "BmGame.upk"))
    own = {o["class"]: o["movies"] for o in owners()}
    classes = [e["name"] for e in pkg.exports
               if e["outer_index"] == 0 and e["name"].startswith(HUD_CLASS)
               and e["name"] != HUD_CLASS]
    paths = {i: pkg.object_path(i) for i in range(1, pkg.export_count + 1)}
    rows = []
    for cls in sorted(set(classes)):
        movies = own.get(cls, [])
        # A module can own an extension movie as well as its main one; the canonical name ends
        # in `.Image`/`.HUD`, so prefer that over `..._Batman`-style sub-movies.
        primary = sorted(movies, key=lambda m: (not m.endswith((".Image", ".HUD")), m))
        movie = primary[0] if primary else None
        members = [(pkg.object_class(i), path.split(".", 1)[1])
                   for i, path in paths.items() if path.startswith(cls + ".")]
        funcs = sorted(m for c, m in members if c == "Function")
        rows.append({
            "class": cls,
            "movie": movie,
            "movies": movies,
            "cdo_movie": movie,
            "movie_key": movie_key(movie) if movie else None,
            "functions": len(funcs),
            "setters": [f for f in funcs if f.startswith("Set")],
            "cached": sorted(m[len("CachedFunction_"):] for c, m in members
                             if c == "StrProperty" and m.startswith("CachedFunction_")),
        })
    return rows


def carve_units() -> tuple[list[dict], list[dict]]:
    """(movies to carve, native roster) - the roster is read once and reused."""
    native = roster()
    all_movies = {m["object"]: m for m in movies()}
    wanted = [m for m in all_movies.values()
              if m["object"] in EXTRA_MOVIES or m["object"].split(".")[0].startswith("HudModule")]
    for mod in native:
        for movie in mod.get("movies") or []:
            if movie in all_movies:
                if all_movies[movie] not in wanted:
                    wanted.append(all_movies[movie])
            else:
                mod["missing_movie"] = movie
    wanted.sort(key=lambda r: r["object"])
    return wanted, native


def build() -> dict:
    wanted, native = carve_units()
    carved = []
    for r in wanted:
        payload, data = bmak_hud.carve(r["package"], r["object"])
        d = DEC / r["key"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "movie.gfx").write_bytes(payload)
        dec = d / "dec" / "scripts"
        carved.append({**r, "payload_bytes": len(payload), "inflated_bytes": len(data),
                       "sha256": hashlib.sha256(payload).hexdigest(),
                       "gfx": str(d / "movie.gfx"),
                       "scripts": len(list(dec.rglob("*.as"))) if dec.exists() else 0})
    for m in native:
        m["carved"] = bool(m["movie_key"]) and any(c["key"] == m["movie_key"] for c in carved)
    doc = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    keys = {r["key"] for r in carved}
    others = [o for o in owners()
              if not o["class"].startswith(HUD_CLASS)
              and any(movie_key(m) in keys for m in o["movies"])]
    doc.update({
        "packages": list(PACKAGES), "movies": movies(), "carved": len(carved),
        "hud_movies": carved, "native_modules": native,
        "other_movie_owners": others,
        "missing_movies": sorted(f"{m['class']} -> {m['missing_movie']}"
                                 for m in native if m.get("missing_movie")),
    })
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"{len(doc['movies'])} SwfMovie exports | {len(native)} native modules | "
          f"{len(carved)} movies carved -> {OUT}")
    for r in carved:
        print(f"  {r['key']:34} {r['payload_bytes']:9,} B  {r['object']}")
    gaps = [m for m in native if not m["carved"]]
    if gaps:
        print(f"\n{len(gaps)} native modules without a carved movie:")
        for m in gaps:
            print(f"  {m['class']:38} {m['movie'] or '(no SwfMovie reference)'}")
    return doc


SETTER = re.compile(r"public\s+function\s+(UC_[A-Za-z0-9_]+)\s*\(([^)]*)\)")


def interface() -> dict:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    modules = {}
    for r in doc["hud_movies"]:
        scripts = Path(r["gfx"]).parent / "dec" / "scripts"
        if not scripts.exists():
            print(f"skip  {r['key']} (not decompiled)")
            continue
        setters, structs = {}, set()
        for f in scripts.rglob("*.as"):
            if f.name.startswith("ModuleStruct"):
                structs.add(f.stem)
            for name, args in SETTER.findall(f.read_text(encoding="utf-8", errors="replace")):
                args = " ".join(args.split())
                setters.setdefault(name, args)
        modules[r["key"]] = {
            "object": r["object"],
            "structs": sorted(structs),
            "setters": [{"name": k, "args": v} for k, v in sorted(setters.items())],
        }
    doc["interfaces"] = modules
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    IFACE.write_text(json.dumps(modules, indent=1) + "\n", encoding="utf-8")
    total = sum(len(m["setters"]) for m in modules.values())
    print(f"{len(modules)} movies, {total} UC_* setters -> {IFACE}")
    for key, m in sorted(modules.items()):
        print(f"  {key:34} {len(m['setters']):3} setters  {', '.join(m['structs'])[:60]}")
    match(doc, modules)
    return modules


def match(doc: dict, modules: dict) -> dict:
    """Pair each native class with the movie whose `UC_*` surface it calls.

    A module's `CachedFunction_X` properties are the AS function names it resolves at runtime;
    the movie defines `UC_X`. Overlap is evidence, not a guess, so a class with no `SwfMovie`
    reference in its default object can still be bound to its movie (Boss -> HudModuleBoss).
    """
    surfaces = {key: {n[3:] if n.startswith("UC_") else n for n in
                      (s["name"] for s in m["setters"])}
                for key, m in modules.items()}
    rows = []
    for mod in doc["native_modules"]:
        cdo = mod.get("cdo_movie")
        cached = set(mod["cached"])
        best_key, best_score = None, 0
        for key, names in surfaces.items():
            score = len(cached & names) if cached else 0
            if score > best_score:
                best_key, best_score = key, score
        # No cached names at all (GadgetSelect): fall back to the class's own Set/Setup names.
        fallback = set()
        if not cached:
            fallback = {f for f in mod["setters"] if f.startswith(("Set", "Setup", "Show", "Hide"))}
            for key, names in surfaces.items():
                score = len(fallback & names)
                if score > best_score:
                    best_key, best_score = key, score
        total = len(cached) or len(fallback)
        proven = bool(best_key) and best_score >= (2 if total >= 2 else 1)
        src = "default-object" if cdo else ("interface-match" if proven else None)
        if src == "default-object":
            best_key = mod["movie_key"]
        elif not proven:
            best_key = None
        rows.append({**mod, "cdo_movie": cdo,
                     "movie": cdo or (modules[best_key]["object"] if best_key else None),
                     "movie_key": best_key, "movie_source": src,
                     "match_score": best_score, "match_total": total})
    doc["native_modules"] = rows
    doc["unmatched"] = sorted(m["class"] for m in rows if not m["movie"])
    owned = {movie_key(m) for o in doc.get("other_movie_owners", []) for m in o["movies"]}
    owned |= {movie_key(m) for mod in doc["native_modules"] for m in mod.get("movies") or []}
    owned |= {m["movie_key"] for m in rows if m["movie_key"]}
    # The container document and the prompt HUD are stand-alone movies, not module movies.
    owned |= {"ModularHudBm3", "StoryModeHUD"}
    doc["unclaimed_movies"] = sorted(set(modules) - owned)
    doc["interfaces"] = modules
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"\n{'native module':38} {'movie':34} {'source':16} score")
    for m in rows:
        score = (f"{m['match_score']}/{m['match_total']}"
                 if m["movie_source"] == "interface-match" else "-")
        print(f"  {m['class']:36} {str(m['movie'] or '-'):34} {str(m['movie_source'] or '-'):16} {score}")
    if doc["unmatched"]:
        print(f"\n{len(doc['unmatched'])} module(s) with no movie: {', '.join(doc['unmatched'])}")
    for o in doc.get("other_movie_owners", []):
        print(f"  owner (not RHudModule*): {o['class']:32} {', '.join(o['movies'])}")
    if doc["unclaimed_movies"]:
        print(f"{len(doc['unclaimed_movies'])} carved movie(s) with no owner: "
              f"{', '.join(doc['unclaimed_movies'])}")
    return doc


def check() -> int:
    if not OUT.exists():
        print("FAIL: no HUD_INVENTORY.json - run `build` first")
        return 1
    old = json.loads(OUT.read_text(encoding="utf-8"))
    bad = 0
    now = movies()
    if [r["object"] for r in now] != [r["object"] for r in old["movies"]]:
        print("FAIL: the SwfMovie census changed")
        bad += 1
    native = roster()
    if [(m["class"], m["cdo_movie"]) for m in native] != \
            [(m["class"], m.get("cdo_movie")) for m in old["native_modules"]]:
        print("FAIL: the RHudModule roster changed")
        bad += 1
    for r in old["hud_movies"]:
        payload, data = bmak_hud.carve(r["package"], r["object"])
        if (len(payload) != r["payload_bytes"] or len(data) != r["inflated_bytes"]
                or hashlib.sha256(payload).hexdigest() != r["sha256"]):
            print(f"FAIL {r['key']}: carved bytes differ")
            bad += 1
    keys = {c["key"] for c in old["hud_movies"]}
    others = [o for o in owners()
              if not o["class"].startswith(HUD_CLASS)
              and any(movie_key(m) in keys for m in o["movies"])]
    if others != old.get("other_movie_owners"):
        print("FAIL: the non-RHudModule movie owners changed")
        bad += 1
    iface = old.get("interfaces") or {}
    missing = [c["key"] for c in old["hud_movies"] if c.get("scripts") and c["key"] not in iface]
    if missing:
        print(f"FAIL: {len(missing)} decompiled movie(s) have no interface record: "
              f"{', '.join(missing)}")
        bad += 1
    gaps = [m for m in old["native_modules"] if not any(c["key"] == m["movie_key"]
                                                        for c in old["hud_movies"])]
    print(f"{'PASS' if not bad else 'FAIL'}: {len(native)} native modules, "
          f"{len(old['hud_movies'])} movies, {len(now)} SwfMovie exports, "
          f"{sum(len(m['setters']) for m in iface.values())} setters, "
          f"{len(gaps)} module(s) without a movie")
    for m in gaps:
        print(f"  gap: {m['class']:38} {m['movie'] or '(no SwfMovie reference)'}")
    return 1 if bad else 0


def decompile() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    if not FFDEC.exists():
        raise SystemExit(f"no ffdec at {FFDEC} (set FFDEC=...)")
    for r in doc["hud_movies"]:
        gfx = Path(r["gfx"])
        out = gfx.parent / "dec"
        if (out / "scripts").exists():
            print(f"skip  {r['key']} (already decompiled)")
            r["scripts"] = len(list((out / "scripts").rglob("*.as")))
            continue
        cmd = ["java", "-jar", str(FFDEC), "-export", "script", str(out), str(gfx)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        n = len(list((out / "scripts").rglob("*.as"))) if (out / "scripts").exists() else 0
        print(f"{'ok' if p.returncode == 0 else 'FAIL'}  {r['key']:34} {n:3} scripts")
        r["scripts"] = n
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("roster", "build", "interface", "check", "decompile"))
    a = ap.parse_args()
    if a.action == "roster":
        native = roster()
        print(f"{len(native)} native HUD modules")
        for m in native:
            print(f"  {m['class']:38} {m['movie'] or '(none)':34} "
                  f"{m['functions']:3} funcs")
        return 0
    if a.action == "build":
        build()
        return 0
    if a.action == "interface":
        interface()
        return 0
    if a.action == "check":
        return check()
    return decompile()


if __name__ == "__main__":
    sys.exit(main())
