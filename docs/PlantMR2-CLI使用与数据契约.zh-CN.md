# PlantMR 2.x CLI使用与数据契约

## 当前状态

PlantMR 2.x正在独立开发分支`platform-v2`上实现。主分支中的v1.1.0论文版不被覆盖，也不把当前开发版包装成已经完成的MRBIGR替代品。

PlantMR 2.x不提供图形界面。用户通过一个项目目录、一个`plantmr.toml`和`plantmr2`命令完成分析。所有分析都写入独立的run目录，保留输入路径、分析参数、检查结果和Markdown/JSON/TSV产物。

## 快速开始

```bash
python -m pip install -e .

plantmr2 init maize-demo \
  --species Zea_mays \
  --assembly RefGen_v5 \
  --outdir maize-demo

# 编辑 maize-demo/plantmr.toml，并把文件放到 maize-demo/data/
plantmr2 inspect maize-demo/plantmr.toml --json
plantmr2 validate maize-demo/plantmr.toml --json
```

`init`只创建目录和模板，不会猜测文件位置，也不会启动分析。`inspect`只检查manifest和路径；`validate`才检查当前分析所需的文件、列名、数值范围和重复标识符。

## 项目文件

```text
maize-demo/
├── plantmr.toml
├── README.md
├── data/
├── runs/
├── reports/
└── logs/
```

一个最小普通MR项目：

```toml
project_name = "maize-demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["ordinary-mr"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"

[metadata]
tissue = "leaf"
stage = "V6"
environment = "field"
ploidy = "2"
ld_panel = "data/ld.tsv"
```

路径相对于`plantmr.toml`解析。run目录不能覆盖已有目录；重复run必须显式换`--run-id`。

## 支持的分析命令

### 普通摘要统计MR

```bash
plantmr2 run plantmr.toml \
  --analysis ordinary-mr \
  --run-id mr-001 \
  --json
```

输出包括：

- `harmonized.tsv`：等位基因协调后的工具变量；
- `selected_instruments.tsv`：经过P值、F统计量和MAF检查的工具变量；
- `leave_one_out.tsv`：工具变量足够时的留一分析；
- `results.json`：方法结果和参数；
- `report.md`：可直接阅读的报告；
- `run_manifest.json`：本次运行的项目、验证、参数和产物清单。

### 基线GWAS

基因型使用long格式，表型也使用long格式：

```bash
plantmr2 run plantmr.toml \
  --analysis gwas \
  --trait height \
  --run-id gwas-height \
  --json
```

当前GWAS是透明的逐变异普通最小二乘模型，不包含PCA、亲缘关系、群体结构、协变量或混合线性模型。它是可复查的基线和QTL输入生产器，不应直接替代正式植物GWAS软件。

### eQTL、mQTL和pQTL基线

表达、代谢物和蛋白使用同一个long格式：

```bash
plantmr2 run plantmr.toml \
  --analysis qtl \
  --feature-role expression \
  --feature-id ZmGene0001 \
  --run-id eqtl-gene0001 \
  --json
```

`--feature-role`可选`expression`、`metabolite`或`protein`。QTL和GWAS使用同样的效应、标准误、P值和样本交集定义，便于后续接入因果分析。

### SMR/HEIDI

exposure摘要统计需要增加`feature_id`列：

```bash
plantmr2 run plantmr.toml \
  --analysis smr \
  --run-id smr-001 \
  --json
```

SMR对每个分子特征选择最强暴露QTL；HEIDI对共享SNP的比值效应做异质性诊断。当前实现假设暴露和结局效应等位基因方向已经可以按SNP协调，未建模LD结构和样本重叠协方差；HEIDI不是共定位证明。

### GO富集

```bash
plantmr2 run plantmr.toml \
  --analysis go \
  --run-id go-001 \
  --json
```

需要`inputs.go_annotation`和`inputs.selected_features`。默认背景集合是GO注释文件中出现的所有特征。如果实际实验只测了其中一部分，应通过Python API显式传入测试背景集合，而不能直接接受默认背景。

### 因果边网络汇总

```bash
plantmr2 run plantmr.toml \
  --analysis network \
  --network-p-threshold 0.05 \
  --run-id network-001 \
  --json
```

`network`读取已经由MR、SMR或其他方法产生的边，不从边表反推因果性。它计算边的BH校正P值、节点数和显著边中的循环，并在报告中明确“edge summary, not causal proof”。

## 输入契约

### 摘要统计

`exposure`和`outcome`至少需要：

```text
SNP  effect_allele  other_allele  beta  se  pval
```

建议同时提供`eaf`和`n`。普通MR的工具变量筛选需要暴露侧的`eaf`；缺少它时，位点会在MAF筛选中被排除，而不是静默填成合理值。

### 基因型

```text
sample_id  variant_id  dosage
```

`dosage`默认按二倍体解释，范围为0到2；在`metadata.ploidy`中可指定其他倍性。每个`sample_id`/`variant_id`组合必须唯一。

### 表型

```text
sample_id  trait  value
```

同一trait中每个sample只能有一行。多性状文件通过`trait`区分，GWAS多性状运行时必须显式使用`--trait`。

### 表达、代谢物和蛋白

```text
sample_id  feature_id  value
```

同一sample和feature只能有一行。该格式可用于QTL，也可作为后续多组学模块的统一输入。

### GO注释和特征列表

```text
# go_annotation.tsv
feature_id  go_term  term_name

# selected_features.tsv
feature_id
```

### 因果边

```text
source  target  beta  se  pval
```

`network`不会替边表补充方向、共定位或干预证据。

## 设计原则

- 先`inspect`，再`validate`，最后`run`；检查命令不启动分析；
- 路径相对于manifest，结果相对于run目录；
- JSON输出用于脚本和流水线，Markdown用于人工阅读，TSV用于下游分析；
- 已声明但格式错误的输入会阻塞运行；未声明的可选输入只产生提示；
- 每个run独立保存，不覆盖历史结果；
- 统计模型、输入假设和限制写入报告，不把简单OLS称为混合模型，也不把关联网络称为已证实因果网络。

## Python API

```python
from plant_mr.platform import (
    ProjectManifest,
    run_gwas,
    run_qtl,
    run_smr_heidi,
    go_enrichment,
    summarize_causal_network,
)
```

当前API和CLI共享数据契约。后续增加协变量、LD、环境协方差、多倍体和结构变异模块时，仍沿用同一项目manifest和run记录，而不是再建立一套互不兼容的输入格式。

## 当前边界

已经实现的是可运行的CLI平台骨架、项目契约、输入检查、普通MR、GWAS基线、QTL基线、SMR/HEIDI、GO富集和网络汇总。正式的群体结构校正GWAS、完整LD-aware多组学MR、共定位/精细定位、MVMR、环境特异QTL、多倍体和泛基因组SV仍需独立实现和验证，不能因为命令名已经存在就宣称这些能力已经完成。
