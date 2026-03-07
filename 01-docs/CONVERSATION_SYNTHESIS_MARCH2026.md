# Conversation Synthesis (Canonical)

**Scope**: Consolidated synthesis of March 2026 conversations and terminal outcomes.  
**Status**: Canonical one-page reference for learnings, decisions, backlog, and operational notes.

---

## Executive Summary

March 2026 work clarified three priorities:
1. **Reliability first**: recurring CLI/audio failures need diagnostics and smoke tests.
2. **Safe corpus operations**: Nayiri access must be whitelist-gated with conservative pacing.
3. **Pragmatic audio strategy**: IPA-directed workflows and adaptation/fine-tuning are more realistic than training from scratch.

---

## Confirmed Decisions

- Nayiri scraping should use **page-based browsing** (not search-prefix probing).
- Nayiri runs require **IP whitelist coordination** and should start with bounded test runs.
- IPA-first path (espeak-ng track) is the preferred direction for strict letter-name control.
- Existing Anki audio is best treated as **validation data**, not primary TTS training corpus.
- Architecture extraction remains the plan: `wa-corpus` -> `armenian-linguistics` -> `lousardzag` refactor.

---

## Consolidated Learnings

- Terminal/network assumptions can be wrong: external-IP lookups may fail in-shell while browser access succeeds.
- VPN exit-node changes can invalidate whitelisted access without obvious app errors.
- Search-like scraping patterns can create poor signal and higher block risk.
- Repeated `exit code 1` incidents show the need for better startup diagnostics and structured failure logs.
- Documentation drift is a real risk; canonical references reduce duplicate/contradictory guidance.

---

## Prioritized Backlog Snapshot

### P0 (8-12h): Stabilize Core Workflows
- Add explicit startup diagnostics for `03-cli/letter_cards_viewer.py`.
- Add `--debug` mode for viewer and `07-tools/test_mms_tts.py`.
- Add smoke checks for viewer/preview/newspaper build entry points.
- Normalize timestamped error logs under `logs/`.
- Improve newspaper build resilience (retry, partial-success reporting).

### P1 (5-8h): Operational Guardrails
- Add Nayiri `--preflight` mode.
- Add VPN/public-IP guardrail check before Nayiri runs.
- Enforce first bounded Nayiri run (`--max-pages 3`) in runbooks/help.
- Add scraper default-mode and cooldown regression tests.

### P2 (6-10h): Developer Experience
- Add `lousardzag doctor` diagnostics command.
- Add Audio Pipeline Health Report.
- Add TTS Data Readiness Score utility.
- Add shared config for audio generation scripts.

---

## Espeak-ng Environment Status

### Verified on March 6, 2026
- **System path binary**: `C:\Program Files\eSpeak NG\espeak-ng.exe`
- **Conda `base`**: `espeak-ng` callable
- **Conda `wa-llm`**: `espeak-ng` callable
- **Result**: No installation required during this pass.

### Verification Commands

```powershell
where.exe espeak-ng
conda run -n base espeak-ng --version
conda run -n wa-llm espeak-ng --version
```

### Install Command (only if missing)

```powershell
conda install -n wa-llm -c conda-forge espeak-ng -y
```

### Post-install Recheck

```powershell
conda run -n wa-llm espeak-ng --version
```

---

## Canonical References

- Operational runbook: `01-docs/NAYIRI-SCRAPING-GUIDE.md`
- Prioritized implementation plan: `IMPLEMENTATION_ACTION_PLAN.md`
- Session log: `01-docs/SESSION-SUMMARY.md`
- Active task tracker: `NEXT_STEPS_MARCH2026.md`
- Feature backlog: `FUTURE_IDEAS.md`
