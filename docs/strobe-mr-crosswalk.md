# STROBE-MR crosswalk for PlantMR manuscript

This is a pre-submission crosswalk, not a claim that the manuscript has passed journal review.

| STROBE-MR area | Manuscript location | Current status / required wording |
|---|---|---|
| Title identifies MR design | Title | State “summary-statistics MR” and “environment-aware effect heterogeneity”; do not call it causal discovery software. |
| Abstract background/objective | Abstract | States plant data-contract problem and bounded estimand. |
| Abstract methods | Abstract | States GLS ratio model, covariance inputs and complete-grid rule. |
| Abstract results | Abstract | Reports simulation calibration, LD stress, and real-case estimates with limitations. |
| Abstract conclusions | Abstract | Claims reproducibility/diagnostics, not independent causal validation. |
| Scientific background | Introduction | Explain plant population structure, LD, environment and existing MR-GxE/MR-EILLS/MRBIGR. |
| Causal diagram / assumptions | Methods: Identification assumptions | State relevance, exchangeability, exclusion restriction, linear environment score, covariance and selection assumptions. Add a DAG if a biological application is retained. |
| Exposure definition | Software contract; Arabidopsis data | State baseline AT1G11560 expression, log1p transformation, local OLS and environment treatment. |
| Outcome definition | Arabidopsis data | State FT10/FT16, units, AraPheno IDs and centered environment values. |
| Genetic instrument source | Arabidopsis data; data audit | State 1001 Genomes v3.1, region, allele mapping and PCs. |
| Sample size and selection | Arabidopsis data; source data | Report 665 expression accessions, 1,003/970 outcome rows after local matching, 48 retained instruments, and missingness rules. |
| Sample overlap | Identification assumptions; Discussion | State overlap explicitly and do not call the case independent validation. |
| Population structure | Arabidopsis data | State PC1–PC5 adjustment and that local OLS is not the published LMM. |
| Instrument strength | Instrument selection | Report P≤5×10^-8, F≥10, MAF≥0.05 and complete-grid selection. |
| LD handling | Environment-aware method; results | Report signed LD matrix, covariance rank and rank-aware Q degrees of freedom. |
| Main analysis | Methods and Results | Primary analysis is LD-aware with diagonal environment-error covariance; sensitivity uses phenotype-correlation proxy. |
| Sensitivity analyses | Results | Independent stratified IVW, LD-misspecification simulation, environment-correlation proxy. |
| Multiple testing | Scope limitation | Current case is a prespecified one-gene demonstration, not genome-wide discovery. A genome-wide release must add FDR/Bonferroni and gene-level aggregation. |
| Pleiotropy | Simulation and limitations | Directional pleiotropy biases the pooled intercept; PlantMR does not remove it. |
| Heterogeneity | Results | Report Q, rank-aware degrees of freedom and interpretation. |
| Negative/null results | Results | Report non-significant environment slope and significant residual heterogeneity; do not select a favorable method. |
| Interpretation | Discussion | Use “application/data-contract demonstration” and “MR-supported relationship” only. |
| Generalisability | Discussion | State limitations of one species, one local region and local OLS. |
| Data/code availability | Code/data statements | Before submission, add public repository URL and DOI; current local tree has no remote. |
| Funding/conflicts | Submission metadata | Add author-supplied funding, author contributions and competing-interest statements before submission. |
