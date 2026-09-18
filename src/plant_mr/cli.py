import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from .analysis import PairAnalysis, analyze_pair
from .gxe import gxe_ivw, select_gxe_instruments
from .report import write_report
from .schema import SchemaError, read_summary, validate_summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="plantmr", description="Plant-native Mendelian randomization toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate summary statistics and metadata")
    validate.add_argument("--exposure", required=True)
    validate.add_argument("--outcome", required=True)
    validate.add_argument("--metadata", required=True)
    for name, help_text in (("run", "run summary-level MR"), ("run-stratified", "run MR separately by environment")):
        run = sub.add_parser(name, help=help_text)
        run.add_argument("--exposure", required=True)
        run.add_argument("--outcome", required=True)
        run.add_argument("--metadata", required=True)
        run.add_argument("--outdir", required=True)
        run.add_argument("--p-threshold", type=float, default=5e-8)
        run.add_argument("--f-threshold", type=float, default=10.0)
        run.add_argument("--maf-threshold", type=float, default=0.01)
        run.add_argument("--ld-matrix", default=None, help="square TSV/CSV LD correlation matrix")
        run.add_argument("--ld-r2", type=float, default=0.01)
    gxe = sub.add_parser("run-gxe", help="run covariance-aware environment-interaction MR")
    gxe.add_argument("--exposure", required=True)
    gxe.add_argument("--outcome", required=True)
    gxe.add_argument("--metadata", required=True)
    gxe.add_argument("--outdir", required=True)
    gxe.add_argument("--p-threshold", type=float, default=5e-8)
    gxe.add_argument("--f-threshold", type=float, default=10.0)
    gxe.add_argument("--maf-threshold", type=float, default=0.01)
    gxe.add_argument("--environment-correlation", default=None,
                      help="square TSV/CSV environment correlation matrix")
    gxe.add_argument("--ld-correlation", default=None,
                      help="square TSV/CSV SNP LD correlation matrix")
    return parser


