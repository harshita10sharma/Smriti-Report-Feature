from datetime import date

import pydantic
import pytest

from analysis.baseline.models import PracticeEffectAssessment, PracticeObservationPoint
from analysis.models.enums import QualityStatus
from tests.fixtures.baseline_fixtures import make_observation


def test_baseline_observation_is_usable_when_sufficient() -> None:
    obs = make_observation("s1", date(2026, 1, 1), quality=QualityStatus.SUFFICIENT)
    assert obs.is_usable is True


def test_baseline_observation_is_usable_when_limited() -> None:
    obs = make_observation(
        "s1", date(2026, 1, 1), quality=QualityStatus.LIMITED, reason="degraded"
    )
    assert obs.is_usable is True


@pytest.mark.parametrize(
    "quality", [QualityStatus.INSUFFICIENT, QualityStatus.UNAVAILABLE]
)
def test_baseline_observation_is_not_usable_when_insufficient_or_unavailable(
    quality: QualityStatus,
) -> None:
    obs = make_observation(
        "s1", date(2026, 1, 1), value=None, quality=quality, reason="no data",
        valid_count=0, source_ids=(), ts_range=None,
    )
    assert obs.is_usable is False


def test_practice_effect_assessment_cannot_claim_correction_applied() -> None:
    with pytest.raises(pydantic.ValidationError, match="correction_applied must remain False"):
        PracticeEffectAssessment(
            patient_id="p1", metric_id="m1", status=QualityStatus.SUFFICIENT,
            reason=None, raw_trajectory=(), correction_applied=True,
        )


def test_practice_effect_assessment_insufficient_requires_reason() -> None:
    with pytest.raises(pydantic.ValidationError, match="reason is required"):
        PracticeEffectAssessment(
            patient_id="p1", metric_id="m1", status=QualityStatus.INSUFFICIENT,
            reason=None, raw_trajectory=(), correction_applied=False,
        )


def test_practice_effect_assessment_trajectory_must_be_date_ordered() -> None:
    out_of_order = (
        PracticeObservationPoint(session_id="s2", observed_on=date(2026, 1, 2), value=1.0),
        PracticeObservationPoint(session_id="s1", observed_on=date(2026, 1, 1), value=0.5),
    )
    with pytest.raises(pydantic.ValidationError, match="must be ordered"):
        PracticeEffectAssessment(
            patient_id="p1", metric_id="m1", status=QualityStatus.SUFFICIENT,
            reason=None, raw_trajectory=out_of_order, correction_applied=False,
        )


def test_practice_effect_assessment_accepts_ordered_trajectory() -> None:
    ordered = (
        PracticeObservationPoint(session_id="s1", observed_on=date(2026, 1, 1), value=0.5),
        PracticeObservationPoint(session_id="s2", observed_on=date(2026, 1, 2), value=1.0),
    )
    assessment = PracticeEffectAssessment(
        patient_id="p1", metric_id="m1", status=QualityStatus.SUFFICIENT,
        reason=None, raw_trajectory=ordered, correction_applied=False,
    )
    assert assessment.correction_applied is False
    assert len(assessment.raw_trajectory) == 2
