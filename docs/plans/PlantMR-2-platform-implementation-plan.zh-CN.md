# PlantMR 2.x platform core implementation plan

> **For Hermes:** Implement this plan task-by-task with strict TDD. Keep `main` and the published v1.1.0 release unchanged; work on branch `platform-v2` until the new vertical slice is stable.

**Goal:** Build a practical, CLI/API-first plant causal multi-omics platform without a graphical interface, covering the MRBIGR baseline modules while adding plant-native metadata, environment-aware covariance, reproducibility and safer result interpretation.

**Architecture:** Keep scientific engines as small importable Python modules. Put project configuration, provenance, validation and report generation around them. Every command reads one project manifest and writes a deterministic run directory with normalized inputs, a manifest, logs, results and a human-readable report. The first vertical slice will support project initialization, summary-statistics ingestion, plant metadata validation and execution of the existing ordinary/stratified/GxE engines through the new project contract.

**Tech Stack:** Python 3.10+, dataclasses/JSON/TOML-compatible configuration, pandas/NumPy/SciPy, pytest, existing PlantMR estimators retained behind adapters; CLI only, no GUI.

---

## Current implementation status

The CLI/API platform work in Tasks 1–9 is implemented on `platform-v2` and
covered by 73 automated tests. The implementation includes genotype/phenotype
QC, VCF/PLINK-raw/HapMap readers, PCA/kinship/t-SNE/UPGMA, OLS and
kinship-aware GLS GWAS, QTL, SAL/annotation, ordinary/stratified/environment
MR, SMR/HEIDI, coloc, MVMR, bidirectional networks/modules, GO, plots and
input hash receipts.

Task 10 remains an evidence task rather than an empty code placeholder:
running matched public maize/rice cases requires the external datasets and
GEMMA/GAPIT3/rMVP installations. PlantMR provides a safe external-command
adapter but does not invent those benchmark results. Therefore the repository
does not claim `MRBIGR_SURPASSED_IN_DEFINED_DIMENSIONS` until those runs have
real receipts.

## Product rules

1. `main` remains the v1.1.0 manuscript/software release. Platform work stays on `platform-v2` until a separate release decision.
2. No empty feature modules. A module is “implemented” only when it has a real input contract, a runnable path, result files, a report section and tests.
3. Every analysis records species, assembly, tissue, stage, environment, ploidy, LD source, sample overlap and software version.
4. A result report must distinguish association, MR-supported candidate, colocalization-supported result and functional validation.
5. CLI, Python API and future batch execution use the same project manifest. No GUI is planned.
6. Use TDD vertical slices: failing test, observed RED, minimal implementation, GREEN, refactor, full suite.

## Task 1: Create the v2 package contract

**Objective:** Define the project manifest and result-directory contract without changing v1 behavior.

**Files:**
- Create: `src/plant_mr/platform/__init__.py`
- Create: `src/plant_mr/platform/project.py`
- Create: `src/plant_mr/platform/errors.py`
- Create: `tests/test_platform_project.py`

**Required behavior:**

- `ProjectManifest.from_dict()` accepts `project_name`, `species`, `assembly`, `inputs`, `analyses` and `output_dir`.
- Required plant context fields fail with a clear error rather than silently defaulting.
- Relative input paths resolve relative to the manifest file, not the current shell directory.
- `ProjectManifest.to_dict()` produces stable key ordering and JSON-safe values.
- Unknown top-level fields are rejected or stored explicitly as `extensions`; they must not disappear.

**Verification:**

```bash
pytest tests/test_platform_project.py -q
```

## Task 2: Add project initialization and inspection

**Objective:** Let a user create a usable project skeleton from one command.

**Files:**
- Modify: `src/plant_mr/cli.py`
- Create: `src/plant_mr/platform/init.py`
- Create: `tests/test_platform_cli.py`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Commands:**

```bash
plantmr2 init maize-demo --species Zea_mays --assembly RefGen_v5 --outdir project
plantmr2 inspect project/plantmr.toml
```

**Required outputs:**

- `plantmr.toml` with explicit placeholders for exposure, outcome, genotype, phenotype, expression and LD inputs;
- `data/`, `runs/`, `reports/` and `logs/` directories;
- a README explaining the first required edits;
- `inspect` prints missing fields and never starts analysis.

**Verification:**

- init is deterministic for the same arguments;
- inspect exits non-zero for an incomplete manifest and reports each missing field;
- no analysis output is created by `inspect`.

## Task 3: Add a unified data/provenance manifest

**Objective:** Normalize file roles and provenance before adding more scientific modules.

**Files:**
- Create: `src/plant_mr/platform/inputs.py`
- Create: `src/plant_mr/platform/provenance.py`
- Create: `tests/test_platform_inputs.py`

**Required behavior:**

- Register input roles: genotype, phenotype, exposure, outcome, expression, metabolite, protein, LD, environment correlation and annotation.
- Validate file existence, readable format, SHA-256, declared species/assembly and optional sample counts.
- Write `run_manifest.json` with source paths stored relative to the project root and absolute paths omitted from public reports.
- Detect duplicate role declarations and stale hashes.

## Task 4: Expose existing MR engines through a project runner

**Objective:** Make v1.1 ordinary MR, environment-stratified MR and covariance-aware GxE usable through the new project contract.

