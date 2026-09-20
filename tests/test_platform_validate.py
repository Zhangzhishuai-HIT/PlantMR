import json

from plant_mr.platform.cli import main


SUMMARY_HEADER = "SNP,effect_allele,other_allele,beta,se,pval\n"


def _write_project_manifest(path, exposure="data/exposure.tsv", outcome="data/outcome.tsv"):
    path.write_text(
        f"""
project_name = "demo"
species = "Arabidopsis_thaliana"
assembly = "TAIR10"
output_dir = "runs"
analyses = ["ordinary-mr"]

[inputs]
exposure = "{exposure}"
outcome = "{outcome}"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_validate_reports_missing_required_file(tmp_path, capsys):
    manifest = tmp_path / "plantmr.toml"
    _write_project_manifest(manifest)

    rc = main(["validate", str(manifest), "--json"])

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert any("exposure" in item for item in payload["errors"])


def test_validate_accepts_minimal_summary_inputs(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    for name in ["exposure.tsv", "outcome.tsv"]:
        (data / name).write_text(
            SUMMARY_HEADER.replace(",", "\t")
            + "s1\tA\tG\t0.2\t0.05\t1e-8\n",
            encoding="utf-8",
        )
    manifest = tmp_path / "plantmr.toml"
    _write_project_manifest(manifest)

    rc = main(["validate", str(manifest), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["errors"] == []
    assert payload["inputs"]["exposure"]["rows"] == 1
