param(
    [string]$Version = (Get-Content -LiteralPath (Join-Path $PSScriptRoot "..\VERSION") -Raw).Trim(),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\dist")
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $RepositoryRoot "assetto_corsa\apps\lua\sim_telemetry_engineer"
$ResolvedOutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$Archive = Join-Path $ResolvedOutputDirectory "sim-telemetry-engineer-v$Version.zip"

if ($Version -notmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$') {
    throw "Invalid release version: $Version"
}

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "App source was not found: $Source"
}

if (-not (Test-Path -LiteralPath $ResolvedOutputDirectory)) {
    New-Item -ItemType Directory -Path $ResolvedOutputDirectory | Out-Null
}

Compress-Archive -LiteralPath $Source -DestinationPath $Archive -CompressionLevel Optimal -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$Zip = [System.IO.Compression.ZipFile]::OpenRead($Archive)
try {
    $EntryNames = @($Zip.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
    $RequiredEntries = @(
        "sim_telemetry_engineer/manifest.ini",
        "sim_telemetry_engineer/sim_telemetry_engineer.lua",
        "sim_telemetry_engineer/src/deployment_model.lua",
        "sim_telemetry_engineer/src/setup_reader.lua",
        "sim_telemetry_engineer/src/track_map.lua",
        "sim_telemetry_engineer/src/vrc_adapter.lua"
    )
    foreach ($RequiredEntry in $RequiredEntries) {
        if ($EntryNames -notcontains $RequiredEntry) {
            throw "Release archive is missing: $RequiredEntry"
        }
    }
}
finally {
    $Zip.Dispose()
}

$Hash = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "Created: $Archive"
Write-Host "SHA256: $Hash"
