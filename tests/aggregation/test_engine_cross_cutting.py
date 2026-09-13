import random

import pytest

from analysis.aggregation.engine import aggregate_max_achieved, aggregate_mean, aggregate_rate
from analysis.aggregation.models import RawObservation
from analysis.models.enums import AggregationMethod
from analysis.registry import METRIC_REGISTRY
from tests.fixtures.aggregation_fixtures import make_metric, obs

# --- PROVENANCE -----------------------------------------------------------


def test_source_ids_of_contributing_observations_are_preserved() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    observations = [
        RawObservation(source_id="event-a", ts=1, value=1.0),
        RawObservation(source_id="event-b", ts=2, value=3.0),
    ]
    result = aggregate_mean(metric, "p1", observations)
    assert set(result.source_ids) == {"event-a", "event-b"}


def test_patient_identity_is_preserved_on_the_result() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    result = aggregate_mean(metric, "patient-42", obs([1.0, 2.0]))
    assert result.patient_id == "patient-42"


def test_exclusions_are_preserved_with_source_and_reason() -> None:
    metric = make_metric(AggregationMethod.MEAN, valid_range=(0.0, 10.0))
    observations = [
        RawObservation(source_id="good", ts=1, value=5.0),
        RawObservation(source_id="bad", ts=2, value=999.0),
    ]
    result = aggregate_mean(metric, "p1", observations)
    assert len(result.excluded) == 1
    assert result.excluded[0].source_id == "bad"
    assert "999.0" in result.excluded[0].reason_message


def test_ts_range_spans_contributing_observations() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    result = aggregate_mean(metric, "p1", obs([1.0, 2.0, 3.0], start_ts=100))
    assert result.ts_range == (100, 102)


# --- MISSINGNESS ------------------------------------------------------------


def test_missing_value_is_not_treated_as_zero() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    with_missing = aggregate_mean(metric, "p1", obs([4.0, None]))
    without_missing = aggregate_mean(metric, "p1", obs([4.0]))
    # If missing were silently treated as 0.0, the mean would be 2.0
    # instead of 4.0.
    assert with_missing.value == without_missing.value == 4.0


def test_no_fabricated_observation_for_a_gap() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    result = aggregate_mean(metric, "p1", obs([5.0, None, None, 5.0]))
    assert result.valid_count == 2
    assert result.missing_count == 2
    assert result.value == 5.0


# --- PATIENT ISOLATION ------------------------------------------------------


def test_patient_a_and_patient_b_results_do_not_cross_contaminate() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    observations_a = [RawObservation(source_id="a-event", ts=1, value=1.0),
                       RawObservation(source_id="a-event-2", ts=2, value=2.0)]
    observations_b = [RawObservation(source_id="b-event", ts=1, value=100.0),
                       RawObservation(source_id="b-event-2", ts=2, value=200.0)]
    result_a = aggregate_mean(metric, "patient-a", observations_a)
    result_b = aggregate_mean(metric, "patient-b", observations_b)
    assert result_a.patient_id == "patient-a"
    assert result_b.patient_id == "patient-b"
    assert result_a.value == 1.5
    assert result_b.value == 150.0
    assert set(result_a.source_ids).isdisjoint(result_b.source_ids)


# --- TELEMETRY GATES ---------------------------------------------------------


def test_unavailable_gated_registry_metric_cannot_be_aggregated() -> None:
    gated_metric = METRIC_REGISTRY["sort_harvest_switch_cost_ms"]
    with pytest.raises(AssertionError, match="attempted to aggregate"):
        aggregate_mean(gated_metric, "p1", obs([100.0, 200.0]))


def test_all_gated_registry_metrics_reject_aggregation() -> None:
    gated_metrics = [
        m for m in METRIC_REGISTRY.values() if m.telemetry_source.value != "verified_column"
        and m.telemetry_source.value != "derived_from_verified_columns"
    ]
    assert gated_metrics, "fixture assumption: at least one gated metric exists"
    for metric in gated_metrics:
        with pytest.raises(AssertionError):
            aggregate_mean(metric, "p1", obs([1.0]))


# --- DETERMINISM / INVARIANTS -----------------------------------------------


def test_aggregation_is_deterministic() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    observations = obs([3.0, 1.0, 4.0, 1.0, 5.0])
    first = aggregate_mean(metric, "p1", observations)
    second = aggregate_mean(metric, "p1", observations)
    assert first.value == second.value
    assert first.quality == second.quality


def test_mean_is_order_independent() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0]
    shuffled = values[:]
    random.Random(42).shuffle(shuffled)
    result_original = aggregate_mean(metric, "p1", obs(values))
    result_shuffled = aggregate_mean(metric, "p1", obs(shuffled))
    assert result_original.value == result_shuffled.value


def test_rate_is_always_within_declared_bounds() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    for _ in range(20):
        indicators = [float(random.Random().randint(0, 1)) for _ in range(10)]
        result = aggregate_rate(metric, "p1", obs(indicators))
        assert result.value is not None
        assert 0.0 <= result.value <= 1.0


def test_max_achieved_never_exceeds_the_largest_valid_input() -> None:
    metric = make_metric(AggregationMethod.MAX_ACHIEVED, valid_range=(0.0, 100.0))
    values = [3.0, 7.0, 2.0, 9.0]
    result = aggregate_max_achieved(metric, "p1", obs(values))
    assert result.value == max(values)
