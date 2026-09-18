# GSE54680 processed target extraction

Source series: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE54680

The series contains 10°C and 16°C Arabidopsis samples. The repository keeps only target-gene rows extracted from the per-sample processed expression tables, not raw reads. `scripts/fetch_gse54680_target.py` and `scripts/fetch_gse54680_targets.py` record the extraction procedure and failure counts.

AT1G11560 was too sparse in the 10°C expression subset to supply a conventional F≥10 environment-specific eQTL in the local re-analysis. This negative result is retained as a data-audit boundary; the final real-data application uses baseline GSE80744 expression and FT10/FT16 outcome environments instead.
