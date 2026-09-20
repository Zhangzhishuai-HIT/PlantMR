PlantMR：面向植物和作物、具有环境效应异质性感知能力的可审计摘要统计孟德尔随机化工具包

[作者姓名、单位和通讯作者信息待补]

中文阅读稿｜PlantMR v1.1.0-paper｜2026年9月19日

| 稿件说明 本文件是英文投稿手稿的完整中文翻译，科学内容、分析、源数据、模拟和软件版本与英文稿一致。作者信息、公开归档DOI和最终期刊格式仍需在投稿前补充。 |
| --- |

# 摘要

## 背景

植物孟德尔随机化（Mendelian randomization，MR）可以把分子性状与农艺表型联系起来，但植物参考基因组组装、环境分层、连锁不平衡（linkage disequilibrium，LD）和样本重叠信息常常没有被明确记录。我们开发了PlantMR 1.1，这是一个本地运行、开源、可审计的植物和作物摘要统计MR工具，同时提供范围明确的环境效应异质性分析。

## 结果

PlantMR能够检查植物元数据和摘要统计量、协调等位基因、强制建立完整的SNP×环境工具变量网格、接收带符号的SNP-LD矩阵和环境相关矩阵，并报告考虑矩阵秩的异质性诊断。在每个场景500次重复的模拟中，考虑协方差的估计器在零假设下的拒绝率为0.054，95%覆盖率为0.946；当真实环境斜率为0.25时，平均估计值为0.2498，偏差为−0.00018，覆盖率为0.952，功效为1.00。在AR(1) LD相关系数ρ=0.6的LD压力测试中，正确建模协方差时拒绝率为0.044、覆盖率为0.956，而将观测当作独立时分别为0.126和0.874。真实Arabidopsis数据契约案例针对AT1G11560和10°C、16°C开花时间，最终保留了48个存在LD相关的工具变量。主要分析的环境斜率为−0.0371（SE 0.1562，P=0.812），残余异质性为Q=192.89，df=60，P=7.33×10−16。

## 结论

PlantMR提供了一个面向植物的可复现实现和审计工作流。在本研究测试的场景下，模拟结果支持考虑协方差的校准方式；但Arabidopsis案例只是软件演示，并不是独立的因果验证。PlantMR不能替代共定位、正式的交互MR方法、混合模型GWAS或功能验证。

关键词：孟德尔随机化；植物基因组学；作物基因组学；基因型—环境互作；表达数量性状位点；连锁不平衡；摘要统计量；可复现性

# 背景

孟德尔随机化使用与暴露相关的遗传变异作为工具变量，估计遗传代理暴露对结局的影响。[1,2] 工具变量的相关性、可交换性和排除限制假设是解释结果的基础，但这些假设能否成立，取决于研究群体、表型、分子暴露以及数据生成过程。摘要统计MR可以借助公开的全基因组关联研究（genome-wide association study，GWAS）和MR-Base等平台开展大规模分析，[10] 但摘要关联同样容易受到弱工具变量、水平多效性、LD和样本重叠的影响。[3–9]

植物研究还带来一些额外问题。自然群体和育种群体可能具有明显的地理结构和亲缘关系。不同物种、群体和基因组区域的LD衰减速度可能差别很大。基因表达强烈依赖组织、发育阶段和处理条件。多环境试验和胁迫实验经常在多个条件下重复测量相同基因型，因此得到的是相关估计，而不是相互独立的GWAS数据集。多倍体剂量、存在/缺失变异和结构变异还需要不同的数据表示，不能在没有说明的情况下全部转换成普通的双等位基因SNP；近期的Arabidopsis泛基因组研究说明，局部适应和非参考序列变异应当保持明确记录。[35]

已有植物软件说明了整合式工作流的价值。MRBIGR提供了面向玉米的大规模多组学、GWAS和MR工具箱。[17] 本研究所参考的玉米干旱研究利用动态eQTL和先导eQTL MR工作流对候选基因进行了优先排序。[18] 植物基因型—环境互作GWAS和多环境荟萃分析方法也表明，环境对比、群体结构和交互项需要联合建模，不能只把环境当作标签处理。[25–27] 在植物研究之外，MR-GxE利用基因—协变量交互来检测或校正恒定多效性假设下的多效性偏倚，[14] 而基于交互的MR研究则区分了MR-GxE和MR-GENIUS，并强调交互强度及模型假设的敏感性。[15] MR-EILLS针对异质GWAS摘要数据中的不变因果效应，并评估了多种MR和荟萃分析比较方法。[16] 这些方法的估计目标不同，不能混为一谈。

本文将PlantMR开发为一个面向植物和作物的摘要统计软件及报告工作流。其贡献有意区别于一般交互MR理论：第一，建立明确的植物元数据和摘要统计数据契约；第二，选择完整的SNP×环境工具变量网格；第三，接收带符号的LD和环境相关性输入；第四，报告考虑矩阵秩的异质性诊断；第五，通过模拟和真实Arabidopsis数据契约案例提供可复现的本地实现。我们评估的是校准、LD错配风险和适用边界，而不是声称发现了新的因果基因。

# 实现

## 研究问题和工作流

我们预先设定了四个问题：（1）软件能否执行面向植物、可审计的数据契约；（2）在SNP误差和环境误差相关的情况下，考虑协方差的环境斜率估计器能否恢复已知效应；（3）当LD和环境依赖性被错误地当作独立时，推断会恶化到什么程度；（4）同一套审计记录能否在真实植物数据契约上运行，同时避免把演示结果写成因果基因结论？图1将这些问题分成输入来源记录、协调、工具变量筛选、协方差设定、估计和报告几个阶段。

