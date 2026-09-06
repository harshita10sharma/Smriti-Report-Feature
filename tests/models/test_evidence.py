import pydantic
import pytest

from analysis.models.enums import Domain, EvidenceSeverity, QualityStatus
from analysis.models.evidence import Evidence


def _make_evidence(**overrides: object) -> Evidence:
    fields: dict[str, object] = {
        "evidence_id": "ev1",
        "patient_id": "p1",
        "domain": Domain.EXECUTIVE,
        "metric_ids": ("switch_cost_ms",),
        "game_ids": ("sort_the_harvest",),
        "baseline_period": None,
        "comparison_period": None,
        "change_point": None,
        "direction": None,
        "severity": EvidenceSeverity.MODERATE,
        "persistent": None,
        "concordant_metric_ids": (),
        "contradicting_metric_ids": (),
        "supporting_session_ids": ("s1", "s2"),
        "confounder_context": (),
        "engagement_status": QualityStatus.SUFFICIENT,
        "confidence": 0.6,
        "data_quality": QualityStatus.SUFFICIENT,
        "rationale": "Perseverative errors increased across three sessions.",
        "limitations": (),
    }
    fields.update(overrides)
    return Evidence.model_validate(fields)


def test_valid_evidence_round_trips() -> None:
    evidence = _make_evidence()
    assert evidence.domain is Domain.EXECUTIVE


def test_evidence_without_metric_ids_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="at least one metric_id"):
        _make_evidence(metric_ids=())


def test_evidence_without_supporting_sessions_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="at least one supporting session_id"):
        _make_evidence(supporting_session_ids=())


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_evidence_rejects_confidence_outside_probability_range(
    confidence: float,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        _make_evidence(confidence=confidence)


def test_evidence_is_immutable() -> None:
    evidence = _make_evidence()
    with pytest.raises(pydantic.ValidationError):
        evidence.confidence = 0.9
