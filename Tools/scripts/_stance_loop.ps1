# Stance loop: one command builds every rearward-shift variant (048-052).
# Each = 047 tree + land_global shifted +Delta (wheelbase fixed at 3.484 m).
# land_global keeps its size, so every variant reuses 047's .toc byte-identically
# (asserted). Install sequentially, stop at the first that sits right and report it.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$lg  = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default\v0300_car_kensington_sportsmuscle_land_global.vmodc'
$reftoc = "$root\Builds\test-047\$ee.toc"

$tags = @(@{Tag='test-048'; D='+0.1'}, @{Tag='test-049'; D='+0.2'}, @{Tag='test-050'; D='+0.3'},
          @{Tag='test-051'; D='+0.4'}, @{Tag='test-052'; D='+0.5'})
foreach ($t in $tags) {
    $b = "$root\Builds\$($t.Tag)"
    Write-Host "=== $($t.Tag)  (shift $($t.D) m rearward)"
    if (Test-Path $b) { Remove-Item $b -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $b | Out-Null
    Copy-Item "$root\Builds\test-047\aaf" "$b\aaf" -Recurse -Force
    & $py run python "$root\Tools\scripts\_stance_shift.py" $t.D "$b\land_global_shift.vmodc" 2>&1 |
        Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    Copy-Item "$b\land_global_shift.vmodc" "$b\aaf\$lg" -Force
    Remove-Item "$b\land_global_shift.vmodc*" -Force
    & "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
    if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
    & $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
        --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe --internal sportsmuscle_land_global.vmodc -o "$b\$ee.toc" 2>&1 |
        Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    $a = (Get-FileHash "$b\$ee.toc").Hash; $r = (Get-FileHash $reftoc).Hash
    if ($a -ne $r) { throw "$($t.Tag) .toc differs from 047's" }
    & $py run python "$root\Tools\scripts\_make_installer.py" $t.Tag "Stance shift $($t.D) m rearward (wheelbase 3.484)" test-047 "Tumbler stance + mirrored L/R wheels" test-045 "CLEAN plain Batmobile + black palette" test-003 "vanilla geometry, no .toc"
    Write-Host ('  {0,9} B  {1}' -f (Get-Item "$b\$ee").Length, (Get-FileHash "$b\$ee").Hash)
}
Write-Host 'ALL FIVE BUILT. Install 048..052 in order; report the first that sits right.'
