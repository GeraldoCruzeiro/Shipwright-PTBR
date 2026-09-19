param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$ModsDir = Join-Path $OutputDir "mods"
$ManagedDir = Join-Path $ModsDir "9000 - PTBR 3D Models"
$CacheDir = Join-Path $env:LOCALAPPDATA "Shipwright-PTBR\downloads\3d-models"
$MarkerPath = Join-Path $ManagedDir ".ptbr_3d_models_v1.txt"

$DjipiModId = 477979
$EnhancedModId = 578470

function Write-Step([string]$Message) {
    Write-Host "[PTBR-3D] $Message"
}

function Get-GameBananaFiles {
    param([int]$ModId)

    $Uri = "https://gamebanana.com/apiv11/Mod/$ModId?_csvProperties=_aFiles"
    Write-Step "Consultando GameBanana mod $ModId..."
    $Response = Invoke-RestMethod -Uri $Uri -Method Get
    $Files = @($Response._aFiles)

    if ($Files.Count -eq 0) {
        throw "GameBanana nao retornou arquivos para o mod $ModId."
    }

    return $Files
}

function Select-DjipiArchive {
    param([object[]]$Files)

    $Archives = @(
        $Files | Where-Object {
            $_._sFile -match '\.(zip|7z)

function Select-EnhancedArchive {
    param([object[]]$Files)

    $Archives = @(
        $Files | Where-Object {
            $_._sFile -match '\.(zip|7z)$' -and
            $_._sFile -notmatch '(?i)(texture.?only|textures.?only|optional)'
        }
    )

    if ($Archives.Count -eq 0) {
        throw "Nao encontrei um pacote utilizavel do Enhanced 3DS Overhaul no mod $EnhancedModId."
    }

    # The main release is expected to be the largest non-optional archive.
    return ($Archives | Sort-Object _nFilesize -Descending | Select-Object -First 1)
}

function Download-GameBananaFile {
    param(
        [object]$File,
        [string]$ModCacheDir
    )

    New-Item -ItemType Directory -Path $ModCacheDir -Force | Out-Null

    $Destination = Join-Path $ModCacheDir $File._sFile
    $ExpectedSize = 0
    if ($null -ne $File._nFilesize) {
        $ExpectedSize = [int64]$File._nFilesize
    }

    if (Test-Path $Destination) {
        $ActualSize = (Get-Item $Destination).Length
        if ($ExpectedSize -le 0 -or $ActualSize -eq $ExpectedSize) {
            Write-Step "Cache valido: $($File._sFile)"
            return $Destination
        }

        Write-Step "Cache incompleto; baixando novamente: $($File._sFile)"
        Remove-Item $Destination -Force
    }

    $Partial = "$Destination.part"
    if (Test-Path $Partial) {
        Remove-Item $Partial -Force
    }

    Write-Step "Baixando $($File._sFile)..."
    $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -ne $Curl) {
        & $Curl.Source -L --fail --retry 3 --retry-delay 2 -o $Partial $File._sDownloadUrl
        if ($LASTEXITCODE -ne 0) {
            throw "Falha no download de $($File._sFile) via curl.exe (codigo $LASTEXITCODE)."
        }
    } else {
        Invoke-WebRequest -Uri $File._sDownloadUrl -OutFile $Partial
    }

    if ($ExpectedSize -gt 0) {
        $DownloadedSize = (Get-Item $Partial).Length
        if ($DownloadedSize -ne $ExpectedSize) {
            Remove-Item $Partial -Force
            throw "Tamanho invalido para $($File._sFile). Esperado $ExpectedSize, recebido $DownloadedSize."
        }
    }

    Move-Item $Partial $Destination -Force
    return $Destination
}

function Expand-ArchiveSmart {
    param(
        [string]$Archive,
        [string]$Destination
    )

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $Extension = [System.IO.Path]::GetExtension($Archive).ToLowerInvariant()

    if ($Extension -eq ".zip") {
        Write-Step "Extraindo $(Split-Path $Archive -Leaf)..."
        Expand-Archive -Path $Archive -DestinationPath $Destination -Force
        return
    }

    $CMake = Get-Command cmake.exe -ErrorAction SilentlyContinue
    if ($null -eq $CMake) {
        throw "CMake nao encontrado para extrair $(Split-Path $Archive -Leaf)."
    }

    Write-Step "Extraindo $(Split-Path $Archive -Leaf) com CMake/libarchive..."
    Push-Location $Destination
    try {
        & $CMake.Source -E tar xvf $Archive | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao extrair $(Split-Path $Archive -Leaf)."
        }
    } finally {
        Pop-Location
    }
}

function Copy-ModFile {
    param(
        [System.IO.FileInfo]$Source,
        [string]$DestinationDir,
        [string]$Prefix
    )

    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    $TargetName = "$Prefix - $($Source.Name)"
    $TargetPath = Join-Path $DestinationDir $TargetName
    Copy-Item $Source.FullName $TargetPath -Force
    Write-Step "Instalado: $TargetName"
    return $TargetName
}

function Install-DjipiModels {
    param(
        [string]$ExtractedDir,
        [string]$DestinationDir
    )

    $All = @(
        Get-ChildItem -Path $ExtractedDir -Recurse -File |
            Where-Object { $_.Extension -match '^\.(otr|o2r)$' }
    )

    $IncludePattern = '(?i)(Objects? Animals|Objects? Inventory|Objects? Temples|Objects? World|Objects? NPC|Objects? Ennemies|Objects? Enemies|Objects? ARIA)'
    $ExcludePattern = '(?i)(Main Textures|Link.?s Textures|Background|Original N64 HUD|Crescent Moon)'

    $Selected = @(
        $All | Where-Object {
            $_.Name -match $IncludePattern -and
            $_.Name -notmatch $ExcludePattern
        }
    )

    if ($Selected.Count -eq 0) {
        $Names = ($All | ForEach-Object { $_.Name }) -join "; "
        throw "Nao encontrei os modulos 3D esperados do Djipi. Arquivos encontrados: $Names"
    }

    $Installed = @()
    foreach ($File in $Selected) {
        $Installed += Copy-ModFile -Source $File -DestinationDir $DestinationDir -Prefix "1000 Djipi"
    }

    return $Installed
}

function Install-EnhancedOverhaul {
    param(
        [string]$ExtractedDir,
        [string]$DestinationDir
    )

    $Files = @(
        Get-ChildItem -Path $ExtractedDir -Recurse -File |
            Where-Object { $_.Extension -match '^\.(otr|o2r)$' }
    )

    if ($Files.Count -eq 0) {
        throw "Nenhum arquivo OTR/O2R encontrado no Enhanced 3DS Overhaul."
    }

    $Installed = @()
    foreach ($File in $Files) {
        $Installed += Copy-ModFile -Source $File -DestinationDir $DestinationDir -Prefix "2000 Enhanced3DS"
    }

    return $Installed
}

Write-Step "Preparando pacote 3D sem substituir o OoT Reloaded 4K."
New-Item -ItemType Directory -Path $ModsDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null

$DjipiFiles = Get-GameBananaFiles -ModId $DjipiModId
$EnhancedFiles = Get-GameBananaFiles -ModId $EnhancedModId

$DjipiArchiveInfo = Select-DjipiArchive -Files $DjipiFiles
$EnhancedArchiveInfo = Select-EnhancedArchive -Files $EnhancedFiles

Write-Step "Djipi selecionado: $($DjipiArchiveInfo._sFile)"
Write-Step "Enhanced selecionado: $($EnhancedArchiveInfo._sFile)"

$DjipiArchive = Download-GameBananaFile -File $DjipiArchiveInfo -ModCacheDir (Join-Path $CacheDir "djipi")
$EnhancedArchive = Download-GameBananaFile -File $EnhancedArchiveInfo -ModCacheDir (Join-Path $CacheDir "enhanced3ds")

$TempRoot = Join-Path $env:TEMP ("Shipwright-PTBR-3D-" + [guid]::NewGuid().ToString("N"))

try {
    $DjipiTemp = Join-Path $TempRoot "djipi"
    $EnhancedTemp = Join-Path $TempRoot "enhanced"

    Expand-ArchiveSmart -Archive $DjipiArchive -Destination $DjipiTemp
    Expand-ArchiveSmart -Archive $EnhancedArchive -Destination $EnhancedTemp

    # A dedicated directory makes rollback trivial and leaves Reloaded 4K untouched.
    if (Test-Path $ManagedDir) {
        Remove-Item $ManagedDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $ManagedDir -Force | Out-Null

    $Installed = @()
    $Installed += Install-DjipiModels -ExtractedDir $DjipiTemp -DestinationDir $ManagedDir
    $Installed += Install-EnhancedOverhaul -ExtractedDir $EnhancedTemp -DestinationDir $ManagedDir

    $Marker = @(
        "version=1"
        "djipi_mod_id=$DjipiModId"
        "djipi_archive=$($DjipiArchiveInfo._sFile)"
        "enhanced_mod_id=$EnhancedModId"
        "enhanced_archive=$($EnhancedArchiveInfo._sFile)"
        "reloaded_4k_preserved=true"
    )
    $Marker += $Installed | ForEach-Object { "file=$_" }
    Set-Content -Path $MarkerPath -Value $Marker -Encoding UTF8

    Write-Step "Pacote 3D instalado com sucesso."
    Write-Step "OoT Reloaded 4K foi mantido fora da pasta gerenciada e nao foi removido."
} finally {
    if (Test-Path $TempRoot) {
        Remove-Item $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

        }
    )

    # Current main release documented for this mod.
    $Exact = @(
        $Archives | Where-Object {
            $_._sFile -ieq 'djipi_s_3ds_experience_christmas_2024.zip'
        }
    )
    if ($Exact.Count -gt 0) {
        return $Exact[0]
    }

    # GameBanana has renamed/reissued this archive before, so keep a robust
    # fallback instead of depending on punctuation in the display filename.
    $Preferred = @(
        $Archives | Where-Object {
            $_._sFile -notmatch '(?i)skilar' -and
            $_._sFile -match '(?i)(djipi|3ds|experience)'
        }
    )
    if ($Preferred.Count -gt 0) {
        return ($Preferred | Sort-Object _nFilesize -Descending | Select-Object -First 1)
    }

    # Last resort: the main package is substantially larger than the small
    # optional/add-on archives. Skilar is intentionally excluded because the
    # Enhanced 3DS pack handles the principal character models in this branch.
    $Fallback = @(
        $Archives | Where-Object { $_._sFile -notmatch '(?i)skilar' }
    )
    if ($Fallback.Count -gt 0) {
        return ($Fallback | Sort-Object _nFilesize -Descending | Select-Object -First 1)
    }

    $Available = ($Files | ForEach-Object { $_._sFile }) -join '; '
    throw "Nao encontrei o pacote principal do Djipi no mod $DjipiModId. Arquivos retornados: $Available"
}

function Select-EnhancedArchive {
    param([object[]]$Files)

    $Archives = @(
        $Files | Where-Object {
            $_._sFile -match '\.(zip|7z)$' -and
            $_._sFile -notmatch '(?i)(texture.?only|textures.?only|optional)'
        }
    )

    if ($Archives.Count -eq 0) {
        throw "Nao encontrei um pacote utilizavel do Enhanced 3DS Overhaul no mod $EnhancedModId."
    }

    # The main release is expected to be the largest non-optional archive.
    return ($Archives | Sort-Object _nFilesize -Descending | Select-Object -First 1)
}

function Download-GameBananaFile {
    param(
        [object]$File,
        [string]$ModCacheDir
    )

    New-Item -ItemType Directory -Path $ModCacheDir -Force | Out-Null

    $Destination = Join-Path $ModCacheDir $File._sFile
    $ExpectedSize = 0
    if ($null -ne $File._nFilesize) {
        $ExpectedSize = [int64]$File._nFilesize
    }

    if (Test-Path $Destination) {
        $ActualSize = (Get-Item $Destination).Length
        if ($ExpectedSize -le 0 -or $ActualSize -eq $ExpectedSize) {
            Write-Step "Cache valido: $($File._sFile)"
            return $Destination
        }

        Write-Step "Cache incompleto; baixando novamente: $($File._sFile)"
        Remove-Item $Destination -Force
    }

    $Partial = "$Destination.part"
    if (Test-Path $Partial) {
        Remove-Item $Partial -Force
    }

    Write-Step "Baixando $($File._sFile)..."
    $Curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($null -ne $Curl) {
        & $Curl.Source -L --fail --retry 3 --retry-delay 2 -o $Partial $File._sDownloadUrl
        if ($LASTEXITCODE -ne 0) {
            throw "Falha no download de $($File._sFile) via curl.exe (codigo $LASTEXITCODE)."
        }
    } else {
        Invoke-WebRequest -Uri $File._sDownloadUrl -OutFile $Partial
    }

    if ($ExpectedSize -gt 0) {
        $DownloadedSize = (Get-Item $Partial).Length
        if ($DownloadedSize -ne $ExpectedSize) {
            Remove-Item $Partial -Force
            throw "Tamanho invalido para $($File._sFile). Esperado $ExpectedSize, recebido $DownloadedSize."
        }
    }

    Move-Item $Partial $Destination -Force
    return $Destination
}

function Expand-ArchiveSmart {
    param(
        [string]$Archive,
        [string]$Destination
    )

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $Extension = [System.IO.Path]::GetExtension($Archive).ToLowerInvariant()

    if ($Extension -eq ".zip") {
        Write-Step "Extraindo $(Split-Path $Archive -Leaf)..."
        Expand-Archive -Path $Archive -DestinationPath $Destination -Force
        return
    }

    $CMake = Get-Command cmake.exe -ErrorAction SilentlyContinue
    if ($null -eq $CMake) {
        throw "CMake nao encontrado para extrair $(Split-Path $Archive -Leaf)."
    }

    Write-Step "Extraindo $(Split-Path $Archive -Leaf) com CMake/libarchive..."
    Push-Location $Destination
    try {
        & $CMake.Source -E tar xvf $Archive | Out-Host
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao extrair $(Split-Path $Archive -Leaf)."
        }
    } finally {
        Pop-Location
    }
}

