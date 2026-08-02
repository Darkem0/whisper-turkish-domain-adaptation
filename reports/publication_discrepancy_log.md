# Publication discrepancy log

| id | discrepancy | resolution | residual risk |
|---|---|---|---|
| D-01 | Source branch and `origin/main` have no common history | clean worktree created from `origin/main`; file-level reconciliation only | none |
| D-02 | Main tracked `docs/NEGATIVE_RESULTS.md` and `docs/negative_results.md` | retain comprehensive lowercase file; remove case-only duplicate | case-sensitive clones lose the three-line teaching duplicate, whose idea is covered elsewhere |
| D-03 | MEM2 described both as ~32.12% faster and as no meaningful speedup | distinguish early microbenchmark from later interleaved deployment validation | production-scale benefit remains unmeasured |
| D-04 | A5–A6 former zero-delta/self-comparison | mark superseded; retain corrected 4,059/27-of-28 evidence | canonical cross-run paired lock remains incomplete |
| D-05 | A7 step-200 appears in stale/original and retry locations | only isolated retry1 step-200 is authoritative | optimizer-reset continuation limits exact reproducibility |
| D-06 | A7 eval contract readiness label is stale after completion | run progress, target locks, and 28/28 integrity report govern completion | contract label remains historical |
| D-07 | Main archaeology prompt exposed an absolute user path | replaced with `<PROJECT_ROOT>` | none |
| D-08 | Local automation scripts embed environment/process assumptions | not published; document concepts only | public scaffold does not reproduce private overnight orchestration |
