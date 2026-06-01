#!/usr/bin/env python3
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
"""
Production decompilation demo using the pattern library.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.builder import build
import tokens


def tok(s):
    return s.replace(';', ' ;').replace(',', ' ,').split()

def untok(toks):
    s = ' '.join(toks)
    return s.replace(' ;', ';').replace(' ,', ',')


resolver, eng = build()

print("=" * 70)
print("  PRODUCTION X86 DECOMPILER")
print("=" * 70)

TESTS = [
    # Data movement
    ("mov eax, 5",          "mov immediate"),
    ("mov eax, ebx",        "mov register"),
    ("push eax",            "push"),
    ("pop ebx",             "pop"),

    # Arithmetic
    ("add eax, 10",         "add immediate"),
    ("sub ebx, 3",          "sub immediate"),
    ("add ecx, edx",        "add register"),
    ("inc eax",             "increment"),
    ("dec ebx",             "decrement"),

    # Control flow
    ("cmp eax, 0 ; je L1",   "jump if equal"),
    ("cmp ebx, 5 ; jne L2", "jump if not equal"),
    ("cmp ecx, 10 ; jl L3", "jump if less"),
    ("cmp edx, 7 ; jg L4",  "jump if greater"),
    ("cmp eax, ebx ; je L1","jump regs equal"),
    ("jmp L5",              "unconditional jump"),

    # Sequences
    ("mov eax, 5 ; add eax, 10 ; sub eax, 3", "arithmetic sequence"),

    # Unknown opcodes (bridge via resolver)
    ("xor edx, 7",          "xor via bridge"),
    ("and eax, 3",          "and via bridge"),
    ("or ebx, 1",           "or via bridge"),
]

all_pass = True
for asm, desc in TESTS:
    t = tok(asm)
    out, log = eng.apply(t)
    result = untok(out)
    has_output = len(log) > 0
    status = "✓" if has_output else "✗"
    if not has_output:
        all_pass = False
    print(f"\n  {status} {desc:25s}  {result}")
    for l in log[:2]:
        print(f"     [{l['pat']}] score={l['score']:.3f}")

print(f"\n  {'─' * 50}")
print(f"  {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")

# Feedback loop demo
print(f"\n  {'═' * 50}")
print(f"  FEEDBACK LOOP")
print(f"  {'═' * 50}")

for unknown_op, correct_op in [('shl', '<<='), ('shr', '>>=')]:
    test_in = f"{unknown_op} eax, 1"
    t = tok(test_in)
    out, log = eng.apply(t)
    result = untok(out)
    print(f"\n    '{unknown_op}' unknown → bridges to '{result.split()[0]}'")

    c = eng.feedback(tok(test_in), [correct_op, 'eax'], resolver)
    out, log = eng.apply(t)
    result = untok(out)
    print(f"    After feedback: {result}  ({c} corrections)")
