# Smriti Report Feature — Phase 0 Readiness Audit

**Audit date:** 2026-09-06
**Auditor:** Autonomous engineering session (Claude Code)

Legend used throughout:

- **FACT** — verified directly by reading files, running commands, or fetching a page.
- **GAP** — a requirement or capability that is missing or could not be located.
- **INFERENCE** — an engineering conclusion drawn from the facts, not itself directly observed.
- **RECOMMENDATION** — a proposed future action. Not yet authorized or implemented.

No implementation, installation, or migration occurred during this audit. No repository other than `smriti-report` was modified. The VoiceBot repository was inspected read-only in an earlier discovery pass and was not touched or re-modified here.

**Revision note:** An earlier version of this document was built against `D:\personal projects\smritivoicebotv5.0.0` (the Smriti VoiceBot project) as if it were the games/backend source of truth. That was the wrong repository — VoiceBot is a separate, previously stabilized feature — and its lack of game code does not establish that the Report Feature is greenfield. A corrected pass then searched every local project directory and the full GitHub account and found no third repository. This document is that corrected audit, re-verified and reformatted to the full structure required for Phase 0 sign-off. The discovery findings below were independently re-confirmed immediately before writing this document (repeated local directory listing and GitHub repository listing), not merely carried over from memory.

---

## 1. Repositories and Directories Inspected, and Why

