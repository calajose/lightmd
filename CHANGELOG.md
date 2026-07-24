# Changelog

All notable changes to LightMD Viewer will be documented in this file.

The format is based on [Keep a Changelog][keepachangelog],
and this project adheres to [Semantic Versioning][semver].

[keepachangelog]: https://keepachangelog.com/
[semver]: https://semver.org/

## [Unreleased]

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
