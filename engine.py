"""
Pattern engine — v3.

Score-aware matching with phase attention (on by default).
Feedback loop via engine.feedback().
"""

from typing import Optional
import matchers as M
import transforms as T
from phase import path_phase, pos_phase, phase_distance

_SPEC = {'Value': 100, 'Class': 50, 'Any': 30, 'Seq': 20, 'Opt': 10, 'Star': 5}


def _specificity(m) -> int:
    name = type(m).__name__
    base = _SPEC.get(name, 10)
    if hasattr(m, 'matchers') and m.matchers:
        return base + max(_specificity(c) for c in m.matchers) // 10
    return base


class Pattern:
    def __init__(self, matcher: M.Matcher, transform: T.Transform,
                 name: str = '', weight: float = 1.0):
        self.matcher = matcher
        self.transform = transform
        self.name = name
        self.weight = weight

    def apply(self, toks: list[str], pos: int
              ) -> Optional[tuple[list[str], float, list[tuple[list[int], int]], int]]:
        m = self.matcher.match(toks, pos)
        if m is None or m.length == 0:
            return None
        w = toks[pos:pos + m.length]
        # Convert absolute positions to window-relative for transforms
        rel_paths = [(p, idx - pos) for p, idx in m.paths]
        ctx = {'match_paths': rel_paths}
        out = self.transform.apply(w, ctx)
        return (out, m.score * self.weight, m.paths, m.length)

    def specificity(self) -> int:
        return _specificity(self.matcher)


class PatternEngine:
    """Score-aware matching with phase attention (enabled by default)."""

    def __init__(self):
        self.patterns: list[Pattern] = []
        self._cache: dict[int, list[tuple[str, int]]] = {}

    def add(self, pat: Pattern):
        self.patterns.append(pat)

    def _boost(self, name: str, seq_pos: int) -> float:
        if not self._cache:
            return 1.0
        pv = pos_phase(seq_pos)
        boost = 1.0
        for bucket, entries in self._cache.items():
            for n, count in entries:
                if n != name:
                    continue
                d = phase_distance(pv, pos_phase(bucket))
                if d < 0.3:
                    boost += count * 0.05 * (1.0 - d)
        return min(boost, 2.0)

    def _record(self, name: str, seq_pos: int):
        b = seq_pos
        if b not in self._cache:
            self._cache[b] = []
        for i, (n, c) in enumerate(self._cache[b]):
            if n == name:
                self._cache[b][i] = (n, c + 1)
                return
        self._cache[b].append((name, 1))

    def apply(self, toks: list[str]) -> tuple[list[str], list[dict]]:
        out = list(toks)
        log = []
        i = 0
        while i < len(out):
            best = None
            bs = -1.0
            bp = -1
            for p in self.patterns:
                r = p.apply(out, i)
                if r is None:
                    continue
                ot, c, _, ml = r
                bv = c * self._boost(p.name, i)
                sp = p.specificity()
                if bv > bs or (bv == bs and sp > bp):
                    best = (ot, c, ml, p, bv)
                    bs = bv
                    bp = sp
            if best is not None and bs > 0:
                ot, c, ml, pat, bv = best
                self._record(pat.name, i)
                log.append({'pos': i, 'pat': pat.name, 'score': c,
                            'boost': round(bv / c, 3) if c > 0 else 1.0,
                            'out': ' '.join(ot)})
                out[i:i + ml] = ot
                i += len(ot)
            else:
                i += 1
        return out, log

    def feedback(self, toks: list[str], expected: list[str],
                 resolver: 'Resolver'):
        """Feedback loop: detect mismatches and learn corrections.
        
        Runs the engine, compares output to |expected| token-by-token,
        and learns the correct mapping for each mismatch via the Resolver.
        
        Returns the number of corrections made.
        """
        out, log = self.apply(toks)
        corrections = 0
        for i, (a, e) in enumerate(zip(out, expected)):
            if a != e:
                pat_path = [i]
                resolver.learn(toks[i] if i < len(toks) else '', e, pat_path)
                corrections += 1
        return corrections
