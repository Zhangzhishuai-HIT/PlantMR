# PlantMR 2.x 与 MRBIGR 功能对照

本目录保存PlantMR 2.x的功能对照和可复现验证入口。MRBIGR功能基线来自Xu等人的论文及补充材料（Plant Communications, DOI: 10.1016/j.xplc.2024.101197）。

真实公开玉米fixture的下载、样本交集、运行结果和MRBIGR源码审计见：
`docs/PlantMR-MRBIGR真实公开玉米fixture验证报告.zh-CN.md`。

## 对照矩阵

| MRBIGR模块 | PlantMR 2.x实现 | 实际入口 | 证据/限制 |
|---|---|---|---|
| genotype | 已实现内部表格、VCF、PLINK `.raw`、HapMap读取；缺失率、MAF、填补、PCA、亲缘、t-SNE、UPGMA | Python API `qc_genotype`、`read_genotype`、`pca_scores`、`kinship_matrix`、`tsne_scores`、`upgma_newick` | 73项自动测试；PLINK二进制转换仍通过外部工具完成 |
| pheno | 已实现表型QC、mean/BLUE近似/BLUP收缩、变换、异常值审计、多环境合并 | `plantmr2 run --analysis phenotype-qc/environment-merge` | BLUE/BLUP为当前内部透明实现，须在正式育种数据上与专用软件头对头 |
| gwas/SAL | 已实现OLS、协变量、亲缘矩阵感知GLS、SAL、位置注释、Manhattan/QQ | `--analysis gwas/sal/annotate` | `gemma_mlm`是内部GLS，不宣称GEMMA数值复现；GAPIT3/rMVP通过外部命令适配而非内置R运行时 |
| mr | 已实现普通MR、stratified MR、环境异质性、SMR/HEIDI、ABF coloc、MVMR | `--analysis ordinary-mr/stratified-mr/environment-heterogeneity/smr/coloc/mvmr` | LD-aware fine-mapping、样本重叠协方差和复杂多效性仍需单独输入/模型 |
| net | 已实现双向MR边、权重、模块、hub分数、循环诊断 | `--analysis network` | 模块为greedy-modularity确定性近似，不称为ClusterONE完全复现；网络边不等于实验因果 |
| go | 已实现超几何富集、背景集合、BH校正 | `--analysis go` / `go_enrichment` | 注释版本和背景集合必须由用户提供；不自动下载物种注释 |
| plot | 已实现PNG/PDF Manhattan、QQ、MR森林图、网络图 | 各run自动写入 | 无GUI，图由Agg后端生成，适合批处理和论文初稿 |

## 可复现命令

```bash
python -m pip install -e .
pytest -q
python -m compileall -q src scripts
```

项目入口：

```bash
plantmr2 init demo --species Zea_mays --assembly RefGen_v5 --outdir demo
plantmr2 inspect demo/plantmr.toml --json
plantmr2 validate demo/plantmr.toml --json
plantmr2 status demo/plantmr.toml --json
plantmr2 explain environment-slope --json
```

## 当前对标状态

已经完成真实公开文件的PlantMR端到端fixture验证：VCF QC、表型QC、GWAS、QTL、SMR/HEIDI、coloc、MVMR、SAL、AGPv4注释、GO和网络均有run目录与结果回执。该fixture只保留了8个VCF×表型直接同名材料和5个VCF×表达直接同名材料，属于工程验证，不是正式生物学发现。

MRBIGR源码已下载并审计，但同输入头对头运行仍未完成：其入口依赖pandas-plink、pyranges、rpy2、R和外部工具；当前主机GCC 4.8.5无法编译sorted-nearest，Rscript/GEMMA/PLINK运行链也不齐。报告中没有把MRBIGR未运行解释成PlantMR胜出。

## 不把适配器说成内置算法

`platform.external.run_external_command`只负责安全地运行用户提供的外部命令、捕获日志并检查预期输出。它不包含GEMMA、GAPIT3或rMVP的源码，也不在没有这些软件时伪造结果。任何外部工具比较都必须保存工具版本、完整命令、输入回执和输出文件。
