"""
Sequential Probability Ratio Test (SPRT) & CUSUM Performance Drift Detector
=============================================================================
Reference:
1. Wald, A. (1945). "Sequential Tests of Statistical Hypotheses."
   Annals of Mathematical Statistics, 16(2), 117-186.
2. Page, E. S. (1954). "Continuous Inspection Schemes."
   Biometrika, 41(1/2), 100-115.

Provides deterministic statistical gating for:
- Promotion Ladder: Testing whether live execution confirms edge (H1) or zero-edge (H0).
- Auto-Decommission: Detecting performance drift when live return cumulative deviation drops > 2 sigma / > 3 sigma.
"""

import sys
import math
import numpy as np
from typing import List, Dict, Any, Union

class SequentialProbabilityRatioTest:
    def __init__(
        self,
        mu_0: float = 0.0,            # H0: Zero edge
        mu_1: float = 0.001,          # H1: Expected backtest edge per trade
        sigma: float = 0.01,          # Standard deviation of trade returns
        alpha: float = 0.05,          # Type I error (false positive)
        beta: float = 0.10,           # Type II error (false negative)
    ):
        self.mu_0 = mu_0
        self.mu_1 = max(mu_1, 1e-6)
        self.sigma = max(sigma, 1e-6)
        self.alpha = alpha
        self.beta = beta

        # Wald decision thresholds
        self.lower_boundary = math.log(beta / (1.0 - alpha))
        self.upper_boundary = math.log((1.0 - beta) / alpha)

    def evaluate_sequence(self, returns: List[float]) -> Dict[str, Any]:
        """
        Calculates cumulative log-likelihood ratio Lambda_n for the sequence.
        Under Gaussian distribution:
        ln(f(x|H1)/f(x|H0)) = ((mu_1 - mu_0) / sigma^2) * (x - (mu_0 + mu_1) / 2)
        """
        if not returns:
            return {
                "decision": "CONTINUE_TESTING",
                "cum_llr": 0.0,
                "n_trades": 0,
                "lower_boundary": round(self.lower_boundary, 3),
                "upper_boundary": round(self.upper_boundary, 3),
            }

        llr_sum = 0.0
        llr_history = []
        half_sum_mu = 0.5 * (self.mu_0 + self.mu_1)
        scale = (self.mu_1 - self.mu_0) / (self.sigma ** 2)

        decision = "CONTINUE_TESTING"
        decision_idx = len(returns)

        for i, r in enumerate(returns):
            llr = scale * (r - half_sum_mu)
            llr_sum += llr
            llr_history.append(round(llr_sum, 3))

            if llr_sum >= self.upper_boundary and decision == "CONTINUE_TESTING":
                decision = "ACCEPT_H1_EDGE_PROVEN"
                decision_idx = i + 1
            elif llr_sum <= self.lower_boundary and decision == "CONTINUE_TESTING":
                decision = "ACCEPT_H0_EDGE_REJECTED"
                decision_idx = i + 1

        return {
            "decision": decision,
            "decision_trade_n": decision_idx,
            "cum_llr": round(llr_sum, 3),
            "n_trades": len(returns),
            "lower_boundary_h0": round(self.lower_boundary, 3),
            "upper_boundary_h1": round(self.upper_boundary, 3),
            "verdict": (
                "PROMOTE_TO_NEXT_STAGE" if decision == "ACCEPT_H1_EDGE_PROVEN" else
                ("DEMOTE_OR_KILL" if decision == "ACCEPT_H0_EDGE_REJECTED" else "COLLECT_MORE_DATA")
            )
        }

class CusumDriftDetector:
    def __init__(
        self,
        expected_mean: float = 0.001,
        expected_std: float = 0.01,
        allowance_k_sigma: float = 0.5, # Allowance parameter k = 0.5 * sigma
        threshold_2sigma: float = 2.0,
        threshold_3sigma: float = 3.0,
    ):
        self.expected_mean = expected_mean
        self.expected_std = max(expected_std, 1e-6)
        self.k = allowance_k_sigma * self.expected_std
        self.h2 = threshold_2sigma * self.expected_std
        self.h3 = threshold_3sigma * self.expected_std

    def detect_decay(self, returns: List[float]) -> Dict[str, Any]:
        """
        Page-Hinkley cumulative sum for negative drift (performance decay):
        S_t = max(0, S_{t-1} + (E[X] - X_t - k))
        """
        s_neg = 0.0
        s_history = []
        action = "NORMAL"

        for r in returns:
            # Downward deviation from expected mean
            dev = (self.expected_mean - r) - self.k
            s_neg = max(0.0, s_neg + dev)
            s_history.append(round(s_neg, 4))

        sigma_dev = round(s_neg / self.expected_std, 2)

        if s_neg >= self.h3:
            action = "AUTO_DECOMMISSION (เกิน 3 Sigma -> ปลดออกจากการเทรดทันที)"
        elif s_neg >= self.h2:
            action = "REDUCE_SIZE_50_PCT (เกิน 2 Sigma -> ลดขนาดสัญญาลง 50%)"
        else:
            action = "NORMAL_HEALTHY (ประสิทธิภาพปกติ)"

        return {
            "action": action,
            "cusum_score": round(s_neg, 4),
            "sigma_deviation": sigma_dev,
            "threshold_2sigma": round(self.h2, 4),
            "threshold_3sigma": round(self.h3, 4),
            "drift_detected": s_neg >= self.h2,
            "kill_triggered": s_neg >= self.h3
        }

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    np.random.seed(42)

    # Test SPRT with true positive alpha
    sprt = SequentialProbabilityRatioTest(mu_0=0.0, mu_1=0.002, sigma=0.01)
    good_trades = list(np.random.normal(0.0025, 0.01, 80))
    print("SPRT (Good Trades):", sprt.evaluate_sequence(good_trades))

    # Test SPRT with zero edge (under fees)
    bad_trades = list(np.random.normal(-0.0005, 0.01, 80))
    print("SPRT (Losing Trades):", sprt.evaluate_sequence(bad_trades))

    # Test CUSUM decay
    cusum = CusumDriftDetector(expected_mean=0.002, expected_std=0.01)
    decay_trades = list(np.random.normal(-0.004, 0.01, 50))
    print("CUSUM Drift on Decay:", cusum.detect_decay(decay_trades))