![图1](figures/plantmr_workflow.png)

图1。PlantMR工作流示意图。植物材料背景和重复环境测量进入共同的SNP×环境网格，再进入考虑协方差的估计，并分别输出统计结果和可追溯的复现材料。

## PlantMR软件契约和分析工作流

PlantMR接收包含SNP、效应等位基因、另一等位基因、beta、标准误和P值的暴露表和结局表。可选字段包括效应等位基因频率和样本量。植物元数据记录物种、参考基因组组装、性状、组织、发育阶段、环境、多倍体信息和LD面板来源。软件会检查数值和等位基因，协调反向及互补等位基因，识别有歧义的回文变异，执行P值、MAF和F统计量筛选，并记录每一项排除。

表1。PlantMR的组成、范围和审计输出。

| 组成部分 | 功能 | 输出 |
| --- | --- | --- |
| 数据模式和元数据 | 检查摘要统计量和植物背景信息 | 检查信息和元数据JSON |
| 等位基因协调 | 对齐效应等位基因并处理回文变异 | 协调后的表格和排除数量 |
| 工具变量质量控制 | P值、MAF、F统计量和完整网格筛选 | 工具变量审计表和保留SNP表 |
| 标准MR | Wald比值、固定/随机效应IVW、MR-Egger、Q和留一法 | JSON、TSV和Markdown报告 |
| 环境斜率 | 对SNP×环境比值估计进行GLS | 汇总效应、斜率、协方差秩和Q |
| 可复现性 | 命令行接口、测试、模拟和源数据记录 | 带版本的报告和基准结果 |

命令行接口提供validate、run、run-stratified和run-gxe命令。软件不会在没有明确说明的情况下，用SMR、GSMR、共定位、MVMR、MR-PRESSO、MR-GxE、MR-GENIUS或MR-EILLS替代当前分析。

## 与相关工具的比较

按照近期Plant Methods软件论文的组织方式，我们在展示基准结果之前，先将PlantMR与功能相邻的工具进行比较。这是基于相关软件论文和公开文档的范围与数据契约比较，不是虚构的运行时间头对头实验。PlantMR的目标是把植物元数据、完整SNP×环境网格、带符号的LD/环境协方差和可审计的摘要统计输出组合在一起。

表2。与相关工具的功能定位比较。“不是主要关注点”表示某个工具可能支持相关分析，但没有暴露出与本文相同的数据契约或估计目标。

| 工具 | 主要范围 | 植物背景 | 环境/LD处理 | 本文使用的证据 |
| --- | --- | --- | --- | --- |
| PlantMR 1.1 | 植物摘要统计MR和环境效应异质性 | 原生记录物种、组装、组织、阶段、多倍体和LD来源 | 带符号LD和可选环境协方差；要求完整网格 | 模拟、LD压力测试和Arabidopsis案例 |
| MRBIGR [17] | 大规模多组学、GWAS和MR工具箱 | 玉米和水稻案例；广泛的多组学工作流 | MR/网络估计目标不同，不是本文的G×E协方差契约 | 文献范围比较 |
| MR-Base / TwoSampleMR [10] | 人类GWAS资源和双样本MR自动化 | 面向人类GWAS的公共资源生态 | 标准MR敏感性分析；植物元数据不是主要契约 | 文献范围比较 |
| metaGE [25] | 多环境GWAS荟萃分析 | 植物多环境试验和G×E QTL检测 | 在GWAS荟萃分析层面建模异质性和环境协变量 | 估计目标比较；未重新实现 |
| MAPtools [36] | mapping-by-sequencing和QTL-Seq命令行分析 | 在植物和多物种mapping工作流中测试 | 变异/QTL定位，不是摘要统计MR协方差 | 工作流/软件论文比较 |

## 环境效应异质性模型

对于SNP j和环境k，比值估计为r_jk = beta_y,jk / beta_x,jk。令z_k为预先指定的数值环境分数。PlantMR拟合r_jk = θ_0 + θ_1 z_k + ε_jk。θ_0表示z=0时的遗传代理效应，θ_1表示MR效应随环境分数每增加一个单位的变化量。这是一个效应异质性模型。它的截距不是MR-GxE中的多效性截距，也不被解释为水平多效性的校正项。

一阶Delta方差为v_jk = se_y,jk² / beta_x,jk² + beta_y,jk² se_x,jk² / beta_x,jk⁴。在以SNP为主、环境为次的排列方式下，可选的带符号SNP相关矩阵和环境相关矩阵定义V = D(R_SNP ⊗ R_ENV)D，其中D为比值标准误构成的对角矩阵。GLS估计量为theta_hat = (X′V⁻¹X)⁻¹X′V⁻¹r，其中X=[1,z]。如果V秩亏，残余异质性自由度为rank(V)−rank(X)。

该模型要求每个SNP都有完整的环境网格，并且只保留在每个环境中都满足暴露P值、F统计量和MAF要求的SNP。这样可以避免把工具变量组成的改变误认为环境斜率。缺少环境相关性并不被当作已确认的独立性；报告会明确说明使用了对角近似。

## 实现细节

本研究按软件/方法学评估组织。我们没有利用真实数据案例选择有利的估计器、定义新的基因层面结论或调节模拟真值。主要结论集中于输入检查、考虑协方差的估计和诊断透明度。

### 输入模式和等位基因协调

