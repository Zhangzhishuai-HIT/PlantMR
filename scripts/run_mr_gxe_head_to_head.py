#!/usr/bin/env python3
"""Fair shared-input comparison of PlantMR and summary-data MR-GxE.

The comparator follows the three-step summary-data MR-GxE construction in
Spiller et al. (2019): a fixed exposure-only weighted allele score is formed
within each prespecified environment stratum, then score-outcome associations
are regressed on score-exposure associations. The methods have different
estimands; the output therefore reports method-specific targets and leaves
bias/coverage undefined when the target is not identified by that method.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from plant_mr.comparators import summary_mr_gxe  # noqa: E402
from plant_mr.gxe import gxe_ivw  # noqa: E402


def simulate_case(rng, scenario, n_snp=20, env_values=(-1.5, -0.5, 0.5, 1.5)):
    z = np.asarray(env_values, dtype=float)
    n_env = len(z)
    env_corr = np.full((n_env, n_env), 0.5, dtype=float)
    np.fill_diagonal(env_corr, 1.0)
    ld_corr = np.eye(n_snp, dtype=float)
    base = np.maximum(rng.normal(0.18, 0.025, n_snp), 0.05)
    exposure_slope = 0.35
    causal_intercept = 0.5
    causal_slope = 0.25 if scenario == "environment_effect_heterogeneity" else 0.0
    if scenario == "constant_null_directional_pleiotropy":
        causal_intercept = 0.0
    pleiotropy = 0.04 if "directional_pleiotropy" in scenario else 0.0
    sx = 0.01
    sy = 0.04
    bx_true = base[:, None] * (1.0 + exposure_slope * z[None, :])
    bx_noise = rng.multivariate_normal(
        np.zeros(n_snp * n_env), sx ** 2 * np.kron(ld_corr, env_corr)
    ).reshape(n_snp, n_env)
    by_noise = rng.multivariate_normal(
        np.zeros(n_snp * n_env), sy ** 2 * np.kron(ld_corr, env_corr)
    ).reshape(n_snp, n_env)
    bx = bx_true + bx_noise
    by = bx_true * (causal_intercept + causal_slope * z[None, :]) + pleiotropy + by_noise
    rows = []
    for j in range(n_snp):
        for k, value in enumerate(z):
            rows.append({
                "SNP": "s%03d" % (j + 1),
                "environment": "E%02d" % (k + 1),
                "environment_value": value,
                "exposure_beta": bx[j, k],
                "exposure_se": sx,
                "outcome_beta": by[j, k],
                "outcome_se": sy,
                "eaf": rng.uniform(0.2, 0.8),
            })
    table = pd.DataFrame(rows)
    env_labels = ["E%02d" % (i + 1) for i in range(n_env)]
    snp_labels = ["s%03d" % (i + 1) for i in range(n_snp)]
    return table, pd.DataFrame(env_corr, index=env_labels, columns=env_labels), pd.DataFrame(ld_corr, index=snp_labels, columns=snp_labels), {
        "causal_intercept": causal_intercept,
        "causal_slope": causal_slope,
        "exposure_slope": exposure_slope,
        "pleiotropy": pleiotropy,
    }


def run(reps, seed):
    scenarios = [
        "constant_null_directional_pleiotropy",
        "constant_effect_no_pleiotropy",
        "constant_effect_directional_pleiotropy",
        "environment_effect_heterogeneity",
    ]
    records = []
    for scenario_index, scenario in enumerate(scenarios):
        rng = np.random.default_rng(seed + scenario_index)
        for rep in range(reps):
            table, env_corr, ld_corr, truth = simulate_case(rng, scenario)
            results = {}
            try:
                results["PlantMR"] = gxe_ivw(table, environment_correlation=env_corr, ld_correlation=ld_corr)
            except Exception as exc:  # preserve failures as evidence
                results["PlantMR_error"] = str(exc)
            try:
                results["summary_MR_GxE"] = summary_mr_gxe(table, environment_correlation=env_corr, ld_correlation=ld_corr)
            except Exception as exc:
                results["summary_MR_GxE_error"] = str(exc)
            for method in ["PlantMR", "summary_MR_GxE"]:
                if method == "PlantMR" and method in results:
                    result = results[method]
                    estimate = result.slope
                    se = result.slope_se
                    pval = result.slope_pval
                    true_parameter = truth["causal_slope"] if truth["pleiotropy"] == 0 else np.nan
                    parameter = "environment_slope"
                    intercept = result.intercept
                elif method == "summary_MR_GxE" and method in results:
                    result = results[method]
                    estimate = result.causal_slope
                    se = result.causal_slope_se
                    pval = result.causal_slope_pval
                    true_parameter = truth["causal_intercept"] if truth["causal_slope"] == 0 else np.nan
                    parameter = "causal_effect"
                    intercept = result.pleiotropy_intercept
                else:
                    error_key = method + "_error"
                    records.append({
                        "scenario": scenario, "replicate": rep + 1, "method": method,
                        "parameter": "", "estimate": np.nan, "se": np.nan,
                        "pval": np.nan, "true_parameter": np.nan, "intercept": np.nan,
                        "failure": results.get(error_key, "unknown failure"),
                    })
                    continue
                records.append({
                    "scenario": scenario, "replicate": rep + 1, "method": method,
                    "parameter": parameter, "estimate": float(estimate), "se": float(se),
                    "pval": float(pval), "true_parameter": float(true_parameter) if np.isfinite(true_parameter) else np.nan,
                    "intercept": float(intercept), "failure": "",
                })
    return records


def summarize(records):
    frame = pd.DataFrame(records)
    rows = []
    for (scenario, method), group in frame.groupby(["scenario", "method"], sort=True):
        ok = group[group["failure"] == ""].copy()
        defined = ok[np.isfinite(ok["true_parameter"])]
        row = {
            "scenario": scenario, "method": method, "replicates": len(group),
            "successful": len(ok), "failure_rate": 1.0 - len(ok) / len(group),
            "parameter": ok["parameter"].iloc[0] if len(ok) else "",
            "mean_estimate": float(ok["estimate"].mean()) if len(ok) else np.nan,
            "mean_intercept": float(ok["intercept"].mean()) if len(ok) else np.nan,
            "true_parameter": float(defined["true_parameter"].iloc[0]) if len(defined) else np.nan,
            "target_defined": bool(len(defined)),
        }
        if len(defined):
            err = defined["estimate"] - defined["true_parameter"]
            row.update({
                "bias": float(err.mean()),
                "rmse": float(np.sqrt(np.mean(err ** 2))),
                "mean_se": float(defined["se"].mean()),
                "coverage_95": float(np.mean((defined["estimate"] - 1.96 * defined["se"] <= defined["true_parameter"]) & (defined["true_parameter"] <= defined["estimate"] + 1.96 * defined["se"]))),
                "rejection_p05": float(np.mean(defined["pval"] < 0.05)),
            })
        else:
            row.update({"bias": np.nan, "rmse": np.nan, "mean_se": np.nan, "coverage_95": np.nan, "rejection_p05": np.nan})
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20260920)
    ap.add_argument("--outdir", default="results/benchmarks/mr_gxe_head_to_head")
    args = ap.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    records = run(args.reps, args.seed)
    raw = pd.DataFrame(records); summary = summarize(records)
    raw.to_csv(outdir / "replicates.tsv", sep="\t", index=False)
    summary.to_csv(outdir / "summary.tsv", sep="\t", index=False)
    metadata = {
        "seed": args.seed, "replicates_per_scenario": args.reps,
        "n_snp": 20, "n_environment": 4, "environment_rho": 0.5,
        "ld_structure": "identity (same independent-SNP contract for both methods)",
        "external_method": "summary-data MR-GxE three-step weighted-score regression",
        "external_reference": "Spiller et al. 2019, https://doi.org/10.1093/ije/dyy204",
        "fairness": [
            "same simulated summary-statistics table",
            "same SNPs and environment strata",
            "same signed environment covariance",
            "exposure-only weights for the external score",
            "method-specific estimands; undefined target cells are not scored as bias or coverage",
        ],
        "scenarios": {
            "constant_null_directional_pleiotropy": "MR-GxE causal target is zero; PlantMR environment slope is not scored because pleiotropy makes it non-causal.",
            "constant_effect_no_pleiotropy": "Both methods have a defined causal/heterogeneity target under no pleiotropy.",
            "constant_effect_directional_pleiotropy": "MR-GxE is designed for constant causal effect plus constant pleiotropy; PlantMR slope is diagnostic, not a causal target.",
            "environment_effect_heterogeneity": "PlantMR has a defined environment slope; summary MR-GxE invariant-effect target is not scored.",
        },
    }
    (outdir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
