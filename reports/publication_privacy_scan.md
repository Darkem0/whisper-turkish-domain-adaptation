# Publication privacy scan

Result: `PASS`

- Secret-pattern scan found no credential value or private key. `.env.example` contains an empty `HF_TOKEN=` placeholder only; prose occurrences of “token” are technical discussion.
- The exact local project path in `docs/codex_project_archaeology_prompt.md` was replaced with `<PROJECT_ROOT>`.
- Remaining `C:\Users\...` text is a redacted example explaining what must not be published, not a resolvable private path.
- No tracked raw audio, transcript, prediction JSONL, private manifest, checkpoint, adapter, process log, PID/state, or company-domain artefact is included.
- No file exceeds 1 MiB in the publication diff.
- Untracked local paths are represented in the public classification report by short path hashes only. Full names and sizes remain in the external safety record.
