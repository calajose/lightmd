"""LightMD Viewer - Visor Markdown ligero basado en Tkinter."""

from __future__ import annotations

__version__ = "0.3.0"

from lightmd.viewer import MarkdownViewer
from lightmd.cli import main

__all__ = ["MarkdownViewer", "main"]
