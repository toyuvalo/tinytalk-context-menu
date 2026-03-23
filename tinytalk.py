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

INSTALL_DIR  = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "TinyTalk")
# Ensure bundled ffmpeg.exe is always findable, even when launched outside the VBS
os.environ["PATH"] = INSTALL_DIR + os.pathsep + os.environ.get("PATH", "")

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

        self._spin_idx       = 0
        self._spin_job       = None
        self._done_evt       = threading.Event()   # set when transcription finishes
        self._clean_audio    = False               # toggled by user before transcription
        self._diarize_enabled = False              # toggled by user before transcription
        self._transcribing   = False               # locks toggles once processing starts
        self._file_dur       = None                # populated sync from ffmpeg

        self.title("TinyTalk")
        self.configure(bg=C_BG)
        self.resizable(False, False)

        self._probe_duration_sync()   # get file duration before building UI so estimate is shown immediately
        self._build()

        W, H = 520, 460
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

        # Background model-update check runs immediately; _run waits for START button
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

        # ── Options row ───────────────────────────────────────────────────────
        tk.Frame(self, bg=C_BG, height=8).pack()

        opts_row = tk.Frame(self, bg=C_BG, padx=28)
        opts_row.pack(fill="x")

        f_opt = tkfont.Font(family="Consolas", size=9, weight="bold")

        eta = self._eta_clean()
        dirty_text = f"DIRTY AUDIO  {eta}" if eta else "DIRTY AUDIO"
        self._clean_btn = tk.Button(
            opts_row, text=dirty_text, font=f_opt,
            bg=C_CARD, fg=C_ACCENT,
            activebackground=C_YELLOW, activeforeground=C_BG,
            relief="solid", bd=1, padx=10, pady=6,
            cursor="hand2",
            highlightbackground=C_ACCENT, highlightcolor=C_ACCENT, highlightthickness=1,
            command=self._toggle_clean,
        )
        self._clean_btn.pack(side="left")

        tk.Frame(opts_row, bg=C_BG, width=8).pack(side="left")

        self._diarize_btn = tk.Button(
            opts_row, text="MULTI-SPEAKER", font=f_opt,
            bg=C_CARD, fg=C_ACCENT,
            activebackground=C_SUCCESS, activeforeground=C_BG,
            relief="solid", bd=1, padx=10, pady=6,
            cursor="hand2",
            highlightbackground=C_ACCENT, highlightcolor=C_ACCENT, highlightthickness=1,
            command=self._toggle_diarize,
        )
        self._diarize_btn.pack(side="left")

        self._start_btn = tk.Button(
            opts_row, text="START  ▶", font=f_opt,
            bg=C_ACCENT, fg=C_BG,
            activebackground="#00b8b8", activeforeground=C_BG,
            relief="flat", bd=0, padx=14, pady=6,
            cursor="hand2",
            command=self._start_processing,
        )
        self._start_btn.pack(side="right")

        tk.Frame(self, bg=C_BG, height=12).pack()
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x", padx=28)
        tk.Frame(self, bg=C_BG, height=8).pack()

        status_row = tk.Frame(self, bg=C_BG, padx=28)
        status_row.pack(fill="x")

        self.spin_var   = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="configure options above  →  then start")

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
        # Progress bar starts only when user clicks START

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

    # ── Clean audio toggle ────────────────────────────────────────────────────

    def _probe_duration_sync(self):
        """Get file duration synchronously via ffmpeg before UI builds."""
        try:
            import re
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                return
            r = subprocess.run(
                [ffmpeg, "-i", self.file_path],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", r.stderr)
            if m:
                self._file_dur = (int(m.group(1)) * 3600 +
                                  int(m.group(2)) * 60 +
                                  float(m.group(3)))
        except Exception:
            pass

    def _eta_clean(self):
        """Estimated clean time string, or empty string if unknown."""
        if self._file_dur is None:
            return ""
        secs = int(self._file_dur / 5)   # noisereduce ≈ 5x real-time
        if secs < 60:
            return f"~{secs}s"
        return f"~{secs // 60}m {secs % 60}s"

    def _update_clean_btn(self):
        eta = self._eta_clean()
        if self._transcribing:
            if self._clean_audio:
                label = f"DIRTY AUDIO  {eta}  ON" if eta else "DIRTY AUDIO  ON"
                self._clean_btn.config(bg=C_DIM, fg=C_BG, text=label,
                                       cursor="", relief="flat", bd=0,
                                       highlightthickness=0)
            else:
                label = f"DIRTY AUDIO  {eta}" if eta else "DIRTY AUDIO"
                self._clean_btn.config(bg=C_DIM, fg="#333333", text=label,
                                       cursor="", relief="flat", bd=0,
                                       highlightthickness=0)
        elif self._clean_audio:
            label = f"DIRTY AUDIO  {eta}  ON" if eta else "DIRTY AUDIO  ON"
            self._clean_btn.config(bg=C_YELLOW, fg=C_BG, text=label,
                                   cursor="hand2", relief="flat", bd=0,
                                   highlightthickness=0)
        else:
            label = f"DIRTY AUDIO  {eta}" if eta else "DIRTY AUDIO"
            self._clean_btn.config(bg=C_CARD, fg=C_ACCENT, text=label,
                                   cursor="hand2", relief="solid", bd=1,
                                   highlightthickness=1)

    def _toggle_clean(self):
        if self._transcribing:
            return
        self._clean_audio = not self._clean_audio
        self._update_clean_btn()

    def _update_diarize_btn(self):
        if self._transcribing:
            if self._diarize_enabled:
                self._diarize_btn.config(bg=C_DIM, fg=C_BG, text="MULTI-SPEAKER  ON",
                                         cursor="", relief="flat", bd=0, highlightthickness=0)
            else:
                self._diarize_btn.config(bg=C_DIM, fg="#333333", text="MULTI-SPEAKER",
                                         cursor="", relief="flat", bd=0, highlightthickness=0)
        elif self._diarize_enabled:
            self._diarize_btn.config(bg=C_SUCCESS, fg=C_BG, text="MULTI-SPEAKER  ON",
                                     cursor="hand2", relief="flat", bd=0, highlightthickness=0)
        else:
            self._diarize_btn.config(bg=C_CARD, fg=C_ACCENT, text="MULTI-SPEAKER",
                                     cursor="hand2", relief="solid", bd=1, highlightthickness=1)

    def _toggle_diarize(self):
        if self._transcribing:
            return
        self._diarize_enabled = not self._diarize_enabled
        self._update_diarize_btn()

    def _start_processing(self):
        if self._transcribing:
            return
        self._transcribing = True
        self._update_clean_btn()
        self._update_diarize_btn()
        self._start_btn.config(text="processing...", bg=C_DIM, fg="#555555",
                               cursor="", state="disabled")
        self.after(0, self._set_status, "loading model...", C_YELLOW)
        self.progress.config(mode="indeterminate")
        self.progress.start(12)
        threading.Thread(target=self._run, daemon=True).start()

    # ── Audio cleaning ────────────────────────────────────────────────────────

    def _clean_file(self, audio_path):
        """Denoise audio_path with noisereduce. Returns temp WAV path or None."""
        try:
            import noisereduce as nr
            import soundfile as sf
        except ImportError:
            self.after(0, self._append_log,
                       "  noisereduce not installed — skipping clean", "dim")
            return None
        try:
            import tempfile, numpy as np
            ffmpeg = shutil.which("ffmpeg")
            work   = audio_path
            tmp_in = None

            # Extract to WAV first for non-WAV inputs
            if ffmpeg and not audio_path.lower().endswith(".wav"):
                tmp_in = tempfile.mktemp(suffix=".wav")
                r = subprocess.run(
                    [ffmpeg, "-i", audio_path,
                     "-ac", "1", "-ar", "44100", "-y", tmp_in],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if r.returncode == 0:
                    work = tmp_in

            data, rate = sf.read(work)
            if tmp_in and os.path.exists(tmp_in):
                os.remove(tmp_in)

            reduced = nr.reduce_noise(y=data, sr=rate, prop_decrease=0.8)
            tmp_out = tempfile.mktemp(suffix="_clean.wav")
            sf.write(tmp_out, reduced, rate)
            return tmp_out
        except Exception as e:
            self.after(0, self._append_log, f"  clean failed: {e}", "dim")
            return None

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

            # Optional: clean audio before transcribing
            transcribe_path = self.file_path
            tmp_clean       = None
            if self._clean_audio:
                self.after(0, self._set_status, "cleaning audio...", C_YELLOW)
                tmp_clean = self._clean_file(self.file_path)
                if tmp_clean:
                    transcribe_path = tmp_clean
                    self.after(0, self._append_log, "  audio cleaned", "dim")

            # Speaker diarization (only if user enabled it)
            diarization = self._diarize(transcribe_path) if self._diarize_enabled else None
            if diarization:
                n_spk = len(set(lbl for _, _, lbl in diarization))
                self.after(0, self._append_log,
                           f"  {n_spk} speaker{'s' if n_spk != 1 else ''} detected", "dim")

            def _speaker_at(t):
                if not diarization:
                    return None
                for s, e, lbl in diarization:
                    if s <= t < e:
                        return lbl
                return diarization[-1][2]

            self.after(0, self._set_status, "transcribing...", C_YELLOW)
            segments, info = model.transcribe(transcribe_path, beam_size=5,
                                              word_timestamps=True)

            lang = info.language.upper() if info.language else "?"
            duration = info.duration or 1
            self.after(0, self._set_status, f"transcribing  [{lang}]  ...", C_YELLOW)

            # Switch progress bar to determinate now that we know the duration
            self.after(0, self._progress_start_determinate)

            import time as _time
            t_start = _time.monotonic()

            def _fmt_ts(secs):
                h = int(secs // 3600)
                m = int((secs % 3600) // 60)
                s = int(secs % 60)
                return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

            lines  = []
            # Use a mutable state dict so the inner closure can update all fields
            st = {"words": [], "start": None, "speaker": None}

            def _flush():
                if not st["words"]:
                    return
                ts   = _fmt_ts(st["start"])
                text = "".join(st["words"]).strip()
                if text:
                    spk  = f"{st['speaker']}: " if st["speaker"] else ""
                    line = f"[{ts}] {spk}{text}"
                    lines.append(line)
                    self.after(0, self._append_log, line, "text")
                st["words"].clear()
                st["start"]   = None
                st["speaker"] = None

            for seg in segments:
                for w in (seg.words or []):
                    word     = w.word
                    word_t   = w.start if w.start is not None else seg.start
                    word_spk = _speaker_at(word_t)

                    # Flush on speaker change mid-sentence
                    if st["speaker"] is not None and word_spk != st["speaker"] and st["words"]:
                        _flush()

                    if st["start"] is None:
                        st["start"]   = word_t
                        st["speaker"] = word_spk
                    st["words"].append(word)

                    if word.strip() and word.strip()[-1] in ".?!,":
                        _flush()

                pct = min(seg.end / duration * 100, 99)
                self.after(0, self._progress_set, pct)

                # ETA: based on measured speed so far (self-corrects as it runs)
                elapsed = _time.monotonic() - t_start
                if elapsed > 1 and seg.end > 0:
                    speed     = seg.end / elapsed
                    remaining = (duration - seg.end) / speed
                    if remaining >= 60:
                        eta_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                    else:
                        eta_str = f"{int(remaining)}s"
                    self.after(0, self._set_status,
                               f"transcribing  [{lang}]  ~{eta_str} left", C_YELLOW)

            _flush()  # trailing words

            with open(self.out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            # Clean up temp cleaned audio file
            if tmp_clean and os.path.exists(tmp_clean):
                try:
                    os.remove(tmp_clean)
                except Exception:
                    pass

            self.after(0, self._done, lang)

        except Exception as exc:
            if 'tmp_clean' in dir() and tmp_clean and os.path.exists(tmp_clean):
                try:
                    os.remove(tmp_clean)
                except Exception:
                    pass
            self.after(0, self._err, str(exc))

    # ── Speaker diarization ───────────────────────────────────────────────────

    def _diarize(self, audio_path):
        """Return [(start, end, 'SPEAKER N'), ...] or None if unavailable/single speaker.
        Uses resemblyzer (speaker embeddings) + scikit-learn (clustering).
        Falls back silently if either library is missing or diarization fails.
        Audio extraction handled by ffmpeg so any format works."""
        try:
            import numpy as np
            from resemblyzer import VoiceEncoder
            from sklearn.cluster import AgglomerativeClustering
        except ImportError:
            return None

        try:
            import tempfile, wave as _wave

            self.after(0, self._set_status, "detecting speakers...", C_YELLOW)

            # Extract 16 kHz mono WAV with ffmpeg (handles all audio/video formats)
            ffmpeg = shutil.which("ffmpeg")
            if not ffmpeg:
                return None

            tmp = tempfile.mktemp(suffix=".wav")
            r = subprocess.run(
                [ffmpeg, "-i", audio_path,
                 "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le", "-y", tmp],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if r.returncode != 0 or not os.path.exists(tmp):
                return None

            # Load PCM with stdlib wave — no librosa needed
            with _wave.open(tmp, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
            os.remove(tmp)

            wav = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            sr  = 16000
            dur = len(wav) / sr

            if dur < 6:
                return None  # too short for meaningful diarization

            # Sliding window speaker embeddings
            encoder  = VoiceEncoder()
            win_sec  = 1.5
            step_sec = 0.5
            embeddings, centers = [], []
            t = 0.0
            while t + win_sec <= dur:
                chunk = wav[int(t * sr): int((t + win_sec) * sr)]
                embeddings.append(encoder.embed_utterance(chunk))
                centers.append(t + win_sec / 2)
                t += step_sec

            if len(embeddings) < 6:
                return None

            X = np.array(embeddings)   # already L2-normalised by resemblyzer

            # Agglomerative clustering — threshold controls sensitivity
            clustering = AgglomerativeClustering(
                n_clusters=None, distance_threshold=0.65, linkage="ward"
            )
            labels = clustering.fit_predict(X)

            if len(set(labels)) <= 1:
                return None  # single speaker — don't add labels

            # Build contiguous speaker segments
            timeline = []
            seg_start = max(0.0, centers[0] - step_sec / 2)
            prev      = labels[0]
            for i in range(1, len(labels)):
                if labels[i] != prev:
                    seg_end = centers[i - 1] + step_sec / 2
                    timeline.append((seg_start, seg_end, f"SPEAKER {prev + 1}"))
                    seg_start = seg_end
                    prev      = labels[i]
            timeline.append((seg_start, dur, f"SPEAKER {prev + 1}"))
            return timeline

        except Exception:
            return None   # never crash the main transcription

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
