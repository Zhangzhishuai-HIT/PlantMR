import json

from plant_mr.platform.cli import main


def test_cli_runs_sal_and_variant_annotation(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "gwas.tsv").write_text(
        "variant_id\tchromosome\tposition\tpval\n"
        "s1\t1\t100\t1e-10\n"
        "s2\t1\t200\t1e-6\n"
        "s3\t1\t1000\t0.5\n",
        encoding="utf-8",
    )
    (data / "genes.tsv").write_text(
        "feature_id\tgene_symbol\tchromosome\tstart\tend\n"
        "g1\tGeneA\t1\t90\t220\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "sal-demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["sal"]

[inputs]
gwas = "data/gwas.tsv"
gene_annotation = "data/genes.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc1 = main(["run", str(manifest), "--analysis", "sal", "--run-id", "sal1", "--json"])
    assert rc1 == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "sal1" / "sal.tsv").exists()

    rc2 = main(["run", str(manifest), "--analysis", "annotate", "--run-id", "ann1", "--json"])
    assert rc2 == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "ann1" / "variant_annotation.tsv").exists()


def test_cli_runs_coloc_and_mvmr(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    exposure = "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    outcome = "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    mvmr = "SNP\texposure_id\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    for i, (b1, b2) in enumerate([(0.2, 0.1), (0.25, 0.12), (0.15, 0.08), (0.3, 0.15)]):
        snp = f"s{i + 1}"
        exposure += f"{snp}\tA\tG\t{b1}\t0.02\t1e-10\t0.3\n"
        outcome += f"{snp}\tA\tG\t{b2}\t0.03\t1e-10\t0.3\n"
        mvmr += f"{snp}\tGeneA\tA\tG\t{b1}\t0.02\t1e-10\t0.3\n"
        mvmr += f"{snp}\tMetA\tA\tG\t{b2}\t0.02\t1e-10\t0.3\n"
    (data / "exposure.tsv").write_text(exposure, encoding="utf-8")
    (data / "outcome.tsv").write_text(outcome, encoding="utf-8")
    (data / "mvmr.tsv").write_text(mvmr, encoding="utf-8")
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "causal-demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["coloc"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    assert main(["run", str(manifest), "--analysis", "coloc", "--run-id", "c1", "--json"]) == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "c1" / "coloc.tsv").exists()

    manifest.write_text(manifest.read_text(encoding="utf-8").replace("data/exposure.tsv", "data/mvmr.tsv"), encoding="utf-8")
    assert main(["run", str(manifest), "--analysis", "mvmr", "--run-id", "m1", "--json"]) == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "m1" / "mvmr.tsv").exists()
