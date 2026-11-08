"""texture_build_plan.py - one ordered list of the BmAK textures that are still dropped or baked.

Merges four research reports into a single build order:

  tmp/freebuff/reports/app-microdetail-bake-plan.md      -> the s1 micro-detail bake (POL-2)
  tmp/freebuff/reports/app-emissive-mask-channel.md      -> CarLight s5 / CarPaintMM m_Emissive
  tmp/freebuff/reports/app-texture-binding-audit.md      -> role -> sampler census, mask packing
  tmp/freebuff/reports/app-damage-chapter-masks.md       -> the chapter masks (D9)

Every row names: the BmAK texture, whether its pixels are on disk, its destination block and
channel, the transform, the check that proves it, and whether the route is faithful. The status
column is NOT invented here - it is read from Working/Appearance/progress.json, the file
`appearance_progress.py` writes from the build itself.

Usage:
  python Tools/scripts/texture_build_plan.py --write   # write md + json
  python Tools/scripts/texture_build_plan.py --check   # re-derive and compare byte for byte
"""
import argparse
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_MD = os.path.join(ROOT, "Working", "Appearance", "TEXTURE_BUILD_PLAN.md")
OUT_JS = os.path.join(ROOT, "Working", "Appearance", "TEXTURE_BUILD_PLAN.json")
PROGRESS = os.path.join(ROOT, "Working", "Appearance", "progress.json")

