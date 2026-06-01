"""
Transforms — v3.

CopyPath uses log-space path encoding (RoPE-style), making it
invariant to operand reordering. Bridge integrates with the
Resolver via path-indexed mappings.
"""

from typing import Optional
from phase import path_phase, phase_distance


class Transform:
    def apply(self, window: list[str],
              context: Optional[dict] = None) -> list[str]:
        raise NotImplementedError


class Lit(Transform):
    def __init__(self, value: str):
        self.value = value
    def apply(self, window, context=None):
        return [self.value]


class CopyPath(Transform):
    """Copy token at pattern path |path|.
    
    Resolves by exact path match first, then phase proximity.
    Log-space encoding means swapped tokens preserve their
    phase relationship (negated under conjugation).
    """
    def __init__(self, path: list[int]):
        self.path = list(path)

    def apply(self, window, context=None):
        if context and 'match_paths' in context:
            pv = path_phase(self.path)
            best_idx = None
            best_dist = float('inf')
            for p, idx in context['match_paths']:
                if p == self.path or (len(p) >= len(self.path) and
                                      p[:len(self.path)] == self.path):
                    if idx < len(window):
                        best_idx = idx
                        break
                d = phase_distance(pv, path_phase(p))
                if d < best_dist:
                    best_dist = d
                    best_idx = idx if idx < len(window) else best_idx
            if best_idx is not None and best_idx < len(window):
                return [window[best_idx]]
        return [window[0]] if window else ['']


class Drop(Transform):
    def apply(self, window, context=None):
        return []


class Cond(Transform):
    """Conditional: token at |path| determines output.
    
    case_map: {token_value: output_string, ...}
    """
    def __init__(self, path: list[int], case_map: dict[str, str],
                 default: str = ''):
        self.path = list(path)
        self.cases = case_map
        self.default = default

    def apply(self, window, context=None):
        val = window[0] if window else ''
        if context and 'match_paths' in context:
            for p, idx in context['match_paths']:
                if p == self.path or (len(p) >= len(self.path) and
                                      p[:len(self.path)] == self.path):
                    if idx < len(window):
                        val = window[idx]
                        break
        return [self.cases.get(val, self.default)]


class SeqT(Transform):
    def __init__(self, *transforms):
        self.transforms = transforms

    def apply(self, window, context=None):
        r = []
        for t in self.transforms:
            r.extend(t.apply(window, context))
        return r


class Bridge(Transform):
    """Resolve unknown at |path| via Resolver.
    
    Uses path-indexed mappings (holographic + phase proximity).
    """
    def __init__(self, path: list[int], resolver: 'Resolver'):
        self.path = list(path)
        self.resolver = resolver

    def apply(self, window, context=None):
        val = window[0] if window else ''
        if context and 'match_paths' in context:
            for p, idx in context['match_paths']:
                if p == self.path or (len(p) >= len(self.path) and
                                      p[:len(self.path)] == self.path):
                    if idx < len(window):
                        val = window[idx]
                        break
        mapping, conf, _ = self.resolver.resolve(val, self.path)
        return [mapping if mapping is not None and conf > 0.1 else val]
