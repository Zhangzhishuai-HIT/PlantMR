import pandas as pd

from plant_mr.platform.annotation import annotate_variants
from plant_mr.platform.genotype import tsne_scores, upgma_newick


def test_tsne_and_upgma_are_sample_labeled():
    matrix = pd.DataFrame(
        [[0, 0], [1, 0], [2, 2], [2, 1], [0, 2], [1, 1]],
        index=[f"p{i}" for i in range(6)],
        columns=["s1", "s2"],
        dtype=float,
    )

    tsne = tsne_scores(matrix, perplexity=2)
    tree = upgma_newick(matrix)

    assert tsne.index.tolist() == matrix.index.tolist()
    assert list(tsne.columns) == ["TSNE1", "TSNE2"]
    assert tree.endswith(";")
    assert all(sample in tree for sample in matrix.index)


def test_variant_annotation_reports_overlap_and_nearest_gene():
    variants = pd.DataFrame(
        {
            "variant_id": ["s1", "s2"],
            "chromosome": ["1", "1"],
            "position": [105, 500],
        }
    )
    genes = pd.DataFrame(
        {
            "feature_id": ["g1"],
            "gene_symbol": ["GeneA"],
            "chromosome": ["1"],
            "start": [100],
            "end": [200],
        }
    )

    result = annotate_variants(variants, genes, flank=500)

    assert result.loc[result["variant_id"] == "s1", "relationship"].iloc[0] == "within"
    assert result.loc[result["variant_id"] == "s2", "gene_symbol"].iloc[0] == "GeneA"
    assert result.loc[result["variant_id"] == "s2", "relationship"].iloc[0] == "nearest"
