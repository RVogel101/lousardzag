# Migration PR Guide (Step 5)

**Status**: Ready for pull requests  
**Date**: March 6, 2026  
**Priority**: Create PR #1 first (central package), then PR #2 (lousardzag) after understanding central package changes

---

## PR #1: armenian-corpus-core (Steps 1-3)

**Repository**: https://github.com/RVogel101/armenian-corpus-core  
**Base Branch**: `main`  
**Head Branch**: `feat/migrate-extraction-tools-step1`  
**Commits Included**: 3
- `ce974ef` - Migrate batch 2-6 extraction tools into central package
- `a402516` - Centralize core contracts and decouple extraction mappers
- `9e518dc` - Remove duplicate top-level package path

### PR Title
```
feat(extraction): centralize extraction tools and contracts into core package
```

### PR Description (Copy & Paste)
```markdown
## Overview
Multi-step migration of Armenian corpus extraction infrastructure into
`armenian-corpus-core` as a standalone, reusable package.

## What Changed (3 Commits)

### Commit 1: Migrate 8 extraction tools (ce974ef)
- Moved from `lousardzag/07-tools/extraction/` to `armenian_corpus_core/extraction/`:
  - `export_core_contracts_jsonl.py`
  - `validate_contract_alignment.py`
  - `ingest_wa_fingerprints_to_contracts.py`
  - `merge_document_records.py`
  - `merge_document_records_with_profiles.py`
  - `extract_fingerprint_index.py`
  - `materialize_dialect_views.py`
  - `summarize_unified_documents.py`
- Updated module registry in `run_extraction_pipeline.py`
- Extraction dir now resolved from package path instead of lousardzag root

### Commit 2: Centralize core contracts (a402516)
- Created `armenian_corpus_core/core_contracts/` package:
  - `types.py`: DocumentRecord, LexiconEntry, PhoneticResult (frozen dataclasses)
  - `hashing.py`: Normalized hashing utilities (NFKC normalization, SHA256)
  - `__init__.py`: Public API exports
- Created `extraction/mappers.py`: Extraction-specific mappers
  - `anki_card_row_to_lexicon_entry()`
  - `sentence_row_to_document_record()`
  - `wa_fingerprint_row_to_document_record()`
- Updated all extraction tools to import from central contracts
- Fixed `pyproject.toml` package discovery (setuptools.find_packages)

### Commit 3: Remove duplicate paths (9e518dc)
- Deleted duplicate top-level `/extraction` package (was temporary during migration)
- Canonicalized all imports/docs to `armenian_corpus_core/extraction` path
- Updated README.md architecture documentation
- Updated DEVELOPMENT.md invocation syntax to `-m armenian_corpus_core.extraction.run_extraction_pipeline`
- Updated install scripts (install.ps1, install.sh)

## Architecture

### New Package Structure
```
armenian_corpus_core/
├── core_contracts/           # NEW: Shared domain contracts
│   ├── types.py             # DocumentRecord, LexiconEntry, PhoneticResult
│   ├── hashing.py           # Normalized hashing for deduplication
│   └── __init__.py
├── extraction/              # REFACTORED: 8 tools + registry + orchestration
│   ├── run_extraction_pipeline.py
│   ├── registry.py
│   ├── mappers.py           # NEW: Extraction-specific mappers
│   ├── export_core_contracts_jsonl.py
│   ├── validate_contract_alignment.py
│   ├── ingest_wa_fingerprints_to_contracts.py
│   ├── merge_document_records.py
│   ├── merge_document_records_with_profiles.py
│   ├── extract_fingerprint_index.py
│   ├── materialize_dialect_views.py
│   ├── summarize_unified_documents.py
│   └── __init__.py
└── __init__.py              # Exports contracts + extraction APIs
```

### Key Changes
- **Before**: Lousardzag contained local extraction tools + shims; central package was baseline skeleton
- **After**: Central package is self-contained ETL framework; lousardzag will consume via adapter pattern (Step 4)

## Migration Strategy
- **No breaking changes**: Extraction tools maintain same CLI/data contracts
- **Backward compatible**: Registry pattern supports dynamic tool discovery
- **Decoupled**: Core contracts separated from extraction logic (enables reuse by other projects)

## Why This Change
1. **Reusability**: Other Armenian NLP projects can use extraction tools + contracts independently
2. **Maintainability**: Cleaner separation of concerns (contracts vs. tools)
3. **Deduplication**: Hashing contracts enable cross-project deduplication
4. **Scalability**: Registry pattern supports adding tools without modifying orchestration

## Merge Prerequisites
- [x] All 3 commits pass local tests
- [x] Integration tests added (02-tests/integration/test_central_package_integration.py)
- [x] CI workflows updated
- [x] Documentation updated (README, DEVELOPMENT)
- [x] No breaking changes to CLI contracts

## Post-Merge
After this PR merges:
1. Central package version bumps to 0.1.0 (from 0.1.0-alpha)
2. Lousardzag PR (feat/migration-core-central-package) can proceed
3. Central extraction will be the canonical tool location
```

### Reviewers to Tag
- @litni (original lousardzag maintainer)

### Labels
- `refactor`
- `extraction`
- `migration`

---

## PR #2: lousardzag (Step 4)

**Repository**: https://github.com/litni/lousardzag  
**Base Branch**: `main`  
**Head Branch**: `feat/migration-core-central-package`  
**Commits Included**: 1
- `3f4912f` - Add adapter-driven pipeline runner with central/local fallback

### PR Title
```
feat(extraction): wire lousardzag to consume central package via adapter pattern
```

