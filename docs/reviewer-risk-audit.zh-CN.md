# PlantMR manuscript reviewer-risk audit

## 1. Novelty overclaim

审稿人可能问：环境交互MR和多数据集MR是否已经存在？

稿件应对：

- 不再使用“首次提出环境交互MR”；
- 标题改为“environment-aware effect heterogeneity”；
- 明确区分PlantMR的环境斜率模型、MR-GxE/MR-GENIUS的多效性校正目标和MR-EILLS的不变因果效应目标；
- 将贡献限定为植物数据契约、LD/环境协方差输入、完整SNP×环境网格和审计工作流。

状态：已修正。

## 2. 把环境斜率误写成MR-GxE

审稿人可能问：为什么你们的截距不等于MR-GxE的多效性截距？

稿件应对：

- 方法章节明确：PlantMR估计环境效应异质性，不用第一阶段交互强度识别no-relevance subgroup；
- 不把截距解释为水平多效性估计；
- README和论文均声明不能静默替代MR-GxE/MR-GENIUS。

状态：已修正。

## 3. 忽略LD导致假精度

审稿人可能问：局部SNP高度相关时，为什么仍使用普通IVW？

稿件应对：

- 主模型输入带符号LD矩阵；
- 记录协方差秩；
- 奇异协方差使用`rank(V)-rank(X)`计算Q自由度；
- 新增LD+环境相关压力测试：正确模型零假阳性0.044、覆盖0.956；独立性错配零假阳性0.126、覆盖0.874；
- Arabidopsis独立IVW只作为故意不推荐的比较。

状态：已完成。

## 4. 环境协方差不是已知量

审稿人可能问：为什么用FT10/FT16表型相关代替ratio-error covariance？

稿件应对：

- 主分析不假设环境协方差；
- 表型相关只作为敏感性代理；
- 报告中明确它不是已知ratio-error covariance；
- 不把敏感性结果作为独立确认。

状态：已完成，但正式生物学论文仍需真实样本协方差或独立样本。

## 5. Arabidopsis案例不是独立验证

审稿人可能问：表达和表型是否样本重叠？是否能称为外部验证？

稿件应对：

- 明确表达和FT10/FT16共享accessions；
- 不称为独立验证；
- 不声称AT1G11560是本研究新因果基因；
- 把案例定位为真实数据契约、LD处理和审计报告示例；
- 引用已有SMR/HEIDI论文作为外部背景，而不是把它算成PlantMR验证。

状态：已完成。

## 6. 局部OLS替代正式混合模型

审稿人可能问：为什么不复现公开论文的LMM/eQTL流程？

稿件应对：

- 结果中明确local OLS+PC1–PC5；
- 不写成 published LMM/SMR replication；
- 把正式LMM、样本重叠协方差和独立验证列为应用论文的后续Gate。

状态：已诚实处理；仍是软件论文的限制。

## 7. 方法比较不足

审稿人可能问：为什么没有正式重跑MR-GxE、MR-GENIUS、MR-EILLS？

稿件应对：

- 不声称这些方法已被公平重跑；
- 当前真实比较包括标准分层IVW、MR-Egger、随机IVW、LD-aware GxE和独立性错配；
- 论文明确这些外部方法是不同估计量，必须作为独立适配器实现后再做正式比较。

状态：方法稿可先送预审；公开投稿前最好补至少一个可复现等价 comparator。

## 8. 模拟覆盖面不足

已完成：

- null；
- causal G×E；
- directional pleiotropy；
- environment correlation；
- LD+environment correlation；
- covariance misspecification；
- rank-deficient LD。

仍建议：

- weak instruments；
- 2/4/8个环境数量敏感性；
- nonlinear environmental response；
- exposure–outcome sample overlap；
- LD panel misspecification；
- unequal sample sizes和缺失环境。

状态：LD压力已补，其他属于增强版Gate。

## 9. 多重检验和genome-wide claims

稿件应对：

- 当前Arabidopsis只做预先指定的单基因数据契约案例；
- 不做全基因组候选发现声明；
- 不把P值写成基因因果证据；
- 未来扩展到全基因组时必须预先固定Bonferroni/FDR、基因级聚合和独立验证。

状态：已通过当前稿件边界。

## 10. 软件发布不完整

Nature软件审查重点包括：源码、安装说明、demo、典型运行时间、开源许可、测试、输入输出和公共代码链接。

已完成：

- MIT License；
- `README.md`和中文说明；
- synthetic普通MR和GxE demo；
- 23 tests；
- runtime.tsv；
- simulation scripts和source data；
- v1.1.0 tag。

投稿前必须完成：

- 公共GitHub/GitLab仓库；
- Zenodo DOI；
- 独立干净环境复现；
- Docker构建或明确解释容器不可用；
- 最好邀请一名不熟悉项目的同事进行盲用测试。

## 最低安全投稿版本

如果投稿软件/方法论文，必须把摘要、标题、结果和讨论都保持在以下Claim Ceiling：

“PlantMR provides a reproducible plant summary-statistics MR contract and a covariance-aware environment-effect-heterogeneity workflow. It improves transparency of LD/environment dependence under tested simulation settings. It does not by itself establish a causal gene, correct horizontal pleiotropy, solve sample overlap or replace independent validation.”
