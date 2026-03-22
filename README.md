# TinyTalk Context Menu

**Right-click any audio or video file → instant local transcription**

TinyTalk adds a single right-click option to every audio and video file on Windows. It runs [OpenAI Whisper](https://github.com/SYSTRAN/faster-whisper) locally — nothing is uploaded, no API key, no cloud. The transcript lands as a `.txt` file right next to your source file.

---

## Install

Download **[TinyTalk_Setup.exe](../../releases/latest)** and run it.

The installer handles everything in one shot:

1. Locates Python on your system
2. Installs `faster-whisper`
3. Downloads the Whisper model (~150 MB, stored locally, never re-downloaded)
4. Copies files to `%LOCALAPPDATA%\TinyTalk\`
5. Registers the context menu for all audio and video file types

First transcription is instant — no waiting for downloads.

> **Requires Python 3.8+.** If not installed, the setup will prompt you.

---

## Usage

1. Right-click any audio or video file
2. Click **Transcribe with TinyTalk**
3. Transcript streams in live, segment by segment
4. Hit **Open Transcript** when done

The `.txt` file is saved in the same folder as your source file.

**Supported formats:** `.mp3` `.wav` `.m4a` `.flac` `.ogg` `.aac` `.mp4` `.mkv` `.mov` `.webm` `.avi` and more

---

## Keeps itself updated

On every run, TinyTalk silently checks HuggingFace for a newer version of the Whisper model. If one is available it downloads in the background while your file transcribes — using the current model the whole time. When the download finishes you'll see a note in the log: `↑ model updated — will use next run`.

---

## Model sizes

Edit `MODEL_SIZE` at the top of `tinytalk.py` to trade speed for accuracy:

| Model | Download | Speed | Notes |
|-------|----------|-------|-------|
| `tiny` | 75 MB | fastest | fine for clear speech |
| `base` | 150 MB | fast | **default** |
| `small` | 500 MB | medium | noticeably better accuracy |
| `medium` | 1.5 GB | slow | good for accents / music |
| `large-v3` | 3 GB | slowest | best possible |

---

## Uninstall

Run `uninstall.bat` — removes the context menu entries. Delete `%LOCALAPPDATA%\TinyTalk\` to remove all files.

---

## Build from source

```
build.bat
```

Outputs `dist/TinyTalk_Setup.exe` via PyInstaller.

---

## Requirements

- Windows 10/11
- Python 3.8+
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — installed automatically

---

## License

MIT — free to use, modify, and distribute.
