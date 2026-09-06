"""GameDefinition: registry metadata for one canonical game.

Holds no data - it describes what a game is and what telemetry it is
expected to produce, so downstream code never hard-codes this
information (master spec S22, S32).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import Domain, GameId


class GameDefinition(BaseModel):
    """Registry metadata for one of the nine canonical games.

    ``error_classes`` lists the ``error_class`` string values this
    game is documented to use, per the ``events.error_class`` column
    comment (REPORT_READINESS_AUDIT.md S3) - that column has no DB
    CHECK constraint, so this list is the closest thing to an
    authoritative vocabulary and must be validated against at the
    telemetry-validation layer (a later phase), not assumed to be
    enforced by the database.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    game_id: GameId
    display_name: str
    instrument: str
    primary_domain: Domain
    secondary_domains: tuple[Domain, ...] = ()
    constructs: tuple[str, ...]
    error_classes: tuple[str, ...] = ()
    difficulty_dimensions: tuple[str, ...] = ()
    required_event_fields: tuple[str, ...]
    optional_event_fields: tuple[str, ...] = ()
    notes: str = ""

    @model_validator(mode="after")
    def _secondary_domains_exclude_primary(self) -> GameDefinition:
        if self.primary_domain in self.secondary_domains:
            raise ValueError(
                f"{self.game_id.value}: primary_domain "
                f"({self.primary_domain.value}) must not also appear in "
                "secondary_domains"
            )
        return self

    @model_validator(mode="after")
    def _required_and_optional_fields_do_not_overlap(self) -> GameDefinition:
        overlap = set(self.required_event_fields) & set(self.optional_event_fields)
        if overlap:
            raise ValueError(
                f"{self.game_id.value}: fields listed as both required and "
                f"optional: {sorted(overlap)}"
            )
        return self
