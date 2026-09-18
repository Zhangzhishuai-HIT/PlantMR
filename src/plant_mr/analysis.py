from dataclasses import dataclass
from typing import Optional

import pandas as pd

from .estimators import ivw_fixed, ivw_random, leave_one_out, mr_egger
from .harmonize import HarmonizationResult, harmonize_summary
from .instruments import clump_instruments, select_instruments


@dataclass
class PairAnalysis:
    harmonized: HarmonizationResult
    selected: pd.DataFrame
    audit: dict
    methods: list[dict]
    leave_one_out: Optional[pd.DataFrame]


def analyze_pair(exposure: pd.DataFrame, outcome: pd.DataFrame, *,
                 p_threshold: float = 5e-8, f_threshold: float = 10.0,
                 maf_threshold: float = 0.01, ld_matrix: Optional[pd.DataFrame] = None,
                 ld_r2: float = 0.01) -> PairAnalysis:
    harmonized = harmonize_summary(exposure, outcome)
    selected, audit = select_instruments(
        harmonized.data,
        p_threshold=p_threshold,
        f_threshold=f_threshold,
        maf_threshold=maf_threshold,
    )
    if ld_matrix is not None and not selected.empty:
        selected, removed = clump_instruments(selected, ld_matrix, r2_threshold=ld_r2)
        audit["excluded_ld"] = len(removed)
        audit["selected"] = int(len(selected))
    if selected.empty:
        raise ValueError("no instruments remained after harmonization, QC and LD filtering")
    methods = [ivw_fixed(selected).as_dict(), ivw_random(selected).as_dict()]
    if len(selected) >= 3:
        methods.append(mr_egger(selected).as_dict())
    loo = leave_one_out(selected) if len(selected) >= 2 else None
    return PairAnalysis(harmonized, selected, audit, methods, loo)
