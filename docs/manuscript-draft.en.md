# PlantMR-GxE: an auditable summary-statistics workflow for plant and crop environment-interaction Mendelian randomization

## Abstract

Plant Mendelian randomization (MR) analyses are increasingly used to connect molecular traits with agronomic phenotypes, but existing workflows often inherit human-oriented data contracts and do not make plant reference assemblies, environmental strata, linkage disequilibrium (LD), or sample overlap explicit. We developed PlantMR 1.1, a local Python toolkit with a stable plant summary-statistics schema, allele harmonization, instrument quality control, signed LD handling, standard MR estimators, environment-stratified analysis, and a narrowly defined covariance-aware environment-interaction estimator. The environment-interaction estimator computes SNP-by-environment ratio estimates and fits a two-parameter generalized least-squares model with a pooled effect and a prespecified environmental slope. It accepts signed environment and SNP-LD correlation matrices and rejects incomplete SNP-by-environment grids. In 500-replicate simulations, the covariance-aware estimator had a null rejection rate of 0.054 and 95% coverage of 0.946; under a true environment slope of 0.25, its mean estimate was 0.2498, bias −0.00018, coverage 0.952, and power 1.00. A directional-pleiotropy scenario showed the intended limitation: the slope remained approximately unbiased, but the pooled intercept was biased by 0.216. We also executed a real Arabidopsis case using AT1G11560 baseline expression, 1001 Genomes local genotypes, and flowering-time phenotypes at 10°C and 16°C. Forty-eight LD-correlated instruments passed the prespecified exposure thresholds. The primary LD-aware analysis estimated an environment slope of −0.0371 (SE 0.1562, P=0.812), with significant residual heterogeneity (Q-test P=8.42×10−9). The case demonstrates a reproducible data contract and diagnostic workflow, not independent causal validation. PlantMR-GxE is positioned as a plant-focused, auditable implementation and comparator workflow, not as the first environment-interaction MR method.

Keywords: Mendelian randomization; plants; crops; genotype-by-environment interaction; eQTL; LD; summary statistics; reproducibility

## Introduction

Mendelian randomization uses genetic associations as instrumental variables to estimate genetically proxied exposure effects on outcomes. Plant applications differ from many human applications because natural accessions and breeding panels can have strong geographic structure, rapid or heterogeneous LD decay, non-standard reference assemblies, tissue- and stage-specific expression, and multiple controlled or field environments. These properties make an apparently simple transfer of a human MR workflow unsafe unless the plant data contract is explicit.

Plant-oriented software already exists. MRBIGR provides a broad population-scale multi-omics and MR workflow for maize. The original maize drought study that motivated this project used a lead-eQTL, two-stage least-squares-style workflow to prioritize genes. More general methods such as MR-GxE and MR-GENIUS use gene-by-covariate interactions for different identification targets, and MR-EILLS integrates heterogeneous GWAS summary datasets under an invariance-based estimand. Therefore, the contribution of PlantMR is not the invention of environment-interaction MR. Instead, PlantMR provides a reproducible plant/crop summary-statistics contract, explicit environment and LD covariance inputs, complete-grid instrument selection, auditable reports, and an executable implementation that can be compared with these existing methods.

We address three engineering and statistical requirements: (i) effects must be harmonized with plant assembly, tissue, stage and environment metadata; (ii) LD and environmental dependence must not be silently replaced by independence; and (iii) environment-specific estimates must be distinguished from a formal environment-interaction estimand. We implement a two-parameter covariance-aware estimator and evaluate it by simulations and an Arabidopsis application case.

## Methods

### Software contract

PlantMR accepts exposure and outcome summary tables with `SNP`, `effect_allele`, `other_allele`, `beta`, `se`, and `pval`. Optional fields include `eaf` and `n`. Plant metadata records species, assembly, trait, tissue, developmental stage, environment, ploidy and LD-panel provenance. The package validates alleles, non-finite values, standard errors, P values and allele frequencies; harmonizes reversed/complemented alleles; flags ambiguous palindromic variants; and records exclusions.

Standard methods include Wald ratio, fixed- and random-effects IVW, MR-Egger, Cochran heterogeneity and leave-one-out diagnostics. `run-stratified` estimates each shared environment separately. These estimates are explicitly not described as a formal G×E causal model.

### Environment-interaction estimand

For SNP `j` and environment `k`, define the ratio estimate

`r_jk = beta_y,jk / beta_x,jk`.

