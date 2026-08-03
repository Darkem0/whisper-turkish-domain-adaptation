"""Minimum-diff A5 frozen-evaluation runner derived from verified A4 logic."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).with_name("run_a4_v2_frozen_evaluation.py")


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8").replace("A4_v2", "A5_v2").replace("a4_v2", "a5_v2")
    namespace = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
    exec(compile(code, str(Path(__file__).resolve()), "exec"), namespace)


if __name__ == "__main__":
    main()
