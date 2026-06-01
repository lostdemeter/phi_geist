"""
Assembly normalizer — v3 port.

Converts real x86 assembly (gcc -masm=intel output) to the
pseudo-asm format used by our decompiler patterns.
"""

import re


def normalize(x86_asm: str) -> str:
    """Normalize gcc-style x86 to pseudo-asm.
    
    Two-pass: regex first (handles DWORD PTR, .L labels, function frame),
    then stripped of prologue/epilogue.
    """
    result = []
    for line in x86_asm.split('\n'):
        line = re.sub(r'\s+', ' ', line.strip())
        if not line:
            continue

        label = re.match(r'^\.?([A-Za-z0-9_]+):', line)
        if label:
            result.append(f"{label.group(1)} :")
            continue

        line = re.sub(r'mov\s+DWORD\s+PTR\s+-\d+\[\w+\]\s*,\s*(\d+)',
                      r'mov eax, \1', line)
        line = re.sub(r'add\s+DWORD\s+PTR\s+-\d+\[\w+\]\s*,\s*(\d+)',
                      r'add eax, \1', line)
        line = re.sub(r'cmp\s+DWORD\s+PTR\s+-\d+\[\w+\]\s*,\s*(\d+)',
                      r'cmp eax, \1', line)
        line = re.sub(r'mov\s+(\w+),\s*DWORD\s+PTR\s+-\d+\[\w+\]',
                      r'mov \1, eax', line)
        line = re.sub(r'\.(L\d+)', r'\1', line)

        stripped = line.strip()
        if stripped in ('endbr64', 'push rbp', 'mov rbp, rsp',
                        'pop rbp', 'ret', 'nop', 'leave'):
            continue

        result.append(line)

    return '\n'.join(result)
