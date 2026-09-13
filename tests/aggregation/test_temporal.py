from analysis.aggregation.engine import aggregate_mean
from analysis.aggregation.temporal import filter_by_cutoff
from analysis.models.enums import AggregationMethod
from tests.fixtures.aggregation_fixtures import make_metric, obs


def test_filter_by_cutoff_excludes_future_observations() -> None:
    observations = obs([1.0, 2.0, 3.0], start_ts=100)  # ts 100, 101, 102
    filtered = filter_by_cutoff(observations, cutoff_ts=101)
    assert [o.ts for o in filtered] == [100, 101]


def test_filter_by_cutoff_is_inclusive_of_the_cutoff_itself() -> None:
    observations = obs([1.0], start_ts=50)
    filtered = filter_by_cutoff(observations, cutoff_ts=50)
    assert len(filtered) == 1


def test_a_historical_aggregation_is_unaffected_by_future_observations() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    historical = obs([2.0, 4.0], start_ts=0)  # ts 0, 1
    future_event = obs([1000.0], start_ts=100)[0]  # ts 100, dramatically different

    without_future = aggregate_mean(metric, "p1", historical)
    with_future_present_but_filtered = aggregate_mean(
        metric, "p1", filter_by_cutoff([*historical, future_event], cutoff_ts=1)
    )

    assert without_future.value == with_future_present_but_filtered.value == 3.0


def test_unfiltered_future_observation_would_change_the_result() -> None:
    # Sanity check that the future event genuinely would have mattered
    # if it had NOT been filtered - confirms the previous test is
    # actually exercising temporal protection, not a no-op.
    metric = make_metric(AggregationMethod.MEAN)
    historical = obs([2.0, 4.0], start_ts=0)
    future_event = obs([1000.0], start_ts=100)[0]

    with_future_unfiltered = aggregate_mean(metric, "p1", [*historical, future_event])
    assert with_future_unfiltered.value != 3.0
