"""
Unified Resolver — v3.

Everything is path-indexed. Holographic fallback walks the class
hierarchy at the same path. No separate global entries.

Resolution strategy:
  1. Exact match at path → EXPAND
  2. Sibling at path (prefix sim tiebreak) → PRESERVE_NEG
  3. Hierarchy walk at path (broader class) → PRESERVE_POS
  4. Nothing → CONTRACT
"""

from . import tokens
from .gates import exact_match
from .phase import path_phase, phase_distance

EXPAND = '+1'
PRESERVE_POS = '+0'
PRESERVE_NEG = '-0'
CONTRACT = '-1'


def _sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    p = 0
    for x, y in zip(a, b):
        if x == y:
            p += 1
        else:
            break
    m = max(len(a), len(b))
    return (p / m) if m > 0 else 0.0


def _related(a, b):
    if a is b:
        return True
    if hasattr(a, 'is_subclass_of') and hasattr(b, 'is_subclass_of'):
        if a.is_subclass_of(b) or b.is_subclass_of(a):
            return True
        pa, pb = a.parent, b.parent
        while pa and pb:
            if pa is pb:
                return True
            pa = pa.parent if pa.parent else None
            pb = pb.parent if pb.parent else None
    return False


class Resolver:
    def __init__(self):
        # (path_key, class_name) → [(phase_vector, token, output), ...]
        self._entries: dict[tuple, list] = {}

    def learn(self, token: str, output: str, path: list[int]):
        from .phase import path_key as pk_fn
        pk = pk_fn(path)
        pv = path_phase(path)
        cls = tokens.classify(token).name
        key = (pk, cls)
        if key not in self._entries:
            self._entries[key] = []
        if (token, output) not in [(t, o) for _, t, o in self._entries[key]]:
            self._entries[key].append((pv, token, output))

    def resolve(self, token: str, path: list[int]
                ) -> tuple[str | None, float, str]:
        from .phase import path_key as pk_fn
        pk = pk_fn(path)
        pv = path_phase(path)
        cls = tokens.classify(token)

        for (epk, ecls), entries in self._entries.items():
            if epk != pk:
                continue
            for _, t, o in entries:
                if exact_match(token, t) > 0:
                    return o, 1.0, EXPAND

        candidates = []
        for (epk, ecls), entries in self._entries.items():
            if epk != pk:
                continue
            ec = getattr(tokens, ecls, None)
            if ec is None or not _related(ec, cls):
                continue
            for epv, t, o in entries:
                d = phase_distance(pv, epv)
                sim = _sim(token, t)
                score = (1.0 - d) * 0.6 + sim * 0.4
                candidates.append((score, o))

        if candidates:
            candidates.sort(key=lambda x: -x[0])
            s, o = candidates[0]
            if s > 0.5:
                return o, s, PRESERVE_NEG

        hcls = cls
        while hcls:
            for (epk, ecls), entries in self._entries.items():
                ec = getattr(tokens, ecls, None)
                if ec is None or not hcls.is_subclass_of(ec) and not ec.is_subclass_of(hcls):
                    continue
                for _, t, o in entries:
                    sim = _sim(token, t)
                    if sim > 0:
                        return o, 0.3 + sim * 0.2, PRESERVE_POS
            hcls = hcls.parent

        return None, 0.0, CONTRACT

    def save(self, filepath: str):
        import json
        data = {'mappings': []}
        for (pk, cls), entries in self._entries.items():
            for pv, t, o in entries:
                data['mappings'].append({'path': str(pv), 'token': t, 'output': o})
        with open(filepath, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load(cls, filepath: str):
        import json
        r = cls()
        with open(filepath) as f:
            data = json.load(f)
        return r
