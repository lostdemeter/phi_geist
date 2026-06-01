"""
Pattern matchers — v3.

Class, Value, Seq, Any, Opt, Star, Not.
Every matcher tracks its pattern path (structural position in the tree).
Paths are invariant to variable-length matches (Opt/Star).
"""

from typing import Optional
from . import tokens as tk
from .gates import exact_match


class Match:
    def __init__(self, length: int, score: float,
                 paths: Optional[list[tuple[list[int], int]]] = None):
        self.length = length
        self.score = score
        self.paths = paths or []


class Matcher:
    def match(self, toks: list[str], pos: int) -> Optional[Match]:
        raise NotImplementedError


class Class(Matcher):
    def __init__(self, cls):
        self.cls = cls
        self.path: list[int] = []

    def set_path(self, path: list[int]):
        self.path = list(path)

    def match(self, toks, pos):
        if pos < len(toks) and tk.matches(toks[pos], self.cls):
            return Match(1, 1.0, paths=[(list(self.path), pos)])
        return None


class Value(Matcher):
    def __init__(self, value: str):
        self.value = value
        self.path: list[int] = []

    def set_path(self, path: list[int]):
        self.path = list(path)

    def match(self, toks, pos):
        if pos < len(toks) and exact_match(toks[pos], self.value) > 0:
            return Match(1, 1.0, paths=[(list(self.path), pos)])
        return None


class Seq(Matcher):
    def __init__(self, *matchers):
        self.matchers = matchers
        self._assign_paths()

    def _assign_paths(self, prefix: list[int] | None = None):
        for i, m in enumerate(self.matchers):
            p = (prefix or []) + [i]
            if hasattr(m, 'set_path'):
                m.set_path(p)
            if hasattr(m, '_assign_paths'):
                m._assign_paths(p)

    def match(self, toks, pos):
        n = 0
        s = 1.0
        ap = []
        for m in self.matchers:
            r = m.match(toks, pos + n)
            if r is None:
                return None
            cs = max(r.score, 0.1) if r.length == 0 else r.score
            n += r.length
            s *= cs
            ap.extend(r.paths)
        return Match(n, s, paths=ap)


class Any(Matcher):
    def __init__(self, *matchers):
        self.matchers = matchers

    def set_path(self, path: list[int]):
        for m in self.matchers:
            if hasattr(m, 'set_path'):
                m.set_path(path + [0])
            if hasattr(m, '_assign_paths'):
                m._assign_paths(path + [0])

    def match(self, toks, pos):
        best = None
        for m in self.matchers:
            r = m.match(toks, pos)
            if r is not None and (best is None or r.score > best.score):
                best = r
        return best


class Opt(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher

    def set_path(self, path: list[int]):
        if hasattr(self.matcher, 'set_path'):
            self.matcher.set_path(path + [0])

    def _assign_paths(self, prefix: list[int] | None = None):
        if hasattr(self.matcher, '_assign_paths'):
            self.matcher._assign_paths((prefix or []) + [0])
        elif hasattr(self.matcher, 'set_path'):
            self.matcher.set_path((prefix or []) + [0])

    def match(self, toks, pos):
        r = self.matcher.match(toks, pos)
        if r is not None:
            return Match(r.length, r.score, paths=r.paths)
        return Match(0, 0.0)


class Star(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher

    def set_path(self, path: list[int]):
        if hasattr(self.matcher, 'set_path'):
            self.matcher.set_path(path + [0])

    def _assign_paths(self, prefix: list[int] | None = None):
        if hasattr(self.matcher, '_assign_paths'):
            self.matcher._assign_paths((prefix or []) + [0])
        elif hasattr(self.matcher, 'set_path'):
            self.matcher.set_path((prefix or []) + [0])

    def match(self, toks, pos):
        n = 0
        s = 1.0
        ap = []
        while True:
            r = self.matcher.match(toks, pos + n)
            if r is None:
                break
            cs = max(r.score, 0.1) if r.length == 0 else r.score
            n += r.length
            s *= cs
            ap.extend(r.paths)
            if r.length == 0:
                break
        return Match(n, s, paths=ap)


class Not(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher

    def match(self, toks, pos):
        r = self.matcher.match(toks, pos)
        if r is None:
            return Match(0, 0.5)
        return None
