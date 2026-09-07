"""The canonical metric registry (master spec S21, S32).

Every metric named in the functional specification (Part 2, S23-S31)
appears here, tagged with its real ``TelemetrySource`` per the Phase 0
audit. A metric whose telemetry_source is ``METRICS_JSONB_UNVERIFIED``
or ``CROSS_TABLE_UNVERIFIED`` is registered (so its definition,
directionality, and intended domain are documented) but must not be
computed by any extractor until the underlying field is confirmed -
see each metric's ``verification_note``.

``audio_path`` (Name the Harvest) is deliberately not registered as a
metric here: it has no directionality and is not scored - it is raw
evidence data retained for human verification (master spec S29), not
a metric a domain estimator would consume.
"""

from __future__ import annotations

from analysis.models.enums import (
    AggregationMethod,
    Direction,
    Domain,
    GameId,
    MetricType,
    TelemetrySource,
)
from analysis.registry.metrics import RegisteredMetric

_VERIFIED_COLUMN = TelemetrySource.VERIFIED_COLUMN
_DERIVED = TelemetrySource.DERIVED_FROM_VERIFIED_COLUMNS
_JSONB = TelemetrySource.METRICS_JSONB_UNVERIFIED
_CROSS_TABLE = TelemetrySource.CROSS_TABLE_UNVERIFIED

