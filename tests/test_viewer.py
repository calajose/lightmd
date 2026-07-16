"""Tests para LightMD Viewer (sin dependencia de Tkinter)."""

from __future__ import annotations

from lightmd import __version__
from lightmd.parser import (
    RE_HR,
    RE_HEADING,
    RE_QUOTE,
    RE_TASK,
    RE_UNORDERED,
    RE_ORDERED,
    RE_TOKEN,
    Block,
    InlineNode,
    parse_inline,
    parse_markdown,
)
from lightmd.viewer import _cap_cell, _column_width, MAX_COL_PX


# ── Import / version ─────────────────────────────────────────────

def test_version() -> None:
    assert __version__ == "0.1.0"


# ── Regex de bloque ──────────────────────────────────────────────

def test_hr_regex() -> None:
    assert RE_HR.fullmatch("---")
    assert RE_HR.fullmatch("***")
    assert RE_HR.fullmatch("___")
    assert RE_HR.fullmatch("-----")
    assert RE_HR.fullmatch("- - - -")
    assert not RE_HR.fullmatch("-- ")
    assert not RE_HR.fullmatch("abc")


def test_heading_regex() -> None:
    m = RE_HEADING.match("# Title")
    assert m is not None
    assert m.group(1) == "#"
    assert m.group(2) == "Title"

    m = RE_HEADING.match("## Subtitle")
    assert m is not None
    assert m.group(1) == "##"
    assert m.group(2) == "Subtitle"

    m = RE_HEADING.match("###### Level 6")
    assert m is not None
    assert m.group(1) == "######"
    assert m.group(2) == "Level 6"

    assert RE_HEADING.match("No heading") is None


def test_quote_regex() -> None:
    m = RE_QUOTE.match("> quote")
    assert m is not None
    assert m.group(1) == "quote"

    m = RE_QUOTE.match(">  indented")
    assert m is not None
    assert m.group(1) == " indented"

    assert RE_QUOTE.match("no quote") is None


def test_task_regex() -> None:
    m = RE_TASK.match("- [x] done")
    assert m is not None
    assert m.group(1) == "x"
    assert m.group(2) == "done"

    m = RE_TASK.match("- [ ] pending")
    assert m is not None
    assert m.group(1) == " "
    assert m.group(2) == "pending"

    m = RE_TASK.match("+ [X] uppercase")
    assert m is not None
    assert m.group(1) == "X"
    assert m.group(2) == "uppercase"

    assert RE_TASK.match("- normal item") is None


def test_unordered_regex() -> None:
    m = RE_UNORDERED.match("- item")
    assert m is not None
    assert m.group(1) == ""
    assert m.group(2) == "item"

    m = RE_UNORDERED.match("  * subitem")
    assert m is not None
    assert m.group(1) == "  "
    assert m.group(2) == "subitem"

    m = RE_UNORDERED.match("    + third")
    assert m is not None
    assert m.group(1) == "    "
    assert m.group(2) == "third"


def test_ordered_regex() -> None:
    m = RE_ORDERED.match("1. first")
    assert m is not None
    assert m.group(1) == ""
    assert m.group(2) == "1"
    assert m.group(3) == "first"

    m = RE_ORDERED.match("  2. second")
    assert m is not None
    assert m.group(1) == "  "
    assert m.group(2) == "2"
    assert m.group(3) == "second"


def test_token_regex() -> None:
    text = "before **bold** after"
    match = RE_TOKEN.search(text)
    assert match is not None
    assert match.group(0) == "**bold**"

    text = "text *italic* end"
    match = RE_TOKEN.search(text)
    assert match is not None
    assert match.group(0) == "*italic*"

    text = "text `code` here"
    match = RE_TOKEN.search(text)
    assert match is not None
    assert match.group(0) == "`code`"

    text = "click [link](url) now"
    match = RE_TOKEN.search(text)
    assert match is not None
    assert match.group(0) == "[link](url)"

    text = "__bold__ and _italic_"
    match = RE_TOKEN.search(text)
    assert match is not None
    assert match.group(0) == "__bold__"


# ── parse_inline ─────────────────────────────────────────────────

def test_parse_inline_text_only() -> None:
    assert parse_inline("hello world") == [InlineNode("text", "hello world")]


