param(
    [string]$Version = "v1.0.0",
    [string]$Repository = "GeraldoCruzeiro/Shipwright-PTBR"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DistDir = Join-Path $RepoRoot "dist"
$ZipPath = Join-Path $DistDir ("Shipwright-PTBR-{0}-Windows-x64.zip" -f $Version)
$HashPath = "$ZipPath.sha256"
$NotesPath = Join-Path $RepoRoot "docs\RELEASE_NOTES_v1.0.0.md"

$Gh = Get-Command gh.exe -ErrorAction SilentlyContinue
if ($null -eq $Gh) {
    throw "GitHub CLI (gh) nao foi encontrado. Instale em https://cli.github.com/ e execute 'gh auth login'."
}

& $Gh.Source auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI nao esta autenticado. Execute: gh auth login"
}

if (-not (Test-Path $ZipPath) -or -not (Test-Path $HashPath)) {
    Write-Host "[RELEASE] Pacote ainda nao existe. Gerando..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "package_windows.ps1") -Version $Version
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao gerar o pacote Windows."
    }
}

if (-not (Test-Path $NotesPath)) {
    throw "Notas da release nao encontradas: $NotesPath"
}

Write-Host "[RELEASE] Criando release $Version em $Repository..."

& $Gh.Source release view $Version --repo $Repository *> $null
$ReleaseExists = $LASTEXITCODE -eq 0

if ($ReleaseExists) {
    Write-Host "[RELEASE] A tag/release ja existe. Enviando os arquivos com --clobber..."
    & $Gh.Source release upload $Version $ZipPath $HashPath --repo $Repository --clobber
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao atualizar os assets da release."
    }
} else {
    & $Gh.Source release create $Version $ZipPath $HashPath --repo $Repository --target main --title "Shipwright-PTBR $Version" --notes-file $NotesPath
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar a release no GitHub."
    }
}

Write-Host "[RELEASE] Publicacao concluida."
& $Gh.Source release view $Version --repo $Repository --web
