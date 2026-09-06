# Smriti Report Feature — Phase 0 Reconciliation Audit

**Audit date:** 2026-09-06
**Target repository:** `D:\personal projects\smriti-report` (GitHub: `Smriti-Report-Feature`) — the Report Engine implementation home.
**Reference repository:** `https://github.com/Abhayk777/SMRITI` — read-only architectural reference, cloned shallow (depth 1) to a scratch directory outside this repository for inspection; never modified.

Category legend (per the master specification):

- **IMPLEMENTED** — exists as working code/schema in the reference repository, verified by direct reading.
- **SPECIFIED** — explicitly defined in `docs/backend-spec.md` or the shared zod/TS types, but not (yet) backed by working code.
- **MISSING** — required by the Report Feature's specification but absent from both the reference repository's code and its documentation.
- **UNVERIFIED** — plausible/likely but not directly confirmed by inspection.

Supplementary legend (carried over from prior audits, used for the target repository and integration reasoning):

- **FACT** / **GAP** / **INFERENCE** / **RECOMMENDATION**.

---

## 1. Target Repository State

**FACT:** `smriti-report` contains only prior audit documents and `.git`; no application code exists yet. Git status is clean, `main` is in sync with `origin/main` (`https://github.com/harshita10sharma/smriti-report-feature.git`, which GitHub reports has moved to `https://github.com/harshita10sharma/Smriti-Report-Feature.git`). No language, framework, or dependency has been chosen or installed in this repository yet.

---

## 2. Reference Repository State

**FACT:** `Abhayk777/SMRITI` is an npm-workspaces monorepo: `web/` (React 19 + Vite + TypeScript caregiver app), `packages/shared/` (TypeScript types + zod schemas shared by web and edge functions), `supabase/` (Postgres migrations, Edge Functions in Deno/TypeScript, `config.toml`), `docs/` (`INDEX.md`, `backend-spec.md`, `rls-test.sql`), `scripts/verify.sh`, plus root `AGENTS.md`/`CLAUDE.md`/`TASKS.md`. There is **no REST server** — the architecture is PostgREST + Row-Level Security (RLS) directly, per `AGENTS.md`. The single visible commit (`248e00f`, shallow clone) is labeled `T14: watchdog — device health monitoring and missed-dose safety net`, corresponding to the last item of a 14-task build plan in `TASKS.md`; all 14 tasks' code is present in the repo.

**FACT:** `docs/INDEX.md` explicitly states that three companion specifications — `app-spec.md` (what the Flutter tablet writes), `ml-spec.md` (the analysis job, trajectory detector, synthetic seeder), and `games-spec.md` (the per-game data contract) — are **referenced but not included in this repository**. This is a direct, first-party statement that the authoritative per-game telemetry contract lives in a document this session cannot see.

**INFERENCE:** `smriti-report` is very likely intended to be (or to absorb the responsibilities of) the "ML engineer" role that `docs/backend-spec.md` repeatedly refers to in third person (e.g., "the ML engineer's Python," "the ML engineer owns the deeper signal views"). This is consistent with everything found, but the human should confirm it explicitly (§13, Open Question 1).

---

## 3. Verified Backend Schema (all 15 migrations read in full)

