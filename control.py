"""
Control flow graph builder and structural decompiler — v3 port.

Builds basic blocks from a token stream (split on semicolons),
constructs a CFG from labels and jumps, and produces structured C
with if/else, while loops, and nesting.

Usage:
    from control import decompile
    c_code = decompile(token_stream)
"""

import re
from collections import defaultdict


class BasicBlock:
    def __init__(self, name: str = ''):
        self.name = name
        self.stmts: list[list[str]] = []
        self.label: str | None = None
        self.falls_to: 'BasicBlock | None' = None
        self.branch_true: 'BasicBlock | None' = None
        self.branch_false: 'BasicBlock | None' = None
        self.is_conditional = False
        self.back_edge_target: str | None = None

    def add_stmt(self, stmt: list[str]):
        self.stmts.append(stmt)

    @property
    def has_jump(self) -> bool:
        if not self.stmts:
            return False
        return 'goto' in ' '.join(self.stmts[-1])

    @property
    def jump_target(self) -> str | None:
        if not self.has_jump:
            return None
        m = re.search(r'goto\s+(\S+)', ' '.join(self.stmts[-1]))
        return m.group(1) if m else None

    @property
    def condition_text(self) -> str:
        for stmt in self.stmts:
            s = ' '.join(stmt)
            m = re.search(r'if\s*\(\s*(.*?)\s*\)', s)
            if m:
                return m.group(1)
        return ''

    def text(self) -> str:
        return '; '.join(' '.join(s) for s in self.stmts)

    def __repr__(self):
        lbl = f" {self.label}:" if self.label else ""
        jmp = f" → {self.jump_target}" if self.has_jump else ""
        cond = f" if({self.condition_text})" if self.is_conditional else ""
        back = f" ← BACK" if self.back_edge_target else ""
        return f"Block{self.name}{lbl}{cond}{jmp}{back} [{len(self.stmts)} stmts]"


class ControlFlowGraph:
    def __init__(self):
        self.blocks: list[BasicBlock] = []
        self.block_by_label: dict[str, BasicBlock] = {}
        self.entry: BasicBlock | None = None

    def build(self, stmts: list[list[str]]):
        def is_label(s):
            t = ' '.join(s) if s else ''
            return bool(re.match(r'^\w+\s*:\s*$', t))

        def has_label(s):
            t = ' '.join(s) if s else ''
            return ':' in t

        labels = {}
        for i, stmt in enumerate(stmts):
            for j, tok in enumerate(stmt):
                if tok.endswith(':') and len(tok) > 1:
                    labels[tok[:-1]] = i
                    break
                if tok == ':' and j > 0 and len(stmt[j-1]) > 0:
                    labels[stmt[j-1]] = i
                    break

        leaders = {0}
        for lpos in labels.values():
            leaders.add(lpos)
        for i, stmt in enumerate(stmts):
            s = ' '.join(stmt) if stmt else ''
            if 'if' in s:
                leaders.add(i + 1) if i + 1 < len(stmts) else None
            if 'goto' in s or 'jmp' in s:
                leaders.add(i + 1) if i + 1 < len(stmts) else None

        leaders = sorted(leaders)
        for idx in range(len(leaders)):
            start = leaders[idx]
            end = leaders[idx + 1] if idx + 1 < len(leaders) else len(stmts)
            block = BasicBlock(name=f"B{idx}")
            for i in range(start, end):
                s = stmts[i]
                if is_label(s):
                    block.label = ' '.join(s).rstrip(':').strip()
                elif s:
                    block.add_stmt(s)
            for lbl, pos in labels.items():
                if pos == start:
                    block.label = lbl
            for stmt in block.stmts:
                if 'if' in ' '.join(stmt) and not has_label(stmt):
                    block.is_conditional = True
                    break
            self.blocks.append(block)

        for blk in self.blocks:
            if blk.label and blk.label not in self.block_by_label:
                self.block_by_label[blk.label] = blk

        for i, blk in enumerate(self.blocks):
            if blk.has_jump:
                tgt = blk.jump_target
                if tgt and tgt in self.block_by_label:
                    target = self.block_by_label[tgt]
                    if self.blocks.index(target) <= i:
                        blk.back_edge_target = tgt
                    else:
                        blk.branch_true = target
            if blk.is_conditional:
                if i + 1 < len(self.blocks):
                    blk.branch_false = self.blocks[i + 1]
            elif not blk.has_jump and i + 1 < len(self.blocks):
                blk.falls_to = self.blocks[i + 1]

        self.entry = self.blocks[0] if self.blocks else None

    def __repr__(self):
        lines = [f"CFG ({len(self.blocks)} blocks):"]
        for b in self.blocks:
            edges = []
            if b.falls_to:
                edges.append(f"fall→{b.falls_to.name}")
            if b.branch_true:
                edges.append(f"T→{b.branch_true.name}")
            if b.branch_false:
                edges.append(f"F→{b.branch_false.name}")
            back = " ←BACK" if b.back_edge_target else ""
            lines.append(f"  {b.name}: {b.text():40s} {' '.join(edges)}{back}")
        return '\n'.join(lines)


