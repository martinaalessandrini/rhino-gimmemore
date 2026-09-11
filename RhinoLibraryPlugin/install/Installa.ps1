# Requires: PowerShell 5+
# Copia il plugin in AppData e registra il comando LibreriaInterni in Rhino 8 (e 7 se presente).

$ErrorActionPreference = "Stop"

$PluginSource = Split-Path -Parent $PSScriptRoot
$InstallRoot = Join-Path $env:LOCALAPPDATA "RhinoLibraryPlugin"
$CommandName = "LibreriaInterni"
$GimmeMoreCommand = "GimmeMore"
$SkipItems = @("tests", "__pycache__", "install", "dist")

function Test-RhinoRunning {
    return [bool](Get-Process -Name "Rhino" -ErrorAction SilentlyContinue)
}

function Copy-PluginFiles {
    param([string]$Source, [string]$Destination)

    if (Test-Path $Destination) {
        Remove-Item -Path $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null

    Get-ChildItem -Path $Source -Force | Where-Object {
        $SkipItems -notcontains $_.Name
    } | ForEach-Object {
        if ($_.PSIsContainer) {
            Copy-Item -Path $_.FullName -Destination (Join-Path $Destination $_.Name) -Recurse -Force
        }
        else {
            Copy-Item -Path $_.FullName -Destination (Join-Path $Destination $_.Name) -Force
        }
    }

    Get-ChildItem -Path $Destination -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}

function Set-RhinoAlias {
    param(
        [string]$SettingsPath,
        [string]$AliasName,
        [string]$Macro
    )

    if (-not (Test-Path $SettingsPath)) {
        return $false
    }

    $backup = "$SettingsPath.bak-libreria-interni"
    Copy-Item -Path $SettingsPath -Destination $backup -Force

    [xml]$xml = Get-Content -Path $SettingsPath -Encoding UTF8
    $dict = $xml.SelectSingleNode("//child[@key='AliasList']/entry[@key='AliasDictionary']/dictionary")
    if (-not $dict) {
        Write-Host "Non trovo l'elenco alias in: $SettingsPath"
        return $false
    }

    $existing = $dict.SelectSingleNode("value[@key='$AliasName']")
    if ($existing) {
        $existing.InnerText = $Macro
    }
    else {
        $el = $xml.CreateElement("value")
        $el.SetAttribute("key", $AliasName)
        $el.InnerText = $Macro
        [void]$dict.AppendChild($el)
    }

    $xml.Save($SettingsPath)
    return $true
}

if (Test-RhinoRunning) {
    Write-Host ""
    Write-Host "Chiudi Rhino e rilancia Installa.bat."
    Write-Host "Rhino deve essere chiuso per registrare il comando."
    Write-Host ""
    exit 1
}

Write-Host "Installazione in: $InstallRoot"
Copy-PluginFiles -Source $PluginSource -Destination $InstallRoot

$launcher = Join-Path $InstallRoot "LibreriaInterni.py"
if (-not (Test-Path $launcher)) {
    throw "File comando mancante: $launcher"
}
$gimmeLauncher = Join-Path $InstallRoot "GimmeMore.py"
if (-not (Test-Path $gimmeLauncher)) {
    throw "File comando mancante: $gimmeLauncher"
}

$macro = '! _-RunPythonScript "' + $launcher + '"'
$gimmeMacro = '! _-RunPythonScript "' + $gimmeLauncher + '"'
$registered = $false

function Get-RhinoSettingsFiles {
    $files = @()
    $root = Join-Path $env:APPDATA "McNeel\Rhinoceros"
    foreach ($version in @("7.0", "8.0")) {
        $settingsDir = Join-Path $root "$version\settings"
        if (Test-Path $settingsDir) {
            $files += Get-ChildItem -Path $settingsDir -Filter "settings-Scheme__*.xml" -File -ErrorAction SilentlyContinue
        }
    }
    return $files
}

foreach ($settingsFile in Get-RhinoSettingsFiles) {
    $okInterni = Set-RhinoAlias -SettingsPath $settingsFile.FullName -AliasName $CommandName -Macro $macro
    $okGimme = Set-RhinoAlias -SettingsPath $settingsFile.FullName -AliasName $GimmeMoreCommand -Macro $gimmeMacro
    if ($okInterni -or $okGimme) {
        Write-Host "Comandi registrati in: $($settingsFile.FullName)"
        $registered = $true
    }
}

foreach ($version in @("7.0", "8.0")) {
    $scriptsDir = Join-Path $env:APPDATA "McNeel\Rhinoceros\$version\scripts"
    if (Test-Path (Split-Path $scriptsDir -Parent)) {
        if (-not (Test-Path $scriptsDir)) {
            New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
        }
        Copy-Item -Path $launcher -Destination (Join-Path $scriptsDir "LibreriaInterni.py") -Force
        Copy-Item -Path $gimmeLauncher -Destination (Join-Path $scriptsDir "GimmeMore.py") -Force
    }
}

$aliasFile = Join-Path $InstallRoot "LibreriaInterni-alias.txt"
@"
$CommandName $macro
$GimmeMoreCommand $gimmeMacro
"@ | Set-Content -Path $aliasFile -Encoding UTF8

Write-Host ""
if ($registered) {
    Write-Host "Installazione completata."
    Write-Host "Apri Rhino e digita: LibreriaInterni"
    Write-Host "Oppure, per la posa con click: GimmeMore"
}
else {
    Write-Host "File copiati, ma il comando non e' stato registrato automaticamente."
    Write-Host "In Rhino: Opzioni > Alias > Importa, poi scegli:"
    Write-Host $aliasFile
}
Write-Host ""
Write-Host "La cartella dei modelli 3D si sceglie da dentro il plugin (Scegli cartella)."
Write-Host ""
