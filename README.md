# PlantMR

PlantMR 是一个面向植物和作物遗传数据的因果组学工具。当前开发中的 v0.1 提供本地命令行工作流：

- 植物摘要统计输入规范与元数据；
- 暴露/结局等位基因协调；
- 工具变量P值、MAF和F统计量质控；
- Wald ratio、固定/随机效应IVW、MR-Egger和异质性Q检验；
- 逐工具变量留一分析；
- JSON、TSV和Markdown可复现报告。

当前版本是可运行的基础版，不把普通MR结果直接命名为“因果基因”。环境感知MR、SMR/GSMR适配器、多倍体、PAV/SV和泛基因组支持列在 `PLAN.md` 中，尚未伪装成已完成功能。

## 安装

```bash
python -m pip install -e .
```

Python要求 >= 3.10。

## 最小示例

```bash
plantmr validate \
  --exposure examples/synthetic/exposure.tsv \
  --outcome examples/synthetic/outcome.tsv \
  --metadata examples/synthetic/metadata.json

plantmr run \
  --exposure examples/synthetic/exposure.tsv \
  --outcome examples/synthetic/outcome.tsv \
  --metadata examples/synthetic/metadata.json \
  --outdir examples/synthetic/result
```

输出：

- `harmonized.tsv`：等位基因协调后、通过工具变量筛选的数据；
- `leave_one_out.tsv`：至少保留两个工具变量时的逐工具变量留一结果；
- `results.json`：机器可读结果、参数、审计计数和警告；
- `report.md`：中文/英文混合的简洁结果报告。

## 输入列

必需列：

`SNP`, `effect_allele`, `other_allele`, `beta`, `se`, `pval`

可选列：

`eaf`, `n`, `trait`, `species`, `assembly`, `tissue`, `stage`, `environment`, `ploidy`

`metadata.json` 用于声明物种、参考组装、组织、发育时期、环境、倍性和LD参考面板。例如：

```json
{
  "species": "Zea mays",
  "assembly": "Zm-B73-REFERENCE-NAM-5.0",
  "environment": "WW",
  "tissue": "kernel",
  "stage": "15_DAP",
  "ploidy": 2,
  "ld_panel": "not_supplied_in_synthetic_example"
}
```

## 科学边界

v0.1要求用户确认输入已经按研究设计完成GWAS并处理了相关性问题。没有LD参考面板时，PlantMR会显式警告，不会假装完成LD独立性验证。MR结果是遗传工具变量条件下的因果证据，不等于已经完成基因编辑或转基因验证。

详细研究路线、验收门和后续环境感知MR设计见 `PLAN.md`。
