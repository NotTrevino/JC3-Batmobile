# Assumption challenge — P0-1 · Baseline the standing gates

Read-only challenge: no existing file edited, no game launched, nothing written under
`D:/Games`, nothing committed. The only write is this file. Date 2026-10-29.

Card: `GRAB_BACKLOG.md:355-364`. Row: `GRAB_BACKLOG.md:1274`. Result under challenge:
`MODLOG.md:7720-7740` — "All nine gates green, no red gate to explain → P0-1 done, G1 unlocked",
with the dropzone "**== test-091 (all match)**".

**VERDICT summary:** the baseline is a faithful record of what the nine §0.7 commands printed on
2026-10-24 (re-run today: the same nine exit 0, and 7 of the 9 quote numbers that still reproduce).
Four of the assumptions it rests on are WEAK, one is close to BROKEN as evidence:

| # | assumption | verdict |
|---|---|---|
| 1 | The nine §0.7 commands are "the standing gates" | **WEAK** — 81 scripts expose `--check`; one outside §0.7 (`grab_modes.py`) is **red today** (exit 1, `STALE`) |
| 2 | A green gate means the file matches a fresh derivation (not just self-consistency) | **HOLDS** for the nine (code re-derives; `status_audit` compares fresh text) |
| 3 | A gate's pass covers the whole population the gate names | **WEAK** — "57,187 files" is the FX table's own length; "17/17 station sets" is 17 of 234 files |
| 4 | "The dropzone still carries test-091" = the dropzone is in the expected state | **WEAK** — 4 files in the dropzone, 2 are hashed; the other two are a 210 MB sound bank and a 0-byte video stub |
| 5 | The recorded hashes identify the live state | **WEAK** — masked to 18 chars and identical to `install.ps1`'s expected constants, so a copy-paste is indistinguishable from a live read |
| 6 | The table's numbers were produced by those commands | **HOLDS** (point-in-time; drift since is explained later) |
| 7 | "41 members over 156 vehicles" is a fleet statement | **WEAK** — the decoded evidence is 232 entities over **79** chassis; the fleet table has 144–156 vehicles |
| 8 | "Nothing was installed, rolled back or modified" | **WEAK** — an assertion, not a measurement |

---

## 1. "These nine are the standing gates"

**Assumption (silent):** §0.7's list is the complete set, so nine green gates mean nothing on the
desk is stale.

**Test:** count scripts that expose a `--check`, then run the ones outside §0.7 that guard generated
research files.

```
$ grep -rln -- "--check" Tools/scripts/*.py | wc -l
81
$ sed -n '95,110p' GRAB_BACKLOG.md | grep -c "^python"
9
```

Running the closest relatives of the nine:

```
$ python Tools/scripts/grab_modes.py --check ; echo exit=$?
STALE: MODES.json does not match a fresh build (run --write)
exit=1
```

`grab_modes.py --check` is the same kind of gate as `status_audit.py --check` (a generated research
doc must equal a fresh build) and it is **red right now**. The cause is visible in the code: it
compares `MODES.json` byte-for-byte with `build()` (`grab_modes.py:716-726`), and the underlying
inputs grew after 2026-10-24 (`bmak_chain.py` now reports 105 objects / 9,225 bindings against the
86 / 8,595 the baseline recorded).

Other non-§0.7 checks that are green today (so the red one is not a systemic break):
`bmak_damage.py --check` PASS, `grab_bones.py --check` "all record and .npy checks pass",
`t12_parts.py --check` PASS, `review_splits.py --check` PASS, `grab_poses/sockets/anims/weapons/
lights/meshes --check` PASS.

**Verdict: WEAK.** The card says "Run every §0.7 command", so the *record* is honest — but the
sentence it feeds ("no red gate to explain → G1 unlocked") is a claim about the desk, and a gate of
the same family is red today. The baseline did not establish that §0.7 is the full set; nothing
in the repo does.

## 2. "Green means the file on disk equals a fresh derivation"

**Assumption:** a quiet exit 0 means the generated artifact is current, not merely self-consistent.

**Test:** read each gate's check path.

* `status_audit.py:313-320` builds the markdown and compares it to `STATUS.md` — a fresh re-derivation,
  not a stored hash.
* `grab_model.py check` re-runs 15 schema/inventory checks and prints `15/15 … OK: grab output
  matches schema 6 and its own summary`.
* `bmak_chain.py --check` prints `PASS: chain record current (…)`; `t_rows.py check` recomputes the
  category sums (`check ok`); `jc3fx.py check` re-reads every row (`checked 57187 files | problems 0`);
  `jc3hkx.py check --all` re-reads 234 files (`check ok`).

**Verdict: HOLDS** for the nine. It is also why the red gate in §1 is meaningful: the family does
detect staleness when it is run — it just was not run for `MODES.json`.

## 3. "A pass covers the population the gate names"

**Assumption (silent):** "57,187 files" and "17/17 station sets" are population counts.

**Test:**

