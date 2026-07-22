"""Small deterministic VAD/segmentation condition helper for experiment design."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Window:
    start: float
    end: float
    energy: float


def vad_segments(windows: list[Window], threshold: float) -> list[Window]:
    """Select non-empty windows above a declared synthetic threshold."""
    return [window for window in windows if window.end > window.start and window.energy >= threshold]


def segmentation_condition(windows: list[Window], threshold: float) -> dict[str, float | int]:
    kept = vad_segments(windows, threshold)
    return {
        "threshold": threshold,
        "input_windows": len(windows),
        "active_windows": len(kept),
        "active_seconds": round(sum(window.end - window.start for window in kept), 3),
    }
