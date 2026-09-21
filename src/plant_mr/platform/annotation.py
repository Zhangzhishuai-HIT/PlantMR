"""Plant variant-to-gene and functional annotation helpers."""

from __future__ import annotations

import pandas as pd


def annotate_variants(
    variants: pd.DataFrame,
    genes: pd.DataFrame,
    *,
    flank: int = 2000,
) -> pd.DataFrame:
    required_v = {"variant_id", "chromosome", "position"}
    required_g = {"feature_id", "chromosome", "start", "end"}
    if not required_v.issubset(variants.columns):
        raise ValueError(f"variants missing columns: {', '.join(sorted(required_v - set(variants.columns)))}")
    if not required_g.issubset(genes.columns):
        raise ValueError(f"genes missing columns: {', '.join(sorted(required_g - set(genes.columns)))}")
    if flank < 0:
        raise ValueError("flank must be non-negative")
    gene_table = genes.copy()
    gene_table["start"] = pd.to_numeric(gene_table["start"], errors="coerce")
    gene_table["end"] = pd.to_numeric(gene_table["end"], errors="coerce")
    if gene_table[["start", "end"]].isna().any().any():
        raise ValueError("gene start/end must be numeric")
    records = []
    for variant in variants.itertuples(index=False):
        chromosome = str(variant.chromosome)
        position = int(variant.position)
        candidates = gene_table.loc[
            (gene_table["chromosome"].astype(str) == chromosome)
            & (gene_table["end"] >= position - flank)
            & (gene_table["start"] <= position + flank)
        ].copy()
        if candidates.empty:
            records.append({"variant_id": str(variant.variant_id), "gene_id": "", "gene_symbol": "", "relationship": "intergenic"})
            continue
        candidates["distance"] = candidates.apply(
            lambda row: 0 if row["start"] <= position <= row["end"] else min(abs(position - row["start"]), abs(position - row["end"])),
            axis=1,
        )
        row = candidates.sort_values(["distance", "feature_id"], kind="mergesort").iloc[0]
        if row["start"] <= position <= row["end"]:
            relationship = "within"
        else:
            relationship = "nearest"
        records.append(
            {
                "variant_id": str(variant.variant_id),
                "gene_id": str(row["feature_id"]),
                "gene_symbol": str(row.get("gene_symbol", row["feature_id"])),
                "relationship": relationship,
                "distance": int(row["distance"]),
            }
        )
    return pd.DataFrame(records)
