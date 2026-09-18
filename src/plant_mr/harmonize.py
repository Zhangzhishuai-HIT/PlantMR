from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from .schema import validate_summary


_COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C"}
_PALINDROMIC = {frozenset(("A", "T")), frozenset(("C", "G"))}


@dataclass(frozen=True)
class HarmonizationResult:
    data: pd.DataFrame
    dropped: Dict[str, int]


def _palindromic(a1: str, a2: str) -> bool:
    return frozenset((a1, a2)) in _PALINDROMIC


def _safe_palindromic(eaf_exposure: float, eaf_outcome: float, threshold: float = 0.08) -> bool:
    if not np.isfinite(eaf_exposure) or not np.isfinite(eaf_outcome):
        return False
    return min(abs(eaf_exposure - 0.5), abs(eaf_outcome - 0.5)) >= threshold


def harmonize_summary(exposure: pd.DataFrame, outcome: pd.DataFrame) -> HarmonizationResult:
    exp = validate_summary(exposure, "exposure").data
    out = validate_summary(outcome, "outcome").data
    merged = exp.merge(out, on="SNP", how="inner", suffixes=("_exposure", "_outcome"))
    rows = []
    dropped = {"missing_outcome": int(len(exp) - len(merged)), "ambiguous_palindromic": 0,
               "incompatible_alleles": 0, "duplicate": 0}
    for row in merged.itertuples(index=False):
        ea, oa = row.effect_allele_exposure, row.other_allele_exposure
        oe, oo = row.effect_allele_outcome, row.other_allele_outcome
        candidates = []
        if (oe, oo) == (ea, oa):
            candidates.append(("aligned", False))
        if (oe, oo) == (oa, ea):
            candidates.append(("flipped", True))
        if (_COMPLEMENT.get(oe), _COMPLEMENT.get(oo)) == (ea, oa):
            candidates.append(("complemented", False))
        if (_COMPLEMENT.get(oe), _COMPLEMENT.get(oo)) == (oa, ea):
            candidates.append(("complemented_flipped", True))
        if not candidates:
            dropped["incompatible_alleles"] += 1
            continue
        if _palindromic(ea, oa):
            if not _safe_palindromic(float(row.eaf_exposure), float(row.eaf_outcome)):
                dropped["ambiguous_palindromic"] += 1
                continue
            # Use allele frequencies to resolve the otherwise symmetric mapping.
            same_distance = abs(float(row.eaf_exposure) - float(row.eaf_outcome))
            reverse_distance = abs(float(row.eaf_exposure) - (1 - float(row.eaf_outcome)))
            candidates = [candidate for candidate in candidates if candidate[1] == (reverse_distance < same_distance)] or candidates
        status, flip = candidates[0]
        outcome_beta = -float(row.beta_outcome) if flip else float(row.beta_outcome)
        outcome_eaf = 1 - float(row.eaf_outcome) if flip else float(row.eaf_outcome)
        rows.append({
            "SNP": row.SNP,
            "exposure_beta": float(row.beta_exposure),
            "exposure_se": float(row.se_exposure),
            "exposure_pval": float(row.pval_exposure),
            "outcome_beta": outcome_beta,
            "outcome_se": float(row.se_outcome),
            "outcome_pval": float(row.pval_outcome),
            "eaf": float(row.eaf_exposure),
            "outcome_eaf": outcome_eaf,
            "harmonization_status": status,
        })
    return HarmonizationResult(data=pd.DataFrame(rows), dropped=dropped)
