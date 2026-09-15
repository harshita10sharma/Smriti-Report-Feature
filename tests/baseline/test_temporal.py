from datetime import date

from analysis.baseline.temporal import filter_by_cutoff_date
from tests.fixtures.baseline_fixtures import make_observation


def test_filter_excludes_observations_after_cutoff() -> None:
    observations = [
        make_observation("s1", date(2026, 1, 1)),
        make_observation("s2", date(2026, 1, 15)),
        make_observation("s3", date(2026, 2, 1)),
    ]
    filtered = filter_by_cutoff_date(observations, cutoff=date(2026, 1, 15))
    assert [o.session_id for o in filtered] == ["s1", "s2"]


def test_filter_is_inclusive_of_the_cutoff_date_itself() -> None:
    observations = [make_observation("s1", date(2026, 1, 15))]
    filtered = filter_by_cutoff_date(observations, cutoff=date(2026, 1, 15))
    assert len(filtered) == 1


def test_filter_excludes_everything_before_the_earliest_cutoff() -> None:
    observations = [make_observation("s1", date(2026, 1, 1))]
    filtered = filter_by_cutoff_date(observations, cutoff=date(2025, 12, 31))
    assert filtered == []


def test_filter_of_empty_input_is_empty() -> None:
    assert filter_by_cutoff_date([], cutoff=date(2026, 1, 1)) == []
