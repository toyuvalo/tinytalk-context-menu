#!/usr/bin/env bash
# TinyTalk — macOS installer
# Registers a Finder Quick Action for audio + video files.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$HOME/Library/Application Support/TinyTalk"
SERVICE_DIR="$HOME/Library/Services"
WORKFLOW="$SERVICE_DIR/Transcribe with TinyTalk.workflow"

echo ""
echo " ================================"
echo "   TinyTalk  —  macOS Setup"
echo " ================================"
echo ""

# ── Python ────────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "✗  Python 3 not found. Install from https://python.org"
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
        $PY -m pip install "$pkg" --quiet
        echo "✓  installed: $pkg"
    fi
done
echo ""

# ── ffmpeg ────────────────────────────────────────────────────────────────────
if command -v ffmpeg &>/dev/null; then
    echo "✓  ffmpeg: $(command -v ffmpeg)"
else
    if command -v brew &>/dev/null; then
        echo "   Installing ffmpeg via Homebrew..."
        brew install ffmpeg --quiet
        echo "✓  ffmpeg installed"
    else
        echo "✗  ffmpeg not found and Homebrew is not installed."
        echo "   Install Homebrew first: https://brew.sh"
        echo "   Then run:  brew install ffmpeg"
        echo "   Then re-run this script."
        exit 1
    fi
fi
echo ""

# ── App files ─────────────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/tinytalk.py" "$INSTALL_DIR/tinytalk.py"
echo "✓  Copied tinytalk.py → $INSTALL_DIR"

# Thin launcher script (keeps the workflow XML simple and path-agnostic)
cat > "$INSTALL_DIR/run.sh" << RUNSH
#!/usr/bin/env bash
exec python3 "$INSTALL_DIR/tinytalk.py" "\$1"
RUNSH
chmod +x "$INSTALL_DIR/run.sh"
echo "✓  Launcher created"
echo ""

# ── Automator Quick Action ────────────────────────────────────────────────────
echo "   Registering Finder Quick Action..."
mkdir -p "$WORKFLOW/Contents"

# Info.plist — declares service name and accepted file types
cat > "$WORKFLOW/Contents/Info.plist" << 'INFOPLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>NSServices</key>
	<array>
		<dict>
			<key>NSMenuItem</key>
			<dict>
				<key>default</key>
				<string>Transcribe with TinyTalk</string>
			</dict>
			<key>NSMessage</key>
			<string>runWorkflowAsService</string>
			<key>NSSendFileTypes</key>
			<array>
				<string>public.audio</string>
				<string>public.movie</string>
				<string>public.mpeg-4</string>
				<string>com.apple.m4a-audio</string>
				<string>public.mp3</string>
				<string>public.aifc-audio</string>
				<string>com.microsoft.waveform-audio</string>
				<string>org.xiph.flac</string>
			</array>
		</dict>
	</array>
</dict>
</plist>
INFOPLIST

# document.wflow — "Run Shell Script" action, passes files as arguments
# Note: & must be &amp; inside plist XML
ESCAPED_DIR="$(printf '%s' "$INSTALL_DIR" | sed 's/&/\&amp;/g')"

cat > "$WORKFLOW/Contents/document.wflow" << WFLOW
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>521</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>for f in "\$@"; do
    "$ESCAPED_DIR/run.sh" "\$f" &amp;
done</string>
					<key>shell</key>
					<string>/bin/bash</string>
					<key>source</key>
					<string>pass-as-arguments</string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.automator.runShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>UUID</key>
				<string>AA11BB22-CC33-DD44-EE55-TINYTALK0001</string>
				<key>isViewVisible</key>
				<true/>
			</dict>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
WFLOW

echo "✓  Quick Action → $WORKFLOW"

# Flush the Services database so Finder picks it up without a reboot
/System/Library/CoreServices/pbs -update 2>/dev/null || true

echo ""
echo " ================================"
echo "   Done!"
echo " ================================"
echo ""
echo "   Right-click any audio or video file in Finder"
echo "   → Quick Actions → Transcribe with TinyTalk"
echo ""
echo "   If the option doesn't appear:"
echo "   System Settings → Privacy & Security → Extensions"
echo "   → Added Extensions → Finder → enable TinyTalk"
echo ""
