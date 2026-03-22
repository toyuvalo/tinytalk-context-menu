"""
TinyTalk Context Menu — Installer GUI
Builds into TinyTalk_Setup.exe via PyInstaller.
"""
import tkinter as tk
from tkinter import font as tkfont
import subprocess
import threading
import shutil
import sys
import os

# ── Install location ──────────────────────────────────────────────────────────
INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "TinyTalk")

# ── Bundled tinytalk.py (works frozen or from source) ─────────────────────────
if getattr(sys, "frozen", False):
    BUNDLE_DIR = sys._MEIPASS
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))

BUNDLED_SCRIPT = os.path.join(BUNDLE_DIR, "tinytalk.py")

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

MODEL_SIZE  = "base"
MODEL_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface",
                           "hub", f"models--Systran--faster-whisper-{MODEL_SIZE}")

STEPS = [
    "Check Python",
    "Install faster-whisper",
    "Download Whisper model",
    "Copy files",
    "Register context menu",
]


class Installer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TinyTalk — Setup")
        self.configure(bg=C_BG)
        self.resizable(False, False)

        self._spin_idx = 0
        self._spin_job = None
        self._step_labels = []
        self._step_icons  = []

        self._build()

        W, H = 460, 440
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

    def _build(self):
        f_title  = tkfont.Font(family="Consolas", size=20, weight="bold")
        f_sub    = tkfont.Font(family="Consolas", size=7)
        f_step   = tkfont.Font(family="Consolas", size=9)
        f_log    = tkfont.Font(family="Consolas", size=8)
        f_btn    = tkfont.Font(family="Consolas", size=10, weight="bold")
        f_status = tkfont.Font(family="Consolas", size=8)

        tk.Frame(self, bg=C_BG, height=26).pack()

        hdr = tk.Frame(self, bg=C_BG, padx=28)
        hdr.pack(fill="x")
        tk.Label(hdr, text="TinyTalk", font=f_title, bg=C_BG, fg=C_ACCENT).pack(side="left")
        meta = tk.Frame(hdr, bg=C_BG)
        meta.pack(side="left", padx=(12, 0), pady=(8, 0))
        tk.Label(meta, text="context menu installer",
                 font=f_sub, bg=C_BG, fg=C_MID).pack(anchor="w")
        tk.Label(meta, text=f"→ {INSTALL_DIR}",
                 font=f_sub, bg=C_BG, fg=C_DIM).pack(anchor="w")

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28, pady=(18, 0))
        tk.Frame(self, bg=C_BG, height=16).pack()

        # Step checklist
        steps_frame = tk.Frame(self, bg=C_BG, padx=36)
        steps_frame.pack(fill="x")

        for i, label in enumerate(STEPS):
            row = tk.Frame(steps_frame, bg=C_BG)
            row.pack(fill="x", pady=3)

            icon = tk.Label(row, text="○", font=f_step,
                            bg=C_BG, fg=C_DIM, width=2, anchor="w")
            icon.pack(side="left")

            lbl = tk.Label(row, text=label, font=f_step,
                           bg=C_BG, fg=C_DIM, anchor="w")
            lbl.pack(side="left")

            self._step_icons.append(icon)
            self._step_labels.append(lbl)

        tk.Frame(self, bg=C_BG, height=14).pack()
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28)
        tk.Frame(self, bg=C_BG, height=8).pack()

        # Status
        status_row = tk.Frame(self, bg=C_BG, padx=28)
        status_row.pack(fill="x")

        self.spin_var   = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="ready to install")

        tk.Label(status_row, textvariable=self.spin_var,
                 font=f_status, bg=C_BG, fg=C_ACCENT,
                 width=2, anchor="w").pack(side="left")
        self.status_lbl = tk.Label(status_row, textvariable=self.status_var,
                                   font=f_status, bg=C_BG, fg=C_MID, anchor="w")
        self.status_lbl.pack(side="left")

        tk.Frame(self, bg=C_BG, height=6).pack()

        # Log
        log_wrap = tk.Frame(self, bg=C_BG, padx=28)
        log_wrap.pack(fill="both", expand=True)

        self.log = tk.Text(
            log_wrap,
            font=f_log,
            bg=C_CARD, fg=C_DIM,
            relief="flat", bd=0,
            padx=10, pady=6,
            wrap="word",
            state="disabled",
            height=5,
        )
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",  foreground=C_SUCCESS)
        self.log.tag_config("err", foreground=C_ERROR)
        self.log.tag_config("dim", foreground=C_DIM)

        tk.Frame(self, bg=C_BG, height=12).pack()

        # Install button
        self.btn = tk.Button(
            self,
            text="INSTALL  ↓",
            font=f_btn,
            bg=C_ACCENT, fg="#000000",
            activebackground="#00b8b8", activeforeground="#000000",
            relief="flat", bd=0, pady=11,
            cursor="hand2",
            command=self._start,
        )
        self.btn.pack(fill="x", padx=28, pady=(0, 20))

    # ── Install flow ──────────────────────────────────────────────────────────

    def _start(self):
        self.btn.config(state="disabled", bg=C_DIM, fg=C_BG, text="installing...")
        self._start_spin()
        threading.Thread(target=self._run_steps, daemon=True).start()

    def _run_steps(self):
        steps = [
            self._step_check_python,
            self._step_install_whisper,
            self._step_download_model,
            self._step_copy_files,
            self._step_register_menu,
        ]
        for i, fn in enumerate(steps):
            self.after(0, self._set_step_active, i)
            ok, msg = fn()
            self.after(0, self._set_step_done, i, ok, msg)
            if not ok:
                self.after(0, self._finish, False)
                return
        self.after(0, self._finish, True)

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _step_check_python(self):
        self.after(0, self._set_status, "locating Python...", C_YELLOW)
        pythonw = shutil.which("pythonw") or shutil.which("python")
        if not pythonw:
            return False, "Python not found — install from python.org then re-run"
        self._pythonw = pythonw
        return True, pythonw

    def _step_install_whisper(self):
        self.after(0, self._set_status, "installing faster-whisper...", C_YELLOW)
        # Always use system Python — never sys.executable when frozen (that's the .exe, not Python)
        python = shutil.which("python") or shutil.which("py")
        if not python:
            return False, "Python not found"
        try:
            result = subprocess.run(
                [python, "-m", "pip", "install", "faster-whisper", "--quiet"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                return False, result.stderr.strip() or "pip install failed"
            return True, "faster-whisper installed"
        except Exception as e:
            return False, str(e)

    def _step_download_model(self):
        if os.path.exists(MODEL_CACHE):
            return True, f"whisper-{MODEL_SIZE} already cached"
        self.after(0, self._set_status, f"downloading whisper-{MODEL_SIZE} (~150 MB)...", C_YELLOW)
        python = shutil.which("python") or shutil.which("py")
        try:
            result = subprocess.run(
                [python, "-c",
                 "import os; os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';"
                 f"from faster_whisper import WhisperModel;"
                 f"WhisperModel('{MODEL_SIZE}', device='cpu', compute_type='default');"
                 "print('done')"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode != 0:
                return False, result.stderr.strip() or "model download failed"
            return True, f"whisper-{MODEL_SIZE} ready"
        except Exception as e:
            return False, str(e)

    def _step_copy_files(self):
        self.after(0, self._set_status, "copying files...", C_YELLOW)
        try:
            # Wipe any previous install so only one version ever exists
            if os.path.exists(INSTALL_DIR):
                shutil.rmtree(INSTALL_DIR)
            os.makedirs(INSTALL_DIR)

            # Copy tinytalk.py
            dst_script = os.path.join(INSTALL_DIR, "tinytalk.py")
            shutil.copy2(BUNDLED_SCRIPT, dst_script)

            # Write launch.vbs (silent launcher, no console)
            vbs_path = os.path.join(INSTALL_DIR, "launch.vbs")
            with open(vbs_path, "w") as f:
                # Use Chr(34) for every quote — avoids the double-quote bug
                # that breaks paths containing spaces (e.g. "F:\Fruity Loops\...")
                f.write(
                    'Set sh = CreateObject("WScript.Shell")\n'
                    f'sh.Run Chr(34) & "{self._pythonw}" & Chr(34)'
                    f' & " " & Chr(34) & "{dst_script}" & Chr(34)'
                    ' & " " & Chr(34) & WScript.Arguments(0) & Chr(34)'
                    ', 0, False\n'
                )

            self._dst_script = dst_script
            self._vbs_path   = vbs_path
            return True, INSTALL_DIR
        except Exception as e:
            return False, str(e)

    def _step_register_menu(self):
        self.after(0, self._set_status, "writing registry...", C_YELLOW)
        cmd = f'wscript.exe "{self._vbs_path}" "%1"'
        label = "Transcribe with TinyTalk"
        try:
            for ptype in ("audio", "video"):
                key = f"HKCU\\Software\\Classes\\SystemFileAssociations\\{ptype}\\shell\\TinyTalk"
                subprocess.run(["reg", "add", key, "/ve", "/d", label, "/f"],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(["reg", "add", f"{key}\\command", "/ve", "/d", cmd, "/f"],
                               capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True, "registered for audio + video"
        except Exception as e:
            return False, str(e)

    # ── Finish ────────────────────────────────────────────────────────────────

    def _finish(self, success):
        self._stop_spin()
        if success:
            self._set_status("✓  TinyTalk installed!", C_SUCCESS)
            self._log("Right-click any audio or video file and choose:", "ok")
            self._log('"Transcribe with TinyTalk"', "ok")
            self._log("", "dim")
            self._log("Note: first transcription downloads the Whisper", "dim")
            self._log("base model (~150 MB). Cached forever after.", "dim")
            self.btn.config(state="normal", bg=C_SUCCESS, fg="#000000",
                            text="CLOSE  ✓", cursor="hand2",
                            command=self.destroy)
        else:
            self._set_status("installation failed", C_ERROR)
            self.btn.config(state="normal", bg=C_ACCENT, fg="#000000",
                            text="RETRY  ↺", cursor="hand2",
                            command=self._start)

    # ── Step UI helpers ───────────────────────────────────────────────────────

    def _set_step_active(self, i):
        self._step_icons[i].config(text="›", fg=C_YELLOW)
        self._step_labels[i].config(fg=C_TEXT)

    def _set_step_done(self, i, ok, msg):
        if ok:
            self._step_icons[i].config(text="✓", fg=C_SUCCESS)
            self._step_labels[i].config(fg=C_SUCCESS)
            if msg:
                self._log(f"  {msg}", "dim")
        else:
            self._step_icons[i].config(text="✗", fg=C_ERROR)
            self._step_labels[i].config(fg=C_ERROR)
            self._log(f"  Error: {msg}", "err")

    # ── Spinner ───────────────────────────────────────────────────────────────

    def _start_spin(self):
        self._spin_idx = 0
        self._tick()

    def _tick(self):
        self.spin_var.set(SPIN_FRAMES[self._spin_idx % len(SPIN_FRAMES)])
        self._spin_idx += 1
        self._spin_job = self.after(110, self._tick)

    def _stop_spin(self):
        if self._spin_job:
            self.after_cancel(self._spin_job)
        self.spin_var.set("")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _log(self, text, tag="dim"):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, msg, color):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)


if __name__ == "__main__":
    app = Installer()
    app.mainloop()
