import numpy as np
import pandas as pd
import pytest

from plant_mr.comparators import summary_mr_gxe


def _table(exposure_slope=0.25, pleiotropy=0.1):
    rows = []
    for j, bx in enumerate([0.20, 0.16, 0.24, 0.19], start=1):
        for env, z in [("E1", -1.0), ("E2", 1.0), ("E3", 0.0)]:
            bx_env = bx * (1.0 + exposure_slope * z)
            by = 0.5 * bx_env + pleiotropy
            rows.append({
                "SNP": "s%02d" % j,
                "environment": env,
                "environment_value": z,
                "exposure_beta": bx_env,
                "exposure_se": 0.01,
                "outcome_beta": by,
                "outcome_se": 0.02,
            })
    return pd.DataFrame(rows)


def test_summary_mr_gxe_recovers_causal_slope_and_pleiotropic_intercept():
    result = summary_mr_gxe(_table())
    assert result.method == "summary_mr_gxe"
    assert np.isclose(result.causal_slope, 0.5, atol=1e-8)
    assert np.isclose(result.pleiotropy_intercept, 0.1, atol=1e-8)
    assert result.n_environment == 3
    assert result.n_snp == 4


def test_summary_mr_gxe_uses_exposure_only_weights():
    table = _table()
    result_a = summary_mr_gxe(table)
    table.loc[0, "outcome_beta"] += 10.0
    result_b = summary_mr_gxe(table)
    assert result_a.score_weights is not None
    assert np.allclose(result_a.score_weights, result_b.score_weights)


def test_summary_mr_gxe_rejects_incomplete_environment_grid():
    table = _table().query("not (SNP == 's04' and environment == 'E2')")
    with pytest.raises(ValueError, match="complete environment grid"):
        summary_mr_gxe(table)
