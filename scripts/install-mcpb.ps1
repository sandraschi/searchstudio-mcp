#Requires -Version 5.1
<#
.SYNOPSIS
Install a .mcpb extension into Claude Desktop (Windows) without the drag-and-drop dialog.

.DESCRIPTION
Claude Desktop only. Cursor, VS Code, Claude Code and other clients do not read .mcpb.

Source can be a local path or an https URL (e.g. a GitHub release asset). The bundle is
unpacked into "%APPDATA%\Claude\Claude Extensions\<id>", registered in
extensions-installations.json (backed up first) and enabled. Re-running upgrades in place.
Claude Desktop reads the extension list at startup: quit it from the tray and relaunch.

NOTE: this writes Claude Desktop's own extension store directly. That layout is not a
documented API; if Desktop changes it, fall back to double-clicking the .mcpb.

.EXAMPLE
irm https://github.com/OWNER/REPO/releases/latest/download/install.ps1 | iex

.EXAMPLE
.\install-mcpb.ps1 -Source D:\Dev\repos\x\dist\x.mcpb
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [string]$Sha256
)
$ErrorActionPreference = 'Stop'

$claudeDir = Join-Path $env:APPDATA 'Claude'
if (-not (Test-Path $claudeDir)) { throw "Claude Desktop data folder not found ($claudeDir). This installer is for Claude Desktop on Windows only." }
$extRoot = Join-Path $claudeDir 'Claude Extensions'
$setRoot = Join-Path $claudeDir 'Claude Extensions Settings'
$regPath = Join-Path $claudeDir 'extensions-installations.json'
$utf8 = New-Object System.Text.UTF8Encoding($false)   # no BOM: Desktop's JSON parser dislikes one

$work = Join-Path ([IO.Path]::GetTempPath()) ('install-mcpb-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force -Path $work | Out-Null
try {
    # 1. Fetch
    $zip = Join-Path $work 'bundle.zip'   # Expand-Archive on 5.1 insists on .zip
    if ($Source -match '^https://') {
        Write-Host "Downloading $Source"
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $Source -OutFile $zip -UseBasicParsing
    } elseif (Test-Path $Source) {
        Copy-Item $Source $zip
    } else { throw "Source is neither an https URL nor an existing file: $Source" }

    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
    if ($Sha256 -and $hash -ne $Sha256.ToLower()) { throw "SHA256 mismatch: expected $Sha256, got $hash" }

    # 2. Unpack + read manifest
    $unpacked = Join-Path $work 'x'
    Expand-Archive -Path $zip -DestinationPath $unpacked -Force
    $manifestPath = Join-Path $unpacked 'manifest.json'
    if (-not (Test-Path $manifestPath)) { throw 'Not a valid .mcpb: manifest.json missing.' }
    $manifestText = Get-Content $manifestPath -Raw
    $manifest = $manifestText | ConvertFrom-Json
    if (-not $manifest.name -or -not $manifest.version) { throw 'manifest.json lacks name/version.' }

    # Refuse the exact bug this script exists because of: variables Desktop does not expand.
    $allowed = '^(__dirname|HOME|DESKTOP|DOCUMENTS|DOWNLOADS|pathSeparator|/|user_config\.[A-Za-z0-9_]+)$'
    $bad = [regex]::Matches($manifestText, '\$\{([^}]*)\}') | ForEach-Object { $_.Groups[1].Value } |
        Where-Object { $_ -notmatch $allowed } | Select-Object -Unique
    if ($bad) { throw "Bundle manifest uses variables Claude Desktop does not expand ($($bad -join ', ')). It will not start; ask the author for a rebuilt bundle." }

    $author = if ($manifest.author.name) { $manifest.author.name } else { 'unknown' }
    $slug = { param($s) ($s.ToLower() -replace '[^a-z0-9._-]+', '-').Trim('-') }
    $id = 'local.mcpb.{0}.{1}' -f (& $slug $author), (& $slug $manifest.name)

    # 2b. Runtime prerequisite: bundles launched via uv/uvx need uv on this machine.
    # uv also fetches the right Python itself, so uv is the only thing a normal user needs.
    $launcher = [string]$manifest.server.mcp_config.command
    if ($launcher -in @('uv', 'uvx')) {
        $uvDirs = @("$env:USERPROFILE\.local\bin", "$env:LOCALAPPDATA\Microsoft\WinGet\Links", "$env:USERPROFILE\.cargo\bin")
        $uvOk = [bool](Get-Command uv -ErrorAction SilentlyContinue) -or [bool]($uvDirs | Where-Object { Test-Path (Join-Path $_ 'uv.exe') })
        if ($uvOk) {
            Write-Host 'uv: already installed.'
        } else {
            Write-Host 'uv (the helper that runs this add-on) is not installed - installing it now...'
            if (Get-Command winget -ErrorAction SilentlyContinue) {
                winget install --id astral-sh.uv --exact --silent --accept-package-agreements --accept-source-agreements | Out-Host
            } else {
                Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
            }
            $uvOk = [bool]($uvDirs | Where-Object { Test-Path (Join-Path $_ 'uv.exe') }) -or [bool](Get-Command uv -ErrorAction SilentlyContinue)
            if (-not $uvOk) { throw 'Could not install uv automatically. Install it from https://docs.astral.sh/uv/ and run this again.' }
            Write-Host 'uv installed.' -ForegroundColor Green
        }
    }

    # 3. Place files (upgrade in place)
    $dest = Join-Path $extRoot $id
    New-Item -ItemType Directory -Force -Path $extRoot, $setRoot | Out-Null
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item (Join-Path $unpacked '*') $dest -Recurse -Force

    # 4. Register (backup first, keep every other entry)
    if (Test-Path $regPath) {
        Copy-Item $regPath ("$regPath." + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.bak')
        $reg = Get-Content $regPath -Raw | ConvertFrom-Json
    } else { $reg = [pscustomobject]@{ extensions = [pscustomobject]@{} } }
    if (-not $reg.extensions) { $reg | Add-Member -NotePropertyName extensions -NotePropertyValue ([pscustomobject]@{}) -Force }
    $entry = [pscustomobject]@{
        id = $id; version = [string]$manifest.version; hash = $hash
        installedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
    }
    $reg.extensions | Add-Member -NotePropertyName $id -NotePropertyValue $entry -Force
    [IO.File]::WriteAllText($regPath, ($reg | ConvertTo-Json -Depth 20), $utf8)
    [IO.File]::WriteAllText((Join-Path $setRoot "$id.json"), '{"isEnabled": true}', $utf8)

    Write-Host ''
    Write-Host "Installed $($manifest.name) $($manifest.version) as $id" -ForegroundColor Green
    if (Get-Process -Name claude -ErrorAction SilentlyContinue) {
        Write-Host 'Claude Desktop is running: quit it completely (system tray > Quit) and relaunch to load the extension.' -ForegroundColor Yellow
    } else {
        Write-Host 'Start Claude Desktop to load the extension.' -ForegroundColor Yellow
    }
    Write-Host "If it does not appear under Settings > Extensions, double-click the .mcpb file instead."
} finally {
    Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
}
