from __future__ import annotations


GLOBAL_FATAL_MARKERS = (
    "locked v2d artifact changed",
    "training_lock",
    "eval_lock",
    "acceptance_lock",
    "leakage",
    "pinned revision",
    "schedule sha",
    "manifest corruption",
    "disk safety minimum",
)


def is_global_fatal(message: str) -> bool:
    text = message.lower()
    return any(marker in text for marker in GLOBAL_FATAL_MARKERS)


def next_after_failure(state: str) -> str:
    mapping = {
        "A1_FINALIZE": "A1_LOCK",
        "A1_LOCK": "A2_TRAIN",
        "A2_TRAIN": "A2_EVAL",
        "A2_EVAL": "A2_FINALIZE",
        "A2_FINALIZE": "A3_TRAIN",
        "A3_TRAIN": "A3_EVAL",
        "A3_EVAL": "A3_FINALIZE",
        "A3_FINALIZE": "A6_TRAIN",
        "A6_TRAIN": "A6_EVAL",
        "A6_EVAL": "A6_FINALIZE",
        "A6_FINALIZE": "COMPARISON_REPORT",
        "COMPARISON_REPORT": "DONE",
    }
    return mapping[state]


def watchdog_should_restart(*, supervisor_alive: bool, state: str, restarts: int) -> bool:
    return not supervisor_alive and state != "DONE" and restarts < 20
