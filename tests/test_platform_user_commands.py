import json

from plant_mr.platform.cli import main


def test_status_reads_run_manifests_without_rerunning(tmp_path, capsys):
    runs = tmp_path / "runs" / "r1"
    runs.mkdir(parents=True)
    (runs / "run_manifest.json").write_text(
        json.dumps({"config": {"analysis": "gwas"}, "outputs": ["results.json"]}),
        encoding="utf-8",
    )
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
inputs = {}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["status", str(manifest), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["runs"][0]["run_id"] == "r1"
    assert payload["runs"][0]["analysis"] == "gwas"


def test_explain_returns_estimand_and_noninterpretations(capsys):
    rc = main(["explain", "environment-slope", "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "estimand" in payload
    assert payload["not"]
