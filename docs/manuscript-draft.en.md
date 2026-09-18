# PlantMR: an auditable summary-statistics toolkit for plant and crop Mendelian randomization with environment-aware effect heterogeneity

## Abstract

Plant Mendelian randomization (MR) analyses are increasingly used to connect molecular traits with agronomic phenotypes, but plant reference assemblies, environmental strata, linkage disequilibrium (LD) and sample overlap are often left implicit. We developed PlantMR 1.1, an open-source local toolkit with a plant summary-statistics schema, allele harmonization, instrument quality control, signed LD handling, standard MR estimators and a narrowly defined environment-slope analysis. The environment-slope estimator models SNP-by-environment ratio estimates by generalized least squares, accepts signed environment and SNP-LD correlation matrices, requires a complete SNP-by-environment grid and reports covariance rank. In 500-replicate simulations with environmental correlation, the covariance-aware estimator had a null rejection rate of 0.054 and 95% coverage of 0.946; under a true slope of 0.25, its mean estimate was 0.2498, bias −0.00018, coverage 0.952 and power 1.00. In an additional LD stress test (AR(1) LD correlation ρ=0.6), correct covariance modeling gave a null rejection rate of 0.044 and coverage of 0.956, whereas an independence approximation gave 0.126 and 0.874. Directional pleiotropy remained a limitation: the slope was approximately unbiased, but the pooled intercept was biased by 0.216. We executed an Arabidopsis data-contract case using AT1G11560 baseline expression, 1001 Genomes local genotypes and flowering-time phenotypes at 10°C and 16°C. Forty-eight LD-correlated instruments passed prespecified exposure thresholds. The primary LD-aware analysis estimated a slope of −0.0371 (SE 0.1562, P=0.812), with residual heterogeneity (Q-test P=7.33×10−16). This case demonstrates reproducibility and diagnostics, not independent causal validation. PlantMR is positioned as a plant-focused implementation and audit workflow, not as the first environment-interaction MR method.

Keywords: Mendelian randomization; plants; crops; genotype-by-environment interaction; eQTL; LD; summary statistics; reproducibility

## Introduction

Mendelian randomization uses genetic associations as instrumental variables to estimate genetically proxied exposure effects on outcomes. The relevance, exchangeability and exclusion-restriction assumptions remain the basis for interpretation, but their practical implementation depends on the study population and data-generating design. Plant applications differ from many human applications because natural accessions and breeding panels can have strong geographic structure, rapid or heterogeneous LD decay, non-standard reference assemblies, tissue- and stage-specific expression, and multiple controlled or field environments. These properties make an apparently simple transfer of a human MR workflow unsafe unless the plant data contract is explicit.

Plant-oriented software already exists. MRBIGR provides a broad population-scale multi-omics and MR workflow for maize, including genotype/phenotype processing, GWAS, MR, network and enrichment modules.[1] The original maize drought study that motivated this project used a lead-eQTL, two-stage-least-squares-style workflow to prioritize genes.[2] More general interaction-based methods have different targets: MR-GxE uses gene-by-covariate interactions to detect or correct pleiotropic bias under a constant-pleiotropy assumption,[3] whereas MR-GENIUS does not require an observed interaction but makes stronger global assumptions.[4] MR-EILLS targets an invariant causal effect across heterogeneous GWAS datasets and compares against multiple MR and meta-analytic methods.[5] These methods are not interchangeable with the environment-slope estimand implemented here. Therefore, the contribution of PlantMR is not the invention of environment-interaction MR. Instead, PlantMR provides a reproducible plant/crop summary-statistics contract, explicit environment and LD covariance inputs, complete-grid instrument selection, auditable reports and an executable implementation that can be compared with these existing methods.

We address three engineering and statistical requirements: (i) effects must be harmonized with plant assembly, tissue, stage and environment metadata; (ii) LD and environmental dependence must not be silently replaced by independence; and (iii) environment-specific estimates must be distinguished from a formal environment-effect-heterogeneity estimand. We implement a two-parameter covariance-aware estimator and evaluate it using analytical recovery tests, null/causal/pleiotropy simulations, an LD-misspecification stress test and an Arabidopsis application case.

## Methods

### Software contract

PlantMR accepts exposure and outcome summary tables with `SNP`, `effect_allele`, `other_allele`, `beta`, `se`, and `pval`. Optional fields include `eaf` and `n`. Plant metadata records species, assembly, trait, tissue, developmental stage, environment, ploidy and LD-panel provenance. The package validates alleles, non-finite values, standard errors, P values and allele frequencies; harmonizes reversed/complemented alleles; flags ambiguous palindromic variants; and records exclusions.

