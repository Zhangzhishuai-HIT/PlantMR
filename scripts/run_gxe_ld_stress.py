#!/usr/bin/env python3
"""Stress-test GxE-IVW when SNP summary errors are correlated by LD."""
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


def p_from_z(z):
    return 2.0 * ndtr(-np.abs(z))


def make_case(rng, slope, n_snp=20, z_values=(-1.5, -0.5, 0.5, 1.5)):
    z_values = np.asarray(z_values, dtype=float)
    n_env = len(z_values)
    env_corr = np.full((n_env, n_env), 0.5)
    np.fill_diagonal(env_corr, 1.0)
    ld_corr = np.fromfunction(lambda i, j: 0.6 ** np.abs(i - j), (n_snp, n_snp))
    bx = np.maximum(rng.normal(0.18, 0.025, n_snp), 0.05)
    eaf = rng.uniform(0.2, 0.8, n_snp)
    sy = 0.04
    errors = rng.multivariate_normal(
        np.zeros(n_snp * n_env),
        sy ** 2 * np.kron(ld_corr, env_corr),
    ).reshape(n_snp, n_env)
    rows = []
    for j in range(n_snp):
        for k, z in enumerate(z_values):
            by = bx[j] * (0.5 + slope * z) + errors[j, k]
            rows.append({
                "SNP": "s%03d" % (j + 1),
                "environment": "E%02d" % (k + 1),
                "environment_value": z,
                "exposure_beta": bx[j],
                "exposure_se": 0.01,
                "outcome_beta": by,
                "outcome_se": sy,
                "eaf": eaf[j],
            })
    env_labels = ["E%02d" % (i + 1) for i in range(n_env)]
    snp_labels = ["s%03d" % (i + 1) for i in range(n_snp)]
    return pd.DataFrame(rows), pd.DataFrame(env_corr, index=env_labels, columns=env_labels), pd.DataFrame(ld_corr, index=snp_labels, columns=snp_labels)


def run(reps, seed, slope):
    rng = np.random.default_rng(seed)
    rows = []
    for rep in range(reps):
        table, env_corr, ld_corr = make_case(rng, slope)
        for label, env_arg, ld_arg in [
            ("correct_ld_environment", env_corr, ld_corr),
            ("diagonal_misspecified", None, None),
        ]:
            result = gxe_ivw(table, environment_correlation=env_arg, ld_correlation=ld_arg)
            rows.append({
                "scenario": "null" if slope == 0 else "causal_gxe",
                "covariance": label,
                "replicate": rep + 1,
                "true_slope": slope,
                "slope": result.slope,
                "slope_se": result.slope_se,
                "slope_pval": result.slope_pval,
                "q_pval": result.q_pval,
                "q_df": result.q_df,
            })
    return rows


def summarize(frame):
    out = []
    for (scenario, cov), g in frame.groupby(["scenario", "covariance"], sort=True):
        true = float(g.true_slope.iloc[0])
        err = g.slope - true
        out.append({
            "scenario": scenario,
            "covariance": cov,
            "replicates": len(g),
            "mean_slope": float(g.slope.mean()),
            "bias": float(err.mean()),
            "rmse": float(np.sqrt(np.mean(err ** 2))),
            "mean_se": float(g.slope_se.mean()),
            "coverage_95": float(np.mean((g.slope - 1.96 * g.slope_se <= true) & (true <= g.slope + 1.96 * g.slope_se))),
            "rejection_p05": float(np.mean(g.slope_pval < 0.05)),
            "mean_q_pval": float(g.q_pval.mean()),
        })
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20260919)
    ap.add_argument("--outdir", default="results/benchmarks/gxe_ld_stress")
    args = ap.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    rows = run(args.reps, args.seed, 0.0) + run(args.reps, args.seed + 1, 0.25)
    raw = pd.DataFrame(rows); summary = summarize(raw)
    raw.to_csv(outdir / "replicates.tsv", sep="\t", index=False)
    summary.to_csv(outdir / "summary.tsv", sep="\t", index=False)
    (outdir / "metadata.json").write_text(json.dumps({
        "seed": args.seed, "replicates_per_scenario": args.reps,
        "n_snp": 20, "n_environment": 4,
        "environment_rho": 0.5, "ld_ar1_rho": 0.6,
        "interpretation": "The diagonal comparator intentionally ignores true SNP-LD and environment correlation.",
    }, indent=2) + "\n")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
