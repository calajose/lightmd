#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

BASE="${XDG_DATA_HOME:-$HOME/.local/share}/lightmd"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_FILE="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/256x256/apps/lightmd.png"
DESKTOP_FILE="$APP_DIR/lightmd.desktop"

info "Desinstalando LightMD..."

[ ! -d "$BASE" ] && [ ! -f "$DESKTOP_FILE" ] && [ ! -f "$ICON_FILE" ] && {
    info "No se encontró ninguna instalación de LightMD. Nada que hacer."
    exit 0
}

if [ -d "$BASE" ]; then
    rm -rf "$BASE"
    info "Eliminado: $BASE"
fi

if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    info "Eliminado: $DESKTOP_FILE"
fi

if [ -f "$ICON_FILE" ]; then
    rm -f "$ICON_FILE"
    info "Eliminado: $ICON_FILE"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR"
    info "Base de datos de escritorio actualizada."
fi

info "LightMD ha sido desinstalado."
