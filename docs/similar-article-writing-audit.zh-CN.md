# Similar-article writing audit for PlantMR

更新时间：2026-09-19

## 本次参考的文章和期刊要求

1. Plant Methods 软件论文规范：
   - https://link.springer.com/journal/13007/submission-guidelines/software
   - 明确要求 Background、Implementation、Results、Discussion（如适用）、Conclusions、Availability and requirements、List of abbreviations 和 Declarations。
   - 摘要要求 Background、Results、Conclusions 三个小标题，少于350词，摘要中不引用参考文献。
   - 软件文章需要说明架构、可用性、验证、数据和材料，并通常通过相关软件的直接比较说明推进。

2. MAPtools：command-line tools for mapping-by-sequencing and QTL-Seq analysis and visualization，Plant Methods 20, 107 (2024)，DOI：10.1186/s13007-024-01222-2。
   - 写法特点：先用流程和问题说明工具用途，再写Implementation和命令；用公开发表的数据测试；给出图、图注、软件可用性、依赖和许可证；说明能做什么和不能做什么。
   - 对PlantMR的启发：把工作流图提前；在Implementation中先讲输入契约和命令；把真实Arabidopsis案例写成数据契约演示；加入Availability and requirements。

3. MRBIGR：A versatile toolbox for genetic regulation inference from population-scale multi-omics data，Plant Communications 6, 101197 (2025)，DOI：10.1016/j.xplc.2024.101197。
   - 写法特点：以工具定位和模块架构开篇；用模块图说明从数据准备、GWAS、MR到网络和可视化；使用玉米和水稻案例；提供补充方法、算法、图表和用户手册。
   - 对PlantMR的启发：需要把PlantMR与MRBIGR的功能边界写清，不把两个不同估计量包装成同一工具；把软件边界和未实现功能直接写入Discussion。

4. metaGE：Investigating genotype × environment interactions through GWAS meta-analysis，PLOS Genetics 21, e1011553 (2025)，DOI：10.1371/journal.pgen.1011553。
   - 写法特点：Background先解释多环境试验为什么复杂；Methods明确固定效应/随机效应和环境协变量；模拟中与竞争方法比较；再用Arabidopsis和作物案例验证；公开数据和R包。
   - 对PlantMR的启发：区分“环境异质性MR”与“G×E GWAS meta-analysis”；不能把两个方法当作同一估计量；应把模拟、竞争方法和真实案例分开写。

5. Conducting a Reproducible Mendelian Randomization Analysis using the R analytic statistical environment，Current Protocols in Human Genetics，DOI：10.1002/cphg.82。
   - 写法特点：按用户实际操作顺序组织；列出硬件、软件、输入文件、步骤和输出；逐个解释Wald、IVW和MR-Egger。
   - 对PlantMR的启发：软件论文不能只讲统计公式，还必须说明输入列、命令、输出文件和复现顺序。

## 本次真正用于植物MR结果和图形的文章

上一版主要用软件论文确定章节结构，这不足以指导植物MR结果图。此次补充以下三篇植物方向文章，分别用于结果顺序、图形类型和生物学边界：

1. Liu S et al. Mapping regulatory variants controlling gene expression in drought response and tolerance in maize. Genome Biology 21, 163 (2020). DOI：10.1186/s13059-020-02069-1。
   - 文章把水分处理、表达变化、eQTL、MR候选基因和实验验证连成一条证据链。
   - 对PlantMR的直接启发：图不能只有软件流程和模拟柱图，还要体现环境分层、分子关联和候选结果；PlantMR没有实验验证，因此只保留数据契约和诊断，不照搬“已验证基因”的语气。

2. Feng X et al. Dual-trait genomic analysis in highly stratified Arabidopsis thaliana populations using genome-wide association summary statistics. Heredity 133, 11–20 (2024). DOI：10.1038/s41437-024-00688-z。
   - 文章的SMR/HEIDI案例图把区域GWAS、eQTL、候选基因位置和LD结构放在同一个坐标体系中，并用独立表达数据复现候选基因。
   - 对PlantMR的直接启发：Arabidopsis图改为区域关联轨道、48个工具变量的LD热图、分环境森林图和环境斜率；同时明确本案例缺少独立复现和精确样本重叠协方差。

3. Liang X et al. Association study and Mendelian randomization analysis reveal effects of the genetic interaction between PtoMIR403b and PtoGT31B-1 on wood formation in Populus tomentosa. Frontiers in Plant Science 12, 704941 (2021). DOI：10.3389/fpls.2021.704941。
   - 文章先展示遗传变异和表达关联，再进入上位性、MR和木材性状解释。
   - 对PlantMR的直接启发：方法结果应先说明输入材料和环境，再报告遗传关联与MR估计，最后单独写能否支持生物学解释。

## 已应用到PlantMR稿件的变化

- 摘要改为Plant Methods要求的Background、Results、Conclusions结构，当前约242词，不含参考文献引用。
- 主文改为：Background → Implementation → Results → Discussion → Conclusions → Availability and requirements → List of abbreviations → Declarations → References。
- 在Implementation中加入PlantMR完整工作流图、输入契约、命令、工具变量筛选和协方差模型。
- 新增“Comparison with related tools”表，比较PlantMR、MRBIGR、MR-Base/TwoSampleMR、metaGE和MAPtools的任务范围、植物元数据、环境/LD处理和证据类型。
- 新增软件论文特有的Availability and requirements表，列出项目名、操作系统、编程语言、依赖、许可证和使用限制。
- 新增List of abbreviations和完整Declarations字段。
- Discussion中明确区分功能范围比较和性能比较；新增summary-data MR-GxE共享输入比较，但不把不同估计量放进一个总排行榜。
- 参考文献加入MAPtools和Populus植物MR案例，全文参考文献增至37条，全部正文引用编号均已覆盖，37个DOI均通过Crossref解析。
- 真实案例仍明确写成可复现数据契约演示，不写成AT1G11560因果验证。

