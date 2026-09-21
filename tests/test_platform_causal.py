import numpy as np
import pandas as pd

from plant_mr.platform.causal import coloc_abf, run_mvmr


def test_coloc_abf_recovers_shared_signal():
    variants = ["s1", "s2", "s3", "s4"]
    exposure = pd.DataFrame(
        {"variant_id": variants, "beta": [0.4, 0.02, 0.01, 0.0], "se": [0.05] * 4}
    )
    outcome = pd.DataFrame(
        {"variant_id": variants, "beta": [0.5, 0.01, 0.0, 0.0], "se": [0.05] * 4}
    )

    result = coloc_abf(exposure, outcome)

    assert result["nsnp"] == 4
    assert result["lead_variant"] == "s1"
    assert result["PP4"] > result["PP3"]
    assert result["PP4"] > 0.5


def test_mvmr_estimates_two_exposure_effects():
    rng = np.random.default_rng(5)
    variants = [f"s{i}" for i in range(30)]
    x1 = rng.normal(0.2, 0.05, 30)
    x2 = rng.normal(0.3, 0.05, 30)
    y = 0.7 * x1 - 0.4 * x2 + rng.normal(0, 0.01, 30)
    exposure = pd.DataFrame(
        [
            {"variant_id": variant, "exposure_id": "GeneA", "beta": a, "se": 0.01}
            for variant, a in zip(variants, x1)
        ]
        + [
            {"variant_id": variant, "exposure_id": "MetA", "beta": a, "se": 0.01}
            for variant, a in zip(variants, x2)
        ]
    )
    outcome = pd.DataFrame({"variant_id": variants, "beta": y, "se": 0.01})

    result = run_mvmr(exposure, outcome)

    assert set(result["exposure_id"]) == {"GeneA", "MetA"}
    assert result.loc[result["exposure_id"] == "GeneA", "beta"].iloc[0] > 0.4
    assert result.loc[result["exposure_id"] == "MetA", "beta"].iloc[0] < -0.2
