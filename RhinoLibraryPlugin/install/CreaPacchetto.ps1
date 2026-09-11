# Crea uno zip da inviare ad altri PC.
$ErrorActionPreference = "Stop"

$PluginRoot = Split-Path -Parent $PSScriptRoot
$RepoRoot = Split-Path -Parent $PluginRoot
$Version = (Get-Content (Join-Path $PluginRoot "VERSION.txt") -Raw).Trim()
$DistDir = Join-Path $RepoRoot "dist"
$StageDir = Join-Path $DistDir "LibreriaInterni"
$ZipPath = Join-Path $DistDir "LibreriaInterni-$Version.zip"
$SkipNames = @("tests", "__pycache__", "dist")

if (Test-Path $DistDir) {
    Remove-Item -Path $DistDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StageDir -Force | Out-Null

Get-ChildItem -Path $PluginRoot -Force | Where-Object {
    $SkipNames -notcontains $_.Name
} | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination (Join-Path $StageDir $_.Name) -Recurse -Force
}

Get-ChildItem -Path $StageDir -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}
Compress-Archive -Path $StageDir -DestinationPath $ZipPath -Force
Write-Host "Pacchetto creato:"
Write-Host $ZipPath
