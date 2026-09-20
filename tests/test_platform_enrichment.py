import pandas as pd
import json

from plant_mr.platform.cli import main
from plant_mr.platform.enrichment import go_enrichment


def test_go_enrichment_returns_multiple_testing_corrected_terms():
    annotation = pd.DataFrame(
        {
            "feature_id": ["g1", "g2", "g3", "g4", "g5", "g6"],
            "go_term": ["GO:0001", "GO:0001", "GO:0001", "GO:0002", "GO:0002", "GO:0003"],
            "term_name": ["stress"] * 3 + ["growth"] * 2 + ["other"],
        }
    )
    result = go_enrichment(["g1", "g2", "g4"], annotation)

    assert {"go_term", "term_name", "overlap", "pval", "qval", "fold_enrichment"} <= set(result.columns)
    stress = result.loc[result["go_term"] == "GO:0001"].iloc[0]
    assert stress["overlap"] == 2
    assert 0 <= stress["qval"] <= 1
    assert stress["fold_enrichment"] > 1


def test_cli_runs_go_without_exposure_or_outcome(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "go.tsv").write_text(
        "feature_id\tgo_term\tterm_name\n"
        "g1\tGO:0001\tstress\n"
        "g2\tGO:0001\tstress\n"
        "g3\tGO:0002\tgrowth\n",
        encoding="utf-8",
    )
    (data / "selected.tsv").write_text("feature_id\ng1\n", encoding="utf-8")
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "go-demo"
species = "Arabidopsis_thaliana"
assembly = "TAIR10"
output_dir = "runs"
analyses = ["go"]

[inputs]
go_annotation = "data/go.tsv"
selected_features = "data/selected.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["run", str(manifest), "--analysis", "go", "--run-id", "go1", "--json"])

    assert rc == 0
    json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "go1"
    assert (run_dir / "go_enrichment.tsv").exists()
    assert (run_dir / "report.md").exists()
