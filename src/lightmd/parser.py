"""Markdown parser — produce estructuras de datos sin dependencia Tkinter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Callable, Optional


RE_HR = re.compile(r"\s*([-*_])(?:\s*\1){2,}\s*")
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
RE_QUOTE = re.compile(r"^\s*>\s?(.*)$")
RE_TASK = re.compile(r"^\s*[-+*]\s+\[([ xX])\]\s+(.*)$")
RE_UNORDERED = re.compile(r"^(\s*)[-+*]\s+(.*)$")
RE_ORDERED = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
RE_TOKEN = re.compile(
    r"(`[^`]+`|~~[^~]+~~|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|!\[[^\]]+\]\([^)]+\)|\[[^\]]+\]\([^)]+\))"
)
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
RE_IMAGE = re.compile(r"!\[([^\]]+)\]\(([^)]+)\)")


@dataclass
class InlineNode:
    kind: str
    content: str
    target: str = ""


@dataclass
class Block:
    kind: str
    level: int = 0
    checked: bool = False
    code_language: str = ""
    text: str = ""
    inline: List[InlineNode] = field(default_factory=list)
    ordered_index: str = ""
    table_data: List[List[str]] = field(default_factory=list)


def parse_inline(text: str) -> List[InlineNode]:
    nodes: List[InlineNode] = []
    position = 0

    for match in RE_TOKEN.finditer(text):
        if match.start() > position:
            nodes.append(InlineNode("text", text[position:match.start()]))

        token = match.group(0)

        if token.startswith("`") and token.endswith("`"):
            nodes.append(InlineNode("code", token[1:-1]))
        elif token.startswith("~~") and token.endswith("~~"):
            nodes.append(InlineNode("strikethrough", token[2:-2]))
        elif (token.startswith("**") and token.endswith("**")) or (
            token.startswith("__") and token.endswith("__")
        ):
            nodes.append(InlineNode("bold", token[2:-2]))
        elif (token.startswith("*") and token.endswith("*")) or (
            token.startswith("_") and token.endswith("_")
        ):
            nodes.append(InlineNode("italic", token[1:-1]))
        elif token.startswith("!["):
            img_match = RE_IMAGE.match(token)
            if img_match:
                nodes.append(InlineNode("image", img_match.group(1), target=img_match.group(2)))
        elif token.startswith("["):
            link_match = RE_LINK.match(token)
            if link_match:
                nodes.append(InlineNode("link", link_match.group(1), target=link_match.group(2)))

        position = match.end()

    if position < len(text):
        nodes.append(InlineNode("text", text[position:]))

    return nodes


def parse_hr(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    if RE_HR.fullmatch(lines[i].strip()):
        return Block(kind="hr"), i + 1
    return None


def parse_heading(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    match = RE_HEADING.match(lines[i])
    if match:
        return (
            Block(
                kind="heading",
                level=len(match.group(1)),
                inline=parse_inline(match.group(2).strip()),
            ),
            i + 1,
        )
    return None


def parse_quote(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    match = RE_QUOTE.match(lines[i])
    if match:
        return Block(kind="quote", inline=parse_inline(match.group(1))), i + 1
    return None


def parse_task(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    match = RE_TASK.match(lines[i])
    if match:
        return (
            Block(
                kind="task",
                checked=match.group(1).lower() == "x",
                inline=parse_inline(match.group(2)),
            ),
            i + 1,
        )
    return None


def parse_unordered(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    match = RE_UNORDERED.match(lines[i])
    if match:
        return (
            Block(
                kind="unordered",
                level=len(match.group(1)) // 2,
                inline=parse_inline(match.group(2)),
            ),
            i + 1,
        )
    return None


def parse_ordered(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    match = RE_ORDERED.match(lines[i])
    if match:
        return (
            Block(
                kind="ordered",
                level=len(match.group(1)) // 2,
                ordered_index=match.group(2),
                inline=parse_inline(match.group(3)),
            ),
            i + 1,
        )
    return None


def parse_table(lines: List[str], i: int) -> Optional[tuple[Block, int]]:
    if i + 1 >= len(lines):
        return None

    line = lines[i]
    next_line = lines[i + 1]

    if "|" not in line or "|" not in next_line:
        return None

    # False-positive guard: require at least 2 pipes (so "- item | x" is not a table)
    if line.count("|") < 2 and not line.lstrip().startswith("|"):
        return None

    # Consume all consecutive pipe-lines as table rows
    table_rows: List[List[str]] = []

    j = i
    while j < len(lines) and "|" in lines[j]:
        # Skip separator row if present (e.g. |---|---|)
        if all(c in "-:| " for c in lines[j]):
            j += 1
            continue

        parts = [p.strip() for p in lines[j].split("|")]
        row = [p for p in parts if p]
        if row:
            table_rows.append(row)
        j += 1

    return Block(kind="table", table_data=table_rows), j


def parse_markdown(markdown: str) -> List[Block]:
    blocks: List[Block] = []
    lines = markdown.expandtabs(4).splitlines()
    in_code_block = False
    
    # Updated parser signature: takes (lines, index) returns (Block, new_index)
    parsers: List[Callable[[List[str], int], Optional[tuple[Block, int]]]] = [
        parse_table,
        parse_hr,
        parse_heading,
        parse_quote,
        parse_task,
        parse_unordered,
        parse_ordered,
    ]

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                blocks.append(Block(kind="code_open", code_language=stripped[3:].strip()))
            else:
                in_code_block = False
                blocks.append(Block(kind="code_close"))
            i += 1
            continue

        if in_code_block:
            blocks.append(Block(kind="code_line", text=line))
            i += 1
            continue

        # Try parsers
        parsed_something = False
        for parser in parsers:
            result = parser(lines, i)
            if result:
                block, next_i = result
                blocks.append(block)
                i = next_i
                parsed_something = True
                break
        
        if parsed_something:
            continue

        if stripped == "":
            blocks.append(Block(kind="blank"))
        else:
            blocks.append(Block(kind="paragraph", inline=parse_inline(line)))
        i += 1

    return blocks
