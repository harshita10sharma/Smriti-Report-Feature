import pydantic
import pytest

from analysis.models.enums import Domain
from analysis.models.telemetry import Session, TelemetryEvent, Trial


def test_event_defaults_metrics_to_empty_dict() -> None:
    event = TelemetryEvent(
        id="e1",
        patient_id="p1",
        session_id="s1",
        game_id="market_basket",
        domain=Domain.MEMORY,
        ts=1_700_000_000_000,
    )
    assert event.metrics == {}
    assert event.hint_level == 0


def test_event_is_immutable() -> None:
    event = TelemetryEvent(
        id="e1",
        patient_id="p1",
        session_id="s1",
        game_id="market_basket",
        domain=Domain.MEMORY,
        ts=1,
    )
    with pytest.raises(pydantic.ValidationError):
        event.hint_level = 5


def test_event_rejects_domain_outside_the_five_values() -> None:
    with pytest.raises(pydantic.ValidationError):
        TelemetryEvent.model_validate(
            {
                "id": "e1",
                "patient_id": "p1",
                "session_id": "s1",
                "game_id": "market_basket",
                "domain": "overall_cognition",
                "ts": 1,
            }
        )


def test_event_preserves_unknown_extra_fields() -> None:
    event = TelemetryEvent.model_validate(
        {
            "id": "e1",
            "patient_id": "p1",
            "session_id": "s1",
            "game_id": "market_basket",
            "domain": "memory",
            "ts": 1,
            "some_future_column": "unrecognized-but-kept",
        }
    )
    assert event.model_extra is not None
    assert event.model_extra["some_future_column"] == "unrecognized-but-kept"


def test_session_requires_game_ids_as_raw_text() -> None:
    session = Session(id="s1", patient_id="p1", started_at=100, game_ids="market_basket")
    assert session.game_ids == "market_basket"


def test_session_is_immutable() -> None:
    session = Session(id="s1", patient_id="p1", started_at=100, game_ids="market_basket")
    with pytest.raises(pydantic.ValidationError):
        session.ended_at = 200


def test_trial_rejects_unknown_fields() -> None:
    with pytest.raises(pydantic.ValidationError):
        Trial.model_validate(
            {
                "event_id": "e1",
                "patient_id": "p1",
                "session_id": "s1",
                "game_id": "market_basket",
                "domain": "memory",
                "trial_index": 0,
                "item_id": None,
                "difficulty": None,
                "correct": True,
                "response_time_ms": 500,
                "error_class": None,
                "trial_context": None,
                "metrics": {},
                "ts": 1,
                "unexpected_field": "not allowed",
            }
        )
