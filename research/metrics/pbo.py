"""
Probability of Backtest Overfitting (PBO) via Combinatorial Symmetric Cross-Validation (CSCV)
=============================================================================================
Reference:
Bailey, D. H., Borwein, J. M., Lopez de Prado, M., & Zhu, Q. J. (2016).
"The Probability of Backtest Overfitting."
Journal of Computational Finance, 20(4), 39-69.

Calculates the probability that the in-sample optimal strategy underperforms
the median strategy out-of-sample across all combinatorial splits.
"""

import sys
import math
import itertools
import numpy as np
from typing import List, Dict, Any, Union

from .stat_utils import norm_cdf

def compute_pbo_from_returns_matrix(
    returns_matrix: np.ndarray,
    n_slices: int = 16,
) -> Dict[str, Any]:
    """
    Computes PBO using CSCV:
    returns_matrix: shape (T, M) where T is time periods and M is number of model variants/trials.
    n_slices: even number of partitions S (default 16, yielding C(16, 8) = 12,870 combinations).
    """
    T, M = returns_matrix.shape
    if M < 2:
        return {
            "pbo": 0.0,
            "verdict": "SINGLE_STRATEGY_PBO_NOT_APPLICABLE",
            "c_combinations": 1,
            "statistically_sound": True
        }

    # Ensure even slices
    if n_slices % 2 != 0:
        n_slices -= 1
    n_slices = max(4, min(n_slices, 16))

    slice_len = T // n_slices
    if slice_len < 2:
        return {
            "pbo": 1.0,
            "verdict": "INSUFFICIENT_TIME_SERIES_LENGTH",
            "c_combinations": 0,
            "statistically_sound": False
        }

    # Partition returns into S slices of performance (mean or Sharpe per slice)
    # Shape: (S, M)
    slice_sharpes = np.zeros((n_slices, M), dtype=np.float64)
    for s in range(n_slices):
        start = s * slice_len
        end = (s + 1) * slice_len if s < n_slices - 1 else T
        sub = returns_matrix[start:end, :]
        means = np.mean(sub, axis=0)
        stds = np.std(sub, axis=0, ddof=1)
        stds = np.where(stds > 1e-8, stds, 1e-8)
        slice_sharpes[s, :] = means / stds

    # Generate combinatorial splits C(S, S/2)
    k = n_slices // 2
    combos = list(itertools.combinations(range(n_slices), k))
    total_combos = len(combos)

    logits = []
    oos_ranks = []
    overfit_count = 0

    all_indices = set(range(n_slices))

    for J in combos:
        J_set = set(J)
        J_bar = list(all_indices - J_set)
        J_list = list(J)

        # In-sample performance: mean across slices in J
        is_perf = np.mean(slice_sharpes[J_list, :], axis=0)
        # Out-of-sample performance: mean across slices in J_bar
        oos_perf = np.mean(slice_sharpes[J_bar, :], axis=0)

        # In-sample optimal strategy index
        best_is_idx = int(np.argmax(is_perf))

        # Rank of best_is_idx in OOS performance (1-based, 1 is best)
        # Order OOS descending
        sorted_oos_indices = np.argsort(-oos_perf)
        rank_oos = int(np.where(sorted_oos_indices == best_is_idx)[0][0]) + 1
        relative_rank = rank_oos / (M + 1.0) # between 0 and 1

        oos_ranks.append(rank_oos)

        # Overfit condition: relative_rank > 0.5 (i.e. below median OOS)
        if relative_rank > 0.5:
            overfit_count += 1

        # Logit lambda
        # Avoid log(0)
        p = max(1e-4, min(1.0 - 1e-4, 1.0 - relative_rank))
        lam = math.log(p / (1.0 - p))
        logits.append(lam)

    pbo = float(overfit_count) / float(total_combos)
    is_safe = pbo < 0.20 # Proposed threshold on Page 6

    return {
        "pbo": round(pbo, 4),
        "total_combinations_tested": total_combos,
        "n_slices": n_slices,
        "n_strategies_compared": M,
        "median_oos_rank": float(np.median(oos_ranks)),
        "mean_logit_lambda": round(float(np.mean(logits)), 3),
        "statistically_sound": is_safe,
        "verdict": "PASS_LOW_OVERFITTING" if is_safe else "FAIL_OVERFITTED_TO_PAST",
        "threshold": "< 0.20 (Bailey et al. 2016)"
    }

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    np.random.seed(42)
    # Test with 20 strategy parameter variants over 500 days
    # All are random noise: PBO should be high (~0.50)
    fake_matrix = np.random.normal(0.0001, 0.01, (500, 20))
    res = compute_pbo_from_returns_matrix(fake_matrix, n_slices=8)
    print("Random Strategies Matrix PBO:", res)

    # Test where strategy #0 has a real persistent signal
    strong_matrix = np.random.normal(0.0001, 0.01, (500, 20))
    strong_matrix[:, 0] += 0.003 # Persistent edge in variant 0
    res2 = compute_pbo_from_returns_matrix(strong_matrix, n_slices=8)
    print("Persistent Alpha Matrix PBO:", res2)
