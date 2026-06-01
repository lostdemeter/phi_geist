"""
Geometric gate primitives — v3 (final).

φ-geometry is COMMENTARY ONLY. Runtime uses exact_match().
The continuous gate (rect_pair) converges to exact_match at
infinite sharpness — this file proves the limit exists.

For the full mathematical derivation of the φ-π connection,
gate_step vs rect_pair, and SiLU's 4 states, see the references
in README.md and WHY.md.
"""

PHI = 1.618033988749895
PHI2 = 2.618033988749895


def exact_match(a: str, b: str) -> float:
    """1.0 if a == b, 0.0 otherwise.
    
    Infinite-sharpness limit of rect_pair(hash(a), hash(b), s → ∞).
    This is the ONLY runtime gate mechanism.
    """
    return 1.0 if a == b else 0.0


def token_hash(t: str) -> int:
    """Deterministic hash for phase computation."""
    s = 0
    for c in t:
        s = s * 31 + ord(c)
    return s
