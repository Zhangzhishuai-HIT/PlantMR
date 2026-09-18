import numpy as np
import pandas as pd
import pytest

from plant_mr.gxe import gxe_ivw, select_gxe_instruments


def _table():
    rows = []
    z_values = {"WW": -1.0, "DS": 1.0, "REC": 0.0}
    for snp, bx in [("s1", 0.20), ("s2", 0.15), ("s3", 0.25)]:
        for env, z in z_values.items():
            theta = 0.5 + 0.2 * z
            rows.append({
                "SNP": snp,
                "environment": env,
                "environment_value": z,
                "exposure_beta": bx,
                "exposure_se": 0.01,
                "exposure_pval": 1e-20,
                "outcome_beta": bx * theta,
                "outcome_se": 0.02,
                "outcome_pval": 1e-8,
                "eaf": 0.4,
            })
    return pd.DataFrame(rows)


def test_gxe_ivw_recovers_intercept_and_environment_slope():
    result = gxe_ivw(_table())
    assert result.method == "gxe_ivw"
    assert np.isclose(result.intercept, 0.5, atol=1e-8)
    assert np.isclose(result.slope, 0.2, atol=1e-8)
    assert result.n_snp == 3
    assert result.n_environment == 3
    assert 0 <= result.slope_pval <= 1


def test_gxe_ivw_accepts_environment_and_ld_correlation():
    env_corr = pd.DataFrame(
        [[1.0, 0.4, 0.2], [0.4, 1.0, 0.3], [0.2, 0.3, 1.0]],
        index=["DS", "REC", "WW"], columns=["DS", "REC", "WW"],
    )
    ld = pd.DataFrame(
        [[1.0, 0.2, 0.1], [0.2, 1.0, 0.25], [0.1, 0.25, 1.0]],
        index=["s1", "s2", "s3"], columns=["s1", "s2", "s3"],
    )
    result = gxe_ivw(_table(), environment_correlation=env_corr, ld_correlation=ld)
    assert result.covariance_source == "environment_and_ld_correlation"
    assert np.isfinite(result.slope_se)
    assert result.covariance_rank == 9


def test_gxe_selection_keeps_only_snps_passing_in_every_environment():
    table = _table()
    table.loc[(table.SNP == "s2") & (table.environment == "DS"), "exposure_pval"] = 0.1
    selected, audit = select_gxe_instruments(table, p_threshold=5e-8, f_threshold=10, maf_threshold=0.01)
    assert set(selected.SNP) == {"s1", "s3"}
    assert audit["excluded_incomplete_qc"] == 1
    assert audit["selected"] == 2


def test_gxe_rejects_incomplete_environment_grid():
    table = _table().query("not (SNP == 's3' and environment == 'REC')")
    with pytest.raises(ValueError, match="complete environment grid"):
        gxe_ivw(table)


def test_gxe_q_degrees_of_freedom_uses_covariance_rank_for_singular_ld():
    table = _table()
    snps = ["s1", "s2", "s3"]
    ld = pd.DataFrame(np.ones((3, 3)), index=snps, columns=snps)
    result = gxe_ivw(table, ld_correlation=ld)
    assert result.covariance_rank == 3
    assert result.q_df == 1
