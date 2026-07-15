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

## Instalación para usuarios finales (Linux)

### Instalar

El instalador crea un entorno virtual privado en
`~/.local/share/lightmd/venv`, instala LightMD dentro y añade un lanzador
al menú de aplicaciones. No requiere permisos de root.

```bash
git clone https://github.com/jmcala/lightmd.git
cd lightmd
bash scripts/install_linux.sh
```

Tras la instalación, LightMD aparece en el menú de aplicaciones y los
archivos `.md` se abren con él al hacer doble clic.

### Actualizar

```bash
cd lightmd
git pull
bash scripts/install_linux.sh
```

El instalador es idempotente: se puede ejecutar varias veces para
actualizar la instalación.

### Desinstalar

```bash
bash scripts/uninstall_linux.sh
```

Elimina el entorno virtual, el lanzador y el icono.

## Instalación para desarrolladores

### Desde el código fuente

```bash
git clone https://github.com/jmcala/lightmd.git
cd lightmd
pip install .
```

### Instalación en editable

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

## Ejecutar tests

```bash
pip install pytest
pytest
```

## Licencia

MIT