必需的摘要统计列为SNP、effect_allele、other_allele、beta、se和pval。可选列为eaf和n。数据模式会拒绝空的或重复的SNP标识符、非有限数值、非正标准误、无效P值、无效等位基因字符以及效应等位基因和另一等位基因相同的记录。协调程序能够识别对齐、反向、互补和反向互补等位基因，并利用等位基因频率只保留能够解析的回文变异。

### 工具变量选择

Arabidopsis案例的主要阈值为暴露P≤5×10−8、F≥10和MAF≥0.05。GxE选择器要求保留的每个SNP在每个环境中都通过这些筛选。这样可以避免环境特异的工具变量组成被误认为效应异质性。LD使用带符号的相关系数表示，而不是使用r²值。

### 估计器和诊断

标准方法包括Wald比值、固定效应IVW、随机效应IVW、MR-Egger、Cochran Q和留一法分析。环境斜率估计器使用上文所述的Delta法比值方差和GLS协方差。如果协方差矩阵奇异，则对二次型使用Moore–Penrose逆，并按矩阵秩调整Q的自由度。

### 模拟设计

所有模拟都使用固定随机种子，并记录在元数据JSON文件中。基础基准使用20个SNP和4个环境分数（−1.5、−0.5、0.5、1.5）。暴露效应被生成为正向且强的工具变量。结局效应由汇总效应、已知环境斜率和多元正态抽样误差生成。LD压力测试额外使用了rho=0.6的AR(1) LD相关矩阵。

### Arabidopsis数据处理

从GEO下载GSE80744标准化表达矩阵，并提取AT1G11560行。使用1001 Genomes HDF5矩阵提取局部区域；每隔1000个标记计算5个主成分。公共材料的VCF提供REF/ALT标签。根据材料ID合并AraPheno FT10和FT16数值。局部关联回归纳入基因型和PC1–PC5。案例中记录了源URL、哈希值、生成表格和限制条件。

### 统计报告

所有数值结果均报告效应估计、标准误、P值、工具变量数量、协方差来源和异质性诊断，遵循STROBE-MR的报告原则。[13] 单基因Arabidopsis演示不作全基因组多重检验结论。任何未来的全基因组分析都必须预先规定基因层面聚合方式、多重检验控制和独立验证集。

# 结果

## 模拟校准和LD压力测试

主要模拟基准使用20个工具变量、4个环境、环境相关性0.5、暴露标准误0.01、结局标准误0.04，以及每个场景500次重复。场景包括零斜率、真实斜率为0.25和共同方向性多效性。LD压力测试使用相同维度，并采用rho=0.6的AR(1)带符号LD相关矩阵，比较正确协方差设定与对角独立近似。

表3。主要模拟校准和LD压力测试汇总。图2和图3中的虚线在适用时表示名义拒绝率0.05和覆盖率0.95。

| 场景 | 协方差 | 均值/偏差 | 覆盖率 | 拒绝率或功效 |
| --- | --- | --- | --- | --- |
| Null | 环境感知 | 斜率偏差−0.00069 | 0.946 | 0.054 |
| Null | 对角 | 斜率偏差−0.00071 | 0.994 | 0.006 |
| Causal G×E | 环境感知 | 均值0.24982；偏差−0.00018 | 0.952 | 1.000 |
| Causal G×E | 对角 | 均值0.24832；偏差−0.00168 | 1.000 | 1.000 |
| LD压力测试零假设 | 正确LD+环境协方差 | 偏差0.00172 | 0.956 | 0.044 |
| LD压力测试零假设 | 错配对角模型 | 偏差0.00177 | 0.874 | 0.126 |
| LD压力测试因果场景 | 正确LD+环境协方差 | 偏差0.00136 | 0.970 | 1.000 |
| LD压力测试因果场景 | 错配对角模型 | 偏差0.00170 | 0.880 | 1.000 |

方向性多效性场景暴露出一个重要限制。当真实斜率为零时，环境斜率仍近似无偏，但合并截距偏高+0.216。因此，环境斜率稳定并不能证明合并的因果关系不受水平多效性影响。

![图2](figures/gxe_simulation.png)

图2。模拟校准。（a）各场景的平均斜率估计及模拟均值的95%置信区间，虚线段表示数据生成值；（b）拒绝比例；（c）95%覆盖率；（d）方向性多效性使截距发生偏移，而环境斜率仍接近其目标值。

![图3](figures/gxe_ld_stress.png)

图3。LD压力测试。（a）零假设P值的经验校准；（b）斜率抽样分布；（c）覆盖率；（d）相对标准误失真，均基于给定的LD和环境依赖结构。独立性近似使零假设拒绝率从0.044升至0.126，使覆盖率从0.956降至0.874。

## 共享输入的外部方法比较

我们根据Spiller等人提出的三步构造，实现了一个范围有限的摘要统计MR-GxE比较器。[14] 该比较器只使用每个环境中的暴露关联来建立一个固定加权的等位基因分数，然后计算分数—暴露和分数—结局关联，并带截距回归后者。两种方法使用相同的20个SNP、4个环境层、环境相关矩阵、标准误和每个场景500次重复。该比较是按方法各自的估计目标进行的，而不是制作一个总性能排行榜：PlantMR估计环境效应斜率，而摘要MR-GxE估计不变因果效应和恒定多效性截距。

表4。共享输入的PlantMR与摘要统计MR-GxE基准比较。只有当模拟数据生成模型定义了相应估计目标时，才报告偏差和覆盖率；目标不一致的输出保留为诊断。