function Copy-ModFile {
    param(
        [System.IO.FileInfo]$Source,
        [string]$DestinationDir,
        [string]$Prefix
    )

    New-Item -ItemType Directory -Path $DestinationDir -Force | Out-Null
    $TargetName = "$Prefix - $($Source.Name)"
    $TargetPath = Join-Path $DestinationDir $TargetName
    Copy-Item $Source.FullName $TargetPath -Force
    Write-Step "Instalado: $TargetName"
    return $TargetName
}

function Install-DjipiModels {
    param(
        [string]$ExtractedDir,
        [string]$DestinationDir
    )

    $All = @(
        Get-ChildItem -Path $ExtractedDir -Recurse -File |
            Where-Object { $_.Extension -match '^\.(otr|o2r)$' }
    )

    $IncludePattern = '(?i)(Objects? Animals|Objects? Inventory|Objects? Temples|Objects? NPC|Objects? Ennemies|Objects? Enemies|Objects? ARIA)'
    $ExcludePattern = '(?i)(Main Textures|Link.?s Textures|Background|Objects? World|Original N64 HUD|Crescent Moon)'

    $Selected = @(
        $All | Where-Object {
            $_.Name -match $IncludePattern -and
            $_.Name -notmatch $ExcludePattern
        }
    )

    if ($Selected.Count -eq 0) {
        $Names = ($All | ForEach-Object { $_.Name }) -join "; "
        throw "Nao encontrei os modulos 3D esperados do Djipi. Arquivos encontrados: $Names"
    }

    $Installed = @()
    foreach ($File in $Selected) {
        $Installed += Copy-ModFile -Source $File -DestinationDir $DestinationDir -Prefix "1000 Djipi"
    }

    return $Installed
}

