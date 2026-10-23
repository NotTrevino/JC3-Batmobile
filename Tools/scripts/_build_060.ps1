# test-060: 059 tree (body+movement) + Batmobile nitro audio in vehicles.bank.
# Bank: patch game5 vehicles.bank with FSB #56/150/355 PCM swapped (same sizes)
# to Batmobile Turbo/start content. Dropzone-loose bank overrides the archive.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$b = "$root\Builds\test-060"
Write-Host '=== test-060 (Batmobile body + movement + nitro audio)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-059\v0300_car_kensington_sportsmuscle_civilian_01.ee" "$b\" -Force
Copy-Item "$root\Builds\test-059\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc" "$b\" -Force
uv run --with fsb5,numpy python "$root\Tools\scripts\_apply_audio.py" "$root\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank" "$b\vehicles.bank" 2>&1 |
    Where-Object { $_ -notmatch 'Installed|^\s*$' }
$ee = Get-Item "$b\v0300_car_kensington_sportsmuscle_civilian_01.ee"
$toc = Get-Item "$b\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc"
$bank = Get-Item "$b\vehicles.bank"
$eeH = (Get-FileHash $ee -Algorithm SHA256).Hash
$tocH = (Get-FileHash $toc -Algorithm SHA256).Hash
$bankH = (Get-FileHash $bank -Algorithm SHA256).Hash
@"
<#
    test-060 installer: 059 body+movement + Batmobile nitro audio (vehicles.bank FSB swap).
    Deploys .ee + .toc + dropzone-loose vehicles.bank. Rollback059 removes the bank.
    Close the game first. Sizes/shas pinned below.
#>
[CmdletBinding()]
param([ValidateSet('Install','Rollback059','Rollback053','Status')][string]`$Action = 'Status')
`$ErrorActionPreference = 'Stop'
`$GameDir = 'D:\Games\Just Cause 3'
`$EeT = Join-Path `$GameDir 'dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$BankT = Join-Path `$GameDir 'dropzone\sound\fmod_banks\vehicles.bank'
`$EeSha = '$eeH'
`$TocSha = '$tocH'
`$BankSha = '$bankH'
`$B = 'E:\Modding\JC3-Batmobile\Builds\test-060'
function Dep(`$ee,`$toc) {
    Copy-Item -LiteralPath (Join-Path `$B `$ee) -Destination `$EeT -Force
    Copy-Item -LiteralPath (Join-Path `$B `$toc) -Destination (`$EeT + '.toc') -Force
}
function DepBank { `$d = Split-Path -Parent `$BankT; if (-not (Test-Path -LiteralPath `$d)) { New-Item -ItemType Directory -Force -Path `$d | Out-Null }; Copy-Item -LiteralPath (Join-Path `$B 'vehicles.bank') -Destination `$BankT -Force }
function UnBank { if (Test-Path -LiteralPath `$BankT) { Remove-Item -LiteralPath `$BankT -Force; Write-Host 'removed dropzone vehicles.bank' } }
switch (`$Action) {
    'Install' { Dep 'v0300_car_kensington_sportsmuscle_civilian_01.ee' 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc'; DepBank; Write-Host 'deployed test-060: body+movement+Batmobile nitro' }
    'Rollback059' { Dep 'v0300_car_kensington_sportsmuscle_civilian_01.ee' 'v0300_car_kensington_sportsmuscle_civilian_01.ee.toc'; UnBank; Write-Host 'rolled back to 059 tree, bank removed' }
    'Rollback053' { Copy-Item -LiteralPath 'E:\Modding\JC3-Batmobile\Builds\test-053\v0300_car_kensington_sportsmuscle_civilian_01.ee' -Destination `$EeT -Force; Copy-Item -LiteralPath 'E:\Modding\JC3-Batmobile\Builds\test-053\v0300_car_kensington_sportsmuscle_civilian_01.ee.toc' -Destination (`$EeT + '.toc') -Force; UnBank; Write-Host 'rolled back to 053, bank removed' }
    'Status' {
        `$e = if (Test-Path -LiteralPath `$EeT) { (Get-FileHash -LiteralPath `$EeT).Hash } else { 'none' }
        `$t = if (Test-Path -LiteralPath (`$EeT + '.toc')) { (Get-FileHash -LiteralPath (`$EeT + '.toc')).Hash } else { 'none' }
        `$k = if (Test-Path -LiteralPath `$BankT) { (Get-FileHash -LiteralPath `$BankT).Hash } else { 'none' }
        Write-Host "dropzone .ee : `$e"; Write-Host "dropzone .toc: `$t"; Write-Host "dropzone bank: `$k"
        if (`$e -eq `$EeSha -and `$t -eq `$TocSha -and `$k -eq `$BankSha) { Write-Host '  == test-060 (all three match)' }
    }
}
"@ | Out-File "$b\install.ps1" -Encoding utf8
Write-Host ('build ready: ee={0} toc={1} bank={2}' -f $ee.Length, $toc.Length, $bank.Length)