def test_parse_inline_bold() -> None:
    assert parse_inline("**bold**") == [InlineNode("bold", "bold")]


def test_parse_inline_italic() -> None:
    assert parse_inline("*italic*") == [InlineNode("italic", "italic")]


def test_parse_inline_code() -> None:
    assert parse_inline("`code`") == [InlineNode("code", "code")]


def test_parse_inline_link() -> None:
    assert parse_inline("[label](url)") == [InlineNode("link", "label", target="url")]


def test_parse_inline_mixed() -> None:
    result = parse_inline("before **bold** after")
    assert result == [
        InlineNode("text", "before "),
        InlineNode("bold", "bold"),
        InlineNode("text", " after"),
    ]


def test_parse_inline_underscores() -> None:
    result = parse_inline("__bold__ and _italic_")
    assert result == [
        InlineNode("bold", "bold"),
        InlineNode("text", " and "),
        InlineNode("italic", "italic"),
    ]


def test_parse_inline_multiple_tokens() -> None:
    result = parse_inline("*a* and **b** and `c`")
    assert result == [
        InlineNode("italic", "a"),
        InlineNode("text", " and "),
        InlineNode("bold", "b"),
        InlineNode("text", " and "),
        InlineNode("code", "c"),
    ]


def test_parse_inline_strikethrough() -> None:
    assert parse_inline("~~tachado~~") == [InlineNode("strikethrough", "tachado")]


def test_parse_inline_image() -> None:
    assert parse_inline("![alt](url.png)") == [InlineNode("image", "alt", target="url.png")]


def test_parse_inline_mixed_with_new() -> None:
    result = parse_inline("text **bold** ~~tachado~~")
    assert result == [
        InlineNode("text", "text "),
        InlineNode("bold", "bold"),
        InlineNode("text", " "),
        InlineNode("strikethrough", "tachado"),
    ]


def test_parse_inline_empty() -> None:
    assert parse_inline("") == []


# ── parse_markdown ───────────────────────────────────────────────

def test_parse_empty() -> None:
    assert parse_markdown("") == []


def test_parse_heading() -> None:
    blocks = parse_markdown("# Title")
    assert len(blocks) == 1
    assert blocks[0] == Block(kind="heading", level=1, inline=[InlineNode("text", "Title")])


def test_parse_heading_levels() -> None:
    blocks = parse_markdown("## Sub\n### Subsub")
    assert len(blocks) == 2
    assert blocks[0].kind == "heading" and blocks[0].level == 2
    assert blocks[1].kind == "heading" and blocks[1].level == 3


def test_parse_hr() -> None:
    blocks = parse_markdown("---")
    assert len(blocks) == 1
    assert blocks[0].kind == "hr"


def test_parse_hr_asterisks() -> None:
    blocks = parse_markdown("***")
    assert len(blocks) == 1
    assert blocks[0].kind == "hr"


def test_parse_quote() -> None:
    blocks = parse_markdown("> cita")
    assert len(blocks) == 1
    assert blocks[0] == Block(kind="quote", inline=[InlineNode("text", "cita")])


def test_parse_quote_multiline() -> None:
    blocks = parse_markdown("> first\n> second")
    assert len(blocks) == 2
    assert all(b.kind == "quote" for b in blocks)


def test_parse_task_checked() -> None:
    blocks = parse_markdown("- [x] done")
    assert len(blocks) == 1
    assert blocks[0].kind == "task"
    assert blocks[0].checked is True


def test_parse_task_unchecked() -> None:
    blocks = parse_markdown("- [ ] pendiente")
    assert len(blocks) == 1
    assert blocks[0].kind == "task"
    assert blocks[0].checked is False


def test_parse_unordered() -> None:
    blocks = parse_markdown("- item")
    assert len(blocks) == 1
    assert blocks[0].kind == "unordered"
    assert blocks[0].level == 0


def test_parse_unordered_nested() -> None:
    blocks = parse_markdown("  * sub")
    assert len(blocks) == 1
    assert blocks[0].kind == "unordered"
    assert blocks[0].level == 1


def test_parse_ordered() -> None:
    blocks = parse_markdown("1. first")
    assert len(blocks) == 1
    assert blocks[0].kind == "ordered"
    assert blocks[0].level == 0
    assert blocks[0].ordered_index == "1"


