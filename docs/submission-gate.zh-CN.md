# 投稿Gate：PlantMR 1.1.0

更新时间：2026-09-18

## 当前可交付层级

当前仓库已经达到：

- 可安装、可测试的植物/作物摘要MR软件版本；
- 有明确统计估计量、环境/LD协方差输入和限制；
- 有500次/场景模拟、PNG/PDF图和机器结果；
- 有一个真实Arabidopsis数据契约案例和公开来源回执；
- 有英文论文初稿 `docs/manuscript-draft.en.md`。

这足以作为“软件/方法论文初稿 + 可复现实验包”送合作者或内部预审，不足以支持不加限定的“已证明植物基因因果”应用论文。

## 已通过Gate

### 软件

- [x] v1.1.0版本号、CHANGELOG、Python包入口同步；
- [x] 23个自动化测试通过；
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

## 投稿前仍不能伪造的事项

### 红色：如果目标是生物学因果论文，必须补

1. Arabidopsis案例的表达—表型样本重叠协方差；
2. 用正式混合模型而不是局部OLS重建eQTL/GWAS摘要统计；
3. 独立群体或独立环境的验证；
4. 共定位/HEIDI或精细定位，以及至少一项功能证据；
5. 对方向性水平多效性、弱工具、群体结构和样本重叠做更多正式模拟；
6. 与MR-GxE、MR-GENIUS、MR-EILLS或其可复现等价实现进行公平的统计比较；
7. 对所有候选基因进行预先固定的多重检验规则。

### 黄色：如果目标是软件/方法论文，投稿前必须补

1. 在独立干净环境重新执行测试；
2. 构建Docker镜像并保存构建日志；当前主机没有Docker/Podman，因此未完成；
3. 将本地仓库镜像到公开GitHub/GitLab并取得Zenodo DOI；当前没有配置远程仓库；
4. 完成STROBE-MR逐项核对；
5. 将GxE模拟扩展到弱工具、LD错配和不同环境数量；当前已完成LD错配，弱工具和环境数量敏感性仍建议补。

## 投稿定位建议

最稳妥的第一投稿定位是：

“Plant/crop summary-statistics MR software and covariance-aware environment-interaction workflow”，主证据为模拟校准、LD/环境协方差审计和真实Arabidopsis数据契约案例；Arabidopsis结果只作为应用示范，不写成AT1G11560的新因果发现。

不建议当前投稿为：

- “AT1G11560已被PlantMR证明为因果基因”；
- “PlantMR首次提出环境交互MR”；
- “玉米干旱97个候选基因是本研究的新发现”。
