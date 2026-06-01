"""
Production x86 instruction patterns — arithmetic.

add REG, IMM   → REG += IMM
add REG, REG   → REG += REG
sub REG, IMM   → REG -= IMM
sub REG, REG   → REG -= REG
inc REG        → REG++
dec REG        → REG--
"""

from .. import matchers as M
from .. import transforms as T
from .. import tokens as tk
from .. import engine as E


def register(resolver, eng):
    for op in ('add', 'sub'):
        eng.add(E.Pattern(
            M.Seq(M.Value(op), M.Class(tk.REGISTER),
                  M.Opt(M.Class(tk.PUNCTUATION)), M.Class(tk.IMMEDIATE)),
            T.SeqT(T.CopyPath([1]),
                   T.Cond([0], {'add': '+=', 'sub': '-='}, '?='),
                   T.CopyPath([3])),
            name=f'{op}_imm',
        ))
        eng.add(E.Pattern(
            M.Seq(M.Value(op), M.Class(tk.REGISTER),
                  M.Opt(M.Class(tk.PUNCTUATION)), M.Class(tk.REGISTER)),
            T.SeqT(T.CopyPath([1]),
                   T.Cond([0], {'add': '+=', 'sub': '-='}, '?='),
                   T.CopyPath([3])),
            name=f'{op}_reg',
        ))

    for op in ('inc', 'dec'):
        eng.add(E.Pattern(
            M.Seq(M.Value(op), M.Class(tk.REGISTER)),
            T.SeqT(T.CopyPath([1]), T.Lit('++' if op == 'inc' else '--')),
            name=op,
        ))
