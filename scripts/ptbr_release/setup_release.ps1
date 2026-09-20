param(
    [Parameter(Mandatory = $false)]
    [string]$AppDir = (Get-Location).Path,

    [ValidateSet("4K", "HD")]
    [string]$TextureQuality = "4K",

    [switch]$SkipGraphics,

    [switch]$DontLaunch
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "[SHIPWRIGHT-PTBR] $Message"
}

# Defensive normalization for paths received from cmd.exe/native argument parsing.
# Older Windows PowerShell setups can leave surrounding quotes in an argument,
# especially when the original quoted path ends with a backslash.
$AppDir = $AppDir.Trim().Trim('"')

if ([string]::IsNullOrWhiteSpace($AppDir)) {
    throw "Pasta do jogo nao informada."
}

try {
    $AppDir = (Resolve-Path -LiteralPath $AppDir -ErrorAction Stop).Path
} catch {
    throw "Pasta do jogo invalida ou inexistente: '$AppDir'. $($_.Exception.Message)"
}
$ExePath = Join-Path $AppDir "soh.exe"
$GraphicsDir = Join-Path $AppDir "scripts\ptbr_graphics"
$ModsDir = Join-Path $AppDir "mods"
$VoicesDir = Join-Path $AppDir "voices\ptbr"

# Ship of Harkinian nao deve ser executado dentro de pastas sincronizadas pelo
# OneDrive. O proprio SoH bloqueia esse cenario porque a sincronizacao pode
# interferir em arquivos temporarios, configuracoes e assets gerados.
$IsOneDrivePath =
    $AppDir -match '(?i)(^|\\)OneDrive($|\\)' -or
    (-not [string]::IsNullOrWhiteSpace($env:OneDrive) -and
        $AppDir.StartsWith($env:OneDrive, [System.StringComparison]::OrdinalIgnoreCase)) -or
    (-not [string]::IsNullOrWhiteSpace($env:OneDriveConsumer) -and
        $AppDir.StartsWith($env:OneDriveConsumer, [System.StringComparison]::OrdinalIgnoreCase)) -or
    (-not [string]::IsNullOrWhiteSpace($env:OneDriveCommercial) -and
        $AppDir.StartsWith($env:OneDriveCommercial, [System.StringComparison]::OrdinalIgnoreCase))

if ($IsOneDrivePath) {
    $SuggestedDir = Join-Path $env:USERPROFILE "Games\Shipwright-PTBR"

    Write-Host ""
    Write-Host "ERRO: o jogo esta dentro de uma pasta do OneDrive." -ForegroundColor Red
    Write-Host "O Ship of Harkinian nao funciona corretamente em pastas sincronizadas." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Mova a pasta COMPLETA do jogo para um local fora do OneDrive, por exemplo:" -ForegroundColor Yellow
    Write-Host "  $SuggestedDir" -ForegroundColor Cyan
    Write-Host "ou:"
    Write-Host "  C:\Games\Shipwright-PTBR" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Depois execute INSTALAR_E_JOGAR_PTBR.bat novamente na nova pasta."
    throw "Shipwright-PTBR nao pode ser executado dentro do OneDrive."
}

if (-not (Test-Path $ExePath)) {
    throw "soh.exe nao foi encontrado em: $AppDir"
}

Write-Step "Pasta do jogo: $AppDir"

if (-not $SkipGraphics) {
    New-Item -ItemType Directory -Path $ModsDir -Force | Out-Null

    $ReloadedMarker = Join-Path $ModsDir (".ptbr_oot_reloaded_{0}_v11.0.0.txt" -f $TextureQuality.ToLowerInvariant())
    $ModelsMarker = Join-Path $ModsDir ".ptbr_3d_models_v6.txt"

    $ReloadedScript = Join-Path $GraphicsDir "install_oot_reloaded.ps1"
    $ModelsScript = Join-Path $GraphicsDir "install_3d_models.ps1"

    if (-not (Test-Path $ReloadedMarker)) {
        if (-not (Test-Path $ReloadedScript)) {
            throw "Instalador do OoT Reloaded nao encontrado: $ReloadedScript"
        }

        Write-Step "Instalando OoT Reloaded $TextureQuality. A primeira execucao pode baixar varios GB..."
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ReloadedScript -OutputDir $AppDir -Quality $TextureQuality
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar OoT Reloaded $TextureQuality. Codigo $LASTEXITCODE."
        }
    } else {
        Write-Step "OoT Reloaded $TextureQuality ja esta preparado."
    }

    if (-not (Test-Path $ModelsMarker)) {
        if (-not (Test-Path $ModelsScript)) {
            throw "Instalador dos modelos 3D nao encontrado: $ModelsScript"
        }

        Write-Step "Instalando modelos e backgrounds 3DS..."
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ModelsScript -OutputDir $AppDir
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao instalar os modelos 3D. Codigo $LASTEXITCODE."
        }
    } else {
        Write-Step "Pacote de modelos 3D ja esta preparado."
    }
}

$VoiceCount = 0
if (Test-Path $VoicesDir) {
    $VoiceCount = @(Get-ChildItem -Path $VoicesDir -File -Filter "*.wav" -ErrorAction SilentlyContinue).Count
}

if ($VoiceCount -gt 0) {
    Write-Step "Dublagem encontrada: $VoiceCount WAVs."
} else {
    Write-Warning "Nenhum WAV foi encontrado em voices\ptbr. O jogo funcionara, mas sem o pacote de dublagem pronto."
}

$HasOtr = (Test-Path (Join-Path $AppDir "oot.o2r")) -or (Test-Path (Join-Path $AppDir "oot-mq.o2r"))
$RomFiles = @(
    Get-ChildItem -Path $AppDir -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Extension -ieq ".z64" -or
            $_.Extension -ieq ".n64" -or
            $_.Extension -ieq ".v64"
        }
)

if (-not $HasOtr -and $RomFiles.Count -eq 0) {
    Write-Host ""
    Write-Host "ATENCAO:" -ForegroundColor Yellow
    Write-Host "Nenhum oot.o2r e nenhuma ROM foram encontrados nesta pasta."
    Write-Host "Voce precisa fornecer uma copia legal e compativel de Ocarina of Time."
    Write-Host "O Ship of Harkinian fara o processamento localmente."
    Write-Host "Compatibilidade: https://ship.equipment/"
    Write-Host ""
}

if (-not $DontLaunch) {
    Write-Step "Iniciando Shipwright-PTBR..."
    Start-Process -FilePath $ExePath -WorkingDirectory $AppDir
}
