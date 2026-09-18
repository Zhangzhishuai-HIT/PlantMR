import numpy as np
import pandas as pd
from scipy.stats import chi2

from plant_mr.estimators import ivw_fixed, ivw_random, leave_one_out, mr_egger, wald_ratio


def test_wald_ratio_matches_outcome_over_exposure():
    estimate = wald_ratio(beta_exposure=0.5, se_exposure=0.1, beta_outcome=0.2, se_outcome=0.05)
    assert np.isclose(estimate.beta, 0.4)
    assert estimate.nsnp == 1


def test_fixed_ivw_is_weighted_ratio_average():
    table = pd.DataFrame(
        {
            "exposure_beta": [1.0, 2.0],
            "exposure_se": [0.1, 0.2],
            "outcome_beta": [0.5, 1.0],
            "outcome_se": [0.1, 0.2],
        }
    )
    result = ivw_fixed(table)
    assert np.isclose(result.beta, 0.5)
    assert result.nsnp == 2
    assert 0 <= result.pval <= 1


def test_ivw_q_pvalue_uses_number_of_instruments_as_degrees_of_freedom():
    table = pd.DataFrame(
        {
            "exposure_beta": [1.0, 1.0, 1.0],
            "exposure_se": [0.1, 0.1, 0.1],
            "outcome_beta": [0.5, 0.7, 0.9],
            "outcome_se": [0.1, 0.1, 0.1],
        }
    )
    result = ivw_fixed(table)
    assert np.isclose(result.q_pval, chi2.sf(result.q, df=2))


def test_random_effects_ivw_reports_tau2_and_not_smaller_standard_error():
    table = pd.DataFrame(
        {
            "exposure_beta": [1.0, 1.0, 1.0],
            "exposure_se": [0.1, 0.1, 0.1],
            "outcome_beta": [0.5, 0.7, 0.9],
            "outcome_se": [0.1, 0.1, 0.1],
        }
    )
    fixed = ivw_fixed(table)
    random = ivw_random(table)
    assert random.method == "ivw_random"
    assert random.tau2 > 0
    assert random.se >= fixed.se


def test_egger_returns_slope_and_intercept_for_three_instruments():
    table = pd.DataFrame(
        {
            "exposure_beta": [0.2, 0.4, 0.6],
            "exposure_se": [0.02, 0.02, 0.02],
            "outcome_beta": [0.1, 0.2, 0.3],
            "outcome_se": [0.02, 0.02, 0.02],
        }
    )
    result = mr_egger(table)
    assert result.method == "mr_egger"
    assert np.isclose(result.beta, 0.5, atol=1e-8)
    assert result.intercept is not None


def test_leave_one_out_returns_one_row_per_removed_instrument():
    table = pd.DataFrame(
        {
            "SNP": ["s1", "s2", "s3"],
            "exposure_beta": [1.0, 1.0, 1.0],
            "exposure_se": [0.1, 0.1, 0.1],
            "outcome_beta": [0.5, 0.6, 0.7],
            "outcome_se": [0.1, 0.1, 0.1],
        }
    )
    result = leave_one_out(table)
    assert result["removed_snp"].tolist() == ["s1", "s2", "s3"]
    assert len(result) == 3
