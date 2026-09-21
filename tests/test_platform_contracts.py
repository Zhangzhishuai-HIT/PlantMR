import gzip
import json

from plant_mr.platform.cli import main


def _manifest(tmp_path, extra=""):
    path = tmp_path / "plantmr.toml"
    path.write_text(
        """
project_name = "demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["ordinary-mr"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
"""
        + extra
        + "\n",
        encoding="utf-8",
    )
    return path


def _summary_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    text = (
        "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
        "s1\tA\tG\t0.2\t0.05\t1e-8\t0.3\n"
    )
    for name in ("exposure.tsv", "outcome.tsv"):
        (data / name).write_text(text, encoding="utf-8")
    return data


def test_validate_checks_declared_genotype_contract(tmp_path, capsys):
    data = _summary_files(tmp_path)
    (data / "genotype.tsv").write_text(
        "sample_id\tvariant_id\tdosage\n"
        "plant_01\ts1\t1\n"
        "plant_02\ts1\t2\n",
        encoding="utf-8",
    )
    manifest = _manifest(
        tmp_path,
        "\ngenotype = \"data/genotype.tsv\"\n",
    )

    rc = main(["validate", str(manifest), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["inputs"]["genotype"]["contract"] == "genotype-long"
    assert payload["inputs"]["genotype"]["rows"] == 2


def test_validate_rejects_malformed_declared_expression(tmp_path, capsys):
    data = _summary_files(tmp_path)
    (data / "expression.tsv").write_text(
        "sample_id\tfeature_id\nplant_01\tZm00001\n",
        encoding="utf-8",
    )
    manifest = _manifest(
        tmp_path,
        "\nexpression = \"data/expression.tsv\"\n",
    )

    rc = main(["validate", str(manifest), "--json"])

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert any("expression" in item for item in payload["errors"])


def test_validate_accepts_compressed_vcf_genotype_contract(tmp_path, capsys):
    data = _summary_files(tmp_path)
    with gzip.open(data / "genotype.vcf.gz", "wt", encoding="utf-8") as handle:
        handle.write("##fileformat=VCFv4.2\n")
        handle.write("##contig=<ID=1>\n")
        handle.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tplant_01\n")
        handle.write("1\t10\ts1\tA\tG\t.\tPASS\t.\tGT\t0/1\n")
    manifest = _manifest(tmp_path, "\ngenotype = \"data/genotype.vcf.gz\"\n")

    rc = main(["validate", str(manifest), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["inputs"]["genotype"]["contract"] == "genotype-vcf"