function Install-EnhancedOverhaul {
    param(
        [string]$ExtractedDir,
        [string]$DestinationDir
    )

    $Files = @(
        Get-ChildItem -Path $ExtractedDir -Recurse -File |
            Where-Object { $_.Extension -match '^\.(otr|o2r)$' }
    )

    if ($Files.Count -eq 0) {
        throw "Nenhum arquivo OTR/O2R encontrado no Enhanced 3DS Overhaul."
    }

    $Installed = @()
    foreach ($File in $Files) {
        $Installed += Copy-ModFile -Source $File -DestinationDir $DestinationDir -Prefix "2000 Enhanced3DS"
    }

    return $Installed
}

Write-Step "Preparando pacote 3D sem substituir o OoT Reloaded 4K."
New-Item -ItemType Directory -Path $ModsDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null

$DjipiFiles = Get-GameBananaFiles -ModId $DjipiModId
$EnhancedFiles = Get-GameBananaFiles -ModId $EnhancedModId

$DjipiArchiveInfo = Select-DjipiArchive -Files $DjipiFiles
$EnhancedArchiveInfo = Select-EnhancedArchive -Files $EnhancedFiles

Write-Step "Djipi selecionado: $($DjipiArchiveInfo._sFile)"
Write-Step "Enhanced selecionado: $($EnhancedArchiveInfo._sFile)"

