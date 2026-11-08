"""
Pure Python & NumPy Statistical Utilities (Self-Contained, Zero External SciPy Dependency)
=========================================================================================
Implements:
1. norm_cdf(z): Standard normal cumulative distribution function
2. norm_ppf(p): Standard normal percent point function (inverse CDF) using Acklam's algorithm
3. sample_skew_kurt(x): Unbiased sample skewness and Pearson kurtosis
"""

import math
import numpy as np
from typing import Tuple

def norm_cdf(z: float) -> float:
    """Standard normal cumulative distribution function Phi(z)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def norm_ppf(p: float) -> float:
    """
    Inverse standard normal cumulative distribution function (quantile function).
    Implementation of Peter J. Acklam's algorithm (accurate to 1.15e-9).
    """
    if p <= 0.0:
        return -9.0
    if p >= 1.0:
        return 9.0

    # Coefficients in rational approximations
    a = [
        -3.969683028665376e+01,
         2.209460984245205e+02,
        -2.759285104469687e+02,
         1.383577518672690e+02,
        -3.066479806614716e+01,
         2.506628277459239e+00
    ]
    b = [
        -5.447609879822406e+01,
         1.615858368580409e+02,
        -1.556989798598866e+02,
         6.680131188771972e+01,
        -1.328068155288572e+01
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e+00,
        -2.549732539343734e+00,
         4.374664141464968e+00,
         2.938163982698783e+00
    ]
    d = [
         7.784695709041462e-03,
         3.224671290700398e-01,
         2.445134137142996e+00,
         3.754408661907416e+00
    ]

    p_low = 0.02425
    p_high = 1.0 - p_low

    if p < p_low:
        # Rational approximation for lower region
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
               ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1.0)
    elif p > p_high:
        # Rational approximation for upper region
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1.0)
    else:
        # Rational approximation for central region
        q = p - 0.5
        r = q * q
        return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5])*q / \
               (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1.0)

def sample_moments(x: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Computes unbiased sample mean, sample std, sample skewness (gamma_3),
    and Pearson sample kurtosis (gamma_4, normal = 3.0).
    """
    n = len(x)
    if n < 3:
        return 0.0, 1.0, 0.0, 3.0

    mean = float(np.mean(x))
    diff = x - mean
    var = float(np.sum(diff ** 2) / (n - 1))
    std = math.sqrt(var) if var > 0 else 1e-8

    # Unbiased sample skewness (Fisher-Pearson)
    m3 = float(np.sum(diff ** 3) / n)
    m2 = float(np.sum(diff ** 2) / n)
    if m2 > 0 and n > 2:
        skew = (math.sqrt(n * (n - 1.0)) / (n - 2.0)) * (m3 / (m2 ** 1.5))
    else:
        skew = 0.0

    # Unbiased sample kurtosis
    m4 = float(np.sum(diff ** 4) / n)
    if m2 > 0 and n > 3:
        # Pearson kurtosis (normal distribution = 3.0)
        unbiased_kurt = ((n - 1.0) / ((n - 2.0) * (n - 3.0))) * ((n + 1.0) * (m4 / (m2 ** 2)) - 3.0 * (n - 1.0)) + 3.0
    else:
        unbiased_kurt = 3.0

    return mean, std, float(skew), float(unbiased_kurt)

if __name__ == "__main__":
    # Test accuracy against known standard normal percentiles
    print("norm_cdf(0.0) =", norm_cdf(0.0))   # 0.5
    print("norm_cdf(1.96) =", norm_cdf(1.96)) # ~0.975
    print("norm_ppf(0.5) =", norm_ppf(0.5))   # 0.0
    print("norm_ppf(0.975) =", norm_ppf(0.975)) # ~1.95996
    arr = np.random.normal(0, 1, 1000)
    m, s, sk, kt = sample_moments(arr)
    print(f"Sample Moments: mean={m:.3f}, std={s:.3f}, skew={sk:.3f}, kurt={kt:.3f}")
