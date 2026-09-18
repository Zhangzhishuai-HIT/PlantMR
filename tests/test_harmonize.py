import pandas as pd

from plant_mr.harmonize import harmonize_summary


def test_reversed_alleles_flip_outcome_beta():
    exposure = pd.DataFrame(
        {
            "SNP": ["s1"], "effect_allele": ["A"], "other_allele": ["G"],
            "beta": [0.2], "se": [0.05], "pval": [1e-6], "eaf": [0.4],
        }
    )
    outcome = pd.DataFrame(
        {
            "SNP": ["s1"], "effect_allele": ["G"], "other_allele": ["A"],
            "beta": [0.3], "se": [0.1], "pval": [0.2], "eaf": [0.6],
        }
    )
    result = harmonize_summary(exposure, outcome)
    row = result.data.iloc[0]
    assert row.outcome_beta == -0.3
    assert row.harmonization_status == "flipped"


def test_ambiguous_palindromic_variant_is_dropped_without_safe_eaf():
    exposure = pd.DataFrame(
        {
            "SNP": ["s1"], "effect_allele": ["A"], "other_allele": ["T"],
            "beta": [0.2], "se": [0.05], "pval": [1e-6], "eaf": [0.5],
        }
    )
    outcome = exposure.copy()
    result = harmonize_summary(exposure, outcome)
    assert len(result.data) == 0
    assert result.dropped["ambiguous_palindromic"] == 1
