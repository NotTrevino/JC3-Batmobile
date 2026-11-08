# Claude dependency handover — what breaks on 2026-11-09, and the manual replacement

STATUS: **done, report only** (+ `NEXT_TASKS.md` at the repo root). No skill file, no `server.py`, no queue brief
and no ledger row was edited. Read: `C:/Users/User/.claude/skills/freebuff/scripts/gui/server.py` (lines 317–679),
`C:/Users/User/.claude/skills/freebuff/SKILL.md` (lines 3–181), `ROADMAP.md` §§1–10,
`Working/Roadmap/*.md` (8 files, card lines read), `tmp/freebuff/queue/` (53 briefs listed),
`tmp/freebuff/INSTRUCTIONS.md`.

The short version: **only one step truly needs Claude — writing the briefs — and the honest replacement is the
operator writing short briefs from `NEXT_TASKS.md`.** Everything else in the emergency path is either Claude
*deciding* things a human or a Freebuff agent can decide, or a local monitor that never calls a model.

---

## (a) Which steps need Claude — with file and line

### A1. The pre-reset brief generator (the one that actually stalls lanes)

`scripts/gui/server.py`:

| line | what it does |
|---|---|
| `317–322` | the design comment: in the last `EMERG_MIN` minutes before the daily reset, if hours are free and a slot is open, start sessions by itself; *"A project with no briefs gets emergency-need-tasks.txt and, once per 45 min, `claude -p` is asked to write briefs into its queue."* |
| `325` | `EMERG_PRIORITY = {'E:/Modding/JustCause3/JC3-Batmobile'}` — this project is the emergency priority |
| `346` | `next_reset()` — daily hours reset (local midnight, 05:00Z in CDT) |
| `464` | `def emergency_loop():` — the loop itself |
| `509` | writes `emergency-need-tasks.txt` when the queue is empty |
| `514–518` | `subprocess.Popen(['claude', '--model', 'haiku', '-p', 'Freebuff emergency: %d daily hours expire in %d min and the queue at %s is empty. …'], … stdout=open(B/'emergency-claude.out','ab'))` — **the hard dependency**: briefs are invented by Claude Haiku at the last minute |
| `533` | writes `emergency-start.txt` (the audit trail of auto-starts) |
| `675–679` | `threading.Thread(target=watchdog.loop, daemon=True).start()` — *"zero-token local watchdog (runs only while emergency mode is on)"*; it does **not** call a model |

`SKILL.md` lines `44–46` explain why this matters: the keeper starts a lane only with **≥ `MIN_BRIEFS` (default 4)
hand-written briefs queued**, and logs `ALARM briefs` when the queue is short. Line `51–52`: *"**Every task carries
a hand-written brief, marked `BRIEF: hand-written <date>`** … The driver refuses a task without that header
(`NEEDS BRIEF` -> `low/needs-brief`)."* So an empty queue is not just slow — the driver **refuses** tasks without a
brief, and a lane that runs dry idles until a human or Claude writes one.

### A2. The autonomous emergency driver

| line | what it does |
|---|---|
| `380–384` | the global switch comment: emergency mode ON *"launches an autonomous `claude --dangerously-skip-permissions` terminal to monitor lanes, write distinct hand-written briefs and keep backlogs fed. Prompt: emergency-claude-prompt.md."* |
| `400–407` | `subprocess.Popen(['cmd','/c','start','Freebuff emergency Claude','cmd','/k','claude','--dangerously-skip-permissions', msg], …)` — a visible console that runs unsupervised |
| `459` | `emergency-ended.txt` — the mode ends at 0 daily hours |

### A3. The brief-writing policy that constrains any replacement

`SKILL.md`:

| line | rule |
|---|---|
| `51–54` | one hand-written brief per task, written *for that task*, never from a template; shared rules live in `<project>/tmp/freebuff/rules.txt` |
| `60–61` | templated fillers are **off** by default; only a project that opts in with `restock.json {"templated": true}` gets them |
| `65–74` | the Freebuff-policy incident: *"the same job again and again"* was refused; what was accepted is one brief per task; *"Never add noise to make repeated work look different"* |
| `121–124` | the queue file format: `NNN-slug.txt` with `DONE: <absolute path>` |
| `106–107` | never start a session flippantly: *"only when the user asked, or standing instructions say to keep sessions busy"* |

### A4. Reviews and report triage

Reviews are not code; they are the *judgement* step. The two wave reviews in `tmp/freebuff/reports/`
(`review-translation-wave.md`, `review-build-wave.md`) and the two written this session
(`review-v2-apply-wave.md`, `hud-gfx-ffdec-roundtrip.md`) are exactly the shape a review brief produces: read
everything, re-run the owning scripts, compare claims with bytes, list findings. A brief can specify that. What a
brief cannot do is decide *which* review is worth running — that is the operator's menu choice in `NEXT_TASKS.md`.

---

## (b) The replacement for each step, inside Freebuff policy

The policy line that decides everything: **briefs stay distinct and hand-written; templated or looped briefs are
forbidden** (`SKILL.md:51–74`). So no replacement may "generate" briefs. The replacement is a *menu*, not a
generator.

