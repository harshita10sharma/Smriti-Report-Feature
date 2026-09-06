# Smriti Report Feature — Phase 0 Readiness Audit (Corrected)

**Audit date:** 2026-09-06
**Auditor:** Autonomous engineering session (Claude Code)
**Scope of this audit:** the Smriti Report Feature repository itself, and the search for whatever external repository/system actually contains the nine cognitive games, their telemetry, and any existing analytics/dashboard code.

**Correction note:** An earlier version of this document was produced against `D:\personal projects\smritivoicebotv5.0.0` (the Smriti VoiceBot project). That was the wrong source of truth — the VoiceBot is a separate, previously stabilized feature, and its lack of game code was incorrectly used as evidence that the Report Feature is greenfield. That version was never pushed and has been discarded. This document replaces it with a correctly scoped investigation.

Legend used throughout:

- **FACT** — verified directly by reading files, running commands, or fetching a page.
- **GAP** — a requirement or capability that is missing or could not be located.
- **INFERENCE** — an engineering conclusion drawn from the facts, not itself directly observed.
- **RECOMMENDATION** — a proposed future action. Not yet authorized or implemented.

No implementation, installation, or migration occurred during this audit. No repository other than this one (`smriti-report`) was modified. The VoiceBot repository was not touched.

---

## 1. Executive Summary

**FACT:** This repository, `smriti-report` (GitHub: `Smriti-Report-Feature`), is new and currently empty of application code — it contains only this audit document.

