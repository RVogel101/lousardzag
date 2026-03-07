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
- **Requires**: PR #1 (armenian-corpus-core) to be merged first ✅ COMPLETED
- **Installation**: Central package is now available on main branch

## Merge Strategy
- Central package from PR #1 is now merged and stable
- This PR enables lousardzag to consume central extraction tools
- Default `LOUSARDZAG_USE_CENTRAL_PACKAGE=0` (local fallback) on merge for safety
- Gradually enable via feature flag rollout after validation

## Post-Merge
After this PR merges:
1. Lousardzag can consume central extraction tools via environment variable
2. Local extraction tools remain as fallback (no data loss risk)
3. CI validates both central and fallback execution modes
4. Ready for Step 5 (optional): Local tool cleanup after extended validation period
