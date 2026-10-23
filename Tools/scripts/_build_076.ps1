# test-076: base = test-075 aaf.
#  Bullet/impact proofing completion. The full damage chain is decoded now
#  (_adftypes.py -> the .vmodc's own type library; _healthband.py -> the shipped
#  tank/Urga/stock band). Bullet and impact armour were already at or beyond the
#  tank in 074; the only members still weaker than the tank are the
#  explosion/fire/smoke threshold family, which is exactly where an explosion or
#  fire can still start. This copies the tank's values for those members only:
#   max_health 1800 -> 2000, explosion_threshold 1800 -> 4000,
#   npc_explosion_threshold 1800 -> 4000, vulnerable_explosion_threshold 90 -> 100,
#   smoke_threshold 200 -> 1050, burn_threshold 80 -> 250, explosion_delay_s 8 -> 10.
#  The (max_health 2000, explosion_threshold 4000) pair is copied exactly from the
#  shipped tank, so no invented numbers. All edits are same-size; no .toc change.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$b = "$root\Builds\test-076"
Write-Host '=== test-076 (bullet/impact proofing: tank damage profile)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-075\aaf" "$b\aaf" -Recurse -Force
& $py run python "$root\Tools\scripts\_apply_move.py" "$root\Working\Damage\batmobile_076_tank_parity.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
$oldEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& $py run python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-075\aaf" "$b\verify" --hash 2>&1 | Select-Object -Last 8
$ErrorActionPreference = $oldEAP
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe `
    --internal sportsmuscle_land_global.vmodc --internal sportsmuscle_land_engine.vmodc `
    --internal sportsmuscle_transmission.vmodc --internal sportsmuscle_vehicle_misc.vmodc `
    --internal sportsmuscle_custom_land_global.vmodc --internal sportsmuscle_land_aerodynamics.vmodc `
    --internal sportsmuscle_land_steering.vmodc --internal sportsmuscle_suspension.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
$eeH = (Get-FileHash "$b\$ee" -Algorithm SHA256).Hash
$tocH = (Get-FileHash "$b\$ee.toc" -Algorithm SHA256).Hash
@"
<#
    test-076 installer: bullet/impact proofing completed - the damage header is
    the shipped tank's profile. Bank untouched. Close the game first.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback075','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$B = 'E:\Modding\JC3-Batmobile\Builds\test-076'
switch (`$Action) {
    'Install' { Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee') -Destination `$EeT -Force; Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc') -Destination (`$EeT + '.toc') -Force; Write-Host 'deployed test-076: tank damage profile (bullet/impact proofing complete)' }
    'Rollback075' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JC3-Batmobile\Builds\test-075\install.ps1' -Action Install }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha) { Write-Host '  == test-076 (all match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host 'build ready'
