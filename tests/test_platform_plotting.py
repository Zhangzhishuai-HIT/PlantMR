import pandas as pd

from plant_mr.platform.plotting import (
    plot_manhattan,
    plot_mr_forest,
    plot_network,
    plot_qq,
)


def test_plotting_writes_png_and_pdf_outputs(tmp_path):
    gwas = pd.DataFrame(
        {
            "variant_id": ["s1", "s2", "s3", "s4"],
            "chromosome": [1, 1, 2, 2],
            "position": [10, 20, 10, 20],
            "pval": [1e-8, 0.2, 1e-5, 0.8],
        }
    )
    methods = pd.DataFrame(
        {"method": ["IVW", "Egger"], "beta": [0.2, 0.1], "se": [0.05, 0.08], "pval": [1e-4, 0.2], "nsnp": [4, 4]}
    )
    network = pd.DataFrame({"source": ["A"], "target": ["B"], "weight": [2.0]})

    outputs = []
    outputs += plot_manhattan(gwas, tmp_path / "manhattan")
    outputs += plot_qq(gwas, tmp_path / "qq")
    outputs += plot_mr_forest(methods, tmp_path / "forest")
    outputs += plot_network(network, tmp_path / "network")

    assert len(outputs) == 8
    assert all(path.exists() and path.stat().st_size > 0 for path in outputs)
