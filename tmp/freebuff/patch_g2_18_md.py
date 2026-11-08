import io

p = 'Tools/scripts/jc3interact.py'
s = open(p, encoding='utf-8').read()

old_table = '''    a("| area | centre on Batmobile | centre verdict | centre clearance m | vertices "
      "on-surface | worst vertex clearance m |")
    a("|---|---|---|---|---|---|")
    for ar in sa["areas"]:
        a(f"| `{ar['name']}` | {ar['bat_center'][0]:.3f}, {ar['bat_center'][1]:.3f}, "
          f"{ar['bat_center'][2]:.3f} | **{ar['bat_center_verdict']}** | "
          f"{ar['bat_center_surface_m']} | {ar['bat_on_surface']}/{ar['n_deform_points']} | "
          f"{ar['bat_max_clearance_m']} |")'''

new_table = '''    a("Two centres, because the module ships one and the vertices give another: `center_local`")
    a("is the file's own field, the geometric centroid is what the surface actually spans, and")
    a(f"they sit up to {max(x['center_gap_m'] for x in sa['areas'])} m apart.")
    a("")
    a("| area | `center_local` on Batmobile | verdict | m | vertex centroid on Batmobile | "
      "verdict | m | vertices on-surface | worst vertex m |")
    a("|---|---|---|---|---|---|---|---|---|")
    for ar in sa["areas"]:
        a(f"| `{ar['name']}` | {ar['bat_center'][0]:.3f}, {ar['bat_center'][1]:.3f}, "
          f"{ar['bat_center'][2]:.3f} | **{ar['bat_center_verdict']}** | "
          f"{ar['bat_center_surface_m']} | {ar['bat_center_geom'][0]:.3f}, "
          f"{ar['bat_center_geom'][1]:.3f}, {ar['bat_center_geom'][2]:.3f} | "
          f"**{ar['bat_center_geom_verdict']}** | {ar['bat_center_geom_surface_m']} | "
          f"{ar['bat_on_surface']}/{ar['n_deform_points']} | {ar['bat_max_clearance_m']} |")'''

assert old_table in s
s = s.replace(old_table, new_table)

old_txt = '''    a("`main_area` is the roof/trunk deck. **None of the three touches the Batmobile shell**:")
    a("every centre floats, "
      + ", ".join(f"`{x['name']}` {x['bat_center_surface_m']} m" for x in sa["areas"])
      + " above the nearest triangle, and no vertex is within the")
    a(f"{m['on_surface_threshold_m']} m on-surface band. The clearances are the number a build has")
    a("to close by re-fitting the surfaces to the Batmobile's own parts, not by scaling.")'''

new_txt = '''    a("`main_area` is the roof/trunk deck. Read the two verdict columns together:")
    a("")
    for ar in sa["areas"]:
        a(f"- `{ar['name']}`: its own `center_local` lands **{ar['bat_center_verdict']}** "
          f"({ar['bat_center_surface_m']} m) but its vertex centroid "
          f"**{ar['bat_center_geom_verdict']}** ({ar['bat_center_geom_surface_m']} m); the worst")
        a(f"  vertex is {ar['bat_max_clearance_m']} m away, so the surface is *tilted* against the")
        a("  Batmobile shell rather than uniformly lifted.")
    a("")
    a("The gap is the point of the exercise: a bbox-scaled copy lands close enough to *look* right")
    a("at the centre and is tens of centimetres out at its edges. A build has to re-fit the")
    a("vertices against the Batmobile mesh, not scale them.")'''

assert old_txt in s
s = s.replace(old_txt, new_txt)

old4 = '''    a(f"  {c['verdicts'].get('inside', 0)} inside the shell, {c['verdicts'].get('floating', 0)}"
      " floating and **0 on-surface**.")'''
new4 = '''    a(f"  {c['verdicts'].get('inside', 0)} inside the shell, {c['verdicts'].get('floating', 0)}"
      " floating, "
      + f"{c['verdicts'].get('on-surface', 0)} on-surface and"
      + f" {c['verdicts'].get('n/a (container origin)', 0)} with no position of their own.")'''
assert old4 in s
s = s.replace(old4, new4)

open(p, 'w', encoding='utf-8').write(s)
print('patched')
