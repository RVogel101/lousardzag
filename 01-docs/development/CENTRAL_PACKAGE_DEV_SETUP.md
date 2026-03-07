# Central Package Development Setup

This guide documents the local development setup for the migration to
`armenian-corpus-core`.

## Scope

- Repository: `lousardzag`
- Central package: sibling repo `armenian-corpus-core`
- Goal: run migration in editable mode and validate adapter + CLI wiring

## 1. Environment

Use the preferred conda environment:

```powershell
(C:\Users\litni\anaconda3\shell\condabin\conda-hook.ps1) ; (conda activate wa-llm)
```

## 2. Install Central Package (Editable)

From the central package repository root:

```powershell
cd C:\Users\litni\OneDrive\Documents\anki\armenian-corpus-core
pip install -e .
```

## 3. Enable Central Package in lousardzag

```powershell
$env:LOUSARDZAG_USE_CENTRAL_PACKAGE = "1"
```

Optional diagnostics:

```powershell
$env:LOUSARDZAG_DEBUG_IMPORTS = "1"
python -c "from lousardzag.core_adapters import diagnose_central_package; import pprint; pprint.pprint(diagnose_central_package())"
```

Expected diagnostics:

- `central_package_enabled: True`
- `central_package_installed: True`
- `registry_available: True`
- `tools_count: 8`

## 4. Validate End-to-End Imports and Registry Access

```powershell
python -c "from lousardzag.core_adapters import get_extraction_registry; r = get_extraction_registry(); print(len(r.list_tools()))"
```

Expected output: `8`

## 5. Validate Orchestration CLI Discovery

```powershell
$env:PYTHONIOENCODING = "utf-8"
python C:\Users\litni\OneDrive\Documents\anki\armenian-corpus-core\armenian_corpus_core\extraction\run_extraction_pipeline.py --project lousardzag --dry-run
```

Expected output includes:

- `Pipeline completed successfully`
- `summarize_unified_documents`

## 6. Pytest Integration Check

Run the new integration test:

```powershell
cd C:\Users\litni\OneDrive\Documents\anki\lousardzag
pytest 04-tests/integration/test_central_package_integration.py -q
```

## 7. Notes About WA-LLM Shim

The WA-LLM shim code cannot be finalized in this repository because
`WesternArmenianLLM` is a separate repo. Use the same pattern as
`02-src/lousardzag/core_adapters.py`:

- feature flag to enable central package
- adapter function to load central registry
- diagnostics helper mirroring `diagnose_central_package`

This keeps migration safe while both projects transition independently.