# stage order = build order. `status` comes from progress.json; `faithful` is this file's verdict.
ROWS = [
    # ---------------------------------------------------------------- 1. albedo / normal (already shipped)
    dict(stage=1, rule="—", tex="Batmobile_V3_Body_N", role="normal", on_disk="yes",
         dest="CarPaintMM s1 NormalMap", ch="RGB (tangent normal)",
         xform="BC5 re-encode at the allocator cap; no bake",
         check="in the build today: .ddsc exists, block s1 binds it", faithful="yes"),
    dict(stage=1, rule="—", tex="Batmobile_V3_Body_Decals_D", role="albedo", on_disk="yes",
         dest="CarPaintMM s7 DecalAlbedo", ch="RGB + A",
         xform="BC1/BC3 as authored", check=".ddsc exists and a decal block binds it", faithful="yes"),
    # ---------------------------------------------------------------- 2. mask packing (s2 / s3)
    dict(stage=2, rule="D3", tex="Batmobile_V3_BRAKE_DISC_R", role="mask (roughness)",
         on_disk="yes", dest="CarPaintMM s2 PropertyMap", ch="channels R/G/B/A",
         xform="band the per-pixel roughness into the four s2 channel levels; texel-weighted mean",
         check="band histogram == mask bin fractions +-1 %; s2 rebuilt and byte-identical re-encode",
         faithful="partial"),
    dict(stage=2, rule="D3", tex="Batmobile_V3_Int_Cockpit_S", role="mask (reflectivity)",
         on_disk="yes", dest="CarPaintMM s2 PropertyMap", ch="channels R/G/B/A",
         xform="four-band mean into s2; the bands are shared with gloss, so report the quantisation error",
         check="band histogram + reported error; the same s2 selector as the gloss plan",
         faithful="partial"),
    dict(stage=2, rule="D3", tex="Batmobile_V3_Missile_Upgrade_S", role="mask (reflectivity)",
         on_disk="yes", dest="CarPaintMM s2 PropertyMap", ch="channels R/G/B/A",
         xform="four-band mean into s2", check="band histogram + reported error", faithful="partial"),
    dict(stage=2, rule="D3", tex="Nimbus_Power_Cell_S", role="mask (reflectivity)",
         on_disk="yes", dest="CarPaintMM s2 PropertyMap", ch="channels R/G/B/A",
         xform="four-band mean into s2", check="band histogram + reported error", faithful="partial"),
    # ---------------------------------------------------------------- 3. micro-detail bake into s1
    dict(stage=3, rule="P1", tex="Batmobile_Microdetail", role="micro-detail normal", on_disk="yes",
         dest="CarPaintMM s1 NormalMap (baked)", ch="tangent XY of the RNM blend",
         xform="reoriented normal mapping, tile at UV1 x T_eff (T=15 body family), weight 1 on channel 0",
         check="C1 difference-spectrum >= 0.5x tile; C2 repeat-frequency peak at T_eff; C3 seam; C4 low band",
         faithful="yes"),
    dict(stage=3, rule="P1", tex="Batmobile_Micropattern_A", role="micro-detail normal", on_disk="no",
         dest="CarPaintMM s1 (channel 1, emissive material only)", ch="tangent XY",
         xform="same bake as channel 0 once the pixels exist",
         check="C1-C4 on the baked channel; today: cannot run", faithful="no"),
    dict(stage=3, rule="P1", tex="Batmobile_Micropattern_A_Normal", role="micro-detail normal",
         on_disk="no", dest="CarPaintMM s1 (Material3 detail)", ch="tangent XY",
         xform="same bake once the pixels exist", check="C1-C4; today: cannot run", faithful="no"),
    dict(stage=3, rule="P1", tex="Batmobile_Micropattern_B", role="micro-detail albedo", on_disk="no",
         dest="CarPaintMM s0 DiffuseMap (baked) and s1", ch="RGB into s0, slope into s1",
         xform="multiply into albedo + RNM into s1 once the pixels exist",
         check="C1-C5; today: cannot run", faithful="no"),
    dict(stage=3, rule="P1", tex="Batmobile_Micropattern_C", role="micro-detail", on_disk="no",
         dest="CarPaintMM s1 (channels 2/3)", ch="tangent XY",
         xform="same bake once the pixels exist", check="C1-C4; today: cannot run", faithful="no"),
    dict(stage=3, rule="P1", tex="neutral_normal", role="value, not an asset", on_disk="n/a",
         dest="—", ch="—", xform="none: it is a flat normal constant the material points at",
         check="n/a - excluded from the bake", faithful="yes"),
    # ---------------------------------------------------------------- 4. emissive
    dict(stage=4, rule="R2", tex="Batmobile_V3_Int_Cockpit_E", role="emissive", on_disk="yes",
         dest="CarLight s5 EmissiveMap; else CarPaintMM m_Emissive (4 bands)",
         ch="RGB = colour x coverage, A = max(R,G,B)",
         xform="re-bake the atlas in the lamp mesh's own UV space; RGB as authored, alpha copy; BC3",
         check="T1 channel census, T2 round-trip (A == max(RGB)), T5 UV-island containment, T6 gates",
         faithful="yes"),
    dict(stage=4, rule="R2", tex="Batmobile_V3_Wheel_E", role="emissive", on_disk="no",
         dest="CarLight s5 (four arch strips already built)", ch="RGB + A",
         xform="same as Int_Cockpit_E once the pixels exist",
         check="T1/T2/T5 once grabbed; today the strips must stay dark and emit 0",
         faithful="no"),
    # ---------------------------------------------------------------- 5. glass
    dict(stage=5, rule="R4", tex="Batmobile_V3_Glass_S", role="glass layer mask", on_disk="yes",
         dest="Window material-level tint (no per-layer slot)", ch="scalar tint",
         xform="fold the layer mask into the tint constant", check="glass tint read back from the block",
         faithful="partial"),
    # ---------------------------------------------------------------- 6. colour ramps (blocked)
    dict(stage=6, rule="D10", tex="Batman_BM3_V2_Lacquered_Underlayer_Ramp", role="ramp", on_disk="no",
         dest="CarPaintMM s3 TintMap (2-D approximation) or the s1/s2 bake", ch="—",
         xform="none until the ramp pixels exist; the name index resolves but no file does",
         check="blocked: the ramp rows stay open, no faithful route", faithful="no"),
    dict(stage=6, rule="D10", tex="Batman_BM3_V2_Leather_Ramp", role="ramp", on_disk="no",
         dest="CarPaintMM s3 TintMap (seat) or m_Emissive bands", ch="—",
         xform="none until the ramp pixels exist",
         check="blocked: the ramp rows stay open, no faithful route", faithful="no"),
    dict(stage=6, rule="D10", tex="Batmobile_V3_Body_ColourRamp", role="ramp", on_disk="no",
         dest="CarPaintMM s3 TintMap; the banded s2 tint", ch="—",
         xform="none until the ramp pixels exist",
         check="blocked: the ramp rows stay open, no faithful route", faithful="no"),
    dict(stage=6, rule="D5", tex="Aniso_ramp_Lacquered", role="anisotropy ramp", on_disk="yes",
         dest="folded into the s1/s2 bake (no anisotropy sampler on any block)", ch="—",
         xform="UV-space fake: the two lobes are baked as a normal perturbation, not shipped as a ramp",
         check="the bake's C1-C4 on the affected s1; the 0-of-961-headers absence is recorded",
         faithful="partial"),
    # ---------------------------------------------------------------- 7. chapter damage (no faithful route)
    dict(stage=7, rule="D9", tex="Batmobile_V3_TEXTURES_Body_Damage_ChapterMask", role="damage chapter",
         on_disk="yes", dest="CarPaintMM s5 DamageAlbedoMap + SupportDmgBlend 1", ch="RGB",
         xform="ONE fixed pre-damaged state (gate 1, m_Damage non-zero); four chapters are impossible",
         check="SupportDmgBlend and m_Damage bytes in the block; a chapter change needs an entity variant",
         faithful="no"),
    dict(stage=7, rule="D9", tex="Batmobile_V3_TEXTURES_Weaponry_Damage_ChapterMask", role="damage chapter",
         on_disk="yes", dest="CarPaintMM s5 + SupportDmgBlend 1", ch="RGB",
         xform="one fixed state only", check="as above; faithful only as a single state", faithful="no"),
    dict(stage=7, rule="D9", tex="Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask", role="damage chapter",
         on_disk="yes", dest="CarPaintMM s5 + SupportDmgBlend 1", ch="RGB",
         xform="one fixed state only", check="as above; faithful only as a single state", faithful="no"),
    dict(stage=7, rule="D9", tex="Batmobile_V3_Undercarriage_Damage_ChapterMask", role="damage chapter",
         on_disk="yes", dest="CarPaintMM s5 + SupportDmgBlend 1", ch="RGB",
         xform="one fixed state only", check="as above; faithful only as a single state", faithful="no"),
]