Standard methods include Wald ratio, fixed- and random-effects IVW, MR-Egger, Cochran heterogeneity and leave-one-out diagnostics. `run-stratified` estimates each shared environment separately. These estimates are explicitly not described as a formal G×E causal model.

### Environment-effect-heterogeneity estimand

For SNP `j` and environment `k`, define the ratio estimate

`r_jk = beta_y,jk / beta_x,jk`.

Let `z_k` be a prespecified numeric environmental score. PlantMR-GxE fits

`r_jk = theta_0 + theta_1 z_k + epsilon_jk`.

`theta_0` is the genetically proxied effect at `z=0`, and `theta_1` is the change in the MR effect per unit increase in `z`. The user must center and scale `z` before analysis when a particular reference environment is intended for `theta_0`. This is an effect-heterogeneity model: its intercept is not the MR-GxE pleiotropy intercept and is not interpreted as a correction for horizontal pleiotropy. In particular, the estimator does not use variation in first-stage exposure effects to identify a no-relevance subgroup and should not be reported as MR-GxE or MR-GENIUS.

The first-order delta variance is

`v_jk = se_y,jk^2 / beta_x,jk^2 + beta_y,jk^2 se_x,jk^2 / beta_x,jk^4`.

With SNP-major/environment-major row order, optional signed SNP and environment correlation matrices define

`V = D (R_SNP kron R_ENV) D`,

where `D=diag(sqrt(v_jk))`. If a matrix is not supplied, its factor is the identity and the report states that a diagonal approximation was used. The GLS estimate is

`theta_hat = (X' V^-1 X)^-1 X' V^-1 r`,

With `X=[1,z]`. The output records the covariance source, numerical covariance rank, standard errors, P values and residual Q statistic. The implementation requires the same complete environment set for every SNP and retains only instruments that pass exposure P-value, F-statistic and MAF criteria in every environment. If the covariance matrix is rank-deficient, heterogeneity degrees of freedom are `rank(V)-rank(X)`, not the raw number of rows minus two.

### Identification assumptions and limitations

The usual MR relevance, independence and exclusion-restriction assumptions are required in every environment.[8] Additional assumptions are that the environmental score is prespecified, the linear slope is an adequate approximation over the analyzed environments, the covariance matrices describe summary-estimation dependence, and instruments are not selected using outcomes or fitted slopes.

The method does not remove directional horizontal pleiotropy, infer causal environmental doses, perform colocalization, HEIDI, fine-mapping, MVMR or functional validation, or support polyploid dosage, PAV and SV by silent recoding. Exposure–outcome sample-overlap covariance is not recovered from marginal summary statistics by default; overlapping-sample analyses must be marked as sensitivity analyses unless a suitable covariance model is supplied.

### Simulation benchmark

We simulated 20 instruments across four environments with environmental correlation 0.5, outcome SE 0.04, exposure SE 0.01, and 500 replicates per scenario using a fixed seed (20260918). We compared covariance-aware estimation with a diagonal covariance comparator under: (i) a null environment slope, (ii) a true slope of 0.25, and (iii) a common directional pleiotropic component of 0.04. We reported bias, RMSE, standard error, 95% coverage, rejection rate at 0.05 and residual Q P values. In a separate 500-replicate LD stress benchmark (seed 20260919), SNP errors followed an AR(1) LD correlation with rho=0.6 in addition to environmental correlation; the correctly specified estimator was compared with an independence approximation. Simulation truth was kept separate from biological data.

### Arabidopsis application data

We used a transparent local re-analysis rather than claiming to reproduce a published mixed-model result. The molecular exposure was AT1G11560 baseline leaf expression from the GSE80744 normalized matrix, an Arabidopsis transcriptome resource used in prior population-genetic analyses.[6] Genotypes came from the 1001 Genomes v3.1 imputed binary matrix,[7] a Chr1 region spanning 3,861,124–3,901,085 was extracted, and five whole-genome PCs were computed from a sparse marker subset. REF/ALT labels were mapped from a public 1001 Genomes accession VCF. The outcomes were AraPheno FT10 and FT16 values, with environment scores −3 and +3. Each local association used ordinary least squares with five PCs. Exposure and outcome tables, the LD matrix, source hashes and metadata are included in the repository.

