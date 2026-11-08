# RECORD — a take with the game's own audio, proven non-silent

> change 2026-11-07 (review-pilot-cards): step 4's peak reader assumes float32 samples and had no
> branch for any other encoding, so a wrong-format take would have produced a confident number. It
> now refuses above 1.0 and names the assumption. `--offset 0.25` is labelled a pilot threshold.

GOAL: a 20 s clip of the game window with JC3's own audio inside it, and a measured peak that
proves the audio track is not silence.

Why the audio step exists: QA-1's take was recorded with `--no-audio`, and JC3's only engine-rpm
channel is audio, so the take could not answer the gearbox question (catalogue A-1). A silent
take is a failed take, not a smaller one.

PRE-CONDITIONS
| # | check | command | must show |
|---|---|---|---|
| P1 | LAUNCH card PASS | `Working/Q/PILOT/LAUNCH.md` RESULT line | `RESULT: PASS`, pid recorded |
| P2 | the process is the recorded one | `um win ps \| grep -i justcause3` | the same `<pid>` |
| P3 | JC3 is not muted in the Windows volume mixer | Volume mixer, JC3 row | not the muted icon (a per-app mute yields exact silence even with loopback) |

STEPS

### 1. Make the capture directory
    DO   mkdir -p tmp/freebuff/caps
    SEE  exit 0
    IF NOT  STOP — repo not writable

### 2. Record 20 seconds WITH audio
    DO   um win record --exe JustCause3.exe --pid <pid> --out tmp/freebuff/caps/take1 --seconds 20
    SEE  exit 0, and `take1.mkv`, `take1.audio.raw`, `take1.json` all exist
    IF NOT  no `.audio.raw` -> STOP; never re-run with `--no-audio`

### 3. Check the three files are non-empty
    DO   ls -l tmp/freebuff/caps/take1.mkv tmp/freebuff/caps/take1.audio.raw tmp/freebuff/caps/take1.json
    SEE  three lines, none with size 0
    IF NOT  a zero-byte file -> STOP, note which one

### 4. Measure the audio peak
    DO   python -c "import array;a=array.array('f');a.frombytes(open('tmp/freebuff/caps/take1.audio.raw','rb').read());print(max(abs(v) for v in a))"
    SEE  a number greater than 0.001 and not above 1.0 — write it on the RESULT line
    IF NOT  0.0 or below 0.001 -> unmute JC3 in the volume mixer, re-run steps 2-4 once; a second silent take -> STOP (the take is unusable)
    IF NOT  a peak above 1.0 -> the `.audio.raw` is not float32, which the reader assumes: STOP and quote the first 16 bytes as hex; do not interpret that number

### 5. Mux the take
    DO   um video mux tmp/freebuff/caps/take1.mkv tmp/freebuff/caps/take1.audio.raw tmp/freebuff/caps/take1.json tmp/freebuff/caps/take1.mp4 --offset 0.25
    SEE  exit 0 and `tmp/freebuff/caps/take1.mp4` exists, larger than 0 bytes
    IF NOT  re-run once without `--offset`; still failing -> STOP and keep the `.mkv` (it survives a kill)

### 6. Confirm the muxed file size
    DO   ls -l tmp/freebuff/caps/take1.mp4
    SEE  one line, size larger than 0
    IF NOT  STOP

### 7. Confirm the game is still the same process
    DO   um win ps | grep -i justcause3
    SEE  the same pid as P2
    IF NOT  STOP — the take may have ended with the game (catalogue L-1); record the RESULT as STOP

RESULT
    RESULT: PASS — 20 s take with non-silent audio — pid=<pid> — peak=<n> — tmp/freebuff/caps/take1.mp4
    RESULT: STOP — step <n> — <the SEE that failed, quoted> — <artifacts so far>

TRAPS: A-1 (`--no-audio` banned; audio is a data channel here, not decoration), per-app mute =
exact silence (detect by peak, never by ear), never stop the encoder from the game's main thread
(the tool owns that), write `.mkv` (survives a kill), NVENC H.264 tops out at 4096 px wide (crop
with `--crop` rather than shrinking the window). `--offset 0.25` is the encoder start-up offset, a **pilot threshold** measured once per machine (not a
value any repo file decodes); if the muxed audio is early or late, the offset is re-measured, never guessed.
