# PlantMR GxE-IVW report

## Estimand

The intercept is the pooled MR effect at environment_value=0; the slope is the change in MR effect per unit environment_value.

## Result

| Parameter | Estimate | SE | P value |
|---|---:|---:|---:|
| pooled intercept | 2.360075 | 0.4685172 | 4.7207409e-07 |
| environment slope | -0.037046365 | 0.1561724 | 0.81249035 |

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

- source: ld_correlation
- rank: 62

## Warnings

- GxE-IVW is a summary-statistics GLS model under supplied covariance assumptions.
- MR evidence does not replace colocalization, functional validation, or gene editing.
- No environment correlation was supplied; diagonal ratio covariance was used.
