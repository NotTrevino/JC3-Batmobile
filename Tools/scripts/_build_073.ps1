# test-073: COMBINED (user direction). Base = test-072 aaf.
#  (a) BmAK-conformant damage model, copied from shipped lave_health_armored.vmodc
#      (bullet/impact/melee/elec/grapple immune; explosion live-but-strong).
#  (b) deform_scale 1->0 (user: BmAK Batmobile doesn't deform).
#  (c) handling: grip_multiplier x2.84 (MODLOG 81a) + mass 975->4000 (MODLOG 85,
#      tonnes range) applied JOINTLY as 85 prescribes.
# health/land_global already internal; rigid_body patched in place (no round trip).
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$b = "$root\Builds\test-073"
Write-Host '=== test-073 (BmAK damage model + joint handling)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-072\aaf" "$b\aaf" -Recurse -Force
& $py run python "$root\Tools\scripts\_apply_move.py" "$root\Working\Damage\batmobile_073_health.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\_apply_move.py" "$root\Working\Movement\batmobile_073_grip.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\_patch_bin.py" "$root\Working\Movement\batmobile_073_mass.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
$oldEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& $py run python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-072\aaf" "$b\verify" --hash 2>&1 | Select-Object -Last 8
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
    test-073 installer: BmAK damage model (immune bullet/impact/melee) + no deform
    + joint handling (grip x2.84, mass 4000). Bank untouched. Close the game first.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback072','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$B = 'E:\Modding\JC3-Batmobile\Builds\test-073'
switch (`$Action) {
    'Install' { Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee') -Destination `$EeT -Force; Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc') -Destination (`$EeT + '.toc') -Force; Write-Host 'deployed test-073: BmAK damage model + joint handling' }
    'Rollback072' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JC3-Batmobile\Builds\test-072\install.ps1' -Action Install }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha) { Write-Host '  == test-073 (all match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host 'build ready'
