$ErrorActionPreference = "Stop"

$InstallRoot = Join-Path $env:LOCALAPPDATA "RhinoLibraryPlugin"
$CommandName = "LibreriaInterni"
$GimmeMoreCommand = "GimmeMore"

function Test-RhinoRunning {
    return [bool](Get-Process -Name "Rhino" -ErrorAction SilentlyContinue)
}

function Remove-RhinoAlias {
    param([string]$SettingsPath, [string]$AliasName)

    if (-not (Test-Path $SettingsPath)) {
        return
    }

    [xml]$xml = Get-Content -Path $SettingsPath -Encoding UTF8
    $dict = $xml.SelectSingleNode("//child[@key='AliasList']/entry[@key='AliasDictionary']/dictionary")
    if (-not $dict) {
        return
    }

    $existing = $dict.SelectSingleNode("value[@key='$AliasName']")
    if ($existing) {
        [void]$dict.RemoveChild($existing)
        $xml.Save($SettingsPath)
    }
}

if (Test-RhinoRunning) {
    Write-Host ""
    Write-Host "Chiudi Rhino e rilancia Disinstalla.bat."
    Write-Host ""
    exit 1
}

$settingsCandidates = @()
$root = Join-Path $env:APPDATA "McNeel\Rhinoceros"
foreach ($version in @("7.0", "8.0")) {
    $settingsDir = Join-Path $root "$version\settings"
    if (Test-Path $settingsDir) {
        $settingsCandidates += Get-ChildItem -Path $settingsDir -Filter "settings-Scheme__*.xml" -File -ErrorAction SilentlyContinue
    }
}

foreach ($settingsFile in $settingsCandidates) {
    Remove-RhinoAlias -SettingsPath $settingsFile.FullName -AliasName $CommandName
    Remove-RhinoAlias -SettingsPath $settingsFile.FullName -AliasName $GimmeMoreCommand
}

foreach ($version in @("7.0", "8.0")) {
    $scriptsDir = Join-Path $env:APPDATA "McNeel\Rhinoceros\$version\scripts"
    foreach ($scriptName in @("LibreriaInterni.py", "GimmeMore.py")) {
        $scriptCopy = Join-Path $scriptsDir $scriptName
        if (Test-Path $scriptCopy) {
            Remove-Item $scriptCopy -Force
        }
    }
}

if (Test-Path $InstallRoot) {
    Remove-Item -Path $InstallRoot -Recurse -Force
}

Write-Host "Plugin rimosso. Le impostazioni della libreria in AppData\Roaming\RhinoLibraryPlugin restano sul PC."
