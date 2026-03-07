# Comprehensive Espeak-ng Environment Verification Script
# Purpose: Single-command check of espeak-ng availability across all project conda environments
# Usage: .\check_espeak_env.ps1
# 
# This script verifies:
# 1. System binary availability (PATH check)
# 2. Version details and data location
# 3. Availability in base conda environment
# 4. Availability in wa-llm (project IPA environment)
# 5. Installation instructions if missing

$ErrorActionPreference = 'SilentlyContinue'
$WarningPreference = 'SilentlyContinue'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Espeak-ng Environment Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. System PATH check
Write-Host "[1/4] System PATH Check" -ForegroundColor Yellow
$systemPath = where.exe espeak-ng 2>$null
if ($systemPath) {
    Write-Host "✓ System binary found:" -ForegroundColor Green
    Write-Host "  $systemPath"
    $version = & espeak-ng --version 2>$null
    Write-Host "  Version: $version"
} else {
    Write-Host "✗ System binary NOT on PATH (fallback to conda environments below)" -ForegroundColor Red
}
Write-Host ""

# 2. Base environment check
Write-Host "[2/4] Conda base Environment Check" -ForegroundColor Yellow
try {
    $baseVersion = & conda run -n base espeak-ng --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ espeak-ng available in conda base:" -ForegroundColor Green
        Write-Host "  $baseVersion"
    } else {
        Write-Host "✗ espeak-ng NOT available in base (but system PATH may have it)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not check base environment" -ForegroundColor Yellow
}
Write-Host ""

# 3. wa-llm environment check (project IPA environment)
Write-Host "[3/4] Conda wa-llm Environment Check (Project IPA Path)" -ForegroundColor Yellow
try {
    $waLlmVersion = & conda run -n wa-llm espeak-ng --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ espeak-ng available in wa-llm:" -ForegroundColor Green
        Write-Host "  $waLlmVersion"
        $waLlmPath = & conda run -n wa-llm where.exe espeak-ng 2>&1
        if ($waLlmPath -and $waLlmPath -notmatch "not found") {
            Write-Host "  Path: $waLlmPath"
        }
    } else {
        Write-Host "✗ espeak-ng NOT available in wa-llm (installation needed)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  To install, run:" -ForegroundColor Cyan
        Write-Host "  conda install -n wa-llm -c conda-forge espeak-ng -y" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠ Could not check wa-llm environment (environment may not exist)" -ForegroundColor Yellow
}
Write-Host ""

# 4. Summary & Usage Instructions
Write-Host "[4/4] Summary & Quick Reference" -ForegroundColor Yellow
Write-Host ""
Write-Host "Quick verification command:" -ForegroundColor Cyan
Write-Host "  conda run -n wa-llm espeak-ng --version" -ForegroundColor Gray
Write-Host ""
Write-Host "Quick install (if needed):" -ForegroundColor Cyan
Write-Host "  conda install -n wa-llm -c conda-forge espeak-ng -y" -ForegroundColor Gray
Write-Host ""
Write-Host "Test transcription (phonetic, Western Armenian):" -ForegroundColor Cyan
Write-Host "  conda run -n wa-llm espeak-ng -v hy 'պետք'" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
