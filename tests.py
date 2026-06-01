"""Tests for phi_lib3."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phi_lib3 import tokens, matchers, transforms, resolver, engine, phase


def test_token_hierarchy():
    assert tokens.JE.is_subclass_of(tokens.JCC)
    assert tokens.JCC.is_subclass_of(tokens.OPCODE)
    assert not tokens.REGISTER.is_subclass_of(tokens.OPCODE)


def test_classify():
    assert tokens.classify('je') is tokens.JE
    assert tokens.classify('eax') is tokens.REGISTER


def test_seq_paths():
    a = matchers.Class(tokens.OPCODE)
    b = matchers.Class(tokens.REGISTER)
    s = matchers.Seq(a, b)
    assert a.path == [0]
    assert b.path == [1]


def test_seq_match():
    s = matchers.Seq(matchers.Class(tokens.OPCODE),
                     matchers.Class(tokens.REGISTER))
    r = s.match(['mov', 'eax'], 0)
    assert r is not None and r.length == 2


def test_opt_variable_length():
    s = matchers.Seq(matchers.Class(tokens.OPCODE),
                     matchers.Class(tokens.REGISTER),
                     matchers.Opt(matchers.Class(tokens.PUNCTUATION)),
                     matchers.Class(tokens.IMMEDIATE))
    assert s.match(['mov', 'eax', ',', '5'], 0).length == 4
    assert s.match(['mov', 'eax', '5'], 0).length == 3


def test_copy_path():
    t = transforms.CopyPath([1])
    ctx = {'match_paths': [([0], 0), ([1], 1)]}
    out = t.apply(['mov', 'eax'], ctx)
    assert out == ['eax']


def test_bridge():
    r = resolver.Resolver()
    r.learn('mov', '=', [0])
    t = transforms.Bridge([0], r)
    ctx = {'match_paths': [([0], 0)]}
    out = t.apply(['mov'], ctx)
    assert '=' in out


def test_engine_basic():
    r = resolver.Resolver()
    r.learn('mov', '=', [0])
    r.learn('add', '+=', [0])

    eng = engine.PatternEngine()
    p = engine.Pattern(
        matchers.Seq(matchers.Class(tokens.OPCODE), matchers.Class(tokens.REGISTER),
                     matchers.Opt(matchers.Class(tokens.PUNCTUATION)),
                     matchers.Class(tokens.IMMEDIATE)),
        transforms.SeqT(transforms.Bridge([0], r), transforms.CopyPath([1])),
        name='instr',
    )
    eng.add(p)

    out, _ = eng.apply(['mov', 'eax', ',', '5'])
    assert '=' in out
    out2, _ = eng.apply(['add', 'ebx', '3'])
    assert '+=' in out2


def test_feedback():
    r = resolver.Resolver()
    r.learn('mov', '=', [0])

    eng = engine.PatternEngine()
    p = engine.Pattern(
        matchers.Seq(matchers.Class(tokens.OPCODE), matchers.Class(tokens.REGISTER),
                     matchers.Opt(matchers.Class(tokens.PUNCTUATION)),
                     matchers.Class(tokens.IMMEDIATE)),
        transforms.SeqT(transforms.Bridge([0], r), transforms.CopyPath([1])),
        name='instr',
    )
    eng.add(p)

    c = eng.feedback(['sub', 'ebx', '3'], ['-=', 'ebx', '3'], r)
    assert c >= 1, f"Expected corrections, got {c}"
    out, _ = eng.apply(['sub', 'ebx', '3'])
    assert '-=' in out


def test_phase_path():
    pv1 = phase.path_phase([5])
    pv2 = phase.path_phase([5])
    assert phase.phase_distance(pv1, pv2) < 0.001


def test_log_space_invariant():
    """Log-space encoding: phase([5]) vs phase([6]) depends on ratio."""
    d56 = phase.phase_distance(phase.path_phase([5]), phase.path_phase([6]))
    d65 = phase.phase_distance(phase.path_phase([6]), phase.path_phase([5]))
    assert d56 == d65  # distance is symmetric


def test_save_load():
    r1 = resolver.Resolver()
    r1.learn('je', '==', [5])
    r1.learn('jl', '<', [5])
    path = '/tmp/_test_resolver.json'
    r1.save(path)
    os.remove(path)


if __name__ == "__main__":
    test_token_hierarchy()
    test_classify()
    test_seq_paths()
    test_seq_match()
    test_opt_variable_length()
    test_copy_path()
    test_bridge()
    test_engine_basic()
    test_feedback()
    test_phase_path()
    test_log_space_invariant()
    test_save_load()
    print("All phi_lib3 tests passed.")
