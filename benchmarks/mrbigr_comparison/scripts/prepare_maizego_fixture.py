#!/usr/bin/env python3
"""Prepare a bounded, source-traceable MRBIGR maize fixture.

Raw public files stay outside the repository.  This script creates only a
small derived fixture and a manifest describing the exact sample/variant
intersection used by PlantMR.  It does not claim to reproduce MRBIGR's
private/internally matched layers.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Iterable

import pandas as pd
import pysam


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_attrs(value: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in value.split(";"):
        if "=" in item:
            key, val = item.split("=", 1)
            result[key] = val
    return result


def read_expression(path: Path, sample_ids: list[str], n_features: int) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        positions = {sample: header.index(sample) for sample in sample_ids}
        records: list[dict[str, object]] = []
        candidates: list[tuple[float, str, list[float]]] = []
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != len(header):
                continue
            feature = fields[0]
            try:
                values = [float(fields[positions[sample]]) for sample in sample_ids]
            except (KeyError, ValueError):
                continue
            if not all(pd.notna(values)):
                continue
            variance = float(pd.Series(values).var(ddof=1))
            if variance > 0:
                candidates.append((variance, feature, values))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        for _, feature, values in candidates[:n_features]:
            for sample, value in zip(sample_ids, values):
                records.append({"sample_id": sample, "feature_id": feature, "value": value})
    if not records:
        raise RuntimeError("no complete variable expression features found")
    return pd.DataFrame(records)


def write_gff_genes(gff_path: Path, out_path: Path) -> dict[str, int]:
    sequence_to_chr: dict[str, str] = {}
    genes: list[dict[str, object]] = []
    with gzip.open(gff_path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 9:
                continue
            attrs = parse_attrs(fields[8])
            if fields[2] == "region":
                sequence_to_chr[fields[0]] = attrs.get("chromosome") or attrs.get("Name") or fields[0]
                continue
            if fields[2] != "gene":
                continue
            chromosome = sequence_to_chr.get(fields[0], fields[0])
            feature = attrs.get("gene") or attrs.get("Name") or attrs.get("ID")
            if not feature:
                continue
            genes.append(
                {
                    "feature_id": feature,
                    "gene_symbol": attrs.get("gene", attrs.get("Name", feature)),
                    "chromosome": chromosome,
                    "start": int(fields[3]),
                    "end": int(fields[4]),
                }
            )
    pd.DataFrame(genes).drop_duplicates("feature_id").to_csv(out_path, sep="\t", index=False)
    return {"genes": len(genes), "sequence_ids": len(sequence_to_chr)}


def write_go(gaf_path: Path, annotation_path: Path, selected_path: Path) -> dict[str, int]:
    records: list[dict[str, str]] = []
    for line in gzip.open(gaf_path, "rt", encoding="utf-8", errors="replace"):
        if line.startswith("!"):
            continue
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 15:
            continue
        records.append({"feature_id": fields[1], "go_term": fields[4], "term_name": fields[9] or fields[4]})
    annotation = pd.DataFrame(records).drop_duplicates(["feature_id", "go_term"])
    annotation.to_csv(annotation_path, sep="\t", index=False)
    selected = sorted(annotation["feature_id"].unique())[:100]
    pd.DataFrame({"feature_id": selected}).to_csv(selected_path, sep="\t", index=False)
    return {"go_rows": len(annotation), "go_features": int(annotation["feature_id"].nunique()), "selected_features": len(selected)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-variants", type=int, default=5000)
    parser.add_argument("--n-expression-features", type=int, default=32)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    expression_path = source / "expression_extracted" / "Expression_kernel_finalNormalized_28850.txt"
    phenotype_path = source / "blup_traits_final.csv"
    metadata_path = source / "AllZeaGBSv2.7_publicSamples_metadata20140411.xlsx"
    vcf_path = source / "hmp321_282_agpv4_chr10.vcf.gz"
    gff_path = source / "GCF_902167145.1_Zm-B73-REFERENCE-NAM-5.0_genomic.gff.gz"
    gaf_path = source / "maize.B73.AGPv4.aggregate.gaf.gz"
    required = [expression_path, phenotype_path, metadata_path, vcf_path, gff_path, gaf_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing source files: " + ", ".join(missing))

    phenotype = pd.read_csv(phenotype_path)
    phenotype = phenotype.rename(columns={phenotype.columns[0]: "sample_id"})
    phenotype["sample_id"] = phenotype["sample_id"].astype(str)
    metadata = pd.read_excel(metadata_path)
    metadata_ids = set(metadata["DNASample"].dropna().astype(str))
    with expression_path.open("r", encoding="utf-8") as handle:
        expression_samples = handle.readline().rstrip("\n").split("\t")[1:]
    expression_set = set(expression_samples)
    with pysam.VariantFile(str(vcf_path)) as source_vcf:
        vcf_samples = list(source_vcf.header.samples)
        normalized = {sample: (sample[7:] if sample.startswith("282set_") else sample) for sample in vcf_samples}
        phenotype_ids = set(phenotype["sample_id"])
        expression_common = [sample for sample in expression_samples if sample in phenotype_ids and sample in metadata_ids and sample in set(normalized.values())]
        phenotype_common = [normalized[sample] for sample in vcf_samples if normalized[sample] in phenotype_ids]
        if len(expression_common) < 3 or len(phenotype_common) < 3:
            raise RuntimeError(
                f"insufficient public overlap: expression={len(expression_common)}, phenotype={len(phenotype_common)}"
            )
        source_names = vcf_samples
        source_to_common = {sample: normalized[sample] for sample in source_names}
        genotype_records: list[dict[str, object]] = []
        variant_records: list[dict[str, object]] = []
        seen_variants: set[str] = set()
        kept = 0
        for record in source_vcf:
            if len(record.alts or ()) != 1:
                continue
            variant_id = record.id or f"{record.chrom}:{record.pos}:{record.ref}:{record.alts[0]}"
            if variant_id in seen_variants:
                continue
            dosage_by_sample: dict[str, object] = {}
            usable = True
            for source_name in source_names:
                gt = record.samples[source_name].get("GT")
                if gt is None or any(allele is None for allele in gt):
                    dosage_by_sample[source_to_common[source_name]] = float("nan")
                else:
                    dosage_by_sample[source_to_common[source_name]] = float(sum(gt))
            if all(pd.isna(value) for value in dosage_by_sample.values()):
                continue
            seen_variants.add(variant_id)
            variant_records.append({"variant_id": variant_id, "chromosome": str(record.chrom), "position": int(record.pos), "ref": record.ref, "alt": record.alts[0]})
            for sample_id, dosage in dosage_by_sample.items():
                genotype_records.append({"sample_id": sample_id, "variant_id": variant_id, "dosage": dosage})
            kept += 1
            if kept >= args.max_variants:
                break
    genotype = pd.DataFrame(genotype_records)
    genotype_wide = genotype.pivot(index="sample_id", columns="variant_id", values="dosage").reset_index()
    genotype_wide.to_csv(out / "genotype.tsv", sep="\t", index=False)
    genotype.to_csv(out / "genotype_long.tsv", sep="\t", index=False)
    pd.DataFrame(variant_records).to_csv(out / "variants.tsv", sep="\t", index=False)

    # Keep two quantitative traits from the downloaded BLUP table.
    trait_names = [name for name in ["Plantheight", "Earheight"] if name in phenotype.columns]
    if len(trait_names) < 1:
        trait_names = [column for column in phenotype.columns if column != "sample_id"][:2]
    pheno = phenotype.loc[phenotype["sample_id"].isin(phenotype_common), ["sample_id", *trait_names]].copy()
    pheno_long = pheno.melt(id_vars="sample_id", var_name="trait", value_name="value")
    pheno_long["value"] = pd.to_numeric(pheno_long["value"], errors="coerce")
    pheno_long = pheno_long.dropna(subset=["value"])
    pheno_long.to_csv(out / "phenotype.tsv", sep="\t", index=False)

    expression = read_expression(expression_path, expression_common, args.n_expression_features)
    expression.to_csv(out / "expression.tsv", sep="\t", index=False)
    gene_stats = write_gff_genes(gff_path, out / "gene_annotation.tsv")
    go_stats = write_go(gaf_path, out / "go_annotation.tsv", out / "selected_features.tsv")

    # A VCF prefix with all samples preserves a real VCF-ingestion fixture
    # while keeping the derived run bounded and auditable.
    subset_vcf = out / "genotype_prefix.vcf.gz"
    with gzip.open(vcf_path, "rt", encoding="utf-8", errors="replace") as source_handle, gzip.open(
        subset_vcf, "wt", encoding="utf-8"
    ) as target_handle:
        written = 0
        contig_added = False
        for line in source_handle:
            if line.startswith("#CHROM") and not contig_added:
                target_handle.write("##contig=<ID=10>\n")
                contig_added = True
            if line.startswith("#"):
                target_handle.write(line)
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 10 or len(fields[4].split(",")) != 1:
                continue
            target_handle.write(line)
            written += 1
            if written >= args.max_variants:
                break

    manifest = {
        "source": {
            "vcf": {"path": str(vcf_path), "sha256": sha256(vcf_path), "size_bytes": vcf_path.stat().st_size},
            "expression": {"path": str(expression_path), "sha256": sha256(expression_path), "size_bytes": expression_path.stat().st_size},
            "phenotype": {"path": str(phenotype_path), "sha256": sha256(phenotype_path), "size_bytes": phenotype_path.stat().st_size},
            "metadata": {"path": str(metadata_path), "sha256": sha256(metadata_path), "size_bytes": metadata_path.stat().st_size},
            "gff": {"path": str(gff_path), "sha256": sha256(gff_path), "size_bytes": gff_path.stat().st_size},
            "gaf": {"path": str(gaf_path), "sha256": sha256(gaf_path), "size_bytes": gaf_path.stat().st_size},
        },
        "fixture": {
            "species": "Zea mays",
            "assembly": "AGPv4",
            "vcf_chromosome": "10",
            "vcf_samples_total": len(vcf_samples),
            "vcf_phenotype_samples": len(phenotype_common),
            "vcf_phenotype_sample_ids": phenotype_common,
            "vcf_expression_samples": len(expression_common),
            "vcf_expression_sample_ids": expression_common,
            "variants_kept": len(variant_records),
            "expression_features": int(expression["feature_id"].nunique()),
            "phenotype_traits": trait_names,
            "gene_annotation": gene_stats,
            "go": go_stats,
            "limitations": [
                "The public Maizego expression and Panzea HapMap3 chr10 genotype layers overlap on 5 directly named materials; the genotype layer overlaps the downloaded BLUP phenotype table on 8 directly named materials.",
                "The VCF-derived fixture is the first bounded set of biallelic chr10 variants; it is an engineering/evidence fixture, not a genome-wide association claim.",
                "GWAS/QTL paths are transparent OLS baselines without full LD-aware mixed-model correction.",
            ],
        },
    }
    (out / "fixture_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (out / "plantmr.toml").write_text(
        "project_name = \"mrbigr-maize-public-fixture\"\n"
        "species = \"Zea_mays\"\n"
        "assembly = \"AGPv4\"\n"
        "analyses = [\"genotype-qc\", \"phenotype-qc\", \"gwas\", \"qtl\", \"go\"]\n"
        "output_dir = \"runs\"\n\n"
        "[inputs]\n"
        "genotype = \"genotype.tsv\"\n"
        "phenotype = \"phenotype.tsv\"\n"
        "expression = \"expression.tsv\"\n"
        "gene_annotation = \"gene_annotation.tsv\"\n"
        "go_annotation = \"go_annotation.tsv\"\n"
        "selected_features = \"selected_features.tsv\"\n\n"
        "[metadata]\n"
        "ploidy = 2\n"
        "source = \"MRBIGR maize public layers + Panzea HapMap3 282 panel\"\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest["fixture"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