STAGES = {
    1: "Albedo and normal — already shipped, nothing to do (the reference rows)",
    2: "Mask packing — BmAK's separate masks into one `s2`/`s3` RGBA (`D3`)",
    3: "Micro-detail bake into `s1` — `P1`, POL-2 (reoriented normal mapping)",
    4: "Emissive — `CarLight s5` where a lamp block exists, else the `m_Emissive` bands (`R2`)",
    5: "Glass — the `Window` material tint (`R4`)",
    6: "Colour ramps — blocked on pixels that are not on disk (`D10`), or folded into the bake (`D5`)",
    7: "Chapter damage masks — no faithful route: one static state exists, four chapters do not (`D9`)",
}

EVIDENCE = {
    "P1": "`tmp/freebuff/reports/app-microdetail-bake-plan.md` §2-§5",
    "D3": "`tmp/freebuff/reports/app-per-pixel-reflectivity.md` §5.1; `app-texture-binding-audit.md` §6",
    "R2": "`tmp/freebuff/reports/app-emissive-mask-channel.md` §2.3, §5.1-§5.2",
    "R4": "`tmp/freebuff/reports/app-reflectance-f0.md`; `TEXTURE_AUDIT.md` role table",
    "D5": "`tmp/freebuff/reports/app-anisotropic-highlights.md`; `APPEARANCE_PLAN.md` D5 rule",
    "D9": "`tmp/freebuff/reports/app-damage-chapter-masks.md` §1-§4",
    "D10": "`tmp/freebuff/reports/ramp-names-quick-search.md` (names resolve, files absent)",
    "—": "`Working/Appearance/TEXTURE_AUDIT.md` (shipped files)",
}


