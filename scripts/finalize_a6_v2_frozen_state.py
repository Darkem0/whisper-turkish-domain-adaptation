"""Atomically finalize A6 frozen-evaluation state after a passed audit."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).with_name("finalize_a5_v2_frozen_state.py")


def main() -> None:
    code = (
        SOURCE.read_text(encoding="utf-8")
        .replace("A5_v2", "A6_v2")
        .replace("a5_v2", "a6_v2")
        .replace("22344", "9504")
    )
    namespace = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
    exec(compile(code, str(Path(__file__).resolve()), "exec"), namespace)


if __name__ == "__main__":
    main()
