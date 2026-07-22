# Limitations

- The bundled fixture is not speech audio and the runner does not execute Whisper training or inference.
- The metrics implementation is intentionally small and should be independently reviewed before a formal study.
- Repeat-safe suppression can remove legitimate repetition; it needs domain-specific error analysis.
- Domain routing can introduce selection bias and should include a base-model fallback.
- No historical private metrics are exported by this repository.
