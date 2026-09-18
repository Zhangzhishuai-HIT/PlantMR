# PlantMR v1.1.0 final report

## Deliverable

PlantMR v1.1.0 is a local Python CLI and library for plant/crop summary-statistics MR. The repository is self-contained at `/home/user/zhangzhishuai/myhermes/plant_mr`.

## Final product contract

The final release accepts two summary-statistics tables and a JSON plant metadata file. It validates alleles and numeric values, harmonizes effects, filters instruments, optionally performs LD clumping, runs fixed/random IVW and MR-Egger, performs leave-one-out diagnostics, and writes JSON/TSV/Markdown results. `run-stratified` repeats the same contract by environment. `run-gxe` adds complete-grid, covariance-aware GLS for a pooled effect and environment slope.

## Machine verification

本次最终验收实际返回：

- `pytest -q`：22 passed；
- `python -m compileall -q src`：通过；
- 安装后的 `plantmr validate`：通过；
- 安装后的普通 `plantmr run`：通过，LD clumping 移除1个高LD工具变量并保留2个；
- 安装后的 `plantmr run-stratified`：通过，`DS`和`WW`两个环境各输出固定IVW、随机IVW和MR-Egger，共6条方法结果；
- 普通流程生成 `harmonized.tsv`、`leave_one_out.tsv`、`results.json`和`report.md`；
- 分层流程生成 `environment_results.tsv`、`results.json`和 `report.md`；
- `run-gxe`真实执行通过，生成GxE摘要、协方差来源、完整网格QC和报告；
- 500次/场景的零模型、G×E功效和方向性多效性模拟已执行，生成TSV、JSON、PNG和PDF；
- Arabidopsis真实数据契约案例已执行，包含48个标准QC工具、LD协方差主分析和环境相关敏感性分析；
- Git工作区在提交前后均通过范围和空白检查。

当前机器没有 Docker/Podman 运行时，因此 Dockerfile 已纳入发布目录但未在本机执行镜像构建；Conda/本地pip安装路径已实际验证。

## Scientific boundary

This is a reliable summary-MR product, not a claim that MR alone establishes plant gene causality. SMR/GSMR, coloc, MVMR, MR-PRESSO, functional validation, polyploid haplotype modeling and pan-genome SV causal models are deliberately outside the v1.1 built-in estimator contract. MR-GxE and MR-EILLS are existing methodological comparators; PlantMR does not claim to invent environment-interaction MR. Unsupported methods must be added as versioned adapters with their own tests rather than silently substituted.

## Release evidence

The exact test command and observed output are recorded in the final session delivery. The repository includes `PLAN.md`, `CHANGELOG.md`, method definitions, synthetic inputs and the locked Conda specification used for verification.
