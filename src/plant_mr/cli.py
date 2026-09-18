import argparse
import json
from pathlib import Path
import sys

import pandas as pd

from .analysis import PairAnalysis, analyze_pair
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
        "tool_version": "1.0.0",
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
        "tool_version": "1.0.0",
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
        return _run(args)
    except (SchemaError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"PlantMR error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
