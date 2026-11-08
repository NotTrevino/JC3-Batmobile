# Stale numbers in STATUS.md — what `status_audit.py --check` says, and what it cannot see

STATUS: done. `python Tools/scripts/status_audit.py --check` reports **no complaint** (exit 0,
`STATUS.md is current`). The two G1/G2 count rows I recounted — `grab.json` objects and
`INDEX.json` named entries — are **correct and current**. Three other numbers in STATUS.md are
stale or have no source behind them, and the reason all of them survive `--check` is the same:
`--check` compares the document byte-for-byte with `status_audit.py`'s own `markdown()`, and those
numbers are **string literals inside that function**, not values read from a file.

Nothing was written to `STATUS.md`. The only files this task created/edited are this report and an
appended MODLOG section.

## 1. What `--check` complains about: nothing

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/status_audit.py --check
STATUS.md is current
check_exit=0
```

That is expected once you look at what the check does (`Tools/scripts/status_audit.py`, `main()`):

```python
d = build()                      # g1(): grab.json + OFFSETS.json
text = markdown(d)               #       g2(): INDEX.json + GEOMETRY.md
if a.check:                      #       t_rows(): T_ROWS.jsonl + T6_HUD_CAMERA.md
    if not os.path.exists(OUT) or open(OUT, encoding="utf-8").read() != text:
        print("STATUS.md is stale; run --write"); return 1
    print("STATUS.md is current"); return 0
```

**`GRAB_BACKLOG.md` §12 is not an input.** The several reports today that added tracker rows
(`V-05-driving` among them) cannot make this check fail, and cannot make it pass either: the audit
never reads the tracker. A tracker row and a STATUS count are two separate ledgers that nothing
reconciles.

The second, larger consequence: because `markdown()` contains hardcoded sentences next to derived
ones, `--check` proves only "STATUS.md == markdown(build())". It cannot prove any literal in
`markdown()` is still true. A number that ages in the prose stays green forever.

## 2. Two rows recounted from their named source files

### 2.1 G1 — "objects decoded | 19,203 / 20,128 | `grab.json`" (STATUS.md:12)

Recounted four ways from `Research/BatmobileGrab/grab.json`, none of them the field pair the
generator reads:

```
$ python - <<'EOF'
import json; g=json.load(open("Research/BatmobileGrab/grab.json",encoding="utf-8"))
print("exports", g["exports"], "readable", g["readable"], "native", g["native"],
      "readable+native", g["readable"]+g["native"])
print("per_package sum", sum(g["per_package"].values()), "packages", len(g["per_package"]))
print("classes sum", sum(v for k,v in g["classes"].items()))
EOF
exports 20128 readable 19203 native 925 readable+native 20128
per_package sum 20128 packages 15
classes sum 20128
```

**Verdict: current.** 19,203 decoded of 20,128 total agrees with `exports`, with
`readable + native`, with the sum over the 15 packages and with the sum over all classes. Nothing
in that row is stale; `grab.json` (schema 6, mtime 2026-10-25) still describes the 15 BmAK packages.

### 2.2 G2 — "archive entries named | 81,952 / 81,953 | `INDEX.json`" (STATUS.md:13)

```
$ python - <<'EOF'
import json; i=json.load(open("Research/JC3Grab/INDEX.json",encoding="utf-8"))
pa=i["per_archive"]
print("tab_entries", i["tab_entries"], "named_rows", i["named_rows"], "unnamed", i["unnamed_entries"])
print("per_archive entries sum", sum(a["entries"] for a in pa.values()),
      "named sum", sum(a["named"] for a in pa.values()), "archives", len(pa), i["archives"])
