"""Markdown parser — produce estructuras de datos sin dependencia Tkinter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List


RE_HR = re.compile(r"\s*([-*_])(?:\s*\1){2,}\s*")
RE_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
RE_QUOTE = re.compile(r"^\s*>\s?(.*)$")
RE_TASK = re.compile(r"^\s*[-+*]\s+\[([ xX])\]\s+(.*)$")
RE_UNORDERED = re.compile(r"^(\s*)[-+*]\s+(.*)$")
RE_ORDERED = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")
RE_TOKEN = re.compile(
    r"(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))"
)
RE_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


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


def parse_inline(text: str) -> List[InlineNode]:
    nodes: List[InlineNode] = []
    position = 0

    for match in RE_TOKEN.finditer(text):
        if match.start() > position:
            nodes.append(InlineNode("text", text[position:match.start()]))

        token = match.group(0)

        if token.startswith("`") and token.endswith("`"):
            nodes.append(InlineNode("code", token[1:-1]))
        elif (token.startswith("**") and token.endswith("**")) or (
            token.startswith("__") and token.endswith("__")
        ):
            nodes.append(InlineNode("bold", token[2:-2]))
        elif (token.startswith("*") and token.endswith("*")) or (
            token.startswith("_") and token.endswith("_")
        ):
            nodes.append(InlineNode("italic", token[1:-1]))
        elif token.startswith("["):
            link_match = RE_LINK.match(token)
            if link_match:
                nodes.append(InlineNode("link", link_match.group(1), target=link_match.group(2)))

        position = match.end()

    if position < len(text):
        nodes.append(InlineNode("text", text[position:]))

    return nodes


def parse_markdown(markdown: str) -> List[Block]:
    blocks: List[Block] = []
    lines = markdown.expandtabs(4).splitlines()
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_code_block:
                in_code_block = True
                blocks.append(Block(kind="code_open", code_language=stripped[3:].strip()))
            else:
                in_code_block = False
                blocks.append(Block(kind="code_close"))
            continue

        if in_code_block:
            blocks.append(Block(kind="code_line", text=line))
            continue

        if RE_HR.fullmatch(stripped):
            blocks.append(Block(kind="hr"))
            continue

        heading = RE_HEADING.match(line)
        if heading:
            blocks.append(
                Block(
                    kind="heading",
                    level=len(heading.group(1)),
                    inline=parse_inline(heading.group(2).strip()),
                )
            )
            continue

        quote = RE_QUOTE.match(line)
        if quote:
            blocks.append(Block(kind="quote", inline=parse_inline(quote.group(1))))
            continue

        task = RE_TASK.match(line)
        if task:
            blocks.append(
                Block(
                    kind="task",
                    checked=task.group(1).lower() == "x",
                    inline=parse_inline(task.group(2)),
                )
            )
            continue

        unordered = RE_UNORDERED.match(line)
        if unordered:
            blocks.append(
                Block(
                    kind="unordered",
                    level=len(unordered.group(1)) // 2,
                    inline=parse_inline(unordered.group(2)),
                )
            )
            continue

        ordered = RE_ORDERED.match(line)
        if ordered:
            blocks.append(
                Block(
                    kind="ordered",
                    level=len(ordered.group(1)) // 2,
                    ordered_index=ordered.group(2),
                    inline=parse_inline(ordered.group(3)),
                )
            )
            continue

        if stripped == "":
            blocks.append(Block(kind="blank"))
        else:
            blocks.append(Block(kind="paragraph", inline=parse_inline(line)))

    return blocks
