# 玉米干旱多环境MR数据审计

更新时间：2026-09-18

## 已确认

论文：Mapping regulatory variants controlling gene expression in drought response and tolerance in maize。

主研究设计：

- 224个玉米自交系；
- WW、WS1、WS2三个水分条件；
- 627个高质量RNA-seq样本；
- B73 RefGen_v4；
- 约1,288,889个SNP用于eQTL；
- 约30,000个表达性状；
- 73,573个eQTL；
- 原研究报告使用MR优先筛选97个候选基因。

公开数据回执：

- NCBI BioProject：PRJNA637522；
- NCBI项目页显示685个SRA实验、约1,613 Gbases、约0.75 TB原始序列；
- GSA：CRA000334、CRA002002；
- Genome Variation Map：GVM000048；
- 论文称RNA-seq reads、FPKM表达数据和变异数据均已提交；
- 论文称MR脚本已公开。

GSA CRA002002页面目前可直接确认：

- 标题：Unraveling Regulatory Variants Controlling Gene Expression in Drought Response in Maize；
- Release date：2020-08-15；
- 1,779个文件；
- 总大小约812.06 GB；
- 样本别名明确包含WW、WS1、WS2以及S/P文库类型；
- 原始文件提供HTTPS和FTP地址。

## 当前尚未通过的Gate

以下内容不能仅凭论文摘要或项目页视为已完成：

1. 处理后的表达矩阵是否能直接下载并保留样本ID—环境一一对应；
2. 224个自交系的最终基因型、等位基因方向和B73 RefGen_v4坐标是否能直接复用；
3. 每个环境的eQTL beta/SE/P值是否有公开的完整摘要统计文件；
4. 干旱表型/结局GWAS是否与同一批样本、同一环境和同一基因组版本一致；
5. 原研究MR脚本与补充表能否逐项重现97个候选基因；
6. 是否有独立的玉米群体或独立环境可以作为验证集。

## 不下载全部原始reads的原因

PRJNA637522约0.75 TB，CRA002002本身约812 GB。方法学第一阶段不应先下载全部原始reads，而应优先获取：

1. 样本元数据和环境映射；
2. 处理后的FPKM/表达矩阵；
3. 变异VCF/剂量矩阵；
4. 原研究eQTL和MR摘要统计；
5. 干旱表型和结局GWAS摘要统计；
6. 原研究代码和补充表。

只有在这些文件无法恢复、必须从原始reads重建时，才启动大规模原始数据下载和CPU重算。

## 下一道数据Gate

必须形成一份机器清单，至少包含：

- `sample_id`
- `accession`
- `genotype_id`
- `environment`
- `tissue`
- `development_stage`
- `library_type`
- `expression_file`
- `genotype_file`
- `phenotype_file`
- `source_url`
- `source_accession`
- `sha256`
- `status`

只有在eQTL—GWAS—环境—样本ID全部闭合后，才进入PlantGxE-MR方法开发。若摘要统计无法恢复，则研究路线切换为从处理矩阵重建；若处理矩阵也无法恢复，才评估原始reads重建的CPU时间、存储和可复现性。

## References

- Paper/PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC7336464
- NCBI BioProject: https://www.ncbi.nlm.nih.gov/bioproject/PRJNA637522
- GSA CRA002002: https://ngdc.cncb.ac.cn/gsa/browse/CRA002002
- GSA CRA000334: https://ngdc.cncb.ac.cn/gsa/browse/CRA000334
- GVM: https://ngdc.cncb.ac.cn/gvm
