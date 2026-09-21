import numpy as np
import pandas as pd

from plant_mr.platform.gwas_models import run_matrix_gwas
from plant_mr.platform.genotype import kinship_matrix


def test_matrix_gwas_supports_covariates_and_kinship_model():
    rng = np.random.default_rng(123)
    samples = [f"p{i:03d}" for i in range(50)]
    population = np.repeat([0.0, 1.0], 25)
    causal = rng.integers(0, 3, size=50)
    null = rng.integers(0, 3, size=50)
    genotype = pd.DataFrame(
        {"s_causal": causal, "s_null": null}, index=samples, dtype=float
    )
    phenotype = pd.DataFrame(
        {
            "sample_id": samples,
            "trait": "height",
            "value": 1.5 * causal + 2.0 * population + rng.normal(0, 0.2, 50),
        }
    )
    covariates = pd.DataFrame({"PC1": population}, index=samples)
    kinship = kinship_matrix(genotype)

    ols = run_matrix_gwas(genotype, phenotype, trait="height", covariates=covariates, model="ols")
    mlm = run_matrix_gwas(
        genotype,
        phenotype,
        trait="height",
        covariates=covariates,
        kinship=kinship,
        model="gemma_mlm",
    )

    assert set(ols["variant_id"]) == {"s_causal", "s_null"}
    assert ols.loc[ols["variant_id"] == "s_causal", "pval"].iloc[0] < 1e-8
    assert set(mlm["model"]) == {"gemma_mlm"}
    assert mlm.loc[mlm["variant_id"] == "s_causal", "pval"].iloc[0] < 1e-6
    assert (mlm["n_covariates"] == 1).all()
