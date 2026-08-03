# A5 possible remediation plan — no manifest materialized

The completed automatic audit identifies seven confirmed empty transcripts; their underlying label/audio status still requires human review. Placeholder and duplicate findings remain review signals, not automatic removals. A0–A4 frozen manifests and validation artefacts remain immutable.

After reviewer decisions only, classify rows as: `confirmed_bad_row_quarantine`, `relabel_required`, `valid_repeated_script`, `template_down_weighting_candidate`, `source_level_investigation_required`, or `no_action`. Any future versioned A5 manifest must lock source-manifest hashes, excluded rows and rationale, reviewer decisions, new manifest hashes, and a fresh train/validation leakage audit.
