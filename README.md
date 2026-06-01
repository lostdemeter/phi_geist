# φ-lib: Geometric Pattern Matching and Transformation

A library for typed token sequence transformation using composable
matchers, path-indexed resolution, and geometric phase encoding.

## What It Does

φ-lib transforms structured token sequences — assembly instructions,
log formats, DSLs — into different representations using composable
pattern matching, with built-in handling for unknown tokens and
self-correction.

## Quick Start

```python
from phi_lib3.patterns.builder import build

resolver, engine = build()

tokens = "mov eax, 5".replace(',', ' ,').split()
output, log = engine.apply(tokens)
# output = ['eax', '=', '5']

# Unknown tokens resolve via bridge:
tokens = "xor edx, 7".replace(',', ' ,').split()
output, _ = engine.apply(tokens)
# output = ['edx', '^=', '7']

# Feedback loop for self-correction:
engine.feedback(tokens, ['<<=', 'eax'], resolver)
```

## Architecture

```
tokens → matchers (Seq, Any, Opt, Class, Value)
       ↓
       transforms (CopyPath, Bridge, Cond, SeqT)
       ↓
       engine (score-aware, phase attention, feedback)
       ↓
       resolver (path-indexed, holographic + phase bridge)
       ↓
       control flow graph → structured C
       ↓
       verify (compile → normalize → diff)
```

## Core Concepts

**Pattern paths:** Every matcher in a sequence is assigned a structural
position in the pattern tree (e.g., `[0]`, `[1]`, `[2, 0]`). These paths
are invariant to optional matches, enabling variable-length pattern
recognition without fragile index arithmetic.

**Two-strategy resolution:** Unknown tokens are resolved by combining
class hierarchy walking (find a known sibling by class) with phase-field
matching (find a known token at the same structural position). The
former provides breadth; the latter provides precision.

**Phase attention:** The engine maintains a cache of successful matches
keyed by the Riemann phase of the match position. Subsequent matches at
similar phases receive a score boost. This is the geometric equivalent
of attention — patterns that worked in similar contexts get preferred
in similar future contexts.

**Feedback convergence:** The feedback loop detects mismatches between
expected and actual output, learns the correct mapping at the error's
pattern path, and converges in 1-2 iterations.

## Project Structure

```
phi_lib3/
├── gates.py          exact_match primitive
├── phase.py          Riemann zero phase encoding
├── tokens.py         token class hierarchy
├── matchers.py       Seq, Any, Opt, Class, Value, Star, Not
├── transforms.py     CopyPath, Lit, Drop, Cond, SeqT, Bridge
├── resolver.py       path-indexed resolve (holographic + phase)
├── engine.py         Pattern + PatternEngine + feedback()
├── control.py        CFG builder → structured C
├── normalize.py      x86 assembly normalizer
├── verify.py         re-compile verification pipeline
├── resonant.py       Riemann-zero jump table detection
├── patterns/         production decompiler patterns
│   ├── builder.py    build() — pre-configured resolver + engine
│   ├── mov.py        data movement patterns
│   ├── arith.py      arithmetic patterns
│   └── control.py    control flow patterns
├── WHY.md            design philosophy
└── tests.py          19 tests
```

## Requirements

- Python 3.10+
- NumPy (for phase computation)
- GCC (for verification pipeline — optional)

## Tests

```bash
python -m phi_lib3.tests
```

## License

GPLv3 — see LICENSE.
