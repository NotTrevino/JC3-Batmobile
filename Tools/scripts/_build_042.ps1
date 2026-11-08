# test-042: the Batmobile body alone. MODLOG §54.
#
# test-040 drew the Batmobile (bytes at the vanilla sportsmuscle_body_lod5.rbm path) but every
# other Serpente part still drew around it. test-030 proved a 5-part .epe (body + 4 wheels,
# 105,302 B) loads with the other 35 parts gone.
#   test-042 = test-040 tree + test-030's 5-part .epe, read from the .ee (internal)
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$epe  = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.epe'
$b    = "$root\Builds\test-042"

if ((Get-Item "$root\Builds\test-030\aaf\$epe").Length -ne 105302) { throw 'test-030 .epe is not the 5-part 105,302 B file' }
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-040\aaf" "$b\aaf" -Recurse -Force
Copy-Item "$root\Builds\test-030\aaf\$epe" "$b\aaf\$epe" -Force

& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_vehicle_parts.vmodc `
    --internal sportsmuscle_civilian_01.epe --include-lod -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
python -I "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}
