# PlantMR Causal Genomics Final Plan and Research Roadmap

> **For Hermes:** Implement task-by-task with strict TDD. Each statistical behavior must have a failing test before production code.

**Goal:** Deliver and maintain a plant-native Mendelian randomization toolkit that turns plant GWAS/QTL summary statistics into harmonized, diagnostically transparent MR results and reproducible reports.

**Architecture:** A Python package exposes a stable summary-statistics schema, allele harmonization, instrument QC, optional LD clumping, MR estimators, plant metadata, environment stratification, covariance-aware G×E GLS, report generation, and tests. v1.1 is a complete local CLI product for summary MR plus a narrowly defined environment-slope estimand; external-method adapters and polyploid/PAV/SV causal models remain separately versioned research extensions.

**Tech Stack:** Python 3.10+, NumPy, pandas, pytest, argparse/JSON/Markdown; optional R/GCTA/SMR adapters only behind explicit external-tool interfaces.

---

## Final v1.0 closure

Completed and verified in the repository:

- summary-statistics schema and plant metadata;
- allele harmonization and palindromic handling;
- P-value/MAF/F-statistic QC and optional LD clumping;
- Wald ratio, fixed/random IVW, MR-Egger, heterogeneity and leave-one-out diagnostics;
- environment-stratified MR;
- JSON/TSV/Markdown reports, Conda/Docker packaging, tests and CI configuration.

The v1.0 contract deliberately does not claim built-in SMR/GSMR, coloc, MVMR, MR-PRESSO, hierarchical G×E, polyploid dosage, PAV/SV or pan-genome causal inference. Those are research extensions, not hidden TODOs inside the final release.

## Research route and gates

### Stage R0: Scope and evidence freeze

- Treat MRBIGR as the closest plant-oriented comparator, not as an empty field.
- Compare against SMR/HEIDI, GSMR/GSMR2, TwoSampleMR, MendelianRandomization, coloc and plant G×E tools.
- Freeze the first biological question as: “Does a genetically increased molecular trait affect a crop phenotype, and does the effect differ by tissue, stage, or environment?”
- Do not call a result causal unless instrument validity, direction, pleiotropy, and independent biological evidence are reported.

Gate: a written comparator matrix and a machine-readable input/output schema exist before large implementation.

### Stage R1: v1.0 usable summary-MR tool — complete

Scope:

- TSV/CSV exposure and outcome summary statistics.
- Explicit species, assembly, trait, tissue, stage, environment, ploidy, and LD-panel metadata.
- Allele harmonization, palindromic-variant handling, sample-size and allele-frequency checks.
- Instrument selection by exposure P value, MAF, F statistic, and LD-clumped input declaration.
- Wald ratio, fixed/random-effects IVW, Cochran heterogeneity, MR-Egger when identifiable, leave-one-out diagnostics.
- JSON/TSV/Markdown outputs and a single reproducible command.

Gate: synthetic end-to-end test passes; malformed allele orientation and weak-instrument fixtures are rejected or explicitly flagged; report contains a warning when LD clumping or independent LD reference is absent.

### Stage R2: plant reliability layer

- Add reference-panel metadata and LD correlation import.
- Add colocalization and fine-mapping adapters.
- Add SMR/HEIDI and GSMR adapters with version capture, command capture, and output parsing.
- Add multiple-testing correction and evidence tiers.
- Add negative-control and permutation modules.

Gate: identical input plus identical configuration gives byte-stable machine-readable results; external-tool failures are surfaced rather than silently replaced.

### Stage R3: environment- and tissue-aware MR — implemented with bounded scope

Research hypothesis: causal effects of molecular traits on crop phenotypes can vary across environments, tissues, or developmental stages, and this heterogeneity should be estimated rather than averaged away.

- Define environment-specific beta/se inputs and covariance metadata. [done]
- Implement pooled effect, condition-specific effect, heterogeneity, and effect-by-environment models. [done for linear two-parameter GLS]
- Add cross-environment replication and sign-consistency reports.
- Compare against plant multi-environment GWAS/meta-analysis baselines and ordinary MR.
- Simulate realistic plant LD, population structure, sample overlap, weak instruments, and directional pleiotropy.

Gate: calibrated type-I error under null simulations, power curves across instrument strengths, and a held-out real crop dataset with predefined success criteria. The current Arabidopsis case is an executable application demonstration with explicit sample-overlap and local-OLS limitations; it is not independent causal validation.

### Stage R4: plant genome complexity

- Polyploid allele dosage and homoeolog-aware identifiers.
- PAV/SV instruments with explicit variant classes and reference-assembly mapping.
- Pan-genome/graph coordinate adapters.
- Species-specific LD panels and cross-population portability diagnostics.

Gate: each variant class has separate simulation and real-data validation; unsupported representations fail loudly instead of being coerced into SNPs.

### Stage R5: usable product

- Python CLI remains the reference interface.
- Add a lightweight local web UI only after the CLI/report contract is stable.
- Provide example datasets, tutorials, schema documentation, versioned reports, environment lock, and container.
- Benchmark runtime and memory on desktop and HPC-style batch execution.

Gate: a new user can install the package, run the example in one command, inspect the report, and reproduce the same result.

---

## Implementation tasks

### Task 1: Establish repository and contracts

