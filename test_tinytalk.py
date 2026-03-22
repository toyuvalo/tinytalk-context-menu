"""
TinyTalk test suite.
Run: python test_tinytalk.py
"""
import os, sys, time, wave, struct, shutil, math, subprocess

MODEL_SIZE   = "base"
MODEL_CACHE  = os.path.join(os.path.expanduser("~"), ".cache", "huggingface",
                            "hub", f"models--Systran--faster-whisper-{MODEL_SIZE}")
TEST_WAV     = os.path.join(os.path.dirname(__file__), "_test_audio.wav")
TEST_TXT     = TEST_WAV.replace(".wav", ".txt")

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
INFO = "\033[94m·\033[0m"

def header(msg): print(f"\n\033[1m{msg}\033[0m")
def ok(msg):     print(f"  {PASS}  {msg}")
def fail(msg):   print(f"  {FAIL}  {msg}"); sys.exit(1)
def info(msg):   print(f"  {INFO}  {msg}")


# ── Test 1: cache sanity ───────────────────────────────────────────────────────
header("1 · Model cache")

if os.path.exists(MODEL_CACHE):
    # Check for incomplete blobs — these cause the silent hang
    incomplete = [
        f for root, _, files in os.walk(MODEL_CACHE)
        for f in files if f.endswith(".incomplete")
    ]
    if incomplete:
        info(f"Found {len(incomplete)} .incomplete blob(s) — wiping broken cache")
        shutil.rmtree(MODEL_CACHE)
        ok("Broken cache removed")
    else:
        size_mb = sum(
            os.path.getsize(os.path.join(r, f))
            for r, _, files in os.walk(MODEL_CACHE) for f in files
        ) / 1e6
        ok(f"Cache present  ({size_mb:.1f} MB)")
else:
    info("No cache — will download during model load test")


# ── Test 2: faster-whisper import ─────────────────────────────────────────────
header("2 · faster-whisper import")
try:
    from faster_whisper import WhisperModel
    ok("faster_whisper imported")
except ImportError as e:
    fail(f"Import failed: {e}")


# ── Test 3: model load + download ─────────────────────────────────────────────
header("3 · Model load (downloads if needed)")
t0 = time.time()
try:
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="default")
    elapsed = time.time() - t0
    ok(f"Model loaded in {elapsed:.1f}s")

    # Verify cache is now populated and clean
    size_mb = sum(
        os.path.getsize(os.path.join(r, f))
        for r, _, files in os.walk(MODEL_CACHE) for f in files
    ) / 1e6
    incomplete = [
        f for root, _, files in os.walk(MODEL_CACHE)
        for f in files if f.endswith(".incomplete")
    ]
    if incomplete:
        fail(f"Cache still has {len(incomplete)} .incomplete files after load!")
    ok(f"Cache clean  ({size_mb:.1f} MB, 0 incomplete files)")
except Exception as e:
    fail(f"Model load failed after {time.time()-t0:.1f}s: {e}")


# ── Test 4: generate test audio via Windows TTS ───────────────────────────────
header("4 · Test audio (Windows TTS)")
try:
    ps_script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.SetOutputToWaveFile('{TEST_WAV.replace(chr(92), chr(92)*2)}'); "
        "$s.Speak('The quick brown fox jumps over the lazy dog. "
        "TinyTalk is working correctly.'); "
        "$s.Dispose()"
    )
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True
    )
    if not os.path.exists(TEST_WAV) or os.path.getsize(TEST_WAV) < 1000:
        fail(f"TTS failed: {result.stderr.strip()}")
    size_kb = os.path.getsize(TEST_WAV) / 1024
    ok(f"Test WAV created  ({size_kb:.0f} KB)")
except Exception as e:
    fail(str(e))


# ── Test 5: transcription ─────────────────────────────────────────────────────
header("5 · Transcription")
t0 = time.time()
try:
    segments, info_obj = model.transcribe(TEST_WAV, beam_size=5)
    lines = []
    for seg in segments:
        lines.append(seg.text.strip())
    elapsed = time.time() - t0
    transcript = " ".join(lines)

    ok(f"Transcribed in {elapsed:.1f}s")
    ok(f"Language detected: {info_obj.language.upper()}")
    info(f"Transcript: \"{transcript}\"")

    # Check it got the key words
    lower = transcript.lower()
    hits = [w for w in ["quick", "brown", "fox", "dog"] if w in lower]
    if len(hits) >= 2:
        ok(f"Content check passed ({len(hits)}/4 key words found)")
    else:
        fail(f"Transcript looks wrong — only matched: {hits}")
except Exception as e:
    fail(f"Transcription failed: {e}")


# ── Test 6: file output ────────────────────────────────────────────────────────
header("6 · File output")
try:
    with open(TEST_TXT, "w", encoding="utf-8") as f:
        f.write(transcript)
    ok(f"Written: {TEST_TXT}")
except Exception as e:
    fail(str(e))


# ── Cleanup ────────────────────────────────────────────────────────────────────
for p in (TEST_WAV, TEST_TXT):
    if os.path.exists(p):
        os.remove(p)

print(f"\n\033[92m\033[1m  All tests passed.\033[0m\n")