At exposure P≤5×10−8 and F≥10, 48 SNPs passed in both environments. They were strongly correlated; the primary run supplied their signed LD correlation matrix but no environment-error covariance. A sensitivity run supplied the Pearson correlation of FT10 and FT16 across 1,122 shared accessions (r=0.88195) as an explicitly labeled phenotype-correlation proxy, not as known ratio-error covariance. We also ran independent environment-specific IVW without LD correction as a comparator.

## Results

### Software verification

The v1.1.0 package passed 23 automated tests and Python compilation. The ordinary MR, stratified MR and GxE command-line workflows produced deterministic JSON, TSV and Markdown outputs. The GxE tests covered recovery of known intercept and slope, environment/LD covariance input, complete-grid instrument selection, rejection of incomplete grids and rank-aware heterogeneity degrees of freedom. On the verification host, the installed CLI required approximately 9.8 s for input validation, 9.8 s for the synthetic GxE demo and 9.9 s for the Arabidopsis case; peak resident memory was 123–131 MB.

### Simulation results

Under the null, the covariance-aware rejection rate was 0.054 and 95% coverage was 0.946. The diagonal comparator had rejection 0.006 and coverage 0.994, reflecting conservative standard errors in this simulation. Under the causal G×E scenario, the covariance-aware mean slope was 0.24982 with bias −0.00018, RMSE 0.01490, mean SE 0.01575, coverage 0.952 and power 1.00. The diagonal comparator had mean slope 0.24832, bias −0.00168, RMSE 0.01518, mean SE 0.02229, coverage 1.00 and power 1.00.

Under directional pleiotropy, the covariance-aware slope mean was 0.00014 when the true slope was zero, but the intercept mean was 0.71645 for a true intercept of 0.5 (bias +0.21645). This deliberately demonstrates that a stable environment slope is not evidence that the pooled causal effect is protected from horizontal pleiotropy.

In the LD stress benchmark, correct covariance specification produced a null rejection rate of 0.044 and 95% coverage of 0.956. The independence approximation produced a null rejection rate of 0.126 and coverage of 0.874. Under a true slope of 0.25, correct specification gave bias 0.00136 and coverage 0.970, whereas the independence approximation gave bias 0.00170 and coverage 0.880. Thus, the LD-aware covariance is not a cosmetic option: under this deliberately controlled setting, ignoring it led to anti-conservative inference.

### Arabidopsis case

The primary LD-aware, diagonal-environment-covariance run used 48 SNPs and 96 SNP×environment observations. The pooled intercept was 2.3601 (SE 0.4685, P=4.72×10−7). The environment slope was −0.03705 (SE 0.15617, P=0.81249). Residual heterogeneity was significant (Q=192.89, df=60, P=7.33×10−16).

When the phenotype-correlation proxy was supplied as an environment covariance sensitivity, the intercept was 1.8027 (SE 0.6217, P=0.00374) and the slope was −0.08228 (SE 0.06634, P=0.21491); residual Q remained significant (P=2.27×10−15). The independent, LD-unaware stratified IVW comparator produced 6.6001 at 10°C and 8.2379 at 16°C, with significant heterogeneity in both environments. These differences show why the LD and covariance assumptions must be visible in the report.

The Arabidopsis case is an application and data-contract demonstration. It is not an independent causal validation: the expression and flowering datasets share accessions, exposure–outcome covariance was not estimated, local OLS differs from the published mixed model, and residual heterogeneity remains.

## Discussion

PlantMR 1.1 makes three practical contributions. First, it treats species, assembly, tissue, stage, environment, ploidy and LD provenance as analysis metadata rather than informal notes. Second, it implements an explicit linear environment slope with signed LD/environment correlation inputs and complete-grid QC. Third, it produces machine-readable audit outputs that expose weak instruments, missing environments, covariance approximations and heterogeneity.

The simulation benchmark supports implementation-level calibration under the specified model, but it does not establish robustness to all plant-specific confounding. The directional-pleiotropy scenario shows a central limitation: the interaction slope can appear stable while the pooled intercept is biased. The Arabidopsis case further shows that strong local LD can produce extreme heterogeneity under an independence-based stratified IVW workflow.

A full biological application requires complete beta/SE/EAF summary statistics, a justified sample-overlap covariance model, population-appropriate LD, independent environments or populations, colocalization/HEIDI or fine-mapping, and functional evidence. In the maize drought study examined during development, the public supplementary tables support candidate-list auditing but do not provide a complete beta/SE summary-statistics contract; therefore the maize data are not presented as a new causal result here. The appropriate next use of PlantMR is as a transparent analysis layer after those upstream contracts have been met, not as a substitute for them.

