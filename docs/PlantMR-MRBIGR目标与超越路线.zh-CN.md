# PlantMR：对标并超过MRBIGR的产品与实现路线

## 目标

把PlantMR从当前的“植物摘要统计MR和环境效应异质性工具”发展成一个面向植物和作物的因果多组学分析平台：覆盖MRBIGR的基因型、表型、GWAS、MR、因果网络、GO富集和可视化七类能力，并在植物环境、LD、样本重叠、组织/发育阶段、多倍体和泛基因组输入方面提供更严格的数据契约和可复现分析。

当前v1.1.0不能称为MRBIGR的替代品，也不能称为超越MRBIGR。它作为已经完成的协方差感知摘要统计MR基线保留；后续路线进入PlantMR 2.x平台开发。

## MRBIGR的功能基线

MRBIGR论文（Xu et al., Plant Communications 2025, DOI 10.1016/j.xplc.2024.101197）明确描述了七个模块：

1. 基因型数据分析（geno）；
2. 表型数据分析（pheno）；
3. GWAS和显著关联位点分析（gwas/SAL）；
4. MR分析（mr）；
5. MR因果网络分析（net）；
6. Gene Ontology富集分析（go）；
7. 数据可视化，并通过GUI串联整个流程。

其案例覆盖玉米基因型、转录组、代谢组和农艺性状，也提供了水稻多组学案例、用户手册、补充算法和可复现脚本。

## 当前差距

| 能力 | PlantMR v1.1.0 | 目标状态 |
| --- | --- | --- |
| 原始基因型处理 | 只接收摘要统计和外部LD矩阵 | 支持VCF/PLINK/剂量矩阵、缺失率、MAF、LD、PCA、亲缘关系和群体结构 |
| 原始表型处理 | 只接收已整理的结局摘要统计 | 支持表型清洗、变换、批次/环境记录、重复和缺失审计 |
| 多组学输入 | 暴露/结局摘要统计 | 统一接入表达、代谢物、蛋白、甲基化和其他植物分子QTL |
| GWAS/eQTL | 不直接运行 | 植物GWAS、eQTL、mQTL、pQTL和环境特异QTL工作流 |
| 标准MR | Wald、IVW、MR-Egger、Q、留一法和环境分层MR | 扩展到稳健MR、SMR/HEIDI、GSMR、MVMR、中介、双向MR和多组学MR |
| G×E | 已有窄定义环境斜率和协方差GLS | 保留当前模型，并增加环境特异eQTL、交互MR、连续环境、非线性环境和样本重叠协方差 |
| 共定位/精细定位 | 没有内置实现 | coloc/多信号共定位、fine-mapping、HEIDI和LD一致性检查 |
| 因果网络 | 没有 | 基因—表达—代谢物—性状的方向性网络、边级证据和网络审计 |
| GO/通路 | 没有 | GO、KEGG/植物通路、富集背景和多重检验记录 |
| GUI | 没有 | GUI和无界面批处理共用同一后端任务、配置和报告格式 |
| 报告 | JSON、TSV、Markdown | 统一项目报告、图表、源数据、日志、参数锁和可复现运行记录 |
| 植物原生支持 | 元数据、LD、环境、组织/阶段、倍性字段 | 再加入多倍体剂量、亚基因组、泛基因组、PAV/SV和多材料环境设计 |

## “超过MRBIGR”的定义

不能只靠模块数量声称超过。达到以下条件后，才可以在论文中写“功能范围超过MRBIGR”或类似表述：

1. 七类基线模块都有真实可运行的实现，而不是空接口或文档占位；
2. 同一套输入契约能完成从数据导入、QC、QTL/GWAS、MR到网络和富集的连续运行；
3. 用公开的玉米多组学案例重跑MRBIGR论文中的核心分析，并保留输入、参数、输出和差异解释；
4. 至少增加一个MRBIGR没有覆盖或没有作为核心估计目标的植物专长能力：协方差感知环境效应异质性、环境特异eQTL、样本重叠协方差、多倍体/泛基因组输入或结构变异；
5. GUI和CLI产生同一份机器可读结果，不允许GUI有一套隐藏逻辑；
6. 所有重要结果都有源数据、参数、软件版本、随机种子、失败记录和可复现报告；
7. 与MRBIGR比较时同时报告功能覆盖、运行资源、成功/失败案例和估计目标，不能只挑PlantMR有利的指标。

