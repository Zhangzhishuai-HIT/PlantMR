# PlantMR v1.0.0 中文说明

PlantMR v1.0.0 是一个面向植物/作物GWAS与QTL摘要数据的本地MR工具，重点是：

1. 把植物物种、参考组装、组织、发育阶段、环境、倍性和LD来源写进分析契约；
2. 在等位基因协调、工具变量筛选和LD假设上留下可检查的审计记录；
3. 同时提供普通摘要MR和按环境分层MR；
4. 输出机器可读结果和人类可读报告。

已实现：固定/随机效应IVW、Wald ratio、MR-Egger、异质性Q、留一分析、LD clumping、环境分层分析、JSON/TSV/Markdown报告。

最终边界、统计假设和已完成验收见 `docs/FINAL_REPORT.zh-CN.md`。外部SMR/GSMR、共定位、多变量MR和泛基因组结构变异模型没有被冒充为内置功能。
