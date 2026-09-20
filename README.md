# PlantMR

PlantMR is a small Python toolkit for Mendelian randomization with plant and crop summary statistics. It is designed for analyses in which the species, reference assembly, tissue, developmental stage, environment and LD reference panel need to stay attached to the results.

The current release provides three related workflows:

- ordinary summary-statistics MR;
- MR estimates reported separately for each environment;
- a covariance-aware model for asking whether the MR effect changes along a prespecified environmental scale.

The third workflow is intentionally narrow. It estimates an intercept and an environment slope from a complete SNP-by-environment grid. It is not an implementation of MR-GxE, MR-GENIUS or MR-EILLS, and it does not turn an MR association into an automatically validated causal gene.

Repository: https://github.com/Zhangzhishuai-HIT/PlantMR

## PlantMR 2.x CLI-first platform

The `platform-v2` development branch is rebuilding PlantMR as a practical,
GUI-free plant causal multi-omics platform. It currently provides the
`plantmr2` project workflow, shared input contracts, ordinary summary MR,
transparent GWAS/QTL baselines, SMR/HEIDI, GO enrichment and causal-edge
network summaries. The implementation is deliberately explicit about what
is not yet a mixed-model GWAS, LD-aware multi-omics model or colocalization
engine.

Start with `plantmr2 init`, then `inspect`, `validate` and `run`. The full
Chinese CLI and data-contract guide is in
`docs/PlantMR2-CLI使用与数据契约.zh-CN.md`. The published v1.1.0 manuscript
release remains on `main` and is not overwritten by this development work.

## What is included

- summary-statistics input validation and plant metadata;
- allele harmonization, including reverse-strand handling and palindromic-allele checks;
- P-value, MAF, F-statistic and non-finite-value checks;
- optional signed LD clumping;
- Wald ratio, fixed-effects IVW, random-effects IVW and MR-Egger;
- Cochran's Q, MR-Egger intercept and leave-one-out diagnostics;
- environment-stratified MR;
- covariance-aware GLS for a complete SNP-by-environment grid;
- explicit environment and LD correlation matrices;
- JSON, TSV and Markdown reports;
- a summary-data MR-GxE comparator used only for the external-method benchmark;
- synthetic examples, real-data processing records and simulation scripts.

## Installation

Python 3.10 or later is required.

```bash
python -m pip install -e .
```

The research environment is listed in `environment.yml`. The core package uses NumPy, pandas and SciPy; the benchmark and figure scripts additionally use statsmodels, matplotlib and psutil.

## Ordinary summary MR

```bash
plantmr validate \
  --exposure examples/synthetic/exposure.tsv \
  --outcome examples/synthetic/outcome.tsv \
  --metadata examples/synthetic/metadata.json

plantmr run \
  --exposure examples/synthetic/exposure.tsv \
  --outcome examples/synthetic/outcome.tsv \
  --metadata examples/synthetic/metadata.json \
  --ld-matrix examples/synthetic/ld.tsv \
  --outdir examples/synthetic/result
```

The LD file is optional. When supplied, it is a square matrix of signed LD correlations with SNP identifiers in the first column and header. When it is omitted, the report says that independence was not checked with an LD panel.

## Environment-stratified MR

The exposure and outcome tables contain an `environment` column. A SNP can therefore occur once per environment.

```bash
plantmr run-stratified \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --outdir stratified_result
```

The output includes `environment_results.tsv`, `results.json` and `report.md`.

## Covariance-aware environment-effect analysis

For this analysis, both tables contain `environment`, and the exposure table also contains one numeric `environment_value` for each environment. Every retained SNP must be present in every environment and must pass the instrument filters in every environment.

```bash
plantmr run-gxe \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --environment-correlation environment_corr.tsv \
  --ld-correlation ld_corr.tsv \
  --outdir gxe_result
```

For each SNP and environment, PlantMR calculates `beta_outcome / beta_exposure` and fits a two-column GLS model with `[1, environment_value]`. The intercept is the estimated effect at `environment_value = 0`; the slope is the change in that estimate per unit of the environmental score.

The environment and LD matrices must be signed correlation matrices. If they are not supplied, PlantMR uses the diagonal approximation and states that choice in the report. The model is an effect-heterogeneity model. Its intercept should not be read as a horizontal-pleiotropy term.

## External-method comparison

`scripts/run_mr_gxe_head_to_head.py` implements a narrow summary-data MR-GxE comparator based on the three-step score regression described by Spiller et al. The benchmark passes the same simulated summary-statistics tables to PlantMR and the comparator. Because the two methods estimate different quantities, the benchmark scores each method only in scenarios where its own target is defined; other outputs are shown as diagnostics rather than placed on a single leaderboard.

The results and figure are in:

- `results/benchmarks/mr_gxe_head_to_head/`
- `docs/figures/mr_gxe_head_to_head.png`
- `docs/figures/mr_gxe_head_to_head.pdf`

## Input columns

Required columns for ordinary MR:

`SNP`, `effect_allele`, `other_allele`, `beta`, `se`, `pval`

Recommended columns:

`eaf`, `n`

Plant metadata should describe:

`species`, `assembly`, `trait`, `tissue`, `stage`, `environment`, `ploidy`, `ld_panel`

## Interpreting results

- The output is MR evidence conditional on the instrumental-variable assumptions; it is not an automatic declaration that a gene is causal.
- MR-Egger and random-effects IVW do not remove every form of horizontal pleiotropy.
- Environment-stratified estimates are conditional estimates, not a complete structural model of genotype-by-environment biology.
- SMR/HEIDI, GSMR, colocalization, fine-mapping, MVMR, MR-PRESSO and polyploid or pan-genome SV models are not silently substituted by the commands in this release.
- A real biological study still needs matching LD data, independent replication and functional evidence.

More detail is available in:

- `docs/methods/estimands.md`
- `docs/methods/assumptions.md`
- `docs/methods/environment-aware-mr.md`
- `docs/real-case-arabidopsis.zh-CN.md`
- `docs/mr-gxe-head-to-head.zh-CN.md`
- `docs/similar-article-writing-audit.zh-CN.md`
- `docs/PlantMR_submission_manuscript.docx`
- `docs/PlantMR_submission_manuscript.pdf`
- `docs/PlantMR_submission_manuscript.zh-CN.docx`
- `docs/PlantMR_submission_manuscript.zh-CN.pdf`
- `docs/manuscript-draft.zh-CN.md`
- `docs/PlantMR-MRBIGR目标与超越路线.zh-CN.md`
- `docs/PlantMR2-CLI使用与数据契约.zh-CN.md`

## License

MIT License. See `LICENSE`.
