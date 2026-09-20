"""Project-level validation for the PlantMR 2.x CLI."""

from __future__ import annotations

from typing import Any

from ..schema import SchemaError, read_summary
from .contracts import InputContractError, validate_input_file
from .project import ProjectManifest

REQUIRED_INPUTS = {"exposure", "outcome"}


def required_inputs_for_analysis(
    analysis: str,
    *,
    feature_role: str = "expression",
) -> set[str]:
    if analysis in {"ordinary-mr", "mr", "smr"}:
        return {"exposure", "outcome"}
    if analysis == "gwas":
        return {"genotype", "phenotype"}
    if analysis == "qtl":
        return {"genotype", feature_role}
    if analysis == "go":
        return {"go_annotation", "selected_features"}
    if analysis == "network":
        return {"edges"}
    return set()


def validate_project(
    manifest: ProjectManifest,
    *,
    required_inputs: set[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    inputs: dict[str, dict[str, Any]] = {}
    required_roles = set(REQUIRED_INPUTS if required_inputs is None else required_inputs)

    for role in sorted(required_roles):
        raw_path = manifest.inputs.get(role, "")
        if not raw_path:
            errors.append(f"required input '{role}' has no path")
            continue
        path = manifest.resolve_input(role)
        if not path.exists():
            errors.append(f"required input '{role}' does not exist: {path}")
            continue
        try:
            if role in {"exposure", "outcome"}:
                result = read_summary(str(path), role)
                inputs[role] = {
                    "path": str(path),
                    "rows": int(len(result.data)),
                    "columns": list(result.data.columns),
                }
            else:
                inputs[role] = validate_input_file(
                    path,
                    role,
                    metadata=manifest.metadata,
                )
        except (InputContractError, OSError, SchemaError, ValueError) as exc:
            errors.append(str(exc))

    optional_roles = sorted(set(manifest.inputs) - required_roles)
    for role in optional_roles:
        raw_path = manifest.inputs.get(role, "")
        if not raw_path:
            warnings.append(f"optional input '{role}' is not configured")
            continue
        path = manifest.resolve_input(role)
        if not path.exists():
            warnings.append(f"optional input '{role}' does not exist: {path}")
            continue
        try:
            inputs[role] = validate_input_file(
                path,
                role,
                metadata=manifest.metadata,
            )
        except (InputContractError, OSError, ValueError) as exc:
            errors.append(str(exc))

    if not manifest.metadata or not manifest.metadata.get("ld_panel"):
        warnings.append("metadata.ld_panel is not configured; LD provenance will be incomplete")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "inputs": inputs,
    }
