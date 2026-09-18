# PlantMR v1.1.0

PlantMR 是面向植物和作物GWAS/QTL摘要数据的本地因果组学工具。v1.1.0 的产品边界是：在明确声明植物物种、参考组装、环境和LD假设的前提下，完成可复现的摘要数据MR、环境分层MR和协方差感知的环境交互MR。

## 已实现功能

- 摘要统计输入规范和植物元数据；
- effect allele / other allele 协调、反向效应翻转、互补链识别；
- 回文位点的等位基因频率判定；
- P值、MAF、F统计量和非有限值检查；
- 可选LD相关矩阵的贪心clumping（默认r²阈值0.01）；
- Wald ratio、固定效应IVW、随机效应IVW、MR-Egger；
- Cochran异质性Q检验、MR-Egger截距和逐工具变量留一分析；
- `run-stratified` 按环境分别估计结果；
- `run-gxe` 用完整SNP×环境网格和显式协方差估计总体效应与环境交互斜率；
- JSON、TSV、Markdown报告；
- 合成数据、自动化测试、Conda环境和Docker入口。

## 安装

```bash
python -m pip install -e .
```

Python >= 3.10，依赖 NumPy、pandas、SciPy。

## 普通摘要MR

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

`--ld-matrix` 为可选的方阵，第一列为SNP，表头为SNP，数值为带符号LD相关系数。没有LD矩阵时工具会保留分析，但在报告中明确警告没有重新验证工具变量独立性。

## 环境分层MR

暴露和结局文件都需要增加 `environment` 列，同一SNP可以在不同环境重复出现：

```bash
plantmr run-stratified \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --outdir stratified_result
```

输出 `environment_results.tsv` 和 `results.json`，分别保存每个环境的估计、审计计数和警告。

## 协方差感知的环境交互MR

暴露和结局文件都需要增加 `environment` 列；暴露文件还需要每个环境唯一的数值列 `environment_value`。同一SNP必须在所有环境都有记录，工具会在每个环境内协调等位基因，再只保留所有环境均通过P值、F统计量和MAF筛选的SNP。

```bash
plantmr run-gxe \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --environment-correlation environment_corr.tsv \
  --ld-correlation ld_corr.tsv \
  --outdir gxe_result
```

模型对每个SNP×环境单元计算 `beta_outcome / beta_exposure`，用两列设计 `[1, environment_value]` 做广义最小二乘（GLS）。截距是 `environment_value=0` 时的总体MR效应，斜率是每增加一个环境值单位时MR效应的变化。环境相关矩阵和SNP-LD相关矩阵必须是带符号的相关矩阵；未提供时不会假装独立，而是在报告中写入警告并使用对角近似。

## 输入列

必需列：

`SNP`, `effect_allele`, `other_allele`, `beta`, `se`, `pval`

建议列：

`eaf`, `n`

植物元数据至少应说明：

`species`, `assembly`, `trait`, `tissue`, `stage`, `environment`, `ploidy`, `ld_panel`

## 结果解释边界

- 工具输出的是工具变量假设下的MR证据，不是自动确认的“因果基因”；
- MR-Egger和随机效应IVW不能消除所有水平多效性；
- 环境分层结果是条件性估计，不等同于完整的结构化G×E因果模型；
- v1.0不内置SMR/HEIDI、GSMR、共定位、精细定位、MVMR、MR-PRESSO或泛基因组SV因果模型；这些需要独立方法和版本锁定，不能静默替代；
- 没有LD参考面板时，不应把结果解释为已经完成独立工具变量验证；
- 真实研究仍需要跨群体/跨环境重复和实验功能验证。

完整的输入契约、统计假设和最终验收记录见：

- `PLAN.md`
- `docs/methods/estimands.md`
- `docs/methods/assumptions.md`
- `docs/FINAL_REPORT.zh-CN.md`
- `docs/methods/environment-aware-mr.md`
