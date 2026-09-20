import pandas as pd
import json

from plant_mr.platform.cli import main
from plant_mr.platform.network import summarize_causal_network


def test_network_filters_edges_and_reports_cycles():
    edges = pd.DataFrame(
        {
            "source": ["GeneA", "GeneB", "GeneC"],
            "target": ["GeneB", "GeneC", "GeneA"],
            "beta": [0.4, 0.2, -0.1],
            "se": [0.1, 0.1, 0.1],
            "pval": [1e-5, 1e-5, 1e-6],
        }
    )

    result, summary = summarize_causal_network(edges, p_threshold=0.05)

    assert set(result["target"]) == {"GeneA", "GeneB", "GeneC"}
    assert result["qval"].between(0, 1).all()
    assert summary["n_significant_edges"] == 3
    assert summary["has_cycle"] is True


def test_cli_runs_network_without_mr_summary_inputs(tmp_path, capsys):
    data = tmp_path / "data"
    data.mkdir()
    (data / "edges.tsv").write_text(
        "source\ttarget\tbeta\tse\tpval\nGeneA\tTrait1\t0.4\t0.1\t1e-5\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "plantmr.toml"
    manifest.write_text(
        """
project_name = "network-demo"
species = "Arabidopsis_thaliana"
assembly = "TAIR10"
output_dir = "runs"
analyses = ["network"]

[inputs]
edges = "data/edges.tsv"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = main(["run", str(manifest), "--analysis", "network", "--run-id", "net1", "--json"])

    assert rc == 0
    json.loads(capsys.readouterr().out)
    run_dir = tmp_path / "runs" / "net1"
    assert (run_dir / "network.tsv").exists()
    assert (run_dir / "report.md").exists()
