# PlantMR v1.1.0 中文说明

PlantMR v1.1.0 是一个面向植物/作物GWAS与QTL摘要数据的本地MR工具，重点是：

1. 把植物物种、参考组装、组织、发育阶段、环境、倍性和LD来源写进分析契约；
2. 在等位基因协调、工具变量筛选和LD假设上留下可检查的审计记录；
3. 同时提供普通摘要MR、按环境分层MR和协方差感知的环境交互MR；
4. 输出机器可读结果和人类可读报告。

已实现：固定/随机效应IVW、Wald ratio、MR-Egger、异质性Q、留一分析、LD clumping、环境分层分析、完整SNP×环境网格的G×E GLS、JSON/TSV/Markdown报告。

## `run-gxe`

暴露表和结局表都要有 `environment` 列，暴露表必须有 `environment_value`。同一个SNP必须在所有环境出现，工具只保留在所有环境均通过工具变量QC的SNP。可选的环境相关矩阵和SNP-LD相关矩阵必须为带符号相关系数方阵。

```bash
plantmr run-gxe \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --environment-correlation environment_corr.tsv \
  --ld-correlation ld_corr.tsv \
  --outdir gxe_result
```

输出包括 `gxe_harmonized.tsv`、`results.json` 和 `report.md`。报告中的 `slope` 是环境交互斜率，不等于“所有环境下的因果基因”；若没有协方差文件，结果会明确标记为对角近似。

最终边界、统计假设和已完成验收见 `docs/FINAL_REPORT.zh-CN.md`。MR-GxE和MR-EILLS等相关方法已经存在，本项目的贡献定位为植物/作物摘要数据契约、环境/LD协方差实现和可复现审计工作流；不宣称环境交互MR理论首创。外部SMR/GSMR、共定位、多变量MR和泛基因组结构变异模型没有被冒充为内置功能。
