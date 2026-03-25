# GeekNews Daily Pipeline - Obsidian Vault 동기화 스크립트
# 이 스크립트는 repo의 output/ 폴더에서 최신 md 파일을 Obsidian Vault로 복사합니다.
# 실행 전 git pull을 수행하여 GitHub Actions가 생성한 최신 파일을 가져옵니다.

param(
    [string]$VaultPath = "$env:USERPROFILE\Documents\Obsidian Vault",
    [string]$SubFolder = "GeekNews"
)

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OutputDir = Join-Path $RepoRoot "geeknews-daily-pipeline\output"

# 1. Git pull to get latest from GitHub Actions
Write-Host "Pulling latest from remote..."
Push-Location $RepoRoot
git pull --quiet 2>$null
Pop-Location

# 2. Ensure target folder exists in Obsidian Vault
$TargetDir = Join-Path $VaultPath $SubFolder
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Host "Created folder: $TargetDir"
}

# 3. Copy new md files
$copied = 0
Get-ChildItem -Path $OutputDir -Filter "*.md" -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $TargetDir $_.Name
    if (-not (Test-Path $dest) -or ($_.LastWriteTime -gt (Get-Item $dest).LastWriteTime)) {
        Copy-Item $_.FullName $dest -Force
        Write-Host "Synced: $($_.Name)"
        $copied++
    }
}

if ($copied -eq 0) {
    Write-Host "No new files to sync."
} else {
    Write-Host "Synced $copied file(s) to $TargetDir"
}
