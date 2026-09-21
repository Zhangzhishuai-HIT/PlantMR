"""Lead-SNP haplotype summaries for post-GWAS interpretation."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def summarize_haplotypes(
    genotype: pd.DataFrame,
    phenotype: pd.Series | pd.DataFrame,
    *,
    lead_variants: Iterable[str],
) -> pd.DataFrame:
    """Group samples by exact lead-variant dosage patterns and summarize a trait."""
    lead_variants = [str(value) for value in lead_variants]
    missing = sorted(set(lead_variants) - set(genotype.columns))
    if missing:
        raise ValueError(f"haplotype genotype is missing lead variants: {', '.join(missing)}")
    if isinstance(phenotype, pd.DataFrame):
        if phenotype.shape[1] != 1:
            raise ValueError("phenotype DataFrame must contain exactly one trait")
        phenotype = phenotype.iloc[:, 0]
    phenotype = pd.to_numeric(phenotype, errors="coerce")
    samples = genotype.index.intersection(phenotype.dropna().index)
    if len(samples) == 0:
        raise ValueError("haplotype and phenotype have no overlapping non-missing samples")
    work = genotype.loc[samples, lead_variants].apply(pd.to_numeric, errors="coerce")
    y = phenotype.loc[samples]
    complete = ~work.isna().any(axis=1)
    work = work.loc[complete]
    y = y.loc[work.index]
    if work.empty:
        raise ValueError("no complete lead-variant haplotypes remain")
    haplotype = work.astype(int).astype(str).agg("/".join, axis=1)
    records = []
    for label, values in y.groupby(haplotype, sort=True):
        values = values.astype(float)
        records.append(
            {
                "haplotype": str(label),
                "n": int(len(values)),
                "mean": float(values.mean()),
                "se": float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else np.nan,
            }
        )
    return pd.DataFrame(records).sort_values("haplotype", kind="mergesort").reset_index(drop=True)
