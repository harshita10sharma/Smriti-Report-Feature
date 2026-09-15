"""Centralized baseline configuration (master spec S38, S49).

The specification calls for an initial baseline period of "approximately
3-5 weeks / 21-28 days," but explicitly warns against hard-coding this
without inspecting real observation density. No real deployed telemetry
currently exists for this project to inspect (per
REPORT_READINESS_AUDIT.md and the client-repo reconciliation - only
Market Basket has any client implementation at all). The values below
are therefore an explicit, documented engineering default, not a
clinical rule - they exist so the baseline engine has *a* deterministic
threshold to apply today, and are expected to be revisited once real
session-density data is available.
"""

from __future__ import annotations

#: Length of the candidate baseline window, in days, looking backward
#: from the report's "as of" date. Purpose: bounds how far back a
#: baseline estimate may draw evidence from, per the specification's
#: "3-5 weeks" framing. Units: days. Default: 28 (the upper end of the
#: specified range, chosen to maximize available evidence rather than
#: prematurely truncating it). Not a clinical threshold - revisit once
#: real session-density data exists.
BASELINE_WINDOW_DAYS = 28

#: Minimum number of usable (SUFFICIENT or LIMITED quality) session
#: observations, within the window, required before a baseline may
#: reach ESTABLISHED. Purpose: a baseline must reflect repeated
#: behavior, not one lucky/unlucky session. Units: sessions. Default: 5
#: (an engineering judgment call - enough to compute a meaningful
#: median/MAD, not derived from clinical data). Revisit once real
#: session-density data exists.
MINIMUM_BASELINE_SESSIONS = 5

#: Minimum number of distinct calendar days, among usable observations
#: within the window, required before a baseline may reach ESTABLISHED.
#: Purpose: several sessions played in one afternoon must not count as
#: "repeated behavior over time" - a baseline claiming temporal breadth
#: needs evidence actually spread across days. Units: days. Default: 5.
#: Not a clinical threshold - revisit once real session-density data
#: exists.
MINIMUM_BASELINE_DAYS = 5
