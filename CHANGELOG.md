# Changelog

## 1.1.0 - covariance-aware plant GxE extension

- 增加 `run-gxe` 命令和 `gxe_ivw` API。
- 使用完整SNP×环境网格估计总体MR效应和环境交互斜率。
- 可显式输入环境相关矩阵和SNP-LD相关矩阵；缺失时在报告中警告并使用对角近似。
- 增加500次/场景的零模型、G×E功效和方向性多效性模拟，模拟结果与真实植物数据分开保存。
- 明确MR-GxE、MR-EILLS等现有方法，PlantMR不宣称环境交互MR理论首创。

## 1.0.0 - final release

- 固化摘要统计输入契约和植物元数据契约。
- 增加LD相关矩阵和r² clumping。
- 增加随机效应IVW、MR-Egger、异质性和留一分析。
- 增加按环境分层MR命令 `run-stratified`。
- 增加最终报告、方法假设、Docker入口和CI配置。
- 明确SMR/GSMR、共定位、MVMR、MR-PRESSO和泛基因组方法不属于本版内置算法。

## 0.1.0 - initial vertical slice

- 初始摘要数据读取、等位基因协调、工具变量筛选和基础报告。
