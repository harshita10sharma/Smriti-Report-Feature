"""Centralized trajectory configuration.

As with ``analysis.baseline.config``, these are explicit engineering
defaults, not clinical thresholds - no real deployed telemetry exists
yet for this project to calibrate against. Revisit once real
session-density data is available.
"""

from __future__ import annotations

#: Minimum number of distinct-day trajectory points required before a
#: trend direction may be computed at all. Purpose: a slope drawn
#: through fewer than 3 points is not distinguishable from noise or an
#: artifact of exactly 2 data points always forming a "perfect" line -
#: it is not evidence of a trend. Units: distinct calendar days with
#: usable evidence. Default: 3 (the smallest count for which a linear
#: fit has any residual/fit-quality information at all). Not a
#: clinical threshold.
MINIMUM_TRAJECTORY_POINTS = 3

#: A trend is classified STABLE (rather than INCREASING/DECREASING)
#: when the total change predicted by the fitted slope across the
#: observed time span is smaller than this fraction of the
#: trajectory's own robust variability (median absolute deviation of
#: its raw values). Purpose: scales the "is this slope meaningful"
#: question to each metric's own observed noise level, rather than an
#: arbitrary absolute number that would not generalize across metrics
#: measured in different units. Units: none (a ratio). Default: 0.5 -
#: an engineering judgment call, not derived from clinical data.
STABLE_THRESHOLD_RATIO = 0.5
