#!/usr/bin/env python3
"""
LightMD Viewer
Visor Markdown ligero y multiplataforma basado en Tkinter.

Compatible con Python 3.8+ y pensado para equipos modestos,
incluidos sistemas Linux de 32 bits.
"""

from __future__ import annotations

import os
import re
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.font import Font
from typing import Optional


APP_NAME = "LightMD Viewer"
DEFAULT_WIDTH = 980
DEFAULT_HEIGHT = 700


class MarkdownViewer(tk.Tk):
    def __init__(self, initial_file: Optional[str] = None) -> None:
        super().__init__()

        self.current_file: Optional[Path] = None
        self.dark_mode = False
        self.link_targets: dict[str, str] = {}
        self.search_matches: list[tuple[str, str]] = []
        self.search_index = -1

        self.title(APP_NAME)
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.minsize(650, 450)

        self._build_fonts()
        self._build_ui()
        self._build_menu()
        self._bind_shortcuts()
        self._apply_theme()

        if initial_file:
            self.open_path(Path(initial_file))

    def _build_fonts(self) -> None:
        base = Font(family="Sans", size=11)
        self.font_normal = base
        self.font_bold = Font(family="Sans", size=11, weight="bold")
        self.font_h1 = Font(family="Sans", size=22, weight="bold")
        self.font_h2 = Font(family="Sans", size=18, weight="bold")
        self.font_h3 = Font(family="Sans", size=15, weight="bold")
        self.font_h4 = Font(family="Sans", size=13, weight="bold")
        self.font_code = Font(family="Monospace", size=10)
        self.font_link = Font(family="Sans", size=11, underline=True)

    def _build_ui(self) -> None:
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Button(self.toolbar, text="Abrir", command=self.open_file).pack(side="left")
        ttk.Button(self.toolbar, text="Recargar", command=self.reload_file).pack(side="left", padx=(6, 0))
        ttk.Button(self.toolbar, text="Oscuro", command=self.toggle_theme).pack(side="left", padx=(6, 0))

        self.file_label = ttk.Label(self.toolbar, text="Ningún archivo abierto")
        self.file_label.pack(side="left", padx=12)

        self.search_frame = ttk.Frame(self)
        self.search_visible = False
        self.last_search_query = ""
        self.search_entry = ttk.Entry(self.search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda _: self.search_next())
        ttk.Button(self.search_frame, text="Anterior", command=self.search_previous).pack(side="left", padx=(6, 0))
        ttk.Button(self.search_frame, text="Siguiente", command=self.search_next).pack(side="left", padx=(6, 0))
        ttk.Button(self.search_frame, text="Cerrar", command=self.hide_search).pack(side="left", padx=(6, 0))

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.text = tk.Text(
            content,
            wrap="word",
            padx=22,
            pady=18,
            relief="flat",
            undo=False,
            cursor="arrow",
        )
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set, state="disabled")

        self.status = ttk.Label(self, text="Listo", anchor="w")
        self.status.pack(fill="x", padx=8, pady=(0, 6))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Abrir…", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Recargar", accelerator="F5", command=self.reload_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", accelerator="Ctrl+Q", command=self.destroy)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Buscar", accelerator="Ctrl+F", command=self.show_search)
        view_menu.add_command(label="Cambiar tema", accelerator="Ctrl+D", command=self.toggle_theme)
        menubar.add_cascade(label="Ver", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.config(menu=menubar)

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-o>", lambda _: self.open_file())
        self.bind("<Control-q>", lambda _: self.destroy())
        self.bind("<Control-f>", lambda _: self.show_search())
        self.bind("<Control-d>", lambda _: self.toggle_theme())
        self.bind("<F5>", lambda _: self.reload_file())
        self.bind("<Escape>", lambda _: self.hide_search())

    def _apply_theme(self) -> None:
        if self.dark_mode:
            bg = "#202124"
            fg = "#e8eaed"
            code_bg = "#2b2d31"
            quote_fg = "#bdc1c6"
            link_fg = "#8ab4f8"
            select_bg = "#3f51b5"
        else:
            bg = "#ffffff"
            fg = "#202124"
            code_bg = "#f3f4f6"
            quote_fg = "#5f6368"
            link_fg = "#1a73e8"
            select_bg = "#b3d4fc"

        self.configure(bg=bg)
        self.text.configure(
            bg=bg,
            fg=fg,
            insertbackground=fg,
            selectbackground=select_bg,
        )

        self.text.tag_configure("normal", font=self.font_normal, foreground=fg, spacing1=2, spacing3=2)
        self.text.tag_configure("bold", font=self.font_bold, foreground=fg)
        self.text.tag_configure("italic", font=Font(family="Sans", size=11, slant="italic"), foreground=fg)
        self.text.tag_configure("h1", font=self.font_h1, foreground=fg, spacing1=18, spacing3=10)
        self.text.tag_configure("h2", font=self.font_h2, foreground=fg, spacing1=16, spacing3=8)
        self.text.tag_configure("h3", font=self.font_h3, foreground=fg, spacing1=14, spacing3=6)
        self.text.tag_configure("h4", font=self.font_h4, foreground=fg, spacing1=12, spacing3=5)
        self.text.tag_configure(
            "code",
            font=self.font_code,
            foreground=fg,
            background=code_bg,
            lmargin1=18,
            lmargin2=18,
            spacing1=4,
            spacing3=4,
        )
        self.text.tag_configure(
            "quote",
            font=self.font_normal,
            foreground=quote_fg,
            lmargin1=22,
            lmargin2=22,
            spacing1=4,
            spacing3=4,
        )
        self.text.tag_configure("link", font=self.font_link, foreground=link_fg)
        self.text.tag_configure("hr", foreground=quote_fg, spacing1=8, spacing3=8)
        self.text.tag_configure("search", background="#ffd54f", foreground="#000000")
        self.text.tag_configure("search_current", background="#ff9800", foreground="#000000")

        if self.current_file:
            self.reload_file()

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(
            title="Abrir archivo Markdown",
            filetypes=[
                ("Markdown", "*.md *.markdown *.mdown *.mkd"),
                ("Texto", "*.txt"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if filename:
            self.open_path(Path(filename))

    def open_path(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="latin-1")
            except OSError as exc:
                messagebox.showerror(APP_NAME, f"No se pudo abrir el archivo:\n{exc}")
                return
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"No se pudo abrir el archivo:\n{exc}")
            return

        self.current_file = path
        self.file_label.configure(text=path.name)
        self.title(f"{path.name} — {APP_NAME}")
        self.render_markdown(content)
        self.status.configure(text=str(path))

    def reload_file(self) -> None:
        if self.current_file:
            self.open_path(self.current_file)

    def render_markdown(self, markdown: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.link_targets.clear()
        self.search_matches.clear()
        self.search_index = -1

        lines = markdown.expandtabs(4).splitlines()
        in_code_block = False
        code_language = ""

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_language = stripped[3:].strip()
                    if code_language:
                        self.text.insert("end", f"{code_language}\n", ("code", "bold"))
                else:
                    in_code_block = False
                    code_language = ""
                    self.text.insert("end", "\n")
                continue

            if in_code_block:
                self.text.insert("end", line + "\n", "code")
                continue

            if re.fullmatch(r"\s*([-*_])(?:\s*\1){2,}\s*", line):
                self.text.insert("end", "─" * 64 + "\n", "hr")
                continue

            heading = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading:
                level = len(heading.group(1))
                text = heading.group(2).strip()
                tag = "h1" if level == 1 else "h2" if level == 2 else "h3" if level == 3 else "h4"
                self._insert_inline(text, tag)
                self.text.insert("end", "\n")
                continue

            quote = re.match(r"^\s*>\s?(.*)$", line)
            if quote:
                self.text.insert("end", "│ ", "quote")
                self._insert_inline(quote.group(1), "quote")
                self.text.insert("end", "\n")
                continue

            task = re.match(r"^\s*[-+*]\s+\[([ xX])\]\s+(.*)$", line)
            if task:
                mark = "☑" if task.group(1).lower() == "x" else "☐"
                self.text.insert("end", f"{mark} ", "normal")
                self._insert_inline(task.group(2), "normal")
                self.text.insert("end", "\n")
                continue

            unordered = re.match(r"^(\s*)[-+*]\s+(.*)$", line)
            if unordered:
                indent = len(unordered.group(1)) // 2
                self.text.insert("end", "  " * indent + "• ", "normal")
                self._insert_inline(unordered.group(2), "normal")
                self.text.insert("end", "\n")
                continue

            ordered = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
            if ordered:
                indent = len(ordered.group(1)) // 2
                self.text.insert("end", "  " * indent + ordered.group(2) + ". ", "normal")
                self._insert_inline(ordered.group(3), "normal")
                self.text.insert("end", "\n")
                continue

            if stripped == "":
                self.text.insert("end", "\n")
            else:
                self._insert_inline(line, "normal")
                self.text.insert("end", "\n")

        self.text.configure(state="disabled")

    def _insert_inline(self, text: str, base_tag: str = "normal") -> None:
        token_pattern = re.compile(
            r"(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))"
        )
        position = 0

        for match in token_pattern.finditer(text):
            if match.start() > position:
                self.text.insert("end", text[position:match.start()], base_tag)

            token = match.group(0)

            if token.startswith("`") and token.endswith("`"):
                self.text.insert("end", token[1:-1], "code")
            elif (token.startswith("**") and token.endswith("**")) or (
                token.startswith("__") and token.endswith("__")
            ):
                self.text.insert("end", token[2:-2], (base_tag, "bold"))
            elif (token.startswith("*") and token.endswith("*")) or (
                token.startswith("_") and token.endswith("_")
            ):
                self.text.insert("end", token[1:-1], (base_tag, "italic"))
            elif token.startswith("["):
                link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", token)
                if link_match:
                    label, target = link_match.groups()
                    tag_name = f"link_{len(self.link_targets)}"
                    self.link_targets[tag_name] = target
                    self.text.insert("end", label, (base_tag, "link", tag_name))
                    self.text.tag_bind(tag_name, "<Button-1>", lambda _, t=target: self.open_link(t))
                    self.text.tag_bind(tag_name, "<Enter>", lambda _: self.text.configure(cursor="hand2"))
                    self.text.tag_bind(tag_name, "<Leave>", lambda _: self.text.configure(cursor="arrow"))
            position = match.end()

        if position < len(text):
            self.text.insert("end", text[position:], base_tag)

    def open_link(self, target: str) -> None:
        if target.startswith(("http://", "https://", "mailto:")):
            webbrowser.open(target)
            return

        if self.current_file:
            linked_path = (self.current_file.parent / target).resolve()
            if linked_path.exists() and linked_path.suffix.lower() in {
                ".md", ".markdown", ".mdown", ".mkd", ".txt"
            }:
                self.open_path(linked_path)
            elif linked_path.exists():
                webbrowser.open(linked_path.as_uri())
            else:
                messagebox.showwarning(APP_NAME, f"No se encontró el enlace:\n{linked_path}")

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self._apply_theme()

    def show_search(self) -> None:
        if not self.search_visible:
            self.search_frame.pack(fill="x", padx=8, pady=(0, 4), after=self.toolbar)
            self.search_visible = True
        self.search_entry.focus_set()
        self.search_entry.select_range(0, "end")

    def hide_search(self) -> None:
        if self.search_visible:
            self.search_frame.pack_forget()
            self.search_visible = False
        self.text.configure(state="normal")
        self.text.tag_remove("search", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")
        self.text.configure(state="disabled")
        self.search_matches.clear()
        self.search_index = -1

    def _find_matches(self) -> None:
        query = self.search_entry.get().strip()
        self.search_matches.clear()
        self.search_index = -1

        self.text.configure(state="normal")
        self.text.tag_remove("search", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")

        if query:
            start = "1.0"
            while True:
                pos = self.text.search(query, start, stopindex="end", nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(query)}c"
                self.search_matches.append((pos, end))
                self.text.tag_add("search", pos, end)
                start = end

        self.text.configure(state="disabled")

    def search_next(self) -> None:
        current_query = self.search_entry.get().strip()
        if not current_query:
            return

        if current_query != self.last_search_query or not self.search_matches:
            self._find_matches()
            self.last_search_query = current_query

        if not self.search_matches:
            self.status.configure(text="No se encontraron coincidencias")
            return

        self.search_index = (self.search_index + 1) % len(self.search_matches)
        self._select_search_match()

    def search_previous(self) -> None:
        current_query = self.search_entry.get().strip()
        if not current_query:
            return

        if current_query != self.last_search_query or not self.search_matches:
            self._find_matches()
            self.last_search_query = current_query

        if not self.search_matches:
            self.status.configure(text="No se encontraron coincidencias")
            return

        self.search_index = (self.search_index - 1) % len(self.search_matches)
        self._select_search_match()

    def _select_search_match(self) -> None:
        start, end = self.search_matches[self.search_index]

        self.text.configure(state="normal")
        self.text.tag_remove("search_current", "1.0", "end")
        self.text.tag_add("search_current", start, end)
        self.text.see(start)
        self.text.configure(state="disabled")

        self.status.configure(
            text=f"Coincidencia {self.search_index + 1} de {len(self.search_matches)}"
        )

    def show_about(self) -> None:
        messagebox.showinfo(
            APP_NAME,
            f"{APP_NAME}\n\n"
            "Visor Markdown ligero para Linux y Windows.\n"
            "Creado con Python y Tkinter.\n\n"
            "Licencia sugerida: MIT",
        )


def main() -> None:
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None
    app = MarkdownViewer(initial_file)
    app.mainloop()


if __name__ == "__main__":
    main()
