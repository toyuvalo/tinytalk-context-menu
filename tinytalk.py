"""
TinyTalk — right-click Whisper transcription
Usage: tinytalk.py <audio_or_video_file>
"""
import sys
import os
import threading
import subprocess
import shutil
import urllib.request
import json
import tkinter as tk
from tkinter import font as tkfont, ttk

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_SIZE   = "base"      # tiny | base | small | medium | large-v3
COMPUTE_TYPE = "default"   # default lets CTranslate2 pick; int8 hangs on some CPUs
MODEL_REPO   = f"Systran/faster-whisper-{MODEL_SIZE}"
MODEL_CACHE  = os.path.join(os.path.expanduser("~"), ".cache", "huggingface",
                            "hub", f"models--Systran--faster-whisper-{MODEL_SIZE}")
MODEL_REFS   = os.path.join(MODEL_CACHE, "refs", "main")

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG      = "#090909"
C_CARD    = "#101010"
C_BORDER  = "#1f1f1f"
C_ACCENT  = "#00d9d9"
C_TEXT    = "#f0f0f0"
C_DIM     = "#3a3a3a"
C_MID     = "#666666"
C_SUCCESS = "#00e87a"
C_ERROR   = "#ff4444"
C_YELLOW  = "#ffc400"

SPIN_FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]


