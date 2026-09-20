# PlantMR v1.1.0

PlantMR是一个用植物和作物GWAS/QTL摘要数据做孟德尔随机化（MR）的Python工具。它把物种、参考组装、组织、发育阶段、环境和LD参考面板等信息同分析结果一起保存，便于之后复查输入和假设。

这一版主要提供三种分析：

- 普通摘要数据MR；
- 按环境分别估计MR结果；
- 在完整SNP×环境数据上，用协方差感知的GLS模型估计总体效应和环境斜率。

第三种分析回答的是“MR效应是否沿着预先指定的环境分数发生变化”。它不是MR-GxE、MR-GENIUS或MR-EILLS的替代实现，也不会仅凭一个MR结果确认某个基因为因果基因。

项目地址：

https://github.com/Zhangzhishuai-HIT/PlantMR

## PlantMR 2.x：无图形界面的平台版

`platform-v2`开发分支正在把PlantMR重新做成一个实用的命令行/Python API植物因果多组学平台，不提供GUI。当前已经有统一项目目录和输入契约、普通摘要MR、透明GWAS/QTL基线、SMR/HEIDI、GO富集和因果边网络汇总。

这些模块会明确写出限制：当前GWAS不是混合线性模型，QTL不是完整的LD-aware模型，SMR/HEIDI不是共定位证明，网络模块也不会把输入边自动包装成已证实因果关系。

使用顺序是`plantmr2 init`、`inspect`、`validate`、`run`。完整的中文命令和数据契约见：

`docs/PlantMR2-CLI使用与数据契约.zh-CN.md`

论文版v1.1.0仍保留在`main`，v2开发不会覆盖已经发布的论文和稳定版代码。

## 已实现的功能

- 摘要统计和植物元数据检查；
- effect allele / other allele协调，包括反向链处理和回文位点检查；
- P值、MAF、F统计量和非有限值检查；
- 可选的带符号LD clumping；
- Wald ratio、固定效应IVW、随机效应IVW和MR-Egger；
- Cochran Q、MR-Egger截距和留一分析；
- 按环境分层估计；
- 完整SNP×环境网格上的协方差感知GLS；
- 显式的环境相关矩阵和LD相关矩阵；
- JSON、TSV和Markdown报告；
- 用于外部方法比较的summary-data MR-GxE comparator；
- 合成示例、真实数据记录和模拟脚本。

## 安装

需要Python 3.10或更高版本。

```bash
python -m pip install -e .
```

完整研究环境写在`environment.yml`中。核心包使用NumPy、pandas和SciPy；基准测试和绘图还需要statsmodels、matplotlib和psutil。

## 普通摘要MR

```bash
plantmr validate \
  --exposure examples/synthetic/exposure.tsv \
  --outcome examples/synthetic/outcome.tsv \
  --metadata examples/synthetic/metadata.json

plantmr run \
  --exposure examples/synthetic/exposure.tsv \
  --outcome examples/synthetic/outcome.tsv \
  --metadata examples/synthetic/metadata.json \
  --ld-matrix examples/synthetic/ld.tsv \
  --outdir examples/synthetic/result
```

LD矩阵是可选的。提供时，它应当是带符号LD相关系数方阵，第一列和表头都是SNP名称。不提供LD矩阵时，报告会明确说明没有用LD面板检查工具变量之间的独立性。

## 按环境分层MR

暴露表和结局表都需要有`environment`列，同一个SNP可以在不同环境各出现一次。

```bash
plantmr run-stratified \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --outdir stratified_result
```

输出包括`environment_results.tsv`、`results.json`和`report.md`。

## 协方差感知的环境效应分析

暴露表和结局表都要有`environment`列，暴露表还要为每个环境提供唯一的数值`environment_value`。同一个SNP必须出现在所有环境中，并且在所有环境都通过工具变量筛选。

```bash
plantmr run-gxe \
  --exposure examples/synthetic/environment_exposure.tsv \
  --outcome examples/synthetic/environment_outcome.tsv \
  --metadata examples/synthetic/environment_metadata.json \
  --environment-correlation environment_corr.tsv \
  --ld-correlation ld_corr.tsv \
  --outdir gxe_result
```

对每个SNP×环境单元，PlantMR先计算`beta_outcome / beta_exposure`，再用`[1, environment_value]`做两列GLS模型。截距表示`environment_value = 0`时的估计效应，斜率表示环境分数每增加一个单位时效应改变多少。

环境相关矩阵和LD相关矩阵必须是带符号的相关系数方阵。不提供时，工具使用对角近似，并在报告中写明。这个模型估计的是环境效应异质性，不能把截距解释成水平多效性校正项。

## 外部方法比较

`scripts/run_mr_gxe_head_to_head.py`实现了一个summary-data MR-GxE比较器，按照Spiller等人提出的三步score regression思路工作。它与PlantMR使用完全相同的模拟摘要数据。两个方法估计的量不同，所以脚本只在各自估计目标有定义的场景下计算偏差和覆盖率；其他输出会保留下来，但只作为诊断，不放进一个简单的总排行榜。

结果和图在：

- `results/benchmarks/mr_gxe_head_to_head/`
- `docs/figures/mr_gxe_head_to_head.png`
- `docs/figures/mr_gxe_head_to_head.pdf`

## 输入列

普通MR的必需列：

`SNP`, `effect_allele`, `other_allele`, `beta`, `se`, `pval`

建议列：

`eaf`, `n`

植物元数据至少应说明：

`species`, `assembly`, `trait`, `tissue`, `stage`, `environment`, `ploidy`, `ld_panel`

## 如何理解结果

- 输出的是在工具变量假设下的MR证据，不是自动确认的“因果基因”；
- MR-Egger和随机效应IVW不能消除所有水平多效性；
- 按环境分层的结果是条件性估计，不等同于完整的结构化G×E因果模型；
- SMR/HEIDI、GSMR、共定位、精细定位、MVMR、MR-PRESSO以及多倍体或泛基因组SV模型不会被命令静默替代；
- 真实研究仍需要匹配的LD数据、独立重复和功能证据。

更详细的说明见：

- `docs/methods/estimands.md`
- `docs/methods/assumptions.md`
- `docs/methods/environment-aware-mr.md`
- `docs/real-case-arabidopsis.zh-CN.md`
- `docs/mr-gxe-head-to-head.zh-CN.md`
- `docs/similar-article-writing-audit.zh-CN.md`
- `docs/PlantMR_submission_manuscript.docx`
- `docs/PlantMR_submission_manuscript.pdf`
- `docs/PlantMR_submission_manuscript.zh-CN.docx`
- `docs/PlantMR_submission_manuscript.zh-CN.pdf`
- `docs/manuscript-draft.zh-CN.md`
- `docs/PlantMR-MRBIGR目标与超越路线.zh-CN.md`
- `docs/PlantMR2-CLI使用与数据契约.zh-CN.md`

## 许可证

MIT License，见`LICENSE`。
