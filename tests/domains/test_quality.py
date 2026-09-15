import pytest

from analysis.domains.quality import classify_domain_quality
from analysis.models.enums import QualityStatus


def test_zero_registered_metrics_is_unavailable() -> None:
    status, reason = classify_domain_quality(
        total_registered=0, usable_count=0, limited_count=0,
        insufficient_count=0, unavailable_count=0,
    )
    assert status == QualityStatus.UNAVAILABLE
    assert reason is not None and "no metrics are registered" in reason


def test_all_unavailable_is_unavailable() -> None:
    status, reason = classify_domain_quality(
        total_registered=9, usable_count=0, limited_count=0,
        insufficient_count=0, unavailable_count=9,
    )
    assert status == QualityStatus.UNAVAILABLE
    assert reason is not None and "none of the 9" in reason


def test_zero_usable_with_some_insufficient_is_insufficient() -> None:
    status, reason = classify_domain_quality(
        total_registered=4, usable_count=0, limited_count=0,
        insufficient_count=1, unavailable_count=3,
    )
    assert status == QualityStatus.INSUFFICIENT
    assert reason is not None


def test_all_registered_metrics_usable_with_no_degradation_is_sufficient() -> None:
    status, reason = classify_domain_quality(
        total_registered=2, usable_count=2, limited_count=0,
        insufficient_count=0, unavailable_count=0,
    )
    assert status == QualityStatus.SUFFICIENT
    assert reason is None


def test_partial_coverage_is_limited_even_with_one_usable_metric() -> None:
    status, reason = classify_domain_quality(
        total_registered=6, usable_count=1, limited_count=0,
        insufficient_count=0, unavailable_count=5,
    )
    assert status == QualityStatus.LIMITED
    assert reason is not None and "1 of 6" in reason


def test_a_single_limited_metric_among_usable_metrics_is_domain_limited() -> None:
    status, _ = classify_domain_quality(
        total_registered=2, usable_count=2, limited_count=1,
        insufficient_count=0, unavailable_count=0,
    )
    assert status == QualityStatus.LIMITED


def test_domain_cannot_reach_sufficient_while_any_metric_is_gated() -> None:
    # Even if the one computable metric is itself perfectly sufficient,
    # the domain overall must not claim SUFFICIENT while other
    # registered metrics remain unavailable.
    status, _ = classify_domain_quality(
        total_registered=9, usable_count=3, limited_count=0,
        insufficient_count=0, unavailable_count=6,
    )
    assert status != QualityStatus.SUFFICIENT


@pytest.mark.parametrize(
    ("usable", "limited", "insufficient", "unavailable"),
    [(5, 0, 0, 0), (3, 1, 1, 0), (1, 0, 0, 4)],
)
def test_reason_is_present_whenever_quality_is_not_perfectly_sufficient(
    usable: int, limited: int, insufficient: int, unavailable: int
) -> None:
    total = usable + insufficient + unavailable
    status, reason = classify_domain_quality(
        total_registered=total, usable_count=usable, limited_count=limited,
        insufficient_count=insufficient, unavailable_count=unavailable,
    )
    if status != QualityStatus.SUFFICIENT:
        assert reason is not None