| 场景 | 方法/目标 | 平均估计 | 偏差 | 覆盖率 | 拒绝率 | 解释 |
| --- | --- | --- | --- | --- | --- | --- |
| 零因果效应+多效性 | 摘要MR-GxE/因果效应 | −0.0021 | −0.0021 | 0.934 | 0.066 | 目标明确的因果校准 |
| 零因果效应+多效性 | PlantMR/环境斜率 | −0.0692 | — | — | — | 仅作诊断：多效性使斜率不再具有因果含义 |
| 恒定效应、无多效性 | PlantMR/环境斜率 | 0.0036 | 0.0036 | 0.938 | 0.062 | 目标明确的异质性校准 |
| 恒定效应、无多效性 | 摘要MR-GxE/因果效应 | 0.5003 | 0.0003 | 0.958 | 1.000 | 目标明确的因果校准 |
| 恒定效应+多效性 | 摘要MR-GxE/因果效应 | 0.4983 | −0.0017 | 0.938 | 1.000 | 在恒定多效性下恢复正确因果目标 |
| 恒定效应+多效性 | PlantMR/环境斜率 | −0.0653 | — | — | — | 仅作诊断：不是因果斜率 |
| 环境效应异质性 | PlantMR/环境斜率 | 0.2515 | 0.0015 | 0.942 | 1.000 | 正确的环境斜率目标 |
| 环境效应异质性 | 摘要MR-GxE/因果效应 | 1.2143 | — | — | — | 仅作诊断：不变效应目标在此场景未定义 |

这一比较支持的是互补性，而不是某个方法胜出。在恒定因果效应和方向性多效性场景下，摘要MR-GxE恢复了因果效应（均值0.4983，覆盖率0.938），而PlantMR环境斜率是由排除限制被违反所产生的诊断信号。在真实存在环境效应异质性且没有多效性的场景下，PlantMR恢复了环境斜率（均值0.2515，覆盖率0.942），而摘要MR-GxE输出并不对应同一个因果估计目标。因此，外部比较说明的是方法范围和假设，而不是某个方法全面优于另一个方法。

![图5](figures/mr_gxe_head_to_head.png)

图5。共享输入比较。（a）显示目标明确的估计，并用菱形标出生成真值；（b）只对估计目标明确的方法—场景组合显示覆盖率，灰色单元格表示目标不同，因此不评分。

## Arabidopsis数据契约案例

Arabidopsis案例的目的，是演示公开数据工作流和诊断，而不是进行新的因果发现。从GSE80744标准化表达矩阵中提取AT1G11560的基线叶片表达，从1001 Genomes v3.1矩阵中提取局部基因型，并从AraPheno中提取10°C和16°C开花时间。局部关联模型使用带5个全基因组主成分的普通最小二乘回归，遵循植物关联分析中需要建模群体结构和亲缘关系的一般原则，[29–34] 但没有把它写成已重新实现发表研究中的混合模型/SMR分析。[19–24]

表5。Arabidopsis数据契约的输入和局部处理。

| 层面 | 公共来源 | 局部处理 |
| --- | --- | --- |
| 分子暴露 | GSE80744标准化表达 | AT1G11560行；log1p变换；基线暴露 |
| 基因型 | 1001 Genomes v3.1 | Chr1:3,861,124–3,901,085；3,352个局部SNP；5个主成分 |
| 结局环境1 | AraPheno FT10 | 10°C开花时间；z=−3 |
| 结局环境2 | AraPheno FT16 | 16°C开花时间；z=+3 |
| 等位基因 | 1001 Genomes材料VCF | 为剂量编码矩阵建立REF/ALT对应关系 |

在P≤5×10−8、F≥10和MAF≥0.05的条件下，48个SNP在两个环境中都通过筛选。由于它们之间存在较强相关，主要分析提供了带符号的LD相关矩阵。主要的对角环境协方差分析估计截距为2.3601（SE 0.4685，P=4.72×10−7），环境斜率为−0.03705（SE 0.15617，P=0.81249）。残余异质性为Q=192.89，自由度为60（按矩阵秩调整），P=7.33×10−16。

表6。Arabidopsis案例的工具变量审计。各排除数量可能来自重叠诊断，不能相加后当作互不重叠的阶段数量。

| 审计阶段 | 数量 | 解释 |
| --- | --- | --- |
| 原始完整SNP×环境网格 | 172个SNP/344行 | 每个原始局部SNP都有两个环境的记录。 |
| 有歧义的回文变异排除 | 每个环境3个 | 在等位基因协调阶段排除；剩余169个SNP/338行。 |
| P值诊断排除 | 121行 | 与其他质量控制排除重叠，不是独立阶段数量。 |
| F统计量诊断排除 | 106行 | 与P值和完整网格诊断重叠。 |
| 最终完整网格工具变量 | 48个SNP/96行 | 在两个环境中均满足预先设定的P值、F和MAF要求。 |
| LD矩阵/协方差秩 | 48×48 LD；rank(V)=62 | 考虑矩阵秩的Q使用62−2=60个残余自由度。 |

表7。按环境分层的比较估计。估计来自局部OLS摘要统计演示，不是因果模型的独立验证。

| 环境 | 估计器 | 估计值 | SE | P值 | Q（P值） |
| --- | --- | --- | --- | --- | --- |
| 10°C | 固定效应IVW | 6.6001 | 0.2038 | 4.999×10−230 | 84.90（5.89×10−4） |
| 10°C | 随机效应IVW | 7.0842 | 0.2970 | 1.030×10−125 | 84.90（5.89×10−4） |
| 10°C | MR-Egger | 4.2259 | 0.5188 | 3.758×10−16 | — |
| 16°C | 固定效应IVW | 8.2379 | 0.2933 | 1.402×10−173 | 97.70（2.05×10−5） |
| 16°C | 随机效应IVW | 8.8667 | 0.4561 | 3.598×10−84 | 97.70（2.05×10−5） |
| 16°C | MR-Egger | 6.7552 | 0.7683 | 1.466×10−18 | — |

