#!/home/user/zhangzhishuai/.local/share/mamba/envs/py36/bin/python
import json
from pathlib import Path

import h5py
import numpy as np

root = Path(__file__).resolve().parents[1]
h5_path = root / "data/external/arabidopsis_1001genomes/1001_SNP_MATRIX/ imputed_snps_binary.hdf5"
h5_path = root / "data/external/arabidopsis_1001genomes/1001_SNP_MATRIX/imputed_snps_binary.hdf5"
outdir = root / "data/external/arabidopsis_1001genomes"
outdir.mkdir(parents=True, exist_ok=True)

target = 3881093
window = 20000
with h5py.File(str(h5_path), "r") as h:
    positions = h["positions"]
    chr1_end = int(np.where(np.diff(positions[:3000000]) < 0)[0][0]) + 1
    lo = int(np.searchsorted(positions[:chr1_end], target - window))
    hi = int(np.searchsorted(positions[:chr1_end], target + window + 1))
    region_positions = positions[lo:hi]
    region_genotypes = h["snps"][lo:hi, :]
    accessions = h["accessions"][:]
    # Every 1000th marker is enough to construct a reproducibility PC covariate.
    pc_genotypes = h["snps"][::1000, :].astype(np.float64)

pc_genotypes -= pc_genotypes.mean(axis=1, keepdims=True)
# SVD on variants x accessions; columns are accession scores.
u, singular_values, vt = np.linalg.svd(pc_genotypes, full_matrices=False)
pc_scores = (vt[:5, :].T * singular_values[:5])
accession_ids = np.array([x.decode("utf-8") for x in accessions])
np.savez_compressed(
    outdir / "AT1G11560_region_genotypes.npz",
    positions=np.asarray(region_positions, dtype=np.int32),
    genotypes=np.asarray(region_genotypes, dtype=np.int8),
    accessions=accession_ids,
)
with (outdir / "AT1G11560_region_metadata.json").open("w", encoding="utf-8") as handle:
    json.dump({
        "assembly": "TAIR10-compatible 1001 Genomes v3.1 matrix",
        "target_position_chr1": target,
        "window_bp": window,
        "region_rows": int(hi - lo),
        "accessions": int(len(accession_ids)),
        "chromosome1_end_index": chr1_end,
        "source_tar_sha256": "015fec67d8de2048f8a46d7f3abac848ecb1e002340cbdc98eccaae5fc69ca0a",
        "source_matrix_md5": "6857bf13f35d3e36d555958ef33d7b77",
        "pc_marker_stride": 1000,
    }, handle, indent=2)
with (outdir / "1001genomes_PC5.tsv").open("w", encoding="utf-8") as handle:
    handle.write("accession_id\tPC1\tPC2\tPC3\tPC4\tPC5\n")
    for acc, row in zip(accession_ids, pc_scores):
        handle.write(acc + "\t" + "\t".join("%.12g" % value for value in row) + "\n")
print("region", region_genotypes.shape, "positions", int(region_positions[0]), int(region_positions[-1]))
print("target_present", int(target in set(int(x) for x in region_positions)))
print("pc", pc_scores.shape)
