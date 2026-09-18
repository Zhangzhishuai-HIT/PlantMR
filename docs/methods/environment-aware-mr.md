# Environment-aware summary-statistics MR

## Positioning

PlantMR 1.1 adds a plant/crop-oriented implementation of a covariance-aware environment-interaction MR estimand. It is not the first environment-interaction MR idea: MR-GxE and related interaction-MR methods already exist, and MR-EILLS is a recent heterogeneous-summary-data comparator. The contribution claimed here is narrower and testable: an explicit plant summary-statistics contract, complete SNP-by-environment instrument selection, signed environment and LD correlation inputs, and auditable local reports.

## Input contract

The long-format harmonized table contains one row per SNP and environment:

- `SNP`;
- `environment`;
- `environment_value`, a prespecified numeric environmental score;
- `exposure_beta`, `exposure_se`;
- `outcome_beta`, `outcome_se`;
- `exposure_pval`, `eaf` for instrument QC.

The CLI accepts exposure and outcome tables in long format. Effects are harmonized separately within each environment. An instrument is retained only if it passes the exposure P-value, F-statistic and MAF rules in every environment. A complete grid is required because changing the instrument set across environments would confound the environment slope with instrument composition.

Optional matrices:

- `environment_correlation`: signed correlation of the ratio-estimation errors across environments;
- `ld_correlation`: signed LD correlation among SNP instruments.

Both matrices must be symmetric, have unit diagonal, match the exact labels in the input, and be positive semidefinite. If omitted, the model uses a diagonal first-order ratio covariance and writes a warning. No human LD panel is inferred or substituted.

## Estimand

For SNP `j` and environment `k`, define the ratio estimate

`r_jk = beta_y,jk / beta_x,jk`.

The primary linear environment model is

`r_jk = theta_0 + theta_1 z_k + epsilon_jk`,

where `z_k` is the prespecified `environment_value`.

- `theta_0` is the pooled MR effect at `z=0`;
- `theta_1` is the change in MR effect for a one-unit increase in `z`.

The environmental score must be centered and scaled before analysis when the user wants `theta_0` to represent a meaningful reference environment. The tool does not choose or transform it automatically.

## Variance and GLS

The diagonal first-order delta variance is

`v_jk = se_y,jk^2 / beta_x,jk^2 + beta_y,jk^2 se_x,jk^2 / beta_x,jk^4`.

Let `D=diag(sqrt(v_jk))`. With SNP-major and environment-major row order, the covariance used by the implementation is

`V = D (R_SNP kron R_ENV) D`.

If either matrix is omitted, its factor is an identity matrix. The estimator is

`theta_hat = (X' V^-1 X)^-1 X' V^-1 r`,

with `X=[1,z]`. The reported standard errors come from `(X'V^-1X)^-1`; the report also records the covariance source and numerical rank. Cochran-style residual heterogeneity is `Q=(r-X theta)'V^-1(r-X theta)` with `rank(V)-rank(X)` degrees of freedom when the covariance is singular (and the usual `n-2` value when it is full rank).

The current implementation uses a first-order summary-statistics approximation. It does not estimate cross-environment exposure–outcome covariance from individual-level data. If the exposure and outcome associations are estimated in overlapping samples, the user must provide an appropriate covariance model or treat the result as sensitivity analysis rather than exact inference.

## Identification assumptions

The usual MR relevance, independence and exclusion assumptions are required for every environment. In addition:

1. The environmental score is fixed before inspecting the outcome results.
2. The same latent causal estimand is adequately represented by a linear function of `z` over the analyzed environments.
3. The supplied environment and LD correlation matrices describe the sampling/error dependence of the summary estimates.
4. Missing environments are not selectively driving the slope; hence the complete-grid requirement.
5. The instrument set is not selected using outcome associations or the estimated slope.

These assumptions are stronger than simply running independent environment-specific MR analyses.

## What the model does not solve

- Directional horizontal pleiotropy is not automatically removed. The simulation benchmark shows that a common pleiotropic component can bias the pooled intercept while leaving the interaction slope approximately unbiased.
- It does not perform colocalization, HEIDI, fine-mapping, MVMR, MR-PRESSO, or functional validation.
- It does not convert treatment labels into causal environmental doses.
- It does not support polyploid dosage, PAV or SV instruments by silently recoding them as SNPs.
- The model is not a replacement for MR-GxE, MR-GENIUS or MR-EILLS; those methods have different estimands and assumptions and must be compared as separate adapters.

## Simulation gate

The checked benchmark uses 20 instruments, 4 environments, environment correlation 0.5, 500 replicates per scenario and a fixed seed. It includes a null slope, a true slope of 0.25, and directional pleiotropy. It compares the covariance-aware estimator with a diagonal covariance comparator. Results are under `results/benchmarks/gxe_simulation/`; the figure is `docs/figures/gxe_simulation.png` and `.pdf`.

Simulation results are method verification only. They are not evidence that any maize gene or environmental response is causal.