def _metadata(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("metadata must be a JSON object")
    return data


def _read_table(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python")


def _read_ld(path: str | None) -> pd.DataFrame | None:
    if path is None:
        return None
    matrix = pd.read_csv(path, sep=None, engine="python", index_col=0)
    matrix.index = matrix.index.astype(str)
    matrix.columns = matrix.columns.astype(str)
    return matrix


def _read_correlation(path: str | None) -> pd.DataFrame | None:
    return _read_ld(path)


def _warnings(metadata: dict, ld_matrix, stratified: bool = False) -> list[str]:
    warnings = []
    if ld_matrix is None:
        warnings.append("No LD correlation matrix was supplied; independence/clumping was not re-verified.")
    if not metadata.get("ld_panel"):
        warnings.append("LD panel provenance is absent from metadata.")
    if stratified:
        warnings.append("Environment-specific estimates are not a substitute for a preregistered G×E causal model.")
    warnings.append("MR evidence does not replace colocalization, functional validation, or gene editing.")
    return warnings


def _config(args) -> dict:
    return {
        "tool_version": "1.1.0",
        "command": args.command,
        "p_threshold": args.p_threshold,
        "f_threshold": args.f_threshold,
        "maf_threshold": args.maf_threshold,
        "ld_r2": args.ld_r2,
        "input_exposure": Path(args.exposure).name,
        "input_outcome": Path(args.outcome).name,
        "ld_matrix": None if args.ld_matrix is None else Path(args.ld_matrix).name,
    }


def _write_pair_outputs(outdir: Path, analysis: PairAnalysis, metadata: dict,
                        warnings: list[str], config: dict) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    analysis.selected.to_csv(outdir / "harmonized.tsv", sep="\t", index=False)
    if analysis.leave_one_out is not None:
        analysis.leave_one_out.to_csv(outdir / "leave_one_out.tsv", sep="\t", index=False)
    write_report(
        outdir, metadata, analysis.audit, analysis.harmonized.dropped,
        analysis.methods, warnings, config,
    )


def _run(args) -> int:
    exposure = read_summary(args.exposure, "exposure")
    outcome = read_summary(args.outcome, "outcome")
    metadata = _metadata(args.metadata)
    ld_matrix = _read_ld(args.ld_matrix)
    analysis = analyze_pair(
        exposure.data, outcome.data,
        p_threshold=args.p_threshold, f_threshold=args.f_threshold,
        maf_threshold=args.maf_threshold, ld_matrix=ld_matrix, ld_r2=args.ld_r2,
    )
    _write_pair_outputs(Path(args.outdir), analysis, metadata, _warnings(metadata, ld_matrix), _config(args))
    print(f"PlantMR completed: {args.outdir}")
    return 0


def _run_stratified(args) -> int:
    exposure = _read_table(args.exposure)
    outcome = _read_table(args.outcome)
    if "environment" not in exposure.columns or "environment" not in outcome.columns:
        raise ValueError("run-stratified requires an environment column in both input tables")
    environments = sorted(set(exposure["environment"].astype(str)).intersection(outcome["environment"].astype(str)))
    if not environments:
        raise ValueError("no shared environments were found")
    metadata = _metadata(args.metadata)
    ld_matrix = _read_ld(args.ld_matrix)
    rows = []
    audits = {}
    dropped = {}
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for environment in environments:
        exp = exposure.loc[exposure["environment"].astype(str) == environment].drop(columns=["environment"])
        out = outcome.loc[outcome["environment"].astype(str) == environment].drop(columns=["environment"])
        exp_result = validate_summary(exp, f"exposure[{environment}]")
        out_result = validate_summary(out, f"outcome[{environment}]")
        analysis = analyze_pair(
            exp_result.data, out_result.data,
            p_threshold=args.p_threshold, f_threshold=args.f_threshold,
            maf_threshold=args.maf_threshold, ld_matrix=ld_matrix, ld_r2=args.ld_r2,
        )
        audits[environment] = analysis.audit
        dropped[environment] = analysis.harmonized.dropped
        for method in analysis.methods:
            rows.append({"environment": environment, **method})
    result_table = pd.DataFrame(rows).sort_values(["environment", "method"]).reset_index(drop=True)
    result_table.to_csv(outdir / "environment_results.tsv", sep="\t", index=False)
    payload = {
        "tool_version": "1.1.0",
        "metadata": metadata,
        "environments": environments,
        "results": rows,
        "audits": audits,
        "harmonization_dropped": dropped,
        "warnings": _warnings(metadata, ld_matrix, stratified=True),
        "config": _config(args),
    }
    (outdir / "results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# PlantMR v1.0 stratified report", "", "## Environments", "", ", ".join(environments), "", "## Results", "", "| Environment | Method | Beta | SE | P value | SNPs |", "|---|---|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['environment']} | {row['method']} | {row['beta']:.8g} | {row['se']:.8g} | {row['pval']:.8g} | {row['nsnp']} |")
    lines += ["", "## Warnings", ""] + [f"- {item}" for item in payload["warnings"]] + [""]
    (outdir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"PlantMR stratified analysis completed: {args.outdir}")
    return 0


def _harmonize_gxe_inputs(exposure: pd.DataFrame, outcome: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    required = {"environment", "environment_value"}
    if not required.issubset(exposure.columns):
        raise ValueError("run-gxe exposure requires environment and environment_value columns")
    if "environment" not in outcome.columns:
        raise ValueError("run-gxe outcome requires an environment column")
    environments = sorted(set(exposure["environment"].astype(str)).intersection(outcome["environment"].astype(str)))
    if len(environments) < 2:
        raise ValueError("run-gxe requires at least two shared environments")
    chunks = []
    dropped = {}
    for environment in environments:
        exp_mask = exposure["environment"].astype(str) == environment
        out_mask = outcome["environment"].astype(str) == environment
        env_value = pd.to_numeric(exposure.loc[exp_mask, "environment_value"], errors="coerce")
        if env_value.isna().any() or env_value.nunique() != 1:
            raise ValueError("exposure environment_value must be finite and constant within each environment")
        exp = exposure.loc[exp_mask].drop(columns=["environment", "environment_value"])
        out = outcome.loc[out_mask].drop(columns=["environment"])
        if "environment_value" in out.columns:
            out_value = pd.to_numeric(out["environment_value"], errors="coerce")
            if out_value.isna().any() or out_value.nunique() != 1:
                raise ValueError("outcome environment_value must be finite and constant within each environment")
            out = out.drop(columns=["environment_value"])
        from .harmonize import harmonize_summary
        result = harmonize_summary(exp, out)
        if result.data.empty:
            raise ValueError("no harmonized instruments remain in environment %s" % environment)
        chunk = result.data.copy()
        chunk["environment"] = environment
        chunk["environment_value"] = float(env_value.iloc[0])
        chunks.append(chunk)
        dropped[environment] = result.dropped
    return pd.concat(chunks, ignore_index=True), {"environments": environments, "dropped": dropped}


def _run_gxe(args) -> int:
    exposure = _read_table(args.exposure)
    outcome = _read_table(args.outcome)
    metadata = _metadata(args.metadata)
    harmonized, harmonization = _harmonize_gxe_inputs(exposure, outcome)
    selected, audit = select_gxe_instruments(
        harmonized,
        p_threshold=args.p_threshold,
        f_threshold=args.f_threshold,
        maf_threshold=args.maf_threshold,
    )
    if selected.empty:
        raise ValueError("no SNP passed GxE instrument QC in every environment")
    env_corr = _read_correlation(args.environment_correlation)
    ld_corr = _read_correlation(args.ld_correlation)
    result = gxe_ivw(selected, environment_correlation=env_corr, ld_correlation=ld_corr)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    selected.to_csv(outdir / "gxe_harmonized.tsv", sep="\t", index=False)
    warnings = [
        "GxE-IVW is a summary-statistics GLS model under supplied covariance assumptions.",
        "MR evidence does not replace colocalization, functional validation, or gene editing.",
    ]
    if env_corr is None:
        warnings.append("No environment correlation was supplied; diagonal ratio covariance was used.")
    if ld_corr is None:
        warnings.append("No LD correlation was supplied; cross-SNP covariance was set to zero.")
    payload = {
        "tool_version": "1.1.0",
        "method": "gxe_ivw",
        "metadata": metadata,
        "result": result.as_dict(),
        "audit": audit,
        "harmonization": harmonization,
        "warnings": warnings,
        "config": {
            "p_threshold": args.p_threshold,
            "f_threshold": args.f_threshold,
            "maf_threshold": args.maf_threshold,
            "environment_correlation": None if args.environment_correlation is None else Path(args.environment_correlation).name,
            "ld_correlation": None if args.ld_correlation is None else Path(args.ld_correlation).name,
        },
    }
    (outdir / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# PlantMR GxE-IVW report", "", "## Estimand", "",
        "The intercept is the pooled MR effect at environment_value=0; the slope is the change in MR effect per unit environment_value.",
        "", "## Result", "", "| Parameter | Estimate | SE | P value |", "|---|---:|---:|---:|",
        f"| pooled intercept | {result.intercept:.8g} | {result.intercept_se:.8g} | {result.intercept_pval:.8g} |",
        f"| environment slope | {result.slope:.8g} | {result.slope_se:.8g} | {result.slope_pval:.8g} |",
        "", "## Audit", "",
    ]
    lines.extend("- %s: %s" % (key, value) for key, value in sorted(audit.items()))
    lines += ["", "## Covariance", "", "- source: %s" % result.covariance_source,
              "- rank: %s" % result.covariance_rank, "", "## Warnings", ""]
    lines.extend("- " + warning for warning in warnings)
    (outdir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PlantMR GxE analysis completed: {args.outdir}")
    return 0


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            read_summary(args.exposure, "exposure")
            read_summary(args.outcome, "outcome")
            _metadata(args.metadata)
            print("PlantMR input validation passed")
            return 0
        if args.command == "run-stratified":
            return _run_stratified(args)
        if args.command == "run-gxe":
            return _run_gxe(args)
        return _run(args)
    except (SchemaError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"PlantMR error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
