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

## 已应用到PlantMR稿件的变化

- 摘要改为Plant Methods要求的Background、Results、Conclusions结构，当前约242词，不含参考文献引用。
- 主文改为：Background → Implementation → Results → Discussion → Conclusions → Availability and requirements → List of abbreviations → Declarations → References。
- 在Implementation中加入PlantMR完整工作流图、输入契约、命令、工具变量筛选和协方差模型。
- 新增“Comparison with related tools”表，比较PlantMR、MRBIGR、MR-Base/TwoSampleMR、metaGE和MAPtools的任务范围、植物元数据、环境/LD处理和证据类型。
- 新增软件论文特有的Availability and requirements表，列出项目名、操作系统、编程语言、依赖、许可证和使用限制。
- 新增List of abbreviations和完整Declarations字段。
- Discussion中明确承认：当前是功能范围比较和受控校准，不是已经完成的外部MR软件头对头性能比较。
- 参考文献加入MAPtools，全文参考文献增至36条，全部正文引用编号均已覆盖，36个DOI均通过Crossref解析。
- 真实案例仍明确写成可复现数据契约演示，不写成AT1G11560因果验证。

## 仍然存在的投稿风险

Plant Methods软件标准通常希望用相关软件的直接比较证明显著推进。当前PlantMR已经有：

- 相关工具功能范围矩阵；
- 主模拟、LD错配压力测试和真实植物案例；
- 运行时间和内存基准；
- 明确的功能边界和失败边界。

但当前还没有在相同输入、相同工具变量、相同环境和相同评价指标下，正式执行MR-GxE、MR-GENIUS、MR-EILLS或其他外部MR实现的头对头比较。因此稿件中只能写“scope comparison”“controlled calibration”和“software contract demonstration”，不能写“优于现有工具”或“性能最好”。

如果要进一步提高Plant Methods接受概率，下一步最有价值的是：

1. 选一个可公开获得且估计量相近的外部方法，明确转换输入契约；
2. 在同一批模拟数据上比较点估计、覆盖率、假阳性率、功效和运行成本；
3. 把比较规则、失败案例和适用边界全部写入表格；
4. 不把不同目标的MR-GxE、MR-GENIUS、MR-EILLS和PlantMR硬凑成单一排行榜。

该缺口已经在正文Discussion和投稿Gate中明确标记，不能用文字包装替代真实比较。

## 结论

当前稿件的叙事和章节已经按照Plant Methods软件文章的写法重构，不再是普通研究论文套用软件内容。文章现在具备正式软件方法稿的结构、图表、软件可用性、数据契约、验证和边界说明；正式投稿前真正剩下的是作者信息、公开仓库/DOI、Office视觉排版确认，以及是否补做至少一个公平的外部方法头对头比较。
