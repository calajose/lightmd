#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Resolve paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BASE="${XDG_DATA_HOME:-$HOME/.local/share}/lightmd"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps"
VENV="$BASE/venv"
DESKTOP_FILE="$APP_DIR/lightmd.desktop"

# --- Prerequisites ---
info "Comprobando requisitos..."

command -v python3 >/dev/null 2>&1 \
    || { error "python3 no está instalado."; exit 1; }

pyver="$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)"
major="${pyver%.*}"
minor="${pyver#*.}"
if [ "$major" -eq 3 ] && [ "$minor" -lt 8 ] 2>/dev/null; then
    error "Se requiere Python >= 3.8 (actual: $(python3 --version))"
    exit 1
fi

python3 -m venv --help >/dev/null 2>&1 || {
    error "El módulo 'venv' de Python no está disponible."
    command -v apt >/dev/null 2>&1 \
        && echo "  En Debian/antiX/Ubuntu: sudo apt install python3-venv"
    command -v pacman >/dev/null 2>&1 \
        && echo "  En Arch/CachyOS: sudo pacman -S python"
    exit 1
}

# --- Create directories ---
mkdir -p "$BASE" "$APP_DIR" "$ICON_DIR"

# --- Venv (idempotent) ---
if [ ! -f "$VENV/bin/python" ]; then
    info "Creando entorno virtual en $VENV..."
    python3 -m venv "$VENV"
else
    info "Entorno virtual ya existe."
fi

# --- Ensure build tools inside venv ---
"$VENV/bin/pip" install --upgrade pip setuptools wheel 2>/dev/null \
    || warn "No se pudieron actualizar pip/setuptools/wheel (posiblemente sin conexión)"

# --- Install / upgrade project ---
info "Instalando LightMD en el entorno virtual..."

if "$VENV/bin/pip" install --upgrade --no-build-isolation "$PROJECT_DIR" 2>/dev/null; then
    # succeeded with local build tools
    true
elif "$VENV/bin/pip" install --upgrade "$PROJECT_DIR" 2>/dev/null; then
    info "Usado build isolation (descarga de dependencias de build)."
else
    error "Falló la instalación con pip."
    echo ""
    echo "  Posibles causas y soluciones:"
    echo "    1. Sin conexión a internet → instala dependencias de build manualmente:"
    echo "       $VENV/bin/pip install setuptools wheel"
    echo "       $VENV/bin/pip install --no-build-isolation --upgrade $PROJECT_DIR"
    echo ""
    echo "    2. Falta el paquete python3-venv → instálalo con tu gestor de paquetes."
    exit 1
fi

# --- Verify binary ---
BIN="$VENV/bin/lightmd"
if [ ! -f "$BIN" ]; then
    error "No se encontró el comando 'lightmd' en $BIN."
    error "La instalación de pip pudo fallar silenciosamente. Revisa los mensajes anteriores."
    exit 1
fi

# --- Icon ---
SOURCE_ICON="$PROJECT_DIR/src/lightmd/resources/lightmd.png"
if [ -f "$SOURCE_ICON" ]; then
    cp "$SOURCE_ICON" "$ICON_DIR/lightmd.png"
    ICON_NAME="lightmd"
    info "Icono copiado a $ICON_DIR/lightmd.png"
else
    ICON_NAME="text-x-markdown"
    warn "No se encontró lightmd.png. Usando icono genérico."
fi

# --- Desktop file ---
cat > "$DESKTOP_FILE" << DESKTOP_EOF
[Desktop Entry]
Name=LightMD
Comment=Visor Markdown ligero
Exec=$BIN %f
Icon=$ICON_NAME
Terminal=false
Type=Application
Categories=Office;Utility;Viewer;
MimeType=text/markdown;text/plain;
StartupWMClass=Lightmd
StartupNotify=true
DESKTOP_EOF
chmod 644 "$DESKTOP_FILE"
info "Lanzador creado: $DESKTOP_FILE"

# --- Update desktop database ---
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR"
    info "Base de datos de escritorio actualizada."
else
    warn "update-desktop-database no disponible. Ignorando (sigue funcionando)."
fi

echo ""
info "¡Instalación completada!"
echo "  Ejecuta:  $BIN"
echo "  O desde el menú de aplicaciones como 'LightMD'."