def _status_by_texture():
    """status per texture component, read from progress.json (never invented here)."""
    if not os.path.exists(PROGRESS):
        return {}
    prog = json.load(open(PROGRESS, encoding="utf-8"))
    return {c["component"]: c for c in prog["classes"]["textures"]["components"]}


def build():
    status = _status_by_texture()
    rows = []
    for r in ROWS:
        s = status.get(r["tex"], {})
        rows.append(dict(r, status=s.get("status", "not-in-build"),
                         why=s.get("why", ""),
                         plan=(s.get("plan") or {}).get("action")))
    tally = {}
    for r in rows:
        tally[r["faithful"]] = tally.get(r["faithful"], 0) + 1
    plan_tally = {}
    for r in rows:
        plan_tally[r["plan"] or "unplanned"] = plan_tally.get(r["plan"] or "unplanned", 0) + 1
    return rows, tally, plan_tally


def render(rows, tally, plan_tally):
    L = []
    A = L.append
    A("# TEXTURE BUILD PLAN — the BmAK textures that are still dropped or baked")
    A("")
    A("Generated by `Tools/scripts/texture_build_plan.py --write` (no timestamp: the page is")
    A("byte-stable, so `--check` re-derives it exactly); `--check` re-derives")
    A("this page and the json byte for byte. One ordered list, merged from four research reports:")
    A("`app-microdetail-bake-plan`, `app-emissive-mask-channel`, `app-texture-binding-audit`,")
    A("`app-damage-chapter-masks`. The `status` column is read from `Working/Appearance/progress.json`")
    A("(written by `appearance_progress.py` from the build itself), never from a log.")
    A("")
    A("Read the columns as: **destination** = the block and channel that will carry the meaning;")
    A("**transform** = what the bake/pack does; **check** = the test that can fail; **faithful** =")
    A("whether that route carries *all* of BmAK's meaning (`yes`), part of it (`partial`), or none (`no`).")
    A("")
    A("## 0. The totals")
    A("")
    A("| faithful | rows | meaning |")
    A("|---|---:|---|")
    A(f"| yes | {tally.get('yes', 0)} | the route carries the whole meaning |")
    A(f"| partial | {tally.get('partial', 0)} | carried as a band, a mean or a tint — the per-pixel part is a gap |")
    A(f"| no | {tally.get('no', 0)} | **no faithful route**: pixels absent, or the mechanism has no JC3 slot |")
    A("")
    A("| plan action (from `progress.json`) | rows |")
    A("|---|---:|")
    for k in ("bake", "route", "drop", "unplanned"):
        if k in plan_tally:
            A(f"| {k} | {plan_tally[k]} |")
    A("")
    no_route = [r["tex"] for r in rows if r["faithful"] == "no"]
    A(f"**No faithful route today ({len(no_route)}):** " + ", ".join(f"`{t}`" for t in no_route) + ".")
    A("")
    A("Each one is blocked for a stated reason, not skipped: the `Micropattern_*` family and")
    A("`Batmobile_V3_Wheel_E` have no pixels in the 115-file grab; the three colour ramps have their")
    A("*names* indexed (`ramp-names-quick-search.md`) but no texture file on disk; the four chapter")
    A("masks exist and can carry **one** static pre-damaged state, but JC3 has no chapter selector.")
    A("")
    A("## 1. Build order")
    A("")
    A("Order is dependency order, not preference: masks before the bake (the bake's per-channel weight")
    A("comes from the mask), the bake before the emissive atlas (both write the same atlas budget), and")
    A("the ramps/damage last because they are blocked.")
    A("")
    for stage in sorted(STAGES):
        A(f"### Stage {stage} — {STAGES[stage]}")
        A("")
        A("| rule | BmAK texture | role | on disk | destination | channel | transform | check | faithful | status |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            if r["stage"] != stage:
                continue
            A(f"| `{r['rule']}` | `{r['tex']}` | {r['role']} | {r['on_disk']} | {r['dest']} | "
              f"{r['ch']} | {r['xform']} | {r['check']} | **{r['faithful']}** | {r['status']} |")
        A("")
    A("## 2. Progress, and why the percentages do not move on their own")
    A("")
    A("`appearance_progress.py` computes `% = (transferred + 0.5 * partial) / total` from what the")
    A("**build** contains — a `.ddsc` on disk, a block of the right type in the parts, a factor's")
    A("disposition. A plan action (`bake`/`route`/`drop`) is an annotation beside that number, not an")
    A("input to it (`appearance_progress.py` `summarise()` and `attach_plan()`), so reclassifying a row")
    A("from `drop` to `route` in `appearance_plan.py` does **not** raise the percentage. The number")
    A("moves only when a texture is actually converted and registered in `assembly.json`.")
    A("")
    A("That is the honest reading of this plan: it schedules work, it does not claim the work is done.")
    A("Each row's `status` in the json is the build's own state at the last `appearance_progress.py`")
    A("run; a row whose check has been run and passed still reads `excluded`/`partial` until the")
    A("converted file exists.")
    A("")
    A("## 3. The checks, once, in full")
    A("")
    A("| check | what it proves | where it is defined |")
    A("|---|---|---|")
    A("| C1 difference spectrum | the detail reached `s1` at all | `app-microdetail-bake-plan.md` §5 |")
    A("| C2 repeat-frequency peak | the **tile scale** is right (the only reader of `MicroDetail_size`'s unit) | same |")
    A("| C3 seam / grid | the tiling is integer and aligned | same |")
    A("| C4 low band | the panel's large-scale shading did not move | same |")
    A("| C5 gloss mean | the roughness coupling constant did not do the texture's work | same §4.4 |")
    A("| T1 channel census | colour atlas vs greyscale mask, with the Old Jeep as the negative control | `app-emissive-mask-channel.md` §7 |")
    A("| T2 pack round-trip | `A == max(R,G,B)`, slot 5 points at the new atlas, RBM byte-identical | same |")
    A("| T5 UV containment | the atlas was baked in **our** lamp UVs, not Kensington's | same |")
    A("| band histogram | the `s2` bands match the mask's own bins +-1 % | `app-per-pixel-reflectivity.md` §5.1 |")
    A("| damage gate read-back | `SupportDmgBlend` == 1 and `m_Damage` != 0 for the one static state | `app-damage-chapter-masks.md` §1 |")
    A("| T6 / C6 build gates | 25/25 RBMs byte-identical, `spec_check.py` 0, `@files.xml` registered, budgets | both bake reports |")
    A("")
    A("## 4. Evidence, per rule")
    A("")
    A("| rule | report |")
    A("|---|---|")
    for k in sorted(EVIDENCE):
        if k in {r["rule"] for r in rows}:
            A(f"| `{k}` | {EVIDENCE[k]} |")
    A("")
    A("Nothing is baked by this file. It names the order, the destination and the check; the")
    A("conversion runs in the appearance pipeline and the numbers above follow the build.")
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("one of --write / --check is required")

    rows, tally, plan_tally = build()
    md = render(rows, tally, plan_tally)
    js = json.dumps({"rows": rows, "tally": tally, "plan_tally": plan_tally,
                     "stages": {str(k): v for k, v in STAGES.items()},
                     "evidence": EVIDENCE}, indent=1, sort_keys=True) + "\n"

    if a.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JS, "w", encoding="utf-8", newline="\n").write(js)
        print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({len(rows)} rows)")
        print(f"wrote {os.path.relpath(OUT_JS, ROOT)}")
        print(f"faithful: yes {tally.get('yes', 0)} partial {tally.get('partial', 0)} "
              f"no {tally.get('no', 0)}")
        return

    ok = True
    for path, want in ((OUT_MD, md), (OUT_JS, js)):
        if not os.path.exists(path):
            print(f"MISSING {os.path.relpath(path, ROOT)}")
            ok = False
            continue
        got = open(path, encoding="utf-8").read().replace("\r\n", "\n")
        if got != want:
            print(f"DRIFT {os.path.relpath(path, ROOT)}")
            ok = False
    print("check ok" if ok else "check FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
