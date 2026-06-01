"""
Token class hierarchy — v3.

JE < JCC < OPCODE < STRUCTURE < TOKEN
REGISTER < DATA < TOKEN
"""

import re


class Meta:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        parts = [name]
        p = parent
        while p:
            parts.append(p.name)
            p = p.parent
        self._path = tuple(reversed(parts))
        if parent is not None:
            parent.children.append(self)

    def is_subclass_of(self, other):
        if self is other:
            return True
        if self.parent is None:
            return False
        return self.parent.is_subclass_of(other)

    def __repr__(self):
        return self.name


def _make(name, parent=None):
    m = Meta(name, parent)
    globals()[name] = m
    return m


TOKEN = _make('TOKEN')
DATA = _make('DATA', TOKEN)
REGISTER = _make('REGISTER', DATA)
IMMEDIATE = _make('IMMEDIATE', DATA)
LABEL = _make('LABEL', DATA)
STRUCTURE = _make('STRUCTURE', TOKEN)
OPCODE = _make('OPCODE', STRUCTURE)
MOV = _make('MOV', OPCODE)
ADD = _make('ADD', OPCODE)
SUB = _make('SUB', OPCODE)
INC = _make('INC', OPCODE)
CMP = _make('CMP', OPCODE)
JCC = _make('JCC', OPCODE)
JE = _make('JE', JCC)
JNE = _make('JNE', JCC)
JG = _make('JG', JCC)
JGE = _make('JGE', JCC)
JL = _make('JL', JCC)
JLE = _make('JLE', JCC)
PUNCTUATION = _make('PUNCTUATION', STRUCTURE)

_JCC_MAP = {
    'je': JE, 'jne': JNE, 'jg': JG, 'jge': JGE,
    'jl': JL, 'jle': JLE,
}

_OPCODE_MAP = {
    'mov': MOV, 'add': ADD, 'sub': SUB, 'inc': INC, 'cmp': CMP,
}

_RE_MAP = [
    (r'^(eax|ebx|ecx|edx|esi|edi|esp|ebp)$', REGISTER),
    (r'^-?\d+$', IMMEDIATE),
    (r'^[A-Z]\d+$', LABEL),
    (r'^[;:,(){}]$', PUNCTUATION),
]


def classify(token: str) -> Meta:
    if token in _JCC_MAP:
        return _JCC_MAP[token]
    if token in _OPCODE_MAP:
        return _OPCODE_MAP[token]
    for pat, cls in _RE_MAP:
        if re.match(pat, token):
            return cls
    return OPCODE


def matches(token: str, cls) -> bool:
    return classify(token).is_subclass_of(cls)
