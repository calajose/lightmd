# Changelog

All notable changes to LightMD Viewer will be documented in this file.

The format is based on [Keep a Changelog][keepachangelog],
and this project adheres to [Semantic Versioning][semver].

[keepachangelog]: https://keepachangelog.com/
[semver]: https://semver.org/

## [Unreleased]

### Added

- Linux installer script (`scripts/install_linux.sh`) — creates a private
  virtual environment, installs LightMD, and places a desktop launcher
  with MIME association.
- Linux uninstaller script (`scripts/uninstall_linux.sh`).
- Application icon (`src/lightmd/resources/lightmd.png`).
- Soporte de tablas Markdown: parseo y renderizado como texto.
- Soporte de imágenes inline: se renderizan como enlaces clickeables con el texto alternativo.
- Soporte de tachado (`~~texto~~`): renderizado con estilo overstrike.
- Refactorización del parser: arquitectura modular con registro de parseadores de bloques.
- Tablas Markdown renderizadas como un grid real (`ttk.Treeview`) con columnas alineadas y celdas truncadas a 40 caracteres.
- Tablas: el texto de las celdas se muestra completo (sin truncado); las columnas son redimensionables arrastrando la cabecera; ancho máximo de columna fijado a 480px con scroll horizontal.
- Tablas: la última columna (p. ej. "Explicación") se renderiza sin tope de ancho, mostrando el texto completo; el resto mantiene 480px.
