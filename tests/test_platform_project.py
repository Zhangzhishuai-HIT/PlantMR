from pathlib import Path

import pytest

from plant_mr.platform.errors import ProjectManifestError
from plant_mr.platform.project import ProjectManifest


def test_manifest_resolves_relative_inputs_from_manifest_directory(tmp_path):
    manifest_path = tmp_path / "plantmr.toml"
    manifest_path.write_text(
        """
project_name = "maize-demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["ordinary-mr"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    manifest = ProjectManifest.from_file(manifest_path)

    assert manifest.project_name == "maize-demo"
    assert manifest.resolve_input("exposure") == tmp_path / "data/exposure.tsv"
    assert manifest.resolve_output_dir() == tmp_path / "runs"
    assert manifest.to_dict()["assembly"] == "RefGen_v5"


def test_manifest_rejects_missing_plant_context(tmp_path):
    with pytest.raises(ProjectManifestError, match="assembly"):
        ProjectManifest.from_dict(
            {
                "project_name": "demo",
                "species": "Arabidopsis_thaliana",
                "inputs": {},
            },
            source_path=tmp_path / "plantmr.toml",
        )


def test_manifest_rejects_unknown_top_level_fields(tmp_path):
    with pytest.raises(ProjectManifestError, match="unknown"):
        ProjectManifest.from_dict(
            {
                "project_name": "demo",
                "species": "Arabidopsis_thaliana",
                "assembly": "TAIR10",
                "inputs": {},
                "unknown": True,
            },
            source_path=tmp_path / "plantmr.toml",
        )