$DjipiArchive = Download-GameBananaFile -File $DjipiArchiveInfo -ModCacheDir (Join-Path $CacheDir "djipi")
$EnhancedArchive = Download-GameBananaFile -File $EnhancedArchiveInfo -ModCacheDir (Join-Path $CacheDir "enhanced3ds")

$TempRoot = Join-Path $env:TEMP ("Shipwright-PTBR-3D-" + [guid]::NewGuid().ToString("N"))

try {
    $DjipiTemp = Join-Path $TempRoot "djipi"
    $EnhancedTemp = Join-Path $TempRoot "enhanced"

    Expand-ArchiveSmart -Archive $DjipiArchive -Destination $DjipiTemp
    Expand-ArchiveSmart -Archive $EnhancedArchive -Destination $EnhancedTemp

    # A dedicated directory makes rollback trivial and leaves Reloaded 4K untouched.
    if (Test-Path $ManagedDir) {
        Remove-Item $ManagedDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $ManagedDir -Force | Out-Null

    $Installed = @()
    $Installed += Install-DjipiModels -ExtractedDir $DjipiTemp -DestinationDir $ManagedDir
    $Installed += Install-EnhancedOverhaul -ExtractedDir $EnhancedTemp -DestinationDir $ManagedDir

    $Marker = @(
        "version=1"
        "djipi_mod_id=$DjipiModId"
        "djipi_archive=$($DjipiArchiveInfo._sFile)"
        "enhanced_mod_id=$EnhancedModId"
        "enhanced_archive=$($EnhancedArchiveInfo._sFile)"
        "reloaded_4k_preserved=true"
    )
    $Marker += $Installed | ForEach-Object { "file=$_" }
    Set-Content -Path $MarkerPath -Value $Marker -Encoding UTF8

    Write-Step "Pacote 3D instalado com sucesso."
    Write-Step "OoT Reloaded 4K foi mantido fora da pasta gerenciada e nao foi removido."
} finally {
    if (Test-Path $TempRoot) {
        Remove-Item $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
