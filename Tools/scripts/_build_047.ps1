# test-047: Tumbler stance + mirrored L/R wheels. MODLOG sect 58.
#
# Base = test-045 tree. Two placement-class changes (visually separable, each
# revertable per file; split if anything reads ambiguously):
#   1. land_global := PATCHED 1600 B copy with hardpoint Z front -1.557 -> -1.945,
#      rear +1.446 -> +1.539 (Tumbler stations for the 5.001 m body; _stance_047.py
#      asserts size + 12 diff bytes + re-export values), INTERNAL in the .toc.
#      (§48 rule: never the .ee's stale 1494 B copy.)
#   2. wheels: L paths (*_f_l*, *_r_l* incl mshswap) := bat_wheel_2k5.rbm,
#      R paths := bat_wheel_R.rbm (X-mirrored, winding flipped; _mirror_wheel.py).
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$lg  = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default\v0300_car_kensington_sportsmuscle_land_global.vmodc'

$b = "$root\Builds\test-047"
Write-Host '=== test-047 (Tumbler stance + mirrored wheels)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-045\aaf" "$b\aaf" -Recurse -Force
Copy-Item "$root\Working\Stance\land_global_stance.vmodc" "$b\aaf\$lg" -Force
$wl = Get-ChildItem "$b\aaf\$dir" -Filter 'sportsmuscle_wheel*.rbm' | Where-Object { ($_.Name -match '_wheel_f_l') -or ($_.Name -match '_wheel_r_l') } | Select-Object -ExpandProperty FullName
$wr = Get-ChildItem "$b\aaf\$dir" -Filter 'sportsmuscle_wheel*.rbm' | Where-Object { ($_.Name -match '_wheel_f_r') -or ($_.Name -match '_wheel_r_r') } | Select-Object -ExpandProperty FullName
Write-Host "  L paths: $($wl.Count), R paths: $($wr.Count)"
if ($wl.Count + $wr.Count -ne 30) { throw 'wheel path count is not 30' }
foreach ($p in $wl) { Copy-Item "$root\Working\Batmobile\bat_wheel_2k5.rbm" $p -Force }
foreach ($p in $wr) { Copy-Item "$root\Working\Batmobile\bat_wheel_R.rbm" $p -Force }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe --internal sportsmuscle_land_global.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\_make_installer.py" test-047 "Tumbler stance + mirrored L/R wheels" test-046 "Batmobile wheels at vanilla wheel paths" test-045 "CLEAN plain Batmobile + black palette" test-003 "vanilla geometry, no .toc"
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}
