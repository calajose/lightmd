"""CLI entry point para LightMD Viewer."""

from __future__ import annotations

import argparse

from lightmd.viewer import MarkdownViewer


def main(argv: list[str] | None = None) -> int | None:
    parser = argparse.ArgumentParser(
        prog="lightmd",
        description="Visor Markdown ligero basado en Tkinter.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Archivo Markdown a abrir (opcional)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Mostrar la versión y salir",
    )
    args = parser.parse_args(argv)

    if args.version:
        from lightmd import __version__

        print(f"lightmd {__version__}")
        return 0

    app = MarkdownViewer(args.file)
    app.mainloop()
    return None
