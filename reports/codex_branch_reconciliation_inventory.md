# Codex branch reconciliation inventory

## Git topology

- Main base: `06a2ca672dcda383a1a5f89a6f733b6c51bbd7ff`
- Source snapshot: `793c730801a91cb6f4212c23326197a077cf7e5d`
- Source/main merge base: none, as expected for the unrelated historical source branch
- Publication branch: `codex/reconcile-whisper-research-docs`, created directly from `origin/main`
- Reconciliation method: file-by-file review; no merge, cherry-pick, rebase, unrelated-history override, or force push

## Review scope

| surface | paths reviewed or classified | treatment |
|---|---:|---|
| `origin/main` tracked tree | 40 | retained as publication base |
| detached source snapshot | 152 | content comparison; no bulk import |
| original dirty worktree untracked paths | 268 | name/size metadata classification only |
| authoritative local evidence | selected checkpoint locks, progress, metrics, P7 comparison | read-only validation |

The earlier archaeology inventory counted 201,256 local files, dominated by materialized data. That count is historical scan metadata, not publication scope.

## Reconciliation decisions

- Imported/adapted 12 aggregate, non-sensitive reports from the source snapshot.
- Merged new evidence into the existing comprehensive main documents instead of replacing them with shorter source versions.
- Kept the full main archive, timeline, research-vs-executed matrix, practical guide, research report, catalogue, negative-results, reproducibility, and provenance documents.
- Removed the case-only three-line duplicate `docs/NEGATIVE_RESULTS.md`; retained the comprehensive `docs/negative_results.md`.
- Did not import raw runs, predictions, manifests, checkpoints, audio, transcripts, state, logs, caches, or unknown untracked files.

## Special automation review

| file | decision | reason |
|---|---|---|
| `automation/experiment_runner.py` | `PRIVATE_LOCAL_TOOL` | local evaluation-lock, Git-state, run and process orchestration |
| `automation/supervisor.py` | `PRIVATE_LOCAL_TOOL` | local PID/state and experiment queue behaviour |
| `scripts/Start-WhisperResearch.ps1` | `DOCUMENT_ONLY` | environment-specific worker/PID startup and stale-PID removal |
| `scripts/Watch-WhisperResearch.ps1` | `DOCUMENT_ONLY` | local monitoring wrapper; not needed by the public scaffold |

Their reusable concepts are already described in `docs/reproducibility.md` and the implementation sections of the public archive.
