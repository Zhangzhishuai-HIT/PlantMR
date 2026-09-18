# Arabidopsis 1001 Genomes inputs

Source: https://1001genomes.org/data/GMI-MPI/releases/v3.1/

The provider tarball and extracted 919 MB HDF5 matrix are intentionally ignored by Git. The repository keeps only:

- provider README and MD5 receipt;
- a 3,352-SNP region subset around Chr1:3,881,093 (`AT1G11560_region_genotypes.npz`);
- five whole-genome PC scores;
- one public accession VCF used to map REF/ALT labels;
- region metadata and source hashes.

The region subset was created by `scripts/extract_arabidopsis_region.py` from the provider HDF5 matrix.
