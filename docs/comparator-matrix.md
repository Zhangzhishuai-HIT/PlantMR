# PlantMR comparator and scope

| Capability | PlantMR v1.0 | Generic MR packages | Plant-oriented MRBIGR |
|---|---|---|---|
| Plant metadata contract | Native fields for species, assembly, tissue, stage, environment, ploidy and LD provenance | Usually user-managed | Workflow-specific | 
| Allele harmonization | Built in with palindromic handling | Varies by package | Built into its own workflow | 
| LD-aware clumping | Optional signed LD matrix with explicit warning when absent | Usually external/reference-panel dependent | Input/workflow dependent | 
| Standard summary MR | Wald, fixed/random IVW, MR-Egger | Broad ecosystem | Individual-level/workflow-oriented MR | 
| Environment stratification | Built-in `run-stratified` | Usually manual | Not the primary contract | 
| PAV/SV/polyploid causal model | Explicitly out of scope in v1.0 | Usually out of scope | Not claimed as a universal solution | 
| Reproducible local report | JSON, TSV, Markdown, config and warnings | Package dependent | GUI/workflow reports | 

This matrix defines the v1.0 engineering scope; it is not a claim that any external package lacks features outside the listed contract. External adapters require version pinning and independent verification.
