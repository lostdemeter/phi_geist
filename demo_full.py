#!/usr/bin/env python3
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
"""
Full decompilation pipeline demo — v3.

Assembly → Patterns → CFG → Structured C → Compile → Verify
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from patterns.builder import build
from control import decompile as cfg_decompile
from verify import wrap_c, verify, report
from resonant import is_jump_table


def tok(s):
    return s.replace(';', ' ;').replace(',', ' ,').split()


resolver, eng = build()

PROGRAMS = [
    ("Simple if-then",
     "cmp eax, 0 ; je L1 ; mov ebx, 1 ; L1 :"),
    ("If-then-else",
     "cmp ebx, 5 ; jl L3 ; mov eax, 2 ; jmp L4 ; L3 : mov eax, 1 ; L4 :"),
    ("While loop",
     "mov ecx, 0 ; L1 : add ecx, 1 ; cmp ecx, 10 ; jl L1"),
    ("Nested if-in-loop",
     "mov eax, 0 ; L1 : cmp eax, 5 ; jl L3 ; add eax, 2 ; "
     "jmp L4 ; L3 : add eax, 1 ; L4 : cmp eax, 10 ; jl L1"),
]

print("=" * 70)
print("  FULL DECOMPILATION PIPELINE")
print("=" * 70)

for name, asm in PROGRAMS:
    print(f"\n  {'─' * 60}")
    print(f"  {name}")
    print(f"  {'─' * 60}")
    print(f"  ASM: {asm}")

    t = tok(asm)
    decompiled, log = eng.apply(t)
    processed = decompiled

    result = cfg_decompile(processed)
    print(f"  C:   {result}")

    wrapped = wrap_c(result)
    v_result = verify(result)
    print(f"  Compiles: {'✓' if v_result['compiles'] else '✗'}")

print(f"\n  {'═' * 60}")
print(f"  JUMP TABLE DETECTION")
print(f"  {'═' * 60}")

table = [0x401100, 0x401150, 0x401200, 0x401250, 0x401300]
random = [0x401000, 0x7ffff000, 0xdeadbeef, 0x12345678]

is_jt, reg = is_jump_table(table, (0x401000, 0x402000))
print(f"  Jump table:    regularity={reg:.3f}  {'✓' if is_jt else '✗'}")

is_jt, reg = is_jump_table(random, (0x400000, 0x402000))
print(f"  Random data:   regularity={reg:.3f}  {'✗' if not is_jt else '✓'}")

print(f"\n  FEEDBACK LOOP:")
unknown = "shl eax, 1"
t = tok(unknown)
out, _ = eng.apply(t)
print(f"  Before: {unknown:15s} → {' '.join(out)}")
c = eng.feedback(tok(unknown), ['<<=', 'eax'], resolver)
out, _ = eng.apply(t)
print(f"  After:  {unknown:15s} → {' '.join(out)}  ({c} corrections)")