METRICS: tuple[RegisteredMetric, ...] = (
    # --- Faces of My Family --------------------------------------------
    RegisteredMetric(
        metric_id="faces_recognition_accuracy",
        display_name="Recognition accuracy",
        description="Proportion of correct recognition-stage trials.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.FACES_OF_MY_FAMILY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.stage"),
        verification_note=(
            "'correct' is a verified column, but there is no verified way "
            "to isolate recognition-stage trials from naming/relationship/ "
            "last-contact-recall trials without a stage marker, which is "
            "proposed here as metrics.stage pending client confirmation."
        ),
    ),
    RegisteredMetric(
        metric_id="faces_naming_accuracy",
        display_name="Naming accuracy",
        description="Proportion of correct naming-stage trials.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.FACES_OF_MY_FAMILY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.stage"),
        verification_note="Same stage-marker gap as faces_recognition_accuracy.",
    ),
    RegisteredMetric(
        metric_id="faces_relationship_accuracy",
        display_name="Relationship accuracy",
        description="Proportion of correct relationship-stage trials.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.FACES_OF_MY_FAMILY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.stage"),
        verification_note="Same stage-marker gap as faces_recognition_accuracy.",
    ),
    RegisteredMetric(
        metric_id="faces_last_contact_recall_accuracy",
        display_name="Last-contact recall accuracy",
        description="Proportion of correct last-contact-recall-stage trials.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.FACES_OF_MY_FAMILY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.stage"),
        verification_note="Same stage-marker gap as faces_recognition_accuracy.",
    ),
    RegisteredMetric(
        metric_id="faces_semantic_error_rate",
        display_name="Semantic error rate",
        description="Proportion of incorrect trials classified as semantic errors.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.MEMORY,
        game_id=GameId.FACES_OF_MY_FAMILY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note=(
            "error_class is a verified column; 'semantic' is a documented "
            "value in its comment, but the value is not DB-enforced."
        ),
    ),
    RegisteredMetric(
        metric_id="faces_random_error_rate",
        display_name="Random error rate",
        description="Proportion of incorrect trials classified as random errors.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.MEMORY,
        game_id=GameId.FACES_OF_MY_FAMILY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="Same basis as faces_semantic_error_rate.",
    ),
    # --- Market Basket ----------------------------------------------------
    RegisteredMetric(
        metric_id="market_basket_forward_span_achieved",
        display_name="Forward span achieved",
        description="Longest forward word span correctly recalled.",
        unit="items",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.MARKET_BASKET,
        aggregation=AggregationMethod.MAX_ACHIEVED,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.direction"),
        verification_note=(
            "No verified column distinguishes forward from backward span "
            "trials; proposed as metrics.direction pending client "
            "confirmation."
        ),
    ),
    RegisteredMetric(
        metric_id="market_basket_backward_span_achieved",
        display_name="Backward span achieved",
        description="Longest backward word span correctly recalled.",
        unit="items",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.MARKET_BASKET,
        aggregation=AggregationMethod.MAX_ACHIEVED,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.direction"),
        verification_note="Same basis as market_basket_forward_span_achieved.",
    ),
    # --- Sort the Harvest ---------------------------------------------
    RegisteredMetric(
        metric_id="sort_harvest_perseverative_error_rate",
        display_name="Perseverative error rate",
        description="Proportion of trials with a perseverative error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.EXECUTIVE,
        game_id=GameId.SORT_THE_HARVEST,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='perseverative' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="sort_harvest_switch_cost_ms",
        display_name="Switch cost",
        description="Post-switch minus pre-switch median reaction time.",
        unit="ms",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.EXECUTIVE,
        game_id=GameId.SORT_THE_HARVEST,
        aggregation=AggregationMethod.DIFFERENCE,
        telemetry_source=_JSONB,
        required_fields=("response_time_ms", "metrics.pre_switch"),
        minimum_observations=6,
        verification_note=(
            "response_time_ms is verified, but only a 'post_switch' "
            "trial_context value is documented - no confirmed way to "
            "identify pre-switch trials. Proposed as metrics.pre_switch "
            "(boolean) pending client confirmation. Master spec S25: never "
            "compute switch cost without valid trial context."
        ),
    ),
    RegisteredMetric(
        metric_id="sort_harvest_trials_to_criterion",
        display_name="Trials to criterion",
        description="Number of trials needed to reach the sorting criterion after a rule switch.",
        unit="trials",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.EXECUTIVE,
        game_id=GameId.SORT_THE_HARVEST,
        aggregation=AggregationMethod.MEDIAN,
        telemetry_source=_DERIVED,
        required_fields=("trial_index", "correct"),
        verification_note=(
            "Derivable from verified trial_index+correct sequence; the "
            "criterion rule itself (e.g. N consecutive correct) is an "
            "analytical design choice, not a telemetry gap."
        ),
    ),
    # --- Trace the Path -------------------------------------------------
    RegisteredMetric(
        metric_id="trace_path_completion_ms",
        display_name="Completion time",
        description="Time to complete one Trail Making variant attempt.",
        unit="ms",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.TRACE_THE_PATH,
        aggregation=AggregationMethod.MEDIAN,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("response_time_ms",),
        verification_note=(
            "Assumes one events row per completed attempt so "
            "response_time_ms represents whole-task completion time; this "
            "assumption is UNVERIFIED but uses only a verified column."
        ),
    ),
    RegisteredMetric(
        metric_id="trace_path_stroke_velocity",
        display_name="Stroke velocity",
        description="Average pointer movement velocity during tracing.",
        unit="px/s",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.TRACE_THE_PATH,
        aggregation=AggregationMethod.MEAN,
        telemetry_source=_JSONB,
        required_fields=("metrics.stroke_velocity",),
        supports_baseline_normalization=True,
        verification_note="No verified column; proposed metrics.stroke_velocity.",
    ),
    RegisteredMetric(
        metric_id="trace_path_lifts",
        display_name="Pointer lifts",
        description="Number of times the pointer was lifted during tracing.",
        unit="count",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.TRACE_THE_PATH,
        aggregation=AggregationMethod.MEAN,
        telemetry_source=_JSONB,
        required_fields=("metrics.lifts",),
        verification_note="No verified column; proposed metrics.lifts.",
    ),
    RegisteredMetric(
        metric_id="trace_path_jitter",
        display_name="Jitter",
        description="Stroke-path irregularity during tracing.",
        unit="px",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.TRACE_THE_PATH,
        aggregation=AggregationMethod.MEAN,
        telemetry_source=_JSONB,
        required_fields=("metrics.jitter",),
        verification_note="No verified column; proposed metrics.jitter.",
    ),
    RegisteredMetric(
        metric_id="trace_path_b_minus_a_ms",
        display_name="Trail B minus Trail A",
        description="Variant-B completion time minus variant-A completion time.",
        unit="ms",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.EXECUTIVE,
        game_id=GameId.TRACE_THE_PATH,
        aggregation=AggregationMethod.DIFFERENCE,
        telemetry_source=_JSONB,
        required_fields=("response_time_ms", "metrics.variant"),
        verification_note=(
            "response_time_ms is verified, but distinguishing variant A "
            "from B requires a field not confirmed to exist; proposed as "
            "metrics.variant. Master spec S26: never compare B and A from "
            "incompatible sessions."
        ),
    ),
    # --- My Day -----------------------------------------------------------
    RegisteredMetric(
        metric_id="my_day_orientation_accuracy",
        display_name="Orientation accuracy",
        description="Proportion of correct orientation-task trials.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.MY_DAY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct",),
        verification_note="Uses only the verified 'correct' column.",
    ),
    # --- Lamps of the Festival -----------------------------------------
    RegisteredMetric(
        metric_id="lamps_forward_span_achieved",
        display_name="Forward span achieved",
        description="Longest forward spatial sequence correctly reproduced.",
        unit="items",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.LAMPS_OF_THE_FESTIVAL,
        aggregation=AggregationMethod.MAX_ACHIEVED,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.direction"),
        verification_note="Same direction-field gap as Market Basket.",
    ),
    RegisteredMetric(
        metric_id="lamps_backward_span_achieved",
        display_name="Backward span achieved",
        description="Longest backward spatial sequence correctly reproduced.",
        unit="items",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.LAMPS_OF_THE_FESTIVAL,
        aggregation=AggregationMethod.MAX_ACHIEVED,
        telemetry_source=_JSONB,
        required_fields=("correct", "metrics.direction"),
        verification_note="Same direction-field gap as Market Basket.",
    ),
    RegisteredMetric(
        metric_id="lamps_sequence_error_rate",
        display_name="Sequence error rate",
        description="Proportion of trials with a sequence-order error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.LAMPS_OF_THE_FESTIVAL,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='sequence_error' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="lamps_item_error_rate",
        display_name="Item error rate",
        description="Proportion of trials with an item-identity error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.LAMPS_OF_THE_FESTIVAL,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='item_error' is a documented value.",
    ),
    # --- Name the Harvest -------------------------------------------------
    RegisteredMetric(
        metric_id="name_harvest_items_named",
        display_name="Items named",
        description="Number of correct, non-repeated items named within the 60s window.",
        unit="items",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.LANGUAGE,
        game_id=GameId.NAME_THE_HARVEST,
        aggregation=AggregationMethod.COUNT,
        telemetry_source=_DERIVED,
        required_fields=("correct",),
        verification_note=(
            "Derivable by counting correct=true trials within the session; "
            "relies on the tablet emitting one event per named item, which "
            "is UNVERIFIED but uses only a verified column."
        ),
    ),
    RegisteredMetric(
        metric_id="name_harvest_clusters",
        display_name="Semantic clusters",
        description="Number of semantically related item clusters produced.",
        unit="clusters",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.LANGUAGE,
        game_id=GameId.NAME_THE_HARVEST,
        aggregation=AggregationMethod.COUNT,
        telemetry_source=_JSONB,
        required_fields=("metrics.cluster_id",),
        verification_note=(
            "Requires either a category taxonomy for item_id values or an "
            "explicit per-item cluster tag; proposed as metrics.cluster_id."
        ),
    ),
    RegisteredMetric(
        metric_id="name_harvest_switches",
        display_name="Cluster switches",
        description="Number of transitions between semantic clusters.",
        unit="switches",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.LANGUAGE,
        game_id=GameId.NAME_THE_HARVEST,
        aggregation=AggregationMethod.COUNT,
        telemetry_source=_JSONB,
        required_fields=("metrics.cluster_id",),
        verification_note="Same basis as name_harvest_clusters.",
    ),
    # --- Weaving Patterns -------------------------------------------------
    RegisteredMetric(
        metric_id="weaving_mirror_error_rate",
        display_name="Mirror error rate",
        description="Proportion of trials with a mirror-image confusion error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.WEAVING_PATTERNS,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='mirror' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="weaving_rotation_error_rate",
        display_name="Rotation error rate",
        description="Proportion of trials with a rotation confusion error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.WEAVING_PATTERNS,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='rotation' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="weaving_detail_error_rate",
        display_name="Detail error rate",
        description="Proportion of trials with a fine-detail discrimination error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.WEAVING_PATTERNS,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='detail' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="weaving_random_error_rate",
        display_name="Random error rate",
        description="Proportion of trials with an unstructured random error.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.VISUOSPATIAL,
        game_id=GameId.WEAVING_PATTERNS,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct", "error_class"),
        verification_note="error_class='random' is a documented value.",
    ),
    # --- Sounds of Home -----------------------------------------------
    RegisteredMetric(
        metric_id="sounds_home_hit_rate",
        display_name="Hit rate",
        description="Proportion of target stimuli correctly responded to.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.ATTENTION,
        game_id=GameId.SOUNDS_OF_HOME,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("correct",),
        verification_note="Uses only the verified 'correct' column.",
    ),
    RegisteredMetric(
        metric_id="sounds_home_false_alarm_rate",
        display_name="False alarm rate",
        description="Proportion of non-target stimuli incorrectly responded to.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.ATTENTION,
        game_id=GameId.SOUNDS_OF_HOME,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("error_class",),
        verification_note="error_class='false_alarm' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="sounds_home_miss_rate",
        display_name="Miss rate",
        description="Proportion of target stimuli not responded to.",
        unit="proportion",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.STRUCTURAL_ERROR_PATTERN,
        domain=Domain.ATTENTION,
        game_id=GameId.SOUNDS_OF_HOME,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("error_class",),
        verification_note="error_class='miss' is a documented value.",
    ),
    RegisteredMetric(
        metric_id="sounds_home_rt_sd",
        display_name="Reaction-time variability",
        description="Standard deviation of response time across trials in a session.",
        unit="ms",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.ATTENTION,
        game_id=GameId.SOUNDS_OF_HOME,
        aggregation=AggregationMethod.STDDEV,
        telemetry_source=_VERIFIED_COLUMN,
        required_fields=("response_time_ms",),
        verification_note="Uses only the verified response_time_ms column.",
    ),
    RegisteredMetric(
        metric_id="sounds_home_block_hit_rate",
        display_name="Per-block hit rate",
        description="Hit rate computed separately for each of the three 30s blocks.",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.ATTENTION,
        game_id=GameId.SOUNDS_OF_HOME,
        aggregation=AggregationMethod.RATE,
        telemetry_source=_DERIVED,
        required_fields=("correct", "ts"),
        verification_note=(
            "Derivable by binning ts into three ~30s windows relative to "
            "session start, using only verified columns - but this assumes "
            "the session is one continuous 90s run with no pauses, which "
            "is UNVERIFIED."
        ),
    ),
    RegisteredMetric(
        metric_id="sounds_home_block_rt",
        display_name="Per-block reaction time",
        description="Median response time computed separately for each of the three 30s blocks.",
        unit="ms",
        direction=Direction.LOWER_IS_BETTER,
        metric_type=MetricType.BEHAVIOURAL,
        domain=Domain.ATTENTION,
        game_id=GameId.SOUNDS_OF_HOME,
        aggregation=AggregationMethod.MEDIAN,
        telemetry_source=_DERIVED,
        required_fields=("response_time_ms", "ts"),
        verification_note="Same block-binning basis and caveat as sounds_home_block_hit_rate.",
    ),
)

METRIC_REGISTRY: dict[str, RegisteredMetric] = {metric.metric_id: metric for metric in METRICS}