## 目标架构

### 1. 数据层：植物多组学数据契约

建议新增目录：

- `src/plant_mr/ingest/`
- `src/plant_mr/schema/`
- `src/plant_mr/provenance/`

统一记录：

- species；
- reference assembly；
- genotype representation；
- accession/line ID；
- tissue；
- developmental stage；
- treatment/environment；
- ploidy and subgenome；
- assay and normalization；
- sample overlap；
- LD/QTL panel provenance；
- source URL、文件哈希和处理步骤。

目标是让基因型、表型、表达、代谢物和蛋白数据都能被同一个项目配置引用，而不是每个脚本自己解释输入。

### 2. 基因型和表型层

建议新增目录：

- `src/plant_mr/genotype/`
- `src/plant_mr/phenotype/`
- `src/plant_mr/population/`

功能包括：

- VCF/PLINK/剂量矩阵读取；
- 缺失率、MAF、杂合率和等位基因检查；
- PCA和亲缘关系矩阵；
- LD计算、clumping和tag SNP；
- 群体结构和材料分层报告；
- 表型缺失、异常值、变换、重复和环境信息审计；
- 多倍体剂量和亚基因组编码；
- PAV/SV的显式输入契约。

第一阶段不应直接复制MRBIGR的GUI功能，而应先让所有输入处理都有独立、可测试的Python API和命令行接口。

### 3. 关联分析层

建议新增目录：

- `src/plant_mr/association/`
- `src/plant_mr/qtl/`

功能路线：

1. 单性状GWAS和多环境GWAS；
2. 表达QTL、代谢物QTL和蛋白QTL；
3. cis/trans、静态/动态和环境特异QTL；
4. 多环境效应、交互项和异质性统计；
5. SAL/候选位点表；
6. 与现有外部GWAS工具的结果导入和统一审计。

正式植物分析可以优先调用成熟的混合模型程序或容器，PlantMR负责输入契约、参数记录、结果导入和跨模块连接，不应在第一阶段盲目重写所有GWAS算法。

### 4. 因果分析层

建议新增目录：

- `src/plant_mr/causal/`
- `src/plant_mr/colocalization/`
- `src/plant_mr/fine_mapping/`

分层实现：

第一层，已有能力整理成统一接口：

- Wald；
- fixed/random IVW；
- MR-Egger；
- weighted median/mode；
- Q和留一法；
- 环境分层MR；
- 当前协方差感知环境斜率。

第二层，植物多组学常用方法：

- SMR/HEIDI；
- GSMR/GSMR2兼容输入和结果审计；
- MVMR；
- 双向/递归MR；
- 中介分析；
- 多组学MR；
- 共定位和多信号共定位；
- fine-mapping和可信集合；
- 样本重叠、弱工具和方向性多效性敏感性。

第三层，PlantMR的专长：

- 环境特异eQTL与环境特异MR；
- SNP和环境联合协方差；
- 连续环境和非线性环境基函数；
- 多环境混合模型摘要统计导入；
- 多倍体和PAV/SV工具变量；
- 跨群体/跨组织/跨发育阶段的估计目标追踪。

每个方法必须单独记录：输入契约、估计目标、识别假设、LD要求、样本重叠要求、失败条件和不能解释的结果。

### 5. 网络和通路层

建议新增目录：

- `src/plant_mr/network/`
- `src/plant_mr/enrichment/`

功能包括：

- 基于MR边的有向网络；
- 边级方法、P值、效应值、方向和证据来源；
- 网络中的多重检验；
- hub节点与模块分析；
- GO、KEGG/植物通路富集；
- 背景基因集、物种注释版本和注释缺失率；
- 网络与功能验证结果分层展示。

不能把MR网络边直接写成已证实调控关系。网络报告必须区分“统计支持的候选边”“共定位支持”“独立验证”和“功能验证”。

### 6. GUI和运行层

建议新增：

- `src/plant_mr/app/`
- `src/plant_mr/workflow/`
- `configs/`
- `tests/integration/`

GUI应当只是统一后端的一个入口，至少支持：