Let `z_k` be a prespecified numeric environmental score. PlantMR-GxE fits

`r_jk = theta_0 + theta_1 z_k + epsilon_jk`.

`theta_0` is the genetically proxied effect at `z=0`, and `theta_1` is the change in the MR effect per unit increase in `z`. The user must center and scale `z` before analysis when a particular reference environment is intended for `theta_0`.

The first-order delta variance is

`v_jk = se_y,jk^2 / beta_x,jk^2 + beta_y,jk^2 se_x,jk^2 / beta_x,jk^4`.

With SNP-major/environment-major row order, optional signed SNP and environment correlation matrices define

`V = D (R_SNP kron R_ENV) D`,

where `D=diag(sqrt(v_jk))`. If a matrix is not supplied, its factor is the identity and the report states that a diagonal approximation was used. The GLS estimate is

`theta_hat = (X' V^-1 X)^-1 X' V^-1 r`,

with `X=[1,z]`. The output records the covariance source, numerical covariance rank, standard errors, P values and residual Q statistic. The implementation requires the same complete environment set for every SNP and retains only instruments that pass exposure P-value, F-statistic and MAF criteria in every environment.

### Identification assumptions and limitations

The usual MR relevance, independence and exclusion-restriction assumptions are required in every environment. Additional assumptions are that the environmental score is prespecified, the linear slope is an adequate approximation over the analyzed environments, the covariance matrices describe summary-estimation dependence, and instruments are not selected using outcomes or fitted slopes.

The method does not remove directional horizontal pleiotropy, infer causal environmental doses, perform colocalization, HEIDI, fine-mapping, MVMR or functional validation, or support polyploid dosage, PAV and SV by silent recoding. Exposure–outcome sample-overlap covariance is not recovered from marginal summary statistics by default; overlapping-sample analyses must be marked as sensitivity analyses unless a suitable covariance model is supplied.

### Simulation benchmark

We simulated 20 instruments across four environments with environmental correlation 0.5, outcome SE 0.04, exposure SE 0.01, and 500 replicates per scenario using a fixed seed (20260918). We compared covariance-aware estimation with a diagonal covariance comparator under: (i) a null environment slope, (ii) a true slope of 0.25, and (iii) a common directional pleiotropic component of 0.04. We reported bias, RMSE, standard error, 95% coverage, rejection rate at 0.05 and residual Q P values. Simulation truth was kept separate from biological data.

### Arabidopsis application data

We used a transparent local re-analysis rather than claiming to reproduce a published mixed-model result. The molecular exposure was AT1G11560 baseline leaf expression from the GSE80744 normalized matrix. Genotypes came from the 1001 Genomes v3.1 imputed binary matrix; a Chr1 region spanning 3,861,124–3,901,085 was extracted, and five whole-genome PCs were computed from a sparse marker subset. REF/ALT labels were mapped from a public 1001 Genomes accession VCF. The outcomes were AraPheno FT10 and FT16 values, with environment scores −3 and +3. Each local association used ordinary least squares with five PCs. Exposure and outcome tables, the LD matrix, source hashes and metadata are included in the repository.

At exposure P≤5×10−8 and F≥10, 48 SNPs passed in both environments. They were strongly correlated; the primary run supplied their signed LD correlation matrix but no environment-error covariance. A sensitivity run supplied the Pearson correlation of FT10 and FT16 across 1,122 shared accessions (r=0.88195) as an explicitly labeled phenotype-correlation proxy, not as known ratio-error covariance. We also ran independent environment-specific IVW without LD correction as a comparator.

## Results

### Software verification

The v1.1.0 package passed 22 automated tests and Python compilation. The ordinary MR, stratified MR and GxE command-line workflows produced deterministic JSON, TSV and Markdown outputs. The GxE tests covered recovery of known intercept and slope, environment/LD covariance input, complete-grid instrument selection and rejection of incomplete grids.

### Simulation results

Under the null, the covariance-aware rejection rate was 0.054 and 95% coverage was 0.946. The diagonal comparator had rejection 0.006 and coverage 0.994, reflecting conservative standard errors in this simulation. Under the causal G×E scenario, the covariance-aware mean slope was 0.24982 with bias −0.00018, RMSE 0.01490, mean SE 0.01575, coverage 0.952 and power 1.00. The diagonal comparator had mean slope 0.24832, bias −0.00168, RMSE 0.01518, mean SE 0.02229, coverage 1.00 and power 1.00.

