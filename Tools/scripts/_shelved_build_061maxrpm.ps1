# test-061: STATMAP rpm diagnostic (max_rpm 14600->6000, all else = 060).
# Base = test-059 aaf (060 tree). Repack + internalize (same 5 as 059) + bank copy.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'

$b = "$root\Builds\_shelved-061maxrpm"
Write-Host '=== test-061 (STATMAP rpm diagnostic)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-059\aaf" "$b\aaf" -Recurse -Force
& $py run python "$root\Tools\scripts\_apply_move.py" "$root\Working\Movement\bmak_targets_061.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe `
    --internal sportsmuscle_transmission.vmodc --internal sportsmuscle_vehicle_misc.vmodc `
    --internal sportsmuscle_land_engine.vmodc --internal sportsmuscle_custom_land_global.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
$oldEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& $py run python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-059\aaf" "$b\verify" --hash 2>&1 | Select-Object -Last 3
$ErrorActionPreference = $oldEAP
Copy-Item "$root\Builds\test-060\vehicles.bank" "$b\vehicles.bank" -Force
$eeH = (Get-FileHash "$b\$ee" -Algorithm SHA256).Hash
$tocH = (Get-FileHash "$b\$ee.toc" -Algorithm SHA256).Hash
$bankH = (Get-FileHash "$b\vehicles.bank" -Algorithm SHA256).Hash
@"
<#
    test-061 installer: 060 tree + max_rpm 14600->6000 (STATMAP rpm diagnostic).
    Close the game first. Sizes/shas pinned below.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback060','Rollback059','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$BankT = Join-Path `$GameDir 'dropzone\sound\fmod_banks\vehicles.bank'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$BankSha = '$bankH'
`$B = 'E:\Modding\JustCause3\JC3-Batmobile\Builds\_shelved-061maxrpm'
function DepBank { `$d = Split-Path -Parent `$BankT; if (-not (Test-Path -LiteralPath `$d)) { New-Item -ItemType Directory -Force -Path `$d | Out-Null }; Copy-Item -LiteralPath (Join-Path `$B 'vehicles.bank') -Destination `$BankT -Force }
function UnBank { if (Test-Path -LiteralPath `$BankT) { Remove-Item -LiteralPath `$BankT -Force; Write-Host 'removed dropzone vehicles.bank' } }
switch (`$Action) {
    'Install' { Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee') -Destination `$EeT -Force; Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc') -Destination (`$EeT + '.toc') -Force; DepBank; Write-Host 'deployed test-061: 060 + max_rpm 6000' }
    'Rollback060' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JustCause3\JC3-Batmobile\Builds\test-060\install.ps1' -Action Install }
    'Rollback059' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JustCause3\JC3-Batmobile\Builds\test-060\install.ps1' -Action Rollback059 }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        `$k = if (Test-Path -LiteralPath `$BankT) { (Get-FileHash -LiteralPath `$BankT).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"; Write-Host "dropzone bank: `$k"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha -and `$k -eq `$BankSha) { Write-Host '  == test-061 (all three match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host 'build ready'