class StructuredNode:
    def __init__(self, kind: str, **kwargs):
        self.kind = kind
        self.body: list = kwargs.get('body', [])
        self.condition: str = kwargs.get('condition', '')
        self.true_branch: 'StructuredNode | None' = kwargs.get('true_branch')
        self.false_branch: 'StructuredNode | None' = kwargs.get('false_branch')
        self.text: str = kwargs.get('text', '')

    def emit(self, indent: str = '') -> str:
        if self.kind == 'block':
            return self._emit_block(indent)
        elif self.kind == 'if':
            return self._emit_if(indent)
        elif self.kind == 'while':
            return self._emit_while(indent)
        elif self.kind == 'stmt':
            return f"{indent}{self.text};" if self.text else ''
        return ''

    def _emit_block(self, indent: str) -> str:
        if not self.body:
            return f"{indent}{{}}"
        lines = [f"{indent}{{"]
        for c in self.body:
            o = c.emit(indent + '    ')
            if o:
                lines.append(o)
        lines.append(f"{indent}}}")
        return '\n'.join(lines)

    def _emit_if(self, indent: str) -> str:
        t = self.true_branch.emit(indent) if self.true_branch else '{}'
        lines = [f"{indent}if ({self.condition}) {t}"]
        if self.false_branch and self.false_branch.kind != 'empty':
            e = self.false_branch.emit(indent)
            lines.append(f"{indent}else {e}")
        return '\n'.join(lines)

    def _emit_while(self, indent: str) -> str:
        body = StructuredNode('block', body=self.body) if self.body else None
        b = body.emit(indent) if body else '{}'
        return f"{indent}while ({self.condition}) {b}"


def _invert_cond(cond: str) -> str:
    pairs = [('==', '!='), ('!=', '=='), ('<', '>='), ('<=', '>'),
             ('>', '<='), ('>=', '<')]
    for old, new in pairs:
        if old in cond:
            return cond.replace(old, new, 1)
    return cond


def _find_loop_headers(cfg):
    headers = set()
    for b in cfg.blocks:
        if b.back_edge_target:
            target = cfg.block_by_label.get(b.back_edge_target)
            if target:
                headers.add(target.name)
    return headers


def _structure(cfg, block, visited, loop_header, loop_latch, loop_headers):
    if block is None or block.name in visited:
        return StructuredNode('empty')
    if block is loop_latch and loop_header is not None:
        return StructuredNode('empty')

    visited = visited | {block.name}

    if block.name in loop_headers and loop_header is None:
        for b in cfg.blocks:
            if b.back_edge_target and cfg.block_by_label.get(b.back_edge_target) is block:
                return _structure_loop(cfg, b, visited)
        return _structure(cfg, block.falls_to, visited, loop_header, loop_latch, loop_headers) if block.falls_to else StructuredNode('empty')

    if block.back_edge_target:
        if block is loop_latch and loop_header is not None:
            return StructuredNode('empty')
        return _structure_loop(cfg, block, visited)

    if block.is_conditional:
        cond = _invert_cond(block.condition_text)
        then_node = _structure(cfg, block.branch_false, visited.copy(), loop_header, loop_latch, loop_headers) if block.branch_false else StructuredNode('empty')
        else_node = _structure(cfg, block.branch_true, visited.copy(), loop_header, loop_latch, loop_headers) if block.branch_true else StructuredNode('empty')
        return StructuredNode('if', condition=cond, true_branch=then_node, false_branch=else_node)

    children = [StructuredNode('stmt', text=' '.join(s)) for s in block.stmts]
    if block.falls_to:
        rest = _structure(cfg, block.falls_to, visited, loop_header, loop_latch, loop_headers)
        if rest.kind != 'empty':
            children.append(rest)
    return StructuredNode('block', body=children) if len(children) > 1 else (children[0] if children else StructuredNode('empty'))


def _structure_loop(cfg, latch, visited):
    target = latch.back_edge_target
    header = cfg.block_by_label.get(target) if target else None
    if not header:
        return StructuredNode('empty')

    loop_vis = visited | {latch.name, header.name}
    body_stmts = []
    loop_headers = _find_loop_headers(cfg)

    if header is latch:
        for s in header.stmts:
            t = ' '.join(s)
            if 'if' not in t and 'goto' not in t:
                body_stmts.append(StructuredNode('stmt', text=t))
    elif header.is_conditional:
        inner = _structure(cfg, header, loop_vis, header, latch, loop_headers)
        if inner.kind != 'empty':
            body_stmts.append(inner)
    else:
        seen = set()
        for b in cfg.blocks:
            if b is header:
                for s in b.stmts:
                    body_stmts.append(StructuredNode('stmt', text=' '.join(s)))
                continue
            if b is latch:
                break
            if b.name in visited or b.name in seen:
                continue
            seen.add(b.name)
            sub = _structure(cfg, b, loop_vis, header, latch, loop_headers)
            if sub.kind != 'empty':
                body_stmts.append(sub)

    cond = latch.condition_text
    body = StructuredNode('block', body=body_stmts) if body_stmts else None
    return StructuredNode('while', condition=cond, body=body.body if body else [])


def decompile(tokens: list[str]) -> str:
    """Full pipeline: token stream → structured C."""
    stmts = []
    cur = []
    for tok in tokens:
        if tok == ';':
            if cur:
                stmts.append(cur)
                cur = []
        else:
            cur.append(tok)
    if cur:
        stmts.append(cur)

    cfg = ControlFlowGraph()
    cfg.build(stmts)

    loop_headers = _find_loop_headers(cfg)
    ast = _structure(cfg, cfg.entry, set(), None, None, loop_headers)

    result = ast.emit().strip()
    # Cleanup
    result = re.sub(r'(?m)^[ \t]*\w+\s*:\s*(;.*)?$', '', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()
