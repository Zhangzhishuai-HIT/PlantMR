import pandas as pd

from plant_mr.instruments import select_instruments


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
