"""
transcribe-menu — right-click Whisper transcription
Usage: transcribe.py <audio_or_video_file>
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import font as tkfont

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_SIZE = "base"   # tiny | base | small | medium | large-v3

# ── Palette (matches RipWave) ─────────────────────────────────────────────────
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

        self._spin_idx = 0
        self._spin_job = None

        self.title("TinyTalk")
        self.configure(bg=C_BG)
        self.resizable(False, False)

        self._build()

        W, H = 520, 420
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

        threading.Thread(target=self._run, daemon=True).start()

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
        tk.Label(meta, text=f"whisper transcriber · tinytalk  /  model: {MODEL_SIZE}",
                 font=f_tiny, bg=C_BG, fg=C_MID).pack(anchor="w")
        tk.Label(meta, text=f"→ {os.path.dirname(self.out_path)}",
                 font=f_tiny, bg=C_BG, fg=C_DIM).pack(anchor="w")

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28, pady=(18, 0))
        tk.Frame(self, bg=C_BG, height=12).pack()

        # File name pill
        fname_row = tk.Frame(self, bg=C_BG, padx=28)
        fname_row.pack(fill="x")
        fname_bg = tk.Frame(fname_row, bg=C_CARD, padx=10, pady=5)
        fname_bg.pack(side="left")
        tk.Label(fname_bg, text=self.fname, font=f_file,
                 bg=C_CARD, fg=C_TEXT).pack(side="left")

        tk.Frame(self, bg=C_BG, height=12).pack()
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28)
        tk.Frame(self, bg=C_BG, height=8).pack()

        # Status row
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

        # Transcript log
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

        # Bottom row (open button, hidden until done)
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
        # hidden until done

    # ── Transcription ─────────────────────────────────────────────────────────

    def _run(self):
        self._start_spin()
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            self.after(0, self._err, "faster-whisper not installed.\nRun install.bat to set up dependencies.")
            return

        try:
            self.after(0, self._set_status, "loading model...", C_YELLOW)
            model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

            self.after(0, self._set_status, "transcribing...", C_YELLOW)
            segments, info = model.transcribe(self.file_path, beam_size=5)

            lang = info.language.upper() if info.language else "?"
            self.after(0, self._set_status, f"transcribing  [{lang}]  ...", C_YELLOW)

            lines = []
            for seg in segments:
                text = seg.text.strip()
                if text:
                    lines.append(text)
                    self.after(0, self._append_log, text, "text")

            # Write output file
            with open(self.out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self.after(0, self._done, lang)

        except Exception as exc:
            self.after(0, self._err, str(exc))

    def _done(self, lang):
        self._stop_spin()
        self._append_log(f"\n✓  saved to: {os.path.basename(self.out_path)}", "ok")
        self._set_status(f"✓  done  [{lang}]  →  {os.path.basename(self.out_path)}", C_SUCCESS)
        self.open_btn.pack(side="left")

    def _err(self, msg):
        self._stop_spin()
        self._append_log(f"✗  {msg}", "err")
        self._set_status("something went wrong", C_ERROR)

    def _open_file(self):
        os.startfile(self.out_path)

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
        print("Usage: transcribe.py <file>")
        sys.exit(1)
    app = App(sys.argv[1])
    app.mainloop()
