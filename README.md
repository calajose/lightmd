# LightMD Viewer

Visor Markdown ligero hecho con Python y Tkinter.

## Funciones

- Apertura de archivos `.md`, `.markdown`, `.mdown`, `.mkd` y `.txt`.
- Encabezados, listas (ordenadas y no ordenadas), tareas, citas y bloques de código.
- Negrita, cursiva, código en línea y enlaces.
- Modo claro y oscuro (`Ctrl+D`).
- Búsqueda con `Ctrl+F`.
- Recarga con `F5`.
- Apertura de un archivo desde la línea de comandos.

## Requisitos

- Python 3.8 o superior.
- Tkinter.

En antiX/Debian/Ubuntu:

```bash
sudo apt install python3 python3-tk
```

## Instalación

### Desde el código fuente

```bash
git clone https://github.com/jmcala/lightmd.git
cd lightmd
pip install .
```

### Instalación en editable (para desarrollo)

```bash
pip install -e .
```

### Con pipx (entorno aislado)

```bash
pipx install .
```

## Uso

```bash
# Abrir el visor
lightmd

# Abrir un archivo
lightmd README.md

# O usando el módulo
python -m lightmd README.md

# Versión
lightmd --version
```

El script original también sigue funcionando:

```bash
./lightmd_viewer.py README.md
```

## Asociación con archivos Markdown en Linux

Tras instalar, copia el lanzador de escritorio:

```bash
cp src/lightmd/resources/lightmd.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications
xdg-mime default lightmd.desktop text/markdown
```

## Ejecutar tests

```bash
pip install pytest
pytest
```

## Licencia

MIT
