import json
from pathlib import Path

from plant_mr.platform.cli import main


def test_init_creates_user_facing_project_skeleton(tmp_path, capsys):
    outdir = tmp_path / "maize_project"

    rc = main([
        "init",
        "maize-demo",
        "--species",
        "Zea_mays",
        "--assembly",
        "RefGen_v5",
        "--outdir",
        str(outdir),
        "--json",
    ])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert Path(payload["manifest"]) == outdir / "plantmr.toml"
    assert (outdir / "plantmr.toml").exists()
    assert (outdir / "data").is_dir()
    assert (outdir / "runs").is_dir()
    assert (outdir / "reports").is_dir()
    assert (outdir / "logs").is_dir()
    assert (outdir / "README.md").exists()


def test_inspect_reports_missing_input_paths_without_running(tmp_path, capsys):
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "demo"
species = "Arabidopsis_thaliana"
assembly = "TAIR10"
output_dir = "runs"
analyses = ["ordinary-mr"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["inspect", str(manifest), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid_manifest"] is True
    assert payload["missing_inputs"] == ["exposure", "outcome"]
    assert "genotype" in payload["missing_optional_inputs"]
    assert not (tmp_path / "runs").exists()
