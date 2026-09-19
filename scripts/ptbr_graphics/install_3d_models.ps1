param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

$ModsDir = Join-Path $OutputDir "mods"
$CacheDir = Join-Path $env:LOCALAPPDATA "Shipwright-PTBR\downloads\3d-models"
$MarkerPath = Join-Path $ModsDir ".ptbr_3d_models_v5.txt"
$LegacyManagedDir = Join-Path $ModsDir "9000 - PTBR 3D Models"

$DjipiModId = 477979
$LinkModId = 475743

function Write-Step([string]$Message) {
    Write-Host "[PTBR-3D] $Message"
}

function Find-GameBananaFileRecords {
    param([object]$Node)

    $Results = @()

    if ($null -eq $Node) {
        return $Results
    }

    if ($Node -is [string] -or
        $Node -is [ValueType]) {
        return $Results
    }

    $PropertyNames = @($Node.PSObject.Properties.Name)

    if ($PropertyNames -contains "_sFile" -and
        $PropertyNames -contains "_sDownloadUrl") {
        return @($Node)
    }

    if ($Node -is [System.Collections.IEnumerable]) {
        foreach ($Item in $Node) {
            $Results += Find-GameBananaFileRecords -Node $Item
        }

        if ($Results.Count -gt 0) {
            return $Results
        }
    }

    foreach ($Property in @($Node.PSObject.Properties)) {
        $Results += Find-GameBananaFileRecords -Node $Property.Value
    }

    return $Results
}

function Get-GameBananaFiles {
    param([int]$ModId)

    $Headers = @{
        "Accept" = "application/json"
        "User-Agent" = "Shipwright-PTBR/1.0"
    }

    $Fields = [uri]::EscapeDataString("Files().aFiles()")
    $Uri = "https://api.gamebanana.com/Core/Item/Data?itemtype=Mod&itemid=$ModId&fields=$Fields&return_keys=1"

    Write-Step "Consultando API oficial GameBanana para o mod $ModId..."

    try {
        $Response = Invoke-RestMethod -Uri $Uri -Method Get -Headers $Headers
    } catch {
        throw "Falha ao consultar a API oficial do GameBanana para o mod $ModId. $($_.Exception.Message)"
    }

    $Files = @(Find-GameBananaFileRecords -Node $Response)

    if ($Files.Count -eq 0) {
        $JsonPreview = ""
        try {
            $JsonPreview = ($Response | ConvertTo-Json -Depth 8 -Compress)
            if ($JsonPreview.Length -gt 1200) {
                $JsonPreview = $JsonPreview.Substring(0, 1200)
            }
        } catch {
            $JsonPreview = "<nao foi possivel serializar a resposta>"
        }

        throw "A API oficial respondeu, mas nenhum arquivo utilizavel foi encontrado para o mod $ModId. Resposta: $JsonPreview"
    }

    $UniqueFiles = @(
        $Files |
            Group-Object _sFile |
            ForEach-Object { $_.Group[0] }
    )

    $Names = ($UniqueFiles | ForEach-Object { $_._sFile }) -join "; "
    Write-Step "Arquivos encontrados no mod $($ModId): $Names"

    return $UniqueFiles
}

function Test-ArchiveName {
    param([string]$Name)

    if ([string]::IsNullOrWhiteSpace($Name)) {
        return $false
    }

    $Lower = $Name.ToLowerInvariant()
    return $Lower.EndsWith(".zip") -or $Lower.EndsWith(".7z")
}

function Select-DjipiMainArchive {
    param([object[]]$Files)

    $Candidates = @(
        $Files | Where-Object {
            (Test-ArchiveName $_._sFile) -and
            $_._sFile -notmatch "(?i)skilar" -and
            $_._sFile -notmatch "(?i)optional"
        }
    )

    if ($Candidates.Count -eq 0) {
        $Available = ($Files | ForEach-Object { $_._sFile }) -join "; "
        throw "Nao encontrei o pacote principal do Djipi. Arquivos retornados: $Available"
    }

    $Named = @(
        $Candidates | Where-Object {
            $_._sFile -match "(?i)djipi" -and
            $_._sFile -match "(?i)3ds"
        }
    )

    if ($Named.Count -gt 0) {
        return ($Named | Sort-Object _nFilesize -Descending | Select-Object -First 1)
    }

    return ($Candidates | Sort-Object _nFilesize -Descending | Select-Object -First 1)
}