Files:

- Create: `pyproject.toml`
- Create: `README.md`
- Create: `README.zh-CN.md`
- Create: `src/plant_mr/__init__.py`
- Create: `src/plant_mr/schema.py`
- Create: `tests/test_schema.py`

Acceptance:

- Supported Python version and installation command are documented.
- Required summary-statistic columns and optional plant metadata are explicit.
- A valid small table passes validation; missing beta/se/allele columns fail with actionable messages.

### Task 2: Allele harmonization

Files:

- Create: `src/plant_mr/harmonize.py`
- Create: `tests/test_harmonize.py`

Acceptance:

- Same alleles retain effect direction.
- Reversed alleles flip beta and preserve SE.
- Complement alleles are recognized only when unambiguous.
- Ambiguous palindromic variants are removed or retained only with a declared EAF rule.
- Duplicate SNPs and incompatible alleles produce explicit status codes.

### Task 3: Instrument selection and QC

Files:

- Create: `src/plant_mr/instruments.py`
- Create: `tests/test_instruments.py`

Acceptance:

- Exposure P-value, MAF and F-statistic thresholds are applied deterministically.
- Weak instruments are excluded with a reason.
- Input that claims pre-clumped instruments records that claim in the report.
- Absence of LD information is a warning, not a hidden assumption.

### Task 4: Core estimators

Files:

- Create: `src/plant_mr/estimators.py`
- Create: `tests/test_estimators.py`

Acceptance:

- Wald ratio is correct for one instrument.
- IVW estimate and standard error are correct for multiple instruments.
- Random-effects IVW and Cochran Q are reported when heterogeneity is estimable.
- MR-Egger is disabled with an explicit reason when fewer than three usable instruments remain.
- Zero or non-finite standard errors fail validation.

### Task 5: Reproducible report

Files:

- Create: `src/plant_mr/report.py`
- Create: `tests/test_report.py`

Acceptance:

- Report includes input metadata, tool version, configuration, filtering counts, method results, warnings, and output paths.
- JSON is machine-readable and Markdown is human-readable.
- Results are stably ordered.

### Task 6: CLI vertical slice

Files:

- Create: `src/plant_mr/cli.py`
- Modify: `pyproject.toml`
- Create: `tests/test_cli.py`
- Create: `examples/synthetic/exposure.tsv`
- Create: `examples/synthetic/outcome.tsv`
- Create: `examples/synthetic/metadata.json`

Acceptance:

- `plantmr validate` validates both tables and metadata.
- `plantmr run` produces harmonized data, JSON results, and Markdown report.
- The example command succeeds from a clean environment.
- The end-to-end output includes a warning that the example does not provide LD correlations.

### Task 7: Statistical verification

Files:

- Create: `tests/test_simulation.py`
- Create: `docs/methods/estimands.md`
- Create: `docs/methods/assumptions.md`
- Create: `docs/benchmarks/` for future simulation benchmark records

Acceptance:

- Future simulation benchmarks must cover weak instruments, pleiotropy, LD and environment-specific effects before any new estimator is released.
- Type-I error, bias, coverage and power are reported rather than only point estimates.
- The tool never presents simulation truth as real-data evidence.

### Task 8: Plant-aware extension design

Files:

- Create: `docs/methods/environment-aware-mr.md`
- Create: `docs/methods/polyploid-and-pan-genome.md`
- Create: `docs/roadmap.md`
- Create: `docs/comparator-matrix.md`

Acceptance:

- Environment-aware MR is specified with estimands, covariance requirements, identification assumptions and failure modes before implementation.
- Polyploid/PAV/SV support is represented as explicit variant classes, not a generic SNP alias.
- At least two crop datasets are selected with sample IDs, traits, environments, tissues, and independent validation evidence documented.

### Task 9: Release hardening

Files:

- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Create: `CHANGELOG.md`
- Create: `LICENSE`
- Create: `.github/workflows/test.yml`
- Create: `environment.yml`
- Create: `Dockerfile`

Acceptance:

- Tests pass in the locked environment and container.
- Example output is reproducible.
- Unsupported methods and missing external dependencies fail clearly.
- Documentation distinguishes association, MR evidence, and experimental validation.

---

## Non-negotiable scientific safeguards

- Do not use “causal gene” as an unconditional label; use “MR-prioritized candidate” unless independent evidence supports stronger language.
- Do not silently harmonize incompatible genome builds, gene IDs, alleles, or ploidy states.
- Do not apply a human LD reference panel to a plant population without an explicit warning and sensitivity analysis.
- Do not treat consistent estimates across MR estimators as proof that all instruments are valid.
- Do not call an ordinary multi-environment GWAS meta-analysis an environment-aware MR method.
- Do not use the same data to choose instruments, tune thresholds, select a favorable method, and claim independent validation.

## Definition of done for the first usable release

A user can run one command on a documented exposure/outcome pair and receive:

1. validated and harmonized instruments;
2. filtering and warning audit;
3. Wald/IVW/random-effects/Egger results when identifiable;
4. heterogeneity and leave-one-out diagnostics;
5. explicit plant metadata and LD assumptions;
6. machine-readable JSON and human-readable Markdown;
7. deterministic output under a pinned environment;
8. tests and a synthetic example that pass on a clean install.
