import pytest

from analysis.aggregation.quality import EXCESSIVE_EXCLUSION_RATIO, classify_quality
from analysis.models.enums import QualityStatus


def test_zero_candidates_is_unavailable() -> None:
    status, reason = classify_quality(
        valid_count=0, excluded_count=0, missing_count=0, minimum_observations=1
    )
    assert status == QualityStatus.UNAVAILABLE
    assert reason is not None and "no observations" in reason


def test_valid_below_minimum_is_insufficient() -> None:
    status, reason = classify_quality(
        valid_count=2, excluded_count=0, missing_count=0, minimum_observations=5
    )
    assert status == QualityStatus.INSUFFICIENT
    assert reason is not None and "minimum_observations=5" in reason


def test_all_valid_meeting_minimum_is_sufficient_with_no_reason() -> None:
    status, reason = classify_quality(
        valid_count=10, excluded_count=0, missing_count=0, minimum_observations=1
    )
    assert status == QualityStatus.SUFFICIENT
    assert reason is None


def test_low_exclusion_ratio_stays_sufficient() -> None:
    # 1 excluded out of 10 candidates = 10% -> below the 50% threshold
    status, reason = classify_quality(
        valid_count=9, excluded_count=1, missing_count=0, minimum_observations=1
    )
    assert status == QualityStatus.SUFFICIENT
    assert reason is None


def test_high_exclusion_ratio_downgrades_to_limited_even_above_minimum() -> None:
    # 9 excluded out of 10 candidates = 90% -> above threshold, but the
    # single valid observation still clears minimum_observations=1.
    status, reason = classify_quality(
        valid_count=1, excluded_count=9, missing_count=0, minimum_observations=1
    )
    assert status == QualityStatus.LIMITED
    assert reason is not None and "exceeding" in reason


def test_missing_counts_toward_the_exclusion_ratio_too() -> None:
    status, _ = classify_quality(
        valid_count=1, excluded_count=0, missing_count=9, minimum_observations=1
    )
    assert status == QualityStatus.LIMITED


@pytest.mark.parametrize("valid_count", [1, 2, 3, 4])
def test_insufficient_takes_priority_over_exclusion_ratio(valid_count: int) -> None:
    # Even a 0% exclusion ratio must still be INSUFFICIENT if the
    # (higher-priority) minimum-observations check fails first.
    status, _ = classify_quality(
        valid_count=valid_count, excluded_count=0, missing_count=0, minimum_observations=5
    )
    assert status == QualityStatus.INSUFFICIENT


def test_zero_valid_but_some_candidates_present_is_insufficient_not_unavailable() -> None:
    # Distinct from the true zero-candidates case: some raw data was
    # supplied (and excluded/missing), just none of it was valid.
    status, reason = classify_quality(
        valid_count=0, excluded_count=0, missing_count=3, minimum_observations=1
    )
    assert status == QualityStatus.INSUFFICIENT
    assert reason is not None and "minimum_observations=1" in reason


def test_exclusion_ratio_boundary_is_strictly_greater_than() -> None:
    # exactly at the threshold (50%) must NOT downgrade - only strictly
    # exceeding it does.
    status, _ = classify_quality(
        valid_count=5, excluded_count=5, missing_count=0, minimum_observations=1
    )
    assert status == QualityStatus.SUFFICIENT
    assert 5 / 10 == EXCESSIVE_EXCLUSION_RATIO
