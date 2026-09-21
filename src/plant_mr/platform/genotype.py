"""Plant genotype ingestion, quality control and population-structure utilities."""

from __future__ import annotations

from dataclasses import dataclass
import gzip
from pathlib import Path
from typing import Any, TextIO

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GenotypeQCResult:
    matrix: pd.DataFrame
    audit: dict[str, Any]


def as_genotype_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize long or wide genotype data to sample-by-variant dosage matrix."""
    if not isinstance(data, pd.DataFrame):
        raise ValueError("genotype must be a pandas DataFrame")
    if {"sample_id", "variant_id", "dosage"}.issubset(data.columns):
        if data.duplicated(["sample_id", "variant_id"]).any():
            raise ValueError("genotype long table has duplicate sample_id/variant_id pairs")
        matrix = data.pivot(index="sample_id", columns="variant_id", values="dosage")
    else:
        if "sample_id" in data.columns:
            matrix = data.set_index("sample_id").copy()
        elif not isinstance(data.index, pd.RangeIndex):
            matrix = data.copy()
        else:
            raise ValueError("genotype requires sample_id, or long columns sample_id/variant_id/dosage")
    if matrix.index.duplicated().any():
        raise ValueError("genotype sample_id values must be unique in wide format")
    if matrix.columns.duplicated().any():
        raise ValueError("genotype variant identifiers must be unique")
    if matrix.empty or matrix.shape[1] == 0:
        raise ValueError("genotype matrix has no variants")
    matrix.index = matrix.index.astype(str)
    matrix.columns = matrix.columns.astype(str)
    matrix = matrix.apply(pd.to_numeric, errors="coerce")
    values = matrix.to_numpy(dtype=float)
    if np.isinf(values).any():
        raise ValueError("genotype contains infinite dosage values")
    return matrix


def _impute(matrix: pd.DataFrame, method: str, *, ploidy: float, seed: int) -> pd.DataFrame:
    if method not in {"random", "mean0", "mean2", "mode"}:
        raise ValueError("impute must be one of: random, mean0, mean2, mode")
    result = matrix.copy()
    rng = np.random.default_rng(seed)
    for column in result.columns:
        missing = result[column].isna()
        if not missing.any():
            continue
        observed = result.loc[~missing, column].to_numpy(dtype=float)
        if len(observed) == 0:
            raise ValueError(f"cannot impute variant with no observed dosages: {column}")
        if method == "random":
            p = float(np.clip(observed.mean() / ploidy, 0.0, 1.0))
            values = rng.binomial(int(round(ploidy)), p, size=int(missing.sum())).astype(float)
        elif method == "mean0":
            values = np.repeat(np.rint(observed.mean()), int(missing.sum()))
        elif method == "mean2":
            values = np.repeat(np.round(observed.mean(), 2), int(missing.sum()))
        else:
            counts = pd.Series(observed).value_counts()
            values = np.repeat(float(counts.index[0]), int(missing.sum()))
        result.loc[missing, column] = values
    return result


def qc_genotype(
    matrix: pd.DataFrame,
    *,
    maf_threshold: float = 0.05,
    variant_missing_threshold: float = 0.10,
    sample_missing_threshold: float = 0.10,
    impute: str | None = None,
    ploidy: float = 2.0,
    seed: int = 0,
) -> GenotypeQCResult:
    """Filter genotype markers/samples and optionally impute missing dosages."""
    if not 0 <= maf_threshold <= 0.5:
        raise ValueError("maf_threshold must be within [0, 0.5]")
    if not 0 <= variant_missing_threshold <= 1 or not 0 <= sample_missing_threshold <= 1:
        raise ValueError("missingness thresholds must be within [0, 1]")
    if ploidy <= 0:
        raise ValueError("ploidy must be greater than zero")
    work = as_genotype_matrix(matrix)
    audit: dict[str, Any] = {
        "samples_input": int(work.shape[0]),
        "variants_input": int(work.shape[1]),
        "duplicate_variants_removed": 0,
        "samples_removed_missingness": 0,
        "variants_removed_missingness": 0,
        "variants_removed_maf": 0,
        "imputation": impute or "none",
        "seed": int(seed),
    }
    sample_mask = work.isna().mean(axis=1) <= sample_missing_threshold
    audit["samples_removed_missingness"] = int((~sample_mask).sum())
    work = work.loc[sample_mask].copy()
    if work.empty:
        raise ValueError("all samples failed genotype missingness filtering")
    variant_mask = work.isna().mean(axis=0) <= variant_missing_threshold
    audit["variants_removed_missingness"] = int((~variant_mask).sum())
    work = work.loc[:, variant_mask].copy()
    if work.shape[1] == 0:
        raise ValueError("all variants failed genotype missingness filtering")
    observed_mean = work.mean(axis=0, skipna=True)
    maf = np.minimum(observed_mean / ploidy, 1.0 - observed_mean / ploidy)
    maf_mask = maf >= maf_threshold
    audit["variants_removed_maf"] = int((~maf_mask).sum())
    work = work.loc[:, maf_mask].copy()
    if work.shape[1] == 0:
        raise ValueError("all variants failed MAF filtering")
    if impute is not None:
        work = _impute(work, impute, ploidy=ploidy, seed=seed)
    audit["samples_output"] = int(work.shape[0])
    audit["variants_output"] = int(work.shape[1])
    audit["remaining_missing_values"] = int(work.isna().sum().sum())
    return GenotypeQCResult(work, audit)


def pca_scores(matrix: pd.DataFrame, n_components: int = 10) -> pd.DataFrame:
    """Compute deterministic dosage PCA scores after column-mean imputation."""
    if n_components <= 0:
        raise ValueError("n_components must be positive")
    work = as_genotype_matrix(matrix).astype(float)
    work = work.fillna(work.mean(axis=0))
    values = work.to_numpy(dtype=float)
    centered = values - centered_mean(values)
    scales = centered.std(axis=0, ddof=1)
    scales[scales == 0] = 1.0
    standardized = centered / scales
    u, singular, _ = np.linalg.svd(standardized, full_matrices=False)
    count = min(n_components, u.shape[1])
    scores = u[:, :count] * singular[:count]
    return pd.DataFrame(scores, index=work.index, columns=[f"PC{i}" for i in range(1, count + 1)])


def centered_mean(values: np.ndarray) -> np.ndarray:
    return np.mean(values, axis=0)


def kinship_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """Return a standardized additive genomic relationship matrix."""
    work = as_genotype_matrix(matrix).astype(float)
    work = work.fillna(work.mean(axis=0))
    values = work.to_numpy(dtype=float)
    centered = values - centered_mean(values)
    scales = centered.std(axis=0, ddof=1)
    scales[scales == 0] = 1.0
    standardized = centered / scales
    kinship = standardized @ standardized.T / max(1, standardized.shape[1])
    return pd.DataFrame(kinship, index=work.index, columns=work.index)


def genotype_from_vcf(path: str | Path) -> pd.DataFrame:
    """Read biallelic or multi-allelic GT dosages from a text VCF."""
    path = Path(path)
    opener = gzip.open if path.name.endswith(".gz") else open
    header: list[str] | None = None
    rows: list[list[float]] = []
    variant_ids: list[str] = []
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                header = line.rstrip("\n").split("\t")
                continue
            if not line.strip():
                continue
            if header is None:
                raise ValueError("VCF is missing #CHROM header")
            fields = line.rstrip("\n").split("\t")
            if len(fields) != len(header):
                raise ValueError("VCF record has a different number of fields than its header")
            chrom, pos, variant_id, ref, alt = fields[:5]
            key = variant_id if variant_id != "." else f"{chrom}:{pos}:{ref}:{alt}"
            if key in variant_ids:
                raise ValueError(f"duplicate VCF variant identifier: {key}")
            variant_ids.append(key)
            calls: list[float] = []
            for sample in fields[9:]:
                gt = sample.split(":", 1)[0]
                if "." in gt:
                    calls.append(np.nan)
                    continue
                alleles = gt.replace("|", "/").split("/")
                try:
                    calls.append(float(sum(int(allele) for allele in alleles)))
                except ValueError as exc:
                    raise ValueError(f"invalid VCF genotype field: {gt}") from exc
            rows.append(calls)
    if header is None:
        raise ValueError("VCF is missing #CHROM header")
    samples = header[9:]
    if not samples:
        raise ValueError("VCF contains no samples")
    return pd.DataFrame(np.asarray(rows, dtype=float).T, index=samples, columns=variant_ids)


def read_genotype(path: str | Path) -> pd.DataFrame:
    """Read VCF or a tabular genotype matrix."""
    path = Path(path)
    if path.name.endswith(".vcf") or path.name.endswith(".vcf.gz"):
        return genotype_from_vcf(path)
    from .contracts import read_table

    return as_genotype_matrix(read_table(path))


def tsne_scores(
    matrix: pd.DataFrame,
    *,
    n_components: int = 2,
    perplexity: float = 30.0,
    seed: int = 17,
) -> pd.DataFrame:
    """Compute deterministic t-SNE coordinates for population exploration."""
    if n_components != 2:
        raise ValueError("PlantMR t-SNE output currently requires n_components=2")
    work = as_genotype_matrix(matrix).astype(float).fillna(0.0)
    if len(work) < 3:
        raise ValueError("t-SNE requires at least three samples")
    from sklearn.manifold import TSNE

    effective_perplexity = min(float(perplexity), max(1.0, (len(work) - 1) / 3.0))
    coordinates = TSNE(
        n_components=2,
        perplexity=effective_perplexity,
        random_state=seed,
        init="pca",
        learning_rate="auto",
    ).fit_transform(work.to_numpy(dtype=float))
    return pd.DataFrame(coordinates, index=work.index, columns=["TSNE1", "TSNE2"])


def upgma_newick(matrix: pd.DataFrame) -> str:
    """Construct a deterministic UPGMA Newick tree from genotype distances."""
    from scipy.cluster.hierarchy import linkage, to_tree
    from scipy.spatial.distance import pdist

    work = as_genotype_matrix(matrix).astype(float).fillna(0.0)
    if len(work) < 2:
        raise ValueError("UPGMA requires at least two samples")
    tree = to_tree(linkage(pdist(work.to_numpy(dtype=float)), method="average"), rd=False)

    def render(node, parent_distance: float) -> str:
        branch = max(0.0, parent_distance - float(node.dist))
        if node.is_leaf():
            return f"{work.index[node.id]}:{branch:.8g}"
        left = render(node.left, float(node.dist))
        right = render(node.right, float(node.dist))
        return f"({left},{right}):{branch:.8g}"

    return render(tree, float(tree.dist)) + ";"
