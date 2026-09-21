import pandas as pd

from plant_mr.platform.network import build_mr_network, identify_network_modules


def test_bidirectional_mr_network_and_modules():
    edges = pd.DataFrame(
        {
            "source": ["A", "B", "B"],
            "target": ["B", "A", "C"],
            "beta": [0.5, 0.2, -0.3],
            "se": [0.1, 0.1, 0.1],
            "pval": [1e-5, 1e-4, 1e-6],
        }
    )

    network = build_mr_network(edges, p_threshold=0.01)
    modules = identify_network_modules(network, min_nodes=2)

    ab = network.loc[(network["node_a"] == "A") & (network["node_b"] == "B")].iloc[0]
    assert bool(ab["reciprocal"]) is True
    assert ab["weight"] > 3
    assert set(modules["node"]) == {"A", "B", "C"}
    assert modules["hub_score"].max() == 1.0
