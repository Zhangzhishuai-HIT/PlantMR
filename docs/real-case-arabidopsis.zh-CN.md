# Arabidopsis real-data case audit

## Case definition

- Species: *Arabidopsis thaliana*.
- Molecular exposure: baseline leaf expression of `AT1G11560` from GSE80744 normalized counts, log1p transformed.
- Outcome: flowering time in 10°C (`FT10`) and 16°C (`FT16`) from AraPheno.
- Environment score: `10C=-3`, `16C=+3`; the score is centered at 13°C for the intercept interpretation.
- Genotype: 1001 Genomes v3.1 imputed binary SNP matrix, Chr1:3,861,124–3,901,085, with 3,352 regional SNPs and 1,135 accessions.
- Local association model: ordinary least squares of the molecular/phenotype value on dosage plus PC1–PC5. This is an auditable local re-analysis, not the published LMM/SMR analysis.

## Public source files

- FT10 values: `https://arapheno.1001genomes.org/rest/phenotype/261/values.csv`
  - SHA-256: `e2b4203dd57973e5bb05a42acbe88ed2ece6fa778a8cba7770640ed43527eddf`.
- FT16 values: `https://arapheno.1001genomes.org/rest/phenotype/262/values.csv`
  - SHA-256: `472d330c9466094306e327a6227bb29823731fbdf3e1674353088dec69343eba`.
- GSE80744 series metadata: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE80744`
- GSE80744 normalized expression matrix:
  `https://ftp.ncbi.nlm.nih.gov/geo/series/GSE80nnn/GSE80744/suppl/GSE80744_ath1001_tx_norm_2016-04-21-UQ_gNorm_normCounts_k4.tsv.gz`
  - SHA-256: `36f4a904c577550eb156ae6cd3386e7f6e8e589fd752288e5f1c11d0312c12e8`.
- GSE54680 series metadata: `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE54680`
- 1001 Genomes matrix source tarball:
  `https://1001genomes.org/data/GMI-MPI/releases/v3.1/SNP_matrix_imputed_hdf5/1001_SNP_MATRIX.tar.gz`
  - SHA-256: `015fec67d8de2048f8a46d7f3abac848ecb1e002340cbdc98eccaae5fc69ca0a`.
  - Source HDF5 MD5 from the provider README: `6857bf13f35d3e36d555958ef33d7b77`.
- Allele mapping VCF for accession 991:
  `https://1001genomes.org/data/GMI-MPI/releases/v3.1/intersection_snp_short_indel_vcf/intersection_991.vcf.gz`
  - SHA-256: `ce38bc02de19e453a4e6846440940578b02774a091e9dbed7fce8c7412f5ccc7`.

## Generated inputs

- `data/real/arabidopsis_baseline_AT1G11560/exposure.tsv`
- `data/real/arabidopsis_baseline_AT1G11560/outcome.tsv`
- `data/real/arabidopsis_baseline_AT1G11560/metadata.json`
- `data/real/arabidopsis_baseline_AT1G11560/ld_correlation.tsv`
- `data/real/arabidopsis_baseline_AT1G11560/environment_correlation_phenotype_proxy.tsv`
- `data/real/arabidopsis_baseline_AT1G11560/instrument_selection.json`

The input table contains 172 rows per environment before harmonization, representing 172 complete-grid SNPs. Standard QC at exposure P≤5×10^-8 and F≥10 retains 48 SNPs in both environments. The retained SNPs are highly correlated and are therefore passed with a signed LD correlation matrix rather than treated as independent.

## Executed analyses

### Primary covariance-limited run

Command output directory: `results/real/arabidopsis_baseline_AT1G11560_diag/`.

- 48 SNPs; 96 SNP×environment observations;
- LD covariance supplied; environment-error covariance not supplied;
- intercept: 2.3601, SE 0.4685, P=4.72×10^-7;
- environment slope: −0.03705, SE 0.1562, P=0.8125;
- residual Q=192.89 on 94 degrees of freedom, P=8.42×10^-9.

### Environment-correlation sensitivity

Command output directory: `results/real/arabidopsis_baseline_AT1G11560_envproxy/`.

The proxy correlation is the Pearson correlation of FT10 and FT16 across 1,122 shared AraPheno accessions (`r=0.88195`). It is not known ratio-error covariance and is not a primary inference input.

- intercept: 1.8027, SE 0.6217, P=0.00374;
- environment slope: −0.08228, SE 0.06634, P=0.2149;
- residual Q=189.67 on 94 degrees of freedom, P=1.97×10^-8.

### Independent-environment baseline

Command output directory: `results/real/arabidopsis_baseline_AT1G11560_stratified_all/`.

Without LD covariance/clumping, fixed IVW estimates are 6.6001 (10°C) and 8.2379 (16°C), with Q-test P=5.89×10^-4 and 2.00×10^-5, respectively. These are deliberately shown as a comparator, not as preferred biological estimates: the strong local LD and heterogeneity make the independent-IVW assumption inappropriate.

## Interpretation boundary

This case demonstrates that PlantMR can ingest a real plant molecular-trait/outcome pair, retain environment labels, apply complete-grid QC, and expose how LD and environment-covariance assumptions change inference. It does not establish that AT1G11560 is causal, because:

1. expression and flowering phenotypes share accessions, but exposure–outcome sampling covariance was not estimated;
2. the local OLS associations are not the published mixed-model summary statistics;
3. the baseline expression exposure is copied across outcome environments, so the slope describes outcome-environment heterogeneity, not an environment-specific eQTL mechanism;
4. residual heterogeneity is significant;
5. independent functional validation is not supplied by this software run.

The published Arabidopsis study independently reported SMR/HEIDI evidence for AT1G11560, but that is external evidence and is not silently counted as validation of this local PlantMR re-analysis.
