"""
Deflated Sharpe Ratio (DSR) & Probabilistic Sharpe Ratio (PSR)
==============================================================
Reference:
Bailey, D. H., & Lopez de Prado, M. (2014).
"The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality."
The Journal of Portfolio Management, 40(5), 94-107.

Calculates the statistical significance of a Sharpe ratio after penalizing for:
1. Non-normality (skewness and fat-tailed kurtosis of returns)
2. Sample length (track record length T)
3. Multiple testing / Data Snooping (number of trials N_trials mined)
4. Variance of the mined Sharpe ratios (var_sharpe)
"""

import math
import sys
import numpy as np
from typing import List, Union, Dict, Any

from .stat_utils import norm_cdf, norm_ppf, sample_moments

EULER_MASCHERONI = 0.5772156649015328606065120900824024310421

def estimated_benchmark_sharpe(n_trials: int, var_sharpe: float) -> float:
    """
    Computes expected maximum Sharpe ratio under the null hypothesis
    that all N_trials have true Sharpe = 0.
    Formula (Bailey & Lopez de Prado 2014, Eq 8):
    E[max_k {SR_k}] = sqrt(var_sharpe) * ((1 - gamma) * Z^{-1}[1 - 1/N] + gamma * Z^{-1}[1 - 1/(N*e)])
    """
    if n_trials <= 1:
        return 0.0
    std_sharpe = math.sqrt(max(var_sharpe, 1e-6))
    z1 = norm_ppf(1.0 - 1.0 / n_trials)
    z2 = norm_ppf(1.0 - 1.0 / (n_trials * math.e))
    sr_0 = std_sharpe * ((1.0 - EULER_MASCHERONI) * z1 + EULER_MASCHERONI * z2)
    return max(0.0, float(sr_0))

def probabilistic_sharpe_ratio(
    observed_sr: float,
    benchmark_sr: float,
    n_samples: int,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
) -> float:
    """
    Computes PSR: probability that true SR > benchmark_sr given non-normal returns.
    Formula (Op. cit., Eq 5):
    Z = (observed_sr - benchmark_sr) * sqrt(T - 1) / sqrt(1 - skew*observed_sr + (kurt - 1)/4 * observed_sr^2)
    """
    if n_samples <= 2:
        return 0.5
    denom_sq = 1.0 - skewness * observed_sr + ((kurtosis - 1.0) / 4.0) * (observed_sr ** 2)
    denom = math.sqrt(max(denom_sq, 1e-6))
    z_stat = (observed_sr - benchmark_sr) * math.sqrt(n_samples - 1) / denom
    psr = float(norm_cdf(z_stat))
    return psr

def deflated_sharpe_ratio(
    returns: Union[List[float], np.ndarray],
    n_trials: int = 1,
    var_sharpe: float = 0.25,
    annualization_factor: float = 252.0,
) -> Dict[str, Any]:
    """
    Full DSR computation for a strategy returns series.
    Returns exact DSR value, benchmark SR_0, p-value, and pass/fail verdict.
    """
    arr = np.array(returns, dtype=np.float64)
    n = len(arr)
    if n < 5:
        return {
            "dsr_stat": 0.0,
            "p_value": 1.0,
            "sr_observed_ann": 0.0,
            "sr_benchmark_ann": 0.0,
            "n_samples": n,
            "n_trials": n_trials,
            "verdict": "FAIL_INSUFFICIENT_DATA",
            "statistically_significant": False
        }

    mean, std, skew, kurt = sample_moments(arr)
    sr_period = mean / std if std > 0 else 0.0
    sr_annualized = sr_period * math.sqrt(annualization_factor)

    # Benchmark Sharpe penalizing for N_trials mined
    sr_benchmark_ann = estimated_benchmark_sharpe(n_trials, var_sharpe)
    # Convert benchmark to period frequency
    sr_benchmark_period = sr_benchmark_ann / math.sqrt(annualization_factor)

    # Compute PSR with the penalised benchmark
    dsr_stat = probabilistic_sharpe_ratio(
        observed_sr=sr_period,
        benchmark_sr=sr_benchmark_period,
        n_samples=n,
        skewness=skew,
        kurtosis=kurt,
    )

    p_value = float(1.0 - dsr_stat)
    is_sig = (p_value < 0.05) and (sr_annualized > 0.0)

    return {
        "dsr_stat": round(dsr_stat, 4),
        "p_value": round(p_value, 4),
        "sr_observed_ann": round(sr_annualized, 3),
        "sr_benchmark_ann": round(sr_benchmark_ann, 3),
        "n_samples": n,
        "n_trials": n_trials,
        "skewness": round(skew, 3),
        "kurtosis": round(kurt, 3),
        "statistically_significant": is_sig,
        "verdict": "PASS_EMPIRICAL" if is_sig else "FAIL_DATA_SNOOPING_OR_WEAK",
        "formula_ref": "Bailey & Lopez de Prado (2014) JPM Eq 8"
    }

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    np.random.seed(42)
    fake_returns = np.random.normal(0.0005, 0.01, 250)
    res = deflated_sharpe_ratio(fake_returns, n_trials=1000, var_sharpe=0.5)
    print("Test 1 (Overfitted Noise 1,000 trials):", res)

    real_returns = np.random.normal(0.002, 0.008, 500)
    res2 = deflated_sharpe_ratio(real_returns, n_trials=50, var_sharpe=0.3)
    print("Test 2 (Strong Alpha):", res2)
