#!/usr/bin/env python3
"""Create the full English submission manuscript as a DOCX."""
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/PlantMR_submission_manuscript.docx'
FIG=ROOT/'docs/figures/gxe_simulation.png'
NAVY='17365D'; TEAL='0F6B78'; LIGHT='EAF3F5'; GREY='F4F6F8'; YELLOW='FFF2CC'


def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=tcPr.find(qn('w:shd'))
    if shd is None: shd=OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'), fill)

def cell_text(cell,text,bold=False,size=8.5,color=None):
    cell.text=''; p=cell.paragraphs[0]; p.paragraph_format.space_after=Pt(0)
    r=p.add_run(str(text)); r.bold=bold; r.font.size=Pt(size)
    if color: r.font.color.rgb=RGBColor.from_string(color)
    cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER

def table(doc,headers,rows,widths=None,size=8.5):
    t=doc.add_table(rows=1,cols=len(headers)); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,h in enumerate(headers): cell_text(t.rows[0].cells[i],h,True,size,'FFFFFF'); shade(t.rows[0].cells[i],NAVY)
    for ri,row in enumerate(rows):
        cells=t.add_row().cells
        for i,v in enumerate(row):
            cell_text(cells[i],v,size=size)
            if ri%2: shade(cells[i],GREY)
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Cm(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return t

def heading(doc,text,level=1):
    p=doc.add_paragraph(style='Heading %d'%level); p.add_run(text); return p

def para(doc,text,after=5):
    p=doc.add_paragraph(); p.paragraph_format.line_spacing=1.12; p.paragraph_format.space_after=Pt(after); p.add_run(text); return p

def bullet(doc,text):
    p=doc.add_paragraph(style='List Bullet'); p.paragraph_format.space_after=Pt(2); p.add_run(text); return p

def numbered(doc,text):
    p=doc.add_paragraph(style='List Number'); p.paragraph_format.space_after=Pt(2); p.add_run(text); return p

def note(doc,title,text,fill=LIGHT):
    t=doc.add_table(rows=1,cols=1); c=t.cell(0,0); shade(c,fill); c.text=''
    p=c.paragraphs[0]; r=p.add_run(title+'\n'); r.bold=True; r.font.color.rgb=RGBColor.from_string(TEAL); r.font.size=Pt(9.5)
    r=p.add_run(text); r.font.size=Pt(9)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)

def hyperlink(paragraph,text,url):
    rid=paragraph.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    h=OxmlElement('w:hyperlink'); h.set(qn('r:id'),rid); r=OxmlElement('w:r'); rp=OxmlElement('w:rPr'); c=OxmlElement('w:color'); c.set(qn('w:val'),'0563C1'); rp.append(c); u=OxmlElement('w:u'); u.set(qn('w:val'),'single'); rp.append(u); r.append(rp); t=OxmlElement('w:t'); t.text=text; r.append(t); h.append(r); paragraph._p.append(h)

def page_field(p):
    r=p.add_run('Page '); r.font.size=Pt(8)
    for typ in ['begin','separate','end']:
        el=OxmlElement('w:fldChar'); el.set(qn('w:fldCharType'),typ); r._r.append(el)
        if typ=='separate':
            t=OxmlElement('w:t'); t.text='1'; r._r.append(t)

