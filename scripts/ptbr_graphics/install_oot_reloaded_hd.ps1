param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$PackVersion = "v11.0.0"
$ArchiveName = "oot-reloaded-v11.0.0-soh-o2r-hd.7z"
$DownloadUrl = "https://github.com/GhostlyDark/OoT-Reloaded/releases/download/v11.0.0/$ArchiveName"
$ExpectedSha256 = "a6a551e880739de7f5313888f6cf4eea2eb9d2f04274697fe8ad524ea3c30161"

$ModsDir = Join-Path $OutputDir "mods"
$MarkerPath = Join-Path $ModsDir ".ptbr_oot_reloaded_hd_$PackVersion.txt"
$CacheDir = Join-Path $env:LOCALAPPDATA "Shipwright-PTBR\downloads\oot-reloaded\$PackVersion"
$ArchivePath = Join-Path $CacheDir $ArchiveName

function Write-Step([string]$Message) {
    Write-Host "[PTBR-GRAPHICS] $Message"
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Download-Pack {
    param(
        [string]$Url,
        [string]$Destination
    )

    $Partial = "$Destination.part"
    if (Test-Path $Partial) {
        Remove-Item $Partial -Force
    }

    $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -ne $Curl) {
        Write-Step "Baixando OoT Reloaded HD..."
        & $Curl.Source -L --fail --retry 3 --retry-delay 2 -o $Partial $Url
        if ($LASTEXITCODE -ne 0) {
            throw "Falha no download via curl.exe (codigo $LASTEXITCODE)."
        }
    } else {
        Write-Step "Baixando OoT Reloaded HD via PowerShell..."
        Invoke-WebRequest -Uri $Url -OutFile $Partial
    }

    Move-Item -Path $Partial -Destination $Destination -Force
}

function Find-SevenZip {
    $Command = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($null -ne $Command) {
        return $Command.Source
    }

    $ProgramFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
    $Candidates = @(
        (Join-Path $env:ProgramFiles "7-Zip\7z.exe"),
        (Join-Path $ProgramFilesX86 "7-Zip\7z.exe")
    )

    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path $Candidate)) {
            return $Candidate
        }
    }

    return $null
}

function Expand-SevenZipArchive {
    param(
        [string]$Archive,
        [string]$Destination
    )

    $Tar = Get-Command tar.exe -ErrorAction SilentlyContinue
    if ($null -ne $Tar) {
        Write-Step "Extraindo texture pack com tar.exe..."
        & $Tar.Source -xf $Archive -C $Destination
        if ($LASTEXITCODE -eq 0) {
            return
        }

        Write-Step "tar.exe nao conseguiu extrair o arquivo; tentando 7-Zip."
    }

    $SevenZip = Find-SevenZip
    if ($null -eq $SevenZip) {
        throw "Nao foi possivel extrair o .7z. Instale 7-Zip ou use uma versao do Windows cujo tar.exe suporte 7z."
    }

    Write-Step "Extraindo texture pack com 7-Zip..."
    & $SevenZip x $Archive "-o$Destination" -y | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao extrair o texture pack com 7-Zip (codigo $LASTEXITCODE)."
    }
}

Write-Step "Verificando OoT Reloaded HD $PackVersion."

New-Item -ItemType Directory -Path $ModsDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null

if (Test-Path $MarkerPath) {
    $InstalledName = (Get-Content $MarkerPath -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if ($InstalledName) {
        $InstalledPath = Join-Path $ModsDir $InstalledName
        if (Test-Path $InstalledPath) {
            Write-Step "Texture pack ja instalado: $InstalledName"
            exit 0
        }
    }
}

$NeedDownload = $true
if (Test-Path $ArchivePath) {
    Write-Step "Validando arquivo em cache..."
    $CurrentHash = Get-Sha256 $ArchivePath
    if ($CurrentHash -eq $ExpectedSha256) {
        $NeedDownload = $false
        Write-Step "Cache valido."
    } else {
        Write-Step "Cache invalido; removendo arquivo corrompido ou desatualizado."
        Remove-Item $ArchivePath -Force
    }
}

if ($NeedDownload) {
    Download-Pack -Url $DownloadUrl -Destination $ArchivePath

    Write-Step "Validando SHA-256 do download..."
    $DownloadedHash = Get-Sha256 $ArchivePath
    if ($DownloadedHash -ne $ExpectedSha256) {
        Remove-Item $ArchivePath -Force
        throw "SHA-256 invalido para $ArchiveName. Esperado $ExpectedSha256, recebido $DownloadedHash."
    }
}

$TempDir = Join-Path $env:TEMP ("Shipwright-PTBR-OoTReloaded-" + [guid]::NewGuid().ToString("N"))

try {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    Expand-SevenZipArchive -Archive $ArchivePath -Destination $TempDir

    $O2rFiles = @(Get-ChildItem -Path $TempDir -Recurse -File -Filter *.o2r)
    if ($O2rFiles.Count -ne 1) {
        $Names = ($O2rFiles | ForEach-Object { $_.FullName }) -join "; "
        throw "Esperado exatamente 1 arquivo .o2r no pacote, mas foram encontrados $($O2rFiles.Count). $Names"
    }

    $SourceO2r = $O2rFiles[0]
    $TargetO2r = Join-Path $ModsDir $SourceO2r.Name

    Write-Step "Instalando $($SourceO2r.Name) em $ModsDir ..."
    Copy-Item -Path $SourceO2r.FullName -Destination $TargetO2r -Force

    Set-Content -Path $MarkerPath -Value @(
        $SourceO2r.Name
        "version=$PackVersion"
        "archive_sha256=$ExpectedSha256"
        "source=$DownloadUrl"
    ) -Encoding ASCII

    Write-Step "OoT Reloaded HD instalado com sucesso."
} finally {
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
