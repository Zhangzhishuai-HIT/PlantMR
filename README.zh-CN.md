# PlantMR 植物因果组学工具

PlantMR 的目标是把植物GWAS/QTL摘要数据整理成透明、可复现、带植物元数据的MR分析流程。

当前 v0.1 已实现：

- 暴露/结局摘要统计规范检查；
- A/C/G/T等位基因协调和反向效应翻转；
- 回文位点模糊性处理；
- 工具变量P值、MAF、F统计量筛选；
- Wald ratio、固定效应IVW和Cochran异质性Q；
- JSON、TSV和Markdown报告。

现在的版本是第一个可运行纵向切片，不是最终研究版。环境、组织、发育期和多倍体字段已经进入输入契约；环境感知MR、SMR/GSMR、共定位、多倍体剂量、PAV/SV和泛基因组扩展写在 `PLAN.md` 中。

安装和示例请看英文 `README.md`。