### PR Description (Copy & Paste)
```markdown
## Overview
Lousardzag adapter layer enabling gradual adoption of centralized extraction tools
with safe fallback to local scripts during transition.

## What Changed (1 Commit)

### Commit: Add adapter runner (3f4912f)
- Created `07-tools/extraction/run_pipeline_adapter.py`:
  - Queries `get_extraction_registry()` from central package
  - Returns tool specs (batch, name, module path) when central package available
  - Falls back to local script paths when unavailable or disabled
  - Feature-controlled via `LOUSARDZAG_USE_CENTRAL_PACKAGE` environment variable
  - Dry-run mode for validation (`--dry-run` flag)
- Updated `.github/workflows/extraction_pipeline.yml`:
  - Added dry-run validation step before extraction pipeline
  - Validates both central and fallback modes in CI
- Extended `04-tests/integration/test_central_package_integration.py`:
  - `test_adapter_runner_dry_run_central_mode()`: Central execution validation
  - `test_adapter_runner_dry_run_local_fallback()`: Local fallback validation

## Architecture

### Adapter Pattern
```
lousardzag/07-tools/extraction/run_pipeline_adapter.py
├── Query central registry (if available)
├── If registry → return `-m armenian_corpus_core.extraction.TOOL` module paths
├── Else → return `07-tools/extraction/TOOL.py` local script paths
└── Control via LOUSARDZAG_USE_CENTRAL_PACKAGE env var
```

### Feature Flag Behavior
| Env Var | Central Available | Mode | Command |
|---------|-------------------|------|---------|
| `1` | Yes | Central | `python -m armenian_corpus_core.extraction.TOOL` |
| `1` | No | Central (Error) | Fails (registry unavailable) |
| `0` | Yes or No | Fallback | `python 07-tools/extraction/TOOL.py` |
| Unset | - | Disabled (None) | Adapter returns None (no registry) |

### Safe Migration Path
- **Phase 1 (Now)**: Env var defaults to unset → adapter returns None → existing scripts continue
- **Phase 2 (After testing)**: Set env var `=0` (explicit fallback) → validates local paths work
- **Phase 3 (After central merge)**: Set env var `=1` → Central package becomes primary
- **Phase 4 (Future)**: Once stable, remove local scripts (Step 5 optional cleanup)

## Validation

### Tested Scenarios
- Central mode dry-run: All 8 tools show central module execution
- Local fallback dry-run: All 8 tools show local script execution
- Integration tests: 5 passing (central registry, central adapter, fallback adapter, etc.)

## Dependencies
- **Requires**: PR #1 (armenian-corpus-core) to be merged first
- **Installation**: `pip install -e git+https://github.com/RVogel101/armenian-corpus-core@main#egg=armenian-corpus-core`

## Merge Strategy
- Merge PR #1 (central package) first to stabilize central extraction infrastructure
- Post-merge PR #1: Validate central package in production
- Then merge PR #2 (lousardzag adapter) to enable central package consumption
- Default `LOUSARDZAG_USE_CENTRAL_PACKAGE=0` (local fallback) on merge for safety
- Gradually enable via feature flag rollout after validation

## Post-Merge
After this PR merges:
1. Lousardzag can consume central extraction tools via environment variable
2. Local extraction tools remain as fallback (no data loss risk)
3. CI validates both central and fallback execution modes
4. Ready for Step 5 (optional): Local tool cleanup after extended validation period
```

### Reviewers to Tag
- @RVogel101 (armenian-corpus-core maintainer)

### Labels
- `refactor`
- `extraction`
- `migration`
- `adapter`

---

## Merge Order & Timeline

### Step 5a: PR #1 (armenian-corpus-core)
1. Push PR #1 to https://github.com/RVogel101/armenian-corpus-core
2. Request review from @litni
3. Address review feedback
4. Merge to `main` (central package becomes canonical source)

### Step 5b: PR #2 (lousardzag)
1. Push PR #2 to https://github.com/litni/lousardzag
2. **After PR #1 merges**: Create PR (now central package is available)
3. Request review from @RVogel101
4. Address review feedback
5. Merge to `main` (adapter layer enables gradual adoption)

### Step 5c (Optional): Validation & Step 5 Planning
1. Monitor both repos in production for 1-2 weeks
2. Validate central extraction execution (`LOUSARDZAG_USE_CENTRAL_PACKAGE=1`)
3. Once stable, plan Step 5 (local tool cleanup): Remove `07-tools/extraction/*.py` scripts

---

## Quick Reference: How to Create PRs

### Option A: GitHub Web UI
1. Go to https://github.com/RVogel101/armenian-corpus-core
2. Click "Pull Requests" → "New Pull Request"
3. Base: `main`, Compare: `feat/migrate-extraction-tools-step1`
4. Copy PR description from above
5. Add labels + reviewers
6. Create PR

### Option B: GitHub CLI (if installed)
```powershell
# For PR #1 (armenian-corpus-core)
cd C:\Users\litni\OneDrive\Documents\anki\armenian-corpus-core
git push -u origin feat/migrate-extraction-tools-step1  # Already done
gh pr create --base main --head feat/migrate-extraction-tools-step1 \
  --title "feat(extraction): centralize extraction tools and contracts into core package" \
  --body @pr_description_1.md  # Paste description into file first
```

---

## Checklist Before Creating PRs

- [x] Both branches pushed to remote
- [x] All commits are clean (no unrelated changes)
- [x] Integration tests pass locally
- [x] Changes are documented
- [ ] PR descriptions reviewed and ready
- [ ] Reviewers identified and notified
- [ ] Expected merge timeline communicated

**Next Action**: Create PR #1 on armenian-corpus-core, then PR #2 on lousardzag after #1 merges.
