# PR #2 Final Creation Guide - Two Paths Forward

**Status**: Ready to create (Step 5 in progress)  
**Date**: March 6, 2026  
**PR Details**:
- **Repository**: github.com/RVogel101/lousardzag
- **Base**: main
- **Head**: feat/migration-core-central-package
- **Commit**: 3f4912f (1 commit)
- **Files Changed**: 3

---

## Path 1: Automated Creation (Recommended)

### Prerequisites
- GitHub CLI (`gh`) installed
- GitHub account authenticated

### Quick Setup

```powershell
# 1. Install GitHub CLI (choose one)
winget install GitHub.cli          # Windows Package Manager
# OR
choco install gh                   # Chocolatey
# OR
scoop install gh                   # Scoop
# OR
# Download from: https://github.com/cli/cli/releases

# 2. Verify installation
gh --version

# 3. Authenticate with GitHub (if first time)
gh auth login
# Follow the prompts to authorize

# 4. Run from lousardzag repo root
cd 'C:\Users\litni\OneDrive\Documents\anki\lousardzag'
.\create_pr_2.ps1

# 5. Script will:
#    - Read PR title and description from files
#    - Create PR automatically
#    - Display PR URL on success
```

### What the Script Does
- Reads PR title: "feat(extraction): wire lousardzag to consume central package..."
- Reads PR description from `PR2_DESCRIPTION.md`
- Adds labels: `refactor`, `extraction`, `migration`, `adapter`
- Creates PR via GitHub CLI
- Shows resulting PR URL

---

## Path 2: Manual Creation via GitHub Web UI

### Step 1: Navigate to Pull Requests
1. **URL**: https://github.com/RVogel101/lousardzag/pulls
2. Click green **"New pull request"** button

### Step 2: Select Branches
1. **Base branch** dropdown: Select `main`
2. **Head branch** dropdown: Select `feat/migration-core-central-package`
3. **Verify**: GitHub shows "Able to merge" (green checkmark)

### Step 3: Enter PR Title
**Copy exactly**:
```
feat(extraction): wire lousardzag to consume central package via adapter pattern
```

### Step 4: Enter PR Description
1. Click in the Description field
2. Open `PR2_DESCRIPTION.md` in an editor
3. Copy entire contents (from "## Overview" to the end)
4. Paste into GitHub description field

### Step 5: Add Labels
1. Click **"Labels"** on the right sidebar
2. Search and select:
   - `refactor`
   - `extraction`
   - `migration`
   - `adapter`

### Step 6: Create PR
1. Click green **"Create pull request"** button
2. Wait for page to redirect to new PR

### Expected Result
- PR created with number (e.g., #42)
- URL format: `https://github.com/RVogel101/lousardzag/pull/42`
- Shows 1 commit (3f4912f)
- Shows 3 files changed
- CI/CD should start running automatically

---

## Files Available for Reference

| File | Purpose |
|------|---------|
| `PR2_DESCRIPTION.md` | PR body (copy-paste ready) |
| `PR2_CREATION_STEPS.md` | Detailed step-by-step instructions |
| `create_pr_2.ps1` | Automated PowerShell creation script |
| `MIGRATION_PR_GUIDE.md` | Full migration documentation |
| `STEP5_QUICK_START.md` | Quick reference guide |

---

## Troubleshooting

### Getting 404 Error?
- **Cause**: Possible URL typo or network issue
- **Fix**: Use **Path 2 (Manual)** - Start from repository home page, not direct URL

### GitHub CLI Installation Issues?
- **Windows**: Use `winget install GitHub.cli` (built into Windows 10+)
- **Alternative**: Download MSI from https://github.com/cli/cli/releases
- **Verify**: `gh --version` should return version number

### Can't Authenticate with gh?
- **Fix**: Run `gh auth login` and follow prompts
- **Use**: Personal Access Token if needed
- **Scopes**: Need `repo` and `workflow` scopes

### PR Creation Script Fails?
1. **Verify**: `PR2_DESCRIPTION.md` exists in repo root
2. **Check**: `get-item PR2_DESCRIPTION.md -Force` in PowerShell
3. **Re-run**: `.\create_pr_2.ps1` after fixing

---

## After PR is Created

1. **Note the PR number** from the URL (e.g., #42)
2. **CI/CD validates** automatically (~5-15 minutes)
3. **Notify** when PR is created (reply with PR URL)
4. **Next steps**:
   - Merge PR #2 (if approved)
   - Mark TODO as complete
   - Begin post-merge validation (1-2 weeks)
   - Plan Step 5 cleanup (optional)

---

## Quick Decision Tree

```
Do you have GitHub CLI installed?
├─ YES → Run: .\create_pr_2.ps1
│       └─→ PR created automatically ✓
│
└─ NO → Install or use manual method?
   ├─ Install → winget install GitHub.cli
   │           gh auth login
   │           .\create_pr_2.ps1
   │
   └─ Manual → Navigate to:
               https://github.com/RVogel101/lousardzag/pulls
               Click "New pull request"
               Use: PR2_DESCRIPTION.md content
```

---

## Current TODO Status

- [x] Step 5a: Create PR #1 (armenian-corpus-core) - COMPLETED & MERGED ✓
- [x] Step 5b: Review & merge PR #1 - COMPLETED ✓
- [ ] **← CURRENT: Step 5c: Create PR #2 (lousardzag adapter)** - READY TO CREATE
- [ ] Step 5d: Review & merge PR #2
- [ ] Step 5e: Post-merge validation (1-2 weeks)
- [ ] Step 6: Plan cleanup (optional)

**Choose your path above and create PR #2!**
