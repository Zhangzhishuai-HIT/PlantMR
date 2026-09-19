# 期刊定位建议：PlantMR 1.1.0

更新时间：2026-09-18

## 结论

当前稿件可以进行“编辑预询”和投稿前沟通；完成公开代码仓库/DOI、干净环境复现和作者信息后，最推荐正式投稿 Plant Methods。

当前不建议直接投 Nature Methods、Communications Biology 或 PLOS Computational Biology。不是稿件完全不能投，而是现有稿件的算法创新、跨工具比较和独立生物学验证还没有达到这些期刊的安全线。

## 第一选择：Plant Methods

官网范围明确包括 Software articles，要求软件描述显著技术进步、对较广泛植物研究者有潜在价值，并且软件必须经过充分验证。[24]

适配度：高。

理由：

- 论文中心是植物/作物MR软件和方法学数据契约；
- 植物元数据、参考组装、环境、倍性和LD是核心而不是附属信息；
- 已有软件demo、测试、模拟、真实植物数据案例和MIT许可；
- 文章不依赖“发现一个新因果基因”才能成立；
- Plant Methods本身已有软件文章类型，且官网建议不确定时先做预投稿咨询。[24]

正式投稿前必须补：

1. GitHub/GitLab公开仓库；
2. Zenodo DOI；
3. 一封预投稿咨询，附标题、摘要、软件版本、模拟结果和真实案例限制；
4. 作者、基金、贡献和利益冲突信息；
5. 最好补一个不熟悉项目的外部用户安装记录。

建议投稿题目：

PlantMR: an auditable summary-statistics toolkit for plant and crop Mendelian randomization with environment-aware effect heterogeneity

## 第二选择：BMC Bioinformatics

BMC Bioinformatics明确接收novel computational algorithms/software，软件文章通常要求具有广泛应用价值、相对已有工具有显著进步，并且最好做直接比较；软件要能让审稿人测试。[25]

适配度：中高，但当前不如Plant Methods安全。

当前问题：

- 目前只完成普通MR、分层IVW、PlantMR环境斜率和对角/LD协方差比较；
- 尚未正式实现或重跑MR-GxE、MR-GENIUS、MR-EILLS等外部方法；
- 真实案例是数据契约示范，不是独立生物学验证；
- 需要公开仓库和审稿人匿名测试方式。

如果补齐两个正式外部比较器和公共DOI，可作为第二投递目标。

## 第三选择：GigaScience

GigaScience强调可复现性、可用性、实用性以及代码、数据和方法的FAIR共享，并支持将软件、工作流和数据作为研究对象一起归档。[26]

适配度：中高。

适合的改写方向：

- 把文章写成“plant MR reproducible research object”；
- 增加公开数据/代码/环境锁/结果归档；
- 把Arabidopsis案例、模拟、LD压力测试和完整输入输出作为一个可复现资源包；
- 重点突出可复用数据契约和工作流，而不是宣称新的MR理论。

当前缺口：公开DOI、FAIR目录、干净容器、外部复现者记录。

## 第四选择：Plant Communications

Plant Communications覆盖植物基础和应用研究，也接收重要技术进展和高实用性研究资源；MRBIGR就是相近方向的已发表植物工具。[29]

适配度：中等。

需要注意：

- 期刊更偏向有明确植物生物学意义的工具/资源；
- 当前Arabidopsis案例不能作为新因果发现；
- 若要投这里，最好增加一个正式植物生物学应用问题，并使用正式LMM/eQTL/GWAS摘要统计、独立验证或功能证据。

当前更适合先做预投稿咨询，而不是直接正式投稿。

## 第五选择：PLOS Computational Biology

PLOS Computational Biology的Software/Methods文章强调显著的新方法、广泛采用潜力、重要生物学或方法学洞见和实质性证据；代码需要在发表时公开，并且相关软件文章要求开放源代码。[27][28]

适配度：目前偏低，后续可提升。

当前主要不足：

- 环境斜率模型的理论创新幅度有限；
- 尚未完成与MR-GxE/MR-GENIUS/MR-EILLS的公平实现级比较；
- 真实案例没有独立验证；
- 还没有展示大规模全基因组运行和广泛用户场景。

## 暂不推荐：Bioinformatics

Bioinformatics强调能够显著推进计算分子生物学/基因组学的新算法和数据库。[30]

当前稿件的问题是：核心估计量是透明、合理但相对窄的GLS环境斜率模型；如果没有更强的算法理论、正式外部方法比较、规模化基准和更强生物学应用，直接投稿风险较高。

## 暂不推荐：Nature Methods

Nature Methods适合高概念创新、强验证和广泛改变实验/计算实践的方法。当前稿件已经有较好的可复现框架，但还缺：

- 更强的概念性算法突破；
- 多个独立植物应用；
- 与现有方法的系统级比较；
- 独立用户和独立验证证据。

当前不建议把它作为首投期刊。

## 暂不推荐：Communications Biology

Communications Biology要求研究对特定生物学领域有明确的新生物学洞见，并且结论证据强、数据技术上可靠。[31]

当前稿件刻意不声称AT1G11560新因果发现，因此更像软件/方法稿，不是该刊最自然的稿型。

## 推荐投稿顺序

1. 先向 Plant Methods 做预投稿咨询；
2. 完成GitHub/GitLab + Zenodo DOI + 干净环境复现；
3. 若编辑认为方法学范围合适，正式投 Plant Methods；
4. 若希望提高计算方法定位，补MR-GxE/MR-GENIUS/MR-EILLS正式比较后投 BMC Bioinformatics；
5. 若完成FAIR研究对象和容器化，再考虑 GigaScience；
6. 只有在补齐独立植物应用和正式统计验证后，再考虑 Plant Communications 或更高门槛期刊。
