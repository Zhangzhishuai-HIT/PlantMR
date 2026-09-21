import pandas as pd

from plant_mr.platform.formats import read_hapmap, read_plink_raw
from plant_mr.platform.haplotype import summarize_haplotypes


def test_plink_raw_and_hapmap_readers_return_dosage_matrix(tmp_path):
    raw = tmp_path / "x.raw"
    raw.write_text(
        "FID IID PAT MAT SEX PHENOTYPE rs1_A rs2_G\n"
        "f1 p1 0 0 0 -9 0 2\n"
        "f1 p2 0 0 0 -9 1 0\n",
        encoding="utf-8",
    )
    hap = tmp_path / "x.hmp.txt"
    hap.write_text(
        "rs#\talleles\tchrom\tpos\tstrand\tassembly#\tcenter\tprotLSID\tpanelLSID\tQCcode\tp1\tp2\n"
        "s1\tA/G\t1\t10\t+\tRef\t.\t.\t.\t.\tAA\tAG\n",
        encoding="utf-8",
    )

    plink = read_plink_raw(raw)
    hapmap = read_hapmap(hap)

    assert plink.index.tolist() == ["p1", "p2"]
    assert plink.columns.tolist() == ["rs1", "rs2"]
    assert hapmap.loc["p1", "s1"] == 0
    assert hapmap.loc["p2", "s1"] == 1


def test_haplotype_summary_reports_group_sizes_and_trait_means():
    genotype = pd.DataFrame({"s1": [0, 1, 0], "s2": [0, 0, 1]}, index=["p1", "p2", "p3"])
    phenotype = pd.Series([1.0, 2.0, 3.0], index=["p1", "p2", "p3"], name="height")

    result = summarize_haplotypes(genotype, phenotype, lead_variants=["s1", "s2"])

    assert set(result.columns) >= {"haplotype", "n", "mean", "se"}
    assert result["n"].sum() == 3
