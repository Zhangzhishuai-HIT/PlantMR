import json

from plant_mr.platform.project import ProjectManifest
from plant_mr.platform.provenance import input_receipts, sha256_file


def test_input_receipt_is_relative_and_hashes_bytes(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    source = data / "x.tsv"
    source.write_text("a\tb\n1\t2\n", encoding="utf-8")
    manifest_path = tmp_path / "plantmr.toml"
    manifest_path.write_text(
        """
project_name = "demo"
species = "Zea_mays"
assembly = "RefGen_v5"
[inputs]
edges = "data/x.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    manifest = ProjectManifest.from_file(manifest_path)

    receipts = input_receipts(manifest)

    assert receipts[0]["path"] == "data/x.tsv"
    assert receipts[0]["sha256"] == sha256_file(source)
    assert receipts[0]["size_bytes"] == source.stat().st_size
