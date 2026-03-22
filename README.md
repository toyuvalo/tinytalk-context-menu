# TinyTalk Context Menu

**Right-click any audio or video file → Transcribe with TinyTalk**

Adds a Windows context menu item to every audio and video file. One click runs local [Whisper](https://github.com/SYSTRAN/faster-whisper) transcription — no internet required after setup, no API key, nothing uploaded anywhere. Transcript saved as `.txt` right next to the source file.

---

## Install

Download **`TinyTalk_Setup.exe`** from the [latest release](../../releases/latest) and run it.

The installer will:
1. Locate Python on your system
2. Install `faster-whisper`
3. Copy files to `%LOCALAPPDATA%\TinyTalk\`
4. Register the right-click menu for all audio and video file types

> First transcription downloads the Whisper `base` model (~150 MB). All subsequent runs are instant.

---

## Usage

1. Right-click any `.mp3`, `.wav`, `.mp4`, `.mkv`, `.m4a`, `.flac`, `.mov`, etc.
2. Click **Transcribe with TinyTalk**
3. Watch the transcript stream in live, segment by segment
4. Hit **Open Transcript** when done — `.txt` saved right next to your file

---

## Model sizes

Edit `MODEL_SIZE` at the top of `tinytalk.py` to trade speed for accuracy:

| Model | Size | Speed |
|-------|------|-------|
| `tiny` | 75 MB | fastest |
| `base` | 150 MB | **default** |
| `small` | 500 MB | medium |
| `medium` | 1.5 GB | slow |
| `large-v3` | 3 GB | best quality |

---

## Uninstall

Run `uninstall.bat` to remove context menu entries.

---

## Build from source

```bash
build.bat
```

Outputs `dist/TinyTalk_Setup.exe`.
