"""Project completion estimate, recomputed from live progress (operator request 2026-11-08: shown in the Freebuff GUI).

Model (stated so it can be challenged):
  * game_scale (landmarks.json) shrinks in-game days once unattended agent piloting is measured (Q-0 lessons, brief 8608).
  * Each landmark in Working/Roadmap/landmarks.json has desk_days (agent work at ref_briefs_per_day) and game_days
    (operator-supervised in-game sessions + fix loops), deps, and the queue briefs that measure its progress.
  * Desk progress = share of the landmark's `briefs` found in tmp/freebuff/done/; game progress = share of `q_briefs`
    done (0 when none are listed). done:true zeroes the landmark.
  * Desk time scales by velocity v = ref_rate / measured rate (briefs finished over the last 3 days), clamped 0.6..2.0.
  * Finish = max(critical path through deps, today + L0 + game_overlap * total remaining game days) because one operator
    can only run one game at a time. likely = finish * risk_likely, high = finish * risk_high.
  * Nothing finishing means the remaining durations stay the same while today moves on, so the date slips by itself.
Writes tmp/freebuff/eta.json. Usage: python Tools/scripts/project_eta.py [--print]
Revert: delete this file, Working/Roadmap/landmarks.json and tmp/freebuff/eta.json.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LM = ROOT / 'Working' / 'Roadmap' / 'landmarks.json'
DONE = ROOT / 'tmp' / 'freebuff' / 'done'
OUT = ROOT / 'tmp' / 'freebuff' / 'eta.json'


def done_ids():
    ids, recent = set(), 0
    cutoff = dt.datetime.now().timestamp() - 3 * 86400
    if DONE.is_dir():
        for f in DONE.iterdir():
            if f.suffix != '.txt':
                continue
            ids.add(f.name.split('-')[0])
            if f.stat().st_mtime >= cutoff:
                recent += 1
    return ids, recent / 3.0


def main():
    cfg = json.loads(LM.read_text(encoding='utf-8'))
    ids, rate = done_ids()
    ref = cfg.get('ref_briefs_per_day', 100)
    v = min(2.0, max(0.6, ref / rate)) if rate > 0 else 2.0
    rem, rows = {}, []
    for L in cfg['landmarks']:
        b, q = L.get('briefs', []), L.get('q_briefs', [])
        dp = (sum(x in ids for x in b) / len(b)) if b else 0.0
        gp = (sum(x in ids for x in q) / len(q)) if q else 0.0
        if L.get('done'):
            dp = gp = 1.0
        desk = L['desk_days'] * (1 - dp) * v
        game = L['game_days'] * (1 - gp) * cfg.get('game_scale', 1.0)   # <1 once unattended piloting is proven (brief 8608 sets it)
        rem[L['id']] = (desk, game)
        rows.append(dict(id=L['id'], name=L['name'], desk_progress=round(dp, 2), game_progress=round(gp, 2),
                         desk_days_left=round(desk, 1), game_days_left=round(game, 1)))
    end = {}
    by = {L['id']: L for L in cfg['landmarks']}

    def fin(i):
        if i not in end:
            start = max([fin(d) for d in by[i]['deps']] or [0.0])
            end[i] = start + sum(rem[i])
        return end[i]
    crit = max(fin(i) for i in by)
    game_total = sum(g for _, g in rem.values())
    cap = sum(rem['L0']) + cfg.get('game_overlap', 0.7) * game_total if 'L0' in rem else game_total
    base = max(crit, cap)
    today = dt.date.today()
    likely = base * cfg.get('risk_likely', 1.2)
    high = base * cfg.get('risk_high', 1.5)
    res = dict(updated=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
               days=round(likely), days_low=round(base), days_high=round(high),
               date=str(today + dt.timedelta(days=round(likely))),
               date_low=str(today + dt.timedelta(days=round(base))),
               date_high=str(today + dt.timedelta(days=round(high))),
               briefs_per_day_3d=round(rate, 1), velocity_factor=round(v, 2),
               bound='critical path' if crit >= cap else 'in-game capacity', game_scale=cfg.get('game_scale', 1.0),
               landmarks=rows)
    OUT.write_text(json.dumps(res, indent=1), encoding='utf-8')
    if '--print' in sys.argv:
        print('~%d days (%s; range %s..%s) | %.0f briefs/day over 3 d, v=%.2f, bound: %s' % (
            res['days'], res['date'], res['date_low'], res['date_high'], rate, v, res['bound']))
        for r in rows:
            print('  %-4s %-45s desk %3.0f%% (%4.1f d)  game %3.0f%% (%4.1f d)' % (
                r['id'], r['name'], 100 * r['desk_progress'], r['desk_days_left'], 100 * r['game_progress'], r['game_days_left']))


if __name__ == '__main__':
    main()
