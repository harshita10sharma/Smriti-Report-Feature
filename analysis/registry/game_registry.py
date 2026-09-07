"""The nine canonical games (master spec S12/S13, S22-S31).

Every field here is sourced from one of two places, and each game's
``notes`` says which applies to what:

1. The functional specification (Part 2 of the master prompt) - what
   the game is supposed to measure and how.
2. The verified reference-backend schema (REPORT_READINESS_AUDIT.md
   S3/S4) - what telemetry actually, confirmedly exists today.

Where the specification calls for something the verified schema does
not confirm (e.g. span direction, stroke velocity, block indices),
this is stated explicitly in ``notes`` rather than assumed. The
corresponding metrics in ``analysis.registry.metric_registry`` carry
this same distinction via ``TelemetrySource``.
"""

from __future__ import annotations

from analysis.models.enums import Domain, GameId
from analysis.registry.games import GameDefinition

#: Columns verified to exist on every row of the reference backend's
#: `events` table (REPORT_READINESS_AUDIT.md S3) - every game requires
#: at least these to identify and locate a trial.
_COMMON_REQUIRED_FIELDS = ("patient_id", "session_id", "game_id", "domain", "ts")

GAMES: tuple[GameDefinition, ...] = (
    GameDefinition(
        game_id=GameId.FACES_OF_MY_FAMILY,
        display_name="Faces of My Family",
        instrument="Face-name paired associate learning",
        primary_domain=Domain.MEMORY,
        secondary_domains=(Domain.LANGUAGE,),
        constructs=("face-name paired associate learning", "semantic association"),
        error_classes=("semantic", "random"),
        difficulty_dimensions=("option_count", "free_recall_vs_recognition", "relationship_depth"),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct", "item_id"),
        optional_event_fields=("error_class", "chosen_id", "trial_index", "item_difficulty"),
        notes=(
            "Spec requires item_id == person_id for per-person trajectories "
            "(master spec S23); the reference backend's item_id column exists "
            "but whether the tablet client actually sets it to a people.id "
            "value is UNVERIFIED (REPORT_READINESS_AUDIT.md S4). The "
            "recognition/naming/relationship/last-contact-recall progression "
            "stage is not backed by any verified column."
        ),
    ),
    GameDefinition(
        game_id=GameId.MARKET_BASKET,
        display_name="Market Basket",
        instrument="Word span",
        primary_domain=Domain.MEMORY,
        secondary_domains=(Domain.ATTENTION,),
        constructs=("word span",),
        difficulty_dimensions=("list_length", "delay", "direction"),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct"),
        optional_event_fields=("item_difficulty", "trial_index"),
        notes=(
            "Forward/backward direction (master spec S24) is not a verified "
            "column; it is expected in the undocumented metrics jsonb "
            "payload (REPORT_READINESS_AUDIT.md S4)."
        ),
    ),
    GameDefinition(
        game_id=GameId.SORT_THE_HARVEST,
        display_name="Sort the Harvest",
        instrument="Card sorting with unsignalled rule shifts",
        primary_domain=Domain.EXECUTIVE,
        constructs=("card sorting", "set shifting"),
        error_classes=("perseverative", "random", "omission"),
        required_event_fields=(
            *_COMMON_REQUIRED_FIELDS,
            "correct",
            "trial_index",
            "response_time_ms",
        ),
        optional_event_fields=("trial_context", "error_class"),
        notes=(
            "trial_context column exists and its comment documents a "
            "'post_switch' value, but no distinct pre-switch/at-switch value "
            "is documented (REPORT_READINESS_AUDIT.md S4). Neither switch "
            "cost nor trials-to-criterion can be computed without a "
            "confirmed pre-switch/rule-boundary contract."
        ),
    ),
    GameDefinition(
        game_id=GameId.TRACE_THE_PATH,
        display_name="Trace the Path",
        instrument="Trail Making A/B-style tracing",
        primary_domain=Domain.VISUOSPATIAL,
        secondary_domains=(Domain.EXECUTIVE,),
        constructs=("visuomotor tracing", "set shifting"),
        difficulty_dimensions=("variant",),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "response_time_ms"),
        optional_event_fields=("item_difficulty",),
        notes=(
            "No verified field establishes that an event is a completed "
            "whole-task attempt. Variant (A/B), stroke_velocity, lifts, and "
            "jitter (master spec S26) are also not backed by any verified "
            "column - expected in the undocumented metrics jsonb payload."
        ),
    ),
    GameDefinition(
        game_id=GameId.MY_DAY,
        display_name="My Day",
        instrument="Orientation-task analogue (not a literal MMSE implementation)",
        primary_domain=Domain.MEMORY,
        secondary_domains=(Domain.ATTENTION,),
        constructs=("temporal orientation",),
        difficulty_dimensions=("day", "season", "order", "routine"),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct"),
        optional_event_fields=("item_id",),
        notes=(
            "Per-dimension breakdown (day/season/order/routine) is not "
            "backed by any verified column."
        ),
    ),
    GameDefinition(
        game_id=GameId.LAMPS_OF_THE_FESTIVAL,
        display_name="Lamps of the Festival",
        instrument="Corsi-style spatial span",
        primary_domain=Domain.VISUOSPATIAL,
        constructs=("visuospatial working memory",),
        error_classes=("sequence_error", "item_error"),
        difficulty_dimensions=("direction",),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct"),
        optional_event_fields=("error_class", "trial_index"),
        notes=(
            "Forward/backward direction is not a verified column - expected "
            "in the undocumented metrics jsonb payload, same as Market "
            "Basket."
        ),
    ),
    GameDefinition(
        game_id=GameId.NAME_THE_HARVEST,
        display_name="Name the Harvest",
        instrument="60-second category fluency",
        primary_domain=Domain.LANGUAGE,
        constructs=("category fluency",),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct"),
        optional_event_fields=("item_id",),
        notes=(
            "clusters/switches (master spec S29) are not backed by any "
            "verified column, and no verified field establishes that one "
            "event represents one unique spoken item. audio_path is not a "
            "column on `events` at "
            "all; the reference backend's `memos` table has a "
            "storage_path column, but its association to a specific "
            "fluency-task event/session is undocumented "
            "(REPORT_READINESS_AUDIT.md S4) - CROSS_TABLE_UNVERIFIED."
        ),
    ),
    GameDefinition(
        game_id=GameId.WEAVING_PATTERNS,
        display_name="Weaving Patterns",
        instrument="Visual discrimination / figure matching",
        primary_domain=Domain.VISUOSPATIAL,
        constructs=("visual discrimination",),
        error_classes=("mirror", "rotation", "detail", "random"),
        difficulty_dimensions=("element_count", "distractor_similarity", "rotation_angle"),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct"),
        optional_event_fields=("error_class", "chosen_id"),
        notes=(
            "distractor_similarity and rotation_angle (master spec S30) are "
            "not backed by any verified column - expected in the "
            "undocumented metrics jsonb payload."
        ),
    ),
    GameDefinition(
        game_id=GameId.SOUNDS_OF_HOME,
        display_name="Sounds of Home",
        instrument="Redesigned auditory continuous-performance-style task",
        primary_domain=Domain.ATTENTION,
        constructs=("sustained attention",),
        error_classes=("miss", "false_alarm"),
        required_event_fields=(*_COMMON_REQUIRED_FIELDS, "correct", "response_time_ms"),
        optional_event_fields=("error_class",),
        notes=(
            "Reaction-time variability is derivable from verified "
            "response_time_ms values. Hit/miss/false-alarm rates require a "
            "confirmed target/non-target marker, and block-level results "
            "require an explicit client-emitted block marker. Neither may "
            "be inferred from correct/error_class or timestamps."
        ),
    ),
)

GAME_REGISTRY: dict[GameId, GameDefinition] = {game.game_id: game for game in GAMES}