## 本次Discussion的逐段写法

这次不是把原来的项目式小标题换一个标题，而是按照三篇文章常见的论证顺序重排Discussion。具体对应如下：

| PlantMR段落 | 参考文章中的对应写法 | 本稿承担的内容 |
| --- | --- | --- |
| Principal findings，第1–3段 | MRBIGR开头先交代工具解决什么分析需要；metaGE随后说明方法为什么适用于多环境数据 | 先说明植物摘要统计MR中的元数据问题，再定义环境斜率，最后用模拟结果说明协方差会改变推断 |
| Comparison with related methods，第1–3段 | metaGE的“Comparison to existing methods”；MRBIGR对工具模块和已有分析流程的定位 | 先放回标准MR框架，再区分summary-data MR-GxE、MR-GENIUS、MR-EILLS，最后说明PlantMR与MRBIGR、metaGE、MAPtools的任务差异 |
| Simulation and covariance behavior，第1–3段 | metaGE先给竞争方法的模拟表现，再解释假阳性和校准问题 | 先解释植物群体和多环境数据为什么产生相关误差，再解释rank-aware Q，最后区分功效与零假设校准 |
| Application to Arabidopsis data，第1–3段 | MRBIGR用玉米和水稻案例展示工具能完成什么；metaGE用Arabidopsis和作物数据展示方法表现 | 把Arabidopsis作为公开数据案例，报告主要结果，随后说明为什么不能把它写成因果发现，并解释表型相关性敏感性分析 |
| Use in plant and crop studies，第1–3段 | MAPtools从案例回到不同植物、输入格式和可复用工作流；MRBIGR回到多组学应用 | 说明自然群体、育种群体、eQTL、异源多倍体和结构变异使用时需要记录的条件 |
| Limitations，第1–3段 | 方法论文通常在Discussion末尾集中写适用条件、未覆盖场景和解释边界 | 把样本重叠、两环境斜率、未覆盖的多效性情形、LD输入和外部方法实现限制集中写清，不再列“验证阶梯” |
| Conclusions | MAPtools和MRBIGR用一段话概括工具用途、证据和可解释边界 | 用一段话收束PlantMR能支持的分析以及不能替代的生物学证据 |

## 图表如何对应参考文章

| PlantMR图 | 参考文章中的相似图表 | 本稿的处理 |
| --- | --- | --- |
| Figure 1 workflow | Liu等文章的环境处理/分子分析顺序；MAPtools和MRBIGR的工作流图 | 用四个面板展示植物环境背景、SNP×环境网格、协方差模型和报告输出 |
| Figure 2 simulation calibration | metaGE的模拟结果图和性能表 | 用点估计、校准比例和方向性多效性散点展示结果，不再使用大块柱图 |
| Figure 3 LD stress | metaGE用于检验P值校准的诊断图 | 用ECDF、采样分布、覆盖率和标准误比值展示独立性错配的后果 |
| Figure 4 Arabidopsis case | Feng等文章的区域SMR/eQTL/LD图；Liu等文章的环境分层证据链 | 用区域关联轨道、LD热图、分环境森林图和环境斜率组成四面板案例图 |
| Figure 5 shared-input comparison | metaGE的竞争方法比较表和结果图 | 用目标定义的森林图和覆盖率矩阵比较方法；目标不同的输出不进入评分 |

因此，当前5张图不是单纯增加数量，而是分别承担工作流、模拟、诊断、真实数据和方法比较五个常见软件/方法论文功能。

## 仍然存在的投稿风险

Plant Methods软件标准通常希望用相关软件的直接比较证明显著推进。当前PlantMR已经有：

- 相关工具功能范围矩阵；
- 主模拟、LD错配压力测试和真实植物案例；
- 运行时间和内存基准；
- 明确的功能边界和失败边界。

现在已经在相同摘要统计输入、相同SNP、相同环境分层和相同协方差输入下，完成了summary-data MR-GxE的500次/场景比较。比较结果按各自的估计目标评分：恒定效应加方向性多效性场景评估MR-GxE的因果效应，环境效应异质性场景评估PlantMR的环境斜率，其他方法/场景组合只保留为诊断。

这项比较不是完整复现MR-GxE论文中的个体水平分析，也没有声称已经完成MR-GENIUS或MR-EILLS的公平实现。稿件因此可以写“shared-input comparator”和“method-specific calibration”，不能写“PlantMR优于现有工具”或“性能最好”。

稿件当前只把这一结果写成shared-input comparator和method-specific calibration；如果以后加入其他公开实现，也应沿用相同输入契约并分别报告不同估计量。

## 结论

当前稿件的叙事和章节已经按照Plant Methods软件文章的写法重构，不再是普通研究论文套用软件内容。文章现在具备正式软件方法稿的结构、图表、软件可用性、数据契约、验证和边界说明；公开仓库已发布为 https://github.com/Zhangzhishuai-HIT/PlantMR，共享输入的summary-data MR-GxE比较也已经完成。正式投稿前剩下的是作者信息、Zenodo/等效归档DOI，以及提交前再核对一次目标期刊的在线格式要求。
