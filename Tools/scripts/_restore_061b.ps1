# RESTORE-2 test-061: hypothesis 061 RBMs == 062 RBMs (diet already in); revert
# land_global -> live1600 + physicsc -> vanilla059 on top of 062 tree.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$b = "$root\Builds\test-061"
$m = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$mm = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default'
Write-Host '=== RESTORE-2 test-061 (062 tree minus true LG/PC)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-062\aaf" "$b\aaf" -Recurse -Force
Copy-Item "$root\Working\Movement\live\v0300_car_kensington_sportsmuscle_land_global.vmodc" "$b\aaf\$mm\" -Force
Copy-Item "$root\Builds\test-059\aaf\$m\sportsmuscle.physicsc" "$b\aaf\$m\" -Force
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
$len = (Get-Item "$b\$ee").Length
$h = (Get-FileHash "$b\$ee" -Algorithm SHA256).Hash
Write-Host ('packed: {0} B {1} want 7132666 36B63D5A...' -f $len, $h)
