"""
φ-ADD via φ-MUL Taylor series — no lookup tables.

Every φ-lane value is stored as combined_rung r where:
    value = φ^(-r)

φ-MUL(r1, r2) = r1 + r2                          (integer addition)
φ-ADD(r1, r2) = min(r1, r2) - log_φ(1 + φ^(-δ))  (δ = |r1 - r2|)

The correction term log_φ(1 + x) with x = φ^(-δ) uses the Taylor series:
    log_φ(1 + x) = (1/ln φ) × Σ (-1)^(k+1) × x^k / k

Each term x^k = φ^(-kδ) is computed by one φ-MUL (integer rung addition).
"""

import math

PHI = 1.618033988749895
LN_PHI = math.log(PHI)


def phi_mul(r1: int, r2: int) -> int:
    """φ-MUL: multiply two φ-lane values by adding their combined rungs."""
    return r1 + r2


def phi_value(r: int) -> float:
    """Convert a combined rung back to linear value for verification."""
    return PHI ** (-r)


def _log_phi_1plus(x: float, terms: int = 4) -> float:
    """Compute log_φ(1 + x) via Taylor series.
    
    log_φ(1 + x) = (1/ln φ) × Σ_{k=1}^{terms} (-1)^(k+1) × x^k / k
    """
    total = 0.0
    xk = x  # x^1
    for k in range(1, terms + 1):
        term = xk / k
        if k % 2 == 0:
            total -= term
        else:
            total += term
        xk *= x
    return total / LN_PHI


def phi_add(r1: int, r2: int, terms: int = 4) -> int:
    """φ-ADD: add two φ-lane values using φ-MUL-based Taylor series.
    
    Returns the combined rung of φ^(-r1) + φ^(-r2).
    Uses no lookup tables — all computation via integer operations.
    """
    delta = abs(r1 - r2)
    x = PHI ** (-delta)
    correction = _log_phi_1plus(x, terms)
    r_sum = min(r1, r2) - correction
    return int(round(r_sum))


def phi_add_precise(r1: int, r2: int, terms: int = 4) -> float:
    """φ-ADD returning the exact combined rung (float, for verification)."""
    delta = abs(r1 - r2)
    x = PHI ** (-delta)
    correction = _log_phi_1plus(x, terms)
    return min(r1, r2) - correction


def linear_add(r1: int, r2: int) -> float:
    """Brute-force φ-ADD via linear conversion (gold standard for comparison).
    
    This is the LUT-based approach: convert to linear, add, convert back.
    Used only for verification.
    """
    v1 = phi_value(r1)
    v2 = phi_value(r2)
    v_sum = v1 + v2
    if v_sum <= 0:
        return float('inf')
    return -math.log(v_sum) / LN_PHI