两个环境的IVW估计均为正，但大小不同（固定效应IVW在10°C为6.6001，在16°C为8.2379）。它们的异质性统计量显著，这为环境斜率分析提供了动机，但本身不能识别环境效应。MR-Egger估计值更低，并且截距诊断较大（10°C截距为2.9281，P=3.59×10−8；16°C截距为2.0160，P=0.0103），说明多效性应被视为尚未解决的限制，而不是已经解决的问题。

敏感性分析使用1,122个共享AraPheno材料中FT10和FT16的Pearson相关性（r=0.88195）作为表型相关性代理。该分析估计截距为1.8027（SE 0.6217，P=0.00374），斜率为−0.08228（SE 0.06634，P=0.21491）。该代理值不是已知的比值误差协方差，因此不作为主要推断。

| 解释 本案例说明PlantMR可以把植物数据来源、LD依赖、完整网格选择和协方差近似明确呈现出来。它不能证明AT1G11560具有因果作用，因为表达队列和结局队列存在材料重叠，没有估计暴露—结局协方差，局部OLS不同于发表的混合模型，并且残余异质性仍然存在。 |
| --- |

![图4](figures/arabidopsis_case.png)

图4。Arabidopsis植物MR案例。（a）AT1G11560案例中对齐的暴露和结局区域关联轨道；（b）48个保留工具变量之间的LD；（c）按环境分层的MR估计；（d）主要分析和表型相关性代理下的环境斜率。误差条表示95%置信区间。

## 可复现性和运行时间

本地运行基准以返回码0完成了验证、合成G×E运行和Arabidopsis案例。三个任务耗时9.70–9.93秒，峰值常驻内存为126,664–133,424 KB。这些结果是单台主机上的可复现性基准，不代表普遍性能，也不代表全基因组规模的可扩展性。

表8。冻结版PlantMR实现的本地运行基准。

| 任务 | 用时（秒） | 峰值RSS（KB） | 返回码 |
| --- | --- | --- | --- |
| validate | 9.7034 | 126,664 | 0 |
| gxe_synthetic | 9.7974 | 129,736 | 0 |
| gxe_arabidopsis | 9.9300 | 133,424 | 0 |

# 讨论

## 主要发现

PlantMR针对植物摘要统计MR中的一个反复出现的问题：基因型、组织、发育阶段、环境、LD和样本重叠信息经常被分别保存。该工作流将这些字段与估计结果联系起来，并带入报告。这一点很重要，因为当暴露组织、发育阶段或处理条件发生变化时，同一个SNP层面的beta和标准误可能对应不同的估计目标。因此，本文的贡献是一个可复现的数据和分析工作流，而不是关于植物因果关系的新声明。

环境斜率分析回答的是一个更具体的问题：遗传代理的暴露—结局关联是否沿着预先指定的环境尺度发生变化？该斜率不是普遍适用的基因—环境因果参数，也不是多效性校正截距。它的使用依赖于共同的SNP×环境工具变量网格、具有生物学解释的环境对比以及与数据结构相匹配的协方差模型。

模拟结果说明这些细节为什么会影响推断。在本研究测试场景下，正确协方差模型和对角模型给出了相近的点估计，但在LD压力测试中，独立性近似降低了标准误。零假设拒绝率从0.044升至0.126，覆盖率从0.956降至0.874。因此，在依赖性合理存在时，应报告协方差来源，并把对角分析作为敏感性分析，而不是默认的真实模型。

## 与相关方法的比较

PlantMR应当与已有MR方法配合使用。IVW、MR-Egger、稳健估计器和中位数估计器、多效性诊断、共定位及精细定位分别处理不同的不确定性来源。[3–12,28] 本文纳入的标准估计器提供共同的审计记录，但不能让无效工具变量变得有效。因此，Arabidopsis案例中的较大Q统计量和非零Egger截距是结果的一部分，不是通过更换另一个估计器就可以消除的问题。

共享输入比较也区分了PlantMR和交互MR。摘要统计MR-GxE利用工具变量—暴露关联中的基因—协变量交互，并在相应假设下估计不变因果效应和多效性项。[14] MR-GENIUS采用不同的识别策略，对交互强度和异质性有自己的条件要求。[15] MR-EILLS针对异质GWAS摘要数据中的不变因果效应。[16] PlantMR则估计效应沿观测环境尺度的变化。这四种量不能互相替换。

PlantMR与植物生物学MR应用的区别，在于证据目标不同。Liu等人将玉米干旱响应表达、eQTL、MR优先排序和实验跟进结合起来，提出了干旱耐受调控因子的候选名单。[18] Feng等人利用Arabidopsis区域GWAS和eQTL摘要统计、SMR/HEIDI以及独立表达数据，对AT1G11560进行候选优先排序。[19] 在Populus研究中，Liang等人通过关联分析、上位性、表达和MR分析，把一个miRNA及其靶基因的变异与木材性状联系起来。[37] 这些研究为本文的图形顺序提供了更直接的植物MR参照：环境或组织背景、区域遗传证据、分子关联、MR估计以及生物学解释边界。MRBIGR在玉米中整合基因型、转录组、代谢组、GWAS和MR分析，并用玉米和水稻数据展示工作流。[17] metaGE面向多环境GWAS荟萃分析，并在多个植物数据集上比较固定效应、随机效应和其他荟萃分析程序。[25] MAPtools强调命令行工作流、公开数据案例和可复现输出。[36] PlantMR采用植物研究中常见的证据顺序，但把重点放在考虑协方差的摘要统计MR上，而不是声称发现了新的生物学结论。

