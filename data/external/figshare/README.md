# Maize drought supplementary data

Source article: Liu et al., *Mapping regulatory variants controlling gene expression in drought response and tolerance in maize*.

Source DOI: https://doi.org/10.1186/s13059-020-02069-1

Figshare item: https://doi.org/10.6084/m9.figshare.12618374.v1

Downloaded file:

- `maize_drought_additional_file_2.xlsx`
- Figshare file ID: `23720900`
- Download URL: `https://ndownloader.figshare.com/files/23720900`
- SHA-256: `2478c3ab688d3f408660a8b7db593086267c7ef16596961b26b9eba78b99b069`

Derived tabular extracts:

- `table_s2_eqtl.tsv`: 73,579 eQTL rows extracted from Table S2;
- `table_s5_mr_candidates.tsv`: 97 candidate-gene rows extracted from Table S5 after removing six footnote rows.

Derived-file SHA-256:

- `table_s2_eqtl.tsv`: `4a9c52fe1f629d9914e4c7c83ec1b7f09b7e4f18f87fba6ee2ed06b0ca595ae5`;
- `table_s5_mr_candidates.tsv`: `08ff9c6617a21fd9fd524bded1254f8e7bddadcd80335a0ef993c4b6553e2c73`.

Interpretation boundary:

- Table S5 contains the original paper's MR candidate list, treatment strings, reported expression-effect values and P values, and is suitable for reproduction/label auditing;
- Table S2 contains eQTL lead SNPs, treatments, P values and candidate annotations, but not a complete beta/SE summary-statistics contract for re-estimating PlantGxE-MR;
- the original raw reads and full genotype/phenotype inputs remain separate accessions and are not duplicated in this repository.