class App(tk.Tk):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.out_path  = os.path.splitext(file_path)[0] + ".txt"
        self.fname     = os.path.basename(file_path)

        self._spin_idx  = 0
        self._spin_job  = None
        self._done_evt  = threading.Event()   # set when transcription finishes

        self.title("TinyTalk")
        self.configure(bg=C_BG)
        self.resizable(False, False)

        self._build()

        W, H = 520, 420
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

        # Transcription and background model update run concurrently
        threading.Thread(target=self._run,                daemon=True).start()
        threading.Thread(target=self._check_model_update, daemon=True).start()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        f_title  = tkfont.Font(family="Consolas", size=22, weight="bold")
        f_tiny   = tkfont.Font(family="Consolas", size=7)
        f_file   = tkfont.Font(family="Consolas", size=9)
        f_log    = tkfont.Font(family="Consolas", size=8)
        f_status = tkfont.Font(family="Consolas", size=8)
        f_btn    = tkfont.Font(family="Consolas", size=9, weight="bold")

        tk.Frame(self, bg=C_BG, height=26).pack()

        hdr = tk.Frame(self, bg=C_BG, padx=28)
        hdr.pack(fill="x")
        tk.Label(hdr, text="TinyTalk", font=f_title, bg=C_BG, fg=C_ACCENT).pack(side="left")

        meta = tk.Frame(hdr, bg=C_BG)
        meta.pack(side="left", padx=(12, 0), pady=(8, 0))
        tk.Label(meta, text=f"whisper transcriber  /  model: {MODEL_SIZE}",
                 font=f_tiny, bg=C_BG, fg=C_MID).pack(anchor="w")
        tk.Label(meta, text=f"→ {os.path.dirname(self.out_path)}",
                 font=f_tiny, bg=C_BG, fg=C_DIM).pack(anchor="w")

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28, pady=(18, 0))
        tk.Frame(self, bg=C_BG, height=12).pack()

        fname_row = tk.Frame(self, bg=C_BG, padx=28)
        fname_row.pack(fill="x")
        fname_bg = tk.Frame(fname_row, bg=C_CARD, padx=10, pady=5)
        fname_bg.pack(side="left")
        tk.Label(fname_bg, text=self.fname, font=f_file,
                 bg=C_CARD, fg=C_TEXT).pack(side="left")

        tk.Frame(self, bg=C_BG, height=12).pack()
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28)
        tk.Frame(self, bg=C_BG, height=8).pack()

        status_row = tk.Frame(self, bg=C_BG, padx=28)
        status_row.pack(fill="x")

        self.spin_var   = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="loading model...")

        tk.Label(status_row, textvariable=self.spin_var,
                 font=f_status, bg=C_BG, fg=C_ACCENT,
                 width=2, anchor="w").pack(side="left")
        self.status_lbl = tk.Label(status_row, textvariable=self.status_var,
                                   font=f_status, bg=C_BG, fg=C_YELLOW, anchor="w")
        self.status_lbl.pack(side="left", fill="x", expand=True)

        tk.Frame(self, bg=C_BG, height=6).pack()

        # Progress bar
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TinyTalk.Horizontal.TProgressbar",
                        troughcolor=C_CARD, background=C_ACCENT,
                        bordercolor=C_BG, lightcolor=C_ACCENT, darkcolor=C_ACCENT)
        self.progress = ttk.Progressbar(
            self,
            style="TinyTalk.Horizontal.TProgressbar",
            mode="indeterminate",
            length=100,
        )
        self.progress.pack(fill="x", padx=28)
        self.progress.start(12)

        tk.Frame(self, bg=C_BG, height=6).pack()

        log_wrap = tk.Frame(self, bg=C_BG, padx=28)
        log_wrap.pack(fill="both", expand=True)

        self.log = tk.Text(
            log_wrap,
            font=f_log,
            bg=C_CARD, fg=C_MID,
            relief="flat", bd=0,
            padx=10, pady=8,
            wrap="word",
            state="disabled",
        )
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",   foreground=C_SUCCESS)
        self.log.tag_config("err",  foreground=C_ERROR)
        self.log.tag_config("text", foreground=C_TEXT)
        self.log.tag_config("dim",  foreground=C_DIM)

        self.bottom = tk.Frame(self, bg=C_BG, padx=28)
        self.bottom.pack(fill="x", pady=(10, 20))

        self.open_btn = tk.Button(
            self.bottom,
            text="OPEN TRANSCRIPT  ↗",
            font=f_btn,
            bg=C_ACCENT, fg="#000000",
            activebackground="#00b8b8", activeforeground="#000000",
            relief="flat", bd=0, padx=16, pady=8,
            cursor="hand2",
            command=self._open_file,
        )

    # ── Transcription ─────────────────────────────────────────────────────────

    def _run(self):
        self._start_spin()
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            self.after(0, self._err, "faster-whisper not installed — run the installer again.")
            return

        try:
            # Wipe any broken partial download before trying to load
            if os.path.exists(MODEL_CACHE):
                incomplete = [
                    f for root, _, files in os.walk(MODEL_CACHE)
                    for f in files if f.endswith(".incomplete")
                ]
                if incomplete:
                    shutil.rmtree(MODEL_CACHE)
                    self.after(0, self._append_log,
                               "Cleared broken cache, re-downloading model...", "dim")

            if os.path.exists(MODEL_CACHE):
                self.after(0, self._set_status, f"loading model ({MODEL_SIZE})...", C_YELLOW)
            else:
                self.after(0, self._set_status,
                           f"downloading model ({MODEL_SIZE}, ~300 MB, one time only)...", C_YELLOW)
                self.after(0, self._append_log,
                           "Downloading Whisper model — this only happens once.", "dim")

            model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)

            self.after(0, self._set_status, "transcribing...", C_YELLOW)
            segments, info = model.transcribe(self.file_path, beam_size=5)

            lang = info.language.upper() if info.language else "?"
            duration = info.duration or 1
            self.after(0, self._set_status, f"transcribing  [{lang}]  ...", C_YELLOW)

            # Switch progress bar to determinate now that we know the duration
            self.after(0, self._progress_start_determinate)

            import time as _time
            t_start = _time.monotonic()

            lines = []
            for seg in segments:
                text = seg.text.strip()
                if text:
                    lines.append(text)
                    self.after(0, self._append_log, text, "text")
                pct = min(seg.end / duration * 100, 99)
                self.after(0, self._progress_set, pct)

                # ETA: based on measured speed so far (self-corrects as it runs)
                elapsed = _time.monotonic() - t_start
                if elapsed > 1 and seg.end > 0:
                    speed = seg.end / elapsed          # audio-seconds per wall-second
                    remaining = (duration - seg.end) / speed
                    if remaining >= 60:
                        eta_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                    else:
                        eta_str = f"{int(remaining)}s"
                    self.after(0, self._set_status,
                               f"transcribing  [{lang}]  ~{eta_str} left", C_YELLOW)

            with open(self.out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self.after(0, self._done, lang)

        except Exception as exc:
            self.after(0, self._err, str(exc))

    def _done(self, lang):
        self._stop_spin()
        self._progress_set(100)
        self._append_log(f"\n✓  saved to: {os.path.basename(self.out_path)}", "ok")
        self._set_status(f"✓  done  [{lang}]  →  {os.path.basename(self.out_path)}", C_SUCCESS)
        self.open_btn.pack(side="left")
        self._done_evt.set()

    def _err(self, msg):
        self._stop_spin()
        self.progress.stop()
        self._append_log(f"✗  {msg}", "err")
        self._set_status("something went wrong", C_ERROR)
        self._done_evt.set()

    def _open_file(self):
        os.startfile(self.out_path)

    # ── Background model update ───────────────────────────────────────────────

    def _check_model_update(self):
        """Silently check HuggingFace for a newer model. Download in background,
        report after transcription is done so it doesn't clutter the output."""
        try:
            # Need a clean cached model to compare against
            if not os.path.exists(MODEL_REFS):
                return
            incomplete = [f for r, _, files in os.walk(MODEL_CACHE)
                          for f in files if f.endswith(".incomplete")]
            if incomplete:
                return  # Broken cache — _run will fix it

            with open(MODEL_REFS) as f:
                local_sha = f.read().strip()

            # Hit the HuggingFace API
            req = urllib.request.Request(
                f"https://huggingface.co/api/models/{MODEL_REPO}",
                headers={"User-Agent": "tinytalk/1.0"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
            latest_sha = data.get("sha", "")

            if not latest_sha or latest_sha == local_sha:
                return  # Already up to date, say nothing

            # Update available — download while transcription runs
            python = shutil.which("pythonw") or shutil.which("python")
            proc = subprocess.run(
                [python, "-c",
                 "import os; os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';"
                 f"from faster_whisper import WhisperModel;"
                 f"WhisperModel('{MODEL_SIZE}', device='cpu', compute_type='default')"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            # Wait for transcription to finish, then show the result in the log
            self._done_evt.wait(timeout=600)

            if proc.returncode == 0:
                self.after(0, self._append_log,
                           f"\n↑  model updated ({MODEL_SIZE}) — will use next run", "ok")
            # Silent fail on error — don't distract from the transcript

        except Exception:
            pass  # No internet, timeout, etc — never interrupt the user

    # ── Progress ──────────────────────────────────────────────────────────────

    def _progress_start_determinate(self):
        self.progress.stop()
        self.progress.config(mode="determinate", maximum=100, value=0)

    def _progress_set(self, value):
        self.progress.config(mode="determinate")
        self.progress["value"] = value

    # ── Spinner ───────────────────────────────────────────────────────────────

    def _start_spin(self):
        self._spin_idx = 0
        self._tick_spin()

    def _tick_spin(self):
        self.spin_var.set(SPIN_FRAMES[self._spin_idx % len(SPIN_FRAMES)])
        self._spin_idx += 1
        self._spin_job = self.after(110, self._tick_spin)

    def _stop_spin(self):
        if self._spin_job:
            self.after_cancel(self._spin_job)
            self._spin_job = None
        self.spin_var.set("")

    # ── Log ───────────────────────────────────────────────────────────────────

    def _append_log(self, text, tag="dim"):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, msg, color):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: tinytalk.py <file>")
        sys.exit(1)
    app = App(sys.argv[1])
    app.mainloop()
