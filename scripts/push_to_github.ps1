# Push enterprise-rag to GitHub (run after: gh auth login)
# Usage: .\scripts\push_to_github.ps1

$ErrorActionPreference = "Stop"
$repoName = "enterprise-rag-intelligence-platform"
$owner = "Lucifer7355"

Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) not found. Install: winget install GitHub.cli"
}

$auth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Run: gh auth login" -ForegroundColor Yellow
    gh auth login
}

$exists = gh repo view "$owner/$repoName" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating public repo $owner/$repoName ..."
    gh repo create $repoName --public --source=. --remote=origin --description "Enterprise RAG with RBAC hybrid retrieval, knowledge graph, JWT auth, and observability"
} else {
    Write-Host "Repo exists. Adding remote if needed ..."
    if (-not (git remote get-url origin 2>$null)) {
        git remote add origin "https://github.com/$owner/$repoName.git"
    }
}

git push -u origin main
Write-Host ""
Write-Host "Done: https://github.com/$owner/$repoName" -ForegroundColor Green
