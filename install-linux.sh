#!/usr/bin/env bash
# TinyTalk — Linux installer
# Registers right-click entry for GNOME/Nautilus and KDE/Dolphin.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/.local/share/TinyTalk"

echo ""
echo " ================================"
echo "   TinyTalk  —  Linux Setup"
echo " ================================"
echo ""

# ── Python ────────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "✗  Python 3 not found."
    echo "   Ubuntu/Debian:  sudo apt install python3 python3-pip"
    echo "   Fedora:         sudo dnf install python3 python3-pip"
    exit 1
fi
PY="$(command -v python3)"
echo "✓  Python $($PY --version 2>&1 | awk '{print $2}')  →  $PY"
echo ""

# ── pip packages ──────────────────────────────────────────────────────────────
PKGS=(faster-whisper resemblyzer scikit-learn noisereduce soundfile)
for pkg in "${PKGS[@]}"; do
    if $PY -m pip show "$pkg" &>/dev/null 2>&1; then
        echo "   already installed: $pkg"
    else
        echo "   installing: $pkg"
        $PY -m pip install "$pkg" --quiet --break-system-packages 2>/dev/null \
            || $PY -m pip install "$pkg" --quiet
        echo "✓  installed: $pkg"
    fi
done
echo ""

# ── ffmpeg ────────────────────────────────────────────────────────────────────
if command -v ffmpeg &>/dev/null; then
    echo "✓  ffmpeg: $(command -v ffmpeg)"
else
    echo "   ffmpeg not found — attempting install..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ffmpeg
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm ffmpeg
    elif command -v snap &>/dev/null; then
        sudo snap install ffmpeg
    else
        echo "✗  Cannot install ffmpeg automatically."
        echo "   Please install it manually and re-run this script."
        exit 1
    fi
    echo "✓  ffmpeg installed"
fi
echo ""

# ── App files ─────────────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/tinytalk.py" "$INSTALL_DIR/tinytalk.py"
echo "✓  Copied tinytalk.py → $INSTALL_DIR"
echo ""

# ── GNOME / Nautilus ──────────────────────────────────────────────────────────
NAUTILUS_SCRIPTS="$HOME/.local/share/nautilus/scripts"
mkdir -p "$NAUTILUS_SCRIPTS"

cat > "$NAUTILUS_SCRIPTS/Transcribe with TinyTalk" << NSCRIPT
#!/usr/bin/env bash
# Nautilus passes selected files via env var (newline-separated)
IFS=\$'\n'
for f in \$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    [ -z "\$f" ] && continue
    python3 "$INSTALL_DIR/tinytalk.py" "\$f" &
done
NSCRIPT
chmod +x "$NAUTILUS_SCRIPTS/Transcribe with TinyTalk"
echo "✓  GNOME/Nautilus script registered"
echo "   Scripts menu: right-click file → Scripts → Transcribe with TinyTalk"

# ── KDE / Dolphin ─────────────────────────────────────────────────────────────
# Support both Plasma 5 and Plasma 6 service menu paths
DOLPHIN_DIRS=(
    "$HOME/.local/share/kservices5/ServiceMenus"
    "$HOME/.local/share/kio/servicemenus"
)
for DOLPHIN_DIR in "${DOLPHIN_DIRS[@]}"; do
    mkdir -p "$DOLPHIN_DIR"
    cat > "$DOLPHIN_DIR/tinytalk.desktop" << DESKTOP
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=audio/*;video/*;
Actions=tinytalk_transcribe;
X-KDE-Priority=TopLevel

[Desktop Action tinytalk_transcribe]
Name=Transcribe with TinyTalk
Icon=audio-x-generic
Exec=python3 $INSTALL_DIR/tinytalk.py %f
DESKTOP
done
echo "✓  KDE/Dolphin service menu registered (Plasma 5 + 6)"

echo ""
echo " ================================"
echo "   Done!"
echo " ================================"
echo ""
echo "   GNOME: right-click audio/video → Scripts → Transcribe with TinyTalk"
echo "   KDE:   right-click audio/video → Transcribe with TinyTalk"
echo ""
echo "   Note: Restart Nautilus or Dolphin if the menu doesn't appear:"
echo "     nautilus -q   (GNOME)"
echo "     kbuildsycoca6 --noincremental   (KDE Plasma 6)"
echo "     kbuildsycoca5 --noincremental   (KDE Plasma 5)"
echo ""
