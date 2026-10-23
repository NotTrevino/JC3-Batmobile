$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g = "$root\Tools\Gibbed"
$van = "$root\Builds\test-003\aaf"
$target_rel = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\sportsmuscle_body_lod1.rbm'

function Build-Package($tag, $srcRbm, $desc) {
    $b = "$root\Builds\$tag"
    # stage the source OUTSIDE the directory we are about to wipe
    $stage = [IO.Path]::GetTempFileName()
    Copy-Item $srcRbm $stage -Force
    if (Test-Path $b) { Remove-Item $b -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $b | Out-Null
    Copy-Item $van "$b\aaf" -Recurse -Force
    Copy-Item $stage "$b\aaf\$target_rel" -Force
    Remove-Item $stage -Force

    $ee = "$b\v0300_car_kensington_sportsmuscle_civilian_01.ee"
    & "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" $ee | Out-Null
    if (Test-Path "$b\verify") { Remove-Item "$b\verify" -Recurse -Force }
    & "$g\Gibbed.JustCause3.SmallUnpack.exe" $ee "$b\verify" | Out-Null

    $size = (Get-Item $ee).Length
    $sha = (Get-FileHash $ee -Algorithm SHA256).Hash
    "  $tag packed: $size B  sha256 $sha"
    "  $desc"

    $script = @"
<#
    $tag installer. BuildDir from `$PSScriptRoot; asserts size AND sha256 before copying.
#>
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Rollback010', 'Rollback003', 'Status')]
    [string]`$Action = 'Status'
)
`$ErrorActionPreference = 'Stop'
`$BuildDir = `$PSScriptRoot
`$RepoRoot = (Resolve-Path (Join-Path `$BuildDir '..\..')).Path
`$Target = 'D:\Games\Just Cause 3\dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.ee'
`$Artifacts = [ordered]@{
    '$tag' = @{ Path = Join-Path `$BuildDir 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
        Size = $size; Sha = '$sha'
        Desc = '$desc' }
    'test-010' = @{ Path = Join-Path `$RepoRoot 'Builds\test-010\v0300_car_kensington_sportsmuscle_civilian_01.ee'
        Size = 5530633; Sha = 'C79D44B4937FAA330949580E523066511B62F3CB0252707EEDCB29B936F4C896'
        Desc = 'wedge reshape, no added geometry' }
    'test-017' = @{ Path = Join-Path `$RepoRoot 'Builds\test-017\v0300_car_kensington_sportsmuscle_civilian_01.ee'
        Size = 5526093; Sha = '4C7251130F4A2130786196F6D389E88C11F55172B423D7C32B7CD4875145F8DF'
        Desc = '.epe round-tripped with pad bytes restored' }
    'test-003' = @{ Path = Join-Path `$RepoRoot 'Builds\test-003\v0300_car_kensington_sportsmuscle_civilian_01.ee'
        Size = 5526072; Sha = '194A01B573D586259B854E3607CBBEC02C10CED8406A95C42979DDEF22B8FFF8'
        Desc = 'proven-good vanilla black car' }
}
function Test-Artifact(`$a) {
    if (-not (Test-Path -LiteralPath `$a.Path)) { throw "artifact missing: `$(`$a.Path)" }
    `$f = Get-Item -LiteralPath `$a.Path
    if (`$f.Length -ne `$a.Size) { throw "size mismatch for `$(`$f.Name): expected `$(`$a.Size), found `$(`$f.Length)" }
    `$h = (Get-FileHash -LiteralPath `$a.Path -Algorithm SHA256).Hash
    if (`$h -ne `$a.Sha) { throw "sha256 mismatch for `$(`$f.Name):`n  expected `$(`$a.Sha)`n  found    `$h" }
    Write-Host "verified `$(`$f.Name): `$(`$f.Length) B, sha256 `$(`$h.Substring(0,16))..." -ForegroundColor DarkGray
}
function Deploy(`$name) {
    `$a = `$Artifacts[`$name]; Test-Artifact `$a
    `$dir = Split-Path -Parent `$Target
    if (-not (Test-Path -LiteralPath `$dir)) { New-Item -ItemType Directory -Force -Path `$dir | Out-Null }
    Copy-Item -LiteralPath `$a.Path -Destination `$Target -Force
    Write-Host "deployed `$name" -ForegroundColor Green
    Write-Host "  `$(`$a.Desc)" -ForegroundColor DarkGray
}
switch (`$Action) {
    'Install' { Deploy '$tag' }
    'Rollback010' { Deploy 'test-010' }
    'Rollback003' { Deploy 'test-003' }
    'Status' {
        if (Test-Path -LiteralPath `$Target) {
            Write-Host "dropzone: `$((Get-FileHash -LiteralPath `$Target -Algorithm SHA256).Hash)"
        } else { Write-Host 'dropzone: nothing deployed' }
    }
}
"@
    Set-Content -Path "$b\install.ps1" -Value $script -Encoding UTF8
}

Write-Host '=== packing both bisection builds ==='
Build-Package 'test-018' "$root\Builds\_bisect\test-018.rbm" `
    'INDEX-COUNT BISECTION: last triangle dropped (3168->3165), vertex bytes untouched'
Build-Package 'test-019' "$root\Builds\_bisect\test-019.rbm" `
    'VERTEX-COUNT BISECTION: one vertex duplicated (1024->1025), index buffer untouched'

Write-Host ''
Write-Host '=== verifying each package against the pristine tree ==='
cd "$root\Tools\scripts"
foreach ($tag in @('test-018', 'test-019')) {
    Write-Host "-- $tag"
    uv run --quiet python aafdiff.py "$root\Builds\test-003\aaf" "$root\Builds\$tag\verify" --hash 2>&1 |
        Select-String 'only in|identical content|different content'
}

Write-Host ''
Write-Host '=== deploying test-018 (one experiment at a time; 019 stays staged) ==='
& "$root\Builds\test-018\install.ps1" -Action Install
& "$root\Builds\test-018\install.ps1" -Action Rollback010 | Out-Null
& "$root\Builds\test-018\install.ps1" -Action Install
& "$root\Builds\test-018\install.ps1" -Action Status