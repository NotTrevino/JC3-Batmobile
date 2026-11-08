# test-035 / test-036. MODLOG §49.
#
# test-034 (patched parts vmodc internal + body -> dababy_head.lod) LOADS, the stock body is
# gone, but nothing replaces it. The new .lod was not in the .toc (eetoc followed the DaBaby
# .toc, which omits its .lods) -- yet the VANILLA .toc lists all 59 of its .lod files with
# real offsets. Hypothesis: unlisted .lod -> body model fails to resolve -> empty slot.
#
#   test-035 = test-034's .ee (byte-identical) + .toc that also lists dababy_head.lod
#   test-036 = test-035 with dababy_head.rbm's CONTENT := Working\Batmobile\bat_body_20k.rbm
#
# LOCAL TEST ONLY while the tree carries Luke JC's dababy_head.lod / convertible.ddsc.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$vtoc = "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc"
$head = 'models\jc_vehicles\01_land\v0000_car_autostraad_oldjeep\dababy\dababy_head.rbm'
$bat  = "$root\Working\Batmobile\bat_body_20k.rbm"

function Toc($b) {
    python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" $vtoc --base-ee "$root\Builds\test-003\$ee" `
        --internal sportsmuscle_vehicle_parts.vmodc --include-lod -o "$b\$ee.toc" 2>&1 |
        Where-Object { $_ -notmatch 'Warning|warnings.warn' }
}
function Show($b) {
    foreach ($f in "$b\$ee", "$b\$ee.toc") {
        Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
    }
}

Write-Host '=== test-035'
$b = "$root\Builds\test-035"
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-034\$ee" "$b\$ee"
Toc $b; Show $b

Write-Host '=== test-036'
$b = "$root\Builds\test-036"
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-034\aaf" "$b\aaf" -Recurse -Force
Copy-Item $bat "$b\aaf\$head" -Force
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
Toc $b; Show $b
