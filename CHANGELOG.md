# Changelog

All notable changes to LightMD Viewer will be documented in this file.

The format is based on [Keep a Changelog][keepachangelog],
and this project adheres to [Semantic Versioning][semver].

[keepachangelog]: https://keepachangelog.com/
[semver]: https://semver.org/

## [Unreleased]

## [0.4.0] - 2026-11-17

### Fixed

- Congelación del sistema al abrir o recargar documentos con muchas tablas. Las tablas y los bloques de código se renderizan ahora como **texto alineado dentro del `Text` principal**: se eliminan las decenas de ventanas X hijas (`window_create` + `ttk.Treeview` + scrollbars) que generaban una ráfaga de `ConfigureNotify`/`Expose` a través de Xwayland y saturaban el motor gráfico.
- El cambio de tema (claro/oscuro) ya no vuelve a renderizar el documento: solo reconfigura los tags del `Text`. Antes destruía y recreaba todas las ventanas embebidas en cada pulsación.
- Fuga de fuentes Tcl: `_apply_theme()` creaba una `Font` nueva en cada llamada; ahora se reutiliza `font_italic`.

### Added

- `src/lightmd/diagnostics.py`: registro *best-effort* de fallos (`faulthandler`), volcado de trazas cuando el hilo principal se bloquea más de 5 s (watchdog con latido desde Tk) y métricas de render. Permite distinguir «la app está atascada» de «el sistema gráfico se ha colgado».
- Log en `$XDG_STATE_HOME/lightmd/lightmd.log` (por defecto `~/.local/state/lightmd/lightmd.log`), con rotación a 1 MB.
- Excepciones de callbacks Tk registradas en el log y mostradas en la barra de estado, en lugar de perderse en `stderr`.
- Opciones de CLI: `--safe-render` (fuerza render en texto), `--grid-tables` (mantiene el `ttk.Treeview` experimental), `--diagnose` (informe del entorno y salida) y `--debug` (métricas de render).
- Menú **Ayuda → Diagnóstico** con el informe del entorno.
- Render troceado (`RENDER_CHUNK_BLOCKS = 200`) con `after_idle`: el bucle de eventos respira durante documentos grandes y un nuevo documento cancela el render en curso.

### Changed

- Tablas Markdown: se dibujan como texto monoespaciado alineado, con celdas truncadas a 40 caracteres (`MAX_CELL_CHARS`) y resumen «… y N filas más» a partir de 500 filas. Se pierden el grid interactivo y el scroll por tabla, pero también el tráfico gráfico que provocaba los bloqueos. `--grid-tables` permite recuperar el comportamiento anterior.
- Bloques de código: sin `Text` interior ni scrollbar propia; usan el scroll horizontal del documento.
- Líneas en blanco: se preservan al renderizar (antes se descartaban y los párrafos quedaban pegados).

### Notes

- Investigación del incidente del 2026-11-17 (congelación total al abrir un informe con tablas, con reinicio obligado): `journalctl -b -1 -k` muestra `GPU HANG: ecode 12:1:8796fff9, in Xwayland`, seguido de `GT0: Failed to reset GuC, ret = -110`, `device wedged, needs recovery` y fallos de asignación en `kwin_wayland`. Es un fallo del driver i915, no un bucle de Python: el parser tarda 1,2 s con 2 MB y 160 000 líneas. La app era el detonante por la carga gráfica que generaba, y eso es lo que se corrige aquí. El fallo del driver debe reportarse upstream.

## [0.3.4] - 2026-10-13

### Fixed

- Posible bloqueo de la interfaz al renderizar tablas: eliminada la llamada `frame.update_idletasks()` dentro de `_insert_table`, que forzaba la negociación de geometría de Tk a mitad del renderizado (ingrediente clásico de los bucles de geometría del widget `Text` con ventanas embebidas).

### Changed

