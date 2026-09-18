# Estimands and methods

## Inputs

For each SNP, PlantMR uses an exposure association `(beta_x, se_x)` and an outcome association `(beta_y, se_y)` after allele harmonization. The primary estimand is the genetically instrumented effect of the exposure on the outcome under the instrumental-variable assumptions.

## Wald ratio

For one instrument:

`beta_hat = beta_y / beta_x`

The standard error uses first-order delta propagation of both exposure and outcome uncertainty:

`Var(beta_hat) = se_y^2 / beta_x^2 + beta_y^2 se_x^2 / beta_x^4`

## IVW

For multiple instruments, PlantMR forms ratio estimates and inverse-variance weights using the same first-order variance. Fixed-effects IVW uses a common effect. Random-effects IVW estimates a non-negative DerSimonian–Laird `tau2` from Cochran's Q and inflates the variance when instruments are heterogeneous.

## MR-Egger

MR-Egger fits a weighted regression of SNP–outcome effects on SNP–exposure effects with an intercept. The slope is the reported exposure effect and the intercept is a directional-pleiotropy diagnostic. At least three instruments are required by the implementation.

## Leave-one-out

Each instrument is removed once and fixed-effects IVW is recomputed. This identifies results dominated by a single instrument; it does not prove the remaining instruments are valid.

## Environment stratification

`run-stratified` repeats the complete analysis independently for each shared `environment` value. It estimates condition-specific effects and reports them side by side. This is a stratified analysis, not a full hierarchical G×E causal model; the report states this limitation explicitly.

## LD clumping

If a square signed LD correlation matrix is supplied, instruments are sorted by exposure P value and greedily retained when their squared correlation with all retained variants is at most the configured threshold. The report records how many variants were removed. Without a matrix, the tool does not infer independence from SNP names or coordinates.
