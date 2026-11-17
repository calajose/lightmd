# LightMD Viewer

Visor Markdown ligero hecho con Python y Tkinter.

## Funciones

- Apertura de archivos `.md`, `.markdown`, `.mdown`, `.mkd` y `.txt`.
- Encabezados, listas (ordenadas y no ordenadas), tareas, citas y bloques de código.
- Negrita, cursiva, código en línea, enlaces, imágenes y tachado.
- Tablas Markdown como texto monoespaciado alineado (ligero, sin widgets embebidos), con celdas truncadas y resumen de filas en tablas enormes.
- Modo claro y oscuro (`Ctrl+D`) instantáneo, sin re-renderizar el documento.
- Búsqueda con `Ctrl+F` (limitada a 2000 coincidencias por búsqueda).
- Recarga con `F5`.
- Apertura de un archivo desde la línea de comandos.
- Diagnóstico integrado: log de fallos y de bloqueos del hilo principal.

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

# Informe de diagnóstico del entorno
lightmd --diagnose

# Forzar render en texto (sin ninguna ventana embebida)
lightmd --safe-render README.md

# Recuperar el grid experimental de tablas (mayor carga gráfica)
lightmd --grid-tables informe.md

# Registrar métricas de render en el log de diagnóstico
lightmd --debug informe.md
```

El script original también sigue funcionando:

```bash
./lightmd_viewer.py README.md
```

## Congelaciones del sistema

LightMD no dibuja con GPU: usa Tkinter sobre X11 (a través de Xwayland en
sesiones Wayland). Aun así, los documentos con muchas tablas podían generar
suficiente tráfico gráfico como para desestabilizar un driver i915 frágil.

Desde 0.4.0 no se crean ventanas X hijas al renderizar, así que la carga
gráfica es mínima. Si el equipo se congela igualmente:

1. **Comprueba el log de diagnóstico**:

   ```bash
   tail -n 50 ~/.local/state/lightmd/lightmd.log
   ```

   - Si aparece «Hilo principal bloqueado …s» con una traza dentro de
     `render_markdown` o `tag_add`, el problema es de la aplicación:
     adjunta el log a un issue.
   - Si no hay ninguna entrada, la aplicación estaba viva esperando en
     `mainloop` y el cuelgue es del sistema gráfico.

2. **Comprueba los logs del kernel** tras reiniciar:

   ```bash
   journalctl -b -1 -k | grep -iE "GPU HANG|i915|drm"
   ```

   Mensajes como `GPU HANG … in Xwayland`, `Failed to reset GuC` o
   `device wedged, needs recovery` son fallos del driver, no de LightMD.
   En ese caso conviene reportarlos upstream (freedesktop / kernel) y
   probar el mismo documento en una sesión X11 y en otro kernel antes de
   descartar la app.

3. **Aísla el detonante**: abre el mismo documento con `--safe-render`
   (sin ninguna ventana embebida) y, si hace falta, con `--grid-tables`
   para comparar. La combinación «texto sí, grid no» apunta al render
   de tablas; «ambos fallan» apunta al sistema.

## Ejecutar tests

```bash
pip install pytest
pytest
```

## Licencia

MIT