- 新建项目和导入数据；
- 数据契约检查；
- 选择分析模块和参数；
- 预览QC和工具变量；
- 运行GWAS/QTL/MR/网络/富集任务；
- 查看任务日志和失败原因；
- 导出图、表、JSON、TSV、Markdown和完整运行包。

CLI、Python API和GUI必须共享同一个配置文件和同一个结果模式。

## 分阶段执行路线

### Phase 0：目标和契约冻结

目标：不再把v1.1.0当作最终产品。

产出：

- MRBIGR七模块功能交叉表；
- PlantMR 2.x统一数据模式；
- 每个模块的估计目标和边界；
- 玉米、Arabidopsis、Populus或水稻案例登记表；
- 公共数据和许可证清单；
- GUI/CLI共同配置格式。

验收：所有模块都有明确输入、输出、测试和失败条件。

### Phase 1：统一数据层和原始数据入口

目标：从“只接收摘要统计”扩展到可审计地接收基因型、表型和多组学数据。

优先实现：

- VCF/PLINK/剂量矩阵；
- phenotype table；
- expression/metabolite table；
- accession/environment/tissue/stage schema；
- MAF、缺失率、PCA、LD和样本重叠报告。

验收：同一项目配置可以导入玉米和Arabidopsis示例，并生成一致的数据契约报告。

### Phase 2：GWAS/QTL和多环境关联

目标：覆盖MRBIGR的geno、pheno、gwas/SAL三类核心能力。

优先实现：

- 外部混合模型结果导入；
- eQTL/mQTL/pQTL统一结果模式；
- 静态/动态和环境特异QTL；
- 多环境效应与异质性报告；
- 结果与LD/样本/元数据绑定。

验收：能够从基因型/表型或标准化外部结果生成可进入MR模块的QTL摘要统计。

### Phase 3：多组学MR和共定位

目标：让PlantMR在分子因果推断上达到MRBIGR以上的植物专长深度。

优先实现：

- SMR/HEIDI；
- GSMR兼容工作流；
- MVMR和中介；
- 共定位和多信号共定位；
- fine-mapping接口；
- 弱工具、多效性、样本重叠和LD错配敏感性。

验收：完成玉米干旱、Arabidopsis AT1G11560和一个多组学作物案例的端到端运行，并明确区分候选、统计支持和功能证据。

### Phase 4：网络、GO和植物解释层

目标：覆盖MRBIGR的net、go和visualization模块，并提高证据分层。

优先实现：

- MR有向网络；
- GO和植物通路富集；
- hub/模块识别；
- 网络边级不确定性；
- 通路多重检验；
- 网络到功能验证的证据链。

验收：输出一份带源数据、边级证据和多重检验的完整网络报告，而不是只有一张网络图片。

### Phase 5：GUI、批处理和可复现运行包

目标：达到MRBIGR的易用性，并在可复现性上超过它。

优先实现：

- GUI项目管理；
- CLI和GUI同配置；
- 任务日志、失败恢复和断点；
- 容器/环境锁；
- 源数据、参数、版本、随机种子、结果和图表一体化归档；
- 自动生成中文/英文报告。

验收：新用户不读源代码，仅根据教程即可完成一个植物多组学MR项目，并得到可审计归档包。

## 论文策略

当前PlantMR v1.1.0手稿不能直接改写成“MRBIGR的全面替代品”。更稳妥的做法是：

1. 保留v1.1.0作为环境协方差MR基线论文；
2. 以PlantMR 2.x为新开发路线；
3. 完成至少三类端到端植物案例后，再写“对标并超过MRBIGR”的新论文；
4. 新论文中同时报告功能覆盖、统计估计目标、运行效率、失败案例和可复现性；
5. 不用模块数量代替真实功能，不把未实现模块写成已完成。

## 第一批真正值得先做的垂直切片

不要一开始同时开发七个空模块。优先完成一条可运行链：

“玉米基因型/表型/表达输入 → eQTL或外部QTL结果 → SMR/HEIDI和共定位 → PlantMR环境敏感性 → MR网络 → GO富集 → GUI/CLI报告”。

这条链完成后，再扩展到多倍体、PAV/SV和非线性环境模型。它比继续给当前v1.1.0添加零散MR估计器更接近MRBIGR，也更有机会真正超过MRBIGR。
