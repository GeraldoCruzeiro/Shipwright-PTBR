param(
    [string]$Version = "v1.0.0",
    [string]$ReleaseDir,
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

if ([string]::IsNullOrWhiteSpace($ReleaseDir)) {
    $ReleaseDir = Join-Path $RepoRoot "x64\Release"
}

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $RepoRoot "dist"
}

if (-not (Test-Path $ReleaseDir)) {
    throw "Pasta Release nao encontrada: $ReleaseDir"
}

$Exe = Join-Path $ReleaseDir "soh.exe"
$SohO2r = Join-Path $ReleaseDir "soh.o2r"
$VoiceDir = Join-Path $ReleaseDir "voices\ptbr"

if (-not (Test-Path $Exe)) {
    throw "soh.exe nao encontrado. Compile Release x64 antes de empacotar."
}

if (-not (Test-Path $SohO2r)) {
    throw "soh.o2r nao encontrado em $ReleaseDir."
}

$VoiceCount = 0
if (Test-Path $VoiceDir) {
    $VoiceCount = @(Get-ChildItem -Path $VoiceDir -File -Filter "*.wav").Count
}

if ($VoiceCount -lt 2500) {
    throw "Pacote de dublagem parece incompleto: encontrados $VoiceCount WAVs. Esperado pelo menos 2500."
}

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$SafeVersion = $Version.Trim()
$PackageName = "Shipwright-PTBR-$SafeVersion-Windows-x64"
$Stage = Join-Path $OutputDir $PackageName
$ZipPath = Join-Path $OutputDir "$PackageName.zip"
$HashPath = "$ZipPath.sha256"

if (Test-Path $Stage) {
    Remove-Item $Stage -Recurse -Force
}
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}
if (Test-Path $HashPath) {
    Remove-Item $HashPath -Force
}

New-Item -ItemType Directory -Path $Stage -Force | Out-Null

Write-Host "[RELEASE] Copiando build local..."
Copy-Item -Path (Join-Path $ReleaseDir "*") -Destination $Stage -Recurse -Force

# Nunca redistribuir ROM, OTR extraido da ROM, saves ou configuracoes pessoais.
$ForbiddenFiles = @(
    "oot.o2r",
    "oot-mq.o2r",
    "shipofharkinian.json",
    "shipofharkinian.ini",
    "imgui.ini",
    "timesplitdata.json",
    ".env"
)

foreach ($Name in $ForbiddenFiles) {
    $Path = Join-Path $Stage $Name
    if (Test-Path $Path) {
        Remove-Item $Path -Force
    }
}

Get-ChildItem -Path $Stage -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -ieq ".z64" -or
        $_.Extension -ieq ".n64" -or
        $_.Extension -ieq ".v64" -or
        $_.Extension -ieq ".sav" -or
        $_.Extension -ieq ".sra" -or
        $_.Extension -ieq ".log" -or
        $_.Extension -ieq ".bak"
    } |
    Remove-Item -Force

# Mods de terceiros sao baixados das fontes originais no primeiro inicio.
$ModsPath = Join-Path $Stage "mods"
if (Test-Path $ModsPath) {
    Remove-Item $ModsPath -Recurse -Force
}

foreach ($Folder in @("logs", "screenshots")) {
    $Path = Join-Path $Stage $Folder
    if (Test-Path $Path) {
        Remove-Item $Path -Recurse -Force
    }
}

# Arquivos publicos para instalacao e documentacao.
Copy-Item (Join-Path $RepoRoot "INSTALAR_E_JOGAR_PTBR.bat") $Stage -Force
Copy-Item (Join-Path $RepoRoot "README.md") $Stage -Force
Copy-Item (Join-Path $RepoRoot "NOTICE.md") $Stage -Force

$DocsDest = Join-Path $Stage "docs"
New-Item -ItemType Directory -Path $DocsDest -Force | Out-Null
Copy-Item (Join-Path $RepoRoot "docs\PTBR_CREDITOS_E_DIREITOS.md") $DocsDest -Force

$GraphicsDest = Join-Path $Stage "scripts\ptbr_graphics"
New-Item -ItemType Directory -Path $GraphicsDest -Force | Out-Null
Copy-Item (Join-Path $RepoRoot "scripts\ptbr_graphics\install_oot_reloaded.ps1") $GraphicsDest -Force
Copy-Item (Join-Path $RepoRoot "scripts\ptbr_graphics\install_3d_models.ps1") $GraphicsDest -Force

$ReleaseScriptDest = Join-Path $Stage "scripts\ptbr_release"
New-Item -ItemType Directory -Path $ReleaseScriptDest -Force | Out-Null
Copy-Item (Join-Path $RepoRoot "scripts\ptbr_release\setup_release.ps1") $ReleaseScriptDest -Force

# Auditoria final.
$ForbiddenAudit = @(
    Get-ChildItem -Path $Stage -Recurse -File |
        Where-Object {
            $_.Name -ieq "oot.o2r" -or
            $_.Name -ieq "oot-mq.o2r" -or
            $_.Extension -ieq ".z64" -or
            $_.Extension -ieq ".n64" -or
            $_.Extension -ieq ".v64" -or
            $_.Name -ieq ".env"
        }
)

if ($ForbiddenAudit.Count -gt 0) {
    $List = ($ForbiddenAudit | ForEach-Object { $_.FullName }) -join "; "
    throw "Auditoria falhou: arquivos proibidos ainda estao no pacote: $List"
}

$PackagedVoiceCount = @(Get-ChildItem -Path (Join-Path $Stage "voices\ptbr") -File -Filter "*.wav").Count
Write-Host "[RELEASE] Dublagem incluida: $PackagedVoiceCount WAVs."
Write-Host "[RELEASE] Criando ZIP..."

Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $ZipPath -CompressionLevel Optimal

$Hash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $([System.IO.Path]::GetFileName($ZipPath))" | Set-Content -Path $HashPath -Encoding ASCII

Remove-Item $Stage -Recurse -Force

Write-Host ""
Write-Host "[RELEASE] Pacote pronto:"
Write-Host "  $ZipPath"
Write-Host "  $HashPath"
Write-Host "[RELEASE] SHA-256: $Hash"