| Location | Type | Why inspected | Result |
|---|---|---|---|
| `D:\personal projects\smriti-report` | Local repo (this one) | The Report Feature implementation repository under active development. | Contains only this audit document and `.git`; no application code, no commits besides the audit. |
| `D:\personal projects\` (all ~24 sibling entries) | Local directories | To find a Smriti game-client/frontend/backend/dashboard project under any other name on this machine. | Re-listed twice (once per audit pass); entry count and names unchanged both times. No entry is named or otherwise evidently related to the nine games, a Smriti frontend, or a caregiver dashboard. |
| `D:\personal projects\smritivoicebotv5.0.0\smriti-voicebot-v5.0.0` | Local repo (VoiceBot) | The one confirmed Smriti-related codebase on this machine besides this repo; needed to establish the VoiceBot boundary and rule it in/out as a data source. | FastAPI + SQLite voice-assistant backend; contains no game-session schema, no game telemetry, no analytics/reporting code, no PDF generation, no dashboard (full detail in §5–§9). Treated strictly as a protected, separate system per instruction — not re-modified or re-explored beyond what was already established. |
| `github.com/harshita10sharma` repository listing | Remote (GitHub, public, read-only) | To check whether a third Smriti-related repository exists on GitHub that isn't cloned to this machine. | Fetched twice, at two points in this engagement. Both times returned the identical 21-repository list. Only two are Smriti-related: `Smriti-Report-Feature` and `Smriti-VoiceBot`. No third repository. |
| `smriti-report` GitHub remote (`git ls-remote origin`) | Remote (GitHub) | To confirm the remote's actual state before and after each audit revision, and to avoid assuming local state matches remote. | Remote `HEAD`/`main` matches the local `main` tip at every check; no divergent or unexpected remote content. |

**FACT:** No other repository, local directory, or GitHub project accessible to this session contains the nine games, a game client, a caregiver dashboard, or existing report/analytics infrastructure.

**INFERENCE:** Given a genuinely exhaustive search of everything visible to this session, one of the following must be true, and this audit cannot distinguish between them: (a) the games do not yet exist as working software anywhere, (b) they exist in a location genuinely inaccessible to this session (a private repo, another machine/account, a non-Git artifact), or (c) building them is intended to happen inside this same `smriti-report` repository as part of this project's scope. This is reported as an open question (§16), not resolved by assumption, because the three interpretations lead to materially different Phase 1 designs.

---

## 2. Repository Ownership and Boundaries

**FACT:** `smriti-report` (GitHub: `Smriti-Report-Feature`) is the Report Feature implementation repository. It is currently empty of application code.

**FACT:** `smriti-voicebot-v5.0.0` (GitHub: `Smriti-VoiceBot`) is a separate, independently versioned repository with its own git history, its own `.env`/configuration, and its own dependency set. It is explicitly designated as a protected, previously stabilized system per project instruction.

**FACT:** The two repositories are not linked by any shared submodule, monorepo structure, or symlink — they are fully independent Git repositories at sibling filesystem paths.

**GAP:** No repository was found that is explicitly the "existing Smriti application" containing the nine games, as distinct from the VoiceBot. If such a repository exists, its location must come from the human (§16, Open Question 1).

---

## 3. Verified Architecture (of what actually exists)

**FACT — `smriti-report`:** Empty except for this audit and `.git`. No language, framework, or dependency has been chosen or installed yet.

**FACT — `smriti-voicebot-v5.0.0`** (verified by direct file inspection in the initial discovery pass): Python ≥3.10, FastAPI, Pydantic v2, stdlib `sqlite3` (no ORM), single SQLite database file (`runtime/smriti.db`), schema defined as an ordered list of raw-SQL migrations in `smriti_voice/database/migrations.py` (`SCHEMA_VERSION = 3`). No frontend/JS project exists inside it. Package structure: `smriti_voice/{api,asr,tts,llm,safety,language,conversation,memory,offline,tools,database}` plus root-level pipeline/engine modules.

**GAP:** No architecture can be verified for the actual game client, since no such repository was found.

---

## 4. Nine-Game Audit

A case-insensitive search for each game's name and plausible synonyms (e.g. "corsi", "spatial_span", "fluency", "trail", "cpt") was run against the one confirmed Smriti codebase available (VoiceBot), and no matching directory/repository name was found among any other project on this machine or GitHub account to search inside instead.

| # | Game | Status | Basis |
|---|---|---|---|
| 1 | Faces of My Family | **GAP — no implementation found anywhere accessible** | No file/table/string match in VoiceBot; no other repository exists to search. |
| 2 | Market Basket | **GAP — not found** | Same basis. |
| 3 | Sort the Harvest | **GAP — not found** | Same basis. |
| 4 | Trace the Path | **GAP — not found** | Same basis. |
| 5 | My Day | **GAP — not found** | VoiceBot has a `daily_routines` table, but it is a voice-assistant routine-logging concept unrelated to an orientation-task game. |
| 6 | Lamps of the Festival | **GAP — not found** | Same basis. Flagged by the spec as needing special attention for spec drift — no legacy implementation exists to have drifted from. |
| 7 | Name the Harvest | **GAP — not found** | Same basis. |
| 8 | Weaving Patterns | **GAP — not found** | Same basis. Flagged by the spec for spec drift — no legacy implementation exists. |
| 9 | Sounds of Home | **GAP — not found** | Same basis. Flagged by the spec as "redesigned" — no prior implementation, redesigned or otherwise, exists in any accessible repository. |

**FACT:** The only game-adjacent artifact anywhere is VoiceBot's `games` database table (catalog only: `id, user_id, game_key, display_name, description, enabled, created_at` — no gameplay columns) seeded with three unrelated placeholder rows (`memory_match`, `word_recall`, `number_order`), and a `start_game` voice tool that only emits an `OPEN_PLAY` client-navigation signal. Neither constitutes an implementation of any of the nine games.

**GAP — per-game required attributes (session lifecycle, event schema, item IDs, difficulty, correctness, timing, error classes, trial context, metrics, persistence, synchronization, historical availability, report readiness, missing/reconstructable telemetry) cannot be assessed for any of the nine games, because no implementation of any of them was found to inspect.**

---

## 5. Telemetry / Event Architecture Audit

**GAP:** No game-session or game-event telemetry exists anywhere accessible to this session. VoiceBot's generic `telemetry` table and JSONL event log (`logs/voice_events.jsonl`) record only voice-pipeline events (ASR/LLM/TTS/turn-level), not gameplay, and were confirmed by direct code inspection to carry no game-event semantics.

**GAP:** Session lifecycle, event schema, item identity, difficulty parameters, correctness, timing, error classification, and trial context — all required inputs to Phase 1 (Telemetry Contract) — have no existing implementation to inspect.

---

## 6. Database Architecture Audit

**FACT:** The only verified database in scope is VoiceBot's single SQLite file (`runtime/smriti.db`), containing `users`, `family_members`, `personal_memories`, `meals`, `medicines`, `appointments`, `daily_routines`, `visitors`, `reminders`, `preferences`, `conversations`, `conversation_turns`, `telemetry`, `sync_outbox`, `games` (catalog only), and `voice_jobs`. Full column detail was captured in the initial discovery pass; none of these tables store game session/event/trial data.

**GAP:** No database for `smriti-report` exists yet — it has not been designed or created.

**GAP:** No evidence establishes whether a separate database for game/report data already exists elsewhere (outside the two repositories found). This is an open question (§16).

---

## 7. Backend / API Integration Boundary Audit

**FACT:** VoiceBot exposes a FastAPI HTTP API (`smriti_voice/api/`, `routes/{command,conversation,health,languages,voice,tools,memory_sync}.py`) covering voice/conversation/auth/sync concerns. None of its routes serve game data, reports, or analytics.

**FACT:** `memory_sync.py` is the one VoiceBot route that handles caregiver/data synchronization (family, medicine, routine data) rather than voice-pipeline logic — it is the most plausible integration point if the Report Feature ever needs to read `users`/`family_members`/`medicines` context from VoiceBot, but no such integration has been designed, requested, or verified as necessary yet.

**GAP:** No backend/API exists yet for the Report Feature itself. No backend/API exists for whatever system would run the nine games, since that system was not found.

**RECOMMENDATION:** Do not assume the Report Feature must integrate with VoiceBot's API at all. Treat any such integration as a genuine, explicit requirement to be confirmed by the human before design — consistent with the VoiceBot-protection rule that integration dependencies must be demonstrated, not assumed.

---

## 8. Dashboard / Report Infrastructure Audit

**GAP:** No caregiver dashboard, report UI, or report-generation code exists in `smriti-report`, in VoiceBot, or in any other repository/directory found on this machine or GitHub account. VoiceBot's own documentation (`HANDOFF.md`, `AUDIT.md`) refers to "the caregiver app" as an external system that is "the source of truth for family, medicines, appointments and routine" — implying such an app exists, but its location was not discoverable from anything accessible to this session.

---

## 9. Existing Analytics Audit

**GAP:** No analytics, scoring, cognitive-assessment, or ML code exists in any repository found. VoiceBot's `smriti_voice/memory/rag.py` implements BM25-style lexical retrieval for conversational memory recall — this is unrelated to cognitive analytics and is called out explicitly so it is not mistaken for existing analytics infrastructure in a later phase.

---

## 10. Game → Metric → Domain Mapping Audit

**GAP:** No mapping can be audited from existing code, because no game implementations or telemetry exist to map from. The registry required by the specification (§19 of the master prompt) is entirely a Phase 1/Phase 2 design deliverable, not an extraction task — there is nothing in any accessible repository to reverse-engineer a mapping from.

---

## 11. Reusable Infrastructure

**FACT — genuinely reusable, if the human decides Report Feature data should share VoiceBot's stack:**
- The SQLite + ordered raw-SQL migration-list pattern (`smriti_voice/database/migrations.py`), including its `PRAGMA user_version` versioning and shared provenance-column convention (`source`, `created_by`, `confidence`, `verification_status`, timestamps).
- The `users`, `family_members`, and `medicines` tables as potential identity, family-recognition ground-truth, and medication-confounder data sources.
- The Pydantic-model-per-table convention and FastAPI app/router structure as stylistic precedent, if the Report Feature is built as a sibling service in a similar style.
- The `.env` / `SMRITI_*`-prefixed configuration convention.

**INFERENCE:** None of this constitutes telemetry the Report Feature can consume today — it is architectural precedent only, and adopting it is a design choice, not a requirement, since `smriti-report` is fully independent.

---

## 12. Telemetry Gaps (consolidated)

- No game-session lifecycle of any kind.
- No trial/round-level event recording.
- No difficulty-parameter recording.
- No error classification of any kind (semantic/random, sequence/item, mirror/rotation/detail/random, perseverative).
- No trial-context recording (e.g., post-switch flags for Sort the Harvest).
- No reaction-time, completion-time, stroke/velocity/jitter, or block-level telemetry.
- No item-identity linkage (e.g., `itemId → personId` for Faces of My Family).
- No audio-retention path scoped for a fluency task, though VoiceBot's general audio-cache configuration (`SMRITI_AUDIO_CACHE_DIR`, `SMRITI_AUDIO_RETENTION_MINUTES`) could plausibly be adapted if audio ever flows through VoiceBot's infrastructure — unconfirmed.

---

## 13. Data Quality Findings

**GAP — not assessable yet:** With no real telemetry available anywhere, no missingness, duplication, or malformed-value analysis can be performed on actual data. Data-quality tooling will need to be validated against synthetic data first (Phase 9) and against real telemetry once a real source is identified.

**FACT:** VoiceBot's provenance-column convention (source/confidence/verification_status) is a reasonable precedent for how the Report Feature should represent data quality, if consistency with that system is ever desired.

---

## 14. Proposed Integration Boundary

**RECOMMENDATION (pending human confirmation):**
- `smriti-report` should own its own data model, database, and API, independent of VoiceBot, unless and until a specific, demonstrated need arises to read VoiceBot data (e.g., `family_members` for Faces-of-My-Family ground truth, or `medicines` for confounder context).
- Any such need must be raised explicitly as an integration-boundary decision before implementation, per the VoiceBot-protection rule — never inferred or designed around silently.
- No VoiceBot file should be modified under any currently known Report Feature requirement; this audit found none.

---

## 15. Proposed Report Feature Architecture

**RECOMMENDATION:** Since `smriti-report` is empty, a modular-monolith structure adapted from the specification's conceptual pipeline is proposed, to be refined once Open Questions (§16) are answered — particularly whether this repository must also define/host game telemetry ingestion for a not-yet-located or not-yet-built game client:

```
report/
  telemetry/    # event/session contract + validation (Phase 1)
  games/        # per-game feature extraction (Phase 2)
  domains/      # five cognitive domain estimators (Phase 3)
  baseline/     # personal baseline + practice-effect modeling (Phase 4)
  trajectory/   # longitudinal aggregation and trend estimation (Phase 5)
  detection/    # sustained-change and fluctuation detection (Phase 6)
  confounders/  # confounder + engagement analysis (Phase 7)
  evidence/     # evidence object construction (Phase 8)
  synthetic/    # synthetic cohort + ground truth (Phase 9, dev/validation only)
  narrative/    # deterministic caregiver/technical narrative (Phase 12-13)
  contract/     # versioned report data contract (Phase 11)
  api/          # FastAPI (or equivalent) routes exposing the contract (Phase 11)
