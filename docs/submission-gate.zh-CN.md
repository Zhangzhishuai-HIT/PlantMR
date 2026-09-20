# 投稿Gate：PlantMR 1.1.0

更新时间：2026-09-19

## 当前可交付层级

当前仓库已经达到：

- 可安装、可测试的植物/作物摘要MR软件版本；
- 有明确统计估计量、环境/LD协方差输入和限制；
- 有500次/场景模拟、PNG/PDF图和机器结果；
- 有5张论文图、9张编号表和36篇可核验科学参考文献；
- 有一个真实Arabidopsis数据契约案例和公开来源回执；
- 有完整英文投稿稿 `docs/PlantMR_submission_manuscript.docx` 和同步Markdown稿 `docs/manuscript-draft.en.md`；
- 有公开仓库 `https://github.com/Zhangzhishuai-HIT/PlantMR`；
- 有包含代码、测试、环境、图表和稿件的 `release/PlantMR_v1.1.0-paper_source.zip`。

当前已经达到“完整软件/方法论文稿 + 可复现实验包 + 合作者预审”层级，可以开展Plant Methods预投稿咨询；仍不能把它写成“已证明植物基因因果”的应用论文。

## 已通过Gate

### 软件

- [x] v1.1.0版本号、CHANGELOG、Python包入口同步；
- [x] 26个自动化测试通过；
- [x] `compileall`通过；
- [x] 普通MR、环境分层MR、GxE CLI均真实执行；
- [x] JSON/TSV/Markdown输出；
- [x] GxE完整SNP×环境网格检查；
- [x] 环境相关矩阵和LD相关矩阵校验；
- [x] 失败边界（方向性多效性、缺失环境、协方差缺失）写入报告。

### 方法学

- [x] 估计量和方差公式写入 `docs/methods/environment-aware-mr.md`；
- [x] MR-GxE、MR-EILLS、MRBIGR列入比较范围；
- [x] 不再声称环境交互MR理论首创；
- [x] 零模型、真实G×E、方向性多效性场景各500次；
- [x] 额外LD+环境相关压力测试各500次，比较正确协方差与独立性错配；
- [x] 报告偏差、RMSE、覆盖率、拒绝率和Q检验；
- [x] 模拟真值与真实植物数据分目录保存。

### 真实数据

- [x] Arabidopsis FT10/FT16 AraPheno值表；
- [x] GSE80744归一化表达矩阵；
- [x] 1001 Genomes局部基因型和PC；
- [x] 真实REF/ALT映射；
- [x] 48个标准QC工具和LD矩阵；
- [x] LD-aware主分析和环境相关代理敏感性分析；
- [x] 独立分层IVW作为比较；
- [x] 结果和限制写入 `docs/real-case-arabidopsis.zh-CN.md`。

### 投稿稿件

- [x] Structured abstract（Background/Results/Conclusions）、Background、Implementation、Results、Discussion、Conclusions、Availability、List of abbreviations和Declarations齐全；
- [x] Discussion扩展为主要发现、方法比较、协方差意义、植物应用和适用限制；
- [x] 所有正文引用编号均能对应37条参考文献；
- [x] 37个DOI全部通过Crossref解析；
- [x] DOCX结构、5张嵌入图、13个表格和源码归档通过机器检查；
- [x] 旧的错误DOI `10.1093/ije/dyx233` 和 `10.1038/s41467-018-03940-5` 已删除。

## 投稿前仍不能伪造的事项

### 红色：如果目标是生物学因果论文，必须补

1. Arabidopsis案例的表达—表型样本重叠协方差；
2. 用正式混合模型而不是局部OLS重建eQTL/GWAS摘要统计；
3. 独立群体或独立环境的验证；
4. 共定位/HEIDI或精细定位，以及至少一项功能证据；
5. 对方向性水平多效性、弱工具、群体结构和样本重叠做更多正式模拟；
6. 目前已完成summary-data MR-GxE共享输入比较；若要扩展到MR-GENIUS或MR-EILLS，仍需分别实现并验证；
7. 对所有候选基因进行预先固定的多重检验规则。

### 黄色：如果目标是软件/方法论文，投稿前必须补

1. 在独立干净环境重新执行测试；
2. 构建Docker镜像并保存构建日志；当前主机没有Docker/Podman，因此未完成；
3. 已完成公开GitHub仓库；仍需取得Zenodo或等效归档DOI；
4. 已用LibreOffice将Word稿渲染为16页PDF并逐页检查；提交前仍需按目标期刊在线系统要求复核格式；
5. summary-data MR-GxE共享输入比较已完成；弱工具、不同环境数量和更复杂多效性仍建议作为后续模拟。

## 投稿定位建议

最稳妥的第一投稿定位是：

“Plant/crop summary-statistics MR software and covariance-aware environment-interaction workflow”，主证据为模拟校准、LD/环境协方差审计和真实Arabidopsis数据契约案例；Arabidopsis结果只作为应用示范，不写成AT1G11560的新因果发现。

不建议当前投稿为：

- “AT1G11560已被PlantMR证明为因果基因”；
- “PlantMR首次提出环境交互MR”；
- “玉米干旱97个候选基因是本研究的新发现”。
