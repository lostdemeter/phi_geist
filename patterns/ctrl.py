import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
"""
Production x86 instruction patterns — control flow.

cmp REG, IMM ; JCC LABEL → if (REG op IMM) goto LABEL
cmp REG, REG ; JCC LABEL → if (REG op REG) goto LABEL
jmp LABEL                → goto LABEL
"""

import matchers as M
import transforms as T
import tokens as tk
import engine as E


JCC_OPS = {'je': '==', 'jne': '!=', 'jl': '<', 'jle': '<=',
           'jg': '>', 'jge': '>=', 'ja': '>', 'jb': '<',
           'jae': '>=', 'jbe': '<='}


def register(resolver, eng):
    # cmp REG , IMM ; JCC LABEL
    eng.add(E.Pattern(
        M.Seq(M.Value('cmp'), M.Class(tk.REGISTER), M.Class(tk.PUNCTUATION),
              M.Class(tk.IMMEDIATE), M.Class(tk.PUNCTUATION),
              M.Class(tk.JCC), M.Class(tk.LABEL)),
        T.SeqT(T.Lit('if'), T.Lit('('), T.CopyPath([1]),
               T.Cond([5], JCC_OPS, '?'),
               T.CopyPath([3]), T.Lit(')'), T.Lit('goto'), T.CopyPath([6])),
        name='jcc_imm',
    ))

    # cmp REG , REG ; JCC LABEL
    eng.add(E.Pattern(
        M.Seq(M.Value('cmp'), M.Class(tk.REGISTER), M.Class(tk.PUNCTUATION),
              M.Class(tk.REGISTER), M.Class(tk.PUNCTUATION),
              M.Class(tk.JCC), M.Class(tk.LABEL)),
        T.SeqT(T.Lit('if'), T.Lit('('), T.CopyPath([1]),
               T.Cond([5], JCC_OPS, '?'),
               T.CopyPath([3]), T.Lit(')'), T.Lit('goto'), T.CopyPath([6])),
        name='jcc_reg',
    ))

    # jmp LABEL → goto LABEL
    eng.add(E.Pattern(
        M.Seq(M.Value('jmp'), M.Opt(M.Class(tk.PUNCTUATION)),
              M.Class(tk.LABEL)),
        T.SeqT(T.Lit('goto'), T.CopyPath([2])),
        name='jmp',
    ))
