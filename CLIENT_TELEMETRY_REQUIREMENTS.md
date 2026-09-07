# Client Telemetry Requirements

**Purpose:** this document tells whoever builds/owns the nine game clients exactly what telemetry the Smriti Report Engine needs, and is honest about which of it is already confirmed to exist versus proposed and awaiting confirmation. It was generated directly from `analysis/registry/` (the canonical game/metric registry) so it cannot drift from what the code actually encodes.

Per Phase 0's audit (`REPORT_READINESS_AUDIT.md`), the games themselves were not found in any repository accessible to this project. This document is therefore the authoritative specification a future game client should be built against for report-generation purposes — not a description of an existing client's confirmed behavior beyond the reference backend's database schema.

Two labels are used throughout:

- **VERIFIED FROM BACKEND** — this field is a real column in the reference backend's `events`/`sessions` tables (`REPORT_READINESS_AUDIT.md` §3), confirmed by direct inspection of `supabase/migrations/0004_events.sql`.
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY** — this field is needed by the specification but is not confirmed to exist anywhere. Where it is expected inside the `metrics` jsonb payload, a proposed key name is given (written as `metrics.<key>`); this key name is **proposed by this project, not confirmed by any backend or client code**.

---

## 1. Fields common to every game (VERIFIED FROM BACKEND)

Every telemetry event, regardless of game, must carry:

| Field | Type | Notes |
|---|---|---|
| `patient_id` | string | Elder/patient identifier. |
| `session_id` | string | Groups events into one play session. |
| `game_id` | string | See §2 for the canonical values this project expects. |
| `domain` | enum | One of `memory`, `attention`, `executive`, `visuospatial`, `language` — matches the reference backend's `events.domain` CHECK constraint exactly. |
| `ts` | integer | Device-epoch milliseconds. Must be a positive value. |

Optional but broadly useful fields that exist as real columns and should be sent whenever available: `id` (event id, needed for de-duplication), `correct` (boolean), `error_class` (free text — see the documented vocabulary in §3), `trial_index` (integer), `trial_context` (free text), `response_time_ms`, `initiation_ms`, `movement_ms`, `item_id`, `item_difficulty`, `chosen_id`, `hint_level`.

---

## 2. Canonical game IDs

This project's nine canonical `game_id` values are:

```
faces_of_my_family, market_basket, sort_the_harvest, trace_the_path, my_day,
lamps_of_the_festival, name_the_harvest, weaving_patterns, sounds_of_home
```

**Important:** the reference backend's `events.game_id` column is free text with no enum or foreign-key constraint. The only raw values ever actually observed anywhere (in the reference repo's RLS-test seed fixture, not real production data) are `market_basket` and `faces_family` — note `faces_family`, not `faces_of_my_family`. This project accepts `faces_family` as a documented alias, but **whichever exact strings the real game client sends must be confirmed and, if different, either matched to these canonical values or added as a new documented alias** — never guessed at silently.

---

## 3. Documented `error_class` vocabulary (VERIFIED FROM BACKEND, values not DB-enforced)

The `events.error_class` column exists and is free text; the following values are documented in its column comment and are treated as the working vocabulary. Any other value is accepted but flagged as a data-quality warning, not rejected:

```
semantic, random, perseverative, repeat_selection, omission,
mirror, rotation, detail, sequence_error, item_error, miss, false_alarm
```

## 4. Documented `trial_context` vocabulary (partially verified)

The column exists; only `post_switch` is documented in the reference backend's comment. `first_exposure`, `repeat_exposure`, and `delayed_recall` are this project's own specification vocabulary, not confirmed to be emitted by any client. **No distinct pre-switch/at-switch value is documented anywhere** — this is a real gap (see Sort the Harvest, below).

---

## 5. Per-game requirements

### 5.1 Faces of My Family

- **VERIFIED FROM BACKEND:** `correct`, `item_id`, `error_class` (values `semantic`, `random`).
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:**
  - `item_id` must equal the corresponding `people.id` value for per-person recognition trajectories. This is assumed, not confirmed.
  - A progression-stage marker (recognition / naming / relationship / last-contact-recall) — proposed as `metrics.stage`. Without it, `faces_recognition_accuracy` and the other stage-specific metrics cannot be computed.

### 5.2 Market Basket

- **VERIFIED FROM BACKEND:** `correct`, `item_difficulty`, `trial_index`.
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** forward/backward span direction — proposed as `metrics.direction` (expected values: `forward`, `backward`). Without it, forward and backward span cannot be distinguished at all.

