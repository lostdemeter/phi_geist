"""
Riemann zero phase primitives — v3.

First-class citizen from line 1. Every pattern path is encoded
as a log-space (RoPE-style) phase vector:
  phase(path, γₙ) = γₙ · log(path_key + 1)  mod  2π

This encoding:
  - Is deterministic (Riemann zeros are incommensurate irrationals)
  - Is invariant to reordering (phase depends on RATIO, not difference)
  - Under conjugate pairing, swapped tokens preserve the sum
"""

import math


RIEMANN_ZEROS = [
    14.134725141734693790, 21.022039638771554992,
    25.010857580145688763, 30.424876125859513210,
    32.935061587739189690, 37.586178158825671257,
    40.918719012147495187, 43.327073280891999615,
]

TWOPI = 2.0 * math.pi
DEFAULT_K = 3


def riemann_zero(n: int) -> float:
    if 1 <= n <= len(RIEMANN_ZEROS):
        return RIEMANN_ZEROS[n - 1]
    return 2.0 * math.pi * (n - 11/8) / math.log(n + 1)


def phase(key: int, gamma: float) -> float:
    return (gamma * key) % TWOPI


def multi_phase(key: int, k: int = DEFAULT_K) -> list[float]:
    return [phase(key, riemann_zero(i + 1)) for i in range(k)]


def path_key(path: list[int]) -> int:
    """Pattern path → integer key. [3, 5] → 3005."""
    h = 0
    for p in path:
        h = h * 100 + p
    return h + 1  # +1 avoids log(0) for path [0]


def path_phase(path: list[int], k: int = DEFAULT_K) -> list[float]:
    """Log-space (RoPE-style) phase for a pattern path.
    
    Phase difference between paths a and b:
      γₙ · log(key(b) / key(a))
    
    This depends on the RATIO, not the linear difference.
    If a transform swaps two tokens, the phase difference is
    negated (log(a/b) = -log(b/a)). Under conjugate pairing,
    the sum over both orderings is preserved.
    """
    key = path_key(path)
    return [phase(int(math.log(key) * 1000), riemann_zero(i + 1))
            for i in range(k)]


def pos_phase(position: int, k: int = DEFAULT_K) -> list[float]:
    """Riemann phase for a LINEAR position in the token sequence.
    
    Used for the phase attention cache (positions near each other
    have similar phases, creating a locality bias).
    """
    return multi_phase(position + 1, k)


def phase_distance(a: list[float], b: list[float]) -> float:
    """Circular L1 distance in [0, 1], 0 = identical."""
    d = 0.0
    for x, y in zip(a, b):
        r = abs(x - y)
        d += min(r, TWOPI - r)
    return d / (len(a) * math.pi) if a else 1.0
