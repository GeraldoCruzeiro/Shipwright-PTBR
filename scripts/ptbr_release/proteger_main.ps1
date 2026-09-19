param(
    [string]$Repository = "GeraldoCruzeiro/Shipwright-PTBR",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

$Gh = Get-Command gh.exe -ErrorAction SilentlyContinue
if ($null -eq $Gh) {
    throw "GitHub CLI (gh) nao foi encontrado. Instale em https://cli.github.com/ e execute 'gh auth login'."
}

& $Gh.Source auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI nao esta autenticado. Execute: gh auth login"
}

Write-Host "[GITHUB] Protegendo a branch $Branch de $Repository..."

$Protection = @{
    required_status_checks = $null
    enforce_admins = $false
    required_pull_request_reviews = @{
        dismiss_stale_reviews = $true
        require_code_owner_reviews = $false
        required_approving_review_count = 1
        require_last_push_approval = $false
        bypass_pull_request_allowances = @{
            users = @()
            teams = @()
            apps = @()
        }
    }
    restrictions = $null
    required_linear_history = $false
    allow_force_pushes = $false
    allow_deletions = $false
    block_creations = $false
    required_conversation_resolution = $true
    lock_branch = $false
    allow_fork_syncing = $true
}

$TempJson = [System.IO.Path]::GetTempFileName()

try {
    $Protection | ConvertTo-Json -Depth 8 | Set-Content -Path $TempJson -Encoding UTF8

    & $Gh.Source api --method PUT -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "repos/$Repository/branches/$Branch/protection" --input $TempJson

    if ($LASTEXITCODE -ne 0) {
        throw "Nao foi possivel aplicar a protecao da branch. Codigo $LASTEXITCODE."
    }
} finally {
    Remove-Item $TempJson -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "[GITHUB] Protecao aplicada:"
Write-Host "  - colaboradores nao podem alterar a main sem Pull Request;"
Write-Host "  - exige 1 aprovacao antes do merge para usuarios sujeitos a regra;"
Write-Host "  - novas alteracoes invalidam aprovacoes antigas;"
Write-Host "  - conversas do PR precisam ser resolvidas;"
Write-Host "  - force push bloqueado;"
Write-Host "  - exclusao da main bloqueada;"
Write-Host "  - administradores continuam com possibilidade de bypass."
Write-Host ""
Write-Host "[GITHUB] Consultando estado atual..."

& $Gh.Source api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "repos/$Repository/branches/$Branch/protection" --jq '{url: .url, required_pull_request_reviews: .required_pull_request_reviews, enforce_admins: .enforce_admins, required_conversation_resolution: .required_conversation_resolution, allow_force_pushes: .allow_force_pushes, allow_deletions: .allow_deletions}'
