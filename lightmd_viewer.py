#!/usr/bin/env python3
"""
LightMD Viewer - shim de compatibilidad.
Instala el paquete y usa 'lightmd' o 'python -m lightmd' en su lugar.
"""

from lightmd.cli import main

if __name__ == "__main__":
    main()
