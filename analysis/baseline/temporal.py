"""Temporal-integrity helper for baseline estimation (master spec S29).

Mirrors ``analysis.aggregation.temporal.filter_by_cutoff`` exactly in
policy (inclusive cutoff, never let a historical calculation see
future data) but operates on ``BaselineObservation.observed_on``
(a calendar ``date``) rather than ``RawObservation.ts`` (an epoch-ms
int) - the two types are not interchangeable, so this is the same
rule re-expressed at the type baseline estimation actually works with,
not a second, divergent cutoff mechanism.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from analysis.baseline.models import BaselineObservation


def filter_by_cutoff_date(
    observations: Sequence[BaselineObservation], cutoff: date
) -> list[BaselineObservation]:
    """Return only observations with ``observed_on <= cutoff``.

    A historical baseline must never be influenced by a session that
    occurred after its report cutoff.
    """
    return [obs for obs in observations if obs.observed_on <= cutoff]
