# Review — G2-12 · The armed Serpente: civilian → signature_preorder

Independent review, 2026-10-28. Read-only: nothing under `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file was edited; this report is the only file written.

## VERDICT: minor issues

The diff itself is good work. Every number I spot-checked re-derives — including the hash
resolutions, which I recomputed independently with `rbmhdr.hash_jenkins` — and `--check` really
does re-read both `.ee` containers out of the archives, re-convert both inner `.epe`s, rebuild the
JSON and diff the Markdown. The card's premise is corrected where it is wrong (there is no second
parts module; the "added" hood/missile-base parts are defined in both modules and only instantiated
by the signature graph), which is exactly the job.

One finding is substantive and worth fixing before B-05/B-06 lean on it: **the `CForcePulse` →
`w618_sportsmuscle_missile.ftunec` link is name-matched, not decoded**, yet it appears in the
section titled "What B-05/B-06 must carry". The remaining findings are documentation consistency
and R11 typing issues, none of which change a decoded value.

## Check output (verbatim)

`python Tools/scripts/jc3sigdiff.py --check`:

```
PASS: 566 -> 601 members, graph 450 -> 464 objects, 4 added / 1 removed, 19 part rows changed, 84 mesh pairs, 2 graph objects changed
exit=0
```

No progress chatter, one verdict line, exit 0. It re-read both containers (it does not read the
`E:\Modding\JustCause3\_grab\sigdiff\` cache), so the PASS is a live decode, not a comparison against
already-written files.

## Issues

### 1. The `CForcePulse` → `ftunec` link is an inference presented as wiring — `SIGNATURE_DIFF.md:205`, `:534`

The add-list records the pulse as an object only:

> `| root/CForcePulse:w618_sportsmuscle_missile | CForcePulse | w618_sportsmuscle_missile | 1 | CForcePulse×1 |`

and §8 then says:

> "…one `CForcePulse` (`...w618...ftune`) and one `CMaterialEffectTable` (`tank_explosion_effect_table`)."

There is no pointer for that parenthetical anywhere in the artefact I can check:
`SIGNATURE_DIFF.json` carries the added pulse as `{class, classes, name, objects, path}` with **no
`props`**, and the `weapon` section's keys are `aim, autoaim, class, collision, found, model,
muzzles, name, object_id, points, rigid_object_effect_settings, slots, tune, weapon_id,
weapon_type` — no force-pulse field. The blast tune *is* decoded (`tunes.w618_sportsmuscle_missile.ftunec`,
649 B, `PlayerDamage` 1100 …) and the container *does* add it as a member, but nothing decoded here
joins the two; the join is the shared object name plus G2-17's fleet-wide pattern (a weapon
component owns a pulse whose tune is its own `jc_explosions/weapons/<id>.ftune`).

Why it matters: this is the one line a B-05/B-06 implementer would copy as "the pulse points at this
blast". G2-17's pattern makes the inference very likely right — but under R4 it is `decoded (fleet)`
at best, and the doc states it as a property of this entity. The fix is cheap: dump the pulse's own
properties (the same parse that produced `slots` and the component's `model`/`tune` already walks
these objects) and either show the pointer or mark the link "inferred from G2-17". `--check` has no
assertion on the pulse, so nothing currently guards it.

### 2. §2 and §7 give different "added" totals with no reconciliation — `SIGNATURE_DIFF.md:20` vs `:513`

§2: "566 members vs 601: **167 added** … **132 removed**".
§7: "468 records vs 498 … Added 162, removed 132."

Both are right for their own layer (container members vs `.ee.toc` records; 167−132 = +35 = 601−566,
162−132 = +30 = 498−468 — I re-derived both from the JSON), but the 5-member difference is never
named. It is explainable and small — `added_by_kind` shows `other` 6 vs 4, `texture` 27 vs 25,
`tune` 4 vs 3, and the five extra container members are two `*.tga.N_Na.trim` files, two `.ddsc`
textures and one tune — i.e. members with no load record. A reader comparing the two tables has to
do that work himself. One sentence ("five added members have no `.toc` record: two trims, two
textures, one tune") closes it.

### 3. §8 restates derived values as literals (R11) — `SIGNATURE_DIFF.md:534`, `:539`, `:541`

The §6 table derives its numbers from the decoded tune (`TUNE_KEYS` → `wt['rows'][k]`,
`ft['rows'][k]`, `len(vfs['diff'])`), and the counts elsewhere in the doc are computed. But the §8
bullets are plain string literals in `Tools/scripts/jc3sigdiff.py`:

* "`missile_turning_speed` 0, no lock-on, `magazine_size` -1, `fire_rate` 0.5 s, `damage` 1500,
  `max_range` 300 m, blast 1100 player / 500 AI in 8 m";
* "The container embeds an older 148-row `wtunec`; the patch path has 155 rows. The seven extras …
  `fire_rate_level_2` = 0.12";
* "two `CPartProp` nodes", "index 25 … index 41", "four type-2 `internal.fire_point.N` points",
  "adds that mesh's five LODs and four textures".

I verified each is correct today (see spot-checks), so this is not a wrong number. The risk is
duplication: the same values appear twice in one document, once derived and once typed. If the tune
changed, `--check` would fail through §6, but a plain `--write` would then rewrite the file with the
**stale §8 copy** and go green again — leaving the two halves of the document contradicting each
other. Deriving §8 from the same dicts removes the whole class of drift.

### 4. "not new geometry" is stronger than the measurement — `SIGNATURE_DIFF.md:530`

§8: "The paired `.rbm` files have the same block counts and the same AABBs, **i.e.** the kit is the
same shell recompiled against the signature textures, **not new geometry**."
§9 (limits): "the mesh comparison is header-level (block count, AABB, size); it does not decode
vertex data, so `aabb_equal` means the same bounds, not the same vertices."

§9 is the honest statement; §8's "i.e. … not new geometry" is a conclusion the header comparison
cannot establish (identical block count and AABB are also what a re-sculpted part of the same
material-block structure would produce). The MODLOG limits paragraph says the same as §9, so the
project already knows the constraint — §8 just needs the same hedge ("consistent with a recompile;
vertex data was not compared").

### 5. "no lock-on" is a name-level claim — `SIGNATURE_DIFF.md:539`

§8: "The tune is unguided and unlimited: `missile_turning_speed` 0, **no lock-on**, …". The value
cited supports "unguided" (turn rate 0); "no lock-on" is carried by the autoaim preset's *name*
(`autoaim_vehicle_no_lockon_missile`) and by `missile_loose_lock_distance` 0 in §6 — and
`loose_lock_distance` is the distance at which a held lock is lost, not a lock-acquisition member.
The MODLOG entry is more careful than the doc here ("no lock-on, as the name and the 0 turn rate
say"); the doc should carry the same qualifier. Note the same preset is bound by `w608`, `w611`,
`w615`, `w621` (G2-10), so the name is consistent across the fleet — this is a wording issue, not a
data error.

### 6. The card's "any hinge/door entries" is answered only implicitly — whole doc

The card's `Do:` names "modules added/changed (parts module: `hood_signature`,
`missile_base_signature`, **any hinge/door entries**)". `grep -i hinge SIGNATURE_DIFF.md` → **0
hits**. The negative is deducible from §4 ("Changed fields across the shared parts: `model`,
`model_swap`", `changed_fields = ['model','model_swap']` in the JSON) and it is stated plainly in
the MODLOG done entry ("No hinge, door or entry part is added or changed"), but a reader of the
artefact alone has to infer it. For a card whose whole purpose is to be the B-04/B-05 template,
that sentence belongs in §4 or §8.

### 7. `id:851CAABE` is labelled "(unnamed)" in the table that the same doc names elsewhere — `SIGNATURE_DIFF.md:222`

The §3 changed-properties row reads `` `id:851CAABE` (unnamed) | objectid | 00000000 | ->root/CMissileWeaponBase:… ``,
while line 262 and line 534 of the same document call it `main_weapon`, and G2-11 recovered that
name by Jenkins match the day before. Small, but this is the single most load-bearing property in
the diff (it is *the* weapon slot), so the table should use the same name as the prose.

### 8. Scope note on the deliverable vs the card

The card's `Out:` is `Research/JC3Grab/SIGNATURE_DIFF.md` only; the work also produced
`SIGNATURE_DIFF.json` and `Tools/scripts/jc3sigdiff.py` and the §12 row cites all three. That is a
superset, not a deviation, and it is what makes `--check` possible — but the card's `Done:` ("a
complete list of what JC3 changes to arm this exact chassis") is prose that `--check` cannot test.
What `--check` does test is continuity plus a list of invariants (§9: slot counts, restyle paths,
changed fields, 40/41 instantiation, four fire points paired with muzzles, 84/84 AABB, tune path
exists). "Complete" therefore rests on the diff's layer coverage (container, graph, parts, meshes,
tune, toc, interaction), which the doc does enumerate — acceptable, but it should be said in §9
that completeness is layer-scoped, not proven.

## Spot-checks (value, where verified)

| # | claim | verified where | result |
|---|---|---|---|
| 1 | muzzle effect hash `667364510` → `effects/jc_weapons/muzzle_flash/sportsmuscle_missile_muzzleflash.effc` | recomputed with `rbmhdr.hash_jenkins(path.encode())` and compared with `weapon.muzzles[].effect` in the JSON | **exact match** — the hash→path resolution is real, not asserted |
| 2 | "`vehicle_parts` 1526043305 → 402479768 = `signature/sportsmuscle_vehicle_parts.vmodc`; `palette` cleared; `decals` → `default_decals.vmodc`" | recomputed Jenkins for the three paths and compared with `graph.changed[CCar].props` (`palette.before` −1071400364 = 3926031899 − 2³²; `decals.after` −211122583 = 4083844713 − 2³²) | **match for all three** (unsigned/signed int32 pairing checks out) |
| 3 | four `internal.fire_point.0…3`, type 2, positions (0.182 / 0.058 / −0.063 / −0.19, 1.085, −1.566), each equal to its muzzle's position, all one effect | `weapon.points[]` and `weapon.muzzles[]` in the JSON | **match 4/4**, including the pairing the doc says `--check` asserts |
| 4 | 84 mesh pairs, all equal block count + AABB, sizes −141…+44 B; 5 added meshes with no base counterpart | recomputed from `meshes.pairs` (84, 0 failing) and `meshes.standalone_added` (5) | **match**; the 5 are exactly `w143_rpg_fire_leach_projectile_body_lod1…5` |
| 5 | tune: VFS copy 155 rows / 14,244 B, embedded 148 rows / 12,773 B, 7-field diff = six zero `missile_base_tuning` members + `fire_rate_level_2` 0.12 | `tunes.vfs_wtunec` (rows 155, size 14244, `diff` has exactly those 7 keys) and `tunes['w618_sportsmuscle_missile.wtunec']` | **match**; `PlayerDamage` 1100 / `AIDamage` 500 in 8 m / `PlayerDamageRadiusPercentageMax` 0.15 also match the doc's blast table |
| 6 | parts: 42 defined in both, 19 rows / 23 links changed, civilian instantiates 40 (missing 25, 41), signature 41 (missing 24) | `parts.variant_rows` (42), `parts.changed` (19), `changed_fields` (`model`,`model_swap`), `parts.epe_instantiated` | **match** |
| 7 | graph: 450→464 objects, 2 changed, added subtrees 4 / removed 1, "15 objects added in total", 51 refs / 603 `vec_events` / 1,245 identity fields discarded | `graph.objects`, `graph.changed` (2: `CCar`, `point.stunt.hood`), `graph.added` (2+1+1+11 = 15 objects), `graph.skipped {refs 51, vec_events 603, volatile 1245}` | **match**, including the MODLOG's discard counts |

Also checked and consistent: the toc counts (468→498, added 162 / removed 132, per-kind sums matching
each total), the two root scalars (`id:EA011E72` 0.3→1 float, `id:FFE31EE1` 1→0 int) which the doc
correctly reports as unnamed rather than guessing, and the loose-vs-container `.epe` sizes/hashes
(109,526 vs 109,766 B; 114,962 vs 115,378 B) which justify excluding the loose entry.

## What would make this "sound"

1. Decode the `CForcePulse`'s properties (or label the ftune link "inferred from G2-17").
2. One sentence reconciling 167 container members with 162 toc records.
3. Derive §8's tune/count numbers from the JSON instead of restating them as literals.
4. Copy the §9 hedge into §8's "not new geometry" sentence, and the MODLOG's "as the name says"
   qualifier into §8's "no lock-on".
5. State the hinge/door negative in the doc, and use `main_weapon` for `id:851CAABE` in the changed
   table.

None of these touches a measured value; the wiring this card exists to hand to B-05/B-06 (one
`CMissileWeaponBase`, four paired fire points/muzzles, one aim component, the slot, the tune path)
is decoded and independently confirmed.
