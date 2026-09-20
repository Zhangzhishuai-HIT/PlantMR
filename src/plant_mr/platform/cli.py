"""CLI for the PlantMR 2.x project contract."""

from __future__ import annotations

import argparse
import json
import sys

from .errors import ProjectManifestError
from .init import write_project_skeleton
from .project import ProjectManifest
from .runner import run_project
from .validate import required_inputs_for_analysis, validate_project

OPTIONAL_INPUTS = {
    "annotation",
    "environment_correlation",
    "edges",
    "expression",
    "genotype",
    "ld",
    "metabolite",
    "phenotype",
    "protein",
    "go_annotation",
    "selected_features",
}


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        for key, value in payload.items():
            if isinstance(value, list):
                print(f"{key}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")


def _missing_inputs(manifest: ProjectManifest, roles: set[str] | None = None) -> list[str]:
    missing = []
    candidate_roles = sorted(roles if roles is not None else set(manifest.inputs))
    for role in candidate_roles:
        raw_path = manifest.inputs.get(role, "")
        if not raw_path:
            missing.append(role)
            continue
        if not manifest.resolve_input(role).exists():
            missing.append(role)
    return missing


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="plantmr2",
        description="PlantMR 2.x CLI-first plant causal multi-omics platform",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a project skeleton")
    init.add_argument("project_name")
    init.add_argument("--species", required=True)
    init.add_argument("--assembly", required=True)
    init.add_argument("--outdir", required=True)
    init.add_argument("--json", action="store_true")

    inspect = sub.add_parser("inspect", help="inspect a project manifest without running analysis")
    inspect.add_argument("manifest")
    inspect.add_argument("--json", action="store_true")
    validate = sub.add_parser("validate", help="validate required project inputs")
    validate.add_argument("manifest")
    validate.add_argument("--analysis")
    validate.add_argument("--feature-role", default="expression")
    validate.add_argument("--json", action="store_true")
    run = sub.add_parser("run", help="run a supported analysis and write an isolated report")
    run.add_argument("manifest")
    run.add_argument("--analysis")
    run.add_argument("--run-id")
    run.add_argument("--trait")
    run.add_argument("--feature-role", default="expression")
    run.add_argument("--feature-id")
    run.add_argument("--network-p-threshold", type=float, default=0.05)
    run.add_argument("--json", action="store_true")
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "init":
            manifest = write_project_skeleton(
                args.project_name, args.species, args.assembly, args.outdir
            )
            payload = {
                "command": "init",
                "manifest": str(manifest),
                "project_dir": str(manifest.parent),
                "next": [
                    "edit plantmr.toml",
                    "place files under data/",
                    f"plantmr2 inspect {manifest}",
                ],
            }
            _emit(payload, args.json)
            return 0
        if args.command == "inspect":
            manifest = ProjectManifest.from_file(args.manifest)
            selected_analysis = manifest.analyses[0] if manifest.analyses else "ordinary-mr"
            required_inputs = required_inputs_for_analysis(selected_analysis)
            payload = {
                "command": "inspect",
                "analysis": selected_analysis,
                "valid_manifest": True,
                "project_name": manifest.project_name,
                "species": manifest.species,
                "assembly": manifest.assembly,
                "missing_inputs": _missing_inputs(manifest, required_inputs),
                "missing_optional_inputs": sorted(
                    OPTIONAL_INPUTS | (set(manifest.inputs) - required_inputs)
                    - set(manifest.inputs)
                    | set(_missing_inputs(manifest, set(manifest.inputs) - required_inputs))
                ),
                "output_dir": str(manifest.resolve_output_dir()),
                "analyses": list(manifest.analyses),
            }
            _emit(payload, args.json)
            return 0
        if args.command == "validate":
            manifest = ProjectManifest.from_file(args.manifest)
            selected_analysis = args.analysis or (manifest.analyses[0] if manifest.analyses else "ordinary-mr")
            required_inputs = required_inputs_for_analysis(
                selected_analysis,
                feature_role=args.feature_role,
            )
            payload = {
                "command": "validate",
                "analysis": selected_analysis,
                **validate_project(manifest, required_inputs=required_inputs),
            }
            _emit(payload, args.json)
            return 0 if payload["valid"] else 2
        if args.command == "run":
            manifest = ProjectManifest.from_file(args.manifest)
            run_dir = run_project(
                manifest,
                analysis=args.analysis,
                run_id=args.run_id,
                trait=args.trait,
                feature_role=args.feature_role,
                feature_id=args.feature_id,
                network_p_threshold=args.network_p_threshold,
            )
            _emit(
                {
                    "command": "run",
                    "analysis": args.analysis or (manifest.analyses[0] if manifest.analyses else "ordinary-mr"),
                    "run_dir": str(run_dir),
                    "report": str(run_dir / "report.md"),
                    "results": str(run_dir / "results.json"),
                },
                args.json,
            )
            return 0
    except (ProjectManifestError, OSError, TypeError, ValueError, KeyError) as exc:
        if getattr(args, "json", False):
            print(
                json.dumps(
                    {
                        "command": getattr(args, "command", ""),
                        "valid": False,
                        "errors": [str(exc)],
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(f"plantmr2 error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
