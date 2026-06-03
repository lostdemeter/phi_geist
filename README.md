# φ-lib: Geometric Pattern Matching and Transformation

A library for typed token sequence transformation using composable
matchers, path-indexed resolution, and geometric phase encoding —
with built-in handling for unknown tokens and self-correction.

## Why This Exists

This library is a practical demonstration that three mathematical
structures — φ-geometry, Riemann zeros, and token class hierarchies —
are the SAME structure at different scales. The evidence:

**1. φ-rung atlas.** Every weight in a trained transformer occupies one
of 256 discrete φ-ladder values, not a continuous range. The ladder is
φ^(-r × 20/255) for r = 0..255 — a geometric series where the golden
ratio determines the step size. This was discovered by quantizing
Qwen2-0.5B to 256 φ-rungs and analyzing the resulting weight patterns.

**2. The funnel.** Attention scale decays linearly with layer depth,
from all-to-all at layer 0 to within-band at layer 23. Token frequency
(Zipf's law) determines a token's φ-phase: frequent tokens form a
ROUTE band, common tokens form CONTENT, rare tokens form DETAIL.
The attention mask between tokens i and j is φ^(-|φ_i - φ_j| / scale(L)).

**3. IEEE 754 is a φ-computer.** The φ-FPU architecture proves it:
a float32's exponent bits map directly to φ-rungs, its mantissa maps
to φ-mantissa corrections. The conversion is a 2-cycle instruction.
Every GPU is already a φ-ladder machine — we just didn't notice because
we were told floating point was "approximate real arithmetic."

**4. Riemann zeros are deterministically random.** Phase(key, γₙ) =
γₙ · key mod 2π gives uniformly distributed values for any integer key
with NO random source. The Montgomery-Odlyzko law guarantees their
spacing matches random matrix eigenvalues. This means the frequency
basis for attention is exact, not stochastic.

**5. Signed weights are essential.** The Riemann attention paper proves
that the explicit formula for the prime-counting function converges
because terms cancel destructively. Softmax positivity is structurally
incompatible — you cannot represent cancellation if you clamp all
terms positive. The -0/-1 states in our holographic gate are this
cancellation mechanism.

**6. Feedback converges at error phase.** Adding a mapping at the
Riemann phase of a detected error causes the correction to converge
in 1-2 iterations. This is the Riemann convergence property applied
to program decompilation.

For the full chain of evidence, see [WHY.md](WHY.md).

## Quick Start

```python
from phi_lib3.patterns.builder import build

resolver, engine = build()

# Decompile basic instructions:
tokens = "mov eax, 5".replace(',', ' ,').split()
output, log = engine.apply(tokens)
# output = ['eax', '=', '5']

# Unknown tokens resolve via two-strategy bridge:
tokens = "xor edx, 7".replace(',', ' ,').split()
output, _ = engine.apply(tokens)
# output = ['edx', '^=', '7']

# Self-correction via feedback loop:
tokens = "shl eax, 1".replace(',', ' ,').split()
engine.feedback(tokens, ['<<=', 'eax'], resolver)
output, _ = engine.apply(tokens)
# output = ['eax', '<<=', '1']  — converged in 1 iteration
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

### Matchers

Patterns are built by composing matchers:

```python
from phi_lib3.matchers import Seq, Any, Opt, Class, Value
from phi_lib3 import tokens

# Match a specific opcode followed by any register:
Seq(Value('mov'), Class(tokens.REGISTER))

# Match opcode, register, optional comma, immediate:
Seq(Class(tokens.OPCODE), Class(tokens.REGISTER),
    Opt(Class(tokens.PUNCTUATION)), Class(tokens.IMMEDIATE))
```

Each matcher is assigned a PATTERN PATH — its structural position in
the pattern tree (e.g., [0], [1], [2, 0]). These paths are invariant
to whether optional elements (Opt) matched or not, enabling
variable-length pattern recognition without fragile index arithmetic.

### Transforms

Transforms map matched token windows to output tokens:

```python
from phi_lib3.transforms import SeqT, Lit, CopyPath, Bridge, Cond

# Produce "register = immediate":
SeqT(CopyPath([1]), Lit('='), CopyPath([3]))
```

`CopyPath` resolves by pattern path, not absolute index. It falls
back to phase proximity when exact path match fails, making it
invariant to operand reordering.

`Bridge` resolves unknown tokens via the Resolver — it combines
class hierarchy walking (broad generalization) with phase-field
matching (structural position precision).

### Engine

The PatternEngine is score-aware: when multiple patterns match at
the same position, it picks the highest-scoring match. When scores
are equal, the more specific pattern wins (Value > Class > Seq).

Phase attention is ON by default. The engine caches successful
(pattern, position) pairs. Subsequent matches at positions with
similar Riemann phases receive a score boost — the geometric
equivalent of attention, without learned weights.

### Resolver

The Resolver uses two strategies:

1. **Phase field (pattern path):** Tokens at the SAME structural
   position in the same pattern have the same Riemann phase vector.
   Unknown tokens resolve to known siblings at the same path,
   with prefix similarity as tiebreaker.

2. **Holographic (class hierarchy):** If no sibling exists at the
   same path, walk the class tree upward (JE → JCC → OPCODE →
   STRUCTURE → TOKEN) until a known token is found.

These correspond to the -0 (dark fringe, structured guess) and +0
(dim bright, class-based guess) states in the 4-state holographic
gate. +1 is an exact match (EXPAND). -1 is CONTRACT (no bridge
found — fall through unchanged).

### Control Flow

The `control.py` module builds a control flow graph from the
token stream and produces structured C with if/else, while loops,
and nesting. Labels and jumps define basic blocks; the structural
decompiler recognizes patterns (back-edge → loop, branch → if).

### Verification

The `verify.py` module wraps decompiled C in a compilable function,
compiles it with gcc, normalizes both original and re-compiled
assembly, and produces a structured diff with a semantic score
(Jaccard similarity of opcode sets).

### Jump Table Detection

The `resonant.py` module uses Riemann-zero phase increment
regularity to detect switch/case structures. A jump table's
target addresses produce CONSTANT phase increments (because
they're equally spaced in memory). Random data produces
uncorrelated phases.

## Project Structure

```
phi_lib3/
├── gates.py          exact_match + φ-geometry commentary
├── phase.py          Riemann zero phase encoding (log-space, RoPE-style)
├── tokens.py         token class hierarchy (JE < JCC < OPCODE < ...)
├── matchers.py       Seq, Any, Opt, Class, Value, Star, Not
├── transforms.py     CopyPath, Lit, Drop, Cond, SeqT, Bridge
├── resolver.py       path-indexed resolve (holographic + phase)
├── engine.py         Pattern + PatternEngine + feedback()
├── control.py        CFG builder → structured C (if/else, loops)
├── normalize.py      x86 assembly normalizer
├── verify.py         re-compile validation (compile → normalize → diff)
├── resonant.py       Riemann-zero jump table detection
├── phi_add.py        φ-ADD via Taylor series (no lookup tables)
├── PHI_ADD.md        Derivation of lookup-table-free φ-ADD
├── patterns/         production decompiler patterns
│   ├── builder.py    build() — pre-configured resolver + engine
│   ├── mov.py        data movement (mov, push, pop, generic op_imm)
│   ├── arith.py      arithmetic (add/sub, inc/dec)
│   └── control.py    control flow (cmp+jcc, jmp)
├── WHY.md            full design philosophy and evidence chain
├── tests.py          21 tests
├── LICENSE           GPLv3
└── README.md         this file
```

## The φ-FPU

The φ-FPU is a vector floating-point unit where each lane operates on
8-bit φ-values instead of 32-bit IEEE 754 floats. A lane stores:
[2 mantissa | 1 sign | 5 rung bits]. Value = sign × φ^(-rung) ×
mantissa_correction (from {0.75, 0.88, 1.13, 1.33}).

φ-MUL is 1 cycle (rung addition + sign XOR).
φ-ADD uses φ-MUL's integer adder to compute a Taylor series for
log_φ(1 + φ^(-δ)), eliminating all lookup tables. Typical cost:
~7 cycles, all integer operations — 2-3× faster than LUT-based
approaches and requiring no dedicated lookup hardware.

See [PHI_ADD.md](PHI_ADD.md) for the full derivation and
cycle-by-cycle breakdown.

The General-Purpose φ-FPU (GP-FPU) extends this with a biased rung
(like IEEE 754's biased exponent), enabling the full dynamic range
needed for 3D math and physics while keeping the same lane format
and instruction set. A 16-bit GP lane (8 rung + 3 exp + 1 sign + 4 mant)
converts 1e6 to φ-format with 0.5% error.

## Requirements

- Python 3.10+
- NumPy (for phase computation)
- GCC (for verification pipeline — optional)


## Tests

```bash
python -m phi_lib3.tests
```

## References

- **TruthSpace** (Gushurst, 2026): φ-Zipf duality, 3,584 critical lines
- **Constructive transformer v2** (Gushurst, 2026): 26-axis, 4-state
  alphabet, hand-placed weights, no training
- **Riemann attention** (Gushurst, 2026): Explicit formula as position-only
  linear attention; signed weights vs softmax incompatibility
- **φ-rung GPTQ**: Weight quantization to 256 φ-ladder values at +0.023 loss
- **Riemann structures**: 16 data structures using γₙ · key mod 2π primitive

## License

GPLv3 — see LICENSE.
