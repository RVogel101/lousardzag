# Step 5: Create Migration PRs - Quick Start

## PR #1: armenian-corpus-core (Steps 1-3)

### Pre-Flight Check
```powershell
# Verify branch exists and is up to date
cd C:\Users\litni\OneDrive\Documents\anki\armenian-corpus-core
git branch -vv
# Expected output: feat/migrate-extraction-tools-step1 tracking origin/feat/migrate-extraction-tools-step1
```

### Create PR on GitHub Web UI
1. **Open**: https://github.com/RVogel101/armenian-corpus-core
2. **Click**: "Pull Requests" tab → "New Pull Request" button
3. **Set bases**:
   - Base: `main` (left dropdown)
   - Compare: `feat/migrate-extraction-tools-step1` (right dropdown)
4. **Verify**: GitHub shows "Able to merge" and lists 3 commits
5. **Copy Title**:
   ```
   feat(extraction): centralize extraction tools and contracts into core package
   ```
6. **Copy Description**: Use PR description from MIGRATION_PR_GUIDE.md (Section "PR #1 Description")
7. **Add Labels**: `refactor`, `extraction`, `migration`
8. **Add Reviewers**: @litni
9. **Create PR**: Click "Create pull request" button

### Expected Result
- Title: "feat(extraction): centralize extraction tools and contracts..."
- Commits: 3 (ce974ef, a402516, 9e518dc)
- Files changed: ~15 (extraction tools, contracts, test, docs)
- Status: Ready for review

---

## PR #2: lousardzag (Step 4)

### Wait For
⏳ **DO NOT create this PR until PR #1 (armenian-corpus-core) is MERGED**

**Reason**: PR #2 depends on the central package being available; merging PR #1 first stabilizes the dependency.

### Pre-Flight Check (When PR #1 Merges)
```powershell
# Verify branch exists and is up to date
cd C:\Users\litni\OneDrive\Documents\anki\lousardzag
git branch -vv
# Expected output: feat/migration-core-central-package tracking origin/feat/migration-core-central-package
```

### Create PR on GitHub Web UI
1. **Open**: https://github.com/litni/lousardzag
2. **Click**: "Pull Requests" tab → "New Pull Request" button
3. **Set bases**:
   - Base: `main` (left dropdown)
   - Compare: `feat/migration-core-central-package` (right dropdown)
4. **Verify**: GitHub shows "Able to merge" and lists 1 commit
5. **Copy Title**:
   ```
   feat(extraction): wire lousardzag to consume central package via adapter pattern
   ```
6. **Copy Description**: Use PR description from MIGRATION_PR_GUIDE.md (Section "PR #2 Description")
7. **Add Labels**: `refactor`, `extraction`, `migration`, `adapter`
8. **Add Reviewers**: @RVogel101 (optional)
9. **Create PR**: Click "Create pull request" button

### Expected Result
- Title: "feat(extraction): wire lousardzag to consume..."
- Commits: 1 (3f4912f)
- Files changed: 3 (run_pipeline_adapter.py, test file, workflow)
- Status: Ready for review (after PR #1 merges)

---

## After PRs Are Created

### Checklist
- [ ] PR #1 created and linked in lousardzag issue tracker (if applicable)
- [ ] PR #1 review requested from @litni
- [ ] PR #1 approved and merged
- [ ] PR #2 created after PR #1 merge
- [ ] PR #2 reviewed and merged
- [ ] Both branches deleted (GitHub: "Delete branch" button on PR)

### Monitoring Post-Merge
1. **Central package** (`armenian-corpus-core`):
   - Verify CI/CD passes on merged commit (main branch)
   - Confirm package version bumps to 0.1.0
   - Test extraction pipeline works: `python -m armenian_corpus_core.extraction.run_extraction_pipeline`

2. **Lousardzag adapter** (`lousardzag`):
   - Verify CI/CD passes on merged commit (main branch)
   - Test adapter behaves correctly with fallback (default):
     ```powershell
     python 07-tools/extraction/run_pipeline_adapter.py --dry-run
     # Should show local fallback mode
     ```
   - Optional: Test central mode with feature flag
     ```powershell
     $env:LOUSARDZAG_USE_CENTRAL_PACKAGE='1'
     python 07-tools/extraction/run_pipeline_adapter.py --dry-run
     # Should show central mode
     ```

---

## Timeline Estimate

| Phase | Estimate | Blocker |
|-------|----------|---------|
| Create PR #1 | Now | None |
| PR #1 review cycle | 1-3 days | None |
| PR #1 merge | ~5 min | None |
| Create PR #2 | 5 min | PR #1 merged |
| PR #2 review cycle | 1-3 days | PR #1 merged |
| PR #2 merge | ~5 min | None |
| Post-merge validation | 1-2 weeks | Both merged |
| Step 5 planning (optional) | 3-7 days | Both merged + validation |

---

## Next Action

PR creation and merge flow is complete. Continue with post-merge Step 5 cleanup planning in `STEP5_CLEANUP_PLAN.md`.
