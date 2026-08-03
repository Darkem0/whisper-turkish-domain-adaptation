# Data-quality experiment schedule-impact audit

This is an exact, read-only `sample_id` intersection with locked schedules. Duplicate findings are exposure signals, not confirmed label errors.

## Input population

- Empty train transcripts: 7.
- Duplicate transcript members: train=1795, validation=30.
- Placeholder validation rows: 2 of 9081 local-validation rows (0.02202%).

## Per-experiment impact

### A2

- Empty-transcript exposure: 0 uses (0.0% of locked microbatches).
- Train duplicate-cluster exposure: 0 uses (0.0% of locked microbatches).
- Placeholder validation theoretical upper bound: 2 / 9,081 = 0.02202% of rows. The rows are validation-only and have no training-schedule exposure.
- Interpretation: a schedule intersection alone cannot attribute broad, cross-dataset A2/A3/A4 gains or regressions to these low-prevalence data-quality findings; it only quantifies potential exposure.

### A3_v2

- Empty-transcript exposure: 0 uses (0.0% of locked microbatches).
- Train duplicate-cluster exposure: 40 uses (1.25% of locked microbatches).
- Placeholder validation theoretical upper bound: 2 / 9,081 = 0.02202% of rows. The rows are validation-only and have no training-schedule exposure.
- Interpretation: a schedule intersection alone cannot attribute broad, cross-dataset A2/A3/A4 gains or regressions to these low-prevalence data-quality findings; it only quantifies potential exposure.

### A4_v2

- Empty-transcript exposure: 52 uses (1.625% of locked microbatches).
- Train duplicate-cluster exposure: 28 uses (0.875% of locked microbatches).
- Placeholder validation theoretical upper bound: 2 / 9,081 = 0.02202% of rows. The rows are validation-only and have no training-schedule exposure.
- Interpretation: a schedule intersection alone cannot attribute broad, cross-dataset A2/A3/A4 gains or regressions to these low-prevalence data-quality findings; it only quantifies potential exposure.

## Conclusion

No schedule is modified. The full row-level evidence is in `data_quality_schedule_intersections.csv`.
