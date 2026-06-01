"""Pattern builder — registers all instruction patterns."""
from .. import resolver as R
from .. import engine as E
from . import mov, arith, control


def build_resolver():
    r = R.Resolver()
    # Train known opcode→operator mappings at path [0]
    for op, out in [('mov', '='), ('add', '+='), ('sub', '-='),
                     ('xor', '^='), ('and', '&='), ('or', '|='),
                     ('shl', '<<='), ('shr', '>>=')]:
        r.learn(op, out, [0])
    return r


def build_engine(resolver):
    eng = E.PatternEngine()
    mov.register(resolver, eng)
    arith.register(resolver, eng)
    control.register(resolver, eng)
    return eng


def build():
    r = build_resolver()
    eng = build_engine(r)
    return r, eng
