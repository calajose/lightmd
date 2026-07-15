# AGENTS.md — LightMD Viewer

Instrucciones permanentes para agentes que trabajen en este repositorio.

---

## Objetivo del proyecto

LightMD Viewer es un visor Markdown ligero y multiplataforma construido
con Python y Tkinter. Está diseñado para equipos modestos, sistemas
Linux de 32 bits, y cualquier entorno donde se prefiera una herramienta
simple e instantánea frente a soluciones pesadas basadas en Electron.

## Filosofía

- **Ligereza y velocidad ante todo.** El arranque debe ser casi
  instantáneo; el consumo de RAM debe minimizarse.
- **Sin Electron, sin navegadores embebidos, sin dependencias pesadas.**
  Se prefiere la biblioteca estándar de Python siempre que sea posible.
- **Cero dependencias runtime instalables.** Tkinter se documenta como
  requisito del sistema operativo, no como dependencia pip.
- **Mantener Tkinter mientras sea suficiente.** Solo se considerará un
  reemplazo si Tkinter impide funcionalidades esenciales, y con una
  justificación fuerte.
- **Preferir código claro y directo** sobre abstracciones innecesarias.

## Compatibilidad (requisitos duros)

- **Python 3.8 mínimo.** Usar `from __future__ import annotations` en
  todos los módulos. No usar sintaxis exclusiva de Python 3.9+
  (ej. `list[str]` sin `from __future__ import annotations`, `|` para
  uniones de tipos como argumentos de función, etc.). Las anotaciones
  diferidas con `from __future__ import annotations` hacen válidas
  las sintaxis modernas en 3.8 siempre que no se evalúen en runtime.
- **Linux de 32 bits, Linux moderno y Windows.**
- **No asumir硬件 potente:** la aplicación debe funcionar en pantallas
  pequeñas, resolución baja y sin aceleración gráfica.

## Estructura del proyecto

```
lightmd/
├── src/lightmd/
│   ├── __init__.py         # __version__, reexporta MarkdownViewer y main
│   ├── __main__.py         # python -m lightmd
│   ├── cli.py              # entry point de consola (argparse)
│   ├── viewer.py           # GUI Tkinter + render Markdown actual
│   ├── parser.py           # parseo Markdown puro y testeable
│   └── resources/
│       ├── lightmd.desktop # lanzador .desktop empaquetado
│       └── lightmd.png     # icono de la aplicación
├── scripts/
│   ├── install_linux.sh    # instalador de usuario (venv + lanzador)
│   └── uninstall_linux.sh  # desinstalador
├── tests/
│   └── test_viewer.py      # pruebas de regex y CLI sin Tk
├── lightmd_viewer.py       # shim de compatibilidad heredado
├── pyproject.toml          # build setuptools, entry point, pytest config
├── AGENTS.md               # este archivo
├── README.md
├── LICENSE                 # MIT
├── CHANGELOG.md            # cambios por versión (Keep a Changelog + SemVer)
└── .gitignore
```

## Responsabilidades por módulo

### `cli.py`
- Punto de entrada principal (`lightmd` en `[project.scripts]`).
- Usa `argparse` con argumento posicional `file` opcional y `--version`.
- Llama a `MarkdownViewer(args.file).mainloop()`.
- No contiene lógica de negocio ni de GUI.

### `viewer.py`
- Clase `MarkdownViewer(tk.Tk)`: ventana, menús, atajos, temas, barra de
  búsqueda.
- **Contiene hoy también la lógica de render Markdown**:
  `render_markdown()`, `_insert_inline()`, y las constantes de regex
  (`RE_HR`, `RE_HEADING`, `RE_QUOTE`, `RE_TASK`, `RE_UNORDERED`,
  `RE_ORDERED`, `RE_TOKEN`) como atributos de clase.
- La prioridad a futuro es extraer el parseo a `parser.py` para que sea
  testeable sin Tkinter.

### `parser.py`
- Módulo de parseo Markdown puro, sin dependencia de Tkinter.
- Recibe texto Markdown como `str` y devuelve `List[Block]` de tipos
  `dataclass` sencillos (`Block`, `InlineNode`).
- `parse_markdown()` es la función principal; `parse_inline()` procesa
  tokens en línea (negrita, cursiva, código, enlaces).
- Regex precompiladas como constantes de módulo (`RE_HR`, `RE_HEADING`,
  `RE_QUOTE`, `RE_TASK`, `RE_UNORDERED`, `RE_ORDERED`, `RE_TOKEN`).
- Puramente testeable con pytest sin display. No importa Tkinter.

### `resources/`
- Archivos de datos empaquetados con setuptools (`[tool.setuptools.package-data]`).
- `lightmd.desktop`: lanzador Freedesktop con `Exec=lightmd %f`.
- `lightmd.png`: icono de la aplicación.

## Estilo de código

- **Sin comentarios superfluos.** El código debe ser autoexplicativo con
  nombres de variables, funciones y clases claros.
- **Type hints obligatorios** en todos los parámetros y valores de retorno
  de funciones y métodos públicos.
- **`from __future__ import annotations`** en todos los módulos.
- **Regex precompiladas como constantes** de clase o módulo, nunca
  recompiladas en cada llamada.
- **Seguir el estilo existente:** indentación 4 espacios, líneas ~100
  caracteres, comillas dobles para docstrings, comillas simples para
  strings cortos.
- No introducir dependencias externas sin aprobación explícita.

## Tests

- Framework: **pytest**.
- Los tests deben ejecutarse **sin display gráfico** (sin instanciar Tk).
  La lógica de parseo se prueba a través de las constantes regex y
  funciones exportadas.
- **Cubrir:** importación del paquete, versión, patrones regex de
  Markdown (HR, headings, quotes, tasks, listas, inline tokens), y CLI
  (`--version`, argumento posicional).
- **Ejecutar `pytest` después de cada cambio relevante** y mantener
  todos los tests en verde. Si un cambio requiere modificar un test,
  actualizarlo en el mismo commit.
- Compatibilidad con Python 3.8 debe verificarse periódicamente.

## Documentación

- **README.md:** reflejar cambios en uso, instalación, CLI o
  dependencias. Mantener ejemplos actualizados.
- **CHANGELOG.md:** seguir el formato [Keep a Changelog][keepachangelog]
  y usar [SemVer][semver] para versionado. Documentar todo cambio
  relevante: añadidos, cambios, correcciones y deprecaciones. Si el
  archivo no existe, crearlo al hacer el primer cambio relevante.

[keepachangelog]: https://keepachangelog.com/
[semver]: https://semver.org/

## Reglas de trabajo para agentes

1. **No hacer commits ni push automáticamente.** Solo cuando el usuario
   lo solicite explícitamente.
2. **No modificar archivos ajenos a la tarea.** Limitarse estrictamente
   a los archivos necesarios para completar la instrucción recibida.
3. **Ejecutar `pytest` después de cada cambio relevante.** Verificar que
   todo siga en verde antes de dar una tarea por terminada.
4. **No introducir dependencias pip sin aprobación explícita del usuario.**
   Tkinter se documenta, no se instala.
5. **Preservar la compatibilidad con Python 3.8** en todo momento.

---

Última actualización: 2026-07-15
