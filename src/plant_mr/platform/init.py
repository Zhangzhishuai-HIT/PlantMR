"""Project skeleton creation for the PlantMR 2.x platform."""

from __future__ import annotations

from pathlib import Path

from .errors import ProjectManifestError


def _toml_string(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def write_project_skeleton(
    project_name: str,
    species: str,
    assembly: str,
    outdir: str | Path,
) -> Path:
    root = Path(outdir).expanduser().resolve()
    if root.exists() and any(root.iterdir()):
        raise ProjectManifestError(f"output directory is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for name in ("data", "runs", "reports", "logs"):
        (root / name).mkdir()
    roles = (
        "exposure",
        "outcome",
        "genotype",
        "gwas",
        "gene_annotation",
        "kinship",
        "covariates",
        "phenotype",
        "expression",
        "metabolite",
        "protein",
        "ld",
        "environment_correlation",
        "annotation",
        "go_annotation",
        "selected_features",
        "edges",
    )
    lines = [
        f"project_name = {_toml_string(project_name)}",
        f"species = {_toml_string(species)}",
        f"assembly = {_toml_string(assembly)}",
        'output_dir = "runs"',
        'analyses = ["ordinary-mr"]',
        "",
        "[inputs]",
    ]
    for role in roles:
        lines.append(f'{role} = ""')
    lines += [
        "",
        "[metadata]",
        'tissue = ""',
        'stage = ""',
        'environment = ""',
        'ploidy = ""',
        'ld_panel = ""',
        "",
    ]
    manifest = root / "plantmr.toml"
    manifest.write_text("\n".join(lines), encoding="utf-8")
    readme = root / "README.md"
    readme.write_text(
        "# PlantMR project\n\n"
        "Edit plantmr.toml and place input files under data/.\n\n"
        "1. Fill the exposure and outcome paths in [inputs].\n"
        "2. Fill species, assembly, tissue, stage, environment, ploidy and LD metadata.\n"
        "3. Run `plantmr2 inspect plantmr.toml`.\n"
        "4. Run `plantmr2 validate plantmr.toml` before analysis.\n",
        encoding="utf-8",
    )
    return manifest
