param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [ValidateSet("HD", "4K")]
    [string]$Quality = "4K"
)

$ErrorActionPreference = "Stop"

$PackVersion = "v11.0.0"
$BaseUrl = "https://github.com/GhostlyDark/OoT-Reloaded/releases/download/$PackVersion"
$QualityKey = $Quality.ToLowerInvariant()

$Assets = if ($Quality -eq "4K") {
    @(
        @{
            Name = "oot-reloaded-v11.0.0-soh-o2r-4k.7z.001"
            Sha256 = "e73e44a4608f43a8674964a47c2550a81d93c92959b0763895673030b3541ba9"
        },
        @{
            Name = "oot-reloaded-v11.0.0-soh-o2r-4k.7z.002"
            Sha256 = "a9b62c6e5bd4fae1a4467b9a208c3ab9f01f334009ed041e9b78a6ecfe78502c"
        }
    )
} else {
    @(
        @{
            Name = "oot-reloaded-v11.0.0-soh-o2r-hd.7z"
            Sha256 = "a6a551e880739de7f5313888f6cf4eea2eb9d2f04274697fe8ad524ea3c30161"
        }
    )
}

$ModsDir = Join-Path $OutputDir "mods"
$CacheDir = Join-Path $env:LOCALAPPDATA "Shipwright-PTBR\downloads\oot-reloaded\$PackVersion\$QualityKey"
$MarkerName = ".ptbr_oot_reloaded_{0}_{1}.txt" -f $QualityKey, $PackVersion
$MarkerPath = Join-Path $ModsDir $MarkerName

# End-user releases must not depend on CMake or a system-wide 7-Zip install.
# If neither extractor is available, we fetch the official standalone 7zr.exe
# and validate its SHA-256 before using it.
$SevenZipVersion = "26.03"
$SevenZipUrl = "https://github.com/ip7z/7zip/releases/download/26.03/7zr.exe"
$SevenZipSha256 = "ad4c82fadcbdf93c03b4fc440f300509c7d60c5c2f4d183e35d9d70d6957037d"
$SevenZipCacheDir = Join-Path $env:LOCALAPPDATA "Shipwright-PTBR\tools\7zip\$SevenZipVersion"
$SevenZipCachePath = Join-Path $SevenZipCacheDir "7zr.exe"

function Write-Step([string]$Message) {
    Write-Host "[PTBR-GRAPHICS] $Message"
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Download-Asset {
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
        Write-Step "Baixando $(Split-Path $Destination -Leaf)..."
        & $Curl.Source -L --fail --retry 3 --retry-delay 2 -o $Partial $Url
        if ($LASTEXITCODE -ne 0) {
            throw "Falha no download via curl.exe (codigo $LASTEXITCODE)."
        }
    } else {
        Write-Step "Baixando $(Split-Path $Destination -Leaf) via PowerShell..."
        Invoke-WebRequest -Uri $Url -OutFile $Partial
    }

    Move-Item -Path $Partial -Destination $Destination -Force
}

function Ensure-Asset {
    param(
        [hashtable]$Asset
    )

    $Path = Join-Path $CacheDir $Asset.Name
    $Expected = $Asset.Sha256.ToLowerInvariant()

    if (Test-Path $Path) {
        Write-Step "Validando cache: $($Asset.Name)"
        if ((Get-Sha256 $Path) -eq $Expected) {
            Write-Step "Cache valido: $($Asset.Name)"
            return $Path
        }

        Write-Step "Cache invalido; removendo $($Asset.Name)."
        Remove-Item $Path -Force
    }

    Download-Asset -Url "$BaseUrl/$($Asset.Name)" -Destination $Path

    Write-Step "Validando SHA-256: $($Asset.Name)"
    $Actual = Get-Sha256 $Path
    if ($Actual -ne $Expected) {
        Remove-Item $Path -Force
        throw "SHA-256 invalido para $($Asset.Name). Esperado $Expected, recebido $Actual."
    }

    return $Path
}

