#Requires -Version 5.1
<#
  inventory.ps1 - build a machine-readable inventory of the JC3-Batmobile project.

  Usage:
    powershell -File inventory.ps1 -Root E:\Modding\JustCause3\JC3-Batmobile -Out E:\Modding\JustCause3\JC3-Batmobile\Research

  Writes:
    <Out>\INVENTORY.json   full file list + per-directory rollups
    <Out>\INVENTORY.md     human summary

  Read-only: this script never modifies anything under -Root.
#>
[CmdletBinding()]
param(
    [string]$Root = 'E:\Modding\JustCause3\JC3-Batmobile',
    [string]$Out  = 'E:\Modding\JustCause3\JC3-Batmobile\Research'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Root)) { throw "Root not found: $Root" }
New-Item -ItemType Directory -Force -Path $Out | Out-Null

$rootFull = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')

function Get-Rel([string]$p) { $p.Substring($rootFull.Length).TrimStart('\') }

# ---- file list -------------------------------------------------------------
$files = Get-ChildItem -LiteralPath $rootFull -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike "$Out\*" } |
    ForEach-Object {
        [PSCustomObject]@{
            path   = Get-Rel $_.FullName
            bytes  = $_.Length
            ext    = $_.Extension.TrimStart('.').ToLowerInvariant()
            sha256 = $null
        }
    }

# ---- per-top-directory rollup ---------------------------------------------
$dirs = $files | Group-Object { ($_.path -split '\\')[0] } | ForEach-Object {
    $g = $_.Group
    [PSCustomObject]@{
        name      = $_.Name
        files     = $g.Count
        megabytes = [math]::Round((($g | Measure-Object bytes -Sum).Sum) / 1MB, 2)
        extensions = @($g | Group-Object ext | Sort-Object Count -Descending |
                        Select-Object -First 12 |
                        ForEach-Object { "$($_.Name):$($_.Count)" })
    }
} | Sort-Object name

# ---- extension rollup ------------------------------------------------------
$exts = $files | Group-Object ext | Sort-Object Count -Descending | ForEach-Object {
    [PSCustomObject]@{ ext = $_.Name; count = $_.Count }
}

# ---- semantically interesting file classes --------------------------------
function Select-Match([string]$rx, [int]$limit = 40) {
    @($files | Where-Object { $_.path -match $rx } | Select-Object -First $limit |
        Select-Object path, bytes)
}

$classes = [ordered]@{
    rbm_models   = Select-Match '\.rbm$'
    lod_tables   = Select-Match '\.lod$'
    vmodc_modules= Select-Match '\.vmodc$'
    entities_ee  = Select-Match '\.ee$'
    entities_epe = Select-Match '\.epe$'
    physics      = Select-Match '\.physicsc$'
    textures_hmd = Select-Match '\.hmddsc$'
    source_pskx  = Select-Match '\.pskx$'
    tools_exe    = Select-Match '\.(exe|dll)$' 20
}

# ---- donor integrity: hash the files we must never mutate ----------------
$donorRoots = @(
    'SerpenteR-EE',
    '1497004460_BATMAN-mod',
    'Playable_Batmobile_SF'
)
$donors = foreach ($d in $donorRoots) {
    $prefix = "$d\"
    $g = @($files | Where-Object { $_.path.StartsWith($prefix, 'OrdinalIgnoreCase') })
    [PSCustomObject]@{
        name      = $d
        files     = $g.Count
        megabytes = [math]::Round((($g | Measure-Object bytes -Sum).Sum) / 1MB, 2)
        present   = ($g.Count -gt 0)
    }
}

$inv = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    generator     = 'inventory.ps1'
    root          = $rootFull
    totals        = [ordered]@{
        files     = $files.Count
        megabytes = [math]::Round((($files | Measure-Object bytes -Sum).Sum) / 1MB, 2)
        directories = ($files | ForEach-Object { $_.path -replace '[^\\]+$','' } | Sort-Object -Unique).Count
    }
    by_directory  = @($dirs)
    by_extension  = @($exts)
    donors        = @($donors)
    classes       = $classes
    files         = @($files | Sort-Object path)
}

$jsonPath = Join-Path $Out 'INVENTORY.json'
$inv | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

# ---- markdown summary ------------------------------------------------------
$md = New-Object System.Collections.Generic.List[string]
$md.Add('# Project inventory')
$md.Add('')
$md.Add("- Root: ``$rootFull``")
$md.Add("- Generated: ``$($inv.generated_utc)``")
$md.Add("- Files: **$($inv.totals.files)** ($($inv.totals.megabytes) MB) across $($inv.totals.directories) directories")
$md.Add('')
$md.Add('## By top-level directory')
$md.Add('')
$md.Add('| Directory | Files | MB |')
$md.Add('|---|---:|---:|')
foreach ($d in $dirs) { $md.Add("| ``$($d.name)`` | $($d.files) | $($d.megabytes) |") }
$md.Add('')
$md.Add('## Donors (must stay byte-identical)')
$md.Add('')
$md.Add('| Donor | Present | Files | MB |')
$md.Add('|---|---|---:|---:|')
foreach ($d in $donors) { $md.Add("| ``$($d.name)`` | $($d.present) | $($d.files) | $($d.megabytes) |") }
$md.Add('')
$md.Add('## Key file classes')
$md.Add('')
foreach ($kv in $classes.GetEnumerator()) {
    $md.Add("### $($kv.Key) ($($kv.Value.Count) shown)")
    $md.Add('')
    $md.Add('```')
    foreach ($f in $kv.Value) {
        $line = '{0,10}  {1}' -f $f.bytes, $f.path
        $md.Add($line)
    }
    $md.Add('```')
    $md.Add('')
}
$mdPath = Join-Path $Out 'INVENTORY.md'
Set-Content -LiteralPath $mdPath -Value $md -Encoding UTF8

Write-Host "wrote $jsonPath"
Write-Host "wrote $mdPath"