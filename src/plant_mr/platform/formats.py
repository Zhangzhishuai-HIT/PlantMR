"""Lightweight plant genotype format readers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def read_plink_raw(path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(path, sep=r"\s+", engine="python")
    if "IID" not in data.columns:
        raise ValueError("PLINK .raw requires IID column")
    fixed = {"FID", "IID", "PAT", "MAT", "SEX", "PHENOTYPE"}
    variant_columns = [column for column in data.columns if column not in fixed]
    if not variant_columns:
        raise ValueError("PLINK .raw contains no variant columns")
    result = data.set_index("IID")[variant_columns].apply(pd.to_numeric, errors="coerce")
    result.columns = [str(column).rsplit("_", 1)[0] for column in result.columns]
    if result.columns.duplicated().any():
        raise ValueError("PLINK .raw variant identifiers become duplicated after allele suffix removal")
    return result


def _hapmap_dosage(call: str, ref: str, alt: str) -> float:
    call = str(call).upper().replace("/", "").replace("|", "")
    if not call or "N" in call or "-" in call or "." in call:
        return np.nan
    if len(call) != 2 or any(base not in {ref, alt} for base in call):
        raise ValueError(f"invalid HapMap genotype call: {call}")
    return float(call.count(alt))


def read_hapmap(path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(path, sep="\t", dtype=str)
    required = {"rs#", "alleles", "chrom", "pos"}
    if not required.issubset(data.columns):
        raise ValueError(f"HapMap input missing columns: {', '.join(sorted(required - set(data.columns)))}")
    fixed_end = list(data.columns).index("QCcode") + 1 if "QCcode" in data.columns else 10
    sample_names = list(data.columns[fixed_end:])
    if not sample_names:
        raise ValueError("HapMap input contains no samples")
    result = pd.DataFrame(index=sample_names)
    for row in data.itertuples(index=False):
        variant = str(getattr(row, "_0")) if False else str(row[0])
        alleles = str(row[1]).split("/")
        if len(alleles) != 2:
            raise ValueError(f"invalid HapMap alleles for {variant}")
        ref, alt = alleles[0].upper(), alleles[1].upper()
        calls = [
            _hapmap_dosage(call, ref, alt)
            for call in row[fixed_end:]
        ]
        result[variant] = calls
    result.index = result.index.astype(str)
    return result
