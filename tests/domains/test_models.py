import pydantic
import pytest

from analysis.domains.models import DomainEvidence, MetricEvidenceEntry
from analysis.models.enums import Direction, Domain, GameId, QualityStatus


def _entry(**overrides: object) -> MetricEvidenceEntry:
    fields: dict[str, object] = {
        "metric_id": "m1",
        "game_id": GameId.MY_DAY,
        "direction": Direction.HIGHER_IS_BETTER,
        "value": 0.8,
        "quality": QualityStatus.SUFFICIENT,
        "reason": None,
        "source_ids": ("e1",),
        "valid_count": 5,
    }
    fields.update(overrides)
    return MetricEvidenceEntry.model_validate(fields)


def _domain_evidence(**overrides: object) -> DomainEvidence:
    fields: dict[str, object] = {
        "patient_id": "p1",
        "domain": Domain.MEMORY,
        "quality": QualityStatus.SUFFICIENT,
        "reason": None,
        "metric_evidence": (_entry(),),
        "contributing_game_ids": (GameId.MY_DAY,),
        "usable_metric_ids": ("m1",),
        "limited_metric_ids": (),
        "insufficient_metric_ids": (),
        "unavailable_metric_ids": (),
        "usable_observation_count": 5,
    }
    fields.update(overrides)
    return DomainEvidence.model_validate(fields)


def test_valid_metric_evidence_entry() -> None:
    entry = _entry()
    assert entry.value == 0.8


def test_metric_entry_missing_value_requires_reason() -> None:
    with pytest.raises(pydantic.ValidationError, match="reason is required"):
        _entry(value=None, quality=QualityStatus.UNAVAILABLE, reason=None)


def test_metric_entry_missing_value_with_reason_is_valid() -> None:
    entry = _entry(value=None, quality=QualityStatus.UNAVAILABLE, reason="gated")
    assert entry.value is None


def test_valid_domain_evidence() -> None:
    evidence = _domain_evidence()
    assert evidence.total_registered_domain_metrics == 1


def test_domain_evidence_unavailable_requires_reason() -> None:
    with pytest.raises(pydantic.ValidationError, match="reason is required"):
        _domain_evidence(
            quality=QualityStatus.UNAVAILABLE,
            reason=None,
            usable_metric_ids=(),
            unavailable_metric_ids=("m1",),
            metric_evidence=(_entry(value=None, quality=QualityStatus.UNAVAILABLE, reason="x"),),
        )


def test_domain_evidence_insufficient_requires_reason() -> None:
    with pytest.raises(pydantic.ValidationError, match="reason is required"):
        _domain_evidence(
            quality=QualityStatus.INSUFFICIENT,
            reason=None,
            usable_metric_ids=(),
            insufficient_metric_ids=("m1",),
            metric_evidence=(_entry(value=None, quality=QualityStatus.INSUFFICIENT, reason="x"),),
        )


def test_domain_evidence_sufficient_does_not_require_reason() -> None:
    evidence = _domain_evidence(quality=QualityStatus.SUFFICIENT, reason=None)
    assert evidence.reason is None


def test_metric_id_buckets_must_partition_all_evidence() -> None:
    with pytest.raises(pydantic.ValidationError, match="do not match"):
        _domain_evidence(usable_metric_ids=())  # m1 unaccounted for


def test_limited_must_be_subset_of_usable() -> None:
    # m1 is correctly bucketed as usable, but "m2" (not even part of
    # metric_evidence) is claimed as limited - not a subset of usable.
    with pytest.raises(pydantic.ValidationError, match="subset"):
        _domain_evidence(limited_metric_ids=("m2",), usable_metric_ids=("m1",))


def test_negative_usable_observation_count_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="must not be negative"):
        _domain_evidence(usable_observation_count=-1)


def test_domain_evidence_is_immutable() -> None:
    evidence = _domain_evidence()
    with pytest.raises(pydantic.ValidationError):
        evidence.quality = QualityStatus.LIMITED