def main():
    doc=Document(); sec=doc.sections[0]; sec.top_margin=Cm(2.0); sec.bottom_margin=Cm(1.8); sec.left_margin=Cm(2.0); sec.right_margin=Cm(2.0)
    styles=doc.styles; n=styles['Normal']; n.font.name='Arial'; n._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); n.font.size=Pt(10.5)
    for level,size,color in [(1,16,NAVY),(2,13,TEAL),(3,11,TEAL)]:
        s=styles['Heading %d'%level]; s.font.name='Arial'; s._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor.from_string(color); s.paragraph_format.space_before=Pt(10); s.paragraph_format.space_after=Pt(4)
    for sn in ['List Bullet','List Number']:
        s=styles[sn]; s.font.name='Arial'; s.font.size=Pt(10)
    header=sec.header.paragraphs[0]; header.text='PlantMR | Submission manuscript'; header.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    for r in header.runs: r.font.size=Pt(8); r.font.color.rgb=RGBColor.from_string('666666')
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER; page_field(footer)

    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(35)
    r=p.add_run('PlantMR: an auditable summary-statistics toolkit for plant and crop Mendelian randomization with environment-aware effect heterogeneity'); r.bold=True; r.font.size=Pt(20); r.font.color.rgb=RGBColor.from_string(NAVY)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('[Author names, affiliations and corresponding-author details to be supplied]').italic=True
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('Submission manuscript | PlantMR v1.1.0-paper | 19 September 2026').font.size=Pt(10)
    note(doc,'Submission status','The scientific content, analyses, source data, simulations and software snapshot are frozen. Author metadata, public repository DOI and final journal formatting remain to be supplied before external submission.',YELLOW)
    doc.add_page_break()

    heading(doc,'Abstract',1)
    para(doc,'Plant Mendelian randomization (MR) analyses can connect molecular traits to agronomic phenotypes, but plant reference assemblies, environmental strata, linkage disequilibrium (LD) and sample overlap are often left implicit. We developed PlantMR 1.1, an open-source local toolkit with a plant summary-statistics schema, allele harmonization, instrument quality control, signed LD handling, standard MR estimators and a narrowly defined environment-slope analysis. The environment-slope estimator models SNP-by-environment ratio estimates by generalized least squares, accepts signed environment and SNP-LD correlation matrices, requires a complete SNP-by-environment grid and reports covariance rank. In 500-replicate simulations with environmental correlation, the covariance-aware estimator had a null rejection rate of 0.054 and 95% coverage of 0.946; under a true slope of 0.25, its mean estimate was 0.2498, bias −0.00018, coverage 0.952 and power 1.00. In an additional LD stress test with AR(1) LD correlation rho=0.6, correct covariance modeling gave a null rejection rate of 0.044 and coverage of 0.956, whereas an independence approximation gave 0.126 and 0.874. Directional pleiotropy remained a limitation: the slope was approximately unbiased, but the pooled intercept was biased by 0.216. We executed an Arabidopsis data-contract case using AT1G11560 baseline expression, 1001 Genomes local genotypes and flowering-time phenotypes at 10°C and 16°C. Forty-eight LD-correlated instruments passed prespecified exposure thresholds. The primary LD-aware analysis estimated a slope of −0.0371 (SE 0.1562, P=0.812), with residual heterogeneity (Q=192.89, df=60, P=7.33×10−16). This case demonstrates reproducibility and diagnostics, not independent causal validation. PlantMR is positioned as a plant-focused implementation and audit workflow, not as the first environment-interaction MR method.')
    para(doc,'Keywords: Mendelian randomization; plant genomics; crop genomics; genotype–environment interaction; eQTL; linkage disequilibrium; summary statistics; reproducibility')

    heading(doc,'Introduction',1)
    para(doc,'Mendelian randomization uses genetic associations as instrumental variables to estimate genetically proxied exposure effects on outcomes.[1,2] The relevance, exchangeability and exclusion-restriction assumptions provide the foundation for interpretation, but their implementation depends on the study population, phenotype, molecular exposure and data-generating design. Summary-statistics MR has enabled large-scale analyses using public genome-wide association studies (GWAS), yet summarized associations are also vulnerable to weak instruments, horizontal pleiotropy, LD and sample overlap.[3–9]')
    para(doc,'Plant applications add several complications. Natural accessions and breeding panels can exhibit strong geographic structure and kinship. LD decay can differ substantially between species, populations and genomic regions. Expression is strongly dependent on tissue, developmental stage and treatment. Multi-environment trials and stress experiments frequently measure the same genotypes under several conditions, creating correlated estimates rather than independent GWAS datasets. Polyploid dosage, presence/absence variation and structural variation introduce additional representations that cannot be silently converted to ordinary biallelic SNPs.')
    para(doc,'Existing plant-oriented software demonstrates the value of integrated workflows. MRBIGR provides a broad population-scale multi-omics and MR toolbox for maize.[17] The maize drought study that motivates the present work prioritized genes using dynamic eQTLs and a lead-eQTL MR workflow.[18] Outside plants, MR-GxE uses gene-by-covariate interactions to detect or correct pleiotropic bias under a constant-pleiotropy assumption,[14] whereas interaction-based MR work distinguishes MR-GxE from MR-GENIUS and emphasizes interaction strength and assumption sensitivity.[15] MR-EILLS targets an invariant causal effect across heterogeneous GWAS summary datasets and evaluates multiple MR and meta-analytic comparators.[16] These methods have different estimands and should not be conflated.')
    para(doc,'Here we develop PlantMR as a plant/crop summary-statistics software and reporting workflow. The contribution is deliberately narrower than a new general theory of interaction MR: (i) an explicit plant metadata and summary-statistics contract; (ii) complete SNP-by-environment instrument selection; (iii) signed LD and environment-correlation inputs; (iv) rank-aware heterogeneity diagnostics; and (v) a reproducible local implementation with simulations and a real Arabidopsis data-contract case. We evaluate calibration, LD-misspecification risk and failure boundaries rather than claiming a new causal gene discovery.')

    heading(doc,'Results',1)
    heading(doc,'PlantMR software contract and analysis workflow',2)
    para(doc,'PlantMR accepts exposure and outcome tables containing SNP, effect allele, other allele, beta, standard error and P value. Optional fields include effect-allele frequency and sample size. Plant metadata records species, reference assembly, trait, tissue, developmental stage, environment, ploidy and LD-panel provenance. The software validates numeric values and alleles, harmonizes reversed and complemented alleles, identifies ambiguous palindromic variants, applies P-value/MAF/F-statistic filters and records every exclusion.')
    table(doc,['Component','Function','Output'],[
        ['Schema and metadata','Validate summary statistics and plant context','Validation messages and metadata JSON'],
        ['Allele harmonization','Align effect alleles and handle palindromic variants','Harmonized table and exclusion counts'],
        ['Instrument QC','P value, MAF, F statistic and complete-grid filtering','Instrument audit and retained SNP table'],
        ['Standard MR','Wald, fixed/random IVW, MR-Egger, Q and leave-one-out','JSON, TSV and Markdown reports'],
        ['Environment slope','GLS on SNP×environment ratio estimates','Pooled effect, slope, covariance rank and Q'],
        ['Reproducibility','CLI, tests, simulations, source-data records','Versioned reports and benchmark outputs'],
    ],[3.2,7.0,6.0],8.2)
    para(doc,'The command-line interface exposes validate, run, run-stratified and run-gxe commands. The software does not silently substitute SMR, GSMR, colocalization, MVMR, MR-PRESSO, MR-GxE, MR-GENIUS or MR-EILLS.')

    heading(doc,'Environment-effect-heterogeneity model',2)
    para(doc,'For SNP j and environment k, the ratio estimate is r_jk = beta_y,jk / beta_x,jk. Let z_k be a prespecified numeric environmental score. PlantMR fits r_jk = theta_0 + theta_1 z_k + epsilon_jk. theta_0 is the genetically proxied effect at z=0 and theta_1 is the change in the MR effect per unit increase in z. This is an effect-heterogeneity model. Its intercept is not the MR-GxE pleiotropy intercept and is not interpreted as a correction for horizontal pleiotropy.')
    para(doc,'The first-order delta variance is v_jk = se_y,jk² / beta_x,jk² + beta_y,jk² se_x,jk² / beta_x,jk⁴. With SNP-major/environment-major ordering, optional signed SNP and environment correlation matrices define V = D(R_SNP ⊗ R_ENV)D, where D is the diagonal matrix of ratio standard errors. The GLS estimator is theta_hat = (X′V⁻¹X)⁻¹X′V⁻¹r, with X=[1,z]. If V is rank-deficient, residual heterogeneity degrees of freedom are rank(V)−rank(X).')
    para(doc,'The model requires a complete environment grid for each SNP and retains only SNPs that pass exposure P value, F statistic and MAF requirements in every environment. This prevents an apparent environmental slope from being caused solely by changing instrument composition. Missing environment correlation is not treated as verified independence; the report states that a diagonal approximation was used.')

    heading(doc,'Simulation calibration and LD stress',2)
    para(doc,'The primary simulation benchmark used 20 instruments, four environments, environmental correlation 0.5, exposure SE 0.01, outcome SE 0.04 and 500 replicates per scenario. It included a null slope, a true slope of 0.25 and a common directional-pleiotropic component. The LD stress benchmark used the same dimensions with AR(1) signed LD correlation rho=0.6 and compared correct covariance specification with a diagonal independence approximation.')
    table(doc,['Scenario','Covariance','Mean/bias','Coverage','Rejection or power'],[
        ['Null','Environment-aware','slope bias −0.00069','0.946','0.054'],
        ['Null','Diagonal','slope bias −0.00071','0.994','0.006'],
        ['Causal G×E','Environment-aware','mean 0.24982; bias −0.00018','0.952','1.000'],
        ['Causal G×E','Diagonal','mean 0.24832; bias −0.00168','1.000','1.000'],
        ['LD stress null','Correct LD+environment','bias 0.00172','0.956','0.044'],
        ['LD stress null','Diagonal misspecified','bias 0.00177','0.874','0.126'],
        ['LD stress causal','Correct LD+environment','bias 0.00136','0.970','1.000'],
        ['LD stress causal','Diagonal misspecified','bias 0.00170','0.880','1.000'],
    ],[3.5,4.3,4.2,2.7,3.0],8.0)
    para(doc,'The directional-pleiotropy scenario exposed an important limitation. The environment slope remained approximately unbiased when the true slope was zero, but the pooled intercept was biased by +0.216. Therefore, a stable environment slope cannot be interpreted as proof that the pooled causal relation is protected from horizontal pleiotropy.')
    if FIG.exists():
        doc.add_picture(str(FIG),width=Inches(6.35))
        p=doc.add_paragraph('Figure 1. Sampling distributions, rejection rates and confidence-interval coverage for the primary simulation benchmark. The separate LD stress benchmark is reported in Table 2 and the source-data directory.')
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].italic=True; p.runs[0].font.size=Pt(9)

    heading(doc,'Arabidopsis data-contract case',2)
    para(doc,'The Arabidopsis case was designed as a reproducibility and diagnostics demonstration rather than a new causal discovery. Baseline leaf expression of AT1G11560 was extracted from the GSE80744 normalized expression matrix, local genotypes were taken from the 1001 Genomes v3.1 matrix and flowering time at 10°C and 16°C was taken from AraPheno. The local association model used ordinary least squares with five whole-genome PCs; it was not presented as a reimplementation of the published mixed-model/SMR analysis.[19–23]')
    table(doc,['Layer','Public source','Local processing'],[
        ['Molecular exposure','GSE80744 normalized expression','AT1G11560 row; log1p transformation; baseline exposure'],
        ['Genotype','1001 Genomes v3.1','Chr1:3,861,124–3,901,085; 3,352 local SNPs; five PCs'],
        ['Outcome environment 1','AraPheno FT10','10°C flowering time; z=−3'],
        ['Outcome environment 2','AraPheno FT16','16°C flowering time; z=+3'],
        ['Alleles','1001 Genomes accession VCF','REF/ALT mapping for dosage-coded matrix'],
    ],[4.0,5.0,8.0],8.2)
    para(doc,'At P≤5×10−8, F≥10 and MAF≥0.05, 48 SNPs passed in both environments. They were strongly correlated, so the primary analysis supplied a signed LD correlation matrix. The primary diagonal-environment-covariance run estimated an intercept of 2.3601 (SE 0.4685, P=4.72×10−7) and an environment slope of −0.03705 (SE 0.15617, P=0.81249). Residual heterogeneity was Q=192.89 on 60 rank-adjusted degrees of freedom (P=7.33×10−16).')
    para(doc,'A sensitivity run used the Pearson correlation between FT10 and FT16 across 1,122 shared AraPheno accessions (r=0.88195) as a phenotype-correlation proxy. It estimated an intercept of 1.8027 (SE 0.6217, P=0.00374) and slope −0.08228 (SE 0.06634, P=0.21491). This proxy is not known ratio-error covariance and is not treated as primary inference.')
    note(doc,'Interpretation','The case shows that PlantMR can make plant data provenance, LD dependence, complete-grid selection and covariance approximations visible. It does not prove AT1G11560 causality, because expression and outcome cohorts share accessions, exposure–outcome covariance is not estimated, local OLS differs from the published LMM and residual heterogeneity remains.',YELLOW)

    heading(doc,'Discussion',1)
    para(doc,'PlantMR addresses a practical gap between generic MR estimators and plant data realities. The central contribution is an auditable analysis contract: an MR result is only interpretable together with the species, reference assembly, tissue, stage, environment, ploidy, instrument set, LD source and sample-overlap statement. The environment-slope model adds a narrow and transparent way to quantify effect heterogeneity without claiming the stronger identification properties of MR-GxE, MR-GENIUS or MR-EILLS.')
    para(doc,'The simulations show that the estimator recovers a known slope under the stated covariance model and that LD misspecification can make inference anti-conservative. The directional-pleiotropy scenario shows why the intercept and slope must not be overinterpreted. These are implementation-level findings, not universal guarantees. Weak instruments, nonlinear environmental response, unequal sample sizes, missing environments, LD-panel mismatch and exact exposure–outcome covariance require additional benchmarks before a genome-wide biological application.')
    para(doc,'The Arabidopsis analysis deliberately avoids a causal-gene claim. Existing Arabidopsis work has used SMR/HEIDI to prioritize AT1G11560 in an independent research context, but that external evidence is not counted as validation of this local PlantMR re-analysis.[19] The correct use of this case is to show how the software behaves on real plant inputs and how conclusions change when LD and environmental dependence are exposed.')
    para(doc,'PlantMR therefore should be submitted first as a plant methods/software article. A biological application paper would require formal mixed-model summary statistics, an appropriate sample-overlap covariance model, independent population or environment replication, colocalization or HEIDI/fine-mapping evidence and functional validation.')

    heading(doc,'Methods',1)
    heading(doc,'Study design and claim ceiling',2)
    para(doc,'The study was organized as a software/methods evaluation. We did not use the real-data case to select a favorable estimator, define a new gene-level claim or tune simulation truth. The main claims concern input validation, covariance-aware estimation and diagnostic transparency.')
    heading(doc,'Input schema and harmonization',2)
    para(doc,'Required summary columns were SNP, effect_allele, other_allele, beta, se and pval. Optional columns were eaf and n. The schema rejects empty/duplicate SNP identifiers, non-finite values, non-positive SE, invalid P values, invalid allele characters and equal effect/other alleles. Harmonization recognizes aligned, reversed, complemented and complemented-reversed alleles and uses allele frequencies to retain only resolvable palindromic variants.')
    heading(doc,'Instrument selection',2)
    para(doc,'The primary thresholds were exposure P≤5×10−8, F≥10 and MAF≥0.05 in the Arabidopsis case. The GxE selector requires every retained SNP to pass these filters in every environment. This prevents environment-specific tool composition from masquerading as effect heterogeneity. LD is represented by signed correlations, not r² values.')
    heading(doc,'Estimators and diagnostics',2)
    para(doc,'Standard methods include Wald ratio, fixed-effects IVW, random-effects IVW, MR-Egger, Cochran Q and leave-one-out analysis. The environment-slope estimator uses the delta-method ratio variance and GLS covariance described above. If the covariance is singular, a Moore–Penrose inverse is used for the quadratic form and Q degrees of freedom are rank adjusted.')
    heading(doc,'Simulation design',2)
    para(doc,'All simulations used fixed seeds recorded in metadata JSON files. The base benchmark used 20 SNPs and four environment scores (−1.5, −0.5, 0.5, 1.5). Exposure effects were generated as positive strong instruments. Outcome effects were generated from a pooled effect plus a known environment slope, with multivariate normal sampling errors. The LD stress benchmark additionally used an AR(1) LD correlation matrix with rho=0.6.')
    heading(doc,'Arabidopsis data processing',2)
    para(doc,'The GSE80744 normalized matrix was downloaded from GEO and the AT1G11560 row extracted. The 1001 Genomes HDF5 matrix was used to extract the local region; five PCs were calculated from every 1000th marker. A public accession VCF supplied REF/ALT labels. AraPheno FT10 and FT16 values were merged by accession ID. Local association regressions included genotype and PC1–PC5. Source URLs, hashes, generated tables and limitations are recorded with the case.')
    heading(doc,'Statistical reporting',2)
    para(doc,'All numerical results are reported with effect estimates, standard errors, P values, instrument counts, covariance source and heterogeneity diagnostics. No genome-wide multiple-testing claim is made for the single-gene Arabidopsis demonstration. Any future genome-wide run must prespecify gene-level aggregation, multiple-testing control and an independent validation set.')

    heading(doc,'Data, code and materials availability',1)
    para(doc,'PlantMR is released under the MIT License. The software snapshot is v1.1.0 and the complete manuscript/benchmark/Word-document package is frozen at tag v1.1.0-paper. The source archive `release/PlantMR_v1.1.0-paper_source.zip` is suitable for submission as supplementary software. Before publication, the archive should be mirrored to a public repository and assigned a DOI.')
    para(doc,'Public data sources include GSE80744 normalized expression data, AraPheno FT10/FT16, 1001 Genomes v3.1 and the Arabidopsis source publications. The large 1001 Genomes provider archive is not redistributed; the derived local genotype region, PC scores, allele mapping and provider checksums are included. The maize supplementary workbook, eQTL table and candidate table are included for audit but not used as a new causal result.')

    heading(doc,'Declarations',1)
    table(doc,['Declaration','Status'],[
        ['Ethics approval','Not applicable: public plant accessions and public aggregate/processed data were used.'],
        ['Competing interests','To be completed by authors.'],
        ['Funding','To be completed by authors.'],
        ['Author contributions','To be completed by authors.'],
        ['Corresponding author','To be completed by authors.'],
        ['Data/code availability','Source archive included; public repository and DOI to be added before submission.'],
    ],[4.5,12.5],8.8)

    heading(doc,'References',1)
    refs=[
        '1. Davey Smith, G. & Ebrahim, S. “Mendelian randomization”: can genetic epidemiology contribute to understanding environmental determinants of disease? Int. J. Epidemiol. 32, 1–22 (2003). https://doi.org/10.1093/ije/dyg070',
        '2. Lawlor, D. A., Harbord, R. M., Sterne, J. A. C., Timpson, N. & Smith, G. D. Mendelian randomization: using genes as instruments for making causal inferences in epidemiology. Stat. Med. 27, 1133–1163 (2008). https://doi.org/10.1002/sim.3034',
        '3. Burgess, S., Butterworth, A. & Thompson, S. G. Mendelian randomization analysis with multiple genetic variants using summarized data. Genet. Epidemiol. 37, 658–665 (2013). https://doi.org/10.1002/gepi.21758',
        '4. Bowden, J., Davey Smith, G. & Burgess, S. Mendelian randomization with invalid instruments: effect estimation and bias detection through Egger regression. Int. J. Epidemiol. 44, 512–525 (2015). https://doi.org/10.1093/ije/dyv080',
        '5. Bowden, J., Davey Smith, G., Haycock, P. C. & Burgess, S. Consistent estimation in Mendelian randomization with some invalid instruments using a weighted median estimator. Genet. Epidemiol. 40, 304–314 (2016). https://doi.org/10.1002/gepi.21965',
        '6. Hartwig, F. P., Davey Smith, G. & Bowden, J. Robust inference in summary data Mendelian randomization via the zero modal pleiotropy assumption. Int. J. Epidemiol. 46, 1985–1998 (2017). https://doi.org/10.1093/ije/dyx233',
        '7. Verbanck, M. et al. Detection of widespread horizontal pleiotropy in causal relationships inferred from Mendelian randomization between complex traits and diseases. Nat. Genet. 50, 693–698 (2018). https://doi.org/10.1038/s41588-018-0099-7',
        '8. Zhao, Q., Wang, J., Hemani, G., Bowden, J. & Small, D. S. Statistical inference in two-sample summary-data Mendelian randomization using robust adjusted profile score. Ann. Statist. 48, 1742–1769 (2020). https://doi.org/10.1214/19-AOS1866',
        '9. Burgess, S. et al. Guidelines for performing Mendelian randomization investigations: update for summer 2023. Wellcome Open Res. 4, 186 (2023). https://doi.org/10.12688/wellcomeopenres.15555.3',
        '10. Hemani, G. et al. The MR-Base platform supports systematic causal inference across the human phenome. eLife 7, e34408 (2018). https://doi.org/10.7554/eLife.34408',
        '11. Zhu, Z. et al. Integration of summary data from GWAS and eQTL studies predicts complex trait gene targets. Nat. Genet. 48, 481–487 (2016). https://doi.org/10.1038/ng.3538',
        '12. Zhu, Z. et al. Causal associations between risk factors and common diseases inferred from GWAS summary data. Nat. Commun. 9, 2242 (2018). https://doi.org/10.1038/s41467-018-03940-5',
        '13. Skrivankova, V. W. et al. Strengthening the reporting of observational studies in epidemiology using Mendelian randomization: the STROBE-MR statement. JAMA 326, 1614–1621 (2021). https://doi.org/10.1001/jama.2021.18236',
        '14. Spiller, W. et al. Detecting and correcting for bias in Mendelian randomization analyses using Gene-by-Environment interactions. Int. J. Epidemiol. (2018). https://doi.org/10.1093/ije/dyy204',
        '15. Spiller, W., Hartwig, F. P., Sanderson, E., Davey Smith, G. & Bowden, J. Interaction-based Mendelian randomization with measured and unmeasured gene-by-covariate interactions. PLoS ONE 17, e0271933 (2022). https://doi.org/10.1371/journal.pone.0271933',
        '16. Hou, L., Chen, H. & Zhou, X.-H. MR-EILLS: an invariance-based Mendelian randomization method integrating multiple heterogeneous GWAS summary datasets. Nat. Commun. 16, 1–15 (2025). https://doi.org/10.1038/s41467-025-62823-6',
        '17. Xu, F. et al. MRBIGR: a versatile toolbox for genetic regulation inference from population-scale multi-omics data. Plant Commun. (2024). https://doi.org/10.1016/j.xplc.2024.101197',
        '18. Liu, S. et al. Mapping regulatory variants controlling gene expression in drought response and tolerance in maize. Genome Biol. 21, 163 (2020). https://doi.org/10.1186/s13059-020-02069-1',
        '19. Feng, X. et al. Dual-trait genomic analysis in highly stratified Arabidopsis thaliana populations using genome-wide association summary statistics. Heredity 133, 11–20 (2024). https://doi.org/10.1038/s41437-024-00688-z',
        '20. The 1001 Genomes Consortium. 1,135 Genomes reveal the global pattern of polymorphism in Arabidopsis thaliana. Cell 166, 481–491 (2016). https://doi.org/10.1016/j.cell.2016.05.063',
        '21. Kawakatsu, T. et al. Epigenomic diversity in a global collection of Arabidopsis thaliana accessions. Cell 166, 492–505 (2016). https://doi.org/10.1016/j.cell.2016.06.044',
        '22. Schmitz, R. J. et al. Patterns of population epigenomic diversity. Nature 495, 193–198 (2013). https://doi.org/10.1038/nature11968',
        '23. Atwell, S. et al. Genome-wide association study of 107 phenotypes in Arabidopsis thaliana inbred lines. Nature 465, 627–631 (2010). https://doi.org/10.1038/nature08800',
        '24. Brachi, B. et al. Linkage and association mapping of Arabidopsis thaliana flowering time in nature. PLoS Genet. 6, e1000940 (2010). https://doi.org/10.1371/journal.pgen.1000940',
        '25. De Walsche, A. et al. metaGE: investigating genotype × environment interactions through GWAS meta-analysis. PLoS Genet. 21, e1011553 (2025). https://doi.org/10.1371/journal.pgen.1011553',
        '26. Sul, J. H. et al. Accounting for population structure in gene-by-environment interactions in genome-wide association studies using mixed models. PLoS Genet. 12, e1005849 (2016). https://doi.org/10.1371/journal.pgen.1005849',
        '27. An, X. et al. An approach to identify gene-environment interactions and reveal new biological insight in complex traits. Nat. Commun. 15, 1–16 (2024). https://doi.org/10.1038/s41467-024-47806-3',
        '28. Giambartolomei, C. et al. Bayesian test for colocalisation between pairs of genetic association studies using summary statistics. PLoS Genet. 10, e1004383 (2014). https://doi.org/10.1371/journal.pgen.1004383',
        '29. Nature Portfolio. Guidelines for authors submitting code and software. https://media.nature.com/full/nature-cms/documents/GuidelinesCodePublication.pdf',
        '30. Nature Portfolio. Guidance on reproducibility for papers using computational tools. https://www.nature.com/documents/Computational_tools_reporting_guidelines.pdf',
        '31. Plant Methods. Aims and scope and software-article criteria. https://plantmethods.biomedcentral.com/about',
        '32. BMC Bioinformatics. Software article submission guidelines. https://link.springer.com/journal/12859/submission-guidelines/software-article',
        '33. GigaScience. Open science journal: aims and research-object policy. https://academic.oup.com/gigascience/pages/About',
        '34. PLOS Computational Biology. Journal information and software/code-availability policies. https://journals.plos.org/ploscompbiol/s/journal-information',
        '35. PLOS Computational Biology. Code availability policy. https://journals.plos.org/ploscompbiol/s/code-availability',
    ]
    for ref in refs:
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Cm(0.45); p.paragraph_format.first_line_indent=Cm(-0.45); p.paragraph_format.space_after=Pt(3); p.add_run(ref).font.size=Pt(8.5)

    heading(doc,'Submission metadata to complete',1)
    table(doc,['Field','Status'],[
        ['Authors and affiliations','To be supplied by authors'],
        ['Corresponding author','To be supplied by authors'],
        ['Funding','To be supplied by authors'],
        ['Competing interests','To be supplied by authors'],
        ['Public repository URL/DOI','To be supplied before external submission'],
        ['Target journal formatting','Plant Methods recommended; format after presubmission response'],
    ],[5.0,12.0],8.8)

    cp=doc.core_properties; cp.title='PlantMR: plant and crop Mendelian randomization with environment-aware effect heterogeneity'; cp.subject='Submission manuscript'; cp.author='PlantMR contributors'; cp.keywords='Mendelian randomization, plants, crops, LD, GxE, software'
    OUT.parent.mkdir(parents=True,exist_ok=True); doc.save(OUT); print(OUT)

if __name__=='__main__': main()
