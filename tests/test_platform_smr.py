import numpy as np
import pandas as pd
import json

from plant_mr.platform.cli import main
from plant_mr.platform.smr import run_smr_heidi


def test_smr_heidi_recovers_shared_causal_signal():
    exposure = pd.DataFrame(
        {
            "SNP": ["s1", "s2", "s3", "s4"],
            "feature_id": ["GeneA"] * 4,
            "effect_allele": ["A"] * 4,
            "other_allele": ["G"] * 4,
            "beta": [0.20, 0.25, 0.15, 0.30],
            "se": [0.02] * 4,
            "pval": [1e-20, 1e-18, 1e-12, 1e-25],
            "eaf": [0.3] * 4,
        }
    )
    outcome = exposure.drop(columns="feature_id").copy()
    outcome["beta"] = outcome["beta"] * 0.5
    outcome["se"] = 0.03
    outcome["pval"] = 1e-10

    result = run_smr_heidi(exposure, outcome)

    row = result.iloc[0]
    assert row["feature_id"] == "GeneA"
    assert row["top_snp"] == "s4"
    assert abs(float(row["smr_beta"]) - 0.5) < 1e-8


def test_cli_runs_smr_with_feature_annotated_exposure(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    exposure = "SNP\tfeature_id\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    outcome = "SNP\teffect_allele\tother_allele\tbeta\tse\tpval\teaf\n"
    for i, (beta, pval) in enumerate([(0.2, 1e-20), (0.25, 1e-18), (0.15, 1e-12)]):
        snp = f"s{i + 1}"
        exposure += f"{snp}\tGeneA\tA\tG\t{beta}\t0.02\t{pval}\t0.3\n"
        outcome += f"{snp}\tA\tG\t{beta * 0.5}\t0.03\t1e-10\t0.3\n"
    (data / "exposure.tsv").write_text(exposure, encoding="utf-8")
    (data / "outcome.tsv").write_text(outcome, encoding="utf-8")
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "smr-demo"
species = "Arabidopsis_thaliana"
assembly = "TAIR10"
output_dir = "runs"
analyses = ["smr"]

[inputs]
exposure = "data/exposure.tsv"
outcome = "data/outcome.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["run", str(manifest), "--analysis", "smr", "--run-id", "smr1", "--json"])

    assert rc == 0
    json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "smr1"
    assert (run_dir / "smr.tsv").exists()
    assert (run_dir / "report.md").exists()
