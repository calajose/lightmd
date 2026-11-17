"""
LightMD Viewer
Visor Markdown ligero y multiplataforma basado en Tkinter.

Compatible con Python 3.8+ y pensado para equipos modestos,
incluidos sistemas Linux de 32 bits.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import time
import tkinter as tk
import traceback
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.font import Font
from typing import Dict, List, Optional

from lightmd import diagnostics
from lightmd.diagnostics import Diagnostics
from lightmd.parser import Block, InlineNode, parse_markdown


def _cap_cell(text: str, max_chars: int = 40) -> str:
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars - 1].rstrip() + "…"
    return text


MAX_COL_PX = 480
MAX_TABLE_ROWS = 500
MAX_CELL_CHARS = 40
MAX_FILE_BYTES = 8 * 1000 * 1000
RENDER_CHUNK_BLOCKS = 200
MAX_SEARCH_MATCHES = 2000


def _column_width(max_len: int, char_w: int = 10, max_px: int = MAX_COL_PX) -> int:
    return min(max(max_len * char_w, char_w * 5), max_px)


def _fit_cell(text: str, width: int) -> str:
    return _cap_cell(text, width).ljust(width)


def _format_row(cells: List[str], widths: List[int]) -> str:
    parts = []
    for index, width in enumerate(widths):
        cell = cells[index] if index < len(cells) else ""
        parts.append(_fit_cell(cell, width))
    return " │ ".join(parts)


def format_table_as_text(
    rows: List[List[str]], max_cell_chars: int = MAX_CELL_CHARS
) -> List[str]:
    """Convierte las filas de una tabla Markdown en líneas alineadas de texto.

    No crea ningún widget: elimina las ventanas X hijas dentro del ``Text``,
    que eran el origen del tráfico gráfico desmedido en Xwayland.
    """
    if not rows:
        return []

    header = [cell.strip() for cell in rows[0]]
    body = [[cell.strip() for cell in row] for row in rows[1:]]

    hidden_rows = 0
    if len(body) > MAX_TABLE_ROWS:
        hidden_rows = len(body) - MAX_TABLE_ROWS
        body = body[:MAX_TABLE_ROWS]

    widths = []
    for index in range(len(header)):
        cells = [header[index]] + [row[index] for row in body if index < len(row)]
        longest = max(len(cell) for cell in cells)
        widths.append(max(1, min(longest, max_cell_chars)))

    lines = [
        _format_row(header, widths),
        "─┼─".join("─" * width for width in widths),
    ]
    for row in body:
        lines.append(_format_row(row, widths))
    if hidden_rows:
        lines.append("… y %d filas más" % hidden_rows)
    return lines


APP_NAME = "LightMD Viewer"
DEFAULT_WIDTH = 980
DEFAULT_HEIGHT = 700


def _is_dark_windows() -> bool:
    try:
        import winreg  # type: ignore[import-not-found]
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False


def _is_dark_macos() -> bool:
    try:
        res = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        return res.returncode == 0 and "dark" in res.stdout.lower()
    except Exception:
        return False


def _is_dark_linux() -> bool:
    gtk_theme = os.environ.get("GTK_THEME", "").lower()
    if "dark" in gtk_theme:
        return True

    try:
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if res.returncode == 0 and "dark" in res.stdout.lower():
            return True
    except Exception:
        pass

    try:
        res = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if res.returncode == 0 and "dark" in res.stdout.lower():
            return True
    except Exception:
        pass

    try:
        kde_config = Path.home() / ".config" / "kdeglobals"
        if kde_config.exists():
            content = kde_config.read_text(encoding="utf-8", errors="ignore").lower()
            for line in content.splitlines():
                if ("colorscheme" in line or "lookandfeelpackage" in line) and "dark" in line:
                    return True
    except Exception:
        pass

    return False


def detect_system_dark_mode() -> bool:
    """Detecta si el sistema operativo está configurado en modo oscuro."""
    if sys.platform == "win32":
        return _is_dark_windows()
    elif sys.platform == "darwin":
        return _is_dark_macos()
    else:
        return _is_dark_linux()


class MarkdownViewer(tk.Tk):

    def __init__(
        self,
        initial_file: Optional[str] = None,
        dark_mode: Optional[bool] = None,
        safe_render: bool = False,
        grid_tables: bool = False,
        debug: bool = False,
    ) -> None:
        super().__init__(className="LightMD")

        self.current_file: Optional[Path] = None
        self.dark_mode = detect_system_dark_mode() if dark_mode is None else dark_mode
        self.link_targets: Dict[str, str] = {}
        self.search_matches: List[tuple] = []
        self.search_index = -1
        self.search_truncated = False
        self.use_grid_tables = grid_tables and not safe_render
        self._table_widgets: List[ttk.Frame] = []
        self._render_generation = 0
        self._render_status = "Listo"
        self._render_started = 0.0
        self._pending_code_block: Optional[dict] = None
        self._closing = False
        self._diagnostics = Diagnostics(metrics=debug)

        self._tree_style = ttk.Style(self)
        self._tree_style.theme_use("clam")

        self.title(APP_NAME)
        self.geometry(f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}")
        self.minsize(650, 450)

        self._app_icons: list[tk.PhotoImage] = []
        self._toolbar_icon: Optional[tk.PhotoImage] = None
        icon_path = Path(__file__).parent / "resources" / "lightmd.png"
        if icon_path.exists():
            try:
                img = tk.PhotoImage(file=str(icon_path))
                self._icon_source = img  # Evita que img se recolecte
                s16 = img.subsample(max(1, img.width() // 16))
                s32 = img.subsample(max(1, img.width() // 32))
                s64 = img.subsample(max(1, img.width() // 64))
                self._app_icons = [img, s64, s32, s16]
                self.iconphoto(True, *self._app_icons)
                # Toolbar icon ~28px
                t_factor = max(1, img.width() // 28)
                self._toolbar_icon = img.subsample(t_factor, t_factor)
            except tk.TclError:
                pass

        self._build_fonts()
        self._build_ui()
        self._build_menu()
        self._bind_shortcuts()
        self._apply_theme()

        self._diagnostics.start()
        self._schedule_heartbeat()

        if initial_file:
            self.open_path(Path(initial_file))

    def destroy(self) -> None:
        self._closing = True
        try:
            self._diagnostics.stop()
        except Exception:
            pass
        super().destroy()

    def report_callback_exception(self, exc, val, tb) -> None:
        """Registra excepciones de callbacks Tk que antes solo iban a stderr."""
        diagnostics.append_entry(
            "Excepción en callback Tk:\n" + "".join(traceback.format_exception(exc, val, tb))
        )
        if hasattr(self, "status"):
            self.status.configure(text="Error interno: %s" % val)

    def _schedule_heartbeat(self) -> None:
        self._diagnostics.beat()
        self.after(diagnostics.HEARTBEAT_INTERVAL_MS, self._schedule_heartbeat)

    def _build_fonts(self) -> None:
        base = Font(family="Sans", size=11)
        self.font_normal = base
        self.font_bold = Font(family="Sans", size=11, weight="bold")
        self.font_italic = Font(family="Sans", size=11, slant="italic")
        self.font_h1 = Font(family="Sans", size=22, weight="bold")
        self.font_h2 = Font(family="Sans", size=18, weight="bold")
        self.font_h3 = Font(family="Sans", size=15, weight="bold")
        self.font_h4 = Font(family="Sans", size=13, weight="bold")
        self.font_code = Font(family="Monospace", size=10)
        self.font_link = Font(family="Sans", size=11, underline=True)
        self.font_strikethrough = Font(family="Sans", size=11, overstrike=True)

    def _build_ui(self) -> None:
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill="x", padx=8, pady=(8, 4))

        if self._toolbar_icon:
            tk.Label(self.toolbar, image=self._toolbar_icon).pack(side="left", padx=(0, 6))

        ttk.Button(self.toolbar, text="Abrir", command=self.open_file).pack(side="left")
        ttk.Button(self.toolbar, text="Recargar", command=self.reload_file).pack(side="left", padx=(6, 0))
        self.theme_button = ttk.Button(self.toolbar, text="Oscuro", command=self.toggle_theme)
        self.theme_button.pack(side="left", padx=(6, 0))

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

        # Horizontal Scroll
        h_scrollbar = ttk.Scrollbar(content, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")

        # Vertical Scroll
        v_scrollbar = ttk.Scrollbar(content, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")

        self.text = tk.Text(
            content,
            wrap="none",
            padx=22,
            pady=18,
            relief="flat",
            undo=False,
            cursor="arrow",
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
        )
        self.text.pack(side="left", fill="both", expand=True)
        h_scrollbar.config(command=self.text.xview)
        v_scrollbar.config(command=self.text.yview)
        self.text.configure(state="disabled")

        for tag in ("link", "image"):
            self.text.tag_bind(tag, "<Enter>", lambda _: self.text.configure(cursor="hand2"))
            self.text.tag_bind(tag, "<Leave>", lambda _: self.text.configure(cursor="arrow"))

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
        help_menu.add_command(label="Diagnóstico", command=self.show_diagnostics)
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
        self.text.tag_configure("italic", font=self.font_italic, foreground=fg)
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
        self.text.tag_configure("strikethrough", font=self.font_strikethrough, foreground=fg)
        self.text.tag_configure("image", font=self.font_link, foreground=link_fg)
        self.text.tag_configure(
            "table",
            font=self.font_code,
            foreground=fg,
            lmargin1=12,
            lmargin2=12,
            spacing1=2,
            spacing3=2,
        )
        self.text.tag_configure("code_lang", font=self.font_bold, foreground=quote_fg, lmargin1=18)
        self.text.tag_configure("hr", foreground=quote_fg, spacing1=8, spacing3=8)
        self.text.tag_configure("search", background="#ffd54f", foreground="#000000")
        self.text.tag_configure("search_current", background="#ff9800", foreground="#000000")

        style = self._tree_style
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, borderwidth=0)
        style.configure("Treeview.Heading", background=code_bg, foreground=fg, borderwidth=1)
        style.map("Treeview", background=[("selected", select_bg)])
        style.map("Treeview.Heading", background=[("active", code_bg)])

        if hasattr(self, "theme_button"):
            self.theme_button.configure(text="Claro" if self.dark_mode else "Oscuro")

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
            file_stat = path.stat()
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"No se pudo abrir el archivo:\n{exc}")
            return

        if not stat.S_ISREG(file_stat.st_mode):
            messagebox.showerror(APP_NAME, f"No es un archivo regular:\n{path}")
            return

        if file_stat.st_size > MAX_FILE_BYTES:
            confirmed = messagebox.askyesno(
                APP_NAME,
                "El archivo ocupa %.1f MB.\n\n"
                "Los documentos muy grandes pueden tardar en mostrarse.\n"
                "¿Abrirlo igualmente?" % (file_stat.st_size / 1_000_000),
            )
            if not confirmed:
                self.status.configure(text="Apertura cancelada")
                return

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
        self.render_markdown(content, status_text=str(path))

    def reload_file(self) -> None:
        if self.current_file:
            self.open_path(self.current_file)

    def render_markdown(self, markdown: str, status_text: Optional[str] = None) -> None:
        blocks = parse_markdown(markdown)
        table_count = sum(1 for block in blocks if block.kind == "table")

        self._render_generation += 1
        generation = self._render_generation
        self._render_status = status_text or "Listo"
        self._render_started = time.monotonic()
        self._pending_code_block = None

        self.text.configure(state="normal")

        for widget in self._table_widgets:
            widget.destroy()
        self._table_widgets.clear()

        self.text.delete("1.0", "end")
        self.link_targets.clear()
        self.search_matches.clear()
        self.search_index = -1
        self.search_truncated = False

        self._diagnostics.record(
            "render %.2f MB, %d bloques, %d tablas, modo %s"
            % (
                len(markdown) / 1_000_000,
                len(blocks),
                table_count,
                "grid" if self.use_grid_tables else "texto",
            )
        )

        self._render_chunk(blocks, 0, generation)

    def _render_chunk(self, blocks: List[Block], start: int, generation: int) -> None:
        if self._closing or generation != self._render_generation:
            return

        end = min(start + RENDER_CHUNK_BLOCKS, len(blocks))
        for block in blocks[start:end]:
            self._render_block(block)

        if end < len(blocks):
            percent = end * 100 // len(blocks)
            self.status.configure(text="Renderizando… %d%%" % percent)
            self.after_idle(lambda: self._render_chunk(blocks, end, generation))
            return

        if self._pending_code_block is not None:
            self._insert_code_block(self._pending_code_block)
            self._pending_code_block = None

        self.text.configure(state="disabled")
        self.status.configure(text=self._render_status)
        self._diagnostics.record(
            "render completado en %.2fs (%d bloques)"
            % (time.monotonic() - self._render_started, len(blocks))
        )

    def _render_block(self, block: Block) -> None:
        if block.kind == "code_open":
            self._pending_code_block = {"lang": block.code_language, "lines": []}
        elif block.kind == "code_line":
            if self._pending_code_block is not None:
                self._pending_code_block["lines"].append(block.text)
        elif block.kind == "code_close":
            if self._pending_code_block is not None:
                self._insert_code_block(self._pending_code_block)
                self._pending_code_block = None
        elif block.kind == "blank":
            self.text.insert("end", "\n")
        elif block.kind == "hr":
            self.text.insert("end", "─" * 64 + "\n", "hr")
        elif block.kind == "heading":
            tag = "h1" if block.level == 1 else "h2" if block.level == 2 else "h3" if block.level == 3 else "h4"
            self._insert_inline(block.inline, tag)
            self.text.insert("end", "\n")
        elif block.kind == "quote":
            self.text.insert("end", "│ ", "quote")
            self._insert_inline(block.inline, "quote")
            self.text.insert("end", "\n")
        elif block.kind == "task":
            mark = "☑" if block.checked else "☐"
            self.text.insert("end", f"{mark} ", "normal")
            self._insert_inline(block.inline, "normal")
            self.text.insert("end", "\n")
        elif block.kind == "unordered":
            self.text.insert("end", "  " * block.level + "• ", "normal")
            self._insert_inline(block.inline, "normal")
            self.text.insert("end", "\n")
        elif block.kind == "ordered":
            self.text.insert("end", "  " * block.level + block.ordered_index + ". ", "normal")
            self._insert_inline(block.inline, "normal")
            self.text.insert("end", "\n")
        elif block.kind == "paragraph":
            self._insert_inline(block.inline, "normal")
            self.text.insert("end", "\n")
        elif block.kind == "table":
            self._insert_table(block)

    def _insert_code_block(self, block_data: dict) -> None:
        language = block_data["lang"]
        if language:
            self.text.insert("end", language + "\n", "code_lang")

        lines = block_data["lines"]
        if lines:
            self.text.insert("end", "\n".join(lines) + "\n", "code")
        else:
            self.text.insert("end", "\n", "code")
        self.text.insert("end", "\n")

    def _insert_inline(self, nodes: List[InlineNode], base_tag: str = "normal") -> None:
        for node in nodes:
            if node.kind == "text":
                self.text.insert("end", node.content, base_tag)
            elif node.kind == "bold":
                self.text.insert("end", node.content, (base_tag, "bold"))
            elif node.kind == "italic":
                self.text.insert("end", node.content, (base_tag, "italic"))
            elif node.kind == "strikethrough":
                self.text.insert("end", node.content, (base_tag, "strikethrough"))
            elif node.kind == "code":
                self.text.insert("end", node.content, "code")
            elif node.kind == "link":
                tag_name = f"link_{len(self.link_targets)}"
                self.link_targets[tag_name] = node.target
                self.text.insert("end", node.content, (base_tag, "link", tag_name))
                self.text.tag_bind(tag_name, "<Button-1>", lambda _, t=node.target: self.open_link(t))
            elif node.kind == "image":
                tag_name = f"img_{len(self.link_targets)}"
                self.link_targets[tag_name] = node.target
                display = f"[{node.content}]" if node.content else "[img]"
                self.text.insert("end", display, (base_tag, "image", tag_name))
                self.text.tag_bind(tag_name, "<Button-1>", lambda _, t=node.target: self.open_link(t))

    def _insert_table(self, block: Block) -> None:
        if not block.table_data:
            return

        if self.use_grid_tables:
            try:
                self._insert_table_grid(block)
                return
            except Exception as exc:
                diagnostics.append_entry("Tabla degradada a texto por error de grid: %s" % exc)

        lines = format_table_as_text(block.table_data)
        if not lines:
            return

        for line in lines:
            self.text.insert("end", line + "\n", "table")
        self.text.insert("end", "\n")

    def _insert_table_grid(self, block: Block) -> None:
        rows = block.table_data
        header = [c.strip() for c in rows[0]]
        data = [[c.strip() for c in row] for row in rows[1:]] if len(rows) > 1 else []

        col_count = len(header)
        columns = [f"col{i}" for i in range(col_count)]

        # Truncar tablas gigantes para mantener la UI receptiva en máquinas modestas
        if len(data) > MAX_TABLE_ROWS:
            ocultas = len(data) - MAX_TABLE_ROWS
            data = data[:MAX_TABLE_ROWS]
            data.append(["… y %d filas más" % ocultas] + [""] * (col_count - 1))

        frame = ttk.Frame(self.text)
        vis_rows = min(len(data), 18) if data else 1

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=vis_rows,
            selectmode="none",
        )

        tree.column("#0", width=0, stretch=False)

        # Safe access to row data
        total_width = 0
        for idx, col in enumerate(columns):
            tree.heading(col, text=header[idx])
            char_w = 8 if idx == 0 else 10
            
            # Use a safe way to get cell data, defaulting to empty string
            cell_data = []
            for r in data:
                if idx < len(r):
                    cell_data.append(r[idx])
                else:
                    cell_data.append("")
            
            max_len = max([len(c) for c in [header[idx]] + cell_data])
            width_px = _column_width(max_len, char_w, max_px=MAX_COL_PX)
            tree.column(col, width=width_px, minwidth=char_w * 5, stretch=False)
            total_width += width_px

        for row in data:
            tree.insert("", "end", values=row)

        # Asegurar que el frame tenga un ancho razonable
        min_width = min(total_width, MAX_COL_PX * col_count)
        frame.config(width=min_width)

        hscroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=hscroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        hscroll.grid(row=1, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        if data:
            vscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vscroll.set)
            vscroll.grid(row=0, column=1, sticky="ns")

        self.text.window_create("end", window=frame, stretch=1)
        self.text.insert("end", "\n\n")
        self._table_widgets.append(frame)

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
        self.search_truncated = False

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
                if len(self.search_matches) >= MAX_SEARCH_MATCHES:
                    self.search_truncated = True
                    break

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

        suffix = " (máximo alcanzado)" if self.search_truncated else ""
        self.status.configure(
            text="Coincidencia %d de %d%s"
            % (self.search_index + 1, len(self.search_matches), suffix)
        )

    def show_diagnostics(self) -> None:
        from lightmd import __version__

        report = diagnostics.system_report(__version__)
        diagnostics.append_entry("diagnóstico solicitado por el usuario")
        messagebox.showinfo("Diagnóstico de %s" % APP_NAME, report)

    def show_about(self) -> None:
        messagebox.showinfo(
            APP_NAME,
            f"{APP_NAME}\n\n"
            "Visor Markdown ligero para Linux y Windows.\n"
            "Creado con Python y Tkinter.\n\n"
            "Licencia: MIT",
        )
