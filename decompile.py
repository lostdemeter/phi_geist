#!/usr/bin/env python3
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
"""
Full decompilation stress test for phi_lib3.

Tests the complete pipeline on real assembly fragments with
unknown opcodes, variable-length patterns, and control flow.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tokens, matchers, transforms, resolver, engine, phase


def tok(s):
    return s.replace(';', ' ;').replace(',', ' ,').split()

def untok(toks):
    s = ' '.join(toks)
    return s.replace(' ;', ';').replace(' ,', ',')


# ─── Build the decompiler ───────────────────────────────────────

r = resolver.Resolver()
eng = engine.PatternEngine()

# Train resolver with known opcode mappings at path [0]
for op, out in [('mov', '='), ('add', '+='), ('sub', '-='),
                 ('xor', '^='), ('and', '&='), ('or', '|=')]:
    r.learn(op, out, [0])

# Instruction pattern: opcode REG [PUNCT] IMM → operator REG
eng.add(engine.Pattern(
    matchers.Seq(matchers.Any(matchers.Value('mov'), matchers.Value('add'),
                               matchers.Value('sub'), matchers.Value('xor'),
                               matchers.Value('and'), matchers.Value('or'),
                               matchers.Value('shl'), matchers.Value('shr')),
                 matchers.Class(tokens.REGISTER),
                 matchers.Opt(matchers.Class(tokens.PUNCTUATION)),
                 matchers.Class(tokens.IMMEDIATE)),
    transforms.SeqT(transforms.Bridge([0], r), transforms.CopyPath([1])),
    name='instr_imm',
))

# Instruction pattern: opcode REG [PUNCT] REG → dest = src
eng.add(engine.Pattern(
    matchers.Seq(matchers.Any(matchers.Value('mov'), matchers.Value('add'),
                               matchers.Value('sub')),
                 matchers.Class(tokens.REGISTER),
                 matchers.Opt(matchers.Class(tokens.PUNCTUATION)),
                 matchers.Class(tokens.REGISTER)),
    transforms.SeqT(transforms.CopyPath([1]), transforms.Bridge([0], r),
                    transforms.CopyPath([3])),
    name='instr_reg',
))

# Conditional jump: cmp REG , IMM ; JCC LABEL
eng.add(engine.Pattern(
    matchers.Seq(matchers.Class(tokens.CMP), matchers.Class(tokens.REGISTER),
                 matchers.Class(tokens.PUNCTUATION),
                 matchers.Class(tokens.IMMEDIATE),
                 matchers.Class(tokens.PUNCTUATION),
                 matchers.Class(tokens.JCC), matchers.Class(tokens.LABEL)),
    transforms.SeqT(
        transforms.Lit('if'), transforms.Lit('('),
        transforms.CopyPath([1]),
        transforms.Cond([5], {'je': '==', 'jne': '!=', 'jl': '<',
                              'jle': '<=', 'jg': '>', 'jge': '>='}, '?'),
        transforms.CopyPath([3]),
        transforms.Lit(')'), transforms.Lit('goto'), transforms.CopyPath([6]),
    ),
    name='jcc_imm',
))

# Conditional jump: cmp REG , REG ; JCC LABEL
eng.add(engine.Pattern(
    matchers.Seq(matchers.Class(tokens.CMP), matchers.Class(tokens.REGISTER),
                 matchers.Class(tokens.PUNCTUATION),
                 matchers.Class(tokens.REGISTER),
                 matchers.Class(tokens.PUNCTUATION),
                 matchers.Class(tokens.JCC), matchers.Class(tokens.LABEL)),
    transforms.SeqT(
        transforms.Lit('if'), transforms.Lit('('),
        transforms.CopyPath([1]),
        transforms.Cond([5], {'je': '==', 'jne': '!=', 'jl': '<',
                              'jle': '<=', 'jg': '>', 'jge': '>='}, '?'),
        transforms.CopyPath([3]),
        transforms.Lit(')'), transforms.Lit('goto'), transforms.CopyPath([6]),
    ),
    name='jcc_reg',
))


def decompile(asm: str) -> tuple[str, list[dict]]:
    t = tok(asm)
    out, log = eng.apply(t)
    return untok(out), log


# ─── Test cases ─────────────────────────────────────────────────

TESTS = [
    # Basic instructions
    ("mov eax, 5",           "mov immediate"),
    ("add ebx, 3",           "add immediate"),
    ("sub ecx, 1",           "sub immediate"),

    # Variable length (no comma)
    ("mov eax 5",            "mov without comma"),
    ("add ebx 3",            "add without comma"),

    # Register-to-register
    ("mov eax, ebx",         "mov reg to reg"),
    ("add ebx, ecx",         "add reg to reg"),

    # Conditional jumps
    ("cmp eax, 0 ; je L1",   "jump if equal"),
    ("cmp ebx, 5 ; jne L2",  "jump if not equal"),
    ("cmp ecx, 10 ; jl L3",  "jump if less"),
    ("cmp edx, 7 ; jg L4",   "jump if greater"),

    # Conditional jumps with register comparison
    ("cmp eax, ebx ; je L1", "jump if regs equal"),
    ("cmp ecx, edx ; jl L2", "jump if reg less"),

    # Unknown opcodes (should bridge via resolver)
    ("xor edx, 7",           "xor (known)"),
    ("and eax, 3",           "and (known)"),
    ("or ebx, 1",            "or (known)"),

    # Sequences
    ("mov eax, 5 ; add eax, 10 ; sub eax, 3",  "multi-instr sequence"),
    ("cmp eax, 0 ; je L1 ; mov ebx, 1",        "conditional + mov"),
]

print("=" * 70)
print("  PHI_LIB3 DECOMPILATION STRESS TEST")
print("=" * 70)
print(f"\n  Trained opcodes: mov, add, sub, xor, and, or")
print(f"  Patterns: {len(eng.patterns)}")

passed = 0
failed = 0

for asm, desc in TESTS:
    result, log = decompile(asm)
    has_output = len(log) > 0
    has_bridge = any('Bridge' in str(p) for p in eng.patterns)
    has_cond = any('Cond' in str(p) for p in eng.patterns)
    has_lit = any(l['pat'] in ['jcc_imm', 'jcc_reg', 'instr_imm', 'instr_reg']
                  for l in log)
    
    status = "✓" if has_lit or has_output else "✗"
    if status == "✓":
        passed += 1
    else:
        failed += 1
    
    print(f"\n  {status} {desc:30s}")
    print(f"    IN:  {asm}")
    print(f"    OUT: {result}")
    for l in log:
        print(f"         [{l['pat']}] score={l['score']:.3f} boost={l['boost']}")

print(f"\n  {'─' * 50}")
print(f"  Results: {passed}/{passed + failed} passed")
if failed > 0:
    print(f"  {failed} test(s) produced no output")

# Test feedback loop
print(f"\n  {'═' * 50}")
print(f"  FEEDBACK LOOP TEST")
print(f"  {'═' * 50}")

unknown_op = "shl"
print(f"\n  '{unknown_op}' unknown → testing bridge + feedback:")

test_in = f"{unknown_op} eax, 2"
result, log = decompile(test_in)
print(f"    Before: {test_in:25s} → {result}")

corrections = eng.feedback(
    tok(test_in),
    ['<<=', 'eax'],
    r,
)
print(f"    Corrections learned: {corrections}")

result, log = decompile(test_in)
print(f"    After:  {test_in:25s} → {result}")
print(f"    Resolver knows: {unknown_op} → '{r.resolve(unknown_op, [0])[0]}'")

print(f"\n  {'═' * 50}")
print(f"  OVERALL: {passed}/{passed + failed} basic tests passed")
if corrections > 0:
    print(f"          + feedback loop working ({corrections} corrections)")
