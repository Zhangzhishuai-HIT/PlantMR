from typing import Dict, Tuple

import numpy as np
import pandas as pd


def select_instruments(table: pd.DataFrame, p_threshold: float = 5e-8,
                       f_threshold: float = 10.0, maf_threshold: float = 0.01) -> Tuple[pd.DataFrame, Dict[str, int]]:
    required = {"SNP", "exposure_beta", "exposure_se", "exposure_pval", "eaf"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"missing instrument columns: {', '.join(sorted(missing))}")
    work = table.copy()
    work["f_stat"] = (work["exposure_beta"] / work["exposure_se"]) ** 2
    audit = {"input": int(len(work)), "excluded_pval": 0, "excluded_f": 0, "excluded_maf": 0, "selected": 0}
    p_mask = work["exposure_pval"] <= p_threshold
    audit["excluded_pval"] = int((~p_mask).sum())
    work = work.loc[p_mask].copy()
    f_mask = work["f_stat"] >= f_threshold
    audit["excluded_f"] = int((~f_mask).sum())
    work = work.loc[f_mask].copy()
    maf = np.minimum(work["eaf"], 1 - work["eaf"])
    maf_mask = maf >= maf_threshold
    audit["excluded_maf"] = int((~maf_mask).sum())
    work = work.loc[maf_mask].copy()
    work = work.sort_values("SNP").reset_index(drop=True)
    audit["selected"] = int(len(work))
    return work, audit
