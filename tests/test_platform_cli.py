import json
from pathlib import Path

from plant_mr.platform.cli import _build_parser, main


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


def test_run_parser_exposes_instrument_thresholds():
    args = _build_parser().parse_args(
        [
            "run",
            "plantmr.toml",
            "--p-threshold",
            "0.05",
            "--f-threshold",
            "1.0",
            "--maf-threshold",
            "0.01",
        ]
    )

    assert args.p_threshold == 0.05
    assert args.f_threshold == 1.0
    assert args.maf_threshold == 0.01
