param(
    [string]$Version = "v1.0.0",
    [string]$Repository = "GeraldoCruzeiro/Shipwright-PTBR",
    [switch]$MakePublic
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DistDir = Join-Path $RepoRoot "dist"
$ZipPath = Join-Path $DistDir ("Shipwright-PTBR-{0}-Windows-x64.zip" -f $Version)
$HashPath = "$ZipPath.sha256"
$NotesPath = Join-Path $RepoRoot ("docs\RELEASE_NOTES_{0}.md" -f $Version)

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

# Nao use "gh release view" para testar existencia: quando a release ainda nao
# existe, o GitHub CLI escreve "release not found" em stderr e o Windows
# PowerShell pode transformar isso em NativeCommandError com
# ErrorActionPreference=Stop. Listar as releases e comparar a tag e mais seguro.
$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$ReleaseListJson = & $Gh.Source release list --repo $Repository --limit 100 --json tagName 2>$null
$ReleaseListExitCode = $LASTEXITCODE
$ErrorActionPreference = $PreviousErrorActionPreference

if ($ReleaseListExitCode -ne 0) {
    throw "Nao foi possivel consultar as releases existentes no GitHub. Codigo $ReleaseListExitCode."
}

$ReleaseTags = @()
if (-not [string]::IsNullOrWhiteSpace(($ReleaseListJson | Out-String))) {
    $ReleaseTags = @(
        ($ReleaseListJson | Out-String | ConvertFrom-Json) |
            ForEach-Object { $_.tagName }
    )
}

$ReleaseExists = $ReleaseTags -contains $Version

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

Write-Host "[RELEASE] Release concluida."

if ($MakePublic) {
    Write-Host "[RELEASE] Alterando a visibilidade do repositorio para PUBLIC..."
    & $Gh.Source repo edit $Repository --visibility public --accept-visibility-change-consequences --description "Ocarina of Time no Ship of Harkinian com traducao e dublagem PT-BR, OoT Reloaded 4K e modelos 3DS." --homepage "https://www.shipofharkinian.com/"
    if ($LASTEXITCODE -ne 0) {
        throw "A release foi criada, mas nao foi possivel tornar o repositorio publico."
    }

    foreach ($Topic in @("ship-of-harkinian", "ocarina-of-time", "pt-br", "zelda", "fan-translation")) {
        & $Gh.Source repo edit $Repository --add-topic $Topic
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Nao foi possivel adicionar o topico: $Topic"
        }
    }

    Write-Host "[RELEASE] Repositorio definido como PUBLIC."
}

& $Gh.Source repo view $Repository --json nameWithOwner,visibility,url
& $Gh.Source release view $Version --repo $Repository --web
