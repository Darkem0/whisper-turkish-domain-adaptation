# Evaluation gate semantics repair

| Condition | Status | Gate treatment |
| --- | --- | --- |
| Measured threshold breach | `REAL_METRIC_FAILURE` | hard failure |
| Required metric absent | `NOT_EVALUATED` | incomplete evidence; not a measured model failure |
| Fewer than required seeds | `REPRODUCIBILITY_NOT_YET_ESTABLISHED` | no reproducibility pass; not `FAILED_REPRODUCIBILITY` |
| Execution/integrity error | `TECHNICAL_FAILURE` | block evaluation |

A single-seed candidate may remain ineligible when another hard gate fails, as A3 does here.
