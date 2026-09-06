"""The canonical game -> metric -> domain registry.

This package is the single source of truth for game analytics (master
spec S22). No other module should hard-code a game's domain mapping,
metric list, or telemetry requirements - it must look them up here.
"""