The software evidence should also be interpreted at the correct level. The current benchmarks validate implementation behavior under stated data-generating models; they do not establish universal robustness. The real-data case tests ingestion, harmonization, LD accounting and reporting, but its local association model and sample overlap prevent it from serving as an independent causal validation set. These boundaries are deliberate and should remain visible in the title, abstract, results and data-availability statements.

## Code, data and reproducibility statements

Code is released under the MIT License in the PlantMR v1.1.0 snapshot. Nature software guidance emphasizes usable source code, installation documentation, a runnable demo, typical runtime, an open-source license and a public repository/DOI for code central to the manuscript.[9][10] Before external submission, the local snapshot should be mirrored to a public versioned repository and archived with a DOI; the present working copy has no configured remote repository. The release includes installation instructions, synthetic input/output examples, unit tests, source code, simulation scripts, benchmark outputs and a reproducibility tag.

The exact local source tree used for this draft is `/home/user/zhangzhishuai/myhermes/plant_mr`; the release tag is `v1.1.0`. The current verification host used Python 3.10, NumPy, pandas, SciPy and statsmodels. The input tables, public-data URLs, source hashes and access restrictions are recorded in `docs/real-case-arabidopsis.zh-CN.md` and the data subdirectories. The large 1001 Genomes provider archive and HDF5 matrix are not redistributed; only the derived local region subset and provider checksums are included.

The synthetic and Arabidopsis outputs are intended to reproduce the software and reporting behavior. The Arabidopsis exposure and outcome data share accessions, and the environment-correlation sensitivity uses a phenotype-correlation proxy rather than a known ratio-error covariance; these facts are part of the result, not hidden preprocessing.

Key outputs:

- `src/plant_mr/gxe.py`
- `docs/methods/environment-aware-mr.md`
- `scripts/run_gxe_simulation.py`
- `results/benchmarks/gxe_simulation/`
- `docs/figures/gxe_simulation.png`
- `docs/figures/gxe_simulation.pdf`
- `docs/real-case-arabidopsis.zh-CN.md`
- `results/benchmarks/gxe_ld_stress/`
- `results/benchmarks/runtime.tsv`

## References

1. Xu, F. et al. MRBIGR: A versatile toolbox for genetic regulation inference from population-scale multi-omics data. Plant Commun. (2024). https://doi.org/10.1016/j.xplc.2024.101197
2. Liu, S. et al. Mapping regulatory variants controlling gene expression in drought response and tolerance in maize. Genome Biol. 21, 163 (2020). https://doi.org/10.1186/s13059-020-02069-1
3. Spiller, W. et al. Detecting and correcting for bias in Mendelian randomization analyses using gene-by-environment interactions. Int. J. Epidemiol. (2018). https://doi.org/10.1093/ije/dyy204
4. Spiller, W. et al. Interaction-based Mendelian randomization with measured and unmeasured gene-by-covariate interactions. PLoS ONE 17, e0271933 (2022). https://doi.org/10.1371/journal.pone.0271933
5. MR-EILLS. MR-EILLS: an invariance-based Mendelian randomization method integrating multiple heterogeneous GWAS summary datasets. Nature Communications (2025). https://www.nature.com/articles/s41467-025-62823-6
6. Feng et al. Dual-trait genomic analysis in highly stratified Arabidopsis thaliana populations using genome-wide association summary statistics. Heredity (2024). https://doi.org/10.1038/s41437-024-00688-z
7. The 1001 Genomes Consortium. 1,135 Genomes Reveal the Global Pattern of Polymorphism in Arabidopsis thaliana. Cell (2016). https://doi.org/10.1016/j.cell.2016.05.063
8. Skrivankova, W. et al. Strengthening the reporting of observational studies in epidemiology using Mendelian randomization (STROBE-MR). JAMA 326, 1614–1621 (2021). https://pubmed.ncbi.nlm.nih.gov/34698778/
9. Nature Portfolio. Guidelines for authors submitting code and software. https://media.nature.com/full/nature-cms/documents/GuidelinesCodePublication.pdf
10. Nature Portfolio. Guidance on reproducibility for papers using computational tools. https://www.nature.com/documents/Computational_tools_reporting_guidelines.pdf
