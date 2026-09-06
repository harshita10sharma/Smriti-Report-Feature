# Smriti Report Engine

Explainable longitudinal cognitive-analytics and report-generation engine for
the Smriti project. This service turns validated game/session telemetry into
a traceable, non-diagnostic caregiver and clinician report.

This repository does **not** implement the Smriti backend, the caregiver web
app, or the nine cognitive games. Those live in the separate reference
repository documented in `REPORT_READINESS_AUDIT.md`. This service is the
analytics layer the reference backend's nightly `smriti-analysis` cron job
and `generate-report` endpoint are expected to call into.

## Status

Early foundation stage. See `REPORT_READINESS_AUDIT.md` for the full
reconciliation against the reference backend's actual schema, and
`CLIENT_TELEMETRY_REQUIREMENTS.md` (once created) for the per-game telemetry
contract this engine expects.

## Project layout

- `analysis/` — the Report Engine package (models, telemetry validation,
  metrics, domains, baseline, trajectory, detection, evidence, report,
  narrative, API).
- `tests/` — test suite, organized by responsibility to mirror `analysis/`.

## Development

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -e ".[dev]"
pytest
ruff check .
mypy
```

## Non-negotiable principles

- Five independent cognitive domains (memory, attention, executive,
  visuospatial, language). No single "cognitive score."
- Not a diagnostic system. No disease/condition claims.
- Deterministic, reproducible analytics and narrative generation. No LLM in
  the core report-generation path.
- Personal baseline (person vs. their own history), not population norms.
- Missingness is explicit, never silently imputed.
- Every finding is traceable to source sessions, metrics, and evidence.
