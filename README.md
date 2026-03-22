# transcribe-menu

**Right-click any audio or video file → Transcribe to TXT**

Adds a Windows context menu item to every audio and video file. One click runs local [Whisper](https://github.com/openai/whisper) transcription — no internet required after setup, no API key, nothing uploaded anywhere. Transcript saved as `.txt` right next to the source file.

---

## Install

```
install.bat
```

That's it. Downloads `faster-whisper`, registers the context menu for all audio and video file types.

> First transcription downloads the Whisper `base` model (~150 MB). All subsequent runs are instant.

---

## Usage

1. Right-click any `.mp3`, `.wav`, `.mp4`, `.mkv`, `.m4a`, `.flac`, `.mov`, etc.
2. Click **Transcribe to TXT**
3. Watch segments stream in live
4. Click **Open Transcript** when done — `.txt` saved next to your file

---

## Model sizes

Edit `MODEL_SIZE` at the top of `transcribe.py` to trade speed for accuracy:

| Model | Size | Speed | Best for |
|-------|------|-------|---------|
| `tiny` | 75 MB | fastest | quick drafts |
| `base` | 150 MB | fast | **default — good balance** |
| `small` | 500 MB | medium | better accuracy |
| `medium` | 1.5 GB | slow | high accuracy |
| `large-v3` | 3 GB | slowest | best possible |

---

## Uninstall

```
uninstall.bat
```

---

## Requirements

- Windows 10/11
- Python 3.8+
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (installed automatically)
