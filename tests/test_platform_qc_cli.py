import json

from plant_mr.platform.cli import main


def test_cli_runs_genotype_qc_on_wide_matrix(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "genotype.tsv").write_text(
        "sample_id\ts1\ts2\n"
        "p1\t0\t0\n"
        "p2\t1\t1\n"
        "p3\t2\t2\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "qc"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["genotype-qc"]

[inputs]
genotype = "data/genotype.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["run", str(manifest), "--analysis", "genotype-qc", "--run-id", "g1", "--json"])

    assert rc == 0
    json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "g1"
    assert (run_dir / "genotype_qc.tsv").exists()
    assert json.loads((run_dir / "results.json").read_text())["audit"]["variants_output"] == 2


def test_cli_runs_phenotype_qc_on_wide_matrix(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "phenotype.tsv").write_text(
        "sample_id\theight\tyield\n"
        "p1\t1\t2\n"
        "p2\t\t3\n"
        "p3\t5\t4\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "qc"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["phenotype-qc"]

[inputs]
phenotype = "data/phenotype.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main([
        "run", str(manifest), "--analysis", "phenotype-qc", "--run-id", "p1",
        "--impute", "mean", "--transform", "zscore", "--json",
    ])

    assert rc == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "p1" / "phenotype_qc.tsv").exists()