### 5.3 Sort the Harvest

- **VERIFIED FROM BACKEND:** `correct`, `trial_index`, `response_time_ms`, `error_class` (value `perseverative` for perseverative-error rate).
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** a pre-switch trial marker — proposed as `metrics.pre_switch` (boolean). Only a `post_switch` value is documented for `trial_context`; **`switch_cost_ms` must not be computed until pre-switch trials can be reliably identified.**

### 5.4 Trace the Path

- **VERIFIED FROM BACKEND:** `response_time_ms` (used as whole-attempt completion time — this assumes one event per completed attempt, which is itself unverified).
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** variant A/B marker (`metrics.variant`), `metrics.stroke_velocity`, `metrics.lifts`, `metrics.jitter`. None of these exist as verified columns; `trace_path_b_minus_a_ms` additionally needs the variant marker to compare the correct pair of sessions.

### 5.5 My Day

- **VERIFIED FROM BACKEND:** `correct` — sufficient for overall orientation accuracy.
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** a per-dimension marker (day / season / order / routine) if dimension-level breakdown is wanted; no verified column carries this today.

### 5.6 Lamps of the Festival

- **VERIFIED FROM BACKEND:** `correct`, `error_class` (values `sequence_error`, `item_error`).
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** forward/backward direction — same gap and same proposed `metrics.direction` key as Market Basket.

### 5.7 Name the Harvest

- **VERIFIED FROM BACKEND:** `correct` (one event per named item is assumed, giving `items_named` via a simple count).
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:**
  - A semantic-cluster tag per item — proposed as `metrics.cluster_id` — needed for both `clusters` and `switches`.
  - `audio_path`: the reference backend has a `memos` table with a `storage_path` column, but **no documented mechanism associates a memo row with a specific Name the Harvest session/event.** This must be either a real foreign key/session reference on `memos`, or a different mechanism entirely — currently unknown.

### 5.8 Weaving Patterns

- **VERIFIED FROM BACKEND:** `correct`, `error_class` (values `mirror`, `rotation`, `detail`, `random`).
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** `distractor_similarity` and `rotation_angle` difficulty metadata — no verified column carries either; proposed to live in `metrics` but no key name is even proposed yet since neither has an assigned `RegisteredMetric` requiring one today (they are difficulty dimensions, not yet metrics).

### 5.9 Sounds of Home

- **VERIFIED FROM BACKEND:** `correct`, `error_class` (values `miss`, `false_alarm`), `response_time_ms` — sufficient for hit rate, false-alarm rate, and reaction-time variability.
- **REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY:** block-level (3×30s) breakdown is *derivable* from `ts` binned relative to `sessions.started_at`, provided the session is one uninterrupted 90-second run with no pauses — this assumption is unverified and should be confirmed with whoever builds the client, since a paused/resumed session would silently corrupt the block boundaries.

---

## 6. Fields needed for cross-cutting analysis (not game-specific)

- **Longitudinal analysis / practice-effect correction:** needs consistent `session_id` and `ts` sequencing per patient across sessions (verified — already present) plus, ideally, an explicit item-repetition marker if practice effects are to be modeled at the item level rather than only the session-index level (not currently available; session index alone, derivable from `sessions.started_at` ordering, is sufficient for a simpler model).
- **Evidence traceability:** needs `id` (event id) and `session_id` on every event — both verified — so an Evidence object can cite exact contributing sessions/events.
- **Motor/confounder analysis:** `initiation_ms` and `movement_ms` are verified columns that could distinguish motor/interaction issues from cognitive performance (per master spec S63), but no game in the registry currently declares them as required — this should be revisited once real telemetry samples are available to see whether they are populated in practice.

---

## 7. What this project will not do

Per the master specification, this project will not fabricate any of the "REQUIRED BY REPORT CONTRACT — CLIENT INTEGRATION TO VERIFY" fields into extractor code as if they were confirmed. The registry (`analysis/registry/metric_registry.py`) tags every such metric `TelemetrySource.METRICS_JSONB_UNVERIFIED` or `CROSS_TABLE_UNVERIFIED`, and the telemetry-validation layer (`analysis/telemetry/validation.py`) validates only the columns that are actually confirmed to exist. Game-specific feature extraction (a later phase) must check a metric's `telemetry_source` before attempting to compute it, and must return an explicit `UNAVAILABLE` observation with a stated reason when the required field cannot be confirmed present — never a fabricated value.
