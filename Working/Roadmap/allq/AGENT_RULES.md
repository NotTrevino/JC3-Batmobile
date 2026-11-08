# Queue ALL remaining work for one landmark — rules for the brief-writing agent

The operator wants every remaining task of the JC3 Batmobile project (E:/Modding/JC3-Batmobile) queued now, with all dependencies, so free model lanes (DeepSeek, weaker than you) can execute it without anyone writing more briefs. You write the briefs for ONE landmark. A merge script numbers them, resolves dependencies and moves them into the queue. You never write into tmp/freebuff/queue yourself and never edit project files.

## Inputs
- Your landmark map: E:/Modding/JC3-Batmobile/Working/Roadmap/<map>.md (task table: id, task, stage, status, blocked by, blocks, size, evidence; plus blockers, operator questions, risks).
- Existing briefs (queued, held, done) with their report paths: C:/Users/User/AppData/Local/Temp/claude/85a72aa72e1c87a6/2cba09a9-6c5e-4f2a-a2a9-f93cd4ff0f7c/scratchpad/allq/brief_index.md (full JSON: brief_index.json). Read the queued 79xx/91xx/86xx briefs relevant to your landmark (tmp/freebuff/queue/*.txt) before writing, so you do not duplicate them.
- Overall plan and operator facts: E:/Modding/JC3-Batmobile/ROADMAP.md (sections 3-10, especially 7 = operator gameplay facts that override older records), OPERATOR_PRIORITIES.md, STAGES.md (closest-system rule: "JC3 has no system" is never an answer; name the closest system and the gap; the build closes it).
- Key new facts (2026-11-08): native hooks are permitted. The hook base is jc3-console-thingy v1.1 (E:/Modding/_tools/jc3-console-thingy), whose addresses match the operator's exe. The hook chain is already queued: 7974 design, 7981 scaffold, 7982 telemetry, 7983 gamepad, 7984 mode swap, 7985 HUD overlay, 7986 water/flip/regen, 7987 handling switch, 7967 safety. JC3MP is unavailable (no Steam ownership). The operator plays on an Xbox gamepad. In-game tests are agent-piloted under operator supervision, and run only once the operator approves them.

## What to produce
One brief per OPEN task (status todo/partial/queued-but-not-covered/blocked) in your map that no existing brief already covers, from where it stands now through BUILD, VERIFY, in-game TEST and RELEASE. Split L-size tasks into steps of at most about 45 minutes of agent work each. Also add:
- a review brief after each group of about 8 build briefs. It re-reads their reports and rewrites the later briefs' text if facts changed (it may edit queue files that have not started yet);
- for every BUILD output, a VERIFY brief (offline read-back or --check);
- for every feature, the in-game TEST brief(s) (flag ingame: true). Each states the pilot cards to use (Working/Q/PILOT/), the one observation, the pass rule, and the fix-card route on fail.
A blocked task still gets its brief: depend on whatever unblocks it (a probe, the hook, an earlier report). If the unblocker itself is missing, write that brief too.

## Output: a JSON file, exactly this shape
Write C:/Users/User/AppData/Local/Temp/claude/85a72aa72e1c87a6/2cba09a9-6c5e-4f2a-a2a9-f93cd4ff0f7c/scratchpad/allq/staging/<landmark>.json:
```
{"landmark": "<L-id from Working/Roadmap/landmarks.json>", "briefs": [
  {"key": "<landmark-short>-<nn>", "slug": "kebab-case-title-max-6-words", "est": 15-60, "ingame": false,
   "covers": ["<map task ids>"],
   "deps": ["<existing brief number e.g. 9120 or 7982>", "<key of another brief in ANY landmark's staging file, e.g. hud-07>", "APPROVED_Q"],
   "body": "<the brief text>"}
]}
```
- `deps` lists only what must FINISH first: existing brief numbers (the merge script turns them into report paths), keys of new briefs (yours, or another landmark's key if you know it from the cross-landmark table below), or "APPROVED_Q" for in-game work. No cycles.
- Cross-landmark keys you may depend on (other agents use these exact keys for their landmark's FIRST brief of each kind): `app-01`, `wpn-01`, `hdl-01`, `aud-01`, `mod-01`, `hud-01`, `arm-01`, `int-01`. Prefer depending on existing brief numbers (the 79xx hook chain, 91xx RC5 builds, 9190 merge, 9193 VX, 8606 probes) — they are stable.
- `body`: a self-contained instruction for a weaker model, 90-220 words, YOUR OWN WORDING for each brief (a machine-wide guard rejects any body that shares >= 50% of its word trigrams with another brief: do not reuse sentences, openings or closing lines between briefs; never paste rules). Name exact input files, the values or questions, the output files, and the done-check (a command, a count, or a comparison). Cite operator facts where they apply. Read-only unless the task builds; builds go to new private trees under E:/Modding/JC3-Batmobile/Builds/ only, never the game folder. End every body with: "Shared rules: E:/Modding/JC3-Batmobile/tmp/freebuff/INSTRUCTIONS.md." (the merge script exempts that line from the similarity check).
- Never assume a JC3/BmAK value. If the map says UNKNOWN, the brief's job is to settle it, or to depend on the brief that does.

## Done
Validate your JSON: it parses, keys are unique, every dep is an existing number, a key in your file, a key from the cross-landmark list, or "APPROVED_Q". Then return a 6-line summary: brief count, in-game count, task ids covered, task ids you deliberately did not cover (with the existing brief that covers each), and anything that looked impossible.