## 模拟和协方差行为

植物群体经常包含相关材料、局部单倍型和不均匀LD。因此，不能因为输入文件每行对应一个SNP，就假设比值估计的协方差矩阵是对角的。当相同材料被重复表型测量、试验共享对照或环境测量彼此相关时，环境之间也会产生依赖。在这些情况下，协方差模型对标准误和异质性的影响通常大于对点估计的影响。

考虑矩阵秩的Q计算，为奇异或近似奇异的协方差矩阵提供了直接处理方式。主要案例有96个比值观测，但给定协方差矩阵的秩为62。因此，报告的残余自由度为rank(V)−rank(X)=60，而不是94或95。这个计算不能验证协方差矩阵在生物学上是否正确，但可以避免把线性依赖的观测当作相互独立。

压力测试还区分了校准和功效。在真实斜率为0.25的测试中，两种协方差选择的功效均为1.00，但对角模型未能保持零假设校准。只用功效评价会漏掉这一差异。因此，对于考虑协方差的方法，应同时报告零假设拒绝率、覆盖率、偏差、RMSE和标准误表现。

## Arabidopsis数据应用

Arabidopsis分析被用作一个公开数据工作流案例。局部区域提供了完整的双环境网格；有歧义的回文变异被排除，48个SNP通过最终工具变量筛选。按环境分层的固定效应IVW估计在两个温度下均为正，但大小不同。考虑协方差的环境斜率为−0.03705（SE 0.15617，P=0.81249），而残余异质性较高（Q=192.89，按矩阵秩调整的自由度为60，P=7.33×10−16）。

该案例不能证明AT1G11560是开花时间的因果调控因子。表达队列和结局队列存在材料重叠，暴露—结局抽样协方差不可得，局部关联模型使用普通最小二乘而不是发表的混合模型。基线表达代理还被直接带入两个结局环境，而不是作为环境特异的eQTL重新估计。适当的解释是：PlantMR能够暴露这些依赖关系，并产生可复现的敏感性结果；生物学结论仍然是暂时性的。

表型相关性敏感性分析说明了同一问题。FT10与FT16的相关性改变了拟合截距和斜率，但它不是暴露和结局GWAS估计值的实测协方差。因此，它可以作为敏感性计算，而不是样本重叠的正式校正。报告这个代理值及其性质，可以避免把一个方便获得的相关性误认为已识别的协方差。

## 在植物和作物研究中的使用

对于自然群体研究，报告应说明材料面板、地理结构处理策略、亲缘关系或混合模型方法、参考基因组组装，以及构建LD矩阵时使用的等位基因表示方式。对于育种群体和多环境试验，环境分数应在分析前定义，并代表具有生物学意义的对比，而不是事后命名的标签。温度、干旱程度、光周期或营养水平等变量的测量误差及其试验间相关性也应记录。

表达介导分析还要求把暴露背景与关联结果绑定。每个eQTL都应报告组织、发育阶段、处理条件和标准化方式。不能把基线eQTL不加说明地当作胁迫特异分子暴露。若生物学问题是中介作用，除了MR之外，还需要共定位、精细定位或HEIDI类证据。[11,12,28] 如果问题是环境特异的生物学效应，可能还需要对暴露关联本身进行环境特异建模。

多倍体剂量、同源异源基因归属、亚基因组特异LD、存在/缺失变异和结构变异都需要明确的数据模型。在当前实现中，这些变异不会被静默地重新编码为二倍体SNP。这样可以把软件限制与生物学阴性结果区分开，并明确未来解释这些分析所需的输入条件。

## 局限性

Arabidopsis案例不是独立的因果验证。它使用公开处理数据、重叠材料和局部OLS模型。案例只有两个结局环境，因此斜率只是预先指定环境尺度上的对比，不能证明线性关系、阈值效应或一般响应曲线。

方向性多效性模拟只覆盖一个结构化场景，没有覆盖平衡多效性、相关多效性、弱工具变量、非线性效应、环境测量误差、赢家诅咒或群体分层LD错配。当前软件接收外部提供的带符号相关矩阵，但不会估计因果LD面板、修复所有非半正定输入，或建模多倍体剂量和结构变异。

外部比较明确限于一个摘要统计MR-GxE实现。完整的个体水平MR-GxE分析以及MR-GENIUS或MR-EILLS的独立实现不在当前研究范围内。只有在对齐输入契约和目标估计量之后，才适合比较这些方法。若要把生物学结论推广到本演示之外，还需要在独立群体、更多环境、混合模型摘要统计和功能证据中扩展评估。

# 结论

PlantMR提供了一个用于植物摘要统计MR和环境效应异质性分析的可复现工作流。本文证据包括明确的元数据、完整网格工具变量选择、考虑协方差的GLS、考虑矩阵秩的异质性报告、校准模拟、共享输入MR-GxE比较和公开Arabidopsis案例。这些结果支持使用PlantMR把假设和数据依赖关系明确呈现出来；但它们不能证明AT1G11560是因果基因，也不能让PlantMR替代共定位、混合模型GWAS、交互MR方法或功能验证。

# 可用性和运行要求

