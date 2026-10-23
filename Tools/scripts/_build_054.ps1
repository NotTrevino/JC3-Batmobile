# test-054: full-asset body (turret/cockpit/batteries included) at the vanilla
# body paths. MODLOG sect 62-63.
#
# Base = test-053 tree (mirrored wheels at RAY stations, black palette, 5-part
# .epe — all proven). Only sportsmuscle_body_lod1..5 change content (full chain
# from the importer matrix). No repoint, parts vmodc stays EXTERNAL.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'

$b = "$root\Builds\test-054"
Write-Host '=== test-054 (full-asset body)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-053\aaf" "$b\aaf" -Recurse -Force
foreach ($i in 1..5) {
    Copy-Item "$root\Working\Batmobile\full_plain_lod$i.rbm" "$b\aaf\$dir\sportsmuscle_body_lod$i.rbm" -Force
}
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\_make_installer.py" test-054 "Full-asset body (turret/cockpit included)" test-053 "Stance reverted to RAY stations, mirrored L/R wheels kept" test-045 "CLEAN plain Batmobile + black palette" test-003 "vanilla geometry, no .toc"
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}
