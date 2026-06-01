"""Pattern builder — registers all instruction patterns."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import resolver as R
import engine as E
import mov, arith, ctrl


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
    ctrl.register(resolver, eng)
    return eng


def build():
    r = build_resolver()
    eng = build_engine(r)
    return r, eng
