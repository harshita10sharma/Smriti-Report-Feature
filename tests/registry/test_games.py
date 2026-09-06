import pydantic
import pytest

from analysis.models.enums import Domain, GameId
from analysis.registry.games import GameDefinition


def _make_game(**overrides: object) -> GameDefinition:
    fields: dict[str, object] = {
        "game_id": GameId.MARKET_BASKET,
        "display_name": "Market Basket",
        "instrument": "Word span",
        "primary_domain": Domain.MEMORY,
        "secondary_domains": (Domain.ATTENTION,),
        "constructs": ("word span",),
        "required_event_fields": ("patient_id", "session_id", "game_id", "domain", "ts"),
    }
    fields.update(overrides)
    return GameDefinition.model_validate(fields)


def test_valid_game_definition() -> None:
    game = _make_game()
    assert game.primary_domain is Domain.MEMORY


def test_primary_domain_cannot_also_be_secondary() -> None:
    with pytest.raises(pydantic.ValidationError, match="must not also appear"):
        _make_game(secondary_domains=(Domain.MEMORY,))


def test_required_and_optional_fields_cannot_overlap() -> None:
    with pytest.raises(pydantic.ValidationError, match="both required and optional"):
        _make_game(
            required_event_fields=("ts",),
            optional_event_fields=("ts",),
        )


def test_secondary_domains_default_to_empty() -> None:
    game = _make_game(secondary_domains=())
    assert game.secondary_domains == ()
