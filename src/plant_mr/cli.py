import argparse
import json
from pathlib import Path
import sys

from .estimators import ivw_fixed, ivw_random, leave_one_out, mr_egger
from .harmonize import harmonize_summary
from .instruments import select_instruments
from .report import write_report
from .schema import SchemaError, read_summary


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="plantmr", description="Plant-native Mendelian randomization toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate summary statistics and metadata")
    validate.add_argument("--exposure", required=True)
    validate.add_argument("--outcome", required=True)
    validate.add_argument("--metadata", required=True)
    run = sub.add_parser("run", help="run v0.1 summary-level MR")
    run.add_argument("--exposure", required=True)
    run.add_argument("--outcome", required=True)
    run.add_argument("--metadata", required=True)
    run.add_argument("--outdir", required=True)
    run.add_argument("--p-threshold", type=float, default=5e-8)
    run.add_argument("--f-threshold", type=float, default=10.0)
    run.add_argument("--maf-threshold", type=float, default=0.01)
    return parser


def _metadata(path: str):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("metadata must be a JSON object")
    return data


def _run(args) -> int:
    exposure = read_summary(args.exposure, "exposure")
    outcome = read_summary(args.outcome, "outcome")
    metadata = _metadata(args.metadata)
    harmonized = harmonize_summary(exposure.data, outcome.data)
    selected, audit = select_instruments(
        harmonized.data,
        p_threshold=args.p_threshold,
        f_threshold=args.f_threshold,
        maf_threshold=args.maf_threshold,
    )
    if selected.empty:
        raise ValueError("no instruments remained after harmonization and QC")
    methods = [ivw_fixed(selected).as_dict(), ivw_random(selected).as_dict()]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    selected.to_csv(outdir / "harmonized.tsv", sep="\t", index=False)
    if len(selected) >= 3:
        methods.append(mr_egger(selected).as_dict())
    if len(selected) >= 2:
        leave_one_out(selected).to_csv(outdir / "leave_one_out.tsv", sep="\t", index=False)
    warnings = []
    if not metadata.get("ld_panel"):
        warnings.append("No LD reference panel was supplied; independence/clumping was not re-verified.")
    warnings.append("v0.1 does not yet implement colocalization, MVMR, MR-PRESSO, or environment-aware MR.")
    config = {
        "command": "run",
        "p_threshold": args.p_threshold,
        "f_threshold": args.f_threshold,
        "maf_threshold": args.maf_threshold,
        "input_exposure": Path(args.exposure).name,
        "input_outcome": Path(args.outcome).name,
    }
    write_report(outdir, metadata, audit, harmonized.dropped, methods, warnings, config)
    print(f"PlantMR completed: {outdir}")
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
        return _run(args)
    except (SchemaError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"PlantMR error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
