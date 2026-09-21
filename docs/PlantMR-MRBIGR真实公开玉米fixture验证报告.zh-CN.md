# PlantMR 2.x真实公开玉米fixture验证报告

## 结论先说

PlantMR 2.x已经用真实公开玉米数据跑通了一条无GUI命令行链：

VCF摄入/QC → 表型QC → GWAS → eQTL → SMR/HEIDI → 共定位 → MVMR → SAL → AGPv4变异注释 → GO → MR证据网络。

这证明了平台代码可以读取和处理真实文件，而不是只在模拟数据上通过测试。

这还不是“PlantMR已经在同一输入上超过MRBIGR”的证据。MRBIGR头对头运行没有完成，原因是MRBIGR当前源码依赖旧的Python/R生态，主机缺少可工作的依赖链；报告不把PlantMR自己的结果冒充MRBIGR比较结果。

## 下载来源和回执

原始文件保存在项目外部目录：

`/home/user/zhangzhishuai/myhermes/plant_mr_external/mrbigr_maize/source`

下载来源：

- MRBIGR论文公开Maizego表型：`http://www.maizego.org/download/blup_traits_final.csv`
- MRBIGR论文公开代谢物：`http://www.maizego.org/download/metabolic%20traits-E2.zip`
- MRBIGR公开转录组：`https://github.com/maizego/Transcriptome`
- Panzea HapMap3 282 panel共享目录：`https://iastate.app.box.com/s/8s77gpdtavyt9rdwav4o1nhndn9m4ivr`
- AGPv4官方基因注释：`GCF_902167145.1_Zm-B73-REFERENCE-NAM-5.0_genomic.gff.gz`
- MaizeGDB maize-GAMER AGPv4 GO：`maize.B73.AGPv4.aggregate.gaf.gz`

关键SHA-256：

- `hmp321_282_agpv4_chr10.vcf.gz`：2,344,063,132 bytes；`3b48137b1ac466e68b86def3f1f762de029947fc0e4511bec0e66ea2ec2d8681`
- `Expression_finalNormalized_28850.tar.gz`：20,012,366 bytes；`975699569d5c9033f472d8c78e04fd319e49ca9c9fa9ef542be2f42320b78276`
- `blup_traits_final.csv`：100,798 bytes；`992078e0702ddace583684ec9c4826ffec0f2f8275bb4e86dc5deef876d6427f`
- `metabolic_traits-E2.zip`：538,631 bytes；`24adfd175829e1a129cef3974ff981e8ec90c13ff57280482162807dea64864a`
- `GCF_902167145.1_Zm-B73-REFERENCE-NAM-5.0_genomic.gff.gz`：16,151,440 bytes；`c346640f06bfed314e00173a4fb8dc2ca85952ef9f6c82dfa3c23b3c08fe4675`
- `maize.B73.AGPv4.aggregate.gaf.gz`：2,274,860 bytes；`be3a2cd56021ddfcc87d00d89ba7537ba6e6f44c9395fde1ca8329a54c22efbc`

完整文件回执和Box目录清单在外部目录的`receipts/`中。

## 样本边界

公开层之间不能直接按论文中的总样本数拼接：

- Panzea chr10 VCF：277个样本；原始目录声明为282 panel，但chr10文件实际缺5个样本。
- 表达矩阵：368个材料、28,850个表达特征。
- 下载的BLUP表：508行材料×17个性状列。
- VCF与BLUP表直接同名交集：8个材料。
- VCF与表达矩阵直接同名交集：5个材料：B73、B77、CML323、CML69、SC55。
- 代谢物文件：339个材料×748列，其中与该VCF直接同名的交集过小，没有被硬拼进QTL链。

因此本次验证采用两条真实但分层的路径：

1. 277个VCF样本用于VCF读取和基因型QC；
2. 8个VCF×BLUP样本用于Plantheight GWAS；
3. 5个VCF×表达样本用于表达QTL；
4. 通过共享SNP的真实summary statistics运行SMR、coloc和MVMR。

这是一条工程和接口验证链，不是8/5个样本上的生物学发现研究。

## 实际运行结果

### 基因型QC

- 输入：277 samples × 5,000个chr10双等位变异前缀。
- 样本缺失率过滤后：32个样本。
- 变异缺失率过滤移除419个；进入MAF过滤的4,581个变异中，4,327个因MAF移除，最终保留254个变异。
- `mean0`填补后剩余缺失：0。
- 真实运行目录：`prepared/runs_vcf/vcf_qc/`。

### 表型QC

- 8个样本。
- 2个性状：Plantheight、Earheight。
- mean填补、z-score变换。
- 未标记异常值：0。
- 真实运行目录：`prepared/runs/phenotype_qc/`。

### GWAS

- 性状：Plantheight。
- 8个直接同名样本。
- OLS矩阵GWAS。
- 1,353个变异进入结果表。
- 真实运行目录：`prepared/runs/gwas_plantheight_v2/`。

该GWAS只用于验证输入、模型和输出链；8个样本不支持正式植物GWAS结论。

### QTL

- 表达特征1：`AC152495.1_FG017`，399个可用变异。
- 表达特征2：`AC208892.3_FG005`，399个可用变异。
- 使用5个直接同名表达样本，去掉含缺失剂量的变异后运行透明OLS QTL。
- 真实运行目录：`prepared/runs_qtl/qtl_expression_v2/`和`prepared/runs_qtl/qtl_expression_2/`。

### 普通MR