def test_parse_paragraph() -> None:
    blocks = parse_markdown("línea normal")
    assert len(blocks) == 1
    assert blocks[0].kind == "paragraph"
    assert blocks[0].inline == [InlineNode("text", "línea normal")]


def test_parse_blank() -> None:
    blocks = parse_markdown("\n")
    assert len(blocks) == 1
    assert blocks[0].kind == "blank"


def test_parse_code_block_with_lang() -> None:
    blocks = parse_markdown("```python\nprint(1)\n```")
    assert len(blocks) == 3
    assert blocks[0] == Block(kind="code_open", code_language="python")
    assert blocks[1] == Block(kind="code_line", text="print(1)")
    assert blocks[2] == Block(kind="code_close")


def test_parse_code_block_no_lang() -> None:
    blocks = parse_markdown("```\nplain\n```")
    assert len(blocks) == 3
    assert blocks[0].kind == "code_open"
    assert blocks[0].code_language == ""
    assert blocks[1].kind == "code_line"
    assert blocks[1].text == "plain"
    assert blocks[2].kind == "code_close"


def test_parse_code_with_blank_lines() -> None:
    md = "```\na\n\nb\n```"
    blocks = parse_markdown(md)
    assert len(blocks) == 5
    assert blocks[0] == Block(kind="code_open", code_language="")
    assert blocks[1] == Block(kind="code_line", text="a")
    assert blocks[2] == Block(kind="code_line", text="")
    assert blocks[3] == Block(kind="code_line", text="b")
    assert blocks[4] == Block(kind="code_close")


def test_parse_mixed_document() -> None:
    md = "# Título\n\nTexto normal\n\n- [ ] tarea\n"
    blocks = parse_markdown(md)
    assert len(blocks) == 5
    assert blocks[0].kind == "heading"
    assert blocks[1].kind == "blank"
    assert blocks[2].kind == "paragraph"
    assert blocks[3].kind == "blank"
    assert blocks[4].kind == "task"
    assert blocks[4].checked is False


def test_parse_table() -> None:
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    blocks = parse_markdown(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "table"
    assert blocks[0].table_data == [["A", "B"], ["1", "2"]]


def test_parse_table_without_separator() -> None:
    md = "| Col1 | Col2 |\n| val1 | val2 |\n| val3 | val4 |"
    blocks = parse_markdown(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "table"
    assert blocks[0].table_data == [["Col1", "Col2"], ["val1", "val2"], ["val3", "val4"]]


def test_parse_table_single_row() -> None:
    md = "| Header |\n| data |"
    blocks = parse_markdown(md)
    assert len(blocks) == 1
    assert blocks[0].kind == "table"
    assert blocks[0].table_data == [["Header"], ["data"]]


def test_parse_table_pipe_in_list_is_not_table() -> None:
    md = "- item | other"
    blocks = parse_markdown(md)
    assert blocks[0].kind != "table"


# ── _cap_cell ─────────────────────────────────────────────────────

def test_cap_cell_short() -> None:
    assert _cap_cell("hola") == "hola"


def test_cap_cell_exact() -> None:
    assert _cap_cell("a" * 40) == "a" * 40


def test_cap_cell_truncated() -> None:
    result = _cap_cell("a" * 50)
    assert len(result) == 40
    assert result.endswith("…")


def test_cap_cell_strips_whitespace() -> None:
    assert _cap_cell("  hola  ") == "hola"


def test_cap_cell_truncated_no_trailing_space() -> None:
    result = _cap_cell("hello world" + "x" * 40)
    assert result.endswith("…")
    assert "  " not in result


# ── _column_width ─────────────────────────────────────────────────

def test_column_width_short() -> None:
    assert _column_width(10, 10) == 100


def test_column_width_hits_max() -> None:
    assert _column_width(100, 10) == MAX_COL_PX


def test_column_width_respects_minimum() -> None:
    assert _column_width(1, 10) == 50


def test_column_width_custom_max() -> None:
    result = _column_width(100, 10, max_px=10_000)
    assert result == 1000
    assert result != MAX_COL_PX


# ── CLI parser ────────────────────────────────────────────────────

def test_cli_version() -> None:
    from lightmd.cli import main

    assert main(["--version"]) == 0
