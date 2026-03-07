# PR #2 Creation - Manual Steps (March 6, 2026)

**Status**: Ready to create  
**Repository**: RVogel101/lousardzag (central repository)  
**Branch**: feat/migration-core-central-package (1 commit: 3f4912f)  

---

## Step-by-Step PR Creation (GitHub Web UI)

### 1. Navigate to the Repository (Alternative if 404 Error)

**Option A (Recommended if you got 404):**
1. Go to: https://github.com/RVogel101/lousardzag
2. Click "Pull Requests" tab at the top
3. Click green "New pull request" button
4. GitHUb will auto-suggest the comparison with your branch

**Option B (Direct comparison URL):**
- URL: https://github.com/RVogel101/lousardzag/compare/main...feat/migration-core-central-package

### 2. Verify Comparison Shows:
- Base: `main`
- Compare: `feat/migration-core-central-package`
- Status: "Able to merge"
- Commits: 1 (3f4912f)
- Files changed: 3 files

### 3. Enter PR Title
**Title Field:**
```
feat(extraction): wire lousardzag to consume central package via adapter pattern
```

### 4. Copy PR Description
**Description Field:**
Paste the content from: `PR2_DESCRIPTION.md` (file saved in repo root)

The description includes:
- Overview of adapter pattern
- What changed (the 1 commit)
- Architecture explanation
- Feature flag behavior table
- Safe migration path (4 phases)
- Validation scenarios tested
- Dependencies (PR #1 now ✅ merged)
- Post-merge actions

### 5. Add Labels (Click "Labels" on right sidebar)
Select these labels:
- `refactor`
- `extraction`
- `migration`
- `adapter`

### 6. Add Reviewers (Optional - Click "Assignees" on right sidebar)
Suggested:
- @RVogel101 (for awareness, no approval required)

### 7. Click "Create Pull Request" Button
Green button at bottom of form

---

## Expected Result

After creating PR:
- **PR Title**: feat(extraction): wire lousardzag to consume...
- **PR Number**: Auto-assigned (e.g., #123)
- **Status**: Open, ready for review
- **Commits**: 3f4912f shows in PR
- **Files**: 3 changed files visible
- **Description**: Full architecture and validation details

---

## Next Steps After PR Created

1. **PR URL**: Note the PR number from the URL (e.g., https://github.com/RVogel101/lousardzag/pull/123)
2. **Notify**: The PR is now visible to project maintainers
3. **Monitor**: CI/CD should run automatically (GitHub Actions workflow)
4. **Wait for Review**: Reviewers can provide feedback
5. **Merge**: Once approved, click "Merge pull request" button

---

## Checklist

- [ ] Browser at: https://github.com/RVogel101/lousardzag/compare/main...feat/migration-core-central-package
- [ ] Comparison shows: Base=main, Compare=feat/migration-core-central-package
- [ ] Status shows: "Able to merge"
- [ ] Title entered: "feat(extraction): wire lousardzag to consume..."
- [ ] Description copied: From PR2_DESCRIPTION.md
- [ ] Labels added: refactor, extraction, migration, adapter
- [ ] Reviewers added: @RVogel101 (optional)
- [ ] "Create pull request" button clicked ✓

---

## PR Created? Let Me Know!

Once the PR is created, provide the PR number (or URL) and we'll:
1. Mark PR #2 creation as complete ✓
2. Move to "Review & Merge PR #2" phase
3. Then monitor and validate post-merge

**Current TODO Status:**
- [x] Create PR #1 (armenian-corpus-core) - MERGED
- [x] Review & merge PR #1 - MERGED
- [ ] **← YOU ARE HERE: Create PR #2 (lousardzag adapter)** - IN PROGRESS
- [ ] Review & merge PR #2
- [ ] Post-merge validation (1-2 weeks)
- [ ] Plan Step 5 cleanup (optional)