- 真实共享summary统计经过ref/alt等位基因对齐。
- 以`p≤0.05`、`F≥1`、`MAF≥0.01`作为这个小样本工程fixture的显式运行阈值；这不是正式研究阈值。
- 9个工具进入普通MR。
- IVW固定效应：β=-1.2413，SE=1.2068，P=0.3037。
- IVW随机效应：β=-1.2413，SE=1.2068，P=0.3037。
- MR-Egger：β=-1.6020，SE=1.4603，P=0.2726。
- 没有提供LD矩阵，因此没有做LD clumping；报告已明确写出这一限制。
- 真实运行目录：`prepared/runs_causal/ordinary_mr_v3/`。

### SMR/HEIDI

两个表达特征分别运行，均有364个共享SNP：

- `AC152495.1_FG017`：SMR β=-2.1104，P=0.5207，HEIDI P=1.0，状态pass。
- `AC208892.3_FG005`：SMR β=0.0323，P=0.9925，HEIDI P=1.0，状态pass。

这里的pass只表示本实现中的HEIDI异质性统计没有达到0.01阈值，不表示表达特征具有生物学因果作用。

### 共定位

Wakefield ABF结果：

- PP0=0.9213
- PP1=0.0398
- PP2=0.0335
- PP3=0.0014
- PP4=0.0040

PP4很低，不能支持共享因果变异的结论。

### MVMR

- 两个表达特征，各364个SNP。
- `AC152495.1_FG017`：β=-1.9337，SE=0.3098，P=1.21e-09。
- `AC208892.3_FG005`：β=-0.6373，SE=0.3652，P=0.0818。
- Q统计量=206.5455，df=362。

这个结果只能证明MVMR代码接受并处理了真实summary统计；由于输入来自5个表达样本和8个表型样本，不能作为植物因果发现。

### SAL和AGPv4注释

- 1,270个带有真实chr10坐标的GWAS结果用于注释。
- NCBI AGPv4 GFF导出44,680条gene记录，去重后输入平台4万余条基因区间。
- 变异位置注释输出：1,270条。
- 放宽到fixture验证阈值后检测到1个SAL。
- 真实运行目录：`prepared/runs_annotation/annotation_gff/`和`prepared/runs_sal/sal_plantheight/`。

### GO

- MaizeGDB maize-GAMER AGPv4 GAF：39,324个feature、450,632条feature-GO关系。
- 选择100个真实GAF feature作为GO模块输入测试。
- 输出566个GO term结果并进行BH校正。
- 这一步验证的是GO文件读取、超几何检验和多重校正；输入feature不是从一个可靠的全基因组显著QTL列表筛出的，不能解释成生物学富集发现。

### 网络

- 输入边来自两次真实SMR输出。
- 2条feature→Plantheight边，3个节点，1个模块，无环。
- 为了让这个小fixture验证网络输出，网络P阈值设为1.0；因此两条边都进入汇总，不代表显著因果关系。
- 真实运行目录：`prepared/runs_network/smr_network/`。

## MRBIGR实际审计

源码：`https://github.com/CrazyHsu/MRBIGR`

源码commit：`7c80d44cb88260a2b5e1b90b453f3747244ac1ce`

实际尝试：

1. 直接运行`python MRBIGR.py -h`，最初因缺少`pandas_plink`失败。
2. 读取源码后确认顶层还会导入`pyranges`、`rpy2`和R相关模块；GO模块明确调用`AnnotationForge`、`clusterProfiler`。
3. 尝试安装公开Python依赖时，`sorted-nearest`需要本机编译；系统GCC 4.8.5不能编译其C99代码，安装失败。
4. 当前机器也没有可用的Rscript/GEMMA/PLINK运行链。

所以本轮没有声称“MRBIGR与PlantMR在同一输入上谁更快、谁更准、谁输出更多”。当前可核验结论是：

- MRBIGR提供GUI工作流和Python/R混合环境；
- PlantMR按用户要求不做GUI，使用CLI/API和项目manifest；
- PlantMR已经用真实文件跑通公开fixture的主链；
- MRBIGR的真实无GUI头对头复跑仍被其依赖链阻塞；
- 不能把“MRBIGR没有在本机跑起来”解释成PlantMR算法优于MRBIGR。

## 当前可声称和不可声称

可以声称：

- PlantMR 2.x可以在无GUI环境中处理真实玉米VCF、表型、表达、GFF和GAF文件。
- PlantMR 2.x的GWAS、QTL、SMR/HEIDI、coloc、MVMR、SAL、位置注释、GO和网络命令有真实运行回执。
- 输入文件和运行输出有独立目录、manifest和SHA-256来源回执。

不能声称：

- 这8/5个样本证明了新的玉米生物学发现；
- PlantMR已经在统计性能上超过MRBIGR；
- 当前内置OLS/GLS等价于GEMMA/GAPIT3/rMVP；
- 当前SMR、coloc或网络结果证明了因果基因；
- 已完成全基因组、全368表达材料和全527/282材料的公平对照。

## 可复跑入口

准备fixture：

```bash
python benchmarks/mrbigr_comparison/scripts/prepare_maizego_fixture.py \
  --source-dir /home/user/zhangzhishuai/myhermes/plant_mr_external/mrbigr_maize/source \
  --out-dir /home/user/zhangzhishuai/myhermes/plant_mr_external/mrbigr_maize/prepared \
  --max-variants 5000 \
  --n-expression-features 32
```

随后使用prepared目录中的manifest运行`plantmr2`。完整机器路径和run目录在本报告引用的外部fixture目录中；原始数据不复制进Git仓库。
