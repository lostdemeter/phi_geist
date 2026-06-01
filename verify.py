"""
Re-compile verification — v3 port.

Pipeline:
  1. Wrap decompiled C in a compilable function
  2. Compile with gcc -c -S -masm=intel
  3. Normalize both original and re-compiled assembly
  4. Structured diff
"""

import subprocess, tempfile, os, re
from collections import defaultdict
from normalize import normalize


def compile_to_asm(c_code: str, compiler: str = 'gcc') -> tuple[bool, str, str]:
    """Returns (success, asm_text, error)."""
    with tempfile.TemporaryDirectory() as tmp:
        c_path = os.path.join(tmp, 'test.c')
        s_path = os.path.join(tmp, 'test.s')
        with open(c_path, 'w') as f:
            f.write(c_code)
        r = subprocess.run(
            [compiler, '-c', '-S', '-O0', '-masm=intel',
             '-fno-asynchronous-unwind-tables', '-o', s_path, c_path],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return False, '', r.stderr
        with open(s_path) as f:
            return True, f.read(), ''


def wrap_c(c_code: str, func_name: str = 'test') -> str:
    """Wrap decompiled C with variable declarations."""
    vars_used = set()
    for tok in re.findall(r'\b[a-z_]\w+\b', c_code):
        if re.match(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)$', tok):
            vars_used.add(tok)
    decls = f"    int {', '.join(sorted(vars_used))};\n" if vars_used else ''
    body = '\n'.join('    ' + l for l in c_code.split('\n'))
    return f"void {func_name}() {{\n{decls}{body}\n}}"


def extract_ops(asm_text: str) -> list[str]:
    """Extract normalized opcode sequences for comparison."""
    ops = []
    for line in asm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('.') or line.endswith(':'):
            continue
        line = re.sub(r'^[a-f0-9]+\s*:', '', line).strip()
        if not line:
            continue
        op = line.split()[0] if line.split() else ''
        if op:
            ops.append(op)
    return ops


def semantic_score(orig_asm: str, recomp_asm: str) -> float:
    """Jaccard similarity of opcode sets."""
    orig_ops = set(extract_ops(orig_asm))
    recomp_ops = set(extract_ops(recomp_asm))
    if not orig_ops:
        return 1.0 if not recomp_ops else 0.0
    intersection = orig_ops & recomp_ops
    union = orig_ops | recomp_ops
    return len(intersection) / len(union)


def verify(decompiled_c: str, original_asm: str = '',
           compiler: str = 'gcc') -> dict:
    """Full verification pipeline."""
    wrapped = wrap_c(decompiled_c)
    ok, asm_text, err = compile_to_asm(wrapped, compiler)
    result = {
        'compiles': ok,
        'error': err,
        'asm': asm_text if ok else '',
        'score': 0.0,
        'issues': [],
    }
    if ok and original_asm:
        result['score'] = semantic_score(original_asm, asm_text)
        orig_norm = normalize(original_asm)
        recomp_norm = normalize(asm_text)
        orig_ops = extract_ops(orig_norm)
        recomp_ops = extract_ops(recomp_norm)
        diff = []
        for i, (a, b) in enumerate(zip(orig_ops, recomp_ops)):
            if a != b:
                diff.append({'pos': i, 'orig': a, 'recomp': b})
        result['issues'] = diff
    return result


def report(result: dict) -> str:
    lines = ["=" * 60, "  VERIFICATION REPORT", "=" * 60]
    if not result['compiles']:
        lines.append("\n  ✗ COMPILE ERROR:")
        for line in result['error'].split('\n')[:5]:
            lines.append(f"    {line}")
        return '\n'.join(lines)
    lines.append(f"\n  ✓ Compiles successfully")
    issues = result.get('issues', [])
    score = result.get('score', 0)
    lines.append(f"  Semantic score: {score:.3f}")
    if issues:
        lines.append(f"  {len(issues)} instruction opcode mismatches:")
        for issue in issues[:10]:
            lines.append(f"    pos {issue['pos']}: expected '{issue['orig']}' "
                         f"got '{issue['recomp']}'")
        if len(issues) > 10:
            lines.append(f"    ... ({len(issues) - 10} more)")
    return '\n'.join(lines)
