# RESTORE test-061 (lore_stats torque build, MODLOG: .ee 36B63D5A 7,132,666 B).
# aaf = test-059 aaf + patched land_global (live, 1600B) + 6 lore modules (out/).
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$b = "$root\Builds\test-061"
Write-Host '=== RESTORE test-061 (lore torque build)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-059\aaf" "$b\aaf" -Recurse -Force
$mod = "$b\aaf\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default"
Copy-Item "$root\Working\Movement\live\v0300_car_kensington_sportsmuscle_land_global.vmodc" "$mod\" -Force
foreach ($m in 'custom_land_global','land_aerodynamics','land_engine','land_steering','transmission','vehicle_misc') {
    Copy-Item "$root\Working\Movement\out\v0300_car_kensington_sportsmuscle_$m.vmodc" "$mod\" -Force
}
if ((Get-Item "$mod\v0300_car_kensington_sportsmuscle_land_global.vmodc").Length -ne 1600) { throw 'land_global not patched' }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
$h = (Get-FileHash "$b\$ee" -Algorithm SHA256).Hash
$len = (Get-Item "$b\$ee").Length
Write-Host ('packed: {0} B {1}' -f $len, $h)
if ($len -ne 7132666) { throw "size mismatch: expected 7132666 (MODLOG), got $len" }
Write-Host 'size matches recorded 7,132,666 B'
& uv run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe `
    --internal sportsmuscle_land_global.vmodc --internal sportsmuscle_land_engine.vmodc `
    --internal sportsmuscle_transmission.vmodc --internal sportsmuscle_vehicle_misc.vmodc `
    --internal sportsmuscle_custom_land_global.vmodc --internal sportsmuscle_land_aerodynamics.vmodc `
    --internal sportsmuscle_land_steering.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
$tocH = (Get-FileHash "$b\$ee.toc" -Algorithm SHA256).Hash
$eeH = (Get-FileHash "$b\$ee" -Algorithm SHA256).Hash
Write-Host ('toc: {0} B {1}' -f (Get-Item "$b\$ee.toc").Length, $tocH)
if ($tocH.Substring(0,8) -ne 'B04F8ABE') { throw 'toc hash prefix mismatch (want B04F8ABE...)' }
if ($eeH.Substring(0,8) -ne '36B63D5A') { throw 'ee hash prefix mismatch (want 36B63D5A...)' }
Write-Host 'hashes match recorded prefixes 36B63D5A/B04F8ABE'
@"
<#
    test-061 installer (RESTORED lore torque build 2026-10-15): 060 tree + 6 lore
    modules + patched land_global. Bank untouched (060 bank stays deployed).
    Close the game first.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback060','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$B = 'E:\Modding\JC3-Batmobile\Builds\test-061'
switch (`$Action) {
    'Install' { Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee') -Destination `$EeT -Force; Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc') -Destination (`$EeT + '.toc') -Force; Write-Host 'deployed test-061 (restored lore build)' }
    'Rollback060' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JC3-Batmobile\Builds\test-060\install.ps1' -Action Install }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha) { Write-Host '  == test-061 (restored, both match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host 'restore build ready'
