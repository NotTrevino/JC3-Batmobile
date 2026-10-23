# test-046: Batmobile wheels at the vanilla wheel paths. MODLOG sect 57.
#
# Base = test-045 tree (black Batmobile + palette + 5-part .epe); the wheel RBM
# (Working\Batmobile\bat_wheel_2k5.rbm: plain 0x0004 block cloned from the
# Serpente wheel, 2,500 tris, VERIFY PASS) goes into EVERY sportsmuscle_wheel*
# .rbm path (lod + mshswap). Same bytes everywhere; sizes free (.toc regen).
# .toc: vanilla + base-ee test-003 + --internal epe (parts external, palette
# internal via vanilla).
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$wheel = "$root\Working\Batmobile\bat_wheel_2k5.rbm"

$b = "$root\Builds\test-046"
Write-Host '=== test-046 (Batmobile wheels)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-045\aaf" "$b\aaf" -Recurse -Force
$paths = Get-ChildItem "$b\aaf\$dir" -Filter 'sportsmuscle_wheel*.rbm' | Select-Object -ExpandProperty FullName
Write-Host "  wheel rbm paths: $($paths.Count)"
foreach ($p in $paths) { Copy-Item $wheel $p -Force }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\_make_installer.py" test-046 "Batmobile wheels at vanilla wheel paths" test-045 "CLEAN plain Batmobile + black palette" test-043 "CLEAN: Batmobile in body_lod1..5 (deform), 5-part .epe" test-003 "vanilla geometry, no .toc"
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}