function Select-LinkArchive {
    param([object[]]$Files)

    $Candidates = @(
        $Files | Where-Object {
            (Test-ArchiveName $_._sFile) -and
            $_._sFile -notmatch "(?i)upscaled" -and
            $_._sFile -notmatch "(?i)mm_link"
        }
    )

    $Preferred = @(
        $Candidates | Where-Object {
            $_._sFile -match "(?i)3ds_link" -and
            $_._sFile -match "(?i)adult" -and
            $_._sFile -match "(?i)child"
        }
    )

    if ($Preferred.Count -gt 0) {
        return ($Preferred | Sort-Object _nFilesize -Descending | Select-Object -First 1)
    }

    if ($Candidates.Count -gt 0) {
        return ($Candidates | Sort-Object _nFilesize -Descending | Select-Object -First 1)
    }

    $Available = ($Files | ForEach-Object { $_._sFile }) -join "; "
    throw "Nao encontrei o pacote 3DS Adult/Young Link. Arquivos retornados: $Available"
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
            throw "Falha no download de $($File._sFile) via curl.exe. Codigo $LASTEXITCODE."
        }
    } else {
        Invoke-WebRequest -Uri $File._sDownloadUrl -OutFile $Partial
    }

    if ($ExpectedSize -gt 0) {
        $DownloadedSize = (Get-Item $Partial).Length
        if ($DownloadedSize -ne $ExpectedSize) {
            Remove-Item $Partial -Force
            throw "Download incompleto de $($File._sFile). Esperado $ExpectedSize bytes, recebido $DownloadedSize."
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

function Get-ModFiles {
    param([string]$Root)

    return @(
        Get-ChildItem -Path $Root -Recurse -File |
            Where-Object {
                $_.Extension -ieq ".otr" -or
                $_.Extension -ieq ".o2r"
            }
    )
}

function Select-DjipiModelFiles {
    param([string]$Root)

    $All = Get-ModFiles $Root

    $Selected = @(
        $All | Where-Object {
            $Name = $_.Name

            $IsWantedModule =
                $Name -match "(?i)animal" -or
                $Name -match "(?i)inventory" -or
                $Name -match "(?i)temple" -or
                $Name -match "(?i)npc" -or
                $Name -match "(?i)enemy" -or
                $Name -match "(?i)ennemi" -or
                $Name -match "(?i)ennemy"

            $ConflictsWithReloaded =
                $Name -match "(?i)main textures" -or
                $Name -match "(?i)link.*texture" -or
                $Name -match "(?i)background" -or
                $Name -match "(?i)object.*world" -or
                $Name -match "(?i)scene" -or
                $Name -match "(?i)optional" -or
                $Name -match "(?i)aria" -or
                $Name -match "(?i)crescent"

            $IsWantedModule -and -not $ConflictsWithReloaded
        }
    )

    if ($Selected.Count -eq 0) {
        $Available = ($All | ForEach-Object { $_.Name }) -join "; "
        throw "Nenhum modulo 3D seguro do Djipi foi encontrado. Arquivos encontrados: $Available"
    }

    return $Selected
}

function Copy-ModelMod {
    param(
        [System.IO.FileInfo]$Source,
        [string]$Label
    )

    $SafeLabel = $Label.Replace(" ", "_")
    $TargetName = "ZZZ_PTBR_3D_{0}_{1}" -f $SafeLabel, $Source.Name
    $TargetPath = Join-Path $ModsDir $TargetName

    Copy-Item $Source.FullName $TargetPath -Force
    Write-Step "Instalado: $TargetName"
    return $TargetName
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

function Remove-PreviousPtbr3D {
    foreach ($OldMarker in @(Get-ChildItem -Path $ModsDir -File -Filter ".ptbr_3d_models_*.txt" -ErrorAction SilentlyContinue)) {
        foreach ($FileName in (Get-MarkerFiles $OldMarker.FullName)) {
            $Path = Join-Path $ModsDir $FileName
            if (Test-Path $Path) {
                Remove-Item $Path -Force
            }
        }

        Remove-Item $OldMarker.FullName -Force -ErrorAction SilentlyContinue
    }

    foreach ($LegacyFile in @(Get-ChildItem -Path $ModsDir -File -Filter "ZZZ_PTBR_3D_*" -ErrorAction SilentlyContinue)) {
        Remove-Item $LegacyFile.FullName -Force
    }

    if (Test-Path $LegacyManagedDir) {
        Remove-Item $LegacyManagedDir -Recurse -Force
    }
}

Write-Step "Preparando modelos 3D mantendo OoT Reloaded 4K."

New-Item -ItemType Directory -Path $ModsDir -Force | Out-Null
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null

$AlreadyInstalled = Get-MarkerFiles $MarkerPath
if ($AlreadyInstalled.Count -gt 0) {
    $Missing = @(
        $AlreadyInstalled |
            Where-Object { -not (Test-Path (Join-Path $ModsDir $_)) }
    )

    if ($Missing.Count -eq 0) {
        Write-Step "Pacote 3D v5 ja instalado."
        exit 0
    }
}

$DjipiFiles = Get-GameBananaFiles -ModId $DjipiModId
$LinkFiles = Get-GameBananaFiles -ModId $LinkModId

$DjipiArchiveInfo = Select-DjipiMainArchive -Files $DjipiFiles
$LinkArchiveInfo = Select-LinkArchive -Files $LinkFiles

Write-Step "Djipi selecionado: $($DjipiArchiveInfo._sFile)"
Write-Step "Link 3DS selecionado: $($LinkArchiveInfo._sFile)"

$DjipiArchive = Download-GameBananaFile -File $DjipiArchiveInfo -ModCacheDir (Join-Path $CacheDir "djipi")
$LinkArchive = Download-GameBananaFile -File $LinkArchiveInfo -ModCacheDir (Join-Path $CacheDir "link3ds")

$TempRoot = Join-Path $env:TEMP ("Shipwright-PTBR-3D-" + [guid]::NewGuid().ToString("N"))

try {
    $DjipiTemp = Join-Path $TempRoot "djipi"
    $LinkTemp = Join-Path $TempRoot "link"

    Expand-ArchiveSmart -Archive $DjipiArchive -Destination $DjipiTemp
    Expand-ArchiveSmart -Archive $LinkArchive -Destination $LinkTemp

    $DjipiModels = Select-DjipiModelFiles -Root $DjipiTemp
    $LinkModels = Get-ModFiles -Root $LinkTemp

    if ($LinkModels.Count -eq 0) {
        throw "Nenhum arquivo OTR/O2R encontrado no pacote 3DS Adult/Young Link."
    }

    Remove-PreviousPtbr3D

    $Installed = @()

    foreach ($File in $DjipiModels) {
        $Installed += Copy-ModelMod -Source $File -Label "Djipi"
    }

    foreach ($File in $LinkModels) {
        $Installed += Copy-ModelMod -Source $File -Label "Link"
    }

    $Marker = @(
        "version=5"
        "djipi_mod_id=$DjipiModId"
        "djipi_archive=$($DjipiArchiveInfo._sFile)"
        "link_mod_id=$LinkModId"
        "link_archive=$($LinkArchiveInfo._sFile)"
        "reloaded_4k_preserved=true"
        "excluded=main_textures,link_textures,background,world,scenes,optional,aria,crescent"
    )

    $Marker += $Installed | ForEach-Object { "file=$_" }
    Set-Content -Path $MarkerPath -Value $Marker -Encoding UTF8

    Write-Step "Modelos 3D instalados com sucesso."
    Write-Step "OoT Reloaded 4K foi preservado como base; apenas texturas 3DS pareadas de animals/inventory/temples/NPC/enemies foram adicionadas."
} finally {
    if (Test-Path $TempRoot) {
        Remove-Item $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
