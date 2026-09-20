# PlantMR and related methods

The table below describes what was implemented and what was compared for the current release. It is a scope description, not a claim that other packages lack functions that are not listed here.

| Capability | PlantMR v1.1 | Generic MR packages | MRBIGR | MR-GxE / MR-EILLS |
|---|---|---|---|---|
| Plant metadata | Species, assembly, tissue, stage, environment, ploidy and LD provenance are stored with the analysis | Usually supplied and managed by the user | Part of its own workflow | Usually human or heterogeneous-GWAS oriented |
| Allele harmonization | Included, with palindromic-allele handling | Varies by package | Included in its workflow | Depends on the implementation |
| LD-aware analysis | Optional signed LD matrix for clumping or covariance | Usually relies on an external reference panel | Depends on the input workflow | Method-specific |
| Standard summary MR | Wald ratio, fixed/random IVW and MR-Egger | Broad ecosystem | Primarily an individual-level and multi-omics workflow | Not the main purpose |
| Environment-stratified results | Built-in `run-stratified` command | Often assembled manually | Not the main input contract | Explicit interaction or invariance estimands |
| Plant environment-effect model | Complete SNP×environment grid with GLS and optional LD/environment correlation | Not usually a plant-native default | Not the primary contract | Related questions, different estimands |
| External comparison in this release | Shared-input summary-data MR-GxE comparator, with method-specific scoring | — | — | Compared as an external method, not merged into a common leaderboard |
| Polyploid/PAV/SV causal model | Not included in v1.1 | Usually not a default feature | Not claimed as a universal solution | Not the primary contract |
| Reports | JSON, TSV and Markdown reports with warnings and input provenance | Package dependent | GUI/workflow reports | Varies |

The shared-input comparison is in `results/benchmarks/mr_gxe_head_to_head/`. It uses the same simulated summary statistics, SNPs, environments and covariance inputs for PlantMR and the summary-data MR-GxE comparator. Because the two methods estimate different quantities, the comparison scores each method only where its own target is defined.

Key sources:

- MRBIGR: https://doi.org/10.1016/j.xplc.2024.101197
- MR-GxE: https://doi.org/10.1093/ije/dyy204
- MR-GENIUS / interaction-based MR: https://doi.org/10.1371/journal.pone.0271933
- MR-EILLS: https://www.nature.com/articles/s41467-025-62823-6