```
$ wc -l Research/JC3Grab/FX_TABLE.jsonl
57187
```

The FX number is exactly the length of the table the gate iterates (`jc3fx.py:50, 205`), so it says
"every row of our table re-reads", not "every effect file in the game was found". The table is built
from `.effc/.ctunec/.trim` payloads inside `.ee` SARC containers plus standalone entries
(`jc3fx.py:49, 77-89`); those files are not enumerable from `INDEX.jsonl` (its extensions are
`wavc`, `ban`, `hmddsc`, `rbm`, …, no `effc`), so the denominator's completeness rests on the
builder, not on the check.

`jc3hkx.py check --all` prints `station sets 17 (land_global agree 17, disagree 0)`; 17 is the
number of the 234 files that carry a station set, not 17 vehicles out of the fleet.

**Verdict: WEAK** as a coverage claim, **HOLDS** as worded ("checked 57,187 files", "station sets 17").

## 4. "The dropzone still carries test-091" = the dropzone is in the expected state

**Assumption:** two matching hashes characterise the dropzone.

**Test:**

```
$ find "D:/Games/Just Cause 3/dropzone" -type f -printf "%s %p\n"
10737057 …/v0300_car_kensington_sportsmuscle_civilian_01.ee
   50643 …/v0300_car_kensington_sportsmuscle_civilian_01.ee.toc
210781376 …/sound/fmod_banks/vehicles.bank
       0 …/videos/corona_video.bikc
```

`install.ps1:44-50` hashes only the first two. A 210 MB sound bank and a zero-byte video stub are
in the dropzone and are invisible to the Status gate, so "the dropzone still carries test-091" is
true of the entity pair and silent about the rest. (Neither of the extra files is a Batmobile mod
artifact — but the baseline does not say that, and the 0-byte file in particular is not something
"== test-091" would ever flag.)

**Verdict: WEAK.**

## 5. "The recorded hashes identify the live state"

**Assumption:** the logged `.ee`/`.toc` strings are what was live on 2026-10-24.

**Test:** the log records `6AB8275F…FCF8D` / `444ED479…C55AA` (`MODLOG.md:7737-7738`). Those are
exactly the first 8 and last 5 characters of `install.ps1`'s own expectations
(`install.ps1:10-11`), and the live Status call prints those same full values today. There is no way
to tell a live read from a paste of the script's constants, which is the one thing the card's
"record the live … hashes" was for.

**Verdict: WEAK** (as evidence; the present state does match).

## 6. "The table's numbers were produced by those commands"

**Assumption:** each row is a command's one-line result.

**Test:** re-ran all nine. Reproduced exactly today: `grab_model` 380 offset-only / 101 light rigs /
15-15 / schema 6; `jc3index` 81,952 rows / 78,907 paths / 1 unnamed / DLC 20,682-20,682;
`jc3hkx` 233 entities / 18,865 hulls / 6,382 compounds / 17-17; `jc3fx` 57,187 / 0; `t3_fleet`
41 members over 156 vehicles; `status_audit` "STATUS.md is current". Changed since: `bmak_chain`
86→105 objects, 8,595→9,225 bindings; `t_rows` 105→198 rows. Both old values are corroborated by the
same-day entry `MODLOG.md:7623` (86 objects / 8,595 bindings) and later drift is recorded at
`MODLOG.md:14117` (105 / 9,225).

**Verdict: HOLDS** as a point-in-time record.

## 7. "41 members over 156 vehicles" speaks about the fleet

**Assumption (silent):** the fleet numbers and the decoded evidence describe the same population.

**Test:** the census/decoded set is 232 `.ee` files over **79** distinct chassis:

```
$ python - <<'PY'
import glob,os,re
fs=[os.path.basename(p) for p in glob.glob('E:/Modding/_JC3grab/detail/*.ee.json')]
ch={re.match(r'(v\d{4}_[a-z]+_[a-z0-9]+)',f).group(1) for f in fs}
print(len(fs), len(ch))
PY
232 79
```

`t3_fleet --check` prints `41 members over 156 vehicles`, and `Research/JC3Grab/FLEET.md:4-5` says
"**145** vehicles have a `land_global` station set; **144** … can host the Batmobile". So "156",
"145", "144" and "79" are four different denominators in the same project. A gate that prints 156
next to a decoded set of 79 is not wrong — it is answering a different question — but any claim of
the form "every vehicle …" that leans on the census (or the reverse) is a fleet-wide claim tested on
about half the fleet.

**Verdict: WEAK.**

## 8. "Nothing was installed, rolled back or modified"

**Assumption:** the sentence is evidence.

**Test:** the log asserts it (`MODLOG.md:7722-7723`) and the present dropzone matches test-091, which
is consistent with the assertion but does not measure it: Status is a read, and there is no
before/after record for the other two files in the dropzone (§4), nor for the build directory.

**Verdict: WEAK** (an assertion, not a measurement — acceptable for a read-only Status call, but it
should not be read as proof that the dropzone was untouched).
