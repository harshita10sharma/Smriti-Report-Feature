"""Temporal-integrity helper (master spec S29).

The aggregation engine itself has no notion of "now" - it aggregates
exactly whatever ``RawObservation`` sequence it is given, which is
what makes it deterministic (see the determinism tests in
``tests/aggregation/test_engine_cross_cutting.py``). Callers building
a historical report for some cutoff date are responsible for
filtering *before* calling the engine; this function is the one
canonical way to do that, so future callers (e.g. a Phase 6+
longitudinal trajectory) do not each reinvent slightly different
cutoff logic.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.aggregation.models import RawObservation


def filter_by_cutoff(
    observations: Sequence[RawObservation], cutoff_ts: int
) -> list[RawObservation]:
    """Return only observations with ``ts <= cutoff_ts``.

    A historical aggregation must never be influenced by an
    observation that occurred after its report cutoff.
    """
    return [observation for observation in observations if observation.ts <= cutoff_ts]
