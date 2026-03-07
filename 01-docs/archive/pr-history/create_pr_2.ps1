#!/usr/bin/env pwsh
# GitHub PR #2 Creator - Automated Script
# Purpose: Create PR for lousardzag feat/migration-core-central-package branch
# Requires: GitHub CLI (gh) installed, or manual intervention with generated templates

param(
    [switch]$UseWebUI = $false,
    [switch]$DryRun = $false
)

Write-Host "=== PR #2 Creation Script ===" -ForegroundColor Cyan
Write-Host "Repository: RVogel101/lousardzag"
Write-Host "Branch: feat/migration-core-central-package"
Write-Host "Base: main"
Write-Host ""

# Define PR details
$PR_TITLE = "feat(extraction): wire lousardzag to consume central package via adapter pattern"
$PR_LABELS = @("refactor", "extraction", "migration", "adapter")
$REPO = "RVogel101/lousardzag"
$BASE_BRANCH = "main"
$HEAD_BRANCH = "feat/migration-core-central-package"

# Read PR description from file
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PR_DESC_FILE = Join-Path $SCRIPT_DIR "PR2_DESCRIPTION.md"

if (Test-Path $PR_DESC_FILE) {
    Write-Host "✓ Found PR description file: $PR_DESC_FILE" -ForegroundColor Green
    $PR_BODY = Get-Content $PR_DESC_FILE -Raw
} else {
    Write-Host "✗ PR description file not found: $PR_DESC_FILE" -ForegroundColor Red
    Write-Host "Please ensure PR2_DESCRIPTION.md exists in the repo root"
    exit 1
}

# Check if gh CLI is available
$gh_available = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)

if ($gh_available) {
    Write-Host ""
    Write-Host "=== GitHub CLI Detected ===" -ForegroundColor Cyan
    Write-Host "Using 'gh pr create' to create PR..."
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "DRY RUN MODE - Would execute:"
        Write-Host "gh pr create --repo $REPO --base $BASE_BRANCH --head $HEAD_BRANCH --title `"$PR_TITLE`" --body `"<description>`" --label $(($PR_LABELS) -join ',') --assignee @RVogel101"
    } else {
        try {
            # Create the PR using gh CLI
            $labels_arg = $PR_LABELS -join ","
            
            Write-Host "Creating PR..."
            $pr_output = gh pr create `
                --repo $REPO `
                --base $BASE_BRANCH `
                --head $HEAD_BRANCH `
                --title $PR_TITLE `
                --body $PR_BODY `
                --label $labels_arg `
                --draft:$false
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ PR Created Successfully!" -ForegroundColor Green
                Write-Host ""
                Write-Host $pr_output
                Write-Host ""
                Write-Host "Next: Monitor the PR for CI and review feedback"
            } else {
                Write-Host "✗ PR Creation Failed" -ForegroundColor Red
                Write-Host "GitHub CLI Error: $pr_output"
                exit 1
            }
        } catch {
            Write-Host "✗ Error executing gh command: $_" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host ""
    Write-Host "⚠ GitHub CLI Not Found" -ForegroundColor Yellow
    Write-Host "GitHub CLI (gh) is required for automated PR creation."
    Write-Host ""
    Write-Host "Installation options:"
    Write-Host "  1. Install via chocolatey: choco install gh"
    Write-Host "  2. Install via scoop: scoop install gh"
    Write-Host "  3. Download from: https://github.com/cli/cli/releases"
    Write-Host ""
    Write-Host "Alternatively, create PR manually via GitHub web UI:"
    Write-Host "  URL: https://github.com/RVogel101/lousardzag/pulls"
    Write-Host "  Steps: See PR2_CREATION_STEPS.md"
    Write-Host ""
    Write-Host "To continue manually:"
    Write-Host "  1. Install gh CLI"
    Write-Host "  2. Run: gh auth login (authorize with GitHub)"
    Write-Host "  3. Run: .\create_pr_2.ps1"
    exit 0
}