**IMPLEMENTED — full table list**, `supabase/migrations/0001`–`0015` (content verified to match `docs/backend-spec.md`'s code blocks for 0001–0012; 0013–0015 extend beyond the spec document):

| Table | Ownership (per RLS) | Purpose | Key columns |
|---|---|---|---|
| `patients` | caregiver R/W, device limited R/W | Elder/patient identity | `id, display_name, age, education_years, lang_code, script, timezone, content_version, lang_pack_version, device_user_id, device_last_seen_at, device_pending_events, device_app_version, clock_skew_ms, consent_given_at, active_flag_count, created_by, created_at, archived_at` |
| `patient_members` | self-managed via RPC | Caregiver/family/health-worker access grants | `patient_id, user_id, role (caregiver\|family_viewer\|health_worker), invited_by, created_at` |
| `pairing_tokens` | server/edge-function only | Tablet pairing flow | `token, patient_id, created_by, expires_at, consumed, consumed_at, attempts, created_at` |
| `audit_log` | server only | Security/audit trail | `id, patient_id, actor, action, detail jsonb, created_at` |
| `people` | caregiver R/W, member/device read | Family members (Faces of My Family ground truth) | `id, patient_id, name, relationship, photo_path, voice_path, memory_prompt, is_deceased, sort_order, created_at` |
| `medications` | caregiver R/W, member/device read | Medication data | `id, patient_id, name, dose, pill_photo_path, voice_path, window_start_min, window_end_min, chosen_time_min, days_of_week, active, created_at` |
| `routine_items` | caregiver R/W | Daily routine content | `id, patient_id, time_min, label_key, icon_asset, created_at` |
| `escalation_config` | caregiver R/W | Safety-escalation ladder config | `patient_id, steps jsonb, primary_name/phone, secondary_name/phone, updated_at` |
| `sessions` | **device insert-only**, member read | Game session envelope | `id (client-generated), patient_id, started_at (device-epoch-ms), ended_at, game_ids text, completed, abandoned_at_ms, demo_replays, server_received_at` |
| `events` | **device insert-only**, member read, **update/delete hard-denied** | **Per-trial cognitive-game telemetry — this IS the telemetry contract** | `id, patient_id, session_id, game_id, domain (check: memory\|attention\|executive\|visuospatial\|language), item_id, item_difficulty, theta_before, correct, initiation_ms, movement_ms, response_time_ms, chosen_id, error_class (free text; comment lists semantic\|random\|perseverative\|repeat_selection\|omission\|mirror\|rotation\|detail\|sequence_error\|item_error\|miss\|false_alarm), trial_index, trial_context (free text; comment lists post_switch\|first_exposure\|repeat_exposure\|delayed_recall), hint_level, metrics jsonb, ts, hour_of_day, tz_offset_min, server_received_at` |
| `reminder_events` | device insert-only, member read | Medication reminder outcomes | `id, patient_id, medication_id, scheduled_at, fired_at, responded_at, outcome (confirmed\|declined\|no_response), channel (in_app\|call\|sms\|watchdog), ladder_step, server_received_at` |
| `memos` | device insert-only, member read | Voice memo recordings | `id, patient_id, storage_path, duration_ms, recorded_at, context_tag, transcript, read_at, server_received_at` |
| `escalations` | device insert, caregiver read, update denied to all client roles | Safety-net escalation ladder execution | `id (text, {reminderEventId}_{step}), patient_id, reminder_event_id, medication_id, step, status (requested\|executing\|completed\|cancelled\|failed), reason, twilio_sid, requested_at, executed_at, source (device\|watchdog), not_before (added 0014), created_at` |
| `ability_mirror` | server-write only (trigger), member read | **Per-domain running ability estimate mirrored from device-computed `theta_before`** — NOT a Report Engine output | `patient_id, domain, theta, n_trials, rt_mean_log, rt_var, updated_at` (PK patient_id+domain) |
| `flags` | **server-write only**, member/caregiver read | **Pre-built schema for change-point/evidence findings — currently unpopulated by any code** | `id, patient_id, type (decline\|engagement_drop\|adherence_drop\|device_offline\|pattern_mismatch), domains text[], severity (info\|moderate\|high), changepoint_date, z_scores jsonb, evidence_session_ids uuid[], baseline_window daterange, recent_window daterange, confidence, status (active\|acknowledged\|resolved), created_at, acknowledged_by, acknowledged_at` |
| `bandit_state` | server-write only | Medication-reminder-timing bandit (unrelated to cognition) | `medication_id, patient_id, posteriors jsonb, last_decay_at, updated_at` |
| `reports` | server-write only, member read | **Generated PDF report artifact metadata** | `id, patient_id, storage_path, months, generated_by, created_at` |
| `app_config` | service-role only | Internal secrets/config (e.g. `cron_secret`) | `key, value` |

**IMPLEMENTED — 5 read-optimized SQL views** (`0010_views.sql`, all `security_invoker = true`):
- `daily_play` — per patient/day: sessions, trials, accuracy, mean_rt_ms, mean_initiation_ms, mean_movement_ms, rt_variability, mean_hint_level, perseverations, repeat_errors, semantic_errors, peak_difficulty, `games_played[]`.
- `daily_domain` — per patient/day/domain: trials, accuracy, mean_theta, mean_rt_ms, rt_variability.
- `daily_sessions` — per patient/day: sessions, minutes_played, abandoned, demo_replays.
- `daily_adherence` — per patient/day: scheduled, confirmed, via_tablet, via_call, missed.
- `daily_report` — full outer join of `daily_play` + `daily_adherence`, left-joined with `daily_sessions`; this is the existing "daily rollup" the caregiver dashboard (`my_patients_overview` RPC) reads from.

**IMPLEMENTED — 5 RPCs** (`0008_rpcs.sql`): `get_patient_content` (tablet content sync bundle), `device_heartbeat`, `create_patient` (atomic patient+membership+escalation-config creation), `my_patients_overview` (caregiver landing page, reads `daily_report`), `invite_member`.

**IMPLEMENTED — RLS/authorization model**: driven by `patient_members` rows (role: caregiver/family_viewer/health_worker) plus a device identity signed into the JWT's `app_metadata`. Helper functions `patient_role`, `is_member`, `is_caregiver`, `is_device`, `can_read`. Content tables: member/device read, caregiver write. `events`/`sessions`/`reminder_events`/`memos`: device insert-only, immutable (no update/delete for any role). Derived tables (`flags`, `ability_mirror`, `bandit_state`, `reports`): all client-side writes are `with check (false)` — **only the service role (i.e., a server-side job with the service-role key) can populate them.**

**IMPLEMENTED — storage**: 4 private buckets — `patient-media` (5MB cap, caregiver write), `patient-memos` (10MB cap, device write — this is where Name the Harvest's `audio_path` would plausibly live), `lang-packs` (any authenticated read), `reports` (member read; **no client write policy — service-role only**, consistent with `reports` table).

**IMPLEMENTED — triggers** (`0009_triggers.sql`): `bump_content_version` (cache-busting for tablet sync); `default_chosen_time`; **`update_ability_mirror`** — on every `events` INSERT, upserts `ability_mirror.theta = new.theta_before, n_trials += 1`. This means `ability_mirror` is a live mirror of whatever adaptive-difficulty ability estimate the *tablet client* computes per trial (`theta_before`) — it is not something the Report Engine computes, and must not be confused with the Report Engine's own personal-baseline estimate; **`sync_flag_count`** — denormalizes `patients.active_flag_count` whenever `flags` changes, confirming `flags` is meant to be written to (by something), even though nothing in this repo currently writes to it.

**IMPLEMENTED — scheduled jobs** (`0012_cron.sql`, amended by `0013`/`0014`/`0015`): `smriti-watchdog` (*/10 min), `smriti-escalation-sweep` (*/2–5 min), `smriti-bandit-decay` (weekly), `smriti-keepalive` (every 6h) — all safety/adherence infrastructure, unrelated to cognition. **`smriti-analysis`** (nightly, `30 20 * * *` = 02:00 IST) — `net.http_post` to `https://<analysis-host>/run` with header `x-internal-secret` (from `app_config.cron_secret`) and **body `{}`** (empty). The placeholder host and empty body confirm: **this cron job is the reference repo's explicit, pre-wired hook for calling the Report Engine nightly — but the actual contract of `/run` (request/response shape, per-patient vs. all-patients semantics) is not specified anywhere in this repository.** This is UNVERIFIED beyond "it POSTs an empty JSON body with a shared secret header, once a night, to a URL we must supply."

**SPECIFIED, NOT IMPLEMENTED — `generate-report` edge function**: exact contract given in `docs/backend-spec.md` §8.8:
```
POST { patient_id, months }   [caregiver JWT]
→    { signed_url, report_id }
```
Described as "server-side rendering, not client-side — the clinician page needs deterministic layout." Corresponding zod request/response schemas (`generateReportBodySchema`, `generateReportResultSchema`) already exist in `packages/shared/src/schemas.ts`, but **no `supabase/functions/generate-report/` code exists** — it is designed, not built. The spec also documents the intended two-page structure (Page 1 caregiver domain trajectories with ±1 SD band and changepoints; Page 2 clinician instrument-mapping table) and the exact required disclaimer footer: *"This is a record of home-based activity over time. It is not a clinical assessment and does not replace examination."*

**SPECIFIED, NOT IMPLEMENTED — clinician instrument-mapping table** (`docs/backend-spec.md` §8.8), given as the intended Page 2 content:

| Game | Instrument | Reported as (example) |
|---|---|---|
| Market Basket | Word span | Forward 5, backward 3 |
| Trace the Path | TMT A / B | B−A: 34s → 61s |
| Sort the Harvest | Card sorting | Perseverative errors 1.2 → 3.8/session |
| My Day | MMSE orientation | 4/5 |
| Name the Harvest | Category fluency | 15 → 11 items/60s |
| Lamps of the Festival | Corsi span | Forward 5, backward 3 |
| Delayed probe | Savings score | 0.71 → 0.42 |

Note: this table names 7 of the 9 canonical games (Faces of My Family, Weaving Patterns, and Sounds of Home are absent from it; "Delayed probe" appears as an eighth instrument not in our nine-game roster — likely referring to the `trial_context = 'delayed_recall'` partial index seen in `events`, possibly overlapping with Faces of My Family's "last-contact recall" stage or a distinct delayed-recall mechanic). This is flagged as an open question (§13).

**SPECIFIED, NOT IMPLEMENTED — `ocr-prescription` edge function**: mentioned in the directory tree and has zod schemas (`ocrPrescriptionBodySchema`) in `packages/shared`, but no code and no `ANTHROPIC_API_KEY` usage anywhere else in the repo. Unrelated to the Report Feature; noted only for completeness.

**MISSING — deeper analytical views**: `docs/backend-spec.md` states explicitly: *"The ML engineer owns the deeper signal views — post-error slowing, across-session savings, per-person recognition trajectories, delayed-recall savings, sundowning. Those go in `0013_report_views.sql`."* The actual `0013` migration in this repo is `app_config.sql` (unrelated) — **the report-views migration was never created.** This is explicit, first-party confirmation that the Report Engine (this project) is expected to author its own migration(s) for these views, additively, against the real `events`/`sessions` schema above.

---

## 4. Verified Telemetry Fields

**IMPLEMENTED:** The `events` and `sessions` tables (§3) constitute a real, already-deployed-shape telemetry contract — this is a materially different situation from earlier audits against the unrelated VoiceBot repository. Per-trial fields (`game_id`, `domain`, `item_id`, `item_difficulty`, `theta_before`, `correct`, `initiation_ms`, `movement_ms`, `response_time_ms`, `chosen_id`, `error_class`, `trial_index`, `trial_context`, `hint_level`, `metrics jsonb`, `ts`, `hour_of_day`, `tz_offset_min`) map directly onto most of the master specification's per-game requirements (§13.1–13.9 of Part 1 of the master prompt):

| Master-spec requirement | Backing column | Status |
|---|---|---|
| `itemId = personId` (Faces of My Family) | `item_id text` | IMPLEMENTED as a generic text field; no FK to `people.id`, no enforced convention — **UNVERIFIED whether the tablet client actually sets `item_id` to a `people.id` value.** |
| Semantic vs. random error (Faces) | `error_class` (comment-documented, not DB-enforced enum) | IMPLEMENTED as free text; **no CHECK constraint**, so any value can be written — validation must happen in the Report Engine, not assumed from the DB. |
| Forward/backward span direction (Market Basket, Lamps) | Not a dedicated column — likely encoded in `metrics jsonb` or via `trial_context`/`item_difficulty` | **GAP/UNVERIFIED** — no explicit `direction` column exists; must be recovered from `metrics jsonb`, whose internal shape is entirely undocumented in this repo. |
| Trial context (pre/post-switch, Sort the Harvest) | `trial_context` (comment lists `post_switch`, not a distinct pre/post pair) | PARTIALLY SPECIFIED — only a `post_switch` value is documented in the comment; there is no documented value for "pre-switch" or "at-switch," and again no DB-level enum enforcement. |
| Trail A/B variant, stroke velocity, lifts, jitter (Trace the Path) | Not explicit columns — must live in `metrics jsonb` | **GAP/UNVERIFIED** |
| Block-level data (Sounds of Home) | Not an explicit column — `trial_index`/`ts` could reconstruct blocks if trial-level rows are emitted, but this is UNVERIFIED | **GAP/UNVERIFIED** |
| Sequence vs. item error (Lamps) | `error_class` (comment lists both `sequence_error` and `item_error`) | IMPLEMENTED as free text, same caveat as above. |
| Audio path (Name the Harvest) | Not a column on `events`; `memos.storage_path` exists but is a separate table for voice-memo recordings, not obviously wired to fluency-task events | **GAP/UNVERIFIED** — plausible reuse candidate, not confirmed. |
| Mirror/rotation/detail/random error, distractor similarity, rotation angle (Weaving Patterns) | Not explicit columns — `error_class` comment lists `mirror`, `rotation`, `detail` but not `random`; similarity/angle would need `metrics jsonb` or `item_difficulty` | **GAP/UNVERIFIED** |

**INFERENCE:** The `metrics jsonb` column is almost certainly where most game-specific structured payloads (span direction, stroke telemetry, block-level breakdowns, distractor similarity, etc.) are intended to live, since the fixed columns cannot hold them all. **Its internal shape is not documented anywhere in this repository** — this is the single largest concrete gap standing between "the schema exists" and "the Report Engine can be built against a fully known contract." This is exactly the `games-spec.md` gap `docs/INDEX.md` already told us about (§2).

**RECOMMENDATION:** Treat `metrics jsonb`'s internal shape per game as the primary open contract question (§13, Open Question 2) rather than guessing its structure. Until answered, the Report Engine's per-game extractors must validate `metrics` defensively (unknown/missing keys → explicit `UNAVAILABLE`, never fabricated) rather than assuming a particular shape.

---

## 5. Verified Report-Generation Components

**IMPLEMENTED:** `reports` table + `reports` storage bucket (metadata + artifact storage, service-role write only).
**SPECIFIED, NOT IMPLEMENTED:** `generate-report` edge function (contract in §3).
**MISSING:** Any code that populates `flags`, `reports`, or the "deeper signal views" — none exists anywhere in the reference repository. **This is precisely the Report Engine's job.**

---

## 6. Report Engine Responsibilities (proposed, pending confirmation)

**RECOMMENDATION:** Based on the evidence above, `smriti-report` should own:
1. The nightly analysis job that `smriti-analysis`'s cron hook expects to call at `/run` (§3) — reading `events`/`sessions`/`reminder_events` per patient (via service-role Postgres access, since RLS blocks client roles from derived tables anyway), computing baseline/trajectory/detection/evidence, and writing results into `flags` and/or new report-specific tables.
2. The "deeper signal views" explicitly deferred to the ML engineer (§3) — as new, additive SQL migrations proposed for the reference repository (never applied by this session; see §12).
3. The actual rendering behind `generate-report` — either as the literal Deno edge function (if Python is not viable inside Supabase Edge Functions and a rewrite/proxy is needed) or as a service the edge function calls into. This needs human confirmation (§13, Open Question 3), since `docs/backend-spec.md`'s own directory tree separately lists `analysis/` as "ML engineer's Python" alongside the Deno `supabase/functions/`, suggesting the intended split is: **Python analysis service (this repo) computes and writes `flags`/report data; a thin `generate-report` Deno function (reference repo) renders the PDF from already-computed data and returns a signed URL.**

---

## 7. Backend Responsibilities (reference repo, not to be duplicated here)

**FACT:** Patient/caregiver identity, device pairing, medication/routine/people content management, the safety-escalation ladder (Twilio/Vapi), and RLS/auth are all fully implemented in the reference repository and must not be reimplemented here.

---

## 8. Game-Client Responsibilities

**GAP:** No game client (Flutter tablet app) exists in the reference repository or anywhere else found by this or prior audits. Per the master specification (§128 of Part 3), `smriti-report` must **not** implement the nine games — it may only build fixtures, validators, and adapters against their documented/inferred telemetry shape. The authoritative per-game contract (`games-spec.md`) is confirmed to exist as a concept but is not accessible to this session (§2).

---

## 9. Frontend Responsibilities

**FACT:** `web/src/` is an unmodified Vite/React scaffold (confirmed by direct read of `App.tsx`/`main.tsx`) — no routing, no Supabase client usage, no dashboard, no report view exists yet, despite `docs/backend-spec.md` describing an intended 13-route app including `/p/:pid/dashboard` and `/p/:pid/report`. **This means there is currently no caregiver dashboard to "reuse the architecture of," contrary to what the master specification assumes might exist** — the dashboard is unbuilt on both sides (reference repo and this repo).

---

## 10. PDF-Rendering Responsibilities

**RECOMMENDATION:** Pending §6/§13, the safest default is: this repository (`smriti-report`) computes and owns all analytical content and produces the machine-readable `ReportData` contract; actual PDF byte generation can live either here (Python, e.g. `reportlab`/`weasyprint`) or in a `generate-report` Deno function that calls this service for data and renders — a decision that materially affects architecture and must be confirmed, not assumed (§13, Open Question 3).

---

## 11. Proposed Integration Boundary

**RECOMMENDATION:**
- **Read access:** `smriti-report` reads `patients`, `people`, `medications`, `sessions`, `events`, `reminder_events` via a service-role Postgres connection (bypassing RLS, since this is a trusted server-side job) — never via the anon/caregiver client path.
- **Write access:** `smriti-report` writes only to `flags` and, if approved, new report-specific tables/views it proposes via additive migrations (§12). It must never write to any tablet-owned table (`events`, `sessions`, `reminder_events`, `memos`) — these are correctly immutable at the RLS layer and must stay that way.
- **API surface:** `smriti-report` exposes at minimum a `/run` endpoint matching the pre-wired `smriti-analysis` cron hook (accepting the secret header `x-internal-secret`, validated against `app_config.cron_secret` or an equivalent secret this service is given out-of-band), plus whatever report-retrieval endpoints `generate-report` (or an equivalent) needs to call.
- **No modification of the reference repository** occurs from this session; any schema needs are documented as proposed migrations only (§12).

---

## 12. Risks / Blockers

- **The `metrics jsonb` internal shape is undocumented** (§4) — the single biggest concrete blocker to writing correct, non-fabricated per-game extractors. Building against a guessed shape risks exactly the "invented event fields" failure mode the master specification prohibits.
- **The `games-spec.md` and `ml-spec.md` companion documents are known to exist conceptually but are not accessible to this session** — if they exist somewhere (another repo, a shared doc), obtaining them would resolve most of §4's gaps at once.
- **The `/run` cron contract is minimal (empty body + secret header)** — this session must design a reasonable request/response contract for it, since none is specified, and document that decision clearly as a Report Engine design choice rather than a discovered fact.
- **No confirmation of the Python-vs-Deno split** for the analysis job vs. `generate-report` rendering (§6) — building the wrong shape of service risks wasted work.
- **RLS immutability is a hard constraint, not a suggestion**: `events`/`sessions` have `update`/`delete` denied at the database level for every role, including implicitly for us unless we use the service-role key, which bypasses RLS entirely. The Report Engine must never attempt to "correct" or backfill tablet-owned rows.

---

## 13. Explicit Assumptions and Open Questions Requiring Confirmation

Per Part 1 §18 stop conditions ("two authoritative specifications materially contradict one another," "telemetry contract fundamentally conflicts with the documented backend schema"), the following are raised for confirmation rather than resolved by assumption, because each would materially change the data contract, API contract, or architecture:

1. **Is `smriti-report` intended to be (or become) the "ML engineer" role/service** referenced throughout `docs/backend-spec.md`, responsible for the nightly `/run` job and the deferred `0013_report_views.sql`-equivalent migrations? (Assumed yes for planning purposes in §6, pending confirmation.)
2. **What is the actual internal shape of the `metrics jsonb` column per game** — is there a `games-spec.md` document available from the human, or does this need to be defined by `smriti-report` as a proposed contract (per the master specification's "define the contract, mark client integration to verify" principle)?
3. **Should PDF rendering live inside `smriti-report` (Python) or inside the reference repo's `generate-report` Deno edge function** calling out to this service for computed data? The reference repo's own directory tree suggests a Python `analysis/` service plus a separate Deno rendering function, but this is not stated definitively.
4. **Does the human have access to `games-spec.md` / `app-spec.md` / `ml-spec.md`**, and if so, can they be provided? These would resolve most of §4's per-game telemetry gaps directly rather than requiring `smriti-report` to define a contract "cold."
5. **Should `smriti-report` connect directly to the reference repository's live/staging Supabase Postgres instance** (via service-role credentials the human would need to provision) for development, or should development proceed entirely against local fixtures/synthetic data until a real integration environment is arranged? This has direct implications for what can be tested in Phase 1–2 versus deferred to a later phase.
6. **The Page-2 instrument table names 7 games plus "Delayed probe," omitting Faces of My Family, Weaving Patterns, and Sounds of Home, and using an 8th unlisted instrument name.** Is "Delayed probe" a tenth mechanic, an alias for something in the nine-game roster (e.g., Faces of My Family's last-contact-recall stage), or a documentation gap in the reference repo itself? This affects the game registry (§22 of Part 2) and should not be resolved by guessing.

---

## 14. Decisions Safe to Make Now

**RECOMMENDATION (proceeding without further confirmation, per Part 1 §77's "choose minimal correct design" rule):**
- Python is the implementation language for `smriti-report` (confirmed appropriate by the reference repo's own `analysis/` directory convention and by the master specification's Python-quality requirements).
- The five-domain enum (`memory`, `attention`, `executive`, `visuospatial`, `language`) matches the reference repo's `events.domain` CHECK constraint exactly — no reconciliation needed; this can be adopted verbatim as the Report Engine's `Domain` enum.
- The game registry's nine canonical `game_id` values (§22, Part 2) are new IDs this project defines; the reference repo's `events.game_id` is a free-text column with no FK/enum, so there is no naming collision to resolve — but the actual strings the tablet will send are UNVERIFIED (only `market_basket` and `faces_family` appear, as RLS-test fixture data, not confirmed production values — note `faces_family`, not `faces_of_my_family`, which may hint at the tablet's real naming convention differing slightly from this project's canonical IDs). This discrepancy is worth flagging back to the human but does not block starting Phase 1 with our own canonical naming, documented as provisional.
- Foundational typed domain objects (§72 of Part 3) can be built now against the verified `events`/`sessions` schema (§3) without waiting on the open questions above, since those objects are internal to the Report Engine and can be adapted later if the `metrics jsonb` shape is clarified.
- Telemetry validation (Phase 3) can be built against the verified fixed columns now; validation of `metrics jsonb` contents must be conservative/defensive pending Open Question 2.

---

## 15. Decisions Requiring Backend/Client Confirmation Before Proceeding Further

- Anything depending on the actual `metrics jsonb` shape (most of Phase 4's per-game extractors for span direction, stroke telemetry, block-level data, error sub-types beyond what `error_class` documents).
- The `/run` request/response contract (Phase 23 API design) — this project must propose one, but it should be confirmed with whoever owns the reference repository before being treated as final.
- Where PDF rendering will actually execute (§13, Open Question 3) — affects Phase 22 architecture materially.
- Service-role credential provisioning for any real integration testing beyond synthetic fixtures (§13, Open Question 5).

---

## 16. Phase 0 Sign-Off

This audit satisfies the Phase 0 acceptance criteria to the extent possible from read-only inspection of both repositories: repository/data architecture has been verified against real, working schema (not assumed); the nine-game telemetry gap is now precisely bounded (fixed columns exist and are usable; `metrics jsonb` internals are the one real unknown); reusable infrastructure (`daily_*` views, `flags`, `reports`, storage buckets, RLS model) has been identified; and integration boundaries are proposed with explicit open questions flagged rather than silently assumed.

**RECOMMENDATION:** Proceed to Phase 1 (Project Foundation) now, since foundational typed models and configuration do not depend on resolving §13's open questions. Defer any code that would need to assume `metrics jsonb`'s shape until Open Question 2 is answered or a defensible provisional schema is explicitly documented as such.
