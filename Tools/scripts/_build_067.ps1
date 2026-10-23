# test-067: Batmobile armor (bullet/melee/grapple immune; explosions/fire/impact live).
# Base = test-061 aaf. Same-size module edits; health already internal (no toc change expected).
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$b = "$root\Builds\test-067"
Write-Host '=== test-067 (Batmobile armor)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-061\aaf" "$b\aaf" -Recurse -Force
& $py run python "$root\Tools\scripts\_apply_move.py" "$root\Working\Damage\batmobile_armor.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
$oldEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& $py run python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-061\aaf" "$b\verify" --hash 2>&1 | Select-Object -Last 3
$ErrorActionPreference = $oldEAP
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe `
    --internal sportsmuscle_land_global.vmodc --internal sportsmuscle_land_engine.vmodc `
    --internal sportsmuscle_transmission.vmodc --internal sportsmuscle_vehicle_misc.vmodc `
    --internal sportsmuscle_custom_land_global.vmodc --internal sportsmuscle_land_aerodynamics.vmodc `
    --internal sportsmuscle_land_steering.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
$eeH = (Get-FileHash "$b\$ee" -Algorithm SHA256).Hash
$tocH = (Get-FileHash "$b\$ee.toc" -Algorithm SHA256).Hash
@"
<#
    test-067 installer: Batmobile armor (061 tree + bullet/melee/grapple immunity).
    Bank untouched. Close the game first.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback061','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$B = 'E:\Modding\JC3-Batmobile\Builds\test-067'
switch (`$Action) {
    'Install' { Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee') -Destination `$EeT -Force; Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc') -Destination (`$EeT + '.toc') -Force; Write-Host 'deployed test-067: Batmobile armor' }
    'Rollback061' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JC3-Batmobile\Builds\test-061\install.ps1' -Action Install }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha) { Write-Host '  == test-067 (all match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host 'build ready'
