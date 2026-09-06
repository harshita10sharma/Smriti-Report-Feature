"""Mapping from the reference backend's raw, unconstrained
``events.game_id`` text column to this project's canonical
``GameId`` enum.

The only two raw values ever actually observed by this project are
``"market_basket"`` and ``"faces_family"`` - both appear solely as
seed data in the reference backend's ``docs/rls-test.sql`` RLS-test
fixture, not confirmed production values from a real game client
(REPORT_READINESS_AUDIT.md S3/S14). ``"market_basket"`` matches this
project's canonical ID exactly; ``"faces_family"`` does not match
``"faces_of_my_family"`` and is included here only as a documented,
provisional alias - not a verified fact about what the real client
sends.

An unrecognized raw game_id is never guessed at: it is reported as
unresolvable so the caller can quarantine the record (master spec
S15: never invent event fields and claim the real client sends them).
"""

from __future__ import annotations

from analysis.models.enums import GameId

#: raw events.game_id string -> canonical GameId, for every value this
#: project has ever actually seen anywhere (including test fixtures).
#: Extending this map for a new observed raw value is a deliberate,
#: reviewable change - never done implicitly by fuzzy-matching.
_RAW_GAME_ID_ALIASES: dict[str, GameId] = {
    # Canonical IDs also accepted verbatim, so a client that already
    # sends our canonical spelling needs no alias entry.
    **{member.value: member for member in GameId},
    # Observed only in docs/rls-test.sql seed data (RLS-test fixture,
    # not a confirmed production value) - REPORT_READINESS_AUDIT.md S14.
    "faces_family": GameId.FACES_OF_MY_FAMILY,
}


def resolve_game_id(raw_game_id: str) -> GameId | None:
    """Map a raw telemetry game_id string to a canonical GameId.

    Returns ``None`` (never raises, never guesses) if the raw value is
    not recognized - the caller is responsible for treating that as a
    validation error, not for falling back to a best guess.
    """
    return _RAW_GAME_ID_ALIASES.get(raw_game_id)