function Join-ArchiveParts {
    param(
        [string[]]$Parts,
        [string]$Destination
    )

    Write-Step "Unindo as partes do pacote 4K..."
    $Output = [System.IO.File]::Open(
        $Destination,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )

    try {
        foreach ($Part in $Parts) {
            $Input = [System.IO.File]::OpenRead($Part)
            try {
                $Input.CopyTo($Output, 8MB)
            } finally {
                $Input.Dispose()
            }
        }
    } finally {
        $Output.Dispose()
    }
}

function Find-SevenZip {
    foreach ($CommandName in @("7z.exe", "7zr.exe")) {
        $Command = Get-Command $CommandName -ErrorAction SilentlyContinue
        if ($null -ne $Command) {
            return $Command.Source
        }
    }

    $ProgramFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
    $Candidates = @(
        (Join-Path $env:ProgramFiles "7-Zip\7z.exe"),
        (Join-Path $ProgramFilesX86 "7-Zip\7z.exe"),
        $SevenZipCachePath
    )

    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path $Candidate)) {
            return $Candidate
        }
    }

    return $null
}

function Ensure-SevenZip {
    $Existing = Find-SevenZip
    if ($null -ne $Existing) {
        return $Existing
    }

    New-Item -ItemType Directory -Path $SevenZipCacheDir -Force | Out-Null

    if (Test-Path $SevenZipCachePath) {
        $CurrentHash = Get-Sha256 $SevenZipCachePath
        if ($CurrentHash -eq $SevenZipSha256) {
            Write-Step "7zr.exe portatil encontrado no cache."
            return $SevenZipCachePath
        }

        Write-Step "7zr.exe em cache com hash invalido; baixando novamente."
        Remove-Item $SevenZipCachePath -Force
    }

    $Partial = "$SevenZipCachePath.part"
    if (Test-Path $Partial) {
        Remove-Item $Partial -Force
    }

    Write-Step "7-Zip nao encontrado. Baixando 7zr.exe oficial ($SevenZipVersion)..."

    $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -ne $Curl) {
        & $Curl.Source -L --fail --retry 3 --retry-delay 2 -o $Partial $SevenZipUrl
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao baixar o 7zr.exe oficial (codigo $LASTEXITCODE)."
        }
    } else {
        Invoke-WebRequest -Uri $SevenZipUrl -OutFile $Partial
    }

    $ActualHash = Get-Sha256 $Partial
    if ($ActualHash -ne $SevenZipSha256) {
        Remove-Item $Partial -Force -ErrorAction SilentlyContinue
        throw "SHA-256 invalido para 7zr.exe. Esperado $SevenZipSha256, recebido $ActualHash."
    }

    Move-Item -Path $Partial -Destination $SevenZipCachePath -Force
    Write-Step "7zr.exe oficial validado e preparado."
    return $SevenZipCachePath
}

function Expand-SevenZipArchive {
    param(
        [string]$Archive,
        [string]$Destination
    )

    $CMake = Get-Command cmake.exe -ErrorAction SilentlyContinue
    if ($null -ne $CMake) {
        Write-Step "Extraindo texture pack com CMake/libarchive..."
        Push-Location $Destination
        try {
            & $CMake.Source -E tar xvf $Archive | Out-Host
            if ($LASTEXITCODE -eq 0) {
                return
            }
        } finally {
            Pop-Location
        }

        Write-Step "CMake/libarchive nao conseguiu extrair; tentando outros extratores."
    }

    $Tar = Get-Command tar.exe -ErrorAction SilentlyContinue
    if ($null -ne $Tar) {
        Write-Step "Extraindo texture pack com tar.exe..."
        & $Tar.Source -xf $Archive -C $Destination
        if ($LASTEXITCODE -eq 0) {
            return
        }

        Write-Step "tar.exe nao conseguiu extrair; tentando 7-Zip."
    }

    $SevenZip = Ensure-SevenZip

    Write-Step "Extraindo texture pack com 7-Zip..."
    & $SevenZip x $Archive "-o$Destination" -y | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao extrair o texture pack com 7-Zip (codigo $LASTEXITCODE)."
    }
}

