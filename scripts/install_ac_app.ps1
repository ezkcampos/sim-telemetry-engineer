param(
    [string]$AssettoCorsaRoot = "C:\Program Files (x86)\Steam\steamapps\common\assettocorsa"
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $RepositoryRoot "assetto_corsa\apps\lua\sim_telemetry_engineer"
$AppsRoot = Join-Path $AssettoCorsaRoot "apps\lua"
$Destination = Join-Path $AppsRoot "sim_telemetry_engineer"

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "App source was not found: $Source"
}

if (-not (Test-Path -LiteralPath $AppsRoot -PathType Container)) {
    throw "Assetto Corsa Lua apps directory was not found: $AppsRoot"
}

if (-not (Test-Path -LiteralPath $Destination)) {
    New-Item -ItemType Directory -Path $Destination | Out-Null
}

Copy-Item -LiteralPath (Join-Path $Source "manifest.ini") -Destination $Destination -Force
Copy-Item -LiteralPath (Join-Path $Source "sim_telemetry_engineer.lua") -Destination $Destination -Force

$SourceModules = Join-Path $Source "src"
$DestinationModules = Join-Path $Destination "src"
if (-not (Test-Path -LiteralPath $DestinationModules)) {
    New-Item -ItemType Directory -Path $DestinationModules | Out-Null
}
Get-ChildItem -LiteralPath $SourceModules -File -Filter "*.lua" | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $DestinationModules -Force
}

Write-Host "Installed Sim Telemetry Engineer at: $Destination"
