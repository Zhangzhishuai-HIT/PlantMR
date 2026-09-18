# PlantMR GxE-IVW report

## Estimand

The intercept is the pooled MR effect at environment_value=0; the slope is the change in MR effect per unit environment_value.

## Result

| Parameter | Estimate | SE | P value |
|---|---:|---:|---:|
| pooled intercept | 1.8027415 | 0.62173894 | 0.0037374023 |
| environment slope | -0.082277083 | 0.066343555 | 0.21491366 |

## Audit

- excluded_f: 106
- excluded_incomplete_qc: 121
- excluded_maf: 0
- excluded_pval: 121
- input_rows: 338
- input_snps: 169
- selected: 48
- selected_rows: 96

## Covariance

- source: environment_and_ld_correlation
- rank: 62

## Warnings

- GxE-IVW is a summary-statistics GLS model under supplied covariance assumptions.
- MR evidence does not replace colocalization, functional validation, or gene editing.
