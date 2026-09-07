from analysis.models.enums import Domain
from analysis.telemetry.adapter import event_to_trial
from analysis.telemetry.validation import validate_event
from tests.fixtures.telemetry_fixtures import valid_event


def test_adapter_copies_verified_fields_across() -> None:
    event, issues = validate_event(valid_event())
    assert event is not None
    trial = event_to_trial(event)

    assert trial.event_id == event.id
    assert trial.patient_id == event.patient_id
    assert trial.session_id == event.session_id
    assert trial.game_id == event.game_id
    assert trial.domain == Domain.MEMORY
    assert trial.trial_index == event.trial_index
    assert trial.correct == event.correct
    assert trial.response_time_ms == event.response_time_ms
    assert trial.ts == event.ts


def test_adapter_passes_metrics_through_unchanged_without_interpreting_it() -> None:
    event, issues = validate_event(
        valid_event(metrics={"some_future_key": "opaque-value"})
    )
    assert event is not None
    trial = event_to_trial(event)
    assert trial.metrics == {"some_future_key": "opaque-value"}


def test_adapter_maps_item_difficulty_to_difficulty() -> None:
    event, issues = validate_event(valid_event(item_difficulty=2.5))
    assert event is not None
    trial = event_to_trial(event)
    assert trial.difficulty == 2.5


def test_adapter_result_is_a_distinct_immutable_object() -> None:
    event, issues = validate_event(valid_event())
    assert event is not None
    trial = event_to_trial(event)
    trial_2 = event_to_trial(event)
    assert trial == trial_2
    assert trial is not trial_2
