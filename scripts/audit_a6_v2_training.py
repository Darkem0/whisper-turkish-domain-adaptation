"""Minimum-diff A6 read-only training audit derived from A5."""

from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).with_name("audit_a5_v2_training.py")


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    for before, after in (("A5_v2", "A6_v2"), ("a5_v2", "a6_v2"), ("2621440", "3276800")):
        code = code.replace(before, after)
    namespace = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
    exec(compile(code, str(Path(__file__).resolve()), "exec"), namespace)


if __name__ == "__main__":
    main()