print("named_by_source", i["named_by_source"], "sum", sum(i["named_by_source"].values()))
EOF
tab_entries 81953 named_rows 81952 unnamed 1
per_archive entries sum 81953 named sum 81952 archives 88 88
named_by_source {'derived-names': 90, 'gibbed-filelist': 55811, 'jcmr-dictionary': 26051} sum 81952
```

**Verdict: current.** 81,952 / 81,953 is reproduced by the per-archive table over all 88 archives
and by the name-source split (90 + 55,811 + 26,051 = 81,952); exactly one entry is unnamed, which
is the `.wavc` the same page names.

## 3. The numbers that ARE stale, and why

### 3.1 "the in-scope rows (113 today…)" contradicts the table above it (STATUS.md:123)

| place | number |
|---|---|
| table, `rows resolved from evidence (in scope)` | 126 / **180** |
| table, `rows out` + `rows superseded` separate | 43 + 8 |
| closing paragraph | "the denominator is now the in-scope rows (**113 today**…)" |

In scope is 180 (`126 resolved + 1 assumed + 17 blocked`, with 43 out and 8 superseded excluded);
the prose says 113. **Stale by 67 rows.** Why: `"the in-scope rows (113 today; …)"` is a literal in
`markdown()` — it was true when the denominator was 113 and did not move when 40 `next` rows and the
re-opened T-10 rows entered the ledger. `--check` cannot catch it because the literal is on both
sides of the comparison.

### 3.2 "test-090 … (the live pair)" is stale about which build is live (STATUS.md:47, 103)

```
$ grep -n "test-090\|live pair" STATUS.md
47:Batch B4's 2 value(s) over 1 row(s) in **test-090** are read back through the installed `.toc` (the live pair). All file-level, not behaviour.
103:- 40 resolved rows are queued: the live pair carries **test-090** (this batch 2 values / 1 rows; …)
```

`GRAB_BACKLOG.md` §3 states the live dropzone carries **test-091**, and `Builds/` holds test-091
(`ls Builds` → … test-089, test-090, test-091). Nowhere in STATUS.md does test-091 appear.

Why: `b2()` discovers the newest applied record by trying `t5e_applied.json → t5d → t5c` and the
image path inside it:

```
$ ls Working/Translation/t5*_applied.json
t5c_applied.json  (4 applied, 3 rows, Builds/test-088)
t5d_applied.json  (4 applied, 3 rows, Builds/test-089)
t5e_applied.json  (2 applied, 1 row,  Builds/test-090)
t5f_applied.json  absent
```

Batch F (camera, test-091) left no `t5f_applied.json`, and `b2()` has no glob for the newest tag,
so the audit's newest visible batch is test-090. The paragraph is right about test-090's 2 values
and wrong about it being the live pair. `--check` is green because the generator and the document
agree on the stale tag.

### 3.3 "vehicle modules decoded | 6,045 / 6,045 | `ENTITIES.md`" — right number, source it cannot come from (STATUS.md:14)

The generator hardcodes the whole row — it is not in `g1()`/`g2()`, and it reads no file:

```python
f"| | vehicle modules decoded | 6,045 / 6,045 | 100% | `ENTITIES.md` |",
```

`Research/JC3Grab/ENTITIES.md` does not contain the number at all — a case-insensitive search for
"module" in that file returns **zero** lines, and its headings are Class inventory / Parts / Lights /
Meshes / `.physicsc`. So the cited source cannot supply the count.

Recount from the decoded entities (the files `ENTITIES.md` was built from):

```
$ python - <<'EOF'
import json, glob, os
fs=sorted(glob.glob("E:/Modding/_shared/gamedata/JC3grab/entities/*.ee.json"))
tot=sum(len(json.load(open(f,encoding="utf-8"))["modules"]) for f in fs)
print("files:", len(fs), "sum modules:", tot, "per-file min/max:",
      min(len(json.load(open(f,encoding="utf-8"))["modules"]) for f in fs),
      max(len(json.load(open(f,encoding="utf-8"))["modules"]) for f in fs))
EOF
files: 232 sum modules: 6045 per-file min/max: 12 49
```

**6,045 is correct** (232 entities, 12-49 modules each) — but the row is not stale in its value, it
is stale in its provenance: a typed literal, in a column that names a document which never states
it, and the decoded inputs live at `E:/Modding/_shared/gamedata/JC3grab/entities/`, not the
`E:\Modding\JustCause3\_grab\` path GRAB_BACKLOG §0.6 gives:

```
$ ls -d "E:/Modding/JustCause3/_grab" "E:/Modding/JustCause3/_grab/entities" "E:/Modding/_shared/gamedata/JC3grab/entities"
ls: cannot access 'E:/Modding/JustCause3/_grab': No such file or directory
ls: cannot access 'E:/Modding/JustCause3/_grab/entities': No such file or directory
E:/Modding/_shared/gamedata/JC3grab/entities
```

### 3.4 Other literals in the same page (not recounted here — flagged, not claimed stale)

These are also typed into `markdown()` rather than derived, so `--check` cannot defend them; I did
not recount them and am not calling them wrong:

* "768 of them 2-byte `Package` stubs" (the `925` next to it *is* derived, from `grab.json`).
* "232 graphs / 91,157 objects" in the damage-immunity bullet.
* "`HUD_INTERFACES.json` holds 252 `UC_*` setters" and "15 `RHudModule*` classes to 19 carved movies".
* "10 BmAK audio banks are absent".
* "4 have partial manoeuvre measurements (QA-1)".
* the "Built and measured" paragraph's "test-085 / 35 values / 16 rows" half (the `35` and `16` are
  derived from the ledger; the build tag and the "B3's 4 values sit in test-089" clause are typed).

## 4. Why the tracker rows added today changed nothing

`status_audit.py` builds its T section from `T_ROWS.jsonl` dispositions and `T6_HUD_CAMERA.md` rows
only. §12 tracker rows are not read, so the `V-05-driving` row (and every other row added today)
leaves STATUS.md's T totals at 126/180 resolved, 1 assumed, 17 blocked — those still match the
ledger, and `--check` stays green. What a tracker row can do is *contradict* STATUS.md without
either file being regenerated: a `done` tracker row for a card whose values are not in the ledger
shows up nowhere in the audit.

## 5. What would close each gap (not done here — no edits to STATUS.md)

| gap | fix |
|---|---|
| 113 vs 180 | delete the parenthetical and generate it: `f"(the in-scope rows ({td['in_scope']} today; …))"` |
| test-090 as live | make `b2()` glob `t5*_applied.json` and pick the highest `Builds/test-0NN`, or write `t5f_applied.json` for Batch F |
| 6,045 hardcoded | move the modules count into `g2()` (a sum over the decoded `*.ee.json`, as recounted above) and change the source column to that path |
| literals in 3.4 | derive each, or move them into a bullet that names its file, so `--check` fails when the file moves |
| tracker vs audit | a `--check` that also asserts every §12 row marked `done` has its evidence path on disk would catch the drift the current check is blind to |

## 6. Files and commands

* Written: this report; one appended MODLOG section. **STATUS.md not edited** (its mtime is
  unchanged, and `--check` still says `STATUS.md is current`).
* Commands: the `status_audit.py --check` run, two `grep`s, three inline `python -` recounts (G1
  sums, G2 sums, module sum), and the `ls`/`ls -d` path checks — all quoted above with their output.
* Nothing was built, installed, launched or attached to; no game file was written.
