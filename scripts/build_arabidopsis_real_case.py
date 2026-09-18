#!/usr/bin/env python3
"""Build a transparent local Arabidopsis summary-statistics case study."""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t


def association(genotype, phenotype, pcs):
    frame = pd.DataFrame({"g": genotype, "y": phenotype}).join(pcs, how="inner").dropna()
    if len(frame) < 30 or frame.g.nunique() < 2 or frame.y.nunique() < 2:
        return None
    x = sm.add_constant(frame[["g", "PC1", "PC2", "PC3", "PC4", "PC5"]], has_constant="add")
    fit = sm.OLS(frame.y.to_numpy(float), x.to_numpy(float)).fit()
    beta = float(fit.params[1])
    se = float(fit.bse[1])
    pval = float(fit.pvalues[1])
    return {"beta": beta, "se": se, "pval": pval, "n": int(len(frame)),
            "eaf": float(frame.g.mean()), "f_stat": float((beta / se) ** 2)}


def read_alleles(path, positions):
    positions = set(int(x) for x in positions)
    alleles = {}
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip().split("\t")
            if fields[0] not in ("1", "Chr1"):
                continue
            pos = int(fields[1])
            if pos not in positions:
                continue
            ref, alt = fields[3], fields[4]
            if len(ref) == 1 and len(alt) == 1 and ref in "ACGT" and alt in "ACGT":
                alleles[pos] = (alt, ref)
    return alleles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--outdir", default="data/real/arabidopsis_AT1G11560")
    parser.add_argument("--gene", default="AT1G11560")
    parser.add_argument("--expression-file", default="data/external/arabidopsis_gse54680/GSE54680_AT1G11560_expression.tsv")
    parser.add_argument("--p-threshold", type=float, default=5e-8)
    parser.add_argument("--maf-threshold", type=float, default=0.05)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    outdir = root / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    genotype_npz = np.load(root / "data/external/arabidopsis_1001genomes/AT1G11560_region_genotypes.npz")
    positions = genotype_npz["positions"].astype(int)
    genotypes = genotype_npz["genotypes"].astype(float)
    accessions = genotype_npz["accessions"].astype(str)
    pc = pd.read_csv(root / "data/external/arabidopsis_1001genomes/1001genomes_PC5.tsv", sep="\t", dtype={"accession_id": str}).set_index("accession_id")
    pc = pc.loc[~pc.index.duplicated(keep="first")]
    pc = pc.reindex(accessions)
    allele_map = read_alleles(
        root / "data/external/arabidopsis_1001genomes/alleles/intersection_991.vcf.gz",
        positions,
    )

    expression = pd.read_csv(root / args.expression_file, sep="\t", dtype={"accession_number": str})
    expression["accession_id"] = expression["accession_number"].astype(str)
    expression_column = args.gene + "_RPKM" if args.gene + "_RPKM" in expression.columns else "RPKM"
    expression["RPKM"] = pd.to_numeric(expression[expression_column], errors="coerce")
    expression["expression_value"] = np.log1p(expression["RPKM"])
    ft = {}
    for environment, filename in [("10C", "FT10_values.csv"), ("16C", "FT16_values.csv")]:
        values = pd.read_csv(root / "data/external/arabidopsis_arapheno" / filename, dtype={"accession_id": str})
        values["accession_id"] = values["accession_id"].astype(str)
        values["phenotype_value"] = pd.to_numeric(values["phenotype_value"], errors="coerce")
        ft[environment] = values.dropna(subset=["phenotype_value"]).drop_duplicates("accession_id").set_index("accession_id")["phenotype_value"]

    index_by_accession = {acc: i for i, acc in enumerate(accessions)}
    exposure_rows = []
    outcome_rows = []
    sample_audit = {}
    for environment, z in [("10C", -3.0), ("16C", 3.0)]:
        expr = expression.loc[expression["growth_temperature"].astype(str) == environment].drop_duplicates("accession_id").set_index("accession_id")
        expr = expr.join(pc, how="inner")
        expr = expr.dropna(subset=["expression_value"])
        out = ft[environment].to_frame("phenotype_value").join(pc, how="inner").dropna()
        expr_indices = [index_by_accession[acc] for acc in expr.index if acc in index_by_accession]
        out_indices = [index_by_accession[acc] for acc in out.index if acc in index_by_accession]
        sample_audit[environment] = {
            "expression_rows": int(len(expr_indices)),
            "outcome_rows": int(len(out_indices)),
            "expression_nonzero_RPKM": int((expr.loc[[acc for acc in expr.index if acc in index_by_accession], "RPKM"] > 0).sum()),
        }
        expr = expr.loc[[acc for acc in expr.index if acc in index_by_accession]]
        out = out.loc[[acc for acc in out.index if acc in index_by_accession]]
        for row_index, pos in enumerate(positions):
            if int(pos) not in allele_map:
                continue
            alt, ref = allele_map[int(pos)]
            g_expr = pd.Series(genotypes[row_index, [index_by_accession[acc] for acc in expr.index]], index=expr.index)
            g_out = pd.Series(genotypes[row_index, [index_by_accession[acc] for acc in out.index]], index=out.index)
            maf = min(float(g_expr.mean()), 1.0 - float(g_expr.mean()))
            if maf < args.maf_threshold:
                continue
            e = association(g_expr, expr["expression_value"], expr[["PC1", "PC2", "PC3", "PC4", "PC5"]])
            o = association(g_out, out["phenotype_value"], out[["PC1", "PC2", "PC3", "PC4", "PC5"]])
            if e is None or o is None:
                continue
            base = {
                "SNP": "Chr1:%d" % int(pos),
                "effect_allele": alt,
                "other_allele": ref,
                "environment": environment,
                "environment_value": z,
                "eaf": e["eaf"],
                "n": e["n"],
            }
            exposure_rows.append({**base, "beta": e["beta"], "se": e["se"], "pval": e["pval"], "trait": "log1p(%s_RPKM)" % args.gene})
            outcome_rows.append({**base, "beta": o["beta"], "se": o["se"], "pval": o["pval"], "trait": "flowering_time_days"})

    exposure = pd.DataFrame(exposure_rows).sort_values(["environment", "SNP"]).reset_index(drop=True)
    outcome = pd.DataFrame(outcome_rows).sort_values(["environment", "SNP"]).reset_index(drop=True)
    complete_snps = exposure.groupby("SNP")["environment"].nunique()
    complete_snps = complete_snps.index[complete_snps == 2]
    exposure = exposure[exposure.SNP.isin(complete_snps)].reset_index(drop=True)
    outcome = outcome[outcome.SNP.isin(complete_snps)].reset_index(drop=True)
    exposure.to_csv(outdir / "exposure.tsv", sep="\t", index=False)
    outcome.to_csv(outdir / "outcome.tsv", sep="\t", index=False)
    metadata = {
        "species": "Arabidopsis thaliana",
        "assembly": "TAIR10-compatible 1001 Genomes v3.1",
        "gene": args.gene,
        "exposure": "local OLS association of log1p(RPKM) with cis SNP dosage, adjusted for PC1-PC5",
        "outcome": "local OLS association of flowering-time days with the same SNP dosage, adjusted for PC1-PC5",
        "environment_values": {"10C": -3.0, "16C": 3.0},
        "p_threshold": args.p_threshold,
        "maf_threshold": args.maf_threshold,
        "sample_audit": sample_audit,
        "region_snps": int(len(positions)),
        "complete_grid_snps": int(len(complete_snps)),
        "allele_mapped_snps": int(len(allele_map)),
        "input_limitations": [
            "This is a transparent local re-analysis, not the published LMM/SMR result.",
            "The binary HDF5 dosage matrix and one accession VCF provide the genotype/allele mapping.",
            "Expression and flowering phenotypes come from related public experiments; sample-overlap covariance is not estimated.",
            "Use as an executable real-data demonstration and sensitivity analysis, not as independent functional validation.",
        ],
    }
    (outdir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"exposure_rows": len(exposure), "outcome_rows": len(outcome), "unique_snps": exposure.SNP.nunique(), "sample_audit": sample_audit}, indent=2))


if __name__ == "__main__":
    main()