PlantMR以MIT许可证发布。软件版本为v1.1.0，完整的手稿、基准结果和Word文档包冻结在v1.1.0-paper标签。公共代码仓库为https://github.com/Zhangzhishuai-HIT/PlantMR，供投稿使用的源码归档为`release/PlantMR_v1.1.0-paper_source.zip`。Zenodo或等效归档DOI尚待分配。

公共数据来源包括GSE80744标准化表达数据、AraPheno FT10/FT16、1001 Genomes v3.1以及Arabidopsis相关原始研究。1001 Genomes的大型提供方归档不随项目重新分发；项目包含派生的局部基因型区域、主成分分数、等位基因对应关系和提供方校验值。玉米补充工作簿、eQTL表和候选基因表被纳入审计材料，但没有被当作新的因果结果。

表9。Plant Methods软件可用性和运行要求。

| 字段 | 当前值 |
| --- | --- |
| 项目名称 | PlantMR 1.1 |
| 项目主页 | https://github.com/Zhangzhishuai-HIT/PlantMR |
| 操作系统 | 已在Linux上验证；目标是可移植的Python代码。 |
| 编程语言 | Python 3.10或更高版本。 |
| 依赖 | NumPy、pandas、SciPy、statsmodels、matplotlib和psutil；已在environment.yml中声明。 |
| 许可证 | MIT许可证。 |
| 非学术使用限制 | 当前许可证没有额外限制。 |

# 缩略语

| 缩略语 | 定义 |
| --- | --- |
| MR | Mendelian randomization，孟德尔随机化 |
| GWAS | Genome-wide association study，全基因组关联研究 |
| eQTL | Expression quantitative trait locus，表达数量性状位点 |
| G×E / GxE | Genotype-by-environment interaction，基因型—环境互作，或环境效应异质性 |
| LD | Linkage disequilibrium，连锁不平衡 |
| GLS | Generalized least squares，广义最小二乘 |
| IVW | Inverse-variance weighted，逆方差加权 |
| MAF | Minor allele frequency，次要等位基因频率 |
| SNP | Single-nucleotide polymorphism，单核苷酸多态性 |
| Q | Cochran-type heterogeneity statistic，Cochran类异质性统计量 |

# 声明

| 声明项目 | 状态 |
| --- | --- |
| 伦理审批和参与同意 | 不适用：使用的是公共植物材料和公共汇总/处理数据。 |
| 发表同意 | 不适用。 |
| 数据和材料可得性 | 上文说明了公共源数据和派生审计材料；代码位于https://github.com/Zhangzhishuai-HIT/PlantMR；归档DOI待分配。 |
| 利益冲突 | 待作者补充。 |
| 基金 | 待作者补充。 |
| 作者贡献 | 待作者补充。 |
| 致谢 | 待作者补充，或标记为不适用。 |
| 作者信息 | 作者姓名、单位和通讯作者信息待补。 |

# 参考文献

1. Davey Smith, G. & Ebrahim, S. “Mendelian randomization”: can genetic epidemiology contribute to understanding environmental determinants of disease? Int. J. Epidemiol. 32, 1–22 (2003). https://doi.org/10.1093/ije/dyg070

2. Lawlor, D. A., Harbord, R. M., Sterne, J. A. C., Timpson, N. & Smith, G. D. Mendelian randomization: using genes as instruments for making causal inferences in epidemiology. Stat. Med. 27, 1133–1163 (2008). https://doi.org/10.1002/sim.3034

3. Burgess, S., Butterworth, A. & Thompson, S. G. Mendelian randomization analysis with multiple genetic variants using summarized data. Genet. Epidemiol. 37, 658–665 (2013). https://doi.org/10.1002/gepi.21758

4. Bowden, J., Davey Smith, G. & Burgess, S. Mendelian randomization with invalid instruments: effect estimation and bias detection through Egger regression. Int. J. Epidemiol. 44, 512–525 (2015). https://doi.org/10.1093/ije/dyv080

5. Bowden, J., Davey Smith, G., Haycock, P. C. & Burgess, S. Consistent estimation in Mendelian randomization with some invalid instruments using a weighted median estimator. Genet. Epidemiol. 40, 304–314 (2016). https://doi.org/10.1002/gepi.21965

6. Hartwig, F. P., Davey Smith, G. & Bowden, J. Robust inference in summary data Mendelian randomization via the zero modal pleiotropy assumption. Int. J. Epidemiol. 46, 1985–1998 (2017). https://doi.org/10.1093/ije/dyx102

7. Verbanck, M. et al. Detection of widespread horizontal pleiotropy in causal relationships inferred from Mendelian randomization between complex traits and diseases. Nat. Genet. 50, 693–698 (2018). https://doi.org/10.1038/s41588-018-0099-7

8. Zhao, Q., Wang, J., Hemani, G., Bowden, J. & Small, D. S. Statistical inference in two-sample summary-data Mendelian randomization using robust adjusted profile score. Ann. Statist. 48, 1742–1769 (2020). https://doi.org/10.1214/19-AOS1866

9. Burgess, S. et al. Guidelines for performing Mendelian randomization investigations: update for summer 2023. Wellcome Open Res. 4, 186 (2023). https://doi.org/10.12688/wellcomeopenres.15555.3

10. Hemani, G. et al. The MR-Base platform supports systematic causal inference across the human phenome. eLife 7, e34408 (2018). https://doi.org/10.7554/eLife.34408

11. Zhu, Z. et al. Integration of summary data from GWAS and eQTL studies predicts complex trait gene targets. Nat. Genet. 48, 481–487 (2016). https://doi.org/10.1038/ng.3538