function Get-MarkerFiles {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return @()
    }

    return @(
        Get-Content $Path -ErrorAction SilentlyContinue |
            Where-Object { $_ -like "file=*" } |
            ForEach-Object { $_.Substring(5) }
    )
}

function Remove-OtherPtbrTexturePacks {
    $Markers = @(Get-ChildItem -Path $ModsDir -File -Filter ".ptbr_oot_reloaded_*.txt" -ErrorAction SilentlyContinue)

    foreach ($Marker in $Markers) {
        if ($Marker.FullName -eq $MarkerPath) {
            continue
        }

        foreach ($FileName in (Get-MarkerFiles $Marker.FullName)) {
            $InstalledPath = Join-Path $ModsDir $FileName
            if (Test-Path $InstalledPath) {
                Write-Step "Removendo texture pack anterior: $FileName"
                Remove-Item $InstalledPath -Force
            }
        }

        Remove-Item $Marker.FullName -Force -ErrorAction SilentlyContinue
    }
}

Write-Step "Verificando OoT Reloaded $Quality $PackVersion."

New-Item -ItemType Directory -Path $ModsDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null

$InstalledNames = Get-MarkerFiles $MarkerPath
if ($InstalledNames.Count -gt 0) {
    $MissingFiles = @(
        $InstalledNames |
            Where-Object { -not (Test-Path (Join-Path $ModsDir $_)) }
    )

    if ($MissingFiles.Count -eq 0) {
        Write-Step "Texture pack $Quality ja instalado: $($InstalledNames -join ', ')"
        exit 0
    }
}

$ArchiveParts = @()
foreach ($Asset in $Assets) {
    $ArchiveParts += Ensure-Asset $Asset
}

$TempDir = Join-Path $env:TEMP ("Shipwright-PTBR-OoTReloaded-" + [guid]::NewGuid().ToString("N"))

try {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

    if ($Quality -eq "4K") {
        $ArchiveToExtract = Join-Path $TempDir "oot-reloaded-v11.0.0-soh-o2r-4k.7z"
        Join-ArchiveParts -Parts $ArchiveParts -Destination $ArchiveToExtract
    } else {
        $ArchiveToExtract = $ArchiveParts[0]
    }

    Expand-SevenZipArchive -Archive $ArchiveToExtract -Destination $TempDir

    $O2rFiles = @(Get-ChildItem -Path $TempDir -Recurse -File -Filter *.o2r)
    if ($O2rFiles.Count -eq 0) {
        throw "Nenhum arquivo .o2r foi encontrado dentro do pacote $Quality."
    }

    Remove-OtherPtbrTexturePacks

    $InstalledNames = @()
    foreach ($SourceO2r in $O2rFiles) {
        $TargetO2r = Join-Path $ModsDir $SourceO2r.Name
        Write-Step "Instalando $($SourceO2r.Name) em $ModsDir ..."
        Copy-Item -Path $SourceO2r.FullName -Destination $TargetO2r -Force
        $InstalledNames += $SourceO2r.Name
    }

    $MarkerLines = @(
        "version=$PackVersion"
        "quality=$Quality"
    )

    foreach ($Asset in $Assets) {
        $MarkerLines += "archive=$($Asset.Name)"
        $MarkerLines += "archive_sha256=$($Asset.Sha256)"
        $MarkerLines += "source=$BaseUrl/$($Asset.Name)"
    }

    $MarkerLines += $InstalledNames | ForEach-Object { "file=$_" }
    Set-Content -Path $MarkerPath -Value $MarkerLines -Encoding ASCII

    Write-Step "OoT Reloaded $Quality instalado com sucesso: $($InstalledNames -join ', ')"
} finally {
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
