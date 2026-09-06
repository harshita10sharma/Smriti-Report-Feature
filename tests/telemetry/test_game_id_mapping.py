import pytest

from analysis.models.enums import GameId
from analysis.telemetry.game_id_mapping import resolve_game_id


@pytest.mark.parametrize("game_id", list(GameId))
def test_every_canonical_id_resolves_to_itself(game_id: GameId) -> None:
    assert resolve_game_id(game_id.value) is game_id


def test_documented_faces_family_alias_resolves() -> None:
    assert resolve_game_id("faces_family") is GameId.FACES_OF_MY_FAMILY


def test_unknown_raw_game_id_resolves_to_none() -> None:
    assert resolve_game_id("some_game_nobody_registered") is None


def test_empty_string_resolves_to_none() -> None:
    assert resolve_game_id("") is None
