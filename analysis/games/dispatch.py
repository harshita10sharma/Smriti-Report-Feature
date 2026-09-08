"""Single dispatch point for all nine game analyzers (master spec S76).

Every game module in this package exports one function with an
identical signature: ``analyze(patient_id, session_id, ts, trials) ->
GameAnalysisResult``. This module is the only place that maps a
``GameId`` to its analyzer - callers elsewhere (e.g. a future
domain-aggregation stage) must go through ``analyze_game`` rather than
writing their own ``if game_id == ...`` chain.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from analysis.games import (
    faces,
    lamps,
    market_basket,
    my_day,
    name_harvest,
    sort_harvest,
    sounds_home,
    trace_path,
    weaving,
)
from analysis.games.base import GameAnalysisResult
from analysis.models.enums import GameId
from analysis.models.telemetry import Trial

AnalyzeFn = Callable[[str, str, int, Sequence[Trial]], GameAnalysisResult]

_ANALYZERS: dict[GameId, AnalyzeFn] = {
    GameId.FACES_OF_MY_FAMILY: faces.analyze,
    GameId.MARKET_BASKET: market_basket.analyze,
    GameId.SORT_THE_HARVEST: sort_harvest.analyze,
    GameId.TRACE_THE_PATH: trace_path.analyze,
    GameId.MY_DAY: my_day.analyze,
    GameId.LAMPS_OF_THE_FESTIVAL: lamps.analyze,
    GameId.NAME_THE_HARVEST: name_harvest.analyze,
    GameId.WEAVING_PATTERNS: weaving.analyze,
    GameId.SOUNDS_OF_HOME: sounds_home.analyze,
}


def analyze_game(
    game_id: GameId,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
) -> GameAnalysisResult:
    """Run the correct analyzer for ``game_id``.

    Raises ``KeyError`` if ``game_id`` is somehow not one of the nine
    canonical games - this should be unreachable in practice since
    ``GameId`` is a closed enum and ``_ANALYZERS`` covers every member
    (enforced by the module-level assertion below).
    """
    return _ANALYZERS[game_id](patient_id, session_id, ts, trials)


assert set(_ANALYZERS) == set(GameId), (
    "every canonical GameId must have a registered analyzer in "
    "analysis.games.dispatch._ANALYZERS"
)
