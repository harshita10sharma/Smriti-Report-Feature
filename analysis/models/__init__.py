"""Typed domain objects for the Report Engine.

Raw dictionaries from telemetry or the database are converted into
these validated objects at the system boundary (see
``analysis.telemetry``); internal code should never pass untyped
dicts between layers.
"""
