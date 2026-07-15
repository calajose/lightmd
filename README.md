# LightMD Viewer

Visor Markdown ligero hecho con Python y Tkinter.

## Funciones actuales

- Apertura de archivos `.md`, `.markdown` y `.txt`.
- Encabezados, listas, citas y bloques de código.
- Negrita, cursiva, código en línea y enlaces.
- Modo claro y oscuro.
- Búsqueda con `Ctrl+F`.
- Recarga con `F5`.
- Apertura de un archivo desde la línea de comandos.

## Requisitos

- Python 3.8 o superior.
- Tkinter.

En antiX/Debian:

```bash
sudo apt install python3 python3-tk
```

## Ejecución

```bash
python3 lightmd_viewer.py
```

Abrir directamente un archivo:

```bash
python3 lightmd_viewer.py README.md
```

## Hacerlo ejecutable

```bash
chmod +x lightmd_viewer.py
./lightmd_viewer.py README.md
```

## Asociación con archivos Markdown en Linux

Puedes crear este lanzador:

```ini
[Desktop Entry]
Name=LightMD Viewer
Comment=Visor Markdown ligero
Exec=python3 /ruta/completa/lightmd_viewer.py %f
Icon=text-x-markdown
Terminal=false
Type=Application
MimeType=text/markdown;text/plain;
Categories=Utility;TextEditor;
```

Guárdalo como:

```text
~/.local/share/applications/lightmd-viewer.desktop
```

Después ejecuta:

```bash
update-desktop-database ~/.local/share/applications
xdg-mime default lightmd-viewer.desktop text/markdown
```
