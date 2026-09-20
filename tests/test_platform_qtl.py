import numpy as np
import pandas as pd
import json

from plant_mr.platform.cli import main
from plant_mr.platform.qtl import run_qtl


def test_qtl_uses_the_same_contract_for_expression_features():
    rng = np.random.default_rng(7)
    samples = [f"p{i:03d}" for i in range(40)]
    dosage = rng.integers(0, 3, size=len(samples))
    genotype = pd.DataFrame(
        [{"sample_id": s, "variant_id": "s1", "dosage": int(d)} for s, d in zip(samples, dosage)]
    )
    expression = pd.DataFrame(
        [{"sample_id": s, "feature_id": "ZmGene1", "value": 3 + 1.2 * d + rng.normal(0, .2)}
         for s, d in zip(samples, dosage)]
    )

    result = run_qtl(genotype, expression, feature_id="ZmGene1", molecular_type="expression")

    assert list(result.columns) == [
        "variant_id", "feature_id", "molecular_type", "beta", "se", "pval", "n", "maf", "mean_dosage"
    ]
    assert result.iloc[0]["feature_id"] == "ZmGene1"
    assert result.iloc[0]["molecular_type"] == "expression"
    assert result.iloc[0]["pval"] < 1e-5


def test_cli_runs_qtl_without_exposure_or_outcome(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    samples = [f"p{i:02d}" for i in range(12)]
    (data / "genotype.tsv").write_text(
        "sample_id\tvariant_id\tdosage\n" + "".join(
            f"{sample}\ts1\t{i % 3}\n" for i, sample in enumerate(samples)
        ),
        encoding="utf-8",
    )
    (data / "expression.tsv").write_text(
        "sample_id\tfeature_id\tvalue\n" + "".join(
            f"{sample}\tGeneA\t{1 + 0.8 * (i % 3)}\n" for i, sample in enumerate(samples)
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "qtl-demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["qtl"]

[inputs]
genotype = "data/genotype.tsv"
expression = "data/expression.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main([
        "run", str(manifest), "--analysis", "qtl", "--feature-role", "expression",
        "--feature-id", "GeneA", "--run-id", "qtl1", "--json",
    ])

    assert rc == 0
    json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "qtl1"
    assert (run_dir / "qtl.tsv").exists()
    assert (run_dir / "report.md").exists()
