# PlantMR comparator and scope

| Capability | PlantMR v1.1 | Generic MR packages | Plant-oriented MRBIGR | MR-GxE / MR-EILLS |
|---|---|---|---|---|
| Plant metadata contract | Native fields for species, assembly, tissue, stage, environment, ploidy and LD provenance | Usually user-managed | Workflow-specific | Usually human/heterogeneous-GWAS oriented |
| Allele harmonization | Built in with palindromic handling | Varies by package | Built into its own workflow | Method-specific |
| LD-aware clumping/covariance | Optional signed LD matrix with explicit warning when absent | Usually external/reference-panel dependent | Input/workflow dependent | Depends on implementation/data |
| Standard summary MR | Wald, fixed/random IVW, MR-Egger | Broad ecosystem | Individual-level/workflow-oriented MR | Not the primary focus |
| Environment stratification | Built-in `run-stratified` | Usually manual | Not the primary contract | Explicit interaction/invariance estimands |
| Covariance-aware plant G×E summary MR | Complete SNP×environment grid, GLS with environment and LD correlation | Not a default plant contract | Not the primary contract | Closest conceptual comparators; not equivalent estimands |
| PAV/SV/polyploid causal model | Explicitly out of scope in v1.1 | Usually out of scope | Not claimed as a universal solution | Not the primary contract |
| Reproducible local report | JSON, TSV, Markdown, config and warnings | Package dependent | GUI/workflow reports | Varies |

This matrix defines the v1.1 engineering scope; it is not a claim that any external package lacks features outside the listed contract. MR-GxE and MR-EILLS are existing methodological comparators, so PlantMR does not claim to invent environment-interaction MR. External adapters require version pinning and independent verification.

Key comparator sources:

- MRBIGR: https://doi.org/10.1016/j.xplc.2024.101197
- MR-GxE: https://doi.org/10.1093/ije/dyy204
- MR-GENIUS / interaction-based MR: https://doi.org/10.1371/journal.pone.0271933
- MR-EILLS: https://www.nature.com/articles/s41467-025-62823-6
- Nature code/software guidance: https://media.nature.com/full/nature-cms/documents/GuidelinesCodePublication.pdf
