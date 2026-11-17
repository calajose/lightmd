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
    parser.add_argument(
        "--safe-render",
        action="store_true",
        help="Renderizar tablas y código como texto, sin widgets embebidos",
    )
    parser.add_argument(
        "--grid-tables",
        action="store_true",
        help="Renderizar tablas con ttk.Treeview (experimental, mayor carga gráfica)",
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Mostrar información de diagnóstico del sistema y salir",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Registrar métricas de render en el log de diagnóstico",
    )
    args = parser.parse_args(argv)

    if args.version:
        from lightmd import __version__

        print(f"lightmd {__version__}")
        return 0

    if args.diagnose:
        from lightmd import __version__
        from lightmd.diagnostics import system_report

        print(system_report(__version__))
        return 0

    app = MarkdownViewer(
        args.file,
        safe_render=args.safe_render,
        grid_tables=args.grid_tables,
        debug=args.debug,
    )
    app.mainloop()
    return None
