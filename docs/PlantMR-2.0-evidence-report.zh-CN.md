# PlantMR 2.0平台验收证据（中文）

## 当前交付

当前分支`platform-v2`已经不是最初的CLI骨架，而是一套无GUI的植物因果多组学CLI/API平台。所有分析都采用同一个`plantmr.toml`、输入契约和run回执。

已实现并有自动测试的主链：

1. 项目初始化、inspect、validate、status、estimand explain；
2. SHA-256输入回执和独立run目录；
3. VCF/VCF.GZ、PLINK raw、HapMap和表格基因型读取；
4. 基因型缺失率、MAF、样本过滤、随机/均值/众数填补、PCA、亲缘、t-SNE、UPGMA；
5. 表型缺失、填补、z-score/log1p/Box-Cox、异常值审计、mean/BLUE近似/BLUP收缩和多环境合并；
6. OLS、协变量模型、kinship-aware GLS GWAS；
7. eQTL/mQTL/pQTL基线；
8. SAL区域、最近基因/区间注释和lead-SNP单倍型汇总API；
9. 普通MR、环境分层MR、环境异质性GLS；
10. SMR/HEIDI、Wakefield ABF共定位、MVMR；
11. 双向MR网络、网络模块、hub分数、循环诊断和GO富集；
12. Manhattan、QQ、MR森林图和网络PNG/PDF。

## 真实验证

- 自动测试：77项通过；
- Python编译检查：通过；
- editable安装：通过；
- `plantmr2 --help`：通过；
- `init → inspect → validate`：通过；
- 多分析无GUI端到端run：普通MR、GWAS、QTL、QC、SMR、coloc、MVMR、GO、SAL、annotation、network、stratified MR、environment heterogeneity均有测试或运行验证；
- 真实公开玉米fixture：Panzea chr10 VCF、Maizego表达/表型、NCBI AGPv4 GFF和MaizeGDB GO均已下载并有SHA-256回执；Plantheight GWAS、两个表达QTL、SMR/HEIDI、coloc、MVMR、SAL、注释、GO和网络均真实运行；详细边界见`docs/PlantMR-MRBIGR真实公开玉米fixture验证报告.zh-CN.md`；
- 安全检查：外部命令适配器固定`shell=False`，不使用eval/exec/pickle，run_id拒绝路径穿越。

## 与MRBIGR的准确关系

PlantMR 2.x已经覆盖MRBIGR七个功能模块的内部CLI/API主链，但“覆盖模块名称”不等于“复现MRBIGR所有第三方工具和所有数值实现”。以下边界必须保留：

- `gemma_mlm`是PlantMR内部亲缘矩阵GLS实现，不是GEMMA二进制复现；
- GAPIT3/rMVP/GEMMA的外部命令只通过安全适配器接入，必须由用户安装并提供版本和输出；
- 当前没有完整LD-aware共定位/精细定位和样本重叠协方差模型；
- 多倍体复杂等位基因、PAV/SV和泛基因组专用模型没有被普通剂量矩阵静默替代；
- 没有GUI，用户体验通过CLI、JSON、Markdown、TSV、帮助、status和explain实现；
- 已完成PlantMR在真实公开玉米fixture上的独立运行，但该fixture只有8个VCF×表型直接同名样本和5个VCF×表达直接同名样本；MRBIGR源码头对头运行仍被其旧Python/R依赖链阻塞，因此尚未形成同输入数值胜负表。

因此，本交付可以称为“完整的PlantMR 2.x内部CLI/API平台实现”，但不能称为“已经在所有维度击败MRBIGR”。超过MRBIGR的结论只应在实际公开数据头对头结果产生后，对具体维度单独声明。
