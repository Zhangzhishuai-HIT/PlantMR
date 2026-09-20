"""SMR/HEIDI summary-statistic integration for molecular traits."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..schema import validate_summary


def run_smr_heidi(
    exposure: pd.DataFrame,
    outcome: pd.DataFrame,
    *,
    feature_column: str = "feature_id",
    exposure_p_threshold: float | None = 5e-8,
) -> pd.DataFrame:
    """Estimate SMR effects and a summary-data HEIDI heterogeneity statistic.

    ``exposure`` contains one or more molecular features and the standard
    summary-statistic columns plus ``feature_id``. ``outcome`` contains the
    same SNP-level columns. Effect alleles must already be harmonized; this
    function rejects incompatible alleles and flips reversed outcome alleles.
    It assumes independent exposure and outcome samples and does not model
    LD or sample-overlap covariance.
    """
    if feature_column not in exposure.columns:
        raise ValueError(f"exposure: missing feature column: {feature_column}")
    exp = validate_summary(exposure, "exposure").data.copy()
    out = validate_summary(outcome, "outcome").data.copy()
    if exposure_p_threshold is not None and exposure_p_threshold <= 0:
        raise ValueError("exposure_p_threshold must be positive or None")

    out = out.rename(
        columns={
            "effect_allele": "out_effect_allele",
            "other_allele": "out_other_allele",
            "beta": "out_beta",
            "se": "out_se",
            "pval": "out_pval",
            "eaf": "out_eaf",
        }
    )
    exp = exp.rename(
        columns={
            "effect_allele": "exp_effect_allele",
            "other_allele": "exp_other_allele",
            "beta": "exp_beta",
            "se": "exp_se",
            "pval": "exp_pval",
            "eaf": "exp_eaf",
        }
    )
    merged = exp.merge(out, on="SNP", how="inner", suffixes=("", "_out"))
    if merged.empty:
        raise ValueError("exposure and outcome have no shared SNPs")
    aligned_rows = []
    for row in merged.itertuples(index=False):
        if (row.out_effect_allele, row.out_other_allele) == (
            row.exp_effect_allele,
            row.exp_other_allele,
        ):
            sign = 1.0
        elif (row.out_effect_allele, row.out_other_allele) == (
            row.exp_other_allele,
            row.exp_effect_allele,
        ):
            sign = -1.0
        else:
            continue
        item = row._asdict()
        item["out_beta"] = sign * float(item["out_beta"])
        aligned_rows.append(item)
    if not aligned_rows:
        raise ValueError("no shared SNPs had compatible effect alleles")
    aligned = pd.DataFrame(aligned_rows)

    results = []
    for feature, group in aligned.groupby(feature_column, sort=True):
        group = group.copy()
        if exposure_p_threshold is not None:
            eligible = group.loc[group["exp_pval"] <= exposure_p_threshold]
        else:
            eligible = group
        if eligible.empty:
            results.append(
                {
                    "feature_id": str(feature),
                    "top_snp": "",
                    "nsnp_shared": int(len(group)),
                    "smr_beta": np.nan,
                    "smr_se": np.nan,
                    "smr_pval": np.nan,
                    "heidi_q": np.nan,
                    "heidi_df": 0,
                    "heidi_pval": np.nan,
                    "status": "no_exposure_instrument",
                }
            )
            continue
        top = eligible.sort_values(["exp_pval", "SNP"], kind="mergesort").iloc[0]
        bx = float(top["exp_beta"])
        by = float(top["out_beta"])
        sx = float(top["exp_se"])
        sy = float(top["out_se"])
        if bx == 0:
            results.append(
                {
                    "feature_id": str(feature),
                    "top_snp": str(top["SNP"]),
                    "nsnp_shared": int(len(group)),
                    "smr_beta": np.nan,
                    "smr_se": np.nan,
                    "smr_pval": np.nan,
                    "heidi_q": np.nan,
                    "heidi_df": 0,
                    "heidi_pval": np.nan,
                    "status": "zero_exposure_effect",
                }
            )
            continue
        smr_beta = by / bx
        smr_var = (sy * sy) / (bx * bx) + ((by * by) * (sx * sx)) / (bx**4)
        smr_se = float(np.sqrt(smr_var))
        smr_pval = float(2 * stats.norm.sf(abs(smr_beta / smr_se))) if smr_se > 0 else np.nan

        valid = group.loc[group["exp_beta"].abs() > 0].copy()
        ratio = valid["out_beta"].to_numpy(dtype=float) / valid["exp_beta"].to_numpy(dtype=float)
        ratio_var = (
            valid["out_se"].to_numpy(dtype=float) ** 2 / valid["exp_beta"].to_numpy(dtype=float) ** 2
            + valid["out_beta"].to_numpy(dtype=float) ** 2
            * valid["exp_se"].to_numpy(dtype=float) ** 2
            / valid["exp_beta"].to_numpy(dtype=float) ** 4
        )
        finite = np.isfinite(ratio) & np.isfinite(ratio_var) & (ratio_var > 0)
        ratio = ratio[finite]
        ratio_var = ratio_var[finite]
        if len(ratio) < 2:
            heidi_q, heidi_df, heidi_pval, status = np.nan, 0, np.nan, "heidi_not_testable"
        else:
            weights = 1.0 / ratio_var
            weighted_mean = float(np.sum(weights * ratio) / np.sum(weights))
            heidi_q = float(np.sum(weights * (ratio - weighted_mean) ** 2))
            heidi_df = int(len(ratio) - 1)
            heidi_pval = float(stats.chi2.sf(heidi_q, heidi_df))
            status = "heterogeneity" if heidi_pval < 0.01 else "pass"
        results.append(
            {
                "feature_id": str(feature),
                "top_snp": str(top["SNP"]),
                "nsnp_shared": int(len(group)),
                "smr_beta": float(smr_beta),
                "smr_se": smr_se,
                "smr_pval": smr_pval,
                "heidi_q": heidi_q,
                "heidi_df": heidi_df,
                "heidi_pval": heidi_pval,
                "status": status,
            }
        )
    return pd.DataFrame(results)
