# Migration Core Split Report (2026-03-06)

## Scope
This report records the focused migration pass where only central package integration code was committed, while generated artifacts and documentation churn were intentionally excluded.

## Repositories and Commits
- lousardzag: `7eb4226` - feat(core): add central package adapters, contracts, shims, and extraction bridge
- WesternArmenianLLM: `4587e0b` - feat(core): add corpus-core adapter layer and focused migration scripts
- armenian-corpus-core: `6419a6b` - chore: baseline import for corpus core (repository metadata repair)

## Included (Committed)
### lousardzag
- 02-src/lousardzag/core_adapters.py
- 02-src/lousardzag/core_contracts/*
- 02-src/lousardzag/core_shims/*
- 02-src/lousardzag/__init__.py (central package integration wiring)
- 04-tests/integration/test_central_package_integration.py
- 07-tools/extraction/export_core_contracts_jsonl.py
- 07-tools/extraction/extract_fingerprint_index.py
- 07-tools/extraction/ingest_wa_fingerprints_to_contracts.py
- 07-tools/extraction/materialize_dialect_views.py
- 07-tools/extraction/merge_document_records.py
- 07-tools/extraction/merge_document_records_with_profiles.py
- 07-tools/extraction/summarize_unified_documents.py
- 07-tools/extraction/validate_contract_alignment.py

### WesternArmenianLLM
- src/core_adapters.py
- src/__init__.py (adapter exposure)
- tests/test_core_adapters.py
- scripts/export_corpus_overlap_fingerprints.py
- scripts/phonetics_audit.py

## Excluded (Not Included in Focused Migration Commits)
- Generated corpus artifacts under 08-data/*.jsonl in lousardzag
- migration_exports/* in WesternArmenianLLM
- Planning/knowledge/docs updates not required for adapter behavior
- Existing unrelated modified files in CLI, e2e, phonetics, and roadmap docs

## Validation
- lousardzag: `pytest 04-tests/integration/test_central_package_integration.py -q` -> 3 passed
- WesternArmenianLLM: `pytest tests/test_core_adapters.py -q` -> 3 passed