| step | replacement | why it complies |
|---|---|---|
| **A1** pre-reset brief generator (`server.py:509–518`) | **The operator writes 1–4 briefs from `NEXT_TASKS.md`** (each entry is already a task with inputs and a done-check, so a brief is a two-minute copy-and-tighten). When the queue is empty, accept the idle: `emergency-need-tasks.txt` is the prompt to a human, not to a model. Do **not** point `claude -p` at `NEXT_TASKS.md` as a "write briefs from this file" job — that is exactly the templated series the policy refused | each brief is written for one task, by a person, and can differ every time; the menu supplies the task, not the prose |
| **A2** autonomous `--dangerously-skip-permissions` driver (`server.py:400–407`) | **One Freebuff session per brief**, started by the operator (or by the GUI's start button, which is an explicit act). No console left running that writes its own work | `SKILL.md:106–107`: a session starts only when the user asked or standing instructions say so; an autonomous brief-writer is precisely what the policy incident was about |
| **A3** brief prose | **`NEXT_TASKS.md` holds the inputs and the done-check only.** The operator adds the `BRIEF: hand-written 2026-11-09` line, one sentence of intent and the exact report path. Two different tasks never share wording, even if they share a shape | keeps the header the driver requires (`SKILL.md:51`) without a template; the marker is a claim the human makes |
| **A4** reviews | **Hand-written review briefs** pointed at a named set of reports and at the scripts that arbitrate (e.g. "re-run `t_rows.py check`, `status_audit.py --check`, `t23_closeout.py --check`; every number in the reports re-derived; findings with file:line"). `review-v2-apply-wave.md` is the worked example, and it found a real red pin | a review is one distinct task per wave; the arbiter is a script, so the brief can be short and still checkable |
| **watchdog** (`server.py:675–679`) | **Keep it.** Zero tokens, no model, only logs. Nothing to replace | no policy surface |
| **refused-task revision** | **The operator writes a genuinely different brief** (or moves the task to `low/`). Never resend the same task under new words | `SKILL.md:39`: resending/rewording a refused task is forbidden; distinct work only |

**What the operator needs to do in the two-minute loop:** open `NEXT_TASKS.md` → take the first task whose
dependencies are done → paste its five lines into `tmp/freebuff/queue/92NN-<slug>.txt` → add
`BRIEF: hand-written 2026-11-09` and the `DONE:` path → start one lane. Nothing else in the pipeline changes.

**Degraded mode, stated plainly:** without a brief writer, lanes idle between operator sessions (the 11 hours on
2026-11-08 are the measured cost). The menu cannot remove that idle time; it removes the *authoring* delay once the
operator is at the keyboard. A queue of 4 briefs is about one hour of one lane (`SKILL.md:44–46`).

---

## (c) The menu: `NEXT_TASKS.md`

Written at `E:/Modding/JustCause3/JC3-Batmobile/NEXT_TASKS.md`: **32 tasks in dependency order**, none covered by a queued
brief. Coverage was checked against all 53 files in `tmp/freebuff/queue/` (the 91xx RC5 chain, 798x hooks, 8600/8606/
8607/8608, 8906, 7940/7942/7943, 7981–7987). Every entry gives: the card id, the task in one line, its inputs (files
that exist today), and a done-check that a script or a byte count can settle — so "done" is not an opinion.

The order is by what unblocks what:

1. **Record hygiene** (`NEW-WPN-46`, `NEW-AUD-26`, `NEW-APP-4`, `NEW-ARM-03`) — four documents currently disagree
   with the ledger; fixing them first stops a small model from "fixing" the wrong side.
2. **Decodes that gate RC5 builds** (`NEW-WLD-01`, `NEW-WLD-03`, `NEW-WPN-26`, `NEW-WPN-27`, `NEW-WPN-8`,
   `NEW-HDL-5/6/7/8`, `NEW-AUD-1/2/3`, `NEW-ARM-05/06/07/12`).
3. **Appearance desk work** (`NEW-APP-5/7/8/10/11/13/17/29/30/31`) — budget and slot questions the RC5 branches
   will hit at 9190.
4. **Parts, controls, keymap** (`NEW-MOD-13`, `NEW-MOD-19`) — these two are in the 32 because the controls are
   absent from the ledger and the keymap writer is the last step of a card that already has a plan.

The file ends with a **second batch** (`NEW-MOD-15`, `NEW-WLD-07/08/20`, `NEW-MOD-23`, `NEW-WPN-15/16`, `NEW-APP-40`,
`NEW-WPN-24`) — named but not written up, so the operator queues them only after the 32 are placed.

Two things the menu deliberately does **not** contain: any task that needs the test ban lifted (those are Q-1…Q-4
and 9x9x verify briefs already queued), and any task whose only input is a game folder that must be launched.

---

## What I did not do

- No edit to `server.py`, `SKILL.md`, `EMERGENCY_MODE_REPORT.md`, the keeper or any queue brief.
- No brief written for a future task: `NEXT_TASKS.md` is a menu with inputs and done-checks, not prose to paste
  blindly, and it carries no `BRIEF:` header.
- No game started, no install script run.

## Revert

Delete `NEXT_TASKS.md` and this report. Nothing else was written.