- Tablas con muchas filas: el número de filas insertadas en el `Treeview` se limita a 500 (`MAX_TABLE_ROWS`); las filas restantes se resumen en una fila final «… y N filas más». Mantiene la UI receptiva en máquinas modestas al abrir informes grandes.

### Notes

- Investigación del incidente del 2026-10-13 (congelación total del PC al abrir un informe de correo): los logs del kernel (`journalctl -b -1`) muestran un cuelgue de la GPU Intel i915 (timeouts de forcewake, fallo en el reset de GuC), no un bucle de la aplicación. La app se verificó con el mismo fichero: render estable (<0,2 s), RAM ~56 MB, CPU ~0 %.

## [0.3.3] - 2026-08-30

### Fixed

- Cierre inesperado al abrir ficheros Markdown con tablas que contienen celdas vacías o filas con distinto número de columnas (`IndexError` en `_insert_table`).
- Parser de tablas normaliza ahora el número de columnas de todas las filas para que coincidan con el encabezado.
- Rendering defensivo en `_insert_table`: acceso seguro a datos de filas y `try-except` aislado para que un error en una tabla no cierre la aplicación.

### Changed

- Script de instalación (`scripts/install_linux.sh`): el archivo `.desktop` se instala siempre en `~/.local/share/applications/` (ruta estándar XDG) independientemente del valor de `XDG_DATA_HOME`.

## [0.3.1] - 2026-07-24

### Added

- Detección automática del tema del sistema (oscuro/claro) al iniciar la aplicación en Linux, Windows y macOS.

### Changed

- El botón de cambio de tema en la barra de herramientas cambia dinámicamente su texto a "Claro" en modo oscuro y "Oscuro" en modo claro.


## [0.3.0] - 2026-07-24

### Fixed

- Solucionado bloqueo del sistema gráfico al intentar renderizar tablas anchas (causado por un bucle recursivo de cálculo geométrico en `Text` widget con `wrap="word"` + `grid`).
- Scroll horizontal funcional para todo el documento: el widget `Text` principal ahora permite desplazamiento horizontal sin causar inestabilidad.
- Refactorización del layout principal para usar `pack` en lugar de `grid`, evitando colapsos del compositor de ventanas.
- Mejora en el renderizado de bloques de código: ahora se aíslan en contenedores independientes para permitir scroll horizontal sin afectar al layout general.

---

## [0.2.1] - 2026-07-16

### Added

- Icono de la aplicación visible dentro de la ventana (barra de herramientas) y en la barra de tareas (vía `iconphoto` + `iconname` + `StartupWMClass` en el `.desktop`).
- Scripts de instalación y desinstalación para Linux (`scripts/install_linux.sh`, `scripts/uninstall_linux.sh`).
- Soporte de imágenes inline: se renderizan como enlaces clickeables con el texto alternativo.
- Soporte de tachado (`~~texto~~`): renderizado con estilo overstrike.

### Changed

- Tablas Markdown renderizadas como grid real (`ttk.Treeview`) con columnas alineadas, scroll horizontal funcional y ancho máximo de columna fijado a 480px.
- Tablas: las celdas muestran el texto completo sin truncado; columnas redimensionables arrastrando la cabecera.
- El `.desktop` del repo y el generado por el instalador incluyen `StartupWMClass=Lightmd` para emparejar la ventana con el icono en KDE.

### Fixed

- Scroll horizontal en tablas: ahora aparece correctamente cuando las columnas exceden el ancho visible de la ventana.

### Internal

- Refactorización del parser: arquitectura modular con registro de parseadores de bloques.
- Carga segura del icono con `subsample` a ~64px (ventana) y ~28px (toolbar), protegida con `try/except tk.TclError`.
- Eliminada llamada inexistente `wm class` que rompía el arranque en Tk 8.6; reemplazada por `iconname("lightmd")`.
- Separación del parser Markdown a `src/lightmd/parser.py` para testeo sin Tkinter.
