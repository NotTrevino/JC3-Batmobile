p = 'Tools/scripts/jc3interact.py'
s = open(p, encoding='utf-8').read()

old = '''    for ar in sa["areas"]:
        a(f"- `{ar['name']}`: its own `center_local` lands **{ar['bat_center_verdict']}** "
          f"({ar['bat_center_surface_m']} m) but its vertex centroid "
          f"**{ar['bat_center_geom_verdict']}** ({ar['bat_center_geom_surface_m']} m); the worst")
        a(f"  vertex is {ar['bat_max_clearance_m']} m away, so the surface is *tilted* against the")
        a("  Batmobile shell rather than uniformly lifted.")'''

new = '''    for ar in sa["areas"]:
        a(f"- `{ar['name']}`: `center_local` -> **{ar['bat_center_verdict']}** "
          f"({ar['bat_center_surface_m']} m); vertex centroid -> "
          f"**{ar['bat_center_geom_verdict']}** ({ar['bat_center_geom_surface_m']} m); worst "
          f"vertex {ar['bat_max_clearance_m']} m - the surface is *tilted* against the shell,")
        a("  not uniformly lifted.")'''

assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
