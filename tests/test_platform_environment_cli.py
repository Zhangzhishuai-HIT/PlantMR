import json

from plant_mr.platform.cli import main


def _write_env_project(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    header = "SNP\tenvironment\tenvironment_value\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    exp = header
    out = header
    for snp, bx in [("s1", 0.2), ("s2", 0.25), ("s3", 0.3)]:
        for env, value in [("E1", 0.0), ("E2", 1.0)]:
            exp += f"{snp}\t{env}\t{value}\tA\tG\t{bx}\t0.02\t1e-12\t0.3\n"
            out += f"{snp}\t{env}\t{value}\tA\tG\t{bx * (1 + value * 0.2)}\t0.03\t1e-10\t0.3\n"
    (data / "exposure.tsv").write_text(exp, encoding="utf-8")
    (data / "outcome.tsv").write_text(out, encoding="utf-8")
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "env-demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["stratified-mr"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return manifest


def test_cli_runs_stratified_and_environment_heterogeneity(tmp_path, capsys):
    manifest = _write_env_project(tmp_path)

    assert main(["run", str(manifest), "--analysis", "stratified-mr", "--run-id", "s1", "--json"]) == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "s1" / "environment_results.tsv").exists()

    assert main(["run", str(manifest), "--analysis", "environment-heterogeneity", "--run-id", "g1", "--json"]) == 0
    json.loads(capsys.readouterr().out)
    assert (tmp_path / "runs" / "g1" / "gxe_results.json").exists()
