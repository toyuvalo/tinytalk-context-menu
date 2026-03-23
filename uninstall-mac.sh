#!/usr/bin/env bash
# TinyTalk — macOS uninstaller
set -euo pipefail

INSTALL_DIR="$HOME/Library/Application Support/TinyTalk"
WORKFLOW="$HOME/Library/Services/Transcribe with TinyTalk.workflow"

echo ""
echo " ================================"
echo "   TinyTalk  —  macOS Uninstall"
echo " ================================"
echo ""

if [ -d "$WORKFLOW" ]; then
    rm -rf "$WORKFLOW"
    echo "✓  Removed Quick Action"
else
    echo "   Quick Action not found (already removed?)"
fi

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "✓  Removed $INSTALL_DIR"
else
    echo "   Install dir not found (already removed?)"
fi

/System/Library/CoreServices/pbs -update 2>/dev/null || true

echo ""
echo "   Done. Whisper model cache is kept at:"
echo "   ~/.cache/huggingface/hub/"
echo "   Delete that folder manually to reclaim disk space."
echo ""
