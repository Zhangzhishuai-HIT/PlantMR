import numpy as np
import pandas as pd
import pytest

from plant_mr.platform.genotype import (
    as_genotype_matrix,
    genotype_from_vcf,
    kinship_matrix,
    pca_scores,
    qc_genotype,
)


def test_genotype_qc_filters_missingness_and_imputes_mean():
    long = pd.DataFrame(
        {
            "sample_id": ["p1", "p1", "p2", "p2", "p3", "p3", "p4", "p4"],
            "variant_id": ["s1", "s2"] * 4,
            "dosage": [0, 0, 1, np.nan, 2, 2, np.nan, 2],
        }
    )
    matrix = as_genotype_matrix(long)

    result = qc_genotype(
        matrix,
        maf_threshold=0.2,
        variant_missing_threshold=0.25,
        sample_missing_threshold=0.5,
        impute="mean0",
    )

    assert list(result.matrix.index) == ["p1", "p2", "p3", "p4"]
    assert result.matrix.isna().sum().sum() == 0
    assert result.audit["variants_input"] == 2
    assert result.audit["imputation"] == "mean0"


def test_pca_and_kinship_return_sample_aligned_outputs():
    matrix = pd.DataFrame(
        [[0, 0, 1], [1, 0, 2], [2, 1, 2], [1, 2, 0]],
        index=["p1", "p2", "p3", "p4"],
        columns=["s1", "s2", "s3"],
        dtype=float,
    )

    pcs = pca_scores(matrix, n_components=2)
    kinship = kinship_matrix(matrix)

    assert list(pcs.index) == list(matrix.index)
    assert list(pcs.columns) == ["PC1", "PC2"]
    assert kinship.index.tolist() == matrix.index.tolist()
    assert kinship.columns.tolist() == matrix.index.tolist()
    np.testing.assert_allclose(kinship.to_numpy(), kinship.to_numpy().T)


def test_vcf_reader_decodes_dosage_and_missing(tmp_path):
    vcf = tmp_path / "demo.vcf"
    vcf.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tp1\tp2\n"
        "1\t10\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t./.\n"
        "1\t20\trs2\tC\tT\t.\tPASS\t.\tGT\t1/1\t0/0\n",
        encoding="utf-8",
    )

    matrix = genotype_from_vcf(vcf)

    assert matrix.index.tolist() == ["p1", "p2"]
    assert matrix.columns.tolist() == ["1:10:A:G", "rs2"]
    assert matrix.loc["p1", "1:10:A:G"] == 1
    assert np.isnan(matrix.loc["p2", "1:10:A:G"])
    assert matrix.loc["p1", "rs2"] == 2