**Files:**
- Create: `src/plant_mr/platform/runner.py`
- Create: `src/plant_mr/platform/report.py`
- Modify: `src/plant_mr/cli.py`
- Create: `tests/test_platform_runner.py`

**Commands:**

```bash
plantmr2 validate project/plantmr.toml
plantmr2 run project/plantmr.toml --analysis ordinary-mr
plantmr2 run project/plantmr.toml --analysis stratified-mr
plantmr2 run project/plantmr.toml --analysis environment-heterogeneity
```

**Required outputs per run:**

- `runs/<timestamp-or-run-id>/run_manifest.json`;
- normalized input receipt;
- `results.json` and tabular results;
- warnings and assumption ledger;
- `report.md`;
- non-zero exit with an actionable error on invalid input.

## Task 5: Build a user-friendly command contract

**Objective:** Make common work possible without reading Python source code.

**Files:**
- Modify: `src/plant_mr/cli.py`
- Create: `docs/platform-v2-cli.zh-CN.md`
- Create: `tests/test_platform_help.py`

**Required behavior:**

- `plantmr2 --help`, `init`, `inspect`, `validate`, `run`, `status` and `explain` have concise help;
- errors identify the file, column and correction;
- `explain estimand environment-slope` prints the estimand, assumptions and non-interpretations;
- `status` reads only run manifests and does not rerun analyses;
- all commands support `--json` for scripting.

## Task 6: Add the first MRBIGR-level data module

**Objective:** Add raw genotype and phenotype audit without pretending to implement GWAS yet.

**Files:**
- Create: `src/plant_mr/genotype/qc.py`
- Create: `src/plant_mr/phenotype/qc.py`
- Create: `tests/test_genotype_qc.py`
- Create: `tests/test_phenotype_qc.py`

**Required behavior:**

- genotype QC for VCF/PLINK-derived tabular input: missingness, MAF, duplicate markers, allele validity and sample counts;
- phenotype QC: missingness, duplicate accession IDs, numeric conversion, environment/tissue/stage completeness;
- results are reports and receipts, not hidden filters;
- raw input is never overwritten.

## Task 7: Add QTL/GWAS result adapters

**Objective:** Connect external plant GWAS/eQTL/mQTL/pQTL results into one downstream contract.

**Files:**
- Create: `src/plant_mr/association/schema.py`
- Create: `src/plant_mr/association/importers.py`
- Create: `tests/test_association_importers.py`

**Required behavior:**

- normalize variant, trait, tissue, stage, environment, beta, SE, P value, sample and allele fields;
- preserve source method and source software;
- support static, dynamic and environment-specific QTL labels;
- reject incompatible species/assembly unless explicitly overridden in the manifest.

## Task 8: Implement the first multi-omics causal vertical slice

**Objective:** Connect imported QTL to MR, HEIDI/colocalization-compatible evidence and a report.

**Files:**
- Create: `src/plant_mr/causal/smr.py`
- Create: `src/plant_mr/causal/heidi.py`
- Create: `src/plant_mr/causal/coloc.py`
- Create: `tests/test_smr.py`
- Create: `tests/test_heidi.py`
- Create: `tests/test_coloc_contract.py`

**Required behavior:**

- start with summary-statistics SMR-style ratio estimation and explicit HEIDI input contract;
- do not label an SMR association as causal without the documented assumptions;
- import external coloc/fine-mapping results with provenance before implementing every algorithm internally;
- write one candidate-level evidence table with association, MR, HEIDI/coloc and validation status separated.

## Task 9: Add network and GO outputs

**Objective:** Cover MRBIGR’s network and enrichment modules with auditable evidence.

**Files:**
- Create: `src/plant_mr/network/edges.py`
- Create: `src/plant_mr/network/build.py`
- Create: `src/plant_mr/enrichment/go.py`
- Create: `tests/test_network.py`
- Create: `tests/test_enrichment.py`

**Required behavior:**

- network edges retain exposure, outcome, method, effect, uncertainty, P value, source run and evidence class;
- GO enrichment records background gene set, annotation version and multiple-testing correction;
- network and enrichment reports cannot silently combine unsupported species annotations.

## Task 10: Benchmark against MRBIGR and publish the v2 decision

**Objective:** Establish whether PlantMR 2.x actually meets the stated goal.

**Files:**
- Create: `benchmarks/mrbigr_comparison/README.md`
- Create: `benchmarks/mrbigr_comparison/manifest.yaml`
- Create: `docs/PlantMR-2.0-evidence-report.zh-CN.md`
- Create: `tests/test_mrbigr_comparison_contract.py`

**Required comparisons:**

- feature coverage across all seven MRBIGR modules;
- same public maize multi-omics case where licensing and data access permit;
- an Arabidopsis environment-aware case;
- a multi-environment crop case;
- runtime, peak memory, failure modes and reproducibility receipts;
- target estimands and assumption differences.

**Decision gate:**

- `PLATFORM_READY` only when all implemented modules have real tests and end-to-end outputs;
- `MRBIGR_SCOPE_MATCHED` only when the seven baseline modules are runnable;
- `MRBIGR_SURPASSED_IN_DEFINED_DIMENSIONS` only for dimensions with matched evidence;
- otherwise report the narrower status honestly.

## First implementation order

Implement Tasks 1–5 first as one usable CLI/API backbone. Then implement Task 6 and Task 7 before adding SMR, network or GO. This avoids building disconnected algorithms that cannot share plant metadata, provenance or user-facing reports.
