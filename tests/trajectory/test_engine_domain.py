from collections.abc import Sequence
from datetime import date

from analysis.baseline.models import BaselineObservation
from analysis.models.enums import Direction, Domain, QualityStatus
from analysis.trajectory.engine import estimate_domain_trajectories
from tests.fixtures.baseline_fixtures import make_observation

_AS_OF = date(2026, 1, 30)
_UNGATED_METRIC = "sort_harvest_perseverative_error_rate"
_GATED_METRIC = "sort_harvest_switch_cost_ms"  # metrics_jsonb_unverified


def test_domain_trajectories_returns_independent_per_metric_entries() -> None:
    observations_by_metric: dict[str, Sequence[BaselineObservation]] = {
        _UNGATED_METRIC: [
            make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(4)
        ]
    }
    trajectories = estimate_domain_trajectories(
        Domain.EXECUTIVE, "p1", observations_by_metric, _AS_OF
    )
    assert _GATED_METRIC in trajectories
    assert trajectories[_GATED_METRIC].quality == QualityStatus.UNAVAILABLE
    assert trajectories[_GATED_METRIC].points == ()
    assert trajectories[_GATED_METRIC].metric_direction == Direction.LOWER_IS_BETTER

    assert _UNGATED_METRIC in trajectories
    assert trajectories[_UNGATED_METRIC].quality == QualityStatus.SUFFICIENT
    assert len(trajectories[_UNGATED_METRIC].points) == 4

    # No composite/overall domain entry - only per-metric keys registered
    # to this domain.
    assert "overall" not in trajectories
    assert "composite" not in trajectories


def test_metric_missing_from_observations_dict_still_gets_a_trajectory() -> None:
    trajectories = estimate_domain_trajectories(Domain.EXECUTIVE, "p1", {}, _AS_OF)
    assert trajectories[_UNGATED_METRIC].quality == QualityStatus.UNAVAILABLE
    assert trajectories[_UNGATED_METRIC].points == ()
