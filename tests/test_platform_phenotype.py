import numpy as np
import pandas as pd

from plant_mr.platform.phenotype import (
    as_phenotype_matrix,
    merge_environments,
    qc_phenotype,
)


def test_phenotype_qc_imputes_transforms_and_audits_outliers():
    long = pd.DataFrame(
        {
            "sample_id": ["p1", "p1", "p2", "p2", "p3", "p3"],
            "trait": ["height", "yield"] * 3,
            "value": [1.0, 2.0, np.nan, 2.5, 100.0, 3.0],
        }
    )
    matrix = as_phenotype_matrix(long)

    result = qc_phenotype(
        matrix,
        missing_threshold=0.5,
        impute="mean",
        transform="zscore",
        outlier_z=3.0,
    )

    assert result.matrix.isna().sum().sum() == 0
    assert result.matrix.shape == (3, 2)
    assert result.audit["imputation"] == "mean"
    assert result.audit["transform"] == "zscore"
    assert result.audit["outliers_flagged"] >= 0


def test_merge_environments_produces_mean_blue_and_blup_outputs():
    data = pd.DataFrame(
        {
            "sample_id": ["p1", "p1", "p2", "p2", "p3", "p3"],
            "trait": ["height"] * 6,
            "environment": ["E1", "E2"] * 3,
            "value": [10.0, 12.0, 20.0, 22.0, 30.0, 32.0],
        }
    )

    outputs = {method: merge_environments(data, method=method) for method in ("mean", "blue", "blup")}

    assert all(set(frame.columns) >= {"sample_id", "trait", "value", "method"} for frame in outputs.values())
    assert outputs["mean"].set_index("sample_id").loc["p1", "value"] == 11.0
    assert outputs["blue"]["method"].iloc[0] == "blue"
    assert outputs["blup"]["method"].iloc[0] == "blup"
