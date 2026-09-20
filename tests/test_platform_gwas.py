import numpy as np
import pandas as pd
import json

from plant_mr.platform.cli import main
from plant_mr.platform.gwas import run_gwas


def test_gwas_recovers_a_variant_trait_signal():
    rng = np.random.default_rng(42)
    samples = [f"p{i:03d}" for i in range(60)]
    causal = rng.integers(0, 3, size=len(samples))
    null = rng.integers(0, 3, size=len(samples))
    genotype = pd.DataFrame(
        [
            {"sample_id": sample, "variant_id": variant, "dosage": int(dosage)}
            for variant, values in (("s_causal", causal), ("s_null", null))
            for sample, dosage in zip(samples, values)
        ]
    )
    phenotype = pd.DataFrame(
        {
            "sample_id": samples,
            "trait": "height",
            "value": 2.0 + 1.5 * causal + rng.normal(0, 0.2, len(samples)),
        }
    )

    result = run_gwas(genotype, phenotype, trait="height")

    assert list(result.columns) == [
        "variant_id", "trait", "beta", "se", "pval", "n", "maf", "mean_dosage"
    ]
    causal_row = result.loc[result["variant_id"] == "s_causal"].iloc[0]
    null_row = result.loc[result["variant_id"] == "s_null"].iloc[0]
    assert causal_row["beta"] > 1.0
    assert causal_row["pval"] < null_row["pval"]
    assert causal_row["n"] == len(samples)


def test_cli_runs_gwas_as_an_isolated_project_run(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "exposure.tsv").write_text(
        "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
        "s1\tA\tG\t0.2\t0.05\t1e-8\t0.3\n",
        encoding="utf-8",
    )
    (data / "outcome.tsv").write_text(
        "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
        "s1\tA\tG\t0.1\t0.05\t1e-8\t0.3\n",
        encoding="utf-8",
    )
    samples = [f"p{i:02d}" for i in range(12)]
    genotype = "sample_id\tvariant_id\tdosage\n" + "".join(
        f"{sample}\ts1\t{i % 3}\n" for i, sample in enumerate(samples)
    )
    phenotype = "sample_id\ttrait\tvalue\n" + "".join(
        f"{sample}\theight\t{1.0 + 0.8 * (i % 3)}\n" for i, sample in enumerate(samples)
    )
    (data / "genotype.tsv").write_text(genotype, encoding="utf-8")
    (data / "phenotype.tsv").write_text(phenotype, encoding="utf-8")
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "demo"
species = "Zea_mays"
assembly = "RefGen_v5"
output_dir = "runs"
analyses = ["gwas"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
genotype = "data/genotype.tsv"
phenotype = "data/phenotype.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["run", str(manifest), "--analysis", "gwas", "--run-id", "gwas1", "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "gwas1"
    assert payload["run_dir"] == str(run_dir)
    assert (run_dir / "gwas.tsv").exists()
    assert (run_dir / "results.json").exists()
    assert (run_dir / "report.md").exists()
