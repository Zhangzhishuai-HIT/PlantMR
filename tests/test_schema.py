import pandas as pd
import pytest

from plant_mr.schema import REQUIRED_COLUMNS, SchemaError, validate_summary


def valid_table():
    return pd.DataFrame(
        {
            "SNP": ["s1", "s2"],
            "effect_allele": ["A", "C"],
            "other_allele": ["G", "T"],
            "beta": [0.2, -0.1],
            "se": [0.05, 0.04],
            "pval": [1e-4, 0.01],
            "eaf": [0.4, 0.3],
        }
    )


def test_valid_summary_has_required_contract():
    result = validate_summary(valid_table(), label="exposure")
    assert result.label == "exposure"
    assert set(REQUIRED_COLUMNS).issubset(result.data.columns)
    assert len(result.data) == 2


def test_missing_required_column_fails_with_column_name():
    table = valid_table().drop(columns=["se"])
    with pytest.raises(SchemaError, match="se"):
        validate_summary(table, label="outcome")


def test_invalid_allele_and_standard_error_are_rejected():
    table = valid_table()
    table.loc[0, "effect_allele"] = "AA"
    table.loc[1, "se"] = 0
    with pytest.raises(SchemaError, match="allele|se"):
        validate_summary(table, label="exposure")
