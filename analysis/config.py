"""Configuration management.

Centralizes every environment-derived setting the Report Engine uses.
No other module should call ``os.environ`` directly - this keeps
configuration separated from business logic (master spec S58) and
gives one place to validate required values at startup (S121).

Only the standard library is used here deliberately: at this stage a
handful of environment variables do not justify adding
``pydantic-settings`` as a dependency (master spec S54, dependency
discipline). This can be revisited if configuration grows materially
more complex.

Secret values are never logged or included in error messages - only
the *name* of a missing variable is reported.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from analysis.errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    """Typed, validated configuration for the Report Engine process.

    Fields are grouped by when they become required:

    - Always required: none yet at this foundation stage.
    - Required once database integration is implemented (a later
      phase): ``supabase_url``, ``supabase_service_role_key``.
    - Required once the nightly analysis endpoint is implemented:
      ``internal_shared_secret``.

    They are optional (``None``-able) here so this module is usable
    before those later phases exist, but every consumer of a
    not-yet-required field must call the field's own guard (e.g.
    ``require_supabase()``) rather than assuming it is set.
    """

    log_level: str
    supabase_url: str | None
    supabase_service_role_key: str | None
    internal_shared_secret: str | None

    def require_supabase(self) -> tuple[str, str]:
        """Return (url, service_role_key), raising if either is unset."""
        if not self.supabase_url or not self.supabase_service_role_key:
            raise ConfigurationError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required "
                "for any operation that reads backend data, but at least "
                "one is not set."
            )
        return self.supabase_url, self.supabase_service_role_key

    def require_internal_shared_secret(self) -> str:
        """Return the shared secret used to authenticate the nightly
        analysis trigger, raising if it is unset."""
        if not self.internal_shared_secret:
            raise ConfigurationError(
                "INTERNAL_SHARED_SECRET is required to authenticate "
                "inbound analysis-trigger requests, but is not set."
            )
        return self.internal_shared_secret


def load_settings() -> Settings:
    """Load settings from the process environment.

    Never raises for fields that are legitimately optional at this
    stage of the project; raises ``ConfigurationError`` only for
    values that are present but structurally invalid.
    """
    log_level = os.environ.get("REPORT_ENGINE_LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        raise ConfigurationError(
            f"REPORT_ENGINE_LOG_LEVEL must be one of {sorted(valid_levels)}, "
            f"got an invalid value."
        )

    return Settings(
        log_level=log_level,
        supabase_url=os.environ.get("SUPABASE_URL") or None,
        supabase_service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or None,
        internal_shared_secret=os.environ.get("INTERNAL_SHARED_SECRET") or None,
    )