tests/report/   # mirrors the module structure above
```

This is explicitly provisional — the specification itself instructs not to blindly adopt this shape, and there is no existing repository architecture in `smriti-report` to adapt to instead, so this proposal is a starting point for human review, not a decision.

---

## 16. Open Questions (block Phase 1 until answered)

1. **Do the nine cognitive games already exist as working software anywhere?** If yes, exact repository/location. If no, is building them in scope for this project or a separate effort this repository must define a contract for?
2. **Where does the actual game client (web/mobile/desktop) live**, if it exists?
3. **Is any game telemetry being generated today, even informally** (manual testing, a prototype, logs)?
4. **Does a caregiver dashboard or report UI already exist anywhere** outside what this session can see?
5. **Should `smriti-report` read any data from VoiceBot** (`users`, `family_members`, `medicines`) for identity/confounder context, and if so, via what mechanism (direct DB read, new VoiceBot API endpoint, sync export)?
6. **Is `smriti-report`'s scope backend/API only, or does it also include a frontend dashboard and/or the game clients themselves?**

---

## 17. Assumptions

**FACT — no assumption was substituted for missing information in this audit.** Where information could not be verified, it is recorded as a GAP or Open Question rather than assumed. The one interpretive step taken is the INFERENCE in §1/§16 that greenfield status cannot be presumed merely from an exhaustive-but-possibly-incomplete search — that conclusion is explicitly flagged as requiring human confirmation before Phase 1 design proceeds.

---

## 18. Risks

- **Designing a telemetry contract or database schema before knowing whether a real game client exists** risks producing something nothing will ever integrate with, or that conflicts with a client built independently and out of view of this session.
- **Single-SQLite-file precedent in VoiceBot**, if adopted for Report Feature data by a future decision, would require strict additive-only migration discipline to avoid risk to the protected VoiceBot system.
- **No caregiver dashboard was located**, so the specification's "reuse its architecture and design system" instruction (master prompt §47/§74) cannot currently be honored — a dashboard may need to be designed from scratch, or its real location must be found first.
- **Name the Harvest's regional-language ASR requirement** (Meiteilon, Khasi, Mizo) is a known hard problem; VoiceBot has multiple ASR providers, but their accuracy for these specific languages is unverified and is out of scope for a Report-Feature-only audit.

---

## 19. Proposed Implementation Plan (pending Open Questions)

**RECOMMENDATION:** Do not begin Phase 1 until §16 is answered. Once answered:

1. If a real game client is identified: read its actual event output (logs/API/source) and design the telemetry contract to faithfully represent what it emits.
2. If no game client exists yet: design the telemetry contract as the authoritative specification a future game client must implement against, explicitly labeled as a proposed contract pending client-side confirmation.
3. In either case, make an explicit, human-confirmed decision on where game/report data will be persisted (new database owned by `smriti-report`, vs. shared with another system) before writing schema code.
4. Build the Game → Metric → Domain registry (specification §19) as new, authoritative design work, once the telemetry contract is fixed.
5. Proceed through Phases 2–17 as specified, each gated by its own inspect → plan → implement → validate → commit → push loop.

This audit found no technical blocker to starting Phase 1 once the repository/data boundary is clarified by the human. The blocker is informational (unresolved Open Questions), not technical.
