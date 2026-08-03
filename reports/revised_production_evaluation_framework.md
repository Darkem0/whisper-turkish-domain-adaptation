# Revised production evaluation framework

This is a prospective framework; it does not rewrite A2/A3 terminal scientific records or promote A4.

## Dataset roles

- **Production-relevant:** MediaSpeech Phone, MediaSpeech G.711 and the predeclared MediaSpeech robustness proxy. Any natural/spontaneous telephone-like subset must be frozen and provenance-checked before it is added.
- **General-domain scientific monitoring:** CV Scripted, FLEURS, clean read speech and other company-external sets. Regressions are reported with paired CIs and investigated, but do not alone trigger automatic production rejection.
- **Critical-behavior guardrails:** empty output, prediction-derived repetition/length outliers, malformed/non-Turkish text, number/name errors and catastrophic paired regressions. Semantic hallucination, real call-flow safety and business terminology require a company-domain test set and manual review; they are `MISSING`, not inferred.

## Reclassification without changing terminal records

| Experiment | Existing scientific terminal | Additional operational class |
| --- | --- | --- |
| A2 | unchanged prior non-promotion record | insufficient_company_domain_evidence |
| A3 | A3_V2_NO_PROMOTABLE_CHECKPOINT | research_only; measured CV Scripted failure remains recorded |
| A4 | A4_V2_FROZEN_EVALUATION_COMPLETED, diagnostic-only | insufficient_company_domain_evidence |

No result above establishes production readiness without an independently frozen company-domain test set and critical-behavior audit.

## Available A4 prediction-derived guardrail diagnostics

{
  "step-050": {
    "samples": 15367,
    "empty_output": 0,
    "extreme_length_ratio": 40,
    "repeated_adjacent_bigram": 50,
    "malformed_unicode": 0
  },
  "step-100": {
    "samples": 15367,
    "empty_output": 0,
    "extreme_length_ratio": 35,
    "repeated_adjacent_bigram": 47,
    "malformed_unicode": 0
  },
  "step-150": {
    "samples": 15367,
    "empty_output": 1,
    "extreme_length_ratio": 40,
    "repeated_adjacent_bigram": 53,
    "malformed_unicode": 0
  },
  "step-200": {
    "samples": 15367,
    "empty_output": 1,
    "extreme_length_ratio": 37,
    "repeated_adjacent_bigram": 51,
    "malformed_unicode": 0
  }
}

These checks cannot establish semantic hallucination, number/name correctness in a business workflow, or company-call operational safety; those remain `MISSING` pending a frozen company-domain set and manual review.