12. Zhu, Z. et al. Causal associations between risk factors and common diseases inferred from GWAS summary data. Nat. Commun. 9, 224 (2018). https://doi.org/10.1038/s41467-017-02317-2

13. Skrivankova, V. W. et al. Strengthening the reporting of observational studies in epidemiology using Mendelian randomization: the STROBE-MR statement. JAMA 326, 1614–1621 (2021). https://doi.org/10.1001/jama.2021.18236

14. Spiller, W. et al. Detecting and correcting for bias in Mendelian randomization analyses using Gene-by-Environment interactions. Int. J. Epidemiol. 48, 702–712 (2019). https://doi.org/10.1093/ije/dyy204

15. Spiller, W., Hartwig, F. P., Sanderson, E., Davey Smith, G. & Bowden, J. Interaction-based Mendelian randomization with measured and unmeasured gene-by-covariate interactions. PLoS ONE 17, e0271933 (2022). https://doi.org/10.1371/journal.pone.0271933

16. Hou, L., Chen, H. & Zhou, X.-H. MR-EILLS: an invariance-based Mendelian randomization method integrating multiple heterogeneous GWAS summary datasets. Nat. Commun. 16, 1–15 (2025). https://doi.org/10.1038/s41467-025-62823-6

17. Xu, F. et al. MRBIGR: a versatile toolbox for genetic regulation inference from population-scale multi-omics data. Plant Commun. 6, 101197 (2025). https://doi.org/10.1016/j.xplc.2024.101197

18. Liu, S. et al. Mapping regulatory variants controlling gene expression in drought response and tolerance in maize. Genome Biol. 21, 163 (2020). https://doi.org/10.1186/s13059-020-02069-1

19. Feng, X. et al. Dual-trait genomic analysis in highly stratified Arabidopsis thaliana populations using genome-wide association summary statistics. Heredity 133, 11–20 (2024). https://doi.org/10.1038/s41437-024-00688-z

20. The 1001 Genomes Consortium. 1,135 Genomes reveal the global pattern of polymorphism in Arabidopsis thaliana. Cell 166, 481–491 (2016). https://doi.org/10.1016/j.cell.2016.05.063

21. Kawakatsu, T. et al. Epigenomic diversity in a global collection of Arabidopsis thaliana accessions. Cell 166, 492–505 (2016). https://doi.org/10.1016/j.cell.2016.06.044

22. Schmitz, R. J. et al. Patterns of population epigenomic diversity. Nature 495, 193–198 (2013). https://doi.org/10.1038/nature11968

23. Atwell, S. et al. Genome-wide association study of 107 phenotypes in Arabidopsis thaliana inbred lines. Nature 465, 627–631 (2010). https://doi.org/10.1038/nature08800

24. Brachi, B. et al. Linkage and association mapping of Arabidopsis thaliana flowering time in nature. PLoS Genet. 6, e1000940 (2010). https://doi.org/10.1371/journal.pgen.1000940

25. De Walsche, A. et al. metaGE: investigating genotype × environment interactions through GWAS meta-analysis. PLoS Genet. 21, e1011553 (2025). https://doi.org/10.1371/journal.pgen.1011553

26. Sul, J. H. et al. Accounting for population structure in gene-by-environment interactions in genome-wide association studies using mixed models. PLoS Genet. 12, e1005849 (2016). https://doi.org/10.1371/journal.pgen.1005849

27. An, X. et al. An approach to identify gene-environment interactions and reveal new biological insight in complex traits. Nat. Commun. 15, 1–16 (2024). https://doi.org/10.1038/s41467-024-47806-3

28. Giambartolomei, C. et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. PLoS Genet. 10, e1004383 (2014). https://doi.org/10.1371/journal.pgen.1004383

29. Price, A. L. et al. Principal components analysis corrects for stratification in genome-wide association studies. Nat. Genet. 38, 904–909 (2006). https://doi.org/10.1038/ng1847

30. Kang, H. M. et al. Efficient control of population structure in model organism association mapping. Genetics 178, 1709–1723 (2008). https://doi.org/10.1534/genetics.107.080101

31. Zhou, X. & Stephens, M. Genome-wide efficient mixed-model analysis for association studies. Nat. Genet. 44, 821–824 (2012). https://doi.org/10.1038/ng.2310

32. Lipka, A. E. et al. GAPIT: genome association and prediction integrated tool. Bioinformatics 28, 2397–2399 (2012). https://doi.org/10.1093/bioinformatics/bts444

33. Purcell, S. et al. PLINK: a tool set for whole-genome association and population-based linkage analyses. Am. J. Hum. Genet. 81, 559–575 (2007). https://doi.org/10.1086/519795

34. Chang, C. C. et al. Second-generation PLINK: rising to the challenge of larger and richer datasets. GigaScience 4, 7 (2015). https://doi.org/10.1186/s13742-015-0047-8

35. Kang, M. et al. The pan-genome and local adaptation of Arabidopsis thaliana. Nat. Commun. 14, 6259 (2023). https://doi.org/10.1038/s41467-023-42029-4

36. Candela, H. et al. MAPtools: command-line tools for mapping-by-sequencing and QTL-Seq analysis and visualization. Plant Methods 20, 107 (2024). https://doi.org/10.1186/s13007-024-01222-2

37. Liang, X. et al. Association study and Mendelian randomization analysis reveal effects of the genetic interaction between PtoMIR403b and PtoGT31B-1 on wood formation in Populus tomentosa. Front. Plant Sci. 12, 704941 (2021). https://doi.org/10.3389/fpls.2021.704941
