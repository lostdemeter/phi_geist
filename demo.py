#!/usr/bin/env python3
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
"""phi_lib3 end-to-end demo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tokens, matchers, transforms, resolver, engine


def tok(s):
    return s.replace(';', ' ;').replace(',', ' ,').split()

def untok(toks):
    s = ' '.join(toks)
    return s.replace(' ;', ';').replace(' ,', ',')


r = resolver.Resolver()
r.learn('mov', '=', [0])
r.learn('add', '+=', [0])

eng = engine.PatternEngine()
eng.add(engine.Pattern(
    matchers.Seq(matchers.Any(matchers.Value('mov'), matchers.Value('add'),
                               matchers.Value('sub')),
                 matchers.Class(tokens.REGISTER),
                 matchers.Opt(matchers.Class(tokens.PUNCTUATION)),
                 matchers.Class(tokens.IMMEDIATE)),
    transforms.SeqT(transforms.Bridge([0], r), transforms.CopyPath([1])),
    name='instr',
))
eng.add(engine.Pattern(
    matchers.Seq(matchers.Class(tokens.CMP), matchers.Class(tokens.REGISTER),
                 matchers.Class(tokens.PUNCTUATION),
                 matchers.Class(tokens.IMMEDIATE),
                 matchers.Class(tokens.PUNCTUATION),
                 matchers.Class(tokens.JCC), matchers.Class(tokens.LABEL)),
    transforms.SeqT(
        transforms.Lit('if'), transforms.Lit('('),
        transforms.CopyPath([1]),
        transforms.Cond([5], {'je': '==', 'jne': '!=', 'jl': '<', 'jg': '>'}, '?'),
        transforms.CopyPath([3]),
        transforms.Lit(')'), transforms.Lit('goto'), transforms.CopyPath([6]),
    ),
    name='jcc',
))

tests = [
    "mov eax, 5",
    "mov eax 5",
    "add ebx, 3",
    "cmp eax, 0 ; je L1",
    "cmp ecx, 10 ; jl L4",
    "cmp ebx, 1 ; jne L2",
]

print("=" * 60)
print("  phi_lib3 — final library")
print("=" * 60)
for asm in tests:
    t = tok(asm)
    out, log = eng.apply(t)
    print(f"\n  IN:  {asm}")
    print(f"  OUT: {untok(out)}")
    for entry in log:
        print(f"       [{entry['pat']}] score={entry['score']:.3f} "
              f"boost={entry['boost']}")

print(f"\n  Feedback test:")
print(f"    sub unknown → '=' (wrong, bridges to mov)")
corrections = eng.feedback(
    tok("sub ebx, 3"),
    ['-=', 'ebx', '3'],
    r,
)
print(f"    Corrections learned: {corrections}")
out, _ = eng.apply(tok("sub ebx, 3"))
print(f"    After feedback: {untok(out)}")
