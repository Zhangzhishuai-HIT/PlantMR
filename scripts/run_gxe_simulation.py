#!/usr/bin/env python3
"""Deterministic simulation benchmark for PlantMR GxE-IVW.

The benchmark is deliberately separate from biological data. It evaluates the
estimand and covariance implementation, not a claim about any crop trait.
"""

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.special import ndtr


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from plant_mr.gxe import gxe_ivw  # noqa: E402


def _p_from_z(z):
    return 2.0 * ndtr(-np.abs(z))


def simulate_table(rng, intercept, slope, n_snp=20, env_values=(-1.5, -0.5, 0.5, 1.5),
                   outcome_se=0.04, exposure_se=0.01, environment_corr=0.5,
                   directional_pleiotropy=0.0):
    env_values = np.asarray(env_values, dtype=float)
    n_env = len(env_values)
    corr = np.full((n_env, n_env), environment_corr, dtype=float)
    np.fill_diagonal(corr, 1.0)
    bx_values = rng.normal(0.18, 0.025, size=n_snp)
    bx_values = np.maximum(bx_values, 0.05)
    eaf_values = rng.uniform(0.2, 0.8, size=n_snp)
    rows = []
    for j in range(n_snp):
        noise = rng.multivariate_normal(np.zeros(n_env), outcome_se ** 2 * corr)
        for k, z in enumerate(env_values):
            bx = bx_values[j]
            by = bx * (intercept + slope * z) + directional_pleiotropy + noise[k]
            rows.append({
                "SNP": "s%03d" % (j + 1),
                "environment": "E%02d" % (k + 1),
                "environment_value": z,
                "exposure_beta": bx,
                "exposure_se": exposure_se,
                "exposure_pval": float(_p_from_z(bx / exposure_se)),
                "outcome_beta": by,
                "outcome_se": outcome_se,
                "outcome_pval": float(_p_from_z(by / outcome_se)),
                "eaf": eaf_values[j],
            })
    return pd.DataFrame(rows), pd.DataFrame(corr, index=["E%02d" % (i + 1) for i in range(n_env)],
                                              columns=["E%02d" % (i + 1) for i in range(n_env)])


def run_scenario(name, true_intercept, true_slope, reps, seed, use_correlation, directional_pleiotropy=0.0):
    rng = np.random.default_rng(seed)
    records = []
    for rep in range(reps):
        table, corr = simulate_table(
            rng, true_intercept, true_slope,
            directional_pleiotropy=directional_pleiotropy,
        )
        result = gxe_ivw(table, environment_correlation=corr if use_correlation else None)
        records.append({
            "scenario": name,
            "replicate": rep + 1,
            "covariance": "environment" if use_correlation else "diagonal",
            "true_intercept": true_intercept,
            "true_slope": true_slope,
            "intercept": result.intercept,
            "slope": result.slope,
            "intercept_se": result.intercept_se,
            "slope_se": result.slope_se,
            "intercept_pval": result.intercept_pval,
            "slope_pval": result.slope_pval,
            "q_pval": result.q_pval,
        })
    return records


def summarize(records):
    frame = pd.DataFrame(records)
    rows = []
    for (scenario, covariance), group in frame.groupby(["scenario", "covariance"], sort=True):
        true_slope = float(group["true_slope"].iloc[0])
        slope_error = group["slope"] - true_slope
        true_intercept = float(group["true_intercept"].iloc[0])
        intercept_error = group["intercept"] - true_intercept
        z = slope_error / group["slope_se"]
        rows.append({
            "scenario": scenario,
            "covariance": covariance,
            "replicates": int(len(group)),
            "true_slope": true_slope,
            "true_intercept": true_intercept,
            "mean_intercept": float(group["intercept"].mean()),
            "bias_intercept": float(intercept_error.mean()),
            "coverage_95_intercept": float(np.mean((group["intercept"] - 1.96 * group["intercept_se"] <= true_intercept) & (true_intercept <= group["intercept"] + 1.96 * group["intercept_se"]))),
            "mean_slope": float(group["slope"].mean()),
            "bias_slope": float(slope_error.mean()),
            "rmse_slope": float(np.sqrt(np.mean(slope_error ** 2))),
            "mean_slope_se": float(group["slope_se"].mean()),
            "coverage_95_slope": float(np.mean((group["slope"] - 1.96 * group["slope_se"] <= true_slope) & (true_slope <= group["slope"] + 1.96 * group["slope_se"]))),
            "rejection_p05_slope": float(np.mean(group["slope_pval"] < 0.05)),
            "mean_q_pval": float(group["q_pval"].mean()),
            "mean_abs_z_error": float(np.mean(np.abs(z))),
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reps", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260918)
    parser.add_argument("--outdir", default="results/benchmarks/gxe_simulation")
    args = parser.parse_args()
    if args.reps < 20:
        raise SystemExit("--reps must be at least 20")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    records = []
    records += run_scenario("null", 0.5, 0.0, args.reps, args.seed, True)
    records += run_scenario("null", 0.5, 0.0, args.reps, args.seed + 1, False)
    records += run_scenario("causal_gxe", 0.5, 0.25, args.reps, args.seed + 2, True)
    records += run_scenario("causal_gxe", 0.5, 0.25, args.reps, args.seed + 3, False)
    records += run_scenario("directional_pleiotropy", 0.5, 0.0, args.reps, args.seed + 4, True, directional_pleiotropy=0.04)
    records += run_scenario("directional_pleiotropy", 0.5, 0.0, args.reps, args.seed + 5, False, directional_pleiotropy=0.04)
    raw = pd.DataFrame(records)
    summary = summarize(records)
    raw.to_csv(outdir / "replicates.tsv", sep="\t", index=False)
    summary.to_csv(outdir / "summary.tsv", sep="\t", index=False)
    payload = {
        "seed": args.seed,
        "replicates_per_scenario": args.reps,
        "n_snp": 20,
        "n_environment": 4,
        "environment_correlation": 0.5,
        "scenarios": ["null", "causal_gxe", "directional_pleiotropy"],
        "interpretation": "Simulation-only evidence; no row is a biological result.",
    }
    (outdir / "metadata.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
