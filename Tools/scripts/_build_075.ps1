# test-075: base = test-074 aaf.
#  Handling only: completes the 091 mass change (975 -> 4000 kg) by scaling the
#  YAW-authority channels into JC3's own shipped band for a heavy vehicle.
#  Every new value is one a shipped JC3 vehicle already uses (MODLOG 93/94):
#   counter_steer_torque 3000 -> 16000 (jeep ships 16000; Mugello 15000@2.5t,
#       Urga 18000@6t -> 16000 at our 4t), counter_steer_torque_brake 5000 ->
#       15000 (Mugello), max_drift_torque 5000 -> 12000 (Mugello AND Urga),
#       t_to_full_steer_s 1.2 -> 0.8 (Mugello supercar), max_speed_t_to_full_
#       steer_s 0.85 -> 0.6 (Mugello AND jeep).
#  Engine torque deliberately untouched: our peak torque/mass 0.348 already
#  exceeds the Mugello's 0.276 and the Urga's 0.183, so "sluggish" is a rotation
#  deficit, not a power deficit.
#  All modules internal already; no .toc change expected.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$b = "$root\Builds\test-075"
Write-Host '=== test-075 (yaw authority -> JC3 shipped band)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-074\aaf" "$b\aaf" -Recurse -Force
& $py run python "$root\Tools\scripts\_apply_move.py" "$root\Working\Movement\batmobile_075_yaw.json" "$b\aaf" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
$oldEAP = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
& $py run python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-074\aaf" "$b\verify" --hash 2>&1 | Select-Object -Last 8
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
    test-075 installer: yaw authority scaled into JC3's shipped heavy-vehicle band
    (completes the mass change). Bank untouched. Close the game first.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback074','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$B = 'E:\Modding\JustCause3\JC3-Batmobile\Builds\test-075'
switch (`$Action) {
    'Install' { Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee') -Destination `$EeT -Force; Copy-Item -LiteralPath (Join-Path `$B 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc') -Destination (`$EeT + '.toc') -Force; Write-Host 'deployed test-075: yaw authority -> JC3 shipped heavy band' }
    'Rollback074' { powershell -NoProfile -ExecutionPolicy Bypass -File 'E:\Modding\JustCause3\JC3-Batmobile\Builds\test-074\install.ps1' -Action Install }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha) { Write-Host '  == test-075 (all match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host 'build ready'
