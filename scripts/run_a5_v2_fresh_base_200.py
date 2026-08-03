"""Minimum-diff A5 runner derived at runtime from the verified A4 runner.

Only identifiers, A5 paths, and the LoRA layer scope/count are changed.
"""

from __future__ import annotations

from pathlib import Path


SOURCE = Path(__file__).with_name("run_a4_v2_fresh_base_200.py")


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    replacements = (
        ("A4_v2", "A5_v2"),
        ("A4_V2", "A5_V2"),
        ("a4_v2", "a5_v2"),
        ("training_a4_v2", "training_a5_v2"),
        ("a4_", "a5_"),
        (".decoder.", ".encoder."),
        ("len(targets) != 16", "len(targets) != 64"),
        ("count != 655360", "count != 2621440"),
        ("!= 655360", "!= 2621440"),
        ("655360,", "2621440,"),
    )
    for before, after in replacements:
        code = code.replace(before, after)
    namespace = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
    exec(compile(code, str(Path(__file__).resolve()), "exec"), namespace)


if __name__ == "__main__":
    main()
