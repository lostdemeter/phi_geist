"""
Production x86 instruction patterns — data movement.

mov REG, IMM   → REG = IMM
mov REG, REG   → REG = REG  
push REG       → push(REG)
pop REG        → REG = pop()
"""

from .. import matchers as M
from .. import transforms as T
from .. import tokens as tk
from .. import engine as E


def register(resolver, eng):
    # Generic opcode REG, IMM → REG operator IMM (via bridge)
    eng.add(E.Pattern(
        M.Seq(M.Class(tk.OPCODE), M.Class(tk.REGISTER),
              M.Opt(M.Class(tk.PUNCTUATION)), M.Class(tk.IMMEDIATE)),
        T.SeqT(T.CopyPath([1]), T.Bridge([0], resolver), T.CopyPath([3])),
        name='op_imm',
    ))

    # mov REG, IMM → REG = IMM
    eng.add(E.Pattern(
        M.Seq(M.Value('mov'), M.Class(tk.REGISTER),
              M.Opt(M.Class(tk.PUNCTUATION)), M.Class(tk.IMMEDIATE)),
        T.SeqT(T.CopyPath([1]), T.Lit('='), T.CopyPath([3])),
        name='mov_imm',
    ))

    # mov REG, REG → REG = REG
    eng.add(E.Pattern(
        M.Seq(M.Value('mov'), M.Class(tk.REGISTER),
              M.Opt(M.Class(tk.PUNCTUATION)), M.Class(tk.REGISTER)),
        T.SeqT(T.CopyPath([1]), T.Lit('='), T.CopyPath([3])),
        name='mov_reg',
    ))

    # push REG → push(REG)
    eng.add(E.Pattern(
        M.Seq(M.Value('push'), M.Class(tk.REGISTER)),
        T.SeqT(T.Lit('push'), T.Lit('('), T.CopyPath([1]), T.Lit(')')),
        name='push',
    ))

    # pop REG → REG = pop()
    eng.add(E.Pattern(
        M.Seq(M.Value('pop'), M.Class(tk.REGISTER)),
        T.SeqT(T.CopyPath([1]), T.Lit('='), T.Lit('pop'), T.Lit('()')),
        name='pop',
    ))