**FACT:** A systematic search of (a) every project directory on this machine under `D:\personal projects\`, and (b) every repository on the `harshita10sharma` GitHub account, found exactly two Smriti-related repositories: `Smriti-VoiceBot` (the protected, separate voice-assistant project) and `Smriti-Report-Feature` (this repository, currently empty). **No third repository containing the nine cognitive games, a game client/frontend, a caregiver dashboard, or existing analytics code was found anywhere accessible to this session.**

**GAP:** This means the actual location of the nine games' implementation — and therefore the actual telemetry format the Report Feature must consume — is genuinely unknown from what is accessible here. This is reported as an open question requiring human input, not resolved by assumption.

**INFERENCE:** Three explanations are consistent with the evidence, and this audit cannot distinguish between them from the information available:
1. The games have not been built yet anywhere, and this Report Feature repository (or a future sibling repository) is expected to define the telemetry contract *first*, before or alongside game implementation.
2. The games exist in a private repository, local project, or on another machine/account not accessible to this session.
3. The games are planned to be built inside this same `smriti-report` repository as part of this project's scope (the specification's Phase 1 "Telemetry Contract and Data Foundation" language is consistent with this).

**RECOMMENDATION:** Do not proceed to Phase 1 schema/contract design until the human confirms which of the above is true (see Open Questions, §9). Implementing a telemetry contract without knowing whether a game client already exists — and if so, what it actually emits — risks building a contract nothing will ever match.

---

## 2. What Was Inspected, and Why

| Location | Why inspected | Result |
|---|---|---|
| `D:\personal projects\smriti-report` (this repo) | The actual project under development. | Empty except for this audit; no commits pushed to its GitHub remote yet. |
| `D:\personal projects\*` (all ~20 sibling directories) | To check whether a Smriti game-client/frontend project exists locally under a different name. | No directory name or content suggestive of the nine games, a Smriti frontend, or a caregiver dashboard was found. Full listing in §3. |
| `github.com/harshita10sharma` repository list (public, fetched read-only) | To check whether a third Smriti-related repository exists on GitHub that isn't cloned locally. | Exactly two Smriti repositories exist: `Smriti-VoiceBot` and `Smriti-Report-Feature`. No third repository. Full listing in §4. |
| `smriti-report` GitHub remote (`git ls-remote origin`) | To check whether the remote already has commits/content not yet pulled locally. | Remote is empty — no branches, no commits. |

**FACT:** The VoiceBot repository (`smritivoicebotv5.0.0`) was **not** re-inspected in this corrected audit beyond what was already known not to require further digging — per instruction, it is treated as a separate, protected, and unrelated project unless a genuine integration dependency is demonstrated. No such dependency has been demonstrated, so it is out of scope here except as a boundary note (§7).

---

## 3. Local Directory Survey

**FACT — full listing of `D:\personal projects\`:**

`claude/`, `claude.zip`, `Customer-Lifetime-Value-Predictor/`, `guardian-node/`, `Machine Learning/`, `market-sentiment-vs-trader-performance/`, `mcp_cli/`, `Mental health ai track/`, `mnist_digit_classifier_ann/`, `nlp-nltk/`, `Python practise/`, `Restraunt-rating-prediction/`, `SignalZero/`, `smriti-report/` (this repo), `smritivoicebotv5.0.0/` (+ its zip), `task_team5/`, `trader-dashboard-clean/`, `Video2Voice-AI/`, `Youtube_audio_debugging/`, `Youtube-audio-transcription-using-colab-GPU/`, `Youtube-video-dubbing-system/`.

**GAP:** None of these directories are named or described in a way consistent with the nine Smriti cognitive games, a Smriti game client/frontend, or a Smriti caregiver dashboard. No further content-level search of unrelated third-party projects (e.g., `Customer-Lifetime-Value-Predictor`) was performed, since their names/purposes are clearly unrelated and opening unrelated developers' project directories without cause was avoided.

---

## 4. GitHub Account Survey

**FACT — repositories on `github.com/harshita10sharma`** (fetched via public repository listing page, read-only, no authentication used):

`Smriti-Report-Feature` ("Explainable longitudinal cognitive analytics and report generation for the Smriti project"), `Smriti-VoiceBot` ("Multilingual AI voice interaction system for SMRITI..."), plus 19 unrelated personal/academic projects (dubbing systems, ML coursework, trading analysis, a number-guessing game, travel planners, etc. — none Smriti-related).

**FACT:** `Smriti-Report-Feature` is described in its own GitHub description as the home for "explainable longitudinal cognitive analytics and report generation" — consistent with this being the correct repository for the Report Feature, but its description does not claim it also contains the games themselves.

**GAP:** No repository named or described as containing the nine games, a Smriti mobile/web client, or a Smriti caregiver dashboard exists on this account.

---

## 5. Game, Telemetry, and Database Location

**GAP — cannot be answered from information accessible to this session:**
1. What repository/project actually contains the nine cognitive games (if they already exist)? — **Unknown; not found.**
2. Where does the game client/frontend implementation live? — **Unknown; not found.**
3. Where are game sessions and telemetry/events actually generated? — **Unknown; not found.**
4. What database/schema stores those events? — **Unknown; not found.** (The VoiceBot's SQLite database was previously found to contain no game-event schema, but per the correction above, its absence there is not evidence about where such a schema might exist elsewhere — it is simply one data point ruling out one location.)
5. Where do synchronization/backend APIs for game data live? — **Unknown; not found.**
6. Where does the caregiver dashboard/report UI live, if it exists? — **Unknown; not found.**
7. Does any existing analytics/reporting infrastructure exist outside the VoiceBot repo? — **Unknown; not found** among the repositories and directories accessible to this session.

**INFERENCE:** Given that (a) this repository is brand new and empty, (b) no other accessible repository contains the games, and (c) the GitHub description of `Smriti-Report-Feature` frames it as the analytics/reporting layer rather than the games themselves, the most defensible reading of the evidence is that **the games' implementation is either not yet built, or lives somewhere genuinely outside this session's visibility** (a private repo, another developer's machine, or not yet created). This audit does not treat that as license to assume greenfield status for design purposes — it is reported as an open question because building a telemetry contract that must match a real, existing game client is a fundamentally different task than designing one for a game client that will be built afterward to match it.

---

## 6. What Role Should This Repository Play?

**GAP — this is a decision for the human, not a conclusion this audit can reach:** The specification (master prompt) describes a pipeline from "RAW GAME EVENTS" through to "DASHBOARD / PDF," and frames Phase 1 as "Telemetry Contract and Data Foundation" — which is consistent with this repository being responsible for *defining* the contract that a game client must emit, rather than merely consuming an already-fixed one. However, the same specification also assumes an "already-built Smriti system" and "already-built" games exist to integrate with (§1 and §2 of the master prompt). These two framings are in tension given what was actually found (§5), and this audit will not silently resolve that tension by choosing one interpretation.

**RECOMMENDATION:** Ask the human directly (see §9) whether `smriti-report` should:
- (a) consume an existing telemetry stream from a game client that exists but wasn't found by this session (human should provide its location), or
- (b) define the telemetry contract as new, authoritative work product that a not-yet-built or in-progress game client will be built against, or
- (c) also implement the missing game/report integration components (e.g., event-ingestion API, and possibly stub/reference game telemetry) within this same repository's scope.

---

## 7. VoiceBot Boundary

**FACT:** The VoiceBot (`Smriti-VoiceBot` / `smritivoicebotv5.0.0`) is treated as a separate, protected, previously stabilized feature per explicit instruction. It was not re-inspected beyond the read-only GitHub listing in §4, which confirms it is a distinct repository from `Smriti-Report-Feature`.

**FACT (carried forward from the initial inspection, still valid as a boundary fact, not as an architecture conclusion):** The VoiceBot repository is a FastAPI + SQLite voice-assistant backend (ASR/LLM/TTS/safety/command-routing) with no game-event schema of its own. This fact only rules out the VoiceBot's own database as *a* place where game telemetry currently lives — it does not imply anything about where game telemetry *should* live for the Report Feature, and it must not be used to justify any VoiceBot modification.

**RECOMMENDATION:** No VoiceBot modification is proposed or needed at this time. If a genuine integration requirement is discovered in a future phase (e.g., the games turn out to already write into the VoiceBot's shared SQLite database), that must be raised explicitly as its own stop-and-confirm item, per the master prompt's VoiceBot protection rules — it must not be assumed or silently designed around.

---

## 8. Existing Analytics/Reporting/Dashboard Infrastructure

**GAP:** No analytics, scoring, ML, report-generation, PDF-generation, or caregiver-dashboard code was found in any repository or directory accessible to this session — neither in `smriti-report` (empty) nor in the VoiceBot repo (confirmed in the prior, VoiceBot-scoped inspection to contain none) nor in any other local project or GitHub repository surveyed in §3–§4.

**INFERENCE:** If such infrastructure exists, it is not visible to this session. This should be confirmed with the human rather than assumed absent for design purposes, since a wrong assumption here (as happened with the first draft of this audit) would misdirect the entire Phase 1 design.

---

## 9. Open Questions (must be answered before Phase 1 begins)

1. **Do the nine cognitive games already exist as working software anywhere?** If yes, what is the exact repository path, URL, or location? If no, is building them in scope for this project, or is a separate team/repository building them against a contract this repository will define?
2. **Where is the game client (web/mobile/desktop) that elders actually play?** This determines what "raw game events" will look like in practice.
3. **Where is game session/event data currently stored, if it is being generated at all today** (even in a prototype or manual-testing form)?
4. **Does a caregiver dashboard or any report UI already exist anywhere** (a repo not on this GitHub account, a Figma/design file, a separate team's codebase)?
5. **What is the intended relationship between `Smriti-Report-Feature` and `Smriti-VoiceBot`** — fully independent services, or does the Report Feature need to call into or read from the VoiceBot's API/database at all (e.g., for `users`, `family_members`, `medicines` data used as confounder/family-recognition context)? If the latter, that is the "genuine, verified integration requirement" the master prompt says must be explicitly raised before any VoiceBot-adjacent design decision is made.
6. **Should `smriti-report` be a backend-only analytics/API service, or does its scope include a frontend (dashboard) and/or the game clients themselves?**

---

## 10. Phase 1 Recommendation

**RECOMMENDATION:** Do not begin Phase 1 (Telemetry Contract and Data Foundation) until Open Questions 1–6 above are answered. The specific risk of proceeding without answers: designing a telemetry contract, database schema, or ingestion API that has nothing real to integrate with, or that conflicts with a game client that already exists elsewhere and was simply not visible to this session.

Once the human clarifies the actual location and status of the games and any existing infrastructure, Phase 1 should:
1. If a game client already exists: read its actual event output (logs, API payloads, or source) and design the telemetry contract to faithfully represent what it emits — not an idealized version of it.
2. If no game client exists yet: design the telemetry contract as the authoritative specification the eventual game client(s) must implement against, in close collaboration with whoever will build them, and document it as a proposed contract pending client-side confirmation rather than as an assumed-correct fact.
3. In either case, decide and document where game/report data will be persisted (a new database owned by `smriti-report`, or a data store shared with another system) as an explicit, human-confirmed architectural decision — not an inferred default.

This audit found no technical blocker to starting Phase 1 once the repository/data boundary is clarified by the human. The blocker is informational, not technical.
