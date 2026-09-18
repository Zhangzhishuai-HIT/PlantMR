import numpy as np
import pandas as pd

from plant_mr.instruments import clump_instruments, select_instruments


def test_select_instruments_reports_weak_instrument_reason():
    table = pd.DataFrame(
        {
            "SNP": ["strong", "weak"],
            "exposure_beta": [0.5, 0.01],
            "exposure_se": [0.05, 0.05],
            "exposure_pval": [1e-8, 0.8],
            "eaf": [0.4, 0.4],
        }
    )
    selected, audit = select_instruments(table, p_threshold=5e-8, f_threshold=10)
    assert selected.SNP.tolist() == ["strong"]
    assert audit["excluded_pval"] == 1
    assert audit["selected"] == 1


def test_ld_clumping_keeps_more_significant_variant():
    table = pd.DataFrame(
        {
            "SNP": ["s1", "s2", "s3"],
            "exposure_beta": [0.5, 0.4, 0.3],
            "exposure_se": [0.05, 0.05, 0.05],
            "exposure_pval": [1e-10, 1e-8, 1e-9],
            "eaf": [0.4, 0.4, 0.4],
        }
    )
    ld = pd.DataFrame(
        [[1.0, 0.9, 0.0], [0.9, 1.0, 0.0], [0.0, 0.0, 1.0]],
        index=["s1", "s2", "s3"], columns=["s1", "s2", "s3"],
    )
    result, removed = clump_instruments(table, ld, r2_threshold=0.01)
    assert result.SNP.tolist() == ["s1", "s3"]
    assert removed == ["s2"]
