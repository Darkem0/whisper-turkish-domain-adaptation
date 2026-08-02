# Publication test results

## Static checks

| check | result |
|---|---|
| `git diff --check` | PASS (line-ending warnings only during initial Windows inspection) |
| Markdown relative links | PASS |
| JSON/JSONL parse | PASS |
| CSV column width | PASS |
| UTF-8 decode | PASS |
| duplicate headings | PASS |
| secret scan | PASS; empty example token and prose false positives reviewed |
| local path scan | PASS after replacing exact user path |
| files larger than 1 MiB | none |
| tracked audio/checkpoint extensions | none |
| public `reports/` ignored | no |
| Ruff | BASELINE_WARNING: `tests/test_research.py` has one pre-existing unused import (`F401`); no auto-fix applied |

## CPU-only executable checks

The Windows Store `python` alias was unavailable. The existing project virtual environment was used without installing or downloading anything.

- `python -m unittest discover -s tests -v`: PASS, 5/5 tests.
- `python -m whisper_adaptation demo`: PASS, synthetic fixture only.
- `python -m whisper_adaptation evaluate --manifest experiments/adapter-routing.json`: PASS, synthetic fixture only.

No GPU job, model download, dataset download, training, inference on real audio, or frozen evaluation was run.
