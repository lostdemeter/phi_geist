"""
Riemann-zero jump table detection — v3 port.

Detects switch/case structures in compiled binaries by projecting
potential jump table target addresses through Riemann zeros and
measuring phase increment regularity.

Key insight:
  Jump table targets are at addresses base, base+step, base+2*step, ...
  Their Riemann phases increment by a CONSTANT amount:
    Δφₙ = γₙ · step mod 2π
  Random data has uncorrelated increments.
"""

import math
from phase import riemann_zero

TWOPI = 2.0 * math.pi


def increment_regularity(targets: list[int], k: int = 3) -> float:
    """Measure regularity of phase increments between consecutive targets.
    
    Returns a score in [0, 1] where 1 = perfectly regular (jump table).
    """
    if len(targets) < 3:
        return 0.0
    sorted_t = sorted(targets)
    regularities = []
    for z in range(k):
        gamma = riemann_zero(z + 1)
        increments = []
        for i in range(1, len(sorted_t)):
            delta = sorted_t[i] - sorted_t[i - 1]
            increments.append((gamma * delta) % TWOPI)
        if increments:
            mean_inc = sum(increments) / len(increments)
            var_inc = sum((inc - mean_inc) ** 2 for inc in increments) / len(increments)
            max_var = (TWOPI ** 2) / 12.0
            reg = max(0.0, 1.0 - math.sqrt(var_inc / max_var))
            regularities.append(reg)
    return sum(regularities) / len(regularities) if regularities else 0.0


def is_jump_table(targets: list[int], code_range: tuple[int, int] | None = None,
                  min_entries: int = 3) -> tuple[bool, float]:
    """Detect if address set forms a jump table.
    
    Returns (is_table, regularity_score).
    """
    if len(targets) < min_entries:
        return False, 0.0
    distinct = list(set(targets))
    if len(distinct) < min_entries:
        return False, 0.0
    if code_range:
        lo, hi = code_range
        if not all(lo <= t <= hi for t in distinct):
            return False, 0.0
    reg = increment_regularity(distinct, 3)
    # Check pointer-sized spacing (4 or 8 bytes between table slots)
    sorted_t = sorted(distinct)
    gaps = [sorted_t[i+1] - sorted_t[i] for i in range(len(sorted_t) - 1)]
    mean_gap = sum(gaps) / len(gaps) if gaps else 0
    ptr_ok = any(abs(mean_gap / ps - round(mean_gap / ps)) < 0.3 for ps in (4, 8)) if mean_gap > 0 else False
    return reg > 0.5 and ptr_ok, reg
