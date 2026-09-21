import pandas as pd
import pytest

from plant_mr.platform.association import normalize_association
from plant_mr.platform.sal import detect_sal


def test_normalize_association_preserves_context_and_source():
    data = pd.DataFrame(
        {
            "SNP": ["s1", "s2"],
            "beta": [0.2, -0.1],
            "se": [0.05, 0.04],
            "pval": [1e-8, 0.2],
            "eaf": [0.3, 0.4],
        }
    )

    result = normalize_association(
        data,
        trait="height",
        species="Zea_mays",
        assembly="RefGen_v5",
        source="demo-gwas.tsv",
        source_method="gemma_mlm",
    )

    assert result.loc[0, "variant_id"] == "s1"
    assert result.loc[0, "trait"] == "height"
    assert result.loc[0, "species"] == "Zea_mays"
    assert result.loc[0, "source_method"] == "gemma_mlm"


def test_detect_sal_uses_lead_and_ld_neighbors():
    gwas = pd.DataFrame(
        {
            "variant_id": ["s1", "s2", "s3", "s4"],
            "chromosome": [1, 1, 1, 2],
            "position": [100, 200, 1000, 100],
            "pval": [1e-10, 1e-6, 0.4, 1e-9],
            "beta": [0.2] * 4,
            "se": [0.05] * 4,
        }
    )
    ld = pd.DataFrame(
        [[1, 0.6, 0, 0], [0.6, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        index=["s1", "s2", "s3", "s4"],
        columns=["s1", "s2", "s3", "s4"],
    )

    result = detect_sal(gwas, ld_matrix=ld, p_lead=5e-8, p_secondary=1e-5, window=500)

    assert len(result) == 2
    lead1 = result.loc[result["lead_variant"] == "s1"].iloc[0]
    assert lead1["n_variants"] == 2
    assert lead1["start"] == 100
    assert lead1["end"] == 200
