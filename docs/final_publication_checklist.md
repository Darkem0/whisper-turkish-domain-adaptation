# Final Publication Checklist

## Repository structure

- [x] Canonical research hub selected.
- [x] Companion repositories retained with independent history.
- [x] Companion commits pinned in `ecosystem/components.lock.json`.
- [x] Bootstrap script added for a single local workspace.
- [x] Unrelated Codex branch not force-merged.

## Scientific integrity

- [x] Legacy and controlled experiment series remain separate.
- [x] A5–A6 self-comparison result marked superseded.
- [x] A7 authoritative checkpoint mapping documented.
- [x] A7 optimizer-reset continuation disclosed.
- [x] Phone/G.711 results described as public-data proxies.
- [x] General-domain negative transfer retained.
- [x] Augmentation contribution labelled inconclusive.
- [x] MEM2 classified as microbenchmark-positive / deployment-inconclusive.
- [x] MEM3/MEM4 rejected when prediction drift occurred.

## Public artefacts

- [x] Turkish final manuscript.
- [x] English final manuscript.
- [x] Public aggregate metric tables.
- [x] Citation metadata.
- [x] Repository ecosystem audit.
- [x] End-to-end public architecture.
- [x] Safe Codex reconciliation prompt for remaining local artefacts.

## Privacy

- [x] No raw call audio.
- [x] No private transcripts.
- [x] No model checkpoints or adapter weights.
- [x] No credentials or `.env` files.
- [x] No internal IP/host/service topology.
- [x] No private materialized datasets.
- [x] Companion workspaces ignored through `components/`.

## Automated checks

`tests/test_canonical_publication.py` validates:

- component lock structure and commit format,
- bootstrap script syntax,
- authoritative Phone result,
- complete A7 4×7 metric grid,
- README relative links,
- proxy limitation language in both manuscripts.

## Final decision

The canonical public record is `Darkem0/whisper-turkish-domain-adaptation`. Other repositories remain preserved as runnable companion components, publication records, or discovery indexes.