Under directional pleiotropy, the covariance-aware slope mean was 0.00014 when the true slope was zero, but the intercept mean was 0.71645 for a true intercept of 0.5 (bias +0.21645). This deliberately demonstrates that a stable environment slope is not evidence that the pooled causal effect is protected from horizontal pleiotropy.

### Arabidopsis case

The primary LD-aware, diagonal-environment-covariance run used 48 SNPs and 96 SNP×environment observations. The pooled intercept was 2.3601 (SE 0.4685, P=4.72×10−7). The environment slope was −0.03705 (SE 0.15617, P=0.81249). Residual heterogeneity was significant (Q=192.89, df=60, P=7.33×10−16).

When the phenotype-correlation proxy was supplied as an environment covariance sensitivity, the intercept was 1.8027 (SE 0.6217, P=0.00374) and the slope was −0.08228 (SE 0.06634, P=0.21491); residual Q remained significant (P=2.27×10−15). The independent, LD-unaware stratified IVW comparator produced 6.6001 at 10°C and 8.2379 at 16°C, with significant heterogeneity in both environments. These differences show why the LD and covariance assumptions must be visible in the report.

The Arabidopsis case is an application and data-contract demonstration. It is not an independent causal validation: the expression and flowering datasets share accessions, exposure–outcome covariance was not estimated, local OLS differs from the published mixed model, and residual heterogeneity remains.

## Discussion

PlantMR 1.1 makes three practical contributions. First, it treats species, assembly, tissue, stage, environment, ploidy and LD provenance as analysis metadata rather than informal notes. Second, it implements an explicit linear environment slope with signed LD/environment correlation inputs and complete-grid QC. Third, it produces machine-readable audit outputs that expose weak instruments, missing environments, covariance approximations and heterogeneity.

The simulation benchmark supports implementation-level calibration under the specified model, but it does not establish robustness to all plant-specific confounding. The directional-pleiotropy scenario shows a central limitation: the interaction slope can appear stable while the pooled intercept is biased. The Arabidopsis case further shows that strong local LD can produce extreme heterogeneity under an independence-based stratified IVW workflow.

A full biological application requires complete beta/SE/EAF summary statistics, a justified sample-overlap covariance model, population-appropriate LD, independent environments or populations, colocalization/HEIDI or fine-mapping, and functional evidence. In the maize drought study examined during development, the public supplementary tables support candidate-list auditing but do not provide a complete beta/SE summary-statistics contract; therefore the maize data are not presented as a new causal result here.

## Availability

Source repository: `/home/user/zhangzhishuai/myhermes/plant_mr`.

Key outputs:

- `src/plant_mr/gxe.py`
- `docs/methods/environment-aware-mr.md`
- `scripts/run_gxe_simulation.py`
- `results/benchmarks/gxe_simulation/`
- `docs/figures/gxe_simulation.png`
- `docs/figures/gxe_simulation.pdf`
- `docs/real-case-arabidopsis.zh-CN.md`

## References

1. Liu et al. Mapping regulatory variants controlling gene expression in drought response and tolerance in maize. Genome Biology (2020). https://doi.org/10.1186/s13059-020-02069-1
2. MRBIGR. A versatile toolbox for genetic regulation inference from population-scale multi-omics data. Plant Communications (2024). https://doi.org/10.1016/j.xplc.2024.101197
3. Spiller et al. Detecting and correcting for bias in MR analyses using gene-by-environment interactions. International Journal of Epidemiology (2019). https://doi.org/10.1093/ije/dyz195
4. Spiller et al. Interaction-based Mendelian randomization with measured and unmeasured gene-by-covariate interactions. PLOS ONE (2022). https://doi.org/10.1371/journal.pone.0271933
5. MR-EILLS. MR-EILLS: an invariance-based Mendelian randomization method integrating multiple heterogeneous GWAS summary datasets. Nature Communications (2025). https://www.nature.com/articles/s41467-025-62823-6
6. Feng et al. Dual-trait genomic analysis in highly stratified Arabidopsis thaliana populations using genome-wide association summary statistics. Heredity (2024). https://doi.org/10.1038/s41437-024-00688-z
7. The 1001 Genomes Consortium. 1,135 Genomes Reveal the Global Pattern of Polymorphism in Arabidopsis thaliana. Cell (2016). https://doi.org/10.1016/j.cell.2016.05.063
8. STROBE-MR. Strengthening the reporting of observational studies in epidemiology using Mendelian randomization. JAMA (2021). https://pubmed.ncbi.nlm.nih.gov/34698778/
