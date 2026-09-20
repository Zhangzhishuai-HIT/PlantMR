import json

from plant_mr.platform.cli import main


def test_run_ordinary_mr_writes_reproducible_run_directory(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    header = "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    rows = "".join(
        f"s{i}\tA\tG\t{0.20 + i * 0.01}\t0.05\t1e-8\t0.3\n"
        for i in range(1, 4)
    )
    (data / "exposure.tsv").write_text(header + rows, encoding="utf-8")
    (data / "outcome.tsv").write_text(header + rows.replace("\t0.20", "\t0.10"), encoding="utf-8")
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

    rc = main([
        "run",
        str(manifest),
        "--analysis",
        "ordinary-mr",
        "--run-id",
        "smoke",
        "--json",
    ])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "smoke"
    assert payload["run_dir"] == str(run_dir)
    assert (run_dir / "run_manifest.json").exists()
    assert (run_dir / "results.json").exists()
    assert (run_dir / "harmonized.tsv").exists()
    assert (run_dir / "report.md").exists()
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    assert results["methods"]
    assert results["config"]["analysis"] == "ordinary-mr"


def test_run_returns_structured_json_for_invalid_project(tmp_path, capsys):
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "invalid"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["ordinary-mr"]

[inputs]
exposure = "data/missing.tsv"
outcome = "data/missing.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["run", str(manifest), "--json"])

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "run"
    assert payload["valid"] is False
    assert payload["errors"]


def test_run_rejects_path_traversal_run_id(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    summary = (
        "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
        "s1\tA\tG\t0.2\t0.05\t1e-8\t0.3\n"
    )
    (data / "exposure.tsv").write_text(summary, encoding="utf-8")
    (data / "outcome.tsv").write_text(summary, encoding="utf-8")
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "safe"
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

    rc = main(["run", str(manifest), "--run-id", "../outside", "--json"])

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert not (tmp_path / "outside").exists()
