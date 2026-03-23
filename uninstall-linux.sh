#!/usr/bin/env bash
# TinyTalk — Linux uninstaller
set -euo pipefail

INSTALL_DIR="$HOME/.local/share/TinyTalk"
NAUTILUS_SCRIPT="$HOME/.local/share/nautilus/scripts/Transcribe with TinyTalk"
DOLPHIN5="$HOME/.local/share/kservices5/ServiceMenus/tinytalk.desktop"
DOLPHIN6="$HOME/.local/share/kio/servicemenus/tinytalk.desktop"

echo ""
echo " ================================"
echo "   TinyTalk  —  Linux Uninstall"
echo " ================================"
echo ""

[ -d "$INSTALL_DIR" ]       && rm -rf "$INSTALL_DIR"       && echo "✓  Removed install dir"
[ -f "$NAUTILUS_SCRIPT" ]   && rm -f  "$NAUTILUS_SCRIPT"   && echo "✓  Removed Nautilus script"
[ -f "$DOLPHIN5" ]          && rm -f  "$DOLPHIN5"          && echo "✓  Removed KDE Plasma 5 service menu"
[ -f "$DOLPHIN6" ]          && rm -f  "$DOLPHIN6"          && echo "✓  Removed KDE Plasma 6 service menu"

echo ""
echo "   Done. Whisper model cache is kept at:"
echo "   ~/.cache/huggingface/hub/"
echo "   Delete that folder manually to reclaim disk space."
echo ""
